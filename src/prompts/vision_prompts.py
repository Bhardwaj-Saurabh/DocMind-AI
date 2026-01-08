"""
Prompt templates for vision-based extraction.

These prompts are used with multimodal models (GPT-4 Vision, Claude Sonnet)
to extract content from images, charts, scanned documents, etc.
"""

# Full page analysis prompt
FULL_PAGE_ANALYSIS_PROMPT = """You are analyzing a page from a document. Please extract all visible content from this image.

Extract and structure the following:

1. **Text Content**: All readable text on the page, maintaining structure and formatting
2. **Visual Elements**: Describe any images, diagrams, or visual elements
3. **Tables**: If there are tables, extract the structure and data
4. **Charts/Graphs**: Describe charts and extract key data points
5. **Layout**: Note the overall layout and organization

Format your response as structured JSON:
{
    "text": "full text content...",
    "images": [{"description": "...", "location": "..."}],
    "tables": [{"headers": [...], "rows": [[...]]}],
    "charts": [{"type": "...", "description": "...", "data": {...}}],
    "layout_notes": "..."
}

Be thorough and accurate. Extract everything visible."""

# Image analysis prompt
IMAGE_ANALYSIS_PROMPT = """Analyze this image and provide a detailed description.

Please describe:
1. What is shown in the image (main subject, objects, people, scenes)
2. Any text visible in the image
3. Important details, colors, context
4. Purpose or function of this image in a document context

Provide a clear, concise description suitable for document extraction."""

# Chart analysis prompt
CHART_ANALYSIS_PROMPT = """Analyze this chart or graph and extract the data.

Please provide:
1. **Chart Type**: (bar, line, pie, scatter, etc.)
2. **Title**: Chart title if visible
3. **Axes**: X and Y axis labels and scales
4. **Data Series**: All data series with labels
5. **Data Points**: Extract as many data points as clearly visible
6. **Key Insights**: Main takeaways from the chart

Format as structured JSON:
{
    "chart_type": "...",
    "title": "...",
    "x_axis": {"label": "...", "scale": "..."},
    "y_axis": {"label": "...", "scale": "..."},
    "data_series": [
        {"name": "...", "data_points": [{"x": ..., "y": ...}]}
    ],
    "insights": ["..."]
}"""

# Table extraction prompt
TABLE_EXTRACTION_PROMPT = """Extract the table structure and data from this image.

Please extract:
1. **Headers**: Column headers (if present)
2. **Rows**: All data rows
3. **Structure**: Number of rows and columns
4. **Merged Cells**: Note any merged cells
5. **Cell Data**: Exact text from each cell

Format as structured JSON:
{
    "has_headers": true/false,
    "headers": ["col1", "col2", ...],
    "rows": [
        ["cell1", "cell2", ...],
        ["cell1", "cell2", ...]
    ],
    "row_count": N,
    "col_count": M,
    "merged_cells": [{"row": ..., "col": ..., "span": ...}]
}

Maintain the exact cell content and structure."""

# Scanned document OCR prompt
SCANNED_DOCUMENT_PROMPT = """This appears to be a scanned document image. Please extract all text using OCR.

Extract:
1. All readable text, maintaining line breaks and paragraphs
2. Preserve formatting (headings, lists, indentation)
3. Note any unclear or illegible sections
4. Maintain reading order (left to right, top to bottom)

Provide clean, accurate text extraction suitable for document processing.

If there are multiple columns, extract left column first, then right column.
Mark unclear sections with [UNCLEAR: ...] with your best guess."""

# Diagram analysis prompt
DIAGRAM_ANALYSIS_PROMPT = """Analyze this diagram and explain its content and structure.

Please describe:
1. **Type**: (flowchart, organizational chart, technical diagram, etc.)
2. **Components**: All boxes, shapes, and elements
3. **Connections**: How elements are connected
4. **Labels**: All text labels on elements and connections
5. **Flow/Hierarchy**: Direction of flow or hierarchical structure
6. **Purpose**: What this diagram represents

Provide a clear description that captures the diagram's meaning and structure."""

# Form extraction prompt
FORM_EXTRACTION_PROMPT = """Extract information from this form image.

Please identify:
1. **Form Fields**: All input fields with labels
2. **Filled Values**: Any pre-filled or handwritten values
3. **Checkboxes/Radio Buttons**: Their labels and states (checked/unchecked)
4. **Form Structure**: Sections and organization
5. **Instructions**: Any instructional text

Format as structured JSON:
{
    "form_title": "...",
    "sections": [
        {
            "section_name": "...",
            "fields": [
                {"label": "...", "value": "...", "type": "text/checkbox/radio"}
            ]
        }
    ]
}"""

# SmartArt/Complex Graphics prompt
SMARTART_PROMPT = """Analyze this SmartArt or complex graphic element.

Please describe:
1. **Type**: (process, hierarchy, cycle, relationship, matrix, pyramid, etc.)
2. **Main Elements**: All shapes and their text content
3. **Relationships**: How elements are connected or related
4. **Structure**: Overall organization and flow
5. **Purpose**: What concept or process is being illustrated

Provide a clear textual representation that preserves the meaning and structure."""

# Multi-column layout prompt
MULTI_COLUMN_PROMPT = """This page has a multi-column layout. Extract text maintaining the correct reading order.

Extract:
1. **Column 1**: All text from the left column
2. **Column 2**: All text from the middle column (if present)
3. **Column 3**: All text from the right column (if present)
4. Maintain paragraph breaks within columns
5. Note any images or graphics between columns

Format response clearly separating each column."""

# Quality check prompt (for validation)
QUALITY_CHECK_PROMPT = """Compare this extracted text with the image to verify accuracy.

Original text extracted:
{extracted_text}

Please:
1. Verify if the extraction is complete
2. Check for any missing sections
3. Identify any obvious errors
4. Estimate confidence score (0-1)

Respond with:
{
    "is_complete": true/false,
    "missing_sections": ["..."],
    "errors_found": ["..."],
    "confidence_score": 0.95,
    "suggested_improvements": ["..."]
}"""


def get_prompt_for_content_type(content_type: str) -> str:
    """
    Get the appropriate prompt template for a content type.

    Args:
        content_type: Type of content (full_page, image, chart, table, etc.)

    Returns:
        Prompt template string
    """
    prompt_map = {
        "full_page": FULL_PAGE_ANALYSIS_PROMPT,
        "image": IMAGE_ANALYSIS_PROMPT,
        "chart": CHART_ANALYSIS_PROMPT,
        "table": TABLE_EXTRACTION_PROMPT,
        "scanned": SCANNED_DOCUMENT_PROMPT,
        "diagram": DIAGRAM_ANALYSIS_PROMPT,
        "form": FORM_EXTRACTION_PROMPT,
        "smartart": SMARTART_PROMPT,
        "multi_column": MULTI_COLUMN_PROMPT,
        "quality_check": QUALITY_CHECK_PROMPT,
    }

    return prompt_map.get(content_type, FULL_PAGE_ANALYSIS_PROMPT)


def format_page_analysis_prompt(page_number: int, total_pages: int) -> str:
    """
    Format a prompt for full page analysis with context.

    Args:
        page_number: Current page number
        total_pages: Total pages in document

    Returns:
        Formatted prompt
    """
    return f"""{FULL_PAGE_ANALYSIS_PROMPT}

Context: This is page {page_number} of {total_pages} in the document.

Please be thorough and extract all visible content."""


def format_quality_check_prompt(extracted_text: str) -> str:
    """
    Format a prompt for quality validation.

    Args:
        extracted_text: Previously extracted text to validate

    Returns:
        Formatted prompt
    """
    return QUALITY_CHECK_PROMPT.format(extracted_text=extracted_text)
