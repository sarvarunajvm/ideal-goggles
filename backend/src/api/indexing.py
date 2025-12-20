"""Indexing control endpoints for Ideal Goggles API."""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from ..core.config import settings
from ..core.logging_config import get_logger, log_error_with_context, log_slow_operation
from ..core.middleware import get_request_id
from ..db.connection import get_database_manager

router = APIRouter()
logger = get_logger(__name__)


def _is_e2e_test_mode() -> bool:
    """
    Return True when running in Playwright E2E mode.

    We use this to skip heavy ML phases (CLIP embeddings, face detection) to keep
    E2E runs fast and avoid OOM kills in constrained environments.
    """
    return os.getenv("E2E_TEST", "").strip().lower() in {"1", "true", "yes", "on"}


class IndexStatus(BaseModel):
    """Index status model."""

    status: str = Field(description="Current indexing status")
    progress: dict[str, Any] = Field(description="Progress information")
    errors: list[str] = Field(description="List of errors encountered")
    started_at: datetime | None = Field(description="Indexing start time")
    estimated_completion: datetime | None = Field(
        description="Estimated completion time"
    )


class StartIndexRequest(BaseModel):
    """Request model for starting indexing."""

    full: bool = Field(default=False, description="Whether to perform full re-index")


class IndexingStateManager:
    """Thread-safe manager for indexing state using asyncio.Lock."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._state = {
            "status": "idle",
            "progress": {
                "total_files": 0,
                "processed_files": 0,
                "current_phase": "discovery",
            },
            "errors": [],
            "started_at": None,
            "estimated_completion": None,
            "task": None,
            "last_completed_at": None,
            "request_count": 0,
        }

    async def get_state(self) -> dict[str, Any]:
        """Get a copy of the current state."""
        async with self._lock:
            return self._state.copy()

    async def get_value(self, key: str) -> Any:
        """Get a specific value from state."""
        async with self._lock:
            return self._state.get(key)

    async def set_value(self, key: str, value: Any) -> None:
        """Set a specific value in state."""
        async with self._lock:
            self._state[key] = value

    async def update_state(self, updates: dict[str, Any]) -> None:
        """Update multiple state values atomically."""
        async with self._lock:
            self._state.update(updates)

    async def update_progress(self, **kwargs) -> None:
        """Update progress values atomically."""
        async with self._lock:
            self._state["progress"].update(kwargs)

    async def append_error(self, error: str) -> None:
        """Append an error to the errors list."""
        async with self._lock:
            self._state["errors"].append(error)

    async def extend_errors(self, errors: list[str]) -> None:
        """Extend errors list with multiple errors."""
        async with self._lock:
            self._state["errors"].extend(errors)

    async def reset_for_new_indexing(self) -> None:
        """Reset state for a new indexing run.

        Note: We use clear() + update() instead of reassigning self._state
        to preserve the reference that _indexing_state points to.
        """
        async with self._lock:
            request_count = self._state.get("request_count", 0) + 1
            self._state.clear()
            self._state.update(
                {
                    "status": "indexing",
                    "progress": {
                        "total_files": 0,
                        "processed_files": 0,
                        "current_phase": "discovery",
                    },
                    "errors": [],
                    "started_at": datetime.now(),
                    "estimated_completion": None,
                    "task": None,
                    "last_completed_at": None,
                    "request_count": request_count,
                }
            )

    async def is_indexing(self) -> bool:
        """Check if indexing is currently running."""
        async with self._lock:
            return self._state["status"] == "indexing"

    async def calculate_estimated_completion(self) -> datetime | None:
        """Calculate estimated completion time based on current progress."""
        async with self._lock:
            if (
                not self._state["started_at"]
                or self._state["progress"]["total_files"] == 0
            ):
                return None

            progress = self._state["progress"]
            current_time = datetime.now()
            elapsed = (current_time - self._state["started_at"]).total_seconds()

            if progress["processed_files"] == 0:
                return None

            progress_ratio = progress["processed_files"] / progress["total_files"]
            if progress_ratio <= 0:
                return None

            estimated_total_time = elapsed / progress_ratio
            remaining_time = estimated_total_time - elapsed

            return current_time + timedelta(seconds=remaining_time)

    # Synchronous access for backward compatibility (use sparingly)
    def get_state_sync(self) -> dict[str, Any]:
        """Get state synchronously (not thread-safe, use only when necessary).

        Returns a deep copy to prevent callers from modifying nested structures
        like 'progress' which would corrupt the internal state.
        """
        import copy

        return copy.deepcopy(self._state)

    def set_value_sync(self, key: str, value: Any) -> None:
        """Set value synchronously (not thread-safe, use only when necessary)."""
        self._state[key] = value

    def reset_state_sync(self) -> None:
        """Reset state synchronously for testing purposes.

        Note: We use clear() + update() instead of reassigning self._state
        to preserve the reference that _indexing_state points to.
        """
        self._state.clear()
        self._state.update(
            {
                "status": "idle",
                "progress": {
                    "total_files": 0,
                    "processed_files": 0,
                    "current_phase": "discovery",
                },
                "errors": [],
                "started_at": None,
                "estimated_completion": None,
                "task": None,
                "last_completed_at": None,
                "request_count": 0,
            }
        )


# Global state manager instance
_state_manager = IndexingStateManager()

# Legacy global state for backward compatibility (deprecated)
# Note: This is a reference to the internal state dict. Changes will be reflected
# in _state_manager._state. For thread-safe access, use _state_manager methods.
_indexing_state = _state_manager._state


def reset_indexing_state_for_tests() -> None:
    """Reset indexing state for testing purposes. Do not use in production."""
    _state_manager.reset_state_sync()


@router.post("/index/start")
async def start_indexing(
    background_tasks: BackgroundTasks, request: StartIndexRequest | None = None
) -> dict[str, Any]:
    """
    Start indexing process.

    Args:
        request: Indexing configuration
        background_tasks: FastAPI background tasks

    Returns:
        Indexing start confirmation
    """
    # Check if indexing is already running (thread-safe)
    if await _state_manager.is_indexing():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Indexing already in progress"
        )

    try:
        # Use default values if no request provided
        if request is None:
            request = StartIndexRequest()

        # Reset indexing state atomically
        await _state_manager.reset_for_new_indexing()

        # Start indexing in background and store task for cancellation
        task = asyncio.create_task(_run_indexing_process(request.full))
        await _state_manager.set_value("task", task)
        background_tasks.add_task(_monitor_indexing_task, task)

        state = await _state_manager.get_state()
        started_at = state["started_at"]

        logger.info(
            "Indexing started successfully",
            extra={
                "request_id": get_request_id(),
                "full_reindex": request.full,
                "started_at": started_at.isoformat() if started_at else None,
            },
        )

        return {
            "message": "Indexing started successfully",
            "full_reindex": request.full,
            "started_at": started_at.isoformat() if started_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        await _state_manager.update_state({"status": "error"})
        await _state_manager.append_error(str(e))

        # Sanitize error message for client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start indexing. Please check logs for details.",
        )


@router.get("/index/status", response_model=IndexStatus)
async def get_indexing_status() -> IndexStatus:
    """
    Get current indexing status.

    Returns:
        Current indexing status and progress
    """
    state = await _state_manager.get_state()

    # Calculate estimated completion in real-time
    estimated_completion = None
    if state["status"] == "indexing":
        estimated_completion = await _state_manager.calculate_estimated_completion()

    # Add percentage to progress
    progress = dict(state["progress"])
    if progress.get("total_files", 0) > 0:
        progress["percentage"] = (
            progress.get("processed_files", 0) / progress["total_files"]
        ) * 100
    else:
        progress["percentage"] = 0.0

    return IndexStatus(
        status=state["status"],
        progress=progress,
        errors=state["errors"],
        started_at=state["started_at"],
        estimated_completion=estimated_completion,
    )


@router.post("/index/stop")
async def stop_indexing() -> dict[str, Any]:
    """
    Stop current indexing process.

    Returns:
        Stop confirmation
    """
    if not await _state_manager.is_indexing():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No indexing process is currently running",
        )

    try:
        # Cancel the indexing task if it exists
        task = await _state_manager.get_value("task")
        if task:
            task.cancel()

        await _state_manager.set_value("status", "stopped")

        logger.info("Indexing process stopped")

        return {
            "message": "Indexing process stopped",
            "stopped_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.exception(f"Failed to stop indexing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop indexing. Please check logs for details.",
        )


@router.get("/index/thumbnails/validate")
async def validate_thumbnail_cache(
    sample_size: int = 100,
) -> dict[str, Any]:
    """
    Validate thumbnail cache integrity.

    Args:
        sample_size: Number of thumbnails to sample for validation

    Returns:
        Validation results with cache health metrics
    """
    try:
        from ..core.config import settings
        from ..workers.thumbnail_worker import ThumbnailCacheManager

        cache_manager = ThumbnailCacheManager(str(settings.THUMBNAIL_DIR))

        # Get cache statistics
        stats = await cache_manager.get_cache_statistics()

        # Validate sample
        validation = await cache_manager.validate_cache_integrity(sample_size)

        # Calculate health score
        total_checked = validation["total_checked"]
        if total_checked > 0:
            health_score = (validation["valid_files"] / total_checked) * 100
        else:
            health_score = 0.0

        return {
            "cache_statistics": stats,
            "validation": validation,
            "health": {
                "score": round(health_score, 2),
                "status": (
                    "healthy"
                    if health_score >= 95
                    else "degraded" if health_score >= 80 else "poor"
                ),
            },
            "recommendations": _get_cache_recommendations(validation, stats),
        }

    except Exception as e:
        logger.exception(f"Thumbnail cache validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache validation failed: {e!s}",
        )


def _get_cache_recommendations(
    validation: dict[str, Any], stats: dict[str, Any]
) -> list[str]:
    """Generate recommendations based on validation results."""
    recommendations = []

    if validation["invalid_files"] > 0:
        recommendations.append(
            f"Found {validation['invalid_files']} corrupted thumbnails. Consider regenerating thumbnails."
        )

    if stats.get("total_size_mb", 0) > 1000:
        recommendations.append(
            "Cache size exceeds 1GB. Consider cleanup of orphaned thumbnails."
        )

    total_checked = validation["total_checked"]
    if total_checked > 0:
        invalid_rate = (validation["invalid_files"] / total_checked) * 100
        if invalid_rate > 5:
            recommendations.append(
                f"High invalid file rate ({invalid_rate:.1f}%). Check for disk corruption or interrupted writes."
            )

    if not recommendations:
        recommendations.append("Thumbnail cache is healthy. No action needed.")

    return recommendations


@router.get("/index/diagnostics")
async def get_model_diagnostics() -> dict[str, Any]:
    """
    Get diagnostic information about ML models and dependencies.

    Returns:
        Model availability and status information
    """
    diagnostics = {"models": {}, "dependencies": {}, "errors": []}

    # Check CLIP model
    try:
        from ..workers.embedding_worker import OptimizedCLIPWorker

        clip_worker = OptimizedCLIPWorker()
        diagnostics["models"]["clip"] = {
            "available": True,
            "model_name": getattr(clip_worker, "model_name", "CLIP"),
            "status": "ready",
        }
    except Exception as e:
        diagnostics["models"]["clip"] = {
            "available": False,
            "error": str(e),
            "status": "failed",
        }
        diagnostics["errors"].append(f"CLIP model failed: {e}")

    # Check Face detection model
    try:
        from ..workers.face_worker import FaceDetectionWorker

        face_worker = FaceDetectionWorker()
        diagnostics["models"]["face_detection"] = {
            "available": face_worker.is_available(),
            "status": "ready" if face_worker.is_available() else "not_available",
        }
    except Exception as e:
        diagnostics["models"]["face_detection"] = {
            "available": False,
            "error": str(e),
            "status": "failed",
        }
        diagnostics["errors"].append(f"Face detection model failed: {e}")

    # Check EXIF extraction (no ML model required)
    try:
        from ..workers.exif_extractor import EXIFExtractionPipeline

        diagnostics["dependencies"]["exif"] = {"available": True, "status": "ready"}
    except Exception as e:
        diagnostics["dependencies"]["exif"] = {
            "available": False,
            "error": str(e),
            "status": "failed",
        }
        diagnostics["errors"].append(f"EXIF extraction failed: {e}")

    # Check thumbnail generation
    try:
        from ..workers.thumbnail_worker import SmartThumbnailGenerator

        diagnostics["dependencies"]["thumbnails"] = {
            "available": True,
            "status": "ready",
        }
    except Exception as e:
        diagnostics["dependencies"]["thumbnails"] = {
            "available": False,
            "error": str(e),
            "status": "failed",
        }

    # Overall status
    all_critical_available = (
        diagnostics["models"].get("clip", {}).get("available", False)
        and diagnostics["dependencies"].get("exif", {}).get("available", False)
        and diagnostics["dependencies"].get("thumbnails", {}).get("available", False)
    )

    diagnostics["overall_status"] = "healthy" if all_critical_available else "degraded"
    diagnostics["recommendation"] = (
        "All critical components are functional"
        if all_critical_available
        else "Some components are not available. Indexing will proceed with reduced functionality."
    )

    return diagnostics


@router.get("/index/stats")
async def get_indexing_statistics() -> dict[str, Any]:
    """
    Get indexing statistics.

    Returns:
        Comprehensive indexing statistics
    """
    try:
        db_manager = get_database_manager()

        # Get database statistics
        db_info = db_manager.get_database_info()

        # Get processing statistics
        # Get state snapshot once for consistency (avoid race conditions from multiple reads)
        state_snapshot = _state_manager.get_state_sync()

        return {
            "database": {
                "total_photos": db_info.get("table_counts", {}).get("photos", 0),
                "indexed_photos": _get_indexed_photo_count(db_manager),
                "photos_with_exif": db_info.get("table_counts", {}).get("exif", 0),
                "photos_with_embeddings": db_info.get("table_counts", {}).get(
                    "embeddings", 0
                ),
                "total_faces": db_info.get("table_counts", {}).get("faces", 0),
                "enrolled_people": db_info.get("table_counts", {}).get("people", 0),
                "thumbnails": db_info.get("table_counts", {}).get("thumbnails", 0),
            },
            "current_indexing": {
                "status": state_snapshot["status"],
                "progress": state_snapshot["progress"],
                "started_at": (
                    state_snapshot["started_at"].isoformat()
                    if state_snapshot["started_at"]
                    else None
                ),
                "errors_count": len(state_snapshot["errors"]),
            },
            "database_info": {
                "size_mb": db_info.get("database_size_mb", 0),
                "schema_version": db_info.get("settings", {}).get(
                    "schema_version", "unknown"
                ),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get indexing statistics: {e!s}",
        )


async def _monitor_indexing_task(task):
    """Monitor the indexing task and handle completion/cancellation."""
    try:
        await task
    except asyncio.CancelledError:
        await _state_manager.update_state({"status": "stopped", "task": None})
        logger.info("Indexing task was successfully cancelled")
    except Exception as e:
        await _state_manager.update_state({"status": "error", "task": None})
        await _state_manager.append_error(str(e))
        logger.exception(f"Indexing task failed: {e}")
    finally:
        # Clear task reference when done
        current_task = await _state_manager.get_value("task")
        if current_task == task:
            await _state_manager.set_value("task", None)


async def _setup_indexing_workers():
    """Setup and import all required workers."""
    from ..workers.crawler import FileCrawler
    from ..workers.embedding_worker import OptimizedCLIPWorker
    from ..workers.exif_extractor import EXIFExtractionPipeline
    from ..workers.face_worker import FaceDetectionWorker
    from ..workers.thumbnail_worker import SmartThumbnailGenerator

    return {
        "FileCrawler": FileCrawler,
        "OptimizedCLIPWorker": OptimizedCLIPWorker,
        "EXIFExtractionPipeline": EXIFExtractionPipeline,
        "FaceDetectionWorker": FaceDetectionWorker,
        "SmartThumbnailGenerator": SmartThumbnailGenerator,
    }


async def _check_cancellation():
    """Check if indexing has been cancelled and raise CancelledError if so."""
    status = await _state_manager.get_value("status")
    if status == "stopped":
        cancellation_msg = "Indexing was stopped by user request"
        raise asyncio.CancelledError(cancellation_msg)


async def _run_discovery_phase(workers, config, full_reindex):
    """Run file discovery phase."""
    from ..db.connection import get_database_manager

    await _state_manager.update_progress(current_phase="discovery")
    logger.info("Phase 1: File discovery")

    # Check for cancellation
    await _check_cancellation()

    crawler = workers["FileCrawler"]()
    for root_path in config.get("roots", []):
        crawler.add_root_path(root_path)

    await asyncio.sleep(0.5)  # Add small delay to show progress
    crawl_result = await crawler.crawl_all_paths(full_reindex)
    await _state_manager.update_progress(
        total_files=crawl_result.total_files, processed_files=0
    )

    if crawl_result.errors > 0:
        await _state_manager.extend_errors(crawl_result.error_details)

    # Save discovered photos to database
    db_manager = get_database_manager()
    inserted_count = 0

    # Process the crawled files
    for file_info in crawl_result.files:
        if file_info.get("status") in ["new", "modified"]:
            try:
                photo = file_info.get("photo")
                if photo:
                    # Insert or update photo in database
                    query = """
                        INSERT OR REPLACE INTO photos
                        (path, folder, filename, ext, size, created_ts, modified_ts, sha1, phash, indexed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                    """
                    params = (
                        photo.path,
                        photo.folder,
                        photo.filename,
                        photo.ext,
                        photo.size,
                        photo.created_ts,
                        photo.modified_ts,
                        photo.sha1 or "",
                        photo.phash or "",
                    )
                    db_manager.execute_update(query, params)
                    inserted_count += 1
            except Exception as e:
                logger.exception(f"Failed to insert photo {file_info.get('path')}: {e}")

    logger.info(f"Inserted/updated {inserted_count} photos in database")
    return crawl_result


async def _run_processing_phases(workers, config, photos_to_process):
    """Run all processing phases for photos."""
    total_photos = len(photos_to_process)
    await _state_manager.update_progress(total_files=total_photos)
    processed_count = 0

    # Phase 2: Metadata extraction
    await _state_manager.update_progress(current_phase="metadata")
    logger.info("Phase 2: EXIF metadata extraction")

    # Check for cancellation
    await _check_cancellation()

    try:
        exif_pipeline = workers["EXIFExtractionPipeline"]()
        await asyncio.sleep(0.5)  # Add small delay to show progress
        exif_results = await exif_pipeline.process_photos(photos_to_process)

        # Save EXIF data to database
        from ..db.connection import get_database_manager

        db_manager = get_database_manager()
        saved_exif_count = 0

        for result in exif_results:
            if result.get("extraction_successful") and result.get("exif_data"):
                try:
                    exif_data = result["exif_data"]
                    query = """
                        INSERT OR REPLACE INTO exif
                        (file_id, shot_dt, camera_make, camera_model, lens, iso,
                         aperture, shutter_speed, focal_length, gps_lat, gps_lon, orientation)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params = (
                        result["photo_id"],
                        exif_data.shot_dt if hasattr(exif_data, "shot_dt") else None,
                        (
                            exif_data.camera_make
                            if hasattr(exif_data, "camera_make")
                            else None
                        ),
                        (
                            exif_data.camera_model
                            if hasattr(exif_data, "camera_model")
                            else None
                        ),
                        exif_data.lens if hasattr(exif_data, "lens") else None,
                        exif_data.iso if hasattr(exif_data, "iso") else None,
                        exif_data.aperture if hasattr(exif_data, "aperture") else None,
                        (
                            exif_data.shutter_speed
                            if hasattr(exif_data, "shutter_speed")
                            else None
                        ),
                        (
                            exif_data.focal_length
                            if hasattr(exif_data, "focal_length")
                            else None
                        ),
                        exif_data.gps_lat if hasattr(exif_data, "gps_lat") else None,
                        exif_data.gps_lon if hasattr(exif_data, "gps_lon") else None,
                        (
                            exif_data.orientation
                            if hasattr(exif_data, "orientation")
                            else None
                        ),
                    )
                    db_manager.execute_update(query, params)
                    saved_exif_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to save EXIF for photo {result['photo_id']}: {e}"
                    )

        logger.info(
            f"Saved {saved_exif_count}/{len(exif_results)} EXIF records to database"
        )
    except Exception as e:
        logger.exception(f"EXIF extraction failed: {e}")
        await _state_manager.append_error(f"EXIF extraction failed: {e!s}")

    processed_count = int(total_photos * 0.3)  # 30% complete after metadata
    await _state_manager.update_progress(processed_files=processed_count)

    # In E2E mode, skip heavy ML phases to keep tests stable.
    if _is_e2e_test_mode():
        logger.info(
            "E2E_TEST enabled: skipping embeddings/thumbnails/faces phases for lightweight indexing"
        )
        await _state_manager.update_progress(
            current_phase="completed", processed_files=total_photos
        )
        return

    # Phase 3: Embedding generation (optional - skip if dependencies missing)
    await _state_manager.update_progress(current_phase="embeddings")
    logger.info("Phase 3: Embedding generation")

    # Check for cancellation
    await _check_cancellation()

    await asyncio.sleep(0.5)  # Add small delay to show progress
    try:
        embedding_worker = workers["OptimizedCLIPWorker"]()
        embeddings = await embedding_worker.generate_batch_optimized(photos_to_process)

        # Save embeddings to database
        import time

        from ..db.connection import get_database_manager

        db_manager = get_database_manager()
        saved_embedding_count = 0

        for embedding in embeddings:
            if embedding and hasattr(embedding, "file_id"):
                try:
                    query = """
                        INSERT OR REPLACE INTO embeddings
                        (file_id, clip_vector, embedding_model, processed_at)
                        VALUES (?, ?, ?, ?)
                    """
                    params = (
                        embedding.file_id,
                        (
                            embedding.clip_vector
                            if hasattr(embedding, "clip_vector")
                            else None
                        ),
                        (
                            embedding.embedding_model
                            if hasattr(embedding, "embedding_model")
                            else "CLIP"
                        ),
                        (
                            embedding.processed_at
                            if hasattr(embedding, "processed_at")
                            else time.time()
                        ),
                    )
                    db_manager.execute_update(query, params)
                    saved_embedding_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to save embedding for file_id {embedding.file_id}: {e}"
                    )

        logger.info(
            f"Saved {saved_embedding_count}/{len(embeddings)} embeddings to database"
        )
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
        await _state_manager.append_error(f"Embedding generation failed: {e!s}")
        logger.info("Continuing without embeddings")
    processed_count = int(total_photos * 0.5)  # 50% complete after embeddings
    await _state_manager.update_progress(processed_files=processed_count)

    # Phase 4: Thumbnail generation
    await _state_manager.update_progress(current_phase="thumbnails")
    logger.info("Phase 4: Thumbnail generation")

    # Check for cancellation
    await _check_cancellation()

    await asyncio.sleep(0.5)  # Add small delay to show progress
    thumbnail_generator = workers["SmartThumbnailGenerator"](
        cache_root=str(settings.THUMBNAILS_DIR)
    )
    thumbnails = await thumbnail_generator.generate_batch(photos_to_process)

    # Save thumbnails to database
    from ..db.connection import get_database_manager

    db_manager = get_database_manager()
    saved_count = 0
    for thumbnail in thumbnails:
        if thumbnail:
            try:
                query = """
                    INSERT OR REPLACE INTO thumbnails
                    (file_id, thumb_path, width, height, format, generated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                params = (
                    thumbnail.file_id,
                    thumbnail.thumb_path,
                    thumbnail.width,
                    thumbnail.height,
                    thumbnail.format,
                    thumbnail.generated_at,
                )
                db_manager.execute_update(query, params)
                saved_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to save thumbnail for file_id {thumbnail.file_id}: {e}"
                )

    logger.info(f"Saved {saved_count}/{len(thumbnails)} thumbnails to database")
    processed_count = int(total_photos * 0.75)  # 75% complete after thumbnails
    await _state_manager.update_progress(processed_files=processed_count)

    # Phase 5: Face detection (if enabled)
    if config.get("face_search_enabled", True):
        await _state_manager.update_progress(current_phase="faces")
        logger.info("Phase 5: Face detection")

        # Check for cancellation
        await _check_cancellation()

        try:
            face_worker = workers["FaceDetectionWorker"]()
            if face_worker.is_available():
                face_results = await face_worker.process_batch(photos_to_process)

                # Save face detection results to database
                from ..db.connection import get_database_manager

                db_manager = get_database_manager()
                saved_face_count = 0

                # face_results is a list of face lists, one per photo
                for i, face_list in enumerate(face_results):
                    if face_list:  # If this photo has faces
                        photo = photos_to_process[i]
                        logger.debug(
                            f"Saving {len(face_list)} faces for photo {photo.id} ({photo.filename})"
                        )

                        for face in face_list:
                            try:
                                # Use the Face object's to_db_params method to get database parameters
                                params = face.to_db_params()

                                query = """
                                    INSERT INTO faces
                                    (file_id, person_id, box_xyxy, face_vector, confidence, verified)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """
                                db_manager.execute_update(query, params)
                                saved_face_count += 1
                            except Exception as e:
                                logger.warning(
                                    f"Failed to save face for photo {photo.id} ({photo.filename}): {e}"
                                )

                logger.info(f"Saved {saved_face_count} face records to database")
            else:
                logger.warning("Face detection not available, skipping")
                await _state_manager.append_error("Face detection model not available")
        except Exception as e:
            logger.exception(f"Face detection failed: {e}")
            await _state_manager.append_error(f"Face detection failed: {e!s}")

    # Final update - 100% complete
    await _state_manager.update_progress(processed_files=total_photos)


async def _run_indexing_process(full_reindex: bool):
    """Run the complete indexing process."""
    try:
        logger.info(
            f"Starting indexing process in background task (full: {full_reindex})"
        )

        # Setup
        workers = await _setup_indexing_workers()
        db_manager = get_database_manager()
        config = _get_config_from_db(db_manager)

        if not config.get("roots", []):
            await _state_manager.append_error("No root paths configured")
            await _state_manager.set_value("status", "error")
            return

        # Validate root paths exist
        valid_roots = []
        for root_path in config.get("roots", []):
            if Path(root_path).exists():
                valid_roots.append(root_path)
            else:
                await _state_manager.append_error(
                    f"Root path does not exist: {root_path}"
                )

        if not valid_roots:
            # Complete immediately when no valid paths (for faster testing)
            await _state_manager.append_error(
                "No valid root paths found - indexing completed with no work"
            )
            await _state_manager.update_state(
                {
                    "status": "idle",
                    "last_completed_at": datetime.now(),
                }
            )
            await _state_manager.update_progress(
                current_phase="completed", processed_files=0
            )
            logger.info("Indexing completed with no valid root paths")
            return

        # Update config with valid roots only
        config["roots"] = valid_roots

        # Run phases
        await _run_discovery_phase(workers, config, full_reindex)
        photos_to_process = _get_photos_for_processing(db_manager, full_reindex)
        await _run_processing_phases(workers, config, photos_to_process)

        # Mark all processed photos as indexed
        if photos_to_process:
            photo_ids = [photo.id for photo in photos_to_process]
            indexed_time = datetime.now().isoformat()

            # Update indexed_at for all processed photos (batched for safety)
            batch_size = 500
            for i in range(0, len(photo_ids), batch_size):
                batch_ids = photo_ids[i : i + batch_size]
                placeholders = ",".join("?" * len(batch_ids))
                update_query = (
                    f"UPDATE photos SET indexed_at = ? WHERE id IN ({placeholders})"
                )
                db_manager.execute_update(update_query, (indexed_time, *batch_ids))
            logger.info(f"Marked {len(photo_ids)} photos as indexed")

        # Complete indexing
        await _state_manager.update_state(
            {
                "status": "idle",
                "last_completed_at": datetime.now(),
            }
        )
        await _state_manager.update_progress(
            current_phase="completed", processed_files=len(photos_to_process)
        )
        logger.info("Indexing process completed successfully")

    except asyncio.CancelledError:
        await _state_manager.set_value("status", "stopped")
        logger.info("Indexing process was cancelled")
    except Exception as e:
        await _state_manager.set_value("status", "error")
        await _state_manager.append_error(str(e))
        logger.exception(f"Indexing process failed: {e}")


def _get_config_from_db(db_manager) -> dict[str, Any]:
    """Get configuration from database."""
    try:
        settings_query = "SELECT key, value FROM settings"
        settings_rows = db_manager.execute_query(settings_query)

        config = {}
        for row in settings_rows:
            key, value = row[0], row[1]
            if key == "roots":
                import json

                try:
                    config[key] = json.loads(value)
                except:
                    config[key] = []
            elif key == "face_search_enabled":
                config[key] = value.lower() in ("true", "1", "yes")
            else:
                config[key] = value

        # Set defaults
        if "roots" not in config:
            config["roots"] = []
        if "face_search_enabled" not in config:
            config["face_search_enabled"] = True

        return config

    except Exception:
        return {"roots": [], "face_search_enabled": True}


def _get_photos_for_processing(db_manager, full_reindex: bool) -> list:
    """Get photos that need processing."""
    # This is a simplified implementation
    # In a real system, you'd return actual Photo objects

    if full_reindex:
        query = "SELECT * FROM photos"
    else:
        query = (
            "SELECT * FROM photos WHERE indexed_at IS NULL OR modified_ts > indexed_at"
        )

    rows = db_manager.execute_query(query)

    # Convert to Photo objects
    from ..models.photo import Photo

    photos = []
    for row in rows:
        photo = Photo.from_db_row(row)
        photos.append(photo)

    return photos


def _get_indexed_photo_count(db_manager) -> int:
    """Get count of indexed photos."""
    try:
        query = "SELECT COUNT(*) FROM photos WHERE indexed_at IS NOT NULL"
        result = db_manager.execute_query(query)
        return result[0][0] if result else 0
    except:
        return 0
