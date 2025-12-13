"""initial_schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2025-12-13 21:44:38

"""

import sqlalchemy as sa

from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS photos (
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
        )
    """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS exif (
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
          orientation INTEGER
        )
    """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
          file_id INTEGER PRIMARY KEY,
          clip_vector BLOB NOT NULL,
          embedding_model TEXT NOT NULL,
          processed_at REAL NOT NULL,
          FOREIGN KEY (file_id) REFERENCES photos(id) ON DELETE CASCADE
        )
    """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS people (
          id INTEGER PRIMARY KEY,
          name TEXT UNIQUE NOT NULL,
          face_vector BLOB NOT NULL,
          sample_count INTEGER NOT NULL,
          created_at REAL NOT NULL,
          updated_at REAL NOT NULL,
          active BOOLEAN DEFAULT TRUE
        )
    """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS faces (
          id INTEGER PRIMARY KEY,
          file_id INTEGER NOT NULL,
          person_id INTEGER,
          box_xyxy TEXT NOT NULL,
          face_vector BLOB NOT NULL,
          confidence REAL NOT NULL,
          verified BOOLEAN DEFAULT FALSE,
          FOREIGN KEY (file_id) REFERENCES photos(id) ON DELETE CASCADE,
          FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE SET NULL
        )
    """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS thumbnails (
          file_id INTEGER PRIMARY KEY,
          thumb_path TEXT NOT NULL,
          width INTEGER NOT NULL,
          height INTEGER NOT NULL,
          format TEXT NOT NULL,
          generated_at REAL NOT NULL
        )
    """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at REAL NOT NULL
        )
    """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS drive_aliases (
          device_id TEXT PRIMARY KEY,
          alias TEXT NOT NULL,
          mount_point TEXT,
          last_seen REAL NOT NULL
        )
    """
    )

    op.execute("CREATE INDEX IF NOT EXISTS idx_photos_sha1 ON photos(sha1)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_photos_folder ON photos(folder)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_photos_ext ON photos(ext)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_photos_indexed_at ON photos(indexed_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_exif_shot_dt ON exif(shot_dt)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_faces_person_id ON faces(person_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_faces_confidence ON faces(confidence)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_thumbnails_format ON thumbnails(format)")

    op.execute(
        "INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES ('schema_version', '1', datetime('now'))"
    )
    op.execute(
        "INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES ('index_version', '1', datetime('now'))"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS drive_aliases")
    op.execute("DROP TABLE IF EXISTS settings")
    op.execute("DROP TABLE IF EXISTS thumbnails")
    op.execute("DROP TABLE IF EXISTS faces")
    op.execute("DROP TABLE IF EXISTS people")
    op.execute("DROP TABLE IF EXISTS embeddings")
    op.execute("DROP TABLE IF EXISTS exif")
    op.execute("DROP TABLE IF EXISTS photos")
