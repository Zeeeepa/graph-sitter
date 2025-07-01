"""
Autonomous Pipeline Manager - Intelligent CI/CD orchestration with Codegen SDK integration.

This module provides the core autonomous CI/CD capabilities that can:
- Monitor pipeline health and performance
- Auto-heal failing builds using Codegen SDK
- Optimize pipeline configuration based on patterns
- Predict and prevent failures
- Generate intelligent reports and recommendations
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

# Graph-Sitter imports
from graph_sitter import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

# Codegen SDK imports
from codegen import Agent

# GitHub integration
from ..github.events.pull_request import PullRequestEvent
from ..github.workflow.workflow_manager import WorkflowManager

logger = get_logger(__name__)

class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    HEALING = "healing"
    OPTIMIZING = "optimizing"

class FailureCategory(Enum):
    """Categories of pipeline failures."""
    TEST_FAILURE = "test_failure"
    BUILD_FAILURE = "build_failure"
    LINT_FAILURE = "lint_failure"
    DEPENDENCY_FAILURE = "dependency_failure"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    TIMEOUT_FAILURE = "timeout_failure"
    UNKNOWN_FAILURE = "unknown_failure"

@dataclass
class PipelineMetrics:
    """Pipeline performance metrics."""
    execution_time: float
    success_rate: float
    failure_count: int
    healing_attempts: int
    optimization_count: int
    cost_savings: float
    performance_improvement: float

@dataclass
class FailureAnalysis:
    """Analysis of pipeline failure."""
    category: FailureCategory
    root_cause: str
    affected_components: List[str]
    suggested_fixes: List[str]
    confidence_score: float
    healing_strategy: str

@dataclass
class PipelineOptimization:
    """Pipeline optimization recommendation."""
    optimization_type: str
    description: str
    expected_improvement: float
    implementation_effort: str
    priority: int

class AutonomousPipelineManager:
    """
    Autonomous CI/CD pipeline manager with Codegen SDK integration.
    
    Provides intelligent pipeline orchestration, self-healing capabilities,
    and continuous optimization based on machine learning insights.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize Codegen SDK agent
        self.codegen_agent = Agent(
            org_id=self.config.get('codegen_org_id'),
            token=self.config.get('codegen_token'),
            base_url=self.config.get('codegen_base_url', 'https://api.codegen.com')
        )
        
        # Pipeline configuration
        self.auto_healing_enabled = self.config.get('auto_healing_enabled', True)
        self.predictive_analysis_enabled = self.config.get('predictive_analysis_enabled', True)
        self.optimization_enabled = self.config.get('optimization_enabled', True)
        self.max_healing_attempts = self.config.get('max_healing_attempts', 3)
        
        # Metrics and state
        self.pipeline_metrics: Dict[str, PipelineMetrics] = {}
        self.failure_history: List[FailureAnalysis] = []
        self.optimization_history: List[PipelineOptimization] = []
        
        # Callbacks
        self.failure_callbacks: List[Callable] = []
        self.success_callbacks: List[Callable] = []
        self.optimization_callbacks: List[Callable] = []
        
        # Initialize codebase if path provided
        self.codebase = None
        if 'codebase_path' in self.config:
            self.codebase = Codebase(self.config['codebase_path'])
    
    async def monitor_pipeline(self, pipeline_id: str, workflow_run_id: str) -> PipelineStatus:
        """
        Monitor a pipeline execution and provide autonomous management.
        
        Args:
            pipeline_id: Unique identifier for the pipeline
            workflow_run_id: GitHub workflow run ID
            
        Returns:
            Final pipeline status after autonomous management
        """
        logger.info(f"Starting autonomous monitoring for pipeline {pipeline_id}")
        
        start_time = datetime.now()
        status = PipelineStatus.RUNNING
        healing_attempts = 0
        
        try:
            # Monitor pipeline execution
            while status == PipelineStatus.RUNNING:
                # Check current status
                current_status = await self._check_pipeline_status(workflow_run_id)
                
                if current_status == PipelineStatus.FAILURE:
                    logger.warning(f"Pipeline {pipeline_id} failed, initiating analysis")
                    
                    # Analyze failure
                    failure_analysis = await self._analyze_failure(workflow_run_id)
                    self.failure_history.append(failure_analysis)
                    
                    # Attempt self-healing if enabled
                    if (self.auto_healing_enabled and 
                        healing_attempts < self.max_healing_attempts and
                        failure_analysis.confidence_score > 0.7):
                        
                        logger.info(f"Attempting self-healing for pipeline {pipeline_id}")
                        status = PipelineStatus.HEALING
                        
                        healing_success = await self._attempt_healing(
                            pipeline_id, failure_analysis, workflow_run_id
                        )
                        
                        if healing_success:
                            logger.info(f"Self-healing successful for pipeline {pipeline_id}")
                            status = PipelineStatus.RUNNING
                            healing_attempts += 1
                        else:
                            logger.error(f"Self-healing failed for pipeline {pipeline_id}")
                            status = PipelineStatus.FAILURE
                            break
                    else:
                        status = PipelineStatus.FAILURE
                        break
                
                elif current_status == PipelineStatus.SUCCESS:
                    status = PipelineStatus.SUCCESS
                    break
                
                elif current_status == PipelineStatus.CANCELLED:
                    status = PipelineStatus.CANCELLED
                    break
                
                # Wait before next check
                await asyncio.sleep(30)
            
            # Record metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._record_pipeline_metrics(
                pipeline_id, status, execution_time, healing_attempts
            )
            
            # Trigger optimization analysis if successful
            if status == PipelineStatus.SUCCESS and self.optimization_enabled:
                await self._analyze_optimization_opportunities(pipeline_id)
            
            # Call appropriate callbacks
            if status == PipelineStatus.SUCCESS:
                for callback in self.success_callbacks:
                    await callback(pipeline_id, status)
            elif status == PipelineStatus.FAILURE:
                for callback in self.failure_callbacks:
                    await callback(pipeline_id, status)
            
            return status
            
        except Exception as e:
            logger.error(f"Error monitoring pipeline {pipeline_id}: {e}", exc_info=True)
            return PipelineStatus.FAILURE
    
    async def _check_pipeline_status(self, workflow_run_id: str) -> PipelineStatus:
        """Check the current status of a GitHub workflow run."""
        try:
            # Use Codegen SDK to check workflow status
            task = self.codegen_agent.run(
                prompt=f"Check the status of GitHub workflow run {workflow_run_id} and return the current status"
            )
            
            # Wait for task completion
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            # Parse status from result
            result = task.result.lower()
            if "success" in result or "completed" in result:
                return PipelineStatus.SUCCESS
            elif "failure" in result or "failed" in result:
                return PipelineStatus.FAILURE
            elif "cancelled" in result:
                return PipelineStatus.CANCELLED
            else:
                return PipelineStatus.RUNNING
                
        except Exception as e:
            logger.error(f"Error checking pipeline status: {e}")
            return PipelineStatus.RUNNING
    
    async def _analyze_failure(self, workflow_run_id: str) -> FailureAnalysis:
        """
        Analyze pipeline failure using Codegen SDK for intelligent diagnosis.
        """
        logger.info(f"Analyzing failure for workflow run {workflow_run_id}")
        
        try:
            # Use Codegen SDK to analyze the failure
            analysis_prompt = f"""
            Analyze the failed GitHub workflow run {workflow_run_id} and provide:
            1. Root cause of the failure
            2. Category of failure (test, build, lint, dependency, infrastructure, timeout)
            3. Affected components or files
            4. Suggested fixes with confidence scores
            5. Recommended healing strategy
            
            Focus on actionable insights that can be automatically implemented.
            """
            
            task = self.codegen_agent.run(prompt=analysis_prompt)
            
            # Wait for analysis completion
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            # Parse analysis result
            analysis_result = task.result
            
            # Extract structured information (simplified parsing)
            failure_analysis = FailureAnalysis(
                category=self._categorize_failure(analysis_result),
                root_cause=self._extract_root_cause(analysis_result),
                affected_components=self._extract_affected_components(analysis_result),
                suggested_fixes=self._extract_suggested_fixes(analysis_result),
                confidence_score=self._calculate_confidence_score(analysis_result),
                healing_strategy=self._extract_healing_strategy(analysis_result)
            )
            
            logger.info(f"Failure analysis complete: {failure_analysis.category.value}")
            return failure_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing failure: {e}")
            return FailureAnalysis(
                category=FailureCategory.UNKNOWN_FAILURE,
                root_cause="Analysis failed",
                affected_components=[],
                suggested_fixes=[],
                confidence_score=0.0,
                healing_strategy="manual_intervention"
            )
    
    async def _attempt_healing(
        self, 
        pipeline_id: str, 
        failure_analysis: FailureAnalysis,
        workflow_run_id: str
    ) -> bool:
        """
        Attempt to heal the pipeline failure using Codegen SDK.
        """
        logger.info(f"Attempting healing for pipeline {pipeline_id}")
        
        try:
            # Generate healing prompt based on failure analysis
            healing_prompt = f"""
            Fix the pipeline failure with the following details:
            - Root cause: {failure_analysis.root_cause}
            - Category: {failure_analysis.category.value}
            - Affected components: {', '.join(failure_analysis.affected_components)}
            - Suggested fixes: {', '.join(failure_analysis.suggested_fixes)}
            - Healing strategy: {failure_analysis.healing_strategy}
            
            Please implement the necessary fixes and create a PR with the changes.
            Focus on minimal, targeted fixes that address the root cause.
            """
            
            # Use Codegen SDK to implement fixes
            healing_task = self.codegen_agent.run(prompt=healing_prompt)
            
            # Wait for healing completion
            while healing_task.status != "completed":
                await asyncio.sleep(10)
                healing_task.refresh()
            
            # Check if healing was successful
            if "PR created" in healing_task.result or "fixes applied" in healing_task.result:
                logger.info(f"Healing successful for pipeline {pipeline_id}")
                
                # Trigger re-run of the pipeline
                await self._trigger_pipeline_rerun(workflow_run_id)
                return True
            else:
                logger.warning(f"Healing attempt failed for pipeline {pipeline_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error during healing attempt: {e}")
            return False
    
    async def _trigger_pipeline_rerun(self, workflow_run_id: str):
        """Trigger a re-run of the failed pipeline."""
        try:
            rerun_prompt = f"""
            Re-run the GitHub workflow run {workflow_run_id} after applying fixes.
            Use the GitHub API to trigger the re-run.
            """
            
            task = self.codegen_agent.run(prompt=rerun_prompt)
            
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            logger.info(f"Pipeline re-run triggered for workflow {workflow_run_id}")
            
        except Exception as e:
            logger.error(f"Error triggering pipeline re-run: {e}")
    
    async def _record_pipeline_metrics(
        self, 
        pipeline_id: str, 
        status: PipelineStatus, 
        execution_time: float,
        healing_attempts: int
    ):
        """Record pipeline execution metrics."""
        if pipeline_id not in self.pipeline_metrics:
            self.pipeline_metrics[pipeline_id] = PipelineMetrics(
                execution_time=0.0,
                success_rate=0.0,
                failure_count=0,
                healing_attempts=0,
                optimization_count=0,
                cost_savings=0.0,
                performance_improvement=0.0
            )
        
        metrics = self.pipeline_metrics[pipeline_id]
        
        # Update metrics
        metrics.execution_time = (metrics.execution_time + execution_time) / 2  # Moving average
        metrics.healing_attempts += healing_attempts
        
        if status == PipelineStatus.SUCCESS:
            metrics.success_rate = min(1.0, metrics.success_rate + 0.1)
        else:
            metrics.failure_count += 1
            metrics.success_rate = max(0.0, metrics.success_rate - 0.1)
        
        logger.info(f"Updated metrics for pipeline {pipeline_id}: success_rate={metrics.success_rate:.2f}")
    
    async def _analyze_optimization_opportunities(self, pipeline_id: str):
        """Analyze opportunities for pipeline optimization."""
        logger.info(f"Analyzing optimization opportunities for pipeline {pipeline_id}")
        
        try:
            optimization_prompt = f"""
            Analyze the successful pipeline execution for {pipeline_id} and identify optimization opportunities:
            1. Performance improvements (faster execution)
            2. Cost reductions (resource optimization)
            3. Reliability enhancements (reduce flakiness)
            4. Maintainability improvements (better structure)
            
            Provide specific, actionable recommendations with expected impact.
            """
            
            task = self.codegen_agent.run(prompt=optimization_prompt)
            
            while task.status != "completed":
                await asyncio.sleep(5)
                task.refresh()
            
            # Parse optimization recommendations
            optimizations = self._parse_optimization_recommendations(task.result)
            self.optimization_history.extend(optimizations)
            
            # Trigger optimization callbacks
            for callback in self.optimization_callbacks:
                await callback(pipeline_id, optimizations)
            
            logger.info(f"Found {len(optimizations)} optimization opportunities")
            
        except Exception as e:
            logger.error(f"Error analyzing optimization opportunities: {e}")
    
    def _categorize_failure(self, analysis_result: str) -> FailureCategory:
        """Categorize failure based on analysis result."""
        result_lower = analysis_result.lower()
        
        if "test" in result_lower and "fail" in result_lower:
            return FailureCategory.TEST_FAILURE
        elif "build" in result_lower or "compile" in result_lower:
            return FailureCategory.BUILD_FAILURE
        elif "lint" in result_lower or "format" in result_lower:
            return FailureCategory.LINT_FAILURE
        elif "dependency" in result_lower or "import" in result_lower:
            return FailureCategory.DEPENDENCY_FAILURE
        elif "timeout" in result_lower:
            return FailureCategory.TIMEOUT_FAILURE
        elif "infrastructure" in result_lower or "runner" in result_lower:
            return FailureCategory.INFRASTRUCTURE_FAILURE
        else:
            return FailureCategory.UNKNOWN_FAILURE
    
    def _extract_root_cause(self, analysis_result: str) -> str:
        """Extract root cause from analysis result."""
        # Simplified extraction - in practice, use more sophisticated NLP
        lines = analysis_result.split('\n')
        for line in lines:
            if "root cause" in line.lower() or "cause:" in line.lower():
                return line.split(':', 1)[-1].strip()
        return "Unknown root cause"
    
    def _extract_affected_components(self, analysis_result: str) -> List[str]:
        """Extract affected components from analysis result."""
        components = []
        lines = analysis_result.split('\n')
        for line in lines:
            if "affected" in line.lower() or "component" in line.lower():
                # Extract file names or component names
                parts = line.split()
                for part in parts:
                    if '.' in part and ('/' in part or part.endswith('.py') or part.endswith('.js')):
                        components.append(part)
        return components
    
    def _extract_suggested_fixes(self, analysis_result: str) -> List[str]:
        """Extract suggested fixes from analysis result."""
        fixes = []
        lines = analysis_result.split('\n')
        in_fixes_section = False
        
        for line in lines:
            if "suggested" in line.lower() and "fix" in line.lower():
                in_fixes_section = True
                continue
            elif in_fixes_section and line.strip():
                if line.startswith('-') or line.startswith('*') or line.startswith('1.'):
                    fixes.append(line.strip().lstrip('-*1234567890. '))
        
        return fixes
    
    def _calculate_confidence_score(self, analysis_result: str) -> float:
        """Calculate confidence score for the analysis."""
        # Simplified scoring based on content quality
        score = 0.5  # Base score
        
        if "root cause" in analysis_result.lower():
            score += 0.2
        if "suggested fix" in analysis_result.lower():
            score += 0.2
        if len(analysis_result.split()) > 50:  # Detailed analysis
            score += 0.1
        
        return min(1.0, score)
    
    def _extract_healing_strategy(self, analysis_result: str) -> str:
        """Extract healing strategy from analysis result."""
        result_lower = analysis_result.lower()
        
        if "automatic" in result_lower or "auto" in result_lower:
            return "automatic_fix"
        elif "manual" in result_lower:
            return "manual_intervention"
        elif "rerun" in result_lower or "retry" in result_lower:
            return "retry_pipeline"
        else:
            return "investigate_further"
    
    def _parse_optimization_recommendations(self, result: str) -> List[PipelineOptimization]:
        """Parse optimization recommendations from analysis result."""
        optimizations = []
        
        # Simplified parsing - in practice, use more sophisticated NLP
        lines = result.split('\n')
        current_optimization = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if any(keyword in line.lower() for keyword in ['performance', 'cost', 'reliability', 'maintainability']):
                if current_optimization:
                    optimizations.append(current_optimization)
                
                current_optimization = PipelineOptimization(
                    optimization_type=self._extract_optimization_type(line),
                    description=line,
                    expected_improvement=0.1,  # Default 10% improvement
                    implementation_effort="medium",
                    priority=1
                )
            elif current_optimization and line.startswith('-'):
                current_optimization.description += f"\n{line}"
        
        if current_optimization:
            optimizations.append(current_optimization)
        
        return optimizations
    
    def _extract_optimization_type(self, line: str) -> str:
        """Extract optimization type from line."""
        line_lower = line.lower()
        
        if "performance" in line_lower:
            return "performance"
        elif "cost" in line_lower:
            return "cost"
        elif "reliability" in line_lower:
            return "reliability"
        elif "maintainability" in line_lower:
            return "maintainability"
        else:
            return "general"
    
    async def get_pipeline_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive pipeline health report."""
        total_pipelines = len(self.pipeline_metrics)
        if total_pipelines == 0:
            return {"status": "no_data", "message": "No pipeline data available"}
        
        # Calculate aggregate metrics
        avg_success_rate = sum(m.success_rate for m in self.pipeline_metrics.values()) / total_pipelines
        total_failures = sum(m.failure_count for m in self.pipeline_metrics.values())
        total_healing_attempts = sum(m.healing_attempts for m in self.pipeline_metrics.values())
        
        # Recent failure trends
        recent_failures = [f for f in self.failure_history if f.confidence_score > 0.5]
        failure_categories = {}
        for failure in recent_failures:
            category = failure.category.value
            failure_categories[category] = failure_categories.get(category, 0) + 1
        
        return {
            "status": "healthy" if avg_success_rate > 0.8 else "needs_attention",
            "metrics": {
                "total_pipelines": total_pipelines,
                "average_success_rate": avg_success_rate,
                "total_failures": total_failures,
                "total_healing_attempts": total_healing_attempts,
                "healing_success_rate": total_healing_attempts / max(total_failures, 1)
            },
            "failure_analysis": {
                "recent_failures": len(recent_failures),
                "failure_categories": failure_categories,
                "top_failure_category": max(failure_categories.items(), key=lambda x: x[1])[0] if failure_categories else None
            },
            "optimizations": {
                "total_opportunities": len(self.optimization_history),
                "implemented_optimizations": len([o for o in self.optimization_history if o.priority <= 2])
            },
            "recommendations": self._generate_health_recommendations(avg_success_rate, failure_categories)
        }
    
    def _generate_health_recommendations(self, success_rate: float, failure_categories: Dict[str, int]) -> List[str]:
        """Generate health recommendations based on metrics."""
        recommendations = []
        
        if success_rate < 0.7:
            recommendations.append("Pipeline success rate is low - consider enabling auto-healing")
        
        if failure_categories:
            top_category = max(failure_categories.items(), key=lambda x: x[1])[0]
            recommendations.append(f"Most common failure type is {top_category} - focus optimization efforts here")
        
        if len(self.optimization_history) > 5:
            recommendations.append("Multiple optimization opportunities identified - prioritize implementation")
        
        return recommendations
    
    def add_failure_callback(self, callback: Callable):
        """Add a callback for pipeline failures."""
        self.failure_callbacks.append(callback)
    
    def add_success_callback(self, callback: Callable):
        """Add a callback for pipeline successes."""
        self.success_callbacks.append(callback)
    
    def add_optimization_callback(self, callback: Callable):
        """Add a callback for optimization opportunities."""
        self.optimization_callbacks.append(callback)

