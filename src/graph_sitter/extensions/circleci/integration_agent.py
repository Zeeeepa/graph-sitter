"""
CircleCI integration agent
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from .config import CircleCIIntegrationConfig
from .types import (
    CircleCIEventType,
    BuildStatus,
    CircleCIEvent,
    WorkflowEvent,
    JobEvent,
    FailureAnalysis,
    FailureType,
    FixConfidence
)
from .webhook_processor import WebhookProcessor, WebhookResult


@dataclass
class IntegrationStatus:
    """Integration status"""
    healthy: bool
    api_healthy: bool
    webhook_healthy: bool
    uptime: timedelta
    active_tasks: int
    queue_size: int


@dataclass
class IntegrationMetrics:
    """Integration metrics"""
    builds_monitored: int = 0
    builds_failed: int = 0
    builds_fixed: int = 0
    webhook_stats: Dict[str, int] = field(default_factory=dict)
    analysis_stats: Dict[str, int] = field(default_factory=dict)
    uptime_duration: timedelta = field(default_factory=lambda: timedelta())


class CircleCIIntegrationAgent:
    """CircleCI integration agent"""

    def __init__(self, config: CircleCIIntegrationConfig):
        """Initialize agent"""
        self.config = config
        self.webhook_processor = WebhookProcessor(config)
        self._logger = logging.getLogger(__name__)
        self._start_time = None
        self._is_running = False
        self._active_tasks = {}
        self._metrics = IntegrationMetrics()

    @property
    def is_running(self) -> bool:
        """Check if agent is running"""
        return self._is_running

    async def start(self):
        """Start the agent"""
        if self._is_running:
            return

        self._start_time = datetime.now()
        self._is_running = True

        # Start webhook processor
        await self.webhook_processor.start()

        # Register handlers
        self.webhook_processor.register_handler(
            self._handle_workflow_completed,
            name="workflow-handler",
            event_type=CircleCIEventType.WORKFLOW_COMPLETED,
            priority=10
        )
        self.webhook_processor.register_handler(
            self._handle_job_completed,
            name="job-handler",
            event_type=CircleCIEventType.JOB_COMPLETED,
            priority=5
        )

        self._logger.info("CircleCI integration agent started")

    async def stop(self):
        """Stop the agent"""
        if not self._is_running:
            return

        self._is_running = False

        # Stop webhook processor
        await self.webhook_processor.stop()

        # Cancel active tasks
        for task in self._active_tasks.values():
            task.cancel()
        self._active_tasks.clear()

        self._logger.info("CircleCI integration agent stopped")

    async def process_webhook(
        self,
        headers: Dict[str, str],
        body: str
    ) -> Dict[str, Any]:
        """Process incoming webhook"""
        if not self._is_running:
            return {
                "success": False,
                "error": "Agent not running"
            }

        result = await self.webhook_processor.process_webhook(headers, body)
        return {
            "success": result.success,
            "event_type": result.event_type.value if result.event_type else None,
            "event_id": result.event_id,
            "error": result.error,
            "processing_time": result.processing_time
        }

    async def _handle_workflow_completed(self, event: WorkflowEvent):
        """Handle workflow completed event"""
        self._metrics.builds_monitored += 1

        if event.status == BuildStatus.FAILED:
            self._metrics.builds_failed += 1

            if self.config.failure_analysis.enabled:
                task = asyncio.create_task(
                    self.analyze_build_failure(event.project_slug, event.workflow_id)
                )
                self._active_tasks[f"analysis-{event.workflow_id}"] = task

    async def _handle_job_completed(self, event: JobEvent):
        """Handle job completed event"""
        if event.status == BuildStatus.FAILED:
            if self.config.failure_analysis.enabled:
                task = asyncio.create_task(
                    self.analyze_build_failure(
                        event.project_slug,
                        None,
                        event.job_id
                    )
                )
                self._active_tasks[f"analysis-{event.job_id}"] = task

    async def analyze_build_failure(
        self,
        project_slug: str,
        workflow_id: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> FailureAnalysis:
        """Analyze build failure"""
        start_time = datetime.now()

        try:
            # Simulate analysis for now
            await asyncio.sleep(1.0)

            analysis = FailureAnalysis(
                project_slug=project_slug,
                workflow_id=workflow_id or "unknown",
                job_id=job_id,
                failure_type=FailureType.TEST_FAILURE,
                error_messages=["Test failure detected"],
                confidence=0.8,
                analysis_time=(datetime.now() - start_time).total_seconds()
            )

            self._metrics.analysis_stats["failures_analyzed"] = (
                self._metrics.analysis_stats.get("failures_analyzed", 0) + 1
            )

            return analysis

        except Exception as e:
            self._logger.error(f"Error analyzing build failure: {str(e)}")
            self._metrics.analysis_stats["analysis_errors"] = (
                self._metrics.analysis_stats.get("analysis_errors", 0) + 1
            )
            raise

    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get active tasks"""
        tasks = []
        for task_id, task in self._active_tasks.items():
            if not task.done():
                tasks.append({
                    "id": task_id,
                    "type": task_id.split("-")[0],
                    "status": "running"
                })
        return tasks

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False

    def get_metrics(self) -> IntegrationMetrics:
        """Get integration metrics"""
        if self._start_time:
            self._metrics.uptime_duration = datetime.now() - self._start_time

        # Add webhook stats
        webhook_stats = self.webhook_processor.get_stats()
        self._metrics.webhook_stats = {
            "workflow_events": webhook_stats.workflow_events,
            "job_events": webhook_stats.job_events,
            "events_processed": webhook_stats.events_processed,
            "events_failed": webhook_stats.events_failed
        }

        return self._metrics

    def get_integration_status(self) -> IntegrationStatus:
        """Get integration status"""
        webhook_info = self.webhook_processor.get_queue_info()
        uptime = (
            datetime.now() - self._start_time if self._start_time else timedelta()
        )

        return IntegrationStatus(
            healthy=self._is_running and webhook_info["is_running"],
            api_healthy=True,  # TODO: Implement API health check
            webhook_healthy=webhook_info["is_running"],
            uptime=uptime,
            active_tasks=len(self._active_tasks),
            queue_size=webhook_info["queue_size"]
        )

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        status = self.get_integration_status()
        metrics = self.get_metrics()

        return {
            "healthy": status.healthy,
            "uptime": str(status.uptime),
            "components": {
                "api": status.api_healthy,
                "webhook": status.webhook_healthy
            },
            "metrics": {
                "builds_monitored": metrics.builds_monitored,
                "builds_failed": metrics.builds_failed,
                "builds_fixed": metrics.builds_fixed
            }
        }

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

