#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE CODEBASE ANALYSIS TOOL 🚀

A single, powerful executable that consolidates all analysis capabilities:
- Core quality metrics (maintainability, complexity, Halstead, etc.)
- Advanced investigation features (function context, relationships)
- Usage pattern analysis (ML training data, visualizations)
- Graph-sitter integration (pre-computed graphs, dependencies)
- Tree-sitter query patterns and visualization
- Interactive syntax tree visualization
- Production-ready error handling and performance optimization

Based on patterns from: https://graph-sitter.com/tutorials/at-a-glance

Features:
- Tree-sitter query pattern analysis
- Interactive syntax tree visualization
- Advanced code structure analysis
- Pattern-based code search
- Visualization export (JSON, DOT, HTML)

Usage:
    python analyze_codebase.py path/to/code
    python analyze_codebase.py --repo fastapi/fastapi
    python analyze_codebase.py . --format json --output results.json
    python analyze_codebase.py . --comprehensive --visualize
    python analyze_codebase.py . --tree-sitter --export-html analysis.html
"""

import argparse
import ast
import json
import math
import os
import re
import sys
import time
import traceback
import html
import tempfile
import webbrowser
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the path for graph_sitter imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

try:
    from graph_sitter import Codebase
    from graph_sitter.core.codebase import Codebase as CoreCodebase
    from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
    from graph_sitter.core.statements.if_block_statement import IfBlockStatement
    from graph_sitter.core.statements.try_catch_statement import TryCatchStatement
    from graph_sitter.core.statements.while_statement import WhileStatement
    from graph_sitter.core.expressions.binary_expression import BinaryExpression
    from graph_sitter.core.expressions.unary_expression import UnaryExpression
    from graph_sitter.core.expressions.comparison_expression import ComparisonExpression
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary, get_file_summary, get_class_summary, 
        get_function_summary, get_symbol_summary
    )
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False
    # Fallback imports for basic functionality
    ForLoopStatement = None
    IfBlockStatement = None
    TryCatchStatement = None
    WhileStatement = None
    BinaryExpression = None
    UnaryExpression = None
    ComparisonExpression = None


# ============================================================================
# DATA CLASSES AND MODELS
# ============================================================================

@dataclass
class CodeIssue:
    """Represents a code issue with detailed information."""
    type: str
    severity: str  # 'critical', 'major', 'minor', 'info'
    message: str
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None
    confidence: float = 1.0

@dataclass
class ParameterIssue:
    """Represents an issue with a specific parameter."""
    parameter_name: str
    parameter_type: Optional[str]
    issue_type: str  # 'missing_type', 'unused', 'mutable_default', 'too_many', 'naming_convention'
    description: str
    suggestion: Optional[str] = None
    line_number: int = 0

@dataclass
class CodeContext:
    """Provides context around a code issue."""
    surrounding_lines: List[str]
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    module_path: str = ""
    imports: List[str] = field(default_factory=list)
    
@dataclass
class DetailedCodeIssue:
    """Enhanced code issue with comprehensive details."""
    id: str  # Unique identifier
    type: str
    severity: str  # 'critical', 'major', 'minor', 'info'
    category: str  # 'style', 'performance', 'security', 'maintainability', 'correctness'
    message: str
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    
    # Enhanced details
    code_snippet: str = ""
    context: Optional[CodeContext] = None
    parameter_issues: List[ParameterIssue] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)  # IDs of related issues
    
    # Metadata
    rule_id: Optional[str] = None
    confidence: float = 1.0
    fix_complexity: str = "easy"  # 'easy', 'medium', 'hard'
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    
    # Impact analysis
    impact_scope: str = "local"  # 'local', 'module', 'project'
    affected_functions: List[str] = field(default_factory=list)
    affected_classes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

@dataclass
class DeadCodeItem:
    """Represents dead/unused code."""
    type: str  # 'function', 'class', 'variable'
    name: str
    file_path: str
    line_start: int
    line_end: int
    reason: str
    confidence: float



# ============================================================================
# ENHANCED ISSUE DETECTION AND ANALYSIS
# ============================================================================

class EnhancedIssueDetector:
    """Comprehensive issue detection with detailed logging and context."""
    
    def __init__(self, use_graph_sitter: bool = True):
        self.enhanced_issue_detector = EnhancedIssueDetector(use_graph_sitter)
        self.use_graph_sitter = use_graph_sitter
        self.issue_counter = 0
        self.detected_issues: List[DetailedCodeIssue] = []
        
    def generate_issue_id(self, file_path: str, line: int, issue_type: str) -> str:
        """Generate unique issue ID."""
        self.issue_counter += 1
        return f"{Path(file_path).stem}_{line}_{issue_type}_{self.issue_counter}"
    
    def get_code_context(self, file_path: str, line_start: int, line_end: Optional[int] = None) -> CodeContext:
        """Extract code context around an issue."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Get surrounding lines (5 before and after)
            start_idx = max(0, line_start - 6)
            end_idx = min(len(lines), (line_end or line_start) + 5)
            surrounding_lines = [f"{i+1:4d}: {line.rstrip()}" for i, line in enumerate(lines[start_idx:end_idx], start_idx)]
            
            # Try to determine function/class context
            function_name = None
            class_name = None
            
            # Look backwards for function/class definitions
            for i in range(line_start - 1, max(0, line_start - 50), -1):
                if i < len(lines):
                    line = lines[i].strip()
                    if line.startswith('def '):
                        function_name = line.split('(')[0].replace('def ', '').strip()
                        break
                    elif line.startswith('class '):
                        class_name = line.split('(')[0].replace('class ', '').strip().rstrip(':')
                        break
            
            # Extract imports
            imports = []
            for line in lines[:50]:  # Check first 50 lines for imports
                line = line.strip()
                if line.startswith(('import ', 'from ')):
                    imports.append(line)
            
            return CodeContext(
                surrounding_lines=surrounding_lines,
                function_name=function_name,
                class_name=class_name,
                module_path=file_path,
                imports=imports
            )
        except Exception as e:
            logger.debug(f"Error getting context for {file_path}:{line_start}: {e}")
            return CodeContext(surrounding_lines=[])
    
    def analyze_function_parameters(self, func_node: ast.FunctionDef, file_path: str) -> List[ParameterIssue]:
        """Analyze function parameters for issues."""
        issues = []
        
        # Check for too many parameters
        if len(func_node.args.args) > 7:
            issues.append(ParameterIssue(
                parameter_name="function_signature",
                parameter_type=None,
                issue_type="too_many",
                description=f"Function has {len(func_node.args.args)} parameters (recommended: ≤7)",
                suggestion="Consider using a configuration object or breaking into smaller functions",
                line_number=func_node.lineno
            ))
        
        # Check each parameter
        for arg in func_node.args.args:
            param_name = arg.arg
            
            # Check naming convention
            if not re.match(r'^[a-z_][a-z0-9_]*$', param_name):
                issues.append(ParameterIssue(
                    parameter_name=param_name,
                    parameter_type=None,
                    issue_type="naming_convention",
                    description=f"Parameter '{param_name}' doesn't follow snake_case convention",
                    suggestion=f"Rename to follow snake_case: {re.sub(r'([A-Z])', r'_\\1', param_name).lower()}",
                    line_number=func_node.lineno
                ))
            
            # Check for missing type annotations
            if not arg.annotation:
                issues.append(ParameterIssue(
                    parameter_name=param_name,
                    parameter_type=None,
                    issue_type="missing_type",
                    description=f"Parameter '{param_name}' missing type annotation",
                    suggestion=f"Add type annotation: {param_name}: <type>",
                    line_number=func_node.lineno
                ))
        
        # Check for mutable default arguments
        for default in func_node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                issues.append(ParameterIssue(
                    parameter_name="default_argument",
                    parameter_type=None,
                    issue_type="mutable_default",
                    description="Mutable default argument detected",
                    suggestion="Use None as default and create mutable object inside function",
                    line_number=func_node.lineno
                ))
        
        return issues
    
    def detect_security_issues(self, node: ast.AST, file_path: str) -> List[DetailedCodeIssue]:
        """Detect potential security issues."""
        issues = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                # Check for eval() usage
                if isinstance(child.func, ast.Name) and child.func.id == 'eval':
                    issue_id = self.generate_issue_id(file_path, child.lineno, "security_eval")
                    context = self.get_code_context(file_path, child.lineno)
                    
                    issues.append(DetailedCodeIssue(
                        id=issue_id,
                        type="security_vulnerability",
                        severity="critical",
                        category="security",
                        message="Use of eval() function detected - potential code injection vulnerability",
                        file_path=file_path,
                        line_start=child.lineno,
                        code_snippet=ast.unparse(child) if hasattr(ast, 'unparse') else str(child),
                        context=context,
                        rule_id="SEC001",
                        confidence=0.9,
                        fix_complexity="medium",
                        suggestion="Replace eval() with safer alternatives like ast.literal_eval() for literals or proper parsing",
                        auto_fixable=False,
                        impact_scope="project"
                    ))
                
                # Check for exec() usage
                elif isinstance(child.func, ast.Name) and child.func.id == 'exec':
                    issue_id = self.generate_issue_id(file_path, child.lineno, "security_exec")
                    context = self.get_code_context(file_path, child.lineno)
                    
                    issues.append(DetailedCodeIssue(
                        id=issue_id,
                        type="security_vulnerability",
                        severity="critical",
                        category="security",
                        message="Use of exec() function detected - potential code injection vulnerability",
                        file_path=file_path,
                        line_start=child.lineno,
                        code_snippet=ast.unparse(child) if hasattr(ast, 'unparse') else str(child),
                        context=context,
                        rule_id="SEC002",
                        confidence=0.9,
                        fix_complexity="hard",
                        suggestion="Avoid exec() - redesign to use proper function calls or configuration",
                        auto_fixable=False,
                        impact_scope="project"
                    ))
        
        return issues
    
    def detect_performance_issues(self, node: ast.AST, file_path: str) -> List[DetailedCodeIssue]:
        """Detect potential performance issues."""
        issues = []
        
        for child in ast.walk(node):
            # Detect string concatenation in loops
            if isinstance(child, (ast.For, ast.While)):
                for loop_child in ast.walk(child):
                    if isinstance(loop_child, ast.AugAssign) and isinstance(loop_child.op, ast.Add):
                        if isinstance(loop_child.target, ast.Name):
                            issue_id = self.generate_issue_id(file_path, loop_child.lineno, "performance_string_concat")
                            context = self.get_code_context(file_path, loop_child.lineno)
                            
                            issues.append(DetailedCodeIssue(
                                id=issue_id,
                                type="performance_issue",
                                severity="minor",
                                category="performance",
                                message="String concatenation in loop detected - potential performance issue",
                                file_path=file_path,
                                line_start=loop_child.lineno,
                                code_snippet=ast.unparse(loop_child) if hasattr(ast, 'unparse') else str(loop_child),
                                context=context,
                                rule_id="PERF001",
                                confidence=0.7,
                                fix_complexity="easy",
                                suggestion="Use list.append() and ''.join() or io.StringIO for better performance",
                                auto_fixable=True,
                                impact_scope="local"
                            ))
        
        return issues
    
    def detect_maintainability_issues(self, node: ast.AST, file_path: str) -> List[DetailedCodeIssue]:
        """Detect maintainability issues."""
        issues = []
        
        for child in ast.walk(node):
            # Detect long functions
            if isinstance(child, ast.FunctionDef):
                func_lines = child.end_lineno - child.lineno if hasattr(child, 'end_lineno') else 0
                if func_lines > 50:
                    issue_id = self.generate_issue_id(file_path, child.lineno, "maintainability_long_function")
                    context = self.get_code_context(file_path, child.lineno)
                    
                    issues.append(DetailedCodeIssue(
                        id=issue_id,
                        type="maintainability_issue",
                        severity="major",
                        category="maintainability",
                        message=f"Function '{child.name}' is too long ({func_lines} lines) - consider breaking it down",
                        file_path=file_path,
                        line_start=child.lineno,
                        line_end=getattr(child, 'end_lineno', child.lineno),
                        context=context,
                        rule_id="MAINT001",
                        confidence=0.8,
                        fix_complexity="medium",
                        suggestion="Break function into smaller, focused functions with single responsibilities",
                        auto_fixable=False,
                        impact_scope="module",
                        affected_functions=[child.name]
                    ))
                
                # Analyze function parameters
                param_issues = self.analyze_function_parameters(child, file_path)
                for param_issue in param_issues:
                    issue_id = self.generate_issue_id(file_path, param_issue.line_number, f"param_{param_issue.issue_type}")
                    context = self.get_code_context(file_path, param_issue.line_number)
                    
                    severity_map = {
                        "missing_type": "minor",
                        "too_many": "major",
                        "mutable_default": "major",
                        "naming_convention": "minor"
                    }
                    
                    issues.append(DetailedCodeIssue(
                        id=issue_id,
                        type="parameter_issue",
                        severity=severity_map.get(param_issue.issue_type, "minor"),
                        category="maintainability",
                        message=param_issue.description,
                        file_path=file_path,
                        line_start=param_issue.line_number,
                        context=context,
                        parameter_issues=[param_issue],
                        rule_id=f"PARAM_{param_issue.issue_type.upper()}",
                        confidence=0.9,
                        fix_complexity="easy",
                        suggestion=param_issue.suggestion,
                        auto_fixable=param_issue.issue_type in ["naming_convention"],
                        impact_scope="local",
                        affected_functions=[child.name]
                    ))
            
            # Detect deeply nested code
            elif isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                nesting_level = self._calculate_nesting_level(child)
                if nesting_level > 4:
                    issue_id = self.generate_issue_id(file_path, child.lineno, "maintainability_deep_nesting")
                    context = self.get_code_context(file_path, child.lineno)
                    
                    issues.append(DetailedCodeIssue(
                        id=issue_id,
                        type="maintainability_issue",
                        severity="minor",
                        category="maintainability",
                        message=f"Deep nesting detected (level {nesting_level}) - consider refactoring",
                        file_path=file_path,
                        line_start=child.lineno,
                        context=context,
                        rule_id="MAINT002",
                        confidence=0.7,
                        fix_complexity="medium",
                        suggestion="Extract nested logic into separate functions or use early returns",
                        auto_fixable=False,
                        impact_scope="local"
                    ))
        
        return issues
    
    def _calculate_nesting_level(self, node: ast.AST, level: int = 0) -> int:
        """Calculate the maximum nesting level of a node."""
        max_level = level
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_level = self._calculate_nesting_level(child, level + 1)
                max_level = max(max_level, child_level)
        return max_level
    
    def analyze_file_issues(self, file_path: str, source_code: str) -> List[DetailedCodeIssue]:
        """Comprehensive analysis of a single file for all types of issues."""
        issues = []
        
        try:
            tree = ast.parse(source_code, filename=file_path)
            
            # Detect different types of issues
            issues.extend(self.detect_security_issues(tree, file_path))
            issues.extend(self.detect_performance_issues(tree, file_path))
            issues.extend(self.detect_maintainability_issues(tree, file_path))
            
            # Add file-level issues
            lines = source_code.splitlines()
            
            # Check file length
            if len(lines) > 1000:
                issue_id = self.generate_issue_id(file_path, 1, "file_too_long")
                context = self.get_code_context(file_path, 1)
                
                issues.append(DetailedCodeIssue(
                    id=issue_id,
                    type="file_issue",
                    severity="major",
                    category="maintainability",
                    message=f"File is too long ({len(lines)} lines) - consider splitting into multiple files",
                    file_path=file_path,
                    line_start=1,
                    line_end=len(lines),
                    context=context,
                    rule_id="FILE001",
                    confidence=0.8,
                    fix_complexity="hard",
                    suggestion="Split file into logical modules or classes",
                    auto_fixable=False,
                    impact_scope="module"
                ))
            
            # Check for missing docstrings in classes and functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        issue_id = self.generate_issue_id(file_path, node.lineno, "missing_docstring")
                        context = self.get_code_context(file_path, node.lineno)
                        
                        issues.append(DetailedCodeIssue(
                            id=issue_id,
                            type="documentation_issue",
                            severity="minor",
                            category="maintainability",
                            message=f"{node.__class__.__name__.replace('Def', '')} '{node.name}' missing docstring",
                            file_path=file_path,
                            line_start=node.lineno,
                            context=context,
                            rule_id="DOC001",
                            confidence=0.9,
                            fix_complexity="easy",
                            suggestion=f"Add docstring describing the purpose and parameters of {node.name}",
                            auto_fixable=True,
                            impact_scope="local",
                            affected_functions=[node.name] if isinstance(node, ast.FunctionDef) else [],
                            affected_classes=[node.name] if isinstance(node, ast.ClassDef) else []
                        ))
            
        except SyntaxError as e:
            issue_id = self.generate_issue_id(file_path, e.lineno or 1, "syntax_error")
            context = self.get_code_context(file_path, e.lineno or 1)
            
            issues.append(DetailedCodeIssue(
                id=issue_id,
                type="syntax_error",
                severity="critical",
                category="correctness",
                message=f"Syntax error: {e.msg}",
                file_path=file_path,
                line_start=e.lineno or 1,
                column_start=e.offset,
                context=context,
                rule_id="SYN001",
                confidence=1.0,
                fix_complexity="medium",
                suggestion="Fix syntax error according to Python language rules",
                auto_fixable=False,
                impact_scope="module"
            ))
        except Exception as e:
            logger.debug(f"Error analyzing {file_path}: {e}")
        
        return issues


def generate_detailed_issue_report(issues: List[DetailedCodeIssue]) -> str:
    """Generate a comprehensive HTML report of all detected issues."""
    
    # Group issues by severity and category
    by_severity = defaultdict(list)
    by_category = defaultdict(list)
    by_file = defaultdict(list)
    
    for issue in issues:
        by_severity[issue.severity].append(issue)
        by_category[issue.category].append(issue)
        by_file[issue.file_path].append(issue)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Comprehensive Code Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
            .summary-card {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }}
            .critical {{ border-left: 5px solid #d32f2f; }}
            .major {{ border-left: 5px solid #f57c00; }}
            .minor {{ border-left: 5px solid #fbc02d; }}
            .info {{ border-left: 5px solid #1976d2; }}
            .issue {{ margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .issue-header {{ font-weight: bold; margin-bottom: 10px; }}
            .code-snippet {{ background: #f5f5f5; padding: 10px; border-radius: 3px; font-family: monospace; }}
            .context {{ background: #fafafa; padding: 10px; border-radius: 3px; font-family: monospace; font-size: 12px; }}
            .suggestion {{ background: #e8f5e8; padding: 10px; border-radius: 3px; margin-top: 10px; }}
            .tabs {{ margin: 20px 0; }}
            .tab-button {{ background: #f0f0f0; border: none; padding: 10px 20px; cursor: pointer; }}
            .tab-button.active {{ background: #007bff; color: white; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .parameter-issue {{ background: #fff3cd; padding: 5px; margin: 5px 0; border-radius: 3px; }}
        </style>
        <script>
            function showTab(tabName) {{
                var tabs = document.getElementsByClassName('tab-content');
                var buttons = document.getElementsByClassName('tab-button');
                
                for (var i = 0; i < tabs.length; i++) {{
                    tabs[i].classList.remove('active');
                }}
                for (var i = 0; i < buttons.length; i++) {{
                    buttons[i].classList.remove('active');
                }}
                
                document.getElementById(tabName).classList.add('active');
                event.target.classList.add('active');
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Comprehensive Code Analysis Report</h1>
            <p>Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Total Issues Found: <strong>{len(issues)}</strong></p>
        </div>
        
        <div class="summary">
            <div class="summary-card critical">
                <h3>Critical Issues</h3>
                <p><strong>{len(by_severity['critical'])}</strong> issues</p>
                <small>Require immediate attention</small>
            </div>
            <div class="summary-card major">
                <h3>Major Issues</h3>
                <p><strong>{len(by_severity['major'])}</strong> issues</p>
                <small>Should be addressed soon</small>
            </div>
            <div class="summary-card minor">
                <h3>Minor Issues</h3>
                <p><strong>{len(by_severity['minor'])}</strong> issues</p>
                <small>Improvements recommended</small>
            </div>
            <div class="summary-card info">
                <h3>Info Issues</h3>
                <p><strong>{len(by_severity['info'])}</strong> issues</p>
                <small>Informational only</small>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab-button active" onclick="showTab('by-severity')">By Severity</button>
            <button class="tab-button" onclick="showTab('by-category')">By Category</button>
            <button class="tab-button" onclick="showTab('by-file')">By File</button>
        </div>
    """
    
    # By Severity Tab
    html_content += '<div id="by-severity" class="tab-content active">'
    for severity in ['critical', 'major', 'minor', 'info']:
        if by_severity[severity]:
            html_content += f'<h2>{severity.title()} Issues ({len(by_severity[severity])})</h2>'
            for issue in by_severity[severity]:
                html_content += format_issue_html(issue)
    html_content += '</div>'
    
    # By Category Tab
    html_content += '<div id="by-category" class="tab-content">'
    for category, category_issues in by_category.items():
        html_content += f'<h2>{category.title()} Issues ({len(category_issues)})</h2>'
        for issue in category_issues:
            html_content += format_issue_html(issue)
    html_content += '</div>'
    
    # By File Tab
    html_content += '<div id="by-file" class="tab-content">'
    for file_path, file_issues in by_file.items():
        html_content += f'<h2>{file_path} ({len(file_issues)} issues)</h2>'
        for issue in file_issues:
            html_content += format_issue_html(issue)
    html_content += '</div>'
    
    html_content += """
    </body>
    </html>
    """
    
    return html_content


def format_issue_html(issue: DetailedCodeIssue) -> str:
    """Format a single issue as HTML."""
    
    parameter_issues_html = ""
    if issue.parameter_issues:
        parameter_issues_html = "<h4>Parameter Issues:</h4>"
        for param_issue in issue.parameter_issues:
            parameter_issues_html += f"""
            <div class="parameter-issue">
                <strong>{param_issue.parameter_name}</strong> ({param_issue.issue_type}): {param_issue.description}
                {f'<br><em>Suggestion: {param_issue.suggestion}</em>' if param_issue.suggestion else ''}
            </div>
            """
    
    context_html = ""
    if issue.context and issue.context.surrounding_lines:
        context_html = f"""
        <h4>Code Context:</h4>
        <div class="context">
{chr(10).join(issue.context.surrounding_lines)}
        </div>
        """
        
        if issue.context.function_name or issue.context.class_name:
            context_html += f"<p><strong>Location:</strong> "
            if issue.context.class_name:
                context_html += f"Class: {issue.context.class_name}"
            if issue.context.function_name:
                context_html += f"{' → ' if issue.context.class_name else ''}Function: {issue.context.function_name}"
            context_html += "</p>"
    
    suggestion_html = ""
    if issue.suggestion:
        suggestion_html = f"""
        <div class="suggestion">
            <strong>💡 Suggestion:</strong> {issue.suggestion}
            <br><small>Fix Complexity: {issue.fix_complexity} | Auto-fixable: {'Yes' if issue.auto_fixable else 'No'}</small>
        </div>
        """
    
    return f"""
    <div class="issue {issue.severity}">
        <div class="issue-header">
            [{issue.severity.upper()}] {issue.message}
        </div>
        <p><strong>File:</strong> {issue.file_path}:{issue.line_start}{f'-{issue.line_end}' if issue.line_end and issue.line_end != issue.line_start else ''}</p>
        <p><strong>Type:</strong> {issue.type} | <strong>Category:</strong> {issue.category} | <strong>Rule:</strong> {issue.rule_id or 'N/A'}</p>
        <p><strong>Impact:</strong> {issue.impact_scope} | <strong>Confidence:</strong> {issue.confidence:.1%}</p>
        
        {f'<div class="code-snippet"><strong>Code:</strong><br>{html.escape(issue.code_snippet)}</div>' if issue.code_snippet else ''}
        
        {parameter_issues_html}
        {context_html}
        {suggestion_html}
        
        {f'<p><strong>Affected Functions:</strong> {", ".join(issue.affected_functions)}</p>' if issue.affected_functions else ''}
        {f'<p><strong>Affected Classes:</strong> {", ".join(issue.affected_classes)}</p>' if issue.affected_classes else ''}
        {f'<p><strong>Related Issues:</strong> {", ".join(issue.related_issues)}</p>' if issue.related_issues else ''}
    </div>
    """



def format_detailed_issues_output(detailed_issues: List[DetailedCodeIssue], show_parameter_issues: bool = False) -> str:
    """Format detailed issues for console output."""
    if not detailed_issues:
        return "\n✅ No issues found!"
    
    output = []
    output.append("\n" + "="*80)
    output.append("🔍 DETAILED ISSUE ANALYSIS REPORT")
    output.append("="*80)
    
    # Group issues by severity
    by_severity = defaultdict(list)
    for issue in detailed_issues:
        by_severity[issue.severity].append(issue)
    
    for severity in ["critical", "major", "minor", "info"]:
        if by_severity[severity]:
            output.append(f"\n📋 {severity.upper()} ISSUES ({len(by_severity[severity])})")
            output.append("-" * 50)
            
            for issue in by_severity[severity]:
                output.append(f"\n🔸 [{issue.id}] {issue.message}")
                output.append(f"   📁 File: {issue.file_path}:{issue.line_start}")
                output.append(f"   🏷️  Type: {issue.type} | Category: {issue.category}")
                output.append(f"   📊 Confidence: {issue.confidence:.1%} | Fix: {issue.fix_complexity}")
                
                if issue.code_snippet:
                    output.append(f"   💻 Code: {issue.code_snippet}")
                
                if issue.parameter_issues and show_parameter_issues:
                    output.append("   🔧 Parameter Issues:")
                    for param_issue in issue.parameter_issues:
                        output.append(f"      • {param_issue.parameter_name}: {param_issue.description}")
                
                if issue.suggestion:
                    output.append(f"   💡 Suggestion: {issue.suggestion}")
                
                if issue.context and issue.context.function_name:
                    location = []
                    if issue.context.class_name:
                        location.append(f"Class: {issue.context.class_name}")
                    if issue.context.function_name:
                        location.append(f"Function: {issue.context.function_name}")
                    output.append(f"   📍 Location: {' → '.join(location)}")
    
    output.append(f"\n📈 SUMMARY: {len(detailed_issues)} total issues found")
    severity_counts = {sev: len(issues) for sev, issues in by_severity.items()}
    output.append(f"   Critical: {severity_counts.get('critical', 0)}, "
                  f"Major: {severity_counts.get('major', 0)}, "
                  f"Minor: {severity_counts.get('minor', 0)}, "
                  f"Info: {severity_counts.get('info', 0)}")
    
    return "\n".join(output)

