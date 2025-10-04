"""Unit tests for batch worker operations."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from PIL import Image

from src.models.photo import Photo
from src.workers.batch_worker import (
    process_batch_delete,
    process_batch_export,
    process_batch_tag,
)


@pytest.fixture
def mock_job_store():
    """Create a mock job store."""
    return {
        "test_job_1": {
            "status": "pending",
            "processed_items": 0,
            "failed_items": 0,
        }
    }


@pytest.fixture
def mock_photo():
    """Create a mock photo object."""
    photo = Mock(spec=Photo)
    photo.id = 1
    photo.path = "/tmp/test_photo.jpg"
    photo.size = 1024
    return photo


@pytest.fixture
def temp_test_image():
    """Create a temporary test image."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(f.name, "JPEG")
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        Path(temp_path).unlink()
    except:
        pass


class TestBatchExport:
    """Tests for batch export operations."""

    @pytest.mark.asyncio
    async def test_process_batch_export_no_job_store(self):
        """Test batch export with no job store provided."""
        await process_batch_export(
            job_id="test_job_1",
            photo_ids=["1", "2"],
            destination="/tmp",
            job_store=None,
        )
        # Should complete without error but log warning

    @pytest.mark.asyncio
    async def test_process_batch_export_job_not_found(self):
        """Test batch export when job not found in store."""
        job_store = {}
        await process_batch_export(
            job_id="missing_job",
            photo_ids=["1", "2"],
            destination="/tmp",
            job_store=job_store,
        )
        # Should complete without error but log error

    @pytest.mark.asyncio
    async def test_process_batch_export_original_format(
        self, mock_job_store, temp_test_image
    ):
        """Test batch export in original format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            photo_path = temp_test_image

            with (
                patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr,
                patch("src.workers.batch_worker.Photo") as mock_photo_class,
            ):
                # Setup database mock
                mock_db = MagicMock()
                mock_db_mgr.return_value = mock_db

                # Create photo mock with real file path
                mock_photo = Mock(spec=Photo)
                mock_photo.id = 1
                mock_photo.path = photo_path
                mock_photo_class.from_db_row.return_value = mock_photo

                # Setup query to return photo row
                mock_db.execute_query.return_value = [{"id": 1, "path": photo_path}]

                await process_batch_export(
                    job_id="test_job_1",
                    photo_ids=["1"],
                    destination=temp_dir,
                    export_format="original",
                    job_store=mock_job_store,
                )

                # Verify job status
                assert mock_job_store["test_job_1"]["status"] == "completed"
                assert mock_job_store["test_job_1"]["processed_items"] == 1
                assert "completed_at" in mock_job_store["test_job_1"]

    @pytest.mark.asyncio
    async def test_process_batch_export_convert_format(
        self, mock_job_store, temp_test_image
    ):
        """Test batch export with format conversion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            photo_path = temp_test_image

            with (
                patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr,
                patch("src.workers.batch_worker.Photo") as mock_photo_class,
            ):
                # Setup database mock
                mock_db = MagicMock()
                mock_db_mgr.return_value = mock_db

                # Create photo mock with real file path
                mock_photo = Mock(spec=Photo)
                mock_photo.id = 1
                mock_photo.path = photo_path
                mock_photo_class.from_db_row.return_value = mock_photo

                # Setup query to return photo row
                mock_db.execute_query.return_value = [{"id": 1, "path": photo_path}]

                await process_batch_export(
                    job_id="test_job_1",
                    photo_ids=["1"],
                    destination=temp_dir,
                    export_format="png",
                    max_dimension=50,
                    job_store=mock_job_store,
                )

                # Verify job status
                assert mock_job_store["test_job_1"]["status"] == "completed"
                assert mock_job_store["test_job_1"]["processed_items"] == 1

    @pytest.mark.asyncio
    async def test_process_batch_export_invalid_photo_id(self, mock_job_store):
        """Test batch export with invalid photo ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.workers.batch_worker.get_database_manager"):
                await process_batch_export(
                    job_id="test_job_1",
                    photo_ids=["invalid_id"],
                    destination=temp_dir,
                    job_store=mock_job_store,
                )

                # Should mark as failed
                assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1
                assert mock_job_store["test_job_1"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_process_batch_export_photo_not_found(self, mock_job_store):
        """Test batch export when photo not found in database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
                mock_db = MagicMock()
                mock_db_mgr.return_value = mock_db
                mock_db.execute_query.return_value = []  # No photo found

                await process_batch_export(
                    job_id="test_job_1",
                    photo_ids=["999"],
                    destination=temp_dir,
                    job_store=mock_job_store,
                )

                # Should mark as failed
                assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1
                assert mock_job_store["test_job_1"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_process_batch_export_source_not_found(self, mock_job_store):
        """Test batch export when source file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr,
                patch("src.workers.batch_worker.Photo") as mock_photo_class,
            ):
                mock_db = MagicMock()
                mock_db_mgr.return_value = mock_db

                # Create photo with non-existent path
                mock_photo = Mock(spec=Photo)
                mock_photo.id = 1
                mock_photo.path = "/nonexistent/file.jpg"
                mock_photo_class.from_db_row.return_value = mock_photo

                mock_db.execute_query.return_value = [
                    {"id": 1, "path": "/nonexistent/file.jpg"}
                ]

                await process_batch_export(
                    job_id="test_job_1",
                    photo_ids=["1"],
                    destination=temp_dir,
                    job_store=mock_job_store,
                )

                # Should mark as failed
                assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1
                assert mock_job_store["test_job_1"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_process_batch_export_exception_handling(self, mock_job_store):
        """Test batch export handles exceptions gracefully."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr,
        ):
            mock_db_mgr.side_effect = Exception("Database error")

            await process_batch_export(
                job_id="test_job_1",
                photo_ids=["1"],
                destination=temp_dir,
                job_store=mock_job_store,
            )

            # Should mark job as failed
            assert mock_job_store["test_job_1"]["status"] == "failed"
            assert "error" in mock_job_store["test_job_1"]

    @pytest.mark.asyncio
    async def test_process_batch_export_photo_processing_exception(
        self, mock_job_store, temp_test_image
    ):
        """Test batch export with exception during photo processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            photo_path = temp_test_image

            with (
                patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr,
                patch("src.workers.batch_worker.Photo") as mock_photo_class,
                patch("src.workers.batch_worker.Image") as mock_image,
            ):
                # Setup database mock
                mock_db = MagicMock()
                mock_db_mgr.return_value = mock_db

                # Create photo mock
                mock_photo = Mock(spec=Photo)
                mock_photo.id = 1
                mock_photo.path = photo_path
                mock_photo_class.from_db_row.return_value = mock_photo

                # Setup query to return photo row
                mock_db.execute_query.return_value = [{"id": 1, "path": photo_path}]

                # Make Image.open raise an exception
                mock_image.open.side_effect = Exception("Image processing error")

                await process_batch_export(
                    job_id="test_job_1",
                    photo_ids=["1"],
                    destination=temp_dir,
                    export_format="png",
                    job_store=mock_job_store,
                )

                # Should have caught exception and marked as failed
                assert mock_job_store["test_job_1"]["status"] == "completed"
                assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1


class TestBatchDelete:
    """Tests for batch delete operations."""

    @pytest.mark.asyncio
    async def test_process_batch_delete_no_job_store(self):
        """Test batch delete with no job store provided."""
        await process_batch_delete(
            job_id="test_job_1",
            photo_ids=["1", "2"],
            job_store=None,
        )
        # Should complete without error but log warning

    @pytest.mark.asyncio
    async def test_process_batch_delete_job_not_found(self):
        """Test batch delete when job not found in store."""
        job_store = {}
        await process_batch_delete(
            job_id="missing_job",
            photo_ids=["1", "2"],
            job_store=job_store,
        )
        # Should complete without error but log error

    @pytest.mark.asyncio
    async def test_process_batch_delete_to_trash(
        self, mock_job_store, temp_test_image
    ):
        """Test batch delete moving files to trash."""
        photo_path = temp_test_image

        with (
            patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr,
            patch("src.workers.batch_worker.Photo") as mock_photo_class,
            patch("src.workers.batch_worker.send2trash.send2trash") as mock_trash,
        ):
            # Setup database mock
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Create photo mock with real file path
            mock_photo = Mock(spec=Photo)
            mock_photo.id = 1
            mock_photo.path = photo_path
            mock_photo_class.from_db_row.return_value = mock_photo

            # Setup query to return photo row
            mock_db.execute_query.return_value = [{"id": 1, "path": photo_path}]

            await process_batch_delete(
                job_id="test_job_1",
                photo_ids=["1"],
                permanent=False,
                job_store=mock_job_store,
            )

            # Verify trash was called
            mock_trash.assert_called_once()

            # Verify database delete
            mock_db.execute_update.assert_called_once()

            # Verify job status
            assert mock_job_store["test_job_1"]["status"] == "completed"
            assert mock_job_store["test_job_1"]["processed_items"] == 1

    @pytest.mark.asyncio
    async def test_process_batch_delete_permanent(
        self, mock_job_store, temp_test_image
    ):
        """Test batch delete with permanent deletion."""
        photo_path = temp_test_image

        with (
            patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr,
            patch("src.workers.batch_worker.Photo") as mock_photo_class,
        ):
            # Setup database mock
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Create photo mock with real file path
            mock_photo = Mock(spec=Photo)
            mock_photo.id = 1
            mock_photo.path = photo_path
            mock_photo_class.from_db_row.return_value = mock_photo

            # Setup query to return photo row
            mock_db.execute_query.return_value = [{"id": 1, "path": photo_path}]

            await process_batch_delete(
                job_id="test_job_1",
                photo_ids=["1"],
                permanent=True,
                job_store=mock_job_store,
            )

            # Verify database delete
            mock_db.execute_update.assert_called_once()

            # Verify file was deleted (should not exist)
            assert not Path(photo_path).exists()

            # Verify job status
            assert mock_job_store["test_job_1"]["status"] == "completed"
            assert mock_job_store["test_job_1"]["processed_items"] == 1

    @pytest.mark.asyncio
    async def test_process_batch_delete_invalid_photo_id(self, mock_job_store):
        """Test batch delete with invalid photo ID."""
        with patch("src.workers.batch_worker.get_database_manager"):
            await process_batch_delete(
                job_id="test_job_1",
                photo_ids=["invalid_id"],
                job_store=mock_job_store,
            )

            # Should mark as failed
            assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1
            assert mock_job_store["test_job_1"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_process_batch_delete_photo_not_found(self, mock_job_store):
        """Test batch delete when photo not found in database."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db
            mock_db.execute_query.return_value = []  # No photo found

            await process_batch_delete(
                job_id="test_job_1",
                photo_ids=["999"],
                job_store=mock_job_store,
            )

            # Should mark as failed
            assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1
            assert mock_job_store["test_job_1"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_process_batch_delete_file_not_exists(self, mock_job_store):
        """Test batch delete when file doesn't exist."""
        with (
            patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr,
            patch("src.workers.batch_worker.Photo") as mock_photo_class,
        ):
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Create photo with non-existent path
            mock_photo = Mock(spec=Photo)
            mock_photo.id = 1
            mock_photo.path = "/nonexistent/file.jpg"
            mock_photo_class.from_db_row.return_value = mock_photo

            mock_db.execute_query.return_value = [
                {"id": 1, "path": "/nonexistent/file.jpg"}
            ]

            await process_batch_delete(
                job_id="test_job_1",
                photo_ids=["1"],
                job_store=mock_job_store,
            )

            # Should still remove from database
            mock_db.execute_update.assert_called_once()

            # Verify job status
            assert mock_job_store["test_job_1"]["status"] == "completed"
            assert mock_job_store["test_job_1"]["processed_items"] == 1

    @pytest.mark.asyncio
    async def test_process_batch_delete_exception_handling(self, mock_job_store):
        """Test batch delete handles exceptions gracefully."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db_mgr.side_effect = Exception("Database error")

            await process_batch_delete(
                job_id="test_job_1",
                photo_ids=["1"],
                job_store=mock_job_store,
            )

            # Should mark job as failed
            assert mock_job_store["test_job_1"]["status"] == "failed"
            assert "error" in mock_job_store["test_job_1"]

    @pytest.mark.asyncio
    async def test_process_batch_delete_photo_processing_exception(
        self, mock_job_store, temp_test_image
    ):
        """Test batch delete with exception during photo processing."""
        photo_path = temp_test_image

        with (
            patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr,
            patch("src.workers.batch_worker.Photo") as mock_photo_class,
        ):
            # Setup database mock
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Create photo mock
            mock_photo = Mock(spec=Photo)
            mock_photo.id = 1
            mock_photo.path = photo_path
            mock_photo_class.from_db_row.return_value = mock_photo

            # Setup query to return photo row
            mock_db.execute_query.return_value = [{"id": 1, "path": photo_path}]

            # Make database delete raise an exception
            mock_db.execute_update.side_effect = Exception("Database delete error")

            await process_batch_delete(
                job_id="test_job_1",
                photo_ids=["1"],
                permanent=True,
                job_store=mock_job_store,
            )

            # Should have caught exception and marked as failed
            assert mock_job_store["test_job_1"]["status"] == "completed"
            assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1


class TestBatchTag:
    """Tests for batch tag operations."""

    @pytest.mark.asyncio
    async def test_process_batch_tag_no_job_store(self):
        """Test batch tag with no job store provided."""
        await process_batch_tag(
            job_id="test_job_1",
            photo_ids=["1", "2"],
            tags=["tag1", "tag2"],
            job_store=None,
        )
        # Should complete without error but log warning

    @pytest.mark.asyncio
    async def test_process_batch_tag_job_not_found(self):
        """Test batch tag when job not found in store."""
        job_store = {}
        await process_batch_tag(
            job_id="missing_job",
            photo_ids=["1", "2"],
            tags=["tag1"],
            job_store=job_store,
        )
        # Should complete without error but log error

    @pytest.mark.asyncio
    async def test_process_batch_tag_no_tags_column(self, mock_job_store):
        """Test batch tag when tags column doesn't exist."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Mock PRAGMA to return no tags column
            mock_db.execute_query.return_value = [
                (0, "id", "INTEGER", 0, None, 1),
                (1, "path", "TEXT", 0, None, 0),
            ]

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["tag1"],
                job_store=mock_job_store,
            )

            # Should mark job as failed
            assert mock_job_store["test_job_1"]["status"] == "failed"
            assert "error" in mock_job_store["test_job_1"]

    @pytest.mark.asyncio
    async def test_process_batch_tag_malformed_pragma_result(self, mock_job_store):
        """Test batch tag with malformed PRAGMA result that raises exception in helper."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Create a mock object that will raise exception when accessing attributes
            class MalformedColumn:
                def __getitem__(self, key):
                    raise KeyError("Malformed column")

                def get(self, key):
                    raise AttributeError("Malformed column")

            # Mock PRAGMA to return malformed column info
            mock_db.execute_query.return_value = [
                MalformedColumn(),
                (0, "id", "INTEGER", 0, None, 1),
            ]

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["tag1"],
                job_store=mock_job_store,
            )

            # Should mark job as failed (no tags column found due to exception)
            assert mock_job_store["test_job_1"]["status"] == "failed"
            assert "error" in mock_job_store["test_job_1"]

    @pytest.mark.asyncio
    async def test_process_batch_tag_add_operation(self, mock_job_store):
        """Test batch tag with add operation."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Mock PRAGMA to return tags column (using tuple format)
            mock_db.execute_query.side_effect = [
                [(0, "id", "INTEGER", 0, None, 1), (1, "tags", "TEXT", 0, None, 0)],
                [(1, "existing,tags")],  # Existing tags for photo
            ]

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["newtag"],
                operation="add",
                job_store=mock_job_store,
            )

            # Verify job status
            assert mock_job_store["test_job_1"]["status"] == "completed"
            assert mock_job_store["test_job_1"]["processed_items"] == 1

            # Verify tags were updated
            mock_db.execute_update.assert_called_once()
            call_args = mock_db.execute_update.call_args[0]
            # Should contain existing tags + new tag
            assert "existing" in call_args[1][0]
            assert "newtag" in call_args[1][0]

    @pytest.mark.asyncio
    async def test_process_batch_tag_remove_operation(self, mock_job_store):
        """Test batch tag with remove operation."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Mock PRAGMA to return tags column (using dict format)
            mock_db.execute_query.side_effect = [
                [{"name": "id"}, {"name": "tags"}],
                [{"id": 1, "tags": "tag1,tag2,tag3"}],  # Existing tags
            ]

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["tag2"],
                operation="remove",
                job_store=mock_job_store,
            )

            # Verify job status
            assert mock_job_store["test_job_1"]["status"] == "completed"
            assert mock_job_store["test_job_1"]["processed_items"] == 1

            # Verify tags were updated
            mock_db.execute_update.assert_called_once()
            call_args = mock_db.execute_update.call_args[0]
            # Should not contain removed tag
            assert "tag2" not in call_args[1][0]
            assert "tag1" in call_args[1][0]
            assert "tag3" in call_args[1][0]

    @pytest.mark.asyncio
    async def test_process_batch_tag_replace_operation(self, mock_job_store):
        """Test batch tag with replace operation."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Mock PRAGMA and query
            mock_db.execute_query.side_effect = [
                [(0, "id", "INTEGER", 0, None, 1), (1, "tags", "TEXT", 0, None, 0)],
                [(1, "old,tags")],  # Existing tags
            ]

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["new", "tags"],
                operation="replace",
                job_store=mock_job_store,
            )

            # Verify job status
            assert mock_job_store["test_job_1"]["status"] == "completed"
            assert mock_job_store["test_job_1"]["processed_items"] == 1

            # Verify tags were replaced
            mock_db.execute_update.assert_called_once()
            call_args = mock_db.execute_update.call_args[0]
            # Should only contain new tags
            assert call_args[1][0] == "new,tags"

    @pytest.mark.asyncio
    async def test_process_batch_tag_invalid_photo_id(self, mock_job_store):
        """Test batch tag with invalid photo ID."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Mock PRAGMA
            mock_db.execute_query.return_value = [
                (0, "id", "INTEGER", 0, None, 1),
                (1, "tags", "TEXT", 0, None, 0),
            ]

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["invalid_id"],
                tags=["tag1"],
                job_store=mock_job_store,
            )

            # Should mark as failed
            assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1
            assert mock_job_store["test_job_1"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_process_batch_tag_photo_not_found(self, mock_job_store):
        """Test batch tag when photo not found in database."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Mock PRAGMA and empty query result
            mock_db.execute_query.side_effect = [
                [(0, "id", "INTEGER", 0, None, 1), (1, "tags", "TEXT", 0, None, 0)],
                [],  # No photo found
            ]

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["999"],
                tags=["tag1"],
                job_store=mock_job_store,
            )

            # Should mark as failed
            assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1
            assert mock_job_store["test_job_1"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_process_batch_tag_invalid_operation(self, mock_job_store):
        """Test batch tag with invalid operation."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Mock PRAGMA and query
            mock_db.execute_query.side_effect = [
                [(0, "id", "INTEGER", 0, None, 1), (1, "tags", "TEXT", 0, None, 0)],
                [(1, "existing")],
            ]

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["tag1"],
                operation="invalid_op",
                job_store=mock_job_store,
            )

            # Should mark as failed
            assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1
            assert mock_job_store["test_job_1"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_process_batch_tag_empty_existing_tags(self, mock_job_store):
        """Test batch tag when photo has no existing tags."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Mock PRAGMA and query with null tags
            mock_db.execute_query.side_effect = [
                [(0, "id", "INTEGER", 0, None, 1), (1, "tags", "TEXT", 0, None, 0)],
                [(1, "")],  # Empty tags
            ]

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["newtag"],
                operation="add",
                job_store=mock_job_store,
            )

            # Verify job status
            assert mock_job_store["test_job_1"]["status"] == "completed"
            assert mock_job_store["test_job_1"]["processed_items"] == 1

    @pytest.mark.asyncio
    async def test_process_batch_tag_exception_handling(self, mock_job_store):
        """Test batch tag handles exceptions gracefully."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db_mgr.side_effect = Exception("Database error")

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["tag1"],
                job_store=mock_job_store,
            )

            # Should mark job as failed
            assert mock_job_store["test_job_1"]["status"] == "failed"
            assert "error" in mock_job_store["test_job_1"]

    @pytest.mark.asyncio
    async def test_process_batch_tag_pragma_exception(self, mock_job_store):
        """Test batch tag when PRAGMA query fails."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Make PRAGMA query raise exception
            mock_db.execute_query.side_effect = Exception("PRAGMA error")

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["tag1"],
                job_store=mock_job_store,
            )

            # Should have caught exception
            assert mock_job_store["test_job_1"]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_process_batch_tag_processing_exception(self, mock_job_store):
        """Test batch tag with exception during tag processing."""
        with patch("src.workers.batch_worker.get_database_manager") as mock_db_mgr:
            mock_db = MagicMock()
            mock_db_mgr.return_value = mock_db

            # Mock PRAGMA and query
            mock_db.execute_query.side_effect = [
                [(0, "id", "INTEGER", 0, None, 1), (1, "tags", "TEXT", 0, None, 0)],
                [(1, "existing")],
            ]

            # Make update raise exception
            mock_db.execute_update.side_effect = Exception("Update error")

            await process_batch_tag(
                job_id="test_job_1",
                photo_ids=["1"],
                tags=["newtag"],
                operation="add",
                job_store=mock_job_store,
            )

            # Should have caught exception and marked as failed
            assert mock_job_store["test_job_1"]["status"] == "completed"
            assert mock_job_store["test_job_1"].get("failed_items", 0) >= 1
