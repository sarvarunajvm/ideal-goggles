"""File crawler and watcher service for photo indexing."""

import os
import logging
import asyncio
from pathlib import Path
from typing import List, Set, Dict, Callable, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import hashlib
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

from ..models.photo import Photo

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Result of a crawl operation."""
    total_files: int = 0
    new_files: int = 0
    modified_files: int = 0
    deleted_files: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    error_details: List[str] = None

    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []


class PhotoFileHandler(FileSystemEventHandler):
    """File system event handler for photo files."""

    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}

    def __init__(self, crawler: 'FileCrawler'):
        self.crawler = crawler
        self.last_event_time = {}
        self.debounce_delay = 1.0  # seconds

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and self._is_photo_file(event.src_path):
            self._debounced_event('created', event.src_path)

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and self._is_photo_file(event.src_path):
            self._debounced_event('modified', event.src_path)

    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory and self._is_photo_file(event.src_path):
            self._debounced_event('deleted', event.src_path)

    def on_moved(self, event):
        """Handle file move events."""
        if not event.is_directory:
            if self._is_photo_file(event.src_path):
                self._debounced_event('deleted', event.src_path)
            if self._is_photo_file(event.dest_path):
                self._debounced_event('created', event.dest_path)

    def _is_photo_file(self, file_path: str) -> bool:
        """Check if file is a supported photo format."""
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _debounced_event(self, event_type: str, file_path: str):
        """Debounce file events to avoid duplicate processing."""
        current_time = time.time()
        event_key = f"{event_type}:{file_path}"

        # Check if we should debounce this event
        if event_key in self.last_event_time:
            if current_time - self.last_event_time[event_key] < self.debounce_delay:
                return

        self.last_event_time[event_key] = current_time

        # Queue the event for processing
        try:
            if event_type == 'created':
                asyncio.run_coroutine_threadsafe(
                    self.crawler.handle_file_created(file_path),
                    self.crawler.event_loop
                )
            elif event_type == 'modified':
                asyncio.run_coroutine_threadsafe(
                    self.crawler.handle_file_modified(file_path),
                    self.crawler.event_loop
                )
            elif event_type == 'deleted':
                asyncio.run_coroutine_threadsafe(
                    self.crawler.handle_file_deleted(file_path),
                    self.crawler.event_loop
                )
        except RuntimeError:
            # Event loop might be closed
            logger.warning(f"Could not queue {event_type} event for {file_path}")


class FileCrawler:
    """File crawler for discovering and monitoring photo files."""

    def __init__(self, event_loop: asyncio.AbstractEventLoop = None):
        self.root_paths: Set[str] = set()
        self.observers: List[Observer] = []
        self.is_watching = False
        self.is_crawling = False
        self.crawl_callbacks: List[Callable] = []
        self.watch_callbacks: List[Callable] = []
        self.event_loop = event_loop or asyncio.get_event_loop()

        # Statistics
        self.last_crawl_result: Optional[CrawlResult] = None

    def add_root_path(self, path: str):
        """Add a root path for crawling."""
        path_obj = Path(path)
        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {path}")
        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        self.root_paths.add(str(path_obj.absolute()))
        logger.info(f"Added root path: {path}")

    def remove_root_path(self, path: str):
        """Remove a root path."""
        abs_path = str(Path(path).absolute())
        self.root_paths.discard(abs_path)
        logger.info(f"Removed root path: {path}")

    def add_crawl_callback(self, callback: Callable):
        """Add callback for crawl events."""
        self.crawl_callbacks.append(callback)

    def add_watch_callback(self, callback: Callable):
        """Add callback for file watch events."""
        self.watch_callbacks.append(callback)

    async def crawl_all_paths(self, force_full_crawl: bool = False) -> CrawlResult:
        """Crawl all root paths for photo files."""
        if self.is_crawling:
            raise RuntimeError("Crawl already in progress")

        self.is_crawling = True
        start_time = time.time()

        result = CrawlResult()

        try:
            for root_path in self.root_paths:
                logger.info(f"Crawling path: {root_path}")

                async for file_result in self._crawl_directory(root_path, force_full_crawl):
                    result.total_files += 1

                    if file_result['status'] == 'new':
                        result.new_files += 1
                        await self._notify_crawl_callbacks('file_discovered', file_result)
                    elif file_result['status'] == 'modified':
                        result.modified_files += 1
                        await self._notify_crawl_callbacks('file_modified', file_result)
                    elif file_result['status'] == 'error':
                        result.errors += 1
                        result.error_details.append(file_result['error'])
                        await self._notify_crawl_callbacks('file_error', file_result)

                    # Yield control periodically
                    if result.total_files % 100 == 0:
                        await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Crawl failed: {e}")
            result.errors += 1
            result.error_details.append(str(e))

        finally:
            result.duration_seconds = time.time() - start_time
            self.is_crawling = False
            self.last_crawl_result = result

        logger.info(f"Crawl completed: {result.total_files} files, "
                   f"{result.new_files} new, {result.modified_files} modified, "
                   f"{result.errors} errors in {result.duration_seconds:.2f}s")

        return result

    async def _crawl_directory(self, root_path: str, force_full_crawl: bool) -> AsyncGenerator[Dict, None]:
        """Crawl a single directory recursively."""
        try:
            for root, dirs, files in os.walk(root_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    if file.startswith('.'):
                        continue

                    file_path = os.path.join(root, file)
                    file_ext = Path(file).suffix.lower()

                    # Check if it's a supported photo format
                    if file_ext not in PhotoFileHandler.SUPPORTED_EXTENSIONS:
                        continue

                    try:
                        # Check if file exists and get basic info
                        if not os.path.exists(file_path):
                            continue

                        stat = os.stat(file_path)
                        if stat.st_size == 0:
                            continue

                        # Create photo object for validation
                        photo = Photo.from_file_path(file_path)

                        # Determine if this is new or modified
                        # This would typically check against database
                        status = 'new'  # Simplified for now
                        if not force_full_crawl:
                            # Check if file needs reprocessing
                            if photo.needs_reprocessing():
                                status = 'modified'

                        yield {
                            'path': file_path,
                            'photo': photo,
                            'status': status,
                            'size': stat.st_size,
                            'modified_time': stat.st_mtime,
                        }

                    except Exception as e:
                        logger.warning(f"Error processing file {file_path}: {e}")
                        yield {
                            'path': file_path,
                            'status': 'error',
                            'error': str(e),
                        }

                    # Yield control every few files
                    await asyncio.sleep(0)

        except PermissionError as e:
            logger.warning(f"Permission denied accessing {root_path}: {e}")
            yield {
                'path': root_path,
                'status': 'error',
                'error': f"Permission denied: {e}",
            }

    def start_watching(self):
        """Start watching root paths for file changes."""
        if self.is_watching:
            return

        if not self.root_paths:
            raise ValueError("No root paths configured for watching")

        logger.info("Starting file system watching")

        for root_path in self.root_paths:
            observer = Observer()
            handler = PhotoFileHandler(self)
            observer.schedule(handler, root_path, recursive=True)
            observer.start()
            self.observers.append(observer)

        self.is_watching = True
        logger.info(f"Watching {len(self.root_paths)} root paths")

    def stop_watching(self):
        """Stop watching file system changes."""
        if not self.is_watching:
            return

        logger.info("Stopping file system watching")

        for observer in self.observers:
            observer.stop()
            observer.join(timeout=5.0)

        self.observers.clear()
        self.is_watching = False
        logger.info("File system watching stopped")

    async def handle_file_created(self, file_path: str):
        """Handle file creation event."""
        try:
            photo = Photo.from_file_path(file_path)
            await self._notify_watch_callbacks('file_created', {
                'path': file_path,
                'photo': photo,
            })
        except Exception as e:
            logger.warning(f"Error handling file creation {file_path}: {e}")

    async def handle_file_modified(self, file_path: str):
        """Handle file modification event."""
        try:
            photo = Photo.from_file_path(file_path)
            await self._notify_watch_callbacks('file_modified', {
                'path': file_path,
                'photo': photo,
            })
        except Exception as e:
            logger.warning(f"Error handling file modification {file_path}: {e}")

    async def handle_file_deleted(self, file_path: str):
        """Handle file deletion event."""
        await self._notify_watch_callbacks('file_deleted', {
            'path': file_path,
        })

    async def _notify_crawl_callbacks(self, event_type: str, data: Dict):
        """Notify crawl callbacks of events."""
        for callback in self.crawl_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in crawl callback: {e}")

    async def _notify_watch_callbacks(self, event_type: str, data: Dict):
        """Notify watch callbacks of events."""
        for callback in self.watch_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in watch callback: {e}")

    def get_statistics(self) -> Dict:
        """Get crawler statistics."""
        return {
            'root_paths': list(self.root_paths),
            'is_watching': self.is_watching,
            'is_crawling': self.is_crawling,
            'watchers_active': len(self.observers),
            'last_crawl_result': self.last_crawl_result.to_dict() if self.last_crawl_result else None,
        }


class BatchFileCrawler:
    """Batch file crawler for efficient processing of large directories."""

    def __init__(self, batch_size: int = 1000, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers

    async def crawl_in_batches(self, root_paths: List[str],
                              callback: Callable,
                              force_full_crawl: bool = False) -> CrawlResult:
        """Crawl files in batches for memory efficiency."""
        result = CrawlResult()
        start_time = time.time()

        try:
            # Collect all files first
            all_files = []
            for root_path in root_paths:
                async for file_data in self._collect_files(root_path):
                    all_files.append(file_data)

            result.total_files = len(all_files)

            # Process in batches
            for i in range(0, len(all_files), self.batch_size):
                batch = all_files[i:i + self.batch_size]
                batch_result = await self._process_batch(batch, callback)

                result.new_files += batch_result.new_files
                result.modified_files += batch_result.modified_files
                result.errors += batch_result.errors
                result.error_details.extend(batch_result.error_details)

                # Progress update
                progress = (i + len(batch)) / len(all_files) * 100
                logger.info(f"Batch processing progress: {progress:.1f}%")

                # Yield control between batches
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Batch crawl failed: {e}")
            result.errors += 1
            result.error_details.append(str(e))

        finally:
            result.duration_seconds = time.time() - start_time

        return result

    async def _collect_files(self, root_path: str) -> AsyncGenerator[Dict, None]:
        """Collect file information without processing."""
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                if file.startswith('.'):
                    continue

                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()

                if file_ext in PhotoFileHandler.SUPPORTED_EXTENSIONS:
                    try:
                        stat = os.stat(file_path)
                        yield {
                            'path': file_path,
                            'size': stat.st_size,
                            'modified_time': stat.st_mtime,
                        }
                    except OSError:
                        continue

                await asyncio.sleep(0)

    async def _process_batch(self, batch: List[Dict], callback: Callable) -> CrawlResult:
        """Process a batch of files."""
        result = CrawlResult()

        tasks = []
        for file_data in batch:
            task = asyncio.create_task(self._process_file(file_data, callback))
            tasks.append(task)

        # Process with limited concurrency
        semaphore = asyncio.Semaphore(self.max_workers)

        async def process_with_semaphore(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(
            *[process_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        for file_result in results:
            if isinstance(file_result, Exception):
                result.errors += 1
                result.error_details.append(str(file_result))
            elif file_result:
                if file_result.get('status') == 'new':
                    result.new_files += 1
                elif file_result.get('status') == 'modified':
                    result.modified_files += 1

        return result

    async def _process_file(self, file_data: Dict, callback: Callable) -> Dict:
        """Process a single file."""
        try:
            photo = Photo.from_file_path(file_data['path'])
            status = 'new'  # Simplified

            file_result = {
                'path': file_data['path'],
                'photo': photo,
                'status': status,
            }

            if callback:
                if asyncio.iscoroutinefunction(callback):
                    await callback(file_result)
                else:
                    callback(file_result)

            return file_result

        except Exception as e:
            logger.warning(f"Error processing file {file_data['path']}: {e}")
            return {
                'path': file_data['path'],
                'status': 'error',
                'error': str(e),
            }