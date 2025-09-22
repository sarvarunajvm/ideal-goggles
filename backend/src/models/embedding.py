"""Embedding model for photo search system."""

import struct
from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass
class Embedding:
    """Vector embeddings for semantic and visual similarity search."""

    file_id: int
    clip_vector: np.ndarray
    embedding_model: str
    processed_at: float | None = None

    def __post_init__(self):
        """Post-initialization validation."""
        if self.processed_at is None:
            self.processed_at = datetime.now().timestamp()

        # Ensure clip_vector is numpy array
        if not isinstance(self.clip_vector, np.ndarray):
            self.clip_vector = np.array(self.clip_vector, dtype=np.float32)

        # Normalize vector if not already normalized
        if self.clip_vector.size > 0:
            norm = np.linalg.norm(self.clip_vector)
            if norm > 0 and not np.isclose(norm, 1.0, rtol=1e-6):
                self.clip_vector = self.clip_vector / norm

    @classmethod
    def from_clip_output(
        cls,
        file_id: int,
        clip_features: np.ndarray | list[float],
        model_name: str = "clip-vit-b-32",
    ) -> "Embedding":
        """Create Embedding from CLIP model output."""
        # Convert to numpy array if needed
        if not isinstance(clip_features, np.ndarray):
            clip_features = np.array(clip_features, dtype=np.float32)

        # Flatten if multi-dimensional
        if clip_features.ndim > 1:
            clip_features = clip_features.flatten()

        return cls(
            file_id=file_id,
            clip_vector=clip_features,
            embedding_model=model_name,
            processed_at=datetime.now().timestamp(),
        )

    @classmethod
    def from_db_row(cls, row) -> "Embedding":
        """Create Embedding from database row."""
        # Decode blob to numpy array
        vector_blob = row["clip_vector"]
        clip_vector = cls._blob_to_numpy(vector_blob)

        return cls(
            file_id=row["file_id"],
            clip_vector=clip_vector,
            embedding_model=row["embedding_model"],
            processed_at=row["processed_at"],
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "file_id": self.file_id,
            "clip_vector": self.clip_vector.tolist(),
            "embedding_model": self.embedding_model,
            "processed_at": self.processed_at,
            "vector_dimension": len(self.clip_vector),
            "vector_norm": float(np.linalg.norm(self.clip_vector)),
        }

    def to_db_params(self) -> tuple:
        """Convert to database parameters for insertion."""
        vector_blob = self._numpy_to_blob(self.clip_vector)
        return (self.file_id, vector_blob, self.embedding_model, self.processed_at)

    def validate(self) -> list[str]:
        """Validate embedding data and return list of errors."""
        errors = []

        if self.file_id <= 0:
            errors.append("File ID must be positive")

        if self.clip_vector.size == 0:
            errors.append("CLIP vector cannot be empty")

        if self.clip_vector.dtype != np.float32:
            errors.append("CLIP vector must be float32")

        # Check for standard CLIP dimensions
        if len(self.clip_vector) not in [512, 768, 1024]:
            errors.append(f"Unexpected CLIP vector dimension: {len(self.clip_vector)}")

        if not self.embedding_model:
            errors.append("Embedding model name is required")

        # Check for valid values
        if np.any(np.isnan(self.clip_vector)) or np.any(np.isinf(self.clip_vector)):
            errors.append("CLIP vector contains invalid values (NaN or Inf)")

        return errors

    def is_valid(self) -> bool:
        """Check if embedding data is valid."""
        return len(self.validate()) == 0

    def cosine_similarity(self, other: "Embedding") -> float:
        """Calculate cosine similarity with another embedding."""
        if len(self.clip_vector) != len(other.clip_vector):
            msg = "Vector dimensions must match"
            raise ValueError(msg)

        # Since vectors are normalized, dot product equals cosine similarity
        similarity = np.dot(self.clip_vector, other.clip_vector)
        return float(similarity)

    def euclidean_distance(self, other: "Embedding") -> float:
        """Calculate Euclidean distance with another embedding."""
        if len(self.clip_vector) != len(other.clip_vector):
            msg = "Vector dimensions must match"
            raise ValueError(msg)

        distance = np.linalg.norm(self.clip_vector - other.clip_vector)
        return float(distance)

    def get_dimension(self) -> int:
        """Get embedding vector dimension."""
        return len(self.clip_vector)

    def get_norm(self) -> float:
        """Get vector norm (should be close to 1.0 for normalized vectors)."""
        return float(np.linalg.norm(self.clip_vector))

    def is_normalized(self, tolerance: float = 1e-6) -> bool:
        """Check if vector is normalized."""
        return np.isclose(self.get_norm(), 1.0, rtol=tolerance)

    def normalize(self):
        """Normalize the vector in-place."""
        norm = np.linalg.norm(self.clip_vector)
        if norm > 0:
            self.clip_vector = self.clip_vector / norm

    def get_vector_stats(self) -> dict:
        """Get statistics about the vector."""
        return {
            "dimension": self.get_dimension(),
            "norm": self.get_norm(),
            "mean": float(np.mean(self.clip_vector)),
            "std": float(np.std(self.clip_vector)),
            "min": float(np.min(self.clip_vector)),
            "max": float(np.max(self.clip_vector)),
            "is_normalized": self.is_normalized(),
        }

    @staticmethod
    def _numpy_to_blob(vector: np.ndarray) -> bytes:
        """Convert numpy array to blob for database storage."""
        # Store dimension first, then float32 data
        dimension = len(vector)
        blob = struct.pack("<I", dimension)  # 4 bytes for dimension
        blob += vector.astype(np.float32).tobytes()
        return blob

    @staticmethod
    def _blob_to_numpy(blob: bytes) -> np.ndarray:
        """Convert blob from database to numpy array."""
        if len(blob) < 4:
            msg = "Invalid blob: too short"
            raise ValueError(msg)

        # Read dimension
        dimension = struct.unpack("<I", blob[:4])[0]

        # Read vector data
        expected_size = 4 + dimension * 4  # 4 bytes for dim + 4 bytes per float32
        if len(blob) != expected_size:
            msg = f"Invalid blob size: expected {expected_size}, got {len(blob)}"
            raise ValueError(msg)

        vector_bytes = blob[4:]
        vector = np.frombuffer(vector_bytes, dtype=np.float32)

        if len(vector) != dimension:
            msg = f"Dimension mismatch: expected {dimension}, got {len(vector)}"
            raise ValueError(msg)

        return vector

    @staticmethod
    def batch_cosine_similarity(
        query_vector: np.ndarray, vectors: list[np.ndarray]
    ) -> np.ndarray:
        """Calculate cosine similarity between query and batch of vectors."""
        if not vectors:
            return np.array([])

        # Stack vectors into matrix
        matrix = np.stack(vectors)

        # Calculate dot products (cosine similarity for normalized vectors)
        return np.dot(matrix, query_vector)

    @staticmethod
    def create_random_embedding(
        file_id: int, dimension: int = 512, model_name: str = "random"
    ) -> "Embedding":
        """Create random embedding for testing purposes."""
        # Generate random normalized vector
        vector = np.random.randn(dimension).astype(np.float32)
        vector = vector / np.linalg.norm(vector)

        return Embedding(
            file_id=file_id,
            clip_vector=vector,
            embedding_model=model_name,
            processed_at=datetime.now().timestamp(),
        )


class EmbeddingStats:
    """Statistics for embedding processing."""

    def __init__(self):
        self.total_embeddings = 0
        self.model_counts = {}
        self.dimension_counts = {}
        self.total_processing_time = 0.0

    def add_embedding(self, embedding: Embedding, processing_time: float = 0.0):
        """Add embedding to statistics."""
        self.total_embeddings += 1
        self.total_processing_time += processing_time

        # Track model usage
        model = embedding.embedding_model
        if model in self.model_counts:
            self.model_counts[model] += 1
        else:
            self.model_counts[model] = 1

        # Track dimensions
        dimension = embedding.get_dimension()
        if dimension in self.dimension_counts:
            self.dimension_counts[dimension] += 1
        else:
            self.dimension_counts[dimension] = 1

    def get_average_processing_time(self) -> float:
        """Get average processing time per embedding."""
        if self.total_embeddings == 0:
            return 0.0
        return self.total_processing_time / self.total_embeddings

    def to_dict(self) -> dict:
        """Convert statistics to dictionary."""
        return {
            "total_embeddings": self.total_embeddings,
            "model_counts": self.model_counts,
            "dimension_counts": self.dimension_counts,
            "total_processing_time": round(self.total_processing_time, 2),
            "average_processing_time": round(self.get_average_processing_time(), 3),
        }
