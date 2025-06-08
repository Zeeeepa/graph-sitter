#!/usr/bin/env python3
"""
ControlFlow Codegen Integration

Enhanced ControlFlow orchestrator that seamlessly integrates with Codegen SDK
for intelligent agent coordination and task distribution.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .orchestrator import FlowOrchestrator
from .executor import FlowExecutor
from .scheduler import FlowScheduler

logger = logging.getLogger(__name__)


class AgentCapability(str, Enum):
    """Agent capability types."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    ANALYSIS = "analysis"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class TaskComplexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class CodegenAgent:
    """Codegen agent representation."""
    id: str
    name: str
    org_id: str
    token: str
    base_url: str
    capabilities: List[AgentCapability]
    max_concurrent_tasks: int = 3
    current_tasks: int = 0
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    last_used: Optional[float] = None
    is_available: bool = True


@dataclass
class TaskAssignment:
    """Task assignment to agent."""
    task_id: str
    agent_id: str
    assigned_at: float
    estimated_duration: int
    priority: int
    complexity: TaskComplexity
    required_capabilities: List[AgentCapability]
    context: Dict[str, Any] = field(default_factory=dict)


class CodegenFlowOrchestrator(FlowOrchestrator):
    """Enhanced ControlFlow orchestrator with Codegen SDK integration."""
    
    def __init__(self, **kwargs):
        """Initialize Codegen flow orchestrator."""
        super().__init__(agents=[], **kwargs)
        
        self.codegen_agents: Dict[str, CodegenAgent] = {}
        self.task_assignments: Dict[str, TaskAssignment] = {}
        self.performance_tracker = PerformanceTracker()
        self.load_balancer = LoadBalancer()
        self.task_optimizer = TaskOptimizer()
        
        # Callbacks for monitoring
        self.assignment_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        
        logger.info("Codegen flow orchestrator initialized")
    
    def register_codegen_agent(
        self,
        agent_id: str,
        name: str,
        org_id: str,
        token: str,
        base_url: str = "https://api.codegen.com",
        capabilities: List[AgentCapability] = None
    ) -> CodegenAgent:
        """Register a Codegen agent with the orchestrator."""
        if capabilities is None:
            capabilities = [
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_REVIEW,
                AgentCapability.TESTING,
                AgentCapability.DOCUMENTATION
            ]
        
        agent = CodegenAgent(
            id=agent_id,
            name=name,
            org_id=org_id,
            token=token,
            base_url=base_url,
            capabilities=capabilities
        )
        
        self.codegen_agents[agent_id] = agent
        logger.info(f"Registered Codegen agent: {name} ({agent_id})")
        
        return agent
    
    def add_assignment_callback(self, callback: Callable):
        """Add callback for task assignments."""
        self.assignment_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable):
        """Add callback for task completions."""
        self.completion_callbacks.append(callback)
    
    async def execute_workflow_with_codegen(
        self,
        workflow_definition: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute workflow with intelligent Codegen agent coordination."""
        logger.info(f"Starting workflow execution: {workflow_definition.get('name', 'unnamed')}")
        
        if context is None:
            context = {}
        
        workflow_result = {
            'workflow_id': workflow_definition.get('id', f"workflow_{int(time.time())}"),
            'name': workflow_definition.get('name', 'unnamed'),
            'status': 'running',
            'start_time': time.time(),
            'tasks': {},
            'assignments': {},
            'performance': {},
            'agent_utilization': {}
        }
        
        try:
            # Extract and analyze tasks
            tasks = workflow_definition.get('tasks', [])
            analyzed_tasks = await self._analyze_tasks(tasks, context)
            
            # Create optimal execution plan
            execution_plan = await self._create_execution_plan(analyzed_tasks, context)
            workflow_result['execution_plan'] = execution_plan
            
            # Execute tasks according to plan
            execution_results = await self._execute_tasks_with_agents(
                execution_plan=execution_plan,
                context=context,
                workflow_result=workflow_result
            )
            
            workflow_result['tasks'] = execution_results
            workflow_result['status'] = 'completed'
            
            # Calculate performance metrics
            workflow_result['performance'] = self._calculate_workflow_performance(workflow_result)
            
            logger.info(f"Workflow completed successfully: {workflow_result['workflow_id']}")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            workflow_result['status'] = 'failed'
            workflow_result['error'] = str(e)
        
        workflow_result['end_time'] = time.time()
        workflow_result['duration'] = workflow_result['end_time'] - workflow_result['start_time']
        
        return workflow_result
    
    async def _analyze_tasks(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze tasks to determine requirements and complexity."""
        analyzed_tasks = []
        
        for task in tasks:
            analyzed_task = await self.task_optimizer.analyze_task(task, context)
            analyzed_tasks.append(analyzed_task)
        
        return analyzed_tasks
    
    async def _create_execution_plan(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create optimal execution plan with agent assignments."""
        execution_plan = {
            'total_tasks': len(tasks),
            'estimated_duration': 0,
            'parallel_groups': [],
            'sequential_tasks': [],
            'agent_assignments': {}
        }
        
        # Group tasks by dependencies
        dependency_groups = self._group_tasks_by_dependencies(tasks)
        
        # Create parallel execution groups
        for group_index, task_group in enumerate(dependency_groups):
            parallel_group = {
                'group_id': f"group_{group_index}",
                'tasks': [],
                'estimated_duration': 0
            }
            
            # Assign agents to tasks in this group
            for task in task_group:
                # Find best agent for this task
                best_agent = await self._find_best_agent_for_task(task, context)
                
                if best_agent:
                    assignment = TaskAssignment(
                        task_id=task['id'],
                        agent_id=best_agent.id,
                        assigned_at=time.time(),
                        estimated_duration=task.get('estimated_duration', 300),
                        priority=task.get('priority', 1),
                        complexity=TaskComplexity(task.get('complexity', 'moderate')),
                        required_capabilities=[
                            AgentCapability(cap) for cap in task.get('required_capabilities', [])
                        ],
                        context=task.get('context', {})
                    )
                    
                    self.task_assignments[task['id']] = assignment
                    execution_plan['agent_assignments'][task['id']] = best_agent.id
                    
                    parallel_group['tasks'].append({
                        'task_id': task['id'],
                        'agent_id': best_agent.id,
                        'estimated_duration': assignment.estimated_duration
                    })
                    
                    # Update group duration (max of parallel tasks)
                    parallel_group['estimated_duration'] = max(
                        parallel_group['estimated_duration'],
                        assignment.estimated_duration
                    )
                else:
                    logger.warning(f"No suitable agent found for task: {task['id']}")
                    # Add to sequential tasks as fallback
                    execution_plan['sequential_tasks'].append(task)
            
            if parallel_group['tasks']:
                execution_plan['parallel_groups'].append(parallel_group)
                execution_plan['estimated_duration'] += parallel_group['estimated_duration']
        
        return execution_plan
    
    def _group_tasks_by_dependencies(self, tasks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group tasks by their dependencies for parallel execution."""
        # Simple dependency grouping - in practice, this would be more sophisticated
        groups = []
        remaining_tasks = tasks.copy()
        completed_task_ids = set()
        
        while remaining_tasks:
            current_group = []
            
            # Find tasks with no unresolved dependencies
            for task in remaining_tasks[:]:
                dependencies = task.get('dependencies', [])
                if all(dep_id in completed_task_ids for dep_id in dependencies):
                    current_group.append(task)
                    remaining_tasks.remove(task)
                    completed_task_ids.add(task['id'])
            
            if not current_group and remaining_tasks:
                # Handle circular dependencies by taking the first task
                current_group.append(remaining_tasks.pop(0))
                completed_task_ids.add(current_group[0]['id'])
            
            if current_group:
                groups.append(current_group)
        
        return groups
    
    async def _find_best_agent_for_task(
        self,
        task: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[CodegenAgent]:
        """Find the best available agent for a task."""
        required_capabilities = [
            AgentCapability(cap) for cap in task.get('required_capabilities', [])
        ]
        
        # Filter agents by capabilities
        suitable_agents = []
        for agent in self.codegen_agents.values():
            if not agent.is_available:
                continue
            
            if agent.current_tasks >= agent.max_concurrent_tasks:
                continue
            
            # Check if agent has required capabilities
            if all(cap in agent.capabilities for cap in required_capabilities):
                suitable_agents.append(agent)
        
        if not suitable_agents:
            return None
        
        # Select best agent using load balancer
        best_agent = self.load_balancer.select_best_agent(
            agents=suitable_agents,
            task=task,
            performance_tracker=self.performance_tracker
        )
        
        return best_agent
    
    async def _execute_tasks_with_agents(
        self,
        execution_plan: Dict[str, Any],
        context: Dict[str, Any],
        workflow_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks using assigned Codegen agents."""
        task_results = {}
        
        # Execute parallel groups
        for group in execution_plan['parallel_groups']:
            logger.info(f"Executing parallel group: {group['group_id']}")
            
            # Create tasks for parallel execution
            group_tasks = []
            for task_info in group['tasks']:
                task_id = task_info['task_id']
                agent_id = task_info['agent_id']
                
                # Get task assignment
                assignment = self.task_assignments.get(task_id)
                if not assignment:
                    logger.error(f"No assignment found for task: {task_id}")
                    continue
                
                # Create execution coroutine
                task_coro = self._execute_single_task(
                    assignment=assignment,
                    context=context,
                    workflow_result=workflow_result
                )
                group_tasks.append(task_coro)
            
            # Execute tasks in parallel
            if group_tasks:
                group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(group_results):
                    task_info = group['tasks'][i]
                    task_id = task_info['task_id']
                    
                    if isinstance(result, Exception):
                        logger.error(f"Task {task_id} failed: {result}")
                        task_results[task_id] = {
                            'status': 'failed',
                            'error': str(result),
                            'agent_id': task_info['agent_id']
                        }
                    else:
                        task_results[task_id] = result
        
        # Execute sequential tasks
        for task in execution_plan['sequential_tasks']:
            logger.info(f"Executing sequential task: {task['id']}")
            
            # Find agent for sequential task
            best_agent = await self._find_best_agent_for_task(task, context)
            if best_agent:
                assignment = TaskAssignment(
                    task_id=task['id'],
                    agent_id=best_agent.id,
                    assigned_at=time.time(),
                    estimated_duration=task.get('estimated_duration', 300),
                    priority=task.get('priority', 1),
                    complexity=TaskComplexity(task.get('complexity', 'moderate')),
                    required_capabilities=[
                        AgentCapability(cap) for cap in task.get('required_capabilities', [])
                    ]
                )
                
                result = await self._execute_single_task(assignment, context, workflow_result)
                task_results[task['id']] = result
            else:
                logger.error(f"No agent available for sequential task: {task['id']}")
                task_results[task['id']] = {
                    'status': 'failed',
                    'error': 'No suitable agent available'
                }
        
        return task_results
    
    async def _execute_single_task(
        self,
        assignment: TaskAssignment,
        context: Dict[str, Any],
        workflow_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single task with assigned Codegen agent."""
        agent = self.codegen_agents[assignment.agent_id]
        task_id = assignment.task_id
        
        logger.info(f"Executing task {task_id} with agent {agent.name}")
        
        # Update agent status
        agent.current_tasks += 1
        agent.last_used = time.time()
        
        # Notify assignment callbacks
        for callback in self.assignment_callbacks:
            try:
                callback(assignment, agent)
            except Exception as e:
                logger.error(f"Assignment callback failed: {e}")
        
        task_result = {
            'task_id': task_id,
            'agent_id': agent.id,
            'agent_name': agent.name,
            'status': 'running',
            'start_time': time.time()
        }
        
        try:
            # Initialize Codegen agent
            from codegen.agents.agent import Agent
            
            codegen_agent = Agent(
                org_id=agent.org_id,
                token=agent.token,
                base_url=agent.base_url
            )
            
            # Create task prompt
            prompt = self._create_task_prompt(assignment, context)
            
            # Execute task
            codegen_task = codegen_agent.run(prompt)
            
            # Wait for completion
            timeout = assignment.estimated_duration * 2
            start_time = time.time()
            
            while codegen_task.status not in ['completed', 'failed'] and (time.time() - start_time) < timeout:
                await asyncio.sleep(5)
                codegen_task.refresh()
            
            if codegen_task.status == 'completed':
                task_result['status'] = 'completed'
                task_result['result'] = codegen_task.result if hasattr(codegen_task, 'result') else 'Task completed'
                task_result['codegen_task_id'] = codegen_task.id
                
                # Update performance metrics
                duration = time.time() - task_result['start_time']
                self.performance_tracker.record_task_completion(
                    agent_id=agent.id,
                    task_complexity=assignment.complexity,
                    duration=duration,
                    success=True
                )
                
            else:
                task_result['status'] = 'failed'
                task_result['error'] = f"Task failed or timed out: {codegen_task.status}"
                
                # Update performance metrics
                duration = time.time() - task_result['start_time']
                self.performance_tracker.record_task_completion(
                    agent_id=agent.id,
                    task_complexity=assignment.complexity,
                    duration=duration,
                    success=False
                )
        
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task_result['status'] = 'failed'
            task_result['error'] = str(e)
            
            # Update performance metrics
            duration = time.time() - task_result['start_time']
            self.performance_tracker.record_task_completion(
                agent_id=agent.id,
                task_complexity=assignment.complexity,
                duration=duration,
                success=False
            )
        
        finally:
            # Update agent status
            agent.current_tasks -= 1
            
            task_result['end_time'] = time.time()
            task_result['duration'] = task_result['end_time'] - task_result['start_time']
            
            # Notify completion callbacks
            for callback in self.completion_callbacks:
                try:
                    callback(assignment, agent, task_result)
                except Exception as e:
                    logger.error(f"Completion callback failed: {e}")
        
        return task_result
    
    def _create_task_prompt(self, assignment: TaskAssignment, context: Dict[str, Any]) -> str:
        """Create detailed prompt for Codegen agent."""
        agent = self.codegen_agents[assignment.agent_id]
        
        prompt = f"""
        Execute the following task as part of a coordinated workflow:
        
        Task ID: {assignment.task_id}
        Complexity: {assignment.complexity.value}
        Priority: {assignment.priority}
        Estimated Duration: {assignment.estimated_duration} seconds
        
        Required Capabilities: {', '.join([cap.value for cap in assignment.required_capabilities])}
        Agent Capabilities: {', '.join([cap.value for cap in agent.capabilities])}
        
        Task Context:
        {assignment.context}
        
        Workflow Context:
        {context}
        
        Please execute this task efficiently and provide detailed results.
        Focus on the specific requirements and maintain consistency with the overall workflow.
        """
        
        return prompt
    
    def _calculate_workflow_performance(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate workflow performance metrics."""
        tasks = workflow_result.get('tasks', {})
        
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks.values() if task.get('status') == 'completed')
        failed_tasks = sum(1 for task in tasks.values() if task.get('status') == 'failed')
        
        total_duration = sum(task.get('duration', 0) for task in tasks.values())
        avg_duration = total_duration / total_tasks if total_tasks > 0 else 0
        
        # Agent utilization
        agent_utilization = {}
        for task in tasks.values():
            agent_id = task.get('agent_id')
            if agent_id:
                if agent_id not in agent_utilization:
                    agent_utilization[agent_id] = {'tasks': 0, 'duration': 0}
                agent_utilization[agent_id]['tasks'] += 1
                agent_utilization[agent_id]['duration'] += task.get('duration', 0)
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'total_duration': total_duration,
            'average_task_duration': avg_duration,
            'agent_utilization': agent_utilization,
            'workflow_duration': workflow_result.get('duration', 0)
        }


class PerformanceTracker:
    """Tracks agent performance metrics."""
    
    def __init__(self):
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
    
    def record_task_completion(
        self,
        agent_id: str,
        task_complexity: TaskComplexity,
        duration: float,
        success: bool
    ):
        """Record task completion metrics."""
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = {
                'total_tasks': 0,
                'successful_tasks': 0,
                'failed_tasks': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'complexity_performance': {},
                'success_rate': 0
            }
        
        metrics = self.agent_metrics[agent_id]
        metrics['total_tasks'] += 1
        metrics['total_duration'] += duration
        
        if success:
            metrics['successful_tasks'] += 1
        else:
            metrics['failed_tasks'] += 1
        
        metrics['avg_duration'] = metrics['total_duration'] / metrics['total_tasks']
        metrics['success_rate'] = metrics['successful_tasks'] / metrics['total_tasks']
        
        # Track complexity-specific performance
        complexity_key = task_complexity.value
        if complexity_key not in metrics['complexity_performance']:
            metrics['complexity_performance'][complexity_key] = {
                'tasks': 0,
                'successes': 0,
                'avg_duration': 0,
                'total_duration': 0
            }
        
        complexity_metrics = metrics['complexity_performance'][complexity_key]
        complexity_metrics['tasks'] += 1
        complexity_metrics['total_duration'] += duration
        complexity_metrics['avg_duration'] = complexity_metrics['total_duration'] / complexity_metrics['tasks']
        
        if success:
            complexity_metrics['successes'] += 1
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for an agent."""
        return self.agent_metrics.get(agent_id, {})


class LoadBalancer:
    """Intelligent load balancer for agent selection."""
    
    def select_best_agent(
        self,
        agents: List[CodegenAgent],
        task: Dict[str, Any],
        performance_tracker: PerformanceTracker
    ) -> CodegenAgent:
        """Select the best agent for a task based on multiple factors."""
        if not agents:
            return None
        
        if len(agents) == 1:
            return agents[0]
        
        # Score agents based on multiple factors
        agent_scores = []
        
        for agent in agents:
            score = self._calculate_agent_score(agent, task, performance_tracker)
            agent_scores.append((agent, score))
        
        # Sort by score (higher is better)
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        return agent_scores[0][0]
    
    def _calculate_agent_score(
        self,
        agent: CodegenAgent,
        task: Dict[str, Any],
        performance_tracker: PerformanceTracker
    ) -> float:
        """Calculate agent score for task assignment."""
        score = 0.0
        
        # Base availability score
        availability_score = (agent.max_concurrent_tasks - agent.current_tasks) / agent.max_concurrent_tasks
        score += availability_score * 0.3
        
        # Performance score
        performance_metrics = performance_tracker.get_agent_performance(agent.id)
        if performance_metrics:
            success_rate = performance_metrics.get('success_rate', 0.5)
            score += success_rate * 0.4
            
            # Complexity-specific performance
            task_complexity = task.get('complexity', 'moderate')
            complexity_performance = performance_metrics.get('complexity_performance', {}).get(task_complexity, {})
            if complexity_performance:
                complexity_success_rate = complexity_performance.get('successes', 0) / complexity_performance.get('tasks', 1)
                score += complexity_success_rate * 0.2
        else:
            # New agent gets neutral score
            score += 0.3
        
        # Recency score (prefer agents that haven't been used recently)
        if agent.last_used:
            time_since_last_use = time.time() - agent.last_used
            recency_score = min(time_since_last_use / 3600, 1.0)  # Max 1 hour
            score += recency_score * 0.1
        else:
            score += 0.1  # New agent bonus
        
        return score


class TaskOptimizer:
    """Optimizes task definitions for better execution."""
    
    async def analyze_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and optimize task definition."""
        analyzed_task = task.copy()
        
        # Infer complexity if not specified
        if 'complexity' not in analyzed_task:
            analyzed_task['complexity'] = self._infer_complexity(task)
        
        # Infer required capabilities if not specified
        if 'required_capabilities' not in analyzed_task:
            analyzed_task['required_capabilities'] = self._infer_capabilities(task)
        
        # Estimate duration if not specified
        if 'estimated_duration' not in analyzed_task:
            analyzed_task['estimated_duration'] = self._estimate_duration(task)
        
        # Set priority if not specified
        if 'priority' not in analyzed_task:
            analyzed_task['priority'] = self._calculate_priority(task, context)
        
        return analyzed_task
    
    def _infer_complexity(self, task: Dict[str, Any]) -> str:
        """Infer task complexity from description and requirements."""
        description = task.get('description', '').lower()
        
        # Simple heuristics for complexity inference
        if any(keyword in description for keyword in ['simple', 'basic', 'quick', 'minor']):
            return 'simple'
        elif any(keyword in description for keyword in ['complex', 'advanced', 'sophisticated', 'comprehensive']):
            return 'complex'
        elif any(keyword in description for keyword in ['expert', 'critical', 'architecture', 'system']):
            return 'expert'
        else:
            return 'moderate'
    
    def _infer_capabilities(self, task: Dict[str, Any]) -> List[str]:
        """Infer required capabilities from task description."""
        description = task.get('description', '').lower()
        capabilities = []
        
        # Map keywords to capabilities
        capability_keywords = {
            'code_generation': ['implement', 'create', 'build', 'develop', 'generate'],
            'code_review': ['review', 'check', 'validate', 'audit', 'inspect'],
            'testing': ['test', 'verify', 'validate', 'check', 'unit test', 'integration test'],
            'documentation': ['document', 'readme', 'docs', 'comment', 'explain'],
            'debugging': ['debug', 'fix', 'troubleshoot', 'resolve', 'error'],
            'refactoring': ['refactor', 'optimize', 'improve', 'restructure', 'clean'],
            'analysis': ['analyze', 'examine', 'investigate', 'study', 'assess'],
            'integration': ['integrate', 'connect', 'api', 'webhook', 'service'],
            'deployment': ['deploy', 'release', 'publish', 'launch', 'production'],
            'monitoring': ['monitor', 'track', 'observe', 'metrics', 'logging']
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in description for keyword in keywords):
                capabilities.append(capability)
        
        # Default capabilities if none inferred
        if not capabilities:
            capabilities = ['code_generation']
        
        return capabilities
    
    def _estimate_duration(self, task: Dict[str, Any]) -> int:
        """Estimate task duration in seconds."""
        complexity = task.get('complexity', 'moderate')
        
        # Base duration by complexity
        base_durations = {
            'simple': 300,      # 5 minutes
            'moderate': 900,    # 15 minutes
            'complex': 1800,    # 30 minutes
            'expert': 3600      # 60 minutes
        }
        
        base_duration = base_durations.get(complexity, 900)
        
        # Adjust based on capabilities required
        capabilities = task.get('required_capabilities', [])
        capability_multiplier = 1.0 + (len(capabilities) - 1) * 0.2
        
        return int(base_duration * capability_multiplier)
    
    def _calculate_priority(self, task: Dict[str, Any], context: Dict[str, Any]) -> int:
        """Calculate task priority based on various factors."""
        priority = 1  # Default priority
        
        # Increase priority for critical tasks
        description = task.get('description', '').lower()
        if any(keyword in description for keyword in ['critical', 'urgent', 'important', 'blocker']):
            priority += 2
        
        # Increase priority for tasks with many dependencies
        dependencies = task.get('dependencies', [])
        if len(dependencies) > 3:
            priority += 1
        
        # Increase priority for deployment/production tasks
        if any(keyword in description for keyword in ['deploy', 'production', 'release']):
            priority += 1
        
        return min(priority, 5)  # Cap at priority 5


# Factory function for easy integration
def create_codegen_flow_orchestrator(**kwargs) -> CodegenFlowOrchestrator:
    """Create and initialize Codegen flow orchestrator."""
    return CodegenFlowOrchestrator(**kwargs)

