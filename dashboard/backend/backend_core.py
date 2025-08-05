"""
REAL PRODUCTION CODEBASE ANALYSIS BACKEND
Complete integration with graph-sitter for production dashboard
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import tempfile
import shutil
import subprocess
from collections import defaultdict, Counter

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add graph-sitter to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Real graph-sitter imports
from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major" 
    MINOR = "minor"

class IssueType(str, Enum):
    UNUSED_FUNCTION = "unused_function"
    UNUSED_CLASS = "unused_class"
    UNUSED_IMPORT = "unused_import"
    UNUSED_PARAMETER = "unused_parameter"
    MISSING_TYPE_ANNOTATION = "missing_type_annotation"
    EMPTY_FUNCTION = "empty_function"
    PARAMETER_MISMATCH = "parameter_mismatch"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    IMPLEMENTATION_ERROR = "implementation_error"

@dataclass
class CodeIssue:
    id: str
    type: IssueType
    severity: IssueSeverity
    file_path: str
    line_number: int
    symbol_name: str
    description: str
    context: str
    suggestion: str
    auto_fixable: bool = False

@dataclass
class FunctionContext:
    name: str
    filepath: str
    line_start: int
    line_end: int
    source: str
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]
    dependencies: List[Dict[str, str]]
    usages: List[Dict[str, Any]]
    function_calls: List[str]
    called_by: List[str]
    class_name: Optional[str]
    max_call_chain: List[str]
    issues: List[CodeIssue]
    is_entry_point: bool = False
    is_dead_code: bool = False
    call_count: int = 0

@dataclass
class TreeNode:
    name: str
    type: str  # file, folder, function, class
    path: str
    children: List['TreeNode']
    issues: List[CodeIssue]
    is_entry_point: bool = False
    is_important: bool = False
    line_count: int = 0
    
class AnalysisRequest(BaseModel):
    repo_url: str
    language: Optional[str] = None

class AnalysisResponse(BaseModel):
    success: bool
    analysis_id: str
    message: str
    
class TreeStructureResponse(BaseModel):
    tree: Dict[str, Any]
    total_issues: int
    issues_by_severity: Dict[str, int]

class RealCodebaseAnalyzer:
    """Real production codebase analyzer using graph-sitter"""
    
    def __init__(self):
        self.analyses: Dict[str, Dict] = {}
        self.temp_dirs: Dict[str, str] = {}
        
    def clone_repository(self, repo_url: str) -> str:
        """Clone repository to temporary directory"""
        temp_dir = tempfile.mkdtemp(prefix="codebase_analysis_")
        
        try:
            logger.info(f"Cloning repository: {repo_url}")
            result = subprocess.run(
                ["git", "clone", repo_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
                
            logger.info(f"Repository cloned to: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    def get_codebase_summary(self, codebase: Codebase) -> str:
        """Get comprehensive codebase summary using real graph-sitter"""
        try:
            files = codebase.files(extensions=None)
            functions = codebase.functions
            classes = codebase.classes
            imports = codebase.imports
            
            summary = f"""
CODEBASE SUMMARY
================
Total Files: {len(files)}
Total Functions: {len(functions)}
Total Classes: {len(classes)}
Total Imports: {len(imports)}

LANGUAGE BREAKDOWN:
"""
            
            # Language breakdown
            lang_counts: defaultdict[str, int] = defaultdict(int)
            for file in files:
                ext = Path(file.filepath).suffix.lower()
                if ext in ['.py']:
                    lang_counts['Python'] += 1
                elif ext in ['.ts', '.tsx', '.js', '.jsx']:
                    lang_counts['TypeScript/JavaScript'] += 1
                else:
                    lang_counts['Other'] += 1
            
            for lang, count in lang_counts.items():
                summary += f"- {lang}: {count} files\n"
            
            # Top level structure
            summary += "\nTOP LEVEL STRUCTURE:\n"
            root_dirs = set()
            for file in files[:20]:  # Show first 20 files
                parts = Path(file.filepath).parts
                if len(parts) > 1:
                    root_dirs.add(parts[0])
            
            for dir_name in sorted(root_dirs):
                summary += f"- {dir_name}/\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating codebase summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def get_file_summary(self, file) -> str:
        """Get file summary using real graph-sitter"""
        try:
            summary = f"""
FILE SUMMARY: {file.filepath}
{'=' * (14 + len(file.filepath))}
"""
            
            # Basic info
            if hasattr(file, 'source'):
                lines = file.source.count('\n') + 1
                summary += f"Lines of Code: {lines}\n"
            
            # Functions in file
            if hasattr(file, 'functions'):
                functions = list(file.functions)
                summary += f"Functions: {len(functions)}\n"
                for func in functions[:5]:  # Show first 5
                    summary += f"  - {func.name}\n"
                if len(functions) > 5:
                    summary += f"  ... and {len(functions) - 5} more\n"
            
            # Classes in file
            if hasattr(file, 'classes'):
                classes = list(file.classes)
                summary += f"Classes: {len(classes)}\n"
                for cls in classes[:5]:  # Show first 5
                    summary += f"  - {cls.name}\n"
                if len(classes) > 5:
                    summary += f"  ... and {len(classes) - 5} more\n"
            
            # Imports
            if hasattr(file, 'imports'):
                imports = list(file.imports)
                summary += f"Imports: {len(imports)}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating file summary: {e}")
            return f"Error generating file summary: {str(e)}"
    
    def get_function_summary(self, function) -> str:
        """Get function summary using real graph-sitter"""
        try:
            summary = f"""
FUNCTION SUMMARY: {function.name}
{'=' * (18 + len(function.name))}
File: {function.filepath}
"""
            
            # Parameters
            if hasattr(function, 'parameters'):
                params = list(function.parameters)
                summary += f"Parameters: {len(params)}\n"
                for param in params:
                    param_name = param.name if hasattr(param, 'name') else str(param)
                    param_type = param.type if hasattr(param, 'type') else 'Unknown'
                    summary += f"  - {param_name}: {param_type}\n"
            
            # Return type
            if hasattr(function, 'return_type') and function.return_type:
                summary += f"Return Type: {function.return_type}\n"
            
            # Function calls
            if hasattr(function, 'function_calls'):
                calls = list(function.function_calls)
                summary += f"Function Calls: {len(calls)}\n"
                for call in calls[:5]:
                    summary += f"  - {call.name}\n"
                if len(calls) > 5:
                    summary += f"  ... and {len(calls) - 5} more\n"
            
            # Called by
            if hasattr(function, 'call_sites'):
                call_sites = list(function.call_sites)
                summary += f"Called By: {len(call_sites)} functions\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating function summary: {e}")
            return f"Error generating function summary: {str(e)}"
    
    def get_class_summary(self, cls) -> str:
        """Get class summary using real graph-sitter"""
        try:
            summary = f"""
CLASS SUMMARY: {cls.name}
{'=' * (15 + len(cls.name))}
File: {cls.filepath}
"""
            
            # Methods
            if hasattr(cls, 'methods'):
                methods = list(cls.methods)
                summary += f"Methods: {len(methods)}\n"
                for method in methods:
                    summary += f"  - {method.name}\n"
            
            # Attributes
            if hasattr(cls, 'attributes'):
                attributes = list(cls.attributes)
                summary += f"Attributes: {len(attributes)}\n"
                for attr in attributes[:5]:
                    summary += f"  - {attr.name}\n"
                if len(attributes) > 5:
                    summary += f"  ... and {len(attributes) - 5} more\n"
            
            # Inheritance
            if hasattr(cls, 'superclasses'):
                superclasses = list(cls.superclasses)
                if superclasses:
                    summary += f"Inherits from: {' -> '.join(s.name for s in superclasses)}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating class summary: {e}")
            return f"Error generating class summary: {str(e)}"
    
    def get_symbol_summary(self, symbol) -> str:
        """Get symbol summary using real graph-sitter"""
        try:
            summary = f"""
SYMBOL SUMMARY: {symbol.name}
{'=' * (16 + len(symbol.name))}
File: {symbol.filepath}
Type: {symbol.symbol_type if hasattr(symbol, 'symbol_type') else 'Unknown'}
"""
            
            # Usages
            if hasattr(symbol, 'usages'):
                usages = list(symbol.usages)
                summary += f"Usages: {len(usages)}\n"
                for usage in usages[:5]:
                    if hasattr(usage, 'usage_symbol'):
                        summary += f"  - {usage.usage_symbol.filepath}\n"
                if len(usages) > 5:
                    summary += f"  ... and {len(usages) - 5} more\n"
            
            # Dependencies
            if hasattr(symbol, 'dependencies'):
                deps = list(symbol.dependencies)
                summary += f"Dependencies: {len(deps)}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating symbol summary: {e}")
            return f"Error generating symbol summary: {str(e)}"

# Initialize FastAPI app
app = FastAPI(title="Real Codebase Analysis Dashboard", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzer
analyzer = RealCodebaseAnalyzer()

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_codebase(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start codebase analysis"""
    analysis_id = f"analysis_{int(time.time())}"
    
    # Start background analysis
    background_tasks.add_task(run_analysis, analysis_id, request.repo_url, request.language)
    
    return AnalysisResponse(
        success=True,
        analysis_id=analysis_id,
        message="Analysis started"
    )

async def run_analysis(analysis_id: str, repo_url: str, language: Optional[str]):
    """Run the actual analysis in background"""
    try:
        logger.info(f"Starting analysis {analysis_id} for {repo_url}")
        
        # Clone repository
        temp_dir = analyzer.clone_repository(repo_url)
        analyzer.temp_dirs[analysis_id] = temp_dir
        
        # Initialize codebase with real graph-sitter
        logger.info("Initializing codebase with graph-sitter...")
        
        # Determine language
        prog_lang = None
        if language:
            prog_lang = ProgrammingLanguage(language.upper())
        
        # Create codebase
        codebase = Codebase(repo_path=temp_dir, language=prog_lang)
        
        # Store initial analysis
        analyzer.analyses[analysis_id] = {
            "status": "analyzing",
            "repo_url": repo_url,
            "temp_dir": temp_dir,
            "codebase": codebase,
            "start_time": time.time(),
            "progress": 0
        }
        
        # Run comprehensive analysis
        await perform_comprehensive_analysis(analysis_id, codebase)
        
        logger.info(f"Analysis {analysis_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        analyzer.analyses[analysis_id] = {
            "status": "error",
            "error": str(e),
            "progress": 0
        }

async def perform_comprehensive_analysis(analysis_id: str, codebase: Codebase):
    """Perform comprehensive analysis using real graph-sitter"""
    try:
        analysis = analyzer.analyses[analysis_id]
        analysis["progress"] = 10
        
        # Get all codebase elements
        logger.info("Extracting codebase elements...")
        files = codebase.files(extensions=None)
        functions = codebase.functions
        classes = codebase.classes
        imports = codebase.imports
        symbols = codebase.symbols
        
        analysis["progress"] = 30
        
        # Generate summaries
        logger.info("Generating summaries...")
        codebase_summary = analyzer.get_codebase_summary(codebase)
        
        analysis["progress"] = 50
        
        # Analyze issues and patterns
        logger.info("Analyzing issues and patterns...")
        issues = await analyze_issues(codebase, functions, classes, imports)
        important_functions = await find_important_functions(functions)
        dead_code = await find_dead_code(functions, classes, imports)
        
        analysis["progress"] = 80
        
        # Build tree structure
        logger.info("Building tree structure...")
        tree_structure = await build_tree_structure(files, functions, classes, issues)
        
        analysis["progress"] = 100
        
        # Store complete results
        analysis.update({
            "status": "completed",
            "codebase_summary": codebase_summary,
            "stats": {
                "total_files": len(files),
                "total_functions": len(functions),
                "total_classes": len(classes),
                "total_imports": len(imports),
                "total_symbols": len(symbols),
                "total_issues": len(issues)
            },
            "issues": [asdict(issue) for issue in issues],
            "important_functions": important_functions,
            "dead_code": dead_code,
            "tree_structure": tree_structure,
            "completion_time": time.time()
        })
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        analysis["status"] = "error"
        analysis["error"] = str(e)

async def analyze_issues(codebase, functions, classes, imports) -> List[CodeIssue]:
    """Analyze codebase for issues using real graph-sitter data"""
    issues = []
    issue_id = 0
    
    try:
        # Find unused functions
        for func in functions:
            if hasattr(func, 'call_sites'):
                call_sites = list(func.call_sites)
                if len(call_sites) == 0:
                    issues.append(CodeIssue(
                        id=f"issue_{issue_id}",
                        type=IssueType.UNUSED_FUNCTION,
                        severity=IssueSeverity.MINOR,
                        file_path=func.filepath,
                        line_number=func.start_point[0] if hasattr(func, 'start_point') else 0,
                        symbol_name=func.name,
                        description=f"Function '{func.name}' is never called",
                        context=func.source if hasattr(func, 'source') else "",
                        suggestion="Consider removing this function if it's truly unused",
                        auto_fixable=True
                    ))
                    issue_id += 1
        
        # Find functions with missing type annotations
        for func in functions:
            if hasattr(func, 'parameters'):
                for param in func.parameters:
                    if not hasattr(param, 'type') or param.type is None:
                        issues.append(CodeIssue(
                            id=f"issue_{issue_id}",
                            type=IssueType.MISSING_TYPE_ANNOTATION,
                            severity=IssueSeverity.MAJOR,
                            file_path=func.filepath,
                            line_number=func.start_point[0] if hasattr(func, 'start_point') else 0,
                            symbol_name=f"{func.name}.{param.name}",
                            description=f"Parameter '{param.name}' in function '{func.name}' lacks type annotation",
                            context=func.source if hasattr(func, 'source') else "",
                            suggestion=f"Add type annotation: {param.name}: <type>",
                            auto_fixable=True
                        ))
                        issue_id += 1
        
        # Find unused classes
        for cls in classes:
            if hasattr(cls, 'usages'):
                usages = list(cls.usages)
                if len(usages) == 0:
                    issues.append(CodeIssue(
                        id=f"issue_{issue_id}",
                        type=IssueType.UNUSED_CLASS,
                        severity=IssueSeverity.MINOR,
                        file_path=cls.filepath,
                        line_number=cls.start_point[0] if hasattr(cls, 'start_point') else 0,
                        symbol_name=cls.name,
                        description=f"Class '{cls.name}' is never used",
                        context=cls.source if hasattr(cls, 'source') else "",
                        suggestion="Consider removing this class if it's truly unused",
                        auto_fixable=True
                    ))
                    issue_id += 1
        
        # Find unused imports
        for imp in imports:
            if hasattr(imp, 'imported_symbol'):
                for symbol in imp.imported_symbol:
                    if hasattr(symbol, 'usages'):
                        usages = list(symbol.usages)
                        if len(usages) == 0:
                            issues.append(CodeIssue(
                                id=f"issue_{issue_id}",
                                type=IssueType.UNUSED_IMPORT,
                                severity=IssueSeverity.MINOR,
                                file_path=imp.filepath,
                                line_number=imp.start_point[0] if hasattr(imp, 'start_point') else 0,
                                symbol_name=symbol.name,
                                description=f"Import '{symbol.name}' is never used",
                                context=imp.source if hasattr(imp, 'source') else "",
                                suggestion="Remove this unused import",
                                auto_fixable=True
                            ))
                            issue_id += 1
        
    except Exception as e:
        logger.error(f"Error analyzing issues: {e}")
    
    return issues

async def find_important_functions(functions) -> List[Dict[str, Any]]:
    """Find most important functions using real graph-sitter data"""
    important = []
    
    try:
        # Find most called functions
        functions_with_calls = []
        for func in functions:
            if hasattr(func, 'call_sites'):
                call_count = len(list(func.call_sites))
                functions_with_calls.append((func, call_count))
        
        # Sort by call count
        functions_with_calls.sort(key=lambda x: x[1], reverse=True)
        
        # Get top 10 most called
        for func, call_count in functions_with_calls[:10]:
            important.append({
                "name": func.name,
                "filepath": func.filepath,
                "call_count": call_count,
                "type": "most_called",
                "line_number": func.start_point[0] if hasattr(func, 'start_point') else 0
            })
        
        # Find functions that make the most calls
        functions_making_calls = []
        for func in functions:
            if hasattr(func, 'function_calls'):
                calls_made = len(list(func.function_calls))
                functions_making_calls.append((func, calls_made))
        
        functions_making_calls.sort(key=lambda x: x[1], reverse=True)
        
        # Get top 5 functions making most calls
        for func, calls_made in functions_making_calls[:5]:
            important.append({
                "name": func.name,
                "filepath": func.filepath,
                "calls_made": calls_made,
                "type": "makes_most_calls",
                "line_number": func.start_point[0] if hasattr(func, 'start_point') else 0
            })
        
    except Exception as e:
        logger.error(f"Error finding important functions: {e}")
    
    return important

async def find_dead_code(functions, classes, imports) -> List[Dict[str, Any]]:
    """Find dead code using real graph-sitter data"""
    dead_code = []
    
    try:
        # Find unused functions
        for func in functions:
            if hasattr(func, 'call_sites'):
                call_sites = list(func.call_sites)
                if len(call_sites) == 0:
                    dead_code.append({
                        "type": "function",
                        "name": func.name,
                        "filepath": func.filepath,
                        "line_number": func.start_point[0] if hasattr(func, 'start_point') else 0,
                        "reason": "Never called"
                    })
        
        # Find unused classes
        for cls in classes:
            if hasattr(cls, 'usages'):
                usages = list(cls.usages)
                if len(usages) == 0:
                    dead_code.append({
                        "type": "class",
                        "name": cls.name,
                        "filepath": cls.filepath,
                        "line_number": cls.start_point[0] if hasattr(cls, 'start_point') else 0,
                        "reason": "Never instantiated or referenced"
                    })
        
    except Exception as e:
        logger.error(f"Error finding dead code: {e}")
    
    return dead_code

async def build_tree_structure(files, functions, classes, issues) -> Dict[str, Any]:
    """Build interactive tree structure with real data"""
    tree = {
        "name": "root",
        "type": "folder",
        "path": "/",
        "children": [],
        "issues": [],
        "total_issues": len(issues)
    }
    
    try:
        # Group issues by file
        issues_by_file = defaultdict(list)
        for issue in issues:
            issues_by_file[issue.file_path].append(issue)
        
        # Build file tree
        file_tree: Dict[str, Any] = {}
        for file in files:
            path_parts = Path(file.filepath).parts
            current = file_tree
            
            for part in path_parts[:-1]:  # Directories
                if part not in current:
                    current[part] = {"type": "folder", "children": {}, "issues": []}
                current = current[part]["children"]
            
            # File
            filename = path_parts[-1]
            file_issues = issues_by_file.get(file.filepath, [])
            current[filename] = {
                "type": "file",
                "path": file.filepath,
                "issues": [asdict(issue) for issue in file_issues],
                "functions": [],
                "classes": []
            }
            
            # Add functions in this file
            for func in functions:
                if func.filepath == file.filepath:
                    current[filename]["functions"].append({
                        "name": func.name,
                        "line_number": func.start_point[0] if hasattr(func, 'start_point') else 0,
                        "issues": [asdict(issue) for issue in file_issues if issue.symbol_name == func.name]
                    })
            
            # Add classes in this file
            for cls in classes:
                if cls.filepath == file.filepath:
                    current[filename]["classes"].append({
                        "name": cls.name,
                        "line_number": cls.start_point[0] if hasattr(cls, 'start_point') else 0,
                        "issues": [asdict(issue) for issue in file_issues if issue.symbol_name == cls.name]
                    })
        
        # Convert to tree format
        def convert_to_tree(node_dict, name="root", path="/"):
            children = []
            node_issues = []
            
            for key, value in node_dict.items():
                if value["type"] == "folder":
                    child = convert_to_tree(value["children"], key, f"{path}/{key}")
                    children.append(child)
                else:  # file
                    children.append({
                        "name": key,
                        "type": "file",
                        "path": value["path"],
                        "issues": value["issues"],
                        "functions": value["functions"],
                        "classes": value["classes"],
                        "children": []
                    })
                    node_issues.extend(value["issues"])
            
            return {
                "name": name,
                "type": "folder" if children else "file",
                "path": path,
                "children": children,
                "issues": node_issues,
                "total_issues": len(node_issues)
            }
        
        tree = convert_to_tree(file_tree)
        
    except Exception as e:
        logger.error(f"Error building tree structure: {e}")
    
    return tree

@app.get("/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """Get analysis status"""
    if analysis_id not in analyzer.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyzer.analyses[analysis_id]
    return {
        "analysis_id": analysis_id,
        "status": analysis.get("status", "unknown"),
        "progress": analysis.get("progress", 0),
        "error": analysis.get("error")
    }

@app.get("/analysis/{analysis_id}/tree")
async def get_tree_structure(analysis_id: str):
    """Get interactive tree structure"""
    if analysis_id not in analyzer.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyzer.analyses[analysis_id]
    if analysis.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return TreeStructureResponse(
        tree=analysis["tree_structure"],
        total_issues=len(analysis["issues"]),
        issues_by_severity={
            "critical": len([i for i in analysis["issues"] if i["severity"] == "critical"]),
            "major": len([i for i in analysis["issues"] if i["severity"] == "major"]),
            "minor": len([i for i in analysis["issues"] if i["severity"] == "minor"])
        }
    )

@app.get("/analysis/{analysis_id}/summary")
async def get_codebase_summary(analysis_id: str):
    """Get codebase summary"""
    if analysis_id not in analyzer.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyzer.analyses[analysis_id]
    if analysis.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return {
        "summary": analysis["codebase_summary"],
        "stats": analysis["stats"],
        "important_functions": analysis["important_functions"],
        "dead_code": analysis["dead_code"]
    }

@app.get("/analysis/{analysis_id}/issues")
async def get_issues(analysis_id: str):
    """Get all issues"""
    if analysis_id not in analyzer.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyzer.analyses[analysis_id]
    if analysis.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return {
        "issues": analysis["issues"],
        "total": len(analysis["issues"]),
        "by_severity": {
            "critical": [i for i in analysis["issues"] if i["severity"] == "critical"],
            "major": [i for i in analysis["issues"] if i["severity"] == "major"],
            "minor": [i for i in analysis["issues"] if i["severity"] == "minor"]
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
