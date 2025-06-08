"""Example demonstrating the unified extension system.

This example shows how to:
1. Set up the unified extension system
2. Register extensions and adapters
3. Create and execute workflows
4. Handle events and messages between extensions
"""

import asyncio
import logging
from typing import Dict, Any

# Core system imports
from src.contexten.extensions.core.registry import ExtensionRegistry
from src.contexten.extensions.core.event_bus import EventBus, EventBusConfig
from src.contexten.extensions.core.orchestrator import (
    WorkflowOrchestrator, WorkflowDefinition, TaskDefinition, TaskType
)
from src.contexten.extensions.core.connection import ConnectionManager
from src.contexten.extensions.core.extension_base import ExtensionEvent

# Extension adapters
from src.contexten.extensions.adapters.linear_adapter import LinearExtensionAdapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedExtensionSystemExample:
    """Example demonstrating the unified extension system."""

    def __init__(self):
        """Initialize the example system."""
        # Core components
        self.connection_manager = ConnectionManager()
        self.event_bus = EventBus(EventBusConfig(
            max_queue_size=1000,
            enable_metrics=True,
            enable_persistence=False
        ))
        self.extension_registry = ExtensionRegistry(self.connection_manager)
        self.orchestrator = WorkflowOrchestrator(self.event_bus, self.extension_registry)
        
        # Extensions
        self.linear_adapter = LinearExtensionAdapter()

    async def setup_system(self) -> None:
        """Set up the unified extension system."""
        logger.info("Setting up unified extension system...")
        
        # Start core components
        await self.event_bus.start()
        await self.orchestrator.start()
        
        # Add discovery paths for automatic extension discovery
        self.extension_registry.add_discovery_path("src/contexten/extensions")
        
        # Discover and register extensions automatically
        discovered = await self.extension_registry.discover_extensions()
        logger.info(f"Auto-discovered extensions: {discovered}")
        
        # Manually register adapters
        await self.extension_registry.register_extension(
            self.linear_adapter.metadata,
            instance=self.linear_adapter
        )
        
        # Start all extensions
        start_results = await self.extension_registry.start_all_extensions()
        logger.info(f"Extension start results: {start_results}")
        
        # Set up event handlers
        self.event_bus.subscribe(
            "example_system",
            self._handle_system_event
        )
        
        logger.info("Unified extension system setup complete")

    async def demonstrate_basic_usage(self) -> None:
        """Demonstrate basic extension usage."""
        logger.info("=== Demonstrating Basic Extension Usage ===")
        
        # List registered extensions
        extensions = self.extension_registry.list_extensions()
        logger.info(f"Registered extensions: {extensions}")
        
        # Get extension capabilities
        for ext_name in extensions:
            registration = self.extension_registry.get_extension(ext_name)
            if registration:
                capabilities = [cap.name for cap in registration.capabilities]
                logger.info(f"{ext_name} capabilities: {capabilities}")
        
        # Find extensions by capability
        issue_trackers = self.extension_registry.find_extensions_by_capability("issue_management")
        logger.info(f"Extensions with issue management capability: {issue_trackers}")
        
        # Check extension health
        health_results = await self.extension_registry.health_check_all()
        logger.info(f"Extension health status: {health_results}")

    async def demonstrate_linear_integration(self) -> None:
        """Demonstrate Linear extension integration."""
        logger.info("=== Demonstrating Linear Integration ===")
        
        try:
            # Create a Linear issue using the adapter
            issue_data = await self.linear_adapter.create_issue(
                title="Test Issue from Unified System",
                description="This issue was created through the unified extension system",
                priority=2
            )
            logger.info(f"Created Linear issue: {issue_data.get('id', 'Unknown ID')}")
            
            # Search for issues
            issues = await self.linear_adapter.search_issues(
                query="Test Issue",
                limit=5
            )
            logger.info(f"Found {len(issues)} issues matching search")
            
            # Get teams
            teams = await self.linear_adapter.get_teams()
            logger.info(f"Available teams: {len(teams)}")
            
        except Exception as e:
            logger.error(f"Linear integration demo failed: {e}")

    async def demonstrate_event_system(self) -> None:
        """Demonstrate the event system."""
        logger.info("=== Demonstrating Event System ===")
        
        # Publish some test events
        events = [
            ExtensionEvent(
                type="code.analyzed",
                source="graph_sitter",
                data={"file": "example.py", "issues_found": 3}
            ),
            ExtensionEvent(
                type="issue.created",
                source="linear",
                data={"issue_id": "TEST-123", "title": "Fix code issues"}
            ),
            ExtensionEvent(
                type="build.started",
                source="circleci",
                data={"build_id": "build-456", "branch": "main"}
            )
        ]
        
        for event in events:
            await self.event_bus.publish(event)
            logger.info(f"Published event: {event.type} from {event.source}")
        
        # Wait a bit for events to be processed
        await asyncio.sleep(1)
        
        # Get event metrics
        metrics = self.event_bus.get_metrics()
        logger.info(f"Event bus metrics: {metrics.dict()}")
        
        # Get event history
        history = self.event_bus.get_event_history(limit=10)
        logger.info(f"Recent events: {len(history)}")

    async def demonstrate_workflow_orchestration(self) -> None:
        """Demonstrate workflow orchestration."""
        logger.info("=== Demonstrating Workflow Orchestration ===")
        
        # Define a sample workflow
        workflow = WorkflowDefinition(
            id="code_analysis_workflow",
            name="Code Analysis and Issue Creation Workflow",
            description="Analyze code, create issues for problems, and notify team",
            tasks=[
                TaskDefinition(
                    id="analyze_code",
                    name="Analyze Code",
                    type=TaskType.EXTENSION_CALL,
                    extension="graph_sitter",
                    method="analyze_file",
                    parameters={
                        "file_path": "${file_path}",
                        "language": "python"
                    }
                ),
                TaskDefinition(
                    id="create_issue",
                    name="Create Issue for Problems",
                    type=TaskType.EXTENSION_CALL,
                    extension="linear",
                    method="create_issue",
                    parameters={
                        "title": "Code issues found in ${file_path}",
                        "description": "Analysis found ${task_analyze_code_result.issue_count} issues",
                        "priority": 2
                    },
                    depends_on=["analyze_code"]
                ),
                TaskDefinition(
                    id="notify_team",
                    name="Notify Team",
                    type=TaskType.EXTENSION_CALL,
                    extension="slack",
                    method="send_message",
                    parameters={
                        "channel": "#development",
                        "message": "Created issue ${task_create_issue_result.id} for code problems"
                    },
                    depends_on=["create_issue"]
                )
            ],
            triggers=["code.analyzed"]
        )
        
        # Register the workflow
        if self.orchestrator.register_workflow(workflow):
            logger.info(f"Registered workflow: {workflow.name}")
        else:
            logger.error("Failed to register workflow")
            return
        
        # Execute the workflow manually
        try:
            execution_id = await self.orchestrator.execute_workflow(
                workflow.id,
                context={"file_path": "src/example.py"},
                triggered_by="manual_demo"
            )
            logger.info(f"Started workflow execution: {execution_id}")
            
            # Wait for execution to complete
            await asyncio.sleep(5)
            
            # Check execution status
            execution = self.orchestrator.get_execution(execution_id)
            if execution:
                logger.info(f"Workflow status: {execution.status}")
                logger.info(f"Task statuses: {[(t.task_id, t.status) for t in execution.task_executions.values()]}")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")

    async def demonstrate_extension_communication(self) -> None:
        """Demonstrate inter-extension communication."""
        logger.info("=== Demonstrating Extension Communication ===")
        
        # Send a message between extensions
        try:
            response = await self.event_bus.publish_message(
                source="example_system",
                target="linear",
                message_type="get_teams",
                payload={}
            )
            
            if response and response.success:
                logger.info(f"Message response: {response.data}")
            else:
                logger.error(f"Message failed: {response.error if response else 'No response'}")
                
        except Exception as e:
            logger.error(f"Extension communication failed: {e}")

    async def _handle_system_event(self, event: ExtensionEvent) -> None:
        """Handle system events.
        
        Args:
            event: Event to handle
        """
        logger.info(f"System event handler received: {event.type} from {event.source}")
        
        # Example event processing logic
        if event.type == "code.analyzed":
            logger.info("Code analysis completed, could trigger issue creation workflow")
        elif event.type == "issue.created":
            logger.info("Issue created, could notify stakeholders")
        elif event.type == "build.started":
            logger.info("Build started, could update issue status")

    async def cleanup_system(self) -> None:
        """Clean up the system."""
        logger.info("Cleaning up unified extension system...")
        
        # Stop all extensions
        await self.extension_registry.stop_all_extensions()
        
        # Stop core components
        await self.orchestrator.stop()
        await self.event_bus.stop()
        
        logger.info("System cleanup complete")

    async def run_complete_demo(self) -> None:
        """Run the complete demonstration."""
        try:
            await self.setup_system()
            await self.demonstrate_basic_usage()
            await self.demonstrate_linear_integration()
            await self.demonstrate_event_system()
            await self.demonstrate_workflow_orchestration()
            await self.demonstrate_extension_communication()
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
        finally:
            await self.cleanup_system()


async def main():
    """Main function to run the example."""
    logger.info("Starting Unified Extension System Example")
    
    example = UnifiedExtensionSystemExample()
    await example.run_complete_demo()
    
    logger.info("Example completed")


if __name__ == "__main__":
    asyncio.run(main())

