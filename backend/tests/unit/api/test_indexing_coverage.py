"""Additional coverage tests for backend/src/api/indexing.py."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.indexing import (
    IndexingStateManager,
    _check_cancellation,
    _monitor_indexing_task,
    get_model_diagnostics,
    validate_thumbnail_cache,
)


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

