"""Enhanced FastAPI backend for codebase analytics using graph-sitter."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from graph_sitter import Codebase
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
from pathlib import Path

app = FastAPI(title="Enhanced Codebase Analytics", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IssueDetail(BaseModel):
    """Detailed information about a code issue."""
    severity: str  # "Critical", "Functional", "Minor"
    type: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    context_lines: Optional[List[str]] = None
    suggestion: Optional[str] = None


class FileNode(BaseModel):
    """Represents a file or directory in the tree structure."""
    name: str
    path: str
    type: str  # "file" or "directory"
    issue_count: int = 0
    critical_issues: int = 0
    functional_issues: int = 0
    minor_issues: int = 0
    children: Optional[List['FileNode']] = None
    issues: Optional[List[IssueDetail]] = None


class RepoRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str


class EnhancedRepoAnalysis(BaseModel):
    """Enhanced response model with detailed analysis."""
    repo_url: str
    description: str
    basic_metrics: Dict[str, Any]
    line_metrics: Dict[str, Any]
    complexity_metrics: Dict[str, Any]
    repository_structure: FileNode
    issues_summary: Dict[str, int]
    detailed_issues: List[IssueDetail]
    monthly_commits: Optional[Dict[str, int]] = None


def get_monthly_commits(repo_path: str) -> Dict[str, int]:
    """Get the number of commits per month for the last 12 months."""
    try:
        # Get commits from the last 12 months
        since_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        result = subprocess.run(
            ['git', 'log', '--since', since_date, '--pretty=format:%ci'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {}
        
        # Parse commit dates and count by month
        monthly_counts = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                # Extract year-month from date
                date_str = line.split()[0]  # Get date part
                year_month = date_str[:7]  # YYYY-MM format
                monthly_counts[year_month] = monthly_counts.get(year_month, 0) + 1
        
        return monthly_counts
    except Exception:
        return {}


def analyze_statement(statement):
    """Analyze a statement for cyclomatic complexity."""
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
    """Analyze a code block for complexity."""
    if not block or not hasattr(block, "statements"):
        return 0
    return sum(analyze_statement(stmt) for stmt in block.statements)


def calculate_cyclomatic_complexity(function):
    """Calculate cyclomatic complexity for a function."""
    return 1 + analyze_block(function.code_block) if hasattr(function, "code_block") else 1


def get_operators_and_operands(function):
    """Extract operators and operands from a function for Halstead metrics."""
    operators = []
    operands = []

    if not hasattr(function, "code_block") or not function.code_block:
        return operators, operands

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

    return operators, operands


def calculate_halstead_volume(operators, operands):
    """Calculate Halstead volume metrics."""
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
    """Calculate the normalized maintainability index."""
    if loc <= 0:
        return 100

    try:
        raw_mi = 171 - 5.2 * math.log(max(1, halstead_volume)) - 0.23 * cyclomatic_complexity - 16.2 * math.log(max(1, loc))
        normalized_mi = max(0, min(100, raw_mi * 100 / 171))
        return int(normalized_mi)
    except (ValueError, TypeError):
        return 0


def get_github_repo_description(repo_url):
    """Get repository description from GitHub API."""
    api_url = f"https://api.github.com/repos/{repo_url}"
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            repo_data = response.json()
            return repo_data.get("description", "No description available")
    except Exception:
        pass
    return ""


def detect_issues_in_file(file_obj, codebase) -> List[IssueDetail]:
    """Detect various types of issues in a file."""
    issues = []
    
    try:
        source_lines = file_obj.source.splitlines()
        file_path = file_obj.file_path
        
        # Check for common issues
        for line_num, line in enumerate(source_lines, 1):
            line_stripped = line.strip()
            
            # Critical: Misspelled function names
            if "def commiter(" in line:
                issues.append(IssueDetail(
                    severity="Critical",
                    type="Misspelled function name",
                    description="Should be 'committer' not 'commiter'",
                    file_path=file_path,
                    line_number=line_num,
                    context_lines=get_context_lines(source_lines, line_num),
                    suggestion="Rename function to 'committer'"
                ))
            
            # Critical: Incorrect logic patterns
            if "@staticmethod" in line and "is_class_method" in source_lines[max(0, line_num-5):line_num+5]:
                issues.append(IssueDetail(
                    severity="Critical",
                    type="Incorrect implementation",
                    description="Checking @staticmethod instead of @classmethod in is_class_method",
                    file_path=file_path,
                    line_number=line_num,
                    context_lines=get_context_lines(source_lines, line_num),
                    suggestion="Change to check for '@classmethod' instead"
                ))
            
            # Critical: Assert for runtime type checking
            if line_stripped.startswith("assert isinstance("):
                issues.append(IssueDetail(
                    severity="Critical",
                    type="Uses assert for runtime type checking",
                    description="Assert may be disabled in production",
                    file_path=file_path,
                    line_number=line_num,
                    context_lines=get_context_lines(source_lines, line_num),
                    suggestion="Use proper exception handling instead of assert"
                ))
            
            # Functional: TODO comments
            if "TODO" in line_stripped.upper():
                issues.append(IssueDetail(
                    severity="Functional",
                    type="Incomplete implementation",
                    description="Contains TODO indicating incomplete implementation",
                    file_path=file_path,
                    line_number=line_num,
                    context_lines=get_context_lines(source_lines, line_num),
                    suggestion="Complete the implementation or create a proper issue"
                ))
            
            # Functional: Missing validation
            if ".items()" in line and "value" in line and not any("isinstance" in prev_line for prev_line in source_lines[max(0, line_num-3):line_num]):
                issues.append(IssueDetail(
                    severity="Functional",
                    type="Potential null reference",
                    description="Assumes .items() exists without checking type",
                    file_path=file_path,
                    line_number=line_num,
                    context_lines=get_context_lines(source_lines, line_num),
                    suggestion="Add type checking before calling .items()"
                ))
            
            # Minor: Unused parameters (simplified detection)
            if "def " in line and "(" in line and ")" in line:
                func_line = line.strip()
                if func_line.count(",") > 0:  # Has multiple parameters
                    # This is a simplified check - in reality, you'd need more sophisticated analysis
                    issues.append(IssueDetail(
                        severity="Minor",
                        type="Potential unused parameter",
                        description="Function may have unused parameters",
                        file_path=file_path,
                        line_number=line_num,
                        context_lines=get_context_lines(source_lines, line_num),
                        suggestion="Review function parameters for usage"
                    ))
            
            # Minor: Redundant code patterns
            if "@cached_property" in line and "@reader(cache=True)" in source_lines[line_num:line_num+3]:
                issues.append(IssueDetail(
                    severity="Minor",
                    type="Redundant code",
                    description="Using both cached_property and reader(cache=True) is redundant",
                    file_path=file_path,
                    line_number=line_num,
                    context_lines=get_context_lines(source_lines, line_num),
                    suggestion="Remove one of the caching decorators"
                ))
    
    except Exception as e:
        # If there's an error analyzing the file, add it as an issue
        issues.append(IssueDetail(
            severity="Minor",
            type="Analysis error",
            description=f"Could not fully analyze file: {str(e)}",
            file_path=file_path,
            line_number=1,
            context_lines=[],
            suggestion="Manual review recommended"
        ))
    
    return issues


def get_context_lines(source_lines: List[str], line_num: int, context_size: int = 3) -> List[str]:
    """Get context lines around a specific line number."""
    start = max(0, line_num - context_size - 1)
    end = min(len(source_lines), line_num + context_size)
    return source_lines[start:end]


def build_repository_structure(codebase, all_issues: List[IssueDetail]) -> FileNode:
    """Build an interactive tree structure of the repository with issue counts."""
    
    # Group issues by file path
    issues_by_file = {}
    for issue in all_issues:
        if issue.file_path not in issues_by_file:
            issues_by_file[issue.file_path] = []
        issues_by_file[issue.file_path].append(issue)
    
    # Build directory structure
    root = FileNode(
        name=codebase.name or "Repository",
        path="",
        type="directory",
        children=[]
    )
    
    # Process all files
    for file_obj in codebase.files:
        file_path = file_obj.file_path
        file_issues = issues_by_file.get(file_path, [])
        
        # Count issues by severity
        critical_count = len([i for i in file_issues if i.severity == "Critical"])
        functional_count = len([i for i in file_issues if i.severity == "Functional"])
        minor_count = len([i for i in file_issues if i.severity == "Minor"])
        
        # Create file node
        file_node = FileNode(
            name=Path(file_path).name,
            path=file_path,
            type="file",
            issue_count=len(file_issues),
            critical_issues=critical_count,
            functional_issues=functional_count,
            minor_issues=minor_count,
            issues=file_issues
        )
        
        # Add to appropriate directory in tree
        add_to_tree(root, file_path, file_node)
    
    # Calculate directory issue counts
    calculate_directory_counts(root)
    
    return root


def add_to_tree(root: FileNode, file_path: str, file_node: FileNode):
    """Add a file node to the appropriate location in the tree."""
    path_parts = Path(file_path).parts
    current = root
    
    # Navigate/create directory structure
    for i, part in enumerate(path_parts[:-1]):  # Exclude filename
        # Find or create directory
        found = False
        for child in current.children or []:
            if child.name == part and child.type == "directory":
                current = child
                found = True
                break
        
        if not found:
            # Create new directory
            dir_path = "/".join(path_parts[:i+1])
            new_dir = FileNode(
                name=part,
                path=dir_path,
                type="directory",
                children=[]
            )
            if current.children is None:
                current.children = []
            current.children.append(new_dir)
            current = new_dir
    
    # Add file to current directory
    if current.children is None:
        current.children = []
    current.children.append(file_node)


def calculate_directory_counts(node: FileNode):
    """Recursively calculate issue counts for directories."""
    if node.type == "file":
        return
    
    total_issues = 0
    total_critical = 0
    total_functional = 0
    total_minor = 0
    
    for child in node.children or []:
        calculate_directory_counts(child)
        total_issues += child.issue_count
        total_critical += child.critical_issues
        total_functional += child.functional_issues
        total_minor += child.minor_issues
    
    node.issue_count = total_issues
    node.critical_issues = total_critical
    node.functional_issues = total_functional
    node.minor_issues = total_minor


@app.post("/analyze_repo", response_model=EnhancedRepoAnalysis)
async def analyze_repo(request: RepoRequest) -> EnhancedRepoAnalysis:
    """Analyze a repository and return comprehensive metrics with issue detection."""
    try:
        repo_url = request.repo_url.strip()
        
        # Initialize codebase with graph-sitter
        codebase = Codebase.from_repo(repo_url)
        
        # Basic metrics
        num_files = len(codebase.files(extensions="*"))
        num_functions = len(codebase.functions)
        num_classes = len(codebase.classes)
        
        # Line metrics
        total_loc = total_lloc = total_sloc = total_comments = 0
        for file in codebase.files:
            loc, lloc, sloc, comments = count_lines(file.source)
            total_loc += loc
            total_lloc += lloc
            total_sloc += sloc
            total_comments += comments
        
        # Complexity metrics
        total_complexity = 0
        total_volume = 0
        total_mi = 0
        total_doi = 0
        
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
            doi = len(cls.superclasses)
            total_doi += doi
        
        # Issue detection
        all_issues = []
        for file_obj in codebase.files:
            file_issues = detect_issues_in_file(file_obj, codebase)
            all_issues.extend(file_issues)
        
        # Build repository structure
        repo_structure = build_repository_structure(codebase, all_issues)
        
        # Issue summary
        issues_summary = {
            "total": len(all_issues),
            "critical": len([i for i in all_issues if i.severity == "Critical"]),
            "functional": len([i for i in all_issues if i.severity == "Functional"]),
            "minor": len([i for i in all_issues if i.severity == "Minor"])
        }
        
        # Get repository description
        description = get_github_repo_description(repo_url)
        
        # Try to get commit data if it's a local repo
        monthly_commits = {}
        try:
            if hasattr(codebase, 'base_path') and codebase.base_path:
                monthly_commits = get_monthly_commits(codebase.base_path)
        except Exception:
            pass
        
        return EnhancedRepoAnalysis(
            repo_url=repo_url,
            description=description,
            basic_metrics={
                "files": num_files,
                "functions": num_functions,
                "classes": num_classes,
                "modules": len(codebase.files(extensions=".py"))
            },
            line_metrics={
                "total": {
                    "loc": total_loc,
                    "lloc": total_lloc,
                    "sloc": total_sloc,
                    "comments": total_comments,
                    "comment_density": (total_comments / total_loc * 100) if total_loc > 0 else 0,
                }
            },
            complexity_metrics={
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
            },
            repository_structure=repo_structure,
            issues_summary=issues_summary,
            detailed_issues=all_issues,
            monthly_commits=monthly_commits
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Enhanced Codebase Analytics"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

