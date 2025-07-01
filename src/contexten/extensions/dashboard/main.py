#!/usr/bin/env python3
"""
Simple FastAPI app for Contexten Dashboard
This version avoids relative import issues
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Contexten Dashboard API",
    description="Multi-layered Workflow Orchestration Platform",
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

# Basic health check endpoint
@app.get("/")
async def root():
    return {"message": "Contexten Dashboard API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-06-06T06:30:00Z"}

# Projects endpoint
@app.get("/api/projects")
async def get_projects():
    return {
        "projects": [
            {
                "id": "1",
                "name": "Sample Project",
                "description": "A sample project for demonstration",
                "status": "active",
                "created_at": "2025-06-06T06:30:00Z"
            }
        ]
    }

@app.post("/api/projects")
async def create_project(project_data: dict):
    return {
        "id": "new-project",
        "name": project_data.get("name", "New Project"),
        "description": project_data.get("description", ""),
        "status": "active",
        "created_at": "2025-06-06T06:30:00Z"
    }

# Settings endpoint
@app.get("/api/settings")
async def get_settings():
    return {
        "theme": "light",
        "notifications": True,
        "auto_save": True
    }

if __name__ == "__main__":
    print("🚀 Starting Contexten Dashboard API...")
    print("📊 Multi-layered Workflow Orchestration Platform")
    print("🌐 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False  # Disable reload when running as script
    )

