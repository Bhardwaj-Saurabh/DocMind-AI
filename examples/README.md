# DocMind-AI Examples

This directory contains examples demonstrating different features and use cases of DocMind-AI.

## Prerequisites

1. Install dependencies:
```bash
poetry install
```

2. Set up your environment variables in `.env`:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Examples

### 1. Quickstart (`quickstart.py`)

The simplest way to get started with DocMind-AI.

**Features demonstrated:**
- Basic PDF extraction
- Automatic vision processing (if API key available)
- Result access and export

**Run:**
```bash
python examples/quickstart.py
```

**Best for:** First-time users, simple extraction tasks

---

### 2. Basic PDF Extraction (`basic_pdf_extraction.py`)

Manual extraction without LangGraph workflow.

**Features demonstrated:**
- Direct PDFExtractor usage
- Content analysis per page
- Strategy recommendations
- Cost estimation

**Run:**
```bash
python examples/basic_pdf_extraction.py
```

**Best for:** Understanding the extraction process, custom workflows

---

### 3. LangGraph Extraction (`langgraph_extraction.py`)

Text-only extraction using LangGraph workflow (no vision).

**Features demonstrated:**
- LangGraph StateGraph workflow
- Content analysis agent
- Text extraction agent
- State management
- Cost tracking

**Run:**
```bash
python examples/langgraph_extraction.py
```

**Best for:** Text-heavy documents, understanding LangGraph integration

---

### 4. Multimodal Extraction (`multimodal_extraction.py`) ⭐

**The complete end-to-end example with vision processing.**

**Features demonstrated:**
- Full workflow: analyze → extract_text → process_vision → finalize
- Adaptive routing based on content type
- Vision API for charts, images, scanned pages
- Detailed cost analysis and savings calculation
- Page-by-page breakdown
- Multiple export formats (text, markdown, report)

**Run:**
```bash
# Use your own PDF
python examples/multimodal_extraction.py /path/to/your/document.pdf

# Or use the default sample
python examples/multimodal_extraction.py
```

**Best for:**
- Documents with mixed content (text + images + charts + tables)
- Understanding cost optimization
- Production use cases

**Expected document structure for best demonstration:**
- Pages with pure text (articles, reports)
- Pages with charts and graphs
- Pages with images and diagrams
- Pages with tables
- Scanned document pages

**Output:**
```
output/multimodal_example/
  ├── document_extracted.txt      # Plain text extraction
  ├── document_extracted.md       # Markdown with structure
  └── document_report.txt         # Processing report with costs
```

---

## Sample Output

### Cost Savings Example

```
═══════════════════════════════════════════════════════════════════
  Cost Analysis
═══════════════════════════════════════════════════════════════════

Adaptive Approach (DocMind-AI):
  Total Cost: $0.0342
  Processing Time: 8.45s
  Average Quality Score: 0.92

Naive Approach (Vision API for all pages):
  Estimated Cost: $0.2400
  Estimated Time: 36.00s

💰 Cost Savings: $0.2058 (85.8% reduction)
⚡ Time Savings: 27.55s

Strategy Breakdown:
  TEXT_ONLY: 8 pages
  VISION_PRIMARY: 2 pages
  HYBRID_SIMPLE: 2 pages
```

## API Key Requirements

### Text-Only Extraction
No API keys required - uses PyMuPDF for text extraction.

### Vision Processing
Requires OpenAI API key for:
- GPT-4 Vision API (charts, images, scanned documents)
- Advanced table extraction
- Complex visual content

Set in `.env`:
```bash
OPENAI_API_KEY=your_key_here
```

### Advanced Features (Future)
Optional API keys for advanced routing:
- `ANTHROPIC_API_KEY` - Claude models
- Additional model providers

## Troubleshooting

### Vision Processing Disabled

If you see:
```
⚠️  Vision processing disabled (no API key)
💡 Set OPENAI_API_KEY in .env to enable vision features
```

**Solution:** Add your OpenAI API key to `.env`:
```bash
OPENAI_API_KEY=sk-...
```

### File Not Found

If you see:
```
❌ File not found: data/samples/sample_document.pdf
```

**Solution:** Either:
1. Create the sample directory and add a PDF:
   ```bash
   mkdir -p data/samples
   cp /path/to/your/pdf data/samples/sample_document.pdf
   ```

2. Or run with your own PDF:
   ```bash
   python examples/multimodal_extraction.py /path/to/your/document.pdf
   ```

### Module Import Errors

If you see import errors:

**Solution:**
```bash
# Make sure you're in the project root
cd /path/to/DocMind-AI

# Install dependencies
poetry install

# Run with poetry
poetry run python examples/multimodal_extraction.py
```

## Next Steps

1. Start with `quickstart.py` to verify your setup
2. Try `multimodal_extraction.py` with your own documents
3. Explore the source code in `src/` to understand the architecture
4. Customize the workflow for your specific use case

## Need Help?

- Check the main [README.md](../README.md) for architecture overview
- Read the [claude.md](../claude.md) for design decisions
- Review the code comments in `src/` for implementation details
