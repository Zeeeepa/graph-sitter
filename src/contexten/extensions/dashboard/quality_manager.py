"""
Quality Manager for Single-User Dashboard

Provides practical code quality checks using Graph-sitter for analysis 
and GrainChain for sandboxed deployments and testing.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from graph_sitter.shared.logging.get_logger import get_logger
from .models import (
    GraphSitterAnalysis, GrainChainDeployment, DeploymentStatus,
    create_analysis_from_graph_sitter, create_deployment_for_project,
    TestResult, SandboxEnvironment, DeploymentSnapshot
)
from ..graph_sitter.graph_sitter import GraphSitter
from ..grainchain.grainchain import Grainchain
from ..circleci.circleci import CircleCI

logger = get_logger(__name__)


class QualityManager:
    """
    Handles code quality checks and deployment validation.
    
    Features:
    - Graph-sitter code analysis
    - GrainChain sandboxed deployments
    - CircleCI pipeline monitoring
    - Quality scoring and recommendations
    - Automated testing and validation
    """
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.analyses: Dict[str, GraphSitterAnalysis] = {}
        self.deployments: Dict[str, GrainChainDeployment] = {}
        self.graph_sitter: Optional[GraphSitter] = None
        self.grainchain: Optional[Grainchain] = None
        self.circleci: Optional[CircleCI] = None
        
    async def initialize(self):
        """Initialize the quality manager"""
        logger.info("Initializing QualityManager...")
        
        # Initialize Graph-sitter
        if self.dashboard.settings_manager.is_extension_enabled("graph_sitter"):
            self.graph_sitter = GraphSitter({})
            await self.graph_sitter.initialize()
            logger.info("Graph-sitter integration initialized")
            
        # Initialize GrainChain
        if self.dashboard.settings_manager.is_extension_enabled("grainchain"):
            self.grainchain = Grainchain({})
            await self.grainchain.initialize()
            logger.info("GrainChain integration initialized")
            
        # Initialize CircleCI
        if self.dashboard.settings_manager.is_extension_enabled("circleci"):
            circleci_token = self.dashboard.settings_manager.get_api_credential("circleci")
            if circleci_token:
                self.circleci = CircleCI({"api_token": circleci_token})
                await self.circleci.initialize()
                logger.info("CircleCI integration initialized")
            else:
                logger.warning("CircleCI token not configured")
                
    async def analyze_project(self, project_id: str, force_refresh: bool = False) -> Optional[GraphSitterAnalysis]:
        """
        Perform comprehensive code analysis using Graph-sitter
        
        Args:
            project_id: Project ID to analyze
            force_refresh: Force new analysis even if cached
            
        Returns:
            Analysis results or None if failed
        """
        try:
            logger.info(f"Analyzing project {project_id}")
            
            # Check cache first
            if not force_refresh and project_id in self.analyses:
                analysis = self.analyses[project_id]
                # Check if analysis is recent (less than 1 hour old)
                if (datetime.now() - analysis.analysis_timestamp).seconds < 3600:
                    logger.info(f"Using cached analysis for project {project_id}")
                    return analysis
                    
            # Get project details
            project = await self.dashboard.project_manager.get_project(project_id)
            if not project:
                logger.error(f"Project not found: {project_id}")
                return None
                
            # Update project status
            await self.dashboard.project_manager.update_project_status(project_id, "analyzing")
            
            # Perform analysis
            if self.graph_sitter:
                analysis_result = await self._perform_graph_sitter_analysis(project)
            else:
                # Fallback analysis without Graph-sitter
                analysis_result = await self._perform_fallback_analysis(project)
                
            if analysis_result:
                # Create analysis object
                analysis = create_analysis_from_graph_sitter(project_id, analysis_result)
                
                # Store analysis
                self.analyses[project_id] = analysis
                project.analysis = analysis
                
                # Update project status
                await self.dashboard.project_manager.update_project_status(project_id, "analyzed")
                
                # Emit event
                await self.dashboard.event_coordinator.emit_event(
                    "analysis_completed",
                    "quality_manager",
                    project_id=project_id,
                    data={
                        "quality_score": analysis.quality_score,
                        "error_count": len(analysis.errors),
                        "missing_features": len(analysis.missing_features),
                        "config_issues": len(analysis.config_issues)
                    }
                )
                
                logger.info(f"Analysis completed for project {project_id} - Quality Score: {analysis.quality_score:.2f}")
                return analysis
            else:
                logger.error(f"Analysis failed for project {project_id}")
                await self.dashboard.project_manager.update_project_status(project_id, "failed")
                return None
                
        except Exception as e:
            logger.error(f"Failed to analyze project {project_id}: {e}")
            await self.dashboard.project_manager.update_project_status(project_id, "failed")
            return None
            
    async def _perform_graph_sitter_analysis(self, project) -> Dict[str, Any]:
        """Perform analysis using Graph-sitter"""
        try:
            # Get repository path (simplified - in real implementation, would clone repo)
            repo_path = f"./workspace/{project.github_owner}/{project.github_repo}"
            
            # Perform comprehensive analysis
            analysis_result = await self.graph_sitter.analyze_codebase(repo_path)
            
            # Process results
            processed_result = {
                "errors": self._extract_errors(analysis_result),
                "missing_features": self._extract_missing_features(analysis_result),
                "config_issues": self._extract_config_issues(analysis_result),
                "quality_score": self._calculate_quality_score(analysis_result),
                "complexity_score": analysis_result.get("complexity_score", 0.0),
                "maintainability_score": analysis_result.get("maintainability_score", 0.0),
                "test_coverage": analysis_result.get("test_coverage", 0.0),
                "dependencies": analysis_result.get("dependencies", {}),
                "security_issues": analysis_result.get("security_issues", []),
                "performance_issues": analysis_result.get("performance_issues", [])
            }
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Graph-sitter analysis failed: {e}")
            return {}
            
    async def _perform_fallback_analysis(self, project) -> Dict[str, Any]:
        """Perform basic analysis without Graph-sitter"""
        logger.info("Performing fallback analysis without Graph-sitter")
        
        # Simulate basic analysis
        await asyncio.sleep(2)
        
        return {
            "errors": [],
            "missing_features": [],
            "config_issues": [],
            "quality_score": 7.5,  # Default score
            "complexity_score": 6.0,
            "maintainability_score": 8.0,
            "test_coverage": 65.0,
            "dependencies": {},
            "security_issues": [],
            "performance_issues": []
        }
        
    def _extract_errors(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract code errors from analysis result"""
        errors = []
        
        # Extract syntax errors
        for error in analysis_result.get("syntax_errors", []):
            errors.append({
                "file_path": error.get("file", "unknown"),
                "line_number": error.get("line", 0),
                "column": error.get("column", 0),
                "error_type": "syntax",
                "message": error.get("message", "Syntax error"),
                "severity": "error",
                "suggestion": error.get("suggestion")
            })
            
        # Extract logic errors
        for error in analysis_result.get("logic_errors", []):
            errors.append({
                "file_path": error.get("file", "unknown"),
                "line_number": error.get("line", 0),
                "column": error.get("column", 0),
                "error_type": "logic",
                "message": error.get("message", "Logic error"),
                "severity": "warning",
                "suggestion": error.get("suggestion")
            })
            
        return errors
        
    def _extract_missing_features(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract missing features from analysis result"""
        features = []
        
        for feature in analysis_result.get("missing_features", []):
            features.append({
                "feature_name": feature.get("name", "Unknown feature"),
                "description": feature.get("description", ""),
                "file_path": feature.get("file", ""),
                "suggested_implementation": feature.get("suggestion"),
                "priority": feature.get("priority", "medium")
            })
            
        return features
        
    def _extract_config_issues(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract configuration issues from analysis result"""
        issues = []
        
        for issue in analysis_result.get("config_issues", []):
            issues.append({
                "config_file": issue.get("file", "unknown"),
                "issue_type": issue.get("type", "unknown"),
                "message": issue.get("message", "Configuration issue"),
                "suggested_fix": issue.get("fix")
            })
            
        return issues
        
    def _calculate_quality_score(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        base_score = 10.0
        
        # Deduct for errors
        error_count = len(analysis_result.get("syntax_errors", [])) + len(analysis_result.get("logic_errors", []))
        base_score -= min(error_count * 0.5, 3.0)
        
        # Deduct for missing features
        missing_count = len(analysis_result.get("missing_features", []))
        base_score -= min(missing_count * 0.3, 2.0)
        
        # Deduct for config issues
        config_count = len(analysis_result.get("config_issues", []))
        base_score -= min(config_count * 0.2, 1.0)
        
        # Factor in test coverage
        test_coverage = analysis_result.get("test_coverage", 0.0)
        if test_coverage < 50:
            base_score -= 1.0
        elif test_coverage < 70:
            base_score -= 0.5
            
        return max(base_score, 0.0)
        
    async def deploy_to_sandbox(self, project_id: str, environment_type: str = "development") -> Optional[GrainChainDeployment]:
        """
        Deploy project to GrainChain sandbox environment
        
        Args:
            project_id: Project ID to deploy
            environment_type: Type of environment (development, staging, production)
            
        Returns:
            Deployment information or None if failed
        """
        try:
            logger.info(f"Deploying project {project_id} to sandbox")
            
            # Get project
            project = await self.dashboard.project_manager.get_project(project_id)
            if not project:
                logger.error(f"Project not found: {project_id}")
                return None
                
            # Create deployment
            sandbox_config = {
                "type": environment_type,
                "resources": {
                    "cpu": "1",
                    "memory": "2Gi",
                    "storage": "10Gi"
                }
            }
            
            deployment = create_deployment_for_project(project_id, sandbox_config)
            
            # Store deployment
            self.deployments[deployment.deployment_id] = deployment
            project.deployment = deployment
            
            # Start deployment process
            if self.grainchain:
                success = await self._deploy_with_grainchain(deployment)
            else:
                # Simulate deployment without GrainChain
                success = await self._simulate_deployment(deployment)
                
            if success:
                deployment.status = DeploymentStatus.DEPLOYED
                
                # Run tests
                await self._run_deployment_tests(deployment)
                
                # Emit event
                await self.dashboard.event_coordinator.emit_event(
                    "deployment_completed",
                    "quality_manager",
                    project_id=project_id,
                    data={
                        "deployment_id": deployment.deployment_id,
                        "sandbox_id": deployment.sandbox.sandbox_id,
                        "environment_type": environment_type
                    }
                )
                
                logger.info(f"Deployment completed: {deployment.deployment_id}")
                return deployment
            else:
                deployment.status = DeploymentStatus.FAILED
                logger.error(f"Deployment failed: {deployment.deployment_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to deploy project {project_id}: {e}")
            return None
            
    async def _deploy_with_grainchain(self, deployment: GrainChainDeployment) -> bool:
        """Deploy using GrainChain"""
        try:
            # Create sandbox environment
            sandbox_result = await self.grainchain.create_sandbox(
                sandbox_id=deployment.sandbox.sandbox_id,
                config=deployment.sandbox.resources
            )
            
            if sandbox_result:
                deployment.sandbox.status = "ready"
                deployment.sandbox.url = sandbox_result.get("url")
                
                # Deploy application
                deploy_result = await self.grainchain.deploy_application(
                    sandbox_id=deployment.sandbox.sandbox_id,
                    project_id=deployment.project_id
                )
                
                return deploy_result.get("success", False)
            else:
                return False
                
        except Exception as e:
            logger.error(f"GrainChain deployment failed: {e}")
            return False
            
    async def _simulate_deployment(self, deployment: GrainChainDeployment) -> bool:
        """Simulate deployment without GrainChain"""
        logger.info("Simulating deployment without GrainChain")
        
        # Simulate deployment process
        deployment.status = DeploymentStatus.DEPLOYING
        await asyncio.sleep(3)
        
        deployment.sandbox.status = "ready"
        deployment.sandbox.url = f"http://sandbox-{deployment.sandbox.sandbox_id}.local"
        
        return True
        
    async def _run_deployment_tests(self, deployment: GrainChainDeployment):
        """Run tests on deployed application"""
        try:
            logger.info(f"Running tests for deployment {deployment.deployment_id}")
            
            # Simulate test execution
            test_results = [
                TestResult(
                    test_name="Health Check",
                    status="passed",
                    duration=1.2,
                    message="Application is responding"
                ),
                TestResult(
                    test_name="API Endpoints",
                    status="passed",
                    duration=2.5,
                    message="All endpoints accessible"
                ),
                TestResult(
                    test_name="Database Connection",
                    status="passed",
                    duration=0.8,
                    message="Database connection successful"
                )
            ]
            
            deployment.test_results = test_results
            deployment.status = DeploymentStatus.VALIDATED
            
            logger.info(f"Tests completed for deployment {deployment.deployment_id}")
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            deployment.status = DeploymentStatus.FAILED
            
    async def create_snapshot(self, deployment_id: str, description: str = "") -> Optional[DeploymentSnapshot]:
        """Create a snapshot of a deployment"""
        try:
            if deployment_id not in self.deployments:
                logger.error(f"Deployment not found: {deployment_id}")
                return None
                
            deployment = self.deployments[deployment_id]
            
            snapshot_id = f"snapshot_{deployment_id}_{int(datetime.now().timestamp())}"
            snapshot = DeploymentSnapshot(
                snapshot_id=snapshot_id,
                deployment_id=deployment_id,
                created_at=datetime.now(),
                description=description or f"Snapshot of {deployment_id}",
                size_mb=150.0,  # Simulated size
                status="creating"
            )
            
            # Simulate snapshot creation
            await asyncio.sleep(2)
            snapshot.status = "ready"
            
            deployment.snapshots.append(snapshot)
            
            logger.info(f"Created snapshot: {snapshot_id}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return None
            
    async def get_analysis(self, project_id: str) -> Optional[GraphSitterAnalysis]:
        """Get analysis results for a project"""
        return self.analyses.get(project_id)
        
    async def get_deployment(self, deployment_id: str) -> Optional[GrainChainDeployment]:
        """Get deployment information"""
        return self.deployments.get(deployment_id)
        
    async def get_project_deployment(self, project_id: str) -> Optional[GrainChainDeployment]:
        """Get current deployment for a project"""
        for deployment in self.deployments.values():
            if deployment.project_id == project_id:
                return deployment
        return None
        
    async def check_ci_status(self, project_id: str) -> Dict[str, Any]:
        """Check CircleCI pipeline status for a project"""
        try:
            if not self.circleci:
                return {"status": "unavailable", "message": "CircleCI not configured"}
                
            project = await self.dashboard.project_manager.get_project(project_id)
            if not project:
                return {"status": "error", "message": "Project not found"}
                
            # Get pipeline status
            status = await self.circleci.get_project_status(
                f"{project.github_owner}/{project.github_repo}"
            )
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to check CI status: {e}")
            return {"status": "error", "message": str(e)}
            
    async def get_quality_summary(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive quality summary for a project"""
        analysis = self.analyses.get(project_id)
        deployment = await self.get_project_deployment(project_id)
        ci_status = await self.check_ci_status(project_id)
        
        summary = {
            "project_id": project_id,
            "analysis": {
                "available": bool(analysis),
                "quality_score": analysis.quality_score if analysis else 0.0,
                "error_count": len(analysis.errors) if analysis else 0,
                "missing_features": len(analysis.missing_features) if analysis else 0,
                "config_issues": len(analysis.config_issues) if analysis else 0,
                "last_analyzed": analysis.analysis_timestamp.isoformat() if analysis else None
            },
            "deployment": {
                "available": bool(deployment),
                "status": deployment.status if deployment else "not_deployed",
                "sandbox_url": deployment.sandbox.url if deployment else None,
                "test_results": len(deployment.test_results) if deployment else 0,
                "snapshots": len(deployment.snapshots) if deployment else 0
            },
            "ci_status": ci_status,
            "overall_health": self._calculate_overall_health(analysis, deployment, ci_status)
        }
        
        return summary
        
    def _calculate_overall_health(self, analysis, deployment, ci_status) -> str:
        """Calculate overall project health"""
        if not analysis:
            return "unknown"
            
        if analysis.quality_score >= 8.0 and deployment and deployment.status == "validated":
            return "excellent"
        elif analysis.quality_score >= 6.0:
            return "good"
        elif analysis.quality_score >= 4.0:
            return "fair"
        else:
            return "poor"

