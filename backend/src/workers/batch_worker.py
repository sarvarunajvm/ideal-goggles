"""
Batch operation workers.

Handles background processing for batch export, delete, and tag operations.
"""

import shutil
from datetime import UTC, datetime
from pathlib import Path

import send2trash
from PIL import Image

from src.core.logging_config import get_logger
from src.db.connection import get_database_manager
from src.models.photo import Photo

logger = get_logger(__name__)


async def process_batch_export(
    job_id: str,
    photo_ids: list[str],
    destination: str,
    export_format: str = "original",
    max_dimension: int | None = None,
    job_store: dict | None = None,
):
    """
    Process batch photo export operation.

    Args:
        job_id: Unique job identifier
        photo_ids: List of photo IDs to export
        destination: Destination folder path
        format: Export format (original, jpg, png)
        max_dimension: Maximum dimension for resizing
        job_store: Shared job status dictionary
    """
    if job_store is None:
        logger.warning("No job store provided for batch export")
        return

    job = job_store.get(job_id)
    if not job:
        logger.error(f"Job {job_id} not found in store")
        return

    job["status"] = "processing"
    dest_path = Path(destination)

    try:
        # Ensure destination exists
        dest_path.mkdir(parents=True, exist_ok=True)

        db_manager = get_database_manager()
        processed = 0
        failed = 0

        for photo_id in photo_ids:
            try:
                # Get photo from database
                try:
                    pid = int(photo_id)
                except Exception:
                    logger.warning(f"Invalid photo id: {photo_id}")
                    failed += 1
                    job["failed_items"] = failed
                    continue

                rows = db_manager.execute_query(
                    "SELECT * FROM photos WHERE id = ?", (pid,)
                )
                if not rows:
                    logger.warning(f"Photo {photo_id} not found in database")
                    failed += 1
                    job["failed_items"] = failed
                    continue

                photo = Photo.from_db_row(rows[0])

                source_path = Path(photo.path)
                if not source_path.exists():
                    logger.warning(f"Source file not found: {source_path}")
                    failed += 1
                    job["failed_items"] = failed
                    continue

                # Determine output filename
                if export_format == "original":
                    output_path = dest_path / source_path.name
                    shutil.copy2(source_path, output_path)
                else:
                    # Convert/resize image
                    img = Image.open(source_path)

                    # Resize if max_dimension is specified
                    if max_dimension:
                        img.thumbnail(
                            (max_dimension, max_dimension), Image.Resampling.LANCZOS
                        )

                    # Save in requested format
                    output_name = source_path.stem + f".{export_format}"
                    output_path = dest_path / output_name
                    img.save(output_path, export_format.upper())

                processed += 1
                job["processed_items"] = processed

            except Exception as e:
                logger.exception(f"Failed to export photo {photo_id}: {e}")
                failed += 1
                job["failed_items"] = failed

        # Mark job as complete
        job["status"] = "completed"
        job["completed_at"] = datetime.now(UTC).isoformat()

        logger.info(f"Batch export completed: {processed} exported, {failed} failed")

    except Exception as e:
        logger.exception(f"Batch export job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.now(UTC).isoformat()


async def process_batch_delete(
    job_id: str,
    photo_ids: list[str],
    permanent: bool = False,
    job_store: dict | None = None,
):
    """
    Process batch photo deletion operation.

    Args:
        job_id: Unique job identifier
        photo_ids: List of photo IDs to delete
        permanent: If True, permanently delete. If False, move to trash.
        job_store: Shared job status dictionary
    """
    if job_store is None:
        logger.warning("No job store provided for batch delete")
        return

    job = job_store.get(job_id)
    if not job:
        logger.error(f"Job {job_id} not found in store")
        return

    job["status"] = "processing"

    try:
        db_manager = get_database_manager()
        processed = 0
        failed = 0

        for photo_id in photo_ids:
            try:
                # Get photo from database
                try:
                    pid = int(photo_id)
                except Exception:
                    logger.warning(f"Invalid photo id: {photo_id}")
                    failed += 1
                    job["failed_items"] = failed
                    continue

                rows = db_manager.execute_query(
                    "SELECT * FROM photos WHERE id = ?", (pid,)
                )
                if not rows:
                    logger.warning(f"Photo {photo_id} not found in database")
                    failed += 1
                    job["failed_items"] = failed
                    continue

                photo = Photo.from_db_row(rows[0])

                file_path = Path(photo.path)

                # Delete file
                if file_path.exists():
                    if permanent:
                        file_path.unlink()
                        logger.info(f"Permanently deleted: {file_path}")
                    else:
                        send2trash.send2trash(str(file_path))
                        logger.info(f"Moved to trash: {file_path}")

                # Remove from database
                db_manager.execute_update("DELETE FROM photos WHERE id = ?", (pid,))

                processed += 1
                job["processed_items"] = processed

            except Exception as e:
                logger.exception(f"Failed to delete photo {photo_id}: {e}")
                failed += 1
                job["failed_items"] = failed

        # Mark job as complete
        job["status"] = "completed"
        job["completed_at"] = datetime.now(UTC).isoformat()

        logger.info(f"Batch delete completed: {processed} deleted, {failed} failed")

    except Exception as e:
        logger.exception(f"Batch delete job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.now(UTC).isoformat()


async def process_batch_tag(
    job_id: str,
    photo_ids: list[str],
    tags: list[str],
    operation: str = "add",
    job_store: dict | None = None,
):
    """
    Process batch photo tagging operation.

    Args:
        job_id: Unique job identifier
        photo_ids: List of photo IDs to tag
        tags: Tags to add/remove/replace
        operation: Operation type (add, remove, replace)
        job_store: Shared job status dictionary
    """
    if job_store is None:
        logger.warning("No job store provided for batch tag")
        return

    job = job_store.get(job_id)
    if not job:
        logger.error(f"Job {job_id} not found in store")
        return

    job["status"] = "processing"

    try:
        db_manager = get_database_manager()
        processed = 0
        failed = 0

        # Determine if a 'tags' column exists on photos
        try:
            cols = db_manager.execute_query("PRAGMA table_info(photos)")

            # cols can be tuples (name at index 1) or dict-like with 'name'
            def _col_is_tags(col):
                try:
                    if isinstance(col, (tuple, list)):
                        return col[1] == "tags"
                    return col.get("name") == "tags"  # type: ignore[attr-defined]
                except Exception:
                    return False

            has_tags = any(_col_is_tags(c) for c in cols)
        except Exception:
            has_tags = False

        if not has_tags:
            logger.warning(
                "'tags' column not found on photos table; skipping batch tag operation"
            )
            job["status"] = "failed"
            job["error"] = "Tagging not supported: 'tags' column missing"
            job["completed_at"] = datetime.now(UTC).isoformat()
            return

        for photo_id in photo_ids:
            try:
                # Get current tags from database
                try:
                    pid = int(photo_id)
                except Exception:
                    logger.warning(f"Invalid photo id: {photo_id}")
                    failed += 1
                    job["failed_items"] = failed
                    continue

                rows = db_manager.execute_query(
                    "SELECT id, COALESCE(tags, '') as tags FROM photos WHERE id = ?",
                    (pid,),
                )
                if not rows:
                    logger.warning(f"Photo {photo_id} not found in database")
                    failed += 1
                    job["failed_items"] = failed
                    continue

                row = rows[0]
                current = row[1] if isinstance(row, (tuple, list)) else row["tags"]
                existing_tags = []
                if current:
                    existing_tags = [
                        t.strip() for t in str(current).split(",") if t.strip()
                    ]

                # Perform operation
                if operation == "add":
                    new_tags = list(set(existing_tags + tags))
                elif operation == "remove":
                    new_tags = [t for t in existing_tags if t not in tags]
                elif operation == "replace":
                    new_tags = tags
                else:
                    logger.warning(f"Invalid operation: {operation}")
                    failed += 1
                    job["failed_items"] = failed
                    continue

                # Update photo tags (store as comma-separated string)
                db_manager.execute_update(
                    "UPDATE photos SET tags = ? WHERE id = ?", (",".join(new_tags), pid)
                )

                processed += 1
                job["processed_items"] = processed

            except Exception as e:
                logger.exception(f"Failed to tag photo {photo_id}: {e}")
                failed += 1
                job["failed_items"] = failed

        # Mark job as complete
        job["status"] = "completed"
        job["completed_at"] = datetime.now(UTC).isoformat()

        logger.info(f"Batch tag completed: {processed} tagged, {failed} failed")

    except Exception as e:
        logger.exception(f"Batch tag job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.now(UTC).isoformat()
