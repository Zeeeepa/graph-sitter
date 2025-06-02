"""
Orchestrator Integration for Advanced Dashboard

This module integrates the Contexten Orchestrator with the dashboard,
providing enhanced task management, self-healing capabilities, and
comprehensive monitoring through the contexten_app.py system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..extensions.contexten_app import (
    ContextenOrchestrator, 
    ContextenConfig, 
    TaskRequest, 
    TaskResult,
    HealthMonitor
)
from .advanced_analytics import AdvancedAnalyticsEngine, AnalyticsReport
from .chat_manager import ChatManager
from ...shared.logging.get_logger import get_logger

logger = get_logger(__name__)

@dataclass
class DashboardTask:
    """Enhanced task for dashboard operations"""
    id: str
    type: str
    description: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = None

class OrchestratorDashboardIntegration:
    """Integration layer between Contexten Orchestrator and Dashboard"""
    
    def __init__(self, config: ContextenConfig):
        self.config = config
        self.orchestrator = ContextenOrchestrator(config)
        self.analytics_engine = AdvancedAnalyticsEngine()
        self.chat_manager = ChatManager()
        
        # Dashboard-specific state
        self.dashboard_tasks: Dict[str, DashboardTask] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.system_metrics: Dict[str, Any] = {}
        self.real_time_events: List[Dict[str, Any]] = []
        
        # Background monitoring
        self.monitoring_tasks: List[asyncio.Task] = []
        self.is_running = False
    
    async def start(self):
        """Start the integrated orchestrator and dashboard services"""
        
        logger.info("Starting Orchestrator Dashboard Integration...")
        
        try:
            # Start the core orchestrator
            await self.orchestrator.start()
            
            # Start dashboard-specific monitoring
            self.is_running = True
            self.monitoring_tasks = [
                asyncio.create_task(self._monitor_system_health()),
                asyncio.create_task(self._monitor_task_progress()),
                asyncio.create_task(self._monitor_real_time_events()),
                asyncio.create_task(self._update_analytics())
            ]
            
            logger.info("Orchestrator Dashboard Integration started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start integration: {e}")
            raise
    
    async def stop(self):
        """Stop the integration services"""
        
        logger.info("Stopping Orchestrator Dashboard Integration...")
        
        self.is_running = False
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        # Stop the orchestrator
        await self.orchestrator.stop()
        
        logger.info("Orchestrator Dashboard Integration stopped")
    
    async def execute_dashboard_task(
        self, 
        task_type: str, 
        task_data: Dict[str, Any],
        description: str = "",
        priority: int = 3
    ) -> DashboardTask:
        """Execute a task through the orchestrator with dashboard tracking"""
        
        task_id = f"dash_{int(datetime.now().timestamp() * 1000)}"
        
        # Create dashboard task
        dashboard_task = DashboardTask(
            id=task_id,
            type=task_type,
            description=description or f"Execute {task_type}",
            status="running",
            created_at=datetime.now(),
            metadata={"priority": priority}
        )
        
        self.dashboard_tasks[task_id] = dashboard_task
        
        try:
            # Execute through orchestrator
            orchestrator_request = TaskRequest(
                task_type=task_type,
                task_data=task_data,
                priority=priority
            )
            
            result = await self.orchestrator.execute_task(
                orchestrator_request.task_type,
                orchestrator_request.task_data,
                priority=orchestrator_request.priority
            )
            
            # Update dashboard task
            dashboard_task.status = result.status
            dashboard_task.completed_at = datetime.now()
            dashboard_task.result = result.result
            dashboard_task.error = result.error
            dashboard_task.progress = 100.0 if result.status == "completed" else 0.0
            
            # Add to real-time events
            self._add_real_time_event({
                "type": "task_completed",
                "task_id": task_id,
                "task_type": task_type,
                "status": result.status,
                "timestamp": datetime.now().isoformat()
            })
            
            return dashboard_task
            
        except Exception as e:
            dashboard_task.status = "failed"
            dashboard_task.error = str(e)
            dashboard_task.completed_at = datetime.now()
            
            logger.error(f"Dashboard task {task_id} failed: {e}")
            return dashboard_task
    
    async def create_comprehensive_analysis(self, project_id: str, codebase_path: str) -> Dict[str, Any]:
        """Create comprehensive project analysis using orchestrator capabilities"""
        
        analysis_tasks = []
        
        try:
            # 1. Codebase Analysis
            codebase_task = await self.execute_dashboard_task(
                "core.analyze_codebase",
                {"codebase_path": codebase_path},
                "Analyzing codebase structure and metrics"
            )
            analysis_tasks.append(codebase_task)
            
            # 2. Advanced Analytics
            analytics_task = await self.execute_dashboard_task(
                "analytics.comprehensive_analysis",
                {"project_id": project_id, "codebase_path": codebase_path},
                "Running advanced code analytics"
            )
            analysis_tasks.append(analytics_task)
            
            # 3. Security Analysis
            security_task = await self.execute_dashboard_task(
                "security.vulnerability_scan",
                {"codebase_path": codebase_path},
                "Scanning for security vulnerabilities"
            )
            analysis_tasks.append(security_task)
            
            # 4. Performance Analysis
            performance_task = await self.execute_dashboard_task(
                "performance.bottleneck_analysis",
                {"codebase_path": codebase_path},
                "Analyzing performance bottlenecks"
            )
            analysis_tasks.append(performance_task)
            
            # 5. Technical Debt Assessment
            debt_task = await self.execute_dashboard_task(
                "debt.assessment",
                {"codebase_path": codebase_path},
                "Assessing technical debt"
            )
            analysis_tasks.append(debt_task)
            
            # Compile comprehensive report
            report = {
                "project_id": project_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "tasks": [
                    {
                        "id": task.id,
                        "type": task.type,
                        "status": task.status,
                        "result": task.result,
                        "error": task.error
                    } for task in analysis_tasks
                ],
                "summary": await self._generate_analysis_summary(analysis_tasks),
                "recommendations": await self._generate_recommendations(analysis_tasks),
                "health_score": await self._calculate_project_health(analysis_tasks),
                "risk_assessment": await self._assess_project_risks(analysis_tasks)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to create comprehensive analysis: {e}")
            return {"error": str(e), "tasks": analysis_tasks}
    
    async def create_automated_workflow(
        self, 
        workflow_type: str, 
        project_id: str, 
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create automated workflow using orchestrator and chat manager"""
        
        workflow_id = f"workflow_{int(datetime.now().timestamp() * 1000)}"
        
        try:
            # 1. Generate implementation plan using chat manager
            plan_result = await self.chat_manager.process_chat_message(
                message=f"Create a detailed implementation plan for: {requirements.get('description', '')}",
                project_id=project_id
            )
            
            # 2. Create Linear issues through orchestrator
            linear_task = await self.execute_dashboard_task(
                "linear.create_implementation_issues",
                {
                    "project_id": project_id,
                    "plan": plan_result.get("plan"),
                    "requirements": requirements
                },
                "Creating Linear implementation issues"
            )
            
            # 3. Set up GitHub workflows
            github_task = await self.execute_dashboard_task(
                "github.setup_workflows",
                {
                    "project_id": project_id,
                    "workflow_type": workflow_type,
                    "requirements": requirements
                },
                "Setting up GitHub workflows"
            )
            
            # 4. Configure monitoring agents
            monitoring_task = await self.execute_dashboard_task(
                "monitoring.setup_agents",
                {
                    "project_id": project_id,
                    "workflow_id": workflow_id,
                    "monitoring_config": requirements.get("monitoring", {})
                },
                "Setting up monitoring agents"
            )
            
            # 5. Initialize autogenlib for code generation
            autogen_task = await self.execute_dashboard_task(
                "autogenlib.initialize_project",
                {
                    "project_id": project_id,
                    "codebase_path": requirements.get("codebase_path"),
                    "generation_config": requirements.get("autogen_config", {})
                },
                "Initializing automated code generation"
            )
            
            # Store workflow
            workflow = {
                "id": workflow_id,
                "type": workflow_type,
                "project_id": project_id,
                "requirements": requirements,
                "plan": plan_result,
                "tasks": [linear_task.id, github_task.id, monitoring_task.id, autogen_task.id],
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "progress": 0.0
            }
            
            self.active_workflows[workflow_id] = workflow
            
            return {
                "workflow_id": workflow_id,
                "status": "created",
                "plan": plan_result,
                "tasks": {
                    "linear": linear_task.id,
                    "github": github_task.id,
                    "monitoring": monitoring_task.id,
                    "autogen": autogen_task.id
                },
                "next_steps": [
                    "Monitor Linear issues for progress updates",
                    "Track GitHub workflow executions",
                    "Review automated code generation results",
                    "Validate implementation against requirements"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to create automated workflow: {e}")
            return {"error": str(e), "workflow_id": workflow_id}
    
    async def get_system_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        
        try:
            # Get orchestrator metrics
            orchestrator_metrics = await self.orchestrator.get_system_metrics()
            
            # Get health status
            health_status = await self.orchestrator.health_monitor.check_health()
            
            # Get analytics summary
            analytics_data = {}
            for project_id in self.analytics_engine.analysis_cache.keys():
                analytics_data[project_id] = await self.analytics_engine.get_analytics_summary(project_id)
            
            # Compile dashboard data
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "system_health": health_status,
                "orchestrator_metrics": orchestrator_metrics,
                "analytics": analytics_data,
                "active_tasks": len([t for t in self.dashboard_tasks.values() if t.status == "running"]),
                "completed_tasks": len([t for t in self.dashboard_tasks.values() if t.status == "completed"]),
                "failed_tasks": len([t for t in self.dashboard_tasks.values() if t.status == "failed"]),
                "active_workflows": len(self.active_workflows),
                "recent_events": self.real_time_events[-10:],  # Last 10 events
                "performance_metrics": {
                    "avg_task_duration": self._calculate_avg_task_duration(),
                    "success_rate": self._calculate_success_rate(),
                    "system_load": orchestrator_metrics.get("active_tasks", 0)
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}
    
    async def _monitor_system_health(self):
        """Background task to monitor system health"""
        
        while self.is_running:
            try:
                # Update system metrics every 30 seconds
                self.system_metrics = await self.orchestrator.get_system_metrics()
                
                # Check for system issues
                health_status = await self.orchestrator.health_monitor.check_health()
                if health_status.get("overall_status") != "healthy":
                    self._add_real_time_event({
                        "type": "system_health_warning",
                        "status": health_status.get("overall_status"),
                        "components": health_status.get("components", {}),
                        "timestamp": datetime.now().isoformat()
                    })
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_task_progress(self):
        """Background task to monitor task progress"""
        
        while self.is_running:
            try:
                # Update task progress every 10 seconds
                for task_id, task in self.dashboard_tasks.items():
                    if task.status == "running":
                        # Check if task is still active in orchestrator
                        if task_id not in self.orchestrator.active_tasks:
                            # Task might have completed, check results
                            if task_id in self.orchestrator.task_results:
                                result = self.orchestrator.task_results[task_id]
                                task.status = result.status
                                task.result = result.result
                                task.error = result.error
                                task.completed_at = datetime.now()
                                task.progress = 100.0 if result.status == "completed" else 0.0
                
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task monitoring: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_real_time_events(self):
        """Background task to monitor real-time events"""
        
        while self.is_running:
            try:
                # Clean up old events (keep last 100)
                if len(self.real_time_events) > 100:
                    self.real_time_events = self.real_time_events[-100:]
                
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _update_analytics(self):
        """Background task to update analytics"""
        
        while self.is_running:
            try:
                # Update analytics every 5 minutes
                for project_id in list(self.analytics_engine.analysis_cache.keys()):
                    # Refresh analytics if data is older than 1 hour
                    report = self.analytics_engine.analysis_cache.get(project_id)
                    if report and (datetime.now() - report.timestamp).seconds > 3600:
                        # Trigger analytics refresh
                        self._add_real_time_event({
                            "type": "analytics_refresh",
                            "project_id": project_id,
                            "timestamp": datetime.now().isoformat()
                        })
                
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analytics update: {e}")
                await asyncio.sleep(600)
    
    def _add_real_time_event(self, event: Dict[str, Any]):
        """Add event to real-time feed"""
        
        event["id"] = f"event_{int(datetime.now().timestamp() * 1000)}"
        self.real_time_events.append(event)
    
    async def _generate_analysis_summary(self, tasks: List[DashboardTask]) -> Dict[str, Any]:
        """Generate summary from analysis tasks"""
        
        completed_tasks = [t for t in tasks if t.status == "completed"]
        failed_tasks = [t for t in tasks if t.status == "failed"]
        
        return {
            "total_tasks": len(tasks),
            "completed": len(completed_tasks),
            "failed": len(failed_tasks),
            "success_rate": len(completed_tasks) / len(tasks) if tasks else 0,
            "key_findings": [
                result.get("summary", "") for task in completed_tasks 
                if task.result and task.result.get("summary")
            ]
        }
    
    async def _generate_recommendations(self, tasks: List[DashboardTask]) -> List[str]:
        """Generate recommendations from analysis tasks"""
        
        recommendations = []
        
        for task in tasks:
            if task.status == "completed" and task.result:
                task_recommendations = task.result.get("recommendations", [])
                recommendations.extend(task_recommendations)
        
        # Remove duplicates and limit to top 10
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:10]
    
    async def _calculate_project_health(self, tasks: List[DashboardTask]) -> float:
        """Calculate overall project health score"""
        
        if not tasks:
            return 50.0
        
        completed_tasks = [t for t in tasks if t.status == "completed"]
        health_scores = []
        
        for task in completed_tasks:
            if task.result and "health_score" in task.result:
                health_scores.append(task.result["health_score"])
        
        return sum(health_scores) / len(health_scores) if health_scores else 50.0
    
    async def _assess_project_risks(self, tasks: List[DashboardTask]) -> Dict[str, Any]:
        """Assess project risks from analysis tasks"""
        
        risks = {
            "security": 0,
            "performance": 0,
            "maintainability": 0,
            "overall": 0
        }
        
        for task in tasks:
            if task.status == "completed" and task.result:
                if "security" in task.type:
                    risks["security"] = task.result.get("risk_score", 0)
                elif "performance" in task.type:
                    risks["performance"] = task.result.get("risk_score", 0)
                elif "debt" in task.type:
                    risks["maintainability"] = task.result.get("risk_score", 0)
        
        risks["overall"] = (risks["security"] + risks["performance"] + risks["maintainability"]) / 3
        
        return risks
    
    def _calculate_avg_task_duration(self) -> float:
        """Calculate average task duration"""
        
        completed_tasks = [
            t for t in self.dashboard_tasks.values() 
            if t.status == "completed" and t.completed_at
        ]
        
        if not completed_tasks:
            return 0.0
        
        durations = [
            (t.completed_at - t.created_at).total_seconds() 
            for t in completed_tasks
        ]
        
        return sum(durations) / len(durations)
    
    def _calculate_success_rate(self) -> float:
        """Calculate task success rate"""
        
        if not self.dashboard_tasks:
            return 100.0
        
        completed_tasks = len([t for t in self.dashboard_tasks.values() if t.status == "completed"])
        total_tasks = len([t for t in self.dashboard_tasks.values() if t.status in ["completed", "failed"]])
        
        return (completed_tasks / total_tasks * 100) if total_tasks > 0 else 100.0

