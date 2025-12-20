"""Advanced FAISS index management with optimization and persistence features."""

import asyncio
import json
import logging
import os
import shutil
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np

from ..core.config import get_settings

# Expose a module-level 'faiss' symbol so tests can patch it
try:  # pragma: no cover - import guard
    import faiss as _faiss  # type: ignore[import-not-found]

    faiss = _faiss
except Exception:  # pragma: no cover - faiss may not be installed in tests

    class _FaissPlaceholder:  # type: ignore[misc]
        pass

    faiss = _FaissPlaceholder()  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class FAISSIndexManager:
    """
    Advanced FAISS index manager with optimization, persistence, and monitoring.

    Features:
    - Automatic index optimization based on collection size
    - Backup and restore capabilities
    - Performance monitoring and statistics
    - Index compression and optimization
    - Memory usage optimization
    """

    def __init__(self, vector_search_service=None):
        self.settings = get_settings()
        self.vector_service = vector_search_service

        # Paths
        self.base_path = Path(self.settings.app_data_dir) / "faiss"
        self.index_path = self.base_path / "index.faiss"
        self.metadata_path = self.base_path / "metadata.json"
        self.backup_path = self.base_path / "backups"
        self.stats_path = self.base_path / "stats.json"

        # Ensure directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)

        # Optimization parameters
        self.auto_optimize_threshold = 50000  # Vectors before auto-optimization
        self.backup_interval_hours = 24  # Backup frequency
        self.max_backups = 7  # Keep last 7 backups

        # Performance tracking
        self.stats = {
            "last_optimization": None,
            "last_backup": None,
            "total_vectors": 0,
            "search_count": 0,
            "average_search_time": 0.0,
            "index_size_mb": 0.0,
            "memory_usage_mb": 0.0,
        }

        # Thread safety
        self._lock = threading.RLock()
        self._optimization_in_progress = False
        self._stop_event = threading.Event()

        # Load existing stats
        self._load_stats()

        # Start background optimization scheduler
        self._start_background_scheduler()

    def _load_stats(self):
        """Load performance statistics from disk."""
        try:
            if self.stats_path.exists():
                with open(self.stats_path) as f:
                    saved_stats = json.load(f)
                    self.stats.update(saved_stats)
                    logger.info("Loaded FAISS index statistics")
        except Exception as e:
            logger.warning(f"Failed to load stats: {e}")

    def _save_stats(self):
        """Save performance statistics to disk."""
        try:
            # Update current stats
            if self.vector_service and hasattr(self.vector_service, "index"):
                if self.vector_service.index:
                    self.stats["total_vectors"] = self.vector_service.index.ntotal

                    # Calculate index size
                    if self.index_path.exists():
                        self.stats["index_size_mb"] = self.index_path.stat().st_size / (
                            1024 * 1024
                        )

            with open(self.stats_path, "w") as f:
                json.dump(self.stats, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save stats: {e}")

    def should_optimize(self) -> bool:
        """Check if index should be optimized."""
        if not self.vector_service or not self.vector_service.index:
            return False

        # Check if optimization is already in progress
        if self._optimization_in_progress:
            return False

        num_vectors = self.vector_service.index.ntotal

        # Optimize if we've crossed the threshold
        if num_vectors >= self.auto_optimize_threshold:
            # Check if we haven't optimized recently
            last_opt = self.stats.get("last_optimization")
            if not last_opt:
                return True

            # Parse last optimization time
            try:
                last_opt_time = datetime.fromisoformat(last_opt)
                # Only optimize if it's been more than 4 hours since last optimization
                return datetime.now() - last_opt_time > timedelta(hours=4)
            except (ValueError, TypeError):
                return True

        return False

    async def optimize_index(self, force: bool = False) -> bool:
        """
        Optimize the FAISS index for better performance.

        Args:
            force: Force optimization even if not needed

        Returns:
            True if optimization was performed
        """
        if not force and not self.should_optimize():
            return False

        if self._optimization_in_progress:
            logger.info("Index optimization already in progress")
            return False

        with self._lock:
            self._optimization_in_progress = True

        try:
            return await self._perform_optimization()
        finally:
            self._optimization_in_progress = False

    async def _perform_optimization(self) -> bool:
        """Internal method to perform index optimization."""
        try:
            if getattr(faiss, "IndexFlatL2", None) is None:
                msg = "faiss not available"
                raise RuntimeError(msg)

            if not self.vector_service or not self.vector_service.index:
                logger.warning("No vector service or index available for optimization")
                return False

            logger.info("Starting FAISS index optimization")
            start_time = time.time()

            index = self.vector_service.index
            num_vectors = index.ntotal

            if num_vectors == 0:
                logger.info("No vectors to optimize")
                return False

            # Create backup before optimization
            await self.create_backup("pre_optimization")

            # Determine optimal index type based on collection size
            if num_vectors < 10000:
                # Small collection: keep flat index
                logger.info("Small collection, keeping flat index")
                optimized_index = self._optimize_flat_index(index)
            elif num_vectors < 200000:
                # Medium collection: use IVF with minimal compression
                logger.info("Medium collection, creating IVF index")
                optimized_index = self._create_ivf_index(index, use_pq=False)
            else:
                # Large collection: use IVF with PQ compression
                logger.info("Large collection, creating IVF-PQ index")
                optimized_index = self._create_ivf_index(index, use_pq=True)

            if optimized_index:
                # Replace the index
                self.vector_service.index = optimized_index

                # Save optimized index
                await self._save_optimized_index()

                # Update stats
                self.stats["last_optimization"] = datetime.now().isoformat()
                self._save_stats()

                optimization_time = time.time() - start_time
                logger.info(f"Index optimization completed in {optimization_time:.2f}s")
                return True
            logger.warning("Index optimization failed")
            return False

        except Exception as e:
            logger.exception(f"Error during index optimization: {e}")
            return False

    def _optimize_flat_index(self, index):
        """Optimize a flat index by rebuilding it."""
        try:
            if getattr(faiss, "IndexFlatL2", None) is None:
                msg = "faiss not available"
                raise RuntimeError(msg)

            # Extract all vectors
            vectors = index.reconstruct_n(0, index.ntotal)

            # Create new optimized flat index
            if index.d == 512:  # CLIP embeddings
                new_index = faiss.IndexFlatIP(index.d)
            else:
                new_index = faiss.IndexFlatL2(index.d)

            # Add vectors in batches for better memory efficiency
            batch_size = 10000
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                new_index.add(batch)

            return new_index

        except Exception as e:
            logger.exception(f"Failed to optimize flat index: {e}")
            return None

    def _create_ivf_index(self, index, use_pq: bool = False):
        """Create an optimized IVF index."""
        try:
            if getattr(faiss, "IndexFlatL2", None) is None:
                msg = "faiss not available"
                raise RuntimeError(msg)

            num_vectors = index.ntotal
            dimension = index.d

            # Calculate optimal number of clusters
            nlist = min(4096, max(100, int(np.sqrt(num_vectors))))

            # Extract all vectors for training
            vectors = index.reconstruct_n(0, num_vectors)

            # Create quantizer
            quantizer = (
                faiss.IndexFlatIP(dimension)
                if dimension == 512
                else faiss.IndexFlatL2(dimension)
            )

            if use_pq:
                # Use Product Quantization for large collections
                m = 64  # Number of subquantizers
                nbits = 8  # Bits per subquantizer
                new_index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, nbits)
            else:
                # Use regular IVF for medium collections
                new_index = faiss.IndexIVFFlat(quantizer, dimension, nlist)

            # Train the index
            logger.info(f"Training IVF index with {nlist} clusters")
            new_index.train(vectors)

            # Add vectors in batches
            batch_size = 10000
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                new_index.add(batch)

            # Optimize search parameters
            new_index.nprobe = min(100, nlist // 4)

            logger.info(
                f"Created IVF index with {nlist} clusters, nprobe={new_index.nprobe}"
            )
            return new_index

        except Exception as e:
            logger.exception(f"Failed to create IVF index: {e}")
            return None

    async def _save_optimized_index(self):
        """Save the optimized index to disk."""
        try:
            if not self.vector_service or not self.vector_service.index:
                return

            # Save using the vector service's save method
            success = self.vector_service.save_index()
            if success:
                logger.info("Optimized index saved successfully")
            else:
                logger.warning("Failed to save optimized index")

        except Exception as e:
            logger.exception(f"Error saving optimized index: {e}")

    async def create_backup(self, backup_name: str | None = None) -> bool:
        """
        Create a backup of the current index.

        Args:
            backup_name: Optional name for the backup

        Returns:
            True if backup was successful
        """
        try:
            if not self.vector_service:
                return False

            # Generate backup name if not provided
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            backup_dir = self.backup_path / backup_name
            backup_dir.mkdir(exist_ok=True)

            # Save current index state
            success = self.vector_service.save_index()
            if not success:
                logger.warning("Failed to save current index state")
                return False

            # Copy index files to backup location
            if self.vector_service.index_path and os.path.exists(
                self.vector_service.index_path
            ):
                shutil.copy2(self.vector_service.index_path, backup_dir / "index.faiss")

            if self.vector_service.metadata_path and os.path.exists(
                self.vector_service.metadata_path
            ):
                shutil.copy2(
                    self.vector_service.metadata_path, backup_dir / "metadata.pkl"
                )

            # Save backup metadata
            backup_info = {
                "created_at": datetime.now().isoformat(),
                "vector_count": (
                    self.vector_service.index.ntotal if self.vector_service.index else 0
                ),
                "index_type": (
                    str(type(self.vector_service.index))
                    if self.vector_service.index
                    else "None"
                ),
                "backup_name": backup_name,
            }

            with open(backup_dir / "info.json", "w") as f:
                json.dump(backup_info, f, indent=2)

            # Update stats
            self.stats["last_backup"] = datetime.now().isoformat()
            self._save_stats()

            # Clean up old backups
            await self._cleanup_old_backups()

            logger.info(f"Index backup created: {backup_name}")
            return True

        except Exception as e:
            logger.exception(f"Failed to create backup: {e}")
            return False

    async def restore_backup(self, backup_name: str) -> bool:
        """
        Restore index from a backup.

        Args:
            backup_name: Name of the backup to restore

        Returns:
            True if restore was successful
        """
        try:
            backup_dir = self.backup_path / backup_name

            if not backup_dir.exists():
                logger.error(f"Backup not found: {backup_name}")
                return False

            # Verify backup integrity
            index_file = backup_dir / "index.faiss"
            metadata_file = backup_dir / "metadata.pkl"

            if not index_file.exists():
                logger.error(f"Backup index file not found: {index_file}")
                return False

            # Create current backup before restoring
            await self.create_backup("pre_restore")

            # Copy backup files to current location
            if self.vector_service:
                if index_file.exists():
                    shutil.copy2(index_file, self.vector_service.index_path)

                if metadata_file.exists() and self.vector_service.metadata_path:
                    shutil.copy2(metadata_file, self.vector_service.metadata_path)

                # Reload the index
                self.vector_service._load_index()

            logger.info(f"Index restored from backup: {backup_name}")
            return True

        except Exception as e:
            logger.exception(f"Failed to restore backup: {e}")
            return False

    async def _cleanup_old_backups(self):
        """Remove old backups, keeping only the most recent ones."""
        try:
            if not self.backup_path.exists():
                return

            # Get all backup directories with their creation times
            backups = []
            for backup_dir in self.backup_path.iterdir():
                if backup_dir.is_dir():
                    info_file = backup_dir / "info.json"
                    if info_file.exists():
                        try:
                            with open(info_file) as f:
                                info = json.load(f)
                            created_at = datetime.fromisoformat(info["created_at"])
                            backups.append((created_at, backup_dir))
                        except Exception:
                            # If we can't parse the info, use directory modification time
                            backups.append(
                                (
                                    datetime.fromtimestamp(backup_dir.stat().st_mtime),
                                    backup_dir,
                                )
                            )

            # Sort by creation time (newest first)
            backups.sort(reverse=True)

            # Remove old backups
            for _, backup_dir in backups[self.max_backups :]:
                try:
                    shutil.rmtree(backup_dir)
                    logger.info(f"Removed old backup: {backup_dir.name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to remove old backup {backup_dir.name}: {e}"
                    )

        except Exception as e:
            logger.exception(f"Error cleaning up old backups: {e}")

    def get_performance_stats(self) -> dict:
        """Get current performance statistics."""
        # Update real-time stats
        if self.vector_service and hasattr(self.vector_service, "index"):
            if self.vector_service.index:
                self.stats["total_vectors"] = self.vector_service.index.ntotal

        # Calculate memory usage estimate
        if self.index_path.exists():
            self.stats["index_size_mb"] = self.index_path.stat().st_size / (1024 * 1024)

        return self.stats.copy()

    def record_search_time(self, search_time: float):
        """Record a search operation for performance tracking."""
        self.stats["search_count"] += 1

        # Update running average
        current_avg = self.stats["average_search_time"]

        # Use exponential moving average for recent performance
        alpha = 0.1  # Weight for new measurements
        self.stats["average_search_time"] = (
            alpha * search_time + (1 - alpha) * current_avg
        )

    def _start_background_scheduler(self):
        """Start background scheduler for automatic optimization and backups."""
        # Skip scheduler in tests to avoid thread leaks and race conditions
        if "PYTEST_CURRENT_TEST" in os.environ:
            return

        def scheduler():
            """Background scheduler loop."""
            while not self._stop_event.is_set():
                try:
                    # Check for automatic optimization
                    if self.should_optimize():
                        # Run in a dedicated loop inside this thread to avoid
                        # "no running event loop" errors.
                        asyncio.run(self.optimize_index())

                    # Check for automatic backup
                    last_backup = self.stats.get("last_backup")
                    should_backup = False

                    if not last_backup:
                        should_backup = True
                    else:
                        try:
                            last_backup_time = datetime.fromisoformat(last_backup)
                            should_backup = (
                                datetime.now() - last_backup_time
                                > timedelta(hours=self.backup_interval_hours)
                            )
                        except (ValueError, TypeError):
                            should_backup = True

                    if should_backup:
                        asyncio.run(self.create_backup())

                    # Save stats periodically
                    self._save_stats()

                except Exception as e:
                    logger.exception(f"Error in background scheduler: {e}")

                # Sleep for 1 hour before next check
                if self._stop_event.wait(3600):
                    break

        # Start scheduler in daemon thread
        scheduler_thread = threading.Thread(target=scheduler, daemon=True)
        scheduler_thread.start()

    async def shutdown(self):
        """Graceful shutdown of the manager."""
        try:
            # Signal scheduler to stop
            self._stop_event.set()

            # Save final stats
            self._save_stats()

            logger.info("FAISS index manager shutdown complete")

        except Exception as e:
            logger.exception(f"Error during shutdown: {e}")
