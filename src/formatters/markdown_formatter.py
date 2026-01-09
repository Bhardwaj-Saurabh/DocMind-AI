"""
Markdown formatter for extraction results.

Converts extraction results into hierarchical markdown format optimized for RAG applications.
All non-text content (images, charts, graphs) are described in detail by vision models.
"""

from ..models import ExtractionResult, PageContent, ExtractedImage, ExtractedTable, ExtractedChart


class MarkdownFormatter:
    """
    Formats extraction results as hierarchical markdown.

    Philosophy: Everything becomes text for RAG/embedding.
    - Text: Preserved with hierarchy
    - Tables: Converted to markdown tables
    - Images/Charts: Detailed textual descriptions
    - Structure: Headings, sections maintained
    """

    def __init__(self, include_metadata: bool = True, include_page_numbers: bool = True, preserve_hierarchy: bool = True):
        """
        Initialize markdown formatter.

        Args:
            include_metadata: Whether to include document metadata
            include_page_numbers: Whether to include page number markers
            preserve_hierarchy: Whether to preserve document hierarchy (headings, sections)
        """
        self.include_metadata = include_metadata
        self.include_page_numbers = include_page_numbers
        self.preserve_hierarchy = preserve_hierarchy

    def format(self, result: ExtractionResult) -> str:
        """
        Format extraction result as markdown.

        Args:
            result: Extraction result to format

        Returns:
            Markdown-formatted document
        """
        lines = []

        # Document header
        if self.include_metadata:
            lines.extend(self._format_metadata(result))
            lines.append("\n---\n")

        # Main content - page by page
        for page in result.pages:
            lines.extend(self._format_page(page))

        return "\n".join(lines)

    def _format_metadata(self, result: ExtractionResult) -> list[str]:
        """Format document metadata as markdown."""
        lines = []
        metadata = result.metadata

        # Title
        title = metadata.title or metadata.file_name
        lines.append(f"# {title}\n")

        # Metadata section
        lines.append("## Document Information\n")
        lines.append(f"- **File**: {metadata.file_name}")
        format_str = metadata.format.value.upper() if metadata.format else "UNKNOWN"
        lines.append(f"- **Format**: {format_str}")
        lines.append(f"- **Pages**: {metadata.total_pages}")

        if metadata.author:
            lines.append(f"- **Author**: {metadata.author}")
        if metadata.subject:
            lines.append(f"- **Subject**: {metadata.subject}")
        if metadata.created_date:
            lines.append(f"- **Created**: {metadata.created_date.strftime('%Y-%m-%d')}")

        lines.append("")
        return lines

    def _format_page(self, page: PageContent) -> list[str]:
        """
        Format a single page with full hierarchy.

        Args:
            page: Page content to format

        Returns:
            List of markdown lines
        """
        lines = []

        # Page marker (for reference in RAG)
        if self.include_page_numbers:
            lines.append(f"\n<!-- Page {page.page_number} -->\n")

        # Main text content with hierarchy preserved
        if page.text:
            # Try to detect and preserve heading structure
            text_lines = page.text.split('\n')
            formatted_text = self._preserve_text_hierarchy(text_lines)
            lines.extend(formatted_text)
            lines.append("")

        # Images - convert to detailed descriptions
        if page.images:
            for img in page.images:
                lines.extend(self._format_image(img, page.page_number))
                lines.append("")

        # Tables - convert to markdown tables
        if page.tables:
            for table in page.tables:
                lines.extend(self._format_table(table, page.page_number))
                lines.append("")

        # Charts/Graphs - convert to detailed descriptions
        if page.charts:
            for chart in page.charts:
                lines.extend(self._format_chart(chart, page.page_number))
                lines.append("")

        return lines

    def _preserve_text_hierarchy(self, text_lines: list[str]) -> list[str]:
        """
        Detect and preserve document hierarchy in text.

        Args:
            text_lines: Lines of text

        Returns:
            Formatted lines with hierarchy preserved
        """
        formatted = []

        for line in text_lines:
            stripped = line.strip()

            if not stripped:
                formatted.append("")
                continue

            # Detect headings based on patterns
            # This is a heuristic - you might need to adjust based on your documents
            if self._is_heading(stripped):
                # Convert to markdown heading
                level = self._detect_heading_level(stripped)
                formatted.append(f"{'#' * level} {stripped}")
            else:
                formatted.append(line)

        return formatted

    def _is_heading(self, text: str) -> bool:
        """
        Heuristic to detect if a line is a heading.

        Args:
            text: Text line

        Returns:
            True if likely a heading
        """
        # Short lines (< 100 chars)
        # All caps or Title Case
        # No ending punctuation
        # Not too short (> 3 chars)
        if len(text) < 3 or len(text) > 100:
            return False

        # All caps
        if text.isupper() and len(text) > 5:
            return True

        # Title case and no ending punctuation
        if text.istitle() and not text.endswith(('.', '!', '?', ',')):
            return True

        # Numbered headings (1., 1.1, etc.)
        if text[0].isdigit() and '.' in text[:5]:
            return True

        return False

    def _detect_heading_level(self, text: str) -> int:
        """
        Detect heading level (1-6).

        Args:
            text: Heading text

        Returns:
            Heading level (1-6)
        """
        # Simple heuristic based on text characteristics
        if text.isupper() and len(text) < 30:
            return 2  # Major section
        elif text[0].isdigit() and text[1] == '.':
            # 1. = level 2, 1.1 = level 3, 1.1.1 = level 4
            dots = text[:10].count('.')
            return min(dots + 2, 6)
        else:
            return 3  # Default subsection

    def _format_image(self, image: ExtractedImage, page_num: int) -> list[str]:
        """
        Format image as detailed text description.

        Args:
            image: Extracted image
            page_num: Page number

        Returns:
            Markdown lines describing the image
        """
        lines = []

        # Image section header
        image_type = image.image_type.value.replace('_', ' ').title() if image.image_type else "Image"
        lines.append(f"### {image_type} (Page {page_num})")
        lines.append("")

        # Detailed description from vision model
        if image.description:
            lines.append("**Visual Content Description:**")
            lines.append("")
            lines.append(image.description)
            lines.append("")

        # Extracted text (OCR)
        if image.extracted_text:
            lines.append("**Text in Image:**")
            lines.append("")
            lines.append(f"> {image.extracted_text}")
            lines.append("")

        # Metadata
        if image.width and image.height:
            lines.append(f"*Image dimensions: {image.width}x{image.height}px*")
            lines.append("")

        return lines

    def _format_table(self, table: ExtractedTable, page_num: int) -> list[str]:
        """
        Format table as markdown table.

        Args:
            table: Extracted table
            page_num: Page number

        Returns:
            Markdown table lines
        """
        lines = []

        # Table title
        if table.title:
            lines.append(f"### {table.title}")
        else:
            lines.append(f"### Table (Page {page_num})")
        lines.append("")

        # Markdown table
        if table.headers and table.data:
            # Header row
            header_line = "| " + " | ".join(table.headers) + " |"
            lines.append(header_line)

            # Separator
            separator = "| " + " | ".join(["---"] * len(table.headers)) + " |"
            lines.append(separator)

            # Data rows
            for row in table.data:
                # Ensure row has same number of columns as headers
                padded_row = row + [""] * (len(table.headers) - len(row))
                row_line = "| " + " | ".join(padded_row[:len(table.headers)]) + " |"
                lines.append(row_line)

        elif table.data:
            # No headers, just data
            if table.data:
                # Use generic column headers
                num_cols = len(table.data[0]) if table.data else 0
                headers = [f"Column {i+1}" for i in range(num_cols)]

                # Header row
                header_line = "| " + " | ".join(headers) + " |"
                lines.append(header_line)

                # Separator
                separator = "| " + " | ".join(["---"] * num_cols) + " |"
                lines.append(separator)

                # Data rows
                for row in table.data:
                    padded_row = row + [""] * (num_cols - len(row))
                    row_line = "| " + " | ".join(padded_row[:num_cols]) + " |"
                    lines.append(row_line)

        lines.append("")

        # Table metadata
        lines.append(f"*Extracted using {table.extraction_method} method*")
        if table.complexity:
            lines.append(f"*Table complexity: {table.complexity.value}*")
        lines.append("")

        return lines

    def _format_chart(self, chart: ExtractedChart, page_num: int) -> list[str]:
        """
        Format chart/graph as detailed text description.

        Args:
            chart: Extracted chart
            page_num: Page number

        Returns:
            Markdown lines describing the chart
        """
        lines = []

        # Chart section header
        chart_type = chart.chart_type or "Chart"
        lines.append(f"### {chart_type.title()} (Page {page_num})")
        lines.append("")

        # Detailed description from vision model
        if chart.description:
            lines.append("**Chart Description:**")
            lines.append("")
            lines.append(chart.description)
            lines.append("")

        # Key insights
        if chart.insights:
            lines.append("**Key Insights:**")
            lines.append("")
            for i, insight in enumerate(chart.insights, 1):
                lines.append(f"{i}. {insight}")
            lines.append("")

        # Underlying data (if available)
        if chart.has_underlying_data and chart.data:
            lines.append("**Chart Data:**")
            lines.append("")
            lines.append("```")
            lines.append(str(chart.data))
            lines.append("```")
            lines.append("")

        return lines

    def format_for_rag(self, result: ExtractionResult) -> str:
        """
        Format specifically for RAG applications.

        Optimized for:
        - Chunking and embedding
        - Semantic search
        - Context retrieval

        Args:
            result: Extraction result

        Returns:
            RAG-optimized markdown
        """
        # Use standard format but with page markers for chunking
        return self.format(result)

    def format_page_only(self, page: PageContent) -> str:
        """
        Format a single page as markdown.

        Args:
            page: Page content

        Returns:
            Markdown for single page
        """
        lines = self._format_page(page)
        return "\n".join(lines)


def format_to_markdown(result: ExtractionResult, **kwargs) -> str:
    """
    Convenience function to format extraction result as markdown.

    Args:
        result: Extraction result
        **kwargs: Additional arguments for MarkdownFormatter

    Returns:
        Markdown-formatted document
    """
    formatter = MarkdownFormatter(**kwargs)
    return formatter.format(result)
