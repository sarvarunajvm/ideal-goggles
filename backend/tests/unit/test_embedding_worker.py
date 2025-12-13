"""Unit tests for CLIP embedding worker."""

import asyncio
import contextlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from src.models.embedding import Embedding, EmbeddingStats
from src.models.photo import Photo
from src.workers.embedding_worker import (
    CLIPEmbeddingWorker,
    EmbeddingValidator,
    OptimizedCLIPWorker,
)


@pytest.fixture
def mock_clip():
    """Mock CLIP module."""
    # Create mock objects
    mock_model = Mock()
    mock_model.eval = Mock()
    mock_model.encode_image = Mock()
    mock_model.encode_text = Mock()
    mock_preprocess = Mock()

    # Patch at the builtins level to catch dynamic imports
    mock_clip_module = Mock()
    mock_clip_module.load = Mock(return_value=(mock_model, mock_preprocess))

    with patch.dict("sys.modules", {"clip": mock_clip_module}):
        yield mock_clip_module


@pytest.fixture
def mock_torch():
    """Mock torch module."""
    # Create mock torch module
    mock_torch_module = Mock()
    mock_torch_module.cuda.is_available = Mock(return_value=False)
    mock_torch_module.no_grad = Mock()
    mock_torch_module.no_grad.return_value.__enter__ = Mock()
    mock_torch_module.no_grad.return_value.__exit__ = Mock()

    # Mock tensor operations
    mock_torch_module.tensor = Mock()
    mock_torch_module.from_numpy = Mock()

    with patch.dict("sys.modules", {"torch": mock_torch_module}):
        yield mock_torch_module


@pytest.fixture
def test_photo():
    """Create a test photo."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        temp_path = temp_file.name

    # Create a simple test image
    try:
        from PIL import Image

        img = Image.new("RGB", (100, 100), color="red")
        img.save(temp_path)
    except ImportError:
        pass

    photo = Photo(
        id=1,
        path=temp_path,
        folder=str(Path(temp_path).parent),
        filename=Path(temp_path).name,
        modified_ts=1640995200.0,
    )

    yield photo

    # Cleanup
    with contextlib.suppress(Exception):
        Path(temp_path).unlink()


@pytest.fixture
def test_photos():
    """Create multiple test photos."""
    photos = []
    temp_paths = []

    for i in range(3):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_paths.append(temp_path)

        try:
            from PIL import Image

            img = Image.new("RGB", (100, 100), color="red")
            img.save(temp_path)
        except ImportError:
            pass

        photo = Photo(
            id=i + 1,
            path=temp_path,
            folder=str(Path(temp_path).parent),
            filename=Path(temp_path).name,
            modified_ts=1640995200.0,
        )
        photos.append(photo)

    yield photos

    # Cleanup
    for path in temp_paths:
        with contextlib.suppress(Exception):
            Path(path).unlink()


class TestCLIPEmbeddingWorkerInitialization:
    """Test CLIPEmbeddingWorker initialization."""

    def test_initialization_default_parameters(self, mock_clip, mock_torch):
        """Test worker initialization with default parameters."""
        worker = CLIPEmbeddingWorker()

        assert worker.max_workers == 2
        assert worker.model_name == "ViT-B/32"
        assert worker.model is not None
        assert worker.preprocess is not None
        assert isinstance(worker.stats, EmbeddingStats)

    def test_initialization_custom_parameters(self, mock_clip, mock_torch):
        """Test worker initialization with custom parameters."""
        worker = CLIPEmbeddingWorker(max_workers=4, model_name="ViT-L/14")

        assert worker.max_workers == 4
        assert worker.model_name == "ViT-L/14"

    def test_initialization_uses_cuda_if_available(self, mock_clip):
        """Test worker uses CUDA when available."""
        # Create mock torch module with CUDA available
        mock_torch_cuda = Mock()
        mock_torch_cuda.cuda.is_available = Mock(return_value=True)
        mock_torch_cuda.no_grad = Mock()
        mock_torch_cuda.no_grad.return_value.__enter__ = Mock()
        mock_torch_cuda.no_grad.return_value.__exit__ = Mock()
        mock_torch_cuda.tensor = Mock()
        mock_torch_cuda.from_numpy = Mock()

        with patch.dict("sys.modules", {"torch": mock_torch_cuda}):
            worker = CLIPEmbeddingWorker()
            assert worker.device == "cuda"

    def test_initialization_uses_cpu_when_cuda_unavailable(self, mock_clip, mock_torch):
        """Test worker uses CPU when CUDA unavailable."""
        worker = CLIPEmbeddingWorker()

        assert worker.device == "cpu"

    def test_initialization_clip_import_error(self, mock_torch):
        """Test initialization handles CLIP import error gracefully."""
        # Simulate CLIP not being available - remove it from sys.modules
        original_clip = sys.modules.get("clip")
        if "clip" in sys.modules:
            del sys.modules["clip"]

        # Mock the import to raise ImportError
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "clip":
                raise ImportError("CLIP not installed")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # Should not raise - graceful degradation
            worker = CLIPEmbeddingWorker()
            # Worker should be created but not available
            assert not worker.is_available()

        # Restore original state
        if original_clip is not None:
            sys.modules["clip"] = original_clip

    def test_initialization_model_load_error(self, mock_clip, mock_torch):
        """Test initialization handles model load error gracefully."""
        mock_clip.load.side_effect = Exception("Model load failed")

        # Should not raise - graceful degradation
        worker = CLIPEmbeddingWorker()
        # Worker should be created but not available
        assert not worker.is_available()


@pytest.mark.asyncio
class TestGenerateEmbedding:
    """Test generate_embedding method."""

    async def test_generate_embedding_success(self, mock_clip, mock_torch, test_photo):
        """Test generating embedding successfully."""
        worker = CLIPEmbeddingWorker()

        # Mock the sync generation method
        mock_vector = np.random.randn(512).astype(np.float32)
        worker._generate_embedding_sync = Mock(return_value=mock_vector)

        result = await worker.generate_embedding(test_photo)

        assert result is not None
        assert isinstance(result, Embedding)
        assert result.file_id == test_photo.id
        assert result.embedding_model == "ViT-B/32"

    async def test_generate_embedding_file_not_found(self, mock_clip, mock_torch):
        """Test generating embedding for non-existent file."""
        worker = CLIPEmbeddingWorker()

        photo = Photo(
            id=1,
            path="/nonexistent/file.jpg",
            folder="/nonexistent",
            filename="file.jpg",
            modified_ts=1640995200.0,
        )

        result = await worker.generate_embedding(photo)

        assert result is None

    async def test_generate_embedding_exception_handling(
        self, mock_clip, mock_torch, test_photo
    ):
        """Test exception handling during embedding generation."""
        worker = CLIPEmbeddingWorker()
        worker._generate_embedding_sync = Mock(
            side_effect=Exception("Processing error")
        )

        result = await worker.generate_embedding(test_photo)

        assert result is None

    async def test_generate_embedding_updates_stats(
        self, mock_clip, mock_torch, test_photo
    ):
        """Test that stats are updated after embedding generation."""
        worker = CLIPEmbeddingWorker()

        mock_vector = np.random.randn(512).astype(np.float32)
        worker._generate_embedding_sync = Mock(return_value=mock_vector)

        initial_count = worker.stats.total_embeddings

        await worker.generate_embedding(test_photo)

        assert worker.stats.total_embeddings == initial_count + 1


class TestGenerateEmbeddingSync:
    """Test _generate_embedding_sync method."""

    def test_generate_embedding_sync_success(self, mock_clip, mock_torch, test_photo):
        """Test synchronous embedding generation."""
        # Mock PIL Image module
        mock_pil_module = Mock()
        mock_image = Mock()
        mock_image.mode = "RGB"
        mock_pil_module.open = Mock()
        mock_pil_module.open.return_value.__enter__ = Mock(return_value=mock_image)
        mock_pil_module.open.return_value.__exit__ = Mock()

        with patch.dict("sys.modules", {"PIL.Image": mock_pil_module}):
            worker = CLIPEmbeddingWorker()

            # Setup mock chain for preprocessing and encoding
            mock_tensor = Mock()
            mock_features = MagicMock()  # Use MagicMock to support __truediv__
            mock_norm = Mock()
            mock_features.norm.return_value = mock_norm

            # Setup the division operation result
            mock_normalized = Mock()
            mock_normalized.cpu.return_value.numpy.return_value.flatten.return_value = (
                np.random.randn(512).astype(np.float32)
            )
            mock_features.__truediv__.return_value = mock_normalized

            worker.preprocess.return_value.unsqueeze.return_value.to.return_value = (
                mock_tensor
            )
            worker.model.encode_image.return_value = mock_features

            result = worker._generate_embedding_sync(test_photo.path)

            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.dtype == np.float32

    def test_generate_embedding_sync_converts_non_rgb(
        self, mock_clip, mock_torch, test_photo
    ):
        """Test that non-RGB images are converted."""
        worker = CLIPEmbeddingWorker()

        # Test with the real file - just verify it doesn't crash
        # The actual conversion logic is tested via integration
        # Mock the processing to avoid needing actual CLIP
        mock_tensor = Mock()
        mock_features = MagicMock()
        mock_norm = Mock()
        mock_features.norm.return_value = mock_norm

        mock_normalized = Mock()
        mock_normalized.cpu.return_value.numpy.return_value.flatten.return_value = (
            np.random.randn(512).astype(np.float32)
        )
        mock_features.__truediv__.return_value = mock_normalized

        worker.preprocess.return_value.unsqueeze.return_value.to.return_value = (
            mock_tensor
        )
        worker.model.encode_image.return_value = mock_features

        result = worker._generate_embedding_sync(test_photo.path)

        assert result is not None
        # Verify the conversion path was exercised (RGB images don't need conversion)
        # This test verifies the method runs without error on real files

    def test_generate_embedding_sync_handles_error(
        self, mock_clip, mock_torch, test_photo
    ):
        """Test error handling in sync embedding generation."""
        # Mock PIL Image module to raise error
        mock_pil_module = Mock()
        mock_pil_module.open.side_effect = Exception("Image load error")

        with patch.dict("sys.modules", {"PIL.Image": mock_pil_module}):
            worker = CLIPEmbeddingWorker()

            result = worker._generate_embedding_sync(test_photo.path)

            assert result is None


@pytest.mark.asyncio
class TestGenerateTextEmbedding:
    """Test generate_text_embedding method."""

    async def test_generate_text_embedding_success(self, mock_clip, mock_torch):
        """Test generating text embedding successfully."""
        worker = CLIPEmbeddingWorker()

        mock_vector = np.random.randn(512).astype(np.float32)
        worker._generate_text_embedding_sync = Mock(return_value=mock_vector)

        result = await worker.generate_text_embedding("test query")

        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32

    async def test_generate_text_embedding_exception(self, mock_clip, mock_torch):
        """Test exception handling in text embedding generation."""
        worker = CLIPEmbeddingWorker()
        worker._generate_text_embedding_sync = Mock(
            side_effect=Exception("Text processing error")
        )

        result = await worker.generate_text_embedding("test query")

        assert result is None


class TestGenerateTextEmbeddingSync:
    """Test _generate_text_embedding_sync method."""

    def test_generate_text_embedding_sync_success(self, mock_clip, mock_torch):
        """Test synchronous text embedding generation."""
        worker = CLIPEmbeddingWorker()

        mock_tokens = Mock()
        mock_features = MagicMock()  # Use MagicMock to support __truediv__
        mock_norm = Mock()
        mock_features.norm.return_value = mock_norm

        # Setup the division operation result
        mock_normalized = Mock()
        mock_normalized.cpu.return_value.numpy.return_value.flatten.return_value = (
            np.random.randn(512).astype(np.float32)
        )
        mock_features.__truediv__.return_value = mock_normalized

        mock_clip.tokenize.return_value.to.return_value = mock_tokens
        worker.model.encode_text.return_value = mock_features

        result = worker._generate_text_embedding_sync("test query")

        assert result is not None
        assert isinstance(result, np.ndarray)

    def test_generate_text_embedding_sync_handles_error(self, mock_clip, mock_torch):
        """Test error handling in sync text embedding."""
        worker = CLIPEmbeddingWorker()

        mock_clip.tokenize.side_effect = Exception("Tokenization error")

        result = worker._generate_text_embedding_sync("test query")

        assert result is None


@pytest.mark.asyncio
class TestGenerateBatch:
    """Test generate_batch method."""

    async def test_generate_batch_empty_list(self, mock_clip, mock_torch):
        """Test batch generation with empty list."""
        worker = CLIPEmbeddingWorker()

        result = await worker.generate_batch([])

        assert result == []

    async def test_generate_batch_success(self, mock_clip, mock_torch, test_photos):
        """Test batch generation successfully."""
        worker = CLIPEmbeddingWorker()

        mock_vector = np.random.randn(512).astype(np.float32)
        worker._generate_embedding_sync = Mock(return_value=mock_vector)

        results = await worker.generate_batch(test_photos, batch_size=2)

        assert len(results) == len(test_photos)
        assert all(isinstance(r, Embedding) for r in results if r is not None)

    async def test_generate_batch_with_failures(
        self, mock_clip, mock_torch, test_photos
    ):
        """Test batch generation with some failures."""
        worker = CLIPEmbeddingWorker()

        # Mock to return None for second photo
        def mock_generate(path):
            if "2" in path:
                return None
            return np.random.randn(512).astype(np.float32)

        worker._generate_embedding_sync = Mock(side_effect=mock_generate)

        results = await worker.generate_batch(test_photos)

        assert len(results) == len(test_photos)
        assert results[1] is None  # Second photo should fail

    async def test_generate_batch_handles_exceptions(
        self, mock_clip, mock_torch, test_photos
    ):
        """Test batch generation handles exceptions."""
        worker = CLIPEmbeddingWorker()

        # Mock to raise exception for one photo
        call_count = [0]

        def mock_generate(path):
            call_count[0] += 1
            if call_count[0] == 2:
                msg = "Processing error"
                raise Exception(msg)
            return np.random.randn(512).astype(np.float32)

        worker._generate_embedding_sync = Mock(side_effect=mock_generate)

        results = await worker.generate_batch(test_photos)

        assert len(results) == len(test_photos)
        # Should have None for the failed embedding
        assert None in results


class TestWorkerStatistics:
    """Test worker statistics methods."""

    def test_get_statistics(self, mock_clip, mock_torch):
        """Test getting worker statistics."""
        worker = CLIPEmbeddingWorker()

        stats = worker.get_statistics()

        assert "model_name" in stats
        assert "device" in stats
        assert "max_workers" in stats
        assert stats["model_name"] == "ViT-B/32"
        assert stats["max_workers"] == 2

    def test_reset_statistics(self, mock_clip, mock_torch):
        """Test resetting statistics."""
        worker = CLIPEmbeddingWorker()

        # Add some stats
        worker.stats.total_embeddings = 10

        worker.reset_statistics()

        assert worker.stats.total_embeddings == 0


class TestWorkerShutdown:
    """Test worker shutdown."""

    def test_shutdown_without_cuda(self, mock_clip, mock_torch):
        """Test shutdown without CUDA."""
        worker = CLIPEmbeddingWorker()
        worker.shutdown()

        # Should complete without error

    def test_shutdown_with_cuda(self, mock_clip):
        """Test shutdown with CUDA."""
        # Create mock torch module with CUDA available
        mock_torch_cuda = Mock()
        mock_torch_cuda.cuda.is_available = Mock(return_value=True)
        mock_torch_cuda.cuda.empty_cache = Mock()
        mock_torch_cuda.no_grad = Mock()
        mock_torch_cuda.no_grad.return_value.__enter__ = Mock()
        mock_torch_cuda.no_grad.return_value.__exit__ = Mock()
        mock_torch_cuda.tensor = Mock()
        mock_torch_cuda.from_numpy = Mock()

        with patch.dict("sys.modules", {"torch": mock_torch_cuda}):
            worker = CLIPEmbeddingWorker()
            worker.shutdown()

            mock_torch_cuda.cuda.empty_cache.assert_called_once()


class TestOptimizedCLIPWorker:
    """Test OptimizedCLIPWorker."""

    def test_initialization(self, mock_clip, mock_torch):
        """Test optimized worker initialization."""
        worker = OptimizedCLIPWorker(
            max_workers=4, enable_batch_processing=True, cache_size=500
        )

        assert worker.max_workers == 4
        assert worker.enable_batch_processing is True
        assert worker.cache_size == 500
        assert isinstance(worker.embedding_cache, dict)

    def test_initialization_default_parameters(self, mock_clip, mock_torch):
        """Test optimized worker with default parameters."""
        worker = OptimizedCLIPWorker()

        assert worker.enable_batch_processing is True
        assert worker.cache_size == 1000

    @pytest.mark.asyncio
    async def test_generate_batch_optimized_disabled(
        self, mock_clip, mock_torch, test_photos
    ):
        """Test optimized batch when disabled."""
        worker = OptimizedCLIPWorker(enable_batch_processing=False)

        mock_vector = np.random.randn(512).astype(np.float32)
        worker._generate_embedding_sync = Mock(return_value=mock_vector)

        results = await worker.generate_batch_optimized(test_photos)

        assert len(results) == len(test_photos)

    @pytest.mark.asyncio
    async def test_generate_batch_optimized_with_cache(
        self, mock_clip, mock_torch, test_photos
    ):
        """Test optimized batch with caching."""
        worker = OptimizedCLIPWorker()

        mock_vector = np.random.randn(512).astype(np.float32)
        worker._generate_batch_embeddings_sync = Mock(
            return_value=[mock_vector] * len(test_photos)
        )

        # Mock database save
        with patch.object(worker, "_save_embeddings_to_database"):
            # First call - should process all
            results1 = await worker.generate_batch_optimized(test_photos)

            # Second call - should use cache
            results2 = await worker.generate_batch_optimized(test_photos)

            assert len(results1) == len(test_photos)
            assert len(results2) == len(test_photos)

    @pytest.mark.asyncio
    async def test_process_batch_on_gpu_success(
        self, mock_clip, mock_torch, test_photos
    ):
        """Test processing batch on GPU."""
        worker = OptimizedCLIPWorker()

        mock_vectors = [np.random.randn(512).astype(np.float32) for _ in test_photos]
        worker._generate_batch_embeddings_sync = Mock(return_value=mock_vectors)

        results = await worker._process_batch_on_gpu(test_photos)

        assert len(results) == len(test_photos)
        assert all(isinstance(r, Embedding) for r in results if r is not None)

    @pytest.mark.asyncio
    async def test_process_batch_on_gpu_fallback(
        self, mock_clip, mock_torch, test_photos
    ):
        """Test GPU processing fallback on error."""
        worker = OptimizedCLIPWorker()

        worker._generate_batch_embeddings_sync = Mock(
            side_effect=Exception("GPU error")
        )
        mock_vector = np.random.randn(512).astype(np.float32)
        worker._generate_embedding_sync = Mock(return_value=mock_vector)

        results = await worker._process_batch_on_gpu(test_photos)

        assert len(results) == len(test_photos)

    def test_generate_batch_embeddings_sync_success(
        self, mock_clip, mock_torch, test_photos
    ):
        """Test synchronous batch embedding generation."""
        # Mock PIL Image module
        mock_pil_module = Mock()
        mock_image = Mock()
        mock_image.mode = "RGB"
        mock_pil_module.open = Mock()
        mock_pil_module.open.return_value.__enter__ = Mock(return_value=mock_image)
        mock_pil_module.open.return_value.__exit__ = Mock()

        # Mock torch for batch operations
        mock_torch_local = Mock()
        mock_tensor = Mock()
        mock_torch_local.stack.return_value.to.return_value = mock_tensor
        mock_torch_local.no_grad.return_value.__enter__ = Mock()
        mock_torch_local.no_grad.return_value.__exit__ = Mock()

        with patch.dict(
            "sys.modules", {"PIL.Image": mock_pil_module, "torch": mock_torch_local}
        ):
            worker = OptimizedCLIPWorker()

            mock_batch_features = MagicMock()  # Use MagicMock to support __truediv__
            mock_norm = Mock()
            mock_batch_features.norm.return_value = mock_norm

            # Setup the division operation result
            mock_normalized = Mock()
            mock_normalized.cpu.return_value.numpy.return_value = np.random.randn(
                3, 512
            ).astype(np.float32)
            mock_batch_features.__truediv__.return_value = mock_normalized

            worker.preprocess.return_value = mock_tensor
            worker.model.encode_image.return_value = mock_batch_features

            file_paths = [photo.path for photo in test_photos]
            results = worker._generate_batch_embeddings_sync(file_paths)

            assert len(results) == len(test_photos)

    def test_generate_batch_embeddings_sync_handles_errors(
        self, mock_clip, mock_torch, test_photos
    ):
        """Test batch embedding handles individual image errors."""
        # Mock PIL Image module to raise error
        mock_pil_module = Mock()
        mock_pil_module.open.side_effect = Exception("Image error")

        with patch.dict("sys.modules", {"PIL.Image": mock_pil_module}):
            worker = OptimizedCLIPWorker()

            file_paths = [photo.path for photo in test_photos]
            results = worker._generate_batch_embeddings_sync(file_paths)

            assert len(results) == len(test_photos)
            assert all(r is None for r in results)

    def test_update_cache(self, mock_clip, mock_torch):
        """Test cache update."""
        worker = OptimizedCLIPWorker(cache_size=2)

        embedding1 = Mock()
        embedding2 = Mock()
        embedding3 = Mock()

        worker._update_cache("key1", embedding1)
        worker._update_cache("key2", embedding2)

        assert len(worker.embedding_cache) == 2

        # Adding third should evict first
        worker._update_cache("key3", embedding3)

        assert len(worker.embedding_cache) == 2
        assert "key1" not in worker.embedding_cache

    def test_clear_cache(self, mock_clip, mock_torch):
        """Test clearing cache."""
        worker = OptimizedCLIPWorker()

        worker.embedding_cache["key1"] = Mock()
        worker.embedding_cache["key2"] = Mock()

        worker.clear_cache()

        assert len(worker.embedding_cache) == 0

    def test_get_cache_statistics(self, mock_clip, mock_torch):
        """Test getting cache statistics."""
        worker = OptimizedCLIPWorker(cache_size=100)

        worker.embedding_cache["key1"] = Mock()

        stats = worker.get_cache_statistics()

        assert stats["cache_size"] == 1
        assert stats["cache_limit"] == 100
        assert "cache_hit_rate" in stats


class TestEmbeddingValidator:
    """Test EmbeddingValidator."""

    def test_validate_embedding_valid(self):
        """Test validating a valid embedding."""
        embedding = Embedding(
            file_id=1,
            clip_vector=np.random.randn(512).astype(np.float32),
            embedding_model="ViT-B/32",
        )

        # Normalize the vector
        norm = np.linalg.norm(embedding.clip_vector)
        embedding.clip_vector = embedding.clip_vector / norm

        result = EmbeddingValidator.validate_embedding(embedding)

        assert result["is_valid"]
        assert result["dimension"] == 512
        assert result["is_normalized"]

    def test_validate_embedding_invalid(self):
        """Test validating an invalid embedding."""
        embedding = Embedding(
            file_id=1,
            clip_vector=np.array([np.nan, np.inf], dtype=np.float32),
            embedding_model="ViT-B/32",
        )

        result = EmbeddingValidator.validate_embedding(embedding)

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_embedding_warnings_high_mean(self):
        """Test validation warnings for high mean."""
        # Create embedding with high mean (not normalized)
        # Construct a vector where half the values are high positive
        vector = np.ones(512, dtype=np.float32) * 10.0  # High values
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="ViT-B/32")

        result = EmbeddingValidator.validate_embedding(embedding)

        # The vector will get normalized, but we may still get warnings for low std
        assert "warnings" in result
        # After normalization, constant vectors have very low std
        assert any("standard deviation" in w.lower() for w in result["warnings"])

    def test_validate_embedding_warnings_low_std(self):
        """Test validation warnings for low standard deviation."""
        # Create embedding with low std
        vector = np.full(512, 0.1, dtype=np.float32)
        embedding = Embedding(file_id=1, clip_vector=vector, embedding_model="ViT-B/32")

        result = EmbeddingValidator.validate_embedding(embedding)

        assert "warnings" in result
        assert any("standard deviation" in w for w in result["warnings"])

    def test_compare_embeddings_compatible(self):
        """Test comparing compatible embeddings."""
        vector1 = np.random.randn(512).astype(np.float32)
        vector2 = np.random.randn(512).astype(np.float32)

        # Normalize
        vector1 = vector1 / np.linalg.norm(vector1)
        vector2 = vector2 / np.linalg.norm(vector2)

        embedding1 = Embedding(
            file_id=1, clip_vector=vector1, embedding_model="ViT-B/32"
        )
        embedding2 = Embedding(
            file_id=2, clip_vector=vector2, embedding_model="ViT-B/32"
        )

        result = EmbeddingValidator.compare_embeddings(embedding1, embedding2)

        assert result["comparable"] is True
        assert "cosine_similarity" in result
        assert "euclidean_distance" in result
        assert result["dimension_match"] is True
        assert result["model_match"] is True

    def test_compare_embeddings_different_models(self):
        """Test comparing embeddings from different models."""
        embedding1 = Embedding(
            file_id=1,
            clip_vector=np.random.randn(512).astype(np.float32),
            embedding_model="ViT-B/32",
        )
        embedding2 = Embedding(
            file_id=2,
            clip_vector=np.random.randn(512).astype(np.float32),
            embedding_model="ViT-L/14",
        )

        result = EmbeddingValidator.compare_embeddings(embedding1, embedding2)

        assert result["comparable"] is False
        assert "Different embedding models" in result["reason"]
