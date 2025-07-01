"""
Core Quality Monitoring System

Provides real-time code quality monitoring with configurable thresholds,
alerts, and trend tracking capabilities.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
import json

from graph_sitter import Codebase
from graph_sitter.analysis import EnhancedCodebaseAnalyzer

logger = logging.getLogger(__name__)


class QualitySeverity(Enum):
    """Quality issue severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of quality metrics."""
    HEALTH_SCORE = "health_score"
    TECHNICAL_DEBT = "technical_debt"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    TEST_COVERAGE = "test_coverage"
    DEAD_CODE = "dead_code"
    CIRCULAR_DEPS = "circular_dependencies"


@dataclass
class QualityThreshold:
    """Quality threshold configuration."""
    metric_type: MetricType
    warning_threshold: float
    critical_threshold: float
    direction: str = "lower"  # "lower" means values below threshold are bad
    enabled: bool = True
    
    def evaluate(self, value: float) -> Optional[QualitySeverity]:
        """Evaluate if value violates threshold."""
        if not self.enabled:
            return None
        
        if self.direction == "lower":
            if value < self.critical_threshold:
                return QualitySeverity.CRITICAL
            elif value < self.warning_threshold:
                return QualitySeverity.HIGH
        else:  # "higher" means values above threshold are bad
            if value > self.critical_threshold:
                return QualitySeverity.CRITICAL
            elif value > self.warning_threshold:
                return QualitySeverity.HIGH
        
        return None


@dataclass
class QualityMetrics:
    """Current quality metrics snapshot."""
    timestamp: datetime
    health_score: float
    technical_debt_score: float
    complexity_score: float
    maintainability_score: float
    documentation_coverage: float
    test_coverage: float
    dead_code_count: int
    circular_dependencies_count: int
    
    # Additional metrics
    total_functions: int = 0
    total_classes: int = 0
    total_lines: int = 0
    high_complexity_functions: int = 0
    low_cohesion_classes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'health_score': self.health_score,
            'technical_debt_score': self.technical_debt_score,
            'complexity_score': self.complexity_score,
            'maintainability_score': self.maintainability_score,
            'documentation_coverage': self.documentation_coverage,
            'test_coverage': self.test_coverage,
            'dead_code_count': self.dead_code_count,
            'circular_dependencies_count': self.circular_dependencies_count,
            'total_functions': self.total_functions,
            'total_classes': self.total_classes,
            'total_lines': self.total_lines,
            'high_complexity_functions': self.high_complexity_functions,
            'low_cohesion_classes': self.low_cohesion_classes
        }


@dataclass
class QualityTrend:
    """Quality trend analysis."""
    metric_type: MetricType
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # "improving", "degrading", "stable"
    time_period: timedelta
    
    @property
    def is_improving(self) -> bool:
        """Check if trend is improving."""
        return self.trend_direction == "improving"
    
    @property
    def is_degrading(self) -> bool:
        """Check if trend is degrading."""
        return self.trend_direction == "degrading"


@dataclass
class QualityAlert:
    """Quality alert notification."""
    id: str
    timestamp: datetime
    severity: QualitySeverity
    metric_type: MetricType
    message: str
    current_value: float
    threshold_value: float
    suggested_actions: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'metric_type': self.metric_type.value,
            'message': self.message,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'suggested_actions': self.suggested_actions,
            'affected_files': self.affected_files
        }


@dataclass
class MonitoringConfig:
    """Monitoring system configuration."""
    
    # Monitoring intervals
    analysis_interval: int = 300  # 5 minutes
    alert_check_interval: int = 60  # 1 minute
    trend_analysis_period: int = 3600  # 1 hour
    
    # Quality thresholds
    thresholds: List[QualityThreshold] = field(default_factory=lambda: [
        QualityThreshold(MetricType.HEALTH_SCORE, 0.7, 0.5, "lower"),
        QualityThreshold(MetricType.TECHNICAL_DEBT, 0.7, 0.9, "higher"),
        QualityThreshold(MetricType.COMPLEXITY, 0.7, 0.9, "higher"),
        QualityThreshold(MetricType.MAINTAINABILITY, 0.6, 0.4, "lower"),
        QualityThreshold(MetricType.DOCUMENTATION, 0.6, 0.3, "lower"),
        QualityThreshold(MetricType.TEST_COVERAGE, 0.7, 0.5, "lower"),
    ])
    
    # Alert settings
    enable_alerts: bool = True
    alert_cooldown: int = 1800  # 30 minutes
    max_alerts_per_hour: int = 10
    
    # Storage settings
    store_metrics: bool = True
    metrics_retention_days: int = 30
    storage_path: Optional[str] = None
    
    # Notification settings
    notification_channels: List[str] = field(default_factory=list)
    webhook_urls: List[str] = field(default_factory=list)
    
    def get_threshold(self, metric_type: MetricType) -> Optional[QualityThreshold]:
        """Get threshold for metric type."""
        for threshold in self.thresholds:
            if threshold.metric_type == metric_type:
                return threshold
        return None


class QualityMonitor:
    """Real-time code quality monitoring system."""
    
    def __init__(self, codebase: Codebase, config: Optional[MonitoringConfig] = None):
        self.codebase = codebase
        self.config = config or MonitoringConfig()
        self.analyzer = EnhancedCodebaseAnalyzer(codebase, "quality-monitor")
        
        # State
        self.is_running = False
        self.current_metrics: Optional[QualityMetrics] = None
        self.metrics_history: List[QualityMetrics] = []
        self.active_alerts: Dict[str, QualityAlert] = {}
        self.alert_history: List[QualityAlert] = []
        
        # Callbacks
        self.metric_callbacks: List[Callable[[QualityMetrics], None]] = []
        self.alert_callbacks: List[Callable[[QualityAlert], None]] = []
        self.trend_callbacks: List[Callable[[List[QualityTrend]], None]] = []
        
        # Tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None
        
        # Alert rate limiting
        self._alert_timestamps: List[datetime] = []
        self._last_alert_times: Dict[str, datetime] = {}
    
    async def start_monitoring(self):
        """Start the monitoring system."""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return
        
        logger.info("Starting quality monitoring system")
        self.is_running = True
        
        # Start monitoring tasks
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._alert_task = asyncio.create_task(self._alert_loop())
        
        # Initial analysis
        await self._perform_analysis()
    
    async def stop_monitoring(self):
        """Stop the monitoring system."""
        if not self.is_running:
            return
        
        logger.info("Stopping quality monitoring system")
        self.is_running = False
        
        # Cancel tasks
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._alert_task:
            self._alert_task.cancel()
        
        # Wait for tasks to complete
        try:
            if self._monitoring_task:
                await self._monitoring_task
        except asyncio.CancelledError:
            pass
        
        try:
            if self._alert_task:
                await self._alert_task
        except asyncio.CancelledError:
            pass
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                await self._perform_analysis()
                await asyncio.sleep(self.config.analysis_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _alert_loop(self):
        """Alert checking loop."""
        while self.is_running:
            try:
                await self._check_alerts()
                await asyncio.sleep(self.config.alert_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _perform_analysis(self):
        """Perform quality analysis."""
        try:
            logger.debug("Performing quality analysis")
            
            # Run comprehensive analysis
            report = self.analyzer.run_full_analysis()
            
            # Extract metrics
            metrics = self._extract_metrics(report)
            
            # Update current metrics
            self.current_metrics = metrics
            self.metrics_history.append(metrics)
            
            # Trim history if needed
            if len(self.metrics_history) > 1000:  # Keep last 1000 entries
                self.metrics_history = self.metrics_history[-1000:]
            
            # Store metrics if configured
            if self.config.store_metrics:
                await self._store_metrics(metrics)
            
            # Notify callbacks
            for callback in self.metric_callbacks:
                try:
                    callback(metrics)
                except Exception as e:
                    logger.error(f"Error in metric callback: {e}")
            
            logger.debug(f"Analysis complete - Health Score: {metrics.health_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error performing analysis: {e}")
    
    def _extract_metrics(self, report) -> QualityMetrics:
        """Extract metrics from analysis report."""
        try:
            # Get health data
            health_data = report.get('health_score_data', {})
            component_scores = health_data.get('component_scores', {})
            
            # Get issue counts
            issues = report.get('issues', [])
            dead_code_issues = [i for i in issues if 'dead code' in i.get('description', '').lower()]
            circular_dep_issues = [i for i in issues if 'circular' in i.get('description', '').lower()]
            
            # Get function/class counts
            function_analysis = report.get('function_analysis', [])
            class_analysis = report.get('class_analysis', [])
            
            high_complexity_funcs = [f for f in function_analysis 
                                   if f.get('cyclomatic_complexity', 0) > 10]
            low_cohesion_classes = [c for c in class_analysis 
                                  if c.get('cohesion_score', 1.0) < 0.3]
            
            return QualityMetrics(
                timestamp=datetime.now(),
                health_score=health_data.get('overall_health_score', 0.0),
                technical_debt_score=component_scores.get('technical_debt', 0.0),
                complexity_score=component_scores.get('complexity', 0.0),
                maintainability_score=component_scores.get('maintainability', 0.0),
                documentation_coverage=component_scores.get('documentation', 0.0),
                test_coverage=component_scores.get('test_coverage', 0.0),
                dead_code_count=len(dead_code_issues),
                circular_dependencies_count=len(circular_dep_issues),
                total_functions=len(function_analysis),
                total_classes=len(class_analysis),
                total_lines=sum(f.get('lines_of_code', 0) for f in function_analysis),
                high_complexity_functions=len(high_complexity_funcs),
                low_cohesion_classes=len(low_cohesion_classes)
            )
            
        except Exception as e:
            logger.error(f"Error extracting metrics: {e}")
            # Return default metrics
            return QualityMetrics(
                timestamp=datetime.now(),
                health_score=0.0, technical_debt_score=1.0, complexity_score=1.0,
                maintainability_score=0.0, documentation_coverage=0.0, test_coverage=0.0,
                dead_code_count=0, circular_dependencies_count=0
            )
    
    async def _check_alerts(self):
        """Check for quality threshold violations."""
        if not self.config.enable_alerts or not self.current_metrics:
            return
        
        try:
            # Check rate limiting
            if not self._can_send_alert():
                return
            
            # Check each threshold
            for threshold in self.config.thresholds:
                if not threshold.enabled:
                    continue
                
                # Get current value
                current_value = self._get_metric_value(threshold.metric_type)
                if current_value is None:
                    continue
                
                # Evaluate threshold
                severity = threshold.evaluate(current_value)
                if severity is None:
                    # Clear any existing alert for this metric
                    alert_key = f"{threshold.metric_type.value}"
                    if alert_key in self.active_alerts:
                        del self.active_alerts[alert_key]
                    continue
                
                # Check if we should create/update alert
                alert_key = f"{threshold.metric_type.value}"
                
                # Check cooldown
                if alert_key in self._last_alert_times:
                    time_since_last = datetime.now() - self._last_alert_times[alert_key]
                    if time_since_last.total_seconds() < self.config.alert_cooldown:
                        continue
                
                # Create alert
                alert = self._create_alert(threshold, current_value, severity)
                
                # Store alert
                self.active_alerts[alert_key] = alert
                self.alert_history.append(alert)
                self._last_alert_times[alert_key] = datetime.now()
                self._alert_timestamps.append(datetime.now())
                
                # Notify callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")
                
                logger.warning(f"Quality alert: {alert.message}")
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _can_send_alert(self) -> bool:
        """Check if we can send an alert (rate limiting)."""
        now = datetime.now()
        
        # Clean old timestamps
        cutoff = now - timedelta(hours=1)
        self._alert_timestamps = [ts for ts in self._alert_timestamps if ts > cutoff]
        
        # Check rate limit
        return len(self._alert_timestamps) < self.config.max_alerts_per_hour
    
    def _get_metric_value(self, metric_type: MetricType) -> Optional[float]:
        """Get current value for metric type."""
        if not self.current_metrics:
            return None
        
        metric_map = {
            MetricType.HEALTH_SCORE: self.current_metrics.health_score,
            MetricType.TECHNICAL_DEBT: self.current_metrics.technical_debt_score,
            MetricType.COMPLEXITY: self.current_metrics.complexity_score,
            MetricType.MAINTAINABILITY: self.current_metrics.maintainability_score,
            MetricType.DOCUMENTATION: self.current_metrics.documentation_coverage,
            MetricType.TEST_COVERAGE: self.current_metrics.test_coverage,
            MetricType.DEAD_CODE: float(self.current_metrics.dead_code_count),
            MetricType.CIRCULAR_DEPS: float(self.current_metrics.circular_dependencies_count)
        }
        
        return metric_map.get(metric_type)
    
    def _create_alert(self, threshold: QualityThreshold, current_value: float, 
                     severity: QualitySeverity) -> QualityAlert:
        """Create quality alert."""
        
        # Generate alert message
        if threshold.direction == "lower":
            threshold_val = (threshold.critical_threshold if severity == QualitySeverity.CRITICAL 
                           else threshold.warning_threshold)
            message = (f"{threshold.metric_type.value.replace('_', ' ').title()} is below threshold: "
                      f"{current_value:.2f} < {threshold_val:.2f}")
        else:
            threshold_val = (threshold.critical_threshold if severity == QualitySeverity.CRITICAL 
                           else threshold.warning_threshold)
            message = (f"{threshold.metric_type.value.replace('_', ' ').title()} is above threshold: "
                      f"{current_value:.2f} > {threshold_val:.2f}")
        
        # Generate suggested actions
        suggested_actions = self._get_suggested_actions(threshold.metric_type, severity)
        
        return QualityAlert(
            id=f"{threshold.metric_type.value}_{int(time.time())}",
            timestamp=datetime.now(),
            severity=severity,
            metric_type=threshold.metric_type,
            message=message,
            current_value=current_value,
            threshold_value=threshold_val,
            suggested_actions=suggested_actions
        )
    
    def _get_suggested_actions(self, metric_type: MetricType, severity: QualitySeverity) -> List[str]:
        """Get suggested actions for metric type."""
        actions_map = {
            MetricType.HEALTH_SCORE: [
                "Run comprehensive code analysis",
                "Address high-priority issues",
                "Review and refactor complex functions",
                "Improve test coverage"
            ],
            MetricType.TECHNICAL_DEBT: [
                "Refactor high-complexity functions",
                "Remove dead code",
                "Improve documentation",
                "Address circular dependencies"
            ],
            MetricType.COMPLEXITY: [
                "Break down complex functions",
                "Simplify conditional logic",
                "Extract helper methods",
                "Review algorithmic complexity"
            ],
            MetricType.MAINTAINABILITY: [
                "Improve code documentation",
                "Reduce function complexity",
                "Enhance class cohesion",
                "Follow coding standards"
            ],
            MetricType.DOCUMENTATION: [
                "Add missing docstrings",
                "Improve inline comments",
                "Update API documentation",
                "Add type annotations"
            ],
            MetricType.TEST_COVERAGE: [
                "Write unit tests for uncovered code",
                "Add integration tests",
                "Improve test quality",
                "Review test effectiveness"
            ]
        }
        
        return actions_map.get(metric_type, ["Review and improve code quality"])
    
    async def _store_metrics(self, metrics: QualityMetrics):
        """Store metrics to persistent storage."""
        if not self.config.storage_path:
            return
        
        try:
            storage_path = Path(self.config.storage_path)
            storage_path.mkdir(parents=True, exist_ok=True)
            
            # Store as JSON
            metrics_file = storage_path / f"metrics_{metrics.timestamp.strftime('%Y%m%d')}.json"
            
            # Load existing data
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
            else:
                data = []
            
            # Append new metrics
            data.append(metrics.to_dict())
            
            # Save back
            with open(metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
    
    def get_current_metrics(self) -> Optional[QualityMetrics]:
        """Get current quality metrics."""
        return self.current_metrics
    
    def get_metrics_history(self, hours: int = 24) -> List[QualityMetrics]:
        """Get metrics history for specified hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp > cutoff]
    
    def get_active_alerts(self) -> List[QualityAlert]:
        """Get currently active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[QualityAlert]:
        """Get alert history for specified hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alert_history if a.timestamp > cutoff]
    
    def get_quality_trends(self, hours: int = 24) -> List[QualityTrend]:
        """Get quality trends for specified period."""
        try:
            recent_metrics = self.get_metrics_history(hours)
            if len(recent_metrics) < 2:
                return []
            
            current = recent_metrics[-1]
            previous = recent_metrics[0]
            time_period = current.timestamp - previous.timestamp
            
            trends = []
            
            # Calculate trends for each metric
            metric_pairs = [
                (MetricType.HEALTH_SCORE, current.health_score, previous.health_score),
                (MetricType.TECHNICAL_DEBT, current.technical_debt_score, previous.technical_debt_score),
                (MetricType.COMPLEXITY, current.complexity_score, previous.complexity_score),
                (MetricType.MAINTAINABILITY, current.maintainability_score, previous.maintainability_score),
                (MetricType.DOCUMENTATION, current.documentation_coverage, previous.documentation_coverage),
                (MetricType.TEST_COVERAGE, current.test_coverage, previous.test_coverage)
            ]
            
            for metric_type, current_val, previous_val in metric_pairs:
                if previous_val == 0:
                    continue
                
                change_pct = ((current_val - previous_val) / previous_val) * 100
                
                # Determine trend direction
                if abs(change_pct) < 1:  # Less than 1% change
                    direction = "stable"
                elif metric_type in [MetricType.HEALTH_SCORE, MetricType.MAINTAINABILITY, 
                                   MetricType.DOCUMENTATION, MetricType.TEST_COVERAGE]:
                    # Higher is better for these metrics
                    direction = "improving" if change_pct > 0 else "degrading"
                else:
                    # Lower is better for these metrics
                    direction = "improving" if change_pct < 0 else "degrading"
                
                trend = QualityTrend(
                    metric_type=metric_type,
                    current_value=current_val,
                    previous_value=previous_val,
                    change_percentage=change_pct,
                    trend_direction=direction,
                    time_period=time_period
                )
                trends.append(trend)
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating quality trends: {e}")
            return []
    
    def add_metric_callback(self, callback: Callable[[QualityMetrics], None]):
        """Add callback for metric updates."""
        self.metric_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable[[QualityAlert], None]):
        """Add callback for alerts."""
        self.alert_callbacks.append(callback)
    
    def add_trend_callback(self, callback: Callable[[List[QualityTrend]], None]):
        """Add callback for trend updates."""
        self.trend_callbacks.append(callback)
    
    async def force_analysis(self) -> QualityMetrics:
        """Force immediate analysis."""
        await self._perform_analysis()
        return self.current_metrics
    
    def clear_alerts(self):
        """Clear all active alerts."""
        self.active_alerts.clear()
    
    def update_config(self, config: MonitoringConfig):
        """Update monitoring configuration."""
        self.config = config
        logger.info("Monitoring configuration updated")

