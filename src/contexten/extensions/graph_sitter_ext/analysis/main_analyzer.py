#!/usr/bin/env python3
"""
Main Analyzer

Comprehensive codebase analysis using all available analyzers.
Provides a unified interface to run all analysis modules and generate reports.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import graph_sitter
from graph_sitter import Codebase

# Import all analyzer modules
from .dead_code_detector import detect_dead_code, remove_dead_code
from .complexity_analyzer import analyze_complexity, find_complex_functions, find_large_functions
from .dependency_analyzer import analyze_dependencies, detect_circular_dependencies, analyze_module_coupling
from .security_analyzer import analyze_security, check_import_security
from .call_graph_analyzer import analyze_call_graph, find_hotspot_functions


@graph_sitter.function("comprehensive-analysis")
def comprehensive_analysis(codebase: Codebase):
    """Run comprehensive analysis using all available analyzers."""
    start_time = time.time()
    
    print("🔍 Starting comprehensive codebase analysis...")
    
    results = {
        'metadata': {
            'analysis_timestamp': datetime.now().isoformat(),
            'codebase_info': {
                'total_files': len(codebase.files),
                'total_functions': len(codebase.functions),
                'total_classes': len(codebase.classes),
            },
            'analysis_duration': 0
        },
        'dead_code': {},
        'complexity': {},
        'dependencies': {},
        'security': {},
        'call_graph': {},
        'summary': {},
        'recommendations': []
    }
    
    # 1. Dead Code Analysis
    print("💀 Analyzing dead code...")
    try:
        results['dead_code'] = detect_dead_code(codebase)
    except Exception as e:
        print(f"Error in dead code analysis: {e}")
        results['dead_code'] = {'error': str(e)}
    
    # 2. Complexity Analysis
    print("📊 Analyzing complexity...")
    try:
        results['complexity'] = analyze_complexity(codebase)
        # Add additional complexity insights
        results['complexity']['complex_functions'] = find_complex_functions(codebase)
        results['complexity']['large_functions'] = find_large_functions(codebase)
    except Exception as e:
        print(f"Error in complexity analysis: {e}")
        results['complexity'] = {'error': str(e)}
    
    # 3. Dependency Analysis
    print("🔗 Analyzing dependencies...")
    try:
        results['dependencies'] = analyze_dependencies(codebase)
        # Add circular dependency detection
        circular_deps = detect_circular_dependencies(codebase)
        results['dependencies']['circular_analysis'] = circular_deps
        # Add coupling analysis
        coupling = analyze_module_coupling(codebase)
        results['dependencies']['coupling_analysis'] = coupling
    except Exception as e:
        print(f"Error in dependency analysis: {e}")
        results['dependencies'] = {'error': str(e)}
    
    # 4. Security Analysis
    print("🔒 Analyzing security...")
    try:
        results['security'] = analyze_security(codebase)
        # Add import security check
        dangerous_imports = check_import_security(codebase)
        results['security']['dangerous_imports'] = dangerous_imports
    except Exception as e:
        print(f"Error in security analysis: {e}")
        results['security'] = {'error': str(e)}
    
    # 5. Call Graph Analysis
    print("📞 Analyzing call graph...")
    try:
        results['call_graph'] = analyze_call_graph(codebase)
        # Add hotspot analysis
        hotspots = find_hotspot_functions(codebase)
        results['call_graph']['hotspots'] = hotspots
    except Exception as e:
        print(f"Error in call graph analysis: {e}")
        results['call_graph'] = {'error': str(e)}
    
    # 6. Generate Summary and Recommendations
    results['summary'] = generate_summary(results)
    results['recommendations'] = generate_recommendations(results)
    
    # Update metadata
    results['metadata']['analysis_duration'] = time.time() - start_time
    
    print(f"✅ Analysis complete in {results['metadata']['analysis_duration']:.2f} seconds")
    
    return results


def generate_summary(results):
    """Generate a summary of all analysis results."""
    summary = {
        'total_issues': 0,
        'critical_issues': 0,
        'high_priority_issues': 0,
        'code_quality_score': 0,
        'maintainability_score': 0,
        'security_score': 0
    }
    
    # Count issues from different analyzers
    if 'dead_code' in results and 'summary' in results['dead_code']:
        dead_code_issues = (
            results['dead_code']['summary'].get('total_dead_functions', 0) +
            results['dead_code']['summary'].get('total_unused_imports', 0) +
            results['dead_code']['summary'].get('total_unused_classes', 0)
        )
        summary['total_issues'] += dead_code_issues
    
    if 'complexity' in results and 'summary' in results['complexity']:
        high_complexity = results['complexity']['summary'].get('high_complexity_functions', 0)
        summary['high_priority_issues'] += high_complexity
        summary['total_issues'] += high_complexity
    
    if 'security' in results and 'summary' in results['security']:
        security_issues = results['security']['summary'].get('total_issues', 0)
        critical_security = results['security']['summary'].get('critical_issues', 0)
        summary['total_issues'] += security_issues
        summary['critical_issues'] += critical_security
    
    if 'dependencies' in results and 'summary' in results['dependencies']:
        circular_deps = results['dependencies']['summary'].get('circular_count', 0)
        summary['high_priority_issues'] += circular_deps
        summary['total_issues'] += circular_deps
    
    # Calculate quality scores (0-100)
    if 'complexity' in results and 'summary' in results['complexity']:
        avg_maintainability = results['complexity']['summary'].get('avg_maintainability', 50)
        summary['maintainability_score'] = int(avg_maintainability)
    
    # Security score based on issues found
    if 'security' in results and 'summary' in results['security']:
        total_security_issues = results['security']['summary'].get('total_issues', 0)
        # Simple scoring: start at 100, subtract points for issues
        summary['security_score'] = max(0, 100 - (total_security_issues * 10))
    
    # Overall code quality score
    summary['code_quality_score'] = int((
        summary['maintainability_score'] + 
        summary['security_score'] + 
        max(0, 100 - summary['total_issues'])
    ) / 3)
    
    return summary


def generate_recommendations(results):
    """Generate actionable recommendations based on analysis results."""
    recommendations = []
    
    # Dead code recommendations
    if 'dead_code' in results and 'summary' in results['dead_code']:
        dead_functions = results['dead_code']['summary'].get('total_dead_functions', 0)
        if dead_functions > 0:
            recommendations.append({
                'category': 'dead_code',
                'priority': 'medium',
                'title': f'Remove {dead_functions} unused functions',
                'description': 'Clean up codebase by removing unused functions to improve maintainability',
                'action': 'Run dead code removal tool'
            })
        
        unused_imports = results['dead_code']['summary'].get('total_unused_imports', 0)
        if unused_imports > 0:
            recommendations.append({
                'category': 'dead_code',
                'priority': 'low',
                'title': f'Remove {unused_imports} unused imports',
                'description': 'Clean up import statements to reduce dependencies',
                'action': 'Remove unused import statements'
            })
    
    # Complexity recommendations
    if 'complexity' in results and 'summary' in results['complexity']:
        high_complexity = results['complexity']['summary'].get('high_complexity_functions', 0)
        if high_complexity > 0:
            recommendations.append({
                'category': 'complexity',
                'priority': 'high',
                'title': f'Refactor {high_complexity} complex functions',
                'description': 'Break down complex functions to improve readability and maintainability',
                'action': 'Split large functions into smaller, focused functions'
            })
        
        avg_maintainability = results['complexity']['summary'].get('avg_maintainability', 100)
        if avg_maintainability < 50:
            recommendations.append({
                'category': 'complexity',
                'priority': 'high',
                'title': 'Improve overall maintainability',
                'description': f'Average maintainability index is {avg_maintainability:.1f}, consider refactoring',
                'action': 'Focus on reducing complexity and improving code structure'
            })
    
    # Security recommendations
    if 'security' in results and 'summary' in results['security']:
        critical_security = results['security']['summary'].get('critical_issues', 0)
        if critical_security > 0:
            recommendations.append({
                'category': 'security',
                'priority': 'critical',
                'title': f'Fix {critical_security} critical security issues',
                'description': 'Address critical security vulnerabilities immediately',
                'action': 'Review and fix SQL injection, hardcoded secrets, and other critical issues'
            })
        
        high_security = results['security']['summary'].get('high_issues', 0)
        if high_security > 0:
            recommendations.append({
                'category': 'security',
                'priority': 'high',
                'title': f'Address {high_security} high-priority security issues',
                'description': 'Fix high-priority security vulnerabilities',
                'action': 'Review unsafe eval usage, command injection risks, etc.'
            })
    
    # Dependency recommendations
    if 'dependencies' in results and 'summary' in results['dependencies']:
        circular_deps = results['dependencies']['summary'].get('circular_count', 0)
        if circular_deps > 0:
            recommendations.append({
                'category': 'dependencies',
                'priority': 'high',
                'title': f'Resolve {circular_deps} circular dependencies',
                'description': 'Break circular dependencies to improve code architecture',
                'action': 'Refactor code to eliminate circular imports'
            })
    
    # Call graph recommendations
    if 'call_graph' in results and 'summary' in results['call_graph']:
        unused_functions = results['call_graph']['summary'].get('unused_count', 0)
        if unused_functions > 5:
            recommendations.append({
                'category': 'call_graph',
                'priority': 'medium',
                'title': f'Review {unused_functions} unused functions',
                'description': 'Consider removing or documenting unused functions',
                'action': 'Review function usage and remove if truly unused'
            })
    
    # Sort recommendations by priority
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
    
    return recommendations


def save_analysis_report(results, output_file: str = None):
    """Save analysis results to a JSON file."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"codebase_analysis_{timestamp}.json"
    
    output_path = Path(output_file)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"📄 Analysis report saved to {output_path}")
    return output_path


def print_analysis_summary(results):
    """Print a formatted summary of the analysis results."""
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE CODEBASE ANALYSIS REPORT")
    print("="*60)
    
    # Metadata
    metadata = results.get('metadata', {})
    print(f"📅 Analysis Date: {metadata.get('analysis_timestamp', 'Unknown')}")
    print(f"⏱️  Duration: {metadata.get('analysis_duration', 0):.2f} seconds")
    
    codebase_info = metadata.get('codebase_info', {})
    print(f"📁 Files: {codebase_info.get('total_files', 0)}")
    print(f"⚡ Functions: {codebase_info.get('total_functions', 0)}")
    print(f"🏗️  Classes: {codebase_info.get('total_classes', 0)}")
    
    # Summary scores
    summary = results.get('summary', {})
    print(f"\n📈 QUALITY SCORES")
    print(f"Overall Code Quality: {summary.get('code_quality_score', 0)}/100")
    print(f"Maintainability: {summary.get('maintainability_score', 0)}/100")
    print(f"Security: {summary.get('security_score', 0)}/100")
    
    # Issue counts
    print(f"\n🚨 ISSUES FOUND")
    print(f"Total Issues: {summary.get('total_issues', 0)}")
    print(f"Critical Issues: {summary.get('critical_issues', 0)}")
    print(f"High Priority: {summary.get('high_priority_issues', 0)}")
    
    # Top recommendations
    recommendations = results.get('recommendations', [])
    if recommendations:
        print(f"\n💡 TOP RECOMMENDATIONS")
        for i, rec in enumerate(recommendations[:5], 1):
            priority_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(rec['priority'], '⚪')
            print(f"{i}. {priority_emoji} {rec['title']}")
            print(f"   {rec['description']}")
    
    print("="*60)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        codebase_path = sys.argv[1]
    else:
        codebase_path = "./"
    
    print(f"🔍 Analyzing codebase: {codebase_path}")
    codebase = Codebase(codebase_path)
    
    # Run comprehensive analysis
    results = comprehensive_analysis(codebase)
    
    # Print summary
    print_analysis_summary(results)
    
    # Save detailed report
    report_file = save_analysis_report(results)
    
    print(f"\n✅ Analysis complete! Detailed report saved to {report_file}")
    
    # Optionally show how to fix issues
    if results['summary']['total_issues'] > 0:
        print(f"\n🔧 To automatically fix some issues, you can run:")
        print(f"   python -c \"from graph_sitter import Codebase; from analysis.dead_code_detector import remove_dead_code; codebase = Codebase('{codebase_path}'); remove_dead_code(codebase); codebase.commit()\"")

