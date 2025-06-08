import os
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.configs.models.secrets import SecretsConfig
from graph_sitter import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

from ..github.github import GitHub
from ..linear.linear import Linear
from ..slack.slack import Slack
from ..circleci.circleci import CircleCI
from ..modal.base import CodebaseEventsApp

# Import new orchestration components
from ..prefect.flow import PrefectFlow
from ..controlflow.orchestrator import FlowOrchestrator
from ..grainchain.quality_gates import QualityGateManager
from ..grainchain.sandbox_manager import SandboxManager
from ..graph_sitter.analysis.main_analyzer import comprehensive_analysis

logger = get_logger(__name__)


class ContextenApp:
    """A FastAPI-based application for handling various code-related events and orchestrating contexten extensions."""

    github: GitHub
    linear: Linear
    slack: Slack
    circleci: CircleCI
    modal: CodebaseEventsApp
    
    # New orchestration components
    prefect_flow: Optional[PrefectFlow]
    flow_orchestrator: Optional[FlowOrchestrator]
    quality_gate_manager: Optional[QualityGateManager]
    sandbox_manager: Optional[SandboxManager]
    graph_sitter_quality_gates: Optional[list]

    def __init__(self, name: str, repo: Optional[str] = None, tmp_dir: str = "/tmp/contexten", commit: str | None = "latest"):
        self.name = name
        self.tmp_dir = tmp_dir

        # Create the FastAPI app
        self.app = FastAPI(title=name)

        # Initialize existing event handlers
        self.github = GitHub(self)
        self.linear = Linear(self)
        self.slack = Slack(self)
        self.circleci = CircleCI(self)
        self.modal = CodebaseEventsApp()
        
        # Initialize new orchestration components
        self.prefect_flow = None
        self.flow_orchestrator = None
        self.quality_gate_manager = None
        self.sandbox_manager = None
        self.graph_sitter_quality_gates = None
        
        # Set repository and commit info
        self.repo = repo
        self.commit = commit
        
        # Initialize codebase cache
        self._codebase_cache = {}
        
        # Initialize Codegen SDK integration
        self._codegen_agent = None
        self._codegen_config = {
            'org_id': os.getenv('CODEGEN_ORG_ID'),
            'token': os.getenv('CODEGEN_API_TOKEN'),
            'base_url': os.getenv('CODEGEN_BASE_URL', 'https://api.codegen.com')
        }
        
        # Register unified API endpoints
        self._register_unified_endpoints()
        
        logger.info(f"ContextenApp '{name}' initialized with comprehensive orchestration")

    async def initialize_orchestration(self):
        """Initialize the orchestration components for seamless tool transitions."""
        logger.info("Initializing orchestration components...")
        
        try:
            # Initialize Grainchain components
            from ..grainchain.config import GrainchainIntegrationConfig
            grainchain_config = GrainchainIntegrationConfig()
            
            self.quality_gate_manager = QualityGateManager(grainchain_config)
            self.sandbox_manager = SandboxManager(grainchain_config)
            
            # Initialize enhanced Graph_sitter quality gates
            from ..grainchain.graph_sitter_integration import create_graph_sitter_quality_gates
            self.graph_sitter_quality_gates = create_graph_sitter_quality_gates(
                quality_manager=self.quality_gate_manager,
                sandbox_manager=self.sandbox_manager
            )
            
            # Initialize enhanced ControlFlow orchestrator
            from ..controlflow.codegen_integration import create_codegen_flow_orchestrator
            self.flow_orchestrator = create_codegen_flow_orchestrator()
            
            # Register Codegen agents with ControlFlow
            if self._codegen_config['org_id'] and self._codegen_config['token']:
                self.flow_orchestrator.register_codegen_agent(
                    agent_id="primary_agent",
                    name="Primary Codegen Agent",
                    org_id=self._codegen_config['org_id'],
                    token=self._codegen_config['token'],
                    base_url=self._codegen_config['base_url']
                )
            
            # Initialize enhanced Prefect workflow pipeline
            from ..prefect.workflow_pipeline import create_prefect_workflow_pipeline
            self.prefect_pipeline = create_prefect_workflow_pipeline("contexten_main_pipeline")
            
            # Initialize Codegen workflow integration
            await self._initialize_codegen_integration()
            
            logger.info("Enhanced orchestration components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestration: {e}")
            raise

    async def _initialize_codegen_integration(self):
        """Initialize Codegen SDK integration with overlay system."""
        try:
            # Apply Codegen overlay if not already applied
            from ..codegen.apply_overlay import OverlayApplicator
            
            applicator = OverlayApplicator()
            try:
                applicator.detect_package()
                if not applicator.applied:
                    applicator.apply_overlay()
                    logger.info("Codegen overlay applied successfully")
            except Exception as e:
                logger.warning(f"Codegen overlay application failed: {e}")
            
            # Initialize Codegen agent if credentials available
            if self._codegen_config['org_id'] and self._codegen_config['token']:
                from codegen.agents.agent import Agent
                
                self._codegen_agent = Agent(
                    org_id=self._codegen_config['org_id'],
                    token=self._codegen_config['token'],
                    base_url=self._codegen_config['base_url']
                )
                
                logger.info("Codegen SDK agent initialized")
            else:
                logger.warning("Codegen credentials not found - some features will be limited")
                
        except ImportError as e:
            logger.warning(f"Codegen SDK not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Codegen integration: {e}")

    async def execute_workflow_pipeline(self, project_id: str, requirements: str) -> dict:
        """Execute complete workflow pipeline: Planning -> Orchestration -> Execution -> Quality Gates."""
        logger.info(f"Starting enhanced workflow pipeline for project {project_id}")
        
        workflow_result = {
            'project_id': project_id,
            'status': 'running',
            'stages': {
                'planning': {'status': 'pending'},
                'orchestration': {'status': 'pending'},
                'execution': {'status': 'pending'},
                'quality_gates': {'status': 'pending'}
            },
            'results': {}
        }
        
        try:
            # Use enhanced Prefect workflow pipeline for orchestration
            if hasattr(self, 'prefect_pipeline') and self.prefect_pipeline:
                logger.info("Using enhanced Prefect workflow pipeline")
                
                # Create pipeline context
                from ..prefect.workflow_pipeline import PipelineContext
                
                context = PipelineContext(
                    project_id=project_id,
                    requirements=requirements,
                    config={
                        'validation_level': 'moderate',
                        'parallel_execution': True,
                        'quality_gates_enabled': True
                    },
                    variables={
                        'codebase_path': self.repo or '.',
                        'analysis_types': ['comprehensive', 'security', 'complexity']
                    }
                )
                
                # Execute enhanced pipeline
                pipeline_result = await self.prefect_pipeline.execute_pipeline(
                    context=context,
                    codegen_config=self._codegen_config,
                    controlflow_config={
                        'agents': [{
                            'id': 'primary_agent',
                            'name': 'Primary Codegen Agent',
                            'org_id': self._codegen_config['org_id'],
                            'token': self._codegen_config['token'],
                            'base_url': self._codegen_config['base_url']
                        }]
                    } if self._codegen_config['org_id'] and self._codegen_config['token'] else None,
                    grainchain_config={
                        'sandbox_provider': 'docker',
                        'analysis_timeout': 1800,
                        'quality_thresholds': {
                            'max_complexity': 15,
                            'max_security_issues': 2,
                            'max_critical_issues': 1
                        }
                    }
                )
                
                # Map pipeline results to workflow result format
                workflow_result.update({
                    'status': pipeline_result['status'],
                    'stages': {
                        stage_name: {
                            'status': stage_data.status.value if hasattr(stage_data, 'status') else 'completed',
                            'result': stage_data.result if hasattr(stage_data, 'result') else stage_data,
                            'duration': stage_data.duration if hasattr(stage_data, 'duration') else 0
                        }
                        for stage_name, stage_data in pipeline_result.get('stages', {}).items()
                    },
                    'results': {
                        'pipeline_metrics': pipeline_result.get('overall_metrics', {}),
                        'flow_run_id': pipeline_result.get('flow_run_id'),
                        'total_duration': pipeline_result.get('duration', 0)
                    }
                })
                
                logger.info(f"Enhanced workflow pipeline completed for project {project_id}")
                
            else:
                # Fallback to original pipeline implementation
                logger.warning("Enhanced pipeline not available, using fallback implementation")
                
                # Stage 1: Planning with Codegen SDK
                logger.info("Stage 1: Planning with Codegen SDK")
                planning_result = await self._execute_planning_stage(requirements)
                workflow_result['stages']['planning'] = {'status': 'completed', 'result': planning_result}
                workflow_result['results']['plan'] = planning_result
                
                # Stage 2: Orchestration with ControlFlow
                logger.info("Stage 2: Orchestration with ControlFlow")
                orchestration_result = await self._execute_orchestration_stage(planning_result)
                workflow_result['stages']['orchestration'] = {'status': 'completed', 'result': orchestration_result}
                workflow_result['results']['orchestration'] = orchestration_result
                
                # Stage 3: Execution with Prefect + Codegen
                logger.info("Stage 3: Execution with Prefect + Codegen")
                execution_result = await self._execute_execution_stage(orchestration_result)
                workflow_result['stages']['execution'] = {'status': 'completed', 'result': execution_result}
                workflow_result['results']['execution'] = execution_result
                
                # Stage 4: Quality Gates with Grainchain + Graph_sitter
                logger.info("Stage 4: Quality Gates with Grainchain + Graph_sitter")
                quality_result = await self._execute_quality_gates_stage(execution_result)
                workflow_result['stages']['quality_gates'] = {'status': 'completed', 'result': quality_result}
                workflow_result['results']['quality'] = quality_result
                
                workflow_result['status'] = 'completed'
                logger.info(f"Fallback workflow pipeline completed for project {project_id}")
            
        except Exception as e:
            logger.error(f"Workflow pipeline failed: {e}")
            workflow_result['status'] = 'failed'
            workflow_result['error'] = str(e)
            
        return workflow_result

    async def _execute_planning_stage(self, requirements: str) -> dict:
        """Execute planning stage using Codegen SDK."""
        if not self._codegen_agent:
            raise Exception("Codegen agent not initialized")
        
        planning_prompt = f"""
        Create a detailed implementation plan for the following requirements:
        
        {requirements}
        
        Please provide:
        1. List of specific tasks to be completed
        2. Dependencies between tasks
        3. Estimated complexity for each task
        4. Required tools/integrations for each task
        5. Quality gates and validation criteria
        
        Format the response as a structured plan that can be executed by automated agents.
        """
        
        try:
            task = self._codegen_agent.run(planning_prompt)
            
            # Wait for task completion with timeout
            import time
            timeout = 300  # 5 minutes
            start_time = time.time()
            
            while task.status not in ['completed', 'failed'] and (time.time() - start_time) < timeout:
                time.sleep(5)
                task.refresh()
            
            if task.status == 'completed':
                return {
                    'task_id': task.id,
                    'status': task.status,
                    'plan': task.result if hasattr(task, 'result') else 'Plan generated successfully',
                    'duration': time.time() - start_time
                }
            else:
                raise Exception(f"Planning task failed or timed out: {task.status}")
                
        except Exception as e:
            logger.error(f"Planning stage failed: {e}")
            raise

    async def _execute_orchestration_stage(self, planning_result: dict) -> dict:
        """Execute orchestration stage using ControlFlow."""
        if not self.flow_orchestrator:
            raise Exception("Flow orchestrator not initialized")
        
        # Convert planning result to workflow definition
        workflow_def = {
            'name': 'contexten_workflow',
            'plan': planning_result.get('plan', ''),
            'tasks': self._extract_tasks_from_plan(planning_result),
            'dependencies': self._extract_dependencies_from_plan(planning_result)
        }
        
        try:
            # Create a simple workflow for orchestration
            from ..controlflow.orchestrator import FlowOrchestrator
            
            # Execute workflow orchestration
            orchestration_result = await self.flow_orchestrator.execute_workflow(
                workflow=None,  # We'll create a simple workflow object
                workflow_def=workflow_def
            )
            
            return {
                'workflow_def': workflow_def,
                'orchestration_result': orchestration_result,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Orchestration stage failed: {e}")
            raise

    async def _execute_execution_stage(self, orchestration_result: dict) -> dict:
        """Execute tasks using Prefect + Codegen integration."""
        if not self._codegen_agent:
            raise Exception("Codegen agent not initialized")
        
        workflow_def = orchestration_result.get('workflow_def', {})
        tasks = workflow_def.get('tasks', [])
        
        execution_results = []
        
        try:
            for task in tasks:
                logger.info(f"Executing task: {task.get('name', 'unnamed')}")
                
                # Execute task using Codegen SDK
                task_prompt = f"""
                Execute the following task:
                
                Task: {task.get('name', 'unnamed')}
                Description: {task.get('description', '')}
                Requirements: {task.get('requirements', '')}
                
                Please implement this task and provide the results.
                """
                
                codegen_task = self._codegen_agent.run(task_prompt)
                
                # Wait for completion
                import time
                timeout = 600  # 10 minutes per task
                start_time = time.time()
                
                while codegen_task.status not in ['completed', 'failed'] and (time.time() - start_time) < timeout:
                    time.sleep(10)
                    codegen_task.refresh()
                
                task_result = {
                    'task_name': task.get('name', 'unnamed'),
                    'task_id': codegen_task.id,
                    'status': codegen_task.status,
                    'duration': time.time() - start_time
                }
                
                if codegen_task.status == 'completed':
                    task_result['result'] = codegen_task.result if hasattr(codegen_task, 'result') else 'Task completed'
                else:
                    task_result['error'] = f"Task failed or timed out: {codegen_task.status}"
                
                execution_results.append(task_result)
            
            return {
                'tasks_executed': len(execution_results),
                'results': execution_results,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Execution stage failed: {e}")
            raise

    async def _execute_quality_gates_stage(self, execution_result: dict) -> dict:
        """Execute quality gates using Grainchain + Graph_sitter."""
        if not self.quality_gate_manager or not self.sandbox_manager:
            raise Exception("Quality gate components not initialized")
        
        try:
            # Get codebase for analysis
            codebase = await self._get_or_create_codebase()
            
            # Run Graph_sitter comprehensive analysis
            logger.info("Running Graph_sitter comprehensive analysis")
            analysis_result = comprehensive_analysis(codebase)
            
            # Run Grainchain quality gates
            logger.info("Running Grainchain quality gates")
            from ..grainchain.grainchain_types import QualityGateType
            
            quality_gates = [
                QualityGateType.UNIT_TESTS,
                QualityGateType.INTEGRATION_TESTS,
                QualityGateType.CODE_QUALITY,
                QualityGateType.SECURITY_SCAN
            ]
            
            quality_results = []
            for gate_type in quality_gates:
                try:
                    gate_result = await self.quality_gate_manager.execute_quality_gate(
                        gate_type=gate_type,
                        codebase_path=str(codebase.path),
                        context={'execution_result': execution_result}
                    )
                    quality_results.append(gate_result)
                except Exception as e:
                    logger.warning(f"Quality gate {gate_type} failed: {e}")
                    quality_results.append({
                        'gate_type': gate_type,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return {
                'graph_sitter_analysis': analysis_result,
                'quality_gates': quality_results,
                'overall_status': 'passed' if all(r.get('status') == 'passed' for r in quality_results) else 'failed',
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Quality gates stage failed: {e}")
            raise

    def _extract_tasks_from_plan(self, planning_result: dict) -> list:
        """Extract tasks from planning result."""
        # Simple task extraction - in real implementation, this would parse the plan
        return [
            {
                'name': 'implement_core_functionality',
                'description': 'Implement the core functionality based on requirements',
                'requirements': planning_result.get('plan', '')
            },
            {
                'name': 'add_tests',
                'description': 'Add comprehensive tests for the implementation',
                'requirements': 'Create unit and integration tests'
            },
            {
                'name': 'update_documentation',
                'description': 'Update documentation to reflect changes',
                'requirements': 'Update README and API documentation'
            }
        ]

    def _extract_dependencies_from_plan(self, planning_result: dict) -> dict:
        """Extract task dependencies from planning result."""
        return {
            'implement_core_functionality': [],
            'add_tests': ['implement_core_functionality'],
            'update_documentation': ['implement_core_functionality', 'add_tests']
        }

    async def _get_or_create_codebase(self) -> Codebase:
        """Get or create codebase instance for analysis."""
        if self.repo and self.repo not in self._codebase_cache:
            try:
                # Create codebase instance
                codebase = Codebase(self.repo)
                self._codebase_cache[self.repo] = codebase
                logger.info(f"Created codebase instance for {self.repo}")
            except Exception as e:
                logger.error(f"Failed to create codebase: {e}")
                # Create a temporary codebase for current directory
                codebase = Codebase(".")
                self._codebase_cache["."] = codebase
        
        return self._codebase_cache.get(self.repo, self._codebase_cache.get(".", Codebase(".")))

    def _register_unified_endpoints(self):
        """Register unified API endpoints for all extensions."""
        
        @self.app.get("/")
        async def root():
            return {"message": f"ContextenApp {self.name} - Unified Orchestration Hub"}
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for all components."""
            health_status = {
                'status': 'healthy',
                'components': {
                    'github': 'healthy' if self.github else 'unavailable',
                    'linear': 'healthy' if self.linear else 'unavailable',
                    'slack': 'healthy' if self.slack else 'unavailable',
                    'circleci': 'healthy' if self.circleci else 'unavailable',
                    'codegen': 'healthy' if self._codegen_agent else 'unavailable',
                    'quality_gates': 'healthy' if self.quality_gate_manager else 'unavailable',
                    'orchestrator': 'healthy' if self.flow_orchestrator else 'unavailable'
                }
            }
            return health_status
        
        @self.app.post("/workflow/execute")
        async def execute_workflow(request: Request):
            """Execute complete workflow pipeline."""
            data = await request.json()
            project_id = data.get('project_id')
            requirements = data.get('requirements')
            
            if not project_id or not requirements:
                return {'error': 'project_id and requirements are required'}
            
            try:
                result = await self.execute_workflow_pipeline(project_id, requirements)
                return result
            except Exception as e:
                return {'error': str(e), 'status': 'failed'}
        
        @self.app.get("/workflow/status/{project_id}")
        async def get_workflow_status(project_id: str):
            """Get workflow status for a project."""
            # Implementation would track workflow status
            return {'project_id': project_id, 'status': 'not_implemented'}
        
        @self.app.post("/analysis/comprehensive")
        async def run_comprehensive_analysis(request: Request):
            """Run comprehensive codebase analysis."""
            try:
                codebase = await self._get_or_create_codebase()
                analysis_result = comprehensive_analysis(codebase)
                return {'status': 'completed', 'analysis': analysis_result}
            except Exception as e:
                return {'error': str(e), 'status': 'failed'}

    def parse_repo(self) -> None:
        # Parse initial repos if provided
        if self.repo:
            self._parse_repo(self.repo, self.commit)

    def _parse_repo(self, repo_name: str, commit: str | None = None) -> None:
        """Parse a GitHub repository and cache it.

        Args:
            repo_name: Repository name in format "owner/repo"
        """
        try:
            logger.info(f"[CODEBASE] Parsing repository: {repo_name}")
            config = CodebaseConfig(sync_enabled=True)
            secrets = SecretsConfig(github_token=os.environ.get("GITHUB_ACCESS_TOKEN"), linear_api_key=os.environ.get("LINEAR_ACCESS_TOKEN"))
            self.codebase = Codebase.from_repo(repo_full_name=repo_name, tmp_dir=self.tmp_dir, commit=commit, config=config, secrets=secrets)
            logger.info(f"[CODEBASE] Successfully parsed and cached: {repo_name}")
        except Exception as e:
            logger.exception(f"[CODEBASE] Failed to parse repository {repo_name}: {e!s}")
            raise

    def get_codebase(self) -> Codebase:
        """Get a cached codebase by repository name.

        Args:
            repo_name: Repository name in format "owner/repo"

        Returns:
            The cached Codebase instance

        Raises:
            KeyError: If the repository hasn't been parsed
        """
        if not self.codebase:
            msg = "Repository has not been parsed"
            raise KeyError(msg)
        return self.codebase

    def add_repo(self, repo_name: str) -> None:
        """Add a new repository to parse and cache.

        Args:
            repo_name: Repository name in format "owner/repo"
        """
        self._parse_repo(repo_name)

    async def simulate_event(self, provider: str, event_type: str, payload: dict) -> Any:
        """Simulate an event without running the server.

        Args:
            provider: The event provider ('slack', 'github', or 'linear')
            event_type: The type of event to simulate
            payload: The event payload

        Returns:
            The handler's response
        """
        provider_map = {"slack": self.slack, "github": self.github, "linear": self.linear}

        if provider not in provider_map:
            msg = f"Unknown provider: {provider}. Must be one of {list(provider_map.keys())}"
            raise ValueError(msg)

        handler = provider_map[provider]
        return await handler.handle(payload)

    async def root(self):
        """Render the main page."""
        return """
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Contexten</title>
                    <style>
                        body {
                            margin: 0;
                            height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            background-color: #1a1a1a;
                            color: #ffffff;
                        }
                        h1 {
                            font-size: 4rem;
                            font-weight: 700;
                            letter-spacing: -0.05em;
                        }
                    </style>
                </head>
                <body>
                    <h1>contexten</h1>
                </body>
            </html>
            """

    async def handle_slack_event(self, request: Request):
        """Handle incoming Slack events."""
        payload = await request.json()
        return await self.slack.handle(payload)

    async def handle_github_event(self, request: Request):
        """Handle incoming GitHub events."""
        payload = await request.json()
        return await self.github.handle(payload, request)

    async def handle_linear_event(self, request: Request):
        """Handle incoming Linear events."""
        payload = await request.json()
        return await self.linear.handle(payload)

    def _setup_routes(self):
        """Set up the FastAPI routes for different event types."""

        @self.app.get("/", response_class=HTMLResponse)
        async def _root():
            return await self.root()

        # @self.app.post("/{org}/{repo}/slack/events")
        @self.app.post("/slack/events")
        async def _handle_slack_event(request: Request):
            return await self.handle_slack_event(request)

        # @self.app.post("/{org}/{repo}/github/events")
        @self.app.post("/github/events")
        async def _handle_github_event(request: Request):
            return await self.handle_github_event(request)

        # @self.app.post("/{org}/{repo}/linear/events")
        @self.app.post("/linear/events")
        async def handle_linear_event(request: Request):
            return await self.handle_linear_event(request)

    def _setup_webhook_routes(self):
        """Setup webhook routes for all integrated services."""
        
        @self.app.post("/webhooks/github")
        async def github_webhook(request: Request):
            payload = await request.json()
            return await self.github.handle(payload, request)

        @self.app.post("/webhooks/linear")
        async def linear_webhook(request: Request):
            payload = await request.json()
            return await self.linear.handle(payload, request)

        @self.app.post("/webhooks/slack")
        async def slack_webhook(request: Request):
            payload = await request.json()
            return await self.slack.handle(payload, request)

        @self.app.post("/webhooks/circleci")
        async def circleci_webhook(request: Request):
            payload = await request.json()
            return await self.circleci.handle(payload, request)

    async def initialize_services(self):
        """Initialize all services with proper error handling."""
        services = {
            'github': self.github,
            'linear': self.linear,
            'slack': self.slack,
            'circleci': self.circleci
        }
        
        for service_name, service in services.items():
            try:
                if hasattr(service, 'initialize'):
                    await service.initialize()
                logger.info(f"✅ {service_name.title()} service initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {service_name} service: {e}")

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the FastAPI application."""
        import uvicorn

        uvicorn.run(self.app, host=host, port=port, **kwargs)
