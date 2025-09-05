"""
Enhanced Tree API for Codebase Dashboard

Provides structured tree data with comprehensive issue detection,
dead code analysis, and important function identification.
"""

import sys
import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from datetime import datetime
import time

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)


@dataclass
class IssueInfo:
    """Information about a code issue."""
    id: str
    type: str
    severity: str  # critical, major, minor
    message: str
    file_path: str
    line_number: int
    column: int
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    context: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class TreeNode:
    """Tree node representing a file or directory."""
    name: str
    path: str
    type: str  # folder, file, function, class
    children: List['TreeNode']
    issues: List[IssueInfo]
    issue_counts: Dict[str, int]  # critical, major, minor
    is_entry_point: bool = False
    is_important: bool = False
    is_dead_code: bool = False
    lines_of_code: int = 0
    functions_count: int = 0
    classes_count: int = 0


class ComprehensiveAnalyzer:
    """Comprehensive codebase analyzer with tree structure generation."""
    
    def __init__(self, repo_path_or_url: str):
        self.repo_path_or_url = repo_path_or_url
        self.codebase: Optional[Codebase] = None
        self.analysis_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.issues: List[IssueInfo] = []
        self.tree_structure: Dict[str, Any] = {}
        self.dead_code_analysis: Dict[str, List[Dict[str, Any]]] = {
            "functions": [],
            "classes": [],
            "imports": []
        }
        self.important_functions: Dict[str, List[Dict[str, Any]]] = {
            "entry_points": [],
            "important_functions": [],
            "most_called": [],
            "recursive": []
        }
        self.codebase_stats: Dict[str, Any] = {}
    
    async def analyze(self) -> Dict[str, Any]:
        """Run comprehensive analysis and return results."""
        try:
            # Step 1: Build codebase
            await self._build_codebase()
            
            # Step 2: Detect issues
            await self._detect_comprehensive_issues()
            
            # Step 3: Analyze dead code
            await self._analyze_dead_code()
            
            # Step 4: Identify important functions
            await self._identify_important_functions()
            
            # Step 5: Generate tree structure
            await self._generate_tree_structure()
            
            # Step 6: Calculate statistics
            await self._calculate_statistics()
            
            return {
                "analysis_id": self.analysis_id,
                "status": "completed",
                "duration": time.time() - self.start_time,
                "tree_structure": self.tree_structure,
                "issues": {
                    "total": len(self.issues),
                    "by_severity": self._group_issues_by_severity(),
                    "issues": [asdict(issue) for issue in self.issues]
                },
                "dead_code": self.dead_code_analysis,
                "important_functions": self.important_functions,
                "stats": self.codebase_stats
            }
            
        except Exception as e:
            return {
                "analysis_id": self.analysis_id,
                "status": "error",
                "error": str(e),
                "duration": time.time() - self.start_time
            }
    
    async def _build_codebase(self):
        """Build the codebase graph."""
        if self.repo_path_or_url.startswith(('http://', 'https://')):
            # GitHub URL
            self.codebase = Codebase.from_repo(self.repo_path_or_url)
        else:
            # Local path
            self.codebase = Codebase(self.repo_path_or_url)
    
    async def _detect_comprehensive_issues(self):
        """Detect comprehensive issues across the codebase."""
        if not self.codebase:
            return
        
        # Issue detection patterns
        issue_id_counter = 0
        
        # 1. Untyped parameters and return types
        for function in self.codebase.functions:
            issue_id_counter += 1
            
            # Check for untyped parameters
            if hasattr(function, 'parameters'):
                for param in function.parameters:
                    if not hasattr(param, 'type') or param.type is None:
                        self.issues.append(IssueInfo(
                            id=f"issue_{issue_id_counter}",
                            type="missing_type_annotation",
                            severity="minor",
                            message=f"Parameter '{param.name}' lacks type annotation",
                            file_path=function.file.filepath if hasattr(function, 'file') else "unknown",
                            line_number=getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                            column=0,
                            function_name=function.name,
                            suggestion=f"Add type annotation: {param.name}: <type>"
                        ))
                        issue_id_counter += 1
            
            # Check for untyped return types
            if not hasattr(function, 'return_type') or function.return_type is None:
                self.issues.append(IssueInfo(
                    id=f"issue_{issue_id_counter}",
                    type="missing_return_type",
                    severity="minor",
                    message=f"Function '{function.name}' lacks return type annotation",
                    file_path=function.file.filepath if hasattr(function, 'file') else "unknown",
                    line_number=getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                    column=0,
                    function_name=function.name,
                    suggestion="Add return type annotation: -> <type>"
                ))
                issue_id_counter += 1
        
        # 2. Unused functions (dead code)
        for function in self.codebase.functions:
            if not hasattr(function, 'call_sites') or len(function.call_sites) == 0:
                # Check if it's not a main function or entry point
                if function.name not in ['main', '__main__', '__init__']:
                    self.issues.append(IssueInfo(
                        id=f"issue_{issue_id_counter}",
                        type="unused_function",
                        severity="major",
                        message=f"Function '{function.name}' appears to be unused",
                        file_path=function.file.filepath if hasattr(function, 'file') else "unknown",
                        line_number=getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                        column=0,
                        function_name=function.name,
                        suggestion="Consider removing if truly unused, or add to __all__ if it's a public API"
                    ))
                    issue_id_counter += 1
        
        # 3. Unused classes
        for cls in self.codebase.classes:
            if not hasattr(cls, 'usages') or len(cls.usages) == 0:
                self.issues.append(IssueInfo(
                    id=f"issue_{issue_id_counter}",
                    type="unused_class",
                    severity="major",
                    message=f"Class '{cls.name}' appears to be unused",
                    file_path=cls.file.filepath if hasattr(cls, 'file') else "unknown",
                    line_number=getattr(cls, 'start_point', [0])[0] if hasattr(cls, 'start_point') else 0,
                    column=0,
                    class_name=cls.name,
                    suggestion="Consider removing if truly unused"
                ))
                issue_id_counter += 1
        
        # 4. Empty functions
        for function in self.codebase.functions:
            if hasattr(function, 'source') and function.source:
                # Simple check for empty functions (just pass or docstring)
                source_lines = [line.strip() for line in function.source.split('\n') if line.strip()]
                if len(source_lines) <= 2 and any('pass' in line for line in source_lines):
                    self.issues.append(IssueInfo(
                        id=f"issue_{issue_id_counter}",
                        type="empty_function",
                        severity="minor",
                        message=f"Function '{function.name}' appears to be empty or only contains 'pass'",
                        file_path=function.file.filepath if hasattr(function, 'file') else "unknown",
                        line_number=getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                        column=0,
                        function_name=function.name,
                        suggestion="Implement the function or remove if not needed"
                    ))
                    issue_id_counter += 1
        
        # 5. Complex functions (high cyclomatic complexity)
        for function in self.codebase.functions:
            if hasattr(function, 'source') and function.source:
                # Simple complexity check based on control flow keywords
                complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with']
                complexity_count = sum(function.source.count(keyword) for keyword in complexity_keywords)
                
                if complexity_count > 10:  # Arbitrary threshold
                    self.issues.append(IssueInfo(
                        id=f"issue_{issue_id_counter}",
                        type="high_complexity",
                        severity="major",
                        message=f"Function '{function.name}' has high cyclomatic complexity ({complexity_count})",
                        file_path=function.file.filepath if hasattr(function, 'file') else "unknown",
                        line_number=getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                        column=0,
                        function_name=function.name,
                        suggestion="Consider breaking down into smaller functions"
                    ))
                    issue_id_counter += 1
    
    async def _analyze_dead_code(self):
        """Analyze dead code in the codebase."""
        if not self.codebase:
            return
        
        # Find unused functions
        for function in self.codebase.functions:
            if not hasattr(function, 'call_sites') or len(function.call_sites) == 0:
                if function.name not in ['main', '__main__', '__init__']:
                    self.dead_code_analysis["functions"].append({
                        "name": function.name,
                        "file_path": function.file.filepath if hasattr(function, 'file') else "unknown",
                        "line_number": getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                        "reason": "No call sites found"
                    })
        
        # Find unused classes
        for cls in self.codebase.classes:
            if not hasattr(cls, 'usages') or len(cls.usages) == 0:
                self.dead_code_analysis["classes"].append({
                    "name": cls.name,
                    "file_path": cls.file.filepath if hasattr(cls, 'file') else "unknown",
                    "line_number": getattr(cls, 'start_point', [0])[0] if hasattr(cls, 'start_point') else 0,
                    "reason": "No usages found"
                })
        
        # Find unused imports (simplified)
        for import_stmt in self.codebase.imports:
            if hasattr(import_stmt, 'imported_symbol') and import_stmt.imported_symbol:
                for symbol in import_stmt.imported_symbol:
                    if not hasattr(symbol, 'usages') or len(symbol.usages) == 0:
                        self.dead_code_analysis["imports"].append({
                            "name": symbol.name if hasattr(symbol, 'name') else str(symbol),
                            "file_path": import_stmt.file.filepath if hasattr(import_stmt, 'file') else "unknown",
                            "line_number": getattr(import_stmt, 'start_point', [0])[0] if hasattr(import_stmt, 'start_point') else 0,
                            "reason": "Imported but never used"
                        })
    
    async def _identify_important_functions(self):
        """Identify important functions and entry points."""
        if not self.codebase:
            return
        
        # Find entry points
        for function in self.codebase.functions:
            if function.name in ['main', '__main__', 'run', 'start', 'execute']:
                self.important_functions["entry_points"].append({
                    "name": function.name,
                    "file_path": function.file.filepath if hasattr(function, 'file') else "unknown",
                    "line_number": getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                    "reason": "Entry point function"
                })
        
        # Find most called functions
        functions_with_calls = []
        for function in self.codebase.functions:
            call_count = len(function.call_sites) if hasattr(function, 'call_sites') else 0
            if call_count > 0:
                functions_with_calls.append((function, call_count))
        
        # Sort by call count and take top 10
        functions_with_calls.sort(key=lambda x: x[1], reverse=True)
        for function, call_count in functions_with_calls[:10]:
            self.important_functions["most_called"].append({
                "name": function.name,
                "file_path": function.file.filepath if hasattr(function, 'file') else "unknown",
                "line_number": getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                "call_count": call_count,
                "reason": f"Called {call_count} times"
            })
        
        # Find recursive functions
        for function in self.codebase.functions:
            if hasattr(function, 'function_calls'):
                for call in function.function_calls:
                    if hasattr(call, 'name') and call.name == function.name:
                        self.important_functions["recursive"].append({
                            "name": function.name,
                            "file_path": function.file.filepath if hasattr(function, 'file') else "unknown",
                            "line_number": getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                            "reason": "Recursive function"
                        })
                        break
        
        # Find functions that make many calls
        functions_with_outgoing_calls = []
        for function in self.codebase.functions:
            call_count = len(function.function_calls) if hasattr(function, 'function_calls') else 0
            if call_count > 5:  # Threshold for "many calls"
                functions_with_outgoing_calls.append((function, call_count))
        
        functions_with_outgoing_calls.sort(key=lambda x: x[1], reverse=True)
        for function, call_count in functions_with_outgoing_calls[:10]:
            self.important_functions["important_functions"].append({
                "name": function.name,
                "file_path": function.file.filepath if hasattr(function, 'file') else "unknown",
                "line_number": getattr(function, 'start_point', [0])[0] if hasattr(function, 'start_point') else 0,
                "outgoing_calls": call_count,
                "reason": f"Makes {call_count} function calls"
            })
    
    async def _generate_tree_structure(self):
        """Generate hierarchical tree structure with issue annotations."""
        if not self.codebase:
            return
        
        # Group issues by file path
        issues_by_file = defaultdict(list)
        for issue in self.issues:
            issues_by_file[issue.file_path].append(issue)
        
        # Build tree structure
        tree_nodes = {}
        
        for file in self.codebase.files:
            file_path = file.filepath if hasattr(file, 'filepath') else file.name
            file_issues = issues_by_file.get(file_path, [])
            
            # Count issues by severity
            issue_counts = {"critical": 0, "major": 0, "minor": 0}
            for issue in file_issues:
                issue_counts[issue.severity] += 1
            
            # Check if file contains entry points or important functions
            is_entry_point = any(
                ep["file_path"] == file_path 
                for ep in self.important_functions["entry_points"]
            )
            
            is_important = any(
                func["file_path"] == file_path 
                for func in self.important_functions["important_functions"]
            )
            
            # Check if file has dead code
            is_dead_code = any(
                func["file_path"] == file_path 
                for func in self.dead_code_analysis["functions"]
            ) or any(
                cls["file_path"] == file_path 
                for cls in self.dead_code_analysis["classes"]
            )
            
            # Calculate file metrics
            lines_of_code = len(file.source.split('\n')) if hasattr(file, 'source') else 0
            functions_count = len(file.functions) if hasattr(file, 'functions') else 0
            classes_count = len(file.classes) if hasattr(file, 'classes') else 0
            
            tree_nodes[file_path] = {
                "name": Path(file_path).name,
                "path": file_path,
                "type": "file",
                "issues": [asdict(issue) for issue in file_issues],
                "issue_counts": issue_counts,
                "is_entry_point": is_entry_point,
                "is_important": is_important,
                "is_dead_code": is_dead_code,
                "lines_of_code": lines_of_code,
                "functions_count": functions_count,
                "classes_count": classes_count,
                "children": []
            }
        
        self.tree_structure = tree_nodes
    
    async def _calculate_statistics(self):
        """Calculate comprehensive codebase statistics."""
        if not self.codebase:
            return
        
        self.codebase_stats = {
            "total_files": len(list(self.codebase.files)),
            "total_functions": len(list(self.codebase.functions)),
            "total_classes": len(list(self.codebase.classes)),
            "total_imports": len(list(self.codebase.imports)),
            "total_symbols": len(list(self.codebase.symbols)),
            "lines_of_code": sum(
                len(file.source.split('\n')) if hasattr(file, 'source') else 0
                for file in self.codebase.files
            ),
            "issues_summary": {
                "total": len(self.issues),
                "critical": len([i for i in self.issues if i.severity == "critical"]),
                "major": len([i for i in self.issues if i.severity == "major"]),
                "minor": len([i for i in self.issues if i.severity == "minor"])
            },
            "dead_code_summary": {
                "functions": len(self.dead_code_analysis["functions"]),
                "classes": len(self.dead_code_analysis["classes"]),
                "imports": len(self.dead_code_analysis["imports"])
            }
        }
    
    def _group_issues_by_severity(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group issues by severity level."""
        grouped = {"critical": [], "major": [], "minor": []}
        for issue in self.issues:
            grouped[issue.severity].append(asdict(issue))
        return grouped


# Global storage for analysis results (in production, use a proper database)
analysis_results = {}


async def start_analysis(repo_url: str) -> str:
    """Start a new codebase analysis."""
    analyzer = ComprehensiveAnalyzer(repo_url)
    analysis_id = analyzer.analysis_id
    
    # Store the analyzer for progress tracking
    analysis_results[analysis_id] = {
        "status": "analyzing",
        "progress": 0,
        "message": "Starting analysis...",
        "analyzer": analyzer,
        "start_time": time.time()
    }
    
    # Run analysis in background
    asyncio.create_task(_run_analysis(analyzer))
    
    return analysis_id


async def _run_analysis(analyzer: ComprehensiveAnalyzer):
    """Run the analysis in the background."""
    analysis_id = analyzer.analysis_id
    
    try:
        # Update progress
        analysis_results[analysis_id]["progress"] = 10
        analysis_results[analysis_id]["message"] = "Building codebase graph..."
        
        await analyzer._build_codebase()
        
        analysis_results[analysis_id]["progress"] = 30
        analysis_results[analysis_id]["message"] = "Detecting issues..."
        
        await analyzer._detect_comprehensive_issues()
        
        analysis_results[analysis_id]["progress"] = 50
        analysis_results[analysis_id]["message"] = "Analyzing dead code..."
        
        await analyzer._analyze_dead_code()
        
        analysis_results[analysis_id]["progress"] = 70
        analysis_results[analysis_id]["message"] = "Identifying important functions..."
        
        await analyzer._identify_important_functions()
        
        analysis_results[analysis_id]["progress"] = 85
        analysis_results[analysis_id]["message"] = "Generating tree structure..."
        
        await analyzer._generate_tree_structure()
        
        analysis_results[analysis_id]["progress"] = 95
        analysis_results[analysis_id]["message"] = "Calculating statistics..."
        
        await analyzer._calculate_statistics()
        
        # Complete
        analysis_results[analysis_id]["status"] = "completed"
        analysis_results[analysis_id]["progress"] = 100
        analysis_results[analysis_id]["message"] = "Analysis completed"
        analysis_results[analysis_id]["duration"] = time.time() - analysis_results[analysis_id]["start_time"]
        
    except Exception as e:
        analysis_results[analysis_id]["status"] = "error"
        analysis_results[analysis_id]["error"] = str(e)
        analysis_results[analysis_id]["message"] = f"Analysis failed: {str(e)}"


def get_analysis_status(analysis_id: str) -> Dict[str, Any]:
    """Get the status of an analysis."""
    if analysis_id not in analysis_results:
        return {"error": "Analysis not found"}
    
    result = analysis_results[analysis_id].copy()
    # Remove the analyzer object from the response
    result.pop("analyzer", None)
    return result


def get_analysis_tree(analysis_id: str) -> Dict[str, Any]:
    """Get the tree structure for an analysis."""
    if analysis_id not in analysis_results:
        return {"error": "Analysis not found"}
    
    result = analysis_results[analysis_id]
    if result["status"] != "completed":
        return {"error": "Analysis not completed"}
    
    analyzer = result["analyzer"]
    return analyzer.tree_structure


def get_analysis_issues(analysis_id: str) -> Dict[str, Any]:
    """Get the issues for an analysis."""
    if analysis_id not in analysis_results:
        return {"error": "Analysis not found"}
    
    result = analysis_results[analysis_id]
    if result["status"] != "completed":
        return {"error": "Analysis not completed"}
    
    analyzer = result["analyzer"]
    return {
        "issues": [asdict(issue) for issue in analyzer.issues],
        "by_severity": analyzer._group_issues_by_severity(),
        "total": len(analyzer.issues)
    }


def get_analysis_dead_code(analysis_id: str) -> Dict[str, Any]:
    """Get the dead code analysis for an analysis."""
    if analysis_id not in analysis_results:
        return {"error": "Analysis not found"}
    
    result = analysis_results[analysis_id]
    if result["status"] != "completed":
        return {"error": "Analysis not completed"}
    
    analyzer = result["analyzer"]
    return analyzer.dead_code_analysis


def get_analysis_important_functions(analysis_id: str) -> Dict[str, Any]:
    """Get the important functions for an analysis."""
    if analysis_id not in analysis_results:
        return {"error": "Analysis not found"}
    
    result = analysis_results[analysis_id]
    if result["status"] != "completed":
        return {"error": "Analysis not completed"}
    
    analyzer = result["analyzer"]
    return analyzer.important_functions


def get_analysis_stats(analysis_id: str) -> Dict[str, Any]:
    """Get the statistics for an analysis."""
    if analysis_id not in analysis_results:
        return {"error": "Analysis not found"}
    
    result = analysis_results[analysis_id]
    if result["status"] != "completed":
        return {"error": "Analysis not completed"}
    
    analyzer = result["analyzer"]
    return analyzer.codebase_stats
