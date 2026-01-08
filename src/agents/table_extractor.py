"""
Table extraction agent for LangGraph workflow.

This agent specializes in extracting tables from document pages using:
1. Rule-based extraction (PyMuPDF) for simple tables
2. Vision API fallback for complex tables
"""

import time
from typing import Dict, Any

from ..graph.state import DocumentState
from ..models import PageContent, ProcessingStrategy
from ..processors import TableProcessor, VisionProcessor
from ..utils import get_logger, log_agent_step, log_cost, log_performance


class TableExtractor:
    """
    Agent for extracting tables from document pages.

    This agent processes pages with STRUCTURAL_PARSING strategy,
    optimizing for cost by using rule-based extraction first and
    falling back to vision API only for complex tables.
    """

    def __init__(self, enable_vision_fallback: bool = True):
        """
        Initialize table extractor agent.

        Args:
            enable_vision_fallback: Whether to use vision API for complex tables
        """
        self.logger = get_logger()
        self.name = "TableExtractor"

        # Initialize processors
        vision_processor = None
        if enable_vision_fallback:
            try:
                vision_processor = VisionProcessor()
                log_agent_step(self.name, "Vision fallback enabled for complex tables")
            except Exception as e:
                self.logger.warning(f"Could not initialize vision processor: {e}")
                log_agent_step(self.name, "Vision fallback disabled (no API key)")

        self.table_processor = TableProcessor(vision_processor=vision_processor)
        self.enable_vision_fallback = enable_vision_fallback and vision_processor is not None

        log_agent_step(
            self.name,
            "Initialized",
            {"vision_fallback": self.enable_vision_fallback},
        )

    def process_node(self, state: DocumentState) -> DocumentState:
        """
        LangGraph node function to process pages with tables.

        Args:
            state: Current document state

        Returns:
            Updated state with table extraction results
        """
        log_agent_step(
            self.name,
            "Processing pages with tables",
            {"total_pages": len(state["page_analyses"])},
        )

        start_time = time.time()
        extractor = state["extractor"]
        page_analyses = state["page_analyses"]
        total_cost = 0.0
        processed_count = 0

        # Find pages that need table extraction
        pages_to_process = []
        for analysis in page_analyses:
            if analysis.recommended_strategy == ProcessingStrategy.STRUCTURAL_PARSING:
                pages_to_process.append(analysis.page_number)

        if not pages_to_process:
            log_agent_step(
                self.name,
                "No pages require table extraction",
                level="debug",
            )
            return state

        log_agent_step(
            self.name,
            f"Found {len(pages_to_process)} pages with tables",
            {"pages": pages_to_process},
        )

        # Process each page
        for page_num in pages_to_process:
            try:
                page_result = self._extract_tables_from_page(
                    extractor,
                    page_num,
                )

                # Update state
                state["page_results"].append(page_result)
                state["pages_processed"].append(page_num)
                total_cost += page_result.processing_cost
                processed_count += 1

                log_agent_step(
                    self.name,
                    f"Processed page {page_num + 1}",
                    {
                        "tables": len(page_result.extracted_tables),
                        "cost": f"${page_result.processing_cost:.4f}",
                    },
                    level="debug",
                )

            except Exception as e:
                self.logger.error(f"Failed to extract tables from page {page_num}: {e}")
                state["errors"].append(f"Table extraction failed on page {page_num}: {str(e)}")

        # Update state costs and time
        state["total_cost"] += total_cost
        state["total_time"] += time.time() - start_time

        # Update strategy counts
        if "STRUCTURAL_PARSING" not in state["strategy_counts"]:
            state["strategy_counts"]["STRUCTURAL_PARSING"] = 0
        state["strategy_counts"]["STRUCTURAL_PARSING"] += processed_count

        log_agent_step(
            self.name,
            "Table extraction complete",
            {
                "pages_processed": processed_count,
                "total_cost": f"${total_cost:.4f}",
                "avg_cost_per_page": f"${total_cost/processed_count:.4f}" if processed_count > 0 else "N/A",
            },
        )

        log_cost(self.name, total_cost, {"pages": processed_count})

        return state

    def _extract_tables_from_page(
        self,
        extractor: Any,
        page_number: int,
    ) -> PageContent:
        """
        Extract tables from a single page.

        Args:
            extractor: Document extractor instance
            page_number: Page number to process

        Returns:
            PageContent with extracted tables
        """
        page_start = time.time()

        # Get the page from extractor
        page = extractor.get_page(page_number)

        # Extract text (quick)
        text = page.get_text()

        # Extract tables using table processor
        extracted_tables, table_cost, table_time = self.table_processor.extract_tables(
            page=page,
            page_number=page_number,
            fallback_to_vision=self.enable_vision_fallback,
        )

        processing_time = time.time() - page_start

        # Create page content
        page_content = PageContent(
            page_number=page_number,
            text=text.strip(),
            extracted_images=[],  # No image extraction in this node
            extracted_tables=extracted_tables,
            extracted_charts=[],  # No chart extraction in this node
            processing_strategy=ProcessingStrategy.STRUCTURAL_PARSING,
            processing_time=processing_time,
            processing_cost=table_cost,
            quality_score=self._calculate_quality_score(extracted_tables),
            metadata={
                "table_count": len(extracted_tables),
                "vision_fallback_used": any(
                    t.extraction_method == "vision_api" for t in extracted_tables
                ),
            },
        )

        return page_content

    def _calculate_quality_score(self, extracted_tables: list) -> float:
        """
        Calculate quality score based on extraction results.

        Args:
            extracted_tables: List of extracted tables

        Returns:
            Quality score between 0 and 1
        """
        if not extracted_tables:
            return 0.5  # No tables found, neutral score

        # Average confidence scores
        avg_confidence = sum(t.confidence_score for t in extracted_tables) / len(extracted_tables)

        return avg_confidence
