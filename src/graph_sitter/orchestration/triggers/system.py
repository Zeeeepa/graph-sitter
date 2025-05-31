"""
Automated Trigger System

Main system for managing and executing automated triggers.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta

from .models import Trigger, TriggerStatus, TriggerType, TriggerAction, COMMON_TRIGGERS
from .engine import TriggerEngine


class AutomatedTriggerSystem:
    """
    Automated trigger system that monitors events and executes workflows
    based on configurable triggers and conditions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Storage
        self.triggers: Dict[str, Trigger] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Components
        self.trigger_engine = TriggerEngine()
        
        # State
        self.running = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.workflow_callbacks: List[Callable] = []
        self.notification_callbacks: List[Callable] = []
        
        # Load common triggers
        self._load_common_triggers()
    
    async def start(self):
        """Start the trigger system"""
        if self.running:
            return
        
        self.logger.info("Starting automated trigger system")
        self.running = True
        
        await self.trigger_engine.start()
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Automated trigger system started")
    
    async def stop(self):
        """Stop the trigger system"""
        self.logger.info("Stopping automated trigger system")
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        await self.trigger_engine.stop()
        
        self.logger.info("Automated trigger system stopped")
    
    def _load_common_triggers(self):
        """Load common trigger templates"""
        for trigger in COMMON_TRIGGERS.values():
            self.triggers[trigger.id] = trigger
        
        self.logger.info(f"Loaded {len(COMMON_TRIGGERS)} common triggers")
    
    def register_trigger(self, trigger: Trigger) -> bool:
        """
        Register a new trigger
        
        Args:
            trigger: Trigger to register
            
        Returns:
            True if successful
        """
        try:
            # Validate trigger
            if not trigger.name:
                raise ValueError("Trigger name is required")
            
            if not trigger.actions:
                raise ValueError("Trigger must have at least one action")
            
            # Register with engine
            self.trigger_engine.register_trigger(trigger)
            
            # Store trigger
            self.triggers[trigger.id] = trigger
            
            self.logger.info(f"Registered trigger: {trigger.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register trigger {trigger.id}: {e}")
            return False
    
    def unregister_trigger(self, trigger_id: str) -> bool:
        """Remove a trigger"""
        if trigger_id in self.triggers:
            self.trigger_engine.unregister_trigger(trigger_id)
            del self.triggers[trigger_id]
            self.logger.info(f"Unregistered trigger: {trigger_id}")
            return True
        return False
    
    def enable_trigger(self, trigger_id: str) -> bool:
        """Enable a trigger"""
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger.status = TriggerStatus.ACTIVE
            self.logger.info(f"Enabled trigger: {trigger_id}")
            return True
        return False
    
    def disable_trigger(self, trigger_id: str) -> bool:
        """Disable a trigger"""
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger.status = TriggerStatus.DISABLED
            self.logger.info(f"Disabled trigger: {trigger_id}")
            return True
        return False
    
    async def check_triggers(
        self, 
        platform: str, 
        event: Dict[str, Any],
        correlated_events: List[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Check triggers for an event and return triggered workflows
        
        Args:
            platform: Source platform
            event: Event data
            correlated_events: Related events from correlation
            
        Returns:
            List of workflow configurations to execute
        """
        triggered_workflows = []
        
        # Build context for trigger evaluation
        context = {
            'platform': platform,
            'event': event,
            'correlated_events': correlated_events or [],
            'timestamp': datetime.now()
        }
        
        # Check each trigger
        for trigger in self.triggers.values():
            if trigger.trigger_type == TriggerType.EVENT and trigger.should_trigger(context):
                try:
                    # Execute trigger actions
                    workflows = await self._execute_trigger(trigger, context)
                    triggered_workflows.extend(workflows)
                    
                    # Update trigger state
                    trigger.last_triggered = datetime.now()
                    trigger.execution_count += 1
                    
                    # Record execution
                    self._record_execution(trigger, context, True)
                    
                except Exception as e:
                    self.logger.error(f"Error executing trigger {trigger.id}: {e}")
                    trigger.status = TriggerStatus.ERROR
                    self._record_execution(trigger, context, False, str(e))
        
        return triggered_workflows
    
    async def _execute_trigger(self, trigger: Trigger, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a trigger's actions"""
        workflows = []
        
        self.logger.info(f"Executing trigger: {trigger.id}")
        
        for action in trigger.actions:
            try:
                # Apply delay if specified
                if action.delay:
                    await asyncio.sleep(action.delay.total_seconds())
                
                # Resolve parameters
                resolved_params = self._resolve_action_parameters(action.parameters, context)
                
                # Execute action based on type
                if action.action_type == 'workflow':
                    workflow_config = {
                        'workflow_id': resolved_params.get('workflow_id'),
                        'context': resolved_params
                    }
                    workflows.append(workflow_config)
                    
                    # Notify workflow callbacks
                    for callback in self.workflow_callbacks:
                        try:
                            await callback(workflow_config)
                        except Exception as e:
                            self.logger.error(f"Workflow callback error: {e}")
                
                elif action.action_type == 'notification':
                    # Notify notification callbacks
                    for callback in self.notification_callbacks:
                        try:
                            await callback(resolved_params)
                        except Exception as e:
                            self.logger.error(f"Notification callback error: {e}")
                
                elif action.action_type == 'webhook':
                    await self._execute_webhook_action(resolved_params)
                
                # Update action state
                action.last_executed = datetime.now()
                action.execution_count += 1
                action.retry_count = 0  # Reset on success
                
            except Exception as e:
                self.logger.error(f"Action execution failed: {e}")
                action.last_error = str(e)
                
                # Retry logic
                if action.retry_count < action.max_retries:
                    action.retry_count += 1
                    # Schedule retry (simplified - could be more sophisticated)
                    asyncio.create_task(self._retry_action(action, context, trigger))
        
        return workflows
    
    async def _retry_action(self, action: TriggerAction, context: Dict[str, Any], trigger: Trigger):
        """Retry a failed action"""
        delay = min(2 ** action.retry_count, 60)  # Exponential backoff, max 60s
        await asyncio.sleep(delay)
        
        try:
            self.logger.info(f"Retrying action for trigger {trigger.id} (attempt {action.retry_count})")
            await self._execute_trigger(trigger, context)
        except Exception as e:
            self.logger.error(f"Action retry failed: {e}")
    
    def _resolve_action_parameters(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter values with variable substitution"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and '${' in value:
                # Variable substitution
                resolved_value = self._substitute_variables(value, context)
                resolved[key] = resolved_value
            else:
                resolved[key] = value
        
        return resolved
    
    def _substitute_variables(self, template: str, context: Dict[str, Any]) -> str:
        """Substitute variables in a template string"""
        import re
        
        def replace_var(match):
            var_path = match.group(1)
            try:
                return str(self._get_context_value(var_path, context))
            except:
                return match.group(0)  # Return original if substitution fails
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, template)
    
    def _get_context_value(self, path: str, context: Dict[str, Any]) -> Any:
        """Get a value from context using dot notation"""
        parts = path.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                raise KeyError(f"Path not found: {path}")
        
        return value
    
    async def _execute_webhook_action(self, parameters: Dict[str, Any]):
        """Execute a webhook action"""
        import aiohttp
        
        url = parameters.get('url')
        method = parameters.get('method', 'POST')
        headers = parameters.get('headers', {})
        data = parameters.get('data', {})
        
        if not url:
            raise ValueError("Webhook URL is required")
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                if response.status >= 400:
                    raise Exception(f"Webhook failed with status {response.status}")
    
    def _record_execution(self, trigger: Trigger, context: Dict[str, Any], success: bool, error: str = None):
        """Record trigger execution for history and metrics"""
        execution_record = {
            'trigger_id': trigger.id,
            'trigger_name': trigger.name,
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'error': error,
            'context': {
                'platform': context.get('platform'),
                'event_type': context.get('event', {}).get('event_type'),
                'event_id': context.get('event', {}).get('id')
            }
        }
        
        self.execution_history.append(execution_record)
        
        # Keep only recent history (last 1000 executions)
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def add_workflow_callback(self, callback: Callable):
        """Add a callback for workflow execution"""
        self.workflow_callbacks.append(callback)
    
    def add_notification_callback(self, callback: Callable):
        """Add a callback for notifications"""
        self.notification_callbacks.append(callback)
    
    def get_triggers(self) -> List[Dict[str, Any]]:
        """Get list of all triggers"""
        return [
            {
                'id': trigger.id,
                'name': trigger.name,
                'description': trigger.description,
                'type': trigger.trigger_type.value,
                'status': trigger.status.value,
                'execution_count': trigger.execution_count,
                'last_triggered': trigger.last_triggered.isoformat() if trigger.last_triggered else None,
                'created_at': trigger.created_at.isoformat(),
                'tags': trigger.tags
            }
            for trigger in self.triggers.values()
        ]
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        return sorted(
            self.execution_history, 
            key=lambda x: x['timestamp'], 
            reverse=True
        )[:limit]
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get trigger system metrics"""
        total_triggers = len(self.triggers)
        active_triggers = len([t for t in self.triggers.values() if t.status == TriggerStatus.ACTIVE])
        
        # Execution statistics
        total_executions = len(self.execution_history)
        successful_executions = len([e for e in self.execution_history if e['success']])
        
        # Recent activity (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        recent_executions = [
            e for e in self.execution_history 
            if datetime.fromisoformat(e['timestamp']) >= cutoff
        ]
        
        return {
            'total_triggers': total_triggers,
            'active_triggers': active_triggers,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': successful_executions / total_executions if total_executions > 0 else 0,
            'recent_executions_24h': len(recent_executions),
            'trigger_types': {
                trigger_type.value: len([
                    t for t in self.triggers.values() 
                    if t.trigger_type == trigger_type
                ])
                for trigger_type in TriggerType
            }
        }
    
    async def _monitoring_loop(self):
        """Background monitoring and maintenance"""
        while self.running:
            try:
                # Check for scheduled triggers
                await self._check_scheduled_triggers()
                
                # Clean up old execution history
                cutoff = datetime.now() - timedelta(days=7)
                old_count = len(self.execution_history)
                self.execution_history = [
                    e for e in self.execution_history
                    if datetime.fromisoformat(e['timestamp']) >= cutoff
                ]
                
                if len(self.execution_history) < old_count:
                    self.logger.debug(f"Cleaned up {old_count - len(self.execution_history)} old execution records")
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _check_scheduled_triggers(self):
        """Check and execute scheduled triggers"""
        now = datetime.now()
        
        for trigger in self.triggers.values():
            if (trigger.trigger_type == TriggerType.SCHEDULE and 
                trigger.status == TriggerStatus.ACTIVE and
                trigger.cron_expression):
                
                # Check if it's time to execute (simplified cron check)
                if self._should_execute_scheduled_trigger(trigger, now):
                    context = {
                        'platform': 'scheduler',
                        'event': {
                            'event_type': 'schedule.triggered',
                            'trigger_id': trigger.id
                        },
                        'timestamp': now
                    }
                    
                    try:
                        await self._execute_trigger(trigger, context)
                        trigger.last_triggered = now
                        trigger.execution_count += 1
                        self._record_execution(trigger, context, True)
                    except Exception as e:
                        self.logger.error(f"Scheduled trigger execution failed: {e}")
                        self._record_execution(trigger, context, False, str(e))
    
    def _should_execute_scheduled_trigger(self, trigger: Trigger, now: datetime) -> bool:
        """Check if a scheduled trigger should execute (simplified cron logic)"""
        # This is a simplified implementation
        # In a production system, you'd want a proper cron parser
        
        if not trigger.last_triggered:
            return True  # First execution
        
        # For now, just check if it's been more than an hour since last execution
        # This would be replaced with proper cron evaluation
        return now - trigger.last_triggered > timedelta(hours=1)

