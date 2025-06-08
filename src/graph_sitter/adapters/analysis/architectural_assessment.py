#!/usr/bin/env python3
"""
🏗️ ARCHITECTURAL ASSESSMENT ENGINE 🏗️

Step 2 of CI/CD Orchestration Platform Transformation:
Comprehensive assessment of current contexten capabilities and system architecture.

This module provides:
- Current system capability mapping
- Architecture documentation and analysis
- Performance baseline collection
- Gap analysis for CI/CD transformation
- Integration point identification
- Technology stack assessment
"""

import os
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
import ast

logger = logging.getLogger(__name__)

@dataclass
class SystemCapability:
    """Represents a system capability or feature."""
    name: str
    category: str
    description: str
    current_state: str  # "present", "partial", "missing"
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    integration_points: List[str] = field(default_factory=list)

@dataclass
class ArchitecturalComponent:
    """Represents an architectural component."""
    name: str
    type: str  # "service", "library", "tool", "framework"
    path: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceBaseline:
    """Performance baseline metrics."""
    metric_name: str
    current_value: float
    unit: str
    measurement_time: str
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GapAnalysisItem:
    """Represents a gap in current capabilities."""
    area: str
    current_state: str
    desired_state: str
    priority: str  # "critical", "high", "medium", "low"
    effort_estimate: str  # "small", "medium", "large", "xl"
    impact: str  # "high", "medium", "low"
    recommendations: List[str] = field(default_factory=list)

@dataclass
class ArchitecturalAssessment:
    """Complete architectural assessment results."""
    timestamp: str
    project_root: str
    capabilities: List[SystemCapability] = field(default_factory=list)
    components: List[ArchitecturalComponent] = field(default_factory=list)
    performance_baselines: List[PerformanceBaseline] = field(default_factory=list)
    gap_analysis: List[GapAnalysisItem] = field(default_factory=list)
    technology_stack: Dict[str, Any] = field(default_factory=dict)
    integration_map: Dict[str, List[str]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def save_to_file(self, filepath: Path) -> None:
        """Save assessment to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

class ArchitecturalAssessmentEngine:
    """Main engine for conducting architectural assessments."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.assessment = ArchitecturalAssessment(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            project_root=str(self.project_root)
        )
    
    def assess_contexten_capabilities(self) -> List[SystemCapability]:
        """Assess current contexten system capabilities."""
        capabilities = []
        
        # Define expected CI/CD capabilities
        expected_capabilities = {
            "Agent Orchestration": {
                "description": "Ability to orchestrate multiple AI agents",
                "indicators": ["agents/", "ContextenApp", "CodeAgent", "ChatAgent"]
            },
            "GitHub Integration": {
                "description": "Integration with GitHub for PR management",
                "indicators": ["github", "pull_request", "create_pr_comment"]
            },
            "Linear Integration": {
                "description": "Integration with Linear for issue tracking",
                "indicators": ["linear", "LinearEvent", "LinearIssue"]
            },
            "Slack Integration": {
                "description": "Integration with Slack for notifications",
                "indicators": ["slack", "SlackEvent"]
            },
            "Code Analysis": {
                "description": "Code analysis and quality assessment",
                "indicators": ["analysis", "graph_sitter", "codebase"]
            },
            "LangChain Integration": {
                "description": "LangChain framework integration",
                "indicators": ["langchain", "create_agent", "tools"]
            },
            "Vector Search": {
                "description": "Vector-based search and RAG capabilities",
                "indicators": ["VectorIndex", "embedding", "rag"]
            },
            "Build Automation": {
                "description": "Automated build and deployment processes",
                "indicators": ["build", "deploy", "ci", "cd"]
            },
            "Testing Framework": {
                "description": "Automated testing capabilities",
                "indicators": ["test", "pytest", "unittest"]
            },
            "Monitoring & Observability": {
                "description": "System monitoring and observability",
                "indicators": ["monitoring", "metrics", "logging", "tracer"]
            }
        }
        
        for capability_name, config in expected_capabilities.items():
            evidence = self._find_capability_evidence(config["indicators"])
            
            if len(evidence) >= 3:
                state = "present"
                confidence = 0.9
            elif len(evidence) >= 1:
                state = "partial"
                confidence = 0.6
            else:
                state = "missing"
                confidence = 0.1
            
            capability = SystemCapability(
                name=capability_name,
                category="CI/CD",
                description=config["description"],
                current_state=state,
                confidence=confidence,
                evidence=evidence
            )
            capabilities.append(capability)
        
        return capabilities
    
    def _find_capability_evidence(self, indicators: List[str]) -> List[str]:
        """Find evidence of capability indicators in the codebase."""
        evidence = []
        
        for indicator in indicators:
            # Search for files containing the indicator
            try:
                result = subprocess.run(
                    ["grep", "-r", "-l", indicator, str(self.project_root)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    files = result.stdout.strip().split('\n')
                    for file in files[:3]:  # Limit evidence
                        if file and not file.startswith('.git'):
                            evidence.append(f"Found '{indicator}' in {file}")
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
        
        return evidence
    
    def analyze_architectural_components(self) -> List[ArchitecturalComponent]:
        """Analyze architectural components in the system."""
        components = []
        
        # Analyze contexten components
        contexten_path = self.project_root / "src" / "contexten"
        if contexten_path.exists():
            components.extend(self._analyze_contexten_components(contexten_path))
        
        # Analyze graph_sitter components
        graph_sitter_path = self.project_root / "src" / "graph_sitter"
        if graph_sitter_path.exists():
            components.extend(self._analyze_graph_sitter_components(graph_sitter_path))
        
        return components
    
    def _analyze_contexten_components(self, base_path: Path) -> List[ArchitecturalComponent]:
        """Analyze contexten-specific components."""
        components = []
        
        # Agent components
        agents_path = base_path / "agents"
        if agents_path.exists():
            for py_file in agents_path.rglob("*.py"):
                if py_file.name != "__init__.py":
                    component = self._analyze_python_component(py_file, "agent")
                    if component:
                        components.append(component)
        
        # Extension components
        extensions_path = base_path / "extensions"
        if extensions_path.exists():
            for py_file in extensions_path.rglob("*.py"):
                if py_file.name != "__init__.py":
                    component = self._analyze_python_component(py_file, "extension")
                    if component:
                        components.append(component)
        
        return components
    
    def _analyze_graph_sitter_components(self, base_path: Path) -> List[ArchitecturalComponent]:
        """Analyze graph_sitter-specific components."""
        components = []
        
        # Analysis components
        analysis_path = base_path / "adapters" / "analysis"
        if analysis_path.exists():
            for py_file in analysis_path.rglob("*.py"):
                if py_file.name != "__init__.py":
                    component = self._analyze_python_component(py_file, "analysis")
                    if component:
                        components.append(component)
        
        return components
    
    def _analyze_python_component(self, file_path: Path, component_type: str) -> Optional[ArchitecturalComponent]:
        """Analyze a Python file as an architectural component."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract imports
            dependencies = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    dependencies.append(node.module)
            
            # Extract classes and functions as interfaces
            interfaces = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    interfaces.append(f"class:{node.name}")
                elif isinstance(node, ast.FunctionDef):
                    interfaces.append(f"function:{node.name}")
            
            # Calculate metrics
            metrics = {
                "lines_of_code": len(content.splitlines()),
                "num_classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                "num_functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "num_imports": len(dependencies)
            }
            
            # Extract description from docstring
            description = "No description available"
            if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
                description = tree.body[0].value.value[:200] + "..." if len(tree.body[0].value.value) > 200 else tree.body[0].value.value
            
            return ArchitecturalComponent(
                name=file_path.stem,
                type=component_type,
                path=str(file_path.relative_to(self.project_root)),
                description=description,
                dependencies=dependencies[:10],  # Limit for readability
                interfaces=interfaces[:10],  # Limit for readability
                metrics=metrics
            )
        
        except Exception as e:
            logger.warning(f"Failed to analyze component {file_path}: {e}")
            return None
    
    def collect_performance_baselines(self) -> List[PerformanceBaseline]:
        """Collect current performance baselines."""
        baselines = []
        
        # File system metrics
        try:
            total_files = len(list(self.project_root.rglob("*.py")))
            baselines.append(PerformanceBaseline(
                metric_name="total_python_files",
                current_value=total_files,
                unit="files",
                measurement_time=time.strftime("%Y-%m-%d %H:%M:%S")
            ))
        except Exception as e:
            logger.warning(f"Failed to collect file metrics: {e}")
        
        # Code complexity metrics
        try:
            total_lines = 0
            for py_file in self.project_root.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        total_lines += len(f.readlines())
                except Exception:
                    pass
            
            baselines.append(PerformanceBaseline(
                metric_name="total_lines_of_code",
                current_value=total_lines,
                unit="lines",
                measurement_time=time.strftime("%Y-%m-%d %H:%M:%S")
            ))
        except Exception as e:
            logger.warning(f"Failed to collect complexity metrics: {e}")
        
        return baselines
    
    def perform_gap_analysis(self, capabilities: List[SystemCapability]) -> List[GapAnalysisItem]:
        """Perform gap analysis for CI/CD transformation."""
        gaps = []
        
        # Analyze missing or partial capabilities
        for capability in capabilities:
            if capability.current_state in ["missing", "partial"]:
                if capability.current_state == "missing":
                    priority = "high" if "Integration" in capability.name else "medium"
                    effort = "large" if "Integration" in capability.name else "medium"
                else:  # partial
                    priority = "medium"
                    effort = "medium"
                
                gap = GapAnalysisItem(
                    area=capability.name,
                    current_state=capability.current_state,
                    desired_state="present",
                    priority=priority,
                    effort_estimate=effort,
                    impact="high" if "Integration" in capability.name else "medium",
                    recommendations=self._generate_recommendations(capability)
                )
                gaps.append(gap)
        
        # Add CI/CD specific gaps
        cicd_gaps = [
            GapAnalysisItem(
                area="Automated Testing Pipeline",
                current_state="unknown",
                desired_state="comprehensive",
                priority="critical",
                effort_estimate="large",
                impact="high",
                recommendations=[
                    "Implement automated test execution on PR creation",
                    "Add test coverage reporting",
                    "Set up parallel test execution"
                ]
            ),
            GapAnalysisItem(
                area="Deployment Automation",
                current_state="manual",
                desired_state="automated",
                priority="high",
                effort_estimate="large",
                impact="high",
                recommendations=[
                    "Implement automated deployment pipelines",
                    "Add environment-specific configurations",
                    "Set up rollback mechanisms"
                ]
            ),
            GapAnalysisItem(
                area="Real-time Monitoring",
                current_state="limited",
                desired_state="comprehensive",
                priority="medium",
                effort_estimate="medium",
                impact="medium",
                recommendations=[
                    "Implement real-time performance monitoring",
                    "Add alerting for critical issues",
                    "Create monitoring dashboards"
                ]
            )
        ]
        
        gaps.extend(cicd_gaps)
        return gaps
    
    def _generate_recommendations(self, capability: SystemCapability) -> List[str]:
        """Generate recommendations for improving a capability."""
        recommendations = []
        
        if "GitHub" in capability.name:
            recommendations.extend([
                "Implement GitHub webhook handlers",
                "Add automated PR review workflows",
                "Set up GitHub Actions integration"
            ])
        elif "Linear" in capability.name:
            recommendations.extend([
                "Implement Linear webhook integration",
                "Add automated issue tracking",
                "Set up Linear-GitHub synchronization"
            ])
        elif "Code Analysis" in capability.name:
            recommendations.extend([
                "Enhance code quality metrics",
                "Add automated code review",
                "Implement security scanning"
            ])
        else:
            recommendations.append(f"Implement {capability.name} functionality")
        
        return recommendations
    
    def assess_technology_stack(self) -> Dict[str, Any]:
        """Assess current technology stack."""
        stack = {
            "languages": {},
            "frameworks": {},
            "tools": {},
            "dependencies": {}
        }
        
        # Analyze Python dependencies
        requirements_files = list(self.project_root.glob("*requirements*.txt"))
        requirements_files.extend(list(self.project_root.glob("pyproject.toml")))
        
        for req_file in requirements_files:
            try:
                with open(req_file, 'r') as f:
                    content = f.read()
                    stack["dependencies"][req_file.name] = content[:500]  # Limit content
            except Exception:
                pass
        
        # Detect frameworks and tools
        framework_indicators = {
            "FastAPI": ["fastapi", "uvicorn"],
            "LangChain": ["langchain", "langsmith"],
            "Modal": ["modal"],
            "Pytest": ["pytest"],
            "Graph-sitter": ["graph_sitter", "tree_sitter"]
        }
        
        for framework, indicators in framework_indicators.items():
            evidence = self._find_capability_evidence(indicators)
            if evidence:
                stack["frameworks"][framework] = {
                    "detected": True,
                    "evidence": evidence[:3]
                }
        
        return stack
    
    def create_integration_map(self, components: List[ArchitecturalComponent]) -> Dict[str, List[str]]:
        """Create a map of component integrations."""
        integration_map = defaultdict(list)
        
        for component in components:
            for dependency in component.dependencies:
                # Filter for internal dependencies
                if any(internal in dependency for internal in ["contexten", "graph_sitter"]):
                    integration_map[component.name].append(dependency)
        
        return dict(integration_map)
    
    def run_assessment(self) -> ArchitecturalAssessment:
        """Run complete architectural assessment."""
        logger.info("Starting architectural assessment...")
        
        # Step 1: Assess capabilities
        logger.info("Assessing system capabilities...")
        self.assessment.capabilities = self.assess_contexten_capabilities()
        
        # Step 2: Analyze components
        logger.info("Analyzing architectural components...")
        self.assessment.components = self.analyze_architectural_components()
        
        # Step 3: Collect performance baselines
        logger.info("Collecting performance baselines...")
        self.assessment.performance_baselines = self.collect_performance_baselines()
        
        # Step 4: Perform gap analysis
        logger.info("Performing gap analysis...")
        self.assessment.gap_analysis = self.perform_gap_analysis(self.assessment.capabilities)
        
        # Step 5: Assess technology stack
        logger.info("Assessing technology stack...")
        self.assessment.technology_stack = self.assess_technology_stack()
        
        # Step 6: Create integration map
        logger.info("Creating integration map...")
        self.assessment.integration_map = self.create_integration_map(self.assessment.components)
        
        # Step 7: Generate overall recommendations
        self.assessment.recommendations = self._generate_overall_recommendations()
        
        logger.info("Architectural assessment completed")
        return self.assessment
    
    def _generate_overall_recommendations(self) -> List[str]:
        """Generate overall recommendations for CI/CD transformation."""
        recommendations = [
            "Implement comprehensive automated testing pipeline",
            "Set up continuous deployment with environment promotion",
            "Add real-time monitoring and alerting systems",
            "Enhance code quality gates and automated reviews",
            "Implement infrastructure as code practices",
            "Set up centralized logging and observability",
            "Add automated security scanning and compliance checks",
            "Implement feature flag management system",
            "Set up automated rollback and recovery mechanisms",
            "Add performance testing and optimization workflows"
        ]
        
        # Prioritize based on current capabilities
        missing_capabilities = [c for c in self.assessment.capabilities if c.current_state == "missing"]
        if len(missing_capabilities) > 5:
            recommendations.insert(0, "Focus on implementing missing core capabilities first")
        
        return recommendations

def assess_architecture(project_root: str = ".") -> ArchitecturalAssessment:
    """Convenience function to run architectural assessment."""
    engine = ArchitecturalAssessmentEngine(project_root)
    return engine.run_assessment()

def generate_assessment_report(assessment: ArchitecturalAssessment, output_path: Path) -> str:
    """Generate a comprehensive assessment report."""
    report = f"""
# 🏗️ ARCHITECTURAL ASSESSMENT REPORT

**Generated:** {assessment.timestamp}
**Project:** {assessment.project_root}

## 📊 EXECUTIVE SUMMARY

### Current State Overview
- **Total Components Analyzed:** {len(assessment.components)}
- **Capabilities Assessed:** {len(assessment.capabilities)}
- **Performance Baselines:** {len(assessment.performance_baselines)}
- **Identified Gaps:** {len(assessment.gap_analysis)}

### Capability Maturity
"""
    
    # Capability summary
    present = len([c for c in assessment.capabilities if c.current_state == "present"])
    partial = len([c for c in assessment.capabilities if c.current_state == "partial"])
    missing = len([c for c in assessment.capabilities if c.current_state == "missing"])
    
    report += f"""
- ✅ **Present:** {present} capabilities
- 🔄 **Partial:** {partial} capabilities  
- ❌ **Missing:** {missing} capabilities

## 🎯 CAPABILITIES ANALYSIS

"""
    
    for capability in assessment.capabilities:
        status_emoji = {"present": "✅", "partial": "🔄", "missing": "❌"}[capability.current_state]
        report += f"### {status_emoji} {capability.name}\n"
        report += f"**Status:** {capability.current_state.title()} (Confidence: {capability.confidence:.1%})\n"
        report += f"**Description:** {capability.description}\n"
        if capability.evidence:
            report += f"**Evidence:** {len(capability.evidence)} indicators found\n"
        report += "\n"
    
    # Gap analysis
    report += "## 🔍 GAP ANALYSIS\n\n"
    
    critical_gaps = [g for g in assessment.gap_analysis if g.priority == "critical"]
    high_gaps = [g for g in assessment.gap_analysis if g.priority == "high"]
    
    if critical_gaps:
        report += "### 🚨 Critical Gaps\n"
        for gap in critical_gaps:
            report += f"- **{gap.area}:** {gap.current_state} → {gap.desired_state}\n"
    
    if high_gaps:
        report += "### ⚠️ High Priority Gaps\n"
        for gap in high_gaps:
            report += f"- **{gap.area}:** {gap.current_state} → {gap.desired_state}\n"
    
    # Recommendations
    report += "\n## 🚀 RECOMMENDATIONS\n\n"
    for i, rec in enumerate(assessment.recommendations, 1):
        report += f"{i}. {rec}\n"
    
    # Save report
    with open(output_path, 'w') as f:
        f.write(report)
    
    return report

if __name__ == "__main__":
    # Run assessment
    assessment = assess_architecture()
    
    # Save results
    assessment.save_to_file(Path("architectural_assessment.json"))
    
    # Generate report
    report = generate_assessment_report(assessment, Path("architectural_assessment_report.md"))
    
    print("🏗️ Architectural Assessment Complete!")
    print(f"📊 Results saved to: architectural_assessment.json")
    print(f"📝 Report saved to: architectural_assessment_report.md")

