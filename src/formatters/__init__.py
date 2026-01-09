"""
Output formatters for DocMind-AI.

Formatters for different output formats:
- MarkdownFormatter: Hierarchical markdown optimized for RAG
- JSONFormatter: JSON output with schema validation (TODO)
- CSVFormatter: Tabular data export (TODO)
- HTMLFormatter: Styled HTML output (TODO)
"""

# Markdown formatter (primary format for RAG applications)
from .markdown_formatter import MarkdownFormatter, format_to_markdown

# Other formatters (to be implemented)
# from .json_formatter import JSONFormatter
# from .csv_formatter import CSVFormatter
# from .html_formatter import HTMLFormatter

__all__ = [
    "MarkdownFormatter",
    "format_to_markdown",
]
