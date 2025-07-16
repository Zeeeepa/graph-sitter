"""
Integration tests for the Enhanced Orchestrator
"""

import asyncio
import pytest
import tempfile
import os
from pathlib import Path

from .orchestrator import EnhancedOrchestrator
from .memory import MemoryManager
from .events import EventEvaluator
from .cicd import AutonomousCICD
from .config import ContextenConfig


class TestEnhancedOrchestrator:
    """Test the Enhanced Orchestrator functionality"""
    
    @pytest.fixture
    async def orchestrator(self):
        """Create a test orchestrator instance"""
        config = ContextenConfig()
        config.debug = True
        config.logging.level = "DEBUG"
        
        # Use temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            config.memory.db_path = tmp.name
        
        orchestrator = EnhancedOrchestrator(config)
        await orchestrator.start()
        
        yield orchestrator
        
        await orchestrator.stop()
        
        # Cleanup temporary database
        if os.path.exists(config.memory.db_path):
            os.unlink(config.memory.db_path)
    
    async def test_orchestrator_startup_shutdown(self, orchestrator):
        """Test basic startup and shutdown"""
        health = orchestrator.get_health_status()
        assert health["orchestrator"] == "healthy"
        assert health["memory_manager"] is True
        assert health["event_evaluator"] is True
    
    async def test_agent_creation(self, orchestrator):
        """Test agent creation with SDK-Python integration"""
        agent_config = {
            "name": "test_agent",
            "model_provider": "bedrock",
            "temperature": 0.3
        }
        
        agent_id = await orchestrator.create_agent(
            agent_config=agent_config,
            tools=["calculator", "memory_operations"]
        )
        
        assert agent_id is not None
        assert len(agent_id) > 0
        
        # Get agent info
        if orchestrator.sdk_python:
            agent_info = await orchestrator.sdk_python.get_agent_info(agent_id)
            assert agent_info is not None
            assert agent_info["name"] == "test_agent"
    
    async def test_task_execution(self, orchestrator):
        """Test task execution"""
        task_config = {
            "description": "Test calculation",
            "expression": "2 + 2"
        }
        
        result = await orchestrator.execute_task(
            task_id="test_task",
            task_config=task_config,
            use_memory=True
        )
        
        assert result["task_id"] == "test_task"
        assert result["status"] == "completed"
        assert "result" in result
    
    async def test_system_optimization(self, orchestrator):
        """Test system optimization"""
        optimization_results = await orchestrator.optimize_system()
        
        assert isinstance(optimization_results, dict)
        assert "memory" in optimization_results


class TestMemoryManager:
    """Test the Memory Manager functionality"""
    
    @pytest.fixture
    async def memory_manager(self):
        """Create a test memory manager instance"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        memory = MemoryManager(db_path=db_path)
        await memory.start()
        
        yield memory
        
        await memory.stop()
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    async def test_store_and_retrieve_context(self, memory_manager):
        """Test storing and retrieving context"""
        # Store context
        success = await memory_manager.store_context(
            context_id="test_context",
            data={"key": "value", "number": 42},
            metadata={"type": "test"}
        )
        
        assert success is True
        
        # Retrieve context
        result = await memory_manager.retrieve_context(context_id="test_context")
        
        assert result["context_id"] == "test_context"
        assert result["data"]["key"] == "value"
        assert result["data"]["number"] == 42
    
    async def test_semantic_search(self, memory_manager):
        """Test semantic search functionality"""
        # Store multiple contexts
        contexts = [
            {"context_id": "user_prefs", "data": {"theme": "dark"}, "metadata": {"type": "preferences"}},
            {"context_id": "project_config", "data": {"name": "test_project"}, "metadata": {"type": "config"}},
            {"context_id": "task_data", "data": {"status": "completed"}, "metadata": {"type": "task"}}
        ]
        
        for context in contexts:
            await memory_manager.store_context(**context)
        
        # Search for preferences
        results = await memory_manager.retrieve_context(
            query="user preferences",
            relevance_threshold=0.1,
            limit=5
        )
        
        assert "results" in results
        assert len(results["results"]) > 0
    
    async def test_memory_optimization(self, memory_manager):
        """Test memory optimization"""
        # Store some test data
        for i in range(10):
            await memory_manager.store_context(
                context_id=f"test_{i}",
                data={"index": i},
                metadata={"type": "test_data"}
            )
        
        # Run optimization
        optimization_result = await memory_manager.optimize()
        
        assert isinstance(optimization_result, dict)
        assert "entries_before" in optimization_result


class TestEventEvaluator:
    """Test the Event Evaluator functionality"""
    
    @pytest.fixture
    async def event_evaluator(self):
        """Create a test event evaluator instance"""
        evaluator = EventEvaluator(
            monitoring_enabled=True,
            real_time_processing=False  # Disable for testing
        )
        await evaluator.start()
        
        yield evaluator
        
        await evaluator.stop()
    
    async def test_event_evaluation(self, event_evaluator):
        """Test event evaluation"""
        event_data = {
            "type": "task_execution",
            "status": "completed",
            "task_id": "test_task",
            "source": "test"
        }
        
        event_id = await event_evaluator.evaluate_event(event_data)
        
        assert event_id is not None
        assert len(event_id) > 0
    
    async def test_event_classification(self, event_evaluator):
        """Test event classification"""
        # Test error event
        error_event = {
            "type": "task_execution",
            "status": "failed",
            "error_message": "ImportError: No module named 'missing_lib'",
            "source": "test"
        }
        
        event_id = await event_evaluator.evaluate_event(error_event)
        
        # Get the event back
        events = await event_evaluator.get_events(limit=1)
        assert len(events) > 0
        
        latest_event = events[0]
        assert latest_event["type"] in ["error", "task"]  # Should be classified as error or task
    
    async def test_get_events(self, event_evaluator):
        """Test getting events"""
        # Create some test events
        test_events = [
            {"type": "test_event_1", "source": "test"},
            {"type": "test_event_2", "source": "test"},
            {"type": "test_event_3", "source": "test"}
        ]
        
        for event_data in test_events:
            await event_evaluator.evaluate_event(event_data)
        
        # Get events
        events = await event_evaluator.get_events(limit=10)
        
        assert len(events) >= 3


class TestAutonomousCICD:
    """Test the Autonomous CI/CD functionality"""
    
    @pytest.fixture
    async def cicd_system(self):
        """Create a test CI/CD system instance"""
        cicd = AutonomousCICD(
            enabled=True,
            auto_healing=False,  # Disable for testing
            continuous_optimization=False
        )
        await cicd.start()
        
        yield cicd
        
        await cicd.stop()
    
    async def test_list_pipelines(self, cicd_system):
        """Test listing available pipelines"""
        pipelines = await cicd_system.list_pipelines()
        
        assert isinstance(pipelines, list)
        assert len(pipelines) > 0
        assert "build" in pipelines
    
    async def test_pipeline_execution(self, cicd_system):
        """Test pipeline execution"""
        execution_id = await cicd_system.execute_pipeline(
            pipeline_name="build",
            parameters={"branch": "test"}
        )
        
        assert execution_id is not None
        assert len(execution_id) > 0
        
        # Wait a bit for execution to start
        await asyncio.sleep(0.1)
        
        # Get execution status
        status = await cicd_system.get_execution_status(execution_id)
        
        assert status is not None
        assert status["id"] == execution_id
        assert status["pipeline_name"] == "build"
    
    async def test_get_system_status(self, cicd_system):
        """Test getting CI/CD system status"""
        status = await cicd_system.get_status()
        
        assert isinstance(status, dict)
        assert "enabled" in status
        assert "total_pipelines" in status
        assert status["enabled"] is True


# Integration test functions that can be run directly
async def test_basic_integration():
    """Test basic integration between components"""
    print("🧪 Testing basic integration...")
    
    config = ContextenConfig()
    config.debug = True
    
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        config.memory.db_path = tmp.name
    
    orchestrator = EnhancedOrchestrator(config)
    
    try:
        await orchestrator.start()
        print("✅ Orchestrator started")
        
        # Test agent creation
        agent_config = {
            "name": "integration_test_agent",
            "model_provider": "bedrock",
            "temperature": 0.3
        }
        
        agent_id = await orchestrator.create_agent(
            agent_config=agent_config,
            tools=["calculator"]
        )
        print(f"✅ Created agent: {agent_id}")
        
        # Test task execution
        task_config = {
            "description": "Calculate 5 + 3",
            "expression": "5 + 3"
        }
        
        result = await orchestrator.execute_task(
            task_id="integration_test",
            task_config=task_config,
            agent_id=agent_id
        )
        print(f"✅ Task executed: {result['status']}")
        
        # Test system health
        health = orchestrator.get_health_status()
        print(f"✅ System health: {health['orchestrator']}")
        
        print("✅ Basic integration test passed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        raise
    
    finally:
        await orchestrator.stop()
        
        # Cleanup
        if os.path.exists(config.memory.db_path):
            os.unlink(config.memory.db_path)


async def test_memory_integration():
    """Test memory integration"""
    print("🧪 Testing memory integration...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    memory = MemoryManager(db_path=db_path)
    
    try:
        await memory.start()
        print("✅ Memory manager started")
        
        # Store test data
        await memory.store_context(
            context_id="integration_test",
            data={"test": "data", "number": 123},
            metadata={"type": "integration_test"}
        )
        print("✅ Context stored")
        
        # Retrieve data
        result = await memory.retrieve_context(context_id="integration_test")
        assert result["data"]["test"] == "data"
        print("✅ Context retrieved")
        
        # Test optimization
        optimization = await memory.optimize()
        print(f"✅ Memory optimized: {optimization}")
        
        print("✅ Memory integration test passed!")
        
    except Exception as e:
        print(f"❌ Memory integration test failed: {e}")
        raise
    
    finally:
        await memory.stop()
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


async def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Running Enhanced Orchestrator Integration Tests")
    print("=" * 50)
    
    try:
        await test_basic_integration()
        await test_memory_integration()
        
        print("\n" + "=" * 50)
        print("✅ All integration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run integration tests
    asyncio.run(run_integration_tests())

