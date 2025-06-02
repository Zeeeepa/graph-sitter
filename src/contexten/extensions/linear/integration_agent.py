"""
Linear Integration Agent

Main orchestrator for comprehensive Linear integration that coordinates:
- Enhanced Linear client with caching and rate limiting
- Webhook processing with event routing
- Assignment detection and auto-assignment
- Workflow automation with Codegen SDK integration
- Real-time monitoring and health checks
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import asyncio

from .assignment_detector import AssignmentDetector
from .config import LinearIntegrationConfig, get_linear_config
from .enhanced_client import EnhancedLinearClient
from .types import (
from .webhook_processor import WebhookProcessor
from .workflow_automation import WorkflowAutomation
    LinearIntegrationMetrics, IntegrationStatus, ComponentStats
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class LinearIntegrationAgent:
    """Comprehensive Linear integration agent"""
    
    def __init__(self, config: Optional[LinearIntegrationConfig] = None):
        # Load configuration
        self.config = config or get_linear_config()
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            logger.error(f"Configuration validation failed: {errors}")
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")
        
        # Initialize components
        self.linear_client = EnhancedLinearClient(self.config)
        self.webhook_processor = WebhookProcessor(self.config)
        self.assignment_detector = AssignmentDetector(self.config)
        self.workflow_automation = WorkflowAutomation(self.config)
        
        # Set up component relationships
        self.workflow_automation.set_linear_client(self.linear_client)
        
        # State tracking
        self.initialized = False
        self.monitoring_active = False
        self.last_sync = None
        self.last_health_check = None
        
        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.start_time = datetime.now()
        
        # Register webhook handlers
        self._register_webhook_handlers()
        
        logger.info("Linear integration agent initialized")
    
    def _register_webhook_handlers(self) -> None:
        """Register webhook event handlers"""
        
        # Assignment detection handler
        async def assignment_handler(event_data: Dict[str, Any]) -> None:
            try:
                assignment_event = await self.assignment_detector.detect_assignment_change(event_data)
                if assignment_event:
                    should_process = await self.assignment_detector.should_process_assignment(assignment_event)
                    if should_process:
                        # Handle the assignment
                        success = await self.workflow_automation.handle_assignment(assignment_event)
                        if success:
                            await self.assignment_detector.mark_assignment_processed(assignment_event.issue_id)
                            logger.info(f"Successfully processed assignment for issue {assignment_event.issue_id}")
                        else:
                            logger.error(f"Failed to process assignment for issue {assignment_event.issue_id}")
            except Exception as e:
                logger.error(f"Error in assignment handler: {e}")
        
        # Auto-assignment handler
        async def auto_assignment_handler(event_data: Dict[str, Any]) -> None:
            try:
                should_auto_assign = await self.assignment_detector.detect_auto_assignment_candidates(event_data)
                if should_auto_assign:
                    issue_id = event_data.get("data", {}).get("id")
                    if issue_id:
                        success = await self.assignment_detector.create_auto_assignment(
                            issue_id, 
                            self.linear_client
                        )
                        if success:
                            logger.info(f"Successfully auto-assigned issue {issue_id}")
                        else:
                            logger.warning(f"Failed to auto-assign issue {issue_id}")
            except Exception as e:
                logger.error(f"Error in auto-assignment handler: {e}")
        
        # Progress tracking handler
        async def progress_handler(event_data: Dict[str, Any]) -> None:
            try:
                # Handle issue updates that might affect task progress
                event_type = event_data.get("type", "")
                if event_type in ["IssueUpdate"]:
                    issue_id = event_data.get("data", {}).get("id")
                    if issue_id and issue_id in self.workflow_automation.active_tasks:
                        # Check for status changes or comments that might indicate progress
                        # This is a placeholder for more sophisticated progress tracking
                        logger.debug(f"Received update for tracked issue {issue_id}")
            except Exception as e:
                logger.error(f"Error in progress handler: {e}")
        
        # Register handlers with different priorities
        self.webhook_processor.register_global_handler(
            assignment_handler, 
            name="assignment_detection",
            priority=100
        )
        
        self.webhook_processor.register_global_handler(
            auto_assignment_handler,
            name="auto_assignment",
            priority=90
        )
        
        self.webhook_processor.register_global_handler(
            progress_handler,
            name="progress_tracking",
            priority=80
        )
        
        logger.info("Registered webhook handlers")
    
    async def initialize(self) -> bool:
        """Initialize the integration agent"""
        try:
            if not self.config.enabled:
                logger.info("Linear integration is disabled")
                return True
            
            logger.info("Initializing Linear integration agent...")
            
            # Initialize Linear client
            await self.linear_client.initialize()
            
            # Authenticate with Linear
            if not await self.linear_client.authenticate(self.config.api.api_key):
                logger.error("Failed to authenticate with Linear API")
                return False
            
            # Update bot configuration with authenticated user info
            if self.linear_client.user_info:
                if not self.config.bot.bot_user_id:
                    self.config.bot.bot_user_id = self.linear_client.user_info.get("id")
                if not self.config.bot.bot_email:
                    self.config.bot.bot_email = self.linear_client.user_info.get("email")
                
                logger.info(f"Bot configured as: {self.config.bot.bot_email} ({self.config.bot.bot_user_id})")
            
            # Load persisted events
            await self.webhook_processor.load_failed_events()
            
            # Start webhook processing
            await self.webhook_processor.start_processing()
            
            # Start workflow automation background tasks
            await self.workflow_automation.start_background_tasks()
            
            self.initialized = True
            self.last_sync = datetime.now()
            
            logger.info("Linear integration agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Linear integration agent: {e}")
            return False
    
    async def start_monitoring(self) -> None:
        """Start monitoring for assignments and health checks"""
        if not self.initialized:
            logger.error("Agent not initialized, cannot start monitoring")
            return
        
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        
        # Start assignment monitoring
        if self.config.monitoring.enabled:
            self.monitoring_task = asyncio.create_task(self._assignment_monitoring_loop())
        
        # Start health checks
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("Started Linear integration monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring tasks"""
        if not self.monitoring_active:
            logger.warning("Monitoring is not active")
            return
        
        self.monitoring_active = False
        
        # Cancel monitoring tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped Linear integration monitoring")
    
    async def handle_webhook(self, payload: bytes, signature: str, headers: Optional[Dict[str, str]] = None) -> bool:
        """Handle incoming webhook"""
        try:
            if not self.initialized:
                logger.error("Agent not initialized, cannot handle webhook")
                return False
            
            success = await self.webhook_processor.process_webhook(payload, signature, headers)
            
            if success:
                logger.debug("Webhook processed successfully")
            else:
                logger.error("Webhook processing failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return False
    
    async def process_event_directly(self, event_data: Dict[str, Any]) -> bool:
        """Process an event directly without webhook validation"""
        try:
            if not self.initialized:
                logger.error("Agent not initialized, cannot process event")
                return False
            
            return await self.webhook_processor.process_event_directly(event_data)
            
        except Exception as e:
            logger.error(f"Error processing event directly: {e}")
            return False
    
    async def sync_with_linear(self) -> bool:
        """Sync state with Linear"""
        try:
            logger.info("Syncing with Linear...")
            
            # Get active tasks
            active_tasks = self.workflow_automation.get_active_tasks()
            
            # Sync progress for each active task
            sync_count = 0
            for issue_id, task_info in active_tasks.items():
                try:
                    # Create progress data
                    progress_data = {
                        "status": task_info["status"],
                        "progress_percentage": task_info["progress"],
                        "current_step": task_info["current_step"]
                    }
                    
                    if await self.workflow_automation.sync_progress(issue_id, progress_data):
                        sync_count += 1
                
                except Exception as e:
                    logger.error(f"Error syncing progress for issue {issue_id}: {e}")
            
            self.last_sync = datetime.now()
            logger.info(f"Synced {sync_count} tasks with Linear")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing with Linear: {e}")
            return False
    
    async def get_integration_status(self) -> IntegrationStatus:
        """Get comprehensive integration status"""
        try:
            # Get component statuses
            webhook_status = "running" if self.webhook_processor.is_processing else "stopped"
            assignment_status = "running" if self.monitoring_active else "stopped"
            workflow_status = "running" if self.workflow_automation.is_running else "stopped"
            
            # Count active tasks
            active_tasks = len(self.workflow_automation.active_tasks)
            
            # Get event statistics
            webhook_stats = self.webhook_processor.get_processing_stats()
            
            status = IntegrationStatus(
                initialized=self.initialized,
                monitoring_active=self.monitoring_active,
                last_sync=self.last_sync,
                webhook_processor_status=webhook_status,
                assignment_detector_status=assignment_status,
                workflow_automation_status=workflow_status,
                event_manager_status="running",  # Placeholder
                active_tasks=active_tasks,
                processed_events=webhook_stats.events_processed,
                failed_events=webhook_stats.events_failed,
                last_error=webhook_stats.last_error
            )
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting integration status: {e}")
            return IntegrationStatus(last_error=str(e))
    
    async def get_metrics(self) -> LinearIntegrationMetrics:
        """Get comprehensive integration metrics"""
        try:
            status = await self.get_integration_status()
            
            # Get component statistics
            client_stats = self.linear_client.get_stats()
            webhook_stats = self.webhook_processor.get_stats()
            assignment_stats = self.assignment_detector.get_stats()
            workflow_stats = self.workflow_automation.get_stats()
            
            # Create placeholder event stats
            event_stats = ComponentStats()
            
            metrics = LinearIntegrationMetrics(
                status=status,
                client_stats=client_stats,
                webhook_stats=webhook_stats,
                assignment_stats=assignment_stats,
                workflow_stats=workflow_stats,
                event_stats=event_stats,
                collected_at=datetime.now()
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            # Return minimal metrics with error
            return LinearIntegrationMetrics(
                status=IntegrationStatus(last_error=str(e)),
                client_stats=ComponentStats(),
                webhook_stats=ComponentStats(),
                assignment_stats=ComponentStats(),
                workflow_stats=ComponentStats(),
                event_stats=ComponentStats(),
                collected_at=datetime.now()
            )
    
    async def _assignment_monitoring_loop(self) -> None:
        """Background loop for monitoring assignments"""
        logger.info("Starting assignment monitoring loop")
        
        while self.monitoring_active:
            try:
                # Get assigned issues for the bot
                if self.config.bot.bot_user_id:
                    assigned_issues = await self.linear_client.get_user_assigned_issues(
                        self.config.bot.bot_user_id,
                        limit=50,
                        include_completed=False
                    )
                    
                    # Process each assigned issue
                    for issue in assigned_issues:
                        await self._process_monitored_issue(issue)
                
                # Wait before next check
                await asyncio.sleep(self.config.monitoring.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in assignment monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
        
        logger.info("Assignment monitoring loop stopped")
    
    async def _process_monitored_issue(self, issue) -> None:
        """Process an issue found during monitoring"""
        try:
            # Check if we've already processed this assignment
            if issue.id in self.assignment_detector.processed_assignments:
                return
            
            # Check if issue should be processed
            if await self.assignment_detector.is_bot_assigned(issue):
                # Create assignment event
                from .types import AssignmentEvent, AssignmentAction
                assignment_event = AssignmentEvent(
                    issue_id=issue.id,
                    action=AssignmentAction.ASSIGNED,
                    assignee_id=issue.assignee_id,
                    timestamp=datetime.now(),
                    metadata={"source": "monitoring"}
                )
                
                # Process assignment
                if await self.assignment_detector.should_process_assignment(assignment_event):
                    success = await self.workflow_automation.handle_assignment(assignment_event)
                    if success:
                        await self.assignment_detector.mark_assignment_processed(issue.id)
                        logger.info(f"Processed monitored assignment for issue {issue.id}")
            
        except Exception as e:
            logger.error(f"Error processing monitored issue {issue.id}: {e}")
    
    async def _health_check_loop(self) -> None:
        """Background loop for health checks"""
        logger.info("Starting health check loop")
        
        while self.monitoring_active:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.monitoring.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
        
        logger.info("Health check loop stopped")
    
    async def _perform_health_check(self) -> None:
        """Perform comprehensive health check"""
        try:
            self.last_health_check = datetime.now()
            
            # Check Linear API connectivity
            if self.linear_client.user_info:
                logger.debug("Linear API connectivity: OK")
            else:
                logger.warning("Linear API connectivity: Failed")
            
            # Check webhook processor
            queue_info = self.webhook_processor.get_queue_info()
            if queue_info["queue_size"] > queue_info["max_queue_size"] * 0.8:
                logger.warning(f"Webhook queue is {queue_info['queue_size']}/{queue_info['max_queue_size']} (80%+ full)")
            
            # Check failed events
            if queue_info["failed_events"] > 10:
                logger.warning(f"High number of failed events: {queue_info['failed_events']}")
            
            # Check active tasks
            active_tasks = self.workflow_automation.get_active_tasks()
            stuck_tasks = []
            
            for issue_id, task_info in active_tasks.items():
                # Check for stuck tasks (running for more than timeout)
                if task_info["status"] == "running":
                    task_age = datetime.now() - task_info["created_at"]
                    if task_age.total_seconds() > self.config.workflow.task_timeout:
                        stuck_tasks.append(issue_id)
            
            if stuck_tasks:
                logger.warning(f"Found {len(stuck_tasks)} stuck tasks: {stuck_tasks}")
                
                # Cancel stuck tasks
                for issue_id in stuck_tasks:
                    await self.workflow_automation.cancel_task(issue_id)
                    logger.info(f"Cancelled stuck task for issue {issue_id}")
            
            # Clean up old cache entries
            self.linear_client.clear_cache()
            
            logger.debug("Health check completed successfully")
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup resources and save state"""
        try:
            logger.info("Cleaning up Linear integration agent...")
            
            # Stop monitoring
            await self.stop_monitoring()
            
            # Stop workflow automation
            await self.workflow_automation.stop_background_tasks()
            
            # Stop webhook processing
            await self.webhook_processor.stop_processing()
            
            # Save failed events
            await self.webhook_processor.save_failed_events()
            
            # Close Linear client
            await self.linear_client.close()
            
            logger.info("Linear integration agent cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()


# Convenience function for creating and initializing the agent
async def create_linear_integration_agent(config: Optional[LinearIntegrationConfig] = None) -> LinearIntegrationAgent:
    """Create and initialize a Linear integration agent"""
    agent = LinearIntegrationAgent(config)
    
    if await agent.initialize():
        await agent.start_monitoring()
        return agent
    else:
        raise RuntimeError("Failed to initialize Linear integration agent")

