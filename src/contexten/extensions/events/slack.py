import logging
import os

from slack_sdk import WebClient

from contexten.extensions.events.interface import EventHandlerManagerProtocol
from contexten.extensions.slack.types import SlackWebhookPayload
from contexten.extensions.slack.enhanced_client import EnhancedSlackClient, SlackConfig, NotificationContext
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


class Slack(EventHandlerManagerProtocol):
    _client: WebClient | None = None
    _enhanced_client: EnhancedSlackClient | None = None

    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}
        
        # Initialize enhanced client if configuration is available
        self._initialize_enhanced_client()

    def _initialize_enhanced_client(self):
        """Initialize enhanced Slack client with configuration."""
        try:
            if os.environ.get("SLACK_BOT_TOKEN") and os.environ.get("SLACK_SIGNING_SECRET"):
                config = SlackConfig(
                    bot_token=os.environ["SLACK_BOT_TOKEN"],
                    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
                    app_token=os.environ.get("SLACK_APP_TOKEN"),
                    # Enable enhanced features based on environment
                    enable_analytics=os.environ.get("SLACK_ENABLE_ANALYTICS", "true").lower() == "true",
                    enable_intelligent_routing=os.environ.get("SLACK_ENABLE_ROUTING", "true").lower() == "true",
                    enable_cross_platform=os.environ.get("SLACK_ENABLE_CROSS_PLATFORM", "true").lower() == "true",
                    enable_interactive_workflows=os.environ.get("SLACK_ENABLE_WORKFLOWS", "true").lower() == "true"
                )
                self._enhanced_client = EnhancedSlackClient(config)
                logger.info("Enhanced Slack client initialized successfully")
            else:
                logger.warning("Enhanced Slack client not initialized - missing required environment variables")
        except Exception as e:
            logger.exception(f"Failed to initialize enhanced Slack client: {e}")
            self._enhanced_client = None

    @property
    def client(self) -> WebClient:
        if not self._client:
            self._client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        return self._client
    
    @property
    def enhanced_client(self) -> EnhancedSlackClient | None:
        """Access to enhanced Slack client with advanced features."""
        return self._enhanced_client

    def unsubscribe_all_handlers(self):
        logger.info("[HANDLERS] Clearing all handlers")
        self.registered_handlers.clear()

    async def handle(self, event_data: dict) -> dict:
        """Handle incoming Slack events with enhanced capabilities."""
        logger.info("[HANDLER] Handling Slack event")

        try:
            # Validate and convert to SlackWebhookPayload
            event = SlackWebhookPayload.model_validate(event_data)

            if event.type == "url_verification":
                return {"challenge": event.challenge}
            elif event.type == "event_callback" and event.event:
                return await self._handle_event_callback(event)
            elif event.type == "interactive":
                return await self._handle_interactive_component(event_data)
            else:
                logger.info(f"[HANDLER] No handler found for event type: {event.type}")
                return {"message": "Event handled successfully"}

        except Exception as e:
            logger.exception(f"Error handling Slack event: {e}")
            return {"error": f"Failed to handle event: {e!s}"}
    
    async def _handle_event_callback(self, event: SlackWebhookPayload) -> dict:
        """Handle event callback with enhanced processing."""
        if event.event.type not in self.registered_handlers:
            logger.info(f"[HANDLER] No handler found for event type: {event.event.type}")
            return {"message": "Event handled successfully"}
        
        handler = self.registered_handlers[event.event.type]
        
        # Execute the registered handler
        result = handler(event.event)
        if hasattr(result, "__await__"):
            result = await result
        
        # If enhanced client is available, record analytics
        if self._enhanced_client and self._enhanced_client.analytics_engine:
            await self._record_event_analytics(event.event)
        
        return result or {"message": "Event handled successfully"}
    
    async def _handle_interactive_component(self, payload: dict) -> dict:
        """Handle interactive component interactions."""
        if self._enhanced_client:
            return await self._enhanced_client.handle_interactive_component(payload)
        else:
            logger.warning("Interactive component received but enhanced client not available")
            return {"message": "Interactive component handled"}
    
    async def _record_event_analytics(self, slack_event):
        """Record event for analytics if enhanced client is available."""
        try:
            if self._enhanced_client and self._enhanced_client.analytics_engine:
                # Create notification context for analytics
                context = NotificationContext(
                    event_type=slack_event.type,
                    source_platform="slack",
                    metadata={
                        "user": slack_event.user,
                        "channel": slack_event.channel,
                        "timestamp": slack_event.ts,
                        "text": slack_event.text
                    }
                )
                
                # Record the event
                await self._enhanced_client.analytics_engine.record_notification(
                    event_data={"user_id": slack_event.user, "text": slack_event.text},
                    context=context,
                    responses=[]
                )
        except Exception as e:
            logger.exception(f"Failed to record event analytics: {e}")

    async def send_enhanced_notification(
        self, 
        event_data: dict, 
        context: NotificationContext
    ) -> dict:
        """Send enhanced notification using the enhanced client."""
        if self._enhanced_client:
            return await self._enhanced_client.send_intelligent_notification(event_data, context)
        else:
            # Fallback to basic client
            logger.warning("Enhanced client not available, falling back to basic notification")
            return await self._send_basic_notification(event_data, context)
    
    async def coordinate_workflow(self, workflow_type: str, data: dict) -> dict:
        """Coordinate team workflow using enhanced client."""
        if self._enhanced_client:
            return await self._enhanced_client.coordinate_team_workflow(workflow_type, data)
        else:
            logger.warning("Enhanced client not available, workflow coordination not supported")
            return {"error": "Enhanced features not available"}
    
    async def _send_basic_notification(self, event_data: dict, context: NotificationContext) -> dict:
        """Fallback method for basic notifications."""
        try:
            message = event_data.get("message", "Notification")
            
            responses = []
            for channel in context.target_channels:
                response = self.client.chat_postMessage(
                    channel=channel,
                    text=message,
                    thread_ts=context.thread_ts
                )
                responses.append({"channel": channel, "ts": response["ts"]})
            
            return {"status": "success", "responses": responses}
        except Exception as e:
            logger.exception(f"Failed to send basic notification: {e}")
            return {"status": "error", "error": str(e)}

    def event(self, event_name: str):
        """Decorator for registering a Slack event handler."""
        logger.info(f"[EVENT] Registering handler for {event_name}")

        def register_handler(func):
            # Register the handler with the app's registry
            func_name = func.__qualname__
            logger.info(f"[EVENT] Registering function {func_name} for {event_name}")

            async def new_func(event):
                # Just pass the event, handler can access client via app.slack.client
                return await func(event)

            self.registered_handlers[event_name] = new_func
            return func

        return register_handler
