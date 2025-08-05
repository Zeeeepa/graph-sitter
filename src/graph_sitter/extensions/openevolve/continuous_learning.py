"""
Continuous Learning System for OpenEvolve Integration

This module implements continuous learning mechanics that learn from every evolution step,
recognize patterns, and adapt algorithms for better outcomes over time.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from graph_sitter.shared.logging import get_logger

from .config import OpenEvolveConfig
from .database_manager import OpenEvolveDatabase

logger = get_logger(__name__)


class PatternRecognizer:
    """
    Recognizes patterns in evolution history to identify successful strategies.
    """
    
    def __init__(self):
        self.pattern_cache = {}
        self.success_patterns = []
        self.failure_patterns = []
    
    def analyze_evolution_patterns(
        self,
        evolution_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze patterns in evolution history.
        
        Args:
            evolution_history: List of evolution steps with results
            
        Returns:
            Identified patterns and their success rates
        """
        if len(evolution_history) < 5:
            return {"patterns": [], "confidence": 0.0}
        
        # Extract features from evolution history
        features = self._extract_features(evolution_history)
        
        # Cluster similar evolution attempts
        patterns = self._cluster_evolution_attempts(features, evolution_history)
        
        # Analyze success rates for each pattern
        pattern_analysis = self._analyze_pattern_success(patterns, evolution_history)
        
        return {
            "patterns": pattern_analysis,
            "total_patterns": len(patterns),
            "confidence": self._calculate_confidence(pattern_analysis),
            "timestamp": time.time()
        }
    
    def _extract_features(self, evolution_history: List[Dict[str, Any]]) -> np.ndarray:
        """Extract numerical features from evolution history."""
        features = []
        
        for step in evolution_history:
            step_features = [
                # Code complexity features
                step.get("complexity_metrics", {}).get("cyclomatic_complexity", 0),
                step.get("complexity_metrics", {}).get("lines_of_code", 0),
                step.get("complexity_metrics", {}).get("function_count", 0),
                
                # Evolution context features
                len(step.get("evolution_prompt", "")),
                len(step.get("applied_patterns", [])),
                
                # Performance features
                step.get("execution_time", 0),
                step.get("evolution_metrics", {}).get("performance_improvement", 0),
                step.get("evolution_metrics", {}).get("maintainability_score", 0),
                
                # Success indicator
                1.0 if step.get("success", False) else 0.0
            ]
            features.append(step_features)
        
        return np.array(features)
    
    def _cluster_evolution_attempts(
        self,
        features: np.ndarray,
        evolution_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Cluster similar evolution attempts to identify patterns."""
        if len(features) < 3:
            return []
        
        # Normalize features
        scaler = StandardScaler()
        normalized_features = scaler.fit_transform(features[:, :-1])  # Exclude success indicator
        
        # Determine optimal number of clusters
        n_clusters = min(5, max(2, len(features) // 3))
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(normalized_features)
        
        # Group evolution attempts by cluster
        patterns = []
        for cluster_id in range(n_clusters):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            cluster_steps = [evolution_history[i] for i in cluster_indices]
            
            pattern = {
                "cluster_id": cluster_id,
                "steps": cluster_steps,
                "centroid": kmeans.cluster_centers_[cluster_id].tolist(),
                "size": len(cluster_steps)
            }
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_pattern_success(
        self,
        patterns: List[Dict[str, Any]],
        evolution_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze success rates for identified patterns."""
        pattern_analysis = []
        
        for pattern in patterns:
            steps = pattern["steps"]
            if not steps:
                continue
            
            # Calculate success metrics
            success_count = sum(1 for step in steps if step.get("success", False))
            success_rate = success_count / len(steps)
            
            # Calculate average improvements
            avg_performance = np.mean([
                step.get("evolution_metrics", {}).get("performance_improvement", 0)
                for step in steps
            ])
            
            avg_maintainability = np.mean([
                step.get("evolution_metrics", {}).get("maintainability_score", 0)
                for step in steps
            ])
            
            # Identify common characteristics
            common_patterns = self._identify_common_characteristics(steps)
            
            analysis = {
                "pattern_id": pattern["cluster_id"],
                "success_rate": success_rate,
                "sample_size": len(steps),
                "avg_performance_improvement": avg_performance,
                "avg_maintainability_score": avg_maintainability,
                "common_characteristics": common_patterns,
                "confidence": min(1.0, len(steps) / 10.0)  # Higher confidence with more samples
            }
            
            pattern_analysis.append(analysis)
        
        # Sort by success rate
        pattern_analysis.sort(key=lambda x: x["success_rate"], reverse=True)
        
        return pattern_analysis
    
    def _identify_common_characteristics(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify common characteristics in a group of evolution steps."""
        characteristics = {
            "common_prompt_keywords": [],
            "common_patterns": [],
            "avg_complexity_range": {},
            "common_file_types": []
        }
        
        # Analyze prompt keywords
        all_keywords = []
        for step in steps:
            prompt = step.get("evolution_prompt", "")
            keywords = prompt.lower().split()
            all_keywords.extend(keywords)
        
        # Find most common keywords
        keyword_counts = defaultdict(int)
        for keyword in all_keywords:
            keyword_counts[keyword] += 1
        
        characteristics["common_prompt_keywords"] = [
            keyword for keyword, count in keyword_counts.items()
            if count >= len(steps) * 0.5  # Appears in at least 50% of steps
        ]
        
        # Analyze applied patterns
        all_patterns = []
        for step in steps:
            patterns = step.get("applied_patterns", [])
            all_patterns.extend(patterns)
        
        pattern_counts = defaultdict(int)
        for pattern in all_patterns:
            pattern_counts[pattern] += 1
        
        characteristics["common_patterns"] = [
            pattern for pattern, count in pattern_counts.items()
            if count >= len(steps) * 0.3  # Appears in at least 30% of steps
        ]
        
        return characteristics
    
    def _calculate_confidence(self, pattern_analysis: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in pattern analysis."""
        if not pattern_analysis:
            return 0.0
        
        # Weight confidence by sample size and success rate
        total_weight = 0
        weighted_confidence = 0
        
        for pattern in pattern_analysis:
            weight = pattern["sample_size"] * (1 + pattern["success_rate"])
            weighted_confidence += pattern["confidence"] * weight
            total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0


class AdaptiveAlgorithm:
    """
    Adaptive algorithms that modify behavior based on historical outcomes.
    """
    
    def __init__(self):
        self.performance_model = None
        self.strategy_weights = defaultdict(float)
        self.adaptation_history = []
    
    def train_performance_predictor(
        self,
        evolution_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Train a model to predict evolution success based on context.
        
        Args:
            evolution_history: Historical evolution data
            
        Returns:
            Training results and model performance
        """
        if len(evolution_history) < 10:
            return {"status": "insufficient_data", "required_samples": 10}
        
        # Prepare training data
        X, y = self._prepare_training_data(evolution_history)
        
        if len(X) == 0:
            return {"status": "no_valid_data"}
        
        # Train random forest model
        self.performance_model = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
        
        self.performance_model.fit(X, y)
        
        # Calculate feature importance
        feature_names = self._get_feature_names()
        feature_importance = dict(zip(
            feature_names,
            self.performance_model.feature_importances_
        ))
        
        # Evaluate model performance
        score = self.performance_model.score(X, y)
        
        training_result = {
            "status": "success",
            "model_score": score,
            "feature_importance": feature_importance,
            "training_samples": len(X),
            "timestamp": time.time()
        }
        
        logger.info(f"Performance predictor trained with score: {score:.3f}")
        return training_result
    
    def predict_evolution_success(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict the likelihood of evolution success for given context.
        
        Args:
            context: Evolution context
            
        Returns:
            Prediction results with confidence
        """
        if self.performance_model is None:
            return {"prediction": 0.5, "confidence": 0.0, "status": "no_model"}
        
        # Extract features from context
        features = self._extract_context_features(context)
        
        if not features:
            return {"prediction": 0.5, "confidence": 0.0, "status": "no_features"}
        
        # Make prediction
        prediction = self.performance_model.predict([features])[0]
        
        # Calculate confidence based on feature similarity to training data
        confidence = self._calculate_prediction_confidence(features)
        
        return {
            "prediction": max(0.0, min(1.0, prediction)),
            "confidence": confidence,
            "status": "success"
        }
    
    def adapt_strategy_weights(
        self,
        recent_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Adapt strategy weights based on recent performance.
        
        Args:
            recent_results: Recent evolution results
            
        Returns:
            Updated strategy weights
        """
        # Analyze performance by strategy
        strategy_performance = defaultdict(list)
        
        for result in recent_results:
            strategies = result.get("applied_patterns", [])
            success_score = result.get("evolution_metrics", {}).get("performance_improvement", 0)
            
            for strategy in strategies:
                strategy_performance[strategy].append(success_score)
        
        # Update weights based on average performance
        for strategy, scores in strategy_performance.items():
            if scores:
                avg_score = np.mean(scores)
                # Exponential moving average for weight updates
                alpha = 0.1
                self.strategy_weights[strategy] = (
                    alpha * avg_score + (1 - alpha) * self.strategy_weights[strategy]
                )
        
        # Normalize weights
        total_weight = sum(abs(w) for w in self.strategy_weights.values())
        if total_weight > 0:
            for strategy in self.strategy_weights:
                self.strategy_weights[strategy] /= total_weight
        
        return dict(self.strategy_weights)
    
    def _prepare_training_data(
        self,
        evolution_history: List[Dict[str, Any]]
    ) -> Tuple[List[List[float]], List[float]]:
        """Prepare training data for the performance model."""
        X, y = [], []
        
        for step in evolution_history:
            features = self._extract_context_features(step)
            if features:
                success_score = step.get("evolution_metrics", {}).get("performance_improvement", 0)
                X.append(features)
                y.append(success_score)
        
        return X, y
    
    def _extract_context_features(self, context: Dict[str, Any]) -> List[float]:
        """Extract numerical features from evolution context."""
        features = []
        
        # Code complexity features
        complexity = context.get("complexity_metrics", {})
        features.extend([
            complexity.get("cyclomatic_complexity", 0),
            complexity.get("lines_of_code", 0),
            complexity.get("function_count", 0),
            complexity.get("class_count", 0)
        ])
        
        # Evolution context features
        features.extend([
            len(context.get("evolution_prompt", "")),
            len(context.get("applied_patterns", [])),
            len(context.get("dependencies", [])),
            context.get("execution_time", 0)
        ])
        
        # Historical performance features
        features.extend([
            context.get("historical_success_rate", 0.5),
            context.get("avg_improvement", 0.0),
            context.get("pattern_confidence", 0.0)
        ])
        
        return features
    
    def _get_feature_names(self) -> List[str]:
        """Get names for the extracted features."""
        return [
            "cyclomatic_complexity", "lines_of_code", "function_count", "class_count",
            "prompt_length", "pattern_count", "dependency_count", "execution_time",
            "historical_success_rate", "avg_improvement", "pattern_confidence"
        ]
    
    def _calculate_prediction_confidence(self, features: List[float]) -> float:
        """Calculate confidence in prediction based on feature similarity."""
        # Simple confidence calculation - could be enhanced with more sophisticated methods
        return 0.8  # Placeholder confidence


class ContinuousLearningSystem:
    """
    Main continuous learning system that coordinates pattern recognition and adaptation.
    """
    
    def __init__(self, database: OpenEvolveDatabase, config: OpenEvolveConfig):
        self.database = database
        self.config = config
        self.pattern_recognizer = PatternRecognizer()
        self.adaptive_algorithm = AdaptiveAlgorithm()
        
        # Learning state
        self.last_training_time = 0
        self.learning_cache = {}
    
    async def enhance_context(
        self,
        file_path: str,
        current_analysis: Dict[str, Any],
        evolution_prompt: str,
        historical_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enhance evolution context with learning insights.
        
        Args:
            file_path: Path to file being evolved
            current_analysis: Current code analysis
            evolution_prompt: Evolution prompt
            historical_context: Additional historical context
            
        Returns:
            Enhanced context with learning insights
        """
        # Get historical data for this file
        file_history = await self.database.get_file_evolution_history(file_path)
        
        # Analyze patterns in historical data
        pattern_analysis = self.pattern_recognizer.analyze_evolution_patterns(file_history)
        
        # Predict success probability
        context = {
            **current_analysis,
            "evolution_prompt": evolution_prompt,
            "historical_context": historical_context or {}
        }
        
        success_prediction = self.adaptive_algorithm.predict_evolution_success(context)
        
        # Generate suggestions based on patterns
        suggestions = self._generate_suggestions(pattern_analysis, success_prediction)
        
        enhanced_context = {
            **context,
            "pattern_analysis": pattern_analysis,
            "success_prediction": success_prediction,
            "suggested_patterns": suggestions.get("patterns", []),
            "insights": suggestions.get("insights", []),
            "confidence": pattern_analysis.get("confidence", 0.0)
        }
        
        return enhanced_context
    
    async def learn_from_result(
        self,
        step_id: str,
        evolution_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """
        Learn from evolution result to improve future predictions.
        
        Args:
            step_id: Evolution step ID
            evolution_result: Result of the evolution
            context: Context used for the evolution
        """
        # Store the learning data
        learning_data = {
            "step_id": step_id,
            "context": context,
            "result": evolution_result,
            "timestamp": time.time()
        }
        
        await self.database.store_learning_data(learning_data)
        
        # Check if we should retrain models
        if self._should_retrain():
            await self._retrain_models()
    
    async def get_insights(
        self,
        session_id: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get learning insights for a session or file.
        
        Args:
            session_id: Session ID
            file_path: Optional file path filter
            
        Returns:
            Learning insights and recommendations
        """
        # Get session data
        session_data = await self.database.get_session_data(session_id)
        
        if file_path:
            # Filter for specific file
            session_data = [
                step for step in session_data
                if step.get("file_path") == file_path
            ]
        
        # Analyze patterns
        pattern_analysis = self.pattern_recognizer.analyze_evolution_patterns(session_data)
        
        # Get strategy performance
        strategy_weights = self.adaptive_algorithm.strategy_weights
        
        insights = {
            "session_id": session_id,
            "file_path": file_path,
            "pattern_analysis": pattern_analysis,
            "strategy_performance": dict(strategy_weights),
            "recommendations": self._generate_recommendations(pattern_analysis),
            "learning_confidence": pattern_analysis.get("confidence", 0.0),
            "timestamp": time.time()
        }
        
        return insights
    
    async def optimize_strategy(self, session_id: str) -> Dict[str, Any]:
        """
        Optimize evolution strategy based on session performance.
        
        Args:
            session_id: Session ID to analyze
            
        Returns:
            Optimization results and suggested configuration changes
        """
        # Get session performance data
        session_data = await self.database.get_session_data(session_id)
        
        # Adapt strategy weights
        updated_weights = self.adaptive_algorithm.adapt_strategy_weights(session_data)
        
        # Generate configuration suggestions
        config_suggestions = self._generate_config_suggestions(session_data, updated_weights)
        
        optimization_result = {
            "session_id": session_id,
            "updated_strategy_weights": updated_weights,
            "suggested_config": config_suggestions,
            "performance_improvement": self._calculate_improvement_potential(session_data),
            "timestamp": time.time()
        }
        
        return optimization_result
    
    def _should_retrain(self) -> bool:
        """Check if models should be retrained."""
        current_time = time.time()
        time_since_training = current_time - self.last_training_time
        
        # Retrain every hour or after significant new data
        return time_since_training > 3600  # 1 hour
    
    async def _retrain_models(self) -> None:
        """Retrain learning models with latest data."""
        logger.info("Retraining learning models...")
        
        # Get recent evolution history
        recent_history = await self.database.get_recent_evolution_history(limit=1000)
        
        # Retrain performance predictor
        training_result = self.adaptive_algorithm.train_performance_predictor(recent_history)
        
        # Update last training time
        self.last_training_time = time.time()
        
        logger.info(f"Model retraining completed: {training_result}")
    
    def _generate_suggestions(
        self,
        pattern_analysis: Dict[str, Any],
        success_prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate suggestions based on pattern analysis and predictions."""
        suggestions = {
            "patterns": [],
            "insights": []
        }
        
        # Extract successful patterns
        patterns = pattern_analysis.get("patterns", [])
        for pattern in patterns:
            if pattern.get("success_rate", 0) > 0.7:  # High success rate
                suggestions["patterns"].extend(pattern.get("common_characteristics", {}).get("common_patterns", []))
        
        # Add insights based on prediction
        if success_prediction.get("prediction", 0) < 0.5:
            suggestions["insights"].append("Low success probability predicted - consider alternative approach")
        
        if success_prediction.get("confidence", 0) < 0.3:
            suggestions["insights"].append("Low prediction confidence - limited historical data available")
        
        return suggestions
    
    def _generate_recommendations(self, pattern_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on pattern analysis."""
        recommendations = []
        
        patterns = pattern_analysis.get("patterns", [])
        if not patterns:
            recommendations.append("Insufficient data for pattern-based recommendations")
            return recommendations
        
        # Find best performing pattern
        best_pattern = max(patterns, key=lambda p: p.get("success_rate", 0))
        
        if best_pattern.get("success_rate", 0) > 0.8:
            recommendations.append(
                f"High success pattern identified with {best_pattern['success_rate']:.1%} success rate"
            )
            
            common_chars = best_pattern.get("common_characteristics", {})
            if common_chars.get("common_patterns"):
                recommendations.append(
                    f"Recommended patterns: {', '.join(common_chars['common_patterns'][:3])}"
                )
        
        return recommendations
    
    def _generate_config_suggestions(
        self,
        session_data: List[Dict[str, Any]],
        strategy_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate configuration suggestions based on performance data."""
        suggestions = {}
        
        # Analyze execution times
        execution_times = [step.get("execution_time", 0) for step in session_data]
        if execution_times:
            avg_time = np.mean(execution_times)
            if avg_time > 30:  # If average execution time is high
                suggestions["max_evolution_time"] = min(60, avg_time * 1.5)
        
        # Suggest strategy adjustments based on weights
        top_strategies = sorted(
            strategy_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        if top_strategies:
            suggestions["preferred_strategies"] = [strategy for strategy, _ in top_strategies]
        
        return suggestions
    
    def _calculate_improvement_potential(self, session_data: List[Dict[str, Any]]) -> float:
        """Calculate potential for improvement based on session data."""
        if not session_data:
            return 0.0
        
        # Calculate average performance improvement
        improvements = [
            step.get("evolution_metrics", {}).get("performance_improvement", 0)
            for step in session_data
        ]
        
        if improvements:
            return max(0.0, np.mean(improvements))
        
        return 0.0

