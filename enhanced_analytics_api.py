from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.statements.for_loop_statement import ForLoopStatement
from graph_sitter.core.statements.if_block_statement import IfBlockStatement
from graph_sitter.core.statements.try_catch_statement import TryCatchStatement
from graph_sitter.core.statements.while_statement import WhileStatement
from graph_sitter.core.expressions.binary_expression import BinaryExpression
from graph_sitter.core.expressions.unary_expression import UnaryExpression
from graph_sitter.core.expressions.comparison_expression import ComparisonExpression
import math
import re
import requests
from datetime import datetime, timedelta
import subprocess
import os
import tempfile
from fastapi.middleware.cors import CORSMiddleware
import modal
import asyncio
import logging
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

# Enhanced imports for LSP and error analysis
# Note: LSP imports are optional and will be used if available
try:
    from graph_sitter.extensions.lsp.server import GraphSitterLanguageServer
    from graph_sitter.extensions.lsp.protocol import GraphSitterLanguageServerProtocol
    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False

try:
    from lsprotocol import types as lsp_types
    LSPROTOCOL_AVAILABLE = True
except ImportError:
    LSPROTOCOL_AVAILABLE = False

# Create Serena-compatible types and classes
class DiagnosticSeverity(Enum):
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4

class ErrorCategory(Enum):
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    IMPORT = "import"
    UNDEFINED = "undefined"

@dataclass
class Position:
    line: int
    character: int

@dataclass
class Range:
    start: Position
    end: Position

@dataclass
class Diagnostic:
    range: Range
    severity: DiagnosticSeverity
    code: Optional[str]
    source: Optional[str]
    message: str
    category: ErrorCategory

@dataclass
class CodeError:
    """Represents a code error with comprehensive context."""
    file_path: str
    line_number: int
    column: int
    severity: DiagnosticSeverity
    category: ErrorCategory
    message: str
    code: Optional[str] = None
    source: Optional[str] = None
    context_lines: Optional[List[str]] = None
    fix_suggestions: Optional[List[str]] = None

class SerenaErrorAnalyzer:
    """Enhanced error analyzer using LSP and graph-sitter capabilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def analyze_codebase_errors(self, codebase_path: str) -> List[CodeError]:
        """Analyze codebase for errors using LSP and static analysis."""
        errors = []
        
        try:
            # Initialize codebase
            self.logger.info(f"Initializing codebase for path: {codebase_path}")
            
            if codebase_path.startswith('http') or ('/' in codebase_path and not os.path.exists(codebase_path)):
                # Remote repository
                self.logger.info("Using from_repo for remote repository")
                codebase = Codebase.from_repo(codebase_path)
                static_errors = self._perform_static_analysis(codebase)
                errors.extend(static_errors)
            else:
                # Local directory - read files and separate by language
                self.logger.info("Reading local directory files")
                python_files = {}
                js_files = {}
                
                if os.path.isdir(codebase_path):
                    for root, dirs, files in os.walk(codebase_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, codebase_path)
                            
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    
                                if file.endswith('.py'):
                                    python_files[rel_path] = content
                                elif file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                                    js_files[rel_path] = content
                            except Exception as e:
                                self.logger.warning(f"Could not read file {file_path}: {e}")
                
                self.logger.info(f"Found {len(python_files)} Python files and {len(js_files)} JS/TS files")
                
                # Analyze Python files first
                if python_files:
                    self.logger.info("Analyzing Python files")
                    python_codebase = Codebase.from_files(python_files)
                    static_errors = self._perform_static_analysis(python_codebase)
                    errors.extend(static_errors)
                
                # Analyze JS/TS files
                if js_files:
                    self.logger.info("Analyzing JS/TS files")
                    js_codebase = Codebase.from_files(js_files)
                    static_errors = self._perform_static_analysis(js_codebase)
                    errors.extend(static_errors)
                
                if not python_files and not js_files:
                    self.logger.warning("No supported files found to analyze")
                    return []
            
            self.logger.info(f"Codebase analysis completed - found {len(errors)} errors")
            
            # Try LSP-based analysis if available
            try:
                lsp_errors = await self._perform_lsp_analysis(codebase_path)
                errors.extend(lsp_errors)
            except Exception as e:
                self.logger.warning(f"LSP analysis failed: {e}")
                
        except Exception as e:
            self.logger.error(f"Error analyzing codebase: {e}")
            
        return errors
    
    def _perform_static_analysis(self, codebase: Codebase) -> List[CodeError]:
        """Perform static analysis to detect common errors."""
        errors = []
        
        self.logger.info(f"Found {len(codebase.files)} files in codebase")
        
        for file in codebase.files:
            if not file.source.strip():
                continue
                
            try:
                # Analyze Python files for common issues
                if file.path.suffix == '.py':
                    file_errors = self._analyze_python_file(file)
                    errors.extend(file_errors)
                    
                # Analyze JavaScript/TypeScript files
                elif file.path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                    file_errors = self._analyze_js_file(file)
                    errors.extend(file_errors)
                    
            except Exception as e:
                self.logger.warning(f"Error analyzing file {file.path}: {e}")
                
        self.logger.info(f"Static analysis found {len(errors)} errors")
        return errors
    
    def _analyze_python_file(self, file) -> List[CodeError]:
        """Analyze Python file for common errors."""
        errors = []
        lines = file.source.splitlines()
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for common Python issues
            if line_stripped.startswith('import ') or line_stripped.startswith('from '):
                # Check for unused imports (simplified)
                if 'import' in line and not self._is_import_used(file.source, line):
                    errors.append(CodeError(
                        file_path=str(file.path),
                        line_number=i,
                        column=0,
                        severity=DiagnosticSeverity.WARNING,
                        category=ErrorCategory.IMPORT,
                        message=f"Potentially unused import: {line_stripped}",
                        context_lines=self._get_context_lines(lines, i)
                    ))
            
            # Check for undefined variables (simplified)
            if '=' in line and not line_stripped.startswith('#'):
                undefined_vars = self._check_undefined_variables(line, file.source)
                for var in undefined_vars:
                    errors.append(CodeError(
                        file_path=str(file.path),
                        line_number=i,
                        column=line.find(var),
                        severity=DiagnosticSeverity.ERROR,
                        category=ErrorCategory.UNDEFINED,
                        message=f"Potentially undefined variable: {var}",
                        context_lines=self._get_context_lines(lines, i)
                    ))
            
            # Check for syntax issues
            if line_stripped.endswith(':') and not any(keyword in line for keyword in ['if', 'for', 'while', 'def', 'class', 'try', 'except', 'with']):
                errors.append(CodeError(
                    file_path=str(file.path),
                    line_number=i,
                    column=len(line) - 1,
                    severity=DiagnosticSeverity.WARNING,
                    category=ErrorCategory.SYNTAX,
                    message="Unexpected colon - possible syntax issue",
                    context_lines=self._get_context_lines(lines, i)
                ))
                
        return errors
    
    def _analyze_js_file(self, file) -> List[CodeError]:
        """Analyze JavaScript/TypeScript file for common errors."""
        errors = []
        lines = file.source.splitlines()
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for console.log statements (style issue)
            if 'console.log' in line:
                errors.append(CodeError(
                    file_path=str(file.path),
                    line_number=i,
                    column=line.find('console.log'),
                    severity=DiagnosticSeverity.INFORMATION,
                    category=ErrorCategory.STYLE,
                    message="console.log statement found - consider removing for production",
                    context_lines=self._get_context_lines(lines, i)
                ))
            
            # Check for var usage (style issue)
            if line_stripped.startswith('var '):
                errors.append(CodeError(
                    file_path=str(file.path),
                    line_number=i,
                    column=0,
                    severity=DiagnosticSeverity.WARNING,
                    category=ErrorCategory.STYLE,
                    message="Use 'let' or 'const' instead of 'var'",
                    context_lines=self._get_context_lines(lines, i),
                    fix_suggestions=["Replace 'var' with 'let' or 'const'"]
                ))
                
        return errors
    
    def _is_import_used(self, source: str, import_line: str) -> bool:
        """Check if an import is used in the source code (simplified)."""
        # Extract imported names
        if 'from' in import_line and 'import' in import_line:
            parts = import_line.split('import')
            if len(parts) > 1:
                imported = parts[1].strip().split(',')
                for item in imported:
                    item = item.strip().split(' as ')[0].strip()
                    if item in source:
                        return True
        elif import_line.startswith('import '):
            module = import_line.replace('import ', '').strip().split(' as ')[0]
            if module in source:
                return True
        return False
    
    def _check_undefined_variables(self, line: str, source: str) -> List[str]:
        """Check for potentially undefined variables (simplified)."""
        undefined = []
        # This is a very simplified check - in practice, you'd want more sophisticated analysis
        if '=' in line and not line.strip().startswith('#'):
            # Look for variables on the right side of assignment
            parts = line.split('=')
            if len(parts) > 1:
                right_side = parts[1]
                # Simple regex to find variable-like tokens
                import re
                variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', right_side)
                for var in variables:
                    if var not in ['True', 'False', 'None'] and f'{var} =' not in source and f'def {var}' not in source:
                        undefined.append(var)
        return undefined
    
    def _get_context_lines(self, lines: List[str], line_number: int, context_size: int = 2) -> List[str]:
        """Get context lines around the error."""
        start = max(0, line_number - context_size - 1)
        end = min(len(lines), line_number + context_size)
        return lines[start:end]
    
    async def _perform_lsp_analysis(self, codebase_path: str) -> List[CodeError]:
        """Perform LSP-based analysis (placeholder for future implementation)."""
        # This would integrate with actual LSP servers
        # For now, return empty list as LSP integration is not fully available
        if not LSP_AVAILABLE:
            self.logger.info("LSP integration not available, skipping LSP analysis")
            return []
        
        # Future: Implement actual LSP server communication
        return []

# Modal configuration
image = (
    modal.Image.debian_slim()
    .apt_install("git")
    .pip_install(
        "graph-sitter", "fastapi", "uvicorn", "gitpython", "requests", "pydantic", "datetime"
    )
)

app = modal.App(name="enhanced-analytics-app", image=image)

fastapi_app = FastAPI(title="Enhanced Codebase Analytics API", version="2.0.0")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Original functions (keeping all existing functionality)
def get_monthly_commits(repo_path: str) -> Dict[str, int]:
    """Get the number of commits per month for the last 12 months."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    date_format = "%Y-%m-%d"
    since_date = start_date.strftime(date_format)
    until_date = end_date.strftime(date_format)
    repo_path = "https://github.com/" + repo_path

    try:
        original_dir = os.getcwd()

        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run(["git", "clone", repo_path, temp_dir], check=True)
            os.chdir(temp_dir)

            cmd = [
                "git",
                "log",
                f"--since={since_date}",
                f"--until={until_date}",
                "--format=%aI",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commit_dates = result.stdout.strip().split("\n")

            monthly_counts = {}
            current_date = start_date
            while current_date <= end_date:
                month_key = current_date.strftime("%Y-%m")
                monthly_counts[month_key] = 0
                current_date = (
                    current_date.replace(day=1) + timedelta(days=32)
                ).replace(day=1)

            for date_str in commit_dates:
                if date_str:  # Skip empty lines
                    commit_date = datetime.fromisoformat(date_str.strip())
                    month_key = commit_date.strftime("%Y-%m")
                    if month_key in monthly_counts:
                        monthly_counts[month_key] += 1

            os.chdir(original_dir)
            return dict(sorted(monthly_counts.items()))

    except subprocess.CalledProcessError as e:
        print(f"Error executing git command: {e}")
        return {}
    except Exception as e:
        print(f"Error processing git commits: {e}")
        return {}
    finally:
        try:
            os.chdir(original_dir)
        except:
            pass

def calculate_cyclomatic_complexity(function):
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
            complexity += statement.condition.count(
                " and "
            ) + statement.condition.count(" or ")

        if hasattr(statement, "nested_code_blocks"):
            for block in statement.nested_code_blocks:
                complexity += analyze_block(block)

        return complexity

    def analyze_block(block):
        if not block or not hasattr(block, "statements"):
            return 0
        return sum(analyze_statement(stmt) for stmt in block.statements)

    return (
        1 + analyze_block(function.code_block) if hasattr(function, "code_block") else 1
    )

def cc_rank(complexity):
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
    """Calculate the depth of inheritance for a given class."""
    return len(cls.superclasses)

def get_operators_and_operands(function):
    operators = []
    operands = []

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

    return operators, operands

def calculate_halstead_volume(operators, operands):
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
    """Count different types of lines in source code."""
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

        if ('"""' in line or "'''" in line) and not (
            line.count('"""') % 2 == 0 or line.count("'''") % 2 == 0
        ):
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

def calculate_maintainability_index(
    halstead_volume: float, cyclomatic_complexity: float, loc: int
) -> int:
    """Calculate the normalized maintainability index for a given function."""
    if loc <= 0:
        return 100

    try:
        raw_mi = (
            171
            - 5.2 * math.log(max(1, halstead_volume))
            - 0.23 * cyclomatic_complexity
            - 16.2 * math.log(max(1, loc))
        )
        normalized_mi = max(0, min(100, raw_mi * 100 / 171))
        return int(normalized_mi)
    except (ValueError, TypeError):
        return 0

def get_maintainability_rank(mi_score: float) -> str:
    """Convert maintainability index score to a letter grade."""
    if mi_score >= 85:
        return "A"
    elif mi_score >= 65:
        return "B"
    elif mi_score >= 45:
        return "C"
    elif mi_score >= 25:
        return "D"
    else:
        return "F"

def get_github_repo_description(repo_url):
    api_url = f"https://api.github.com/repos/{repo_url}"

    response = requests.get(api_url)

    if response.status_code == 200:
        repo_data = response.json()
        return repo_data.get("description", "No description available")
    else:
        return ""

# Enhanced Pydantic models
class ErrorInfo(BaseModel):
    file_path: str
    line_number: int
    column: int
    severity: str
    category: str
    message: str
    code: Optional[str] = None
    source: Optional[str] = None
    context_lines: Optional[List[str]] = None
    fix_suggestions: Optional[List[str]] = None

class ErrorSummary(BaseModel):
    total_errors: int
    errors_by_severity: Dict[str, int]
    errors_by_category: Dict[str, int]
    errors_by_file: Dict[str, int]

class EnhancedRepoAnalysis(BaseModel):
    repo_url: str
    line_metrics: Dict[str, Any]
    cyclomatic_complexity: Dict[str, Any]
    depth_of_inheritance: Dict[str, Any]
    halstead_metrics: Dict[str, Any]
    maintainability_index: Dict[str, Any]
    description: str
    num_files: int
    num_functions: int
    num_classes: int
    monthly_commits: Dict[str, int]
    
    # Enhanced error analysis
    error_analysis: ErrorSummary
    errors: List[ErrorInfo]

class RepoRequest(BaseModel):
    repo_url: str

# Original endpoint (keeping for backward compatibility)
@fastapi_app.post("/analyze_repo")
async def analyze_repo(request: RepoRequest) -> Dict[str, Any]:
    """Analyze a repository and return comprehensive metrics."""
    repo_url = request.repo_url
    codebase = Codebase.from_repo(repo_url)

    num_files = len(codebase.files(extensions="*"))
    num_functions = len(codebase.functions)
    num_classes = len(codebase.classes)

    total_loc = total_lloc = total_sloc = total_comments = 0
    total_complexity = 0
    total_volume = 0
    total_mi = 0
    total_doi = 0

    monthly_commits = get_monthly_commits(repo_url)

    for file in codebase.files:
        loc, lloc, sloc, comments = count_lines(file.source)
        total_loc += loc
        total_lloc += lloc
        total_sloc += sloc
        total_comments += comments

    callables = codebase.functions + [m for c in codebase.classes for m in c.methods]

    num_callables = 0
    for func in callables:
        if not hasattr(func, "code_block"):
            continue

        complexity = calculate_cyclomatic_complexity(func)
        operators, operands = get_operators_and_operands(func)
        volume, _, _, _, _ = calculate_halstead_volume(operators, operands)
        loc = len(func.code_block.source.splitlines())
        mi_score = calculate_maintainability_index(volume, complexity, loc)

        total_complexity += complexity
        total_volume += volume
        total_mi += mi_score
        num_callables += 1

    for cls in codebase.classes:
        doi = calculate_doi(cls)
        total_doi += doi

    desc = get_github_repo_description(repo_url)

    results = {
        "repo_url": repo_url,
        "line_metrics": {
            "total": {
                "loc": total_loc,
                "lloc": total_lloc,
                "sloc": total_sloc,
                "comments": total_comments,
                "comment_density": (total_comments / total_loc * 100)
                if total_loc > 0
                else 0,
            },
        },
        "cyclomatic_complexity": {
            "average": total_complexity if num_callables > 0 else 0,
        },
        "depth_of_inheritance": {
            "average": total_doi / len(codebase.classes) if codebase.classes else 0,
        },
        "halstead_metrics": {
            "total_volume": int(total_volume),
            "average_volume": int(total_volume / num_callables)
            if num_callables > 0
            else 0,
        },
        "maintainability_index": {
            "average": int(total_mi / num_callables) if num_callables > 0 else 0,
        },
        "description": desc,
        "num_files": num_files,
        "num_functions": num_functions,
        "num_classes": num_classes,
        "monthly_commits": monthly_commits,
    }

    return results

# Enhanced endpoint with error analysis
@fastapi_app.post("/analyze_repo_enhanced", response_model=EnhancedRepoAnalysis)
async def analyze_repo_enhanced(request: RepoRequest) -> EnhancedRepoAnalysis:
    """Analyze a repository with comprehensive metrics and error detection."""
    repo_url = request.repo_url
    
    # Get original analysis
    original_analysis = await analyze_repo(request)
    
    # Perform error analysis
    error_analyzer = SerenaErrorAnalyzer()
    errors = await error_analyzer.analyze_codebase_errors(repo_url)
    
    # Convert errors to response format
    error_infos = []
    errors_by_severity = {}
    errors_by_category = {}
    errors_by_file = {}
    
    for error in errors:
        error_info = ErrorInfo(
            file_path=error.file_path,
            line_number=error.line_number,
            column=error.column,
            severity=error.severity.name,
            category=error.category.value,
            message=error.message,
            code=error.code,
            source=error.source,
            context_lines=error.context_lines,
            fix_suggestions=error.fix_suggestions
        )
        error_infos.append(error_info)
        
        # Count by severity
        severity_name = error.severity.name
        errors_by_severity[severity_name] = errors_by_severity.get(severity_name, 0) + 1
        
        # Count by category
        category_name = error.category.value
        errors_by_category[category_name] = errors_by_category.get(category_name, 0) + 1
        
        # Count by file
        errors_by_file[error.file_path] = errors_by_file.get(error.file_path, 0) + 1
    
    error_summary = ErrorSummary(
        total_errors=len(errors),
        errors_by_severity=errors_by_severity,
        errors_by_category=errors_by_category,
        errors_by_file=errors_by_file
    )
    
    # Combine with original analysis
    enhanced_analysis = EnhancedRepoAnalysis(
        repo_url=original_analysis["repo_url"],
        line_metrics=original_analysis["line_metrics"],
        cyclomatic_complexity=original_analysis["cyclomatic_complexity"],
        depth_of_inheritance=original_analysis["depth_of_inheritance"],
        halstead_metrics=original_analysis["halstead_metrics"],
        maintainability_index=original_analysis["maintainability_index"],
        description=original_analysis["description"],
        num_files=original_analysis["num_files"],
        num_functions=original_analysis["num_functions"],
        num_classes=original_analysis["num_classes"],
        monthly_commits=original_analysis["monthly_commits"],
        error_analysis=error_summary,
        errors=error_infos
    )
    
    return enhanced_analysis

# New endpoint for error-focused analysis
@fastapi_app.post("/analyze_errors")
async def analyze_errors(request: RepoRequest) -> Dict[str, Any]:
    """Analyze a repository specifically for errors with detailed context."""
    repo_url = request.repo_url
    
    error_analyzer = SerenaErrorAnalyzer()
    errors = await error_analyzer.analyze_codebase_errors(repo_url)
    
    # Format errors in the requested style
    formatted_errors = []
    for i, error in enumerate(errors, 1):
        context_str = ""
        if error.context_lines:
            context_str = " | ".join(error.context_lines[:3])  # First 3 context lines
        
        formatted_error = {
            "index": i,
            "file": error.file_path,
            "line": error.line_number,
            "column": error.column,
            "severity": error.severity.name,
            "category": error.category.value,
            "message": error.message,
            "context": context_str,
            "fix_suggestions": error.fix_suggestions or []
        }
        formatted_errors.append(formatted_error)
    
    return {
        "title": f"Errors in Codebase [{len(errors)}]",
        "total_errors": len(errors),
        "errors": formatted_errors,
        "summary": {
            "by_severity": {severity.name: sum(1 for e in errors if e.severity == severity) for severity in DiagnosticSeverity},
            "by_category": {category.value: sum(1 for e in errors if e.category == category) for category in ErrorCategory},
            "most_problematic_files": sorted(
                [(file, sum(1 for e in errors if e.file_path == file)) for file in set(e.file_path for e in errors)],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    }

@app.function(image=image)
@modal.asgi_app()
def fastapi_modal_app():
    return fastapi_app

if __name__ == "__main__":
    app.deploy("enhanced-analytics-app")
