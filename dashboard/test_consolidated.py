#!/usr/bin/env python3
"""
Quick test to verify the consolidated app.py works correctly
"""

import sys
import time
import subprocess
import threading
from pathlib import Path

def test_imports():
    """Test that all imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Test importing the consolidated app
        import app
        print("✅ app.py imports successfully")
        
        # Test that key components exist
        assert hasattr(app, 'analyzer'), "CodebaseAnalyzer not found"
        assert hasattr(app, 'api_app'), "FastAPI app not found"
        assert hasattr(app, 'app'), "Reflex app not found"
        assert hasattr(app, 'DashboardState'), "DashboardState not found"
        
        print("✅ All key components present")
        
        # Test analyzer functionality
        analysis_id = app.analyzer.generate_analysis_id()
        assert analysis_id.startswith("analysis_"), "Analysis ID generation failed"
        print(f"✅ Analysis ID generation works: {analysis_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_backend_startup():
    """Test that backend can start"""
    print("\n🚀 Testing backend startup...")
    
    try:
        # Start backend in a separate process
        process = subprocess.Popen([
            sys.executable, "-c", 
            "import sys; sys.path.insert(0, '.'); from app import start_backend; start_backend()"
        ], cwd=Path(__file__).parent)
        
        # Wait a moment for startup
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Backend started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            print("❌ Backend failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Backend startup test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔥 TESTING CONSOLIDATED DASHBOARD")
    print("=" * 50)
    
    # Test imports
    import_success = test_imports()
    
    # Test backend startup
    backend_success = test_backend_startup()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   Imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"   Backend: {'✅ PASS' if backend_success else '❌ FAIL'}")
    
    if import_success and backend_success:
        print("\n🎉 ALL TESTS PASSED - CONSOLIDATED SYSTEM READY!")
        print("\n🚀 TO RUN THE DASHBOARD:")
        print("   cd dashboard")
        print("   python app.py")
        print("\n🌐 THEN OPEN:")
        print("   Frontend: http://localhost:3000")
        print("   Backend API: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - CHECK CONFIGURATION")
        return 1

if __name__ == "__main__":
    sys.exit(main())
