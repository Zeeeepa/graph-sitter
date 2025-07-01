"""
Comprehensive Linear Integration for Dashboard

This module provides a complete Linear integration for the Contexten dashboard,
including issue management, project tracking, workflow automation, and real-time updates.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..extensions.linear.enhanced_agent import EnhancedLinearAgent, LinearAgentConfig
from ..extensions.linear.enhanced_client import EnhancedLinearClient
from ..extensions.linear.workflow.automation import WorkflowAutomation
from ..extensions.linear.webhook.processor import WebhookProcessor
from ..extensions.linear.events.manager import EventManager
from ..extensions.linear.types import LinearIssue, LinearProject, LinearTeam, LinearUser
from ..shared.logging.get_logger import get_logger

logger = get_logger(__name__)

# Pydantic Models for API
class LinearIssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    team_id: str
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    priority: Optional[int] = None
    labels: Optional[List[str]] = None

class LinearIssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    state_id: Optional[str] = None
    assignee_id: Optional[str] = None
    priority: Optional[int] = None
    labels: Optional[List[str]] = None

class LinearProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    team_id: str
    target_date: Optional[datetime] = None

class LinearDashboardConfig:
    """Configuration for Linear Dashboard Integration"""
    def __init__(self, api_key: str, webhook_secret: Optional[str] = None):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.auto_sync = True
        self.sync_interval = 300  # 5 minutes
        self.cache_ttl = 600  # 10 minutes

class LinearDashboardManager:
    """
    Comprehensive Linear Dashboard Manager
    
    Provides:
    - Issue management (CRUD operations)
    - Project tracking and analytics
    - Team management
    - Workflow automation
    - Real-time updates via webhooks
    - Dashboard metrics and insights
    """
    
    def __init__(self, config: LinearDashboardConfig):
        self.config = config
        self.agent_config = LinearAgentConfig(
            api_key=config.api_key,
            webhook_secret=config.webhook_secret,
            auto_assignment=True,
            workflow_automation=True,
            event_processing=True
        )
        self.agent = EnhancedLinearAgent(self.agent_config)
        self.client = EnhancedLinearClient(config.api_key)
        self.workflow_automation = WorkflowAutomation(self.agent_config)
        self.webhook_processor = WebhookProcessor(config.webhook_secret)
        self.event_manager = EventManager()
        
        # Cache for dashboard data
        self._cache = {}
        self._cache_timestamps = {}
        
        # Background tasks
        self._sync_task = None
        self._running = False
    
    async def start(self):
        """Start the Linear dashboard manager"""
        self._running = True
        if self.config.auto_sync:
            self._sync_task = asyncio.create_task(self._background_sync())
        logger.info("Linear Dashboard Manager started")
    
    async def stop(self):
        """Stop the Linear dashboard manager"""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
        logger.info("Linear Dashboard Manager stopped")
    
    async def _background_sync(self):
        """Background task for syncing Linear data"""
        while self._running:
            try:
                await self._sync_dashboard_data()
                await asyncio.sleep(self.config.sync_interval)
            except Exception as e:
                logger.error(f"Error in background sync: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _sync_dashboard_data(self):
        """Sync all dashboard data from Linear"""
        try:
            # Sync teams, projects, and issues
            await self._cache_teams()
            await self._cache_projects()
            await self._cache_recent_issues()
            logger.debug("Dashboard data synced successfully")
        except Exception as e:
            logger.error(f"Error syncing dashboard data: {e}")
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache_timestamps:
            return False
        return (datetime.now() - self._cache_timestamps[key]).seconds < self.config.cache_ttl
    
    def _set_cache(self, key: str, data: Any):
        """Set cached data with timestamp"""
        self._cache[key] = data
        self._cache_timestamps[key] = datetime.now()
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """Get cached data if valid"""
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None
    
    # Team Management
    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams with caching"""
        cached = self._get_cache("teams")
        if cached:
            return cached
        
        teams = await self.client.get_teams()
        team_data = []
        for team in teams:
            team_info = {
                "id": team.id,
                "name": team.name,
                "key": team.key,
                "description": team.description,
                "member_count": len(team.members) if team.members else 0,
                "active_issues": await self._get_team_active_issues_count(team.id),
                "completed_issues": await self._get_team_completed_issues_count(team.id)
            }
            team_data.append(team_info)
        
        self._set_cache("teams", team_data)
        return team_data
    
    async def _cache_teams(self):
        """Cache teams data"""
        await self.get_teams()
    
    async def _get_team_active_issues_count(self, team_id: str) -> int:
        """Get count of active issues for a team"""
        try:
            issues = await self.client.get_team_issues(team_id, states=["Todo", "In Progress", "In Review"])
            return len(issues)
        except Exception as e:
            logger.error(f"Error getting active issues count for team {team_id}: {e}")
            return 0
    
    async def _get_team_completed_issues_count(self, team_id: str) -> int:
        """Get count of completed issues for a team"""
        try:
            # Get issues completed in the last 30 days
            since_date = datetime.now() - timedelta(days=30)
            issues = await self.client.get_team_issues(
                team_id, 
                states=["Done", "Completed"],
                since=since_date
            )
            return len(issues)
        except Exception as e:
            logger.error(f"Error getting completed issues count for team {team_id}: {e}")
            return 0
    
    # Project Management
    async def get_projects(self, team_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get projects with analytics"""
        cache_key = f"projects_{team_id or 'all'}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        projects = await self.client.get_projects(team_id=team_id)
        project_data = []
        
        for project in projects:
            # Get project analytics
            analytics = await self._get_project_analytics(project.id)
            
            project_info = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "state": project.state,
                "progress": project.progress,
                "target_date": project.target_date.isoformat() if project.target_date else None,
                "team_id": project.team_id,
                "team_name": project.team.name if project.team else None,
                "analytics": analytics,
                "health_status": self._calculate_project_health(analytics),
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None
            }
            project_data.append(project_info)
        
        self._set_cache(cache_key, project_data)
        return project_data
    
    async def _cache_projects(self):
        """Cache projects data"""
        await self.get_projects()
    
    async def _get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project analytics"""
        try:
            issues = await self.client.get_project_issues(project_id)
            
            total_issues = len(issues)
            completed_issues = len([i for i in issues if i.state.name in ["Done", "Completed"]])
            in_progress_issues = len([i for i in issues if i.state.name in ["In Progress", "In Review"]])
            todo_issues = len([i for i in issues if i.state.name == "Todo"])
            
            # Calculate velocity (issues completed per week)
            now = datetime.now()
            week_ago = now - timedelta(days=7)
            recent_completed = len([
                i for i in issues 
                if i.state.name in ["Done", "Completed"] and 
                i.completed_at and i.completed_at >= week_ago
            ])
            
            # Calculate average completion time
            completed_with_times = [
                i for i in issues 
                if i.state.name in ["Done", "Completed"] and 
                i.created_at and i.completed_at
            ]
            
            avg_completion_time = None
            if completed_with_times:
                total_time = sum([
                    (i.completed_at - i.created_at).total_seconds() 
                    for i in completed_with_times
                ])
                avg_completion_time = total_time / len(completed_with_times) / 3600  # hours
            
            return {
                "total_issues": total_issues,
                "completed_issues": completed_issues,
                "in_progress_issues": in_progress_issues,
                "todo_issues": todo_issues,
                "completion_rate": (completed_issues / total_issues * 100) if total_issues > 0 else 0,
                "weekly_velocity": recent_completed,
                "avg_completion_time_hours": avg_completion_time,
                "burndown_data": await self._get_burndown_data(project_id)
            }
        except Exception as e:
            logger.error(f"Error getting project analytics for {project_id}: {e}")
            return {
                "total_issues": 0,
                "completed_issues": 0,
                "in_progress_issues": 0,
                "todo_issues": 0,
                "completion_rate": 0,
                "weekly_velocity": 0,
                "avg_completion_time_hours": None,
                "burndown_data": []
            }
    
    async def _get_burndown_data(self, project_id: str) -> List[Dict[str, Any]]:
        """Get burndown chart data for a project"""
        try:
            # Get issues with completion dates over the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            issues = await self.client.get_project_issues(project_id)
            total_issues = len(issues)
            
            burndown_data = []
            current_date = start_date
            
            while current_date <= end_date:
                completed_by_date = len([
                    i for i in issues 
                    if i.completed_at and i.completed_at <= current_date
                ])
                remaining = total_issues - completed_by_date
                
                burndown_data.append({
                    "date": current_date.isoformat(),
                    "remaining_issues": remaining,
                    "completed_issues": completed_by_date
                })
                
                current_date += timedelta(days=1)
            
            return burndown_data
        except Exception as e:
            logger.error(f"Error getting burndown data for project {project_id}: {e}")
            return []
    
    def _calculate_project_health(self, analytics: Dict[str, Any]) -> str:
        """Calculate project health status based on analytics"""
        completion_rate = analytics.get("completion_rate", 0)
        weekly_velocity = analytics.get("weekly_velocity", 0)
        
        if completion_rate >= 80:
            return "excellent"
        elif completion_rate >= 60:
            return "good"
        elif completion_rate >= 40:
            return "fair"
        elif weekly_velocity > 0:
            return "active"
        else:
            return "at_risk"
    
    # Issue Management
    async def get_issues(
        self, 
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get issues with filtering and enriched data"""
        try:
            issues = await self.client.get_issues(
                team_id=team_id,
                project_id=project_id,
                assignee_id=assignee_id,
                state=state,
                limit=limit
            )
            
            issue_data = []
            for issue in issues:
                issue_info = {
                    "id": issue.id,
                    "title": issue.title,
                    "description": issue.description,
                    "state": {
                        "id": issue.state.id,
                        "name": issue.state.name,
                        "color": issue.state.color
                    } if issue.state else None,
                    "priority": issue.priority,
                    "assignee": {
                        "id": issue.assignee.id,
                        "name": issue.assignee.name,
                        "email": issue.assignee.email
                    } if issue.assignee else None,
                    "team": {
                        "id": issue.team.id,
                        "name": issue.team.name,
                        "key": issue.team.key
                    } if issue.team else None,
                    "project": {
                        "id": issue.project.id,
                        "name": issue.project.name
                    } if issue.project else None,
                    "labels": [{"id": l.id, "name": l.name, "color": l.color} for l in issue.labels] if issue.labels else [],
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "completed_at": issue.completed_at.isoformat() if issue.completed_at else None,
                    "url": issue.url
                }
                issue_data.append(issue_info)
            
            return issue_data
        except Exception as e:
            logger.error(f"Error getting issues: {e}")
            return []
    
    async def _cache_recent_issues(self):
        """Cache recent issues data"""
        recent_issues = await self.get_issues(limit=100)
        self._set_cache("recent_issues", recent_issues)
    
    async def create_issue(self, issue_data: LinearIssueCreate) -> Dict[str, Any]:
        """Create a new Linear issue"""
        try:
            issue = await self.agent.create_issue(
                title=issue_data.title,
                description=issue_data.description,
                team_id=issue_data.team_id,
                project_id=issue_data.project_id,
                assignee_id=issue_data.assignee_id,
                priority=issue_data.priority,
                labels=issue_data.labels
            )
            
            # Invalidate relevant caches
            self._invalidate_caches(["recent_issues", f"projects_{issue_data.team_id}"])
            
            return {
                "id": issue.id,
                "title": issue.title,
                "url": issue.url,
                "created_at": issue.created_at.isoformat() if issue.created_at else None
            }
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create issue: {str(e)}")
    
    async def update_issue(self, issue_id: str, issue_data: LinearIssueUpdate) -> Dict[str, Any]:
        """Update an existing Linear issue"""
        try:
            issue = await self.agent.update_issue(
                issue_id=issue_id,
                title=issue_data.title,
                description=issue_data.description,
                state_id=issue_data.state_id,
                assignee_id=issue_data.assignee_id,
                priority=issue_data.priority,
                labels=issue_data.labels
            )
            
            # Invalidate relevant caches
            self._invalidate_caches(["recent_issues"])
            
            return {
                "id": issue.id,
                "title": issue.title,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None
            }
        except Exception as e:
            logger.error(f"Error updating issue {issue_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update issue: {str(e)}")
    
    async def get_issue_details(self, issue_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific issue"""
        try:
            issue = await self.client.get_issue(issue_id)
            comments = await self.client.get_issue_comments(issue_id)
            
            return {
                "issue": {
                    "id": issue.id,
                    "title": issue.title,
                    "description": issue.description,
                    "state": {
                        "id": issue.state.id,
                        "name": issue.state.name,
                        "color": issue.state.color
                    } if issue.state else None,
                    "priority": issue.priority,
                    "assignee": {
                        "id": issue.assignee.id,
                        "name": issue.assignee.name,
                        "email": issue.assignee.email
                    } if issue.assignee else None,
                    "team": {
                        "id": issue.team.id,
                        "name": issue.team.name,
                        "key": issue.team.key
                    } if issue.team else None,
                    "project": {
                        "id": issue.project.id,
                        "name": issue.project.name
                    } if issue.project else None,
                    "labels": [{"id": l.id, "name": l.name, "color": l.color} for l in issue.labels] if issue.labels else [],
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "completed_at": issue.completed_at.isoformat() if issue.completed_at else None,
                    "url": issue.url
                },
                "comments": [
                    {
                        "id": comment.id,
                        "body": comment.body,
                        "user": {
                            "id": comment.user.id,
                            "name": comment.user.name
                        } if comment.user else None,
                        "created_at": comment.created_at.isoformat() if comment.created_at else None
                    }
                    for comment in comments
                ]
            }
        except Exception as e:
            logger.error(f"Error getting issue details for {issue_id}: {e}")
            raise HTTPException(status_code=404, detail=f"Issue not found: {str(e)}")
    
    # Dashboard Analytics
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get comprehensive dashboard overview"""
        try:
            teams = await self.get_teams()
            projects = await self.get_projects()
            recent_issues = self._get_cache("recent_issues") or await self.get_issues(limit=100)
            
            # Calculate overall metrics
            total_active_issues = sum(team["active_issues"] for team in teams)
            total_completed_issues = sum(team["completed_issues"] for team in teams)
            
            # Project health distribution
            health_distribution = {}
            for project in projects:
                health = project["health_status"]
                health_distribution[health] = health_distribution.get(health, 0) + 1
            
            # Recent activity
            now = datetime.now()
            week_ago = now - timedelta(days=7)
            recent_activity = [
                issue for issue in recent_issues
                if issue.get("updated_at") and 
                datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00")) >= week_ago
            ]
            
            return {
                "overview": {
                    "total_teams": len(teams),
                    "total_projects": len(projects),
                    "total_active_issues": total_active_issues,
                    "total_completed_issues": total_completed_issues,
                    "recent_activity_count": len(recent_activity)
                },
                "teams": teams,
                "projects": projects[:10],  # Top 10 projects
                "project_health_distribution": health_distribution,
                "recent_activity": recent_activity[:20],  # Last 20 activities
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")
    
    # Webhook Processing
    async def process_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """Process Linear webhook events"""
        try:
            event = await self.webhook_processor.process_webhook(payload, signature)
            
            # Invalidate relevant caches based on event type
            if event.type in ["Issue", "IssueUpdate"]:
                self._invalidate_caches(["recent_issues"])
            elif event.type in ["Project", "ProjectUpdate"]:
                self._invalidate_caches(["projects_all"])
            
            # Process event through event manager
            await self.event_manager.handle_event(event)
            
            return {
                "status": "processed",
                "event_type": event.type,
                "event_id": event.id,
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to process webhook: {str(e)}")
    
    # Utility Methods
    def _invalidate_caches(self, cache_keys: List[str]):
        """Invalidate specific cache entries"""
        for key in cache_keys:
            if key in self._cache:
                del self._cache[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of Linear integration"""
        try:
            # Test API connectivity
            viewer = await self.client.get_viewer()
            
            return {
                "status": "healthy",
                "api_connected": True,
                "user": {
                    "id": viewer.id,
                    "name": viewer.name,
                    "email": viewer.email
                } if viewer else None,
                "cache_entries": len(self._cache),
                "last_sync": max(self._cache_timestamps.values()) if self._cache_timestamps else None,
                "checked_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Linear health check failed: {e}")
            return {
                "status": "unhealthy",
                "api_connected": False,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }

# Global Linear Dashboard Manager instance
linear_dashboard_manager: Optional[LinearDashboardManager] = None

def get_linear_dashboard_manager() -> LinearDashboardManager:
    """Get the global Linear dashboard manager instance"""
    global linear_dashboard_manager
    if not linear_dashboard_manager:
        raise HTTPException(status_code=503, detail="Linear integration not configured")
    return linear_dashboard_manager

def initialize_linear_dashboard(api_key: str, webhook_secret: Optional[str] = None) -> LinearDashboardManager:
    """Initialize the Linear dashboard manager"""
    global linear_dashboard_manager
    config = LinearDashboardConfig(api_key=api_key, webhook_secret=webhook_secret)
    linear_dashboard_manager = LinearDashboardManager(config)
    return linear_dashboard_manager

# FastAPI Router for Linear endpoints
def create_linear_router() -> APIRouter:
    """Create FastAPI router for Linear endpoints"""
    router = APIRouter(prefix="/api/linear", tags=["linear"])
    
    @router.get("/health")
    async def linear_health():
        """Get Linear integration health status"""
        manager = get_linear_dashboard_manager()
        return await manager.get_health_status()
    
    @router.get("/overview")
    async def linear_overview():
        """Get Linear dashboard overview"""
        manager = get_linear_dashboard_manager()
        return await manager.get_dashboard_overview()
    
    @router.get("/teams")
    async def get_teams():
        """Get all teams"""
        manager = get_linear_dashboard_manager()
        return await manager.get_teams()
    
    @router.get("/projects")
    async def get_projects(team_id: Optional[str] = None):
        """Get projects, optionally filtered by team"""
        manager = get_linear_dashboard_manager()
        return await manager.get_projects(team_id=team_id)
    
    @router.get("/issues")
    async def get_issues(
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50
    ):
        """Get issues with filtering"""
        manager = get_linear_dashboard_manager()
        return await manager.get_issues(
            team_id=team_id,
            project_id=project_id,
            assignee_id=assignee_id,
            state=state,
            limit=limit
        )
    
    @router.get("/issues/{issue_id}")
    async def get_issue_details(issue_id: str):
        """Get detailed information about a specific issue"""
        manager = get_linear_dashboard_manager()
        return await manager.get_issue_details(issue_id)
    
    @router.post("/issues")
    async def create_issue(issue_data: LinearIssueCreate):
        """Create a new Linear issue"""
        manager = get_linear_dashboard_manager()
        return await manager.create_issue(issue_data)
    
    @router.put("/issues/{issue_id}")
    async def update_issue(issue_id: str, issue_data: LinearIssueUpdate):
        """Update an existing Linear issue"""
        manager = get_linear_dashboard_manager()
        return await manager.update_issue(issue_id, issue_data)
    
    @router.post("/webhook")
    async def linear_webhook(payload: Dict[str, Any], signature: str = None):
        """Process Linear webhook events"""
        manager = get_linear_dashboard_manager()
        return await manager.process_webhook(payload, signature or "")
    
    return router

