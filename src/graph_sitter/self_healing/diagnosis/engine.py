"""
Diagnosis Engine

Automated root cause analysis and diagnostic data correlation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..models.events import ErrorEvent, DiagnosisResult, HealthMetric
from ..models.enums import DiagnosisConfidence, ErrorType
from .analyzers import RootCauseAnalyzer, EventCorrelator, DecisionTree


class DiagnosisEngine:
    """
    Engine for automated diagnosis of system errors.
    
    Performs root cause analysis, correlates events, and generates
    recommended actions for error resolution.
    """
    
    def __init__(self):
        """Initialize the diagnosis engine."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize analyzers
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.event_correlator = EventCorrelator()
        self.decision_tree = DecisionTree()
        
        # Cache for recent events and metrics
        self.recent_events: List[ErrorEvent] = []
        self.recent_metrics: Dict[str, List[HealthMetric]] = {}
        self.max_cache_size = 1000
        self.cache_duration = timedelta(hours=24)
    
    async def analyze_error(self, error_id: str, error_event: ErrorEvent) -> DiagnosisResult:
        """
        Perform comprehensive analysis of an error event.
        
        Args:
            error_id: Unique identifier for the error
            error_event: The error event to analyze
            
        Returns:
            Diagnosis result with root cause and recommendations
        """
        try:
            self.logger.info(f"Starting diagnosis for error {error_id}")
            
            # Add to recent events cache
            self._add_to_cache(error_event)
            
            # Perform root cause analysis
            root_cause = await self.root_cause_analyzer.analyze(error_event, self.recent_metrics)
            
            # Correlate with recent events
            correlated_events = await self.correlate_events(error_event)
            
            # Generate diagnosis result
            diagnosis = await self.generate_diagnosis({
                "error_event": error_event,
                "root_cause": root_cause,
                "correlated_events": correlated_events,
                "recent_metrics": self.recent_metrics,
            })
            
            diagnosis.error_event_id = error_id
            
            self.logger.info(f"Diagnosis completed for error {error_id}: {diagnosis.root_cause}")
            return diagnosis
            
        except Exception as e:
            self.logger.error(f"Error analyzing error {error_id}: {e}")
            
            # Return basic diagnosis on failure
            return DiagnosisResult(
                error_event_id=error_id,
                root_cause=f"Analysis failed: {str(e)}",
                confidence=DiagnosisConfidence.LOW,
                recommended_actions=["Manual investigation required"],
                analysis_data={"error": str(e)},
            )
    
    async def correlate_events(self, error_context: ErrorEvent) -> List[str]:
        """
        Correlate error event with recent events and patterns.
        
        Args:
            error_context: The error event to correlate
            
        Returns:
            List of correlated event IDs
        """
        try:
            return await self.event_correlator.correlate(error_context, self.recent_events)
            
        except Exception as e:
            self.logger.error(f"Error correlating events: {e}")
            return []
    
    async def generate_diagnosis(self, analysis_result: Dict[str, Any]) -> DiagnosisResult:
        """
        Generate diagnosis and recommended actions from analysis results.
        
        Args:
            analysis_result: Results from various analysis components
            
        Returns:
            Complete diagnosis result
        """
        try:
            error_event = analysis_result["error_event"]
            root_cause = analysis_result["root_cause"]
            correlated_events = analysis_result["correlated_events"]
            
            # Use decision tree to determine recommended actions
            recommended_actions = await self.decision_tree.get_recommendations(
                error_event, root_cause, correlated_events
            )
            
            # Assess confidence based on analysis quality
            confidence = self._assess_confidence(analysis_result)
            
            # Create diagnosis result
            diagnosis = DiagnosisResult(
                root_cause=root_cause["description"],
                confidence=confidence,
                recommended_actions=recommended_actions,
                analysis_data={
                    "root_cause_details": root_cause,
                    "correlation_score": len(correlated_events),
                    "metrics_analyzed": len(analysis_result.get("recent_metrics", {})),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                },
                correlated_events=correlated_events,
            )
            
            return diagnosis
            
        except Exception as e:
            self.logger.error(f"Error generating diagnosis: {e}")
            
            # Return minimal diagnosis on error
            return DiagnosisResult(
                root_cause="Unable to determine root cause",
                confidence=DiagnosisConfidence.LOW,
                recommended_actions=["Manual investigation required"],
                analysis_data={"error": str(e)},
            )
    
    def add_metric_data(self, metric_name: str, metrics: List[HealthMetric]) -> None:
        """
        Add metric data for analysis.
        
        Args:
            metric_name: Name of the metric
            metrics: List of metric measurements
        """
        if metric_name not in self.recent_metrics:
            self.recent_metrics[metric_name] = []
        
        # Add new metrics
        self.recent_metrics[metric_name].extend(metrics)
        
        # Clean old metrics
        cutoff_time = datetime.utcnow() - self.cache_duration
        self.recent_metrics[metric_name] = [
            m for m in self.recent_metrics[metric_name]
            if m.measured_at and m.measured_at > cutoff_time
        ]
        
        # Limit cache size
        if len(self.recent_metrics[metric_name]) > self.max_cache_size:
            self.recent_metrics[metric_name] = self.recent_metrics[metric_name][-self.max_cache_size:]
    
    def _add_to_cache(self, error_event: ErrorEvent) -> None:
        """Add error event to recent events cache."""
        self.recent_events.append(error_event)
        
        # Clean old events
        cutoff_time = datetime.utcnow() - self.cache_duration
        self.recent_events = [
            e for e in self.recent_events
            if e.detected_at > cutoff_time
        ]
        
        # Limit cache size
        if len(self.recent_events) > self.max_cache_size:
            self.recent_events = self.recent_events[-self.max_cache_size:]
    
    def _assess_confidence(self, analysis_result: Dict[str, Any]) -> DiagnosisConfidence:
        """
        Assess confidence level of the diagnosis.
        
        Args:
            analysis_result: Analysis results to assess
            
        Returns:
            Confidence level
        """
        try:
            confidence_score = 0.0
            
            # Root cause analysis quality
            root_cause = analysis_result.get("root_cause", {})
            if root_cause.get("confidence", 0) > 0.8:
                confidence_score += 0.4
            elif root_cause.get("confidence", 0) > 0.6:
                confidence_score += 0.3
            elif root_cause.get("confidence", 0) > 0.4:
                confidence_score += 0.2
            else:
                confidence_score += 0.1
            
            # Event correlation quality
            correlated_events = analysis_result.get("correlated_events", [])
            if len(correlated_events) >= 3:
                confidence_score += 0.3
            elif len(correlated_events) >= 1:
                confidence_score += 0.2
            else:
                confidence_score += 0.1
            
            # Metrics availability
            recent_metrics = analysis_result.get("recent_metrics", {})
            if len(recent_metrics) >= 3:
                confidence_score += 0.3
            elif len(recent_metrics) >= 1:
                confidence_score += 0.2
            else:
                confidence_score += 0.1
            
            # Convert to confidence enum
            if confidence_score >= 0.9:
                return DiagnosisConfidence.VERY_HIGH
            elif confidence_score >= 0.7:
                return DiagnosisConfidence.HIGH
            elif confidence_score >= 0.5:
                return DiagnosisConfidence.MEDIUM
            else:
                return DiagnosisConfidence.LOW
                
        except Exception as e:
            self.logger.error(f"Error assessing confidence: {e}")
            return DiagnosisConfidence.LOW
    
    async def get_diagnosis_history(self, error_type: Optional[ErrorType] = None, 
                                  limit: int = 100) -> List[DiagnosisResult]:
        """
        Get historical diagnosis results for learning and improvement.
        
        Args:
            error_type: Filter by error type (optional)
            limit: Maximum number of results to return
            
        Returns:
            List of historical diagnosis results
        """
        # This would typically query a database
        # For now, return empty list as placeholder
        return []
    
    async def update_diagnosis_effectiveness(self, diagnosis_id: str, 
                                           effectiveness_score: float) -> bool:
        """
        Update the effectiveness score of a diagnosis.
        
        Args:
            diagnosis_id: ID of the diagnosis to update
            effectiveness_score: Score from 0.0 to 1.0
            
        Returns:
            True if update was successful
        """
        try:
            # This would typically update a database record
            self.logger.info(f"Updated diagnosis {diagnosis_id} effectiveness: {effectiveness_score}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating diagnosis effectiveness: {e}")
            return False

