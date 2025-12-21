"""Unit tests for Embedding model."""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.models.embedding import Embedding, EmbeddingStats


class TestEmbeddingModel:
    """Test Embedding model functionality."""

    def test_embedding_creation_with_valid_data(self):
        """Test creating an Embedding with valid data."""
        embedding = Embedding(
            file_id=1,
            clip_vector=np.array([0.1, 0.2, 0.3], dtype=np.float32),
            embedding_model="clip-vit-b32",
            processed_at=1640995200.0,
        )

        assert embedding.file_id == 1
        # Vector is auto-normalized in __post_init__
        assert embedding.clip_vector.shape == (3,)
        assert embedding.embedding_model == "clip-vit-b32"
        assert embedding.processed_at == 1640995200.0

    def test_embedding_creation_with_defaults(self):
        """Test Embedding creation with default values."""
        test_vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with patch("src.models.embedding.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 1640995200.0
            embedding = Embedding(
                file_id=1,
                clip_vector=test_vector,
                embedding_model="clip-vit-b32",
            )

        assert embedding.file_id == 1
        # Vector is auto-normalized in __post_init__
        assert embedding.clip_vector.shape == (3,)
        assert embedding.embedding_model == "clip-vit-b32"  # Default
        assert embedding.processed_at == 1640995200.0

    def test_to_dict(self):
        """Test converting Embedding to dictionary."""
        embedding = Embedding(
            file_id=1,
            clip_vector=np.array([0.1, 0.2, 0.3], dtype=np.float32),
            embedding_model="clip-vit-b32",
            processed_at=1640995200.0,
        )

        embedding_dict = embedding.to_dict()

        assert embedding_dict["file_id"] == 1
        assert "clip_vector" in embedding_dict
        assert embedding_dict["embedding_model"] == "clip-vit-b32"
        assert embedding_dict["processed_at"] == 1640995200.0
        assert embedding_dict["vector_dimension"] == 3

    def test_to_dict_includes_vector_stats(self):
        """Test that to_dict includes vector statistics."""
        vector = np.array([0.1, 0.2, -0.1, 0.5], dtype=np.float32)
        embedding = Embedding(
            file_id=1,
            clip_vector=vector,
            embedding_model="clip-vit-b32",
            processed_at=1640995200.0,
        )

        embedding_dict = embedding.to_dict()

        assert embedding_dict["vector_dimension"] == 4
        assert "vector_norm" in embedding_dict
        assert embedding_dict["vector_norm"] > 0

    def test_str_representation(self):
        """Test string representation of Embedding."""
        embedding = Embedding(
            file_id=1,
            clip_vector=np.array([0.1, 0.2, 0.3], dtype=np.float32),
            embedding_model="clip-vit-b32",
            processed_at=1640995200.0,
        )

        str_repr = str(embedding)
        assert "file_id=1" in str_repr
        assert "clip-vit-b32" in str_repr
        # The actual __repr__ doesn't include dim, just the vector array
        assert "clip_vector" in str_repr

    def test_post_init_converts_list(self):
        """Test that __post_init__ converts list to numpy array."""
        embedding = Embedding(
            file_id=1, clip_vector=[0.1, 0.2, 0.3], embedding_model="test"
        )

        assert isinstance(embedding.clip_vector, np.ndarray)
        assert embedding.clip_vector.dtype == np.float32

    def test_from_clip_output_with_list(self):
        """Test creating Embedding from CLIP output as list."""
        features = [0.5, 0.5, 0.5, 0.5]
        embedding = Embedding.from_clip_output(file_id=1, clip_features=features)

        assert embedding.file_id == 1
        assert isinstance(embedding.clip_vector, np.ndarray)
        assert len(embedding.clip_vector) == 4

    def test_from_clip_output_multidimensional(self):
        """Test creating Embedding from multi-dimensional array."""
        features = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
        embedding = Embedding.from_clip_output(
            file_id=1, clip_features=features, model_name="custom-model"
        )

        assert embedding.file_id == 1
        assert embedding.embedding_model == "custom-model"
        # Should be flattened
        assert embedding.clip_vector.ndim == 1
        assert len(embedding.clip_vector) == 4

    def test_from_db_row(self):
        """Test creating Embedding from database row."""
        # Use a normalized 512-dimensional vector since post_init normalizes
        vector = np.array([0.6, 0.8] + [0.0] * 510, dtype=np.float32)
        blob = Embedding._numpy_to_blob(vector)

        row = {
            "file_id": 1,
            "clip_vector": blob,
            "embedding_model": "test-model",
            "processed_at": 1640995200.0,
        }

        embedding = Embedding.from_db_row(row)

        assert embedding.file_id == 1
        assert embedding.embedding_model == "test-model"
        assert embedding.processed_at == 1640995200.0
        # Vector will be normalized, so check normalized version
        np.testing.assert_array_almost_equal(embedding.clip_vector, vector)

    def test_to_db_params(self):
        """Test converting to database parameters."""
        vector = np.array([0.1, 0.2, 0.3] + [0.1] * 509, dtype=np.float32)
        embedding = Embedding(
            file_id=1,
            clip_vector=vector,
            embedding_model="test-model",
            processed_at=1640995200.0,
        )

        params = embedding.to_db_params()

        assert params[0] == 1  # file_id
        assert isinstance(params[1], bytes)  # blob
        assert params[2] == "test-model"  # embedding_model
        assert params[3] == 1640995200.0  # processed_at

    def test_validate_valid_embedding(self):
        """Test validation of valid embedding."""
        vector = np.array([0.1] * 512, dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        errors = embedding.validate()
        assert len(errors) == 0

    def test_validate_negative_file_id(self):
        """Test validation catches negative file_id."""
        vector = np.array([0.1] * 512, dtype=np.float32)
        embedding = Embedding(file_id=0, clip_vector=vector, embedding_model="test")

        errors = embedding.validate()
        assert any("File ID must be positive" in e for e in errors)

    def test_validate_empty_vector(self):
        """Test validation catches empty vector."""
        vector = np.array([], dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        errors = embedding.validate()
        assert any("CLIP vector cannot be empty" in e for e in errors)

    def test_validate_wrong_dtype(self):
        """Test validation catches wrong dtype."""
        vector = np.array([0.1] * 512, dtype=np.float64)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        errors = embedding.validate()
        assert any("CLIP vector must be float32" in e for e in errors)

    def test_validate_unexpected_dimension(self):
        """Test validation catches unexpected dimension."""
        vector = np.array([0.1] * 256, dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        errors = embedding.validate()
        assert any("Unexpected CLIP vector dimension" in e for e in errors)

    def test_validate_missing_model_name(self):
        """Test validation catches missing model name."""
        vector = np.array([0.1] * 512, dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="")

        errors = embedding.validate()
        assert any("Embedding model name is required" in e for e in errors)

    def test_validate_nan_values(self):
        """Test validation catches NaN values."""
        vector = np.array([0.1, np.nan] + [0.1] * 510, dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        errors = embedding.validate()
        assert any("invalid values" in e for e in errors)

    def test_validate_inf_values(self):
        """Test validation catches Inf values."""
        vector = np.array([0.1, np.inf] + [0.1] * 510, dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        errors = embedding.validate()
        assert any("invalid values" in e for e in errors)

    def test_is_valid(self):
        """Test is_valid method."""
        valid_vector = np.array([0.1] * 512, dtype=np.float32)
        valid_embedding = Embedding(
            file_id=1, clip_vector=valid_vector, embedding_model="test"
        )
        assert valid_embedding.is_valid() is True

        invalid_embedding = Embedding(
            file_id=0, clip_vector=valid_vector, embedding_model="test"
        )
        assert invalid_embedding.is_valid() is False

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vector1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        emb1 = Embedding(file_id=1, clip_vector=vector1, embedding_model="test")
        emb2 = Embedding(file_id=2, clip_vector=vector2, embedding_model="test")

        similarity = emb1.cosine_similarity(emb2)
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity of orthogonal vectors."""
        vector1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vector2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        emb1 = Embedding(file_id=1, clip_vector=vector1, embedding_model="test")
        emb2 = Embedding(file_id=2, clip_vector=vector2, embedding_model="test")

        similarity = emb1.cosine_similarity(emb2)
        assert similarity == pytest.approx(0.0)

    def test_cosine_similarity_mismatched_dimensions(self):
        """Test cosine similarity with mismatched dimensions."""
        vector1 = np.array([1.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        emb1 = Embedding(file_id=1, clip_vector=vector1, embedding_model="test")
        emb2 = Embedding(file_id=2, clip_vector=vector2, embedding_model="test")

        with pytest.raises(ValueError, match="Vector dimensions must match"):
            emb1.cosine_similarity(emb2)

    def test_euclidean_distance(self):
        """Test Euclidean distance calculation."""
        vector1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        emb1 = Embedding(file_id=1, clip_vector=vector1, embedding_model="test")
        emb2 = Embedding(file_id=2, clip_vector=vector2, embedding_model="test")

        distance = emb1.euclidean_distance(emb2)
        assert distance == pytest.approx(0.0)

    def test_euclidean_distance_mismatched_dimensions(self):
        """Test Euclidean distance with mismatched dimensions."""
        vector1 = np.array([1.0, 0.0], dtype=np.float32)
        vector2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        emb1 = Embedding(file_id=1, clip_vector=vector1, embedding_model="test")
        emb2 = Embedding(file_id=2, clip_vector=vector2, embedding_model="test")

        with pytest.raises(ValueError, match="Vector dimensions must match"):
            emb1.euclidean_distance(emb2)

    def test_get_dimension(self):
        """Test get_dimension method."""
        vector = np.array([0.1] * 512, dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        assert embedding.get_dimension() == 512

    def test_get_norm(self):
        """Test get_norm method."""
        vector = np.array([0.6, 0.8, 0.0], dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        # Vector should be normalized during __post_init__
        assert embedding.get_norm() == pytest.approx(1.0)

    def test_is_normalized(self):
        """Test is_normalized method."""
        # Create a already normalized vector
        vector = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        # Should remain normalized
        assert embedding.is_normalized()

    def test_normalize(self):
        """Test normalize method."""
        # Create embedding WITHOUT going through __init__ to avoid auto-normalization
        embedding = Embedding.__new__(Embedding)
        embedding.file_id = 1
        embedding.clip_vector = np.array([3.0, 4.0, 0.0], dtype=np.float32)
        embedding.embedding_model = "test"
        embedding.processed_at = 1640995200.0

        # Manually normalize
        embedding.normalize()

        assert embedding.is_normalized()
        assert embedding.clip_vector[0] == pytest.approx(0.6)
        assert embedding.clip_vector[1] == pytest.approx(0.8)

    def test_get_vector_stats(self):
        """Test get_vector_stats method."""
        vector = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        stats = embedding.get_vector_stats()

        assert "dimension" in stats
        assert "norm" in stats
        assert "mean" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert "is_normalized" in stats

    def test_numpy_to_blob(self):
        """Test _numpy_to_blob method."""
        vector = np.array([0.1, 0.2, 0.3] + [0.1] * 509, dtype=np.float32)
        blob = Embedding._numpy_to_blob(vector)

        assert isinstance(blob, bytes)
        assert len(blob) == 2048  # 512 floats * 4 bytes each

    def test_blob_to_numpy(self):
        """Test _blob_to_numpy method."""
        original = np.array([0.1, 0.2, 0.3] + [0.1] * 509, dtype=np.float32)
        blob = Embedding._numpy_to_blob(original)
        restored = Embedding._blob_to_numpy(blob)

        np.testing.assert_array_almost_equal(restored, original)

    def test_blob_to_numpy_too_short(self):
        """Test _blob_to_numpy with invalid blob."""
        with pytest.raises(ValueError, match="Invalid blob size"):
            Embedding._blob_to_numpy(b"abc")

    def test_blob_to_numpy_wrong_size(self):
        """Test _blob_to_numpy with wrong size."""
        import struct

        # Create blob with dimension 3 but only 2 floats
        blob = struct.pack("<I", 3)  # Says dimension is 3
        blob += struct.pack("<ff", 0.1, 0.2)  # But only 2 floats

        with pytest.raises(ValueError, match="Invalid blob size"):
            Embedding._blob_to_numpy(blob)

    def test_blob_to_numpy_dimension_mismatch(self):
        """Test _blob_to_numpy with dimension mismatch."""
        import struct

        # Create blob with wrong size (not 512 floats)
        # Create blob with only 4 floats (16 bytes) instead of 512
        blob = struct.pack("<ffff", 0.1, 0.2, 0.3, 0.4)

        # This should raise ValueError for invalid blob size
        with pytest.raises(ValueError, match="Invalid blob size"):
            Embedding._blob_to_numpy(blob)

    def test_batch_cosine_similarity(self):
        """Test batch_cosine_similarity static method."""
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vectors = [
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0, 0.0], dtype=np.float32),
        ]

        similarities = Embedding.batch_cosine_similarity(query, vectors)

        assert len(similarities) == 2
        assert similarities[0] == pytest.approx(1.0)
        assert similarities[1] == pytest.approx(0.0)

    def test_batch_cosine_similarity_empty(self):
        """Test batch_cosine_similarity with empty list."""
        query = np.array([1.0, 0.0], dtype=np.float32)
        vectors = []

        similarities = Embedding.batch_cosine_similarity(query, vectors)

        assert len(similarities) == 0

    def test_create_random_embedding(self):
        """Test create_random_embedding static method."""
        embedding = Embedding.create_random_embedding(file_id=1, dimension=512)

        assert embedding.file_id == 1
        assert len(embedding.clip_vector) == 512
        assert embedding.embedding_model == "random"
        # Random vectors are normalized during creation
        assert embedding.get_norm() == pytest.approx(1.0, rel=1e-5)

    def test_create_random_embedding_custom(self):
        """Test create_random_embedding with custom parameters."""
        embedding = Embedding.create_random_embedding(
            file_id=5, dimension=768, model_name="custom-random"
        )

        assert embedding.file_id == 5
        assert len(embedding.clip_vector) == 768
        assert embedding.embedding_model == "custom-random"


class TestEmbeddingStats:
    """Test EmbeddingStats functionality."""

    def test_embedding_stats_creation(self):
        """Test creating EmbeddingStats."""
        stats = EmbeddingStats()

        assert stats.total_embeddings == 0
        assert stats.model_counts == {}
        assert stats.dimension_counts == {}
        assert stats.total_processing_time == 0.0

    def test_add_embedding(self):
        """Test adding embedding to stats."""
        stats = EmbeddingStats()
        vector = np.array([0.1] * 512, dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")

        stats.add_embedding(embedding, processing_time=1.5)

        assert stats.total_embeddings == 1
        assert stats.model_counts["test"] == 1
        assert stats.dimension_counts[512] == 1
        assert stats.total_processing_time == 1.5

    def test_add_multiple_embeddings(self):
        """Test adding multiple embeddings."""
        stats = EmbeddingStats()

        for i in range(5):
            vector = np.array([0.1] * 512, dtype=np.float32)
            embedding = Embedding(
                file_id=i, clip_vector=vector, embedding_model="model-a"
            )
            stats.add_embedding(embedding, processing_time=1.0)

        for i in range(3):
            vector = np.array([0.1] * 768, dtype=np.float32)
            embedding = Embedding(
                file_id=i + 5, clip_vector=vector, embedding_model="model-b"
            )
            stats.add_embedding(embedding, processing_time=2.0)

        assert stats.total_embeddings == 8
        assert stats.model_counts["model-a"] == 5
        assert stats.model_counts["model-b"] == 3
        assert stats.dimension_counts[512] == 5
        assert stats.dimension_counts[768] == 3
        assert stats.total_processing_time == 11.0

    def test_get_average_processing_time_no_embeddings(self):
        """Test average processing time with no embeddings."""
        stats = EmbeddingStats()

        avg = stats.get_average_processing_time()

        assert avg == 0.0

    def test_get_average_processing_time(self):
        """Test average processing time calculation."""
        stats = EmbeddingStats()

        for i in range(4):
            vector = np.array([0.1] * 512, dtype=np.float32)
            embedding = Embedding(file_id=i, clip_vector=vector, embedding_model="test")
            stats.add_embedding(embedding, processing_time=2.0)

        avg = stats.get_average_processing_time()

        assert avg == 2.0

    def test_to_dict(self):
        """Test converting EmbeddingStats to dictionary."""
        stats = EmbeddingStats()

        vector = np.array([0.1] * 512, dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="test")
        stats.add_embedding(embedding, processing_time=1.5)

        result = stats.to_dict()

        assert result["total_embeddings"] == 1
        assert "model_counts" in result
        assert "dimension_counts" in result
        assert "total_processing_time" in result
        assert "average_processing_time" in result
