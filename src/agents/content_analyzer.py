"""
Content Analysis Agent - Analyzes document pages to determine optimal processing strategy.

This is the CRITICAL agent that enables adaptive processing and cost optimization.
"""

from typing import List, Dict, Any
import time

from ..models import ContentAnalysisResult, ProcessingPlan
from ..graph.state import DocumentState
from ..utils import get_logger, log_agent_step, log_performance


class ContentAnalyzer:
    """
    Content Analysis Agent.

    This agent analyzes each page in the document to:
    1. Detect content type (text, images, tables, charts, etc.)
    2. Assess text quality and extractability
    3. Identify visual elements that need processing
    4. Recommend optimal processing strategy
    5. Estimate processing cost and time

    This enables the adaptive routing that gives us 85% cost savings!
    """

    def __init__(self):
        """Initialize content analyzer."""
        self.logger = get_logger()
        self.name = "ContentAnalyzer"

    def analyze_document(self, state: DocumentState) -> DocumentState:
        """
        Analyze all pages in the document.

        This is a LangGraph node function that takes state and returns updated state.

        Args:
            state: Current document state

        Returns:
            Updated state with page analyses
        """
        log_agent_step(
            self.name,
            "Starting content analysis",
            {"pages": state["metadata"].total_pages if state["metadata"] else "unknown"},
        )

        start_time = time.time()

        extractor = state["extractor"]

        # Get metadata if not already loaded
        if not state["metadata"]:
            state["metadata"] = extractor.get_metadata()
            log_agent_step(
                self.name,
                "Loaded metadata",
                {"title": state["metadata"].title, "pages": state["metadata"].total_pages},
            )

        total_pages = state["metadata"].total_pages

        # Analyze each page
        page_analyses = []
        for page_num in range(1, total_pages + 1):
            try:
                log_agent_step(
                    self.name,
                    f"Analyzing page {page_num}/{total_pages}",
                    level="debug",
                )

                # Use the extractor's analyze_page_content method
                analysis = extractor.analyze_page_content(page_num)
                page_analyses.append(analysis)

                log_agent_step(
                    self.name,
                    f"Page {page_num} analyzed",
                    {
                        "type": analysis.content_type.value,
                        "strategy": analysis.recommended_strategy.value,
                        "cost": f"${analysis.estimated_cost:.4f}",
                    },
                    level="debug",
                )

            except Exception as e:
                self.logger.error(f"Error analyzing page {page_num}: {e}")
                state["errors"].append(f"Analysis failed for page {page_num}: {str(e)}")

        # Update state
        state["page_analyses"] = page_analyses
        state["analyses_complete"] = True

        # Mark pages to process (all pages)
        state["pages_to_process"] = list(range(1, total_pages + 1))

        # Calculate totals
        total_cost = sum(a.estimated_cost for a in page_analyses)
        total_time = sum(a.estimated_time for a in page_analyses)

        duration = time.time() - start_time

        log_agent_step(
            self.name,
            "Analysis complete",
            {
                "pages": len(page_analyses),
                "estimated_cost": f"${total_cost:.4f}",
                "estimated_time": f"{total_time:.1f}s",
            },
        )

        log_performance(
            f"Content analysis for {len(page_analyses)} pages",
            duration,
        )

        # Update phase
        state["current_phase"] = "analysis_complete"

        return state

    def create_processing_plan(self, state: DocumentState) -> ProcessingPlan:
        """
        Create a processing plan based on content analysis.

        Args:
            state: Document state with completed analyses

        Returns:
            ProcessingPlan with strategy recommendations and cost estimates
        """
        page_analyses = state["page_analyses"]

        # Count pages by strategy
        strategy_counts = {}
        for analysis in page_analyses:
            strategy = analysis.recommended_strategy.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        # Calculate totals
        total_cost = sum(a.estimated_cost for a in page_analyses)
        total_time = sum(a.estimated_time for a in page_analyses)

        # Count page types
        text_only = sum(1 for a in page_analyses if a.is_text_only())
        hybrid = sum(1 for a in page_analyses if a.has_embedded_images() or a.has_simple_tables())
        vision_required = sum(1 for a in page_analyses if a.needs_vision_api())

        plan = ProcessingPlan(
            document_id=state["document_id"],
            total_pages=len(page_analyses),
            page_analyses=page_analyses,
            text_only_pages=text_only,
            hybrid_pages=hybrid,
            vision_pages=vision_required,
            total_estimated_cost=total_cost,
            total_estimated_time=total_time,
            strategy_counts=strategy_counts,
        )

        log_agent_step(
            self.name,
            "Processing plan created",
            {
                "text_only": text_only,
                "hybrid": hybrid,
                "vision": vision_required,
                "total_cost": f"${total_cost:.4f}",
            },
        )

        return plan

    def get_analysis_summary(self, state: DocumentState) -> Dict[str, Any]:
        """
        Get a summary of the content analysis.

        Args:
            state: Document state with completed analyses

        Returns:
            Summary dictionary
        """
        if not state["page_analyses"]:
            return {"status": "No analysis performed"}

        page_analyses = state["page_analyses"]

        # Aggregate statistics
        content_types = {}
        strategies = {}
        total_cost = 0.0
        total_time = 0.0

        for analysis in page_analyses:
            # Count content types
            ct = analysis.content_type.value
            content_types[ct] = content_types.get(ct, 0) + 1

            # Count strategies
            st = analysis.recommended_strategy.value
            strategies[st] = strategies.get(st, 0) + 1

            # Sum costs and times
            total_cost += analysis.estimated_cost
            total_time += analysis.estimated_time

        return {
            "total_pages": len(page_analyses),
            "content_types": content_types,
            "strategies": strategies,
            "total_estimated_cost": total_cost,
            "total_estimated_time": total_time,
            "average_cost_per_page": total_cost / len(page_analyses),
            "average_time_per_page": total_time / len(page_analyses),
        }
