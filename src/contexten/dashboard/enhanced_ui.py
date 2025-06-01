"""
Enhanced Dashboard UI Components

Provides enhanced UI components for project selection, flow management,
and real-time event streaming.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ...shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.project_subscribers: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: Optional[str] = None):
        """Connect a WebSocket client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if project_id:
            if project_id not in self.project_subscribers:
                self.project_subscribers[project_id] = []
            self.project_subscribers[project_id].append(websocket)
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, project_id: Optional[str] = None):
        """Disconnect a WebSocket client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if project_id and project_id in self.project_subscribers:
            if websocket in self.project_subscribers[project_id]:
                self.project_subscribers[project_id].remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)
    
    async def send_to_project_subscribers(self, project_id: str, message: str):
        """Send message to subscribers of a specific project"""
        if project_id not in self.project_subscribers:
            return
        
        disconnected = []
        for connection in self.project_subscribers[project_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending project message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.project_subscribers[project_id].remove(connection)


class EventStreamProcessor:
    """Processes events from MultiProjectManager and sends to WebSocket clients"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.event_queue: Optional[asyncio.Queue] = None
        self.processing_task: Optional[asyncio.Task] = None
    
    async def start(self, multi_project_manager):
        """Start event processing"""
        self.event_queue = await multi_project_manager.subscribe_to_events()
        self.processing_task = asyncio.create_task(self._process_events())
        logger.info("Event stream processor started")
    
    async def stop(self, multi_project_manager):
        """Stop event processing"""
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        if self.event_queue:
            multi_project_manager.unsubscribe_from_events(self.event_queue)
        
        logger.info("Event stream processor stopped")
    
    async def _process_events(self):
        """Process events from the queue and send to WebSocket clients"""
        while True:
            try:
                event = await self.event_queue.get()
                await self._handle_event(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle individual events"""
        event_type = event.get("type")
        data = event.get("data", {})
        project_id = data.get("project_id")
        
        # Format event for frontend
        formatted_event = {
            "type": event_type,
            "timestamp": event.get("timestamp"),
            "data": data,
            "message": self._format_event_message(event_type, data)
        }
        
        message = json.dumps(formatted_event)
        
        # Send to all clients
        await self.websocket_manager.broadcast(message)
        
        # Send to project-specific subscribers
        if project_id:
            await self.websocket_manager.send_to_project_subscribers(project_id, message)
    
    def _format_event_message(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format event message for display"""
        project_id = data.get("project_id", "Unknown")
        
        if event_type == "project_added":
            return f"✅ Project '{data.get('name', project_id)}' added"
        elif event_type == "project_removed":
            return f"🗑️ Project '{project_id}' removed"
        elif event_type == "analysis_completed":
            health_score = data.get("health_score", 0)
            return f"🔍 Analysis completed for '{project_id}' - Health Score: {health_score:.1f}/100"
        elif event_type == "quality_gate_checked":
            gate_name = data.get("gate_name", "Unknown")
            passed = data.get("passed", False)
            status = "✅ Passed" if passed else "❌ Failed"
            return f"🚪 Quality Gate '{gate_name}' - {status}"
        elif event_type == "codegen_task_completed":
            return f"🤖 Codegen task completed for '{project_id}'"
        elif event_type == "deployment_blocked":
            return f"🚫 Deployment blocked for '{project_id}' - Quality gate failed"
        elif event_type == "team_notification":
            message = data.get("message", "Notification")
            return f"📢 {message}"
        else:
            return f"📡 {event_type} - {project_id}"


def generate_enhanced_dashboard_html() -> str:
    """Generate enhanced dashboard HTML with real-time features"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph-Sitter Multi-Project Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <style>
        .fade-in { animation: fadeIn 0.5s ease-in; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .pulse-green { animation: pulse-green 2s infinite; }
        @keyframes pulse-green { 0%, 100% { background-color: rgb(34, 197, 94); } 50% { background-color: rgb(22, 163, 74); } }
        .pulse-red { animation: pulse-red 2s infinite; }
        @keyframes pulse-red { 0%, 100% { background-color: rgb(239, 68, 68); } 50% { background-color: rgb(220, 38, 38); } }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div x-data="dashboardApp()" x-init="init()" class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800">Graph-Sitter Dashboard</h1>
                    <p class="text-gray-600">Multi-Project Management & Quality Gates</p>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="flex items-center space-x-2">
                        <div :class="connected ? 'bg-green-500 pulse-green' : 'bg-red-500 pulse-red'" 
                             class="w-3 h-3 rounded-full"></div>
                        <span class="text-sm text-gray-600" x-text="connected ? 'Connected' : 'Disconnected'"></span>
                    </div>
                    <button @click="refreshData()" 
                            class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                        🔄 Refresh
                    </button>
                </div>
            </div>
        </div>

        <!-- System Status -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600">Projects</p>
                        <p class="text-2xl font-bold text-blue-600" x-text="systemStatus.projects?.total || 0"></p>
                    </div>
                    <div class="text-blue-500 text-3xl">📁</div>
                </div>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600">Running Executions</p>
                        <p class="text-2xl font-bold text-green-600" x-text="systemStatus.executions?.running || 0"></p>
                    </div>
                    <div class="text-green-500 text-3xl">⚡</div>
                </div>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600">Quality Gates</p>
                        <p class="text-2xl font-bold text-purple-600" x-text="systemStatus.quality_gates?.total || 0"></p>
                    </div>
                    <div class="text-purple-500 text-3xl">🚪</div>
                </div>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600">Codegen Available</p>
                        <p class="text-2xl font-bold" 
                           :class="systemStatus.codegen_available ? 'text-green-600' : 'text-red-600'"
                           x-text="systemStatus.codegen_available ? 'Yes' : 'No'"></p>
                    </div>
                    <div class="text-3xl" x-text="systemStatus.codegen_available ? '🤖' : '❌'"></div>
                </div>
            </div>
        </div>

        <!-- Project Selection and Management -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <!-- Projects List -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-semibold text-gray-800">Projects</h2>
                    <button @click="showAddProject = true" 
                            class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm transition-colors">
                        + Add Project
                    </button>
                </div>
                <div class="space-y-3 max-h-96 overflow-y-auto">
                    <template x-for="project in projects" :key="project.id">
                        <div class="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                             @click="selectProject(project)"
                             :class="selectedProject?.id === project.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h3 class="font-medium text-gray-800" x-text="project.name"></h3>
                                    <p class="text-sm text-gray-600" x-text="project.description"></p>
                                    <div class="flex items-center space-x-2 mt-2">
                                        <span class="text-xs bg-gray-200 px-2 py-1 rounded" x-text="project.type"></span>
                                        <template x-for="tag in project.tags" :key="tag">
                                            <span class="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded" x-text="tag"></span>
                                        </template>
                                    </div>
                                </div>
                                <div class="flex space-x-2">
                                    <button @click.stop="analyzeProject(project.id)" 
                                            class="text-blue-500 hover:text-blue-700 text-sm">🔍</button>
                                    <button @click.stop="removeProject(project.id)" 
                                            class="text-red-500 hover:text-red-700 text-sm">🗑️</button>
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- Project Details -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Project Details</h2>
                <div x-show="selectedProject" class="space-y-4">
                    <div>
                        <h3 class="font-medium text-gray-700" x-text="selectedProject?.name"></h3>
                        <p class="text-sm text-gray-600" x-text="selectedProject?.path"></p>
                    </div>
                    
                    <!-- Quick Actions -->
                    <div class="flex space-x-2">
                        <button @click="analyzeProject(selectedProject?.id)" 
                                class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded text-sm transition-colors">
                            🔍 Analyze
                        </button>
                        <button @click="showQualityGates = true" 
                                class="bg-purple-500 hover:bg-purple-600 text-white px-3 py-2 rounded text-sm transition-colors">
                            🚪 Quality Gates
                        </button>
                        <button @click="showChatInterface = true" 
                                class="bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded text-sm transition-colors">
                            💬 Chat
                        </button>
                    </div>

                    <!-- Recent Executions -->
                    <div>
                        <h4 class="font-medium text-gray-700 mb-2">Recent Executions</h4>
                        <div class="space-y-2 max-h-48 overflow-y-auto">
                            <template x-for="execution in projectExecutions" :key="execution.id">
                                <div class="flex justify-between items-center p-2 bg-gray-50 rounded">
                                    <div>
                                        <span class="text-sm font-medium" x-text="execution.flow_type"></span>
                                        <span class="text-xs text-gray-500 ml-2" x-text="formatDate(execution.started_at)"></span>
                                    </div>
                                    <span class="text-xs px-2 py-1 rounded"
                                          :class="getStatusColor(execution.status)"
                                          x-text="execution.status"></span>
                                </div>
                            </template>
                        </div>
                    </div>
                </div>
                <div x-show="!selectedProject" class="text-center text-gray-500 py-8">
                    Select a project to view details
                </div>
            </div>
        </div>

        <!-- Real-time Events -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold text-gray-800">Real-time Events</h2>
                <button @click="clearEvents()" 
                        class="text-gray-500 hover:text-gray-700 text-sm">Clear</button>
            </div>
            <div class="space-y-2 max-h-64 overflow-y-auto">
                <template x-for="event in events.slice().reverse()" :key="event.timestamp">
                    <div class="flex items-center space-x-3 p-2 bg-gray-50 rounded fade-in">
                        <span class="text-xs text-gray-500" x-text="formatTime(event.timestamp)"></span>
                        <span class="text-sm" x-text="event.message"></span>
                    </div>
                </template>
            </div>
        </div>

        <!-- Chat Interface Modal -->
        <div x-show="showChatInterface" 
             class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
             @click.self="showChatInterface = false">
            <div class="bg-white rounded-lg p-6 w-full max-w-md">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold">Chat with Project</h3>
                    <button @click="showChatInterface = false" class="text-gray-500 hover:text-gray-700">✕</button>
                </div>
                <div class="space-y-4">
                    <div class="max-h-48 overflow-y-auto space-y-2">
                        <template x-for="msg in chatMessages" :key="msg.timestamp">
                            <div class="p-2 rounded" :class="msg.type === 'user' ? 'bg-blue-100 ml-4' : 'bg-gray-100 mr-4'">
                                <p class="text-sm" x-text="msg.message"></p>
                            </div>
                        </template>
                    </div>
                    <div class="flex space-x-2">
                        <input x-model="chatInput" 
                               @keyup.enter="sendChatMessage()"
                               placeholder="Type your message..."
                               class="flex-1 border rounded px-3 py-2 text-sm">
                        <button @click="sendChatMessage()" 
                                class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm">
                            Send
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Add Project Modal -->
        <div x-show="showAddProject" 
             class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
             @click.self="showAddProject = false">
            <div class="bg-white rounded-lg p-6 w-full max-w-md">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold">Add New Project</h3>
                    <button @click="showAddProject = false" class="text-gray-500 hover:text-gray-700">✕</button>
                </div>
                <form @submit.prevent="addProject()" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
                        <input x-model="newProject.name" required 
                               class="w-full border rounded px-3 py-2 text-sm">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
                        <select x-model="newProject.type" required 
                                class="w-full border rounded px-3 py-2 text-sm">
                            <option value="local_directory">Local Directory</option>
                            <option value="github_repo">GitHub Repository</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Path</label>
                        <input x-model="newProject.path" required 
                               class="w-full border rounded px-3 py-2 text-sm">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea x-model="newProject.description" 
                                  class="w-full border rounded px-3 py-2 text-sm h-20"></textarea>
                    </div>
                    <div class="flex justify-end space-x-2">
                        <button type="button" @click="showAddProject = false" 
                                class="px-4 py-2 text-gray-600 hover:text-gray-800">Cancel</button>
                        <button type="submit" 
                                class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">
                            Add Project
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        function dashboardApp() {
            return {
                connected: false,
                websocket: null,
                projects: [],
                selectedProject: null,
                projectExecutions: [],
                systemStatus: {},
                events: [],
                showChatInterface: false,
                showAddProject: false,
                showQualityGates: false,
                chatMessages: [],
                chatInput: '',
                newProject: {
                    name: '',
                    type: 'local_directory',
                    path: '',
                    description: ''
                },

                async init() {
                    await this.connectWebSocket();
                    await this.refreshData();
                },

                async connectWebSocket() {
                    try {
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const wsUrl = `${protocol}//${window.location.host}/ws`;
                        this.websocket = new WebSocket(wsUrl);
                        
                        this.websocket.onopen = () => {
                            this.connected = true;
                            console.log('WebSocket connected');
                        };
                        
                        this.websocket.onmessage = (event) => {
                            const data = JSON.parse(event.data);
                            this.handleWebSocketMessage(data);
                        };
                        
                        this.websocket.onclose = () => {
                            this.connected = false;
                            console.log('WebSocket disconnected');
                            // Attempt to reconnect after 5 seconds
                            setTimeout(() => this.connectWebSocket(), 5000);
                        };
                        
                        this.websocket.onerror = (error) => {
                            console.error('WebSocket error:', error);
                        };
                    } catch (error) {
                        console.error('Failed to connect WebSocket:', error);
                    }
                },

                handleWebSocketMessage(data) {
                    this.events.push(data);
                    // Keep only last 50 events
                    if (this.events.length > 50) {
                        this.events = this.events.slice(-50);
                    }
                    
                    // Update data if relevant
                    if (data.type === 'analysis_completed' || data.type === 'project_added' || data.type === 'project_removed') {
                        this.refreshData();
                    }
                },

                async refreshData() {
                    try {
                        // Fetch projects
                        const projectsResponse = await fetch('/api/core-projects');
                        this.projects = await projectsResponse.json();
                        
                        // Fetch system status
                        const statusResponse = await fetch('/api/core-projects/status');
                        this.systemStatus = await statusResponse.json();
                        
                        // Refresh project executions if project is selected
                        if (this.selectedProject) {
                            await this.loadProjectExecutions(this.selectedProject.id);
                        }
                    } catch (error) {
                        console.error('Failed to refresh data:', error);
                    }
                },

                selectProject(project) {
                    this.selectedProject = project;
                    this.loadProjectExecutions(project.id);
                },

                async loadProjectExecutions(projectId) {
                    try {
                        const response = await fetch(`/api/core-projects/${projectId}/executions`);
                        this.projectExecutions = await response.json();
                    } catch (error) {
                        console.error('Failed to load project executions:', error);
                    }
                },

                async analyzeProject(projectId) {
                    try {
                        const response = await fetch(`/api/core-projects/${projectId}/analyze`, {
                            method: 'POST'
                        });
                        const result = await response.json();
                        this.events.push({
                            type: 'user_action',
                            timestamp: new Date().toISOString(),
                            message: `🔍 Started analysis for project ${projectId}`
                        });
                    } catch (error) {
                        console.error('Failed to analyze project:', error);
                    }
                },

                async addProject() {
                    try {
                        const projectData = {
                            id: `project_${Date.now()}`,
                            ...this.newProject
                        };
                        
                        const response = await fetch('/api/core-projects', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(projectData)
                        });
                        
                        if (response.ok) {
                            this.showAddProject = false;
                            this.newProject = { name: '', type: 'local_directory', path: '', description: '' };
                            await this.refreshData();
                        }
                    } catch (error) {
                        console.error('Failed to add project:', error);
                    }
                },

                async removeProject(projectId) {
                    if (confirm('Are you sure you want to remove this project?')) {
                        try {
                            const response = await fetch(`/api/core-projects/${projectId}`, {
                                method: 'DELETE'
                            });
                            if (response.ok) {
                                await this.refreshData();
                                if (this.selectedProject?.id === projectId) {
                                    this.selectedProject = null;
                                }
                            }
                        } catch (error) {
                            console.error('Failed to remove project:', error);
                        }
                    }
                },

                async sendChatMessage() {
                    if (!this.chatInput.trim() || !this.selectedProject) return;
                    
                    const userMessage = {
                        type: 'user',
                        message: this.chatInput,
                        timestamp: new Date().toISOString()
                    };
                    this.chatMessages.push(userMessage);
                    
                    try {
                        const response = await fetch('/api/chat/core-projects', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                message: this.chatInput,
                                project_id: this.selectedProject.id
                            })
                        });
                        
                        const result = await response.json();
                        this.chatMessages.push({
                            type: 'assistant',
                            message: result.message,
                            timestamp: new Date().toISOString()
                        });
                    } catch (error) {
                        console.error('Failed to send chat message:', error);
                    }
                    
                    this.chatInput = '';
                },

                clearEvents() {
                    this.events = [];
                },

                formatDate(dateString) {
                    return new Date(dateString).toLocaleString();
                },

                formatTime(dateString) {
                    return new Date(dateString).toLocaleTimeString();
                },

                getStatusColor(status) {
                    switch (status) {
                        case 'completed': return 'bg-green-200 text-green-800';
                        case 'running': return 'bg-blue-200 text-blue-800';
                        case 'failed': return 'bg-red-200 text-red-800';
                        default: return 'bg-gray-200 text-gray-800';
                    }
                }
            }
        }
    </script>
</body>
</html>
    """

