"""
Core Analysis Components

Provides the fundamental analysis capabilities for the unified tree-sitter system.
"""

from .models import (
    CodeIssue, DeadCodeItem, FunctionMetrics, ClassMetrics, FileAnalysis,
    ComprehensiveAnalysisResult, AnalysisOptions, AnalysisContext,
    ImportLoop, TrainingDataItem, GraphAnalysisResult,
    EnhancedFunctionMetrics, EnhancedClassMetrics,
    create_default_analysis_options, merge_analysis_results
)

# Tree-sitter core components
from .tree_sitter_core import TreeSitterCore, get_tree_sitter_core, ParseResult, QueryMatch

# Import other core components
from .graph_enhancements import (
    hop_through_imports, get_function_context, detect_import_loops,
    analyze_graph_structure, detect_dead_code, generate_training_data,
    analyze_function_enhanced, analyze_class_enhanced, get_codebase_summary_enhanced,
    generate_dead_code_recommendations, generate_import_loop_recommendations
)

from .class_hierarchy import (
    analyze_inheritance_chains, find_deepest_inheritance, find_inheritance_chains,
    find_abstract_classes, build_inheritance_tree, get_class_relationships,
    detect_design_patterns, has_singleton_methods, has_factory_methods,
    has_observer_methods, has_decorator_structure, has_strategy_structure,
    generate_hierarchy_report
)

try:
    from .codebase_analyzer import CodebaseAnalyzer
    CODEBASE_ANALYZER_AVAILABLE = True
except ImportError:
    CODEBASE_ANALYZER_AVAILABLE = False

# Core analysis functions - implementing missing functionality
def calculate_cyclomatic_complexity(node) -> int:
    """Calculate cyclomatic complexity for a code node."""
    # Enhanced implementation using tree-sitter
    try:
        if hasattr(node, 'type'):
            # Tree-sitter node
            return _calculate_complexity_tree_sitter(node)
        else:
            # Fallback for other node types
            return 1
    except Exception:
        return 1

def _calculate_complexity_tree_sitter(node) -> int:
    """Calculate complexity using tree-sitter node analysis."""
    complexity = 1  # Base complexity
    
    # Decision points that increase complexity
    decision_points = [
        'if_statement', 'elif_clause', 'else_clause',
        'while_statement', 'for_statement', 
        'try_statement', 'except_clause',
        'and', 'or',
        'conditional_expression',
        'case_clause', 'match_statement'
    ]
    
    def count_decision_points(node):
        count = 0
        if hasattr(node, 'type') and node.type in decision_points:
            count += 1
        
        if hasattr(node, 'children'):
            for child in node.children:
                count += count_decision_points(child)
        
        return count
    
    complexity += count_decision_points(node)
    return complexity

def calculate_cyclomatic_complexity_graph_sitter(function) -> int:
    """Enhanced cyclomatic complexity calculation using Graph-Sitter."""
    try:
        # Use tree-sitter core for analysis
        core = get_tree_sitter_core()
        
        if hasattr(function, 'source') and hasattr(function, 'filepath'):
            # Parse the function source
            language = core.detect_language(function.filepath) or 'python'
            parse_result = core.parse_string(function.source, language)
            
            if parse_result and parse_result.tree:
                return calculate_cyclomatic_complexity(parse_result.tree.root_node)
        
        # Fallback to basic analysis
        return _calculate_complexity_basic(function)
    except Exception:
        return 1

def _calculate_complexity_basic(function) -> int:
    """Basic complexity calculation fallback."""
    if not hasattr(function, 'source'):
        return 1
    
    source = function.source.lower()
    complexity = 1
    
    # Count decision points in source
    keywords = ['if ', 'elif ', 'while ', 'for ', 'try:', 'except ', 'and ', 'or ', '?']
    for keyword in keywords:
        complexity += source.count(keyword)
    
    return max(1, complexity)

def get_operators_and_operands(function):
    """Extract operators and operands for Halstead metrics."""
    try:
        if not hasattr(function, 'source'):
            return [], []
        
        # Use tree-sitter for accurate parsing
        core = get_tree_sitter_core()
        language = getattr(function, 'language', 'python')
        if hasattr(function, 'filepath'):
            language = core.detect_language(function.filepath) or 'python'
        
        parse_result = core.parse_string(function.source, language)
        if not parse_result or not parse_result.tree:
            return _extract_operators_operands_basic(function.source)
        
        operators = []
        operands = []
        
        def extract_from_node(node):
            if hasattr(node, 'type'):
                # Operators
                if node.type in ['binary_operator', 'unary_operator', 'comparison_operator', 
                               'boolean_operator', 'assignment', 'augmented_assignment']:
                    operators.append(node.type)
                
                # Operands (identifiers, literals)
                elif node.type in ['identifier', 'integer', 'float', 'string', 'true', 'false', 'none']:
                    operands.append(node.type)
                
                # Recurse through children
                if hasattr(node, 'children'):
                    for child in node.children:
                        extract_from_node(child)
        
        extract_from_node(parse_result.tree.root_node)
        return operators, operands
    except Exception:
        return _extract_operators_operands_basic(getattr(function, 'source', ''))

def _extract_operators_operands_basic(source: str):
    """Basic operator/operand extraction fallback."""
    operators = []
    operands = []
    
    # Basic operator patterns
    operator_patterns = ['+', '-', '*', '/', '//', '%', '**', '=', '==', '!=', '<', '>', '<=', '>=', 
                        'and', 'or', 'not', 'in', 'is', '&', '|', '^', '~', '<<', '>>', '+=', '-=']
    
    for op in operator_patterns:
        count = source.count(op)
        operators.extend([op] * count)
    
    # Basic operand patterns (simplified)
    import re
    # Find identifiers
    identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', source)
    # Find numbers
    numbers = re.findall(r'\b\d+\.?\d*\b', source)
    # Find strings
    strings = re.findall(r'["\'][^"\']*["\']', source)
    
    operands.extend(identifiers)
    operands.extend(numbers)
    operands.extend(strings)
    
    return operators, operands

def calculate_halstead_volume(operators, operands):
    """Calculate Halstead volume metrics."""
    try:
        # Halstead metrics calculation
        n1 = len(set(operators))  # Number of distinct operators
        n2 = len(set(operands))   # Number of distinct operands
        N1 = len(operators)       # Total number of operators
        N2 = len(operands)        # Total number of operands
        
        # Avoid division by zero
        if n1 == 0 and n2 == 0:
            return 0.0, 0, 0, 0, 0
        
        # Program vocabulary
        vocabulary = n1 + n2
        
        # Program length
        length = N1 + N2
        
        # Calculated program length
        import math
        if n1 > 0 and n2 > 0:
            calculated_length = n1 * math.log2(n1) + n2 * math.log2(n2)
        else:
            calculated_length = length
        
        # Volume
        if vocabulary > 0:
            volume = length * math.log2(vocabulary)
        else:
            volume = 0.0
        
        return volume, n1, n2, N1, N2
    except Exception:
        return 0.0, 0, 0, 0, 0

def calculate_maintainability_index(volume: float, complexity: int, loc: int) -> int:
    """Calculate maintainability index."""
    try:
        import math
        
        # Maintainability Index formula
        # MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
        
        # Avoid log of zero
        volume = max(1, volume)
        loc = max(1, loc)
        
        mi = 171 - 5.2 * math.log(volume) - 0.23 * complexity - 16.2 * math.log(loc)
        
        # Normalize to 0-100 scale
        mi = max(0, min(100, mi))
        
        return int(mi)
    except Exception:
        return 50  # Default moderate maintainability

def calculate_doi(cls) -> int:
    """Calculate depth of inheritance."""
    try:
        if not hasattr(cls, 'superclasses'):
            return 0
        
        superclasses = cls.superclasses
        if not superclasses:
            return 0
        
        # Simple depth calculation
        return len(superclasses)
    except Exception:
        return 0

def count_lines(source_code: str):
    """Count different types of lines in source code."""
    try:
        lines = source_code.split('\n')
        total_lines = len(lines)
        
        blank_lines = 0
        comment_lines = 0
        code_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                comment_lines += 1
            else:
                code_lines += 1
        
        return total_lines, code_lines, comment_lines, blank_lines
    except Exception:
        lines = source_code.split('\n') if source_code else []
        total = len(lines)
        return total, total, 0, 0

def analyze_python_file(file_path: str, options=None):
    """Analyze a Python file - redirects to unified analyzer."""
    from ..unified_analyzer import UnifiedAnalyzer
    analyzer = UnifiedAnalyzer()
    return analyzer.analyze_file(file_path, 'python')

def analyze_function_ast(node, file_path: str, source_code: str):
    """Analyze function AST node."""
    # Placeholder implementation
    return None

def analyze_class_ast(node, file_path: str):
    """Analyze class AST node."""
    # Placeholder implementation
    return None

def analyze_codebase_directory(path: str, options=None):
    """Analyze codebase directory - redirects to unified analyzer."""
    from ..unified_analyzer import UnifiedAnalyzer
    analyzer = UnifiedAnalyzer()
    return analyzer.analyze_codebase(path)

def get_complexity_rank(complexity: int) -> str:
    """Get complexity rank description."""
    if complexity <= 5:
        return "Low"
    elif complexity <= 10:
        return "Medium"
    elif complexity <= 20:
        return "High"
    else:
        return "Very High"

def calculate_technical_debt_hours(issues) -> float:
    """Calculate technical debt in hours."""
    # Placeholder implementation
    return 0.0

def generate_summary_statistics(result):
    """Generate summary statistics."""
    # Placeholder implementation
    return {}

__all__ = [
    # Models
    "CodeIssue", "DeadCodeItem", "FunctionMetrics", "ClassMetrics", "FileAnalysis",
    "ComprehensiveAnalysisResult", "AnalysisOptions", "AnalysisContext",
    "ImportLoop", "TrainingDataItem", "GraphAnalysisResult",
    "EnhancedFunctionMetrics", "EnhancedClassMetrics",
    "create_default_analysis_options", "merge_analysis_results",
    
    # Graph Enhancement Functions
    "hop_through_imports", "get_function_context", "detect_import_loops",
    "analyze_graph_structure", "detect_dead_code", "generate_training_data",
    "analyze_function_enhanced", "analyze_class_enhanced", "get_codebase_summary_enhanced",
    "generate_dead_code_recommendations", "generate_import_loop_recommendations",
    
    # Class Hierarchy Analysis
    "analyze_inheritance_chains", "find_deepest_inheritance", "find_inheritance_chains",
    "find_abstract_classes", "build_inheritance_tree", "get_class_relationships",
    "detect_design_patterns", "has_singleton_methods", "has_factory_methods",
    "has_observer_methods", "has_decorator_structure", "has_strategy_structure",
    "generate_hierarchy_report",
    
    # Tree-sitter core components
    "TreeSitterCore", "get_tree_sitter_core", "ParseResult", "QueryMatch",
    
    # Analysis Engine Functions
    "calculate_cyclomatic_complexity", "calculate_cyclomatic_complexity_graph_sitter",
    "get_operators_and_operands", "calculate_halstead_volume", "calculate_maintainability_index",
    "calculate_doi", "count_lines", "analyze_python_file", "analyze_function_ast",
    "analyze_class_ast", "analyze_codebase_directory", "get_complexity_rank",
    "calculate_technical_debt_hours", "generate_summary_statistics",
    
    # Conditional exports
    "CODEBASE_ANALYZER_AVAILABLE",
]

# Add CodebaseAnalyzer if available
if CODEBASE_ANALYZER_AVAILABLE:
    __all__.append("CodebaseAnalyzer")
