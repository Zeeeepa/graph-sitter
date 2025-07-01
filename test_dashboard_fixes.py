#!/usr/bin/env python3
"""
Test script to verify dashboard fixes without requiring all dependencies
"""

import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_config_attributes():
    """Test that DashboardConfig has required attributes"""
    try:
        from contexten.dashboard.app import DashboardConfig
        
        config = DashboardConfig()
        
        # Test that github_token attribute exists
        assert hasattr(config, 'github_token'), "❌ github_token attribute missing"
        print("✅ github_token attribute exists")
        
        # Test that linear_api_key attribute exists  
        assert hasattr(config, 'linear_api_key'), "❌ linear_api_key attribute missing"
        print("✅ linear_api_key attribute exists")
        
        # Test that slack_webhook_url attribute exists
        assert hasattr(config, 'slack_webhook_url'), "❌ slack_webhook_url attribute missing"
        print("✅ slack_webhook_url attribute exists")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  Import error (expected due to missing dependencies): {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_logger_definition():
    """Test that logger is properly defined"""
    try:
        # Read the app.py file and check for logger definition
        app_path = project_root / "src" / "contexten" / "dashboard" / "app.py"
        
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check that logger is defined after get_logger import
        if 'logger = get_logger(__name__)' in content:
            print("✅ Logger properly initialized")
            return True
        else:
            print("❌ Logger initialization not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking logger: {e}")
        return False

def test_orchestration_config_compatibility():
    """Test that OrchestrationConfig can be initialized with DashboardConfig attributes"""
    try:
        from contexten.orchestration.config import OrchestrationConfig
        from contexten.dashboard.app import DashboardConfig
        
        dashboard_config = DashboardConfig()
        
        # Test that we can create OrchestrationConfig with dashboard config attributes
        orch_config = OrchestrationConfig(
            codegen_org_id=dashboard_config.codegen_org_id,
            codegen_token=dashboard_config.codegen_token,
            github_token=dashboard_config.github_token,
            linear_api_key=dashboard_config.linear_api_key,
            slack_webhook_url=dashboard_config.slack_webhook_url
        )
        
        print("✅ OrchestrationConfig compatible with DashboardConfig")
        return True
        
    except ImportError as e:
        print(f"⚠️  Import error (expected due to missing dependencies): {e}")
        return False
    except Exception as e:
        print(f"❌ Compatibility error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing Dashboard Fixes")
    print("=" * 50)
    
    tests = [
        ("Configuration Attributes", test_config_attributes),
        ("Logger Definition", test_logger_definition), 
        ("Config Compatibility", test_orchestration_config_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All critical fixes verified!")
    else:
        print("⚠️  Some issues remain - check individual test output")

if __name__ == "__main__":
    main()

