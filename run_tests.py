import asyncio
import unittest
from test_mcp_orchestrator_lib import TestMCPOrchestrator

async def run_test(test_case, method_name):
    """Run a test method."""
    test = test_case(method_name)
    await test.asyncSetUp()
    try:
        await getattr(test, method_name)()
    finally:
        await test.asyncTearDown()

async def run_tests():
    """Run all tests."""
    # Get all test methods
    test_methods = [method for method in dir(TestMCPOrchestrator) if method.startswith("test_")]
    
    # Run each test
    for method_name in test_methods:
        print(f"Running {method_name}...")
        await run_test(TestMCPOrchestrator, method_name)
        print(f"{method_name} passed!")
    
    print(f"All {len(test_methods)} tests passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())

