#!/usr/bin/env python3
"""
Test the dashboard entrypoint without starting the full server.
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_api_creation():
    """Test creating the API directly."""
    logger.info("Testing direct API creation...")
    try:
        # Import and create API without the contexten dependency
        from consolidated_api import ConsolidatedDashboardAPI
        
        # Create API instance
        api = ConsolidatedDashboardAPI(contexten_app=None)
        
        logger.info(f"✅ API created successfully")
        logger.info(f"   App title: {api.app.title}")
        logger.info(f"   App version: {api.app.version}")
        logger.info(f"   Routes: {len(api.app.routes)}")
        logger.info(f"   Active connections: {len(api.active_connections)}")
        logger.info(f"   Background tasks: {len(api.background_tasks)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Direct API creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard_creation():
    """Test creating the dashboard."""
    logger.info("Testing dashboard creation...")
    try:
        # Import and create dashboard without the contexten dependency
        from consolidated_dashboard import ConsolidatedDashboard
        
        # Create dashboard instance
        dashboard = ConsolidatedDashboard(contexten_app=None)
        
        logger.info(f"✅ Dashboard created successfully")
        logger.info(f"   Host: {dashboard.host}")
        logger.info(f"   Port: {dashboard.port}")
        logger.info(f"   Debug: {dashboard.debug}")
        
        # Test health status
        health = dashboard.get_health_status()
        logger.info(f"   Health status: {health['status']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Dashboard creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_factory_functions():
    """Test factory functions."""
    logger.info("Testing factory functions...")
    try:
        # Test API factory
        from consolidated_api import create_dashboard_app
        app = create_dashboard_app(contexten_app=None)
        
        logger.info(f"✅ API factory successful - {app.title}")
        
        # Test dashboard factory
        from consolidated_dashboard import create_consolidated_dashboard
        dashboard = create_consolidated_dashboard(contexten_app=None)
        
        logger.info(f"✅ Dashboard factory successful - {dashboard.host}:{dashboard.port}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Factory functions failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_check():
    """Test environment variable checking."""
    logger.info("Testing environment check...")
    try:
        # Check required variables
        required_vars = ['CODEGEN_ORG_ID', 'CODEGEN_TOKEN']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.info(f"⚠️  Missing required variables: {missing_vars}")
            logger.info("   Dashboard will use mock implementations")
        else:
            logger.info("✅ All required environment variables present")
        
        # Check optional variables
        optional_vars = ['GITHUB_ACCESS_TOKEN', 'LINEAR_ACCESS_TOKEN', 'SLACK_BOT_TOKEN']
        missing_optional = []
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        if missing_optional:
            logger.info(f"ℹ️  Missing optional variables: {missing_optional}")
        else:
            logger.info("✅ All optional environment variables present")
        
        return True
    except Exception as e:
        logger.error(f"❌ Environment check failed: {e}")
        return False

def main():
    """Main test function."""
    logger.info("🚀 Testing Dashboard Entrypoints")
    logger.info("=" * 50)
    
    tests = [
        ("Environment Check", test_environment_check),
        ("Direct API Creation", test_direct_api_creation),
        ("Dashboard Creation", test_dashboard_creation),
        ("Factory Functions", test_factory_functions),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Report results
    logger.info("\n" + "=" * 50)
    logger.info("📊 ENTRYPOINT TEST RESULTS")
    logger.info("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:<20} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("-" * 50)
    logger.info(f"Total Tests: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    if failed == 0:
        logger.info("\n🎉 ALL ENTRYPOINT TESTS PASSED!")
        logger.info("✅ Dashboard can be started successfully")
        logger.info("✅ All factory functions work correctly")
        logger.info("✅ Environment configuration is validated")
        logger.info("\n🚀 Ready to start the dashboard with:")
        logger.info("   python consolidated_dashboard.py")
        logger.info("   or")
        logger.info("   python start_consolidated_dashboard.py")
        return True
    else:
        logger.info(f"\n⚠️  {failed} test(s) failed.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Tests crashed: {e}")
        sys.exit(1)

