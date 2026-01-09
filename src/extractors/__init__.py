"""
Document format extractors for DocMind-AI.

This module provides format-specific extractors that handle document loading
and basic content extraction:
- PDFExtractor: Extracts content from PDF files using PyMuPDF
- DOCXExtractor: Extracts content from Word documents using python-docx
- PPTExtractor: Extracts content from PowerPoint files using python-pptx
- BaseExtractor: Abstract base class for all extractors
- ExtractorFactory: Factory for creating extractors based on file type
"""

# Base extractor
from .base import BaseExtractor

# Format-specific extractors
from .pdf_extractor import PDFExtractor
# from .docx_extractor import DOCXExtractor  # TODO: Implement
# from .ppt_extractor import PPTExtractor  # TODO: Implement

# Factory
from .factory import ExtractorFactory, create_extractor

__all__ = [
    "BaseExtractor",
    "PDFExtractor",
    # "DOCXExtractor",
    # "PPTExtractor",
    "ExtractorFactory",
    "create_extractor",
]
