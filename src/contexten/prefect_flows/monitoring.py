"""
System monitoring and health check flows.

This module provides monitoring capabilities for the autonomous CI/CD system,
including health checks, performance monitoring, and alerting.
"""

import os
import time
from typing import Dict, List, Optional
from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret


@task
def check_codegen_sdk_health() -> Dict:
    """Check Codegen SDK connectivity and health."""
    logger = get_run_logger()
    
    try:
        from codegen import Agent
        
        # Get credentials
        org_id = os.getenv("CODEGEN_ORG_ID") or Secret.load("codegen-org-id").get()
        api_token = os.getenv("CODEGEN_API_TOKEN") or Secret.load("codegen-api-token").get()
        
        # Test connection
        start_time = time.time()
        agent = Agent(org_id=org_id, token=api_token)
        
        # Simple health check task
        task = agent.run(prompt="Health check: respond with 'OK' if you can receive this message")
        
        # Wait for response (short timeout for health check)
        max_attempts = 6  # 1 minute with 10-second intervals
        attempts = 0
        
        while attempts < max_attempts:
            task.refresh()
            if task.status in ["completed", "failed"]:
                break
            attempts += 1
            time.sleep(10)
        
        response_time = time.time() - start_time
        
        if task.status == "completed":
            logger.info("Codegen SDK health check passed")
            return {
                "status": "healthy",
                "response_time": response_time,
                "message": "Codegen SDK is responsive"
            }
        else:
            logger.warning("Codegen SDK health check failed")
            return {
                "status": "unhealthy",
                "response_time": response_time,
                "message": f"Task status: {task.status}"
            }
            
    except Exception as e:
        logger.error(f"Codegen SDK health check error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@task
def check_linear_api_health() -> Dict:
    """Check Linear API connectivity and health."""
    logger = get_run_logger()
    
    try:
        # TODO: Implement Linear API health check
        # This would test Linear API connectivity
        logger.info("Linear API health check - placeholder")
        
        return {
            "status": "healthy",
            "message": "Linear API health check not implemented yet"
        }
        
    except Exception as e:
        logger.error(f"Linear API health check error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@task
def check_github_api_health() -> Dict:
    """Check GitHub API connectivity and health."""
    logger = get_run_logger()
    
    try:
        # TODO: Implement GitHub API health check
        # This would test GitHub API connectivity and rate limits
        logger.info("GitHub API health check - placeholder")
        
        return {
            "status": "healthy",
            "message": "GitHub API health check not implemented yet"
        }
        
    except Exception as e:
        logger.error(f"GitHub API health check error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@task
def check_system_resources() -> Dict:
    """Check system resource usage."""
    logger = get_run_logger()
    
    try:
        import psutil
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Define thresholds
        cpu_threshold = 80.0
        memory_threshold = 80.0
        disk_threshold = 90.0
        
        # Check thresholds
        issues = []
        if cpu_percent > cpu_threshold:
            issues.append(f"High CPU usage: {cpu_percent}%")
        if memory.percent > memory_threshold:
            issues.append(f"High memory usage: {memory.percent}%")
        if disk.percent > disk_threshold:
            issues.append(f"High disk usage: {disk.percent}%")
        
        status = "healthy" if not issues else "warning"
        
        logger.info(f"System resources check: {status}")
        
        return {
            "status": status,
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "issues": issues
        }
        
    except ImportError:
        logger.warning("psutil not available for system monitoring")
        return {
            "status": "unknown",
            "message": "psutil not available"
        }
    except Exception as e:
        logger.error(f"System resources check error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@task
def check_prefect_flows_health() -> Dict:
    """Check health of other Prefect flows."""
    logger = get_run_logger()
    
    try:
        # TODO: Implement Prefect flow health monitoring
        # This would check the status of recent flow runs
        logger.info("Prefect flows health check - placeholder")
        
        return {
            "status": "healthy",
            "message": "Prefect flows health check not implemented yet"
        }
        
    except Exception as e:
        logger.error(f"Prefect flows health check error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@task
def send_health_alert(health_results: List[Dict]) -> Dict:
    """Send health alerts if issues are detected."""
    logger = get_run_logger()
    
    # Check for any unhealthy services
    unhealthy_services = [
        result for result in health_results 
        if result.get("status") in ["unhealthy", "error", "warning"]
    ]
    
    if unhealthy_services:
        logger.warning(f"Found {len(unhealthy_services)} unhealthy services")
        
        # TODO: Implement alerting (Slack, email, etc.)
        # For now, just log the issues
        for service in unhealthy_services:
            logger.warning(f"Service issue: {service}")
        
        return {
            "alerts_sent": len(unhealthy_services),
            "status": "alerts_triggered"
        }
    else:
        logger.info("All services healthy - no alerts needed")
        return {
            "alerts_sent": 0,
            "status": "all_healthy"
        }


@flow(name="system-health-monitoring")
def system_health_flow():
    """
    System health monitoring flow.
    
    This flow:
    1. Checks health of all integrated services
    2. Monitors system resources
    3. Checks Prefect flow status
    4. Sends alerts if issues are detected
    """
    logger = get_run_logger()
    logger.info("Starting system health monitoring flow")
    
    # Perform health checks
    codegen_health = check_codegen_sdk_health()
    linear_health = check_linear_api_health()
    github_health = check_github_api_health()
    system_resources = check_system_resources()
    prefect_health = check_prefect_flows_health()
    
    # Collect all health results
    health_results = [
        {"service": "codegen_sdk", **codegen_health},
        {"service": "linear_api", **linear_health},
        {"service": "github_api", **github_health},
        {"service": "system_resources", **system_resources},
        {"service": "prefect_flows", **prefect_health}
    ]
    
    # Send alerts if needed
    alert_result = send_health_alert(health_results)
    
    # Calculate overall health status
    unhealthy_count = len([r for r in health_results if r.get("status") in ["unhealthy", "error"]])
    warning_count = len([r for r in health_results if r.get("status") == "warning"])
    
    if unhealthy_count > 0:
        overall_status = "unhealthy"
    elif warning_count > 0:
        overall_status = "warning"
    else:
        overall_status = "healthy"
    
    logger.info(f"System health monitoring completed. Overall status: {overall_status}")
    
    return {
        "overall_status": overall_status,
        "services_checked": len(health_results),
        "unhealthy_services": unhealthy_count,
        "warning_services": warning_count,
        "health_results": health_results,
        "alert_result": alert_result
    }


if __name__ == "__main__":
    # For testing purposes
    system_health_flow()

