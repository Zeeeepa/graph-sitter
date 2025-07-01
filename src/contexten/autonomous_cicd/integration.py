"""
Integration module for Autonomous CI/CD with existing Contexten system

This module integrates the autonomous CI/CD system with the existing
Contexten orchestrator and Graph-Sitter codebase analysis.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

from .core import AutonomousCICD
from .config import CICDConfig

logger = get_logger(__name__)


@dataclass
class IntegrationConfig:
    """Configuration for CI/CD integration"""
    enable_contexten_integration: bool = True
    enable_graph_sitter_analysis: bool = True
    enable_auto_pr_creation: bool = True
    enable_issue_tracking: bool = True


class ContextenCICDIntegration:
    """
    Integration layer between Autonomous CI/CD and Contexten orchestrator
    
    This class provides seamless integration with:
    - Existing Contexten extensions (GitHub, Linear, Slack)
    - Graph-Sitter codebase analysis
    - Codegen SDK for intelligent automation
    """
    
    def __init__(self, cicd_config: CICDConfig, integration_config: IntegrationConfig):
        self.cicd_config = cicd_config
        self.integration_config = integration_config
        self.cicd_system = None
        self.codebase = None
        
    async def initialize(self):
        """Initialize the integrated CI/CD system"""
        try:
            # Initialize autonomous CI/CD system
            self.cicd_system = AutonomousCICD(self.cicd_config)
            await self.cicd_system.initialize()
            
            # Initialize Graph-Sitter codebase analysis
            if self.integration_config.enable_graph_sitter_analysis:
                self.codebase = Codebase.from_path(self.cicd_config.repo_path)
                logger.info(f"Graph-Sitter codebase loaded: {self.codebase.summary}")
            
            # Setup integration hooks
            await self._setup_integration_hooks()
            
            logger.info("Contexten CI/CD integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CI/CD integration: {e}")
            raise
    
    async def _setup_integration_hooks(self):
        """Setup integration hooks with existing Contexten system"""
        
        # Hook into GitHub events
        if self.integration_config.enable_contexten_integration:
            github_trigger = self.cicd_system.triggers.get("github")
            if github_trigger:
                # Extend GitHub trigger with Contexten integration
                original_handle_push = github_trigger._handle_push_event
                
                async def enhanced_handle_push(payload):
                    # Call original handler
                    await original_handle_push(payload)
                    
                    # Add Contexten-specific processing
                    await self._handle_contexten_github_event(payload)
                
                github_trigger._handle_push_event = enhanced_handle_push
        
        # Hook into Linear events
        linear_trigger = self.cicd_system.triggers.get("linear")
        if linear_trigger and self.integration_config.enable_issue_tracking:
            original_handle_issue = linear_trigger._handle_issue_event
            
            async def enhanced_handle_issue(payload):
                await original_handle_issue(payload)
                await self._handle_contexten_linear_event(payload)
            
            linear_trigger._handle_issue_event = enhanced_handle_issue
    
    async def _handle_contexten_github_event(self, payload: Dict[str, Any]):
        """Handle GitHub events with Contexten integration"""
        try:
            # Extract relevant information
            branch = payload.get("ref", "").replace("refs/heads/", "")
            commits = payload.get("commits", [])
            
            # Use Graph-Sitter for enhanced code analysis
            if self.codebase and commits:
                changed_files = []
                for commit in commits:
                    changed_files.extend(commit.get("added", []))
                    changed_files.extend(commit.get("modified", []))
                
                # Analyze changes using Graph-Sitter
                analysis_results = await self._analyze_changes_with_graph_sitter(changed_files)
                
                # Create intelligent PR comments if needed
                if self.integration_config.enable_auto_pr_creation:
                    await self._create_intelligent_pr_comment(payload, analysis_results)
            
        except Exception as e:
            logger.error(f"Error handling Contexten GitHub event: {e}")
    
    async def _handle_contexten_linear_event(self, payload: Dict[str, Any]):
        """Handle Linear events with Contexten integration"""
        try:
            issue = payload.get("data", {})
            issue_title = issue.get("title", "")
            
            # Check if issue is related to CI/CD
            if any(keyword in issue_title.lower() for keyword in ["ci/cd", "deployment", "testing", "build"]):
                # Create corresponding CI/CD pipeline
                await self._create_pipeline_from_linear_issue(issue)
            
        except Exception as e:
            logger.error(f"Error handling Contexten Linear event: {e}")
    
    async def _analyze_changes_with_graph_sitter(self, changed_files: list) -> Dict[str, Any]:
        """Analyze code changes using Graph-Sitter"""
        try:
            if not self.codebase:
                return {}
            
            analysis_results = {
                "complexity_changes": [],
                "dependency_impacts": [],
                "test_coverage_gaps": [],
                "security_concerns": []
            }
            
            for file_path in changed_files:
                try:
                    # Get file from codebase
                    file_obj = self.codebase.get_file(file_path)
                    if not file_obj:
                        continue
                    
                    # Analyze complexity
                    if hasattr(file_obj, 'functions'):
                        for func in file_obj.functions:
                            if hasattr(func, 'complexity') and func.complexity > 10:
                                analysis_results["complexity_changes"].append({
                                    "file": file_path,
                                    "function": func.name,
                                    "complexity": func.complexity
                                })
                    
                    # Analyze dependencies
                    if hasattr(file_obj, 'imports'):
                        for imp in file_obj.imports:
                            # Check for potentially problematic imports
                            if any(risky in str(imp) for risky in ["eval", "exec", "subprocess"]):
                                analysis_results["security_concerns"].append({
                                    "file": file_path,
                                    "import": str(imp),
                                    "concern": "Potentially unsafe import"
                                })
                
                except Exception as e:
                    logger.warning(f"Error analyzing file {file_path}: {e}")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in Graph-Sitter analysis: {e}")
            return {}
    
    async def _create_intelligent_pr_comment(self, payload: Dict[str, Any], analysis_results: Dict[str, Any]):
        """Create intelligent PR comments based on analysis"""
        try:
            if not analysis_results:
                return
            
            # Generate intelligent comment using Codegen SDK
            from codegen import Agent
            
            agent = Agent(
                org_id=self.cicd_config.codegen_org_id,
                token=self.cicd_config.codegen_token
            )
            
            # Create analysis summary
            comment_prompt = f"""
Based on the code analysis results, create a helpful PR comment:

Analysis Results:
- Complexity Changes: {len(analysis_results.get('complexity_changes', []))} functions with high complexity
- Security Concerns: {len(analysis_results.get('security_concerns', []))} potential issues
- Dependency Impacts: {len(analysis_results.get('dependency_impacts', []))} dependency changes

Please provide:
1. A summary of the analysis
2. Specific recommendations for improvement
3. Any security or performance concerns
4. Suggestions for additional testing

Keep the comment constructive and helpful.
"""
            
            task = agent.run(prompt=comment_prompt)
            
            # Wait for completion (with timeout)
            timeout_count = 0
            while task.status not in ['completed', 'failed'] and timeout_count < 30:
                await asyncio.sleep(2)
                task.refresh()
                timeout_count += 1
            
            if task.status == 'completed':
                # This would post the comment to the actual PR
                logger.info(f"Generated intelligent PR comment: {task.result[:100]}...")
            
        except Exception as e:
            logger.error(f"Error creating intelligent PR comment: {e}")
    
    async def _create_pipeline_from_linear_issue(self, issue: Dict[str, Any]):
        """Create CI/CD pipeline from Linear issue"""
        try:
            issue_title = issue.get("title", "")
            issue_description = issue.get("description", "")
            
            # Determine pipeline type from issue content
            pipeline_type = "analysis"
            if "deploy" in issue_title.lower():
                pipeline_type = "deploy"
            elif "test" in issue_title.lower():
                pipeline_type = "test"
            
            # Create pipeline
            trigger_event = {
                "trigger_type": "linear_issue",
                "issue_id": issue.get("id"),
                "issue_title": issue_title,
                "branch": self.cicd_config.target_branch,
                "changes": []
            }
            
            result = await self.cicd_system.execute_pipeline(
                trigger_event=trigger_event,
                pipeline_type=pipeline_type
            )
            
            logger.info(f"Created pipeline {result.pipeline_id} from Linear issue {issue.get('id')}")
            
        except Exception as e:
            logger.error(f"Error creating pipeline from Linear issue: {e}")
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get status of the integration"""
        status = {
            "cicd_system_status": "unknown",
            "graph_sitter_status": "unknown",
            "contexten_integration": self.integration_config.enable_contexten_integration,
            "active_pipelines": 0,
            "codebase_loaded": self.codebase is not None
        }
        
        if self.cicd_system:
            cicd_metrics = await self.cicd_system.get_system_metrics()
            status.update({
                "cicd_system_status": "active",
                "active_pipelines": cicd_metrics["active_pipelines"],
                "total_pipelines": cicd_metrics["total_pipelines"],
                "success_rate": cicd_metrics["success_rate"]
            })
        
        if self.codebase:
            status.update({
                "graph_sitter_status": "active",
                "codebase_files": len(self.codebase.files) if hasattr(self.codebase, 'files') else 0,
                "codebase_summary": str(self.codebase.summary) if hasattr(self.codebase, 'summary') else "Available"
            })
        
        return status
    
    async def shutdown(self):
        """Shutdown the integration"""
        if self.cicd_system:
            await self.cicd_system.shutdown()
        
        logger.info("Contexten CI/CD integration shutdown complete")


# Convenience function for easy setup
async def setup_autonomous_cicd(
    codegen_org_id: str,
    codegen_token: str,
    repo_path: str = ".",
    enable_all_features: bool = True
) -> ContextenCICDIntegration:
    """
    Setup autonomous CI/CD system with sensible defaults
    
    Args:
        codegen_org_id: Codegen organization ID
        codegen_token: Codegen API token
        repo_path: Path to repository
        enable_all_features: Enable all integration features
    
    Returns:
        Configured and initialized CI/CD integration
    """
    
    cicd_config = CICDConfig(
        codegen_org_id=codegen_org_id,
        codegen_token=codegen_token,
        repo_path=repo_path,
        enable_auto_testing=True,
        enable_code_analysis=True,
        enable_security_scanning=True
    )
    
    integration_config = IntegrationConfig(
        enable_contexten_integration=enable_all_features,
        enable_graph_sitter_analysis=enable_all_features,
        enable_auto_pr_creation=enable_all_features,
        enable_issue_tracking=enable_all_features
    )
    
    integration = ContextenCICDIntegration(cicd_config, integration_config)
    await integration.initialize()
    
    return integration

