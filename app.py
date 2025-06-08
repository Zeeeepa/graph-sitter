#!/usr/bin/env python3
"""
Simple Graph-Sitter Dashboard Backend
Run this to provide the backend API for the React frontend.
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Graph-Sitter Dashboard API",
    description="Backend API for the Graph-Sitter development dashboard",
    version="1.0.0"
)

# Add CORS middleware
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
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Sample data
sample_projects = [
    {
        "id": "1",
        "name": "Graph-Sitter Core",
        "description": "Code analysis and manipulation framework",
        "status": "active",
        "lastUpdated": datetime.now().isoformat(),
        "metrics": {
            "files": 2073,
            "functions": 1250,
            "lines": 480110,
            "coverage": 85
        }
    },
    {
        "id": "2", 
        "name": "Contexten Extensions",
        "description": "AI-powered development extensions",
        "status": "active",
        "lastUpdated": datetime.now().isoformat(),
        "metrics": {
            "files": 156,
            "functions": 420,
            "lines": 25000,
            "coverage": 78
        }
    }
]

sample_workflows = [
    {
        "id": "wf1",
        "name": "Code Analysis Pipeline",
        "status": "running",
        "progress": 75,
        "startTime": datetime.now().isoformat(),
        "steps": ["Parse", "Analyze", "Report"]
    },
    {
        "id": "wf2", 
        "name": "Syntax Error Fixes",
        "status": "completed",
        "progress": 100,
        "startTime": datetime.now().isoformat(),
        "steps": ["Scan", "Fix", "Validate"]
    }
]

# API Routes
@app.get("/")
async def root():
    return {"message": "Graph-Sitter Dashboard API", "status": "running"}

@app.get("/api/projects")
async def get_projects():
    return {"projects": sample_projects}

@app.get("/api/workflows")
async def get_workflows():
    return {"workflows": sample_workflows}

@app.get("/api/metrics")
async def get_metrics():
    return {
        "totalProjects": len(sample_projects),
        "activeWorkflows": len([w for w in sample_workflows if w["status"] == "running"]),
        "totalFiles": sum(p["metrics"]["files"] for p in sample_projects),
        "totalLines": sum(p["metrics"]["lines"] for p in sample_projects),
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            await manager.broadcast({
                "type": "metrics_update",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "activeConnections": len(manager.active_connections),
                    "systemStatus": "healthy"
                }
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("🚀 Starting Graph-Sitter Dashboard Backend...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

