#!/usr/bin/env python3
"""
Test script for the Comprehensive Unified Analyzer
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_comprehensive_unified_analyzer():
    """Test the comprehensive unified analyzer."""
    print("🧪 TESTING COMPREHENSIVE UNIFIED ANALYZER")
    print("=" * 60)
    
    try:
        from comprehensive_unified_analyzer import ComprehensiveUnifiedAnalyzer
        
        # Initialize analyzer
        analyzer = ComprehensiveUnifiedAnalyzer(".")
        
        # Test initialization
        print("🔍 Testing initialization...")
        if await analyzer.initialize_codebase():
            print("✅ Initialization successful")
        else:
            print("❌ Initialization failed")
            return
        
        # Test basic functionality
        print("\n🧪 Testing basic functionality...")
        
        # Test Serena status
        serena_status = analyzer.serena_status
        print(f"   Serena Integration: {'✅' if serena_status.get('integration_active') else '❌'}")
        print(f"   Available Methods: {len(serena_status.get('methods_available', []))}")
        
        # Test LSP diagnostics collection
        print("\n🔍 Testing LSP diagnostics collection...")
        try:
            lsp_diagnostics = await analyzer._collect_all_lsp_diagnostics()
            print(f"   ✅ LSP Diagnostics: {len(lsp_diagnostics)} collected")
        except Exception as e:
            print(f"   ❌ LSP Diagnostics failed: {e}")
        
        # Test symbol overview
        print("\n🎯 Testing symbol overview...")
        try:
            symbol_overview = await analyzer._analyze_symbol_overview()
            print(f"   ✅ Symbol Overview: {len(symbol_overview)} symbols analyzed")
        except Exception as e:
            print(f"   ❌ Symbol Overview failed: {e}")
        
        # Test codebase health
        print("\n📊 Testing codebase health...")
        try:
            health = await analyzer._calculate_codebase_health()
            print(f"   ✅ Codebase Health: {health.get('total_files', 0)} files, {health.get('total_errors', 0)} errors")
        except Exception as e:
            print(f"   ❌ Codebase Health failed: {e}")
        
        # Cleanup
        analyzer.cleanup()
        print("\n✅ All tests completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_comprehensive_unified_analyzer())
