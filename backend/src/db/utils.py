"""Database utility functions for Ideal Goggles."""

from typing import Any, Optional

from ..core.logging_config import get_logger
from .connection import get_database_manager

logger = get_logger(__name__)


class DatabaseHelper:
    """Helper class for common database operations."""

    @staticmethod
    def get_config(key: str | None = None) -> dict[str, Any]:
        """Get configuration from database.

        Args:
            key: Specific config key to retrieve (optional)

        Returns:
            dict: Configuration dictionary
        """
        db_manager = get_database_manager()

        if key:
            query = "SELECT value FROM config WHERE key = ?"
            rows = db_manager.execute_query(query, (key,))
            if rows:
                import json

                return json.loads(rows[0][0])
            return {}

        # Get all config
        query = "SELECT key, value FROM config"
        rows = db_manager.execute_query(query)

        config = {}
        for row in rows:
            import json

            try:
                config[row[0]] = json.loads(row[1])
            except (json.JSONDecodeError, TypeError):
                config[row[0]] = row[1]

        return config

    @staticmethod
    def update_config(updates: dict[str, Any]) -> None:
        """Update configuration in database.

        Args:
            updates: Dictionary of config updates
        """
        import json

        db_manager = get_database_manager()

        for key, value in updates.items():
            # Serialize value to JSON
            json_value = json.dumps(value)

            # Upsert config value
            query = """
                INSERT INTO config (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """
            db_manager.execute_update(query, (key, json_value))

        logger.info(f"Updated config keys: {list(updates.keys())}")

    @staticmethod
    def get_photo_count(indexed_only: bool = False) -> int:
        """Get total count of photos.

        Args:
            indexed_only: Whether to count only indexed photos

        Returns:
            int: Photo count
        """
        db_manager = get_database_manager()

        if indexed_only:
            query = "SELECT COUNT(*) FROM photos WHERE indexed_at IS NOT NULL"
        else:
            query = "SELECT COUNT(*) FROM photos"

        rows = db_manager.execute_query(query)
        return rows[0][0] if rows else 0

    @staticmethod
    def get_database_stats() -> dict[str, Any]:
        """Get comprehensive database statistics.

        Returns:
            dict: Database statistics
        """
        db_manager = get_database_manager()

        stats = {}

        # Table counts
        tables = [
            ("photos", "total_photos"),
            ("exif", "photos_with_exif"),
            ("thumbnails", "photos_with_thumbnails"),
            ("embeddings", "photos_with_embeddings"),
            ("faces", "total_faces"),
            ("people", "enrolled_people"),
        ]

        for table, stat_name in tables:
            query = f"SELECT COUNT(*) FROM {table}"
            rows = db_manager.execute_query(query)
            stats[stat_name] = rows[0][0] if rows else 0

        # Indexed photos
        query = "SELECT COUNT(*) FROM photos WHERE indexed_at IS NOT NULL"
        rows = db_manager.execute_query(query)
        stats["indexed_photos"] = rows[0][0] if rows else 0

        # Database file size
        from pathlib import Path

        db_path = db_manager.db_path if hasattr(db_manager, "db_path") else None
        if db_path and Path(db_path).exists():
            stats["database_size_bytes"] = Path(db_path).stat().st_size
            stats["database_size_mb"] = round(
                stats["database_size_bytes"] / (1024 * 1024), 2
            )

        return stats

    @staticmethod
    def search_photos_basic(
        query: str | None = None,
        folder: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Basic photo search without complex dependencies.

        Args:
            query: Search query for filename/folder
            folder: Folder path filter
            limit: Maximum results
            offset: Results offset

        Returns:
            list: List of photo dictionaries
        """
        db_manager = get_database_manager()

        where_conditions = []
        params = []

        if query:
            where_conditions.append("(filename LIKE ? OR folder LIKE ?)")
            search_pattern = f"%{query}%"
            params.extend([search_pattern, search_pattern])

        if folder:
            where_conditions.append("folder LIKE ?")
            params.append(f"{folder}%")

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        query = f"""
            SELECT
                p.id, p.path, p.folder, p.filename, p.size,
                p.created_ts, p.modified_ts, p.indexed_at,
                t.thumb_path, e.shot_dt
            FROM photos p
            LEFT JOIN thumbnails t ON p.id = t.file_id
            LEFT JOIN exif e ON p.id = e.file_id
            {where_clause}
            ORDER BY p.modified_ts DESC
            LIMIT ? OFFSET ?
        """

        params.extend([limit, offset])
        rows = db_manager.execute_query(query, params)

        return [
            {
                "file_id": row[0],
                "path": row[1],
                "folder": row[2],
                "filename": row[3],
                "size": row[4],
                "created_ts": row[5],
                "modified_ts": row[6],
                "indexed_at": row[7],
                "thumb_path": row[8],
                "shot_dt": row[9],
            }
            for row in rows
        ]

    @staticmethod
    def cleanup_orphaned_records() -> dict[str, int]:
        """Clean up orphaned records in the database.

        Returns:
            dict: Counts of cleaned records by table
        """
        db_manager = get_database_manager()
        cleaned = {}

        # Clean orphaned thumbnails
        query = """
            DELETE FROM thumbnails
            WHERE file_id NOT IN (SELECT id FROM photos)
        """
        result = db_manager.execute_update(query)
        cleaned["thumbnails"] = result

        # Clean orphaned EXIF
        query = """
            DELETE FROM exif
            WHERE file_id NOT IN (SELECT id FROM photos)
        """
        result = db_manager.execute_update(query)
        cleaned["exif"] = result

        # Clean orphaned embeddings
        query = """
            DELETE FROM embeddings
            WHERE file_id NOT IN (SELECT id FROM photos)
        """
        result = db_manager.execute_update(query)
        cleaned["embeddings"] = result

        # Clean orphaned faces
        query = """
            DELETE FROM faces
            WHERE file_id NOT IN (SELECT id FROM photos)
        """
        result = db_manager.execute_update(query)
        cleaned["faces"] = result

        logger.info(f"Cleaned orphaned records: {cleaned}")
        return cleaned
