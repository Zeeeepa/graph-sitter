"""
WebSocket manager for real-time communication with the frontend dashboard
"""
import json
import asyncio
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections by client_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store client subscriptions (which projects/workflows they're interested in)
        self.client_subscriptions: Dict[str, List[str]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = []
        
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message with connection info
        await self.send_personal_message({
            "type": "connection_established",
            "client_id": client_id,
            "message": "Connected to AI-Powered CI/CD Platform",
            "timestamp": asyncio.get_event_loop().time()
        }, client_id)
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
            
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Any, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                if isinstance(message, dict):
                    await websocket.send_text(json.dumps(message))
                else:
                    await websocket.send_text(str(message))
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                # Remove broken connection
                self.disconnect(client_id)
    
    async def broadcast(self, message: Any):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
            
        # Prepare message
        if isinstance(message, dict):
            message_text = json.dumps(message)
        else:
            message_text = str(message)
        
        # Send to all clients
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_to_project_subscribers(self, message: Dict[str, Any], project_id: str):
        """Broadcast message to clients subscribed to a specific project"""
        if not self.active_connections:
            return
            
        message_text = json.dumps(message)
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            # Check if client is subscribed to this project
            if project_id in self.client_subscriptions.get(client_id, []):
                try:
                    await websocket.send_text(message_text)
                except Exception as e:
                    logger.error(f"Error sending project update to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def subscribe_to_project(self, client_id: str, project_id: str):
        """Subscribe a client to project updates"""
        if client_id in self.client_subscriptions:
            if project_id not in self.client_subscriptions[client_id]:
                self.client_subscriptions[client_id].append(project_id)
                
                await self.send_personal_message({
                    "type": "subscription_confirmed",
                    "project_id": project_id,
                    "message": f"Subscribed to updates for project {project_id}"
                }, client_id)
    
    async def unsubscribe_from_project(self, client_id: str, project_id: str):
        """Unsubscribe a client from project updates"""
        if client_id in self.client_subscriptions:
            if project_id in self.client_subscriptions[client_id]:
                self.client_subscriptions[client_id].remove(project_id)
                
                await self.send_personal_message({
                    "type": "subscription_removed",
                    "project_id": project_id,
                    "message": f"Unsubscribed from updates for project {project_id}"
                }, client_id)
    
    async def send_agent_status_update(self, task_id: str, project_id: str, status_data: Dict[str, Any]):
        """Send agent status update to relevant clients"""
        message = {
            "type": "agent_status_update",
            "task_id": task_id,
            "project_id": project_id,
            "timestamp": asyncio.get_event_loop().time(),
            **status_data
        }
        
        # Send to project subscribers
        await self.broadcast_to_project_subscribers(message, project_id)
    
    async def send_workflow_update(self, workflow_id: str, project_id: str, workflow_data: Dict[str, Any]):
        """Send workflow status update to relevant clients"""
        message = {
            "type": "workflow_update",
            "workflow_id": workflow_id,
            "project_id": project_id,
            "timestamp": asyncio.get_event_loop().time(),
            **workflow_data
        }
        
        # Send to project subscribers
        await self.broadcast_to_project_subscribers(message, project_id)
    
    async def send_code_analysis_update(self, project_id: str, analysis_data: Dict[str, Any]):
        """Send code analysis results to relevant clients"""
        message = {
            "type": "code_analysis_update",
            "project_id": project_id,
            "timestamp": asyncio.get_event_loop().time(),
            **analysis_data
        }
        
        # Send to project subscribers
        await self.broadcast_to_project_subscribers(message, project_id)
    
    async def send_deployment_update(self, deployment_id: str, project_id: str, deployment_data: Dict[str, Any]):
        """Send deployment status update to relevant clients"""
        message = {
            "type": "deployment_update",
            "deployment_id": deployment_id,
            "project_id": project_id,
            "timestamp": asyncio.get_event_loop().time(),
            **deployment_data
        }
        
        # Send to project subscribers
        await self.broadcast_to_project_subscribers(message, project_id)
    
    async def send_system_notification(self, notification_type: str, message: str, severity: str = "info"):
        """Send system-wide notification to all clients"""
        notification = {
            "type": "system_notification",
            "notification_type": notification_type,
            "message": message,
            "severity": severity,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.broadcast(notification)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "connected_clients": list(self.active_connections.keys()),
            "total_subscriptions": sum(len(subs) for subs in self.client_subscriptions.values()),
            "subscription_details": self.client_subscriptions
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# WebSocket message handlers
class WebSocketMessageHandler:
    """Handle incoming WebSocket messages from clients"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
    
    async def handle_message(self, client_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        message_type = message_data.get("type")
        
        if message_type == "subscribe_project":
            project_id = message_data.get("project_id")
            if project_id:
                await self.websocket_manager.subscribe_to_project(client_id, project_id)
        
        elif message_type == "unsubscribe_project":
            project_id = message_data.get("project_id")
            if project_id:
                await self.websocket_manager.unsubscribe_from_project(client_id, project_id)
        
        elif message_type == "ping":
            await self.websocket_manager.send_personal_message({
                "type": "pong",
                "timestamp": asyncio.get_event_loop().time()
            }, client_id)
        
        elif message_type == "get_connection_stats":
            stats = self.websocket_manager.get_connection_stats()
            await self.websocket_manager.send_personal_message({
                "type": "connection_stats",
                "stats": stats
            }, client_id)
        
        else:
            await self.websocket_manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }, client_id)

