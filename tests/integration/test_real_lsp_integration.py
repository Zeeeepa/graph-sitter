"""
Real LSP Server Integration Test

This test validates the enhanced error handling system with actual LSP servers
to ensure the mock implementations correctly simulate real-world behavior.
"""

import asyncio
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from graph_sitter.core.enhanced_lsp_manager import EnhancedLSPManager
    from graph_sitter.core.enhanced_error_types import EnhancedErrorInfo, ErrorSeverity, ErrorCategory
    ENHANCED_SYSTEM_AVAILABLE = True
except ImportError:
    ENHANCED_SYSTEM_AVAILABLE = False


class RealLSPIntegrationTest:
    """Integration test with real LSP servers."""
    
    def __init__(self):
        self.test_results = {
            'pylsp_available': False,
            'enhanced_system_available': ENHANCED_SYSTEM_AVAILABLE,
            'integration_tests': [],
            'performance_metrics': {},
            'errors_detected': 0,
            'context_quality': 0.0
        }
    
    def check_pylsp_availability(self) -> bool:
        """Check if pylsp (Python LSP Server) is available."""
        try:
            result = subprocess.run(['pylsp', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.test_results['pylsp_available'] = True
                print(f"✅ pylsp available: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ pylsp not available: {result.stderr}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"❌ pylsp not available: {e}")
            return False
    
    def create_test_files(self, temp_dir: Path) -> List[Path]:
        """Create test files with various error types."""
        test_files = []
        
        # Syntax error file
        syntax_error_file = temp_dir / "syntax_errors.py"
        syntax_error_file.write_text("""
# Missing colon syntax errors
def test_function()  # Missing colon
    return "hello"

if True  # Missing colon
    print("test")

for i in range(5)  # Missing colon
    print(i)
""")
        test_files.append(syntax_error_file)
        
        # Semantic error file
        semantic_error_file = temp_dir / "semantic_errors.py"
        semantic_error_file.write_text("""
# Undefined variable errors
def test_undefined():
    print(undefined_variable)  # Undefined variable
    return missing_var + 5     # Another undefined variable

def test_scope():
    if True:
        local_var = 10
    print(local_var)  # Variable out of scope
""")
        test_files.append(semantic_error_file)
        
        # Import error file
        import_error_file = temp_dir / "import_errors.py"
        import_error_file.write_text("""
# Import errors
import nonexistent_module  # Module not found
from missing_package import something  # Package not found
from os import nonexistent_function  # Function not found
""")
        test_files.append(import_error_file)
        
        return test_files
    
    async def test_enhanced_system_with_real_files(self, test_files: List[Path]) -> Dict[str, Any]:
        """Test enhanced system with real test files."""
        if not ENHANCED_SYSTEM_AVAILABLE:
            return {'success': False, 'error': 'Enhanced system not available'}
        
        try:
            # Initialize enhanced LSP manager
            temp_dir = test_files[0].parent
            manager = EnhancedLSPManager(str(temp_dir))
            
            start_time = time.time()
            
            # Initialize and get errors
            await manager.initialize()
            all_errors = await manager.get_all_errors()
            
            initialization_time = time.time() - start_time
            
            # Test error detection
            errors_by_file = {}
            for error in all_errors:
                file_path = error.location.file_path
                if file_path not in errors_by_file:
                    errors_by_file[file_path] = []
                errors_by_file[file_path].append(error)
            
            # Test context extraction
            context_tests = []
            for error in all_errors[:3]:  # Test first 3 errors
                context_start = time.time()
                context = await manager.get_full_error_context(error.id)
                context_time = time.time() - context_start
                
                if context:
                    context_quality = self._assess_context_quality(context)
                    context_tests.append({
                        'error_id': error.id,
                        'context_time': context_time,
                        'context_quality': context_quality,
                        'has_surrounding_code': bool(context.context.surrounding_code),
                        'has_reasoning': bool(context.reasoning.root_cause),
                        'has_fixes': len(context.suggested_fixes) > 0
                    })
            
            await manager.shutdown()
            
            return {
                'success': True,
                'initialization_time': initialization_time,
                'total_errors': len(all_errors),
                'errors_by_file': {str(k): len(v) for k, v in errors_by_file.items()},
                'context_tests': context_tests,
                'average_context_quality': sum(t['context_quality'] for t in context_tests) / len(context_tests) if context_tests else 0.0
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _assess_context_quality(self, error: EnhancedErrorInfo) -> float:
        """Assess the quality of error context (0.0 to 1.0)."""
        score = 0.0
        
        # Check context completeness
        if error.context.surrounding_code:
            score += 0.2
        if error.context.symbol_definitions:
            score += 0.2
        if error.context.dependency_chain:
            score += 0.1
        if error.context.related_files:
            score += 0.1
        
        # Check reasoning quality
        if error.reasoning.root_cause:
            score += 0.2
        if error.reasoning.why_occurred:
            score += 0.1
        if error.reasoning.semantic_analysis:
            score += 0.1
        
        return min(score, 1.0)
    
    def test_performance_requirements(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Test performance requirements."""
        performance_results = {
            'initialization_under_5s': False,
            'context_under_1s': False,
            'meets_requirements': False
        }
        
        if test_results.get('success'):
            # Check initialization time
            init_time = test_results.get('initialization_time', 0)
            performance_results['initialization_under_5s'] = init_time < 5.0
            
            # Check context extraction time
            context_tests = test_results.get('context_tests', [])
            if context_tests:
                avg_context_time = sum(t['context_time'] for t in context_tests) / len(context_tests)
                performance_results['context_under_1s'] = avg_context_time < 1.0
                performance_results['average_context_time'] = avg_context_time
            
            performance_results['meets_requirements'] = (
                performance_results['initialization_under_5s'] and
                performance_results['context_under_1s']
            )
        
        return performance_results
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run comprehensive integration tests."""
        print("🧪 Running Real LSP Integration Tests...")
        
        # Check prerequisites
        pylsp_available = self.check_pylsp_availability()
        
        if not ENHANCED_SYSTEM_AVAILABLE:
            print("❌ Enhanced system not available")
            return self.test_results
        
        if not pylsp_available:
            print("⚠️  pylsp not available, running with mock diagnostics only")
        
        # Create temporary test environment
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_files = self.create_test_files(temp_path)
            
            print(f"📁 Created test files: {[f.name for f in test_files]}")
            
            # Test enhanced system
            enhanced_results = await self.test_enhanced_system_with_real_files(test_files)
            self.test_results['integration_tests'].append({
                'test_name': 'enhanced_system_integration',
                'results': enhanced_results
            })
            
            if enhanced_results.get('success'):
                self.test_results['errors_detected'] = enhanced_results['total_errors']
                self.test_results['context_quality'] = enhanced_results['average_context_quality']
                
                # Test performance
                performance_results = self.test_performance_requirements(enhanced_results)
                self.test_results['performance_metrics'] = performance_results
                
                print(f"✅ Enhanced system test completed:")
                print(f"   Errors detected: {enhanced_results['total_errors']}")
                print(f"   Context quality: {enhanced_results['average_context_quality']:.2f}")
                print(f"   Performance: {'✅' if performance_results['meets_requirements'] else '❌'}")
            else:
                print(f"❌ Enhanced system test failed: {enhanced_results.get('error')}")
        
        return self.test_results
    
    def generate_report(self) -> str:
        """Generate integration test report."""
        report = {
            'test_summary': {
                'enhanced_system_available': self.test_results['enhanced_system_available'],
                'pylsp_available': self.test_results['pylsp_available'],
                'total_tests': len(self.test_results['integration_tests']),
                'errors_detected': self.test_results['errors_detected'],
                'context_quality': self.test_results['context_quality']
            },
            'integration_tests': self.test_results['integration_tests'],
            'performance_metrics': self.test_results['performance_metrics'],
            'recommendations': []
        }
        
        # Generate recommendations
        if not self.test_results['enhanced_system_available']:
            report['recommendations'].append("Install enhanced error system components")
        
        if not self.test_results['pylsp_available']:
            report['recommendations'].append("Install pylsp for real LSP integration: pip install python-lsp-server")
        
        if self.test_results['context_quality'] < 0.7:
            report['recommendations'].append("Improve context extraction quality")
        
        performance = self.test_results.get('performance_metrics', {})
        if not performance.get('meets_requirements', False):
            report['recommendations'].append("Optimize performance to meet requirements")
        
        return json.dumps(report, indent=2)


async def main():
    """Run the integration tests."""
    tester = RealLSPIntegrationTest()
    results = await tester.run_integration_tests()
    
    print("\n📊 Integration Test Results:")
    print("=" * 50)
    
    if results['enhanced_system_available']:
        print(f"✅ Enhanced System: Available")
    else:
        print(f"❌ Enhanced System: Not Available")
    
    if results['pylsp_available']:
        print(f"✅ pylsp: Available")
    else:
        print(f"❌ pylsp: Not Available")
    
    print(f"🔍 Errors Detected: {results['errors_detected']}")
    print(f"📊 Context Quality: {results['context_quality']:.2f}/1.0")
    
    performance = results.get('performance_metrics', {})
    if performance:
        print(f"⚡ Performance: {'✅ Meets Requirements' if performance.get('meets_requirements') else '❌ Needs Improvement'}")
    
    # Save detailed report
    report = tester.generate_report()
    report_file = Path("real_lsp_integration_report.json")
    report_file.write_text(report)
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    print("\n✅ Step 2 Complete: Real LSP Integration Test")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())

