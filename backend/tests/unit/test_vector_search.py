"""Unit tests for vector search service."""

import os
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

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

    @pytest.fixture
    def mock_faiss(self):
        """Mock faiss module."""
        with patch("src.services.vector_search.faiss") as mock:
            # Mock index classes
            mock.IndexFlatIP = Mock(return_value=Mock())
            mock.IndexFlatL2 = Mock(return_value=Mock())
            mock.IndexIVFFlat = Mock(return_value=Mock())
            yield mock

    def test_initialization_new_index(self, temp_index_path, mock_faiss):
        """Test initialization with new index."""
        service = FAISSVectorSearchService(index_path=temp_index_path, dimension=512)

        assert service.dimension == 512
        assert service.index_path == temp_index_path
        assert service.metadata_path == temp_index_path.replace(".bin", "_metadata.pkl")
        assert service.index is not None
        assert service.id_to_file_id == {}
        assert service.file_id_to_index == {}
        mock_faiss.IndexFlatIP.assert_called_once_with(512)

    def test_initialization_load_existing(self, temp_index_path, mock_faiss):
        """Test loading existing index."""
        # Create mock existing files
        Path(temp_index_path).touch()
        metadata_path = temp_index_path.replace(".bin", "_metadata.pkl")
        Path(metadata_path).touch()

        with patch.object(
            FAISSVectorSearchService, "_load_index"
        ) as mock_load:
            mock_index = Mock()
            mock_index.ntotal = 100
            mock_load.return_value = None

            service = FAISSVectorSearchService(index_path=temp_index_path)
            service.index = mock_index

            mock_load.assert_called_once()

    def test_initialization_no_faiss(self, temp_index_path):
        """Test initialization when FAISS is not available."""
        with patch("src.services.vector_search.faiss", side_effect=ImportError):
            with pytest.raises(RuntimeError, match="FAISS not available"):
                FAISSVectorSearchService(index_path=temp_index_path)

    def test_create_new_index_clip_dimension(self, temp_index_path, mock_faiss):
        """Test creating new index with CLIP dimension."""
        service = FAISSVectorSearchService(index_path=temp_index_path, dimension=512)
        mock_faiss.IndexFlatIP.assert_called_with(512)

    def test_create_new_index_other_dimension(self, temp_index_path, mock_faiss):
        """Test creating new index with non-CLIP dimension."""
        service = FAISSVectorSearchService(index_path=temp_index_path, dimension=256)
        mock_faiss.IndexFlatL2.assert_called_with(256)

    @patch("src.services.vector_search.faiss")
    def test_add_single_vector(self, mock_faiss, temp_index_path):
        """Test adding a single vector."""
        mock_index = Mock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        vector = np.random.randn(512).astype(np.float32)

        service.add(file_id=1, vector=vector)

        # Check vector was normalized and added
        mock_index.add.assert_called_once()
        assert 1 in service.file_id_to_index
        assert service.unsaved_additions == 1

    @patch("src.services.vector_search.faiss")
    def test_add_multiple_vectors(self, mock_faiss, temp_index_path):
        """Test adding multiple vectors at once."""
        mock_index = Mock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        vectors = np.random.randn(5, 512).astype(np.float32)
        file_ids = [1, 2, 3, 4, 5]

        service.add_batch(file_ids=file_ids, vectors=vectors)

        mock_index.add.assert_called_once()
        for file_id in file_ids:
            assert file_id in service.file_id_to_index

    @patch("src.services.vector_search.faiss")
    def test_search_basic(self, mock_faiss, temp_index_path):
        """Test basic vector search."""
        mock_index = Mock()
        mock_index.ntotal = 10
        mock_index.search.return_value = (
            np.array([[0.9, 0.8, 0.7]]),
            np.array([[0, 1, 2]]),
        )
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        # Add some mappings
        service.id_to_file_id = {0: 10, 1: 20, 2: 30}

        query_vector = np.random.randn(512).astype(np.float32)
        results = service.search(query_vector, k=3)

        assert len(results) == 3
        assert results[0]["file_id"] == 10
        assert results[0]["score"] == pytest.approx(0.9)
        assert results[1]["file_id"] == 20
        assert results[2]["file_id"] == 30

    @patch("src.services.vector_search.faiss")
    def test_search_empty_index(self, mock_faiss, temp_index_path):
        """Test searching in empty index."""
        mock_index = Mock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        query_vector = np.random.randn(512).astype(np.float32)

        results = service.search(query_vector, k=5)
        assert results == []

    @patch("src.services.vector_search.faiss")
    def test_update_vector(self, mock_faiss, temp_index_path):
        """Test updating an existing vector."""
        mock_index = Mock()
        mock_index.ntotal = 1
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        service.file_id_to_index = {1: 0}
        service.id_to_file_id = {0: 1}

        new_vector = np.random.randn(512).astype(np.float32)
        service.update(file_id=1, vector=new_vector)

        # Should remove and re-add
        mock_index.remove_ids.assert_called_once()
        mock_index.add.assert_called_once()

    @patch("src.services.vector_search.faiss")
    def test_remove_vector(self, mock_faiss, temp_index_path):
        """Test removing a vector."""
        mock_index = Mock()
        mock_index.ntotal = 1
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        service.file_id_to_index = {1: 0}
        service.id_to_file_id = {0: 1}

        success = service.remove(file_id=1)

        assert success
        mock_index.remove_ids.assert_called_once()
        assert 1 not in service.file_id_to_index
        assert 0 not in service.id_to_file_id

    @patch("src.services.vector_search.faiss")
    def test_remove_nonexistent_vector(self, mock_faiss, temp_index_path):
        """Test removing a vector that doesn't exist."""
        mock_index = Mock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        success = service.remove(file_id=999)

        assert not success
        mock_index.remove_ids.assert_not_called()

    @patch("src.services.vector_search.faiss")
    def test_save_index(self, mock_faiss, temp_index_path):
        """Test saving index to disk."""
        mock_index = Mock()
        mock_index.ntotal = 5
        mock_faiss.IndexFlatIP.return_value = mock_index
        mock_faiss.write_index = Mock()

        service = FAISSVectorSearchService(index_path=temp_index_path)
        service.id_to_file_id = {0: 10, 1: 20}

        with patch("builtins.open", create=True) as mock_open:
            with patch("pickle.dump") as mock_pickle:
                service.save()

                mock_faiss.write_index.assert_called_once_with(
                    mock_index, temp_index_path
                )
                mock_pickle.assert_called_once()

    @patch("src.services.vector_search.faiss")
    def test_load_index(self, mock_faiss, temp_index_path):
        """Test loading index from disk."""
        mock_index = Mock()
        mock_index.ntotal = 5
        mock_faiss.read_index.return_value = mock_index

        # Create metadata file
        metadata = {
            "id_to_file_id": {0: 10, 1: 20},
            "file_id_to_index": {10: 0, 20: 1},
        }
        metadata_path = temp_index_path.replace(".bin", "_metadata.pkl")

        with patch("builtins.open", create=True):
            with patch("pickle.load", return_value=metadata):
                service = FAISSVectorSearchService(index_path=temp_index_path)
                service._load_index()

                assert service.index == mock_index
                assert service.id_to_file_id == {0: 10, 1: 20}
                assert service.file_id_to_index == {10: 0, 20: 1}

    @patch("src.services.vector_search.faiss")
    def test_clear_index(self, mock_faiss, temp_index_path):
        """Test clearing the index."""
        mock_index = Mock()
        mock_index.ntotal = 5
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        service.id_to_file_id = {0: 10, 1: 20}
        service.file_id_to_index = {10: 0, 20: 1}

        service.clear()

        # Should create new index
        assert service.id_to_file_id == {}
        assert service.file_id_to_index == {}

    @patch("src.services.vector_search.faiss")
    def test_auto_save_threshold(self, mock_faiss, temp_index_path):
        """Test auto-save after threshold additions."""
        mock_index = Mock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        service.auto_save_threshold = 2  # Low threshold for testing

        with patch.object(service, "save") as mock_save:
            # Add vectors up to threshold
            for i in range(3):
                vector = np.random.randn(512).astype(np.float32)
                service.add(file_id=i, vector=vector)

            # Should trigger auto-save
            mock_save.assert_called()

    @patch("src.services.vector_search.faiss")
    def test_batch_search(self, mock_faiss, temp_index_path):
        """Test batch vector search."""
        mock_index = Mock()
        mock_index.ntotal = 10
        mock_index.search.return_value = (
            np.array([[0.9, 0.8], [0.85, 0.75]]),
            np.array([[0, 1], [2, 3]]),
        )
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        service.id_to_file_id = {0: 10, 1: 20, 2: 30, 3: 40}

        query_vectors = np.random.randn(2, 512).astype(np.float32)
        results = service.search_batch(query_vectors, k=2)

        assert len(results) == 2
        assert len(results[0]) == 2
        assert results[0][0]["file_id"] == 10
        assert results[1][0]["file_id"] == 30

    @patch("src.services.vector_search.faiss")
    def test_get_statistics(self, mock_faiss, temp_index_path):
        """Test getting index statistics."""
        mock_index = Mock()
        mock_index.ntotal = 100
        mock_index.d = 512
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        service.unsaved_additions = 5

        stats = service.get_statistics()

        assert stats["total_vectors"] == 100
        assert stats["dimension"] == 512
        assert stats["index_type"] == "IndexFlatIP"
        assert stats["unsaved_additions"] == 5

    @patch("src.services.vector_search.faiss")
    def test_thread_safety(self, mock_faiss, temp_index_path):
        """Test thread safety with concurrent operations."""
        import threading

        mock_index = Mock()
        mock_index.ntotal = 0
        mock_faiss.IndexFlatIP.return_value = mock_index

        service = FAISSVectorSearchService(index_path=temp_index_path)
        errors = []

        def add_vectors():
            try:
                for i in range(10):
                    vector = np.random.randn(512).astype(np.float32)
                    service.add(file_id=i, vector=vector)
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = [threading.Thread(target=add_vectors) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0  # No errors should occur