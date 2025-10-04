# API Contracts Summary

## Endpoints to Implement

### Tags API (`tags-api.yaml` - detailed)
- GET /api/tags - List all tags
- POST /api/tags - Create manual tag
- GET /api/tags/{id} - Tag details
- DELETE /api/tags/{id} - Delete tag
- GET /api/photos/{id}/tags - Get photo tags
- POST /api/photos/{id}/tags - Add tag to photo
- DELETE /api/photos/{id}/tags - Remove tag

### Events API
- GET /api/events - List all events
- POST /api/events/detect - Trigger event detection
- GET /api/events/{id} - Event details with photos
- PUT /api/events/{id} - Rename event
- DELETE /api/events/{id} - Delete event
- POST /api/events/merge - Merge multiple events
- POST /api/events/{id}/split - Split event

### Collections API
- GET /api/collections - List all collections
- POST /api/collections - Create manual collection
- GET /api/collections/{id} - Collection details
- PUT /api/collections/{id} - Update collection
- DELETE /api/collections/{id} - Delete collection
- POST /api/collections/{id}/photos - Add photo to collection
- DELETE /api/collections/{id}/photos/{photo_id} - Remove photo

### Smart Albums API
- GET /api/smart-albums - List smart albums
- POST /api/smart-albums - Create smart album with rules
- GET /api/smart-albums/{id} - Get album with dynamic membership
- PUT /api/smart-albums/{id}/rules - Update rules
- DELETE /api/smart-albums/{id} - Delete smart album
- POST /api/smart-albums/{id}/evaluate - Force re-evaluation

### Duplicates API
- GET /api/duplicates - List duplicate groups
- POST /api/duplicates/detect - Trigger duplicate detection
- GET /api/duplicates/{group_id} - Group details
- POST /api/duplicates/{group_id}/resolve - Mark as resolved
- DELETE /api/duplicates/{group_id}/photos/{photo_id} - Delete duplicate

## Contract Test Files (to be created)

```
backend/tests/contract/
├── test_tags_api.py
├── test_events_api.py
├── test_collections_api.py
├── test_smart_albums_api.py
└── test_duplicates_api.py
```

Each test file validates request/response schemas per OpenAPI spec.
