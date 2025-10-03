"""Unit tests for TextSearchService."""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from src.services.text_search import TextSearchService


class TestTextSearchService:
    """Test TextSearchService functionality."""

    @pytest.fixture
    def text_search_service(self):
        """Create TextSearchService instance with mocked database."""
        with patch("src.services.text_search.get_database_manager") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            service = TextSearchService()
            service.db_manager = mock_db
            return service, mock_db

    def test_process_search_query_basic(self, text_search_service):
        """Test basic search query processing."""
        service, _ = text_search_service

        # Test simple query
        processed = service._process_search_query("vacation photos")
        assert processed == "vacation* AND photos*"

    def test_process_search_query_short_words(self, text_search_service):
        """Test search query processing with short words."""
        service, _ = text_search_service

        # Short words should not get asterisk
        processed = service._process_search_query("my cat")
        assert processed == "my AND cat"

    def test_process_search_query_special_characters(self, text_search_service):
        """Test search query processing with special characters."""
        service, _ = text_search_service

        # Special characters should be removed
        processed = service._process_search_query("beach@sunset#2023!")
        assert processed == "beach* AND sunset* AND 2023*"

    def test_process_search_query_empty(self, text_search_service):
        """Test processing empty search query."""
        service, _ = text_search_service

        processed = service._process_search_query("")
        assert processed == ""

    def test_process_search_query_very_short_words(self, text_search_service):
        """Test processing query with very short words that get filtered."""
        service, _ = text_search_service

        processed = service._process_search_query("a b cd efgh")
        assert processed == "cd AND efgh*"

    def test_search_photos_basic(self, text_search_service):
        """Test basic photo search functionality."""
        service, mock_db = text_search_service

        # Mock search results
        mock_search_results = [
            (
                1,
                "/path/photo1.jpg",
                "/path",
                "photo1.jpg",
                1024,
                1640995200.0,
                1640995200.0,
                "hash1",
                "/thumb/1.jpg",
                "2022-01-01",
                "Canon",
                "EOS R5",
                "vacation text",
                0.9,
                2.5,
            ),
        ]

        mock_count_results = [(1,)]

        mock_db.execute_query.side_effect = [mock_search_results, mock_count_results]

        result = service.search_photos("vacation", limit=10, offset=0)

        assert result["query"] == "vacation"
        assert result["total_count"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["filename"] == "photo1.jpg"
        # The match_types contains "ocr" since the match was in OCR text column
        assert "ocr" in result["results"][0]["match_types"]

    def test_search_photos_with_filters(self, text_search_service):
        """Test photo search with various filters."""
        service, mock_db = text_search_service

        mock_db.execute_query.side_effect = [[], [(0,)]]

        # Test with all filters
        service.search_photos(
            query="vacation",
            folders=["/photos/2022", "/photos/2023"],
            date_range=(date(2022, 1, 1), date(2022, 12, 31)),
            file_types=[".jpg", ".png"],
            limit=20,
            offset=10,
        )

        # Verify database was called
        assert mock_db.execute_query.call_count == 2

        # Check that parameters include filters
        search_call_args = mock_db.execute_query.call_args_list[0]
        search_query, search_params = search_call_args[0]

        # Should contain folder filter
        assert "p.folder LIKE ?" in search_query
        assert "/photos/2022%" in search_params

        # Should contain date filter
        assert "date(e.shot_dt) BETWEEN ? AND ?" in search_query
        assert "2022-01-01" in search_params
        assert "2022-12-31" in search_params

        # Should contain file type filter
        assert "p.ext = ?" in search_query
        assert ".jpg" in search_params

    def test_search_photos_no_results(self, text_search_service):
        """Test photo search with no results."""
        service, mock_db = text_search_service

        mock_db.execute_query.side_effect = [[], [(0,)]]

        result = service.search_photos("nonexistent", limit=10, offset=0)

        assert result["query"] == "nonexistent"
        assert result["total_count"] == 0
        assert len(result["results"]) == 0

    def test_search_photos_error_handling(self, text_search_service):
        """Test error handling in photo search."""
        service, mock_db = text_search_service

        # Mock database error
        mock_db.execute_query.side_effect = Exception("Database error")

        result = service.search_photos("test", limit=10, offset=0)

        assert result["query"] == "test"
        assert result["total_count"] == 0
        assert len(result["results"]) == 0
        assert "error" in result
        assert "Database error" in result["error"]

    def test_generate_snippet_basic(self, text_search_service):
        """Test text snippet generation."""
        service, _ = text_search_service

        text = "This is a long text about vacation photos from the beach. We had a great time taking pictures."
        query = "vacation"

        snippet = service._generate_snippet(text, query, max_length=50)

        assert "vacation" in snippet.lower()
        # The snippet may be slightly longer due to word boundary handling
        assert len(snippet) <= 60  # Allow some buffer for word boundary handling

    def test_generate_snippet_no_match(self, text_search_service):
        """Test snippet generation when query not found in text."""
        service, _ = text_search_service

        text = "This is some text without the search term."
        query = "vacation"

        snippet = service._generate_snippet(text, query, max_length=20)

        assert snippet == "This is some text wi..."

    def test_generate_snippet_empty_inputs(self, text_search_service):
        """Test snippet generation with empty inputs."""
        service, _ = text_search_service

        # Empty text
        snippet = service._generate_snippet("", "query")
        assert snippet == ""

        # Empty query
        snippet = service._generate_snippet("some text", "")
        assert snippet == "some text"

    def test_get_search_suggestions(self, text_search_service):
        """Test getting search suggestions."""
        service, mock_db = text_search_service

        mock_filename_results = [("vacation_photo.jpg",), ("vacation_video.jpg",)]
        mock_camera_results = [("Canon EOS R5",)]

        mock_db.execute_query.side_effect = [mock_filename_results, mock_camera_results]

        suggestions = service.get_search_suggestions("vac", limit=5)

        assert len(suggestions) == 3
        assert "vacation_photo.jpg" in suggestions
        assert "vacation_video.jpg" in suggestions
        assert "Canon EOS R5" in suggestions

    def test_get_search_suggestions_short_query(self, text_search_service):
        """Test search suggestions with too short query."""
        service, _ = text_search_service

        suggestions = service.get_search_suggestions("v", limit=5)
        assert len(suggestions) == 0

    def test_get_search_suggestions_error_handling(self, text_search_service):
        """Test error handling in search suggestions."""
        service, mock_db = text_search_service

        mock_db.execute_query.side_effect = Exception("Database error")

        suggestions = service.get_search_suggestions("test", limit=5)
        assert len(suggestions) == 0

    def test_get_popular_searches(self, text_search_service):
        """Test getting popular search terms."""
        service, mock_db = text_search_service

        mock_camera_results = [("Canon EOS R5", 10), ("Nikon D850", 5)]
        mock_ext_results = [(".jpg", 100), (".png", 50)]

        mock_db.execute_query.side_effect = [mock_camera_results, mock_ext_results]

        popular_searches = service.get_popular_searches(limit=4)

        assert len(popular_searches) == 4
        assert {
            "term": "Canon EOS R5",
            "type": "camera_model",
            "count": 10,
        } in popular_searches
        assert {
            "term": ".jpg",
            "type": "file_extension",
            "count": 100,
        } in popular_searches

    def test_get_popular_searches_error_handling(self, text_search_service):
        """Test error handling in popular searches."""
        service, mock_db = text_search_service

        mock_db.execute_query.side_effect = Exception("Database error")

        popular_searches = service.get_popular_searches(limit=5)
        assert len(popular_searches) == 0

    def test_get_search_statistics(self, text_search_service):
        """Test getting search statistics."""
        service, mock_db = text_search_service

        mock_stats_results = [(1000, 800, 900, 150.5)]
        mock_db.execute_query.return_value = mock_stats_results

        stats = service.get_search_statistics()

        assert stats["total_photos"] == 1000
        assert stats["photos_with_ocr"] == 800
        assert stats["photos_with_exif"] == 900
        assert stats["avg_ocr_length"] == 150.5
        assert stats["ocr_coverage"] == 80.0  # 800/1000 * 100
        assert stats["exif_coverage"] == 90.0  # 900/1000 * 100

    def test_get_search_statistics_error_handling(self, text_search_service):
        """Test error handling in search statistics."""
        service, mock_db = text_search_service

        mock_db.execute_query.side_effect = Exception("Database error")

        stats = service.get_search_statistics()
        assert len(stats) == 0

    def test_build_search_query_text_conditions(self, text_search_service):
        """Test building search query with text conditions."""
        service, _ = text_search_service

        query, params = service._build_search_query(
            processed_query="vacation*",
            folders=None,
            date_range=None,
            file_types=None,
            limit=10,
            offset=0,
        )

        # Should contain text search conditions
        assert "p.filename LIKE ?" in query
        assert "p.folder LIKE ?" in query
        assert "(e.camera_make LIKE ? OR e.camera_model LIKE ?)" in query
        assert "p.id IN (SELECT file_id FROM ocr WHERE ocr MATCH ?)" in query

        # Should have appropriate parameters
        assert "%vacation%" in params
        assert "vacation*" in params

    def test_build_search_query_no_conditions(self, text_search_service):
        """Test building search query with no search conditions."""
        service, _ = text_search_service

        query, params = service._build_search_query(
            processed_query="",
            folders=None,
            date_range=None,
            file_types=None,
            limit=10,
            offset=5,
        )

        # Should not contain WHERE clause
        assert "WHERE" not in query

        # Should have limit and offset
        assert "LIMIT ? OFFSET ?" in query
        assert params[-2:] == [10, 5]

    def test_process_search_results_with_matches(self, text_search_service):
        """Test processing search results with various match types."""
        service, _ = text_search_service

        mock_results = [
            (
                1,
                "/test/vacation.jpg",
                "/test",
                "vacation.jpg",
                1024,
                1640995200.0,
                1640995300.0,
                "hash1",
                "/thumb/1.jpg",
                "2022-01-01",
                "Canon",
                "EOS R5",
                "beach vacation",
                0.9,
                2.5,
            ),
        ]

        processed = service._process_search_results(mock_results, "vacation")

        assert len(processed) == 1
        result = processed[0]

        assert result["file_id"] == 1
        assert result["filename"] == "vacation.jpg"
        assert "filename" in result["match_types"]
        assert "ocr" in result["match_types"]
        assert result["snippet"] is not None
        assert "vacation" in result["snippet"]
        assert result["relevance_score"] > 0

    def test_process_search_results_no_matches(self, text_search_service):
        """Test processing search results with no specific matches."""
        service, _ = text_search_service

        mock_results = [
            (
                1,
                "/test/photo.jpg",
                "/test",
                "photo.jpg",
                1024,
                1640995200.0,
                1640995300.0,
                "hash1",
                "/thumb/1.jpg",
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        ]

        processed = service._process_search_results(mock_results, "vacation")

        assert len(processed) == 1
        result = processed[0]

        assert result["file_id"] == 1
        assert result["filename"] == "photo.jpg"
        assert len(result["match_types"]) == 0
        assert result["relevance_score"] == 0.1  # Default score
