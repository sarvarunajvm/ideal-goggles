"""Person and Face models for face recognition functionality."""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
import numpy as np
from datetime import datetime
import json
import struct


@dataclass
class Person:
    """Enrolled person for face-based search functionality."""

    id: Optional[int] = None
    name: str = ""
    face_vector: Optional[np.ndarray] = None
    sample_count: int = 0
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    active: bool = True

    def __post_init__(self):
        """Post-initialization validation and defaults."""
        if self.created_at is None:
            self.created_at = datetime.now().timestamp()

        if self.updated_at is None:
            self.updated_at = self.created_at

        # Ensure face_vector is numpy array if provided
        if self.face_vector is not None and not isinstance(self.face_vector, np.ndarray):
            self.face_vector = np.array(self.face_vector, dtype=np.float32)

    @classmethod
    def create_from_face_vectors(cls, name: str, face_vectors: List[np.ndarray]) -> "Person":
        """Create Person by averaging multiple face vectors."""
        if not face_vectors:
            raise ValueError("At least one face vector is required")

        if not name.strip():
            raise ValueError("Person name cannot be empty")

        # Validate all vectors have same dimension
        dimensions = [len(vec) for vec in face_vectors]
        if len(set(dimensions)) > 1:
            raise ValueError("All face vectors must have the same dimension")

        # Average the vectors
        stacked_vectors = np.stack(face_vectors)
        averaged_vector = np.mean(stacked_vectors, axis=0)

        # Normalize the averaged vector
        norm = np.linalg.norm(averaged_vector)
        if norm > 0:
            averaged_vector = averaged_vector / norm

        return cls(
            name=name.strip(),
            face_vector=averaged_vector,
            sample_count=len(face_vectors),
            created_at=datetime.now().timestamp(),
            updated_at=datetime.now().timestamp(),
            active=True
        )

    @classmethod
    def from_db_row(cls, row) -> "Person":
        """Create Person from database row."""
        face_vector = None
        if row['face_vector']:
            face_vector = cls._blob_to_numpy(row['face_vector'])

        return cls(
            id=row['id'],
            name=row['name'],
            face_vector=face_vector,
            sample_count=row['sample_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            active=bool(row['active']),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'sample_count': self.sample_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'active': self.active,
            'face_vector_dimension': len(self.face_vector) if self.face_vector is not None else None,
        }

    def to_db_params(self) -> tuple:
        """Convert to database parameters for insertion."""
        face_vector_blob = None
        if self.face_vector is not None:
            face_vector_blob = self._numpy_to_blob(self.face_vector)

        return (
            self.name,
            face_vector_blob,
            self.sample_count,
            self.created_at,
            self.updated_at,
            self.active
        )

    def validate(self) -> List[str]:
        """Validate person data and return list of errors."""
        errors = []

        if not self.name or not self.name.strip():
            errors.append("Person name cannot be empty")

        if len(self.name) > 255:
            errors.append("Person name too long (max 255 characters)")

        if self.sample_count <= 0:
            errors.append("Sample count must be positive")

        if self.face_vector is None:
            errors.append("Face vector is required")
        else:
            if self.face_vector.dtype != np.float32:
                errors.append("Face vector must be float32")

            if len(self.face_vector) not in [512, 1024]:  # Common face embedding dimensions
                errors.append(f"Unexpected face vector dimension: {len(self.face_vector)}")

            if np.any(np.isnan(self.face_vector)) or np.any(np.isinf(self.face_vector)):
                errors.append("Face vector contains invalid values (NaN or Inf)")

        return errors

    def is_valid(self) -> bool:
        """Check if person data is valid."""
        return len(self.validate()) == 0

    def update_face_vector(self, new_face_vectors: List[np.ndarray]):
        """Update face vector by including new samples."""
        if not new_face_vectors:
            return

        all_vectors = new_face_vectors.copy()
        if self.face_vector is not None:
            # Include current vector (weighted by sample count)
            for _ in range(self.sample_count):
                all_vectors.append(self.face_vector)

        # Recalculate averaged vector
        stacked_vectors = np.stack(all_vectors)
        averaged_vector = np.mean(stacked_vectors, axis=0)

        # Normalize
        norm = np.linalg.norm(averaged_vector)
        if norm > 0:
            averaged_vector = averaged_vector / norm

        self.face_vector = averaged_vector
        self.sample_count += len(new_face_vectors)
        self.updated_at = datetime.now().timestamp()

    def similarity_to_vector(self, face_vector: np.ndarray, metric: str = "cosine") -> float:
        """Calculate similarity to a face vector."""
        if self.face_vector is None:
            return 0.0

        if len(self.face_vector) != len(face_vector):
            raise ValueError("Vector dimensions must match")

        if metric == "cosine":
            # Cosine similarity (higher is more similar)
            similarity = float(np.dot(self.face_vector, face_vector))
            return similarity
        elif metric == "euclidean":
            # Euclidean distance (lower is more similar)
            distance = float(np.linalg.norm(self.face_vector - face_vector))
            return 1.0 / (1.0 + distance)  # Convert to similarity score
        else:
            raise ValueError(f"Unknown similarity metric: {metric}")

    def deactivate(self):
        """Deactivate person (soft delete)."""
        self.active = False
        self.updated_at = datetime.now().timestamp()

    def reactivate(self):
        """Reactivate person."""
        self.active = True
        self.updated_at = datetime.now().timestamp()

    @staticmethod
    def _numpy_to_blob(vector: np.ndarray) -> bytes:
        """Convert numpy array to blob for database storage."""
        dimension = len(vector)
        blob = struct.pack('<I', dimension)
        blob += vector.astype(np.float32).tobytes()
        return blob

    @staticmethod
    def _blob_to_numpy(blob: bytes) -> np.ndarray:
        """Convert blob from database to numpy array."""
        if len(blob) < 4:
            raise ValueError("Invalid blob: too short")

        dimension = struct.unpack('<I', blob[:4])[0]
        expected_size = 4 + dimension * 4
        if len(blob) != expected_size:
            raise ValueError(f"Invalid blob size: expected {expected_size}, got {len(blob)}")

        vector_bytes = blob[4:]
        vector = np.frombuffer(vector_bytes, dtype=np.float32)
        return vector


@dataclass
class Face:
    """Individual face detection within photos."""

    id: Optional[int] = None
    file_id: int = 0
    person_id: Optional[int] = None
    box_xyxy: List[float] = None
    face_vector: Optional[np.ndarray] = None
    confidence: float = 0.0
    verified: bool = False

    def __post_init__(self):
        """Post-initialization validation."""
        if self.box_xyxy is None:
            self.box_xyxy = [0.0, 0.0, 0.0, 0.0]

        # Ensure face_vector is numpy array if provided
        if self.face_vector is not None and not isinstance(self.face_vector, np.ndarray):
            self.face_vector = np.array(self.face_vector, dtype=np.float32)

    @classmethod
    def from_detection_result(cls, file_id: int, detection_result: Dict[str, Any]) -> "Face":
        """Create Face from face detection result."""
        # Extract bounding box
        box = detection_result.get('bbox', [0, 0, 0, 0])
        if len(box) != 4:
            raise ValueError("Bounding box must have 4 coordinates")

        # Extract face embedding
        embedding = detection_result.get('embedding')
        if embedding is not None:
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding, dtype=np.float32)

            # Normalize if needed
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

        return cls(
            file_id=file_id,
            box_xyxy=box,
            face_vector=embedding,
            confidence=detection_result.get('confidence', 0.0),
            verified=False
        )

    @classmethod
    def from_db_row(cls, row) -> "Face":
        """Create Face from database row."""
        # Parse bounding box JSON
        box_xyxy = json.loads(row['box_xyxy'])

        # Decode face vector
        face_vector = None
        if row['face_vector']:
            face_vector = Person._blob_to_numpy(row['face_vector'])

        return cls(
            id=row['id'],
            file_id=row['file_id'],
            person_id=row['person_id'],
            box_xyxy=box_xyxy,
            face_vector=face_vector,
            confidence=row['confidence'],
            verified=bool(row['verified']),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'person_id': self.person_id,
            'box_xyxy': self.box_xyxy,
            'confidence': self.confidence,
            'verified': self.verified,
            'face_vector_dimension': len(self.face_vector) if self.face_vector is not None else None,
        }

    def to_db_params(self) -> tuple:
        """Convert to database parameters for insertion."""
        box_json = json.dumps(self.box_xyxy)

        face_vector_blob = None
        if self.face_vector is not None:
            face_vector_blob = Person._numpy_to_blob(self.face_vector)

        return (
            self.file_id,
            self.person_id,
            box_json,
            face_vector_blob,
            self.confidence,
            self.verified
        )

    def validate(self) -> List[str]:
        """Validate face data and return list of errors."""
        errors = []

        if self.file_id <= 0:
            errors.append("File ID must be positive")

        if len(self.box_xyxy) != 4:
            errors.append("Bounding box must have 4 coordinates")

        if not all(isinstance(coord, (int, float)) for coord in self.box_xyxy):
            errors.append("Bounding box coordinates must be numeric")

        if not (0.0 <= self.confidence <= 1.0):
            errors.append("Confidence must be between 0.0 and 1.0")

        if self.face_vector is not None:
            if self.face_vector.dtype != np.float32:
                errors.append("Face vector must be float32")

            if np.any(np.isnan(self.face_vector)) or np.any(np.isinf(self.face_vector)):
                errors.append("Face vector contains invalid values (NaN or Inf)")

        return errors

    def is_valid(self) -> bool:
        """Check if face data is valid."""
        return len(self.validate()) == 0

    def get_box_area(self) -> float:
        """Get bounding box area."""
        x1, y1, x2, y2 = self.box_xyxy
        return abs((x2 - x1) * (y2 - y1))

    def get_box_center(self) -> Tuple[float, float]:
        """Get bounding box center coordinates."""
        x1, y1, x2, y2 = self.box_xyxy
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return center_x, center_y

    def assign_to_person(self, person_id: int):
        """Assign face to a person."""
        self.person_id = person_id

    def verify_assignment(self):
        """Mark face assignment as manually verified."""
        self.verified = True

    def unverify_assignment(self):
        """Mark face assignment as unverified."""
        self.verified = False

    def similarity_to_person(self, person: Person, metric: str = "cosine") -> float:
        """Calculate similarity to a person's face vector."""
        if self.face_vector is None or person.face_vector is None:
            return 0.0

        return person.similarity_to_vector(self.face_vector, metric)

    def similarity_to_face(self, other_face: "Face", metric: str = "cosine") -> float:
        """Calculate similarity to another face."""
        if self.face_vector is None or other_face.face_vector is None:
            return 0.0

        if len(self.face_vector) != len(other_face.face_vector):
            raise ValueError("Vector dimensions must match")

        if metric == "cosine":
            similarity = float(np.dot(self.face_vector, other_face.face_vector))
            return similarity
        elif metric == "euclidean":
            distance = float(np.linalg.norm(self.face_vector - other_face.face_vector))
            return 1.0 / (1.0 + distance)
        else:
            raise ValueError(f"Unknown similarity metric: {metric}")

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if face detection confidence is high."""
        return self.confidence >= threshold


class FaceSearchResult:
    """Result of face search operation."""

    def __init__(self, query_vector: np.ndarray, threshold: float = 0.5):
        self.query_vector = query_vector
        self.threshold = threshold
        self.matches = []

    def add_match(self, face: Face, similarity: float):
        """Add a face match to results."""
        if similarity >= self.threshold:
            self.matches.append({
                'face': face,
                'similarity': similarity,
                'file_id': face.file_id,
                'person_id': face.person_id,
            })

    def sort_by_similarity(self):
        """Sort matches by similarity (highest first)."""
        self.matches.sort(key=lambda x: x['similarity'], reverse=True)

    def get_top_matches(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N matches."""
        self.sort_by_similarity()
        return self.matches[:n]

    def get_unique_files(self) -> List[int]:
        """Get unique file IDs from matches."""
        file_ids = [match['file_id'] for match in self.matches]
        return list(set(file_ids))

    def get_matches_by_person(self, person_id: int) -> List[Dict[str, Any]]:
        """Get matches for specific person."""
        return [match for match in self.matches if match['person_id'] == person_id]