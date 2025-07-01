# Real-time Code Quality Monitoring System

This document describes the comprehensive real-time monitoring system that provides continuous code quality assessment, alerting, and dashboard capabilities.

## 🎯 Overview

The Real-time Code Quality Monitoring System transforms static code analysis into a dynamic, continuous monitoring solution that provides:

- **Real-time Quality Metrics**: Live tracking of code health, complexity, and maintainability
- **File Change Detection**: Immediate analysis of code changes as they happen
- **Intelligent Alerting**: Multi-channel alerts with configurable rules and thresholds
- **Live Dashboards**: Real-time visualization with widgets and trend charts
- **Continuous Monitoring**: Session management, health checks, and automated reporting

## 🏗️ Architecture

### Core Components

```
Real-time Monitoring System
├── QualityMonitor           # Core quality metrics tracking
├── RealTimeAnalyzer        # File change detection & analysis
├── AlertSystem             # Multi-channel alerting
├── DashboardMonitor        # Live dashboard integration
└── ContinuousMonitor       # Session & health management
```

### Data Flow

```
File Changes → Real-time Analysis → Quality Metrics → Alerts & Dashboard
     ↓              ↓                    ↓              ↓
File Watcher → Incremental → Metric Updates → Notifications
     ↓         Analysis         ↓              ↓
Debouncing → Quality Deltas → Trend Analysis → Reporting
```

## 📊 Quality Monitor

### Core Features

The `QualityMonitor` provides continuous quality assessment with:

- **Configurable Analysis Intervals**: From seconds to hours
- **Quality Threshold Monitoring**: Customizable warning and critical thresholds
- **Trend Analysis**: Historical quality trend tracking
- **Alert Generation**: Automatic threshold violation detection
- **Metric Storage**: Persistent storage of quality metrics

### Basic Usage

```python
from graph_sitter import Codebase
from graph_sitter.monitoring import QualityMonitor, MonitoringConfig

# Configure monitoring
config = MonitoringConfig(
    analysis_interval=300,  # 5 minutes
    alert_check_interval=60,  # 1 minute
    enable_alerts=True,
    store_metrics=True,
    storage_path="./monitoring_data"
)

# Create and start monitor
codebase = Codebase(".")
monitor = QualityMonitor(codebase, config)

# Add callbacks
def on_metrics_update(metrics):
    print(f"Health Score: {metrics.health_score:.2f}")
    print(f"Technical Debt: {metrics.technical_debt_score:.2f}")

def on_alert_generated(alert):
    print(f"Alert: {alert.message}")

monitor.add_metric_callback(on_metrics_update)
monitor.add_alert_callback(on_alert_generated)

# Start monitoring
await monitor.start_monitoring()

# Monitor runs continuously...

# Stop monitoring
await monitor.stop_monitoring()
```

### Quality Metrics

The system tracks comprehensive quality metrics:

```python
@dataclass
class QualityMetrics:
    timestamp: datetime
    health_score: float                    # Overall health (0-1)
    technical_debt_score: float           # Technical debt level (0-1)
    complexity_score: float               # Code complexity (0-1)
    maintainability_score: float          # Maintainability index (0-1)
    documentation_coverage: float         # Documentation coverage (0-1)
    test_coverage: float                  # Test coverage estimate (0-1)
    dead_code_count: int                  # Number of dead code items
    circular_dependencies_count: int      # Circular dependency count
    
    # Additional metrics
    total_functions: int
    total_classes: int
    total_lines: int
    high_complexity_functions: int
    low_cohesion_classes: int
```

### Threshold Configuration

```python
from graph_sitter.monitoring import QualityThreshold, MetricType

# Configure custom thresholds
thresholds = [
    QualityThreshold(
        metric_type=MetricType.HEALTH_SCORE,
        warning_threshold=0.7,
        critical_threshold=0.5,
        direction="lower"  # Values below threshold are bad
    ),
    QualityThreshold(
        metric_type=MetricType.TECHNICAL_DEBT,
        warning_threshold=0.7,
        critical_threshold=0.9,
        direction="higher"  # Values above threshold are bad
    )
]

config = MonitoringConfig(thresholds=thresholds)
```

## 🔄 Real-time Analyzer

### File Change Detection

The `RealTimeAnalyzer` provides real-time file monitoring with:

- **File System Watching**: Automatic detection of file changes
- **Debouncing**: Intelligent batching of rapid changes
- **Incremental Analysis**: Efficient analysis of only changed code
- **Quality Delta Tracking**: Measurement of quality changes

### Usage Example

```python
from graph_sitter.monitoring import RealTimeAnalyzer, AnalysisScope

# Create analyzer
analyzer = RealTimeAnalyzer(codebase, watch_path="./src")

# Configure analysis
analyzer.set_analysis_scope(AnalysisScope.FILE_AND_DEPENDENCIES)
analyzer.set_debounce_delay(2.0)  # 2 second debounce

# Add callbacks
def on_file_change(change_event):
    print(f"File changed: {change_event.file_path}")
    print(f"Change type: {change_event.change_type.value}")

def on_analysis_result(result):
    print(f"Analysis complete: {result.file_path}")
    print(f"Quality change: {result.overall_quality_change:+.2f}")
    
    for delta in result.quality_deltas:
        improvement = "✅" if delta.is_improvement else "❌"
        print(f"  {improvement} {delta.metric_name}: {delta.change:+.2f}")

analyzer.add_change_callback(on_file_change)
analyzer.add_analysis_callback(on_analysis_result)

# Start watching
await analyzer.start_watching()

# Analyzer monitors file changes continuously...

# Stop watching
await analyzer.stop_watching()
```

### Analysis Scopes

The system supports different analysis scopes:

- **FILE_ONLY**: Analyze only the changed file
- **FILE_AND_DEPENDENCIES**: Analyze file and its dependencies
- **FULL_CODEBASE**: Run complete codebase analysis

### Quality Delta Tracking

```python
@dataclass
class QualityDelta:
    metric_name: str
    old_value: float
    new_value: float
    change: float
    change_percentage: float
    
    @property
    def is_improvement(self) -> bool:
        # Automatically determines if change is positive
        return self.change > 0 for quality metrics
```

## 🚨 Alert System

### Multi-Channel Alerting

The alert system supports multiple notification channels:

- **Console**: Terminal output with formatting
- **Email**: SMTP email notifications
- **Webhook**: HTTP POST to custom endpoints
- **Slack**: Slack webhook integration
- **Microsoft Teams**: Teams webhook integration
- **File**: Log alerts to files (JSON/text)

### Alert Configuration

```python
from graph_sitter.monitoring import (
    AlertSystem, AlertChannelConfig, AlertRule, 
    AlertChannel, QualitySeverity, MetricType
)

# Configure alert channels
config = AlertChannelConfig(
    # Email settings
    email_smtp_server="smtp.gmail.com",
    email_smtp_port=587,
    email_username="monitoring@company.com",
    email_password="password",
    email_from="monitoring@company.com",
    email_to=["team@company.com"],
    
    # Slack settings
    slack_webhook_url="https://hooks.slack.com/...",
    slack_channel="#quality-alerts",
    
    # File settings
    file_path="./alerts.log",
    file_format="json"
)

# Create alert system
alert_system = AlertSystem(config)

# Add custom alert rules
rule = AlertRule(
    id="health_critical",
    name="Critical Health Score",
    description="Health score below 50%",
    metric_type=MetricType.HEALTH_SCORE,
    severity_threshold=QualitySeverity.CRITICAL,
    channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
    max_value=0.5,
    cooldown_minutes=30,
    include_suggestions=True
)

alert_system.add_rule(rule)
```

### Alert Rules

Alert rules provide flexible condition matching:

```python
@dataclass
class AlertRule:
    id: str
    name: str
    description: str
    metric_type: MetricType
    severity_threshold: QualitySeverity
    channels: List[AlertChannel]
    
    # Conditions
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    change_threshold: Optional[float] = None
    
    # Rate limiting
    cooldown_minutes: int = 30
    max_alerts_per_hour: int = 5
    
    # Customization
    custom_message: Optional[str] = None
    include_suggestions: bool = True
```

### Alert Processing

```python
# Process alerts automatically from quality monitor
quality_monitor.add_alert_callback(alert_system.process_alert)

# Or process alerts manually
from graph_sitter.monitoring import QualityAlert

alert = QualityAlert(
    id="manual_alert",
    timestamp=datetime.now(),
    severity=QualitySeverity.HIGH,
    metric_type=MetricType.COMPLEXITY,
    message="Code complexity increased significantly",
    current_value=0.85,
    threshold_value=0.8
)

await alert_system.process_alert(alert)
```

## 📊 Dashboard Integration

### Live Dashboard Features

The dashboard system provides real-time visualization:

- **Live Metrics Widgets**: Real-time quality metric displays
- **Trend Charts**: Historical trend visualization
- **Alert Panels**: Active and recent alert displays
- **Change Tracking**: Recent file change summaries
- **Health Status**: System component health monitoring

### Dashboard Setup

```python
from graph_sitter.monitoring import DashboardMonitor, QualityWidget, TrendChart

# Create dashboard monitor
dashboard = DashboardMonitor(quality_monitor, real_time_analyzer, alert_system)

# Add custom widgets
custom_widget = QualityWidget(
    id="custom_health",
    title="Custom Health Score",
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
)

dashboard.add_widget(custom_widget)

# Add custom charts
custom_chart = TrendChart(
    id="quality_trends",
    title="Quality Trends",
    metrics=["health_score", "technical_debt_score"],
    time_range="24h",
    chart_type="line"
)

dashboard.add_chart(custom_chart)

# Start dashboard
await dashboard.start()

# Subscribe to live updates
def on_dashboard_update(metrics):
    print(f"Dashboard update: {metrics.health_score:.2f}")

dashboard.subscribe_to_updates("my_subscriber", on_dashboard_update)
```

### Dashboard Data API

```python
# Get complete dashboard data
dashboard_data = dashboard.get_dashboard_data()

# Get specific widget data
widget_data = dashboard.get_widget_data("health_score")

# Get specific chart data
chart_data = dashboard.get_chart_data("quality_trends")

# Export/import dashboard configuration
config = dashboard.export_dashboard_config()
dashboard.import_dashboard_config(config)

# Generate dashboard snapshot
snapshot = await dashboard.generate_dashboard_snapshot()
```

## 🔄 Continuous Monitoring

### Session Management

The continuous monitoring system provides comprehensive session management:

- **Session Lifecycle**: Start, pause, resume, stop monitoring sessions
- **Health Monitoring**: Automatic system health checks
- **Report Generation**: Automated quality reports
- **Statistics Tracking**: Comprehensive monitoring statistics

### Continuous Monitoring Setup

```python
from graph_sitter.monitoring import ContinuousMonitor

# Create continuous monitor
continuous_monitor = ContinuousMonitor(codebase, monitoring_config, alert_config)

# Add session callbacks
def on_session_event(session):
    print(f"Session {session.name}: {session.status.value}")

def on_health_check(health_checks):
    for check in health_checks:
        print(f"{check.component}: {check.status.value}")

def on_report_generated(report):
    print(f"Report generated: {report.id}")
    print(f"Recommendations: {len(report.recommendations)}")

continuous_monitor.add_session_callback(on_session_event)
continuous_monitor.add_health_callback(on_health_check)
continuous_monitor.add_report_callback(on_report_generated)

# Start monitoring session
session_id = await continuous_monitor.start_monitoring("Production Monitoring")

# Monitor runs continuously with health checks and reporting...

# Stop monitoring session
final_report = await continuous_monitor.stop_monitoring()
```

### Health Monitoring

The system performs automatic health checks on all components:

```python
# Get current health status
health_status = continuous_monitor.get_health_status()

print(f"Overall Status: {health_status['overall_status']}")
print(f"Components: {len(health_status['components'])}")

for component, check in health_status['components'].items():
    print(f"  {component}: {check['status']} - {check['message']}")
```

### Quality Reports

Automated reports provide comprehensive session summaries:

```python
@dataclass
class QualityReport:
    id: str
    session_id: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    
    # Metrics summary
    initial_metrics: Optional[QualityMetrics]
    final_metrics: Optional[QualityMetrics]
    average_metrics: Dict[str, float]
    
    # Analysis results
    total_analyses: int
    files_analyzed: int
    issues_found: int
    issues_resolved: int
    
    # Alerts
    total_alerts: int
    critical_alerts: int
    
    # Recommendations
    recommendations: List[str]
```

## 🔧 Configuration

### Monitoring Configuration

```python
@dataclass
class MonitoringConfig:
    # Intervals
    analysis_interval: int = 300        # 5 minutes
    alert_check_interval: int = 60      # 1 minute
    trend_analysis_period: int = 3600   # 1 hour
    
    # Thresholds
    thresholds: List[QualityThreshold] = field(default_factory=list)
    
    # Alerts
    enable_alerts: bool = True
    alert_cooldown: int = 1800          # 30 minutes
    max_alerts_per_hour: int = 10
    
    # Storage
    store_metrics: bool = True
    metrics_retention_days: int = 30
    storage_path: Optional[str] = None
    
    # Notifications
    notification_channels: List[str] = field(default_factory=list)
    webhook_urls: List[str] = field(default_factory=list)
```

### Alert Channel Configuration

```python
@dataclass
class AlertChannelConfig:
    # Email settings
    email_smtp_server: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: List[str] = field(default_factory=list)
    
    # Webhook settings
    webhook_urls: List[str] = field(default_factory=list)
    webhook_timeout: int = 30
    
    # Slack settings
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    
    # Teams settings
    teams_webhook_url: Optional[str] = None
    
    # File settings
    file_path: Optional[str] = None
    file_format: str = "json"
```

## 📈 Use Cases

### 1. Development Team Monitoring

```python
# Setup for development team
config = MonitoringConfig(
    analysis_interval=180,  # 3 minutes
    alert_check_interval=60,  # 1 minute
    enable_alerts=True
)

alert_config = AlertChannelConfig(
    slack_webhook_url="https://hooks.slack.com/...",
    slack_channel="#dev-quality",
    email_to=["team-lead@company.com"]
)

continuous_monitor = ContinuousMonitor(codebase, config, alert_config)
await continuous_monitor.start_monitoring("Development Team Monitoring")
```

### 2. CI/CD Integration

```python
# Setup for CI/CD pipeline
config = MonitoringConfig(
    analysis_interval=60,   # 1 minute for fast feedback
    enable_alerts=True,
    store_metrics=True,
    storage_path="/ci/monitoring_data"
)

alert_config = AlertChannelConfig(
    webhook_urls=["https://ci-system.com/webhook"],
    file_path="/ci/quality_alerts.json"
)

# Start monitoring for build
session_id = await continuous_monitor.start_monitoring(f"Build {build_number}")

# Run for duration of build...

# Stop and get report
report = await continuous_monitor.stop_monitoring()
if report.final_metrics.health_score < 0.7:
    # Fail the build
    exit(1)
```

### 3. Production Monitoring

```python
# Setup for production monitoring
config = MonitoringConfig(
    analysis_interval=600,  # 10 minutes
    alert_check_interval=120,  # 2 minutes
    enable_alerts=True,
    store_metrics=True,
    metrics_retention_days=90
)

alert_config = AlertChannelConfig(
    email_smtp_server="smtp.company.com",
    email_to=["ops-team@company.com", "dev-team@company.com"],
    slack_webhook_url="https://hooks.slack.com/...",
    slack_channel="#production-alerts"
)

# Add production-specific alert rules
production_rules = [
    AlertRule(
        id="prod_health_critical",
        name="Production Health Critical",
        description="Production health score critical",
        metric_type=MetricType.HEALTH_SCORE,
        severity_threshold=QualitySeverity.CRITICAL,
        channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
        max_value=0.6,
        cooldown_minutes=15  # Faster response for production
    )
]

alert_system = AlertSystem(alert_config)
for rule in production_rules:
    alert_system.add_rule(rule)

continuous_monitor = ContinuousMonitor(codebase, config, alert_config)
await continuous_monitor.start_monitoring("Production Monitoring")
```

### 4. Code Review Monitoring

```python
# Monitor code quality during review process
analyzer = RealTimeAnalyzer(codebase)
analyzer.set_analysis_scope(AnalysisScope.FILE_AND_DEPENDENCIES)

def on_analysis_result(result):
    if result.overall_quality_change < -0.1:  # Significant degradation
        print(f"⚠️  Quality degradation in {result.file_path}")
        print(f"   Change: {result.overall_quality_change:.2f}")
        
        # Post to code review system
        post_review_comment(
            file=result.file_path,
            message=f"Quality degradation detected: {result.overall_quality_change:.2f}"
        )

analyzer.add_analysis_callback(on_analysis_result)
await analyzer.start_watching()
```

## 🔍 Monitoring Best Practices

### 1. Threshold Configuration

- **Start Conservative**: Begin with loose thresholds and tighten based on experience
- **Environment-Specific**: Use different thresholds for development vs. production
- **Metric-Appropriate**: Consider the nature of each metric when setting thresholds

### 2. Alert Management

- **Rate Limiting**: Prevent alert fatigue with appropriate cooldowns
- **Channel Selection**: Use appropriate channels for different severity levels
- **Actionable Alerts**: Ensure alerts include clear next steps

### 3. Performance Considerations

- **Analysis Intervals**: Balance responsiveness with system load
- **Storage Management**: Configure appropriate retention periods
- **Debouncing**: Use appropriate debounce delays for file watching

### 4. Dashboard Design

- **Key Metrics First**: Prioritize most important metrics in dashboard layout
- **Trend Visualization**: Include trend charts for pattern recognition
- **Alert Integration**: Ensure alerts are prominently displayed

## 🚀 Advanced Features

### Custom Metric Providers

```python
class CustomMetricProvider:
    def get_custom_metrics(self, codebase):
        # Calculate custom metrics
        return {
            'custom_score': 0.85,
            'business_logic_complexity': 0.6
        }

# Integrate with monitoring system
monitor.add_custom_metric_provider(CustomMetricProvider())
```

### Webhook Integration

```python
# Custom webhook handler
async def handle_quality_webhook(alert_data):
    # Process alert data
    if alert_data['severity'] == 'critical':
        # Trigger automated response
        await trigger_automated_fix(alert_data)

# Register webhook handler
alert_system.add_webhook_handler(handle_quality_webhook)
```

### Machine Learning Integration

```python
# Integrate ML-based quality prediction
class MLQualityPredictor:
    def predict_quality_trend(self, metrics_history):
        # Use ML model to predict future quality
        return predicted_score

# Add to monitoring system
monitor.add_quality_predictor(MLQualityPredictor())
```

## 📊 Metrics and KPIs

### Quality Metrics

- **Health Score**: Overall codebase health (0-1)
- **Technical Debt Score**: Accumulated technical debt (0-1)
- **Complexity Score**: Code complexity level (0-1)
- **Maintainability Score**: Ease of maintenance (0-1)
- **Documentation Coverage**: Documentation completeness (0-1)
- **Test Coverage**: Test coverage estimate (0-1)

### Monitoring Metrics

- **Alert Response Time**: Time from threshold violation to alert
- **Analysis Frequency**: Number of analyses per time period
- **System Uptime**: Monitoring system availability
- **Data Retention**: Historical data availability

### Performance Metrics

- **Analysis Duration**: Time to complete quality analysis
- **File Processing Rate**: Files analyzed per second
- **Memory Usage**: System memory consumption
- **Storage Growth**: Rate of data storage growth

## 🔧 Troubleshooting

### Common Issues

#### 1. High Memory Usage

```python
# Reduce memory usage
config = MonitoringConfig(
    metrics_retention_days=7,  # Reduce retention
    analysis_interval=600      # Reduce frequency
)

# Clear old data
monitor.clear_old_metrics(days=7)
```

#### 2. Alert Fatigue

```python
# Adjust alert rules
rule.cooldown_minutes = 60      # Increase cooldown
rule.max_alerts_per_hour = 3    # Reduce frequency
rule.severity_threshold = QualitySeverity.HIGH  # Raise threshold
```

#### 3. File Watching Issues

```python
# Check file watcher status
if not analyzer.is_watching:
    print("File watcher not running")
    await analyzer.start_watching()

# Reduce debounce for faster response
analyzer.set_debounce_delay(0.5)
```

#### 4. Dashboard Performance

```python
# Optimize dashboard performance
dashboard.live_metrics.update_interval = 10  # Reduce update frequency

# Limit data points
chart_data = dashboard.get_chart_data("trends", max_points=100)
```

### Debugging

```python
# Enable debug logging
import logging
logging.getLogger('graph_sitter.monitoring').setLevel(logging.DEBUG)

# Check component status
health_status = continuous_monitor.get_health_status()
for component, status in health_status['components'].items():
    if status['status'] != 'healthy':
        print(f"Issue with {component}: {status['message']}")

# Monitor system statistics
stats = continuous_monitor.get_monitoring_statistics()
print(f"System stats: {stats}")
```

## 🎯 Future Enhancements

### Planned Features

1. **Predictive Analytics**: ML-based quality trend prediction
2. **Automated Remediation**: Automatic code quality fixes
3. **Integration APIs**: REST APIs for external system integration
4. **Mobile Dashboard**: Mobile-friendly monitoring interface
5. **Team Analytics**: Team-specific quality metrics and insights

### Extensibility

The monitoring system is designed for extensibility:

- **Custom Metrics**: Add domain-specific quality metrics
- **Custom Alerts**: Implement custom alert channels
- **Custom Analyzers**: Add specialized analysis capabilities
- **Custom Dashboards**: Create custom visualization components

This comprehensive real-time monitoring system provides the foundation for maintaining high code quality through continuous assessment, intelligent alerting, and actionable insights.

