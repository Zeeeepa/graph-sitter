"""
Prefect Tasks for Autonomous CI/CD Operations

This module defines individual tasks that can be composed into workflows
for autonomous CI/CD operations.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import json
import logging

from codegen import Agent as CodegenAgent
from prefect import task, get_run_logger
from prefect.artifacts import create_markdown_artifact
from prefect.blocks.system import Secret

from .config import get_config, TaskConfig
from contexten.extensions.github.enhanced_client import EnhancedGitHubClient
from contexten.extensions.linear.enhanced_client import EnhancedLinearClient
from graph_sitter import Codebase


@task(
    name="analyze-codebase",
    description="Analyze codebase for issues and optimization opportunities",
    tags=["analysis", "codebase"],
    retries=3,
    retry_delay_seconds=60,
)
async def analyze_codebase_task(
    repo_url: str,
    branch: str = "main",
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """
    Analyze a codebase for various issues and opportunities.
    
    Args:
        repo_url: Repository URL to analyze
        branch: Branch to analyze (default: main)
        analysis_type: Type of analysis (comprehensive, security, performance)
    
    Returns:
        Dictionary containing analysis results
    """
    logger = get_run_logger()
    logger.info(f"Starting codebase analysis for {repo_url} on branch {branch}")
    
    try:
        # Initialize codebase
        codebase = Codebase.from_repo(repo_url, branch=branch)
        
        analysis_results = {
            "repo_url": repo_url,
            "branch": branch,
            "analysis_type": analysis_type,
            "timestamp": datetime.utcnow().isoformat(),
            "issues": [],
            "opportunities": [],
            "metrics": {},
            "recommendations": []
        }
        
        if analysis_type in ["comprehensive", "security"]:
            # Security analysis
            security_issues = await _analyze_security(codebase)
            analysis_results["issues"].extend(security_issues)
            logger.info(f"Found {len(security_issues)} security issues")
        
        if analysis_type in ["comprehensive", "performance"]:
            # Performance analysis
            performance_issues = await _analyze_performance(codebase)
            analysis_results["issues"].extend(performance_issues)
            logger.info(f"Found {len(performance_issues)} performance issues")
        
        if analysis_type == "comprehensive":
            # Code quality analysis
            quality_issues = await _analyze_code_quality(codebase)
            analysis_results["issues"].extend(quality_issues)
            
            # Dependency analysis
            dependency_issues = await _analyze_dependencies(codebase)
            analysis_results["issues"].extend(dependency_issues)
            
            # Generate metrics
            analysis_results["metrics"] = await _generate_metrics(codebase)
            
            logger.info(f"Comprehensive analysis complete. Total issues: {len(analysis_results['issues'])}")
        
        # Create analysis artifact
        await create_markdown_artifact(
            key=f"codebase-analysis-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            markdown=_format_analysis_report(analysis_results),
            description=f"Codebase analysis report for {repo_url}"
        )
        
        return analysis_results
        
    except Exception as e:
        logger.error(f"Codebase analysis failed: {str(e)}")
        raise


@task(
    name="generate-fixes",
    description="Generate fixes for identified issues using Codegen SDK",
    tags=["fixes", "codegen"],
    retries=2,
    retry_delay_seconds=120,
)
async def generate_fixes_task(
    analysis_results: Dict[str, Any],
    confidence_threshold: float = 0.75
) -> Dict[str, Any]:
    """
    Generate fixes for issues using the Codegen SDK.
    
    Args:
        analysis_results: Results from codebase analysis
        confidence_threshold: Minimum confidence for auto-fixes
    
    Returns:
        Dictionary containing generated fixes
    """
    logger = get_run_logger()
    config = get_config()
    
    if not config.codegen_org_id or not config.codegen_token:
        raise ValueError("Codegen credentials not configured")
    
    logger.info(f"Generating fixes for {len(analysis_results['issues'])} issues")
    
    try:
        # Initialize Codegen agent
        agent = CodegenAgent(
            org_id=config.codegen_org_id,
            token=config.codegen_token
        )
        
        fixes = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_issues": len(analysis_results["issues"]),
            "generated_fixes": [],
            "skipped_fixes": [],
            "confidence_threshold": confidence_threshold
        }
        
        for issue in analysis_results["issues"]:
            try:
                # Generate fix using Codegen
                fix_prompt = _create_fix_prompt(issue, analysis_results)
                
                logger.info(f"Generating fix for issue: {issue.get('title', 'Unknown')}")
                
                task = agent.run(prompt=fix_prompt)
                
                # Wait for completion with timeout
                max_wait = 300  # 5 minutes
                start_time = datetime.utcnow()
                
                while task.status not in ["completed", "failed"] and \
                      (datetime.utcnow() - start_time).seconds < max_wait:
                    await asyncio.sleep(10)
                    task.refresh()
                
                if task.status == "completed":
                    fix_data = {
                        "issue_id": issue.get("id"),
                        "issue_title": issue.get("title"),
                        "fix_description": task.result,
                        "confidence": _calculate_fix_confidence(issue, task.result),
                        "task_id": task.id,
                        "generated_at": datetime.utcnow().isoformat()
                    }
                    
                    if fix_data["confidence"] >= confidence_threshold:
                        fixes["generated_fixes"].append(fix_data)
                        logger.info(f"Generated high-confidence fix for {issue.get('title')}")
                    else:
                        fixes["skipped_fixes"].append({
                            **fix_data,
                            "skip_reason": f"Low confidence ({fix_data['confidence']:.2f})"
                        })
                        logger.info(f"Skipped low-confidence fix for {issue.get('title')}")
                else:
                    fixes["skipped_fixes"].append({
                        "issue_id": issue.get("id"),
                        "issue_title": issue.get("title"),
                        "skip_reason": f"Fix generation failed: {task.status}",
                        "generated_at": datetime.utcnow().isoformat()
                    })
                    logger.warning(f"Fix generation failed for {issue.get('title')}")
                    
            except Exception as e:
                logger.error(f"Error generating fix for issue {issue.get('id')}: {str(e)}")
                fixes["skipped_fixes"].append({
                    "issue_id": issue.get("id"),
                    "issue_title": issue.get("title"),
                    "skip_reason": f"Exception: {str(e)}",
                    "generated_at": datetime.utcnow().isoformat()
                })
        
        logger.info(f"Generated {len(fixes['generated_fixes'])} fixes, skipped {len(fixes['skipped_fixes'])}")
        
        # Create fixes artifact
        await create_markdown_artifact(
            key=f"generated-fixes-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            markdown=_format_fixes_report(fixes),
            description="Generated fixes report"
        )
        
        return fixes
        
    except Exception as e:
        logger.error(f"Fix generation failed: {str(e)}")
        raise


@task(
    name="apply-fixes",
    description="Apply generated fixes to the codebase",
    tags=["fixes", "apply"],
    retries=1,
    retry_delay_seconds=60,
)
async def apply_fixes_task(
    fixes: Dict[str, Any],
    repo_url: str,
    create_pr: bool = True
) -> Dict[str, Any]:
    """
    Apply generated fixes to the codebase.
    
    Args:
        fixes: Generated fixes from generate_fixes_task
        repo_url: Repository URL
        create_pr: Whether to create a PR for the fixes
    
    Returns:
        Dictionary containing application results
    """
    logger = get_run_logger()
    config = get_config()
    
    logger.info(f"Applying {len(fixes['generated_fixes'])} fixes to {repo_url}")
    
    try:
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "repo_url": repo_url,
            "applied_fixes": [],
            "failed_fixes": [],
            "pr_url": None,
            "branch_name": None
        }
        
        if not fixes["generated_fixes"]:
            logger.info("No fixes to apply")
            return results
        
        # Create branch for fixes
        branch_name = f"autonomous-fixes-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        results["branch_name"] = branch_name
        
        # Initialize GitHub client
        github_client = EnhancedGitHubClient(token=config.github_token)
        
        # Apply each fix
        for fix in fixes["generated_fixes"]:
            try:
                # Apply fix logic would go here
                # This is a placeholder for the actual fix application
                logger.info(f"Applying fix for {fix['issue_title']}")
                
                # Simulate fix application
                results["applied_fixes"].append({
                    "issue_id": fix["issue_id"],
                    "issue_title": fix["issue_title"],
                    "applied_at": datetime.utcnow().isoformat(),
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"Failed to apply fix for {fix['issue_title']}: {str(e)}")
                results["failed_fixes"].append({
                    "issue_id": fix["issue_id"],
                    "issue_title": fix["issue_title"],
                    "error": str(e),
                    "failed_at": datetime.utcnow().isoformat()
                })
        
        # Create PR if requested and fixes were applied
        if create_pr and results["applied_fixes"]:
            pr_title = f"🤖 Autonomous fixes - {len(results['applied_fixes'])} issues resolved"
            pr_body = _create_pr_description(results, fixes)
            
            # Create PR logic would go here
            results["pr_url"] = f"https://github.com/example/repo/pull/123"  # Placeholder
            logger.info(f"Created PR: {results['pr_url']}")
        
        logger.info(f"Applied {len(results['applied_fixes'])} fixes, {len(results['failed_fixes'])} failed")
        
        return results
        
    except Exception as e:
        logger.error(f"Fix application failed: {str(e)}")
        raise


@task(
    name="monitor-performance",
    description="Monitor system performance and detect regressions",
    tags=["performance", "monitoring"],
    retries=2,
    retry_delay_seconds=30,
)
async def monitor_performance_task(
    repo_url: str,
    baseline_branch: str = "main",
    current_branch: str = "main"
) -> Dict[str, Any]:
    """
    Monitor system performance and detect regressions.
    
    Args:
        repo_url: Repository URL
        baseline_branch: Baseline branch for comparison
        current_branch: Current branch to analyze
    
    Returns:
        Dictionary containing performance metrics
    """
    logger = get_run_logger()
    logger.info(f"Monitoring performance for {repo_url}")
    
    try:
        performance_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "repo_url": repo_url,
            "baseline_branch": baseline_branch,
            "current_branch": current_branch,
            "metrics": {},
            "regressions": [],
            "improvements": []
        }
        
        # Placeholder for actual performance monitoring
        # This would integrate with actual performance testing tools
        
        logger.info("Performance monitoring completed")
        return performance_data
        
    except Exception as e:
        logger.error(f"Performance monitoring failed: {str(e)}")
        raise


@task(
    name="update-dependencies",
    description="Update dependencies with smart prioritization",
    tags=["dependencies", "security"],
    retries=2,
    retry_delay_seconds=120,
)
async def update_dependencies_task(
    repo_url: str,
    update_strategy: str = "smart",
    security_priority: str = "high"
) -> Dict[str, Any]:
    """
    Update dependencies with smart prioritization.
    
    Args:
        repo_url: Repository URL
        update_strategy: Update strategy (smart, security-only, all)
        security_priority: Security update priority (low, medium, high)
    
    Returns:
        Dictionary containing update results
    """
    logger = get_run_logger()
    logger.info(f"Updating dependencies for {repo_url} with strategy: {update_strategy}")
    
    try:
        update_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "repo_url": repo_url,
            "update_strategy": update_strategy,
            "security_priority": security_priority,
            "updates": [],
            "security_fixes": [],
            "skipped_updates": []
        }
        
        # Placeholder for actual dependency update logic
        # This would integrate with package managers and security scanners
        
        logger.info("Dependency update completed")
        return update_results
        
    except Exception as e:
        logger.error(f"Dependency update failed: {str(e)}")
        raise


# Helper functions

async def _analyze_security(codebase: Codebase) -> List[Dict[str, Any]]:
    """Analyze codebase for security issues"""
    # Placeholder for security analysis
    return []


async def _analyze_performance(codebase: Codebase) -> List[Dict[str, Any]]:
    """Analyze codebase for performance issues"""
    # Placeholder for performance analysis
    return []


async def _analyze_code_quality(codebase: Codebase) -> List[Dict[str, Any]]:
    """Analyze codebase for code quality issues"""
    # Placeholder for code quality analysis
    return []


async def _analyze_dependencies(codebase: Codebase) -> List[Dict[str, Any]]:
    """Analyze codebase for dependency issues"""
    # Placeholder for dependency analysis
    return []


async def _generate_metrics(codebase: Codebase) -> Dict[str, Any]:
    """Generate codebase metrics"""
    # Placeholder for metrics generation
    return {}


def _create_fix_prompt(issue: Dict[str, Any], analysis_results: Dict[str, Any]) -> str:
    """Create a prompt for fix generation"""
    return f"""
    Please analyze and fix the following issue:
    
    Issue: {issue.get('title', 'Unknown')}
    Description: {issue.get('description', 'No description')}
    Severity: {issue.get('severity', 'Unknown')}
    File: {issue.get('file', 'Unknown')}
    
    Context: This is part of an autonomous CI/CD system. Please provide a complete fix
    that can be automatically applied.
    """


def _calculate_fix_confidence(issue: Dict[str, Any], fix_result: str) -> float:
    """Calculate confidence score for a fix"""
    # Placeholder for confidence calculation
    # This would analyze the fix quality and completeness
    return 0.8


def _format_analysis_report(analysis_results: Dict[str, Any]) -> str:
    """Format analysis results as markdown"""
    return f"""
# Codebase Analysis Report

**Repository:** {analysis_results['repo_url']}
**Branch:** {analysis_results['branch']}
**Analysis Type:** {analysis_results['analysis_type']}
**Timestamp:** {analysis_results['timestamp']}

## Summary

- **Total Issues:** {len(analysis_results['issues'])}
- **Opportunities:** {len(analysis_results['opportunities'])}

## Issues Found

{chr(10).join([f"- {issue.get('title', 'Unknown')}" for issue in analysis_results['issues']])}

## Recommendations

{chr(10).join([f"- {rec}" for rec in analysis_results['recommendations']])}
"""


def _format_fixes_report(fixes: Dict[str, Any]) -> str:
    """Format fixes results as markdown"""
    return f"""
# Generated Fixes Report

**Timestamp:** {fixes['timestamp']}
**Total Issues:** {fixes['total_issues']}
**Generated Fixes:** {len(fixes['generated_fixes'])}
**Skipped Fixes:** {len(fixes['skipped_fixes'])}
**Confidence Threshold:** {fixes['confidence_threshold']}

## Generated Fixes

{chr(10).join([f"- {fix['issue_title']} (Confidence: {fix['confidence']:.2f})" for fix in fixes['generated_fixes']])}

## Skipped Fixes

{chr(10).join([f"- {fix['issue_title']}: {fix['skip_reason']}" for fix in fixes['skipped_fixes']])}
"""


def _create_pr_description(results: Dict[str, Any], fixes: Dict[str, Any]) -> str:
    """Create PR description for applied fixes"""
    return f"""
# 🤖 Autonomous Fixes Applied

This PR contains automatically generated and applied fixes from the autonomous CI/CD system.

## Summary

- **Applied Fixes:** {len(results['applied_fixes'])}
- **Failed Fixes:** {len(results['failed_fixes'])}
- **Branch:** {results['branch_name']}

## Applied Fixes

{chr(10).join([f"- {fix['issue_title']}" for fix in results['applied_fixes']])}

## Failed Fixes

{chr(10).join([f"- {fix['issue_title']}: {fix['error']}" for fix in results['failed_fixes']])}

---

*This PR was automatically created by the autonomous CI/CD system.*
"""

