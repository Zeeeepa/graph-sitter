"""
Continuous Learning Pipeline

This module implements the main continuous learning pipeline that coordinates
pattern recognition, knowledge graph updates, and real-time learning.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import asyncio
import time
import logging
from enum import Enum

from graph_sitter.core.codebase import Codebase
from .pattern_engine import PatternEngine, CodePattern
from .knowledge_graph import KnowledgeGraph, RelationshipType, NodeType
from .analytics_processor import AnalyticsProcessor, AnalyticsEvent, EventType


class LearningSignalType(Enum):
    """Types of learning signals."""
    USER_FEEDBACK = "user_feedback"
    PERFORMANCE_METRIC = "performance_metric"
    ERROR_RESOLUTION = "error_resolution"
    PATTERN_SUCCESS = "pattern_success"
    CODE_CHANGE = "code_change"
    SYSTEM_METRIC = "system_metric"


@dataclass
class LearningSignal:
    """Represents a learning signal that drives continuous improvement."""
    signal_id: str
    signal_type: LearningSignalType
    source: str
    data: Dict[str, Any]
    confidence: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert learning signal to dictionary representation."""
        return {
            'signal_id': self.signal_id,
            'signal_type': self.signal_type.value,
            'source': self.source,
            'data': self.data,
            'confidence': self.confidence,
            'timestamp': self.timestamp
        }


class FeedbackProcessor:
    """Processes user feedback and converts it to learning signals."""
    
    def __init__(self):
        self.feedback_history = []
        self.feedback_weights = {
            'positive': 1.0,
            'negative': -0.5,
            'neutral': 0.0
        }
    
    def process_user_feedback(self, pattern_id: str, feedback_type: str, 
                            feedback_data: Dict[str, Any]) -> LearningSignal:
        """Process user feedback into a learning signal."""
        confidence = self.feedback_weights.get(feedback_type, 0.0)
        
        signal = LearningSignal(
            signal_id=f"feedback_{pattern_id}_{int(time.time())}",
            signal_type=LearningSignalType.USER_FEEDBACK,
            source="user_interface",
            data={
                'pattern_id': pattern_id,
                'feedback_type': feedback_type,
                'feedback_data': feedback_data
            },
            confidence=confidence,
            timestamp=time.time()
        )
        
        self.feedback_history.append(signal)
        return signal
    
    def process_performance_feedback(self, operation: str, metrics: Dict[str, float]) -> LearningSignal:
        """Process performance metrics into a learning signal."""
        # Calculate confidence based on performance improvement
        baseline_duration = metrics.get('baseline_duration', 1.0)
        current_duration = metrics.get('current_duration', 1.0)
        
        improvement = (baseline_duration - current_duration) / baseline_duration
        confidence = min(1.0, max(-1.0, improvement))
        
        signal = LearningSignal(
            signal_id=f"perf_{operation}_{int(time.time())}",
            signal_type=LearningSignalType.PERFORMANCE_METRIC,
            source="performance_monitor",
            data={
                'operation': operation,
                'metrics': metrics,
                'improvement': improvement
            },
            confidence=confidence,
            timestamp=time.time()
        )
        
        return signal
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed feedback."""
        if not self.feedback_history:
            return {'total_feedback': 0}
        
        positive_count = sum(1 for signal in self.feedback_history 
                           if signal.confidence > 0)
        negative_count = sum(1 for signal in self.feedback_history 
                           if signal.confidence < 0)
        neutral_count = len(self.feedback_history) - positive_count - negative_count
        
        return {
            'total_feedback': len(self.feedback_history),
            'positive_feedback': positive_count,
            'negative_feedback': negative_count,
            'neutral_feedback': neutral_count,
            'average_confidence': sum(s.confidence for s in self.feedback_history) / len(self.feedback_history)
        }


class PatternUpdater:
    """Updates pattern confidence and relationships based on learning signals."""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.update_history = []
        self.learning_rate = 0.1
    
    async def update_pattern_confidence(self, signal: LearningSignal):
        """Update pattern confidence based on learning signal."""
        if signal.signal_type == LearningSignalType.USER_FEEDBACK:
            pattern_id = signal.data.get('pattern_id')
            if pattern_id:
                # Update pattern in knowledge graph
                feedback_data = {
                    'score': signal.confidence,
                    'feedback_type': signal.data.get('feedback_type'),
                    'timestamp': signal.timestamp
                }
                
                self.knowledge_graph.update_pattern_feedback(pattern_id, feedback_data)
                
                # Record update
                self.update_history.append({
                    'pattern_id': pattern_id,
                    'signal_id': signal.signal_id,
                    'confidence_change': signal.confidence,
                    'timestamp': signal.timestamp
                })
    
    async def update_pattern_relationships(self, signal: LearningSignal):
        """Update relationships between patterns based on learning signals."""
        if signal.signal_type == LearningSignalType.PATTERN_SUCCESS:
            # Create or strengthen relationships between successful patterns
            pattern_id = signal.data.get('pattern_id')
            related_patterns = signal.data.get('related_patterns', [])
            
            for related_pattern_id in related_patterns:
                # Create similarity relationship
                self.knowledge_graph.create_relationship(
                    pattern_id, related_pattern_id, 
                    RelationshipType.SIMILAR_TO,
                    properties={'strength': signal.confidence},
                    confidence=signal.confidence
                )
    
    def get_update_statistics(self) -> Dict[str, Any]:
        """Get statistics about pattern updates."""
        return {
            'total_updates': len(self.update_history),
            'recent_updates': len([u for u in self.update_history 
                                 if u['timestamp'] > time.time() - 3600]),  # Last hour
            'average_confidence_change': (
                sum(u['confidence_change'] for u in self.update_history) / 
                len(self.update_history) if self.update_history else 0
            )
        }


class RecommendationUpdater:
    """Updates recommendation models based on learning signals."""
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.model_performance = {}
        self.recommendation_history = []
    
    async def update_recommendation_model(self, signal: LearningSignal):
        """Update recommendation models based on learning signals."""
        if signal.signal_type == LearningSignalType.USER_FEEDBACK:
            # Track recommendation effectiveness
            recommendation_id = signal.data.get('recommendation_id')
            if recommendation_id:
                self.model_performance[recommendation_id] = {
                    'feedback_score': signal.confidence,
                    'timestamp': signal.timestamp
                }
        
        elif signal.signal_type == LearningSignalType.PATTERN_SUCCESS:
            # Update success patterns for future recommendations
            pattern_id = signal.data.get('pattern_id')
            success_metrics = signal.data.get('success_metrics', {})
            
            # Create optimization node in knowledge graph
            optimization_id = self.knowledge_graph.add_implementation({
                'name': f"optimization_for_{pattern_id}",
                'description': f"Successful optimization based on pattern {pattern_id}",
                'success_rate': signal.confidence,
                'success_metrics': success_metrics,
                'pattern_id': pattern_id
            })
            
            # Link pattern to optimization
            self.knowledge_graph.create_relationship(
                pattern_id, optimization_id,
                RelationshipType.IMPROVES,
                confidence=signal.confidence
            )
    
    def get_recommendation_effectiveness(self) -> Dict[str, float]:
        """Get effectiveness metrics for recommendations."""
        if not self.model_performance:
            return {}
        
        total_score = sum(perf['feedback_score'] for perf in self.model_performance.values())
        count = len(self.model_performance)
        
        return {
            'average_effectiveness': total_score / count,
            'total_recommendations': count,
            'positive_feedback_rate': sum(1 for perf in self.model_performance.values() 
                                        if perf['feedback_score'] > 0) / count
        }


class ContinuousLearningPipeline:
    """Main continuous learning pipeline that coordinates all learning components."""
    
    def __init__(self, knowledge_graph: Optional[KnowledgeGraph] = None):
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self.pattern_engine = PatternEngine()
        self.analytics_processor = AnalyticsProcessor()
        
        # Learning components
        self.feedback_processor = FeedbackProcessor()
        self.pattern_updater = PatternUpdater(self.knowledge_graph)
        self.recommendation_updater = RecommendationUpdater(self.knowledge_graph)
        
        # Pipeline state
        self.is_running = False
        self.learning_queue = asyncio.Queue()
        self.pipeline_stats = {
            'signals_processed': 0,
            'patterns_updated': 0,
            'recommendations_generated': 0,
            'errors': 0
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    async def start_pipeline(self):
        """Start the continuous learning pipeline."""
        if self.is_running:
            self.logger.warning("Pipeline is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting continuous learning pipeline")
        
        # Start background tasks
        asyncio.create_task(self._process_learning_signals())
        asyncio.create_task(self._periodic_model_updates())
    
    async def stop_pipeline(self):
        """Stop the continuous learning pipeline."""
        self.is_running = False
        self.logger.info("Stopping continuous learning pipeline")
    
    async def process_codebase(self, codebase: Codebase) -> Dict[str, Any]:
        """Process a codebase through the complete learning pipeline."""
        start_time = time.time()
        
        try:
            # 1. Analyze codebase with enhanced analytics
            analysis_result = await self.analytics_processor.process_codebase_analysis(codebase)
            
            # 2. Identify patterns
            patterns = self.pattern_engine.identify_patterns(codebase)
            
            # 3. Update knowledge graph with new patterns
            for pattern in patterns:
                pattern_node_id = self.knowledge_graph.add_pattern(pattern)
                
                # Create learning signal for new pattern discovery
                signal = LearningSignal(
                    signal_id=f"pattern_discovery_{pattern.pattern_id}",
                    signal_type=LearningSignalType.PATTERN_SUCCESS,
                    source="pattern_engine",
                    data={'pattern_id': pattern.pattern_id, 'confidence': pattern.confidence},
                    confidence=pattern.confidence,
                    timestamp=time.time()
                )
                await self.learning_queue.put(signal)
            
            # 4. Generate recommendations
            recommendations = self.knowledge_graph.get_recommendations(codebase, patterns)
            
            # 5. Create comprehensive result
            result = {
                'analysis': analysis_result,
                'patterns': [pattern.to_dict() for pattern in patterns],
                'recommendations': recommendations,
                'processing_time': time.time() - start_time,
                'pipeline_stats': self.get_pipeline_statistics()
            }
            
            self.pipeline_stats['patterns_updated'] += len(patterns)
            self.pipeline_stats['recommendations_generated'] += len(recommendations)
            
            return result
            
        except Exception as e:
            self.pipeline_stats['errors'] += 1
            self.logger.error(f"Error processing codebase: {e}")
            raise
    
    async def submit_feedback(self, pattern_id: str, feedback_type: str, 
                            feedback_data: Dict[str, Any]) -> bool:
        """Submit user feedback for a pattern."""
        try:
            signal = self.feedback_processor.process_user_feedback(
                pattern_id, feedback_type, feedback_data
            )
            await self.learning_queue.put(signal)
            return True
        except Exception as e:
            self.logger.error(f"Error submitting feedback: {e}")
            return False
    
    async def submit_performance_metrics(self, operation: str, 
                                       metrics: Dict[str, float]) -> bool:
        """Submit performance metrics for learning."""
        try:
            signal = self.feedback_processor.process_performance_feedback(operation, metrics)
            await self.learning_queue.put(signal)
            return True
        except Exception as e:
            self.logger.error(f"Error submitting performance metrics: {e}")
            return False
    
    async def _process_learning_signals(self):
        """Background task to process learning signals."""
        while self.is_running:
            try:
                # Wait for learning signal with timeout
                signal = await asyncio.wait_for(self.learning_queue.get(), timeout=1.0)
                
                # Process the signal
                await self._handle_learning_signal(signal)
                
                self.pipeline_stats['signals_processed'] += 1
                
            except asyncio.TimeoutError:
                # No signals to process, continue
                continue
            except Exception as e:
                self.logger.error(f"Error processing learning signal: {e}")
                self.pipeline_stats['errors'] += 1
    
    async def _handle_learning_signal(self, signal: LearningSignal):
        """Handle a single learning signal."""
        try:
            # Update pattern confidence
            await self.pattern_updater.update_pattern_confidence(signal)
            
            # Update pattern relationships
            await self.pattern_updater.update_pattern_relationships(signal)
            
            # Update recommendation models
            await self.recommendation_updater.update_recommendation_model(signal)
            
            self.logger.debug(f"Processed learning signal: {signal.signal_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling learning signal {signal.signal_id}: {e}")
            raise
    
    async def _periodic_model_updates(self):
        """Periodic task to update models and clean up data."""
        while self.is_running:
            try:
                # Wait for 1 hour
                await asyncio.sleep(3600)
                
                # Perform periodic maintenance
                await self._perform_maintenance()
                
            except Exception as e:
                self.logger.error(f"Error in periodic maintenance: {e}")
    
    async def _perform_maintenance(self):
        """Perform periodic maintenance tasks."""
        self.logger.info("Performing periodic maintenance")
        
        # Clean up old data
        # Update model parameters
        # Optimize knowledge graph
        # Generate performance reports
        
        # This is a placeholder for actual maintenance tasks
        pass
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics."""
        return {
            'pipeline_stats': self.pipeline_stats,
            'feedback_stats': self.feedback_processor.get_feedback_statistics(),
            'pattern_update_stats': self.pattern_updater.get_update_statistics(),
            'recommendation_effectiveness': self.recommendation_updater.get_recommendation_effectiveness(),
            'knowledge_graph_stats': self.knowledge_graph.get_graph_statistics(),
            'pattern_engine_stats': self.pattern_engine.get_learning_statistics(),
            'is_running': self.is_running,
            'queue_size': self.learning_queue.qsize()
        }
    
    def get_learning_insights(self, codebase: Codebase) -> Dict[str, Any]:
        """Get learning insights for a specific codebase."""
        # Identify patterns
        patterns = self.pattern_engine.identify_patterns(codebase)
        
        # Get recommendations
        recommendations = self.knowledge_graph.get_recommendations(codebase, patterns)
        
        # Calculate learning metrics
        total_patterns = len(patterns)
        high_confidence_patterns = len([p for p in patterns if p.confidence > 0.8])
        
        return {
            'total_patterns_identified': total_patterns,
            'high_confidence_patterns': high_confidence_patterns,
            'pattern_confidence_avg': sum(p.confidence for p in patterns) / max(total_patterns, 1),
            'recommendations_count': len(recommendations),
            'learning_effectiveness': high_confidence_patterns / max(total_patterns, 1),
            'top_patterns': [p.to_dict() for p in patterns[:5]],  # Top 5 patterns
            'top_recommendations': recommendations[:5]  # Top 5 recommendations
        }

