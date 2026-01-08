"""
Data models for document metadata and page content.
"""

from typing import Optional, List, Dict, Any
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
    title: Optional[str] = Field(default=None, description="Document title")
    author: Optional[str] = Field(default=None, description="Document author")
    subject: Optional[str] = Field(default=None, description="Document subject")
    keywords: Optional[List[str]] = Field(default=None, description="Document keywords")
    created_date: Optional[datetime] = Field(default=None, description="Document creation date")
    modified_date: Optional[datetime] = Field(default=None, description="Document modification date")

    # Structure
    total_pages: int = Field(..., description="Total number of pages")
    page_count: int = Field(..., description="Number of pages processed")

    # Extraction metadata
    extraction_date: datetime = Field(default_factory=datetime.now, description="When extraction occurred")
    extraction_version: str = Field(default="0.1.0", description="Version of extraction system")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PageContent(BaseModel):
    """Content extracted from a single page."""

    page_id: str = Field(..., description="Unique page identifier")
    page_number: int = Field(..., description="Page number (1-indexed)")

    # Content analysis
    content_analysis: Optional[ContentAnalysisResult] = Field(
        default=None, description="Analysis of page content"
    )
    processing_strategy: Optional[ProcessingStrategy] = Field(
        default=None, description="Strategy used for processing"
    )

    # Extracted content
    text: str = Field(default="", description="Extracted text content")
    images: List[ExtractedImage] = Field(default_factory=list, description="Extracted images")
    tables: List[ExtractedTable] = Field(default_factory=list, description="Extracted tables")
    charts: List[ExtractedChart] = Field(default_factory=list, description="Extracted charts")

    # Metadata
    word_count: int = Field(default=0, description="Number of words in text")
    char_count: int = Field(default=0, description="Number of characters in text")

    # Processing info
    processing_time: float = Field(default=0.0, description="Processing time in seconds")
    processing_cost: float = Field(default=0.0, description="Processing cost in USD")
    quality_score: float = Field(default=0.0, description="Quality score (0-1)")
    fallback_triggered: bool = Field(default=False, description="Whether fallback was used")

    # Raw data (optional)
    raw_html: Optional[str] = Field(default=None, description="Raw HTML if available")
    raw_xml: Optional[str] = Field(default=None, description="Raw XML if available")

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

    def get_summary(self) -> Dict[str, Any]:
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
    pages: List[PageContent] = Field(default_factory=list, description="Content from each page")

    # Aggregate content
    full_text: str = Field(default="", description="All text concatenated")
    all_images: List[ExtractedImage] = Field(default_factory=list, description="All images")
    all_tables: List[ExtractedTable] = Field(default_factory=list, description="All tables")
    all_charts: List[ExtractedChart] = Field(default_factory=list, description="All charts")

    # Processing statistics
    total_processing_time: float = Field(default=0.0, description="Total processing time in seconds")
    total_processing_cost: float = Field(default=0.0, description="Total processing cost in USD")
    average_quality_score: float = Field(default=0.0, description="Average quality score")

    # Strategy usage
    strategies_used: Dict[str, int] = Field(default_factory=dict, description="Count of each strategy used")
    fallbacks_triggered: int = Field(default=0, description="Number of fallbacks triggered")

    # Status
    success: bool = Field(default=True, description="Whether extraction was successful")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")

    def get_processing_report(self) -> Dict[str, Any]:
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

    def to_markdown(self) -> str:
        """Export as markdown."""
        lines = [f"# {self.metadata.title or self.metadata.file_name}\n"]

        for page in self.pages:
            lines.append(f"\n## Page {page.page_number}\n")
            lines.append(page.text)

            for table in page.tables:
                if table.title:
                    lines.append(f"\n### {table.title}\n")
                # Add markdown table
                if table.headers:
                    lines.append("| " + " | ".join(table.headers) + " |")
                    lines.append("| " + " | ".join(["---"] * len(table.headers)) + " |")
                for row in table.data:
                    lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)
