"""
LangGraph state management for document extraction workflow.
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated
from operator import add

from ..models import (
    DocumentMetadata,
    PageContent,
    ContentAnalysisResult,
    ProcessingStrategy,
    ExtractionResult,
)


class PageState(TypedDict, total=False):
    """State for a single page during processing."""

    page_number: int
    page_id: str

    # Content analysis
    content_analysis: Optional[ContentAnalysisResult]
    processing_strategy: Optional[ProcessingStrategy]

    # Extracted content
    text: str
    images: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]

    # Processing metadata
    processing_time: float
    processing_cost: float
    quality_score: float
    fallback_triggered: bool
    extraction_method: str  # "text", "vision", "hybrid"

    # Errors
    errors: List[str]


class DocumentState(TypedDict):
    """
    Main state for the document extraction workflow.

    This state flows through the LangGraph workflow and is modified by each agent.
    """

    # Document information
    document_id: str
    file_path: str
    metadata: Optional[DocumentMetadata]

    # Extractor instance (passed through but not serialized)
    extractor: Any  # BaseExtractor instance

    # Processing configuration
    config: Dict[str, Any]

    # Content analysis phase
    analyses_complete: bool
    page_analyses: Annotated[List[ContentAnalysisResult], add]  # Accumulated list

    # Processing phase
    pages_to_process: List[int]  # Page numbers to process
    pages_processed: Annotated[List[int], add]  # Completed page numbers
    page_results: Annotated[List[PageContent], add]  # Accumulated page results

    # Aggregated results
    total_cost: float
    total_time: float
    strategy_counts: Dict[str, int]

    # Final result
    extraction_result: Optional[ExtractionResult]

    # Status
    current_phase: str  # "init", "analysis", "processing", "synthesis", "complete"
    errors: Annotated[List[str], add]  # Accumulated errors
    warnings: Annotated[List[str], add]  # Accumulated warnings


def create_initial_state(
    file_path: str,
    extractor: Any,
    config: Optional[Dict[str, Any]] = None,
) -> DocumentState:
    """
    Create initial state for document extraction workflow.

    Args:
        file_path: Path to document file
        extractor: Extractor instance (PDFExtractor, DOCXExtractor, etc.)
        config: Configuration dictionary

    Returns:
        Initial DocumentState
    """
    return DocumentState(
        # Document info
        document_id=extractor.document_id if hasattr(extractor, "document_id") else "",
        file_path=file_path,
        metadata=None,
        # Extractor
        extractor=extractor,
        # Config
        config=config or {},
        # Analysis phase
        analyses_complete=False,
        page_analyses=[],
        # Processing phase
        pages_to_process=[],
        pages_processed=[],
        page_results=[],
        # Aggregation
        total_cost=0.0,
        total_time=0.0,
        strategy_counts={},
        # Result
        extraction_result=None,
        # Status
        current_phase="init",
        errors=[],
        warnings=[],
    )


def add_page_analysis(state: DocumentState, analysis: ContentAnalysisResult) -> DocumentState:
    """
    Add a page analysis result to the state.

    Args:
        state: Current document state
        analysis: Content analysis result for a page

    Returns:
        Updated state
    """
    state["page_analyses"].append(analysis)
    return state


def add_page_result(state: DocumentState, page_content: PageContent) -> DocumentState:
    """
    Add a processed page result to the state.

    Args:
        state: Current document state
        page_content: Extracted page content

    Returns:
        Updated state
    """
    state["page_results"].append(page_content)
    state["pages_processed"].append(page_content.page_number)

    # Update aggregates
    state["total_cost"] += page_content.processing_cost
    state["total_time"] += page_content.processing_time

    # Update strategy counts
    if page_content.processing_strategy:
        strategy = page_content.processing_strategy.value
        state["strategy_counts"][strategy] = state["strategy_counts"].get(strategy, 0) + 1

    return state


def add_error(state: DocumentState, error: str) -> DocumentState:
    """
    Add an error to the state.

    Args:
        state: Current document state
        error: Error message

    Returns:
        Updated state
    """
    state["errors"].append(error)
    return state


def add_warning(state: DocumentState, warning: str) -> DocumentState:
    """
    Add a warning to the state.

    Args:
        state: Current document state
        warning: Warning message

    Returns:
        Updated state
    """
    state["warnings"].append(warning)
    return state


def is_processing_complete(state: DocumentState) -> bool:
    """
    Check if all pages have been processed.

    Args:
        state: Current document state

    Returns:
        True if processing is complete
    """
    return len(state["pages_processed"]) >= len(state["pages_to_process"])


def get_next_page_to_process(state: DocumentState) -> Optional[int]:
    """
    Get the next page number to process.

    Args:
        state: Current document state

    Returns:
        Next page number or None if all pages processed
    """
    for page_num in state["pages_to_process"]:
        if page_num not in state["pages_processed"]:
            return page_num
    return None
