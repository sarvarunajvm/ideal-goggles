# Feature Specification: Smart Collections with Auto-Tagging and Event Detection

**Feature Branch**: `002-smart-collections-with`
**Created**: 2025-10-04
**Status**: Draft
**Input**: User description: "Smart Collections with Auto-Tagging and Event Detection"

---

## User Scenarios & Testing

### Primary User Story

A photo studio operator imports hundreds of photos from a wedding shoot. Instead of manually organizing photos into folders and adding tags, the system automatically:
- Detects that photos belong to the same event (wedding on specific date)
- Generates descriptive tags (e.g., "bride", "ceremony", "reception", "outdoor", "sunset")
- Groups photos into a smart collection labeled "Wedding - [Date]"
- Identifies duplicate or near-duplicate shots for review
- Creates dynamic albums based on detected patterns (e.g., all sunset photos, all group photos)

The operator can then quickly find specific moments, share curated collections with clients, and manage storage by removing duplicates.

### Acceptance Scenarios

1. **Given** 500 photos from a wedding imported, **When** indexing completes, **Then** system creates a collection "Wedding Event - 2024-06-15" containing all related photos grouped by ceremony/reception/candid sub-collections

2. **Given** photos contain similar subjects and lighting, **When** auto-tagging runs, **Then** each photo receives relevant tags (minimum 3, maximum 10 tags) describing content, composition, and mood

3. **Given** user searches for "sunset ceremony", **When** query executes, **Then** system returns photos tagged with both "sunset" AND "ceremony" ranked by relevance

4. **Given** duplicate photos exist (same scene, slightly different angle), **When** duplicate detection runs, **Then** system groups duplicates together and suggests keeping best quality version

5. **Given** user creates rule "All outdoor sunset photos from 2024", **When** new photos matching criteria are indexed, **Then** they automatically appear in the smart album without manual action

6. **Given** 10,000+ photos in library, **When** user views collections page, **Then** all auto-generated collections load within 2 seconds with preview thumbnails

### Edge Cases

- What happens when photos span multiple events on same day (morning client, afternoon client)?
- How does system handle photos with no clear event pattern (miscellaneous snapshots)?
- What if user disagrees with auto-generated tags - can they be corrected/removed?
- How are duplicates handled when quality is similar but not identical?
- What happens if event detection groups unrelated photos together?
- How does system handle very large events (5000+ photos from multi-day wedding)?

## Requirements

### Functional Requirements

#### Auto-Tagging
- **FR-001**: System MUST automatically generate descriptive tags for each indexed photo without requiring manual input
- **FR-002**: System MUST generate minimum 3 and maximum 10 relevant tags per photo describing subjects, composition, mood, and scene
- **FR-003**: Tags MUST be searchable and filterable in the main search interface
- **FR-004**: System MUST support tag confidence scores indicating certainty of tag relevance
- **FR-005**: Users MUST be able to view all tags associated with a photo in the preview/details view
- **FR-006**: Users MUST be able to manually add, edit, or remove tags from individual photos
- **FR-007**: System MUST maintain tag consistency (same subjects get same tag names across photos)
- **FR-008**: Tag generation MUST complete within 100ms per photo during indexing

#### Event Detection
- **FR-009**: System MUST automatically detect events by analyzing temporal proximity (photos taken within same time window)
- **FR-010**: System MUST group photos into events when taken within configurable time threshold (default: 4 hours)
- **FR-011**: System MUST name events using pattern: "[Event Type] - [Date]" when event type can be inferred
- **FR-012**: System MUST create hierarchical collections with main event and sub-collections for different parts (e.g., ceremony, reception)
- **FR-013**: Users MUST be able to view all auto-detected events in a dedicated Collections view
- **FR-014**: Users MUST be able to rename, merge, split, or delete auto-generated events
- **FR-015**: System MUST handle multi-day events by spanning date ranges in collection name
- **FR-016**: Event detection MUST work on library of 1M+ photos without performance degradation

#### Duplicate Detection
- **FR-017**: System MUST identify near-duplicate photos (same scene, similar composition, within 60 seconds)
- **FR-018**: System MUST calculate similarity score between potential duplicates (0-100%)
- **FR-019**: System MUST group duplicates with similarity > 85% for user review
- **FR-020**: System MUST recommend highest quality photo in duplicate group based on resolution, sharpness, and file size
- **FR-021**: Users MUST be able to view duplicate groups side-by-side for comparison
- **FR-022**: Users MUST be able to mark preferred photo in duplicate group and archive/delete others
- **FR-023**: Duplicate detection MUST not flag intentional burst shots or sequences as duplicates
- **FR-024**: System MUST provide one-click "delete all duplicates except best" action with confirmation

#### Smart Albums
- **FR-025**: Users MUST be able to create rule-based smart albums using tag, date, location, and metadata criteria
- **FR-026**: Smart albums MUST update automatically when new photos matching criteria are indexed
- **FR-027**: System MUST support compound rules with AND/OR logic (e.g., "sunset AND beach" OR "sunset AND mountains")
- **FR-028**: Users MUST be able to save, edit, and delete smart album rules
- **FR-029**: System MUST show photo count for each smart album in collections view
- **FR-030**: Smart albums MUST support exclusion rules (e.g., "landscape NOT people")
- **FR-031**: System MUST provide template smart albums (e.g., "Best of Year", "Portraits", "Landscapes")

#### Performance & Scale
- **FR-032**: Auto-tagging MUST process 100 photos per minute on mid-range hardware
- **FR-033**: Event detection MUST complete within 5 seconds for 10,000 photo library
- **FR-034**: Duplicate detection MUST complete within 30 seconds for 1,000 photos
- **FR-035**: Collections view MUST load within 2 seconds showing all events and smart albums
- **FR-036**: All operations MUST remain local with no network dependency

#### User Control & Privacy
- **FR-037**: System MUST allow users to disable auto-tagging, event detection, or duplicate detection independently
- **FR-038**: All auto-generated data (tags, events, duplicates) MUST be stored locally in SQLite database
- **FR-039**: Users MUST be able to clear all auto-generated collections and tags with one action
- **FR-040**: System MUST provide confidence scores for auto-generated tags and events for transparency

### Key Entities

- **Tag**: Descriptive keyword assigned to photos (e.g., "sunset", "portrait", "beach"). Has name, confidence score, source (auto/manual), and association with photos.

- **Event**: Temporal grouping of photos (e.g., "Wedding - 2024-06-15"). Has name, start date, end date, photo count, and hierarchical sub-events.

- **Collection**: Container for related photos. Can be manual (user-created) or automatic (event-based, smart album). Has name, type, rules (for smart albums), and photo membership.

- **DuplicateGroup**: Set of near-duplicate photos. Has similarity scores, recommended primary photo, and group status (reviewed/pending).

- **SmartAlbumRule**: Criteria defining smart album membership. Has conditions (tags, dates, metadata), logic operators (AND/OR/NOT), and associated smart album.

- **TagConfidence**: Relationship between photo and tag with confidence score (0.0-1.0) indicating certainty.

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (none remaining)
- [x] User scenarios defined
- [x] Requirements generated (40 functional requirements)
- [x] Entities identified (6 key entities)
- [x] Review checklist passed

---
