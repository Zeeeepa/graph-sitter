#!/usr/bin/env python3
"""
🔥 CONSOLIDATED CODEBASE ANALYSIS DASHBOARD
Complete production dashboard with graph-sitter integration
Single file containing both frontend (Reflex) and backend (FastAPI) functionality
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
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

# Reflex imports
import reflex as rx

# Add graph-sitter to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Real graph-sitter imports
from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# BACKEND MODELS AND ENUMS
# ============================================================================

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

@dataclass
class Issue:
    type: IssueType
    severity: IssueSeverity
    description: str
    file_path: str
    line_number: int
    suggestion: str
    context: Optional[Dict[str, Any]] = None

class AnalysisRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")
    language: str = Field(default="python", description="Programming language")

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str

class AnalysisStatus(BaseModel):
    analysis_id: str
    status: str
    progress: int
    error: Optional[str] = None

# ============================================================================
# BACKEND ANALYSIS ENGINE
# ============================================================================

class CodebaseAnalyzer:
    """Real production codebase analyzer using graph-sitter"""
    
    def __init__(self):
        self.analyses: Dict[str, Dict[str, Any]] = {}
        self.temp_dirs: Dict[str, str] = {}
    
    def generate_analysis_id(self) -> str:
        """Generate unique analysis ID"""
        return f"analysis_{int(time.time())}"
    
    def clone_repository(self, repo_url: str, temp_dir: str) -> bool:
        """Clone repository to temporary directory"""
        try:
            logger.info(f"Cloning repository: {repo_url}")
            result = subprocess.run([
                "git", "clone", "--depth", "1", repo_url, temp_dir
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Repository cloned successfully to {temp_dir}")
                return True
            else:
                logger.error(f"Failed to clone repository: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return False
    
    def analyze_codebase(self, analysis_id: str, repo_url: str, language: str):
        """Perform real codebase analysis using graph-sitter"""
        try:
            # Update status
            self.analyses[analysis_id] = {
                "status": "running",
                "progress": 10,
                "repo_url": repo_url,
                "language": language,
                "start_time": time.time()
            }
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix=f"analysis_{analysis_id}_")
            self.temp_dirs[analysis_id] = temp_dir
            
            # Clone repository
            self.analyses[analysis_id]["progress"] = 20
            if not self.clone_repository(repo_url, temp_dir):
                raise Exception("Failed to clone repository")
            
            # Initialize graph-sitter Codebase
            self.analyses[analysis_id]["progress"] = 40
            logger.info(f"Initializing graph-sitter Codebase for {temp_dir}")
            
            # Get programming language enum
            lang_map = {
                "python": ProgrammingLanguage.PYTHON,
                "javascript": ProgrammingLanguage.JAVASCRIPT,
                "typescript": ProgrammingLanguage.TYPESCRIPT,
                "java": ProgrammingLanguage.JAVA,
                "cpp": ProgrammingLanguage.CPP,
                "c": ProgrammingLanguage.C,
                "go": ProgrammingLanguage.GO,
                "rust": ProgrammingLanguage.RUST,
            }
            
            programming_language = lang_map.get(language.lower(), ProgrammingLanguage.PYTHON)
            
            # Create real Codebase instance
            codebase = Codebase.from_directory(
                directory_path=temp_dir,
                programming_language=programming_language
            )
            
            self.analyses[analysis_id]["progress"] = 60
            logger.info("Codebase initialized successfully")
            
            # Perform comprehensive analysis
            self.analyses[analysis_id]["progress"] = 80
            analysis_results = self._perform_comprehensive_analysis(codebase)
            
            # Store results
            self.analyses[analysis_id].update({
                "status": "completed",
                "progress": 100,
                "results": analysis_results,
                "end_time": time.time()
            })
            
            logger.info(f"Analysis {analysis_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {e}")
            self.analyses[analysis_id].update({
                "status": "error",
                "progress": 0,
                "error": str(e),
                "end_time": time.time()
            })
    
    def _perform_comprehensive_analysis(self, codebase: Codebase) -> Dict[str, Any]:
        """Perform comprehensive analysis using real graph-sitter data"""
        
        # Get all codebase elements
        files = list(codebase.files)
        functions = list(codebase.functions)
        classes = list(codebase.classes)
        imports = list(codebase.imports)
        
        # Basic statistics
        stats = {
            "total_files": len(files),
            "total_functions": len(functions),
            "total_classes": len(classes),
            "total_imports": len(imports),
            "total_issues": 0
        }
        
        # Find dead code (unused functions)
        dead_code = []
        for func in functions:
            if hasattr(func, 'call_sites') and len(func.call_sites) == 0:
                dead_code.append({
                    "name": func.name,
                    "file_path": getattr(func, 'filepath', 'unknown'),
                    "type": "function",
                    "reason": "Never called"
                })
        
        # Find important functions (most called)
        important_functions = []
        if functions:
            # Sort by call sites count
            functions_with_calls = []
            for func in functions:
                call_count = len(getattr(func, 'call_sites', []))
                if call_count > 0:
                    functions_with_calls.append((func, call_count))
            
            # Get top functions
            functions_with_calls.sort(key=lambda x: x[1], reverse=True)
            for func, call_count in functions_with_calls[:15]:
                important_functions.append({
                    "name": func.name,
                    "file_path": getattr(func, 'filepath', 'unknown'),
                    "type": "most_called",
                    "call_count": call_count
                })
        
        # Generate issues from dead code
        issues = []
        for item in dead_code:
            issues.append(Issue(
                type=IssueType.UNUSED_FUNCTION,
                severity=IssueSeverity.MINOR,
                description=f"Function '{item['name']}' is never called",
                file_path=item['file_path'],
                line_number=0,
                suggestion="Consider removing this function if it's truly unused"
            ))
        
        stats["total_issues"] = len(issues)
        
        # Generate tree structure
        tree_structure = self._generate_tree_structure(files, issues)
        
        return {
            "stats": stats,
            "issues": [asdict(issue) for issue in issues],
            "dead_code": dead_code,
            "important_functions": important_functions,
            "tree_structure": tree_structure,
            "issues_by_severity": {
                "critical": len([i for i in issues if i.severity == IssueSeverity.CRITICAL]),
                "major": len([i for i in issues if i.severity == IssueSeverity.MAJOR]),
                "minor": len([i for i in issues if i.severity == IssueSeverity.MINOR])
            }
        }
    
    def _generate_tree_structure(self, files, issues) -> Dict[str, Any]:
        """Generate interactive tree structure"""
        
        # Group issues by file
        issues_by_file: Dict[str, List[Issue]] = defaultdict(list)
        for issue in issues:
            issues_by_file[issue.file_path].append(issue)
        
        # Build tree structure
        tree: Dict[str, Any] = {
            "name": "Repository",
            "type": "directory",
            "children": [],
            "issues": len(issues),
            "expanded": True
        }
        
        # Group files by directory
        dir_structure: Dict[str, List[str]] = defaultdict(list)
        for file in files:
            file_path = getattr(file, 'path', getattr(file, 'filepath', 'unknown'))
            if file_path != 'unknown':
                parts = Path(file_path).parts
                if len(parts) > 1:
                    dir_name = parts[0]
                    dir_structure[dir_name].append(file_path)
                else:
                    dir_structure["root"].append(file_path)
        
        # Build directory nodes
        for dir_name, file_paths in dir_structure.items():
            dir_issues = sum(len(issues_by_file.get(fp, [])) for fp in file_paths)
            
            dir_node: Dict[str, Any] = {
                "name": dir_name,
                "type": "directory", 
                "children": [],
                "issues": dir_issues,
                "expanded": False
            }
            
            # Add file nodes
            for file_path in file_paths:
                file_issues = issues_by_file.get(file_path, [])
                file_node: Dict[str, Any] = {
                    "name": Path(file_path).name,
                    "type": "file",
                    "path": file_path,
                    "issues": len(file_issues),
                    "issue_details": [asdict(issue) for issue in file_issues]
                }
                dir_node["children"].append(file_node)
            
            tree["children"].append(dir_node)
        
        return tree

# Global analyzer instance
analyzer = CodebaseAnalyzer()

# ============================================================================
# FASTAPI BACKEND
# ============================================================================

# Create FastAPI app
api_app = FastAPI(
    title="Codebase Analysis API",
    description="Real production codebase analysis with graph-sitter integration",
    version="1.0.0"
)

# Add CORS middleware
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api_app.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start codebase analysis"""
    analysis_id = analyzer.generate_analysis_id()
    
    # Start analysis in background
    background_tasks.add_task(
        analyzer.analyze_codebase,
        analysis_id,
        request.repo_url,
        request.language
    )
    
    return AnalysisResponse(
        analysis_id=analysis_id,
        status="started",
        message="Analysis started successfully"
    )

@api_app.get("/analysis/{analysis_id}/status", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """Get analysis status"""
    if analysis_id not in analyzer.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyzer.analyses[analysis_id]
    return AnalysisStatus(
        analysis_id=analysis_id,
        status=analysis["status"],
        progress=analysis["progress"],
        error=analysis.get("error")
    )

@api_app.get("/analysis/{analysis_id}/summary")
async def get_analysis_summary(analysis_id: str):
    """Get analysis summary"""
    if analysis_id not in analyzer.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyzer.analyses[analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    results = analysis["results"]
    return {
        "analysis_id": analysis_id,
        "stats": results["stats"],
        "important_functions": results["important_functions"],
        "dead_code": results["dead_code"]
    }

@api_app.get("/analysis/{analysis_id}/tree")
async def get_analysis_tree(analysis_id: str):
    """Get interactive tree structure"""
    if analysis_id not in analyzer.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyzer.analyses[analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    results = analysis["results"]
    return {
        "analysis_id": analysis_id,
        "tree": results["tree_structure"],
        "total_issues": results["stats"]["total_issues"],
        "issues_by_severity": results["issues_by_severity"]
    }

@api_app.get("/analysis/{analysis_id}/issues")
async def get_analysis_issues(analysis_id: str):
    """Get detailed issues"""
    if analysis_id not in analyzer.analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyzer.analyses[analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    results = analysis["results"]
    return {
        "analysis_id": analysis_id,
        "issues": results["issues"],
        "total_issues": len(results["issues"])
    }

# ============================================================================
# REFLEX FRONTEND STATE
# ============================================================================

class DashboardState(rx.State):
    """Main dashboard state"""
    
    # Analysis state
    repo_url: str = ""
    analysis_id: str = ""
    analysis_status: str = "idle"
    progress: int = 0
    error_message: str = ""
    
    # Results state
    stats: Dict[str, Any] = {}
    tree_data: Dict[str, Any] = {}
    selected_node: Dict[str, Any] = {}
    issues: List[Dict[str, Any]] = []
    
    # UI state
    is_loading: bool = False
    show_results: bool = False
    
    async def start_analysis(self):
        """Start codebase analysis"""
        if not self.repo_url.strip():
            self.error_message = "Please enter a repository URL"
            return
        
        self.is_loading = True
        self.analysis_status = "starting"
        self.error_message = ""
        self.progress = 0
        
        try:
            # Call backend API
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/analyze",
                    json={"repo_url": self.repo_url, "language": "python"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.analysis_id = result["analysis_id"]
                    self.analysis_status = "running"
                    
                    # Start polling for status
                    await self.poll_analysis_status()
                else:
                    self.error_message = f"Failed to start analysis: {response.text}"
                    self.is_loading = False
        
        except Exception as e:
            self.error_message = f"Error starting analysis: {str(e)}"
            self.is_loading = False
    
    async def poll_analysis_status(self):
        """Poll analysis status until completion"""
        import httpx
        
        max_attempts = 60
        attempt = 0
        
        while attempt < max_attempts:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://localhost:8000/analysis/{self.analysis_id}/status"
                    )
                    
                    if response.status_code == 200:
                        status_data = response.json()
                        self.analysis_status = status_data["status"]
                        self.progress = status_data["progress"]
                        
                        if self.analysis_status == "completed":
                            await self.load_results()
                            break
                        elif self.analysis_status == "error":
                            self.error_message = status_data.get("error", "Analysis failed")
                            self.is_loading = False
                            break
                
                await asyncio.sleep(2)
                attempt += 1
                
            except Exception as e:
                self.error_message = f"Error polling status: {str(e)}"
                self.is_loading = False
                break
        
        if attempt >= max_attempts:
            self.error_message = "Analysis timed out"
            self.is_loading = False
    
    async def load_results(self):
        """Load analysis results"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Load summary
                summary_response = await client.get(
                    f"http://localhost:8000/analysis/{self.analysis_id}/summary"
                )
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    self.stats = summary_data["stats"]
                
                # Load tree
                tree_response = await client.get(
                    f"http://localhost:8000/analysis/{self.analysis_id}/tree"
                )
                if tree_response.status_code == 200:
                    tree_data = tree_response.json()
                    self.tree_data = tree_data["tree"]
                
                # Load issues
                issues_response = await client.get(
                    f"http://localhost:8000/analysis/{self.analysis_id}/issues"
                )
                if issues_response.status_code == 200:
                    issues_data = issues_response.json()
                    self.issues = issues_data["issues"]
            
            self.is_loading = False
            self.show_results = True
            
        except Exception as e:
            self.error_message = f"Error loading results: {str(e)}"
            self.is_loading = False
    
    def select_node(self, node: Dict[str, Any]):
        """Select a tree node"""
        self.selected_node = node

# ============================================================================
# REFLEX FRONTEND COMPONENTS
# ============================================================================

def header() -> rx.Component:
    """Dashboard header"""
    return rx.hstack(
        rx.heading("🔍 Codebase Analysis Dashboard", size="lg"),
        rx.spacer(),
        rx.text("Real graph-sitter integration", color="gray.600"),
        width="100%",
        padding="1rem",
        bg="white",
        border_bottom="1px solid #e2e8f0"
    )

def analysis_form() -> rx.Component:
    """Repository analysis form"""
    return rx.vstack(
        rx.heading("Analyze Repository", size="md"),
        rx.input(
            placeholder="Enter GitHub repository URL (e.g., https://github.com/user/repo)",
            value=DashboardState.repo_url,
            on_change=DashboardState.set_repo_url,
            width="100%",
            size="lg"
        ),
        rx.button(
            "Analyze Codebase",
            on_click=DashboardState.start_analysis,
            loading=DashboardState.is_loading,
            size="lg",
            width="100%",
            bg="blue.500",
            color="white",
            _hover={"bg": "blue.600"}
        ),
        rx.cond(
            DashboardState.error_message != "",
            rx.alert(
                rx.alert_icon(),
                rx.alert_title("Error"),
                rx.alert_description(DashboardState.error_message),
                status="error"
            )
        ),
        spacing="4",
        width="100%",
        max_width="600px"
    )

def progress_display() -> rx.Component:
    """Analysis progress display"""
    return rx.cond(
        DashboardState.is_loading,
        rx.vstack(
            rx.text(f"Status: {DashboardState.analysis_status}", font_weight="bold"),
            rx.progress(value=DashboardState.progress, width="100%"),
            rx.text(f"Progress: {DashboardState.progress}%"),
            spacing="2",
            width="100%"
        )
    )

def stats_display() -> rx.Component:
    """Statistics display"""
    return rx.cond(
        DashboardState.show_results,
        rx.grid(
            rx.stat(
                rx.stat_label("Files"),
                rx.stat_number(DashboardState.stats.get("total_files", 0)),
                rx.stat_help_text("Total files analyzed")
            ),
            rx.stat(
                rx.stat_label("Functions"),
                rx.stat_number(DashboardState.stats.get("total_functions", 0)),
                rx.stat_help_text("Functions found")
            ),
            rx.stat(
                rx.stat_label("Classes"),
                rx.stat_number(DashboardState.stats.get("total_classes", 0)),
                rx.stat_help_text("Classes discovered")
            ),
            rx.stat(
                rx.stat_label("Issues"),
                rx.stat_number(DashboardState.stats.get("total_issues", 0)),
                rx.stat_help_text("Issues detected")
            ),
            columns=4,
            spacing="4",
            width="100%"
        )
    )

def tree_node(node: Dict[str, Any]) -> rx.Component:
    """Render a tree node"""
    return rx.vstack(
        rx.hstack(
            rx.text("📁" if node.get("type") == "directory" else "📄"),
            rx.text(node.get("name", "Unknown")),
            rx.cond(
                node.get("issues", 0) > 0,
                rx.badge(f"{node.get('issues', 0)} issues", color_scheme="red")
            ),
            spacing="2",
            align="center",
            cursor="pointer",
            on_click=DashboardState.select_node(node),
            _hover={"bg": "gray.100"}
        ),
        spacing="1",
        align="start"
    )

def tree_display() -> rx.Component:
    """Tree structure display"""
    return rx.cond(
        DashboardState.show_results & (DashboardState.tree_data != {}),
        rx.vstack(
            rx.heading("Repository Structure", size="md"),
            rx.box(
                tree_node(DashboardState.tree_data),
                width="100%",
                max_height="400px",
                overflow_y="auto",
                border="1px solid #e2e8f0",
                border_radius="md",
                padding="4"
            ),
            spacing="4",
            width="100%"
        )
    )

def issues_display() -> rx.Component:
    """Issues display"""
    return rx.cond(
        DashboardState.show_results & (DashboardState.issues != []),
        rx.vstack(
            rx.heading("Issues Found", size="md"),
            rx.box(
                rx.foreach(
                    DashboardState.issues[:10],  # Show first 10 issues
                    lambda issue: rx.alert(
                        rx.alert_icon(),
                        rx.vstack(
                            rx.alert_title(issue["description"]),
                            rx.alert_description(f"File: {issue['file_path']}"),
                            rx.text(f"Suggestion: {issue['suggestion']}", font_size="sm"),
                            align="start",
                            spacing="1"
                        ),
                        status="warning",
                        margin_bottom="2"
                    )
                ),
                width="100%",
                max_height="400px",
                overflow_y="auto"
            ),
            spacing="4",
            width="100%"
        )
    )

def dashboard_page() -> rx.Component:
    """Main dashboard page"""
    return rx.container(
        rx.vstack(
            analysis_form(),
            progress_display(),
            stats_display(),
            rx.hstack(
                tree_display(),
                issues_display(),
                spacing="8",
                width="100%",
                align="start"
            ),
            spacing="8",
            width="100%",
            padding="2rem"
        ),
        max_width="1200px"
    )

# ============================================================================
# REFLEX APP SETUP
# ============================================================================

# Create Reflex app
app = rx.App()

def index() -> rx.Component:
    """Main page"""
    return rx.vstack(
        header(),
        dashboard_page(),
        min_height="100vh",
        width="100%",
        spacing="0",
        align="stretch"
    )

app.add_page(index, route="/", title="Codebase Analysis Dashboard")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def start_backend():
    """Start FastAPI backend"""
    uvicorn.run(api_app, host="0.0.0.0", port=8000, log_level="info")

def start_frontend():
    """Start Reflex frontend"""
    import subprocess
    subprocess.run(["reflex", "run", "--frontend-port", "3000", "--backend-port", "8001"])

def main():
    """Main entry point"""
    print("🔥 CONSOLIDATED CODEBASE ANALYSIS DASHBOARD")
    print("=" * 60)
    print("🚀 Starting backend server...")
    
    # Start backend in thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    print("✅ Backend started on http://localhost:8000")
    print("🎨 Starting frontend dashboard...")
    
    # Start frontend (this will block)
    start_frontend()

if __name__ == "__main__":
    main()
