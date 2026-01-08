"""
Data models for DocMind-AI.

Pydantic models for type-safe data structures:
- DocumentMetadata: Document-level metadata
- PageContent: Page-level content structure
- ExtractedImage: Image metadata and content
- ExtractedTable: Table structure and data
- ContentAnalysisResult: Content analysis output
- ProcessingStrategy: Strategy recommendation
- ExtractionResult: Final extraction result
"""

# Document models
from .document import (
    DocumentMetadata,
    PageContent,
    ExtractionResult,
    DocumentFormat,
)

# Extracted content models
from .extracted_content import (
    ExtractedImage,
    ExtractedTable,
    ExtractedChart,
    ImageType,
    TableComplexity,
)

# Analysis models
from .analysis import (
    ContentAnalysisResult,
    ProcessingPlan,
    ContentType,
    ProcessingStrategy,
    TextQuality,
    TableInfo,
)

__all__ = [
    # Document models
    "DocumentMetadata",
    "PageContent",
    "ExtractionResult",
    "DocumentFormat",
    # Extracted content
    "ExtractedImage",
    "ExtractedTable",
    "ExtractedChart",
    "ImageType",
    "TableComplexity",
    # Analysis
    "ContentAnalysisResult",
    "ProcessingPlan",
    "ContentType",
    "ProcessingStrategy",
    "TextQuality",
    "TableInfo",
]
