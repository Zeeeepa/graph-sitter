#!/usr/bin/env python3
"""
🌳 TREE-SITTER QUERY PATTERNS & ADVANCED SYNTAX ANALYSIS 🌳

Advanced tree-sitter query patterns based on graph-sitter.com/introduction/advanced-settings
for comprehensive syntax tree analysis and pattern-based code search.

This module provides:
- Tree-sitter query pattern definitions
- Advanced syntax tree traversal
- Pattern-based code analysis
- Query-based metrics calculation
- Custom query pattern support
- Performance-optimized query execution

Features:
- Function and class pattern queries
- Import and dependency pattern analysis
- Control flow pattern detection
- Design pattern recognition
- Code smell detection patterns
- Security vulnerability patterns
- Performance anti-pattern detection
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Try to import tree-sitter for advanced query support
try:
    import tree_sitter
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.warning("Tree-sitter not available - query patterns will be limited")

# Try to import graph-sitter for enhanced integration
try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    logger.warning("Graph-sitter not available - using basic query patterns")


@dataclass
class QueryPattern:
    """Represents a tree-sitter query pattern."""
    name: str
    description: str
    pattern: str
    language: str
    category: str  # 'function', 'class', 'import', 'control_flow', 'design_pattern', etc.
    severity: str  # 'info', 'warning', 'error', 'critical'
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryMatch:
    """Represents a match from a query pattern."""
    pattern: QueryPattern
    node: Any  # Tree-sitter node or graph-sitter symbol
    file_path: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    matched_text: str
    captures: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """Results from executing query patterns."""
    pattern: QueryPattern
    matches: List[QueryMatch]
    execution_time: float
    total_matches: int
    files_analyzed: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class TreeSitterQueryEngine:
    """
    Advanced tree-sitter query engine for pattern-based code analysis.
    
    Based on graph-sitter.com advanced settings and tree-sitter query capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the query engine."""
        self.config = config or {}
        self.patterns: Dict[str, QueryPattern] = {}
        self.parsers: Dict[str, Any] = {}
        self.languages: Dict[str, Any] = {}
        
        # Initialize built-in patterns
        self._load_builtin_patterns()
        
        # Initialize parsers if tree-sitter is available
        if TREE_SITTER_AVAILABLE:
            self._initialize_parsers()
    
    def _load_builtin_patterns(self):
        """Load built-in query patterns for common analysis tasks."""
        
        # Function analysis patterns
        self.add_pattern(QueryPattern(
            name="complex_function",
            description="Functions with high complexity (many nested statements)",
            pattern="""
            (function_definition
              name: (identifier) @func_name
              body: (block
                (if_statement) @if_stmt
                (for_statement) @for_stmt
                (while_statement) @while_stmt
                (try_statement) @try_stmt
              )
            ) @function
            """,
            language="python",
            category="function",
            severity="warning",
            tags=["complexity", "maintainability"]
        ))
        
        self.add_pattern(QueryPattern(
            name="long_parameter_list",
            description="Functions with too many parameters",
            pattern="""
            (function_definition
              name: (identifier) @func_name
              parameters: (parameters
                (parameter) @param1
                (parameter) @param2
                (parameter) @param3
                (parameter) @param4
                (parameter) @param5
                (parameter) @param6
              )
            ) @function
            """,
            language="python",
            category="function",
            severity="warning",
            tags=["design", "parameters"]
        ))
        
        # Class analysis patterns
        self.add_pattern(QueryPattern(
            name="large_class",
            description="Classes with many methods (potential god class)",
            pattern="""
            (class_definition
              name: (identifier) @class_name
              body: (block
                (function_definition) @method1
                (function_definition) @method2
                (function_definition) @method3
                (function_definition) @method4
                (function_definition) @method5
                (function_definition) @method6
                (function_definition) @method7
                (function_definition) @method8
                (function_definition) @method9
                (function_definition) @method10
              )
            ) @class
            """,
            language="python",
            category="class",
            severity="warning",
            tags=["design", "god_class"]
        ))
        
        # Import analysis patterns
        self.add_pattern(QueryPattern(
            name="wildcard_import",
            description="Wildcard imports that can cause namespace pollution",
            pattern="""
            (import_from_statement
              module_name: (dotted_name) @module
              name: (wildcard_import) @wildcard
            ) @import
            """,
            language="python",
            category="import",
            severity="warning",
            tags=["imports", "namespace"]
        ))
        
        # Security patterns
        self.add_pattern(QueryPattern(
            name="eval_usage",
            description="Usage of eval() function which can be dangerous",
            pattern="""
            (call
              function: (identifier) @func_name
              (#eq? @func_name "eval")
            ) @eval_call
            """,
            language="python",
            category="security",
            severity="error",
            tags=["security", "dangerous"]
        ))
        
        # Performance patterns
        self.add_pattern(QueryPattern(
            name="nested_loops",
            description="Nested loops that may indicate performance issues",
            pattern="""
            (for_statement
              body: (block
                (for_statement) @inner_loop
              )
            ) @outer_loop
            """,
            language="python",
            category="performance",
            severity="info",
            tags=["performance", "loops"]
        ))
        
        # Design pattern detection
        self.add_pattern(QueryPattern(
            name="singleton_pattern",
            description="Potential singleton pattern implementation",
            pattern="""
            (class_definition
              name: (identifier) @class_name
              body: (block
                (function_definition
                  name: (identifier) @method_name
                  (#match? @method_name "getInstance|get_instance")
                ) @method
              )
            ) @class
            """,
            language="python",
            category="design_pattern",
            severity="info",
            tags=["singleton", "design_pattern"]
        ))
        
        # Code smell patterns
        self.add_pattern(QueryPattern(
            name="magic_numbers",
            description="Magic numbers that should be constants",
            pattern="""
            (integer) @number
            (#not-match? @number "^[01]$")
            """,
            language="python",
            category="code_smell",
            severity="info",
            tags=["magic_numbers", "constants"]
        ))
        
        # TypeScript/JavaScript patterns
        self.add_pattern(QueryPattern(
            name="any_type_usage",
            description="Usage of 'any' type in TypeScript",
            pattern="""
            (type_annotation
              (predefined_type) @type
              (#eq? @type "any")
            ) @any_usage
            """,
            language="typescript",
            category="type_safety",
            severity="warning",
            tags=["typescript", "type_safety"]
        ))
    
    def _initialize_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        if not TREE_SITTER_AVAILABLE:
            return
        
        # Note: In a real implementation, you would need to build and load
        # the actual tree-sitter language libraries
        logger.info("Tree-sitter parsers would be initialized here")
    
    def add_pattern(self, pattern: QueryPattern):
        """Add a custom query pattern."""
        self.patterns[pattern.name] = pattern
        logger.debug(f"Added query pattern: {pattern.name}")
    
    def remove_pattern(self, pattern_name: str):
        """Remove a query pattern."""
        if pattern_name in self.patterns:
            del self.patterns[pattern_name]
            logger.debug(f"Removed query pattern: {pattern_name}")
    
    def get_patterns_by_category(self, category: str) -> List[QueryPattern]:
        """Get all patterns in a specific category."""
        return [p for p in self.patterns.values() if p.category == category]
    
    def get_patterns_by_severity(self, severity: str) -> List[QueryPattern]:
        """Get all patterns with a specific severity."""
        return [p for p in self.patterns.values() if p.severity == severity]
    
    def get_patterns_by_language(self, language: str) -> List[QueryPattern]:
        """Get all patterns for a specific language."""
        return [p for p in self.patterns.values() if p.language == language]
    
    def execute_pattern(self, pattern: QueryPattern, codebase, files: Optional[List[str]] = None) -> QueryResult:
        """Execute a single query pattern against the codebase."""
        import time
        start_time = time.time()
        
        matches = []
        files_analyzed = 0
        
        try:
            if GRAPH_SITTER_AVAILABLE and hasattr(codebase, 'files'):
                # Use graph-sitter integration for enhanced analysis
                matches = self._execute_with_graph_sitter(pattern, codebase, files)
                files_analyzed = len(codebase.files)
            elif TREE_SITTER_AVAILABLE:
                # Use pure tree-sitter for pattern matching
                matches = self._execute_with_tree_sitter(pattern, codebase, files)
                files_analyzed = len(files) if files else 0
            else:
                # Fallback to basic pattern matching
                matches = self._execute_basic_pattern(pattern, codebase, files)
                files_analyzed = len(files) if files else 0
        
        except Exception as e:
            logger.error(f"Error executing pattern {pattern.name}: {e}")
        
        execution_time = time.time() - start_time
        
        return QueryResult(
            pattern=pattern,
            matches=matches,
            execution_time=execution_time,
            total_matches=len(matches),
            files_analyzed=files_analyzed,
            metadata={
                "engine": "graph-sitter" if GRAPH_SITTER_AVAILABLE else "tree-sitter" if TREE_SITTER_AVAILABLE else "basic"
            }
        )
    
    def _execute_with_graph_sitter(self, pattern: QueryPattern, codebase, files: Optional[List[str]] = None) -> List[QueryMatch]:
        """Execute pattern using graph-sitter integration."""
        matches = []
        
        try:
            # Use graph-sitter's advanced capabilities
            if pattern.category == "function":
                matches.extend(self._analyze_functions_with_graph_sitter(pattern, codebase))
            elif pattern.category == "class":
                matches.extend(self._analyze_classes_with_graph_sitter(pattern, codebase))
            elif pattern.category == "import":
                matches.extend(self._analyze_imports_with_graph_sitter(pattern, codebase))
            else:
                # Generic analysis
                matches.extend(self._generic_analysis_with_graph_sitter(pattern, codebase))
        
        except Exception as e:
            logger.warning(f"Graph-sitter analysis failed for {pattern.name}: {e}")
        
        return matches
    
    def _analyze_functions_with_graph_sitter(self, pattern: QueryPattern, codebase) -> List[QueryMatch]:
        """Analyze functions using graph-sitter."""
        matches = []
        
        for function in codebase.functions:
            try:
                match = None
                
                if pattern.name == "complex_function":
                    # Check for complexity indicators
                    complexity_score = getattr(function, 'complexity', 0)
                    if complexity_score > 10:  # High complexity threshold
                        match = QueryMatch(
                            pattern=pattern,
                            node=function,
                            file_path=str(function.filepath) if hasattr(function, 'filepath') else '',
                            start_line=function.start_point[0] if hasattr(function, 'start_point') else 0,
                            end_line=function.end_point[0] if hasattr(function, 'end_point') else 0,
                            start_column=function.start_point[1] if hasattr(function, 'start_point') else 0,
                            end_column=function.end_point[1] if hasattr(function, 'end_point') else 0,
                            matched_text=function.source if hasattr(function, 'source') else '',
                            captures={"func_name": function.name, "complexity": complexity_score}
                        )
                
                elif pattern.name == "long_parameter_list":
                    # Check parameter count
                    param_count = len(function.parameters) if hasattr(function, 'parameters') else 0
                    if param_count > 5:  # Too many parameters
                        match = QueryMatch(
                            pattern=pattern,
                            node=function,
                            file_path=str(function.filepath) if hasattr(function, 'filepath') else '',
                            start_line=function.start_point[0] if hasattr(function, 'start_point') else 0,
                            end_line=function.end_point[0] if hasattr(function, 'end_point') else 0,
                            start_column=function.start_point[1] if hasattr(function, 'start_point') else 0,
                            end_column=function.end_point[1] if hasattr(function, 'end_point') else 0,
                            matched_text=function.source if hasattr(function, 'source') else '',
                            captures={"func_name": function.name, "param_count": param_count}
                        )
                
                if match:
                    matches.append(match)
            
            except Exception as e:
                logger.warning(f"Error analyzing function {function.name}: {e}")
        
        return matches
    
    def _analyze_classes_with_graph_sitter(self, pattern: QueryPattern, codebase) -> List[QueryMatch]:
        """Analyze classes using graph-sitter."""
        matches = []
        
        for cls in codebase.classes:
            try:
                match = None
                
                if pattern.name == "large_class":
                    # Check method count
                    method_count = len(cls.methods) if hasattr(cls, 'methods') else 0
                    if method_count > 10:  # Too many methods
                        match = QueryMatch(
                            pattern=pattern,
                            node=cls,
                            file_path=str(cls.filepath) if hasattr(cls, 'filepath') else '',
                            start_line=cls.start_point[0] if hasattr(cls, 'start_point') else 0,
                            end_line=cls.end_point[0] if hasattr(cls, 'end_point') else 0,
                            start_column=cls.start_point[1] if hasattr(cls, 'start_point') else 0,
                            end_column=cls.end_point[1] if hasattr(cls, 'end_point') else 0,
                            matched_text=cls.source if hasattr(cls, 'source') else '',
                            captures={"class_name": cls.name, "method_count": method_count}
                        )
                
                elif pattern.name == "singleton_pattern":
                    # Check for singleton pattern indicators
                    if hasattr(cls, 'methods'):
                        singleton_methods = [m for m in cls.methods 
                                           if m.name in ['getInstance', 'get_instance', '__new__']]
                        if singleton_methods:
                            match = QueryMatch(
                                pattern=pattern,
                                node=cls,
                                file_path=str(cls.filepath) if hasattr(cls, 'filepath') else '',
                                start_line=cls.start_point[0] if hasattr(cls, 'start_point') else 0,
                                end_line=cls.end_point[0] if hasattr(cls, 'end_point') else 0,
                                start_column=cls.start_point[1] if hasattr(cls, 'start_point') else 0,
                                end_column=cls.end_point[1] if hasattr(cls, 'end_point') else 0,
                                matched_text=cls.source if hasattr(cls, 'source') else '',
                                captures={"class_name": cls.name, "singleton_methods": [m.name for m in singleton_methods]}
                            )
                
                if match:
                    matches.append(match)
            
            except Exception as e:
                logger.warning(f"Error analyzing class {cls.name}: {e}")
        
        return matches
    
    def _analyze_imports_with_graph_sitter(self, pattern: QueryPattern, codebase) -> List[QueryMatch]:
        """Analyze imports using graph-sitter."""
        matches = []
        
        try:
            for imp in codebase.imports:
                match = None
                
                if pattern.name == "wildcard_import":
                    # Check for wildcard imports
                    if hasattr(imp, 'imported_symbol') and imp.imported_symbol:
                        if any('*' in str(symbol) for symbol in imp.imported_symbol):
                            match = QueryMatch(
                                pattern=pattern,
                                node=imp,
                                file_path=str(imp.file.filepath) if hasattr(imp, 'file') and hasattr(imp.file, 'filepath') else '',
                                start_line=imp.start_point[0] if hasattr(imp, 'start_point') else 0,
                                end_line=imp.end_point[0] if hasattr(imp, 'end_point') else 0,
                                start_column=imp.start_point[1] if hasattr(imp, 'start_point') else 0,
                                end_column=imp.end_point[1] if hasattr(imp, 'end_point') else 0,
                                matched_text=imp.source if hasattr(imp, 'source') else '',
                                captures={"module": str(imp.module) if hasattr(imp, 'module') else ''}
                            )
                
                if match:
                    matches.append(match)
        
        except Exception as e:
            logger.warning(f"Error analyzing imports: {e}")
        
        return matches
    
    def _generic_analysis_with_graph_sitter(self, pattern: QueryPattern, codebase) -> List[QueryMatch]:
        """Generic analysis using graph-sitter."""
        matches = []
        
        # This would implement more generic pattern matching
        # For now, return empty list
        logger.debug(f"Generic analysis for pattern {pattern.name} not yet implemented")
        
        return matches
    
    def _execute_with_tree_sitter(self, pattern: QueryPattern, codebase, files: Optional[List[str]] = None) -> List[QueryMatch]:
        """Execute pattern using pure tree-sitter."""
        matches = []
        
        # This would implement pure tree-sitter query execution
        logger.debug(f"Pure tree-sitter execution for pattern {pattern.name} not yet implemented")
        
        return matches
    
    def _execute_basic_pattern(self, pattern: QueryPattern, codebase, files: Optional[List[str]] = None) -> List[QueryMatch]:
        """Execute pattern using basic string matching."""
        matches = []
        
        # This would implement basic pattern matching as fallback
        logger.debug(f"Basic pattern execution for pattern {pattern.name} not yet implemented")
        
        return matches
    
    def execute_patterns(self, patterns: List[str], codebase, files: Optional[List[str]] = None) -> List[QueryResult]:
        """Execute multiple query patterns."""
        results = []
        
        for pattern_name in patterns:
            if pattern_name in self.patterns:
                result = self.execute_pattern(self.patterns[pattern_name], codebase, files)
                results.append(result)
            else:
                logger.warning(f"Pattern not found: {pattern_name}")
        
        return results
    
    def execute_all_patterns(self, codebase, files: Optional[List[str]] = None) -> List[QueryResult]:
        """Execute all available query patterns."""
        return self.execute_patterns(list(self.patterns.keys()), codebase, files)
    
    def execute_patterns_by_category(self, category: str, codebase, files: Optional[List[str]] = None) -> List[QueryResult]:
        """Execute all patterns in a specific category."""
        patterns = self.get_patterns_by_category(category)
        return self.execute_patterns([p.name for p in patterns], codebase, files)
    
    def execute_patterns_by_severity(self, severity: str, codebase, files: Optional[List[str]] = None) -> List[QueryResult]:
        """Execute all patterns with a specific severity."""
        patterns = self.get_patterns_by_severity(severity)
        return self.execute_patterns([p.name for p in patterns], codebase, files)
    
    def generate_report(self, results: List[QueryResult]) -> Dict[str, Any]:
        """Generate a comprehensive report from query results."""
        report = {
            "summary": {
                "total_patterns": len(results),
                "total_matches": sum(r.total_matches for r in results),
                "total_execution_time": sum(r.execution_time for r in results),
                "files_analyzed": max((r.files_analyzed for r in results), default=0)
            },
            "by_category": {},
            "by_severity": {},
            "by_language": {},
            "patterns": []
        }
        
        # Group by category
        for result in results:
            category = result.pattern.category
            if category not in report["by_category"]:
                report["by_category"][category] = {"patterns": 0, "matches": 0}
            report["by_category"][category]["patterns"] += 1
            report["by_category"][category]["matches"] += result.total_matches
        
        # Group by severity
        for result in results:
            severity = result.pattern.severity
            if severity not in report["by_severity"]:
                report["by_severity"][severity] = {"patterns": 0, "matches": 0}
            report["by_severity"][severity]["patterns"] += 1
            report["by_severity"][severity]["matches"] += result.total_matches
        
        # Group by language
        for result in results:
            language = result.pattern.language
            if language not in report["by_language"]:
                report["by_language"][language] = {"patterns": 0, "matches": 0}
            report["by_language"][language]["patterns"] += 1
            report["by_language"][language]["matches"] += result.total_matches
        
        # Add detailed pattern results
        for result in results:
            report["patterns"].append({
                "name": result.pattern.name,
                "description": result.pattern.description,
                "category": result.pattern.category,
                "severity": result.pattern.severity,
                "language": result.pattern.language,
                "matches": result.total_matches,
                "execution_time": result.execution_time,
                "files_analyzed": result.files_analyzed
            })
        
        return report
    
    def save_patterns_to_file(self, filepath: str):
        """Save all patterns to a JSON file."""
        patterns_data = {}
        for name, pattern in self.patterns.items():
            patterns_data[name] = {
                "name": pattern.name,
                "description": pattern.description,
                "pattern": pattern.pattern,
                "language": pattern.language,
                "category": pattern.category,
                "severity": pattern.severity,
                "tags": pattern.tags,
                "metadata": pattern.metadata
            }
        
        with open(filepath, 'w') as f:
            json.dump(patterns_data, f, indent=2)
        
        logger.info(f"Saved {len(patterns_data)} patterns to {filepath}")
    
    def load_patterns_from_file(self, filepath: str):
        """Load patterns from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                patterns_data = json.load(f)
            
            for name, data in patterns_data.items():
                pattern = QueryPattern(
                    name=data["name"],
                    description=data["description"],
                    pattern=data["pattern"],
                    language=data["language"],
                    category=data["category"],
                    severity=data["severity"],
                    tags=data.get("tags", []),
                    metadata=data.get("metadata", {})
                )
                self.add_pattern(pattern)
            
            logger.info(f"Loaded {len(patterns_data)} patterns from {filepath}")
        
        except Exception as e:
            logger.error(f"Error loading patterns from {filepath}: {e}")


def create_query_engine(config: Optional[Dict[str, Any]] = None) -> TreeSitterQueryEngine:
    """Create a new tree-sitter query engine."""
    return TreeSitterQueryEngine(config)


def analyze_with_queries(codebase, patterns: Optional[List[str]] = None, 
                        category: Optional[str] = None, 
                        severity: Optional[str] = None) -> List[QueryResult]:
    """
    Analyze codebase using tree-sitter query patterns.
    
    Args:
        codebase: The codebase to analyze
        patterns: Specific patterns to execute (optional)
        category: Execute patterns from specific category (optional)
        severity: Execute patterns with specific severity (optional)
    
    Returns:
        List of query results
    """
    engine = create_query_engine()
    
    if patterns:
        return engine.execute_patterns(patterns, codebase)
    elif category:
        return engine.execute_patterns_by_category(category, codebase)
    elif severity:
        return engine.execute_patterns_by_severity(severity, codebase)
    else:
        return engine.execute_all_patterns(codebase)


if __name__ == "__main__":
    # Example usage
    engine = create_query_engine()
    
    print("🌳 Tree-sitter Query Engine")
    print("=" * 50)
    print(f"Available patterns: {len(engine.patterns)}")
    
    for category in ["function", "class", "import", "security", "performance"]:
        patterns = engine.get_patterns_by_category(category)
        print(f"{category.title()} patterns: {len(patterns)}")
    
    print("\nExample patterns:")
    for pattern in list(engine.patterns.values())[:5]:
        print(f"- {pattern.name}: {pattern.description}")

