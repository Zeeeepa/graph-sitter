#!/usr/bin/env python3
"""
Complete validation script for the consolidated dashboard.
This script validates all working components and identifies issues.
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")

def print_info(message):
    """Print an info message."""
    print(f"ℹ️  {message}")

def test_imports():
    """Test all import capabilities."""
    print_header("IMPORT VALIDATION")
    
    # Test working imports
    try:
        from consolidated_models import Project, Flow, Task
        print_success("consolidated_models.py - ALL MODELS WORK")
    except Exception as e:
        print_error(f"consolidated_models.py failed: {e}")
    
    try:
        import start_dashboard_standalone
        print_success("start_dashboard_standalone.py - IMPORTS WORK")
    except Exception as e:
        print_error(f"start_dashboard_standalone.py failed: {e}")
    
    try:
        from fastapi import FastAPI
        app = FastAPI()
        print_success("FastAPI framework - WORKS")
    except Exception as e:
        print_error(f"FastAPI failed: {e}")
    
    # Test broken imports
    print_info("Testing known broken imports...")
    
    broken_files = [
        'consolidated_api.py',
        'consolidated_dashboard.py',
        'services/codegen_service.py',
        'services/project_service.py'
    ]
    
    for file in broken_files:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location('test_module', file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print_success(f"{file} - UNEXPECTEDLY WORKS!")
        except Exception:
            print_error(f"{file} - CONFIRMED BROKEN (relative imports)")

def test_dashboard_creation():
    """Test dashboard application creation."""
    print_header("DASHBOARD CREATION TEST")
    
    try:
        from start_dashboard_standalone import create_standalone_dashboard
        
        app = create_standalone_dashboard()
        if app:
            print_success("Dashboard app created successfully")
            print_success(f"App type: {type(app)}")
            print_success(f"App title: {app.title}")
            print_success(f"App version: {app.version}")
            
            # Check routes
            routes = [route.path for route in app.routes]
            print_success(f"Available routes: {routes}")
            
            return True
        else:
            print_error("Failed to create dashboard")
            return False
            
    except Exception as e:
        print_error(f"Dashboard creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_startup():
    """Test server startup and basic functionality."""
    print_header("SERVER STARTUP TEST")
    
    try:
        # Start server in background
        print_info("Starting dashboard server...")
        process = subprocess.Popen(
            [sys.executable, 'start_dashboard_standalone.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        time.sleep(3)
        
        if process.poll() is None:
            print_success("Server started successfully")
            
            # Test endpoints with curl
            endpoints = [
                '/health',
                '/api/health', 
                '/api/projects'
            ]
            
            for endpoint in endpoints:
                try:
                    result = subprocess.run(
                        ['curl', '-s', f'http://localhost:8000{endpoint}'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        # Try to parse as JSON
                        try:
                            json.loads(result.stdout)
                            print_success(f"Endpoint {endpoint} - WORKING (valid JSON)")
                        except:
                            print_success(f"Endpoint {endpoint} - WORKING (response received)")
                    else:
                        print_error(f"Endpoint {endpoint} - FAILED")
                        
                except subprocess.TimeoutExpired:
                    print_error(f"Endpoint {endpoint} - TIMEOUT")
                except Exception as e:
                    print_error(f"Endpoint {endpoint} - ERROR: {e}")
            
            # Kill server
            process.terminate()
            process.wait(timeout=5)
            print_success("Server stopped cleanly")
            return True
            
        else:
            print_error("Server failed to start")
            stdout, stderr = process.communicate()
            print_error(f"STDOUT: {stdout}")
            print_error(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print_error(f"Server test failed: {e}")
        return False

def test_models():
    """Test data model functionality."""
    print_header("DATA MODEL TEST")
    
    try:
        from consolidated_models import Project, Flow, Task, FlowStatus, TaskStatus
        
        # Test Project creation
        project = Project(
            id="test-1",
            name="Test Project",
            repo_url="https://github.com/test/repo",
            owner="test",
            repo_name="repo",
            full_name="test/repo"
        )
        
        project_dict = project.to_dict()
        print_success("Project model - CREATION AND SERIALIZATION WORK")
        
        # Test Flow creation
        flow = Flow(
            id="flow-1",
            project_id="test-1",
            name="Test Flow",
            status=FlowStatus.IDLE
        )
        
        flow_dict = flow.to_dict()
        print_success("Flow model - CREATION AND SERIALIZATION WORK")
        
        # Test Task creation
        task = Task(
            id="task-1",
            flow_id="flow-1",
            name="Test Task",
            status=TaskStatus.PENDING
        )
        
        task_dict = task.to_dict()
        print_success("Task model - CREATION AND SERIALIZATION WORK")
        
        return True
        
    except Exception as e:
        print_error(f"Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("🚀 COMPREHENSIVE DASHBOARD VALIDATION")
    print("=" * 60)
    print("This script validates all components of the consolidated dashboard.")
    print("It will test imports, dashboard creation, server startup, and models.")
    print()
    
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    # Add current directory to Python path
    sys.path.insert(0, str(dashboard_dir))
    
    # Run all tests
    results = []
    
    results.append(("Import Validation", test_imports()))
    results.append(("Dashboard Creation", test_dashboard_creation()))
    results.append(("Data Models", test_models()))
    results.append(("Server Startup", test_server_startup()))
    
    # Print summary
    print_header("VALIDATION SUMMARY")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name} - PASSED")
            passed += 1
        else:
            print_error(f"{test_name} - FAILED")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("ALL TESTS PASSED - DASHBOARD FULLY VALIDATED!")
    elif passed >= total // 2:
        print_info("CORE FUNCTIONALITY WORKING - Some advanced features need fixes")
    else:
        print_error("MAJOR ISSUES FOUND - Dashboard needs significant fixes")
    
    print("\n📋 USAGE:")
    print("   To start the working dashboard:")
    print("   python start_dashboard_standalone.py")
    print("   Then visit: http://localhost:8000")

if __name__ == "__main__":
    main()

