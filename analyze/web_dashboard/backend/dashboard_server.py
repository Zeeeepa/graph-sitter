"""
FastAPI Server for Codebase Dashboard

Provides REST API endpoints for the Reflex frontend to interact with
the comprehensive codebase analysis system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import uvicorn

from .enhanced_tree_api import (
    start_analysis,
    get_analysis_status,
    get_analysis_tree,
    get_analysis_issues,
    get_analysis_dead_code,
    get_analysis_important_functions,
    get_analysis_stats
)

app = FastAPI(
    title="Codebase Analysis Dashboard API",
    description="Comprehensive codebase analysis with tree visualization, issue detection, and dead code analysis",
    version="1.0.0"
)

# Enable CORS for Reflex frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    """Request model for starting analysis."""
    repo_url: str


class AnalyzeResponse(BaseModel):
    """Response model for analysis start."""
    analysis_id: str
    status: str
    message: str


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest):
    """Start a new repository analysis."""
    try:
        analysis_id = await start_analysis(request.repo_url)
        return AnalyzeResponse(
            analysis_id=analysis_id,
            status="started",
            message="Analysis started successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@app.get("/api/analysis/{analysis_id}/status")
async def get_status(analysis_id: str):
    """Get the status of an analysis."""
    result = get_analysis_status(analysis_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/analysis/{analysis_id}/tree")
async def get_tree(analysis_id: str):
    """Get the tree structure for an analysis."""
    result = get_analysis_tree(analysis_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/analysis/{analysis_id}/issues")
async def get_issues(analysis_id: str):
    """Get the issues for an analysis."""
    result = get_analysis_issues(analysis_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/analysis/{analysis_id}/dead_code")
async def get_dead_code(analysis_id: str):
    """Get the dead code analysis for an analysis."""
    result = get_analysis_dead_code(analysis_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/analysis/{analysis_id}/important_functions")
async def get_important_functions(analysis_id: str):
    """Get the important functions for an analysis."""
    result = get_analysis_important_functions(analysis_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/analysis/{analysis_id}/stats")
async def get_stats(analysis_id: str):
    """Get the statistics for an analysis."""
    result = get_analysis_stats(analysis_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "codebase-analysis-dashboard"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Codebase Analysis Dashboard API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "status": "GET /api/analysis/{analysis_id}/status",
            "tree": "GET /api/analysis/{analysis_id}/tree",
            "issues": "GET /api/analysis/{analysis_id}/issues",
            "dead_code": "GET /api/analysis/{analysis_id}/dead_code",
            "important_functions": "GET /api/analysis/{analysis_id}/important_functions",
            "stats": "GET /api/analysis/{analysis_id}/stats",
            "health": "GET /api/health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "dashboard_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
