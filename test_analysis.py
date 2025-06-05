#!/usr/bin/env python3
"""
Test script to validate the enhanced codebase analysis system
"""

from graph_sitter.core.codebase import Codebase
from graph_sitter.configs.models.codebase import CodebaseConfig
from collections import Counter
import json

def test_basic_analysis():
    """Test basic analysis functionality"""
    print("🔍 Starting Basic Codebase Analysis Test...")
    print("=" * 60)
    
    try:
        # Initialize codebase with current directory
        print("📂 Initializing codebase...")
        codebase = Codebase("./")
        
        # Get basic metrics
        print("📊 Gathering basic metrics...")
        files = list(codebase.files)
        functions = list(codebase.functions)
        classes = list(codebase.classes)
        imports = list(codebase.imports)
        
        print(f"📚 Total Files: {len(files)}")
        print(f"⚡ Total Functions: {len(functions)}")
        print(f"🏗️  Total Classes: {len(classes)}")
        print(f"🔄 Total Imports: {len(imports)}")
        
        # Sample file analysis
        if files:
            print(f"\n📄 Sample Files:")
            for i, file in enumerate(files[:5]):
                print(f"   {i+1}. {file.filepath if hasattr(file, 'filepath') else str(file)}")
        
        # Sample function analysis
        if functions:
            print(f"\n⚡ Sample Functions:")
            for i, func in enumerate(functions[:5]):
                usages = len(func.usages) if hasattr(func, 'usages') else 'unknown'
                print(f"   {i+1}. {func.name} (usages: {usages})")
        
        # Dead code detection
        print(f"\n💀 Dead Code Analysis:")
        dead_functions = []
        for func in functions:
            if hasattr(func, 'usages') and len(func.usages) == 0 and not func.name.startswith('test_'):
                dead_functions.append(func.name)
        
        print(f"🗑️  Dead Functions Found: {len(dead_functions)}")
        if dead_functions:
            for i, func_name in enumerate(dead_functions[:3]):
                print(f"   {i+1}. {func_name}")
        
        # Test coverage analysis
        print(f"\n🧪 Test Coverage Analysis:")
        test_functions = [f for f in functions if f.name.startswith('test_')]
        test_classes = [c for c in classes if c.name.startswith('Test')]
        
        print(f"📝 Test Functions: {len(test_functions)}")
        print(f"🔬 Test Classes: {len(test_classes)}")
        
        if len(functions) > 0:
            coverage_ratio = len(test_functions) / len(functions)
            print(f"📈 Coverage Ratio: {coverage_ratio:.2%}")
        
        # Inheritance analysis
        print(f"\n🌳 Inheritance Analysis:")
        inheritance_classes = []
        for cls in classes:
            if hasattr(cls, 'superclasses') and len(cls.superclasses) > 0:
                inheritance_classes.append({
                    'name': cls.name,
                    'depth': len(cls.superclasses)
                })
        
        print(f"🏗️  Classes with Inheritance: {len(inheritance_classes)}")
        if inheritance_classes:
            deepest = max(inheritance_classes, key=lambda x: x['depth'])
            print(f"🌲 Deepest Inheritance: {deepest['name']} ({deepest['depth']} levels)")
        
        print(f"\n✅ Basic Analysis Complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_analysis()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")

