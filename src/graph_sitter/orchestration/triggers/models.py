"""
Trigger Models

Data models for automated trigger system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4


class TriggerType(Enum):
    """Types of triggers"""
    EVENT = "event"           # Triggered by specific events
    SCHEDULE = "schedule"     # Triggered by time schedule
    CONDITION = "condition"   # Triggered by condition evaluation
    WEBHOOK = "webhook"       # Triggered by webhook
    MANUAL = "manual"         # Manually triggered


class TriggerStatus(Enum):
    """Status of triggers"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"
    ERROR = "error"


class ConditionOperator(Enum):
    """Operators for trigger conditions"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    REGEX_MATCH = "regex_match"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


@dataclass
class TriggerCondition:
    """Condition for trigger evaluation"""
    field: str                                    # Field to evaluate (e.g., 'event.type', 'event.data.repository')
    operator: ConditionOperator                   # Comparison operator
    value: Union[str, int, float, List[Any]]     # Value to compare against
    case_sensitive: bool = True                   # For string comparisons
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate this condition against a context"""
        try:
            # Get the field value from context
            field_value = self._get_field_value(context, self.field)
            
            if field_value is None:
                return False
            
            # Apply operator
            if self.operator == ConditionOperator.EQUALS:
                return self._compare_values(field_value, self.value, self.case_sensitive)
            elif self.operator == ConditionOperator.NOT_EQUALS:
                return not self._compare_values(field_value, self.value, self.case_sensitive)
            elif self.operator == ConditionOperator.CONTAINS:
                return self._contains_check(field_value, self.value, self.case_sensitive)
            elif self.operator == ConditionOperator.NOT_CONTAINS:
                return not self._contains_check(field_value, self.value, self.case_sensitive)
            elif self.operator == ConditionOperator.GREATER_THAN:
                return float(field_value) > float(self.value)
            elif self.operator == ConditionOperator.LESS_THAN:
                return float(field_value) < float(self.value)
            elif self.operator == ConditionOperator.REGEX_MATCH:
                import re
                pattern = self.value if self.case_sensitive else f"(?i){self.value}"
                return bool(re.search(pattern, str(field_value)))
            elif self.operator == ConditionOperator.IN_LIST:
                return field_value in self.value
            elif self.operator == ConditionOperator.NOT_IN_LIST:
                return field_value not in self.value
            
            return False
            
        except Exception:
            return False
    
    def _get_field_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """Get a nested field value from context"""
        parts = field_path.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return value
    
    def _compare_values(self, field_value: Any, compare_value: Any, case_sensitive: bool) -> bool:
        """Compare two values with case sensitivity option"""
        if isinstance(field_value, str) and isinstance(compare_value, str) and not case_sensitive:
            return field_value.lower() == compare_value.lower()
        return field_value == compare_value
    
    def _contains_check(self, field_value: Any, search_value: Any, case_sensitive: bool) -> bool:
        """Check if field_value contains search_value"""
        field_str = str(field_value)
        search_str = str(search_value)
        
        if not case_sensitive:
            field_str = field_str.lower()
            search_str = search_str.lower()
        
        return search_str in field_str


@dataclass
class TriggerAction:
    """Action to execute when trigger fires"""
    action_type: str                              # Type of action (workflow, webhook, notification)
    parameters: Dict[str, Any] = field(default_factory=dict)
    delay: Optional[timedelta] = None             # Delay before execution
    retry_count: int = 0                          # Number of retries on failure
    max_retries: int = 3                          # Maximum retry attempts
    
    # Execution state
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    last_error: Optional[str] = None


@dataclass
class Trigger:
    """Complete trigger definition"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    
    # Trigger configuration
    trigger_type: TriggerType = TriggerType.EVENT
    event_types: List[str] = field(default_factory=list)      # Event types to listen for
    platforms: List[str] = field(default_factory=list)        # Platforms to monitor
    conditions: List[TriggerCondition] = field(default_factory=list)
    
    # Actions
    actions: List[TriggerAction] = field(default_factory=list)
    
    # Scheduling (for SCHEDULE type triggers)
    cron_expression: Optional[str] = None
    
    # Rate limiting
    cooldown: Optional[timedelta] = None          # Minimum time between executions
    max_executions_per_hour: Optional[int] = None
    max_executions_per_day: Optional[int] = None
    
    # State
    status: TriggerStatus = TriggerStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    execution_count: int = 0
    
    # Metadata
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """Check if this trigger should fire for the given context"""
        if self.status != TriggerStatus.ACTIVE:
            return False
        
        # Check cooldown
        if self.cooldown and self.last_triggered:
            if datetime.now() - self.last_triggered < self.cooldown:
                return False
        
        # Check rate limits
        if not self._check_rate_limits():
            return False
        
        # Check event type (for EVENT triggers)
        if self.trigger_type == TriggerType.EVENT:
            event_type = context.get('event', {}).get('event_type')
            if self.event_types and event_type not in self.event_types:
                return False
            
            # Check platform
            platform = context.get('platform')
            if self.platforms and platform not in self.platforms:
                return False
        
        # Evaluate all conditions
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False
        
        return True
    
    def _check_rate_limits(self) -> bool:
        """Check if rate limits allow execution"""
        now = datetime.now()
        
        # Check hourly limit
        if self.max_executions_per_hour:
            hour_ago = now - timedelta(hours=1)
            # This would need to be implemented with execution history
            # For now, simplified check
            pass
        
        # Check daily limit
        if self.max_executions_per_day:
            day_ago = now - timedelta(days=1)
            # This would need to be implemented with execution history
            # For now, simplified check
            pass
        
        return True
    
    def add_condition(self, condition: TriggerCondition) -> 'Trigger':
        """Add a condition to this trigger"""
        self.conditions.append(condition)
        self.updated_at = datetime.now()
        return self
    
    def add_action(self, action: TriggerAction) -> 'Trigger':
        """Add an action to this trigger"""
        self.actions.append(action)
        self.updated_at = datetime.now()
        return self


# Common trigger templates
COMMON_TRIGGERS = {
    'github_pr_review': Trigger(
        id='github_pr_review',
        name='GitHub PR Review Trigger',
        description='Trigger code review workflow when PR is opened',
        trigger_type=TriggerType.EVENT,
        event_types=['github.pr.opened'],
        platforms=['github'],
        conditions=[
            TriggerCondition(
                field='event.data.draft',
                operator=ConditionOperator.EQUALS,
                value=False
            )
        ],
        actions=[
            TriggerAction(
                action_type='workflow',
                parameters={
                    'workflow_id': 'github_pr_review',
                    'pr_number': '${event.data.number}',
                    'repository': '${event.data.repository}'
                }
            )
        ]
    ),
    
    'linear_issue_sync': Trigger(
        id='linear_issue_sync',
        name='Linear Issue Sync Trigger',
        description='Sync GitHub issues to Linear when created',
        trigger_type=TriggerType.EVENT,
        event_types=['github.issue.opened'],
        platforms=['github'],
        conditions=[
            TriggerCondition(
                field='event.data.labels',
                operator=ConditionOperator.CONTAINS,
                value='sync-to-linear'
            )
        ],
        actions=[
            TriggerAction(
                action_type='workflow',
                parameters={
                    'workflow_id': 'linear_issue_sync',
                    'issue_number': '${event.data.number}',
                    'repository': '${event.data.repository}'
                }
            )
        ]
    ),
    
    'daily_report': Trigger(
        id='daily_report',
        name='Daily Activity Report',
        description='Generate daily activity report',
        trigger_type=TriggerType.SCHEDULE,
        cron_expression='0 9 * * *',  # 9 AM daily
        actions=[
            TriggerAction(
                action_type='workflow',
                parameters={
                    'workflow_id': 'generate_daily_report'
                }
            )
        ]
    ),
    
    'high_priority_alert': Trigger(
        id='high_priority_alert',
        name='High Priority Issue Alert',
        description='Alert on high priority Linear issues',
        trigger_type=TriggerType.EVENT,
        event_types=['linear.issue.created', 'linear.issue.updated'],
        platforms=['linear'],
        conditions=[
            TriggerCondition(
                field='event.data.priority',
                operator=ConditionOperator.GREATER_THAN,
                value=3
            )
        ],
        actions=[
            TriggerAction(
                action_type='notification',
                parameters={
                    'type': 'slack',
                    'channel': '#alerts',
                    'message': 'High priority issue: ${event.data.title}'
                }
            )
        ],
        cooldown=timedelta(minutes=5)  # Prevent spam
    )
}

