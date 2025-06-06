#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE CODEBASE ANALYSIS TOOL - ENHANCED WITH GRAPH-SITTER 🚀

A single, powerful executable that consolidates all analysis capabilities:
- Core quality metrics (maintainability, complexity, Halstead, etc.)
- Advanced investigation features (function context, relationships)
- Usage pattern analysis (ML training data, visualizations)
- Graph-sitter integration (pre-computed graphs, dependencies)
- Tree-sitter query patterns and visualization
- Interactive syntax tree visualization
- Production-ready error handling and performance optimization
- Import loop detection and circular dependency analysis
- Training data generation for LLMs
- Advanced graph-based code analysis
- Dead code detection using usage analysis
- Enhanced configuration options

Based on patterns from: https://graph-sitter.com/tutorials/at-a-glance

Enhanced Features:
- Graph-sitter pre-computed element access (functions, classes, imports, files)
- Function/class dependency and usage analysis
- Import relationship mapping and loop detection
- Training data extraction for ML models
- Advanced configuration with CodebaseConfig
- Visualization integration with codebase.viz
- Performance optimizations with lazy loading

Usage:
    python analyze_codebase.py path/to/code
    python analyze_codebase.py --repo fastapi/fastapi
    python analyze_codebase.py . --format json --output results.json
    python analyze_codebase.py . --comprehensive --visualize
    python analyze_codebase.py . --tree-sitter --export-html analysis.html
    python analyze_codebase.py . --training-data --output training.json
    python analyze_codebase.py . --import-loops --visualize-graph
    python analyze_codebase.py . --dead-code --remove-unused
    python analyze_codebase.py . --graph-analysis --advanced-config
"""
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
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.enums import EdgeType, SymbolType
    from graph_sitter.adapters.graph_sitter_enhancements import (
    from graph_sitter.adapters.enhanced_analyzer import EnhancedCodebaseAnalyzer
        detect_import_loops, analyze_graph_structure, detect_dead_code,
        generate_training_data, get_codebase_summary_enhanced,
        analyze_function_enhanced, analyze_class_enhanced,
        ImportLoop, TrainingDataItem, DeadCodeItem, GraphAnalysisResult,
        EnhancedFunctionMetrics, EnhancedClassMetrics
    )
        get_codebase_summary, get_file_summary, get_class_summary, 
        get_function_summary, get_symbol_summary
    )
    GRAPH_SITTER_AVAILABLE = True
    
    # Try to import NetworkX for import loop detection
    try:
        import networkx as nx
        NETWORKX_AVAILABLE = True
    except ImportError:
        NETWORKX_AVAILABLE = False
        logger.warning("NetworkX not available - import loop detection will be disabled")
except ImportError as e:
    logger.warning(f"Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False
    NETWORKX_AVAILABLE = False
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
class DeadCodeItem:
    """Represents dead/unused code."""
    type: str  # 'function', 'class', 'variable'
    name: str
    file_path: str
    line_start: int
    line_end: int
    reason: str
    confidence: float

@dataclass
class FunctionMetrics:
    """Comprehensive function metrics."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    halstead_volume: float
    maintainability_index: int
    lines_of_code: int
    parameters_count: int
    return_statements: int
    dependencies: List[str] = field(default_factory=list)
    usages: List[str] = field(default_factory=list)
    call_sites: List[str] = field(default_factory=list)
    complexity_rank: str = "A"
    loc: int = 0
    lloc: int = 0
    sloc: int = 0
    comments: int = 0
    halstead_n1: int = 0
    halstead_n2: int = 0
    halstead_N1: int = 0
    halstead_N2: int = 0
    docstring: str = ""
    function_calls: int = 0
    parameters: int = 0
    returns: int = 0

@dataclass
class ClassMetrics:
    """Metrics for a class."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    depth_of_inheritance: int
    method_count: int  # Changed from methods_count to method_count for consistency
    attribute_count: int  # Changed from attributes_count to attribute_count for consistency
    lines_of_code: int
    parent_classes: List[str] = field(default_factory=list)

@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    file_path: str
    lines_of_code: int
    logical_lines: int
    source_lines: int
    comment_lines: int
    comment_density: float
    functions: List[FunctionMetrics] = field(default_factory=list)
    classes: List[ClassMetrics] = field(default_factory=list)
    issues: List[CodeIssue] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    complexity_score: float = 0.0

@dataclass
class ComprehensiveAnalysisResult:
    """Complete analysis results."""
    # Basic metrics
    total_files: int
    total_functions: int
    total_classes: int
    total_lines: int
    total_logical_lines: int
    total_source_lines: int
    total_comment_lines: int
    
    # Quality metrics
    average_maintainability_index: float
    average_cyclomatic_complexity: float
    average_halstead_volume: float
    average_depth_of_inheritance: float
    comment_density: float
    technical_debt_ratio: float
    
    # Analysis results
    files: List[FileAnalysis] = field(default_factory=list)
    issues: List[CodeIssue] = field(default_factory=list)
    dead_code_items: List[DeadCodeItem] = field(default_factory=list)
    
    # Advanced metrics
    function_metrics: List[FunctionMetrics] = field(default_factory=list)
    class_metrics: List[ClassMetrics] = field(default_factory=list)
    
    # Investigation results
    top_level_functions: List[str] = field(default_factory=list)
    top_level_classes: List[str] = field(default_factory=list)
    inheritance_hierarchy: Dict[str, Any] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    usage_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    analysis_time: float = 0.0
    files_per_second: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# ============================================================================
# CORE ANALYSIS FUNCTIONS - Enhanced with Graph-Sitter Integration
# ============================================================================

def calculate_cyclomatic_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity for AST node (fallback method)."""
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.Try):
            complexity += len(child.handlers)
        elif isinstance(child, (ast.And, ast.Or)):
            complexity += 1
        elif isinstance(child, ast.comprehension):
            complexity += 1
    
    return complexity


def calculate_cyclomatic_complexity_graph_sitter(function):
    """Enhanced cyclomatic complexity calculation using Graph-Sitter (from repo_analytics)."""
    if not GRAPH_SITTER_AVAILABLE or not hasattr(function, 'code_block'):
        return 1
    
    def analyze_statement(statement):
        complexity = 0

        if isinstance(statement, IfBlockStatement):
            complexity += 1
            if hasattr(statement, "elif_statements"):
                complexity += len(statement.elif_statements)

        elif isinstance(statement, (ForLoopStatement, WhileStatement)):
            complexity += 1

        elif isinstance(statement, TryCatchStatement):
            complexity += len(getattr(statement, "except_blocks", []))

        if hasattr(statement, "condition") and isinstance(statement.condition, str):
            complexity += statement.condition.count(" and ") + statement.condition.count(" or ")

        if hasattr(statement, "nested_code_blocks"):
            for block in statement.nested_code_blocks:
                complexity += analyze_block(block)

        return complexity

    def analyze_block(block):
        if not block or not hasattr(block, "statements"):
            return 0
        return sum(analyze_statement(stmt) for stmt in block.statements)

    return 1 + analyze_block(function.code_block)


def cc_rank(complexity):
    """Rank cyclomatic complexity (from repo_analytics)."""
    if complexity < 0:
        raise ValueError("Complexity must be a non-negative value")

    ranks = [
        (1, 5, "A"),
        (6, 10, "B"),
        (11, 20, "C"),
        (21, 30, "D"),
        (31, 40, "E"),
        (41, float("inf"), "F"),
    ]
    for low, high, rank in ranks:
        if low <= complexity <= high:
            return rank
    return "F"


def calculate_doi(cls):
    """Calculate the depth of inheritance for a given class (from repo_analytics)."""
    if GRAPH_SITTER_AVAILABLE and hasattr(cls, 'superclasses'):
        return len(cls.superclasses)
    elif hasattr(cls, 'bases'):
        return len(cls.bases)
    return 0


def get_operators_and_operands(function):
    """Extract operators and operands from function (from repo_analytics)."""
    operators = []
    operands = []

    if not GRAPH_SITTER_AVAILABLE or not hasattr(function, 'code_block'):
        return operators, operands

    try:
        for statement in function.code_block.statements:
            for call in statement.function_calls:
                operators.append(call.name)
                for arg in call.args:
                    operands.append(arg.source)

            if hasattr(statement, "expressions"):
                for expr in statement.expressions:
                    if isinstance(expr, BinaryExpression):
                        operators.extend([op.source for op in expr.operators])
                        operands.extend([elem.source for elem in expr.elements])
                    elif isinstance(expr, UnaryExpression):
                        operators.append(expr.ts_node.type)
                        operands.append(expr.argument.source)
                    elif isinstance(expr, ComparisonExpression):
                        operators.extend([op.source for op in expr.operators])
                        operands.extend([elem.source for elem in expr.elements])

            if hasattr(statement, "expression"):
                expr = statement.expression
                if isinstance(expr, BinaryExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])
                elif isinstance(expr, UnaryExpression):
                    operators.append(expr.ts_node.type)
                    operands.append(expr.argument.source)
                elif isinstance(expr, ComparisonExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])
    except Exception as e:
        logger.debug(f"Error extracting operators/operands: {e}")

    return operators, operands


def calculate_halstead_volume(operators, operands):
    """Calculate Halstead volume metrics (from repo_analytics)."""
    n1 = len(set(operators))
    n2 = len(set(operands))

    N1 = len(operators)
    N2 = len(operands)

    N = N1 + N2
    n = n1 + n2

    if n > 0:
        volume = N * math.log2(n)
        return volume, N1, N2, n1, n2
    return 0, N1, N2, n1, n2


def count_lines(source: str):
    """Count different types of lines in source code (from repo_analytics)."""
    if not source.strip():
        return 0, 0, 0, 0

    lines = [line.strip() for line in source.splitlines()]
    loc = len(lines)
    sloc = len([line for line in lines if line])

    in_multiline = False
    comments = 0
    code_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        code_part = line
        if not in_multiline and "#" in line:
            comment_start = line.find("#")
            if not re.search(r'["\'].*#.*["\']', line[:comment_start]):
                code_part = line[:comment_start].strip()
                if line[comment_start:].strip():
                    comments += 1

        if ('"""' in line or "'''" in line) and not (line.count('"""') % 2 == 0 or line.count("'''") % 2 == 0):
            if in_multiline:
                in_multiline = False
                comments += 1
            else:
                in_multiline = True
                comments += 1
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    code_part = ""
        elif in_multiline:
            comments += 1
            code_part = ""
        elif line.strip().startswith("#"):
            comments += 1
            code_part = ""

        if code_part.strip():
            code_lines.append(code_part)

        i += 1

    lloc = 0
    continued_line = False
    for line in code_lines:
        if continued_line:
            if not any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
                continued_line = False
            continue

        lloc += len([stmt for stmt in line.split(";") if stmt.strip()])

        if any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
            continued_line = True

    return loc, lloc, sloc, comments


def calculate_maintainability_index(halstead_volume: float, cyclomatic_complexity: float, loc: int) -> int:
    """Calculate the normalized maintainability index (from repo_analytics)."""
    if loc <= 0:
        return 100

    try:
        raw_mi = 171 - 5.2 * math.log(max(1, halstead_volume)) - 0.23 * cyclomatic_complexity - 16.2 * math.log(max(1, loc))
        normalized_mi = max(0, min(100, raw_mi * 100 / 171))
        return int(normalized_mi)
    except (ValueError, TypeError):
        return 0


# ============================================================================
# AST ANALYSIS UTILITIES
# ============================================================================

def extract_operators_operands_ast(node: ast.AST) -> Tuple[List[str], List[str]]:
    """Extract operators and operands from AST node for Halstead metrics."""
    operators = []
    operands = []
    
    for child in ast.walk(node):
        # Operators
        if isinstance(child, ast.BinOp):
            operators.append(type(child.op).__name__)
        elif isinstance(child, ast.UnaryOp):
            operators.append(type(child.op).__name__)
        elif isinstance(child, ast.Compare):
            operators.extend([type(op).__name__ for op in child.ops])
        elif isinstance(child, ast.BoolOp):
            operators.append(type(child.op).__name__)
        elif isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            operators.append(type(child).__name__)
        elif isinstance(child, ast.FunctionDef):
            operators.append('FunctionDef')
        elif isinstance(child, ast.ClassDef):
            operators.append('ClassDef')
        elif isinstance(child, ast.Return):
            operators.append('Return')
        elif isinstance(child, ast.Assign):
            operators.append('Assign')
        
        # Operands
        elif isinstance(child, ast.Name):
            operands.append(child.id)
        elif isinstance(child, ast.Constant):
            operands.append(str(child.value))
        elif isinstance(child, ast.Attribute):
            operands.append(child.attr)
    
    return operators, operands

def analyze_function_ast(func_node: ast.FunctionDef, file_path: str, source_lines: List[str]) -> FunctionMetrics:
    """Analyze a function using AST (fallback method)."""
    try:
        # Calculate basic metrics
        complexity = calculate_cyclomatic_complexity(func_node)
        
        # Extract function source
        start_line = func_node.lineno - 1
        end_line = func_node.end_lineno if hasattr(func_node, 'end_lineno') else start_line + 10
        func_source = '\n'.join(source_lines[start_line:end_line])
        
        # Calculate line metrics
        loc, lloc, sloc, comments = count_lines(func_source)
        
        # Extract operators and operands (basic AST-based)
        operators, operands = extract_operators_operands_ast(func_node)
        
        # Calculate Halstead metrics
        volume, n1, n2, N1, N2 = calculate_halstead_volume(operators, operands)
        
        # Calculate maintainability index
        maintainability = calculate_maintainability_index(volume, complexity, loc)
        
        return FunctionMetrics(
            name=func_node.name,
            file_path=file_path,
            line_start=func_node.lineno,
            line_end=end_line,
            cyclomatic_complexity=complexity,
            halstead_volume=volume,  # Required field
            maintainability_index=maintainability,  # Required field
            lines_of_code=loc,  # Required field
            parameters_count=len(func_node.args.args),  # Required field
            return_statements=len([node for node in ast.walk(func_node) if isinstance(node, ast.Return)]),  # Required field
            # Optional enhanced fields
            complexity_rank=cc_rank(complexity),
            loc=loc,
            lloc=lloc,
            sloc=sloc,
            comments=comments,
            halstead_n1=n1,
            halstead_n2=n2,
            halstead_N1=N1,
            halstead_N2=N2,
            parameters=len(func_node.args.args),
            returns=len([node for node in ast.walk(func_node) if isinstance(node, ast.Return)]),
            docstring=ast.get_docstring(func_node) or ""
        )
    except Exception as e:
        logger.debug(f"Error analyzing function {func_node.name}: {e}")
        return FunctionMetrics(
            name=func_node.name,
            file_path=file_path,
            line_start=func_node.lineno,
            line_end=func_node.lineno,
            cyclomatic_complexity=1,
            halstead_volume=0,  # Required field
            maintainability_index=100,  # Required field
            lines_of_code=1,  # Required field
            parameters_count=0,  # Required field
            return_statements=0,  # Required field
            # Optional enhanced fields
            complexity_rank="A",
            loc=1,
            lloc=1,
            sloc=1,
            comments=0,
            halstead_n1=0,
            halstead_n2=0,
            halstead_N1=0,
            halstead_N2=0,
            parameters=0,
            returns=0,
            docstring=""
        )


def analyze_function_graph_sitter(function, file_path: str) -> FunctionMetrics:
    """Analyze a function using Graph-Sitter (enhanced method)."""
    try:
        # Use enhanced graph-sitter complexity calculation
        complexity = calculate_cyclomatic_complexity_graph_sitter(function)
        
        # Get function source
        func_source = function.code_block.source if hasattr(function, 'code_block') else ""
        
        # Calculate line metrics
        loc, lloc, sloc, comments = count_lines(func_source)
        
        # Extract operators and operands using graph-sitter
        operators, operands = get_operators_and_operands(function)
        
        # Calculate Halstead metrics
        volume, n1, n2, N1, N2 = calculate_halstead_volume(operators, operands)
        
        # Calculate maintainability index
        maintainability = calculate_maintainability_index(volume, complexity, loc)
        
        # Get additional graph-sitter specific metrics
        parameters = len(function.parameters) if hasattr(function, 'parameters') else 0
        returns = len(function.return_statements) if hasattr(function, 'return_statements') else 0
        function_calls = len(function.function_calls) if hasattr(function, 'function_calls') else 0
        call_sites = len(function.call_sites) if hasattr(function, 'call_sites') else 0
        dependencies = len(function.dependencies) if hasattr(function, 'dependencies') else 0
        
        return FunctionMetrics(
            name=function.name,
            file_path=file_path,
            line_start=function.line_start if hasattr(function, 'line_start') else 0,
            line_end=function.line_end if hasattr(function, 'line_end') else 0,
            cyclomatic_complexity=complexity,
            halstead_volume=volume,  # Required field
            maintainability_index=maintainability,  # Required field
            lines_of_code=loc,  # Required field
            parameters_count=parameters,  # Required field
            return_statements=returns,  # Required field
            # Optional enhanced fields
            complexity_rank=cc_rank(complexity),
            loc=loc,
            lloc=lloc,
            sloc=sloc,
            comments=comments,
            halstead_n1=n1,
            halstead_n2=n2,
            halstead_N1=N1,
            halstead_N2=N2,
            parameters=parameters,
            returns=returns,
            docstring=function.docstring if hasattr(function, 'docstring') else "",
            # Additional graph-sitter metrics
            function_calls=function_calls,
            call_sites=call_sites,
            dependencies=dependencies
        )
    except Exception as e:
        logger.debug(f"Error analyzing function {function.name}: {e}")
        # Fallback to basic metrics
        return FunctionMetrics(
            name=function.name,
            file_path=file_path,
            line_start=0,
            line_end=0,
            cyclomatic_complexity=1,
            halstead_volume=0,  # Required field
            maintainability_index=100,  # Required field
            lines_of_code=1,  # Required field
            parameters_count=0,  # Required field
            return_statements=0,  # Required field
            # Optional enhanced fields
            complexity_rank="A",
            loc=1,
            lloc=1,
            sloc=1,
            comments=0,
            halstead_n1=0,
            halstead_n2=0,
            halstead_N1=0,
            halstead_N2=0,
            parameters=0,
            returns=0,
            docstring=""
        )

def analyze_class_ast(class_node: ast.ClassDef, file_path: str, source_lines: List[str]) -> ClassMetrics:
    """Analyze a class AST node and return comprehensive metrics."""
    try:
        # Basic info
        name = class_node.name
        line_start = class_node.lineno
        line_end = class_node.end_lineno or line_start
        
        # Calculate depth of inheritance
        doi = calculate_doi(class_node)
        
        # Count methods
        methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]
        method_count = len(methods)
        
        # Count attributes (assignments in class body)
        attributes = []
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
        
        # Extract class source
        class_source = '\n'.join(source_lines[line_start-1:line_end])
        loc, _, _, _ = count_lines(class_source)
        
        return ClassMetrics(
            name=name,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            depth_of_inheritance=doi,
            method_count=method_count,
            attribute_count=len(attributes),
            lines_of_code=loc,
            parent_classes=[base.id for base in class_node.bases if isinstance(base, ast.Name)]
        )
    except Exception as e:
        logger.warning(f"Error analyzing class {class_node.name}: {e}")
        return ClassMetrics(
            name=class_node.name,
            file_path=file_path,
            line_start=class_node.lineno,
            line_end=class_node.end_lineno or class_node.lineno,
            depth_of_inheritance=0,
            method_count=0,
            attribute_count=0,
            lines_of_code=0
        )


def analyze_class_graph_sitter(cls, file_path: str) -> ClassMetrics:
    """Analyze a class using Graph-Sitter (enhanced method)."""
    try:
        # Use enhanced graph-sitter DOI calculation
        doi = calculate_doi(cls)
        
        # Get class metrics
        method_count = len(cls.methods) if hasattr(cls, 'methods') else 0
        attribute_count = len(cls.attributes) if hasattr(cls, 'attributes') else 0
        
        # Get class source for line counting
        class_source = cls.source if hasattr(cls, 'source') else ""
        loc, _, _, _ = count_lines(class_source)
        
        # Get parent classes
        parent_classes = cls.parent_class_names if hasattr(cls, 'parent_class_names') else []
        
        return ClassMetrics(
            name=cls.name,
            file_path=file_path,
            line_start=cls.line_start if hasattr(cls, 'line_start') else 0,
            line_end=cls.line_end if hasattr(cls, 'line_end') else 0,
            depth_of_inheritance=doi,
            method_count=method_count,
            attribute_count=attribute_count,
            lines_of_code=loc,
            parent_classes=parent_classes
        )
    except Exception as e:
        logger.debug(f"Error analyzing class {cls.name}: {e}")
        return ClassMetrics(
            name=cls.name,
            file_path=file_path,
            line_start=0,
            line_end=0,
            depth_of_inheritance=0,
            method_count=0,
            attribute_count=0,
            lines_of_code=0
        )


# ============================================================================
# ISSUE DETECTION ENGINE
# ============================================================================

def detect_code_issues(tree: ast.AST, file_path: str, source_lines: List[str]) -> List[CodeIssue]:
    """Detect various code issues using AST analysis."""
    issues = []
    
    for node in ast.walk(tree):
        try:
            # High cyclomatic complexity
            if isinstance(node, ast.FunctionDef):
                complexity = calculate_cyclomatic_complexity(node)
                if complexity > 15:
                    issues.append(CodeIssue(
                        type="high_complexity",
                        severity="major",
                        message=f"Function '{node.name}' has high cyclomatic complexity ({complexity})",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno,
                        suggestion="Consider breaking this function into smaller functions",
                        rule_id="CC001"
                    ))
                elif complexity > 10:
                    issues.append(CodeIssue(
                        type="moderate_complexity",
                        severity="minor",
                        message=f"Function '{node.name}' has moderate complexity ({complexity})",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno,
                        suggestion="Consider simplifying this function",
                        rule_id="CC002"
                    ))
            
            # Long functions
            if isinstance(node, ast.FunctionDef):
                func_length = (node.end_lineno or node.lineno) - node.lineno + 1
                if func_length > 100:
                    issues.append(CodeIssue(
                        type="long_function",
                        severity="major",
                        message=f"Function '{node.name}' is very long ({func_length} lines)",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno,
                        suggestion="Consider breaking this function into smaller functions",
                        rule_id="LF001"
                    ))
                elif func_length > 50:
                    issues.append(CodeIssue(
                        type="long_function",
                        severity="minor",
                        message=f"Function '{node.name}' is long ({func_length} lines)",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno,
                        suggestion="Consider if this function can be simplified",
                        rule_id="LF002"
                    ))
            
            # Too many parameters
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > 7:
                    issues.append(CodeIssue(
                        type="too_many_parameters",
                        severity="major",
                        message=f"Function '{node.name}' has too many parameters ({param_count})",
                        file_path=file_path,
                        line_start=node.lineno,
                        suggestion="Consider using a configuration object or reducing parameters",
                        rule_id="TMP001"
                    ))
                elif param_count > 5:
                    issues.append(CodeIssue(
                        type="many_parameters",
                        severity="minor",
                        message=f"Function '{node.name}' has many parameters ({param_count})",
                        file_path=file_path,
                        line_start=node.lineno,
                        suggestion="Consider if parameters can be grouped",
                        rule_id="TMP002"
                    ))
            
            # Deep nesting
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                nesting_level = 0
                parent = node
                while hasattr(parent, 'parent'):
                    parent = parent.parent
                    if isinstance(parent, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                        nesting_level += 1
                
                if nesting_level > 4:
                    issues.append(CodeIssue(
                        type="deep_nesting",
                        severity="major",
                        message=f"Deep nesting detected (level {nesting_level})",
                        file_path=file_path,
                        line_start=node.lineno,
                        suggestion="Consider extracting nested logic into separate functions",
                        rule_id="DN001"
                    ))
            
            # Missing docstrings
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    severity = "minor" if isinstance(node, ast.FunctionDef) else "major"
                    issues.append(CodeIssue(
                        type="missing_docstring",
                        severity=severity,
                        message=f"{type(node).__name__[:-3]} '{node.name}' is missing a docstring",
                        file_path=file_path,
                        line_start=node.lineno,
                        suggestion="Add a docstring to document the purpose and usage",
                        rule_id="DOC001"
                    ))
            
            # Potential security issues
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec']:
                        issues.append(CodeIssue(
                            type="security_risk",
                            severity="critical",
                            message=f"Use of '{node.func.id}' function detected",
                            file_path=file_path,
                            line_start=node.lineno,
                            suggestion="Avoid using eval/exec as they can execute arbitrary code",
                            rule_id="SEC001"
                        ))
                    elif node.func.id == 'input' and len(node.args) == 0:
                        issues.append(CodeIssue(
                            type="security_risk",
                            severity="minor",
                            message="Use of 'input()' without prompt detected",
                            file_path=file_path,
                            line_start=node.lineno,
                            suggestion="Consider providing a clear prompt for user input",
                            rule_id="SEC002"
                        ))
        
        except Exception as e:
            logger.debug(f"Error detecting issues in node: {e}")
            continue
    
    # Check for long lines
    for i, line in enumerate(source_lines, 1):
        if len(line) > 120:
            issues.append(CodeIssue(
                type="long_line",
                severity="minor",
                message=f"Line too long ({len(line)} > 120 characters)",
                file_path=file_path,
                line_start=i,
                suggestion="Break line into multiple lines",
                rule_id="LL001"
            ))
    
    return issues

def detect_dead_code(tree: ast.AST, file_path: str, all_functions: Set[str], all_classes: Set[str]) -> List[DeadCodeItem]:
    """Detect potentially dead/unused code."""
    dead_code = []
    defined_functions = set()
    defined_classes = set()
    used_functions = set()
    used_classes = set()
    
    # Collect defined and used symbols
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined_functions.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_classes.add(node.name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                used_functions.add(node.func.id)
        elif isinstance(node, ast.Name):
            if node.id in all_functions:
                used_functions.add(node.id)
            elif node.id in all_classes:
                used_classes.add(node.id)
    
    # Find potentially unused functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if (node.name not in used_functions and 
                not node.name.startswith('_') and 
                node.name not in ['main', '__init__']):
                dead_code.append(DeadCodeItem(
                    type="function",
                    name=node.name,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    reason="Function is defined but never called",
                    confidence=0.8
                ))
        elif isinstance(node, ast.ClassDef):
            if (node.name not in used_classes and 
                not node.name.startswith('_')):
                dead_code.append(DeadCodeItem(
                    type="class",
                    name=node.name,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    reason="Class is defined but never instantiated",
                    confidence=0.7
                ))
    
    return dead_code


# ============================================================================
# COMPREHENSIVE ANALYSIS ENGINE
# ============================================================================

class ComprehensiveCodebaseAnalyzer:
    """Main analyzer class that orchestrates all analysis components."""
    
    def __init__(self, use_graph_sitter: bool = True):
        self.use_graph_sitter = use_graph_sitter and GRAPH_SITTER_AVAILABLE
        self.all_functions = set()
        self.all_classes = set()
        self.dependency_graph = defaultdict(list)
        self.usage_patterns = defaultdict(int)
        
    def analyze_file(self, file_path: str) -> FileAnalysis:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            if not source.strip():
                return self._empty_file_analysis(file_path)
            
            # Parse AST
            try:
                tree = ast.parse(source)
            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {e}")
                return self._error_file_analysis(file_path, str(e))
            
            source_lines = source.splitlines()
            
            # Calculate line metrics
            loc, lloc, sloc, comments = count_lines(source)
            comment_density = (comments / loc * 100) if loc > 0 else 0
            
            # Analyze functions and classes
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_metrics = analyze_function_ast(node, file_path, source_lines)
                    functions.append(func_metrics)
                    self.all_functions.add(node.name)
                    
                    # Build dependency graph
                    for dep in func_metrics.dependencies:
                        self.dependency_graph[node.name].append(dep)
                        self.usage_patterns[dep] += 1
                
                elif isinstance(node, ast.ClassDef):
                    class_metrics = analyze_class_ast(node, file_path, source_lines)
                    classes.append(class_metrics)
                    self.all_classes.add(node.name)
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    else:
                        module = node.module or ""
                        for alias in node.names:
                            imports.append(f"{module}.{alias.name}")
            
            # Detect issues
            issues = detect_code_issues(tree, file_path, source_lines)
            
            # Calculate complexity score
            complexity_score = self._calculate_file_complexity(functions, classes, issues)
            
            return FileAnalysis(
                file_path=file_path,
                lines_of_code=loc,
                logical_lines=lloc,
                source_lines=sloc,
                comment_lines=comments,
                comment_density=comment_density,
                functions=functions,
                classes=classes,
                issues=issues,
                imports=imports,
                complexity_score=complexity_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return self._error_file_analysis(file_path, str(e))
    
    def _empty_file_analysis(self, file_path: str) -> FileAnalysis:
        """Return analysis for empty file."""
        return FileAnalysis(
            file_path=file_path,
            lines_of_code=0,
            logical_lines=0,
            source_lines=0,
            comment_lines=0,
            comment_density=0
        )
    
    def _error_file_analysis(self, file_path: str, error: str) -> FileAnalysis:
        """Return analysis for file with errors."""
        return FileAnalysis(
            file_path=file_path,
            lines_of_code=0,
            logical_lines=0,
            source_lines=0,
            comment_lines=0,
            comment_density=0,
            issues=[CodeIssue(
                type="parse_error",
                severity="critical",
                message=f"Failed to parse file: {error}",
                file_path=file_path,
                line_start=1
            )]
        )
    
    def _calculate_file_complexity(self, functions: List[FunctionMetrics], 
                                 classes: List[ClassMetrics], 
                                 issues: List[CodeIssue]) -> float:
        """Calculate overall complexity score for a file."""
        if not functions and not classes:
            return 0.0
        
        # Average function complexity
        func_complexity = sum(f.cyclomatic_complexity for f in functions) / len(functions) if functions else 0
        
        # Class complexity (based on methods and inheritance)
        class_complexity = sum(c.method_count + c.depth_of_inheritance for c in classes) / len(classes) if classes else 0
        
        # Issue penalty
        issue_penalty = len([i for i in issues if i.severity in ['critical', 'major']]) * 0.5
        
        return func_complexity + class_complexity + issue_penalty
    
    def analyze_codebase(self, path: str, extensions: List[str] = None) -> ComprehensiveAnalysisResult:
        """Analyze entire codebase."""
        start_time = time.time()
        
        if extensions is None:
            extensions = ['.py']
        
        # Use graph-sitter if available
        if self.use_graph_sitter:
            try:
                return self._analyze_with_graph_sitter(path)
            except Exception as e:
                logger.warning(f"Graph-sitter analysis failed: {e}. Falling back to AST analysis.")
        
        # Fallback to AST analysis
        return self._analyze_with_ast(path, extensions, start_time)
    
    def _analyze_with_graph_sitter(self, path: str) -> ComprehensiveAnalysisResult:
        """Analyze using graph-sitter (enhanced analysis)."""
        if os.path.isfile(path):
            codebase = Codebase.from_directory(os.path.dirname(path))
        else:
            codebase = Codebase.from_directory(path)
        
        start_time = time.time()
        
        # Get basic metrics from graph-sitter
        files = list(codebase.files)
        functions = list(codebase.functions)
        classes = list(codebase.classes)
        
        logger.info(f"Graph-sitter loaded: {len(files)} files, {len(functions)} functions, {len(classes)} classes")
        
        # Enhanced analysis using graph-sitter capabilities
        function_metrics = []
        class_metrics = []
        all_issues = []
        all_dead_code = []
        
        # Analyze functions using enhanced graph-sitter analysis
        for function in functions:
            try:
                metrics = analyze_function_graph_sitter(function, function.filepath)
                function_metrics.append(metrics)
                
                # Add issues based on metrics
                if metrics.cyclomatic_complexity > 10:
                    all_issues.append(CodeIssue(
                        type="high_complexity",
                        severity="major",
                        message=f"High cyclomatic complexity ({metrics.cyclomatic_complexity})",
                        file_path=metrics.file_path,
                        line_start=metrics.line_start,
                        line_end=metrics.line_end,
                        suggestion=f"Consider breaking down this function (complexity: {metrics.cyclomatic_complexity}, rank: {metrics.complexity_rank})"
                    ))
                
                if metrics.maintainability_index < 20:
                    all_issues.append(CodeIssue(
                        type="low_maintainability",
                        severity="major",
                        message=f"Low maintainability index ({metrics.maintainability_index})",
                        file_path=metrics.file_path,
                        line_start=metrics.line_start,
                        line_end=metrics.line_end,
                        suggestion="Improve code structure and reduce complexity"
                    ))
                    
            except Exception as e:
                logger.debug(f"Error analyzing function {function.name}: {e}")
        
        # Analyze classes using enhanced graph-sitter analysis
        for cls in classes:
            try:
                metrics = analyze_class_graph_sitter(cls, cls.filepath)
                class_metrics.append(metrics)
                
                # Add issues based on metrics
                if metrics.depth_of_inheritance > 5:
                    all_issues.append(CodeIssue(
                        type="deep_inheritance",
                        severity="minor",
                        message=f"Deep inheritance hierarchy (depth: {metrics.depth_of_inheritance})",
                        file_path=metrics.file_path,
                        line_start=metrics.line_start,
                        line_end=metrics.line_end,
                        suggestion="Consider composition over inheritance"
                    ))
                    
            except Exception as e:
                logger.debug(f"Error analyzing class {cls.name}: {e}")
        
        # Use graph-sitter's codebase analysis for additional insights
        try:
            codebase_summary = get_codebase_summary(codebase)
            logger.info(f"Codebase summary: {codebase_summary}")
        except Exception as e:
            logger.debug(f"Error getting codebase summary: {e}")
        
        # Detect dead code using graph-sitter symbol usage
        for function in functions:
            try:
                # Check if function has no usages (potential dead code)
                if hasattr(function, 'symbol_usages') and len(function.symbol_usages) == 0:
                    all_dead_code.append(DeadCodeItem(
                        type="function",
                        name=function.name,
                        file_path=function.filepath,
                        line_start=function.line_start if hasattr(function, 'line_start') else 0,
                        line_end=function.line_end if hasattr(function, 'line_end') else 0,
                        reason="Function is defined but never called",
                        confidence=0.8
                    ))
            except Exception as e:
                logger.debug(f"Error checking dead code for {function.name}: {e}")
        
        # Calculate aggregate metrics
        total_files = len(files)
        total_functions = len(function_metrics)
        total_classes = len(class_metrics)
        
        # Calculate averages
        avg_complexity = sum(f.cyclomatic_complexity for f in function_metrics) / len(function_metrics) if function_metrics else 0
        avg_maintainability = sum(f.maintainability_index for f in function_metrics) / len(function_metrics) if function_metrics else 100
        avg_doi = sum(c.depth_of_inheritance for c in class_metrics) / len(class_metrics) if class_metrics else 0
        
        # Calculate technical debt ratio
        high_complexity_functions = len([f for f in function_metrics if f.cyclomatic_complexity > 10])
        technical_debt_ratio = high_complexity_functions / total_functions if total_functions > 0 else 0
        
        # Create file analyses from graph-sitter data
        file_analyses = []
        for file in files:
            if file.name.endswith('.py'):
                file_functions = [f for f in function_metrics if f.file_path == file.path]
                file_classes = [c for c in class_metrics if c.file_path == file.path]
                file_issues = [i for i in all_issues if i.file_path == file.path]
                
                # Calculate file metrics
                total_loc = sum(f.loc for f in file_functions) + sum(c.lines_of_code for c in file_classes)
                
                file_analysis = FileAnalysis(
                    file_path=file.path,
                    lines_of_code=total_loc,
                    functions=file_functions,
                    classes=file_classes,
                    issues=file_issues,
                    imports=[],  # Could be enhanced with graph-sitter import analysis
                    exports=[]   # Could be enhanced with graph-sitter export analysis
                )
                file_analyses.append(file_analysis)
        
        processing_time = time.time() - start_time
        
        return ComprehensiveAnalysisResult(
            total_files=total_files,
            total_functions=total_functions,
            total_classes=total_classes,
            function_metrics=function_metrics,
            class_metrics=class_metrics,
            issues=all_issues,
            dead_code_items=all_dead_code,
            file_analyses=file_analyses,
            average_complexity=avg_complexity,
            average_maintainability=avg_maintainability,
            average_doi=avg_doi,
            technical_debt_ratio=technical_debt_ratio,
            test_coverage_estimate=0.0,  # Could be enhanced with test detection
            processing_time=processing_time,
            analysis_method="graph-sitter-enhanced"
        )


    def _analyze_with_ast(self, path: str, extensions: List[str], start_time: float) -> ComprehensiveAnalysisResult:
        """Analyze using pure AST (fallback method)."""
        python_files = []
        
        if os.path.isfile(path):
            if path.endswith('.py'):
                python_files = [path]
        else:
            for root, dirs, files in os.walk(path):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        python_files.append(os.path.join(root, file))
        
        # Analyze each file
        file_analyses = []
        all_issues = []
        all_dead_code = []
        
        for file_path in python_files:
            file_analysis = self.analyze_file(file_path)
            file_analyses.append(file_analysis)
            all_issues.extend(file_analysis.issues)
        
        # Detect dead code across all files
        for file_analysis in file_analyses:
            try:
                with open(file_analysis.file_path, 'r') as f:
                    source = f.read()
                tree = ast.parse(source)
                dead_code = detect_dead_code(tree, file_analysis.file_path, 
                                           self.all_functions, self.all_classes)
                all_dead_code.extend(dead_code)
            except:
                continue
        
        # Calculate aggregate metrics (same as graph-sitter method)
        total_files = len(file_analyses)
        total_functions = sum(len(f.functions) for f in file_analyses)
        total_classes = sum(len(f.classes) for f in file_analyses)
        total_lines = sum(f.lines_of_code for f in file_analyses)
        total_logical_lines = sum(f.logical_lines for f in file_analyses)
        total_source_lines = sum(f.source_lines for f in file_analyses)
        total_comment_lines = sum(f.comment_lines for f in file_analyses)
        
        # Calculate quality metrics
        all_function_metrics = [f for fa in file_analyses for f in fa.functions]
        all_class_metrics = [c for fa in file_analyses for c in fa.classes]
        
        avg_maintainability = (sum(f.maintainability_index for f in all_function_metrics) / 
                             len(all_function_metrics)) if all_function_metrics else 0
        avg_complexity = (sum(f.cyclomatic_complexity for f in all_function_metrics) / 
                         len(all_function_metrics)) if all_function_metrics else 0
        avg_halstead = (sum(f.halstead_volume for f in all_function_metrics) / 
                       len(all_function_metrics)) if all_function_metrics else 0
        avg_doi = (sum(c.depth_of_inheritance for c in all_class_metrics) / 
                  len(all_class_metrics)) if all_class_metrics else 0
        
        comment_density = (total_comment_lines / total_lines * 100) if total_lines > 0 else 0
        
        # Calculate technical debt ratio
        critical_issues = len([i for i in all_issues if i.severity == 'critical'])
        major_issues = len([i for i in all_issues if i.severity == 'major'])
        technical_debt_ratio = (critical_issues * 0.3 + major_issues * 0.1) / total_files if total_files > 0 else 0
        
        # Build inheritance hierarchy
        inheritance_hierarchy = self._build_inheritance_hierarchy(all_class_metrics)
        
        # Performance metrics
        analysis_time = time.time() - start_time
        files_per_second = total_files / analysis_time if analysis_time > 0 else 0
        
        return ComprehensiveAnalysisResult(
            total_files=total_files,
            total_functions=total_functions,
            total_classes=total_classes,
            total_lines=total_lines,
            total_logical_lines=total_logical_lines,
            total_source_lines=total_source_lines,
            total_comment_lines=total_comment_lines,
            average_maintainability_index=avg_maintainability,
            average_cyclomatic_complexity=avg_complexity,
            average_halstead_volume=avg_halstead,
            average_depth_of_inheritance=avg_doi,
            comment_density=comment_density,
            technical_debt_ratio=technical_debt_ratio,
            files=file_analyses,
            issues=all_issues,
            dead_code_items=all_dead_code,
            function_metrics=all_function_metrics,
            class_metrics=all_class_metrics,
            top_level_functions=[f.name for f in all_function_metrics],
            top_level_classes=[c.name for c in all_class_metrics],
            inheritance_hierarchy=inheritance_hierarchy,
            dependency_graph=dict(self.dependency_graph),
            usage_patterns=dict(self.usage_patterns),
            analysis_time=analysis_time,
            files_per_second=files_per_second
        )
    
    def _build_inheritance_hierarchy(self, class_metrics: List[ClassMetrics]) -> Dict[str, Any]:
        """Build inheritance hierarchy from class metrics."""
        hierarchy = {}
        
        for class_metric in class_metrics:
            hierarchy[class_metric.name] = {
                'file_path': class_metric.file_path,
                'line_start': class_metric.line_start,
                'parent_classes': class_metric.parent_classes,
                'depth': class_metric.depth_of_inheritance,
                'method_count': class_metric.method_count,
                'attribute_count': class_metric.attribute_count
            }
        
        # Add child relationships
        for class_name, info in hierarchy.items():
            info['child_classes'] = []
            for other_class, other_info in hierarchy.items():
                if class_name in other_info['parent_classes']:
                    info['child_classes'].append(other_class)
        
        return hierarchy


# ============================================================================
# OUTPUT FORMATTING AND VISUALIZATION
# ============================================================================

def format_analysis_results(result: ComprehensiveAnalysisResult, format_type: str = "text") -> str:
    """Format analysis results for display."""
    if format_type == "json":
        return json.dumps(result.to_dict(), indent=2, default=str)
    
    # Text format with enhanced visualization
    output = []
    
    # Header
    output.append("🚀 COMPREHENSIVE CODEBASE ANALYSIS RESULTS 🚀")
    output.append("=" * 80)
    
    # Performance metrics
    output.append(f"⚡ Analysis completed in {result.analysis_time:.2f}s ({result.files_per_second:.1f} files/sec)")
    output.append("")
    
    # Summary metrics
    output.append("📊 SUMMARY METRICS:")
    output.append(f"  • Total Files: {result.total_files:,}")
    output.append(f"  • Total Functions: {result.total_functions:,}")
    output.append(f"  • Total Classes: {result.total_classes:,}")
    output.append(f"  • Total Lines: {result.total_lines:,}")
    output.append(f"  • Logical Lines: {result.total_logical_lines:,}")
    output.append(f"  • Source Lines: {result.total_source_lines:,}")
    output.append(f"  • Comment Lines: {result.total_comment_lines:,}")
    output.append("")
    
    # Quality metrics
    output.append("🎯 QUALITY METRICS:")
    output.append(f"  • Average Maintainability Index: {result.average_maintainability_index:.1f}/100")
    output.append(f"  • Average Cyclomatic Complexity: {result.average_cyclomatic_complexity:.1f}")
    output.append(f"  • Average Halstead Volume: {result.average_halstead_volume:.1f}")
    output.append(f"  • Average Depth of Inheritance: {result.average_depth_of_inheritance:.1f}")
    output.append(f"  • Comment Density: {result.comment_density:.1f}%")
    output.append(f"  • Technical Debt Ratio: {result.technical_debt_ratio:.3f}")
    output.append("")
    
    # Top-level symbols
    if result.top_level_functions:
        output.append("������ TOP-LEVEL FUNCTIONS:")
        for i, func in enumerate(result.top_level_functions[:10], 1):
            output.append(f"  {i:2d}. {func}")
        if len(result.top_level_functions) > 10:
            output.append(f"     ... and {len(result.top_level_functions) - 10} more")
        output.append("")
    
    if result.top_level_classes:
        output.append("🏗️ TOP-LEVEL CLASSES:")
        for i, cls in enumerate(result.top_level_classes[:10], 1):
            output.append(f"  {i:2d}. {cls}")
        if len(result.top_level_classes) > 10:
            output.append(f"     ... and {len(result.top_level_classes) - 10} more")
        output.append("")
    
    # Issues summary
    if result.issues:
        issues_by_severity = defaultdict(list)
        for issue in result.issues:
            issues_by_severity[issue.severity].append(issue)
        
        output.append("⚠️ ISSUES DETECTED:")
        output.append(f"  • Total Issues: {len(result.issues)}")
        
        for severity in ['critical', 'major', 'minor', 'info']:
            if severity in issues_by_severity:
                count = len(issues_by_severity[severity])
                emoji = {'critical': '🔴', 'major': '🟡', 'minor': '🔵', 'info': '⚪'}[severity]
                output.append(f"  {emoji} {severity.title()}: {count}")
        
        output.append("")
        
        # Show top issues
        critical_issues = issues_by_severity.get('critical', [])
        major_issues = issues_by_severity.get('major', [])
        top_issues = critical_issues[:3] + major_issues[:3]
        
        if top_issues:
            output.append("🔍 TOP ISSUES:")
            for i, issue in enumerate(top_issues, 1):
                severity_emoji = {'critical': '🔴', 'major': '🟡', 'minor': '🔵', 'info': '⚪'}[issue.severity]
                output.append(f"  {i}. {severity_emoji} {issue.type}: {issue.message}")
                output.append(f"     📍 {issue.file_path}:{issue.line_start}")
                if issue.suggestion:
                    output.append(f"     💡 {issue.suggestion}")
            output.append("")
    
    # Dead code
    if result.dead_code_items:
        output.append("💀 DEAD CODE DETECTED:")
        output.append(f"  • Total Dead Code Items: {len(result.dead_code_items)}")
        
        for i, item in enumerate(result.dead_code_items[:5], 1):
            confidence_emoji = "���" if item.confidence > 0.8 else "🟡" if item.confidence > 0.6 else "🔵"
            output.append(f"  {i}. {confidence_emoji} {item.type.title()}: {item.name}")
            output.append(f"     📍 {item.file_path}:{item.line_start}-{item.line_end}")
            output.append(f"     📝 {item.reason} (confidence: {item.confidence:.0%})")
        
        if len(result.dead_code_items) > 5:
            output.append(f"     ... and {len(result.dead_code_items) - 5} more")
        output.append("")
    
    # Inheritance hierarchy
    if result.inheritance_hierarchy:
        output.append("🏗️ INHERITANCE HIERARCHY:")
        hierarchy_items = list(result.inheritance_hierarchy.items())[:10]
        for class_name, info in hierarchy_items:
            depth_indent = "  " * (info.get('depth', 0) + 1)
            output.append(f"{depth_indent}📦 {class_name}")
            output.append(f"{depth_indent}   📍 {info.get('file_path', 'Unknown')}:{info.get('line_start', 0)}")
            if info.get('parent_classes'):
                output.append(f"{depth_indent}   ⬆️ Parents: {', '.join(info['parent_classes'])}")
            if info.get('child_classes'):
                output.append(f"{depth_indent}   ⬇️ Children: {', '.join(info['child_classes'])}")
        
        if len(result.inheritance_hierarchy) > 10:
            output.append(f"  ... and {len(result.inheritance_hierarchy) - 10} more classes")
        output.append("")
    
    # Dependency patterns
    if result.usage_patterns:
        output.append("🔗 MOST USED DEPENDENCIES:")
        sorted_patterns = sorted(result.usage_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (dep, count) in enumerate(sorted_patterns, 1):
            output.append(f"  {i:2d}. {dep} (used {count} times)")
        output.append("")
    
    # Files with most issues
    files_with_issues = defaultdict(int)
    for issue in result.issues:
        files_with_issues[issue.file_path] += 1
    
    if files_with_issues:
        output.append("📁 FILES WITH MOST ISSUES:")
        sorted_files = sorted(files_with_issues.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (file_path, count) in enumerate(sorted_files, 1):
            output.append(f"  {i}. {file_path} ({count} issues)")
        output.append("")
    
    # Complexity distribution
    if result.function_metrics:
        complexity_distribution = Counter()
        for func in result.function_metrics:
            rank = cc_rank(func.cyclomatic_complexity)
            complexity_distribution[rank] += 1
        
        output.append("📈 COMPLEXITY DISTRIBUTION:")
        for rank in ['A', 'B', 'C', 'D', 'E', 'F']:
            if rank in complexity_distribution:
                count = complexity_distribution[rank]
                percentage = count / len(result.function_metrics) * 100
                bar = "█" * int(percentage / 5)  # Scale bar
                output.append(f"  {rank}: {count:3d} functions ({percentage:4.1f}%) {bar}")
        output.append("")
    
    # Footer
    output.append("=" * 80)
    output.append("🎉 Analysis Complete! Use --format json for machine-readable output.")
    
    return "\n".join(output)

def save_analysis_results(result: ComprehensiveAnalysisResult, output_path: str, format_type: str = "text"):
    """Save analysis results to file."""
    try:
        content = format_analysis_results(result, format_type)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Analysis results saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving results to {output_path}: {e}")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="🚀 Comprehensive Codebase Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s .                              # Analyze current directory
  %(prog)s /path/to/project               # Analyze specific directory
  %(prog)s --repo fastapi/fastapi         # Analyze remote repository
  %(prog)s . --format json               # Output as JSON
  %(prog)s . --output results.txt        # Save to file
  %(prog)s . --comprehensive             # Full analysis with all features
  %(prog)s . --no-graph-sitter           # Use AST-only analysis
  %(prog)s . --extensions .py .pyx       # Analyze specific file types
        """
    )
    
    # Input options
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to analyze (directory or file, default: current directory)"
    )
    
    parser.add_argument(
        "--repo",
        help="Analyze remote repository (format: owner/repo)"
    )
    
    parser.add_argument(
        "--repo-analytics",
        action="store_true",
        help="Run repository analytics mode (requires --repo, from repo_analytics example)"
    )
    
    # Analysis options
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Enable comprehensive analysis with all features"
    )
    
    parser.add_argument(
        "--no-graph-sitter",
        action="store_true",
        help="Disable graph-sitter integration (use AST-only analysis)"
    )
    
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".py"],
        help="File extensions to analyze (default: .py)"
    )
    
    # Output options
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file path (default: stdout)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except results"
    )
    
    return parser

def main():
    """Main entry point with enhanced graph-sitter features."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Configure logging
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    try:
        # Handle enhanced graph-sitter analysis modes
        if GRAPH_SITTER_AVAILABLE and any([
            getattr(args, "training_data", False),
            getattr(args, "import_loops", False),
            getattr(args, "dead_code", False),
            getattr(args, "graph_analysis", False),
            getattr(args, "enhanced_metrics", False)
        ]):
            # Use enhanced analyzer for graph-sitter specific features
            enhanced_analyzer = EnhancedCodebaseAnalyzer(
                use_advanced_config=getattr(args, "advanced_config", False)
            )
            
            # Determine analysis path
            if args.repo:
                # For repo analysis, we need to handle it differently
                analysis_path = args.repo
                logger.info(f"Analyzing remote repository: {args.repo}")
            else:
                analysis_path = os.path.abspath(args.path)
                if not os.path.exists(analysis_path):
                    logger.error(f"Path does not exist: {analysis_path}")
                    sys.exit(1)
                logger.info(f"Analyzing local path: {analysis_path}")
            
            results = {}
            
            # Training data generation
            if getattr(args, "training_data", False):
                logger.info("Generating training data for LLMs...")
                training_results = enhanced_analyzer.analyze_training_data(analysis_path)
                results["training_data"] = training_results
            
            # Import loop detection
            if getattr(args, "import_loops", False):
                logger.info("Detecting circular import dependencies...")
                import_results = enhanced_analyzer.analyze_import_loops(analysis_path)
                results["import_loops"] = import_results
            
            # Dead code detection
            if getattr(args, "dead_code", False):
                logger.info("Detecting unused code...")
                dead_code_results = enhanced_analyzer.analyze_dead_code(analysis_path)
                results["dead_code"] = dead_code_results
            
            # Graph structure analysis
            if getattr(args, "graph_analysis", False):
                logger.info("Analyzing graph structure...")
                graph_results = enhanced_analyzer.analyze_graph_structure(analysis_path)
                results["graph_analysis"] = graph_results
            
            # Enhanced metrics
            if getattr(args, "enhanced_metrics", False):
                logger.info("Generating enhanced metrics...")
                metrics_results = enhanced_analyzer.analyze_enhanced_metrics(analysis_path)
                results["enhanced_metrics"] = metrics_results
            
            # If no specific analysis requested, do comprehensive enhanced analysis
            if not results:
                logger.info("Running comprehensive enhanced analysis...")
                results = enhanced_analyzer.analyze_codebase_enhanced(analysis_path, args.extensions)
            
            # Output results
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)
                if not args.quiet:
                    print(f"✅ Enhanced analysis complete! Results saved to {args.output}")
            else:
                print(json.dumps(results, indent=2))
            
            sys.exit(0)
        
        # Handle repo analytics mode (from repo_analytics example)
        if args.repo and hasattr(args, "repo_analytics") and args.repo_analytics:
            if not GRAPH_SITTER_AVAILABLE:
                logger.error("Graph-sitter is required for repository analytics")
                sys.exit(1)
            
            logger.info(f"Running repository analytics for: {args.repo}")
            results = analyze_repo(args.repo)
            
            # Format repo analytics output (from repo_analytics example)
            print("\n📊 Repository Analysis Report 📊")
            print("=" * 50)
            print(f"📁 Repository: {results["repo_url"]}")
            print(f"📝 Description: {results["description"]}")
            print("\n📈 Basic Metrics:")
            print(f"  • Files: {results["num_files"]}")
            print(f"  • Functions: {results["num_functions"]}")
            print(f"  • Classes: {results["num_classes"]}")

            print("\n📏 Line Metrics:")
            line_metrics = results["line_metrics"]["total"]
            print(f"  • Lines of Code: {line_metrics["loc"]:,}")
            print(f"  • Logical Lines: {line_metrics["lloc"]:,}")
            print(f"  • Source Lines: {line_metrics["sloc"]:,}")
            print(f"  • Comments: {line_metrics["comments"]:,}")
            print(f"  • Comment Density: {line_metrics["comment_density"]:.1f}%")

            print("\n🔄 Complexity Metrics:")
            print(f"  • Average Cyclomatic Complexity: {results["cyclomatic_complexity"]["average"]:.1f}")
            print(f"  • Average Maintainability Index: {results["maintainability_index"]["average"]}")
            print(f"  • Average Depth of Inheritance: {results["depth_of_inheritance"]["average"]:.1f}")
            print(f"  • Total Halstead Volume: {results["halstead_metrics"]["total_volume"]:,}")
            print(f"  • Average Halstead Volume: {results["halstead_metrics"]["average_volume"]:,}")
            
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"\n💾 Results saved to: {args.output}")
            
            return
        
        # Determine analysis path for traditional analysis
        if args.repo:
            if GRAPH_SITTER_AVAILABLE:
                try:
                    codebase = Codebase.from_repo(args.repo)
                    analysis_path = codebase.path
                    logger.info(f"Analyzing remote repository: {args.repo}")
                except Exception as e:
                    logger.error(f"Failed to load repository {args.repo}: {e}")
                    sys.exit(1)
            else:
                logger.error("Graph-sitter is required for remote repository analysis")
                sys.exit(1)
        else:
            analysis_path = os.path.abspath(args.path)
            if not os.path.exists(analysis_path):
                logger.error(f"Path does not exist: {analysis_path}")
                sys.exit(1)
            logger.info(f"Analyzing local path: {analysis_path}")
        
        # Initialize analyzer
        use_graph_sitter = not args.no_graph_sitter
        analyzer = ComprehensiveCodebaseAnalyzer(use_graph_sitter=use_graph_sitter)
        
        if use_graph_sitter and GRAPH_SITTER_AVAILABLE:
            logger.info("Using graph-sitter enhanced analysis")
        else:
            logger.info("Using AST-based analysis")
        
        # Run analysis
        logger.info("Starting comprehensive codebase analysis...")
        result = analyzer.analyze_codebase(analysis_path, args.extensions)
        
        # Format and output results
        formatted_output = format_analysis_results(result, args.format)
        
        if args.output:
            save_analysis_results(result, args.output, args.format)
            if not args.quiet:
                print(f"✅ Analysis complete! Results saved to {args.output}")
        else:
            print(formatted_output)
        
        # Exit with appropriate code based on issues found
        critical_issues = len([i for i in result.issues if i.severity == "critical"])
        major_issues = len([i for i in result.issues if i.severity == "major"])
        
        if critical_issues > 0:
            sys.exit(2)  # Critical issues found
        elif major_issues > 0:
            sys.exit(1)  # Major issues found
        else:
            sys.exit(0)  # Success
            
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
            
            logger.info(f"Running repository analytics for: {args.repo}")
            results = analyze_repo(args.repo)
            
            # Format repo analytics output (from repo_analytics example)
            print("\n📊 Repository Analysis Report 📊")
            print("=" * 50)
            print(f"📁 Repository: {results['repo_url']}")
            print(f"📝 Description: {results['description']}")
            print("\n📈 Basic Metrics:")
            print(f"  • Files: {results['num_files']}")
            print(f"  • Functions: {results['num_functions']}")
            print(f"  • Classes: {results['num_classes']}")

            print("\n📏 Line Metrics:")
            line_metrics = results["line_metrics"]["total"]
            print(f"  ��� Lines of Code: {line_metrics['loc']:,}")
            print(f"  • Logical Lines: {line_metrics['lloc']:,}")
            print(f"  • Source Lines: {line_metrics['sloc']:,}")
            print(f"  • Comments: {line_metrics['comments']:,}")
            print(f"  • Comment Density: {line_metrics['comment_density']:.1f}%")

            print("\n🔄 Complexity Metrics:")
            print(f"  • Average Cyclomatic Complexity: {results['cyclomatic_complexity']['average']:.1f}")
            print(f"  • Average Maintainability Index: {results['maintainability_index']['average']}")
            print(f"  • Average Depth of Inheritance: {results['depth_of_inheritance']['average']:.1f}")
            print(f"  • Total Halstead Volume: {results['halstead_metrics']['total_volume']:,}")
            print(f"  • Average Halstead Volume: {results['halstead_metrics']['average_volume']:,}")
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\n💾 Results saved to: {args.output}")
            
            return
        
        # Determine analysis path
        if args.repo:
            if GRAPH_SITTER_AVAILABLE:
                try:
                    codebase = Codebase.from_repo(args.repo)
                    analysis_path = codebase.path
                    logger.info(f"Analyzing remote repository: {args.repo}")
                except Exception as e:
                    logger.error(f"Failed to load repository {args.repo}: {e}")
                    sys.exit(1)
            else:
                logger.error("Graph-sitter is required for remote repository analysis")
                sys.exit(1)
        else:
            analysis_path = os.path.abspath(args.path)
            if not os.path.exists(analysis_path):
                logger.error(f"Path does not exist: {analysis_path}")
                sys.exit(1)
            logger.info(f"Analyzing local path: {analysis_path}")
        
        # Initialize analyzer
        use_graph_sitter = not args.no_graph_sitter
        analyzer = ComprehensiveCodebaseAnalyzer(use_graph_sitter=use_graph_sitter)
        
        if use_graph_sitter and GRAPH_SITTER_AVAILABLE:
            logger.info("Using graph-sitter enhanced analysis")
        else:
            logger.info("Using AST-based analysis")
        
        # Run analysis
        logger.info("Starting comprehensive codebase analysis...")
        result = analyzer.analyze_codebase(analysis_path, args.extensions)
        
        # Format and output results
        formatted_output = format_analysis_results(result, args.format)
        
        if args.output:
            save_analysis_results(result, args.output, args.format)
            if not args.quiet:
                print(f"✅ Analysis complete! Results saved to {args.output}")
        else:
            print(formatted_output)
        
        # Exit with appropriate code based on issues found
        critical_issues = len([i for i in result.issues if i.severity == 'critical'])
        major_issues = len([i for i in result.issues if i.severity == 'major'])
        
        if critical_issues > 0:
            sys.exit(2)  # Critical issues found
        elif major_issues > 0:
            sys.exit(1)  # Major issues found
        else:
            sys.exit(0)  # Success
            
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

# ============================================================================
# CONVENIENCE FUNCTIONS FOR INTEGRATION
# ============================================================================

def analyze_codebase(path: str, use_graph_sitter: bool = True) -> ComprehensiveAnalysisResult:
    """Convenience function for programmatic use."""
    analyzer = ComprehensiveCodebaseAnalyzer(use_graph_sitter=use_graph_sitter)
    return analyzer.analyze_codebase(path)

def analyze_from_repo(repo_url: str) -> ComprehensiveAnalysisResult:
    """Analyze a remote repository."""
    if not GRAPH_SITTER_AVAILABLE:
        raise ImportError("Graph-sitter is required for remote repository analysis")
    
    codebase = Codebase.from_repo(repo_url)
    analyzer = ComprehensiveCodebaseAnalyzer(use_graph_sitter=True)
    return analyzer.analyze_codebase(codebase.path)


def analyze_repo(repo_url: str) -> Dict[str, Any]:
    """Analyze a repository and return comprehensive metrics (from repo_analytics)."""
    if not GRAPH_SITTER_AVAILABLE:
        raise ImportError("Graph-sitter is required for repository analysis")
    
    codebase = Codebase.from_repo(repo_url)

    num_files = len(codebase.files(extensions="*"))
    num_functions = len(codebase.functions)
    num_classes = len(codebase.classes)

    total_loc = total_lloc = total_sloc = total_comments = 0
    total_complexity = 0
    total_volume = 0
    total_mi = 0
    total_doi = 0

    # Analyze all files for line metrics
    for file in codebase.files:
        try:
            loc, lloc, sloc, comments = count_lines(file.source)
            total_loc += loc
            total_lloc += lloc
            total_sloc += sloc
            total_comments += comments
        except Exception as e:
            logger.debug(f"Error analyzing file {file.name}: {e}")

    # Analyze functions and methods
    callables = list(codebase.functions) + [m for c in codebase.classes for m in c.methods]

    num_callables = 0
    for func in callables:
        try:
            if not hasattr(func, "code_block"):
                continue

            complexity = calculate_cyclomatic_complexity_graph_sitter(func)
            operators, operands = get_operators_and_operands(func)
            volume, _, _, _, _ = calculate_halstead_volume(operators, operands)
            loc = len(func.code_block.source.splitlines()) if hasattr(func.code_block, 'source') else 0
            mi_score = calculate_maintainability_index(volume, complexity, loc)

            total_complexity += complexity
            total_volume += volume
            total_mi += mi_score
            num_callables += 1
        except Exception as e:
            logger.debug(f"Error analyzing callable {func.name}: {e}")

    # Analyze classes for depth of inheritance
    for cls in codebase.classes:
        try:
            doi = calculate_doi(cls)
            total_doi += doi
        except Exception as e:
            logger.debug(f"Error analyzing class {cls.name}: {e}")

    # Get repository description (if available)
    try:
        import requests
        api_url = f"https://api.github.com/repos/{repo_url}"
        response = requests.get(api_url)
        if response.status_code == 200:
            repo_data = response.json()
            desc = repo_data.get("description", "No description available")
        else:
            desc = ""
    except Exception:
        desc = ""

    results = {
        "repo_url": repo_url,
        "line_metrics": {
            "total": {
                "loc": total_loc,
                "lloc": total_lloc,
                "sloc": total_sloc,
                "comments": total_comments,
                "comment_density": (total_comments / total_loc * 100) if total_loc > 0 else 0,
            },
        },
        "cyclomatic_complexity": {
            "average": total_complexity / num_callables if num_callables > 0 else 0,
        },
        "depth_of_inheritance": {
            "average": total_doi / len(codebase.classes) if codebase.classes else 0,
        },
        "halstead_metrics": {
            "total_volume": int(total_volume),
            "average_volume": int(total_volume / num_callables) if num_callables > 0 else 0,
        },
        "maintainability_index": {
            "average": int(total_mi / num_callables) if num_callables > 0 else 0,
        },
        "description": desc,
        "num_files": num_files,
        "num_functions": num_functions,
        "num_classes": num_classes,
    }

    return results

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
