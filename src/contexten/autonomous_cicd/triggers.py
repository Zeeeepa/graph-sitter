"""
CI/CD Pipeline Triggers

This module provides various triggers for the autonomous CI/CD system,
including GitHub webhooks, Linear integrations, and scheduled triggers.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class TriggerEvent:
    """Event that triggers a CI/CD pipeline"""
    trigger_type: str
    event_type: str
    data: Dict[str, Any]
    timestamp: float
    branch: Optional[str] = None
    changes: List[str] = None


class BaseTrigger(ABC):
    """Base class for CI/CD triggers"""
    
    def __init__(self, config, cicd_system):
        self.config = config
        self.cicd_system = cicd_system
        self.running = False
        
    @abstractmethod
    async def start(self):
        """Start the trigger"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the trigger"""
        pass
    
    async def trigger_pipeline(self, event: TriggerEvent):
        """Trigger a CI/CD pipeline"""
        try:
            logger.info(f"Triggering pipeline for {event.trigger_type} event: {event.event_type}")
            
            # Determine pipeline type based on event
            pipeline_type = self._determine_pipeline_type(event)
            
            # Execute pipeline
            result = await self.cicd_system.execute_pipeline(
                trigger_event=event.data,
                pipeline_type=pipeline_type
            )
            
            logger.info(f"Pipeline {result.pipeline_id} triggered successfully")
            
        except Exception as e:
            logger.error(f"Failed to trigger pipeline: {e}")
    
    def _determine_pipeline_type(self, event: TriggerEvent) -> str:
        """Determine the type of pipeline to run based on the event"""
        if event.event_type in ['push', 'pull_request']:
            return 'full'
        elif event.event_type in ['issue_comment', 'review']:
            return 'analysis'
        elif event.event_type == 'schedule':
            return 'test'
        else:
            return 'analysis'


class GitHubTrigger(BaseTrigger):
    """
    GitHub webhook trigger for CI/CD pipelines
    """
    
    def __init__(self, config, cicd_system):
        super().__init__(config, cicd_system)
        self.webhook_server = None
        
    async def start(self):
        """Start GitHub webhook server"""
        if not self.config.github_token:
            logger.warning("GitHub token not configured, skipping GitHub trigger")
            return
        
        try:
            from fastapi import FastAPI, Request
            import uvicorn
            
            app = FastAPI()
            
            @app.post("/webhook/github")
            async def github_webhook(request: Request):
                return await self._handle_github_webhook(request)
            
            # Start webhook server in background
            config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
            self.webhook_server = uvicorn.Server(config)
            
            # Run server in background task
            asyncio.create_task(self.webhook_server.serve())
            
            self.running = True
            logger.info("GitHub trigger started on port 8080")
            
        except Exception as e:
            logger.error(f"Failed to start GitHub trigger: {e}")
            raise
    
    async def stop(self):
        """Stop GitHub webhook server"""
        if self.webhook_server:
            self.webhook_server.should_exit = True
        self.running = False
        logger.info("GitHub trigger stopped")
    
    async def _handle_github_webhook(self, request):
        """Handle incoming GitHub webhook"""
        try:
            payload = await request.json()
            headers = request.headers
            
            # Verify webhook signature
            if not self._verify_signature(payload, headers):
                return {"error": "Invalid signature"}
            
            # Parse GitHub event
            event_type = headers.get("X-GitHub-Event", "unknown")
            
            if event_type == "push":
                await self._handle_push_event(payload)
            elif event_type == "pull_request":
                await self._handle_pull_request_event(payload)
            elif event_type == "issue_comment":
                await self._handle_comment_event(payload)
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"GitHub webhook error: {e}")
            return {"error": str(e)}
    
    async def _handle_push_event(self, payload: Dict[str, Any]):
        """Handle GitHub push event"""
        branch = payload.get("ref", "").replace("refs/heads/", "")
        commits = payload.get("commits", [])
        
        # Extract changed files
        changes = []
        for commit in commits:
            changes.extend(commit.get("added", []))
            changes.extend(commit.get("modified", []))
        
        # Skip if no relevant changes
        if not changes or branch in self.config.protected_branches:
            return
        
        event = TriggerEvent(
            trigger_type="github",
            event_type="push",
            data=payload,
            timestamp=time.time(),
            branch=branch,
            changes=list(set(changes))  # Remove duplicates
        )
        
        await self.trigger_pipeline(event)
    
    async def _handle_pull_request_event(self, payload: Dict[str, Any]):
        """Handle GitHub pull request event"""
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        
        if action not in ["opened", "synchronize", "reopened"]:
            return
        
        branch = pr.get("head", {}).get("ref")
        
        event = TriggerEvent(
            trigger_type="github",
            event_type="pull_request",
            data=payload,
            timestamp=time.time(),
            branch=branch,
            changes=[]  # Would need to fetch PR files
        )
        
        await self.trigger_pipeline(event)
    
    async def _handle_comment_event(self, payload: Dict[str, Any]):
        """Handle GitHub comment event"""
        comment = payload.get("comment", {}).get("body", "")
        
        # Check for CI/CD commands in comments
        if "/run-tests" in comment or "/analyze" in comment:
            event = TriggerEvent(
                trigger_type="github",
                event_type="issue_comment",
                data=payload,
                timestamp=time.time(),
                branch=None,
                changes=[]
            )
            
            await self.trigger_pipeline(event)
    
    def _verify_signature(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Verify GitHub webhook signature"""
        if not self.config.github_webhook_secret:
            return True  # Skip verification if no secret configured
        
        # Implementation would verify HMAC signature
        # For now, return True
        return True


class LinearTrigger(BaseTrigger):
    """
    Linear webhook trigger for CI/CD pipelines
    """
    
    def __init__(self, config, cicd_system):
        super().__init__(config, cicd_system)
        
    async def start(self):
        """Start Linear trigger"""
        if not self.config.linear_api_key:
            logger.warning("Linear API key not configured, skipping Linear trigger")
            return
        
        self.running = True
        logger.info("Linear trigger started")
    
    async def stop(self):
        """Stop Linear trigger"""
        self.running = False
        logger.info("Linear trigger stopped")
    
    async def handle_linear_event(self, payload: Dict[str, Any]):
        """Handle Linear webhook event"""
        try:
            event_type = payload.get("type", "unknown")
            
            if event_type == "Issue":
                await self._handle_issue_event(payload)
            elif event_type == "Comment":
                await self._handle_comment_event(payload)
            
        except Exception as e:
            logger.error(f"Linear event error: {e}")
    
    async def _handle_issue_event(self, payload: Dict[str, Any]):
        """Handle Linear issue event"""
        action = payload.get("action")
        issue = payload.get("data", {})
        
        if action == "create" and "ci/cd" in issue.get("title", "").lower():
            event = TriggerEvent(
                trigger_type="linear",
                event_type="issue",
                data=payload,
                timestamp=time.time(),
                branch=None,
                changes=[]
            )
            
            await self.trigger_pipeline(event)
    
    async def _handle_comment_event(self, payload: Dict[str, Any]):
        """Handle Linear comment event"""
        comment = payload.get("data", {}).get("body", "")
        
        if "/deploy" in comment or "/test" in comment:
            event = TriggerEvent(
                trigger_type="linear",
                event_type="comment",
                data=payload,
                timestamp=time.time(),
                branch=None,
                changes=[]
            )
            
            await self.trigger_pipeline(event)


class ScheduledTrigger(BaseTrigger):
    """
    Scheduled trigger for periodic CI/CD operations
    """
    
    def __init__(self, config, cicd_system):
        super().__init__(config, cicd_system)
        self.scheduler_task = None
        
    async def start(self):
        """Start scheduled trigger"""
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduled trigger started")
    
    async def stop(self):
        """Stop scheduled trigger"""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
        logger.info("Scheduled trigger stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = time.time()
                
                # Run daily health check at 2 AM
                if self._should_run_daily_check(current_time):
                    await self._trigger_health_check()
                
                # Run weekly full analysis on Sundays at 3 AM
                if self._should_run_weekly_analysis(current_time):
                    await self._trigger_weekly_analysis()
                
                # Sleep for 1 hour before next check
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(300)  # Sleep 5 minutes on error
    
    def _should_run_daily_check(self, current_time: float) -> bool:
        """Check if daily health check should run"""
        import datetime
        dt = datetime.datetime.fromtimestamp(current_time)
        return dt.hour == 2 and dt.minute < 5  # Run at 2 AM
    
    def _should_run_weekly_analysis(self, current_time: float) -> bool:
        """Check if weekly analysis should run"""
        import datetime
        dt = datetime.datetime.fromtimestamp(current_time)
        return dt.weekday() == 6 and dt.hour == 3 and dt.minute < 5  # Sunday 3 AM
    
    async def _trigger_health_check(self):
        """Trigger daily health check"""
        event = TriggerEvent(
            trigger_type="scheduled",
            event_type="health_check",
            data={"type": "daily_health_check"},
            timestamp=time.time(),
            branch=self.config.target_branch,
            changes=[]
        )
        
        await self.trigger_pipeline(event)
    
    async def _trigger_weekly_analysis(self):
        """Trigger weekly full analysis"""
        event = TriggerEvent(
            trigger_type="scheduled",
            event_type="weekly_analysis",
            data={"type": "weekly_full_analysis"},
            timestamp=time.time(),
            branch=self.config.target_branch,
            changes=[]
        )
        
        await self.trigger_pipeline(event)

