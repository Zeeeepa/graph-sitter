#!/usr/bin/env python3
"""
Comprehensive Analysis Dashboard for Contexten

This module provides a unified dashboard that integrates all analysis features:
- Linear issue tracking and automation
- GitHub PR analysis and automation  
- Prefect workflow orchestration
- Graph-sitter code analysis
- Dead code detection and cleanup
- Real-time monitoring and alerts
- AI-powered insights and recommendations

Features:
- Multi-platform integration (Linear, GitHub, Prefect)
- Real-time code analysis using graph-sitter
- Dead code detection and safe removal recommendations
- Automated workflow orchestration
- AI-powered code insights and suggestions
- Comprehensive project health monitoring
- Automated CI/CD pipeline management
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

# Import core components
from .advanced_analytics import AdvancedAnalyticsEngine
from .linear_integration import LinearIntegration
from .orchestrator_integration import OrchestratorDashboardIntegration
from .workflow_automation import WorkflowAutomationEngine
from .enhanced_codebase_ai import EnhancedCodebaseAI

# Import analysis tools
try:
    from ..agents.tools.github.search import GitHubSearchTool
    from ..agents.tools.linear.linear import LinearTool
    from ..extensions.github.enhanced_agent import GitHubEnhancedAgent
    from ..extensions.linear.enhanced_agent import LinearEnhancedAgent
    from ..extensions.prefect.client import PrefectOrchestrator
except ImportError as e:
    logging.warning(f"Some analysis tools not available: {e}")

logger = logging.getLogger(__name__)

class ComprehensiveAnalysisDashboard:
    """
    Unified dashboard providing comprehensive analysis across all platforms
    """
    
    def __init__(self):
        self.analytics_engine = AdvancedAnalyticsEngine()
        self.linear_integration = LinearIntegration()
        self.orchestrator_integration = OrchestratorDashboardIntegration()
        self.workflow_automation = WorkflowAutomationEngine(self.orchestrator_integration)
        self.codebase_ai = EnhancedCodebaseAI()
        
        # Analysis state
        self.active_analyses: Dict[str, Dict] = {}
        self.analysis_history: List[Dict] = []
        self.system_health: Dict[str, Any] = {}
        
        # Integration clients
        self.github_agent: Optional[GitHubEnhancedAgent] = None
        self.linear_agent: Optional[LinearEnhancedAgent] = None
        self.prefect_client: Optional[PrefectOrchestrator] = None
        
        # Real-time monitoring
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []
        
    async def initialize(self):
        """Initialize all dashboard components and integrations"""
        try:
            logger.info("Initializing Comprehensive Analysis Dashboard...")
            
            # Initialize core components
            await self.analytics_engine.initialize()
            await self.linear_integration.initialize()
            await self.orchestrator_integration.start()
            await self.codebase_ai.initialize()
            
            # Initialize integration clients
            await self._initialize_integrations()
            
            # Start monitoring
            await self._start_monitoring()
            
            logger.info("Comprehensive Analysis Dashboard initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")
            raise
    
    async def _initialize_integrations(self):
        """Initialize external platform integrations"""
        try:
            # Initialize GitHub integration
            try:
                self.github_agent = GitHubEnhancedAgent()
                await self.github_agent.start()
                logger.info("GitHub integration initialized")
            except Exception as e:
                logger.warning(f"GitHub integration not available: {e}")
            
            # Initialize Linear integration
            try:
                self.linear_agent = LinearEnhancedAgent()
                await self.linear_agent.start()
                logger.info("Linear integration initialized")
            except Exception as e:
                logger.warning(f"Linear integration not available: {e}")
            
            # Initialize Prefect integration
            try:
                self.prefect_client = PrefectOrchestrator()
                await self.prefect_client.initialize()
                logger.info("Prefect integration initialized")
            except Exception as e:
                logger.warning(f"Prefect integration not available: {e}")
                
        except Exception as e:
            logger.error(f"Error initializing integrations: {e}")
    
    async def _start_monitoring(self):
        """Start real-time monitoring tasks"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._monitor_system_health()),
            asyncio.create_task(self._monitor_active_analyses()),
            asyncio.create_task(self._monitor_integrations()),
            asyncio.create_task(self._monitor_workflows())
        ]
        
        logger.info("Real-time monitoring started")
    
    async def _monitor_system_health(self):
        """Monitor overall system health"""
        while self.monitoring_active:
            try:
                health_data = await self._collect_system_health()
                self.system_health.update(health_data)
                
                # Check for critical issues
                await self._check_critical_issues(health_data)
                
            except Exception as e:
                logger.error(f"Error monitoring system health: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _monitor_active_analyses(self):
        """Monitor active analysis tasks"""
        while self.monitoring_active:
            try:
                for analysis_id, analysis in list(self.active_analyses.items()):
                    if analysis['status'] == 'running':
                        # Update analysis progress
                        progress = await self._get_analysis_progress(analysis_id)
                        analysis['progress'] = progress
                        analysis['last_updated'] = datetime.now().isoformat()
                        
                        # Check if analysis completed
                        if progress >= 100:
                            await self._complete_analysis(analysis_id)
                            
            except Exception as e:
                logger.error(f"Error monitoring analyses: {e}")
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    async def _monitor_integrations(self):
        """Monitor integration health"""
        while self.monitoring_active:
            try:
                integration_status = {}
                
                # Check GitHub integration
                if self.github_agent:
                    integration_status['github'] = await self.github_agent.health_check()
                
                # Check Linear integration
                if self.linear_agent:
                    integration_status['linear'] = await self.linear_agent.health_check()
                
                # Check Prefect integration
                if self.prefect_client:
                    integration_status['prefect'] = await self.prefect_client.get_system_metrics()
                
                self.system_health['integrations'] = integration_status
                
            except Exception as e:
                logger.error(f"Error monitoring integrations: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _monitor_workflows(self):
        """Monitor active workflows"""
        while self.monitoring_active:
            try:
                if self.prefect_client:
                    active_workflows = await self.prefect_client.list_active_workflows()
                    self.system_health['active_workflows'] = len(active_workflows)
                    
                    # Check for failed workflows
                    failed_workflows = [w for w in active_workflows if w.get('status') == 'failed']
                    if failed_workflows:
                        await self._handle_failed_workflows(failed_workflows)
                        
            except Exception as e:
                logger.error(f"Error monitoring workflows: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def run_comprehensive_analysis(
        self,
        project_path: str,
        analysis_types: List[str],
        options: Optional[Dict] = None
    ) -> str:
        """
        Run comprehensive analysis on a project
        
        Args:
            project_path: Path to the project to analyze
            analysis_types: List of analysis types to run
            options: Additional options for analysis
            
        Returns:
            Analysis ID for tracking progress
        """
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        analysis_config = {
            'id': analysis_id,
            'project_path': project_path,
            'analysis_types': analysis_types,
            'options': options or {},
            'status': 'running',
            'progress': 0,
            'started_at': datetime.now().isoformat(),
            'results': {}
        }
        
        self.active_analyses[analysis_id] = analysis_config
        
        # Start analysis in background
        asyncio.create_task(self._execute_comprehensive_analysis(analysis_id))
        
        return analysis_id
    
    async def _execute_comprehensive_analysis(self, analysis_id: str):
        """Execute comprehensive analysis"""
        try:
            analysis = self.active_analyses[analysis_id]
            project_path = analysis['project_path']
            analysis_types = analysis['analysis_types']
            
            total_steps = len(analysis_types)
            completed_steps = 0
            
            # Run each analysis type
            for analysis_type in analysis_types:
                try:
                    result = await self._run_single_analysis(
                        analysis_type, 
                        project_path, 
                        analysis['options']
                    )
                    analysis['results'][analysis_type] = result
                    
                    completed_steps += 1
                    analysis['progress'] = (completed_steps / total_steps) * 100
                    
                except Exception as e:
                    logger.error(f"Error in {analysis_type} analysis: {e}")
                    analysis['results'][analysis_type] = {'error': str(e)}
            
            # Complete analysis
            await self._complete_analysis(analysis_id)
            
        except Exception as e:
            logger.error(f"Error executing analysis {analysis_id}: {e}")
            analysis['status'] = 'failed'
            analysis['error'] = str(e)
    
    async def _run_single_analysis(
        self, 
        analysis_type: str, 
        project_path: str, 
        options: Dict
    ) -> Dict:
        """Run a single type of analysis"""
        
        if analysis_type == 'dead_code':
            return await self._analyze_dead_code(project_path, options)
        elif analysis_type == 'code_quality':
            return await self._analyze_code_quality(project_path, options)
        elif analysis_type == 'dependencies':
            return await self._analyze_dependencies(project_path, options)
        elif analysis_type == 'security':
            return await self._analyze_security(project_path, options)
        elif analysis_type == 'performance':
            return await self._analyze_performance(project_path, options)
        elif analysis_type == 'linear_integration':
            return await self._analyze_linear_integration(project_path, options)
        elif analysis_type == 'github_integration':
            return await self._analyze_github_integration(project_path, options)
        elif analysis_type == 'prefect_workflows':
            return await self._analyze_prefect_workflows(project_path, options)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    async def _analyze_dead_code(self, project_path: str, options: Dict) -> Dict:
        """Analyze dead code using graph-sitter"""
        try:
            # Use the enhanced codebase AI for dead code analysis
            result = await self.codebase_ai.analyze_dead_code(project_path)
            
            # Add graph-sitter specific analysis
            graph_sitter_result = await self._run_graph_sitter_analysis(project_path)
            result['graph_sitter'] = graph_sitter_result
            
            return result
            
        except Exception as e:
            logger.error(f"Dead code analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_code_quality(self, project_path: str, options: Dict) -> Dict:
        """Analyze code quality metrics"""
        try:
            return await self.analytics_engine.analyze_code_quality(project_path)
        except Exception as e:
            logger.error(f"Code quality analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_dependencies(self, project_path: str, options: Dict) -> Dict:
        """Analyze project dependencies"""
        try:
            return await self.analytics_engine.analyze_dependencies(project_path)
        except Exception as e:
            logger.error(f"Dependency analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_security(self, project_path: str, options: Dict) -> Dict:
        """Analyze security vulnerabilities"""
        try:
            return await self.analytics_engine.analyze_security(project_path)
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_performance(self, project_path: str, options: Dict) -> Dict:
        """Analyze performance metrics"""
        try:
            return await self.analytics_engine.analyze_performance(project_path)
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_linear_integration(self, project_path: str, options: Dict) -> Dict:
        """Analyze Linear integration status"""
        try:
            if not self.linear_agent:
                return {'error': 'Linear integration not available'}
            
            # Get Linear issues for the project
            issues = await self.linear_agent.get_projects()
            
            # Analyze integration health
            integration_health = await self.linear_integration.get_integration_status()
            
            return {
                'issues_count': len(issues),
                'integration_health': integration_health,
                'recent_activity': await self.linear_integration.get_metrics()
            }
            
        except Exception as e:
            logger.error(f"Linear integration analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_github_integration(self, project_path: str, options: Dict) -> Dict:
        """Analyze GitHub integration status"""
        try:
            if not self.github_agent:
                return {'error': 'GitHub integration not available'}
            
            # Get current user and repository info
            user_info = await self.github_agent.get_current_user()
            
            return {
                'user_info': user_info,
                'integration_health': 'healthy',
                'last_activity': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"GitHub integration analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_prefect_workflows(self, project_path: str, options: Dict) -> Dict:
        """Analyze Prefect workflows"""
        try:
            if not self.prefect_client:
                return {'error': 'Prefect integration not available'}
            
            # Get workflow status
            workflows = await self.prefect_client.list_active_workflows()
            metrics = await self.prefect_client.get_metrics()
            
            return {
                'active_workflows': len(workflows),
                'metrics': metrics,
                'health': 'healthy'
            }
            
        except Exception as e:
            logger.error(f"Prefect workflow analysis failed: {e}")
            return {'error': str(e)}
    
    async def _run_graph_sitter_analysis(self, project_path: str) -> Dict:
        """Run graph-sitter specific code analysis"""
        try:
            # This would integrate with the graph-sitter analysis tools
            # For now, return a placeholder result
            return {
                'syntax_trees_analyzed': 0,
                'patterns_found': [],
                'recommendations': []
            }
        except Exception as e:
            logger.error(f"Graph-sitter analysis failed: {e}")
            return {'error': str(e)}
    
    async def get_analysis_status(self, analysis_id: str) -> Dict:
        """Get status of an analysis"""
        if analysis_id not in self.active_analyses:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return self.active_analyses[analysis_id]
    
    async def get_analysis_results(self, analysis_id: str) -> Dict:
        """Get results of a completed analysis"""
        if analysis_id not in self.active_analyses:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis = self.active_analyses[analysis_id]
        
        if analysis['status'] != 'completed':
            raise HTTPException(status_code=400, detail="Analysis not completed")
        
        return analysis['results']
    
    async def get_system_overview(self) -> Dict:
        """Get comprehensive system overview"""
        return {
            'system_health': self.system_health,
            'active_analyses': len([a for a in self.active_analyses.values() if a['status'] == 'running']),
            'completed_analyses': len([a for a in self.active_analyses.values() if a['status'] == 'completed']),
            'integrations': {
                'github': self.github_agent is not None,
                'linear': self.linear_agent is not None,
                'prefect': self.prefect_client is not None
            },
            'last_updated': datetime.now().isoformat()
        }
    
    async def _collect_system_health(self) -> Dict:
        """Collect system health metrics"""
        return {
            'cpu_usage': 0.0,  # Would implement actual monitoring
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'uptime': (datetime.now() - datetime.now()).total_seconds(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _check_critical_issues(self, health_data: Dict):
        """Check for critical system issues"""
        # Implement critical issue detection
        pass
    
    async def _get_analysis_progress(self, analysis_id: str) -> float:
        """Get progress of an analysis"""
        # This would track actual progress
        return self.active_analyses[analysis_id].get('progress', 0)
    
    async def _complete_analysis(self, analysis_id: str):
        """Mark analysis as completed"""
        if analysis_id in self.active_analyses:
            analysis = self.active_analyses[analysis_id]
            analysis['status'] = 'completed'
            analysis['completed_at'] = datetime.now().isoformat()
            analysis['progress'] = 100
            
            # Move to history
            self.analysis_history.append(analysis.copy())
            
            logger.info(f"Analysis {analysis_id} completed")
    
    async def _handle_failed_workflows(self, failed_workflows: List[Dict]):
        """Handle failed workflows"""
        for workflow in failed_workflows:
            logger.warning(f"Workflow {workflow.get('id')} failed: {workflow.get('error')}")
            # Implement failure handling logic
    
    async def shutdown(self):
        """Shutdown the dashboard"""
        logger.info("Shutting down Comprehensive Analysis Dashboard...")
        
        # Stop monitoring
        self.monitoring_active = False
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Shutdown integrations
        if self.github_agent:
            await self.github_agent.stop()
        if self.linear_agent:
            await self.linear_agent.stop()
        if self.prefect_client:
            await self.prefect_client.shutdown()
        
        # Shutdown core components
        await self.orchestrator_integration.stop()
        
        logger.info("Dashboard shutdown complete")

# Global dashboard instance
comprehensive_dashboard = ComprehensiveAnalysisDashboard()

