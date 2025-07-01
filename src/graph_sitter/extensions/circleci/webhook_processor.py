"""
CircleCI webhook processor
"""

import json
import hmac
import hashlib
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Awaitable
from dataclasses import dataclass, field

from .config import CircleCIIntegrationConfig
from .types import (
    CircleCIEventType,
    BuildStatus,
    CircleCIEvent,
    WorkflowEvent,
    JobEvent,
    WebhookResult,
    WebhookStats
)


class WebhookValidationError(Exception):
    """Webhook validation error"""
    pass


class WebhookProcessingError(Exception):
    """Webhook processing error"""
    pass


@dataclass
class EventHandler:
    """Event handler configuration"""
    handler: Callable[[CircleCIEvent], Awaitable[None]]
    name: str
    event_type: Optional[CircleCIEventType] = None
    priority: int = 0
    enabled: bool = True


@dataclass
class WebhookProcessor:
    """CircleCI webhook processor"""
    config: CircleCIIntegrationConfig
    handlers: List[EventHandler] = field(default_factory=list)
    stats: WebhookStats = field(default_factory=WebhookStats)
    _queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue())
    _recent_events: List[Dict[str, Any]] = field(default_factory=list)
    _is_running: bool = False
    _processing_task: Optional[asyncio.Task] = None

    def __post_init__(self):
        """Initialize processor"""
        self._logger = logging.getLogger(__name__)

    @property
    def is_running(self) -> bool:
        """Check if processor is running"""
        return self._is_running

    async def start(self):
        """Start webhook processor"""
        if self._is_running:
            return

        self._is_running = True
        self._processing_task = asyncio.create_task(self._process_queue())
        self._logger.info("Webhook processor started")

    async def stop(self):
        """Stop webhook processor"""
        if not self._is_running:
            return

        self._is_running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        self._logger.info("Webhook processor stopped")

    def register_handler(
        self,
        handler: Callable[[CircleCIEvent], Awaitable[None]],
        name: str,
        event_type: Optional[CircleCIEventType] = None,
        priority: int = 0
    ):
        """Register event handler"""
        self.handlers.append(
            EventHandler(
                handler=handler,
                name=name,
                event_type=event_type,
                priority=priority
            )
        )
        self.handlers.sort(key=lambda h: h.priority, reverse=True)
        self._logger.debug(f"Registered handler: {name}")

    def unregister_handler(self, name: str) -> bool:
        """Unregister event handler"""
        initial_count = len(self.handlers)
        self.handlers = [h for h in self.handlers if h.name != name]
        return len(self.handlers) < initial_count

    def _validate_signature(self, headers: Dict[str, str], body: str) -> bool:
        """Validate webhook signature"""
        if not self.config.webhook.validate_signatures:
            return True

        signature_header = headers.get("circleci-signature")
        if not signature_header:
            raise WebhookValidationError("Missing signature header")

        if not signature_header.startswith("sha256="):
            raise WebhookValidationError("Invalid signature format")

        signature = signature_header.replace("sha256=", "")
        expected = hmac.new(
            self.config.webhook.webhook_secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

    def _parse_event(self, payload: Dict[str, Any]) -> CircleCIEvent:
        """Parse webhook payload into event object"""
        event_type = payload.get("type")
        if not event_type:
            raise WebhookProcessingError("Missing event type")

        try:
            event_type = CircleCIEventType(event_type)
        except ValueError:
            raise WebhookProcessingError(f"Unknown event type: {event_type}")

        event_id = payload.get("id")
        if not event_id:
            raise WebhookProcessingError("Missing event ID")

        happened_at = datetime.fromisoformat(
            payload.get("happened_at", "").replace("Z", "+00:00")
        )

        if event_type == CircleCIEventType.WORKFLOW_COMPLETED:
            workflow = payload.get("workflow", {})
            return WorkflowEvent(
                type=event_type,
                id=event_id,
                happened_at=happened_at,
                raw_payload=payload,
                workflow_id=workflow.get("id"),
                workflow_name=workflow.get("name"),
                project_slug=workflow.get("project_slug"),
                status=BuildStatus(workflow.get("status", "unknown")),
                started_at=datetime.fromisoformat(
                    workflow.get("started_at", "").replace("Z", "+00:00")
                ),
                stopped_at=datetime.fromisoformat(
                    workflow.get("stopped_at", "").replace("Z", "+00:00")
                ),
                pipeline_id=workflow.get("pipeline_id"),
                pipeline_number=workflow.get("pipeline_number"),
                branch=payload.get("pipeline", {}).get("vcs", {}).get("branch"),
                revision=payload.get("pipeline", {}).get("vcs", {}).get("revision")
            )
        elif event_type == CircleCIEventType.JOB_COMPLETED:
            job = payload.get("job", {})
            return JobEvent(
                type=event_type,
                id=event_id,
                happened_at=happened_at,
                raw_payload=payload,
                job_id=job.get("id"),
                job_name=job.get("name"),
                project_slug=job.get("project_slug"),
                status=BuildStatus(job.get("status", "unknown")),
                started_at=datetime.fromisoformat(
                    job.get("started_at", "").replace("Z", "+00:00")
                ),
                stopped_at=datetime.fromisoformat(
                    job.get("stopped_at", "").replace("Z", "+00:00")
                ),
                web_url=job.get("web_url"),
                exit_code=job.get("exit_code"),
                branch=payload.get("pipeline", {}).get("vcs", {}).get("branch"),
                revision=payload.get("pipeline", {}).get("vcs", {}).get("revision")
            )
        else:
            return CircleCIEvent(
                type=event_type,
                id=event_id,
                happened_at=happened_at,
                raw_payload=payload
            )

    async def process_webhook(
        self,
        headers: Dict[str, str],
        body: str
    ) -> WebhookResult:
        """Process incoming webhook"""
        start_time = datetime.now()
        self.stats.requests_total += 1

        try:
            # Validate signature
            if not self._validate_signature(headers, body):
                raise WebhookValidationError("Invalid webhook signature")

            # Parse payload
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                raise WebhookProcessingError("Invalid JSON payload")

            # Parse event
            event = self._parse_event(payload)

            # Skip ping events if configured
            if (
                event.type == CircleCIEventType.PING
                and self.config.webhook.ignore_ping_events
            ):
                self.stats.ping_events += 1
                return WebhookResult(
                    success=True,
                    event_type=event.type,
                    event_id=event.id
                )

            # Add to processing queue
            if self._queue.qsize() >= self.config.webhook.max_queue_size:
                raise WebhookProcessingError("Webhook queue full")

            await self._queue.put(event)
            self.stats.requests_successful += 1

            # Update stats
            if event.type == CircleCIEventType.WORKFLOW_COMPLETED:
                self.stats.workflow_events += 1
            elif event.type == CircleCIEventType.JOB_COMPLETED:
                self.stats.job_events += 1

            # Store recent event
            self._recent_events.append({
                "id": event.id,
                "type": event.type,
                "timestamp": event.happened_at,
                "status": "queued"
            })
            if len(self._recent_events) > 100:
                self._recent_events.pop(0)

            processing_time = (datetime.now() - start_time).total_seconds()
            return WebhookResult(
                success=True,
                event_type=event.type,
                event_id=event.id,
                processing_time=processing_time
            )

        except (WebhookValidationError, WebhookProcessingError) as e:
            self.stats.requests_failed += 1
            self._logger.error(f"Webhook processing error: {str(e)}")
            return WebhookResult(
                success=False,
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            self.stats.requests_failed += 1
            self._logger.exception("Unexpected error processing webhook")
            return WebhookResult(
                success=False,
                error=f"Internal error: {str(e)}",
                processing_time=(datetime.now() - start_time).total_seconds()
            )

    async def _process_queue(self):
        """Process events from queue"""
        while self._is_running:
            try:
                event = await self._queue.get()
                start_time = datetime.now()

                try:
                    # Execute handlers
                    for handler in self.handlers:
                        if (
                            handler.enabled
                            and (
                                handler.event_type is None
                                or handler.event_type == event.type
                            )
                        ):
                            try:
                                await handler.handler(event)
                            except Exception as e:
                                self._logger.error(
                                    f"Handler {handler.name} failed: {str(e)}"
                                )
                                self.stats.events_failed += 1

                    self.stats.events_processed += 1
                    processing_time = (
                        datetime.now() - start_time
                    ).total_seconds()
                    self.stats.processing_time_total += processing_time

                    # Update recent event status
                    for recent in self._recent_events:
                        if recent["id"] == event.id:
                            recent["status"] = "processed"
                            recent["processing_time"] = processing_time
                            break

                except Exception as e:
                    self._logger.exception(
                        f"Error processing event {event.id}: {str(e)}"
                    )
                    self.stats.events_failed += 1

                    # Update recent event status
                    for recent in self._recent_events:
                        if recent["id"] == event.id:
                            recent["status"] = "failed"
                            recent["error"] = str(e)
                            break

                finally:
                    self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.exception(f"Queue processing error: {str(e)}")

    def get_stats(self) -> WebhookStats:
        """Get webhook processing statistics"""
        return self.stats

    def get_queue_info(self) -> Dict[str, Any]:
        """Get queue information"""
        return {
            "queue_size": self._queue.qsize(),
            "max_queue_size": self.config.webhook.max_queue_size,
            "is_running": self._is_running,
            "handlers_registered": len(self.handlers)
        }

    def get_recent_events(self) -> List[Dict[str, Any]]:
        """Get recent events"""
        return self._recent_events.copy()

    def get_handlers(self) -> List[Dict[str, Any]]:
        """Get registered handlers"""
        return [
            {
                "name": h.name,
                "event_type": h.event_type.value if h.event_type else "all",
                "priority": h.priority,
                "enabled": h.enabled
            }
            for h in self.handlers
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        queue_info = self.get_queue_info()
        stats = self.get_stats()

        return {
            "healthy": self._is_running and queue_info["queue_size"] < queue_info["max_queue_size"],
            "queue_size": queue_info["queue_size"],
            "handlers_count": len(self.handlers),
            "stats": {
                "success_rate": stats.success_rate,
                "events_processed": stats.events_processed,
                "events_failed": stats.events_failed
            }
        }

