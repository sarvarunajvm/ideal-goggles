"""Unit tests for database connection and DatabaseManager."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

from src.db.connection import DatabaseManager, get_database_manager, init_database


class TestDatabaseManager:
    """Test DatabaseManager functionality."""

    def test_database_manager_creation_with_default_path(self):
        """Test creating DatabaseManager with default path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use a temporary path for testing
            test_db_path = str(Path(temp_dir) / "test_photos.db")
            db_manager = DatabaseManager(test_db_path)

            assert db_manager.db_path is not None
            assert str(db_manager.db_path).endswith("test_photos.db")

    def test_database_manager_creation_with_custom_path(self):
        """Test creating DatabaseManager with custom path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom.db"

            db_manager = DatabaseManager(str(custom_path))

            assert db_manager.db_path == custom_path.resolve()

    def test_database_creation_if_not_exists(self):
        """Test database creation when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            db_manager = DatabaseManager(str(db_path))

            # Database file should be created
            assert db_path.exists()

            # Should have tables
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in cursor.fetchall()]

            assert "photos" in tables
            assert "settings" in tables

    def test_get_connection_with_proper_settings(self):
        """Test that get_connection returns properly configured connection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            conn = db_manager.get_connection()

            # Test that foreign keys are enabled
            cursor = conn.execute("PRAGMA foreign_keys")
            foreign_keys_enabled = cursor.fetchone()[0]
            assert foreign_keys_enabled == 1

            # Test that WAL mode is set
            cursor = conn.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            assert journal_mode.lower() == "wal"

            # Test row factory
            assert conn.row_factory == sqlite3.Row

            conn.close()

    def test_execute_query(self):
        """Test executing a SELECT query."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            # Insert test data
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "/test/photo.jpg",
                    "/test",
                    "photo.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    "abc123",
                ),
            )

            # Query the data
            results = db_manager.execute_query(
                "SELECT * FROM photos WHERE filename = ?", ("photo.jpg",)
            )

            assert len(results) == 1
            assert results[0]["filename"] == "photo.jpg"
            assert results[0]["size"] == 1024

    def test_execute_update(self):
        """Test executing an INSERT/UPDATE/DELETE query."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            # Insert data
            rows_affected = db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "/test/photo.jpg",
                    "/test",
                    "photo.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    "abc123",
                ),
            )

            assert rows_affected == 1

            # Update data
            rows_affected = db_manager.execute_update(
                "UPDATE photos SET size = ? WHERE filename = ?", (2048, "photo.jpg")
            )

            assert rows_affected == 1

    def test_execute_many(self):
        """Test executing query with multiple parameter sets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            # Insert multiple records
            photo_data = [
                (
                    "/test/photo1.jpg",
                    "/test",
                    "photo1.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    "abc123",
                ),
                (
                    "/test/photo2.jpg",
                    "/test",
                    "photo2.jpg",
                    ".jpg",
                    2048,
                    1640995300.0,
                    1640995300.0,
                    "def456",
                ),
            ]

            rows_affected = db_manager.execute_many(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                photo_data,
            )

            assert rows_affected == 2

            # Verify data was inserted
            results = db_manager.execute_query("SELECT COUNT(*) as count FROM photos")
            assert results[0]["count"] == 2

    def test_get_cursor_context_manager(self):
        """Test get_cursor context manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM photos")
                result = cursor.fetchone()
                assert result[0] == 0

    def test_get_transaction_context_manager_commit(self):
        """Test get_transaction context manager with successful commit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            with db_manager.get_transaction() as conn:
                conn.execute(
                    "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        "/test/photo.jpg",
                        "/test",
                        "photo.jpg",
                        ".jpg",
                        1024,
                        1640995200.0,
                        1640995200.0,
                        "abc123",
                    ),
                )

            # Verify data was committed
            results = db_manager.execute_query("SELECT COUNT(*) as count FROM photos")
            assert results[0]["count"] == 1

    def test_get_transaction_context_manager_rollback(self):
        """Test get_transaction context manager with rollback on exception."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            try:
                with db_manager.get_transaction() as conn:
                    conn.execute(
                        "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            "/test/photo.jpg",
                            "/test",
                            "photo.jpg",
                            ".jpg",
                            1024,
                            1640995200.0,
                            1640995200.0,
                            "abc123",
                        ),
                    )
                    # Force an exception
                    test_error = "Test exception"
                    raise RuntimeError(test_error)
            except RuntimeError:
                pass

            # Verify data was rolled back
            results = db_manager.execute_query("SELECT COUNT(*) as count FROM photos")
            assert results[0]["count"] == 0

    def test_get_database_info(self):
        """Test getting database information and statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            # Insert some test data
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "/test/photo.jpg",
                    "/test",
                    "photo.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    "abc123",
                ),
            )

            info = db_manager.get_database_info()

            assert "database_path" in info
            assert "database_size_bytes" in info
            assert "database_size_mb" in info
            assert "table_counts" in info
            assert "settings" in info

            assert info["table_counts"]["photos"] == 1
            assert info["database_size_bytes"] > 0

    def test_backup_database(self):
        """Test database backup functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Original database
            db_path = Path(temp_dir) / "original.db"
            db_manager = DatabaseManager(str(db_path))

            # Insert test data
            db_manager.execute_update(
                "INSERT INTO photos (path, folder, filename, ext, size, created_ts, modified_ts, sha1) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "/test/photo.jpg",
                    "/test",
                    "photo.jpg",
                    ".jpg",
                    1024,
                    1640995200.0,
                    1640995200.0,
                    "abc123",
                ),
            )

            # Backup
            backup_path = Path(temp_dir) / "backup.db"
            db_manager.backup_database(str(backup_path))

            # Verify backup exists and has data
            assert backup_path.exists()

            backup_manager = DatabaseManager(str(backup_path))
            results = backup_manager.execute_query(
                "SELECT COUNT(*) as count FROM photos"
            )
            assert results[0]["count"] == 1

    def test_vacuum_database(self):
        """Test database vacuum operation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            # Should not raise an exception
            db_manager.vacuum_database()

    def test_schema_version_management(self):
        """Test schema version tracking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(str(db_path))

            # Check default schema version
            version = db_manager._get_schema_version()
            assert version == 1  # Default version from initial schema

    def test_migration_detection(self):
        """Test migration detection when newer version available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            # Create database with lower version
            db_manager = DatabaseManager(str(db_path))
            with db_manager.get_connection() as conn:
                conn.execute(
                    "UPDATE settings SET value = '0' WHERE key = 'schema_version'"
                )

            # Mock higher latest version
            with patch.object(
                db_manager, "_get_latest_migration_version", return_value=2
            ):
                with patch.object(db_manager, "_run_migrations") as mock_run_migrations:
                    # Re-initialize to trigger migration check
                    db_manager._initialize_database()

                    mock_run_migrations.assert_called_once_with(from_version=0)


class TestDatabaseManagerGlobals:
    """Test global database manager functions."""

    def test_get_database_manager_singleton(self):
        """Test that get_database_manager returns singleton instance."""
        # Reset global state
        import src.db.connection

        src.db.connection._db_manager = None

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            manager1 = get_database_manager(str(db_path))
            manager2 = get_database_manager(str(db_path))

            # Should be the same instance
            assert manager1 is manager2

    def test_init_database_with_custom_path(self):
        """Test init_database with custom path."""
        # Reset global state
        import src.db.connection

        src.db.connection._db_manager = None

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            manager = init_database(str(db_path))

            assert manager.db_path == db_path.resolve()

    def test_embedded_schema_fallback(self):
        """Test that embedded schema is used when migrations directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            # Mock migrations directory not existing
            with patch("src.db.connection.Path") as mock_path:
                # Set up the main path mock for the db file
                mock_path.return_value = Path(db_path)

                # Mock the migrations directory check
                def side_effect(path_str):
                    if "migrations" in str(path_str):
                        mock_migrations_path = Mock()
                        mock_migrations_path.exists.return_value = False
                        return mock_migrations_path
                    return Path(path_str)

                mock_path.side_effect = side_effect

                db_manager = DatabaseManager(str(db_path))

                # Should still create database with embedded schema
                assert db_path.exists()

                # Should have basic tables
                with db_manager.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                    tables = [row[0] for row in cursor.fetchall()]

                assert "photos" in tables
