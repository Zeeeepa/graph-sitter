"""
Effectiveness Tracker

Tracks and measures the effectiveness of recovery actions and self-healing procedures.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

from ..models.events import RecoveryAction, ErrorEvent
from ..models.enums import RecoveryStatus, ErrorType, ErrorSeverity


class EffectivenessTracker:
    """
    Tracks and measures the effectiveness of recovery actions.
    
    Provides metrics and insights for continuous improvement of
    self-healing procedures.
    """
    
    def __init__(self):
        """Initialize the effectiveness tracker."""
        self.logger = logging.getLogger(__name__)
        
        # Effectiveness data
        self.action_effectiveness: Dict[str, List[float]] = defaultdict(list)
        self.error_type_effectiveness: Dict[ErrorType, List[float]] = defaultdict(list)
        self.severity_effectiveness: Dict[ErrorSeverity, List[float]] = defaultdict(list)
        
        # Learning data
        self.successful_patterns: List[Dict[str, Any]] = []
        self.failed_patterns: List[Dict[str, Any]] = []
        
        # Performance baselines
        self.baselines = {
            "mean_recovery_time": 300.0,  # 5 minutes
            "success_rate_threshold": 0.7,  # 70%
            "effectiveness_threshold": 0.6,  # 60%
        }
    
    async def calculate_effectiveness(self, recovery_action: RecoveryAction) -> float:
        """
        Calculate the effectiveness score of a recovery action.
        
        Args:
            recovery_action: The recovery action to evaluate
            
        Returns:
            Effectiveness score from 0.0 to 1.0
        """
        try:
            effectiveness_score = 0.0
            
            # Base score based on completion status
            if recovery_action.status == RecoveryStatus.COMPLETED:
                effectiveness_score += 0.4
            elif recovery_action.status == RecoveryStatus.FAILED:
                effectiveness_score += 0.0
            elif recovery_action.status == RecoveryStatus.ESCALATED:
                effectiveness_score += 0.2
            else:
                return 0.0  # Pending or in-progress
            
            # Time-based effectiveness
            if recovery_action.started_at and recovery_action.completed_at:
                recovery_time = (recovery_action.completed_at - recovery_action.started_at).total_seconds()
                time_score = self._calculate_time_effectiveness(recovery_time)
                effectiveness_score += time_score * 0.3
            
            # Retry-based effectiveness (fewer retries = better)
            retry_score = max(0.0, 1.0 - (recovery_action.retry_count / recovery_action.max_retries))
            effectiveness_score += retry_score * 0.2
            
            # Result-based effectiveness
            if recovery_action.result:
                result_score = self._calculate_result_effectiveness(recovery_action.result)
                effectiveness_score += result_score * 0.1
            
            # Store effectiveness data
            action_type = recovery_action.action_type
            self.action_effectiveness[action_type].append(effectiveness_score)
            
            # Learn from this action
            await self._learn_from_action(recovery_action, effectiveness_score)
            
            return min(effectiveness_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            self.logger.error(f"Error calculating effectiveness: {e}")
            return 0.0
    
    def get_action_effectiveness_stats(self, action_type: str) -> Dict[str, Any]:
        """
        Get effectiveness statistics for a specific action type.
        
        Args:
            action_type: Type of action to analyze
            
        Returns:
            Statistics dictionary
        """
        try:
            scores = self.action_effectiveness.get(action_type, [])
            
            if not scores:
                return {
                    "action_type": action_type,
                    "sample_count": 0,
                    "mean_effectiveness": 0.0,
                    "success_rate": 0.0,
                    "trend": "insufficient_data",
                }
            
            mean_effectiveness = sum(scores) / len(scores)
            success_rate = sum(1 for score in scores if score >= self.baselines["effectiveness_threshold"]) / len(scores)
            
            # Calculate trend (last 10 vs previous 10)
            trend = "stable"
            if len(scores) >= 20:
                recent_scores = scores[-10:]
                previous_scores = scores[-20:-10]
                
                recent_avg = sum(recent_scores) / len(recent_scores)
                previous_avg = sum(previous_scores) / len(previous_scores)
                
                if recent_avg > previous_avg + 0.1:
                    trend = "improving"
                elif recent_avg < previous_avg - 0.1:
                    trend = "declining"
            
            return {
                "action_type": action_type,
                "sample_count": len(scores),
                "mean_effectiveness": round(mean_effectiveness, 3),
                "success_rate": round(success_rate, 3),
                "trend": trend,
                "recent_scores": scores[-5:] if len(scores) >= 5 else scores,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting action effectiveness stats: {e}")
            return {"error": str(e)}
    
    def get_overall_effectiveness_report(self) -> Dict[str, Any]:
        """
        Get comprehensive effectiveness report.
        
        Returns:
            Overall effectiveness report
        """
        try:
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "action_types": {},
                "error_types": {},
                "severity_levels": {},
                "overall_metrics": {},
                "recommendations": [],
            }
            
            # Action type effectiveness
            for action_type in self.action_effectiveness:
                report["action_types"][action_type] = self.get_action_effectiveness_stats(action_type)
            
            # Error type effectiveness
            for error_type in self.error_type_effectiveness:
                scores = self.error_type_effectiveness[error_type]
                if scores:
                    report["error_types"][error_type.value] = {
                        "sample_count": len(scores),
                        "mean_effectiveness": round(sum(scores) / len(scores), 3),
                        "success_rate": round(sum(1 for s in scores if s >= 0.6) / len(scores), 3),
                    }
            
            # Severity level effectiveness
            for severity in self.severity_effectiveness:
                scores = self.severity_effectiveness[severity]
                if scores:
                    report["severity_levels"][severity.value] = {
                        "sample_count": len(scores),
                        "mean_effectiveness": round(sum(scores) / len(scores), 3),
                        "success_rate": round(sum(1 for s in scores if s >= 0.6) / len(scores), 3),
                    }
            
            # Overall metrics
            all_scores = []
            for scores in self.action_effectiveness.values():
                all_scores.extend(scores)
            
            if all_scores:
                report["overall_metrics"] = {
                    "total_actions": len(all_scores),
                    "overall_effectiveness": round(sum(all_scores) / len(all_scores), 3),
                    "overall_success_rate": round(sum(1 for s in all_scores if s >= 0.6) / len(all_scores), 3),
                }
            
            # Generate recommendations
            report["recommendations"] = self._generate_recommendations(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating effectiveness report: {e}")
            return {"error": str(e)}
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get insights from successful and failed patterns.
        
        Returns:
            Learning insights
        """
        try:
            insights = {
                "successful_patterns": len(self.successful_patterns),
                "failed_patterns": len(self.failed_patterns),
                "top_success_factors": [],
                "common_failure_causes": [],
                "improvement_opportunities": [],
            }
            
            # Analyze successful patterns
            if self.successful_patterns:
                success_factors = defaultdict(int)
                for pattern in self.successful_patterns:
                    for factor in pattern.get("success_factors", []):
                        success_factors[factor] += 1
                
                insights["top_success_factors"] = [
                    {"factor": factor, "frequency": count}
                    for factor, count in sorted(success_factors.items(), key=lambda x: x[1], reverse=True)[:5]
                ]
            
            # Analyze failed patterns
            if self.failed_patterns:
                failure_causes = defaultdict(int)
                for pattern in self.failed_patterns:
                    for cause in pattern.get("failure_causes", []):
                        failure_causes[cause] += 1
                
                insights["common_failure_causes"] = [
                    {"cause": cause, "frequency": count}
                    for cause, count in sorted(failure_causes.items(), key=lambda x: x[1], reverse=True)[:5]
                ]
            
            # Generate improvement opportunities
            insights["improvement_opportunities"] = self._identify_improvement_opportunities()
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error getting learning insights: {e}")
            return {"error": str(e)}
    
    def _calculate_time_effectiveness(self, recovery_time: float) -> float:
        """Calculate effectiveness based on recovery time."""
        baseline_time = self.baselines["mean_recovery_time"]
        
        if recovery_time <= baseline_time * 0.5:  # Very fast
            return 1.0
        elif recovery_time <= baseline_time:  # Within baseline
            return 0.8
        elif recovery_time <= baseline_time * 2:  # Acceptable
            return 0.6
        elif recovery_time <= baseline_time * 4:  # Slow
            return 0.3
        else:  # Very slow
            return 0.1
    
    def _calculate_result_effectiveness(self, result: Dict[str, Any]) -> float:
        """Calculate effectiveness based on action result."""
        if not result:
            return 0.0
        
        success = result.get("success", False)
        if not success:
            return 0.0
        
        # Additional factors
        score = 0.5  # Base score for success
        
        # Check for specific success indicators
        if "health_status" in result and result["health_status"] == "healthy":
            score += 0.3
        
        if "error_resolved" in result and result["error_resolved"]:
            score += 0.2
        
        return min(score, 1.0)
    
    async def _learn_from_action(self, recovery_action: RecoveryAction, 
                               effectiveness_score: float) -> None:
        """Learn from recovery action for future improvements."""
        try:
            pattern = {
                "action_type": recovery_action.action_type,
                "effectiveness_score": effectiveness_score,
                "recovery_time": None,
                "retry_count": recovery_action.retry_count,
                "parameters": recovery_action.parameters or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Calculate recovery time
            if recovery_action.started_at and recovery_action.completed_at:
                recovery_time = (recovery_action.completed_at - recovery_action.started_at).total_seconds()
                pattern["recovery_time"] = recovery_time
            
            # Classify as successful or failed pattern
            if effectiveness_score >= self.baselines["effectiveness_threshold"]:
                # Successful pattern
                pattern["success_factors"] = self._identify_success_factors(recovery_action)
                self.successful_patterns.append(pattern)
                
                # Limit successful patterns history
                if len(self.successful_patterns) > 1000:
                    self.successful_patterns = self.successful_patterns[-1000:]
            else:
                # Failed pattern
                pattern["failure_causes"] = self._identify_failure_causes(recovery_action)
                self.failed_patterns.append(pattern)
                
                # Limit failed patterns history
                if len(self.failed_patterns) > 1000:
                    self.failed_patterns = self.failed_patterns[-1000:]
            
        except Exception as e:
            self.logger.error(f"Error learning from action: {e}")
    
    def _identify_success_factors(self, recovery_action: RecoveryAction) -> List[str]:
        """Identify factors that contributed to success."""
        factors = []
        
        # Low retry count
        if recovery_action.retry_count == 0:
            factors.append("first_attempt_success")
        elif recovery_action.retry_count <= 1:
            factors.append("low_retry_count")
        
        # Fast completion
        if recovery_action.started_at and recovery_action.completed_at:
            recovery_time = (recovery_action.completed_at - recovery_action.started_at).total_seconds()
            if recovery_time <= self.baselines["mean_recovery_time"] * 0.5:
                factors.append("fast_completion")
        
        # Specific action types that tend to be successful
        if recovery_action.action_type in ["restart_service", "rollback_deployment"]:
            factors.append("reliable_action_type")
        
        return factors
    
    def _identify_failure_causes(self, recovery_action: RecoveryAction) -> List[str]:
        """Identify causes of failure."""
        causes = []
        
        # High retry count
        if recovery_action.retry_count >= recovery_action.max_retries:
            causes.append("max_retries_exceeded")
        elif recovery_action.retry_count >= 2:
            causes.append("high_retry_count")
        
        # Slow completion
        if recovery_action.started_at and recovery_action.completed_at:
            recovery_time = (recovery_action.completed_at - recovery_action.started_at).total_seconds()
            if recovery_time > self.baselines["mean_recovery_time"] * 2:
                causes.append("slow_completion")
        
        # Error in result
        if recovery_action.error_message:
            if "timeout" in recovery_action.error_message.lower():
                causes.append("timeout_error")
            elif "permission" in recovery_action.error_message.lower():
                causes.append("permission_error")
            elif "resource" in recovery_action.error_message.lower():
                causes.append("resource_error")
            else:
                causes.append("unknown_error")
        
        return causes
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on effectiveness data."""
        recommendations = []
        
        try:
            # Check overall effectiveness
            overall_metrics = report.get("overall_metrics", {})
            overall_effectiveness = overall_metrics.get("overall_effectiveness", 0.0)
            
            if overall_effectiveness < 0.6:
                recommendations.append("Overall effectiveness is below threshold. Review and improve recovery procedures.")
            
            # Check action type performance
            action_types = report.get("action_types", {})
            for action_type, stats in action_types.items():
                effectiveness = stats.get("mean_effectiveness", 0.0)
                trend = stats.get("trend", "stable")
                
                if effectiveness < 0.5:
                    recommendations.append(f"Action type '{action_type}' has low effectiveness ({effectiveness:.2f}). Consider alternative approaches.")
                
                if trend == "declining":
                    recommendations.append(f"Action type '{action_type}' effectiveness is declining. Investigate recent changes.")
            
            # Check for patterns in failed actions
            if len(self.failed_patterns) > len(self.successful_patterns):
                recommendations.append("High failure rate detected. Review error detection and action selection logic.")
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Error generating recommendations. Manual review required.")
        
        return recommendations
    
    def _identify_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for improvement."""
        opportunities = []
        
        try:
            # Analyze action type performance
            for action_type, scores in self.action_effectiveness.items():
                if len(scores) >= 5:  # Need sufficient data
                    avg_score = sum(scores) / len(scores)
                    if avg_score < 0.7:
                        opportunities.append({
                            "type": "action_improvement",
                            "action_type": action_type,
                            "current_effectiveness": round(avg_score, 3),
                            "suggestion": f"Improve {action_type} procedures or parameters",
                        })
            
            # Analyze common failure patterns
            if len(self.failed_patterns) >= 10:
                failure_causes = defaultdict(int)
                for pattern in self.failed_patterns[-50:]:  # Last 50 failures
                    for cause in pattern.get("failure_causes", []):
                        failure_causes[cause] += 1
                
                for cause, count in failure_causes.items():
                    if count >= 5:  # Frequent failure cause
                        opportunities.append({
                            "type": "failure_reduction",
                            "failure_cause": cause,
                            "frequency": count,
                            "suggestion": f"Address common failure cause: {cause}",
                        })
        
        except Exception as e:
            self.logger.error(f"Error identifying improvement opportunities: {e}")
        
        return opportunities

