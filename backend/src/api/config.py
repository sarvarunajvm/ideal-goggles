"""Configuration endpoints for Ideal Goggles API."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from ..db.connection import get_database_manager

router = APIRouter()


class ConfigurationResponse(BaseModel):
    """Configuration response model."""

    roots: list[str] = Field(description="Configured root folders")
    ocr_languages: list[str] = Field(description="Enabled OCR languages")
    face_search_enabled: bool = Field(description="Whether face search is enabled")
    semantic_search_enabled: bool = Field(
        description="Whether semantic search is enabled"
    )
    batch_size: int = Field(description="Batch size for processing")
    thumbnail_size: str = Field(description="Thumbnail size preset")
    index_version: str = Field(description="Current index version")


class UpdateRootsRequest(BaseModel):
    """Request model for updating root folders."""

    roots: list[str] = Field(description="Array of root folder paths")

    @field_validator("roots")
    @classmethod
    def validate_roots(cls, v):
        """Validate root folder paths."""
        validated_roots = []
        for root_path in v:
            # Check for empty strings
            if not root_path or not root_path.strip():
                msg = "Root path cannot be empty"
                raise ValueError(msg)

            # Expand home directory and resolve path
            path = Path(root_path).expanduser().resolve()

            if not path.exists():
                msg = f"Path does not exist: {root_path} (resolved to {path})"
                raise ValueError(msg)
            if not path.is_dir():
                msg = f"Path is not a directory: {root_path} (resolved to {path})"
                raise ValueError(msg)

            # Store the expanded/resolved path
            validated_roots.append(str(path))

        return validated_roots


class UpdateConfigRequest(BaseModel):
    """Request model for updating configuration."""

    ocr_languages: list[str] | None = Field(None, description="OCR languages to enable")
    face_search_enabled: bool | None = Field(
        None, description="Enable/disable face search"
    )
    semantic_search_enabled: bool | None = Field(
        None, description="Enable/disable semantic search"
    )
    batch_size: int | None = Field(
        None, ge=1, le=500, description="Batch size for processing"
    )
    thumbnail_size: str | None = Field(
        None, description="Thumbnail size preset (small/medium/large)"
    )
    thumbnail_quality: int | None = Field(
        None, ge=50, le=100, description="Thumbnail quality"
    )

    @field_validator("ocr_languages")
    @classmethod
    def validate_ocr_languages(cls, v):
        """Validate OCR language codes."""
        if v is not None:
            valid_languages = [
                "eng",
                "tam",
            ]
            for lang in v:
                if lang not in valid_languages:
                    msg = f"Unsupported OCR language: {lang}"
                    raise ValueError(msg)
        return v


@router.get("/config", response_model=ConfigurationResponse)
async def get_configuration() -> ConfigurationResponse:
    """
    Get current configuration.

    Returns:
        Current system configuration
    """
    try:
        db_manager = get_database_manager()

        # Get configuration from database
        config_data = _get_config_from_db(db_manager)

        return ConfigurationResponse(
            roots=config_data.get("roots", []),
            ocr_languages=config_data.get("ocr_languages", ["eng"]),
            face_search_enabled=config_data.get("face_search_enabled", False),
            semantic_search_enabled=config_data.get("semantic_search_enabled", True),
            batch_size=config_data.get("batch_size", 50),
            thumbnail_size=config_data.get("thumbnail_size", "medium"),
            index_version=config_data.get("index_version", "1"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {e!s}",
        )


@router.post("/config/roots")
async def update_root_folders(request: UpdateRootsRequest) -> dict[str, Any]:
    """
    Update root folders for indexing.

    Args:
        request: Request containing new root folder paths

    Returns:
        Success message and updated configuration
    """
    try:
        db_manager = get_database_manager()

        # Convert to absolute paths
        absolute_roots = []
        for root_path in request.roots:
            abs_path = str(Path(root_path).absolute())
            absolute_roots.append(abs_path)

        # Update configuration in database
        _update_config_in_db(db_manager, "roots", absolute_roots)

        # Log the configuration change
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Root folders updated: {absolute_roots}")

        return {
            "message": "Root folders updated successfully",
            "roots": absolute_roots,
            "updated_at": datetime.now().isoformat(),
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update root folders: {e!s}",
        )


@router.put("/config")
async def update_configuration(request: UpdateConfigRequest) -> dict[str, Any]:
    """
    Update system configuration.

    Args:
        request: Request containing configuration updates

    Returns:
        Success message and updated configuration
    """
    try:
        db_manager = get_database_manager()
        updated_fields = []

        # Update OCR languages if provided
        if request.ocr_languages is not None:
            _update_config_in_db(db_manager, "ocr_languages", request.ocr_languages)
            updated_fields.append("ocr_languages")

        # Update face search setting if provided
        if request.face_search_enabled is not None:
            _update_config_in_db(
                db_manager, "face_search_enabled", request.face_search_enabled
            )
            updated_fields.append("face_search_enabled")

        # Update semantic search setting if provided
        if request.semantic_search_enabled is not None:
            _update_config_in_db(
                db_manager, "semantic_search_enabled", request.semantic_search_enabled
            )
            updated_fields.append("semantic_search_enabled")

        # Update batch size if provided
        if request.batch_size is not None:
            _update_config_in_db(db_manager, "batch_size", request.batch_size)
            updated_fields.append("batch_size")

        # Update thumbnail settings if provided
        if request.thumbnail_size is not None:
            _update_config_in_db(db_manager, "thumbnail_size", request.thumbnail_size)
            updated_fields.append("thumbnail_size")

        if request.thumbnail_quality is not None:
            _update_config_in_db(
                db_manager, "thumbnail_quality", request.thumbnail_quality
            )
            updated_fields.append("thumbnail_quality")

        if not updated_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No configuration fields provided for update",
            )

        # Get updated configuration
        updated_config = _get_config_from_db(db_manager)

        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Configuration updated: {updated_fields}")

        return {
            "message": "Configuration updated successfully",
            "updated_fields": updated_fields,
            "configuration": updated_config,
            "updated_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {e!s}",
        )


@router.get("/config/defaults")
async def get_default_configuration() -> dict[str, Any]:
    """
    Get default configuration values.

    Returns:
        Default configuration settings
    """
    return {
        "roots": [],
        "ocr_languages": ["eng", "tam"],
        "face_search_enabled": False,
        "semantic_search_enabled": True,
        "batch_size": 50,
        "thumbnail_size": "medium",
        "thumbnail_quality": 85,
        "index_version": "1",
        "supported_ocr_languages": [
            "eng",
            "tam",
        ],
        "supported_image_formats": [".jpg", ".jpeg", ".png", ".tiff", ".tif"],
        "thumbnail_size_options": ["small", "medium", "large"],
        "max_batch_size": 500,
        "min_batch_size": 1,
    }


@router.delete("/config/roots/{root_index}")
async def remove_root_folder(root_index: int) -> dict[str, Any]:
    """
    Remove a root folder by index.

    Args:
        root_index: Index of the root folder to remove

    Returns:
        Success message and updated root folders
    """
    try:
        db_manager = get_database_manager()

        # Get current roots
        config_data = _get_config_from_db(db_manager)
        current_roots = config_data.get("roots", [])

        if root_index < 0 or root_index >= len(current_roots):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Root folder index {root_index} not found",
            )

        # Remove the specified root
        removed_root = current_roots.pop(root_index)
        _update_config_in_db(db_manager, "roots", current_roots)

        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Root folder removed: {removed_root}")

        return {
            "message": "Root folder removed successfully",
            "removed_root": removed_root,
            "remaining_roots": current_roots,
            "updated_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove root folder: {e!s}",
        )


@router.post("/config/reset")
async def reset_configuration() -> dict[str, Any]:
    """
    Reset configuration to defaults.

    Returns:
        Success message and default configuration
    """
    try:
        db_manager = get_database_manager()

        # Reset to default values
        default_config = {
            "roots": [],
            "ocr_languages": ["eng", "tam"],
            "face_search_enabled": False,
            "thumbnail_size": "medium",
            "thumbnail_quality": 85,
        }

        # Update each setting
        for key, value in default_config.items():
            _update_config_in_db(db_manager, key, value)

        import logging

        logger = logging.getLogger(__name__)
        logger.info("Configuration reset to defaults")

        return {
            "message": "Configuration reset to defaults",
            "configuration": default_config,
            "reset_at": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset configuration: {e!s}",
        )


def _parse_json_setting(key: str, value: str) -> Any:
    """Parse JSON setting with fallbacks."""
    try:
        import json

        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {"roots": [], "ocr_languages": ["eng", "tam"]}.get(key, [])


def _parse_boolean_setting(value: str) -> bool:
    """Parse boolean setting."""
    return value.lower() in ("true", "1", "yes")


def _parse_int_setting(key: str, value: str) -> int:
    """Parse integer setting with fallbacks."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return {"thumbnail_quality": 85}.get(key, 0)


def _parse_setting_value(key: str, value: str) -> Any:
    """Parse setting value based on key type."""
    if key in ["roots", "ocr_languages"]:
        return _parse_json_setting(key, value)
    if key == "face_search_enabled":
        return _parse_boolean_setting(value)
    if key == "thumbnail_quality":
        return _parse_int_setting(key, value)
    if key == "thumbnail_size":
        return value
    return value


def _get_config_defaults() -> dict[str, Any]:
    """Get default configuration values."""
    return {
        "roots": [],
        "ocr_languages": ["eng", "tam"],
        "face_search_enabled": False,
        "thumbnail_size": "medium",
        "thumbnail_quality": 85,
        "index_version": "1",
    }


def _get_config_from_db(db_manager) -> dict[str, Any]:
    """Get configuration settings from database."""
    try:
        # Query all settings
        settings_query = "SELECT key, value FROM settings"
        settings_rows = db_manager.execute_query(settings_query)

        # Parse settings
        settings_dict = {}
        for row in settings_rows:
            key, value = row[0], row[1]
            settings_dict[key] = _parse_setting_value(key, value)

        # Apply defaults for missing settings
        defaults = _get_config_defaults()
        for key, default_value in defaults.items():
            if key not in settings_dict:
                settings_dict[key] = default_value

        return settings_dict

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception(f"Failed to get configuration from database: {e}")

        # Return defaults on error
        return {
            "roots": [],
            "ocr_languages": ["eng", "tam"],
            "face_search_enabled": False,
            "thumbnail_size": "medium",
            "thumbnail_quality": 85,
            "index_version": "1",
        }


def _update_config_in_db(db_manager, key: str, value: Any):
    """Update a configuration setting in the database."""
    import json

    # Serialize complex values as JSON
    if isinstance(value, (list, dict)):
        serialized_value = json.dumps(value)
    elif isinstance(value, bool):
        serialized_value = "true" if value else "false"
    else:
        serialized_value = str(value)

    # Use INSERT OR REPLACE to update or create setting
    update_query = """
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, datetime('now'))
    """

    db_manager.execute_update(update_query, (key, serialized_value))
