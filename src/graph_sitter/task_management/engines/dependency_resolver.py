"""
Dependency resolution engine for automated task dependency resolution
"""

from typing import Dict, List, Set
from uuid import UUID

from ..models.task import Task, TaskStatus


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected"""
    pass


class DependencyResolver:
    """
    Automated task dependency resolution engine
    
    Features:
    - Dependency graph analysis
    - Circular dependency detection
    - Topological sorting for execution order
    - Dependency validation
    """
    
    def __init__(self):
        self.tasks: Dict[UUID, Task] = {}
    
    def add_task(self, task: Task) -> None:
        """Add task to dependency resolver"""
        self.tasks[task.id] = task
    
    def remove_task(self, task_id: UUID) -> None:
        """Remove task from dependency resolver"""
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    def update_task(self, task: Task) -> None:
        """Update task in dependency resolver"""
        self.tasks[task.id] = task
    
    def validate_dependencies(self, task: Task) -> List[str]:
        """
        Validate task dependencies
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check if all dependencies exist
        for dep_id in task.depends_on:
            if dep_id not in self.tasks:
                errors.append(f"Dependency task {dep_id} does not exist")
        
        # Check for self-dependency
        if task.id in task.depends_on:
            errors.append("Task cannot depend on itself")
        
        # Check for circular dependencies
        try:
            self._detect_circular_dependencies(task)
        except CircularDependencyError as e:
            errors.append(str(e))
        
        return errors
    
    def _detect_circular_dependencies(self, task: Task) -> None:
        """
        Detect circular dependencies using DFS
        
        Raises:
            CircularDependencyError: If circular dependency is detected
        """
        visited = set()
        rec_stack = set()
        
        def dfs(task_id: UUID, path: List[UUID]) -> None:
            if task_id in rec_stack:
                cycle_path = path[path.index(task_id):] + [task_id]
                raise CircularDependencyError(
                    f"Circular dependency detected: {' -> '.join(str(t) for t in cycle_path)}"
                )
            
            if task_id in visited:
                return
            
            visited.add(task_id)
            rec_stack.add(task_id)
            
            if task_id in self.tasks:
                current_task = self.tasks[task_id]
                for dep_id in current_task.depends_on:
                    dfs(dep_id, path + [task_id])
            
            rec_stack.remove(task_id)
        
        dfs(task.id, [])
    
    def get_execution_order(self, task_ids: Set[UUID] = None) -> List[UUID]:
        """
        Get topological execution order for tasks
        
        Args:
            task_ids: Specific task IDs to order (if None, orders all tasks)
        
        Returns:
            List of task IDs in execution order
        
        Raises:
            CircularDependencyError: If circular dependencies exist
        """
        if task_ids is None:
            task_ids = set(self.tasks.keys())
        
        # Filter to only include existing tasks
        task_ids = {tid for tid in task_ids if tid in self.tasks}
        
        # Topological sort using Kahn's algorithm
        in_degree = {task_id: 0 for task_id in task_ids}
        
        # Calculate in-degrees
        for task_id in task_ids:
            task = self.tasks[task_id]
            for dep_id in task.depends_on:
                if dep_id in task_ids:
                    in_degree[task_id] += 1
        
        # Initialize queue with tasks having no dependencies
        queue = [task_id for task_id in task_ids if in_degree[task_id] == 0]
        result = []
        
        while queue:
            current_id = queue.pop(0)
            result.append(current_id)
            
            # Update in-degrees for dependent tasks
            current_task = self.tasks[current_id]
            for blocked_id in current_task.blocks:
                if blocked_id in task_ids:
                    in_degree[blocked_id] -= 1
                    if in_degree[blocked_id] == 0:
                        queue.append(blocked_id)
        
        # Check for circular dependencies
        if len(result) != len(task_ids):
            remaining_tasks = task_ids - set(result)
            raise CircularDependencyError(
                f"Circular dependency detected among tasks: {remaining_tasks}"
            )
        
        return result
    
    def get_ready_tasks(self, completed_tasks: Set[UUID] = None) -> List[Task]:
        """
        Get tasks that are ready to run based on dependencies
        
        Args:
            completed_tasks: Set of completed task IDs
        
        Returns:
            List of tasks ready to run
        """
        if completed_tasks is None:
            completed_tasks = {
                task_id for task_id, task in self.tasks.items()
                if task.status == TaskStatus.COMPLETED
            }
        
        ready_tasks = []
        for task in self.tasks.values():
            if task.is_ready_to_run(completed_tasks):
                ready_tasks.append(task)
        
        return ready_tasks
    
    def get_blocked_tasks(self, task_id: UUID) -> List[Task]:
        """
        Get tasks that are blocked by the given task
        
        Args:
            task_id: ID of the task to check
        
        Returns:
            List of blocked tasks
        """
        if task_id not in self.tasks:
            return []
        
        task = self.tasks[task_id]
        blocked_tasks = []
        
        for blocked_id in task.blocks:
            if blocked_id in self.tasks:
                blocked_tasks.append(self.tasks[blocked_id])
        
        return blocked_tasks
    
    def get_dependency_chain(self, task_id: UUID) -> List[UUID]:
        """
        Get the full dependency chain for a task
        
        Args:
            task_id: ID of the task
        
        Returns:
            List of task IDs in dependency order
        """
        if task_id not in self.tasks:
            return []
        
        visited = set()
        chain = []
        
        def dfs(current_id: UUID) -> None:
            if current_id in visited or current_id not in self.tasks:
                return
            
            visited.add(current_id)
            task = self.tasks[current_id]
            
            # First add dependencies
            for dep_id in task.depends_on:
                dfs(dep_id)
            
            # Then add current task
            chain.append(current_id)
        
        dfs(task_id)
        return chain
    
    def can_execute_parallel(self, task_ids: Set[UUID]) -> bool:
        """
        Check if tasks can be executed in parallel (no dependencies between them)
        
        Args:
            task_ids: Set of task IDs to check
        
        Returns:
            True if tasks can run in parallel
        """
        for task_id in task_ids:
            if task_id not in self.tasks:
                continue
            
            task = self.tasks[task_id]
            
            # Check if any dependency or blocked task is in the set
            if task.depends_on.intersection(task_ids):
                return False
            if task.blocks.intersection(task_ids):
                return False
        
        return True
    
    def get_dependency_graph(self) -> Dict[str, Dict]:
        """
        Get dependency graph representation
        
        Returns:
            Dictionary representing the dependency graph
        """
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for task_id, task in self.tasks.items():
            graph["nodes"].append({
                "id": str(task_id),
                "name": task.name,
                "status": task.status,
                "priority": task.priority,
                "type": task.task_type
            })
        
        # Add edges
        for task_id, task in self.tasks.items():
            for dep_id in task.depends_on:
                if dep_id in self.tasks:
                    graph["edges"].append({
                        "from": str(dep_id),
                        "to": str(task_id),
                        "type": "dependency"
                    })
        
        return graph
    
    def optimize_execution_plan(self, task_ids: Set[UUID] = None) -> Dict[str, List[UUID]]:
        """
        Create optimized execution plan with parallel execution groups
        
        Args:
            task_ids: Specific task IDs to plan (if None, plans all tasks)
        
        Returns:
            Dictionary with execution phases and parallel groups
        """
        if task_ids is None:
            task_ids = set(self.tasks.keys())
        
        execution_order = self.get_execution_order(task_ids)
        plan = {"phases": []}
        
        remaining_tasks = set(execution_order)
        phase = 0
        
        while remaining_tasks:
            # Find tasks that can run in parallel in this phase
            current_phase_tasks = []
            completed_tasks = set(execution_order) - remaining_tasks
            
            for task_id in list(remaining_tasks):
                task = self.tasks[task_id]
                if task.is_ready_to_run(completed_tasks):
                    current_phase_tasks.append(task_id)
            
            if not current_phase_tasks:
                # This shouldn't happen with valid dependency resolution
                break
            
            # Check which tasks can run in parallel
            parallel_groups = []
            remaining_phase_tasks = set(current_phase_tasks)
            
            while remaining_phase_tasks:
                parallel_group = []
                tasks_to_remove = set()
                
                for task_id in remaining_phase_tasks:
                    # Check if this task can run in parallel with current group
                    test_group = set(parallel_group + [task_id])
                    if self.can_execute_parallel(test_group):
                        parallel_group.append(task_id)
                        tasks_to_remove.add(task_id)
                
                if parallel_group:
                    parallel_groups.append(parallel_group)
                    remaining_phase_tasks -= tasks_to_remove
                else:
                    # Add remaining tasks individually
                    for task_id in remaining_phase_tasks:
                        parallel_groups.append([task_id])
                    break
            
            plan["phases"].append({
                "phase": phase,
                "parallel_groups": parallel_groups
            })
            
            # Remove completed tasks from remaining
            for group in parallel_groups:
                remaining_tasks -= set(group)
            
            phase += 1
        
        return plan

