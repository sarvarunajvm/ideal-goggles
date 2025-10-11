"""Unit tests for indexing API endpoints."""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException

from src.api.indexing import (
    IndexStatus,
    StartIndexRequest,
    _get_config_from_db,
    _get_indexed_photo_count,
    _get_photos_for_processing,
    _indexing_state,
    _run_discovery_phase,
    _run_indexing_process,
    _run_processing_phases,
    _setup_indexing_workers,
    get_indexing_statistics,
    get_indexing_status,
    start_indexing,
    stop_indexing,
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
    with patch("src.api.indexing.get_database_manager") as mock:
        mock.return_value = db_manager
        yield mock


@pytest.fixture
def reset_indexing_state():
    """Reset indexing state before each test."""
    # Import to access the module-level state
    from src.api import indexing

    # Reset the state
    indexing._indexing_state.clear()
    indexing._indexing_state.update(
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
    yield
    # Reset again after test
    indexing._indexing_state.clear()
    indexing._indexing_state.update(
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


class TestIndexStatusModel:
    """Test IndexStatus model."""

    def test_index_status_creation(self):
        """Test creating IndexStatus."""
        status = IndexStatus(
            status="indexing",
            progress={"total_files": 100, "processed_files": 50},
            errors=[],
            started_at=datetime.now(),
            estimated_completion=None,
        )

        assert status.status == "indexing"
        assert status.progress["total_files"] == 100
        assert status.progress["processed_files"] == 50
        assert status.errors == []


class TestStartIndexRequest:
    """Test StartIndexRequest model."""

    def test_start_index_request_default(self):
        """Test default start index request."""
        request = StartIndexRequest()
        assert request.full is False

    def test_start_index_request_full(self):
        """Test full reindex request."""
        request = StartIndexRequest(full=True)
        assert request.full is True


class TestGetIndexingStatus:
    """Test get_indexing_status endpoint."""

    @pytest.mark.asyncio
    async def test_get_indexing_status_idle(self, reset_indexing_state):
        """Test getting status when idle."""
        result = await get_indexing_status()

        assert isinstance(result, IndexStatus)
        assert result.status == "idle"
        assert result.progress["total_files"] == 0
        assert result.progress["processed_files"] == 0
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_get_indexing_status_indexing(self, reset_indexing_state):
        """Test getting status during indexing."""
        from src.api import indexing

        indexing._indexing_state["status"] = "indexing"
        indexing._indexing_state["progress"] = {
            "total_files": 100,
            "processed_files": 50,
            "current_phase": "metadata",
        }
        indexing._indexing_state["started_at"] = datetime.now()

        result = await get_indexing_status()

        assert result.status == "indexing"
        assert result.progress["total_files"] == 100
        assert result.progress["processed_files"] == 50


class TestStartIndexing:
    """Test start_indexing endpoint."""

    @pytest.mark.asyncio
    async def test_start_indexing_success(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test successful indexing start."""
        background_tasks = BackgroundTasks()
        request = StartIndexRequest(full=False)

        with patch("src.api.indexing._run_indexing_process") as mock_run:
            mock_run.return_value = AsyncMock()

            result = await start_indexing(background_tasks, request)

            assert result["message"] == "Indexing started successfully"
            assert result["full_reindex"] is False
            assert "started_at" in result

    @pytest.mark.asyncio
    async def test_start_indexing_already_running(
        self, reset_indexing_state, mock_db_manager
    ):
        """Test starting indexing when already running."""
        from src.api import indexing

        indexing._indexing_state["status"] = "indexing"

        background_tasks = BackgroundTasks()
        request = StartIndexRequest()

        with pytest.raises(HTTPException) as exc_info:
            await start_indexing(background_tasks, request)

        assert exc_info.value.status_code == 409
        assert "already in progress" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_start_indexing_with_none_request(
        self, reset_indexing_state, mock_db_manager
    ):
        """Test starting indexing with None request."""
        background_tasks = BackgroundTasks()

        with patch("src.api.indexing.asyncio.create_task") as mock_create_task:
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            result = await start_indexing(background_tasks, None)

            assert result["message"] == "Indexing started successfully"
            assert result["full_reindex"] is False

    @pytest.mark.asyncio
    async def test_start_indexing_exception(
        self, reset_indexing_state, mock_db_manager
    ):
        """Test indexing start with exception."""
        background_tasks = BackgroundTasks()
        request = StartIndexRequest()

        with patch("src.api.indexing.asyncio.create_task") as mock_create_task:
            mock_create_task.side_effect = Exception("Fatal error")

            with pytest.raises(HTTPException) as exc_info:
                await start_indexing(background_tasks, request)

            assert exc_info.value.status_code == 500


class TestStopIndexing:
    """Test stop_indexing endpoint."""

    @pytest.mark.asyncio
    async def test_stop_indexing_success(self, reset_indexing_state):
        """Test successful indexing stop."""
        from src.api import indexing

        indexing._indexing_state["status"] = "indexing"
        mock_task = MagicMock()
        indexing._indexing_state["task"] = mock_task

        result = await stop_indexing()

        assert result["message"] == "Indexing process stopped"
        assert "stopped_at" in result
        assert indexing._indexing_state["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_stop_indexing_not_running(self, reset_indexing_state):
        """Test stopping when not running."""
        with pytest.raises(HTTPException) as exc_info:
            await stop_indexing()

        assert exc_info.value.status_code == 400
        assert "No indexing process is currently running" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_stop_indexing_exception(self, reset_indexing_state):
        """Test stop indexing with exception."""
        from src.api import indexing

        indexing._indexing_state["status"] = "indexing"
        mock_task = MagicMock()
        mock_task.cancel.side_effect = Exception("Cancel error")
        indexing._indexing_state["task"] = mock_task

        with pytest.raises(HTTPException) as exc_info:
            await stop_indexing()

        assert exc_info.value.status_code == 500


class TestGetIndexingStatistics:
    """Test get_indexing_statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_indexing_statistics_success(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test getting indexing statistics."""
        db_manager.get_database_info = MagicMock(
            return_value={
                "table_counts": {
                    "photos": 100,
                    "exif": 80,
                    "embeddings": 90,
                    "faces": 50,
                    "people": 5,
                    "thumbnails": 95,
                },
                "database_size_mb": 150.5,
                "settings": {"schema_version": "1.0"},
            }
        )
        db_manager.execute_query = MagicMock(return_value=[[75]])

        result = await get_indexing_statistics()

        assert result["database"]["total_photos"] == 100
        assert result["database"]["indexed_photos"] == 75
        assert result["database"]["photos_with_exif"] == 80
        assert result["database"]["photos_with_embeddings"] == 90
        assert result["database"]["total_faces"] == 50
        assert result["database"]["enrolled_people"] == 5
        assert result["database"]["thumbnails"] == 95
        assert result["current_indexing"]["status"] == "idle"
        assert result["database_info"]["size_mb"] == 150.5

    @pytest.mark.asyncio
    async def test_get_indexing_statistics_exception(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test getting statistics with exception."""
        db_manager.get_database_info = MagicMock(side_effect=Exception("DB error"))

        with pytest.raises(HTTPException) as exc_info:
            await get_indexing_statistics()

        assert exc_info.value.status_code == 500


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_indexed_photo_count_success(self, mock_db_manager, db_manager):
        """Test getting indexed photo count."""
        db_manager.execute_query = MagicMock(return_value=[[42]])

        count = _get_indexed_photo_count(db_manager)

        assert count == 42

    def test_get_indexed_photo_count_error(self, mock_db_manager, db_manager):
        """Test getting indexed photo count with error."""
        db_manager.execute_query = MagicMock(side_effect=Exception("Query error"))

        count = _get_indexed_photo_count(db_manager)

        assert count == 0


class TestGetConfigFromDb:
    """Test _get_config_from_db function."""

    def test_get_config_from_db_success(self, mock_db_manager, db_manager):
        """Test getting config from database."""
        db_manager.execute_query = MagicMock(
            return_value=[
                ("roots", '["/path1", "/path2"]'),
                ("face_search_enabled", "true"),
            ]
        )

        config = _get_config_from_db(db_manager)

        assert config["roots"] == ["/path1", "/path2"]
        assert config["face_search_enabled"] is True

    def test_get_config_from_db_defaults(self, mock_db_manager, db_manager):
        """Test getting config with defaults."""
        db_manager.execute_query = MagicMock(return_value=[])

        config = _get_config_from_db(db_manager)

        assert config["roots"] == []
        assert config["face_search_enabled"] is True

    def test_get_config_from_db_error(self, mock_db_manager, db_manager):
        """Test getting config with error."""
        db_manager.execute_query = MagicMock(side_effect=Exception("DB error"))

        config = _get_config_from_db(db_manager)

        assert config["roots"] == []
        assert config["face_search_enabled"] is True


class TestGetPhotosForProcessing:
    """Test _get_photos_for_processing function."""

    def test_get_photos_for_processing_full_reindex(self, mock_db_manager, db_manager):
        """Test getting photos for full reindex."""

        # Mock rows with dictionary-like access
        class MockRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

        db_manager.execute_query = MagicMock(
            return_value=[
                MockRow(
                    {
                        "id": 1,
                        "path": "/path/photo1.jpg",
                        "folder": "/path",
                        "filename": "photo1.jpg",
                        "ext": ".jpg",
                        "size": 1000,
                        "created_ts": 100,
                        "modified_ts": 200,
                        "sha1": "",
                        "phash": "",
                        "indexed_at": None,
                        "index_version": None,
                    }
                ),
                MockRow(
                    {
                        "id": 2,
                        "path": "/path/photo2.jpg",
                        "folder": "/path",
                        "filename": "photo2.jpg",
                        "ext": ".jpg",
                        "size": 2000,
                        "created_ts": 100,
                        "modified_ts": 200,
                        "sha1": "",
                        "phash": "",
                        "indexed_at": None,
                        "index_version": None,
                    }
                ),
            ]
        )

        photos = _get_photos_for_processing(db_manager, full_reindex=True)

        assert len(photos) == 2
        assert photos[0].id == 1
        assert photos[1].id == 2

    def test_get_photos_for_processing_incremental(self, mock_db_manager, db_manager):
        """Test getting photos for incremental reindex."""

        # Mock rows with dictionary-like access
        class MockRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

        db_manager.execute_query = MagicMock(
            return_value=[
                MockRow(
                    {
                        "id": 1,
                        "path": "/path/photo1.jpg",
                        "folder": "/path",
                        "filename": "photo1.jpg",
                        "ext": ".jpg",
                        "size": 1000,
                        "created_ts": 100,
                        "modified_ts": 200,
                        "sha1": "",
                        "phash": "",
                        "indexed_at": None,
                        "index_version": None,
                    }
                ),
            ]
        )

        photos = _get_photos_for_processing(db_manager, full_reindex=False)

        assert len(photos) == 1
        assert photos[0].id == 1


class TestSetupIndexingWorkers:
    """Test _setup_indexing_workers function."""

    @pytest.mark.asyncio
    async def test_setup_indexing_workers(self):
        """Test setting up indexing workers."""
        workers = await _setup_indexing_workers()

        assert "FileCrawler" in workers
        assert "OptimizedCLIPWorker" in workers
        assert "EXIFExtractionPipeline" in workers
        assert "FaceDetectionWorker" in workers
        assert "SmartThumbnailGenerator" in workers


class TestRunDiscoveryPhase:
    """Test _run_discovery_phase function."""

    @pytest.mark.asyncio
    async def test_run_discovery_phase_success(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test running discovery phase."""
        from src.api import indexing

        # Set status to indexing to pass _check_cancellation
        indexing._indexing_state["status"] = "indexing"

        with patch("src.api.indexing._setup_indexing_workers") as mock_setup:
            # Mock crawler
            mock_crawler = MagicMock()
            mock_crawl_result = MagicMock()
            mock_crawl_result.total_files = 10
            mock_crawl_result.errors = 0
            mock_crawl_result.error_details = []
            mock_crawl_result.files = []
            mock_crawler.crawl_all_paths = AsyncMock(return_value=mock_crawl_result)

            mock_crawler_class = MagicMock(return_value=mock_crawler)
            mock_setup.return_value = {"FileCrawler": mock_crawler_class}

            config = {"roots": ["/test/path"]}

            result = await _run_discovery_phase(
                {"FileCrawler": mock_crawler_class}, config, full_reindex=False
            )

            assert result.total_files == 10
            assert result.errors == 0


class TestRunProcessingPhases:
    """Test _run_processing_phases function."""

    @pytest.mark.asyncio
    async def test_run_processing_phases_success(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test running processing phases."""
        from src.api import indexing

        # Set status to indexing to pass _check_cancellation
        indexing._indexing_state["status"] = "indexing"

        with (
            patch("src.api.indexing._setup_indexing_workers") as mock_setup,
            patch("src.api.indexing.asyncio.sleep") as mock_sleep,
        ):
            # Mock workers
            mock_exif = MagicMock()
            mock_exif.process_photos = AsyncMock(return_value=[])

            mock_embedding = MagicMock()
            mock_embedding.generate_batch_optimized = AsyncMock(return_value=[])

            mock_thumbnail = MagicMock()
            mock_thumbnail.generate_batch = AsyncMock(return_value=[])

            workers = {
                "EXIFExtractionPipeline": lambda: mock_exif,
                "OptimizedCLIPWorker": lambda: mock_embedding,
                "SmartThumbnailGenerator": lambda **_kwargs: mock_thumbnail,
            }

            config = {"face_search_enabled": False}
            photos = []

            await _run_processing_phases(workers, config, photos)

            assert indexing._indexing_state["progress"]["current_phase"] == "thumbnails"

    @pytest.mark.asyncio
    async def test_run_processing_phases_with_faces(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test running processing phases with face detection."""
        from src.api import indexing

        # Set status to indexing to pass _check_cancellation
        indexing._indexing_state["status"] = "indexing"

        with (
            patch("src.api.indexing._setup_indexing_workers") as mock_setup,
            patch("src.api.indexing.asyncio.sleep") as mock_sleep,
        ):
            # Mock workers
            mock_exif = MagicMock()
            mock_exif.process_photos = AsyncMock(return_value=[])

            mock_embedding = MagicMock()
            mock_embedding.generate_batch_optimized = AsyncMock(return_value=[])

            mock_thumbnail = MagicMock()
            mock_thumbnail.generate_batch = AsyncMock(return_value=[])

            mock_face = MagicMock()
            mock_face.is_available = MagicMock(return_value=True)
            mock_face.process_batch = AsyncMock(return_value=[])

            workers = {
                "EXIFExtractionPipeline": lambda: mock_exif,
                "OptimizedCLIPWorker": lambda: mock_embedding,
                "SmartThumbnailGenerator": lambda **_kwargs: mock_thumbnail,
                "FaceDetectionWorker": lambda: mock_face,
            }

            config = {"face_search_enabled": True}
            photos = []

            await _run_processing_phases(workers, config, photos)

            assert indexing._indexing_state["progress"]["current_phase"] == "faces"


class TestRunIndexingProcess:
    """Test _run_indexing_process function."""

    @pytest.mark.asyncio
    async def test_run_indexing_process_no_roots(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test indexing process with no roots configured."""
        from src.api import indexing

        db_manager.execute_query = MagicMock(return_value=[])

        await _run_indexing_process(full_reindex=False)

        # When no roots, status becomes "error" and errors are added
        assert indexing._indexing_state["status"] == "error"
        assert len(indexing._indexing_state["errors"]) > 0

    @pytest.mark.asyncio
    async def test_run_indexing_process_invalid_roots(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test indexing process with invalid roots."""
        from src.api import indexing

        db_manager.execute_query = MagicMock(
            return_value=[("roots", '["/nonexistent/path"]')]
        )

        await _run_indexing_process(full_reindex=False)

        # When roots are invalid but configured, status is idle and errors contain message
        assert indexing._indexing_state["status"] == "idle"
        assert len(indexing._indexing_state["errors"]) > 0
        assert indexing._indexing_state["progress"]["current_phase"] == "completed"

    @pytest.mark.asyncio
    async def test_run_indexing_process_cancelled(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test indexing process cancellation."""
        from src.api import indexing

        db_manager.execute_query = MagicMock(return_value=[("roots", '["/tmp"]')])

        with patch("src.api.indexing._setup_indexing_workers") as mock_setup:
            mock_setup.side_effect = asyncio.CancelledError()

            await _run_indexing_process(full_reindex=False)

            assert indexing._indexing_state["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_run_indexing_process_error(
        self, reset_indexing_state, mock_db_manager, db_manager
    ):
        """Test indexing process with error."""
        from src.api import indexing

        db_manager.execute_query = MagicMock(side_effect=Exception("Fatal error"))

        await _run_indexing_process(full_reindex=False)

        assert indexing._indexing_state["status"] == "error"
        assert len(indexing._indexing_state["errors"]) > 0
