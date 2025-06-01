"""
Continuous Quality Monitoring System

Provides comprehensive continuous monitoring with session management,
health checks, and automated reporting capabilities.
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import uuid

from graph_sitter import Codebase
from .quality_monitor import QualityMonitor, QualityMetrics, MonitoringConfig
from .real_time_analyzer import RealTimeAnalyzer, AnalysisResult
from .alert_system import AlertSystem, AlertChannelConfig
from .dashboard_integration import DashboardMonitor

logger = logging.getLogger(__name__)


class MonitoringStatus(Enum):
    """Monitoring session status."""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class HealthStatus(Enum):
    """System health status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """System health check result."""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'component': self.component,
            'status': self.status.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }


@dataclass
class QualityReport:
    """Quality monitoring report."""
    id: str
    session_id: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    
    # Metrics summary
    initial_metrics: Optional[QualityMetrics]
    final_metrics: Optional[QualityMetrics]
    average_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Analysis results
    total_analyses: int = 0
    files_analyzed: int = 0
    issues_found: int = 0
    issues_resolved: int = 0
    
    # Alerts
    total_alerts: int = 0
    critical_alerts: int = 0
    alert_summary: Dict[str, int] = field(default_factory=dict)
    
    # Quality trends
    quality_improvements: List[str] = field(default_factory=list)
    quality_degradations: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': self.duration.total_seconds(),
            'initial_metrics': self.initial_metrics.to_dict() if self.initial_metrics else None,
            'final_metrics': self.final_metrics.to_dict() if self.final_metrics else None,
            'average_metrics': self.average_metrics,
            'total_analyses': self.total_analyses,
            'files_analyzed': self.files_analyzed,
            'issues_found': self.issues_found,
            'issues_resolved': self.issues_resolved,
            'total_alerts': self.total_alerts,
            'critical_alerts': self.critical_alerts,
            'alert_summary': self.alert_summary,
            'quality_improvements': self.quality_improvements,
            'quality_degradations': self.quality_degradations,
            'recommendations': self.recommendations
        }


@dataclass
class MonitoringSession:
    """Monitoring session information."""
    id: str
    name: str
    start_time: datetime
    status: MonitoringStatus
    codebase_path: str
    
    # Configuration
    monitoring_config: MonitoringConfig
    alert_config: AlertChannelConfig
    
    # Runtime state
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metrics_collected: int = 0
    alerts_generated: int = 0
    analyses_performed: int = 0
    
    # Components status
    quality_monitor_status: bool = False
    real_time_analyzer_status: bool = False
    alert_system_status: bool = False
    dashboard_status: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status.value,
            'codebase_path': self.codebase_path,
            'error_message': self.error_message,
            'metrics_collected': self.metrics_collected,
            'alerts_generated': self.alerts_generated,
            'analyses_performed': self.analyses_performed,
            'components_status': {
                'quality_monitor': self.quality_monitor_status,
                'real_time_analyzer': self.real_time_analyzer_status,
                'alert_system': self.alert_system_status,
                'dashboard': self.dashboard_status
            }
        }


class ContinuousMonitor:
    """Comprehensive continuous monitoring system."""
    
    def __init__(self, codebase: Codebase, 
                 monitoring_config: Optional[MonitoringConfig] = None,
                 alert_config: Optional[AlertChannelConfig] = None):
        self.codebase = codebase
        self.monitoring_config = monitoring_config or MonitoringConfig()
        self.alert_config = alert_config or AlertChannelConfig()
        
        # Core components
        self.quality_monitor: Optional[QualityMonitor] = None
        self.real_time_analyzer: Optional[RealTimeAnalyzer] = None
        self.alert_system: Optional[AlertSystem] = None
        self.dashboard_monitor: Optional[DashboardMonitor] = None
        
        # Session management
        self.current_session: Optional[MonitoringSession] = None
        self.session_history: List[MonitoringSession] = []
        
        # Health monitoring
        self.health_checks: List[HealthCheck] = []
        self.last_health_check: Optional[datetime] = None
        self.health_check_interval = 300  # 5 minutes
        
        # Reporting
        self.reports: List[QualityReport] = []
        self.report_generation_interval = 3600  # 1 hour
        
        # Tasks
        self.health_check_task: Optional[asyncio.Task] = None
        self.report_generation_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.session_callbacks: List[Callable[[MonitoringSession], None]] = []
        self.health_callbacks: List[Callable[[List[HealthCheck]], None]] = []
        self.report_callbacks: List[Callable[[QualityReport], None]] = []
        
        # Statistics
        self.total_uptime = timedelta()
        self.total_metrics_collected = 0
        self.total_alerts_generated = 0
        self.total_analyses_performed = 0
    
    async def start_monitoring(self, session_name: Optional[str] = None) -> str:
        """Start continuous monitoring session."""
        if self.current_session and self.current_session.status == MonitoringStatus.RUNNING:
            logger.warning("Monitoring session already running")
            return self.current_session.id
        
        # Create new session
        session_id = str(uuid.uuid4())
        session_name = session_name or f"Monitoring Session {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.current_session = MonitoringSession(
            id=session_id,
            name=session_name,
            start_time=datetime.now(),
            status=MonitoringStatus.STARTING,
            codebase_path=str(self.codebase.root_path),
            monitoring_config=self.monitoring_config,
            alert_config=self.alert_config
        )
        
        try:
            logger.info(f"Starting monitoring session: {session_name}")
            
            # Initialize components
            await self._initialize_components()
            
            # Start components
            await self._start_components()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Update session status
            self.current_session.status = MonitoringStatus.RUNNING
            
            # Notify callbacks
            for callback in self.session_callbacks:
                try:
                    callback(self.current_session)
                except Exception as e:
                    logger.error(f"Error in session callback: {e}")
            
            logger.info(f"Monitoring session started: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting monitoring session: {e}")
            self.current_session.status = MonitoringStatus.ERROR
            self.current_session.error_message = str(e)
            raise
    
    async def stop_monitoring(self) -> Optional[QualityReport]:
        """Stop current monitoring session."""
        if not self.current_session or self.current_session.status != MonitoringStatus.RUNNING:
            logger.warning("No active monitoring session to stop")
            return None
        
        try:
            logger.info(f"Stopping monitoring session: {self.current_session.id}")
            self.current_session.status = MonitoringStatus.STOPPING
            
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Stop components
            await self._stop_components()
            
            # Generate final report
            report = await self._generate_session_report()
            
            # Update session
            self.current_session.end_time = datetime.now()
            self.current_session.status = MonitoringStatus.STOPPED
            
            # Add to history
            self.session_history.append(self.current_session)
            
            # Update statistics
            if self.current_session.end_time:
                session_duration = self.current_session.end_time - self.current_session.start_time
                self.total_uptime += session_duration
            
            # Notify callbacks
            for callback in self.session_callbacks:
                try:
                    callback(self.current_session)
                except Exception as e:
                    logger.error(f"Error in session callback: {e}")
            
            logger.info(f"Monitoring session stopped: {self.current_session.id}")
            self.current_session = None
            
            return report
            
        except Exception as e:
            logger.error(f"Error stopping monitoring session: {e}")
            if self.current_session:
                self.current_session.status = MonitoringStatus.ERROR
                self.current_session.error_message = str(e)
            raise
    
    async def pause_monitoring(self):
        """Pause current monitoring session."""
        if not self.current_session or self.current_session.status != MonitoringStatus.RUNNING:
            logger.warning("No active monitoring session to pause")
            return
        
        logger.info("Pausing monitoring session")
        self.current_session.status = MonitoringStatus.PAUSED
        
        # Pause components (implementation depends on component capabilities)
        # For now, we'll just update the status
    
    async def resume_monitoring(self):
        """Resume paused monitoring session."""
        if not self.current_session or self.current_session.status != MonitoringStatus.PAUSED:
            logger.warning("No paused monitoring session to resume")
            return
        
        logger.info("Resuming monitoring session")
        self.current_session.status = MonitoringStatus.RUNNING
    
    async def _initialize_components(self):
        """Initialize monitoring components."""
        try:
            # Initialize quality monitor
            self.quality_monitor = QualityMonitor(self.codebase, self.monitoring_config)
            
            # Initialize real-time analyzer
            self.real_time_analyzer = RealTimeAnalyzer(self.codebase)
            
            # Initialize alert system
            self.alert_system = AlertSystem(self.alert_config)
            
            # Initialize dashboard monitor
            self.dashboard_monitor = DashboardMonitor(
                self.quality_monitor,
                self.real_time_analyzer,
                self.alert_system
            )
            
            # Setup callbacks
            self.quality_monitor.add_metric_callback(self._on_metrics_update)
            self.quality_monitor.add_alert_callback(self._on_alert_generated)
            self.real_time_analyzer.add_analysis_callback(self._on_analysis_result)
            
            logger.info("Monitoring components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    async def _start_components(self):
        """Start monitoring components."""
        try:
            # Start quality monitor
            if self.quality_monitor:
                await self.quality_monitor.start_monitoring()
                self.current_session.quality_monitor_status = True
            
            # Start real-time analyzer
            if self.real_time_analyzer:
                await self.real_time_analyzer.start_watching()
                self.current_session.real_time_analyzer_status = True
            
            # Alert system is always ready
            if self.alert_system:
                self.current_session.alert_system_status = True
            
            # Start dashboard monitor
            if self.dashboard_monitor:
                await self.dashboard_monitor.start()
                self.current_session.dashboard_status = True
            
            logger.info("Monitoring components started")
            
        except Exception as e:
            logger.error(f"Error starting components: {e}")
            raise
    
    async def _stop_components(self):
        """Stop monitoring components."""
        try:
            # Stop quality monitor
            if self.quality_monitor:
                await self.quality_monitor.stop_monitoring()
                self.current_session.quality_monitor_status = False
            
            # Stop real-time analyzer
            if self.real_time_analyzer:
                await self.real_time_analyzer.stop_watching()
                self.current_session.real_time_analyzer_status = False
            
            # Stop dashboard monitor
            if self.dashboard_monitor:
                await self.dashboard_monitor.stop()
                self.current_session.dashboard_status = False
            
            self.current_session.alert_system_status = False
            
            logger.info("Monitoring components stopped")
            
        except Exception as e:
            logger.error(f"Error stopping components: {e}")
            raise
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks."""
        try:
            # Start health check task
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            # Start report generation task
            self.report_generation_task = asyncio.create_task(self._report_generation_loop())
            
            logger.info("Background tasks started")
            
        except Exception as e:
            logger.error(f"Error starting background tasks: {e}")
            raise
    
    async def _stop_background_tasks(self):
        """Stop background monitoring tasks."""
        try:
            # Stop health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Stop report generation task
            if self.report_generation_task:
                self.report_generation_task.cancel()
                try:
                    await self.report_generation_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Background tasks stopped")
            
        except Exception as e:
            logger.error(f"Error stopping background tasks: {e}")
            raise
    
    async def _health_check_loop(self):
        """Background health check loop."""
        while self.current_session and self.current_session.status == MonitoringStatus.RUNNING:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _report_generation_loop(self):
        """Background report generation loop."""
        while self.current_session and self.current_session.status == MonitoringStatus.RUNNING:
            try:
                await asyncio.sleep(self.report_generation_interval)
                if self.current_session and self.current_session.status == MonitoringStatus.RUNNING:
                    report = await self._generate_periodic_report()
                    if report:
                        self.reports.append(report)
                        
                        # Notify callbacks
                        for callback in self.report_callbacks:
                            try:
                                callback(report)
                            except Exception as e:
                                logger.error(f"Error in report callback: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in report generation loop: {e}")
                await asyncio.sleep(300)  # Wait before retrying
    
    async def _perform_health_checks(self):
        """Perform system health checks."""
        try:
            health_checks = []
            
            # Check quality monitor
            if self.quality_monitor:
                if self.quality_monitor.is_running:
                    health_checks.append(HealthCheck(
                        component="quality_monitor",
                        status=HealthStatus.HEALTHY,
                        message="Quality monitor is running normally",
                        timestamp=datetime.now(),
                        details={
                            'metrics_collected': len(self.quality_monitor.metrics_history),
                            'active_alerts': len(self.quality_monitor.active_alerts)
                        }
                    ))
                else:
                    health_checks.append(HealthCheck(
                        component="quality_monitor",
                        status=HealthStatus.CRITICAL,
                        message="Quality monitor is not running",
                        timestamp=datetime.now()
                    ))
            
            # Check real-time analyzer
            if self.real_time_analyzer:
                if self.real_time_analyzer.is_watching:
                    health_checks.append(HealthCheck(
                        component="real_time_analyzer",
                        status=HealthStatus.HEALTHY,
                        message="Real-time analyzer is watching for changes",
                        timestamp=datetime.now(),
                        details={
                            'queue_size': self.real_time_analyzer.analysis_queue.qsize(),
                            'files_tracked': len(self.real_time_analyzer.file_hashes)
                        }
                    ))
                else:
                    health_checks.append(HealthCheck(
                        component="real_time_analyzer",
                        status=HealthStatus.WARNING,
                        message="Real-time analyzer is not watching",
                        timestamp=datetime.now()
                    ))
            
            # Check alert system
            if self.alert_system:
                delivery_stats = self.alert_system.get_delivery_stats()
                total_errors = sum(stats.get('error', 0) for stats in delivery_stats.values())
                
                if total_errors == 0:
                    health_checks.append(HealthCheck(
                        component="alert_system",
                        status=HealthStatus.HEALTHY,
                        message="Alert system is functioning normally",
                        timestamp=datetime.now(),
                        details={'delivery_stats': delivery_stats}
                    ))
                else:
                    health_checks.append(HealthCheck(
                        component="alert_system",
                        status=HealthStatus.WARNING,
                        message=f"Alert system has {total_errors} delivery errors",
                        timestamp=datetime.now(),
                        details={'delivery_stats': delivery_stats}
                    ))
            
            # Check dashboard monitor
            if self.dashboard_monitor:
                if self.dashboard_monitor.live_metrics.is_running:
                    health_checks.append(HealthCheck(
                        component="dashboard_monitor",
                        status=HealthStatus.HEALTHY,
                        message="Dashboard monitor is providing live metrics",
                        timestamp=datetime.now(),
                        details={
                            'subscribers': len(self.dashboard_monitor.live_metrics.subscribers),
                            'widgets': len(self.dashboard_monitor.widgets),
                            'charts': len(self.dashboard_monitor.charts)
                        }
                    ))
                else:
                    health_checks.append(HealthCheck(
                        component="dashboard_monitor",
                        status=HealthStatus.WARNING,
                        message="Dashboard monitor is not providing live metrics",
                        timestamp=datetime.now()
                    ))
            
            # Store health checks
            self.health_checks.extend(health_checks)
            
            # Keep only recent health checks (last 24 hours)
            cutoff = datetime.now() - timedelta(hours=24)
            self.health_checks = [hc for hc in self.health_checks if hc.timestamp > cutoff]
            
            self.last_health_check = datetime.now()
            
            # Notify callbacks
            for callback in self.health_callbacks:
                try:
                    callback(health_checks)
                except Exception as e:
                    logger.error(f"Error in health callback: {e}")
            
            logger.debug(f"Health checks completed: {len(health_checks)} components checked")
            
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")
    
    def _on_metrics_update(self, metrics: QualityMetrics):
        """Handle metrics update."""
        if self.current_session:
            self.current_session.metrics_collected += 1
            self.total_metrics_collected += 1
    
    def _on_alert_generated(self, alert):
        """Handle alert generation."""
        if self.current_session:
            self.current_session.alerts_generated += 1
            self.total_alerts_generated += 1
    
    def _on_analysis_result(self, result: AnalysisResult):
        """Handle analysis result."""
        if self.current_session:
            self.current_session.analyses_performed += 1
            self.total_analyses_performed += 1
    
    async def _generate_session_report(self) -> QualityReport:
        """Generate report for current session."""
        if not self.current_session:
            raise ValueError("No active session")
        
        try:
            report_id = str(uuid.uuid4())
            end_time = datetime.now()
            duration = end_time - self.current_session.start_time
            
            # Get initial and final metrics
            initial_metrics = None
            final_metrics = None
            
            if self.quality_monitor and self.quality_monitor.metrics_history:
                # Find metrics closest to session start
                session_start = self.current_session.start_time
                for metrics in self.quality_monitor.metrics_history:
                    if metrics.timestamp >= session_start:
                        initial_metrics = metrics
                        break
                
                # Final metrics is the latest
                final_metrics = self.quality_monitor.metrics_history[-1]
            
            # Calculate average metrics
            average_metrics = {}
            if self.quality_monitor and self.quality_monitor.metrics_history:
                session_metrics = [
                    m for m in self.quality_monitor.metrics_history
                    if m.timestamp >= self.current_session.start_time
                ]
                
                if session_metrics:
                    average_metrics = {
                        'health_score': sum(m.health_score for m in session_metrics) / len(session_metrics),
                        'technical_debt_score': sum(m.technical_debt_score for m in session_metrics) / len(session_metrics),
                        'complexity_score': sum(m.complexity_score for m in session_metrics) / len(session_metrics),
                        'maintainability_score': sum(m.maintainability_score for m in session_metrics) / len(session_metrics),
                        'documentation_coverage': sum(m.documentation_coverage for m in session_metrics) / len(session_metrics),
                        'test_coverage': sum(m.test_coverage for m in session_metrics) / len(session_metrics)
                    }
            
            # Generate recommendations
            recommendations = self._generate_recommendations(initial_metrics, final_metrics)
            
            report = QualityReport(
                id=report_id,
                session_id=self.current_session.id,
                start_time=self.current_session.start_time,
                end_time=end_time,
                duration=duration,
                initial_metrics=initial_metrics,
                final_metrics=final_metrics,
                average_metrics=average_metrics,
                total_analyses=self.current_session.analyses_performed,
                total_alerts=self.current_session.alerts_generated,
                recommendations=recommendations
            )
            
            logger.info(f"Session report generated: {report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating session report: {e}")
            raise
    
    async def _generate_periodic_report(self) -> Optional[QualityReport]:
        """Generate periodic report during session."""
        # This would generate interim reports during long-running sessions
        # Implementation similar to _generate_session_report but for a time window
        return None
    
    def _generate_recommendations(self, initial_metrics: Optional[QualityMetrics], 
                                final_metrics: Optional[QualityMetrics]) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        if not initial_metrics or not final_metrics:
            recommendations.append("Insufficient data for trend analysis")
            return recommendations
        
        # Health score recommendations
        if final_metrics.health_score < 0.6:
            recommendations.append("Overall code health is below acceptable levels - consider comprehensive refactoring")
        elif final_metrics.health_score < initial_metrics.health_score:
            recommendations.append("Code health has declined - review recent changes")
        
        # Technical debt recommendations
        if final_metrics.technical_debt_score > 0.7:
            recommendations.append("High technical debt detected - prioritize debt reduction activities")
        
        # Complexity recommendations
        if final_metrics.complexity_score > 0.8:
            recommendations.append("Code complexity is high - focus on simplifying complex functions")
        
        # Documentation recommendations
        if final_metrics.documentation_coverage < 0.5:
            recommendations.append("Documentation coverage is low - add docstrings and comments")
        
        # Test coverage recommendations
        if final_metrics.test_coverage < 0.7:
            recommendations.append("Test coverage is below recommended levels - add more tests")
        
        return recommendations
    
    def get_current_session(self) -> Optional[MonitoringSession]:
        """Get current monitoring session."""
        return self.current_session
    
    def get_session_history(self) -> List[MonitoringSession]:
        """Get monitoring session history."""
        return self.session_history.copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current system health status."""
        if not self.health_checks:
            return {'status': 'unknown', 'message': 'No health checks performed'}
        
        # Get latest health checks for each component
        latest_checks = {}
        for check in reversed(self.health_checks):
            if check.component not in latest_checks:
                latest_checks[check.component] = check
        
        # Determine overall status
        statuses = [check.status for check in latest_checks.values()]
        
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
        elif HealthStatus.HEALTHY in statuses:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        return {
            'overall_status': overall_status.value,
            'last_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'components': {comp: check.to_dict() for comp, check in latest_checks.items()},
            'total_checks': len(self.health_checks)
        }
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get monitoring system statistics."""
        return {
            'total_uptime_seconds': self.total_uptime.total_seconds(),
            'total_sessions': len(self.session_history) + (1 if self.current_session else 0),
            'total_metrics_collected': self.total_metrics_collected,
            'total_alerts_generated': self.total_alerts_generated,
            'total_analyses_performed': self.total_analyses_performed,
            'current_session_active': self.current_session is not None,
            'reports_generated': len(self.reports)
        }
    
    def add_session_callback(self, callback: Callable[[MonitoringSession], None]):
        """Add session event callback."""
        self.session_callbacks.append(callback)
    
    def add_health_callback(self, callback: Callable[[List[HealthCheck]], None]):
        """Add health check callback."""
        self.health_callbacks.append(callback)
    
    def add_report_callback(self, callback: Callable[[QualityReport], None]):
        """Add report generation callback."""
        self.report_callbacks.append(callback)

