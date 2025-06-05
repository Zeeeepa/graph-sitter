#!/usr/bin/env python3
"""
Run the enhanced codebase analysis and capture results
"""

from graph_sitter.core.codebase import Codebase
from graph_sitter.configs.models.codebase import CodebaseConfig
from enhanced_codebase_analysis import EnhancedCodebaseAnalyzer

def main():
    """Run analysis and capture results"""
    print("🚀 Running Enhanced Codebase Analysis on graph-sitter repository...")
    print("=" * 80)
    
    try:
        # Initialize analyzer
        analyzer = EnhancedCodebaseAnalyzer("./")
        
        # Run analysis
        result = analyzer.analyze()
        
        # Print results
        analyzer.print_analysis_results(result)
        
        # Save results to file
        import json
        results_data = {
            'total_files': result.total_files,
            'total_functions': result.total_functions,
            'total_classes': result.total_classes,
            'total_imports': result.total_imports,
            'dead_code_items': result.dead_code_items,
            'issues': [
                {
                    'type': issue.type.value,
                    'severity': issue.severity,
                    'location': issue.location,
                    'range': issue.range,
                    'description': issue.description,
                    'suggestion': issue.suggestion,
                    'affected_symbols': issue.affected_symbols
                }
                for issue in result.issues
            ],
            'test_coverage': result.test_coverage,
            'complexity_metrics': result.complexity_metrics,
            'dependency_analysis': result.dependency_analysis,
            'inheritance_analysis': result.inheritance_analysis
        }
        
        with open('analysis_results.json', 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Results saved to analysis_results.json")
        print(f"📊 Summary: {len(result.issues)} issues found across {result.total_files} files")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

