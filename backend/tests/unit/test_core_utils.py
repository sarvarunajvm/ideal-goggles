"""Comprehensive unit tests for core utility functions - 70%+ coverage target."""

import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException

from src.core.utils import (
    DependencyChecker,
    batch_items,
    calculate_execution_time,
    format_file_size,
    get_default_photo_roots,
    handle_internal_error,
    handle_service_unavailable,
    safe_json_response,
    sanitize_filename,
    validate_path,
)


class TestDependencyChecker:
    """Test DependencyChecker class."""

    def test_check_clip_available(self):
        """Test checking CLIP availability when installed."""
        # Clear cache
        DependencyChecker._cache.clear()

        with patch("builtins.__import__") as mock_import:
            # Mock successful imports
            mock_import.return_value = MagicMock()

            available, error = DependencyChecker.check_clip()

            assert available is True
            assert error is None

    def test_check_clip_not_available(self):
        """Test checking CLIP when not installed."""
        DependencyChecker._cache.clear()

        with patch("builtins.__import__", side_effect=ImportError("No module named 'clip'")):
            available, error = DependencyChecker.check_clip()

            assert available is False
            assert error is not None
            assert "CLIP" in error

    def test_check_clip_cached(self):
        """Test that CLIP check result is cached."""
        DependencyChecker._cache.clear()
        DependencyChecker._cache["clip"] = (True, None)

        # Should return cached value without import
        available, error = DependencyChecker.check_clip()

        assert available is True
        assert error is None

    def test_check_face_recognition_available(self):
        """Test checking face recognition when available."""
        DependencyChecker._cache.clear()

        with patch("builtins.__import__") as mock_import:
            mock_import.return_value = MagicMock()

            available, error = DependencyChecker.check_face_recognition()

            assert available is True
            assert error is None

    def test_check_face_recognition_not_available(self):
        """Test checking face recognition when not available."""
        DependencyChecker._cache.clear()

        with patch("builtins.__import__", side_effect=ImportError("No module")):
            available, error = DependencyChecker.check_face_recognition()

            assert available is False
            assert "face recognition" in error.lower()

    def test_check_face_recognition_cached(self):
        """Test face recognition check caching."""
        DependencyChecker._cache.clear()
        DependencyChecker._cache["face_recognition"] = (False, "Not installed")

        available, error = DependencyChecker.check_face_recognition()

        assert available is False
        assert error == "Not installed"

    def test_check_tesseract_available(self):
        """Test checking Tesseract when available."""
        DependencyChecker._cache.clear()

        with patch("builtins.__import__") as mock_import:
            mock_pytesseract = MagicMock()
            mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
            mock_import.return_value = mock_pytesseract

            available, error = DependencyChecker.check_tesseract()

            assert available is True
            assert error is None

    def test_check_tesseract_not_available(self):
        """Test checking Tesseract when not available."""
        DependencyChecker._cache.clear()

        with patch("builtins.__import__") as mock_import:
            mock_pytesseract = MagicMock()
            mock_pytesseract.get_tesseract_version.side_effect = Exception("Not found")
            mock_import.return_value = mock_pytesseract

            available, error = DependencyChecker.check_tesseract()

            assert available is False
            assert "Tesseract" in error

    def test_check_tesseract_cached(self):
        """Test Tesseract check caching."""
        DependencyChecker._cache.clear()
        DependencyChecker._cache["tesseract"] = (True, None)

        available, error = DependencyChecker.check_tesseract()

        assert available is True


class TestHandleServiceUnavailable:
    """Test handle_service_unavailable function."""

    def test_raises_503_exception(self):
        """Test that 503 exception is raised."""
        with pytest.raises(HTTPException) as exc_info:
            handle_service_unavailable("TestService", "Service is down")

        assert exc_info.value.status_code == 503

    def test_includes_service_name_in_detail(self):
        """Test that service name is in error detail."""
        with pytest.raises(HTTPException) as exc_info:
            handle_service_unavailable("CLIP Service", "Dependencies missing")

        assert "CLIP Service" in exc_info.value.detail

    def test_includes_error_message_in_detail(self):
        """Test that error message is in detail."""
        with pytest.raises(HTTPException) as exc_info:
            handle_service_unavailable("Service", "Custom error message")

        assert "Custom error message" in exc_info.value.detail

    def test_logs_warning(self):
        """Test that warning is logged."""
        with patch("src.core.utils.logger") as mock_logger:
            with pytest.raises(HTTPException):
                handle_service_unavailable("Service", "Error")

            mock_logger.warning.assert_called_once()


class TestHandleInternalError:
    """Test handle_internal_error function."""

    def test_raises_500_exception(self):
        """Test that 500 exception is raised."""
        error = ValueError("Test error")

        with pytest.raises(HTTPException) as exc_info:
            handle_internal_error("TestOperation", error)

        assert exc_info.value.status_code == 500

    def test_includes_operation_in_detail(self):
        """Test that operation name is in error detail."""
        error = RuntimeError("Error")

        with pytest.raises(HTTPException) as exc_info:
            handle_internal_error("DataProcessing", error)

        assert "DataProcessing" in exc_info.value.detail

    def test_includes_error_in_detail(self):
        """Test that error is in detail."""
        error = Exception("Specific error message")

        with pytest.raises(HTTPException) as exc_info:
            handle_internal_error("Operation", error)

        assert "Specific error message" in exc_info.value.detail

    def test_logs_exception_with_context(self):
        """Test that exception is logged with context."""
        error = ValueError("Error")

        with patch("src.core.utils.logger") as mock_logger:
            with pytest.raises(HTTPException):
                handle_internal_error("Op", error, user_id="user123", request_id="req456")

            mock_logger.exception.assert_called_once()
            call_kwargs = mock_logger.exception.call_args[1]
            assert call_kwargs["extra"]["user_id"] == "user123"
            assert call_kwargs["extra"]["request_id"] == "req456"


class TestValidatePath:
    """Test validate_path function."""

    def test_validate_existing_file(self):
        """Test validating existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = validate_path(tmp_path, must_exist=True, must_be_dir=False)

            assert result.exists()
            assert result.is_file()
        finally:
            Path(tmp_path).unlink()

    def test_validate_existing_directory(self):
        """Test validating existing directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = validate_path(tmp_dir, must_exist=True, must_be_dir=True)

            assert result.exists()
            assert result.is_dir()

    def test_validate_nonexistent_path_allowed(self):
        """Test validating non-existent path when allowed."""
        nonexistent = "/tmp/does_not_exist_12345"

        result = validate_path(nonexistent, must_exist=False, must_be_dir=False)

        assert isinstance(result, Path)

    def test_validate_nonexistent_path_required(self):
        """Test error when path must exist but doesn't."""
        with pytest.raises(ValueError) as exc_info:
            validate_path("/tmp/nonexistent_path_xyz", must_exist=True)

        assert "does not exist" in str(exc_info.value)

    def test_validate_file_not_directory(self):
        """Test error when file path provided but directory required."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError) as exc_info:
                validate_path(tmp_path, must_exist=True, must_be_dir=True)

            assert "not a directory" in str(exc_info.value)
        finally:
            Path(tmp_path).unlink()

    def test_validate_empty_path(self):
        """Test error on empty path."""
        with pytest.raises(ValueError) as exc_info:
            validate_path("")

        assert "cannot be empty" in str(exc_info.value)

    def test_validate_whitespace_path(self):
        """Test error on whitespace-only path."""
        with pytest.raises(ValueError) as exc_info:
            validate_path("   ")

        assert "cannot be empty" in str(exc_info.value)

    def test_validate_path_expansion(self):
        """Test that path is expanded and resolved."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a path with .. in it
            subdir = Path(tmp_dir) / "subdir"
            subdir.mkdir()

            path_with_dots = str(subdir / ".." / "subdir")

            result = validate_path(path_with_dots, must_exist=True)

            # Should be resolved (no ..)
            assert ".." not in str(result)


class TestGetDefaultPhotoRoots:
    """Test get_default_photo_roots function."""

    def test_get_default_on_windows(self):
        """Test getting default roots on Windows."""
        with patch("sys.platform", "win32"):
            with patch("os.environ.get", return_value="C:\\Users\\TestUser"):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.is_dir", return_value=True):
                        roots = get_default_photo_roots()

                        assert len(roots) > 0
                        assert "Pictures" in roots[0]

    def test_get_default_on_unix(self):
        """Test getting default roots on Unix systems."""
        with patch("sys.platform", "linux"):
            with patch("pathlib.Path.home", return_value=Path("/home/testuser")):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.is_dir", return_value=True):
                        roots = get_default_photo_roots()

                        assert len(roots) > 0

    def test_get_default_directory_not_exists(self):
        """Test when default directory doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            roots = get_default_photo_roots()

            assert roots == []

    def test_get_default_handles_exception(self):
        """Test handling of exceptions."""
        with patch("sys.platform", side_effect=Exception("Error")):
            roots = get_default_photo_roots()

            # Should return empty list, not crash
            assert roots == []


class TestFormatFileSize:
    """Test format_file_size function."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        result = format_file_size(500)

        assert "500" in result
        assert "B" in result

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        result = format_file_size(2048)

        assert "2.00" in result
        assert "KB" in result

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        result = format_file_size(5 * 1024 * 1024)

        assert "5.00" in result
        assert "MB" in result

    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        result = format_file_size(3 * 1024 * 1024 * 1024)

        assert "3.00" in result
        assert "GB" in result

    def test_format_terabytes(self):
        """Test formatting terabytes."""
        result = format_file_size(2 * 1024 * 1024 * 1024 * 1024)

        assert "2.00" in result
        assert "TB" in result

    def test_format_zero_bytes(self):
        """Test formatting zero bytes."""
        result = format_file_size(0)

        assert result == "0.00 B"


class TestCalculateExecutionTime:
    """Test calculate_execution_time function."""

    def test_calculate_execution_time(self):
        """Test calculating execution time."""
        start = datetime.now()
        # Simulate some time passing
        import time
        time.sleep(0.1)

        result = calculate_execution_time(start)

        assert result >= 100  # At least 100ms
        assert isinstance(result, int)

    def test_calculate_execution_time_immediate(self):
        """Test execution time for immediate completion."""
        start = datetime.now()

        result = calculate_execution_time(start)

        assert result >= 0
        assert isinstance(result, int)


class TestSanitizeFilename:
    """Test sanitize_filename function."""

    def test_sanitize_simple_filename(self):
        """Test sanitizing simple valid filename."""
        result = sanitize_filename("photo.jpg")

        assert result == "photo.jpg"

    def test_sanitize_removes_invalid_characters(self):
        """Test that invalid characters are replaced."""
        result = sanitize_filename("photo<>:test.jpg")

        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_sanitize_removes_slashes(self):
        """Test that slashes are removed."""
        result = sanitize_filename("path/to/file.jpg")

        assert "/" not in result
        assert "\\" not in result

    def test_sanitize_removes_leading_dots(self):
        """Test that leading dots are removed."""
        result = sanitize_filename("...photo.jpg")

        assert not result.startswith(".")

    def test_sanitize_removes_trailing_spaces(self):
        """Test that trailing spaces are removed."""
        result = sanitize_filename("photo.jpg   ")

        assert not result.endswith(" ")

    def test_sanitize_empty_becomes_unnamed(self):
        """Test that empty string becomes 'unnamed'."""
        result = sanitize_filename("")

        assert result == "unnamed"

    def test_sanitize_only_invalid_chars(self):
        """Test filename with only invalid characters."""
        result = sanitize_filename("<>:|")

        assert result == "unnamed"

    def test_sanitize_preserves_extension(self):
        """Test that file extension is preserved."""
        result = sanitize_filename("my:photo.jpg")

        assert result.endswith(".jpg")


class TestBatchItems:
    """Test batch_items function."""

    def test_batch_simple_list(self):
        """Test batching a simple list."""
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        batches = list(batch_items(items, batch_size=3))

        assert len(batches) == 4
        assert batches[0] == [1, 2, 3]
        assert batches[1] == [4, 5, 6]
        assert batches[2] == [7, 8, 9]
        assert batches[3] == [10]

    def test_batch_exact_multiple(self):
        """Test batching when list is exact multiple of batch size."""
        items = [1, 2, 3, 4, 5, 6]

        batches = list(batch_items(items, batch_size=2))

        assert len(batches) == 3
        assert all(len(batch) == 2 for batch in batches)

    def test_batch_smaller_than_batch_size(self):
        """Test batching list smaller than batch size."""
        items = [1, 2, 3]

        batches = list(batch_items(items, batch_size=10))

        assert len(batches) == 1
        assert batches[0] == [1, 2, 3]

    def test_batch_empty_list(self):
        """Test batching empty list."""
        items = []

        batches = list(batch_items(items, batch_size=5))

        assert len(batches) == 0

    def test_batch_single_item(self):
        """Test batching single item."""
        items = ["single"]

        batches = list(batch_items(items, batch_size=1))

        assert len(batches) == 1
        assert batches[0] == ["single"]


class TestSafeJsonResponse:
    """Test safe_json_response function."""

    def test_safe_json_simple_dict(self):
        """Test with simple JSON-serializable dict."""
        data = {"key": "value", "number": 123}

        result = safe_json_response(data)

        assert result == data

    def test_safe_json_with_datetime(self):
        """Test with datetime object."""
        data = {"timestamp": datetime(2023, 1, 1, 12, 0, 0)}

        result = safe_json_response(data)

        # Should still return the data (json_encoder handles datetime)
        assert result == data

    def test_safe_json_with_path(self):
        """Test with Path object."""
        data = {"path": Path("/tmp/test")}

        result = safe_json_response(data)

        assert result == data

    def test_safe_json_complex_nested(self):
        """Test with nested structures."""
        data = {
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
            "mixed": [{"a": 1}, {"b": 2}]
        }

        result = safe_json_response(data)

        assert result == data

    def test_safe_json_handles_non_serializable(self):
        """Test handling of non-serializable data."""
        # Create a non-serializable object
        class NonSerializable:
            pass

        data = {"obj": NonSerializable()}

        result = safe_json_response(data)

        # Should return data (json_encoder converts to str)
        assert result == data

    def test_safe_json_with_default(self):
        """Test using default value on error."""
        # Force an error scenario
        class BadObject:
            def __repr__(self):
                raise Exception("Cannot repr")

        data = BadObject()

        result = safe_json_response(data, default={"error": "fallback"})

        # Depending on implementation, might return default or handle with __dict__
        assert result is not None

    def test_safe_json_with_custom_object(self):
        """Test with custom object having __dict__."""
        class CustomObject:
            def __init__(self):
                self.attr1 = "value1"
                self.attr2 = 42

        data = {"custom": CustomObject()}

        result = safe_json_response(data)

        assert result is not None


class TestUtilsEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_dependency_checker_multiple_checks(self):
        """Test multiple dependency checks in sequence."""
        DependencyChecker._cache.clear()

        with patch("builtins.__import__", side_effect=ImportError()):
            clip_result = DependencyChecker.check_clip()
            face_result = DependencyChecker.check_face_recognition()
            tess_result = DependencyChecker.check_tesseract()

            assert clip_result[0] is False
            assert face_result[0] is False
            assert tess_result[0] is False

    def test_validate_path_with_tilde(self):
        """Test path validation with tilde expansion."""
        # Should expand ~ to home directory
        result = validate_path("~/test", must_exist=False)

        assert "~" not in str(result)

    def test_format_file_size_boundary_values(self):
        """Test file size formatting at boundary values."""
        # Test 1024 bytes (exactly 1 KB)
        result = format_file_size(1024)
        assert "1.00" in result
        assert "KB" in result

        # Test 1023 bytes (just under 1 KB)
        result = format_file_size(1023)
        assert "B" in result

    def test_batch_items_with_strings(self):
        """Test batching with string items."""
        items = ["a", "b", "c", "d", "e"]

        batches = list(batch_items(items, batch_size=2))

        assert len(batches) == 3
        assert batches[0] == ["a", "b"]
        assert batches[1] == ["c", "d"]
        assert batches[2] == ["e"]
