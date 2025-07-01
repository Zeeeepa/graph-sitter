#!/usr/bin/env python3
"""
Integration Analysis and Repair Tool

This script analyzes and fixes the integration patterns between:
- GitHub extensions → Agents
- Linear extensions → Dashboard  
- Prefect extensions → Dashboard
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

def find_python_files(directory: str) -> List[str]:
    """Find all Python files in a directory"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(root, filename))
    return files

def analyze_imports(file_path: str) -> Tuple[Set[str], Set[str]]:
    """Analyze imports in a file, return (extensions_imports, tools_imports)"""
    extensions_imports = set()
    tools_imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find extension imports
        ext_patterns = [
            r'from\s+.*extensions\.(\w+)',
            r'import\s+.*extensions\.(\w+)',
        ]
        
        for pattern in ext_patterns:
            matches = re.findall(pattern, content)
            extensions_imports.update(matches)
            
        # Find tool imports  
        tool_patterns = [
            r'from\s+.*tools\.(\w+)',
            r'import\s+.*tools\.(\w+)',
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, content)
            tools_imports.update(matches)
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return extensions_imports, tools_imports

def analyze_integration_patterns():
    """Analyze current integration patterns"""
    
    print("🔍 Analyzing Integration Patterns...")
    
    # Analyze agents folder
    print("\n📁 AGENTS FOLDER ANALYSIS:")
    agent_files = find_python_files("src/contexten/agents")
    
    github_ext_in_agents = 0
    github_tools_in_agents = 0
    
    for file_path in agent_files:
        ext_imports, tool_imports = analyze_imports(file_path)
        
        if 'github' in ext_imports:
            github_ext_in_agents += 1
            print(f"   ✅ {file_path} uses GitHub extensions")
            
        if 'github' in tool_imports:
            github_tools_in_agents += 1
            
    print(f"   📊 GitHub Extensions in Agents: {github_ext_in_agents} files")
    print(f"   📊 GitHub Tools in Agents: {github_tools_in_agents} files")
    
    # Analyze dashboard folder
    print("\n📁 DASHBOARD FOLDER ANALYSIS:")
    dashboard_files = find_python_files("src/contexten/dashboard")
    
    linear_ext_in_dashboard = 0
    prefect_ext_in_dashboard = 0
    
    for file_path in dashboard_files:
        ext_imports, tool_imports = analyze_imports(file_path)
        
        if 'linear' in ext_imports:
            linear_ext_in_dashboard += 1
            print(f"   ✅ {file_path} uses Linear extensions")
            
        if 'prefect' in ext_imports:
            prefect_ext_in_dashboard += 1
            print(f"   ✅ {file_path} uses Prefect extensions")
            
    print(f"   📊 Linear Extensions in Dashboard: {linear_ext_in_dashboard} files")
    print(f"   📊 Prefect Extensions in Dashboard: {prefect_ext_in_dashboard} files")
    
    # Check available extensions
    print("\n📦 AVAILABLE EXTENSIONS:")
    
    github_ext_files = find_python_files("src/contexten/extensions/github")
    linear_ext_files = find_python_files("src/contexten/extensions/linear") 
    prefect_ext_files = find_python_files("src/contexten/extensions/prefect")
    
    print(f"   🐙 GitHub Extensions: {len(github_ext_files)} files")
    print(f"   📋 Linear Extensions: {len(linear_ext_files)} files") 
    print(f"   🔄 Prefect Extensions: {len(prefect_ext_files)} files")
    
    return {
        'github_ext_in_agents': github_ext_in_agents,
        'github_tools_in_agents': github_tools_in_agents,
        'linear_ext_in_dashboard': linear_ext_in_dashboard,
        'prefect_ext_in_dashboard': prefect_ext_in_dashboard,
        'available_github_ext': len(github_ext_files),
        'available_linear_ext': len(linear_ext_files),
        'available_prefect_ext': len(prefect_ext_files),
    }

def identify_missing_integrations(stats: Dict):
    """Identify missing integrations that need to be added"""
    
    print("\n🔧 MISSING INTEGRATIONS ANALYSIS:")
    
    missing = []
    
    # GitHub extensions should be used by agents
    if stats['available_github_ext'] > 0 and stats['github_ext_in_agents'] == 0:
        missing.append("❌ GitHub extensions not integrated with agents")
        
    # Linear extensions should be used by dashboard  
    if stats['available_linear_ext'] > 0 and stats['linear_ext_in_dashboard'] <= 2:
        missing.append("⚠️ Linear extensions minimally integrated with dashboard")
        
    # Prefect extensions should be used by dashboard
    if stats['available_prefect_ext'] > 0 and stats['prefect_ext_in_dashboard'] == 0:
        missing.append("❌ Prefect extensions not integrated with dashboard")
        
    if missing:
        print("   🚨 ISSUES FOUND:")
        for issue in missing:
            print(f"      {issue}")
    else:
        print("   ✅ All integrations appear to be working!")
        
    return missing

def suggest_integration_fixes(missing: List[str]):
    """Suggest specific fixes for missing integrations"""
    
    if not missing:
        return
        
    print("\n💡 SUGGESTED FIXES:")
    
    for issue in missing:
        if "GitHub extensions not integrated" in issue:
            print("""
   🐙 GitHub Extensions → Agents Integration:
      1. Add imports in agents/langchain/tools.py:
         from ...extensions.github.enhanced_agent import EnhancedGitHubAgent
         from ...extensions.github.github import GitHubClient
         
      2. Add imports in agents/tools/__init__.py:
         from ...extensions.github import *
         
      3. Update agent initialization to use enhanced GitHub features
      """)
            
        if "Linear extensions" in issue:
            print("""
   📋 Linear Extensions → Dashboard Integration:
      1. Add more imports in dashboard files:
         from ..extensions.linear.workflow.automation import LinearWorkflowAutomation
         from ..extensions.linear.webhook.processor import LinearWebhookProcessor
         
      2. Initialize Linear extensions in dashboard/app.py
      """)
            
        if "Prefect extensions not integrated" in issue:
            print("""
   🔄 Prefect Extensions → Dashboard Integration:
      1. Add imports in dashboard/app.py:
         from ..extensions.prefect.client import PrefectOrchestrator
         from ..extensions.prefect.workflows import WorkflowManager
         
      2. Initialize Prefect integration in dashboard
      """)

if __name__ == "__main__":
    print("🚀 Integration Analysis and Repair Tool")
    print("=" * 50)
    
    # We're already in the right directory
    
    # Run analysis
    stats = analyze_integration_patterns()
    missing = identify_missing_integrations(stats)
    suggest_integration_fixes(missing)
    
    print("\n" + "=" * 50)
    print("✅ Analysis complete!")
