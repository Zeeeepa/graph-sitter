import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Dict, Any
import uvicorn

app = FastAPI(title="Graph-Sitter Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Enhanced project data with flow information
projects_data = [
    {
        "id": "1",
        "name": "Graph-Sitter Core",
        "description": "Code analysis framework with advanced parsing capabilities",
        "status": "active",
        "repository": "https://github.com/Zeeeepa/graph-sitter",
        "progress": 85,
        "flowEnabled": True,
        "flowStatus": "running",
        "lastActivity": datetime.now().isoformat(),
        "tags": ["core", "typescript", "analysis"],
        "metrics": {
            "commits": 156,
            "prs": 23,
            "contributors": 8,
            "issues": 45
        },
        "extensions": ["analysis", "visualize", "resolve"]
    },
    {
        "id": "2", 
        "name": "Contexten Extensions",
        "description": "AI agent framework with graph-sitter integration",
        "status": "active",
        "repository": "https://github.com/Zeeeepa/contexten",
        "progress": 70,
        "flowEnabled": True,
        "flowStatus": "idle",
        "lastActivity": datetime.now().isoformat(),
        "tags": ["ai", "agents", "python"],
        "metrics": {
            "commits": 89,
            "prs": 12,
            "contributors": 5,
            "issues": 23
        },
        "extensions": ["graph_sitter", "dashboard", "langchain"]
    },
    {
        "id": "3",
        "name": "Dashboard UI",
        "description": "React dashboard interface with real-time updates",
        "status": "development",
        "repository": "https://github.com/Zeeeepa/dashboard",
        "progress": 60,
        "flowEnabled": False,
        "flowStatus": "disabled",
        "lastActivity": datetime.now().isoformat(),
        "tags": ["frontend", "react", "dashboard"],
        "metrics": {
            "commits": 67,
            "prs": 8,
            "contributors": 3,
            "issues": 15
        },
        "extensions": ["websocket", "api"]
    }
]

@app.get("/")
async def root():
    return {"message": "Graph-Sitter Dashboard API", "status": "running", "timestamp": datetime.now().isoformat()}

@app.get("/api/projects")
async def get_projects():
    return {"projects": projects_data}

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    project = next((p for p in projects_data if p["id"] == project_id), None)
    if project:
        return {"project": project}
    return {"error": "Project not found"}, 404

@app.post("/api/projects/{project_id}/pin")
async def pin_project(project_id: str):
    project = next((p for p in projects_data if p["id"] == project_id), None)
    if project:
        # Broadcast update to all connected clients
        await manager.broadcast(json.dumps({
            "type": "project_pinned",
            "projectId": project_id,
            "timestamp": datetime.now().isoformat()
        }))
        return {"success": True, "message": f"Project {project_id} pinned"}
    return {"error": "Project not found"}, 404

@app.post("/api/projects/{project_id}/unpin")
async def unpin_project(project_id: str):
    project = next((p for p in projects_data if p["id"] == project_id), None)
    if project:
        # Broadcast update to all connected clients
        await manager.broadcast(json.dumps({
            "type": "project_unpinned", 
            "projectId": project_id,
            "timestamp": datetime.now().isoformat()
        }))
        return {"success": True, "message": f"Project {project_id} unpinned"}
    return {"error": "Project not found"}, 404

@app.get("/api/stats")
async def get_stats():
    total_projects = len(projects_data)
    active_projects = len([p for p in projects_data if p["status"] == "active"])
    flow_enabled = len([p for p in projects_data if p["flowEnabled"]])
    
    return {
        "stats": {
            "totalProjects": total_projects,
            "activeProjects": active_projects,
            "flowEnabled": flow_enabled,
            "totalCommits": sum(p["metrics"]["commits"] for p in projects_data),
            "totalPRs": sum(p["metrics"]["prs"] for p in projects_data),
            "totalContributors": sum(p["metrics"]["contributors"] for p in projects_data),
            "totalIssues": sum(p["metrics"]["issues"] for p in projects_data)
        }
    }

@app.get("/api/extensions")
async def get_extensions():
    extensions = [
        {
            "id": "graph_sitter_analysis",
            "name": "Graph-Sitter Analysis",
            "description": "Code analysis and complexity metrics",
            "status": "active",
            "version": "1.0.0",
            "capabilities": ["complexity_analysis", "dependency_analysis", "security_analysis"]
        },
        {
            "id": "graph_sitter_visualize", 
            "name": "Graph-Sitter Visualize",
            "description": "Code visualization and graph generation",
            "status": "active",
            "version": "1.0.0",
            "capabilities": ["dependency_graphs", "call_graphs", "complexity_heatmaps"]
        },
        {
            "id": "graph_sitter_resolve",
            "name": "Graph-Sitter Resolve", 
            "description": "Symbol resolution and import analysis",
            "status": "active",
            "version": "1.0.0",
            "capabilities": ["symbol_resolution", "import_analysis", "cross_references"]
        }
    ]
    return {"extensions": extensions}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "WebSocket connected successfully",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send periodic updates
        while True:
            # Send project status updates every 30 seconds
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({
                "type": "project_status_update",
                "data": {
                    "activeProjects": len([p for p in projects_data if p["status"] == "active"]),
                    "flowsRunning": len([p for p in projects_data if p["flowStatus"] == "running"]),
                    "timestamp": datetime.now().isoformat()
                }
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "connections": len(manager.active_connections),
        "projects": len(projects_data)
    }

if __name__ == "__main__":
    print("🚀 Starting Graph-Sitter Dashboard API...")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")
    print("🌐 API endpoint: http://localhost:8000/api")
    uvicorn.run(app, host="0.0.0.0", port=8000)

