"""Analytics engine for team communication insights and productivity metrics."""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from enum import Enum
import json

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of metrics to track."""
    COMMUNICATION_FREQUENCY = "communication_frequency"
    RESPONSE_TIME = "response_time"
    COLLABORATION_PATTERNS = "collaboration_patterns"
    WORKFLOW_EFFICIENCY = "workflow_efficiency"
    TEAM_ENGAGEMENT = "team_engagement"
    NOTIFICATION_EFFECTIVENESS = "notification_effectiveness"


class InsightType(Enum):
    """Types of insights to generate."""
    BOTTLENECK_IDENTIFICATION = "bottleneck_identification"
    PRODUCTIVITY_TRENDS = "productivity_trends"
    COMMUNICATION_GAPS = "communication_gaps"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    TEAM_HEALTH = "team_health"
    PREDICTIVE_ALERTS = "predictive_alerts"


@dataclass
class CommunicationEvent:
    """Represents a communication event for analytics."""
    
    timestamp: datetime
    event_type: str
    user_id: str
    channel_id: Optional[str] = None
    thread_ts: Optional[str] = None
    response_to: Optional[str] = None
    platform: str = "slack"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowEvent:
    """Represents a workflow event for analytics."""
    
    timestamp: datetime
    workflow_id: str
    workflow_type: str
    step: str
    user_id: str
    action: str  # initiated, approved, rejected, completed, etc.
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamMetrics:
    """Team-level metrics for a specific time period."""
    
    period_start: datetime
    period_end: datetime
    
    # Communication metrics
    total_messages: int = 0
    unique_participants: int = 0
    avg_response_time_minutes: float = 0.0
    peak_activity_hour: int = 12
    
    # Workflow metrics
    workflows_initiated: int = 0
    workflows_completed: int = 0
    avg_workflow_duration_hours: float = 0.0
    workflow_success_rate: float = 0.0
    
    # Collaboration metrics
    cross_team_interactions: int = 0
    knowledge_sharing_events: int = 0
    mentoring_interactions: int = 0
    
    # Productivity indicators
    blocked_workflows: int = 0
    escalated_issues: int = 0
    automation_usage: int = 0


@dataclass
class UserMetrics:
    """User-level metrics for a specific time period."""
    
    user_id: str
    period_start: datetime
    period_end: datetime
    
    # Activity metrics
    messages_sent: int = 0
    workflows_participated: int = 0
    avg_response_time_minutes: float = 0.0
    
    # Engagement metrics
    reactions_given: int = 0
    threads_started: int = 0
    help_requests: int = 0
    help_provided: int = 0
    
    # Productivity metrics
    tasks_completed: int = 0
    reviews_completed: int = 0
    approvals_given: int = 0


@dataclass
class Insight:
    """Represents an analytical insight."""
    
    insight_type: InsightType
    title: str
    description: str
    severity: str  # low, medium, high, critical
    confidence: float  # 0.0 to 1.0
    recommendations: List[str] = field(default_factory=list)
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class AnalyticsEngine:
    """Engine for analyzing team communication and generating insights."""
    
    def __init__(self, config):
        self.config = config
        self._communication_events: List[CommunicationEvent] = []
        self._workflow_events: List[WorkflowEvent] = []
        self._user_metrics_cache: Dict[str, UserMetrics] = {}
        self._team_metrics_cache: Dict[str, TeamMetrics] = {}
        self._insights_cache: List[Insight] = []
        
        # Analytics configuration
        self.retention_days = config.analytics_retention_days
        self.enable_team_insights = config.enable_team_insights
        self.enable_productivity_metrics = config.enable_productivity_metrics
        
        logger.info("Analytics engine initialized for team communication insights")
    
    async def record_notification(
        self, 
        event_data: Dict[str, Any], 
        context: Any, 
        responses: List[Dict[str, Any]]
    ):
        """Record a notification event for analytics."""
        try:
            # Create communication event
            comm_event = CommunicationEvent(
                timestamp=datetime.now(),
                event_type=context.event_type,
                user_id=event_data.get("user_id", "system"),
                channel_id=context.target_channels[0] if context.target_channels else None,
                platform=context.source_platform,
                metadata={
                    "priority": context.priority,
                    "target_channels": context.target_channels,
                    "target_users": context.target_users,
                    "correlation_id": context.correlation_id,
                    "responses": len(responses)
                }
            )
            
            self._communication_events.append(comm_event)
            await self._cleanup_old_events()
            
            logger.debug(f"Recorded notification event: {context.event_type}")
            
        except Exception as e:
            logger.exception(f"Failed to record notification event: {e}")
    
    async def record_workflow_initiation(self, workflow_context: Any):
        """Record workflow initiation for analytics."""
        try:
            workflow_event = WorkflowEvent(
                timestamp=datetime.now(),
                workflow_id=workflow_context.workflow_id,
                workflow_type=workflow_context.workflow_type,
                step=workflow_context.step,
                user_id=workflow_context.data.get("initiator", "unknown"),
                action="initiated",
                metadata={
                    "approvers": workflow_context.approvers,
                    "deadline": workflow_context.deadline.isoformat() if workflow_context.deadline else None,
                    "data": workflow_context.data
                }
            )
            
            self._workflow_events.append(workflow_event)
            await self._cleanup_old_events()
            
            logger.debug(f"Recorded workflow initiation: {workflow_context.workflow_id}")
            
        except Exception as e:
            logger.exception(f"Failed to record workflow initiation: {e}")
    
    async def record_workflow_action(
        self, 
        workflow_id: str, 
        user_id: str, 
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a workflow action (approval, rejection, etc.)."""
        try:
            # Find the original workflow
            original_workflow = None
            for event in reversed(self._workflow_events):
                if event.workflow_id == workflow_id and event.action == "initiated":
                    original_workflow = event
                    break
            
            if not original_workflow:
                logger.warning(f"Original workflow not found for {workflow_id}")
                return
            
            # Calculate duration if completing
            duration = None
            if action in ["completed", "approved", "rejected"]:
                duration = (datetime.now() - original_workflow.timestamp).total_seconds()
            
            workflow_event = WorkflowEvent(
                timestamp=datetime.now(),
                workflow_id=workflow_id,
                workflow_type=original_workflow.workflow_type,
                step=action,
                user_id=user_id,
                action=action,
                duration_seconds=duration,
                metadata=metadata or {}
            )
            
            self._workflow_events.append(workflow_event)
            
            logger.debug(f"Recorded workflow action: {workflow_id} - {action}")
            
        except Exception as e:
            logger.exception(f"Failed to record workflow action: {e}")
    
    async def analyze_communication_patterns(self, timeframe: str) -> Dict[str, Any]:
        """Analyze team communication patterns for the specified timeframe."""
        try:
            # Parse timeframe
            start_time, end_time = self._parse_timeframe(timeframe)
            
            # Filter events to timeframe
            filtered_events = [
                event for event in self._communication_events
                if start_time <= event.timestamp <= end_time
            ]
            
            # Generate team metrics
            team_metrics = await self._calculate_team_metrics(filtered_events, start_time, end_time)
            
            # Generate user metrics
            user_metrics = await self._calculate_user_metrics(filtered_events, start_time, end_time)
            
            # Generate insights
            insights = await self._generate_communication_insights(team_metrics, user_metrics)
            
            # Create analysis report
            analysis = {
                "timeframe": timeframe,
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "team_metrics": self._serialize_team_metrics(team_metrics),
                "user_metrics": {
                    user_id: self._serialize_user_metrics(metrics)
                    for user_id, metrics in user_metrics.items()
                },
                "insights": [self._serialize_insight(insight) for insight in insights],
                "summary": await self._generate_summary(team_metrics, insights)
            }
            
            logger.info(f"Generated communication analysis for {timeframe}")
            return analysis
            
        except Exception as e:
            logger.exception(f"Failed to analyze communication patterns: {e}")
            return {"error": str(e)}
    
    async def generate_productivity_insights(self, timeframe: str) -> Dict[str, Any]:
        """Generate productivity insights for the specified timeframe."""
        if not self.enable_productivity_metrics:
            return {"error": "Productivity metrics not enabled"}
        
        try:
            start_time, end_time = self._parse_timeframe(timeframe)
            
            # Filter workflow events
            workflow_events = [
                event for event in self._workflow_events
                if start_time <= event.timestamp <= end_time
            ]
            
            # Analyze workflow efficiency
            workflow_analysis = await self._analyze_workflow_efficiency(workflow_events)
            
            # Identify bottlenecks
            bottlenecks = await self._identify_bottlenecks(workflow_events)
            
            # Generate productivity recommendations
            recommendations = await self._generate_productivity_recommendations(
                workflow_analysis, bottlenecks
            )
            
            return {
                "timeframe": timeframe,
                "workflow_analysis": workflow_analysis,
                "bottlenecks": bottlenecks,
                "recommendations": recommendations,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception(f"Failed to generate productivity insights: {e}")
            return {"error": str(e)}
    
    async def generate_team_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive team health report."""
        if not self.enable_team_insights:
            return {"error": "Team insights not enabled"}
        
        try:
            # Analyze last 30 days
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            
            # Get communication events
            comm_events = [
                event for event in self._communication_events
                if start_time <= event.timestamp <= end_time
            ]
            
            # Get workflow events
            workflow_events = [
                event for event in self._workflow_events
                if start_time <= event.timestamp <= end_time
            ]
            
            # Calculate health metrics
            health_metrics = {
                "communication_health": await self._assess_communication_health(comm_events),
                "workflow_health": await self._assess_workflow_health(workflow_events),
                "collaboration_health": await self._assess_collaboration_health(comm_events),
                "overall_score": 0.0
            }
            
            # Calculate overall health score
            health_metrics["overall_score"] = (
                health_metrics["communication_health"]["score"] * 0.4 +
                health_metrics["workflow_health"]["score"] * 0.4 +
                health_metrics["collaboration_health"]["score"] * 0.2
            )
            
            # Generate recommendations
            recommendations = await self._generate_health_recommendations(health_metrics)
            
            return {
                "report_date": datetime.now().isoformat(),
                "period_days": 30,
                "health_metrics": health_metrics,
                "recommendations": recommendations,
                "trend_analysis": await self._analyze_health_trends()
            }
            
        except Exception as e:
            logger.exception(f"Failed to generate team health report: {e}")
            return {"error": str(e)}
    
    def _parse_timeframe(self, timeframe: str) -> Tuple[datetime, datetime]:
        """Parse timeframe string into start and end datetime."""
        end_time = datetime.now()
        
        if timeframe == "day":
            start_time = end_time - timedelta(days=1)
        elif timeframe == "week":
            start_time = end_time - timedelta(weeks=1)
        elif timeframe == "month":
            start_time = end_time - timedelta(days=30)
        elif timeframe == "quarter":
            start_time = end_time - timedelta(days=90)
        else:
            # Default to week
            start_time = end_time - timedelta(weeks=1)
        
        return start_time, end_time
    
    async def _calculate_team_metrics(
        self, 
        events: List[CommunicationEvent], 
        start_time: datetime, 
        end_time: datetime
    ) -> TeamMetrics:
        """Calculate team-level metrics from communication events."""
        metrics = TeamMetrics(period_start=start_time, period_end=end_time)
        
        if not events:
            return metrics
        
        # Basic counts
        metrics.total_messages = len(events)
        metrics.unique_participants = len(set(event.user_id for event in events))
        
        # Response time analysis
        response_times = []
        for event in events:
            if event.response_to:
                # Find original message
                for orig_event in events:
                    if orig_event.metadata.get("message_ts") == event.response_to:
                        response_time = (event.timestamp - orig_event.timestamp).total_seconds() / 60
                        response_times.append(response_time)
                        break
        
        if response_times:
            metrics.avg_response_time_minutes = sum(response_times) / len(response_times)
        
        # Peak activity analysis
        hour_counts = Counter(event.timestamp.hour for event in events)
        if hour_counts:
            metrics.peak_activity_hour = hour_counts.most_common(1)[0][0]
        
        return metrics
    
    async def _calculate_user_metrics(
        self, 
        events: List[CommunicationEvent], 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, UserMetrics]:
        """Calculate user-level metrics from communication events."""
        user_metrics = {}
        
        # Group events by user
        user_events = defaultdict(list)
        for event in events:
            user_events[event.user_id].append(event)
        
        for user_id, user_event_list in user_events.items():
            metrics = UserMetrics(
                user_id=user_id,
                period_start=start_time,
                period_end=end_time
            )
            
            metrics.messages_sent = len(user_event_list)
            
            # Calculate response times for this user
            response_times = []
            for event in user_event_list:
                if event.response_to:
                    # Find original message
                    for orig_event in events:
                        if orig_event.metadata.get("message_ts") == event.response_to:
                            response_time = (event.timestamp - orig_event.timestamp).total_seconds() / 60
                            response_times.append(response_time)
                            break
            
            if response_times:
                metrics.avg_response_time_minutes = sum(response_times) / len(response_times)
            
            user_metrics[user_id] = metrics
        
        return user_metrics
    
    async def _generate_communication_insights(
        self, 
        team_metrics: TeamMetrics, 
        user_metrics: Dict[str, UserMetrics]
    ) -> List[Insight]:
        """Generate insights from communication metrics."""
        insights = []
        
        # Check for low engagement
        if team_metrics.unique_participants < 5:
            insights.append(Insight(
                insight_type=InsightType.TEAM_HEALTH,
                title="Low Team Engagement",
                description=f"Only {team_metrics.unique_participants} team members participated in communication.",
                severity="medium",
                confidence=0.8,
                recommendations=[
                    "Encourage more team members to participate in discussions",
                    "Consider team building activities",
                    "Review communication channels and accessibility"
                ]
            ))
        
        # Check for slow response times
        if team_metrics.avg_response_time_minutes > 120:  # 2 hours
            insights.append(Insight(
                insight_type=InsightType.COMMUNICATION_GAPS,
                title="Slow Response Times",
                description=f"Average response time is {team_metrics.avg_response_time_minutes:.1f} minutes.",
                severity="medium",
                confidence=0.7,
                recommendations=[
                    "Set expectations for response times",
                    "Consider notification settings optimization",
                    "Review urgent vs non-urgent communication channels"
                ]
            ))
        
        # Check for communication imbalances
        if user_metrics:
            message_counts = [metrics.messages_sent for metrics in user_metrics.values()]
            if message_counts:
                max_messages = max(message_counts)
                min_messages = min(message_counts)
                
                if max_messages > min_messages * 5:  # 5x imbalance
                    insights.append(Insight(
                        insight_type=InsightType.COLLABORATION_PATTERNS,
                        title="Communication Imbalance",
                        description="Some team members are significantly more active than others.",
                        severity="low",
                        confidence=0.6,
                        recommendations=[
                            "Encourage quieter team members to participate",
                            "Consider rotating meeting facilitators",
                            "Review if some members are overwhelmed"
                        ]
                    ))
        
        return insights
    
    async def _analyze_workflow_efficiency(self, workflow_events: List[WorkflowEvent]) -> Dict[str, Any]:
        """Analyze workflow efficiency from events."""
        if not workflow_events:
            return {"total_workflows": 0}
        
        # Group by workflow type
        workflow_types = defaultdict(list)
        for event in workflow_events:
            workflow_types[event.workflow_type].append(event)
        
        analysis = {"total_workflows": len(set(event.workflow_id for event in workflow_events))}
        
        for workflow_type, events in workflow_types.items():
            # Calculate completion rate
            initiated = len([e for e in events if e.action == "initiated"])
            completed = len([e for e in events if e.action in ["completed", "approved"]])
            
            completion_rate = completed / initiated if initiated > 0 else 0
            
            # Calculate average duration
            durations = [e.duration_seconds for e in events if e.duration_seconds is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            analysis[workflow_type] = {
                "initiated": initiated,
                "completed": completed,
                "completion_rate": completion_rate,
                "avg_duration_hours": avg_duration / 3600 if avg_duration else 0
            }
        
        return analysis
    
    async def _identify_bottlenecks(self, workflow_events: List[WorkflowEvent]) -> List[Dict[str, Any]]:
        """Identify workflow bottlenecks."""
        bottlenecks = []
        
        # Group by workflow ID to analyze individual workflows
        workflows = defaultdict(list)
        for event in workflow_events:
            workflows[event.workflow_id].append(event)
        
        # Analyze each workflow for bottlenecks
        for workflow_id, events in workflows.items():
            events.sort(key=lambda x: x.timestamp)
            
            # Look for long delays between steps
            for i in range(len(events) - 1):
                current_event = events[i]
                next_event = events[i + 1]
                
                delay_hours = (next_event.timestamp - current_event.timestamp).total_seconds() / 3600
                
                if delay_hours > 24:  # More than 24 hours delay
                    bottlenecks.append({
                        "workflow_id": workflow_id,
                        "workflow_type": current_event.workflow_type,
                        "bottleneck_step": current_event.step,
                        "delay_hours": delay_hours,
                        "severity": "high" if delay_hours > 72 else "medium"
                    })
        
        return bottlenecks
    
    async def _generate_productivity_recommendations(
        self, 
        workflow_analysis: Dict[str, Any], 
        bottlenecks: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate productivity improvement recommendations."""
        recommendations = []
        
        # Analyze completion rates
        for workflow_type, data in workflow_analysis.items():
            if isinstance(data, dict) and "completion_rate" in data:
                if data["completion_rate"] < 0.8:
                    recommendations.append(
                        f"Improve {workflow_type} completion rate (currently {data['completion_rate']:.1%})"
                    )
        
        # Analyze bottlenecks
        if bottlenecks:
            bottleneck_steps = Counter(b["bottleneck_step"] for b in bottlenecks)
            most_common_bottleneck = bottleneck_steps.most_common(1)[0][0]
            recommendations.append(
                f"Address bottleneck in '{most_common_bottleneck}' step - appears in {bottleneck_steps[most_common_bottleneck]} workflows"
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append("Workflow efficiency looks good! Consider automation opportunities.")
        
        return recommendations
    
    async def _assess_communication_health(self, events: List[CommunicationEvent]) -> Dict[str, Any]:
        """Assess communication health metrics."""
        if not events:
            return {"score": 0.0, "status": "no_data"}
        
        # Calculate various health indicators
        unique_users = len(set(event.user_id for event in events))
        daily_activity = len(events) / 30  # Average per day over 30 days
        
        # Score based on activity and participation
        activity_score = min(daily_activity / 10, 1.0)  # Target 10 messages per day
        participation_score = min(unique_users / 10, 1.0)  # Target 10 active users
        
        overall_score = (activity_score + participation_score) / 2
        
        return {
            "score": overall_score,
            "status": "healthy" if overall_score > 0.7 else "needs_attention",
            "metrics": {
                "daily_activity": daily_activity,
                "unique_participants": unique_users,
                "activity_score": activity_score,
                "participation_score": participation_score
            }
        }
    
    async def _assess_workflow_health(self, events: List[WorkflowEvent]) -> Dict[str, Any]:
        """Assess workflow health metrics."""
        if not events:
            return {"score": 0.0, "status": "no_data"}
        
        # Calculate workflow completion rate
        initiated = len([e for e in events if e.action == "initiated"])
        completed = len([e for e in events if e.action in ["completed", "approved"]])
        
        completion_rate = completed / initiated if initiated > 0 else 0
        
        # Calculate average workflow duration
        durations = [e.duration_seconds for e in events if e.duration_seconds is not None]
        avg_duration_hours = sum(durations) / len(durations) / 3600 if durations else 0
        
        # Score based on completion rate and speed
        completion_score = completion_rate
        speed_score = max(0, 1 - (avg_duration_hours / 48))  # Target 48 hours max
        
        overall_score = (completion_score + speed_score) / 2
        
        return {
            "score": overall_score,
            "status": "healthy" if overall_score > 0.7 else "needs_attention",
            "metrics": {
                "completion_rate": completion_rate,
                "avg_duration_hours": avg_duration_hours,
                "total_workflows": initiated
            }
        }
    
    async def _assess_collaboration_health(self, events: List[CommunicationEvent]) -> Dict[str, Any]:
        """Assess collaboration health metrics."""
        if not events:
            return {"score": 0.0, "status": "no_data"}
        
        # Analyze cross-user interactions
        user_interactions = defaultdict(set)
        for event in events:
            if event.response_to:
                # This is a response, find original author
                for orig_event in events:
                    if orig_event.metadata.get("message_ts") == event.response_to:
                        user_interactions[event.user_id].add(orig_event.user_id)
                        break
        
        # Calculate collaboration metrics
        total_users = len(set(event.user_id for event in events))
        collaborative_users = len([u for u, interactions in user_interactions.items() if len(interactions) > 1])
        
        collaboration_rate = collaborative_users / total_users if total_users > 0 else 0
        
        return {
            "score": collaboration_rate,
            "status": "healthy" if collaboration_rate > 0.6 else "needs_attention",
            "metrics": {
                "collaboration_rate": collaboration_rate,
                "collaborative_users": collaborative_users,
                "total_users": total_users
            }
        }
    
    async def _generate_health_recommendations(self, health_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on health metrics."""
        recommendations = []
        
        # Communication health recommendations
        comm_health = health_metrics["communication_health"]
        if comm_health["score"] < 0.7:
            recommendations.append("Increase team communication frequency and participation")
        
        # Workflow health recommendations
        workflow_health = health_metrics["workflow_health"]
        if workflow_health["score"] < 0.7:
            recommendations.append("Improve workflow completion rates and reduce processing time")
        
        # Collaboration health recommendations
        collab_health = health_metrics["collaboration_health"]
        if collab_health["score"] < 0.6:
            recommendations.append("Encourage more cross-team collaboration and knowledge sharing")
        
        # Overall recommendations
        if health_metrics["overall_score"] > 0.8:
            recommendations.append("Team health is excellent! Consider sharing best practices with other teams.")
        
        return recommendations
    
    async def _analyze_health_trends(self) -> Dict[str, Any]:
        """Analyze health trends over time."""
        # This would analyze trends over multiple time periods
        # For now, return placeholder data
        return {
            "trend": "stable",
            "change_percentage": 0.0,
            "recommendation": "Continue current practices"
        }
    
    async def _generate_summary(self, team_metrics: TeamMetrics, insights: List[Insight]) -> Dict[str, Any]:
        """Generate a summary of the analysis."""
        return {
            "total_messages": team_metrics.total_messages,
            "active_participants": team_metrics.unique_participants,
            "avg_response_time_hours": team_metrics.avg_response_time_minutes / 60,
            "insights_count": len(insights),
            "high_priority_insights": len([i for i in insights if i.severity in ["high", "critical"]])
        }
    
    def _serialize_team_metrics(self, metrics: TeamMetrics) -> Dict[str, Any]:
        """Serialize team metrics to dict."""
        return {
            "period_start": metrics.period_start.isoformat(),
            "period_end": metrics.period_end.isoformat(),
            "total_messages": metrics.total_messages,
            "unique_participants": metrics.unique_participants,
            "avg_response_time_minutes": metrics.avg_response_time_minutes,
            "peak_activity_hour": metrics.peak_activity_hour
        }
    
    def _serialize_user_metrics(self, metrics: UserMetrics) -> Dict[str, Any]:
        """Serialize user metrics to dict."""
        return {
            "messages_sent": metrics.messages_sent,
            "avg_response_time_minutes": metrics.avg_response_time_minutes,
            "workflows_participated": metrics.workflows_participated
        }
    
    def _serialize_insight(self, insight: Insight) -> Dict[str, Any]:
        """Serialize insight to dict."""
        return {
            "type": insight.insight_type.value,
            "title": insight.title,
            "description": insight.description,
            "severity": insight.severity,
            "confidence": insight.confidence,
            "recommendations": insight.recommendations,
            "timestamp": insight.timestamp.isoformat()
        }
    
    async def _cleanup_old_events(self):
        """Clean up old events based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        # Clean communication events
        self._communication_events = [
            event for event in self._communication_events
            if event.timestamp > cutoff_date
        ]
        
        # Clean workflow events
        self._workflow_events = [
            event for event in self._workflow_events
            if event.timestamp > cutoff_date
        ]

