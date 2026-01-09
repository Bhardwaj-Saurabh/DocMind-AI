"""
Vision Processing Agent - Handles multimodal processing of visual content.

This agent uses vision models (GPT-4 Vision, GPT-4o) to process:
- Scanned documents
- Pages with charts and graphs
- Complex visual layouts
- SmartArt and constructed graphics
"""

from typing import Optional, List
import time

from ..models import PageContent, ProcessingStrategy
from ..graph.state import DocumentState
from ..processors import create_vision_processor
from ..utils import get_logger, log_agent_step, log_cost, log_performance


class VisionAgent:
    """
    Vision Processing Agent.

    This agent provides multimodal processing for visual content that
    cannot be extracted with simple text extraction.

    Strategies handled:
    - VISION_PRIMARY: Full page vision processing
    - RENDER_AND_VISION: Scanned documents
    - HYBRID_COMPLEX: Pages with charts/images (vision for visual elements)

    Cost: ~$0.02-0.05 per page
    Speed: ~2-5 seconds per page
    """

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize vision agent.

        Args:
            model: Vision model name (default from config)
            provider: Provider (openai, anthropic) - default from config
        """
        self.logger = get_logger()
        self.name = "VisionAgent"

        # Create vision processor
        self.vision_processor = create_vision_processor(model=model, provider=provider)

        log_agent_step(
            self.name,
            "Initialized",
            {"model": self.vision_processor.model},
        )

    def process_page(
        self,
        page_number: int,
        state: DocumentState,
    ) -> PageContent:
        """
        Process a single page using vision API.

        Args:
            page_number: Page number to process (1-indexed)
            state: Current document state

        Returns:
            PageContent with vision-extracted content
        """
        log_agent_step(
            self.name,
            f"Processing page {page_number} with vision",
            level="debug",
        )

        start_time = time.time()

        extractor = state["extractor"]
        metadata = state["metadata"]

        try:
            # Get the content analysis for this page
            analysis = None
            for a in state["page_analyses"]:
                if a.page_number == page_number:
                    analysis = a
                    break

            # Render page as image
            image_bytes = extractor.render_page_as_image(page_number, dpi=150)

            # Analyze with vision API
            result = self.vision_processor.analyze_page_as_image(
                image_bytes=image_bytes,
                page_number=page_number,
                total_pages=metadata.total_pages,
            )

            if not result["success"]:
                raise RuntimeError(f"Vision analysis failed: {result.get('error')}")

            # Extract content from result
            content = result["content"]

            # Parse content (it should be JSON or structured text)
            text = ""
            images = []
            tables = []
            charts = []

            if isinstance(content, dict):
                # Structured JSON response from vision model
                text = content.get("text", "")

                # Parse images with descriptions (already converted to text by vision model)
                if "images" in content:
                    for img_data in content.get("images", []):
                        from ..models import ExtractedImage
                        images.append(ExtractedImage(
                            image_id=f"img_{page_number}_{len(images)}",
                            page_number=page_number,
                            format="png",
                            width=0,  # Not available from vision
                            height=0,
                            size_bytes=0,
                            description=img_data.get("description", ""),  # Vision-generated description
                            text_content=img_data.get("text_content", ""),
                            extraction_method="vision_api",
                            confidence_score=0.9
                        ))

                # Parse tables (already converted to markdown by vision model)
                if "tables" in content:
                    for tbl_data in content.get("tables", []):
                        from ..models import ExtractedTable
                        tables.append(ExtractedTable(
                            table_id=f"tbl_{page_number}_{len(tables)}",
                            page_number=page_number,
                            headers=tbl_data.get("headers", []),
                            data=tbl_data.get("rows", []),
                            title=tbl_data.get("title"),
                            extraction_method="vision_api",
                            confidence_score=0.9
                        ))

                # Parse charts (already converted to text by vision model)
                if "charts" in content:
                    for chart_data in content.get("charts", []):
                        from ..models import ExtractedChart
                        charts.append(ExtractedChart(
                            chart_id=f"chart_{page_number}_{len(charts)}",
                            page_number=page_number,
                            chart_type=chart_data.get("type", "unknown"),
                            title=chart_data.get("title", ""),
                            description=chart_data.get("description", ""),  # Comprehensive description
                            data_series=[],  # Data embedded in description
                            extraction_method="vision_api",
                            confidence_score=0.9
                        ))
            else:
                # Plain text response (comprehensive markdown from updated prompts)
                # This is the expected format with the new RAG-optimized prompts
                text = str(content)

            # Calculate metrics
            word_count = len(text.split()) if text else 0
            char_count = len(text) if text else 0

            processing_time = time.time() - start_time
            processing_cost = result["cost"]

            # Create page content
            page_id = f"{state['document_id']}_page_{page_number}"

            page_content = PageContent(
                page_id=page_id,
                page_number=page_number,
                content_analysis=analysis,
                processing_strategy=ProcessingStrategy.VISION_PRIMARY,
                text=text,
                images=images,
                tables=tables,
                charts=charts,
                word_count=word_count,
                char_count=char_count,
                processing_time=processing_time,
                processing_cost=processing_cost,
                quality_score=0.90,  # Good quality for vision extraction
                fallback_triggered=False,
            )

            log_cost(
                f"Vision processing (page {page_number})",
                processing_cost,
                {"words": word_count},
            )

            log_performance(
                f"Vision processing (page {page_number})",
                processing_time,
                {"words": word_count},
            )

            return page_content

        except Exception as e:
            self.logger.error(f"Error processing page {page_number} with vision: {e}")

            # Return empty page content with error
            page_id = f"{state['document_id']}_page_{page_number}"
            return PageContent(
                page_id=page_id,
                page_number=page_number,
                text="",
                word_count=0,
                char_count=0,
                processing_time=time.time() - start_time,
                processing_cost=0.0,
                quality_score=0.0,
                fallback_triggered=False,
            )

    def process_pages(
        self,
        page_numbers: List[int],
        state: DocumentState,
    ) -> List[PageContent]:
        """
        Process multiple pages with vision.

        Args:
            page_numbers: List of page numbers to process
            state: Current document state

        Returns:
            List of PageContent objects
        """
        log_agent_step(
            self.name,
            f"Processing {len(page_numbers)} pages with vision",
        )

        results = []
        for page_num in page_numbers:
            page_content = self.process_page(page_num, state)
            results.append(page_content)

        log_agent_step(
            self.name,
            f"Completed vision processing for {len(results)} pages",
            {
                "total_words": sum(p.word_count for p in results),
                "total_cost": f"${sum(p.processing_cost for p in results):.4f}",
            },
        )

        return results

    def process_node(self, state: DocumentState) -> DocumentState:
        """
        LangGraph node function for vision processing.

        Processes all pages that need vision API.

        Args:
            state: Current document state

        Returns:
            Updated state with vision processing results
        """
        log_agent_step(
            self.name,
            "Starting vision processing node",
        )

        # Find pages that need vision processing
        vision_pages = []
        for analysis in state["page_analyses"]:
            if analysis.recommended_strategy in [
                ProcessingStrategy.VISION_PRIMARY,
                ProcessingStrategy.RENDER_AND_VISION,
                ProcessingStrategy.HYBRID_COMPLEX,
            ]:
                if analysis.page_number not in state["pages_processed"]:
                    vision_pages.append(analysis.page_number)

        if not vision_pages:
            log_agent_step(
                self.name,
                "No pages need vision processing",
                level="debug",
            )
            return state

        # Process all vision pages
        page_results = self.process_pages(vision_pages, state)

        # Add results to state
        for page_content in page_results:
            state["page_results"].append(page_content)
            state["pages_processed"].append(page_content.page_number)

            # Update aggregates
            state["total_cost"] += page_content.processing_cost
            state["total_time"] += page_content.processing_time

            # Update strategy counts
            if page_content.processing_strategy:
                strategy = page_content.processing_strategy.value
                state["strategy_counts"][strategy] = state["strategy_counts"].get(strategy, 0) + 1

        log_agent_step(
            self.name,
            f"Vision processing complete",
            {
                "pages_processed": len(page_results),
                "total_cost": f"${sum(p.processing_cost for p in page_results):.4f}",
            },
        )

        return state
