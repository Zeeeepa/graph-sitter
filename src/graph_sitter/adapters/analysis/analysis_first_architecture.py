#!/usr/bin/env python3
"""
🧠 ANALYSIS-FIRST ARCHITECTURE ENGINE 🧠

Step 3 of CI/CD Orchestration Platform Transformation:
Real-time contextual knowledge system for analysis-driven CI/CD decisions.

This module provides:
- Real-time project state analysis
- Contextual knowledge extraction
- Analysis-driven decision making
- Intelligent CI/CD workflow orchestration
- Dynamic quality gates and thresholds
- Predictive analysis for build/deployment decisions
"""

import os
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class AnalysisContext:
    """Represents analysis context for decision making."""
    context_id: str
    timestamp: str
    project_state: Dict[str, Any]
    quality_metrics: Dict[str, float]
    risk_factors: List[str]
    confidence_score: float
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QualityGate:
    """Represents a dynamic quality gate."""
    name: str
    metric: str
    threshold: float
    operator: str  # ">=", "<=", "==", "!=", ">", "<"
    severity: str  # "critical", "high", "medium", "low"
    adaptive: bool = True
    historical_data: List[float] = field(default_factory=list)
    
    def evaluate(self, current_value: float) -> Tuple[bool, str]:
        """Evaluate if the quality gate passes."""
        operators = {
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y
        }
        
        passes = operators[self.operator](current_value, self.threshold)
        status = "PASS" if passes else "FAIL"
        message = f"{self.name}: {current_value} {self.operator} {self.threshold} = {status}"
        
        return passes, message
    
    def adapt_threshold(self, historical_values: List[float]) -> None:
        """Adapt threshold based on historical performance."""
        if not self.adaptive or len(historical_values) < 5:
            return
        
        # Calculate adaptive threshold based on historical performance
        avg = sum(historical_values) / len(historical_values)
        std_dev = (sum((x - avg) ** 2 for x in historical_values) / len(historical_values)) ** 0.5
        
        # Adjust threshold to be within 1 standard deviation of historical average
        if self.operator in [">=", ">"]:
            # For "greater than" gates, set threshold to avg - std_dev
            self.threshold = max(self.threshold * 0.9, avg - std_dev)
        else:
            # For "less than" gates, set threshold to avg + std_dev
            self.threshold = min(self.threshold * 1.1, avg + std_dev)

@dataclass
class CICDDecision:
    """Represents a CI/CD decision with context."""
    decision_id: str
    timestamp: str
    decision_type: str  # "build", "test", "deploy", "rollback"
    action: str  # "proceed", "block", "warn", "manual_review"
    confidence: float
    reasoning: List[str]
    context: AnalysisContext
    quality_gates: List[Tuple[str, bool, str]] = field(default_factory=list)
    
@dataclass
class ProjectState:
    """Real-time project state representation."""
    timestamp: str
    commit_hash: str
    branch: str
    files_changed: List[str]
    lines_added: int
    lines_removed: int
    test_coverage: float
    complexity_score: float
    security_score: float
    performance_score: float
    dependency_health: float
    build_status: str
    deployment_status: str
    active_issues: int
    recent_failures: int

class AnalysisFirstEngine:
    """Main engine for analysis-first CI/CD orchestration."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.quality_gates = self._initialize_quality_gates()
        self.analysis_history = deque(maxlen=100)
        self.decision_history = deque(maxlen=50)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.monitoring_active = False
        self._lock = threading.Lock()
    
    def _initialize_quality_gates(self) -> List[QualityGate]:
        """Initialize default quality gates."""
        return [
            QualityGate(
                name="Test Coverage",
                metric="test_coverage",
                threshold=80.0,
                operator=">=",
                severity="high",
                adaptive=True
            ),
            QualityGate(
                name="Code Complexity",
                metric="complexity_score",
                threshold=7.0,
                operator="<=",
                severity="medium",
                adaptive=True
            ),
            QualityGate(
                name="Security Score",
                metric="security_score",
                threshold=85.0,
                operator=">=",
                severity="critical",
                adaptive=False
            ),
            QualityGate(
                name="Performance Score",
                metric="performance_score",
                threshold=75.0,
                operator=">=",
                severity="high",
                adaptive=True
            ),
            QualityGate(
                name="Dependency Health",
                metric="dependency_health",
                threshold=90.0,
                operator=">=",
                severity="medium",
                adaptive=True
            ),
            QualityGate(
                name="Recent Failures",
                metric="recent_failures",
                threshold=3,
                operator="<=",
                severity="high",
                adaptive=False
            )
        ]
    
    def analyze_project_state(self) -> ProjectState:
        """Analyze current project state."""
        try:
            # Get current git information
            commit_hash = self._get_current_commit()
            branch = self._get_current_branch()
            files_changed = self._get_changed_files()
            
            # Calculate code metrics
            lines_added, lines_removed = self._get_line_changes()
            test_coverage = self._calculate_test_coverage()
            complexity_score = self._calculate_complexity()
            security_score = self._calculate_security_score()
            performance_score = self._calculate_performance_score()
            dependency_health = self._calculate_dependency_health()
            
            # Get build/deployment status
            build_status = self._get_build_status()
            deployment_status = self._get_deployment_status()
            
            # Count issues and failures
            active_issues = self._count_active_issues()
            recent_failures = self._count_recent_failures()
            
            return ProjectState(
                timestamp=datetime.now().isoformat(),
                commit_hash=commit_hash,
                branch=branch,
                files_changed=files_changed,
                lines_added=lines_added,
                lines_removed=lines_removed,
                test_coverage=test_coverage,
                complexity_score=complexity_score,
                security_score=security_score,
                performance_score=performance_score,
                dependency_health=dependency_health,
                build_status=build_status,
                deployment_status=deployment_status,
                active_issues=active_issues,
                recent_failures=recent_failures
            )
        
        except Exception as e:
            logger.error(f"Failed to analyze project state: {e}")
            # Return default state
            return ProjectState(
                timestamp=datetime.now().isoformat(),
                commit_hash="unknown",
                branch="unknown",
                files_changed=[],
                lines_added=0,
                lines_removed=0,
                test_coverage=0.0,
                complexity_score=10.0,
                security_score=50.0,
                performance_score=50.0,
                dependency_health=50.0,
                build_status="unknown",
                deployment_status="unknown",
                active_issues=0,
                recent_failures=0
            )
    
    def _get_current_commit(self) -> str:
        """Get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def _get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def _get_changed_files(self) -> List[str]:
        """Get list of changed files."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.split('\n') if f.strip()]
            return []
        except Exception:
            return []
    
    def _get_line_changes(self) -> Tuple[int, int]:
        """Get lines added and removed."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "diff", "--numstat", "HEAD~1", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                added, removed = 0, 0
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                            added += int(parts[0])
                            removed += int(parts[1])
                return added, removed
            return 0, 0
        except Exception:
            return 0, 0
    
    def _calculate_test_coverage(self) -> float:
        """Calculate test coverage percentage."""
        # Simplified calculation - count test files vs source files
        try:
            source_files = list(self.project_root.rglob("*.py"))
            test_files = [f for f in source_files if "test" in f.name.lower()]
            
            if len(source_files) == 0:
                return 0.0
            
            # Rough estimate: assume each test file covers 3 source files
            estimated_coverage = min(100.0, (len(test_files) * 3 / len(source_files)) * 100)
            return round(estimated_coverage, 1)
        except Exception:
            return 0.0
    
    def _calculate_complexity(self) -> float:
        """Calculate average code complexity."""
        try:
            # Simplified complexity calculation
            total_complexity = 0
            file_count = 0
            
            for py_file in self.project_root.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Count complexity indicators
                    complexity = (
                        content.count('if ') +
                        content.count('elif ') +
                        content.count('for ') +
                        content.count('while ') +
                        content.count('try:') +
                        content.count('except ') +
                        content.count('def ') * 0.5
                    )
                    
                    lines = len(content.splitlines())
                    if lines > 0:
                        total_complexity += complexity / lines * 100
                        file_count += 1
                
                except Exception:
                    continue
            
            return round(total_complexity / file_count if file_count > 0 else 5.0, 1)
        except Exception:
            return 5.0
    
    def _calculate_security_score(self) -> float:
        """Calculate security score."""
        try:
            # Simplified security scoring
            security_issues = 0
            total_files = 0
            
            for py_file in self.project_root.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                    
                    # Check for potential security issues
                    if 'eval(' in content:
                        security_issues += 3
                    if 'exec(' in content:
                        security_issues += 3
                    if 'shell=true' in content:
                        security_issues += 2
                    if 'password' in content and '=' in content:
                        security_issues += 1
                    if 'secret' in content and '=' in content:
                        security_issues += 1
                    
                    total_files += 1
                
                except Exception:
                    continue
            
            # Calculate score (100 - issues per file * 10)
            score = max(0, 100 - (security_issues / max(total_files, 1)) * 10)
            return round(score, 1)
        except Exception:
            return 85.0
    
    def _calculate_performance_score(self) -> float:
        """Calculate performance score."""
        try:
            # Simplified performance scoring based on code patterns
            performance_issues = 0
            total_files = 0
            
            for py_file in self.project_root.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                    
                    # Check for performance anti-patterns
                    if 'time.sleep(' in content:
                        performance_issues += 1
                    if content.count('for ') > 3 and 'in range(' in content:
                        performance_issues += 1  # Nested loops
                    if 'import *' in content:
                        performance_issues += 0.5
                    
                    total_files += 1
                
                except Exception:
                    continue
            
            # Calculate score
            score = max(0, 100 - (performance_issues / max(total_files, 1)) * 15)
            return round(score, 1)
        except Exception:
            return 75.0
    
    def _calculate_dependency_health(self) -> float:
        """Calculate dependency health score."""
        try:
            # Check for requirements files and analyze dependencies
            req_files = list(self.project_root.glob("*requirements*.txt"))
            req_files.extend(list(self.project_root.glob("pyproject.toml")))
            
            if not req_files:
                return 50.0  # No dependency management
            
            # Count dependencies and check for version pinning
            total_deps = 0
            pinned_deps = 0
            
            for req_file in req_files:
                try:
                    with open(req_file, 'r') as f:
                        content = f.read()
                    
                    lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                    for line in lines:
                        if '==' in line or '>=' in line or '<=' in line:
                            total_deps += 1
                            if '==' in line:
                                pinned_deps += 1
                        elif line and not line.startswith('['):
                            total_deps += 1
                
                except Exception:
                    continue
            
            if total_deps == 0:
                return 90.0
            
            # Score based on version pinning ratio
            pinning_ratio = pinned_deps / total_deps
            score = 60 + (pinning_ratio * 40)  # 60-100 based on pinning
            return round(score, 1)
        except Exception:
            return 90.0
    
    def _get_build_status(self) -> str:
        """Get current build status."""
        # This would integrate with actual CI/CD systems
        return "unknown"
    
    def _get_deployment_status(self) -> str:
        """Get current deployment status."""
        # This would integrate with actual deployment systems
        return "unknown"
    
    def _count_active_issues(self) -> int:
        """Count active issues."""
        # This would integrate with issue tracking systems
        return 0
    
    def _count_recent_failures(self) -> int:
        """Count recent build/deployment failures."""
        # This would integrate with CI/CD history
        return 0
    
    def create_analysis_context(self, project_state: ProjectState) -> AnalysisContext:
        """Create analysis context from project state."""
        # Extract quality metrics
        quality_metrics = {
            "test_coverage": project_state.test_coverage,
            "complexity_score": project_state.complexity_score,
            "security_score": project_state.security_score,
            "performance_score": project_state.performance_score,
            "dependency_health": project_state.dependency_health
        }
        
        # Identify risk factors
        risk_factors = []
        if project_state.test_coverage < 70:
            risk_factors.append("Low test coverage")
        if project_state.complexity_score > 8:
            risk_factors.append("High code complexity")
        if project_state.security_score < 80:
            risk_factors.append("Security concerns")
        if project_state.recent_failures > 2:
            risk_factors.append("Recent build failures")
        if len(project_state.files_changed) > 20:
            risk_factors.append("Large changeset")
        
        # Calculate confidence score
        confidence_factors = [
            min(project_state.test_coverage / 100, 1.0),
            max(0, 1.0 - (project_state.complexity_score - 5) / 10),
            project_state.security_score / 100,
            project_state.performance_score / 100,
            project_state.dependency_health / 100
        ]
        confidence_score = sum(confidence_factors) / len(confidence_factors)
        
        # Generate recommendations
        recommendations = []
        if project_state.test_coverage < 80:
            recommendations.append("Increase test coverage before deployment")
        if project_state.complexity_score > 7:
            recommendations.append("Refactor complex code sections")
        if project_state.security_score < 85:
            recommendations.append("Address security vulnerabilities")
        if len(project_state.files_changed) > 15:
            recommendations.append("Consider breaking changes into smaller deployments")
        
        return AnalysisContext(
            context_id=f"ctx_{int(time.time())}",
            timestamp=project_state.timestamp,
            project_state=asdict(project_state),
            quality_metrics=quality_metrics,
            risk_factors=risk_factors,
            confidence_score=confidence_score,
            recommendations=recommendations
        )
    
    def evaluate_quality_gates(self, context: AnalysisContext) -> List[Tuple[str, bool, str]]:
        """Evaluate all quality gates against current context."""
        results = []
        
        for gate in self.quality_gates:
            if gate.metric in context.quality_metrics:
                current_value = context.quality_metrics[gate.metric]
                passes, message = gate.evaluate(current_value)
                results.append((gate.name, passes, message))
                
                # Update historical data for adaptive gates
                if gate.adaptive:
                    gate.historical_data.append(current_value)
                    if len(gate.historical_data) > 20:
                        gate.historical_data = gate.historical_data[-20:]
                    gate.adapt_threshold(gate.historical_data)
        
        return results
    
    def make_cicd_decision(self, context: AnalysisContext, decision_type: str) -> CICDDecision:
        """Make a CI/CD decision based on analysis context."""
        quality_gate_results = self.evaluate_quality_gates(context)
        
        # Evaluate quality gates
        critical_failures = [r for r in quality_gate_results if not r[1] and any(g.severity == "critical" for g in self.quality_gates if g.name == r[0])]
        high_failures = [r for r in quality_gate_results if not r[1] and any(g.severity == "high" for g in self.quality_gates if g.name == r[0])]
        
        # Decision logic
        reasoning = []
        
        if critical_failures:
            action = "block"
            reasoning.append(f"Critical quality gates failed: {[r[0] for r in critical_failures]}")
        elif len(high_failures) >= 2:
            action = "manual_review"
            reasoning.append(f"Multiple high-priority quality gates failed: {[r[0] for r in high_failures]}")
        elif high_failures:
            action = "warn"
            reasoning.append(f"High-priority quality gate failed: {[r[0] for r in high_failures]}")
        elif context.confidence_score < 0.6:
            action = "manual_review"
            reasoning.append(f"Low confidence score: {context.confidence_score:.2f}")
        elif len(context.risk_factors) >= 3:
            action = "warn"
            reasoning.append(f"Multiple risk factors identified: {context.risk_factors}")
        else:
            action = "proceed"
            reasoning.append("All quality gates passed and confidence is high")
        
        # Add context-specific reasoning
        if decision_type == "deploy" and context.project_state.get("recent_failures", 0) > 1:
            if action == "proceed":
                action = "warn"
            reasoning.append("Recent deployment failures detected")
        
        if decision_type == "build" and len(context.project_state.get("files_changed", [])) > 20:
            reasoning.append("Large changeset detected - consider incremental approach")
        
        return CICDDecision(
            decision_id=f"dec_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            decision_type=decision_type,
            action=action,
            confidence=context.confidence_score,
            reasoning=reasoning,
            context=context,
            quality_gates=quality_gate_results
        )
    
    def start_real_time_monitoring(self, interval: int = 60) -> None:
        """Start real-time project monitoring."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Analyze current state
                    project_state = self.analyze_project_state()
                    context = self.create_analysis_context(project_state)
                    
                    # Store in history
                    with self._lock:
                        self.analysis_history.append(context)
                    
                    # Log current state
                    logger.info(f"Project analysis: confidence={context.confidence_score:.2f}, risks={len(context.risk_factors)}")
                    
                    time.sleep(interval)
                
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(interval)
        
        # Start monitoring in background thread
        self.executor.submit(monitor_loop)
        logger.info(f"Real-time monitoring started (interval: {interval}s)")
    
    def stop_real_time_monitoring(self) -> None:
        """Stop real-time project monitoring."""
        self.monitoring_active = False
        logger.info("Real-time monitoring stopped")
    
    def get_current_analysis(self) -> Optional[AnalysisContext]:
        """Get the most recent analysis context."""
        with self._lock:
            return self.analysis_history[-1] if self.analysis_history else None
    
    def get_analysis_history(self, limit: int = 10) -> List[AnalysisContext]:
        """Get recent analysis history."""
        with self._lock:
            return list(self.analysis_history)[-limit:]
    
    def get_decision_history(self, limit: int = 10) -> List[CICDDecision]:
        """Get recent decision history."""
        with self._lock:
            return list(self.decision_history)[-limit:]
    
    def export_analysis_data(self, filepath: Path) -> None:
        """Export analysis data for external systems."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "quality_gates": [asdict(gate) for gate in self.quality_gates],
            "analysis_history": [asdict(ctx) for ctx in self.analysis_history],
            "decision_history": [asdict(dec) for dec in self.decision_history]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

def create_analysis_first_engine(project_root: str = ".") -> AnalysisFirstEngine:
    """Create and configure an analysis-first engine."""
    return AnalysisFirstEngine(project_root)

def analyze_for_cicd_decision(project_root: str = ".", decision_type: str = "build") -> CICDDecision:
    """Convenience function to analyze project and make CI/CD decision."""
    engine = create_analysis_first_engine(project_root)
    project_state = engine.analyze_project_state()
    context = engine.create_analysis_context(project_state)
    decision = engine.make_cicd_decision(context, decision_type)
    
    # Store decision in history
    with engine._lock:
        engine.decision_history.append(decision)
    
    return decision

if __name__ == "__main__":
    # Example usage
    engine = create_analysis_first_engine()
    
    # Analyze current state
    project_state = engine.analyze_project_state()
    print(f"📊 Project State Analysis:")
    print(f"   Branch: {project_state.branch}")
    print(f"   Files changed: {len(project_state.files_changed)}")
    print(f"   Test coverage: {project_state.test_coverage}%")
    print(f"   Complexity: {project_state.complexity_score}")
    print(f"   Security: {project_state.security_score}")
    
    # Create analysis context
    context = engine.create_analysis_context(project_state)
    print(f"\n🧠 Analysis Context:")
    print(f"   Confidence: {context.confidence_score:.2f}")
    print(f"   Risk factors: {len(context.risk_factors)}")
    print(f"   Recommendations: {len(context.recommendations)}")
    
    # Make CI/CD decisions
    for decision_type in ["build", "test", "deploy"]:
        decision = engine.make_cicd_decision(context, decision_type)
        print(f"\n🚀 {decision_type.title()} Decision: {decision.action.upper()}")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Reasoning: {decision.reasoning[0] if decision.reasoning else 'No specific reasoning'}")
    
    # Export data
    engine.export_analysis_data(Path("analysis_first_data.json"))
    print(f"\n💾 Analysis data exported to: analysis_first_data.json")

