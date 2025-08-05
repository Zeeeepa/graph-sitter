"""
Event Correlator

Cross-platform event correlation engine for identifying related events.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .models import Event, EventCorrelation, CorrelationRule, CorrelationType, DEFAULT_CORRELATION_RULES
from .analyzer import EventAnalyzer


class EventCorrelator:
    """
    Cross-platform event correlation engine that identifies and analyzes
    relationships between events from different platforms.
    """
    
    def __init__(self, correlation_window: timedelta = timedelta(minutes=5)):
        self.logger = logging.getLogger(__name__)
        self.correlation_window = correlation_window
        
        # Storage
        self.events: List[Event] = []
        self.correlations: List[EventCorrelation] = []
        self.correlation_rules: Dict[str, CorrelationRule] = {}
        
        # Components
        self.analyzer = EventAnalyzer()
        
        # State
        self.running = False
        self.correlation_task: Optional[asyncio.Task] = None
        
        # Load default rules
        self._load_default_rules()
    
    async def start(self):
        """Start the event correlator"""
        if self.running:
            return
        
        self.logger.info("Starting event correlator")
        self.running = True
        
        # Start correlation processing
        self.correlation_task = asyncio.create_task(self._correlation_loop())
        
        self.logger.info("Event correlator started")
    
    async def stop(self):
        """Stop the event correlator"""
        self.logger.info("Stopping event correlator")
        self.running = False
        
        if self.correlation_task:
            self.correlation_task.cancel()
            try:
                await self.correlation_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Event correlator stopped")
    
    def _load_default_rules(self):
        """Load default correlation rules"""
        for rule in DEFAULT_CORRELATION_RULES:
            self.correlation_rules[rule.id] = rule
        
        self.logger.info(f"Loaded {len(DEFAULT_CORRELATION_RULES)} default correlation rules")
    
    def add_correlation_rule(self, rule: CorrelationRule):
        """Add a custom correlation rule"""
        self.correlation_rules[rule.id] = rule
        self.logger.info(f"Added correlation rule: {rule.id}")
    
    def remove_correlation_rule(self, rule_id: str) -> bool:
        """Remove a correlation rule"""
        if rule_id in self.correlation_rules:
            del self.correlation_rules[rule_id]
            self.logger.info(f"Removed correlation rule: {rule_id}")
            return True
        return False
    
    async def correlate_event(self, platform: str, event_data: Dict[str, Any]) -> List[EventCorrelation]:
        """
        Correlate a new event with existing events
        
        Args:
            platform: Source platform
            event_data: Event data
            
        Returns:
            List of correlations involving this event
        """
        # Create event object
        event = self._create_event(platform, event_data)
        
        # Add to event store
        self.events.append(event)
        
        # Find correlations
        correlations = await self._find_correlations(event)
        
        # Store correlations
        self.correlations.extend(correlations)
        
        # Clean up old events
        self._cleanup_old_events()
        
        self.logger.debug(f"Correlated event {event.id}, found {len(correlations)} correlations")
        
        return correlations
    
    def _create_event(self, platform: str, event_data: Dict[str, Any]) -> Event:
        """Create an Event object from platform data"""
        event = Event(
            platform=platform,
            data=event_data.copy()
        )
        
        # Extract common attributes
        if 'type' in event_data:
            event.event_type = self._map_event_type(platform, event_data['type'])
        
        if 'user' in event_data:
            event.user_id = str(event_data['user'])
        elif 'actor' in event_data:
            event.user_id = str(event_data['actor'])
        
        if 'repository' in event_data:
            event.repository = str(event_data['repository'])
        elif 'repo' in event_data:
            event.repository = str(event_data['repo'])
        
        if 'issue' in event_data:
            event.issue_id = str(event_data['issue'])
        
        if 'pull_request' in event_data:
            event.pr_id = str(event_data['pull_request'])
        elif 'pr' in event_data:
            event.pr_id = str(event_data['pr'])
        
        # Generate correlation keys
        self._generate_correlation_keys(event)
        
        return event
    
    def _map_event_type(self, platform: str, event_type: str) -> str:
        """Map platform-specific event types to standard types"""
        mapping = {
            'github': {
                'pull_request.opened': 'github.pr.opened',
                'pull_request.closed': 'github.pr.closed',
                'pull_request.merged': 'github.pr.merged',
                'issues.opened': 'github.issue.opened',
                'issues.closed': 'github.issue.closed',
                'push': 'github.push',
                'release': 'github.release',
            },
            'linear': {
                'issue.created': 'linear.issue.created',
                'issue.updated': 'linear.issue.updated',
                'issue.completed': 'linear.issue.completed',
                'comment.created': 'linear.comment.added',
            },
            'slack': {
                'message': 'slack.message',
                'reaction_added': 'slack.reaction',
                'thread_reply': 'slack.thread.reply',
            },
            'codegen': {
                'task.started': 'codegen.task.started',
                'task.completed': 'codegen.task.completed',
                'task.failed': 'codegen.task.failed',
            }
        }
        
        platform_mapping = mapping.get(platform, {})
        return platform_mapping.get(event_type, f"{platform}.{event_type}")
    
    def _generate_correlation_keys(self, event: Event):
        """Generate correlation keys for an event"""
        # Repository-based correlation
        if event.repository:
            event.add_correlation_key("repository", event.repository)
        
        # User-based correlation
        if event.user_id:
            event.add_correlation_key("user", event.user_id)
        
        # Issue-based correlation
        if event.issue_id:
            event.add_correlation_key("issue", event.issue_id)
        
        # PR-based correlation
        if event.pr_id:
            event.add_correlation_key("pr", event.pr_id)
        
        # Title/content-based correlation
        if 'title' in event.data:
            # Extract keywords from title for correlation
            title = str(event.data['title']).lower()
            words = [w for w in title.split() if len(w) > 3]
            for word in words[:3]:  # Use first 3 significant words
                event.add_correlation_key("keyword", word)
    
    async def _find_correlations(self, new_event: Event) -> List[EventCorrelation]:
        """Find correlations for a new event"""
        correlations = []
        
        # Get candidate events within time window
        cutoff_time = new_event.timestamp - self.correlation_window
        candidate_events = [
            e for e in self.events 
            if e.timestamp >= cutoff_time and e.id != new_event.id
        ]
        
        # Apply correlation rules
        for rule in self.correlation_rules.values():
            if not rule.enabled or not rule.matches_event(new_event):
                continue
            
            # Find matching events for this rule
            matching_events = [new_event]
            for event in candidate_events:
                if rule.matches_event(event):
                    # Check time window
                    time_diff = abs((new_event.timestamp - event.timestamp).total_seconds())
                    if time_diff <= rule.time_window.total_seconds():
                        matching_events.append(event)
            
            # Create correlations if we have multiple matching events
            if len(matching_events) > 1:
                correlation = await self._create_correlation(rule, matching_events)
                if correlation:
                    correlations.append(correlation)
        
        # Find correlations based on shared attributes
        attribute_correlations = await self._find_attribute_correlations(new_event, candidate_events)
        correlations.extend(attribute_correlations)
        
        return correlations
    
    async def _create_correlation(
        self, 
        rule: CorrelationRule, 
        events: List[Event]
    ) -> Optional[EventCorrelation]:
        """Create a correlation based on a rule"""
        confidence = rule.calculate_confidence(events)
        
        if confidence < 0.3:  # Minimum confidence threshold
            return None
        
        # Find common attributes
        common_attributes = {}
        if len(events) > 1:
            first_event_data = events[0].data
            for key, value in first_event_data.items():
                if all(e.data.get(key) == value for e in events[1:]):
                    common_attributes[key] = value
        
        correlation = EventCorrelation(
            correlation_type=rule.correlation_type,
            events=events.copy(),
            confidence=confidence,
            common_attributes=common_attributes,
            time_window=rule.time_window,
            description=f"Correlation based on rule: {rule.name}",
            created_by=f"rule:{rule.id}"
        )
        
        return correlation
    
    async def _find_attribute_correlations(
        self, 
        new_event: Event, 
        candidate_events: List[Event]
    ) -> List[EventCorrelation]:
        """Find correlations based on shared attributes"""
        correlations = []
        
        # Group events by correlation keys
        key_groups = defaultdict(list)
        for event in candidate_events:
            for key in event.correlation_keys:
                key_groups[key].append(event)
        
        # Check if new event shares keys with existing events
        for key in new_event.correlation_keys:
            if key in key_groups and len(key_groups[key]) > 0:
                related_events = [new_event] + key_groups[key]
                
                # Calculate confidence based on key type and time proximity
                confidence = 0.5
                if key.startswith("repository:"):
                    confidence = 0.7
                elif key.startswith("user:"):
                    confidence = 0.6
                elif key.startswith("issue:") or key.startswith("pr:"):
                    confidence = 0.8
                
                # Adjust for time proximity
                timestamps = [e.timestamp for e in related_events]
                time_span = max(timestamps) - min(timestamps)
                if time_span < self.correlation_window / 2:
                    confidence += 0.1
                
                if confidence >= 0.5:
                    correlation = EventCorrelation(
                        correlation_type=CorrelationType.RELATED,
                        events=related_events,
                        confidence=confidence,
                        common_attributes={key.split(":", 1)[0]: key.split(":", 1)[1]},
                        description=f"Correlation based on shared {key.split(':', 1)[0]}",
                        created_by="attribute_matcher"
                    )
                    correlations.append(correlation)
        
        return correlations
    
    def _cleanup_old_events(self):
        """Remove events older than the correlation window"""
        cutoff_time = datetime.now() - self.correlation_window * 2
        
        # Remove old events
        old_count = len(self.events)
        self.events = [e for e in self.events if e.timestamp >= cutoff_time]
        
        # Remove old correlations
        old_corr_count = len(self.correlations)
        self.correlations = [c for c in self.correlations if c.created_at >= cutoff_time]
        
        if len(self.events) < old_count or len(self.correlations) < old_corr_count:
            self.logger.debug(f"Cleaned up {old_count - len(self.events)} old events, "
                            f"{old_corr_count - len(self.correlations)} old correlations")
    
    async def get_correlations_for_event(self, event_id: str) -> List[EventCorrelation]:
        """Get all correlations involving a specific event"""
        return [
            corr for corr in self.correlations
            if any(e.id == event_id for e in corr.events)
        ]
    
    async def get_recent_correlations(self, limit: int = 50) -> List[EventCorrelation]:
        """Get recent correlations"""
        sorted_correlations = sorted(
            self.correlations, 
            key=lambda c: c.created_at, 
            reverse=True
        )
        return sorted_correlations[:limit]
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get correlation metrics"""
        total_events = len(self.events)
        total_correlations = len(self.correlations)
        
        # Platform distribution
        platform_counts = defaultdict(int)
        for event in self.events:
            platform_counts[event.platform] += 1
        
        # Correlation type distribution
        correlation_type_counts = defaultdict(int)
        for corr in self.correlations:
            correlation_type_counts[corr.correlation_type.value] += 1
        
        # Average confidence
        avg_confidence = 0.0
        if self.correlations:
            avg_confidence = sum(c.confidence for c in self.correlations) / len(self.correlations)
        
        return {
            'total_events': total_events,
            'total_correlations': total_correlations,
            'platform_distribution': dict(platform_counts),
            'correlation_type_distribution': dict(correlation_type_counts),
            'average_confidence': avg_confidence,
            'active_rules': len([r for r in self.correlation_rules.values() if r.enabled]),
            'correlation_window_minutes': self.correlation_window.total_seconds() / 60
        }
    
    async def _correlation_loop(self):
        """Background correlation processing loop"""
        while self.running:
            try:
                # Periodic cleanup and analysis
                self._cleanup_old_events()
                
                # Run advanced analysis
                await self.analyzer.analyze_patterns(self.events, self.correlations)
                
                await asyncio.sleep(60)  # Run every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Correlation loop error: {e}")
                await asyncio.sleep(60)

