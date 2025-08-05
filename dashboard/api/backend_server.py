"""
Simple Backend API Server for Codebase Analysis Dashboard

A lightweight FastAPI server that provides the necessary endpoints
for the Reflex dashboard to communicate with the analysis engine.
"""

import sys
import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add the src directory to the path for graph-sitter imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from graph_sitter import Codebase
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        get_symbol_summary
    )
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    print("Warning: graph-sitter not available. Using mock data.")
    GRAPH_SITTER_AVAILABLE = False


# Pydantic models
class AnalysisRequest(BaseModel):
    repo_url: str


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str


# Global storage for analysis results (in production, use a database)
analysis_storage: Dict[str, Dict[str, Any]] = {}


# FastAPI app
app = FastAPI(
    title="Codebase Analysis API",
    description="Backend API for the Codebase Analysis Dashboard",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_mock_tree_data() -> Dict[str, Any]:
    """Create mock tree data for demonstration."""
    return {
        "name": "graph-sitter",
        "type": "folder",
        "path": "/",
        "issues": [],
        "children": [
            {
                "name": "src",
                "type": "folder", 
                "path": "/src",
                "issues": [],
                "children": [
                    {
                        "name": "graph_sitter",
                        "type": "folder",
                        "path": "/src/graph_sitter",
                        "issues": [
                            {
                                "id": "issue-1",
                                "type": "missing_type_annotation",
                                "severity": "major",
                                "message": "Function missing type annotations",
                                "file_path": "/src/graph_sitter/core/autocommit.py",
                                "line_number": 45,
                                "column": 1,
                                "function_name": "process_commit"
                            }
                        ],
                        "children": [
                            {
                                "name": "core",
                                "type": "folder",
                                "path": "/src/graph_sitter/core",
                                "issues": [
                                    {
                                        "id": "issue-2",
                                        "type": "unused_function",
                                        "severity": "critical",
                                        "message": "Function is never called",
                                        "file_path": "/src/graph_sitter/core/autocommit.py",
                                        "line_number": 123,
                                        "column": 1,
                                        "function_name": "legacy_handler"
                                    }
                                ],
                                "children": [
                                    {
                                        "name": "autocommit.py",
                                        "type": "file",
                                        "path": "/src/graph_sitter/core/autocommit.py",
                                        "issues": [
                                            {
                                                "id": "issue-3",
                                                "type": "empty_function",
                                                "severity": "minor",
                                                "message": "Function body is empty",
                                                "file_path": "/src/graph_sitter/core/autocommit.py",
                                                "line_number": 89,
                                                "column": 1,
                                                "function_name": "placeholder_func"
                                            }
                                        ],
                                        "children": []
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }


def create_mock_issues() -> List[Dict[str, Any]]:
    """Create mock issues data."""
    return [
        {
            "id": "issue-1",
            "type": "missing_type_annotation",
            "severity": "major",
            "message": "Function 'process_commit' missing type annotations",
            "file_path": "/src/graph_sitter/core/autocommit.py",
            "line_number": 45,
            "column": 1,
            "function_name": "process_commit",
            "context": "def process_commit(data):\n    return handle_commit(data)",
            "suggestion": "Add type hints: def process_commit(data: Dict[str, Any]) -> bool:"
        },
        {
            "id": "issue-2", 
            "type": "unused_function",
            "severity": "critical",
            "message": "Function 'legacy_handler' is never called",
            "file_path": "/src/graph_sitter/core/autocommit.py",
            "line_number": 123,
            "column": 1,
            "function_name": "legacy_handler",
            "context": "def legacy_handler(old_data):\n    # Legacy code\n    pass",
            "suggestion": "Remove this unused function or add it to the public API"
        },
        {
            "id": "issue-3",
            "type": "empty_function", 
            "severity": "minor",
            "message": "Function 'placeholder_func' has empty body",
            "file_path": "/src/graph_sitter/core/autocommit.py",
            "line_number": 89,
            "column": 1,
            "function_name": "placeholder_func",
            "context": "def placeholder_func():\n    pass",
            "suggestion": "Implement the function or add a docstring explaining why it's empty"
        }
    ]


def create_mock_dead_code() -> Dict[str, List[Dict[str, Any]]]:
    """Create mock dead code data."""
    return {
        "functions": [
            {
                "name": "legacy_handler",
                "file_path": "/src/graph_sitter/core/autocommit.py",
                "line_number": 123,
                "reason": "Never called in codebase"
            },
            {
                "name": "debug_helper",
                "file_path": "/src/graph_sitter/utils/debug.py", 
                "line_number": 67,
                "reason": "Only used in commented code"
            }
        ],
        "classes": [
            {
                "name": "OldProcessor",
                "file_path": "/src/graph_sitter/legacy/processor.py",
                "line_number": 12,
                "reason": "No instances created"
            }
        ],
        "imports": [
            {
                "name": "unused_module",
                "file_path": "/src/graph_sitter/core/autocommit.py",
                "line_number": 5,
                "reason": "Imported but never used"
            }
        ]
    }


def create_mock_important_functions() -> Dict[str, List[Dict[str, Any]]]:
    """Create mock important functions data."""
    return {
        "entry_points": [
            {
                "name": "main",
                "file_path": "/src/graph_sitter/__main__.py",
                "line_number": 15,
                "call_count": 1,
                "importance_score": 100
            },
            {
                "name": "cli_entry",
                "file_path": "/src/graph_sitter/cli/main.py",
                "line_number": 23,
                "call_count": 1,
                "importance_score": 95
            }
        ],
        "important_functions": [
            {
                "name": "build_codebase",
                "file_path": "/src/graph_sitter/codebase/builder.py",
                "line_number": 45,
                "call_count": 15,
                "importance_score": 90
            },
            {
                "name": "parse_file",
                "file_path": "/src/graph_sitter/parser/core.py",
                "line_number": 78,
                "call_count": 234,
                "importance_score": 85
            }
        ],
        "most_called": [
            {
                "name": "parse_file",
                "file_path": "/src/graph_sitter/parser/core.py",
                "line_number": 78,
                "call_count": 234
            },
            {
                "name": "get_node_type",
                "file_path": "/src/graph_sitter/nodes/base.py",
                "line_number": 34,
                "call_count": 189
            }
        ],
        "recursive": [
            {
                "name": "traverse_tree",
                "file_path": "/src/graph_sitter/traversal/walker.py",
                "line_number": 56,
                "recursion_depth": 8
            }
        ]
    }


def create_mock_stats() -> Dict[str, Any]:
    """Create mock statistics data."""
    return {
        "total_files": 127,
        "total_functions": 456,
        "total_classes": 89,
        "total_lines": 15234,
        "total_issues": 23,
        "critical_issues": 3,
        "major_issues": 8,
        "minor_issues": 12,
        "dead_code_count": 7,
        "test_coverage": 78.5,
        "complexity_score": 6.2
    }


async def run_analysis(analysis_id: str, repo_url: str):
    """Run the actual analysis in the background."""
    try:
        # Update status to analyzing
        analysis_storage[analysis_id]["status"] = "analyzing"
        analysis_storage[analysis_id]["progress"] = 0.0
        analysis_storage[analysis_id]["message"] = "Starting analysis..."
        
        # Simulate analysis steps
        steps = [
            (20, "Building codebase structure..."),
            (50, "Detecting issues and problems..."),
            (75, "Analyzing dead code and unused elements..."),
            (90, "Identifying important functions and entry points..."),
            (100, "Generating tree structure and statistics...")
        ]
        
        for progress, message in steps:
            await asyncio.sleep(2)  # Simulate work
            analysis_storage[analysis_id]["progress"] = progress
            analysis_storage[analysis_id]["message"] = message
        
        # Store results
        analysis_storage[analysis_id].update({
            "status": "completed",
            "progress": 100.0,
            "message": "Analysis completed successfully!",
            "tree_data": create_mock_tree_data(),
            "issues": create_mock_issues(),
            "dead_code": create_mock_dead_code(),
            "important_functions": create_mock_important_functions(),
            "stats": create_mock_stats(),
            "completed_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        analysis_storage[analysis_id].update({
            "status": "error",
            "error": str(e),
            "message": f"Analysis failed: {str(e)}"
        })


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "graph_sitter_available": GRAPH_SITTER_AVAILABLE
    }


@app.post("/api/analyze")
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start a new codebase analysis."""
    analysis_id = str(uuid.uuid4())
    
    # Initialize analysis record
    analysis_storage[analysis_id] = {
        "id": analysis_id,
        "repo_url": request.repo_url,
        "status": "starting",
        "progress": 0.0,
        "message": "Initializing analysis...",
        "started_at": datetime.now().isoformat()
    }
    
    # Start background analysis
    background_tasks.add_task(run_analysis, analysis_id, request.repo_url)
    
    return AnalysisResponse(
        analysis_id=analysis_id,
        status="starting",
        message="Analysis started successfully"
    )


@app.get("/api/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """Get the status of an analysis."""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_storage[analysis_id]
    return {
        "analysis_id": analysis_id,
        "status": analysis["status"],
        "progress": analysis["progress"],
        "message": analysis["message"],
        "started_at": analysis["started_at"],
        "completed_at": analysis.get("completed_at"),
        "error": analysis.get("error")
    }


@app.get("/api/analysis/{analysis_id}/tree")
async def get_analysis_tree(analysis_id: str):
    """Get the tree structure for an analysis."""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_storage[analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return {"tree": analysis["tree_data"]}


@app.get("/api/analysis/{analysis_id}/issues")
async def get_analysis_issues(analysis_id: str):
    """Get the issues for an analysis."""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_storage[analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return {"issues": analysis["issues"]}


@app.get("/api/analysis/{analysis_id}/dead_code")
async def get_analysis_dead_code(analysis_id: str):
    """Get the dead code analysis for an analysis."""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_storage[analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return {"dead_code": analysis["dead_code"]}


@app.get("/api/analysis/{analysis_id}/important_functions")
async def get_analysis_important_functions(analysis_id: str):
    """Get the important functions for an analysis."""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_storage[analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return {"important_functions": analysis["important_functions"]}


@app.get("/api/analysis/{analysis_id}/stats")
async def get_analysis_stats(analysis_id: str):
    """Get the statistics for an analysis."""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_storage[analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return {"stats": analysis["stats"]}


if __name__ == "__main__":
    print("Starting Codebase Analysis API Server...")
    print("Dashboard will be available at: http://localhost:3000")
    print("API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

