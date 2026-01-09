"""
Data models for extracted content from documents.
"""

from pydantic import BaseModel, Field
from enum import Enum


class ImageType(str, Enum):
    """Type of image in document."""
    EMBEDDED = "embedded"  # Image file inserted into document
    CONSTRUCTED = "constructed"  # SmartArt, shapes, drawings
    CHART = "chart"  # Chart or graph
    DIAGRAM = "diagram"  # Diagram or flowchart
    PHOTO = "photo"  # Photograph
    LOGO = "logo"  # Logo or icon
    SCREENSHOT = "screenshot"  # Screenshot
    UNKNOWN = "unknown"


class ExtractedImage(BaseModel):
    """Metadata and content for an extracted image."""

    image_id: str = Field(..., description="Unique identifier for the image")
    page_number: int = Field(..., description="Page number where image appears")
    image_type: ImageType = Field(default=ImageType.UNKNOWN, description="Type of image")

    # Image data
    image_data: bytes | None = Field(default=None, description="Raw image bytes")
    image_path: str | None = Field(default=None, description="Path to saved image file")
    width: int | None = Field(default=None, description="Image width in pixels")
    height: int | None = Field(default=None, description="Image height in pixels")
    format: str | None = Field(default=None, description="Image format (PNG, JPEG, etc.)")

    # Vision API analysis
    description: str | None = Field(default=None, description="AI-generated description")
    extracted_text: str | None = Field(default=None, description="Text extracted from image (OCR)")
    confidence_score: float | None = Field(default=None, description="Confidence score (0-1)")

    # Position information
    bbox: dict[str, float] | None = Field(default=None, description="Bounding box {x, y, width, height}")

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractedImage":
        """Type-safe factory method from dictionary."""
        return cls(**data)

    @property
    def has_description(self) -> bool:
        """Check if image has AI-generated description."""
        return bool(self.description)

    @property
    def aspect_ratio(self) -> float | None:
        """Calculate image aspect ratio (width/height)."""
        if self.width and self.height and self.height > 0:
            return self.width / self.height
        return None

    class Config:
        arbitrary_types_allowed = True


class TableComplexity(str, Enum):
    """Complexity level of a table."""
    SIMPLE = "simple"  # Regular rows and columns
    COMPLEX = "complex"  # Merged cells, nested tables
    VERY_COMPLEX = "very_complex"  # Multiple levels of nesting


class ExtractedTable(BaseModel):
    """Structured data for an extracted table."""

    table_id: str = Field(..., description="Unique identifier for the table")
    page_number: int = Field(..., description="Page number where table appears")
    complexity: TableComplexity = Field(default=TableComplexity.SIMPLE, description="Table complexity")

    # Table structure
    rows: int = Field(..., description="Number of rows")
    columns: int = Field(..., description="Number of columns")
    has_header: bool = Field(default=True, description="Whether table has header row")
    has_merged_cells: bool = Field(default=False, description="Whether table has merged cells")

    # Table data
    data: list[list[str]] = Field(default_factory=list, description="Table data as 2D list")
    headers: list[str] | None = Field(default=None, description="Column headers")

    # Metadata
    title: str | None = Field(default=None, description="Table title or caption")
    extraction_method: str = Field(default="structural", description="Method used (structural, vision, hybrid)")
    confidence_score: float | None = Field(default=None, description="Confidence score (0-1)")

    # Position information
    bbox: dict[str, float] | None = Field(default=None, description="Bounding box {x, y, width, height}")

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractedTable":
        """Type-safe factory method from dictionary."""
        return cls(**data)

    @property
    def is_simple(self) -> bool:
        """Check if table has simple structure."""
        return (
            self.complexity == TableComplexity.SIMPLE
            and not self.has_merged_cells
        )

    @property
    def cell_count(self) -> int:
        """Get total number of cells in table."""
        return self.rows * self.columns

    def to_dict(self) -> list[dict[str, any]]:
        """Convert table to list of dictionaries (one per row)."""
        if not self.headers:
            return [{"col_{}".format(i): cell for i, cell in enumerate(row)} for row in self.data]
        return [{header: cell for header, cell in zip(self.headers, row)} for row in self.data]

    def to_csv(self) -> str:
        """Convert table to CSV format."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        if self.headers:
            writer.writerow(self.headers)
        writer.writerows(self.data)

        return output.getvalue()


class ExtractedChart(BaseModel):
    """Data for an extracted chart or graph."""

    chart_id: str = Field(..., description="Unique identifier for the chart")
    page_number: int = Field(..., description="Page number where chart appears")
    chart_type: str | None = Field(default=None, description="Type of chart (bar, line, pie, etc.)")

    # Chart data (if extractable)
    has_underlying_data: bool = Field(default=False, description="Whether chart has extractable data")
    data: dict[str, any] | None = Field(default=None, description="Chart data if available")

    # Vision API analysis
    description: str | None = Field(default=None, description="AI-generated description")
    insights: list[str] | None = Field(default=None, description="Key insights from chart")

    # Image of chart
    image: ExtractedImage | None = Field(default=None, description="Chart as image")

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractedChart":
        """Type-safe factory method from dictionary."""
        return cls(**data)

    @property
    def has_analysis(self) -> bool:
        """Check if chart has AI-generated analysis."""
        return bool(self.description or self.insights)

    class Config:
        arbitrary_types_allowed = True
