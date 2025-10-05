"""Unified API response models for Ideal Goggles."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(default=True, description="Whether the operation succeeded")
    message: str | None = Field(default=None, description="Optional message")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )


class ErrorResponse(BaseResponse):
    """Standard error response model."""

    success: bool = Field(default=False)
    error: str = Field(description="Error message")
    detail: str | None = Field(default=None, description="Detailed error information")
    request_id: str | None = Field(default=None, description="Request ID for tracing")


class StatusResponse(BaseResponse):
    """Standard status response model."""

    status: str = Field(description="Current status")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional status details"
    )


class PhotoItem(BaseModel):
    """Standard photo item model."""

    file_id: int = Field(description="Database ID")
    path: str = Field(description="Absolute file path")
    folder: str = Field(description="Parent folder")
    filename: str = Field(description="File name")
    size: int | None = Field(default=None, description="File size in bytes")
    thumb_path: str | None = Field(default=None, description="Thumbnail path")
    created_ts: datetime | None = Field(default=None, description="File creation time")
    modified_ts: datetime | None = Field(
        default=None, description="File modification time"
    )
    indexed_at: datetime | None = Field(default=None, description="Indexing timestamp")
    shot_dt: datetime | None = Field(
        default=None, description="Photo capture time from EXIF"
    )


class SearchResultItem(PhotoItem):
    """Search result item with additional metadata."""

    score: float = Field(description="Relevance/similarity score (0.0-1.0)")
    badges: list[str] = Field(default_factory=list, description="Match type indicators")
    snippet: str | None = Field(default=None, description="Text excerpt for context")


class PaginatedResponse(BaseResponse):
    """Base model for paginated responses."""

    total: int = Field(description="Total number of items")
    limit: int = Field(description="Items per page")
    offset: int = Field(description="Current offset")
    has_more: bool = Field(description="Whether more items exist")


class SearchResponse(PaginatedResponse):
    """Standard search response model."""

    query: str = Field(description="Search query")
    items: list[SearchResultItem] = Field(description="Search results")
    took_ms: int = Field(description="Search execution time in milliseconds")


class IndexingStatus(BaseModel):
    """Indexing status model."""

    status: str = Field(description="Current status: idle, indexing, error")
    phase: str | None = Field(default=None, description="Current indexing phase")
    progress: dict[str, Any] | None = Field(
        default=None, description="Progress details"
    )
    started_at: datetime | None = Field(default=None, description="Start time")
    errors: list[str] = Field(default_factory=list, description="Error messages")


class ConfigItem(BaseModel):
    """Configuration item model."""

    key: str = Field(description="Configuration key")
    value: Any = Field(description="Configuration value")
    description: str | None = Field(
        default=None, description="Configuration description"
    )
    updated_at: datetime | None = Field(default=None, description="Last update time")


class DependencyStatus(BaseModel):
    """Dependency status model."""

    name: str = Field(description="Dependency name")
    installed: bool = Field(description="Whether dependency is installed")
    version: str | None = Field(default=None, description="Installed version")
    required: bool = Field(default=False, description="Whether dependency is required")
    error: str | None = Field(default=None, description="Error message if check failed")


class HealthStatus(BaseModel):
    """Health check status model."""

    service: str = Field(description="Service name")
    status: str = Field(description="Health status: healthy, degraded, unhealthy")
    version: str = Field(description="Service version")
    uptime_seconds: int | None = Field(default=None, description="Service uptime")
    checks: dict[str, bool] = Field(
        default_factory=dict, description="Health check results"
    )
    metrics: dict[str, Any] | None = Field(default=None, description="Service metrics")


class BatchOperationRequest(BaseModel):
    """Batch operation request model."""

    operation: str = Field(description="Operation type")
    items: list[int] = Field(description="Item IDs to process")
    options: dict[str, Any] | None = Field(
        default=None, description="Operation options"
    )


class BatchOperationResponse(BaseResponse):
    """Batch operation response model."""

    operation: str = Field(description="Operation type")
    total: int = Field(description="Total items to process")
    processed: int = Field(description="Items processed")
    failed: int = Field(description="Items failed")
    errors: list[str] | None = Field(default=None, description="Error messages")
    results: list[dict] | None = Field(default=None, description="Operation results")


class PersonModel(BaseModel):
    """Person model for face search."""

    id: int | None = Field(default=None, description="Person ID")
    name: str = Field(description="Person name")
    sample_count: int = Field(default=0, description="Number of sample photos")
    created_at: datetime | None = Field(default=None, description="Creation time")
    active: bool = Field(default=True, description="Whether person is active")


# Export all models
__all__ = [
    "BaseResponse",
    "BatchOperationRequest",
    "BatchOperationResponse",
    "ConfigItem",
    "DependencyStatus",
    "ErrorResponse",
    "HealthStatus",
    "IndexingStatus",
    "PaginatedResponse",
    "PersonModel",
    "PhotoItem",
    "SearchResponse",
    "SearchResultItem",
    "StatusResponse",
]
