#!/usr/bin/env python3
"""Test script to generate embeddings for indexed photos."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.connection import get_database_manager
from src.workers.embedding_worker import OptimizedCLIPWorker
from src.models.photo import Photo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Generate embeddings for all photos in database."""

    # Get database manager
    db_manager = get_database_manager()

    # Get all photos from database
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT id, path FROM photos")
        rows = cursor.fetchall()

    if not rows:
        print("No photos found in database")
        return

    print(f"Found {len(rows)} photos in database")

    # Create Photo objects
    photos = []
    for row in rows:
        photo = Photo(id=row['id'], path=row['path'])
        photos.append(photo)
        print(f"  - {photo.path}")

    # Initialize CLIP worker
    print("\nInitializing CLIP worker...")
    try:
        worker = OptimizedCLIPWorker()
        print("CLIP worker initialized successfully")
    except Exception as e:
        print(f"Failed to initialize CLIP worker: {e}")
        return

    # Generate embeddings
    print("\nGenerating embeddings...")
    embeddings = await worker.generate_batch_optimized(photos, batch_size=4)

    # Save embeddings to database
    successful = 0
    for photo, embedding in zip(photos, embeddings):
        if embedding:
            try:
                # Save to database
                with db_manager.get_transaction() as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO embeddings
                        (file_id, clip_vector, embedding_model, processed_at)
                        VALUES (?, ?, ?, datetime('now'))
                        """,
                        (photo.id, embedding.clip_vector, embedding.embedding_model)
                    )
                successful += 1
                print(f"✓ Saved embedding for {photo.path}")
            except Exception as e:
                print(f"✗ Failed to save embedding for {photo.path}: {e}")
        else:
            print(f"✗ No embedding generated for {photo.path}")

    print(f"\n{'='*50}")
    print(f"Successfully generated and saved {successful}/{len(photos)} embeddings")

    # Verify embeddings in database
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM embeddings")
        count = cursor.fetchone()['count']
        print(f"Total embeddings in database: {count}")

if __name__ == "__main__":
    asyncio.run(main())