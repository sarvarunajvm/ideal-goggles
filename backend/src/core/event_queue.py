"""Event queue system for coordinating workers and background tasks."""

import asyncio
import contextlib
import json
import logging
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from queue import PriorityQueue, Queue
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events in the system."""

    # File system events
    FILE_DISCOVERED = "file_discovered"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"

    # Processing events
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_FAILED = "processing_failed"

    # Indexing events
    INDEX_STARTED = "index_started"
    INDEX_PROGRESS = "index_progress"
    INDEX_COMPLETED = "index_completed"
    INDEX_FAILED = "index_failed"

    # Search events
    SEARCH_REQUESTED = "search_requested"
    SEARCH_COMPLETED = "search_completed"

    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    WORKER_STARTED = "worker_started"
    WORKER_STOPPED = "worker_stopped"

    # Background tasks
    OPTIMIZATION_REQUESTED = "optimization_requested"
    BACKUP_REQUESTED = "backup_requested"
    CLEANUP_REQUESTED = "cleanup_requested"


class Priority(Enum):
    """Event priority levels."""

    CRITICAL = 1  # System critical events
    HIGH = 2  # User-triggered events
    NORMAL = 3  # Regular processing
    LOW = 4  # Background tasks
    CLEANUP = 5  # Cleanup operations


@dataclass
class Event:
    """Event data structure."""

    id: str
    type: EventType
    priority: Priority
    data: dict[str, Any]
    created_at: datetime
    scheduled_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3
    correlation_id: str | None = None
    source: str | None = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now()

    def __lt__(self, other):
        """For priority queue ordering."""
        if not isinstance(other, Event):
            return NotImplemented

        # First compare by scheduled time (if set)
        if self.scheduled_at and other.scheduled_at:
            if self.scheduled_at != other.scheduled_at:
                return self.scheduled_at < other.scheduled_at
        elif self.scheduled_at:
            return False  # Scheduled events come after immediate events
        elif other.scheduled_at:
            return True  # Immediate events come before scheduled events

        # Then by priority
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value

        # Finally by creation time
        return self.created_at < other.created_at

    def is_due(self) -> bool:
        """Check if event is due for processing."""
        if not self.scheduled_at:
            return True
        return datetime.now() >= self.scheduled_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": (
                self.scheduled_at.isoformat() if self.scheduled_at else None
            ),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "correlation_id": self.correlation_id,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            priority=Priority(data["priority"]),
            data=data["data"],
            created_at=datetime.fromisoformat(data["created_at"]),
            scheduled_at=(
                datetime.fromisoformat(data["scheduled_at"])
                if data.get("scheduled_at")
                else None
            ),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            correlation_id=data.get("correlation_id"),
            source=data.get("source"),
        )


class EventHandler:
    """Base class for event handlers."""

    def __init__(self, name: str):
        self.name = name

    async def handle(self, event: Event) -> bool:
        """
        Handle an event.

        Args:
            event: Event to handle

        Returns:
            True if handled successfully, False to retry
        """
        raise NotImplementedError

    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the event."""
        return True


class EventQueue:
    """
    Advanced event queue system for coordinating workers and background tasks.

    Features:
    - Priority-based event processing
    - Scheduled/delayed events
    - Event correlation and tracking
    - Retry mechanism with exponential backoff
    - Dead letter queue for failed events
    - Performance monitoring
    """

    def __init__(self, max_workers: int = 10, enable_persistence: bool = True):
        self.max_workers = max_workers
        self.enable_persistence = enable_persistence

        # Queues
        self._event_queue = PriorityQueue()
        self._dead_letter_queue = Queue()
        self._scheduled_events: list[Event] = []

        # Thread management
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="EventWorker"
        )
        self._running = False
        self._scheduler_task: asyncio.Task | None = None
        self._worker_tasks: set[asyncio.Task] = set()

        # Event handlers
        self._handlers: dict[EventType, list[EventHandler]] = {}
        self._middleware: list[Callable[[Event], bool]] = []

        # Statistics
        self._stats = {
            "total_processed": 0,
            "total_failed": 0,
            "processing_times": [],
            "queue_size": 0,
            "active_workers": 0,
        }

        # Thread safety
        self._lock = threading.RLock()

        logger.info(f"Event queue initialized with {max_workers} workers")

    def add_handler(self, event_type: EventType, handler: EventHandler):
        """Add an event handler for a specific event type."""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)

        logger.info(f"Added handler {handler.name} for {event_type.value}")

    def add_middleware(self, middleware: Callable[[Event], bool]):
        """
        Add middleware that runs before event processing.

        Args:
            middleware: Function that takes an event and returns True to continue processing
        """
        self._middleware.append(middleware)
        logger.info("Added event middleware")

    def publish(
        self,
        event_type: EventType,
        data: dict[str, Any],
        priority: Priority = Priority.NORMAL,
        delay: timedelta | None = None,
        correlation_id: str | None = None,
        source: str | None = None,
    ) -> str:
        """
        Publish an event to the queue.

        Args:
            event_type: Type of event
            data: Event data
            priority: Event priority
            delay: Optional delay before processing
            correlation_id: Optional correlation ID
            source: Optional source identifier

        Returns:
            Event ID
        """
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            priority=priority,
            data=data,
            created_at=datetime.now(),
            scheduled_at=datetime.now() + delay if delay else None,
            correlation_id=correlation_id,
            source=source,
        )

        return self._enqueue_event(event)

    def _enqueue_event(self, event: Event) -> str:
        """Internal method to enqueue an event."""
        with self._lock:
            if event.scheduled_at and event.scheduled_at > datetime.now():
                # Add to scheduled events
                self._scheduled_events.append(event)
                self._scheduled_events.sort(
                    key=lambda e: e.scheduled_at or datetime.max.replace(tzinfo=None)
                )
            else:
                # Add to immediate queue
                self._event_queue.put(event)
                self._stats["queue_size"] = self._event_queue.qsize()

        logger.debug(f"Enqueued event {event.id} of type {event.type.value}")
        return event.id

    def schedule_event(
        self,
        event_type: EventType,
        data: dict[str, Any],
        scheduled_at: datetime,
        priority: Priority = Priority.NORMAL,
        correlation_id: str | None = None,
    ) -> str:
        """
        Schedule an event for future processing.

        Args:
            event_type: Type of event
            data: Event data
            scheduled_at: When to process the event
            priority: Event priority
            correlation_id: Optional correlation ID

        Returns:
            Event ID
        """
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            priority=priority,
            data=data,
            created_at=datetime.now(),
            scheduled_at=scheduled_at,
            correlation_id=correlation_id,
        )

        return self._enqueue_event(event)

    async def start(self):
        """Start the event queue processing."""
        if self._running:
            return

        self._running = True

        # Start scheduler for delayed events
        self._scheduler_task = asyncio.create_task(self._schedule_loop())

        # Start worker tasks
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.add(task)

        logger.info("Event queue started")

    async def stop(self, timeout: float = 30.0):
        """Stop the event queue processing."""
        self._running = False

        # Cancel scheduler
        if self._scheduler_task:
            self._scheduler_task.cancel()
            with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                await asyncio.wait_for(self._scheduler_task, timeout=5.0)

        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()

        if self._worker_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._worker_tasks, return_exceptions=True),
                    timeout=timeout,
                )
            except TimeoutError:
                logger.warning("Some worker tasks did not stop within timeout")

        # Shutdown thread pool
        self._executor.shutdown(wait=True)

        logger.info("Event queue stopped")

    async def _schedule_loop(self):
        """Background loop for processing scheduled events."""
        while self._running:
            try:
                with self._lock:
                    due_events = []

                    # Find events that are due
                    remaining_events = []
                    for event in self._scheduled_events:
                        if event.is_due():
                            due_events.append(event)
                        else:
                            remaining_events.append(event)

                    self._scheduled_events = remaining_events

                    # Move due events to processing queue
                    for event in due_events:
                        self._event_queue.put(event)
                        self._stats["queue_size"] = self._event_queue.qsize()

                # Sleep until next check
                await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in schedule loop: {e}")
                await asyncio.sleep(5.0)

    async def _worker_loop(self, worker_name: str):
        """Worker loop for processing events."""
        while self._running:
            try:
                # Get next event (with timeout to allow for shutdown)
                try:
                    # Run the blocking get() in executor to allow cancellation
                    loop = asyncio.get_event_loop()
                    event = await loop.run_in_executor(
                        None, lambda: self._event_queue.get(timeout=0.1)
                    )
                    with self._lock:
                        self._stats["queue_size"] = self._event_queue.qsize()
                        self._stats["active_workers"] += 1
                except:
                    # Check if we should continue or break
                    await asyncio.sleep(0.1)
                    continue  # Timeout or queue empty

                try:
                    # Process the event
                    await self._process_event(event, worker_name)
                finally:
                    with self._lock:
                        self._stats["active_workers"] -= 1
                    self._event_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in worker {worker_name}: {e}")
                await asyncio.sleep(1.0)

    async def _process_event(self, event: Event, worker_name: str):
        """Process a single event."""
        start_time = time.time()

        try:
            logger.debug(
                f"Worker {worker_name} processing event {event.id} ({event.type.value})"
            )

            # Run middleware
            for middleware in self._middleware:
                if not middleware(event):
                    logger.debug(f"Middleware blocked event {event.id}")
                    return

            # Find handlers
            handlers = self._handlers.get(event.type, [])
            if not handlers:
                logger.warning(f"No handlers found for event type {event.type.value}")
                return

            # Process with all applicable handlers
            success = True
            for handler in handlers:
                if handler.can_handle(event):
                    try:
                        result = await handler.handle(event)
                        if not result:
                            success = False
                            break
                    except Exception as e:
                        logger.exception(
                            f"Handler {handler.name} failed for event {event.id}: {e}"
                        )
                        success = False
                        break

            if success:
                with self._lock:
                    self._stats["total_processed"] += 1
                    processing_time = time.time() - start_time
                    self._stats["processing_times"].append(processing_time)

                    # Keep only last 1000 processing times for moving average
                    if len(self._stats["processing_times"]) > 1000:
                        self._stats["processing_times"] = self._stats[
                            "processing_times"
                        ][-1000:]

                logger.debug(
                    f"Event {event.id} processed successfully in {processing_time:.3f}s"
                )
            else:
                await self._handle_failed_event(event)

        except Exception as e:
            logger.exception(f"Unexpected error processing event {event.id}: {e}")
            await self._handle_failed_event(event)

    async def _handle_failed_event(self, event: Event):
        """Handle a failed event with retry logic."""
        event.retry_count += 1

        if event.retry_count <= event.max_retries:
            # Retry with exponential backoff
            delay_seconds = 2**event.retry_count
            retry_at = datetime.now() + timedelta(seconds=delay_seconds)

            event.scheduled_at = retry_at
            self._enqueue_event(event)

            logger.warning(
                f"Event {event.id} failed, retrying in {delay_seconds}s (attempt {event.retry_count}/{event.max_retries})"
            )
        else:
            # Move to dead letter queue
            self._dead_letter_queue.put(event)
            with self._lock:
                self._stats["total_failed"] += 1

            logger.error(
                f"Event {event.id} failed permanently after {event.max_retries} retries"
            )

    def get_statistics(self) -> dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            avg_processing_time = 0.0
            if self._stats["processing_times"]:
                avg_processing_time = sum(self._stats["processing_times"]) / len(
                    self._stats["processing_times"]
                )

            return {
                "total_processed": self._stats["total_processed"],
                "total_failed": self._stats["total_failed"],
                "queue_size": self._stats["queue_size"],
                "scheduled_events": len(self._scheduled_events),
                "dead_letter_queue_size": self._dead_letter_queue.qsize(),
                "active_workers": self._stats["active_workers"],
                "max_workers": self.max_workers,
                "average_processing_time": avg_processing_time,
                "is_running": self._running,
            }

    def get_dead_letter_events(self) -> list[Event]:
        """Get events from the dead letter queue."""
        events = []
        while not self._dead_letter_queue.empty():
            try:
                events.append(self._dead_letter_queue.get_nowait())
            except:
                break
        return events

    def clear_dead_letter_queue(self):
        """Clear the dead letter queue."""
        while not self._dead_letter_queue.empty():
            try:
                self._dead_letter_queue.get_nowait()
            except:
                break
        logger.info("Dead letter queue cleared")


# Global event queue instance
_event_queue: EventQueue | None = None


def get_event_queue() -> EventQueue:
    """Get the global event queue instance."""
    global _event_queue
    if _event_queue is None:
        _event_queue = EventQueue()
    return _event_queue


def publish_event(
    event_type: EventType,
    data: dict[str, Any],
    priority: Priority = Priority.NORMAL,
    delay: timedelta | None = None,
    correlation_id: str | None = None,
    source: str | None = None,
) -> str:
    """Convenience function to publish an event."""
    queue = get_event_queue()
    return queue.publish(event_type, data, priority, delay, correlation_id, source)
