"""
Prefect Orchestrator Client

This module provides a high-level client for managing Prefect workflows
and autonomous CI/CD operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from prefect import get_client
from prefect.client.schemas import FlowRun, TaskRun
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

from .config import get_config, get_workflow_configs, WorkflowConfig
from .workflows import (
    autonomous_maintenance_flow,
    failure_analysis_flow,
    dependency_update_flow,
    performance_optimization_flow,
)
from .notifications import notify_workflow_started, notify_workflow_failed


class PrefectOrchestrator:
    """
    High-level orchestrator for autonomous CI/CD workflows using Prefect.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize the Prefect orchestrator.
        
        Args:
            config: Optional configuration object
        """
        self.config = config or get_config()
        self.client = None
        self.deployments = {}
        self.active_runs = {}
        
    async def initialize(self) -> None:
        """Initialize the Prefect client and deployments"""
        try:
            self.client = get_client()
            await self._setup_deployments()
            logging.info("Prefect orchestrator initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Prefect orchestrator: {str(e)}")
            raise
    
    async def _setup_deployments(self) -> None:
        """Set up Prefect deployments for all workflows"""
        workflow_configs = get_workflow_configs()
        
        # Autonomous Maintenance Deployment
        maintenance_config = workflow_configs["autonomous_maintenance"]
        self.deployments["autonomous_maintenance"] = await Deployment.build_from_flow(
            flow=autonomous_maintenance_flow,
            name="autonomous-maintenance",
            description=maintenance_config.description,
            tags=maintenance_config.tags,
            schedule=CronSchedule(cron=maintenance_config.schedule) if maintenance_config.schedule else None,
            parameters=maintenance_config.parameters,
        )
        
        # Failure Analysis Deployment
        failure_config = workflow_configs["failure_analysis"]
        self.deployments["failure_analysis"] = await Deployment.build_from_flow(
            flow=failure_analysis_flow,
            name="failure-analysis",
            description=failure_config.description,
            tags=failure_config.tags,
            parameters=failure_config.parameters,
        )
        
        # Dependency Update Deployment
        dependency_config = workflow_configs["dependency_update"]
        self.deployments["dependency_update"] = await Deployment.build_from_flow(
            flow=dependency_update_flow,
            name="dependency-update",
            description=dependency_config.description,
            tags=dependency_config.tags,
            schedule=CronSchedule(cron=dependency_config.schedule) if dependency_config.schedule else None,
            parameters=dependency_config.parameters,
        )
        
        # Performance Optimization Deployment
        performance_config = workflow_configs["performance_optimization"]
        self.deployments["performance_optimization"] = await Deployment.build_from_flow(
            flow=performance_optimization_flow,
            name="performance-optimization",
            description=performance_config.description,
            tags=performance_config.tags,
            schedule=CronSchedule(cron=performance_config.schedule) if performance_config.schedule else None,
            parameters=performance_config.parameters,
        )
        
        logging.info(f"Set up {len(self.deployments)} Prefect deployments")
    
    async def run_autonomous_maintenance(
        self,
        repo_url: str,
        branch: str = "main",
        **kwargs
    ) -> str:
        """
        Run autonomous maintenance workflow.
        
        Args:
            repo_url: Repository URL to maintain
            branch: Branch to analyze and maintain
            **kwargs: Additional parameters for the workflow
        
        Returns:
            Flow run ID
        """
        parameters = {
            "repo_url": repo_url,
            "branch": branch,
            **kwargs
        }
        
        return await self._run_workflow("autonomous_maintenance", parameters)
    
    async def run_failure_analysis(
        self,
        repo_url: str,
        workflow_run_id: str,
        failure_logs: str,
        **kwargs
    ) -> str:
        """
        Run failure analysis workflow.
        
        Args:
            repo_url: Repository URL where failure occurred
            workflow_run_id: GitHub workflow run ID
            failure_logs: Failure logs to analyze
            **kwargs: Additional parameters for the workflow
        
        Returns:
            Flow run ID
        """
        parameters = {
            "repo_url": repo_url,
            "workflow_run_id": workflow_run_id,
            "failure_logs": failure_logs,
            **kwargs
        }
        
        return await self._run_workflow("failure_analysis", parameters)
    
    async def run_dependency_update(
        self,
        repo_url: str,
        update_strategy: str = "smart",
        **kwargs
    ) -> str:
        """
        Run dependency update workflow.
        
        Args:
            repo_url: Repository URL to update
            update_strategy: Update strategy (smart, security-only, all)
            **kwargs: Additional parameters for the workflow
        
        Returns:
            Flow run ID
        """
        parameters = {
            "repo_url": repo_url,
            "update_strategy": update_strategy,
            **kwargs
        }
        
        return await self._run_workflow("dependency_update", parameters)
    
    async def run_performance_optimization(
        self,
        repo_url: str,
        baseline_branch: str = "main",
        **kwargs
    ) -> str:
        """
        Run performance optimization workflow.
        
        Args:
            repo_url: Repository URL to monitor
            baseline_branch: Baseline branch for comparison
            **kwargs: Additional parameters for the workflow
        
        Returns:
            Flow run ID
        """
        parameters = {
            "repo_url": repo_url,
            "baseline_branch": baseline_branch,
            **kwargs
        }
        
        return await self._run_workflow("performance_optimization", parameters)
    
    async def _run_workflow(
        self,
        workflow_name: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Run a specific workflow with parameters.
        
        Args:
            workflow_name: Name of the workflow to run
            parameters: Parameters for the workflow
        
        Returns:
            Flow run ID
        """
        if not self.client:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")
        
        if workflow_name not in self.deployments:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        try:
            # Generate unique run ID
            run_id = str(uuid4())
            
            # Start the workflow
            deployment = self.deployments[workflow_name]
            flow_run = await self.client.create_flow_run_from_deployment(
                deployment.id,
                parameters=parameters,
                name=f"{workflow_name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                tags=[f"autonomous", f"repo:{parameters.get('repo_url', 'unknown')}"]
            )
            
            # Track the run
            self.active_runs[run_id] = {
                "flow_run_id": flow_run.id,
                "workflow_name": workflow_name,
                "parameters": parameters,
                "started_at": datetime.utcnow(),
                "status": "running"
            }
            
            # Send start notification
            await notify_workflow_started(
                parameters.get("repo_url", "unknown"),
                workflow_name
            )
            
            logging.info(f"Started {workflow_name} workflow with run ID: {run_id}")
            return run_id
            
        except Exception as e:
            logging.error(f"Failed to start {workflow_name} workflow: {str(e)}")
            
            # Send failure notification
            await notify_workflow_failed(
                parameters.get("repo_url", "unknown"),
                workflow_name,
                str(e)
            )
            
            raise
    
    async def get_workflow_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the status of a workflow run.
        
        Args:
            run_id: Run ID returned from workflow execution
        
        Returns:
            Dictionary containing workflow status and results
        """
        if run_id not in self.active_runs:
            raise ValueError(f"Unknown run ID: {run_id}")
        
        run_info = self.active_runs[run_id]
        
        try:
            # Get flow run from Prefect
            flow_run = await self.client.read_flow_run(run_info["flow_run_id"])
            
            # Update local status
            run_info["status"] = flow_run.state.type.value if flow_run.state else "unknown"
            run_info["updated_at"] = datetime.utcnow()
            
            if flow_run.state and flow_run.state.is_final():
                run_info["completed_at"] = datetime.utcnow()
                run_info["result"] = flow_run.state.result() if hasattr(flow_run.state, 'result') else None
            
            return {
                "run_id": run_id,
                "workflow_name": run_info["workflow_name"],
                "status": run_info["status"],
                "started_at": run_info["started_at"].isoformat(),
                "updated_at": run_info["updated_at"].isoformat(),
                "completed_at": run_info.get("completed_at", {}).isoformat() if run_info.get("completed_at") else None,
                "parameters": run_info["parameters"],
                "result": run_info.get("result"),
                "flow_run_id": run_info["flow_run_id"]
            }
            
        except Exception as e:
            logging.error(f"Failed to get workflow status for {run_id}: {str(e)}")
            raise
    
    async def cancel_workflow(self, run_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            run_id: Run ID of the workflow to cancel
        
        Returns:
            True if cancellation was successful
        """
        if run_id not in self.active_runs:
            raise ValueError(f"Unknown run ID: {run_id}")
        
        run_info = self.active_runs[run_id]
        
        try:
            # Cancel the flow run
            await self.client.set_flow_run_state(
                run_info["flow_run_id"],
                state={"type": "CANCELLED", "message": "Cancelled by user"}
            )
            
            # Update local status
            run_info["status"] = "cancelled"
            run_info["completed_at"] = datetime.utcnow()
            
            logging.info(f"Cancelled workflow {run_info['workflow_name']} with run ID: {run_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to cancel workflow {run_id}: {str(e)}")
            return False
    
    async def list_active_workflows(self) -> List[Dict[str, Any]]:
        """
        List all active workflows.
        
        Returns:
            List of active workflow information
        """
        active_workflows = []
        
        for run_id, run_info in self.active_runs.items():
            if run_info["status"] in ["running", "pending", "scheduled"]:
                try:
                    status = await self.get_workflow_status(run_id)
                    active_workflows.append(status)
                except Exception as e:
                    logging.error(f"Failed to get status for run {run_id}: {str(e)}")
        
        return active_workflows
    
    async def get_workflow_history(
        self,
        workflow_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get workflow execution history.
        
        Args:
            workflow_name: Optional workflow name to filter by
            limit: Maximum number of results to return
        
        Returns:
            List of workflow execution history
        """
        try:
            # Get flow runs from Prefect
            flow_runs = await self.client.read_flow_runs(
                limit=limit,
                sort="CREATED_DESC"
            )
            
            history = []
            for flow_run in flow_runs:
                # Filter by workflow name if specified
                if workflow_name and workflow_name not in flow_run.name:
                    continue
                
                history.append({
                    "flow_run_id": str(flow_run.id),
                    "name": flow_run.name,
                    "status": flow_run.state.type.value if flow_run.state else "unknown",
                    "created_at": flow_run.created.isoformat() if flow_run.created else None,
                    "start_time": flow_run.start_time.isoformat() if flow_run.start_time else None,
                    "end_time": flow_run.end_time.isoformat() if flow_run.end_time else None,
                    "total_run_time": str(flow_run.total_run_time) if flow_run.total_run_time else None,
                    "parameters": flow_run.parameters or {},
                    "tags": flow_run.tags or []
                })
            
            return history
            
        except Exception as e:
            logging.error(f"Failed to get workflow history: {str(e)}")
            raise
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics for autonomous CI/CD operations.
        
        Returns:
            Dictionary containing system metrics
        """
        try:
            # Get recent flow runs for metrics
            recent_runs = await self.client.read_flow_runs(
                limit=100,
                sort="CREATED_DESC"
            )
            
            # Calculate metrics
            total_runs = len(recent_runs)
            successful_runs = len([r for r in recent_runs if r.state and r.state.is_completed()])
            failed_runs = len([r for r in recent_runs if r.state and r.state.is_failed()])
            
            # Calculate average runtime for completed runs
            completed_runs = [r for r in recent_runs if r.total_run_time]
            avg_runtime = sum(r.total_run_time.total_seconds() for r in completed_runs) / len(completed_runs) if completed_runs else 0
            
            # Get active runs count
            active_runs = len([r for r in recent_runs if r.state and r.state.is_running()])
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
                "active_runs": active_runs,
                "average_runtime_seconds": avg_runtime,
                "deployments_count": len(self.deployments),
                "tracked_runs": len(self.active_runs)
            }
            
        except Exception as e:
            logging.error(f"Failed to get system metrics: {str(e)}")
            raise
    
    async def cleanup_completed_runs(self, older_than_days: int = 7) -> int:
        """
        Clean up completed workflow runs older than specified days.
        
        Args:
            older_than_days: Remove runs older than this many days
        
        Returns:
            Number of runs cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        cleaned_count = 0
        
        # Clean up local tracking
        runs_to_remove = []
        for run_id, run_info in self.active_runs.items():
            if (run_info.get("completed_at") and 
                run_info["completed_at"] < cutoff_date and
                run_info["status"] in ["completed", "failed", "cancelled"]):
                runs_to_remove.append(run_id)
        
        for run_id in runs_to_remove:
            del self.active_runs[run_id]
            cleaned_count += 1
        
        logging.info(f"Cleaned up {cleaned_count} completed workflow runs")
        return cleaned_count
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator and clean up resources"""
        try:
            # Cancel any running workflows
            for run_id, run_info in self.active_runs.items():
                if run_info["status"] == "running":
                    await self.cancel_workflow(run_id)
            
            # Close Prefect client
            if self.client:
                await self.client.close()
            
            logging.info("Prefect orchestrator shutdown completed")
            
        except Exception as e:
            logging.error(f"Error during orchestrator shutdown: {str(e)}")


# Convenience functions for common operations

async def create_orchestrator() -> PrefectOrchestrator:
    """Create and initialize a Prefect orchestrator"""
    orchestrator = PrefectOrchestrator()
    await orchestrator.initialize()
    return orchestrator


async def run_maintenance_for_repo(repo_url: str, branch: str = "main") -> str:
    """Run autonomous maintenance for a specific repository"""
    orchestrator = await create_orchestrator()
    try:
        return await orchestrator.run_autonomous_maintenance(repo_url, branch)
    finally:
        await orchestrator.shutdown()


async def analyze_failure(repo_url: str, workflow_run_id: str, failure_logs: str) -> str:
    """Analyze a CI/CD failure"""
    orchestrator = await create_orchestrator()
    try:
        return await orchestrator.run_failure_analysis(repo_url, workflow_run_id, failure_logs)
    finally:
        await orchestrator.shutdown()

