"""Unit tests for internal indexing logic."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.indexing import (
    IndexingStateManager,
    StartIndexRequest,
    _get_cache_recommendations,
    _get_indexed_photo_count,
    _monitor_indexing_task,
    _run_discovery_phase,
    _run_indexing_process,
    _run_processing_phases,
    _state_manager,
    get_indexing_statistics,
    get_model_diagnostics,
    start_indexing,
    stop_indexing,
    validate_thumbnail_cache,
)


class TestIndexingStateManager:
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


