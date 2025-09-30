"""Database connection and session management for Ideal Goggles system."""

import logging
import sqlite3
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

# Embedded initial schema as fallback for bundled environments
INITIAL_SCHEMA = """
-- Initial Ideal Goggles Schema (embedded fallback)
BEGIN TRANSACTION;

-- Core photo metadata
CREATE TABLE photos (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  folder TEXT NOT NULL,
  filename TEXT NOT NULL,
  ext TEXT NOT NULL,
  size INTEGER NOT NULL,
  created_ts REAL NOT NULL,
  modified_ts REAL NOT NULL,
  sha1 TEXT NOT NULL,
  phash TEXT,
  indexed_at REAL,
  index_version INTEGER DEFAULT 1
);

-- EXIF metadata
CREATE TABLE exif (
  file_id INTEGER PRIMARY KEY,
  shot_dt TEXT,
  camera_make TEXT,
  camera_model TEXT,
  lens TEXT,
  iso INTEGER,
  aperture REAL,
  shutter_speed TEXT,
  focal_length REAL,
  gps_lat REAL,
  gps_lon REAL,
  orientation INTEGER,
  FOREIGN KEY (file_id) REFERENCES photos(id) ON DELETE CASCADE
);

-- OCR text with full-text search
CREATE VIRTUAL TABLE ocr USING fts5(
  text,
  file_id UNINDEXED,
  language UNINDEXED,
  confidence UNINDEXED,
  processed_at UNINDEXED,
  content=''
);

-- Vector embeddings
CREATE TABLE embeddings (
  file_id INTEGER PRIMARY KEY,
  clip_vector BLOB NOT NULL,
  embedding_model TEXT NOT NULL,
  processed_at REAL NOT NULL,
  FOREIGN KEY (file_id) REFERENCES photos(id) ON DELETE CASCADE
);

-- Enrolled people
CREATE TABLE people (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  face_vector BLOB NOT NULL,
  sample_count INTEGER NOT NULL,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  active BOOLEAN DEFAULT TRUE
);

-- Face detections
CREATE TABLE faces (
  id INTEGER PRIMARY KEY,
  file_id INTEGER NOT NULL,
  person_id INTEGER,
  box_xyxy TEXT NOT NULL,
  face_vector BLOB NOT NULL,
  confidence REAL NOT NULL,
  verified BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (file_id) REFERENCES photos(id) ON DELETE CASCADE,
  FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE SET NULL
);

-- Thumbnail cache
CREATE TABLE thumbnails (
  file_id INTEGER PRIMARY KEY,
  thumb_path TEXT NOT NULL,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  format TEXT NOT NULL,
  generated_at REAL NOT NULL,
  FOREIGN KEY (file_id) REFERENCES photos(id) ON DELETE CASCADE
);

-- Configuration and settings
CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at REAL NOT NULL
);

-- Drive alias mappings
CREATE TABLE drive_aliases (
  device_id TEXT PRIMARY KEY,
  alias TEXT NOT NULL,
  mount_point TEXT,
  last_seen REAL NOT NULL
);

-- Essential indexes for search performance
CREATE INDEX idx_photos_sha1 ON photos(sha1);
CREATE INDEX idx_photos_folder ON photos(folder);
CREATE INDEX idx_photos_ext ON photos(ext);
CREATE INDEX idx_photos_indexed_at ON photos(indexed_at);
CREATE INDEX idx_exif_shot_dt ON exif(shot_dt);
CREATE INDEX idx_faces_person_id ON faces(person_id);
CREATE INDEX idx_faces_confidence ON faces(confidence);
CREATE INDEX idx_thumbnails_format ON thumbnails(format);

-- Schema version tracking
INSERT INTO settings (key, value, updated_at) VALUES ('schema_version', '1', datetime('now'));
INSERT INTO settings (key, value, updated_at) VALUES ('index_version', '1', datetime('now'));

COMMIT;
"""


class DatabaseManager:
    """Manages SQLite database connections and migrations."""

    def __init__(self, db_path: str | None = None):
        """Initialize database manager with optional custom path.

        Defaults to a workspace-local path (./data/photos.db) to work in
        sandboxed and CI environments where writing to the user home directory
        may be restricted.
        """
        if db_path is None:
            # Use absolute path based on the backend directory
            import os
            backend_dir = Path(__file__).resolve().parent.parent.parent
            data_dir = backend_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "photos.db"

        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = None

        # Initialize database if it doesn't exist
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database with schema if it doesn't exist."""
        if not self.db_path.exists():
            logger.info(f"Creating new database at {self.db_path}")
            self._run_migrations()
        else:
            # Check if the database has tables
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = cursor.fetchall()

            if not tables:
                # Database file exists but is empty, initialize it
                logger.info(f"Initializing empty database at {self.db_path}")
                self._run_migrations()
            else:
                # Check if we need to run migrations
                current_version = self._get_schema_version()
                latest_version = self._get_latest_migration_version()

                if current_version < latest_version:
                    logger.info(
                        f"Upgrading database from version {current_version} to {latest_version}"
                    )
                    self._run_migrations(from_version=current_version)

    def _get_schema_version(self) -> int:
        """Get current schema version from database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT value FROM settings WHERE key = 'schema_version'"
                )
                result = cursor.fetchone()
                return int(result[0]) if result else 0
        except sqlite3.OperationalError:
            # Table doesn't exist, this is a new database
            return 0

    def _get_latest_migration_version(self) -> int:
        """Get the latest migration version available."""
        migrations_dir = Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            return 1

        migration_files = list(migrations_dir.glob("*.sql"))
        if not migration_files:
            return 1

        # Extract version numbers from filenames like "001_initial_schema.sql"
        versions = []
        for file in migration_files:
            try:
                version = int(file.stem.split("_")[0])
                versions.append(version)
            except (ValueError, IndexError):
                continue

        return max(versions) if versions else 1

    def _run_migrations(self, from_version: int = 0):
        """Run database migrations from specified version."""
        migrations_dir = Path(__file__).parent / "migrations"

        if not migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {migrations_dir}")
            # Use embedded schema as fallback for bundled environments
            if from_version == 0:
                logger.info("Using embedded initial schema for database setup")
                self._run_embedded_migration()
            return

        # Find and sort migration files
        migration_files = []
        for file in migrations_dir.glob("*.sql"):
            try:
                version = int(file.stem.split("_")[0])
                if version > from_version:
                    migration_files.append((version, file))
            except (ValueError, IndexError):
                logger.warning(f"Skipping invalid migration file: {file}")
                continue

        migration_files.sort(key=lambda x: x[0])

        with self.get_connection() as conn:
            for version, file_path in migration_files:
                logger.info(f"Running migration {version}: {file_path.name}")
                try:
                    with open(file_path) as f:
                        migration_sql = f.read()

                    # Execute migration
                    conn.executescript(migration_sql)

                    # Update schema version
                    conn.execute(
                        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                        ("schema_version", str(version)),
                    )

                    logger.info(f"Migration {version} completed successfully")

                except Exception as e:
                    logger.exception(f"Migration {version} failed: {e}")
                    raise

    def _run_embedded_migration(self):
        """Run the embedded initial schema migration."""
        with self.get_connection() as conn:
            try:
                # Execute the embedded schema
                conn.executescript(INITIAL_SCHEMA)
                logger.info("Embedded initial schema applied successfully")
            except Exception as e:
                logger.exception(f"Failed to apply embedded schema: {e}")
                raise

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with optimal settings."""
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Set WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")

        # Optimize for performance
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -2000")  # 2MB cache
        conn.execute("PRAGMA temp_store = MEMORY")

        # Row factory for named access
        conn.row_factory = sqlite3.Row

        return conn

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Get a cursor with automatic connection management."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            yield cursor
        finally:
            conn.close()

    @contextmanager
    def get_transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a connection with automatic transaction management."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """Execute a SELECT query and return results."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        with self.get_transaction() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount

    def execute_many(self, query: str, params_list: list) -> int:
        """Execute a query with multiple parameter sets."""
        with self.get_transaction() as conn:
            cursor = conn.executemany(query, params_list)
            return cursor.rowcount

    def backup_database(self, backup_path: str):
        """Create a backup of the database."""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as conn:
            backup = sqlite3.connect(backup_path)
            try:
                conn.backup(backup)
                logger.info(f"Database backed up to {backup_path}")
            finally:
                backup.close()

    def vacuum_database(self):
        """Vacuum database to reclaim space and optimize."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            logger.info("Database vacuumed successfully")

    def get_database_info(self) -> dict:
        """Get database information and statistics."""
        with self.get_cursor() as cursor:
            # Get database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]

            db_size = page_count * page_size

            # Get table counts
            tables = {}
            for table in [
                "photos",
                "exif",
                "embeddings",
                "people",
                "faces",
                "thumbnails",
            ]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    tables[table] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    tables[table] = 0

            # Get settings
            settings = {}
            try:
                cursor.execute("SELECT key, value FROM settings")
                settings = dict(cursor.fetchall())
            except sqlite3.OperationalError:
                pass

            return {
                "database_path": str(self.db_path),
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "table_counts": tables,
                "settings": settings,
            }


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager(db_path: str | None = None) -> DatabaseManager:
    """Get or create the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def init_database(db_path: str | None = None) -> DatabaseManager:
    """Initialize database with custom path."""
    global _db_manager
    _db_manager = DatabaseManager(db_path)
    return _db_manager
