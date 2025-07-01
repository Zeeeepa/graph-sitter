#!/usr/bin/env python3
"""
Contexten Integration Example

This example demonstrates how the contexten module can leverage
the enhanced graph_sitter auto-analysis functionality for AI-powered
codebase analysis and visualization.

Features:
- Automatic analysis integration
- AI context generation
- Dashboard-based insights
- Error detection and blast radius analysis
- Simplified workflow for AI agents
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class GraphSitterContextenIntegration:
    """Integration class for contexten to use graph_sitter auto-analysis."""
    
    def __init__(self, project_path: str):
        """Initialize with automatic analysis."""
        self.project_path = project_path
        self.codebase = None
        self._initialize_analysis()
    
    def _initialize_analysis(self):
        """Initialize codebase with auto-analysis."""
        try:
            from graph_sitter import Codebase, Analysis
            
            print(f"🔍 Initializing auto-analysis for: {self.project_path}")
            
            # This automatically triggers comprehensive analysis
            self.codebase = Codebase.Analysis(self.project_path)
            
            if hasattr(self.codebase, 'analysis_result') and self.codebase.analysis_result:
                print("✅ Auto-analysis completed successfully!")
            else:
                print("⚠️ Auto-analysis not available")
                
        except Exception as e:
            print(f"❌ Failed to initialize analysis: {e}")
    
    def get_ai_context(self) -> Dict[str, Any]:
        """Get analysis data formatted for AI context."""
        if not self.codebase or not hasattr(self.codebase, 'analysis_result'):
            return {"error": "Analysis not available"}
        
        try:
            # Extract key information for AI processing
            context = {
                "project_path": self.project_path,
                "dashboard_url": getattr(self.codebase, 'dashboard_url', None),
                "analysis_available": True,
                "summary": {
                    "total_files": len(getattr(self.codebase, 'files', [])),
                    "analysis_timestamp": "2024-01-01 12:00:00",  # Would be actual timestamp
                    "health_score": "B+",  # Would be calculated from analysis
                },
                "issues": self._extract_issues(),
                "metrics": self._extract_metrics(),
                "recommendations": self._generate_recommendations()
            }
            
            return context
            
        except Exception as e:
            return {"error": f"Failed to extract AI context: {e}"}
    
    def _extract_issues(self) -> List[Dict[str, Any]]:
        """Extract issues from analysis for AI processing."""
        # Mock issues - would be extracted from actual analysis
        return [
            {
                "severity": "critical",
                "type": "Security Vulnerability",
                "message": "Potential SQL injection detected",
                "file": "src/services/user_service.py",
                "line": 45,
                "blast_radius_available": True
            },
            {
                "severity": "high", 
                "type": "Performance Issue",
                "message": "N+1 query pattern detected",
                "file": "src/models/post.py",
                "line": 123,
                "blast_radius_available": True
            },
            {
                "severity": "medium",
                "type": "Code Smell",
                "message": "Function complexity too high (CC: 15)",
                "file": "src/utils/data_processor.py", 
                "line": 78,
                "blast_radius_available": True
            }
        ]
    
    def _extract_metrics(self) -> Dict[str, Any]:
        """Extract metrics from analysis."""
        # Mock metrics - would be extracted from actual analysis
        return {
            "complexity_score": 7.2,
            "test_coverage": 78,
            "technical_debt_days": 2.3,
            "maintainability_grade": "B+",
            "dependencies_count": 42,
            "dead_code_percentage": 5
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate AI-friendly recommendations."""
        return [
            "Fix critical security vulnerability in user_service.py",
            "Optimize database queries to reduce N+1 patterns",
            "Refactor complex functions to improve maintainability",
            "Increase test coverage to reach 85% target",
            "Remove dead code to reduce technical debt"
        ]
    
    def get_dashboard_url(self) -> Optional[str]:
        """Get the URL to the interactive dashboard."""
        if self.codebase and hasattr(self.codebase, 'dashboard_url'):
            return self.codebase.dashboard_url
        return None
    
    def open_dashboard(self) -> bool:
        """Open the dashboard in browser."""
        if self.codebase and hasattr(self.codebase, 'open_dashboard'):
            return self.codebase.open_dashboard()
        return False
    
    def analyze_blast_radius(self, file_path: str, line_number: int) -> Dict[str, Any]:
        """Analyze blast radius for a specific issue."""
        # This would integrate with the dashboard's blast radius functionality
        return {
            "target": f"{file_path}:{line_number}",
            "impact_score": "Medium (7/10)",
            "affected_files": 15,
            "affected_functions": 23,
            "test_coverage": 85,
            "visualization_url": f"{self.get_dashboard_url()}#blast-radius-{file_path}-{line_number}"
        }
    
    def get_issue_summary_for_ai(self) -> str:
        """Get a text summary of issues for AI processing."""
        issues = self._extract_issues()
        
        summary_parts = []
        summary_parts.append(f"Found {len(issues)} issues in the codebase:")
        
        for issue in issues:
            summary_parts.append(
                f"- {issue['severity'].upper()}: {issue['message']} "
                f"in {issue['file']}:{issue['line']}"
            )
        
        summary_parts.append(f"\nInteractive dashboard available at: {self.get_dashboard_url()}")
        
        return "\n".join(summary_parts)

class ContextenChatAgent:
    """Example chat agent that uses graph_sitter analysis."""
    
    def __init__(self, project_path: str):
        self.integration = GraphSitterContextenIntegration(project_path)
    
    def handle_analysis_request(self, user_message: str) -> str:
        """Handle user requests for codebase analysis."""
        if "analyze" in user_message.lower() or "issues" in user_message.lower():
            return self._provide_analysis_summary()
        elif "dashboard" in user_message.lower():
            return self._provide_dashboard_info()
        elif "blast radius" in user_message.lower():
            return self._provide_blast_radius_info()
        else:
            return "I can help you analyze your codebase. Try asking about 'issues', 'dashboard', or 'blast radius'."
    
    def _provide_analysis_summary(self) -> str:
        """Provide analysis summary to user."""
        context = self.integration.get_ai_context()
        
        if "error" in context:
            return f"❌ Analysis not available: {context['error']}"
        
        summary = f"""
🔍 **Codebase Analysis Summary**

📊 **Overall Health:** {context['summary']['health_score']}
📁 **Files Analyzed:** {context['summary']['total_files']}

🚨 **Critical Issues Found:**
"""
        
        critical_issues = [issue for issue in context['issues'] if issue['severity'] == 'critical']
        for issue in critical_issues:
            summary += f"• {issue['message']} ({issue['file']}:{issue['line']})\n"
        
        summary += f"\n🎯 **Interactive Dashboard:** {context['dashboard_url']}"
        summary += "\n\n💡 Use the dashboard to explore visualizations and blast radius analysis!"
        
        return summary
    
    def _provide_dashboard_info(self) -> str:
        """Provide dashboard information."""
        dashboard_url = self.integration.get_dashboard_url()
        
        if not dashboard_url:
            return "❌ Dashboard not available. Analysis may have failed."
        
        return f"""
🎮 **Interactive Dashboard Available**

📊 **Dashboard URL:** {dashboard_url}

🎯 **Features:**
• Issue listings with severity categorization
• Interactive 'Visualize Codebase' button  
• Dropdown visualization selection:
  - Dependency Analysis
  - Blast Radius Analysis
  - Complexity Heatmap
  - Call Graph
  - Dead Code Analysis
• Target selection (functions, classes, files)
• Click-to-analyze blast radius from issues

💡 Click the dashboard link to explore your codebase interactively!
        """
    
    def _provide_blast_radius_info(self) -> str:
        """Provide blast radius analysis information."""
        return """
💥 **Blast Radius Analysis**

The dashboard provides interactive blast radius analysis that shows:
• Impact score for changes
• Affected files and functions  
• Test coverage for changes
• Visual representation of change propagation

🎯 **How to use:**
1. Open the dashboard
2. Click 'Visualize Codebase'
3. Select 'Blast Radius Analysis'
4. Choose a target (function, class, or file)
5. View the interactive visualization

💡 You can also click the 'Blast Radius' button next to any issue in the issues list!
        """

def demo_contexten_integration():
    """Demonstrate contexten integration with graph_sitter auto-analysis."""
    print("🤖 Contexten Integration Demo")
    print("=" * 50)
    
    # Initialize the integration
    integration = GraphSitterContextenIntegration(".")
    
    # Get AI context
    print("📊 Getting AI context...")
    context = integration.get_ai_context()
    
    if "error" not in context:
        print("✅ AI context generated successfully!")
        print(f"📁 Project: {context['project_path']}")
        print(f"🎯 Dashboard: {context['dashboard_url']}")
        print(f"📈 Health Score: {context['summary']['health_score']}")
        print(f"🔍 Issues Found: {len(context['issues'])}")
    else:
        print(f"❌ Error: {context['error']}")
    
    # Demo chat agent
    print("\n🤖 Chat Agent Demo")
    print("-" * 30)
    
    agent = ContextenChatAgent(".")
    
    # Simulate user interactions
    test_messages = [
        "Can you analyze my codebase?",
        "Show me the dashboard",
        "How does blast radius work?",
        "What issues did you find?"
    ]
    
    for message in test_messages:
        print(f"\n👤 User: {message}")
        response = agent.handle_analysis_request(message)
        print(f"🤖 Agent: {response}")

def main():
    """Run the contexten integration example."""
    print("🚀 Graph-Sitter + Contexten Integration Example")
    print("=" * 60)
    print("This example shows how contexten can leverage the enhanced")
    print("graph_sitter auto-analysis functionality for AI-powered")
    print("codebase analysis and interactive visualizations.")
    print("=" * 60)
    
    try:
        demo_contexten_integration()
        
        print("\n🎉 Integration Demo Complete!")
        print("=" * 50)
        print("Key Integration Benefits:")
        print("✅ Automatic analysis on codebase initialization")
        print("✅ AI-friendly context extraction")
        print("✅ Interactive dashboard generation")
        print("✅ Issue-focused insights")
        print("✅ Blast radius analysis")
        print("✅ Simplified workflow for AI agents")
        print("✅ Rich visualizations for user exploration")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        print("💡 This is expected if dependencies are missing")

if __name__ == "__main__":
    main()

