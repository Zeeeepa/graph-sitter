import os
from typing import Any, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.configs.models.secrets import SecretsConfig
from codegen.sdk.core.codebase import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

from .github import GitHub
from .linear import Linear
from .slack import Slack
from .engine import EventProcessingEngine, EventProcessor, EventPriority, create_event_engine
from .storage import EventStorage, create_event_storage
from .streaming import EventStreamingManager, create_streaming_manager, StreamFilter

logger = get_logger(__name__)


class CodegenApp:
    """A FastAPI-based application for handling various code-related events with enhanced processing."""

    github: GitHub
    linear: Linear
    slack: Slack
    event_engine: EventProcessingEngine
    event_storage: Optional[EventStorage]
    streaming_manager: EventStreamingManager

    def __init__(self, 
                 name: str, 
                 repo: Optional[str] = None, 
                 tmp_dir: str = "/tmp/codegen", 
                 commit: str | None = "latest",
                 event_config: Optional[dict] = None,
                 database_config: Optional[dict] = None):
        self.name = name
        self.tmp_dir = tmp_dir

        # Create the FastAPI app
        self.app = FastAPI(title=name)

        # Initialize event system components
        self.event_engine = create_event_engine(event_config or {})
        self.streaming_manager = create_streaming_manager()
        
        # Initialize database storage if configured
        self.event_storage = None
        if database_config:
            try:
                self.event_storage = create_event_storage(database_config)
                self.event_engine.set_storage(self.event_storage)
                logger.info("Event storage initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize event storage: {e}")

        # Initialize event handlers with enhanced capabilities
        self.linear = Linear(self)
        self.slack = Slack(self)
        self.github = GitHub(self)
        
        self.repo = repo
        self.commit = commit
        # Initialize codebase cache
        self.codebase: Codebase | None = None

        # Register routes
        self._setup_routes()
        
        # Setup event processing integration
        self._setup_event_processing()
        
        # Start event processing engine
        self.event_engine.start()

    def _setup_event_processing(self):
        """Setup integration between event handlers and processing engine."""
        # Register default event processors
        self._register_default_processors()
        
        # Setup streaming integration
        self._setup_streaming_integration()
        
    def _register_default_processors(self):
        """Register default event processors for each platform."""
        
        # GitHub event processor
        github_processor = EventProcessor(
            name="github_processor",
            handler=self._process_github_event,
            event_filters={"platform": "github"},
            priority=EventPriority.NORMAL,
            is_async=True
        )
        self.event_engine.register_processor(github_processor)
        
        # Linear event processor
        linear_processor = EventProcessor(
            name="linear_processor", 
            handler=self._process_linear_event,
            event_filters={"platform": "linear"},
            priority=EventPriority.NORMAL,
            is_async=True
        )
        self.event_engine.register_processor(linear_processor)
        
        # Slack event processor
        slack_processor = EventProcessor(
            name="slack_processor",
            handler=self._process_slack_event,
            event_filters={"platform": "slack"},
            priority=EventPriority.HIGH,  # Slack events often need quick response
            is_async=True
        )
        self.event_engine.register_processor(slack_processor)
        
        # High priority processor for critical events
        critical_processor = EventProcessor(
            name="critical_processor",
            handler=self._process_critical_event,
            event_filters={},  # Will check priority in handler
            priority=EventPriority.CRITICAL,
            is_async=True
        )
        self.event_engine.register_processor(critical_processor)
        
    def _setup_streaming_integration(self):
        """Setup streaming integration for real-time event delivery."""
        # Subscribe to all events for logging and monitoring
        self.streaming_manager.subscribe_internal(
            "all_events",
            self._log_event_stream,
            "internal_logger"
        )
        
        # Subscribe to high priority events for alerts
        high_priority_filter = StreamFilter(
            custom_filters={"priority": "high"}
        )
        self.streaming_manager.subscribe_internal(
            "high_priority",
            self._handle_high_priority_alert,
            "alert_handler",
            high_priority_filter
        )

    async def _process_github_event(self, event):
        """Process GitHub events through the enhanced system."""
        logger.info(f"Processing GitHub event: {event.event_type}")
        
        # Call existing GitHub handler
        if event.event_type in self.github.registered_handlers:
            handler = self.github.registered_handlers[event.event_type]
            result = handler(event.payload)
            if hasattr(result, "__await__"):
                result = await result
            return result
            
        return {"message": "GitHub event processed"}
        
    async def _process_linear_event(self, event):
        """Process Linear events through the enhanced system."""
        logger.info(f"Processing Linear event: {event.event_type}")
        
        # Extract Linear event type from payload
        linear_event_type = event.payload.get("type")
        if linear_event_type and linear_event_type in self.linear.registered_handlers:
            handler = self.linear.registered_handlers[linear_event_type]
            result = handler(event.payload)
            if hasattr(result, "__await__"):
                result = await result
            return result
            
        return {"message": "Linear event processed"}
        
    async def _process_slack_event(self, event):
        """Process Slack events through the enhanced system."""
        logger.info(f"Processing Slack event: {event.event_type}")
        
        # Call existing Slack handler
        result = await self.slack.handle(event.payload)
        return result
        
    async def _process_critical_event(self, event):
        """Process critical priority events."""
        if event.priority == EventPriority.CRITICAL:
            logger.critical(f"Processing critical event: {event.event_type} from {event.platform}")
            # Add special handling for critical events
            # Could send alerts, notifications, etc.
        return {"message": "Critical event processed"}
        
    def _log_event_stream(self, event):
        """Log all events for monitoring."""
        logger.debug(f"Event stream: {event.platform}.{event.event_type} from {event.source_name}")
        
    def _handle_high_priority_alert(self, event):
        """Handle high priority event alerts."""
        logger.warning(f"High priority event alert: {event.platform}.{event.event_type}")
        # Could integrate with alerting systems here

    def parse_repo(self) -> None:
        # Parse initial repos if provided
        if self.repo:
            self._parse_repo(self.repo, self.commit)

    def _parse_repo(self, repo_name: str, commit: str | None = None) -> None:
        """Parse a GitHub repository and cache it.

        Args:
            repo_name: Repository name in format "owner/repo"
        """
        try:
            logger.info(f"[CODEBASE] Parsing repository: {repo_name}")
            config = CodebaseConfig(sync_enabled=True)
            secrets = SecretsConfig(github_token=os.environ.get("GITHUB_ACCESS_TOKEN"), linear_api_key=os.environ.get("LINEAR_ACCESS_TOKEN"))
            self.codebase = Codebase.from_repo(repo_full_name=repo_name, tmp_dir=self.tmp_dir, commit=commit, config=config, secrets=secrets)
            logger.info(f"[CODEBASE] Successfully parsed and cached: {repo_name}")
        except Exception as e:
            logger.exception(f"[CODEBASE] Failed to parse repository {repo_name}: {e!s}")
            raise

    def get_codebase(self) -> Codebase:
        """Get a cached codebase by repository name.

        Args:
            repo_name: Repository name in format "owner/repo"

        Returns:
            The cached Codebase instance

        Raises:
            KeyError: If the repository hasn't been parsed
        """
        if not self.codebase:
            msg = "Repository has not been parsed"
            raise KeyError(msg)
        return self.codebase

    def add_repo(self, repo_name: str) -> None:
        """Add a new repository to parse and cache.

        Args:
            repo_name: Repository name in format "owner/repo"
        """
        self._parse_repo(repo_name)

    async def simulate_event(self, provider: str, event_type: str, payload: dict) -> Any:
        """Simulate an event without running the server.

        Args:
            provider: The event provider ('slack', 'github', or 'linear')
            event_type: The type of event to simulate
            payload: The event payload

        Returns:
            The handler's response
        """
        provider_map = {"slack": self.slack, "github": self.github, "linear": self.linear}

        if provider not in provider_map:
            msg = f"Unknown provider: {provider}. Must be one of {list(provider_map.keys())}"
            raise ValueError(msg)

        handler = provider_map[provider]
        return await handler.handle(payload)

    async def root(self):
        """Render the main page."""
        return """
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Codegen</title>
                    <style>
                        body {
                            margin: 0;
                            height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            background-color: #1a1a1a;
                            color: #ffffff;
                        }
                        h1 {
                            font-size: 4rem;
                            font-weight: 700;
                            letter-spacing: -0.05em;
                        }
                    </style>
                </head>
                <body>
                    <h1>codegen</h1>
                </body>
            </html>
            """

    async def handle_slack_event(self, request: Request):
        """Handle incoming Slack events."""
        payload = await request.json()
        
        # Submit to enhanced event system
        event_type = payload.get('event', {}).get('type', 'unknown')
        self.event_engine.submit_event(
            platform='slack',
            event_type=event_type,
            payload=payload,
            source_id=payload.get('team_id'),
            source_name=payload.get('team_domain'),
            actor_id=payload.get('event', {}).get('user'),
            priority=EventPriority.HIGH if event_type == 'app_mention' else EventPriority.NORMAL
        )
        
        # Also broadcast to streaming system
        await self.streaming_manager.broadcast_event(
            self._create_processed_event('slack', event_type, payload)
        )
        
        return await self.slack.handle(payload)

    async def handle_github_event(self, request: Request):
        """Handle incoming GitHub events."""
        payload = await request.json()
        
        # Extract event information
        event_type = request.headers.get('x-github-event', 'unknown')
        action = payload.get('action')
        full_event_type = f"{event_type}:{action}" if action else event_type
        
        # Submit to enhanced event system
        repo = payload.get('repository', {})
        self.event_engine.submit_event(
            platform='github',
            event_type=full_event_type,
            payload=payload,
            source_id=str(repo.get('id')) if repo.get('id') else None,
            source_name=repo.get('full_name'),
            actor_id=payload.get('sender', {}).get('login'),
            actor_name=payload.get('sender', {}).get('login'),
            priority=EventPriority.HIGH if event_type in ['pull_request', 'issues'] else EventPriority.NORMAL
        )
        
        # Also broadcast to streaming system
        await self.streaming_manager.broadcast_event(
            self._create_processed_event('github', full_event_type, payload)
        )
        
        return await self.github.handle(payload, request)

    async def handle_linear_event(self, request: Request):
        """Handle incoming Linear events."""
        payload = await request.json()
        
        # Extract event information
        event_type = payload.get('type', 'unknown')
        data = payload.get('data', {})
        
        # Submit to enhanced event system
        self.event_engine.submit_event(
            platform='linear',
            event_type=event_type,
            payload=payload,
            source_id=data.get('teamId'),
            source_name=data.get('team', {}).get('name'),
            actor_id=payload.get('updatedById'),
            priority=EventPriority.NORMAL
        )
        
        # Also broadcast to streaming system
        await self.streaming_manager.broadcast_event(
            self._create_processed_event('linear', event_type, payload)
        )
        
        return await self.linear.handle(payload)
        
    def _create_processed_event(self, platform: str, event_type: str, payload: dict):
        """Create a ProcessedEvent for streaming."""
        from .engine import ProcessedEvent
        from datetime import datetime, timezone
        import uuid
        
        return ProcessedEvent(
            id=str(uuid.uuid4()),
            platform=platform,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(timezone.utc)
        )

    # Enhanced event submission methods
    def submit_deployment_event(self, 
                               deployment_id: str,
                               environment: str,
                               status: str,
                               repository_name: str,
                               commit_sha: str,
                               branch_name: str = None,
                               deployment_url: str = None,
                               log_url: str = None) -> str:
        """Submit a deployment event to the processing system."""
        payload = {
            'deployment_id': deployment_id,
            'environment': environment,
            'status': status,
            'repository_name': repository_name,
            'commit_sha': commit_sha,
            'branch_name': branch_name,
            'deployment_url': deployment_url,
            'log_url': log_url,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        priority = EventPriority.HIGH if environment == 'production' else EventPriority.NORMAL
        
        return self.event_engine.submit_event(
            platform='deployment',
            event_type=f'deployment:{status}',
            payload=payload,
            source_name=repository_name,
            priority=priority
        )
        
    def submit_custom_event(self,
                           platform: str,
                           event_type: str,
                           payload: dict,
                           source_id: str = None,
                           source_name: str = None,
                           actor_id: str = None,
                           actor_name: str = None,
                           priority: EventPriority = EventPriority.NORMAL) -> str:
        """Submit a custom event to the processing system."""
        return self.event_engine.submit_event(
            platform=platform,
            event_type=event_type,
            payload=payload,
            source_id=source_id,
            source_name=source_name,
            actor_id=actor_id,
            actor_name=actor_name,
            priority=priority
        )

    # Event system management methods
    def get_event_metrics(self) -> dict:
        """Get event processing metrics."""
        engine_metrics = self.event_engine.get_metrics()
        stream_stats = self.streaming_manager.get_stream_stats()
        queue_status = self.event_engine.get_queue_status()
        
        return {
            'processing': engine_metrics,
            'streaming': stream_stats,
            'queue': queue_status
        }
        
    def get_recent_events(self, limit: int = 50) -> list:
        """Get recent events from storage."""
        if self.event_storage:
            return [
                {
                    'id': event.id,
                    'platform': event.platform,
                    'event_type': event.event_type,
                    'source_name': event.source_name,
                    'actor_name': event.actor_name,
                    'created_at': event.created_at.isoformat(),
                    'processed_at': event.processed_at.isoformat() if event.processed_at else None
                }
                for event in self.event_storage.get_recent_events(limit)
            ]
        return []
        
    def subscribe_to_events(self, 
                           stream_name: str,
                           callback: callable,
                           subscriber_id: str,
                           filter_config: dict = None) -> str:
        """Subscribe to event stream with callback."""
        from .streaming import StreamFilter
        
        event_filter = None
        if filter_config:
            event_filter = StreamFilter(**filter_config)
            
        return self.streaming_manager.subscribe_internal(
            stream_name, callback, subscriber_id, event_filter
        )
        
    def unsubscribe_from_events(self, subscription_id: str):
        """Unsubscribe from event stream."""
        self.streaming_manager.unsubscribe(subscription_id)

    def cleanup(self):
        """Cleanup resources when shutting down."""
        logger.info("Shutting down CodegenApp...")
        
        # Stop event processing engine
        if hasattr(self, 'event_engine') and self.event_engine:
            self.event_engine.stop()
            
        # Close database connections
        if hasattr(self, 'event_storage') and self.event_storage:
            self.event_storage.close()
            
        # Cleanup streaming subscriptions
        if hasattr(self, 'streaming_manager') and self.streaming_manager:
            self.streaming_manager.cleanup_inactive_subscriptions()
            
        logger.info("CodegenApp shutdown complete")

    def _setup_routes(self):
        """Set up the FastAPI routes for different event types."""

        @self.app.get("/", response_class=HTMLResponse)
        async def _root():
            return await self.root()

        # @self.app.post("/{org}/{repo}/slack/events")
        @self.app.post("/slack/events")
        async def _handle_slack_event(request: Request):
            return await self.handle_slack_event(request)

        # @self.app.post("/{org}/{repo}/github/events")
        @self.app.post("/github/events")
        async def _handle_github_event(request: Request):
            return await self.handle_github_event(request)

        # @self.app.post("/{org}/{repo}/linear/events")
        @self.app.post("/linear/events")
        async def handle_linear_event(request: Request):
            return await self.handle_linear_event(request)

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the FastAPI application."""
        import uvicorn

        uvicorn.run(self.app, host=host, port=port, **kwargs)
