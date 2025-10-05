"""Common utility functions for the Ideal Goggles backend."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException, status

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class DependencyChecker:
    """Check and cache availability of optional dependencies."""

    _cache = {}

    @classmethod
    def check_clip(cls) -> tuple[bool, Optional[str]]:
        """Check if CLIP dependencies are available.

        Returns:
            tuple: (is_available, error_message)
        """
        if "clip" in cls._cache:
            return cls._cache["clip"]

        try:
            import clip
            import torch
            cls._cache["clip"] = (True, None)
            return (True, None)
        except ImportError as e:
            error_msg = f"CLIP dependencies not installed: {e}"
            cls._cache["clip"] = (False, error_msg)
            return (False, error_msg)

    @classmethod
    def check_face_recognition(cls) -> tuple[bool, Optional[str]]:
        """Check if face recognition dependencies are available.

        Returns:
            tuple: (is_available, error_message)
        """
        if "face_recognition" in cls._cache:
            return cls._cache["face_recognition"]

        try:
            import face_recognition
            cls._cache["face_recognition"] = (True, None)
            return (True, None)
        except ImportError as e:
            error_msg = f"Face recognition not installed: {e}"
            cls._cache["face_recognition"] = (False, error_msg)
            return (False, error_msg)

    @classmethod
    def check_tesseract(cls) -> tuple[bool, Optional[str]]:
        """Check if Tesseract OCR is available.

        Returns:
            tuple: (is_available, error_message)
        """
        if "tesseract" in cls._cache:
            return cls._cache["tesseract"]

        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            cls._cache["tesseract"] = (True, None)
            return (True, None)
        except Exception as e:
            error_msg = f"Tesseract not available: {e}"
            cls._cache["tesseract"] = (False, error_msg)
            return (False, error_msg)


def handle_service_unavailable(service_name: str, error_msg: str) -> None:
    """Raise a consistent 503 error for unavailable services.

    Args:
        service_name: Name of the service
        error_msg: Detailed error message

    Raises:
        HTTPException: 503 Service Unavailable
    """
    logger.warning(f"{service_name} unavailable: {error_msg}")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{service_name} unavailable: {error_msg}"
    )


def handle_internal_error(operation: str, error: Exception, **context) -> None:
    """Handle internal server errors consistently.

    Args:
        operation: Name of the operation that failed
        error: The exception that occurred
        **context: Additional context for logging

    Raises:
        HTTPException: 500 Internal Server Error
    """
    logger.exception(f"{operation} failed: {error}", extra=context)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{operation} failed: {str(error)}"
    )


def validate_path(path_str: str, must_exist: bool = True, must_be_dir: bool = False) -> Path:
    """Validate and resolve a path string.

    Args:
        path_str: Path string to validate
        must_exist: Whether the path must exist
        must_be_dir: Whether the path must be a directory

    Returns:
        Path: Resolved Path object

    Raises:
        ValueError: If validation fails
    """
    if not path_str or not path_str.strip():
        raise ValueError("Path cannot be empty")

    path = Path(path_str).expanduser().resolve()

    if must_exist and not path.exists():
        raise ValueError(f"Path does not exist: {path}")

    if must_be_dir and path.exists() and not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    return path


def get_default_photo_roots() -> list[str]:
    """Get OS-specific default photo directories.

    Returns:
        list: List of default photo directory paths
    """
    import sys

    try:
        if sys.platform.startswith("win"):
            import os
            userprofile = os.environ.get("USERPROFILE", str(Path.home()))
            candidate = Path(userprofile) / "Pictures"
        else:
            candidate = Path.home() / "Pictures"

        if candidate.exists() and candidate.is_dir():
            return [str(candidate.resolve())]
    except Exception as e:
        logger.warning(f"Could not determine default photo roots: {e}")

    return []


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Human-readable size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def calculate_execution_time(start_time: datetime) -> int:
    """Calculate execution time in milliseconds.

    Args:
        start_time: Start time

    Returns:
        int: Execution time in milliseconds
    """
    return int((datetime.now() - start_time).total_seconds() * 1000)


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe filesystem operations.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed"
    return sanitized


def batch_items(items: list, batch_size: int):
    """Yield batches of items from a list.

    Args:
        items: List of items to batch
        batch_size: Size of each batch

    Yields:
        List slices of batch_size
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def safe_json_response(data: Any, default: Any = None) -> Any:
    """Ensure data is JSON serializable.

    Args:
        data: Data to serialize
        default: Default value if serialization fails

    Returns:
        JSON-safe version of the data
    """
    import json
    from datetime import date, datetime

    def json_encoder(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)

    try:
        # Test if it's serializable
        json.dumps(data, default=json_encoder)
        return data
    except (TypeError, ValueError) as e:
        logger.warning(f"Data not JSON serializable: {e}")
        return default if default is not None else {"error": "Data serialization failed"}