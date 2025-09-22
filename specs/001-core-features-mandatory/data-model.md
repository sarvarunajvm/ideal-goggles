# Data Model: Photo Search and Navigation System

## Core Entities

### Photo Entity
Represents individual image files with complete metadata and processing state.

**Fields**:
- `id`: Integer primary key, unique identifier
- `path`: String, absolute file path (unique)
- `folder`: String, parent directory path
- `filename`: String, file name with extension
- `ext`: String, file extension (.jpg, .png, etc.)
- `size`: Integer, file size in bytes
- `created_ts`: Real, file creation timestamp
- `modified_ts`: Real, file modification timestamp
- `sha1`: String, SHA-1 hash for deduplication
- `phash`: String, perceptual hash for near-duplicate detection
- `indexed_at`: Real, timestamp when photo was indexed
- `index_version`: Integer, schema version for migrations

**Validation Rules**:
- `path` must be absolute and unique
- `ext` must be in ['.jpg', '.jpeg', '.png', '.tiff', '.tif']
- `size` must be positive
- `sha1` must be valid 40-character hex string
- `phash` must be valid 16-character hex string

**State Transitions**:
- DISCOVERED → PROCESSING → INDEXED
- INDEXED → REPROCESSING (if file modified)
- INDEXED → DELETED (if file removed)

### EXIF Metadata Entity
Camera and shooting metadata extracted from image files.

**Fields**:
- `file_id`: Integer, foreign key to Photo.id
- `shot_dt`: String, ISO format datetime when photo taken
- `camera_make`: String, camera manufacturer
- `camera_model`: String, camera model name
- `lens`: String, lens information
- `iso`: Integer, ISO sensitivity
- `aperture`: Real, f-stop value
- `shutter_speed`: String, exposure time
- `focal_length`: Real, focal length in mm
- `gps_lat`: Real, GPS latitude
- `gps_lon`: Real, GPS longitude
- `orientation`: Integer, EXIF orientation flag

**Validation Rules**:
- `file_id` must reference valid Photo.id
- `shot_dt` must be valid ISO datetime or null
- Numeric fields must be positive when present
- GPS coordinates must be valid ranges

### OCR Text Entity
Text content extracted from images via optical character recognition.

**Fields**:
- `file_id`: Integer, foreign key to Photo.id
- `text`: String, extracted text content (FTS5 virtual table)
- `language`: String, detected/configured language
- `confidence`: Real, average OCR confidence score
- `processed_at`: Real, timestamp of OCR processing

**Validation Rules**:
- `file_id` must reference valid Photo.id
- `confidence` must be between 0.0 and 1.0
- `language` must be valid language code

### Embedding Entity
Vector embeddings for semantic and visual similarity search.

**Fields**:
- `file_id`: Integer, primary key and foreign key to Photo.id
- `clip_vector`: Blob, CLIP image embedding (512 dimensions)
- `embedding_model`: String, model identifier and version
- `processed_at`: Real, timestamp when embedding created

**Validation Rules**:
- `file_id` must reference valid Photo.id
- `clip_vector` must be valid 512-dimension float32 array
- `embedding_model` must match supported model versions

### Person Entity
Enrolled individuals for face-based search functionality.

**Fields**:
- `id`: Integer primary key
- `name`: String, person's display name
- `face_vector`: Blob, averaged face embedding
- `sample_count`: Integer, number of sample photos used
- `created_at`: Real, enrollment timestamp
- `updated_at`: Real, last update timestamp
- `active`: Boolean, whether person search is enabled

**Validation Rules**:
- `name` must be non-empty and unique
- `face_vector` must be valid 512-dimension float32 array
- `sample_count` must be positive

### Face Detection Entity
Individual face detections within photos with person associations.

**Fields**:
- `id`: Integer primary key
- `file_id`: Integer, foreign key to Photo.id
- `person_id`: Integer, foreign key to Person.id (nullable)
- `box_xyxy`: String, bounding box coordinates as JSON array
- `face_vector`: Blob, individual face embedding
- `confidence`: Real, face detection confidence score
- `verified`: Boolean, whether face match was manually verified

**Validation Rules**:
- `file_id` must reference valid Photo.id
- `person_id` must reference valid Person.id when not null
- `box_xyxy` must be valid JSON array [x1, y1, x2, y2]
- `confidence` must be between 0.0 and 1.0

### Thumbnail Entity
Cached preview images for fast grid display.

**Fields**:
- `file_id`: Integer, primary key and foreign key to Photo.id
- `thumb_path`: String, relative path to thumbnail file
- `width`: Integer, thumbnail width in pixels
- `height`: Integer, thumbnail height in pixels
- `format`: String, thumbnail format (webp, jpeg)
- `generated_at`: Real, timestamp when thumbnail created

**Validation Rules**:
- `file_id` must reference valid Photo.id
- `thumb_path` must be valid relative path
- `width` and `height` must be positive, max 512px
- `format` must be in ['webp', 'jpeg']

### Search Result Entity (Virtual)
Computed search results with relevance scoring and match indicators.

**Fields**:
- `file_id`: Integer, reference to Photo.id
- `score`: Real, combined relevance score (0.0-1.0)
- `match_types`: Array[String], types of matches found
- `snippet`: String, relevant text excerpt for text matches
- `distance`: Real, vector similarity distance for image matches

**Match Types**:
- `filename`: Match in filename
- `folder`: Match in folder path
- `ocr`: Match in extracted text
- `exif`: Match in EXIF metadata
- `face`: Face similarity match
- `image`: Visual similarity match

## Entity Relationships

### Primary Relationships
- Photo → EXIF (1:1, optional)
- Photo → OCR (1:1, optional)
- Photo → Embedding (1:1, optional)
- Photo → Thumbnail (1:1, required for indexed photos)
- Photo → Face Detection (1:N)
- Person → Face Detection (1:N)

### Foreign Key Constraints
- All child entities CASCADE DELETE when parent Photo deleted
- Face Detection.person_id SET NULL when Person deleted
- Orphaned Face Detections remain for potential re-association

## Storage Implementation

### SQLite Schema
```sql
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
```

### Indexes for Performance
```sql
-- Essential indexes for search performance
CREATE INDEX idx_photos_sha1 ON photos(sha1);
CREATE INDEX idx_photos_folder ON photos(folder);
CREATE INDEX idx_photos_ext ON photos(ext);
CREATE INDEX idx_exif_shot_dt ON exif(shot_dt);
CREATE INDEX idx_faces_person_id ON faces(person_id);
CREATE INDEX idx_faces_confidence ON faces(confidence);
```

### FAISS Vector Index
- Separate binary file for vector similarity search
- IVF,PQ configuration for >200k photos
- Flat index for smaller collections
- Periodic rebuilding for optimal performance

## Data Migration Strategy

### Version Control
- Schema version tracked in settings table
- Incremental migration scripts for each version
- Backward compatibility checks before updates

### Import/Export Format
- JSON-based export for backup/restore
- Includes all metadata and relative thumbnail paths
- Excludes original photos (links by path/hash)
- Compressed archive format for distribution