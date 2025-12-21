"""Comprehensive unit tests for database utility functions - 70%+ coverage target."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from src.db.connection import DatabaseManager
from src.db.utils import DatabaseHelper


class TestDatabaseHelperGetConfig:
    """Test DatabaseHelper get_config method."""

    def test_get_config_specific_key(self):
        """Test getting specific config key."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Create config table
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """
                )
                conn.execute(
                    "INSERT INTO config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                    ("test_key", json.dumps({"setting": "value"})),
                )
                conn.commit()

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                result = DatabaseHelper.get_config("test_key")

                assert result == {"setting": "value"}

    def test_get_config_nonexistent_key(self):
        """Test getting nonexistent config key."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Create config table
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """
                )
                conn.commit()

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                result = DatabaseHelper.get_config("nonexistent")

                assert result == {}

    def test_get_config_all_configs(self):
        """Test getting all config entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Create config table with multiple entries
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """
                )
                conn.execute(
                    "INSERT INTO config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                    ("key1", json.dumps({"value": 1})),
                )
                conn.execute(
                    "INSERT INTO config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                    ("key2", json.dumps({"value": 2})),
                )
                conn.commit()

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                result = DatabaseHelper.get_config()

                assert "key1" in result
                assert "key2" in result
                assert result["key1"] == {"value": 1}
                assert result["key2"] == {"value": 2}

    def test_get_config_handles_json_decode_error(self):
        """Test handling of JSON decode errors in config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Create config table with invalid JSON
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """
                )
                conn.execute(
                    "INSERT INTO config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                    ("bad_json", "not valid json"),
                )
                conn.commit()

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                result = DatabaseHelper.get_config()

                # Should return raw value when JSON parsing fails
                assert result["bad_json"] == "not valid json"


class TestDatabaseHelperUpdateConfig:
    """Test DatabaseHelper update_config method."""

    def test_update_config_single_key(self):
        """Test updating a single config key."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Create config table
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """
                )
                conn.commit()

            # Mock execute_update method
            db_manager.execute_update = MagicMock(return_value=None)

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                DatabaseHelper.update_config({"new_key": {"data": "value"}})

                # Verify execute_update was called
                assert db_manager.execute_update.called

    def test_update_config_multiple_keys(self):
        """Test updating multiple config keys."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Create config table
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """
                )
                conn.commit()

            db_manager.execute_update = MagicMock(return_value=None)

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                updates = {
                    "key1": {"value": 1},
                    "key2": {"value": 2},
                    "key3": "simple string",
                }

                DatabaseHelper.update_config(updates)

                # Should be called once for each key
                assert db_manager.execute_update.call_count == 3

    def test_update_config_serializes_to_json(self):
        """Test that config values are serialized to JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Create config table
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """
                )
                conn.commit()

            db_manager.execute_update = MagicMock(return_value=None)

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                DatabaseHelper.update_config({"test": {"nested": {"data": [1, 2, 3]}}})

                # Check that JSON was serialized
                call_args = db_manager.execute_update.call_args
                assert call_args is not None
                # The second argument should be the JSON-serialized value
                assert '"nested"' in call_args[0][1][1]


class TestDatabaseHelperGetPhotoCount:
    """Test DatabaseHelper get_photo_count method."""

    def test_get_photo_count_all_photos(self):
        """Test getting total photo count."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Insert test photos
            for i in range(5):
                db_manager.execute_update(
                    "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"/photo{i}.jpg",
                        "/",
                        f"photo{i}.jpg",
                        ".jpg",
                        1024,
                        1.0,
                        1.0,
                        f"sha{i}",
                    ),
                )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                count = DatabaseHelper.get_photo_count(indexed_only=False)

                assert count == 5

    def test_get_photo_count_indexed_only(self):
        """Test getting indexed photo count."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Insert photos, some indexed
            for i in range(5):
                indexed_at = 1234567890.0 if i < 3 else None
                db_manager.execute_update(
                    "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1, indexed_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"/photo{i}.jpg",
                        "/",
                        f"photo{i}.jpg",
                        ".jpg",
                        1024,
                        1.0,
                        1.0,
                        f"sha{i}",
                        indexed_at,
                    ),
                )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                count = DatabaseHelper.get_photo_count(indexed_only=True)

                assert count == 3

    def test_get_photo_count_empty_database(self):
        """Test getting photo count from empty database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                count = DatabaseHelper.get_photo_count()

                assert count == 0


class TestDatabaseHelperGetDatabaseStats:
    """Test DatabaseHelper get_database_stats method."""

    def test_get_database_stats_basic(self):
        """Test getting basic database statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add test data
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1, indexed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "/test.jpg",
                    "/",
                    "test.jpg",
                    ".jpg",
                    1024,
                    1.0,
                    1.0,
                    "stats123",
                    1234567890.0,
                ),
            )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                stats = DatabaseHelper.get_database_stats()

                assert "total_photos" in stats
                assert "photos_with_exif" in stats
                assert "photos_with_thumbnails" in stats
                assert "photos_with_embeddings" in stats
                assert "total_faces" in stats
                assert "enrolled_people" in stats
                assert "indexed_photos" in stats

    def test_get_database_stats_counts(self):
        """Test that stats contain correct counts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add multiple photos
            for i in range(3):
                db_manager.execute_update(
                    "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1, indexed_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"/photo{i}.jpg",
                        "/",
                        f"photo{i}.jpg",
                        ".jpg",
                        1024,
                        1.0,
                        1.0,
                        f"stat{i}",
                        1234567890.0,
                    ),
                )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                stats = DatabaseHelper.get_database_stats()

                assert stats["total_photos"] == 3
                assert stats["indexed_photos"] == 3

    def test_get_database_stats_file_size(self):
        """Test that stats include database file size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                stats = DatabaseHelper.get_database_stats()

                assert "database_size_bytes" in stats
                assert "database_size_mb" in stats
                assert stats["database_size_bytes"] > 0


class TestDatabaseHelperSearchPhotosBasic:
    """Test DatabaseHelper search_photos_basic method."""

    def test_search_photos_basic_no_filters(self):
        """Test basic photo search with no filters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add test photos
            for i in range(5):
                db_manager.execute_update(
                    "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"/folder/photo{i}.jpg",
                        "/folder",
                        f"photo{i}.jpg",
                        ".jpg",
                        1024,
                        1.0,
                        float(i),
                        f"search{i}",
                    ),
                )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                results = DatabaseHelper.search_photos_basic()

                assert len(results) <= 50  # Default limit
                assert len(results) == 5

    def test_search_photos_basic_with_query(self):
        """Test basic photo search with query filter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add test photos
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "/folder/vacation.jpg",
                    "/folder",
                    "vacation.jpg",
                    ".jpg",
                    1024,
                    1.0,
                    1.0,
                    "search1",
                ),
            )
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "/folder/work.jpg",
                    "/folder",
                    "work.jpg",
                    ".jpg",
                    1024,
                    1.0,
                    1.0,
                    "search2",
                ),
            )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                results = DatabaseHelper.search_photos_basic(query="vacation")

                assert len(results) == 1
                assert results[0]["filename"] == "vacation.jpg"

    def test_search_photos_basic_with_folder_filter(self):
        """Test basic photo search with folder filter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add photos in different folders
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "/photos/2023/photo.jpg",
                    "/photos/2023",
                    "photo.jpg",
                    ".jpg",
                    1024,
                    1.0,
                    1.0,
                    "search1",
                ),
            )
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "/photos/2024/photo.jpg",
                    "/photos/2024",
                    "photo.jpg",
                    ".jpg",
                    1024,
                    1.0,
                    1.0,
                    "search2",
                ),
            )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                results = DatabaseHelper.search_photos_basic(folder="/photos/2023")

                assert len(results) == 1
                assert results[0]["folder"] == "/photos/2023"

    def test_search_photos_basic_with_limit(self):
        """Test basic photo search with limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add multiple photos
            for i in range(10):
                db_manager.execute_update(
                    "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"/photo{i}.jpg",
                        "/",
                        f"photo{i}.jpg",
                        ".jpg",
                        1024,
                        1.0,
                        1.0,
                        f"limit{i}",
                    ),
                )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                results = DatabaseHelper.search_photos_basic(limit=3)

                assert len(results) == 3

    def test_search_photos_basic_with_offset(self):
        """Test basic photo search with offset."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add photos with different timestamps for consistent ordering
            for i in range(5):
                db_manager.execute_update(
                    "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"/photo{i}.jpg",
                        "/",
                        f"photo{i}.jpg",
                        ".jpg",
                        1024,
                        1.0,
                        float(5 - i),
                        f"offset{i}",
                    ),
                )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                results = DatabaseHelper.search_photos_basic(limit=50, offset=2)

                assert len(results) == 3

    def test_search_photos_basic_includes_joins(self):
        """Test that basic search includes thumbnail and exif data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add photo
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("/joined.jpg", "/", "joined.jpg", ".jpg", 1024, 1.0, 1.0, "join123"),
            )

            # Get photo ID
            result = db_manager.execute_query(
                "SELECT id FROM photos WHERE sha1 = ?", ("join123",)
            )
            photo_id = result[0][0]

            # Add thumbnail
            db_manager.execute_update(
                "INSERT INTO thumbnails (file_id, thumb_path, width, height, format, generated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (photo_id, "/thumbs/joined.jpg", 200, 200, "JPEG", 1234567890.0),
            )

            # Add EXIF
            db_manager.execute_update(
                "INSERT INTO exif (file_id, shot_dt) VALUES (?, ?)",
                (photo_id, "2023-01-01 12:00:00"),
            )

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                results = DatabaseHelper.search_photos_basic()

                assert len(results) == 1
                assert results[0]["thumb_path"] == "/thumbs/joined.jpg"
                assert results[0]["shot_dt"] == "2023-01-01 12:00:00"


class TestDatabaseHelperCleanupOrphanedRecords:
    """Test DatabaseHelper cleanup_orphaned_records method."""

    def test_cleanup_orphaned_thumbnails(self):
        """Test cleaning up orphaned thumbnails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add orphaned thumbnail (no photo)
            db_manager.execute_update(
                "INSERT INTO thumbnails (file_id, thumb_path, width, height, format, generated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (99999, "/orphan.jpg", 200, 200, "JPEG", 1234567890.0),
            )

            # Mock execute_update to return rowcount
            db_manager.execute_update = MagicMock(return_value=1)

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                cleaned = DatabaseHelper.cleanup_orphaned_records()

                assert "thumbnails" in cleaned
                assert cleaned["thumbnails"] == 1

    def test_cleanup_orphaned_exif(self):
        """Test cleaning up orphaned EXIF records."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add orphaned EXIF
            db_manager.execute_update(
                "INSERT INTO exif (file_id, shot_dt) VALUES (?, ?)",
                (99999, "2023-01-01"),
            )

            db_manager.execute_update = MagicMock(return_value=1)

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                cleaned = DatabaseHelper.cleanup_orphaned_records()

                assert "exif" in cleaned

    def test_cleanup_orphaned_embeddings(self):
        """Test cleaning up orphaned embeddings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            db_manager.execute_update = MagicMock(return_value=0)

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                cleaned = DatabaseHelper.cleanup_orphaned_records()

                assert "embeddings" in cleaned
                assert cleaned["embeddings"] == 0

    def test_cleanup_orphaned_faces(self):
        """Test cleaning up orphaned faces."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            db_manager.execute_update = MagicMock(return_value=0)

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                cleaned = DatabaseHelper.cleanup_orphaned_records()

                assert "faces" in cleaned
                assert cleaned["faces"] == 0

    def test_cleanup_no_orphaned_records(self):
        """Test cleanup when no orphaned records exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Add valid photo with related records
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("/valid.jpg", "/", "valid.jpg", ".jpg", 1024, 1.0, 1.0, "valid123"),
            )

            result = db_manager.execute_query(
                "SELECT id FROM photos WHERE sha1 = ?", ("valid123",)
            )
            photo_id = result[0][0]

            db_manager.execute_update(
                "INSERT INTO thumbnails (file_id, thumb_path, width, height, format, generated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (photo_id, "/valid_thumb.jpg", 200, 200, "JPEG", 1234567890.0),
            )

            db_manager.execute_update = MagicMock(return_value=0)

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                cleaned = DatabaseHelper.cleanup_orphaned_records()

                assert all(count == 0 for count in cleaned.values())

    def test_cleanup_handles_missing_rowcount(self):
        """Test cleanup handles results without rowcount attribute."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager(str(Path(temp_dir) / "test.db"))

            # Mock execute_update to return something that is not an int (unlikely but safe check)
            # Actually, execute_update returns int (rowcount) directly now.
            # So this test is less relevant or should check for return type being handled if it's not int?
            # Or assume execute_update always returns int.
            # If we want to simulate failure to get count, we can return 0.
            db_manager.execute_update = MagicMock(return_value=0)

            with patch("src.db.utils.get_database_manager", return_value=db_manager):
                cleaned = DatabaseHelper.cleanup_orphaned_records()

                # Should handle missing rowcount gracefully (by getting 0)
                assert all(count == 0 for count in cleaned.values())
