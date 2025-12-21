"""Unit tests for people API endpoints."""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from src.api.people import (
    CreatePersonRequest,
    PersonResponse,
    UpdatePersonRequest,
    _dummy_face_vector,
    _is_e2e_test_mode,
    _parse_datetime,
    create_person,
    delete_person,
    get_person,
    get_person_photos,
    list_people,
    router,
    update_person,
)
from src.db.connection import DatabaseManager
from src.models.person import Person
from src.models.photo import Photo


@pytest.fixture
def db_manager():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        manager = DatabaseManager(str(db_path))
        yield manager


@pytest.fixture
def mock_db_manager(db_manager):
    """Mock the get_database_manager function."""
    with patch("src.api.people.get_database_manager") as mock:
        mock.return_value = db_manager
        yield mock


class TestPersonResponse:
    """Test PersonResponse model."""

    def test_person_response_creation(self):
        """Test creating PersonResponse."""
        response = PersonResponse(
            id=1,
            name="John Doe",
            sample_count=5,
            created_at=datetime(2024, 1, 1),
            active=True,
        )

        assert response.id == 1
        assert response.name == "John Doe"
        assert response.sample_count == 5
        assert response.active is True


class TestCreatePersonRequest:
    """Test CreatePersonRequest validation."""

    def test_valid_create_person_request(self):
        """Test valid person creation request."""
        request = CreatePersonRequest(name="John Doe", sample_file_ids=[1, 2, 3])

        assert request.name == "John Doe"
        assert request.sample_file_ids == [1, 2, 3]

    def test_name_validation_empty_string(self):
        """Test name validation rejects empty string."""
        with pytest.raises(ValueError, match="Person name cannot be empty"):
            CreatePersonRequest(name="", sample_file_ids=[1])

    def test_name_validation_whitespace_only(self):
        """Test name validation rejects whitespace-only string."""
        with pytest.raises(ValueError, match="Person name cannot be empty"):
            CreatePersonRequest(name="   ", sample_file_ids=[1])

    def test_name_validation_too_long(self):
        """Test name validation rejects strings longer than 255 characters."""
        long_name = "a" * 256
        with pytest.raises(ValueError, match="Person name too long"):
            CreatePersonRequest(name=long_name, sample_file_ids=[1])

    def test_name_validation_strips_whitespace(self):
        """Test name validation strips whitespace."""
        request = CreatePersonRequest(name="  John Doe  ", sample_file_ids=[1])
        assert request.name == "John Doe"

    def test_sample_file_ids_validation_empty_list(self):
        """Test sample_file_ids validation rejects empty list."""
        with pytest.raises(ValueError, match="At least one sample photo is required"):
            CreatePersonRequest(name="John Doe", sample_file_ids=[])

    def test_sample_file_ids_validation_too_many(self):
        """Test sample_file_ids validation rejects more than 10 IDs."""
        with pytest.raises(ValueError, match="Too many sample photos"):
            CreatePersonRequest(name="John Doe", sample_file_ids=list(range(11)))


class TestUpdatePersonRequest:
    """Test UpdatePersonRequest validation."""

    def test_valid_update_request_name_only(self):
        """Test valid update request with name only."""
        request = UpdatePersonRequest(name="Jane Doe")
        assert request.name == "Jane Doe"
        assert request.active is None
        assert request.additional_sample_file_ids is None

    def test_valid_update_request_active_only(self):
        """Test valid update request with active only."""
        request = UpdatePersonRequest(active=False)
        assert request.name is None
        assert request.active is False

    def test_valid_update_request_all_fields(self):
        """Test valid update request with all fields."""
        request = UpdatePersonRequest(
            name="Jane Doe", active=True, additional_sample_file_ids=[4, 5]
        )
        assert request.name == "Jane Doe"
        assert request.active is True
        assert request.additional_sample_file_ids == [4, 5]

    def test_name_validation_empty_string(self):
        """Test name validation rejects empty string."""
        with pytest.raises(ValueError, match="Person name cannot be empty"):
            UpdatePersonRequest(name="")

    def test_name_validation_whitespace_only(self):
        """Test name validation rejects whitespace-only string."""
        with pytest.raises(ValueError, match="Person name cannot be empty"):
            UpdatePersonRequest(name="   ")

    def test_name_validation_too_long(self):
        """Test name validation rejects strings longer than 255 characters."""
        long_name = "a" * 256
        with pytest.raises(ValueError, match="Person name too long"):
            UpdatePersonRequest(name=long_name)

    def test_name_validation_strips_whitespace(self):
        """Test name validation strips whitespace."""
        request = UpdatePersonRequest(name="  Jane Doe  ")
        assert request.name == "Jane Doe"

    def test_name_validation_none_allowed(self):
        """Test name validation allows None."""
        request = UpdatePersonRequest(name=None, active=True)
        assert request.name is None


@pytest.mark.asyncio
class TestListPeople:
    """Test list_people endpoint."""

    async def test_list_people_empty(self, mock_db_manager):
        """Test listing people when database is empty."""
        result = await list_people()

        assert result == []

    async def test_list_people_with_data(self, mock_db_manager, db_manager):
        """Test listing people with data."""
        # Insert test data
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Jane Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                5,
                1640995300.0,
                1640995300.0,
                False,
            ),
        )

        result = await list_people()

        assert len(result) == 2
        assert result[0].name == "Jane Doe"
        assert result[1].name == "John Doe"
        assert result[0].sample_count == 5
        assert result[1].sample_count == 3
        assert result[0].active is False
        assert result[1].active is True

    async def test_list_people_database_error(self, mock_db_manager, db_manager):
        """Test handling database errors when listing people."""
        # Mock execute_query to raise an exception
        original_execute_query = db_manager.execute_query

        def mock_execute_query(query, params=None):
            msg = "Database error"
            raise Exception(msg)

        db_manager.execute_query = mock_execute_query

        with pytest.raises(HTTPException) as exc_info:
            await list_people()

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to list people" in exc_info.value.detail


@pytest.mark.asyncio
class TestGetPerson:
    """Test get_person endpoint."""

    async def test_get_person_success(self, mock_db_manager, db_manager):
        """Test getting a person successfully."""
        # Insert test data
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        result = await get_person(1)

        assert result.id == 1
        assert result.name == "John Doe"
        assert result.sample_count == 3
        assert result.active is True

    async def test_get_person_not_found(self, mock_db_manager):
        """Test getting a non-existent person."""
        with pytest.raises(HTTPException) as exc_info:
            await get_person(999)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Person not found"

    async def test_get_person_database_error(self, mock_db_manager, db_manager):
        """Test handling database errors when getting person."""

        # Mock execute_query to raise an exception
        def mock_execute_query(query, params=None):
            msg = "Database error"
            raise Exception(msg)

        db_manager.execute_query = mock_execute_query

        with pytest.raises(HTTPException) as exc_info:
            await get_person(1)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to get person" in exc_info.value.detail


@pytest.mark.asyncio
class TestCreatePerson:
    """Test create_person endpoint."""

    async def test_create_person_success(self, mock_db_manager, db_manager):
        """Test creating a person successfully."""
        # Insert test photos
        for i in range(1, 4):
            db_manager.execute_update(
                """
                INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"/test/photo{i}.jpg",
                    "/test",
                    f"photo{i}.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    f"abc{i}",
                ),
            )

        # Mock face worker
        mock_face_worker = Mock()
        mock_face_worker.is_available.return_value = True
        mock_person = Person(
            name="John Doe",
            face_vector=np.random.randn(512).astype(np.float32),
            sample_count=3,
        )
        mock_face_worker.enroll_person = AsyncMock(return_value=mock_person)

        # Mock config
        mock_config = {"face_search_enabled": True}

        with (
            patch(
                "src.workers.face_worker.FaceDetectionWorker",
                return_value=mock_face_worker,
            ),
            patch("src.api.config._get_config_from_db", return_value=mock_config),
        ):
            request = CreatePersonRequest(name="John Doe", sample_file_ids=[1, 2, 3])
            result = await create_person(request)

            assert result.name == "John Doe"
            assert result.sample_count == 3
            assert result.active is True

    async def test_create_person_face_search_disabled(
        self, mock_db_manager, db_manager
    ):
        """Test creating a person when face search is disabled."""
        mock_config = {"face_search_enabled": False}

        with patch("src.api.config._get_config_from_db", return_value=mock_config):
            request = CreatePersonRequest(name="John Doe", sample_file_ids=[1, 2, 3])

            with pytest.raises(HTTPException) as exc_info:
                await create_person(request)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Face search is disabled" in exc_info.value.detail

    async def test_create_person_duplicate_name(self, mock_db_manager, db_manager):
        """Test creating a person with duplicate name."""
        # Insert existing person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        mock_config = {"face_search_enabled": True}

        with patch("src.api.config._get_config_from_db", return_value=mock_config):
            request = CreatePersonRequest(name="John Doe", sample_file_ids=[1, 2, 3])

            with pytest.raises(HTTPException) as exc_info:
                await create_person(request)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Person with this name already exists" in exc_info.value.detail

    async def test_create_person_invalid_photo_ids(self, mock_db_manager, db_manager):
        """Test creating a person with invalid photo IDs."""
        mock_config = {"face_search_enabled": True}

        with patch("src.api.config._get_config_from_db", return_value=mock_config):
            request = CreatePersonRequest(name="John Doe", sample_file_ids=[999, 1000])

            with pytest.raises(HTTPException) as exc_info:
                await create_person(request)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "One or more sample photos not found" in exc_info.value.detail

    async def test_create_person_face_worker_unavailable(
        self, mock_db_manager, db_manager
    ):
        """Test creating a person when face worker is unavailable."""
        # Insert test photos
        for i in range(1, 4):
            db_manager.execute_update(
                """
                INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"/test/photo{i}.jpg",
                    "/test",
                    f"photo{i}.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    f"abc{i}",
                ),
            )

        mock_face_worker = Mock()
        mock_face_worker.is_available.return_value = False

        mock_config = {"face_search_enabled": True}

        with (
            patch(
                "src.workers.face_worker.FaceDetectionWorker",
                return_value=mock_face_worker,
            ),
            patch("src.api.config._get_config_from_db", return_value=mock_config),
        ):
            request = CreatePersonRequest(name="John Doe", sample_file_ids=[1, 2, 3])

            with pytest.raises(HTTPException) as exc_info:
                await create_person(request)

            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "Face recognition is not available" in exc_info.value.detail

    async def test_create_person_no_faces_found(self, mock_db_manager, db_manager):
        """Test creating a person when no faces are found in sample photos."""
        # Insert test photos
        for i in range(1, 4):
            db_manager.execute_update(
                """
                INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"/test/photo{i}.jpg",
                    "/test",
                    f"photo{i}.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    f"abc{i}",
                ),
            )

        mock_face_worker = Mock()
        mock_face_worker.is_available.return_value = True
        mock_face_worker.enroll_person = AsyncMock(return_value=None)

        mock_config = {"face_search_enabled": True}

        with (
            patch(
                "src.workers.face_worker.FaceDetectionWorker",
                return_value=mock_face_worker,
            ),
            patch("src.api.config._get_config_from_db", return_value=mock_config),
        ):
            request = CreatePersonRequest(name="John Doe", sample_file_ids=[1, 2, 3])

            with pytest.raises(HTTPException) as exc_info:
                await create_person(request)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "no suitable faces found" in exc_info.value.detail


@pytest.mark.asyncio
class TestUpdatePerson:
    """Test update_person endpoint."""

    async def test_update_person_name_only(self, mock_db_manager, db_manager):
        """Test updating person name only."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        request = UpdatePersonRequest(name="Jane Doe")
        result = await update_person(1, request)

        assert result.name == "Jane Doe"
        assert result.sample_count == 3
        assert result.active is True

    async def test_update_person_active_status(self, mock_db_manager, db_manager):
        """Test updating person active status."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        request = UpdatePersonRequest(active=False)
        result = await update_person(1, request)

        assert result.name == "John Doe"
        assert result.active is False

    async def test_update_person_not_found(self, mock_db_manager):
        """Test updating non-existent person."""
        request = UpdatePersonRequest(name="Jane Doe")

        with pytest.raises(HTTPException) as exc_info:
            await update_person(999, request)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Person not found"

    async def test_update_person_duplicate_name(self, mock_db_manager, db_manager):
        """Test updating person with duplicate name."""
        # Insert test persons
        for name in ["John Doe", "Jane Doe"]:
            db_manager.execute_update(
                """
                INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                    3,
                    1640995200.0,
                    1640995200.0,
                    True,
                ),
            )

        request = UpdatePersonRequest(name="Jane Doe")

        with pytest.raises(HTTPException) as exc_info:
            await update_person(1, request)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Person with this name already exists" in exc_info.value.detail

    async def test_update_person_with_additional_samples(
        self, mock_db_manager, db_manager
    ):
        """Test updating person with additional sample photos."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        # Insert test photos
        for i in range(4, 6):
            db_manager.execute_update(
                """
                INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"/test/photo{i}.jpg",
                    "/test",
                    f"photo{i}.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    f"abc{i}",
                ),
            )

        # Mock face worker
        mock_face_worker = Mock()
        mock_face_worker.is_available.return_value = True
        updated_person = Person(
            name="John Doe",
            face_vector=np.random.randn(512).astype(np.float32),
            sample_count=5,
        )
        mock_face_worker.update_person_enrollment = AsyncMock(
            return_value=updated_person
        )

        # Get the actual photo IDs that were inserted
        photo_rows = db_manager.execute_query(
            "SELECT id FROM photos ORDER BY id DESC LIMIT 2", ()
        )
        photo_ids = [dict(row)["id"] for row in photo_rows]
        photo_ids.reverse()  # Reverse to get ascending order

        with patch(
            "src.workers.face_worker.FaceDetectionWorker", return_value=mock_face_worker
        ):
            request = UpdatePersonRequest(additional_sample_file_ids=photo_ids)
            result = await update_person(1, request)

            assert result.name == "John Doe"
            assert result.sample_count == 5

    async def test_update_person_invalid_additional_photos(
        self, mock_db_manager, db_manager
    ):
        """Test updating person with invalid additional photo IDs."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        request = UpdatePersonRequest(additional_sample_file_ids=[999, 1000])

        with pytest.raises(HTTPException) as exc_info:
            await update_person(1, request)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "One or more additional sample photos not found" in exc_info.value.detail

    async def test_update_person_face_worker_unavailable(
        self, mock_db_manager, db_manager
    ):
        """Test updating person when face worker is unavailable."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        # Insert test photo
        db_manager.execute_update(
            """
            INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "/test/photo4.jpg",
                "/test",
                "photo4.jpg",
                ".jpg",
                1024,
                1640995200.0,
                1640995200.0,
                "abc4",
            ),
        )

        mock_face_worker = Mock()
        mock_face_worker.is_available.return_value = False

        with patch(
            "src.workers.face_worker.FaceDetectionWorker", return_value=mock_face_worker
        ):
            request = UpdatePersonRequest(additional_sample_file_ids=[1])

            with pytest.raises(HTTPException) as exc_info:
                await update_person(1, request)

            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.asyncio
class TestDeletePerson:
    """Test delete_person endpoint."""

    async def test_delete_person_success(self, mock_db_manager, db_manager):
        """Test deleting a person successfully."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        await delete_person(1)

        # Verify person is deleted
        rows = db_manager.execute_query("SELECT * FROM people WHERE id = ?", (1,))
        assert len(rows) == 0

    async def test_delete_person_not_found(self, mock_db_manager):
        """Test deleting non-existent person."""
        with pytest.raises(HTTPException) as exc_info:
            await delete_person(999)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Person not found"

    async def test_delete_person_database_error(self, mock_db_manager, db_manager):
        """Test handling database error during deletion."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        # Mock execute_update to return 0 (failed deletion)
        original_execute_update = db_manager.execute_update

        def mock_execute_update(query, params):
            if "DELETE" in query:
                return 0
            return original_execute_update(query, params)

        db_manager.execute_update = mock_execute_update

        with pytest.raises(HTTPException) as exc_info:
            await delete_person(1)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to delete person" in exc_info.value.detail


@pytest.mark.asyncio
class TestGetPersonPhotos:
    """Test get_person_photos endpoint."""

    async def test_get_person_photos_success(self, mock_db_manager, db_manager):
        """Test getting photos for a person."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        # Insert test photos and faces
        for i in range(1, 4):
            db_manager.execute_update(
                """
                INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"/test/photo{i}.jpg",
                    "/test",
                    f"photo{i}.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    f"abc{i}",
                ),
            )

            # Insert face
            db_manager.execute_update(
                """
                INSERT INTO faces (file_id, person_id, box_xyxy, face_vector, confidence, verified)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    i,
                    1,
                    "[0, 0, 100, 100]",
                    Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                    0.9,
                    False,
                ),
            )

        result = await get_person_photos(1)

        assert result["person_id"] == 1
        assert result["person_name"] == "John Doe"
        assert result["total_photos"] == 3
        assert len(result["photos"]) == 3
        assert result["limit"] == 50
        assert result["offset"] == 0

    async def test_get_person_photos_with_pagination(self, mock_db_manager, db_manager):
        """Test getting photos with pagination."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        # Insert multiple photos
        for i in range(1, 6):
            db_manager.execute_update(
                """
                INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"/test/photo{i}.jpg",
                    "/test",
                    f"photo{i}.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    f"abc{i}",
                ),
            )

            # Insert face
            db_manager.execute_update(
                """
                INSERT INTO faces (file_id, person_id, box_xyxy, face_vector, confidence, verified)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    i,
                    1,
                    "[0, 0, 100, 100]",
                    Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                    0.9,
                    False,
                ),
            )

        result = await get_person_photos(1, limit=2, offset=1)

        assert result["total_photos"] == 5
        assert len(result["photos"]) == 2
        assert result["limit"] == 2
        assert result["offset"] == 1

    async def test_get_person_photos_person_not_found(self, mock_db_manager):
        """Test getting photos for non-existent person."""
        with pytest.raises(HTTPException) as exc_info:
            await get_person_photos(999)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Person not found"

    async def test_get_person_photos_no_photos(self, mock_db_manager, db_manager):
        """Test getting photos when person has no photos."""
        # Insert test person
        db_manager.execute_update(
            """
            INSERT INTO people (name, face_vector, sample_count, created_at, updated_at, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "John Doe",
                Person._numpy_to_blob(np.random.randn(512).astype(np.float32)),
                3,
                1640995200.0,
                1640995200.0,
                True,
            ),
        )

        result = await get_person_photos(1)

        assert result["total_photos"] == 0
        assert len(result["photos"]) == 0

    async def test_get_person_photos_database_error(self, mock_db_manager, db_manager):
        """Test handling database error when getting photos."""

        # Mock execute_query to raise an exception
        def mock_execute_query(query, params=None):
            msg = "Database error"
            raise Exception(msg)

        db_manager.execute_query = mock_execute_query

        with pytest.raises(HTTPException) as exc_info:
            await get_person_photos(1)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to get person photos" in exc_info.value.detail


# === Merged from test_people_extended.py ===


class TestHelperFunctions:
    """Test helper functions coverage."""

    def test_parse_datetime_none(self):
        """Test parsing None."""
        dt = _parse_datetime(None)
        assert isinstance(dt, datetime)
        # Should be close to now
        assert (datetime.now() - dt).total_seconds() < 1

    def test_parse_datetime_datetime(self):
        """Test parsing datetime object."""
        now = datetime.now()
        dt = _parse_datetime(now)
        assert dt == now

    def test_parse_datetime_timestamp(self):
        """Test parsing timestamp."""
        ts = 1640995200.0
        dt = _parse_datetime(ts)
        assert dt.timestamp() == ts

    def test_parse_datetime_iso(self):
        """Test parsing ISO string."""
        iso = "2022-01-01T00:00:00"
        dt = _parse_datetime(iso)
        assert dt.year == 2022

    def test_parse_datetime_sqlite_format(self):
        """Test parsing SQLite format."""
        s = "2022-01-01 12:00:00"
        dt = _parse_datetime(s)
        assert dt.year == 2022
        assert dt.hour == 12

    def test_parse_datetime_date_only(self):
        """Test parsing date only."""
        s = "2022-01-01"
        dt = _parse_datetime(s)
        assert dt.year == 2022

    def test_parse_datetime_invalid(self):
        """Test parsing invalid string fallback."""
        dt = _parse_datetime("invalid")
        assert isinstance(dt, datetime)

    def test_is_e2e_test_mode(self):
        """Test E2E mode check."""
        with patch.dict(os.environ, {"E2E_TEST": "1"}):
            assert _is_e2e_test_mode() is True

        with patch.dict(os.environ, {"E2E_TEST": "false"}):
            assert _is_e2e_test_mode() is False

    def test_dummy_face_vector(self):
        """Test dummy vector generation with mocks."""
        mock_rng = MagicMock()
        mock_array = MagicMock()
        mock_array.astype.return_value = MagicMock()
        # Make the vector support len() and division
        mock_vec = MagicMock()
        mock_vec.__len__.return_value = 512
        mock_vec.__truediv__.return_value = mock_vec
        mock_array.astype.return_value = mock_vec

        mock_rng.normal.return_value = mock_array

        with patch("src.api.people.np.random.default_rng", return_value=mock_rng):
            with patch("src.api.people.np.linalg.norm", return_value=1.0):
                vec = _dummy_face_vector("test")
                assert len(vec) == 512


class TestCreatePersonCoverage:
    """Tests for create_person endpoint coverage."""

    @pytest.mark.asyncio
    async def test_create_person_e2e_mode(self):
        """Test create_person in E2E mode."""
        request = CreatePersonRequest(name="E2E User", sample_file_ids=[1])

        mock_db = MagicMock()
        # Config
        mock_db.execute_query.side_effect = [
            # Config check is skipped because we patch _get_config_from_db
            [], # Name check (no existing)
            [(1, "/path/1.jpg", "1.jpg", 1000)], # Photos check
            [(1, "E2E User", 1, "2022-01-01", "2022-01-01", 1)] # Return created
        ]
        mock_db.execute_update.return_value = 1 # Success

        with patch("src.api.people.get_database_manager", return_value=mock_db):
            with patch("src.api.people._is_e2e_test_mode", return_value=True):
                # Mock config
                with patch("src.api.config._get_config_from_db", return_value={"face_search_enabled": True}):
                    # Also patch _dummy_face_vector to return a simple list, avoid numpy issues
                    with patch("src.api.people._dummy_face_vector", return_value=[0.1]*512):
                        result = await create_person(request)
                        assert result.name == "E2E User"

    @pytest.mark.asyncio
    async def test_create_person_db_insert_fail(self):
        """Test create_person fails on DB insert."""
        request = CreatePersonRequest(name="Fail User", sample_file_ids=[1])

        mock_db = MagicMock()
        mock_db.execute_query.side_effect = [
            [], # Name check
            [(1, "/path/1.jpg", "1.jpg", 1000)], # Photos check
        ]
        mock_db.execute_update.return_value = 0 # Fail

        with patch("src.api.people.get_database_manager", return_value=mock_db):
            with patch("src.api.config._get_config_from_db", return_value={"face_search_enabled": True}):
                # Mock face worker
                mock_worker = MagicMock()
                mock_worker.is_available.return_value = True
                mock_worker.enroll_person = AsyncMock(return_value=MagicMock(to_db_params=list))

                with patch("src.workers.face_worker.FaceDetectionWorker", return_value=mock_worker):
                    with pytest.raises(HTTPException) as exc:
                        await create_person(request)
                    assert exc.value.status_code == 500
                    assert "Failed to save person" in exc.value.detail

    @pytest.mark.asyncio
    async def test_create_person_retrieve_fail(self):
        """Test create_person fails to retrieve created record."""
        request = CreatePersonRequest(name="Ghost User", sample_file_ids=[1])

        mock_db = MagicMock()
        # Mock responses
        # 1. Name check -> empty
        # 2. Photos check -> valid
        # 3. Created person retrieval -> empty (fail)

        # Note: Config check is separate call

        mock_db.execute_query.side_effect = [
            [], # Name check
            [(1, "/path/1.jpg", "1.jpg", 1000)], # Photos check
            [], # Retrieve created -> fail
        ]
        mock_db.execute_update.return_value = 1

        with patch("src.api.people.get_database_manager", return_value=mock_db):
            with patch("src.api.config._get_config_from_db", return_value={"face_search_enabled": True}):
                mock_worker = MagicMock()
                mock_worker.is_available.return_value = True
                mock_worker.enroll_person = AsyncMock(return_value=MagicMock(to_db_params=list))

                with patch("src.workers.face_worker.FaceDetectionWorker", return_value=mock_worker):
                    with pytest.raises(HTTPException) as exc:
                        await create_person(request)
                    assert exc.value.status_code == 500
                    assert "Failed to retrieve created" in exc.value.detail


class TestUpdatePersonCoverage:
    """Tests for update_person endpoint coverage."""

    @pytest.mark.asyncio
    async def test_update_person_e2e_mode(self):
        """Test update_person with additional photos in E2E mode."""
        request = UpdatePersonRequest(additional_sample_file_ids=[2])

        mock_db = MagicMock()

        # 1. Check person exists
        # 2. Validate photos
        # 3. Get updated person

        mock_db.execute_query.side_effect = [
            [(1, "Test User", b"vec", 1, 100, 100, 1)], # Person exists
            [(2, "/path/2.jpg", "2.jpg", 2000)], # Photo exists
            # Updated person return: id, name, face_vector, sample_count, created_at, updated_at, active
            [(1, "Test User", b"vec", 2, 100, 200, 1)]
        ]

        from src.models.person import Person
        mock_person = MagicMock(spec=Person)
        mock_person.sample_count = 1
        mock_person.face_vector = [0.1]*512
        mock_person.updated_at = 100

        with patch("src.api.people.get_database_manager", return_value=mock_db):
            with patch("src.api.people._is_e2e_test_mode", return_value=True):
                # Mock Person.from_db_row to return our mock person and avoid blob parsing
                with patch("src.models.person.Person.from_db_row", return_value=mock_person):
                    # Mock _numpy_to_blob since it's called on update
                    with patch("src.models.person.Person._numpy_to_blob", return_value=b"blob"):
                        result = await update_person(1, request)
                        assert mock_person.sample_count == 2
                        mock_db.execute_update.assert_called()

    @pytest.mark.asyncio
    async def test_update_person_exception(self):
        """Test generic exception handling."""
        mock_db = MagicMock()
        mock_db.execute_query.side_effect = Exception("DB Error")

        with patch("src.api.people.get_database_manager", return_value=mock_db):
            with pytest.raises(HTTPException) as exc:
                await update_person(1, UpdatePersonRequest(name="New Name"))
            assert exc.value.status_code == 500

