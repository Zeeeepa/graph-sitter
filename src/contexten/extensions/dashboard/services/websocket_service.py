"""WebSocket service for real-time dashboard updates.

This module provides WebSocket functionality for real-time updates
and event streaming to the dashboard frontend.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = datetime.now(UTC)

class WebSocketManager:
    """WebSocket connection manager."""

    def __init__(self) -> None:
        """Initialize WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.project_subscriptions: Dict[str, Set[str]] = {}
        self._message_queue: asyncio.Queue[WebSocketMessage] = asyncio.Queue()
        self._background_tasks: List[asyncio.Task] = []

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Connect new WebSocket client."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")

    def disconnect(self, client_id: str) -> None:
        """Disconnect WebSocket client."""
        self.active_connections.pop(client_id, None)
        # Remove client from all project subscriptions
        for project_id in self.project_subscriptions:
            self.project_subscriptions[project_id].discard(client_id)
        logger.info(f"WebSocket client disconnected: {client_id}")

    async def subscribe_to_project(self, client_id: str, project_id: str) -> None:
        """Subscribe client to project updates."""
        if project_id not in self.project_subscriptions:
            self.project_subscriptions[project_id] = set()
        self.project_subscriptions[project_id].add(client_id)
        logger.info(f"Client {client_id} subscribed to project {project_id}")

    async def unsubscribe_from_project(self, client_id: str, project_id: str) -> None:
        """Unsubscribe client from project updates."""
        if project_id in self.project_subscriptions:
            self.project_subscriptions[project_id].discard(client_id)
        logger.info(f"Client {client_id} unsubscribed from project {project_id}")

    async def broadcast_message(
        self,
        message_type: str,
        payload: Dict[str, Any],
        project_id: Optional[str] = None
    ) -> None:
        """Broadcast message to connected clients."""
        message = WebSocketMessage(
            type=message_type,
            payload=payload,
            timestamp=datetime.now(UTC)
        )

        # Add message to queue
        await self._message_queue.put(message)

        # Process message immediately if project_id is provided
        if project_id:
            await self._send_project_message(project_id, message)

    async def _send_project_message(
        self,
        project_id: str,
        message: WebSocketMessage
    ) -> None:
        """Send message to project subscribers."""
        if project_id not in self.project_subscriptions:
            return

        message_data = message.model_dump_json()
        subscribers = self.project_subscriptions[project_id].copy()

        for client_id in subscribers:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_text(message_data)
                except WebSocketDisconnect:
                    self.disconnect(client_id)
                except Exception as e:
                    logger.error(f"Failed to send message to client {client_id}: {e}")

    async def start_background_tasks(self) -> None:
        """Start background tasks."""
        self._background_tasks.append(
            asyncio.create_task(self._process_message_queue())
        )

    async def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        for task in self._background_tasks:
            task.cancel()
        self._background_tasks.clear()

    async def _process_message_queue(self) -> None:
        """Process message queue in background."""
        while True:
            try:
                message = await self._message_queue.get()
                message_data = message.model_dump_json()

                # Send to all connected clients
                disconnected_clients = []
                for client_id, websocket in self.active_connections.items():
                    try:
                        await websocket.send_text(message_data)
                    except WebSocketDisconnect:
                        disconnected_clients.append(client_id)
                    except Exception as e:
                        logger.error(f"Failed to send message to client {client_id}: {e}")
                        disconnected_clients.append(client_id)

                # Clean up disconnected clients
                for client_id in disconnected_clients:
                    self.disconnect(client_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")

class WebSocketService:
    """WebSocket service for dashboard real-time updates."""

    def __init__(self) -> None:
        """Initialize WebSocket service."""
        self.manager = WebSocketManager()

    async def start(self) -> None:
        """Start WebSocket service."""
        await self.manager.start_background_tasks()

    async def stop(self) -> None:
        """Stop WebSocket service."""
        await self.manager.stop_background_tasks()

    async def handle_connection(self, websocket: WebSocket, client_id: str) -> None:
        """Handle new WebSocket connection."""
        try:
            await self.manager.connect(websocket, client_id)

            while True:
                try:
                    # Wait for messages from client
                    message = await websocket.receive_text()
                    data = json.loads(message)

                    # Handle client messages
                    message_type = data.get("type")
                    if message_type == "subscribe":
                        project_id = data.get("project_id")
                        if project_id:
                            await self.manager.subscribe_to_project(client_id, project_id)
                    elif message_type == "unsubscribe":
                        project_id = data.get("project_id")
                        if project_id:
                            await self.manager.unsubscribe_from_project(client_id, project_id)

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")

        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {e}")
        finally:
            self.manager.disconnect(client_id)

    async def broadcast_project_update(
        self,
        project_id: str,
        update_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Broadcast project update to subscribers."""
        await self.manager.broadcast_message(
            message_type="project_update",
            payload={
                "project_id": project_id,
                "type": update_type,
                "data": data
            },
            project_id=project_id
        )

    async def broadcast_workflow_event(
        self,
        project_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Broadcast workflow event to subscribers."""
        await self.manager.broadcast_message(
            message_type="workflow_event",
            payload={
                "project_id": project_id,
                "type": event_type,
                "data": event_data
            },
            project_id=project_id
        )

    async def broadcast_metrics_update(
        self,
        project_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Broadcast metrics update to subscribers."""
        await self.manager.broadcast_message(
            message_type="metrics_update",
            payload={
                "project_id": project_id,
                "metrics": metrics
            },
            project_id=project_id
        )

