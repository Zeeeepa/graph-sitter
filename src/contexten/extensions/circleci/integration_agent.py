"""
CircleCI Integration Agent

Main orchestrator that coordinates all CircleCI extension components:
- Webhook processing and event routing
- Failure analysis and fix generation
- Workflow automation and task management
- Integration with GitHub and Codegen SDK
- Health monitoring and metrics collection
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Awaitable
from pathlib import Path

from .config import CircleCIIntegrationConfig
from .client import CircleCIClient
from .webhook_processor import WebhookProcessor
from .failure_analyzer import FailureAnalyzer
from .workflow_automation import WorkflowAutomation
from .auto_fix_generator import AutoFixGenerator
from .types import (
    CircleCIEvent, CircleCIEventType, FailureAnalysis, GeneratedFix,
    CircleCIIntegrationMetrics, IntegrationStatus, BuildStatus
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class CircleCIIntegrationAgent:
    """
    Main integration agent that orchestrates all CircleCI extension functionality
    """
    
    def __init__(self, config: CircleCIIntegrationConfig):
        self.config = config
        
        # Core components
        self.client = CircleCIClient(
            api_token=config.api.api_token.get_secret_value(),
            api_base_url=config.api.api_base_url,
            request_timeout=config.api.request_timeout,
            max_retries=config.api.max_retries,
            retry_delay=config.api.retry_delay,
            rate_limit_requests_per_minute=config.api.rate_limit_requests_per_minute
        )
        
        self.webhook_processor = WebhookProcessor(config)
        self.failure_analyzer = FailureAnalyzer(config, self.client)
        self.workflow_automation = WorkflowAutomation(config)
        self.auto_fix_generator = AutoFixGenerator(config, self.client)
        
        # Integration state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Event handlers
        self._setup_event_handlers()
        
        # Health monitoring
        self.last_health_check: Optional[datetime] = None
        self.health_status = IntegrationStatus()
    
    @classmethod
    def from_env(cls) -> "CircleCIIntegrationAgent":
        """Create agent from environment variables"""
        config = CircleCIIntegrationConfig.from_env()
        return cls(config)
    
    @classmethod
    def from_file(cls, config_path: Path) -> "CircleCIIntegrationAgent":
        """Create agent from configuration file"""
        config = CircleCIIntegrationConfig.from_file(config_path)
        return cls(config)
    
    def _setup_event_handlers(self):
        """Setup event handlers for webhook processing"""
        
        # Register failure event handler
        self.webhook_processor.register_handler(
            handler=self._handle_failure_event,
            event_type=CircleCIEventType.WORKFLOW_COMPLETED,
            name="workflow_failure_handler",
            priority=100
        )
        
        self.webhook_processor.register_handler(
            handler=self._handle_failure_event,
            event_type=CircleCIEventType.JOB_COMPLETED,
            name="job_failure_handler",
            priority=100
        )
        
        # Register ping handler
        self.webhook_processor.register_handler(
            handler=self._handle_ping_event,
            event_type=CircleCIEventType.PING,
            name="ping_handler",
            priority=50
        )
        
        # Register workflow task handlers
        self.workflow_automation.register_task_handler(
            "failure_analysis",
            self._handle_failure_analysis_task
        )
        
        self.workflow_automation.register_task_handler(
            "fix_generation",
            self._handle_fix_generation_task
        )
        
        self.workflow_automation.register_task_handler(
            "fix_application",
            self._handle_fix_application_task
        )
        
        # Register progress callback
        self.workflow_automation.add_progress_callback(
            self._handle_task_progress
        )
    
    async def start(self):
        """Start the integration agent"""
        if self.is_running:
            logger.warning("Integration agent is already running")
            return
        
        logger.info("Starting CircleCI integration agent...")
        
        # Validate configuration
        config_issues = self.config.validate_configuration()
        if config_issues:
            logger.error(f"Configuration issues found: {config_issues}")
            if not self.config.debug_mode:
                raise ValueError(f"Configuration validation failed: {config_issues}")
        
        try:
            # Test API connectivity
            if not await self.client.health_check():
                logger.error("CircleCI API health check failed")
                if not self.config.debug_mode:
                    raise ConnectionError("Cannot connect to CircleCI API")
            
            # Start components
            await self.webhook_processor.start()
            await self.workflow_automation.start()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            # Start health monitoring
            if self.config.monitoring.enabled:
                asyncio.create_task(self._health_monitoring_loop())
            
            logger.info("CircleCI integration agent started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start integration agent: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the integration agent"""
        if not self.is_running:
            return
        
        logger.info("Stopping CircleCI integration agent...")
        
        self.is_running = False
        
        # Stop components
        await self.workflow_automation.stop()
        await self.webhook_processor.stop()
        await self.client.close()
        
        logger.info("CircleCI integration agent stopped")
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
    
    # Event Handlers
    async def _handle_failure_event(self, event: CircleCIEvent):
        """Handle failure events from CircleCI"""
        
        if not event.is_failure_event:
            logger.debug(f"Ignoring non-failure event: {event.id}")
            return
        
        logger.info(f"Processing failure event: {event.id} ({event.type.value})")
        
        try:
            # Create failure analysis task
            if self.config.failure_analysis.enabled:
                task = await self.workflow_automation.create_failure_analysis_task(event)
                logger.info(f"Created failure analysis task: {task.id}")
            
        except Exception as e:
            logger.error(f"Failed to handle failure event {event.id}: {e}")
    
    async def _handle_ping_event(self, event: CircleCIEvent):
        """Handle ping events from CircleCI"""
        logger.debug(f"Received ping event: {event.id}")
        # Ping events are used for webhook validation
        return {"status": "ok", "timestamp": datetime.now().isoformat()}
    
    async def _handle_failure_analysis_task(self, task):
        """Handle failure analysis workflow task"""
        logger.info(f"Executing failure analysis task: {task.id}")
        
        try:
            # Update progress
            await self.workflow_automation.update_task_progress(
                task.id, "Starting analysis", 0, 4
            )
            
            # Perform failure analysis
            analysis = await self.failure_analyzer.analyze_failure(task.event)
            task.failure_analysis = analysis
            
            await self.workflow_automation.update_task_progress(
                task.id, "Analysis completed", 1, 4
            )
            
            # Create fix generation task if auto-fix is enabled
            if self.config.auto_fix.enabled and analysis.confidence >= self.config.auto_fix.fix_confidence_threshold:
                
                await self.workflow_automation.update_task_progress(
                    task.id, "Creating fix generation task", 2, 4
                )
                
                fix_task = await self.workflow_automation.create_fix_generation_task(
                    analysis, parent_task_id=task.id
                )
                
                logger.info(f"Created fix generation task: {fix_task.id}")
            
            await self.workflow_automation.update_task_progress(
                task.id, "Task completed", 4, 4
            )
            
            return {
                "analysis_id": analysis.build_id,
                "failure_type": analysis.failure_type.value,
                "confidence": analysis.confidence,
                "suggestions_count": len(analysis.suggested_fixes)
            }
            
        except Exception as e:
            logger.error(f"Failure analysis task failed: {e}")
            raise
    
    async def _handle_fix_generation_task(self, task):
        """Handle fix generation workflow task"""
        logger.info(f"Executing fix generation task: {task.id}")
        
        if not task.failure_analysis:
            raise ValueError("No failure analysis available for fix generation")
        
        try:
            # Update progress
            await self.workflow_automation.update_task_progress(
                task.id, "Generating fix", 0, 3
            )
            
            # Generate fix
            fix = await self.auto_fix_generator.generate_fix(
                task.failure_analysis,
                repository_url=f"https://github.com/{task.event.project_slug}",
                branch=task.event.branch or "main",
                commit_sha=task.event.commit_sha or "HEAD"
            )
            task.generated_fix = fix
            
            await self.workflow_automation.update_task_progress(
                task.id, "Fix generated", 1, 3
            )
            
            # Create fix application task if auto-apply is enabled
            if (self.config.auto_fix.enabled and 
                not self.config.auto_fix.require_human_approval and
                fix.overall_confidence in ["high", "medium"]):
                
                await self.workflow_automation.update_task_progress(
                    task.id, "Creating application task", 2, 3
                )
                
                app_task = await self.workflow_automation.create_fix_application_task(
                    fix, parent_task_id=task.id
                )
                
                logger.info(f"Created fix application task: {app_task.id}")
            
            await self.workflow_automation.update_task_progress(
                task.id, "Task completed", 3, 3
            )
            
            return {
                "fix_id": fix.id,
                "confidence": fix.overall_confidence.value,
                "fixes_count": len(fix.code_fixes) + len(fix.config_fixes) + len(fix.dependency_fixes)
            }
            
        except Exception as e:
            logger.error(f"Fix generation task failed: {e}")
            raise
    
    async def _handle_fix_application_task(self, task):
        """Handle fix application workflow task"""
        logger.info(f"Executing fix application task: {task.id}")
        
        if not task.generated_fix:
            raise ValueError("No generated fix available for application")
        
        try:
            # Update progress
            await self.workflow_automation.update_task_progress(
                task.id, "Applying fix", 0, 2
            )
            
            # Apply fix
            result = await self.auto_fix_generator.apply_fix(task.generated_fix)
            
            await self.workflow_automation.update_task_progress(
                task.id, "Task completed", 2, 2
            )
            
            return {
                "success": result.get("success", False),
                "pr_url": result.get("pr_url"),
                "validation_results": result.get("validation_results", {})
            }
            
        except Exception as e:
            logger.error(f"Fix application task failed: {e}")
            raise
    
    async def _handle_task_progress(self, task):
        """Handle task progress updates"""
        if self.config.workflow.send_progress_notifications:
            logger.debug(f"Task {task.id} progress: {task.progress.percentage:.1f}% - {task.progress.current_step}")
        
        # Send notifications if configured
        if self.config.notifications.enabled:
            await self._send_progress_notification(task)
    
    async def _send_progress_notification(self, task):
        """Send progress notification"""
        # TODO: Implement notification sending (Slack, email, etc.)
        pass
    
    # Health Monitoring
    async def _health_monitoring_loop(self):
        """Health monitoring loop"""
        logger.info("Started health monitoring")
        
        while self.is_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.monitoring.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
        
        logger.info("Health monitoring stopped")
    
    async def _perform_health_check(self):
        """Perform comprehensive health check"""
        self.last_health_check = datetime.now()
        
        # Check API connectivity
        api_healthy = await self.client.health_check()
        
        # Check component health
        webhook_health = await self.webhook_processor.health_check()
        workflow_health = await self.workflow_automation.health_check()
        
        # Update health status
        self.health_status = IntegrationStatus(
            healthy=api_healthy and webhook_health["healthy"] and workflow_health["healthy"],
            last_check=self.last_health_check,
            webhook_healthy=webhook_health["healthy"],
            api_healthy=api_healthy,
            analysis_healthy=True,  # TODO: Add analyzer health check
            fix_generation_healthy=True,  # TODO: Add fix generator health check
            config_valid=len(self.config.validate_configuration()) == 0,
            credentials_valid=api_healthy,
            projects_monitored=len(await self._get_monitored_projects()),
            active_workflows=len(self.workflow_automation.get_active_tasks())
        )
        
        # Log health issues
        if not self.health_status.healthy:
            issues = []
            if not api_healthy:
                issues.append("API connectivity")
            if not webhook_health["healthy"]:
                issues.append("Webhook processing")
            if not workflow_health["healthy"]:
                issues.append("Workflow automation")
            
            logger.warning(f"Health check failed: {', '.join(issues)}")
    
    async def _get_monitored_projects(self) -> List[str]:
        """Get list of monitored projects"""
        try:
            if self.config.monitor_all_projects:
                projects = await self.client.get_projects()
                return [p.slug for p in projects]
            else:
                return self.config.monitored_projects
        except Exception as e:
            logger.error(f"Failed to get monitored projects: {e}")
            return []
    
    # Public API
    async def process_webhook(self, headers: Dict[str, str], body: str) -> Dict[str, Any]:
        """Process incoming webhook"""
        result = await self.webhook_processor.process_webhook(headers, body)
        
        return {
            "success": result.success,
            "event_id": result.event_id,
            "event_type": result.event_type.value if result.event_type else None,
            "processing_time": result.processing_time,
            "error": result.error
        }
    
    async def analyze_build_failure(self, project_slug: str, build_number: int) -> FailureAnalysis:
        """Analyze a specific build failure"""
        return await self.failure_analyzer.analyze_build_failure(project_slug, build_number)
    
    async def generate_fix_for_analysis(self, analysis: FailureAnalysis) -> GeneratedFix:
        """Generate fix for a failure analysis"""
        return await self.auto_fix_generator.generate_fix(
            analysis,
            repository_url=f"https://github.com/{analysis.project_slug}",
            branch="main",
            commit_sha="HEAD"
        )
    
    def get_metrics(self) -> CircleCIIntegrationMetrics:
        """Get integration metrics"""
        webhook_stats = self.webhook_processor.get_stats()
        analysis_stats = self.failure_analyzer.get_stats()
        workflow_stats = self.workflow_automation.get_workflow_stats()
        
        # Create fix generation stats from workflow stats
        fix_stats = FixGenerationStats(
            requests_total=workflow_stats.tasks_created,
            requests_successful=workflow_stats.tasks_completed,
            requests_failed=workflow_stats.tasks_failed,
            fixes_generated=workflow_stats.tasks_completed,  # Approximation
            fixes_applied=workflow_stats.tasks_completed,    # Approximation
            fixes_successful=workflow_stats.tasks_completed  # Approximation
        )
        
        return CircleCIIntegrationMetrics(
            webhook_stats=webhook_stats,
            analysis_stats=analysis_stats,
            fix_stats=fix_stats,
            uptime_start=self.start_time or datetime.now(),
            builds_monitored=webhook_stats.workflow_events + webhook_stats.job_events,
            failures_detected=analysis_stats.failures_analyzed,
            projects_monitored=len(self.config.monitored_projects) if not self.config.monitor_all_projects else 0
        )
    
    def get_integration_status(self) -> IntegrationStatus:
        """Get current integration status"""
        return self.health_status
    
    async def get_recent_events(self, limit: int = 10) -> List[CircleCIEvent]:
        """Get recent webhook events"""
        return self.webhook_processor.get_recent_events(limit)
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get active workflow tasks"""
        tasks = self.workflow_automation.get_active_tasks()
        return [
            {
                "id": task.id,
                "type": task.type,
                "title": task.title,
                "status": task.status.value,
                "progress": task.progress.__dict__ if task.progress else None,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None
            }
            for task in tasks
        ]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a workflow task"""
        return await self.workflow_automation.cancel_task(task_id)
    
    async def replay_webhook_event(self, event_id: str) -> bool:
        """Replay a webhook event"""
        return await self.webhook_processor.replay_event(event_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        if self.last_health_check is None or (datetime.now() - self.last_health_check).seconds > 300:
            await self._perform_health_check()
        
        return {
            "healthy": self.health_status.healthy,
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "components": {
                "api": self.health_status.api_healthy,
                "webhook": self.health_status.webhook_healthy,
                "analysis": self.health_status.analysis_healthy,
                "fix_generation": self.health_status.fix_generation_healthy
            },
            "metrics": self.get_metrics().__dict__,
            "last_check": self.last_health_check.isoformat() if self.last_health_check else None
        }
    
    async def run_forever(self):
        """Run the agent forever (useful for standalone deployment)"""
        if not self.is_running:
            await self.start()
        
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop()

