"""
LLM prompt templates for DocMind-AI.

Prompt templates for different extraction tasks:
- TEXT_EXTRACTION_PROMPT: Text extraction prompt
- TABLE_EXTRACTION_PROMPT: Table extraction prompt
- IMAGE_ANALYSIS_PROMPT: Image analysis prompt
- QUALITY_VALIDATION_PROMPT: Quality validation prompt
"""

# Vision prompts
from .vision_prompts import (
    FULL_PAGE_ANALYSIS_PROMPT,
    IMAGE_ANALYSIS_PROMPT,
    CHART_ANALYSIS_PROMPT,
    TABLE_EXTRACTION_PROMPT,
    SCANNED_DOCUMENT_PROMPT,
    DIAGRAM_ANALYSIS_PROMPT,
    FORM_EXTRACTION_PROMPT,
    SMARTART_PROMPT,
    QUALITY_CHECK_PROMPT,
    get_prompt_for_content_type,
    format_page_analysis_prompt,
    format_quality_check_prompt,
)

__all__ = [
    "FULL_PAGE_ANALYSIS_PROMPT",
    "IMAGE_ANALYSIS_PROMPT",
    "CHART_ANALYSIS_PROMPT",
    "TABLE_EXTRACTION_PROMPT",
    "SCANNED_DOCUMENT_PROMPT",
    "DIAGRAM_ANALYSIS_PROMPT",
    "FORM_EXTRACTION_PROMPT",
    "SMARTART_PROMPT",
    "QUALITY_CHECK_PROMPT",
    "get_prompt_for_content_type",
    "format_page_analysis_prompt",
    "format_quality_check_prompt",
]
