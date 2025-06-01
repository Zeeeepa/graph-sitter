"""Dashboard API for serving codebase analysis data to frontend applications."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import (
    CodebaseAnalyzer,
    analyze_codebase,
    get_function_context,
    IssueSeverity,
    IssueCategory,
    CodeIssue,
    AnalysisNode
)

logger = logging.getLogger(__name__)

# Pydantic models for API responses
class IssueResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    category: str
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    impact_score: float = 0.0
    affected_symbols: List[str] = []
    suggested_fix: Optional[str] = None
    ai_analysis: Optional[str] = None


class AnalysisNodeResponse(BaseModel):
    id: str
    name: str
    type: str
    summary: Dict[str, Any]
    issues: List[IssueResponse]
    children: List['AnalysisNodeResponse'] = []
    metadata: Dict[str, Any]
    expandable: bool = True


class CodebaseMetrics(BaseModel):
    total_files: int
    total_functions: int
    total_classes: int
    total_symbols: int
    total_imports: int
    total_nodes: int
    total_edges: int


class AnalysisSummary(BaseModel):
    codebase_metrics: CodebaseMetrics
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_category: Dict[str, int]
    analysis_timestamp: str


class FunctionContextResponse(BaseModel):
    implementation: Dict[str, Any]
    dependencies: List[Dict[str, Any]]
    usages: List[Dict[str, Any]]
    call_sites: List[Dict[str, Any]]
    function_calls: List[Dict[str, Any]]


class BlastRadiusResponse(BaseModel):
    symbol_name: str
    symbol_type: str
    affected_symbols: List[str]
    impact_score: float


# Global codebase instance (in production, this would be managed differently)
_codebase_cache: Dict[str, Codebase] = {}
_analyzer_cache: Dict[str, CodebaseAnalyzer] = {}


def create_dashboard_api() -> FastAPI:
    """Create FastAPI application for dashboard API."""
    
    app = FastAPI(
        title="Codebase Analysis Dashboard API",
        description="API for serving codebase analysis data to dashboard applications",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Codebase Analysis Dashboard API",
            "version": "1.0.0",
            "endpoints": {
                "analysis": "/analysis/{codebase_id}",
                "issues": "/issues/{codebase_id}",
                "dashboard": "/dashboard/{codebase_id}",
                "function_context": "/function/{codebase_id}/{function_name}",
                "blast_radius": "/blast_radius/{codebase_id}/{symbol_name}",
                "metrics": "/metrics/{codebase_id}"
            }
        }
    
    @app.post("/codebase/{codebase_id}")
    async def initialize_codebase(codebase_id: str, path: str):
        """Initialize a codebase for analysis."""
        try:
            codebase = Codebase(path)
            analyzer = CodebaseAnalyzer(codebase)
            
            _codebase_cache[codebase_id] = codebase
            _analyzer_cache[codebase_id] = analyzer
            
            return {
                "message": f"Codebase {codebase_id} initialized successfully",
                "path": path,
                "metrics": {
                    "files": len(list(codebase.files)),
                    "functions": len(list(codebase.functions)),
                    "classes": len(list(codebase.classes))
                }
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to initialize codebase: {str(e)}")
    
    @app.get("/analysis/{codebase_id}", response_model=AnalysisSummary)
    async def get_analysis_summary(codebase_id: str):
        """Get comprehensive analysis summary for a codebase."""
        if codebase_id not in _codebase_cache:
            raise HTTPException(status_code=404, detail="Codebase not found")
        
        try:
            codebase = _codebase_cache[codebase_id]
            analysis = analyze_codebase(codebase)
            
            return AnalysisSummary(
                codebase_metrics=CodebaseMetrics(**analysis["summary"]),
                total_issues=analysis["metrics"]["total_issues"],
                issues_by_severity=analysis["metrics"]["issues_by_severity"],
                issues_by_category=analysis["metrics"]["issues_by_category"],
                analysis_timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    @app.get("/issues/{codebase_id}", response_model=List[IssueResponse])
    async def get_issues(
        codebase_id: str,
        severity: Optional[str] = Query(None, description="Filter by severity"),
        category: Optional[str] = Query(None, description="Filter by category"),
        limit: int = Query(100, description="Maximum number of issues to return")
    ):
        """Get issues for a codebase with optional filtering."""
        if codebase_id not in _analyzer_cache:
            raise HTTPException(status_code=404, detail="Codebase not found")
        
        try:
            analyzer = _analyzer_cache[codebase_id]
            issues = analyzer.detect_issues()
            
            # Apply filters
            if severity:
                try:
                    severity_enum = IssueSeverity(severity.lower())
                    issues = [i for i in issues if i.severity == severity_enum]
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
            
            if category:
                try:
                    category_enum = IssueCategory(category.lower())
                    issues = [i for i in issues if i.category == category_enum]
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
            
            # Apply limit
            issues = issues[:limit]
            
            # Convert to response models
            return [
                IssueResponse(
                    id=issue.id,
                    title=issue.title,
                    description=issue.description,
                    severity=issue.severity.value,
                    category=issue.category.value,
                    file_path=issue.file_path,
                    line_start=issue.line_start,
                    line_end=issue.line_end,
                    symbol_name=issue.symbol_name,
                    symbol_type=issue.symbol_type,
                    impact_score=issue.impact_score,
                    affected_symbols=issue.affected_symbols,
                    suggested_fix=issue.suggested_fix,
                    ai_analysis=issue.ai_analysis
                )
                for issue in issues
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get issues: {str(e)}")
    
    @app.get("/dashboard/{codebase_id}", response_model=AnalysisNodeResponse)
    async def get_dashboard_data(codebase_id: str):
        """Get hierarchical dashboard data for expandable UI."""
        if codebase_id not in _analyzer_cache:
            raise HTTPException(status_code=404, detail="Codebase not found")
        
        try:
            analyzer = _analyzer_cache[codebase_id]
            dashboard_data = analyzer.generate_dashboard_data()
            
            def convert_node(node: AnalysisNode) -> AnalysisNodeResponse:
                return AnalysisNodeResponse(
                    id=node.id,
                    name=node.name,
                    type=node.type,
                    summary=node.summary,
                    issues=[
                        IssueResponse(
                            id=issue.id,
                            title=issue.title,
                            description=issue.description,
                            severity=issue.severity.value,
                            category=issue.category.value,
                            file_path=issue.file_path,
                            line_start=issue.line_start,
                            line_end=issue.line_end,
                            symbol_name=issue.symbol_name,
                            symbol_type=issue.symbol_type,
                            impact_score=issue.impact_score,
                            affected_symbols=issue.affected_symbols,
                            suggested_fix=issue.suggested_fix,
                            ai_analysis=issue.ai_analysis
                        )
                        for issue in node.issues
                    ],
                    children=[convert_node(child) for child in node.children],
                    metadata=node.metadata,
                    expandable=node.expandable
                )
            
            return convert_node(dashboard_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate dashboard data: {str(e)}")
    
    @app.get("/function/{codebase_id}/{function_name}", response_model=FunctionContextResponse)
    async def get_function_context(codebase_id: str, function_name: str):
        """Get detailed context for a specific function."""
        if codebase_id not in _codebase_cache:
            raise HTTPException(status_code=404, detail="Codebase not found")
        
        try:
            codebase = _codebase_cache[codebase_id]
            
            # Find the function
            function = None
            for func in codebase.functions:
                if func.name == function_name:
                    function = func
                    break
            
            if not function:
                raise HTTPException(status_code=404, detail=f"Function '{function_name}' not found")
            
            context = get_function_context(function)
            
            return FunctionContextResponse(**context)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get function context: {str(e)}")
    
    @app.get("/blast_radius/{codebase_id}/{symbol_name}", response_model=BlastRadiusResponse)
    async def get_blast_radius(codebase_id: str, symbol_name: str, symbol_type: str = "Function"):
        """Get blast radius analysis for a symbol."""
        if codebase_id not in _analyzer_cache:
            raise HTTPException(status_code=404, detail="Codebase not found")
        
        try:
            analyzer = _analyzer_cache[codebase_id]
            affected_symbols = analyzer.get_blast_radius(symbol_name, symbol_type)
            
            # Calculate impact score
            impact_score = len(affected_symbols)
            
            return BlastRadiusResponse(
                symbol_name=symbol_name,
                symbol_type=symbol_type,
                affected_symbols=affected_symbols,
                impact_score=impact_score
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to calculate blast radius: {str(e)}")
    
    @app.get("/metrics/{codebase_id}", response_model=CodebaseMetrics)
    async def get_codebase_metrics(codebase_id: str):
        """Get basic codebase metrics."""
        if codebase_id not in _codebase_cache:
            raise HTTPException(status_code=404, detail="Codebase not found")
        
        try:
            codebase = _codebase_cache[codebase_id]
            
            return CodebaseMetrics(
                total_files=len(list(codebase.files)),
                total_functions=len(list(codebase.functions)),
                total_classes=len(list(codebase.classes)),
                total_symbols=len(list(codebase.symbols)),
                total_imports=len(list(codebase.imports)),
                total_nodes=len(codebase.ctx.get_nodes()),
                total_edges=len(codebase.ctx.edges)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
    
    @app.post("/analyze/{codebase_id}/ai")
    async def analyze_issue_with_ai(codebase_id: str, issue_id: str):
        """Analyze a specific issue with AI."""
        if codebase_id not in _analyzer_cache:
            raise HTTPException(status_code=404, detail="Codebase not found")
        
        try:
            analyzer = _analyzer_cache[codebase_id]
            issues = analyzer.detect_issues()
            
            # Find the issue
            issue = None
            for i in issues:
                if i.id == issue_id:
                    issue = i
                    break
            
            if not issue:
                raise HTTPException(status_code=404, detail=f"Issue '{issue_id}' not found")
            
            ai_analysis = await analyzer.analyze_with_ai(issue)
            
            return {
                "issue_id": issue_id,
                "ai_analysis": ai_analysis,
                "timestamp": datetime.now().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
    
    @app.delete("/codebase/{codebase_id}")
    async def cleanup_codebase(codebase_id: str):
        """Clean up codebase from cache."""
        if codebase_id in _codebase_cache:
            del _codebase_cache[codebase_id]
        if codebase_id in _analyzer_cache:
            del _analyzer_cache[codebase_id]
        
        return {"message": f"Codebase {codebase_id} cleaned up successfully"}
    
    return app


# Create the FastAPI app instance
app = create_dashboard_api()


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Dashboard API Server...")
    print("📊 Dashboard endpoints available at:")
    print("   - http://localhost:8000/docs (Swagger UI)")
    print("   - http://localhost:8000/redoc (ReDoc)")
    print("   - http://localhost:8000/ (API info)")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

