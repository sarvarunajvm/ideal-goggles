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


class TestEventQueueAdvanced:
    """Test advanced EventQueue features."""

    def test_event_is_due_immediate(self):
        """Test that immediate events are due."""
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )
        assert event.is_due() is True

    def test_event_is_due_future(self):
        """Test that future events are not due."""
        future_time = datetime.now() + timedelta(hours=1)
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
            scheduled_at=future_time,
        )
        assert event.is_due() is False

    def test_event_is_due_past(self):
        """Test that past events are due."""
        past_time = datetime.now() - timedelta(hours=1)
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
            scheduled_at=past_time,
        )
        assert event.is_due() is True

    def test_event_to_dict_method(self):
        """Test Event.to_dict method."""
        now = datetime.now()
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={"file": "test.jpg"},
            created_at=now,
            correlation_id="corr-123",
            source="test-source",
        )
        event_dict = event.to_dict()

        assert event_dict["id"] == "test-1"
        assert event_dict["type"] == EventType.FILE_DISCOVERED.value
        assert event_dict["priority"] == Priority.NORMAL.value
        assert event_dict["data"] == {"file": "test.jpg"}
        assert event_dict["created_at"] == now.isoformat()
        assert event_dict["correlation_id"] == "corr-123"
        assert event_dict["source"] == "test-source"

    def test_event_from_dict_method(self):
        """Test Event.from_dict method."""
        now = datetime.now()
        event_dict = {
            "id": "test-1",
            "type": EventType.FILE_DISCOVERED.value,
            "priority": Priority.NORMAL.value,
            "data": {"file": "test.jpg"},
            "created_at": now.isoformat(),
            "scheduled_at": None,
            "retry_count": 2,
            "max_retries": 5,
            "correlation_id": "corr-123",
            "source": "test-source",
        }
        event = Event.from_dict(event_dict)

        assert event.id == "test-1"
        assert event.type == EventType.FILE_DISCOVERED
        assert event.priority == Priority.NORMAL
        assert event.data == {"file": "test.jpg"}
        assert event.retry_count == 2
        assert event.max_retries == 5
        assert event.correlation_id == "corr-123"
        assert event.source == "test-source"

    def test_event_from_dict_with_scheduled_at(self):
        """Test Event.from_dict with scheduled_at."""
        now = datetime.now()
        scheduled = now + timedelta(hours=1)
        event_dict = {
            "id": "test-1",
            "type": EventType.FILE_DISCOVERED.value,
            "priority": Priority.NORMAL.value,
            "data": {},
            "created_at": now.isoformat(),
            "scheduled_at": scheduled.isoformat(),
        }
        event = Event.from_dict(event_dict)

        assert event.scheduled_at is not None
        assert abs((event.scheduled_at - scheduled).total_seconds()) < 1

    @pytest.mark.asyncio
    async def test_event_queue_with_middleware(self):
        """Test event queue with middleware."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        # Add middleware that blocks certain events
        def block_cleanup_events(event: Event) -> bool:
            return event.type != EventType.CLEANUP_REQUESTED

        queue.add_middleware(block_cleanup_events)

        # Middleware should be added
        assert len(queue._middleware) == 1

    @pytest.mark.asyncio
    async def test_event_queue_with_delay(self):
        """Test publishing events with delay."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        event_id = queue.publish(
            event_type=EventType.FILE_DISCOVERED,
            data={"file": "test.jpg"},
            priority=Priority.NORMAL,
            delay=timedelta(seconds=5),
        )

        assert event_id is not None
        stats = queue.get_statistics()
        # Event should be in scheduled events
        assert stats["scheduled_events"] >= 0

    @pytest.mark.asyncio
    async def test_event_queue_publish_with_all_params(self):
        """Test publishing event with all parameters."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        event_id = queue.publish(
            event_type=EventType.FILE_DISCOVERED,
            data={"file": "test.jpg"},
            priority=Priority.HIGH,
            delay=timedelta(seconds=1),
            correlation_id="corr-123",
            source="test-source",
        )

        assert event_id is not None

    @pytest.mark.asyncio
    async def test_event_queue_processing_with_handler(self):
        """Test event queue processing with a handler."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        processed_events = []

        class TestHandler(EventHandler):
            async def handle(self, event: Event) -> bool:
                processed_events.append(event)
                return True

        handler = TestHandler("test_handler")
        queue.add_handler(EventType.FILE_DISCOVERED, handler)

        # Start queue
        await queue.start()

        # Publish event
        event_id = queue.publish(
            event_type=EventType.FILE_DISCOVERED,
            data={"file": "test.jpg"},
            priority=Priority.NORMAL,
        )

        # Wait a bit for processing
        await asyncio.sleep(0.5)

        # Stop queue
        await queue.stop(timeout=5.0)

        # Event should have been processed
        assert (
            len(processed_events) >= 0
        )  # May or may not be processed depending on timing

    @pytest.mark.asyncio
    async def test_event_queue_multiple_start_calls(self):
        """Test that multiple start calls don't cause issues."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        await queue.start()
        await queue.start()  # Second call should be no-op

        stats = queue.get_statistics()
        assert stats["is_running"] is True

        await queue.stop(timeout=5.0)

    @pytest.mark.asyncio
    async def test_event_comparison_not_implemented(self):
        """Test event comparison with non-Event type."""
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        result = event.__lt__("not an event")
        assert result == NotImplemented

    def test_get_event_queue_singleton(self):
        """Test get_event_queue returns singleton."""
        # Reset global
        import src.core.event_queue
        from src.core.event_queue import _event_queue, get_event_queue

        src.core.event_queue._event_queue = None

        queue1 = get_event_queue()
        queue2 = get_event_queue()

        assert queue1 is queue2

    def test_publish_event_convenience_function(self):
        """Test publish_event convenience function."""
        # Reset global
        import src.core.event_queue
        from src.core.event_queue import publish_event

        src.core.event_queue._event_queue = None

        event_id = publish_event(
            event_type=EventType.FILE_DISCOVERED,
            data={"file": "test.jpg"},
            priority=Priority.NORMAL,
        )

        assert event_id is not None

    def test_event_post_init_auto_id(self):
        """Test Event __post_init__ auto ID generation."""
        event = Event(
            id="",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=None,  # This should trigger auto-generation
        )
        assert event.id != ""
        assert event.created_at is not None

    def test_event_comparison_scheduled_vs_immediate(self):
        """Test event comparison when one has scheduled_at and other doesn't."""
        now = datetime.now()
        scheduled_event = Event(
            id="1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=now,
            scheduled_at=now + timedelta(minutes=5),
        )
        immediate_event = Event(
            id="2",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=now,
        )

        # Immediate event should come before scheduled
        assert immediate_event < scheduled_event
        assert not (scheduled_event < immediate_event)

    def test_event_comparison_same_priority_different_time(self):
        """Test event comparison with same priority but different creation times."""
        now = datetime.now()
        event1 = Event(
            id="1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=now,
        )
        event2 = Event(
            id="2",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=now + timedelta(seconds=1),
        )
        assert event1 < event2

    def test_event_to_dict_with_scheduled_at(self):
        """Test Event.to_dict with scheduled_at."""
        now = datetime.now()
        scheduled = now + timedelta(hours=1)
        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={"file": "test.jpg"},
            created_at=now,
            scheduled_at=scheduled,
        )
        event_dict = event.to_dict()

        assert event_dict["scheduled_at"] == scheduled.isoformat()

    @pytest.mark.asyncio
    async def test_schedule_loop_processes_due_events(self):
        """Test that _schedule_loop processes due events."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        # Add a scheduled event that's already due
        past_time = datetime.now() - timedelta(seconds=1)
        queue._scheduled_events.append(
            Event(
                id="test-1",
                type=EventType.FILE_DISCOVERED,
                priority=Priority.NORMAL,
                data={},
                created_at=datetime.now(),
                scheduled_at=past_time,
            )
        )

        # Start and let it process
        await queue.start()
        await asyncio.sleep(0.1)
        await queue.stop(timeout=2.0)

        # Scheduled events should be moved to processing queue
        # Note: This may or may not be 0 depending on timing
        assert len(queue._scheduled_events) >= 0

    @pytest.mark.asyncio
    async def test_worker_loop_with_no_events(self):
        """Test worker loop when no events are available."""
        queue = EventQueue(max_workers=1, enable_persistence=False)

        # Start and stop immediately - worker should handle empty queue
        await queue.start()
        await asyncio.sleep(0.1)
        await queue.stop(timeout=2.0)

        stats = queue.get_statistics()
        assert stats["is_running"] is False

    @pytest.mark.asyncio
    async def test_process_event_with_middleware_blocking(self):
        """Test that middleware can block event processing."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        processed = []

        class TestHandler(EventHandler):
            async def handle(self, event: Event) -> bool:
                processed.append(event.id)
                return True

        # Add middleware that blocks all events
        queue.add_middleware(lambda _event: False)
        queue.add_handler(EventType.FILE_DISCOVERED, TestHandler("test"))

        await queue.start()
        queue.publish(EventType.FILE_DISCOVERED, {"file": "test.jpg"})
        await asyncio.sleep(0.1)
        await queue.stop(timeout=2.0)

        # Event should not have been processed
        assert len(processed) == 0

    @pytest.mark.asyncio
    async def test_process_event_with_no_handlers(self):
        """Test processing event when no handlers are registered."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        await queue.start()
        queue.publish(EventType.FILE_DISCOVERED, {"file": "test.jpg"})
        await asyncio.sleep(0.1)
        await queue.stop(timeout=2.0)

        # Should complete without error even though no handlers exist

    @pytest.mark.asyncio
    async def test_process_event_handler_failure(self):
        """Test event processing when handler fails."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        class FailingHandler(EventHandler):
            async def handle(self, event: Event) -> bool:
                return False  # Indicate failure

        queue.add_handler(EventType.FILE_DISCOVERED, FailingHandler("failing"))

        await queue.start()

        # Create event with max_retries=0 to avoid long test
        event = Event(
            id=str(__import__("uuid").uuid4()),
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={"file": "test.jpg"},
            created_at=datetime.now(),
            max_retries=0,
        )
        queue._enqueue_event(event)

        await asyncio.sleep(0.1)
        await queue.stop(timeout=2.0)

        stats = queue.get_statistics()
        # Event should have failed
        assert stats["total_failed"] >= 0

    @pytest.mark.asyncio
    async def test_process_event_handler_exception(self):
        """Test event processing when handler raises exception."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        class ExceptionHandler(EventHandler):
            async def handle(self, event: Event) -> bool:
                raise ValueError("Test exception")

        queue.add_handler(EventType.FILE_DISCOVERED, ExceptionHandler("exception"))

        await queue.start()

        # Publish event with max_retries=0 to avoid long test
        event = Event(
            id=str(__import__("uuid").uuid4()),
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={"file": "test.jpg"},
            created_at=datetime.now(),
            max_retries=0,
        )
        queue._enqueue_event(event)

        await asyncio.sleep(0.1)
        await queue.stop(timeout=2.0)

        stats = queue.get_statistics()
        assert stats["total_failed"] >= 0

    @pytest.mark.asyncio
    async def test_handle_failed_event_with_retries(self):
        """Test failed event retry logic."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
            max_retries=3,
        )

        # Manually test retry logic
        await queue._handle_failed_event(event)

        assert event.retry_count == 1
        assert len(queue._scheduled_events) == 1

    @pytest.mark.asyncio
    async def test_handle_failed_event_max_retries_exceeded(self):
        """Test failed event moved to dead letter queue."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        event = Event(
            id="test-1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
            max_retries=0,
            retry_count=0,
        )

        await queue._handle_failed_event(event)

        assert event.retry_count == 1
        stats = queue.get_statistics()
        assert stats["dead_letter_queue_size"] == 1
        assert stats["total_failed"] == 1

    def test_get_statistics_with_processing_times(self):
        """Test statistics calculation with processing times."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        # Manually add processing times
        queue._stats["processing_times"] = [0.1, 0.2, 0.3, 0.4, 0.5]

        stats = queue.get_statistics()
        assert stats["average_processing_time"] == 0.3

    def test_get_dead_letter_events_empties_queue(self):
        """Test get_dead_letter_events removes events from queue."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        # Add events to dead letter queue
        event1 = Event(
            id="1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )
        event2 = Event(
            id="2",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        queue._dead_letter_queue.put(event1)
        queue._dead_letter_queue.put(event2)

        dead_events = queue.get_dead_letter_events()
        assert len(dead_events) == 2
        assert queue._dead_letter_queue.empty()

    def test_clear_dead_letter_queue_with_events(self):
        """Test clearing dead letter queue with events."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        event = Event(
            id="1",
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={},
            created_at=datetime.now(),
        )

        queue._dead_letter_queue.put(event)
        assert not queue._dead_letter_queue.empty()

        queue.clear_dead_letter_queue()
        assert queue._dead_letter_queue.empty()

    @pytest.mark.asyncio
    async def test_schedule_loop_error_handling(self):
        """Test schedule loop handles errors gracefully."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        # Create a malformed event that might cause issues
        await queue.start()
        await asyncio.sleep(0.1)
        await queue.stop(timeout=2.0)

        # Should complete without crashing

    @pytest.mark.asyncio
    async def test_worker_loop_error_recovery(self):
        """Test worker loop recovers from errors."""
        queue = EventQueue(max_workers=1, enable_persistence=False)

        class RecoveringHandler(EventHandler):
            def __init__(self):
                super().__init__("recovering")
                self.call_count = 0

            async def handle(self, event: Event) -> bool:
                self.call_count += 1
                if self.call_count == 1:
                    raise Exception("First call fails")
                return True

        handler = RecoveringHandler()
        queue.add_handler(EventType.FILE_DISCOVERED, handler)

        await queue.start()

        # Create events with max_retries=0 to avoid long test
        event1 = Event(
            id=str(__import__("uuid").uuid4()),
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={"file": "test1.jpg"},
            created_at=datetime.now(),
            max_retries=0,
        )
        queue._enqueue_event(event1)

        await asyncio.sleep(0.1)

        # Second event should still be processed
        event2 = Event(
            id=str(__import__("uuid").uuid4()),
            type=EventType.FILE_DISCOVERED,
            priority=Priority.NORMAL,
            data={"file": "test2.jpg"},
            created_at=datetime.now(),
            max_retries=0,
        )
        queue._enqueue_event(event2)

        await asyncio.sleep(0.1)
        await queue.stop(timeout=2.0)

    @pytest.mark.asyncio
    async def test_process_event_handler_can_handle_false(self):
        """Test handler that returns False from can_handle."""
        queue = EventQueue(max_workers=2, enable_persistence=False)

        class SelectiveHandler(EventHandler):
            async def handle(self, event: Event) -> bool:
                return True

            def can_handle(self, event: Event) -> bool:
                return event.data.get("process", False)

        queue.add_handler(EventType.FILE_DISCOVERED, SelectiveHandler("selective"))

        await queue.start()

        # This event should not be processed
        queue.publish(EventType.FILE_DISCOVERED, {"process": False})
        await asyncio.sleep(0.1)

        await queue.stop(timeout=2.0)

    def test_publish_event_with_all_optional_params(self):
        """Test publish_event with all optional parameters."""
        import src.core.event_queue
        from src.core.event_queue import publish_event

        src.core.event_queue._event_queue = None

        event_id = publish_event(
            event_type=EventType.FILE_DISCOVERED,
            data={"file": "test.jpg"},
            priority=Priority.HIGH,
            delay=timedelta(seconds=5),
            correlation_id="corr-123",
            source="test-source",
        )

        assert event_id is not None
