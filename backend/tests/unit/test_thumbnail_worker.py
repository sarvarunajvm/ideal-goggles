"""Comprehensive unit tests for thumbnail_worker module."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call

import pytest
from PIL import Image

from src.models.photo import Photo
from src.models.thumbnail import Thumbnail, ThumbnailCache
from src.workers.thumbnail_worker import (
    SmartThumbnailGenerator,
    ThumbnailCacheManager,
    ThumbnailGenerator,
)


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


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
def sample_thumbnail():
    """Create a sample thumbnail for testing."""
    return Thumbnail(
        file_id=1,
        thumb_path="01/00/1.webp",
        width=256,
        height=256,
        format="webp",
        generated_at=1640995200.0,
    )


class TestThumbnailGeneratorInitialization:
    """Test ThumbnailGenerator initialization."""

    def test_initialization_with_defaults(self, temp_cache_dir):
        """Test generator initialization with default parameters."""
        generator = ThumbnailGenerator(
            cache_root=temp_cache_dir,
        )

        assert generator.cache_root == Path(temp_cache_dir)
        assert generator.max_workers == 4
        assert generator.max_size == 512
        assert generator.format == "webp"
        assert generator.quality == 85
        assert generator.executor is not None
        assert generator.cache_root.exists()

    def test_initialization_with_custom_params(self, temp_cache_dir):
        """Test generator initialization with custom parameters."""
        generator = ThumbnailGenerator(
            cache_root=temp_cache_dir,
            max_workers=8,
            max_size=256,
            img_format="JPEG",
            quality=90,
        )

        assert generator.max_workers == 8
        assert generator.max_size == 256
        assert generator.format == "jpeg"  # Should be lowercased
        assert generator.quality == 90

    def test_initialization_creates_cache_directory(self, temp_cache_dir):
        """Test that initialization creates cache directory."""
        cache_path = Path(temp_cache_dir) / "thumbnails"
        assert not cache_path.exists()

        generator = ThumbnailGenerator(cache_root=str(cache_path))

        assert cache_path.exists()

    @patch("src.workers.thumbnail_worker.Image")
    def test_validate_pil_success(self, mock_image, temp_cache_dir):
        """Test PIL validation succeeds."""
        mock_img = Mock()
        mock_image.new.return_value = mock_img

        generator = ThumbnailGenerator(cache_root=temp_cache_dir, img_format="webp")

        # Should not raise
        assert generator.format == "webp"

    def test_validate_pil_not_available(self, temp_cache_dir):
        """Test PIL validation when PIL is not available."""
        # Mock PIL.Image module at the import level
        with patch.dict('sys.modules', {'PIL': None, 'PIL.Image': None}):
            with pytest.raises((RuntimeError, AttributeError, ImportError)):
                ThumbnailGenerator(cache_root=temp_cache_dir)

    def test_validate_pil_webp_fallback(self, temp_cache_dir):
        """Test fallback to JPEG when WebP is not supported."""
        # Mock PIL to simulate WebP save failure
        with patch("PIL.Image.new") as mock_new:
            mock_img = Mock()
            mock_img.save.side_effect = Exception("WebP not supported")
            mock_new.return_value = mock_img

            generator = ThumbnailGenerator(cache_root=temp_cache_dir, img_format="webp")

            # Should fallback to JPEG when WebP fails
            assert generator.format == "jpeg"


class TestThumbnailGeneration:
    """Test thumbnail generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_thumbnail_success(self, temp_cache_dir, sample_photo):
        """Test successful thumbnail generation."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        # Create a test image
        test_image = Image.new("RGB", (1000, 800), color="red")

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            thumbnail = await generator.generate_thumbnail(sample_photo)

            assert thumbnail is not None
            assert thumbnail.file_id == sample_photo.id
            assert thumbnail.width <= generator.max_size
            assert thumbnail.height <= generator.max_size
            assert generator.stats["generated"] == 1

    @pytest.mark.asyncio
    async def test_generate_thumbnail_with_existing_cache(self, temp_cache_dir, sample_photo):
        """Test thumbnail generation uses existing cache."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        # Create a test image and thumbnail
        test_image = Image.new("RGB", (1000, 800), color="red")
        existing_thumbnail = Thumbnail.create_for_photo(
            sample_photo.id, 512, 410, 512, "webp"
        )

        # Create the thumbnail file
        thumb_path = existing_thumbnail.get_absolute_path(temp_cache_dir)
        Path(thumb_path).parent.mkdir(parents=True, exist_ok=True)
        test_image.save(thumb_path, "WEBP")

        with patch.object(generator, "_check_existing_thumbnail", return_value=existing_thumbnail):
            thumbnail = await generator.generate_thumbnail(sample_photo)

            assert thumbnail is not None
            assert generator.stats["cache_hits"] == 1
            assert generator.stats["generated"] == 0

    @pytest.mark.asyncio
    async def test_generate_thumbnail_force_regenerate(self, temp_cache_dir, sample_photo):
        """Test thumbnail generation with force regenerate."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        test_image = Image.new("RGB", (1000, 800), color="red")
        existing_thumbnail = Thumbnail.create_for_photo(
            sample_photo.id, 512, 410, 512, "webp"
        )

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image), \
             patch.object(generator, "_check_existing_thumbnail", return_value=existing_thumbnail):
            thumbnail = await generator.generate_thumbnail(sample_photo, force_regenerate=True)

            assert thumbnail is not None
            assert generator.stats["generated"] == 1
            assert generator.stats["cache_hits"] == 0

    @pytest.mark.asyncio
    async def test_generate_thumbnail_with_error(self, temp_cache_dir, sample_photo):
        """Test thumbnail generation handles errors gracefully."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        with patch("PIL.Image.open", side_effect=Exception("Cannot open image")):
            thumbnail = await generator.generate_thumbnail(sample_photo)

            assert thumbnail is None
            assert generator.stats["failed"] == 1

    def test_generate_thumbnail_sync_rgb_image(self, temp_cache_dir, sample_photo):
        """Test synchronous thumbnail generation with RGB image."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        test_image = Image.new("RGB", (1000, 800), color="blue")

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            thumbnail = generator._generate_thumbnail_sync(sample_photo)

            assert thumbnail is not None
            assert thumbnail.width <= 512
            assert thumbnail.height <= 512

    def test_generate_thumbnail_sync_rgba_image(self, temp_cache_dir, sample_photo):
        """Test synchronous thumbnail generation with RGBA image."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        test_image = Image.new("RGBA", (1000, 800), color=(255, 0, 0, 128))

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose") as mock_transpose:
            # Need to handle the converted RGB image
            rgb_image = Image.new("RGB", (1000, 800), color="white")
            mock_transpose.return_value = rgb_image

            thumbnail = generator._generate_thumbnail_sync(sample_photo)

            assert thumbnail is not None

    def test_generate_thumbnail_sync_grayscale_image(self, temp_cache_dir, sample_photo):
        """Test synchronous thumbnail generation with grayscale image."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        test_image = Image.new("L", (1000, 800), color=128)

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            thumbnail = generator._generate_thumbnail_sync(sample_photo)

            assert thumbnail is not None

    def test_generate_thumbnail_sync_with_exception(self, temp_cache_dir, sample_photo):
        """Test synchronous thumbnail generation handles exceptions."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        with patch("PIL.Image.open", side_effect=Exception("Error")):
            thumbnail = generator._generate_thumbnail_sync(sample_photo)

            assert thumbnail is None


class TestThumbnailSizeCalculation:
    """Test thumbnail size calculation."""

    def test_calculate_thumbnail_size_landscape(self, temp_cache_dir):
        """Test thumbnail size calculation for landscape image."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        width, height = generator._calculate_thumbnail_size(1600, 900, 512)

        assert width == 512
        assert height == 288
        assert width / height == pytest.approx(1600 / 900, rel=0.01)

    def test_calculate_thumbnail_size_portrait(self, temp_cache_dir):
        """Test thumbnail size calculation for portrait image."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        width, height = generator._calculate_thumbnail_size(900, 1600, 512)

        assert height == 512
        assert width == 288
        assert width / height == pytest.approx(900 / 1600, rel=0.01)

    def test_calculate_thumbnail_size_square(self, temp_cache_dir):
        """Test thumbnail size calculation for square image."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        width, height = generator._calculate_thumbnail_size(1000, 1000, 512)

        assert width == 512
        assert height == 512

    def test_calculate_thumbnail_size_small_image(self, temp_cache_dir):
        """Test thumbnail size calculation for image smaller than max_size."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        width, height = generator._calculate_thumbnail_size(300, 200, 512)

        # Should not upscale
        assert width == 300
        assert height == 200

    def test_calculate_thumbnail_size_invalid_dimensions(self, temp_cache_dir):
        """Test thumbnail size calculation with invalid dimensions."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        width, height = generator._calculate_thumbnail_size(0, 0, 512)

        assert width == 512
        assert height == 512

    def test_calculate_thumbnail_size_minimum_size(self, temp_cache_dir):
        """Test thumbnail size calculation enforces minimum size."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        width, height = generator._calculate_thumbnail_size(1, 1000, 512)

        assert width >= 1
        assert height >= 1


class TestSaveParameters:
    """Test save parameter generation."""

    def test_get_save_kwargs_webp(self, temp_cache_dir):
        """Test save parameters for WebP format."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, img_format="webp", quality=85)

        kwargs = generator._get_save_kwargs()

        assert kwargs["quality"] == 85
        assert kwargs["method"] == 6
        assert kwargs["optimize"] is True

    def test_get_save_kwargs_jpeg(self, temp_cache_dir):
        """Test save parameters for JPEG format."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, img_format="jpeg", quality=90)

        kwargs = generator._get_save_kwargs()

        assert kwargs["quality"] == 90
        assert kwargs["optimize"] is True
        assert kwargs["progressive"] is True

    def test_get_save_kwargs_png(self, temp_cache_dir):
        """Test save parameters for PNG format."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, img_format="png")

        kwargs = generator._get_save_kwargs()

        assert kwargs["optimize"] is True

    def test_get_save_kwargs_unknown_format(self, temp_cache_dir):
        """Test save parameters for unknown format."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, img_format="bmp")

        kwargs = generator._get_save_kwargs()

        assert kwargs == {}


class TestBatchProcessing:
    """Test batch thumbnail generation."""

    @pytest.mark.asyncio
    async def test_generate_batch_success(self, temp_cache_dir):
        """Test successful batch thumbnail generation."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        photos = [
            Photo(id=i, path=f"/test/photo{i}.jpg", folder="/test", filename=f"photo{i}.jpg",
                  ext=".jpg", size=1024, created_ts=1.0, modified_ts=1.0, sha1=f"hash{i}")
            for i in range(5)
        ]

        test_image = Image.new("RGB", (1000, 800), color="green")

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            results = await generator.generate_batch(photos)

            assert len(results) == 5
            successful = [r for r in results if r is not None]
            assert len(successful) == 5
            assert generator.stats["generated"] == 5

    @pytest.mark.asyncio
    async def test_generate_batch_empty(self, temp_cache_dir):
        """Test batch generation with empty input."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        results = await generator.generate_batch([])

        assert results == []

    @pytest.mark.asyncio
    async def test_generate_batch_with_failures(self, temp_cache_dir):
        """Test batch generation with some failures."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        photos = [
            Photo(id=i, path=f"/test/photo{i}.jpg", folder="/test", filename=f"photo{i}.jpg",
                  ext=".jpg", size=1024, created_ts=1.0, modified_ts=1.0, sha1=f"hash{i}")
            for i in range(3)
        ]

        test_image = Image.new("RGB", (1000, 800), color="yellow")

        call_count = [0]

        def mock_open(path):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Error opening image")
            return test_image

        with patch("PIL.Image.open", side_effect=mock_open), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            results = await generator.generate_batch(photos)

            assert len(results) == 3
            successful = [r for r in results if r is not None]
            assert len(successful) == 2
            assert generator.stats["failed"] >= 1


class TestStatistics:
    """Test statistics functionality."""

    def test_get_statistics(self, temp_cache_dir):
        """Test getting generator statistics."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=256, quality=80)

        generator.stats["generated"] = 100
        generator.stats["failed"] = 5
        generator.stats["skipped"] = 2
        generator.stats["cache_hits"] = 50
        generator.stats["total_time"] = 25.0

        stats = generator.get_statistics()

        assert stats["generated"] == 100
        assert stats["failed"] == 5
        assert stats["skipped"] == 2
        assert stats["cache_hits"] == 50
        assert stats["total_processed"] == 105
        assert stats["success_rate"] == pytest.approx(100 / 105, rel=0.01)
        assert stats["average_generation_time"] == 0.25
        assert stats["format"] == "webp"
        assert stats["max_size"] == 256
        assert stats["quality"] == 80

    def test_reset_statistics(self, temp_cache_dir):
        """Test resetting generator statistics."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        generator.stats["generated"] = 100
        generator.stats["failed"] = 5

        generator.reset_statistics()

        assert generator.stats["generated"] == 0
        assert generator.stats["failed"] == 0
        assert generator.stats["skipped"] == 0
        assert generator.stats["cache_hits"] == 0

    def test_shutdown(self, temp_cache_dir):
        """Test generator shutdown."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)
        mock_executor = Mock()
        generator.executor = mock_executor

        generator.shutdown()

        mock_executor.shutdown.assert_called_once_with(wait=True)


class TestCheckExistingThumbnail:
    """Test checking for existing thumbnails."""

    @pytest.mark.asyncio
    async def test_check_existing_thumbnail_exists(self, temp_cache_dir, sample_photo):
        """Test checking for existing thumbnail that exists."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        # Create thumbnail file
        thumbnail = Thumbnail.create_for_photo(sample_photo.id, 512, 410, 512, "webp")
        thumb_path = thumbnail.get_absolute_path(temp_cache_dir)
        Path(thumb_path).parent.mkdir(parents=True, exist_ok=True)

        test_image = Image.new("RGB", (512, 410), color="cyan")
        test_image.save(thumb_path, "WEBP")

        existing = await generator._check_existing_thumbnail(sample_photo)

        assert existing is not None

    @pytest.mark.asyncio
    async def test_check_existing_thumbnail_not_exists(self, temp_cache_dir, sample_photo):
        """Test checking for existing thumbnail that doesn't exist."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        existing = await generator._check_existing_thumbnail(sample_photo)

        assert existing is None


class TestSmartThumbnailGenerator:
    """Test SmartThumbnailGenerator functionality."""

    def test_smart_generator_initialization(self, temp_cache_dir):
        """Test smart generator initialization."""
        generator = SmartThumbnailGenerator(
            cache_root=temp_cache_dir,
            sizes=[128, 256, 512],
            adaptive_quality=True,
        )

        assert generator.sizes == [128, 256, 512]
        assert generator.adaptive_quality is True
        assert generator.max_size == 512

    def test_smart_generator_default_sizes(self, temp_cache_dir):
        """Test smart generator uses default sizes."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)

        assert generator.sizes == [128, 256, 512]

    @pytest.mark.asyncio
    async def test_generate_multi_size_thumbnails(self, temp_cache_dir, sample_photo):
        """Test generating multiple sizes of thumbnails."""
        generator = SmartThumbnailGenerator(
            cache_root=temp_cache_dir,
            sizes=[128, 256],
        )

        test_image = Image.new("RGB", (1000, 800), color="magenta")

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            thumbnails = await generator.generate_multi_size_thumbnails(sample_photo)

            assert len(thumbnails) == 2
            # Sizes should be different
            assert thumbnails[0] is not None
            assert thumbnails[1] is not None

    def test_calculate_adaptive_quality_small_image(self, temp_cache_dir, sample_photo):
        """Test adaptive quality for small images."""
        generator = SmartThumbnailGenerator(
            cache_root=temp_cache_dir,
            adaptive_quality=True,
        )
        generator.quality = 85

        small_image = Image.new("RGB", (500, 400), color="orange")

        quality = generator._calculate_adaptive_quality(small_image, sample_photo)

        # Should increase quality for small images
        assert quality == 95

    def test_calculate_adaptive_quality_large_image(self, temp_cache_dir, sample_photo):
        """Test adaptive quality for large images."""
        generator = SmartThumbnailGenerator(
            cache_root=temp_cache_dir,
            adaptive_quality=True,
        )
        generator.quality = 85

        large_image = Image.new("RGB", (5000, 4000), color="purple")

        quality = generator._calculate_adaptive_quality(large_image, sample_photo)

        # Should decrease quality for large images
        assert quality == 75

    def test_calculate_adaptive_quality_disabled(self, temp_cache_dir, sample_photo):
        """Test adaptive quality when disabled."""
        generator = SmartThumbnailGenerator(
            cache_root=temp_cache_dir,
            adaptive_quality=False,
        )
        generator.quality = 85

        image = Image.new("RGB", (1000, 800), color="brown")

        quality = generator._calculate_adaptive_quality(image, sample_photo)

        # Should return base quality
        assert quality == 85

    def test_calculate_adaptive_quality_by_file_size(self, temp_cache_dir):
        """Test adaptive quality based on file size."""
        generator = SmartThumbnailGenerator(
            cache_root=temp_cache_dir,
            adaptive_quality=True,
        )
        generator.quality = 85

        # Small file
        small_photo = Photo(
            id=1, path="/test/small.jpg", folder="/test", filename="small.jpg",
            ext=".jpg", size=500000, created_ts=1.0, modified_ts=1.0, sha1="hash1"
        )

        medium_image = Image.new("RGB", (1000, 800), color="gray")
        quality = generator._calculate_adaptive_quality(medium_image, small_photo)

        # Should increase quality for small files
        assert quality == 90

    def test_enhance_image_for_thumbnail(self, temp_cache_dir):
        """Test image enhancement for thumbnails."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)

        test_image = Image.new("RGB", (1000, 800), color="pink")

        enhanced = generator._enhance_image_for_thumbnail(test_image)

        assert enhanced is not None
        assert enhanced.size == test_image.size

    @patch("PIL.ImageEnhance.Contrast", side_effect=Exception("Enhancement error"))
    def test_enhance_image_with_error(self, mock_enhance, temp_cache_dir):
        """Test image enhancement handles errors gracefully."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)

        test_image = Image.new("RGB", (1000, 800), color="teal")

        enhanced = generator._enhance_image_for_thumbnail(test_image)

        # Should return original image on error
        assert enhanced is test_image

    def test_get_adaptive_save_kwargs_webp_high_quality(self, temp_cache_dir):
        """Test adaptive save kwargs for WebP with high quality."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)
        generator.format = "webp"

        kwargs = generator._get_adaptive_save_kwargs(quality=90)

        assert kwargs["quality"] == 90
        assert kwargs["method"] == 6
        assert kwargs["optimize"] is True

    def test_get_adaptive_save_kwargs_webp_low_quality(self, temp_cache_dir):
        """Test adaptive save kwargs for WebP with low quality."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)
        generator.format = "webp"

        kwargs = generator._get_adaptive_save_kwargs(quality=70)

        assert kwargs["quality"] == 70
        assert kwargs["method"] == 4
        assert kwargs["optimize"] is True

    def test_get_adaptive_save_kwargs_jpeg_high_quality(self, temp_cache_dir):
        """Test adaptive save kwargs for JPEG with high quality."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)
        generator.format = "jpeg"

        kwargs = generator._get_adaptive_save_kwargs(quality=90)

        assert kwargs["quality"] == 90
        assert kwargs["optimize"] is True
        assert kwargs["progressive"] is True

    def test_get_adaptive_save_kwargs_jpeg_low_quality(self, temp_cache_dir):
        """Test adaptive save kwargs for JPEG with low quality."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)
        generator.format = "jpeg"

        kwargs = generator._get_adaptive_save_kwargs(quality=70)

        assert kwargs["quality"] == 70
        assert kwargs["progressive"] is False


class TestThumbnailCacheManager:
    """Test ThumbnailCacheManager functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_orphaned_thumbnails(self, temp_cache_dir):
        """Test cleaning up orphaned thumbnails."""
        manager = ThumbnailCacheManager(cache_root=temp_cache_dir)

        # Create some test thumbnail files
        cache_path = Path(temp_cache_dir)
        (cache_path / "01" / "00").mkdir(parents=True, exist_ok=True)
        (cache_path / "02" / "00").mkdir(parents=True, exist_ok=True)

        # Create thumbnail files
        (cache_path / "01" / "00" / "1.webp").touch()
        (cache_path / "02" / "00" / "2.webp").touch()

        # Only file_id 1 is valid
        valid_ids = [1]

        removed_count = await manager.cleanup_orphaned_thumbnails(valid_ids)

        # Should remove file_id 2
        assert removed_count == 1
        assert (cache_path / "01" / "00" / "1.webp").exists()
        assert not (cache_path / "02" / "00" / "2.webp").exists()

    @pytest.mark.asyncio
    async def test_cleanup_empty_directories(self, temp_cache_dir):
        """Test cleaning up empty directories."""
        manager = ThumbnailCacheManager(cache_root=temp_cache_dir)

        # Create empty directory structure
        cache_path = Path(temp_cache_dir)
        (cache_path / "01" / "00").mkdir(parents=True, exist_ok=True)
        (cache_path / "02" / "00").mkdir(parents=True, exist_ok=True)

        removed_count = await manager.cleanup_empty_directories()

        # Should remove empty directories
        assert removed_count >= 2

    @pytest.mark.asyncio
    async def test_get_cache_statistics(self, temp_cache_dir):
        """Test getting cache statistics."""
        manager = ThumbnailCacheManager(cache_root=temp_cache_dir)

        # Create some test files
        cache_path = Path(temp_cache_dir)
        (cache_path / "01" / "00").mkdir(parents=True, exist_ok=True)
        (cache_path / "01" / "00" / "1.webp").write_bytes(b"test data")

        stats = await manager.get_cache_statistics()

        assert stats["exists"] is True
        assert stats["total_files"] >= 1
        assert stats["total_size_bytes"] > 0

    @pytest.mark.asyncio
    async def test_get_cache_statistics_empty(self):
        """Test getting cache statistics for empty cache."""
        # Create a new temporary directory for this test
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = str(Path(temp_dir) / "empty_cache")
            manager = ThumbnailCacheManager(cache_root=cache_dir)

            stats = await manager.get_cache_statistics()

            # Cache exists but should be empty
            assert stats["exists"] is True
            assert stats["total_files"] == 0

    @pytest.mark.asyncio
    async def test_validate_cache_integrity(self, temp_cache_dir):
        """Test validating cache integrity."""
        manager = ThumbnailCacheManager(cache_root=temp_cache_dir)

        result = await manager.validate_cache_integrity(sample_size=10)

        assert "valid_files" in result
        assert "invalid_files" in result
        assert "missing_files" in result
        assert "total_checked" in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_generate_thumbnail_concurrent_requests(self, temp_cache_dir, sample_photo):
        """Test handling concurrent thumbnail generation requests."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        test_image = Image.new("RGB", (1000, 800), color="white")

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            # Generate same thumbnail concurrently
            tasks = [generator.generate_thumbnail(sample_photo) for _ in range(5)]
            results = await asyncio.gather(*tasks)

            # All should succeed
            assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_generate_thumbnail_very_small_image(self, temp_cache_dir, sample_photo):
        """Test thumbnail generation for very small images."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        # Very small image
        test_image = Image.new("RGB", (50, 50), color="red")

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            thumbnail = await generator.generate_thumbnail(sample_photo)

            assert thumbnail is not None
            # Should not upscale
            assert thumbnail.width == 50
            assert thumbnail.height == 50

    @pytest.mark.asyncio
    async def test_generate_thumbnail_very_wide_image(self, temp_cache_dir, sample_photo):
        """Test thumbnail generation for very wide panoramic images."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        # Very wide panoramic image
        test_image = Image.new("RGB", (5000, 500), color="blue")

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            thumbnail = await generator.generate_thumbnail(sample_photo)

            assert thumbnail is not None
            assert thumbnail.width <= 512
            # Aspect ratio should be preserved
            assert thumbnail.width / thumbnail.height == pytest.approx(10.0, rel=0.1)

    @pytest.mark.asyncio
    async def test_generate_thumbnail_very_tall_image(self, temp_cache_dir, sample_photo):
        """Test thumbnail generation for very tall images."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        # Very tall image
        test_image = Image.new("RGB", (500, 5000), color="green")

        with patch("PIL.Image.open", return_value=test_image), \
             patch("PIL.ImageOps.exif_transpose", return_value=test_image):
            thumbnail = await generator.generate_thumbnail(sample_photo)

            assert thumbnail is not None
            assert thumbnail.height <= 512
            # Aspect ratio should be preserved
            assert thumbnail.height / thumbnail.width == pytest.approx(10.0, rel=0.1)

    def test_calculate_thumbnail_size_extreme_aspect_ratio(self, temp_cache_dir):
        """Test thumbnail size calculation with extreme aspect ratios."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir, max_size=512)

        # Very wide
        width, height = generator._calculate_thumbnail_size(10000, 100, 512)
        assert width == 512
        assert height >= 1

        # Very tall
        width, height = generator._calculate_thumbnail_size(100, 10000, 512)
        assert height == 512
        assert width >= 1
