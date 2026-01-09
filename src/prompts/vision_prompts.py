"""
Prompt templates for vision-based extraction.

These prompts are used with multimodal models (GPT-4 Vision, Claude Sonnet)
to extract content from images, charts, scanned documents, etc.
"""

# Full page analysis prompt - Enhanced for RAG
FULL_PAGE_ANALYSIS_PROMPT = """You are analyzing a page from a document for RAG (Retrieval-Augmented Generation) applications.

**CRITICAL REQUIREMENTS**:
1. Convert ALL visual content to detailed text - this is the ONLY representation users will have
2. Maintain hierarchical structure (headings, sections, subsections)
3. Provide comprehensive descriptions for images, charts, and diagrams
4. Extract tables with complete data
5. Preserve document flow and reading order

**Extract and describe the following in detail**:

1. **Document Structure and Hierarchy**:
   - Page title or heading (if present)
   - Section headings and subheadings
   - Hierarchical levels (H1, H2, H3, etc.)
   - Numbered or bulleted lists
   - Overall organization

2. **Text Content**:
   - All readable text, maintaining original formatting
   - Paragraphs with proper breaks
   - Emphasis (bold, italic, underline)
   - Font sizes and styles (if significant)
   - Reading order and flow
   - Captions and labels

3. **Visual Elements** (DETAILED descriptions required):
   - **Images**: Provide comprehensive descriptions (minimum 50 words each)
     - What is shown
     - Visual details (colors, composition, style)
     - Text within images
     - Purpose and context
     - Position on page (top, middle, bottom, left, right)

   - **Diagrams**: Describe structure and content (minimum 100 words)
     - Type of diagram
     - All components and labels
     - Connections and relationships
     - Flow or hierarchy
     - Complete meaning and purpose

4. **Charts and Graphs** (COMPREHENSIVE descriptions):
   - Chart type and title
   - All axes with labels and scales
   - All data series with complete data points
   - Trends and patterns
   - Key insights and takeaways
   - Colors and legend
   - Source and time period
   - **Minimum 150 words per chart**

5. **Tables**:
   - Table title or caption
   - Column headers
   - All rows and cells with data
   - Row headers if present
   - Merged cells or special formatting
   - Table footnotes
   - Convert to markdown table format

6. **Layout and Formatting**:
   - Multi-column layout (describe reading order)
   - Sidebar content
   - Headers and footers
   - Page numbers
   - Watermarks or background elements
   - Spatial relationships between elements

7. **Supporting Elements**:
   - Footnotes and endnotes
   - Callout boxes or sidebars
   - Pull quotes
   - Annotations or comments
   - Logos or branding

**Output Format**:
Provide a comprehensive markdown document that represents the ENTIRE page as hierarchical text. Use:
- # for main headings
- ## for subheadings
- ### for sub-subheadings
- Markdown tables for tabular data
- Detailed narrative paragraphs for images, charts, and diagrams
- Proper formatting (bold, italic, bullets, numbering)

The output should be a complete, self-contained textual representation that someone can read and understand without seeing the original page. Aim for thoroughness over brevity."""

# Image analysis prompt - Enhanced for RAG
IMAGE_ANALYSIS_PROMPT = """Analyze this image and provide a COMPREHENSIVE, DETAILED textual description suitable for RAG (Retrieval-Augmented Generation) applications.

**CRITICAL**: Your description will be converted to text and used for semantic search and embeddings. Be thorough and descriptive.

Please provide:

1. **Main Subject**: Detailed description of the primary content (objects, people, scenes, concepts)
2. **Visual Details**:
   - Colors, shapes, sizes, positions
   - Spatial relationships between elements
   - Visual hierarchy and emphasis
3. **Text Content**: All visible text, labels, captions, annotations
4. **Context & Purpose**:
   - What this image represents in a document
   - Key message or information conveyed
   - Relationship to surrounding content
5. **Technical Details**:
   - Image type (photograph, diagram, illustration, screenshot)
   - Quality and clarity
   - Any notable visual elements

Format your response as a detailed narrative paragraph (minimum 100 words) that captures ALL information visible in the image. This text will be used for semantic search, so include relevant keywords and concepts."""

# Chart analysis prompt - Enhanced for RAG
CHART_ANALYSIS_PROMPT = """Analyze this chart or graph and provide a COMPREHENSIVE textual description suitable for RAG applications.

**CRITICAL**: Convert ALL visual information to detailed text. Your description will be used for semantic search and must be self-contained.

Provide a detailed narrative description including:

1. **Chart Overview**:
   - Chart type (bar, line, pie, scatter, area, combination, etc.)
   - Title and subtitle
   - Time period or scope covered
   - Overall purpose and message

2. **Axes and Scales**:
   - X-axis: label, units, range, scale type (linear/logarithmic)
   - Y-axis: label, units, range, scale type
   - Secondary axes if present

3. **Data Series** (describe each in detail):
   - Series name and legend labels
   - Color and visual representation
   - Complete data points with values
   - Trends and patterns observed
   - Min, max, average values

4. **Visual Elements**:
   - Grid lines, reference lines, annotations
   - Data labels and values displayed
   - Colors used and their meanings
   - Any highlighting or emphasis

5. **Key Insights and Analysis**:
   - Main trends (increasing, decreasing, stable)
   - Comparisons between series
   - Notable data points (peaks, valleys, outliers)
   - Relationships and correlations
   - Business or contextual implications

6. **Supporting Information**:
   - Source attribution if visible
   - Footnotes or disclaimers
   - Time period or date range

Format as a comprehensive narrative (minimum 150 words) that describes EVERYTHING visible in the chart. Someone should be able to understand all the data and insights without seeing the visual."""

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

# Diagram analysis prompt - Enhanced for RAG
DIAGRAM_ANALYSIS_PROMPT = """Analyze this diagram and provide a COMPREHENSIVE textual description suitable for RAG applications.

**CRITICAL**: Convert this visual diagram to detailed, hierarchical text. Your description will be used for semantic search and must capture all information.

Provide a detailed narrative including:

1. **Diagram Type and Purpose**:
   - Specific type (flowchart, org chart, process diagram, network diagram, UML, ER diagram, etc.)
   - Overall purpose and what it represents
   - Context and domain (business process, technical architecture, organizational structure, etc.)

2. **Components and Elements** (describe each):
   - All shapes, boxes, nodes, and their types (rectangle, diamond, circle, etc.)
   - Text content within each element
   - Colors, sizes, and visual styling
   - Hierarchical levels or groupings
   - Numbering or labeling systems

3. **Connections and Relationships**:
   - All arrows, lines, and connectors
   - Direction of flow (unidirectional, bidirectional)
   - Labels on connections
   - Connection types (solid, dashed, thick, thin)
   - What each connection represents (data flow, reporting structure, process sequence, etc.)

4. **Flow and Structure**:
   - Start and end points
   - Main pathways and branches
   - Decision points and conditions
   - Loops or cycles
   - Hierarchical levels (top-down, bottom-up)
   - Left-to-right or other directional flow

5. **Annotations and Supporting Information**:
   - Legend or key
   - Notes and callouts
   - Labels and identifiers
   - Any explanatory text

6. **Semantic Meaning**:
   - What process or structure is depicted
   - Roles and responsibilities (for org charts)
   - Steps and sequence (for flowcharts)
   - System components and interactions (for architecture diagrams)
   - Key decision points and outcomes

Format as a detailed, structured narrative (minimum 200 words) that completely describes the diagram. Use hierarchical structure with clear headings. Someone should fully understand the diagram without seeing it."""

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

# SmartArt/Complex Graphics prompt - Enhanced for RAG
SMARTART_PROMPT = """Analyze this SmartArt or complex graphic element and convert it to COMPREHENSIVE hierarchical text suitable for RAG applications.

**CRITICAL**: This visual graphic must be completely represented in text form. Your description will be the ONLY way users can access this information.

Provide a detailed, structured description including:

1. **Graphic Type and Category**:
   - SmartArt type (process, hierarchy, cycle, relationship, matrix, pyramid, list, picture, etc.)
   - Visual layout (linear, circular, hierarchical, matrix, etc.)
   - Purpose and message being conveyed

2. **Main Elements** (describe each component):
   - All shapes, boxes, circles, or graphical elements
   - Complete text content within each element
   - Visual properties (colors, sizes, positioning)
   - Icons or images embedded
   - Numbering or ordering system

3. **Hierarchical Structure**:
   - Primary/main level elements
   - Secondary/supporting elements
   - Sub-elements and details
   - Parent-child relationships
   - Groupings and categories

4. **Relationships and Connections**:
   - How elements relate to each other
   - Flow or sequence (if applicable)
   - Dependencies or prerequisites
   - Arrows, lines, or connectors
   - Directional flow (left-to-right, top-to-bottom, circular, etc.)

5. **Visual Hierarchy and Emphasis**:
   - Which elements are emphasized (larger, bolder, different color)
   - Visual groupings or sections
   - Color coding and its meaning
   - Background shapes or containers

6. **Complete Content Extraction**:
   - All visible text (headings, body text, labels, captions)
   - Any numbers, dates, or statistics
   - Bullet points or list items
   - Supporting text or descriptions

7. **Conceptual Understanding**:
   - What concept, process, or relationship is illustrated
   - The key message or takeaway
   - How the visual structure supports the meaning
   - Practical application or context

Format as a detailed, hierarchical narrative (minimum 200 words) with clear structure. Use markdown headings, bullet points, and numbering to preserve the hierarchy. Someone should fully understand the graphic's content and meaning without seeing it."""

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
