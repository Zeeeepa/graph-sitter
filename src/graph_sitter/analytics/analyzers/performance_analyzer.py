"""
Performance Analyzer for Graph-Sitter Analytics

Identifies performance bottlenecks and optimization opportunities:
- Algorithm complexity analysis (Big O notation)
- Resource usage patterns
- Performance anti-patterns
- Optimization recommendations
"""

import re
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
from graph_sitter.core.statements.while_statement import WhileStatement
from graph_sitter.shared.logging.logger import get_logger

from ..core.base_analyzer import BaseAnalyzer
from ..core.analysis_result import AnalysisResult, Finding, Severity, FindingType

logger = get_logger(__name__)


class PerformanceAnalyzer(BaseAnalyzer):
    """
    Analyzes code for performance issues and optimization opportunities.
    
    Identifies algorithmic complexity, resource usage patterns, and
    common performance anti-patterns across multiple languages.
    """
    
    def __init__(self):
        super().__init__("performance")
        self.supported_languages = {"python", "typescript", "javascript", "java", "cpp", "rust", "go"}
        
        # Performance anti-patterns
        self.anti_patterns = {
            "nested_loops": {
                "severity": Severity.HIGH,
                "description": "Nested loops can lead to O(n²) or worse complexity"
            },
            "string_concatenation_in_loop": {
                "severity": Severity.MEDIUM,
                "description": "String concatenation in loops is inefficient"
            },
            "inefficient_data_structure": {
                "severity": Severity.MEDIUM,
                "description": "Using inefficient data structures for the operation"
            },
            "unnecessary_computation": {
                "severity": Severity.LOW,
                "description": "Computation that could be cached or avoided"
            },
            "memory_leak_risk": {
                "severity": Severity.HIGH,
                "description": "Code patterns that may lead to memory leaks"
            }
        }
        
        # Language-specific performance patterns
        self.language_patterns = {
            "python": {
                "inefficient_patterns": [
                    r"\.append\(.*\)\s*in\s+.*for.*in",  # List comprehension opportunity
                    r"range\(len\(",  # Direct iteration opportunity
                    r"\+\s*=.*str\(",  # String concatenation in loop
                ],
                "optimization_opportunities": [
                    r"for\s+\w+\s+in\s+range\(len\(",  # enumerate opportunity
                    r"if\s+\w+\s+in\s+\[",  # set membership opportunity
                ]
            },
            "javascript": {
                "inefficient_patterns": [
                    r"\.push\(.*\)\s*in\s+.*for.*of",  # Array method opportunity
                    r"document\.getElementById",  # DOM query optimization
                    r"\.innerHTML\s*\+=",  # DOM manipulation optimization
                ],
                "optimization_opportunities": [
                    r"for\s*\(\s*var\s+\w+\s*=\s*0",  # for...of opportunity
                    r"\.filter\(.*\)\.map\(",  # Chain optimization
                ]
            },
            "java": {
                "inefficient_patterns": [
                    r"new\s+String\(",  # String literal opportunity
                    r"\.toString\(\)\.equals\(",  # Direct comparison opportunity
                    r"Vector|Hashtable",  # Modern collection opportunity
                ],
                "optimization_opportunities": [
                    r"StringBuffer",  # StringBuilder opportunity
                    r"for\s*\(\s*int\s+\w+\s*=\s*0.*\.size\(\)",  # Enhanced for loop
                ]
            }
        }
    
    @BaseAnalyzer.measure_execution_time
    def analyze(self, codebase: Codebase, files: List) -> AnalysisResult:
        """Perform comprehensive performance analysis."""
        if not self.validate_codebase(codebase):
            result = self.create_result("failed")
            result.error_message = "Invalid codebase provided"
            return result
        
        result = self.create_result()
        
        try:
            performance_issues = []
            optimization_opportunities = []
            complexity_analysis = {}
            
            functions_analyzed = 0
            
            for file in files:
                if not self.is_supported_file(str(file.filepath)):
                    continue
                
                file_content = self.get_file_content(file)
                if not file_content:
                    continue
                
                file_language = self._detect_language(str(file.filepath))
                
                # Analyze functions for performance issues
                for func in file.functions:
                    func_analysis = self._analyze_function_performance(func, file_content, file_language)
                    
                    if func_analysis["issues"]:
                        performance_issues.extend(func_analysis["issues"])
                    
                    if func_analysis["optimizations"]:
                        optimization_opportunities.extend(func_analysis["optimizations"])
                    
                    complexity_analysis[f"{func.name}@{func.filepath}"] = func_analysis["complexity"]
                    functions_analyzed += 1
                
                # Analyze file-level patterns
                file_issues = self._analyze_file_patterns(file, file_content, file_language)
                performance_issues.extend(file_issues)
                
                self.log_progress(functions_analyzed, len(list(codebase.functions)), "functions")
            
            # Create findings from issues
            for issue in performance_issues:
                finding = Finding(
                    type=FindingType.PERFORMANCE,
                    severity=issue["severity"],
                    title=issue["title"],
                    description=issue["description"],
                    file_path=issue["file_path"],
                    line_number=issue.get("line_number"),
                    recommendation=issue["recommendation"],
                    rule_id=issue["rule_id"],
                    metadata=issue.get("metadata", {})
                )
                result.add_finding(finding)
            
            # Calculate performance metrics
            result.metrics.files_analyzed = len([f for f in files if self.is_supported_file(str(f.filepath))])
            result.metrics.symbols_analyzed = functions_analyzed
            result.metrics.quality_score = self._calculate_performance_score(performance_issues, functions_analyzed)
            
            # Store detailed performance metrics
            result.metrics.performance_metrics = {
                "functions_analyzed": functions_analyzed,
                "performance_issues_found": len(performance_issues),
                "optimization_opportunities": len(optimization_opportunities),
                "complexity_analysis": complexity_analysis,
                "issue_distribution": self._get_issue_distribution(performance_issues),
                "top_performance_risks": sorted(performance_issues, 
                                               key=lambda x: self._severity_weight(x["severity"]), 
                                               reverse=True)[:10]
            }
            
            # Generate recommendations
            result.recommendations = self._generate_performance_recommendations(performance_issues, optimization_opportunities)
            
            logger.info(f"Performance analysis completed: {len(performance_issues)} issues found in {functions_analyzed} functions")
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {str(e)}")
            result.status = "failed"
            result.error_message = str(e)
        
        return result
    
    def _analyze_function_performance(self, func: Function, file_content: str, language: str) -> Dict[str, Any]:
        """Analyze performance characteristics of a single function."""
        issues = []
        optimizations = []
        
        func_content = self._extract_function_content(func, file_content)
        
        # Analyze algorithmic complexity
        complexity = self._analyze_algorithmic_complexity(func, func_content)
        
        # Check for nested loops
        nested_loops = self._detect_nested_loops(func, func_content)
        if nested_loops > 1:
            issues.append({
                "severity": Severity.HIGH if nested_loops > 2 else Severity.MEDIUM,
                "title": f"Nested Loops Detected: {func.name}",
                "description": f"Function contains {nested_loops} levels of nested loops, potentially leading to O(n^{nested_loops}) complexity.",
                "file_path": str(func.filepath),
                "line_number": getattr(func, 'line_number', None),
                "recommendation": "Consider optimizing algorithm or using more efficient data structures to reduce complexity.",
                "rule_id": "PERF_001",
                "metadata": {"nested_levels": nested_loops, "estimated_complexity": f"O(n^{nested_loops})"}
            })
        
        # Check for string concatenation in loops
        if self._has_string_concatenation_in_loop(func_content, language):
            issues.append({
                "severity": Severity.MEDIUM,
                "title": f"Inefficient String Concatenation: {func.name}",
                "description": "String concatenation inside loops is inefficient and can cause performance issues.",
                "file_path": str(func.filepath),
                "line_number": getattr(func, 'line_number', None),
                "recommendation": "Use string builders, join operations, or list comprehensions for better performance.",
                "rule_id": "PERF_002",
                "metadata": {"language": language}
            })
        
        # Check for inefficient data structure usage
        inefficient_usage = self._detect_inefficient_data_structures(func_content, language)
        for usage in inefficient_usage:
            issues.append({
                "severity": Severity.MEDIUM,
                "title": f"Inefficient Data Structure Usage: {func.name}",
                "description": usage["description"],
                "file_path": str(func.filepath),
                "line_number": getattr(func, 'line_number', None),
                "recommendation": usage["recommendation"],
                "rule_id": "PERF_003",
                "metadata": {"pattern": usage["pattern"]}
            })
        
        # Language-specific performance checks
        lang_issues = self._check_language_specific_patterns(func_content, language, func)
        issues.extend(lang_issues)
        
        # Check for optimization opportunities
        lang_optimizations = self._find_optimization_opportunities(func_content, language, func)
        optimizations.extend(lang_optimizations)
        
        return {
            "issues": issues,
            "optimizations": optimizations,
            "complexity": complexity
        }
    
    def _analyze_algorithmic_complexity(self, func: Function, func_content: str) -> Dict[str, Any]:
        """Analyze the algorithmic complexity of a function."""
        complexity_indicators = {
            "loops": 0,
            "nested_loops": 0,
            "recursive_calls": 0,
            "data_structure_operations": []
        }
        
        # Count loops
        loop_count = len(re.findall(r'\b(for|while)\b', func_content, re.IGNORECASE))
        complexity_indicators["loops"] = loop_count
        
        # Estimate nested loops
        nested_count = self._detect_nested_loops(func, func_content)
        complexity_indicators["nested_loops"] = nested_count
        
        # Check for recursive calls
        if hasattr(func, 'name') and func.name:
            recursive_pattern = rf'\b{re.escape(func.name)}\s*\('
            recursive_calls = len(re.findall(recursive_pattern, func_content))
            complexity_indicators["recursive_calls"] = recursive_calls
        
        # Estimate Big O complexity
        estimated_complexity = self._estimate_big_o_complexity(complexity_indicators)
        
        return {
            "estimated_complexity": estimated_complexity,
            "complexity_indicators": complexity_indicators,
            "performance_risk": self._assess_performance_risk(estimated_complexity)
        }
    
    def _detect_nested_loops(self, func: Function, func_content: str) -> int:
        """Detect the maximum nesting level of loops."""
        if not hasattr(func, 'code_block') or not func.code_block:
            return 0
        
        max_nesting = 0
        
        def analyze_statement(statement, current_depth):
            nonlocal max_nesting
            
            if isinstance(statement, (ForLoopStatement, WhileStatement)):
                current_depth += 1
                max_nesting = max(max_nesting, current_depth)
                
                # Analyze nested statements
                if hasattr(statement, 'nested_code_blocks'):
                    for block in statement.nested_code_blocks:
                        if hasattr(block, 'statements'):
                            for nested_stmt in block.statements:
                                analyze_statement(nested_stmt, current_depth)
            else:
                # Analyze nested statements for non-loop statements
                if hasattr(statement, 'nested_code_blocks'):
                    for block in statement.nested_code_blocks:
                        if hasattr(block, 'statements'):
                            for nested_stmt in block.statements:
                                analyze_statement(nested_stmt, current_depth)
        
        if hasattr(func.code_block, 'statements'):
            for statement in func.code_block.statements:
                analyze_statement(statement, 0)
        
        return max_nesting
    
    def _has_string_concatenation_in_loop(self, func_content: str, language: str) -> bool:
        """Check for string concatenation inside loops."""
        patterns = {
            "python": [r'for\s+.*:\s*.*\+=.*str', r'while\s+.*:\s*.*\+=.*["\']'],
            "javascript": [r'for\s*\(.*\)\s*{.*\+=.*["\']', r'while\s*\(.*\)\s*{.*\+=.*["\']'],
            "java": [r'for\s*\(.*\)\s*{.*\+=.*"', r'while\s*\(.*\)\s*{.*\+=.*"'],
            "cpp": [r'for\s*\(.*\)\s*{.*\+=.*"', r'while\s*\(.*\)\s*{.*\+=.*"']
        }
        
        if language in patterns:
            for pattern in patterns[language]:
                if re.search(pattern, func_content, re.DOTALL | re.IGNORECASE):
                    return True
        
        return False
    
    def _detect_inefficient_data_structures(self, func_content: str, language: str) -> List[Dict[str, str]]:
        """Detect usage of inefficient data structures."""
        inefficiencies = []
        
        patterns = {
            "python": [
                {
                    "pattern": r'\[\s*\]\s*.*for.*in.*if',
                    "description": "List comprehension with filtering could use generator expression",
                    "recommendation": "Consider using generator expressions for memory efficiency"
                },
                {
                    "pattern": r'if\s+\w+\s+in\s+\[.*\]',
                    "description": "Membership testing on list is O(n), consider using set",
                    "recommendation": "Use set for O(1) membership testing instead of list"
                }
            ],
            "javascript": [
                {
                    "pattern": r'\.indexOf\(.*\)\s*!==\s*-1',
                    "description": "Array.indexOf for existence check is inefficient",
                    "recommendation": "Use Set.has() or Array.includes() for better performance"
                },
                {
                    "pattern": r'for\s*\(\s*var\s+\w+\s*=\s*0.*\.length',
                    "description": "Traditional for loop could be optimized",
                    "recommendation": "Consider using for...of or array methods like forEach, map, filter"
                }
            ],
            "java": [
                {
                    "pattern": r'\bVector\b|\bHashtable\b',
                    "description": "Legacy collections are synchronized and slower",
                    "recommendation": "Use ArrayList and HashMap for better performance"
                },
                {
                    "pattern": r'new\s+String\s*\(',
                    "description": "Unnecessary String object creation",
                    "recommendation": "Use string literals instead of new String()"
                }
            ]
        }
        
        if language in patterns:
            for pattern_info in patterns[language]:
                if re.search(pattern_info["pattern"], func_content, re.IGNORECASE):
                    inefficiencies.append(pattern_info)
        
        return inefficiencies
    
    def _check_language_specific_patterns(self, func_content: str, language: str, func: Function) -> List[Dict[str, Any]]:
        """Check for language-specific performance anti-patterns."""
        issues = []
        
        if language == "python":
            # Check for inefficient pandas operations
            if re.search(r'\.iterrows\(\)', func_content):
                issues.append({
                    "severity": Severity.MEDIUM,
                    "title": f"Inefficient Pandas Operation: {func.name}",
                    "description": "iterrows() is slow; consider vectorized operations",
                    "file_path": str(func.filepath),
                    "line_number": getattr(func, 'line_number', None),
                    "recommendation": "Use vectorized operations, .apply(), or .loc[] for better performance",
                    "rule_id": "PERF_PY_001"
                })
            
            # Check for global variable access in loops
            if re.search(r'global\s+\w+.*for\s+.*:', func_content, re.DOTALL):
                issues.append({
                    "severity": Severity.LOW,
                    "title": f"Global Variable Access in Loop: {func.name}",
                    "description": "Accessing global variables in loops can be slower",
                    "file_path": str(func.filepath),
                    "line_number": getattr(func, 'line_number', None),
                    "recommendation": "Cache global variables in local variables before loops",
                    "rule_id": "PERF_PY_002"
                })
        
        elif language == "javascript":
            # Check for DOM queries in loops
            if re.search(r'for\s*\(.*\)\s*{.*document\.(getElementById|querySelector)', func_content, re.DOTALL):
                issues.append({
                    "severity": Severity.HIGH,
                    "title": f"DOM Query in Loop: {func.name}",
                    "description": "DOM queries inside loops are expensive",
                    "file_path": str(func.filepath),
                    "line_number": getattr(func, 'line_number', None),
                    "recommendation": "Cache DOM elements outside loops or use event delegation",
                    "rule_id": "PERF_JS_001"
                })
            
            # Check for inefficient array operations
            if re.search(r'\.push\.apply\(', func_content):
                issues.append({
                    "severity": Severity.LOW,
                    "title": f"Inefficient Array Concatenation: {func.name}",
                    "description": "push.apply can be slow for large arrays",
                    "file_path": str(func.filepath),
                    "line_number": getattr(func, 'line_number', None),
                    "recommendation": "Use spread operator (...) or concat() for better performance",
                    "rule_id": "PERF_JS_002"
                })
        
        return issues
    
    def _find_optimization_opportunities(self, func_content: str, language: str, func: Function) -> List[Dict[str, Any]]:
        """Find optimization opportunities in the code."""
        opportunities = []
        
        if language == "python":
            # List comprehension opportunities
            if re.search(r'for\s+\w+\s+in\s+.*:\s*.*\.append\(', func_content):
                opportunities.append({
                    "type": "list_comprehension",
                    "description": "Loop with append() could be replaced with list comprehension",
                    "recommendation": "Use list comprehension for better performance and readability"
                })
            
            # enumerate() opportunities
            if re.search(r'for\s+\w+\s+in\s+range\(len\(', func_content):
                opportunities.append({
                    "type": "enumerate",
                    "description": "range(len()) pattern could use enumerate()",
                    "recommendation": "Use enumerate() for cleaner and potentially faster iteration"
                })
        
        elif language == "javascript":
            # Array method chaining opportunities
            if re.search(r'\.filter\(.*\)\.map\(', func_content):
                opportunities.append({
                    "type": "array_method_optimization",
                    "description": "Filter followed by map could be optimized",
                    "recommendation": "Consider combining operations or using reduce() for better performance"
                })
        
        return opportunities
    
    def _analyze_file_patterns(self, file, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Analyze file-level performance patterns."""
        issues = []
        
        # Check for excessive imports (can slow startup)
        import_count = len(re.findall(r'^(import|from|#include)', file_content, re.MULTILINE))
        if import_count > 50:
            issues.append({
                "severity": Severity.LOW,
                "title": f"Excessive Imports: {file.name}",
                "description": f"File has {import_count} imports, which may slow module loading",
                "file_path": str(file.filepath),
                "recommendation": "Consider lazy imports or splitting the module",
                "rule_id": "PERF_FILE_001",
                "metadata": {"import_count": import_count}
            })
        
        # Check for large file size (can indicate performance issues)
        line_count = len(file_content.splitlines())
        if line_count > 1000:
            issues.append({
                "severity": Severity.MEDIUM if line_count > 2000 else Severity.LOW,
                "title": f"Large File: {file.name}",
                "description": f"File has {line_count} lines, which may indicate complexity issues",
                "file_path": str(file.filepath),
                "recommendation": "Consider breaking down into smaller, more focused modules",
                "rule_id": "PERF_FILE_002",
                "metadata": {"line_count": line_count}
            })
        
        return issues
    
    def _estimate_big_o_complexity(self, indicators: Dict[str, Any]) -> str:
        """Estimate Big O complexity based on code indicators."""
        nested_loops = indicators["nested_loops"]
        recursive_calls = indicators["recursive_calls"]
        
        if recursive_calls > 0:
            return "O(2^n) or worse"  # Worst case for recursion
        elif nested_loops >= 3:
            return f"O(n^{nested_loops})"
        elif nested_loops == 2:
            return "O(n²)"
        elif nested_loops == 1 or indicators["loops"] > 0:
            return "O(n)"
        else:
            return "O(1)"
    
    def _assess_performance_risk(self, complexity: str) -> str:
        """Assess performance risk based on complexity."""
        if "2^n" in complexity or "n^" in complexity and int(complexity.split("^")[1].rstrip(")")) >= 3:
            return "HIGH"
        elif "n²" in complexity:
            return "MEDIUM"
        elif "O(n)" in complexity:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        from pathlib import Path
        
        ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".rs": "rust",
            ".go": "go"
        }
        
        return lang_map.get(ext, "unknown")
    
    def _extract_function_content(self, func: Function, file_content: str) -> str:
        """Extract function content from file."""
        # Simplified extraction - could be enhanced with AST parsing
        lines = file_content.splitlines()
        
        if hasattr(func, 'line_number') and func.line_number:
            start_line = func.line_number - 1
            
            # Find function end (simplified heuristic)
            end_line = start_line + 1
            indent_level = None
            
            for i in range(start_line + 1, len(lines)):
                line = lines[i]
                if line.strip():
                    if indent_level is None:
                        indent_level = len(line) - len(line.lstrip())
                    elif len(line) - len(line.lstrip()) <= indent_level and line.strip():
                        break
                end_line = i
            
            return "\n".join(lines[start_line:end_line + 1])
        
        return ""
    
    def _severity_weight(self, severity: Severity) -> int:
        """Get numeric weight for severity."""
        weights = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1
        }
        return weights.get(severity, 0)
    
    def _get_issue_distribution(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of issues by severity."""
        distribution = defaultdict(int)
        for issue in issues:
            distribution[issue["severity"].value] += 1
        return dict(distribution)
    
    def _calculate_performance_score(self, issues: List[Dict[str, Any]], functions_analyzed: int) -> float:
        """Calculate overall performance score."""
        if functions_analyzed == 0:
            return 100.0
        
        # Calculate penalty based on issues
        penalty = 0
        for issue in issues:
            penalty += self._severity_weight(issue["severity"]) * 5
        
        # Normalize penalty
        max_penalty = functions_analyzed * 20  # Max 20 points penalty per function
        normalized_penalty = min(penalty, max_penalty)
        
        score = 100 - (normalized_penalty / max_penalty * 100) if max_penalty > 0 else 100
        return max(0, score)
    
    def _generate_performance_recommendations(self, issues: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable performance recommendations."""
        recommendations = []
        
        # Count issue types
        issue_types = defaultdict(int)
        for issue in issues:
            rule_id = issue.get("rule_id", "UNKNOWN")
            issue_types[rule_id] += 1
        
        # Generate recommendations based on most common issues
        if issue_types.get("PERF_001", 0) > 0:
            recommendations.append(f"Optimize {issue_types['PERF_001']} functions with nested loops to reduce algorithmic complexity")
        
        if issue_types.get("PERF_002", 0) > 0:
            recommendations.append(f"Replace string concatenation in loops in {issue_types['PERF_002']} functions")
        
        if issue_types.get("PERF_003", 0) > 0:
            recommendations.append(f"Optimize data structure usage in {issue_types['PERF_003']} functions")
        
        # Add general recommendations
        high_severity_count = sum(1 for issue in issues if issue["severity"] == Severity.HIGH)
        if high_severity_count > 0:
            recommendations.append(f"Address {high_severity_count} high-severity performance issues immediately")
        
        if len(opportunities) > 0:
            recommendations.append(f"Implement {len(opportunities)} identified optimization opportunities")
        
        return recommendations[:5]  # Return top 5 recommendations

