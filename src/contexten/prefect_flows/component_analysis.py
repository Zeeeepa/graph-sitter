"""
Component analysis flow for systematic code review and optimization.

This flow handles the detailed analysis of individual components
as defined in the Linear sub-issues for comprehensive code review.
"""

from typing import Dict, List, Optional
from prefect import flow, task, get_run_logger
from codegen import Agent

from .autonomous_cicd import initialize_codegen_agent, execute_codegen_task


@task
def get_component_files(component: str) -> List[str]:
    """Get list of files to analyze for a specific component."""
    logger = get_run_logger()
    
    component_file_mappings = {
        "contexten/agents": [
            "src/contexten/agents/chat_agent.py",
            "src/contexten/agents/code_agent.py", 
            "src/contexten/agents/langchain/agent.py",
            "src/contexten/agents/langchain/graph.py",
            "src/contexten/agents/utils.py",
            "src/contexten/agents/data.py",
            "src/contexten/agents/loggers.py",
            "src/contexten/agents/tracer.py"
        ],
        "graph_sitter/gscli": [
            "src/graph_sitter/gscli/cli.py",
            "src/graph_sitter/gscli/backend/utils.py",
            "src/graph_sitter/gscli/backend/typestub_utils.py",
            "src/graph_sitter/gscli/generate/commands.py",
            "src/graph_sitter/gscli/generate/runner_imports.py",
            "src/graph_sitter/gscli/generate/system_prompt.py",
            "src/graph_sitter/gscli/generate/utils.py"
        ],
        "graph_sitter/git": [
            "src/graph_sitter/git/utils/remote_progress.py",
            "src/graph_sitter/git/utils/file_utils.py",
            "src/graph_sitter/git/utils/format.py",
            "src/graph_sitter/git/utils/pr_review.py",
            "src/graph_sitter/git/utils/clone.py"
        ],
        "graph_sitter/visualizations": [
            "src/graph_sitter/visualizations/viz_utils.py",
            "src/graph_sitter/visualizations/enums.py",
            "src/graph_sitter/visualizations/visualization_manager.py"
        ],
        "build_system": [
            "src/gsbuild/build.py",
            "pyproject.toml",
            "hatch.toml", 
            "ruff.toml",
            "mypy.ini",
            ".pre-commit-config.yaml"
        ]
    }
    
    files = component_file_mappings.get(component, [])
    logger.info(f"Found {len(files)} files for component {component}")
    return files


@task
def analyze_code_quality(component: str, files: List[str]) -> Dict:
    """Analyze code quality for a specific component."""
    logger = get_run_logger()
    
    analysis_prompt = f"""
    Perform a comprehensive code quality analysis for the {component} component.
    
    Files to analyze: {', '.join(files)}
    
    Please analyze for:
    1. Unused imports and functions
    2. Incorrect parameter types/defaults
    3. Error handling patterns
    4. Code duplication
    5. Performance issues
    6. Security vulnerabilities
    7. Documentation gaps
    
    Provide specific recommendations for improvements and identify any dead code.
    """
    
    logger.info(f"Starting code quality analysis for {component}")
    
    return {
        "component": component,
        "analysis_type": "code_quality",
        "prompt": analysis_prompt,
        "files": files
    }


@task
def analyze_architecture(component: str, files: List[str]) -> Dict:
    """Analyze architecture and design patterns for a component."""
    logger = get_run_logger()
    
    analysis_prompt = f"""
    Perform an architectural analysis for the {component} component.
    
    Files to analyze: {', '.join(files)}
    
    Please analyze for:
    1. Design pattern consistency
    2. Separation of concerns
    3. Dependency management
    4. Interface design
    5. Modularity and coupling
    6. Scalability considerations
    7. Integration points
    
    Identify architectural improvements and refactoring opportunities.
    """
    
    logger.info(f"Starting architectural analysis for {component}")
    
    return {
        "component": component,
        "analysis_type": "architecture",
        "prompt": analysis_prompt,
        "files": files
    }


@task
def analyze_integration_points(component: str, files: List[str]) -> Dict:
    """Analyze integration points and external dependencies."""
    logger = get_run_logger()
    
    analysis_prompt = f"""
    Analyze integration points and external dependencies for the {component} component.
    
    Files to analyze: {', '.join(files)}
    
    Please analyze for:
    1. External API integrations
    2. Database connections
    3. File system operations
    4. Network communications
    5. Third-party library usage
    6. Configuration management
    7. Error handling in integrations
    
    Identify potential integration issues and improvement opportunities.
    """
    
    logger.info(f"Starting integration analysis for {component}")
    
    return {
        "component": component,
        "analysis_type": "integration",
        "prompt": analysis_prompt,
        "files": files
    }


@flow(name="component-analysis")
def component_analysis_flow(component: str, linear_issue_id: Optional[str] = None):
    """
    Comprehensive component analysis flow.
    
    Args:
        component: The component to analyze (e.g., "contexten/agents")
        linear_issue_id: Optional Linear issue ID for tracking
    """
    logger = get_run_logger()
    logger.info(f"Starting component analysis for: {component}")
    
    # Initialize Codegen agent
    agent = initialize_codegen_agent()
    
    # Get files for the component
    files = get_component_files(component)
    
    if not files:
        logger.warning(f"No files found for component: {component}")
        return {"status": "error", "message": "No files found for component"}
    
    # Perform different types of analysis
    code_quality_analysis = analyze_code_quality(component, files)
    architecture_analysis = analyze_architecture(component, files)
    integration_analysis = analyze_integration_points(component, files)
    
    # Execute analyses via Codegen SDK
    results = []
    
    for analysis in [code_quality_analysis, architecture_analysis, integration_analysis]:
        context = {
            "component": component,
            "analysis_type": analysis["analysis_type"],
            "linear_issue_id": linear_issue_id,
            "files": analysis["files"]
        }
        
        result = execute_codegen_task(
            agent=agent,
            prompt=analysis["prompt"],
            context=context
        )
        
        result["analysis_type"] = analysis["analysis_type"]
        results.append(result)
    
    logger.info(f"Completed component analysis for {component}")
    
    return {
        "component": component,
        "linear_issue_id": linear_issue_id,
        "files_analyzed": len(files),
        "analyses_completed": len(results),
        "results": results
    }


if __name__ == "__main__":
    # For testing purposes
    component_analysis_flow("contexten/agents")

