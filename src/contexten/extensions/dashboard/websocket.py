"""WebSocket handler for real-time dashboard updates."""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time dashboard updates."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Accept a new WebSocket connection."""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            # Store connection metadata
            self.connection_metadata[websocket] = {
                "client_id": client_id or f"client_{len(self.active_connections)}",
                "connected_at": datetime.now(),
                "last_ping": datetime.now()
            }
            
            logger.info(f"WebSocket connection established: {self.connection_metadata[websocket]['client_id']}")
            
            # Send welcome message
            await self.send_personal_message(websocket, {
                "type": "connection_established",
                "data": {
                    "client_id": self.connection_metadata[websocket]["client_id"],
                    "server_time": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error establishing WebSocket connection: {e}")
            raise
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            client_id = self.connection_metadata.get(websocket, {}).get("client_id", "unknown")
            self.active_connections.remove(websocket)
            
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket connection closed: {client_id}")
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket connection."""
        try:
            formatted_message = {
                **message,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(formatted_message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[List[WebSocket]] = None):
        """Broadcast a message to all connected WebSocket clients."""
        if not self.active_connections:
            return
        
        exclude = exclude or []
        formatted_message = {
            **message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected clients
        disconnected = []
        for connection in self.active_connections:
            if connection in exclude:
                continue
                
            try:
                await connection.send_text(json.dumps(formatted_message))
                # Update last ping time
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["last_ping"] = datetime.now()
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                # Connection is broken, mark for removal
                disconnected.append(connection)
        
        # Remove broken connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_project_update(self, event_type: str, project_data: Dict[str, Any]):
        """Broadcast project-related updates."""
        await self.broadcast({
            "type": "project_update",
            "event": event_type,
            "data": project_data
        })
    
    async def broadcast_flow_update(self, event_type: str, flow_data: Dict[str, Any]):
        """Broadcast flow-related updates."""
        await self.broadcast({
            "type": "flow_update",
            "event": event_type,
            "data": flow_data
        })
    
    async def broadcast_task_update(self, event_type: str, task_data: Dict[str, Any]):
        """Broadcast task-related updates."""
        await self.broadcast({
            "type": "task_update",
            "event": event_type,
            "data": task_data
        })
    
    async def broadcast_service_status(self, service_status: Dict[str, str]):
        """Broadcast service status updates."""
        await self.broadcast({
            "type": "service_status",
            "data": service_status
        })
    
    async def broadcast_error(self, error_message: str, error_code: Optional[str] = None):
        """Broadcast error messages."""
        await self.broadcast({
            "type": "error",
            "data": {
                "message": error_message,
                "code": error_code
            }
        })
    
    async def handle_client_message(self, websocket: WebSocket, message: str):
        """Handle incoming messages from WebSocket clients."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                # Respond to ping with pong
                await self.send_personal_message(websocket, {
                    "type": "pong",
                    "data": {"server_time": datetime.now().isoformat()}
                })
            
            elif message_type == "subscribe":
                # Handle subscription to specific events
                subscription_type = data.get("subscription")
                await self._handle_subscription(websocket, subscription_type)
            
            elif message_type == "unsubscribe":
                # Handle unsubscription from specific events
                subscription_type = data.get("subscription")
                await self._handle_unsubscription(websocket, subscription_type)
            
            else:
                logger.warning(f"Unknown message type received: {message_type}")
                await self.send_personal_message(websocket, {
                    "type": "error",
                    "data": {"message": f"Unknown message type: {message_type}"}
                })
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from WebSocket client")
            await self.send_personal_message(websocket, {
                "type": "error",
                "data": {"message": "Invalid JSON format"}
            })
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await self.send_personal_message(websocket, {
                "type": "error",
                "data": {"message": "Internal server error"}
            })
    
    async def _handle_subscription(self, websocket: WebSocket, subscription_type: str):
        """Handle subscription requests."""
        # For now, all clients receive all updates
        # This can be extended to support selective subscriptions
        await self.send_personal_message(websocket, {
            "type": "subscription_confirmed",
            "data": {"subscription": subscription_type}
        })
    
    async def _handle_unsubscription(self, websocket: WebSocket, subscription_type: str):
        """Handle unsubscription requests."""
        # For now, all clients receive all updates
        # This can be extended to support selective subscriptions
        await self.send_personal_message(websocket, {
            "type": "unsubscription_confirmed",
            "data": {"subscription": subscription_type}
        })
    
    async def start_heartbeat(self):
        """Start a heartbeat to check connection health."""
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                
                # Check for stale connections
                current_time = datetime.now()
                stale_connections = []
                
                for connection, metadata in self.connection_metadata.items():
                    last_ping = metadata.get("last_ping", metadata.get("connected_at"))
                    if (current_time - last_ping).total_seconds() > 60:  # 60 seconds timeout
                        stale_connections.append(connection)
                
                # Remove stale connections
                for connection in stale_connections:
                    logger.info("Removing stale WebSocket connection")
                    self.disconnect(connection)
                
                # Send heartbeat to active connections
                if self.active_connections:
                    await self.broadcast({
                        "type": "heartbeat",
                        "data": {"active_connections": len(self.active_connections)}
                    })
                    
            except Exception as e:
                logger.error(f"Error in heartbeat: {e}")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections."""
        return [
            {
                "client_id": metadata["client_id"],
                "connected_at": metadata["connected_at"].isoformat(),
                "last_ping": metadata["last_ping"].isoformat()
            }
            for metadata in self.connection_metadata.values()
        ]


# Global WebSocket manager instance
websocket_manager = WebSocketManager()

