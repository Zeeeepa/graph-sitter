"""
System Watcher for Strands Dashboard
Monitors system health and coordinates with all Strands tools
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import psutil
import json

logger = logging.getLogger(__name__)


class SystemWatcher:
    """
    System watcher that monitors health and coordinates with Strands tools
    """
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.is_running = False
        self.monitoring_tasks = []
        self.health_data = {}
        self.alerts = []
        self.watchers = {
            'system_resources': True,
            'strands_services': True,
            'workflow_health': True,
            'mcp_sessions': True,
            'controlflow_agents': True,
            'prefect_flows': True
        }
        
        # Monitoring intervals (in seconds)
        self.intervals = {
            'system_resources': 30,
            'strands_services': 60,
            'workflow_health': 120,
            'mcp_sessions': 90,
            'controlflow_agents': 120,
            'prefect_flows': 180
        }
        
        # Thresholds for alerts
        self.thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'response_time': 5000,  # milliseconds
            'error_rate': 0.05      # 5%
        }
    
    async def start(self):
        """Start the system watcher"""
        try:
            if self.is_running:
                logger.warning("System watcher is already running")
                return
            
            self.is_running = True
            logger.info("Starting system watcher...")
            
            # Start monitoring tasks
            for watcher_name, enabled in self.watchers.items():
                if enabled:
                    interval = self.intervals.get(watcher_name, 60)
                    task = asyncio.create_task(
                        self._run_watcher(watcher_name, interval)
                    )
                    self.monitoring_tasks.append(task)
                    logger.info(f"Started {watcher_name} watcher (interval: {interval}s)")
            
            # Start alert processor
            alert_task = asyncio.create_task(self._process_alerts())
            self.monitoring_tasks.append(alert_task)
            
            logger.info(f"System watcher started with {len(self.monitoring_tasks)} monitoring tasks")
            
        except Exception as e:
            logger.error(f"Failed to start system watcher: {e}")
            raise
    
    async def stop(self):
        """Stop the system watcher"""
        try:
            if not self.is_running:
                return
            
            self.is_running = False
            logger.info("Stopping system watcher...")
            
            # Cancel all monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            if self.monitoring_tasks:
                await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            
            self.monitoring_tasks.clear()
            logger.info("System watcher stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop system watcher: {e}")
    
    async def _run_watcher(self, watcher_name: str, interval: int):
        """Run a specific watcher"""
        try:
            while self.is_running:
                try:
                    if watcher_name == 'system_resources':
                        await self._monitor_system_resources()
                    elif watcher_name == 'strands_services':
                        await self._monitor_strands_services()
                    elif watcher_name == 'workflow_health':
                        await self._monitor_workflow_health()
                    elif watcher_name == 'mcp_sessions':
                        await self._monitor_mcp_sessions()
                    elif watcher_name == 'controlflow_agents':
                        await self._monitor_controlflow_agents()
                    elif watcher_name == 'prefect_flows':
                        await self._monitor_prefect_flows()
                    
                except Exception as e:
                    logger.error(f"Error in {watcher_name} watcher: {e}")
                    await self._create_alert(
                        'watcher_error',
                        f"Error in {watcher_name} watcher: {e}",
                        'error'
                    )
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            logger.info(f"{watcher_name} watcher cancelled")
        except Exception as e:
            logger.error(f"Fatal error in {watcher_name} watcher: {e}")
    
    async def _monitor_system_resources(self):
        """Monitor system resources (CPU, memory, disk)"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network stats
            network = psutil.net_io_counters()
            
            # Get process count
            process_count = len(psutil.pids())
            
            resource_data = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'usage_percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'processes': process_count
            }
            
            self.health_data['system_resources'] = resource_data
            
            # Check thresholds and create alerts
            if cpu_percent > self.thresholds['cpu_usage']:
                await self._create_alert(
                    'high_cpu_usage',
                    f"CPU usage is {cpu_percent:.1f}% (threshold: {self.thresholds['cpu_usage']}%)",
                    'warning'
                )
            
            if memory.percent > self.thresholds['memory_usage']:
                await self._create_alert(
                    'high_memory_usage',
                    f"Memory usage is {memory.percent:.1f}% (threshold: {self.thresholds['memory_usage']}%)",
                    'warning'
                )
            
            disk_usage_percent = (disk.used / disk.total) * 100
            if disk_usage_percent > self.thresholds['disk_usage']:
                await self._create_alert(
                    'high_disk_usage',
                    f"Disk usage is {disk_usage_percent:.1f}% (threshold: {self.thresholds['disk_usage']}%)",
                    'warning'
                )
            
        except Exception as e:
            logger.error(f"Failed to monitor system resources: {e}")
    
    async def _monitor_strands_services(self):
        """Monitor Strands services health"""
        try:
            if not self.orchestrator:
                return
            
            # Get layer health from orchestrator
            layer_health = await self.orchestrator.get_layer_health()
            
            service_data = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': layer_health.get('overall_status', 'unknown'),
                'layers': layer_health.get('layers', {}),
                'unhealthy_layers': layer_health.get('unhealthy_layers', [])
            }
            
            self.health_data['strands_services'] = service_data
            
            # Create alerts for unhealthy services
            if layer_health.get('overall_status') == 'degraded':
                unhealthy = layer_health.get('unhealthy_layers', [])
                await self._create_alert(
                    'strands_services_degraded',
                    f"Strands services degraded. Unhealthy layers: {', '.join(unhealthy)}",
                    'warning'
                )
            elif layer_health.get('overall_status') == 'error':
                await self._create_alert(
                    'strands_services_error',
                    "Strands services experiencing errors",
                    'error'
                )
            
        except Exception as e:
            logger.error(f"Failed to monitor Strands services: {e}")
    
    async def _monitor_workflow_health(self):
        """Monitor workflow health"""
        try:
            if not self.orchestrator or not self.orchestrator.workflow_manager:
                return
            
            # Get workflow status
            workflows = await self.orchestrator.workflow_manager.list_workflows()
            
            workflow_data = {
                'timestamp': datetime.now().isoformat(),
                'total_workflows': len(workflows),
                'active_workflows': len([w for w in workflows if w.get('status') == 'running']),
                'failed_workflows': len([w for w in workflows if w.get('status') == 'failed']),
                'workflows': workflows[:10]  # Keep only recent 10
            }
            
            self.health_data['workflow_health'] = workflow_data
            
            # Alert on failed workflows
            failed_count = workflow_data['failed_workflows']
            if failed_count > 0:
                await self._create_alert(
                    'workflow_failures',
                    f"{failed_count} workflow(s) have failed",
                    'warning' if failed_count < 5 else 'error'
                )
            
        except Exception as e:
            logger.error(f"Failed to monitor workflow health: {e}")
    
    async def _monitor_mcp_sessions(self):
        """Monitor MCP sessions"""
        try:
            if not self.orchestrator or not self.orchestrator.mcp_manager:
                return
            
            # Get MCP session status
            sessions = await self.orchestrator.mcp_manager.list_active_sessions()
            
            mcp_data = {
                'timestamp': datetime.now().isoformat(),
                'total_sessions': len(sessions),
                'active_sessions': len([s for s in sessions if s.get('status') == 'active']),
                'sessions': sessions[:10]  # Keep only recent 10
            }
            
            self.health_data['mcp_sessions'] = mcp_data
            
        except Exception as e:
            logger.error(f"Failed to monitor MCP sessions: {e}")
    
    async def _monitor_controlflow_agents(self):
        """Monitor ControlFlow agents"""
        try:
            if not self.orchestrator or not hasattr(self.orchestrator, 'controlflow_manager'):
                return
            
            # Get ControlFlow agent status
            agents = await self.orchestrator.controlflow_manager.list_agents()
            flows = await self.orchestrator.controlflow_manager.list_flows()
            
            controlflow_data = {
                'timestamp': datetime.now().isoformat(),
                'total_agents': len(agents),
                'total_flows': len(flows),
                'agents': agents,
                'flows': flows[:5]  # Keep only recent 5
            }
            
            self.health_data['controlflow_agents'] = controlflow_data
            
        except Exception as e:
            logger.error(f"Failed to monitor ControlFlow agents: {e}")
    
    async def _monitor_prefect_flows(self):
        """Monitor Prefect flows"""
        try:
            if not self.orchestrator or not hasattr(self.orchestrator, 'prefect_manager'):
                return
            
            # Get Prefect flow status
            flows = await self.orchestrator.prefect_manager.list_flows()
            flow_runs = await self.orchestrator.prefect_manager.list_flow_runs()
            
            # Count runs by status
            running_runs = len([r for r in flow_runs if r.get('status') == 'running'])
            failed_runs = len([r for r in flow_runs if r.get('status') == 'failed'])
            completed_runs = len([r for r in flow_runs if r.get('status') == 'completed'])
            
            prefect_data = {
                'timestamp': datetime.now().isoformat(),
                'total_flows': len(flows),
                'total_runs': len(flow_runs),
                'running_runs': running_runs,
                'failed_runs': failed_runs,
                'completed_runs': completed_runs,
                'flows': flows,
                'recent_runs': flow_runs[:10]  # Keep only recent 10
            }
            
            self.health_data['prefect_flows'] = prefect_data
            
            # Alert on failed flows
            if failed_runs > 0:
                await self._create_alert(
                    'prefect_flow_failures',
                    f"{failed_runs} Prefect flow run(s) have failed",
                    'warning' if failed_runs < 3 else 'error'
                )
            
        except Exception as e:
            logger.error(f"Failed to monitor Prefect flows: {e}")
    
    async def _create_alert(self, alert_type: str, message: str, severity: str):
        """Create a system alert"""
        try:
            alert = {
                'id': f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                'type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False
            }
            
            self.alerts.append(alert)
            
            # Keep only recent 100 alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
            logger.warning(f"System alert [{severity.upper()}]: {message}")
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    async def _process_alerts(self):
        """Process and manage alerts"""
        try:
            while self.is_running:
                # Clean up old alerts (older than 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                self.alerts = [
                    alert for alert in self.alerts
                    if datetime.fromisoformat(alert['timestamp']) > cutoff_time
                ]
                
                await asyncio.sleep(300)  # Process every 5 minutes
                
        except asyncio.CancelledError:
            logger.info("Alert processor cancelled")
        except Exception as e:
            logger.error(f"Error in alert processor: {e}")
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'healthy',
                'components': {},
                'alerts': {
                    'total': len(self.alerts),
                    'unacknowledged': len([a for a in self.alerts if not a['acknowledged']]),
                    'by_severity': {}
                }
            }
            
            # Count alerts by severity
            for alert in self.alerts:
                severity = alert['severity']
                summary['alerts']['by_severity'][severity] = summary['alerts']['by_severity'].get(severity, 0) + 1
            
            # Determine overall status
            error_alerts = summary['alerts']['by_severity'].get('error', 0)
            warning_alerts = summary['alerts']['by_severity'].get('warning', 0)
            
            if error_alerts > 0:
                summary['overall_status'] = 'error'
            elif warning_alerts > 0:
                summary['overall_status'] = 'warning'
            
            # Add component status
            for component, data in self.health_data.items():
                summary['components'][component] = {
                    'status': 'healthy',
                    'last_check': data.get('timestamp', 'unknown')
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get health summary: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed health data"""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'health_data': self.health_data,
                'alerts': self.alerts[-20:],  # Recent 20 alerts
                'watchers': self.watchers,
                'thresholds': self.thresholds
            }
        except Exception as e:
            logger.error(f"Failed to get detailed health: {e}")
            return {'error': str(e)}
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            for alert in self.alerts:
                if alert['id'] == alert_id:
                    alert['acknowledged'] = True
                    alert['acknowledged_at'] = datetime.now().isoformat()
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False

