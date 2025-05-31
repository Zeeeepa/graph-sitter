"""
Real-time Event Streaming System
Core-7: Event System & Multi-Platform Integration
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import weakref
import threading

try:
    from fastapi import WebSocket, WebSocketDisconnect
    from fastapi.responses import StreamingResponse
except ImportError:
    WebSocket = None
    WebSocketDisconnect = None
    StreamingResponse = None

from graph_sitter.shared.logging.get_logger import get_logger
from .engine import ProcessedEvent

logger = get_logger(__name__)


class StreamType(Enum):
    """Types of event streams."""
    WEBSOCKET = "websocket"
    SSE = "sse"  # Server-Sent Events
    WEBHOOK = "webhook"
    INTERNAL = "internal"


@dataclass
class StreamFilter:
    """Filter criteria for event streams."""
    platforms: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    source_ids: Optional[List[str]] = None
    source_names: Optional[List[str]] = None
    actor_ids: Optional[List[str]] = None
    correlation_ids: Optional[List[str]] = None
    custom_filters: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, event: ProcessedEvent) -> bool:
        """Check if an event matches this filter."""
        if self.platforms and event.platform not in self.platforms:
            return False
            
        if self.event_types:
            matches_type = False
            for event_type in self.event_types:
                if event_type.endswith('*'):
                    if event.event_type.startswith(event_type[:-1]):
                        matches_type = True
                        break
                elif event_type.startswith('*'):
                    if event.event_type.endswith(event_type[1:]):
                        matches_type = True
                        break
                elif event.event_type == event_type:
                    matches_type = True
                    break
            if not matches_type:
                return False
                
        if self.source_ids and event.source_id not in self.source_ids:
            return False
            
        if self.source_names and event.source_name not in self.source_names:
            return False
            
        if self.actor_ids and event.actor_id not in self.actor_ids:
            return False
            
        if self.correlation_ids and event.correlation_id not in self.correlation_ids:
            return False
            
        # Check custom filters
        for key, value in self.custom_filters.items():
            if not self._check_custom_filter(event, key, value):
                return False
                
        return True
        
    def _check_custom_filter(self, event: ProcessedEvent, key: str, value: Any) -> bool:
        """Check a custom filter against an event."""
        # Support nested payload filtering
        if key.startswith('payload.'):
            payload_key = key[8:]  # Remove 'payload.' prefix
            payload_value = self._get_nested_value(event.payload, payload_key)
            return payload_value == value
            
        # Support metadata filtering
        if key.startswith('metadata.'):
            metadata_key = key[9:]  # Remove 'metadata.' prefix
            metadata_value = self._get_nested_value(event.metadata, metadata_key)
            return metadata_value == value
            
        return True
        
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
                
        return current


@dataclass
class StreamSubscription:
    """Represents a subscription to an event stream."""
    id: str
    stream_name: str
    subscriber_id: str
    stream_type: StreamType
    filter: StreamFilter
    callback: Optional[Callable] = None
    websocket: Optional[Any] = None  # WebSocket connection
    webhook_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_event_sent: Optional[str] = None
    events_sent: int = 0
    errors_count: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


class EventStream:
    """Manages a single event stream with multiple subscriptions."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.subscriptions: Dict[str, StreamSubscription] = {}
        self.is_active = True
        self.created_at = datetime.now(timezone.utc)
        self.events_processed = 0
        self.lock = threading.Lock()
        
    def add_subscription(self, subscription: StreamSubscription):
        """Add a subscription to this stream."""
        with self.lock:
            self.subscriptions[subscription.id] = subscription
            logger.info(f"Added subscription {subscription.id} to stream {self.name}")
            
    def remove_subscription(self, subscription_id: str):
        """Remove a subscription from this stream."""
        with self.lock:
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                logger.info(f"Removed subscription {subscription_id} from stream {self.name}")
                
    def get_active_subscriptions(self) -> List[StreamSubscription]:
        """Get all active subscriptions."""
        with self.lock:
            return [sub for sub in self.subscriptions.values() if sub.is_active]
            
    async def broadcast_event(self, event: ProcessedEvent):
        """Broadcast an event to all matching subscriptions."""
        if not self.is_active:
            return
            
        active_subscriptions = self.get_active_subscriptions()
        
        for subscription in active_subscriptions:
            if subscription.filter.matches(event):
                try:
                    await self._send_to_subscription(subscription, event)
                    subscription.events_sent += 1
                    subscription.last_event_sent = event.id
                except Exception as e:
                    logger.error(f"Failed to send event to subscription {subscription.id}: {e}")
                    subscription.errors_count += 1
                    
                    # Deactivate subscription after too many errors
                    if subscription.errors_count > 10:
                        subscription.is_active = False
                        logger.warning(f"Deactivated subscription {subscription.id} due to errors")
                        
        self.events_processed += 1
        
    async def _send_to_subscription(self, subscription: StreamSubscription, event: ProcessedEvent):
        """Send an event to a specific subscription."""
        event_data = self._serialize_event(event)
        
        if subscription.stream_type == StreamType.WEBSOCKET:
            await self._send_websocket(subscription, event_data)
        elif subscription.stream_type == StreamType.SSE:
            await self._send_sse(subscription, event_data)
        elif subscription.stream_type == StreamType.WEBHOOK:
            await self._send_webhook(subscription, event_data)
        elif subscription.stream_type == StreamType.INTERNAL:
            await self._send_internal(subscription, event)
            
    def _serialize_event(self, event: ProcessedEvent) -> Dict[str, Any]:
        """Serialize an event for transmission."""
        return {
            'id': event.id,
            'platform': event.platform,
            'event_type': event.event_type,
            'source_id': event.source_id,
            'source_name': event.source_name,
            'actor_id': event.actor_id,
            'actor_name': event.actor_name,
            'payload': event.payload,
            'metadata': event.metadata,
            'correlation_id': event.correlation_id,
            'parent_event_id': event.parent_event_id,
            'created_at': event.created_at.isoformat(),
            'processed_at': event.processed_at.isoformat() if event.processed_at else None,
            'processing_duration': event.processing_duration
        }
        
    async def _send_websocket(self, subscription: StreamSubscription, event_data: Dict[str, Any]):
        """Send event via WebSocket."""
        if subscription.websocket:
            try:
                await subscription.websocket.send_json(event_data)
            except Exception as e:
                # WebSocket might be closed
                subscription.is_active = False
                raise e
                
    async def _send_sse(self, subscription: StreamSubscription, event_data: Dict[str, Any]):
        """Send event via Server-Sent Events."""
        # SSE events are handled differently - they're queued for the SSE endpoint
        if hasattr(subscription, '_sse_queue'):
            subscription._sse_queue.put_nowait(event_data)
            
    async def _send_webhook(self, subscription: StreamSubscription, event_data: Dict[str, Any]):
        """Send event via webhook."""
        if subscription.webhook_url:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    subscription.webhook_url,
                    json=event_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status >= 400:
                        raise Exception(f"Webhook returned status {response.status}")
                        
    async def _send_internal(self, subscription: StreamSubscription, event: ProcessedEvent):
        """Send event to internal callback."""
        if subscription.callback:
            if asyncio.iscoroutinefunction(subscription.callback):
                await subscription.callback(event)
            else:
                subscription.callback(event)


class EventStreamingManager:
    """Manages multiple event streams and their subscriptions."""
    
    def __init__(self):
        self.streams: Dict[str, EventStream] = {}
        self.lock = threading.Lock()
        self.is_running = False
        
        # Create default streams
        self._create_default_streams()
        
    def _create_default_streams(self):
        """Create default event streams."""
        default_streams = [
            ('all_events', 'All events across all platforms'),
            ('github_events', 'GitHub events only'),
            ('linear_events', 'Linear events only'),
            ('slack_events', 'Slack events only'),
            ('deployment_events', 'Deployment events only'),
            ('pr_events', 'Pull request related events'),
            ('issue_events', 'Issue related events'),
            ('high_priority', 'High priority events only'),
        ]
        
        for name, description in default_streams:
            self.create_stream(name, description)
            
    def create_stream(self, name: str, description: str = "") -> EventStream:
        """Create a new event stream."""
        with self.lock:
            if name in self.streams:
                raise ValueError(f"Stream {name} already exists")
                
            stream = EventStream(name, description)
            self.streams[name] = stream
            logger.info(f"Created event stream: {name}")
            return stream
            
    def get_stream(self, name: str) -> Optional[EventStream]:
        """Get an event stream by name."""
        return self.streams.get(name)
        
    def delete_stream(self, name: str):
        """Delete an event stream."""
        with self.lock:
            if name in self.streams:
                # Close all subscriptions first
                stream = self.streams[name]
                for subscription in stream.get_active_subscriptions():
                    subscription.is_active = False
                    
                del self.streams[name]
                logger.info(f"Deleted event stream: {name}")
                
    def subscribe_websocket(self, 
                           stream_name: str,
                           websocket: Any,
                           subscriber_id: str,
                           filter: Optional[StreamFilter] = None) -> str:
        """Subscribe to a stream via WebSocket."""
        stream = self.get_stream(stream_name)
        if not stream:
            raise ValueError(f"Stream {stream_name} not found")
            
        subscription = StreamSubscription(
            id=str(uuid.uuid4()),
            stream_name=stream_name,
            subscriber_id=subscriber_id,
            stream_type=StreamType.WEBSOCKET,
            filter=filter or StreamFilter(),
            websocket=websocket
        )
        
        stream.add_subscription(subscription)
        return subscription.id
        
    def subscribe_sse(self, 
                     stream_name: str,
                     subscriber_id: str,
                     filter: Optional[StreamFilter] = None) -> tuple[str, asyncio.Queue]:
        """Subscribe to a stream via Server-Sent Events."""
        stream = self.get_stream(stream_name)
        if not stream:
            raise ValueError(f"Stream {stream_name} not found")
            
        event_queue = asyncio.Queue()
        
        subscription = StreamSubscription(
            id=str(uuid.uuid4()),
            stream_name=stream_name,
            subscriber_id=subscriber_id,
            stream_type=StreamType.SSE,
            filter=filter or StreamFilter()
        )
        
        # Attach the queue to the subscription
        subscription._sse_queue = event_queue
        
        stream.add_subscription(subscription)
        return subscription.id, event_queue
        
    def subscribe_webhook(self, 
                         stream_name: str,
                         webhook_url: str,
                         subscriber_id: str,
                         filter: Optional[StreamFilter] = None) -> str:
        """Subscribe to a stream via webhook."""
        stream = self.get_stream(stream_name)
        if not stream:
            raise ValueError(f"Stream {stream_name} not found")
            
        subscription = StreamSubscription(
            id=str(uuid.uuid4()),
            stream_name=stream_name,
            subscriber_id=subscriber_id,
            stream_type=StreamType.WEBHOOK,
            filter=filter or StreamFilter(),
            webhook_url=webhook_url
        )
        
        stream.add_subscription(subscription)
        return subscription.id
        
    def subscribe_internal(self, 
                          stream_name: str,
                          callback: Callable,
                          subscriber_id: str,
                          filter: Optional[StreamFilter] = None) -> str:
        """Subscribe to a stream with an internal callback."""
        stream = self.get_stream(stream_name)
        if not stream:
            raise ValueError(f"Stream {stream_name} not found")
            
        subscription = StreamSubscription(
            id=str(uuid.uuid4()),
            stream_name=stream_name,
            subscriber_id=subscriber_id,
            stream_type=StreamType.INTERNAL,
            filter=filter or StreamFilter(),
            callback=callback
        )
        
        stream.add_subscription(subscription)
        return subscription.id
        
    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from a stream."""
        for stream in self.streams.values():
            if subscription_id in stream.subscriptions:
                stream.remove_subscription(subscription_id)
                break
                
    async def broadcast_event(self, event: ProcessedEvent):
        """Broadcast an event to all matching streams."""
        # Determine which streams should receive this event
        target_streams = self._get_target_streams(event)
        
        # Broadcast to each target stream
        tasks = []
        for stream_name in target_streams:
            stream = self.get_stream(stream_name)
            if stream and stream.is_active:
                tasks.append(stream.broadcast_event(event))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    def _get_target_streams(self, event: ProcessedEvent) -> List[str]:
        """Determine which streams should receive an event."""
        target_streams = ['all_events']  # Always send to all_events
        
        # Platform-specific streams
        target_streams.append(f"{event.platform}_events")
        
        # Event type specific streams
        if 'pull_request' in event.event_type:
            target_streams.append('pr_events')
        if 'issue' in event.event_type:
            target_streams.append('issue_events')
            
        # Priority-based streams
        if event.priority.value >= 3:  # HIGH or CRITICAL
            target_streams.append('high_priority')
            
        return target_streams
        
    def get_stream_stats(self) -> Dict[str, Any]:
        """Get statistics for all streams."""
        stats = {}
        
        for name, stream in self.streams.items():
            active_subs = len(stream.get_active_subscriptions())
            total_subs = len(stream.subscriptions)
            
            stats[name] = {
                'active_subscriptions': active_subs,
                'total_subscriptions': total_subs,
                'events_processed': stream.events_processed,
                'is_active': stream.is_active,
                'created_at': stream.created_at.isoformat()
            }
            
        return stats
        
    def cleanup_inactive_subscriptions(self):
        """Remove inactive subscriptions from all streams."""
        for stream in self.streams.values():
            inactive_ids = [
                sub_id for sub_id, sub in stream.subscriptions.items()
                if not sub.is_active
            ]
            
            for sub_id in inactive_ids:
                stream.remove_subscription(sub_id)
                
        logger.info("Cleaned up inactive subscriptions")


# FastAPI integration helpers
if WebSocket and StreamingResponse:
    
    async def websocket_endpoint(websocket: WebSocket, 
                                stream_manager: EventStreamingManager,
                                stream_name: str = "all_events"):
        """WebSocket endpoint for real-time event streaming."""
        await websocket.accept()
        
        subscriber_id = f"ws_{int(time.time())}_{id(websocket)}"
        subscription_id = None
        
        try:
            # Parse initial filter from query parameters or first message
            filter_data = websocket.query_params.get('filter')
            if filter_data:
                filter_dict = json.loads(filter_data)
                event_filter = StreamFilter(**filter_dict)
            else:
                event_filter = StreamFilter()
                
            subscription_id = stream_manager.subscribe_websocket(
                stream_name, websocket, subscriber_id, event_filter
            )
            
            # Keep connection alive and handle client messages
            while True:
                try:
                    # Wait for client messages (could be filter updates, etc.)
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    
                    # Handle filter updates
                    if message.startswith('{"filter":'):
                        data = json.loads(message)
                        # Update subscription filter
                        stream = stream_manager.get_stream(stream_name)
                        if stream and subscription_id in stream.subscriptions:
                            subscription = stream.subscriptions[subscription_id]
                            subscription.filter = StreamFilter(**data['filter'])
                            
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send_json({"type": "ping", "timestamp": time.time()})
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket client {subscriber_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error for client {subscriber_id}: {e}")
        finally:
            if subscription_id:
                stream_manager.unsubscribe(subscription_id)
                
                
    async def sse_endpoint(stream_manager: EventStreamingManager,
                          stream_name: str = "all_events",
                          filter_params: Optional[Dict[str, Any]] = None):
        """Server-Sent Events endpoint for real-time event streaming."""
        subscriber_id = f"sse_{int(time.time())}"
        
        # Create filter from parameters
        event_filter = StreamFilter()
        if filter_params:
            if 'platforms' in filter_params:
                event_filter.platforms = filter_params['platforms'].split(',')
            if 'event_types' in filter_params:
                event_filter.event_types = filter_params['event_types'].split(',')
                
        subscription_id, event_queue = stream_manager.subscribe_sse(
            stream_name, subscriber_id, event_filter
        )
        
        async def event_generator():
            try:
                while True:
                    try:
                        # Wait for next event
                        event_data = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                        yield f"data: {json.dumps(event_data)}\n\n"
                    except asyncio.TimeoutError:
                        # Send keep-alive
                        yield f"data: {json.dumps({'type': 'ping', 'timestamp': time.time()})}\n\n"
            except Exception as e:
                logger.error(f"SSE error for client {subscriber_id}: {e}")
            finally:
                stream_manager.unsubscribe(subscription_id)
                
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )


# Factory function
def create_streaming_manager() -> EventStreamingManager:
    """Create a new event streaming manager."""
    return EventStreamingManager()

