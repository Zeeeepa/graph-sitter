#!/usr/bin/env python3
"""
Example: Autonomous CI/CD System Usage

This example demonstrates how to use the autonomous CI/CD system
with the Codegen SDK for intelligent automation.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from contexten.autonomous_cicd import AutonomousCICD, CICDConfig
from contexten.autonomous_cicd.integration import setup_autonomous_cicd


async def basic_example():
    """Basic example of autonomous CI/CD usage"""
    
    print("🚀 Autonomous CI/CD System Example")
    print("=" * 50)
    
    # Configuration from environment variables
    org_id = os.getenv("CODEGEN_ORG_ID")
    token = os.getenv("CODEGEN_TOKEN")
    
    if not org_id or not token:
        print("❌ Please set CODEGEN_ORG_ID and CODEGEN_TOKEN environment variables")
        print("   You can get these from https://codegen.com")
        return
    
    try:
        # Setup autonomous CI/CD system
        print("🔧 Setting up autonomous CI/CD system...")
        
        integration = await setup_autonomous_cicd(
            codegen_org_id=org_id,
            codegen_token=token,
            repo_path=".",
            enable_all_features=True
        )
        
        print("✅ Autonomous CI/CD system initialized!")
        
        # Get system status
        print("\n📊 System Status:")
        status = await integration.get_integration_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # Example: Run code analysis
        print("\n🔍 Running code analysis...")
        
        cicd_system = integration.cicd_system
        
        # Create a sample analysis pipeline
        trigger_event = {
            "branch": "develop",
            "changes": ["src/contexten/autonomous_cicd/core.py"],
            "trigger_type": "manual_example"
        }
        
        result = await cicd_system.execute_pipeline(
            trigger_event=trigger_event,
            pipeline_type="analysis"
        )
        
        print(f"✅ Analysis pipeline {result.pipeline_id} completed with status: {result.status}")
        
        if result.stages.get("analysis"):
            analysis_stage = result.stages["analysis"]
            print(f"   Analysis output: {analysis_stage.output}")
        
        # Example: Get system metrics
        print("\n📈 System Metrics:")
        metrics = await cicd_system.get_system_metrics()
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        
        # Cleanup
        print("\n🛑 Shutting down system...")
        await integration.shutdown()
        print("✅ System shutdown complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def advanced_example():
    """Advanced example with custom configuration"""
    
    print("\n🔬 Advanced Autonomous CI/CD Example")
    print("=" * 50)
    
    # Custom configuration
    config = CICDConfig(
        codegen_org_id=os.getenv("CODEGEN_ORG_ID", ""),
        codegen_token=os.getenv("CODEGEN_TOKEN", ""),
        repo_path=".",
        enable_auto_testing=True,
        enable_code_analysis=True,
        enable_security_scanning=True,
        code_quality_threshold=0.8,
        test_coverage_threshold=0.75,
        analysis_timeout=300
    )
    
    if not config.codegen_org_id or not config.codegen_token:
        print("❌ Skipping advanced example - missing credentials")
        return
    
    try:
        # Create CI/CD system with custom config
        cicd = AutonomousCICD(config)
        await cicd.initialize()
        
        print("✅ Advanced CI/CD system initialized!")
        
        # Example: Run full pipeline
        print("\n🔄 Running full CI/CD pipeline...")
        
        trigger_event = {
            "branch": "develop",
            "changes": [
                "src/contexten/autonomous_cicd/core.py",
                "src/contexten/autonomous_cicd/agents.py"
            ],
            "trigger_type": "advanced_example",
            "commit_sha": "abc123",
            "author": "example@example.com"
        }
        
        result = await cicd.execute_pipeline(
            trigger_event=trigger_event,
            pipeline_type="full"
        )
        
        print(f"✅ Full pipeline {result.pipeline_id} completed!")
        print(f"   Status: {result.status}")
        print(f"   Duration: {result.end_time - result.start_time:.2f} seconds")
        print(f"   Stages: {list(result.stages.keys())}")
        
        # Show detailed stage results
        for stage_name, stage in result.stages.items():
            print(f"\n   📋 {stage_name.title()} Stage:")
            print(f"      Status: {stage.status}")
            print(f"      Duration: {stage.end_time - stage.start_time:.2f}s")
            if stage.output:
                print(f"      Output: {stage.output}")
            if stage.error:
                print(f"      Error: {stage.error}")
        
        # Cleanup
        await cicd.shutdown()
        
    except Exception as e:
        print(f"❌ Advanced example error: {e}")


async def webhook_simulation_example():
    """Example simulating webhook events"""
    
    print("\n🔗 Webhook Simulation Example")
    print("=" * 50)
    
    if not os.getenv("CODEGEN_ORG_ID") or not os.getenv("CODEGEN_TOKEN"):
        print("❌ Skipping webhook example - missing credentials")
        return
    
    try:
        integration = await setup_autonomous_cicd(
            codegen_org_id=os.getenv("CODEGEN_ORG_ID"),
            codegen_token=os.getenv("CODEGEN_TOKEN"),
            repo_path="."
        )
        
        # Simulate GitHub push event
        print("📨 Simulating GitHub push event...")
        
        github_payload = {
            "ref": "refs/heads/feature/new-feature",
            "commits": [
                {
                    "id": "abc123",
                    "message": "Add new feature",
                    "added": ["src/new_feature.py"],
                    "modified": ["src/main.py"],
                    "removed": []
                }
            ],
            "repository": {
                "name": "graph-sitter",
                "full_name": "Zeeeepa/graph-sitter"
            }
        }
        
        # Get GitHub trigger and simulate event
        github_trigger = integration.cicd_system.triggers.get("github")
        if github_trigger:
            await github_trigger._handle_push_event(github_payload)
            print("✅ GitHub push event processed!")
        
        # Simulate Linear issue event
        print("\n📋 Simulating Linear issue event...")
        
        linear_payload = {
            "type": "Issue",
            "action": "create",
            "data": {
                "id": "issue-123",
                "title": "CI/CD: Deploy new feature to staging",
                "description": "Please deploy the new feature branch to staging environment"
            }
        }
        
        linear_trigger = integration.cicd_system.triggers.get("linear")
        if linear_trigger:
            await linear_trigger._handle_issue_event(linear_payload)
            print("✅ Linear issue event processed!")
        
        # Wait a bit for pipelines to process
        await asyncio.sleep(2)
        
        # Show recent pipelines
        print("\n📊 Recent Pipelines:")
        for pipeline in integration.cicd_system.pipeline_history[-3:]:
            print(f"   {pipeline.pipeline_id}: {pipeline.status} ({pipeline.end_time - pipeline.start_time:.1f}s)")
        
        await integration.shutdown()
        
    except Exception as e:
        print(f"❌ Webhook simulation error: {e}")


def main():
    """Main function to run examples"""
    
    print("🎯 Graph-Sitter Autonomous CI/CD Examples")
    print("=" * 60)
    print()
    print("This example demonstrates the autonomous CI/CD system")
    print("integrated with the Codegen SDK for intelligent automation.")
    print()
    
    # Check for required environment variables
    if not os.getenv("CODEGEN_ORG_ID") or not os.getenv("CODEGEN_TOKEN"):
        print("⚠️  Environment Setup Required:")
        print("   Please set the following environment variables:")
        print("   - CODEGEN_ORG_ID: Your Codegen organization ID")
        print("   - CODEGEN_TOKEN: Your Codegen API token")
        print()
        print("   You can get these from: https://codegen.com")
        print()
        print("   Example:")
        print("   export CODEGEN_ORG_ID='your-org-id'")
        print("   export CODEGEN_TOKEN='your-token'")
        print()
    
    # Run examples
    try:
        asyncio.run(basic_example())
        asyncio.run(advanced_example())
        asyncio.run(webhook_simulation_example())
        
        print("\n🎉 All examples completed successfully!")
        print("\nNext steps:")
        print("1. Integrate with your GitHub repository webhooks")
        print("2. Configure Linear integration for issue tracking")
        print("3. Set up Slack notifications for pipeline results")
        print("4. Customize the CI/CD pipeline for your specific needs")
        
    except KeyboardInterrupt:
        print("\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

