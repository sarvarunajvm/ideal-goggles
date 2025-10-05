-- Migration 001: Initial Ideal Goggles Schema
-- Created: 2025-09-22
-- Description: Core schema for Ideal Goggles system

BEGIN TRANSACTION;

-- Core photo metadata
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
);

-- EXIF metadata
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
  orientation INTEGER,
  FOREIGN KEY (file_id) REFERENCES photos(id) ON DELETE CASCADE
);

-- Vector embeddings
CREATE TABLE IF NOT EXISTS embeddings (
  file_id INTEGER PRIMARY KEY,
  clip_vector BLOB NOT NULL,
  embedding_model TEXT NOT NULL,
  processed_at REAL NOT NULL,
  FOREIGN KEY (file_id) REFERENCES photos(id) ON DELETE CASCADE
);

-- Enrolled people
CREATE TABLE IF NOT EXISTS people (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  face_vector BLOB NOT NULL,
  sample_count INTEGER NOT NULL,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  active BOOLEAN DEFAULT TRUE
);

-- Face detections
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
);

-- Thumbnail cache
CREATE TABLE IF NOT EXISTS thumbnails (
  file_id INTEGER PRIMARY KEY,
  thumb_path TEXT NOT NULL,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  format TEXT NOT NULL,
  generated_at REAL NOT NULL,
  FOREIGN KEY (file_id) REFERENCES photos(id) ON DELETE CASCADE
);

-- Configuration and settings
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at REAL NOT NULL
);

-- Drive alias mappings
CREATE TABLE IF NOT EXISTS drive_aliases (
  device_id TEXT PRIMARY KEY,
  alias TEXT NOT NULL,
  mount_point TEXT,
  last_seen REAL NOT NULL
);

-- Essential indexes for search performance
CREATE INDEX IF NOT EXISTS idx_photos_sha1 ON photos(sha1);
CREATE INDEX IF NOT EXISTS idx_photos_folder ON photos(folder);
CREATE INDEX IF NOT EXISTS idx_photos_ext ON photos(ext);
CREATE INDEX IF NOT EXISTS idx_photos_indexed_at ON photos(indexed_at);
CREATE INDEX IF NOT EXISTS idx_exif_shot_dt ON exif(shot_dt);
CREATE INDEX IF NOT EXISTS idx_faces_person_id ON faces(person_id);
CREATE INDEX IF NOT EXISTS idx_faces_confidence ON faces(confidence);
CREATE INDEX IF NOT EXISTS idx_thumbnails_format ON thumbnails(format);

-- Schema version tracking
INSERT INTO settings (key, value, updated_at) VALUES ('schema_version', '1', datetime('now'));
INSERT INTO settings (key, value, updated_at) VALUES ('index_version', '1', datetime('now'));

COMMIT;
