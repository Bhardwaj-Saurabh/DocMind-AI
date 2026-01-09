"""
FastAPI application for DocMind-AI document extraction.

This API provides endpoints for:
- Document upload and extraction
- Async job processing with status tracking
- Multiple output formats (JSON, Markdown, Plain Text)
- Health checks and system status
"""

import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, BackgroundTasks, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..extractors import create_extractor
from ..graph import create_extraction_workflow
from ..models import ExtractionResult
from ..utils import get_logger, get_config
from ..exceptions import (
    DocMindException,
    UnsupportedFormatError,
    DocumentProcessingError,
)

# Initialize FastAPI app
app = FastAPI(
    title="DocMind-AI API",
    description="Intelligent document extraction API with multimodal AI processing",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
logger = get_logger()
config = get_config()

# In-memory job storage (use Redis/database in production)
jobs: dict[str, dict] = {}

# Temporary upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================================
# Pydantic Models
# ============================================================================

class JobStatus(str):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionRequest(BaseModel):
    """Request for document extraction."""
    enable_vision: bool = Field(default=True, description="Enable vision processing")
    output_format: str = Field(default="json", description="Output format: json, markdown, text")
    include_metadata: bool = Field(default=True, description="Include document metadata")
    preserve_hierarchy: bool = Field(default=True, description="Preserve document hierarchy")


class JobResponse(BaseModel):
    """Response for job creation."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    created_at: str = Field(..., description="Job creation timestamp")


class JobStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current job status")
    progress: float = Field(default=0.0, description="Progress percentage (0-100)")
    message: str = Field(default="", description="Status message")
    created_at: str = Field(..., description="Job creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    result_url: Optional[str] = Field(default=None, description="Result URL if completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ExtractionResultResponse(BaseModel):
    """Response for extraction results."""
    job_id: str
    document_name: str
    total_pages: int
    processing_time: float
    processing_cost: float
    output_format: str
    content: dict | str  # JSON dict or string for markdown/text


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    vision_enabled: bool
    active_jobs: int


# ============================================================================
# Background Task Functions
# ============================================================================

async def process_document_async(
    job_id: str,
    file_path: str,
    original_filename: str,
    enable_vision: bool = True,
    output_format: str = "json",
    include_metadata: bool = True,
    preserve_hierarchy: bool = True,
):
    """
    Background task to process document extraction.

    Args:
        job_id: Unique job identifier
        file_path: Path to uploaded file
        original_filename: Original filename
        enable_vision: Enable vision processing
        output_format: Desired output format
        include_metadata: Include metadata in output
        preserve_hierarchy: Preserve hierarchy in output
    """
    try:
        # Update job status
        jobs[job_id]["status"] = JobStatus.PROCESSING
        jobs[job_id]["updated_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"] = 10.0

        logger.info(
            "Starting document processing",
            job_id=job_id,
            filename=original_filename,
            vision_enabled=enable_vision
        )

        # Create extractor
        extractor = create_extractor(file_path)
        jobs[job_id]["progress"] = 20.0

        # Create workflow
        workflow = create_extraction_workflow()
        jobs[job_id]["progress"] = 30.0

        # Extract document
        result: ExtractionResult = await workflow.extract_async(
            file_path=file_path,
            extractor=extractor,
        )
        jobs[job_id]["progress"] = 80.0

        # Format output based on requested format
        if output_format == "markdown":
            content = result.to_markdown(
                include_metadata=include_metadata,
                preserve_hierarchy=preserve_hierarchy
            )
        elif output_format == "text":
            content = result.to_text()
        else:  # json
            content = result.model_dump()

        jobs[job_id]["progress"] = 90.0

        # Store result
        jobs[job_id].update({
            "status": JobStatus.COMPLETED,
            "progress": 100.0,
            "updated_at": datetime.now().isoformat(),
            "result": {
                "document_name": original_filename,
                "total_pages": result.metadata.total_pages,
                "processing_time": result.total_processing_time,
                "processing_cost": result.total_processing_cost,
                "output_format": output_format,
                "content": content,
            },
        })

        logger.info(
            "Document processing completed",
            job_id=job_id,
            pages=result.metadata.total_pages,
            cost=result.total_processing_cost,
            time=result.total_processing_time
        )

    except UnsupportedFormatError as e:
        logger.error(f"Unsupported format: {e}", job_id=job_id)
        jobs[job_id].update({
            "status": JobStatus.FAILED,
            "updated_at": datetime.now().isoformat(),
            "error": f"Unsupported file format: {str(e)}",
        })

    except DocumentProcessingError as e:
        logger.error(f"Processing error: {e}", job_id=job_id, exc_info=True)
        jobs[job_id].update({
            "status": JobStatus.FAILED,
            "updated_at": datetime.now().isoformat(),
            "error": f"Document processing failed: {str(e)}",
        })

    except Exception as e:
        logger.error(f"Unexpected error: {e}", job_id=job_id, exc_info=True)
        jobs[job_id].update({
            "status": JobStatus.FAILED,
            "updated_at": datetime.now().isoformat(),
            "error": f"Internal error: {str(e)}",
        })

    finally:
        # Clean up uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up file: {e}", file_path=file_path)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DocMind-AI API",
        "version": "0.1.0",
        "description": "Intelligent document extraction with multimodal AI",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns system status and configuration.
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        vision_enabled=bool(config.openai_api_key),
        active_jobs=sum(1 for job in jobs.values() if job["status"] == JobStatus.PROCESSING),
    )


@app.post("/extract", response_model=JobResponse)
async def extract_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to extract"),
    enable_vision: bool = Query(default=True, description="Enable vision processing"),
    output_format: str = Query(default="json", description="Output format: json, markdown, text"),
    include_metadata: bool = Query(default=True, description="Include document metadata"),
    preserve_hierarchy: bool = Query(default=True, description="Preserve document hierarchy"),
):
    """
    Extract content from uploaded document (async processing).

    Supports: PDF, DOCX, PPTX

    Returns a job ID for status tracking.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate format
    if output_format not in ["json", "markdown", "text"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid output_format. Must be: json, markdown, or text"
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file
    file_extension = Path(file.filename).suffix
    temp_file_path = UPLOAD_DIR / f"{job_id}{file_extension}"

    try:
        # Save file
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Create job entry
        jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "progress": 0.0,
            "message": "Job created, waiting to process",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "filename": file.filename,
            "file_path": str(temp_file_path),
        }

        # Add background task
        background_tasks.add_task(
            process_document_async,
            job_id=job_id,
            file_path=str(temp_file_path),
            original_filename=file.filename,
            enable_vision=enable_vision,
            output_format=output_format,
            include_metadata=include_metadata,
            preserve_hierarchy=preserve_hierarchy,
        )

        logger.info(
            "Extraction job created",
            job_id=job_id,
            filename=file.filename,
            output_format=output_format
        )

        return JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Document extraction job created. Use /jobs/{job_id} to check status.",
            created_at=jobs[job_id]["created_at"],
        )

    except Exception as e:
        logger.error(f"Failed to create extraction job: {e}", exc_info=True)
        # Clean up file if it exists
        if temp_file_path.exists():
            temp_file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of an extraction job.

    Returns current status, progress, and result URL if completed.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0.0),
        message=job.get("message", ""),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        result_url=f"/jobs/{job_id}/result" if job["status"] == JobStatus.COMPLETED else None,
        error=job.get("error"),
    )


@app.get("/jobs/{job_id}/result", response_model=ExtractionResultResponse)
async def get_job_result(job_id: str):
    """
    Get extraction result for completed job.

    Returns the extracted content in the requested format.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] == JobStatus.PENDING:
        raise HTTPException(status_code=202, detail="Job is still pending")

    if job["status"] == JobStatus.PROCESSING:
        raise HTTPException(status_code=202, detail="Job is still processing")

    if job["status"] == JobStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {job.get('error', 'Unknown error')}"
        )

    if "result" not in job:
        raise HTTPException(status_code=500, detail="Result not found")

    result = job["result"]

    return ExtractionResultResponse(
        job_id=job_id,
        document_name=result["document_name"],
        total_pages=result["total_pages"],
        processing_time=result["processing_time"],
        processing_cost=result["processing_cost"],
        output_format=result["output_format"],
        content=result["content"],
    )


@app.get("/jobs/{job_id}/result/markdown", response_class=PlainTextResponse)
async def get_job_result_markdown(job_id: str):
    """
    Get extraction result as markdown (plain text response).

    Useful for direct download or display.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job['status']}"
        )

    if "result" not in job:
        raise HTTPException(status_code=500, detail="Result not found")

    result = job["result"]

    if result["output_format"] != "markdown":
        raise HTTPException(
            status_code=400,
            detail=f"Result format is {result['output_format']}, not markdown"
        )

    return PlainTextResponse(content=result["content"])


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job and its results.

    Use this to clean up completed or failed jobs.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs.pop(job_id)

    logger.info("Job deleted", job_id=job_id)

    return {"message": "Job deleted successfully", "job_id": job_id}


@app.get("/jobs", response_model=list[JobStatusResponse])
async def list_jobs(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=500, description="Max number of jobs to return"),
):
    """
    List all jobs with optional filtering.

    Args:
        status: Filter by job status (pending, processing, completed, failed)
        limit: Maximum number of jobs to return
    """
    filtered_jobs = jobs.values()

    if status:
        filtered_jobs = [j for j in filtered_jobs if j["status"] == status]

    # Sort by created_at descending (newest first)
    sorted_jobs = sorted(
        filtered_jobs,
        key=lambda x: x["created_at"],
        reverse=True
    )[:limit]

    return [
        JobStatusResponse(
            job_id=job["job_id"],
            status=job["status"],
            progress=job.get("progress", 0.0),
            message=job.get("message", ""),
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            result_url=f"/jobs/{job['job_id']}/result" if job["status"] == JobStatus.COMPLETED else None,
            error=job.get("error"),
        )
        for job in sorted_jobs
    ]


# ============================================================================
# Synchronous Extraction Endpoint (for small documents)
# ============================================================================

@app.post("/extract/sync", response_model=ExtractionResultResponse)
async def extract_document_sync(
    file: UploadFile = File(..., description="Document file to extract"),
    enable_vision: bool = Query(default=True, description="Enable vision processing"),
    output_format: str = Query(default="json", description="Output format: json, markdown, text"),
    include_metadata: bool = Query(default=True, description="Include document metadata"),
    preserve_hierarchy: bool = Query(default=True, description="Preserve document hierarchy"),
):
    """
    Extract content from document synchronously (blocking).

    WARNING: This endpoint blocks until processing is complete.
    Use /extract for async processing with large documents.

    Recommended for documents < 10 pages.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if output_format not in ["json", "markdown", "text"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid output_format. Must be: json, markdown, or text"
        )

    # Generate temporary file path
    job_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    temp_file_path = UPLOAD_DIR / f"{job_id}{file_extension}"

    try:
        # Save file
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(
            "Starting synchronous extraction",
            job_id=job_id,
            filename=file.filename
        )

        # Create extractor
        extractor = create_extractor(str(temp_file_path))

        # Create workflow
        workflow = create_extraction_workflow()

        # Extract document (async)
        result: ExtractionResult = await workflow.extract_async(
            file_path=str(temp_file_path),
            extractor=extractor,
        )

        # Format output
        if output_format == "markdown":
            content = result.to_markdown(
                include_metadata=include_metadata,
                preserve_hierarchy=preserve_hierarchy
            )
        elif output_format == "text":
            content = result.to_text()
        else:  # json
            content = result.model_dump()

        logger.info(
            "Synchronous extraction completed",
            job_id=job_id,
            pages=result.metadata.total_pages,
            cost=result.total_processing_cost
        )

        return ExtractionResultResponse(
            job_id=job_id,
            document_name=file.filename,
            total_pages=result.metadata.total_pages,
            processing_time=result.total_processing_time,
            processing_cost=result.total_processing_cost,
            output_format=output_format,
            content=content,
        )

    except UnsupportedFormatError as e:
        logger.error(f"Unsupported format: {e}")
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {str(e)}")

    except DocumentProcessingError as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    finally:
        # Clean up
        if temp_file_path.exists():
            temp_file_path.unlink()


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    logger.info(
        f"DocMind-AI API starting - version=0.1.0 vision_enabled={bool(config.openai_api_key)}"
    )

    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("DocMind-AI API shutting down")

    # Clean up any remaining files
    for file_path in UPLOAD_DIR.glob("*"):
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to clean up file: {e}", file_path=str(file_path))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
