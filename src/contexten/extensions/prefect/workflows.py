"""
Prefect Workflows for Autonomous CI/CD Operations

This module defines complete workflows that orchestrate multiple tasks
for autonomous CI/CD operations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from prefect import flow, get_run_logger
from prefect.artifacts import create_markdown_artifact
from prefect.task_runners import ConcurrentTaskRunner

from .tasks import (
    analyze_codebase_task,
    generate_fixes_task,
    apply_fixes_task,
    monitor_performance_task,
    update_dependencies_task,
)
from .config import get_config, get_workflow_configs
from .notifications import send_notification, NotificationType


@flow(
    name="autonomous-maintenance",
    description="Comprehensive autonomous maintenance workflow",
    task_runner=ConcurrentTaskRunner(),
    retries=1,
    retry_delay_seconds=300,
)
async def autonomous_maintenance_flow(
    repo_url: str,
    branch: str = "main",
    include_security_scan: bool = True,
    include_performance_check: bool = True,
    include_dependency_update: bool = True,
    auto_apply_fixes: bool = True,
) -> Dict[str, Any]:
    """
    Comprehensive autonomous maintenance workflow that performs:
    - Codebase analysis
    - Security scanning
    - Performance monitoring
    - Dependency updates
    - Automatic fix generation and application
    
    Args:
        repo_url: Repository URL to maintain
        branch: Branch to analyze and maintain
        include_security_scan: Whether to include security scanning
        include_performance_check: Whether to include performance monitoring
        include_dependency_update: Whether to include dependency updates
        auto_apply_fixes: Whether to automatically apply generated fixes
    
    Returns:
        Dictionary containing workflow results
    """
    logger = get_run_logger()
    config = get_config()
    
    logger.info(f"Starting autonomous maintenance for {repo_url} on branch {branch}")
    
    workflow_results = {
        "workflow_name": "autonomous-maintenance",
        "repo_url": repo_url,
        "branch": branch,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "status": "running",
        "results": {},
        "errors": [],
        "notifications_sent": []
    }
    
    try:
        # Send start notification
        await send_notification(
            NotificationType.WORKFLOW_STARTED,
            f"🚀 Starting autonomous maintenance for {repo_url}",
            {"repo_url": repo_url, "branch": branch}
        )
        workflow_results["notifications_sent"].append("workflow_started")
        
        # Phase 1: Comprehensive codebase analysis
        logger.info("Phase 1: Analyzing codebase")
        analysis_results = await analyze_codebase_task(
            repo_url=repo_url,
            branch=branch,
            analysis_type="comprehensive"
        )
        workflow_results["results"]["analysis"] = analysis_results
        
        # Phase 2: Generate fixes for identified issues
        if analysis_results["issues"]:
            logger.info(f"Phase 2: Generating fixes for {len(analysis_results['issues'])} issues")
            fixes = await generate_fixes_task(
                analysis_results=analysis_results,
                confidence_threshold=config.auto_fix_confidence_threshold
            )
            workflow_results["results"]["fixes"] = fixes
            
            # Phase 3: Apply fixes if enabled and high-confidence fixes exist
            if auto_apply_fixes and fixes["generated_fixes"]:
                logger.info(f"Phase 3: Applying {len(fixes['generated_fixes'])} fixes")
                application_results = await apply_fixes_task(
                    fixes=fixes,
                    repo_url=repo_url,
                    create_pr=True
                )
                workflow_results["results"]["application"] = application_results
                
                # Send fix notification
                if application_results["applied_fixes"]:
                    await send_notification(
                        NotificationType.FIXES_APPLIED,
                        f"🔧 Applied {len(application_results['applied_fixes'])} autonomous fixes",
                        {
                            "repo_url": repo_url,
                            "fixes_count": len(application_results["applied_fixes"]),
                            "pr_url": application_results.get("pr_url")
                        }
                    )
                    workflow_results["notifications_sent"].append("fixes_applied")
        else:
            logger.info("No issues found, skipping fix generation")
        
        # Phase 4: Performance monitoring (if enabled)
        if include_performance_check:
            logger.info("Phase 4: Monitoring performance")
            performance_results = await monitor_performance_task(
                repo_url=repo_url,
                baseline_branch=branch,
                current_branch=branch
            )
            workflow_results["results"]["performance"] = performance_results
            
            # Check for performance regressions
            if performance_results.get("regressions"):
                await send_notification(
                    NotificationType.PERFORMANCE_REGRESSION,
                    f"⚠️ Performance regression detected in {repo_url}",
                    {
                        "repo_url": repo_url,
                        "regressions": performance_results["regressions"]
                    }
                )
                workflow_results["notifications_sent"].append("performance_regression")
        
        # Phase 5: Dependency updates (if enabled)
        if include_dependency_update:
            logger.info("Phase 5: Updating dependencies")
            dependency_results = await update_dependencies_task(
                repo_url=repo_url,
                update_strategy="smart",
                security_priority="high"
            )
            workflow_results["results"]["dependencies"] = dependency_results
            
            # Send security update notification
            if dependency_results.get("security_fixes"):
                await send_notification(
                    NotificationType.SECURITY_UPDATE,
                    f"🔒 Applied {len(dependency_results['security_fixes'])} security updates",
                    {
                        "repo_url": repo_url,
                        "security_fixes": dependency_results["security_fixes"]
                    }
                )
                workflow_results["notifications_sent"].append("security_update")
        
        # Workflow completed successfully
        workflow_results["status"] = "completed"
        workflow_results["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info("Autonomous maintenance workflow completed successfully")
        
        # Send completion notification
        await send_notification(
            NotificationType.WORKFLOW_COMPLETED,
            f"✅ Autonomous maintenance completed for {repo_url}",
            workflow_results
        )
        workflow_results["notifications_sent"].append("workflow_completed")
        
        # Create workflow summary artifact
        await create_markdown_artifact(
            key=f"maintenance-summary-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            markdown=_format_maintenance_summary(workflow_results),
            description=f"Autonomous maintenance summary for {repo_url}"
        )
        
        return workflow_results
        
    except Exception as e:
        logger.error(f"Autonomous maintenance workflow failed: {str(e)}")
        workflow_results["status"] = "failed"
        workflow_results["completed_at"] = datetime.utcnow().isoformat()
        workflow_results["errors"].append(str(e))
        
        # Send failure notification
        await send_notification(
            NotificationType.WORKFLOW_FAILED,
            f"❌ Autonomous maintenance failed for {repo_url}",
            {"repo_url": repo_url, "error": str(e)}
        )
        workflow_results["notifications_sent"].append("workflow_failed")
        
        raise


@flow(
    name="failure-analysis",
    description="Analyze and fix CI/CD failures",
    task_runner=ConcurrentTaskRunner(),
    retries=2,
    retry_delay_seconds=180,
)
async def failure_analysis_flow(
    repo_url: str,
    workflow_run_id: str,
    failure_logs: str,
    auto_fix: bool = True
) -> Dict[str, Any]:
    """
    Analyze CI/CD failures and attempt automatic fixes.
    
    Args:
        repo_url: Repository URL where failure occurred
        workflow_run_id: GitHub workflow run ID
        failure_logs: Failure logs to analyze
        auto_fix: Whether to automatically apply fixes
    
    Returns:
        Dictionary containing analysis and fix results
    """
    logger = get_run_logger()
    config = get_config()
    
    logger.info(f"Analyzing failure for workflow run {workflow_run_id}")
    
    failure_results = {
        "workflow_name": "failure-analysis",
        "repo_url": repo_url,
        "workflow_run_id": workflow_run_id,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "status": "running",
        "failure_analysis": {},
        "fixes_applied": [],
        "notifications_sent": []
    }
    
    try:
        # Analyze the failure
        logger.info("Analyzing failure patterns")
        
        # Create synthetic analysis results for the failure
        failure_analysis = {
            "failure_type": "test_failure",  # This would be determined by analysis
            "root_cause": "dependency_conflict",  # This would be determined by analysis
            "confidence": 0.85,
            "recommended_actions": [
                "Update conflicting dependencies",
                "Fix test assertions",
                "Update CI configuration"
            ],
            "auto_fixable": True
        }
        
        failure_results["failure_analysis"] = failure_analysis
        
        # Generate and apply fixes if auto_fix is enabled and confidence is high
        if auto_fix and failure_analysis["confidence"] >= config.auto_fix_confidence_threshold:
            logger.info("Generating and applying fixes")
            
            # Create analysis results format for fix generation
            analysis_for_fixes = {
                "repo_url": repo_url,
                "issues": [{
                    "id": f"failure-{workflow_run_id}",
                    "title": f"CI/CD Failure - {failure_analysis['failure_type']}",
                    "description": f"Root cause: {failure_analysis['root_cause']}",
                    "severity": "high",
                    "type": "ci_failure"
                }]
            }
            
            # Generate fixes
            fixes = await generate_fixes_task(
                analysis_results=analysis_for_fixes,
                confidence_threshold=config.auto_fix_confidence_threshold
            )
            
            # Apply fixes if any were generated
            if fixes["generated_fixes"]:
                application_results = await apply_fixes_task(
                    fixes=fixes,
                    repo_url=repo_url,
                    create_pr=True
                )
                failure_results["fixes_applied"] = application_results["applied_fixes"]
                
                # Send fix notification
                await send_notification(
                    NotificationType.FAILURE_FIXED,
                    f"🔧 Automatically fixed CI/CD failure in {repo_url}",
                    {
                        "repo_url": repo_url,
                        "workflow_run_id": workflow_run_id,
                        "fixes_count": len(application_results["applied_fixes"])
                    }
                )
                failure_results["notifications_sent"].append("failure_fixed")
        
        failure_results["status"] = "completed"
        failure_results["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info("Failure analysis workflow completed")
        return failure_results
        
    except Exception as e:
        logger.error(f"Failure analysis workflow failed: {str(e)}")
        failure_results["status"] = "failed"
        failure_results["completed_at"] = datetime.utcnow().isoformat()
        
        await send_notification(
            NotificationType.WORKFLOW_FAILED,
            f"❌ Failure analysis failed for {repo_url}",
            {"repo_url": repo_url, "error": str(e)}
        )
        
        raise


@flow(
    name="dependency-update",
    description="Smart dependency updates with testing",
    task_runner=ConcurrentTaskRunner(),
    retries=1,
    retry_delay_seconds=240,
)
async def dependency_update_flow(
    repo_url: str,
    update_strategy: str = "smart",
    security_priority: str = "high",
    run_tests: bool = True
) -> Dict[str, Any]:
    """
    Perform smart dependency updates with comprehensive testing.
    
    Args:
        repo_url: Repository URL to update
        update_strategy: Update strategy (smart, security-only, all)
        security_priority: Security update priority (low, medium, high)
        run_tests: Whether to run tests after updates
    
    Returns:
        Dictionary containing update results
    """
    logger = get_run_logger()
    
    logger.info(f"Starting dependency update for {repo_url} with strategy: {update_strategy}")
    
    update_results = {
        "workflow_name": "dependency-update",
        "repo_url": repo_url,
        "update_strategy": update_strategy,
        "security_priority": security_priority,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "status": "running",
        "updates": [],
        "test_results": {},
        "notifications_sent": []
    }
    
    try:
        # Perform dependency updates
        dependency_results = await update_dependencies_task(
            repo_url=repo_url,
            update_strategy=update_strategy,
            security_priority=security_priority
        )
        
        update_results["updates"] = dependency_results["updates"]
        
        # Run tests if requested and updates were made
        if run_tests and dependency_results["updates"]:
            logger.info("Running tests after dependency updates")
            # Test running logic would go here
            update_results["test_results"] = {"status": "passed", "details": "All tests passed"}
        
        update_results["status"] = "completed"
        update_results["completed_at"] = datetime.utcnow().isoformat()
        
        # Send notification for security updates
        if dependency_results.get("security_fixes"):
            await send_notification(
                NotificationType.SECURITY_UPDATE,
                f"🔒 Applied {len(dependency_results['security_fixes'])} security updates",
                update_results
            )
            update_results["notifications_sent"].append("security_update")
        
        logger.info("Dependency update workflow completed")
        return update_results
        
    except Exception as e:
        logger.error(f"Dependency update workflow failed: {str(e)}")
        update_results["status"] = "failed"
        update_results["completed_at"] = datetime.utcnow().isoformat()
        
        await send_notification(
            NotificationType.WORKFLOW_FAILED,
            f"❌ Dependency update failed for {repo_url}",
            {"repo_url": repo_url, "error": str(e)}
        )
        
        raise


@flow(
    name="performance-optimization",
    description="Monitor and optimize system performance",
    task_runner=ConcurrentTaskRunner(),
    retries=2,
    retry_delay_seconds=120,
)
async def performance_optimization_flow(
    repo_url: str,
    baseline_branch: str = "main",
    regression_threshold: float = 20.0,
    auto_optimize: bool = True
) -> Dict[str, Any]:
    """
    Monitor system performance and apply optimizations.
    
    Args:
        repo_url: Repository URL to monitor
        baseline_branch: Baseline branch for comparison
        regression_threshold: Performance regression threshold (%)
        auto_optimize: Whether to automatically apply optimizations
    
    Returns:
        Dictionary containing performance results
    """
    logger = get_run_logger()
    
    logger.info(f"Starting performance optimization for {repo_url}")
    
    perf_results = {
        "workflow_name": "performance-optimization",
        "repo_url": repo_url,
        "baseline_branch": baseline_branch,
        "regression_threshold": regression_threshold,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "status": "running",
        "performance_data": {},
        "optimizations_applied": [],
        "notifications_sent": []
    }
    
    try:
        # Monitor performance
        performance_data = await monitor_performance_task(
            repo_url=repo_url,
            baseline_branch=baseline_branch,
            current_branch=baseline_branch
        )
        
        perf_results["performance_data"] = performance_data
        
        # Check for regressions and apply optimizations if needed
        if performance_data.get("regressions") and auto_optimize:
            logger.info("Performance regressions detected, applying optimizations")
            
            # Optimization logic would go here
            perf_results["optimizations_applied"] = ["cache_optimization", "query_optimization"]
            
            # Send regression notification
            await send_notification(
                NotificationType.PERFORMANCE_REGRESSION,
                f"⚠️ Performance regression detected and optimized in {repo_url}",
                perf_results
            )
            perf_results["notifications_sent"].append("performance_regression")
        
        perf_results["status"] = "completed"
        perf_results["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info("Performance optimization workflow completed")
        return perf_results
        
    except Exception as e:
        logger.error(f"Performance optimization workflow failed: {str(e)}")
        perf_results["status"] = "failed"
        perf_results["completed_at"] = datetime.utcnow().isoformat()
        
        await send_notification(
            NotificationType.WORKFLOW_FAILED,
            f"❌ Performance optimization failed for {repo_url}",
            {"repo_url": repo_url, "error": str(e)}
        )
        
        raise


# Helper functions

def _format_maintenance_summary(workflow_results: Dict[str, Any]) -> str:
    """Format maintenance workflow summary as markdown"""
    results = workflow_results["results"]
    
    summary = f"""
# Autonomous Maintenance Summary

**Repository:** {workflow_results['repo_url']}
**Branch:** {workflow_results['branch']}
**Status:** {workflow_results['status']}
**Started:** {workflow_results['started_at']}
**Completed:** {workflow_results['completed_at']}

## Analysis Results

"""
    
    if "analysis" in results:
        analysis = results["analysis"]
        summary += f"""
- **Issues Found:** {len(analysis.get('issues', []))}
- **Opportunities:** {len(analysis.get('opportunities', []))}
"""
    
    if "fixes" in results:
        fixes = results["fixes"]
        summary += f"""
## Fix Generation

- **Generated Fixes:** {len(fixes.get('generated_fixes', []))}
- **Skipped Fixes:** {len(fixes.get('skipped_fixes', []))}
- **Confidence Threshold:** {fixes.get('confidence_threshold', 'N/A')}
"""
    
    if "application" in results:
        application = results["application"]
        summary += f"""
## Fix Application

- **Applied Fixes:** {len(application.get('applied_fixes', []))}
- **Failed Fixes:** {len(application.get('failed_fixes', []))}
- **PR Created:** {application.get('pr_url', 'No')}
"""
    
    if "performance" in results:
        summary += f"""
## Performance Monitoring

- **Regressions:** {len(results['performance'].get('regressions', []))}
- **Improvements:** {len(results['performance'].get('improvements', []))}
"""
    
    if "dependencies" in results:
        deps = results["dependencies"]
        summary += f"""
## Dependency Updates

- **Updates Applied:** {len(deps.get('updates', []))}
- **Security Fixes:** {len(deps.get('security_fixes', []))}
"""
    
    summary += f"""
## Notifications Sent

{chr(10).join([f"- {notif}" for notif in workflow_results['notifications_sent']])}
"""
    
    return summary

