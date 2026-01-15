#!/usr/bin/env python3
"""Initialize test database with schema"""

import logging
import os
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def init_test_database():
    """Initialize test database with schema"""
    # Create test database directory
    db_dir = Path("test_data")
    db_dir.mkdir(exist_ok=True)

    # Database path
    db_path = db_dir / "photos.db"

    # Remove existing database
    if db_path.exists():
        db_path.unlink()

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Read and execute migration
    migration_path = Path("src/db/migrations/001_initial_schema.sql")
    with open(migration_path) as f:
        migration_sql = f.read()

    # Execute migration
    cursor.executescript(migration_sql)
    conn.commit()

    logger.info(f"Database initialized at: {db_path.absolute()}")

    # Set environment variable for backend
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path.absolute()}"
    logger.info(f"DATABASE_URL set to: {os.environ['DATABASE_URL']}")

    conn.close()


if __name__ == "__main__":
    init_test_database()
