"""Unit tests for unified API response models."""

from datetime import datetime

import pytest

from src.api.models import (
    BaseResponse,
    BatchOperationRequest,
    BatchOperationResponse,
    ConfigItem,
    DependencyStatus,
    ErrorResponse,
    HealthStatus,
    IndexingStatus,
    PaginatedResponse,
    PersonModel,
    PhotoItem,
    SearchResponse,
    SearchResultItem,
    StatusResponse,
)


class TestBaseResponse:
    """Test BaseResponse model."""

    def test_base_response_creation_defaults(self):
        """Test creating BaseResponse with defaults."""
        response = BaseResponse()

        assert response.success is True
        assert response.message is None
        assert isinstance(response.timestamp, datetime)

    def test_base_response_creation_custom(self):
        """Test creating BaseResponse with custom values."""
        timestamp = datetime(2022, 1, 1, 12, 0, 0)
        response = BaseResponse(
            success=False,
            message="Custom message",
            timestamp=timestamp,
        )

        assert response.success is False
        assert response.message == "Custom message"
        assert response.timestamp == timestamp

    def test_base_response_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated."""
        before = datetime.now()
        response = BaseResponse()
        after = datetime.now()

        assert before <= response.timestamp <= after


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_error_response_creation_minimal(self):
        """Test creating ErrorResponse with minimal fields."""
        response = ErrorResponse(error="Something went wrong")

        assert response.success is False  # Default for ErrorResponse
        assert response.error == "Something went wrong"
        assert response.detail is None
        assert response.request_id is None

    def test_error_response_creation_full(self):
        """Test creating ErrorResponse with all fields."""
        response = ErrorResponse(
            error="Not found",
            detail="The requested resource was not found",
            request_id="req-123",
            message="Error occurred",
        )

        assert response.success is False
        assert response.error == "Not found"
        assert response.detail == "The requested resource was not found"
        assert response.request_id == "req-123"
        assert response.message == "Error occurred"

    def test_error_response_success_always_false(self):
        """Test that success is always False for ErrorResponse."""
        response = ErrorResponse(error="Error")

        assert response.success is False


class TestStatusResponse:
    """Test StatusResponse model."""

    def test_status_response_creation_minimal(self):
        """Test creating StatusResponse with minimal fields."""
        response = StatusResponse(status="running")

        assert response.status == "running"
        assert response.details is None
        assert response.success is True

    def test_status_response_creation_with_details(self):
        """Test creating StatusResponse with details."""
        response = StatusResponse(
            status="indexing",
            details={"progress": 50, "total": 100},
        )

        assert response.status == "indexing"
        assert response.details["progress"] == 50
        assert response.details["total"] == 100


class TestPhotoItem:
    """Test PhotoItem model."""

    def test_photo_item_creation_minimal(self):
        """Test creating PhotoItem with minimal required fields."""
        photo = PhotoItem(
            file_id=1,
            path="/photos/test.jpg",
            folder="/photos",
            filename="test.jpg",
        )

        assert photo.file_id == 1
        assert photo.path == "/photos/test.jpg"
        assert photo.folder == "/photos"
        assert photo.filename == "test.jpg"
        assert photo.size is None
        assert photo.thumb_path is None
        assert photo.created_ts is None
        assert photo.modified_ts is None
        assert photo.indexed_at is None
        assert photo.shot_dt is None

    def test_photo_item_creation_full(self):
        """Test creating PhotoItem with all fields."""
        created = datetime(2022, 1, 1, 10, 0, 0)
        modified = datetime(2022, 1, 2, 10, 0, 0)
        indexed = datetime(2022, 1, 3, 10, 0, 0)
        shot = datetime(2021, 12, 25, 12, 0, 0)

        photo = PhotoItem(
            file_id=123,
            path="/photos/vacation/beach.jpg",
            folder="/photos/vacation",
            filename="beach.jpg",
            size=2048576,
            thumb_path="/cache/thumbs/beach.webp",
            created_ts=created,
            modified_ts=modified,
            indexed_at=indexed,
            shot_dt=shot,
        )

        assert photo.file_id == 123
        assert photo.path == "/photos/vacation/beach.jpg"
        assert photo.folder == "/photos/vacation"
        assert photo.filename == "beach.jpg"
        assert photo.size == 2048576
        assert photo.thumb_path == "/cache/thumbs/beach.webp"
        assert photo.created_ts == created
        assert photo.modified_ts == modified
        assert photo.indexed_at == indexed
        assert photo.shot_dt == shot


class TestSearchResultItem:
    """Test SearchResultItem model."""

    def test_search_result_item_inherits_from_photo_item(self):
        """Test that SearchResultItem inherits from PhotoItem."""
        result = SearchResultItem(
            file_id=1,
            path="/photos/test.jpg",
            folder="/photos",
            filename="test.jpg",
            score=0.95,
        )

        assert isinstance(result, PhotoItem)
        assert result.file_id == 1
        assert result.path == "/photos/test.jpg"

    def test_search_result_item_creation_minimal(self):
        """Test creating SearchResultItem with minimal fields."""
        result = SearchResultItem(
            file_id=1,
            path="/photos/test.jpg",
            folder="/photos",
            filename="test.jpg",
            score=0.85,
        )

        assert result.score == 0.85
        assert result.badges == []  # Default empty list
        assert result.snippet is None

    def test_search_result_item_creation_full(self):
        """Test creating SearchResultItem with all fields."""
        result = SearchResultItem(
            file_id=1,
            path="/photos/test.jpg",
            folder="/photos",
            filename="test.jpg",
            score=0.95,
            badges=["OCR", "FACES"],
            snippet="Found text in image",
            size=1024,
        )

        assert result.score == 0.95
        assert "OCR" in result.badges
        assert "FACES" in result.badges
        assert result.snippet == "Found text in image"
        assert result.size == 1024

    def test_search_result_item_score_range(self):
        """Test that score can be in valid range."""
        result_low = SearchResultItem(
            file_id=1,
            path="/test.jpg",
            folder="/",
            filename="test.jpg",
            score=0.0,
        )
        result_high = SearchResultItem(
            file_id=2,
            path="/test2.jpg",
            folder="/",
            filename="test2.jpg",
            score=1.0,
        )

        assert result_low.score == 0.0
        assert result_high.score == 1.0


class TestPaginatedResponse:
    """Test PaginatedResponse model."""

    def test_paginated_response_creation(self):
        """Test creating PaginatedResponse."""
        response = PaginatedResponse(
            total=100,
            limit=20,
            offset=40,
            has_more=True,
        )

        assert response.total == 100
        assert response.limit == 20
        assert response.offset == 40
        assert response.has_more is True
        assert response.success is True

    def test_paginated_response_first_page(self):
        """Test PaginatedResponse for first page."""
        response = PaginatedResponse(
            total=50,
            limit=20,
            offset=0,
            has_more=True,
        )

        assert response.offset == 0
        assert response.has_more is True

    def test_paginated_response_last_page(self):
        """Test PaginatedResponse for last page."""
        response = PaginatedResponse(
            total=50,
            limit=20,
            offset=40,
            has_more=False,
        )

        assert response.offset == 40
        assert response.has_more is False

    def test_paginated_response_no_results(self):
        """Test PaginatedResponse with no results."""
        response = PaginatedResponse(
            total=0,
            limit=20,
            offset=0,
            has_more=False,
        )

        assert response.total == 0
        assert response.has_more is False


class TestSearchResponse:
    """Test SearchResponse model."""

    def test_search_response_creation_minimal(self):
        """Test creating SearchResponse with minimal fields."""
        response = SearchResponse(
            query="test query",
            items=[],
            took_ms=100,
            total=0,
            limit=20,
            offset=0,
            has_more=False,
        )

        assert response.query == "test query"
        assert len(response.items) == 0
        assert response.took_ms == 100
        assert response.total == 0

    def test_search_response_creation_with_results(self):
        """Test creating SearchResponse with results."""
        items = [
            SearchResultItem(
                file_id=1,
                path="/photos/test1.jpg",
                folder="/photos",
                filename="test1.jpg",
                score=0.95,
                badges=["OCR"],
            ),
            SearchResultItem(
                file_id=2,
                path="/photos/test2.jpg",
                folder="/photos",
                filename="test2.jpg",
                score=0.85,
                badges=["FACES"],
            ),
        ]

        response = SearchResponse(
            query="vacation photos",
            items=items,
            took_ms=250,
            total=2,
            limit=20,
            offset=0,
            has_more=False,
        )

        assert response.query == "vacation photos"
        assert len(response.items) == 2
        assert response.items[0].score == 0.95
        assert response.items[1].score == 0.85
        assert response.took_ms == 250

    def test_search_response_inherits_pagination(self):
        """Test that SearchResponse inherits pagination fields."""
        response = SearchResponse(
            query="test",
            items=[],
            took_ms=50,
            total=100,
            limit=20,
            offset=20,
            has_more=True,
        )

        assert isinstance(response, PaginatedResponse)
        assert response.total == 100
        assert response.limit == 20
        assert response.offset == 20
        assert response.has_more is True


class TestIndexingStatus:
    """Test IndexingStatus model."""

    def test_indexing_status_idle(self):
        """Test IndexingStatus in idle state."""
        status = IndexingStatus(status="idle")

        assert status.status == "idle"
        assert status.phase is None
        assert status.progress is None
        assert status.started_at is None
        assert status.errors == []

    def test_indexing_status_indexing(self):
        """Test IndexingStatus during indexing."""
        started = datetime(2022, 1, 1, 10, 0, 0)
        status = IndexingStatus(
            status="indexing",
            phase="scanning",
            progress={"current": 50, "total": 100, "percent": 50},
            started_at=started,
        )

        assert status.status == "indexing"
        assert status.phase == "scanning"
        assert status.progress["current"] == 50
        assert status.progress["percent"] == 50
        assert status.started_at == started

    def test_indexing_status_error(self):
        """Test IndexingStatus with errors."""
        status = IndexingStatus(
            status="error",
            errors=["Database connection failed", "Permission denied"],
        )

        assert status.status == "error"
        assert len(status.errors) == 2
        assert "Database connection failed" in status.errors

    def test_indexing_status_completed_with_errors(self):
        """Test IndexingStatus completed with some errors."""
        status = IndexingStatus(
            status="completed",
            phase="complete",
            errors=["Failed to index 1 file"],
        )

        assert status.status == "completed"
        assert len(status.errors) == 1


class TestConfigItem:
    """Test ConfigItem model."""

    def test_config_item_minimal(self):
        """Test creating ConfigItem with minimal fields."""
        config = ConfigItem(key="setting_name", value="setting_value")

        assert config.key == "setting_name"
        assert config.value == "setting_value"
        assert config.description is None
        assert config.updated_at is None

    def test_config_item_full(self):
        """Test creating ConfigItem with all fields."""
        updated = datetime(2022, 1, 1, 10, 0, 0)
        config = ConfigItem(
            key="max_results",
            value=100,
            description="Maximum number of search results",
            updated_at=updated,
        )

        assert config.key == "max_results"
        assert config.value == 100
        assert config.description == "Maximum number of search results"
        assert config.updated_at == updated

    def test_config_item_various_value_types(self):
        """Test ConfigItem with various value types."""
        config_str = ConfigItem(key="string_val", value="text")
        config_int = ConfigItem(key="int_val", value=42)
        config_bool = ConfigItem(key="bool_val", value=True)
        config_dict = ConfigItem(key="dict_val", value={"nested": "value"})
        config_list = ConfigItem(key="list_val", value=[1, 2, 3])

        assert config_str.value == "text"
        assert config_int.value == 42
        assert config_bool.value is True
        assert config_dict.value == {"nested": "value"}
        assert config_list.value == [1, 2, 3]


class TestDependencyStatus:
    """Test DependencyStatus model."""

    def test_dependency_status_installed(self):
        """Test DependencyStatus for installed dependency."""
        dep = DependencyStatus(
            name="PIL",
            installed=True,
            version="9.0.0",
            required=True,
        )

        assert dep.name == "PIL"
        assert dep.installed is True
        assert dep.version == "9.0.0"
        assert dep.required is True
        assert dep.error is None

    def test_dependency_status_not_installed(self):
        """Test DependencyStatus for missing dependency."""
        dep = DependencyStatus(
            name="tesseract",
            installed=False,
            required=False,
            error="Command not found",
        )

        assert dep.name == "tesseract"
        assert dep.installed is False
        assert dep.version is None
        assert dep.required is False
        assert dep.error == "Command not found"

    def test_dependency_status_optional_dependency(self):
        """Test DependencyStatus for optional dependency."""
        dep = DependencyStatus(
            name="optional-lib",
            installed=False,
            required=False,
        )

        assert dep.required is False
        assert dep.installed is False


class TestHealthStatus:
    """Test HealthStatus model."""

    def test_health_status_minimal(self):
        """Test creating HealthStatus with minimal fields."""
        health = HealthStatus(
            service="ideal-goggles",
            status="healthy",
            version="1.0.0",
        )

        assert health.service == "ideal-goggles"
        assert health.status == "healthy"
        assert health.version == "1.0.0"
        assert health.uptime_seconds is None
        assert health.checks == {}
        assert health.metrics is None

    def test_health_status_full(self):
        """Test creating HealthStatus with all fields."""
        health = HealthStatus(
            service="ideal-goggles-api",
            status="healthy",
            version="1.0.8",
            uptime_seconds=3600,
            checks={"database": True, "storage": True},
            metrics={"requests_per_second": 10, "response_time_ms": 50},
        )

        assert health.service == "ideal-goggles-api"
        assert health.status == "healthy"
        assert health.version == "1.0.8"
        assert health.uptime_seconds == 3600
        assert health.checks["database"] is True
        assert health.checks["storage"] is True
        assert health.metrics["requests_per_second"] == 10

    def test_health_status_degraded(self):
        """Test HealthStatus in degraded state."""
        health = HealthStatus(
            service="ideal-goggles",
            status="degraded",
            version="1.0.0",
            checks={"database": True, "cache": False},
        )

        assert health.status == "degraded"
        assert health.checks["database"] is True
        assert health.checks["cache"] is False

    def test_health_status_unhealthy(self):
        """Test HealthStatus in unhealthy state."""
        health = HealthStatus(
            service="ideal-goggles",
            status="unhealthy",
            version="1.0.0",
            checks={"database": False},
        )

        assert health.status == "unhealthy"
        assert health.checks["database"] is False


class TestBatchOperationRequest:
    """Test BatchOperationRequest model."""

    def test_batch_operation_request_minimal(self):
        """Test creating BatchOperationRequest with minimal fields."""
        request = BatchOperationRequest(
            operation="delete",
            items=[1, 2, 3],
        )

        assert request.operation == "delete"
        assert request.items == [1, 2, 3]
        assert request.options is None

    def test_batch_operation_request_with_options(self):
        """Test creating BatchOperationRequest with options."""
        request = BatchOperationRequest(
            operation="export",
            items=[10, 20, 30],
            options={"format": "jpg", "quality": 90},
        )

        assert request.operation == "export"
        assert len(request.items) == 3
        assert request.options["format"] == "jpg"
        assert request.options["quality"] == 90

    def test_batch_operation_request_empty_items(self):
        """Test BatchOperationRequest with empty items list."""
        request = BatchOperationRequest(
            operation="tag",
            items=[],
        )

        assert len(request.items) == 0


class TestBatchOperationResponse:
    """Test BatchOperationResponse model."""

    def test_batch_operation_response_minimal(self):
        """Test creating BatchOperationResponse with minimal fields."""
        response = BatchOperationResponse(
            operation="delete",
            total=10,
            processed=10,
            failed=0,
        )

        assert response.operation == "delete"
        assert response.total == 10
        assert response.processed == 10
        assert response.failed == 0
        assert response.errors is None
        assert response.results is None
        assert response.success is True

    def test_batch_operation_response_with_failures(self):
        """Test creating BatchOperationResponse with failures."""
        response = BatchOperationResponse(
            operation="export",
            total=100,
            processed=95,
            failed=5,
            errors=["File not found", "Permission denied"],
        )

        assert response.total == 100
        assert response.processed == 95
        assert response.failed == 5
        assert len(response.errors) == 2

    def test_batch_operation_response_with_results(self):
        """Test creating BatchOperationResponse with results."""
        response = BatchOperationResponse(
            operation="tag",
            total=3,
            processed=3,
            failed=0,
            results=[
                {"id": 1, "status": "success"},
                {"id": 2, "status": "success"},
                {"id": 3, "status": "success"},
            ],
        )

        assert response.total == 3
        assert len(response.results) == 3
        assert response.results[0]["status"] == "success"

    def test_batch_operation_response_partial_success(self):
        """Test BatchOperationResponse for partial success."""
        response = BatchOperationResponse(
            operation="delete",
            total=10,
            processed=8,
            failed=2,
            errors=["File 9 not found", "File 10 locked"],
            results=[{"processed": 8}],
        )

        assert response.processed == 8
        assert response.failed == 2
        assert response.processed + response.failed == response.total


class TestPersonModel:
    """Test PersonModel model."""

    def test_person_model_minimal(self):
        """Test creating PersonModel with minimal fields."""
        person = PersonModel(name="John Doe")

        assert person.id is None
        assert person.name == "John Doe"
        assert person.sample_count == 0  # Default
        assert person.created_at is None
        assert person.active is True  # Default

    def test_person_model_full(self):
        """Test creating PersonModel with all fields."""
        created = datetime(2022, 1, 1, 10, 0, 0)
        person = PersonModel(
            id=123,
            name="Jane Smith",
            sample_count=5,
            created_at=created,
            active=True,
        )

        assert person.id == 123
        assert person.name == "Jane Smith"
        assert person.sample_count == 5
        assert person.created_at == created
        assert person.active is True

    def test_person_model_inactive(self):
        """Test creating inactive PersonModel."""
        person = PersonModel(
            id=456,
            name="Inactive User",
            active=False,
        )

        assert person.id == 456
        assert person.active is False

    def test_person_model_with_samples(self):
        """Test PersonModel with sample photos."""
        person = PersonModel(
            name="Person with Photos",
            sample_count=10,
        )

        assert person.sample_count == 10


class TestModelsExports:
    """Test that all models are exported in __all__."""

    def test_all_exports_exist(self):
        """Test that __all__ contains all expected models."""
        from src.api.models import __all__

        expected_models = [
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

        for model in expected_models:
            assert model in __all__, f"{model} not in __all__"

    def test_all_exports_count(self):
        """Test that __all__ has correct number of exports."""
        from src.api.models import __all__

        assert len(__all__) == 14


class TestModelSerialization:
    """Test model serialization to dict/json."""

    def test_photo_item_serialization(self):
        """Test PhotoItem can be serialized to dict."""
        photo = PhotoItem(
            file_id=1,
            path="/test.jpg",
            folder="/",
            filename="test.jpg",
            size=1024,
        )

        data = photo.dict()
        assert data["file_id"] == 1
        assert data["path"] == "/test.jpg"
        assert data["size"] == 1024

    def test_search_response_serialization(self):
        """Test SearchResponse can be serialized to dict."""
        response = SearchResponse(
            query="test",
            items=[],
            took_ms=100,
            total=0,
            limit=20,
            offset=0,
            has_more=False,
        )

        data = response.dict()
        assert data["query"] == "test"
        assert data["took_ms"] == 100
        assert data["total"] == 0

    def test_error_response_serialization(self):
        """Test ErrorResponse can be serialized to dict."""
        response = ErrorResponse(
            error="Not found",
            detail="Resource not found",
            request_id="req-123",
        )

        data = response.dict()
        assert data["error"] == "Not found"
        assert data["detail"] == "Resource not found"
        assert data["success"] is False
