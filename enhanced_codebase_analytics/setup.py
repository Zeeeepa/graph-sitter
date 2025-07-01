#!/usr/bin/env python3
"""
Setup script for Enhanced Codebase Analytics
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # Check if pip is available
    if not run_command("pip --version", "Checking pip"):
        print("❌ pip is not available. Please install pip first.")
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    # Try to install graph-sitter if not available
    try:
        import graph_sitter
        print("✅ graph-sitter is already available")
    except ImportError:
        print("📦 Installing graph-sitter...")
        if not run_command("pip install graph-sitter", "Installing graph-sitter"):
            print("⚠️  Warning: graph-sitter installation failed. You may need to install it manually.")
    
    return True


def verify_installation():
    """Verify that all components are working"""
    print("🔍 Verifying installation...")
    
    try:
        # Test imports
        sys.path.append(str(Path(__file__).parent / "backend"))
        
        from enhanced_analytics import EnhancedCodebaseAnalyzer
        print("✅ Core analytics module imported successfully")
        
        import flask
        print("✅ Flask imported successfully")
        
        import networkx
        print("✅ NetworkX imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def create_demo_data():
    """Create demo data directory if needed"""
    print("📁 Setting up demo data...")
    
    demo_dir = Path("demo_data")
    demo_dir.mkdir(exist_ok=True)
    
    # Create a simple demo file
    demo_file = demo_dir / "sample.py"
    if not demo_file.exists():
        demo_content = '''"""
Sample Python file for demo purposes
"""

def hello_world():
    """Simple hello world function"""
    print("Hello, World!")
    return "Hello, World!"

def complex_function(data):
    """A more complex function for testing"""
    result = []
    for item in data:
        if isinstance(item, str):
            if len(item) > 5:
                result.append(item.upper())
            else:
                result.append(item.lower())
        elif isinstance(item, int):
            if item > 10:
                result.append(item * 2)
            else:
                result.append(item + 1)
    return result

if __name__ == "__main__":
    hello_world()
    test_data = ["hello", "world", "test", 5, 15, 3]
    print(complex_function(test_data))
'''
        demo_file.write_text(demo_content)
        print("✅ Demo data created")
    else:
        print("✅ Demo data already exists")
    
    return True


def main():
    """Main setup function"""
    print("🚀 Enhanced Codebase Analytics Setup")
    print("=" * 40)
    print()
    
    # Check Python version
    if not check_python_version():
        return False
    
    print()
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    print()
    
    # Verify installation
    if not verify_installation():
        return False
    
    print()
    
    # Create demo data
    if not create_demo_data():
        return False
    
    print()
    print("🎉 Setup completed successfully!")
    print()
    print("🚀 Quick Start:")
    print("1. Run demo analysis:")
    print("   python run_demo.py")
    print()
    print("2. Start web dashboard:")
    print("   python backend/api_server.py")
    print("   Then open: http://localhost:5000")
    print()
    print("3. Run tests:")
    print("   python test_enhanced_analytics.py")
    print()
    print("📚 For more information, see README.md")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

