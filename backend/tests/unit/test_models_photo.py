"""Unit tests for Photo model."""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.models.photo import Photo


class TestPhotoModel:
    """Test Photo model functionality."""

    def test_photo_creation_from_valid_data(self):
        """Test creating a Photo from valid data."""
        photo = Photo(
            id=1,
            path="/test/photo.jpg",
            folder="/test",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="da39a3ee5e6b4b0d3255bfef95601890afd80709",
        )

        assert photo.id == 1
        assert photo.path == "/test/photo.jpg"
        assert photo.folder == "/test"
        assert photo.filename == "photo.jpg"
        assert photo.ext == ".jpg"
        assert photo.size == 1024
        assert photo.sha1 == "da39a3ee5e6b4b0d3255bfef95601890afd80709"

    def test_photo_creation_with_optional_fields(self):
        """Test creating a Photo with optional fields."""
        photo = Photo(
            id=1,
            path="/test/photo.jpg",
            folder="/test",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="da39a3ee5e6b4b0d3255bfef95601890afd80709",
            phash="abc123",
            indexed_at=1640995300.0,
            index_version=2,
        )

        assert photo.phash == "abc123"
        assert photo.indexed_at == 1640995300.0
        assert photo.index_version == 2

    def test_photo_creation_with_defaults(self):
        """Test Photo creation with default values."""
        photo = Photo(
            id=1,
            path="/test/photo.jpg",
            folder="/test",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="da39a3ee5e6b4b0d3255bfef95601890afd80709",
        )

        assert photo.phash is None
        assert photo.indexed_at is None
        assert photo.index_version == 1  # Default value

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_from_file_path_valid_file(self, mock_stat, mock_exists):
        """Test creating Photo from valid file path."""
        mock_exists.return_value = True
        mock_stat.return_value = Mock(
            st_size=2048, st_ctime=1640995200.0, st_mtime=1640995300.0
        )

        with patch("builtins.open", mock_open_hash("test content")):
            photo = Photo.from_file_path("/test/photos/image.jpg")

        assert "/test/photos/image.jpg" in photo.path
        assert photo.folder == "/test/photos"
        assert photo.filename == "image.jpg"
        assert photo.ext == ".jpg"
        assert photo.size == 2048
        assert photo.created_ts == 1640995200.0
        assert photo.modified_ts == 1640995300.0
        assert len(photo.sha1) == 64  # SHA-256 hash length (not SHA-1)

    @patch("pathlib.Path.exists")
    def test_from_file_path_nonexistent_file(self, mock_exists):
        """Test creating Photo from non-existent file path."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError):
            Photo.from_file_path("/test/nonexistent.jpg")

    def test_validate_unsupported_extension(self):
        """Test validation catches unsupported file extension."""
        photo = Photo(
            path="/test/document.txt",
            filename="document.txt",
            ext=".txt",
            size=1024,
            sha1="a" * 64,  # Valid length for SHA-256
        )

        errors = photo.validate()
        assert any("Unsupported file extension" in error for error in errors)

    def test_validate_valid_extensions(self):
        """Test validation passes for valid photo extensions."""
        valid_extensions = [".jpg", ".jpeg", ".png", ".tiff", ".tif"]

        for ext in valid_extensions:
            photo = Photo(
                path=f"/test/image{ext}",
                filename=f"image{ext}",
                ext=ext,
                size=1024,
                sha1="a" * 64,
            )
            errors = photo.validate()
            # Should not have extension-related errors
            assert not any("Unsupported file extension" in error for error in errors)

    def test_validate_invalid_parameters(self):
        """Test validation catches various invalid parameters."""
        photo = Photo(
            path="relative/path.jpg",  # Not absolute
            filename="photo.jpg",
            ext=".txt",  # Invalid extension
            size=0,  # Invalid size
            sha1="short",  # Invalid hash length
            phash="short",  # Invalid phash length
        )

        errors = photo.validate()
        assert len(errors) >= 4  # Should catch multiple issues

    def test_needs_reprocessing_never_indexed(self):
        """Test needs_reprocessing for never indexed photo."""
        photo = Photo(
            id=1,
            path="/test/photo.jpg",
            folder="/test",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="da39a3ee5e6b4b0d3255bfef95601890afd80709",
            indexed_at=None,
        )

        assert photo.needs_reprocessing() is True

    @patch("pathlib.Path.exists")
    def test_needs_reprocessing_file_modified_after_indexing(self, mock_exists):
        """Test needs_reprocessing when file was modified after indexing."""
        mock_exists.return_value = True

        photo = Photo(
            id=1,
            path="/test/photo.jpg",
            folder="/test",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995400.0,  # Modified after indexing
            sha1="a" * 64,
            indexed_at=1640995300.0,  # Indexed before modification
            index_version=1,
        )

        assert photo.needs_reprocessing() is True

    @patch("pathlib.Path.exists")
    def test_needs_reprocessing_up_to_date(self, mock_exists):
        """Test needs_reprocessing for up-to-date photo."""
        mock_exists.return_value = True

        photo = Photo(
            id=1,
            path="/test/photo.jpg",
            folder="/test",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="a" * 64,
            indexed_at=1640995300.0,  # Indexed after modification
            index_version=1,
        )

        assert photo.needs_reprocessing() is False

    @patch("pathlib.Path.exists")
    def test_needs_reprocessing_file_missing(self, mock_exists):
        """Test needs_reprocessing when file no longer exists."""
        mock_exists.return_value = False

        photo = Photo(
            id=1,
            path="/test/photo.jpg",
            folder="/test",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="a" * 64,
            indexed_at=1640995300.0,
            index_version=1,
        )

        # Should return False when file doesn't exist
        assert photo.needs_reprocessing() is False

    def test_get_relative_folder(self):
        """Test getting relative folder path from absolute path."""
        photo = Photo(
            id=1,
            path="/home/user/photos/vacation/beach.jpg",
            folder="/home/user/photos/vacation",
            filename="beach.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="a" * 64,
        )

        relative_folder = photo.get_relative_folder("/home/user/photos")
        assert relative_folder == "vacation"

    def test_get_relative_folder_no_common_base(self):
        """Test getting relative folder with no common base."""
        photo = Photo(
            id=1,
            path="/different/path/photo.jpg",
            folder="/different/path",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="a" * 64,
        )

        relative_folder = photo.get_relative_folder("/home/user/photos")
        assert relative_folder == "/different/path"  # Returns absolute path

    def test_to_dict(self):
        """Test converting Photo to dictionary."""
        photo = Photo(
            id=1,
            path="/test/photo.jpg",
            folder="/test",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="da39a3ee5e6b4b0d3255bfef95601890afd80709",
            phash="abc123",
            indexed_at=1640995300.0,
            index_version=2,
        )

        photo_dict = photo.to_dict()

        assert photo_dict["id"] == 1
        assert photo_dict["path"] == "/test/photo.jpg"
        assert photo_dict["folder"] == "/test"
        assert photo_dict["filename"] == "photo.jpg"
        assert photo_dict["ext"] == ".jpg"
        assert photo_dict["size"] == 1024
        assert photo_dict["sha1"] == "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        assert photo_dict["phash"] == "abc123"
        assert photo_dict["indexed_at"] == 1640995300.0
        assert photo_dict["index_version"] == 2

    def test_str_representation(self):
        """Test string representation of Photo."""
        photo = Photo(
            id=1,
            path="/test/photo.jpg",
            folder="/test",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            created_ts=1640995200.0,
            modified_ts=1640995200.0,
            sha1="da39a3ee5e6b4b0d3255bfef95601890afd80709",
        )

        str_repr = str(photo)
        assert "photo.jpg" in str_repr
        assert "1024" in str_repr

    def test_calculate_sha256_hash(self):
        """Test SHA-256 hash calculation."""
        test_content = b"test content for hashing"
        expected_hash = hashlib.sha256(test_content).hexdigest()

        with patch("builtins.open", mock_open_hash_content(test_content)):
            calculated_hash = Photo._calculate_sha1("/test/file.jpg")

        assert calculated_hash == expected_hash

    def test_calculate_sha256_hash_empty_file(self):
        """Test SHA-256 hash calculation for empty file."""
        expected_hash = hashlib.sha256(b"").hexdigest()

        with patch("builtins.open", mock_open_hash_content(b"")):
            calculated_hash = Photo._calculate_sha1("/test/empty.jpg")

        assert calculated_hash == expected_hash

    def test_file_exists(self):
        """Test file_exists method."""
        photo = Photo(path="/test/photo.jpg")

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            assert photo.file_exists() is True

            mock_exists.return_value = False
            assert photo.file_exists() is False

    def test_mark_indexed(self):
        """Test mark_indexed method."""
        photo = Photo()

        with patch("src.models.photo.datetime") as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = 1640995300.0
            photo.mark_indexed()

        assert photo.indexed_at == 1640995300.0

    def test_get_display_name(self):
        """Test get_display_name method."""
        photo = Photo(filename="vacation_photo.jpg")
        assert photo.get_display_name() == "vacation_photo.jpg"

    def test_is_valid(self):
        """Test is_valid method."""
        # Valid photo - validation expects SHA-1 format (40 chars) even though implementation uses SHA-256
        valid_photo = Photo(
            path="/test/photo.jpg",
            filename="photo.jpg",
            ext=".jpg",
            size=1024,
            sha1="a" * 40,  # Validation expects SHA-1 length
        )
        assert valid_photo.is_valid() is True

        # Invalid photo
        invalid_photo = Photo(
            path="relative/path.jpg",  # Not absolute
            filename="photo.jpg",
            ext=".txt",  # Invalid extension
            size=0,  # Invalid size
            sha1="short",  # Invalid hash
        )
        assert invalid_photo.is_valid() is False


def mock_open_hash(content: str):
    """Mock open function that returns specific content for hash calculation."""
    from unittest.mock import mock_open

    content_bytes = content.encode("utf-8")
    return mock_open(read_data=content_bytes)


def mock_open_hash_content(content: bytes):
    """Mock open function that returns specific byte content for hash calculation."""
    from unittest.mock import mock_open

    return mock_open(read_data=content)
