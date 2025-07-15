#!/usr/bin/env python3
"""
Enhanced Serena Demo

Demonstrates the comprehensive codebase knowledge extension capabilities
built on top of graph-sitter's existing powerful features.
"""

import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_sitter import Codebase
from graph_sitter.extensions.serena import SerenaCore
from graph_sitter.extensions.serena.types import SerenaCapability, SerenaConfig


def demo_enhanced_symbol_intelligence(serena: SerenaCore):
    """Demonstrate enhanced symbol intelligence capabilities."""
    print("\n" + "="*60)
    print("🧠 ENHANCED SYMBOL INTELLIGENCE")
    print("="*60)
    
    # Get symbol information at a specific position
    print("\n1. Symbol Information Retrieval:")
    try:
        symbol_info = serena.get_symbol_info("src/graph_sitter/core/codebase.py", 100, 10)
        if symbol_info:
            print(f"   Symbol: {symbol_info['name']}")
            print(f"   Kind: {symbol_info['kind']}")
            print(f"   Location: {symbol_info['location']}")
            print(f"   Documentation: {symbol_info['documentation'][:100]}...")
            print(f"   Usages found: {len(symbol_info['usages'])}")
        else:
            print("   No symbol found at specified position")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Semantic search across codebase
    print("\n2. Semantic Search:")
    try:
        search_results = serena.semantic_search("codebase", max_results=5)
        print(f"   Found {len(search_results)} results for 'codebase':")
        for result in search_results[:3]:
            if hasattr(result, 'symbol_name'):
                print(f"   - {result.symbol_name} in {result.file_path}:{result.line_number}")
                print(f"     Relevance: {result.relevance_score:.2f}")
            else:
                print(f"   - {result}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Code generation
    print("\n3. AI-Assisted Code Generation:")
    try:
        generation_result = serena.generate_code("Create a function to validate email addresses")
        if generation_result:
            print(f"   Generated code:")
            print(f"   {generation_result['generated_code'][:200]}...")
            print(f"   Confidence: {generation_result['confidence_score']:.2f}")
            print(f"   Suggestions: {', '.join(generation_result['suggestions'][:2])}")
    except Exception as e:
        print(f"   Error: {e}")


def demo_advanced_refactoring(serena: SerenaCore):
    """Demonstrate advanced refactoring capabilities."""
    print("\n" + "="*60)
    print("🔧 ADVANCED REFACTORING ENGINE")
    print("="*60)
    
    # Safe rename with conflict detection
    print("\n1. Safe Symbol Renaming:")
    try:
        rename_result = serena.rename_symbol(
            "src/graph_sitter/core/codebase.py", 
            50, 10, 
            "new_symbol_name", 
            preview=True
        )
        if rename_result:
            print(f"   Success: {rename_result['success']}")
            print(f"   Changes: {len(rename_result['changes'])} modifications")
            print(f"   Conflicts: {len(rename_result['conflicts'])} issues")
            print(f"   Message: {rename_result['message']}")
            
            if rename_result['changes']:
                print("   Preview of changes:")
                for change in rename_result['changes'][:2]:
                    print(f"   - {change['type']} in {change['file']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method extraction
    print("\n2. Extract Method Refactoring:")
    try:
        extract_result = serena.extract_method(
            "src/graph_sitter/core/codebase.py",
            100, 110,
            "extracted_helper_method",
            preview=True
        )
        if extract_result:
            print(f"   Success: {extract_result['success']}")
            print(f"   Changes: {len(extract_result['changes'])} modifications")
            print(f"   Message: {extract_result['message']}")
            
            if extract_result['changes']:
                print("   Preview of changes:")
                for change in extract_result['changes']:
                    print(f"   - {change['type']}: {change['description']}")
    except Exception as e:
        print(f"   Error: {e}")


def demo_realtime_analysis(serena: SerenaCore):
    """Demonstrate real-time code analysis."""
    print("\n" + "="*60)
    print("⚡ REAL-TIME CODE ANALYSIS")
    print("="*60)
    
    # Start the analysis engine
    print("\n1. Starting Real-time Analysis Engine:")
    try:
        serena.start_analysis_engine()
        print("   ✅ Analysis engine started")
        
        # Give it a moment to initialize
        time.sleep(1)
        
        # Analyze a specific file
        print("\n2. File Analysis:")
        analysis_result = serena.analyze_file("src/graph_sitter/core/codebase.py", force=True)
        if analysis_result:
            print(f"   File: {analysis_result['file_path']}")
            print(f"   Issues found: {len(analysis_result['issues'])}")
            print(f"   Complexity score: {analysis_result['complexity_score']:.2f}")
            print(f"   Maintainability score: {analysis_result['maintainability_score']:.2f}")
            
            # Show some issues
            if analysis_result['issues']:
                print("   Top issues:")
                for issue in analysis_result['issues'][:3]:
                    print(f"   - {issue['severity'].upper()}: {issue['message']}")
                    print(f"     Line {issue['line_number']}: {issue.get('suggestion', 'No suggestion')}")
            
            # Show metrics
            if analysis_result['metrics']:
                print("   Code metrics:")
                metrics = analysis_result['metrics']
                print(f"   - Lines of code: {metrics.get('lines_of_code', 0)}")
                print(f"   - Functions: {metrics.get('function_count', 0)}")
                print(f"   - Classes: {metrics.get('class_count', 0)}")
                print(f"   - Cyclomatic complexity: {metrics.get('cyclomatic_complexity', 0)}")
            
            # Show suggestions
            if analysis_result['suggestions']:
                print("   Improvement suggestions:")
                for suggestion in analysis_result['suggestions'][:2]:
                    print(f"   - {suggestion}")
        
        # Queue additional files for analysis
        print("\n3. Background Analysis Queue:")
        test_files = [
            "src/graph_sitter/core/symbol.py",
            "src/graph_sitter/core/function.py"
        ]
        
        for file_path in test_files:
            serena.queue_file_analysis(file_path)
            print(f"   Queued: {file_path}")
        
        # Wait a bit for background analysis
        print("   Waiting for background analysis...")
        time.sleep(2)
        
        # Get all analysis results
        print("\n4. Analysis Results Summary:")
        all_results = serena.get_analysis_results()
        print(f"   Total files analyzed: {len(all_results)}")
        
        for file_path, result in list(all_results.items())[:3]:
            print(f"   - {file_path}: {len(result['issues'])} issues, "
                  f"maintainability {result['maintainability_score']:.2f}")
        
        # Stop the analysis engine
        print("\n5. Stopping Analysis Engine:")
        serena.stop_analysis_engine()
        print("   ✅ Analysis engine stopped")
        
    except Exception as e:
        print(f"   Error: {e}")


def demo_lsp_integration(serena: SerenaCore):
    """Demonstrate LSP integration capabilities."""
    print("\n" + "="*60)
    print("🔌 LSP INTEGRATION & INTELLIGENCE")
    print("="*60)
    
    # Code completions
    print("\n1. Intelligent Code Completions:")
    try:
        completions = serena.get_completions("src/graph_sitter/core/codebase.py", 50, 10)
        print(f"   Found {len(completions)} completion suggestions:")
        for completion in completions[:5]:
            print(f"   - {completion.get('label', 'N/A')}: {completion.get('detail', 'No details')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Hover information
    print("\n2. Hover Information:")
    try:
        hover_info = serena.get_hover_info("src/graph_sitter/core/codebase.py", 100, 15)
        if hover_info:
            print(f"   Hover content: {hover_info.get('contents', 'No content')[:100]}...")
        else:
            print("   No hover information available")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Signature help
    print("\n3. Signature Help:")
    try:
        signature_help = serena.get_signature_help("src/graph_sitter/core/codebase.py", 120, 25)
        if signature_help:
            signatures = signature_help.get('signatures', [])
            print(f"   Found {len(signatures)} signature(s)")
            for sig in signatures[:2]:
                print(f"   - {sig.get('label', 'No label')}")
        else:
            print("   No signature help available")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Diagnostics
    print("\n4. Code Diagnostics:")
    try:
        diagnostics = serena.get_file_diagnostics("src/graph_sitter/core/codebase.py")
        print(f"   Found {len(diagnostics)} diagnostic(s):")
        for diag in diagnostics[:3]:
            print(f"   - {diag.severity}: {diag.message}")
            print(f"     Line {diag.line}, Column {diag.character}")
    except Exception as e:
        print(f"   Error: {e}")


def demo_performance_monitoring(serena: SerenaCore):
    """Demonstrate performance monitoring and status."""
    print("\n" + "="*60)
    print("📊 PERFORMANCE MONITORING")
    print("="*60)
    
    # Get comprehensive status
    print("\n1. System Status:")
    try:
        status = serena.get_status()
        print(f"   Enabled capabilities: {', '.join(status['enabled_capabilities'])}")
        print(f"   Active capabilities: {', '.join(status['active_capabilities'])}")
        print(f"   Background thread active: {status['background_thread_active']}")
        print(f"   Real-time analysis: {status['realtime_analysis']}")
        
        # Show capability details
        print("\n2. Capability Performance:")
        capability_details = status.get('capability_details', {})
        for cap_name, details in capability_details.items():
            if isinstance(details, dict) and 'performance' in details:
                perf = details['performance']
                print(f"   {cap_name.upper()}:")
                for operation, stats in perf.items():
                    if stats['count'] > 0:
                        print(f"   - {operation}: {stats['count']} calls, "
                              f"avg {stats['average_time']:.3f}s, "
                              f"cache hit rate {stats['cache_hit_rate']:.1%}")
    except Exception as e:
        print(f"   Error: {e}")


def main():
    """Main demo function."""
    print("🚀 ENHANCED SERENA CODEBASE KNOWLEDGE EXTENSION DEMO")
    print("Built on graph-sitter's powerful foundation")
    print("="*80)
    
    # Initialize codebase
    print("\n📁 Initializing codebase...")
    try:
        codebase = Codebase(".")
        print(f"   ✅ Loaded codebase from current directory")
        print(f"   📊 Found {len(codebase.files)} files")
        print(f"   🔍 Found {len(codebase.symbols)} symbols")
        print(f"   🏗️  {len(codebase.classes)} classes, {len(codebase.functions)} functions")
    except Exception as e:
        print(f"   ❌ Error loading codebase: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Configure Serena with all capabilities
    print("\n⚙️  Configuring Serena with enhanced capabilities...")
    config = SerenaConfig(
        enabled_capabilities=[
            SerenaCapability.INTELLIGENCE,
            SerenaCapability.REFACTORING,
            SerenaCapability.ANALYSIS,
            SerenaCapability.SEARCH,
            SerenaCapability.GENERATION
        ],
        realtime_analysis=True,
        cache_enabled=True,
        background_processing=True
    )
    
    # Initialize Serena
    try:
        with SerenaCore(codebase, config) as serena:
            print("   ✅ Serena initialized with enhanced capabilities")
            
            # Run all demos
            demo_enhanced_symbol_intelligence(serena)
            demo_advanced_refactoring(serena)
            demo_realtime_analysis(serena)
            demo_lsp_integration(serena)
            demo_performance_monitoring(serena)
            
            print("\n" + "="*80)
            print("🎉 DEMO COMPLETE!")
            print("Enhanced Serena provides comprehensive codebase knowledge extension")
            print("leveraging graph-sitter's existing powerful capabilities:")
            print("• Real-time symbol intelligence with cross-references")
            print("• Safe refactoring with conflict detection")
            print("• Continuous code quality analysis")
            print("• LSP integration for IDE-like features")
            print("• Semantic search and code generation")
            print("• Performance monitoring and caching")
            print("="*80)
            
    except Exception as e:
        print(f"   ❌ Error initializing Serena: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
