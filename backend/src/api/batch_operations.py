"""
Batch operations API endpoints.

Handles batch export, delete, and tag operations on multiple photos.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from src.workers.batch_worker import (
    process_batch_delete,
    process_batch_export,
    process_batch_tag,
)

router = APIRouter(prefix="/batch", tags=["batch"])

# In-memory job storage (replace with Redis in production)
_jobs = {}


class BatchExportRequest(BaseModel):
    """Request to export multiple photos"""

    photo_ids: list[str] = Field(..., description="List of photo IDs to export")
    destination: str = Field(..., description="Destination folder path")
    format: str | None = Field(
        default="original", description="Export format (original, jpg, png)"
    )
    max_dimension: int | None = Field(
        default=None, description="Maximum dimension for resizing"
    )


class BatchDeleteRequest(BaseModel):
    """Request to delete multiple photos"""

    photo_ids: list[str] = Field(..., description="List of photo IDs to delete")
    permanent: bool = Field(
        default=False,
        description="Permanently delete (true) or move to trash (false)",
    )


class BatchTagRequest(BaseModel):
    """Request to tag multiple photos"""

    photo_ids: list[str] = Field(..., description="List of photo IDs to tag")
    tags: list[str] = Field(..., description="Tags to add")
    operation: str = Field(
        default="add", description="Operation: add, remove, or replace"
    )


class BatchJobStatus(BaseModel):
    """Status of a batch job"""

    job_id: str
    type: str
    status: str  # pending, processing, completed, failed
    total_items: int
    processed_items: int
    failed_items: int
    created_at: str
    completed_at: str | None = None
    error: str | None = None


@router.post("/export", response_model=dict)
async def start_batch_export(request: BatchExportRequest, background_tasks: BackgroundTasks):
    """
    Start a batch export operation.

    Returns a job ID that can be used to track progress.
    """
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "type": "export",
        "status": "pending",
        "total_items": len(request.photo_ids),
        "processed_items": 0,
        "failed_items": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "error": None,
        "request": request.dict(),
    }
    _jobs[job_id] = job

    # Queue the export job
    background_tasks.add_task(
        process_batch_export,
        job_id,
        request.photo_ids,
        request.destination,
        request.format,
        request.max_dimension,
        _jobs,
    )

    return {"job_id": job_id, "status": "pending"}


@router.post("/delete", response_model=dict)
async def start_batch_delete(request: BatchDeleteRequest, background_tasks: BackgroundTasks):
    """
    Start a batch delete operation.

    By default, photos are moved to system trash (recoverable).
    Set permanent=true to permanently delete.
    """
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "type": "delete",
        "status": "pending",
        "total_items": len(request.photo_ids),
        "processed_items": 0,
        "failed_items": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "error": None,
        "request": request.dict(),
    }
    _jobs[job_id] = job

    # Queue the delete job
    background_tasks.add_task(
        process_batch_delete,
        job_id,
        request.photo_ids,
        request.permanent,
        _jobs,
    )

    return {"job_id": job_id, "status": "pending"}


@router.post("/tag", response_model=dict)
async def start_batch_tag(request: BatchTagRequest, background_tasks: BackgroundTasks):
    """
    Start a batch tagging operation.

    Operations:
    - add: Add tags to photos (keeps existing tags)
    - remove: Remove specified tags from photos
    - replace: Replace all tags with specified tags
    """
    if request.operation not in ["add", "remove", "replace"]:
        raise HTTPException(status_code=400, detail="Invalid operation. Must be: add, remove, or replace")

    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "type": "tag",
        "status": "pending",
        "total_items": len(request.photo_ids),
        "processed_items": 0,
        "failed_items": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "error": None,
        "request": request.dict(),
    }
    _jobs[job_id] = job

    # Queue the tag job
    background_tasks.add_task(
        process_batch_tag,
        job_id,
        request.photo_ids,
        request.tags,
        request.operation,
        _jobs,
    )

    return {"job_id": job_id, "status": "pending"}


@router.get("/status/{job_id}", response_model=BatchJobStatus)
async def get_batch_job_status(job_id: str):
    """
    Get the status of a batch job.
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return BatchJobStatus(**job)


@router.get("/jobs", response_model=list[BatchJobStatus])
async def list_batch_jobs(limit: int = 50):
    """
    List recent batch jobs.
    """
    jobs = list(_jobs.values())
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    return [BatchJobStatus(**job) for job in jobs[:limit]]


@router.delete("/jobs/{job_id}")
async def cancel_batch_job(job_id: str):
    """
    Cancel a running batch job.
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")

    job["status"] = "cancelled"
    job["completed_at"] = datetime.now(timezone.utc).isoformat()

    return {"job_id": job_id, "status": "cancelled"}
