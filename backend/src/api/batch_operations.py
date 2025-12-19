"""
Batch operations API endpoints.

Handles batch export, delete, and tag operations on multiple photos.
"""

import asyncio
import uuid
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from src.core.config import settings
from src.workers.batch_worker import (
    process_batch_delete,
    process_batch_export,
    process_batch_tag,
)

router = APIRouter(prefix="/batch", tags=["batch"])


class JobStore:
    """Thread-safe job storage with automatic cleanup of old jobs."""

    MAX_JOBS = 1000
    MAX_AGE_HOURS = 24

    def __init__(self):
        self._jobs: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def add_job(self, job_id: str, job: dict[str, Any]) -> None:
        """Add a new job and cleanup old ones if necessary."""
        async with self._lock:
            self._jobs[job_id] = job
            await self._cleanup_old_jobs_unsafe()

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Get a job by ID."""
        async with self._lock:
            return self._jobs.get(job_id)

    async def update_job(self, job_id: str, updates: dict[str, Any]) -> None:
        """Update a job."""
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(updates)

    async def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent jobs."""
        async with self._lock:
            jobs = list(self._jobs.values())
            jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return jobs[:limit]

    async def _cleanup_old_jobs_unsafe(self) -> None:
        """Remove old jobs (call only while holding lock)."""
        now = datetime.now(UTC)
        cutoff = now.timestamp() - (self.MAX_AGE_HOURS * 3600)

        # Remove old completed jobs
        to_remove = []
        for job_id, job in self._jobs.items():
            if job.get("status") in ("completed", "failed", "cancelled"):
                created_str = job.get("created_at", "")
                if created_str:
                    try:
                        created = datetime.fromisoformat(created_str)
                        if created.timestamp() < cutoff:
                            to_remove.append(job_id)
                    except (ValueError, TypeError):
                        pass

        for job_id in to_remove:
            del self._jobs[job_id]

        # If still too many jobs, remove oldest completed ones
        while len(self._jobs) > self.MAX_JOBS:
            # Find oldest completed job
            oldest_completed = None
            for job_id, job in self._jobs.items():
                if job.get("status") in ("completed", "failed", "cancelled"):
                    oldest_completed = job_id
                    break
            if oldest_completed:
                del self._jobs[oldest_completed]
            else:
                break  # Don't remove active jobs

    def get_sync(self, job_id: str) -> dict[str, Any] | None:
        """Synchronous get for background workers."""
        return self._jobs.get(job_id)

    def update_sync(self, job_id: str, key: str, value: Any) -> None:
        """Thread-safe synchronous update for background workers.

        Uses a simple approach: since OrderedDict operations are atomic
        in CPython and we're updating existing keys, this is safe for
        the specific use case of updating job progress.
        """
        job = self._jobs.get(job_id)
        if job is not None:
            job[key] = value

    def update_job_sync(self, job_id: str, updates: dict[str, Any]) -> None:
        """Thread-safe synchronous batch update for background workers."""
        job = self._jobs.get(job_id)
        if job is not None:
            job.update(updates)


# Global job store instance
_job_store = JobStore()

# Legacy dict access - DEPRECATED: Use _job_store methods instead
# Kept for backward compatibility but workers should use _job_store directly
_jobs = _job_store._jobs


# Flag to disable path validation in tests
_SKIP_PATH_VALIDATION = False


def _validate_export_path(destination: str) -> Path:
    """Validate and sanitize export destination path.

    Prevents path traversal attacks by ensuring the destination
    is within allowed directories.

    Raises:
        HTTPException: If path is invalid or not allowed
    """
    import tempfile

    try:
        dest_path = Path(destination).resolve()
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid destination path: {e}")

    # Allow skipping validation for tests
    if _SKIP_PATH_VALIDATION:
        return dest_path

    # Check for path traversal attempts
    if ".." in destination or destination.startswith(("/etc", "/var/log")):
        raise HTTPException(
            status_code=400,
            detail="Invalid destination path: path traversal not allowed",
        )

    # Allow export to user's home directory or configured data directory
    home_dir = Path.home()
    temp_dir = Path(tempfile.gettempdir())
    allowed_roots = [
        home_dir,
        temp_dir,  # Allow temp directories for tests
        settings.DATA_DIR,
        settings.CACHE_DIR,
    ]

    # Also allow any configured photo roots
    from src.db.connection import get_database_manager

    try:
        db_manager = get_database_manager()
        settings_rows = db_manager.execute_query(
            "SELECT value FROM settings WHERE key = 'roots'"
        )
        if settings_rows:
            import json

            roots = json.loads(settings_rows[0][0])
            allowed_roots.extend(Path(root) for root in roots)
    except Exception:
        pass  # Ignore errors reading config

    # Check if destination is under an allowed root
    for allowed_root in allowed_roots:
        try:
            if allowed_root and dest_path.is_relative_to(allowed_root):
                return dest_path
        except (ValueError, TypeError):
            continue

    raise HTTPException(
        status_code=400, detail="Destination path is not within allowed directories"
    )


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
async def start_batch_export(
    request: BatchExportRequest, background_tasks: BackgroundTasks
):
    """
    Start a batch export operation.

    Returns a job ID that can be used to track progress.
    """
    # Validate destination path to prevent path traversal
    validated_dest = _validate_export_path(request.destination)

    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "type": "export",
        "status": "pending",
        "total_items": len(request.photo_ids),
        "processed_items": 0,
        "failed_items": 0,
        "created_at": datetime.now(UTC).isoformat(),
        "completed_at": None,
        "error": None,
        "request": request.model_dump(),
    }
    await _job_store.add_job(job_id, job)

    # Queue the export job
    background_tasks.add_task(
        process_batch_export,
        job_id,
        request.photo_ids,
        str(validated_dest),  # Use validated path
        request.format,
        request.max_dimension,
        _job_store,  # Pass JobStore for thread-safe updates
    )

    return {"job_id": job_id, "status": "pending"}


@router.post("/delete", response_model=dict)
async def start_batch_delete(
    request: BatchDeleteRequest, background_tasks: BackgroundTasks
):
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
        "created_at": datetime.now(UTC).isoformat(),
        "completed_at": None,
        "error": None,
        "request": request.model_dump(),
    }
    await _job_store.add_job(job_id, job)

    # Queue the delete job
    background_tasks.add_task(
        process_batch_delete,
        job_id,
        request.photo_ids,
        request.permanent,
        _job_store,  # Pass JobStore for thread-safe updates
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
        raise HTTPException(
            status_code=400,
            detail="Invalid operation. Must be: add, remove, or replace",
        )

    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "type": "tag",
        "status": "pending",
        "total_items": len(request.photo_ids),
        "processed_items": 0,
        "failed_items": 0,
        "created_at": datetime.now(UTC).isoformat(),
        "completed_at": None,
        "error": None,
        "request": request.model_dump(),
    }
    await _job_store.add_job(job_id, job)

    # Queue the tag job
    background_tasks.add_task(
        process_batch_tag,
        job_id,
        request.photo_ids,
        request.tags,
        request.operation,
        _job_store,  # Pass JobStore for thread-safe updates
    )

    return {"job_id": job_id, "status": "pending"}


@router.get("/status/{job_id}", response_model=BatchJobStatus)
async def get_batch_job_status(job_id: str):
    """
    Get the status of a batch job.
    """
    job = await _job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return BatchJobStatus(**job)


@router.get("/jobs", response_model=list[BatchJobStatus])
async def list_batch_jobs(limit: int = 50):
    """
    List recent batch jobs.
    """
    jobs = await _job_store.list_jobs(limit)
    return [BatchJobStatus(**job) for job in jobs]


@router.delete("/jobs/{job_id}")
async def cancel_batch_job(job_id: str):
    """
    Cancel a running batch job.
    """
    job = await _job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")

    await _job_store.update_job(
        job_id,
        {
            "status": "cancelled",
            "completed_at": datetime.now(UTC).isoformat(),
        },
    )

    return {"job_id": job_id, "status": "cancelled"}
