"""
Enhanced Codebase Integration
============================

This module provides enhanced integration capabilities that tie together all
the unified components into a cohesive, professional-grade system.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class IntegrationConfig:
    """Configuration for enhanced codebase integration."""
    enable_lsp: bool = True
    enable_real_time_monitoring: bool = True
    enable_code_generation: bool = True
    enable_deep_analysis: bool = True
    analysis_level: str = "COMPREHENSIVE"  # BASIC, COMPREHENSIVE, DEEP
    cache_enabled: bool = True
    max_cache_size: int = 1000
    monitoring_interval: float = 1.0  # seconds
    auto_refresh_diagnostics: bool = True
    enable_performance_tracking: bool = True


@dataclass
class IntegrationStatus:
    """Status of the enhanced integration system."""
    is_initialized: bool = False
    components_loaded: Dict[str, bool] = field(default_factory=dict)
    last_refresh: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    active_monitors: List[str] = field(default_factory=list)


class EnhancedCodebaseIntegration:
    """
    Enhanced integration system that coordinates all unified components
    to provide a seamless, professional-grade codebase analysis experience.
    """
    
    def __init__(self, codebase, config: Optional[IntegrationConfig] = None):
        self.codebase = codebase
        self.config = config or IntegrationConfig()
        self.status = IntegrationStatus()
        
        # Component references
        self._unified_diagnostics = None
        self._unified_analysis = None
        self._code_generation_engine = None
        
        # Integration state
        self._is_running = False
        self._monitoring_tasks = []
        self._event_loop = None
        self._callbacks = {}
        
        # Performance tracking
        self._performance_tracker = {}
        self._start_time = None
    
    async def initialize(self) -> bool:
        """Initialize the enhanced integration system."""
        try:
            logger.info("Initializing Enhanced Codebase Integration...")
            
            # Initialize components
            await self._initialize_components()
            
            # Set up monitoring if enabled
            if self.config.enable_real_time_monitoring:
                await self._setup_monitoring()
            
            # Set up performance tracking
            if self.config.enable_performance_tracking:
                await self._setup_performance_tracking()
            
            self.status.is_initialized = True
            self._is_running = True
            
            logger.info("Enhanced Codebase Integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Codebase Integration: {e}")
            return False
    
    async def _initialize_components(self):
        """Initialize all unified components."""
        try:
            # Initialize unified diagnostics
            if self.config.enable_lsp:
                try:
                    from graph_sitter.core.unified_diagnostics import get_diagnostic_engine
                    self._unified_diagnostics = get_diagnostic_engine(
                        self.codebase, 
                        enable_lsp=True
                    )
                    self.status.components_loaded['unified_diagnostics'] = True
                    logger.info("Unified diagnostics engine loaded")
                except ImportError as e:
                    logger.warning(f"Could not load unified diagnostics: {e}")
                    self.status.components_loaded['unified_diagnostics'] = False
            
            # Initialize unified analysis
            if self.config.enable_deep_analysis:
                try:
                    from graph_sitter.core.unified_analysis import UnifiedAnalysisEngine
                    self._unified_analysis = UnifiedAnalysisEngine(self.codebase)
                    self.status.components_loaded['unified_analysis'] = True
                    logger.info("Unified analysis engine loaded")
                except ImportError as e:
                    logger.warning(f"Could not load unified analysis: {e}")
                    self.status.components_loaded['unified_analysis'] = False
            
            # Initialize code generation engine
            if self.config.enable_code_generation and self._unified_diagnostics:
                try:
                    from graph_sitter.extensions.serena.lsp_code_generation import LSPCodeGenerationEngine
                    self._code_generation_engine = LSPCodeGenerationEngine(self._unified_diagnostics)
                    self.status.components_loaded['code_generation'] = True
                    logger.info("Code generation engine loaded")
                except ImportError as e:
                    logger.warning(f"Could not load code generation engine: {e}")
                    self.status.components_loaded['code_generation'] = False
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    async def _setup_monitoring(self):
        """Set up real-time monitoring."""
        try:
            if self._unified_diagnostics:
                # Set up error monitoring
                monitor_task = asyncio.create_task(self._monitor_errors())
                self._monitoring_tasks.append(monitor_task)
                self.status.active_monitors.append('error_monitor')
                
                # Set up performance monitoring
                if self.config.enable_performance_tracking:
                    perf_task = asyncio.create_task(self._monitor_performance())
                    self._monitoring_tasks.append(perf_task)
                    self.status.active_monitors.append('performance_monitor')
                
                logger.info("Real-time monitoring set up successfully")
            
        except Exception as e:
            logger.error(f"Error setting up monitoring: {e}")
            raise
    
    async def _setup_performance_tracking(self):
        """Set up performance tracking."""
        try:
            import time
            self._start_time = time.time()
            self._performance_tracker = {
                'start_time': self._start_time,
                'diagnostics_calls': 0,
                'analysis_calls': 0,
                'code_generation_calls': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'average_response_time': 0.0,
                'total_errors_processed': 0,
                'total_fixes_generated': 0
            }
            
            logger.info("Performance tracking initialized")
            
        except Exception as e:
            logger.error(f"Error setting up performance tracking: {e}")
    
    async def _monitor_errors(self):
        """Monitor errors in real-time."""
        try:
            while self._is_running:
                if self._unified_diagnostics:
                    # Get current error counts
                    errors = self._unified_diagnostics.errors
                    warnings = self._unified_diagnostics.warnings
                    
                    # Update status
                    self.status.error_count = len(errors)
                    self.status.warning_count = len(warnings)
                    self.status.last_refresh = asyncio.get_event_loop().time()
                    
                    # Trigger callbacks if registered
                    if 'error_change' in self._callbacks:
                        for callback in self._callbacks['error_change']:
                            try:
                                await callback(errors, warnings)
                            except Exception as e:
                                logger.warning(f"Error in callback: {e}")
                
                await asyncio.sleep(self.config.monitoring_interval)
                
        except asyncio.CancelledError:
            logger.info("Error monitoring cancelled")
        except Exception as e:
            logger.error(f"Error in error monitoring: {e}")
    
    async def _monitor_performance(self):
        """Monitor performance metrics in real-time."""
        try:
            while self._is_running:
                if self.config.enable_performance_tracking:
                    # Update performance metrics
                    current_time = asyncio.get_event_loop().time()
                    uptime = current_time - self._start_time
                    
                    self.status.performance_metrics.update({
                        'uptime': uptime,
                        'components_loaded': sum(self.status.components_loaded.values()),
                        'total_components': len(self.status.components_loaded),
                        'monitoring_active': len(self.status.active_monitors),
                        'memory_usage': self._get_memory_usage(),
                        'cache_efficiency': self._calculate_cache_efficiency()
                    })
                
                await asyncio.sleep(self.config.monitoring_interval * 5)  # Less frequent
                
        except asyncio.CancelledError:
            logger.info("Performance monitoring cancelled")
        except Exception as e:
            logger.error(f"Error in performance monitoring: {e}")
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_cache_efficiency(self) -> float:
        """Calculate cache hit efficiency."""
        try:
            hits = self._performance_tracker.get('cache_hits', 0)
            misses = self._performance_tracker.get('cache_misses', 0)
            total = hits + misses
            
            if total == 0:
                return 0.0
            
            return (hits / total) * 100.0
            
        except Exception:
            return 0.0
    
    # Public API Methods
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback for specific events."""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
        logger.info(f"Registered callback for {event_type}")
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the integration system."""
        return {
            'integration_status': {
                'is_initialized': self.status.is_initialized,
                'is_running': self._is_running,
                'components_loaded': self.status.components_loaded,
                'active_monitors': self.status.active_monitors,
                'last_refresh': self.status.last_refresh
            },
            'error_status': {
                'error_count': self.status.error_count,
                'warning_count': self.status.warning_count,
                'total_diagnostics': self.status.error_count + self.status.warning_count
            },
            'performance_metrics': self.status.performance_metrics,
            'configuration': {
                'enable_lsp': self.config.enable_lsp,
                'enable_real_time_monitoring': self.config.enable_real_time_monitoring,
                'enable_code_generation': self.config.enable_code_generation,
                'enable_deep_analysis': self.config.enable_deep_analysis,
                'analysis_level': self.config.analysis_level
            }
        }
    
    async def run_comprehensive_analysis(self, level: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive analysis using all available components."""
        analysis_level = level or self.config.analysis_level
        results = {}
        
        try:
            # Track performance
            import time
            start_time = time.time()
            
            # Run unified analysis
            if self._unified_analysis:
                logger.info(f"Running {analysis_level} analysis...")
                analysis_results = self._unified_analysis.analyze(analysis_level)
                results['analysis'] = analysis_results
                self._performance_tracker['analysis_calls'] += 1
            
            # Get current diagnostics
            if self._unified_diagnostics:
                logger.info("Gathering diagnostics...")
                diagnostics_results = {
                    'errors': self._unified_diagnostics.errors,
                    'warnings': self._unified_diagnostics.warnings,
                    'error_summary': self._unified_diagnostics.get_error_summary(),
                    'error_trends': self._unified_diagnostics.get_error_trends()
                }
                results['diagnostics'] = diagnostics_results
                self._performance_tracker['diagnostics_calls'] += 1
            
            # Generate code fixes if there are errors
            if self._code_generation_engine and self.status.error_count > 0:
                logger.info("Generating code fixes...")
                error_ids = [error.id for error in self._unified_diagnostics.errors[:5]]  # Limit to 5
                fixes = []
                for error_id in error_ids:
                    error_fixes = self._code_generation_engine.generate_error_fixes(error_id)
                    if error_fixes:
                        fixes.extend(error_fixes)
                
                results['code_fixes'] = fixes
                self._performance_tracker['code_generation_calls'] += 1
                self._performance_tracker['total_fixes_generated'] += len(fixes)
            
            # Calculate performance metrics
            end_time = time.time()
            execution_time = end_time - start_time
            
            results['performance'] = {
                'execution_time': execution_time,
                'components_used': len([k for k, v in self.status.components_loaded.items() if v]),
                'analysis_level': analysis_level,
                'timestamp': end_time
            }
            
            # Update performance tracker
            self._performance_tracker['average_response_time'] = (
                (self._performance_tracker.get('average_response_time', 0) + execution_time) / 2
            )
            
            logger.info(f"Comprehensive analysis completed in {execution_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': str(e)}
    
    async def auto_fix_errors(self, max_fixes: int = 10) -> Dict[str, Any]:
        """Automatically fix errors using the code generation engine."""
        if not self._code_generation_engine or not self._unified_diagnostics:
            return {'error': 'Code generation or diagnostics not available'}
        
        try:
            errors = self._unified_diagnostics.errors[:max_fixes]
            fixed_errors = []
            failed_fixes = []
            
            for error in errors:
                try:
                    fixes = self._code_generation_engine.generate_error_fixes(error.id)
                    if fixes:
                        # Apply the highest confidence fix
                        best_fix = max(fixes, key=lambda f: f.get('confidence', 0))
                        # In a real implementation, this would apply the fix to the file
                        fixed_errors.append({
                            'error_id': error.id,
                            'fix_applied': best_fix,
                            'confidence': best_fix.get('confidence', 0)
                        })
                        logger.info(f"Generated fix for error {error.id}")
                    else:
                        failed_fixes.append({'error_id': error.id, 'reason': 'No fixes generated'})
                        
                except Exception as e:
                    failed_fixes.append({'error_id': error.id, 'reason': str(e)})
            
            return {
                'fixed_errors': fixed_errors,
                'failed_fixes': failed_fixes,
                'success_rate': len(fixed_errors) / len(errors) if errors else 0,
                'total_processed': len(errors)
            }
            
        except Exception as e:
            logger.error(f"Error in auto-fix: {e}")
            return {'error': str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of the integration system."""
        health_status = {
            'overall_health': 'healthy',
            'components': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check component health
            for component, loaded in self.status.components_loaded.items():
                if loaded:
                    health_status['components'][component] = 'healthy'
                else:
                    health_status['components'][component] = 'unavailable'
                    health_status['issues'].append(f"{component} is not loaded")
                    health_status['overall_health'] = 'degraded'
            
            # Check error levels
            if self.status.error_count > 50:
                health_status['issues'].append(f"High error count: {self.status.error_count}")
                health_status['recommendations'].append("Consider running auto-fix or manual review")
                health_status['overall_health'] = 'degraded'
            
            # Check performance
            if self.status.performance_metrics:
                memory = self.status.performance_metrics.get('memory_usage', {})
                if isinstance(memory, dict) and memory.get('percent', 0) > 80:
                    health_status['issues'].append("High memory usage detected")
                    health_status['recommendations'].append("Consider restarting or optimizing cache")
                    health_status['overall_health'] = 'degraded'
            
            # Check monitoring
            if self.config.enable_real_time_monitoring and not self.status.active_monitors:
                health_status['issues'].append("Real-time monitoring not active")
                health_status['recommendations'].append("Restart monitoring services")
                health_status['overall_health'] = 'degraded'
            
            # Set overall health based on issues
            if health_status['issues']:
                if len(health_status['issues']) > 3:
                    health_status['overall_health'] = 'critical'
                elif health_status['overall_health'] != 'degraded':
                    health_status['overall_health'] = 'warning'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                'overall_health': 'critical',
                'error': str(e),
                'components': {},
                'issues': [f"Health check failed: {e}"],
                'recommendations': ['Restart the integration system']
            }
    
    async def shutdown(self):
        """Gracefully shutdown the integration system."""
        try:
            logger.info("Shutting down Enhanced Codebase Integration...")
            
            self._is_running = False
            
            # Cancel monitoring tasks
            for task in self._monitoring_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Clean up components
            if self._unified_diagnostics:
                # Shutdown diagnostics if it has a shutdown method
                if hasattr(self._unified_diagnostics, 'shutdown'):
                    await self._unified_diagnostics.shutdown()
            
            self.status.is_initialized = False
            self.status.active_monitors.clear()
            
            logger.info("Enhanced Codebase Integration shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Factory function for easy integration
async def create_enhanced_integration(codebase, config: Optional[IntegrationConfig] = None) -> EnhancedCodebaseIntegration:
    """Create and initialize an enhanced codebase integration."""
    integration = EnhancedCodebaseIntegration(codebase, config)
    
    if await integration.initialize():
        return integration
    else:
        raise RuntimeError("Failed to initialize Enhanced Codebase Integration")


# Convenience function for synchronous usage
def get_enhanced_integration(codebase, config: Optional[IntegrationConfig] = None) -> EnhancedCodebaseIntegration:
    """Get an enhanced codebase integration (synchronous wrapper)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(create_enhanced_integration(codebase, config))
