"""Unit tests for Person and Face models."""

import json
import struct
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.models.person import Face, FaceSearchResult, Person


class TestPersonModel:
    """Test Person model functionality."""

    def test_person_creation_with_defaults(self):
        """Test creating a Person with default values."""
        person = Person()

        assert person.id is None
        assert person.name == ""
        assert person.face_vector is None
        assert person.sample_count == 0
        assert person.created_at is not None
        assert person.updated_at is not None
        assert person.active is True

    def test_person_creation_with_values(self):
        """Test creating a Person with specified values."""
        face_vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        person = Person(
            id=1,
            name="John Doe",
            face_vector=face_vector,
            sample_count=5,
            created_at=1640995200.0,
            updated_at=1640995300.0,
            active=True,
        )

        assert person.id == 1
        assert person.name == "John Doe"
        assert np.array_equal(person.face_vector, face_vector)
        assert person.sample_count == 5
        assert person.created_at == 1640995200.0
        assert person.updated_at == 1640995300.0
        assert person.active is True

    def test_person_post_init_timestamps(self):
        """Test that timestamps are auto-generated if not provided."""
        with patch("src.models.person.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 1640995200.0
            person = Person()

        assert person.created_at == 1640995200.0
        assert person.updated_at == 1640995200.0

    def test_person_post_init_converts_list_to_numpy(self):
        """Test that face_vector list is converted to numpy array."""
        person = Person(face_vector=[0.1, 0.2, 0.3])

        assert isinstance(person.face_vector, np.ndarray)
        assert person.face_vector.dtype == np.float32

    def test_create_from_face_vectors_single(self):
        """Test creating Person from a single face vector."""
        vector = np.array([0.6, 0.8], dtype=np.float32)
        person = Person.create_from_face_vectors("Alice", [vector])

        assert person.name == "Alice"
        assert person.sample_count == 1
        # Normalized vector: [0.6, 0.8] -> [0.6, 0.8] (already normalized)
        expected = vector / np.linalg.norm(vector)
        np.testing.assert_array_almost_equal(person.face_vector, expected)

    def test_create_from_face_vectors_multiple(self):
        """Test creating Person from multiple face vectors."""
        vector1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vector2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        person = Person.create_from_face_vectors("Bob", [vector1, vector2])

        assert person.name == "Bob"
        assert person.sample_count == 2
        # Average: [0.5, 0.5, 0.0], normalized
        expected = np.array([0.5, 0.5, 0.0], dtype=np.float32)
        expected = expected / np.linalg.norm(expected)
        np.testing.assert_array_almost_equal(person.face_vector, expected)

    def test_create_from_face_vectors_empty_list(self):
        """Test creating Person with empty face vectors list."""
        with pytest.raises(ValueError, match="At least one face vector is required"):
            Person.create_from_face_vectors("Charlie", [])

    def test_create_from_face_vectors_empty_name(self):
        """Test creating Person with empty name."""
        vector = np.array([1.0, 0.0], dtype=np.float32)
        with pytest.raises(ValueError, match="Person name cannot be empty"):
            Person.create_from_face_vectors("", [vector])

    def test_create_from_face_vectors_whitespace_name(self):
        """Test creating Person with whitespace-only name."""
        vector = np.array([1.0, 0.0], dtype=np.float32)
        with pytest.raises(ValueError, match="Person name cannot be empty"):
            Person.create_from_face_vectors("   ", [vector])

    def test_create_from_face_vectors_mismatched_dimensions(self):
        """Test creating Person with mismatched vector dimensions."""
        vector1 = np.array([1.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        with pytest.raises(
            ValueError, match="All face vectors must have the same dimension"
        ):
            Person.create_from_face_vectors("Dave", [vector1, vector2])

    def test_create_from_face_vectors_strips_name(self):
        """Test that person name is stripped of whitespace."""
        vector = np.array([1.0, 0.0], dtype=np.float32)
        person = Person.create_from_face_vectors("  Eve  ", [vector])

        assert person.name == "Eve"

    def test_from_db_row(self):
        """Test creating Person from database row."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        blob = Person._numpy_to_blob(vector)

        row = {
            "id": 1,
            "name": "Frank",
            "face_vector": blob,
            "sample_count": 3,
            "created_at": 1640995200.0,
            "updated_at": 1640995300.0,
            "active": 1,
        }

        person = Person.from_db_row(row)

        assert person.id == 1
        assert person.name == "Frank"
        np.testing.assert_array_almost_equal(person.face_vector, vector)
        assert person.sample_count == 3
        assert person.active is True

    def test_from_db_row_null_vector(self):
        """Test creating Person from database row with null face_vector."""
        row = {
            "id": 1,
            "name": "Grace",
            "face_vector": None,
            "sample_count": 0,
            "created_at": 1640995200.0,
            "updated_at": 1640995300.0,
            "active": 1,
        }

        person = Person.from_db_row(row)

        assert person.face_vector is None

    def test_from_db_row_inactive(self):
        """Test creating inactive Person from database row."""
        row = {
            "id": 1,
            "name": "Henry",
            "face_vector": None,
            "sample_count": 1,
            "created_at": 1640995200.0,
            "updated_at": 1640995300.0,
            "active": 0,
        }

        person = Person.from_db_row(row)

        assert person.active is False

    def test_to_dict(self):
        """Test converting Person to dictionary."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        person = Person(
            id=1,
            name="Irene",
            face_vector=vector,
            sample_count=2,
            created_at=1640995200.0,
            updated_at=1640995300.0,
            active=True,
        )

        result = person.to_dict()

        assert result["id"] == 1
        assert result["name"] == "Irene"
        assert result["sample_count"] == 2
        assert result["created_at"] == 1640995200.0
        assert result["updated_at"] == 1640995300.0
        assert result["active"] is True
        assert result["face_vector_dimension"] == 3

    def test_to_dict_null_vector(self):
        """Test converting Person with null vector to dictionary."""
        person = Person(id=1, name="Jack")

        result = person.to_dict()

        assert result["face_vector_dimension"] is None

    def test_to_db_params(self):
        """Test converting Person to database parameters."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        person = Person(
            name="Kate",
            face_vector=vector,
            sample_count=4,
            created_at=1640995200.0,
            updated_at=1640995300.0,
            active=True,
        )

        params = person.to_db_params()

        assert params[0] == "Kate"
        assert params[1] is not None  # blob
        assert params[2] == 4
        assert params[3] == 1640995200.0
        assert params[4] == 1640995300.0
        assert params[5] is True

    def test_validate_valid_person(self):
        """Test validation of valid Person."""
        vector = np.array([0.1] * 512, dtype=np.float32)
        person = Person(
            name="Leo",
            face_vector=vector,
            sample_count=1,
        )

        errors = person.validate()

        assert len(errors) == 0

    def test_validate_empty_name(self):
        """Test validation catches empty name."""
        vector = np.array([0.1] * 512, dtype=np.float32)
        person = Person(name="", face_vector=vector, sample_count=1)

        errors = person.validate()

        assert any("Person name cannot be empty" in e for e in errors)

    def test_validate_long_name(self):
        """Test validation catches name too long."""
        vector = np.array([0.1] * 512, dtype=np.float32)
        person = Person(name="x" * 256, face_vector=vector, sample_count=1)

        errors = person.validate()

        assert any("Person name too long" in e for e in errors)

    def test_validate_negative_sample_count(self):
        """Test validation catches non-positive sample count."""
        vector = np.array([0.1] * 512, dtype=np.float32)
        person = Person(name="Mary", face_vector=vector, sample_count=0)

        errors = person.validate()

        assert any("Sample count must be positive" in e for e in errors)

    def test_validate_no_face_vector(self):
        """Test validation catches missing face vector."""
        person = Person(name="Nancy", sample_count=1)

        errors = person.validate()

        assert any("Face vector is required" in e for e in errors)

    def test_validate_wrong_dtype(self):
        """Test validation catches wrong dtype."""
        vector = np.array([0.1] * 512, dtype=np.float64)
        person = Person(name="Oscar", face_vector=vector, sample_count=1)

        errors = person.validate()

        assert any("Face vector must be float32" in e for e in errors)

    def test_validate_wrong_dimension(self):
        """Test validation catches unexpected dimension."""
        vector = np.array([0.1] * 256, dtype=np.float32)
        person = Person(name="Paul", face_vector=vector, sample_count=1)

        errors = person.validate()

        assert any("Unexpected face vector dimension" in e for e in errors)

    def test_validate_nan_values(self):
        """Test validation catches NaN values."""
        vector = np.array([0.1, np.nan, 0.3] + [0.1] * 509, dtype=np.float32)
        person = Person(name="Quinn", face_vector=vector, sample_count=1)

        errors = person.validate()

        assert any("contains invalid values" in e for e in errors)

    def test_validate_inf_values(self):
        """Test validation catches Inf values."""
        vector = np.array([0.1, np.inf, 0.3] + [0.1] * 509, dtype=np.float32)
        person = Person(name="Rachel", face_vector=vector, sample_count=1)

        errors = person.validate()

        assert any("contains invalid values" in e for e in errors)

    def test_is_valid(self):
        """Test is_valid method."""
        valid_person = Person(
            name="Sam",
            face_vector=np.array([0.1] * 512, dtype=np.float32),
            sample_count=1,
        )
        assert valid_person.is_valid() is True

        invalid_person = Person(name="", sample_count=1)
        assert invalid_person.is_valid() is False

    def test_update_face_vector_single(self):
        """Test updating face vector with new sample."""
        initial_vector = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        person = Person(name="Tina", face_vector=initial_vector, sample_count=1)

        new_vector = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        with patch("src.models.person.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 1640995300.0
            person.update_face_vector([new_vector])

        # Should average [1,0,0] and [0,1,0] -> [0.5, 0.5, 0.0], then normalize
        expected = np.array([0.5, 0.5, 0.0], dtype=np.float32)
        expected = expected / np.linalg.norm(expected)
        np.testing.assert_array_almost_equal(person.face_vector, expected)
        assert person.sample_count == 2
        assert person.updated_at == 1640995300.0

    def test_update_face_vector_empty_list(self):
        """Test updating face vector with empty list does nothing."""
        initial_vector = np.array([1.0, 0.0], dtype=np.float32)
        person = Person(name="Uma", face_vector=initial_vector, sample_count=1)

        person.update_face_vector([])

        np.testing.assert_array_equal(person.face_vector, initial_vector)
        assert person.sample_count == 1

    def test_update_face_vector_null_initial(self):
        """Test updating face vector when starting with None."""
        person = Person(name="Victor", sample_count=0)

        new_vector = np.array([1.0, 0.0], dtype=np.float32)
        person.update_face_vector([new_vector])

        expected = new_vector / np.linalg.norm(new_vector)
        np.testing.assert_array_almost_equal(person.face_vector, expected)
        assert person.sample_count == 1

    def test_similarity_to_vector_cosine(self):
        """Test cosine similarity calculation."""
        vector1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        person = Person(name="Wendy", face_vector=vector1, sample_count=1)

        similarity = person.similarity_to_vector(vector2, metric="cosine")

        assert similarity == pytest.approx(1.0)

    def test_similarity_to_vector_euclidean(self):
        """Test Euclidean distance similarity calculation."""
        vector1 = np.array([1.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0], dtype=np.float32)
        person = Person(name="Xavier", face_vector=vector1, sample_count=1)

        similarity = person.similarity_to_vector(vector2, metric="euclidean")

        # Same vectors: distance=0, similarity = 1/(1+0) = 1.0
        assert similarity == pytest.approx(1.0)

    def test_similarity_to_vector_null_vector(self):
        """Test similarity calculation with null vector."""
        person = Person(name="Yara")

        similarity = person.similarity_to_vector(np.array([1.0, 0.0], dtype=np.float32))

        assert similarity == 0.0

    def test_similarity_to_vector_mismatched_dimensions(self):
        """Test similarity calculation with mismatched dimensions."""
        vector1 = np.array([1.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        person = Person(name="Zara", face_vector=vector1, sample_count=1)

        with pytest.raises(ValueError, match="Vector dimensions must match"):
            person.similarity_to_vector(vector2)

    def test_similarity_to_vector_unknown_metric(self):
        """Test similarity calculation with unknown metric."""
        vector1 = np.array([1.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0], dtype=np.float32)
        person = Person(name="Adam", face_vector=vector1, sample_count=1)

        with pytest.raises(ValueError, match="Unknown similarity metric"):
            person.similarity_to_vector(vector2, metric="unknown")

    def test_deactivate(self):
        """Test deactivating a person."""
        person = Person(name="Beth", active=True)

        with patch("src.models.person.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 1640995300.0
            person.deactivate()

        assert person.active is False
        assert person.updated_at == 1640995300.0

    def test_reactivate(self):
        """Test reactivating a person."""
        person = Person(name="Carl", active=False)

        with patch("src.models.person.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 1640995300.0
            person.reactivate()

        assert person.active is True
        assert person.updated_at == 1640995300.0

    def test_numpy_to_blob_and_back(self):
        """Test converting numpy array to blob and back."""
        original = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

        blob = Person._numpy_to_blob(original)
        restored = Person._blob_to_numpy(blob)

        np.testing.assert_array_almost_equal(restored, original)

    def test_blob_to_numpy_too_short(self):
        """Test blob conversion with invalid blob."""
        with pytest.raises(ValueError, match="Invalid blob: too short"):
            Person._blob_to_numpy(b"abc")

    def test_blob_to_numpy_wrong_size(self):
        """Test blob conversion with wrong size."""
        # Create blob with dimension 3 but only 2 floats
        blob = struct.pack("<I", 3)  # Says dimension is 3
        blob += struct.pack("<ff", 0.1, 0.2)  # But only 2 floats

        with pytest.raises(ValueError, match="Invalid blob size"):
            Person._blob_to_numpy(blob)


class TestFaceModel:
    """Test Face model functionality."""

    def test_face_creation_with_defaults(self):
        """Test creating a Face with default values."""
        face = Face()

        assert face.id is None
        assert face.file_id == 0
        assert face.person_id is None
        assert face.box_xyxy == [0.0, 0.0, 0.0, 0.0]
        assert face.face_vector is None
        assert face.confidence == 0.0
        assert face.verified is False

    def test_face_creation_with_values(self):
        """Test creating a Face with specified values."""
        vector = np.array([0.1, 0.2], dtype=np.float32)
        face = Face(
            id=1,
            file_id=100,
            person_id=5,
            box_xyxy=[10.0, 20.0, 100.0, 120.0],
            face_vector=vector,
            confidence=0.95,
            verified=True,
        )

        assert face.id == 1
        assert face.file_id == 100
        assert face.person_id == 5
        assert face.box_xyxy == [10.0, 20.0, 100.0, 120.0]
        np.testing.assert_array_equal(face.face_vector, vector)
        assert face.confidence == 0.95
        assert face.verified is True

    def test_face_post_init_box_default(self):
        """Test that box_xyxy is initialized if None."""
        face = Face(box_xyxy=None)

        assert face.box_xyxy == [0.0, 0.0, 0.0, 0.0]

    def test_face_post_init_converts_list_to_numpy(self):
        """Test that face_vector list is converted to numpy array."""
        face = Face(face_vector=[0.1, 0.2, 0.3])

        assert isinstance(face.face_vector, np.ndarray)
        assert face.face_vector.dtype == np.float32

    def test_from_detection_result(self):
        """Test creating Face from detection result."""
        detection = {
            "bbox": [10.0, 20.0, 100.0, 120.0],
            "embedding": np.array([0.6, 0.8], dtype=np.float32),
            "confidence": 0.92,
        }

        face = Face.from_detection_result(file_id=50, detection_result=detection)

        assert face.file_id == 50
        assert face.box_xyxy == [10.0, 20.0, 100.0, 120.0]
        assert face.confidence == 0.92
        assert face.verified is False
        # Embedding should be normalized
        expected = np.array([0.6, 0.8], dtype=np.float32)
        expected = expected / np.linalg.norm(expected)
        np.testing.assert_array_almost_equal(face.face_vector, expected)

    def test_from_detection_result_invalid_bbox(self):
        """Test creating Face with invalid bbox."""
        detection = {"bbox": [10.0, 20.0, 100.0]}  # Only 3 coordinates

        with pytest.raises(ValueError, match="Bounding box must have 4 coordinates"):
            Face.from_detection_result(file_id=50, detection_result=detection)

    def test_from_detection_result_no_embedding(self):
        """Test creating Face without embedding."""
        detection = {
            "bbox": [10.0, 20.0, 100.0, 120.0],
            "confidence": 0.9,
        }

        face = Face.from_detection_result(file_id=50, detection_result=detection)

        assert face.face_vector is None

    def test_from_detection_result_list_embedding(self):
        """Test creating Face with embedding as list."""
        detection = {
            "bbox": [10.0, 20.0, 100.0, 120.0],
            "embedding": [0.6, 0.8],
            "confidence": 0.9,
        }

        face = Face.from_detection_result(file_id=50, detection_result=detection)

        assert isinstance(face.face_vector, np.ndarray)

    def test_from_db_row(self):
        """Test creating Face from database row."""
        vector = np.array([0.1, 0.2], dtype=np.float32)
        blob = Person._numpy_to_blob(vector)

        row = {
            "id": 1,
            "file_id": 100,
            "person_id": 5,
            "box_xyxy": json.dumps([10.0, 20.0, 100.0, 120.0]),
            "face_vector": blob,
            "confidence": 0.95,
            "verified": 1,
        }

        face = Face.from_db_row(row)

        assert face.id == 1
        assert face.file_id == 100
        assert face.person_id == 5
        assert face.box_xyxy == [10.0, 20.0, 100.0, 120.0]
        np.testing.assert_array_almost_equal(face.face_vector, vector)
        assert face.confidence == 0.95
        assert face.verified is True

    def test_from_db_row_null_vector(self):
        """Test creating Face from database row with null vector."""
        row = {
            "id": 1,
            "file_id": 100,
            "person_id": None,
            "box_xyxy": json.dumps([10.0, 20.0, 100.0, 120.0]),
            "face_vector": None,
            "confidence": 0.85,
            "verified": 0,
        }

        face = Face.from_db_row(row)

        assert face.face_vector is None
        assert face.verified is False

    def test_to_dict(self):
        """Test converting Face to dictionary."""
        vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        face = Face(
            id=1,
            file_id=100,
            person_id=5,
            box_xyxy=[10.0, 20.0, 100.0, 120.0],
            face_vector=vector,
            confidence=0.95,
            verified=True,
        )

        result = face.to_dict()

        assert result["id"] == 1
        assert result["file_id"] == 100
        assert result["person_id"] == 5
        assert result["box_xyxy"] == [10.0, 20.0, 100.0, 120.0]
        assert result["confidence"] == 0.95
        assert result["verified"] is True
        assert result["face_vector_dimension"] == 3

    def test_to_db_params(self):
        """Test converting Face to database parameters."""
        vector = np.array([0.1, 0.2], dtype=np.float32)
        face = Face(
            file_id=100,
            person_id=5,
            box_xyxy=[10.0, 20.0, 100.0, 120.0],
            face_vector=vector,
            confidence=0.95,
            verified=True,
        )

        params = face.to_db_params()

        assert params[0] == 100
        assert params[1] == 5
        assert json.loads(params[2]) == [10.0, 20.0, 100.0, 120.0]
        assert params[3] is not None  # blob
        assert params[4] == 0.95
        assert params[5] is True

    def test_validate_valid_face(self):
        """Test validation of valid Face."""
        vector = np.array([0.1, 0.2], dtype=np.float32)
        face = Face(
            file_id=100,
            box_xyxy=[10.0, 20.0, 100.0, 120.0],
            face_vector=vector,
            confidence=0.95,
        )

        errors = face.validate()

        assert len(errors) == 0

    def test_validate_negative_file_id(self):
        """Test validation catches non-positive file_id."""
        face = Face(file_id=0)

        errors = face.validate()

        assert any("File ID must be positive" in e for e in errors)

    def test_validate_invalid_bbox_length(self):
        """Test validation catches invalid bbox length."""
        face = Face(file_id=100, box_xyxy=[10.0, 20.0, 100.0])

        errors = face.validate()

        assert any("Bounding box must have 4 coordinates" in e for e in errors)

    def test_validate_invalid_bbox_types(self):
        """Test validation catches non-numeric bbox coordinates."""
        face = Face(file_id=100, box_xyxy=[10.0, "20.0", 100.0, 120.0])

        errors = face.validate()

        assert any("Bounding box coordinates must be numeric" in e for e in errors)

    def test_validate_invalid_confidence(self):
        """Test validation catches invalid confidence values."""
        face = Face(file_id=100, confidence=1.5)

        errors = face.validate()

        assert any("Confidence must be between 0.0 and 1.0" in e for e in errors)

    def test_validate_wrong_dtype(self):
        """Test validation catches wrong vector dtype."""
        vector = np.array([0.1, 0.2], dtype=np.float64)
        face = Face(file_id=100, face_vector=vector)

        errors = face.validate()

        assert any("Face vector must be float32" in e for e in errors)

    def test_validate_nan_values(self):
        """Test validation catches NaN values."""
        vector = np.array([0.1, np.nan], dtype=np.float32)
        face = Face(file_id=100, face_vector=vector)

        errors = face.validate()

        assert any("contains invalid values" in e for e in errors)

    def test_is_valid(self):
        """Test is_valid method."""
        valid_face = Face(
            file_id=100,
            box_xyxy=[10.0, 20.0, 100.0, 120.0],
            confidence=0.95,
        )
        assert valid_face.is_valid() is True

        invalid_face = Face(file_id=0)
        assert invalid_face.is_valid() is False

    def test_get_box_area(self):
        """Test getting bounding box area."""
        face = Face(box_xyxy=[10.0, 20.0, 110.0, 120.0])

        area = face.get_box_area()

        assert area == 10000.0  # (110-10) * (120-20)

    def test_get_box_center(self):
        """Test getting bounding box center."""
        face = Face(box_xyxy=[10.0, 20.0, 110.0, 120.0])

        center_x, center_y = face.get_box_center()

        assert center_x == 60.0
        assert center_y == 70.0

    def test_assign_to_person(self):
        """Test assigning face to person."""
        face = Face()

        face.assign_to_person(42)

        assert face.person_id == 42

    def test_verify_assignment(self):
        """Test verifying face assignment."""
        face = Face(verified=False)

        face.verify_assignment()

        assert face.verified is True

    def test_unverify_assignment(self):
        """Test unverifying face assignment."""
        face = Face(verified=True)

        face.unverify_assignment()

        assert face.verified is False

    def test_similarity_to_person(self):
        """Test calculating similarity to person."""
        face_vector = np.array([1.0, 0.0], dtype=np.float32)
        person_vector = np.array([1.0, 0.0], dtype=np.float32)

        face = Face(face_vector=face_vector)
        person = Person(face_vector=person_vector, sample_count=1)

        similarity = face.similarity_to_person(person)

        assert similarity == pytest.approx(1.0)

    def test_similarity_to_person_null_vectors(self):
        """Test similarity calculation with null vectors."""
        face = Face()
        person = Person()

        similarity = face.similarity_to_person(person)

        assert similarity == 0.0

    def test_similarity_to_face(self):
        """Test calculating similarity to another face."""
        vector1 = np.array([1.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0], dtype=np.float32)

        face1 = Face(face_vector=vector1)
        face2 = Face(face_vector=vector2)

        similarity = face1.similarity_to_face(face2)

        assert similarity == pytest.approx(1.0)

    def test_similarity_to_face_euclidean(self):
        """Test Euclidean similarity to another face."""
        vector1 = np.array([1.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0], dtype=np.float32)

        face1 = Face(face_vector=vector1)
        face2 = Face(face_vector=vector2)

        similarity = face1.similarity_to_face(face2, metric="euclidean")

        assert similarity == pytest.approx(1.0)

    def test_similarity_to_face_null_vectors(self):
        """Test similarity to face with null vectors."""
        face1 = Face()
        face2 = Face()

        similarity = face1.similarity_to_face(face2)

        assert similarity == 0.0

    def test_similarity_to_face_mismatched_dimensions(self):
        """Test similarity to face with mismatched dimensions."""
        vector1 = np.array([1.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        face1 = Face(face_vector=vector1)
        face2 = Face(face_vector=vector2)

        with pytest.raises(ValueError, match="Vector dimensions must match"):
            face1.similarity_to_face(face2)

    def test_similarity_to_face_unknown_metric(self):
        """Test similarity to face with unknown metric."""
        vector = np.array([1.0, 0.0], dtype=np.float32)

        face1 = Face(face_vector=vector)
        face2 = Face(face_vector=vector)

        with pytest.raises(ValueError, match="Unknown similarity metric"):
            face1.similarity_to_face(face2, metric="unknown")

    def test_is_high_confidence_default_threshold(self):
        """Test is_high_confidence with default threshold."""
        face_high = Face(confidence=0.85)
        face_low = Face(confidence=0.75)

        assert face_high.is_high_confidence() is True
        assert face_low.is_high_confidence() is False

    def test_is_high_confidence_custom_threshold(self):
        """Test is_high_confidence with custom threshold."""
        face = Face(confidence=0.75)

        assert face.is_high_confidence(threshold=0.7) is True
        assert face.is_high_confidence(threshold=0.8) is False


class TestFaceSearchResult:
    """Test FaceSearchResult functionality."""

    def test_face_search_result_creation(self):
        """Test creating FaceSearchResult."""
        query_vector = np.array([1.0, 0.0], dtype=np.float32)
        result = FaceSearchResult(query_vector, threshold=0.6)

        assert np.array_equal(result.query_vector, query_vector)
        assert result.threshold == 0.6
        assert result.matches == []

    def test_add_match_above_threshold(self):
        """Test adding match above threshold."""
        query_vector = np.array([1.0, 0.0], dtype=np.float32)
        result = FaceSearchResult(query_vector, threshold=0.5)

        face = Face(id=1, file_id=100, person_id=5)
        result.add_match(face, similarity=0.8)

        assert len(result.matches) == 1
        assert result.matches[0]["face"] == face
        assert result.matches[0]["similarity"] == 0.8
        assert result.matches[0]["file_id"] == 100
        assert result.matches[0]["person_id"] == 5

    def test_add_match_below_threshold(self):
        """Test that matches below threshold are not added."""
        query_vector = np.array([1.0, 0.0], dtype=np.float32)
        result = FaceSearchResult(query_vector, threshold=0.5)

        face = Face(id=1, file_id=100)
        result.add_match(face, similarity=0.3)

        assert len(result.matches) == 0

    def test_add_match_at_threshold(self):
        """Test that matches at threshold are added."""
        query_vector = np.array([1.0, 0.0], dtype=np.float32)
        result = FaceSearchResult(query_vector, threshold=0.5)

        face = Face(id=1, file_id=100)
        result.add_match(face, similarity=0.5)

        assert len(result.matches) == 1

    def test_sort_by_similarity(self):
        """Test sorting matches by similarity."""
        query_vector = np.array([1.0, 0.0], dtype=np.float32)
        result = FaceSearchResult(query_vector, threshold=0.0)

        face1 = Face(id=1, file_id=100)
        face2 = Face(id=2, file_id=101)
        face3 = Face(id=3, file_id=102)

        result.add_match(face1, similarity=0.6)
        result.add_match(face2, similarity=0.9)
        result.add_match(face3, similarity=0.7)

        result.sort_by_similarity()

        assert result.matches[0]["similarity"] == 0.9
        assert result.matches[1]["similarity"] == 0.7
        assert result.matches[2]["similarity"] == 0.6

    def test_get_top_matches(self):
        """Test getting top N matches."""
        query_vector = np.array([1.0, 0.0], dtype=np.float32)
        result = FaceSearchResult(query_vector, threshold=0.0)

        for i in range(20):
            face = Face(id=i, file_id=100 + i)
            result.add_match(face, similarity=0.5 + i * 0.01)

        top_matches = result.get_top_matches(n=5)

        assert len(top_matches) == 5
        # Should be sorted highest to lowest
        assert top_matches[0]["similarity"] > top_matches[4]["similarity"]

    def test_get_unique_files(self):
        """Test getting unique file IDs."""
        query_vector = np.array([1.0, 0.0], dtype=np.float32)
        result = FaceSearchResult(query_vector, threshold=0.0)

        face1 = Face(id=1, file_id=100)
        face2 = Face(id=2, file_id=100)  # Same file
        face3 = Face(id=3, file_id=101)

        result.add_match(face1, similarity=0.8)
        result.add_match(face2, similarity=0.7)
        result.add_match(face3, similarity=0.6)

        unique_files = result.get_unique_files()

        assert len(unique_files) == 2
        assert 100 in unique_files
        assert 101 in unique_files

    def test_get_matches_by_person(self):
        """Test getting matches for specific person."""
        query_vector = np.array([1.0, 0.0], dtype=np.float32)
        result = FaceSearchResult(query_vector, threshold=0.0)

        face1 = Face(id=1, file_id=100, person_id=5)
        face2 = Face(id=2, file_id=101, person_id=6)
        face3 = Face(id=3, file_id=102, person_id=5)

        result.add_match(face1, similarity=0.8)
        result.add_match(face2, similarity=0.7)
        result.add_match(face3, similarity=0.6)

        person_matches = result.get_matches_by_person(person_id=5)

        assert len(person_matches) == 2
        assert all(m["person_id"] == 5 for m in person_matches)
