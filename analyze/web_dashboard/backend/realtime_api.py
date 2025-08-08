#!/usr/bin/env python3
"""
Real-time API Integration for Graph-sitter Analysis Functions
===========================================================

This module integrates existing graph-sitter analysis functions with real-time
WebSocket capabilities for the dashboard. It leverages all existing functionality
without duplication.
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

# Add graph-sitter to path
current_dir = Path(__file__).parent
graph_sitter_root = current_dir.parent.parent
src_path = graph_sitter_root / "src"
sys.path.insert(0, str(src_path))

# Import existing graph-sitter analysis functions
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary, 
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RepoLoadRequest(BaseModel):
    repo_url: str
    include_analysis: bool = True
    include_errors: bool = True

class AnalysisRequest(BaseModel):
    analysis_type: str  # "codebase", "file", "class", "function", "symbol"
    target_path: Optional[str] = None
    target_name: Optional[str] = None

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.codebase_cache: Dict[str, Codebase] = {}
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

# Global connection manager
manager = ConnectionManager()

class RealtimeAnalyzer:
    """Real-time analyzer using existing graph-sitter functions."""
    
    def __init__(self):
        self.analysis_cache = {}
        
    async def load_repository(self, repo_url: str, websocket: WebSocket) -> Dict[str, Any]:
        """Load repository using existing Codebase.from_repo method."""
        try:
            await self.send_progress(websocket, "Loading repository...", 10)
            
            # Use existing from_repo method
            codebase = Codebase.from_repo(repo_url)
            manager.codebase_cache[repo_url] = codebase
            
            await self.send_progress(websocket, "Repository loaded successfully", 50)
            
            # Run initial analysis using existing functions
            analysis_result = await self.run_comprehensive_analysis(codebase, websocket)
            
            await self.send_progress(websocket, "Analysis complete", 100)
            
            return {
                "status": "success",
                "repo_url": repo_url,
                "analysis": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error loading repository: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            await self.send_error(websocket, error_msg)
            return {"status": "error", "message": error_msg}
    
    async def run_comprehensive_analysis(self, codebase: Codebase, websocket: WebSocket) -> Dict[str, Any]:
        """Run comprehensive analysis using existing analysis functions."""
        try:
            await self.send_progress(websocket, "Running codebase analysis...", 60)
            
            # Use existing get_codebase_summary function
            codebase_summary = get_codebase_summary(codebase)
            
            await self.send_progress(websocket, "Analyzing files...", 70)
            
            # Analyze files using existing get_file_summary
            file_analyses = []
            files_list = list(codebase.files)
            for i, file in enumerate(files_list[:10]):  # Limit to first 10 for performance
                try:
                    file_summary = get_file_summary(file)
                    file_analyses.append({
                        "name": file.name,
                        "path": file.filepath,
                        "summary": file_summary,
                        "functions_count": len(file.functions),
                        "classes_count": len(file.classes),
                        "imports_count": len(file.imports)
                    })
                except Exception as e:
                    logger.error(f"Error analyzing file {file.name}: {e}")
                    
                # Send progress update
                progress = 70 + (i / len(files_list[:10])) * 10
                await self.send_progress(websocket, f"Analyzed {i+1}/{len(files_list[:10])} files", progress)
            
            await self.send_progress(websocket, "Analyzing functions...", 80)
            
            # Analyze functions using existing get_function_summary
            function_analyses = []
            functions_list = list(codebase.functions)
            for i, func in enumerate(functions_list[:20]):  # Limit to first 20
                try:
                    func_summary = get_function_summary(func)
                    function_analyses.append({
                        "name": func.name,
                        "file": func.filepath,
                        "summary": func_summary,
                        "parameters_count": len(func.parameters),
                        "dependencies_count": len(func.dependencies)
                    })
                except Exception as e:
                    logger.error(f"Error analyzing function {func.name}: {e}")
                    
                if i % 5 == 0:  # Update progress every 5 functions
                    progress = 80 + (i / len(functions_list[:20])) * 10
                    await self.send_progress(websocket, f"Analyzed {i+1}/{len(functions_list[:20])} functions", progress)
            
            await self.send_progress(websocket, "Analyzing classes...", 90)
            
            # Analyze classes using existing get_class_summary
            class_analyses = []
            classes_list = list(codebase.classes)
            for i, cls in enumerate(classes_list[:10]):  # Limit to first 10
                try:
                    class_summary = get_class_summary(cls)
                    class_analyses.append({
                        "name": cls.name,
                        "file": cls.filepath,
                        "summary": class_summary,
                        "methods_count": len(cls.methods),
                        "attributes_count": len(cls.attributes)
                    })
                except Exception as e:
                    logger.error(f"Error analyzing class {cls.name}: {e}")
            
            return {
                "codebase_summary": codebase_summary,
                "files": file_analyses,
                "functions": function_analyses,
                "classes": class_analyses,
                "statistics": {
                    "total_files": len(files_list),
                    "total_functions": len(functions_list),
                    "total_classes": len(classes_list),
                    "analyzed_files": len(file_analyses),
                    "analyzed_functions": len(function_analyses),
                    "analyzed_classes": len(class_analyses)
                }
            }
            
        except Exception as e:
            error_msg = f"Error in comprehensive analysis: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            await self.send_error(websocket, error_msg)
            return {"error": error_msg}
    
    async def analyze_specific_target(self, codebase: Codebase, analysis_type: str, 
                                    target_path: str = None, target_name: str = None,
                                    websocket: WebSocket = None) -> Dict[str, Any]:
        """Analyze specific targets using existing analysis functions."""
        try:
            if analysis_type == "file" and target_path:
                # Find file and use existing get_file_summary
                for file in codebase.files:
                    if file.filepath == target_path or file.name == target_path:
                        return {
                            "type": "file",
                            "target": target_path,
                            "summary": get_file_summary(file),
                            "details": {
                                "functions": [f.name for f in file.functions],
                                "classes": [c.name for c in file.classes],
                                "imports": [i.name for i in file.imports]
                            }
                        }
                        
            elif analysis_type == "function" and target_name:
                # Find function and use existing get_function_summary
                for func in codebase.functions:
                    if func.name == target_name:
                        return {
                            "type": "function",
                            "target": target_name,
                            "summary": get_function_summary(func),
                            "details": {
                                "file": func.filepath,
                                "parameters": [p.name for p in func.parameters],
                                "dependencies": [d.name for d in func.dependencies]
                            }
                        }
                        
            elif analysis_type == "class" and target_name:
                # Find class and use existing get_class_summary
                for cls in codebase.classes:
                    if cls.name == target_name:
                        return {
                            "type": "class",
                            "target": target_name,
                            "summary": get_class_summary(cls),
                            "details": {
                                "file": cls.filepath,
                                "methods": [m.name for m in cls.methods],
                                "attributes": [a.name for a in cls.attributes]
                            }
                        }
            
            return {"error": f"Target not found: {target_name or target_path}"}
            
        except Exception as e:
            error_msg = f"Error analyzing {analysis_type}: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return {"error": error_msg}
    
    async def send_progress(self, websocket: WebSocket, message: str, progress: int):
        """Send progress update to WebSocket."""
        await manager.send_personal_message({
            "type": "progress",
            "message": message,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }, websocket)
    
    async def send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to WebSocket."""
        await manager.send_personal_message({
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }, websocket)

# Global analyzer instance
analyzer = RealtimeAnalyzer()

async def handle_websocket_message(websocket: WebSocket, data: dict):
    """Handle incoming WebSocket messages."""
    try:
        message_type = data.get("type")
        
        if message_type == "load_repo":
            repo_url = data.get("repo_url")
            if not repo_url:
                await analyzer.send_error(websocket, "Repository URL is required")
                return
                
            result = await analyzer.load_repository(repo_url, websocket)
            await manager.send_personal_message({
                "type": "repo_loaded",
                "data": result
            }, websocket)
            
        elif message_type == "analyze_target":
            repo_url = data.get("repo_url")
            analysis_type = data.get("analysis_type")
            target_path = data.get("target_path")
            target_name = data.get("target_name")
            
            if repo_url not in manager.codebase_cache:
                await analyzer.send_error(websocket, "Repository not loaded")
                return
                
            codebase = manager.codebase_cache[repo_url]
            result = await analyzer.analyze_specific_target(
                codebase, analysis_type, target_path, target_name, websocket
            )
            
            await manager.send_personal_message({
                "type": "analysis_result",
                "data": result
            }, websocket)
            
        elif message_type == "ping":
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }, websocket)
            
        else:
            await analyzer.send_error(websocket, f"Unknown message type: {message_type}")
            
    except Exception as e:
        error_msg = f"Error handling WebSocket message: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        await analyzer.send_error(websocket, error_msg)

async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handle_websocket_message(websocket, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Export functions for use in main FastAPI app
__all__ = [
    'manager',
    'analyzer', 
    'websocket_endpoint',
    'RepoLoadRequest',
    'AnalysisRequest'
]
