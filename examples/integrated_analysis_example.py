#!/usr/bin/env python
"""Example demonstrating the IntegratedAnalyzer for comprehensive code analysis.

This example shows how to:
1. Initialize the integrated analyzer
2. Run structural analysis
3. Get LSP diagnostics
4. Generate AI-powered fixes (optional)
5. Run full analysis pipeline
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from integrated_analysis import IntegratedAnalyzer, analyze_repository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_1_basic_usage():
    """Example 1: Basic structural analysis only."""
    print("\n" + "="*80)
    print("Example 1: Basic Structural Analysis")
    print("="*80)
    
    # Initialize analyzer with minimal features
    analyzer = IntegratedAnalyzer(
        repo_path=".",
        enable_lsp=False,  # Disable LSP for faster analysis
        enable_autogenlib=False
    )
    
    # Check health
    health = analyzer.health_check()
    print(f"\n✅ Components initialized: {health}")
    
    # Run structural analysis
    print("\n📊 Running structural analysis...")
    structure = analyzer.analyze_structure()
    
    print(f"\n📈 Results:")
    print(f"  Files: {structure['file_count']}")
    print(f"  Functions: {structure['function_count']}")
    print(f"  Classes: {structure['class_count']}")
    
    # Show some dependencies
    print(f"\n🔗 Sample dependencies:")
    for file, deps in list(structure['dependencies'].items())[:3]:
        print(f"  {file}: {len(deps)} dependencies")


def example_2_with_lsp():
    """Example 2: Analysis with LSP diagnostics."""
    print("\n" + "="*80)
    print("Example 2: Analysis with LSP Diagnostics")
    print("="*80)
    
    # Initialize with LSP enabled
    analyzer = IntegratedAnalyzer(
        repo_path=".",
        enable_lsp=True,
        enable_autogenlib=False
    )
    
    # Get diagnostics
    print("\n🔍 Collecting LSP diagnostics...")
    diagnostics = analyzer.get_diagnostics()
    
    print(f"\n📋 Diagnostic Summary:")
    print(f"  Errors: {len(diagnostics['errors'])}")
    print(f"  Warnings: {len(diagnostics['warnings'])}")
    print(f"  Info: {len(diagnostics['info'])}")
    
    # Show first few errors
    if diagnostics['errors']:
        print(f"\n❌ First 3 errors:")
        for err in diagnostics['errors'][:3]:
            print(f"  {err.file_path}:{err.line} - {err.message[:60]}...")


def example_3_full_analysis():
    """Example 3: Complete analysis pipeline."""
    print("\n" + "="*80)
    print("Example 3: Full Analysis Pipeline")
    print("="*80)
    
    # Use convenience function for full analysis
    print("\n🚀 Running full analysis...")
    results = analyze_repository(
        repo_path=".",
        enable_lsp=True,
        enable_autogenlib=False,  # Set to True if you have OpenAI API key
        generate_fixes=False  # Set to True to generate AI fixes
    )
    
    print(f"\n📊 Complete Results:")
    print(f"  Files analyzed: {results.file_count}")
    print(f"  Functions: {results.function_count}")
    print(f"  Classes: {results.class_count}")
    print(f"  Symbols: {results.symbol_count}")
    print(f"\n  Errors: {len(results.errors)}")
    print(f"  Warnings: {len(results.warnings)}")
    print(f"  Info: {len(results.info)}")
    
    # Show dependency stats
    total_deps = sum(len(deps) for deps in results.dependency_graph.values())
    print(f"\n  Total dependencies: {total_deps}")
    
    if results.suggested_fixes:
        print(f"  AI fixes suggested: {len(results.suggested_fixes)}")


def example_4_with_ai_fixes():
    """Example 4: AI-powered error resolution (requires OpenAI API key)."""
    print("\n" + "="*80)
    print("Example 4: AI-Powered Error Resolution")
    print("="*80)
    print("⚠️  This example requires OPENAI_API_KEY environment variable")
    
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set, skipping AI fix example")
        return
    
    # Initialize with AutoGenLib enabled
    analyzer = IntegratedAnalyzer(
        repo_path=".",
        enable_lsp=True,
        enable_autogenlib=True
    )
    
    # Get errors
    diagnostics = analyzer.get_diagnostics()
    errors = diagnostics['errors']
    
    if not errors:
        print("✅ No errors found!")
        return
    
    print(f"\n🤖 Generating AI fixes for {min(5, len(errors))} errors...")
    fixes = analyzer.generate_fixes(errors, max_fixes=5)
    
    print(f"\n💡 Generated {len(fixes)} fixes:")
    for i, fix_data in enumerate(fixes, 1):
        diag = fix_data['diagnostic']
        fix = fix_data['fix']
        print(f"\n{i}. {diag.file_path}:{diag.line}")
        print(f"   Error: {diag.message[:60]}...")
        print(f"   Fix: {fix.get('description', 'No description')[:80]}...")
    
    # Optionally apply fixes
    if input("\nApply these fixes? (y/n): ").lower() == 'y':
        applied = analyzer.apply_fixes(fixes)
        print(f"✅ Applied {applied} fixes!")


def main():
    """Run all examples."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Integrated Analysis Examples')
    parser.add_argument(
        '--example',
        type=int,
        choices=[1, 2, 3, 4],
        help='Run specific example (1-4)'
    )
    
    args = parser.parse_args()
    
    if args.example:
        examples = {
            1: example_1_basic_usage,
            2: example_2_with_lsp,
            3: example_3_full_analysis,
            4: example_4_with_ai_fixes,
        }
        examples[args.example]()
    else:
        # Run all examples
        example_1_basic_usage()
        example_2_with_lsp()
        example_3_full_analysis()
        # example_4_with_ai_fixes()  # Commented out by default


if __name__ == "__main__":
    main()

