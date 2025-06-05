#!/usr/bin/env python3
"""
Example demonstrating the new Analysis feature in graph-sitter.

This example shows how to use the enhanced Analysis method that triggers
full-context analysis and generates comprehensive reports.
"""

from graph_sitter import Codebase
import os
import json

def main():
    print("🔍 Graph-Sitter Analysis Example")
    print("=" * 50)
    
    # Example 1: Analyze a local repository
    print("\n📁 Example 1: Analyzing a local repository")
    try:
        # Create a simple test codebase
        test_dir = "example_codebase"
        os.makedirs(test_dir, exist_ok=True)
        
        # Create a sample Python file
        with open(f"{test_dir}/sample.py", "w") as f:
            f.write('''
def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        if hasattr(item, 'price'):
            total += item.price
        else:
            print(f"Warning: {item} has no price attribute")
    return total

class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)
    
    def get_total(self):
        return calculate_total(self.items)
    
    def clear(self):
        self.items = []

def process_order(cart):
    """Process a shopping cart order."""
    if not cart.items:
        raise ValueError("Cannot process empty cart")
    
    total = cart.get_total()
    if total <= 0:
        raise ValueError("Invalid cart total")
    
    # Simulate payment processing
    print(f"Processing payment for ${total:.2f}")
    return {"status": "success", "total": total}
''')
        
        # Initialize codebase and run analysis
        print(f"📊 Analyzing codebase: {test_dir}")
        codebase = Codebase(test_dir)
        
        # Run comprehensive analysis
        print("🚀 Running comprehensive analysis...")
        result = codebase.Analysis(output_dir="analysis_results")
        
        print("✅ Analysis completed successfully!")
        print(f"📈 Analysis result type: {type(result)}")
        
        # Display results
        if os.path.exists("analysis_results"):
            files = os.listdir("analysis_results")
            print(f"📁 Generated files: {files}")
            
            # Show analysis summary
            if "enhanced_analysis.json" in files:
                with open("analysis_results/enhanced_analysis.json", "r") as f:
                    analysis_data = json.load(f)
                    
                print("\n📊 Analysis Summary:")
                print(f"  • Health Score: {analysis_data.get('health_score', 'N/A')}")
                print(f"  • Total Issues: {len(analysis_data.get('issues', []))}")
                print(f"  • Functions Analyzed: {len(analysis_data.get('function_analysis', {}).get('functions', []))}")
                print(f"  • Classes Found: {len(analysis_data.get('class_analysis', {}).get('classes', []))}")
                
                # Show recommendations
                recommendations = analysis_data.get('recommendations', [])
                if recommendations:
                    print(f"\n💡 Top Recommendations:")
                    for i, rec in enumerate(recommendations[:3], 1):
                        print(f"  {i}. {rec}")
        
        print(f"\n🌐 Analysis reports saved to: analysis_results/")
        
    except Exception as e:
        print(f"❌ Error in Example 1: {e}")
    
    # Example 2: Using the from_repo method (commented out as it requires network)
    print("\n📁 Example 2: Analyzing a remote repository (commented)")
    print("# To analyze a remote repository:")
    print("# codebase = Codebase.from_repo('fastapi/fastapi')")
    print("# result = codebase.Analysis(output_dir='fastapi_analysis')")
    
    # Example 3: Accessing analysis results
    print("\n📊 Example 3: Working with analysis results")
    try:
        if 'result' in locals():
            print("Analysis result attributes:")
            print(f"  • Enhanced Analysis: {hasattr(result, 'enhanced_analysis')}")
            print(f"  • Function Contexts: {hasattr(result, 'function_contexts')}")
            print(f"  • Export Paths: {hasattr(result, 'export_paths')}")
            
            if hasattr(result, 'export_paths'):
                print(f"\n📁 Export paths:")
                for name, path in result.export_paths.items():
                    print(f"  • {name.replace('_', ' ').title()}: {path}")
    
    except Exception as e:
        print(f"❌ Error in Example 3: {e}")
    
    print("\n✨ Analysis complete! Check the generated reports for detailed insights.")

if __name__ == "__main__":
    main()

