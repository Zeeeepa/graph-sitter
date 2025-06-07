#!/usr/bin/env python3
"""
Quick Dashboard Test Script
Tests the Material-UI dashboard setup and basic functionality.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def test_dashboard():
    """Test the dashboard setup and basic functionality."""
    print("🧪 Testing Material-UI Dashboard Setup")
    print("=" * 50)
    
    # Test 1: Check if required files exist
    print("📁 Checking file structure...")
    dashboard_dir = Path("src/contexten/extensions/dashboard")
    frontend_dir = dashboard_dir / "frontend"
    
    required_files = [
        frontend_dir / "public" / "index.html",
        frontend_dir / "public" / "manifest.json", 
        frontend_dir / "src" / "index.tsx",
        frontend_dir / "src" / "index.css",
        frontend_dir / "src" / "App.tsx",
        frontend_dir / "src" / "components" / "ProjectCard.tsx",
        frontend_dir / "package.json",
        dashboard_dir / "start_dashboard.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(str(file_path))
        else:
            print(f"✅ {file_path.name}")
    
    if missing_files:
        print("❌ Missing files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    # Test 2: Check package.json for Material-UI dependencies
    print("\n📦 Checking Material-UI dependencies...")
    package_json_path = frontend_dir / "package.json"
    
    try:
        import json
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        mui_deps = [
            "@mui/material",
            "@mui/icons-material", 
            "@emotion/react",
            "@emotion/styled"
        ]
        
        dependencies = package_data.get('dependencies', {})
        for dep in mui_deps:
            if dep in dependencies:
                print(f"✅ {dep}: {dependencies[dep]}")
            else:
                print(f"❌ Missing: {dep}")
                return False
                
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        return False
    
    # Test 3: Check if npm dependencies are installed
    print("\n🔧 Checking npm installation...")
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists():
        print("✅ node_modules directory exists")
        
        # Check for specific Material-UI modules
        mui_modules = [
            node_modules / "@mui" / "material",
            node_modules / "@mui" / "icons-material",
            node_modules / "@emotion" / "react"
        ]
        
        for module in mui_modules:
            if module.exists():
                print(f"✅ {module.name} installed")
            else:
                print(f"⚠️  {module.name} not found (may need npm install)")
    else:
        print("⚠️  node_modules not found - run 'npm install' in frontend directory")
    
    # Test 4: Test backend import
    print("\n🐍 Testing backend imports...")
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        # Test import
        from src.contexten.extensions.dashboard.start_dashboard import DashboardStarter
        print("✅ Backend imports working")
        
        # Test dashboard starter
        starter = DashboardStarter()
        print("✅ DashboardStarter initialized")
        
    except Exception as e:
        print(f"❌ Backend import error: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    print("=" * 50)
    print("🚀 Ready to launch dashboard with:")
    print("   cd src/contexten/extensions/dashboard")
    print("   python start_dashboard.py")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = test_dashboard()
    sys.exit(0 if success else 1)

