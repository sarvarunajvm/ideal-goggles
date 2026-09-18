"""fts5_search

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-29 00:00:00

Text search previously advertised FTS5 (see docstrings in
src/services/text_search.py) but actually ran LIKE '%term%' scans over
photos.filename / photos.folder / exif.camera_make / exif.camera_model. A
leading-wildcard LIKE cannot use an index, so every text search did a full
table scan. This migration adds a real FTS5 virtual table kept in sync via
triggers, so search_photos() can use `photos_fts MATCH ?` instead.
"""

from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS photos_fts USING fts5(
          filename,
          folder,
          camera_make,
          camera_model,
          tokenize = 'unicode61 remove_diacritics 2'
        )
    """)

    op.execute("""
        INSERT OR IGNORE INTO photos_fts (rowid, filename, folder, camera_make, camera_model)
        SELECT p.id, p.filename, p.folder, e.camera_make, e.camera_model
        FROM photos p
        LEFT JOIN exif e ON e.file_id = p.id
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS photos_fts_ai AFTER INSERT ON photos BEGIN
          INSERT INTO photos_fts (rowid, filename, folder, camera_make, camera_model)
          VALUES (
            new.id,
            new.filename,
            new.folder,
            (SELECT camera_make FROM exif WHERE file_id = new.id),
            (SELECT camera_model FROM exif WHERE file_id = new.id)
          );
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS photos_fts_ad AFTER DELETE ON photos BEGIN
          DELETE FROM photos_fts WHERE rowid = old.id;
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS photos_fts_au AFTER UPDATE OF filename, folder ON photos BEGIN
          UPDATE photos_fts SET filename = new.filename, folder = new.folder WHERE rowid = new.id;
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS exif_fts_ai AFTER INSERT ON exif BEGIN
          UPDATE photos_fts
          SET camera_make = new.camera_make, camera_model = new.camera_model
          WHERE rowid = new.file_id;
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS exif_fts_au AFTER UPDATE OF camera_make, camera_model ON exif BEGIN
          UPDATE photos_fts
          SET camera_make = new.camera_make, camera_model = new.camera_model
          WHERE rowid = new.file_id;
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS exif_fts_ad AFTER DELETE ON exif BEGIN
          UPDATE photos_fts
          SET camera_make = NULL, camera_model = NULL
          WHERE rowid = old.file_id;
        END
    """)

    op.execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('schema_version', '2', datetime('now'))"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS exif_fts_ad")
    op.execute("DROP TRIGGER IF EXISTS exif_fts_au")
    op.execute("DROP TRIGGER IF EXISTS exif_fts_ai")
    op.execute("DROP TRIGGER IF EXISTS photos_fts_au")
    op.execute("DROP TRIGGER IF EXISTS photos_fts_ad")
    op.execute("DROP TRIGGER IF EXISTS photos_fts_ai")
    op.execute("DROP TABLE IF EXISTS photos_fts")
    op.execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('schema_version', '1', datetime('now'))"
    )
