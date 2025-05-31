"""
Trigger Engine

Core engine for trigger evaluation and execution.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .models import Trigger, TriggerStatus, TriggerType


class TriggerEngine:
    """
    Core engine for trigger evaluation and execution management.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.registered_triggers: Dict[str, Trigger] = {}
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.worker_tasks: List[asyncio.Task] = []
        self.max_workers = 5
    
    async def start(self):
        """Start the trigger engine"""
        if self.running:
            return
        
        self.logger.info("Starting trigger engine")
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        self.logger.info(f"Trigger engine started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop the trigger engine"""
        self.logger.info("Stopping trigger engine")
        self.running = False
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for workers to finish
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        self.worker_tasks.clear()
        self.logger.info("Trigger engine stopped")
    
    def register_trigger(self, trigger: Trigger):
        """Register a trigger with the engine"""
        self.registered_triggers[trigger.id] = trigger
        self.logger.debug(f"Registered trigger: {trigger.id}")
    
    def unregister_trigger(self, trigger_id: str):
        """Unregister a trigger from the engine"""
        if trigger_id in self.registered_triggers:
            del self.registered_triggers[trigger_id]
            self.logger.debug(f"Unregistered trigger: {trigger_id}")
    
    async def evaluate_triggers(self, context: Dict[str, Any]) -> List[Trigger]:
        """
        Evaluate all triggers against a context and return matching triggers
        
        Args:
            context: Evaluation context
            
        Returns:
            List of triggers that should fire
        """
        matching_triggers = []
        
        for trigger in self.registered_triggers.values():
            if trigger.should_trigger(context):
                matching_triggers.append(trigger)
        
        return matching_triggers
    
    async def queue_trigger_execution(self, trigger: Trigger, context: Dict[str, Any]):
        """Queue a trigger for execution"""
        execution_item = {
            'trigger': trigger,
            'context': context,
            'queued_at': datetime.now()
        }
        
        await self.execution_queue.put(execution_item)
        self.logger.debug(f"Queued trigger execution: {trigger.id}")
    
    async def _worker_loop(self, worker_id: str):
        """Worker loop for processing trigger executions"""
        self.logger.debug(f"Started trigger worker: {worker_id}")
        
        while self.running:
            try:
                # Get next execution item
                execution_item = await asyncio.wait_for(
                    self.execution_queue.get(), 
                    timeout=1.0
                )
                
                trigger = execution_item['trigger']
                context = execution_item['context']
                
                self.logger.debug(f"Worker {worker_id} executing trigger: {trigger.id}")
                
                # Execute trigger
                await self._execute_trigger_actions(trigger, context)
                
                # Mark task as done
                self.execution_queue.task_done()
                
            except asyncio.TimeoutError:
                # No work available, continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                # Mark task as done even on error
                try:
                    self.execution_queue.task_done()
                except:
                    pass
        
        self.logger.debug(f"Stopped trigger worker: {worker_id}")
    
    async def _execute_trigger_actions(self, trigger: Trigger, context: Dict[str, Any]):
        """Execute all actions for a trigger"""
        for action in trigger.actions:
            try:
                # Apply delay if specified
                if action.delay:
                    await asyncio.sleep(action.delay.total_seconds())
                
                # Execute action
                await self._execute_action(action, context, trigger)
                
                # Update action state
                action.last_executed = datetime.now()
                action.execution_count += 1
                action.retry_count = 0
                action.last_error = None
                
            except Exception as e:
                self.logger.error(f"Action execution failed for trigger {trigger.id}: {e}")
                action.last_error = str(e)
                
                # Handle retries
                if action.retry_count < action.max_retries:
                    action.retry_count += 1
                    # Schedule retry with exponential backoff
                    delay = min(2 ** action.retry_count, 60)
                    asyncio.create_task(self._retry_action(action, context, trigger, delay))
    
    async def _execute_action(self, action, context: Dict[str, Any], trigger: Trigger):
        """Execute a specific action"""
        # This is a placeholder - actual implementation would depend on action type
        # and would integrate with the orchestration system
        
        action_type = action.action_type
        parameters = action.parameters
        
        self.logger.info(f"Executing {action_type} action for trigger {trigger.id}")
        
        # Resolve parameters
        resolved_params = self._resolve_parameters(parameters, context)
        
        if action_type == 'workflow':
            # This would trigger workflow execution
            self.logger.info(f"Would execute workflow: {resolved_params.get('workflow_id')}")
        elif action_type == 'notification':
            # This would send notifications
            self.logger.info(f"Would send notification: {resolved_params}")
        elif action_type == 'webhook':
            # This would call webhooks
            await self._call_webhook(resolved_params)
        else:
            self.logger.warning(f"Unknown action type: {action_type}")
    
    async def _retry_action(self, action, context: Dict[str, Any], trigger: Trigger, delay: float):
        """Retry a failed action after delay"""
        await asyncio.sleep(delay)
        
        try:
            self.logger.info(f"Retrying action for trigger {trigger.id} (attempt {action.retry_count})")
            await self._execute_action(action, context, trigger)
        except Exception as e:
            self.logger.error(f"Action retry failed for trigger {trigger.id}: {e}")
    
    def _resolve_parameters(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter values with context substitution"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and '${' in value:
                resolved[key] = self._substitute_variables(value, context)
            else:
                resolved[key] = value
        
        return resolved
    
    def _substitute_variables(self, template: str, context: Dict[str, Any]) -> str:
        """Substitute variables in template string"""
        import re
        
        def replace_var(match):
            var_path = match.group(1)
            try:
                value = self._get_nested_value(context, var_path)
                return str(value)
            except:
                return match.group(0)  # Return original if substitution fails
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, template)
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        parts = path.split('.')
        value = data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                raise KeyError(f"Path not found: {path}")
        
        return value
    
    async def _call_webhook(self, parameters: Dict[str, Any]):
        """Call a webhook"""
        import aiohttp
        
        url = parameters.get('url')
        method = parameters.get('method', 'POST')
        headers = parameters.get('headers', {})
        data = parameters.get('data', {})
        timeout = parameters.get('timeout', 30)
        
        if not url:
            raise ValueError("Webhook URL is required")
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.request(method, url, headers=headers, json=data) as response:
                    if response.status >= 400:
                        response_text = await response.text()
                        raise Exception(f"Webhook failed with status {response.status}: {response_text}")
                    
                    self.logger.info(f"Webhook call successful: {url}")
        
        except Exception as e:
            self.logger.error(f"Webhook call failed: {url} - {e}")
            raise
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get execution queue status"""
        return {
            'queue_size': self.execution_queue.qsize(),
            'active_workers': len([t for t in self.worker_tasks if not t.done()]),
            'total_workers': len(self.worker_tasks),
            'registered_triggers': len(self.registered_triggers)
        }

