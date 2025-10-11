"""Unit tests for FAISSIndexManager service."""

import asyncio
import json
import os
import shutil
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, call, mock_open, patch

import numpy as np
import pytest

from src.services.faiss_manager import FAISSIndexManager


class TestFAISSIndexManagerInitialization:
    """Test FAISSIndexManager initialization."""

    @patch("src.services.faiss_manager.get_settings")
    def test_initialization(self, mock_get_settings):
        """Test FAISSIndexManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()

                    assert manager.base_path == Path(temp_dir) / "faiss"
                    assert (
                        manager.index_path == Path(temp_dir) / "faiss" / "index.faiss"
                    )
                    assert (
                        manager.metadata_path
                        == Path(temp_dir) / "faiss" / "metadata.json"
                    )
                    assert manager.backup_path == Path(temp_dir) / "faiss" / "backups"
                    assert manager.stats_path == Path(temp_dir) / "faiss" / "stats.json"
                    assert isinstance(manager._lock, type(threading.RLock()))
                    assert manager._optimization_in_progress is False
                    assert isinstance(manager._background_tasks, set)

    @patch("src.services.faiss_manager.get_settings")
    def test_initialization_with_vector_service(self, mock_get_settings):
        """Test initialization with vector search service."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_vector_service = Mock()

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                assert manager.vector_service == mock_vector_service

    @patch("src.services.faiss_manager.get_settings")
    def test_initialization_creates_directories(self, mock_get_settings):
        """Test that initialization creates required directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()

                    assert manager.base_path.exists()
                    assert manager.backup_path.exists()


class TestStatsManagement:
    """Test statistics loading and saving."""

    @patch("src.services.faiss_manager.get_settings")
    def test_load_stats_existing_file(self, mock_get_settings):
        """Test loading statistics from existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            # Create stats file
            stats_data = {
                "last_optimization": "2024-01-01T12:00:00",
                "last_backup": "2024-01-01T13:00:00",
                "total_vectors": 1000,
                "search_count": 50,
                "average_search_time": 0.5,
            }

            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()
                manager.stats_path.parent.mkdir(parents=True, exist_ok=True)

                with open(manager.stats_path, "w") as f:
                    json.dump(stats_data, f)

                manager._load_stats()

                assert manager.stats["last_optimization"] == "2024-01-01T12:00:00"
                assert manager.stats["total_vectors"] == 1000

    @patch("src.services.faiss_manager.get_settings")
    def test_load_stats_nonexistent_file(self, mock_get_settings):
        """Test loading statistics when file doesn't exist."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_start_background_scheduler"):
            manager = FAISSIndexManager()

            # Should not raise exception
            manager._load_stats()

    @patch("src.services.faiss_manager.get_settings")
    def test_load_stats_error_handling(self, mock_get_settings):
        """Test error handling when loading stats fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()
                manager.stats_path.parent.mkdir(parents=True, exist_ok=True)

                # Create invalid JSON file
                with open(manager.stats_path, "w") as f:
                    f.write("invalid json")

                # Should not raise exception
                manager._load_stats()

    @patch("src.services.faiss_manager.get_settings")
    def test_save_stats(self, mock_get_settings):
        """Test saving statistics to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()

                    manager.stats["total_vectors"] = 1500
                    manager.stats["search_count"] = 75

                    manager._save_stats()

                    assert manager.stats_path.exists()
                    with open(manager.stats_path) as f:
                        saved_stats = json.load(f)
                        assert saved_stats["total_vectors"] == 1500
                        assert saved_stats["search_count"] == 75

    @patch("src.services.faiss_manager.get_settings")
    def test_save_stats_with_vector_service(self, mock_get_settings):
        """Test saving stats when vector service has index."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            mock_index = Mock()
            mock_index.ntotal = 2000

            mock_vector_service = Mock()
            mock_vector_service.index = mock_index

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    # Create index file for size calculation
                    manager.index_path.parent.mkdir(parents=True, exist_ok=True)
                    manager.index_path.write_bytes(b"x" * 1024 * 1024)  # 1MB

                    manager._save_stats()

                    assert manager.stats["total_vectors"] == 2000
                    assert manager.stats["index_size_mb"] == 1.0

    @patch("src.services.faiss_manager.get_settings")
    def test_save_stats_error_handling(self, mock_get_settings):
        """Test error handling when saving stats fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()

                    # Make stats_path unwritable to trigger exception
                    with patch("builtins.open", side_effect=Exception("Write error")):
                        # Should not raise exception
                        manager._save_stats()


class TestOptimizationDecision:
    """Test optimization decision logic."""

    @patch("src.services.faiss_manager.get_settings")
    def test_should_optimize_no_index(self, mock_get_settings):
        """Test should_optimize when no index exists."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                assert manager.should_optimize() is False

    @patch("src.services.faiss_manager.get_settings")
    def test_should_optimize_below_threshold(self, mock_get_settings):
        """Test should_optimize when below threshold."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 1000  # Below 50000 threshold

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                assert manager.should_optimize() is False

    @patch("src.services.faiss_manager.get_settings")
    def test_should_optimize_above_threshold_no_previous_optimization(
        self, mock_get_settings
    ):
        """Test should_optimize when above threshold with no previous optimization."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 60000  # Above threshold

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                assert manager.should_optimize() is True

    @patch("src.services.faiss_manager.get_settings")
    def test_should_optimize_recent_optimization(self, mock_get_settings):
        """Test should_optimize when recently optimized."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 60000

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                # Set recent optimization
                manager.stats["last_optimization"] = datetime.now().isoformat()

                assert manager.should_optimize() is False

    @patch("src.services.faiss_manager.get_settings")
    def test_should_optimize_old_optimization(self, mock_get_settings):
        """Test should_optimize when optimization is old enough."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 60000

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                # Set old optimization (5 hours ago)
                old_time = datetime.now() - timedelta(hours=5)
                manager.stats["last_optimization"] = old_time.isoformat()

                assert manager.should_optimize() is True

    @patch("src.services.faiss_manager.get_settings")
    def test_should_optimize_in_progress(self, mock_get_settings):
        """Test should_optimize when optimization is in progress."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 60000

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                manager._optimization_in_progress = True

                assert manager.should_optimize() is False

    @patch("src.services.faiss_manager.get_settings")
    def test_should_optimize_invalid_datetime(self, mock_get_settings):
        """Test should_optimize when last_optimization datetime is invalid."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 60000

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                # Set invalid datetime string
                manager.stats["last_optimization"] = "invalid-datetime"

                # Should return True when datetime parsing fails
                assert manager.should_optimize() is True


class TestIndexOptimization:
    """Test index optimization functionality."""

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_optimize_index_not_needed(self, mock_get_settings):
        """Test optimize_index when optimization not needed."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                with patch.object(manager, "should_optimize", return_value=False):
                    result = await manager.optimize_index(force=False)

                    assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_optimize_index_forced(self, mock_get_settings):
        """Test forced optimization."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 1000
        mock_index.d = 512

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                with patch.object(manager, "_perform_optimization") as mock_perform:
                    mock_perform.return_value = True

                    result = await manager.optimize_index(force=True)

                    assert result is True
                    mock_perform.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_optimize_index_already_in_progress(self, mock_get_settings):
        """Test optimization when already in progress."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                manager._optimization_in_progress = True

                result = await manager.optimize_index(force=True)

                assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_perform_optimization_small_collection(self, mock_get_settings):
        """Test optimization for small collection."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        # Mock FAISS index
        mock_index = Mock()
        mock_index.ntotal = 5000  # Small collection
        mock_index.d = 512
        mock_index.reconstruct_n.return_value = np.random.rand(5000, 512).astype(
            np.float32
        )

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index
        mock_vector_service.save_index.return_value = True

        # Mock optimized index
        mock_optimized_index = Mock()
        mock_optimized_index.ntotal = 5000

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                with patch.object(manager, "create_backup") as mock_backup:
                    mock_backup.return_value = True
                    with patch.object(
                        manager,
                        "_optimize_flat_index",
                        return_value=mock_optimized_index,
                    ):
                        result = await manager._perform_optimization()

                        assert result is True
                        assert manager.vector_service.index == mock_optimized_index

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_perform_optimization_medium_collection(self, mock_get_settings):
        """Test optimization for medium collection."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 50000  # Medium collection
        mock_index.d = 512

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index
        mock_vector_service.save_index.return_value = True

        mock_optimized_index = Mock()

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                with patch.object(manager, "create_backup") as mock_backup:
                    mock_backup.return_value = True
                    with patch.object(
                        manager, "_create_ivf_index", return_value=mock_optimized_index
                    ):
                        result = await manager._perform_optimization()

                        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_perform_optimization_large_collection(self, mock_get_settings):
        """Test optimization for large collection."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 250000  # Large collection
        mock_index.d = 512

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index
        mock_vector_service.save_index.return_value = True

        mock_optimized_index = Mock()

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                with patch.object(manager, "create_backup") as mock_backup:
                    mock_backup.return_value = True
                    with patch.object(
                        manager, "_create_ivf_index", return_value=mock_optimized_index
                    ) as mock_create_ivf:
                        result = await manager._perform_optimization()

                        assert result is True
                        # Should call with use_pq=True for large collections
                        mock_create_ivf.assert_called_once_with(mock_index, use_pq=True)

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_perform_optimization_no_vectors(self, mock_get_settings):
        """Test optimization when index has no vectors."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 0

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                result = await manager._perform_optimization()

                assert result is False


class TestIndexOptimizationMethods:
    """Test specific index optimization methods."""

    @patch("src.services.faiss_manager.get_settings")
    def test_optimize_flat_index(self, mock_get_settings):
        """Test flat index optimization."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        # Mock original index
        mock_index = Mock()
        mock_index.ntotal = 1000
        mock_index.d = 512
        mock_index.reconstruct_n.return_value = np.random.rand(1000, 512).astype(
            np.float32
        )

        # Mock new index
        mock_new_index = Mock()

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                # Patch faiss within the method
                with patch("builtins.__import__") as mock_import:
                    mock_faiss = Mock()
                    mock_faiss.IndexFlatIP.return_value = mock_new_index

                    def import_side_effect(name, *args, **kwargs):
                        if name == "faiss":
                            return mock_faiss
                        return __import__(name, *args, **kwargs)

                    mock_import.side_effect = import_side_effect

                    result = manager._optimize_flat_index(mock_index)

                    assert result == mock_new_index
                    mock_faiss.IndexFlatIP.assert_called_once_with(512)

    @patch("src.services.faiss_manager.get_settings")
    def test_optimize_flat_index_non_clip(self, mock_get_settings):
        """Test flat index optimization for non-CLIP embeddings."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 1000
        mock_index.d = 256  # Not CLIP (512)
        mock_index.reconstruct_n.return_value = np.random.rand(1000, 256).astype(
            np.float32
        )

        mock_new_index = Mock()

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                # Patch faiss at the import level
                with patch("builtins.__import__") as mock_import:
                    mock_faiss = Mock()
                    mock_faiss.IndexFlatL2.return_value = mock_new_index

                    def import_side_effect(name, *args, **kwargs):
                        if name == "faiss":
                            return mock_faiss
                        return __import__(name, *args, **kwargs)

                    mock_import.side_effect = import_side_effect

                    result = manager._optimize_flat_index(mock_index)

                    assert result == mock_new_index
                    mock_faiss.IndexFlatL2.assert_called_once_with(256)

    @patch("src.services.faiss_manager.faiss")
    @patch("src.services.faiss_manager.get_settings")
    def test_create_ivf_index_without_pq(self, mock_get_settings, mock_faiss):
        """Test IVF index creation without product quantization."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 50000
        mock_index.d = 512
        vectors = np.random.rand(50000, 512).astype(np.float32)
        mock_index.reconstruct_n.return_value = vectors

        mock_quantizer = Mock()
        mock_faiss.IndexFlatIP.return_value = mock_quantizer

        mock_ivf_index = Mock()
        mock_faiss.IndexIVFFlat.return_value = mock_ivf_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                result = manager._create_ivf_index(mock_index, use_pq=False)

                assert result == mock_ivf_index
                mock_ivf_index.train.assert_called_once()
                mock_ivf_index.add.assert_called()

    @patch("src.services.faiss_manager.faiss")
    @patch("src.services.faiss_manager.get_settings")
    def test_create_ivf_index_with_pq(self, mock_get_settings, mock_faiss):
        """Test IVF index creation with product quantization."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 250000
        mock_index.d = 512
        vectors = np.random.rand(250000, 512).astype(np.float32)
        mock_index.reconstruct_n.return_value = vectors

        mock_quantizer = Mock()
        mock_faiss.IndexFlatIP.return_value = mock_quantizer

        mock_ivf_pq_index = Mock()
        mock_faiss.IndexIVFPQ.return_value = mock_ivf_pq_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                result = manager._create_ivf_index(mock_index, use_pq=True)

                assert result == mock_ivf_pq_index
                mock_ivf_pq_index.train.assert_called_once()

    @patch("src.services.faiss_manager.get_settings")
    def test_create_ivf_index_error_handling(self, mock_get_settings):
        """Test error handling in IVF index creation."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.reconstruct_n.side_effect = Exception("FAISS error")

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                result = manager._create_ivf_index(mock_index, use_pq=False)

                assert result is None


class TestBackupFunctionality:
    """Test backup and restore functionality."""

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_create_backup(self, mock_get_settings):
        """Test creating backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            mock_index = Mock()
            mock_index.ntotal = 1000

            mock_vector_service = Mock()
            mock_vector_service.index = mock_index
            mock_vector_service.save_index.return_value = True
            mock_vector_service.index_path = Path(temp_dir) / "index.faiss"
            mock_vector_service.metadata_path = Path(temp_dir) / "metadata.pkl"

            # Create mock files
            mock_vector_service.index_path.parent.mkdir(parents=True, exist_ok=True)
            mock_vector_service.index_path.write_bytes(b"index data")
            mock_vector_service.metadata_path.write_bytes(b"metadata")

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    with patch.object(manager, "_cleanup_old_backups") as mock_cleanup:
                        result = await manager.create_backup("test_backup")

                        assert result is True
                        backup_dir = manager.backup_path / "test_backup"
                        assert backup_dir.exists()
                        assert (backup_dir / "index.faiss").exists()
                        assert (backup_dir / "info.json").exists()
                        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_create_backup_auto_name(self, mock_get_settings):
        """Test creating backup with auto-generated name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            mock_index = Mock()
            mock_index.ntotal = 500

            mock_vector_service = Mock()
            mock_vector_service.index = mock_index
            mock_vector_service.save_index.return_value = True
            mock_vector_service.index_path = Path(temp_dir) / "index.faiss"
            mock_vector_service.metadata_path = None

            mock_vector_service.index_path.parent.mkdir(parents=True, exist_ok=True)
            mock_vector_service.index_path.write_bytes(b"data")

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    with patch.object(manager, "_cleanup_old_backups"):
                        result = await manager.create_backup()

                        assert result is True
                        # Should have created a backup with timestamp name
                        backups = list(manager.backup_path.iterdir())
                        assert len(backups) == 1

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_create_backup_no_vector_service(self, mock_get_settings):
        """Test backup creation when no vector service available."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                result = await manager.create_backup()

                assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_restore_backup(self, mock_get_settings):
        """Test restoring from backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            # Create current directory
            current_dir = Path(temp_dir) / "current"
            current_dir.mkdir(parents=True, exist_ok=True)

            mock_vector_service = Mock()
            mock_vector_service.index_path = current_dir / "index.faiss"
            mock_vector_service.metadata_path = current_dir / "metadata.pkl"
            mock_vector_service._load_index = Mock()

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    # Create backup
                    backup_dir = manager.backup_path / "test_restore"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    (backup_dir / "index.faiss").write_bytes(b"backup index")
                    (backup_dir / "metadata.pkl").write_bytes(b"backup metadata")

                    with patch.object(manager, "create_backup") as mock_backup:
                        mock_backup.return_value = True

                        result = await manager.restore_backup("test_restore")

                        assert result is True
                        # Should have created pre-restore backup
                        mock_backup.assert_called_once_with("pre_restore")
                        # Should have called _load_index
                        mock_vector_service._load_index.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_restore_backup_not_found(self, mock_get_settings):
        """Test restoring from non-existent backup."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                result = await manager.restore_backup("nonexistent")

                assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_cleanup_old_backups(self, mock_get_settings):
        """Test cleanup of old backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()
                    manager.max_backups = 3

                    # Create 5 backups
                    for i in range(5):
                        backup_dir = manager.backup_path / f"backup_{i}"
                        backup_dir.mkdir(parents=True, exist_ok=True)

                        backup_time = datetime.now() - timedelta(hours=i)
                        info = {
                            "created_at": backup_time.isoformat(),
                            "vector_count": 1000,
                        }
                        with open(backup_dir / "info.json", "w") as f:
                            json.dump(info, f)

                    await manager._cleanup_old_backups()

                    # Should only keep 3 most recent backups
                    remaining_backups = list(manager.backup_path.iterdir())
                    assert len(remaining_backups) == 3


class TestPerformanceStats:
    """Test performance statistics tracking."""

    @patch("src.services.faiss_manager.get_settings")
    def test_get_performance_stats(self, mock_get_settings):
        """Test getting performance statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            mock_index = Mock()
            mock_index.ntotal = 1500

            mock_vector_service = Mock()
            mock_vector_service.index = mock_index

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    # Create index file
                    manager.index_path.parent.mkdir(parents=True, exist_ok=True)
                    manager.index_path.write_bytes(b"x" * 2 * 1024 * 1024)  # 2MB

                    stats = manager.get_performance_stats()

                    assert stats["total_vectors"] == 1500
                    assert stats["index_size_mb"] == 2.0

    @patch("src.services.faiss_manager.get_settings")
    def test_record_search_time(self, mock_get_settings):
        """Test recording search time."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                manager.stats["search_count"] = 10
                manager.stats["average_search_time"] = 0.5

                manager.record_search_time(0.8)

                assert manager.stats["search_count"] == 11
                # Should update average (exponential moving average)
                assert manager.stats["average_search_time"] > 0.5


class TestBackgroundScheduler:
    """Test background scheduler functionality."""

    @patch("src.services.faiss_manager.get_settings")
    def test_start_background_scheduler(self, mock_get_settings):
        """Test starting background scheduler."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch("threading.Thread") as mock_thread:
                manager = FAISSIndexManager()

                mock_thread.assert_called_once()
                # Check that daemon=True was set
                call_kwargs = mock_thread.call_args[1]
                assert call_kwargs["daemon"] is True

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_shutdown(self, mock_get_settings):
        """Test graceful shutdown."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                # Add mock background task
                mock_task = AsyncMock()
                manager._background_tasks.add(mock_task)

                with patch("asyncio.gather") as mock_gather:
                    await manager.shutdown()

                    # Should call gather on background tasks
                    mock_gather.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @patch("src.services.faiss_manager.get_settings")
    def test_optimization_flag_cleanup_after_error(self, mock_get_settings):
        """Test that optimization flag is cleared after error."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 1000

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                async def run_test():
                    from contextlib import suppress

                    with patch.object(
                        manager, "_perform_optimization", side_effect=Exception("Error")
                    ):
                        with suppress(BaseException):
                            await manager.optimize_index(force=True)

                    # Flag should be cleared even after error
                    assert manager._optimization_in_progress is False

                asyncio.run(run_test())

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_save_optimized_index_no_service(self, mock_get_settings):
        """Test saving optimized index when no vector service."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                # Should not raise exception
                await manager._save_optimized_index()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_create_backup_save_fails(self, mock_get_settings):
        """Test backup creation when save fails."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_vector_service = Mock()
        mock_vector_service.save_index.return_value = False

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                result = await manager.create_backup()

                assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_perform_optimization_no_vector_service(self, mock_get_settings):
        """Test _perform_optimization when no vector service available."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                result = await manager._perform_optimization()

                assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_perform_optimization_exception(self, mock_get_settings):
        """Test _perform_optimization when exception occurs."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 5000
        mock_index.d = 512

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index
        mock_vector_service.save_index.return_value = True

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                with patch.object(
                    manager, "create_backup", side_effect=Exception("Backup failed")
                ):
                    result = await manager._perform_optimization()

                    assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_perform_optimization_optimized_index_none(self, mock_get_settings):
        """Test _perform_optimization when optimized index is None."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 5000
        mock_index.d = 512

        mock_vector_service = Mock()
        mock_vector_service.index = mock_index

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                with patch.object(manager, "create_backup", return_value=True):
                    with patch.object(
                        manager, "_optimize_flat_index", return_value=None
                    ):
                        result = await manager._perform_optimization()

                        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_save_optimized_index_success(self, mock_get_settings):
        """Test _save_optimized_index when successful."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            mock_index = Mock()
            mock_index.ntotal = 1000

            mock_vector_service = Mock()
            mock_vector_service.index = mock_index
            mock_vector_service.save_index.return_value = True

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    await manager._save_optimized_index()

                    mock_vector_service.save_index.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_save_optimized_index_failure(self, mock_get_settings):
        """Test _save_optimized_index when save fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            mock_index = Mock()
            mock_index.ntotal = 1000

            mock_vector_service = Mock()
            mock_vector_service.index = mock_index
            mock_vector_service.save_index.return_value = False

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    # Should not raise exception
                    await manager._save_optimized_index()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_save_optimized_index_exception(self, mock_get_settings):
        """Test _save_optimized_index when exception occurs."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_vector_service = Mock()
        mock_vector_service.index = Mock()
        mock_vector_service.save_index.side_effect = Exception("Save failed")

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                # Should not raise exception
                await manager._save_optimized_index()

    @patch("src.services.faiss_manager.get_settings")
    def test_optimize_flat_index_error(self, mock_get_settings):
        """Test _optimize_flat_index when exception occurs."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_index = Mock()
        mock_index.ntotal = 1000
        mock_index.d = 512
        mock_index.reconstruct_n.side_effect = Exception("Reconstruct failed")

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                result = manager._optimize_flat_index(mock_index)

                assert result is None

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_create_backup_with_exception(self, mock_get_settings):
        """Test create_backup when exception occurs."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        mock_vector_service = Mock()
        mock_vector_service.save_index.side_effect = Exception("Save error")

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)

                result = await manager.create_backup()

                assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_restore_backup_missing_index_file(self, mock_get_settings):
        """Test restoring from backup with missing index file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()

                    # Create backup directory but no index file
                    backup_dir = manager.backup_path / "test_missing"
                    backup_dir.mkdir(parents=True, exist_ok=True)

                    result = await manager.restore_backup("test_missing")

                    assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_restore_backup_exception(self, mock_get_settings):
        """Test restore_backup when exception occurs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            mock_vector_service = Mock()
            mock_vector_service.index_path = Path(temp_dir) / "index.faiss"
            mock_vector_service._load_index.side_effect = Exception("Load failed")

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    # Create backup
                    backup_dir = manager.backup_path / "test_exception"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    (backup_dir / "index.faiss").write_bytes(b"data")

                    with patch.object(manager, "create_backup", return_value=True):
                        result = await manager.restore_backup("test_exception")

                        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_cleanup_old_backups_no_backups(self, mock_get_settings):
        """Test _cleanup_old_backups when no backups exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()

                    # Should not raise exception
                    await manager._cleanup_old_backups()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_cleanup_old_backups_with_invalid_info(self, mock_get_settings):
        """Test _cleanup_old_backups when backup has invalid info.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()
                    manager.max_backups = 2

                    # Create backup with invalid info
                    backup_dir = manager.backup_path / "backup_invalid"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    with open(backup_dir / "info.json", "w") as f:
                        f.write("invalid json")

                    await manager._cleanup_old_backups()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_cleanup_old_backups_removal_error(self, mock_get_settings):
        """Test _cleanup_old_backups when removal fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()
                    manager.max_backups = 1

                    # Create multiple backups
                    for i in range(3):
                        backup_dir = manager.backup_path / f"backup_{i}"
                        backup_dir.mkdir(parents=True, exist_ok=True)
                        backup_time = datetime.now() - timedelta(hours=i)
                        info = {"created_at": backup_time.isoformat()}
                        with open(backup_dir / "info.json", "w") as f:
                            json.dump(info, f)

                    # Mock shutil.rmtree to fail
                    with patch("shutil.rmtree", side_effect=Exception("Remove failed")):
                        # Should not raise exception
                        await manager._cleanup_old_backups()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_shutdown_with_exception(self, mock_get_settings):
        """Test shutdown when exception occurs."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                with patch.object(
                    manager, "_save_stats", side_effect=Exception("Save failed")
                ):
                    # Should not raise exception
                    await manager.shutdown()

    @patch("src.services.faiss_manager.get_settings")
    def test_get_performance_stats_no_vector_service(self, mock_get_settings):
        """Test get_performance_stats when no vector service."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()

                    # Create index file
                    manager.index_path.parent.mkdir(parents=True, exist_ok=True)
                    manager.index_path.write_bytes(b"x" * 1024 * 1024)

                    stats = manager.get_performance_stats()

                    assert "total_vectors" in stats
                    assert stats["index_size_mb"] == 1.0

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_cleanup_old_backups_exception_handling(self, mock_get_settings):
        """Test _cleanup_old_backups when exception occurs."""
        mock_settings = Mock()
        mock_settings.app_data_dir = tempfile.mkdtemp()
        mock_get_settings.return_value = mock_settings

        with patch.object(FAISSIndexManager, "_load_stats"):
            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager()

                # Make backup_path.exists() raise exception
                with patch.object(Path, "exists", side_effect=Exception("Path error")):
                    # Should not raise exception
                    await manager._cleanup_old_backups()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_cleanup_old_backups_no_backup_path(self, mock_get_settings):
        """Test _cleanup_old_backups when backup path doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager()

                    # Remove backup path
                    if manager.backup_path.exists():
                        shutil.rmtree(manager.backup_path)

                    # Should handle gracefully
                    await manager._cleanup_old_backups()

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_create_backup_without_metadata(self, mock_get_settings):
        """Test create_backup when metadata_path is None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            mock_index = Mock()
            mock_index.ntotal = 1000

            mock_vector_service = Mock()
            mock_vector_service.index = mock_index
            mock_vector_service.save_index.return_value = True
            mock_vector_service.index_path = Path(temp_dir) / "index.faiss"
            mock_vector_service.metadata_path = None  # No metadata

            mock_vector_service.index_path.parent.mkdir(parents=True, exist_ok=True)
            mock_vector_service.index_path.write_bytes(b"data")

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    with patch.object(manager, "_cleanup_old_backups"):
                        result = await manager.create_backup()

                        assert result is True

    @pytest.mark.asyncio
    @patch("src.services.faiss_manager.get_settings")
    async def test_restore_backup_without_metadata(self, mock_get_settings):
        """Test restoring backup when metadata file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.app_data_dir = temp_dir
            mock_get_settings.return_value = mock_settings

            current_dir = Path(temp_dir) / "current"
            current_dir.mkdir(parents=True, exist_ok=True)

            mock_vector_service = Mock()
            mock_vector_service.index_path = current_dir / "index.faiss"
            mock_vector_service.metadata_path = None
            mock_vector_service._load_index = Mock()

            with patch.object(FAISSIndexManager, "_load_stats"):
                with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                    manager = FAISSIndexManager(
                        vector_search_service=mock_vector_service
                    )

                    # Create backup without metadata
                    backup_dir = manager.backup_path / "test_no_metadata"
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    (backup_dir / "index.faiss").write_bytes(b"data")

                    with patch.object(manager, "create_backup", return_value=True):
                        result = await manager.restore_backup("test_no_metadata")

                        assert result is True
