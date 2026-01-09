"""
Vision Processing using OpenAI Vision API.

This module handles multimodal processing of images, charts, and scanned documents
using GPT-4 Vision or similar multimodal models.
"""

from typing import Optional, Dict, Any, List
import base64
import time
import json
from io import BytesIO

from openai import OpenAI, AzureOpenAI
from PIL import Image

from ..models import ExtractedImage, ExtractedChart, ContentType
from ..utils import get_config, get_logger, log_agent_step, log_cost, log_performance
from ..prompts import get_prompt_for_content_type, format_page_analysis_prompt


class VisionProcessor:
    """
    Vision Processing using OpenAI Vision API.

    This processor uses multimodal models (GPT-4 Vision, GPT-4o) to:
    - Extract text from scanned documents
    - Analyze images and diagrams
    - Extract data from charts and graphs
    - Process complex visual layouts
    - Handle SmartArt and constructed graphics
    """

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize vision processor.

        Args:
            model: Model name (default from config)
            provider: Provider (openai, anthropic) - default from config
        """
        self.logger = get_logger()
        self.config = get_config()

        # Get model configuration
        if model is None or provider is None:
            model_config = self.config.get_model_config("vision")
            self.model = model or model_config.name
            self.provider = provider or model_config.provider
        else:
            self.model = model
            self.provider = provider

        # Initialize OpenAI client
        if self.provider == "openai":
            if not self.config.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.client = OpenAI(api_key=self.config.openai_api_key)
        elif self.provider == "azure_openai":
            if not self.config.azure_openai_api_key:
                raise ValueError("Azure OpenAI API key not configured")
            if not self.config.azure_openai_endpoint:
                raise ValueError("Azure OpenAI endpoint not configured")
            self.client = AzureOpenAI(
                api_key=self.config.azure_openai_api_key,
                api_version=self.config.azure_openai_api_version,
                azure_endpoint=self.config.azure_openai_endpoint
            )
            # For Azure, use the deployment name as the model
            if self.config.azure_openai_vision_deployment:
                self.model = self.config.azure_openai_vision_deployment
            elif self.config.azure_openai_deployment_name:
                self.model = self.config.azure_openai_deployment_name
        else:
            # TODO: Add Anthropic support
            raise ValueError(f"Provider {self.provider} not yet supported")

        self.name = "VisionProcessor"

        log_agent_step(
            self.name,
            "Initialized",
            {"model": self.model, "provider": self.provider},
        )

    def encode_image(self, image_bytes: bytes, max_size: int = 2000) -> str:
        """
        Encode image to base64 and optionally resize.

        Args:
            image_bytes: Image bytes
            max_size: Maximum dimension (width or height)

        Returns:
            Base64 encoded image string
        """
        # Open image
        image = Image.open(BytesIO(image_bytes))

        # Resize if needed
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to RGB if needed
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Encode to base64
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return image_b64

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        content_type: str = "image",
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Analyze an image using vision API.

        Args:
            image_bytes: Image bytes (PNG, JPEG, etc.)
            prompt: Custom prompt (uses default if None)
            content_type: Type of content (image, chart, table, etc.)
            max_tokens: Maximum tokens in response

        Returns:
            Analysis result dictionary
        """
        log_agent_step(
            self.name,
            f"Analyzing {content_type}",
            {"model": self.model},
            level="debug",
        )

        start_time = time.time()

        # Get prompt
        if prompt is None:
            prompt = get_prompt_for_content_type(content_type)

        # Encode image
        image_b64 = self.encode_image(image_bytes)

        try:
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                            },
                        ],
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.0,  # Deterministic for extraction
            )

            # Extract response
            content = response.choices[0].message.content
            usage = response.usage

            # Calculate cost (approximate)
            # GPT-4o vision: ~$0.01 per image
            cost = 0.02  # Conservative estimate

            processing_time = time.time() - start_time

            log_cost(
                f"Vision API ({content_type})",
                cost,
                {
                    "tokens": usage.total_tokens if usage else 0,
                    "model": self.model,
                },
            )

            log_performance(
                f"Vision analysis ({content_type})",
                processing_time,
            )

            # Try to parse as JSON if it looks like JSON
            result_data = content
            if content.strip().startswith("{"):
                try:
                    result_data = json.loads(content)
                except json.JSONDecodeError:
                    # Keep as string if not valid JSON
                    pass

            return {
                "success": True,
                "content": result_data,
                "raw_response": content,
                "model": self.model,
                "cost": cost,
                "processing_time": processing_time,
                "tokens_used": usage.total_tokens if usage else 0,
            }

        except Exception as e:
            self.logger.error(f"Error in vision analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None,
                "cost": 0.0,
                "processing_time": time.time() - start_time,
            }

    def analyze_page_as_image(
        self,
        image_bytes: bytes,
        page_number: int,
        total_pages: int,
    ) -> Dict[str, Any]:
        """
        Analyze a full page rendered as an image.

        Args:
            image_bytes: Page image bytes
            page_number: Page number
            total_pages: Total pages in document

        Returns:
            Analysis result with extracted content
        """
        log_agent_step(
            self.name,
            f"Analyzing full page {page_number}/{total_pages}",
        )

        # Use full page analysis prompt
        prompt = format_page_analysis_prompt(page_number, total_pages)

        result = self.analyze_image(
            image_bytes=image_bytes,
            prompt=prompt,
            content_type="full_page",
            max_tokens=2000,  # More tokens for full page
        )

        return result

    def extract_chart_data(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract data from a chart or graph.

        Args:
            image_bytes: Chart image bytes

        Returns:
            Extracted chart data
        """
        return self.analyze_image(
            image_bytes=image_bytes,
            content_type="chart",
            max_tokens=1500,
        )

    def extract_table(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract table structure and data from image.

        Args:
            image_bytes: Table image bytes

        Returns:
            Extracted table data
        """
        return self.analyze_image(
            image_bytes=image_bytes,
            content_type="table",
            max_tokens=2000,
        )

    def extract_table_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract table from image and return structured data.

        This is used by TableProcessor for complex table fallback.

        Args:
            image_bytes: Table image bytes

        Returns:
            Dictionary with headers, rows, caption, confidence
        """
        result = self.extract_table(image_bytes)

        if not result.get("success"):
            return {"error": result.get("error", "Unknown error")}

        # Parse the content
        content = result.get("content")

        # If content is a dict (parsed JSON), use it directly
        if isinstance(content, dict):
            return {
                "headers": content.get("headers", []),
                "rows": content.get("rows", []),
                "caption": content.get("caption"),
                "confidence": content.get("confidence", 0.8),
            }

        # Otherwise, try to parse the text response
        # For now, return a simple structure
        # TODO: Add more sophisticated parsing
        return {
            "headers": [],
            "rows": [],
            "caption": None,
            "confidence": 0.7,
            "raw_text": str(content),
        }

    def ocr_scanned_document(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text from scanned document image using OCR.

        Args:
            image_bytes: Scanned document image bytes

        Returns:
            Extracted text
        """
        return self.analyze_image(
            image_bytes=image_bytes,
            content_type="scanned",
            max_tokens=2000,
        )

    def analyze_diagram(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analyze a diagram (flowchart, org chart, etc.).

        Args:
            image_bytes: Diagram image bytes

        Returns:
            Diagram description and structure
        """
        return self.analyze_image(
            image_bytes=image_bytes,
            content_type="diagram",
            max_tokens=1500,
        )

    def batch_analyze_images(
        self,
        images: List[bytes],
        content_type: str = "image",
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple images in batch.

        Args:
            images: List of image bytes
            content_type: Type of content

        Returns:
            List of analysis results
        """
        log_agent_step(
            self.name,
            f"Batch analyzing {len(images)} images",
            {"type": content_type},
        )

        results = []
        for i, image_bytes in enumerate(images):
            log_agent_step(
                self.name,
                f"Processing image {i+1}/{len(images)}",
                level="debug",
            )

            result = self.analyze_image(
                image_bytes=image_bytes,
                content_type=content_type,
            )
            results.append(result)

        total_cost = sum(r.get("cost", 0) for r in results)
        log_cost(
            f"Batch vision analysis ({len(images)} images)",
            total_cost,
        )

        return results


def create_vision_processor(
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> VisionProcessor:
    """
    Factory function to create a vision processor.

    Args:
        model: Model name (default from config)
        provider: Provider name (default from config)

    Returns:
        Configured VisionProcessor instance
    """
    return VisionProcessor(model=model, provider=provider)
