"""
WebSocket Manager for Web-Eval-Agent Dashboard

Handles real-time communication between backend and frontend clients.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional, List
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    timestamp: datetime
    data: Dict[str, Any]
    user_id: Optional[str] = None
    project_id: Optional[str] = None


class ConnectionInfo(BaseModel):
    """WebSocket connection information."""
    websocket: WebSocket
    user_id: str
    connected_at: datetime
    last_ping: Optional[datetime] = None
    subscriptions: Set[str] = set()


class WebSocketManager:
    """Manages WebSocket connections and real-time messaging."""
    
    def __init__(self):
        """Initialize WebSocket manager."""
        # Active connections by user ID
        self.connections: Dict[str, List[ConnectionInfo]] = {}
        
        # Connection by WebSocket object for quick lookup
        self.websocket_to_user: Dict[WebSocket, str] = {}
        
        # Message queues for offline users
        self.message_queues: Dict[str, List[WebSocketMessage]] = {}
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0
        }
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_stale_connections())
    
    async def connect(self, websocket: WebSocket, user_id: str) -> bool:
        """Accept a new WebSocket connection."""
        try:
            await websocket.accept()
            
            # Create connection info
            connection_info = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
                connected_at=datetime.utcnow()
            )
            
            # Add to connections
            if user_id not in self.connections:
                self.connections[user_id] = []
            
            self.connections[user_id].append(connection_info)
            self.websocket_to_user[websocket] = user_id
            
            # Update stats
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = sum(len(conns) for conns in self.connections.values())
            
            logger.info(f"WebSocket connected for user {user_id}")
            
            # Send queued messages
            await self._send_queued_messages(user_id)
            
            # Send connection confirmation
            await self._send_to_connection(connection_info, {
                "type": "connection_established",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "message": "WebSocket connection established",
                    "queued_messages": len(self.message_queues.get(user_id, []))
                }
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection for user {user_id}: {e}")
            return False
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Handle WebSocket disconnection."""
        try:
            # Remove from websocket lookup
            if websocket in self.websocket_to_user:
                del self.websocket_to_user[websocket]
            
            # Remove from user connections
            if user_id in self.connections:
                self.connections[user_id] = [
                    conn for conn in self.connections[user_id] 
                    if conn.websocket != websocket
                ]
                
                # Remove user entry if no connections left
                if not self.connections[user_id]:
                    del self.connections[user_id]
            
            # Update stats
            self.stats["active_connections"] = sum(len(conns) for conns in self.connections.values())
            
            logger.info(f"WebSocket disconnected for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling WebSocket disconnection for user {user_id}: {e}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send message to all connections for a specific user."""
        if user_id not in self.connections:
            # Queue message for offline user
            await self._queue_message(user_id, message)
            return False
        
        success_count = 0
        total_connections = len(self.connections[user_id])
        
        # Send to all user connections
        for connection_info in self.connections[user_id].copy():
            try:
                success = await self._send_to_connection(connection_info, message)
                if success:
                    success_count += 1
                else:
                    # Remove failed connection
                    await self._remove_connection(connection_info)
                    
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                await self._remove_connection(connection_info)
        
        # Update stats
        if success_count > 0:
            self.stats["messages_sent"] += 1
        else:
            self.stats["messages_failed"] += 1
        
        return success_count > 0
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Broadcast message to user (alias for send_to_user)."""
        return await self.send_to_user(user_id, message)
    
    async def send_to_project_subscribers(self, project_id: str, message: Dict[str, Any]) -> int:
        """Send message to all users subscribed to a project."""
        sent_count = 0
        
        for user_id, connections in self.connections.items():
            # Check if any connection is subscribed to this project
            for connection_info in connections:
                if project_id in connection_info.subscriptions:
                    success = await self.send_to_user(user_id, message)
                    if success:
                        sent_count += 1
                    break  # Only count once per user
        
        return sent_count
    
    async def subscribe_to_project(self, websocket: WebSocket, project_id: str) -> bool:
        """Subscribe a WebSocket connection to project updates."""
        user_id = self.websocket_to_user.get(websocket)
        if not user_id:
            return False
        
        # Find connection and add subscription
        for connection_info in self.connections.get(user_id, []):
            if connection_info.websocket == websocket:
                connection_info.subscriptions.add(project_id)
                logger.info(f"User {user_id} subscribed to project {project_id}")
                return True
        
        return False
    
    async def unsubscribe_from_project(self, websocket: WebSocket, project_id: str) -> bool:
        """Unsubscribe a WebSocket connection from project updates."""
        user_id = self.websocket_to_user.get(websocket)
        if not user_id:
            return False
        
        # Find connection and remove subscription
        for connection_info in self.connections.get(user_id, []):
            if connection_info.websocket == websocket:
                connection_info.subscriptions.discard(project_id)
                logger.info(f"User {user_id} unsubscribed from project {project_id}")
                return True
        
        return False
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all connected users."""
        sent_count = 0
        
        for user_id in list(self.connections.keys()):
            success = await self.send_to_user(user_id, message)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def ping_user(self, user_id: str) -> bool:
        """Send ping to user connections."""
        if user_id not in self.connections:
            return False
        
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {}
        }
        
        return await self.send_to_user(user_id, ping_message)
    
    async def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user."""
        return len(self.connections.get(user_id, []))
    
    async def get_active_users(self) -> List[str]:
        """Get list of users with active connections."""
        return list(self.connections.keys())
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            **self.stats,
            "active_users": len(self.connections),
            "queued_messages": sum(len(queue) for queue in self.message_queues.values()),
            "total_subscriptions": sum(
                len(conn.subscriptions) 
                for conns in self.connections.values() 
                for conn in conns
            )
        }
    
    async def _send_to_connection(self, connection_info: ConnectionInfo, message: Dict[str, Any]) -> bool:
        """Send message to a specific connection."""
        try:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()
            
            # Send message
            await connection_info.websocket.send_text(json.dumps(message))
            return True
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected during send for user {connection_info.user_id}")
            return False
        except Exception as e:
            logger.error(f"Error sending WebSocket message to user {connection_info.user_id}: {e}")
            return False
    
    async def _remove_connection(self, connection_info: ConnectionInfo):
        """Remove a failed connection."""
        try:
            user_id = connection_info.user_id
            websocket = connection_info.websocket
            
            # Remove from websocket lookup
            if websocket in self.websocket_to_user:
                del self.websocket_to_user[websocket]
            
            # Remove from user connections
            if user_id in self.connections:
                self.connections[user_id] = [
                    conn for conn in self.connections[user_id] 
                    if conn.websocket != websocket
                ]
                
                # Remove user entry if no connections left
                if not self.connections[user_id]:
                    del self.connections[user_id]
            
            # Update stats
            self.stats["active_connections"] = sum(len(conns) for conns in self.connections.values())
            
            # Close websocket if still open
            try:
                await websocket.close()
            except Exception:
                # Ignore errors when closing websocket
                pass
            
        except Exception as e:
            logger.error(f"Error removing connection: {e}")
    
    async def _queue_message(self, user_id: str, message: Dict[str, Any]):
        """Queue message for offline user."""
        if user_id not in self.message_queues:
            self.message_queues[user_id] = []
        
        # Add timestamp
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # Create message object
        websocket_message = WebSocketMessage(
            type=message.get("type", "unknown"),
            timestamp=datetime.utcnow(),
            data=message,
            user_id=user_id
        )
        
        self.message_queues[user_id].append(websocket_message)
        
        # Limit queue size (keep last 100 messages)
        if len(self.message_queues[user_id]) > 100:
            self.message_queues[user_id] = self.message_queues[user_id][-100:]
        
        logger.info(f"Queued message for offline user {user_id}")
    
    async def _send_queued_messages(self, user_id: str):
        """Send queued messages to newly connected user."""
        if user_id not in self.message_queues:
            return
        
        queued_messages = self.message_queues[user_id]
        if not queued_messages:
            return
        
        logger.info(f"Sending {len(queued_messages)} queued messages to user {user_id}")
        
        # Send each queued message
        for websocket_message in queued_messages:
            await self.send_to_user(user_id, websocket_message.data)
        
        # Clear queue
        del self.message_queues[user_id]
    
    async def _cleanup_stale_connections(self):
        """Background task to cleanup stale connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                current_time = datetime.utcnow()
                stale_connections = []
                
                # Find stale connections (no ping for 5 minutes)
                for user_id, connections in self.connections.items():
                    for connection_info in connections:
                        if connection_info.last_ping:
                            time_since_ping = (current_time - connection_info.last_ping).total_seconds()
                            if time_since_ping > 300:  # 5 minutes
                                stale_connections.append(connection_info)
                        else:
                            # No ping recorded, check connection age
                            time_since_connect = (current_time - connection_info.connected_at).total_seconds()
                            if time_since_connect > 600:  # 10 minutes without ping
                                stale_connections.append(connection_info)
                
                # Remove stale connections
                for connection_info in stale_connections:
                    logger.info(f"Removing stale connection for user {connection_info.user_id}")
                    await self._remove_connection(connection_info)
                
                # Cleanup old queued messages (older than 24 hours)
                for user_id, messages in list(self.message_queues.items()):
                    cutoff_time = current_time.timestamp() - (24 * 60 * 60)  # 24 hours ago
                    
                    filtered_messages = [
                        msg for msg in messages 
                        if msg.timestamp.timestamp() > cutoff_time
                    ]
                    
                    if len(filtered_messages) != len(messages):
                        if filtered_messages:
                            self.message_queues[user_id] = filtered_messages
                        else:
                            del self.message_queues[user_id]
                        
                        logger.info(f"Cleaned up old queued messages for user {user_id}")
                
            except asyncio.CancelledError:
                logger.info("WebSocket cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket cleanup task: {e}")
    
    async def handle_client_message(self, websocket: WebSocket, message: str):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            user_id = self.websocket_to_user.get(websocket)
            if not user_id:
                return
            
            # Update last ping time
            for connection_info in self.connections.get(user_id, []):
                if connection_info.websocket == websocket:
                    connection_info.last_ping = datetime.utcnow()
                    break
            
            # Handle different message types
            if message_type == "ping":
                await self._send_to_connection(
                    next(conn for conn in self.connections[user_id] if conn.websocket == websocket),
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                )
            
            elif message_type == "subscribe_project":
                project_id = data.get("project_id")
                if project_id:
                    await self.subscribe_to_project(websocket, project_id)
            
            elif message_type == "unsubscribe_project":
                project_id = data.get("project_id")
                if project_id:
                    await self.unsubscribe_from_project(websocket, project_id)
            
            elif message_type == "get_stats":
                stats = await self.get_connection_stats()
                await self._send_to_connection(
                    next(conn for conn in self.connections[user_id] if conn.websocket == websocket),
                    {"type": "stats", "data": stats}
                )
            
            else:
                logger.warning(f"Unknown message type from client: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from client: {message}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def shutdown(self):
        """Shutdown WebSocket manager."""
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for user_id, connections in list(self.connections.items()):
            for connection_info in connections.copy():
                try:
                    await connection_info.websocket.close()
                except Exception:
                    # Ignore errors when closing websocket
                    pass
                await self._remove_connection(connection_info)
        
        logger.info("WebSocket manager shutdown complete")


# Convenience functions for common message types

async def send_project_update(ws_manager: WebSocketManager, user_id: str, project_data: Dict[str, Any]):
    """Send project update message."""
    message = {
        "type": "project_updated",
        "data": {
            "project": project_data
        }
    }
    await ws_manager.send_to_user(user_id, message)


async def send_agent_run_status(ws_manager: WebSocketManager, user_id: str, run_id: str, status: str, message: str = None):
    """Send agent run status update."""
    message_data = {
        "type": "agent_run_status",
        "data": {
            "run_id": run_id,
            "status": status,
            "message": message
        }
    }
    await ws_manager.send_to_user(user_id, message_data)


async def send_validation_progress(ws_manager: WebSocketManager, user_id: str, project_id: str, pr_number: int, message: str):
    """Send validation progress update."""
    message_data = {
        "type": "validation_progress",
        "data": {
            "project_id": project_id,
            "pr_number": pr_number,
            "message": message
        }
    }
    await ws_manager.send_to_user(user_id, message_data)
