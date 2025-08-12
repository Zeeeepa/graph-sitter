
"""
Enhanced Analytics API Usage Example

This example shows how to use the enhanced analytics API with error detection.
"""

import asyncio
import json
from enhanced_analytics_api import SerenaErrorAnalyzer, RepoRequest

async def analyze_repository(repo_url: str):
    """Analyze a repository for both metrics and errors."""
    
    # Method 1: Direct error analysis
    print(f"🔍 Analyzing {repo_url} for errors...")
    analyzer = SerenaErrorAnalyzer()
    errors = await analyzer.analyze_codebase_errors(repo_url)
    
    print(f"Errors in Codebase [{len(errors)}]")
    for i, error in enumerate(errors[:10], 1):  # Show first 10 errors
        context = " | ".join(error.context_lines[:2]) if error.context_lines else "No context"
        print(f"{i}. {error.file_path} '{error.message}' '{error.severity.name}' '{error.category.value}' 'Line {error.line_number}' '{context}'")
    
    # Method 2: Using the API endpoints (if server is running)
    # This would be done via HTTP requests to the FastAPI server
    
    return errors

# Example usage
if __name__ == "__main__":
    # Analyze a sample repository
    repo_url = "octocat/Hello-World"  # Small test repository
    errors = asyncio.run(analyze_repository(repo_url))
    
    print(f"\n✅ Analysis complete! Found {len(errors)} total errors.")
