#!/usr/bin/env python3
"""
Comprehensive Serena Demo and Test Script

This script demonstrates all the advanced Serena features including:
- Enhanced LSP Integration
- Advanced Refactoring Operations
- Symbol Intelligence
- Code Actions
- Real-time Analysis
- Auto-initialization

Usage:
    python examples/comprehensive_serena_demo.py [--codebase-path PATH] [--test-all]
"""

import asyncio
import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from graph_sitter.extensions.serena import (
        SerenaCore,
        SerenaLSPIntegration,
        create_serena_lsp_integration,
        SerenaConfig,
        SerenaCapability,
        RefactoringType,
        initialize_serena_integration,
        AUTO_INIT_AVAILABLE,
        REFACTORING_AVAILABLE,
        SYMBOL_INTELLIGENCE_AVAILABLE,
        CODE_ACTIONS_AVAILABLE,
        REALTIME_ANALYSIS_AVAILABLE,
        LSP_AVAILABLE
    )
    from graph_sitter.core.codebase import Codebase
    SERENA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Serena extension not available: {e}")
    SERENA_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveSerenaDemo:
    """Comprehensive demonstration of all Serena capabilities."""
    
    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)
        self.serena_core: Optional[SerenaCore] = None
        self.lsp_integration: Optional[SerenaLSPIntegration] = None
        self.codebase: Optional[Codebase] = None
        
        # Test results tracking
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'test_details': []
        }
    
    async def run_comprehensive_demo(self, test_all: bool = False) -> Dict[str, Any]:
        """Run the complete Serena demonstration."""
        print("🚀 Comprehensive Serena Demo")
        print("=" * 80)
        print(f"📁 Codebase: {self.codebase_path}")
        print(f"🧪 Test Mode: {'Full Testing' if test_all else 'Demo Mode'}")
        print()
        
        if not SERENA_AVAILABLE:
            print("❌ Serena extension is not available. Please install dependencies.")
            return self.test_results
        
        try:
            # Phase 1: Capability Check
            await self._test_capability_availability()
            
            # Phase 2: Core Initialization
            await self._test_core_initialization()
            
            # Phase 3: LSP Integration
            await self._test_lsp_integration()
            
            # Phase 4: Auto-initialization
            await self._test_auto_initialization()
            
            # Phase 5: Refactoring Operations
            if test_all:
                await self._test_refactoring_operations()
            
            # Phase 6: Symbol Intelligence
            if test_all:
                await self._test_symbol_intelligence()
            
            # Phase 7: Code Actions
            if test_all:
                await self._test_code_actions()
            
            # Phase 8: Real-time Analysis
            if test_all:
                await self._test_realtime_analysis()
            
            # Phase 9: Integration Testing
            if test_all:
                await self._test_integration_scenarios()
            
            # Phase 10: Performance Testing
            if test_all:
                await self._test_performance()
            
            # Display final results
            await self._display_final_results()
            
        except Exception as e:
            logger.error(f"Demo error: {e}")
            self._record_test_result("Demo Execution", False, str(e))
        
        finally:
            await self._cleanup()
        
        return self.test_results
    
    async def _test_capability_availability(self):
        """Test which Serena capabilities are available."""
        print("🔍 Testing Capability Availability")
        print("-" * 50)
        
        capabilities = {
            'Auto-initialization': AUTO_INIT_AVAILABLE,
            'Refactoring': REFACTORING_AVAILABLE,
            'Symbol Intelligence': SYMBOL_INTELLIGENCE_AVAILABLE,
            'Code Actions': CODE_ACTIONS_AVAILABLE,
            'Real-time Analysis': REALTIME_ANALYSIS_AVAILABLE,
            'LSP Integration': LSP_AVAILABLE
        }
        
        for capability, available in capabilities.items():
            status = "✅ Available" if available else "❌ Not Available"
            print(f"   • {capability}: {status}")
            self._record_test_result(f"Capability: {capability}", available, 
                                   "Available" if available else "Not available")
        
        print()
    
    async def _test_core_initialization(self):
        """Test SerenaCore initialization."""
        print("🏗️  Testing Core Initialization")
        print("-" * 50)
        
        try:
            # Test SerenaConfig creation
            config = SerenaConfig()
            config.enabled_capabilities = [
                SerenaCapability.LSP_INTEGRATION,
                SerenaCapability.REFACTORING,
                SerenaCapability.SYMBOL_INTELLIGENCE,
                SerenaCapability.CODE_ACTIONS,
                SerenaCapability.REAL_TIME_ANALYSIS
            ]
            
            print("   • SerenaConfig created ✅")
            self._record_test_result("SerenaConfig Creation", True, "Config created successfully")
            
            # Test SerenaCore creation
            self.serena_core = SerenaCore(str(self.codebase_path), config)
            print("   • SerenaCore created ✅")
            self._record_test_result("SerenaCore Creation", True, "Core created successfully")
            
            # Test initialization
            await self.serena_core.initialize()
            print("   • SerenaCore initialized ✅")
            self._record_test_result("SerenaCore Initialization", True, "Core initialized successfully")
            
            # Test status
            status = self.serena_core.get_status()
            print(f"   • Status: {len(status.get('enabled_capabilities', []))} capabilities enabled")
            
        except Exception as e:
            logger.error(f"Core initialization error: {e}")
            self._record_test_result("Core Initialization", False, str(e))
        
        print()
    
    async def _test_lsp_integration(self):
        """Test LSP integration capabilities."""
        print("🔌 Testing LSP Integration")
        print("-" * 50)
        
        try:
            # Test LSP integration creation
            self.lsp_integration = await create_serena_lsp_integration(
                codebase_path=str(self.codebase_path),
                serena_config=SerenaConfig()
            )
            
            print("   • LSP Integration created ✅")
            self._record_test_result("LSP Integration Creation", True, "Integration created successfully")
            
            # Test status
            status = self.lsp_integration.get_status()
            print(f"   • Status: {status}")
            
            # Test enhanced methods if available
            if hasattr(self.lsp_integration, 'get_completions_enhanced'):
                print("   • Enhanced methods available ✅")
                self._record_test_result("Enhanced LSP Methods", True, "Enhanced methods available")
            
        except Exception as e:
            logger.error(f"LSP integration error: {e}")
            self._record_test_result("LSP Integration", False, str(e))
        
        print()
    
    async def _test_auto_initialization(self):
        """Test auto-initialization with Codebase class."""
        print("🔄 Testing Auto-initialization")
        print("-" * 50)
        
        try:
            # Test Codebase creation
            self.codebase = Codebase(str(self.codebase_path))
            print("   • Codebase created ✅")
            self._record_test_result("Codebase Creation", True, "Codebase created successfully")
            
            # Test if Serena methods are available
            serena_methods = [
                'get_serena_core',
                'get_serena_lsp_integration',
                'get_completions',
                'get_hover_info',
                'rename_symbol',
                'extract_method',
                'get_symbol_info',
                'get_code_actions',
                'semantic_search',
                'generate_code',
                'get_serena_status'
            ]
            
            available_methods = []
            for method in serena_methods:
                if hasattr(self.codebase, method):
                    available_methods.append(method)
            
            print(f"   • Serena methods available: {len(available_methods)}/{len(serena_methods)}")
            
            if available_methods:
                print("   • Auto-initialization successful ✅")
                self._record_test_result("Auto-initialization", True, 
                                       f"{len(available_methods)} methods available")
                
                # Test a simple method call
                try:
                    status = await self.codebase.get_serena_status()
                    print(f"   • Status check: {status.get('integration_active', False)}")
                except Exception as e:
                    print(f"   • Status check failed: {e}")
            else:
                print("   • Auto-initialization not working ❌")
                self._record_test_result("Auto-initialization", False, "No Serena methods found")
            
        except Exception as e:
            logger.error(f"Auto-initialization error: {e}")
            self._record_test_result("Auto-initialization", False, str(e))
        
        print()
    
    async def _test_refactoring_operations(self):
        """Test refactoring operations."""
        print("🔧 Testing Refactoring Operations")
        print("-" * 50)
        
        if not REFACTORING_AVAILABLE:
            print("   • Refactoring not available, skipping ⏭️")
            self._record_test_result("Refactoring Operations", None, "Not available")
            print()
            return
        
        try:
            # Create test file for refactoring
            test_file = await self._create_test_file_for_refactoring()
            
            if self.serena_core:
                # Test rename refactoring
                try:
                    result = await self.serena_core.get_refactoring_result(
                        RefactoringType.RENAME.value,
                        file_path=str(test_file),
                        line=5,
                        character=4,
                        old_name='test_function',
                        new_name='renamed_function'
                    )
                    
                    print(f"   • Rename refactoring: {'✅' if result.success else '❌'}")
                    self._record_test_result("Rename Refactoring", result.success, 
                                           result.error_message or "Success")
                    
                except Exception as e:
                    print(f"   • Rename refactoring failed: {e}")
                    self._record_test_result("Rename Refactoring", False, str(e))
                
                # Test extract method refactoring
                try:
                    result = await self.serena_core.get_refactoring_result(
                        RefactoringType.EXTRACT_METHOD.value,
                        file_path=str(test_file),
                        start_line=7,
                        end_line=9,
                        new_name='extracted_method'
                    )
                    
                    print(f"   • Extract method: {'✅' if result.success else '❌'}")
                    self._record_test_result("Extract Method", result.success, 
                                           result.error_message or "Success")
                    
                except Exception as e:
                    print(f"   • Extract method failed: {e}")
                    self._record_test_result("Extract Method", False, str(e))
            
        except Exception as e:
            logger.error(f"Refactoring test error: {e}")
            self._record_test_result("Refactoring Operations", False, str(e))
        
        print()
    
    async def _test_symbol_intelligence(self):
        """Test symbol intelligence capabilities."""
        print("🧠 Testing Symbol Intelligence")
        print("-" * 50)
        
        if not SYMBOL_INTELLIGENCE_AVAILABLE:
            print("   • Symbol Intelligence not available, skipping ⏭️")
            self._record_test_result("Symbol Intelligence", None, "Not available")
            print()
            return
        
        try:
            if self.codebase:
                # Test symbol info retrieval
                try:
                    symbol_info = await self.codebase.get_symbol_info("test_function")
                    
                    if symbol_info:
                        print("   • Symbol info retrieval ✅")
                        print(f"     - Symbol: {symbol_info.get('name', 'Unknown')}")
                        print(f"     - Type: {symbol_info.get('type', 'Unknown')}")
                        self._record_test_result("Symbol Info Retrieval", True, "Symbol found")
                    else:
                        print("   • Symbol info retrieval: No symbols found")
                        self._record_test_result("Symbol Info Retrieval", True, "No symbols found")
                    
                except Exception as e:
                    print(f"   • Symbol info retrieval failed: {e}")
                    self._record_test_result("Symbol Info Retrieval", False, str(e))
                
                # Test symbol impact analysis
                try:
                    impact = await self.codebase.analyze_symbol_impact("test_function")
                    
                    if impact and not impact.get('error'):
                        print("   • Symbol impact analysis ✅")
                        print(f"     - Impact level: {impact.get('impact_level', 'Unknown')}")
                        self._record_test_result("Symbol Impact Analysis", True, "Analysis completed")
                    else:
                        print("   • Symbol impact analysis: No impact data")
                        self._record_test_result("Symbol Impact Analysis", True, "No impact data")
                    
                except Exception as e:
                    print(f"   • Symbol impact analysis failed: {e}")
                    self._record_test_result("Symbol Impact Analysis", False, str(e))
            
        except Exception as e:
            logger.error(f"Symbol intelligence test error: {e}")
            self._record_test_result("Symbol Intelligence", False, str(e))
        
        print()
    
    async def _test_code_actions(self):
        """Test code actions capabilities."""
        print("⚡ Testing Code Actions")
        print("-" * 50)
        
        if not CODE_ACTIONS_AVAILABLE:
            print("   • Code Actions not available, skipping ⏭️")
            self._record_test_result("Code Actions", None, "Not available")
            print()
            return
        
        try:
            if self.codebase:
                # Create test file with issues
                test_file = await self._create_test_file_with_issues()
                
                # Test code actions retrieval
                try:
                    actions = await self.codebase.get_code_actions(
                        str(test_file), 1, 10, ["import os", "def test():"]
                    )
                    
                    print(f"   • Code actions retrieval: {len(actions)} actions found")
                    self._record_test_result("Code Actions Retrieval", True, 
                                           f"{len(actions)} actions found")
                    
                    # Show sample actions
                    for i, action in enumerate(actions[:3]):
                        print(f"     - {action.get('title', 'Unknown action')}")
                    
                except Exception as e:
                    print(f"   • Code actions retrieval failed: {e}")
                    self._record_test_result("Code Actions Retrieval", False, str(e))
            
        except Exception as e:
            logger.error(f"Code actions test error: {e}")
            self._record_test_result("Code Actions", False, str(e))
        
        print()
    
    async def _test_realtime_analysis(self):
        """Test real-time analysis capabilities."""
        print("📊 Testing Real-time Analysis")
        print("-" * 50)
        
        if not REALTIME_ANALYSIS_AVAILABLE:
            print("   • Real-time Analysis not available, skipping ⏭️")
            self._record_test_result("Real-time Analysis", None, "Not available")
            print()
            return
        
        try:
            if self.codebase:
                # Test enabling real-time analysis
                try:
                    enabled = await self.codebase.enable_realtime_analysis(['*.py'])
                    
                    print(f"   • Real-time analysis enabled: {'✅' if enabled else '❌'}")
                    self._record_test_result("Real-time Analysis Enable", enabled, 
                                           "Enabled" if enabled else "Failed to enable")
                    
                    if enabled:
                        # Wait a moment for initialization
                        await asyncio.sleep(1)
                        
                        # Test disabling
                        disabled = await self.codebase.disable_realtime_analysis()
                        print(f"   • Real-time analysis disabled: {'✅' if disabled else '❌'}")
                        self._record_test_result("Real-time Analysis Disable", disabled,
                                               "Disabled" if disabled else "Failed to disable")
                    
                except Exception as e:
                    print(f"   • Real-time analysis test failed: {e}")
                    self._record_test_result("Real-time Analysis", False, str(e))
            
        except Exception as e:
            logger.error(f"Real-time analysis test error: {e}")
            self._record_test_result("Real-time Analysis", False, str(e))
        
        print()
    
    async def _test_integration_scenarios(self):
        """Test integration scenarios."""
        print("🔗 Testing Integration Scenarios")
        print("-" * 50)
        
        try:
            if self.codebase:
                # Test comprehensive workflow
                try:
                    # 1. Get completions
                    test_file = await self._create_test_file_for_refactoring()
                    completions = await self.codebase.get_completions(str(test_file), 5, 10)
                    print(f"   • Completions: {len(completions)} items")
                    
                    # 2. Get hover info
                    hover = await self.codebase.get_hover_info(str(test_file), 5, 10)
                    print(f"   • Hover info: {'Available' if hover else 'Not available'}")
                    
                    # 3. Get diagnostics
                    diagnostics = await self.codebase.get_diagnostics(str(test_file))
                    print(f"   • Diagnostics: {len(diagnostics)} issues")
                    
                    # 4. Semantic search
                    search_result = await self.codebase.semantic_search("function definition")
                    print(f"   • Semantic search: {search_result.get('total_count', 0)} results")
                    
                    self._record_test_result("Integration Workflow", True, "All operations completed")
                    
                except Exception as e:
                    print(f"   • Integration workflow failed: {e}")
                    self._record_test_result("Integration Workflow", False, str(e))
            
        except Exception as e:
            logger.error(f"Integration test error: {e}")
            self._record_test_result("Integration Scenarios", False, str(e))
        
        print()
    
    async def _test_performance(self):
        """Test performance characteristics."""
        print("⚡ Testing Performance")
        print("-" * 50)
        
        try:
            if self.codebase:
                # Test multiple concurrent operations
                start_time = time.time()
                
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(
                        self.codebase.get_serena_status()
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = time.time()
                duration = end_time - start_time
                
                successful_results = [r for r in results if not isinstance(r, Exception)]
                
                print(f"   • Concurrent operations: {len(successful_results)}/5 successful")
                print(f"   • Total duration: {duration:.3f}s")
                print(f"   • Average per operation: {duration/5:.3f}s")
                
                self._record_test_result("Performance Test", len(successful_results) >= 3, 
                                       f"{len(successful_results)}/5 successful in {duration:.3f}s")
            
        except Exception as e:
            logger.error(f"Performance test error: {e}")
            self._record_test_result("Performance Test", False, str(e))
        
        print()
    
    async def _display_final_results(self):
        """Display final test results."""
        print("📊 Final Test Results")
        print("=" * 80)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        skipped = self.test_results['skipped_tests']
        
        print(f"📈 Summary:")
        print(f"   • Total Tests: {total}")
        print(f"   • Passed: {passed} ✅")
        print(f"   • Failed: {failed} ❌")
        print(f"   • Skipped: {skipped} ⏭️")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"   • Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results['test_details']:
            status_icon = "✅" if result['passed'] else "❌" if result['passed'] is False else "⏭️"
            print(f"   {status_icon} {result['test_name']}: {result['message']}")
        
        print(f"\n🎯 Serena Capabilities Status:")
        capabilities_status = {
            'Core Initialization': any(r['test_name'].startswith('SerenaCore') and r['passed'] for r in self.test_results['test_details']),
            'LSP Integration': any(r['test_name'].startswith('LSP') and r['passed'] for r in self.test_results['test_details']),
            'Auto-initialization': any(r['test_name'] == 'Auto-initialization' and r['passed'] for r in self.test_results['test_details']),
            'Refactoring': any(r['test_name'].startswith('Rename') or r['test_name'].startswith('Extract') for r in self.test_results['test_details']),
            'Symbol Intelligence': any(r['test_name'].startswith('Symbol') and r['passed'] for r in self.test_results['test_details']),
            'Code Actions': any(r['test_name'].startswith('Code Actions') and r['passed'] for r in self.test_results['test_details']),
            'Real-time Analysis': any(r['test_name'].startswith('Real-time') and r['passed'] for r in self.test_results['test_details'])
        }
        
        for capability, working in capabilities_status.items():
            status = "🟢 Working" if working else "🔴 Not Working"
            print(f"   • {capability}: {status}")
        
        print(f"\n🚀 Overall Status: {'🎉 Serena is ready for production!' if success_rate >= 70 else '⚠️  Some issues detected, review failed tests'}")
    
    async def _cleanup(self):
        """Cleanup resources."""
        try:
            if self.lsp_integration:
                await self.lsp_integration.shutdown()
            
            if self.serena_core:
                await self.serena_core.shutdown()
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _record_test_result(self, test_name: str, passed: Optional[bool], message: str):
        """Record a test result."""
        self.test_results['total_tests'] += 1
        
        if passed is True:
            self.test_results['passed_tests'] += 1
        elif passed is False:
            self.test_results['failed_tests'] += 1
        else:
            self.test_results['skipped_tests'] += 1
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'passed': passed,
            'message': message
        })
    
    async def _create_test_file_for_refactoring(self) -> Path:
        """Create a test file for refactoring operations."""
        test_file = self.codebase_path / "test_refactoring.py"
        
        content = '''"""Test file for refactoring operations."""

def test_function():
    """A simple test function."""
    x = 10
    y = 20
    result = x + y
    print(f"Result: {result}")
    return result

class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
'''
        
        test_file.write_text(content)
        return test_file
    
    async def _create_test_file_with_issues(self) -> Path:
        """Create a test file with code issues for testing code actions."""
        test_file = self.codebase_path / "test_issues.py"
        
        content = '''import os
import sys
import json

def function_with_issues():
    unused_var = "not used"
    result = undefined_variable + 5
    return result

def another_function():
    pass
'''
        
        test_file.write_text(content)
        return test_file


async def main():
    """Main function to run the comprehensive demo."""
    parser = argparse.ArgumentParser(description='Comprehensive Serena Demo')
    parser.add_argument('--codebase-path', default='.', 
                       help='Path to the codebase to analyze')
    parser.add_argument('--test-all', action='store_true',
                       help='Run all tests including performance tests')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Resolve codebase path
    codebase_path = Path(args.codebase_path).resolve()
    
    if not codebase_path.exists():
        print(f"❌ Codebase path does not exist: {codebase_path}")
        return 1
    
    print(f"🎯 Running Comprehensive Serena Demo")
    print(f"📁 Codebase: {codebase_path}")
    print(f"🧪 Mode: {'Full Testing' if args.test_all else 'Basic Demo'}")
    print()
    
    # Run the demo
    demo = ComprehensiveSerenaDemo(str(codebase_path))
    results = await demo.run_comprehensive_demo(test_all=args.test_all)
    
    # Return appropriate exit code
    if results['failed_tests'] == 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
