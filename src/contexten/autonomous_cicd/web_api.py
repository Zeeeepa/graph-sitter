"""
Web API for Autonomous CI/CD System

Provides REST API endpoints for managing and monitoring the CI/CD system.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .core import AutonomousCICD, PipelineResult
from .config import CICDConfig


# Pydantic models for API
class PipelineRequest(BaseModel):
    pipeline_type: str = "full"
    branch: str = "develop"
    changes: List[str] = []
    trigger_data: Dict[str, Any] = {}


class PipelineResponse(BaseModel):
    pipeline_id: str
    status: str
    message: str


class SystemStatus(BaseModel):
    status: str
    uptime: float
    active_pipelines: int
    total_pipelines: int
    success_rate: float
    last_pipeline: Optional[str]


class MetricsResponse(BaseModel):
    total_pipelines: int
    successful_pipelines: int
    failed_pipelines: int
    success_rate: float
    average_duration: float
    active_pipelines: int


# Global CI/CD system instance
cicd_system: Optional[AutonomousCICD] = None
system_start_time = time.time()


def get_cicd_system() -> AutonomousCICD:
    """Dependency to get CI/CD system instance"""
    if cicd_system is None:
        raise HTTPException(status_code=503, detail="CI/CD system not initialized")
    return cicd_system


# Create FastAPI app
app = FastAPI(
    title="Autonomous CI/CD System",
    description="REST API for Graph-Sitter Autonomous CI/CD",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize CI/CD system on startup"""
    global cicd_system
    
    try:
        config = CICDConfig.from_env()
        cicd_system = AutonomousCICD(config)
        await cicd_system.initialize()
        
    except Exception as e:
        print(f"Failed to initialize CI/CD system: {e}")
        # Continue without CI/CD system for API documentation


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown CI/CD system"""
    global cicd_system
    
    if cicd_system:
        await cicd_system.shutdown()


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "Autonomous CI/CD System",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=SystemStatus)
async def health_check(cicd: AutonomousCICD = Depends(get_cicd_system)):
    """Health check endpoint"""
    
    metrics = await cicd.get_system_metrics()
    uptime = time.time() - system_start_time
    
    return SystemStatus(
        status="healthy",
        uptime=uptime,
        active_pipelines=metrics["active_pipelines"],
        total_pipelines=metrics["total_pipelines"],
        success_rate=metrics["success_rate"],
        last_pipeline=None  # Would get from recent pipelines
    )


@app.post("/pipelines", response_model=PipelineResponse)
async def create_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks,
    cicd: AutonomousCICD = Depends(get_cicd_system)
):
    """Create and execute a new pipeline"""
    
    try:
        # Create trigger event
        trigger_event = {
            "branch": request.branch,
            "changes": request.changes,
            "trigger_type": "api",
            **request.trigger_data
        }
        
        # Execute pipeline in background
        result = await cicd.execute_pipeline(
            trigger_event=trigger_event,
            pipeline_type=request.pipeline_type
        )
        
        return PipelineResponse(
            pipeline_id=result.pipeline_id,
            status=result.status,
            message=f"Pipeline {result.pipeline_id} started successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipelines/{pipeline_id}", response_model=Dict[str, Any])
async def get_pipeline(
    pipeline_id: str,
    cicd: AutonomousCICD = Depends(get_cicd_system)
):
    """Get pipeline status and results"""
    
    result = await cicd.get_pipeline_status(pipeline_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return {
        "pipeline_id": result.pipeline_id,
        "status": result.status,
        "start_time": result.start_time,
        "end_time": result.end_time,
        "duration": result.end_time - result.start_time if result.end_time else None,
        "stages": result.stages,
        "artifacts": result.artifacts,
        "errors": result.errors,
        "metrics": result.metrics
    }


@app.get("/pipelines", response_model=List[Dict[str, Any]])
async def list_pipelines(
    limit: int = 10,
    status: Optional[str] = None,
    cicd: AutonomousCICD = Depends(get_cicd_system)
):
    """List recent pipelines"""
    
    pipelines = cicd.pipeline_history[-limit:]
    
    if status:
        pipelines = [p for p in pipelines if p.status == status]
    
    return [
        {
            "pipeline_id": p.pipeline_id,
            "status": p.status,
            "start_time": p.start_time,
            "end_time": p.end_time,
            "duration": p.end_time - p.start_time if p.end_time else None,
            "stage_count": len(p.stages),
            "error_count": len(p.errors)
        }
        for p in pipelines
    ]


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(cicd: AutonomousCICD = Depends(get_cicd_system)):
    """Get system metrics"""
    
    metrics = await cicd.get_system_metrics()
    
    return MetricsResponse(
        total_pipelines=metrics["total_pipelines"],
        successful_pipelines=metrics["successful_pipelines"],
        failed_pipelines=metrics["total_pipelines"] - metrics["successful_pipelines"],
        success_rate=metrics["success_rate"],
        average_duration=metrics["average_duration"],
        active_pipelines=metrics["active_pipelines"]
    )


@app.post("/analyze", response_model=Dict[str, Any])
async def analyze_code(
    branch: str = "develop",
    files: List[str] = [],
    cicd: AutonomousCICD = Depends(get_cicd_system)
):
    """Run code analysis"""
    
    try:
        # Create analysis-only pipeline
        trigger_event = {
            "branch": branch,
            "changes": files,
            "trigger_type": "api_analysis"
        }
        
        result = await cicd.execute_pipeline(
            trigger_event=trigger_event,
            pipeline_type="analysis"
        )
        
        return {
            "pipeline_id": result.pipeline_id,
            "status": result.status,
            "analysis_results": result.stages.get("analysis", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test", response_model=Dict[str, Any])
async def run_tests(
    branch: str = "develop",
    files: List[str] = [],
    cicd: AutonomousCICD = Depends(get_cicd_system)
):
    """Run tests"""
    
    try:
        # Create test-only pipeline
        trigger_event = {
            "branch": branch,
            "changes": files,
            "trigger_type": "api_test"
        }
        
        result = await cicd.execute_pipeline(
            trigger_event=trigger_event,
            pipeline_type="test"
        )
        
        return {
            "pipeline_id": result.pipeline_id,
            "status": result.status,
            "test_results": result.stages.get("testing", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/deploy", response_model=Dict[str, Any])
async def deploy(
    branch: str = "develop",
    environment: str = "staging",
    cicd: AutonomousCICD = Depends(get_cicd_system)
):
    """Deploy application"""
    
    try:
        # Create deployment-only pipeline
        trigger_event = {
            "branch": branch,
            "environment": environment,
            "trigger_type": "api_deploy"
        }
        
        result = await cicd.execute_pipeline(
            trigger_event=trigger_event,
            pipeline_type="deploy"
        )
        
        return {
            "pipeline_id": result.pipeline_id,
            "status": result.status,
            "deployment_results": result.stages.get("deployment", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config", response_model=Dict[str, Any])
async def get_config(cicd: AutonomousCICD = Depends(get_cicd_system)):
    """Get system configuration"""
    return cicd.config.to_dict()


@app.post("/webhooks/github")
async def github_webhook(
    payload: Dict[str, Any],
    cicd: AutonomousCICD = Depends(get_cicd_system)
):
    """GitHub webhook endpoint"""
    
    try:
        # Forward to GitHub trigger
        github_trigger = cicd.triggers.get("github")
        if github_trigger:
            # This would be handled by the trigger's webhook handler
            return {"status": "received"}
        else:
            raise HTTPException(status_code=503, detail="GitHub trigger not available")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhooks/linear")
async def linear_webhook(
    payload: Dict[str, Any],
    cicd: AutonomousCICD = Depends(get_cicd_system)
):
    """Linear webhook endpoint"""
    
    try:
        # Forward to Linear trigger
        linear_trigger = cicd.triggers.get("linear")
        if linear_trigger:
            await linear_trigger.handle_linear_event(payload)
            return {"status": "received"}
        else:
            raise HTTPException(status_code=503, detail="Linear trigger not available")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

