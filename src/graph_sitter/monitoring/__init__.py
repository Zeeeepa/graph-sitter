"""
Real-time Code Quality Monitoring System

This module provides real-time monitoring capabilities for code quality,
including live metrics tracking, alert systems, and continuous quality assessment.
"""

from .quality_monitor import (
    QualityMonitor,
    QualityAlert,
    QualityThreshold,
    MonitoringConfig,
    QualityMetrics,
    QualityTrend
)

from .real_time_analyzer import (
    RealTimeAnalyzer,
    FileChangeEvent,
    AnalysisResult,
    QualityDelta
)

from .alert_system import (
    AlertSystem,
    AlertRule,
    AlertChannel,
    AlertSeverity,
    AlertManager
)

from .dashboard_integration import (
    DashboardMonitor,
    LiveMetricsProvider,
    QualityWidget,
    TrendChart
)

from .continuous_monitoring import (
    ContinuousMonitor,
    MonitoringSession,
    QualityReport,
    HealthCheck
)

__all__ = [
    # Core Monitoring
    'QualityMonitor',
    'QualityAlert',
    'QualityThreshold',
    'MonitoringConfig',
    'QualityMetrics',
    'QualityTrend',
    
    # Real-time Analysis
    'RealTimeAnalyzer',
    'FileChangeEvent',
    'AnalysisResult',
    'QualityDelta',
    
    # Alert System
    'AlertSystem',
    'AlertRule',
    'AlertChannel',
    'AlertSeverity',
    'AlertManager',
    
    # Dashboard Integration
    'DashboardMonitor',
    'LiveMetricsProvider',
    'QualityWidget',
    'TrendChart',
    
    # Continuous Monitoring
    'ContinuousMonitor',
    'MonitoringSession',
    'QualityReport',
    'HealthCheck'
]

# Version info
__version__ = "1.0.0"

