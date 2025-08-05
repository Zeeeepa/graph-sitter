"""
Error Detection and Classification Engine

Provides real-time error monitoring, intelligent classification,
root cause analysis, and pattern recognition capabilities.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from ..models.error_models import (
    ErrorCategory,
    ErrorClassification,
    ErrorInstance,
    ErrorPattern,
    ErrorSeverity,
    HealingStrategy,
)
from ..utils.pattern_matcher import PatternMatcher
from ..utils.log_analyzer import LogAnalyzer


class ErrorDetector:
    """
    Intelligent error detection and classification system with
    real-time monitoring and pattern recognition capabilities.
    """

    def __init__(self, enable_learning: bool = True):
        self.enable_learning = enable_learning
        self.logger = logging.getLogger(__name__)
        
        # Pattern matching and analysis
        self.pattern_matcher = PatternMatcher()
        self.log_analyzer = LogAnalyzer()
        
        # Error tracking
        self.error_instances: Dict[str, ErrorInstance] = {}
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.pattern_statistics: Dict[str, Dict[str, Any]] = {}
        
        # Learning and adaptation
        self.learning_data: List[Dict[str, Any]] = []
        self.confidence_adjustments: Dict[str, float] = {}
        
        # Initialize built-in patterns
        self._initialize_error_patterns()

    def _initialize_error_patterns(self) -> None:
        """Initialize built-in error patterns."""
        patterns = [
            # Build failures
            ErrorPattern(
                id="build_compilation_error",
                name="Compilation Error",
                category=ErrorCategory.BUILD_FAILURE,
                severity=ErrorSeverity.HIGH,
                patterns=[
                    r"SyntaxError:",
                    r"IndentationError:",
                    r"NameError:",
                    r"TypeError:",
                    r"compilation failed",
                    r"build failed"
                ],
                keywords=["error", "failed", "compilation", "syntax"],
                healing_strategies=[
                    HealingStrategy.RETRY,
                    HealingStrategy.CONFIGURATION_FIX
                ]
            ),
            
            # Test failures
            ErrorPattern(
                id="test_assertion_failure",
                name="Test Assertion Failure",
                category=ErrorCategory.TEST_FAILURE,
                severity=ErrorSeverity.MEDIUM,
                patterns=[
                    r"AssertionError:",
                    r"FAILED.*test_",
                    r"test.*failed",
                    r"assertion failed"
                ],
                keywords=["test", "assertion", "failed", "expected"],
                healing_strategies=[
                    HealingStrategy.RETRY,
                    HealingStrategy.ALTERNATIVE_APPROACH
                ]
            ),
            
            # Dependency issues
            ErrorPattern(
                id="dependency_not_found",
                name="Dependency Not Found",
                category=ErrorCategory.DEPENDENCY_ISSUE,
                severity=ErrorSeverity.HIGH,
                patterns=[
                    r"ModuleNotFoundError:",
                    r"ImportError:",
                    r"No module named",
                    r"package not found",
                    r"dependency.*not found"
                ],
                keywords=["module", "import", "dependency", "package"],
                healing_strategies=[
                    HealingStrategy.DEPENDENCY_UPDATE,
                    HealingStrategy.CONFIGURATION_FIX
                ]
            ),
            
            # Resource exhaustion
            ErrorPattern(
                id="memory_exhaustion",
                name="Memory Exhaustion",
                category=ErrorCategory.RESOURCE_EXHAUSTION,
                severity=ErrorSeverity.CRITICAL,
                patterns=[
                    r"MemoryError:",
                    r"OutOfMemoryError",
                    r"out of memory",
                    r"memory exhausted",
                    r"killed.*memory"
                ],
                keywords=["memory", "oom", "killed", "exhausted"],
                healing_strategies=[
                    HealingStrategy.RESOURCE_ADJUSTMENT,
                    HealingStrategy.RETRY
                ]
            ),
            
            # Network issues
            ErrorPattern(
                id="network_timeout",
                name="Network Timeout",
                category=ErrorCategory.NETWORK_ISSUE,
                severity=ErrorSeverity.MEDIUM,
                patterns=[
                    r"ConnectionTimeoutError",
                    r"TimeoutError",
                    r"connection timed out",
                    r"network timeout",
                    r"request timeout"
                ],
                keywords=["timeout", "connection", "network", "unreachable"],
                healing_strategies=[
                    HealingStrategy.RETRY,
                    HealingStrategy.ALTERNATIVE_APPROACH
                ]
            ),
            
            # Configuration errors
            ErrorPattern(
                id="config_invalid",
                name="Invalid Configuration",
                category=ErrorCategory.CONFIGURATION_ERROR,
                severity=ErrorSeverity.HIGH,
                patterns=[
                    r"ConfigurationError",
                    r"invalid configuration",
                    r"config.*error",
                    r"malformed.*config"
                ],
                keywords=["config", "configuration", "invalid", "malformed"],
                healing_strategies=[
                    HealingStrategy.CONFIGURATION_FIX,
                    HealingStrategy.ROLLBACK
                ]
            ),
            
            # Security violations
            ErrorPattern(
                id="security_violation",
                name="Security Violation",
                category=ErrorCategory.SECURITY_VIOLATION,
                severity=ErrorSeverity.CRITICAL,
                patterns=[
                    r"SecurityError",
                    r"permission denied",
                    r"access denied",
                    r"unauthorized",
                    r"security violation"
                ],
                keywords=["security", "permission", "access", "unauthorized"],
                healing_strategies=[
                    HealingStrategy.ESCALATE_TO_HUMAN,
                    HealingStrategy.CONFIGURATION_FIX
                ]
            )
        ]
        
        for pattern in patterns:
            self.error_patterns[pattern.id] = pattern
            self.pattern_statistics[pattern.id] = {
                "matches": 0,
                "successful_healing": 0,
                "false_positives": 0,
                "last_seen": None
            }

    async def detect_errors(
        self,
        log_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ErrorInstance]:
        """
        Detect errors in log content and classify them.
        
        Args:
            log_content: Log content to analyze
            context: Additional context information
            
        Returns:
            List of detected error instances
        """
        self.logger.info("Starting error detection analysis")
        
        # Parse log content
        log_entries = self.log_analyzer.parse_logs(log_content)
        
        # Detect error entries
        error_entries = self._identify_error_entries(log_entries)
        
        # Create error instances
        error_instances = []
        for entry in error_entries:
            error_instance = await self._create_error_instance(entry, context)
            if error_instance:
                error_instances.append(error_instance)
                self.error_instances[error_instance.id] = error_instance
        
        self.logger.info(f"Detected {len(error_instances)} errors")
        return error_instances

    def _identify_error_entries(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify log entries that contain errors."""
        error_entries = []
        
        error_indicators = [
            "error", "failed", "exception", "traceback",
            "fatal", "critical", "abort", "crash"
        ]
        
        for entry in log_entries:
            message = entry.get("message", "").lower()
            level = entry.get("level", "").lower()
            
            # Check log level
            if level in ["error", "critical", "fatal"]:
                error_entries.append(entry)
                continue
            
            # Check for error indicators in message
            if any(indicator in message for indicator in error_indicators):
                error_entries.append(entry)
                continue
        
        return error_entries

    async def _create_error_instance(
        self,
        log_entry: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ErrorInstance]:
        """Create an error instance from a log entry."""
        error_message = log_entry.get("message", "")
        if not error_message:
            return None
        
        # Generate unique error ID
        error_id = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Extract stack trace if available
        stack_trace = log_entry.get("stack_trace")
        
        # Get surrounding log context
        log_context = self._extract_log_context(log_entry, context)
        
        # Classify the error
        classification = await self.classify_error(error_message, log_context)
        
        # Create error instance
        error_instance = ErrorInstance(
            id=error_id,
            pipeline_id=context.get("pipeline_id", "unknown") if context else "unknown",
            stage=context.get("stage", "unknown") if context else "unknown",
            error_message=error_message,
            stack_trace=stack_trace,
            log_context=log_context,
            classification=classification
        )
        
        return error_instance

    def _extract_log_context(
        self,
        log_entry: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Extract relevant log context around the error."""
        # In a real implementation, this would extract surrounding log lines
        # For now, return basic context
        context_lines = []
        
        if context and "full_logs" in context:
            # Extract lines around the error
            full_logs = context["full_logs"].split("\n")
            error_line = log_entry.get("line_number", 0)
            
            start_line = max(0, error_line - 5)
            end_line = min(len(full_logs), error_line + 5)
            
            context_lines = full_logs[start_line:end_line]
        
        return context_lines

    async def classify_error(
        self,
        error_message: str,
        log_context: List[str]
    ) -> ErrorClassification:
        """
        Classify an error using pattern matching and machine learning.
        
        Args:
            error_message: The error message to classify
            log_context: Surrounding log context
            
        Returns:
            Error classification result
        """
        best_match = None
        best_confidence = 0.0
        matched_patterns = []
        
        # Combine error message and context for analysis
        full_text = error_message + " " + " ".join(log_context)
        
        # Check against all patterns
        for pattern_id, pattern in self.error_patterns.items():
            confidence = await self._calculate_pattern_confidence(pattern, full_text)
            
            if confidence >= pattern.confidence_threshold:
                matched_patterns.append(pattern_id)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = pattern
        
        # Apply confidence adjustments based on learning
        if best_match and best_match.id in self.confidence_adjustments:
            best_confidence *= self.confidence_adjustments[best_match.id]
        
        # Create classification
        if best_match:
            classification = ErrorClassification(
                error_id=f"classification_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                category=best_match.category,
                severity=best_match.severity,
                confidence=best_confidence,
                matched_patterns=matched_patterns,
                context={"full_text": full_text},
                suggested_healing=best_match.healing_strategies
            )
            
            # Update pattern statistics
            self._update_pattern_statistics(best_match.id)
        else:
            # Unknown error
            classification = ErrorClassification(
                error_id=f"classification_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                confidence=0.5,
                matched_patterns=[],
                context={"full_text": full_text},
                suggested_healing=[HealingStrategy.ESCALATE_TO_HUMAN]
            )
        
        return classification

    async def _calculate_pattern_confidence(
        self,
        pattern: ErrorPattern,
        text: str
    ) -> float:
        """Calculate confidence score for a pattern match."""
        confidence_scores = []
        
        # Check regex patterns
        pattern_matches = 0
        for regex_pattern in pattern.patterns:
            if re.search(regex_pattern, text, re.IGNORECASE):
                pattern_matches += 1
        
        if pattern.patterns:
            pattern_score = pattern_matches / len(pattern.patterns)
            confidence_scores.append(pattern_score * 0.6)  # 60% weight
        
        # Check keywords
        keyword_matches = 0
        text_lower = text.lower()
        for keyword in pattern.keywords:
            if keyword.lower() in text_lower:
                keyword_matches += 1
        
        if pattern.keywords:
            keyword_score = keyword_matches / len(pattern.keywords)
            confidence_scores.append(keyword_score * 0.4)  # 40% weight
        
        # Calculate final confidence
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 0.0

    def _update_pattern_statistics(self, pattern_id: str) -> None:
        """Update statistics for a pattern match."""
        if pattern_id in self.pattern_statistics:
            stats = self.pattern_statistics[pattern_id]
            stats["matches"] += 1
            stats["last_seen"] = datetime.now()

    async def analyze_error_trends(
        self,
        time_window: timedelta = timedelta(days=7)
    ) -> Dict[str, Any]:
        """
        Analyze error trends over a time window.
        
        Args:
            time_window: Time window for analysis
            
        Returns:
            Error trend analysis results
        """
        cutoff_time = datetime.now() - time_window
        
        # Filter recent errors
        recent_errors = [
            error for error in self.error_instances.values()
            if error.created_at >= cutoff_time
        ]
        
        # Analyze trends
        category_counts = {}
        severity_counts = {}
        hourly_distribution = {}
        
        for error in recent_errors:
            if error.classification:
                # Category analysis
                category = error.classification.category.value
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # Severity analysis
                severity = error.classification.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Hourly distribution
                hour = error.created_at.hour
                hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        # Calculate resolution rates
        resolved_errors = [e for e in recent_errors if e.resolved]
        resolution_rate = len(resolved_errors) / len(recent_errors) if recent_errors else 0
        
        # Identify patterns with high false positive rates
        problematic_patterns = []
        for pattern_id, stats in self.pattern_statistics.items():
            if stats["matches"] > 0:
                false_positive_rate = stats["false_positives"] / stats["matches"]
                if false_positive_rate > 0.3:  # 30% threshold
                    problematic_patterns.append({
                        "pattern_id": pattern_id,
                        "false_positive_rate": false_positive_rate,
                        "total_matches": stats["matches"]
                    })
        
        return {
            "total_errors": len(recent_errors),
            "resolution_rate": resolution_rate,
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "hourly_distribution": hourly_distribution,
            "problematic_patterns": problematic_patterns,
            "analysis_period": {
                "start": cutoff_time.isoformat(),
                "end": datetime.now().isoformat()
            }
        }

    async def learn_from_feedback(
        self,
        error_id: str,
        classification_correct: bool,
        actual_category: Optional[ErrorCategory] = None,
        healing_success: bool = False
    ) -> None:
        """
        Learn from human feedback to improve classification accuracy.
        
        Args:
            error_id: ID of the error instance
            classification_correct: Whether the classification was correct
            actual_category: The actual error category if classification was wrong
            healing_success: Whether the suggested healing was successful
        """
        if not self.enable_learning:
            return
        
        error_instance = self.error_instances.get(error_id)
        if not error_instance or not error_instance.classification:
            return
        
        classification = error_instance.classification
        
        # Record learning data
        learning_entry = {
            "error_id": error_id,
            "predicted_category": classification.category.value,
            "actual_category": actual_category.value if actual_category else classification.category.value,
            "classification_correct": classification_correct,
            "confidence": classification.confidence,
            "matched_patterns": classification.matched_patterns,
            "healing_success": healing_success,
            "timestamp": datetime.now().isoformat()
        }
        
        self.learning_data.append(learning_entry)
        
        # Update pattern statistics
        for pattern_id in classification.matched_patterns:
            if pattern_id in self.pattern_statistics:
                stats = self.pattern_statistics[pattern_id]
                
                if not classification_correct:
                    stats["false_positives"] += 1
                
                if healing_success:
                    stats["successful_healing"] += 1
        
        # Adjust confidence for patterns
        await self._adjust_pattern_confidence(classification, classification_correct)
        
        self.logger.info(f"Learned from feedback for error {error_id}")

    async def _adjust_pattern_confidence(
        self,
        classification: ErrorClassification,
        was_correct: bool
    ) -> None:
        """Adjust pattern confidence based on feedback."""
        adjustment_factor = 0.1  # 10% adjustment
        
        for pattern_id in classification.matched_patterns:
            current_adjustment = self.confidence_adjustments.get(pattern_id, 1.0)
            
            if was_correct:
                # Increase confidence
                new_adjustment = min(1.5, current_adjustment + adjustment_factor)
            else:
                # Decrease confidence
                new_adjustment = max(0.5, current_adjustment - adjustment_factor)
            
            self.confidence_adjustments[pattern_id] = new_adjustment

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error detection statistics."""
        total_errors = len(self.error_instances)
        resolved_errors = sum(1 for e in self.error_instances.values() if e.resolved)
        
        # Pattern performance
        pattern_performance = {}
        for pattern_id, stats in self.pattern_statistics.items():
            if stats["matches"] > 0:
                pattern_performance[pattern_id] = {
                    "matches": stats["matches"],
                    "success_rate": stats["successful_healing"] / stats["matches"],
                    "false_positive_rate": stats["false_positives"] / stats["matches"],
                    "last_seen": stats["last_seen"].isoformat() if stats["last_seen"] else None
                }
        
        return {
            "total_errors_detected": total_errors,
            "resolution_rate": resolved_errors / total_errors if total_errors > 0 else 0,
            "pattern_performance": pattern_performance,
            "learning_entries": len(self.learning_data),
            "confidence_adjustments": len(self.confidence_adjustments)
        }

    async def predict_error_likelihood(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Predict likelihood of different error types based on context.
        
        Args:
            context: Context information (project type, dependencies, etc.)
            
        Returns:
            Dictionary mapping error categories to likelihood scores
        """
        predictions = {}
        
        # Analyze historical patterns
        for category in ErrorCategory:
            category_errors = [
                e for e in self.error_instances.values()
                if e.classification and e.classification.category == category
            ]
            
            # Base likelihood on historical frequency
            base_likelihood = len(category_errors) / len(self.error_instances) if self.error_instances else 0
            
            # Adjust based on context
            context_multiplier = 1.0
            
            # Project type adjustments
            project_type = context.get("project_type")
            if project_type == "python" and category == ErrorCategory.DEPENDENCY_ISSUE:
                context_multiplier *= 1.5
            elif project_type == "typescript" and category == ErrorCategory.BUILD_FAILURE:
                context_multiplier *= 1.3
            
            # Dependency count adjustments
            dependency_count = context.get("dependency_count", 0)
            if dependency_count > 50 and category == ErrorCategory.DEPENDENCY_ISSUE:
                context_multiplier *= 1.4
            
            # Time-based adjustments (e.g., Monday morning deployments)
            current_hour = datetime.now().hour
            if current_hour < 10 and category == ErrorCategory.CONFIGURATION_ERROR:
                context_multiplier *= 1.2
            
            predictions[category.value] = min(1.0, base_likelihood * context_multiplier)
        
        return predictions

