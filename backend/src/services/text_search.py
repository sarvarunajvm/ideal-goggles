"""Text search service using SQLite FTS5 for full-text search capabilities."""

import logging
import re
import sqlite3
from datetime import date, datetime
from typing import Any

from ..db.connection import get_database_manager

logger = logging.getLogger(__name__)


class TextSearchService:
    """Text search service using SQLite FTS5 for efficient full-text search."""

    def __init__(self):
        self.db_manager = get_database_manager()

    def search_photos(
        self,
        query: str,
        folders: list[str] | None = None,
        date_range: tuple[date, date] | None = None,
        file_types: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search photos using text query with optional filters.

        Args:
            query: Search query text
            folders: Folder paths to search within
            date_range: Date range tuple (start_date, end_date)
            file_types: File extensions to filter by
            limit: Maximum number of results
            offset: Results offset for pagination

        Returns:
            Search results with metadata
        """
        try:
            # Parse and prepare query
            processed_query = self._process_search_query(query)

            # Build search SQL
            search_sql, params = self._build_search_query(
                processed_query, folders, date_range, file_types, limit, offset
            )

            # Execute search
            start_time = datetime.now()
            results = self.db_manager.execute_query(search_sql, params)
            search_time = (datetime.now() - start_time).total_seconds()

            # Process results
            processed_results = self._process_search_results(results, query)

            # Get total count for pagination
            count_sql, count_params = self._build_count_query(
                processed_query, folders, date_range, file_types
            )
            count_result = self.db_manager.execute_query(count_sql, count_params)
            total_count = count_result[0][0] if count_result else 0

            return {
                "results": processed_results,
                "total_count": total_count,
                "query": query,
                "processed_query": processed_query,
                "search_time_ms": round(search_time * 1000, 2),
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.exception(f"Text search failed: {e}")
            return {
                "results": [],
                "total_count": 0,
                "query": query,
                "error": str(e),
                "search_time_ms": 0,
                "limit": limit,
                "offset": offset,
            }

    def _process_search_query(self, query: str) -> str:
        """
        Process and clean search query for FTS5.

        Args:
            query: Raw search query

        Returns:
            Processed query suitable for FTS5
        """
        if not query:
            return ""

        # Remove special characters that might break FTS5
        cleaned = re.sub(r'[^\w\s\-\'".]', " ", query)

        # Split into words and process
        words = cleaned.split()
        processed_words = []

        for word in words:
            word = word.strip()
            if len(word) < 2:  # Skip very short words
                continue

            # Add prefix search for longer words
            if len(word) > 3:
                processed_words.append(f"{word}*")
            else:
                processed_words.append(word)

        # Join with AND operator for FTS5
        return " AND ".join(processed_words)

    def _build_search_query(
        self,
        processed_query: str,
        folders: list[str] | None,
        date_range: tuple[date, date] | None,
        file_types: list[str] | None,
        limit: int,
        offset: int,
    ) -> tuple[str, list[Any]]:
        """Build the complete search SQL query."""
        params = []

        # Base query with FTS5 search
        base_query = """
            SELECT DISTINCT
                p.id,
                p.path,
                p.folder,
                p.filename,
                p.size,
                p.created_ts,
                p.modified_ts,
                p.sha1,
                t.thumb_path,
                e.shot_dt,
                e.camera_make,
                e.camera_model,
                o.text as ocr_text,
                o.confidence as ocr_confidence,
                bm25(ocr) as ocr_rank
            FROM photos p
            LEFT JOIN thumbnails t ON p.id = t.file_id
            LEFT JOIN exif e ON p.id = e.file_id
            LEFT JOIN ocr o ON p.id = o.file_id
        """

        # Build WHERE conditions
        where_conditions = []

        # Text search conditions
        if processed_query:
            text_conditions = []

            # Search in filename
            text_conditions.append("p.filename LIKE ?")
            params.append(f"%{processed_query.replace('*', '').replace(' AND ', ' ')}%")

            # Search in folder path
            text_conditions.append("p.folder LIKE ?")
            params.append(f"%{processed_query.replace('*', '').replace(' AND ', ' ')}%")

            # Search in EXIF data
            text_conditions.append("(e.camera_make LIKE ? OR e.camera_model LIKE ?)")
            search_pattern = (
                f"%{processed_query.replace('*', '').replace(' AND ', ' ')}%"
            )
            params.extend([search_pattern, search_pattern])

            # Search in OCR text using FTS5
            if processed_query.strip():
                text_conditions.append(
                    "p.id IN (SELECT file_id FROM ocr WHERE ocr MATCH ?)"
                )
                params.append(processed_query)

            # Combine text conditions with OR
            where_conditions.append(f"({' OR '.join(text_conditions)})")

        # Folder filter
        if folders:
            folder_conditions = []
            for folder in folders:
                folder_conditions.append("p.folder LIKE ?")
                params.append(f"{folder}%")

            if folder_conditions:
                where_conditions.append(f"({' OR '.join(folder_conditions)})")

        # Date range filter
        if date_range:
            start_date, end_date = date_range
            if start_date and end_date:
                where_conditions.append("date(e.shot_dt) BETWEEN ? AND ?")
                params.extend([start_date.isoformat(), end_date.isoformat()])
            elif start_date:
                where_conditions.append("date(e.shot_dt) >= ?")
                params.append(start_date.isoformat())
            elif end_date:
                where_conditions.append("date(e.shot_dt) <= ?")
                params.append(end_date.isoformat())

        # File type filter
        if file_types:
            type_conditions = []
            for file_type in file_types:
                type_conditions.append("p.ext = ?")
                params.append(file_type.lower())

            if type_conditions:
                where_conditions.append(f"({' OR '.join(type_conditions)})")

        # Combine query parts
        if where_conditions:
            full_query = f"{base_query} WHERE {' AND '.join(where_conditions)}"
        else:
            full_query = base_query

        # Add ordering and pagination
        full_query += """
            ORDER BY
                CASE
                    WHEN o.text IS NOT NULL THEN bm25(ocr)
                    ELSE 0
                END DESC,
                p.modified_ts DESC
            LIMIT ? OFFSET ?
        """

        params.extend([limit, offset])

        return full_query, params

    def _build_count_query(
        self,
        processed_query: str,
        folders: list[str] | None,
        date_range: tuple[date, date] | None,
        file_types: list[str] | None,
    ) -> tuple[str, list[Any]]:
        """Build count query for pagination."""
        params = []

        base_query = """
            SELECT COUNT(DISTINCT p.id)
            FROM photos p
            LEFT JOIN exif e ON p.id = e.file_id
            LEFT JOIN ocr o ON p.id = o.file_id
        """

        where_conditions = []

        # Text search conditions (same as main query)
        if processed_query:
            text_conditions = []

            text_conditions.append("p.filename LIKE ?")
            params.append(f"%{processed_query.replace('*', '').replace(' AND ', ' ')}%")

            text_conditions.append("p.folder LIKE ?")
            params.append(f"%{processed_query.replace('*', '').replace(' AND ', ' ')}%")

            text_conditions.append("(e.camera_make LIKE ? OR e.camera_model LIKE ?)")
            search_pattern = (
                f"%{processed_query.replace('*', '').replace(' AND ', ' ')}%"
            )
            params.extend([search_pattern, search_pattern])

            if processed_query.strip():
                text_conditions.append(
                    "p.id IN (SELECT file_id FROM ocr WHERE ocr MATCH ?)"
                )
                params.append(processed_query)

            where_conditions.append(f"({' OR '.join(text_conditions)})")

        # Apply same filters as main query
        if folders:
            folder_conditions = []
            for folder in folders:
                folder_conditions.append("p.folder LIKE ?")
                params.append(f"{folder}%")
            if folder_conditions:
                where_conditions.append(f"({' OR '.join(folder_conditions)})")

        if date_range:
            start_date, end_date = date_range
            if start_date and end_date:
                where_conditions.append("date(e.shot_dt) BETWEEN ? AND ?")
                params.extend([start_date.isoformat(), end_date.isoformat()])
            elif start_date:
                where_conditions.append("date(e.shot_dt) >= ?")
                params.append(start_date.isoformat())
            elif end_date:
                where_conditions.append("date(e.shot_dt) <= ?")
                params.append(end_date.isoformat())

        if file_types:
            type_conditions = []
            for file_type in file_types:
                type_conditions.append("p.ext = ?")
                params.append(file_type.lower())
            if type_conditions:
                where_conditions.append(f"({' OR '.join(type_conditions)})")

        if where_conditions:
            full_query = f"{base_query} WHERE {' AND '.join(where_conditions)}"
        else:
            full_query = base_query

        return full_query, params

    def _process_search_results(
        self, results: list[sqlite3.Row], original_query: str
    ) -> list[dict[str, Any]]:
        """Process raw search results into formatted output."""
        processed_results = []

        for row in results:
            # Determine match types and calculate relevance score
            match_types = []
            relevance_score = 0.0

            # Check filename match
            if original_query.lower() in row[3].lower():  # filename
                match_types.append("filename")
                relevance_score += 0.3

            # Check folder match
            if original_query.lower() in row[2].lower():  # folder
                match_types.append("folder")
                relevance_score += 0.2

            # Check EXIF match
            if (row[10] and original_query.lower() in row[10].lower()) or (
                row[11] and original_query.lower() in row[11].lower()
            ):
                match_types.append("exif")
                relevance_score += 0.2

            # Check OCR match
            if row[12]:  # ocr_text
                match_types.append("ocr")
                # Use FTS5 BM25 rank if available
                if row[14] and row[14] > 0:  # ocr_rank
                    relevance_score += min(0.5, row[14] / 10.0)
                else:
                    relevance_score += 0.3

            # Default score if no specific matches
            if not match_types:
                relevance_score = 0.1

            # Generate snippet for OCR matches
            snippet = None
            if "ocr" in match_types and row[12]:
                snippet = self._generate_snippet(row[12], original_query)

            result_item = {
                "file_id": row[0],
                "path": row[1],
                "folder": row[2],
                "filename": row[3],
                "size": row[4],
                "created_ts": row[5],
                "modified_ts": row[6],
                "sha1": row[7],
                "thumb_path": row[8],
                "shot_dt": row[9],
                "camera_make": row[10],
                "camera_model": row[11],
                "relevance_score": round(relevance_score, 3),
                "match_types": match_types,
                "snippet": snippet,
                "ocr_confidence": row[13] if row[13] else None,
            }

            processed_results.append(result_item)

        return processed_results

    def _generate_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """Generate a text snippet around the search query."""
        if not text or not query:
            return text[:max_length] if text else ""

        query_lower = query.lower()
        text_lower = text.lower()

        # Find the first occurrence of any query word
        query_words = query_lower.split()
        best_pos = -1

        for word in query_words:
            pos = text_lower.find(word)
            if pos != -1 and (best_pos == -1 or pos < best_pos):
                best_pos = pos

        if best_pos == -1:
            # No match found, return beginning of text
            return text[:max_length] + "..." if len(text) > max_length else text

        # Calculate snippet boundaries
        snippet_start = max(0, best_pos - max_length // 2)
        snippet_end = min(len(text), snippet_start + max_length)

        # Adjust start if we're near the end
        if snippet_end - snippet_start < max_length:
            snippet_start = max(0, snippet_end - max_length)

        snippet = text[snippet_start:snippet_end]

        # Add ellipsis if needed
        if snippet_start > 0:
            snippet = "..." + snippet
        if snippet_end < len(text):
            snippet = snippet + "..."

        return snippet

    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> list[str]:
        """
        Get search suggestions based on partial query.

        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions

        Returns:
            List of suggested queries
        """
        try:
            suggestions = []

            if len(partial_query) < 2:
                return suggestions

            # Get suggestions from filenames
            filename_query = """
                SELECT DISTINCT filename
                FROM photos
                WHERE filename LIKE ?
                ORDER BY filename
                LIMIT ?
            """

            filename_results = self.db_manager.execute_query(
                filename_query, (f"%{partial_query}%", limit // 2)
            )

            suggestions.extend(row[0] for row in filename_results)

            # Get suggestions from camera models
            camera_query = """
                SELECT DISTINCT camera_model
                FROM exif
                WHERE camera_model LIKE ? AND camera_model IS NOT NULL
                ORDER BY camera_model
                LIMIT ?
            """

            camera_results = self.db_manager.execute_query(
                camera_query, (f"%{partial_query}%", limit // 2)
            )

            for row in camera_results:
                if row[0] not in suggestions:
                    suggestions.append(row[0])

            return suggestions[:limit]

        except Exception as e:
            logger.exception(f"Failed to get search suggestions: {e}")
            return []

    def get_popular_searches(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get popular search terms based on frequency.

        This is a simplified implementation. In a real system,
        you'd track search queries and their frequency.

        Args:
            limit: Maximum number of results

        Returns:
            List of popular search terms with metadata
        """
        try:
            # Get most common camera models
            camera_query = """
                SELECT camera_model, COUNT(*) as count
                FROM exif
                WHERE camera_model IS NOT NULL
                GROUP BY camera_model
                ORDER BY count DESC
                LIMIT ?
            """

            camera_results = self.db_manager.execute_query(camera_query, (limit // 2,))

            popular_searches = [
                {"term": row[0], "type": "camera_model", "count": row[1]}
                for row in camera_results
            ]

            # Get most common file extensions
            ext_query = """
                SELECT ext, COUNT(*) as count
                FROM photos
                GROUP BY ext
                ORDER BY count DESC
                LIMIT ?
            """

            ext_results = self.db_manager.execute_query(ext_query, (limit // 2,))

            popular_searches.extend(
                [
                    {"term": row[0], "type": "file_extension", "count": row[1]}
                    for row in ext_results
                ]
            )

            return popular_searches[:limit]

        except Exception as e:
            logger.exception(f"Failed to get popular searches: {e}")
            return []

    def get_search_statistics(self) -> dict[str, Any]:
        """Get text search statistics."""
        try:
            # Get total searchable content
            stats_query = """
                SELECT
                    COUNT(DISTINCT p.id) as total_photos,
                    COUNT(DISTINCT o.file_id) as photos_with_ocr,
                    COUNT(DISTINCT e.file_id) as photos_with_exif,
                    AVG(LENGTH(o.text)) as avg_ocr_length
                FROM photos p
                LEFT JOIN ocr o ON p.id = o.file_id
                LEFT JOIN exif e ON p.id = e.file_id
            """

            results = self.db_manager.execute_query(stats_query)

            if results:
                row = results[0]
                return {
                    "total_photos": row[0],
                    "photos_with_ocr": row[1],
                    "photos_with_exif": row[2],
                    "avg_ocr_length": round(row[3], 2) if row[3] else 0,
                    "ocr_coverage": (
                        round((row[1] / row[0]) * 100, 2) if row[0] > 0 else 0
                    ),
                    "exif_coverage": (
                        round((row[2] / row[0]) * 100, 2) if row[0] > 0 else 0
                    ),
                }

            return {}

        except Exception as e:
            logger.exception(f"Failed to get search statistics: {e}")
            return {}


# Global instance
_text_search_service: TextSearchService | None = None


def get_text_search_service() -> TextSearchService:
    """Get or create the global text search service instance."""
    global _text_search_service
    if _text_search_service is None:
        _text_search_service = TextSearchService()
    return _text_search_service
