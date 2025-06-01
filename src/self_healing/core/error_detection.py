"""
Self-Healing Architecture - Error Detection Module
Core error detection and classification system for automated recovery.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class ErrorSeverity(Enum):
    """Error severity levels for classification and prioritization."""
    CRITICAL = 1    # System-wide failure, immediate action required
    HIGH = 2        # Service degradation, automated recovery triggered
    MEDIUM = 3      # Performance impact, monitoring increased
    LOW = 4         # Minor issues, logged for pattern analysis
    INFO = 5        # Informational, no action required


class ErrorCategory(Enum):
    """Error categories for targeted recovery strategies."""
    AUTHENTICATION = "auth"
    DATABASE = "db"
    API = "api"
    PERFORMANCE = "perf"
    INTEGRATION = "integration"
    RESOURCE = "resource"
    CONFIGURATION = "config"
    NETWORK = "network"


@dataclass
class ErrorEvent:
    """Structured representation of a system error event."""
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    source_component: str
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    fingerprint: Optional[str] = None
    
    def __post_init__(self):
        """Generate fingerprint for error deduplication."""
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()
    
    def _generate_fingerprint(self) -> str:
        """Generate unique fingerprint for error deduplication."""
        fingerprint_data = {
            "category": self.category.value,
            "source_component": self.source_component,
            "message_hash": hashlib.md5(self.message.encode()).hexdigest()[:16]
        }
        
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error event to dictionary for storage/transmission."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        data['category'] = self.category.value
        return data


@dataclass
class DetectionResult:
    """Result of error detection analysis."""
    requires_attention: bool
    confidence: float
    detection_methods: List[str]
    metadata: Dict[str, Any]
    recommended_actions: List[str]


class ErrorDetector(ABC):
    """Abstract base class for error detection algorithms."""
    
    @abstractmethod
    async def analyze(self, error_event: ErrorEvent) -> DetectionResult:
        """Analyze error event and return detection result."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return detector name for logging and metrics."""
        pass


class ThresholdDetector(ErrorDetector):
    """Threshold-based error detection using configurable rules."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.error_counts = {}
        self.logger = logging.getLogger(__name__)
    
    async def analyze(self, error_event: ErrorEvent) -> DetectionResult:
        """Analyze error using threshold-based rules."""
        component = error_event.source_component
        current_time = datetime.now()
        
        # Initialize component tracking if needed
        if component not in self.error_counts:
            self.error_counts[component] = []
        
        # Add current error to tracking
        self.error_counts[component].append(current_time)
        
        # Clean old entries (older than time window)
        time_window = timedelta(minutes=self.config.get('time_window_minutes', 5))
        cutoff_time = current_time - time_window
        self.error_counts[component] = [
            t for t in self.error_counts[component] if t > cutoff_time
        ]
        
        # Check thresholds
        error_count = len(self.error_counts[component])
        threshold = self.config.get('error_threshold', 5)
        
        requires_attention = error_count >= threshold
        confidence = min(1.0, error_count / threshold)
        
        recommended_actions = []
        if requires_attention:
            if error_event.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                recommended_actions.append("immediate_recovery")
            else:
                recommended_actions.append("investigate_pattern")
        
        return DetectionResult(
            requires_attention=requires_attention,
            confidence=confidence,
            detection_methods=["threshold"],
            metadata={
                "error_count": error_count,
                "threshold": threshold,
                "time_window_minutes": self.config.get('time_window_minutes', 5)
            },
            recommended_actions=recommended_actions
        )
    
    def get_name(self) -> str:
        return "threshold_detector"


class AnomalyDetector(ErrorDetector):
    """ML-based anomaly detection using Isolation Forest."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = IsolationForest(
            contamination=config.get('contamination', 0.1),
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_history = []
        self.logger = logging.getLogger(__name__)
    
    async def analyze(self, error_event: ErrorEvent) -> DetectionResult:
        """Analyze error using ML-based anomaly detection."""
        features = self._extract_features(error_event)
        
        if not self.is_trained:
            # Collect features for initial training
            self.feature_history.append(features)
            
            # Train model when we have enough data
            if len(self.feature_history) >= self.config.get('min_training_samples', 100):
                await self._train_model()
            
            # Return neutral result until trained
            return DetectionResult(
                requires_attention=False,
                confidence=0.0,
                detection_methods=["anomaly_untrained"],
                metadata={"training_samples": len(self.feature_history)},
                recommended_actions=[]
            )
        
        # Predict anomaly
        features_scaled = self.scaler.transform([features])
        anomaly_score = self.model.decision_function(features_scaled)[0]
        is_anomaly = self.model.predict(features_scaled)[0] == -1
        
        # Convert anomaly score to confidence (higher negative score = more anomalous)
        confidence = max(0.0, min(1.0, abs(anomaly_score) / 2.0)) if is_anomaly else 0.0
        
        recommended_actions = []
        if is_anomaly and confidence > 0.7:
            recommended_actions.append("investigate_anomaly")
        
        return DetectionResult(
            requires_attention=is_anomaly,
            confidence=confidence,
            detection_methods=["anomaly_ml"],
            metadata={
                "anomaly_score": float(anomaly_score),
                "is_anomaly": is_anomaly,
                "features": features
            },
            recommended_actions=recommended_actions
        )
    
    def _extract_features(self, error_event: ErrorEvent) -> List[float]:
        """Extract numerical features from error event for ML analysis."""
        features = [
            # Severity as numerical value
            error_event.severity.value,
            
            # Time-based features
            error_event.timestamp.hour,
            error_event.timestamp.weekday(),
            
            # Message length
            len(error_event.message),
            
            # Stack trace presence and length
            1.0 if error_event.stack_trace else 0.0,
            len(error_event.stack_trace) if error_event.stack_trace else 0.0,
            
            # Context complexity
            len(error_event.context) if error_event.context else 0.0,
            
            # Component hash (for categorical encoding)
            hash(error_event.source_component) % 1000 / 1000.0
        ]
        
        return features
    
    async def _train_model(self):
        """Train the anomaly detection model with collected features."""
        try:
            features_array = np.array(self.feature_history)
            features_scaled = self.scaler.fit_transform(features_array)
            self.model.fit(features_scaled)
            self.is_trained = True
            self.logger.info(f"Anomaly detection model trained with {len(self.feature_history)} samples")
        except Exception as e:
            self.logger.error(f"Failed to train anomaly detection model: {e}")
    
    def get_name(self) -> str:
        return "anomaly_detector"


class PatternDetector(ErrorDetector):
    """Pattern-based error detection using historical analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pattern_cache = {}
        self.error_history = []
        self.logger = logging.getLogger(__name__)
    
    async def analyze(self, error_event: ErrorEvent) -> DetectionResult:
        """Analyze error using pattern recognition."""
        # Add to history
        self.error_history.append(error_event)
        
        # Keep only recent history
        max_history = self.config.get('max_history_size', 1000)
        if len(self.error_history) > max_history:
            self.error_history = self.error_history[-max_history:]
        
        # Look for patterns
        patterns_found = await self._detect_patterns(error_event)
        
        requires_attention = len(patterns_found) > 0
        confidence = min(1.0, len(patterns_found) * 0.3)
        
        recommended_actions = []
        if patterns_found:
            if any(p['severity'] == 'high' for p in patterns_found):
                recommended_actions.append("pattern_based_recovery")
            else:
                recommended_actions.append("monitor_pattern")
        
        return DetectionResult(
            requires_attention=requires_attention,
            confidence=confidence,
            detection_methods=["pattern"],
            metadata={
                "patterns_found": patterns_found,
                "history_size": len(self.error_history)
            },
            recommended_actions=recommended_actions
        )
    
    async def _detect_patterns(self, current_error: ErrorEvent) -> List[Dict[str, Any]]:
        """Detect patterns in error history."""
        patterns = []
        
        # Pattern 1: Rapid succession of similar errors
        similar_errors = [
            e for e in self.error_history[-10:]  # Last 10 errors
            if (e.category == current_error.category and 
                e.source_component == current_error.source_component)
        ]
        
        if len(similar_errors) >= 3:
            time_span = (similar_errors[-1].timestamp - similar_errors[0].timestamp).total_seconds()
            if time_span < 300:  # 5 minutes
                patterns.append({
                    "type": "rapid_succession",
                    "severity": "high",
                    "count": len(similar_errors),
                    "time_span_seconds": time_span
                })
        
        # Pattern 2: Escalating severity
        recent_errors = self.error_history[-5:]
        if len(recent_errors) >= 3:
            severities = [e.severity.value for e in recent_errors]
            if all(severities[i] >= severities[i+1] for i in range(len(severities)-1)):
                patterns.append({
                    "type": "escalating_severity",
                    "severity": "medium",
                    "severity_sequence": severities
                })
        
        # Pattern 3: Cross-component cascade
        recent_components = set(e.source_component for e in self.error_history[-10:])
        if len(recent_components) >= 3:
            patterns.append({
                "type": "cross_component_cascade",
                "severity": "high",
                "affected_components": list(recent_components)
            })
        
        return patterns
    
    def get_name(self) -> str:
        return "pattern_detector"


class ErrorDetectionEngine:
    """Main error detection engine coordinating multiple detection methods."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.detectors: List[ErrorDetector] = []
        self.logger = logging.getLogger(__name__)
        self.detection_callbacks: List[Callable] = []
        
        # Initialize detectors based on configuration
        self._initialize_detectors()
    
    def _initialize_detectors(self):
        """Initialize detection algorithms based on configuration."""
        detector_configs = self.config.get('detectors', {})
        
        if detector_configs.get('threshold', {}).get('enabled', True):
            self.detectors.append(ThresholdDetector(detector_configs.get('threshold', {})))
        
        if detector_configs.get('anomaly', {}).get('enabled', True):
            self.detectors.append(AnomalyDetector(detector_configs.get('anomaly', {})))
        
        if detector_configs.get('pattern', {}).get('enabled', True):
            self.detectors.append(PatternDetector(detector_configs.get('pattern', {})))
        
        self.logger.info(f"Initialized {len(self.detectors)} error detectors")
    
    def add_detection_callback(self, callback: Callable[[ErrorEvent, DetectionResult], None]):
        """Add callback to be called when significant errors are detected."""
        self.detection_callbacks.append(callback)
    
    async def process_error(self, error_event: ErrorEvent) -> DetectionResult:
        """Process error through all detection methods and return aggregated result."""
        try:
            # Run all detectors in parallel
            detection_tasks = [
                detector.analyze(error_event) for detector in self.detectors
            ]
            
            detection_results = await asyncio.gather(*detection_tasks, return_exceptions=True)
            
            # Filter out exceptions and log them
            valid_results = []
            for i, result in enumerate(detection_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Detector {self.detectors[i].get_name()} failed: {result}")
                else:
                    valid_results.append(result)
            
            # Aggregate results
            aggregated_result = self._aggregate_detection_results(valid_results)
            
            # Trigger callbacks if attention required
            if aggregated_result.requires_attention:
                for callback in self.detection_callbacks:
                    try:
                        await callback(error_event, aggregated_result)
                    except Exception as e:
                        self.logger.error(f"Detection callback failed: {e}")
            
            return aggregated_result
            
        except Exception as e:
            self.logger.error(f"Error detection processing failed: {e}")
            return DetectionResult(
                requires_attention=True,  # Fail safe - assume attention needed
                confidence=0.5,
                detection_methods=["error_fallback"],
                metadata={"error": str(e)},
                recommended_actions=["manual_investigation"]
            )
    
    def _aggregate_detection_results(self, results: List[DetectionResult]) -> DetectionResult:
        """Aggregate multiple detection results into a single result."""
        if not results:
            return DetectionResult(
                requires_attention=False,
                confidence=0.0,
                detection_methods=[],
                metadata={},
                recommended_actions=[]
            )
        
        # Aggregate attention requirement (any detector requiring attention)
        requires_attention = any(r.requires_attention for r in results)
        
        # Aggregate confidence (weighted average)
        total_confidence = sum(r.confidence for r in results)
        avg_confidence = total_confidence / len(results)
        
        # Combine detection methods
        all_methods = []
        for r in results:
            all_methods.extend(r.detection_methods)
        
        # Combine recommended actions (deduplicated)
        all_actions = set()
        for r in results:
            all_actions.update(r.recommended_actions)
        
        # Combine metadata
        combined_metadata = {
            "detector_count": len(results),
            "individual_results": [
                {
                    "methods": r.detection_methods,
                    "confidence": r.confidence,
                    "attention": r.requires_attention
                }
                for r in results
            ]
        }
        
        return DetectionResult(
            requires_attention=requires_attention,
            confidence=avg_confidence,
            detection_methods=list(set(all_methods)),
            metadata=combined_metadata,
            recommended_actions=list(all_actions)
        )


# Example usage and integration
async def example_usage():
    """Example of how to use the error detection system."""
    
    # Configuration
    config = {
        "detectors": {
            "threshold": {
                "enabled": True,
                "error_threshold": 5,
                "time_window_minutes": 5
            },
            "anomaly": {
                "enabled": True,
                "contamination": 0.1,
                "min_training_samples": 50
            },
            "pattern": {
                "enabled": True,
                "max_history_size": 1000
            }
        }
    }
    
    # Initialize detection engine
    detection_engine = ErrorDetectionEngine(config)
    
    # Add callback for handling detected issues
    async def handle_detection(error_event: ErrorEvent, result: DetectionResult):
        print(f"Attention required for error: {error_event.message}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Recommended actions: {result.recommended_actions}")
    
    detection_engine.add_detection_callback(handle_detection)
    
    # Example error events
    error_events = [
        ErrorEvent(
            timestamp=datetime.now(),
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            message="Connection timeout to database",
            source_component="user_service"
        ),
        ErrorEvent(
            timestamp=datetime.now(),
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.API,
            message="API endpoint returning 500 errors",
            source_component="api_gateway"
        )
    ]
    
    # Process errors
    for error_event in error_events:
        result = await detection_engine.process_error(error_event)
        print(f"Processed error: {error_event.message}")
        print(f"Detection result: {result}")
        print("---")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run example
    asyncio.run(example_usage())

