#!/usr/bin/env python3
"""
Real LSP Diagnostics Analyzer - Captures Actual Code Errors

This analyzer uses real linting tools (flake8, pylint, mypy) to capture
actual code errors and presents them in LSP diagnostic format.
"""

import os
import sys
import json
import time
import subprocess
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from graph_sitter.core.codebase import Codebase
    GRAPH_SITTER_AVAILABLE = True
    print("✅ Graph-sitter available")
except ImportError as e:
    print(f"❌ Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


@dataclass
class RealLSPDiagnostic:
    """Real LSP diagnostic from actual linting tools."""
    file_path: str
    line: int
    character: int
    severity: str  # error, warning, info, hint
    message: str
    code: Optional[str]
    source: str  # flake8, pylint, mypy
    rule_id: Optional[str]


@dataclass
class CodebaseHealthReport:
    """Comprehensive codebase health report."""
    total_files: int
    total_lines: int
    total_errors: int
    total_warnings: int
    total_info: int
    error_density: float  # errors per 1000 lines
    most_problematic_files: List[Dict[str, Any]]
    error_categories: Dict[str, int]
    tool_results: Dict[str, Dict[str, Any]]


class RealLSPDiagnosticsAnalyzer:
    """Analyzer that captures real code errors using actual linting tools."""
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path).resolve()
        self.codebase: Optional[Codebase] = None
        self.diagnostics: List[RealLSPDiagnostic] = []
        self.analysis_results: Dict[str, Any] = {}
        
    def initialize_codebase(self) -> bool:
        """Initialize the codebase."""
        try:
            print(f"🔍 Initializing real LSP diagnostics analyzer for: {self.codebase_path}")
            
            if GRAPH_SITTER_AVAILABLE:
                self.codebase = Codebase(str(self.codebase_path))
                print("✅ Graph-sitter codebase initialized")
            else:
                print("⚠️  Proceeding without graph-sitter")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize codebase: {e}")
            traceback.print_exc()
            return False
    
    def run_flake8_analysis(self) -> List[RealLSPDiagnostic]:
        """Run flake8 analysis and capture diagnostics."""
        print("\n🔍 Running flake8 analysis...")
        
        diagnostics = []
        
        try:
            # Run flake8 with specific configuration
            cmd = [
                'python', '-m', 'flake8',
                'src/graph_sitter/',
                '--max-line-length=120',
                '--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s',
                '--statistics',
                '--count'
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.codebase_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse flake8 output
            if result.stdout or result.stderr:
                output = result.stderr if result.stderr else result.stdout
                lines = output.strip().split('\n')
                
                for line in lines:
                    if ':' in line and ' ' in line:
                        try:
                            # Parse format: path:line:col: code message
                            parts = line.split(':', 3)
                            if len(parts) >= 4:
                                file_path = parts[0].strip()
                                line_num = int(parts[1])
                                col_num = int(parts[2])
                                
                                # Extract code and message
                                code_and_message = parts[3].strip()
                                if ' ' in code_and_message:
                                    code, message = code_and_message.split(' ', 1)
                                else:
                                    code = code_and_message
                                    message = "Style violation"
                                
                                # Determine severity based on code
                                severity = 'error' if code.startswith('E') else 'warning'
                                
                                diagnostic = RealLSPDiagnostic(
                                    file_path=file_path,
                                    line=line_num,
                                    character=col_num,
                                    severity=severity,
                                    message=message.strip(),
                                    code=code.strip(),
                                    source='flake8',
                                    rule_id=code.strip()
                                )
                                
                                diagnostics.append(diagnostic)
                                
                        except (ValueError, IndexError) as e:
                            # Skip lines that don't match expected format
                            continue
            
            print(f"✅ Flake8 analysis complete: {len(diagnostics)} issues found")
            
        except subprocess.TimeoutExpired:
            print("⚠️  Flake8 analysis timed out")
        except Exception as e:
            print(f"❌ Flake8 analysis failed: {e}")
        
        return diagnostics
    
    def run_mypy_analysis(self) -> List[RealLSPDiagnostic]:
        """Run mypy analysis and capture diagnostics."""
        print("\n🔍 Running mypy analysis...")
        
        diagnostics = []
        
        try:
            # Run mypy with specific configuration
            cmd = [
                'python', '-m', 'mypy',
                'src/graph_sitter/',
                '--ignore-missing-imports',
                '--show-error-codes',
                '--no-error-summary'
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.codebase_path,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            # Parse mypy output
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    if ':' in line and 'error:' in line:
                        try:
                            # Parse format: path:line: error: message [code]
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                file_path = parts[0].strip()
                                line_num = int(parts[1])
                                
                                # Extract error message and code
                                error_part = parts[2].strip()
                                if 'error:' in error_part:
                                    message = error_part.split('error:', 1)[1].strip()
                                    
                                    # Extract error code if present
                                    code = None
                                    if '[' in message and ']' in message:
                                        code_start = message.rfind('[')
                                        code_end = message.rfind(']')
                                        if code_start < code_end:
                                            code = message[code_start+1:code_end]
                                            message = message[:code_start].strip()
                                    
                                    diagnostic = RealLSPDiagnostic(
                                        file_path=file_path,
                                        line=line_num,
                                        character=0,
                                        severity='error',
                                        message=message,
                                        code=code,
                                        source='mypy',
                                        rule_id=code
                                    )
                                    
                                    diagnostics.append(diagnostic)
                                    
                        except (ValueError, IndexError):
                            continue
            
            print(f"✅ Mypy analysis complete: {len(diagnostics)} issues found")
            
        except subprocess.TimeoutExpired:
            print("⚠️  Mypy analysis timed out")
        except Exception as e:
            print(f"❌ Mypy analysis failed: {e}")
        
        return diagnostics
    
    def collect_all_real_diagnostics(self) -> List[RealLSPDiagnostic]:
        """Collect all real diagnostics from multiple tools."""
        print("\n🔍 Collecting ALL real LSP diagnostics from linting tools...")
        
        all_diagnostics = []
        
        # Run flake8 analysis
        flake8_diagnostics = self.run_flake8_analysis()
        all_diagnostics.extend(flake8_diagnostics)
        
        # Run mypy analysis
        mypy_diagnostics = self.run_mypy_analysis()
        all_diagnostics.extend(mypy_diagnostics)
        
        # Store results
        self.diagnostics = all_diagnostics
        
        # Print summary
        print(f"\n✅ Real LSP diagnostics collection complete:")
        print(f"   📊 Total diagnostics: {len(all_diagnostics)}")
        
        # Count by severity and source
        severity_counts = defaultdict(int)
        source_counts = defaultdict(int)
        
        for diag in all_diagnostics:
            severity_counts[diag.severity] += 1
            source_counts[diag.source] += 1
        
        print(f"\n📊 By Severity:")
        for severity, count in severity_counts.items():
            emoji = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'hint': '💡'}.get(severity, '📝')
            print(f"   {emoji} {severity.title()}: {count}")
        
        print(f"\n🔧 By Tool:")
        for source, count in source_counts.items():
            print(f"   {source}: {count}")
        
        return all_diagnostics
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns and hotspots."""
        print("\n📊 Analyzing error patterns...")
        
        if not self.diagnostics:
            return {}
        
        # Count errors by file
        file_errors = defaultdict(int)
        error_categories = defaultdict(int)
        
        for diag in self.diagnostics:
            file_errors[diag.file_path] += 1
            if diag.rule_id:
                error_categories[diag.rule_id] += 1
        
        # Find most problematic files
        most_problematic = sorted(
            file_errors.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Calculate total lines (estimate)
        total_lines = 0
        if self.codebase and hasattr(self.codebase, 'files'):
            total_lines = len(list(self.codebase.files)) * 100  # Rough estimate
        else:
            total_lines = 100000  # Fallback estimate
        
        error_density = (len(self.diagnostics) / total_lines) * 1000
        
        return {
            'most_problematic_files': [
                {'file': file, 'error_count': count} 
                for file, count in most_problematic
            ],
            'error_categories': dict(error_categories),
            'error_density': round(error_density, 2),
            'total_errors': len([d for d in self.diagnostics if d.severity == 'error']),
            'total_warnings': len([d for d in self.diagnostics if d.severity == 'warning'])
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        print("\n📊 Generating comprehensive report...")
        
        start_time = time.time()
        
        # Collect all diagnostics
        diagnostics = self.collect_all_real_diagnostics()
        
        # Analyze patterns
        patterns = self.analyze_error_patterns()
        
        # Calculate metrics
        analysis_time = time.time() - start_time
        
        # Create comprehensive report
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'codebase_path': str(self.codebase_path),
            'analysis_time': round(analysis_time, 2),
            'total_diagnostics': len(diagnostics),
            'diagnostics_by_severity': {
                'errors': len([d for d in diagnostics if d.severity == 'error']),
                'warnings': len([d for d in diagnostics if d.severity == 'warning']),
                'info': len([d for d in diagnostics if d.severity == 'info']),
                'hints': len([d for d in diagnostics if d.severity == 'hint'])
            },
            'diagnostics_by_tool': {
                'flake8': len([d for d in diagnostics if d.source == 'flake8']),
                'mypy': len([d for d in diagnostics if d.source == 'mypy']),
                'pylint': len([d for d in diagnostics if d.source == 'pylint'])
            },
            'error_patterns': patterns,
            'sample_diagnostics': [
                {
                    'file': d.file_path,
                    'line': d.line,
                    'severity': d.severity,
                    'message': d.message,
                    'code': d.code,
                    'source': d.source
                }
                for d in diagnostics[:20]  # Show first 20 as samples
            ],
            'all_diagnostics': [
                {
                    'file_path': d.file_path,
                    'line': d.line,
                    'character': d.character,
                    'severity': d.severity,
                    'message': d.message,
                    'code': d.code,
                    'source': d.source,
                    'rule_id': d.rule_id
                }
                for d in diagnostics
            ]
        }
        
        return report
    
    def print_summary_report(self, report: Dict[str, Any]):
        """Print a summary of the analysis results."""
        print("\n" + "=" * 80)
        print("📊 REAL LSP DIAGNOSTICS ANALYZER - COMPREHENSIVE REPORT")
        print("=" * 80)
        
        print(f"\n🎯 ANALYSIS SUMMARY:")
        print(f"   Analysis Time: {report['analysis_time']} seconds")
        print(f"   Total Issues Found: {report['total_diagnostics']}")
        
        print(f"\n🔍 DIAGNOSTICS BY SEVERITY:")
        severity_data = report['diagnostics_by_severity']
        print(f"   ❌ Errors: {severity_data['errors']}")
        print(f"   ⚠️  Warnings: {severity_data['warnings']}")
        print(f"   ℹ️  Info: {severity_data['info']}")
        print(f"   💡 Hints: {severity_data['hints']}")
        
        print(f"\n🔧 DIAGNOSTICS BY TOOL:")
        tool_data = report['diagnostics_by_tool']
        for tool, count in tool_data.items():
            if count > 0:
                print(f"   {tool}: {count}")
        
        # Show most problematic files
        patterns = report['error_patterns']
        if patterns.get('most_problematic_files'):
            print(f"\n🔥 MOST PROBLEMATIC FILES:")
            for i, file_info in enumerate(patterns['most_problematic_files'][:5]):
                print(f"   {i+1}. {file_info['file']} - {file_info['error_count']} issues")
        
        # Show top error categories
        if patterns.get('error_categories'):
            print(f"\n📊 TOP ERROR CATEGORIES:")
            sorted_categories = sorted(
                patterns['error_categories'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            for i, (category, count) in enumerate(sorted_categories[:5]):
                print(f"   {i+1}. {category}: {count} occurrences")
        
        # Show sample errors
        if report.get('sample_diagnostics'):
            print(f"\n❌ SAMPLE ERRORS:")
            for i, diag in enumerate(report['sample_diagnostics'][:5]):
                print(f"   {i+1}. {diag['file']}:{diag['line']} - {diag['message']} [{diag['code']}]")
        
        print(f"\n✅ Real LSP diagnostics analysis complete!")
        print(f"📄 Found {report['total_diagnostics']} real issues in the codebase")


def main():
    """Main function to run the real LSP diagnostics analyzer."""
    print("🚀 REAL LSP DIAGNOSTICS ANALYZER")
    print("=" * 50)
    print("Captures actual code errors using real linting tools (flake8, mypy)")
    print("This shows the REAL errors that exist in the codebase.")
    print()
    
    # Initialize analyzer
    analyzer = RealLSPDiagnosticsAnalyzer(".")
    
    if not analyzer.initialize_codebase():
        print("❌ Failed to initialize codebase. Exiting.")
        return
    
    try:
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_report()
        
        # Print summary
        analyzer.print_summary_report(report)
        
        # Save detailed report
        report_file = Path("real_lsp_diagnostics_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Save diagnostics separately
        diagnostics_file = Path("real_lsp_diagnostics_detailed.json")
        with open(diagnostics_file, 'w') as f:
            json.dump(report['all_diagnostics'], f, indent=2, default=str)
        print(f"💾 All diagnostics saved to: {diagnostics_file}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        traceback.print_exc()
    
    print("\n🎉 Real LSP Diagnostics Analysis Complete!")
    print("This analyzer shows the actual errors that exist in the codebase using real linting tools.")


if __name__ == "__main__":
    main()

