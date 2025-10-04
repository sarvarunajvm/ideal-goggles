# Research: Smart Collections with Auto-Tagging and Event Detection

**Feature**: 002-smart-collections-with
**Date**: 2025-10-04
**Status**: Complete

---

## Research Objectives

Based on Technical Context analysis, research the following areas to inform implementation decisions:

1. **Zero-shot image classification using CLIP** for auto-tagging
2. **Temporal clustering algorithms** for event detection
3. **Perceptual hashing + embedding similarity** for duplicate detection
4. **FTS5 full-text search** for tag queries
5. **Smart album rule engines** and query builders

---

## 1. Auto-Tagging with CLIP Zero-Shot Classification

### Decision
Use CLIP (ViT-B/32) model already in Ideal Goggles for zero-shot classification to generate photo tags without training custom classifiers.

### Rationale
- **Already integrated**: CLIP model is bundled for semantic search (existing feature)
- **Zero-shot**: Can classify any concept without training data
- **Fast**: ViT-B/32 processes images in ~200ms on CPU
- **Multilingual**: CLIP understands text prompts in multiple languages
- **Proven**: Used by major photo apps (Google Photos, Apple Photos concepts)

### Implementation Approach
```python
# Pseudo-code for auto-tagging worker
class AutoTaggingWorker:
    def __init__(self, clip_model):
        self.clip = clip_model
        # Pre-defined tag vocabulary (expandable)
        self.tag_candidates = [
            "portrait", "landscape", "sunset", "sunrise", "beach", "mountains",
            "city", "architecture", "food", "party", "wedding", "ceremony",
            "outdoor", "indoor", "nature", "people", "group", "candid",
            "closeup", "wide angle", "black and white", "colorful", "vibrant"
        ]

    def generate_tags(self, photo_embedding, top_k=10, threshold=0.25):
        # Compare photo embedding with text embeddings of tag candidates
        text_embeddings = self.clip.encode_text(self.tag_candidates)
        similarities = cosine_similarity(photo_embedding, text_embeddings)

        # Filter by confidence threshold, return top_k
        confident_tags = [(tag, score) for tag, score in zip(self.tag_candidates, similarities)
                          if score > threshold]
        return sorted(confident_tags, key=lambda x: x[1], reverse=True)[:top_k]
```

### Alternatives Considered
- **Custom CNN classifier**: Requires labeled training data (rejected: no training set available)
- **ImageNet labels**: Only 1000 classes, not descriptive enough (rejected: limited vocabulary)
- **Cloud Vision APIs**: Violates privacy principle (rejected: must be local-first)

### Performance Target
- **Speed**: 600ms per photo (400ms CLIP inference + 200ms DB writes)
- **Throughput**: 100 photos/min on mid-range hardware
- **Accuracy**: 80%+ relevant tags (measured via user feedback)

---

## 2. Event Detection using DBSCAN Temporal Clustering

### Decision
Use DBSCAN (Density-Based Spatial Clustering) on photo timestamps to automatically detect events.

### Rationale
- **No predefined cluster count**: DBSCAN auto-determines number of events
- **Handles noise**: Photos with gaps aren't forced into events
- **Temporal proximity**: Natural fit for time-series data
- **Fast**: O(n log n) with spatial indexing
- **Proven**: Used in Google Photos, Apple Photos event detection

### Implementation Approach
```python
from sklearn.cluster import DBSCAN
import numpy as np

class EventDetector:
    def __init__(self, eps_hours=4, min_samples=3):
        # eps_hours: max time gap within event (default 4 hours)
        # min_samples: minimum photos to form event
        self.eps = eps_hours * 3600  # convert to seconds
        self.min_samples = min_samples

    def detect_events(self, photos):
        # Extract timestamps, convert to seconds since epoch
        timestamps = np.array([photo.shot_dt.timestamp() for photo in photos])
        timestamps = timestamps.reshape(-1, 1)  # shape: (n, 1)

        # Run DBSCAN clustering
        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(timestamps)

        # Group photos by cluster label (-1 = noise/unclustered)
        events = defaultdict(list)
        for photo, label in zip(photos, clustering.labels_):
            if label != -1:  # exclude noise
                events[label].append(photo)

        return [self._create_event(photos) for photos in events.values()]
```

### Event Naming Strategy
1. Infer event type from dominant tags (e.g., if >50% photos tagged "wedding" → "Wedding Event")
2. Use date range: "Event - June 15, 2024" or "Event - June 15-17, 2024" (multi-day)
3. Allow user to rename/merge/split events manually

### Alternatives Considered
- **Fixed time windows**: Too rigid, misses events spanning midnight (rejected)
- **K-means clustering**: Requires predefined K (number of events unknown) (rejected)
- **Hierarchical clustering**: Too slow for large datasets (rejected)

### Performance Target
- **Speed**: <5s for 10K photos (optimized with numpy vectorization)
- **Accuracy**: 90%+ photos correctly grouped (measured via user corrections)

---

## 3. Duplicate Detection: Perceptual Hash + Embedding Similarity

### Decision
Use two-stage approach: (1) perceptual hashing for fast pre-filtering, (2) CLIP embedding similarity for accurate matching.

### Rationale
- **Perceptual hash (phash)**: Fast, finds visually similar images even with minor edits
- **CLIP embeddings**: Semantic similarity catches duplicates with different crops/angles
- **Two-stage**: Combines speed of phash with accuracy of embeddings

### Implementation Approach
```python
import imagehash
from PIL import Image

class DuplicateDetector:
    def __init__(self, phash_threshold=8, embedding_threshold=0.85):
        self.phash_threshold = phash_threshold  # Hamming distance
        self.embedding_threshold = embedding_threshold  # cosine similarity

    def find_duplicates(self, photos):
        # Stage 1: Perceptual hashing (fast pre-filter)
        hashes = {}
        for photo in photos:
            img = Image.open(photo.path)
            phash = imagehash.phash(img, hash_size=16)  # 256-bit hash
            hashes[photo.id] = phash

        # Find candidates with similar hashes
        candidates = []
        for i, photo1 in enumerate(photos):
            for photo2 in photos[i+1:]:
                hamming_dist = hashes[photo1.id] - hashes[photo2.id]
                if hamming_dist <= self.phash_threshold:
                    candidates.append((photo1, photo2))

        # Stage 2: CLIP embedding similarity (precise matching)
        duplicates = []
        for photo1, photo2 in candidates:
            similarity = cosine_similarity(photo1.embedding, photo2.embedding)
            if similarity >= self.embedding_threshold:
                duplicates.append({
                    'photos': [photo1, photo2],
                    'similarity': similarity,
                    'recommended': self._select_best(photo1, photo2)
                })

        return self._group_duplicates(duplicates)

    def _select_best(self, photo1, photo2):
        # Recommend highest resolution, then largest file size
        if photo1.width * photo1.height > photo2.width * photo2.height:
            return photo1
        elif photo1.size > photo2.size:
            return photo1
        return photo2
```

### Handling Burst Photos
- Detect burst sequences: photos within 1-2 seconds, same metadata
- Mark as "sequence" not "duplicates"
- Allow user to pick best from sequence

### Alternatives Considered
- **MD5 hash matching**: Only finds exact duplicates (rejected: misses similar photos)
- **SSIM (Structural Similarity)**: Slower, less robust to edits (rejected)
- **Deep hashing networks**: Requires GPU, complex (rejected: overkill for use case)

### Performance Target
- **Speed**: <30s for 1K photos (phash: 10s, embedding compare: 20s)
- **Accuracy**: 95%+ true duplicates found, <5% false positives

---

## 4. FTS5 Full-Text Search for Tags

### Decision
Use SQLite FTS5 (Full-Text Search) virtual table for fast tag queries with AND/OR/NOT operations.

### Rationale
- **Already in SQLite**: No additional dependencies
- **Fast**: Optimized inverted index, sub-millisecond searches
- **Boolean operators**: Supports complex queries (sunset AND beach NOT people)
- **Ranking**: Built-in BM25 relevance scoring
- **Prefix matching**: "suns*" matches "sunset", "sunshine", "sunrise"

### Schema Design
```sql
-- Tags table (normalized)
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Photo-Tag junction with confidence scores
CREATE TABLE photo_tags (
    photo_id INTEGER REFERENCES photos(id),
    tag_id INTEGER REFERENCES tags(id),
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0.0 AND 1.0),
    source TEXT NOT NULL CHECK(source IN ('auto', 'manual')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (photo_id, tag_id)
);

-- FTS5 virtual table for fast text search
CREATE VIRTUAL TABLE tags_fts USING fts5(
    name,
    content=tags,
    content_rowid=id
);

-- Triggers to keep FTS in sync
CREATE TRIGGER tags_fts_insert AFTER INSERT ON tags BEGIN
    INSERT INTO tags_fts(rowid, name) VALUES (new.id, new.name);
END;
```

### Query Examples
```sql
-- Find photos tagged "sunset" AND "beach"
SELECT DISTINCT p.* FROM photos p
JOIN photo_tags pt ON p.id = pt.photo_id
JOIN tags_fts tf ON pt.tag_id = tf.rowid
WHERE tf.name MATCH 'sunset beach';

-- Exclude people photos: "landscape NOT people"
SELECT p.* FROM photos p
JOIN photo_tags pt1 ON p.id = pt1.photo_id
JOIN tags t1 ON pt1.tag_id = t1.id
WHERE t1.name = 'landscape'
  AND p.id NOT IN (
      SELECT pt2.photo_id FROM photo_tags pt2
      JOIN tags t2 ON pt2.tag_id = t2.id
      WHERE t2.name = 'people'
  );
```

### Alternatives Considered
- **LIKE queries**: Too slow for large datasets (rejected)
- **Elasticsearch**: External dependency, overkill (rejected: local-first principle)

---

## 5. Smart Album Rule Engine

### Decision
Implement SQL-based rule engine with JSON-stored rule definitions for maximum flexibility.

### Rationale
- **SQL power**: Leverage SQLite's query optimizer for complex filters
- **JSON rules**: Store user-defined rules in structured format
- **Dynamic queries**: Build SQL WHERE clauses from rule AST
- **Composable**: AND/OR/NOT operators nest naturally

### Rule Storage Schema
```sql
CREATE TABLE smart_albums (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    rules JSON NOT NULL,  -- JSON rule definition
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example rules JSON:
{
    "operator": "AND",
    "conditions": [
        {"field": "tags", "operator": "contains", "value": "sunset"},
        {"field": "tags", "operator": "contains", "value": "beach"},
        {
            "operator": "OR",
            "conditions": [
                {"field": "shot_dt", "operator": ">=", "value": "2024-01-01"},
                {"field": "location", "operator": "=", "value": "California"}
            ]
        }
    ]
}
```

### Rule Evaluation
```python
class SmartAlbumEngine:
    def build_query(self, rules_json):
        # Parse JSON rules into SQL WHERE clause
        rule_ast = json.loads(rules_json)
        where_clause = self._compile_rule(rule_ast)

        return f"""
            SELECT DISTINCT p.* FROM photos p
            LEFT JOIN photo_tags pt ON p.id = pt.photo_id
            LEFT JOIN tags t ON pt.tag_id = t.id
            LEFT JOIN exif e ON p.id = e.file_id
            WHERE {where_clause}
        """

    def _compile_rule(self, node):
        if "conditions" in node:  # AND/OR group
            op = " AND " if node["operator"] == "AND" else " OR "
            clauses = [self._compile_rule(cond) for cond in node["conditions"]]
            return f"({op.join(clauses)})"
        else:  # Leaf condition
            return self._compile_condition(node)
```

### Alternatives Considered
- **Rule engine library (Rete)**: Complex for simple use case (rejected)
- **Hard-coded filters**: Not extensible (rejected)

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| Auto-Tagging | CLIP (ONNX) | ViT-B/32 | Already integrated, zero-shot, fast |
| Event Clustering | scikit-learn DBSCAN | 1.5+ | Auto-determines clusters, handles noise |
| Duplicate Detection | imagehash + CLIP | 4.3+ | Fast pre-filter + accurate matching |
| Tag Search | SQLite FTS5 | Built-in | Fast, boolean operators, no dependencies |
| Smart Albums | JSON rules + SQL | SQLAlchemy 2.0+ | Flexible, leverages SQL optimizer |
| State Management | Zustand | 5.0 | Simple, minimal boilerplate |
| Data Fetching | TanStack Query | 5.x | Caching, optimistic updates, devtools |

---

## Performance Validation Plan

### Benchmarks to Run
1. **Auto-tagging**: 100 photos, measure time per photo
2. **Event detection**: 10K photos, measure clustering time
3. **Duplicate detection**: 1K photos with 10% duplicates, measure precision/recall
4. **Tag search**: 1M photos indexed, measure query latency
5. **Collections page load**: 10K photos, 100 events, measure initial render

### Success Criteria
- Auto-tagging: <600ms/photo on Intel i5-10th gen
- Event detection: <5s for 10K photos
- Duplicate detection: <30s for 1K photos, 95%+ accuracy
- Tag search: <100ms for any query
- Collections page: <2s initial load

---

## Open Questions & Risks

### Risks
1. **CLIP tag vocabulary**: Limited to predefined tags (Mitigation: Allow users to add custom tags manually)
2. **DBSCAN sensitivity**: eps parameter affects event boundaries (Mitigation: Make configurable in settings)
3. **Duplicate false positives**: Similar but different photos grouped (Mitigation: Show similarity score, allow user override)

### Deferred Decisions
- **Tag hierarchies**: Consider later if users request parent/child tags (e.g., "animal" → "dog" → "golden retriever")
- **ML model updates**: How to update CLIP vocabulary without breaking existing tags (store vocabulary version)

---

## Research Complete ✅

All technical unknowns resolved. Ready for Phase 1 (Design & Contracts).
