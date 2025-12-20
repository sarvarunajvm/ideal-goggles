"""Comprehensive unit tests for FAISS index manager."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from src.services.faiss_manager import FAISSIndexManager
from src.services.vector_search import FAISSVectorSearchService


class TestFAISSIndexManager:
    """Test FAISSIndexManager class."""

    @pytest.fixture(autouse=True)
    def stop_scheduler(self):
        """Prevent background scheduler from starting in tests."""
        with patch("src.services.faiss_manager.FAISSIndexManager._start_background_scheduler"):
            yield

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_vector_service(self, temp_dir):
        """Create mock vector search service."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 1000
            mock_index.d = 512
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(
                index_path=str(Path(temp_dir) / "test_index.bin")
            )
            yield service

    @pytest.fixture
    def manager(self, temp_dir, mock_vector_service):
        """Create FAISSIndexManager instance."""
        with patch("src.services.faiss_manager.get_settings") as mock_settings:
            mock_settings.return_value.app_data_dir = temp_dir

            with patch.object(FAISSIndexManager, "_start_background_scheduler"):
                manager = FAISSIndexManager(vector_search_service=mock_vector_service)
                yield manager

    def test_initialization(self, temp_dir, mock_vector_service):
        """Test manager initialization."""
        with patch("src.services.faiss_manager.get_settings") as mock_settings:
            mock_settings.return_value.app_data_dir = temp_dir

            manager = FAISSIndexManager(vector_search_service=mock_vector_service)

            assert manager.vector_service == mock_vector_service
            assert manager.base_path.exists()
            assert manager.backup_path.exists()

    def test_load_stats_existing(self, temp_dir, mock_vector_service):
        """Test loading existing stats."""
        with patch("src.services.faiss_manager.get_settings") as mock_settings:
            mock_settings.return_value.app_data_dir = temp_dir

            stats_path = Path(temp_dir) / "faiss" / "stats.json"
            stats_path.parent.mkdir(parents=True, exist_ok=True)

            existing_stats = {
                "last_optimization": "2023-01-01T00:00:00",
                "total_vectors": 5000,
            }

            with open(stats_path, "w") as f:
                json.dump(existing_stats, f)

            manager = FAISSIndexManager(vector_search_service=mock_vector_service)
            manager._scheduler_thread = None

            assert manager.stats["last_optimization"] == "2023-01-01T00:00:00"
            assert manager.stats["total_vectors"] == 5000

    def test_load_stats_missing(self, temp_dir, mock_vector_service):
        """Test loading stats when file doesn't exist."""
        with patch("src.services.faiss_manager.get_settings") as mock_settings:
            mock_settings.return_value.app_data_dir = temp_dir

            manager = FAISSIndexManager(vector_search_service=mock_vector_service)
            manager._scheduler_thread = None

            # Should have default stats
            assert "total_vectors" in manager.stats

    def test_save_stats(self, temp_dir, mock_vector_service):
        """Test saving stats to disk."""
        with patch("src.services.faiss_manager.get_settings") as mock_settings:
            mock_settings.return_value.app_data_dir = temp_dir

            manager = FAISSIndexManager(vector_search_service=mock_vector_service)
            manager._scheduler_thread = None

            manager.stats["total_vectors"] = 10000
            manager._save_stats()

            stats_path = Path(temp_dir) / "faiss" / "stats.json"
            assert stats_path.exists()

            with open(stats_path) as f:
                saved_stats = json.load(f)

            assert saved_stats["total_vectors"] == 10000

    def test_should_optimize_below_threshold(self, manager):
        """Test should_optimize returns False below threshold."""
        manager.vector_service.index.ntotal = 10000

        result = manager.should_optimize()

        assert result is False

    def test_should_optimize_above_threshold(self, manager):
        """Test should_optimize returns True above threshold."""
        manager.vector_service.index.ntotal = 100000
        manager.stats["last_optimization"] = None

        result = manager.should_optimize()

        assert result is True

    def test_should_optimize_recently_optimized(self, manager):
        """Test should_optimize returns False if recently optimized."""
        manager.vector_service.index.ntotal = 100000
        manager.stats["last_optimization"] = datetime.now().isoformat()

        result = manager.should_optimize()

        assert result is False

    def test_should_optimize_optimization_in_progress(self, manager):
        """Test should_optimize returns False when optimization in progress."""
        manager.vector_service.index.ntotal = 100000
        manager._optimization_in_progress = True

        result = manager.should_optimize()

        assert result is False

    def test_should_optimize_no_index(self, temp_dir):
        """Test should_optimize returns False when no index."""
        with patch("src.services.faiss_manager.get_settings") as mock_settings:
            mock_settings.return_value.app_data_dir = temp_dir

            service = Mock()
            service.index = None

            manager = FAISSIndexManager(vector_search_service=service)
            manager._scheduler_thread = None

            result = manager.should_optimize()

            assert result is False

    @pytest.mark.asyncio
    async def test_optimize_index_force(self, manager):
        """Test force optimization."""
        manager._optimization_in_progress = False

        with (
            patch.object(
                manager, "_perform_optimization", new_callable=AsyncMock
            ) as mock_opt,
            patch.object(manager, "create_backup", new_callable=AsyncMock),
        ):
            mock_opt.return_value = True

            result = await manager.optimize_index(force=True)

            assert result is True
            mock_opt.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_index_not_needed(self, manager):
        """Test optimization when not needed."""
        manager.vector_service.index.ntotal = 10000
        manager._optimization_in_progress = False

        result = await manager.optimize_index(force=False)

        assert result is False

    @pytest.mark.asyncio
    async def test_optimize_index_already_in_progress(self, manager):
        """Test optimization when already in progress."""
        manager._optimization_in_progress = True

        result = await manager.optimize_index(force=True)

        assert result is False

    @pytest.mark.asyncio
    async def test_perform_optimization_small_collection(self, manager):
        """Test optimization for small collection."""
        manager.vector_service.index.ntotal = 5000

        with (
            patch.object(manager, "_optimize_flat_index") as mock_flat,
            patch.object(manager, "create_backup", new_callable=AsyncMock),
            patch.object(manager, "_save_optimized_index", new_callable=AsyncMock),
        ):
            mock_optimized = Mock()
            mock_optimized.ntotal = 5000
            mock_flat.return_value = mock_optimized

            result = await manager._perform_optimization()

            assert result is True
            mock_flat.assert_called_once()

    @pytest.mark.asyncio
    async def test_perform_optimization_medium_collection(self, manager):
        """Test optimization for medium collection."""
        manager.vector_service.index.ntotal = 50000

        with (
            patch.object(manager, "_create_ivf_index") as mock_ivf,
            patch.object(manager, "create_backup", new_callable=AsyncMock),
            patch.object(manager, "_save_optimized_index", new_callable=AsyncMock),
        ):
            mock_optimized = Mock()
            mock_optimized.ntotal = 50000
            mock_ivf.return_value = mock_optimized

            result = await manager._perform_optimization()

            assert result is True
            mock_ivf.assert_called_once_with(manager.vector_service.index, use_pq=False)

    @pytest.mark.asyncio
    async def test_perform_optimization_large_collection(self, manager):
        """Test optimization for large collection."""
        manager.vector_service.index.ntotal = 250000

        with (
            patch.object(manager, "_create_ivf_index") as mock_ivf,
            patch.object(manager, "create_backup", new_callable=AsyncMock),
            patch.object(manager, "_save_optimized_index", new_callable=AsyncMock),
        ):
            mock_optimized = Mock()
            mock_optimized.ntotal = 250000
            mock_ivf.return_value = mock_optimized

            result = await manager._perform_optimization()

            assert result is True
            mock_ivf.assert_called_once_with(manager.vector_service.index, use_pq=True)

    @pytest.mark.asyncio
    async def test_perform_optimization_empty_index(self, manager):
        """Test optimization with empty index."""
        manager.vector_service.index.ntotal = 0

        result = await manager._perform_optimization()

        assert result is False

    def test_optimize_flat_index(self, manager):
        """Test optimizing flat index."""
        mock_index = Mock()
        mock_index.ntotal = 1000
        mock_index.d = 512
        vectors = np.random.randn(1000, 512).astype(np.float32)
        mock_index.reconstruct_n.return_value = vectors

        with patch("faiss.IndexFlatIP") as mock_ip:
            new_index = Mock()
            new_index.ntotal = 0
            mock_ip.return_value = new_index

            result = manager._optimize_flat_index(mock_index)

            assert result is not None
            mock_index.reconstruct_n.assert_called_once()

    def test_create_ivf_index_with_pq(self, manager):
        """Test creating IVF index with PQ."""
        mock_index = Mock()
        mock_index.ntotal = 250000
        mock_index.d = 512
        vectors = np.random.randn(250000, 512).astype(np.float32)
        mock_index.reconstruct_n.return_value = vectors

        with (
            patch("faiss.IndexIVFPQ") as mock_ivf,
            patch("faiss.IndexFlatIP") as mock_quantizer,
        ):
            ivf_index = Mock()
            ivf_index.nlist = 500
            mock_ivf.return_value = ivf_index
            mock_quantizer.return_value = Mock()

            result = manager._create_ivf_index(mock_index, use_pq=True)

            assert result is not None
            mock_ivf.assert_called_once()

    def test_create_ivf_index_without_pq(self, manager):
        """Test creating IVF index without PQ."""
        mock_index = Mock()
        mock_index.ntotal = 50000
        mock_index.d = 512
        vectors = np.random.randn(50000, 512).astype(np.float32)
        mock_index.reconstruct_n.return_value = vectors

        with (
            patch("faiss.IndexIVFFlat") as mock_ivf,
            patch("faiss.IndexFlatIP") as mock_quantizer,
        ):
            ivf_index = Mock()
            ivf_index.nlist = 224
            mock_ivf.return_value = ivf_index
            mock_quantizer.return_value = Mock()

            result = manager._create_ivf_index(mock_index, use_pq=False)

            assert result is not None
            mock_ivf.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_backup(self, manager):
        """Test creating backup."""
        manager.vector_service.index_path = str(Path(manager.base_path) / "index.bin")
        manager.vector_service.metadata_path = str(
            Path(manager.base_path) / "metadata.json"
        )

        # Create mock files
        Path(manager.vector_service.index_path).parent.mkdir(
            parents=True, exist_ok=True
        )
        Path(manager.vector_service.index_path).touch()
        Path(manager.vector_service.metadata_path).touch()

        with patch.object(manager.vector_service, "save_index", return_value=True):
            result = await manager.create_backup("test_backup")

            assert result is True
            backup_dir = manager.backup_path / "test_backup"
            assert backup_dir.exists()

    @pytest.mark.asyncio
    async def test_create_backup_auto_name(self, manager):
        """Test creating backup with auto-generated name."""
        manager.vector_service.index_path = str(Path(manager.base_path) / "index.bin")
        manager.vector_service.metadata_path = str(
            Path(manager.base_path) / "metadata.json"
        )

        Path(manager.vector_service.index_path).parent.mkdir(
            parents=True, exist_ok=True
        )
        Path(manager.vector_service.index_path).touch()
        Path(manager.vector_service.metadata_path).touch()

        with patch.object(manager.vector_service, "save_index", return_value=True):
            result = await manager.create_backup()

            assert result is True
            # Should have created backup with timestamp name
            backups = list(manager.backup_path.iterdir())
            assert len(backups) > 0

    @pytest.mark.asyncio
    async def test_create_backup_no_service(self, temp_dir):
        """Test creating backup when no service."""
        with patch("src.services.faiss_manager.get_settings") as mock_settings:
            mock_settings.return_value.app_data_dir = temp_dir

            manager = FAISSIndexManager(vector_search_service=None)
            manager._scheduler_thread = None

            result = await manager.create_backup()

            assert result is False

    @pytest.mark.asyncio
    async def test_restore_backup(self, manager):
        """Test restoring from backup."""
        backup_name = "test_backup"
        backup_dir = manager.backup_path / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create backup files
        (backup_dir / "index.faiss").touch()
        (backup_dir / "metadata.pkl").touch()

        manager.vector_service.index_path = str(Path(manager.base_path) / "index.bin")
        manager.vector_service.metadata_path = str(
            Path(manager.base_path) / "metadata.json"
        )

        with (
            patch.object(manager, "create_backup", new_callable=AsyncMock),
            patch.object(manager.vector_service, "_load_index", return_value=True),
        ):
            result = await manager.restore_backup(backup_name)

            assert result is True

    @pytest.mark.asyncio
    async def test_restore_backup_not_found(self, manager):
        """Test restoring non-existent backup."""
        result = await manager.restore_backup("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self, manager):
        """Test cleaning up old backups."""
        # Create multiple backups
        for i in range(10):
            backup_dir = manager.backup_path / f"backup_{i}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            info_file = backup_dir / "info.json"
            with open(info_file, "w") as f:
                json.dump(
                    {
                        "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                    },
                    f,
                )

        await manager._cleanup_old_backups()

        # Should keep only max_backups (7)
        remaining_backups = list(manager.backup_path.iterdir())
        assert len(remaining_backups) <= manager.max_backups

    def test_get_performance_stats(self, manager):
        """Test getting performance statistics."""
        manager.vector_service.index.ntotal = 5000
        manager.index_path.touch()

        stats = manager.get_performance_stats()

        assert stats["total_vectors"] == 5000
        assert "index_size_mb" in stats

    def test_record_search_time(self, manager):
        """Test recording search time."""
        initial_count = manager.stats["search_count"]
        initial_avg = manager.stats["average_search_time"]

        manager.record_search_time(0.05)

        assert manager.stats["search_count"] == initial_count + 1
        assert manager.stats["average_search_time"] != initial_avg

    @pytest.mark.asyncio
    async def test_shutdown(self, manager):
        """Test graceful shutdown."""
        with patch.object(manager, "_save_stats") as mock_save:
            await manager.shutdown()

            mock_save.assert_called_once()
