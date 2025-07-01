"""
Prefect deployment configuration for autonomous CI/CD system.

This script sets up Prefect deployments for the autonomous CI/CD flows.
"""

from prefect import serve
from src.contexten.prefect_flows.autonomous_cicd import autonomous_cicd_flow
from src.contexten.prefect_flows.component_analysis import component_analysis_flow
from src.contexten.prefect_flows.monitoring import system_health_flow


def create_deployments():
    """Create Prefect deployments for all flows."""
    
    # Main autonomous CI/CD flow - runs every 15 minutes
    autonomous_deployment = autonomous_cicd_flow.to_deployment(
        name="autonomous-cicd-main",
        description="Main autonomous CI/CD orchestration flow",
        tags=["autonomous", "cicd", "orchestration"],
        interval=900,  # 15 minutes
        work_pool_name="default-agent-pool"
    )
    
    # Component analysis flow - triggered on demand
    component_deployment = component_analysis_flow.to_deployment(
        name="component-analysis",
        description="Detailed component analysis flow",
        tags=["analysis", "components", "code-quality"],
        work_pool_name="default-agent-pool"
    )
    
    # System health monitoring - runs every 5 minutes
    health_deployment = system_health_flow.to_deployment(
        name="system-health-monitoring",
        description="System health and monitoring flow",
        tags=["monitoring", "health", "alerts"],
        interval=300,  # 5 minutes
        work_pool_name="default-agent-pool"
    )
    
    return [autonomous_deployment, component_deployment, health_deployment]


if __name__ == "__main__":
    # Create and serve deployments
    deployments = create_deployments()
    
    print("Starting Prefect deployments for autonomous CI/CD system...")
    print(f"Created {len(deployments)} deployments:")
    for deployment in deployments:
        print(f"  - {deployment.name}: {deployment.description}")
    
    # Serve the deployments
    serve(*deployments)

