"""Unit tests for search services."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from src.services.rank_fusion import (
    FusionWeights,
    RankFusionService,
    SearchResult,
    SearchType,
)
from src.services.text_search import TextSearchService
from src.services.vector_search import FAISSVectorSearchService


class TestTextSearchService(unittest.TestCase):
    """Test cases for TextSearchService."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

        # Mock database manager
        self.mock_db_manager = MagicMock()

        with patch("src.services.text_search.get_database_manager") as mock_get_db_manager:
            mock_get_db_manager.return_value = self.mock_db_manager
            self.service = TextSearchService()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test service initialization."""
        self.assertIsInstance(self.service, TextSearchService)
        self.assertIsNotNone(self.service.db_manager)

    def test_process_search_query_basic(self):
        """Test basic query preprocessing."""
        query = "Hello World Test"
        processed = self.service._process_search_query(query)

        self.assertIsInstance(processed, str)
        self.assertTrue(len(processed) > 0)
        # Should contain AND operator for FTS5
        self.assertIn("AND", processed)

    def test_process_search_query_special_chars(self):
        """Test query preprocessing with special characters."""
        query = "test@example.com & special-chars_123"
        processed = self.service._process_search_query(query)

        # Should handle special characters gracefully
        self.assertIsInstance(processed, str)

    def test_process_search_query_empty(self):
        """Test preprocessing of empty query."""
        query = ""
        processed = self.service._process_search_query(query)

        self.assertEqual(processed, "")

    def test_process_search_query_whitespace_only(self):
        """Test preprocessing of whitespace-only query."""
        query = "   \n\t  "
        processed = self.service._process_search_query(query)

        self.assertEqual(processed.strip(), "")

    def test_search_photos_basic(self):
        """Test basic photo search."""
        # Mock database response - format matches actual query result
        mock_search_results = [
            (1, "/path/photo1.jpg", "/path", "photo1.jpg", 12345, 1234567890, 1234567891, "sha1hash",
             "/thumbs/photo1.jpg", "2023-01-01 12:00:00", "Canon", "EOS R5", "sample text", 0.95, 1.2),
        ]
        mock_count_results = [(1,)]  # Count query result

        # Mock execute_query to return different results for different calls
        self.mock_db_manager.execute_query.side_effect = [mock_search_results, mock_count_results]

        results = self.service.search_photos("photo")

        self.assertIsInstance(results, dict)
        self.assertIn("results", results)
        self.assertIn("total_count", results)
        self.assertEqual(len(results["results"]), 1)
        self.assertEqual(results["total_count"], 1)

        # Verify database was called twice (search + count)
        self.assertEqual(self.mock_db_manager.execute_query.call_count, 2)

    def test_search_photos_with_folders(self):
        """Test photo search with folder filtering."""
        mock_search_results = [
            (1, "/projects/wedding/photo1.jpg", "/projects/wedding", "photo1.jpg", 12345, 1234567890, 1234567891, "sha1hash",
             "/thumbs/photo1.jpg", "2023-01-01 12:00:00", "Canon", "EOS R5", "sample text", 0.95, 1.2),
        ]
        mock_count_results = [(1,)]

        self.mock_db_manager.execute_query.side_effect = [mock_search_results, mock_count_results]

        results = self.service.search_photos("wedding", folders=["/projects/wedding"])

        self.assertIsInstance(results, dict)
        self.assertEqual(len(results["results"]), 1)
        self.assertIn("wedding", results["results"][0]["folder"])

    def test_search_photos_with_date_range(self):
        """Test photo search with date range filtering."""
        from datetime import date

        mock_search_results = [
            (1, "/path/scan1.jpg", "/path", "scan1.jpg", 12345, 1234567890, 1234567891, "sha1hash",
             "/thumbs/scan1.jpg", "2023-06-15 12:00:00", "Canon", "EOS R5", "matching text snippet", 0.95, 1.2),
        ]
        mock_count_results = [(1,)]

        self.mock_db_manager.execute_query.side_effect = [mock_search_results, mock_count_results]

        results = self.service.search_photos(
            "matching text",
            date_range=(date(2023, 1, 1), date(2023, 12, 31))
        )

        self.assertIsInstance(results, dict)
        self.assertEqual(len(results["results"]), 1)
        self.assertIn("matching text snippet", results["results"][0]["snippet"] or "")

    def test_search_photos_pagination(self):
        """Test search result pagination."""
        mock_search_results = [
            (i, f"/path/photo{i}.jpg", "/path", f"photo{i}.jpg", 12345, 1234567890, 1234567891, f"sha1hash{i}",
             f"/thumbs/photo{i}.jpg", "2023-01-01 12:00:00", "Canon", "EOS R5", "sample text", 0.95, 1.2)
            for i in range(1, 21)  # 20 results
        ]
        mock_count_results = [(100,)]  # Total count

        self.mock_db_manager.execute_query.side_effect = [mock_search_results, mock_count_results]

        results = self.service.search_photos("test", limit=20, offset=20)

        self.assertIsInstance(results, dict)
        self.assertEqual(len(results["results"]), 20)
        self.assertEqual(results["total_count"], 100)
        self.assertEqual(results["limit"], 20)
        self.assertEqual(results["offset"], 20)

    def test_get_search_suggestions(self):
        """Test search suggestions functionality."""
        mock_filename_results = [("vacation_photo1.jpg",), ("vacation_photo2.jpg",)]
        mock_camera_results = [("Canon EOS R5",), ("Nikon D850",)]

        # Mock execute_query to return different results for different calls
        self.mock_db_manager.execute_query.side_effect = [mock_filename_results, mock_camera_results]

        results = self.service.get_search_suggestions("vacation")

        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
        self.assertIn("vacation_photo1.jpg", results)

    def test_get_popular_searches(self):
        """Test popular searches functionality."""
        mock_camera_results = [("Canon EOS R5", 50), ("Nikon D850", 30)]
        mock_ext_results = [(".jpg", 1000), (".png", 200)]

        self.mock_db_manager.execute_query.side_effect = [mock_camera_results, mock_ext_results]

        results = self.service.get_popular_searches(limit=5)

        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["term"], "Canon EOS R5")
        self.assertEqual(results[0]["type"], "camera_model")

    def test_get_search_statistics(self):
        """Test search statistics functionality."""
        mock_stats_results = [(1000, 800, 950, 150.5)]

        self.mock_db_manager.execute_query.return_value = mock_stats_results

        results = self.service.get_search_statistics()

        self.assertIsInstance(results, dict)
        self.assertIn("total_photos", results)
        self.assertIn("photos_with_ocr", results)
        self.assertEqual(results["total_photos"], 1000)


try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

@pytest.mark.skipif(
    not FAISS_AVAILABLE,
    reason="FAISS library not installed"
)
class TestFAISSVectorSearchService(unittest.TestCase):
    """Test cases for FAISSVectorSearchService."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.index_path = os.path.join(self.temp_dir, "test_index.bin")

        # Create service with test index path
        self.service = FAISSVectorSearchService(index_path=self.index_path)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test service initialization."""
        self.assertIsInstance(self.service, FAISSVectorSearchService)
        self.assertEqual(self.service.dimension, 512)
        self.assertIsNotNone(self.service.index)

    def test_add_vector_valid(self):
        """Test adding a valid vector."""
        vector = np.random.rand(512).astype(np.float32)
        file_id = 1

        success = self.service.add_vector(file_id, vector)

        self.assertTrue(success)
        self.assertEqual(self.service.index.ntotal, 1)
        self.assertIn(file_id, self.service.file_id_to_index)

    def test_add_vector_invalid_dimension(self):
        """Test adding vector with wrong dimension."""
        vector = np.random.rand(256).astype(np.float32)  # Wrong dimension
        file_id = 1

        success = self.service.add_vector(file_id, vector)

        self.assertFalse(success)
        self.assertEqual(self.service.index.ntotal, 0)

    def test_add_vector_normalization(self):
        """Test vector normalization during addition."""
        # Create unnormalized vector
        vector = np.array([3.0, 4.0] + [0.0] * 510, dtype=np.float32)  # Magnitude = 5
        file_id = 1

        success = self.service.add_vector(file_id, vector)

        self.assertTrue(success)

        # Retrieve vector and check normalization
        retrieved = self.service.index.reconstruct(0)
        magnitude = np.linalg.norm(retrieved)
        self.assertAlmostEqual(magnitude, 1.0, places=5)

    def test_remove_vector(self):
        """Test vector removal."""
        vector = np.random.rand(512).astype(np.float32)
        file_id = 1

        # Add vector
        self.service.add_vector(file_id, vector)
        self.assertEqual(self.service.index.ntotal, 1)

        # Remove vector
        success = self.service.remove_vector(file_id)

        self.assertTrue(success)
        self.assertNotIn(file_id, self.service.file_id_to_index)

    def test_remove_nonexistent_vector(self):
        """Test removing a vector that doesn't exist."""
        success = self.service.remove_vector(999)

        self.assertFalse(success)

    def test_search_similar_empty_index(self):
        """Test similarity search on empty index."""
        query_vector = np.random.rand(512).astype(np.float32)

        results = self.service.search_similar(query_vector, k=5)

        self.assertEqual(len(results), 0)

    def test_search_similar_with_results(self):
        """Test similarity search with results."""
        # Add test vectors
        vectors = [np.random.rand(512).astype(np.float32) for _ in range(10)]
        for i, vector in enumerate(vectors):
            self.service.add_vector(i + 1, vector)

        # Search with one of the added vectors
        query_vector = vectors[0]
        results = self.service.search_similar(query_vector, k=5)

        self.assertGreater(len(results), 0)
        self.assertTrue(len(results) <= 5)

        # First result should be the exact match
        self.assertEqual(results[0]["file_id"], 1)
        self.assertAlmostEqual(results[0]["distance"], 0.0, places=5)

    def test_search_similar_k_parameter(self):
        """Test k parameter in similarity search."""
        # Add test vectors
        for i in range(10):
            vector = np.random.rand(512).astype(np.float32)
            self.service.add_vector(i + 1, vector)

        query_vector = np.random.rand(512).astype(np.float32)

        # Test different k values
        for k in [1, 3, 5, 10]:
            results = self.service.search_similar(query_vector, k=k)
            self.assertTrue(len(results) <= k)

    def test_upgrade_to_ivf_threshold(self):
        """Test automatic upgrade to IVF index."""
        # Mock large number of vectors to trigger upgrade
        with patch.object(self.service, "_should_use_ivf", return_value=True):
            with patch.object(self.service, "_upgrade_to_ivf_index") as mock_upgrade:
                vector = np.random.rand(512).astype(np.float32)
                self.service.add_vector(1, vector)

                # Should trigger upgrade check
                mock_upgrade.assert_called_once()

    def test_save_and_load_index(self):
        """Test saving and loading index."""
        # Add test data
        vectors = [np.random.rand(512).astype(np.float32) for _ in range(5)]
        for i, vector in enumerate(vectors):
            self.service.add_vector(i + 1, vector)

        # Save index
        success = self.service.save_index()
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.service.index_path))

        # Create new service and load
        new_service = FAISSVectorSearchService(index_path=self.index_path)

        # Verify data was loaded
        self.assertEqual(new_service.index.ntotal, 5)
        self.assertEqual(len(new_service.file_id_to_index), 5)

    def test_bulk_operations(self):
        """Test bulk vector operations."""
        # Test bulk addition
        vectors = np.random.rand(100, 512).astype(np.float32)
        file_ids = list(range(1, 101))

        for file_id, vector in zip(file_ids, vectors, strict=False):
            success = self.service.add_vector(file_id, vector)
            self.assertTrue(success)

        self.assertEqual(self.service.index.ntotal, 100)

        # Test bulk search
        query_vector = np.random.rand(512).astype(np.float32)
        results = self.service.search_similar(query_vector, k=10)

        self.assertEqual(len(results), 10)
        self.assertTrue(all(r["distance"] >= 0 for r in results))


class TestRankFusionService(unittest.TestCase):
    """Test cases for RankFusionService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = RankFusionService()

    def test_initialization(self):
        """Test service initialization."""
        self.assertIsInstance(self.service, RankFusionService)

    def test_fuse_results_empty(self):
        """Test fusion with empty result sets."""
        result_sets = {}
        fused = self.service.fuse_results(result_sets)

        self.assertEqual(len(fused), 0)

    def test_fuse_results_single_set(self):
        """Test fusion with single result set."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(file_id=1, score=0.9, search_type=SearchType.TEXT, metadata={}),
                SearchResult(file_id=2, score=0.8, search_type=SearchType.TEXT, metadata={}),
                SearchResult(file_id=3, score=0.7, search_type=SearchType.TEXT, metadata={}),
            ]
        }

        fused = self.service.fuse_results(result_sets)

        self.assertEqual(len(fused), 3)
        self.assertEqual(fused[0].file_id, 1)
        self.assertGreater(fused[0].score, fused[1].score)

    def test_fuse_results_multiple_sets(self):
        """Test fusion with multiple result sets."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(file_id=1, score=0.9, search_type=SearchType.TEXT, metadata={}),
                SearchResult(file_id=2, score=0.7, search_type=SearchType.TEXT, metadata={}),
            ],
            SearchType.SEMANTIC: [
                SearchResult(file_id=2, score=0.8, search_type=SearchType.SEMANTIC, metadata={}),
                SearchResult(file_id=3, score=0.6, search_type=SearchType.SEMANTIC, metadata={}),
            ],
        }

        fused = self.service.fuse_results(result_sets)

        # File 2 appears in both sets, should be ranked higher due to RRF
        file_2_result = next(r for r in fused if r.file_id == 2)
        file_1_result = next(r for r in fused if r.file_id == 1)

        # In RRF, file appearing in multiple sets gets better ranking
        self.assertIsNotNone(file_2_result)
        self.assertIsNotNone(file_1_result)

    def test_fuse_results_with_weights(self):
        """Test fusion with custom weights."""
        result_sets = {
            SearchType.TEXT: [SearchResult(file_id=1, score=0.5, search_type=SearchType.TEXT, metadata={})],
            SearchType.SEMANTIC: [SearchResult(file_id=2, score=0.9, search_type=SearchType.SEMANTIC, metadata={})],
        }

        # Custom weights favoring text over semantic
        weights = FusionWeights(text=1.0, semantic=0.1)
        fused = self.service.fuse_results(result_sets, weights=weights)

        self.assertEqual(len(fused), 2)
        # Both results should be present
        file_ids = [r.file_id for r in fused]
        self.assertIn(1, file_ids)
        self.assertIn(2, file_ids)

    def test_different_fusion_methods(self):
        """Test different fusion methods."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(file_id=1, score=0.9, search_type=SearchType.TEXT, metadata={}),
                SearchResult(file_id=2, score=0.7, search_type=SearchType.TEXT, metadata={}),
            ],
            SearchType.SEMANTIC: [
                SearchResult(file_id=2, score=0.8, search_type=SearchType.SEMANTIC, metadata={}),
                SearchResult(file_id=3, score=0.6, search_type=SearchType.SEMANTIC, metadata={}),
            ],
        }

        # Test RRF method
        fused_rrf = self.service.fuse_results(result_sets, method="rrf")
        self.assertGreater(len(fused_rrf), 0)

        # Test weighted sum method
        fused_ws = self.service.fuse_results(result_sets, method="weighted_sum")
        self.assertGreater(len(fused_ws), 0)

        # Test borda count method
        fused_bc = self.service.fuse_results(result_sets, method="borda_count")
        self.assertGreater(len(fused_bc), 0)

    def test_metadata_preservation(self):
        """Test that metadata is preserved during fusion."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(
                    file_id=1,
                    score=0.9,
                    search_type=SearchType.TEXT,
                    metadata={"snippet": "text match", "source": "filename"}
                ),
            ],
            SearchType.IMAGE: [
                SearchResult(
                    file_id=1,
                    score=0.8,
                    search_type=SearchType.IMAGE,
                    metadata={"similarity": 0.85, "source": "visual"}
                ),
            ],
        }

        fused = self.service.fuse_results(result_sets)

        self.assertEqual(len(fused), 1)
        result = fused[0]
        self.assertEqual(result.file_id, 1)
        # Metadata should be combined
        self.assertIn("snippet", result.metadata)
        self.assertIn("similarity", result.metadata)


if __name__ == "__main__":
    unittest.main()
