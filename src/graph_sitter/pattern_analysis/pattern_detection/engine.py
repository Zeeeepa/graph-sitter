"""Pattern detection engine for identifying trends and patterns in historical data."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from ..models import Pattern, PatternType, MLModel
from ..config import PatternAnalysisConfig
from .algorithms import (
    PerformancePatternDetector,
    AnomalyDetector,
    TrendAnalyzer,
    SeasonalityDetector
)

logger = logging.getLogger(__name__)


class PatternDetectionEngine:
    """
    Pattern detection engine for identifying patterns in task and pipeline data.
    
    This engine uses multiple algorithms to detect:
    - Performance patterns and trends
    - Anomalies and outliers
    - Seasonal patterns
    - Resource usage patterns
    - Error patterns
    """
    
    def __init__(self, models: Dict[str, MLModel], config: Optional[PatternAnalysisConfig] = None):
        """
        Initialize pattern detection engine with trained ML models.
        
        Args:
            models: Dictionary of trained ML models
            config: Configuration for pattern analysis
        """
        self.models = models
        self.config = config or PatternAnalysisConfig()
        
        # Initialize pattern detection algorithms
        self.performance_detector = PerformancePatternDetector()
        self.anomaly_detector = AnomalyDetector()
        self.trend_analyzer = TrendAnalyzer()
        self.seasonality_detector = SeasonalityDetector()
        
        # Pattern cache for efficiency
        self.pattern_cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        
        logger.info("PatternDetectionEngine initialized with {} models".format(len(models)))
    
    async def detect_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """
        Identify patterns in task and pipeline data.
        
        Args:
            data: Preprocessed DataFrame with historical data
            
        Returns:
            List of detected patterns
        """
        logger.info(f"Detecting patterns in {len(data)} records")
        
        try:
            all_patterns = []
            
            # Run different pattern detection algorithms in parallel
            detection_tasks = [
                self._detect_performance_patterns(data),
                self._detect_anomaly_patterns(data),
                self._detect_trend_patterns(data),
                self._detect_seasonal_patterns(data),
                self._detect_resource_patterns(data),
                self._detect_error_patterns(data),
            ]
            
            results = await asyncio.gather(*detection_tasks, return_exceptions=True)
            
            # Combine results from all detectors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Pattern detection task {i} failed: {result}")
                    continue
                if result:
                    all_patterns.extend(result)
            
            # Filter patterns by significance
            significant_patterns = await self._filter_significant_patterns(all_patterns)
            
            logger.info(f"Detected {len(significant_patterns)} significant patterns")
            return significant_patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            raise
    
    async def classify_patterns(self, patterns: List[Pattern]) -> List[Pattern]:
        """
        Classify and score pattern significance.
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            List of classified patterns with updated scores
        """
        logger.info(f"Classifying {len(patterns)} patterns")
        
        try:
            classified_patterns = []
            
            for pattern in patterns:
                # Calculate significance score
                significance_score = await self._calculate_significance_score(pattern)
                pattern.significance_score = significance_score
                
                # Calculate impact score
                impact_score = await self._calculate_impact_score(pattern)
                pattern.impact_score = impact_score
                
                # Calculate confidence score
                confidence_score = await self._calculate_confidence_score(pattern)
                pattern.confidence = confidence_score
                
                classified_patterns.append(pattern)
            
            # Sort by significance score
            classified_patterns.sort(key=lambda p: p.significance_score, reverse=True)
            
            logger.info("Pattern classification completed")
            return classified_patterns
            
        except Exception as e:
            logger.error(f"Error classifying patterns: {e}")
            raise
    
    async def _detect_performance_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect performance-related patterns."""
        logger.debug("Detecting performance patterns")
        
        try:
            patterns = await self.performance_detector.detect(data)
            logger.debug(f"Found {len(patterns)} performance patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting performance patterns: {e}")
            return []
    
    async def _detect_anomaly_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect anomaly patterns."""
        logger.debug("Detecting anomaly patterns")
        
        try:
            patterns = await self.anomaly_detector.detect(data)
            logger.debug(f"Found {len(patterns)} anomaly patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting anomaly patterns: {e}")
            return []
    
    async def _detect_trend_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect trend patterns."""
        logger.debug("Detecting trend patterns")
        
        try:
            patterns = await self.trend_analyzer.detect(data)
            logger.debug(f"Found {len(patterns)} trend patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting trend patterns: {e}")
            return []
    
    async def _detect_seasonal_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect seasonal patterns."""
        logger.debug("Detecting seasonal patterns")
        
        try:
            patterns = await self.seasonality_detector.detect(data)
            logger.debug(f"Found {len(patterns)} seasonal patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting seasonal patterns: {e}")
            return []
    
    async def _detect_resource_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect resource usage patterns."""
        logger.debug("Detecting resource patterns")
        
        try:
            patterns = []
            
            # CPU usage patterns
            if 'cpu_usage' in data.columns:
                cpu_patterns = await self._analyze_resource_metric(data, 'cpu_usage', 'CPU')
                patterns.extend(cpu_patterns)
            
            # Memory usage patterns
            if 'memory_usage' in data.columns:
                memory_patterns = await self._analyze_resource_metric(data, 'memory_usage', 'Memory')
                patterns.extend(memory_patterns)
            
            # Resource efficiency patterns
            if 'resource_efficiency' in data.columns:
                efficiency_patterns = await self._analyze_resource_metric(data, 'resource_efficiency', 'Efficiency')
                patterns.extend(efficiency_patterns)
            
            logger.debug(f"Found {len(patterns)} resource patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting resource patterns: {e}")
            return []
    
    async def _detect_error_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect error and failure patterns."""
        logger.debug("Detecting error patterns")
        
        try:
            patterns = []
            
            # Error frequency patterns
            if 'has_error' in data.columns:
                error_rate = data['has_error'].mean()
                if error_rate > 0.1:  # More than 10% error rate
                    pattern = Pattern(
                        id="",
                        pattern_type=PatternType.ERROR_FREQUENCY,
                        pattern_data={
                            'error_rate': error_rate,
                            'total_errors': data['has_error'].sum(),
                            'pattern_description': f'High error rate detected: {error_rate:.2%}'
                        },
                        significance_score=error_rate,
                        detected_at=datetime.utcnow(),
                        frequency=int(data['has_error'].sum()),
                        impact_score=error_rate * 0.8  # High impact for errors
                    )
                    patterns.append(pattern)
            
            # Success rate patterns
            if 'success_rate' in data.columns:
                avg_success_rate = data['success_rate'].mean()
                if avg_success_rate < 0.9:  # Less than 90% success rate
                    pattern = Pattern(
                        id="",
                        pattern_type=PatternType.TASK_PERFORMANCE,
                        pattern_data={
                            'success_rate': avg_success_rate,
                            'pattern_description': f'Low success rate detected: {avg_success_rate:.2%}'
                        },
                        significance_score=1 - avg_success_rate,
                        detected_at=datetime.utcnow(),
                        frequency=len(data),
                        impact_score=(1 - avg_success_rate) * 0.9
                    )
                    patterns.append(pattern)
            
            logger.debug(f"Found {len(patterns)} error patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting error patterns: {e}")
            return []
    
    async def _analyze_resource_metric(self, data: pd.DataFrame, metric_col: str, metric_name: str) -> List[Pattern]:
        """Analyze a specific resource metric for patterns."""
        patterns = []
        
        try:
            if metric_col not in data.columns:
                return patterns
            
            metric_data = data[metric_col].dropna()
            if len(metric_data) == 0:
                return patterns
            
            # High usage pattern
            high_threshold = 0.8
            high_usage_rate = (metric_data > high_threshold).mean()
            
            if high_usage_rate > 0.2:  # More than 20% high usage
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.RESOURCE_USAGE,
                    pattern_data={
                        'metric': metric_name,
                        'high_usage_rate': high_usage_rate,
                        'average_usage': metric_data.mean(),
                        'max_usage': metric_data.max(),
                        'pattern_description': f'High {metric_name} usage pattern: {high_usage_rate:.2%} of time above {high_threshold}'
                    },
                    significance_score=high_usage_rate,
                    detected_at=datetime.utcnow(),
                    frequency=int((metric_data > high_threshold).sum()),
                    impact_score=high_usage_rate * 0.7
                )
                patterns.append(pattern)
            
            # Variability pattern
            cv = metric_data.std() / metric_data.mean() if metric_data.mean() > 0 else 0
            if cv > 0.5:  # High coefficient of variation
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.RESOURCE_USAGE,
                    pattern_data={
                        'metric': metric_name,
                        'coefficient_of_variation': cv,
                        'std_dev': metric_data.std(),
                        'mean': metric_data.mean(),
                        'pattern_description': f'High {metric_name} variability: CV = {cv:.2f}'
                    },
                    significance_score=min(cv, 1.0),
                    detected_at=datetime.utcnow(),
                    frequency=len(metric_data),
                    impact_score=min(cv * 0.5, 1.0)
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing {metric_name} metric: {e}")
            return []
    
    async def _filter_significant_patterns(self, patterns: List[Pattern]) -> List[Pattern]:
        """Filter patterns by significance threshold."""
        threshold = self.config.pattern_significance_threshold
        
        significant_patterns = [
            pattern for pattern in patterns 
            if pattern.significance_score >= threshold
        ]
        
        logger.debug(f"Filtered {len(significant_patterns)} significant patterns from {len(patterns)} total")
        return significant_patterns
    
    async def _calculate_significance_score(self, pattern: Pattern) -> float:
        """Calculate statistical significance score for a pattern."""
        try:
            # Base significance from pattern data
            base_score = pattern.significance_score
            
            # Adjust based on frequency
            frequency_factor = min(pattern.frequency / 100, 1.0)  # Normalize frequency
            
            # Adjust based on pattern type importance
            type_weights = {
                PatternType.ERROR_FREQUENCY: 1.0,
                PatternType.TASK_PERFORMANCE: 0.9,
                PatternType.RESOURCE_USAGE: 0.8,
                PatternType.PIPELINE_EFFICIENCY: 0.8,
                PatternType.WORKFLOW_OPTIMIZATION: 0.7,
                PatternType.TEMPORAL_TREND: 0.6,
            }
            
            type_weight = type_weights.get(pattern.pattern_type, 0.5)
            
            # Calculate final significance score
            significance = base_score * type_weight * (0.7 + 0.3 * frequency_factor)
            
            return min(significance, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating significance score: {e}")
            return pattern.significance_score
    
    async def _calculate_impact_score(self, pattern: Pattern) -> float:
        """Calculate business impact score for a pattern."""
        try:
            # Base impact from pattern data
            base_impact = pattern.impact_score
            
            # Adjust based on pattern type business impact
            impact_multipliers = {
                PatternType.ERROR_FREQUENCY: 1.0,      # High business impact
                PatternType.TASK_PERFORMANCE: 0.9,     # High impact
                PatternType.PIPELINE_EFFICIENCY: 0.8,  # Medium-high impact
                PatternType.RESOURCE_USAGE: 0.7,       # Medium impact
                PatternType.WORKFLOW_OPTIMIZATION: 0.6, # Medium impact
                PatternType.TEMPORAL_TREND: 0.4,       # Lower impact
            }
            
            multiplier = impact_multipliers.get(pattern.pattern_type, 0.5)
            
            # Calculate final impact score
            impact = base_impact * multiplier
            
            return min(impact, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating impact score: {e}")
            return pattern.impact_score
    
    async def _calculate_confidence_score(self, pattern: Pattern) -> float:
        """Calculate confidence score for pattern detection."""
        try:
            # Base confidence from frequency and significance
            frequency_confidence = min(pattern.frequency / 50, 1.0)  # More frequent = higher confidence
            significance_confidence = pattern.significance_score
            
            # Combine confidence factors
            confidence = (frequency_confidence + significance_confidence) / 2
            
            # Adjust based on data quality (if available in pattern data)
            if 'data_quality' in pattern.pattern_data:
                data_quality = pattern.pattern_data['data_quality']
                confidence *= data_quality
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5  # Default confidence

