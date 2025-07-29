#!/usr/bin/env python3
"""
Comprehensive Serena Error Analysis Test

This script uses the upgraded Serena MCP integration to perform deep analysis
of the codebase and retrieve all errors, issues, and potential problems.
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, 'src')

from graph_sitter.extensions.serena.core import SerenaCore
from graph_sitter.extensions.serena.mcp_bridge import SerenaMCPBridge
from graph_sitter.extensions.serena.semantic_tools import SemanticTools
from graph_sitter.core.codebase import Codebase


class SerenaErrorAnalyzer:
    """Comprehensive error analysis using Serena MCP integration."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.codebase = None
        self.serena = None
        self.bridge = None
        self.errors = []
        self.issues = []
        self.warnings = []
        
    def initialize(self):
        """Initialize Serena components."""
        print("🚀 Initializing Serena Error Analysis...")
        
        # Build codebase
        print("📊 Building codebase graph...")
        self.codebase = Codebase(str(self.repo_path))
        
        # Initialize SerenaCore
        print("🔧 Initializing SerenaCore...")
        self.serena = SerenaCore(self.codebase)
        self.bridge = self.serena.mcp_bridge
        
        print(f"✅ Serena initialized with {len(self.bridge.available_tools)} tools")
        
    def run_comprehensive_analysis(self):
        """Run comprehensive error and issue analysis."""
        print("\n🔍 Running Comprehensive Analysis...")
        
        # 1. Check project onboarding and configuration
        self._check_project_setup()
        
        # 2. Analyze code quality across the codebase
        self._analyze_code_quality()
        
        # 3. Search for common error patterns
        self._search_error_patterns()
        
        # 4. Analyze symbol issues
        self._analyze_symbol_issues()
        
        # 5. Check for import and dependency issues
        self._check_import_issues()
        
        # 6. Look for potential bugs and code smells
        self._detect_code_smells()
        
        # 7. Check for security issues
        self._check_security_issues()
        
    def _check_project_setup(self):
        """Check project setup and configuration."""
        print("  📋 Checking project setup...")
        
        try:
            # Check if onboarding was performed
            if self.bridge.is_tool_available('check_onboarding_performed'):
                result = self.bridge.call_tool('check_onboarding_performed', {})
                if result.success:
                    print(f"    ✅ Onboarding status: {result.content}")
                else:
                    self.issues.append({
                        'type': 'setup',
                        'severity': 'warning',
                        'message': 'Could not check onboarding status',
                        'details': result.error
                    })
            
            # Get current configuration
            if self.bridge.is_tool_available('get_current_config'):
                result = self.bridge.call_tool('get_current_config', {})
                if result.success:
                    print(f"    ✅ Configuration retrieved")
                else:
                    self.issues.append({
                        'type': 'setup',
                        'severity': 'warning', 
                        'message': 'Could not retrieve configuration',
                        'details': result.error
                    })
                    
        except Exception as e:
            self.errors.append({
                'type': 'setup',
                'severity': 'error',
                'message': f'Project setup check failed: {e}',
                'location': 'project_root'
            })
    
    def _analyze_code_quality(self):
        """Analyze code quality across key files."""
        print("  🎯 Analyzing code quality...")
        
        # Key files to analyze
        key_files = [
            'src/graph_sitter/extensions/serena/core.py',
            'src/graph_sitter/extensions/serena/mcp_bridge.py',
            'src/graph_sitter/extensions/serena/semantic_tools.py',
            'src/graph_sitter/core/codebase.py',
            'pyproject.toml'
        ]
        
        for file_path in key_files:
            if (self.repo_path / file_path).exists():
                try:
                    # Get symbols overview for Python files
                    if file_path.endswith('.py') and self.bridge.is_tool_available('get_symbols_overview'):
                        result = self.bridge.call_tool('get_symbols_overview', {
                            'file_or_directory_path': file_path
                        })
                        
                        if result.success:
                            print(f"    ✅ Analyzed {file_path}")
                            # Look for potential issues in the symbols
                            self._analyze_symbols_for_issues(file_path, result.content)
                        else:
                            self.issues.append({
                                'type': 'analysis',
                                'severity': 'warning',
                                'message': f'Could not analyze symbols in {file_path}',
                                'location': file_path,
                                'details': result.error
                            })
                            
                except Exception as e:
                    self.errors.append({
                        'type': 'analysis',
                        'severity': 'error',
                        'message': f'Code quality analysis failed for {file_path}: {e}',
                        'location': file_path
                    })
    
    def _analyze_symbols_for_issues(self, file_path: str, symbols_data: Any):
        """Analyze symbols data for potential issues."""
        try:
            if isinstance(symbols_data, dict):
                # Look for common issues in symbol definitions
                if 'classes' in symbols_data:
                    for class_info in symbols_data.get('classes', []):
                        if isinstance(class_info, dict):
                            # Check for classes without docstrings
                            if not class_info.get('docstring'):
                                self.warnings.append({
                                    'type': 'documentation',
                                    'severity': 'info',
                                    'message': f'Class {class_info.get("name", "unknown")} lacks docstring',
                                    'location': f'{file_path}:{class_info.get("line", "unknown")}'
                                })
                
                if 'functions' in symbols_data:
                    for func_info in symbols_data.get('functions', []):
                        if isinstance(func_info, dict):
                            # Check for functions without docstrings
                            if not func_info.get('docstring'):
                                self.warnings.append({
                                    'type': 'documentation',
                                    'severity': 'info',
                                    'message': f'Function {func_info.get("name", "unknown")} lacks docstring',
                                    'location': f'{file_path}:{func_info.get("line", "unknown")}'
                                })
                                
        except Exception as e:
            self.warnings.append({
                'type': 'analysis',
                'severity': 'warning',
                'message': f'Symbol analysis failed: {e}',
                'location': file_path
            })
    
    def _search_error_patterns(self):
        """Search for common error patterns in the code."""
        print("  🔍 Searching for error patterns...")
        
        error_patterns = [
            ('TODO', 'Unfinished work'),
            ('FIXME', 'Code that needs fixing'),
            ('XXX', 'Problematic code'),
            ('HACK', 'Temporary workaround'),
            ('BUG', 'Known bug'),
            ('raise NotImplementedError', 'Unimplemented functionality'),
            ('except:', 'Bare except clause'),
            ('except Exception:', 'Overly broad exception handling'),
            ('print(', 'Debug print statements'),
            ('import pdb', 'Debug imports'),
            ('breakpoint()', 'Debug breakpoints')
        ]
        
        for pattern, description in error_patterns:
            try:
                if self.bridge.is_tool_available('search_for_pattern'):
                    result = self.bridge.call_tool('search_for_pattern', {
                        'pattern': pattern,
                        'max_results': 20
                    })
                    
                    if result.success and result.content:
                        matches = result.content if isinstance(result.content, list) else [result.content]
                        for match in matches:
                            if isinstance(match, dict):
                                self.issues.append({
                                    'type': 'pattern',
                                    'severity': 'info' if pattern in ['TODO', 'print('] else 'warning',
                                    'message': f'{description}: {pattern}',
                                    'location': f"{match.get('file', 'unknown')}:{match.get('line', 'unknown')}",
                                    'context': match.get('content', '')[:100]
                                })
                                
            except Exception as e:
                self.errors.append({
                    'type': 'pattern_search',
                    'severity': 'error',
                    'message': f'Pattern search failed for "{pattern}": {e}',
                    'location': 'global'
                })
    
    def _analyze_symbol_issues(self):
        """Analyze symbol-related issues."""
        print("  🔤 Analyzing symbol issues...")
        
        # Look for common problematic symbols
        problematic_symbols = [
            'SerenaCore',  # Our main class
            'SerenaMCPBridge',  # Bridge class
            'SemanticTools',  # Tools class
        ]
        
        for symbol_name in problematic_symbols:
            try:
                if self.bridge.is_tool_available('find_symbol'):
                    result = self.bridge.call_tool('find_symbol', {
                        'name_path': symbol_name
                    })
                    
                    if result.success:
                        print(f"    ✅ Found symbol: {symbol_name}")
                        # Check for symbol references
                        if self.bridge.is_tool_available('find_referencing_symbols'):
                            ref_result = self.bridge.call_tool('find_referencing_symbols', {
                                'name_path': symbol_name
                            })
                            if ref_result.success:
                                print(f"    ✅ Found references for: {symbol_name}")
                    else:
                        self.issues.append({
                            'type': 'symbol',
                            'severity': 'warning',
                            'message': f'Could not find symbol: {symbol_name}',
                            'location': 'global',
                            'details': result.error
                        })
                        
            except Exception as e:
                self.errors.append({
                    'type': 'symbol_analysis',
                    'severity': 'error',
                    'message': f'Symbol analysis failed for {symbol_name}: {e}',
                    'location': 'global'
                })
    
    def _check_import_issues(self):
        """Check for import and dependency issues."""
        print("  📦 Checking import issues...")
        
        # Search for problematic import patterns
        import_patterns = [
            ('from .* import \\*', 'Wildcard imports'),
            ('import sys', 'System imports'),
            ('from typing import', 'Typing imports'),
        ]
        
        for pattern, description in import_patterns:
            try:
                if self.bridge.is_tool_available('search_for_pattern'):
                    result = self.bridge.call_tool('search_for_pattern', {
                        'pattern': pattern,
                        'max_results': 10
                    })
                    
                    if result.success and result.content:
                        matches = result.content if isinstance(result.content, list) else [result.content]
                        print(f"    ✅ Found {len(matches)} {description.lower()}")
                        
            except Exception as e:
                self.warnings.append({
                    'type': 'import_check',
                    'severity': 'warning',
                    'message': f'Import pattern check failed for "{pattern}": {e}',
                    'location': 'global'
                })
    
    def _detect_code_smells(self):
        """Detect common code smells."""
        print("  👃 Detecting code smells...")
        
        code_smell_patterns = [
            ('def.*\\(.*,.*,.*,.*,.*,.*,.*\\)', 'Functions with too many parameters'),
            ('class.*\\(.*,.*,.*\\)', 'Classes with multiple inheritance'),
            ('if.*and.*and.*and', 'Complex conditional statements'),
            ('lambda.*:', 'Lambda expressions'),
        ]
        
        for pattern, description in code_smell_patterns:
            try:
                if self.bridge.is_tool_available('search_for_pattern'):
                    result = self.bridge.call_tool('search_for_pattern', {
                        'pattern': pattern,
                        'max_results': 5
                    })
                    
                    if result.success and result.content:
                        matches = result.content if isinstance(result.content, list) else [result.content]
                        for match in matches:
                            if isinstance(match, dict):
                                self.warnings.append({
                                    'type': 'code_smell',
                                    'severity': 'info',
                                    'message': description,
                                    'location': f"{match.get('file', 'unknown')}:{match.get('line', 'unknown')}",
                                    'context': match.get('content', '')[:100]
                                })
                                
            except Exception as e:
                self.warnings.append({
                    'type': 'code_smell_detection',
                    'severity': 'warning',
                    'message': f'Code smell detection failed for "{pattern}": {e}',
                    'location': 'global'
                })
    
    def _check_security_issues(self):
        """Check for potential security issues."""
        print("  🔒 Checking security issues...")
        
        security_patterns = [
            ('eval\\(', 'Use of eval() function'),
            ('exec\\(', 'Use of exec() function'),
            ('subprocess\\.call', 'Subprocess calls'),
            ('os\\.system', 'OS system calls'),
            ('pickle\\.loads', 'Pickle deserialization'),
            ('yaml\\.load\\(', 'Unsafe YAML loading'),
        ]
        
        for pattern, description in security_patterns:
            try:
                if self.bridge.is_tool_available('search_for_pattern'):
                    result = self.bridge.call_tool('search_for_pattern', {
                        'pattern': pattern,
                        'max_results': 10
                    })
                    
                    if result.success and result.content:
                        matches = result.content if isinstance(result.content, list) else [result.content]
                        for match in matches:
                            if isinstance(match, dict):
                                self.issues.append({
                                    'type': 'security',
                                    'severity': 'warning',
                                    'message': f'Potential security issue: {description}',
                                    'location': f"{match.get('file', 'unknown')}:{match.get('line', 'unknown')}",
                                    'context': match.get('content', '')[:100]
                                })
                                
            except Exception as e:
                self.warnings.append({
                    'type': 'security_check',
                    'severity': 'warning',
                    'message': f'Security check failed for "{pattern}": {e}',
                    'location': 'global'
                })
    
    def generate_report(self):
        """Generate comprehensive error and issue report."""
        print("\n📊 Generating Analysis Report...")
        
        total_issues = len(self.errors) + len(self.issues) + len(self.warnings)
        
        print(f"\n{'='*60}")
        print(f"🔍 SERENA ERROR ANALYSIS REPORT")
        print(f"{'='*60}")
        print(f"📊 Total Issues Found: {total_issues}")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️  Issues: {len(self.issues)}")
        print(f"💡 Warnings: {len(self.warnings)}")
        print(f"{'='*60}")
        
        # Report errors
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            print("-" * 40)
            for i, error in enumerate(self.errors, 1):
                print(f"{i:2d}. [{error['type'].upper()}] {error['message']}")
                print(f"    📍 Location: {error['location']}")
                if 'details' in error:
                    print(f"    📝 Details: {error['details']}")
                print()
        
        # Report issues
        if self.issues:
            print(f"\n⚠️  ISSUES ({len(self.issues)}):")
            print("-" * 40)
            for i, issue in enumerate(self.issues, 1):
                print(f"{i:2d}. [{issue['type'].upper()}] {issue['message']}")
                print(f"    📍 Location: {issue['location']}")
                if 'context' in issue:
                    print(f"    📝 Context: {issue['context']}")
                print()
        
        # Report warnings
        if self.warnings:
            print(f"\n💡 WARNINGS ({len(self.warnings)}):")
            print("-" * 40)
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i:2d}. [{warning['type'].upper()}] {warning['message']}")
                print(f"    📍 Location: {warning['location']}")
                if 'context' in warning:
                    print(f"    📝 Context: {warning['context']}")
                print()
        
        # Summary by type
        print(f"\n📈 ISSUE BREAKDOWN BY TYPE:")
        print("-" * 40)
        all_items = self.errors + self.issues + self.warnings
        type_counts = {}
        for item in all_items:
            item_type = item['type']
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        for issue_type, count in sorted(type_counts.items()):
            print(f"  {issue_type:<20}: {count:>3}")
        
        return {
            'total_issues': total_issues,
            'errors': self.errors,
            'issues': self.issues,
            'warnings': self.warnings,
            'type_breakdown': type_counts
        }
    
    def shutdown(self):
        """Clean shutdown."""
        if self.serena:
            self.serena.shutdown()
        print("✅ Analysis complete and resources cleaned up")


def main():
    """Run comprehensive Serena error analysis."""
    print("🔍 Starting Comprehensive Serena Error Analysis")
    print("=" * 60)
    
    analyzer = SerenaErrorAnalyzer(os.getcwd())
    
    try:
        # Initialize
        analyzer.initialize()
        
        # Run analysis
        analyzer.run_comprehensive_analysis()
        
        # Generate report
        report = analyzer.generate_report()
        
        # Save report to file
        with open('serena_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Detailed report saved to: serena_analysis_report.json")
        
        return 0 if report['total_issues'] == 0 else 1
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        analyzer.shutdown()


if __name__ == "__main__":
    sys.exit(main())

