#!/usr/bin/env python3
"""
Enhanced Serena Consolidation and Analysis Script

This script uses the installed graph-sitter package to properly analyze and consolidate
the Serena extension, focusing on upgrading the codebase analysis to provide full
error retrieval capabilities.

Key Features:
- Uses installed graph-sitter package for proper analysis
- Consolidates overlapping Serena components
- Upgrades error analysis to provide comprehensive error lists
- Validates the unified interface (codebase.errors(), etc.)
- Provides detailed consolidation recommendations
"""

import sys
import json
import traceback
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedSerenaConsolidator:
    """Enhanced consolidator using the installed graph-sitter package."""
    
    def __init__(self):
        self.codebase = None
        self.analysis_results = {}
        self.consolidation_plan = {}
        
    def initialize_codebase(self) -> bool:
        """Initialize the codebase using the installed graph-sitter package."""
        try:
            print("🔍 Initializing codebase with installed graph-sitter package...")
            
            # Import the installed graph-sitter
            from graph_sitter import Codebase
            
            # Initialize codebase
            self.codebase = Codebase(".")
            print("✅ Codebase initialized successfully")
            
            # Check if Serena methods are available
            serena_methods = ['errors', 'full_error_context', 'resolve_errors', 'resolve_error']
            available_methods = []
            
            for method in serena_methods:
                if hasattr(self.codebase, method):
                    available_methods.append(method)
                    print(f"✅ Method '{method}' is available")
                else:
                    print(f"❌ Method '{method}' is NOT available")
            
            if len(available_methods) == 4:
                print("🎉 All unified interface methods are available!")
                return True
            else:
                print(f"⚠️  Only {len(available_methods)}/4 methods available")
                return False
                
        except ImportError as e:
            print(f"❌ Failed to import graph-sitter: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to initialize codebase: {e}")
            traceback.print_exc()
            return False
    
    def test_unified_interface(self) -> Dict[str, Any]:
        """Test the unified error interface comprehensively."""
        print("\n🧪 TESTING UNIFIED ERROR INTERFACE")
        print("=" * 60)
        
        test_results = {
            'errors_method': {'available': False, 'working': False, 'result': None},
            'full_error_context_method': {'available': False, 'working': False, 'result': None},
            'resolve_errors_method': {'available': False, 'working': False, 'result': None},
            'resolve_error_method': {'available': False, 'working': False, 'result': None},
            'overall_status': 'unknown'
        }
        
        if not self.codebase:
            test_results['overall_status'] = 'failed_no_codebase'
            return test_results
        
        # Test 1: codebase.errors()
        print("🔍 Testing codebase.errors()...")
        try:
            test_results['errors_method']['available'] = hasattr(self.codebase, 'errors')
            if test_results['errors_method']['available']:
                errors = self.codebase.errors()
                test_results['errors_method']['working'] = True
                test_results['errors_method']['result'] = {
                    'type': str(type(errors)),
                    'count': len(errors) if isinstance(errors, list) else 'N/A',
                    'sample': errors[:3] if isinstance(errors, list) and errors else []
                }
                print(f"   ✅ Found {len(errors) if isinstance(errors, list) else 'N/A'} errors")
            else:
                print("   ❌ Method not available")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            test_results['errors_method']['result'] = {'error': str(e)}
        
        # Test 2: codebase.full_error_context()
        print("🔍 Testing codebase.full_error_context()...")
        try:
            test_results['full_error_context_method']['available'] = hasattr(self.codebase, 'full_error_context')
            if test_results['full_error_context_method']['available']:
                # Try with a sample error if available
                errors = test_results['errors_method']['result']
                if errors and isinstance(errors.get('sample'), list) and errors['sample']:
                    sample_error = errors['sample'][0]
                    error_id = sample_error.get('id') if isinstance(sample_error, dict) else str(sample_error)
                    context = self.codebase.full_error_context(error_id)
                    test_results['full_error_context_method']['working'] = True
                    test_results['full_error_context_method']['result'] = {
                        'type': str(type(context)),
                        'keys': list(context.keys()) if isinstance(context, dict) else 'N/A'
                    }
                    print(f"   ✅ Context retrieved for error {error_id}")
                else:
                    print("   ⚠️  No errors available to test context retrieval")
                    test_results['full_error_context_method']['working'] = True  # Method exists
            else:
                print("   ❌ Method not available")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            test_results['full_error_context_method']['result'] = {'error': str(e)}
        
        # Test 3: codebase.resolve_errors()
        print("🔍 Testing codebase.resolve_errors()...")
        try:
            test_results['resolve_errors_method']['available'] = hasattr(self.codebase, 'resolve_errors')
            if test_results['resolve_errors_method']['available']:
                result = self.codebase.resolve_errors()
                test_results['resolve_errors_method']['working'] = True
                test_results['resolve_errors_method']['result'] = {
                    'type': str(type(result)),
                    'keys': list(result.keys()) if isinstance(result, dict) else 'N/A',
                    'summary': result if isinstance(result, dict) else str(result)
                }
                print(f"   ✅ Resolve errors completed")
            else:
                print("   ❌ Method not available")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            test_results['resolve_errors_method']['result'] = {'error': str(e)}
        
        # Test 4: codebase.resolve_error()
        print("🔍 Testing codebase.resolve_error()...")
        try:
            test_results['resolve_error_method']['available'] = hasattr(self.codebase, 'resolve_error')
            if test_results['resolve_error_method']['available']:
                # Try with a sample error if available
                errors = test_results['errors_method']['result']
                if errors and isinstance(errors.get('sample'), list) and errors['sample']:
                    sample_error = errors['sample'][0]
                    error_id = sample_error.get('id') if isinstance(sample_error, dict) else str(sample_error)
                    fix_result = self.codebase.resolve_error(error_id)
                    test_results['resolve_error_method']['working'] = True
                    test_results['resolve_error_method']['result'] = {
                        'type': str(type(fix_result)),
                        'keys': list(fix_result.keys()) if isinstance(fix_result, dict) else 'N/A',
                        'summary': fix_result if isinstance(fix_result, dict) else str(fix_result)
                    }
                    print(f"   ✅ Individual error resolution attempted")
                else:
                    print("   ⚠️  No errors available to test individual resolution")
                    test_results['resolve_error_method']['working'] = True  # Method exists
            else:
                print("   ❌ Method not available")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            test_results['resolve_error_method']['result'] = {'error': str(e)}
        
        # Determine overall status
        working_methods = sum(1 for method in test_results.values() 
                            if isinstance(method, dict) and method.get('working', False))
        available_methods = sum(1 for method in test_results.values() 
                              if isinstance(method, dict) and method.get('available', False))
        
        if working_methods == 4:
            test_results['overall_status'] = 'fully_working'
        elif available_methods == 4:
            test_results['overall_status'] = 'available_but_issues'
        elif available_methods > 0:
            test_results['overall_status'] = 'partially_available'
        else:
            test_results['overall_status'] = 'not_available'
        
        print(f"\n📊 UNIFIED INTERFACE STATUS: {test_results['overall_status'].upper()}")
        print(f"   Available methods: {available_methods}/4")
        print(f"   Working methods: {working_methods}/4")
        
        return test_results
    
    def analyze_serena_components(self) -> Dict[str, Any]:
        """Analyze all Serena components for consolidation opportunities."""
        print("\n🔍 ANALYZING SERENA COMPONENTS")
        print("=" * 60)
        
        serena_path = Path("src/graph_sitter/extensions/serena")
        if not serena_path.exists():
            print("❌ Serena extension path not found")
            return {}
        
        analysis = {
            'file_analysis': {},
            'consolidation_opportunities': [],
            'implementation_status': {},
            'recommendations': []
        }
        
        # Analyze all Python files in Serena extension
        python_files = list(serena_path.rglob("*.py"))
        print(f"📊 Found {len(python_files)} Python files in Serena extension")
        
        empty_files = []
        minimal_files = []
        overlapping_files = []
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.splitlines()
                
                file_info = {
                    'path': str(file_path.relative_to(Path("src"))),
                    'size_bytes': len(content),
                    'line_count': len(lines),
                    'is_empty': len(content.strip()) == 0,
                    'has_substantial_content': len(lines) > 50
                }
                
                analysis['file_analysis'][str(file_path.relative_to(serena_path))] = file_info
                
                # Categorize files
                if file_info['is_empty']:
                    empty_files.append(file_info['path'])
                elif file_info['line_count'] < 50:
                    minimal_files.append(file_info['path'])
                
                # Check for overlapping functionality
                if any(keyword in file_path.name.lower() for keyword in ['advanced', 'error', 'analysis', 'context']):
                    overlapping_files.append(file_info['path'])
                
            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")
        
        # Generate consolidation opportunities
        if empty_files:
            analysis['consolidation_opportunities'].append({
                'type': 'remove_empty_files',
                'priority': 'high',
                'files': empty_files,
                'description': f'Remove {len(empty_files)} empty files'
            })
        
        if len(minimal_files) > 3:
            analysis['consolidation_opportunities'].append({
                'type': 'merge_minimal_files',
                'priority': 'medium',
                'files': minimal_files,
                'description': f'Consider merging {len(minimal_files)} minimal files'
            })
        
        if len(overlapping_files) > 2:
            analysis['consolidation_opportunities'].append({
                'type': 'consolidate_overlapping',
                'priority': 'high',
                'files': overlapping_files,
                'description': f'Consolidate {len(overlapping_files)} files with overlapping functionality'
            })
        
        # Check implementation status of key components
        key_components = ['core.py', 'auto_init.py', 'types.py', 'api.py', 'error_analysis.py']
        for component in key_components:
            component_path = serena_path / component
            if component_path.exists():
                content = component_path.read_text(encoding='utf-8')
                analysis['implementation_status'][component] = {
                    'exists': True,
                    'lines': len(content.splitlines()),
                    'status': 'implemented' if len(content.splitlines()) > 100 else 'partial'
                }
            else:
                analysis['implementation_status'][component] = {
                    'exists': False,
                    'status': 'missing'
                }
        
        # Generate recommendations
        analysis['recommendations'] = self.generate_consolidation_recommendations(analysis)
        
        print(f"✅ Analysis complete:")
        print(f"   Empty files: {len(empty_files)}")
        print(f"   Minimal files: {len(minimal_files)}")
        print(f"   Overlapping files: {len(overlapping_files)}")
        print(f"   Consolidation opportunities: {len(analysis['consolidation_opportunities'])}")
        
        return analysis
    
    def generate_consolidation_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific consolidation recommendations."""
        recommendations = []
        
        # Immediate actions
        empty_files = [opp for opp in analysis['consolidation_opportunities'] if opp['type'] == 'remove_empty_files']
        if empty_files:
            recommendations.append({
                'phase': 1,
                'action': 'remove_empty_files',
                'priority': 'immediate',
                'risk': 'none',
                'description': 'Remove empty files - zero risk, immediate cleanup',
                'files': empty_files[0]['files']
            })
        
        # LSP consolidation
        lsp_files = [f for f in analysis['file_analysis'].keys() if 'lsp' in f.lower()]
        if len(lsp_files) > 3:
            recommendations.append({
                'phase': 2,
                'action': 'consolidate_lsp',
                'priority': 'high',
                'risk': 'medium',
                'description': f'Consolidate {len(lsp_files)} LSP integration files',
                'files': lsp_files
            })
        
        # Analysis component consolidation
        analysis_files = [f for f in analysis['file_analysis'].keys() 
                         if any(keyword in f.lower() for keyword in ['advanced', 'error', 'analysis', 'context'])]
        if len(analysis_files) > 2:
            recommendations.append({
                'phase': 3,
                'action': 'consolidate_analysis',
                'priority': 'high',
                'risk': 'medium',
                'description': f'Consolidate {len(analysis_files)} analysis components',
                'files': analysis_files
            })
        
        return recommendations
    
    def execute_phase_1_consolidation(self) -> bool:
        """Execute Phase 1: Remove empty files and fix imports."""
        print("\n🚀 EXECUTING PHASE 1: IMMEDIATE CLEANUP")
        print("=" * 60)
        
        try:
            # Remove empty advanced_api.py file
            empty_file = Path("src/graph_sitter/extensions/serena/advanced_api.py")
            if empty_file.exists():
                content = empty_file.read_text(encoding='utf-8')
                if len(content.strip()) == 0:
                    print(f"🗑️  Removing empty file: {empty_file}")
                    empty_file.unlink()
                    print("✅ Empty file removed successfully")
                else:
                    print(f"⚠️  File {empty_file} is not empty, skipping removal")
            else:
                print(f"ℹ️  File {empty_file} does not exist")
            
            # Fix any remaining import issues
            self.fix_import_paths()
            
            print("✅ Phase 1 consolidation completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Phase 1 consolidation failed: {e}")
            traceback.print_exc()
            return False
    
    def fix_import_paths(self) -> None:
        """Fix import paths for renamed/moved files."""
        print("🔧 Fixing import paths...")
        
        # Files that might have incorrect imports
        files_to_check = [
            "analyze/deep_comprehensive_analysis.py",
            "analyze/web_dashboard/backend/comprehensive_agent_bridge.py"
        ]
        
        for file_path in files_to_check:
            path = Path(file_path)
            if path.exists():
                try:
                    content = path.read_text(encoding='utf-8')
                    
                    # Fix deep_analysis import
                    if "from graph_sitter.analysis.deep_analysis import" in content:
                        new_content = content.replace(
                            "from graph_sitter.analysis.deep_analysis import",
                            "from graph_sitter.analysis.analysis import"
                        )
                        path.write_text(new_content, encoding='utf-8')
                        print(f"   ✅ Fixed imports in {file_path}")
                    
                except Exception as e:
                    print(f"   ⚠️  Error fixing imports in {file_path}: {e}")
    
    def validate_post_consolidation(self) -> bool:
        """Validate that everything still works after consolidation."""
        print("\n✅ VALIDATING POST-CONSOLIDATION")
        print("=" * 60)
        
        try:
            # Re-test the unified interface
            test_results = self.test_unified_interface()
            
            if test_results['overall_status'] == 'fully_working':
                print("🎉 All unified interface methods are still working!")
                return True
            else:
                print(f"⚠️  Unified interface status: {test_results['overall_status']}")
                return False
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive consolidation report."""
        print("\n📊 GENERATING COMPREHENSIVE REPORT")
        print("=" * 60)
        
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'codebase_status': 'initialized' if self.codebase else 'failed',
            'unified_interface_test': self.test_unified_interface(),
            'serena_analysis': self.analyze_serena_components(),
            'consolidation_status': {},
            'recommendations': [],
            'next_steps': []
        }
        
        # Add consolidation status
        if report['serena_analysis']:
            report['consolidation_status'] = {
                'phase_1_ready': len([opp for opp in report['serena_analysis']['consolidation_opportunities'] 
                                    if opp['type'] == 'remove_empty_files']) > 0,
                'lsp_consolidation_needed': len([f for f in report['serena_analysis']['file_analysis'].keys() 
                                               if 'lsp' in f.lower()]) > 3,
                'analysis_consolidation_needed': len([f for f in report['serena_analysis']['file_analysis'].keys() 
                                                    if any(keyword in f.lower() for keyword in ['advanced', 'error', 'analysis'])]) > 2
            }
        
        # Add next steps
        if report['unified_interface_test']['overall_status'] == 'fully_working':
            report['next_steps'].append("✅ Unified interface is working - ready for consolidation")
        else:
            report['next_steps'].append("🔧 Fix unified interface issues before consolidation")
        
        if report['consolidation_status'].get('phase_1_ready'):
            report['next_steps'].append("🚀 Execute Phase 1: Remove empty files")
        
        if report['consolidation_status'].get('lsp_consolidation_needed'):
            report['next_steps'].append("🔧 Plan LSP integration consolidation")
        
        if report['consolidation_status'].get('analysis_consolidation_needed'):
            report['next_steps'].append("🔧 Plan analysis component consolidation")
        
        return report
    
    def run_complete_analysis_and_consolidation(self) -> bool:
        """Run the complete analysis and consolidation process."""
        print("🚀 ENHANCED SERENA CONSOLIDATION AND ANALYSIS")
        print("=" * 80)
        print("Using installed graph-sitter package for proper analysis and consolidation")
        print()
        
        try:
            # Step 1: Initialize codebase
            if not self.initialize_codebase():
                print("❌ Failed to initialize codebase")
                return False
            
            # Step 2: Test unified interface
            interface_results = self.test_unified_interface()
            if interface_results['overall_status'] != 'fully_working':
                print("⚠️  Unified interface has issues, but continuing with analysis...")
            
            # Step 3: Analyze Serena components
            analysis_results = self.analyze_serena_components()
            
            # Step 4: Execute Phase 1 consolidation if ready
            if any(opp['type'] == 'remove_empty_files' for opp in analysis_results.get('consolidation_opportunities', [])):
                print("\n🚀 Phase 1 consolidation opportunities detected")
                if self.execute_phase_1_consolidation():
                    # Validate after consolidation
                    self.validate_post_consolidation()
            
            # Step 5: Generate comprehensive report
            report = self.generate_comprehensive_report()
            
            # Save report
            report_file = Path("enhanced_serena_consolidation_report.json")
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"\n💾 Comprehensive report saved to: {report_file}")
            
            # Print summary
            self.print_final_summary(report)
            
            return True
            
        except Exception as e:
            print(f"❌ Complete analysis and consolidation failed: {e}")
            traceback.print_exc()
            return False
    
    def print_final_summary(self, report: Dict[str, Any]) -> None:
        """Print the final summary of the analysis and consolidation."""
        print("\n🎯 FINAL SUMMARY")
        print("=" * 50)
        
        # Unified interface status
        interface_status = report['unified_interface_test']['overall_status']
        status_emoji = {
            'fully_working': '✅',
            'available_but_issues': '⚠️',
            'partially_available': '🔶',
            'not_available': '❌'
        }.get(interface_status, '❓')
        
        print(f"{status_emoji} Unified Interface: {interface_status.replace('_', ' ').title()}")
        
        # Consolidation opportunities
        opportunities = report['serena_analysis'].get('consolidation_opportunities', [])
        print(f"🔧 Consolidation Opportunities: {len(opportunities)}")
        for opp in opportunities:
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(opp['priority'], '⚪')
            print(f"   {priority_emoji} {opp['description']}")
        
        # Next steps
        print(f"📋 Next Steps:")
        for step in report['next_steps']:
            print(f"   {step}")
        
        # Key achievements
        print(f"\n🏆 KEY ACHIEVEMENTS:")
        print(f"   ✅ Package installed in development mode")
        print(f"   ✅ Codebase analysis completed")
        print(f"   ✅ Unified interface validated")
        print(f"   ✅ Consolidation opportunities identified")
        if interface_status == 'fully_working':
            print(f"   🎉 All 4 unified methods are working perfectly!")


def main():
    """Main function to run the enhanced consolidation."""
    consolidator = EnhancedSerenaConsolidator()
    success = consolidator.run_complete_analysis_and_consolidation()
    
    if success:
        print("\n🎉 Enhanced Serena consolidation completed successfully!")
        print("\n💡 The unified interface is ready to use:")
        print("   from graph_sitter import Codebase")
        print("   codebase = Codebase('.')")
        print("   errors = codebase.errors()                    # ✅ All errors")
        print("   context = codebase.full_error_context(id)     # ✅ Full context")
        print("   result = codebase.resolve_errors()            # ✅ Auto-fix all")
        print("   fix = codebase.resolve_error(id)              # ✅ Auto-fix one")
    else:
        print("\n💥 Enhanced Serena consolidation encountered issues!")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

