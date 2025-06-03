"""
Integration test for the comprehensive CI/CD system.

This module provides a comprehensive test of all system components:
- Database initialization and operations
- System orchestration
- Event handling
- Performance monitoring
- Error handling and recovery
- Continuous learning capabilities
"""

import asyncio
import logging
import tempfile
from datetime import datetime
from typing import Dict, Any

from .contexten_app import ContextenApp
from .config import get_settings
from .database import get_database_manager
from .core import SystemOrchestrator

logger = logging.getLogger(__name__)


class SystemIntegrationTest:
    """Comprehensive integration test for the CI/CD system."""
    
    def __init__(self):
        self.app: ContextenApp = None
        self.test_results: Dict[str, Any] = {}
        self.start_time = datetime.utcnow()
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive integration test of all system components."""
        logger.info("🚀 Starting comprehensive CI/CD system integration test")
        
        try:
            # Test 1: System Initialization
            await self._test_system_initialization()
            
            # Test 2: Database Operations
            await self._test_database_operations()
            
            # Test 3: Event System
            await self._test_event_system()
            
            # Test 4: Performance Monitoring
            await self._test_performance_monitoring()
            
            # Test 5: Error Handling
            await self._test_error_handling()
            
            # Test 6: Continuous Learning
            await self._test_continuous_learning()
            
            # Test 7: End-to-End Workflow
            await self._test_end_to_end_workflow()
            
            # Test 8: System Health and Metrics
            await self._test_system_health()
            
            # Calculate overall results
            self._calculate_test_results()
            
            logger.info("✅ Comprehensive integration test completed successfully")
            return self.test_results
            
        except Exception as e:
            logger.error(f"❌ Integration test failed: {e}")
            self.test_results["overall_status"] = "FAILED"
            self.test_results["error"] = str(e)
            return self.test_results
        
        finally:
            # Cleanup
            if self.app:
                await self.app.shutdown()
    
    async def _test_system_initialization(self) -> None:
        """Test system initialization and component setup."""
        logger.info("🔧 Testing system initialization...")
        
        test_name = "system_initialization"
        start_time = datetime.utcnow()
        
        try:
            # Create temporary directory for testing
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Initialize ContextenApp
                self.app = ContextenApp(
                    name="integration-test",
                    tmp_dir=tmp_dir,
                    enable_monitoring=True,
                    enable_learning=True
                )
                
                # Initialize the app
                await self.app.initialize()
                
                # Verify initialization
                assert self.app._initialized, "App should be initialized"
                assert self.app.orchestrator.is_initialized(), "Orchestrator should be initialized"
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "duration_seconds": duration,
                    "details": "System initialized successfully"
                }
                
                logger.info(f"✅ System initialization test passed ({duration:.2f}s)")
                
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "FAILED",
                "duration_seconds": duration,
                "error": str(e)
            }
            logger.error(f"❌ System initialization test failed: {e}")
            raise
    
    async def _test_database_operations(self) -> None:
        """Test database operations across all 7 modules."""
        logger.info("🗄️ Testing database operations...")
        
        test_name = "database_operations"
        start_time = datetime.utcnow()
        
        try:
            # Test database connectivity
            async with self.app.orchestrator.get_db_session() as session:
                # Test basic query
                result = await session.execute("SELECT 1 as test")
                assert result.scalar() == 1, "Basic database query failed"
            
            # Test task creation
            task = await self.app.orchestrator.create_task({
                "name": "Test Task",
                "description": "Integration test task",
                "title": "Test Task Title",
                "task_type": "testing",
                "priority": "medium"
            })
            assert task.id is not None, "Task creation failed"
            
            # Test project creation
            project = await self.app.orchestrator.create_project({
                "name": "Test Project",
                "description": "Integration test project",
                "slug": "test-project"
            })
            assert project.id is not None, "Project creation failed"
            
            # Test event logging
            event = await self.app.orchestrator.log_event({
                "name": "Test Event",
                "description": "Integration test event",
                "event_type": "test",
                "provider": "system",
                "payload": {"test": True}
            })
            assert event.id is not None, "Event logging failed"
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "PASSED",
                "duration_seconds": duration,
                "details": {
                    "task_created": str(task.id),
                    "project_created": str(project.id),
                    "event_logged": str(event.id)
                }
            }
            
            logger.info(f"✅ Database operations test passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "FAILED",
                "duration_seconds": duration,
                "error": str(e)
            }
            logger.error(f"❌ Database operations test failed: {e}")
            raise
    
    async def _test_event_system(self) -> None:
        """Test event system and cross-component communication."""
        logger.info("📡 Testing event system...")
        
        test_name = "event_system"
        start_time = datetime.utcnow()
        
        try:
            # Test event emission and handling
            event_received = False
            
            async def test_handler(data: Dict[str, Any]) -> None:
                nonlocal event_received
                event_received = True
                logger.info(f"Test event handler received: {data}")
            
            # Register test event handler
            self.app.orchestrator.register_event_handler("test_event", test_handler)
            
            # Emit test event
            await self.app.orchestrator.emit_event("test_event", {"test": "data"})
            
            # Wait a bit for async processing
            await asyncio.sleep(0.1)
            
            assert event_received, "Event handler was not called"
            
            # Test event simulation
            result = await self.app.simulate_event("github", "push", {
                "repository": {"full_name": "test/repo"},
                "commits": [{"message": "test commit"}]
            })
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "PASSED",
                "duration_seconds": duration,
                "details": {
                    "event_handler_called": event_received,
                    "event_simulation_result": str(result)
                }
            }
            
            logger.info(f"✅ Event system test passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "FAILED",
                "duration_seconds": duration,
                "error": str(e)
            }
            logger.error(f"❌ Event system test failed: {e}")
            raise
    
    async def _test_performance_monitoring(self) -> None:
        """Test performance monitoring capabilities."""
        logger.info("📊 Testing performance monitoring...")
        
        test_name = "performance_monitoring"
        start_time = datetime.utcnow()
        
        try:
            if not self.app.performance_monitor:
                self.test_results[test_name] = {
                    "status": "SKIPPED",
                    "reason": "Performance monitoring not enabled"
                }
                return
            
            # Test operation monitoring
            await self.app.performance_monitor.record_operation(
                "test_operation", 0.5, success=True
            )
            
            # Test metrics collection
            metrics = await self.app.performance_monitor.get_current_metrics()
            assert "timestamp" in metrics, "Metrics should contain timestamp"
            
            # Test performance report
            report = await self.app.performance_monitor.get_performance_report(1)
            assert "period_hours" in report, "Report should contain period information"
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "PASSED",
                "duration_seconds": duration,
                "details": {
                    "metrics_collected": True,
                    "report_generated": True,
                    "current_metrics": metrics
                }
            }
            
            logger.info(f"✅ Performance monitoring test passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "FAILED",
                "duration_seconds": duration,
                "error": str(e)
            }
            logger.error(f"❌ Performance monitoring test failed: {e}")
            raise
    
    async def _test_error_handling(self) -> None:
        """Test error handling and recovery capabilities."""
        logger.info("🚨 Testing error handling...")
        
        test_name = "error_handling"
        start_time = datetime.utcnow()
        
        try:
            # Test error handling
            test_error = ValueError("Test error for integration testing")
            
            result = await self.app.error_handler.handle_error(
                test_error,
                {"component": "integration_test", "operation": "test_error_handling"},
                attempt_recovery=False
            )
            
            assert result["error_id"] is not None, "Error should be assigned an ID"
            assert result["category"] is not None, "Error should be classified"
            
            # Test error statistics
            stats = self.app.error_handler.get_error_statistics()
            assert stats["total_errors"] > 0, "Error statistics should show recorded errors"
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "PASSED",
                "duration_seconds": duration,
                "details": {
                    "error_handled": True,
                    "error_id": result["error_id"],
                    "error_category": result["category"],
                    "error_statistics": stats
                }
            }
            
            logger.info(f"✅ Error handling test passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "FAILED",
                "duration_seconds": duration,
                "error": str(e)
            }
            logger.error(f"❌ Error handling test failed: {e}")
            raise
    
    async def _test_continuous_learning(self) -> None:
        """Test continuous learning capabilities."""
        logger.info("🧠 Testing continuous learning...")
        
        test_name = "continuous_learning"
        start_time = datetime.utcnow()
        
        try:
            if not self.app.enable_learning:
                self.test_results[test_name] = {
                    "status": "SKIPPED",
                    "reason": "Continuous learning not enabled"
                }
                return
            
            # Test learning data creation
            async with self.app.orchestrator.get_db_session() as session:
                from .database.models import LearningModel
                
                learning = LearningModel(
                    name="Test Learning",
                    description="Integration test learning data",
                    learning_type="pattern_recognition",
                    data={"test": "learning_data"},
                    source_component="integration_test",
                    confidence_score=0.9
                )
                session.add(learning)
                await session.flush()
                
                assert learning.id is not None, "Learning data creation failed"
            
            # Test learning from task completion
            await self.app._update_learning_from_task(
                {"task_id": "test-task", "task_type": "testing"},
                success=True
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "PASSED",
                "duration_seconds": duration,
                "details": {
                    "learning_data_created": True,
                    "task_learning_updated": True
                }
            }
            
            logger.info(f"✅ Continuous learning test passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "FAILED",
                "duration_seconds": duration,
                "error": str(e)
            }
            logger.error(f"❌ Continuous learning test failed: {e}")
            raise
    
    async def _test_end_to_end_workflow(self) -> None:
        """Test end-to-end workflow simulation."""
        logger.info("🔄 Testing end-to-end workflow...")
        
        test_name = "end_to_end_workflow"
        start_time = datetime.utcnow()
        
        try:
            # Simulate a complete workflow
            
            # 1. Create a project
            project = await self.app.orchestrator.create_project({
                "name": "E2E Test Project",
                "description": "End-to-end test project",
                "slug": "e2e-test-project"
            })
            
            # 2. Create a task
            task = await self.app.orchestrator.create_task({
                "name": "E2E Test Task",
                "description": "End-to-end test task",
                "title": "E2E Test Task",
                "task_type": "feature_implementation",
                "priority": "high",
                "project_id": project.id
            })
            
            # 3. Simulate task execution
            await self.app.orchestrator.update_task(str(task.id), {
                "status": "in_progress",
                "started_at": datetime.utcnow()
            })
            
            # 4. Simulate task completion
            await self.app.orchestrator.update_task(str(task.id), {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "result": {"success": True, "output": "Task completed successfully"}
            })
            
            # 5. Simulate event processing
            await self.app.simulate_event("linear", "issue_update", {
                "action": "update",
                "data": {
                    "id": str(task.id),
                    "state": {"name": "Done"}
                }
            })
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "PASSED",
                "duration_seconds": duration,
                "details": {
                    "project_id": str(project.id),
                    "task_id": str(task.id),
                    "workflow_completed": True
                }
            }
            
            logger.info(f"✅ End-to-end workflow test passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "FAILED",
                "duration_seconds": duration,
                "error": str(e)
            }
            logger.error(f"❌ End-to-end workflow test failed: {e}")
            raise
    
    async def _test_system_health(self) -> None:
        """Test system health monitoring and metrics."""
        logger.info("🏥 Testing system health...")
        
        test_name = "system_health"
        start_time = datetime.utcnow()
        
        try:
            # Test health check
            health = await self.app.health_check()
            assert "status" in health, "Health check should return status"
            assert "timestamp" in health, "Health check should return timestamp"
            
            # Test system status
            system_health = await self.app.orchestrator.get_system_health()
            assert "components" in system_health, "System health should include components"
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "PASSED",
                "duration_seconds": duration,
                "details": {
                    "health_check": health,
                    "system_health": system_health
                }
            }
            
            logger.info(f"✅ System health test passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.test_results[test_name] = {
                "status": "FAILED",
                "duration_seconds": duration,
                "error": str(e)
            }
            logger.error(f"❌ System health test failed: {e}")
            raise
    
    def _calculate_test_results(self) -> None:
        """Calculate overall test results."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get("status") == "PASSED")
        failed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get("status") == "FAILED")
        skipped_tests = sum(1 for result in self.test_results.values() 
                           if isinstance(result, dict) and result.get("status") == "SKIPPED")
        
        total_duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "success_rate": success_rate,
            "total_duration_seconds": total_duration,
            "overall_status": "PASSED" if failed_tests == 0 else "FAILED"
        }
        
        logger.info(f"📊 Test Summary: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")


async def run_integration_test() -> Dict[str, Any]:
    """Run the comprehensive integration test."""
    test = SystemIntegrationTest()
    return await test.run_comprehensive_test()


if __name__ == "__main__":
    # Run the integration test
    import json
    
    async def main():
        results = await run_integration_test()
        print("\n" + "="*80)
        print("COMPREHENSIVE CI/CD SYSTEM INTEGRATION TEST RESULTS")
        print("="*80)
        print(json.dumps(results, indent=2, default=str))
        
        summary = results.get("summary", {})
        if summary.get("overall_status") == "PASSED":
            print(f"\n✅ ALL TESTS PASSED! ({summary.get('success_rate', 0):.1f}% success rate)")
            exit(0)
        else:
            print(f"\n❌ SOME TESTS FAILED! ({summary.get('success_rate', 0):.1f}% success rate)")
            exit(1)
    
    asyncio.run(main())

