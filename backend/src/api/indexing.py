"""Indexing control endpoints for photo search API."""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging

from ..db.connection import get_database_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class IndexStatus(BaseModel):
    """Index status model."""
    status: str = Field(description="Current indexing status")
    progress: Dict[str, Any] = Field(description="Progress information")
    errors: List[str] = Field(description="List of errors encountered")
    started_at: Optional[datetime] = Field(description="Indexing start time")
    estimated_completion: Optional[datetime] = Field(description="Estimated completion time")


class StartIndexRequest(BaseModel):
    """Request model for starting indexing."""
    full: bool = Field(default=False, description="Whether to perform full re-index")


# Global indexing state
_indexing_state = {
    "status": "idle",
    "progress": {
        "total_files": 0,
        "processed_files": 0,
        "current_phase": "discovery"
    },
    "errors": [],
    "started_at": None,
    "estimated_completion": None,
    "task": None
}


@router.post("/index/start")
async def start_indexing(
    request: StartIndexRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Start indexing process.

    Args:
        request: Indexing configuration
        background_tasks: FastAPI background tasks

    Returns:
        Indexing start confirmation
    """
    global _indexing_state

    # Check if indexing is already running
    if _indexing_state["status"] == "indexing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Indexing already in progress"
        )

    try:
        # Reset indexing state
        _indexing_state = {
            "status": "indexing",
            "progress": {
                "total_files": 0,
                "processed_files": 0,
                "current_phase": "discovery"
            },
            "errors": [],
            "started_at": datetime.now(),
            "estimated_completion": None,
            "task": None
        }

        # Start indexing in background
        background_tasks.add_task(_run_indexing_process, request.full)

        logger.info(f"Indexing started (full: {request.full})")

        return {
            "message": "Indexing started successfully",
            "full_reindex": request.full,
            "started_at": _indexing_state["started_at"].isoformat()
        }

    except Exception as e:
        _indexing_state["status"] = "error"
        _indexing_state["errors"].append(str(e))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start indexing: {str(e)}"
        )


@router.get("/index/status", response_model=IndexStatus)
async def get_indexing_status() -> IndexStatus:
    """
    Get current indexing status.

    Returns:
        Current indexing status and progress
    """
    return IndexStatus(
        status=_indexing_state["status"],
        progress=_indexing_state["progress"],
        errors=_indexing_state["errors"],
        started_at=_indexing_state["started_at"],
        estimated_completion=_indexing_state["estimated_completion"]
    )


@router.post("/index/stop")
async def stop_indexing() -> Dict[str, Any]:
    """
    Stop current indexing process.

    Returns:
        Stop confirmation
    """
    global _indexing_state

    if _indexing_state["status"] != "indexing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No indexing process is currently running"
        )

    try:
        # Cancel the indexing task if it exists
        if _indexing_state["task"]:
            _indexing_state["task"].cancel()

        _indexing_state["status"] = "stopped"

        logger.info("Indexing process stopped")

        return {
            "message": "Indexing process stopped",
            "stopped_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop indexing: {str(e)}"
        )


@router.get("/index/stats")
async def get_indexing_statistics() -> Dict[str, Any]:
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
        stats = {
            "database": {
                "total_photos": db_info.get("table_counts", {}).get("photos", 0),
                "indexed_photos": _get_indexed_photo_count(db_manager),
                "photos_with_exif": db_info.get("table_counts", {}).get("exif", 0),
                "photos_with_ocr": _get_ocr_photo_count(db_manager),
                "photos_with_embeddings": db_info.get("table_counts", {}).get("embeddings", 0),
                "total_faces": db_info.get("table_counts", {}).get("faces", 0),
                "enrolled_people": db_info.get("table_counts", {}).get("people", 0),
                "thumbnails": db_info.get("table_counts", {}).get("thumbnails", 0)
            },
            "current_indexing": {
                "status": _indexing_state["status"],
                "progress": _indexing_state["progress"],
                "started_at": _indexing_state["started_at"].isoformat() if _indexing_state["started_at"] else None,
                "errors_count": len(_indexing_state["errors"])
            },
            "database_info": {
                "size_mb": db_info.get("database_size_mb", 0),
                "schema_version": db_info.get("settings", {}).get("schema_version", "unknown")
            }
        }

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get indexing statistics: {str(e)}"
        )


async def _run_indexing_process(full_reindex: bool):
    """Run the complete indexing process."""
    global _indexing_state

    try:
        logger.info("Starting indexing process")

        # Import workers
        from ..workers.crawler import FileCrawler
        from ..workers.exif_extractor import EXIFExtractionPipeline
        from ..workers.ocr_worker import SmartOCRWorker
        from ..workers.embedding_worker import OptimizedCLIPWorker
        from ..workers.thumbnail_worker import SmartThumbnailGenerator
        from ..workers.face_worker import FaceDetectionWorker

        # Get configuration
        db_manager = get_database_manager()
        config = _get_config_from_db(db_manager)
        root_paths = config.get("roots", [])

        if not root_paths:
            _indexing_state["errors"].append("No root paths configured")
            _indexing_state["status"] = "error"
            return

        # Phase 1: Discovery
        _indexing_state["progress"]["current_phase"] = "discovery"
        logger.info("Phase 1: File discovery")

        crawler = FileCrawler()
        for root_path in root_paths:
            crawler.add_root_path(root_path)

        crawl_result = await crawler.crawl_all_paths(full_reindex)
        _indexing_state["progress"]["total_files"] = crawl_result.total_files

        if crawl_result.errors > 0:
            _indexing_state["errors"].extend(crawl_result.error_details)

        # Get photos that need processing
        photos_to_process = _get_photos_for_processing(db_manager, full_reindex)

        # Phase 2: Metadata extraction
        _indexing_state["progress"]["current_phase"] = "metadata"
        logger.info("Phase 2: EXIF metadata extraction")

        exif_pipeline = EXIFExtractionPipeline()
        await exif_pipeline.process_photos(photos_to_process)

        # Phase 3: OCR processing
        _indexing_state["progress"]["current_phase"] = "ocr"
        logger.info("Phase 3: OCR text extraction")

        ocr_worker = SmartOCRWorker(languages=config.get("ocr_languages", ["eng"]))
        await ocr_worker.extract_batch(photos_to_process)

        # Phase 4: Embedding generation
        _indexing_state["progress"]["current_phase"] = "embeddings"
        logger.info("Phase 4: Embedding generation")

        embedding_worker = OptimizedCLIPWorker()
        await embedding_worker.generate_batch_optimized(photos_to_process)

        # Phase 5: Thumbnail generation
        _indexing_state["progress"]["current_phase"] = "thumbnails"
        logger.info("Phase 5: Thumbnail generation")

        thumbnail_generator = SmartThumbnailGenerator(
            cache_root=str(Path.home() / '.photo-search' / 'thumbnails')
        )
        await thumbnail_generator.generate_batch(photos_to_process)

        # Phase 6: Face detection (if enabled)
        if config.get("face_search_enabled", False):
            _indexing_state["progress"]["current_phase"] = "faces"
            logger.info("Phase 6: Face detection")

            face_worker = FaceDetectionWorker()
            if face_worker.is_available():
                await face_worker.process_batch(photos_to_process)
            else:
                logger.warning("Face detection not available, skipping")

        # Complete indexing
        _indexing_state["status"] = "idle"
        _indexing_state["progress"]["current_phase"] = "completed"
        _indexing_state["progress"]["processed_files"] = len(photos_to_process)

        logger.info("Indexing process completed successfully")

    except asyncio.CancelledError:
        _indexing_state["status"] = "stopped"
        logger.info("Indexing process was cancelled")
    except Exception as e:
        _indexing_state["status"] = "error"
        _indexing_state["errors"].append(str(e))
        logger.error(f"Indexing process failed: {e}")


def _get_config_from_db(db_manager) -> Dict[str, Any]:
    """Get configuration from database."""
    try:
        settings_query = "SELECT key, value FROM settings"
        settings_rows = db_manager.execute_query(settings_query)

        config = {}
        for row in settings_rows:
            key, value = row[0], row[1]
            if key in ["roots", "ocr_languages"]:
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
        if "ocr_languages" not in config:
            config["ocr_languages"] = ["eng"]
        if "face_search_enabled" not in config:
            config["face_search_enabled"] = False

        return config

    except Exception:
        return {
            "roots": [],
            "ocr_languages": ["eng"],
            "face_search_enabled": False
        }


def _get_photos_for_processing(db_manager, full_reindex: bool) -> List:
    """Get photos that need processing."""
    # This is a simplified implementation
    # In a real system, you'd return actual Photo objects

    if full_reindex:
        query = "SELECT * FROM photos"
    else:
        query = "SELECT * FROM photos WHERE indexed_at IS NULL OR modified_ts > indexed_at"

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


def _get_ocr_photo_count(db_manager) -> int:
    """Get count of photos with OCR data."""
    try:
        query = "SELECT COUNT(DISTINCT file_id) FROM ocr"
        result = db_manager.execute_query(query)
        return result[0][0] if result else 0
    except:
        return 0