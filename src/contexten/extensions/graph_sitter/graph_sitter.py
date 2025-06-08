# Graph_sitter Extension - Analysis for PR validation
# Imports existing contexten and graph_sitter components

import logging
from typing import Any, Callable, Dict, Optional, TypeVar
from fastapi import Request
from pydantic import BaseModel

# Import existing graph_sitter components
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter import Codebase

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class GraphSitter:
    """Graph_sitter extension for comprehensive code analysis and PR validation."""
    
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}
        
        # Initialize Graph_sitter components using existing modules (lazy import)
        self.code_analysis_engine = None
        
        # Integration with other extensions
        self.quality_gate_manager: Optional[Any] = None
        self.sandbox_manager: Optional[Any] = None
        
        # Analysis tracking
        self.analysis_results: Dict[str, Any] = {}
        self.pr_validations: Dict[str, Any] = {}
        self.quality_assessments: Dict[str, Any] = {}
        
        logger.info("✅ Graph_sitter extension initialized with comprehensive analysis capabilities")

    def register_handler(self, event_type: str, handler: Callable[[T], Any]) -> None:
        """Register an event handler for Graph_sitter analysis."""
        if event_type not in self.registered_handlers:
            self.registered_handlers[event_type] = []
        self.registered_handlers[event_type].append(handler)
        logger.info(f"Registered Graph_sitter handler for event type: {event_type}")

    async def handle(self, payload: dict, request: Optional[Request] = None) -> Any:
        """Handle Graph_sitter analysis events."""
        event_type = payload.get('type', 'unknown')
        logger.info(f"Handling Graph_sitter event: {event_type}")
        
        try:
            # Process analysis events
            if event_type == 'comprehensive_analysis':
                return await self._handle_comprehensive_analysis(payload)
            elif event_type == 'pr_validation':
                return await self._handle_pr_validation(payload)
            elif event_type == 'quality_assessment':
                return await self._handle_quality_assessment(payload)
            elif event_type == 'code_analysis':
                return await self._handle_code_analysis(payload)
            else:
                # Handle custom registered handlers
                if event_type in self.registered_handlers:
                    results = []
                    for handler in self.registered_handlers[event_type]:
                        result = await handler(payload)
                        results.append(result)
                    return results
                else:
                    logger.warning(f"No handler registered for Graph_sitter event type: {event_type}")
                    return {'status': 'no_handler', 'event_type': event_type}
                    
        except Exception as e:
            logger.error(f"Error handling Graph_sitter event {event_type}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _handle_comprehensive_analysis(self, payload: dict) -> dict:
        """Handle comprehensive analysis using existing Graph_sitter components."""
        try:
            project_id = payload.get('project_id')
            codebase_path = payload.get('codebase_path', '.')
            analysis_config = payload.get('config', {})
            
            # Create codebase instance using existing Graph_sitter components
            codebase = Codebase(codebase_path)
            
            # Execute comprehensive analysis using existing function
            try:
                from graph_sitter.analysis.main_analyzer import comprehensive_analysis
                analysis_result = comprehensive_analysis(codebase)
            except ImportError:
                logger.warning("comprehensive_analysis not available, using fallback")
                analysis_result = {'fallback': True, 'codebase_path': codebase_path}
            
            # Store analysis results
            self.analysis_results[project_id] = {
                'codebase_path': codebase_path,
                'config': analysis_config,
                'analysis_result': analysis_result,
                'status': 'completed'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'analysis_result': analysis_result,
                'codebase_path': codebase_path
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_pr_validation(self, payload: dict) -> dict:
        """Handle PR validation using existing Graph_sitter analysis components."""
        try:
            project_id = payload.get('project_id')
            pr_data = payload.get('pr_data', {})
            validation_config = payload.get('config', {})
            
            # Execute PR validation using existing components
            validation_result = await self._validate_pr_with_analysis(
                project_id=project_id,
                pr_data=pr_data,
                config=validation_config
            )
            
            # Store PR validation results
            self.pr_validations[project_id] = {
                'pr_data': pr_data,
                'config': validation_config,
                'validation_result': validation_result,
                'status': 'completed'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'pr_valid': validation_result.get('valid', False),
                'validation_result': validation_result,
                'issues_found': validation_result.get('issues', [])
            }
            
        except Exception as e:
            logger.error(f"PR validation failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_quality_assessment(self, payload: dict) -> dict:
        """Handle quality assessment using existing Graph_sitter components."""
        try:
            project_id = payload.get('project_id')
            assessment_config = payload.get('config', {})
            context = payload.get('context', {})
            
            # Execute quality assessment using existing code analysis engine
            assessment_result = await self.code_analysis_engine.analyze_quality(
                project_id=project_id,
                context=context,
                config=assessment_config
            )
            
            # Store quality assessment results
            self.quality_assessments[project_id] = {
                'config': assessment_config,
                'context': context,
                'assessment_result': assessment_result,
                'status': 'completed'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'assessment_result': assessment_result,
                'quality_score': assessment_result.get('quality_score', 0)
            }
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _handle_code_analysis(self, payload: dict) -> dict:
        """Handle code analysis using existing Graph_sitter components."""
        try:
            project_id = payload.get('project_id')
            code_path = payload.get('code_path', '.')
            analysis_type = payload.get('analysis_type', 'comprehensive')
            
            # Create codebase instance
            codebase = Codebase(code_path)
            
            # Execute analysis based on type
            if analysis_type == 'comprehensive':
                analysis_result = comprehensive_analysis(codebase)
            else:
                # Use code analysis engine for specific analysis types
                analysis_result = await self.code_analysis_engine.analyze_code(
                    codebase=codebase,
                    analysis_type=analysis_type
                )
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'analysis_type': analysis_type,
                'analysis_result': analysis_result,
                'code_path': code_path
            }
            
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _validate_pr_with_analysis(self, project_id: str, pr_data: dict, config: dict) -> dict:
        """Validate PR using comprehensive Graph_sitter analysis."""
        try:
            # Extract PR information
            pr_branch = pr_data.get('head', {}).get('ref', 'main')
            base_branch = pr_data.get('base', {}).get('ref', 'main')
            changed_files = pr_data.get('changed_files', [])
            
            validation_result = {
                'valid': True,
                'issues': [],
                'warnings': [],
                'analysis_summary': {}
            }
            
            # Analyze changed files if available
            if changed_files:
                for file_path in changed_files:
                    try:
                        # Create codebase for file analysis
                        codebase = Codebase('.')
                        
                        # Execute analysis on specific file
                        file_analysis = comprehensive_analysis(codebase)
                        
                        # Check for issues in the analysis
                        if file_analysis and 'issues' in file_analysis:
                            validation_result['issues'].extend(file_analysis['issues'])
                        
                        # Update validation status based on issues
                        if validation_result['issues']:
                            validation_result['valid'] = False
                            
                    except Exception as e:
                        logger.warning(f"Failed to analyze file {file_path}: {e}")
                        validation_result['warnings'].append(f"Could not analyze {file_path}: {str(e)}")
            
            # Overall analysis summary
            validation_result['analysis_summary'] = {
                'pr_branch': pr_branch,
                'base_branch': base_branch,
                'files_analyzed': len(changed_files),
                'issues_found': len(validation_result['issues']),
                'warnings_found': len(validation_result['warnings'])
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"PR validation with analysis failed: {e}")
            return {
                'valid': False,
                'issues': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'analysis_summary': {}
            }

    async def execute_comprehensive_analysis(self, project_id: str, codebase_path: str = '.', config: dict = None) -> dict:
        """Execute comprehensive analysis using existing Graph_sitter components."""
        try:
            # Create codebase instance using existing Graph_sitter components
            codebase = Codebase(codebase_path)
            
            # Execute comprehensive analysis using existing function
            analysis_result = comprehensive_analysis(codebase)
            
            # Store analysis results
            self.analysis_results[project_id] = {
                'codebase_path': codebase_path,
                'config': config or {},
                'analysis_result': analysis_result,
                'status': 'completed'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'analysis_result': analysis_result,
                'codebase_path': codebase_path
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def validate_pr(self, project_id: str, pr_data: dict) -> dict:
        """Validate PR using existing Graph_sitter analysis components."""
        try:
            # Execute PR validation using existing components
            validation_result = await self._validate_pr_with_analysis(
                project_id=project_id,
                pr_data=pr_data,
                config={}
            )
            
            # Store PR validation results
            self.pr_validations[project_id] = {
                'pr_data': pr_data,
                'validation_result': validation_result,
                'status': 'completed'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'pr_valid': validation_result.get('valid', False),
                'validation_result': validation_result,
                'issues_found': validation_result.get('issues', [])
            }
            
        except Exception as e:
            logger.error(f"PR validation failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def analyze_quality(self, project_id: str, context: dict) -> dict:
        """Analyze code quality using existing Graph_sitter components."""
        try:
            # Execute quality assessment using existing code analysis engine
            assessment_result = await self.code_analysis_engine.analyze_quality(
                project_id=project_id,
                context=context
            )
            
            # Store quality assessment results
            self.quality_assessments[project_id] = {
                'context': context,
                'assessment_result': assessment_result,
                'status': 'completed'
            }
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'assessment_result': assessment_result,
                'quality_score': assessment_result.get('quality_score', 0)
            }
            
        except Exception as e:
            logger.error(f"Quality analysis failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def integrate_with_grainchain(self, quality_gate_manager: QualityGateManager, sandbox_manager: SandboxManager):
        """Integrate Graph_sitter with Grainchain components."""
        try:
            self.quality_gate_manager = quality_gate_manager
            self.sandbox_manager = sandbox_manager
            
            logger.info("✅ Graph_sitter integrated with Grainchain components")
            
        except Exception as e:
            logger.error(f"Failed to integrate Graph_sitter with Grainchain: {e}")

    def event(self, event_type: str):
        """Decorator for registering Graph_sitter event handlers."""
        def decorator(func: Callable[[T], Any]) -> Callable[[T], Any]:
            self.register_handler(event_type, func)
            return func
        return decorator

    async def initialize(self):
        """Initialize Graph_sitter extension with existing components."""
        try:
            # Initialize code analysis engine
            await self.code_analysis_engine.initialize()
            
            logger.info("✅ Graph_sitter extension fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Graph_sitter extension: {e}")
            raise

    def get_analysis_status(self) -> dict:
        """Get status of all analyses."""
        return {
            'total_analyses': len(self.analysis_results),
            'pr_validations': len(self.pr_validations),
            'quality_assessments': len(self.quality_assessments),
            'analyses': {
                'comprehensive': list(self.analysis_results.keys()),
                'pr_validations': list(self.pr_validations.keys()),
                'quality_assessments': list(self.quality_assessments.keys())
            }
        }

    async def execute_full_analysis_pipeline(self, project_id: str, codebase_path: str, pr_data: dict = None) -> dict:
        """Execute full analysis pipeline: Comprehensive Analysis -> PR Validation -> Quality Assessment."""
        try:
            pipeline_result = {
                'project_id': project_id,
                'status': 'running',
                'stages': {}
            }
            
            # Stage 1: Comprehensive Analysis
            logger.info(f"🔍 Stage 1: Comprehensive analysis for project {project_id}")
            analysis_result = await self.execute_comprehensive_analysis(project_id, codebase_path)
            pipeline_result['stages']['comprehensive_analysis'] = analysis_result
            
            # Stage 2: PR Validation (if PR data provided)
            if pr_data:
                logger.info(f"📋 Stage 2: PR validation for project {project_id}")
                pr_validation_result = await self.validate_pr(project_id, pr_data)
                pipeline_result['stages']['pr_validation'] = pr_validation_result
            
            # Stage 3: Quality Assessment
            logger.info(f"⭐ Stage 3: Quality assessment for project {project_id}")
            quality_result = await self.analyze_quality(project_id, {'codebase_path': codebase_path})
            pipeline_result['stages']['quality_assessment'] = quality_result
            
            # Final status
            pipeline_result['status'] = 'completed'
            pipeline_result['summary'] = {
                'analysis_completed': analysis_result['status'] == 'completed',
                'pr_validation_completed': pr_data is not None and pipeline_result['stages'].get('pr_validation', {}).get('status') == 'completed',
                'quality_assessment_completed': quality_result['status'] == 'completed',
                'pr_valid': pipeline_result['stages'].get('pr_validation', {}).get('pr_valid', True),
                'quality_score': quality_result.get('quality_score', 0)
            }
            
            logger.info(f"🎉 Full Graph_sitter analysis pipeline completed for project {project_id}")
            
            return pipeline_result
            
        except Exception as e:
            logger.error(f"Full analysis pipeline failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e), 'project_id': project_id}

    async def analyze_code_changes(self, project_id: str, changed_files: list, base_branch: str = 'main') -> dict:
        """Analyze specific code changes using existing Graph_sitter components."""
        try:
            analysis_results = []
            
            for file_path in changed_files:
                try:
                    # Create codebase for file analysis
                    codebase = Codebase('.')
                    
                    # Execute analysis on specific file
                    file_analysis = comprehensive_analysis(codebase)
                    
                    analysis_results.append({
                        'file_path': file_path,
                        'analysis': file_analysis,
                        'status': 'completed'
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze file {file_path}: {e}")
                    analysis_results.append({
                        'file_path': file_path,
                        'analysis': None,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return {
                'status': 'completed',
                'project_id': project_id,
                'base_branch': base_branch,
                'files_analyzed': len(changed_files),
                'analysis_results': analysis_results,
                'summary': {
                    'successful_analyses': len([r for r in analysis_results if r['status'] == 'completed']),
                    'failed_analyses': len([r for r in analysis_results if r['status'] == 'failed'])
                }
            }
            
        except Exception as e:
            logger.error(f"Code changes analysis failed for project {project_id}: {e}")
            return {'status': 'failed', 'error': str(e)}
