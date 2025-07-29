#!/usr/bin/env python3
"""
Test Script for Web-Eval-Agent Repository

This script tests the Serena integration specifically on the web-eval-agent repository.
It can be run from the web-eval-agent directory to test all Serena features.

Usage:
    # From web-eval-agent repository root:
    python path/to/graph-sitter/examples/test_web_eval_agent.py
    
    # Or with custom path:
    python path/to/graph-sitter/examples/test_web_eval_agent.py --graph-sitter-path /path/to/graph-sitter
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

def setup_graph_sitter_path(graph_sitter_path: str):
    """Add graph-sitter src to Python path."""
    src_path = Path(graph_sitter_path) / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        print(f"✅ Added graph-sitter src to path: {src_path}")
        return True
    else:
        print(f"❌ Graph-sitter src not found: {src_path}")
        return False

async def test_web_eval_agent():
    """Test Serena features on web-eval-agent repository."""
    print("🌐 Testing Serena on Web-Eval-Agent Repository")
    print("=" * 60)
    
    # Get current directory (should be web-eval-agent root)
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check if this looks like web-eval-agent
    expected_files = ['README.md', 'requirements.txt', 'setup.py']
    web_eval_indicators = ['web_eval', 'eval_agent', 'browser', 'playwright']
    
    has_expected_files = any((current_dir / f).exists() for f in expected_files)
    has_web_eval_content = False
    
    # Check for web-eval-agent specific content
    for indicator in web_eval_indicators:
        if any(indicator in p.name.lower() for p in current_dir.iterdir() if p.is_dir()):
            has_web_eval_content = True
            break
    
    if not (has_expected_files or has_web_eval_content):
        print("⚠️  This doesn't appear to be the web-eval-agent repository")
        print("   Please run this script from the web-eval-agent root directory")
        return False
    
    print("✅ Detected web-eval-agent repository structure")
    
    try:
        # Import the comprehensive demo
        from comprehensive_serena_demo import ComprehensiveSerenaDemo
        
        print("\n🚀 Starting Comprehensive Serena Test...")
        
        # Run the demo on current directory
        demo = ComprehensiveSerenaDemo(str(current_dir))
        results = await demo.run_comprehensive_demo(test_all=True)
        
        # Display web-eval-agent specific results
        print("\n🌐 Web-Eval-Agent Specific Analysis")
        print("-" * 50)
        
        # Analyze Python files in the repository
        python_files = list(current_dir.rglob("*.py"))
        print(f"   • Python files found: {len(python_files)}")
        
        # Look for specific web-eval-agent patterns
        web_eval_files = [f for f in python_files if any(
            keyword in f.name.lower() or keyword in str(f.parent).lower()
            for keyword in ['web', 'eval', 'agent', 'browser', 'playwright']
        )]
        print(f"   • Web-eval related files: {len(web_eval_files)}")
        
        # Test Serena on key files
        if web_eval_files:
            print(f"\n🔍 Testing Serena on key web-eval-agent files:")
            
            for i, file_path in enumerate(web_eval_files[:5]):  # Test first 5 files
                try:
                    if demo.codebase:
                        # Test completions
                        completions = await demo.codebase.get_completions(str(file_path), 10, 0)
                        
                        # Test diagnostics
                        diagnostics = await demo.codebase.get_diagnostics(str(file_path))
                        
                        print(f"   • {file_path.name}: {len(completions)} completions, {len(diagnostics)} diagnostics")
                        
                except Exception as e:
                    print(f"   • {file_path.name}: Error - {e}")
        
        # Summary for web-eval-agent
        total_tests = results['total_tests']
        passed_tests = results['passed_tests']
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 Web-Eval-Agent Integration Results:")
        print(f"   • Total tests: {total_tests}")
        print(f"   • Passed: {passed_tests}")
        print(f"   • Success rate: {success_rate:.1f}%")
        print(f"   • Status: {'🎉 Ready for use!' if success_rate >= 70 else '⚠️  Needs attention'}")
        
        return success_rate >= 70
        
    except ImportError as e:
        print(f"❌ Could not import Serena demo: {e}")
        print("   Make sure graph-sitter is properly installed and in the Python path")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test Serena on Web-Eval-Agent')
    parser.add_argument('--graph-sitter-path', 
                       help='Path to graph-sitter repository (auto-detected if not provided)')
    
    args = parser.parse_args()
    
    # Auto-detect graph-sitter path if not provided
    if args.graph_sitter_path:
        graph_sitter_path = args.graph_sitter_path
    else:
        # Try to find graph-sitter in common locations
        possible_paths = [
            Path(__file__).parent.parent,  # Assuming script is in graph-sitter/examples/
            Path.cwd().parent / "graph-sitter",
            Path.home() / "graph-sitter",
            Path("/tmp/graph-sitter")
        ]
        
        graph_sitter_path = None
        for path in possible_paths:
            if (path / "src" / "graph_sitter").exists():
                graph_sitter_path = str(path)
                break
        
        if not graph_sitter_path:
            print("❌ Could not auto-detect graph-sitter path")
            print("   Please specify --graph-sitter-path")
            return 1
    
    print(f"🔍 Using graph-sitter path: {graph_sitter_path}")
    
    # Setup Python path
    if not setup_graph_sitter_path(graph_sitter_path):
        return 1
    
    # Add examples directory to path for importing the demo
    examples_path = Path(graph_sitter_path) / "examples"
    if examples_path.exists():
        sys.path.insert(0, str(examples_path))
    
    # Run the test
    success = await test_web_eval_agent()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
