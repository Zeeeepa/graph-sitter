#!/usr/bin/env python3
"""
Autonomous Failure Analyzer with Codegen SDK Integration

This script analyzes CI/CD failures and uses AI agents to automatically
diagnose issues and propose or implement fixes.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
from github import Github
from codegen import Agent
from .code_analysis_helper import CodeAnalysisHelper


@dataclass
class FailureAnalysis:
    """Analysis result for a CI/CD failure"""
    workflow_run_id: str
    failure_type: str
    root_cause: str
    suggested_fix: str
    confidence_score: float
    auto_fixable: bool
    affected_files: List[str]
    error_patterns: List[str]


class AutonomousFailureAnalyzer:
    """AI-powered failure analysis and auto-recovery system"""
    
    def __init__(self, codegen_org_id: str, codegen_token: str, github_token: str):
        self.codegen_agent = Agent(
            org_id=codegen_org_id,
            token=codegen_token
        )
        self.github = Github(github_token)
        self.repo = self.github.get_repo(os.environ.get('GITHUB_REPOSITORY', 'Zeeeepa/graph-sitter'))
        
        # Failure pattern database
        self.known_patterns = {
            'cython_compilation': {
                'patterns': ['error: Microsoft Visual C++', 'fatal error C1083', 'cython.*error'],
                'auto_fix': True,
                'fix_strategy': 'rebuild_cython_modules'
            },
            'dependency_conflict': {
                'patterns': ['VersionConflict', 'ResolutionImpossible', 'pip.*conflict'],
                'auto_fix': True,
                'fix_strategy': 'resolve_dependencies'
            },
            'test_timeout': {
                'patterns': ['timeout', 'SIGTERM', 'killed.*timeout'],
                'auto_fix': True,
                'fix_strategy': 'optimize_test_performance'
            },
            'flaky_test': {
                'patterns': ['AssertionError.*random', 'intermittent.*failure', 'race.*condition'],
                'auto_fix': False,
                'fix_strategy': 'quarantine_and_analyze'
            },
            'import_error': {
                'patterns': ['ImportError', 'ModuleNotFoundError', 'No module named'],
                'auto_fix': True,
                'fix_strategy': 'fix_imports'
            }
        }
    
    async def analyze_workflow_failure(self, workflow_run_id: str) -> FailureAnalysis:
        """Analyze a failed workflow run using AI"""
        
        print(f"🔍 Analyzing workflow run {workflow_run_id}...")
        
        # Get workflow run details
        workflow_run = self.repo.get_workflow_run(int(workflow_run_id))
        
        # Collect failure data
        failure_data = await self._collect_failure_data(workflow_run)
        
        # Use Codegen AI to analyze the failure
        analysis_prompt = self._build_analysis_prompt(failure_data)
        
        task = self.codegen_agent.run(prompt=analysis_prompt)
        
        # Wait for analysis completion
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(5)
            task.refresh()
        
        if task.status == 'failed':
            raise Exception(f"AI analysis failed: {task.result}")
        
        # Parse AI analysis result
        analysis = self._parse_ai_analysis(task.result, failure_data)
        
        print(f"✅ Analysis complete. Confidence: {analysis.confidence_score:.2f}")
        print(f"📋 Root cause: {analysis.root_cause}")
        print(f"🔧 Suggested fix: {analysis.suggested_fix}")
        
        return analysis
    
    async def _collect_failure_data(self, workflow_run) -> Dict[str, Any]:
        """Collect comprehensive failure data"""
        
        failure_data = {
            'workflow_name': workflow_run.name,
            'conclusion': workflow_run.conclusion,
            'created_at': workflow_run.created_at.isoformat(),
            'logs': [],
            'jobs': [],
            'recent_commits': [],
            'changed_files': []
        }
        
        # Get job logs
        for job in workflow_run.jobs():
            if job.conclusion == 'failure':
                job_data = {
                    'name': job.name,
                    'conclusion': job.conclusion,
                    'steps': []
                }
                
                for step in job.steps:
                    if step.conclusion == 'failure':
                        step_data = {
                            'name': step.name,
                            'conclusion': step.conclusion,
                            'number': step.number
                        }
                        job_data['steps'].append(step_data)
                
                failure_data['jobs'].append(job_data)
        
        # Get recent commits for context
        commits = list(self.repo.get_commits(since=datetime.now() - timedelta(days=1)))[:5]
        for commit in commits:
            commit_data = {
                'sha': commit.sha,
                'message': commit.commit.message,
                'author': commit.commit.author.name,
                'files': [f.filename for f in commit.files] if commit.files else []
            }
            failure_data['recent_commits'].append(commit_data)
        
        return failure_data
    
    def _build_analysis_prompt(self, failure_data: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for AI analysis"""
        
        prompt = f"""
Analyze this CI/CD failure and provide a structured diagnosis:

WORKFLOW FAILURE DETAILS:
- Workflow: {failure_data['workflow_name']}
- Conclusion: {failure_data['conclusion']}
- Time: {failure_data['created_at']}

FAILED JOBS:
{json.dumps(failure_data['jobs'], indent=2)}

RECENT COMMITS:
{json.dumps(failure_data['recent_commits'], indent=2)}

ANALYSIS REQUIRED:
1. Identify the root cause of the failure
2. Classify the failure type (compilation, test, dependency, infrastructure, etc.)
3. Assess if this is auto-fixable
4. Provide specific fix recommendations
5. Rate confidence level (0.0-1.0)
6. Identify affected files that need attention

Please respond in JSON format:
{{
    "failure_type": "string",
    "root_cause": "detailed explanation",
    "suggested_fix": "specific actionable steps",
    "confidence_score": 0.0-1.0,
    "auto_fixable": boolean,
    "affected_files": ["file1.py", "file2.py"],
    "error_patterns": ["pattern1", "pattern2"],
    "fix_priority": "low|medium|high|critical"
}}
"""
        return prompt
    
    def _parse_ai_analysis(self, ai_result: str, failure_data: Dict[str, Any]) -> FailureAnalysis:
        """Parse AI analysis result into structured format"""
        
        try:
            # Extract JSON from AI response
            import re
            json_match = re.search(r'\{.*\}', ai_result, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                # Fallback parsing
                analysis_data = {
                    "failure_type": "unknown",
                    "root_cause": "AI analysis parsing failed",
                    "suggested_fix": "Manual investigation required",
                    "confidence_score": 0.1,
                    "auto_fixable": False,
                    "affected_files": [],
                    "error_patterns": []
                }
        except json.JSONDecodeError:
            analysis_data = {
                "failure_type": "analysis_error",
                "root_cause": "Failed to parse AI analysis",
                "suggested_fix": "Review AI response manually",
                "confidence_score": 0.0,
                "auto_fixable": False,
                "affected_files": [],
                "error_patterns": []
            }
        
        return FailureAnalysis(
            workflow_run_id=failure_data.get('workflow_run_id', 'unknown'),
            failure_type=analysis_data.get('failure_type', 'unknown'),
            root_cause=analysis_data.get('root_cause', 'Unknown'),
            suggested_fix=analysis_data.get('suggested_fix', 'No fix suggested'),
            confidence_score=analysis_data.get('confidence_score', 0.0),
            auto_fixable=analysis_data.get('auto_fixable', False),
            affected_files=analysis_data.get('affected_files', []),
            error_patterns=analysis_data.get('error_patterns', [])
        )
    
    async def auto_fix_failure(self, analysis: FailureAnalysis) -> bool:
        """Attempt to automatically fix the failure"""
        
        if not analysis.auto_fixable or analysis.confidence_score < 0.7:
            print(f"❌ Auto-fix not recommended. Confidence: {analysis.confidence_score:.2f}")
            return False
        
        print(f"🔧 Attempting auto-fix for {analysis.failure_type}...")
        
        # Create fix prompt for Codegen AI
        fix_prompt = f"""
Implement a fix for this CI/CD failure:

FAILURE TYPE: {analysis.failure_type}
ROOT CAUSE: {analysis.root_cause}
SUGGESTED FIX: {analysis.suggested_fix}
AFFECTED FILES: {', '.join(analysis.affected_files)}

Please create a pull request with the necessary fixes. Focus on:
1. Fixing the immediate issue
2. Adding preventive measures
3. Improving error handling
4. Adding relevant tests

Create the PR with title: "🤖 Auto-fix: {analysis.failure_type}"
"""
        
        task = self.codegen_agent.run(prompt=fix_prompt)
        
        # Wait for fix completion
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(10)
            task.refresh()
            print(f"⏳ Fix in progress... Status: {task.status}")
        
        if task.status == 'completed':
            print(f"✅ Auto-fix completed: {task.result}")
            return True
        else:
            print(f"❌ Auto-fix failed: {task.result}")
            return False
    
    async def create_failure_report(self, analysis: FailureAnalysis) -> None:
        """Create a detailed failure report as a GitHub issue"""
        
        issue_title = f"🚨 CI/CD Failure Analysis: {analysis.failure_type}"
        
        issue_body = f"""
## Autonomous Failure Analysis Report

**Workflow Run ID:** {analysis.workflow_run_id}
**Failure Type:** {analysis.failure_type}
**Confidence Score:** {analysis.confidence_score:.2f}
**Auto-fixable:** {'✅ Yes' if analysis.auto_fixable else '❌ No'}

### Root Cause
{analysis.root_cause}

### Suggested Fix
{analysis.suggested_fix}

### Affected Files
{chr(10).join(f'- `{file}`' for file in analysis.affected_files)}

### Error Patterns Detected
{chr(10).join(f'- `{pattern}`' for pattern in analysis.error_patterns)}

### Next Steps
{'🤖 Auto-fix has been attempted' if analysis.auto_fixable else '👨‍💻 Manual intervention required'}

---
*This report was generated by the Autonomous CI/CD system*
"""
        
        # Create GitHub issue
        issue = self.repo.create_issue(
            title=issue_title,
            body=issue_body,
            labels=['ci-failure', 'autonomous-analysis', f'confidence-{int(analysis.confidence_score * 100)}']
        )
        
        print(f"📋 Failure report created: {issue.html_url}")
    
    async def _analyze_codebase_context(self, failure: FailureAnalysis) -> Dict[str, Any]:
        """Analyze codebase context for failure using standardized graph_sitter imports"""
        
        try:
            # Use the code analysis helper with proper graph_sitter imports
            analyzer = CodeAnalysisHelper(".")
            
            # Get comprehensive analysis to understand failure context
            analysis_result = analyzer.generate_comprehensive_report()
            
            # Extract relevant context for the failure
            context = {
                "codebase_health": analysis_result.get("analysis_results", {}).get("code_quality", {}),
                "potential_issues": analysis_result.get("analysis_results", {}).get("dead_code", {}),
                "dependency_problems": analysis_result.get("analysis_results", {}).get("dependencies", {}),
                "analysis_timestamp": analysis_result.get("timestamp")
            }
            
            return context
            
        except Exception as e:
            print(f"⚠️ Failed to analyze codebase context: {e}")
            return {"error": str(e)}


async def main():
    parser = argparse.ArgumentParser(description='Autonomous CI/CD Failure Analyzer')
    parser.add_argument('--workflow-run-id', required=True, help='GitHub workflow run ID')
    parser.add_argument('--mode', choices=['analyze', 'analyze-and-fix'], default='analyze')
    
    args = parser.parse_args()
    
    # Get environment variables
    codegen_org_id = os.environ.get('CODEGEN_ORG_ID')
    codegen_token = os.environ.get('CODEGEN_TOKEN')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    if not all([codegen_org_id, codegen_token, github_token]):
        print("❌ Missing required environment variables")
        sys.exit(1)
    
    # Initialize analyzer
    analyzer = AutonomousFailureAnalyzer(codegen_org_id, codegen_token, github_token)
    
    try:
        # Analyze the failure
        analysis = await analyzer.analyze_workflow_failure(args.workflow_run_id)
        
        # Create failure report
        await analyzer.create_failure_report(analysis)
        
        # Attempt auto-fix if requested
        if args.mode == 'analyze-and-fix':
            success = await analyzer.auto_fix_failure(analysis)
            if success:
                print("🎉 Auto-fix completed successfully!")
            else:
                print("⚠️ Auto-fix not possible, manual intervention required")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
