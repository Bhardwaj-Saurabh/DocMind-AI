"""
Agent implementations for DocMind-AI.

This module contains all the LangGraph agents used in the document extraction workflow:
- ContentAnalyzer: Analyzes page content and recommends processing strategy
- AdaptiveRouter: Routes pages to optimal processing pipelines
- TextExtractor: Fast text-only extraction agent
- StructuralParser: Parses tables and structured content
- VisionProcessor: Multimodal vision processing agent
- QualityValidator: Validates extraction quality and triggers fallbacks
- Synthesizer: Aggregates results from all agents
"""

# Implemented agents
from .content_analyzer import ContentAnalyzer
from .text_extractor import TextExtractor
from .vision_agent import VisionAgent
from .table_extractor import TableExtractor

# TODO: Implement remaining agents
# from .adaptive_router import AdaptiveRouter
# from .quality_validator import QualityValidator
# from .synthesizer import Synthesizer

__all__ = [
    "ContentAnalyzer",
    "TextExtractor",
    "VisionAgent",
    "TableExtractor",
]
