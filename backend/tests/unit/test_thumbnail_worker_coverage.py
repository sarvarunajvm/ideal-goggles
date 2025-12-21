"""Additional coverage tests for thumbnail_worker module."""

import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from PIL import Image

from src.models.photo import Photo
from src.models.thumbnail import Thumbnail
from src.workers.thumbnail_worker import (
    SmartThumbnailGenerator,
    ThumbnailCacheManager,
    ThumbnailGenerator,
)


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_photo():
    """Create a sample photo."""
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


class TestThumbnailCacheManagerCoverage:
    """Tests for ThumbnailCacheManager validation logic."""

    @pytest.mark.asyncio
    async def test_validate_thumbnails_for_photos_coverage(self, temp_cache_dir):
        """Test validation of thumbnails with real files."""
        manager = ThumbnailCacheManager(cache_root=temp_cache_dir)
        db_manager = MagicMock()

        # Setup test scenarios
        # 1. Valid thumbnail
        # 2. Missing file
        # 3. Invalid file (corrupt)
        # 4. Invalid dimensions (0x0) - hard to create with PIL, but can simulate empty file or text file
        # 5. No DB record

        photo_ids = [1, 2, 3, 4, 5]

        # Setup DB responses
        # file_id -> thumb_path
        db_data = {
            1: "01/00/1.webp",  # Valid
            2: "02/00/2.webp",  # Missing file
            3: "03/00/3.webp",  # Corrupt
            4: "04/00/4.webp",  # Text file (header invalid)
        }
        # 5 is missing from DB

        def execute_query(query, params):
            return [(pid, db_data[pid]) for pid in params if pid in db_data]

        db_manager.execute_query.side_effect = execute_query

        # Create files
        cache_path = Path(temp_cache_dir)

        # 1. Valid
        p1 = cache_path / "01/00/1.webp"
        p1.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (100, 100), "red").save(p1, "WEBP")

        # 2. Missing - do nothing

        # 3. Corrupt (0 bytes or random garbage)
        p3 = cache_path / "03/00/3.webp"
        p3.parent.mkdir(parents=True, exist_ok=True)
        p3.write_bytes(b"garbage data")

        # 4. Text file (PIL verify might fail or size check fails)
        p4 = cache_path / "04/00/4.webp"
        p4.parent.mkdir(parents=True, exist_ok=True)
        p4.write_text("not an image")

        # Run validation
        result = await manager.validate_thumbnails_for_photos(photo_ids, db_manager)

        assert result["photos_checked"] == 5
        assert result["thumbnails_exist"] == 1  # Only photo 1
        assert result["thumbnails_missing"] == 2  # Photo 2 (file missing) + Photo 5 (DB missing)
        assert result["thumbnails_invalid"] == 2  # Photo 3 & 4
        assert 2 in result["missing_photo_ids"]
        assert 3 in result["missing_photo_ids"] # Invalid counts as missing in the returned list?
        assert 4 in result["missing_photo_ids"]
        assert 5 in result["missing_photo_ids"]

    @pytest.mark.asyncio
    async def test_validate_thumbnails_empty_list(self, temp_cache_dir):
        """Test validation with empty list."""
        manager = ThumbnailCacheManager(cache_root=temp_cache_dir)
        db_manager = MagicMock()
        result = await manager.validate_thumbnails_for_photos([], db_manager)
        assert result["photos_checked"] == 0
        assert result["thumbnails_exist"] == 0

    @pytest.mark.asyncio
    async def test_validate_cache_integrity_coverage(self, temp_cache_dir):
        """Test cache integrity validation."""
        manager = ThumbnailCacheManager(cache_root=temp_cache_dir)

        cache_path = Path(temp_cache_dir)

        # 1. Valid file
        p1 = cache_path / "valid.webp"
        Image.new("RGB", (50, 50), "blue").save(p1, "WEBP")

        # 2. Invalid file
        p2 = cache_path / "invalid.jpg"
        p2.write_bytes(b"not an image")

        # 3. Non-thumbnail file (should be ignored by suffix check? code uses .webp, .jpeg, .jpg, .png)
        p3 = cache_path / "other.txt"
        p3.write_text("info")

        # 4. Valid JPEG
        p4 = cache_path / "valid.jpeg"
        Image.new("RGB", (50, 50), "green").save(p4, "JPEG")

        # Check stats first to populate total_files
        await manager.get_cache_statistics()

        # Validate with sample size covering all
        result = await manager.validate_cache_integrity(sample_size=100)

        # Expected: 2 valid (webp, jpeg), 1 invalid (jpg garbage)
        # txt file ignored
        assert result["valid_files"] == 2
        assert result["invalid_files"] == 1
        assert result["total_checked"] == 3

    @pytest.mark.asyncio
    async def test_validate_cache_integrity_empty_sample(self, temp_cache_dir):
        """Test with sample size 0."""
        manager = ThumbnailCacheManager(cache_root=temp_cache_dir)
        p1 = Path(temp_cache_dir) / "valid.webp"
        Image.new("RGB", (10, 10)).save(p1, "WEBP")

        # Force sample size 0
        result = await manager.validate_cache_integrity(sample_size=0)
        assert result["total_checked"] == 0


class TestThumbnailGeneratorCoverage:
    """Additional coverage for ThumbnailGenerator."""

    def test_validate_pil_webp_fallback_warning(self, temp_cache_dir):
        """Test that warning is logged when WebP fails and fallback happens."""
        with patch("src.workers.thumbnail_worker.logger") as mock_logger:
            with patch("PIL.Image.new") as mock_new:
                mock_img = Mock()
                # Fail save
                mock_img.save.side_effect = Exception("WebP fail")
                mock_new.return_value = mock_img

                generator = ThumbnailGenerator(cache_root=temp_cache_dir, img_format="webp")

                assert generator.format == "jpeg"
                # Verify warning logged (line 73)
                args, _ = mock_logger.warning.call_args
                assert "WebP support issue" in args[0]

    def test_validate_pil_generic_error(self, temp_cache_dir):
        """Test generic error during PIL validation (line 76-77)."""
        # We need to trigger an exception during _validate_pil while format is NOT webp
        # _validate_pil calls logger.info at the end of try block
        with patch("src.workers.thumbnail_worker.logger.info", side_effect=Exception("Generic PIL Error")):
            with pytest.raises(RuntimeError, match="PIL format support issue"):
                ThumbnailGenerator(cache_root=temp_cache_dir, img_format="jpeg")

    @pytest.mark.asyncio
    async def test_generate_batch_logging(self, temp_cache_dir):
        """Test logging in batch generation for > 100 items (line 262)."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        # Mock generate_thumbnail to be fast
        generator.generate_thumbnail = AsyncMock(return_value=None)

        photos = [Mock(spec=Photo) for _ in range(150)]

        with patch("src.workers.thumbnail_worker.logger") as mock_logger:
            await generator.generate_batch(photos)

            # Check for progress log
            # logger.info(f"Thumbnail generation progress: {i + 1}/{len(photos)}")
            found_progress = False
            for call_args in mock_logger.info.call_args_list:
                msg = call_args[0][0]
                if "Thumbnail generation progress" in msg:
                    found_progress = True
                    break
            assert found_progress

    def test_generate_thumbnail_sync_la_mode(self, temp_cache_dir, sample_photo):
        """Test generation with LA mode (Luma with Alpha)."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)

        # Create LA image
        img = Image.new("LA", (100, 100), (128, 255))

        with patch("PIL.Image.open", return_value=img):
            with patch("PIL.ImageOps.exif_transpose", return_value=img):
                thumbnail = generator._generate_thumbnail_sync(sample_photo)
                assert thumbnail is not None
                # Check that background paste happened (coverage for line 148)

    def test_base_generator_heif_support(self, temp_cache_dir, sample_photo):
        """Test base ThumbnailGenerator HEIF support."""
        generator = ThumbnailGenerator(cache_root=temp_cache_dir)
        sample_photo.path = "test.heic"

        # 1. Success case
        mock_heif = MagicMock()
        with patch.dict(sys.modules, {"pillow_heif": mock_heif}):
            with patch("PIL.Image.open") as mock_open:
                mock_img = MagicMock()
                mock_img.size = (100, 100)
                mock_img.mode = "RGB"
                mock_open.return_value.__enter__.return_value = mock_img

                with patch("PIL.ImageOps.exif_transpose", return_value=mock_img):
                    thumbnail = generator._generate_thumbnail_sync(sample_photo)
                    assert thumbnail is not None
                    mock_heif.register_heif_opener.assert_called()

        # 2. Import Error case
        import builtins
        original_import = builtins.__import__
        def side_effect(name, *args, **kwargs):
            if name == "pillow_heif":
                raise ImportError("No HEIF")
            return original_import(name, *args, **kwargs)

        with patch.dict(sys.modules):
            if "pillow_heif" in sys.modules:
                del sys.modules["pillow_heif"]

            with patch("builtins.__import__", side_effect=side_effect):
                with patch("src.workers.thumbnail_worker.logger") as mock_logger:
                    # Mock Image.open to ensure no side effects
                    with patch("PIL.Image.open"):
                        thumbnail = generator._generate_thumbnail_sync(sample_photo)
                    assert thumbnail is None
                    assert "pillow-heif not available" in mock_logger.warning.call_args[0][0]



class TestSmartThumbnailGeneratorCoverage:
    """Additional coverage for SmartThumbnailGenerator."""

    def test_heif_support_success(self, temp_cache_dir, sample_photo):
        """Test HEIF support path when module is available."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)
        sample_photo.path = "test.heic"

        # Mock pillow_heif being available
        mock_heif = MagicMock()

        # We need to ensure import pillow_heif works
        with patch.dict(sys.modules, {"pillow_heif": mock_heif}):
            with patch("PIL.Image.open") as mock_open:
                mock_img = MagicMock()
                mock_img.size = (100, 100)
                mock_img.mode = "RGB"
                mock_open.return_value.__enter__.return_value = mock_img

                with patch("PIL.ImageOps.exif_transpose", return_value=mock_img):
                    thumbnail = generator._generate_thumbnail_sync(sample_photo)

                    # Verify register_heif_opener called
                    mock_heif.register_heif_opener.assert_called()
                    assert thumbnail is not None

    def test_heif_support_import_error(self, temp_cache_dir, sample_photo):
        """Test HEIF support path when module is missing."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)
        sample_photo.path = "test.heic"

        # Create a side effect for __import__
        import builtins
        original_import = builtins.__import__

        def import_side_effect(name, *args, **kwargs):
            if name == "pillow_heif":
                raise ImportError("No HEIF")
            return original_import(name, *args, **kwargs)

        # We must ensure pillow_heif is not in sys.modules, otherwise import is skipped
        with patch.dict(sys.modules):
            if "pillow_heif" in sys.modules:
                del sys.modules["pillow_heif"]

            with patch("builtins.__import__", side_effect=import_side_effect):
                with patch("src.workers.thumbnail_worker.logger") as mock_logger:
                    # Also mock Image.open to ensure we don't fail later if import somehow succeeds
                    with patch("PIL.Image.open"):
                        thumbnail = generator._generate_thumbnail_sync(sample_photo)

                    assert thumbnail is None
                    mock_logger.warning.assert_called()
                    assert "pillow-heif not available" in mock_logger.warning.call_args[0][0]

    def test_smart_generator_adaptive_quality_fallthrough(self, temp_cache_dir):
        """Test fallback to super()._get_save_kwargs for non-webp/jpeg."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)
        generator.format = "png"

        kwargs = generator._get_adaptive_save_kwargs(quality=80)
        assert "optimize" in kwargs # PNG uses optimize from super()

    def test_smart_generator_la_mode(self, temp_cache_dir, sample_photo):
        """Test SmartThumbnailGenerator with LA mode."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)

        img = Image.new("LA", (100, 100), (128, 255))

        with patch("PIL.Image.open", return_value=img):
            with patch("PIL.ImageOps.exif_transpose", return_value=img):
                 # Mock _enhance... to avoid complications
                with patch.object(generator, "_enhance_image_for_thumbnail", side_effect=lambda x: x):
                    thumbnail = generator._generate_thumbnail_sync(sample_photo)
                    assert thumbnail is not None

    def test_smart_generator_generic_exception(self, temp_cache_dir, sample_photo):
        """Test SmartThumbnailGenerator generic exception (lines 410-412)."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)

        # Raise exception during Image.open
        with patch("PIL.Image.open", side_effect=Exception("Smart Gen Error")):
            with patch("src.workers.thumbnail_worker.logger") as mock_logger:
                thumbnail = generator._generate_thumbnail_sync(sample_photo)
                assert thumbnail is None
                # Verify debug log
                args, _ = mock_logger.debug.call_args
                assert "Smart thumbnail generation failed" in args[0]
                assert "Smart Gen Error" in args[0]

    def test_smart_generator_adaptive_quality_exception(self, temp_cache_dir, sample_photo):
        """Test adaptive quality calculation handles exceptions (lines 437-440)."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)
        img = Mock()
        img.size = (1000, 1000)

        # Mock photo.size to raise exception
        sample_photo.size = "invalid" # This will cause TypeError during division

        quality = generator._calculate_adaptive_quality(img, sample_photo)
        assert quality == generator.quality

    def test_smart_generator_convert_rgb(self, temp_cache_dir, sample_photo):
        """Test conversion to RGB for non-RGB/RGBA/LA modes (line 380)."""
        generator = SmartThumbnailGenerator(cache_root=temp_cache_dir)

        # Create CMYK image
        img = Image.new("CMYK", (100, 100), (0, 0, 0, 0))

        with patch("PIL.Image.open", return_value=img):
            with patch("PIL.ImageOps.exif_transpose", return_value=img):
                 with patch.object(generator, "_enhance_image_for_thumbnail", side_effect=lambda x: x):
                    thumbnail = generator._generate_thumbnail_sync(sample_photo)
                    assert thumbnail is not None

