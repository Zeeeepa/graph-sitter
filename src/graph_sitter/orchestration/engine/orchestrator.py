"""
Multi-Platform Orchestration Engine

Main orchestrator class that coordinates workflows across GitHub, Linear, Slack
and other integrated platforms.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..workflow.manager import WorkflowManager
from ..events.correlator import EventCorrelator
from ..triggers.system import AutomatedTriggerSystem
from ..integrations.github_client import GitHubIntegration
from ..integrations.linear_client import LinearIntegration
from ..integrations.slack_client import SlackIntegration


class OrchestrationStatus(Enum):
    """Status of orchestration operations"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestration engine"""
    github_enabled: bool = True
    linear_enabled: bool = True
    slack_enabled: bool = True
    max_concurrent_workflows: int = 10
    event_correlation_window: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    auto_retry_failed_workflows: bool = True
    max_retry_attempts: int = 3
    monitoring_interval: timedelta = field(default_factory=lambda: timedelta(seconds=30))


class MultiPlatformOrchestrator:
    """
    Main orchestration engine that coordinates workflows across multiple platforms.
    
    This class serves as the central coordinator for:
    - Multi-platform workflow execution
    - Cross-platform event correlation
    - Automated trigger management
    - Real-time monitoring and coordination
    """
    
    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.status = OrchestrationStatus.IDLE
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.workflow_manager = WorkflowManager()
        self.event_correlator = EventCorrelator(
            correlation_window=config.event_correlation_window
        )
        self.trigger_system = AutomatedTriggerSystem()
        
        # Platform integrations
        self.integrations: Dict[str, Any] = {}
        self._initialize_integrations()
        
        # Runtime state
        self.active_workflows: Dict[str, Any] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        
    def _initialize_integrations(self):
        """Initialize platform integrations based on configuration"""
        if self.config.github_enabled:
            self.integrations['github'] = GitHubIntegration()
            
        if self.config.linear_enabled:
            self.integrations['linear'] = LinearIntegration()
            
        if self.config.slack_enabled:
            self.integrations['slack'] = SlackIntegration()
            
        self.logger.info(f"Initialized integrations: {list(self.integrations.keys())}")
    
    async def start(self):
        """Start the orchestration engine"""
        if self.status == OrchestrationStatus.RUNNING:
            self.logger.warning("Orchestrator is already running")
            return
            
        self.logger.info("Starting multi-platform orchestrator")
        self.status = OrchestrationStatus.RUNNING
        
        # Start core components
        await self.workflow_manager.start()
        await self.event_correlator.start()
        await self.trigger_system.start()
        
        # Start platform integrations
        for name, integration in self.integrations.items():
            try:
                await integration.start()
                self.logger.info(f"Started {name} integration")
            except Exception as e:
                self.logger.error(f"Failed to start {name} integration: {e}")
        
        # Start monitoring
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Multi-platform orchestrator started successfully")
    
    async def stop(self):
        """Stop the orchestration engine"""
        self.logger.info("Stopping multi-platform orchestrator")
        self.status = OrchestrationStatus.STOPPED
        
        # Stop monitoring
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Stop core components
        await self.workflow_manager.stop()
        await self.event_correlator.stop()
        await self.trigger_system.stop()
        
        # Stop platform integrations
        for name, integration in self.integrations.items():
            try:
                await integration.stop()
                self.logger.info(f"Stopped {name} integration")
            except Exception as e:
                self.logger.error(f"Error stopping {name} integration: {e}")
        
        self.logger.info("Multi-platform orchestrator stopped")
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> str:
        """
        Execute a workflow across multiple platforms
        
        Args:
            workflow_id: Unique identifier for the workflow
            context: Execution context and parameters
            
        Returns:
            Execution ID for tracking the workflow
        """
        if len(self.active_workflows) >= self.config.max_concurrent_workflows:
            raise RuntimeError("Maximum concurrent workflows reached")
        
        execution_id = f"{workflow_id}_{datetime.now().isoformat()}"
        
        try:
            # Start workflow execution
            execution = await self.workflow_manager.execute(
                workflow_id=workflow_id,
                context=context,
                integrations=self.integrations
            )
            
            self.active_workflows[execution_id] = execution
            self.logger.info(f"Started workflow execution: {execution_id}")
            
            return execution_id
            
        except Exception as e:
            self.logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            raise
    
    async def handle_platform_event(self, platform: str, event: Dict[str, Any]):
        """
        Handle events from integrated platforms
        
        Args:
            platform: Source platform (github, linear, slack, etc.)
            event: Event data
        """
        try:
            # Correlate with other events
            correlated_events = await self.event_correlator.correlate_event(
                platform=platform,
                event=event
            )
            
            # Check for automated triggers
            triggered_workflows = await self.trigger_system.check_triggers(
                platform=platform,
                event=event,
                correlated_events=correlated_events
            )
            
            # Execute triggered workflows
            for workflow_config in triggered_workflows:
                await self.execute_workflow(
                    workflow_id=workflow_config['workflow_id'],
                    context=workflow_config['context']
                )
            
            # Notify event handlers
            handlers = self.event_handlers.get(platform, [])
            for handler in handlers:
                try:
                    await handler(event, correlated_events)
                except Exception as e:
                    self.logger.error(f"Event handler error: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error handling {platform} event: {e}")
    
    def register_event_handler(self, platform: str, handler: Callable):
        """Register an event handler for a specific platform"""
        if platform not in self.event_handlers:
            self.event_handlers[platform] = []
        self.event_handlers[platform].append(handler)
    
    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow execution"""
        if execution_id not in self.active_workflows:
            return None
            
        execution = self.active_workflows[execution_id]
        return await self.workflow_manager.get_execution_status(execution.id)
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        if execution_id not in self.active_workflows:
            return False
            
        execution = self.active_workflows[execution_id]
        success = await self.workflow_manager.cancel_execution(execution.id)
        
        if success:
            del self.active_workflows[execution_id]
            
        return success
    
    async def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get orchestration metrics and status"""
        return {
            'status': self.status.value,
            'active_workflows': len(self.active_workflows),
            'integrations': {
                name: await integration.get_status()
                for name, integration in self.integrations.items()
            },
            'workflow_manager': await self.workflow_manager.get_metrics(),
            'event_correlator': await self.event_correlator.get_metrics(),
            'trigger_system': await self.trigger_system.get_metrics(),
        }
    
    async def _monitoring_loop(self):
        """Internal monitoring loop for health checks and cleanup"""
        while self.status == OrchestrationStatus.RUNNING:
            try:
                # Check workflow health
                completed_workflows = []
                for execution_id, execution in self.active_workflows.items():
                    status = await self.workflow_manager.get_execution_status(execution.id)
                    if status and status.get('completed', False):
                        completed_workflows.append(execution_id)
                
                # Clean up completed workflows
                for execution_id in completed_workflows:
                    del self.active_workflows[execution_id]
                    self.logger.debug(f"Cleaned up completed workflow: {execution_id}")
                
                # Check integration health
                for name, integration in self.integrations.items():
                    try:
                        health = await integration.health_check()
                        if not health.get('healthy', False):
                            self.logger.warning(f"{name} integration unhealthy: {health}")
                    except Exception as e:
                        self.logger.error(f"Health check failed for {name}: {e}")
                
                await asyncio.sleep(self.config.monitoring_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

