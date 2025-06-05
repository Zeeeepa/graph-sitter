#!/usr/bin/env python3
"""
Simplified Analysis Example using Graph-Sitter's Built-in Capabilities

This example demonstrates the new, clean approach that leverages
Graph-Sitter's pre-computed relationships instead of complex analysis pipelines.
"""

from graph_sitter import Codebase
import os

def main():
    print("🚀 Simplified Graph-Sitter Analysis")
    print("=" * 40)
    
    # Create a test codebase
    test_dir = "simple_codebase"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create sample files
    with open(f"{test_dir}/main.py", "w") as f:
        f.write('''
def used_function():
    """This function is used."""
    return "Hello, World!"

def unused_function():
    """This function is never called."""
    return "Goodbye, World!"

class UsedClass:
    def method(self):
        return used_function()

class UnusedClass:
    def method(self):
        return "Never instantiated"

# Usage
obj = UsedClass()
result = obj.method()
print(result)
''')
    
    print(f"📁 Created test codebase: {test_dir}")
    
    # Initialize codebase - Graph-Sitter does all the heavy lifting
    print("🔍 Initializing codebase...")
    codebase = Codebase(test_dir)
    
    # Run simplified analysis using Graph-Sitter's built-in capabilities
    print("⚡ Running analysis (using Graph-Sitter's pre-computed data)...")
    result = codebase.Analysis(output_dir="simple_analysis")
    
    print("✅ Analysis completed!")
    
    # Display results
    print(f"\n📊 Analysis Results:")
    print(f"  • Health Score: {result.health_score:.2f}")
    print(f"  • Total Functions: {result.total_functions}")
    print(f"  • Total Classes: {result.total_classes}")
    print(f"  • Total Files: {result.total_files}")
    
    # Show dead code detection (using Graph-Sitter's usage tracking)
    if result.dead_code_items:
        print(f"\n🔍 Dead Code Found:")
        for item in result.dead_code_items:
            print(f"  • {item['type']}: {item['name']} ({item['reason']})")
    
    # Show issues
    if result.issues:
        print(f"\n⚠️  Issues:")
        for issue in result.issues:
            print(f"  • {issue['type']}: {issue['description']}")
    
    # Show recommendations
    if result.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in result.recommendations:
            print(f"  • {rec}")
    
    # Show generated files
    print(f"\n📁 Generated Files:")
    for name, path in result.export_paths.items():
        print(f"  • {name}: {path}")
    
    # Demonstrate Graph-Sitter's built-in capabilities directly
    print(f"\n🔧 Graph-Sitter Built-in Capabilities:")
    
    # Access functions directly
    functions = list(codebase.functions)
    print(f"  • Functions found: {len(functions)}")
    
    for func in functions:
        usage_count = len(func.usages) if func.usages else 0
        print(f"    - {func.name}: {usage_count} usages")
        
        # Show dependencies (Graph-Sitter pre-computes these)
        if hasattr(func, 'dependencies') and func.dependencies:
            deps = [dep.name for dep in func.dependencies]
            print(f"      Dependencies: {deps}")
    
    # Access classes directly
    classes = list(codebase.classes)
    print(f"  • Classes found: {len(classes)}")
    
    for cls in classes:
        usage_count = len(cls.usages) if cls.usages else 0
        print(f"    - {cls.name}: {usage_count} usages")
    
    print(f"\n🎯 Key Benefits of Simplified Approach:")
    print(f"  ✅ No complex analysis pipelines")
    print(f"  ✅ No serialization issues")
    print(f"  ✅ Instant results using pre-computed data")
    print(f"  ✅ Clean, maintainable code")
    print(f"  ✅ Leverages Graph-Sitter's proven capabilities")

if __name__ == "__main__":
    main()

