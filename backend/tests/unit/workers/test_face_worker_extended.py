"""Additional coverage tests for backend/src/workers/face_worker.py."""

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.models.person import Face, Person
from src.workers.face_worker import FaceDetectionWorker, FaceSearchEngine


class TestFaceWorkerCoverage:
    """Tests for FaceDetectionWorker coverage."""

    def test_initialize_import_error(self):
        """Test initialization with ImportError."""
        with patch.dict("sys.modules", {"insightface": None}):
            # We need to ensure import raises ImportError
            # Since we can't easily make 'import insightface' raise ImportError if it's already imported or None
            # We'll use a side effect on builtins.__import__ ONLY for insightface

            orig_import = __import__
            def mock_import(name, *args, **kwargs):
                if name == "insightface":
                    raise ImportError("No module named insightface")
                return orig_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                worker = FaceDetectionWorker()
                assert worker.face_app is None

    def test_initialize_generic_exception(self):
        """Test initialization with generic Exception."""
        with patch("insightface.app.FaceAnalysis", side_effect=Exception("Init Failed")):
            worker = FaceDetectionWorker()
            assert worker.face_app is None

    def test_mock_face_detection_logic(self):
        """Test the built-in mock logic for test files."""
        # This targets lines 79-102
        worker = FaceDetectionWorker()

        mock_photo = MagicMock()
        mock_photo.filename = "test-image.jpg"
        mock_photo.path = "/tmp/test-image.jpg"

        # We need to run async method
        import asyncio
        loop = asyncio.new_event_loop()
        faces = loop.run_until_complete(worker.detect_faces(mock_photo))
        loop.close()

        assert len(faces) == 1
        assert faces[0].confidence == 0.99

    def test_detect_faces_sync_exception(self):
        """Test synchronous detection exception handling."""
        worker = FaceDetectionWorker()
        worker.face_app = MagicMock()

        # Mock cv2 to raise exception
        mock_cv2 = MagicMock()
        mock_cv2.imread.side_effect = Exception("CV2 Error")

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            detections = worker._detect_faces_sync("/path/to/img.jpg")
            assert detections == []

    @pytest.mark.asyncio
    async def test_process_batch_partial_failure(self):
        """Test batch processing with some failures."""
        worker = FaceDetectionWorker()

        # Mock detect_faces to succeed for one, fail for another
        async def mock_detect(photo):
            if photo.id == 1:
                return [MagicMock(spec=Face)]
            raise Exception("Detection Failed")

        with patch.object(worker, "detect_faces", side_effect=mock_detect):
            photos = [MagicMock(id=1, path="1.jpg"), MagicMock(id=2, path="2.jpg")]
            results = await worker.process_batch(photos)

            assert len(results) == 2
            assert len(results[0]) == 1
            assert results[1] == []


class TestFaceSearchEngineCoverage:
    """Tests for FaceSearchEngine coverage."""

    @pytest.mark.asyncio
    async def test_search_by_person_success(self):
        """Test search_by_person."""
        engine = FaceSearchEngine()

        # Create person and faces
        person = MagicMock(spec=Person)
        person.face_vector = np.array([0.1]*512, dtype=np.float32)
        person.id = 1

        face = MagicMock(spec=Face)
        face.face_vector = np.array([0.1]*512, dtype=np.float32)
        face.file_id = 100
        face.person_id = 1
        face.confidence = 0.9

        # Mock similarity calculation
        face.similarity_to_person.return_value = 0.9

        matches = await engine.search_by_person(person, [face])
        assert len(matches) == 1
        assert matches[0]["file_id"] == 100

    @pytest.mark.asyncio
    async def test_search_by_person_no_vector(self):
        """Test search_by_person with missing vectors."""
        engine = FaceSearchEngine()

        person = MagicMock(spec=Person)
        person.face_vector = None

        matches = await engine.search_by_person(person, [])
        assert matches == []

        person.face_vector = np.array([0.1]*512)
        face = MagicMock(spec=Face)
        face.face_vector = None

        matches = await engine.search_by_person(person, [face])
        assert matches == []

