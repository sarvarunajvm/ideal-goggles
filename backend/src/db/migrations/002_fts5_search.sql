-- Migration 002: Real full-text search
-- Created: 2026-08-29
-- Description:
--   Text search previously advertised FTS5 (see docstrings in
--   src/services/text_search.py) but actually ran LIKE '%term%' scans over
--   photos.filename / photos.folder / exif.camera_make / exif.camera_model.
--   A leading-wildcard LIKE cannot use an index, so every text search did a
--   full table scan. This migration adds a real FTS5 virtual table kept in
--   sync via triggers, so search_photos() can use `photos_fts MATCH ?`
--   instead.

BEGIN TRANSACTION;

-- FTS5 index over the fields users actually search on today.
CREATE VIRTUAL TABLE IF NOT EXISTS photos_fts USING fts5(
  filename,
  folder,
  camera_make,
  camera_model,
  tokenize = 'unicode61 remove_diacritics 2'
);

-- Backfill from existing data. rowid is aligned with photos.id so results
-- can be joined straight back to the photos table.
INSERT OR IGNORE INTO photos_fts (rowid, filename, folder, camera_make, camera_model)
SELECT p.id, p.filename, p.folder, e.camera_make, e.camera_model
FROM photos p
LEFT JOIN exif e ON e.file_id = p.id;

-- Keep photos_fts in sync with photos.
CREATE TRIGGER IF NOT EXISTS photos_fts_ai AFTER INSERT ON photos BEGIN
  INSERT INTO photos_fts (rowid, filename, folder, camera_make, camera_model)
  VALUES (
    new.id,
    new.filename,
    new.folder,
    (SELECT camera_make FROM exif WHERE file_id = new.id),
    (SELECT camera_model FROM exif WHERE file_id = new.id)
  );
END;

CREATE TRIGGER IF NOT EXISTS photos_fts_ad AFTER DELETE ON photos BEGIN
  DELETE FROM photos_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS photos_fts_au AFTER UPDATE OF filename, folder ON photos BEGIN
  UPDATE photos_fts SET filename = new.filename, folder = new.folder WHERE rowid = new.id;
END;

-- Keep photos_fts in sync with exif (usually inserted after the photos row
-- by a separate worker, so this is an UPDATE, not an INSERT).
CREATE TRIGGER IF NOT EXISTS exif_fts_ai AFTER INSERT ON exif BEGIN
  UPDATE photos_fts
  SET camera_make = new.camera_make, camera_model = new.camera_model
  WHERE rowid = new.file_id;
END;

CREATE TRIGGER IF NOT EXISTS exif_fts_au AFTER UPDATE OF camera_make, camera_model ON exif BEGIN
  UPDATE photos_fts
  SET camera_make = new.camera_make, camera_model = new.camera_model
  WHERE rowid = new.file_id;
END;

CREATE TRIGGER IF NOT EXISTS exif_fts_ad AFTER DELETE ON exif BEGIN
  UPDATE photos_fts
  SET camera_make = NULL, camera_model = NULL
  WHERE rowid = old.file_id;
END;

COMMIT;
