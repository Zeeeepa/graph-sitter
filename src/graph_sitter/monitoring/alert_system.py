"""
Alert System for Quality Monitoring

Provides comprehensive alerting capabilities including multiple channels,
rule-based alerting, and notification management.
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .quality_monitor import QualityAlert, QualitySeverity, MetricType

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    CONSOLE = "console"
    FILE = "file"


@dataclass
class AlertRule:
    """Alert rule configuration."""
    id: str
    name: str
    description: str
    metric_type: MetricType
    severity_threshold: QualitySeverity
    channels: List[AlertChannel]
    enabled: bool = True
    
    # Conditions
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    change_threshold: Optional[float] = None  # Percentage change
    
    # Rate limiting
    cooldown_minutes: int = 30
    max_alerts_per_hour: int = 5
    
    # Notification settings
    include_suggestions: bool = True
    include_affected_files: bool = True
    custom_message: Optional[str] = None
    
    def matches_alert(self, alert: QualityAlert) -> bool:
        """Check if rule matches alert."""
        if not self.enabled:
            return False
        
        # Check metric type
        if self.metric_type != alert.metric_type:
            return False
        
        # Check severity
        severity_order = {
            QualitySeverity.LOW: 0,
            QualitySeverity.MEDIUM: 1,
            QualitySeverity.HIGH: 2,
            QualitySeverity.CRITICAL: 3
        }
        
        if severity_order[alert.severity] < severity_order[self.severity_threshold]:
            return False
        
        # Check value conditions
        if self.min_value is not None and alert.current_value < self.min_value:
            return False
        
        if self.max_value is not None and alert.current_value > self.max_value:
            return False
        
        return True


@dataclass
class AlertChannelConfig:
    """Configuration for alert channels."""
    
    # Email settings
    email_smtp_server: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: List[str] = field(default_factory=list)
    email_use_tls: bool = True
    
    # Webhook settings
    webhook_urls: List[str] = field(default_factory=list)
    webhook_timeout: int = 30
    webhook_retry_count: int = 3
    
    # Slack settings
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    slack_username: str = "Quality Monitor"
    slack_icon_emoji: str = ":warning:"
    
    # Teams settings
    teams_webhook_url: Optional[str] = None
    
    # File settings
    file_path: Optional[str] = None
    file_format: str = "json"  # json, text
    
    # Console settings
    console_format: str = "detailed"  # simple, detailed


class AlertManager:
    """Manages alert rules and delivery."""
    
    def __init__(self, config: AlertChannelConfig):
        self.config = config
        self.rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.delivery_stats: Dict[str, Dict[str, int]] = {}
        
        # Rate limiting
        self.rule_alert_times: Dict[str, List[datetime]] = {}
        self.rule_last_alert: Dict[str, datetime] = {}
    
    def add_rule(self, rule: AlertRule):
        """Add alert rule."""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove alert rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get alert rule by ID."""
        return self.rules.get(rule_id)
    
    def list_rules(self) -> List[AlertRule]:
        """List all alert rules."""
        return list(self.rules.values())
    
    async def process_alert(self, alert: QualityAlert):
        """Process alert through all matching rules."""
        try:
            matching_rules = []
            
            # Find matching rules
            for rule in self.rules.values():
                if rule.matches_alert(alert):
                    # Check rate limiting
                    if self._can_send_alert(rule):
                        matching_rules.append(rule)
            
            if not matching_rules:
                logger.debug(f"No matching rules for alert: {alert.id}")
                return
            
            # Send alerts
            for rule in matching_rules:
                await self._send_alert(alert, rule)
                self._update_rate_limiting(rule)
            
            # Record in history
            self.alert_history.append({
                'alert': alert.to_dict(),
                'rules_triggered': [r.id for r in matching_rules],
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
    
    def _can_send_alert(self, rule: AlertRule) -> bool:
        """Check if alert can be sent based on rate limiting."""
        now = datetime.now()
        
        # Check cooldown
        if rule.id in self.rule_last_alert:
            time_since_last = now - self.rule_last_alert[rule.id]
            if time_since_last.total_seconds() < rule.cooldown_minutes * 60:
                return False
        
        # Check hourly limit
        if rule.id not in self.rule_alert_times:
            self.rule_alert_times[rule.id] = []
        
        # Clean old timestamps
        cutoff = now - timedelta(hours=1)
        self.rule_alert_times[rule.id] = [
            ts for ts in self.rule_alert_times[rule.id] if ts > cutoff
        ]
        
        # Check limit
        return len(self.rule_alert_times[rule.id]) < rule.max_alerts_per_hour
    
    def _update_rate_limiting(self, rule: AlertRule):
        """Update rate limiting tracking."""
        now = datetime.now()
        self.rule_last_alert[rule.id] = now
        
        if rule.id not in self.rule_alert_times:
            self.rule_alert_times[rule.id] = []
        self.rule_alert_times[rule.id].append(now)
    
    async def _send_alert(self, alert: QualityAlert, rule: AlertRule):
        """Send alert through specified channels."""
        try:
            # Prepare alert message
            message = self._format_alert_message(alert, rule)
            
            # Send through each channel
            for channel in rule.channels:
                try:
                    if channel == AlertChannel.EMAIL:
                        await self._send_email_alert(alert, rule, message)
                    elif channel == AlertChannel.WEBHOOK:
                        await self._send_webhook_alert(alert, rule, message)
                    elif channel == AlertChannel.SLACK:
                        await self._send_slack_alert(alert, rule, message)
                    elif channel == AlertChannel.TEAMS:
                        await self._send_teams_alert(alert, rule, message)
                    elif channel == AlertChannel.CONSOLE:
                        await self._send_console_alert(alert, rule, message)
                    elif channel == AlertChannel.FILE:
                        await self._send_file_alert(alert, rule, message)
                    
                    # Update delivery stats
                    self._update_delivery_stats(channel.value, "success")
                    
                except Exception as e:
                    logger.error(f"Error sending alert via {channel.value}: {e}")
                    self._update_delivery_stats(channel.value, "error")
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def _format_alert_message(self, alert: QualityAlert, rule: AlertRule) -> Dict[str, Any]:
        """Format alert message."""
        # Use custom message if provided
        if rule.custom_message:
            message_text = rule.custom_message.format(
                metric=alert.metric_type.value,
                current_value=alert.current_value,
                threshold=alert.threshold_value,
                severity=alert.severity.value
            )
        else:
            message_text = alert.message
        
        message = {
            'title': f"Quality Alert: {alert.metric_type.value.replace('_', ' ').title()}",
            'text': message_text,
            'severity': alert.severity.value,
            'metric_type': alert.metric_type.value,
            'current_value': alert.current_value,
            'threshold_value': alert.threshold_value,
            'timestamp': alert.timestamp.isoformat(),
            'alert_id': alert.id,
            'rule_name': rule.name
        }
        
        # Add suggestions if enabled
        if rule.include_suggestions and alert.suggested_actions:
            message['suggested_actions'] = alert.suggested_actions
        
        # Add affected files if enabled
        if rule.include_affected_files and alert.affected_files:
            message['affected_files'] = alert.affected_files
        
        return message
    
    async def _send_email_alert(self, alert: QualityAlert, rule: AlertRule, message: Dict[str, Any]):
        """Send email alert."""
        if not all([self.config.email_smtp_server, self.config.email_username, 
                   self.config.email_password, self.config.email_from]):
            logger.warning("Email configuration incomplete")
            return
        
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = ', '.join(self.config.email_to)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {message['title']}"
            
            # Create body
            body = f"""
Quality Alert Notification

Alert: {message['title']}
Severity: {alert.severity.value.upper()}
Metric: {alert.metric_type.value.replace('_', ' ').title()}
Current Value: {alert.current_value:.2f}
Threshold: {alert.threshold_value:.2f}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Description:
{message['text']}
"""
            
            if message.get('suggested_actions'):
                body += "\nSuggested Actions:\n"
                for action in message['suggested_actions']:
                    body += f"- {action}\n"
            
            if message.get('affected_files'):
                body += "\nAffected Files:\n"
                for file_path in message['affected_files']:
                    body += f"- {file_path}\n"
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port)
            if self.config.email_use_tls:
                server.starttls()
            server.login(self.config.email_username, self.config.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for: {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            raise
    
    async def _send_webhook_alert(self, alert: QualityAlert, rule: AlertRule, message: Dict[str, Any]):
        """Send webhook alert."""
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available for webhook alerts")
            return
        
        if not self.config.webhook_urls:
            logger.warning("No webhook URLs configured")
            return
        
        payload = {
            'alert': alert.to_dict(),
            'rule': {
                'id': rule.id,
                'name': rule.name,
                'description': rule.description
            },
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        for url in self.config.webhook_urls:
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.config.webhook_timeout,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                logger.info(f"Webhook alert sent to: {url}")
                
            except Exception as e:
                logger.error(f"Error sending webhook alert to {url}: {e}")
                # Continue with other URLs
    
    async def _send_slack_alert(self, alert: QualityAlert, rule: AlertRule, message: Dict[str, Any]):
        """Send Slack alert."""
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available for Slack alerts")
            return
        
        if not self.config.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
        
        # Color based on severity
        color_map = {
            QualitySeverity.LOW: "#36a64f",      # green
            QualitySeverity.MEDIUM: "#ff9500",   # orange
            QualitySeverity.HIGH: "#ff0000",     # red
            QualitySeverity.CRITICAL: "#8B0000"  # dark red
        }
        
        # Create Slack message
        slack_message = {
            "username": self.config.slack_username,
            "icon_emoji": self.config.slack_icon_emoji,
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#ff0000"),
                    "title": message['title'],
                    "text": message['text'],
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Current Value",
                            "value": f"{alert.current_value:.2f}",
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": f"{alert.threshold_value:.2f}",
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ],
                    "footer": f"Rule: {rule.name}",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }
        
        # Add channel if specified
        if self.config.slack_channel:
            slack_message["channel"] = self.config.slack_channel
        
        try:
            response = requests.post(
                self.config.slack_webhook_url,
                json=slack_message,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Slack alert sent for: {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            raise
    
    async def _send_teams_alert(self, alert: QualityAlert, rule: AlertRule, message: Dict[str, Any]):
        """Send Microsoft Teams alert."""
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available for Teams alerts")
            return
        
        if not self.config.teams_webhook_url:
            logger.warning("Teams webhook URL not configured")
            return
        
        # Color based on severity
        color_map = {
            QualitySeverity.LOW: "Good",
            QualitySeverity.MEDIUM: "Warning", 
            QualitySeverity.HIGH: "Attention",
            QualitySeverity.CRITICAL: "Attention"
        }
        
        teams_message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color_map.get(alert.severity, "Attention"),
            "summary": message['title'],
            "sections": [
                {
                    "activityTitle": message['title'],
                    "activitySubtitle": f"Severity: {alert.severity.value.upper()}",
                    "text": message['text'],
                    "facts": [
                        {
                            "name": "Metric",
                            "value": alert.metric_type.value.replace('_', ' ').title()
                        },
                        {
                            "name": "Current Value",
                            "value": f"{alert.current_value:.2f}"
                        },
                        {
                            "name": "Threshold",
                            "value": f"{alert.threshold_value:.2f}"
                        },
                        {
                            "name": "Time",
                            "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        },
                        {
                            "name": "Rule",
                            "value": rule.name
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                self.config.teams_webhook_url,
                json=teams_message,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Teams alert sent for: {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending Teams alert: {e}")
            raise
    
    async def _send_console_alert(self, alert: QualityAlert, rule: AlertRule, message: Dict[str, Any]):
        """Send console alert."""
        try:
            if self.config.console_format == "simple":
                print(f"[{alert.severity.value.upper()}] {message['title']}: {message['text']}")
            else:  # detailed
                print(f"\n{'='*60}")
                print(f"QUALITY ALERT - {alert.severity.value.upper()}")
                print(f"{'='*60}")
                print(f"Title: {message['title']}")
                print(f"Message: {message['text']}")
                print(f"Metric: {alert.metric_type.value.replace('_', ' ').title()}")
                print(f"Current Value: {alert.current_value:.2f}")
                print(f"Threshold: {alert.threshold_value:.2f}")
                print(f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Rule: {rule.name}")
                
                if message.get('suggested_actions'):
                    print(f"\nSuggested Actions:")
                    for action in message['suggested_actions']:
                        print(f"  - {action}")
                
                print(f"{'='*60}\n")
            
            logger.info(f"Console alert displayed for: {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending console alert: {e}")
            raise
    
    async def _send_file_alert(self, alert: QualityAlert, rule: AlertRule, message: Dict[str, Any]):
        """Send file alert."""
        if not self.config.file_path:
            logger.warning("File path not configured for file alerts")
            return
        
        try:
            file_path = Path(self.config.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            alert_data = {
                'alert': alert.to_dict(),
                'rule': {
                    'id': rule.id,
                    'name': rule.name,
                    'description': rule.description
                },
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.config.file_format == "json":
                # Append to JSON file
                alerts = []
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            alerts = json.load(f)
                    except:
                        alerts = []
                
                alerts.append(alert_data)
                
                with open(file_path, 'w') as f:
                    json.dump(alerts, f, indent=2)
            
            else:  # text format
                with open(file_path, 'a') as f:
                    f.write(f"\n[{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] ")
                    f.write(f"{alert.severity.value.upper()}: {message['title']}\n")
                    f.write(f"  {message['text']}\n")
                    f.write(f"  Rule: {rule.name}\n")
                    f.write(f"  Value: {alert.current_value:.2f} (threshold: {alert.threshold_value:.2f})\n")
            
            logger.info(f"File alert written for: {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending file alert: {e}")
            raise
    
    def _update_delivery_stats(self, channel: str, status: str):
        """Update delivery statistics."""
        if channel not in self.delivery_stats:
            self.delivery_stats[channel] = {"success": 0, "error": 0}
        
        self.delivery_stats[channel][status] += 1
    
    def get_delivery_stats(self) -> Dict[str, Dict[str, int]]:
        """Get delivery statistics."""
        return self.delivery_stats.copy()
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            entry for entry in self.alert_history
            if datetime.fromisoformat(entry['timestamp']) > cutoff
        ]


class AlertSystem:
    """Complete alert system with rules and delivery."""
    
    def __init__(self, config: AlertChannelConfig):
        self.config = config
        self.manager = AlertManager(config)
        self.is_running = False
        
        # Default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alert rules."""
        default_rules = [
            AlertRule(
                id="health_score_critical",
                name="Critical Health Score",
                description="Health score below critical threshold",
                metric_type=MetricType.HEALTH_SCORE,
                severity_threshold=QualitySeverity.CRITICAL,
                channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL],
                max_value=0.5
            ),
            AlertRule(
                id="technical_debt_high",
                name="High Technical Debt",
                description="Technical debt above warning threshold",
                metric_type=MetricType.TECHNICAL_DEBT,
                severity_threshold=QualitySeverity.HIGH,
                channels=[AlertChannel.CONSOLE],
                min_value=0.7
            ),
            AlertRule(
                id="complexity_warning",
                name="High Complexity",
                description="Code complexity above acceptable levels",
                metric_type=MetricType.COMPLEXITY,
                severity_threshold=QualitySeverity.HIGH,
                channels=[AlertChannel.CONSOLE],
                min_value=0.8
            )
        ]
        
        for rule in default_rules:
            self.manager.add_rule(rule)
    
    async def process_alert(self, alert: QualityAlert):
        """Process alert through the system."""
        await self.manager.process_alert(alert)
    
    def add_rule(self, rule: AlertRule):
        """Add alert rule."""
        self.manager.add_rule(rule)
    
    def remove_rule(self, rule_id: str):
        """Remove alert rule."""
        self.manager.remove_rule(rule_id)
    
    def get_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        return self.manager.list_rules()
    
    def get_delivery_stats(self) -> Dict[str, Dict[str, int]]:
        """Get delivery statistics."""
        return self.manager.get_delivery_stats()
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history."""
        return self.manager.get_alert_history(hours)

