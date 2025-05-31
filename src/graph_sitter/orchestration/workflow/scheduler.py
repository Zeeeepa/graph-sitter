"""
Workflow Scheduler

Advanced scheduling system with cron support, dependencies, and time-based triggers.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import re


@dataclass
class ScheduledWorkflow:
    """Represents a scheduled workflow"""
    workflow_id: str
    cron_expression: str
    next_run: datetime
    last_run: Optional[datetime] = None
    enabled: bool = True
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


class CronParser:
    """Simple cron expression parser"""
    
    @staticmethod
    def parse_cron(cron_expr: str) -> Dict[str, Any]:
        """
        Parse a cron expression into components
        Format: minute hour day month day_of_week
        """
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 parts: minute hour day month day_of_week")
        
        return {
            'minute': CronParser._parse_field(parts[0], 0, 59),
            'hour': CronParser._parse_field(parts[1], 0, 23),
            'day': CronParser._parse_field(parts[2], 1, 31),
            'month': CronParser._parse_field(parts[3], 1, 12),
            'day_of_week': CronParser._parse_field(parts[4], 0, 6)  # 0 = Sunday
        }
    
    @staticmethod
    def _parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """Parse a single cron field"""
        if field == '*':
            return list(range(min_val, max_val + 1))
        
        values = []
        for part in field.split(','):
            if '/' in part:
                # Step values (e.g., */5, 0-30/5)
                range_part, step = part.split('/')
                step = int(step)
                if range_part == '*':
                    values.extend(range(min_val, max_val + 1, step))
                else:
                    start, end = map(int, range_part.split('-'))
                    values.extend(range(start, end + 1, step))
            elif '-' in part:
                # Range (e.g., 1-5)
                start, end = map(int, part.split('-'))
                values.extend(range(start, end + 1))
            else:
                # Single value
                values.append(int(part))
        
        return sorted(list(set(values)))
    
    @staticmethod
    def next_run_time(cron_expr: str, from_time: datetime = None) -> datetime:
        """Calculate the next run time for a cron expression"""
        if from_time is None:
            from_time = datetime.now()
        
        parsed = CronParser.parse_cron(cron_expr)
        
        # Start from the next minute
        next_time = from_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Find the next valid time
        for _ in range(366 * 24 * 60):  # Max iterations to prevent infinite loop
            if (next_time.minute in parsed['minute'] and
                next_time.hour in parsed['hour'] and
                next_time.day in parsed['day'] and
                next_time.month in parsed['month'] and
                next_time.weekday() + 1 % 7 in parsed['day_of_week']):  # Convert to Sunday=0
                return next_time
            
            next_time += timedelta(minutes=1)
        
        raise ValueError("Could not find next run time for cron expression")


class WorkflowScheduler:
    """
    Advanced workflow scheduler with cron support and dependency management.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.scheduled_workflows: Dict[str, ScheduledWorkflow] = {}
        self.scheduler_task: Optional[asyncio.Task] = None
        self.execution_callbacks: List[Callable] = []
    
    async def start(self):
        """Start the workflow scheduler"""
        if self.running:
            return
        
        self.logger.info("Starting workflow scheduler")
        self.running = True
        
        # Start scheduler loop
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        self.logger.info("Workflow scheduler started")
    
    async def stop(self):
        """Stop the workflow scheduler"""
        self.logger.info("Stopping workflow scheduler")
        self.running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Workflow scheduler stopped")
    
    def schedule_workflow(
        self, 
        workflow_id: str, 
        cron_expression: str,
        context: Dict[str, Any] = None
    ):
        """
        Schedule a workflow with a cron expression
        
        Args:
            workflow_id: ID of workflow to schedule
            cron_expression: Cron expression (minute hour day month day_of_week)
            context: Optional context for workflow execution
        """
        try:
            next_run = CronParser.next_run_time(cron_expression)
            
            scheduled = ScheduledWorkflow(
                workflow_id=workflow_id,
                cron_expression=cron_expression,
                next_run=next_run,
                context=context or {}
            )
            
            self.scheduled_workflows[workflow_id] = scheduled
            self.logger.info(f"Scheduled workflow {workflow_id} with cron '{cron_expression}', next run: {next_run}")
            
        except Exception as e:
            self.logger.error(f"Failed to schedule workflow {workflow_id}: {e}")
            raise
    
    def unschedule_workflow(self, workflow_id: str) -> bool:
        """Remove a workflow from the schedule"""
        if workflow_id in self.scheduled_workflows:
            del self.scheduled_workflows[workflow_id]
            self.logger.info(f"Unscheduled workflow: {workflow_id}")
            return True
        return False
    
    def enable_workflow(self, workflow_id: str) -> bool:
        """Enable a scheduled workflow"""
        if workflow_id in self.scheduled_workflows:
            self.scheduled_workflows[workflow_id].enabled = True
            self.logger.info(f"Enabled scheduled workflow: {workflow_id}")
            return True
        return False
    
    def disable_workflow(self, workflow_id: str) -> bool:
        """Disable a scheduled workflow"""
        if workflow_id in self.scheduled_workflows:
            self.scheduled_workflows[workflow_id].enabled = False
            self.logger.info(f"Disabled scheduled workflow: {workflow_id}")
            return True
        return False
    
    def get_scheduled_workflows(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled workflows"""
        return [
            {
                'workflow_id': sw.workflow_id,
                'cron_expression': sw.cron_expression,
                'next_run': sw.next_run.isoformat(),
                'last_run': sw.last_run.isoformat() if sw.last_run else None,
                'enabled': sw.enabled
            }
            for sw in self.scheduled_workflows.values()
        ]
    
    def add_execution_callback(self, callback: Callable):
        """Add a callback to be called when a scheduled workflow should execute"""
        self.execution_callbacks.append(callback)
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check for workflows that need to run
                for workflow_id, scheduled in self.scheduled_workflows.items():
                    if (scheduled.enabled and 
                        scheduled.next_run <= current_time):
                        
                        # Execute workflow
                        await self._execute_scheduled_workflow(scheduled)
                        
                        # Calculate next run time
                        try:
                            scheduled.next_run = CronParser.next_run_time(
                                scheduled.cron_expression, 
                                current_time
                            )
                            scheduled.last_run = current_time
                        except Exception as e:
                            self.logger.error(f"Failed to calculate next run for {workflow_id}: {e}")
                            scheduled.enabled = False
                
                # Sleep until next check (every minute)
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    async def _execute_scheduled_workflow(self, scheduled: ScheduledWorkflow):
        """Execute a scheduled workflow"""
        self.logger.info(f"Executing scheduled workflow: {scheduled.workflow_id}")
        
        try:
            # Call all execution callbacks
            for callback in self.execution_callbacks:
                try:
                    await callback(scheduled.workflow_id, scheduled.context)
                except Exception as e:
                    self.logger.error(f"Execution callback error: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to execute scheduled workflow {scheduled.workflow_id}: {e}")


# Common cron expressions
COMMON_SCHEDULES = {
    'every_minute': '* * * * *',
    'every_5_minutes': '*/5 * * * *',
    'every_15_minutes': '*/15 * * * *',
    'every_30_minutes': '*/30 * * * *',
    'hourly': '0 * * * *',
    'daily': '0 0 * * *',
    'daily_at_9am': '0 9 * * *',
    'weekly': '0 0 * * 0',  # Sunday at midnight
    'monthly': '0 0 1 * *',  # First day of month at midnight
    'weekdays_9am': '0 9 * * 1-5',  # Monday to Friday at 9 AM
    'weekends': '0 0 * * 0,6',  # Saturday and Sunday at midnight
}

