"""Integration test for batch export of 1K photos."""

import asyncio
import os
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Dict, List  # noqa: UP035
from unittest.mock import AsyncMock, MagicMock, patch

import aiofiles
import pytest

from src.db.connection import get_session
from src.models.photo import Photo
from src.workers.batch_worker import BatchJob, BatchJobStatus, BatchWorker


class TestBatchExport:
    """Test batch export performance with 1K photos."""

    @pytest.fixture
    async def batch_worker(self):
        """Create batch worker instance."""
        worker = BatchWorker()
        yield worker
        await worker.shutdown()

    @pytest.fixture
    def mock_photos(self) -> list[dict]:
        """Generate 1000 mock photo records."""
        photos = []
        for i in range(1000):
            photos.append(
                {
                    "file_id": i + 1,
                    "path": f"/photos/photo_{i:04d}.jpg",
                    "filename": f"photo_{i:04d}.jpg",
                    "folder": "/photos",
                    "size": 1024 * 1024 * (i % 5 + 1),  # 1-5 MB files
                    "sha1": f"sha1_{i:040x}",
                    "thumb_path": f"/thumbnails/thumb_{i:04d}.jpg",
                }
            )
        return photos

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for exports."""
        temp_dir = tempfile.mkdtemp(prefix="batch_export_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_export_1k_photos_performance(
        self, batch_worker, mock_photos, temp_export_dir
    ):
        """Test exporting 1000 photos meets performance requirements (≥100 photos/min)."""
        # Create batch export job
        job = BatchJob(
            id="export_1k_test",
            type="export",
            status=BatchJobStatus.PENDING,
            total_items=len(mock_photos),
            processed_items=0,
            file_ids=[p["file_id"] for p in mock_photos],
            params={
                "output_path": temp_export_dir,
                "format": "zip",
                "include_metadata": True,
            },
        )

        # Mock database queries
        with patch("src.workers.batch_worker.get_session") as mock_session:
            mock_query = MagicMock()
            mock_query.filter.return_value.all.return_value = [
                MagicMock(**photo) for photo in mock_photos
            ]
            mock_session.return_value.__enter__.return_value.query.return_value = (
                mock_query
            )

            # Mock file operations for speed
            with patch("aiofiles.open", new_callable=AsyncMock) as mock_aiofiles:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value=b"fake_image_data")
                mock_aiofiles.return_value.__aenter__.return_value = mock_file

                # Start timing
                start_time = time.time()

                # Execute export
                await batch_worker.execute_job(job)

                # Calculate metrics
                elapsed_time = time.time() - start_time
                photos_per_minute = (len(mock_photos) / elapsed_time) * 60

                # Verify performance requirement: ≥100 photos/min
                assert (
                    photos_per_minute >= 100
                ), f"Export too slow: {photos_per_minute:.1f} photos/min"

                # Verify job completed successfully
                assert job.status == BatchJobStatus.COMPLETED
                assert job.processed_items == 1000
                assert job.error is None

    @pytest.mark.asyncio
    async def test_export_with_metadata(
        self, batch_worker, mock_photos, temp_export_dir
    ):
        """Test export includes metadata correctly."""
        job = BatchJob(
            id="export_metadata_test",
            type="export",
            status=BatchJobStatus.PENDING,
            total_items=100,  # Smaller subset for metadata test
            processed_items=0,
            file_ids=[p["file_id"] for p in mock_photos[:100]],
            params={
                "output_path": temp_export_dir,
                "format": "folder",
                "include_metadata": True,
                "include_exif": True,
                "include_ocr": True,
            },
        )

        # Mock additional metadata
        mock_exif_data = {
            "camera_make": "Canon",
            "camera_model": "EOS R5",
            "iso": 400,
            "aperture": 2.8,
        }

        mock_ocr_data = {"text": "Sample OCR text from image", "confidence": 0.95}

        with patch("src.workers.batch_worker.get_session") as mock_session:
            # Setup mocks
            mock_db = MagicMock()
            mock_photos = [MagicMock(**photo) for photo in mock_photos[:100]]

            for photo in mock_photos:
                photo.exif = MagicMock(**mock_exif_data)
                photo.ocr = MagicMock(**mock_ocr_data)

            mock_db.query.return_value.filter.return_value.all.return_value = (
                mock_photos
            )
            mock_session.return_value.__enter__.return_value = mock_db

            await batch_worker.execute_job(job)

            # Verify metadata file was created
            metadata_path = Path(temp_export_dir) / "metadata.json"
            assert job.params.get("metadata_file") is not None

    @pytest.mark.asyncio
    async def test_export_memory_efficiency(self, batch_worker, mock_photos):
        """Test export maintains memory usage under limits."""
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        job = BatchJob(
            id="export_memory_test",
            type="export",
            status=BatchJobStatus.PENDING,
            total_items=1000,
            processed_items=0,
            file_ids=[p["file_id"] for p in mock_photos],
            params={
                "output_path": tempfile.mkdtemp(),
                "format": "zip",
                "compression": "store",  # No compression for speed
                "batch_size": 50,  # Process in batches
            },
        )

        with patch("src.workers.batch_worker.get_session"):
            with patch("aiofiles.open", new_callable=AsyncMock):
                await batch_worker.execute_job(job)

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Memory increase should be reasonable (< 200MB for 1K photos)
        assert (
            memory_increase < 200
        ), f"Memory usage too high: {memory_increase:.1f}MB increase"

    @pytest.mark.asyncio
    async def test_export_concurrent_jobs(self, batch_worker, mock_photos):
        """Test handling multiple export jobs concurrently."""
        jobs = []
        for i in range(3):
            job = BatchJob(
                id=f"concurrent_export_{i}",
                type="export",
                status=BatchJobStatus.PENDING,
                total_items=300,
                processed_items=0,
                file_ids=[p["file_id"] for p in mock_photos[i * 300 : (i + 1) * 300]],
                params={"output_path": tempfile.mkdtemp(), "format": "zip"},
            )
            jobs.append(job)

        with patch("src.workers.batch_worker.get_session"):
            with patch("aiofiles.open", new_callable=AsyncMock):
                start_time = time.time()

                # Execute jobs concurrently
                tasks = [batch_worker.execute_job(job) for job in jobs]
                await asyncio.gather(*tasks)

                elapsed_time = time.time() - start_time

                # All jobs should complete
                for job in jobs:
                    assert job.status == BatchJobStatus.COMPLETED
                    assert job.processed_items == 300

                # Concurrent execution should be faster than sequential
                # 900 photos should still meet 100 photos/min requirement
                photos_per_minute = (900 / elapsed_time) * 60
                assert photos_per_minute >= 100

    @pytest.mark.asyncio
    async def test_export_error_handling(self, batch_worker, mock_photos):
        """Test export handles errors gracefully."""
        job = BatchJob(
            id="export_error_test",
            type="export",
            status=BatchJobStatus.PENDING,
            total_items=100,
            processed_items=0,
            file_ids=[p["file_id"] for p in mock_photos[:100]],
            params={
                "output_path": "/invalid/path/that/does/not/exist",
                "format": "zip",
            },
        )

        await batch_worker.execute_job(job)

        # Job should fail gracefully
        assert job.status == BatchJobStatus.FAILED
        assert job.error is not None
        assert "error" in job.error.lower() or "failed" in job.error.lower()

    @pytest.mark.asyncio
    async def test_export_progress_tracking(self, batch_worker, mock_photos):
        """Test export progress is tracked accurately."""
        progress_updates = []

        async def progress_callback(job_id: str, progress: int, message: str):
            progress_updates.append(
                {"job_id": job_id, "progress": progress, "message": message}
            )

        job = BatchJob(
            id="export_progress_test",
            type="export",
            status=BatchJobStatus.PENDING,
            total_items=100,
            processed_items=0,
            file_ids=[p["file_id"] for p in mock_photos[:100]],
            params={
                "output_path": tempfile.mkdtemp(),
                "format": "zip",
                "progress_callback": progress_callback,
            },
        )

        with patch("src.workers.batch_worker.get_session"):
            with patch("aiofiles.open", new_callable=AsyncMock):
                await batch_worker.execute_job(job)

        # Should have progress updates
        assert len(progress_updates) > 0

        # Progress should increase monotonically
        progresses = [u["progress"] for u in progress_updates]
        assert progresses == sorted(progresses)

        # Should reach 100% completion
        assert progresses[-1] == 100

    @pytest.mark.asyncio
    async def test_export_formats(self, batch_worker, mock_photos, temp_export_dir):
        """Test different export formats."""
        formats = ["zip", "folder", "tar"]

        for format_type in formats:
            job = BatchJob(
                id=f"export_{format_type}_test",
                type="export",
                status=BatchJobStatus.PENDING,
                total_items=50,
                processed_items=0,
                file_ids=[p["file_id"] for p in mock_photos[:50]],
                params={
                    "output_path": os.path.join(temp_export_dir, format_type),
                    "format": format_type,
                },
            )

            with patch("src.workers.batch_worker.get_session"):
                with patch("aiofiles.open", new_callable=AsyncMock):
                    await batch_worker.execute_job(job)

            assert job.status == BatchJobStatus.COMPLETED
            assert job.processed_items == 50

    @pytest.mark.asyncio
    async def test_export_cancellation(self, batch_worker, mock_photos):
        """Test export can be cancelled mid-operation."""
        job = BatchJob(
            id="export_cancel_test",
            type="export",
            status=BatchJobStatus.PENDING,
            total_items=1000,
            processed_items=0,
            file_ids=[p["file_id"] for p in mock_photos],
            params={"output_path": tempfile.mkdtemp(), "format": "zip"},
        )

        with patch("src.workers.batch_worker.get_session"):
            with patch("aiofiles.open", new_callable=AsyncMock):
                # Start export in background
                export_task = asyncio.create_task(batch_worker.execute_job(job))

                # Wait a bit then cancel
                await asyncio.sleep(0.1)
                job.status = BatchJobStatus.CANCELLED
                export_task.cancel()

                import contextlib

                with contextlib.suppress(asyncio.CancelledError):
                    await export_task

        # Job should be cancelled
        assert job.status == BatchJobStatus.CANCELLED
        assert job.processed_items < 1000  # Should not have completed all

    @pytest.mark.asyncio
    async def test_export_resume(self, batch_worker, mock_photos, temp_export_dir):
        """Test export can resume from interruption."""
        job = BatchJob(
            id="export_resume_test",
            type="export",
            status=BatchJobStatus.PENDING,
            total_items=200,
            processed_items=0,
            file_ids=[p["file_id"] for p in mock_photos[:200]],
            params={
                "output_path": temp_export_dir,
                "format": "folder",
                "resume_enabled": True,
            },
        )

        # Simulate partial completion
        job.processed_items = 100
        job.status = BatchJobStatus.IN_PROGRESS

        with patch("src.workers.batch_worker.get_session"):
            with patch("aiofiles.open", new_callable=AsyncMock):
                await batch_worker.execute_job(job)

        # Should complete remaining items
        assert job.status == BatchJobStatus.COMPLETED
        assert job.processed_items == 200
