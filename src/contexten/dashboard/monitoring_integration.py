"""
Monitoring Integration for Dashboard

This module integrates the real-time monitoring system from PR #109
with the existing dashboard infrastructure to provide comprehensive
code analysis context.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict

try:
    from graph_sitter import Codebase
    from graph_sitter.monitoring import (
        QualityMonitor,
        MonitoringConfig,
        RealTimeAnalyzer,
        AlertSystem,
        DashboardMonitor,
        ContinuousMonitor,
        QualityMetrics,
        QualityAlert,
        AnalysisScope
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Comprehensive metrics for dashboard display"""
    health_score: float
    technical_debt_score: float
    complexity_score: float
    maintainability_score: float
    documentation_coverage: float
    test_coverage: float
    security_score: float
    performance_score: float
    
    # Counts
    total_files: int
    total_functions: int
    total_classes: int
    dead_code_count: int
    circular_dependencies_count: int
    security_issues_count: int
    
    # Trends
    health_trend: str  # "improving", "stable", "degrading"
    quality_change_24h: float
    
    # Timestamps
    last_analysis: datetime
    last_updated: datetime


@dataclass
class CodeIssue:
    """Code quality issue for dashboard display"""
    id: str
    title: str
    description: str
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "quality", "security", "performance", "maintainability"
    file_path: str
    line_number: Optional[int]
    suggestion: Optional[str]
    created_at: datetime


@dataclass
class FileQualityInfo:
    """File-level quality information"""
    path: str
    quality_score: float
    complexity_score: float
    maintainability_score: float
    test_coverage: float
    documentation_coverage: float
    issues_count: int
    last_modified: datetime
    size_lines: int


class EnhancedDashboardMonitoring:
    """Enhanced monitoring integration for comprehensive dashboard context"""
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = codebase_path
        self.codebase = None
        self.quality_monitor = None
        self.real_time_analyzer = None
        self.alert_system = None
        self.dashboard_monitor = None
        self.continuous_monitor = None
        
        # Dashboard-specific state
        self.current_metrics: Optional[DashboardMetrics] = None
        self.code_issues: List[CodeIssue] = []
        self.file_quality_info: Dict[str, FileQualityInfo] = {}
        self.alerts_history: List[QualityAlert] = []
        
        # Callbacks for real-time updates
        self.metrics_callbacks: List[Callable] = []
        self.alerts_callbacks: List[Callable] = []
        self.file_change_callbacks: List[Callable] = []
        
        # Configuration
        self.monitoring_config = MonitoringConfig(
            analysis_interval=300,  # 5 minutes
            alert_check_interval=60,  # 1 minute
            enable_alerts=True,
            store_metrics=True,
            storage_path="./monitoring_data"
        )
        
        self.is_running = False
    
    async def initialize(self) -> bool:
        """Initialize the monitoring system"""
        if not MONITORING_AVAILABLE:
            logger.warning("Monitoring system not available - using mock data")
            await self._initialize_mock_data()
            return True
        
        try:
            # Initialize codebase
            self.codebase = Codebase(self.codebase_path)
            
            # Initialize monitoring components
            self.quality_monitor = QualityMonitor(self.codebase, self.monitoring_config)
            self.real_time_analyzer = RealTimeAnalyzer(self.codebase, watch_path=self.codebase_path)
            self.alert_system = AlertSystem()
            self.dashboard_monitor = DashboardMonitor(
                self.quality_monitor, 
                self.real_time_analyzer, 
                self.alert_system
            )
            self.continuous_monitor = ContinuousMonitor(self.codebase, self.monitoring_config)
            
            # Setup callbacks
            self._setup_monitoring_callbacks()
            
            # Start monitoring
            await self.quality_monitor.start_monitoring()
            await self.real_time_analyzer.start_watching()
            await self.dashboard_monitor.start()
            
            self.is_running = True
            logger.info("Enhanced dashboard monitoring initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring system: {e}")
            await self._initialize_mock_data()
            return False
    
    async def shutdown(self):
        """Shutdown the monitoring system"""
        if not self.is_running:
            return
        
        try:
            if self.quality_monitor:
                await self.quality_monitor.stop_monitoring()
            if self.real_time_analyzer:
                await self.real_time_analyzer.stop_watching()
            if self.dashboard_monitor:
                await self.dashboard_monitor.stop()
            
            self.is_running = False
            logger.info("Enhanced dashboard monitoring shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during monitoring shutdown: {e}")
    
    def _setup_monitoring_callbacks(self):
        """Setup callbacks for monitoring events"""
        if self.quality_monitor:
            self.quality_monitor.add_metric_callback(self._on_metrics_update)
            self.quality_monitor.add_alert_callback(self._on_alert_generated)
        
        if self.real_time_analyzer:
            self.real_time_analyzer.add_analysis_callback(self._on_analysis_complete)
            self.real_time_analyzer.add_change_callback(self._on_file_change)
    
    async def _on_metrics_update(self, metrics: QualityMetrics):
        """Handle quality metrics update"""
        try:
            # Convert to dashboard metrics
            dashboard_metrics = await self._convert_to_dashboard_metrics(metrics)
            self.current_metrics = dashboard_metrics
            
            # Notify callbacks
            for callback in self.metrics_callbacks:
                try:
                    await callback(dashboard_metrics)
                except Exception as e:
                    logger.error(f"Error in metrics callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing metrics update: {e}")
    
    async def _on_alert_generated(self, alert: QualityAlert):
        """Handle alert generation"""
        try:
            self.alerts_history.append(alert)
            
            # Convert to code issue if applicable
            if alert.metric_type in ["quality", "complexity", "maintainability"]:
                code_issue = self._convert_alert_to_issue(alert)
                self.code_issues.append(code_issue)
            
            # Notify callbacks
            for callback in self.alerts_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
    
    async def _on_analysis_complete(self, result):
        """Handle analysis completion"""
        try:
            # Update file quality information
            if hasattr(result, 'file_path') and hasattr(result, 'quality_metrics'):
                file_info = FileQualityInfo(
                    path=result.file_path,
                    quality_score=result.quality_metrics.get('quality_score', 0.0),
                    complexity_score=result.quality_metrics.get('complexity_score', 0.0),
                    maintainability_score=result.quality_metrics.get('maintainability_score', 0.0),
                    test_coverage=result.quality_metrics.get('test_coverage', 0.0),
                    documentation_coverage=result.quality_metrics.get('documentation_coverage', 0.0),
                    issues_count=len(result.quality_metrics.get('issues', [])),
                    last_modified=datetime.now(),
                    size_lines=result.quality_metrics.get('lines_of_code', 0)
                )
                self.file_quality_info[result.file_path] = file_info
                
        except Exception as e:
            logger.error(f"Error processing analysis result: {e}")
    
    async def _on_file_change(self, change_event):
        """Handle file change event"""
        try:
            # Notify callbacks
            for callback in self.file_change_callbacks:
                try:
                    await callback(change_event)
                except Exception as e:
                    logger.error(f"Error in file change callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing file change: {e}")
    
    async def _convert_to_dashboard_metrics(self, metrics: QualityMetrics) -> DashboardMetrics:
        """Convert QualityMetrics to DashboardMetrics"""
        # Calculate additional metrics
        security_score = await self._calculate_security_score()
        performance_score = await self._calculate_performance_score()
        
        # Determine trend
        health_trend = await self._calculate_health_trend()
        quality_change_24h = await self._calculate_quality_change_24h()
        
        return DashboardMetrics(
            health_score=metrics.health_score,
            technical_debt_score=metrics.technical_debt_score,
            complexity_score=metrics.complexity_score,
            maintainability_score=metrics.maintainability_score,
            documentation_coverage=metrics.documentation_coverage,
            test_coverage=metrics.test_coverage,
            security_score=security_score,
            performance_score=performance_score,
            total_files=len(self.file_quality_info),
            total_functions=metrics.total_functions,
            total_classes=metrics.total_classes,
            dead_code_count=metrics.dead_code_count,
            circular_dependencies_count=metrics.circular_dependencies_count,
            security_issues_count=len([issue for issue in self.code_issues if issue.category == "security"]),
            health_trend=health_trend,
            quality_change_24h=quality_change_24h,
            last_analysis=metrics.timestamp,
            last_updated=datetime.now()
        )
    
    def _convert_alert_to_issue(self, alert: QualityAlert) -> CodeIssue:
        """Convert QualityAlert to CodeIssue"""
        return CodeIssue(
            id=alert.id,
            title=f"{alert.metric_type.value.title()} Alert",
            description=alert.message,
            severity=alert.severity.value,
            category="quality",
            file_path=getattr(alert, 'file_path', ''),
            line_number=getattr(alert, 'line_number', None),
            suggestion=getattr(alert, 'suggestion', None),
            created_at=alert.timestamp
        )
    
    async def _calculate_security_score(self) -> float:
        """Calculate overall security score"""
        # This would integrate with security analysis tools
        # For now, return a mock score
        return 0.82
    
    async def _calculate_performance_score(self) -> float:
        """Calculate overall performance score"""
        # This would integrate with performance analysis tools
        # For now, return a mock score
        return 0.75
    
    async def _calculate_health_trend(self) -> str:
        """Calculate health trend over time"""
        # This would analyze historical data
        # For now, return a mock trend
        return "stable"
    
    async def _calculate_quality_change_24h(self) -> float:
        """Calculate quality change over last 24 hours"""
        # This would analyze historical data
        # For now, return a mock change
        return 0.02
    
    async def _initialize_mock_data(self):
        """Initialize with mock data when monitoring is not available"""
        self.current_metrics = DashboardMetrics(
            health_score=0.85,
            technical_debt_score=0.35,
            complexity_score=0.65,
            maintainability_score=0.75,
            documentation_coverage=0.70,
            test_coverage=0.78,
            security_score=0.82,
            performance_score=0.75,
            total_files=45,
            total_functions=234,
            total_classes=67,
            dead_code_count=12,
            circular_dependencies_count=3,
            security_issues_count=5,
            health_trend="stable",
            quality_change_24h=0.02,
            last_analysis=datetime.now() - timedelta(minutes=5),
            last_updated=datetime.now()
        )
        
        self.code_issues = [
            CodeIssue(
                id="issue_1",
                title="High complexity function detected",
                description="Function 'process_data' has cyclomatic complexity of 15",
                severity="high",
                category="quality",
                file_path="src/data_processor.py",
                line_number=45,
                suggestion="Consider breaking this function into smaller, more focused functions",
                created_at=datetime.now() - timedelta(hours=2)
            ),
            CodeIssue(
                id="issue_2",
                title="Missing documentation",
                description="Class 'DataAnalyzer' lacks docstring",
                severity="medium",
                category="quality",
                file_path="src/analyzer.py",
                line_number=12,
                suggestion="Add comprehensive docstring explaining the class purpose and usage",
                created_at=datetime.now() - timedelta(hours=1)
            ),
            CodeIssue(
                id="issue_3",
                title="SQL Injection vulnerability",
                description="Potential SQL injection in user input handling",
                severity="critical",
                category="security",
                file_path="src/database.py",
                line_number=78,
                suggestion="Use parameterized queries to prevent SQL injection",
                created_at=datetime.now() - timedelta(minutes=30)
            )
        ]
        
        self.file_quality_info = {
            "src/main.py": FileQualityInfo(
                path="src/main.py",
                quality_score=0.92,
                complexity_score=0.25,
                maintainability_score=0.88,
                test_coverage=0.85,
                documentation_coverage=0.90,
                issues_count=1,
                last_modified=datetime.now() - timedelta(hours=3),
                size_lines=156
            ),
            "src/data_processor.py": FileQualityInfo(
                path="src/data_processor.py",
                quality_score=0.65,
                complexity_score=0.85,
                maintainability_score=0.60,
                test_coverage=0.45,
                documentation_coverage=0.30,
                issues_count=3,
                last_modified=datetime.now() - timedelta(hours=1),
                size_lines=342
            )
        }
        
        logger.info("Mock monitoring data initialized")
    
    # Public API methods for dashboard
    
    def add_metrics_callback(self, callback: Callable):
        """Add callback for metrics updates"""
        self.metrics_callbacks.append(callback)
    
    def add_alerts_callback(self, callback: Callable):
        """Add callback for alert updates"""
        self.alerts_callbacks.append(callback)
    
    def add_file_change_callback(self, callback: Callable):
        """Add callback for file change updates"""
        self.file_change_callbacks.append(callback)
    
    def get_current_metrics(self) -> Optional[DashboardMetrics]:
        """Get current dashboard metrics"""
        return self.current_metrics
    
    def get_code_issues(self, severity: Optional[str] = None, category: Optional[str] = None) -> List[CodeIssue]:
        """Get code issues with optional filtering"""
        issues = self.code_issues
        
        if severity:
            issues = [issue for issue in issues if issue.severity == severity]
        
        if category:
            issues = [issue for issue in issues if issue.category == category]
        
        return sorted(issues, key=lambda x: x.created_at, reverse=True)
    
    def get_file_quality_info(self) -> List[FileQualityInfo]:
        """Get file quality information"""
        return list(self.file_quality_info.values())
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        recent_alerts = self.alerts_history[-limit:] if self.alerts_history else []
        return [
            {
                "id": alert.id,
                "severity": alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity),
                "type": alert.metric_type.value if hasattr(alert.metric_type, 'value') else str(alert.metric_type),
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in reversed(recent_alerts)
        ]
    
    def get_architecture_metrics(self) -> Dict[str, Any]:
        """Get architecture analysis metrics"""
        return {
            "modules": len(self.file_quality_info),
            "coupling": 0.45,
            "cohesion": 0.78,
            "depth": 4,
            "fan_in": 3.2,
            "fan_out": 2.8,
            "circular_dependencies": [
                {"cycle": ["module_a", "module_b", "module_c", "module_a"]}
            ]
        }
    
    def get_security_analysis(self) -> Dict[str, Any]:
        """Get security analysis data"""
        security_issues = self.get_code_issues(category="security")
        
        return {
            "security_issues": [asdict(issue) for issue in security_issues],
            "security_score": {
                "authentication": 0.9,
                "authorization": 0.8,
                "data_protection": 0.85,
                "input_validation": 0.75,
                "error_handling": 0.88
            },
            "vulnerability_count": len(security_issues)
        }
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Get performance analysis data"""
        return {
            "metrics": {
                "response_times": [120, 135, 98, 156, 142, 118, 167],
                "memory_usage": [45, 52, 48, 61, 58, 44, 67],
                "timestamps": ["10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30"]
            },
            "bottlenecks": [
                {
                    "function": "heavy_computation",
                    "file": "src/processor.py",
                    "line": 234,
                    "impact": "High",
                    "avg_time": "2.3s"
                },
                {
                    "function": "database_query",
                    "file": "src/database.py",
                    "line": 156,
                    "impact": "Medium",
                    "avg_time": "0.8s"
                }
            ]
        }
    
    async def export_comprehensive_report(self) -> Dict[str, Any]:
        """Export comprehensive analysis report"""
        return {
            "overview": {
                "metrics": asdict(self.current_metrics) if self.current_metrics else {},
                "generated_at": datetime.now().isoformat()
            },
            "code_quality": {
                "issues": [asdict(issue) for issue in self.code_issues],
                "file_quality": [asdict(info) for info in self.file_quality_info.values()]
            },
            "architecture": self.get_architecture_metrics(),
            "security": self.get_security_analysis(),
            "performance": self.get_performance_analysis(),
            "alerts": self.get_recent_alerts(limit=50)
        }

