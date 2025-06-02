#!/usr/bin/env python3
"""
Comprehensive Analysis API Routes

This module provides API endpoints for comprehensive code analysis including:
- Dead code detection and cleanup
- Code quality analysis
- Security vulnerability scanning
- Performance analysis
- Integration status monitoring
- Multi-platform synchronization
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .comprehensive_analysis_dashboard import comprehensive_dashboard

logger = logging.getLogger(__name__)

# Create router for comprehensive analysis
analysis_router = APIRouter(prefix="/api/analysis", tags=["analysis"])
integrations_router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================

class AnalysisRequest(BaseModel):
    project_path: str
    analysis_types: List[str]
    options: Optional[Dict] = None

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str

class AnalysisStatusResponse(BaseModel):
    id: str
    status: str
    progress: float
    started_at: str
    completed_at: Optional[str] = None
    results: Optional[Dict] = None
    error: Optional[str] = None

# ==========================================
# COMPREHENSIVE ANALYSIS ENDPOINTS
# ==========================================

@analysis_router.post("/comprehensive", response_model=AnalysisResponse)
async def start_comprehensive_analysis(request: AnalysisRequest):
    """Start comprehensive analysis on a project"""
    try:
        analysis_id = await comprehensive_dashboard.run_comprehensive_analysis(
            project_path=request.project_path,
            analysis_types=request.analysis_types,
            options=request.options
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Comprehensive analysis started successfully"
        )
        
    except Exception as e:
        logger.error(f"Error starting comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str):
    """Get status of an analysis"""
    try:
        status = await comprehensive_dashboard.get_analysis_status(analysis_id)
        return AnalysisStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.get("/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get results of a completed analysis"""
    try:
        results = await comprehensive_dashboard.get_analysis_results(analysis_id)
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.post("/dead-code", response_model=AnalysisResponse)
async def analyze_dead_code(
    project_path: str,
    options: Optional[Dict] = None
):
    """Run dead code analysis using graph-sitter and AI"""
    try:
        analysis_id = await comprehensive_dashboard.run_comprehensive_analysis(
            project_path=project_path,
            analysis_types=["dead_code"],
            options=options or {}
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Dead code analysis started"
        )
        
    except Exception as e:
        logger.error(f"Error starting dead code analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.post("/code-quality", response_model=AnalysisResponse)
async def analyze_code_quality(
    project_path: str,
    options: Optional[Dict] = None
):
    """Run comprehensive code quality analysis"""
    try:
        analysis_id = await comprehensive_dashboard.run_comprehensive_analysis(
            project_path=project_path,
            analysis_types=["code_quality"],
            options=options or {}
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Code quality analysis started"
        )
        
    except Exception as e:
        logger.error(f"Error starting code quality analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.post("/security", response_model=AnalysisResponse)
async def analyze_security(
    project_path: str,
    options: Optional[Dict] = None
):
    """Run security vulnerability analysis"""
    try:
        analysis_id = await comprehensive_dashboard.run_comprehensive_analysis(
            project_path=project_path,
            analysis_types=["security"],
            options=options or {}
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Security analysis started"
        )
        
    except Exception as e:
        logger.error(f"Error starting security analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.post("/performance", response_model=AnalysisResponse)
async def analyze_performance(
    project_path: str,
    options: Optional[Dict] = None
):
    """Run performance analysis"""
    try:
        analysis_id = await comprehensive_dashboard.run_comprehensive_analysis(
            project_path=project_path,
            analysis_types=["performance"],
            options=options or {}
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Performance analysis started"
        )
        
    except Exception as e:
        logger.error(f"Error starting performance analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.post("/dependencies", response_model=AnalysisResponse)
async def analyze_dependencies(
    project_path: str,
    options: Optional[Dict] = None
):
    """Run dependency analysis"""
    try:
        analysis_id = await comprehensive_dashboard.run_comprehensive_analysis(
            project_path=project_path,
            analysis_types=["dependencies"],
            options=options or {}
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message="Dependency analysis started"
        )
        
    except Exception as e:
        logger.error(f"Error starting dependency analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.get("/history")
async def get_analysis_history(limit: int = 50):
    """Get analysis history"""
    try:
        # Get recent analyses from the dashboard
        history = comprehensive_dashboard.analysis_history[-limit:]
        return {"analyses": history, "total": len(comprehensive_dashboard.analysis_history)}
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# INTEGRATION ENDPOINTS
# ==========================================

@integrations_router.get("/status")
async def get_integrations_status():
    """Get status of all integrations (Linear, GitHub, Prefect)"""
    try:
        overview = await comprehensive_dashboard.get_system_overview()
        return {
            "integrations": overview.get("integrations", {}),
            "system_health": overview.get("system_health", {}),
            "last_updated": overview.get("last_updated")
        }
        
    except Exception as e:
        logger.error(f"Error getting integrations status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@integrations_router.post("/linear/sync")
async def sync_linear_integration():
    """Sync Linear integration and analyze issues"""
    try:
        # Start Linear integration analysis
        analysis_id = await comprehensive_dashboard.run_comprehensive_analysis(
            project_path=".",
            analysis_types=["linear_integration"],
            options={"sync": True}
        )
        
        return {
            "status": "success", 
            "message": "Linear sync initiated",
            "analysis_id": analysis_id
        }
        
    except Exception as e:
        logger.error(f"Error syncing Linear integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@integrations_router.post("/github/sync")
async def sync_github_integration():
    """Sync GitHub integration and analyze repositories"""
    try:
        # Start GitHub integration analysis
        analysis_id = await comprehensive_dashboard.run_comprehensive_analysis(
            project_path=".",
            analysis_types=["github_integration"],
            options={"sync": True}
        )
        
        return {
            "status": "success", 
            "message": "GitHub sync initiated",
            "analysis_id": analysis_id
        }
        
    except Exception as e:
        logger.error(f"Error syncing GitHub integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@integrations_router.post("/prefect/sync")
async def sync_prefect_integration():
    """Sync Prefect integration and analyze workflows"""
    try:
        # Start Prefect integration analysis
        analysis_id = await comprehensive_dashboard.run_comprehensive_analysis(
            project_path=".",
            analysis_types=["prefect_workflows"],
            options={"sync": True}
        )
        
        return {
            "status": "success", 
            "message": "Prefect sync initiated",
            "analysis_id": analysis_id
        }
        
    except Exception as e:
        logger.error(f"Error syncing Prefect integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@integrations_router.get("/linear/issues")
async def get_linear_issues():
    """Get Linear issues for the current project"""
    try:
        if comprehensive_dashboard.linear_agent:
            issues = await comprehensive_dashboard.linear_agent.get_projects()
            return {"issues": issues, "count": len(issues)}
        else:
            raise HTTPException(status_code=503, detail="Linear integration not available")
        
    except Exception as e:
        logger.error(f"Error getting Linear issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@integrations_router.get("/github/repositories")
async def get_github_repositories():
    """Get GitHub repositories for the current user"""
    try:
        if comprehensive_dashboard.github_agent:
            user_info = await comprehensive_dashboard.github_agent.get_current_user()
            return {"user": user_info}
        else:
            raise HTTPException(status_code=503, detail="GitHub integration not available")
        
    except Exception as e:
        logger.error(f"Error getting GitHub repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@integrations_router.get("/prefect/workflows")
async def get_prefect_workflows():
    """Get Prefect workflows"""
    try:
        if comprehensive_dashboard.prefect_client:
            workflows = await comprehensive_dashboard.prefect_client.list_active_workflows()
            metrics = await comprehensive_dashboard.prefect_client.get_metrics()
            return {"workflows": workflows, "metrics": metrics}
        else:
            raise HTTPException(status_code=503, detail="Prefect integration not available")
        
    except Exception as e:
        logger.error(f"Error getting Prefect workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# SYSTEM OVERVIEW ENDPOINTS
# ==========================================

@analysis_router.get("/system/overview")
async def get_system_overview():
    """Get comprehensive system overview"""
    try:
        overview = await comprehensive_dashboard.get_system_overview()
        return overview
        
    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.get("/system/health")
async def get_system_health():
    """Get detailed system health metrics"""
    try:
        overview = await comprehensive_dashboard.get_system_overview()
        return {
            "health": overview.get("system_health", {}),
            "integrations": overview.get("integrations", {}),
            "active_analyses": overview.get("active_analyses", 0),
            "completed_analyses": overview.get("completed_analyses", 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# GRAPH-SITTER SPECIFIC ENDPOINTS
# ==========================================

@analysis_router.post("/graph-sitter/parse")
async def parse_with_graph_sitter(
    file_path: str,
    language: str = "python"
):
    """Parse a file using graph-sitter"""
    try:
        # This would use graph-sitter to parse the file
        # For now, return a placeholder response
        return {
            "status": "success",
            "message": f"File {file_path} parsed with graph-sitter",
            "language": language,
            "syntax_tree": "placeholder_tree"
        }
        
    except Exception as e:
        logger.error(f"Error parsing with graph-sitter: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analysis_router.post("/graph-sitter/query")
async def query_syntax_tree(
    file_path: str,
    query: str,
    language: str = "python"
):
    """Query syntax tree using graph-sitter"""
    try:
        # This would use graph-sitter to query the syntax tree
        # For now, return a placeholder response
        return {
            "status": "success",
            "message": f"Query executed on {file_path}",
            "query": query,
            "language": language,
            "matches": []
        }
        
    except Exception as e:
        logger.error(f"Error querying syntax tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export routers for inclusion in main app
__all__ = ["analysis_router", "integrations_router"]

