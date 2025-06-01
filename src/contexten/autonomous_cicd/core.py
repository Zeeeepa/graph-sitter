"""
Core Autonomous CI/CD System

This module provides the main orchestrator for autonomous CI/CD operations
using the Codegen SDK for intelligent automation.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.logging.get_logger import get_logger

from .config import CICDConfig
from .agents import CodeAnalysisAgent, TestingAgent, DeploymentAgent
from .triggers import GitHubTrigger, LinearTrigger, ScheduledTrigger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Result of a CI/CD pipeline execution"""
    pipeline_id: str
    status: str  # 'success', 'failure', 'partial', 'cancelled'
    start_time: float
    end_time: float
    stages: Dict[str, Any]
    artifacts: List[str]
    errors: List[str]
    metrics: Dict[str, float]


@dataclass
class PipelineStage:
    """Individual stage in the CI/CD pipeline"""
    name: str
    status: str
    start_time: float
    end_time: Optional[float] = None
    output: Optional[str] = None
    error: Optional[str] = None
    artifacts: List[str] = None


class AutonomousCICD:
    """
    Autonomous CI/CD system with Codegen SDK integration
    
    Provides intelligent automation for:
    - Code analysis and quality assessment
    - Automated testing and validation
    - Deployment orchestration
    - Issue detection and resolution
    """
    
    def __init__(self, config: CICDConfig):
        self.config = config
        self.codebase = None
        self.active_pipelines: Dict[str, PipelineResult] = {}
        self.pipeline_history: List[PipelineResult] = []
        
        # Initialize agents
        self.code_analysis_agent = CodeAnalysisAgent(config)
        self.testing_agent = TestingAgent(config)
        self.deployment_agent = DeploymentAgent(config)
        
        # Initialize triggers
        self.triggers = {
            'github': GitHubTrigger(config, self),
            'linear': LinearTrigger(config, self),
            'scheduled': ScheduledTrigger(config, self)
        }
        
        logger.info("Autonomous CI/CD system initialized")
    
    async def initialize(self):
        """Initialize the CI/CD system"""
        try:
            # Initialize codebase
            self.codebase = Codebase.from_path(self.config.repo_path)
            logger.info(f"Codebase loaded: {self.codebase.summary}")
            
            # Initialize agents
            await self.code_analysis_agent.initialize()
            await self.testing_agent.initialize()
            await self.deployment_agent.initialize()
            
            # Start triggers
            for name, trigger in self.triggers.items():
                try:
                    await trigger.start()
                    logger.info(f"Started {name} trigger")
                except Exception as e:
                    logger.error(f"Failed to start {name} trigger: {e}")
            
            logger.info("Autonomous CI/CD system ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize CI/CD system: {e}")
            raise
    
    async def execute_pipeline(self, 
                             trigger_event: Dict[str, Any],
                             pipeline_type: str = "full") -> PipelineResult:
        """
        Execute a complete CI/CD pipeline
        
        Args:
            trigger_event: Event that triggered the pipeline
            pipeline_type: Type of pipeline ('full', 'analysis', 'test', 'deploy')
        
        Returns:
            Pipeline execution result
        """
        pipeline_id = f"pipeline_{int(time.time() * 1000)}"
        start_time = time.time()
        
        logger.info(f"Starting pipeline {pipeline_id} (type: {pipeline_type})")
        
        result = PipelineResult(
            pipeline_id=pipeline_id,
            status='running',
            start_time=start_time,
            end_time=0,
            stages={},
            artifacts=[],
            errors=[],
            metrics={}
        )
        
        self.active_pipelines[pipeline_id] = result
        
        try:
            # Stage 1: Code Analysis
            if self.config.enable_code_analysis:
                analysis_stage = await self._execute_analysis_stage(trigger_event)
                result.stages['analysis'] = analysis_stage
                
                if analysis_stage.status == 'failure':
                    result.status = 'failure'
                    result.errors.append(f"Code analysis failed: {analysis_stage.error}")
                    return result
            
            # Stage 2: Testing
            if self.config.enable_auto_testing and pipeline_type in ['full', 'test']:
                testing_stage = await self._execute_testing_stage(trigger_event)
                result.stages['testing'] = testing_stage
                
                if testing_stage.status == 'failure':
                    result.status = 'failure'
                    result.errors.append(f"Testing failed: {testing_stage.error}")
                    return result
            
            # Stage 3: Deployment
            if self.config.enable_auto_deployment and pipeline_type in ['full', 'deploy']:
                deployment_stage = await self._execute_deployment_stage(trigger_event)
                result.stages['deployment'] = deployment_stage
                
                if deployment_stage.status == 'failure':
                    result.status = 'partial'
                    result.errors.append(f"Deployment failed: {deployment_stage.error}")
                else:
                    result.status = 'success'
            else:
                result.status = 'success'
            
            # Calculate metrics
            result.metrics = self._calculate_pipeline_metrics(result)
            
        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} failed: {e}")
            result.status = 'failure'
            result.errors.append(str(e))
        
        finally:
            result.end_time = time.time()
            self.pipeline_history.append(result)
            if pipeline_id in self.active_pipelines:
                del self.active_pipelines[pipeline_id]
            
            logger.info(f"Pipeline {pipeline_id} completed with status: {result.status}")
        
        return result
    
    async def _execute_analysis_stage(self, trigger_event: Dict[str, Any]) -> PipelineStage:
        """Execute code analysis stage"""
        stage = PipelineStage(
            name='analysis',
            status='running',
            start_time=time.time(),
            artifacts=[]
        )
        
        try:
            # Run code analysis using Codegen SDK
            analysis_result = await self.code_analysis_agent.analyze_changes(
                trigger_event.get('changes', []),
                trigger_event.get('branch', self.config.target_branch)
            )
            
            stage.status = 'success' if analysis_result.quality_score >= self.config.code_quality_threshold else 'failure'
            stage.output = f"Quality score: {analysis_result.quality_score:.2f}"
            stage.artifacts = analysis_result.artifacts
            
            if stage.status == 'failure':
                stage.error = f"Code quality below threshold: {analysis_result.quality_score:.2f} < {self.config.code_quality_threshold}"
            
        except Exception as e:
            stage.status = 'failure'
            stage.error = str(e)
            logger.error(f"Analysis stage failed: {e}")
        
        finally:
            stage.end_time = time.time()
        
        return stage
    
    async def _execute_testing_stage(self, trigger_event: Dict[str, Any]) -> PipelineStage:
        """Execute testing stage"""
        stage = PipelineStage(
            name='testing',
            status='running',
            start_time=time.time(),
            artifacts=[]
        )
        
        try:
            # Run automated tests using Codegen SDK
            test_result = await self.testing_agent.run_tests(
                trigger_event.get('changes', []),
                trigger_event.get('branch', self.config.target_branch)
            )
            
            stage.status = 'success' if test_result.coverage >= self.config.test_coverage_threshold else 'failure'
            stage.output = f"Coverage: {test_result.coverage:.2f}%, Tests: {test_result.passed}/{test_result.total}"
            stage.artifacts = test_result.artifacts
            
            if stage.status == 'failure':
                stage.error = f"Test coverage below threshold: {test_result.coverage:.2f}% < {self.config.test_coverage_threshold * 100}%"
            
        except Exception as e:
            stage.status = 'failure'
            stage.error = str(e)
            logger.error(f"Testing stage failed: {e}")
        
        finally:
            stage.end_time = time.time()
        
        return stage
    
    async def _execute_deployment_stage(self, trigger_event: Dict[str, Any]) -> PipelineStage:
        """Execute deployment stage"""
        stage = PipelineStage(
            name='deployment',
            status='running',
            start_time=time.time(),
            artifacts=[]
        )
        
        try:
            # Run deployment using Codegen SDK
            deploy_result = await self.deployment_agent.deploy(
                trigger_event.get('branch', self.config.target_branch),
                trigger_event.get('environment', 'staging')
            )
            
            stage.status = 'success' if deploy_result.success else 'failure'
            stage.output = f"Deployed to {deploy_result.environment}: {deploy_result.url}"
            stage.artifacts = deploy_result.artifacts
            
            if stage.status == 'failure':
                stage.error = deploy_result.error
            
        except Exception as e:
            stage.status = 'failure'
            stage.error = str(e)
            logger.error(f"Deployment stage failed: {e}")
        
        finally:
            stage.end_time = time.time()
        
        return stage
    
    def _calculate_pipeline_metrics(self, result: PipelineResult) -> Dict[str, float]:
        """Calculate pipeline performance metrics"""
        total_duration = result.end_time - result.start_time
        
        metrics = {
            'total_duration': total_duration,
            'success_rate': 1.0 if result.status == 'success' else 0.0,
            'stage_count': len(result.stages),
            'error_count': len(result.errors)
        }
        
        # Calculate stage-specific metrics
        for stage_name, stage in result.stages.items():
            if hasattr(stage, 'end_time') and stage.end_time:
                stage_duration = stage.end_time - stage.start_time
                metrics[f'{stage_name}_duration'] = stage_duration
                metrics[f'{stage_name}_success'] = 1.0 if stage.status == 'success' else 0.0
        
        return metrics
    
    async def get_pipeline_status(self, pipeline_id: str) -> Optional[PipelineResult]:
        """Get status of a specific pipeline"""
        if pipeline_id in self.active_pipelines:
            return self.active_pipelines[pipeline_id]
        
        for result in self.pipeline_history:
            if result.pipeline_id == pipeline_id:
                return result
        
        return None
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        total_pipelines = len(self.pipeline_history)
        successful_pipelines = sum(1 for p in self.pipeline_history if p.status == 'success')
        
        return {
            'total_pipelines': total_pipelines,
            'successful_pipelines': successful_pipelines,
            'success_rate': successful_pipelines / total_pipelines if total_pipelines > 0 else 0.0,
            'active_pipelines': len(self.active_pipelines),
            'average_duration': sum(p.end_time - p.start_time for p in self.pipeline_history) / total_pipelines if total_pipelines > 0 else 0.0,
            'config': self.config.to_dict()
        }
    
    async def shutdown(self):
        """Shutdown the CI/CD system"""
        logger.info("Shutting down Autonomous CI/CD system")
        
        # Stop triggers
        for name, trigger in self.triggers.items():
            try:
                await trigger.stop()
                logger.info(f"Stopped {name} trigger")
            except Exception as e:
                logger.error(f"Error stopping {name} trigger: {e}")
        
        # Cancel active pipelines
        for pipeline_id in list(self.active_pipelines.keys()):
            pipeline = self.active_pipelines[pipeline_id]
            pipeline.status = 'cancelled'
            pipeline.end_time = time.time()
            self.pipeline_history.append(pipeline)
            del self.active_pipelines[pipeline_id]
        
        logger.info("Autonomous CI/CD system shutdown complete")

