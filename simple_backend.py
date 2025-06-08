
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn

app = FastAPI(title="Graph-Sitter Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Graph-Sitter Dashboard API", "status": "running"}

@app.get("/api/projects")
async def get_projects():
    return {"projects": [
        {
            "id": "1",
            "name": "Graph-Sitter Core",
            "description": "Code analysis framework",
            "status": "active",
            "lastUpdated": datetime.now().isoformat()
        }
    ]}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
