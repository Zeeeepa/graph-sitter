#!/usr/bin/env python3
"""
Enhanced Dashboard Backend with Real Graph-Sitter Integration
============================================================

FastAPI backend that serves real codebase analysis data from graph-sitter
instead of mock data, with comprehensive error handling and performance optimization.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import our integrations
from graph_sitter_integration import (
    get_real_file_tree,
    get_real_file_content,
    get_real_code_graph,
    get_real_code_metrics,
    initialize_analyzer
)
from serena_error_integration import (
    analyze_file_errors,
    analyze_codebase_errors
)
from enhanced_visualization import (
    get_enhanced_file_tree,
    get_enhanced_file_content,
    get_enhanced_code_graph,
    get_error_dashboard
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Enhanced Dashboard API",
    description="Real-time codebase analysis dashboard with graph-sitter integration",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5175",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
analysis_status = {
    'initialized': False,
    'last_update': None,
    'error': None
}

@app.on_event("startup")
async def startup_event():
    """Initialize the graph-sitter analyzer on startup."""
    logger.info("Starting enhanced dashboard backend...")
    
    try:
        await initialize_analyzer()
        analysis_status['initialized'] = True
        analysis_status['last_update'] = datetime.now().isoformat()
        analysis_status['error'] = None
        logger.info("✅ Graph-sitter analyzer initialized successfully")
    except Exception as e:
        analysis_status['initialized'] = False
        analysis_status['error'] = str(e)
        logger.error(f"❌ Failed to initialize analyzer: {e}")

@app.get("/api/health")
async def health_check():
    """Enhanced health check with analysis status."""
    return {
        'status': 'ok',
        'message': 'Enhanced Dashboard API is running',
        'timestamp': datetime.now().isoformat(),
        'analysis_status': analysis_status,
        'version': '2.0.0'
    }

@app.get("/api/status")
async def get_status():
    """Get detailed system status."""
    return {
        'api_status': 'running',
        'analysis_initialized': analysis_status['initialized'],
        'last_analysis_update': analysis_status['last_update'],
        'error': analysis_status['error'],
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/file-tree")
async def get_file_tree(enhanced: bool = True):
    """Get the file tree structure with optional error enhancement."""
    try:
        logger.info(f"Fetching {'enhanced' if enhanced else 'basic'} file tree...")
        start_time = datetime.now()
        
        if enhanced:
            file_tree_data = await get_enhanced_file_tree()
        else:
            file_tree_data = await get_real_file_tree()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"File tree fetched in {processing_time:.2f}s")
        
        return {
            'data': file_tree_data,
            'metadata': {
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'source': 'graph-sitter' + (' + serena' if enhanced else ''),
                'enhanced': enhanced
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching file tree: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch file tree: {str(e)}")

@app.get("/api/file-content")
async def get_file_content(filepath: str, enhanced: bool = True):
    """Get file content with optional error highlighting."""
    try:
        logger.info(f"Fetching {'enhanced' if enhanced else 'basic'} content for file: {filepath}")
        start_time = datetime.now()
        
        if enhanced:
            file_content = await get_enhanced_file_content(filepath)
        else:
            file_content = await get_real_file_content(filepath)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"File content fetched in {processing_time:.2f}s")
        
        if 'error' in file_content:
            raise HTTPException(status_code=404, detail=file_content['error'])
        
        return {
            'data': file_content,
            'metadata': {
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'source': 'graph-sitter' + (' + serena' if enhanced else ''),
                'enhanced': enhanced
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching file content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch file content: {str(e)}")

@app.get("/api/code-graph")
async def get_code_graph():
    """Get the code graph visualization data from graph-sitter analysis."""
    try:
        logger.info("Generating code graph...")
        start_time = datetime.now()
        
        code_graph = await get_real_code_graph()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Code graph generated in {processing_time:.2f}s")
        
        return {
            'data': code_graph,
            'metadata': {
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'source': 'graph-sitter'
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating code graph: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate code graph: {str(e)}")

@app.get("/api/code-metrics")
async def get_code_metrics():
    """Get comprehensive code metrics from graph-sitter analysis."""
    try:
        logger.info("Calculating code metrics...")
        start_time = datetime.now()
        
        metrics = await get_real_code_metrics()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Code metrics calculated in {processing_time:.2f}s")
        
        return {
            'data': metrics,
            'metadata': {
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'source': 'graph-sitter'
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")

@app.get("/api/projects")
async def get_projects():
    """Get available projects (enhanced with real data)."""
    try:
        # Get real metrics to enhance project info
        metrics = await get_real_code_metrics()
        
        return {
            'projects': [
                {
                    'id': 'graph-sitter',
                    'name': 'Graph-Sitter',
                    'description': 'Code analysis and manipulation toolkit',
                    'language': 'Python',
                    'stats': {
                        'files': metrics.get('overview', {}).get('total_files', 0),
                        'functions': metrics.get('overview', {}).get('total_functions', 0),
                        'classes': metrics.get('overview', {}).get('total_classes', 0),
                        'lines': metrics.get('overview', {}).get('total_lines', 0)
                    },
                    'last_analyzed': analysis_status.get('last_update'),
                    'status': 'active'
                }
            ],
            'metadata': {
                'total_projects': 1,
                'timestamp': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        # Fallback to basic project info
        return {
            'projects': [
                {
                    'id': 'graph-sitter',
                    'name': 'Graph-Sitter',
                    'description': 'Code analysis and manipulation toolkit',
                    'language': 'Python',
                    'status': 'error',
                    'error': str(e)
                }
            ]
        }

@app.post("/api/refresh-analysis")
async def refresh_analysis(background_tasks: BackgroundTasks):
    """Refresh the codebase analysis in the background."""
    
    async def refresh_task():
        try:
            logger.info("Refreshing codebase analysis...")
            await initialize_analyzer()
            analysis_status['last_update'] = datetime.now().isoformat()
            analysis_status['error'] = None
            logger.info("✅ Analysis refresh completed")
        except Exception as e:
            analysis_status['error'] = str(e)
            logger.error(f"❌ Analysis refresh failed: {e}")
    
    background_tasks.add_task(refresh_task)
    
    return {
        'message': 'Analysis refresh started',
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/error-dashboard")
async def get_error_dashboard_endpoint():
    """Get comprehensive error dashboard data."""
    try:
        logger.info("Fetching error dashboard...")
        start_time = datetime.now()
        
        dashboard_data = await get_error_dashboard()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Error dashboard generated in {processing_time:.2f}s")
        
        return {
            'data': dashboard_data,
            'metadata': {
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'source': 'serena + graph-sitter'
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating error dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate error dashboard: {str(e)}")

@app.get("/api/file-errors")
async def get_file_errors(filepath: str):
    """Get detailed error analysis for a specific file."""
    try:
        logger.info(f"Analyzing errors in file: {filepath}")
        start_time = datetime.now()
        
        # Get file content first
        file_content_data = await get_real_file_content(filepath)
        if 'error' in file_content_data:
            raise HTTPException(status_code=404, detail=file_content_data['error'])
        
        # Analyze errors
        errors = await analyze_file_errors(filepath, file_content_data['content'])
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"File error analysis completed in {processing_time:.2f}s")
        
        return {
            'filepath': filepath,
            'errors': errors,
            'error_count': len(errors),
            'metadata': {
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'source': 'serena'
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing file errors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze file errors: {str(e)}")

@app.get("/api/search")
async def search_codebase(query: str, limit: int = 20):
    """Search the codebase for functions, classes, or files."""
    try:
        logger.info(f"Searching codebase for: {query}")
        
        # Get all data for searching
        file_tree = await get_real_file_tree()
        metrics = await get_real_code_metrics()
        
        results = []
        
        # Simple search implementation (can be enhanced)
        def search_in_tree(node, path=""):
            if isinstance(node, dict):
                current_path = f"{path}/{node.get('name', '')}" if path else node.get('name', '')
                
                # Check if query matches node name
                if query.lower() in node.get('name', '').lower():
                    results.append({
                        'type': node.get('type', 'unknown'),
                        'name': node.get('name', ''),
                        'path': current_path,
                        'filepath': node.get('filepath', current_path)
                    })
                
                # Search in children
                for child in node.get('children', []):
                    search_in_tree(child, current_path)
        
        search_in_tree(file_tree)
        
        # Limit results
        limited_results = results[:limit]
        
        return {
            'query': query,
            'results': limited_results,
            'total_found': len(results),
            'returned': len(limited_results),
            'metadata': {
                'timestamp': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching codebase: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for better error responses."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal server error',
            'message': str(exc),
            'timestamp': datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    print("🚀 Starting Enhanced Dashboard Backend with Graph-Sitter Integration")
    print("=" * 70)
    print("📊 Features:")
    print("  • Real-time codebase analysis")
    print("  • Graph-sitter integration")
    print("  • Enhanced API endpoints")
    print("  • Performance monitoring")
    print("  • Comprehensive error handling")
    print("=" * 70)
    
    uvicorn.run(
        "enhanced_main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )
