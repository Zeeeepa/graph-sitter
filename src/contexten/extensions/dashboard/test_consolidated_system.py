#!/usr/bin/env python3
"""
Test script for the Consolidated Dashboard System.
Validates all components and integrations work together.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.contexten.extensions.dashboard.consolidated_dashboard import create_consolidated_dashboard
from src.contexten.extensions.dashboard.consolidated_models import (
    ProjectCreateRequest, FlowStartRequest, PlanGenerateRequest
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_dashboard_creation():
    """Test dashboard creation and initialization."""
    logger.info("Testing dashboard creation...")
    
    try:
        dashboard = create_consolidated_dashboard()
        assert dashboard is not None
        assert dashboard.api is not None
        assert dashboard.app is not None
        
        logger.info("✅ Dashboard creation successful")
        return True
    except Exception as e:
        logger.error(f"❌ Dashboard creation failed: {e}")
        return False


async def test_api_endpoints():
    """Test API endpoints functionality."""
    logger.info("Testing API endpoints...")
    
    try:
        dashboard = create_consolidated_dashboard()
        api = dashboard.api
        
        # Test health endpoint
        health = await api.monitoring_service.get_system_health()
        assert health is not None
        assert health.status in ['healthy', 'warning', 'degraded', 'critical', 'error']
        
        # Test service status
        services = await api._get_all_service_statuses()
        assert services is not None
        
        logger.info("✅ API endpoints test successful")
        return True
    except Exception as e:
        logger.error(f"❌ API endpoints test failed: {e}")
        return False


async def test_project_service():
    """Test project service functionality."""
    logger.info("Testing project service...")
    
    try:
        dashboard = create_consolidated_dashboard()
        project_service = dashboard.api.project_service
        
        # Test GitHub repositories (mock)
        repos = await project_service.get_github_repositories()
        assert isinstance(repos, list)
        
        # Test project creation
        project = await project_service.create_project(
            repo_url="https://github.com/test/repo",
            requirements="Test project requirements"
        )
        assert project is not None
        assert project.repo_url == "https://github.com/test/repo"
        
        # Test project retrieval
        retrieved_project = await project_service.get_project(project.id)
        assert retrieved_project is not None
        assert retrieved_project.id == project.id
        
        logger.info("✅ Project service test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Project service test failed: {e}")
        return False


async def test_codegen_service():
    """Test Codegen service functionality."""
    logger.info("Testing Codegen service...")
    
    try:
        dashboard = create_consolidated_dashboard()
        codegen_service = dashboard.api.codegen_service
        
        # Test status check
        status = await codegen_service.check_status()
        assert status in ['connected', 'disconnected', 'error']
        
        # Test plan generation
        plan = await codegen_service.generate_plan(
            project_id="test-project",
            requirements="Create a simple web application"
        )
        assert plan is not None
        assert 'summary' in plan
        assert 'tasks' in plan
        
        # Test task creation
        task = await codegen_service.create_task(
            task_type="generate_code",
            project_id="test-project",
            prompt="Create a simple function"
        )
        assert task is not None
        assert task.task_type == "generate_code"
        
        logger.info("✅ Codegen service test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Codegen service test failed: {e}")
        return False


async def test_quality_service():
    """Test quality service functionality."""
    logger.info("Testing quality service...")
    
    try:
        dashboard = create_consolidated_dashboard()
        quality_service = dashboard.api.quality_service
        
        # Test quality gates creation
        gates = await quality_service.get_quality_gates("test-project")
        assert isinstance(gates, list)
        assert len(gates) > 0
        
        # Test validation
        results = await quality_service.validate_all_gates("test-project")
        assert results is not None
        assert 'overall_status' in results
        assert 'gate_results' in results
        
        logger.info("✅ Quality service test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Quality service test failed: {e}")
        return False


async def test_monitoring_service():
    """Test monitoring service functionality."""
    logger.info("Testing monitoring service...")
    
    try:
        dashboard = create_consolidated_dashboard()
        monitoring_service = dashboard.api.monitoring_service
        
        # Test system health
        health = await monitoring_service.get_system_health()
        assert health is not None
        assert health.status is not None
        assert health.system_metrics is not None
        
        # Test alerts
        alerts = await monitoring_service.get_alerts()
        assert isinstance(alerts, list)
        
        logger.info("✅ Monitoring service test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Monitoring service test failed: {e}")
        return False


async def test_strands_orchestrator():
    """Test Strands orchestrator functionality."""
    logger.info("Testing Strands orchestrator...")
    
    try:
        dashboard = create_consolidated_dashboard()
        orchestrator = dashboard.api.strands_orchestrator
        
        # Test workflow creation
        flow = await orchestrator.start_workflow(
            project_id="test-project",
            requirements="Test workflow requirements",
            auto_execute=False
        )
        assert flow is not None
        assert flow.project_id == "test-project"
        assert flow.status.value in ['idle', 'planning', 'running', 'paused', 'completed', 'failed']
        
        # Test workflow retrieval
        retrieved_flow = await orchestrator.get_workflow(flow.id)
        assert retrieved_flow is not None
        assert retrieved_flow.id == flow.id
        
        logger.info("✅ Strands orchestrator test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Strands orchestrator test failed: {e}")
        return False


async def test_websocket_functionality():
    """Test WebSocket functionality."""
    logger.info("Testing WebSocket functionality...")
    
    try:
        dashboard = create_consolidated_dashboard()
        api = dashboard.api
        
        # Test connection management
        assert api.active_connections == []
        assert api.connection_subscriptions == {}
        
        # Test event broadcasting (without actual WebSocket)
        from src.contexten.extensions.dashboard.consolidated_models import ProjectUpdateEvent
        
        event = ProjectUpdateEvent(
            data={"action": "test", "project": {"id": "test"}},
            project_id="test-project"
        )
        
        # This should not fail even with no connections
        await api._broadcast_event(event)
        
        logger.info("✅ WebSocket functionality test successful")
        return True
    except Exception as e:
        logger.error(f"❌ WebSocket functionality test failed: {e}")
        return False


async def test_integration_workflow():
    """Test complete integration workflow."""
    logger.info("Testing complete integration workflow...")
    
    try:
        dashboard = create_consolidated_dashboard()
        
        # 1. Create a project
        project = await dashboard.api.project_service.create_project(
            repo_url="https://github.com/test/integration-test",
            requirements="Build a comprehensive test application"
        )
        
        # 2. Generate a plan
        plan = await dashboard.api.codegen_service.generate_plan(
            project_id=project.id,
            requirements=project.requirements
        )
        
        # 3. Start a workflow
        flow = await dashboard.api.strands_orchestrator.start_workflow(
            project_id=project.id,
            requirements=project.requirements,
            auto_execute=False
        )
        
        # 4. Validate quality gates
        quality_results = await dashboard.api.quality_service.validate_all_gates(project.id)
        
        # 5. Check system health
        health = await dashboard.api.monitoring_service.get_system_health()
        
        # Verify all components worked
        assert project is not None
        assert plan is not None
        assert flow is not None
        assert quality_results is not None
        assert health is not None
        
        logger.info("✅ Complete integration workflow test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Complete integration workflow test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests and report results."""
    logger.info("🚀 Starting Consolidated Dashboard System Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Dashboard Creation", test_dashboard_creation),
        ("API Endpoints", test_api_endpoints),
        ("Project Service", test_project_service),
        ("Codegen Service", test_codegen_service),
        ("Quality Service", test_quality_service),
        ("Monitoring Service", test_monitoring_service),
        ("Strands Orchestrator", test_strands_orchestrator),
        ("WebSocket Functionality", test_websocket_functionality),
        ("Integration Workflow", test_integration_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Report results
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("-" * 60)
    logger.info(f"Total Tests: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! The consolidated dashboard system is working correctly.")
        return True
    else:
        logger.info(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

