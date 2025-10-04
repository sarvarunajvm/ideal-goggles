"""Unit tests for Thumbnail models."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.models.thumbnail import Thumbnail, ThumbnailCache


class TestThumbnailModel:
    """Test Thumbnail model functionality."""

    def test_thumbnail_creation_minimal(self):
        """Test creating Thumbnail with minimal data."""
        with patch("src.models.thumbnail.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 1640995200.0
            thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=256, height=256)

        assert thumb.file_id == 1
        assert thumb.thumb_path == "test.webp"
        assert thumb.width == 256
        assert thumb.height == 256
        assert thumb.format == "webp"
        assert thumb.generated_at == 1640995200.0

    def test_thumbnail_creation_full(self):
        """Test creating Thumbnail with all fields."""
        thumb = Thumbnail(
            file_id=1,
            thumb_path="test.jpeg",
            width=512,
            height=384,
            format="jpeg",
            generated_at=1640995200.0,
        )

        assert thumb.file_id == 1
        assert thumb.thumb_path == "test.jpeg"
        assert thumb.width == 512
        assert thumb.height == 384
        assert thumb.format == "jpeg"
        assert thumb.generated_at == 1640995200.0

    def test_thumbnail_post_init_timestamp(self):
        """Test that timestamp is auto-generated if not provided."""
        with patch("src.models.thumbnail.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 1640995200.0
            thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=256, height=256)

        assert thumb.generated_at == 1640995200.0

    def test_thumbnail_post_init_format_lowercase(self):
        """Test that format is normalized to lowercase."""
        thumb = Thumbnail(
            file_id=1, thumb_path="test.WEBP", width=256, height=256, format="WEBP"
        )

        assert thumb.format == "webp"

    def test_create_for_photo_landscape(self):
        """Test creating thumbnail for landscape photo."""
        thumb = Thumbnail.create_for_photo(
            file_id=1, original_width=3000, original_height=2000, max_size=512
        )

        assert thumb.file_id == 1
        assert thumb.width == 512
        assert thumb.height == 341  # Maintains aspect ratio
        assert thumb.format == "webp"

    def test_create_for_photo_portrait(self):
        """Test creating thumbnail for portrait photo."""
        thumb = Thumbnail.create_for_photo(
            file_id=1, original_width=2000, original_height=3000, max_size=512
        )

        assert thumb.file_id == 1
        assert thumb.width == 341
        assert thumb.height == 512
        assert thumb.format == "webp"

    def test_create_for_photo_square(self):
        """Test creating thumbnail for square photo."""
        thumb = Thumbnail.create_for_photo(
            file_id=1, original_width=2000, original_height=2000, max_size=512
        )

        assert thumb.file_id == 1
        assert thumb.width == 512
        assert thumb.height == 512

    def test_create_for_photo_custom_format(self):
        """Test creating thumbnail with custom format."""
        thumb = Thumbnail.create_for_photo(
            file_id=1,
            original_width=2000,
            original_height=1500,
            max_size=512,
            img_format="jpeg",
        )

        assert thumb.format == "jpeg"
        assert ".jpeg" in thumb.thumb_path

    def test_create_for_photo_small_original(self):
        """Test creating thumbnail from small original."""
        thumb = Thumbnail.create_for_photo(
            file_id=1, original_width=300, original_height=200, max_size=512
        )

        # Should not exceed original size
        assert thumb.width == 300
        assert thumb.height == 200

    def test_from_db_row(self):
        """Test creating Thumbnail from database row."""
        row = {
            "file_id": 1,
            "thumb_path": "01/23/12345.webp",
            "width": 512,
            "height": 384,
            "format": "webp",
            "generated_at": 1640995200.0,
        }

        thumb = Thumbnail.from_db_row(row)

        assert thumb.file_id == 1
        assert thumb.thumb_path == "01/23/12345.webp"
        assert thumb.width == 512
        assert thumb.height == 384
        assert thumb.format == "webp"
        assert thumb.generated_at == 1640995200.0

    def test_to_dict(self):
        """Test converting Thumbnail to dictionary."""
        thumb = Thumbnail(
            file_id=1,
            thumb_path="test.webp",
            width=512,
            height=384,
            format="webp",
            generated_at=1640995200.0,
        )

        result = thumb.to_dict()

        assert result["file_id"] == 1
        assert result["thumb_path"] == "test.webp"
        assert result["width"] == 512
        assert result["height"] == 384
        assert result["format"] == "webp"
        assert result["generated_at"] == 1640995200.0

    def test_to_db_params(self):
        """Test converting Thumbnail to database parameters."""
        thumb = Thumbnail(
            file_id=1,
            thumb_path="test.webp",
            width=512,
            height=384,
            format="webp",
            generated_at=1640995200.0,
        )

        params = thumb.to_db_params()

        assert params[0] == 1
        assert params[1] == "test.webp"
        assert params[2] == 512
        assert params[3] == 384
        assert params[4] == "webp"
        assert params[5] == 1640995200.0

    def test_validate_valid_thumbnail(self):
        """Test validation of valid Thumbnail."""
        thumb = Thumbnail(
            file_id=1, thumb_path="test.webp", width=512, height=384, format="webp"
        )

        errors = thumb.validate()

        assert len(errors) == 0

    def test_validate_negative_file_id(self):
        """Test validation catches non-positive file_id."""
        thumb = Thumbnail(file_id=0, thumb_path="test.webp", width=512, height=384)

        errors = thumb.validate()

        assert any("File ID must be positive" in e for e in errors)

    def test_validate_empty_path(self):
        """Test validation catches empty path."""
        thumb = Thumbnail(file_id=1, thumb_path="", width=512, height=384)

        errors = thumb.validate()

        assert any("Thumbnail path is required" in e for e in errors)

    def test_validate_negative_dimensions(self):
        """Test validation catches non-positive dimensions."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=0, height=384)

        errors = thumb.validate()

        assert any("Width and height must be positive" in e for e in errors)

    def test_validate_dimensions_too_large(self):
        """Test validation catches dimensions too large."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=2000, height=384)

        errors = thumb.validate()

        assert any("Thumbnail dimensions too large" in e for e in errors)

    def test_validate_unsupported_format(self):
        """Test validation catches unsupported format."""
        thumb = Thumbnail(
            file_id=1, thumb_path="test.bmp", width=512, height=384, format="bmp"
        )

        errors = thumb.validate()

        assert any("Unsupported thumbnail format" in e for e in errors)

    def test_validate_supported_formats(self):
        """Test validation passes for supported formats."""
        for fmt in ["webp", "jpeg", "png"]:
            thumb = Thumbnail(
                file_id=1, thumb_path=f"test.{fmt}", width=512, height=384, format=fmt
            )
            errors = thumb.validate()
            assert not any("Unsupported thumbnail format" in e for e in errors)

    def test_is_valid(self):
        """Test is_valid method."""
        valid_thumb = Thumbnail(
            file_id=1, thumb_path="test.webp", width=512, height=384
        )
        assert valid_thumb.is_valid() is True

        invalid_thumb = Thumbnail(file_id=0, thumb_path="", width=0, height=0)
        assert invalid_thumb.is_valid() is False

    def test_get_absolute_path(self):
        """Test getting absolute path."""
        thumb = Thumbnail(
            file_id=1, thumb_path="01/23/12345.webp", width=512, height=384
        )

        abs_path = thumb.get_absolute_path("/cache/root")

        assert abs_path == "/cache/root/01/23/12345.webp"

    def test_file_exists_true(self):
        """Test file_exists when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=512, height=384)

            # Create the file
            test_file = Path(tmpdir) / "test.webp"
            test_file.write_text("test")

            assert thumb.file_exists(tmpdir) is True

    def test_file_exists_false(self):
        """Test file_exists when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            thumb = Thumbnail(
                file_id=1, thumb_path="nonexistent.webp", width=512, height=384
            )

            assert thumb.file_exists(tmpdir) is False

    def test_get_file_size(self):
        """Test getting file size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=512, height=384)

            # Create the file
            test_file = Path(tmpdir) / "test.webp"
            test_file.write_text("test content")

            size = thumb.get_file_size(tmpdir)

            assert size == len("test content")

    def test_get_file_size_nonexistent(self):
        """Test getting file size when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            thumb = Thumbnail(
                file_id=1, thumb_path="nonexistent.webp", width=512, height=384
            )

            size = thumb.get_file_size(tmpdir)

            assert size is None

    def test_get_aspect_ratio_landscape(self):
        """Test getting aspect ratio for landscape."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=800, height=600)

        ratio = thumb.get_aspect_ratio()

        assert abs(ratio - 1.333) < 0.01

    def test_get_aspect_ratio_portrait(self):
        """Test getting aspect ratio for portrait."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=600, height=800)

        ratio = thumb.get_aspect_ratio()

        assert abs(ratio - 0.75) < 0.01

    def test_get_aspect_ratio_zero_height(self):
        """Test getting aspect ratio with zero height."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=800, height=0)

        ratio = thumb.get_aspect_ratio()

        assert ratio == 0.0

    def test_is_landscape(self):
        """Test is_landscape method."""
        landscape = Thumbnail(file_id=1, thumb_path="test.webp", width=800, height=600)
        portrait = Thumbnail(file_id=1, thumb_path="test.webp", width=600, height=800)

        assert landscape.is_landscape() is True
        assert portrait.is_landscape() is False

    def test_is_portrait(self):
        """Test is_portrait method."""
        portrait = Thumbnail(file_id=1, thumb_path="test.webp", width=600, height=800)
        landscape = Thumbnail(file_id=1, thumb_path="test.webp", width=800, height=600)

        assert portrait.is_portrait() is True
        assert landscape.is_portrait() is False

    def test_is_square(self):
        """Test is_square method."""
        square = Thumbnail(file_id=1, thumb_path="test.webp", width=512, height=512)
        almost_square = Thumbnail(
            file_id=1, thumb_path="test.webp", width=512, height=510
        )
        landscape = Thumbnail(file_id=1, thumb_path="test.webp", width=512, height=384)

        assert square.is_square() is True
        assert almost_square.is_square() is True
        assert landscape.is_square() is False

    def test_is_square_custom_tolerance(self):
        """Test is_square with custom tolerance."""
        almost_square = Thumbnail(
            file_id=1, thumb_path="test.webp", width=512, height=500
        )

        assert almost_square.is_square(tolerance=0.05) is True
        assert almost_square.is_square(tolerance=0.01) is False

    def test_needs_regeneration_older_than_original(self):
        """Test needs_regeneration when thumbnail is older."""
        with tempfile.TemporaryDirectory() as tmpdir:
            thumb = Thumbnail(
                file_id=1,
                thumb_path="test.webp",
                width=512,
                height=384,
                generated_at=1640995200.0,
            )

            # Original modified after thumbnail was generated
            needs_regen = thumb.needs_regeneration(
                original_modified_time=1640995300.0, cache_root=tmpdir
            )

            assert needs_regen is True

    def test_needs_regeneration_newer_than_original(self):
        """Test needs_regeneration when thumbnail is newer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            thumb = Thumbnail(
                file_id=1,
                thumb_path="test.webp",
                width=512,
                height=384,
                generated_at=1640995300.0,
            )

            # Create the file
            test_file = Path(tmpdir) / "test.webp"
            test_file.write_text("test")

            # Original modified before thumbnail was generated
            needs_regen = thumb.needs_regeneration(
                original_modified_time=1640995200.0, cache_root=tmpdir
            )

            assert needs_regen is False

    def test_needs_regeneration_file_missing(self):
        """Test needs_regeneration when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            thumb = Thumbnail(
                file_id=1,
                thumb_path="nonexistent.webp",
                width=512,
                height=384,
                generated_at=1640995300.0,
            )

            needs_regen = thumb.needs_regeneration(
                original_modified_time=1640995200.0, cache_root=tmpdir
            )

            assert needs_regen is True

    def test_get_size_category_small(self):
        """Test size category for small thumbnail."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=100, height=100)

        assert thumb.get_size_category() == "small"

    def test_get_size_category_medium(self):
        """Test size category for medium thumbnail."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=200, height=200)

        assert thumb.get_size_category() == "medium"

    def test_get_size_category_large(self):
        """Test size category for large thumbnail."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=400, height=400)

        assert thumb.get_size_category() == "large"

    def test_get_size_category_xlarge(self):
        """Test size category for extra large thumbnail."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=800, height=600)

        assert thumb.get_size_category() == "xlarge"

    def test_get_display_size_landscape(self):
        """Test getting display size for landscape."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=800, height=600)

        display_width, display_height = thumb.get_display_size(target_size=400)

        assert display_width == 400
        assert display_height == 300

    def test_get_display_size_portrait(self):
        """Test getting display size for portrait."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=600, height=800)

        display_width, display_height = thumb.get_display_size(target_size=400)

        assert display_width == 300
        assert display_height == 400

    def test_get_display_size_zero_target(self):
        """Test getting display size with zero target."""
        thumb = Thumbnail(file_id=1, thumb_path="test.webp", width=800, height=600)

        display_width, display_height = thumb.get_display_size(target_size=0)

        assert display_width == 800
        assert display_height == 600

    def test_calculate_thumbnail_size_landscape(self):
        """Test calculating thumbnail size for landscape."""
        width, height = Thumbnail._calculate_thumbnail_size(3000, 2000, 512)

        assert width == 512
        assert height == 341

    def test_calculate_thumbnail_size_portrait(self):
        """Test calculating thumbnail size for portrait."""
        width, height = Thumbnail._calculate_thumbnail_size(2000, 3000, 512)

        assert width == 341
        assert height == 512

    def test_calculate_thumbnail_size_square(self):
        """Test calculating thumbnail size for square."""
        width, height = Thumbnail._calculate_thumbnail_size(2000, 2000, 512)

        assert width == 512
        assert height == 512

    def test_calculate_thumbnail_size_zero_dimensions(self):
        """Test calculating thumbnail size with zero dimensions."""
        width, height = Thumbnail._calculate_thumbnail_size(0, 0, 512)

        assert width == 512
        assert height == 512

    def test_calculate_thumbnail_size_smaller_than_max(self):
        """Test calculating thumbnail size when original is smaller."""
        width, height = Thumbnail._calculate_thumbnail_size(300, 200, 512)

        # Should not exceed original
        assert width == 300
        assert height == 200

    def test_generate_thumbnail_path_simple(self):
        """Test generating thumbnail path."""
        path = Thumbnail._generate_thumbnail_path(12345, "webp")

        assert path == "45/23/12345.webp"

    def test_generate_thumbnail_path_small_id(self):
        """Test generating thumbnail path with small file_id."""
        path = Thumbnail._generate_thumbnail_path(1, "webp")

        assert path == "00/00/1.webp"

    def test_generate_thumbnail_path_custom_format(self):
        """Test generating thumbnail path with custom format."""
        path = Thumbnail._generate_thumbnail_path(12345, "jpeg")

        assert path.endswith(".jpeg")

    def test_get_cache_directory_structure_nonexistent(self):
        """Test getting cache structure for non-existent directory."""
        result = Thumbnail.get_cache_directory_structure("/nonexistent/path")

        assert result["exists"] is False
        assert result["total_files"] == 0
        assert result["total_size_bytes"] == 0

    def test_get_cache_directory_structure_existing(self):
        """Test getting cache structure for existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            (Path(tmpdir) / "test1.webp").write_text("test1")
            (Path(tmpdir) / "test2.webp").write_text("test2")

            result = Thumbnail.get_cache_directory_structure(tmpdir)

            assert result["exists"] is True
            assert result["total_files"] == 2
            assert result["total_size_bytes"] > 0
            assert "total_size_mb" in result


class TestThumbnailCache:
    """Test ThumbnailCache functionality."""

    def test_thumbnail_cache_creation(self):
        """Test creating ThumbnailCache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ThumbnailCache(tmpdir, max_size=512, img_format="webp")

            assert cache.cache_root == Path(tmpdir)
            assert cache.max_size == 512
            assert cache.format == "webp"

    def test_thumbnail_cache_creates_directory(self):
        """Test that ThumbnailCache creates cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache"
            cache = ThumbnailCache(str(cache_path))

            assert cache_path.exists()

    def test_get_thumbnail_path(self):
        """Test getting thumbnail path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ThumbnailCache(tmpdir, img_format="webp")

            path = cache.get_thumbnail_path(12345)

            assert "12345.webp" in path
            assert tmpdir in path

    def test_ensure_directory_exists(self):
        """Test ensuring thumbnail directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ThumbnailCache(tmpdir)

            cache.ensure_directory_exists(12345)

            # Directory should be created
            thumb_path = Thumbnail._generate_thumbnail_path(12345, "webp")
            full_path = Path(tmpdir) / thumb_path
            assert full_path.parent.exists()

    def test_cleanup_orphaned_thumbnails(self):
        """Test cleaning up orphaned thumbnails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ThumbnailCache(tmpdir, img_format="webp")

            # Create test thumbnails
            for file_id in [1, 2, 3, 4, 5]:
                cache.ensure_directory_exists(file_id)
                thumb_path = cache.get_thumbnail_path(file_id)
                Path(thumb_path).write_text("test")

            # Keep only files 1, 2, 3
            removed = cache.cleanup_orphaned_thumbnails([1, 2, 3])

            assert removed == 2  # Files 4 and 5 should be removed

    def test_cleanup_orphaned_thumbnails_invalid_filenames(self):
        """Test cleanup ignores invalid filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ThumbnailCache(tmpdir, img_format="webp")

            # Create invalid filename
            (Path(tmpdir) / "invalid.webp").write_text("test")

            # Should not raise error
            removed = cache.cleanup_orphaned_thumbnails([1, 2, 3])

            assert removed == 0

    def test_cleanup_empty_directories(self):
        """Test cleaning up empty directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ThumbnailCache(tmpdir)

            # Create nested empty directories
            (Path(tmpdir) / "01" / "23").mkdir(parents=True, exist_ok=True)
            (Path(tmpdir) / "04" / "56").mkdir(parents=True, exist_ok=True)

            removed = cache.cleanup_empty_directories()

            assert removed >= 2  # Should remove empty directories

    def test_cleanup_empty_directories_with_files(self):
        """Test cleanup preserves directories with files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ThumbnailCache(tmpdir)

            # Create directory with file
            dir_path = Path(tmpdir) / "01" / "23"
            dir_path.mkdir(parents=True, exist_ok=True)
            (dir_path / "test.webp").write_text("test")

            # Create empty directory
            (Path(tmpdir) / "04" / "56").mkdir(parents=True, exist_ok=True)

            cache.cleanup_empty_directories()

            # Directory with file should still exist
            assert dir_path.exists()

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ThumbnailCache(tmpdir)

            # Create some test files
            (Path(tmpdir) / "test1.webp").write_text("test1")
            (Path(tmpdir) / "test2.webp").write_text("test2")

            stats = cache.get_cache_stats()

            assert stats["exists"] is True
            assert stats["total_files"] == 2
            assert stats["total_size_bytes"] > 0

    def test_get_cache_directory_structure_with_subdirectories(self):
        """Test cache structure counts subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectories
            (Path(tmpdir) / "subdir1").mkdir()
            (Path(tmpdir) / "subdir2").mkdir()
            (Path(tmpdir) / "test.webp").write_text("test")

            result = Thumbnail.get_cache_directory_structure(tmpdir)

            assert result["exists"] is True
            assert result["total_files"] == 1
            assert result["directories"] >= 2

    def test_cleanup_empty_directories_with_oserror(self):
        """Test cleanup handles OSError when removing directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ThumbnailCache(tmpdir)

            # Create a directory structure
            dir_path = Path(tmpdir) / "test_dir"
            dir_path.mkdir()

            # Mock rmdir to raise OSError
            def mock_rmdir(self):
                if "test_dir" in str(self):
                    raise OSError("Permission denied")
                # Call the original implementation for other paths
                import os
                os.rmdir(str(self))

            with patch.object(Path, "rmdir", mock_rmdir):
                removed = cache.cleanup_empty_directories()

                # Should handle the error gracefully
                assert removed >= 0
