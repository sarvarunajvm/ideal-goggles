"""Configuration endpoints for Ideal Goggles API."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from ..core.logging_config import get_logger
from ..core.utils import get_default_photo_roots, validate_path
from ..db.connection import get_database_manager
from ..db.utils import DatabaseHelper

logger = get_logger(__name__)
router = APIRouter()


class ConfigurationResponse(BaseModel):
    """Configuration response model."""

    roots: list[str] = Field(description="Configured root folders")
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
            try:
                path = validate_path(root_path, must_exist=True, must_be_dir=True)
                validated_roots.append(str(path))
            except ValueError as e:
                error_msg = f"Invalid root path: {e}"
                raise ValueError(error_msg)

        return validated_roots


class UpdateConfigRequest(BaseModel):
    """Request model for updating configuration."""

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
            roots=(config_data.get("roots") or get_default_photo_roots()),
            face_search_enabled=config_data.get("face_search_enabled", True),
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

        # Get current roots before updating
        config_data = _get_config_from_db(db_manager)
        old_roots = config_data.get("roots", [])

        # Convert to absolute paths
        absolute_roots = []
        for root_path in request.roots:
            abs_path = str(Path(root_path).absolute())
            absolute_roots.append(abs_path)

        # Find removed roots (paths that were in old but not in new)
        removed_roots = [root for root in old_roots if root not in absolute_roots]

        # Clear photos from removed roots
        if removed_roots:
            for removed_root in removed_roots:
                # Delete photos from removed root paths
                delete_query = """
                    DELETE FROM photos
                    WHERE path LIKE ? || '%'
                """
                db_manager.execute_update(delete_query, (removed_root,))

                # Also delete associated faces
                delete_faces_query = """
                    DELETE FROM faces
                    WHERE file_id NOT IN (SELECT id FROM photos)
                """
                db_manager.execute_update(delete_faces_query)

            # Reset indexing state if roots changed
            # Note: IndexingStateManager doesn't exist, state reset not implemented yet
            import logging

            temp_logger = logging.getLogger(__name__)
            temp_logger.info("Root folders changed - indexing state should be reset")

        # Update configuration in database
        _update_config_in_db(db_manager, "roots", absolute_roots)

        # Log the configuration change
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Root folders updated: {absolute_roots}")
        if removed_roots:
            logger.info(f"Removed roots and cleared associated photos: {removed_roots}")

        return {
            "message": "Root folders updated successfully",
            "roots": absolute_roots,
            "removed_roots": removed_roots if removed_roots else [],
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
        "face_search_enabled": True,
        "semantic_search_enabled": True,
        "batch_size": 50,
        "thumbnail_size": "medium",
        "thumbnail_quality": 85,
        "index_version": "1",
        "supported_image_formats": [
            ".jpg",
            ".jpeg",
            ".png",
            ".tiff",
            ".tif",
            ".webp",
            ".heic",
            ".heif",
        ],
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
            "face_search_enabled": True,
            "semantic_search_enabled": True,
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
        return {"roots": []}.get(key, [])


def _parse_boolean_setting(value: str) -> bool:
    """Parse boolean setting."""
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes")


def _parse_int_setting(key: str, value: str) -> int:
    """Parse integer setting with fallbacks."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return {"thumbnail_quality": 85}.get(key, 0)


def _parse_setting_value(key: str, value: str) -> Any:
    """Parse setting value based on key type."""
    if key == "roots":
        parsed = _parse_json_setting(key, value)
        if key == "roots" and (not isinstance(parsed, list) or not parsed):
            return get_default_photo_roots()
        return parsed
    if key in ["face_search_enabled", "semantic_search_enabled"]:
        return _parse_boolean_setting(value)
    if key in ["thumbnail_quality", "batch_size"]:
        return _parse_int_setting(key, value)
    if key == "thumbnail_size":
        return value
    return value


def _get_config_defaults() -> dict[str, Any]:
    """Get default configuration values."""
    return {
        "roots": get_default_photo_roots(),
        "face_search_enabled": True,
        "semantic_search_enabled": True,
        "batch_size": 50,
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

        # If roots missing or empty, apply computed defaults
        if not settings_dict.get("roots"):
            settings_dict["roots"] = _get_config_defaults().get("roots", [])
        return settings_dict

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception(f"Failed to get configuration from database: {e}")

        # Return defaults on error
        return {
            "roots": get_default_photo_roots(),
            "face_search_enabled": True,
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
