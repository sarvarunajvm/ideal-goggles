import asyncio
import importlib
import sys
import unittest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
from fastapi import HTTPException, UploadFile

# We defer import of the module under test until we've set up mocks

class TestSearchCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Manually patch sys.modules to ensure reliability
        cls.original_modules = sys.modules.copy()

        # Create explicit mocks
        mock_vector_search = MagicMock()
        mock_vector_search.VectorSearchService = MagicMock()

        # Inject mocks
        sys.modules["src.core.logging_config"] = MagicMock()
        sys.modules["src.core.middleware"] = MagicMock()
        sys.modules["src.core.utils"] = MagicMock()
        sys.modules["src.db.connection"] = MagicMock()
        sys.modules["src.workers.embedding_worker"] = MagicMock()
        sys.modules["src.services.vector_search"] = mock_vector_search

        # Import (or reload) the module under test
        import src.api.search
        importlib.reload(src.api.search)
        cls.search_module = src.api.search

    @classmethod
    def tearDownClass(cls):
        # Restore original modules
        sys.modules.clear()
        sys.modules.update(cls.original_modules)

    def setUp(self):
        self.mock_db_manager = MagicMock()
        self.mock_logger = MagicMock()

        # Patch dependencies
        self.patches = [
            patch("src.api.search.get_database_manager", return_value=self.mock_db_manager),
            patch("src.api.search.get_logger", return_value=self.mock_logger),
            patch("src.api.search.DependencyChecker", MagicMock()),
            patch("src.api.search.get_request_id", return_value="test-req-id"),
            patch("src.api.search.log_slow_operation"),
            patch("src.api.search.log_error_with_context"),
        ]

        self.mock_deps = [p.start() for p in self.patches]
        self.mock_dependency_checker = self.mock_deps[2]

        # Setup DependencyChecker default behavior
        self.mock_dependency_checker.check_clip.return_value = (True, "OK")

    def tearDown(self):
        patch.stopall()

class TestTextSearch(TestSearchCoverage):
    def test_search_photos_all_filters(self):
        """Test text search with all filters enabled."""
        mock_rows = [
            (1, "/path/to/photos/photo1.jpg", "/path/to/photos", "photo1.jpg", "thumbs/1.jpg", "2023-01-01T12:00:00", 1.0, "match snippet"),
            (2, "/path/to/photos/photo2.jpg", "/path/to/photos", "photo2.jpg", None, None, 1.0, None)
        ]
        self.mock_db_manager.execute_query.return_value = mock_rows

        result = asyncio.run(self.search_module.search_photos(
            q="photo",
            from_date=date(2023, 1, 1),
            to_date=date(2023, 12, 31),
            folder="/path/to/photos",
            limit=10,
            offset=0
        ))

        self.assertEqual(result.total_matches, 2)
        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.items[0].file_id, 1)
        self.assertEqual(result.items[0].badges, ["filename", "folder"])

    def test_search_photos_no_query(self):
        """Test search without text query (browse mode)."""
        self.mock_db_manager.execute_query.return_value = []

        asyncio.run(self.search_module.search_photos(
            q=None,
            from_date=None,
            to_date=None,
            folder=None,
            limit=10,
            offset=0
        ))

        args = self.mock_db_manager.execute_query.call_args
        if args:
            query_sql = args[0][0]
            self.assertNotIn("LIKE", query_sql)
            self.assertNotIn("WHERE", query_sql)
        else:
            # If args is None, execute_query wasn't called.
            # This happens if implementation details changed or mocked incorrectly.
            # But in search.py, execute_query is called unconditionally in _execute_text_search
            # So this branch implies something is wrong with the mock wiring.
            self.fail("execute_query was not called")

    def test_search_photos_exception(self):
        """Test error handling in search."""
        self.mock_db_manager.execute_query.side_effect = Exception("DB Error")

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(self.search_module.search_photos(q="test"))

        self.assertEqual(cm.exception.status_code, 500)
        self.assertIn("Search failed", cm.exception.detail)

class TestSemanticSearch(TestSearchCoverage):
    def setUp(self):
        super().setUp()
        self.mock_embedding_worker_cls = MagicMock()
        self.mock_embedding_worker = MagicMock()
        self.mock_embedding_worker.is_available.return_value = True
        self.mock_embedding_worker.generate_text_embedding = AsyncMock(return_value=np.zeros((512,), dtype=np.float32))
        self.mock_embedding_worker_cls.return_value = self.mock_embedding_worker

        self.worker_patch = patch("src.workers.embedding_worker.CLIPEmbeddingWorker", self.mock_embedding_worker_cls)
        self.worker_patch.start()

    def tearDown(self):
        super().tearDown()

    def test_semantic_search_clip_unavailable(self):
        """Test semantic search when CLIP dependencies are missing."""
        self.mock_dependency_checker.check_clip.return_value = (False, "Missing")

        request = self.search_module.SemanticSearchRequest(text="test query")

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(self.search_module.semantic_search(request))

        self.assertEqual(cm.exception.status_code, 503)

    def test_semantic_search_worker_unavailable(self):
        """Test semantic search when worker fails to initialize."""
        self.mock_embedding_worker.is_available.return_value = False

        request = self.search_module.SemanticSearchRequest(text="test query")

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(self.search_module.semantic_search(request))

        self.assertEqual(cm.exception.status_code, 503)

    def test_semantic_search_embedding_failure(self):
        """Test semantic search when embedding generation fails."""
        self.mock_embedding_worker.generate_text_embedding.return_value = None

        request = self.search_module.SemanticSearchRequest(text="test query")

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(self.search_module.semantic_search(request))

        self.assertEqual(cm.exception.status_code, 500)

    @patch("src.api.search._execute_semantic_search")
    def test_semantic_search_success(self, mock_execute):
        """Test successful semantic search flow."""
        mock_execute.return_value = []

        request = self.search_module.SemanticSearchRequest(text="test query")
        asyncio.run(self.search_module.semantic_search(request))

        self.mock_embedding_worker.generate_text_embedding.assert_called_with("test query")
        mock_execute.assert_called_once()

class TestExecutionSemanticSearch(TestSearchCoverage):
    def test_faiss_search_success(self):
        """Test search using FAISS index."""
        # Configure global mock module
        mock_module = sys.modules["src.services.vector_search"]
        mock_service = mock_module.VectorSearchService.return_value

        # Reset index mock (might have been set to None by other tests)
        mock_service.index = MagicMock()
        mock_service.index.ntotal = 100
        mock_service.index.search.return_value = (np.array([[0.1, 0.2]]), np.array([[0, 1]]))
        mock_service.id_map = {0: 101, 1: 102}

        self.mock_db_manager.execute_query.return_value = [
            (101, "/p/1.jpg", "/p", "1.jpg", "t/1.jpg", "2023-01-01"),
            (102, "/p/2.jpg", "/p", "2.jpg", "t/2.jpg", "2023-01-02")
        ]

        query_vec = np.random.rand(512).astype(np.float32)

        results = asyncio.run(self.search_module._execute_semantic_search(
            self.mock_db_manager, query_vec, top_k=10
        ))

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].file_id, 101)
        self.assertEqual(results[0].score, 0.1)
        self.assertEqual(results[0].badges, ["semantic"])

    def test_brute_force_fallback(self):
        """Test fallback to brute force when FAISS is unavailable or empty."""
        mock_module = sys.modules["src.services.vector_search"]
        mock_service = mock_module.VectorSearchService.return_value
        mock_service.index = None

        self.mock_db_manager.execute_query.side_effect = [
            [(10,)],
            [
                (1, b"blob", "/p/1.jpg", "/p", "1.jpg", "t/1.jpg", "2023-01-01"),
                (2, b"blob", "/p/2.jpg", "/p", "2.jpg", "t/2.jpg", "2023-01-02")
            ]
        ]

        with patch("src.models.embedding.Embedding._blob_to_numpy") as mock_blob_conv:
            vec1 = np.zeros(512, dtype=np.float32)
            vec1[0] = 1.0
            vec2 = np.zeros(512, dtype=np.float32)
            vec2[1] = 1.0
            mock_blob_conv.side_effect = [vec1, vec2]

            query_vec = np.zeros(512, dtype=np.float32)
            query_vec[0] = 1.0

            results = asyncio.run(self.search_module._execute_semantic_search(
                self.mock_db_manager, query_vec, top_k=10
            ))

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].file_id, 1)
            self.assertAlmostEqual(results[0].score, 1.0)

    def test_faiss_import_error(self):
        """Test brute force fallback on FAISS import error."""
        # Store original module mock
        original_module = sys.modules["src.services.vector_search"]

        # Create a broken module that raises ImportError on attribute access
        class BrokenModule:
            @property
            def VectorSearchService(self):  # noqa: N802
                raise ImportError("FAISS Missing")

        # Replace module in sys.modules
        sys.modules["src.services.vector_search"] = BrokenModule()

        try:
            self.mock_db_manager.execute_query.side_effect = [[(0,)]]

            query_vec = np.zeros(512, dtype=np.float32)
            asyncio.run(self.search_module._execute_semantic_search(self.mock_db_manager, query_vec, top_k=10))

            self.assertTrue(self.mock_db_manager.execute_query.called)
        finally:
            # Restore original module mock
            sys.modules["src.services.vector_search"] = original_module

class TestImageSearch(TestSearchCoverage):
    def setUp(self):
        super().setUp()
        self.mock_embedding_worker_cls = MagicMock()
        self.mock_embedding_worker = MagicMock()
        self.mock_embedding_worker.is_available.return_value = True
        self.mock_embedding_worker_cls.return_value = self.mock_embedding_worker

        self.worker_patch = patch("src.workers.embedding_worker.CLIPEmbeddingWorker", self.mock_embedding_worker_cls)
        self.worker_patch.start()

        self.photo_patch = patch("src.models.photo.Photo", MagicMock())
        self.photo_patch.start()

    def tearDown(self):
        super().tearDown()

    def test_image_search_invalid_file(self):
        """Test validation for non-image files."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "application/pdf"

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(self.search_module.image_search(file, top_k=10))

        self.assertEqual(cm.exception.status_code, 400)

    def test_image_search_success(self):
        """Test successful image search."""
        file = MagicMock(spec=UploadFile)
        file.content_type = "image/jpeg"
        file.filename = "test.jpg"
        file.read = AsyncMock(return_value=b"fake-content")

        mock_emb_obj = MagicMock()
        mock_emb_obj.clip_vector = np.zeros(512, dtype=np.float32)

        self.mock_embedding_worker.generate_embedding = AsyncMock(return_value=mock_emb_obj)

        with patch("src.api.search._execute_image_search", return_value=[]) as mock_exec:
            asyncio.run(self.search_module.image_search(file, top_k=10))
            mock_exec.assert_called_once()

class TestFaceSearch(TestSearchCoverage):
    def test_face_search_disabled(self):
        """Test face search when config disables it."""
        with patch("src.api.config._get_config_from_db", return_value={"face_search_enabled": False}):
            request = self.search_module.FaceSearchRequest(person_id=1)
            with self.assertRaises(HTTPException) as cm:
                asyncio.run(self.search_module.face_search(request))
            self.assertEqual(cm.exception.status_code, 403)

    def test_face_search_person_not_found(self):
        """Test searching for non-existent person."""
        with patch("src.api.config._get_config_from_db", return_value={"face_search_enabled": True}):
            self.mock_db_manager.execute_query.return_value = []

            request = self.search_module.FaceSearchRequest(person_id=1)
            with self.assertRaises(HTTPException) as cm:
                asyncio.run(self.search_module.face_search(request))
            self.assertEqual(cm.exception.status_code, 404)

    def test_face_search_success(self):
        """Test successful face search."""
        with patch("src.api.config._get_config_from_db", return_value={"face_search_enabled": True}):
            self.mock_db_manager.execute_query.side_effect = [
                [(1, "John", b"vec", 1)],
                [
                    (10, 0.95, "/p.jpg", "/f", "p.jpg", "t.jpg", "2023-01-01")
                ]
            ]

            request = self.search_module.FaceSearchRequest(person_id=1)
            result = asyncio.run(self.search_module.face_search(request))

            self.assertEqual(len(result.items), 1)
            self.assertEqual(result.items[0].file_id, 10)
            self.assertEqual(result.items[0].score, 0.95)

class TestGetOriginalPhoto(TestSearchCoverage):
    def test_photo_not_in_db(self):
        """Test requesting photo ID not in DB."""
        self.mock_db_manager.execute_query.return_value = []

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(self.search_module.get_original_photo(999))
        self.assertEqual(cm.exception.status_code, 404)

    @patch("os.path.exists", return_value=False)
    def test_file_not_found_on_disk(self, _):
        """Test requesting photo that is missing from disk."""
        self.mock_db_manager.execute_query.return_value = [("/missing/path.jpg",)]

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(self.search_module.get_original_photo(1))
        self.assertEqual(cm.exception.status_code, 404)

    @patch("os.path.exists", return_value=True)
    def test_success(self, _):
        """Test successful file response."""
        self.mock_db_manager.execute_query.return_value = [("/real/path.jpg",)]

        with patch("src.api.search.FileResponse", MagicMock()) as mock_response:
            asyncio.run(self.search_module.get_original_photo(1))
            mock_response.assert_called_with(
                path="/real/path.jpg",
                media_type="image/jpeg",
                filename="path.jpg"
            )
