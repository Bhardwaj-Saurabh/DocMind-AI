# DocMind-AI REST API Documentation

A comprehensive FastAPI-based REST API for intelligent document extraction with multimodal AI processing.

## Features

- ✅ **Async Document Processing** - Background job processing with status tracking
- ✅ **Multiple Output Formats** - JSON, Markdown, Plain Text
- ✅ **RAG-Optimized Markdown** - Hierarchical structure preserved for embeddings
- ✅ **Multimodal AI** - Vision processing for images, charts, diagrams
- ✅ **Format Support** - PDF, DOCX, PPTX
- ✅ **Job Management** - Create, track, retrieve, and delete extraction jobs
- ✅ **Interactive Docs** - Auto-generated Swagger UI and ReDoc

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Start Server

**Development mode** (with auto-reload):
```bash
python run_api.py --reload
```

**Production mode**:
```bash
python run_api.py --host 0.0.0.0 --port 8000
```

### 4. Access Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check

#### `GET /health`

Check API health and configuration.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "vision_enabled": true,
  "active_jobs": 2
}
```

---

### Document Extraction (Async)

#### `POST /extract`

Upload document for async extraction. Returns job ID for tracking.

**Parameters:**
- `file` (form-data, required): Document file (PDF, DOCX, PPTX)
- `enable_vision` (query, optional): Enable vision processing (default: true)
- `output_format` (query, optional): Output format - `json`, `markdown`, `text` (default: json)
- `include_metadata` (query, optional): Include document metadata (default: true)
- `preserve_hierarchy` (query, optional): Preserve document hierarchy (default: true)

**Example:**
```bash
curl -X POST "http://localhost:8000/extract?output_format=markdown" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Document extraction job created. Use /jobs/{job_id} to check status.",
  "created_at": "2026-01-09T10:30:00.000000"
}
```

---

### Document Extraction (Sync)

#### `POST /extract/sync`

Upload document for synchronous extraction. **Blocks until complete.**

⚠️ **Warning:** Use for small documents only (< 10 pages). For larger documents, use async endpoint.

**Parameters:** Same as `/extract`

**Example:**
```bash
curl -X POST "http://localhost:8000/extract/sync?output_format=markdown" \
  -F "file=@small_doc.pdf"
```

**Response:**
```json
{
  "job_id": "...",
  "document_name": "small_doc.pdf",
  "total_pages": 3,
  "processing_time": 5.23,
  "processing_cost": 0.0234,
  "output_format": "markdown",
  "content": "# Document Title\n\n## Page 1\n..."
}
```

---

### Job Status

#### `GET /jobs/{job_id}`

Check status of extraction job.

**Example:**
```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 65.0,
  "message": "",
  "created_at": "2026-01-09T10:30:00.000000",
  "updated_at": "2026-01-09T10:31:15.000000",
  "result_url": null,
  "error": null
}
```

**Status Values:**
- `pending` - Job created, waiting to process
- `processing` - Currently processing
- `completed` - Processing complete, result available
- `failed` - Processing failed, check error field

---

### Get Job Result

#### `GET /jobs/{job_id}/result`

Retrieve extraction result (JSON format).

**Example:**
```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000/result
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_name": "report.pdf",
  "total_pages": 25,
  "processing_time": 45.67,
  "processing_cost": 0.1234,
  "output_format": "markdown",
  "content": "# Annual Report 2024\n\n## Executive Summary\n..."
}
```

---

### Get Job Result as Markdown

#### `GET /jobs/{job_id}/result/markdown`

Retrieve extraction result as plain text markdown (useful for download).

**Example:**
```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000/result/markdown \
  -o output.md
```

**Response:** Plain text markdown content

---

### List Jobs

#### `GET /jobs`

List all jobs with optional filtering.

**Parameters:**
- `status` (query, optional): Filter by status (`pending`, `processing`, `completed`, `failed`)
- `limit` (query, optional): Max results (default: 50, max: 500)

**Example:**
```bash
curl "http://localhost:8000/jobs?status=completed&limit=10"
```

**Response:**
```json
[
  {
    "job_id": "...",
    "status": "completed",
    "progress": 100.0,
    "message": "",
    "created_at": "2026-01-09T10:30:00",
    "updated_at": "2026-01-09T10:35:00",
    "result_url": "/jobs/.../result",
    "error": null
  },
  ...
]
```

---

### Delete Job

#### `DELETE /jobs/{job_id}`

Delete job and its results.

**Example:**
```bash
curl -X DELETE http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "message": "Job deleted successfully",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Usage Examples

### Python Client Example

```python
import requests
import time

# Upload document
url = "http://localhost:8000/extract"
files = {"file": open("document.pdf", "rb")}
params = {
    "output_format": "markdown",
    "enable_vision": True,
    "preserve_hierarchy": True
}

response = requests.post(url, files=files, params=params)
job_id = response.json()["job_id"]
print(f"Job created: {job_id}")

# Poll for completion
status_url = f"http://localhost:8000/jobs/{job_id}"
while True:
    status_response = requests.get(status_url)
    status_data = status_response.json()

    print(f"Status: {status_data['status']} - Progress: {status_data['progress']}%")

    if status_data["status"] == "completed":
        print("Processing complete!")
        break
    elif status_data["status"] == "failed":
        print(f"Processing failed: {status_data['error']}")
        break

    time.sleep(2)

# Get result
result_url = f"http://localhost:8000/jobs/{job_id}/result"
result = requests.get(result_url).json()

print(f"Document: {result['document_name']}")
print(f"Pages: {result['total_pages']}")
print(f"Cost: ${result['processing_cost']:.4f}")
print(f"Content length: {len(result['content'])} chars")

# Save markdown
with open("output.md", "w", encoding="utf-8") as f:
    f.write(result["content"])
```

### cURL Example

```bash
#!/bin/bash

# Upload document
RESPONSE=$(curl -s -X POST "http://localhost:8000/extract?output_format=markdown" \
  -F "file=@document.pdf")

JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Wait for completion
while true; do
  STATUS=$(curl -s "http://localhost:8000/jobs/$JOB_ID" | jq -r '.status')
  PROGRESS=$(curl -s "http://localhost:8000/jobs/$JOB_ID" | jq -r '.progress')

  echo "Status: $STATUS - Progress: $PROGRESS%"

  if [ "$STATUS" == "completed" ]; then
    echo "Processing complete!"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo "Processing failed!"
    exit 1
  fi

  sleep 2
done

# Download result
curl "http://localhost:8000/jobs/$JOB_ID/result/markdown" -o output.md
echo "Saved to output.md"
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function extractDocument(filePath) {
  // Upload document
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));

  const uploadResponse = await axios.post(
    'http://localhost:8000/extract?output_format=markdown',
    formData,
    { headers: formData.getHeaders() }
  );

  const jobId = uploadResponse.data.job_id;
  console.log(`Job created: ${jobId}`);

  // Poll for completion
  while (true) {
    const statusResponse = await axios.get(
      `http://localhost:8000/jobs/${jobId}`
    );

    const { status, progress } = statusResponse.data;
    console.log(`Status: ${status} - Progress: ${progress}%`);

    if (status === 'completed') {
      console.log('Processing complete!');
      break;
    } else if (status === 'failed') {
      throw new Error(`Processing failed: ${statusResponse.data.error}`);
    }

    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // Get result
  const resultResponse = await axios.get(
    `http://localhost:8000/jobs/${jobId}/result`
  );

  const result = resultResponse.data;
  console.log(`Document: ${result.document_name}`);
  console.log(`Pages: ${result.total_pages}`);
  console.log(`Cost: $${result.processing_cost.toFixed(4)}`);

  // Save markdown
  fs.writeFileSync('output.md', result.content, 'utf-8');
  console.log('Saved to output.md');
}

extractDocument('./document.pdf').catch(console.error);
```

---

## Output Formats

### JSON Format

Complete structured data with all metadata:

```json
{
  "metadata": {
    "document_id": "...",
    "file_name": "report.pdf",
    "total_pages": 25,
    ...
  },
  "pages": [
    {
      "page_number": 1,
      "text": "...",
      "images": [...],
      "tables": [...],
      "charts": [...]
    }
  ],
  "full_text": "...",
  "all_images": [...],
  "all_tables": [...],
  "all_charts": [...]
}
```

### Markdown Format (RAG-Optimized)

Hierarchical markdown with:
- Document structure preserved (headings H1-H6)
- Images converted to detailed text descriptions
- Tables in markdown table format
- Charts converted to comprehensive narratives
- Page markers for chunking

Perfect for RAG applications and embeddings.

### Text Format

Plain text concatenation of all extracted text.

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
VISION_MODEL=gpt-4o
VISION_PROVIDER=openai
MAX_TOKENS=4000
TEMPERATURE=0.0
```

### Server Configuration

Modify `run_api.py` or pass command-line arguments:

```bash
python run_api.py \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

---

## Production Deployment

### Using Uvicorn

```bash
uvicorn src.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t docmind-ai .
docker run -p 8000:8000 --env-file .env docmind-ai
```

### Using Gunicorn (Production)

```bash
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info \
  --access-logfile - \
  --error-logfile -
```

---

## Error Handling

### HTTP Status Codes

- `200 OK` - Success
- `202 Accepted` - Job still processing
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Processing error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Performance Considerations

### Processing Time

- **Text-only pages**: 0.1-0.5 seconds per page
- **Pages with tables**: 0.5-2 seconds per page
- **Pages with vision processing**: 2-5 seconds per page

### Cost Estimation

- **Text extraction**: ~$0.001 per page
- **Structural parsing**: ~$0.002-0.005 per page
- **Vision processing**: ~$0.02-0.05 per page

### Optimization Tips

1. **Disable vision for text-heavy documents**: Set `enable_vision=false`
2. **Use async endpoint**: For documents > 5 pages
3. **Batch processing**: Submit multiple jobs in parallel
4. **Use text format**: When metadata not needed

---

## Troubleshooting

### "Vision processing disabled"

- Ensure `OPENAI_API_KEY` is set in `.env`
- Check API key has access to vision models

### "Unsupported format"

- Only PDF, DOCX, PPTX are supported
- Check file extension is correct

### "Job not found"

- Jobs are stored in memory (cleared on restart)
- For production, implement Redis/database storage

### Slow processing

- Vision API calls are the bottleneck
- Consider disabling vision for faster processing
- Use sync endpoint only for small documents

---

## Development

### Running Tests

```bash
pytest tests/test_api.py -v
```

### Code Quality

```bash
# Format code
black src/api/

# Lint
ruff src/api/

# Type check
mypy src/api/
```

### Adding New Endpoints

1. Add endpoint function in `src/api/main.py`
2. Define request/response models
3. Add error handling
4. Update this documentation
5. Add tests

---

## Roadmap

- [ ] Redis/database backend for job storage
- [ ] Webhook notifications on job completion
- [ ] Batch processing endpoint
- [ ] Authentication and API keys
- [ ] Rate limiting
- [ ] Streaming responses
- [ ] WebSocket for real-time progress
- [ ] PDF annotation output
- [ ] Custom extraction schemas

---

## Support

- **Issues**: https://github.com/yourusername/DocMind-AI/issues
- **Documentation**: http://localhost:8000/docs
- **API Reference**: http://localhost:8000/redoc

---

## License

MIT License - See LICENSE file for details
