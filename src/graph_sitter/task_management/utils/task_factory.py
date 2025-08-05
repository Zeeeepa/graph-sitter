"""
Task factory for creating common task types
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from ..models.task import Task, TaskPriority, TaskType


class TaskFactory:
    """
    Factory for creating common task types with predefined configurations
    """
    
    @staticmethod
    def create_code_analysis_task(
        name: str,
        repository_url: str,
        analysis_type: str,
        created_by: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_minutes: int = 30,
        **kwargs
    ) -> Task:
        """Create a code analysis task"""
        return Task(
            name=name,
            description=f"Code analysis task for {repository_url}",
            task_type=TaskType.CODE_ANALYSIS,
            priority=priority,
            created_by=created_by,
            timeout_seconds=timeout_minutes * 60,
            metadata={
                "repository_url": repository_url,
                "analysis_type": analysis_type,
                **kwargs.get("metadata", {})
            },
            execution_context={
                "repository_url": repository_url,
                "analysis_config": {
                    "type": analysis_type,
                    "timeout_minutes": timeout_minutes,
                },
                **kwargs.get("execution_context", {})
            },
            resource_requirements={
                "cpu_cores": 2,
                "memory_gb": 4,
                "disk_gb": 10,
                **kwargs.get("resource_requirements", {})
            },
            tags={"code_analysis", analysis_type, **kwargs.get("tags", set())},
            **{k: v for k, v in kwargs.items() if k not in ["metadata", "execution_context", "resource_requirements", "tags"]}
        )
    
    @staticmethod
    def create_code_generation_task(
        name: str,
        prompt: str,
        target_language: str,
        created_by: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_tokens: int = 2000,
        **kwargs
    ) -> Task:
        """Create a code generation task"""
        return Task(
            name=name,
            description=f"Generate {target_language} code: {prompt[:100]}...",
            task_type=TaskType.CODE_GENERATION,
            priority=priority,
            created_by=created_by,
            metadata={
                "prompt": prompt,
                "target_language": target_language,
                "max_tokens": max_tokens,
                **kwargs.get("metadata", {})
            },
            execution_context={
                "generation_config": {
                    "language": target_language,
                    "max_tokens": max_tokens,
                    "prompt": prompt,
                },
                **kwargs.get("execution_context", {})
            },
            resource_requirements={
                "cpu_cores": 1,
                "memory_gb": 2,
                "gpu_memory_gb": 4,
                **kwargs.get("resource_requirements", {})
            },
            tags={"code_generation", target_language, **kwargs.get("tags", set())},
            **{k: v for k, v in kwargs.items() if k not in ["metadata", "execution_context", "resource_requirements", "tags"]}
        )
    
    @staticmethod
    def create_code_review_task(
        name: str,
        pull_request_url: str,
        review_criteria: List[str],
        created_by: str,
        priority: TaskPriority = TaskPriority.HIGH,
        **kwargs
    ) -> Task:
        """Create a code review task"""
        return Task(
            name=name,
            description=f"Code review for PR: {pull_request_url}",
            task_type=TaskType.CODE_REVIEW,
            priority=priority,
            created_by=created_by,
            metadata={
                "pull_request_url": pull_request_url,
                "review_criteria": review_criteria,
                **kwargs.get("metadata", {})
            },
            execution_context={
                "review_config": {
                    "criteria": review_criteria,
                    "pr_url": pull_request_url,
                },
                **kwargs.get("execution_context", {})
            },
            resource_requirements={
                "cpu_cores": 1,
                "memory_gb": 2,
                **kwargs.get("resource_requirements", {})
            },
            tags={"code_review", "pull_request", **kwargs.get("tags", set())},
            **{k: v for k, v in kwargs.items() if k not in ["metadata", "execution_context", "resource_requirements", "tags"]}
        )
    
    @staticmethod
    def create_testing_task(
        name: str,
        test_suite: str,
        test_type: str,
        created_by: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_minutes: int = 60,
        **kwargs
    ) -> Task:
        """Create a testing task"""
        return Task(
            name=name,
            description=f"Run {test_type} tests: {test_suite}",
            task_type=TaskType.TESTING,
            priority=priority,
            created_by=created_by,
            timeout_seconds=timeout_minutes * 60,
            metadata={
                "test_suite": test_suite,
                "test_type": test_type,
                **kwargs.get("metadata", {})
            },
            execution_context={
                "test_config": {
                    "suite": test_suite,
                    "type": test_type,
                    "timeout_minutes": timeout_minutes,
                },
                **kwargs.get("execution_context", {})
            },
            resource_requirements={
                "cpu_cores": 2,
                "memory_gb": 4,
                "disk_gb": 5,
                **kwargs.get("resource_requirements", {})
            },
            tags={"testing", test_type, **kwargs.get("tags", set())},
            **{k: v for k, v in kwargs.items() if k not in ["metadata", "execution_context", "resource_requirements", "tags"]}
        )
    
    @staticmethod
    def create_deployment_task(
        name: str,
        environment: str,
        deployment_config: Dict[str, Any],
        created_by: str,
        priority: TaskPriority = TaskPriority.HIGH,
        **kwargs
    ) -> Task:
        """Create a deployment task"""
        return Task(
            name=name,
            description=f"Deploy to {environment} environment",
            task_type=TaskType.DEPLOYMENT,
            priority=priority,
            created_by=created_by,
            metadata={
                "environment": environment,
                "deployment_config": deployment_config,
                **kwargs.get("metadata", {})
            },
            execution_context={
                "deployment": {
                    "environment": environment,
                    "config": deployment_config,
                },
                **kwargs.get("execution_context", {})
            },
            resource_requirements={
                "cpu_cores": 1,
                "memory_gb": 2,
                "network_bandwidth_mbps": 100,
                **kwargs.get("resource_requirements", {})
            },
            tags={"deployment", environment, **kwargs.get("tags", set())},
            **{k: v for k, v in kwargs.items() if k not in ["metadata", "execution_context", "resource_requirements", "tags"]}
        )
    
    @staticmethod
    def create_monitoring_task(
        name: str,
        monitoring_target: str,
        metrics: List[str],
        created_by: str,
        priority: TaskPriority = TaskPriority.LOW,
        check_interval_minutes: int = 5,
        **kwargs
    ) -> Task:
        """Create a monitoring task"""
        return Task(
            name=name,
            description=f"Monitor {monitoring_target} for metrics: {', '.join(metrics)}",
            task_type=TaskType.MONITORING,
            priority=priority,
            created_by=created_by,
            metadata={
                "monitoring_target": monitoring_target,
                "metrics": metrics,
                "check_interval_minutes": check_interval_minutes,
                **kwargs.get("metadata", {})
            },
            execution_context={
                "monitoring_config": {
                    "target": monitoring_target,
                    "metrics": metrics,
                    "interval_minutes": check_interval_minutes,
                },
                **kwargs.get("execution_context", {})
            },
            resource_requirements={
                "cpu_cores": 0.5,
                "memory_gb": 1,
                **kwargs.get("resource_requirements", {})
            },
            tags={"monitoring", **kwargs.get("tags", set())},
            **{k: v for k, v in kwargs.items() if k not in ["metadata", "execution_context", "resource_requirements", "tags"]}
        )
    
    @staticmethod
    def create_batch_tasks(
        task_configs: List[Dict[str, Any]],
        created_by: str,
        batch_name: Optional[str] = None
    ) -> List[Task]:
        """Create multiple tasks as a batch"""
        tasks = []
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        for i, config in enumerate(task_configs):
            task_name = config.get("name", f"{batch_name or 'batch_task'}_{i+1}")
            task_type = TaskType(config.get("task_type", TaskType.CUSTOM))
            
            # Add batch metadata
            metadata = config.get("metadata", {})
            metadata.update({
                "batch_id": batch_id,
                "batch_index": i,
                "batch_size": len(task_configs),
            })
            
            task = Task(
                name=task_name,
                description=config.get("description", f"Batch task {i+1} of {len(task_configs)}"),
                task_type=task_type,
                priority=TaskPriority(config.get("priority", TaskPriority.NORMAL)),
                created_by=created_by,
                metadata=metadata,
                execution_context=config.get("execution_context", {}),
                resource_requirements=config.get("resource_requirements", {}),
                tags=set(config.get("tags", [])) | {"batch", batch_id},
                depends_on=set(config.get("depends_on", [])),
                max_retries=config.get("max_retries", 3),
                timeout_seconds=config.get("timeout_seconds"),
                deadline=config.get("deadline"),
            )
            
            tasks.append(task)
        
        return tasks
    
    @staticmethod
    def create_pipeline_tasks(
        pipeline_config: Dict[str, Any],
        created_by: str
    ) -> List[Task]:
        """Create a pipeline of dependent tasks"""
        tasks = []
        pipeline_id = f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        stages = pipeline_config.get("stages", [])
        previous_task_ids = set()
        
        for stage_index, stage in enumerate(stages):
            stage_tasks = []
            
            # Create tasks for this stage
            for task_index, task_config in enumerate(stage.get("tasks", [])):
                task_name = task_config.get("name", f"pipeline_stage_{stage_index+1}_task_{task_index+1}")
                
                # Add pipeline metadata
                metadata = task_config.get("metadata", {})
                metadata.update({
                    "pipeline_id": pipeline_id,
                    "stage_index": stage_index,
                    "task_index": task_index,
                    "stage_name": stage.get("name", f"Stage {stage_index+1}"),
                })
                
                # Set dependencies to previous stage tasks
                depends_on = set(task_config.get("depends_on", []))
                if stage_index > 0:
                    depends_on.update(previous_task_ids)
                
                task = Task(
                    name=task_name,
                    description=task_config.get("description", f"Pipeline task in stage {stage_index+1}"),
                    task_type=TaskType(task_config.get("task_type", TaskType.CUSTOM)),
                    priority=TaskPriority(task_config.get("priority", TaskPriority.NORMAL)),
                    created_by=created_by,
                    metadata=metadata,
                    execution_context=task_config.get("execution_context", {}),
                    resource_requirements=task_config.get("resource_requirements", {}),
                    tags=set(task_config.get("tags", [])) | {"pipeline", pipeline_id, f"stage_{stage_index+1}"},
                    depends_on=depends_on,
                    max_retries=task_config.get("max_retries", 3),
                    timeout_seconds=task_config.get("timeout_seconds"),
                    deadline=task_config.get("deadline"),
                )
                
                tasks.append(task)
                stage_tasks.append(task.id)
            
            # Update previous task IDs for next stage
            previous_task_ids = set(stage_tasks)
        
        return tasks
    
    @staticmethod
    def create_scheduled_task(
        base_task: Task,
        schedule_time: datetime,
        recurrence: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a scheduled task"""
        scheduled_task = Task.model_validate(base_task.model_dump())
        scheduled_task.scheduled_at = schedule_time
        
        # Add scheduling metadata
        scheduled_task.metadata.update({
            "scheduled": True,
            "original_schedule_time": schedule_time.isoformat(),
            "recurrence": recurrence,
        })
        
        scheduled_task.tags.add("scheduled")
        
        if recurrence:
            scheduled_task.tags.add("recurring")
        
        return scheduled_task

