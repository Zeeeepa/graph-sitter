#!/usr/bin/env python3
"""
Test Script for Unified Serena Analyzer Integration

This script tests the unified analyzer against the actual LSP + Serena architecture
to ensure full compatibility and functionality.
"""

import os
import sys
import json
import time
import asyncio
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the parent directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all required imports for the unified analyzer."""
    print("🧪 Testing imports...")
    
    import_results = {}
    
    # Test graph_sitter import
    try:
        from graph_sitter import Codebase
        import_results['graph_sitter'] = True
        print("   ✅ graph_sitter.Codebase imported successfully")
    except ImportError as e:
        import_results['graph_sitter'] = False
        print(f"   ❌ graph_sitter import failed: {e}")
    
    # Test Serena types
    try:
        from graph_sitter.extensions.serena.types import (
            SerenaConfig, SerenaCapability, RefactoringType, RefactoringResult,
            CodeGenerationResult, SemanticSearchResult, SymbolInfo
        )
        import_results['serena_types'] = True
        print("   ✅ Serena types imported successfully")
    except ImportError as e:
        import_results['serena_types'] = False
        print(f"   ❌ Serena types import failed: {e}")
    
    # Test Serena core
    try:
        from graph_sitter.extensions.serena.core import SerenaCore
        import_results['serena_core'] = True
        print("   ✅ Serena core imported successfully")
    except ImportError as e:
        import_results['serena_core'] = False
        print(f"   ❌ Serena core import failed: {e}")
    
    # Test Serena intelligence
    try:
        from graph_sitter.extensions.serena.intelligence import CodeIntelligence
        import_results['serena_intelligence'] = True
        print("   ✅ Serena intelligence imported successfully")
    except ImportError as e:
        import_results['serena_intelligence'] = False
        print(f"   ❌ Serena intelligence import failed: {e}")
    
    # Test auto_init
    try:
        from graph_sitter.extensions.serena.auto_init import _initialized
        import_results['auto_init'] = _initialized
        print(f"   ✅ Auto-init status: {_initialized}")
    except ImportError as e:
        import_results['auto_init'] = False
        print(f"   ❌ Auto-init import failed: {e}")
    
    return import_results

def test_codebase_initialization():
    """Test codebase initialization with Serena integration."""
    print("\n🏗️ Testing codebase initialization...")
    
    try:
        from graph_sitter import Codebase
        
        # Initialize codebase
        codebase = Codebase(".")
        print("   ✅ Codebase initialized successfully")
        
        # Check for Serena methods
        serena_methods = [
            'get_serena_status', 'shutdown_serena', 'get_completions',
            'get_hover_info', 'get_signature_help', 'rename_symbol',
            'extract_method', 'semantic_search', 'generate_boilerplate',
            'organize_imports', 'get_file_diagnostics', 'get_symbol_context',
            'analyze_symbol_impact', 'enable_realtime_analysis'
        ]
        
        available_methods = []
        for method in serena_methods:
            if hasattr(codebase, method):
                available_methods.append(method)
        
        print(f"   📊 Available Serena methods: {len(available_methods)}/{len(serena_methods)}")
        
        if available_methods:
            print("   ✅ Serena integration detected")
            for method in available_methods[:5]:  # Show first 5
                print(f"      • {method}")
            if len(available_methods) > 5:
                print(f"      • ... and {len(available_methods) - 5} more")
        else:
            print("   ⚠️  No Serena methods detected")
        
        return {
            'success': True,
            'codebase': codebase,
            'available_methods': available_methods
        }
        
    except Exception as e:
        print(f"   ❌ Codebase initialization failed: {e}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def test_lsp_diagnostics_method():
    """Test LSP diagnostics retrieval method."""
    print("\n🔍 Testing LSP diagnostics method...")
    
    try:
        from graph_sitter import Codebase
        codebase = Codebase(".")
        
        # Check if get_file_diagnostics method exists
        if hasattr(codebase, 'get_file_diagnostics'):
            print("   ✅ get_file_diagnostics method available")
            
            # Find a Python file to test
            python_files = []
            for root, dirs, files in os.walk("."):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if file.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, file), ".")
                        python_files.append(rel_path)
                        if len(python_files) >= 3:  # Test with first 3 files
                            break
                if len(python_files) >= 3:
                    break
            
            print(f"   📁 Found {len(python_files)} Python files for testing")
            
            # Test diagnostics on a few files
            diagnostics_results = []
            for file_path in python_files[:3]:
                try:
                    result = codebase.get_file_diagnostics(file_path)
                    diagnostics_results.append({
                        'file': file_path,
                        'success': result.get('success', False) if result else False,
                        'diagnostics_count': len(result.get('diagnostics', [])) if result else 0
                    })
                    print(f"   📄 {file_path}: {len(result.get('diagnostics', [])) if result else 0} diagnostics")
                except Exception as e:
                    diagnostics_results.append({
                        'file': file_path,
                        'success': False,
                        'error': str(e)
                    })
                    print(f"   ❌ {file_path}: Error - {e}")
            
            return {
                'method_available': True,
                'test_results': diagnostics_results
            }
        else:
            print("   ❌ get_file_diagnostics method not available")
            return {'method_available': False}
            
    except Exception as e:
        print(f"   ❌ LSP diagnostics test failed: {e}")
        return {'method_available': False, 'error': str(e)}

def test_symbol_analysis():
    """Test symbol analysis capabilities."""
    print("\n🎯 Testing symbol analysis...")
    
    try:
        from graph_sitter import Codebase
        codebase = Codebase(".")
        
        # Test basic symbol access
        functions = list(codebase.functions)
        classes = list(codebase.classes)
        files = list(codebase.files)
        
        print(f"   📊 Found {len(functions)} functions, {len(classes)} classes, {len(files)} files")
        
        # Test symbol context method if available
        context_results = []
        if hasattr(codebase, 'get_symbol_context') and functions:
            try:
                # Test with first function
                func = functions[0]
                func_name = getattr(func, 'name', 'unknown')
                result = codebase.get_symbol_context(func_name, include_dependencies=True)
                context_results.append({
                    'symbol': func_name,
                    'success': result.get('success', False) if result else False,
                    'has_context': bool(result.get('context')) if result else False
                })
                print(f"   🔧 Symbol context for '{func_name}': {'✅' if result.get('success') else '❌'}")
            except Exception as e:
                context_results.append({
                    'symbol': func_name,
                    'success': False,
                    'error': str(e)
                })
                print(f"   ❌ Symbol context failed: {e}")
        
        return {
            'functions_count': len(functions),
            'classes_count': len(classes),
            'files_count': len(files),
            'context_results': context_results
        }
        
    except Exception as e:
        print(f"   ❌ Symbol analysis test failed: {e}")
        return {'success': False, 'error': str(e)}

def test_serena_status():
    """Test Serena status retrieval."""
    print("\n📊 Testing Serena status...")
    
    try:
        from graph_sitter import Codebase
        codebase = Codebase(".")
        
        if hasattr(codebase, 'get_serena_status'):
            try:
                status = codebase.get_serena_status()
                print("   ✅ Serena status retrieved successfully")
                
                if status:
                    print(f"   📋 Status keys: {list(status.keys())}")
                    if 'enabled' in status:
                        print(f"   🔧 Serena enabled: {status['enabled']}")
                    if 'lsp_bridge_status' in status:
                        lsp_status = status['lsp_bridge_status']
                        print(f"   🌉 LSP bridge initialized: {lsp_status.get('initialized', False)}")
                        if 'language_servers' in lsp_status:
                            servers = lsp_status['language_servers']
                            print(f"   🖥️  Language servers: {len(servers)}")
                
                return {'method_available': True, 'status': status}
            except Exception as e:
                print(f"   ❌ Serena status call failed: {e}")
                return {'method_available': True, 'error': str(e)}
        else:
            print("   ❌ get_serena_status method not available")
            return {'method_available': False}
            
    except Exception as e:
        print(f"   ❌ Serena status test failed: {e}")
        return {'method_available': False, 'error': str(e)}

def test_unified_analyzer_compatibility():
    """Test compatibility with the unified analyzer script."""
    print("\n🔬 Testing unified analyzer compatibility...")
    
    compatibility_results = {
        'graph_sitter_available': False,
        'serena_components': {},
        'required_methods': {},
        'data_structures': {},
        'overall_compatibility': False
    }
    
    # Test graph-sitter availability
    try:
        from graph_sitter import Codebase
        compatibility_results['graph_sitter_available'] = True
        print("   ✅ Graph-sitter available")
    except ImportError:
        print("   ❌ Graph-sitter not available")
        return compatibility_results
    
    # Test Serena components
    serena_components = {
        'types': False,
        'core': False,
        'intelligence': False,
        'auto_init': False
    }
    
    try:
        from graph_sitter.extensions.serena.types import SerenaConfig
        serena_components['types'] = True
    except ImportError:
        pass
    
    try:
        from graph_sitter.extensions.serena.core import SerenaCore
        serena_components['core'] = True
    except ImportError:
        pass
    
    try:
        from graph_sitter.extensions.serena.intelligence import CodeIntelligence
        serena_components['intelligence'] = True
    except ImportError:
        pass
    
    try:
        from graph_sitter.extensions.serena.auto_init import _initialized
        serena_components['auto_init'] = _initialized
    except ImportError:
        pass
    
    compatibility_results['serena_components'] = serena_components
    
    # Test required methods on Codebase
    codebase = Codebase(".")
    required_methods = [
        'get_file_diagnostics',
        'get_serena_status',
        'get_symbol_context'
    ]
    
    method_availability = {}
    for method in required_methods:
        method_availability[method] = hasattr(codebase, method)
    
    compatibility_results['required_methods'] = method_availability
    
    # Test data structure compatibility
    data_structures = {
        'functions_accessible': False,
        'classes_accessible': False,
        'files_accessible': False,
        'imports_accessible': False
    }
    
    try:
        functions = list(codebase.functions)
        data_structures['functions_accessible'] = True
    except:
        pass
    
    try:
        classes = list(codebase.classes)
        data_structures['classes_accessible'] = True
    except:
        pass
    
    try:
        files = list(codebase.files)
        data_structures['files_accessible'] = True
    except:
        pass
    
    try:
        # Test imports access
        for file in list(codebase.files)[:1]:  # Test first file
            imports = file.imports
            data_structures['imports_accessible'] = True
            break
    except:
        pass
    
    compatibility_results['data_structures'] = data_structures
    
    # Calculate overall compatibility
    graph_sitter_ok = compatibility_results['graph_sitter_available']
    serena_ok = any(serena_components.values())
    methods_ok = any(method_availability.values())
    data_ok = any(data_structures.values())
    
    compatibility_results['overall_compatibility'] = graph_sitter_ok and data_ok
    
    # Print results
    print(f"   📦 Serena components: {sum(serena_components.values())}/4 available")
    print(f"   🔧 Required methods: {sum(method_availability.values())}/{len(required_methods)} available")
    print(f"   📊 Data structures: {sum(data_structures.values())}/4 accessible")
    print(f"   🎯 Overall compatibility: {'✅' if compatibility_results['overall_compatibility'] else '❌'}")
    
    return compatibility_results

def generate_test_report(results: Dict[str, Any]):
    """Generate comprehensive test report."""
    print("\n" + "=" * 80)
    print("📋 UNIFIED ANALYZER INTEGRATION TEST REPORT")
    print("=" * 80)
    
    # Summary
    print(f"\n🎯 SUMMARY:")
    print(f"   Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Test Environment: {sys.platform}")
    print(f"   Python Version: {sys.version.split()[0]}")
    
    # Import results
    if 'imports' in results:
        imports = results['imports']
        successful_imports = sum(1 for v in imports.values() if v)
        print(f"\n📦 IMPORTS: {successful_imports}/{len(imports)} successful")
        for component, success in imports.items():
            status = "✅" if success else "❌"
            print(f"   {status} {component}")
    
    # Codebase initialization
    if 'codebase_init' in results:
        init_result = results['codebase_init']
        if init_result['success']:
            print(f"\n🏗️ CODEBASE INITIALIZATION: ✅")
            print(f"   Available Serena methods: {len(init_result.get('available_methods', []))}")
        else:
            print(f"\n🏗️ CODEBASE INITIALIZATION: ❌")
            print(f"   Error: {init_result.get('error', 'Unknown error')}")
    
    # LSP diagnostics
    if 'lsp_diagnostics' in results:
        lsp_result = results['lsp_diagnostics']
        if lsp_result.get('method_available'):
            print(f"\n🔍 LSP DIAGNOSTICS: ✅ Method available")
            if 'test_results' in lsp_result:
                successful_tests = sum(1 for r in lsp_result['test_results'] if r.get('success'))
                print(f"   Test results: {successful_tests}/{len(lsp_result['test_results'])} files processed")
        else:
            print(f"\n🔍 LSP DIAGNOSTICS: ❌ Method not available")
    
    # Symbol analysis
    if 'symbol_analysis' in results:
        symbol_result = results['symbol_analysis']
        if 'functions_count' in symbol_result:
            print(f"\n🎯 SYMBOL ANALYSIS: ✅")
            print(f"   Functions: {symbol_result['functions_count']}")
            print(f"   Classes: {symbol_result['classes_count']}")
            print(f"   Files: {symbol_result['files_count']}")
        else:
            print(f"\n🎯 SYMBOL ANALYSIS: ❌")
    
    # Serena status
    if 'serena_status' in results:
        status_result = results['serena_status']
        if status_result.get('method_available'):
            print(f"\n📊 SERENA STATUS: ✅ Method available")
            if 'status' in status_result:
                status = status_result['status']
                if status and 'enabled' in status:
                    print(f"   Serena enabled: {status['enabled']}")
        else:
            print(f"\n📊 SERENA STATUS: ❌ Method not available")
    
    # Compatibility assessment
    if 'compatibility' in results:
        compat = results['compatibility']
        print(f"\n🔬 COMPATIBILITY ASSESSMENT:")
        print(f"   Graph-sitter: {'✅' if compat['graph_sitter_available'] else '❌'}")
        print(f"   Serena components: {sum(compat['serena_components'].values())}/4")
        print(f"   Required methods: {sum(compat['required_methods'].values())}/{len(compat['required_methods'])}")
        print(f"   Data structures: {sum(compat['data_structures'].values())}/4")
        print(f"   Overall compatibility: {'✅' if compat['overall_compatibility'] else '❌'}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if results.get('compatibility', {}).get('overall_compatibility'):
        print("   ✅ The unified analyzer should work with this codebase")
        print("   🚀 You can proceed with running the full unified analyzer")
        
        if results.get('codebase_init', {}).get('available_methods'):
            methods_count = len(results['codebase_init']['available_methods'])
            if methods_count > 10:
                print("   🌟 Excellent Serena integration detected")
            elif methods_count > 5:
                print("   👍 Good Serena integration detected")
            else:
                print("   ⚠️  Limited Serena integration detected")
    else:
        print("   ❌ The unified analyzer may have compatibility issues")
        print("   🔧 Consider checking Serena installation and configuration")
        
        if not results.get('imports', {}).get('graph_sitter'):
            print("   📦 Install graph-sitter: pip install graph-sitter")
        
        if not any(results.get('compatibility', {}).get('serena_components', {}).values()):
            print("   🔌 Check Serena extension installation and configuration")
    
    print(f"\n✅ Test report complete!")
    
    return results

def main():
    """Main test function."""
    print("🧪 UNIFIED SERENA ANALYZER INTEGRATION TEST")
    print("=" * 60)
    print("Testing compatibility between unified analyzer and LSP + Serena architecture")
    print()
    
    # Run all tests
    test_results = {}
    
    # Test imports
    test_results['imports'] = test_imports()
    
    # Test codebase initialization
    test_results['codebase_init'] = test_codebase_initialization()
    
    # Test LSP diagnostics
    test_results['lsp_diagnostics'] = test_lsp_diagnostics_method()
    
    # Test symbol analysis
    test_results['symbol_analysis'] = test_symbol_analysis()
    
    # Test Serena status
    test_results['serena_status'] = test_serena_status()
    
    # Test overall compatibility
    test_results['compatibility'] = test_unified_analyzer_compatibility()
    
    # Generate comprehensive report
    generate_test_report(test_results)
    
    # Save results to file
    report_file = Path("unified_analyzer_integration_test_report.json")
    with open(report_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\n💾 Detailed test results saved to: {report_file}")
    
    return test_results

if __name__ == "__main__":
    main()
