"""
Workflow orchestration engine for managing complex CI/CD workflows
"""
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging

from backend.config import settings
from backend.database import DatabaseManager, WorkflowExecution, WorkflowStep
from backend.services.websocket_manager import WebSocketManager
from backend.services.codegen_service import CodegenService
from backend.services.github_service import GitHubService
from backend.services.graph_sitter_service import CodeAnalysisService
from backend.services.modal_service import ModalDeploymentService

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class WorkflowStep:
    """Individual workflow step definition"""
    
    def __init__(self, step_id: str, name: str, step_type: str, config: Dict[str, Any]):
        self.step_id = step_id
        self.name = name
        self.step_type = step_type
        self.config = config
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
        self.retry_count = 0
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 300)  # 5 minutes default
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_id': self.step_id,
            'name': self.name,
            'step_type': self.step_type,
            'status': self.status.value,
            'config': self.config,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }


class WorkflowDefinition:
    """Workflow definition with steps and dependencies"""
    
    def __init__(self, workflow_id: str, name: str, project_id: str):
        self.workflow_id = workflow_id
        self.name = name
        self.project_id = project_id
        self.steps: List[WorkflowStep] = []
        self.dependencies: Dict[str, List[str]] = {}  # step_id -> [dependency_step_ids]
        self.status = WorkflowStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.error = None
        self.metadata = {}
    
    def add_step(self, step: WorkflowStep, dependencies: List[str] = None):
        """Add a step to the workflow"""
        self.steps.append(step)
        if dependencies:
            self.dependencies[step.step_id] = dependencies
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute (dependencies completed)"""
        ready_steps = []
        
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            dependencies = self.dependencies.get(step.step_id, [])
            dependencies_completed = all(
                self.get_step_by_id(dep_id).status == StepStatus.COMPLETED
                for dep_id in dependencies
            )
            
            if dependencies_completed:
                ready_steps.append(step)
        
        return ready_steps
    
    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def is_completed(self) -> bool:
        """Check if workflow is completed"""
        return all(step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED] for step in self.steps)
    
    def has_failed(self) -> bool:
        """Check if workflow has failed"""
        return any(step.status == StepStatus.FAILED for step in self.steps)
    
    def get_progress_percentage(self) -> int:
        """Calculate workflow progress percentage"""
        if not self.steps:
            return 0
        
        completed_steps = sum(1 for step in self.steps if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED])
        return int((completed_steps / len(self.steps)) * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'project_id': self.project_id,
            'status': self.status.value,
            'steps': [step.to_dict() for step in self.steps],
            'dependencies': self.dependencies,
            'progress_percentage': self.get_progress_percentage(),
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'metadata': self.metadata
        }


class StepExecutor:
    """Executes individual workflow steps"""
    
    def __init__(self, services: Dict[str, Any]):
        self.codegen_service = services.get('codegen')
        self.github_service = services.get('github')
        self.analysis_service = services.get('analysis')
        self.deployment_service = services.get('deployment')
        self.websocket_manager = services.get('websocket')
    
    async def execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow step"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        try:
            # Execute based on step type
            if step.step_type == 'code_analysis':
                result = await self._execute_code_analysis(step, context)
            elif step.step_type == 'agent_execution':
                result = await self._execute_agent(step, context)
            elif step.step_type == 'pr_creation':
                result = await self._execute_pr_creation(step, context)
            elif step.step_type == 'deployment':
                result = await self._execute_deployment(step, context)
            elif step.step_type == 'validation':
                result = await self._execute_validation(step, context)
            elif step.step_type == 'notification':
                result = await self._execute_notification(step, context)
            elif step.step_type == 'conditional':
                result = await self._execute_conditional(step, context)
            elif step.step_type == 'parallel':
                result = await self._execute_parallel(step, context)
            else:
                raise Exception(f"Unknown step type: {step.step_type}")
            
            step.status = StepStatus.COMPLETED
            step.result = result
            step.completed_at = datetime.now()
            
            return result
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now()
            
            logger.error(f"Step {step.step_id} failed: {e}")
            
            # Check if we should retry
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = StepStatus.RETRYING
                logger.info(f"Retrying step {step.step_id} (attempt {step.retry_count})")
                
                # Wait before retry
                await asyncio.sleep(min(2 ** step.retry_count, 60))  # Exponential backoff
                
                return await self.execute_step(step, context)
            
            raise
    
    async def _execute_code_analysis(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code analysis step"""
        project_id = context['project_id']
        github_token = context['github_token']
        owner = context['owner']
        repo = context['repo']
        branch = step.config.get('branch', context.get('branch', 'main'))
        
        result = await self.analysis_service.analyze_repository(
            project_id, github_token, owner, repo, branch
        )
        
        return {
            'analysis_completed': True,
            'total_issues': result['total_issues'],
            'issues_by_severity': result['summary']['by_severity'],
            'issues_by_type': result['summary']['by_type']
        }
    
    async def _execute_agent(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Codegen agent step"""
        prompt = step.config['prompt']
        project_id = context['project_id']
        
        # Enhance prompt with context
        enhanced_prompt = await self.codegen_service.enhance_prompt(prompt, context.get('project'))
        
        # Execute agent
        task = await self.codegen_service.execute_agent(enhanced_prompt, project_id)
        
        # Wait for completion
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(5)
            await task.refresh_with_monitoring(self.websocket_manager)
        
        if task.status == 'failed':
            raise Exception(f"Agent execution failed: {task.result}")
        
        return {
            'agent_completed': True,
            'task_id': task.id,
            'result': task.result,
            'web_url': task.web_url
        }
    
    async def _execute_pr_creation(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PR creation step"""
        github_token = context['github_token']
        owner = context['owner']
        repo = context['repo']
        
        github_service = GitHubService(github_token)
        
        pr_data = {
            'title': step.config['title'],
            'body': step.config['body'],
            'head': step.config['head_branch'],
            'base': step.config.get('base_branch', 'main')
        }
        
        pr = await github_service.create_pull_request(owner, repo, **pr_data)
        
        return {
            'pr_created': True,
            'pr_number': pr['number'],
            'pr_url': pr['html_url'],
            'pr_data': pr
        }
    
    async def _execute_deployment(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deployment step"""
        environment = step.config['environment']
        project_id = context['project_id']
        
        github_data = {
            'repo': context['repo'],
            'owner': context['owner'],
            'commit_sha': context.get('commit_sha'),
            'branch': context.get('branch'),
            'clone_url': context.get('clone_url')
        }
        
        if environment == 'pr':
            pr_number = step.config['pr_number']
            result = await self.deployment_service.create_pr_environment(project_id, pr_number, github_data)
        elif environment == 'staging':
            result = await self.deployment_service.deploy_to_staging(project_id, github_data)
        elif environment == 'production':
            result = await self.deployment_service.deploy_to_production(project_id, github_data)
        else:
            raise Exception(f"Unknown deployment environment: {environment}")
        
        return {
            'deployment_completed': True,
            'deployment_id': result['deployment_id'],
            'deployment_url': result.get('url'),
            'environment': environment
        }
    
    async def _execute_validation(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation step"""
        validation_type = step.config['type']
        
        if validation_type == 'code_quality':
            # Check if code analysis found any critical issues
            analysis_results = context.get('analysis_results', {})
            critical_issues = analysis_results.get('issues_by_severity', {}).get('critical', 0)
            
            if critical_issues > 0:
                raise Exception(f"Validation failed: {critical_issues} critical issues found")
            
            return {'validation_passed': True, 'type': 'code_quality'}
            
        elif validation_type == 'deployment_health':
            deployment_url = step.config['deployment_url']
            
            # Check deployment health
            validation_result = await self.deployment_service._validate_deployment(deployment_url)
            
            if not validation_result['healthy']:
                raise Exception(f"Deployment validation failed: {validation_result['error']}")
            
            return {'validation_passed': True, 'type': 'deployment_health', 'result': validation_result}
            
        elif validation_type == 'pr_checks':
            # Check PR status checks
            github_token = context['github_token']
            owner = context['owner']
            repo = context['repo']
            pr_number = step.config['pr_number']
            
            github_service = GitHubService(github_token)
            checks = await github_service.get_pr_check_runs(owner, repo, pr_number)
            
            failed_checks = [check for check in checks.get('check_runs', []) if check['conclusion'] == 'failure']
            
            if failed_checks:
                raise Exception(f"PR validation failed: {len(failed_checks)} checks failed")
            
            return {'validation_passed': True, 'type': 'pr_checks', 'checks': checks}
        
        else:
            raise Exception(f"Unknown validation type: {validation_type}")
    
    async def _execute_notification(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification step"""
        notification_type = step.config['type']
        message = step.config['message']
        
        if notification_type == 'websocket':
            await self.websocket_manager.broadcast({
                'type': 'workflow_notification',
                'project_id': context['project_id'],
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        
        elif notification_type == 'github_comment':
            github_token = context['github_token']
            owner = context['owner']
            repo = context['repo']
            pr_number = step.config['pr_number']
            
            github_service = GitHubService(github_token)
            await github_service.create_pr_comment(owner, repo, pr_number, message)
        
        return {'notification_sent': True, 'type': notification_type}
    
    async def _execute_conditional(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional step"""
        condition = step.config['condition']
        
        # Evaluate condition based on context
        if condition['type'] == 'analysis_severity':
            analysis_results = context.get('analysis_results', {})
            severity_counts = analysis_results.get('issues_by_severity', {})
            threshold = condition['threshold']
            severity = condition['severity']
            
            if severity_counts.get(severity, 0) > threshold:
                return {'condition_met': True, 'action': 'continue'}
            else:
                return {'condition_met': False, 'action': 'skip'}
        
        return {'condition_met': False, 'action': 'skip'}
    
    async def _execute_parallel(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel steps"""
        parallel_steps = step.config['steps']
        
        # Create tasks for parallel execution
        tasks = []
        for parallel_step_config in parallel_steps:
            parallel_step = WorkflowStep(
                step_id=f"{step.step_id}_{parallel_step_config['name']}",
                name=parallel_step_config['name'],
                step_type=parallel_step_config['type'],
                config=parallel_step_config
            )
            tasks.append(self.execute_step(parallel_step, context))
        
        # Wait for all parallel steps to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for failures
        failures = [r for r in results if isinstance(r, Exception)]
        if failures:
            raise Exception(f"Parallel execution failed: {failures}")
        
        return {'parallel_completed': True, 'results': results}


class WorkflowEngine:
    """Main workflow orchestration engine"""
    
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowDefinition] = {}
        self.websocket_manager = WebSocketManager()
        
        # Initialize services
        self.services = {
            'codegen': CodegenService(
                token=settings.CODEGEN_TOKEN,
                org_id=settings.CODEGEN_ORG_ID,
                websocket_manager=self.websocket_manager
            ),
            'github': None,  # Will be initialized per workflow with token
            'analysis': CodeAnalysisService(self.websocket_manager),
            'deployment': ModalDeploymentService(self.websocket_manager),
            'websocket': self.websocket_manager
        }
        
        self.step_executor = StepExecutor(self.services)
    
    async def create_workflow_from_plan(self, project_id: str, plan: str, context: Dict[str, Any]) -> WorkflowDefinition:
        """Create workflow from AI-generated plan"""
        workflow_id = str(uuid.uuid4())
        workflow = WorkflowDefinition(workflow_id, "AI Generated Workflow", project_id)
        
        # Parse plan and create steps
        steps = await self._parse_plan_to_steps(plan, context)
        
        for step_config in steps:
            step = WorkflowStep(
                step_id=step_config['id'],
                name=step_config['name'],
                step_type=step_config['type'],
                config=step_config['config']
            )
            workflow.add_step(step, step_config.get('dependencies', []))
        
        # Store workflow
        self.active_workflows[workflow_id] = workflow
        
        return workflow
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            raise Exception(f"Workflow {workflow_id} not found")
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        try:
            # Broadcast workflow start
            await self.websocket_manager.send_workflow_update(workflow_id, workflow.project_id, {
                'status': 'running',
                'message': f'Starting workflow: {workflow.name}',
                'progress': 0
            })
            
            # Execute steps
            while not workflow.is_completed() and not workflow.has_failed():
                ready_steps = workflow.get_ready_steps()
                
                if not ready_steps:
                    # Check if we're stuck (no ready steps but not completed)
                    if not workflow.is_completed():
                        raise Exception("Workflow is stuck - no ready steps available")
                    break
                
                # Execute ready steps (can be parallel)
                step_tasks = []
                for step in ready_steps:
                    step_tasks.append(self._execute_step_with_updates(step, context, workflow))
                
                # Wait for current batch of steps to complete
                await asyncio.gather(*step_tasks, return_exceptions=True)
                
                # Update progress
                progress = workflow.get_progress_percentage()
                await self.websocket_manager.send_workflow_update(workflow_id, workflow.project_id, {
                    'status': 'running',
                    'progress': progress,
                    'completed_steps': [s.name for s in workflow.steps if s.status == StepStatus.COMPLETED]
                })
            
            # Determine final status
            if workflow.has_failed():
                workflow.status = WorkflowStatus.FAILED
                failed_steps = [s for s in workflow.steps if s.status == StepStatus.FAILED]
                workflow.error = f"Workflow failed at steps: {[s.name for s in failed_steps]}"
            else:
                workflow.status = WorkflowStatus.COMPLETED
            
            workflow.completed_at = datetime.now()
            
            # Broadcast completion
            await self.websocket_manager.send_workflow_update(workflow_id, workflow.project_id, {
                'status': workflow.status.value,
                'progress': 100 if workflow.status == WorkflowStatus.COMPLETED else workflow.get_progress_percentage(),
                'message': f'Workflow {workflow.status.value}',
                'error': workflow.error
            })
            
            return workflow.to_dict()
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.completed_at = datetime.now()
            
            await self.websocket_manager.send_workflow_update(workflow_id, workflow.project_id, {
                'status': 'failed',
                'error': str(e),
                'message': f'Workflow failed: {str(e)}'
            })
            
            logger.error(f"Workflow {workflow_id} failed: {e}")
            raise
    
    async def _execute_step_with_updates(self, step: WorkflowStep, context: Dict[str, Any], workflow: WorkflowDefinition):
        """Execute step with real-time updates"""
        try:
            # Broadcast step start
            await self.websocket_manager.send_workflow_update(workflow.workflow_id, workflow.project_id, {
                'status': 'running',
                'current_step': step.name,
                'step_status': 'running',
                'message': f'Executing step: {step.name}'
            })
            
            # Execute step
            result = await self.step_executor.execute_step(step, context)
            
            # Update context with step result
            context[f'step_{step.step_id}_result'] = result
            
            # Broadcast step completion
            await self.websocket_manager.send_workflow_update(workflow.workflow_id, workflow.project_id, {
                'status': 'running',
                'current_step': step.name,
                'step_status': 'completed',
                'message': f'Completed step: {step.name}'
            })
            
        except Exception as e:
            # Broadcast step failure
            await self.websocket_manager.send_workflow_update(workflow.workflow_id, workflow.project_id, {
                'status': 'running',
                'current_step': step.name,
                'step_status': 'failed',
                'error': str(e),
                'message': f'Step failed: {step.name}'
            })
            raise
    
    async def _parse_plan_to_steps(self, plan: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse AI-generated plan into workflow steps"""
        # This would use NLP or structured parsing to convert plan text into steps
        # For now, return a default workflow structure
        
        steps = [
            {
                'id': 'analyze_code',
                'name': 'Analyze Code Quality',
                'type': 'code_analysis',
                'config': {
                    'branch': context.get('branch', 'main')
                },
                'dependencies': []
            },
            {
                'id': 'validate_quality',
                'name': 'Validate Code Quality',
                'type': 'validation',
                'config': {
                    'type': 'code_quality'
                },
                'dependencies': ['analyze_code']
            },
            {
                'id': 'execute_agent',
                'name': 'Execute AI Agent',
                'type': 'agent_execution',
                'config': {
                    'prompt': context.get('requirements', 'Improve code quality and fix issues')
                },
                'dependencies': ['validate_quality']
            },
            {
                'id': 'create_pr',
                'name': 'Create Pull Request',
                'type': 'pr_creation',
                'config': {
                    'title': 'AI-Generated Improvements',
                    'body': 'Automated improvements generated by AI agent',
                    'head_branch': f"ai-improvements-{int(datetime.now().timestamp())}",
                    'base_branch': 'main'
                },
                'dependencies': ['execute_agent']
            },
            {
                'id': 'deploy_staging',
                'name': 'Deploy to Staging',
                'type': 'deployment',
                'config': {
                    'environment': 'staging'
                },
                'dependencies': ['create_pr']
            },
            {
                'id': 'validate_deployment',
                'name': 'Validate Staging Deployment',
                'type': 'validation',
                'config': {
                    'type': 'deployment_health',
                    'deployment_url': '${step_deploy_staging_result.deployment_url}'
                },
                'dependencies': ['deploy_staging']
            },
            {
                'id': 'notify_completion',
                'name': 'Notify Completion',
                'type': 'notification',
                'config': {
                    'type': 'websocket',
                    'message': 'Workflow completed successfully!'
                },
                'dependencies': ['validate_deployment']
            }
        ]
        
        return steps
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.PAUSED
            return True
        return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.PAUSED:
            workflow.status = WorkflowStatus.RUNNING
            # Continue execution in background
            asyncio.create_task(self.execute_workflow(workflow_id, {}))
            return True
        return False
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow and workflow.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.now()
            return True
        return False
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow status"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            return workflow.to_dict()
        return None
    
    async def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        return [workflow.to_dict() for workflow in self.active_workflows.values()]

