"""Unit tests for indexing API endpoints."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException

from src.api.indexing import (
    IndexingStateManager,
    IndexStatus,
    StartIndexRequest,
    _check_cancellation,
    _get_cache_recommendations,
    _get_indexed_photo_count,
    _get_photos_for_processing,
    _indexing_state,
    _monitor_indexing_task,
    _run_discovery_phase,
    _run_indexing_process,
    _run_processing_phases,
    _setup_indexing_workers,
    _state_manager,
    get_indexing_statistics,
    get_indexing_status,
    get_model_diagnostics,
    start_indexing,
    stop_indexing,
    validate_thumbnail_cache,
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

        # Patch get_default_photo_roots to return empty list so we can test the no-roots error case
        with patch("src.api.config.get_default_photo_roots", return_value=[]):
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


# === Merged from test_indexing_extended.py ===


class TestIndexingStateManagerCoverage:
    """Tests for IndexingStateManager coverage."""

    @pytest.mark.asyncio
    async def test_calculate_estimated_completion_no_start(self):
        """Test estimation when not started."""
        manager = IndexingStateManager()
        # Ensure started_at is None
        await manager.update_state({"started_at": None})

        estimate = await manager.calculate_estimated_completion()
        assert estimate is None

    @pytest.mark.asyncio
    async def test_calculate_estimated_completion_zero_processed(self):
        """Test estimation with 0 processed files."""
        from datetime import datetime, timedelta
        manager = IndexingStateManager()
        now = datetime.now()
        await manager.update_state({
            "started_at": now - timedelta(seconds=10),
            "progress": {"total_files": 100, "processed_files": 0}
        })

        estimate = await manager.calculate_estimated_completion()
        assert estimate is None

    @pytest.mark.asyncio
    async def test_calculate_estimated_completion_valid(self):
        """Test valid estimation."""
        from datetime import datetime, timedelta
        manager = IndexingStateManager()
        now = datetime.now()
        # 10 seconds for 10 files (1 file/sec) -> 90 files left -> 90 seconds more
        await manager.update_state({
            "started_at": now - timedelta(seconds=10),
            "progress": {"total_files": 100, "processed_files": 10}
        })

        estimate = await manager.calculate_estimated_completion()
        assert estimate is not None
        # Should be roughly now + 90s
        diff = (estimate - now).total_seconds()
        assert 80 < diff < 100

    def test_sync_methods(self):
        """Test synchronous methods coverage."""
        manager = IndexingStateManager()

        manager.set_value_sync("test_key", "test_val")
        state = manager.get_state_sync()
        assert state["test_key"] == "test_val"

        manager.reset_state_sync()
        state = manager.get_state_sync()
        assert state["status"] == "idle"
        assert "test_key" not in state


class TestValidateThumbnailCache:
    """Tests for validate_thumbnail_cache endpoint."""

    @pytest.mark.asyncio
    async def test_validate_thumbnail_cache_success(self):
        """Test successful validation."""

        mock_stats = {"total_size_mb": 500}
        mock_validation = {
            "total_checked": 100,
            "valid_files": 95,
            "invalid_files": 5,
            "missing_files": 0
        }

        mock_manager = MagicMock()
        mock_manager.get_cache_statistics = AsyncMock(return_value=mock_stats)
        mock_manager.validate_cache_integrity = AsyncMock(return_value=mock_validation)

        with patch.dict("sys.modules", {
            "src.workers.thumbnail_worker": MagicMock(ThumbnailCacheManager=MagicMock(return_value=mock_manager))
        }):
            # We also need to patch settings
            with patch("src.core.config.settings") as mock_settings:
                mock_settings.THUMBNAIL_DIR = "/tmp/thumbnails"

                result = await validate_thumbnail_cache(sample_size=50)

                assert result["health"]["score"] == 95.0
                assert result["health"]["status"] == "healthy"
                assert "recommendations" in result
                assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_validate_thumbnail_cache_exception(self):
        """Test validation failure."""
        with patch("src.core.config.settings"):
            with patch.dict("sys.modules", {
                "src.workers.thumbnail_worker": MagicMock(side_effect=Exception("Import Error"))
            }):
                with pytest.raises(HTTPException) as exc:
                    await validate_thumbnail_cache()
                assert exc.value.status_code == 500


class TestModelDiagnostics:
    """Tests for get_model_diagnostics endpoint."""

    @pytest.mark.asyncio
    async def test_get_model_diagnostics_all_available(self):
        """Test diagnostics when all models are available."""

        mock_clip = MagicMock()
        mock_clip.model_name = "TestCLIP"

        mock_face = MagicMock()
        mock_face.is_available.return_value = True

        modules = {
            "src.workers.embedding_worker": MagicMock(OptimizedCLIPWorker=MagicMock(return_value=mock_clip)),
            "src.workers.face_worker": MagicMock(FaceDetectionWorker=MagicMock(return_value=mock_face)),
            "src.workers.exif_extractor": MagicMock(EXIFExtractionPipeline=MagicMock()),
            "src.workers.thumbnail_worker": MagicMock(SmartThumbnailGenerator=MagicMock()),
        }

        with patch.dict("sys.modules", modules):
            result = await get_model_diagnostics()

            assert result["models"]["clip"]["available"] is True
            assert result["models"]["face_detection"]["available"] is True
            assert result["overall_status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_model_diagnostics_partial_failure(self):
        """Test diagnostics with failures."""

        # Mock CLIP failure
        mock_clip_class = MagicMock(side_effect=Exception("CLIP Missing"))

        # To fail import of EXIFExtractionPipeline, we need to make attribute access raise
        mock_exif_module = MagicMock()
        type(mock_exif_module).EXIFExtractionPipeline = property(lambda _s: (_ for _ in ()).throw(ImportError("Exif Fail")))

        modules = {
            "src.workers.embedding_worker": MagicMock(OptimizedCLIPWorker=mock_clip_class),
            "src.workers.face_worker": MagicMock(FaceDetectionWorker=MagicMock(return_value=MagicMock(is_available=lambda: False))),
            "src.workers.exif_extractor": mock_exif_module,
            "src.workers.thumbnail_worker": MagicMock(SmartThumbnailGenerator=MagicMock()),
        }

        with patch.dict("sys.modules", modules):
            result = await get_model_diagnostics()

            assert result["models"]["clip"]["available"] is False
            assert result["models"]["face_detection"]["available"] is False
            assert result["dependencies"]["exif"]["available"] is False
            assert result["dependencies"]["thumbnails"]["available"] is True
            assert result["overall_status"] == "degraded"


class TestInternalHelpers:
    """Tests for internal helper functions."""

    @pytest.mark.asyncio
    async def test_monitor_indexing_task_exception(self):
        """Test monitoring task handles exceptions."""
        task = AsyncMock()
        task.__await__ = MagicMock(side_effect=Exception("Task Error"))

        from src.api import indexing
        # Mock global state manager
        with patch("src.api.indexing._state_manager") as mock_manager:
            # Ensure async methods are AsyncMock
            mock_manager.update_state = AsyncMock()
            mock_manager.append_error = AsyncMock()
            mock_manager.set_value = AsyncMock()
            mock_manager.get_value = AsyncMock(return_value=task) # for current_task check

            # Create a real coroutine that raises
            async def raising_coro():
                raise Exception("Task Failed")

            await _monitor_indexing_task(raising_coro())

            mock_manager.update_state.assert_called_with({"status": "error", "task": None})
            mock_manager.append_error.assert_called()


class TestIndexingProcessCoverage:
    """Tests for indexing process logic."""

    @pytest.mark.asyncio
    async def test_run_processing_phases_e2e_mode(self):
        """Test processing phases skip heavy tasks in E2E mode."""
        from src.api import indexing

        # We need EXIF worker even in E2E mode
        mock_exif_worker = MagicMock()
        mock_exif_worker.process_photos = AsyncMock(return_value=[])

        workers = {
            "EXIFExtractionPipeline": MagicMock(return_value=mock_exif_worker)
        }

        with patch("src.api.indexing._is_e2e_test_mode", return_value=True):
            with patch("src.api.indexing._check_cancellation", new_callable=AsyncMock):
                with patch("src.api.indexing.asyncio.sleep", new_callable=AsyncMock):
                    with patch("src.api.indexing._state_manager") as mock_manager:
                        mock_manager.update_progress = AsyncMock()
                        mock_manager.get_value = AsyncMock(return_value="indexing")

                        await indexing._run_processing_phases(
                            workers=workers,
                            config={},
                            photos_to_process=[MagicMock()] * 10
                        )

                        # Should mark completed immediately after EXIF
                        mock_manager.update_progress.assert_called_with(
                            current_phase="completed", processed_files=10
                        )

    @pytest.mark.asyncio
    async def test_run_processing_phases_embedding_failure(self):
        """Test processing continues if embeddings fail."""
        from src.api import indexing

        mock_embedding_worker = MagicMock()
        mock_embedding_worker.generate_batch_optimized = AsyncMock(side_effect=Exception("Embed Error"))

        workers = {
            "EXIFExtractionPipeline": MagicMock(return_value=MagicMock(process_photos=AsyncMock(return_value=[]))),
            "OptimizedCLIPWorker": MagicMock(return_value=mock_embedding_worker),
            "SmartThumbnailGenerator": MagicMock(return_value=MagicMock(generate_batch=AsyncMock(return_value=[]))),
            "FaceDetectionWorker": MagicMock(),
        }

        with patch("src.api.indexing._check_cancellation", new_callable=AsyncMock):
            with patch("src.api.indexing._state_manager") as mock_manager:
                mock_manager.update_progress = AsyncMock()
                mock_manager.append_error = AsyncMock()

                # Patch sleep to speed up test
                with patch("src.api.indexing.asyncio.sleep", new_callable=AsyncMock):
                    await indexing._run_processing_phases(
                        workers,
                        config={"face_search_enabled": False},
                        photos_to_process=[MagicMock()]
                    )

                mock_manager.append_error.assert_called()
                assert "Embedding generation failed" in str(mock_manager.append_error.call_args)

    @pytest.mark.asyncio
    async def test_run_indexing_process_db_update_error(self):
        """Test error handling during DB update in indexing process."""
        from src.api import indexing

        mock_db = MagicMock()
        # Fail on execute_update when marking photos as indexed
        mock_db.execute_update.side_effect = Exception("DB Update Error")

        with patch("src.api.indexing.get_database_manager", return_value=mock_db):
            with patch("src.api.indexing._setup_indexing_workers", new_callable=AsyncMock) as mock_setup:
                mock_setup.return_value = {}

                with patch("src.api.indexing._get_config_from_db", return_value={"roots": ["/tmp"]}):
                    with patch("pathlib.Path.exists", return_value=True):
                        with patch("src.api.indexing._run_discovery_phase", new_callable=AsyncMock):
                            with patch("src.api.indexing._get_photos_for_processing", return_value=[MagicMock(id=1)]):
                                with patch("src.api.indexing._run_processing_phases", new_callable=AsyncMock):
                                    with patch("src.api.indexing._state_manager") as mock_manager:
                                        mock_manager.append_error = AsyncMock()
                                        mock_manager.set_value = AsyncMock()
                                        mock_manager.update_state = AsyncMock()

                                        await indexing._run_indexing_process(full_reindex=False)

                                        mock_manager.set_value.assert_called_with("status", "error")
                                        mock_manager.append_error.assert_called()

    @pytest.mark.asyncio
    async def test_check_cancellation(self):
        """Test _check_cancellation raises if status is stopped."""
        from src.api import indexing
        with patch("src.api.indexing._state_manager") as mock_manager:
            mock_manager.get_value = AsyncMock(return_value="stopped")

            with pytest.raises(asyncio.CancelledError):
                await _check_cancellation()

    @pytest.mark.asyncio
    async def test_check_cancellation_continue(self):
        """Test _check_cancellation continues if indexing."""
        from src.api import indexing
        with patch("src.api.indexing._state_manager") as mock_manager:
            mock_manager.get_value = AsyncMock(return_value="indexing")
            await _check_cancellation() # Should not raise



# === Merged from test_indexing_internals.py ===


class TestIndexingStateManagerInternal:
    """Test IndexingStateManager logic."""

    @pytest.mark.asyncio
    async def test_extend_errors(self):
        manager = IndexingStateManager()
        await manager.extend_errors(["e1", "e2"])
        state = await manager.get_state()
        assert state["errors"] == ["e1", "e2"]

    @pytest.mark.asyncio
    async def test_calculate_estimated_completion_none(self):
        manager = IndexingStateManager()
        # Not started
        assert await manager.calculate_estimated_completion() is None

        # Started but 0 total files
        await manager.update_state({"started_at": datetime.now(), "progress": {"total_files": 0}})
        assert await manager.calculate_estimated_completion() is None

        # Started, total > 0, but processed 0
        await manager.update_state({"progress": {"total_files": 100, "processed_files": 0}})
        assert await manager.calculate_estimated_completion() is None

    @pytest.mark.asyncio
    async def test_calculate_estimated_completion_valid(self):
        manager = IndexingStateManager()
        started = datetime.now() - timedelta(seconds=10)
        await manager.update_state({
            "started_at": started,
            "progress": {"total_files": 100, "processed_files": 50}
        })
        # 50 files in 10s = 5 files/s. Remaining 50 files = 10s.
        est = await manager.calculate_estimated_completion()
        assert est is not None
        assert est > datetime.now()

    def test_sync_methods(self):
        manager = IndexingStateManager()
        manager.set_value_sync("status", "test")
        assert manager.get_state_sync()["status"] == "test"

        manager.reset_state_sync()
        assert manager.get_state_sync()["status"] == "idle"


class TestIndexingEndpointsErrors:
    """Test endpoint error handling."""

    @pytest.mark.asyncio
    async def test_start_indexing_exception(self):
        # Mock something inside the try block
        with patch("src.api.indexing._state_manager.reset_for_new_indexing", side_effect=Exception("Boom")):
            with pytest.raises(HTTPException) as exc:
                await start_indexing(MagicMock())
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_stop_indexing_exception(self):
        # Mock is_indexing to return True so we pass the first check
        with patch("src.api.indexing._state_manager.is_indexing", return_value=True):
             with patch("src.api.indexing._state_manager.get_value", side_effect=Exception("Boom")):
                with pytest.raises(HTTPException) as exc:
                    await stop_indexing()
                assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_indexing_statistics_exception(self):
         with patch("src.api.indexing.get_database_manager", side_effect=Exception("Boom")):
             with pytest.raises(HTTPException) as exc:
                 await get_indexing_statistics()
             assert exc.value.status_code == 500

class TestThumbnailValidation:
    """Test thumbnail validation logic."""

    @pytest.mark.asyncio
    async def test_validate_cache_exception(self):
         with patch("src.api.indexing.settings", side_effect=Exception("Boom")):
             with pytest.raises(HTTPException) as exc:
                 await validate_thumbnail_cache()
             assert exc.value.status_code == 500

    def test_cache_recommendations(self):
        # Empty
        assert "healthy" in _get_cache_recommendations({"invalid_files": 0, "total_checked": 100}, {})[0]

        # Invalid files
        recs = _get_cache_recommendations({"invalid_files": 10, "total_checked": 100}, {})
        assert any("corrupted" in r for r in recs)
        assert any("High invalid" in r for r in recs) # 10% > 5%

        # Large cache
        recs = _get_cache_recommendations({"invalid_files": 0, "total_checked": 100}, {"total_size_mb": 2000})
        assert any("exceeds 1GB" in r for r in recs)

class TestDiagnosticsErrors:
    """Test diagnostics error handling."""

    @pytest.mark.asyncio
    async def test_diagnostics_all_fail(self):
        # Create a mock module that does NOT have the classes
        bad_module = MagicMock(spec=[])

        # When checking for import, we need to ensure the attribute is missing
        # from module. class import -> getattr(module, class_name)

        with patch.dict("sys.modules", {
            "src.workers.exif_extractor": bad_module,
            "src.workers.thumbnail_worker": bad_module,
        }):
             with patch("src.workers.embedding_worker.OptimizedCLIPWorker", side_effect=Exception("CLIP Fail")):
                 with patch("src.workers.face_worker.FaceDetectionWorker", side_effect=Exception("Face Fail")):
                     diag = await get_model_diagnostics()
                     assert diag["models"]["clip"]["status"] == "failed"
                     assert diag["models"]["face_detection"]["status"] == "failed"
                     assert diag["dependencies"]["exif"]["status"] == "failed"
                     assert diag["dependencies"]["thumbnails"]["status"] == "failed"


class TestInternalProcesses:
    """Test internal process functions."""

    @pytest.mark.asyncio
    async def test_monitor_indexing_task_exception(self):
        async def failing_task():
            raise Exception("Task Failed")

        task = asyncio.create_task(failing_task())

        await _monitor_indexing_task(task)
        state = await _state_manager.get_state()
        assert state["status"] == "error"
        # The error might be wrapped or just the string
        assert any("Task Failed" in str(e) for e in state["errors"])

    @pytest.mark.asyncio
    async def test_get_indexed_photo_count_error(self):
        mock_db = MagicMock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        assert _get_indexed_photo_count(mock_db) == 0

    @pytest.mark.asyncio
    async def test_run_discovery_phase_errors(self):
        workers = {"FileCrawler": MagicMock()}
        crawler = workers["FileCrawler"].return_value

        # Simulate crawl result with errors
        result = MagicMock()
        result.total_files = 10
        result.errors = 1
        result.error_details = ["Crawl Error"]
        result.files = [{"status": "new", "photo": MagicMock(), "path": "p1"}]

        # Make crawl_all_paths async
        crawler.crawl_all_paths = AsyncMock(return_value=result)

        # Mock DB to fail on insert
        with patch("src.api.indexing.get_database_manager") as mock_db_mgr:
            mock_db_mgr.return_value.execute_update.side_effect = Exception("Insert Fail")

            await _run_discovery_phase(workers, {"roots": ["/"]}, full_reindex=False)

            # Should have logged error but not crashed
            # Check state errors were extended
            state = await _state_manager.get_state()
            assert "Crawl Error" in state["errors"]

    @pytest.mark.asyncio
    async def test_run_processing_phases_errors(self):
        workers = {
            "EXIFExtractionPipeline": MagicMock(),
            "OptimizedCLIPWorker": MagicMock(),
            "SmartThumbnailGenerator": MagicMock(),
            "FaceDetectionWorker": MagicMock()
        }

        # EXIF Error
        workers["EXIFExtractionPipeline"].return_value.process_photos = AsyncMock(side_effect=Exception("EXIF Fail"))

        # Mock others to succeed or fail
        workers["OptimizedCLIPWorker"].return_value.generate_batch_optimized = AsyncMock(side_effect=Exception("CLIP Fail"))
        workers["SmartThumbnailGenerator"].return_value.generate_batch = AsyncMock(side_effect=Exception("Thumb Fail"))

        face_worker = workers["FaceDetectionWorker"].return_value
        face_worker.is_available.return_value = True
        face_worker.process_batch = AsyncMock(side_effect=Exception("Face Fail"))

        # Mock E2E check
        with patch("src.api.indexing._is_e2e_test_mode", return_value=False):
            with patch("src.api.indexing.get_database_manager"):
                photos = [MagicMock()]

                # Expect exception because thumbnail generation crashes
                with pytest.raises(Exception, match="Thumb Fail"):
                    await _run_processing_phases(workers, {"face_search_enabled": True}, photos)

                # Check that previous errors were recorded
                state = await _state_manager.get_state()
                errors = state["errors"]
                # EXIF error is caught and logged to state
                assert any("EXIF extraction failed" in e for e in errors)
                # CLIP error is caught and logged to state
                assert any("Embedding generation failed" in e for e in errors)

    @pytest.mark.asyncio
    async def test_run_indexing_process_no_roots(self):
        with patch("src.api.indexing._setup_indexing_workers"):
            with patch("src.api.indexing.get_database_manager"):
                with patch("src.api.indexing._get_config_from_db", return_value={"roots": []}):
                     await _run_indexing_process(full_reindex=False)
                     state = await _state_manager.get_state()
                     assert "No root paths configured" in state["errors"]
                     assert state["status"] == "error"

    @pytest.mark.asyncio
    async def test_run_indexing_process_invalid_roots(self):
        with patch("src.api.indexing._setup_indexing_workers"):
            with patch("src.api.indexing.get_database_manager"):
                with patch("src.api.indexing._get_config_from_db", return_value={"roots": ["/invalid"]}):
                     with patch("pathlib.Path.exists", return_value=False):
                        await _run_indexing_process(full_reindex=False)
                        state = await _state_manager.get_state()
                        assert any("Root path does not exist" in e for e in state["errors"])
                        # It should complete with no work
                        assert "No valid root paths found" in state["errors"][-1]


class TestMonitorIndexingTaskCancellation:
    """Tests for _monitor_indexing_task cancellation path."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset state before each test."""
        from src.api import indexing

        indexing._indexing_state.clear()
        indexing._indexing_state.update({
            "status": "indexing",
            "progress": {"total_files": 0, "processed_files": 0, "current_phase": "discovery"},
            "errors": [],
            "started_at": None,
            "estimated_completion": None,
            "task": None,
            "last_completed_at": None,
            "request_count": 0,
        })
        yield

    @pytest.mark.asyncio
    async def test_monitor_task_cancelled(self):
        """Test monitor task handles CancelledError."""
        async def cancelled_task():
            raise asyncio.CancelledError

        task = asyncio.create_task(cancelled_task())
        await _state_manager.set_value("task", task)

        await _monitor_indexing_task(task)

        state = await _state_manager.get_state()
        assert state["status"] == "stopped"
        assert state["task"] is None

    @pytest.mark.asyncio
    async def test_monitor_task_finally_clears_task(self):
        """Test monitor task clears task in finally block."""
        async def successful_task():
            pass

        task = asyncio.create_task(successful_task())
        await _state_manager.set_value("task", task)

        await _monitor_indexing_task(task)

        state = await _state_manager.get_state()
        # Task should be cleared in finally block
        assert state["task"] is None


class TestProcessingPhasesDBSave:
    """Tests for database save operations in processing phases."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset state before each test."""
        from src.api import indexing

        indexing._indexing_state.clear()
        indexing._indexing_state.update({
            "status": "indexing",
            "progress": {"total_files": 0, "processed_files": 0, "current_phase": "discovery"},
            "errors": [],
            "started_at": None,
            "estimated_completion": None,
            "task": None,
            "last_completed_at": None,
            "request_count": 0,
        })
        yield

    @pytest.mark.asyncio
    async def test_exif_save_with_all_attributes(self):
        """Test EXIF extraction is called with all attributes present."""
        from src.api.indexing import _run_processing_phases

        mock_exif_data = MagicMock()
        mock_exif_data.shot_dt = "2024-01-01"
        mock_exif_data.camera_make = "Canon"
        mock_exif_data.camera_model = "EOS R5"
        mock_exif_data.lens = "RF 24-70mm"
        mock_exif_data.iso = 100
        mock_exif_data.aperture = 2.8
        mock_exif_data.shutter_speed = "1/250"
        mock_exif_data.focal_length = 50
        mock_exif_data.gps_lat = 40.7128
        mock_exif_data.gps_lon = -74.0060
        mock_exif_data.orientation = 1

        mock_exif_result = {
            "extraction_successful": True,
            "photo_id": 1,
            "exif_data": mock_exif_data,
        }

        mock_photo = MagicMock()
        mock_photo.id = 1

        mock_exif_pipeline = MagicMock()
        mock_exif_pipeline.process_photos = AsyncMock(return_value=[mock_exif_result])

        mock_workers = {
            "EXIFExtractionPipeline": MagicMock(return_value=mock_exif_pipeline),
            "OptimizedCLIPWorker": MagicMock(return_value=MagicMock(
                generate_batch_optimized=AsyncMock(return_value=[])
            )),
            "SmartThumbnailGenerator": MagicMock(return_value=MagicMock(
                generate_batch=AsyncMock(return_value=[])
            )),
            "FaceDetectionWorker": MagicMock(return_value=MagicMock(
                is_available=MagicMock(return_value=False)
            )),
        }

        mock_db = MagicMock()

        with patch("src.api.indexing.get_database_manager", return_value=mock_db):
            with patch("src.api.indexing._is_e2e_test_mode", return_value=True):
                await _run_processing_phases(
                    mock_workers,
                    {"face_search_enabled": False},
                    [mock_photo]
                )

        # Verify EXIF pipeline was called
        mock_exif_pipeline.process_photos.assert_called_once()

    @pytest.mark.asyncio
    async def test_face_detection_worker_not_available(self):
        """Test face detection when worker is not available."""
        from src.api.indexing import _run_processing_phases

        mock_photo = MagicMock()
        mock_photo.id = 1

        mock_face_worker = MagicMock()
        mock_face_worker.is_available.return_value = False

        mock_workers = {
            "EXIFExtractionPipeline": MagicMock(return_value=MagicMock(
                process_photos=AsyncMock(return_value=[])
            )),
            "OptimizedCLIPWorker": MagicMock(return_value=MagicMock(
                generate_batch_optimized=AsyncMock(return_value=[])
            )),
            "SmartThumbnailGenerator": MagicMock(return_value=MagicMock(
                generate_batch=AsyncMock(return_value=[])
            )),
            "FaceDetectionWorker": MagicMock(return_value=mock_face_worker),
        }

        mock_db = MagicMock()

        with patch("src.api.indexing.get_database_manager", return_value=mock_db):
            with patch("src.api.indexing._is_e2e_test_mode", return_value=False):
                await _run_processing_phases(
                    mock_workers,
                    {"face_search_enabled": True},
                    [mock_photo]
                )

        # Should have logged error about face detection not available
        state = await _state_manager.get_state()
        assert any("Face detection model not available" in e for e in state["errors"])


class TestRunIndexingProcessMarkIndexed:
    """Tests for marking photos as indexed."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset state before each test."""
        from src.api import indexing

        indexing._indexing_state.clear()
        indexing._indexing_state.update({
            "status": "idle",
            "progress": {"total_files": 0, "processed_files": 0, "current_phase": "discovery"},
            "errors": [],
            "started_at": None,
            "estimated_completion": None,
            "task": None,
            "last_completed_at": None,
            "request_count": 0,
        })
        yield

    @pytest.mark.asyncio
    async def test_mark_photos_as_indexed(self):
        """Test that photos are marked as indexed after processing."""
        mock_photo = MagicMock()
        mock_photo.id = 1

        mock_db = MagicMock()
        mock_db.execute_query.return_value = []

        mock_crawl_result = MagicMock()
        mock_crawl_result.total_files = 1
        mock_crawl_result.errors = 0
        mock_crawl_result.error_details = []
        mock_crawl_result.files = []

        mock_crawler = MagicMock()
        mock_crawler.crawl_all_paths = AsyncMock(return_value=mock_crawl_result)

        mock_workers = {
            "FileCrawler": MagicMock(return_value=mock_crawler),
            "EXIFExtractionPipeline": MagicMock(return_value=MagicMock(
                process_photos=AsyncMock(return_value=[])
            )),
            "OptimizedCLIPWorker": MagicMock(return_value=MagicMock(
                generate_batch_optimized=AsyncMock(return_value=[])
            )),
            "SmartThumbnailGenerator": MagicMock(return_value=MagicMock(
                generate_batch=AsyncMock(return_value=[])
            )),
            "FaceDetectionWorker": MagicMock(return_value=MagicMock(
                is_available=MagicMock(return_value=False)
            )),
        }

        with patch("src.api.indexing._setup_indexing_workers", return_value=mock_workers):
            with patch("src.api.indexing.get_database_manager", return_value=mock_db):
                with patch("src.api.indexing._get_config_from_db", return_value={"roots": ["/valid"]}):
                    with patch("pathlib.Path.exists", return_value=True):
                        with patch("src.api.indexing._get_photos_for_processing", return_value=[mock_photo]):
                            with patch("src.api.indexing._run_discovery_phase"):
                                with patch("src.api.indexing._run_processing_phases"):
                                    await _run_indexing_process(full_reindex=False)

        # Verify UPDATE was called to mark photos as indexed
        calls = [str(c) for c in mock_db.execute_update.call_args_list]
        assert any("indexed_at" in str(c) for c in calls)


