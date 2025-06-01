#!/usr/bin/env python3
"""
Comprehensive Dashboard Analysis Example

This example demonstrates the enhanced codebase analysis system for dashboard views,
including issue detection, impact analysis, and hierarchical data generation.
"""

import asyncio
import json
from pathlib import Path

from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import (
    CodebaseAnalyzer,
    analyze_codebase,
    get_function_context,
    hop_through_imports,
    run_training_data_generation,
    IssueSeverity,
    IssueCategory
)


async def main():
    """Demonstrate comprehensive dashboard analysis functionality."""
    
    print("🔍 Dashboard Analysis Example")
    print("=" * 60)
    
    # Initialize codebase
    print("\n1. Initializing Codebase...")
    codebase = Codebase(".")
    
    print(f"✅ Loaded codebase with:")
    print(f"   📁 {len(list(codebase.files))} files")
    print(f"   🔧 {len(list(codebase.functions))} functions")
    print(f"   📦 {len(list(codebase.classes))} classes")
    
    # Create analyzer
    print("\n2. Creating Codebase Analyzer...")
    analyzer = CodebaseAnalyzer(codebase)
    
    # Detect issues
    print("\n3. Detecting Code Issues...")
    issues = analyzer.detect_issues()
    
    print(f"✅ Found {len(issues)} issues:")
    
    # Group issues by severity
    issues_by_severity = {}
    for severity in IssueSeverity:
        severity_issues = [i for i in issues if i.severity == severity]
        if severity_issues:
            issues_by_severity[severity] = severity_issues
            print(f"   🔴 {severity.value.upper()}: {len(severity_issues)} issues")
    
    # Group issues by category
    print("\n   Issues by category:")
    issues_by_category = {}
    for category in IssueCategory:
        category_issues = [i for i in issues if i.category == category]
        if category_issues:
            issues_by_category[category] = category_issues
            print(f"   📋 {category.value.replace('_', ' ').title()}: {len(category_issues)} issues")
    
    # Show sample issues
    print("\n4. Sample Issues Detected:")
    print("-" * 40)
    
    for i, issue in enumerate(issues[:5]):  # Show first 5 issues
        print(f"\n   Issue #{i+1}:")
        print(f"   📌 Title: {issue.title}")
        print(f"   📊 Severity: {issue.severity.value}")
        print(f"   📂 Category: {issue.category.value}")
        print(f"   📄 File: {issue.file_path}")
        print(f"   💡 Fix: {issue.suggested_fix[:100]}...")
        
        if issue.impact_score > 0:
            print(f"   ⚡ Impact Score: {issue.impact_score:.1f}")
    
    # Generate dashboard data
    print("\n5. Generating Dashboard Data Structure...")
    dashboard_data = analyzer.generate_dashboard_data()
    
    print(f"✅ Generated hierarchical data:")
    print(f"   🌳 Root node: {dashboard_data.name}")
    print(f"   📊 Summary: {dashboard_data.summary}")
    print(f"   🔗 Children: {len(dashboard_data.children)} categories")
    
    # Show dashboard structure
    print("\n   Dashboard Structure:")
    for child in dashboard_data.children:
        print(f"   ├── {child.name} ({child.type})")
        print(f"   │   ├── Issues: {len(child.issues)}")
        print(f"   │   └── Children: {len(child.children)}")
        
        # Show sub-children for files
        if child.type == "files" and child.children:
            for subchild in child.children[:3]:  # Show first 3 files
                print(f"   │       ├── {subchild.name}")
    
    # Function context analysis
    print("\n6. Function Context Analysis...")
    
    if codebase.functions:
        # Analyze first few functions
        sample_functions = list(codebase.functions)[:3]
        
        for func in sample_functions:
            print(f"\n   📋 Analyzing function: {func.name}")
            
            try:
                context = get_function_context(func)
                
                print(f"   ├── Dependencies: {len(context['dependencies'])}")
                print(f"   ├── Usages: {len(context['usages'])}")
                print(f"   ├── Call Sites: {len(context['call_sites'])}")
                print(f"   └── Function Calls: {len(context['function_calls'])}")
                
                # Show implementation details
                impl = context['implementation']
                print(f"   📄 Implementation:")
                print(f"      ├── File: {impl['filepath']}")
                print(f"      ├── Lines: {impl['line_start']}-{impl['line_end']}")
                print(f"      ├── Async: {impl['is_async']}")
                print(f"      └── Parameters: {len(impl['parameters'])}")
                
                # Show dependencies
                if context['dependencies']:
                    print(f"   🔗 Dependencies:")
                    for dep in context['dependencies'][:2]:  # Show first 2
                        print(f"      ├── {dep['name']} ({dep['type']})")
                
                # Show usages
                if context['usages']:
                    print(f"   📍 Usages:")
                    for usage in context['usages'][:2]:  # Show first 2
                        print(f"      ├── {usage['filepath']}:{usage['line_start']}")
                
            except Exception as e:
                print(f"   ❌ Error analyzing function: {e}")
    
    # Blast radius analysis
    print("\n7. Blast Radius Analysis...")
    
    if codebase.functions:
        sample_func = list(codebase.functions)[0]
        blast_radius = analyzer.get_blast_radius(sample_func.name, "Function")
        
        print(f"   🎯 Function: {sample_func.name}")
        print(f"   💥 Blast Radius: {len(blast_radius)} affected symbols")
        
        if blast_radius:
            print(f"   📊 Affected symbols:")
            for affected in blast_radius[:5]:  # Show first 5
                print(f"      ├── {affected}")
    
    # AI-powered analysis (if available)
    print("\n8. AI-Powered Analysis...")
    
    if hasattr(codebase, 'ai') and issues:
        try:
            # Analyze a high-severity issue with AI
            high_severity_issues = [i for i in issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]]
            
            if high_severity_issues:
                sample_issue = high_severity_issues[0]
                print(f"   🤖 Analyzing issue: {sample_issue.title}")
                
                ai_analysis = await analyzer.analyze_with_ai(sample_issue)
                print(f"   📝 AI Analysis: {ai_analysis[:200]}...")
            else:
                print("   ℹ️  No high-severity issues found for AI analysis")
        except Exception as e:
            print(f"   ⚠️  AI analysis not available: {e}")
    else:
        print("   ℹ️  AI analysis not configured")
    
    # Training data generation
    print("\n9. Training Data Generation...")
    
    training_data = run_training_data_generation(codebase)
    
    print(f"   📊 Training Data Generated:")
    print(f"   ├── Total Functions: {training_data['metadata']['total_functions']}")
    print(f"   ├── Processed: {training_data['metadata']['total_processed']}")
    print(f"   ├── Avg Dependencies: {training_data['metadata']['avg_dependencies']:.1f}")
    print(f"   └── Avg Usages: {training_data['metadata']['avg_usages']:.1f}")
    
    # Export dashboard data
    print("\n10. Exporting Dashboard Data...")
    
    # Convert to JSON for dashboard consumption
    dashboard_json = analyzer.to_json(dashboard_data)
    
    # Save to file
    output_file = Path("dashboard_analysis_output.json")
    with open(output_file, 'w') as f:
        f.write(dashboard_json)
    
    print(f"   ✅ Dashboard data exported to: {output_file}")
    print(f"   📊 JSON size: {len(dashboard_json)} characters")
    
    # Comprehensive analysis summary
    print("\n11. Comprehensive Analysis Summary...")
    
    comprehensive_analysis = analyze_codebase(codebase)
    
    print(f"   📈 Analysis Metrics:")
    print(f"   ├── Total Issues: {comprehensive_analysis['metrics']['total_issues']}")
    
    severity_breakdown = comprehensive_analysis['metrics']['issues_by_severity']
    for severity, count in severity_breakdown.items():
        if count > 0:
            print(f"   ├── {severity.upper()}: {count}")
    
    category_breakdown = comprehensive_analysis['metrics']['issues_by_category']
    print(f"   📋 Category Breakdown:")
    for category, count in category_breakdown.items():
        if count > 0:
            print(f"   ├── {category.replace('_', ' ').title()}: {count}")
    
    # Save comprehensive analysis
    analysis_file = Path("comprehensive_analysis.json")
    with open(analysis_file, 'w') as f:
        json.dump(comprehensive_analysis, f, indent=2, default=str)
    
    print(f"   ✅ Comprehensive analysis saved to: {analysis_file}")
    
    # Dashboard integration example
    print("\n12. Dashboard Integration Example...")
    print("-" * 50)
    
    print("""
   🌐 Dashboard Integration:
   
   The generated JSON structure is designed for React expandable components:
   
   ```javascript
   // Example React component structure
   const DashboardNode = ({ node }) => {
     const [expanded, setExpanded] = useState(false);
     
     return (
       <div className="analysis-node">
         <div onClick={() => setExpanded(!expanded)}>
           <h3>{node.name} ({node.type})</h3>
           <div className="summary">
             {Object.entries(node.summary).map(([key, value]) => (
               <span key={key}>{key}: {value}</span>
             ))}
           </div>
           {node.issues.length > 0 && (
             <div className="issues-badge">{node.issues.length} issues</div>
           )}
         </div>
         
         {expanded && (
           <div className="expanded-content">
             {node.issues.map(issue => (
               <IssueCard key={issue.id} issue={issue} />
             ))}
             {node.children.map(child => (
               <DashboardNode key={child.id} node={child} />
             ))}
           </div>
         )}
       </div>
     );
   };
   ```
   
   🔧 Key Features for Dashboard:
   ├── Hierarchical expandable structure
   ├── Issue categorization and severity
   ├── Impact analysis and blast radius
   ├── Function flow visualization data
   ├── AI-powered issue analysis
   └── Real-time context gathering
   """)
    
    print("\n🎉 Dashboard Analysis Complete!")
    print("\nFiles generated:")
    print(f"├── {output_file} - Dashboard JSON data")
    print(f"└── {analysis_file} - Comprehensive analysis")
    print("\nUse these files to populate your dashboard interface!")


def demonstrate_issue_flagging():
    """Demonstrate issue flagging functionality."""
    print("\n" + "="*60)
    print("🚩 Issue Flagging Demonstration")
    print("="*60)
    
    codebase = Codebase(".")
    
    # Example of manual issue flagging
    for function in list(codebase.functions)[:3]:
        try:
            # Check documentation
            if not getattr(function, 'docstring', None):
                print(f"🔴 Missing docstring: {function.name}")
                # In a real implementation, you'd call function.flag()
                
            # Check error handling for async functions
            if getattr(function, 'is_async', False):
                source = getattr(function, 'source', '')
                if 'try:' not in source and 'except' not in source:
                    print(f"🟡 Missing error handling: {function.name}")
                    
            # Check parameter count
            parameters = getattr(function, 'parameters', [])
            if len(parameters) > 7:
                print(f"🟠 Too many parameters: {function.name} ({len(parameters)} params)")
                
        except Exception as e:
            print(f"❌ Error analyzing {getattr(function, 'name', 'unknown')}: {e}")


if __name__ == "__main__":
    # Run main analysis
    asyncio.run(main())
    
    # Demonstrate issue flagging
    demonstrate_issue_flagging()

