#!/usr/bin/env python3
"""
Real-time Code Quality Monitoring Example

This example demonstrates the comprehensive real-time monitoring system
including quality monitoring, alerts, dashboard integration, and continuous monitoring.
"""

import asyncio
import logging
from pathlib import Path

from graph_sitter import Codebase
from graph_sitter.monitoring import (
    QualityMonitor,
    MonitoringConfig,
    QualityThreshold,
    MetricType,
    RealTimeAnalyzer,
    AnalysisScope,
    AlertSystem,
    AlertChannelConfig,
    AlertRule,
    AlertChannel,
    QualitySeverity,
    DashboardMonitor,
    ContinuousMonitor
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_quality_monitoring():
    """Demonstrate basic quality monitoring."""
    print("🔍 Quality Monitoring Demonstration")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Configure monitoring
    config = MonitoringConfig(
        analysis_interval=60,  # 1 minute for demo
        alert_check_interval=30,  # 30 seconds
        enable_alerts=True,
        store_metrics=True,
        storage_path="./monitoring_data"
    )
    
    # Create quality monitor
    monitor = QualityMonitor(codebase, config)
    
    # Add callback for metrics updates
    def on_metrics_update(metrics):
        print(f"📊 Metrics Update:")
        print(f"   Health Score: {metrics.health_score:.2f}")
        print(f"   Technical Debt: {metrics.technical_debt_score:.2f}")
        print(f"   Complexity: {metrics.complexity_score:.2f}")
        print(f"   Documentation: {metrics.documentation_coverage:.1%}")
    
    monitor.add_metric_callback(on_metrics_update)
    
    # Add callback for alerts
    def on_alert_generated(alert):
        print(f"🚨 Alert Generated:")
        print(f"   Severity: {alert.severity.value.upper()}")
        print(f"   Message: {alert.message}")
        print(f"   Metric: {alert.metric_type.value}")
        print(f"   Value: {alert.current_value:.2f}")
    
    monitor.add_alert_callback(on_alert_generated)
    
    # Start monitoring
    print("🚀 Starting quality monitoring...")
    await monitor.start_monitoring()
    
    # Let it run for a bit
    print("⏱️  Monitoring for 2 minutes...")
    await asyncio.sleep(120)
    
    # Get current metrics
    current_metrics = monitor.get_current_metrics()
    if current_metrics:
        print(f"\n📈 Current Quality Metrics:")
        print(f"   Health Score: {current_metrics.health_score:.2f}")
        print(f"   Technical Debt: {current_metrics.technical_debt_score:.2f}")
        print(f"   Maintainability: {current_metrics.maintainability_score:.2f}")
        print(f"   Documentation: {current_metrics.documentation_coverage:.1%}")
        print(f"   Test Coverage: {current_metrics.test_coverage:.1%}")
    
    # Get quality trends
    trends = monitor.get_quality_trends(1)  # Last hour
    if trends:
        print(f"\n📊 Quality Trends:")
        for trend in trends:
            direction_emoji = "📈" if trend.is_improving else "📉" if trend.is_degrading else "➡️"
            print(f"   {direction_emoji} {trend.metric_type.value}: {trend.change_percentage:+.1f}%")
    
    # Get active alerts
    active_alerts = monitor.get_active_alerts()
    print(f"\n🚨 Active Alerts: {len(active_alerts)}")
    for alert in active_alerts:
        print(f"   - {alert.severity.value.upper()}: {alert.message}")
    
    # Stop monitoring
    await monitor.stop_monitoring()
    print("✅ Quality monitoring demonstration complete")
    
    return monitor


async def demonstrate_real_time_analysis():
    """Demonstrate real-time file analysis."""
    print("\n🔄 Real-time Analysis Demonstration")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Create real-time analyzer
    analyzer = RealTimeAnalyzer(codebase, watch_path=".")
    
    # Configure analysis scope
    analyzer.set_analysis_scope(AnalysisScope.FILE_AND_DEPENDENCIES)
    analyzer.set_debounce_delay(1.0)  # 1 second for demo
    
    # Add callbacks
    def on_file_change(change_event):
        print(f"📁 File Change Detected:")
        print(f"   File: {change_event.file_path}")
        print(f"   Type: {change_event.change_type.value}")
        print(f"   Time: {change_event.timestamp.strftime('%H:%M:%S')}")
    
    def on_analysis_result(result):
        print(f"🔬 Analysis Complete:")
        print(f"   File: {result.file_path}")
        print(f"   Duration: {result.analysis_duration:.2f}s")
        print(f"   Quality Change: {result.overall_quality_change:+.2f}")
        print(f"   Impact Score: {result.impact_score:.2f}")
        
        if result.quality_deltas:
            print(f"   Quality Deltas:")
            for delta in result.quality_deltas:
                improvement = "✅" if delta.is_improvement else "❌"
                print(f"     {improvement} {delta.metric_name}: {delta.change:+.2f}")
    
    analyzer.add_change_callback(on_file_change)
    analyzer.add_analysis_callback(on_analysis_result)
    
    # Start watching
    print("👀 Starting real-time file watching...")
    await analyzer.start_watching()
    
    print("📝 Make some changes to Python files to see real-time analysis...")
    print("⏱️  Watching for 1 minute...")
    await asyncio.sleep(60)
    
    # Get recent results
    recent_results = analyzer.get_recent_results(1)  # Last hour
    print(f"\n📊 Recent Analysis Results: {len(recent_results)}")
    for result in recent_results:
        print(f"   - {result.file_path}: {result.overall_quality_change:+.2f} quality change")
    
    # Stop watching
    await analyzer.stop_watching()
    print("✅ Real-time analysis demonstration complete")
    
    return analyzer


async def demonstrate_alert_system():
    """Demonstrate alert system."""
    print("\n🚨 Alert System Demonstration")
    print("=" * 60)
    
    # Configure alert channels
    alert_config = AlertChannelConfig(
        # Console alerts for demo
        console_format="detailed",
        
        # File alerts
        file_path="./alerts.log",
        file_format="text",
        
        # Email configuration (commented out for demo)
        # email_smtp_server="smtp.gmail.com",
        # email_username="your-email@gmail.com",
        # email_password="your-password",
        # email_from="monitoring@yourcompany.com",
        # email_to=["admin@yourcompany.com"]
    )
    
    # Create alert system
    alert_system = AlertSystem(alert_config)
    
    # Add custom alert rules
    custom_rules = [
        AlertRule(
            id="health_score_warning",
            name="Health Score Warning",
            description="Health score below 70%",
            metric_type=MetricType.HEALTH_SCORE,
            severity_threshold=QualitySeverity.HIGH,
            channels=[AlertChannel.CONSOLE, AlertChannel.FILE],
            max_value=0.7,
            cooldown_minutes=5  # Short cooldown for demo
        ),
        AlertRule(
            id="complexity_critical",
            name="Critical Complexity",
            description="Complexity score above 90%",
            metric_type=MetricType.COMPLEXITY,
            severity_threshold=QualitySeverity.CRITICAL,
            channels=[AlertChannel.CONSOLE, AlertChannel.FILE],
            min_value=0.9,
            cooldown_minutes=5
        ),
        AlertRule(
            id="documentation_low",
            name="Low Documentation",
            description="Documentation coverage below 50%",
            metric_type=MetricType.DOCUMENTATION,
            severity_threshold=QualitySeverity.MEDIUM,
            channels=[AlertChannel.CONSOLE],
            max_value=0.5,
            cooldown_minutes=10
        )
    ]
    
    for rule in custom_rules:
        alert_system.add_rule(rule)
    
    print(f"📋 Alert Rules Configured: {len(alert_system.get_rules())}")
    for rule in alert_system.get_rules():
        print(f"   - {rule.name}: {rule.metric_type.value} ({rule.severity_threshold.value}+)")
    
    # Simulate some alerts (in real usage, these would come from quality monitor)
    from graph_sitter.monitoring.quality_monitor import QualityAlert
    import time
    from datetime import datetime
    
    test_alerts = [
        QualityAlert(
            id=f"test_alert_{int(time.time())}",
            timestamp=datetime.now(),
            severity=QualitySeverity.HIGH,
            metric_type=MetricType.HEALTH_SCORE,
            message="Health score has dropped below acceptable threshold",
            current_value=0.65,
            threshold_value=0.7,
            suggested_actions=[
                "Review recent code changes",
                "Run comprehensive analysis",
                "Address high-priority issues"
            ]
        ),
        QualityAlert(
            id=f"test_alert_{int(time.time()) + 1}",
            timestamp=datetime.now(),
            severity=QualitySeverity.CRITICAL,
            metric_type=MetricType.COMPLEXITY,
            message="Code complexity has reached critical levels",
            current_value=0.95,
            threshold_value=0.9,
            suggested_actions=[
                "Refactor complex functions",
                "Break down large methods",
                "Simplify conditional logic"
            ]
        )
    ]
    
    print("\n🧪 Testing Alert System...")
    for alert in test_alerts:
        await alert_system.process_alert(alert)
        await asyncio.sleep(1)  # Brief pause between alerts
    
    # Get delivery statistics
    delivery_stats = alert_system.get_delivery_stats()
    print(f"\n📊 Alert Delivery Statistics:")
    for channel, stats in delivery_stats.items():
        success_rate = stats['success'] / (stats['success'] + stats['error']) * 100 if (stats['success'] + stats['error']) > 0 else 0
        print(f"   {channel}: {stats['success']} sent, {stats['error']} errors ({success_rate:.1f}% success)")
    
    # Get alert history
    alert_history = alert_system.get_alert_history(1)  # Last hour
    print(f"\n📜 Alert History: {len(alert_history)} alerts in last hour")
    
    print("✅ Alert system demonstration complete")
    
    return alert_system


async def demonstrate_dashboard_integration():
    """Demonstrate dashboard integration."""
    print("\n📊 Dashboard Integration Demonstration")
    print("=" * 60)
    
    # Initialize components
    codebase = Codebase(".")
    quality_monitor = QualityMonitor(codebase)
    real_time_analyzer = RealTimeAnalyzer(codebase)
    alert_system = AlertSystem(AlertChannelConfig())
    
    # Create dashboard monitor
    dashboard = DashboardMonitor(quality_monitor, real_time_analyzer, alert_system)
    
    # Start components
    await quality_monitor.start_monitoring()
    await dashboard.start()
    
    # Let it collect some data
    print("📈 Collecting dashboard data...")
    await asyncio.sleep(30)
    
    # Get dashboard data
    dashboard_data = dashboard.get_dashboard_data()
    
    print(f"\n📊 Dashboard Overview:")
    print(f"   Widgets: {len(dashboard_data['widgets'])}")
    print(f"   Charts: {len(dashboard_data['charts'])}")
    print(f"   Active Alerts: {dashboard_data['alerts']['count']}")
    print(f"   Recent Changes: {len(dashboard_data['recent_changes'])}")
    
    # Show widget data
    print(f"\n🎛️  Widget Data:")
    for widget in dashboard_data['widgets']:
        widget_data = dashboard.get_widget_data(widget['id'])
        if widget_data and 'current_value' in widget_data:
            print(f"   {widget['title']}: {widget_data['current_value']:.2f}")
    
    # Show chart data
    print(f"\n📈 Chart Data:")
    for chart in dashboard_data['charts']:
        chart_data = dashboard.get_chart_data(chart['id'])
        if chart_data and chart_data['data']:
            data_points = len(chart_data['data'])
            print(f"   {chart['title']}: {data_points} data points")
    
    # Export dashboard configuration
    config_export = dashboard.export_dashboard_config()
    print(f"\n💾 Dashboard Configuration:")
    print(f"   Widgets: {len(config_export['widgets'])}")
    print(f"   Charts: {len(config_export['charts'])}")
    print(f"   Export Time: {config_export['export_timestamp']}")
    
    # Generate dashboard snapshot
    snapshot = await dashboard.generate_dashboard_snapshot()
    print(f"\n📸 Dashboard Snapshot:")
    print(f"   System Status: {snapshot['system_status']}")
    print(f"   Performance: {snapshot['performance_metrics']}")
    
    # Stop components
    await dashboard.stop()
    await quality_monitor.stop_monitoring()
    
    print("✅ Dashboard integration demonstration complete")
    
    return dashboard


async def demonstrate_continuous_monitoring():
    """Demonstrate continuous monitoring system."""
    print("\n🔄 Continuous Monitoring Demonstration")
    print("=" * 60)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Configure monitoring
    monitoring_config = MonitoringConfig(
        analysis_interval=30,  # 30 seconds for demo
        alert_check_interval=15,  # 15 seconds
        enable_alerts=True
    )
    
    alert_config = AlertChannelConfig(
        console_format="simple"
    )
    
    # Create continuous monitor
    continuous_monitor = ContinuousMonitor(codebase, monitoring_config, alert_config)
    
    # Add callbacks
    def on_session_event(session):
        print(f"📋 Session Event: {session.name} - {session.status.value}")
        if session.status.value == "running":
            print(f"   Started at: {session.start_time.strftime('%H:%M:%S')}")
        elif session.status.value == "stopped":
            print(f"   Duration: {(session.end_time - session.start_time).total_seconds():.0f}s")
            print(f"   Metrics Collected: {session.metrics_collected}")
            print(f"   Alerts Generated: {session.alerts_generated}")
    
    def on_health_check(health_checks):
        print(f"🏥 Health Check: {len(health_checks)} components checked")
        for check in health_checks:
            status_emoji = {"healthy": "✅", "warning": "⚠️", "critical": "❌", "unknown": "❓"}
            emoji = status_emoji.get(check.status.value, "❓")
            print(f"   {emoji} {check.component}: {check.message}")
    
    def on_report_generated(report):
        print(f"📊 Report Generated: {report.id}")
        print(f"   Duration: {report.duration.total_seconds():.0f}s")
        print(f"   Analyses: {report.total_analyses}")
        print(f"   Alerts: {report.total_alerts}")
        if report.recommendations:
            print(f"   Recommendations: {len(report.recommendations)}")
    
    continuous_monitor.add_session_callback(on_session_event)
    continuous_monitor.add_health_callback(on_health_check)
    continuous_monitor.add_report_callback(on_report_generated)
    
    # Start monitoring session
    print("🚀 Starting continuous monitoring session...")
    session_id = await continuous_monitor.start_monitoring("Demo Session")
    print(f"   Session ID: {session_id}")
    
    # Let it run for a while
    print("⏱️  Running monitoring session for 2 minutes...")
    await asyncio.sleep(120)
    
    # Get current session info
    current_session = continuous_monitor.get_current_session()
    if current_session:
        print(f"\n📋 Current Session Status:")
        print(f"   Name: {current_session.name}")
        print(f"   Status: {current_session.status.value}")
        print(f"   Metrics Collected: {current_session.metrics_collected}")
        print(f"   Alerts Generated: {current_session.alerts_generated}")
        print(f"   Analyses Performed: {current_session.analyses_performed}")
    
    # Get health status
    health_status = continuous_monitor.get_health_status()
    print(f"\n🏥 System Health:")
    print(f"   Overall Status: {health_status['overall_status']}")
    print(f"   Components: {len(health_status['components'])}")
    print(f"   Last Check: {health_status['last_check']}")
    
    # Get monitoring statistics
    stats = continuous_monitor.get_monitoring_statistics()
    print(f"\n📊 Monitoring Statistics:")
    print(f"   Total Uptime: {stats['total_uptime_seconds']:.0f}s")
    print(f"   Total Sessions: {stats['total_sessions']}")
    print(f"   Metrics Collected: {stats['total_metrics_collected']}")
    print(f"   Alerts Generated: {stats['total_alerts_generated']}")
    print(f"   Analyses Performed: {stats['total_analyses_performed']}")
    
    # Stop monitoring session
    print("\n🛑 Stopping monitoring session...")
    final_report = await continuous_monitor.stop_monitoring()
    
    if final_report:
        print(f"📊 Final Session Report:")
        print(f"   Report ID: {final_report.id}")
        print(f"   Session Duration: {final_report.duration.total_seconds():.0f}s")
        print(f"   Total Analyses: {final_report.total_analyses}")
        print(f"   Total Alerts: {final_report.total_alerts}")
        
        if final_report.initial_metrics and final_report.final_metrics:
            health_change = final_report.final_metrics.health_score - final_report.initial_metrics.health_score
            print(f"   Health Score Change: {health_change:+.3f}")
        
        if final_report.recommendations:
            print(f"   Recommendations:")
            for rec in final_report.recommendations:
                print(f"     - {rec}")
    
    print("✅ Continuous monitoring demonstration complete")
    
    return continuous_monitor


async def demonstrate_complete_monitoring_system():
    """Demonstrate the complete monitoring system working together."""
    print("\n🎯 Complete Monitoring System Demonstration")
    print("=" * 80)
    
    # Initialize codebase
    codebase = Codebase(".")
    
    # Create comprehensive monitoring setup
    monitoring_config = MonitoringConfig(
        analysis_interval=45,  # 45 seconds
        alert_check_interval=20,  # 20 seconds
        enable_alerts=True,
        store_metrics=True,
        storage_path="./complete_monitoring_data"
    )
    
    alert_config = AlertChannelConfig(
        console_format="detailed",
        file_path="./complete_monitoring_alerts.log",
        file_format="json"
    )
    
    # Start continuous monitoring
    continuous_monitor = ContinuousMonitor(codebase, monitoring_config, alert_config)
    
    # Add comprehensive callbacks
    metrics_count = 0
    alerts_count = 0
    health_checks_count = 0
    
    def track_metrics(session):
        nonlocal metrics_count
        if session.status.value == "running":
            metrics_count = session.metrics_collected
    
    def track_health(health_checks):
        nonlocal health_checks_count
        health_checks_count += 1
    
    continuous_monitor.add_session_callback(track_metrics)
    continuous_monitor.add_health_callback(track_health)
    
    # Start the complete system
    print("🚀 Starting complete monitoring system...")
    session_id = await continuous_monitor.start_monitoring("Complete System Demo")
    
    # Run for extended period
    print("⏱️  Running complete system for 3 minutes...")
    print("📊 Monitor the console for real-time updates...")
    
    for minute in range(3):
        await asyncio.sleep(60)
        current_session = continuous_monitor.get_current_session()
        if current_session:
            print(f"\n📈 Minute {minute + 1} Status:")
            print(f"   Metrics: {current_session.metrics_collected}")
            print(f"   Alerts: {current_session.alerts_generated}")
            print(f"   Analyses: {current_session.analyses_performed}")
    
    # Get comprehensive status
    health_status = continuous_monitor.get_health_status()
    stats = continuous_monitor.get_monitoring_statistics()
    
    print(f"\n🎯 Complete System Summary:")
    print(f"   System Health: {health_status['overall_status']}")
    print(f"   Total Uptime: {stats['total_uptime_seconds']:.0f}s")
    print(f"   Health Checks: {health_checks_count}")
    print(f"   Components Monitored: {len(health_status['components'])}")
    
    # Stop the complete system
    print("\n🛑 Stopping complete monitoring system...")
    final_report = await continuous_monitor.stop_monitoring()
    
    if final_report:
        print(f"\n📊 Complete System Final Report:")
        print(f"   Session Duration: {final_report.duration.total_seconds():.0f}s")
        print(f"   Data Points Collected: {final_report.total_analyses}")
        print(f"   Quality Alerts: {final_report.total_alerts}")
        print(f"   System Recommendations: {len(final_report.recommendations)}")
        
        if final_report.recommendations:
            print(f"\n💡 System Recommendations:")
            for i, rec in enumerate(final_report.recommendations, 1):
                print(f"   {i}. {rec}")
    
    print("\n🎉 Complete monitoring system demonstration finished!")
    print("✅ All components working together successfully")
    
    return continuous_monitor


async def main():
    """Main demonstration function."""
    print("🚀 Real-time Code Quality Monitoring System")
    print("=" * 80)
    print("This example demonstrates the comprehensive real-time monitoring")
    print("capabilities including quality monitoring, alerts, dashboards,")
    print("and continuous monitoring with health checks and reporting.")
    print("=" * 80)
    
    try:
        # Run individual demonstrations
        await demonstrate_quality_monitoring()
        await demonstrate_real_time_analysis()
        await demonstrate_alert_system()
        await demonstrate_dashboard_integration()
        await demonstrate_continuous_monitoring()
        
        # Run complete system demonstration
        await demonstrate_complete_monitoring_system()
        
        print("\n🎉 All Demonstrations Complete!")
        print("=" * 80)
        print("✅ Quality Monitoring - Real-time metrics and trends")
        print("✅ Real-time Analysis - File change detection and analysis")
        print("✅ Alert System - Multi-channel alerting with rules")
        print("✅ Dashboard Integration - Live metrics and visualization")
        print("✅ Continuous Monitoring - Session management and health checks")
        print("✅ Complete System - All components working together")
        
        print(f"\n📊 System Capabilities Demonstrated:")
        print(f"   🔍 Real-time quality metric tracking")
        print(f"   📁 File change detection and analysis")
        print(f"   🚨 Intelligent alerting with multiple channels")
        print(f"   📊 Live dashboard with widgets and charts")
        print(f"   🏥 System health monitoring and checks")
        print(f"   📋 Session management and reporting")
        print(f"   🔄 Continuous monitoring with automated insights")
        
        print(f"\n🚀 Ready for Production Deployment!")
        
    except Exception as e:
        print(f"❌ Error in demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

