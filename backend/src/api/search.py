"""Search endpoints for photo search API."""

import contextlib
import os
import tempfile
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from ..db.connection import get_database_manager

router = APIRouter()


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
    top_k: int = Field(default=50, ge=1, le=200, description="Maximum number of results")


class FaceSearchRequest(BaseModel):
    """Face search request model."""
    person_id: int = Field(description="ID of enrolled person")
    top_k: int = Field(default=50, ge=1, le=200, description="Maximum number of results")


@router.get("/search", response_model=SearchResults)
async def search_photos(
    q: str | None = Query(None, description="Search query text"),
    from_date: date | None = Query(None, alias="from", description="Start date filter (YYYY-MM-DD)"),
    to_date: date | None = Query(None, alias="to", description="End date filter (YYYY-MM-DD)"),
    folder: str | None = Query(None, description="Folder path filter"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Results offset for pagination")
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
    start_time = datetime.now()

    try:
        db_manager = get_database_manager()

        # Build search query
        search_results = await _execute_text_search(
            db_manager, q, from_date, to_date, folder, limit, offset
        )

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return SearchResults(
            query=q or "",
            total_matches=len(search_results),
            items=search_results,
            took_ms=int(execution_time)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e!s}"
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

    try:
        # Import embedding worker here to avoid circular imports
        from ..workers.embedding_worker import CLIPEmbeddingWorker

        db_manager = get_database_manager()

        # Generate text embedding
        embedding_worker = CLIPEmbeddingWorker()
        query_embedding = await embedding_worker.generate_text_embedding(request.text)

        if query_embedding is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate text embedding"
            )

        # Search for similar images
        search_results = await _execute_semantic_search(
            db_manager, query_embedding, request.top_k
        )

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return SearchResults(
            query=request.text,
            total_matches=len(search_results),
            items=search_results,
            took_ms=int(execution_time)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {e!s}"
        )


@router.post("/search/image", response_model=SearchResults)
async def image_search(
    file: UploadFile = File(..., description="Uploaded image file"),
    top_k: int = Form(50, ge=1, le=200, description="Maximum number of results")
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
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
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
            embedding_worker = CLIPEmbeddingWorker()
            query_embedding_obj = await embedding_worker.generate_embedding(temp_photo)

            if query_embedding_obj is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to process uploaded image"
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
                took_ms=int(execution_time)
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
            detail=f"Image search failed: {e!s}"
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

        # Check if person exists
        person_query = "SELECT id, name, face_vector, active FROM people WHERE id = ? AND active = 1"
        person_rows = db_manager.execute_query(person_query, (request.person_id,))

        if not person_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found or inactive"
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
            took_ms=int(execution_time)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face search failed: {e!s}"
        )


async def _execute_text_search(
    db_manager, query: str | None, from_date: date | None, to_date: date | None,
    folder: str | None, limit: int, offset: int
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
            "e.camera_model LIKE ?"
        ]

        # Add OCR search if available
        ocr_condition = """
            p.id IN (
                SELECT file_id FROM ocr WHERE ocr MATCH ?
            )
        """
        text_conditions.append(ocr_condition)

        # Combine text conditions with OR
        where_conditions.append(f"({' OR '.join(text_conditions)})")

        # Add parameters for each condition
        search_pattern = f"%{query}%"
        params.extend([search_pattern] * 4)  # For LIKE conditions
        params.append(query)  # For FTS match

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
            snippet=row[7] if row[7] else None
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

    rows = db_manager.execute_query(embeddings_query)

    # Calculate similarities
    similarities = []
    import numpy as np

    from ..models.embedding import Embedding

    for row in rows:
        try:
            # Decode embedding from blob
            stored_embedding = Embedding._blob_to_numpy(row[1])

            # Calculate cosine similarity
            similarity = float(np.dot(query_embedding, stored_embedding))

            similarities.append((similarity, row))

        except Exception:
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
            snippet=None
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
            snippet=None
        )
        results.append(item)

    return results
