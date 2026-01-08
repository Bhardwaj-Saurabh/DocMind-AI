"""
PDF extractor using PyMuPDF (fitz).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image
import io

from .base import BaseExtractor
from ..models import (
    DocumentMetadata,
    DocumentFormat,
    ContentAnalysisResult,
    ContentType,
    ProcessingStrategy,
    TextQuality,
    TableInfo,
)


class PDFExtractor(BaseExtractor):
    """
    PDF document extractor using PyMuPDF.

    Provides text extraction, image extraction, and content analysis
    to determine optimal processing strategy for each page.
    """

    def __init__(self, file_path: str):
        """Initialize PDF extractor."""
        super().__init__(file_path)
        self.doc = fitz.open(str(self.file_path))

    def get_format(self) -> DocumentFormat:
        """Get document format."""
        return DocumentFormat.PDF

    def get_page_count(self) -> int:
        """Get total number of pages."""
        return len(self.doc)

    def get_metadata(self) -> DocumentMetadata:
        """Extract PDF metadata."""
        metadata_dict = self.doc.metadata or {}

        # Convert PDF dates to datetime
        created_date = None
        modified_date = None

        if "creationDate" in metadata_dict:
            try:
                # PDF dates are in format: D:20230101120000
                date_str = metadata_dict["creationDate"]
                if date_str.startswith("D:"):
                    date_str = date_str[2:16]  # Extract YYYYMMDDHHMMSS
                    created_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            except:
                pass

        if "modDate" in metadata_dict:
            try:
                date_str = metadata_dict["modDate"]
                if date_str.startswith("D:"):
                    date_str = date_str[2:16]
                    modified_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
            except:
                pass

        return DocumentMetadata(
            document_id=self.document_id,
            file_path=str(self.file_path),
            file_name=self.file_path.name,
            file_size=self.file_path.stat().st_size,
            format=DocumentFormat.PDF,
            title=metadata_dict.get("title"),
            author=metadata_dict.get("author"),
            subject=metadata_dict.get("subject"),
            keywords=metadata_dict.get("keywords", "").split(",") if metadata_dict.get("keywords") else None,
            created_date=created_date,
            modified_date=modified_date,
            total_pages=len(self.doc),
            page_count=len(self.doc),
        )

    def extract_text(self, page_number: int) -> str:
        """
        Extract text from a PDF page.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            Extracted text
        """
        if page_number < 1 or page_number > len(self.doc):
            raise ValueError(f"Invalid page number: {page_number}")

        page = self.doc[page_number - 1]  # Convert to 0-indexed
        text = page.get_text()
        return text.strip()

    def extract_images(self, page_number: int) -> List[Dict[str, Any]]:
        """
        Extract embedded images from a PDF page.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            List of image dictionaries
        """
        if page_number < 1 or page_number > len(self.doc):
            raise ValueError(f"Invalid page number: {page_number}")

        page = self.doc[page_number - 1]
        image_list = page.get_images()

        images = []
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = self.doc.extract_image(xref)
                image_data = {
                    "image_id": f"img_{page_number}_{img_index}",
                    "page_number": page_number,
                    "image_data": base_image["image"],
                    "width": base_image.get("width"),
                    "height": base_image.get("height"),
                    "format": base_image.get("ext", "").upper(),
                    "xref": xref,
                }
                images.append(image_data)
            except:
                # Some images might not be extractable
                continue

        return images

    def extract_tables(self, page_number: int) -> List[Dict[str, Any]]:
        """
        Extract tables from a PDF page.

        Note: This is a basic implementation. For production, consider using
        libraries like camelot-py or tabula-py for better table extraction.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            List of table dictionaries
        """
        # Basic table detection using text blocks
        # This is a placeholder - actual table extraction would use camelot/tabula
        page = self.doc[page_number - 1]

        # Get structured text to analyze for table-like patterns
        blocks = page.get_text("dict")["blocks"]

        tables = []
        # TODO: Implement more sophisticated table detection
        # For now, return empty list and rely on vision API for complex tables

        return tables

    def analyze_page_content(self, page_number: int) -> ContentAnalysisResult:
        """
        Analyze PDF page content and recommend processing strategy.

        This is the CRITICAL method that enables adaptive processing!

        Args:
            page_number: Page number (1-indexed)

        Returns:
            ContentAnalysisResult with processing recommendation
        """
        if page_number < 1 or page_number > len(self.doc):
            raise ValueError(f"Invalid page number: {page_number}")

        page = self.doc[page_number - 1]

        # Extract text
        text = page.get_text().strip()
        text_length = len(text)

        # Detect embedded images
        image_list = page.get_images()
        embedded_images_count = len(image_list)

        # Analyze text quality
        text_quality = TextQuality.HIGH
        if text_length < 50:
            text_quality = TextQuality.LOW
        elif text_length < 200:
            text_quality = TextQuality.MEDIUM

        # Check if page is likely scanned (image-based)
        is_scanned = False
        if text_length < 20 and embedded_images_count == 0:
            # Very little text and no images might indicate a scanned page
            # or a page that's actually rendered as an image
            page_dict = page.get_text("dict")
            if len(page_dict.get("blocks", [])) < 2:
                is_scanned = True
                text_quality = TextQuality.NONE

        # Detect tables (simple heuristic)
        # Look for tab characters or evenly spaced text
        table_info = TableInfo(count=0, complexity="none")
        if "\t" in text or text.count("|") > 5:
            # Likely has tables
            table_info.count = text.count("\n\n") // 3  # Rough estimate
            table_info.complexity = "simple"
            if text.count("|") > 20:  # Many delimiters suggests complex table
                table_info.complexity = "complex"

        # Detect charts (charts are usually embedded as images)
        charts_count = 0
        # Charts are typically larger images
        for img in image_list:
            try:
                base_image = self.doc.extract_image(img[0])
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                # Assume images larger than 200x200 might be charts
                if width > 200 and height > 200:
                    charts_count += 1
            except:
                pass

        # Determine content type
        content_type = ContentType.PURE_TEXT
        if is_scanned:
            content_type = ContentType.SCANNED
        elif charts_count > 0:
            content_type = ContentType.TEXT_WITH_CHARTS
        elif table_info.count > 0:
            content_type = ContentType.TEXT_WITH_TABLES
        elif embedded_images_count > 0:
            content_type = ContentType.TEXT_WITH_IMAGES
        elif text_length < 100:
            content_type = ContentType.VISUAL_HEAVY

        # Determine processing strategy
        strategy = self._determine_strategy(
            content_type=content_type,
            text_quality=text_quality,
            text_length=text_length,
            has_images=embedded_images_count > 0,
            has_tables=table_info.count > 0,
            has_charts=charts_count > 0,
            is_scanned=is_scanned,
        )

        # Estimate cost and time
        estimated_cost, estimated_time = self._estimate_cost_and_time(strategy, text_length, embedded_images_count)

        return ContentAnalysisResult(
            page_id=f"{self.document_id}_page_{page_number}",
            page_number=page_number,
            content_type=content_type,
            text_quality=text_quality,
            text_length=text_length,
            embedded_images_count=embedded_images_count,
            constructed_graphics_count=0,  # PDFs don't have "constructed" graphics like PPT
            charts_count=charts_count,
            table_info=table_info,
            layout_complexity="simple" if text_length > 200 else "complex",
            is_scanned=is_scanned,
            requires_rendering=is_scanned or (text_quality == TextQuality.NONE),
            recommended_strategy=strategy,
            estimated_cost=estimated_cost,
            estimated_time=estimated_time,
        )

    def _determine_strategy(
        self,
        content_type: ContentType,
        text_quality: TextQuality,
        text_length: int,
        has_images: bool,
        has_tables: bool,
        has_charts: bool,
        is_scanned: bool,
    ) -> ProcessingStrategy:
        """Determine optimal processing strategy based on content analysis."""

        # Scanned documents always need vision
        if is_scanned:
            return ProcessingStrategy.RENDER_AND_VISION

        # Pure text - fastest and cheapest
        if content_type == ContentType.PURE_TEXT and text_quality == TextQuality.HIGH:
            return ProcessingStrategy.TEXT_ONLY

        # Text with simple tables
        if has_tables and not has_images and not has_charts:
            return ProcessingStrategy.STRUCTURAL_PARSING

        # Charts always need vision
        if has_charts:
            return ProcessingStrategy.HYBRID_COMPLEX

        # Embedded images
        if has_images and not has_charts:
            return ProcessingStrategy.HYBRID_SIMPLE

        # Default to text extraction for anything else
        if text_quality in [TextQuality.HIGH, TextQuality.MEDIUM]:
            return ProcessingStrategy.TEXT_ONLY

        # Fallback to vision if text quality is poor
        return ProcessingStrategy.VISION_PRIMARY

    def _estimate_cost_and_time(
        self, strategy: ProcessingStrategy, text_length: int, image_count: int
    ) -> tuple[float, float]:
        """Estimate processing cost and time based on strategy."""

        # Cost estimates (in USD)
        TEXT_COST_PER_PAGE = 0.001
        VISION_COST_PER_IMAGE = 0.02
        TABLE_PARSING_COST = 0.002

        # Time estimates (in seconds)
        TEXT_TIME = 0.3
        VISION_TIME = 2.5
        TABLE_TIME = 0.5

        cost = 0.0
        time = 0.0

        if strategy == ProcessingStrategy.TEXT_ONLY:
            cost = TEXT_COST_PER_PAGE
            time = TEXT_TIME

        elif strategy == ProcessingStrategy.STRUCTURAL_PARSING:
            cost = TEXT_COST_PER_PAGE + TABLE_PARSING_COST
            time = TEXT_TIME + TABLE_TIME

        elif strategy == ProcessingStrategy.HYBRID_SIMPLE:
            cost = TEXT_COST_PER_PAGE + (image_count * VISION_COST_PER_IMAGE * 0.5)  # Smaller images
            time = TEXT_TIME + (image_count * VISION_TIME * 0.3)

        elif strategy == ProcessingStrategy.HYBRID_COMPLEX:
            cost = TEXT_COST_PER_PAGE + (image_count * VISION_COST_PER_IMAGE)
            time = TEXT_TIME + (image_count * VISION_TIME)

        elif strategy in [ProcessingStrategy.VISION_PRIMARY, ProcessingStrategy.RENDER_AND_VISION]:
            cost = VISION_COST_PER_IMAGE  # Full page as image
            time = VISION_TIME

        return cost, time

    def render_page_as_image(self, page_number: int, dpi: int = 150) -> bytes:
        """
        Render a PDF page as PNG image.

        Args:
            page_number: Page number (1-indexed)
            dpi: Resolution for rendering (default: 150)

        Returns:
            PNG image as bytes
        """
        if page_number < 1 or page_number > len(self.doc):
            raise ValueError(f"Invalid page number: {page_number}")

        page = self.doc[page_number - 1]

        # Render page to pixmap
        mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 is default DPI
        pix = page.get_pixmap(matrix=mat)

        # Convert to PNG bytes
        img_bytes = pix.tobytes("png")
        return img_bytes

    def close(self):
        """Close the PDF document."""
        if hasattr(self, "doc") and self.doc:
            self.doc.close()
