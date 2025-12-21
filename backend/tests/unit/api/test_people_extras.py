"""Additional coverage tests for backend/src/api/people.py."""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.people import (
    CreatePersonRequest,
    UpdatePersonRequest,
    _dummy_face_vector,
    _is_e2e_test_mode,
    _parse_datetime,
    create_person,
    update_person,
)
from src.models.photo import Photo


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

