"""
WebSocket manager for real-time dashboard updates.

This module provides WebSocket functionality for real-time communication between
the dashboard backend and frontend, enabling live updates for workflow progress,
PR status changes, and other dashboard events.
"""

import json
import logging
from typing import Any, Dict, List, Set
from datetime import datetime

try:
    from fastapi import WebSocket, WebSocketDisconnect
    from fastapi.routing import APIRouter
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    WebSocket = None
    WebSocketDisconnect = None
    APIRouter = None

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a WebSocket connection with metadata."""
    
    def __init__(self, websocket: WebSocket, user_id: str, connection_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id
        self.connected_at = datetime.utcnow()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to this connection."""
        try:
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to connection {self.connection_id}: {e}")
    
    def subscribe(self, topic: str):
        """Subscribe to a topic."""
        self.subscriptions.add(topic)
        logger.debug(f"Connection {self.connection_id} subscribed to {topic}")
    
    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic."""
        self.subscriptions.discard(topic)
        logger.debug(f"Connection {self.connection_id} unsubscribed from {topic}")
    
    def is_subscribed(self, topic: str) -> bool:
        """Check if subscribed to a topic."""
        return topic in self.subscriptions


class WebSocketManager:
    """Manages WebSocket connections and real-time messaging."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.topic_subscribers: Dict[str, Set[str]] = {}  # topic -> connection_ids
        
        if not WEBSOCKET_AVAILABLE:
            logger.warning("WebSocket support not available. Real-time updates disabled.")
    
    def setup_routes(self, app):
        """Setup WebSocket routes on the FastAPI app."""
        if not WEBSOCKET_AVAILABLE:
            return
        
        @app.websocket("/dashboard/ws/{user_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str):
            await self.handle_connection(websocket, user_id)
    
    async def handle_connection(self, websocket: WebSocket, user_id: str):
        """Handle a new WebSocket connection."""
        if not WEBSOCKET_AVAILABLE:
            return
        
        connection_id = f"{user_id}_{datetime.utcnow().timestamp()}"
        
        try:
            await websocket.accept()
            
            # Create connection object
            connection = WebSocketConnection(websocket, user_id, connection_id)
            self.connections[connection_id] = connection
            
            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            logger.info(f"WebSocket connection established: {connection_id} for user {user_id}")
            
            # Send welcome message
            await connection.send_message({
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to Contexten Dashboard"
            })
            
            # Handle incoming messages
            await self._handle_messages(connection)
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
        finally:
            await self._cleanup_connection(connection_id)
    
    async def _handle_messages(self, connection: WebSocketConnection):
        """Handle incoming messages from a WebSocket connection."""
        try:
            while True:
                # Receive message
                data = await connection.websocket.receive_text()
                message = json.loads(data)
                
                # Process message
                await self._process_message(connection, message)
                
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Error handling message from {connection.connection_id}: {e}")
    
    async def _process_message(self, connection: WebSocketConnection, message: Dict[str, Any]):
        """Process an incoming message from a client."""
        message_type = message.get("type")
        
        if message_type == "subscribe":
            topic = message.get("topic")
            if topic:
                await self._subscribe_connection(connection, topic)
        
        elif message_type == "unsubscribe":
            topic = message.get("topic")
            if topic:
                await self._unsubscribe_connection(connection, topic)
        
        elif message_type == "ping":
            await connection.send_message({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif message_type == "get_status":
            await self._send_status_update(connection)
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _subscribe_connection(self, connection: WebSocketConnection, topic: str):
        """Subscribe a connection to a topic."""
        connection.subscribe(topic)
        
        # Track topic subscribers
        if topic not in self.topic_subscribers:
            self.topic_subscribers[topic] = set()
        self.topic_subscribers[topic].add(connection.connection_id)
        
        # Send confirmation
        await connection.send_message({
            "type": "subscribed",
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Connection {connection.connection_id} subscribed to topic: {topic}")
    
    async def _unsubscribe_connection(self, connection: WebSocketConnection, topic: str):
        """Unsubscribe a connection from a topic."""
        connection.unsubscribe(topic)
        
        # Remove from topic subscribers
        if topic in self.topic_subscribers:
            self.topic_subscribers[topic].discard(connection.connection_id)
            if not self.topic_subscribers[topic]:
                del self.topic_subscribers[topic]
        
        # Send confirmation
        await connection.send_message({
            "type": "unsubscribed",
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Connection {connection.connection_id} unsubscribed from topic: {topic}")
    
    async def _send_status_update(self, connection: WebSocketConnection):
        """Send current status to a connection."""
        status = {
            "type": "status_update",
            "timestamp": datetime.utcnow().isoformat(),
            "connection_info": {
                "connection_id": connection.connection_id,
                "user_id": connection.user_id,
                "connected_at": connection.connected_at.isoformat(),
                "subscriptions": list(connection.subscriptions)
            },
            "server_info": {
                "total_connections": len(self.connections),
                "active_topics": len(self.topic_subscribers),
                "server_time": datetime.utcnow().isoformat()
            }
        }
        
        await connection.send_message(status)
    
    async def _cleanup_connection(self, connection_id: str):
        """Clean up a disconnected connection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Remove from user connections
        if connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Remove from topic subscribers
        for topic in list(connection.subscriptions):
            if topic in self.topic_subscribers:
                self.topic_subscribers[topic].discard(connection_id)
                if not self.topic_subscribers[topic]:
                    del self.topic_subscribers[topic]
        
        # Remove connection
        del self.connections[connection_id]
        
        logger.info(f"Cleaned up WebSocket connection: {connection_id}")
    
    async def broadcast(self, message: Dict[str, Any], topic: Optional[str] = None):
        """Broadcast a message to all connections or topic subscribers.
        
        Args:
            message: Message to broadcast
            topic: Optional topic to broadcast to specific subscribers
        """
        if not WEBSOCKET_AVAILABLE:
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        # Determine target connections
        if topic:
            target_connections = self.topic_subscribers.get(topic, set())
            logger.debug(f"Broadcasting to topic '{topic}': {len(target_connections)} connections")
        else:
            target_connections = set(self.connections.keys())
            logger.debug(f"Broadcasting to all connections: {len(target_connections)}")
        
        # Send to target connections
        failed_connections = []
        for connection_id in target_connections:
            if connection_id in self.connections:
                try:
                    await self.connections[connection_id].send_message(message)
                except Exception as e:
                    logger.error(f"Failed to send broadcast to {connection_id}: {e}")
                    failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            await self._cleanup_connection(connection_id)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections for a specific user.
        
        Args:
            user_id: Target user ID
            message: Message to send
        """
        if not WEBSOCKET_AVAILABLE:
            return
        
        if user_id not in self.user_connections:
            logger.warning(f"No connections found for user: {user_id}")
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        connection_ids = self.user_connections[user_id].copy()
        failed_connections = []
        
        for connection_id in connection_ids:
            if connection_id in self.connections:
                try:
                    await self.connections[connection_id].send_message(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id} connection {connection_id}: {e}")
                    failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            await self._cleanup_connection(connection_id)
        
        logger.debug(f"Sent message to user {user_id}: {len(connection_ids) - len(failed_connections)} successful")
    
    async def send_project_update(self, project_id: str, update_data: Dict[str, Any]):
        """Send a project-specific update.
        
        Args:
            project_id: Project ID
            update_data: Update data
        """
        message = {
            "type": "project_update",
            "project_id": project_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(message, topic=f"project:{project_id}")
    
    async def send_workflow_update(self, workflow_id: str, status: str, progress: float, details: Optional[Dict[str, Any]] = None):
        """Send a workflow execution update.
        
        Args:
            workflow_id: Workflow ID
            status: Current status
            progress: Progress percentage (0-100)
            details: Additional details
        """
        message = {
            "type": "workflow_update",
            "workflow_id": workflow_id,
            "status": status,
            "progress": progress,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(message, topic=f"workflow:{workflow_id}")
    
    async def send_pr_update(self, project_id: str, pr_data: Dict[str, Any]):
        """Send a pull request update.
        
        Args:
            project_id: Project ID
            pr_data: PR data
        """
        message = {
            "type": "pr_update",
            "project_id": project_id,
            "pr_data": pr_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(message, topic=f"project:{project_id}")
    
    async def send_quality_gate_update(self, task_id: str, gate_data: Dict[str, Any]):
        """Send a quality gate update.
        
        Args:
            task_id: Task ID
            gate_data: Quality gate data
        """
        message = {
            "type": "quality_gate_update",
            "task_id": task_id,
            "gate_data": gate_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(message, topic=f"task:{task_id}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics.
        
        Returns:
            Connection statistics dictionary
        """
        return {
            "total_connections": len(self.connections),
            "unique_users": len(self.user_connections),
            "active_topics": len(self.topic_subscribers),
            "connections_by_user": {
                user_id: len(connection_ids) 
                for user_id, connection_ids in self.user_connections.items()
            },
            "subscribers_by_topic": {
                topic: len(connection_ids)
                for topic, connection_ids in self.topic_subscribers.items()
            }
        }
    
    async def cleanup(self):
        """Cleanup all WebSocket connections."""
        if not WEBSOCKET_AVAILABLE:
            return
        
        # Close all connections
        for connection_id in list(self.connections.keys()):
            try:
                connection = self.connections[connection_id]
                await connection.websocket.close()
            except Exception as e:
                logger.error(f"Error closing connection {connection_id}: {e}")
            finally:
                await self._cleanup_connection(connection_id)
        
        logger.info("All WebSocket connections cleaned up")

