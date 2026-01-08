"""
Table extraction processor with rule-based extraction and vision fallback.

This processor implements a cost-optimized approach to table extraction:
1. Rule-based extraction using pdfplumber (fast & cheap)
2. Complexity detection
3. Vision API fallback for complex tables
"""

import time
from typing import List, Optional, Dict, Any, Tuple
import io

from PIL import Image

from ..models import ExtractedTable, TableComplexity
from ..utils import get_logger, log_cost


class TableProcessor:
    """
    Processor for extracting tables from documents.

    Implements a hybrid approach:
    - Rule-based extraction for simple tables (~$0.002/table)
    - Vision API for complex tables (~$0.02/table)
    """

    # Cost constants
    RULE_BASED_COST = 0.002  # PyMuPDF/pdfplumber extraction
    VISION_FALLBACK_COST = 0.02  # OpenAI Vision API

    def __init__(self, vision_processor: Optional[Any] = None):
        """
        Initialize table processor.

        Args:
            vision_processor: Optional VisionProcessor for complex tables
        """
        self.logger = get_logger()
        self.vision_processor = vision_processor

    def extract_tables(
        self,
        page: Any,
        page_number: int,
        fallback_to_vision: bool = True
    ) -> Tuple[List[ExtractedTable], float, float]:
        """
        Extract all tables from a page.

        Args:
            page: PyMuPDF page object
            page_number: Page number
            fallback_to_vision: Whether to use vision API for complex tables

        Returns:
            Tuple of (extracted_tables, cost, time)
        """
        start_time = time.time()
        total_cost = 0.0
        extracted_tables = []

        try:
            # Step 1: Try rule-based extraction
            tables_data = self._extract_with_pymupdf(page)

            if not tables_data:
                self.logger.debug(f"No tables found on page {page_number} with rule-based extraction")
                return [], 0.0, time.time() - start_time

            # Step 2: Process each detected table
            for idx, table_data in enumerate(tables_data):
                table_cost = self.RULE_BASED_COST

                # Analyze complexity
                complexity = self._analyze_table_complexity(table_data)

                # If complex and vision available, use vision fallback
                if (complexity == TableComplexity.COMPLEX and
                    fallback_to_vision and
                    self.vision_processor):

                    self.logger.info(
                        f"Table {idx+1} on page {page_number} is complex, using vision fallback"
                    )

                    # Render table region and use vision
                    table_image = self._render_table_region(page, table_data.get("bbox"))
                    if table_image:
                        vision_result = self._extract_with_vision(table_image, page_number, idx)
                        if vision_result:
                            extracted_tables.append(vision_result)
                            table_cost = self.VISION_FALLBACK_COST
                            total_cost += table_cost
                            log_cost("TableProcessor", table_cost, {"method": "vision", "page": page_number})
                            continue

                # Use rule-based result
                extracted_table = self._create_table_object(
                    table_data,
                    page_number,
                    idx,
                    complexity
                )
                extracted_tables.append(extracted_table)
                total_cost += table_cost
                log_cost("TableProcessor", table_cost, {"method": "rule-based", "page": page_number})

        except Exception as e:
            self.logger.error(f"Table extraction failed on page {page_number}: {e}")

        processing_time = time.time() - start_time
        return extracted_tables, total_cost, processing_time

    def _extract_with_pymupdf(self, page: Any) -> List[Dict[str, Any]]:
        """
        Extract tables using PyMuPDF's table detection.

        Args:
            page: PyMuPDF page object

        Returns:
            List of table data dictionaries
        """
        try:
            # PyMuPDF's find_tables() method
            tables = page.find_tables()

            if not tables:
                return []

            tables_data = []
            for table in tables:
                # Extract table data
                table_dict = {
                    "bbox": table.bbox,
                    "rows": table.row_count,
                    "cols": table.col_count,
                    "cells": [],
                    "header": None
                }

                # Extract cell data
                try:
                    # Get table as 2D list
                    table_data = table.extract()

                    if table_data:
                        # First row is often header
                        if len(table_data) > 0:
                            table_dict["header"] = table_data[0]
                            table_dict["cells"] = table_data[1:] if len(table_data) > 1 else []
                        else:
                            table_dict["cells"] = table_data

                except Exception as e:
                    self.logger.warning(f"Failed to extract table data: {e}")
                    continue

                tables_data.append(table_dict)

            return tables_data

        except Exception as e:
            self.logger.error(f"PyMuPDF table extraction failed: {e}")
            return []

    def _analyze_table_complexity(self, table_data: Dict[str, Any]) -> TableComplexity:
        """
        Analyze table complexity to determine if vision fallback is needed.

        Args:
            table_data: Table data from rule-based extraction

        Returns:
            TableComplexity enum
        """
        rows = table_data.get("rows", 0)
        cols = table_data.get("cols", 0)
        cells = table_data.get("cells", [])

        # Simple heuristics
        if rows == 0 or cols == 0:
            return TableComplexity.SIMPLE

        # Large tables are often complex
        if rows > 20 or cols > 10:
            return TableComplexity.COMPLEX

        # Check for merged cells or irregular structure
        if cells:
            # If we have cells data, check for None/empty values (merged cells)
            empty_count = sum(1 for row in cells for cell in row if not cell or str(cell).strip() == "")
            empty_ratio = empty_count / (rows * cols) if (rows * cols) > 0 else 0

            # High empty ratio suggests merged cells
            if empty_ratio > 0.3:
                return TableComplexity.COMPLEX

        # Medium complexity for moderately sized tables
        if rows > 10 or cols > 5:
            return TableComplexity.MEDIUM

        return TableComplexity.SIMPLE

    def _render_table_region(self, page: Any, bbox: Optional[tuple]) -> Optional[bytes]:
        """
        Render a specific table region as an image.

        Args:
            page: PyMuPDF page object
            bbox: Bounding box (x0, y0, x1, y1)

        Returns:
            Image bytes or None
        """
        if not bbox:
            return None

        try:
            import fitz  # PyMuPDF

            # Create clip rect for table region
            clip = fitz.Rect(bbox)

            # Render at higher resolution for better OCR
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
            pix = page.get_pixmap(matrix=mat, clip=clip)

            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")
            return img_bytes

        except Exception as e:
            self.logger.error(f"Failed to render table region: {e}")
            return None

    def _extract_with_vision(
        self,
        image_bytes: bytes,
        page_number: int,
        table_index: int
    ) -> Optional[ExtractedTable]:
        """
        Extract table using vision API (fallback for complex tables).

        Args:
            image_bytes: Image of table region
            page_number: Page number
            table_index: Table index on page

        Returns:
            ExtractedTable or None
        """
        if not self.vision_processor:
            return None

        try:
            # Use vision processor to extract table
            result = self.vision_processor.extract_table_from_image(image_bytes)

            if not result or "error" in result:
                return None

            # Parse vision result into ExtractedTable
            return ExtractedTable(
                page_number=page_number,
                table_index=table_index,
                headers=result.get("headers", []),
                rows=result.get("rows", []),
                caption=result.get("caption"),
                complexity=TableComplexity.COMPLEX,
                extraction_method="vision_api",
                confidence_score=result.get("confidence", 0.8)
            )

        except Exception as e:
            self.logger.error(f"Vision table extraction failed: {e}")
            return None

    def _create_table_object(
        self,
        table_data: Dict[str, Any],
        page_number: int,
        table_index: int,
        complexity: TableComplexity
    ) -> ExtractedTable:
        """
        Create ExtractedTable object from rule-based extraction.

        Args:
            table_data: Table data dictionary
            page_number: Page number
            table_index: Table index
            complexity: Table complexity

        Returns:
            ExtractedTable object
        """
        header = table_data.get("header", [])
        cells = table_data.get("cells", [])

        # Clean header
        headers = [str(h).strip() if h else f"Column {i+1}"
                  for i, h in enumerate(header)] if header else []

        # Clean cells
        rows = []
        for row in cells:
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            rows.append(cleaned_row)

        return ExtractedTable(
            page_number=page_number,
            table_index=table_index,
            headers=headers,
            rows=rows,
            caption=None,
            complexity=complexity,
            extraction_method="rule_based",
            confidence_score=0.9 if complexity == TableComplexity.SIMPLE else 0.7
        )


def create_table_processor(vision_processor: Optional[Any] = None) -> TableProcessor:
    """
    Factory function to create a table processor.

    Args:
        vision_processor: Optional VisionProcessor for complex tables

    Returns:
        Configured TableProcessor instance
    """
    return TableProcessor(vision_processor=vision_processor)
