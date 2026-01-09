"""
Data models for content analysis and processing strategies.
"""

from pydantic import BaseModel, Field
from enum import Enum


class ContentType(str, Enum):
    """Type of content on a page."""
    PURE_TEXT = "pure_text"  # 90%+ text, no visual elements
    TEXT_WITH_IMAGES = "text_with_images"  # Text + embedded images
    TEXT_WITH_TABLES = "text_with_tables"  # Text + tables
    TEXT_WITH_CHARTS = "text_with_charts"  # Text + charts/graphs
    MIXED_CONTENT = "mixed_content"  # Mix of text, images, tables
    VISUAL_HEAVY = "visual_heavy"  # Primarily visual (SmartArt, diagrams)
    FORM = "form"  # Form with input fields
    SCANNED = "scanned"  # Scanned document (image-based)


class ProcessingStrategy(str, Enum):
    """Strategy for processing a page."""
    TEXT_ONLY = "text_only"  # Direct text extraction only
    STRUCTURAL_PARSING = "structural_parsing"  # Parse structure (tables, etc.)
    HYBRID_SIMPLE = "hybrid_simple"  # Text + simple visual processing
    HYBRID_COMPLEX = "hybrid_complex"  # Text + complex visual processing
    VISION_PRIMARY = "vision_primary"  # Vision API as primary method
    VISION_FALLBACK = "vision_fallback"  # Vision API as fallback
    RENDER_AND_VISION = "render_and_vision"  # Render page as image + vision


class TextQuality(str, Enum):
    """Quality of extractable text."""
    HIGH = "high"  # Clean, extractable text
    MEDIUM = "medium"  # Some extraction issues
    LOW = "low"  # Poor quality or little text
    NONE = "none"  # No extractable text (scanned image)


class TableInfo(BaseModel):
    """Information about tables on a page."""
    count: int = Field(default=0, description="Number of tables")
    complexity: str = Field(default="none", description="Overall complexity (none, simple, complex)")
    has_merged_cells: bool = Field(default=False, description="Whether any table has merged cells")
    has_nested_tables: bool = Field(default=False, description="Whether any table is nested")


class ContentAnalysisResult(BaseModel):
    """Result of content analysis for a page."""

    page_id: str = Field(..., description="Page identifier")
    page_number: int = Field(..., description="Page number")

    # Content classification
    content_type: ContentType = Field(..., description="Primary content type")
    text_quality: TextQuality = Field(..., description="Quality of extractable text")

    # Content components
    text_length: int = Field(default=0, description="Length of extractable text")
    embedded_images_count: int = Field(default=0, description="Number of embedded images")
    constructed_graphics_count: int = Field(default=0, description="Number of constructed graphics")
    charts_count: int = Field(default=0, description="Number of charts/graphs")
    table_info: TableInfo = Field(default_factory=TableInfo, description="Table information")

    # Layout analysis
    layout_complexity: str = Field(default="simple", description="Layout complexity (simple, medium, complex)")
    is_scanned: bool = Field(default=False, description="Whether page appears to be scanned")
    requires_rendering: bool = Field(default=False, description="Whether page needs to be rendered as image")

    # Processing recommendation
    recommended_strategy: ProcessingStrategy = Field(..., description="Recommended processing strategy")
    estimated_cost: float = Field(default=0.0, description="Estimated processing cost in USD")
    estimated_time: float = Field(default=0.0, description="Estimated processing time in seconds")

    # Confidence
    confidence_score: float = Field(default=1.0, description="Confidence in analysis (0-1)")

    def is_text_only(self) -> bool:
        """Check if page is text-only."""
        return (
            self.content_type == ContentType.PURE_TEXT
            and self.embedded_images_count == 0
            and self.constructed_graphics_count == 0
            and self.table_info.count == 0
        )

    def has_simple_tables(self) -> bool:
        """Check if page has simple tables."""
        return (
            self.table_info.count > 0
            and self.table_info.complexity == "simple"
            and not self.table_info.has_merged_cells
        )

    def has_complex_visuals(self) -> bool:
        """Check if page has complex visual elements."""
        return (
            self.constructed_graphics_count > 0
            or self.charts_count > 0
            or self.table_info.complexity == "complex"
            or self.requires_rendering
        )

    def has_embedded_images(self) -> bool:
        """Check if page has embedded images."""
        return self.embedded_images_count > 0

    def needs_vision_api(self) -> bool:
        """Determine if vision API is needed."""
        return (
            self.recommended_strategy
            in [
                ProcessingStrategy.VISION_PRIMARY,
                ProcessingStrategy.RENDER_AND_VISION,
                ProcessingStrategy.HYBRID_COMPLEX,
            ]
            or self.is_scanned
            or self.has_complex_visuals()
        )


class ProcessingPlan(BaseModel):
    """Complete processing plan for a document."""

    document_id: str = Field(..., description="Document identifier")
    total_pages: int = Field(..., description="Total number of pages")

    # Per-page analysis
    page_analyses: list[ContentAnalysisResult] = Field(default_factory=list, description="Analysis for each page")

    # Aggregate statistics
    text_only_pages: int = Field(default=0, description="Number of text-only pages")
    hybrid_pages: int = Field(default=0, description="Number of hybrid pages")
    vision_pages: int = Field(default=0, description="Number of vision-required pages")

    # Cost estimates
    total_estimated_cost: float = Field(default=0.0, description="Total estimated cost in USD")
    total_estimated_time: float = Field(default=0.0, description="Total estimated time in seconds")

    # Strategy breakdown
    strategy_counts: dict[str, int] = Field(default_factory=dict, description="Count of each strategy")

    @classmethod
    def from_dict(cls, data: dict) -> "ProcessingPlan":
        """Type-safe factory method from dictionary."""
        return cls(**data)

    @property
    def average_cost_per_page(self) -> float:
        """Get average estimated cost per page."""
        return self.total_estimated_cost / self.total_pages if self.total_pages > 0 else 0.0

    @property
    def vision_percentage(self) -> float:
        """Get percentage of pages requiring vision API."""
        return (self.vision_pages / self.total_pages * 100) if self.total_pages > 0 else 0.0

    def get_cost_breakdown(self) -> dict[str, float]:
        """Get cost breakdown by strategy."""
        breakdown = {}
        for analysis in self.page_analyses:
            strategy = analysis.recommended_strategy.value
            breakdown[strategy] = breakdown.get(strategy, 0.0) + analysis.estimated_cost
        return breakdown

    def get_pages_by_strategy(self, strategy: ProcessingStrategy) -> list[int]:
        """Get list of page numbers using a specific strategy."""
        return [
            analysis.page_number
            for analysis in self.page_analyses
            if analysis.recommended_strategy == strategy
        ]
