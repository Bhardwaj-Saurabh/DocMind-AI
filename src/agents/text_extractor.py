"""
Text Extraction Agent - Fast, cheap text-only extraction.

This agent handles pages with pure text content - the fastest and cheapest strategy.
"""

from typing import Optional
import time

from ..models import PageContent, ProcessingStrategy
from ..graph.state import DocumentState
from ..utils import get_logger, log_agent_step, log_cost, log_performance


class TextExtractor:
    """
    Text Extraction Agent.

    This agent provides fast, cost-effective text extraction for pages
    that contain primarily text without complex visual elements.

    Strategy: TEXT_ONLY
    Cost: ~$0.001 per page
    Speed: ~0.3 seconds per page
    """

    def __init__(self):
        """Initialize text extractor."""
        self.logger = get_logger()
        self.name = "TextExtractor"

    def extract_page(
        self,
        page_number: int,
        state: DocumentState,
    ) -> PageContent:
        """
        Extract text content from a single page.

        Args:
            page_number: Page number to extract (1-indexed)
            state: Current document state

        Returns:
            PageContent with extracted text
        """
        log_agent_step(
            self.name,
            f"Extracting text from page {page_number}",
            level="debug",
        )

        start_time = time.time()

        extractor = state["extractor"]

        try:
            # Get the content analysis for this page
            analysis = None
            for a in state["page_analyses"]:
                if a.page_number == page_number:
                    analysis = a
                    break

            # Extract text
            text = extractor.extract_text(page_number)

            # Calculate metrics
            word_count = len(text.split()) if text else 0
            char_count = len(text) if text else 0

            processing_time = time.time() - start_time

            # Cost for text extraction (very cheap)
            processing_cost = 0.001  # $0.001 per page

            # Create page content
            page_id = f"{state['document_id']}_page_{page_number}"

            page_content = PageContent(
                page_id=page_id,
                page_number=page_number,
                content_analysis=analysis,
                processing_strategy=ProcessingStrategy.TEXT_ONLY,
                text=text,
                images=[],
                tables=[],
                charts=[],
                word_count=word_count,
                char_count=char_count,
                processing_time=processing_time,
                processing_cost=processing_cost,
                quality_score=0.95,  # High quality for direct text extraction
                fallback_triggered=False,
            )

            log_cost(
                f"Text extraction (page {page_number})",
                processing_cost,
                {"words": word_count},
            )

            log_performance(
                f"Text extraction (page {page_number})",
                processing_time,
                {"words": word_count},
            )

            return page_content

        except Exception as e:
            self.logger.error(f"Error extracting text from page {page_number}: {e}")

            # Return empty page content with error
            page_id = f"{state['document_id']}_page_{page_number}"
            return PageContent(
                page_id=page_id,
                page_number=page_number,
                text="",
                word_count=0,
                char_count=0,
                processing_time=time.time() - start_time,
                processing_cost=0.0,
                quality_score=0.0,
                fallback_triggered=False,
            )

    def extract_pages(
        self,
        page_numbers: list[int],
        state: DocumentState,
    ) -> list[PageContent]:
        """
        Extract text from multiple pages.

        Args:
            page_numbers: List of page numbers to extract
            state: Current document state

        Returns:
            List of PageContent objects
        """
        log_agent_step(
            self.name,
            f"Extracting text from {len(page_numbers)} pages",
        )

        results = []
        for page_num in page_numbers:
            page_content = self.extract_page(page_num, state)
            results.append(page_content)

        log_agent_step(
            self.name,
            f"Completed text extraction for {len(results)} pages",
            {
                "total_words": sum(p.word_count for p in results),
                "total_cost": f"${sum(p.processing_cost for p in results):.4f}",
            },
        )

        return results

    def process_node(self, state: DocumentState) -> DocumentState:
        """
        LangGraph node function for text extraction.

        Processes all text-only pages in the document.

        Args:
            state: Current document state

        Returns:
            Updated state with text extraction results
        """
        log_agent_step(
            self.name,
            "Starting text extraction node",
        )

        # Find pages that need text-only extraction
        text_only_pages = []
        for analysis in state["page_analyses"]:
            if analysis.recommended_strategy == ProcessingStrategy.TEXT_ONLY:
                if analysis.page_number not in state["pages_processed"]:
                    text_only_pages.append(analysis.page_number)

        if not text_only_pages:
            log_agent_step(
                self.name,
                "No text-only pages to process",
                level="debug",
            )
            return state

        # Extract text from all text-only pages
        page_results = self.extract_pages(text_only_pages, state)

        # Add results to state
        for page_content in page_results:
            state["page_results"].append(page_content)
            state["pages_processed"].append(page_content.page_number)

            # Update aggregates
            state["total_cost"] += page_content.processing_cost
            state["total_time"] += page_content.processing_time

            # Update strategy counts
            if page_content.processing_strategy:
                strategy = page_content.processing_strategy.value
                state["strategy_counts"][strategy] = state["strategy_counts"].get(strategy, 0) + 1

        log_agent_step(
            self.name,
            f"Text extraction complete",
            {
                "pages_processed": len(page_results),
                "total_cost": f"${sum(p.processing_cost for p in page_results):.4f}",
            },
        )

        return state
