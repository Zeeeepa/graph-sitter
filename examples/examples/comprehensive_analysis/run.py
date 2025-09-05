#!/usr/bin/env python3
"""
Comprehensive Codebase Analysis Example

This example demonstrates the full capabilities of graph-sitter's comprehensive
codebase analysis system, including:

- Dead code detection using graph traversal from entry points
- Unused parameter detection within function scopes
- Import analysis (unused, circular, unresolved)
- Call site validation and analysis
- Entry point identification
- Symbol usage and dependency mapping

Usage:
    python run.py [repository_url_or_path]
    
Examples:
    python run.py fastapi/fastapi
    python run.py /path/to/local/repo
    python run.py https://github.com/fastapi/fastapi
"""

import sys
import argparse
import json
from pathlib import Path

# Add the src directory to the path so we can import graph_sitter
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from graph_sitter import Codebase
from graph_sitter.configs import CodebaseConfig
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
    comprehensive_analysis,
    print_analysis_report,
    identify_entry_points,
    detect_dead_code,
    detect_unused_parameters,
    analyze_imports,
    analyze_call_sites
)


def analyze_fastapi_example():
    """
    Example: Analyze the FastAPI codebase to demonstrate comprehensive analysis.
    """
    print("🚀 Analyzing FastAPI codebase...")
    print("This may take a few minutes for the initial clone and parsing...")
    
    # Configure comprehensive analysis
    config = CodebaseConfig(
        method_usages=True,
        import_resolution_paths=True,
        full_range_index=True,
        sync_enabled=True
    )
    
    # Load FastAPI codebase
    codebase = Codebase.from_repo(
        'fastapi/fastapi',
        config=config,
        language="python"
    )
    
    print(f"✅ Loaded FastAPI codebase with {len(list(codebase.files))} files")
    
    # Perform comprehensive analysis
    results = comprehensive_analysis(codebase)
    
    # Print detailed report
    print_analysis_report(results)
    
    # Save results to JSON for further analysis
    output_file = "fastapi_analysis_results.json"
    
    # Convert results to JSON-serializable format
    json_results = {}
    for key, value in results.items():
        if key == 'unused_parameters':
            # Convert Function objects to strings for JSON serialization
            json_results[key] = {
                func.name: params for func, params in value.items()
            }
        elif key in ['entry_points', 'dead_code']:
            # Convert Symbol objects to strings
            json_results[key] = {
                category: [symbol.name for symbol in symbols]
                for category, symbols in value.items()
            }
        else:
            json_results[key] = value
    
    with open(output_file, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to {output_file}")
    
    return results


def analyze_local_repository(repo_path: str):
    """
    Analyze a local repository.
    
    Args:
        repo_path: Path to the local repository
    """
    print(f"🔍 Analyzing local repository: {repo_path}")
    
    # Configure comprehensive analysis
    config = CodebaseConfig(
        method_usages=True,
        import_resolution_paths=True,
        full_range_index=True,
        sync_enabled=True
    )
    
    # Load local codebase
    codebase = Codebase(repo_path, config=config)
    
    print(f"✅ Loaded codebase with {len(list(codebase.files))} files")
    
    # Perform comprehensive analysis
    results = comprehensive_analysis(codebase)
    
    # Print detailed report
    print_analysis_report(results)
    
    return results


def analyze_remote_repository(repo_url: str):
    """
    Analyze a remote repository by URL.
    
    Args:
        repo_url: GitHub repository URL or owner/repo format
    """
    print(f"🌐 Analyzing remote repository: {repo_url}")
    
    # Configure comprehensive analysis
    config = CodebaseConfig(
        method_usages=True,
        import_resolution_paths=True,
        full_range_index=True,
        sync_enabled=True
    )
    
    # Handle different URL formats
    if repo_url.startswith('http'):
        # Extract owner/repo from URL
        parts = repo_url.rstrip('/').split('/')
        repo_identifier = f"{parts[-2]}/{parts[-1]}"
    else:
        repo_identifier = repo_url
    
    # Load remote codebase
    codebase = Codebase.from_repo(
        repo_identifier,
        config=config
    )
    
    print(f"✅ Loaded {repo_identifier} with {len(list(codebase.files))} files")
    
    # Perform comprehensive analysis
    results = comprehensive_analysis(codebase)
    
    # Print detailed report
    print_analysis_report(results)
    
    return results


def demonstrate_individual_analyses(codebase: Codebase):
    """
    Demonstrate individual analysis functions.
    
    Args:
        codebase: The codebase to analyze
    """
    print("\n" + "="*60)
    print("🔬 INDIVIDUAL ANALYSIS DEMONSTRATIONS")
    print("="*60)
    
    # Basic summaries
    print("\n📋 Basic Codebase Summary:")
    print(get_codebase_summary(codebase))
    
    # Entry point analysis
    print("\n🚪 Entry Point Analysis:")
    entry_points = identify_entry_points(codebase)
    for category, symbols in entry_points.items():
        if symbols:
            print(f"  {category}: {len(symbols)} found")
            for symbol in symbols[:2]:  # Show first 2
                print(f"    - {symbol.name}")
    
    # Dead code detection
    print("\n💀 Dead Code Detection:")
    dead_code = detect_dead_code(codebase)
    for category, symbols in dead_code.items():
        if symbols:
            print(f"  {category}: {len(symbols)} found")
    
    # Import analysis
    print("\n📦 Import Analysis:")
    import_analysis = analyze_imports(codebase)
    stats = import_analysis['import_statistics']
    print(f"  Unused imports: {stats['unused_count']}")
    print(f"  Circular imports: {stats['circular_count']}")
    print(f"  Unresolved imports: {stats['unresolved_count']}")
    
    # Show example file analysis
    files = list(codebase.files)
    if files:
        example_file = files[0]
        print(f"\n📄 Example File Analysis ({example_file.name}):")
        print(get_file_summary(example_file))
    
    # Show example function analysis
    functions = list(codebase.functions)
    if functions:
        example_func = functions[0]
        print(f"\n🔧 Example Function Analysis ({example_func.name}):")
        print(get_function_summary(example_func))


def main():
    """
    Main entry point for the comprehensive analysis example.
    """
    parser = argparse.ArgumentParser(
        description="Comprehensive Codebase Analysis using graph-sitter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Analyze FastAPI (default)
  %(prog)s fastapi/fastapi          # Analyze FastAPI explicitly
  %(prog)s /path/to/local/repo      # Analyze local repository
  %(prog)s owner/repo               # Analyze GitHub repository
  %(prog)s https://github.com/owner/repo  # Analyze by full URL
        """
    )
    
    parser.add_argument(
        'repository',
        nargs='?',
        default='fastapi/fastapi',
        help='Repository to analyze (default: fastapi/fastapi)'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run individual analysis demonstrations'
    )
    
    parser.add_argument(
        '--output',
        help='Output file for JSON results'
    )
    
    args = parser.parse_args()
    
    print("🔍 COMPREHENSIVE CODEBASE ANALYSIS")
    print("="*50)
    print("Using graph-sitter framework for deep code analysis")
    print("="*50)
    
    try:
        # Determine analysis type based on input
        if Path(args.repository).exists():
            # Local path
            results = analyze_local_repository(args.repository)
            codebase = Codebase(args.repository)
        elif args.repository.startswith('http') or '/' in args.repository:
            # Remote repository
            results = analyze_remote_repository(args.repository)
            # For demo purposes, reload the codebase
            if args.demo:
                if args.repository.startswith('http'):
                    parts = args.repository.rstrip('/').split('/')
                    repo_id = f"{parts[-2]}/{parts[-1]}"
                else:
                    repo_id = args.repository
                codebase = Codebase.from_repo(repo_id)
        else:
            # Default to FastAPI example
            results = analyze_fastapi_example()
            if args.demo:
                codebase = Codebase.from_repo('fastapi/fastapi')
        
        # Run individual demonstrations if requested
        if args.demo and 'codebase' in locals():
            demonstrate_individual_analyses(codebase)
        
        # Save results if output file specified
        if args.output:
            # Convert results to JSON-serializable format
            json_results = {}
            for key, value in results.items():
                if key == 'unused_parameters':
                    json_results[key] = {
                        func.name: params for func, params in value.items()
                    }
                elif key in ['entry_points', 'dead_code']:
                    json_results[key] = {
                        category: [symbol.name for symbol in symbols]
                        for category, symbols in value.items()
                    }
                else:
                    json_results[key] = value
            
            with open(args.output, 'w') as f:
                json.dump(json_results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to {args.output}")
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
