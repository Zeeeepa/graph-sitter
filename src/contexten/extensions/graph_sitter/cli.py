#!/usr/bin/env python3
"""
CLI for Graph_Sitter Analysis

Command-line interface for running codebase analysis using graph_sitter.
"""

import argparse
import sys
from pathlib import Path

try:
    from graph_sitter import Codebase
    from .analysis.main_analyzer import comprehensive_analysis, print_analysis_summary, save_analysis_report
    from .analysis.dead_code_detector import detect_dead_code, remove_dead_code
    from .analysis.complexity_analyzer import analyze_complexity
    from .analysis.dependency_analyzer import analyze_dependencies
    from .analysis.security_analyzer import analyze_security
    from .analysis.call_graph_analyzer import analyze_call_graph
except ImportError as e:
    print(f"Error importing graph_sitter: {e}")
    print("Please install graph_sitter: pip install graph-sitter")
    sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive codebase analysis using graph_sitter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./my_project                    # Run comprehensive analysis
  %(prog)s ./my_project --analysis dead   # Run only dead code analysis
  %(prog)s ./my_project --fix-dead-code   # Remove dead code automatically
  %(prog)s ./my_project --output report.json  # Save detailed report
        """
    )
    
    parser.add_argument(
        "codebase_path",
        help="Path to the codebase to analyze"
    )
    
    parser.add_argument(
        "--analysis",
        choices=["comprehensive", "dead", "complexity", "dependencies", "security", "calls"],
        default="comprehensive",
        help="Type of analysis to run (default: comprehensive)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file for detailed JSON report"
    )
    
    parser.add_argument(
        "--fix-dead-code",
        action="store_true",
        help="Automatically remove dead code (use with caution)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output"
    )
    
    args = parser.parse_args()
    
    # Validate codebase path
    codebase_path = Path(args.codebase_path)
    if not codebase_path.exists():
        print(f"Error: Path '{codebase_path}' does not exist")
        sys.exit(1)
    
    if not args.quiet:
        print(f"🔍 Analyzing codebase: {codebase_path}")
    
    try:
        # Initialize codebase
        codebase = Codebase(str(codebase_path))
        
        # Run analysis based on type
        if args.analysis == "comprehensive":
            results = comprehensive_analysis(codebase)
            if not args.quiet:
                print_analysis_summary(results)
        
        elif args.analysis == "dead":
            if not args.quiet:
                print("💀 Running dead code analysis...")
            results = detect_dead_code(codebase)
            print_dead_code_results(results)
        
        elif args.analysis == "complexity":
            if not args.quiet:
                print("📊 Running complexity analysis...")
            results = analyze_complexity(codebase)
            print_complexity_results(results)
        
        elif args.analysis == "dependencies":
            if not args.quiet:
                print("🔗 Running dependency analysis...")
            results = analyze_dependencies(codebase)
            print_dependency_results(results)
        
        elif args.analysis == "security":
            if not args.quiet:
                print("🔒 Running security analysis...")
            results = analyze_security(codebase)
            print_security_results(results)
        
        elif args.analysis == "calls":
            if not args.quiet:
                print("📞 Running call graph analysis...")
            results = analyze_call_graph(codebase)
            print_call_graph_results(results)
        
        # Handle dead code removal
        if args.fix_dead_code:
            if not args.quiet:
                print("\n🔧 Removing dead code...")
            removed_count = remove_dead_code(codebase)
            codebase.commit()
            print(f"✅ Removed {removed_count} dead code elements")
        
        # Save detailed report if requested
        if args.output:
            if args.analysis == "comprehensive":
                save_analysis_report(results, args.output)
            else:
                # Save individual analysis results
                import json
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"📄 Report saved to {args.output}")
    
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def print_dead_code_results(results):
    """Print dead code analysis results."""
    summary = results.get('summary', {})
    print(f"\n💀 Dead Code Analysis Results:")
    print(f"Dead functions: {summary.get('total_dead_functions', 0)}")
    print(f"Dead variables: {summary.get('total_dead_variables', 0)}")
    print(f"Unused imports: {summary.get('total_unused_imports', 0)}")
    print(f"Unused classes: {summary.get('total_unused_classes', 0)}")
    
    # Show some examples
    if results.get('dead_functions'):
        print(f"\nDead functions:")
        for func in results['dead_functions'][:5]:
            print(f"  • {func['name']} in {func['file']}")


def print_complexity_results(results):
    """Print complexity analysis results."""
    summary = results.get('summary', {})
    print(f"\n📊 Complexity Analysis Results:")
    print(f"Total functions: {summary.get('total_functions', 0)}")
    print(f"Average complexity: {summary.get('avg_complexity', 0):.2f}")
    print(f"High complexity functions: {summary.get('high_complexity_functions', 0)}")
    print(f"Average maintainability: {summary.get('avg_maintainability', 0):.1f}")


def print_dependency_results(results):
    """Print dependency analysis results."""
    summary = results.get('summary', {})
    print(f"\n🔗 Dependency Analysis Results:")
    print(f"Total imports: {summary.get('total_imports', 0)}")
    print(f"External imports: {summary.get('external_imports', 0)}")
    print(f"Internal imports: {summary.get('internal_imports', 0)}")
    print(f"Circular dependencies: {summary.get('circular_count', 0)}")
    
    if results.get('circular_dependencies'):
        print(f"\nCircular dependencies:")
        for cycle in results['circular_dependencies'][:3]:
            print(f"  • {' -> '.join(cycle)}")


def print_security_results(results):
    """Print security analysis results."""
    summary = results.get('summary', {})
    print(f"\n🔒 Security Analysis Results:")
    print(f"Total security issues: {summary.get('total_issues', 0)}")
    print(f"Critical issues: {summary.get('critical_issues', 0)}")
    print(f"High severity issues: {summary.get('high_issues', 0)}")
    
    # Show critical issues
    if results.get('sql_injection_risks'):
        print(f"\nSQL injection risks: {len(results['sql_injection_risks'])}")
    if results.get('hardcoded_secrets'):
        print(f"Hardcoded secrets: {len(results['hardcoded_secrets'])}")


def print_call_graph_results(results):
    """Print call graph analysis results."""
    summary = results.get('summary', {})
    print(f"\n📞 Call Graph Analysis Results:")
    print(f"Total functions: {summary.get('total_functions', 0)}")
    print(f"Total calls: {summary.get('total_calls', 0)}")
    print(f"Average calls per function: {summary.get('avg_calls_per_function', 0):.1f}")
    print(f"Recursive functions: {summary.get('recursive_count', 0)}")
    print(f"Unused functions: {summary.get('unused_count', 0)}")


if __name__ == "__main__":
    main()

