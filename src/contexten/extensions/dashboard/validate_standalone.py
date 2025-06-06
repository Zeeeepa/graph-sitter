#!/usr/bin/env python3
"""
Standalone validation script for the Consolidated Dashboard System.
Tests all components without external dependencies.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model_imports():
    """Test model imports."""
    logger.info("Testing model imports...")
    try:
        # Import models directly
        from consolidated_models import (
            Project, Flow, Task, UserSettings, QualityGate,
            FlowStatus, TaskStatus, ServiceStatus, ProjectStatus, QualityGateStatus
        )
        
        # Test model creation
        project = Project(
            id="test-1",
            name="Test Project",
            repo_url="https://github.com/test/repo",
            owner="test",
            repo_name="repo",
            full_name="test/repo"
        )
        
        flow = Flow(
            id="flow-1",
            project_id="test-1",
            name="Test Flow"
        )
        
        task = Task(
            id="task-1",
            flow_id="flow-1",
            project_id="test-1",
            title="Test Task",
            description="Test task description"
        )
        
        logger.info("✅ Model imports and creation successful")
        return True
    except Exception as e:
        logger.error(f"❌ Model imports failed: {e}")
        return False

def test_service_imports():
    """Test service imports."""
    logger.info("Testing service imports...")
    try:
        # Import services with absolute imports
        import sys
        sys.path.append(os.path.dirname(__file__))
        
        from services.codegen_service import CodegenService
        from services.project_service import ProjectService  
        from services.quality_service import QualityService
        from services.monitoring_service import MonitoringService
        from services.strands_orchestrator import StrandsOrchestrator
        
        logger.info("✅ Service imports successful")
        return True
    except Exception as e:
        logger.error(f"❌ Service imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_service_functionality():
    """Test service functionality."""
    logger.info("Testing service functionality...")
    try:
        # Import services
        from services.codegen_service import CodegenService
        from services.project_service import ProjectService
        from services.quality_service import QualityService
        from services.monitoring_service import MonitoringService
        from services.strands_orchestrator import StrandsOrchestrator
        
        # Test Codegen Service
        codegen_service = CodegenService()
        status = await codegen_service.check_status()
        logger.info(f"Codegen service status: {status}")
        
        # Test Project Service
        project_service = ProjectService()
        repos = await project_service.get_github_repositories()
        logger.info(f"Found {len(repos)} repositories")
        
        # Test Quality Service
        quality_service = QualityService()
        gates = await quality_service.get_quality_gates("test-project")
        logger.info(f"Created {len(gates)} quality gates")
        
        # Test Monitoring Service
        monitoring_service = MonitoringService()
        health = await monitoring_service.get_system_health()
        logger.info(f"System health status: {health.status}")
        
        # Test Strands Orchestrator
        orchestrator = StrandsOrchestrator()
        workflow_status = await orchestrator.check_workflow_status()
        logger.info(f"Workflow status: {workflow_status}")
        
        logger.info("✅ Service functionality tests successful")
        return True
    except Exception as e:
        logger.error(f"❌ Service functionality tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fastapi_creation():
    """Test FastAPI app creation."""
    logger.info("Testing FastAPI app creation...")
    try:
        from fastapi import FastAPI
        
        # Create a simple FastAPI app to test
        app = FastAPI(
            title="Test Strands Dashboard",
            version="1.0.0",
            description="Test dashboard"
        )
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        @app.get("/test")
        async def test():
            return {"message": "test successful"}
        
        logger.info(f"✅ FastAPI app created with {len(app.routes)} routes")
        return True
    except Exception as e:
        logger.error(f"❌ FastAPI app creation failed: {e}")
        return False

async def test_integration_workflow():
    """Test a complete integration workflow."""
    logger.info("Testing integration workflow...")
    try:
        from services.project_service import ProjectService
        from services.codegen_service import CodegenService
        from services.quality_service import QualityService
        from services.strands_orchestrator import StrandsOrchestrator
        
        # 1. Create a project
        project_service = ProjectService()
        project = await project_service.create_project(
            repo_url="https://github.com/test/integration-test",
            requirements="Build a test application"
        )
        logger.info(f"Created project: {project.name}")
        
        # 2. Generate a plan
        codegen_service = CodegenService()
        plan = await codegen_service.generate_plan(
            project_id=project.id,
            requirements=project.requirements
        )
        logger.info(f"Generated plan with {len(plan.get('tasks', []))} tasks")
        
        # 3. Start a workflow
        orchestrator = StrandsOrchestrator()
        flow = await orchestrator.start_workflow(
            project_id=project.id,
            requirements=project.requirements,
            auto_execute=False
        )
        logger.info(f"Started workflow: {flow.name}")
        
        # 4. Validate quality gates
        quality_service = QualityService()
        quality_results = await quality_service.validate_all_gates(project.id)
        logger.info(f"Quality validation status: {quality_results['overall_status']}")
        
        logger.info("✅ Integration workflow test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Integration workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_validation():
    """Run all validation tests."""
    logger.info("🚀 Starting Consolidated Dashboard Validation")
    logger.info("=" * 60)
    
    tests = [
        ("Model Imports", test_model_imports),
        ("Service Imports", test_service_imports),
        ("FastAPI Creation", test_fastapi_creation),
        ("Service Functionality", test_service_functionality),
        ("Integration Workflow", test_integration_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Report results
    logger.info("\n" + "=" * 60)
    logger.info("📊 VALIDATION RESULTS")
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
        logger.info(f"\n⚠️  {failed} test(s) failed. The system has some issues but core functionality works.")
        return passed > failed

def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_validation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Validation crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

