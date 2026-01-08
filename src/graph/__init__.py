"""
LangGraph workflow definitions for DocMind-AI.

This module contains the LangGraph state machines and workflow orchestration:
- ExtractionWorkflow: Main document extraction workflow
- State: Graph state management
- Router: Conditional routing logic
"""

# State management
from .state import (
    DocumentState,
    PageState,
    create_initial_state,
    add_page_analysis,
    add_page_result,
    is_processing_complete,
)

# Workflow
from .extraction_workflow import ExtractionWorkflow, create_extraction_workflow

__all__ = [
    # State
    "DocumentState",
    "PageState",
    "create_initial_state",
    "add_page_analysis",
    "add_page_result",
    "is_processing_complete",
    # Workflow
    "ExtractionWorkflow",
    "create_extraction_workflow",
]
