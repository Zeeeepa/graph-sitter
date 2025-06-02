"""
Advanced Analytics Engine for Dashboard

This module provides sophisticated analytics and insights for development workflows,
code quality metrics, and team productivity analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from graph_sitter import Codebase
from ..agents.chat_agent import ChatAgent
from ...shared.logging.get_logger import get_logger

logger = get_logger(__name__)

class MetricType(Enum):
    """Types of metrics we can analyze"""
    CODE_QUALITY = "code_quality"
    PRODUCTIVITY = "productivity"
    COLLABORATION = "collaboration"
    TECHNICAL_DEBT = "technical_debt"
    PERFORMANCE = "performance"
    SECURITY = "security"

@dataclass
class CodeMetric:
    """Represents a code quality metric"""
    name: str
    value: float
    unit: str
    trend: str  # "up", "down", "stable"
    description: str
    severity: str  # "low", "medium", "high", "critical"
    recommendations: List[str]

@dataclass
class AnalyticsReport:
    """Comprehensive analytics report"""
    timestamp: datetime
    project_id: str
    metrics: Dict[MetricType, List[CodeMetric]]
    insights: List[str]
    recommendations: List[str]
    risk_score: float
    health_score: float

class AdvancedAnalyticsEngine:
    """Advanced analytics engine for code and workflow analysis"""
    
    def __init__(self):
        self.codebases: Dict[str, Codebase] = {}
        self.analysis_cache: Dict[str, AnalyticsReport] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        
    async def analyze_codebase(self, project_id: str, codebase_path: str) -> AnalyticsReport:
        """Perform comprehensive codebase analysis"""
        
        try:
            # Load or get cached codebase
            if project_id not in self.codebases:
                self.codebases[project_id] = Codebase(codebase_path)
            
            codebase = self.codebases[project_id]
            
            # Perform various analyses
            code_quality_metrics = await self._analyze_code_quality(codebase)
            technical_debt_metrics = await self._analyze_technical_debt(codebase)
            security_metrics = await self._analyze_security(codebase)
            performance_metrics = await self._analyze_performance(codebase)
            
            # Generate insights and recommendations
            insights = await self._generate_insights(codebase, {
                MetricType.CODE_QUALITY: code_quality_metrics,
                MetricType.TECHNICAL_DEBT: technical_debt_metrics,
                MetricType.SECURITY: security_metrics,
                MetricType.PERFORMANCE: performance_metrics
            })
            
            recommendations = await self._generate_recommendations(codebase, insights)
            
            # Calculate health and risk scores
            health_score = self._calculate_health_score(code_quality_metrics, technical_debt_metrics)
            risk_score = self._calculate_risk_score(security_metrics, technical_debt_metrics)
            
            report = AnalyticsReport(
                timestamp=datetime.now(),
                project_id=project_id,
                metrics={
                    MetricType.CODE_QUALITY: code_quality_metrics,
                    MetricType.TECHNICAL_DEBT: technical_debt_metrics,
                    MetricType.SECURITY: security_metrics,
                    MetricType.PERFORMANCE: performance_metrics
                },
                insights=insights,
                recommendations=recommendations,
                risk_score=risk_score,
                health_score=health_score
            )
            
            # Cache the report
            self.analysis_cache[project_id] = report
            
            return report
            
        except Exception as e:
            logger.error(f"Error analyzing codebase {project_id}: {e}")
            raise
    
    async def _analyze_code_quality(self, codebase: Codebase) -> List[CodeMetric]:
        """Analyze code quality metrics"""
        
        metrics = []
        
        try:
            # Complexity analysis
            total_functions = len(codebase.functions)
            complex_functions = len([f for f in codebase.functions if len(f.function_calls) > 10])
            complexity_ratio = complex_functions / total_functions if total_functions > 0 else 0
            
            metrics.append(CodeMetric(
                name="Function Complexity",
                value=complexity_ratio * 100,
                unit="%",
                trend="stable",
                description=f"{complex_functions} out of {total_functions} functions are highly complex",
                severity="medium" if complexity_ratio > 0.2 else "low",
                recommendations=[
                    "Break down complex functions into smaller, more manageable pieces",
                    "Consider using design patterns to reduce complexity",
                    "Add comprehensive unit tests for complex functions"
                ]
            ))
            
            # Dead code analysis
            unused_functions = [f for f in codebase.functions if len(f.usages) == 0]
            dead_code_ratio = len(unused_functions) / total_functions if total_functions > 0 else 0
            
            metrics.append(CodeMetric(
                name="Dead Code",
                value=dead_code_ratio * 100,
                unit="%",
                trend="down",
                description=f"{len(unused_functions)} unused functions detected",
                severity="high" if dead_code_ratio > 0.1 else "medium",
                recommendations=[
                    "Remove unused functions to reduce codebase size",
                    "Review and refactor legacy code",
                    "Implement automated dead code detection in CI/CD"
                ]
            ))
            
            # Documentation coverage
            documented_functions = len([f for f in codebase.functions if f.docstring])
            doc_coverage = documented_functions / total_functions if total_functions > 0 else 0
            
            metrics.append(CodeMetric(
                name="Documentation Coverage",
                value=doc_coverage * 100,
                unit="%",
                trend="up",
                description=f"{documented_functions} out of {total_functions} functions have documentation",
                severity="low" if doc_coverage > 0.8 else "medium",
                recommendations=[
                    "Add docstrings to undocumented functions",
                    "Use consistent documentation format",
                    "Include examples in complex function documentation"
                ]
            ))
            
            # Test coverage estimation
            test_files = [f for f in codebase.files if "test" in f.name.lower()]
            test_coverage_estimate = min(len(test_files) / len(codebase.files) * 2, 1.0) if codebase.files else 0
            
            metrics.append(CodeMetric(
                name="Test Coverage (Estimated)",
                value=test_coverage_estimate * 100,
                unit="%",
                trend="stable",
                description=f"Estimated based on {len(test_files)} test files",
                severity="critical" if test_coverage_estimate < 0.5 else "medium",
                recommendations=[
                    "Increase test coverage for critical functions",
                    "Implement integration tests",
                    "Set up automated test coverage reporting"
                ]
            ))
            
        except Exception as e:
            logger.error(f"Error in code quality analysis: {e}")
        
        return metrics
    
    async def _analyze_technical_debt(self, codebase: Codebase) -> List[CodeMetric]:
        """Analyze technical debt indicators"""
        
        metrics = []
        
        try:
            # TODO/FIXME comments analysis
            todo_count = 0
            fixme_count = 0
            
            for file in codebase.files:
                if hasattr(file, 'source'):
                    source_lower = file.source.lower()
                    todo_count += source_lower.count('todo')
                    fixme_count += source_lower.count('fixme')
            
            total_debt_markers = todo_count + fixme_count
            
            metrics.append(CodeMetric(
                name="Technical Debt Markers",
                value=total_debt_markers,
                unit="items",
                trend="stable",
                description=f"{todo_count} TODOs and {fixme_count} FIXMEs found",
                severity="high" if total_debt_markers > 50 else "medium",
                recommendations=[
                    "Address high-priority FIXME items",
                    "Convert TODOs into proper issues",
                    "Set up automated debt tracking"
                ]
            ))
            
            # Duplicate code analysis (simplified)
            function_signatures = {}
            duplicate_functions = 0
            
            for func in codebase.functions:
                signature = f"{func.name}_{len(func.parameters) if hasattr(func, 'parameters') else 0}"
                if signature in function_signatures:
                    duplicate_functions += 1
                else:
                    function_signatures[signature] = func
            
            metrics.append(CodeMetric(
                name="Potential Code Duplication",
                value=duplicate_functions,
                unit="functions",
                trend="stable",
                description=f"{duplicate_functions} functions with similar signatures",
                severity="medium" if duplicate_functions > 10 else "low",
                recommendations=[
                    "Review functions with similar signatures",
                    "Extract common functionality into shared utilities",
                    "Implement code deduplication tools"
                ]
            ))
            
        except Exception as e:
            logger.error(f"Error in technical debt analysis: {e}")
        
        return metrics
    
    async def _analyze_security(self, codebase: Codebase) -> List[CodeMetric]:
        """Analyze security-related metrics"""
        
        metrics = []
        
        try:
            # Security-sensitive patterns
            security_patterns = [
                'password', 'secret', 'token', 'api_key', 'private_key',
                'eval(', 'exec(', 'subprocess', 'os.system'
            ]
            
            security_issues = 0
            for file in codebase.files:
                if hasattr(file, 'source'):
                    source_lower = file.source.lower()
                    for pattern in security_patterns:
                        security_issues += source_lower.count(pattern)
            
            metrics.append(CodeMetric(
                name="Security Hotspots",
                value=security_issues,
                unit="occurrences",
                trend="stable",
                description=f"{security_issues} potential security-sensitive code patterns",
                severity="critical" if security_issues > 20 else "medium",
                recommendations=[
                    "Review security-sensitive code patterns",
                    "Implement secure coding practices",
                    "Use security scanning tools in CI/CD",
                    "Store secrets in secure vaults"
                ]
            ))
            
        except Exception as e:
            logger.error(f"Error in security analysis: {e}")
        
        return metrics
    
    async def _analyze_performance(self, codebase: Codebase) -> List[CodeMetric]:
        """Analyze performance-related metrics"""
        
        metrics = []
        
        try:
            # Large file analysis
            large_files = [f for f in codebase.files if hasattr(f, 'source') and len(f.source.split('\n')) > 500]
            
            metrics.append(CodeMetric(
                name="Large Files",
                value=len(large_files),
                unit="files",
                trend="stable",
                description=f"{len(large_files)} files with >500 lines",
                severity="medium" if len(large_files) > 10 else "low",
                recommendations=[
                    "Break down large files into smaller modules",
                    "Separate concerns into different files",
                    "Consider refactoring large classes"
                ]
            ))
            
            # Deep inheritance analysis
            deep_inheritance = 0
            for cls in codebase.classes:
                if hasattr(cls, 'superclasses') and len(cls.superclasses) > 3:
                    deep_inheritance += 1
            
            metrics.append(CodeMetric(
                name="Deep Inheritance",
                value=deep_inheritance,
                unit="classes",
                trend="stable",
                description=f"{deep_inheritance} classes with deep inheritance chains",
                severity="medium" if deep_inheritance > 5 else "low",
                recommendations=[
                    "Consider composition over inheritance",
                    "Flatten inheritance hierarchies where possible",
                    "Review complex inheritance patterns"
                ]
            ))
            
        except Exception as e:
            logger.error(f"Error in performance analysis: {e}")
        
        return metrics
    
    async def _generate_insights(self, codebase: Codebase, metrics: Dict[MetricType, List[CodeMetric]]) -> List[str]:
        """Generate actionable insights from metrics"""
        
        insights = []
        
        try:
            # Code quality insights
            quality_metrics = metrics.get(MetricType.CODE_QUALITY, [])
            for metric in quality_metrics:
                if metric.severity in ["high", "critical"]:
                    insights.append(f"🔴 {metric.name}: {metric.description}")
                elif metric.severity == "medium":
                    insights.append(f"🟡 {metric.name}: {metric.description}")
            
            # Technical debt insights
            debt_metrics = metrics.get(MetricType.TECHNICAL_DEBT, [])
            total_debt_score = sum(m.value for m in debt_metrics if m.unit == "items")
            if total_debt_score > 30:
                insights.append(f"📈 High technical debt detected: {total_debt_score} items need attention")
            
            # Security insights
            security_metrics = metrics.get(MetricType.SECURITY, [])
            for metric in security_metrics:
                if metric.value > 10:
                    insights.append(f"🔒 Security review needed: {metric.description}")
            
            # Overall health insight
            total_functions = len(codebase.functions)
            total_classes = len(codebase.classes)
            total_files = len(codebase.files)
            
            insights.append(f"📊 Codebase overview: {total_files} files, {total_classes} classes, {total_functions} functions")
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights
    
    async def _generate_recommendations(self, codebase: Codebase, insights: List[str]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = [
            "🎯 Set up automated code quality checks in CI/CD pipeline",
            "📝 Implement consistent code documentation standards",
            "🧪 Increase test coverage for critical business logic",
            "🔍 Regular code reviews to maintain quality standards",
            "🛡️ Implement security scanning tools",
            "📈 Track metrics over time to measure improvement",
            "🔄 Regular refactoring sessions to reduce technical debt",
            "📚 Team training on best practices and coding standards"
        ]
        
        return recommendations
    
    def _calculate_health_score(self, quality_metrics: List[CodeMetric], debt_metrics: List[CodeMetric]) -> float:
        """Calculate overall codebase health score (0-100)"""
        
        try:
            # Start with base score
            score = 100.0
            
            # Deduct points for quality issues
            for metric in quality_metrics:
                if metric.severity == "critical":
                    score -= 20
                elif metric.severity == "high":
                    score -= 10
                elif metric.severity == "medium":
                    score -= 5
            
            # Deduct points for technical debt
            for metric in debt_metrics:
                if metric.value > 50:
                    score -= 15
                elif metric.value > 20:
                    score -= 10
                elif metric.value > 10:
                    score -= 5
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0  # Default neutral score
    
    def _calculate_risk_score(self, security_metrics: List[CodeMetric], debt_metrics: List[CodeMetric]) -> float:
        """Calculate risk score (0-100, higher is riskier)"""
        
        try:
            risk = 0.0
            
            # Add risk for security issues
            for metric in security_metrics:
                if metric.value > 20:
                    risk += 40
                elif metric.value > 10:
                    risk += 25
                elif metric.value > 5:
                    risk += 15
            
            # Add risk for technical debt
            for metric in debt_metrics:
                if metric.value > 50:
                    risk += 30
                elif metric.value > 20:
                    risk += 20
                elif metric.value > 10:
                    risk += 10
            
            return min(100.0, risk)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 25.0  # Default low-medium risk
    
    async def get_analytics_summary(self, project_id: str) -> Dict[str, Any]:
        """Get analytics summary for dashboard"""
        
        try:
            report = self.analysis_cache.get(project_id)
            if not report:
                return {"error": "No analytics data available"}
            
            return {
                "health_score": report.health_score,
                "risk_score": report.risk_score,
                "total_insights": len(report.insights),
                "critical_issues": len([
                    metric for metrics in report.metrics.values() 
                    for metric in metrics 
                    if metric.severity == "critical"
                ]),
                "last_analysis": report.timestamp.isoformat(),
                "top_insights": report.insights[:3],
                "top_recommendations": report.recommendations[:3]
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {"error": str(e)}

