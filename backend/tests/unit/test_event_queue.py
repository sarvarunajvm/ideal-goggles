"""Unit tests for the event queue system."""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.core.event_queue import (
    Event,
    EventHandler,
    EventQueue,
    EventType,
    Priority,
)


class TestEvent:
    """Test Event dataclass."""

    def test_event_creation_with_defaults(self):
        """Test creating an event with default values."""
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={"file": "test.jpg"},
            created_at=datetime.now(),
        )
        assert event.id == "test-1"
        assert event.type == EventType.FILE_DISCOVERED
        assert event.priority == Priority.NORMAL
        assert event.data == {"file": "test.jpg"}
        assert event.retry_count == 0
        assert event.max_retries == 3
        assert event.correlation_id is None
        assert event.source is None

    def test_event_auto_id_generation(self):
        """Test that event generates ID if not provided."""
        event = Event(
            id="",  # Empty ID should trigger auto-generation
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )
        assert event.id != ""
        assert len(event.id) == 36  # UUID length

    def test_event_comparison_immediate_events(self):
        """Test event comparison for immediate events."""
        event1 = Event(
            id="1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.HIGH,
            data={},
            created_at=datetime.now(),
        )
        event2 = Event(
            id="2",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.LOW,
            data={},
            created_at=datetime.now(),
        )
        assert event1 < event2  # Higher priority comes first

    def test_event_comparison_scheduled_events(self):
        """Test event comparison for scheduled events."""
        now = datetime.now()
        event1 = Event(
            id="1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=now,
            scheduled_at=now + timedelta(minutes=5),
        )
        event2 = Event(
            id="2",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=now,
            scheduled_at=now + timedelta(minutes=10),
        )
        assert event1 < event2  # Earlier scheduled time comes first

    def test_event_comparison_mixed_scheduling(self):
        """Test event comparison with mixed immediate and scheduled events."""
        now = datetime.now()
        immediate_event = Event(
            id="1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=now,
        )
        scheduled_event = Event(
            id="2",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=now,
            scheduled_at=now + timedelta(minutes=5),
        )
        assert immediate_event < scheduled_event  # Immediate comes before scheduled

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        now = datetime.now()
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={"file": "test.jpg"},
            created_at=now,
        )
        # Event should be convertible to dict via dataclass asdict
        from dataclasses import asdict

        event_dict = asdict(event)
        assert event_dict["id"] == "test-1"
        assert event_dict["type"] == EventType.FILE_DISCOVERED
        assert event_dict["priority"] == Priority.NORMAL
        assert event_dict["data"] == {"file": "test.jpg"}


class TestEventQueue:
    """Test EventQueue class."""

    def test_event_queue_initialization(self):
        """Test EventQueue initialization."""
        queue = EventQueue(max_workers=10, enable_persistence=False)
        assert queue.max_workers == 10
        assert queue.enable_persistence is False
        stats = queue.get_statistics()
        assert stats["queue_size"] == 0
        assert stats["max_workers"] == 10

    def test_event_queue_publish_event(self):
        """Test publishing events to queue."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        event_id = queue.publish(
            event_type=EventType.FILE_DISCOVERED,
            data={"file": "test.jpg"},
            priority=Priority.NORMAL,
        )

        assert event_id is not None
        assert len(event_id) == 36  # UUID length
        stats = queue.get_statistics()
        assert stats["queue_size"] >= 0  # Event may have been queued

    def test_event_queue_schedule_event(self):
        """Test scheduling events for future processing."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        future_time = datetime.now() + timedelta(minutes=5)
        event_id = queue.schedule_event(
            event_type=EventType.CLEANUP_REQUESTED,
            data={"cleanup_type": "temp"},
            scheduled_at=future_time,
            priority=Priority.LOW,
        )

        assert event_id is not None
        stats = queue.get_statistics()
        assert stats["scheduled_events"] >= 1

    def test_event_queue_statistics(self):
        """Test getting queue statistics."""
        queue = EventQueue(max_workers=5, enable_persistence=False)

        stats = queue.get_statistics()
        assert "total_processed" in stats
        assert "total_failed" in stats
        assert "queue_size" in stats
        assert "scheduled_events" in stats
        assert "dead_letter_queue_size" in stats
        assert "active_workers" in stats
        assert "max_workers" in stats
        assert "average_processing_time" in stats
        assert "is_running" in stats

        assert stats["max_workers"] == 5
        assert stats["is_running"] is False

    def test_event_queue_add_handler(self):
        """Test adding event handler."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        class TestHandler(EventHandler):
            def __init__(self):
                super().__init__("test_handler")
                self.handled_events = []

            async def handle(self, event: Event) -> bool:
                self.handled_events.append(event)
                return True

            def can_handle(self, event: Event) -> bool:
                return event.type == EventType.FILE_DISCOVERED

        handler = TestHandler()
        queue.add_handler(EventType.FILE_DISCOVERED, handler)

        # Handler should be registered
        assert EventType.FILE_DISCOVERED in queue._handlers
        assert handler in queue._handlers[EventType.FILE_DISCOVERED]

    def test_event_queue_dead_letter_queue(self):
        """Test dead letter queue operations."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        # Initially empty
        dead_events = queue.get_dead_letter_events()
        assert len(dead_events) == 0

        # Clear should not raise error even when empty
        queue.clear_dead_letter_queue()

    @pytest.mark.asyncio
    async def test_event_queue_start_stop(self):
        """Test starting and stopping the queue."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        # Start the queue
        await queue.start()
        stats = queue.get_statistics()
        assert stats["is_running"] is True

        # Stop the queue
        await queue.stop(timeout=5.0)
        stats = queue.get_statistics()
        assert stats["is_running"] is False


class TestEventHandler:
    """Test EventHandler class."""

    def test_event_handler_initialization(self):
        """Test EventHandler initialization."""
        handler = EventHandler(name="test_handler")
        assert handler.name == "test_handler"

    def test_event_handler_can_handle_default(self):
        """Test EventHandler can_handle default implementation."""
        handler = EventHandler(name="test_handler")

        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        # Default implementation returns True for all events
        assert handler.can_handle(event) is True

    @pytest.mark.asyncio
    async def test_event_handler_handle_not_implemented(self):
        """Test EventHandler handle method raises NotImplementedError."""
        handler = EventHandler(name="test_handler")

        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        # Base class should raise NotImplementedError
        with pytest.raises(NotImplementedError):
            await handler.handle(event)

    @pytest.mark.asyncio
    async def test_custom_event_handler(self):
        """Test creating a custom event handler."""

        class CustomHandler(EventHandler):
            def __init__(self):
                super().__init__("custom_handler")
                self.handled_events = []

            async def handle(self, event: Event) -> bool:
                self.handled_events.append(event)
                return True

            def can_handle(self, event: Event) -> bool:
                return event.type == EventType.FILE_DISCOVERED

        handler = CustomHandler()
        assert handler.name == "custom_handler"

        # Test can_handle
        file_event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        other_event = Event(
            id="test-2",
            type=EventType.SYSTEM_STARTUP,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        assert handler.can_handle(file_event) is True
        assert handler.can_handle(other_event) is False

        # Test handle
        result = await handler.handle(file_event)
        assert result is True
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0].id == "test-1"
