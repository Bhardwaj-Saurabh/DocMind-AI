"""
LangGraph workflow for document extraction.

This module defines the main extraction workflow using LangGraph.
"""

from typing import Optional
from langgraph.graph import StateGraph, END

from .state import DocumentState, create_initial_state
from ..agents import ContentAnalyzer, TextExtractor, VisionAgent, TableExtractor
from ..models import ExtractionResult
from ..utils import get_logger, log_agent_step, get_config


class ExtractionWorkflow:
    """
    Main document extraction workflow using LangGraph.

    This workflow orchestrates the extraction process:
    1. Content Analysis: Analyze all pages to determine strategies
    2. Text Extraction: Process text-only pages (fast & cheap)
    3. Table Extraction: Extract tables with rule-based + vision fallback
    4. Vision Processing: Process visual content (images, charts, scanned docs)
    5. Synthesis: Combine all results

    Currently implements:
    - Content Analysis ✅
    - Text Extraction ✅
    - Table Extraction ✅
    - Vision Processing ✅

    TODO: Quality validation, parallel processing
    """

    def __init__(self, enable_vision: bool = True):
        """
        Initialize the extraction workflow.

        Args:
            enable_vision: Whether to enable vision processing (requires API key)
        """
        self.logger = get_logger()
        self.config = get_config()

        # Check if we can enable vision
        if enable_vision and not self.config.openai_api_key:
            self.logger.warning("OpenAI API key not found, disabling vision processing")
            enable_vision = False

        self.enable_vision = enable_vision

        # Initialize agents
        self.content_analyzer = ContentAnalyzer()
        self.text_extractor = TextExtractor()
        self.table_extractor = TableExtractor(enable_vision_fallback=enable_vision)

        if self.enable_vision:
            self.vision_agent = VisionAgent()
            log_agent_step("Workflow", "Vision processing enabled")
        else:
            self.vision_agent = None
            log_agent_step("Workflow", "Vision processing disabled (no API key)")

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Returns:
            Compiled state graph
        """
        # Create the graph
        workflow = StateGraph(DocumentState)

        # Add nodes
        workflow.add_node("analyze_content", self._analyze_content_node)
        workflow.add_node("extract_text", self._extract_text_node)

        if self.enable_vision:
            workflow.add_node("process_vision", self._process_vision_node)

        workflow.add_node("finalize", self._finalize_node)

        # Define the flow
        workflow.set_entry_point("analyze_content")

        # After analysis, go to text extraction
        workflow.add_edge("analyze_content", "extract_text")

        # After text extraction, go to vision (if enabled) or finalize
        if self.enable_vision:
            workflow.add_edge("extract_text", "process_vision")
            workflow.add_edge("process_vision", "finalize")
        else:
            workflow.add_edge("extract_text", "finalize")

        # Finalize leads to end
        workflow.add_edge("finalize", END)

        # Compile the graph
        return workflow.compile()

    def _analyze_content_node(self, state: DocumentState) -> DocumentState:
        """
        Node: Analyze content of all pages.

        Args:
            state: Current state

        Returns:
            Updated state with analyses
        """
        log_agent_step("Workflow", "Entering analyze_content node")
        state = self.content_analyzer.analyze_document(state)
        state["current_phase"] = "analysis_complete"
        return state

    def _extract_text_node(self, state: DocumentState) -> DocumentState:
        """
        Node: Extract text from text-only pages.

        Args:
            state: Current state

        Returns:
            Updated state with text extraction results
        """
        log_agent_step("Workflow", "Entering extract_text node")
        state = self.text_extractor.process_node(state)
        state["current_phase"] = "text_extraction_complete"
        return state

    def _process_vision_node(self, state: DocumentState) -> DocumentState:
        """
        Node: Process pages with vision API.

        Args:
            state: Current state

        Returns:
            Updated state with vision processing results
        """
        log_agent_step("Workflow", "Entering process_vision node")

        if self.vision_agent:
            state = self.vision_agent.process_node(state)
            state["current_phase"] = "vision_processing_complete"
        else:
            log_agent_step("Workflow", "Vision agent not available, skipping")

        return state

    def _finalize_node(self, state: DocumentState) -> DocumentState:
        """
        Node: Finalize extraction and create result.

        Args:
            state: Current state

        Returns:
            Updated state with final result
        """
        log_agent_step("Workflow", "Entering finalize node")

        # Create extraction result
        metadata = state["metadata"]
        page_results = state["page_results"]

        # Combine all text
        full_text = "\n\n".join([p.text for p in page_results])

        # Calculate average quality score
        avg_quality = (
            sum(p.quality_score for p in page_results) / len(page_results) if page_results else 0.0
        )

        # Create result
        extraction_result = ExtractionResult(
            metadata=metadata,
            pages=page_results,
            full_text=full_text,
            all_images=[],  # TODO: Collect from pages
            all_tables=[],  # TODO: Collect from pages
            all_charts=[],  # TODO: Collect from pages
            total_processing_time=state["total_time"],
            total_processing_cost=state["total_cost"],
            average_quality_score=avg_quality,
            strategies_used=state["strategy_counts"],
            fallbacks_triggered=0,  # TODO: Track fallbacks
            success=len(state["errors"]) == 0,
            errors=state["errors"],
            warnings=state["warnings"],
        )

        state["extraction_result"] = extraction_result
        state["current_phase"] = "complete"

        log_agent_step(
            "Workflow",
            "Extraction complete",
            {
                "pages": len(page_results),
                "cost": f"${state['total_cost']:.4f}",
                "time": f"{state['total_time']:.2f}s",
            },
        )

        return state

    def extract(
        self,
        file_path: str,
        extractor: any,
        config: Optional[dict] = None,
    ) -> ExtractionResult:
        """
        Extract content from a document.

        Args:
            file_path: Path to document file
            extractor: Document extractor instance (PDFExtractor, etc.)
            config: Optional configuration dictionary

        Returns:
            ExtractionResult with all extracted content
        """
        log_agent_step(
            "Workflow",
            "Starting document extraction",
            {"file": file_path},
        )

        # Create initial state
        initial_state = create_initial_state(file_path, extractor, config)

        # Run the workflow
        final_state = self.graph.invoke(initial_state)

        # Return the extraction result
        result = final_state["extraction_result"]

        if not result:
            raise RuntimeError("Extraction failed: No result produced")

        return result

    async def extract_async(
        self,
        file_path: str,
        extractor: any,
        config: Optional[dict] = None,
    ) -> ExtractionResult:
        """
        Extract content from a document asynchronously.

        Args:
            file_path: Path to document file
            extractor: Document extractor instance
            config: Optional configuration dictionary

        Returns:
            ExtractionResult with all extracted content
        """
        # Create initial state
        initial_state = create_initial_state(file_path, extractor, config)

        # Run the workflow asynchronously
        final_state = await self.graph.ainvoke(initial_state)

        # Return the extraction result
        result = final_state["extraction_result"]

        if not result:
            raise RuntimeError("Extraction failed: No result produced")

        return result


def create_extraction_workflow() -> ExtractionWorkflow:
    """
    Factory function to create an extraction workflow.

    Returns:
        Configured ExtractionWorkflow instance
    """
    return ExtractionWorkflow()
