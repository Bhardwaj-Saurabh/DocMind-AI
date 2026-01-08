"""
Base extractor interface for document extraction.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
import hashlib

from ..models import (
    DocumentMetadata,
    PageContent,
    DocumentFormat,
    ContentAnalysisResult,
    ProcessingStrategy,
)


class BaseExtractor(ABC):
    """
    Abstract base class for document extractors.

    All format-specific extractors (PDF, DOCX, PPT) must inherit from this class
    and implement the required methods.
    """

    def __init__(self, file_path: str):
        """
        Initialize extractor with file path.

        Args:
            file_path: Path to the document file
        """
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.document_id = self._generate_document_id()

    def _generate_document_id(self) -> str:
        """Generate unique document ID based on file path and content."""
        # Use file path + modification time for ID
        file_stat = self.file_path.stat()
        id_string = f"{self.file_path.absolute()}_{file_stat.st_mtime}"
        return hashlib.md5(id_string.encode()).hexdigest()

    @abstractmethod
    def get_format(self) -> DocumentFormat:
        """
        Get the document format.

        Returns:
            DocumentFormat enum value
        """
        pass

    @abstractmethod
    def get_metadata(self) -> DocumentMetadata:
        """
        Extract document metadata.

        Returns:
            DocumentMetadata object with document properties
        """
        pass

    @abstractmethod
    def get_page_count(self) -> int:
        """
        Get total number of pages in the document.

        Returns:
            Number of pages
        """
        pass

    @abstractmethod
    def extract_text(self, page_number: int) -> str:
        """
        Extract raw text from a specific page.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            Extracted text as string
        """
        pass

    @abstractmethod
    def extract_images(self, page_number: int) -> List[Dict[str, Any]]:
        """
        Extract embedded images from a specific page.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            List of image dictionaries with metadata
        """
        pass

    @abstractmethod
    def extract_tables(self, page_number: int) -> List[Dict[str, Any]]:
        """
        Extract tables from a specific page.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            List of table dictionaries with structure and data
        """
        pass

    @abstractmethod
    def analyze_page_content(self, page_number: int) -> ContentAnalysisResult:
        """
        Analyze page content and recommend processing strategy.

        This is the CRITICAL method that determines how each page should be processed.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            ContentAnalysisResult with analysis and strategy recommendation
        """
        pass

    @abstractmethod
    def render_page_as_image(self, page_number: int, dpi: int = 150) -> bytes:
        """
        Render a page as an image for vision API processing.

        Args:
            page_number: Page number (1-indexed)
            dpi: Resolution for rendering (default: 150)

        Returns:
            Image bytes (PNG format)
        """
        pass

    def extract_page(
        self, page_number: int, strategy: Optional[ProcessingStrategy] = None
    ) -> PageContent:
        """
        Extract content from a single page using the specified strategy.

        Args:
            page_number: Page number (1-indexed)
            strategy: Processing strategy to use (if None, will analyze first)

        Returns:
            PageContent object with extracted content
        """
        # Analyze content if strategy not provided
        if strategy is None:
            analysis = self.analyze_page_content(page_number)
            strategy = analysis.recommended_strategy
        else:
            analysis = self.analyze_page_content(page_number)

        # Extract content based on strategy
        page_id = f"{self.document_id}_page_{page_number}"

        # Start with text extraction for most strategies
        text = ""
        if strategy != ProcessingStrategy.VISION_PRIMARY:
            text = self.extract_text(page_number)

        # Extract other content
        images = []
        tables = []

        # Note: Actual vision processing and table extraction will be handled
        # by agents. This is just the basic extraction.
        if strategy in [
            ProcessingStrategy.HYBRID_SIMPLE,
            ProcessingStrategy.HYBRID_COMPLEX,
            ProcessingStrategy.VISION_PRIMARY,
        ]:
            images = self.extract_images(page_number)

        if strategy in [
            ProcessingStrategy.STRUCTURAL_PARSING,
            ProcessingStrategy.HYBRID_SIMPLE,
            ProcessingStrategy.HYBRID_COMPLEX,
        ]:
            tables = self.extract_tables(page_number)

        return PageContent(
            page_id=page_id,
            page_number=page_number,
            content_analysis=analysis,
            processing_strategy=strategy,
            text=text,
            word_count=len(text.split()) if text else 0,
            char_count=len(text) if text else 0,
        )

    def extract_all_pages(self) -> List[PageContent]:
        """
        Extract content from all pages in the document.

        Returns:
            List of PageContent objects, one per page
        """
        page_count = self.get_page_count()
        pages = []

        for page_num in range(1, page_count + 1):
            page_content = self.extract_page(page_num)
            pages.append(page_content)

        return pages

    def close(self):
        """Close the document and release resources."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
