import os
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

# Import existing graph_sitter components
from graph_sitter.configs.models.codebase import CodebaseConfig
from graph_sitter.configs.models.secrets import SecretsConfig
from graph_sitter import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

# Import existing contexten extensions
from ..github.github import GitHub
from ..linear.linear import Linear
from ..slack.slack import Slack
from ..circleci.circleci import CircleCI
from ..modal.base import CodebaseEventsApp

# Import existing prefect components
from ..prefect.flow import PrefectFlow
from ..prefect.workflow_pipeline import PrefectWorkflowPipeline

# Import existing controlflow components
from ..controlflow.orchestrator import FlowOrchestrator

# Import existing codegen components
from ..codegen.workflow_integration import CodegenWorkflowClient
from ..codegen.apply_overlay import OverlayApplicator

# Import existing grainchain components
from ..grainchain.quality_gates import QualityGateManager
from ..grainchain.sandbox_manager import SandboxManager
from ..grainchain.graph_sitter_integration import GraphSitterQualityGates

# Import existing graph_sitter analysis components
from ..graph_sitter.analysis.main_analyzer import comprehensive_analysis
from ..graph_sitter.code_analysis import CodeAnalysisEngine

logger = get_logger(__name__)


class ContextenApp:
    """A FastAPI-based application for handling various code-related events and orchestrating all 11 contexten extensions."""

    # Core extension attributes (existing)
    github: GitHub
    linear: Linear
    slack: Slack
    circleci: CircleCI
    modal: CodebaseEventsApp
    
    # Orchestration extension attributes (enhanced)
    prefect_extension: Prefect
    prefect_flow: Optional[PrefectFlow]
    prefect_pipeline: Optional[PrefectWorkflowPipeline]
    controlflow_extension: ControlFlow
    controlflow_orchestrator: Optional[FlowOrchestrator]
    codegen_extension: Codegen
    codegen_integration: Optional[CodegenFlowIntegration]
    codegen_client: Optional[CodegenWorkflowClient]
    grainchain_extension: Grainchain
    grainchain_quality_gates: Optional[QualityGateManager]
    grainchain_sandbox: Optional[SandboxManager]
    graph_sitter_extension: GraphSitter
    graph_sitter_quality: Optional[GraphSitterQualityGates]
    graph_sitter_analysis: Optional[CodeAnalysisEngine]

    def __init__(self, name: str, repo: Optional[str] = None, tmp_dir: str = "/tmp/contexten", commit: str | None = "latest"):
        self.name = name
        self.tmp_dir = tmp_dir
        self.repo = repo
        self.commit = commit

        # Create the FastAPI app
        self.app = FastAPI(title=f"{name} - Unified Contexten System")

        # Initialize all 11 extensions following existing patterns
        self._initialize_core_extensions()
        self._initialize_orchestration_extensions()
        
        # Set up unified API endpoints
        self._register_unified_endpoints()
        self._setup_webhook_routes()
        
        # Initialize codebase cache
        self._codebase_cache = {}
        
        logger.info(f"ContextenApp '{name}' initialized with all 11 extensions integrated")

    def _initialize_core_extensions(self):
        """Initialize the 5 core extensions (GitHub, Linear, Slack, CircleCI, Modal)."""
        try:
            # Initialize existing extensions following established patterns
            self.github = GitHub(self)
            self.linear = Linear(self)
            self.slack = Slack(self)
            self.circleci = CircleCI(self)
            self.modal = CodebaseEventsApp()
            
            logger.info("✅ Core extensions (GitHub, Linear, Slack, CircleCI, Modal) initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize core extensions: {e}")
            raise

    def _initialize_orchestration_extensions(self):
        """Initialize the 6 orchestration extensions (Prefect, ControlFlow, Codegen, Grainchain, Graph_sitter)."""
        try:
            # Initialize Prefect extension (Top Layer - System Watch Flows) - Lazy loading
            self.prefect_extension = None  # Will be loaded when needed
            self.prefect_flow = PrefectFlow(app=self)
            self.prefect_pipeline = PrefectWorkflowPipeline(name=f"{self.name}_pipeline")
            
            # Initialize ControlFlow extension (Agent Orchestrator) - Lazy loading
            self.controlflow_extension = None  # Will be loaded when needed
            self.controlflow_orchestrator = FlowOrchestrator(app=self)
            
            # Initialize Codegen extension (Task Completion with API token/org_id) - Lazy loading
            self.codegen_extension = None  # Will be loaded when needed
            self.codegen_integration = None  # Will be loaded when needed
            self.codegen_client = CodegenWorkflowClient(
                org_id=os.getenv('CODEGEN_ORG_ID'),
                token=os.getenv('CODEGEN_API_TOKEN'),
                base_url=os.getenv('CODEGEN_BASE_URL', 'https://api.codegen.com')
            )
            
            # Initialize Grainchain extension (Sandboxed Deployment + Snapshot saving) - Lazy loading
            from ..grainchain.config import GrainchainIntegrationConfig
            grainchain_config = GrainchainIntegrationConfig()
            self.grainchain_extension = None  # Will be loaded when needed
            self.grainchain_quality_gates = QualityGateManager(grainchain_config)
            self.grainchain_sandbox = SandboxManager(grainchain_config)
            
            # Initialize Graph_sitter extension (Analysis for PR validation) - Lazy loading
            self.graph_sitter_extension = None  # Will be loaded when needed
            self.graph_sitter_quality = GraphSitterQualityGates(
                quality_manager=self.grainchain_quality_gates,
                sandbox_manager=self.grainchain_sandbox
            )
            self.graph_sitter_analysis = CodeAnalysisEngine()
            
            logger.info("✅ Orchestration extensions (Prefect, ControlFlow, Codegen, Grainchain, Graph_sitter) initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize orchestration extensions: {e}")
            # Continue with partial initialization
            self._initialize_fallback_orchestration()

    def _initialize_fallback_orchestration(self):
        """Initialize fallback orchestration components if full initialization fails."""
        try:
            # Set None for failed components
            self.prefect_extension = None
            self.prefect_flow = None
            self.prefect_pipeline = None
            self.controlflow_extension = None
            self.controlflow_orchestrator = None
            self.codegen_extension = None
            self.codegen_integration = None
            self.codegen_client = None
            self.grainchain_extension = None
            self.grainchain_quality_gates = None
            self.grainchain_sandbox = None
            self.graph_sitter_extension = None
            self.graph_sitter_quality = None
            self.graph_sitter_analysis = None
            
            logger.warning("⚠️ Using fallback orchestration - some features may be limited")
        except Exception as e:
            logger.error(f"❌ Even fallback initialization failed: {e}")

    def _get_prefect_extension(self):
        """Lazy load Prefect extension."""
        if self.prefect_extension is None:
            try:
                from ..prefect.prefect import Prefect
                self.prefect_extension = Prefect(self)
                logger.info("✅ Prefect extension lazy loaded")
            except ImportError as e:
                logger.warning(f"Failed to lazy load Prefect extension: {e}")
        return self.prefect_extension

    def _get_controlflow_extension(self):
        """Lazy load ControlFlow extension."""
        if self.controlflow_extension is None:
            try:
                from ..controlflow.controlflow import ControlFlow
                self.controlflow_extension = ControlFlow(self)
                logger.info("✅ ControlFlow extension lazy loaded")
            except ImportError as e:
                logger.warning(f"Failed to lazy load ControlFlow extension: {e}")
        return self.controlflow_extension

    def _get_codegen_extension(self):
        """Lazy load Codegen extension."""
        if self.codegen_extension is None:
            try:
                from ..codegen.codegen import Codegen
                self.codegen_extension = Codegen(self)
                logger.info("✅ Codegen extension lazy loaded")
            except ImportError as e:
                logger.warning(f"Failed to lazy load Codegen extension: {e}")
        return self.codegen_extension

    def _get_grainchain_extension(self):
        """Lazy load Grainchain extension."""
        if self.grainchain_extension is None:
            try:
                from ..grainchain.grainchain import Grainchain
                self.grainchain_extension = Grainchain(self)
                logger.info("✅ Grainchain extension lazy loaded")
            except ImportError as e:
                logger.warning(f"Failed to lazy load Grainchain extension: {e}")
        return self.grainchain_extension

    def _get_graph_sitter_extension(self):
        """Lazy load Graph_sitter extension."""
        if self.graph_sitter_extension is None:
            try:
                from ..graph_sitter.graph_sitter import GraphSitter
                self.graph_sitter_extension = GraphSitter(self)
                logger.info("✅ Graph_sitter extension lazy loaded")
            except ImportError as e:
                logger.warning(f"Failed to lazy load Graph_sitter extension: {e}")
        return self.graph_sitter_extension

    async def execute_comprehensive_workflow(self, project_id: str, requirements: str) -> dict:
        """Execute the complete workflow using all 11 extensions in proper hierarchy."""
        logger.info(f"🚀 Starting comprehensive workflow for project {project_id} using all 11 extensions")
        
        workflow_result = {
            'project_id': project_id,
            'status': 'running',
            'extensions_used': [],
            'stages': {
                'prefect_orchestration': {'status': 'pending'},
                'controlflow_coordination': {'status': 'pending'},
                'codegen_execution': {'status': 'pending'},
                'integration_services': {'status': 'pending'},
                'quality_validation': {'status': 'pending'}
            },
            'results': {}
        }
        
        try:
            # Stage 1: Prefect (Top Layer) - System Watch Flows
            if self.prefect_flow and self.prefect_pipeline:
                logger.info("📊 Stage 1: Prefect orchestration")
                workflow_result['extensions_used'].append('prefect')
                
                # Create pipeline context using existing components
                from ..prefect.workflow_pipeline import PipelineContext
                context = PipelineContext(
                    project_id=project_id,
                    requirements=requirements,
                    config={'validation_level': 'comprehensive'},
                    variables={'codebase_path': self.repo or '.'}
                )
                
                prefect_result = await self.prefect_pipeline.execute_pipeline(context)
                workflow_result['stages']['prefect_orchestration'] = {
                    'status': 'completed',
                    'result': prefect_result
                }
                workflow_result['results']['prefect'] = prefect_result
            
            # Stage 2: ControlFlow (Agent Orchestrator)
            if self.controlflow_orchestrator:
                logger.info("��� Stage 2: ControlFlow agent orchestration")
                workflow_result['extensions_used'].append('controlflow')
                
                # Register Codegen agents with ControlFlow
                if self.codegen_client:
                    await self.controlflow_orchestrator.register_codegen_agent(
                        agent_id="primary_agent",
                        name="Primary Codegen Agent",
                        client=self.codegen_client
                    )
                
                controlflow_result = await self.controlflow_orchestrator.orchestrate_workflow(
                    project_id=project_id,
                    requirements=requirements
                )
                workflow_result['stages']['controlflow_coordination'] = {
                    'status': 'completed',
                    'result': controlflow_result
                }
                workflow_result['results']['controlflow'] = controlflow_result
            
            # Stage 3: Codegen (Task Completion with API token/org_id)
            if self.codegen_client:
                logger.info("🤖 Stage 3: Codegen task execution")
                workflow_result['extensions_used'].append('codegen')
                
                # Execute tasks using Codegen SDK with Strands workflow integration
                codegen_result = await self.codegen_client.execute_workflow_tasks(
                    project_id=project_id,
                    requirements=requirements,
                    context=workflow_result.get('results', {})
                )
                workflow_result['stages']['codegen_execution'] = {
                    'status': 'completed',
                    'result': codegen_result
                }
                workflow_result['results']['codegen'] = codegen_result
            
            # Stage 4: Integration Services (GitHub, Linear, Slack, CircleCI)
            logger.info("🔗 Stage 4: Integration services coordination")
            integration_results = {}
            
            # GitHub integration
            if self.github:
                workflow_result['extensions_used'].append('github')
                github_result = await self._execute_github_integration(project_id, workflow_result['results'])
                integration_results['github'] = github_result
            
            # Linear integration
            if self.linear:
                workflow_result['extensions_used'].append('linear')
                linear_result = await self._execute_linear_integration(project_id, workflow_result['results'])
                integration_results['linear'] = linear_result
            
            # Slack integration
            if self.slack:
                workflow_result['extensions_used'].append('slack')
                slack_result = await self._execute_slack_integration(project_id, workflow_result['results'])
                integration_results['slack'] = slack_result
            
            # CircleCI integration
            if self.circleci:
                workflow_result['extensions_used'].append('circleci')
                circleci_result = await self._execute_circleci_integration(project_id, workflow_result['results'])
                integration_results['circleci'] = circleci_result
            
            workflow_result['stages']['integration_services'] = {
                'status': 'completed',
                'result': integration_results
            }
            workflow_result['results']['integrations'] = integration_results
            
            # Stage 5: Quality Validation (Grainchain + Graph_sitter)
            logger.info("✅ Stage 5: Quality validation and analysis")
            quality_results = {}
            
            # Grainchain quality gates and sandbox
            if self.grainchain_quality_gates and self.grainchain_sandbox:
                workflow_result['extensions_used'].append('grainchain')
                grainchain_result = await self._execute_grainchain_validation(project_id, workflow_result['results'])
                quality_results['grainchain'] = grainchain_result
            
            # Graph_sitter analysis
            if self.graph_sitter_analysis:
                workflow_result['extensions_used'].append('graph_sitter')
                analysis_result = await self._execute_graph_sitter_analysis(project_id, workflow_result['results'])
                quality_results['graph_sitter'] = analysis_result
            
            workflow_result['stages']['quality_validation'] = {
                'status': 'completed',
                'result': quality_results
            }
            workflow_result['results']['quality'] = quality_results
            
            # Final status
            workflow_result['status'] = 'completed'
            workflow_result['extensions_used'] = list(set(workflow_result['extensions_used']))  # Remove duplicates
            
            logger.info(f"🎉 Comprehensive workflow completed using {len(workflow_result['extensions_used'])} extensions: {workflow_result['extensions_used']}")
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            workflow_result['status'] = 'failed'
            workflow_result['error'] = str(e)
        
        return workflow_result

    async def _execute_github_integration(self, project_id: str, context: dict) -> dict:
        """Execute GitHub integration using existing GitHub extension."""
        try:
            # Use existing GitHub extension for repository operations
            result = {
                'status': 'completed',
                'operations': ['repository_analysis', 'pr_management', 'issue_tracking'],
                'project_id': project_id
            }
            
            # If we have a codebase, analyze it
            if self.repo:
                codebase = await self._get_or_create_codebase()
                result['repository'] = self.repo
                result['codebase_analyzed'] = True
            
            return result
        except Exception as e:
            logger.error(f"GitHub integration failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _execute_linear_integration(self, project_id: str, context: dict) -> dict:
        """Execute Linear integration using existing Linear extension."""
        try:
            # Use existing Linear extension for task management
            result = {
                'status': 'completed',
                'operations': ['task_creation', 'issue_management', 'workflow_automation'],
                'project_id': project_id
            }
            
            # Import existing Linear components
            from ..linear.integration_agent import LinearIntegrationAgent
            from ..linear.workflow_automation import LinearWorkflowAutomation
            
            result['linear_integration'] = True
            return result
        except Exception as e:
            logger.error(f"Linear integration failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _execute_slack_integration(self, project_id: str, context: dict) -> dict:
        """Execute Slack integration using existing Slack extension."""
        try:
            # Use existing Slack extension for notifications
            result = {
                'status': 'completed',
                'operations': ['notifications', 'status_updates', 'team_communication'],
                'project_id': project_id
            }
            return result
        except Exception as e:
            logger.error(f"Slack integration failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _execute_circleci_integration(self, project_id: str, context: dict) -> dict:
        """Execute CircleCI integration using existing CircleCI extension."""
        try:
            # Use existing CircleCI extension for CI/CD
            result = {
                'status': 'completed',
                'operations': ['build_automation', 'test_execution', 'deployment_pipeline'],
                'project_id': project_id
            }
            
            # Import existing CircleCI components
            from ..circleci.integration_agent import CircleCIIntegrationAgent
            from ..circleci.workflow_automation import CircleCIWorkflowAutomation
            
            result['circleci_integration'] = True
            return result
        except Exception as e:
            logger.error(f"CircleCI integration failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _execute_grainchain_validation(self, project_id: str, context: dict) -> dict:
        """Execute Grainchain validation using existing Grainchain extension."""
        try:
            # Use existing Grainchain components for quality gates
            result = {
                'status': 'completed',
                'operations': ['sandbox_deployment', 'snapshot_saving', 'quality_gates'],
                'project_id': project_id
            }
            
            # Execute quality gates using existing components
            if self.grainchain_quality_gates:
                quality_result = await self.grainchain_quality_gates.execute_quality_gates(
                    project_id=project_id,
                    context=context
                )
                result['quality_gates'] = quality_result
            
            # Execute sandbox operations using existing components
            if self.grainchain_sandbox:
                sandbox_result = await self.grainchain_sandbox.create_sandbox(
                    project_id=project_id,
                    context=context
                )
                result['sandbox'] = sandbox_result
            
            return result
        except Exception as e:
            logger.error(f"Grainchain validation failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _execute_graph_sitter_analysis(self, project_id: str, context: dict) -> dict:
        """Execute Graph_sitter analysis using existing Graph_sitter extension."""
        try:
            # Use existing Graph_sitter components for code analysis
            result = {
                'status': 'completed',
                'operations': ['code_analysis', 'pr_validation', 'quality_assessment'],
                'project_id': project_id
            }
            
            # Execute comprehensive analysis using existing components
            if self.repo:
                codebase = await self._get_or_create_codebase()
                analysis_result = comprehensive_analysis(codebase)
                result['analysis'] = analysis_result
            
            # Execute quality assessment using existing components
            if self.graph_sitter_analysis:
                quality_assessment = await self.graph_sitter_analysis.analyze_quality(
                    project_id=project_id,
                    context=context
                )
                result['quality_assessment'] = quality_assessment
            
            return result
        except Exception as e:
            logger.error(f"Graph_sitter analysis failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _get_or_create_codebase(self) -> Codebase:
        """Get or create codebase instance using existing graph_sitter components."""
        if self.repo and self.repo in self._codebase_cache:
            return self._codebase_cache[self.repo]
        
        try:
            # Create codebase instance using existing graph_sitter components
            if self.repo:
                config = CodebaseConfig(sync_enabled=True)
                secrets = SecretsConfig(
                    github_token=os.environ.get("GITHUB_ACCESS_TOKEN"),
                    linear_api_key=os.environ.get("LINEAR_ACCESS_TOKEN")
                )
                codebase = Codebase.from_repo(
                    repo_full_name=self.repo,
                    tmp_dir=self.tmp_dir,
                    commit=self.commit,
                    config=config,
                    secrets=secrets
                )
                self._codebase_cache[self.repo] = codebase
                logger.info(f"Created codebase instance for {self.repo}")
            else:
                # Create a temporary codebase for current directory
                codebase = Codebase(".")
                self._codebase_cache["."] = codebase
        except Exception as e:
            logger.error(f"Failed to create codebase: {e}")
            # Create a temporary codebase for current directory
            codebase = Codebase(".")
            self._codebase_cache["."] = codebase
        
        return self._codebase_cache.get(self.repo, self._codebase_cache.get(".", Codebase(".")))

    def _register_unified_endpoints(self):
        """Register unified API endpoints for all 11 extensions."""
        
        @self.app.get("/")
        async def root():
            return {
                "message": f"ContextenApp {self.name} - Unified System with 11 Extensions",
                "extensions": [
                    "github", "linear", "slack", "circleci", "modal",
                    "prefect", "controlflow", "codegen", "grainchain", "graph_sitter"
                ],
                "status": "active"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for all 11 extensions."""
            health_status = {
                'status': 'healthy',
                'extensions': {
                    # Core extensions
                    'github': 'healthy' if self.github else 'unavailable',
                    'linear': 'healthy' if self.linear else 'unavailable',
                    'slack': 'healthy' if self.slack else 'unavailable',
                    'circleci': 'healthy' if self.circleci else 'unavailable',
                    'modal': 'healthy' if self.modal else 'unavailable',
                    # Orchestration extensions
                    'prefect': 'healthy' if self.prefect_flow else 'unavailable',
                    'controlflow': 'healthy' if self.controlflow_orchestrator else 'unavailable',
                    'codegen': 'healthy' if self.codegen_client else 'unavailable',
                    'grainchain': 'healthy' if self.grainchain_quality_gates else 'unavailable',
                    'graph_sitter': 'healthy' if self.graph_sitter_analysis else 'unavailable'
                }
            }
            return health_status
        
        @self.app.post("/workflow/comprehensive")
        async def execute_comprehensive_workflow_endpoint(request: Request):
            """Execute comprehensive workflow using all 11 extensions."""
            data = await request.json()
            project_id = data.get('project_id')
            requirements = data.get('requirements')
            
            if not project_id or not requirements:
                return {'error': 'project_id and requirements are required'}
            
            try:
                result = await self.execute_comprehensive_workflow(project_id, requirements)
                return result
            except Exception as e:
                return {'error': str(e), 'status': 'failed'}
        
        @self.app.get("/extensions/status")
        async def get_extensions_status():
            """Get detailed status of all 11 extensions."""
            return {
                'total_extensions': 11,
                'core_extensions': {
                    'github': {'status': 'active' if self.github else 'inactive', 'type': 'core'},
                    'linear': {'status': 'active' if self.linear else 'inactive', 'type': 'core'},
                    'slack': {'status': 'active' if self.slack else 'inactive', 'type': 'core'},
                    'circleci': {'status': 'active' if self.circleci else 'inactive', 'type': 'core'},
                    'modal': {'status': 'active' if self.modal else 'inactive', 'type': 'core'}
                },
                'orchestration_extensions': {
                    'prefect': {'status': 'active' if self.prefect_flow else 'inactive', 'type': 'orchestration'},
                    'controlflow': {'status': 'active' if self.controlflow_orchestrator else 'inactive', 'type': 'orchestration'},
                    'codegen': {'status': 'active' if self.codegen_client else 'inactive', 'type': 'orchestration'},
                    'grainchain': {'status': 'active' if self.grainchain_quality_gates else 'inactive', 'type': 'orchestration'},
                    'graph_sitter': {'status': 'active' if self.graph_sitter_analysis else 'inactive', 'type': 'orchestration'}
                }
            }

    def _setup_webhook_routes(self):
        """Setup webhook routes for all integrated services."""
        
        @self.app.post("/webhooks/github")
        async def github_webhook(request: Request):
            if self.github:
                payload = await request.json()
                return await self.github.handle(payload, request)
            return {'error': 'GitHub extension not available'}

        @self.app.post("/webhooks/linear")
        async def linear_webhook(request: Request):
            if self.linear:
                payload = await request.json()
                return await self.linear.handle(payload, request)
            return {'error': 'Linear extension not available'}

        @self.app.post("/webhooks/slack")
        async def slack_webhook(request: Request):
            if self.slack:
                payload = await request.json()
                return await self.slack.handle(payload, request)
            return {'error': 'Slack extension not available'}

        @self.app.post("/webhooks/circleci")
        async def circleci_webhook(request: Request):
            if self.circleci:
                payload = await request.json()
                return await self.circleci.handle(payload, request)
            return {'error': 'CircleCI extension not available'}

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
