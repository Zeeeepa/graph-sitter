#!/usr/bin/env python3
"""
Grainchain Graph_sitter Integration

Enhanced integration between Grainchain's sandbox management and quality gates
with Graph_sitter's comprehensive code analysis capabilities.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .quality_gates import QualityGateManager, QualityGateDefinition
from .sandbox_manager import SandboxManager, SandboxSession
from .grainchain_types import (
    QualityGateType, QualityGateStatus, QualityGateResult,
    SandboxProvider, ExecutionResult
)

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """Types of Graph_sitter analysis."""
    COMPREHENSIVE = "comprehensive"
    DEAD_CODE = "dead_code"
    COMPLEXITY = "complexity"
    DEPENDENCIES = "dependencies"
    SECURITY = "security"
    CALL_GRAPH = "call_graph"
    CUSTOM = "custom"


class ValidationLevel(str, Enum):
    """Validation strictness levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"
    CUSTOM = "custom"


@dataclass
class AnalysisConfig:
    """Configuration for Graph_sitter analysis."""
    analysis_types: List[AnalysisType]
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    thresholds: Dict[str, Any] = field(default_factory=dict)
    custom_rules: List[Dict[str, Any]] = field(default_factory=list)
    output_format: str = "json"
    include_suggestions: bool = True
    parallel_analysis: bool = True


@dataclass
class AnalysisResult:
    """Result of Graph_sitter analysis."""
    analysis_type: AnalysisType
    status: str
    start_time: float
    end_time: float
    duration: float
    results: Dict[str, Any]
    issues_found: int
    critical_issues: int
    warnings: int
    suggestions: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class QualityValidationResult:
    """Result of quality validation."""
    overall_status: QualityGateStatus
    analysis_results: List[AnalysisResult]
    quality_score: float
    issues_summary: Dict[str, int]
    recommendations: List[str]
    validation_report: Dict[str, Any]


class GraphSitterQualityGates:
    """Enhanced quality gates using Graph_sitter analysis."""
    
    def __init__(self, quality_manager: QualityGateManager, sandbox_manager: SandboxManager):
        """Initialize Graph_sitter quality gates."""
        self.quality_manager = quality_manager
        self.sandbox_manager = sandbox_manager
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        self.validation_callbacks: List[Callable] = []
        
        # Default analysis configurations
        self.default_configs = {
            ValidationLevel.STRICT: AnalysisConfig(
                analysis_types=[
                    AnalysisType.COMPREHENSIVE,
                    AnalysisType.SECURITY,
                    AnalysisType.COMPLEXITY,
                    AnalysisType.DEPENDENCIES
                ],
                thresholds={
                    'max_complexity': 10,
                    'max_function_length': 50,
                    'max_security_issues': 0,
                    'max_critical_issues': 0,
                    'min_test_coverage': 80
                }
            ),
            ValidationLevel.MODERATE: AnalysisConfig(
                analysis_types=[
                    AnalysisType.COMPREHENSIVE,
                    AnalysisType.SECURITY,
                    AnalysisType.COMPLEXITY
                ],
                thresholds={
                    'max_complexity': 15,
                    'max_function_length': 100,
                    'max_security_issues': 2,
                    'max_critical_issues': 1,
                    'min_test_coverage': 60
                }
            ),
            ValidationLevel.LENIENT: AnalysisConfig(
                analysis_types=[
                    AnalysisType.COMPREHENSIVE,
                    AnalysisType.SECURITY
                ],
                thresholds={
                    'max_complexity': 25,
                    'max_function_length': 200,
                    'max_security_issues': 5,
                    'max_critical_issues': 3,
                    'min_test_coverage': 40
                }
            )
        }
        
        logger.info("Graph_sitter quality gates initialized")
    
    def add_validation_callback(self, callback: Callable):
        """Add callback for validation events."""
        self.validation_callbacks.append(callback)
    
    def _emit_validation_event(self, event_type: str, data: Dict[str, Any]):
        """Emit validation event to registered callbacks."""
        for callback in self.validation_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Validation callback failed: {e}")
    
    async def execute_comprehensive_quality_validation(
        self,
        codebase_path: str,
        config: Optional[AnalysisConfig] = None,
        sandbox_provider: Optional[SandboxProvider] = None,
        context: Dict[str, Any] = None
    ) -> QualityValidationResult:
        """Execute comprehensive quality validation using Graph_sitter in sandbox."""
        logger.info(f"Starting comprehensive quality validation for {codebase_path}")
        
        if config is None:
            config = self.default_configs[ValidationLevel.MODERATE]
        
        if context is None:
            context = {}
        
        validation_start_time = time.time()
        
        self._emit_validation_event('validation_started', {
            'codebase_path': codebase_path,
            'analysis_types': [t.value for t in config.analysis_types],
            'validation_level': config.validation_level.value
        })
        
        try:
            # Create sandbox session for isolated analysis
            sandbox_session = await self._create_analysis_sandbox(
                codebase_path=codebase_path,
                provider=sandbox_provider,
                context=context
            )
            
            # Execute analysis in sandbox
            analysis_results = await self._execute_analysis_in_sandbox(
                sandbox_session=sandbox_session,
                config=config,
                context=context
            )
            
            # Validate results against thresholds
            validation_result = await self._validate_analysis_results(
                analysis_results=analysis_results,
                config=config,
                context=context
            )
            
            # Cleanup sandbox
            await self._cleanup_analysis_sandbox(sandbox_session)
            
            validation_result.validation_report['total_duration'] = time.time() - validation_start_time
            
            self._emit_validation_event('validation_completed', {
                'codebase_path': codebase_path,
                'overall_status': validation_result.overall_status.value,
                'quality_score': validation_result.quality_score,
                'duration': validation_result.validation_report['total_duration']
            })
            
            logger.info(f"Quality validation completed: {validation_result.overall_status.value}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            
            self._emit_validation_event('validation_failed', {
                'codebase_path': codebase_path,
                'error': str(e)
            })
            
            # Return failed validation result
            return QualityValidationResult(
                overall_status=QualityGateStatus.FAILED,
                analysis_results=[],
                quality_score=0.0,
                issues_summary={'error': 1},
                recommendations=[f"Validation failed: {str(e)}"],
                validation_report={
                    'error': str(e),
                    'total_duration': time.time() - validation_start_time
                }
            )
    
    async def _create_analysis_sandbox(
        self,
        codebase_path: str,
        provider: Optional[SandboxProvider],
        context: Dict[str, Any]
    ) -> SandboxSession:
        """Create sandbox session for analysis."""
        logger.info("Creating analysis sandbox")
        
        # Configure sandbox for Graph_sitter analysis
        sandbox_config = {
            'provider': provider or SandboxProvider.DOCKER,
            'image': 'python:3.11-slim',  # Base image with Python
            'packages': [
                'graph-sitter',  # Graph_sitter package
                'tree-sitter',   # Tree-sitter dependency
                'numpy',         # For analysis computations
                'pandas'         # For data processing
            ],
            'environment': {
                'PYTHONPATH': '/workspace',
                'ANALYSIS_MODE': 'quality_gates'
            },
            'volumes': {
                codebase_path: '/workspace/codebase'
            },
            'working_directory': '/workspace',
            'timeout': 1800,  # 30 minutes for analysis
            'memory_limit': '2GB',
            'cpu_limit': '2'
        }
        
        # Create sandbox session
        sandbox_session = await self.sandbox_manager.create_session(
            session_id=f"analysis_{int(time.time())}",
            config=sandbox_config,
            context=context
        )
        
        # Install Graph_sitter and dependencies
        await self._setup_analysis_environment(sandbox_session)
        
        return sandbox_session
    
    async def _setup_analysis_environment(self, sandbox_session: SandboxSession):
        """Set up analysis environment in sandbox."""
        logger.info("Setting up analysis environment")
        
        # Install required packages
        install_commands = [
            "pip install --upgrade pip",
            "pip install graph-sitter tree-sitter",
            "pip install numpy pandas matplotlib seaborn",
            "pip install pylint flake8 bandit safety",
            "pip install pytest pytest-cov"
        ]
        
        for command in install_commands:
            result = await sandbox_session.execute_command(command)
            if result.return_code != 0:
                logger.warning(f"Command failed: {command} - {result.stderr}")
        
        # Copy Graph_sitter analysis modules
        copy_commands = [
            "mkdir -p /workspace/analysis",
            "cp -r /workspace/codebase/src/contexten/extensions/graph_sitter/analysis/* /workspace/analysis/ 2>/dev/null || true"
        ]
        
        for command in copy_commands:
            await sandbox_session.execute_command(command)
        
        logger.info("Analysis environment setup completed")
    
    async def _execute_analysis_in_sandbox(
        self,
        sandbox_session: SandboxSession,
        config: AnalysisConfig,
        context: Dict[str, Any]
    ) -> List[AnalysisResult]:
        """Execute Graph_sitter analysis in sandbox."""
        logger.info("Executing Graph_sitter analysis in sandbox")
        
        analysis_results = []
        
        if config.parallel_analysis and len(config.analysis_types) > 1:
            # Execute analyses in parallel
            analysis_tasks = []
            for analysis_type in config.analysis_types:
                task = self._execute_single_analysis(
                    sandbox_session=sandbox_session,
                    analysis_type=analysis_type,
                    config=config,
                    context=context
                )
                analysis_tasks.append(task)
            
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(analysis_results):
                if isinstance(result, Exception):
                    logger.error(f"Analysis {config.analysis_types[i].value} failed: {result}")
                    analysis_results[i] = AnalysisResult(
                        analysis_type=config.analysis_types[i],
                        status='failed',
                        start_time=time.time(),
                        end_time=time.time(),
                        duration=0,
                        results={},
                        issues_found=0,
                        critical_issues=0,
                        warnings=0,
                        error=str(result)
                    )
        else:
            # Execute analyses sequentially
            for analysis_type in config.analysis_types:
                result = await self._execute_single_analysis(
                    sandbox_session=sandbox_session,
                    analysis_type=analysis_type,
                    config=config,
                    context=context
                )
                analysis_results.append(result)
        
        return analysis_results
    
    async def _execute_single_analysis(
        self,
        sandbox_session: SandboxSession,
        analysis_type: AnalysisType,
        config: AnalysisConfig,
        context: Dict[str, Any]
    ) -> AnalysisResult:
        """Execute a single Graph_sitter analysis."""
        logger.info(f"Executing {analysis_type.value} analysis")
        
        start_time = time.time()
        
        try:
            # Create analysis script based on type
            analysis_script = self._create_analysis_script(analysis_type, config)
            
            # Write script to sandbox
            script_path = f"/workspace/run_{analysis_type.value}_analysis.py"
            await sandbox_session.write_file(script_path, analysis_script)
            
            # Execute analysis
            result = await sandbox_session.execute_command(
                f"cd /workspace/codebase && python {script_path}",
                timeout=600  # 10 minutes per analysis
            )
            
            end_time = time.time()
            
            if result.return_code == 0:
                # Parse analysis results
                analysis_output = self._parse_analysis_output(result.stdout, analysis_type)
                
                return AnalysisResult(
                    analysis_type=analysis_type,
                    status='completed',
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    results=analysis_output.get('results', {}),
                    issues_found=analysis_output.get('issues_found', 0),
                    critical_issues=analysis_output.get('critical_issues', 0),
                    warnings=analysis_output.get('warnings', 0),
                    suggestions=analysis_output.get('suggestions', [])
                )
            else:
                logger.error(f"Analysis {analysis_type.value} failed: {result.stderr}")
                return AnalysisResult(
                    analysis_type=analysis_type,
                    status='failed',
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    results={},
                    issues_found=0,
                    critical_issues=0,
                    warnings=0,
                    error=result.stderr
                )
        
        except Exception as e:
            logger.error(f"Analysis {analysis_type.value} exception: {e}")
            end_time = time.time()
            
            return AnalysisResult(
                analysis_type=analysis_type,
                status='failed',
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                results={},
                issues_found=0,
                critical_issues=0,
                warnings=0,
                error=str(e)
            )
    
    def _create_analysis_script(self, analysis_type: AnalysisType, config: AnalysisConfig) -> str:
        """Create Python script for specific analysis type."""
        base_script = '''
import sys
import json
import traceback
from pathlib import Path

# Add analysis modules to path
sys.path.insert(0, '/workspace/analysis')

try:
    from graph_sitter import Codebase
'''
        
        if analysis_type == AnalysisType.COMPREHENSIVE:
            script = base_script + '''
    from main_analyzer import comprehensive_analysis
    
    # Create codebase
    codebase = Codebase(".")
    
    # Run comprehensive analysis
    results = comprehensive_analysis(codebase)
    
    # Output results
    output = {
        "results": results,
        "issues_found": len(results.get("dead_code", {}).get("unused_functions", [])) + 
                       len(results.get("security", {}).get("vulnerabilities", [])),
        "critical_issues": len(results.get("security", {}).get("critical_vulnerabilities", [])),
        "warnings": len(results.get("complexity", {}).get("complex_functions", [])),
        "suggestions": results.get("recommendations", [])
    }
    
    print(json.dumps(output, indent=2))
    
except Exception as e:
    error_output = {
        "error": str(e),
        "traceback": traceback.format_exc(),
        "results": {},
        "issues_found": 0,
        "critical_issues": 0,
        "warnings": 0,
        "suggestions": []
    }
    print(json.dumps(error_output, indent=2))
    sys.exit(1)
'''
        
        elif analysis_type == AnalysisType.DEAD_CODE:
            script = base_script + '''
    from dead_code_detector import detect_dead_code
    
    # Create codebase
    codebase = Codebase(".")
    
    # Run dead code analysis
    results = detect_dead_code(codebase)
    
    # Output results
    output = {
        "results": results,
        "issues_found": len(results.get("unused_functions", [])) + len(results.get("unused_classes", [])),
        "critical_issues": 0,
        "warnings": len(results.get("unused_imports", [])),
        "suggestions": [f"Remove unused function: {func}" for func in results.get("unused_functions", [])]
    }
    
    print(json.dumps(output, indent=2))
    
except Exception as e:
    error_output = {
        "error": str(e),
        "traceback": traceback.format_exc(),
        "results": {},
        "issues_found": 0,
        "critical_issues": 0,
        "warnings": 0,
        "suggestions": []
    }
    print(json.dumps(error_output, indent=2))
    sys.exit(1)
'''
        
        elif analysis_type == AnalysisType.SECURITY:
            script = base_script + '''
    from security_analyzer import analyze_security
    
    # Create codebase
    codebase = Codebase(".")
    
    # Run security analysis
    results = analyze_security(codebase)
    
    # Output results
    vulnerabilities = results.get("vulnerabilities", [])
    critical_vulns = [v for v in vulnerabilities if v.get("severity") == "critical"]
    
    output = {
        "results": results,
        "issues_found": len(vulnerabilities),
        "critical_issues": len(critical_vulns),
        "warnings": len([v for v in vulnerabilities if v.get("severity") == "medium"]),
        "suggestions": [f"Fix {v.get('type', 'vulnerability')}: {v.get('description', '')}" for v in vulnerabilities]
    }
    
    print(json.dumps(output, indent=2))
    
except Exception as e:
    error_output = {
        "error": str(e),
        "traceback": traceback.format_exc(),
        "results": {},
        "issues_found": 0,
        "critical_issues": 0,
        "warnings": 0,
        "suggestions": []
    }
    print(json.dumps(error_output, indent=2))
    sys.exit(1)
'''
        
        elif analysis_type == AnalysisType.COMPLEXITY:
            script = base_script + '''
    from complexity_analyzer import analyze_complexity
    
    # Create codebase
    codebase = Codebase(".")
    
    # Run complexity analysis
    results = analyze_complexity(codebase)
    
    # Output results
    complex_functions = results.get("complex_functions", [])
    max_complexity = config.get("thresholds", {}).get("max_complexity", 15)
    
    output = {
        "results": results,
        "issues_found": len([f for f in complex_functions if f.get("complexity", 0) > max_complexity]),
        "critical_issues": len([f for f in complex_functions if f.get("complexity", 0) > max_complexity * 2]),
        "warnings": len([f for f in complex_functions if f.get("complexity", 0) > max_complexity * 0.8]),
        "suggestions": [f"Refactor complex function: {f.get('name', '')}" for f in complex_functions if f.get("complexity", 0) > max_complexity]
    }
    
    print(json.dumps(output, indent=2))
    
except Exception as e:
    error_output = {
        "error": str(e),
        "traceback": traceback.format_exc(),
        "results": {},
        "issues_found": 0,
        "critical_issues": 0,
        "warnings": 0,
        "suggestions": []
    }
    print(json.dumps(error_output, indent=2))
    sys.exit(1)
'''
        
        else:
            # Default to comprehensive analysis
            script = base_script + '''
    from main_analyzer import comprehensive_analysis
    
    # Create codebase
    codebase = Codebase(".")
    
    # Run analysis
    results = comprehensive_analysis(codebase)
    
    # Output results
    output = {
        "results": results,
        "issues_found": 0,
        "critical_issues": 0,
        "warnings": 0,
        "suggestions": []
    }
    
    print(json.dumps(output, indent=2))
    
except Exception as e:
    error_output = {
        "error": str(e),
        "traceback": traceback.format_exc(),
        "results": {},
        "issues_found": 0,
        "critical_issues": 0,
        "warnings": 0,
        "suggestions": []
    }
    print(json.dumps(error_output, indent=2))
    sys.exit(1)
'''
        
        return script
    
    def _parse_analysis_output(self, output: str, analysis_type: AnalysisType) -> Dict[str, Any]:
        """Parse analysis output from JSON."""
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis output for {analysis_type.value}: {e}")
            return {
                'results': {},
                'issues_found': 0,
                'critical_issues': 0,
                'warnings': 0,
                'suggestions': [],
                'parse_error': str(e)
            }
    
    async def _validate_analysis_results(
        self,
        analysis_results: List[AnalysisResult],
        config: AnalysisConfig,
        context: Dict[str, Any]
    ) -> QualityValidationResult:
        """Validate analysis results against configured thresholds."""
        logger.info("Validating analysis results against thresholds")
        
        # Calculate overall metrics
        total_issues = sum(result.issues_found for result in analysis_results)
        total_critical = sum(result.critical_issues for result in analysis_results)
        total_warnings = sum(result.warnings for result in analysis_results)
        
        # Check against thresholds
        thresholds = config.thresholds
        validation_failures = []
        
        if total_critical > thresholds.get('max_critical_issues', 1):
            validation_failures.append(f"Too many critical issues: {total_critical} > {thresholds.get('max_critical_issues', 1)}")
        
        if total_issues > thresholds.get('max_total_issues', 10):
            validation_failures.append(f"Too many total issues: {total_issues} > {thresholds.get('max_total_issues', 10)}")
        
        # Check specific analysis results
        for result in analysis_results:
            if result.analysis_type == AnalysisType.COMPLEXITY:
                max_complexity = thresholds.get('max_complexity', 15)
                complex_functions = result.results.get('complex_functions', [])
                over_threshold = [f for f in complex_functions if f.get('complexity', 0) > max_complexity]
                if over_threshold:
                    validation_failures.append(f"Functions exceed complexity threshold: {len(over_threshold)} functions > {max_complexity}")
            
            elif result.analysis_type == AnalysisType.SECURITY:
                max_security_issues = thresholds.get('max_security_issues', 2)
                if result.issues_found > max_security_issues:
                    validation_failures.append(f"Too many security issues: {result.issues_found} > {max_security_issues}")
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(analysis_results, config)
        
        # Determine overall status
        if validation_failures:
            overall_status = QualityGateStatus.FAILED
        elif total_warnings > thresholds.get('max_warnings', 20):
            overall_status = QualityGateStatus.WARNING
        else:
            overall_status = QualityGateStatus.PASSED
        
        # Compile recommendations
        recommendations = []
        for result in analysis_results:
            recommendations.extend(result.suggestions)
        
        if validation_failures:
            recommendations.extend([f"Fix validation failure: {failure}" for failure in validation_failures])
        
        # Create validation report
        validation_report = {
            'total_issues': total_issues,
            'critical_issues': total_critical,
            'warnings': total_warnings,
            'validation_failures': validation_failures,
            'thresholds_used': thresholds,
            'analysis_summary': {
                result.analysis_type.value: {
                    'status': result.status,
                    'issues': result.issues_found,
                    'critical': result.critical_issues,
                    'duration': result.duration
                }
                for result in analysis_results
            }
        }
        
        return QualityValidationResult(
            overall_status=overall_status,
            analysis_results=analysis_results,
            quality_score=quality_score,
            issues_summary={
                'total': total_issues,
                'critical': total_critical,
                'warnings': total_warnings,
                'validation_failures': len(validation_failures)
            },
            recommendations=recommendations,
            validation_report=validation_report
        )
    
    def _calculate_quality_score(self, analysis_results: List[AnalysisResult], config: AnalysisConfig) -> float:
        """Calculate overall quality score from analysis results."""
        if not analysis_results:
            return 0.0
        
        # Base score
        score = 100.0
        
        # Deduct points for issues
        for result in analysis_results:
            if result.status == 'failed':
                score -= 20.0  # Major deduction for failed analysis
            else:
                # Deduct based on issues found
                score -= result.critical_issues * 10.0  # 10 points per critical issue
                score -= result.issues_found * 2.0      # 2 points per regular issue
                score -= result.warnings * 0.5          # 0.5 points per warning
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, score))
    
    async def _cleanup_analysis_sandbox(self, sandbox_session: SandboxSession):
        """Clean up analysis sandbox."""
        logger.info("Cleaning up analysis sandbox")
        
        try:
            await self.sandbox_manager.destroy_session(sandbox_session.session_id)
            logger.info("Analysis sandbox cleaned up successfully")
        except Exception as e:
            logger.error(f"Failed to cleanup analysis sandbox: {e}")


# Factory function for easy integration
def create_graph_sitter_quality_gates(
    quality_manager: QualityGateManager,
    sandbox_manager: SandboxManager
) -> GraphSitterQualityGates:
    """Create and initialize Graph_sitter quality gates."""
    return GraphSitterQualityGates(quality_manager, sandbox_manager)

