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
        queue = EventQueue(max_size=100)
        assert queue.max_size == 100
        assert queue.is_empty()
        assert queue.size() == 0

    def test_event_queue_put_and_get(self):
        """Test putting and getting events from queue."""
        queue = EventQueue()
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        queue.put(event)
        assert queue.size() == 1
        assert not queue.is_empty()

        retrieved_event = queue.get()
        assert retrieved_event.id == "test-1"
        assert queue.is_empty()

    def test_event_queue_priority_ordering(self):
        """Test that events are retrieved in priority order."""
        queue = EventQueue()

        low_priority = Event(
            id="low",
            type=EventType.CLEANUP_REQUESTED,
            priority=Priority.LOW,
            data={},
            created_at=datetime.now(),
        )
        high_priority = Event(
            id="high",
            type=EventType.SEARCH_REQUESTED,
            priority=Priority.HIGH,
            data={},
            created_at=datetime.now(),
        )
        normal_priority = Event(
            id="normal",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        # Add in random order
        queue.put(low_priority)
        queue.put(normal_priority)
        queue.put(high_priority)

        # Should get high priority first
        assert queue.get().id == "high"
        assert queue.get().id == "normal"
        assert queue.get().id == "low"

    def test_event_queue_peek(self):
        """Test peeking at next event without removing it."""
        queue = EventQueue()
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        queue.put(event)
        peeked = queue.peek()
        assert peeked.id == "test-1"
        assert queue.size() == 1  # Event should still be in queue

    def test_event_queue_clear(self):
        """Test clearing the queue."""
        queue = EventQueue()
        for i in range(5):
            queue.put(
                Event(
                    id=f"test-{i}",
                    type=EventType.FILE_DISCOVERED,
                    priority=Priority.NORMAL,
                    data={},
                    created_at=datetime.now(),
                )
            )

        assert queue.size() == 5
        queue.clear()
        assert queue.is_empty()

    def test_event_queue_get_timeout(self):
        """Test getting from empty queue with timeout."""
        queue = EventQueue()
        retrieved = queue.get(timeout=0.1)
        assert retrieved is None

    def test_event_queue_get_all(self):
        """Test getting all events from queue."""
        queue = EventQueue()
        events = []
        for i in range(3):
            event = Event(
                id=f"test-{i}",
                type=EventType.FILE_DISCOVERED,
                priority=Priority.NORMAL,
                data={},
                created_at=datetime.now(),
            )
            events.append(event)
            queue.put(event)

        all_events = queue.get_all()
        assert len(all_events) == 3
        assert queue.is_empty()


class TestEventHandler:
    """Test EventHandler class."""

    def test_event_handler_initialization(self):
        """Test EventHandler initialization."""
        handler = EventHandler(name="test_handler")
        assert handler.name == "test_handler"
        assert handler.event_types == []
        assert handler.handler_func is None

    def test_event_handler_with_callback(self):
        """Test EventHandler with callback function."""
        callback = Mock()
        handler = EventHandler(
            name="test_handler",
            event_types=[EventType.FILE_DISCOVERED],
            handler_func=callback
        )

        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        handler.handle(event)
        callback.assert_called_once_with(event)

    def test_event_handler_can_handle(self):
        """Test EventHandler can_handle method."""
        handler = EventHandler(
            name="test_handler",
            event_types=[EventType.FILE_DISCOVERED, EventType.FILE_MODIFIED]
        )

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

        assert handler.can_handle(file_event)
        assert not handler.can_handle(other_event)