#!/usr/bin/env python3
"""
Prefect Flow Module
Handles flow definitions and orchestration within the Prefect workflow system.
"""

from typing import Dict, List, Any, Optional, Callable
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PrefectFlow:
    """Prefect flow wrapper."""
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.kwargs = kwargs
        self.tasks: List[Any] = []
        self.dependencies: Dict[str, List[str]] = {}
        self.retries = kwargs.get('retries', 0)
        self.timeout = kwargs.get('timeout', None)
        
    def add_task(self, task: Any, dependencies: Optional[List[str]] = None) -> None:
        """Add a task to the flow."""
        self.tasks.append(task)
        if dependencies:
            self.dependencies[task.name] = dependencies
            
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the flow."""
        logger.info(f"Running flow: {self.name}")
        
        start_time = datetime.now()
        results = {}
        
        try:
            # Execute tasks in dependency order
            executed_tasks = set()
            
            while len(executed_tasks) < len(self.tasks):
                for task in self.tasks:
                    if task.name in executed_tasks:
                        continue
                        
                    # Check if dependencies are satisfied
                    task_deps = self.dependencies.get(task.name, [])
                    if all(dep in executed_tasks for dep in task_deps):
                        # Execute task
                        logger.info(f"Executing task: {task.name}")
                        result = await task.run(**kwargs)
                        results[task.name] = result
                        executed_tasks.add(task.name)
                        
                # Prevent infinite loop
                if not any(task.name not in executed_tasks for task in self.tasks):
                    break
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            flow_result = {
                "flow_name": self.name,
                "status": "completed",
                "duration": duration,
                "task_results": results,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
            logger.info(f"Flow completed: {self.name} in {duration:.2f}s")
            return flow_result
            
        except Exception as e:
            logger.error(f"Flow failed: {self.name} - {e}")
            return {
                "flow_name": self.name,
                "status": "failed",
                "error": str(e),
                "task_results": results
            }


def flow(name: Optional[str] = None, **kwargs):
    """Decorator to create a Prefect flow."""
    def decorator(func):
        flow_name = name or func.__name__
        return PrefectFlow(flow_name, **kwargs)
    return decorator


class FlowRunner:
    """Flow execution runner."""
    
    def __init__(self):
        self.running_flows: Dict[str, Any] = {}
        
    async def execute_flow(self, flow: PrefectFlow, **kwargs) -> Dict[str, Any]:
        """Execute a flow with error handling."""
        flow_id = f"{flow.name}_{id(flow)}"
        
        try:
            self.running_flows[flow_id] = {
                "flow": flow,
                "status": "running",
                "start_time": datetime.now()
            }
            
            if flow.timeout:
                result = await asyncio.wait_for(
                    flow.run(**kwargs), 
                    timeout=flow.timeout
                )
            else:
                result = await flow.run(**kwargs)
            
            self.running_flows[flow_id]["status"] = "completed"
            return result
            
        except Exception as e:
            self.running_flows[flow_id]["status"] = "failed"
            raise
            
        finally:
            if flow_id in self.running_flows:
                del self.running_flows[flow_id]

