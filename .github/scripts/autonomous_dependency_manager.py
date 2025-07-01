#!/usr/bin/env python3
"""
Autonomous Dependency Manager with Codegen SDK Integration

This script intelligently manages dependencies, security updates, and compatibility
using AI agents to make informed decisions about updates and conflicts.
"""

import argparse
import asyncio
import json
import os
import sys
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

import requests
from github import Github
from codegen import Agent


@dataclass
class DependencyUpdate:
    """Represents a potential dependency update"""
    name: str
    current_version: str
    latest_version: str
    update_type: str  # major, minor, patch
    security_impact: str  # critical, high, medium, low, none
    compatibility_risk: str  # high, medium, low
    changelog_summary: str
    breaking_changes: List[str]
    recommended_action: str


class AutonomousDependencyManager:
    """AI-powered dependency management system"""
    
    def __init__(self, codegen_org_id: str, codegen_token: str, github_token: str):
        self.codegen_agent = Agent(
            org_id=codegen_org_id,
            token=codegen_token
        )
        self.github = Github(github_token)
        self.repo = self.github.get_repo(os.environ.get('GITHUB_REPOSITORY', 'Zeeeepa/graph-sitter'))
        
        # Security databases
        self.security_advisories = []
        self.compatibility_matrix = {}
    
    async def analyze_dependencies(self) -> List[DependencyUpdate]:
        """Analyze all dependencies for updates and security issues"""
        
        print("🔍 Analyzing dependencies...")
        
        # Get current dependencies
        dependencies = await self._get_current_dependencies()
        
        # Check for updates
        updates = []
        for dep_name, current_version in dependencies.items():
            update = await self._analyze_single_dependency(dep_name, current_version)
            if update:
                updates.append(update)
        
        # Use AI to prioritize and assess updates
        prioritized_updates = await self._ai_prioritize_updates(updates)
        
        return prioritized_updates
    
    async def _get_current_dependencies(self) -> Dict[str, str]:
        """Extract current dependencies from pyproject.toml and uv.lock"""
        
        dependencies = {}
        
        try:
            # Read pyproject.toml
            with open('pyproject.toml', 'r') as f:
                content = f.read()
                # Simple parsing - in production, use proper TOML parser
                import re
                deps = re.findall(r'"([^"]+)"\s*=\s*"([^"]+)"', content)
                for name, version in deps:
                    if not name.startswith('['):  # Skip section headers
                        dependencies[name] = version.replace('^', '').replace('~', '')
        
        except FileNotFoundError:
            print("⚠️ pyproject.toml not found")
        
        return dependencies
    
    async def _analyze_single_dependency(self, name: str, current_version: str) -> Optional[DependencyUpdate]:
        """Analyze a single dependency for updates"""
        
        try:
            # Get latest version from PyPI
            response = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            latest_version = data['info']['version']
            
            if current_version == latest_version:
                return None  # No update needed
            
            # Determine update type
            update_type = self._classify_update_type(current_version, latest_version)
            
            # Check security impact
            security_impact = await self._check_security_impact(name, current_version, latest_version)
            
            # Assess compatibility risk
            compatibility_risk = await self._assess_compatibility_risk(name, current_version, latest_version)
            
            # Get changelog summary
            changelog_summary = await self._get_changelog_summary(name, current_version, latest_version)
            
            return DependencyUpdate(
                name=name,
                current_version=current_version,
                latest_version=latest_version,
                update_type=update_type,
                security_impact=security_impact,
                compatibility_risk=compatibility_risk,
                changelog_summary=changelog_summary,
                breaking_changes=[],
                recommended_action="analyze"
            )
        
        except Exception as e:
            print(f"⚠️ Error analyzing {name}: {e}")
            return None
    
    def _classify_update_type(self, current: str, latest: str) -> str:
        """Classify update as major, minor, or patch"""
        
        try:
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            if len(current_parts) >= 1 and len(latest_parts) >= 1:
                if latest_parts[0] > current_parts[0]:
                    return "major"
                elif len(current_parts) >= 2 and len(latest_parts) >= 2 and latest_parts[1] > current_parts[1]:
                    return "minor"
                else:
                    return "patch"
        except (ValueError, IndexError):
            pass
        
        return "unknown"
    
    async def _check_security_impact(self, name: str, current: str, latest: str) -> str:
        """Check if update addresses security vulnerabilities"""
        
        try:
            # Check GitHub Security Advisories
            response = requests.get(
                f"https://api.github.com/advisories?ecosystem=pip&package={name}",
                timeout=10
            )
            
            if response.status_code == 200:
                advisories = response.json()
                for advisory in advisories:
                    if advisory.get('severity') in ['critical', 'high']:
                        return advisory['severity']
            
            # Use pip-audit for additional security checking
            try:
                result = subprocess.run(
                    ['pip-audit', '--format=json', '--requirement', '/dev/stdin'],
                    input=f"{name}=={current}",
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    audit_data = json.loads(result.stdout)
                    if audit_data.get('vulnerabilities'):
                        return 'high'
            except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
                pass
        
        except Exception:
            pass
        
        return "none"
    
    async def _assess_compatibility_risk(self, name: str, current: str, latest: str) -> str:
        """Assess compatibility risk of the update"""
        
        update_type = self._classify_update_type(current, latest)
        
        # Major updates have high risk
        if update_type == "major":
            return "high"
        elif update_type == "minor":
            return "medium"
        else:
            return "low"
    
    async def _get_changelog_summary(self, name: str, current: str, latest: str) -> str:
        """Get a summary of changes between versions"""
        
        try:
            # Try to get changelog from PyPI
            response = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                description = data['info'].get('description', '')
                if len(description) > 200:
                    description = description[:200] + "..."
                return description
        except Exception:
            pass
        
        return f"Update from {current} to {latest}"
    
    async def _ai_prioritize_updates(self, updates: List[DependencyUpdate]) -> List[DependencyUpdate]:
        """Use AI to prioritize and assess dependency updates"""
        
        if not updates:
            return []
        
        # Build comprehensive analysis prompt
        updates_data = []
        for update in updates:
            updates_data.append({
                'name': update.name,
                'current_version': update.current_version,
                'latest_version': update.latest_version,
                'update_type': update.update_type,
                'security_impact': update.security_impact,
                'compatibility_risk': update.compatibility_risk,
                'changelog_summary': update.changelog_summary
            })
        
        analysis_prompt = f"""
Analyze these dependency updates for a Python project (graph-sitter) and provide intelligent recommendations:

DEPENDENCY UPDATES:
{json.dumps(updates_data, indent=2)}

PROJECT CONTEXT:
- This is a critical code analysis library
- Stability is paramount
- Security updates are high priority
- Breaking changes need careful evaluation
- The project uses Cython extensions

For each dependency, provide:
1. Recommended action (update_immediately, update_with_testing, defer, skip)
2. Risk assessment (critical, high, medium, low)
3. Rationale for the recommendation
4. Any special considerations
5. Suggested testing strategy

Respond in JSON format:
{{
    "recommendations": [
        {{
            "name": "dependency_name",
            "action": "update_immediately|update_with_testing|defer|skip",
            "risk": "critical|high|medium|low",
            "rationale": "explanation",
            "considerations": ["item1", "item2"],
            "testing_strategy": "description"
        }}
    ],
    "overall_strategy": "description",
    "priority_order": ["dep1", "dep2", "dep3"]
}}
"""
        
        task = self.codegen_agent.run(prompt=analysis_prompt)
        
        # Wait for analysis
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(5)
            task.refresh()
        
        if task.status == 'failed':
            print(f"⚠️ AI analysis failed: {task.result}")
            return updates
        
        # Parse AI recommendations
        try:
            import re
            json_match = re.search(r'\{.*\}', task.result, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                
                # Apply AI recommendations to updates
                for update in updates:
                    for rec in recommendations.get('recommendations', []):
                        if rec['name'] == update.name:
                            update.recommended_action = rec['action']
                            break
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Failed to parse AI recommendations: {e}")
        
        return updates
    
    async def apply_updates(self, updates: List[DependencyUpdate], strategy: str = "smart") -> bool:
        """Apply dependency updates based on strategy"""
        
        print(f"🔧 Applying updates with strategy: {strategy}")
        
        # Filter updates based on strategy
        if strategy == "security-only":
            updates_to_apply = [u for u in updates if u.security_impact in ['critical', 'high']]
        elif strategy == "smart":
            updates_to_apply = [u for u in updates if u.recommended_action in ['update_immediately', 'update_with_testing']]
        else:
            updates_to_apply = updates
        
        if not updates_to_apply:
            print("✅ No updates to apply")
            return True
        
        # Create update prompt for Codegen AI
        update_prompt = f"""
Apply these dependency updates to the graph-sitter project:

UPDATES TO APPLY:
{json.dumps([{
    'name': u.name,
    'current': u.current_version,
    'latest': u.latest_version,
    'action': u.recommended_action,
    'security_impact': u.security_impact
} for u in updates_to_apply], indent=2)}

Please:
1. Update pyproject.toml with new versions
2. Run tests to ensure compatibility
3. Update uv.lock file
4. Create a PR with detailed changelog
5. Include any necessary code changes for compatibility

Create PR with title: "🤖 Autonomous dependency updates - {len(updates_to_apply)} packages"

Include in the PR description:
- Security fixes applied
- Compatibility testing results
- Any breaking changes handled
- Rollback instructions if needed
"""
        
        task = self.codegen_agent.run(prompt=update_prompt)
        
        # Wait for completion
        while task.status not in ['completed', 'failed']:
            await asyncio.sleep(10)
            task.refresh()
            print(f"⏳ Applying updates... Status: {task.status}")
        
        if task.status == 'completed':
            print(f"✅ Updates applied successfully: {task.result}")
            return True
        else:
            print(f"❌ Update failed: {task.result}")
            return False
    
    async def create_security_report(self, updates: List[DependencyUpdate]) -> None:
        """Create a security report for dependency vulnerabilities"""
        
        security_updates = [u for u in updates if u.security_impact in ['critical', 'high', 'medium']]
        
        if not security_updates:
            print("✅ No security vulnerabilities found")
            return
        
        issue_title = f"🔒 Security Alert: {len(security_updates)} dependency vulnerabilities found"
        
        issue_body = f"""
## Autonomous Security Analysis Report

**Scan Date:** {datetime.now().isoformat()}
**Vulnerabilities Found:** {len(security_updates)}

### Critical/High Priority Updates

"""
        
        for update in security_updates:
            if update.security_impact in ['critical', 'high']:
                issue_body += f"""
#### {update.name}
- **Current Version:** {update.current_version}
- **Latest Version:** {update.latest_version}
- **Security Impact:** {update.security_impact.upper()}
- **Recommended Action:** {update.recommended_action}
- **Summary:** {update.changelog_summary}

"""
        
        issue_body += """
### Recommended Actions
1. Review and approve high-priority security updates
2. Test updates in staging environment
3. Deploy security fixes as soon as possible
4. Monitor for any compatibility issues

---
*This report was generated by the Autonomous Dependency Manager*
"""
        
        # Create GitHub issue
        issue = self.repo.create_issue(
            title=issue_title,
            body=issue_body,
            labels=['security', 'dependencies', 'autonomous-analysis']
        )
        
        print(f"🔒 Security report created: {issue.html_url}")


async def main():
    parser = argparse.ArgumentParser(description='Autonomous Dependency Manager')
    parser.add_argument('--update-strategy', choices=['security-only', 'smart', 'all'], default='smart')
    parser.add_argument('--test-before-merge', type=bool, default=True)
    parser.add_argument('--security-priority', choices=['low', 'medium', 'high'], default='high')
    
    args = parser.parse_args()
    
    # Get environment variables
    codegen_org_id = os.environ.get('CODEGEN_ORG_ID')
    codegen_token = os.environ.get('CODEGEN_TOKEN')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    if not all([codegen_org_id, codegen_token, github_token]):
        print("❌ Missing required environment variables")
        sys.exit(1)
    
    # Initialize manager
    manager = AutonomousDependencyManager(codegen_org_id, codegen_token, github_token)
    
    try:
        # Analyze dependencies
        updates = await manager.analyze_dependencies()
        
        print(f"📊 Found {len(updates)} potential updates")
        
        # Create security report if needed
        await manager.create_security_report(updates)
        
        # Apply updates based on strategy
        if updates:
            success = await manager.apply_updates(updates, args.update_strategy)
            if success:
                print("🎉 Dependency updates completed successfully!")
            else:
                print("⚠️ Some updates failed, check logs for details")
        
    except Exception as e:
        print(f"❌ Dependency management failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

