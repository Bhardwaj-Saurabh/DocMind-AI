# DocMind-AI

## Project Overview
DocMind-AI is an agentic AI application for intelligent document extraction from multiple formats (PDF, DOCX, PPT). It leverages multimodal AI agents that work in parallel to process each page and extract structured information.

## Tech Stack
- **LangGraph**: For orchestrating agentic workflows
- **LangChain**: For LLM integration and document processing
- **OpenAI**: Multimodal AI models (GPT-4 Vision for image understanding)
- **Python**: Core programming language

## Key Features
- Multi-format support (PDF, DOCX, PPT)
- Parallel page processing using agentic architecture
- Multimodal extraction (text, images, tables, charts)
- Structured output generation

---

## Implementation Plan

### Phase 1: Foundation & Setup
**Goal**: Set up the project infrastructure and core dependencies

1. **Project Initialization**
   - Create Python virtual environment
   - Set up requirements.txt with core dependencies
   - Configure environment variables (.env for API keys)
   - Initialize git repository (already done ✓)

2. **Core Dependencies Installation**
   - langchain
   - langgraph
   - openai
   - python-pptx (for PPT processing)
   - python-docx (for DOCX processing)
   - pypdf or pymupdf (for PDF processing)
   - pillow (for image handling)

3. **Project Structure**
   ```
   docmind-ai/
   ├── src/
   │   ├── agents/          # Agent definitions
   │   ├── extractors/      # Format-specific extractors
   │   ├── processors/      # Page processors
   │   ├── graph/           # LangGraph workflow
   │   └── utils/           # Helper functions
   ├── tests/
   ├── examples/
   ├── .env
   └── requirements.txt
   ```

### Phase 2: Document Loaders & Basic Extraction
**Goal**: Build format-specific document loaders and basic text extraction

1. **PDF Extractor** (`src/extractors/pdf_extractor.py`)
   - Load PDF files using PyMuPDF
   - Extract text content per page
   - Extract images embedded in pages
   - Convert pages to images for multimodal processing
   - Handle metadata extraction

2. **DOCX Extractor** (`src/extractors/docx_extractor.py`)
   - Load DOCX files using python-docx
   - Extract paragraphs and formatting
   - Extract embedded images
   - Handle tables and lists
   - Preserve document structure

3. **PPT Extractor** (`src/extractors/ppt_extractor.py`)
   - Load PPT/PPTX files using python-pptx
   - Extract slide content (text, shapes, images)
   - Convert slides to images
   - Handle speaker notes
   - Extract embedded media

4. **Base Extractor Interface** (`src/extractors/base.py`)
   - Define common interface for all extractors
   - Standardize output format
   - Implement factory pattern for extractor selection

### Phase 3: Agentic Architecture with LangGraph (UPDATED)
**Goal**: Design and implement the adaptive multi-agent system using LangGraph

**Key Change**: Added Content Analysis Agent and Adaptive Router for intelligent processing

1. **Core Agent Definitions** (`src/agents/`)
   - **Content Analysis Agent** (NEW): Analyzes page content and recommends strategy
   - **Adaptive Router Agent** (NEW): Routes pages to optimal processing pipelines
   - **Coordinator Agent**: Orchestrates the overall extraction workflow
   - **Text Extraction Agent**: Fast, cheap text-only extraction
   - **Structural Parser Agent**: Parses tables and structured content
   - **Vision Processing Agent**: Multimodal analysis (use strategically!)
   - **Hybrid Processing Agent**: Combines text + vision selectively
   - **Quality Validator Agent** (NEW): Validates results, triggers fallbacks
   - **Synthesizer Agent**: Combines results from all strategies

2. **Content Analysis Implementation** (`src/agents/content_analyzer.py`)
   - Detect text quality and coverage
   - Count and classify embedded images
   - Identify table complexity
   - Detect charts, SmartArt, constructed graphics
   - Assess layout complexity
   - Generate per-page processing strategy
   - Estimate processing cost

3. **Adaptive LangGraph Workflow** (`src/graph/extraction_graph.py`)
   - Define enhanced state schema with strategy metadata
   - Create nodes for all agents (including new ones)
   - **Implement adaptive routing logic**: Route based on content analysis
   - Add conditional edges based on content type
   - Implement parallel execution with different strategies per page
   - Add quality validation checkpoints
   - Implement fallback mechanisms
   - Handle error recovery and retries

4. **Enhanced State Management** (`src/graph/state.py`)
   ```python
   class PageState:
       page_id: str
       content_analysis: ContentAnalysisResult  # NEW
       processing_strategy: ProcessingStrategy  # NEW
       text_content: Optional[str]
       images: List[ExtractedImage]
       tables: List[ExtractedTable]
       quality_score: float  # NEW
       processing_cost: float  # NEW
       fallback_triggered: bool  # NEW
   ```

5. **Adaptive Routing Logic** (`src/graph/router.py`)
   ```python
   def route_page(content_analysis: ContentAnalysisResult) -> str:
       if content_analysis.is_text_only():
           return "text_extraction_agent"
       elif content_analysis.has_simple_tables():
           return "hybrid_agent_simple"
       elif content_analysis.has_complex_visuals():
           return "vision_processing_agent"
       elif content_analysis.has_embedded_images():
           return "hybrid_agent_with_vision"
       else:
           return "full_multimodal_agent"
   ```

6. **Parallel Processing Strategy**
   - Content analysis runs in parallel for all pages (fast)
   - Different processing strategies execute in parallel (adaptive)
   - Thread-safe state updates with strategy metadata
   - Rate limiting for Vision API calls (expensive ones only)
   - Cost tracking per page and total

### Phase 4: Multimodal Processing with OpenAI
**Goal**: Implement advanced multimodal understanding using GPT-4 Vision

1. **Vision Processing** (`src/processors/vision_processor.py`)
   - Convert document pages to images
   - Use GPT-4 Vision API for visual analysis
   - Extract information from charts and diagrams
   - Identify table structures visually
   - Describe images and figures

2. **Prompt Engineering** (`src/prompts/`)
   - Design prompts for different extraction tasks
   - Create templates for structured output
   - Implement few-shot examples
   - Optimize for accuracy and consistency

3. **Table Detection & Extraction** (`src/processors/table_processor.py`)
   - Detect tables using visual analysis
   - Extract table structure (rows, columns, headers)
   - Parse table content with OCR fallback
   - Convert tables to structured formats (CSV, JSON)

4. **Image & Chart Understanding**
   - Extract insights from business charts
   - Describe visual content
   - Extract text from images (OCR)
   - Identify relationships in diagrams

### Phase 5: Output Formatting & Storage
**Goal**: Generate structured outputs and manage results

1. **Output Formatters** (`src/formatters/`)
   - JSON formatter with schema validation
   - Markdown formatter for human-readable output
   - CSV formatter for tabular data
   - HTML formatter with styling

2. **Result Aggregation** (`src/processors/aggregator.py`)
   - Combine results from parallel agents
   - Remove duplicates and conflicts
   - Maintain document structure and order
   - Generate summary statistics

3. **Data Models** (`src/models/`)
   - Define Pydantic models for extracted data
   - Document metadata schema
   - Page content schema
   - Validation rules

### Phase 6: Testing & Quality Assurance
**Goal**: Ensure reliability and accuracy of the extraction system

1. **Unit Tests** (`tests/unit/`)
   - Test each extractor independently
   - Test agent behaviors
   - Test formatters and utilities
   - Mock OpenAI API calls

2. **Integration Tests** (`tests/integration/`)
   - Test end-to-end extraction workflow
   - Test LangGraph execution
   - Test parallel processing
   - Validate output formats

3. **Sample Documents** (`tests/fixtures/`)
   - Collect diverse sample documents
   - PDFs with different layouts
   - DOCX with complex formatting
   - PPTs with various content types

4. **Performance Testing**
   - Benchmark processing speed
   - Measure API costs
   - Optimize bottlenecks
   - Test with large documents

### Phase 7: Main Application & CLI
**Goal**: Create user-friendly interfaces for the application

1. **Main Application** (`src/main.py`)
   - Initialize LangGraph workflow
   - Handle file input/output
   - Configure extraction parameters
   - Implement logging and monitoring

2. **CLI Interface** (`src/cli.py`)
   - Command-line argument parsing
   - Progress bar for long operations
   - Error handling and user feedback
   - Configuration file support

3. **API Interface (Optional)** (`src/api.py`)
   - FastAPI REST endpoints
   - File upload handling
   - Async processing
   - Job status tracking

4. **Example Scripts** (`examples/`)
   - Basic extraction example
   - Batch processing example
   - Custom agent configuration
   - Output format examples

---

## Architecture Critique & Key Insights

### Critical Questions Addressed

#### 1. Do we need to convert pages to images first?
**Answer: NO - This should be conditional and adaptive!**

The initial architecture had a significant flaw: assuming all pages need vision processing. This is:
- **Expensive**: Vision API costs 10-100x more than text models
- **Slower**: Image processing adds latency
- **Less accurate for text**: Native text extraction is more precise for pure text

**Better approach**: Content-first analysis → Adaptive routing → Minimal vision usage

#### 2. Criteria for Image Conversion vs Direct Processing

| Content Type | Processing Strategy | Rationale |
|--------------|-------------------|-----------|
| **Pure text** | Direct text extraction only | Fastest, cheapest, most accurate |
| **Text + simple tables** | Structural extraction → Vision fallback | Try cheap method first |
| **Text + complex tables** | Hybrid: Text + Vision for tables only | Optimize for accuracy |
| **Embedded images** | Extract images → Text for content, Vision for images | Process separately |
| **Charts/graphs** | Vision API required | Visual understanding needed |
| **SmartArt/constructed graphics** | Page-as-image + Vision API | Cannot extract components separately |
| **Forms/layouts** | Vision API for structure | Layout matters |
| **Scanned documents** | OCR + Vision API | No native text available |
| **Mixed complex content** | Hybrid: Strategic vision usage | Targeted approach |

#### 3. Content Type Detection

Before processing, analyze each page for:
- **Text blocks**: Density, quality, extractability
- **Embedded images**: Count, type (photo vs diagram)
- **Tables**: Simple (parseable) vs complex (nested, merged cells)
- **Charts**: Type (bar, line, pie, etc.)
- **Constructed graphics**: SmartArt, shapes, drawing objects
- **Forms**: Input fields, checkboxes
- **Layout complexity**: Single column vs multi-column vs custom

#### 4. Image Types & Handling

**Embedded Images** (extracted as separate files):
- Photos, logos, diagrams inserted as image files
- Can be extracted from PDF/DOCX/PPT
- Process separately with Vision API
- More efficient than processing entire page

**Constructed Graphics** (require page rendering):
- PPT SmartArt, shapes, connectors
- Drawing objects in Word
- Vector graphics
- Layered elements
- Must render page as image first

**Charts with Data**:
- May have underlying data tables (Excel charts)
- Check for data before using Vision API
- Extracting data table is more accurate than vision

#### 5. Other Critical Considerations

**Cost Management**:
- Vision API: ~$0.01-0.05 per image (depending on size)
- Text models: ~$0.001 per page
- Potential 50x cost difference!

**Processing Speed**:
- Text extraction: 100-500ms per page
- Vision API: 2-5 seconds per image
- 10x speed difference

**Accuracy Trade-offs**:
- Text extraction: 99%+ accuracy for clean text
- Vision OCR: 95-98% accuracy
- Use native extraction when possible

**Document Format Differences**:
- **PDF**: Can be text-based or image-based, needs detection
- **DOCX**: Structured format, excellent text extraction
- **PPT**: Heavy on visual elements, more vision processing needed

---

## Improved Technical Architecture

### Enhanced System Flow with Adaptive Processing

```
1. Input Document (PDF/DOCX/PPT)
   ↓
2. Document Loader (Format-specific extractor)
   ↓
3. Asset Extraction (Extract embedded images, fonts, metadata)
   ↓
4. Page Splitter (Divide into pages)
   ↓
5. Content Analysis Agent (NEW - Analyzes each page)
   │   ├─→ Detect: text quality, images, tables, charts, graphics
   │   ├─→ Classify: pure-text, mixed, visual-heavy
   │   └─→ Generate: processing strategy per page
   ↓
6. Coordinator Agent (Routes based on content analysis)
   ↓
7. Adaptive Parallel Processing (Different strategies per page)
   │
   ├─→ Page 1 [Pure Text]
   │   └─→ Text Extraction Only (Fast & Cheap)
   │
   ├─→ Page 2 [Text + Simple Table]
   │   ├─→ Text Extraction
   │   └─→ Structural Table Parser
   │
   ├─→ Page 3 [Text + Complex Table]
   │   ├─→ Text Extraction
   │   ├─→ Table Structure Parser (try first)
   │   └─→ Vision API (fallback if parser fails)
   │
   ├─→ Page 4 [Text + Embedded Image]
   │   ├─→ Text Extraction (for text)
   │   └─→ Vision API (only for extracted image)
   │
   ├─→ Page 5 [SmartArt/Constructed Graphics]
   │   ├─→ Render page as image
   │   └─→ Vision API (full page analysis)
   │
   └─→ Page N [Chart/Graph]
       ├─→ Check for underlying data
       ├─→ Extract data if available
       └─→ Vision API (if no data available)
   ↓
8. Quality Validator (Check extraction quality)
   ├─→ If quality low: trigger fallback (Vision API)
   └─→ If quality good: proceed
   ↓
9. Synthesizer Agent (Aggregate all results)
   ↓
10. Output Formatter (JSON/Markdown/CSV/HTML)
   ↓
11. Final Output + Processing Report (cost, time, methods used)
```

### Improved Agent Architecture

#### 1. Content Analysis Agent (NEW - Critical Addition)
**Purpose**: Inspect page content before deciding processing strategy

**Responsibilities**:
- Detect text quality and extractability
- Count and classify embedded images
- Identify table structures (simple vs complex)
- Detect charts, graphs, forms
- Identify constructed graphics (SmartArt, shapes)
- Assess layout complexity
- **Output**: Processing strategy recommendation per page

**Implementation**:
```python
{
  "page_id": "page_3",
  "content_type": "mixed",
  "text_quality": "high",
  "components": {
    "text_blocks": 5,
    "embedded_images": 1,
    "tables": {"count": 2, "complexity": "complex"},
    "charts": 0,
    "constructed_graphics": 0
  },
  "processing_strategy": {
    "text": "direct_extraction",
    "tables": "structural_with_vision_fallback",
    "images": "vision_api",
    "estimated_cost": "$0.015"
  }
}
```

#### 2. Adaptive Router Agent (NEW)
**Purpose**: Route each page to optimal processing pipeline

**Decision Logic**:
- Pure text (90%+ text, no images/tables) → Text extraction only
- Text + simple tables → Text + structural parser
- Text + complex tables → Hybrid approach
- Embedded images → Extract separately, process with vision
- Constructed graphics → Render + vision
- Charts → Data extraction first, vision fallback

#### 3. Specialized Processing Agents

**Text Extraction Agent** (Fast & Cheap):
- Native text extraction from PDF/DOCX/PPT
- Preserves formatting and structure
- Cost: ~$0.001 per page
- Speed: 100-500ms

**Structural Parser Agent** (For tables):
- Parse table structure from document
- Extract rows, columns, headers
- Fallback to vision if confidence low

**Vision Processing Agent** (Expensive, use strategically):
- Process images with GPT-4 Vision
- Full page rendering for complex layouts
- Cost: ~$0.01-0.05 per image
- Speed: 2-5 seconds
- **Use only when necessary!**

**Hybrid Agent** (Smart combination):
- Text extraction for content
- Vision for specific visual elements
- Optimal cost/accuracy balance

#### 4. Quality Validator Agent (NEW)
**Purpose**: Verify extraction quality, trigger fallbacks

**Checks**:
- Text completeness (word count, coherence)
- Table structure validity
- Image description quality
- Missing content detection

**Fallback Logic**:
- If text extraction < 50% confidence → Try vision
- If table parsing fails → Use vision API
- If embedded image not found → Render page section

#### 5. Synthesizer Agent (Enhanced)
**Responsibilities**:
- Aggregate results from all processing strategies
- Maintain document structure
- Remove duplicates
- Generate processing report (costs, time, methods)

### Enhanced Agent Communication
```
Content Analysis Agent
        ↓
    [Analyzes all pages in parallel]
        ↓
    [Generates strategy map]
        ↓
Adaptive Router Agent
        ↓
    [Routes to optimal pipelines]
        ↓
Parallel Processing (strategy-specific)
    ├─→ Text-only pages: Text Agent
    ├─→ Mixed pages: Hybrid Agent
    └─→ Visual pages: Vision Agent
        ↓
Quality Validator Agent
        ↓
    [Check quality, trigger fallbacks if needed]
        ↓
Synthesizer Agent
        ↓
    [Merge all results + cost report]
```

### Cost Optimization Strategy
1. **Always try cheapest method first**: Text extraction
2. **Use vision strategically**: Only for visual content
3. **Extract embedded assets**: Process separately (more efficient)
4. **Batch vision calls**: Reduce API overhead
5. **Cache results**: Avoid reprocessing
6. **Quality-based fallback**: Only upgrade method if needed

**Example Cost Comparison**:
- 10-page document, all vision: ~$0.30
- 10-page document, adaptive: ~$0.05 (6x cheaper!)
  - 7 pages text-only: $0.007
  - 2 pages hybrid: $0.024
  - 1 page full vision: $0.020

---

## Key Technical Considerations

### 1. Performance Optimization
- **Batch API calls** to reduce latency
- **Cache intermediate results** for reprocessing
- **Streaming output** for large documents
- **Lazy loading** of pages

### 2. Error Handling
- Retry logic with exponential backoff
- Fallback strategies (e.g., OCR if text extraction fails)
- Graceful degradation for problematic pages
- Comprehensive logging

### 3. Cost Management
- Track OpenAI API token usage
- Implement token limits per document
- Use cheaper models for simple tasks
- Cache vision API results

### 4. Scalability
- Support for very large documents (100+ pages)
- Memory-efficient page processing
- Configurable parallelism level
- Queue-based processing for batch jobs

### 5. Quality & Accuracy
- Validation of extracted data
- Confidence scores for extractions
- Human-in-the-loop for uncertain cases
- A/B testing of different prompts

---

## Key Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Large documents consume too much memory | Process pages in batches, stream results |
| API rate limits with parallel processing | Implement token bucket algorithm, queue management |
| Inconsistent extraction quality | Use prompt engineering, few-shot examples, validation |
| Different document layouts | Use multimodal vision API, adaptive prompts |
| Table extraction accuracy | Combine vision API with OCR, validate structure |
| Cost of processing many documents | Cache results, use cheaper models when possible |

---

## Architecture Improvements Summary

### Original vs Improved Architecture

| Aspect | Original Architecture | Improved Architecture | Impact |
|--------|----------------------|----------------------|--------|
| **Content Analysis** | None - blind processing | Content Analysis Agent first | Intelligent routing |
| **Processing Strategy** | One-size-fits-all | Adaptive per-page strategies | 6x cost reduction |
| **Vision API Usage** | All pages by default | Strategic, conditional usage | 80% fewer vision calls |
| **Cost per 10-page doc** | ~$0.30 (all vision) | ~$0.05 (adaptive) | 85% cost savings |
| **Processing Speed** | Slow (all vision) | Fast (mostly text) | 3-5x faster |
| **Text Accuracy** | 95-98% (vision OCR) | 99%+ (native extraction) | Higher accuracy |
| **Embedded Images** | Full page processing | Extract and process separately | More efficient |
| **Tables** | Always vision | Structural parser first | Better structure |
| **Fallback Logic** | None | Quality-based fallbacks | Better reliability |
| **Cost Tracking** | Not tracked | Per-page and total | Full visibility |

### Key Architectural Decisions

1. **Content-First Analysis**
   - Analyze before processing (not after)
   - Make informed decisions about processing strategy
   - Estimate costs upfront

2. **Cheap-First, Vision-When-Needed**
   - Always try text extraction first
   - Use vision API only for visual content
   - Fallback to vision if quality is low

3. **Separation of Concerns**
   - Embedded images: Extract and process separately
   - Constructed graphics: Render page as image
   - Charts with data: Extract data, not vision

4. **Quality-Driven Fallbacks**
   - Validate extraction quality
   - Automatically upgrade to vision if needed
   - Track when fallbacks occur

5. **Cost Awareness**
   - Track cost per page
   - Report total costs
   - Allow cost budgets/limits

### Implementation Priority (Updated)

**Phase 0: Critical Foundation**
1. Content Analysis Agent (MUST HAVE)
2. Adaptive Router (MUST HAVE)
3. Basic Text Extraction Agent

**Phase 1: Core Processing**
1. Text Extraction Agent
2. Structural Parser Agent (tables)
3. Vision Processing Agent (strategic use)

**Phase 2: Intelligence Layer**
1. Quality Validator Agent
2. Fallback mechanisms
3. Cost tracking

**Phase 3: Optimization**
1. Embedded asset extraction
2. Hybrid processing
3. Caching layer

---

## Implementation Guide: Content Detection

### How to Detect Content Types (Critical for Adaptive Processing)

#### 1. Text Quality Detection

**For PDF**:
```python
# Using PyMuPDF
page = doc[page_num]
text = page.get_text()
# Check if text is extractable and meaningful
text_quality = "high" if len(text.strip()) > 100 else "low"
```

**For DOCX**:
```python
# Using python-docx
text = "\n".join([para.text for para in doc.paragraphs])
# DOCX usually has excellent text quality
```

**For PPT**:
```python
# Using python-pptx
text = []
for shape in slide.shapes:
    if hasattr(shape, "text"):
        text.append(shape.text)
```

#### 2. Embedded Image Detection

**For PDF (PyMuPDF)**:
```python
image_list = page.get_images()
embedded_image_count = len(image_list)
# Extract each image
for img_index in image_list:
    base_image = doc.extract_image(img_index[0])
    image_data = base_image["image"]
```

**For DOCX (python-docx)**:
```python
image_count = 0
for rel in doc.part.rels.values():
    if "image" in rel.target_ref:
        image_count += 1
```

**For PPT (python-pptx)**:
```python
embedded_images = []
for shape in slide.shapes:
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        embedded_images.append(shape)
```

#### 3. Table Detection

**For PDF (PyMuPDF)**:
```python
# Simple heuristic: Look for grid-like text patterns
text = page.get_text("dict")
tables = []
# Check for table-like structures
# Fallback: Use table detection libraries like camelot or tabula
```

**For DOCX (python-docx)**:
```python
tables = doc.tables
for table in tables:
    row_count = len(table.rows)
    col_count = len(table.columns)
    # Assess complexity
    has_merged_cells = any(cell.is_merged for row in table.rows for cell in row.cells)
    complexity = "complex" if has_merged_cells else "simple"
```

**For PPT (python-pptx)**:
```python
tables = []
for shape in slide.shapes:
    if shape.has_table:
        tables.append(shape.table)
```

#### 4. Chart/Graph Detection

**For PDF**:
```python
# Charts are usually rendered as images or vector graphics
# Check image content or look for chart-like patterns
```

**For DOCX**:
```python
for rel in doc.part.rels.values():
    if "chart" in rel.target_ref:
        # Chart detected - may have underlying data
        chart = rel.target_part
```

**For PPT (python-pptx)**:
```python
for shape in slide.shapes:
    if shape.has_chart:
        chart = shape.chart
        # Try to extract chart data
        chart_data = chart.plots[0].series[0].values
```

#### 5. Constructed Graphics Detection (SmartArt, Shapes)

**For PPT (python-pptx)**:
```python
constructed_graphics = []
for shape in slide.shapes:
    if shape.shape_type in [
        MSO_SHAPE_TYPE.AUTO_SHAPE,
        MSO_SHAPE_TYPE.GROUP,
        MSO_SHAPE_TYPE.FREEFORM
    ]:
        constructed_graphics.append(shape)

# SmartArt detection
if hasattr(shape, 'has_smart_art') and shape.has_smart_art:
    # This is SmartArt - need to render page as image
    requires_rendering = True
```

#### 6. Complete Content Analysis Function

```python
def analyze_page_content(page, doc_type):
    """Analyzes page and returns processing strategy"""

    analysis = {
        "text_quality": "unknown",
        "text_length": 0,
        "embedded_images": 0,
        "tables": {"count": 0, "complexity": "none"},
        "charts": 0,
        "constructed_graphics": 0,
        "processing_strategy": "unknown"
    }

    # Detect based on document type
    if doc_type == "pdf":
        text = page.get_text()
        analysis["text_length"] = len(text)
        analysis["text_quality"] = "high" if len(text) > 100 else "low"
        analysis["embedded_images"] = len(page.get_images())

    elif doc_type == "ppt":
        # PPT-specific analysis
        # ... (as shown above)
        pass

    # Determine strategy
    if analysis["text_length"] > 500 and analysis["embedded_images"] == 0:
        analysis["processing_strategy"] = "text_only"
    elif analysis["embedded_images"] > 0:
        analysis["processing_strategy"] = "hybrid"
    elif analysis["constructed_graphics"] > 0:
        analysis["processing_strategy"] = "render_and_vision"
    else:
        analysis["processing_strategy"] = "adaptive"

    return analysis
```

---

## Next Immediate Steps

### Step 1: Environment Setup (Start Here!)
1. Create Python virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Create `requirements.txt` with initial dependencies

3. Create `.env` file for API keys
   ```
   OPENAI_API_KEY=your_key_here
   ```

4. Create basic folder structure

### Step 2: Build First Extractor
Start with PDF extractor as it's the most common format

### Step 3: Implement Simple LangGraph Workflow
Create a basic workflow with just one agent to validate the setup

### Step 4: Add Parallel Processing
Expand to parallel page processing once basic workflow works

---

## Success Metrics

- **Processing Speed**: < 5 seconds per page on average
- **Extraction Accuracy**: > 95% for text, > 85% for tables
- **Cost Efficiency**: < $0.10 per document on average
- **Supported Formats**: PDF, DOCX, PPTX
- **Max Document Size**: Up to 200 pages

---

## Future Enhancements

1. Support for more formats (Excel, Images, Scanned PDFs)
2. Custom extraction schemas per document type
3. Integration with vector databases for semantic search
4. Web interface for document upload
5. Batch processing API
6. Real-time collaboration features
7. Export to additional formats (Word, Excel)
8. Advanced analytics on extracted data

