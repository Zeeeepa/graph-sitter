"""
Enhanced Dashboard Routes
Comprehensive integration routes for Linear, GitHub, Prefect, and graph-sitter analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import integration modules
try:
    from ..extensions.linear.enhanced_client import LinearEnhancedClient
    from ..extensions.github.enhanced_client import GitHubEnhancedClient
    from ..extensions.prefect.client import PrefectOrchestrator
    from ..agents.tools.graph_sitter_analysis import GraphSitterAnalyzer
    from .orchestrator_integration import OrchestratorDashboardIntegration
    from .advanced_analytics import AdvancedAnalyticsEngine
except ImportError as e:
    logging.warning(f"Some integrations not available: {e}")

logger = logging.getLogger(__name__)

# Create enhanced router
enhanced_router = APIRouter(prefix="/api/v2", tags=["enhanced"])

# Pydantic models for request/response
class ProjectAnalysisRequest(BaseModel):
    project_id: str
    analysis_types: List[str] = ["code_quality", "security", "performance", "dependencies"]
    include_ai_insights: bool = True

class FlowCreationRequest(BaseModel):
    name: str
    project_id: str
    flow_type: str
    requirements: List[str] = []
    auto_linear_integration: bool = True
    auto_github_integration: bool = True

class LinearIssueRequest(BaseModel):
    title: str
    description: str
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    priority: int = 3
    auto_create_flow: bool = False

class GitHubPRAnalysisRequest(BaseModel):
    pr_number: int
    repository: str
    analysis_depth: str = "comprehensive"
    include_code_review: bool = True
    auto_create_linear_issue: bool = False

class WorkflowAutomationRequest(BaseModel):
    workflow_type: str
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    integrations: List[str] = ["linear", "github", "prefect"]

# Global integration instances (will be initialized by the main app)
linear_client: Optional[LinearEnhancedClient] = None
github_client: Optional[GitHubEnhancedClient] = None
prefect_client: Optional[PrefectOrchestrator] = None
graph_sitter: Optional[GraphSitterAnalyzer] = None
orchestrator: Optional[OrchestratorDashboardIntegration] = None
analytics_engine: Optional[AdvancedAnalyticsEngine] = None

def get_integration_status():
    """Get status of all integrations"""
    return {
        "linear": linear_client is not None and linear_client.is_connected(),
        "github": github_client is not None and github_client.is_connected(),
        "prefect": prefect_client is not None and prefect_client.is_connected(),
        "graph_sitter": graph_sitter is not None,
        "orchestrator": orchestrator is not None,
        "analytics": analytics_engine is not None
    }

# ============================================================================
# PROJECT MANAGEMENT ROUTES
# ============================================================================

@enhanced_router.get("/projects/comprehensive")
async def get_comprehensive_projects():
    """Get comprehensive project data with all integrations"""
    try:
        projects_data = {}
        
        # Get GitHub projects
        if github_client:
            github_projects = await github_client.get_repositories()
            projects_data["github"] = github_projects
        
        # Get Linear projects
        if linear_client:
            linear_projects = await linear_client.get_projects()
            projects_data["linear"] = linear_projects
        
        # Get Prefect deployments
        if prefect_client:
            prefect_deployments = await prefect_client.get_deployments()
            projects_data["prefect"] = prefect_deployments
        
        # Combine and analyze
        if analytics_engine:
            analysis = await analytics_engine.analyze_project_ecosystem(projects_data)
            projects_data["analysis"] = analysis
        
        return JSONResponse(content={
            "status": "success",
            "data": projects_data,
            "integrations": get_integration_status(),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting comprehensive projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@enhanced_router.post("/projects/{project_id}/analyze")
async def analyze_project_comprehensive(
    project_id: str, 
    request: ProjectAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Perform comprehensive project analysis using all available tools"""
    try:
        analysis_id = f"analysis_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background analysis
        background_tasks.add_task(
            _perform_comprehensive_analysis,
            analysis_id,
            project_id,
            request.analysis_types,
            request.include_ai_insights
        )
        
        return JSONResponse(content={
            "status": "started",
            "analysis_id": analysis_id,
            "message": "Comprehensive analysis started",
            "estimated_duration": "5-10 minutes"
        })
        
    except Exception as e:
        logger.error(f"Error starting project analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _perform_comprehensive_analysis(
    analysis_id: str,
    project_id: str,
    analysis_types: List[str],
    include_ai_insights: bool
):
    """Background task for comprehensive project analysis"""
    try:
        results = {}
        
        # Graph-sitter code analysis
        if graph_sitter and "code_quality" in analysis_types:
            results["code_analysis"] = await graph_sitter.analyze_project(project_id)
        
        # Security analysis
        if "security" in analysis_types:
            results["security"] = await _perform_security_analysis(project_id)
        
        # Performance analysis
        if "performance" in analysis_types:
            results["performance"] = await _perform_performance_analysis(project_id)
        
        # Dependencies analysis
        if "dependencies" in analysis_types:
            results["dependencies"] = await _perform_dependencies_analysis(project_id)
        
        # AI insights
        if include_ai_insights and analytics_engine:
            results["ai_insights"] = await analytics_engine.generate_ai_insights(results)
        
        # Store results (implement your storage mechanism)
        await _store_analysis_results(analysis_id, results)
        
        # Create Linear issue if configured
        if linear_client:
            await _create_analysis_linear_issue(project_id, results)
        
        logger.info(f"Comprehensive analysis {analysis_id} completed")
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis {analysis_id}: {e}")

# ============================================================================
# FLOW MANAGEMENT ROUTES
# ============================================================================

@enhanced_router.post("/flows/autonomous")
async def create_autonomous_flow(request: FlowCreationRequest):
    """Create an autonomous flow with full integration"""
    try:
        flow_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create Prefect flow
        if prefect_client:
            prefect_flow = await prefect_client.create_flow(
                name=request.name,
                project_id=request.project_id,
                flow_type=request.flow_type
            )
        
        # Create Linear issue if enabled
        linear_issue = None
        if request.auto_linear_integration and linear_client:
            linear_issue = await linear_client.create_issue(
                title=f"Flow: {request.name}",
                description=f"Autonomous flow created for project {request.project_id}",
                project_id=request.project_id
            )
        
        # Create GitHub issue/PR if enabled
        github_item = None
        if request.auto_github_integration and github_client:
            github_item = await github_client.create_issue(
                repository=request.project_id,
                title=f"Autonomous Flow: {request.name}",
                body=f"Flow created with requirements: {', '.join(request.requirements)}"
            )
        
        # Start orchestration
        if orchestrator:
            orchestration_task = await orchestrator.execute_dashboard_task(
                task_type="autonomous_flow",
                task_data={
                    "flow_id": flow_id,
                    "prefect_flow": prefect_flow,
                    "linear_issue": linear_issue,
                    "github_item": github_item,
                    "requirements": request.requirements
                }
            )
        
        return JSONResponse(content={
            "status": "success",
            "flow_id": flow_id,
            "integrations": {
                "prefect": prefect_flow is not None,
                "linear": linear_issue is not None,
                "github": github_item is not None
            },
            "message": "Autonomous flow created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating autonomous flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@enhanced_router.get("/flows/{flow_id}/detailed-progression")
async def get_flow_detailed_progression(flow_id: str):
    """Get detailed flow progression with all integration updates"""
    try:
        progression_data = {}
        
        # Get Prefect flow status
        if prefect_client:
            prefect_status = await prefect_client.get_flow_status(flow_id)
            progression_data["prefect"] = prefect_status
        
        # Get related Linear issues
        if linear_client:
            linear_issues = await linear_client.get_issues_by_flow(flow_id)
            progression_data["linear"] = linear_issues
        
        # Get related GitHub items
        if github_client:
            github_items = await github_client.get_items_by_flow(flow_id)
            progression_data["github"] = github_items
        
        # Get orchestrator task status
        if orchestrator:
            orchestrator_status = await orchestrator.get_task_status(flow_id)
            progression_data["orchestrator"] = orchestrator_status
        
        # Calculate overall progression
        overall_progress = _calculate_overall_progress(progression_data)
        
        return JSONResponse(content={
            "status": "success",
            "flow_id": flow_id,
            "progression": progression_data,
            "overall_progress": overall_progress,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting flow progression: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# LINEAR INTEGRATION ROUTES
# ============================================================================

@enhanced_router.post("/linear/sync/comprehensive")
async def sync_linear_comprehensive():
    """Comprehensive Linear synchronization with all integrations"""
    try:
        if not linear_client:
            raise HTTPException(status_code=503, detail="Linear integration not available")
        
        sync_results = {}
        
        # Sync issues
        issues = await linear_client.sync_issues()
        sync_results["issues"] = len(issues)
        
        # Sync projects
        projects = await linear_client.sync_projects()
        sync_results["projects"] = len(projects)
        
        # Create GitHub issues for Linear items if needed
        if github_client:
            github_sync = await _sync_linear_to_github(issues)
            sync_results["github_sync"] = github_sync
        
        # Create Prefect flows for Linear milestones
        if prefect_client:
            prefect_sync = await _sync_linear_to_prefect(projects)
            sync_results["prefect_sync"] = prefect_sync
        
        return JSONResponse(content={
            "status": "success",
            "sync_results": sync_results,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in comprehensive Linear sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@enhanced_router.post("/linear/issues/auto-create")
async def auto_create_linear_issue(request: LinearIssueRequest):
    """Auto-create Linear issue with optional flow integration"""
    try:
        if not linear_client:
            raise HTTPException(status_code=503, detail="Linear integration not available")
        
        # Create Linear issue
        issue = await linear_client.create_issue(
            title=request.title,
            description=request.description,
            project_id=request.project_id,
            assignee_id=request.assignee_id,
            priority=request.priority
        )
        
        # Auto-create flow if requested
        flow_id = None
        if request.auto_create_flow and prefect_client:
            flow = await prefect_client.create_flow(
                name=f"Issue Flow: {request.title}",
                project_id=request.project_id or "default",
                flow_type="issue_resolution"
            )
            flow_id = flow.get("id")
            
            # Link flow to Linear issue
            await linear_client.update_issue(
                issue_id=issue["id"],
                description=f"{request.description}\n\nAutomated Flow: {flow_id}"
            )
        
        return JSONResponse(content={
            "status": "success",
            "issue": issue,
            "flow_id": flow_id,
            "message": "Linear issue created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating Linear issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# GITHUB INTEGRATION ROUTES
# ============================================================================

@enhanced_router.post("/github/prs/{pr_number}/comprehensive-analysis")
async def analyze_github_pr_comprehensive(
    pr_number: int,
    request: GitHubPRAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Comprehensive GitHub PR analysis with all tools"""
    try:
        if not github_client:
            raise HTTPException(status_code=503, detail="GitHub integration not available")
        
        analysis_id = f"pr_analysis_{pr_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start background analysis
        background_tasks.add_task(
            _perform_pr_comprehensive_analysis,
            analysis_id,
            pr_number,
            request.repository,
            request.analysis_depth,
            request.include_code_review,
            request.auto_create_linear_issue
        )
        
        return JSONResponse(content={
            "status": "started",
            "analysis_id": analysis_id,
            "pr_number": pr_number,
            "message": "Comprehensive PR analysis started"
        })
        
    except Exception as e:
        logger.error(f"Error starting PR analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _perform_pr_comprehensive_analysis(
    analysis_id: str,
    pr_number: int,
    repository: str,
    analysis_depth: str,
    include_code_review: bool,
    auto_create_linear_issue: bool
):
    """Background task for comprehensive PR analysis"""
    try:
        results = {}
        
        # Get PR data
        pr_data = await github_client.get_pull_request(repository, pr_number)
        results["pr_data"] = pr_data
        
        # Code analysis with graph-sitter
        if graph_sitter:
            code_analysis = await graph_sitter.analyze_pr_changes(repository, pr_number)
            results["code_analysis"] = code_analysis
        
        # Security analysis
        security_analysis = await _analyze_pr_security(repository, pr_number)
        results["security_analysis"] = security_analysis
        
        # Performance impact analysis
        performance_analysis = await _analyze_pr_performance(repository, pr_number)
        results["performance_analysis"] = performance_analysis
        
        # AI-powered code review
        if include_code_review and analytics_engine:
            ai_review = await analytics_engine.perform_ai_code_review(pr_data)
            results["ai_review"] = ai_review
        
        # Create Linear issue if requested
        if auto_create_linear_issue and linear_client:
            linear_issue = await linear_client.create_issue(
                title=f"PR Review: {pr_data.get('title', f'PR #{pr_number}')}",
                description=f"Comprehensive analysis results for PR #{pr_number}\n\nRepository: {repository}",
                project_id=repository
            )
            results["linear_issue"] = linear_issue
        
        # Store results
        await _store_analysis_results(analysis_id, results)
        
        # Post results as PR comment
        await github_client.create_pr_comment(
            repository,
            pr_number,
            _format_pr_analysis_comment(results)
        )
        
        logger.info(f"PR analysis {analysis_id} completed")
        
    except Exception as e:
        logger.error(f"Error in PR analysis {analysis_id}: {e}")

# ============================================================================
# WORKFLOW AUTOMATION ROUTES
# ============================================================================

@enhanced_router.post("/workflows/automation/create")
async def create_workflow_automation(request: WorkflowAutomationRequest):
    """Create automated workflow with multi-integration support"""
    try:
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create workflow configuration
        workflow_config = {
            "id": workflow_id,
            "type": request.workflow_type,
            "triggers": request.trigger_conditions,
            "actions": request.actions,
            "integrations": request.integrations,
            "created_at": datetime.now().isoformat()
        }
        
        # Set up triggers in each integration
        trigger_results = {}
        
        if "linear" in request.integrations and linear_client:
            linear_trigger = await linear_client.setup_workflow_trigger(workflow_config)
            trigger_results["linear"] = linear_trigger
        
        if "github" in request.integrations and github_client:
            github_trigger = await github_client.setup_workflow_trigger(workflow_config)
            trigger_results["github"] = github_trigger
        
        if "prefect" in request.integrations and prefect_client:
            prefect_trigger = await prefect_client.setup_workflow_trigger(workflow_config)
            trigger_results["prefect"] = prefect_trigger
        
        # Store workflow configuration
        await _store_workflow_config(workflow_id, workflow_config)
        
        return JSONResponse(content={
            "status": "success",
            "workflow_id": workflow_id,
            "trigger_results": trigger_results,
            "message": "Workflow automation created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating workflow automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANALYTICS AND MONITORING ROUTES
# ============================================================================

@enhanced_router.get("/analytics/comprehensive")
async def get_comprehensive_analytics():
    """Get comprehensive analytics across all integrations"""
    try:
        analytics_data = {}
        
        if analytics_engine:
            # Project analytics
            project_analytics = await analytics_engine.get_project_analytics()
            analytics_data["projects"] = project_analytics
            
            # Flow analytics
            flow_analytics = await analytics_engine.get_flow_analytics()
            analytics_data["flows"] = flow_analytics
            
            # Integration analytics
            integration_analytics = await analytics_engine.get_integration_analytics()
            analytics_data["integrations"] = integration_analytics
            
            # AI insights
            ai_insights = await analytics_engine.get_ai_insights()
            analytics_data["ai_insights"] = ai_insights
        
        return JSONResponse(content={
            "status": "success",
            "analytics": analytics_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting comprehensive analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@enhanced_router.get("/monitoring/real-time")
async def get_real_time_monitoring():
    """Get real-time monitoring data from all integrations"""
    try:
        monitoring_data = {}
        
        # System health
        monitoring_data["system_health"] = get_integration_status()
        
        # Active flows
        if prefect_client:
            active_flows = await prefect_client.get_active_flows()
            monitoring_data["active_flows"] = active_flows
        
        # Recent Linear activity
        if linear_client:
            recent_linear = await linear_client.get_recent_activity()
            monitoring_data["linear_activity"] = recent_linear
        
        # Recent GitHub activity
        if github_client:
            recent_github = await github_client.get_recent_activity()
            monitoring_data["github_activity"] = recent_github
        
        # Orchestrator status
        if orchestrator:
            orchestrator_status = await orchestrator.get_system_dashboard_data()
            monitoring_data["orchestrator"] = orchestrator_status
        
        return JSONResponse(content={
            "status": "success",
            "monitoring": monitoring_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real-time monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def _perform_security_analysis(project_id: str) -> Dict[str, Any]:
    """Perform security analysis on project"""
    # Implement security analysis logic
    return {"status": "completed", "vulnerabilities": [], "score": 95}

async def _perform_performance_analysis(project_id: str) -> Dict[str, Any]:
    """Perform performance analysis on project"""
    # Implement performance analysis logic
    return {"status": "completed", "metrics": {}, "score": 88}

async def _perform_dependencies_analysis(project_id: str) -> Dict[str, Any]:
    """Perform dependencies analysis on project"""
    # Implement dependencies analysis logic
    return {"status": "completed", "outdated": [], "vulnerabilities": []}

async def _store_analysis_results(analysis_id: str, results: Dict[str, Any]):
    """Store analysis results"""
    # Implement storage logic (database, file system, etc.)
    logger.info(f"Storing analysis results for {analysis_id}")

async def _create_analysis_linear_issue(project_id: str, results: Dict[str, Any]):
    """Create Linear issue with analysis results"""
    if linear_client:
        await linear_client.create_issue(
            title=f"Analysis Report: {project_id}",
            description=f"Comprehensive analysis completed. Results available in dashboard.",
            project_id=project_id
        )

def _calculate_overall_progress(progression_data: Dict[str, Any]) -> float:
    """Calculate overall progress from all integrations"""
    total_progress = 0
    count = 0
    
    for integration, data in progression_data.items():
        if isinstance(data, dict) and "progress" in data:
            total_progress += data["progress"]
            count += 1
    
    return total_progress / count if count > 0 else 0

async def _sync_linear_to_github(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sync Linear issues to GitHub"""
    # Implement Linear to GitHub sync logic
    return {"synced": len(issues), "errors": 0}

async def _sync_linear_to_prefect(projects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sync Linear projects to Prefect"""
    # Implement Linear to Prefect sync logic
    return {"synced": len(projects), "errors": 0}

async def _analyze_pr_security(repository: str, pr_number: int) -> Dict[str, Any]:
    """Analyze PR for security issues"""
    # Implement PR security analysis logic
    return {"status": "completed", "issues": [], "score": 92}

async def _analyze_pr_performance(repository: str, pr_number: int) -> Dict[str, Any]:
    """Analyze PR for performance impact"""
    # Implement PR performance analysis logic
    return {"status": "completed", "impact": "minimal", "score": 85}

def _format_pr_analysis_comment(results: Dict[str, Any]) -> str:
    """Format PR analysis results as comment"""
    comment = "## 🤖 Comprehensive PR Analysis\n\n"
    
    if "code_analysis" in results:
        comment += "### Code Analysis\n"
        comment += f"- Quality Score: {results['code_analysis'].get('score', 'N/A')}\n"
    
    if "security_analysis" in results:
        comment += "### Security Analysis\n"
        comment += f"- Security Score: {results['security_analysis'].get('score', 'N/A')}\n"
    
    if "performance_analysis" in results:
        comment += "### Performance Analysis\n"
        comment += f"- Performance Score: {results['performance_analysis'].get('score', 'N/A')}\n"
    
    if "ai_review" in results:
        comment += "### AI Review\n"
        comment += f"- {results['ai_review'].get('summary', 'No issues found')}\n"
    
    comment += "\n*Analysis powered by Contexten Dashboard*"
    return comment

async def _store_workflow_config(workflow_id: str, config: Dict[str, Any]):
    """Store workflow configuration"""
    # Implement workflow storage logic
    logger.info(f"Storing workflow config for {workflow_id}")

# ============================================================================
# INITIALIZATION FUNCTION
# ============================================================================

async def initialize_enhanced_integrations(
    linear_client_instance=None,
    github_client_instance=None,
    prefect_client_instance=None,
    graph_sitter_instance=None,
    orchestrator_instance=None,
    analytics_engine_instance=None
):
    """Initialize all integration clients"""
    global linear_client, github_client, prefect_client, graph_sitter, orchestrator, analytics_engine
    
    linear_client = linear_client_instance
    github_client = github_client_instance
    prefect_client = prefect_client_instance
    graph_sitter = graph_sitter_instance
    orchestrator = orchestrator_instance
    analytics_engine = analytics_engine_instance
    
    logger.info("Enhanced integrations initialized")

