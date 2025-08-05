"""
Event Analyzer

Advanced analysis of event patterns and correlations for insights and optimization.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from .models import Event, EventCorrelation, CorrelationType


class EventAnalyzer:
    """
    Advanced analyzer for event patterns, trends, and correlation insights.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analysis_cache: Dict[str, Any] = {}
        self.last_analysis: Optional[datetime] = None
    
    async def analyze_patterns(self, events: List[Event], correlations: List[EventCorrelation]) -> Dict[str, Any]:
        """
        Analyze event patterns and correlations for insights
        
        Args:
            events: List of events to analyze
            correlations: List of correlations to analyze
            
        Returns:
            Analysis results with patterns and insights
        """
        analysis = {
            'timestamp': datetime.now(),
            'event_patterns': await self._analyze_event_patterns(events),
            'correlation_patterns': await self._analyze_correlation_patterns(correlations),
            'temporal_patterns': await self._analyze_temporal_patterns(events),
            'platform_interactions': await self._analyze_platform_interactions(events, correlations),
            'user_behavior': await self._analyze_user_behavior(events),
            'insights': await self._generate_insights(events, correlations)
        }
        
        self.analysis_cache['latest'] = analysis
        self.last_analysis = datetime.now()
        
        return analysis
    
    async def _analyze_event_patterns(self, events: List[Event]) -> Dict[str, Any]:
        """Analyze patterns in event types and frequencies"""
        if not events:
            return {}
        
        # Event type frequency
        event_type_counts = Counter(event.event_type for event in events)
        
        # Platform frequency
        platform_counts = Counter(event.platform for event in events)
        
        # Hourly distribution
        hourly_counts = Counter(event.timestamp.hour for event in events)
        
        # Daily distribution
        daily_counts = Counter(event.timestamp.weekday() for event in events)
        
        # Repository activity
        repo_counts = Counter(
            event.repository for event in events 
            if event.repository
        )
        
        return {
            'event_type_frequency': dict(event_type_counts.most_common(10)),
            'platform_frequency': dict(platform_counts),
            'hourly_distribution': dict(hourly_counts),
            'daily_distribution': dict(daily_counts),
            'top_repositories': dict(repo_counts.most_common(10)),
            'total_events': len(events),
            'unique_users': len(set(e.user_id for e in events if e.user_id)),
            'unique_repositories': len(set(e.repository for e in events if e.repository))
        }
    
    async def _analyze_correlation_patterns(self, correlations: List[EventCorrelation]) -> Dict[str, Any]:
        """Analyze patterns in event correlations"""
        if not correlations:
            return {}
        
        # Correlation type distribution
        type_counts = Counter(corr.correlation_type for corr in correlations)
        
        # Confidence distribution
        confidences = [corr.confidence for corr in correlations]
        confidence_stats = {
            'mean': statistics.mean(confidences),
            'median': statistics.median(confidences),
            'std_dev': statistics.stdev(confidences) if len(confidences) > 1 else 0,
            'min': min(confidences),
            'max': max(confidences)
        }
        
        # Platform pair correlations
        platform_pairs = Counter()
        for corr in correlations:
            platforms = sorted(set(event.platform for event in corr.events))
            if len(platforms) > 1:
                platform_pairs[tuple(platforms)] += 1
        
        # Time span analysis
        time_spans = []
        for corr in correlations:
            span = corr.get_time_span()
            if span:
                time_spans.append(span.total_seconds())
        
        time_span_stats = {}
        if time_spans:
            time_span_stats = {
                'mean_seconds': statistics.mean(time_spans),
                'median_seconds': statistics.median(time_spans),
                'min_seconds': min(time_spans),
                'max_seconds': max(time_spans)
            }
        
        return {
            'correlation_type_distribution': {k.value: v for k, v in type_counts.items()},
            'confidence_statistics': confidence_stats,
            'cross_platform_correlations': dict(platform_pairs.most_common(10)),
            'time_span_statistics': time_span_stats,
            'total_correlations': len(correlations),
            'average_events_per_correlation': statistics.mean([len(c.events) for c in correlations])
        }
    
    async def _analyze_temporal_patterns(self, events: List[Event]) -> Dict[str, Any]:
        """Analyze temporal patterns in events"""
        if not events:
            return {}
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        # Calculate event intervals
        intervals = []
        for i in range(1, len(sorted_events)):
            interval = (sorted_events[i].timestamp - sorted_events[i-1].timestamp).total_seconds()
            intervals.append(interval)
        
        interval_stats = {}
        if intervals:
            interval_stats = {
                'mean_interval_seconds': statistics.mean(intervals),
                'median_interval_seconds': statistics.median(intervals),
                'min_interval_seconds': min(intervals),
                'max_interval_seconds': max(intervals)
            }
        
        # Burst detection (periods of high activity)
        bursts = self._detect_event_bursts(sorted_events)
        
        # Peak hours
        hourly_activity = defaultdict(int)
        for event in events:
            hourly_activity[event.timestamp.hour] += 1
        
        peak_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'interval_statistics': interval_stats,
            'event_bursts': bursts,
            'peak_hours': peak_hours,
            'time_range': {
                'start': sorted_events[0].timestamp.isoformat() if sorted_events else None,
                'end': sorted_events[-1].timestamp.isoformat() if sorted_events else None,
                'duration_hours': (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds() / 3600 if len(sorted_events) > 1 else 0
            }
        }
    
    def _detect_event_bursts(self, sorted_events: List[Event], window_minutes: int = 5, threshold: int = 5) -> List[Dict[str, Any]]:
        """Detect periods of high event activity (bursts)"""
        if len(sorted_events) < threshold:
            return []
        
        bursts = []
        window = timedelta(minutes=window_minutes)
        
        i = 0
        while i < len(sorted_events):
            window_start = sorted_events[i].timestamp
            window_end = window_start + window
            
            # Count events in this window
            window_events = []
            j = i
            while j < len(sorted_events) and sorted_events[j].timestamp <= window_end:
                window_events.append(sorted_events[j])
                j += 1
            
            # If we have a burst, record it
            if len(window_events) >= threshold:
                burst = {
                    'start_time': window_start.isoformat(),
                    'end_time': window_events[-1].timestamp.isoformat(),
                    'event_count': len(window_events),
                    'duration_minutes': (window_events[-1].timestamp - window_start).total_seconds() / 60,
                    'platforms': list(set(e.platform for e in window_events)),
                    'event_types': list(set(e.event_type for e in window_events))
                }
                bursts.append(burst)
                i = j  # Skip past this burst
            else:
                i += 1
        
        return bursts
    
    async def _analyze_platform_interactions(self, events: List[Event], correlations: List[EventCorrelation]) -> Dict[str, Any]:
        """Analyze interactions between different platforms"""
        # Platform event counts
        platform_events = defaultdict(int)
        for event in events:
            platform_events[event.platform] += 1
        
        # Cross-platform correlations
        cross_platform_corrs = []
        for corr in correlations:
            platforms = set(event.platform for event in corr.events)
            if len(platforms) > 1:
                cross_platform_corrs.append({
                    'platforms': sorted(platforms),
                    'confidence': corr.confidence,
                    'correlation_type': corr.correlation_type.value,
                    'event_count': len(corr.events)
                })
        
        # Platform interaction matrix
        interaction_matrix = defaultdict(lambda: defaultdict(int))
        for corr in correlations:
            platforms = list(set(event.platform for event in corr.events))
            for i, platform1 in enumerate(platforms):
                for platform2 in platforms[i+1:]:
                    interaction_matrix[platform1][platform2] += 1
                    interaction_matrix[platform2][platform1] += 1
        
        return {
            'platform_event_counts': dict(platform_events),
            'cross_platform_correlations': cross_platform_corrs,
            'interaction_matrix': {k: dict(v) for k, v in interaction_matrix.items()},
            'most_correlated_platforms': self._find_most_correlated_platforms(interaction_matrix)
        }
    
    def _find_most_correlated_platforms(self, interaction_matrix: Dict[str, Dict[str, int]]) -> List[Tuple[str, str, int]]:
        """Find the most correlated platform pairs"""
        pairs = []
        processed = set()
        
        for platform1, interactions in interaction_matrix.items():
            for platform2, count in interactions.items():
                pair = tuple(sorted([platform1, platform2]))
                if pair not in processed:
                    pairs.append((platform1, platform2, count))
                    processed.add(pair)
        
        return sorted(pairs, key=lambda x: x[2], reverse=True)[:5]
    
    async def _analyze_user_behavior(self, events: List[Event]) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        user_events = defaultdict(list)
        for event in events:
            if event.user_id:
                user_events[event.user_id].append(event)
        
        if not user_events:
            return {}
        
        # User activity levels
        user_activity = {
            user_id: len(user_events)
            for user_id, user_events in user_events.items()
        }
        
        # Most active users
        most_active = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # User platform preferences
        user_platforms = defaultdict(lambda: defaultdict(int))
        for user_id, events in user_events.items():
            for event in events:
                user_platforms[user_id][event.platform] += 1
        
        # Average events per user
        avg_events_per_user = statistics.mean(user_activity.values()) if user_activity else 0
        
        return {
            'total_active_users': len(user_events),
            'most_active_users': most_active,
            'average_events_per_user': avg_events_per_user,
            'user_platform_distribution': {
                user_id: dict(platforms)
                for user_id, platforms in list(user_platforms.items())[:10]
            }
        }
    
    async def _generate_insights(self, events: List[Event], correlations: List[EventCorrelation]) -> List[Dict[str, Any]]:
        """Generate actionable insights from the analysis"""
        insights = []
        
        if not events:
            return insights
        
        # High correlation confidence insight
        high_confidence_corrs = [c for c in correlations if c.confidence > 0.8]
        if high_confidence_corrs:
            insights.append({
                'type': 'high_confidence_correlations',
                'title': 'Strong Event Correlations Detected',
                'description': f'Found {len(high_confidence_corrs)} correlations with >80% confidence',
                'recommendation': 'Consider creating automated workflows for these patterns',
                'data': {
                    'count': len(high_confidence_corrs),
                    'average_confidence': statistics.mean([c.confidence for c in high_confidence_corrs])
                }
            })
        
        # Platform isolation insight
        platform_counts = Counter(event.platform for event in events)
        if len(platform_counts) > 1:
            cross_platform_corrs = [c for c in correlations if len(set(e.platform for e in c.events)) > 1]
            isolation_ratio = 1 - (len(cross_platform_corrs) / len(correlations)) if correlations else 0
            
            if isolation_ratio > 0.7:
                insights.append({
                    'type': 'platform_isolation',
                    'title': 'Limited Cross-Platform Integration',
                    'description': f'{isolation_ratio:.1%} of correlations are within single platforms',
                    'recommendation': 'Consider improving cross-platform workflow integration',
                    'data': {
                        'isolation_ratio': isolation_ratio,
                        'platforms': list(platform_counts.keys())
                    }
                })
        
        # Event burst insight
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        bursts = self._detect_event_bursts(sorted_events)
        if bursts:
            insights.append({
                'type': 'event_bursts',
                'title': 'High Activity Periods Detected',
                'description': f'Found {len(bursts)} periods of intense activity',
                'recommendation': 'Monitor system performance during peak periods',
                'data': {
                    'burst_count': len(bursts),
                    'max_events_in_burst': max(b['event_count'] for b in bursts)
                }
            })
        
        # User concentration insight
        user_events = defaultdict(int)
        for event in events:
            if event.user_id:
                user_events[event.user_id] += 1
        
        if user_events:
            total_events = sum(user_events.values())
            top_user_events = max(user_events.values())
            concentration = top_user_events / total_events
            
            if concentration > 0.5:
                insights.append({
                    'type': 'user_concentration',
                    'title': 'High User Activity Concentration',
                    'description': f'Top user accounts for {concentration:.1%} of all events',
                    'recommendation': 'Consider load balancing or user activity limits',
                    'data': {
                        'concentration_ratio': concentration,
                        'top_user_events': top_user_events,
                        'total_users': len(user_events)
                    }
                })
        
        return insights
    
    async def get_analysis_summary(self) -> Optional[Dict[str, Any]]:
        """Get the latest analysis summary"""
        return self.analysis_cache.get('latest')
    
    async def get_insights(self) -> List[Dict[str, Any]]:
        """Get the latest insights"""
        latest = self.analysis_cache.get('latest')
        return latest.get('insights', []) if latest else []

