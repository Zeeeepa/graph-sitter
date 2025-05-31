"""
Tests for the Enhanced Event System
Core-7: Event System & Multi-Platform Integration
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from codegen.extensions.events.engine import (
    EventProcessingEngine, EventProcessor, ProcessedEvent, 
    EventPriority, EventCorrelator, EventQueue, EventMetrics
)
from codegen.extensions.events.streaming import (
    EventStreamingManager, StreamFilter, EventStream
)


class TestEventProcessingEngine:
    """Test the event processing engine."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = EventProcessingEngine(max_workers=2, queue_maxsize=100)
        
        assert engine.max_workers == 2
        assert engine.queue.queues[EventPriority.NORMAL].maxsize == 100
        assert not engine.running
        assert len(engine.processors) == 0
        
    def test_processor_registration(self):
        """Test processor registration."""
        engine = EventProcessingEngine()
        
        def test_handler(event):
            return {"processed": True}
            
        processor = EventProcessor(
            name="test_processor",
            handler=test_handler,
            event_filters={"platform": "test"}
        )
        
        engine.register_processor(processor)
        assert "test_processor" in engine.processors
        
        engine.unregister_processor("test_processor")
        assert "test_processor" not in engine.processors
        
    def test_event_submission(self):
        """Test event submission."""
        engine = EventProcessingEngine()
        
        event_id = engine.submit_event(
            platform="test",
            event_type="test_event",
            payload={"data": "test"},
            priority=EventPriority.HIGH
        )
        
        assert event_id is not None
        assert isinstance(event_id, str)
        
    def test_event_filtering(self):
        """Test event filtering logic."""
        engine = EventProcessingEngine()
        
        event = ProcessedEvent(
            id=str(uuid.uuid4()),
            platform="github",
            event_type="pull_request:opened",
            payload={"test": "data"}
        )
        
        # Test platform filter
        assert engine._event_matches_filters(event, {"platform": "github"})
        assert not engine._event_matches_filters(event, {"platform": "slack"})
        
        # Test event type filter with wildcards
        assert engine._event_matches_filters(event, {"event_type": "pull_request:*"})
        assert engine._event_matches_filters(event, {"event_type": "*:opened"})
        assert not engine._event_matches_filters(event, {"event_type": "issue:*"})


class TestEventQueue:
    """Test the priority event queue."""
    
    def test_queue_priority(self):
        """Test priority queue ordering."""
        queue = EventQueue()
        
        # Create events with different priorities
        low_event = ProcessedEvent(
            id="1", platform="test", event_type="test", 
            payload={}, priority=EventPriority.LOW
        )
        high_event = ProcessedEvent(
            id="2", platform="test", event_type="test",
            payload={}, priority=EventPriority.HIGH
        )
        critical_event = ProcessedEvent(
            id="3", platform="test", event_type="test",
            payload={}, priority=EventPriority.CRITICAL
        )
        
        # Add in random order
        queue.put(low_event)
        queue.put(high_event)
        queue.put(critical_event)
        
        # Should get critical first
        assert queue.get().id == "3"
        assert queue.get().id == "2"
        assert queue.get().id == "1"
        
    def test_queue_size(self):
        """Test queue size tracking."""
        queue = EventQueue()
        
        event = ProcessedEvent(
            id="1", platform="test", event_type="test", payload={}
        )
        
        assert queue.empty()
        queue.put(event)
        assert not queue.empty()
        
        sizes = queue.qsize()
        assert sizes[EventPriority.NORMAL] == 1
        assert sum(sizes.values()) == 1


class TestEventCorrelator:
    """Test event correlation functionality."""
    
    def test_correlation_rule(self):
        """Test correlation rule application."""
        correlator = EventCorrelator()
        
        def test_rule(event):
            if event.platform == "github" and "pull_request" in event.event_type:
                return f"pr_{event.payload.get('number', 'unknown')}"
            return None
            
        correlator.add_correlation_rule(test_rule)
        
        event = ProcessedEvent(
            id=str(uuid.uuid4()),
            platform="github",
            event_type="pull_request:opened",
            payload={"number": 123}
        )
        
        correlation_id = correlator.correlate_event(event)
        assert correlation_id == "pr_123"
        assert event.correlation_id == "pr_123"
        
    def test_correlated_events_tracking(self):
        """Test tracking of correlated events."""
        correlator = EventCorrelator()
        
        def test_rule(event):
            return "test_correlation"
            
        correlator.add_correlation_rule(test_rule)
        
        event1 = ProcessedEvent(id="1", platform="test", event_type="test", payload={})
        event2 = ProcessedEvent(id="2", platform="test", event_type="test", payload={})
        
        correlator.correlate_event(event1)
        correlator.correlate_event(event2)
        
        correlated = correlator.get_correlated_events("test_correlation")
        assert len(correlated) == 2
        assert event1 in correlated
        assert event2 in correlated


class TestEventMetrics:
    """Test event metrics tracking."""
    
    def test_metrics_recording(self):
        """Test metrics recording."""
        metrics = EventMetrics()
        
        event = ProcessedEvent(
            id=str(uuid.uuid4()),
            platform="github",
            event_type="pull_request:opened",
            payload={}
        )
        
        # Record successful processing
        metrics.record_event_processed(event, 1.5)
        
        stats = metrics.get_metrics()
        assert stats['events_processed'] == 1
        assert stats['events_failed'] == 0
        assert stats['platform_counts']['github'] == 1
        assert stats['event_type_counts']['pull_request:opened'] == 1
        assert stats['avg_processing_time'] == 1.5
        
        # Record failure
        metrics.record_event_failed(event, "Test error")
        
        stats = metrics.get_metrics()
        assert stats['events_failed'] == 1
        assert stats['error_counts']['Test error'] == 1


class TestStreamFilter:
    """Test event stream filtering."""
    
    def test_platform_filter(self):
        """Test platform filtering."""
        filter = StreamFilter(platforms=["github", "linear"])
        
        github_event = ProcessedEvent(
            id="1", platform="github", event_type="test", payload={}
        )
        slack_event = ProcessedEvent(
            id="2", platform="slack", event_type="test", payload={}
        )
        
        assert filter.matches(github_event)
        assert not filter.matches(slack_event)
        
    def test_event_type_filter(self):
        """Test event type filtering with wildcards."""
        filter = StreamFilter(event_types=["pull_request:*", "issue:created"])
        
        pr_event = ProcessedEvent(
            id="1", platform="github", event_type="pull_request:opened", payload={}
        )
        issue_event = ProcessedEvent(
            id="2", platform="github", event_type="issue:created", payload={}
        )
        comment_event = ProcessedEvent(
            id="3", platform="github", event_type="issue:commented", payload={}
        )
        
        assert filter.matches(pr_event)
        assert filter.matches(issue_event)
        assert not filter.matches(comment_event)
        
    def test_custom_filter(self):
        """Test custom payload filtering."""
        filter = StreamFilter(
            custom_filters={"payload.repository.name": "test-repo"}
        )
        
        matching_event = ProcessedEvent(
            id="1", platform="github", event_type="test",
            payload={"repository": {"name": "test-repo"}}
        )
        non_matching_event = ProcessedEvent(
            id="2", platform="github", event_type="test",
            payload={"repository": {"name": "other-repo"}}
        )
        
        assert filter.matches(matching_event)
        assert not filter.matches(non_matching_event)


class TestEventStream:
    """Test individual event stream functionality."""
    
    def test_stream_creation(self):
        """Test stream creation."""
        stream = EventStream("test_stream", "Test stream description")
        
        assert stream.name == "test_stream"
        assert stream.description == "Test stream description"
        assert stream.is_active
        assert len(stream.subscriptions) == 0
        
    @pytest.mark.asyncio
    async def test_event_broadcasting(self):
        """Test event broadcasting to subscriptions."""
        stream = EventStream("test_stream")
        
        # Mock subscription
        subscription = Mock()
        subscription.id = "test_sub"
        subscription.is_active = True
        subscription.filter = StreamFilter()
        subscription.events_sent = 0
        subscription.errors_count = 0
        
        stream.subscriptions["test_sub"] = subscription
        
        # Mock the _send_to_subscription method
        stream._send_to_subscription = Mock()
        
        event = ProcessedEvent(
            id="1", platform="test", event_type="test", payload={}
        )
        
        await stream.broadcast_event(event)
        
        stream._send_to_subscription.assert_called_once()


class TestEventStreamingManager:
    """Test the streaming manager."""
    
    def test_manager_initialization(self):
        """Test manager initialization with default streams."""
        manager = EventStreamingManager()
        
        # Check default streams are created
        assert "all_events" in manager.streams
        assert "github_events" in manager.streams
        assert "linear_events" in manager.streams
        assert "slack_events" in manager.streams
        
    def test_stream_creation(self):
        """Test custom stream creation."""
        manager = EventStreamingManager()
        
        stream = manager.create_stream("custom_stream", "Custom stream")
        assert stream.name == "custom_stream"
        assert "custom_stream" in manager.streams
        
        # Test duplicate creation
        with pytest.raises(ValueError):
            manager.create_stream("custom_stream", "Duplicate")
            
    def test_internal_subscription(self):
        """Test internal callback subscription."""
        manager = EventStreamingManager()
        
        callback_called = False
        received_event = None
        
        def test_callback(event):
            nonlocal callback_called, received_event
            callback_called = True
            received_event = event
            
        subscription_id = manager.subscribe_internal(
            "all_events", test_callback, "test_subscriber"
        )
        
        assert subscription_id is not None
        
        # Test unsubscribe
        manager.unsubscribe(subscription_id)
        
    @pytest.mark.asyncio
    async def test_event_broadcasting(self):
        """Test event broadcasting to target streams."""
        manager = EventStreamingManager()
        
        event = ProcessedEvent(
            id="1", platform="github", event_type="pull_request:opened", payload={}
        )
        
        # Mock stream broadcast methods
        for stream in manager.streams.values():
            stream.broadcast_event = Mock()
            
        await manager.broadcast_event(event)
        
        # Check that appropriate streams received the event
        manager.streams["all_events"].broadcast_event.assert_called_once()
        manager.streams["github_events"].broadcast_event.assert_called_once()
        manager.streams["pr_events"].broadcast_event.assert_called_once()


# Integration tests
class TestEventSystemIntegration:
    """Integration tests for the complete event system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self):
        """Test end-to-end event processing."""
        engine = EventProcessingEngine(max_workers=1)
        
        processed_events = []
        
        def test_processor(event):
            processed_events.append(event)
            return {"processed": True}
            
        processor = EventProcessor(
            name="test_processor",
            handler=test_processor,
            event_filters={"platform": "test"}
        )
        
        engine.register_processor(processor)
        engine.start()
        
        try:
            # Submit test event
            event_id = engine.submit_event(
                platform="test",
                event_type="test_event",
                payload={"data": "test"}
            )
            
            # Wait for processing
            await asyncio.sleep(0.5)
            
            # Check that event was processed
            assert len(processed_events) == 1
            assert processed_events[0].id == event_id
            assert processed_events[0].platform == "test"
            
        finally:
            engine.stop()


if __name__ == "__main__":
    pytest.main([__file__])

