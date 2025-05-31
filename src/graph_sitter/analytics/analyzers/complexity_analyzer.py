"""
Complexity Analyzer for Graph-Sitter Analytics

Analyzes code complexity using multiple metrics:
- Cyclomatic complexity
- Cognitive complexity  
- Halstead complexity
- Maintainability index
- Nesting depth
"""

import math
import re
from typing import List, Dict, Any, Set
from collections import defaultdict

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
from graph_sitter.core.statements.if_block_statement import IfBlockStatement
from graph_sitter.core.statements.try_catch_statement import TryCatchStatement
from graph_sitter.core.statements.while_statement import WhileStatement
from graph_sitter.shared.logging.logger import get_logger

from ..core.base_analyzer import BaseAnalyzer
from ..core.analysis_result import AnalysisResult, Finding, Severity, FindingType

logger = get_logger(__name__)


class ComplexityAnalyzer(BaseAnalyzer):
    """
    Analyzes code complexity using multiple established metrics.
    
    Provides comprehensive complexity analysis including cyclomatic complexity,
    cognitive complexity, Halstead metrics, and maintainability scoring.
    """
    
    def __init__(self):
        super().__init__("complexity")
        self.supported_languages = {"python", "typescript", "javascript", "java", "cpp", "rust", "go"}
        
        # Complexity thresholds
        self.cyclomatic_thresholds = {
            "low": 10,
            "medium": 15,
            "high": 20,
            "critical": 30
        }
        
        self.cognitive_thresholds = {
            "low": 15,
            "medium": 25,
            "high": 35,
            "critical": 50
        }
        
        self.maintainability_thresholds = {
            "critical": 20,
            "high": 40,
            "medium": 60,
            "low": 80
        }
    
    @BaseAnalyzer.measure_execution_time
    def analyze(self, codebase: Codebase, files: List) -> AnalysisResult:
        """Perform comprehensive complexity analysis."""
        if not self.validate_codebase(codebase):
            result = self.create_result("failed")
            result.error_message = "Invalid codebase provided"
            return result
        
        result = self.create_result()
        
        try:
            # Analyze functions and classes
            functions_analyzed = 0
            classes_analyzed = 0
            total_complexity = 0
            complexity_distribution = defaultdict(int)
            
            # Collect all complexity metrics
            function_metrics = []
            class_metrics = []
            
            for file in files:
                if not self.is_supported_file(str(file.filepath)):
                    continue
                
                file_content = self.get_file_content(file)
                if not file_content:
                    continue
                
                # Analyze functions in this file
                for func in file.functions:
                    metrics = self._analyze_function_complexity(func, file_content)
                    function_metrics.append(metrics)
                    
                    total_complexity += metrics['cyclomatic_complexity']
                    functions_analyzed += 1
                    
                    # Check thresholds and create findings
                    self._check_function_thresholds(func, metrics, result)
                    
                    # Update distribution
                    complexity_level = self._get_complexity_level(metrics['cyclomatic_complexity'])
                    complexity_distribution[complexity_level] += 1
                
                # Analyze classes in this file
                for cls in file.classes:
                    metrics = self._analyze_class_complexity(cls, file_content)
                    class_metrics.append(metrics)
                    classes_analyzed += 1
                    
                    # Check class-level thresholds
                    self._check_class_thresholds(cls, metrics, result)
                
                self.log_progress(functions_analyzed + classes_analyzed, 
                                len(list(codebase.functions)) + len(list(codebase.classes)), 
                                "symbols")
            
            # Calculate aggregate metrics
            avg_complexity = total_complexity / functions_analyzed if functions_analyzed > 0 else 0
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(function_metrics, class_metrics)
            
            # Update result metrics
            result.metrics.files_analyzed = len([f for f in files if self.is_supported_file(str(f.filepath))])
            result.metrics.symbols_analyzed = functions_analyzed + classes_analyzed
            result.metrics.quality_score = quality_score
            
            # Store detailed complexity metrics
            result.metrics.complexity_metrics = {
                "functions_analyzed": functions_analyzed,
                "classes_analyzed": classes_analyzed,
                "average_cyclomatic_complexity": avg_complexity,
                "complexity_distribution": dict(complexity_distribution),
                "function_metrics": function_metrics[:100],  # Limit for performance
                "class_metrics": class_metrics[:50],
                "highest_complexity_functions": sorted(function_metrics, 
                                                     key=lambda x: x['cyclomatic_complexity'], 
                                                     reverse=True)[:10]
            }
            
            # Generate recommendations
            result.recommendations = self._generate_recommendations(function_metrics, class_metrics)
            
            logger.info(f"Complexity analysis completed: {functions_analyzed} functions, {classes_analyzed} classes")
            
        except Exception as e:
            logger.error(f"Complexity analysis failed: {str(e)}")
            result.status = "failed"
            result.error_message = str(e)
        
        return result
    
    def _analyze_function_complexity(self, func: Function, file_content: str) -> Dict[str, Any]:
        """Analyze complexity metrics for a single function."""
        metrics = {
            "name": func.name,
            "file_path": str(func.filepath),
            "line_number": getattr(func, 'line_number', 0),
            "cyclomatic_complexity": self._calculate_cyclomatic_complexity(func),
            "cognitive_complexity": self._calculate_cognitive_complexity(func),
            "halstead_metrics": self._calculate_halstead_metrics(func, file_content),
            "nesting_depth": self._calculate_nesting_depth(func),
            "lines_of_code": self._calculate_function_loc(func, file_content),
            "parameter_count": len(func.parameters) if hasattr(func, 'parameters') else 0
        }
        
        # Calculate maintainability index
        metrics["maintainability_index"] = self._calculate_maintainability_index(metrics)
        
        return metrics
    
    def _analyze_class_complexity(self, cls: Class, file_content: str) -> Dict[str, Any]:
        """Analyze complexity metrics for a single class."""
        # Aggregate method complexities
        method_complexities = []
        total_methods = 0
        
        for method in cls.methods:
            method_complexity = self._calculate_cyclomatic_complexity(method)
            method_complexities.append(method_complexity)
            total_methods += 1
        
        avg_method_complexity = sum(method_complexities) / len(method_complexities) if method_complexities else 0
        max_method_complexity = max(method_complexities) if method_complexities else 0
        
        metrics = {
            "name": cls.name,
            "file_path": str(cls.filepath),
            "line_number": getattr(cls, 'line_number', 0),
            "method_count": total_methods,
            "attribute_count": len(cls.attributes) if hasattr(cls, 'attributes') else 0,
            "average_method_complexity": avg_method_complexity,
            "max_method_complexity": max_method_complexity,
            "inheritance_depth": self._calculate_inheritance_depth(cls),
            "coupling": len(cls.dependencies) if hasattr(cls, 'dependencies') else 0
        }
        
        return metrics
    
    def _calculate_cyclomatic_complexity(self, symbol) -> int:
        """Calculate cyclomatic complexity for a function or method."""
        if not hasattr(symbol, 'code_block') or not symbol.code_block:
            return 1
        
        complexity = 1  # Base complexity
        
        def analyze_statement(statement):
            nonlocal complexity
            
            if isinstance(statement, IfBlockStatement):
                complexity += 1
                if hasattr(statement, "elif_statements"):
                    complexity += len(statement.elif_statements)
            
            elif isinstance(statement, (ForLoopStatement, WhileStatement)):
                complexity += 1
            
            elif isinstance(statement, TryCatchStatement):
                if hasattr(statement, "except_blocks"):
                    complexity += len(statement.except_blocks)
                else:
                    complexity += 1
            
            # Analyze nested statements
            if hasattr(statement, 'nested_code_blocks'):
                for block in statement.nested_code_blocks:
                    if hasattr(block, 'statements'):
                        for nested_stmt in block.statements:
                            analyze_statement(nested_stmt)
        
        # Analyze all statements in the code block
        if hasattr(symbol.code_block, 'statements'):
            for statement in symbol.code_block.statements:
                analyze_statement(statement)
        
        return complexity
    
    def _calculate_cognitive_complexity(self, symbol) -> int:
        """Calculate cognitive complexity (more human-oriented than cyclomatic)."""
        if not hasattr(symbol, 'code_block') or not symbol.code_block:
            return 0
        
        complexity = 0
        nesting_level = 0
        
        def analyze_statement(statement, current_nesting):
            nonlocal complexity
            
            increment = 0
            new_nesting = current_nesting
            
            if isinstance(statement, IfBlockStatement):
                increment = 1 + current_nesting
                new_nesting = current_nesting + 1
                
                # elif adds complexity but doesn't increase nesting
                if hasattr(statement, "elif_statements"):
                    increment += len(statement.elif_statements)
            
            elif isinstance(statement, (ForLoopStatement, WhileStatement)):
                increment = 1 + current_nesting
                new_nesting = current_nesting + 1
            
            elif isinstance(statement, TryCatchStatement):
                increment = 1 + current_nesting
                new_nesting = current_nesting + 1
            
            complexity += increment
            
            # Analyze nested statements with increased nesting level
            if hasattr(statement, 'nested_code_blocks'):
                for block in statement.nested_code_blocks:
                    if hasattr(block, 'statements'):
                        for nested_stmt in block.statements:
                            analyze_statement(nested_stmt, new_nesting)
        
        if hasattr(symbol.code_block, 'statements'):
            for statement in symbol.code_block.statements:
                analyze_statement(statement, 0)
        
        return complexity
    
    def _calculate_halstead_metrics(self, func: Function, file_content: str) -> Dict[str, float]:
        """Calculate Halstead complexity metrics."""
        # Extract function content
        func_content = self._extract_function_content(func, file_content)
        
        if not func_content:
            return {"volume": 0, "difficulty": 0, "effort": 0}
        
        # Simple operator and operand counting (language-agnostic approach)
        operators = set()
        operands = set()
        
        # Common operators across languages
        operator_patterns = [
            r'\+', r'-', r'\*', r'/', r'%', r'=', r'==', r'!=', r'<', r'>', r'<=', r'>=',
            r'&&', r'\|\|', r'!', r'&', r'\|', r'\^', r'<<', r'>>', r'\?', r':',
            r'if', r'else', r'for', r'while', r'return', r'break', r'continue'
        ]
        
        for pattern in operator_patterns:
            matches = re.findall(pattern, func_content, re.IGNORECASE)
            if matches:
                operators.update(matches)
        
        # Simple operand extraction (identifiers)
        operand_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        operand_matches = re.findall(operand_pattern, func_content)
        operands.update(operand_matches)
        
        # Calculate Halstead metrics
        n1 = len(operators)  # Number of distinct operators
        n2 = len(operands)   # Number of distinct operands
        N1 = sum(func_content.count(op) for op in operators)  # Total operators
        N2 = sum(func_content.count(op) for op in operands)   # Total operands
        
        vocabulary = n1 + n2
        length = N1 + N2
        
        if vocabulary == 0:
            return {"volume": 0, "difficulty": 0, "effort": 0}
        
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n1 > 0 and n2 > 0 else 0
        effort = difficulty * volume
        
        return {
            "volume": round(volume, 2),
            "difficulty": round(difficulty, 2),
            "effort": round(effort, 2),
            "vocabulary": vocabulary,
            "length": length
        }
    
    def _calculate_nesting_depth(self, symbol) -> int:
        """Calculate maximum nesting depth."""
        if not hasattr(symbol, 'code_block') or not symbol.code_block:
            return 0
        
        max_depth = 0
        
        def analyze_statement(statement, current_depth):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            if isinstance(statement, (IfBlockStatement, ForLoopStatement, WhileStatement, TryCatchStatement)):
                if hasattr(statement, 'nested_code_blocks'):
                    for block in statement.nested_code_blocks:
                        if hasattr(block, 'statements'):
                            for nested_stmt in block.statements:
                                analyze_statement(nested_stmt, current_depth + 1)
        
        if hasattr(symbol.code_block, 'statements'):
            for statement in symbol.code_block.statements:
                analyze_statement(statement, 1)
        
        return max_depth
    
    def _calculate_function_loc(self, func: Function, file_content: str) -> int:
        """Calculate lines of code for a function."""
        func_content = self._extract_function_content(func, file_content)
        return self.calculate_lines_of_code(func_content)
    
    def _calculate_maintainability_index(self, metrics: Dict[str, Any]) -> float:
        """Calculate maintainability index using Halstead and complexity metrics."""
        halstead_volume = metrics["halstead_metrics"]["volume"]
        cyclomatic_complexity = metrics["cyclomatic_complexity"]
        loc = metrics["lines_of_code"]
        
        if loc == 0:
            return 100.0
        
        # Microsoft's maintainability index formula
        mi = 171 - 5.2 * math.log(max(1, halstead_volume)) - 0.23 * cyclomatic_complexity - 16.2 * math.log(max(1, loc))
        
        # Normalize to 0-100 scale
        return max(0, min(100, mi))
    
    def _calculate_inheritance_depth(self, cls: Class) -> int:
        """Calculate inheritance depth for a class."""
        if not hasattr(cls, 'parent_class_names') or not cls.parent_class_names:
            return 0
        
        # Simple depth calculation (could be enhanced with full inheritance tree analysis)
        return len(cls.parent_class_names)
    
    def _extract_function_content(self, func: Function, file_content: str) -> str:
        """Extract the content of a function from file content."""
        # This is a simplified extraction - could be enhanced with AST parsing
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
    
    def _get_complexity_level(self, complexity: int) -> str:
        """Get complexity level based on cyclomatic complexity."""
        if complexity >= self.cyclomatic_thresholds["critical"]:
            return "critical"
        elif complexity >= self.cyclomatic_thresholds["high"]:
            return "high"
        elif complexity >= self.cyclomatic_thresholds["medium"]:
            return "medium"
        elif complexity >= self.cyclomatic_thresholds["low"]:
            return "low"
        else:
            return "simple"
    
    def _check_function_thresholds(self, func: Function, metrics: Dict[str, Any], result: AnalysisResult):
        """Check function metrics against thresholds and create findings."""
        cyclomatic = metrics["cyclomatic_complexity"]
        cognitive = metrics["cognitive_complexity"]
        maintainability = metrics["maintainability_index"]
        
        # Check cyclomatic complexity
        if cyclomatic >= self.cyclomatic_thresholds["critical"]:
            severity = Severity.CRITICAL
        elif cyclomatic >= self.cyclomatic_thresholds["high"]:
            severity = Severity.HIGH
        elif cyclomatic >= self.cyclomatic_thresholds["medium"]:
            severity = Severity.MEDIUM
        elif cyclomatic >= self.cyclomatic_thresholds["low"]:
            severity = Severity.LOW
        else:
            severity = None
        
        if severity:
            finding = Finding(
                type=FindingType.COMPLEXITY,
                severity=severity,
                title=f"High Cyclomatic Complexity: {func.name}",
                description=f"Function '{func.name}' has cyclomatic complexity of {cyclomatic}, which exceeds recommended thresholds.",
                file_path=str(func.filepath),
                line_number=getattr(func, 'line_number', None),
                recommendation=f"Consider breaking down this function into smaller, more focused functions. Target complexity: < {self.cyclomatic_thresholds['low']}",
                rule_id="COMPLEXITY_001",
                metadata={
                    "cyclomatic_complexity": cyclomatic,
                    "cognitive_complexity": cognitive,
                    "maintainability_index": maintainability
                }
            )
            result.add_finding(finding)
        
        # Check maintainability index
        if maintainability < self.maintainability_thresholds["critical"]:
            severity = Severity.CRITICAL
        elif maintainability < self.maintainability_thresholds["high"]:
            severity = Severity.HIGH
        elif maintainability < self.maintainability_thresholds["medium"]:
            severity = Severity.MEDIUM
        elif maintainability < self.maintainability_thresholds["low"]:
            severity = Severity.LOW
        else:
            severity = None
        
        if severity:
            finding = Finding(
                type=FindingType.MAINTAINABILITY,
                severity=severity,
                title=f"Low Maintainability: {func.name}",
                description=f"Function '{func.name}' has low maintainability index ({maintainability:.1f}/100).",
                file_path=str(func.filepath),
                line_number=getattr(func, 'line_number', None),
                recommendation="Improve code structure, reduce complexity, and add documentation to increase maintainability.",
                rule_id="COMPLEXITY_002",
                metadata={
                    "maintainability_index": maintainability,
                    "cyclomatic_complexity": cyclomatic
                }
            )
            result.add_finding(finding)
    
    def _check_class_thresholds(self, cls: Class, metrics: Dict[str, Any], result: AnalysisResult):
        """Check class metrics against thresholds and create findings."""
        method_count = metrics["method_count"]
        max_method_complexity = metrics["max_method_complexity"]
        
        # Check for classes with too many methods
        if method_count > 20:
            severity = Severity.HIGH if method_count > 30 else Severity.MEDIUM
            
            finding = Finding(
                type=FindingType.COMPLEXITY,
                severity=severity,
                title=f"Large Class: {cls.name}",
                description=f"Class '{cls.name}' has {method_count} methods, which may indicate it has too many responsibilities.",
                file_path=str(cls.filepath),
                line_number=getattr(cls, 'line_number', None),
                recommendation="Consider breaking this class into smaller, more focused classes following the Single Responsibility Principle.",
                rule_id="COMPLEXITY_003",
                metadata={
                    "method_count": method_count,
                    "max_method_complexity": max_method_complexity
                }
            )
            result.add_finding(finding)
    
    def _calculate_quality_score(self, function_metrics: List[Dict], class_metrics: List[Dict]) -> float:
        """Calculate overall quality score based on complexity metrics."""
        if not function_metrics:
            return 100.0
        
        # Calculate average maintainability index
        maintainability_scores = [m["maintainability_index"] for m in function_metrics if m["maintainability_index"] > 0]
        avg_maintainability = sum(maintainability_scores) / len(maintainability_scores) if maintainability_scores else 100
        
        # Calculate complexity penalty
        high_complexity_functions = sum(1 for m in function_metrics if m["cyclomatic_complexity"] > self.cyclomatic_thresholds["medium"])
        total_functions = len(function_metrics)
        complexity_penalty = (high_complexity_functions / total_functions) * 30 if total_functions > 0 else 0
        
        # Calculate final score
        quality_score = avg_maintainability - complexity_penalty
        return max(0, min(100, quality_score))
    
    def _generate_recommendations(self, function_metrics: List[Dict], class_metrics: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on complexity analysis."""
        recommendations = []
        
        if not function_metrics:
            return recommendations
        
        # Analyze complexity distribution
        high_complexity_count = sum(1 for m in function_metrics if m["cyclomatic_complexity"] > self.cyclomatic_thresholds["medium"])
        total_functions = len(function_metrics)
        
        if high_complexity_count > 0:
            percentage = (high_complexity_count / total_functions) * 100
            recommendations.append(f"Refactor {high_complexity_count} functions ({percentage:.1f}%) with high complexity")
        
        # Check average complexity
        avg_complexity = sum(m["cyclomatic_complexity"] for m in function_metrics) / total_functions
        if avg_complexity > self.cyclomatic_thresholds["low"]:
            recommendations.append(f"Reduce average cyclomatic complexity from {avg_complexity:.1f} to below {self.cyclomatic_thresholds['low']}")
        
        # Check maintainability
        low_maintainability = sum(1 for m in function_metrics if m["maintainability_index"] < self.maintainability_thresholds["medium"])
        if low_maintainability > 0:
            recommendations.append(f"Improve maintainability of {low_maintainability} functions with low maintainability scores")
        
        # Class-specific recommendations
        large_classes = sum(1 for m in class_metrics if m["method_count"] > 15)
        if large_classes > 0:
            recommendations.append(f"Consider breaking down {large_classes} large classes into smaller, more focused classes")
        
        return recommendations[:5]  # Return top 5 recommendations

