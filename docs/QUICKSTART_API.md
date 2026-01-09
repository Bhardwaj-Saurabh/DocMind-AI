# DocMind-AI API Quick Start Guide

Get started with the DocMind-AI REST API in under 5 minutes!

## Prerequisites

- Python 3.10 or higher
- OpenAI API key (for vision processing)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/DocMind-AI.git
cd DocMind-AI
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

## Running the Server

### Development Mode

```bash
python run_api.py --reload
```

Server starts at: http://localhost:8000

### Production Mode

```bash
python run_api.py --host 0.0.0.0 --port 8000 --workers 4
```

## Using the API

### Option 1: Interactive Documentation (Recommended)

Open your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Try the "Try it out" button on any endpoint!

### Option 2: Python Client

```python
from examples.api_client_example import DocMindClient

# Create client
client = DocMindClient()

# Extract document
result = client.extract_and_wait(
    file_path="document.pdf",
    output_format="markdown"
)

# Save result
with open("output.md", "w") as f:
    f.write(result["content"])
```

### Option 3: cURL

```bash
# Upload document
curl -X POST "http://localhost:8000/extract?output_format=markdown" \
  -F "file=@document.pdf"

# Get job status
curl http://localhost:8000/jobs/{job_id}

# Get result
curl http://localhost:8000/jobs/{job_id}/result/markdown -o output.md
```

### Option 4: Command-Line Client

```bash
python examples/api_client_example.py document.pdf -o output.md
```

## Common Use Cases

### 1. Extract PDF to Markdown (for RAG)

```bash
curl -X POST "http://localhost:8000/extract?output_format=markdown&preserve_hierarchy=true" \
  -F "file=@report.pdf" | jq -r '.job_id'
```

### 2. Fast Text Extraction (No Vision)

```bash
curl -X POST "http://localhost:8000/extract?enable_vision=false&output_format=text" \
  -F "file=@document.pdf"
```

### 3. Synchronous Extraction (Small Documents)

```bash
curl -X POST "http://localhost:8000/extract/sync?output_format=json" \
  -F "file=@small_doc.pdf" | jq .
```

### 4. Check API Health

```bash
curl http://localhost:8000/health | jq .
```

## Docker Deployment

### Quick Start

```bash
# Build image
docker build -t docmind-ai .

# Run container
docker run -p 8000:8000 --env-file .env docmind-ai
```

### Using Docker Compose

```bash
# Start server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop server
docker-compose down
```

## Next Steps

1. **Read Full Documentation**: See [API_README.md](API_README.md)
2. **Explore Examples**: Check [examples/api_client_example.py](examples/api_client_example.py)
3. **Run Tests**: `pytest tests/test_api.py -v`
4. **Configure Settings**: Edit `.env` file for custom configuration

## Troubleshooting

### Server won't start

- Check port 8000 is not in use
- Verify Python version: `python --version`
- Reinstall dependencies: `pip install -r requirements.txt`

### "Vision processing disabled"

- Check `.env` file exists and contains `OPENAI_API_KEY`
- Verify API key is valid

### Slow processing

- Disable vision for faster processing: `enable_vision=false`
- Use async endpoint `/extract` instead of `/extract/sync`

## Support

- **Documentation**: http://localhost:8000/docs
- **Issues**: https://github.com/yourusername/DocMind-AI/issues
- **Examples**: See `examples/` directory

---

**Ready to extract!** 🚀

Try: `python examples/api_client_example.py document.pdf`
