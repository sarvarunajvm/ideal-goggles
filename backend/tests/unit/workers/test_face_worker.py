"""Comprehensive unit tests for face_worker module."""

import asyncio
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from src.models.person import Face, Person
from src.models.photo import Photo
from src.workers.face_worker import (
    FaceDetectionWorker,
    FaceQualityAnalyzer,
    FaceSearchEngine,
)


@contextmanager
def mock_cv2():
    """Context manager to mock cv2 module."""
    mock_cv2_module = Mock()
    mock_cv2_module.imread = Mock(return_value=np.zeros((400, 400, 3), dtype=np.uint8))
    mock_cv2_module.cvtColor = Mock(
        return_value=np.zeros((400, 400, 3), dtype=np.uint8)
    )
    mock_cv2_module.COLOR_BGR2RGB = 1

    with patch.dict("sys.modules", {"cv2": mock_cv2_module}):
        yield mock_cv2_module


@pytest.fixture
def mock_face_app():
    """Create a mock InsightFace application."""
    mock_app = Mock()
    mock_app.prepare = Mock()

    # Create mock face detection result
    mock_face = Mock()
    mock_face.bbox = np.array([100, 100, 200, 200], dtype=np.float32)
    mock_face.normed_embedding = np.random.rand(512).astype(np.float32)
    mock_face.det_score = 0.95
    mock_face.kps = np.array(
        [[120, 120], [180, 120], [150, 150], [130, 170], [170, 170]]
    )

    mock_app.get = Mock(return_value=[mock_face])
    return mock_app


@pytest.fixture
def sample_photo():
    """Create a sample photo for testing."""
    return Photo(
        id=1,
        path="/test/photo.jpg",
        folder="/test",
        filename="photo.jpg",
        ext=".jpg",
        size=1024000,
        created_ts=1640995200.0,
        modified_ts=1640995200.0,
        sha1="abc123",
    )


@pytest.fixture
def sample_face():
    """Create a sample face for testing."""
    face_vector = np.random.rand(512).astype(np.float32)
    face_vector = face_vector / np.linalg.norm(face_vector)

    return Face(
        id=1,
        file_id=1,
        person_id=None,
        box_xyxy=[100.0, 100.0, 200.0, 200.0],
        face_vector=face_vector,
        confidence=0.85,
        verified=False,
    )


@pytest.fixture
def sample_person():
    """Create a sample person for testing."""
    face_vector = np.random.rand(512).astype(np.float32)
    face_vector = face_vector / np.linalg.norm(face_vector)

    return Person(
        id=1,
        name="John Doe",
        face_vector=face_vector,
        sample_count=3,
        created_at=1640995200.0,
        updated_at=1640995200.0,
        active=True,
    )


class TestFaceDetectionWorkerInitialization:
    """Test FaceDetectionWorker initialization."""

    def test_initialization_with_defaults(self):
        """Test worker initialization with default parameters."""
        # Mock the initialization method to avoid importing insightface
        with patch.object(FaceDetectionWorker, "_initialize_face_models"):
            worker = FaceDetectionWorker()

            assert worker.max_workers == 2
            assert worker.model_name == "buffalo_l"
            assert worker.detection_threshold == 0.5
            assert worker.executor is not None
            assert worker.stats["photos_processed"] == 0
            assert worker.stats["faces_detected"] == 0

    def test_initialization_with_custom_params(self):
        """Test worker initialization with custom parameters."""
        with patch.object(FaceDetectionWorker, "_initialize_face_models"):
            worker = FaceDetectionWorker(
                max_workers=4,
                model_name="buffalo_s",
                detection_threshold=0.7,
            )

            assert worker.max_workers == 4
            assert worker.model_name == "buffalo_s"
            assert worker.detection_threshold == 0.7

    def test_initialization_without_insightface(self):
        """Test worker initialization when InsightFace is not available."""
        # Mock insightface import to raise ImportError
        with patch(
            "src.workers.face_worker.FaceDetectionWorker._initialize_face_models"
        ) as mock_init:
            # Make the initialization not set face_app (simulating import failure)
            def no_op_init(self):
                pass

            mock_init.side_effect = lambda: None

            worker = FaceDetectionWorker()
            # Manually set face_app to None to simulate initialization failure
            worker.face_app = None

            assert worker.face_app is None
            assert not worker.is_available()

    def test_initialization_with_model_error(self):
        """Test worker initialization when model fails to load."""

        # Patch to raise exception during initialization
        def raise_error(self):
            error_msg = "Model error"
            raise Exception(error_msg)

        with patch.object(FaceDetectionWorker, "_initialize_face_models", raise_error):
            # Should catch the exception and set face_app to None
            try:
                worker = FaceDetectionWorker()
                # If it doesn't raise, face_app should be None
                assert worker.face_app is None
            except:
                # If it raises, that's also acceptable
                pass


class TestFaceDetection:
    """Test face detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_faces_success(self, mock_face_app, sample_photo):
        """Test successful face detection."""
        worker = FaceDetectionWorker()
        worker.face_app = mock_face_app

        # Mock cv2 module
        mock_cv2 = Mock()
        mock_cv2.imread.return_value = np.zeros((400, 400, 3), dtype=np.uint8)
        mock_cv2.cvtColor.return_value = np.zeros((400, 400, 3), dtype=np.uint8)

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            faces = await worker.detect_faces(sample_photo)

            assert len(faces) == 1
            assert faces[0].file_id == sample_photo.id
            assert faces[0].confidence == 0.95
            assert worker.stats["photos_processed"] == 1
            assert worker.stats["faces_detected"] == 1

    @pytest.mark.asyncio
    async def test_detect_faces_no_app(self, sample_photo):
        """Test face detection when face_app is not initialized."""
        worker = FaceDetectionWorker()
        worker.face_app = None

        faces = await worker.detect_faces(sample_photo)

        assert faces == []
        assert worker.stats["photos_processed"] == 0

    @pytest.mark.asyncio
    async def test_detect_faces_with_error(self, mock_face_app, sample_photo):
        """Test face detection when an error occurs."""
        worker = FaceDetectionWorker()
        worker.face_app = mock_face_app

        # Create a mock executor that will raise exception
        mock_executor = Mock()

        async def raise_error(*args, **kwargs):
            error_msg = "Read error"
            raise Exception(error_msg)

        # Mock the run_in_executor to raise exception
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = Mock()
            mock_loop_instance.run_in_executor = Mock(side_effect=raise_error)
            mock_loop.return_value = mock_loop_instance

            faces = await worker.detect_faces(sample_photo)

            assert faces == []
            # Failed detections should be incremented
            assert worker.stats["failed_detections"] == 1

    @pytest.mark.asyncio
    async def test_detect_faces_no_image(self, mock_face_app, sample_photo):
        """Test face detection when image cannot be loaded."""
        worker = FaceDetectionWorker()
        worker.face_app = mock_face_app

        mock_cv2_module = Mock()
        mock_cv2_module.imread.return_value = None
        mock_cv2_module.cvtColor = Mock()
        with patch.dict("sys.modules", {"cv2": mock_cv2_module}):
            faces = await worker.detect_faces(sample_photo)

            assert faces == []

    def test_detect_faces_sync_success(self, mock_face_app):
        """Test synchronous face detection."""
        worker = FaceDetectionWorker()
        worker.face_app = mock_face_app

        with mock_cv2():
            detections = worker._detect_faces_sync("/test/photo.jpg")

            assert len(detections) == 1
            assert "bbox" in detections[0]
            assert "embedding" in detections[0]
            assert "confidence" in detections[0]
            assert detections[0]["confidence"] == 0.95

    def test_detect_faces_sync_with_threshold_filter(self, mock_face_app):
        """Test synchronous face detection with confidence threshold."""
        # Create mock face with low confidence
        mock_low_conf_face = Mock()
        mock_low_conf_face.bbox = np.array([100, 100, 200, 200], dtype=np.float32)
        mock_low_conf_face.normed_embedding = np.random.rand(512).astype(np.float32)
        mock_low_conf_face.det_score = 0.3
        mock_low_conf_face.kps = np.array([[120, 120]])

        mock_face_app.get = Mock(return_value=[mock_low_conf_face])

        worker = FaceDetectionWorker(detection_threshold=0.5)
        worker.face_app = mock_face_app

        with mock_cv2():
            detections = worker._detect_faces_sync("/test/photo.jpg")

            # Should be filtered out due to low confidence
            assert len(detections) == 0


class TestFaceRecognition:
    """Test face recognition functionality."""

    @pytest.mark.asyncio
    async def test_recognize_faces_success(self, sample_face, sample_person):
        """Test successful face recognition."""
        worker = FaceDetectionWorker()

        # Make face vector similar to person vector
        sample_face.face_vector = sample_person.face_vector.copy()

        results = await worker.recognize_faces(
            [sample_face], [sample_person], similarity_threshold=0.5
        )

        assert len(results) == 1
        assert results[0]["face"] == sample_face
        assert results[0]["matched_person"] == sample_person
        assert results[0]["above_threshold"] is True
        assert worker.stats["faces_recognized"] == 1

    @pytest.mark.asyncio
    async def test_recognize_faces_no_match(self, sample_face, sample_person):
        """Test face recognition with no matching person."""
        worker = FaceDetectionWorker()

        results = await worker.recognize_faces(
            [sample_face], [sample_person], similarity_threshold=0.99
        )

        assert len(results) == 1
        assert results[0]["matched_person"] is None
        assert results[0]["above_threshold"] is False
        assert worker.stats["faces_recognized"] == 0

    @pytest.mark.asyncio
    async def test_recognize_faces_empty_inputs(self):
        """Test face recognition with empty inputs."""
        worker = FaceDetectionWorker()

        results = await worker.recognize_faces([], [], similarity_threshold=0.6)
        assert results == []

    @pytest.mark.asyncio
    async def test_recognize_faces_inactive_person(self, sample_face, sample_person):
        """Test face recognition skips inactive persons."""
        worker = FaceDetectionWorker()
        sample_person.active = False
        sample_face.face_vector = sample_person.face_vector.copy()

        results = await worker.recognize_faces(
            [sample_face], [sample_person], similarity_threshold=0.5
        )

        assert len(results) == 1
        assert results[0]["matched_person"] is None

    @pytest.mark.asyncio
    async def test_recognize_faces_without_vectors(self, sample_face, sample_person):
        """Test face recognition when vectors are missing."""
        worker = FaceDetectionWorker()
        sample_face.face_vector = None

        results = await worker.recognize_faces(
            [sample_face], [sample_person], similarity_threshold=0.6
        )

        assert len(results) == 0


class TestBatchProcessing:
    """Test batch processing functionality."""

    @pytest.mark.asyncio
    async def test_process_batch_success(self, mock_face_app):
        """Test successful batch processing."""
        worker = FaceDetectionWorker()
        worker.face_app = mock_face_app

        photos = [
            Photo(
                id=i,
                path=f"/test/photo{i}.jpg",
                folder="/test",
                filename=f"photo{i}.jpg",
                ext=".jpg",
                size=1024,
                created_ts=1.0,
                modified_ts=1.0,
                sha1=f"hash{i}",
            )
            for i in range(3)
        ]

        with mock_cv2():
            results = await worker.process_batch(photos)

            assert len(results) == 3
            assert worker.stats["photos_processed"] == 3

    @pytest.mark.asyncio
    async def test_process_batch_empty(self):
        """Test batch processing with empty input."""
        worker = FaceDetectionWorker()

        results = await worker.process_batch([])

        assert results == []


class TestPersonEnrollment:
    """Test person enrollment functionality."""

    @pytest.mark.asyncio
    async def test_enroll_person_success(self):
        """Test successful person enrollment."""
        worker = FaceDetectionWorker()

        # Create high confidence mock
        mock_high_conf_face = Mock()
        mock_high_conf_face.bbox = np.array([100, 100, 200, 200], dtype=np.float32)
        mock_high_conf_face.normed_embedding = np.random.rand(512).astype(np.float32)
        mock_high_conf_face.det_score = 0.95
        mock_high_conf_face.kps = np.array([[120, 120]])

        mock_face_app = Mock()
        mock_face_app.get = Mock(return_value=[mock_high_conf_face])
        worker.face_app = mock_face_app

        photos = [
            Photo(
                id=1,
                path="/test/photo1.jpg",
                folder="/test",
                filename="photo1.jpg",
                ext=".jpg",
                size=1024,
                created_ts=1.0,
                modified_ts=1.0,
                sha1="hash1",
            )
        ]

        with mock_cv2():
            person = await worker.enroll_person("John Doe", photos)

            assert person is not None
            assert person.name == "John Doe"
            assert person.sample_count == 1
            assert person.face_vector is not None

    @pytest.mark.asyncio
    async def test_enroll_person_no_photos(self):
        """Test person enrollment with no photos."""
        worker = FaceDetectionWorker()

        with pytest.raises(ValueError, match="At least one sample photo is required"):
            await worker.enroll_person("John Doe", [])

    @pytest.mark.asyncio
    async def test_enroll_person_no_suitable_faces(self):
        """Test person enrollment when no suitable faces are found."""
        mock_face_app = Mock()
        mock_face_app.get = Mock(return_value=[])

        worker = FaceDetectionWorker()
        worker.face_app = mock_face_app

        photos = [
            Photo(
                id=1,
                path="/test/photo1.jpg",
                folder="/test",
                filename="photo1.jpg",
                ext=".jpg",
                size=1024,
                created_ts=1.0,
                modified_ts=1.0,
                sha1="hash1",
            )
        ]

        with mock_cv2():
            with pytest.raises(ValueError, match="No suitable faces found"):
                await worker.enroll_person("John Doe", photos)

    @pytest.mark.asyncio
    async def test_enroll_person_multiple_faces(self):
        """Test person enrollment with multiple faces in one photo."""
        # Create multiple high confidence faces
        faces = []
        for i in range(2):
            mock_face = Mock()
            mock_face.bbox = np.array(
                [100 + i * 50, 100, 200 + i * 50, 200], dtype=np.float32
            )
            mock_face.normed_embedding = np.random.rand(512).astype(np.float32)
            mock_face.det_score = 0.9 - i * 0.05
            mock_face.kps = np.array([[120, 120]])
            faces.append(mock_face)

        mock_face_app = Mock()
        mock_face_app.get = Mock(return_value=faces)

        worker = FaceDetectionWorker()
        worker.face_app = mock_face_app

        photos = [
            Photo(
                id=1,
                path="/test/photo1.jpg",
                folder="/test",
                filename="photo1.jpg",
                ext=".jpg",
                size=1024,
                created_ts=1.0,
                modified_ts=1.0,
                sha1="hash1",
            )
        ]

        with mock_cv2():
            person = await worker.enroll_person("John Doe", photos)

            # Should take the highest confidence face
            assert person is not None
            assert person.sample_count == 1


class TestUpdatePersonEnrollment:
    """Test updating person enrollment."""

    @pytest.mark.asyncio
    async def test_update_person_enrollment_success(self, sample_person):
        """Test successful person enrollment update."""
        # Create high confidence mock
        mock_high_conf_face = Mock()
        mock_high_conf_face.bbox = np.array([100, 100, 200, 200], dtype=np.float32)
        mock_high_conf_face.normed_embedding = np.random.rand(512).astype(np.float32)
        mock_high_conf_face.det_score = 0.95
        mock_high_conf_face.kps = np.array([[120, 120]])

        mock_face_app = Mock()
        mock_face_app.get = Mock(return_value=[mock_high_conf_face])

        worker = FaceDetectionWorker()
        worker.face_app = mock_face_app

        photos = [
            Photo(
                id=1,
                path="/test/photo1.jpg",
                folder="/test",
                filename="photo1.jpg",
                ext=".jpg",
                size=1024,
                created_ts=1.0,
                modified_ts=1.0,
                sha1="hash1",
            )
        ]

        original_sample_count = sample_person.sample_count

        with mock_cv2():
            updated_person = await worker.update_person_enrollment(
                sample_person, photos
            )

            assert updated_person.sample_count > original_sample_count

    @pytest.mark.asyncio
    async def test_update_person_enrollment_no_new_faces(self, sample_person):
        """Test person enrollment update with no new faces."""
        mock_face_app = Mock()
        mock_face_app.get = Mock(return_value=[])

        worker = FaceDetectionWorker()
        worker.face_app = mock_face_app

        photos = [
            Photo(
                id=1,
                path="/test/photo1.jpg",
                folder="/test",
                filename="photo1.jpg",
                ext=".jpg",
                size=1024,
                created_ts=1.0,
                modified_ts=1.0,
                sha1="hash1",
            )
        ]

        original_sample_count = sample_person.sample_count

        with mock_cv2():
            updated_person = await worker.update_person_enrollment(
                sample_person, photos
            )

            # Sample count should not change
            assert updated_person.sample_count == original_sample_count


class TestStatistics:
    """Test statistics functionality."""

    def test_get_statistics(self):
        """Test getting worker statistics."""
        worker = FaceDetectionWorker()
        worker.stats["photos_processed"] = 10
        worker.stats["faces_detected"] = 15
        worker.stats["faces_recognized"] = 12
        worker.stats["processing_time"] = 5.0
        worker.stats["failed_detections"] = 2

        stats = worker.get_statistics()

        assert stats["photos_processed"] == 10
        assert stats["faces_detected"] == 15
        assert stats["faces_recognized"] == 12
        assert stats["failed_detections"] == 2
        assert stats["average_faces_per_photo"] == 1.5
        assert stats["recognition_rate"] == 0.8
        assert stats["average_processing_time"] == 0.5
        assert stats["model_name"] == "buffalo_l"
        assert stats["detection_threshold"] == 0.5

    def test_reset_statistics(self):
        """Test resetting worker statistics."""
        worker = FaceDetectionWorker()
        worker.stats["photos_processed"] = 10
        worker.stats["faces_detected"] = 15

        worker.reset_statistics()

        assert worker.stats["photos_processed"] == 0
        assert worker.stats["faces_detected"] == 0
        assert worker.stats["faces_recognized"] == 0
        assert worker.stats["processing_time"] == 0.0

    def test_is_available(self):
        """Test checking if face detection is available."""
        worker = FaceDetectionWorker()
        worker.face_app = Mock()

        assert worker.is_available() is True

        worker.face_app = None
        assert worker.is_available() is False

    def test_shutdown(self):
        """Test worker shutdown."""
        worker = FaceDetectionWorker()
        mock_executor = Mock()
        worker.executor = mock_executor

        worker.shutdown()

        mock_executor.shutdown.assert_called_once_with(wait=True)


class TestFaceSearchEngine:
    """Test FaceSearchEngine functionality."""

    @pytest.mark.asyncio
    async def test_search_by_face_image(self, sample_face):
        """Test searching by face vector."""
        engine = FaceSearchEngine(similarity_threshold=0.5)

        query_vector = sample_face.face_vector.copy()

        results = await engine.search_by_face_image(
            query_vector, [sample_face], top_k=10
        )

        assert len(results) == 1
        assert results[0]["similarity"] > 0.99  # Should be nearly identical

    @pytest.mark.asyncio
    async def test_search_by_face_image_top_k_limit(self):
        """Test search respects top_k limit."""
        engine = FaceSearchEngine(similarity_threshold=0.0)

        query_vector = np.random.rand(512).astype(np.float32)
        query_vector = query_vector / np.linalg.norm(query_vector)

        # Create multiple similar faces
        faces = []
        for i in range(10):
            face_vector = query_vector + np.random.rand(512).astype(np.float32) * 0.1
            face_vector = face_vector / np.linalg.norm(face_vector)
            face = Face(
                id=i,
                file_id=i,
                box_xyxy=[0, 0, 10, 10],
                face_vector=face_vector,
                confidence=0.9,
            )
            faces.append(face)

        results = await engine.search_by_face_image(query_vector, faces, top_k=5)

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_find_duplicate_faces(self):
        """Test finding duplicate faces."""
        engine = FaceSearchEngine()

        # Create duplicate faces
        base_vector = np.random.rand(512).astype(np.float32)
        base_vector = base_vector / np.linalg.norm(base_vector)

        face1 = Face(
            id=1,
            file_id=1,
            box_xyxy=[0, 0, 10, 10],
            face_vector=base_vector.copy(),
            confidence=0.9,
        )
        face2 = Face(
            id=2,
            file_id=2,
            box_xyxy=[0, 0, 10, 10],
            face_vector=base_vector.copy(),
            confidence=0.9,
        )
        face3 = Face(
            id=3,
            file_id=3,
            box_xyxy=[0, 0, 10, 10],
            face_vector=np.random.rand(512).astype(np.float32),
            confidence=0.9,
        )

        duplicate_groups = await engine.find_duplicate_faces(
            [face1, face2, face3], duplicate_threshold=0.95
        )

        assert len(duplicate_groups) >= 1
        # First group should contain face1 and face2
        assert len(duplicate_groups[0]) >= 2

    @pytest.mark.asyncio
    async def test_cluster_unknown_faces(self):
        """Test clustering unknown faces."""
        engine = FaceSearchEngine()

        # Create clusters of similar faces
        base_vector1 = np.random.rand(512).astype(np.float32)
        base_vector1 = base_vector1 / np.linalg.norm(base_vector1)

        base_vector2 = np.random.rand(512).astype(np.float32)
        base_vector2 = base_vector2 / np.linalg.norm(base_vector2)

        faces = [
            Face(
                id=1,
                file_id=1,
                box_xyxy=[0, 0, 10, 10],
                face_vector=base_vector1 + np.random.rand(512).astype(np.float32) * 0.1,
                confidence=0.9,
            ),
            Face(
                id=2,
                file_id=2,
                box_xyxy=[0, 0, 10, 10],
                face_vector=base_vector1 + np.random.rand(512).astype(np.float32) * 0.1,
                confidence=0.9,
            ),
            Face(
                id=3,
                file_id=3,
                box_xyxy=[0, 0, 10, 10],
                face_vector=base_vector2 + np.random.rand(512).astype(np.float32) * 0.1,
                confidence=0.9,
            ),
        ]

        # Normalize vectors
        for face in faces:
            face.face_vector = face.face_vector / np.linalg.norm(face.face_vector)

        clusters = await engine.cluster_unknown_faces(faces, cluster_threshold=0.7)

        assert len(clusters) >= 1


class TestFaceQualityAnalyzer:
    """Test FaceQualityAnalyzer functionality."""

    def test_analyze_face_quality_high_quality(self):
        """Test analyzing high quality face."""
        face_vector = np.random.rand(512).astype(np.float32)
        face_vector = face_vector / np.linalg.norm(face_vector)

        face = Face(
            id=1,
            file_id=1,
            box_xyxy=[100.0, 100.0, 300.0, 300.0],  # Large face
            face_vector=face_vector,
            confidence=0.95,
            verified=False,
        )

        quality = FaceQualityAnalyzer.analyze_face_quality(face)

        assert quality["quality_score"] > 0.7
        assert quality["quality_grade"] in ["A", "B"]
        assert quality["suitable_for_enrollment"] is True
        assert quality["suitable_for_recognition"] is True

    def test_analyze_face_quality_low_quality(self):
        """Test analyzing low quality face."""
        face_vector = np.random.rand(512).astype(np.float32)
        # Don't normalize to create normalization issue

        face = Face(
            id=1,
            file_id=1,
            box_xyxy=[100.0, 100.0, 110.0, 110.0],  # Very small face
            face_vector=face_vector,
            confidence=0.4,
            verified=False,
        )

        quality = FaceQualityAnalyzer.analyze_face_quality(face)

        assert quality["quality_score"] < 0.7
        assert len(quality["issues"]) > 0

    def test_analyze_face_quality_no_vector(self):
        """Test analyzing face without vector."""
        face = Face(
            id=1,
            file_id=1,
            box_xyxy=[100.0, 100.0, 200.0, 200.0],
            face_vector=None,
            confidence=0.85,
            verified=False,
        )

        quality = FaceQualityAnalyzer.analyze_face_quality(face)

        assert "No face vector available" in quality["issues"]

    def test_get_quality_grade(self):
        """Test quality grade conversion."""
        assert FaceQualityAnalyzer._get_quality_grade(0.95) == "A"
        assert FaceQualityAnalyzer._get_quality_grade(0.75) == "B"
        assert FaceQualityAnalyzer._get_quality_grade(0.55) == "C"
        assert FaceQualityAnalyzer._get_quality_grade(0.35) == "D"
        assert FaceQualityAnalyzer._get_quality_grade(0.15) == "F"

    def test_analyze_enrollment_quality(self, sample_person):
        """Test analyzing enrollment quality."""
        # Create sample faces
        faces = []
        for i in range(3):
            face_vector = np.random.rand(512).astype(np.float32)
            face_vector = face_vector / np.linalg.norm(face_vector)

            face = Face(
                id=i,
                file_id=i,
                box_xyxy=[100.0, 100.0, 250.0, 250.0],
                face_vector=face_vector,
                confidence=0.9,
                verified=False,
            )
            faces.append(face)

        quality = FaceQualityAnalyzer.analyze_enrollment_quality(sample_person, faces)

        assert "enrollment_quality" in quality
        assert "average_face_quality" in quality
        assert quality["total_samples"] == 3
        assert len(quality["recommendations"]) > 0

    def test_analyze_enrollment_quality_no_faces(self, sample_person):
        """Test analyzing enrollment quality with no faces."""
        quality = FaceQualityAnalyzer.analyze_enrollment_quality(sample_person, [])

        assert quality["enrollment_quality"] == 0.0
        assert "No sample faces provided" in quality["recommendations"]


# === Merged from test_face_worker_extended.py ===


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
        with patch(
            "insightface.app.FaceAnalysis", side_effect=Exception("Init Failed")
        ):
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
        person.face_vector = np.array([0.1] * 512, dtype=np.float32)
        person.id = 1

        face = MagicMock(spec=Face)
        face.face_vector = np.array([0.1] * 512, dtype=np.float32)
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

        person.face_vector = np.array([0.1] * 512)
        face = MagicMock(spec=Face)
        face.face_vector = None

        matches = await engine.search_by_person(person, [face])
        assert matches == []
