"""
Pydantic models for the Graph-Sitter Code Analytics API.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator, ConfigDict


class AnalyzeRequest(BaseModel):
    """Request model for repository analysis."""
    
    repo_url: Optional[str] = Field(
        None, 
        description="URL of the GitHub repository to analyze"
    )
    branch: str = Field(
        "main", 
        description="Branch to analyze"
    )
    local_path: Optional[str] = Field(
        None, 
        description="Local path to the repository"
    )
    config: Optional[Dict[str, Any]] = Field(
        None, 
        description="Configuration options for the analysis"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "repo_url": "https://github.com/username/repo",
                "branch": "main",
                "config": {"log_level": "info"}
            }
        }
    )

    @validator("repo_url")
    def validate_repo_url(cls, v):
        """Validate that the repository URL is from GitHub."""
        if v and not (
            v.startswith("https://github.com/") or v.startswith("git@github.com:")
        ):
            raise ValueError("Only GitHub repositories are supported")
        return v


class ErrorItem(BaseModel):
    """Model for code errors found during analysis."""
    
    id: str = Field(..., description="Unique identifier for the error")
    type: str = Field(..., description="Type of error")
    severity: str = Field(..., description="Severity level (critical, major, minor)")
    file: str = Field(..., description="File path where the error was found")
    symbol: str = Field(..., description="Symbol name where the error was found")
    line: int = Field(..., description="Line number where the error was found")
    message: str = Field(..., description="Error message")
    context: str = Field(..., description="Context information about the error")
    suggestion: Optional[str] = Field(None, description="Suggested fix for the error")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "1",
                "type": "missing_type",
                "severity": "major",
                "file": "src/utils.py",
                "symbol": "process_data",
                "line": 45,
                "message": "Parameter 'data' missing type annotation",
                "context": "Function parameter lacks type annotation",
                "suggestion": "Add type annotation to improve code clarity"
            }
        }
    )


class DeadCodeItem(BaseModel):
    """Model for dead code items found during analysis."""
    
    type: str = Field(..., description="Type of dead code (unused_function, unused_class, unused_import)")
    name: str = Field(..., description="Name of the dead code item")
    file: str = Field(..., description="File path where the dead code was found")
    line: int = Field(..., description="Line number where the dead code was found")
    reason: str = Field(..., description="Reason why the code is considered dead")
    last_modified: Optional[str] = Field(None, description="Last modification date of the code")
    safe_to_remove: bool = Field(True, description="Whether it's safe to remove the code")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "unused_function",
                "name": "legacy_process",
                "file": "src/legacy.py",
                "line": 123,
                "reason": "No call sites found",
                "safe_to_remove": True
            }
        }
    )


class EntryPoint(BaseModel):
    """Model for entry points found during analysis."""
    
    name: str = Field(..., description="Name of the entry point")
    type: str = Field(..., description="Type of entry point (function, class, etc.)")
    file: str = Field(..., description="File path where the entry point was found")
    line: int = Field(..., description="Line number where the entry point was found")
    description: str = Field(..., description="Description of the entry point")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "main",
                "type": "function",
                "file": "src/main.py",
                "line": 1,
                "description": "Main entry point"
            }
        }
    )


class CodebaseMetrics(BaseModel):
    """Model for codebase metrics."""
    
    files: int = Field(..., description="Number of files in the codebase")
    functions: int = Field(..., description="Number of functions in the codebase")
    classes: int = Field(..., description="Number of classes in the codebase")
    imports: int = Field(..., description="Number of imports in the codebase")
    lines_of_code: int = Field(..., description="Total lines of code in the codebase")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "files": 25,
                "functions": 150,
                "classes": 45,
                "imports": 89,
                "lines_of_code": 3500
            }
        }
    )


class FunctionMetrics(BaseModel):
    """Model for function metrics."""
    
    complexity: int = Field(..., description="Cyclomatic complexity of the function")
    parameters: int = Field(..., description="Number of parameters in the function")
    lines: int = Field(..., description="Number of lines in the function")
    calls_made: int = Field(..., description="Number of function calls made by the function")
    times_called: int = Field(..., description="Number of times the function is called")
    is_recursive: bool = Field(..., description="Whether the function is recursive")
    has_decorators: bool = Field(..., description="Whether the function has decorators")
    is_async: bool = Field(..., description="Whether the function is asynchronous")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "complexity": 8,
                "parameters": 3,
                "lines": 25,
                "calls_made": 5,
                "times_called": 10,
                "is_recursive": False,
                "has_decorators": True,
                "is_async": False
            }
        }
    )


class ClassMetrics(BaseModel):
    """Model for class metrics."""
    
    methods: int = Field(..., description="Number of methods in the class")
    attributes: int = Field(..., description="Number of attributes in the class")
    inheritance_depth: int = Field(..., description="Depth of inheritance hierarchy")
    subclasses: int = Field(..., description="Number of subclasses")
    is_abstract: bool = Field(..., description="Whether the class is abstract")
    is_dataclass: bool = Field(False, description="Whether the class is a dataclass")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "methods": 8,
                "attributes": 5,
                "inheritance_depth": 2,
                "subclasses": 3,
                "is_abstract": False,
                "is_dataclass": True
            }
        }
    )


class ImportMetrics(BaseModel):
    """Model for import metrics."""
    
    total_imports: int = Field(..., description="Total number of imports")
    external_imports: int = Field(..., description="Number of external imports")
    circular_imports: int = Field(..., description="Number of circular imports")
    unused_imports: int = Field(..., description="Number of unused imports")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_imports": 50,
                "external_imports": 30,
                "circular_imports": 2,
                "unused_imports": 5
            }
        }
    )


class ComplexityMetrics(BaseModel):
    """Model for complexity metrics."""
    
    halstead_volume: float = Field(..., description="Halstead volume")
    halstead_difficulty: float = Field(..., description="Halstead difficulty")
    halstead_effort: float = Field(..., description="Halstead effort")
    unique_operators: int = Field(..., description="Number of unique operators")
    unique_operands: int = Field(..., description="Number of unique operands")
    total_operators: int = Field(..., description="Total number of operators")
    total_operands: int = Field(..., description="Total number of operands")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "halstead_volume": 250.5,
                "halstead_difficulty": 12.3,
                "halstead_effort": 3080.0,
                "unique_operators": 8,
                "unique_operands": 15,
                "total_operators": 30,
                "total_operands": 45
            }
        }
    )


class TreeNode(BaseModel):
    """Model for tree nodes in the codebase structure."""
    
    name: str = Field(..., description="Name of the node")
    type: str = Field(..., description="Type of the node (file, directory, function, class)")
    path: str = Field(..., description="Path to the node")
    children: Optional[List["TreeNode"]] = Field(None, description="Child nodes")
    errors: Optional[Dict[str, int]] = Field(None, description="Error counts by severity")
    metrics: Optional[Dict[str, int]] = Field(None, description="Metrics for the node")
    summary: Optional[str] = Field(None, description="Summary of the node")
    is_entrypoint: bool = Field(False, description="Whether the node is an entry point")
    complexity: Optional[int] = Field(None, description="Complexity of the node")
    dependencies: Optional[List[str]] = Field(None, description="Dependencies of the node")
    usages: Optional[List[str]] = Field(None, description="Usages of the node")
    function_metrics: Optional[FunctionMetrics] = Field(None, description="Function metrics")
    class_metrics: Optional[ClassMetrics] = Field(None, description="Class metrics")
    source_code: Optional[str] = Field(None, description="Source code of the node")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "main.py",
                "type": "file",
                "path": "/src/main.py",
                "metrics": {"lines": 250, "functions": 8, "classes": 2},
                "errors": {"critical": 0, "major": 2, "minor": 5}
            }
        }
    )


# Update forward references for recursive models
TreeNode.model_rebuild()


class ManipulationRequest(BaseModel):
    """Request model for symbol manipulation."""
    
    action: str = Field(..., description="Action to perform (move, rename, delete, extract)")
    target_path: str = Field(..., description="Path to the target symbol")
    destination: Optional[str] = Field(None, description="Destination path for move or extract")
    new_name: Optional[str] = Field(None, description="New name for rename")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action": "move",
                "target_path": "src/utils.py:process_data",
                "destination": "src/core/utils.py"
            }
        }
    )


class ManipulationResponse(BaseModel):
    """Response model for symbol manipulation."""
    
    success: bool = Field(..., description="Whether the manipulation was successful")
    message: str = Field(..., description="Message describing the result")
    changes: List[Dict[str, Any]] = Field(..., description="List of changes made")
    warnings: Optional[List[str]] = Field(None, description="List of warnings")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Successfully moved process_data to src/core/utils.py",
                "changes": [
                    {
                        "type": "move",
                        "symbol": "process_data",
                        "from": "src/utils.py",
                        "to": "src/core/utils.py",
                        "description": "Moved process_data to src/core/utils.py"
                    }
                ]
            }
        }
    )


class AnalysisResponse(BaseModel):
    """Response model for repository analysis."""
    
    analysis_id: str = Field(..., description="Unique identifier for the analysis")
    status: str = Field(..., description="Status of the analysis (completed, failed)")
    codebase_summary: CodebaseMetrics = Field(..., description="Summary metrics for the codebase")
    tree_structure: Dict[str, Any] = Field(..., description="Tree structure of the codebase")
    errors: Dict[str, int] = Field(..., description="Error counts by severity")
    dead_code: Dict[str, int] = Field(..., description="Dead code counts by type")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "codebase_summary": {
                    "files": 25,
                    "functions": 150,
                    "classes": 45,
                    "imports": 89,
                    "lines_of_code": 3500
                },
                "errors": {
                    "critical": 0,
                    "major": 5,
                    "minor": 15,
                    "total": 20
                },
                "dead_code": {
                    "unused_functions": 3,
                    "unused_classes": 1,
                    "unused_imports": 8,
                    "total": 12
                }
            }
        }
    )

