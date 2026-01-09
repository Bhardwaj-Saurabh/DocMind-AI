"""
Data models for document metadata and page content.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from .extracted_content import ExtractedImage, ExtractedTable, ExtractedChart
from .analysis import ContentAnalysisResult, ProcessingStrategy


class DocumentFormat(str, Enum):
    """Supported document formats."""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    UNKNOWN = "unknown"


class DocumentMetadata(BaseModel):
    """Metadata for a document."""

    # Basic information
    document_id: str = Field(..., description="Unique document identifier")
    file_path: str = Field(..., description="Path to source document")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    format: DocumentFormat = Field(..., description="Document format")

    # Document properties
    title: str | None = Field(default=None, description="Document title")
    author: str | None = Field(default=None, description="Document author")
    subject: str | None = Field(default=None, description="Document subject")
    keywords: list[str] | None = Field(default=None, description="Document keywords")
    created_date: datetime | None = Field(default=None, description="Document creation date")
    modified_date: datetime | None = Field(default=None, description="Document modification date")

    # Structure
    total_pages: int = Field(..., description="Total number of pages")
    page_count: int = Field(..., description="Number of pages processed")

    # Extraction metadata
    extraction_date: datetime = Field(default_factory=datetime.now, description="When extraction occurred")
    extraction_version: str = Field(default="0.1.0", description="Version of extraction system")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentMetadata":
        """Type-safe factory method from dictionary."""
        return cls(**data)


class PageContent(BaseModel):
    """Content extracted from a single page."""

    page_id: str = Field(..., description="Unique page identifier")
    page_number: int = Field(..., description="Page number (1-indexed)")

    # Content analysis
    content_analysis: ContentAnalysisResult | None = Field(
        default=None, description="Analysis of page content"
    )
    processing_strategy: ProcessingStrategy | None = Field(
        default=None, description="Strategy used for processing"
    )

    # Extracted content
    text: str = Field(default="", description="Extracted text content")
    images: list[ExtractedImage] = Field(default_factory=list, description="Extracted images")
    tables: list[ExtractedTable] = Field(default_factory=list, description="Extracted tables")
    charts: list[ExtractedChart] = Field(default_factory=list, description="Extracted charts")

    # Metadata
    word_count: int = Field(default=0, description="Number of words in text")
    char_count: int = Field(default=0, description="Number of characters in text")

    # Processing info
    processing_time: float = Field(default=0.0, description="Processing time in seconds")
    processing_cost: float = Field(default=0.0, description="Processing cost in USD")
    quality_score: float = Field(default=0.0, description="Quality score (0-1)")
    fallback_triggered: bool = Field(default=False, description="Whether fallback was used")

    # Raw data (optional)
    raw_html: str | None = Field(default=None, description="Raw HTML if available")
    raw_xml: str | None = Field(default=None, description="Raw XML if available")

    @classmethod
    def from_dict(cls, data: dict) -> "PageContent":
        """Type-safe factory method from dictionary."""
        return cls(**data)

    @property
    def has_content(self) -> bool:
        """Check if page has any extracted content."""
        return bool(self.text or self.images or self.tables or self.charts)

    @property
    def content_types(self) -> list[str]:
        """Get list of content types present on this page."""
        types = []
        if self.text:
            types.append("text")
        if self.images:
            types.append("images")
        if self.tables:
            types.append("tables")
        if self.charts:
            types.append("charts")
        return types

    def get_all_text(self) -> str:
        """Get all text including from tables."""
        text_parts = [self.text]

        # Add text from tables
        for table in self.tables:
            if table.title:
                text_parts.append(f"\n{table.title}\n")
            for row in table.data:
                text_parts.append(" | ".join(row))

        return "\n".join(text_parts)

    def get_summary(self) -> dict[str, any]:
        """Get summary of page content."""
        return {
            "page_number": self.page_number,
            "word_count": self.word_count,
            "images_count": len(self.images),
            "tables_count": len(self.tables),
            "charts_count": len(self.charts),
            "processing_time": self.processing_time,
            "processing_cost": self.processing_cost,
            "quality_score": self.quality_score,
        }


class ExtractionResult(BaseModel):
    """Complete extraction result for a document."""

    # Document information
    metadata: DocumentMetadata = Field(..., description="Document metadata")

    # Page content
    pages: list[PageContent] = Field(default_factory=list, description="Content from each page")

    # Aggregate content
    full_text: str = Field(default="", description="All text concatenated")
    all_images: list[ExtractedImage] = Field(default_factory=list, description="All images")
    all_tables: list[ExtractedTable] = Field(default_factory=list, description="All tables")
    all_charts: list[ExtractedChart] = Field(default_factory=list, description="All charts")

    # Processing statistics
    total_processing_time: float = Field(default=0.0, description="Total processing time in seconds")
    total_processing_cost: float = Field(default=0.0, description="Total processing cost in USD")
    average_quality_score: float = Field(default=0.0, description="Average quality score")

    # Strategy usage
    strategies_used: dict[str, int] = Field(default_factory=dict, description="Count of each strategy used")
    fallbacks_triggered: int = Field(default=0, description="Number of fallbacks triggered")

    # Status
    success: bool = Field(default=True, description="Whether extraction was successful")
    errors: list[str] = Field(default_factory=list, description="List of errors encountered")
    warnings: list[str] = Field(default_factory=list, description="List of warnings")

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractionResult":
        """Type-safe factory method from dictionary."""
        return cls(**data)

    @property
    def total_words(self) -> int:
        """Get total word count across all pages."""
        return sum(p.word_count for p in self.pages)

    @property
    def total_content_items(self) -> int:
        """Get total count of all content items."""
        return len(self.all_images) + len(self.all_tables) + len(self.all_charts)

    @property
    def average_page_cost(self) -> float:
        """Get average cost per page."""
        return self.total_processing_cost / len(self.pages) if self.pages else 0.0

    def get_processing_report(self) -> dict[str, any]:
        """Generate processing report."""
        return {
            "document": {
                "file_name": self.metadata.file_name,
                "format": self.metadata.format,
                "total_pages": self.metadata.total_pages,
            },
            "content_summary": {
                "total_words": sum(p.word_count for p in self.pages),
                "total_images": len(self.all_images),
                "total_tables": len(self.all_tables),
                "total_charts": len(self.all_charts),
            },
            "processing": {
                "total_time": f"{self.total_processing_time:.2f}s",
                "total_cost": f"${self.total_processing_cost:.4f}",
                "average_time_per_page": f"{self.total_processing_time / len(self.pages):.2f}s"
                if self.pages
                else "0s",
                "average_cost_per_page": f"${self.total_processing_cost / len(self.pages):.4f}"
                if self.pages
                else "$0",
            },
            "quality": {
                "average_quality_score": f"{self.average_quality_score:.2f}",
                "fallbacks_triggered": self.fallbacks_triggered,
            },
            "strategies": self.strategies_used,
            "status": {
                "success": self.success,
                "errors": len(self.errors),
                "warnings": len(self.warnings),
            },
        }

    def to_text(self) -> str:
        """Export as plain text."""
        return self.full_text

    def to_markdown(
        self,
        include_metadata: bool = True,
        include_page_numbers: bool = True,
        preserve_hierarchy: bool = True
    ) -> str:
        """
        Export as hierarchical markdown optimized for RAG applications.

        Uses the comprehensive MarkdownFormatter to:
        - Preserve document hierarchy for embeddings
        - Convert all non-text content to detailed text descriptions
        - Format tables as markdown tables
        - Include page markers for chunking

        Args:
            include_metadata: Whether to include document metadata
            include_page_numbers: Whether to include page number markers
            preserve_hierarchy: Whether to preserve text hierarchy (headings)

        Returns:
            Formatted markdown string suitable for RAG/embedding
        """
        from ..formatters import format_to_markdown
        return format_to_markdown(
            self,
            include_metadata=include_metadata,
            include_page_numbers=include_page_numbers,
            preserve_hierarchy=preserve_hierarchy
        )
