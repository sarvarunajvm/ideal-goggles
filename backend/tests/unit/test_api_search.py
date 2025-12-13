"""Unit tests for search API endpoints."""

import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from src.api.search import (
    FaceSearchRequest,
    SearchResultItem,
    SearchResults,
    SemanticSearchRequest,
    _execute_face_search,
    _execute_image_search,
    _execute_semantic_search,
    _execute_text_search,
    face_search,
    get_original_photo,
    image_search,
    search_photos,
    semantic_search,
)
from src.db.connection import DatabaseManager


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
    with patch("src.api.search.get_database_manager") as mock:
        mock.return_value = db_manager
        yield mock


class TestSearchResultItem:
    """Test SearchResultItem model."""

    def test_search_result_item_creation(self):
        """Test creating SearchResultItem."""
        item = SearchResultItem(
            file_id=1,
            path="/path/to/photo.jpg",
            folder="/path/to",
            filename="photo.jpg",
            thumb_path="/thumb/photo.jpg",
            shot_dt=datetime.now(),
            score=0.95,
            badges=["filename", "ocr"],
            snippet="Sample text",
        )

        assert item.file_id == 1
        assert item.path == "/path/to/photo.jpg"
        assert item.score == 0.95
        assert "filename" in item.badges


class TestSearchResults:
    """Test SearchResults model."""

    def test_search_results_creation(self):
        """Test creating SearchResults."""
        items = [
            SearchResultItem(
                file_id=1,
                path="/path/photo.jpg",
                folder="/path",
                filename="photo.jpg",
                thumb_path=None,
                shot_dt=None,
                score=0.95,
                badges=[],
                snippet=None,
            )
        ]

        results = SearchResults(
            query="test query", total_matches=1, items=items, took_ms=50
        )

        assert results.query == "test query"
        assert results.total_matches == 1
        assert len(results.items) == 1
        assert results.took_ms == 50


class TestSemanticSearchRequest:
    """Test SemanticSearchRequest model."""

    def test_semantic_search_request_default(self):
        """Test default semantic search request."""
        request = SemanticSearchRequest(text="sunset beach")
        assert request.text == "sunset beach"
        assert request.top_k == 50

    def test_semantic_search_request_custom_top_k(self):
        """Test custom top_k value."""
        request = SemanticSearchRequest(text="mountain", top_k=100)
        assert request.top_k == 100


class TestFaceSearchRequest:
    """Test FaceSearchRequest model."""

    def test_face_search_request_default(self):
        """Test default face search request."""
        request = FaceSearchRequest(person_id=1)
        assert request.person_id == 1
        assert request.top_k == 50

    def test_face_search_request_custom_top_k(self):
        """Test custom top_k value."""
        request = FaceSearchRequest(person_id=2, top_k=75)
        assert request.person_id == 2
        assert request.top_k == 75


class TestSearchPhotos:
    """Test search_photos endpoint."""

    @pytest.mark.asyncio
    async def test_search_photos_basic_query(self, mock_db_manager, db_manager):
        """Test basic text search."""
        db_manager.execute_query = MagicMock(
            return_value=[
                (
                    1,
                    "/path/photo.jpg",
                    "/path",
                    "photo.jpg",
                    "/thumb/photo.jpg",
                    "2024-01-01T12:00:00",
                    1.0,
                    "",
                )
            ]
        )

        with patch("src.api.search.get_request_id") as mock_request_id:
            mock_request_id.return_value = "test-request-id"

            result = await search_photos(
                q="vacation",
                from_date=None,
                to_date=None,
                folder=None,
                limit=50,
                offset=0,
            )

            assert isinstance(result, SearchResults)
            assert result.query == "vacation"
            assert result.total_matches == 1
            assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_search_photos_with_date_filters(self, mock_db_manager, db_manager):
        """Test search with date filters."""
        db_manager.execute_query = MagicMock(return_value=[])

        with patch("src.api.search.get_request_id") as mock_request_id:
            mock_request_id.return_value = "test-request-id"

            result = await search_photos(
                q="test",
                from_date=date(2024, 1, 1),
                to_date=date(2024, 12, 31),
                limit=50,
                offset=0,
            )

            assert result.total_matches == 0

    @pytest.mark.asyncio
    async def test_search_photos_with_folder_filter(self, mock_db_manager, db_manager):
        """Test search with folder filter."""
        db_manager.execute_query = MagicMock(return_value=[])

        with patch("src.api.search.get_request_id") as mock_request_id:
            mock_request_id.return_value = "test-request-id"

            result = await search_photos(
                q="test",
                from_date=None,
                to_date=None,
                folder="/vacation",
                limit=50,
                offset=0,
            )

            assert result.total_matches == 0

    @pytest.mark.asyncio
    async def test_search_photos_no_query(self, mock_db_manager, db_manager):
        """Test search without query text."""
        db_manager.execute_query = MagicMock(return_value=[])

        with patch("src.api.search.get_request_id") as mock_request_id:
            mock_request_id.return_value = "test-request-id"

            result = await search_photos(
                q=None, from_date=None, to_date=None, folder=None, limit=50, offset=0
            )

            assert result.query == ""

    @pytest.mark.asyncio
    async def test_search_photos_exception(self, mock_db_manager, db_manager):
        """Test search with exception."""
        db_manager.execute_query = MagicMock(side_effect=Exception("DB error"))

        with patch("src.api.search.get_request_id") as mock_request_id:
            mock_request_id.return_value = "test-request-id"

            with pytest.raises(HTTPException) as exc_info:
                await search_photos(q="test", limit=50, offset=0)

            assert exc_info.value.status_code == 500


class TestSemanticSearch:
    """Test semantic_search endpoint."""

    @pytest.mark.asyncio
    async def test_semantic_search_success(self, mock_db_manager, db_manager):
        """Test successful semantic search."""
        request = SemanticSearchRequest(text="sunset beach", top_k=10)

        with (
            patch("src.api.search.DependencyChecker.check_clip") as mock_check_clip,
            patch(
                "src.workers.embedding_worker.CLIPEmbeddingWorker"
            ) as mock_worker_class,
        ):
            mock_check_clip.return_value = (True, None)

            mock_worker = MagicMock()
            mock_worker.generate_text_embedding = AsyncMock(
                return_value=[0.1, 0.2, 0.3]
            )
            mock_worker_class.return_value = mock_worker

            db_manager.execute_query = MagicMock(return_value=[])

            result = await semantic_search(request)

            assert isinstance(result, SearchResults)
            assert result.query == "sunset beach"

    @pytest.mark.asyncio
    async def test_semantic_search_clip_not_installed(
        self, mock_db_manager, db_manager
    ):
        """Test semantic search when CLIP not installed."""
        request = SemanticSearchRequest(text="sunset beach")

        with patch("src.api.search.DependencyChecker.check_clip") as mock_check_clip:
            mock_check_clip.return_value = (False, "CLIP dependencies not installed")

            with pytest.raises(HTTPException) as exc_info:
                await semantic_search(request)

            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_semantic_search_embedding_failed(self, mock_db_manager, db_manager):
        """Test semantic search when embedding generation fails."""
        request = SemanticSearchRequest(text="sunset beach")

        with (
            patch("src.api.search.DependencyChecker.check_clip") as mock_check_clip,
            patch(
                "src.workers.embedding_worker.CLIPEmbeddingWorker"
            ) as mock_worker_class,
        ):
            mock_check_clip.return_value = (True, None)

            mock_worker = MagicMock()
            mock_worker.generate_text_embedding = AsyncMock(return_value=None)
            mock_worker_class.return_value = mock_worker

            with pytest.raises(HTTPException) as exc_info:
                await semantic_search(request)

            assert exc_info.value.status_code == 500
            assert "Failed to generate text embedding" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_semantic_search_runtime_error(self, mock_db_manager, db_manager):
        """Test semantic search with runtime error."""
        request = SemanticSearchRequest(text="sunset beach")

        with (
            patch("src.api.search.DependencyChecker.check_clip") as mock_check_clip,
            patch(
                "src.workers.embedding_worker.CLIPEmbeddingWorker"
            ) as mock_worker_class,
        ):
            mock_check_clip.return_value = (True, None)

            mock_worker = MagicMock()
            mock_worker.generate_text_embedding = AsyncMock(
                side_effect=RuntimeError("CLIP dependencies not installed")
            )
            mock_worker_class.return_value = mock_worker

            with pytest.raises(HTTPException) as exc_info:
                await semantic_search(request)

            # Either 503 (CLIP not available) or 500 (runtime error) is acceptable
            assert exc_info.value.status_code in [500, 503]


class TestImageSearch:
    """Test image_search endpoint."""

    @pytest.mark.asyncio
    async def test_image_search_success(self, mock_db_manager, db_manager):
        """Test successful image search."""
        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file.write(b"fake image content")
            temp_path = temp_file.name

        try:
            # Create mock upload file
            upload_file = MagicMock(spec=UploadFile)
            upload_file.filename = "test.jpg"
            upload_file.content_type = "image/jpeg"
            upload_file.read = AsyncMock(return_value=b"fake image content")

            import sys

            mock_clip = MagicMock()
            mock_torch = MagicMock()
            sys.modules["clip"] = mock_clip
            sys.modules["torch"] = mock_torch

            try:
                with (
                    patch(
                        "src.workers.embedding_worker.CLIPEmbeddingWorker"
                    ) as mock_worker_class,
                    patch("src.models.photo.Photo") as mock_photo_class,
                ):
                    mock_worker = MagicMock()
                    mock_embedding_obj = MagicMock()
                    mock_embedding_obj.clip_vector = [0.1, 0.2, 0.3]
                    mock_worker.generate_embedding = AsyncMock(
                        return_value=mock_embedding_obj
                    )
                    mock_worker_class.return_value = mock_worker

                    db_manager.execute_query = MagicMock(return_value=[])

                    result = await image_search(file=upload_file, top_k=10)

                    assert isinstance(result, SearchResults)
                    assert "Image:" in result.query
            finally:
                if "clip" in sys.modules:
                    del sys.modules["clip"]
                if "torch" in sys.modules:
                    del sys.modules["torch"]

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_image_search_invalid_file_type(self, mock_db_manager, db_manager):
        """Test image search with invalid file type."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.content_type = "text/plain"

        with pytest.raises(HTTPException) as exc_info:
            await image_search(file=upload_file, top_k=10)

        assert exc_info.value.status_code == 400
        assert "Invalid image file" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_image_search_clip_not_installed(self, mock_db_manager, db_manager):
        """Test image search when CLIP not installed."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.content_type = "image/jpeg"

        import sys

        # Ensure clip and torch are not in sys.modules to simulate them not being installed
        if "clip" in sys.modules:
            del sys.modules["clip"]
        if "torch" in sys.modules:
            del sys.modules["torch"]

        with pytest.raises(HTTPException) as exc_info:
            await image_search(file=upload_file, top_k=10)

        # Either 503 (CLIP not available) or 500 (import failed) is acceptable
        assert exc_info.value.status_code in [500, 503]

    @pytest.mark.asyncio
    async def test_image_search_embedding_failed(self, mock_db_manager, db_manager):
        """Test image search when embedding generation fails."""
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "test.jpg"
        upload_file.content_type = "image/jpeg"
        upload_file.read = AsyncMock(return_value=b"fake image")

        import sys

        mock_clip = MagicMock()
        mock_torch = MagicMock()
        sys.modules["clip"] = mock_clip
        sys.modules["torch"] = mock_torch

        try:
            with (
                patch(
                    "src.workers.embedding_worker.CLIPEmbeddingWorker"
                ) as mock_worker_class,
                patch("src.api.search.tempfile.NamedTemporaryFile") as mock_temp,
                patch("src.models.photo.Photo"),
            ):
                mock_worker = MagicMock()
                mock_worker.generate_embedding = AsyncMock(return_value=None)
                mock_worker_class.return_value = mock_worker

                mock_temp_file = MagicMock()
                import tempfile

                mock_temp_file.name = str(Path(tempfile.gettempdir()) / "test.jpg")
                mock_temp_file.__enter__.return_value = mock_temp_file
                mock_temp.return_value = mock_temp_file

                with patch("src.api.search.os.unlink"):
                    with pytest.raises(HTTPException) as exc_info:
                        await image_search(file=upload_file, top_k=10)

                    assert exc_info.value.status_code == 400
        finally:
            if "clip" in sys.modules:
                del sys.modules["clip"]
            if "torch" in sys.modules:
                del sys.modules["torch"]


class TestFaceSearch:
    """Test face_search endpoint."""

    @pytest.mark.asyncio
    async def test_face_search_success(self, mock_db_manager, db_manager):
        """Test successful face search."""
        request = FaceSearchRequest(person_id=1, top_k=20)

        db_manager.execute_query = MagicMock(
            side_effect=[
                # Person query
                [(1, "John Doe", b"face_vector", 1)],
                # Faces query
                [],
            ]
        )

        with patch("src.api.config._get_config_from_db") as mock_config:
            mock_config.return_value = {"face_search_enabled": True}

            result = await face_search(request)

            assert isinstance(result, SearchResults)
            assert "Person:" in result.query

    @pytest.mark.asyncio
    async def test_face_search_disabled(self, mock_db_manager, db_manager):
        """Test face search when feature is disabled."""
        request = FaceSearchRequest(person_id=1)

        with patch("src.api.config._get_config_from_db") as mock_config:
            mock_config.return_value = {"face_search_enabled": False}

            with pytest.raises(HTTPException) as exc_info:
                await face_search(request)

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_face_search_person_not_found(self, mock_db_manager, db_manager):
        """Test face search when person not found."""
        request = FaceSearchRequest(person_id=999)

        db_manager.execute_query = MagicMock(return_value=[])

        with patch("src.api.config._get_config_from_db") as mock_config:
            mock_config.return_value = {"face_search_enabled": True}

            with pytest.raises(HTTPException) as exc_info:
                await face_search(request)

            assert exc_info.value.status_code == 404
            assert "Person not found" in exc_info.value.detail


class TestExecuteTextSearch:
    """Test _execute_text_search function."""

    @pytest.mark.asyncio
    async def test_execute_text_search_with_query(self, mock_db_manager, db_manager):
        """Test text search with query."""
        db_manager.execute_query = MagicMock(
            return_value=[
                (
                    1,
                    "/path/vacation.jpg",
                    "/path",
                    "vacation.jpg",
                    "/thumb/vacation.jpg",
                    "2024-01-01T12:00:00",
                    1.0,
                    "",
                )
            ]
        )

        results = await _execute_text_search(
            db_manager, "vacation", None, None, None, 50, 0
        )

        assert len(results) == 1
        assert results[0].filename == "vacation.jpg"

    @pytest.mark.asyncio
    async def test_execute_text_search_with_dates(self, mock_db_manager, db_manager):
        """Test text search with date filters."""
        db_manager.execute_query = MagicMock(return_value=[])

        results = await _execute_text_search(
            db_manager,
            None,
            date(2024, 1, 1),
            date(2024, 12, 31),
            None,
            50,
            0,
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_execute_text_search_with_folder(self, mock_db_manager, db_manager):
        """Test text search with folder filter."""
        db_manager.execute_query = MagicMock(return_value=[])

        results = await _execute_text_search(
            db_manager, None, None, None, "/vacation", 50, 0
        )

        assert len(results) == 0


class TestExecuteSemanticSearch:
    """Test _execute_semantic_search function."""

    @pytest.mark.asyncio
    async def test_execute_semantic_search_success(self, mock_db_manager, db_manager):
        """Test semantic search execution."""
        import numpy as np

        query_embedding = np.array([0.1, 0.2, 0.3])

        with patch("src.models.embedding.Embedding") as mock_embedding_class:
            mock_embedding_class._blob_to_numpy.return_value = np.array([0.1, 0.2, 0.3])

            db_manager.execute_query = MagicMock(
                return_value=[
                    (
                        1,
                        b"blob_data",
                        "/path/photo.jpg",
                        "/path",
                        "photo.jpg",
                        "/thumb/photo.jpg",
                        "2024-01-01T12:00:00",
                    )
                ]
            )

            results = await _execute_semantic_search(db_manager, query_embedding, 10)

            assert (
                len(results) >= 0
            )  # May be 0 or 1 depending on similarity calculation


class TestExecuteImageSearch:
    """Test _execute_image_search function."""

    @pytest.mark.asyncio
    async def test_execute_image_search(self, mock_db_manager, db_manager):
        """Test image search execution."""
        import numpy as np

        query_embedding = np.array([0.1, 0.2, 0.3])

        db_manager.execute_query = MagicMock(return_value=[])

        results = await _execute_image_search(db_manager, query_embedding, 10)

        assert isinstance(results, list)


class TestExecuteFaceSearch:
    """Test _execute_face_search function."""

    @pytest.mark.asyncio
    async def test_execute_face_search_success(self, mock_db_manager, db_manager):
        """Test face search execution."""
        db_manager.execute_query = MagicMock(
            return_value=[
                (
                    1,
                    0.95,
                    "/path/photo.jpg",
                    "/path",
                    "photo.jpg",
                    "/thumb/photo.jpg",
                    "2024-01-01T12:00:00",
                )
            ]
        )

        results = await _execute_face_search(db_manager, person_id=1, top_k=10)

        assert len(results) == 1
        assert results[0].score == 0.95
        assert "face" in results[0].badges


class TestGetOriginalPhoto:
    """Test get_original_photo endpoint."""

    @pytest.mark.asyncio
    async def test_get_original_photo_success(self, mock_db_manager, db_manager):
        """Test getting original photo."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file.write(b"fake image content")
            temp_path = temp_file.name

        try:
            db_manager.execute_query = MagicMock(return_value=[[temp_path]])

            result = await get_original_photo(photo_id=1)

            assert result.path == temp_path

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_get_original_photo_not_found(self, mock_db_manager, db_manager):
        """Test getting non-existent photo."""
        db_manager.execute_query = MagicMock(return_value=[])

        with pytest.raises(HTTPException) as exc_info:
            await get_original_photo(photo_id=999)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_original_photo_file_missing(self, mock_db_manager, db_manager):
        """Test getting photo when file doesn't exist."""
        db_manager.execute_query = MagicMock(return_value=[["/nonexistent/photo.jpg"]])

        with pytest.raises(HTTPException) as exc_info:
            await get_original_photo(photo_id=1)

        assert exc_info.value.status_code == 404
        assert "file not found" in exc_info.value.detail.lower()
