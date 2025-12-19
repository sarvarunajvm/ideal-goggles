"""Unit tests for vector search service."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.services.vector_search import FAISSVectorSearchService


class TestFAISSVectorSearchService:
    """Test FAISSVectorSearchService class."""

    @pytest.fixture
    def temp_index_path(self):
        """Create a temporary directory for test indices."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield os.path.join(tmpdir, "test_index.bin")

    def test_initialization_new_index(self, temp_index_path):
        """Test initialization with new index."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_index.d = 512
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(
                index_path=temp_index_path, dimension=512
            )

            assert service.dimension == 512
            assert service.index_path == temp_index_path
            assert service.metadata_path == temp_index_path.replace(
                ".bin", "_metadata.json"
            )
            assert service.index is not None
            assert service.id_to_file_id == {}
            assert service.file_id_to_index == {}
            mock_ip.assert_called_once_with(512)

    def test_initialization_load_existing(self, temp_index_path):
        """Test loading existing index."""
        with patch("faiss.read_index") as mock_read:
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_read.return_value = mock_index

            # Create mock existing files
            Path(temp_index_path).touch()
            metadata_path = temp_index_path.replace(".bin", "_metadata.json")
            metadata = {
                "id_to_file_id": {0: 10, 1: 20},
                "file_id_to_index": {10: 0, 20: 1},
                "dimension": 512,
                "saved_at": 123456,
            }

            with patch("builtins.open", create=True):
                with patch("json.load", return_value=metadata):
                    Path(metadata_path).touch()
                    service = FAISSVectorSearchService(index_path=temp_index_path)

                    mock_read.assert_called_once()

    def test_initialization_no_faiss(self, temp_index_path):
        """Test initialization when FAISS is not available."""
        with patch("builtins.__import__", side_effect=ImportError("No module named 'faiss'")):
            service = FAISSVectorSearchService(index_path=temp_index_path)
            # Should set index to None but not raise
            assert service.index is None

    def test_create_new_index_clip_dimension(self, temp_index_path):
        """Test creating new index with CLIP dimension."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(
                index_path=temp_index_path, dimension=512
            )
            mock_ip.assert_called_with(512)

    def test_create_new_index_other_dimension(self, temp_index_path):
        """Test creating new index with non-CLIP dimension."""
        with patch("faiss.IndexFlatL2") as mock_l2:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_l2.return_value = mock_index

            service = FAISSVectorSearchService(
                index_path=temp_index_path, dimension=256
            )
            mock_l2.assert_called_with(256)

    def test_add_single_vector(self, temp_index_path):
        """Test adding a single vector."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            call_count = [0]

            def increment_ntotal(vec):
                call_count[0] += 1
                mock_index.ntotal = call_count[0]

            mock_index.add.side_effect = increment_ntotal
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            vector = np.random.randn(512).astype(np.float32)

            result = service.add_vector(file_id=1, vector=vector)

            # Check vector was normalized and added
            assert result is True
            mock_index.add.assert_called_once()
            assert 1 in service.file_id_to_index
            assert service.unsaved_additions == 1

    def test_add_multiple_vectors(self, temp_index_path):
        """Test adding multiple vectors sequentially."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            call_count = [0]

            def increment_ntotal(vec):
                call_count[0] += 1
                mock_index.ntotal = call_count[0]

            mock_index.add.side_effect = increment_ntotal
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)

            file_ids = [1, 2, 3, 4, 5]
            for file_id in file_ids:
                vector = np.random.randn(512).astype(np.float32)
                service.add_vector(file_id=file_id, vector=vector)

            assert mock_index.add.call_count == 5
            for file_id in file_ids:
                assert file_id in service.file_id_to_index

    def test_search_basic(self, temp_index_path):
        """Test basic vector search."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 10
            mock_index.search.return_value = (
                np.array([[0.9, 0.8, 0.7]]),
                np.array([[0, 1, 2]]),
            )
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            # Add some mappings
            service.id_to_file_id = {0: 10, 1: 20, 2: 30}

            query_vector = np.random.randn(512).astype(np.float32)
            results = service.search(query_vector, top_k=3)

            assert len(results) == 3
            assert results[0][0] == 10
            assert results[0][1] == pytest.approx(0.9)
            assert results[1][0] == 20
            assert results[2][0] == 30

    def test_search_empty_index(self, temp_index_path):
        """Test searching in empty index."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            query_vector = np.random.randn(512).astype(np.float32)

            results = service.search(query_vector, top_k=5)
            assert results == []

    def test_remove_vector(self, temp_index_path):
        """Test removing a vector."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 1
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.file_id_to_index = {1: 0}
            service.id_to_file_id = {0: 1}

            success = service.remove_vector(file_id=1)

            assert success
            assert 1 not in service.file_id_to_index
            assert service.id_to_file_id[0] is None  # Marked as deleted

    def test_remove_nonexistent_vector(self, temp_index_path):
        """Test removing a vector that doesn't exist."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            success = service.remove_vector(file_id=999)

            assert not success

    def test_save_index(self, temp_index_path):
        """Test saving index to disk."""
        with (
            patch("faiss.IndexFlatIP") as mock_ip,
            patch("faiss.write_index") as mock_write,
        ):
            mock_index = Mock()
            mock_index.ntotal = 5
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.id_to_file_id = {0: 10, 1: 20}
            service._index_dirty = True

            with patch("builtins.open", create=True):
                with patch("json.dump") as mock_json:
                    result = service.save_index()

                    assert result is True
                    mock_write.assert_called_once_with(mock_index, temp_index_path)
                    mock_json.assert_called_once()

    def test_batch_search(self, temp_index_path):
        """Test batch vector search."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 10
            mock_index.search.return_value = (
                np.array([[0.9, 0.8], [0.85, 0.75]]),
                np.array([[0, 1], [2, 3]]),
            )
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.id_to_file_id = {0: 10, 1: 20, 2: 30, 3: 40}

            query_vectors = np.random.randn(2, 512).astype(np.float32)
            results = service.batch_search(query_vectors, top_k=2)

            assert len(results) == 2
            assert len(results[0]) == 2
            assert results[0][0][0] == 10
            assert results[1][0][0] == 30

    def test_get_statistics(self, temp_index_path):
        """Test getting index statistics."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_index.d = 512
            # Set the __class__.__name__ properly for type()
            type(mock_index).__name__ = "IndexFlatIP"
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.unsaved_additions = 5

            stats = service.get_statistics()

            assert stats["total_vectors"] == 100
            assert stats["dimension"] == 512
            assert stats["index_type"] == "IndexFlatIP"
            assert stats["unsaved_additions"] == 5

    def test_thread_safety(self, temp_index_path):
        """Test thread safety with concurrent operations."""
        import threading

        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            call_count = [0]
            lock = threading.Lock()

            def increment_ntotal(vec):
                with lock:
                    call_count[0] += 1
                    mock_index.ntotal = call_count[0]

            mock_index.add.side_effect = increment_ntotal
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            errors = []

            def add_vectors(thread_id):
                try:
                    for i in range(10):
                        vector = np.random.randn(512).astype(np.float32)
                        service.add_vector(file_id=thread_id * 1000 + i, vector=vector)
                except Exception as e:
                    errors.append(e)

            # Run multiple threads
            threads = [
                threading.Thread(target=add_vectors, args=(i,)) for i in range(3)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0  # No errors should occur

    def test_search_similar(self, temp_index_path):
        """Test search_similar returns correct format."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 10
            mock_index.search.return_value = (
                np.array([[0.9, 0.8]]),
                np.array([[0, 1]]),
            )
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.id_to_file_id = {0: 10, 1: 20}

            query_vector = np.random.randn(512).astype(np.float32)
            results = service.search_similar(query_vector, k=2)

            assert len(results) == 2
            assert "file_id" in results[0]
            assert "distance" in results[0]
            assert results[0]["file_id"] == 10
            # Distance = 1 - similarity
            assert results[0]["distance"] == pytest.approx(0.1)

    def test_rebuild_index(self, temp_index_path):
        """Test rebuilding index to remove deleted entries."""
        with (
            patch("faiss.IndexFlatIP") as mock_ip,
            patch("faiss.write_index") as mock_write,
        ):
            # First mock for initial creation
            initial_index = Mock()
            initial_index.ntotal = 3
            initial_index.reconstruct.side_effect = [
                np.random.randn(512).astype(np.float32),
                np.random.randn(512).astype(np.float32),
                np.random.randn(512).astype(np.float32),
            ]

            # Second mock for rebuilt index
            rebuilt_index = Mock()
            rebuilt_index.ntotal = 2

            mock_ip.side_effect = [initial_index, rebuilt_index]

            service = FAISSVectorSearchService(index_path=temp_index_path)
            # Simulate some deleted entries
            service.id_to_file_id = {0: 10, 1: None, 2: 30}  # Entry 1 is deleted
            service.file_id_to_index = {10: 0, 30: 2}

            with patch("builtins.open", create=True):
                with patch("json.dump"):
                    result = service.rebuild_index()

            assert result is True
            # Should only have 2 valid entries now
            assert len(service.file_id_to_index) == 2
            assert 10 in service.file_id_to_index
            assert 30 in service.file_id_to_index

    def test_get_vector_existing(self, temp_index_path):
        """Test getting an existing vector."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 1
            mock_vector = np.random.randn(512).astype(np.float32)
            mock_index.reconstruct.return_value = mock_vector
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.file_id_to_index = {1: 0}
            service.id_to_file_id = {0: 1}

            result = service.get_vector(file_id=1)

            assert result is not None
            assert np.array_equal(result, mock_vector)
            mock_index.reconstruct.assert_called_once_with(0)

    def test_get_vector_nonexistent(self, temp_index_path):
        """Test getting a vector that doesn't exist."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)

            result = service.get_vector(file_id=999)

            assert result is None

    def test_get_vector_no_index(self, temp_index_path):
        """Test getting vector when index is None."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.index = None

            result = service.get_vector(file_id=1)

            assert result is None

    def test_get_vector_exception_handling(self, temp_index_path):
        """Test get_vector handles exceptions gracefully."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 1
            mock_index.reconstruct.side_effect = Exception("Reconstruct failed")
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.file_id_to_index = {1: 0}
            service.id_to_file_id = {0: 1}

            result = service.get_vector(file_id=1)

            assert result is None

    def test_cleanup_with_dirty_index(self, temp_index_path):
        """Test cleanup saves index when dirty."""
        with (
            patch("faiss.IndexFlatIP") as mock_ip,
            patch("faiss.write_index") as mock_write,
        ):
            mock_index = Mock()
            mock_index.ntotal = 5
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service._index_dirty = True

            with patch("builtins.open", create=True):
                with patch("json.dump"):
                    service.cleanup()

                    mock_write.assert_called_once()

    def test_cleanup_without_dirty_index(self, temp_index_path):
        """Test cleanup doesn't save when index is not dirty."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 5
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service._index_dirty = False

            with patch("faiss.write_index") as mock_write:
                service.cleanup()

                mock_write.assert_not_called()

    def test_should_use_ivf_below_threshold(self, temp_index_path):
        """Test _should_use_ivf returns False below threshold."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)

            result = service._should_use_ivf(100000)

            assert result is False

    def test_should_use_ivf_above_threshold(self, temp_index_path):
        """Test _should_use_ivf returns True above threshold."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)

            result = service._should_use_ivf(250000)

            assert result is True

    def test_upgrade_to_ivf_index(self, temp_index_path):
        """Test upgrading to IVF index."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            initial_index = Mock()
            initial_index.ntotal = 250000
            initial_index.d = 512
            initial_index.reconstruct_n.return_value = np.random.randn(
                250000, 512
            ).astype(np.float32)

            mock_ip.return_value = initial_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.index = initial_index

            with (
                patch("faiss.IndexIVFPQ") as mock_ivf,
                patch("faiss.IndexFlatIP") as mock_quantizer,
            ):
                ivf_index = Mock()
                ivf_index.nlist = 500
                mock_ivf.return_value = ivf_index
                mock_quantizer.return_value = Mock()

                service._upgrade_to_ivf_index()

                assert mock_ivf.called

    def test_upgrade_to_ivf_index_empty(self, temp_index_path):
        """Test upgrade to IVF with empty index."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.index = mock_index

            # Should return early without error
            service._upgrade_to_ivf_index()

    def test_upgrade_to_ivf_index_none(self, temp_index_path):
        """Test upgrade to IVF when index is None."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.index = None

            # Should return early without error
            service._upgrade_to_ivf_index()

    def test_search_with_score_threshold(self, temp_index_path):
        """Test search with score threshold filtering."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 10
            mock_index.search.return_value = (
                np.array([[0.9, 0.5, 0.3, 0.1]]),
                np.array([[0, 1, 2, 3]]),
            )
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.id_to_file_id = {0: 10, 1: 20, 2: 30, 3: 40}

            query_vector = np.random.randn(512).astype(np.float32)
            results = service.search(query_vector, top_k=10, score_threshold=0.4)

            # Should filter out scores below 0.4
            assert len(results) == 2
            assert results[0][1] >= 0.4
            assert results[1][1] >= 0.4

    def test_search_with_deleted_entries(self, temp_index_path):
        """Test search skips deleted entries."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 10
            mock_index.search.return_value = (
                np.array([[0.9, 0.8, 0.7]]),
                np.array([[0, 1, 2]]),
            )
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            # Entry 1 is deleted (None)
            service.id_to_file_id = {0: 10, 1: None, 2: 30}

            query_vector = np.random.randn(512).astype(np.float32)
            results = service.search(query_vector, top_k=10)

            # Should skip deleted entry
            assert len(results) == 2
            assert results[0][0] == 10
            assert results[1][0] == 30

    def test_search_with_invalid_dimension(self, temp_index_path):
        """Test search with invalid vector dimension."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 10
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path, dimension=512)

            query_vector = np.random.randn(256).astype(np.float32)  # Wrong dimension

            results = service.search(query_vector, top_k=5)

            assert results == []

    def test_search_with_index_pos_minus_one(self, temp_index_path):
        """Test search handles -1 index position (no more results)."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 10
            mock_index.search.return_value = (
                np.array([[0.9, 0.8, -1.0]]),
                np.array([[0, 1, -1]]),
            )
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.id_to_file_id = {0: 10, 1: 20}

            query_vector = np.random.randn(512).astype(np.float32)
            results = service.search(query_vector, top_k=10)

            # Should stop at -1
            assert len(results) == 2

    def test_batch_search_empty_index(self, temp_index_path):
        """Test batch search with empty index."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)

            query_vectors = np.random.randn(3, 512).astype(np.float32)
            results = service.batch_search(query_vectors, top_k=5)

            assert len(results) == 3
            assert all(len(r) == 0 for r in results)

    def test_batch_search_no_index(self, temp_index_path):
        """Test batch search when index is None."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.index = None

            query_vectors = np.random.randn(2, 512).astype(np.float32)
            results = service.batch_search(query_vectors, top_k=5)

            assert len(results) == 2
            assert all(len(r) == 0 for r in results)

    def test_batch_search_with_deleted_entries(self, temp_index_path):
        """Test batch search skips deleted entries."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 10
            mock_index.search.return_value = (
                np.array([[0.9, 0.8, 0.7]]),
                np.array([[0, 1, 2]]),
            )
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            # Entry 1 is deleted
            service.id_to_file_id = {0: 10, 1: None, 2: 30}

            query_vectors = np.random.randn(1, 512).astype(np.float32)
            results = service.batch_search(query_vectors, top_k=10)

            assert len(results) == 1
            # Should skip deleted entry
            assert len(results[0]) == 2

    def test_add_vector_with_existing_file_id(self, temp_index_path):
        """Test adding vector when file_id already exists."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 1
            call_count = [1]

            def increment_ntotal(vec):
                call_count[0] += 1
                mock_index.ntotal = call_count[0]

            mock_index.add.side_effect = increment_ntotal
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.file_id_to_index = {1: 0}
            service.id_to_file_id = {0: 1}

            vector = np.random.randn(512).astype(np.float32)
            result = service.add_vector(file_id=1, vector=vector)

            assert result is True
            # Should have removed old entry and added new one
            assert 1 in service.file_id_to_index

    def test_add_vector_invalid_dimension(self, temp_index_path):
        """Test adding vector with wrong dimension."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path, dimension=512)

            vector = np.random.randn(256).astype(np.float32)  # Wrong dimension
            result = service.add_vector(file_id=1, vector=vector)

            assert result is False

    def test_add_vector_zero_norm(self, temp_index_path):
        """Test adding vector with zero norm."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            call_count = [0]

            def increment_ntotal(vec):
                call_count[0] += 1
                mock_index.ntotal = call_count[0]

            mock_index.add.side_effect = increment_ntotal
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)

            # Zero vector
            vector = np.zeros(512, dtype=np.float32)
            result = service.add_vector(file_id=1, vector=vector)

            # Should handle gracefully (norm is 0, so no normalization)
            assert result is True

    def test_save_index_not_dirty(self, temp_index_path):
        """Test save_index when index is not dirty."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 5
            mock_ip.return_value = mock_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service._index_dirty = False

            result = service.save_index()

            assert result is True

    def test_load_index_with_pickle_migration(self, temp_index_path):
        """Test loading index with pickle metadata migration."""
        import pickle

        with patch("faiss.read_index") as mock_read:
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_read.return_value = mock_index

            Path(temp_index_path).touch()
            pickle_path = temp_index_path.replace(".bin", "_metadata.pkl")
            metadata_path = temp_index_path.replace(".bin", "_metadata.json")

            # Create pickle metadata
            pickle_metadata = {
                "id_to_file_id": {0: 10, 1: 20},
                "file_id_to_index": {10: 0, 20: 1},
            }

            with patch("builtins.open", create=True) as mock_open:
                # Mock pickle file exists but JSON doesn't
                with patch("os.path.exists") as mock_exists:
                    mock_exists.side_effect = lambda p: (
                        p in (temp_index_path, pickle_path)
                    )

                    # Mock pickle.load
                    def mock_open_side_effect(path, mode):
                        if "rb" in mode:
                            return Mock(read=lambda: None)
                        return Mock()

                    mock_open.side_effect = mock_open_side_effect

                    with patch("pickle.load", return_value=pickle_metadata):
                        with patch("json.dump"):
                            service = FAISSVectorSearchService(index_path=temp_index_path)

                            # Should have loaded from pickle
                            assert service.index is not None

    def test_load_index_dimension_mismatch(self, temp_index_path):
        """Test loading index with dimension mismatch."""
        with patch("faiss.read_index") as mock_read:
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_read.return_value = mock_index

            Path(temp_index_path).touch()
            metadata_path = temp_index_path.replace(".bin", "_metadata.json")
            metadata = {
                "id_to_file_id": {0: 10},
                "file_id_to_index": {10: 0},
                "dimension": 256,  # Different from default 512
            }

            with patch("builtins.open", create=True):
                with patch("json.load", return_value=metadata):
                    with patch("os.path.exists", return_value=True):
                        service = FAISSVectorSearchService(
                            index_path=temp_index_path, dimension=512
                        )

                        # Should still load but with warning
                        assert service.index is not None

    def test_rebuild_index_empty_after_deletion(self, temp_index_path):
        """Test rebuild_index when all entries are deleted."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            initial_index = Mock()
            initial_index.ntotal = 3
            initial_index.reconstruct.side_effect = [
                np.random.randn(512).astype(np.float32),
                np.random.randn(512).astype(np.float32),
                np.random.randn(512).astype(np.float32),
            ]

            new_index = Mock()
            new_index.ntotal = 0

            mock_ip.side_effect = [initial_index, new_index]

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.index = initial_index
            # All entries deleted
            service.id_to_file_id = {0: None, 1: None, 2: None}
            service.file_id_to_index = {}

            with patch("builtins.open", create=True):
                with patch("json.dump"):
                    result = service.rebuild_index()

                    assert result is True
                    assert len(service.file_id_to_index) == 0

    def test_rebuild_index_with_ivf_upgrade(self, temp_index_path):
        """Test rebuild_index upgrades to IVF when appropriate."""
        with patch("faiss.IndexFlatIP") as mock_ip:
            initial_index = Mock()
            initial_index.ntotal = 250000
            vectors = np.random.randn(250000, 512).astype(np.float32)
            initial_index.reconstruct.side_effect = [
                vectors[i] for i in range(250000)
            ]

            mock_ip.return_value = initial_index

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.index = initial_index
            service.id_to_file_id = {i: i for i in range(250000)}
            service.file_id_to_index = {i: i for i in range(250000)}

            with (
                patch("faiss.IndexIVFPQ") as mock_ivf,
                patch("faiss.IndexFlatIP") as mock_quantizer,
                patch("builtins.open", create=True),
                patch("json.dump"),
            ):
                ivf_index = Mock()
                ivf_index.nlist = 500
                mock_ivf.return_value = ivf_index
                mock_quantizer.return_value = Mock()

                # Mock reconstruct_n to return all vectors at once
                def mock_reconstruct_n(start, end):
                    return vectors[start:end]

                initial_index.reconstruct_n = mock_reconstruct_n

                result = service.rebuild_index()

                # Should have attempted IVF upgrade
                assert result is True


class TestVectorSearchModuleFunctions:
    """Test module-level functions for vector search service."""

    def test_get_vector_search_service(self, temp_index_path):
        """Test get_vector_search_service creates singleton."""
        import src.services.vector_search as vs_module
        from src.services.vector_search import (
            get_vector_search_service,
            initialize_vector_search_service,
        )

        # Reset global state

        vs_module._vector_search_service = None

        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service1 = get_vector_search_service()
            service2 = get_vector_search_service()

            # Should return same instance
            assert service1 is service2

    def test_initialize_vector_search_service(self, temp_index_path):
        """Test initialize_vector_search_service creates new instance."""
        import src.services.vector_search as vs_module
        from src.services.vector_search import (
            get_vector_search_service,
            initialize_vector_search_service,
        )

        # Reset global state

        vs_module._vector_search_service = None

        with patch("faiss.IndexFlatIP") as mock_ip:
            mock_index = Mock()
            mock_index.ntotal = 0
            mock_ip.return_value = mock_index

            service1 = initialize_vector_search_service(
                index_path=temp_index_path, dimension=256
            )
            service2 = get_vector_search_service()

            # Should return same instance after initialization
            assert service1 is service2
            assert service1.dimension == 256
