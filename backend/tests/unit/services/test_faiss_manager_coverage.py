import asyncio
import json
import os
import shutil
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import numpy as np

# Mock faiss before import
sys_modules_patch = patch.dict("sys.modules", {"faiss": MagicMock()})
sys_modules_patch.start()
import faiss  # noqa: E402

# Import module under test
from src.services.faiss_manager import FAISSIndexManager  # noqa: E402


class TestFAISSManagerCoverage(unittest.TestCase):
    def setUp(self):
        self.mock_vector_service = MagicMock()
        self.mock_vector_service.index = MagicMock()
        self.mock_vector_service.index.ntotal = 1000
        self.mock_vector_service.index.d = 512
        self.mock_vector_service.index_path = Path("/tmp/index.faiss")
        self.mock_vector_service.metadata_path = Path("/tmp/metadata.pkl")
        self.mock_vector_service.save_index.return_value = True

        self.mock_settings = MagicMock()
        self.mock_settings.DATA_DIR = "/tmp/app_data"

        self.settings_patch = patch("src.services.faiss_manager.get_settings", return_value=self.mock_settings)
        self.settings_patch.start()

        # Mock Path/OS operations
        self.path_patch = patch("pathlib.Path.mkdir")
        self.path_patch.start()

        # Instantiate manager
        self.manager = FAISSIndexManager(self.mock_vector_service)
        # Prevent actual thread start (though code skips it if PYTEST_CURRENT_TEST is set)

    def tearDown(self):
        patch.stopall()
        sys_modules_patch.stop()

    def test_should_optimize(self):
        """Test optimization triggers."""
        self.manager.auto_optimize_threshold = 1000

        # Case 1: Not enough vectors
        self.mock_vector_service.index.ntotal = 500
        self.assertFalse(self.manager.should_optimize())

        # Case 2: Enough vectors, never optimized
        self.mock_vector_service.index.ntotal = 1500
        self.manager.stats["last_optimization"] = None
        self.assertTrue(self.manager.should_optimize())

        # Case 3: Optimized recently
        self.manager.stats["last_optimization"] = datetime.now().isoformat()
        self.assertFalse(self.manager.should_optimize())

        # Case 4: Optimized long ago
        old_time = (datetime.now() - timedelta(hours=5)).isoformat()
        self.manager.stats["last_optimization"] = old_time
        self.assertTrue(self.manager.should_optimize())

        # Case 5: Optimization in progress
        self.manager._optimization_in_progress = True
        self.assertFalse(self.manager.should_optimize())

    @patch("src.services.faiss_manager.time.time")
    def test_perform_optimization_small(self, mock_time):
        """Test optimization for small collection (Flat index)."""
        mock_time.return_value = 100.0
        self.mock_vector_service.index.ntotal = 5000 # Small
        self.mock_vector_service.index.reconstruct_n.return_value = np.zeros((5000, 512), dtype=np.float32)

        # Mock faiss classes
        faiss.IndexFlatIP = MagicMock()

        # Mock create_backup to succeed
        self.manager.create_backup = AsyncMock(return_value=True)
        self.manager._save_optimized_index = AsyncMock()
        self.manager._save_stats = MagicMock()

        asyncio.run(self.manager.optimize_index(force=True))

        # Verify Flat index created
        faiss.IndexFlatIP.assert_called_with(512)
        self.manager._save_optimized_index.assert_called()
        self.assertIsNotNone(self.manager.stats["last_optimization"])

    def test_perform_optimization_medium(self):
        """Test optimization for medium collection (IVF)."""
        self.mock_vector_service.index.ntotal = 100000 # Medium
        self.mock_vector_service.index.reconstruct_n.return_value = np.zeros((100000, 512), dtype=np.float32)

        faiss.IndexFlatIP = MagicMock()
        faiss.IndexIVFFlat = MagicMock()

        self.manager.create_backup = AsyncMock(return_value=True)
        self.manager._save_optimized_index = AsyncMock()

        asyncio.run(self.manager.optimize_index(force=True))

        # Verify IVF Flat created (no PQ)
        faiss.IndexIVFFlat.assert_called()
        self.manager._save_optimized_index.assert_called()

    def test_perform_optimization_large(self):
        """Test optimization for large collection (IVF-PQ)."""
        self.mock_vector_service.index.ntotal = 300000 # Large
        self.mock_vector_service.index.reconstruct_n.return_value = np.zeros((300000, 512), dtype=np.float32)

        faiss.IndexFlatIP = MagicMock()
        faiss.IndexIVFPQ = MagicMock()

        self.manager.create_backup = AsyncMock(return_value=True)
        self.manager._save_optimized_index = AsyncMock()

        asyncio.run(self.manager.optimize_index(force=True))

        # Verify IVF PQ created
        faiss.IndexIVFPQ.assert_called()

    @patch("shutil.copy2")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("os.path.exists", return_value=True)
    def test_create_backup(self, mock_exists, mock_open, mock_copy):
        """Test backup creation."""
        self.manager._cleanup_old_backups = AsyncMock()
        self.manager._save_stats = MagicMock()

        asyncio.run(self.manager.create_backup("test_backup"))

        # Verify save_index called
        self.mock_vector_service.save_index.assert_called()
        # Verify files copied
        self.assertTrue(mock_copy.called)
        # Verify metadata saved
        mock_open.assert_called()
        # Verify cleanup called
        self.manager._cleanup_old_backups.assert_called()

    @patch("shutil.copy2")
    @patch("pathlib.Path.exists", return_value=True)
    def test_restore_backup(self, mock_exists, mock_copy):
        """Test backup restoration."""
        self.manager.create_backup = AsyncMock(return_value=True)
        self.mock_vector_service._load_index = MagicMock()

        success = asyncio.run(self.manager.restore_backup("test_backup"))

        self.assertTrue(success)
        # Verify backup of current state created
        self.manager.create_backup.assert_called_with("pre_restore")
        # Verify files copied back
        self.assertTrue(mock_copy.called)
        # Verify index reloaded
        self.mock_vector_service._load_index.assert_called()

    @patch("builtins.open", side_effect=Exception("Read Error"))
    @patch("shutil.rmtree")
    def test_cleanup_old_backups(self, mock_rmtree, mock_open):
        """Test old backup cleanup."""
        # Mock backup_path on the manager instance
        self.manager.backup_path = MagicMock()

        # Create mock backup directories
        backups_list = []
        for i in range(10):
            d = MagicMock()
            d.is_dir.return_value = True
            d.name = f"backup_{i}"

            # Mock / operator to return a mock with exists=True
            info_file_mock = MagicMock()
            info_file_mock.exists.return_value = True
            d.__truediv__.return_value = info_file_mock

            # Make json.load fail so it falls back to mtime (simpler than mocking json content)
            # But json.load is called on open() context manager result.
            # Easiest way: allow fallback.

            d.stat.return_value.st_mtime = 1000 + i # Newer ones have higher mtime
            backups_list.append(d)

        self.manager.backup_path.iterdir.return_value = backups_list
        self.manager.max_backups = 5

        asyncio.run(self.manager._cleanup_old_backups())

        # Should remove 5 oldest backups (indices 0-4 have lowest mtime)
        self.assertEqual(mock_rmtree.call_count, 5)

    def test_record_search_time(self):
        """Test stats recording."""
        self.manager.stats["search_count"] = 0
        self.manager.stats["average_search_time"] = 0.0

        self.manager.record_search_time(10.0) # avg becomes 1.0 (alpha 0.1)
        self.assertAlmostEqual(self.manager.stats["average_search_time"], 1.0)

        self.manager.record_search_time(10.0) # avg becomes 0.1*10 + 0.9*1 = 1.9
        self.assertAlmostEqual(self.manager.stats["average_search_time"], 1.9)

        self.assertEqual(self.manager.stats["search_count"], 2)

    def test_optimize_fail_no_service(self):
        """Test optimization fail when no service."""
        self.manager.vector_service = None
        result = asyncio.run(self.manager.optimize_index(force=True))
        self.assertFalse(result)

    def test_optimize_fail_exception(self):
        """Test optimization exception handling."""
        self.manager.create_backup = AsyncMock(side_effect=Exception("Backup failed"))
        result = asyncio.run(self.manager.optimize_index(force=True))
        self.assertFalse(result)


