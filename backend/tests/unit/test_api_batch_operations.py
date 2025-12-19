"""Unit tests for batch operations API endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks, HTTPException

import src.api.batch_operations as batch_ops
from src.api.batch_operations import (
    BatchDeleteRequest,
    BatchExportRequest,
    BatchJobStatus,
    BatchTagRequest,
    _jobs,
    cancel_batch_job,
    get_batch_job_status,
    list_batch_jobs,
    start_batch_delete,
    start_batch_export,
    start_batch_tag,
)


@pytest.fixture
def clear_jobs():
    """Clear jobs dictionary before and after each test."""
    _jobs.clear()
    # Disable path validation for tests
    original_skip = batch_ops._SKIP_PATH_VALIDATION
    batch_ops._SKIP_PATH_VALIDATION = True
    yield
    _jobs.clear()
    batch_ops._SKIP_PATH_VALIDATION = original_skip


class TestBatchExportRequest:
    """Test BatchExportRequest model."""

    def test_batch_export_request_creation(self):
        """Test creating BatchExportRequest."""
        request = BatchExportRequest(
            photo_ids=["1", "2", "3"],
            destination="/export/path",
            format="jpg",
            max_dimension=1920,
        )

        assert len(request.photo_ids) == 3
        assert request.destination == "/export/path"
        assert request.format == "jpg"
        assert request.max_dimension == 1920

    def test_batch_export_request_defaults(self):
        """Test BatchExportRequest with defaults."""
        request = BatchExportRequest(
            photo_ids=["1", "2"],
            destination="/export/path",
        )

        assert request.format == "original"
        assert request.max_dimension is None


class TestBatchDeleteRequest:
    """Test BatchDeleteRequest model."""

    def test_batch_delete_request_creation(self):
        """Test creating BatchDeleteRequest."""
        request = BatchDeleteRequest(photo_ids=["1", "2", "3"], permanent=True)

        assert len(request.photo_ids) == 3
        assert request.permanent is True

    def test_batch_delete_request_defaults(self):
        """Test BatchDeleteRequest with defaults."""
        request = BatchDeleteRequest(photo_ids=["1", "2"])

        assert request.permanent is False


class TestBatchTagRequest:
    """Test BatchTagRequest model."""

    def test_batch_tag_request_creation(self):
        """Test creating BatchTagRequest."""
        request = BatchTagRequest(
            photo_ids=["1", "2", "3"], tags=["vacation", "beach"], operation="add"
        )

        assert len(request.photo_ids) == 3
        assert len(request.tags) == 2
        assert request.operation == "add"

    def test_batch_tag_request_defaults(self):
        """Test BatchTagRequest with defaults."""
        request = BatchTagRequest(photo_ids=["1"], tags=["test"])

        assert request.operation == "add"


class TestBatchJobStatus:
    """Test BatchJobStatus model."""

    def test_batch_job_status_creation(self):
        """Test creating BatchJobStatus."""
        status = BatchJobStatus(
            job_id="test-job-123",
            type="export",
            status="processing",
            total_items=100,
            processed_items=50,
            failed_items=2,
            created_at=datetime.now(UTC).isoformat(),
            completed_at=None,
            error=None,
        )

        assert status.job_id == "test-job-123"
        assert status.type == "export"
        assert status.status == "processing"
        assert status.total_items == 100
        assert status.processed_items == 50
        assert status.failed_items == 2


class TestStartBatchExport:
    """Test start_batch_export endpoint."""

    @pytest.mark.asyncio
    async def test_start_batch_export_success(self, clear_jobs):
        """Test successful batch export start."""
        request = BatchExportRequest(
            photo_ids=["1", "2", "3"],
            destination="/export/path",
            format="jpg",
            max_dimension=1920,
        )
        background_tasks = BackgroundTasks()

        with patch("src.api.batch_operations.process_batch_export") as mock_process:
            result = await start_batch_export(request, background_tasks)

            assert "job_id" in result
            assert result["status"] == "pending"
            assert result["job_id"] in _jobs
            assert _jobs[result["job_id"]]["type"] == "export"
            assert _jobs[result["job_id"]]["total_items"] == 3

    @pytest.mark.asyncio
    async def test_start_batch_export_stores_request(self, clear_jobs):
        """Test that export request is stored in job."""
        request = BatchExportRequest(
            photo_ids=["1", "2"],
            destination="/export/path",
        )
        background_tasks = BackgroundTasks()

        with patch("src.api.batch_operations.process_batch_export"):
            result = await start_batch_export(request, background_tasks)

            job = _jobs[result["job_id"]]
            assert job["request"]["destination"] == "/export/path"
            assert job["request"]["format"] == "original"


class TestStartBatchDelete:
    """Test start_batch_delete endpoint."""

    @pytest.mark.asyncio
    async def test_start_batch_delete_success(self, clear_jobs):
        """Test successful batch delete start."""
        request = BatchDeleteRequest(photo_ids=["1", "2", "3"], permanent=False)
        background_tasks = BackgroundTasks()

        with patch("src.api.batch_operations.process_batch_delete") as mock_process:
            result = await start_batch_delete(request, background_tasks)

            assert "job_id" in result
            assert result["status"] == "pending"
            assert result["job_id"] in _jobs
            assert _jobs[result["job_id"]]["type"] == "delete"
            assert _jobs[result["job_id"]]["total_items"] == 3

    @pytest.mark.asyncio
    async def test_start_batch_delete_permanent(self, clear_jobs):
        """Test batch delete with permanent flag."""
        request = BatchDeleteRequest(photo_ids=["1", "2"], permanent=True)
        background_tasks = BackgroundTasks()

        with patch("src.api.batch_operations.process_batch_delete"):
            result = await start_batch_delete(request, background_tasks)

            job = _jobs[result["job_id"]]
            assert job["request"]["permanent"] is True


class TestStartBatchTag:
    """Test start_batch_tag endpoint."""

    @pytest.mark.asyncio
    async def test_start_batch_tag_add_success(self, clear_jobs):
        """Test successful batch tag add."""
        request = BatchTagRequest(
            photo_ids=["1", "2", "3"], tags=["vacation", "beach"], operation="add"
        )
        background_tasks = BackgroundTasks()

        with patch("src.api.batch_operations.process_batch_tag") as mock_process:
            result = await start_batch_tag(request, background_tasks)

            assert "job_id" in result
            assert result["status"] == "pending"
            assert result["job_id"] in _jobs
            assert _jobs[result["job_id"]]["type"] == "tag"
            assert _jobs[result["job_id"]]["total_items"] == 3

    @pytest.mark.asyncio
    async def test_start_batch_tag_remove_operation(self, clear_jobs):
        """Test batch tag with remove operation."""
        request = BatchTagRequest(
            photo_ids=["1", "2"], tags=["old_tag"], operation="remove"
        )
        background_tasks = BackgroundTasks()

        with patch("src.api.batch_operations.process_batch_tag"):
            result = await start_batch_tag(request, background_tasks)

            job = _jobs[result["job_id"]]
            assert job["request"]["operation"] == "remove"

    @pytest.mark.asyncio
    async def test_start_batch_tag_replace_operation(self, clear_jobs):
        """Test batch tag with replace operation."""
        request = BatchTagRequest(
            photo_ids=["1"], tags=["new_tag"], operation="replace"
        )
        background_tasks = BackgroundTasks()

        with patch("src.api.batch_operations.process_batch_tag"):
            result = await start_batch_tag(request, background_tasks)

            job = _jobs[result["job_id"]]
            assert job["request"]["operation"] == "replace"

    @pytest.mark.asyncio
    async def test_start_batch_tag_invalid_operation(self, clear_jobs):
        """Test batch tag with invalid operation."""
        request = BatchTagRequest(photo_ids=["1"], tags=["test"], operation="invalid")
        background_tasks = BackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            await start_batch_tag(request, background_tasks)

        assert exc_info.value.status_code == 400
        assert "Invalid operation" in exc_info.value.detail


class TestGetBatchJobStatus:
    """Test get_batch_job_status endpoint."""

    @pytest.mark.asyncio
    async def test_get_batch_job_status_success(self, clear_jobs):
        """Test getting job status."""
        job_id = "test-job-123"
        _jobs[job_id] = {
            "job_id": job_id,
            "type": "export",
            "status": "processing",
            "total_items": 100,
            "processed_items": 50,
            "failed_items": 2,
            "created_at": datetime.now(UTC).isoformat(),
            "completed_at": None,
            "error": None,
        }

        result = await get_batch_job_status(job_id)

        assert isinstance(result, BatchJobStatus)
        assert result.job_id == job_id
        assert result.status == "processing"
        assert result.total_items == 100
        assert result.processed_items == 50

    @pytest.mark.asyncio
    async def test_get_batch_job_status_not_found(self, clear_jobs):
        """Test getting non-existent job status."""
        with pytest.raises(HTTPException) as exc_info:
            await get_batch_job_status("non-existent-job")

        assert exc_info.value.status_code == 404
        assert "Job not found" in exc_info.value.detail


class TestListBatchJobs:
    """Test list_batch_jobs endpoint."""

    @pytest.mark.asyncio
    async def test_list_batch_jobs_empty(self, clear_jobs):
        """Test listing jobs when empty."""
        result = await list_batch_jobs()

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_batch_jobs_multiple(self, clear_jobs):
        """Test listing multiple jobs."""
        # Create some jobs
        for i in range(3):
            job_id = f"job-{i}"
            _jobs[job_id] = {
                "job_id": job_id,
                "type": "export",
                "status": "completed",
                "total_items": 10,
                "processed_items": 10,
                "failed_items": 0,
                "created_at": datetime.now(UTC).isoformat(),
                "completed_at": datetime.now(UTC).isoformat(),
                "error": None,
            }

        result = await list_batch_jobs()

        assert len(result) == 3
        assert all(isinstance(job, BatchJobStatus) for job in result)

    @pytest.mark.asyncio
    async def test_list_batch_jobs_with_limit(self, clear_jobs):
        """Test listing jobs with limit."""
        # Create more jobs than the limit
        for i in range(60):
            job_id = f"job-{i}"
            _jobs[job_id] = {
                "job_id": job_id,
                "type": "export",
                "status": "completed",
                "total_items": 10,
                "processed_items": 10,
                "failed_items": 0,
                "created_at": datetime.now(UTC).isoformat(),
                "completed_at": None,
                "error": None,
            }

        result = await list_batch_jobs(limit=50)

        assert len(result) == 50

    @pytest.mark.asyncio
    async def test_list_batch_jobs_sorted_by_created_at(self, clear_jobs):
        """Test that jobs are sorted by creation time."""
        import time

        # Create jobs with different timestamps
        for i in range(3):
            job_id = f"job-{i}"
            time.sleep(0.01)  # Small delay to ensure different timestamps
            _jobs[job_id] = {
                "job_id": job_id,
                "type": "export",
                "status": "completed",
                "total_items": 10,
                "processed_items": 10,
                "failed_items": 0,
                "created_at": datetime.now(UTC).isoformat(),
                "completed_at": None,
                "error": None,
            }

        result = await list_batch_jobs()

        # Most recent should be first
        assert result[0].job_id == "job-2"


class TestCancelBatchJob:
    """Test cancel_batch_job endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_batch_job_success(self, clear_jobs):
        """Test successful job cancellation."""
        job_id = "test-job-123"
        _jobs[job_id] = {
            "job_id": job_id,
            "type": "export",
            "status": "processing",
            "total_items": 100,
            "processed_items": 50,
            "failed_items": 0,
            "created_at": datetime.now(UTC).isoformat(),
            "completed_at": None,
            "error": None,
        }

        result = await cancel_batch_job(job_id)

        assert result["job_id"] == job_id
        assert result["status"] == "cancelled"
        assert _jobs[job_id]["status"] == "cancelled"
        assert _jobs[job_id]["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_cancel_batch_job_not_found(self, clear_jobs):
        """Test cancelling non-existent job."""
        with pytest.raises(HTTPException) as exc_info:
            await cancel_batch_job("non-existent-job")

        assert exc_info.value.status_code == 404
        assert "Job not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_cancel_batch_job_already_completed(self, clear_jobs):
        """Test cancelling already completed job."""
        job_id = "test-job-123"
        _jobs[job_id] = {
            "job_id": job_id,
            "type": "export",
            "status": "completed",
            "total_items": 100,
            "processed_items": 100,
            "failed_items": 0,
            "created_at": datetime.now(UTC).isoformat(),
            "completed_at": datetime.now(UTC).isoformat(),
            "error": None,
        }

        with pytest.raises(HTTPException) as exc_info:
            await cancel_batch_job(job_id)

        assert exc_info.value.status_code == 400
        assert "Cannot cancel completed job" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_cancel_batch_job_pending(self, clear_jobs):
        """Test cancelling pending job."""
        job_id = "test-job-123"
        _jobs[job_id] = {
            "job_id": job_id,
            "type": "delete",
            "status": "pending",
            "total_items": 50,
            "processed_items": 0,
            "failed_items": 0,
            "created_at": datetime.now(UTC).isoformat(),
            "completed_at": None,
            "error": None,
        }

        result = await cancel_batch_job(job_id)

        assert result["status"] == "cancelled"
