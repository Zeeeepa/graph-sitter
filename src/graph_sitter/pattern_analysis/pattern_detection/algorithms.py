"""Pattern detection algorithms for different types of patterns."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
from scipy.signal import find_peaks

from ..models import Pattern, PatternType

logger = logging.getLogger(__name__)


class PerformancePatternDetector:
    """Detector for performance-related patterns."""
    
    def __init__(self):
        """Initialize performance pattern detector."""
        self.scaler = StandardScaler()
        logger.debug("PerformancePatternDetector initialized")
    
    async def detect(self, data: pd.DataFrame) -> List[Pattern]:
        """
        Detect performance patterns in the data.
        
        Args:
            data: DataFrame with performance metrics
            
        Returns:
            List of detected performance patterns
        """
        patterns = []
        
        try:
            # Task duration patterns
            if 'duration' in data.columns:
                duration_patterns = await self._detect_duration_patterns(data)
                patterns.extend(duration_patterns)
            
            # Throughput patterns
            if 'throughput' in data.columns:
                throughput_patterns = await self._detect_throughput_patterns(data)
                patterns.extend(throughput_patterns)
            
            # Success rate patterns
            if 'success_rate' in data.columns:
                success_patterns = await self._detect_success_patterns(data)
                patterns.extend(success_patterns)
            
            # Efficiency patterns
            if 'resource_efficiency' in data.columns:
                efficiency_patterns = await self._detect_efficiency_patterns(data)
                patterns.extend(efficiency_patterns)
            
            logger.debug(f"PerformancePatternDetector found {len(patterns)} patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error in performance pattern detection: {e}")
            return []
    
    async def _detect_duration_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect patterns in task duration."""
        patterns = []
        
        try:
            duration_data = data['duration'].dropna()
            if len(duration_data) < 10:
                return patterns
            
            # Detect slow tasks pattern
            slow_threshold = duration_data.quantile(0.9)
            slow_tasks_rate = (duration_data > slow_threshold).mean()
            
            if slow_tasks_rate > 0.15:  # More than 15% slow tasks
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.TASK_PERFORMANCE,
                    pattern_data={
                        'pattern_name': 'slow_tasks',
                        'slow_threshold': slow_threshold,
                        'slow_tasks_rate': slow_tasks_rate,
                        'avg_duration': duration_data.mean(),
                        'max_duration': duration_data.max(),
                        'description': f'High rate of slow tasks: {slow_tasks_rate:.2%} exceed {slow_threshold:.1f}s'
                    },
                    significance_score=slow_tasks_rate,
                    detected_at=datetime.utcnow(),
                    frequency=int((duration_data > slow_threshold).sum()),
                    impact_score=slow_tasks_rate * 0.8
                )
                patterns.append(pattern)
            
            # Detect duration variability pattern
            cv = duration_data.std() / duration_data.mean() if duration_data.mean() > 0 else 0
            if cv > 1.0:  # High variability
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.TASK_PERFORMANCE,
                    pattern_data={
                        'pattern_name': 'duration_variability',
                        'coefficient_of_variation': cv,
                        'std_dev': duration_data.std(),
                        'mean_duration': duration_data.mean(),
                        'description': f'High duration variability: CV = {cv:.2f}'
                    },
                    significance_score=min(cv / 2, 1.0),
                    detected_at=datetime.utcnow(),
                    frequency=len(duration_data),
                    impact_score=min(cv * 0.3, 1.0)
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting duration patterns: {e}")
            return []
    
    async def _detect_throughput_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect patterns in throughput metrics."""
        patterns = []
        
        try:
            throughput_data = data['throughput'].dropna()
            if len(throughput_data) < 10:
                return patterns
            
            # Detect low throughput pattern
            low_threshold = throughput_data.quantile(0.25)
            low_throughput_rate = (throughput_data < low_threshold).mean()
            
            if low_throughput_rate > 0.3:  # More than 30% low throughput
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.PIPELINE_EFFICIENCY,
                    pattern_data={
                        'pattern_name': 'low_throughput',
                        'low_threshold': low_threshold,
                        'low_throughput_rate': low_throughput_rate,
                        'avg_throughput': throughput_data.mean(),
                        'min_throughput': throughput_data.min(),
                        'description': f'Frequent low throughput: {low_throughput_rate:.2%} below {low_threshold:.1f}'
                    },
                    significance_score=low_throughput_rate,
                    detected_at=datetime.utcnow(),
                    frequency=int((throughput_data < low_threshold).sum()),
                    impact_score=low_throughput_rate * 0.7
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting throughput patterns: {e}")
            return []
    
    async def _detect_success_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect patterns in success rates."""
        patterns = []
        
        try:
            success_data = data['success_rate'].dropna()
            if len(success_data) < 5:
                return patterns
            
            avg_success_rate = success_data.mean()
            
            # Detect low success rate pattern
            if avg_success_rate < 0.95:  # Less than 95% success rate
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.TASK_PERFORMANCE,
                    pattern_data={
                        'pattern_name': 'low_success_rate',
                        'avg_success_rate': avg_success_rate,
                        'min_success_rate': success_data.min(),
                        'failure_rate': 1 - avg_success_rate,
                        'description': f'Low success rate: {avg_success_rate:.2%} average'
                    },
                    significance_score=1 - avg_success_rate,
                    detected_at=datetime.utcnow(),
                    frequency=len(success_data),
                    impact_score=(1 - avg_success_rate) * 0.9
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting success patterns: {e}")
            return []
    
    async def _detect_efficiency_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect patterns in resource efficiency."""
        patterns = []
        
        try:
            efficiency_data = data['resource_efficiency'].dropna()
            if len(efficiency_data) < 10:
                return patterns
            
            avg_efficiency = efficiency_data.mean()
            
            # Detect low efficiency pattern
            if avg_efficiency < 0.7:  # Less than 70% efficiency
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.RESOURCE_USAGE,
                    pattern_data={
                        'pattern_name': 'low_efficiency',
                        'avg_efficiency': avg_efficiency,
                        'min_efficiency': efficiency_data.min(),
                        'efficiency_loss': 1 - avg_efficiency,
                        'description': f'Low resource efficiency: {avg_efficiency:.2%} average'
                    },
                    significance_score=1 - avg_efficiency,
                    detected_at=datetime.utcnow(),
                    frequency=len(efficiency_data),
                    impact_score=(1 - avg_efficiency) * 0.6
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting efficiency patterns: {e}")
            return []


class AnomalyDetector:
    """Detector for anomalous patterns and outliers."""
    
    def __init__(self):
        """Initialize anomaly detector."""
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        logger.debug("AnomalyDetector initialized")
    
    async def detect(self, data: pd.DataFrame) -> List[Pattern]:
        """
        Detect anomalous patterns in the data.
        
        Args:
            data: DataFrame with metrics
            
        Returns:
            List of detected anomaly patterns
        """
        patterns = []
        
        try:
            # Select numerical columns for anomaly detection
            numerical_cols = data.select_dtypes(include=[np.number]).columns
            if len(numerical_cols) == 0:
                return patterns
            
            # Prepare data for anomaly detection
            anomaly_data = data[numerical_cols].dropna()
            if len(anomaly_data) < 20:
                return patterns
            
            # Detect anomalies using Isolation Forest
            anomalies = self.isolation_forest.fit_predict(anomaly_data)
            anomaly_indices = np.where(anomalies == -1)[0]
            
            if len(anomaly_indices) > 0:
                anomaly_rate = len(anomaly_indices) / len(anomaly_data)
                
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.RESOURCE_USAGE,  # Could be any type
                    pattern_data={
                        'pattern_name': 'anomalous_behavior',
                        'anomaly_count': len(anomaly_indices),
                        'anomaly_rate': anomaly_rate,
                        'total_records': len(anomaly_data),
                        'anomaly_indices': anomaly_indices.tolist()[:10],  # First 10 indices
                        'description': f'Anomalous behavior detected: {len(anomaly_indices)} anomalies ({anomaly_rate:.2%})'
                    },
                    significance_score=min(anomaly_rate * 5, 1.0),  # Scale up for visibility
                    detected_at=datetime.utcnow(),
                    frequency=len(anomaly_indices),
                    impact_score=min(anomaly_rate * 3, 1.0)
                )
                patterns.append(pattern)
            
            # Detect statistical outliers for specific metrics
            outlier_patterns = await self._detect_statistical_outliers(data)
            patterns.extend(outlier_patterns)
            
            logger.debug(f"AnomalyDetector found {len(patterns)} patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return []
    
    async def _detect_statistical_outliers(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect statistical outliers using z-score method."""
        patterns = []
        
        try:
            numerical_cols = ['duration', 'cpu_usage', 'memory_usage', 'throughput']
            
            for col in numerical_cols:
                if col not in data.columns:
                    continue
                
                col_data = data[col].dropna()
                if len(col_data) < 10:
                    continue
                
                # Calculate z-scores
                z_scores = np.abs(stats.zscore(col_data))
                outliers = z_scores > 3  # 3-sigma rule
                
                if outliers.sum() > 0:
                    outlier_rate = outliers.mean()
                    
                    if outlier_rate > 0.05:  # More than 5% outliers
                        pattern = Pattern(
                            id="",
                            pattern_type=PatternType.RESOURCE_USAGE,
                            pattern_data={
                                'pattern_name': f'{col}_outliers',
                                'metric': col,
                                'outlier_count': int(outliers.sum()),
                                'outlier_rate': outlier_rate,
                                'max_z_score': float(z_scores.max()),
                                'description': f'Statistical outliers in {col}: {outlier_rate:.2%} of values'
                            },
                            significance_score=min(outlier_rate * 2, 1.0),
                            detected_at=datetime.utcnow(),
                            frequency=int(outliers.sum()),
                            impact_score=min(outlier_rate * 1.5, 1.0)
                        )
                        patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting statistical outliers: {e}")
            return []


class TrendAnalyzer:
    """Analyzer for trend patterns in time series data."""
    
    def __init__(self):
        """Initialize trend analyzer."""
        logger.debug("TrendAnalyzer initialized")
    
    async def detect(self, data: pd.DataFrame) -> List[Pattern]:
        """
        Detect trend patterns in time series data.
        
        Args:
            data: DataFrame with time series data
            
        Returns:
            List of detected trend patterns
        """
        patterns = []
        
        try:
            if 'timestamp' not in data.columns:
                return patterns
            
            # Sort by timestamp
            data_sorted = data.sort_values('timestamp')
            
            # Detect trends in various metrics
            metrics = ['duration', 'cpu_usage', 'memory_usage', 'throughput', 'success_rate']
            
            for metric in metrics:
                if metric not in data_sorted.columns:
                    continue
                
                trend_patterns = await self._analyze_metric_trend(data_sorted, metric)
                patterns.extend(trend_patterns)
            
            logger.debug(f"TrendAnalyzer found {len(patterns)} patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return []
    
    async def _analyze_metric_trend(self, data: pd.DataFrame, metric: str) -> List[Pattern]:
        """Analyze trend for a specific metric."""
        patterns = []
        
        try:
            metric_data = data[metric].dropna()
            if len(metric_data) < 10:
                return patterns
            
            # Calculate trend using linear regression
            x = np.arange(len(metric_data))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, metric_data)
            
            # Determine trend significance
            if abs(r_value) > 0.3 and p_value < 0.05:  # Significant correlation
                trend_direction = 'increasing' if slope > 0 else 'decreasing'
                trend_strength = abs(r_value)
                
                pattern = Pattern(
                    id="",
                    pattern_type=PatternType.TEMPORAL_TREND,
                    pattern_data={
                        'pattern_name': f'{metric}_trend',
                        'metric': metric,
                        'trend_direction': trend_direction,
                        'slope': slope,
                        'correlation': r_value,
                        'p_value': p_value,
                        'trend_strength': trend_strength,
                        'description': f'{trend_direction.title()} trend in {metric}: r={r_value:.3f}, p={p_value:.3f}'
                    },
                    significance_score=trend_strength,
                    detected_at=datetime.utcnow(),
                    frequency=len(metric_data),
                    impact_score=trend_strength * 0.6
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing trend for {metric}: {e}")
            return []


class SeasonalityDetector:
    """Detector for seasonal patterns in time series data."""
    
    def __init__(self):
        """Initialize seasonality detector."""
        logger.debug("SeasonalityDetector initialized")
    
    async def detect(self, data: pd.DataFrame) -> List[Pattern]:
        """
        Detect seasonal patterns in time series data.
        
        Args:
            data: DataFrame with time series data
            
        Returns:
            List of detected seasonal patterns
        """
        patterns = []
        
        try:
            if 'timestamp' not in data.columns:
                return patterns
            
            # Ensure timestamp is datetime
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data_sorted = data.sort_values('timestamp')
            
            # Check if we have enough data for seasonality analysis
            time_span = (data_sorted['timestamp'].max() - data_sorted['timestamp'].min()).days
            if time_span < 7:  # Need at least a week of data
                return patterns
            
            # Detect hourly patterns
            hourly_patterns = await self._detect_hourly_patterns(data_sorted)
            patterns.extend(hourly_patterns)
            
            # Detect daily patterns (if we have enough data)
            if time_span >= 14:
                daily_patterns = await self._detect_daily_patterns(data_sorted)
                patterns.extend(daily_patterns)
            
            logger.debug(f"SeasonalityDetector found {len(patterns)} patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error in seasonality detection: {e}")
            return []
    
    async def _detect_hourly_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect hourly seasonal patterns."""
        patterns = []
        
        try:
            # Group by hour and calculate statistics
            data['hour'] = data['timestamp'].dt.hour
            hourly_stats = data.groupby('hour').agg({
                'duration': ['mean', 'count'],
                'cpu_usage': 'mean',
                'memory_usage': 'mean'
            }).fillna(0)
            
            # Flatten column names
            hourly_stats.columns = ['_'.join(col).strip() for col in hourly_stats.columns]
            
            # Check for significant hourly variation
            if 'duration_mean' in hourly_stats.columns:
                duration_cv = hourly_stats['duration_mean'].std() / hourly_stats['duration_mean'].mean()
                
                if duration_cv > 0.3:  # Significant hourly variation
                    peak_hour = hourly_stats['duration_mean'].idxmax()
                    low_hour = hourly_stats['duration_mean'].idxmin()
                    
                    pattern = Pattern(
                        id="",
                        pattern_type=PatternType.TEMPORAL_TREND,
                        pattern_data={
                            'pattern_name': 'hourly_duration_pattern',
                            'metric': 'duration',
                            'peak_hour': int(peak_hour),
                            'low_hour': int(low_hour),
                            'coefficient_of_variation': duration_cv,
                            'hourly_stats': hourly_stats['duration_mean'].to_dict(),
                            'description': f'Hourly duration pattern: peak at {peak_hour}:00, low at {low_hour}:00'
                        },
                        significance_score=min(duration_cv, 1.0),
                        detected_at=datetime.utcnow(),
                        frequency=24,  # 24 hours
                        impact_score=min(duration_cv * 0.5, 1.0)
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting hourly patterns: {e}")
            return []
    
    async def _detect_daily_patterns(self, data: pd.DataFrame) -> List[Pattern]:
        """Detect daily seasonal patterns."""
        patterns = []
        
        try:
            # Group by day of week
            data['day_of_week'] = data['timestamp'].dt.dayofweek
            daily_stats = data.groupby('day_of_week').agg({
                'duration': ['mean', 'count'],
                'throughput': 'mean',
                'success_rate': 'mean'
            }).fillna(0)
            
            # Flatten column names
            daily_stats.columns = ['_'.join(col).strip() for col in daily_stats.columns]
            
            # Check for weekend vs weekday patterns
            if 'duration_mean' in daily_stats.columns:
                weekday_avg = daily_stats.loc[0:4, 'duration_mean'].mean()  # Mon-Fri
                weekend_avg = daily_stats.loc[5:6, 'duration_mean'].mean()  # Sat-Sun
                
                if abs(weekday_avg - weekend_avg) / weekday_avg > 0.2:  # 20% difference
                    pattern_type = 'weekend_slower' if weekend_avg > weekday_avg else 'weekend_faster'
                    
                    pattern = Pattern(
                        id="",
                        pattern_type=PatternType.TEMPORAL_TREND,
                        pattern_data={
                            'pattern_name': 'weekday_weekend_pattern',
                            'metric': 'duration',
                            'weekday_avg': weekday_avg,
                            'weekend_avg': weekend_avg,
                            'difference_ratio': abs(weekday_avg - weekend_avg) / weekday_avg,
                            'pattern_type': pattern_type,
                            'description': f'Weekday vs weekend pattern: {pattern_type.replace("_", " ")}'
                        },
                        significance_score=min(abs(weekday_avg - weekend_avg) / weekday_avg, 1.0),
                        detected_at=datetime.utcnow(),
                        frequency=7,  # 7 days
                        impact_score=min(abs(weekday_avg - weekend_avg) / weekday_avg * 0.4, 1.0)
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting daily patterns: {e}")
            return []

