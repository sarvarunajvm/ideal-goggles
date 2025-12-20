"""People management endpoints for Ideal Goggles API."""

import hashlib
import os
from datetime import datetime
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from ..db.connection import get_database_manager
from ..models.person import Person

router = APIRouter()


def _parse_datetime(value: Any) -> datetime:
    """Parse datetime from database value.

    Handles both Unix timestamps (float) and ISO format strings.
    """
    if value is None:
        return datetime.now()

    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        # Unix timestamp
        return datetime.fromtimestamp(value)

    if isinstance(value, str):
        # Try ISO format first (handles both with and without Z suffix)
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass

        # Try common SQLite datetime format
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        # Try date only format
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            pass

    # Fallback to current time if parsing fails
    return datetime.now()


class PersonResponse(BaseModel):
    """Person response model."""

    id: int
    name: str
    sample_count: int = Field(description="Number of sample photos used")
    created_at: datetime
    active: bool = Field(description="Whether person search is enabled")


class CreatePersonRequest(BaseModel):
    """Request model for creating a person."""

    name: str = Field(description="Person's display name")
    sample_file_ids: list[int] = Field(
        description="Array of photo IDs containing this person"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate person name."""
        if not v or not v.strip():
            msg = "Person name cannot be empty"
            raise ValueError(msg)
        if len(v.strip()) > 255:
            msg = "Person name too long (max 255 characters)"
            raise ValueError(msg)
        return v.strip()

    @field_validator("sample_file_ids")
    @classmethod
    def validate_sample_file_ids(cls, v):
        """Validate sample file IDs."""
        if not v or len(v) < 1:
            msg = "At least one sample photo is required"
            raise ValueError(msg)
        if len(v) > 10:
            msg = "Too many sample photos (max 10)"
            raise ValueError(msg)
        return v


class UpdatePersonRequest(BaseModel):
    """Request model for updating a person."""

    name: str | None = Field(None, description="Person's display name")
    active: bool | None = Field(None, description="Whether person search is enabled")
    additional_sample_file_ids: list[int] | None = Field(
        None, description="Additional sample photos"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate person name."""
        if v is not None:
            if not v or not v.strip():
                msg = "Person name cannot be empty"
                raise ValueError(msg)
            if len(v.strip()) > 255:
                msg = "Person name too long (max 255 characters)"
                raise ValueError(msg)
            return v.strip()
        return v


def _is_e2e_test_mode() -> bool:
    """Return True when running in E2E test mode (used to avoid heavy ML requirements)."""
    return os.getenv("E2E_TEST", "").strip().lower() in {"1", "true", "yes", "on"}


def _dummy_face_vector(seed_text: str, dim: int = 512) -> np.ndarray:
    """
    Deterministically generate a normalized face embedding vector for tests.

    This is only used when E2E_TEST mode is enabled to allow People flows without real faces.
    """
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "little", signed=False)
    rng = np.random.default_rng(seed)
    vec = rng.normal(size=dim).astype(np.float32)
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
    return vec


@router.get("/people", response_model=list[PersonResponse])
async def list_people() -> list[PersonResponse]:
    """
    List all enrolled people.

    Returns:
        List of enrolled people
    """
    try:
        db_manager = get_database_manager()

        # Get all people from database
        query = """
            SELECT id, name, sample_count, created_at, updated_at, active
            FROM people
            ORDER BY name
        """

        rows = db_manager.execute_query(query)

        people = []
        for row in rows:
            person = PersonResponse(
                id=row[0],
                name=row[1],
                sample_count=row[2],
                created_at=_parse_datetime(row[3]),
                active=bool(row[5]),
            )
            people.append(person)

        return people

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list people: {e!s}",
        )


@router.get("/people/{person_id}", response_model=PersonResponse)
async def get_person(person_id: int) -> PersonResponse:
    """
    Get a specific person by ID.

    Args:
        person_id: Person ID

    Returns:
        Person details
    """
    try:
        db_manager = get_database_manager()

        # Get person from database
        query = """
            SELECT id, name, sample_count, created_at, updated_at, active
            FROM people
            WHERE id = ?
        """

        rows = db_manager.execute_query(query, (person_id,))

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Person not found"
            )

        row = rows[0]
        return PersonResponse(
            id=row[0],
            name=row[1],
            sample_count=row[2],
            created_at=_parse_datetime(row[3]),
            active=bool(row[5]),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get person: {e!s}",
        )


@router.post(
    "/people", response_model=PersonResponse, status_code=status.HTTP_201_CREATED
)
async def create_person(request: CreatePersonRequest) -> PersonResponse:
    """
    Enroll a new person for face search.

    Args:
        request: Person creation request

    Returns:
        Created person details
    """
    try:
        # Import photo model (face worker is imported only if needed)
        from ..models.photo import Photo

        db_manager = get_database_manager()

        # Check if face search is enabled
        from ..api.config import _get_config_from_db

        config = _get_config_from_db(db_manager)
        if not config.get("face_search_enabled", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Face search is disabled. Enable face search in configuration to create people.",
            )

        # Check if name already exists
        name_check_query = "SELECT id FROM people WHERE name = ?"
        existing = db_manager.execute_query(name_check_query, (request.name,))

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person with this name already exists",
            )

        # Validate that all sample file IDs exist
        file_ids_str = ",".join("?" * len(request.sample_file_ids))
        photos_query = f"""
            SELECT id, path, filename, modified_ts
            FROM photos
            WHERE id IN ({file_ids_str})
        """

        photo_rows = db_manager.execute_query(photos_query, request.sample_file_ids)

        if len(photo_rows) != len(request.sample_file_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more sample photos not found",
            )

        # Convert to Photo objects
        sample_photos = []
        for row in photo_rows:
            photo = Photo(id=row[0], path=row[1], filename=row[2], modified_ts=row[3])
            sample_photos.append(photo)

        # Use face worker to enroll person (or a deterministic dummy embedding in E2E mode)
        if _is_e2e_test_mode():
            # Avoid requiring real faces / InsightFace during deterministic E2E runs
            dummy_vec = _dummy_face_vector(
                f"{request.name}:{','.join(map(str, request.sample_file_ids))}"
            )
            person = Person(
                name=request.name,
                face_vector=dummy_vec,
                sample_count=len(request.sample_file_ids),
                created_at=datetime.now().timestamp(),
                updated_at=datetime.now().timestamp(),
                active=True,
            )
        else:
            from ..workers.face_worker import FaceDetectionWorker

            face_worker = FaceDetectionWorker()

            if not face_worker.is_available():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Face recognition is not available. InsightFace dependencies are not installed or failed to initialize.",
                )

            person = await face_worker.enroll_person(request.name, sample_photos)

        # Save person to database
        insert_query = """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        params = person.to_db_params()
        result = db_manager.execute_update(insert_query, params)

        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save person to database",
            )

        # Get the created person with ID
        created_person_query = """
            SELECT id, name, sample_count, created_at, updated_at, active
            FROM people
            WHERE name = ?
        """

        created_rows = db_manager.execute_query(created_person_query, (request.name,))

        if not created_rows:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created person",
            )

        row = created_rows[0]

        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"Person enrolled: {request.name} with {person.sample_count} samples"
        )

        return PersonResponse(
            id=row[0],
            name=row[1],
            sample_count=row[2],
            created_at=_parse_datetime(row[3]),
            active=bool(row[5]),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create person: {e!s}",
        )


@router.put("/people/{person_id}", response_model=PersonResponse)
async def update_person(person_id: int, request: UpdatePersonRequest) -> PersonResponse:
    """
    Update an existing person.

    Args:
        person_id: Person ID
        request: Update request

    Returns:
        Updated person details
    """
    try:
        db_manager = get_database_manager()

        # Check if person exists
        person_query = """
            SELECT id, name, face_vector, sample_count, created_at, updated_at, active
            FROM people
            WHERE id = ?
        """

        person_rows = db_manager.execute_query(person_query, (person_id,))

        if not person_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Person not found"
            )

        # Build update query
        update_fields = []
        params = []

        if request.name is not None:
            # Check if new name conflicts with existing person
            name_check_query = "SELECT id FROM people WHERE name = ? AND id != ?"
            existing = db_manager.execute_query(
                name_check_query, (request.name, person_id)
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Person with this name already exists",
                )

            update_fields.append("name = ?")
            params.append(request.name)

        if request.active is not None:
            update_fields.append("active = ?")
            params.append(request.active)

        # Handle additional sample photos
        if request.additional_sample_file_ids:
            # Import necessary classes
            from ..models.photo import Photo

            # Validate sample file IDs
            file_ids_str = ",".join("?" * len(request.additional_sample_file_ids))
            photos_query = f"""
                SELECT id, path, filename, modified_ts
                FROM photos
                WHERE id IN ({file_ids_str})
            """

            photo_rows = db_manager.execute_query(
                photos_query, request.additional_sample_file_ids
            )

            if len(photo_rows) != len(request.additional_sample_file_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more additional sample photos not found",
                )

            # Convert to Photo objects
            additional_photos = []
            for row in photo_rows:
                photo = Photo(
                    id=row[0], path=row[1], filename=row[2], modified_ts=row[3]
                )
                additional_photos.append(photo)

            # Load existing person
            person_row = person_rows[0]
            existing_person = Person.from_db_row(
                {
                    "id": person_row[0],
                    "name": person_row[1],
                    "face_vector": person_row[2],
                    "sample_count": person_row[3],
                    "created_at": person_row[4],
                    "updated_at": person_row[5],
                    "active": person_row[6],
                }
            )

            if _is_e2e_test_mode():
                # In E2E mode we don't require real faces; keep the vector stable and
                # just bump sample_count so the UI behaves correctly.
                existing_person.sample_count += len(additional_photos)
                existing_person.updated_at = datetime.now().timestamp()

                update_fields.extend(["face_vector = ?", "sample_count = ?"])
                params.extend(
                    [
                        Person._numpy_to_blob(existing_person.face_vector),
                        existing_person.sample_count,
                    ]
                )
            else:
                from ..workers.face_worker import FaceDetectionWorker

                # Update enrollment with additional photos
                face_worker = FaceDetectionWorker()

                if not face_worker.is_available():
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Face recognition not available",
                    )

                updated_person = await face_worker.update_person_enrollment(
                    existing_person, additional_photos
                )

                # Update face vector and sample count
                update_fields.extend(["face_vector = ?", "sample_count = ?"])
                params.extend(
                    [
                        Person._numpy_to_blob(updated_person.face_vector),
                        updated_person.sample_count,
                    ]
                )

        if update_fields:
            # Add updated_at timestamp
            update_fields.append("updated_at = datetime('now')")

            # Execute update
            update_query = f"""
                UPDATE people
                SET {", ".join(update_fields)}
                WHERE id = ?
            """

            params.append(person_id)
            db_manager.execute_update(update_query, params)

        # Get updated person
        updated_rows = db_manager.execute_query(person_query, (person_id,))
        row = updated_rows[0]

        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Person updated: {row[1]} (ID: {person_id})")

        return PersonResponse(
            id=row[0],
            name=row[1],
            sample_count=row[3],
            created_at=_parse_datetime(row[4]),
            active=bool(row[6]),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update person: {e!s}",
        )


@router.delete("/people/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(person_id: int):
    """
    Delete an enrolled person.

    Args:
        person_id: Person ID to delete
    """
    try:
        db_manager = get_database_manager()

        # Check if person exists
        person_query = "SELECT name FROM people WHERE id = ?"
        person_rows = db_manager.execute_query(person_query, (person_id,))

        if not person_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Person not found"
            )

        person_name = person_rows[0][0]

        # Delete person (this will set person_id to NULL in faces table due to FK constraint)
        delete_query = "DELETE FROM people WHERE id = ?"
        result = db_manager.execute_update(delete_query, (person_id,))

        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete person",
            )

        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Person deleted: {person_name} (ID: {person_id})")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete person: {e!s}",
        )


@router.get("/people/{person_id}/photos")
async def get_person_photos(
    person_id: int, limit: int = 50, offset: int = 0
) -> dict[str, Any]:
    """
    Get photos containing a specific person.

    Args:
        person_id: Person ID
        limit: Maximum number of results
        offset: Results offset for pagination

    Returns:
        Photos containing the person
    """
    try:
        db_manager = get_database_manager()

        # Check if person exists
        person_query = "SELECT name FROM people WHERE id = ?"
        person_rows = db_manager.execute_query(person_query, (person_id,))

        if not person_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Person not found"
            )

        # Get photos with faces of this person
        photos_query = """
            SELECT DISTINCT p.id, p.path, p.folder, p.filename,
                   t.thumb_path, e.shot_dt, f.confidence
            FROM faces f
            JOIN photos p ON f.file_id = p.id
            LEFT JOIN thumbnails t ON p.id = t.file_id
            LEFT JOIN exif e ON p.id = e.file_id
            WHERE f.person_id = ?
            ORDER BY f.confidence DESC, p.modified_ts DESC
            LIMIT ? OFFSET ?
        """

        photo_rows = db_manager.execute_query(photos_query, (person_id, limit, offset))

        # Get total count
        count_query = """
            SELECT COUNT(DISTINCT f.file_id)
            FROM faces f
            WHERE f.person_id = ?
        """

        count_rows = db_manager.execute_query(count_query, (person_id,))
        total_count = count_rows[0][0] if count_rows else 0

        # Format results
        photos = []
        for row in photo_rows:
            photo_data = {
                "file_id": row[0],
                "path": row[1],
                "folder": row[2],
                "filename": row[3],
                "thumb_path": row[4],
                "shot_dt": row[5],
                "confidence": row[6],
            }
            photos.append(photo_data)

        return {
            "person_id": person_id,
            "person_name": person_rows[0][0],
            "total_photos": total_count,
            "photos": photos,
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get person photos: {e!s}",
        )
