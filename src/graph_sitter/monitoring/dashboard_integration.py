"""
Dashboard Integration for Real-time Quality Monitoring

Provides live metrics, widgets, and real-time updates for quality dashboards.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from .quality_monitor import QualityMonitor, QualityMetrics, QualityTrend
from .real_time_analyzer import RealTimeAnalyzer, AnalysisResult
from .alert_system import AlertSystem, QualityAlert

logger = logging.getLogger(__name__)


@dataclass
class QualityWidget:
    """Quality dashboard widget configuration."""
    id: str
    title: str
    widget_type: str  # "metric", "chart", "alert", "trend"
    metric_type: str
    size: str = "medium"  # "small", "medium", "large"
    refresh_interval: int = 30  # seconds
    config: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'widget_type': self.widget_type,
            'metric_type': self.metric_type,
            'size': self.size,
            'refresh_interval': self.refresh_interval,
            'config': self.config or {}
        }


@dataclass
class TrendChart:
    """Trend chart configuration."""
    id: str
    title: str
    metrics: List[str]
    time_range: str = "24h"  # "1h", "6h", "24h", "7d"
    chart_type: str = "line"  # "line", "area", "bar"
    show_threshold: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'metrics': self.metrics,
            'time_range': self.time_range,
            'chart_type': self.chart_type,
            'show_threshold': self.show_threshold
        }


class LiveMetricsProvider:
    """Provides live metrics data for dashboards."""
    
    def __init__(self, quality_monitor: QualityMonitor):
        self.quality_monitor = quality_monitor
        self.subscribers: Dict[str, Callable] = {}
        self.is_running = False
        self.update_task: Optional[asyncio.Task] = None
        self.update_interval = 5  # seconds
    
    async def start(self):
        """Start live metrics provider."""
        if self.is_running:
            return
        
        self.is_running = True
        self.update_task = asyncio.create_task(self._update_loop())
        logger.info("Live metrics provider started")
    
    async def stop(self):
        """Stop live metrics provider."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Live metrics provider stopped")
    
    async def _update_loop(self):
        """Main update loop."""
        while self.is_running:
            try:
                # Get current metrics
                current_metrics = self.quality_monitor.get_current_metrics()
                if current_metrics:
                    # Notify all subscribers
                    for subscriber_id, callback in self.subscribers.items():
                        try:
                            await self._notify_subscriber(callback, current_metrics)
                        except Exception as e:
                            logger.error(f"Error notifying subscriber {subscriber_id}: {e}")
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in live metrics update loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _notify_subscriber(self, callback: Callable, metrics: QualityMetrics):
        """Notify subscriber with metrics."""
        if asyncio.iscoroutinefunction(callback):
            await callback(metrics)
        else:
            callback(metrics)
    
    def subscribe(self, subscriber_id: str, callback: Callable):
        """Subscribe to live metrics updates."""
        self.subscribers[subscriber_id] = callback
        logger.info(f"Subscriber added: {subscriber_id}")
    
    def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from live metrics updates."""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            logger.info(f"Subscriber removed: {subscriber_id}")
    
    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """Get current metrics as dictionary."""
        metrics = self.quality_monitor.get_current_metrics()
        return metrics.to_dict() if metrics else None
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history."""
        history = self.quality_monitor.get_metrics_history(hours)
        return [m.to_dict() for m in history]
    
    def get_quality_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get quality trends."""
        trends = self.quality_monitor.get_quality_trends(hours)
        return [asdict(t) for t in trends]


class DashboardMonitor:
    """Main dashboard monitoring system."""
    
    def __init__(self, quality_monitor: QualityMonitor, 
                 real_time_analyzer: Optional[RealTimeAnalyzer] = None,
                 alert_system: Optional[AlertSystem] = None):
        self.quality_monitor = quality_monitor
        self.real_time_analyzer = real_time_analyzer
        self.alert_system = alert_system
        
        # Components
        self.live_metrics = LiveMetricsProvider(quality_monitor)
        
        # Dashboard state
        self.widgets: Dict[str, QualityWidget] = {}
        self.charts: Dict[str, TrendChart] = {}
        self.dashboard_config: Dict[str, Any] = {}
        
        # WebSocket connections (for real-time updates)
        self.websocket_connections: Dict[str, Any] = {}
        
        # Setup default widgets
        self._setup_default_widgets()
        self._setup_default_charts()
    
    def _setup_default_widgets(self):
        """Setup default dashboard widgets."""
        default_widgets = [
            QualityWidget(
                id="health_score",
                title="Health Score",
                widget_type="metric",
                metric_type="health_score",
                size="large",
                config={
                    "format": "percentage",
                    "color_thresholds": {
                        "good": 0.8,
                        "warning": 0.6,
                        "critical": 0.4
                    }
                }
            ),
            QualityWidget(
                id="technical_debt",
                title="Technical Debt",
                widget_type="metric",
                metric_type="technical_debt_score",
                size="medium",
                config={
                    "format": "percentage",
                    "invert_colors": True  # Lower is better
                }
            ),
            QualityWidget(
                id="complexity",
                title="Complexity Score",
                widget_type="metric",
                metric_type="complexity_score",
                size="medium",
                config={
                    "format": "percentage",
                    "invert_colors": True
                }
            ),
            QualityWidget(
                id="maintainability",
                title="Maintainability",
                widget_type="metric",
                metric_type="maintainability_score",
                size="medium"
            ),
            QualityWidget(
                id="documentation",
                title="Documentation Coverage",
                widget_type="metric",
                metric_type="documentation_coverage",
                size="small"
            ),
            QualityWidget(
                id="test_coverage",
                title="Test Coverage",
                widget_type="metric",
                metric_type="test_coverage",
                size="small"
            ),
            QualityWidget(
                id="active_alerts",
                title="Active Alerts",
                widget_type="alert",
                metric_type="alerts",
                size="medium",
                refresh_interval=10
            ),
            QualityWidget(
                id="recent_changes",
                title="Recent Changes",
                widget_type="trend",
                metric_type="changes",
                size="large",
                refresh_interval=15
            )
        ]
        
        for widget in default_widgets:
            self.widgets[widget.id] = widget
    
    def _setup_default_charts(self):
        """Setup default trend charts."""
        default_charts = [
            TrendChart(
                id="quality_overview",
                title="Quality Overview",
                metrics=["health_score", "technical_debt_score", "maintainability_score"],
                time_range="24h",
                chart_type="line"
            ),
            TrendChart(
                id="complexity_trend",
                title="Complexity Trend",
                metrics=["complexity_score", "high_complexity_functions"],
                time_range="24h",
                chart_type="area"
            ),
            TrendChart(
                id="coverage_trend",
                title="Coverage Trends",
                metrics=["documentation_coverage", "test_coverage"],
                time_range="7d",
                chart_type="line"
            ),
            TrendChart(
                id="issues_trend",
                title="Issues Trend",
                metrics=["dead_code_count", "circular_dependencies_count"],
                time_range="7d",
                chart_type="bar"
            )
        ]
        
        for chart in default_charts:
            self.charts[chart.id] = chart
    
    async def start(self):
        """Start dashboard monitoring."""
        await self.live_metrics.start()
        
        # Setup callbacks
        if self.real_time_analyzer:
            self.real_time_analyzer.add_analysis_callback(self._on_analysis_result)
        
        if self.alert_system:
            # Setup alert callback if needed
            pass
        
        logger.info("Dashboard monitoring started")
    
    async def stop(self):
        """Stop dashboard monitoring."""
        await self.live_metrics.stop()
        logger.info("Dashboard monitoring stopped")
    
    def _on_analysis_result(self, result: AnalysisResult):
        """Handle real-time analysis result."""
        # This could trigger dashboard updates for specific files
        logger.debug(f"Analysis result received for: {result.file_path}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data."""
        current_metrics = self.live_metrics.get_current_metrics()
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': current_metrics,
            'widgets': [w.to_dict() for w in self.widgets.values()],
            'charts': [c.to_dict() for c in self.charts.values()],
            'alerts': self._get_alert_data(),
            'trends': self.live_metrics.get_quality_trends(24),
            'recent_changes': self._get_recent_changes(),
            'config': self.dashboard_config
        }
        
        return dashboard_data
    
    def _get_alert_data(self) -> Dict[str, Any]:
        """Get alert data for dashboard."""
        if not self.alert_system:
            return {'active': [], 'recent': []}
        
        active_alerts = []
        recent_alerts = []
        
        # Get active alerts from quality monitor
        if hasattr(self.quality_monitor, 'get_active_alerts'):
            active_alerts = [a.to_dict() for a in self.quality_monitor.get_active_alerts()]
        
        # Get recent alerts from alert system
        recent_alerts = self.alert_system.get_alert_history(24)
        
        return {
            'active': active_alerts,
            'recent': recent_alerts,
            'count': len(active_alerts)
        }
    
    def _get_recent_changes(self) -> List[Dict[str, Any]]:
        """Get recent file changes."""
        if not self.real_time_analyzer:
            return []
        
        recent_results = self.real_time_analyzer.get_recent_results(1)  # Last hour
        return [r.to_dict() for r in recent_results]
    
    def get_widget_data(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get data for specific widget."""
        widget = self.widgets.get(widget_id)
        if not widget:
            return None
        
        current_metrics = self.live_metrics.get_current_metrics()
        if not current_metrics:
            return None
        
        widget_data = widget.to_dict()
        
        # Add current value
        if widget.metric_type in current_metrics:
            widget_data['current_value'] = current_metrics[widget.metric_type]
        
        # Add trend data for trend widgets
        if widget.widget_type == "trend":
            trends = self.live_metrics.get_quality_trends(24)
            widget_data['trend_data'] = trends
        
        # Add alert data for alert widgets
        elif widget.widget_type == "alert":
            widget_data['alert_data'] = self._get_alert_data()
        
        return widget_data
    
    def get_chart_data(self, chart_id: str) -> Optional[Dict[str, Any]]:
        """Get data for specific chart."""
        chart = self.charts.get(chart_id)
        if not chart:
            return None
        
        # Parse time range
        time_range_map = {
            "1h": 1,
            "6h": 6,
            "24h": 24,
            "7d": 24 * 7
        }
        hours = time_range_map.get(chart.time_range, 24)
        
        # Get metrics history
        history = self.live_metrics.get_metrics_history(hours)
        
        # Extract data for chart metrics
        chart_data = chart.to_dict()
        chart_data['data'] = []
        
        for metrics in history:
            data_point = {
                'timestamp': metrics['timestamp'],
            }
            
            for metric in chart.metrics:
                if metric in metrics:
                    data_point[metric] = metrics[metric]
            
            chart_data['data'].append(data_point)
        
        return chart_data
    
    def add_widget(self, widget: QualityWidget):
        """Add widget to dashboard."""
        self.widgets[widget.id] = widget
        logger.info(f"Widget added: {widget.title}")
    
    def remove_widget(self, widget_id: str):
        """Remove widget from dashboard."""
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            logger.info(f"Widget removed: {widget_id}")
    
    def add_chart(self, chart: TrendChart):
        """Add chart to dashboard."""
        self.charts[chart.id] = chart
        logger.info(f"Chart added: {chart.title}")
    
    def remove_chart(self, chart_id: str):
        """Remove chart from dashboard."""
        if chart_id in self.charts:
            del self.charts[chart_id]
            logger.info(f"Chart removed: {chart_id}")
    
    def update_dashboard_config(self, config: Dict[str, Any]):
        """Update dashboard configuration."""
        self.dashboard_config.update(config)
        logger.info("Dashboard configuration updated")
    
    def subscribe_to_updates(self, subscriber_id: str, callback: Callable):
        """Subscribe to live dashboard updates."""
        self.live_metrics.subscribe(subscriber_id, callback)
    
    def unsubscribe_from_updates(self, subscriber_id: str):
        """Unsubscribe from live dashboard updates."""
        self.live_metrics.unsubscribe(subscriber_id)
    
    def export_dashboard_config(self) -> Dict[str, Any]:
        """Export dashboard configuration."""
        return {
            'widgets': [w.to_dict() for w in self.widgets.values()],
            'charts': [c.to_dict() for c in self.charts.values()],
            'config': self.dashboard_config,
            'export_timestamp': datetime.now().isoformat()
        }
    
    def import_dashboard_config(self, config: Dict[str, Any]):
        """Import dashboard configuration."""
        try:
            # Import widgets
            if 'widgets' in config:
                self.widgets.clear()
                for widget_data in config['widgets']:
                    widget = QualityWidget(**widget_data)
                    self.widgets[widget.id] = widget
            
            # Import charts
            if 'charts' in config:
                self.charts.clear()
                for chart_data in config['charts']:
                    chart = TrendChart(**chart_data)
                    self.charts[chart.id] = chart
            
            # Import config
            if 'config' in config:
                self.dashboard_config = config['config']
            
            logger.info("Dashboard configuration imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing dashboard configuration: {e}")
            raise
    
    async def generate_dashboard_snapshot(self) -> Dict[str, Any]:
        """Generate complete dashboard snapshot."""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'dashboard_data': self.get_dashboard_data(),
            'system_status': {
                'quality_monitor_running': self.quality_monitor.is_running,
                'live_metrics_running': self.live_metrics.is_running,
                'real_time_analyzer_running': (
                    self.real_time_analyzer.is_watching 
                    if self.real_time_analyzer else False
                )
            },
            'performance_metrics': {
                'total_widgets': len(self.widgets),
                'total_charts': len(self.charts),
                'active_subscribers': len(self.live_metrics.subscribers)
            }
        }
        
        return snapshot

