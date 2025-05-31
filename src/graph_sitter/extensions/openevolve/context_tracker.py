"""
Context Tracker for OpenEvolve Integration

This module provides comprehensive step-by-step execution logging, decision tree tracking,
and context capture mechanisms for the OpenEvolve integration.
"""

import asyncio
import json
import time
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from graph_sitter.shared.logging import get_logger

from .database_manager import OpenEvolveDatabase

logger = get_logger(__name__)


class DecisionNode:
    """
    Represents a decision point in the evolution process.
    """
    
    def __init__(
        self,
        node_id: str,
        decision_type: str,
        context: Dict[str, Any],
        timestamp: float = None
    ):
        self.node_id = node_id
        self.decision_type = decision_type
        self.context = context
        self.timestamp = timestamp or time.time()
        self.children = []
        self.parent = None
        self.outcome = None
        self.metrics = {}
    
    def add_child(self, child_node: 'DecisionNode') -> None:
        """Add a child decision node."""
        child_node.parent = self
        self.children.append(child_node)
    
    def set_outcome(self, outcome: Any, metrics: Dict[str, Any] = None) -> None:
        """Set the outcome of this decision."""
        self.outcome = outcome
        self.metrics = metrics or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "node_id": self.node_id,
            "decision_type": self.decision_type,
            "context": self.context,
            "timestamp": self.timestamp,
            "outcome": self.outcome,
            "metrics": self.metrics,
            "children": [child.node_id for child in self.children],
            "parent": self.parent.node_id if self.parent else None
        }


class DecisionTree:
    """
    Tracks decision trees for evolution sessions.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.root = None
        self.nodes = {}
        self.current_node = None
    
    def create_root(self, decision_type: str, context: Dict[str, Any]) -> DecisionNode:
        """Create the root decision node."""
        node_id = f"{self.session_id}_root"
        self.root = DecisionNode(node_id, decision_type, context)
        self.nodes[node_id] = self.root
        self.current_node = self.root
        return self.root
    
    def add_decision(
        self,
        decision_type: str,
        context: Dict[str, Any],
        parent_id: Optional[str] = None
    ) -> DecisionNode:
        """Add a new decision node to the tree."""
        node_id = f"{self.session_id}_{uuid.uuid4().hex[:8]}"
        node = DecisionNode(node_id, decision_type, context)
        
        # Determine parent
        if parent_id and parent_id in self.nodes:
            parent = self.nodes[parent_id]
        else:
            parent = self.current_node or self.root
        
        if parent:
            parent.add_child(node)
        
        self.nodes[node_id] = node
        self.current_node = node
        return node
    
    def set_decision_outcome(
        self,
        node_id: str,
        outcome: Any,
        metrics: Dict[str, Any] = None
    ) -> None:
        """Set the outcome for a decision node."""
        if node_id in self.nodes:
            self.nodes[node_id].set_outcome(outcome, metrics)
    
    def get_path_to_node(self, node_id: str) -> List[DecisionNode]:
        """Get the path from root to a specific node."""
        if node_id not in self.nodes:
            return []
        
        path = []
        current = self.nodes[node_id]
        
        while current:
            path.insert(0, current)
            current = current.parent
        
        return path
    
    def analyze_decision_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in the decision tree."""
        if not self.root:
            return {"patterns": [], "depth": 0, "branches": 0}
        
        # Calculate tree metrics
        depth = self._calculate_depth(self.root)
        branch_count = len(self.nodes)
        
        # Analyze decision types
        decision_types = defaultdict(int)
        outcomes = defaultdict(list)
        
        for node in self.nodes.values():
            decision_types[node.decision_type] += 1
            if node.outcome is not None:
                outcomes[node.decision_type].append(node.outcome)
        
        # Find successful patterns
        successful_patterns = self._find_successful_patterns()
        
        return {
            "session_id": self.session_id,
            "depth": depth,
            "branches": branch_count,
            "decision_types": dict(decision_types),
            "outcomes": dict(outcomes),
            "successful_patterns": successful_patterns,
            "timestamp": time.time()
        }
    
    def _calculate_depth(self, node: DecisionNode) -> int:
        """Calculate the maximum depth of the tree."""
        if not node.children:
            return 1
        
        return 1 + max(self._calculate_depth(child) for child in node.children)
    
    def _find_successful_patterns(self) -> List[Dict[str, Any]]:
        """Find patterns that led to successful outcomes."""
        patterns = []
        
        # Find leaf nodes with successful outcomes
        for node in self.nodes.values():
            if not node.children and node.outcome:
                # Check if outcome indicates success
                if self._is_successful_outcome(node.outcome):
                    path = self.get_path_to_node(node.node_id)
                    pattern = {
                        "path": [n.decision_type for n in path],
                        "context_keys": list(node.context.keys()),
                        "outcome": node.outcome,
                        "metrics": node.metrics
                    }
                    patterns.append(pattern)
        
        return patterns
    
    def _is_successful_outcome(self, outcome: Any) -> bool:
        """Determine if an outcome is considered successful."""
        if isinstance(outcome, dict):
            # Check for success indicators in the outcome
            return outcome.get("success", False) or outcome.get("improvement", 0) > 0
        elif isinstance(outcome, (int, float)):
            return outcome > 0
        elif isinstance(outcome, bool):
            return outcome
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the entire tree to dictionary representation."""
        return {
            "session_id": self.session_id,
            "root_id": self.root.node_id if self.root else None,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "current_node_id": self.current_node.node_id if self.current_node else None
        }


class ContextTracker:
    """
    Main context tracking system for comprehensive step logging.
    """
    
    def __init__(self, database: OpenEvolveDatabase):
        self.database = database
        self.active_sessions = {}
        self.decision_trees = {}
        self.step_contexts = {}
    
    def start_session(self, session_id: str) -> None:
        """Start tracking a new session."""
        self.active_sessions[session_id] = {
            "start_time": time.time(),
            "steps": [],
            "current_step": None
        }
        
        # Initialize decision tree
        self.decision_trees[session_id] = DecisionTree(session_id)
        
        logger.info(f"Started context tracking for session {session_id}")
    
    async def start_step(
        self,
        session_id: str,
        step_type: str,
        file_path: str = None,
        prompt: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Start tracking a new evolution step.
        
        Args:
            session_id: Session ID
            step_type: Type of step (e.g., 'code_evolution', 'analysis')
            file_path: File being processed
            prompt: Evolution prompt
            context: Additional context
            
        Returns:
            Step ID for tracking
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        step_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
        
        step_context = {
            "step_id": step_id,
            "session_id": session_id,
            "step_type": step_type,
            "file_path": file_path,
            "prompt": prompt,
            "context": context or {},
            "start_time": time.time(),
            "status": "running",
            "decisions": [],
            "metrics": {},
            "errors": []
        }
        
        # Store step context
        self.step_contexts[step_id] = step_context
        self.active_sessions[session_id]["steps"].append(step_id)
        self.active_sessions[session_id]["current_step"] = step_id
        
        # Add to decision tree
        decision_tree = self.decision_trees[session_id]
        if not decision_tree.root:
            decision_tree.create_root(step_type, step_context)
        else:
            decision_tree.add_decision(step_type, step_context)
        
        # Store in database
        await self.database.store_step_context(step_context)
        
        logger.debug(f"Started tracking step {step_id} for session {session_id}")
        return step_id
    
    async def record_decision(
        self,
        step_id: str,
        decision_type: str,
        decision_context: Dict[str, Any],
        outcome: Any = None
    ) -> str:
        """
        Record a decision point within a step.
        
        Args:
            step_id: Step ID
            decision_type: Type of decision
            decision_context: Context for the decision
            outcome: Decision outcome (if available)
            
        Returns:
            Decision ID
        """
        if step_id not in self.step_contexts:
            raise ValueError(f"Step {step_id} not found")
        
        decision_id = f"{step_id}_{uuid.uuid4().hex[:8]}"
        
        decision = {
            "decision_id": decision_id,
            "step_id": step_id,
            "decision_type": decision_type,
            "context": decision_context,
            "outcome": outcome,
            "timestamp": time.time()
        }
        
        # Add to step context
        self.step_contexts[step_id]["decisions"].append(decision)
        
        # Add to decision tree
        session_id = self.step_contexts[step_id]["session_id"]
        if session_id in self.decision_trees:
            decision_tree = self.decision_trees[session_id]
            node = decision_tree.add_decision(decision_type, decision_context)
            if outcome is not None:
                decision_tree.set_decision_outcome(node.node_id, outcome)
        
        # Store in database
        await self.database.store_decision(decision)
        
        logger.debug(f"Recorded decision {decision_id} for step {step_id}")
        return decision_id
    
    async def record_metrics(
        self,
        step_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Record metrics for a step.
        
        Args:
            step_id: Step ID
            metrics: Metrics to record
        """
        if step_id not in self.step_contexts:
            raise ValueError(f"Step {step_id} not found")
        
        # Update step context
        self.step_contexts[step_id]["metrics"].update(metrics)
        self.step_contexts[step_id]["last_metric_update"] = time.time()
        
        # Store in database
        await self.database.update_step_metrics(step_id, metrics)
        
        logger.debug(f"Recorded metrics for step {step_id}: {list(metrics.keys())}")
    
    async def record_error(
        self,
        step_id: str,
        error: str,
        execution_time: float = None
    ) -> None:
        """
        Record an error for a step.
        
        Args:
            step_id: Step ID
            error: Error message
            execution_time: Execution time before error
        """
        if step_id not in self.step_contexts:
            raise ValueError(f"Step {step_id} not found")
        
        error_record = {
            "error": error,
            "timestamp": time.time(),
            "execution_time": execution_time
        }
        
        # Update step context
        self.step_contexts[step_id]["errors"].append(error_record)
        self.step_contexts[step_id]["status"] = "error"
        if execution_time:
            self.step_contexts[step_id]["execution_time"] = execution_time
        
        # Store in database
        await self.database.record_step_error(step_id, error_record)
        
        logger.warning(f"Recorded error for step {step_id}: {error}")
    
    async def complete_step(
        self,
        step_id: str,
        result: Dict[str, Any],
        execution_time: float = None
    ) -> None:
        """
        Complete tracking for a step.
        
        Args:
            step_id: Step ID
            result: Step result
            execution_time: Total execution time
        """
        if step_id not in self.step_contexts:
            raise ValueError(f"Step {step_id} not found")
        
        # Update step context
        step_context = self.step_contexts[step_id]
        step_context["result"] = result
        step_context["status"] = "completed"
        step_context["end_time"] = time.time()
        
        if execution_time:
            step_context["execution_time"] = execution_time
        else:
            step_context["execution_time"] = step_context["end_time"] - step_context["start_time"]
        
        # Update decision tree with final outcome
        session_id = step_context["session_id"]
        if session_id in self.decision_trees:
            decision_tree = self.decision_trees[session_id]
            if decision_tree.current_node:
                decision_tree.set_decision_outcome(
                    decision_tree.current_node.node_id,
                    result,
                    step_context["metrics"]
                )
        
        # Store final context in database
        await self.database.complete_step_context(step_id, step_context)
        
        logger.debug(f"Completed tracking for step {step_id}")
    
    async def analyze_patterns(
        self,
        session_id: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze patterns in the tracked context data.
        
        Args:
            session_id: Session ID to analyze
            file_path: Optional file path filter
            
        Returns:
            Pattern analysis results
        """
        if session_id not in self.active_sessions:
            return {"error": f"Session {session_id} not found"}
        
        # Get session steps
        session = self.active_sessions[session_id]
        step_ids = session["steps"]
        
        # Filter by file path if specified
        if file_path:
            step_ids = [
                step_id for step_id in step_ids
                if self.step_contexts.get(step_id, {}).get("file_path") == file_path
            ]
        
        # Analyze step patterns
        step_patterns = self._analyze_step_patterns(step_ids)
        
        # Analyze decision tree patterns
        decision_patterns = {}
        if session_id in self.decision_trees:
            decision_patterns = self.decision_trees[session_id].analyze_decision_patterns()
        
        # Analyze performance patterns
        performance_patterns = self._analyze_performance_patterns(step_ids)
        
        # Analyze error patterns
        error_patterns = self._analyze_error_patterns(step_ids)
        
        return {
            "session_id": session_id,
            "file_path": file_path,
            "step_patterns": step_patterns,
            "decision_patterns": decision_patterns,
            "performance_patterns": performance_patterns,
            "error_patterns": error_patterns,
            "analysis_timestamp": time.time()
        }
    
    def end_session(self, session_id: str) -> None:
        """End tracking for a session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session["end_time"] = time.time()
            session["duration"] = session["end_time"] - session["start_time"]
            
            logger.info(f"Ended context tracking for session {session_id}")
    
    def _analyze_step_patterns(self, step_ids: List[str]) -> Dict[str, Any]:
        """Analyze patterns in step execution."""
        if not step_ids:
            return {"patterns": [], "total_steps": 0}
        
        step_types = defaultdict(int)
        execution_times = []
        success_rates = defaultdict(lambda: {"total": 0, "successful": 0})
        
        for step_id in step_ids:
            if step_id not in self.step_contexts:
                continue
            
            step = self.step_contexts[step_id]
            step_type = step.get("step_type", "unknown")
            
            step_types[step_type] += 1
            
            if "execution_time" in step:
                execution_times.append(step["execution_time"])
            
            # Analyze success
            success_rates[step_type]["total"] += 1
            if step.get("status") == "completed" and not step.get("errors"):
                success_rates[step_type]["successful"] += 1
        
        # Calculate success rates
        calculated_success_rates = {}
        for step_type, counts in success_rates.items():
            if counts["total"] > 0:
                calculated_success_rates[step_type] = counts["successful"] / counts["total"]
        
        return {
            "total_steps": len(step_ids),
            "step_types": dict(step_types),
            "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "success_rates": calculated_success_rates,
            "patterns": self._identify_step_patterns(step_ids)
        }
    
    def _analyze_performance_patterns(self, step_ids: List[str]) -> Dict[str, Any]:
        """Analyze performance patterns in steps."""
        performance_data = []
        
        for step_id in step_ids:
            if step_id not in self.step_contexts:
                continue
            
            step = self.step_contexts[step_id]
            metrics = step.get("metrics", {})
            
            if metrics:
                performance_data.append({
                    "step_id": step_id,
                    "step_type": step.get("step_type"),
                    "execution_time": step.get("execution_time", 0),
                    "metrics": metrics
                })
        
        if not performance_data:
            return {"patterns": [], "trends": {}}
        
        # Analyze trends
        trends = self._calculate_performance_trends(performance_data)
        
        return {
            "total_measurements": len(performance_data),
            "trends": trends,
            "patterns": self._identify_performance_patterns(performance_data)
        }
    
    def _analyze_error_patterns(self, step_ids: List[str]) -> Dict[str, Any]:
        """Analyze error patterns in steps."""
        error_data = []
        
        for step_id in step_ids:
            if step_id not in self.step_contexts:
                continue
            
            step = self.step_contexts[step_id]
            errors = step.get("errors", [])
            
            for error in errors:
                error_data.append({
                    "step_id": step_id,
                    "step_type": step.get("step_type"),
                    "error": error.get("error"),
                    "timestamp": error.get("timestamp")
                })
        
        if not error_data:
            return {"patterns": [], "common_errors": []}
        
        # Find common error patterns
        error_counts = defaultdict(int)
        for error in error_data:
            error_counts[error["error"]] += 1
        
        common_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_errors": len(error_data),
            "common_errors": common_errors,
            "error_rate": len(error_data) / len(step_ids) if step_ids else 0,
            "patterns": self._identify_error_patterns(error_data)
        }
    
    def _identify_step_patterns(self, step_ids: List[str]) -> List[Dict[str, Any]]:
        """Identify patterns in step sequences."""
        # This is a simplified pattern identification
        # Could be enhanced with more sophisticated sequence analysis
        patterns = []
        
        if len(step_ids) < 3:
            return patterns
        
        # Look for common step sequences
        sequences = []
        for i in range(len(step_ids) - 2):
            sequence = []
            for j in range(3):  # Look at 3-step sequences
                step_id = step_ids[i + j]
                if step_id in self.step_contexts:
                    sequence.append(self.step_contexts[step_id].get("step_type", "unknown"))
            
            if len(sequence) == 3:
                sequences.append(tuple(sequence))
        
        # Count sequence frequencies
        sequence_counts = defaultdict(int)
        for seq in sequences:
            sequence_counts[seq] += 1
        
        # Find common patterns
        for seq, count in sequence_counts.items():
            if count >= 2:  # Appears at least twice
                patterns.append({
                    "sequence": list(seq),
                    "frequency": count,
                    "pattern_type": "step_sequence"
                })
        
        return patterns
    
    def _calculate_performance_trends(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance trends over time."""
        trends = {}
        
        # Group by step type
        by_step_type = defaultdict(list)
        for data in performance_data:
            by_step_type[data["step_type"]].append(data)
        
        # Calculate trends for each step type
        for step_type, data_points in by_step_type.items():
            if len(data_points) < 2:
                continue
            
            # Sort by timestamp (using step_id as proxy)
            data_points.sort(key=lambda x: x["step_id"])
            
            # Calculate execution time trend
            execution_times = [dp["execution_time"] for dp in data_points]
            if len(execution_times) >= 2:
                # Simple linear trend calculation
                first_half = execution_times[:len(execution_times)//2]
                second_half = execution_times[len(execution_times)//2:]
                
                avg_first = sum(first_half) / len(first_half)
                avg_second = sum(second_half) / len(second_half)
                
                trend = "improving" if avg_second < avg_first else "degrading"
                trends[step_type] = {
                    "execution_time_trend": trend,
                    "avg_first_half": avg_first,
                    "avg_second_half": avg_second
                }
        
        return trends
    
    def _identify_performance_patterns(self, performance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify performance patterns."""
        patterns = []
        
        # Group by step type and analyze
        by_step_type = defaultdict(list)
        for data in performance_data:
            by_step_type[data["step_type"]].append(data)
        
        for step_type, data_points in by_step_type.items():
            if len(data_points) < 3:
                continue
            
            execution_times = [dp["execution_time"] for dp in data_points]
            avg_time = sum(execution_times) / len(execution_times)
            
            # Identify outliers
            outliers = [t for t in execution_times if abs(t - avg_time) > avg_time * 0.5]
            
            if outliers:
                patterns.append({
                    "step_type": step_type,
                    "pattern_type": "performance_outliers",
                    "outlier_count": len(outliers),
                    "avg_execution_time": avg_time,
                    "outlier_threshold": avg_time * 0.5
                })
        
        return patterns
    
    def _identify_error_patterns(self, error_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify error patterns."""
        patterns = []
        
        # Group errors by step type
        by_step_type = defaultdict(list)
        for error in error_data:
            by_step_type[error["step_type"]].append(error)
        
        for step_type, errors in by_step_type.items():
            if len(errors) >= 2:
                patterns.append({
                    "step_type": step_type,
                    "pattern_type": "recurring_errors",
                    "error_count": len(errors),
                    "common_error": max(
                        set(e["error"] for e in errors),
                        key=lambda x: sum(1 for e in errors if e["error"] == x)
                    )
                })
        
        return patterns

