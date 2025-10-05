"""Search endpoints for Ideal Goggles API."""

import contextlib
import os
import tempfile
import time
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..core.logging_config import get_logger, log_error_with_context, log_slow_operation
from ..core.middleware import get_request_id
from ..core.utils import (
    DependencyChecker,
    calculate_execution_time,
    handle_internal_error,
    handle_service_unavailable,
)
from ..db.connection import get_database_manager
from ..db.utils import DatabaseHelper

router = APIRouter()
logger = get_logger(__name__)


class SearchResultItem(BaseModel):
    """Search result item model."""

    file_id: int
    path: str = Field(description="Absolute path to photo file")
    folder: str = Field(description="Parent folder path")
    filename: str = Field(description="File name with extension")
    thumb_path: str | None = Field(description="Relative path to thumbnail")
    shot_dt: datetime | None = Field(description="Photo capture timestamp")
    score: float = Field(description="Relevance score (0.0-1.0)")
    badges: list[str] = Field(description="Types of matches found")
    snippet: str | None = Field(description="Relevant text excerpt for text matches")


class SearchResults(BaseModel):
    """Search results model."""

    query: str = Field(description="Original search query")
    total_matches: int = Field(description="Total number of matching photos")
    items: list[SearchResultItem] = Field(description="Search result items")
    took_ms: int = Field(description="Search execution time in milliseconds")


class SemanticSearchRequest(BaseModel):
    """Semantic search request model."""

    text: str = Field(description="Natural language description")
    top_k: int = Field(
        default=50, ge=1, le=200, description="Maximum number of results"
    )


class FaceSearchRequest(BaseModel):
    """Face search request model."""

    person_id: int = Field(description="ID of enrolled person")
    top_k: int = Field(
        default=50, ge=1, le=200, description="Maximum number of results"
    )


@router.get("/search", response_model=SearchResults)
async def search_photos(
    q: str | None = Query(None, description="Search query text"),
    from_date: date | None = Query(
        None, alias="from", description="Start date filter (YYYY-MM-DD)"
    ),
    to_date: date | None = Query(
        None, alias="to", description="End date filter (YYYY-MM-DD)"
    ),
    folder: str | None = Query(None, description="Folder path filter"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Results offset for pagination"),
) -> SearchResults:
    """
    Search photos by text and filters.

    Args:
        q: Search query text
        from_date: Start date filter
        to_date: End date filter
        folder: Folder path filter
        limit: Maximum number of results
        offset: Results offset for pagination

    Returns:
        Search results matching the query and filters
    """
    start_time = time.time()
    request_id = get_request_id()

    logger.info(
        "Text search request received",
        extra={
            "request_id": request_id,
            "query": q,
            "from_date": str(from_date) if from_date else None,
            "to_date": str(to_date) if to_date else None,
            "folder": folder,
            "limit": limit,
            "offset": offset,
        },
    )

    try:
        db_manager = get_database_manager()

        # Build search query
        search_results = await _execute_text_search(
            db_manager, q, from_date, to_date, folder, limit, offset
        )

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "Text search completed successfully",
            extra={
                "request_id": request_id,
                "query": q,
                "results_count": len(search_results),
                "duration_ms": execution_time_ms,
            },
        )

        # Log slow search operations
        log_slow_operation(logger, "text_search", execution_time_ms, threshold_ms=2000)

        return SearchResults(
            query=q or "",
            total_matches=len(search_results),
            items=search_results,
            took_ms=int(execution_time_ms),
        )

    except Exception as e:
        log_error_with_context(
            logger,
            e,
            "text_search",
            request_id=request_id,
            query=q,
            from_date=str(from_date) if from_date else None,
            to_date=str(to_date) if to_date else None,
            folder=folder,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e!s}",
        )


@router.post("/search/semantic", response_model=SearchResults)
async def semantic_search(request: SemanticSearchRequest) -> SearchResults:
    """
    Semantic search using text description.

    Args:
        request: Semantic search request

    Returns:
        Search results based on semantic similarity
    """
    start_time = datetime.now()
    logger.info(f"Semantic search started for query: '{request.text}' with top_k: {request.top_k}")

    try:
        # Check if CLIP dependencies are available
        clip_available, error_msg = DependencyChecker.check_clip()
        if not clip_available:
            handle_service_unavailable("Semantic search", error_msg)

        # Import embedding worker here to avoid circular imports
        from ..workers.embedding_worker import CLIPEmbeddingWorker

        db_manager = get_database_manager()

        # Generate text embedding
        try:
            embedding_worker = CLIPEmbeddingWorker()
            query_embedding = await embedding_worker.generate_text_embedding(
                request.text
            )
        except RuntimeError as e:
            if "CLIP dependencies not installed" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Semantic search unavailable: CLIP dependencies not properly configured",
                )
            raise

        if query_embedding is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate text embedding",
            )

        # Search for similar images
        logger.info(f"Calling _execute_semantic_search with embedding shape: {query_embedding.shape if hasattr(query_embedding, 'shape') else 'unknown'}")
        search_results = await _execute_semantic_search(
            db_manager, query_embedding, request.top_k
        )
        logger.info(f"Semantic search returned {len(search_results)} results")

        # Calculate execution time
        execution_time = calculate_execution_time(start_time)

        return SearchResults(
            query=request.text,
            total_matches=len(search_results),
            items=search_results,
            took_ms=execution_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {e!s}",
        )


@router.post("/search/image", response_model=SearchResults)
async def image_search(
    file: UploadFile = File(..., description="Uploaded image file"),
    top_k: int = Form(50, ge=1, le=200, description="Maximum number of results"),
) -> SearchResults:
    """
    Reverse image search using uploaded photo.

    Args:
        file: Uploaded image file
        top_k: Maximum number of results

    Returns:
        Search results based on visual similarity
    """
    start_time = datetime.now()

    try:
        # Check if CLIP dependencies are available
        try:
            import clip
            import torch
        except ImportError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Image search unavailable: CLIP dependencies not installed ({e})",
            )

        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file"
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as temp_file:
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)

        try:
            # Import embedding worker
            from ..models.photo import Photo
            from ..workers.embedding_worker import CLIPEmbeddingWorker

            # Create temporary photo object for embedding generation
            temp_photo = Photo(path=temp_path)

            # Generate embedding for uploaded image
            try:
                embedding_worker = CLIPEmbeddingWorker()
                query_embedding_obj = await embedding_worker.generate_embedding(
                    temp_photo
                )
            except RuntimeError as e:
                if "CLIP dependencies not installed" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Image search unavailable: CLIP dependencies not properly configured",
                    )
                raise

            if query_embedding_obj is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to process uploaded image",
                )

            db_manager = get_database_manager()

            # Search for similar images
            search_results = await _execute_image_search(
                db_manager, query_embedding_obj.clip_vector, top_k
            )

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return SearchResults(
                query=f"Image: {file.filename}",
                total_matches=len(search_results),
                items=search_results,
                took_ms=int(execution_time),
            )

        finally:
            # Clean up temporary file
            with contextlib.suppress(OSError):
                os.unlink(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image search failed: {e!s}",
        )


@router.post("/search/faces", response_model=SearchResults)
async def face_search(request: FaceSearchRequest) -> SearchResults:
    """
    Search photos by enrolled person.

    Args:
        request: Face search request

    Returns:
        Search results containing the specified person
    """
    start_time = datetime.now()

    try:
        db_manager = get_database_manager()

        # Check if face search is enabled
        from .config import _get_config_from_db

        config = _get_config_from_db(db_manager)
        if not config.get("face_search_enabled", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Face search is disabled. Enable face search in configuration.",
            )

        # Check if person exists
        person_query = "SELECT id, name, face_vector, active FROM people WHERE id = ? AND active = 1"
        person_rows = db_manager.execute_query(person_query, (request.person_id,))

        if not person_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found or inactive",
            )

        # Execute face search
        search_results = await _execute_face_search(
            db_manager, request.person_id, request.top_k
        )

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        person_name = person_rows[0][1]

        return SearchResults(
            query=f"Person: {person_name}",
            total_matches=len(search_results),
            items=search_results,
            took_ms=int(execution_time),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face search failed: {e!s}",
        )


async def _execute_text_search(
    db_manager,
    query: str | None,
    from_date: date | None,
    to_date: date | None,
    folder: str | None,
    limit: int,
    offset: int,
) -> list[SearchResultItem]:
    """Execute text-based search with filters."""
    # Build WHERE clause
    where_conditions = []
    params = []

    # Add text search conditions
    if query:
        # Search in multiple fields
        text_conditions = [
            "p.filename LIKE ?",
            "p.folder LIKE ?",
            "e.camera_make LIKE ?",
            "e.camera_model LIKE ?",
        ]

        # Combine text conditions with OR
        where_conditions.append(f"({' OR '.join(text_conditions)})")

        # Add parameters for each condition
        search_pattern = f"%{query}%"
        params.extend([search_pattern] * 4)  # For LIKE conditions

    # Add date filter
    if from_date or to_date:
        if from_date and to_date:
            where_conditions.append("e.shot_dt BETWEEN ? AND ?")
            params.extend([from_date.isoformat(), to_date.isoformat()])
        elif from_date:
            where_conditions.append("e.shot_dt >= ?")
            params.append(from_date.isoformat())
        elif to_date:
            where_conditions.append("e.shot_dt <= ?")
            params.append(to_date.isoformat())

    # Add folder filter
    if folder:
        where_conditions.append("p.folder LIKE ?")
        params.append(f"{folder}%")

    # Build complete query
    base_query = """
        SELECT DISTINCT
            p.id,
            p.path,
            p.folder,
            p.filename,
            t.thumb_path,
            e.shot_dt,
            1.0 as score,
            '' as snippet
        FROM photos p
        LEFT JOIN exif e ON p.id = e.file_id
        LEFT JOIN thumbnails t ON p.id = t.file_id
    """

    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    order_clause = "ORDER BY p.modified_ts DESC"
    limit_clause = f"LIMIT {limit} OFFSET {offset}"

    full_query = f"{base_query} {where_clause} {order_clause} {limit_clause}"

    # Execute search
    rows = db_manager.execute_query(full_query, params)

    # Convert to SearchResultItem objects
    results = []
    for row in rows:
        badges = []
        if query:
            # Determine match types based on where the query was found
            if query.lower() in row[3].lower():  # filename
                badges.append("filename")
            if query.lower() in row[2].lower():  # folder
                badges.append("folder")
            # Would need additional logic to check EXIF and OCR matches

        item = SearchResultItem(
            file_id=row[0],
            path=row[1],
            folder=row[2],
            filename=row[3],
            thumb_path=row[4],
            shot_dt=datetime.fromisoformat(row[5]) if row[5] else None,
            score=row[6],
            badges=badges,
            snippet=row[7] if row[7] else None,
        )
        results.append(item)

    return results


async def _execute_semantic_search(
    db_manager, query_embedding, top_k: int
) -> list[SearchResultItem]:
    """Execute semantic search using CLIP embeddings."""
    # This is a simplified implementation
    # In a real system, you'd use FAISS for efficient vector search

    # Get all embeddings from database
    embeddings_query = """
        SELECT e.file_id, e.clip_vector, p.path, p.folder, p.filename,
               t.thumb_path, ex.shot_dt
        FROM embeddings e
        JOIN photos p ON e.file_id = p.id
        LEFT JOIN thumbnails t ON p.id = t.file_id
        LEFT JOIN exif ex ON p.id = ex.file_id
        WHERE p.indexed_at IS NOT NULL
    """

    logger.info(f"Executing embeddings query for semantic search")
    rows = db_manager.execute_query(embeddings_query)
    logger.info(f"Query returned {len(rows)} rows")

    # Calculate similarities
    similarities = []
    import numpy as np

    from ..models.embedding import Embedding

    logger.info(f"Processing {len(rows)} embeddings for semantic search")

    for i, row in enumerate(rows):
        try:
            # Decode embedding from blob
            stored_embedding = Embedding._blob_to_numpy(row[1])

            # Ensure both embeddings are numpy arrays and have compatible shapes
            if not isinstance(query_embedding, np.ndarray):
                query_embedding = np.array(query_embedding, dtype=np.float32)
            if not isinstance(stored_embedding, np.ndarray):
                stored_embedding = np.array(stored_embedding, dtype=np.float32)

            # Flatten both embeddings to ensure 1D arrays
            query_flat = query_embedding.flatten()
            stored_flat = stored_embedding.flatten()

            # Check dimensions match
            if len(query_flat) != len(stored_flat):
                logger.warning(f"Embedding dimension mismatch: query={len(query_flat)}, stored={len(stored_flat)} for file_id {row[0]}")
                continue

            # Normalize both vectors (important for cosine similarity)
            query_norm = query_flat / (np.linalg.norm(query_flat) + 1e-8)
            stored_norm = stored_flat / (np.linalg.norm(stored_flat) + 1e-8)

            # Calculate cosine similarity
            similarity = float(np.dot(query_norm, stored_norm))

            # Ensure similarity is in valid range [-1, 1]
            similarity = max(-1.0, min(1.0, similarity))

            similarities.append((similarity, row))

            # Log first few similarities for debugging
            if i < 5:
                logger.info(f"Similarity {i}: {similarity:.4f} for file_id {row[0]} (query_dim: {len(query_flat)}, stored_dim: {len(stored_flat)})")

        except Exception as e:
            logger.error(f"Failed to process embedding for file_id {row[0]}: {e}")
            continue

    # Sort by similarity and take top results
    similarities.sort(key=lambda x: x[0], reverse=True)
    top_results = similarities[:top_k]

    # Convert to SearchResultItem objects
    results = []
    for similarity, row in top_results:
        item = SearchResultItem(
            file_id=row[0],
            path=row[2],
            folder=row[3],
            filename=row[4],
            thumb_path=row[5],
            shot_dt=datetime.fromisoformat(row[6]) if row[6] else None,
            score=similarity,
            badges=["image"],
            snippet=None,
        )
        results.append(item)

    return results


async def _execute_image_search(
    db_manager, query_embedding, top_k: int
) -> list[SearchResultItem]:
    """Execute image search using visual similarity."""
    # Reuse semantic search logic since both use CLIP embeddings
    return await _execute_semantic_search(db_manager, query_embedding, top_k)


async def _execute_face_search(
    db_manager, person_id: int, top_k: int
) -> list[SearchResultItem]:
    """Execute face-based search."""
    # Get faces associated with the person
    faces_query = """
        SELECT DISTINCT f.file_id, f.confidence, p.path, p.folder, p.filename,
               t.thumb_path, e.shot_dt
        FROM faces f
        JOIN photos p ON f.file_id = p.id
        LEFT JOIN thumbnails t ON p.id = t.file_id
        LEFT JOIN exif e ON p.id = e.file_id
        WHERE f.person_id = ? AND f.confidence >= 0.5
        ORDER BY f.confidence DESC
        LIMIT ?
    """

    rows = db_manager.execute_query(faces_query, (person_id, top_k))

    # Convert to SearchResultItem objects
    results = []
    for row in rows:
        item = SearchResultItem(
            file_id=row[0],
            path=row[2],
            folder=row[3],
            filename=row[4],
            thumb_path=row[5],
            shot_dt=datetime.fromisoformat(row[6]) if row[6] else None,
            score=row[1],  # Use face confidence as score
            badges=["face"],
            snippet=None,
        )
        results.append(item)

    return results


@router.get("/photos/{photo_id}/original")
async def get_original_photo(photo_id: int):
    """
    Serve the original photo file.

    Args:
        photo_id: The database ID of the photo

    Returns:
        The original photo file
    """
    db_manager = get_database_manager()

    # Get photo path from database
    query = "SELECT path FROM photos WHERE id = ?"
    rows = db_manager.execute_query(query, (photo_id,))

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with ID {photo_id} not found",
        )

    photo_path = rows[0][0]

    # Check if file exists
    if not os.path.exists(photo_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo file not found at path: {photo_path}",
        )

    # Detect media type based on file extension
    file_ext = Path(photo_path).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
    }
    media_type = media_types.get(file_ext, "application/octet-stream")

    # Return the file
    return FileResponse(
        path=photo_path, media_type=media_type, filename=Path(photo_path).name
    )
