"""Webhook management API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel

from ...models.webhook import WebhookConfiguration, WebhookEvent, WebhookEventType, WebhookDelivery
from ...services.webhook_service import WebhookService
from ...utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class WebhookConfigRequest(BaseModel):
    """Request model for webhook configuration."""
    webhook_url: str
    events: List[WebhookEventType]
    secret: Optional[str] = None
    active: bool = True


class WebhookEventResponse(BaseModel):
    """Response model for webhook events."""
    events: List[WebhookEvent]
    total: int
    page: int
    per_page: int


def get_webhook_service(request: Request) -> WebhookService:
    """Dependency to get webhook service."""
    if not hasattr(request.app.state, "webhook_service"):
        raise HTTPException(status_code=503, detail="Webhook service not available")
    return request.app.state.webhook_service


@router.post("/{project_id}/configure", response_model=WebhookConfiguration)
async def configure_webhook(
    project_id: str,
    config_request: WebhookConfigRequest,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Configure webhook for a project."""
    try:
        config = await webhook_service.register_webhook(
            project_id=project_id,
            webhook_url=config_request.webhook_url,
            events=config_request.events,
            secret=config_request.secret,
        )
        
        logger.info(f"Configured webhook for project {project_id}")
        return config
        
    except Exception as e:
        logger.error(f"Error configuring webhook for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure webhook")


@router.get("/{project_id}/config", response_model=WebhookConfiguration)
async def get_webhook_config(
    project_id: str,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Get webhook configuration for a project."""
    try:
        config = await webhook_service.get_webhook_config(project_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Webhook configuration not found")
            
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching webhook config for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch webhook configuration")


@router.put("/{project_id}/config", response_model=WebhookConfiguration)
async def update_webhook_config(
    project_id: str,
    config_request: WebhookConfigRequest,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Update webhook configuration for a project."""
    try:
        config = await webhook_service.update_webhook_config(
            project_id=project_id,
            webhook_url=config_request.webhook_url,
            events=config_request.events,
            active=config_request.active,
        )
        
        if not config:
            raise HTTPException(status_code=404, detail="Webhook configuration not found")
            
        logger.info(f"Updated webhook config for project {project_id}")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating webhook config for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update webhook configuration")


@router.delete("/{project_id}/config")
async def delete_webhook_config(
    project_id: str,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Delete webhook configuration for a project."""
    try:
        success = await webhook_service.unregister_webhook(project_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Webhook configuration not found")
            
        logger.info(f"Deleted webhook config for project {project_id}")
        return {"message": "Webhook configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook config for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete webhook configuration")


@router.post("/github", status_code=200)
async def handle_github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Handle incoming GitHub webhook events."""
    try:
        # Get request body
        payload = await request.json()
        
        # Prepare headers
        headers = {
            "X-GitHub-Event": x_github_event,
            "X-Hub-Signature-256": x_hub_signature_256,
        }
        
        # Process webhook
        event = await webhook_service.process_github_webhook(payload, headers)
        
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
            
        logger.info(f"Processed GitHub webhook event: {event.id}")
        return {"message": "Webhook processed successfully", "event_id": event.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing GitHub webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/linear", status_code=200)
async def handle_linear_webhook(
    request: Request,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Handle incoming Linear webhook events."""
    try:
        # Get request body
        payload = await request.json()
        
        # Get headers
        headers = dict(request.headers)
        
        # Process webhook
        event = await webhook_service.process_linear_webhook(payload, headers)
        
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
            
        logger.info(f"Processed Linear webhook event: {event.id}")
        return {"message": "Webhook processed successfully", "event_id": event.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Linear webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.get("/events", response_model=WebhookEventResponse)
async def get_webhook_events(
    project_id: Optional[str] = None,
    event_type: Optional[WebhookEventType] = None,
    page: int = 1,
    per_page: int = 50,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Get webhook events with optional filtering."""
    try:
        events = await webhook_service.get_webhook_events(
            project_id=project_id,
            event_type=event_type,
            limit=per_page * page,  # Simple pagination
        )
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_events = events[start_idx:end_idx]
        
        return WebhookEventResponse(
            events=paginated_events,
            total=len(events),
            page=page,
            per_page=per_page,
        )
        
    except Exception as e:
        logger.error(f"Error fetching webhook events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch webhook events")


@router.get("/events/{event_id}", response_model=WebhookEvent)
async def get_webhook_event(
    event_id: str,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Get a specific webhook event by ID."""
    try:
        # In a real implementation, this would query the database
        # For now, return a not found error
        raise HTTPException(status_code=404, detail="Event not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching webhook event {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch webhook event")


@router.post("/test/{project_id}")
async def test_webhook(
    project_id: str,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Test webhook configuration by sending a test event."""
    try:
        config = await webhook_service.get_webhook_config(project_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Webhook configuration not found")
            
        # Create test event
        from datetime import datetime
        test_event = WebhookEvent(
            id=f"test_{datetime.utcnow().timestamp()}",
            event_type=WebhookEventType.PUSH,
            action="test",
            repository_id=project_id,
            repository_name=f"test/{project_id}",
            sender="dashboard",
            payload={
                "test": True,
                "message": "This is a test webhook event",
                "timestamp": datetime.utcnow().isoformat(),
            },
            received_at=datetime.utcnow(),
        )
        
        # Deliver webhook
        delivery = await webhook_service.deliver_webhook(config, test_event)
        
        return {
            "message": "Test webhook sent",
            "delivery_id": delivery.id,
            "success": delivery.success,
            "status_code": delivery.status_code,
            "response_time_ms": delivery.response_time_ms,
            "error_message": delivery.error_message,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing webhook for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to test webhook")


@router.get("/stats/overview")
async def get_webhook_stats(
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Get webhook statistics overview."""
    try:
        # In a real implementation, this would aggregate data from the database
        stats = {
            "total_configurations": len(webhook_service.webhook_configs),
            "active_configurations": len([
                c for c in webhook_service.webhook_configs.values() 
                if c.active
            ]),
            "total_events_processed": 0,  # Would come from database
            "successful_deliveries": 0,  # Would come from database
            "failed_deliveries": 0,  # Would come from database
            "average_response_time_ms": 0,  # Would come from database
            "event_types_distribution": {},  # Would come from database
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching webhook stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch webhook statistics")


@router.get("/deliveries/{project_id}")
async def get_webhook_deliveries(
    project_id: str,
    page: int = 1,
    per_page: int = 50,
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    """Get webhook delivery history for a project."""
    try:
        # In a real implementation, this would query delivery history from database
        deliveries = []  # Would fetch from database
        
        return {
            "deliveries": deliveries,
            "total": len(deliveries),
            "page": page,
            "per_page": per_page,
        }
        
    except Exception as e:
        logger.error(f"Error fetching webhook deliveries for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch webhook deliveries")

