"""
Enhanced Linear Extension with Advanced Issue Management

This module provides comprehensive Linear integration with advanced features
including automated issue management, team coordination, and repository analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os

try:
    from linear import LinearClient
except ImportError:
    # Mock for development
    class LinearClient:
        def __init__(self, api_key: str):
            self.api_key = api_key

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

@dataclass
class LinearConfig:
    """Configuration for Linear integration"""
    api_key: str
    team_id: str
    webhook_secret: Optional[str] = None
    auto_create_issues: bool = True
    auto_assign_issues: bool = True
    sync_with_github: bool = True

class EnhancedLinearExtension:
    """Enhanced Linear integration with advanced capabilities"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.config = self._load_config()
        self.client = None
        self.status = "initializing"
        
        # Issue management
        self.issue_templates = {}
        self.auto_assignment_rules = {}
        self.workflow_automations = {}
    
    def _load_config(self) -> LinearConfig:
        """Load Linear configuration from environment"""
        
        api_key = os.getenv('LINEAR_API_KEY')
        if not api_key:
            raise ValueError("LINEAR_API_KEY environment variable required")
        
        team_id = os.getenv('LINEAR_TEAM_ID')
        if not team_id:
            raise ValueError("LINEAR_TEAM_ID environment variable required")
        
        return LinearConfig(
            api_key=api_key,
            team_id=team_id,
            webhook_secret=os.getenv('LINEAR_WEBHOOK_SECRET'),
            auto_create_issues=os.getenv('LINEAR_AUTO_CREATE_ISSUES', 'true').lower() == 'true',
            auto_assign_issues=os.getenv('LINEAR_AUTO_ASSIGN_ISSUES', 'true').lower() == 'true',
            sync_with_github=os.getenv('LINEAR_SYNC_GITHUB', 'true').lower() == 'true'
        )
    
    async def initialize(self):
        """Initialize Linear client and setup"""
        
        try:
            self.client = LinearClient(self.config.api_key)
            
            # Load issue templates
            await self._load_issue_templates()
            
            # Setup auto-assignment rules
            await self._setup_auto_assignment_rules()
            
            # Setup workflow automations
            await self._setup_workflow_automations()
            
            self.status = "active"
            logger.info("Linear extension initialized successfully")
            
        except Exception as e:
            self.status = "error"
            logger.error(f"Failed to initialize Linear extension: {e}")
            raise
    
    async def handle_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Linear-specific tasks"""
        
        if self.status != "active":
            raise RuntimeError(f"Linear extension not active: {self.status}")
        
        if action == "create_issue":
            return await self._create_issue(task_data)
        
        elif action == "update_issue":
            return await self._update_issue(task_data)
        
        elif action == "analyze_repository":
            return await self._analyze_repository(task_data)
        
        elif action == "sync_with_github":
            return await self._sync_with_github(task_data)
        
        elif action == "auto_assign_issues":
            return await self._auto_assign_issues(task_data)
        
        elif action == "create_pr_from_issue":
            return await self._create_pr_from_issue(task_data)
        
        elif action == "get_team_metrics":
            return await self._get_team_metrics(task_data)
        
        else:
            raise ValueError(f"Unknown Linear action: {action}")
    
    async def _create_issue(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Linear issue with enhanced features"""
        
        title = task_data.get('title')
        description = task_data.get('description', '')
        issue_type = task_data.get('type', 'feature')
        priority = task_data.get('priority', 'medium')
        assignee_email = task_data.get('assignee_email')
        labels = task_data.get('labels', [])
        
        # Use issue template if available
        if issue_type in self.issue_templates:
            template = self.issue_templates[issue_type]
            description = template['description_template'].format(
                description=description,
                **task_data.get('template_vars', {})
            )
            labels.extend(template.get('default_labels', []))
        
        # Auto-assign if enabled and no assignee specified
        if self.config.auto_assign_issues and not assignee_email:
            assignee_email = await self._get_auto_assignee(issue_type, labels)
        
        try:
            # Create issue via Linear API (mock implementation)
            issue_data = {
                'title': title,
                'description': description,
                'teamId': self.config.team_id,
                'priority': self._map_priority(priority),
                'labels': labels
            }
            
            if assignee_email:
                # Get user ID from email
                user_id = await self._get_user_id_by_email(assignee_email)
                if user_id:
                    issue_data['assigneeId'] = user_id
            
            # Mock issue creation
            issue_id = f\"ISSUE-{int(asyncio.get_event_loop().time() * 1000)}\"
            
            # Trigger workflow automations
            await self._trigger_workflow_automations('issue_created', {
                'issue_id': issue_id,
                'issue_data': issue_data
            })
            
            return {
                'issue_id': issue_id,
                'url': f\"https://linear.app/team/issue/{issue_id}\",
                'status': 'created',
                'assignee': assignee_email
            }
            
        except Exception as e:
            logger.error(f\"Failed to create Linear issue: {e}\")
            raise
    
    async def _analyze_repository(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Analyze repository and create issues for findings\"\"\"
        
        repository = task_data.get('repository')
        analysis_type = task_data.get('analysis_type', 'comprehensive')
        create_issues = task_data.get('create_issues', True)
        
        if not self.orchestrator.codebase:
            raise ValueError(\"No codebase loaded for analysis\")
        
        # Perform analysis using graph_sitter
        from graph_sitter.codebase.codebase_analysis import get_codebase_summary
        
        analysis_result = {
            'repository': repository,
            'analysis_type': analysis_type,
            'summary': get_codebase_summary(self.orchestrator.codebase),
            'issues_created': []
        }
        
        if create_issues:
            # Create issues based on analysis findings
            issues_to_create = await self._generate_issues_from_analysis(analysis_result)
            
            for issue_data in issues_to_create:
                try:
                    created_issue = await self._create_issue(issue_data)
                    analysis_result['issues_created'].append(created_issue)
                except Exception as e:
                    logger.error(f\"Failed to create issue from analysis: {e}\")
        
        return analysis_result
    
    async def _sync_with_github(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Sync Linear issues with GitHub PRs and issues\"\"\"
        
        if not self.config.sync_with_github:
            return {'status': 'disabled', 'message': 'GitHub sync is disabled'}
        
        repository = task_data.get('repository')
        sync_type = task_data.get('sync_type', 'bidirectional')  # 'linear_to_github', 'github_to_linear', 'bidirectional'
        
        sync_results = {
            'repository': repository,
            'sync_type': sync_type,
            'synced_items': [],
            'errors': []
        }
        
        try:
            # Get GitHub extension
            github_ext = self.orchestrator.extensions.get('github')
            if not github_ext:
                raise ValueError(\"GitHub extension not available\")
            
            # Sync Linear issues to GitHub
            if sync_type in ['linear_to_github', 'bidirectional']:
                linear_issues = await self._get_team_issues()
                
                for issue in linear_issues:
                    try:
                        github_result = await github_ext.handle_task('create_issue_from_linear', {
                            'linear_issue': issue,
                            'repository': repository
                        })
                        sync_results['synced_items'].append({
                            'type': 'linear_to_github',
                            'linear_issue_id': issue['id'],
                            'github_issue_id': github_result.get('issue_id')
                        })
                    except Exception as e:
                        sync_results['errors'].append({
                            'type': 'linear_to_github',
                            'issue_id': issue['id'],
                            'error': str(e)
                        })
            
            # Sync GitHub issues to Linear
            if sync_type in ['github_to_linear', 'bidirectional']:
                github_issues = await github_ext.handle_task('get_repository_issues', {
                    'repository': repository
                })
                
                for issue in github_issues.get('issues', []):
                    try:
                        linear_result = await self._create_issue({
                            'title': issue['title'],
                            'description': f\"Synced from GitHub: {issue['html_url']}\
\
{issue['body']}\",
                            'type': 'bug' if 'bug' in issue.get('labels', []) else 'feature',
                            'labels': ['github-sync'] + issue.get('labels', [])
                        })
                        sync_results['synced_items'].append({
                            'type': 'github_to_linear',
                            'github_issue_id': issue['id'],
                            'linear_issue_id': linear_result.get('issue_id')
                        })
                    except Exception as e:
                        sync_results['errors'].append({
                            'type': 'github_to_linear',
                            'issue_id': issue['id'],
                            'error': str(e)
                        })
            
        except Exception as e:
            logger.error(f\"GitHub sync failed: {e}\")
            sync_results['errors'].append({'type': 'sync_error', 'error': str(e)})
        
        return sync_results
    
    async def _load_issue_templates(self):
        \"\"\"Load issue templates for different types\"\"\"
        
        self.issue_templates = {
            'bug': {
                'description_template': '''## Bug Report

**Description:**
{description}

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Behavior:**


**Actual Behavior:**


**Environment:**
- OS: 
- Browser: 
- Version: 
''',
                'default_labels': ['bug', 'needs-triage']
            },
            'feature': {
                'description_template': '''## Feature Request

**Description:**
{description}

**Use Case:**


**Acceptance Criteria:**
- [ ] 
- [ ] 
- [ ] 

**Additional Context:**

''',
                'default_labels': ['enhancement', 'needs-review']
            },
            'research': {
                'description_template': '''## Research Task

**Objective:**
{description}

**Research Questions:**
1. 
2. 
3. 

**Deliverables:**
- [ ] 
- [ ] 
- [ ] 

**Timeline:**

''',
                'default_labels': ['research', 'investigation']
            }
        }
    
    async def _setup_auto_assignment_rules(self):
        \"\"\"Setup automatic assignment rules\"\"\"
        
        self.auto_assignment_rules = {
            'bug': ['developer1@example.com', 'developer2@example.com'],
            'feature': ['product@example.com', 'developer1@example.com'],
            'research': ['architect@example.com', 'researcher@example.com']
        }
    
    async def _setup_workflow_automations(self):
        \"\"\"Setup workflow automations\"\"\"
        
        self.workflow_automations = {
            'issue_created': self._on_issue_created,
            'issue_updated': self._on_issue_updated,
            'issue_completed': self._on_issue_completed
        }
    
    async def _trigger_workflow_automations(self, event: str, data: Dict[str, Any]):
        \"\"\"Trigger workflow automations for events\"\"\"
        
        if event in self.workflow_automations:
            try:
                await self.workflow_automations[event](data)
            except Exception as e:
                logger.error(f\"Workflow automation error for {event}: {e}\")
    
    async def _on_issue_created(self, data: Dict[str, Any]):
        \"\"\"Handle issue created event\"\"\"
        
        # Notify Slack if enabled
        slack_ext = self.orchestrator.extensions.get('slack')
        if slack_ext:
            await slack_ext.handle_task('notify_issue_created', data)
    
    async def _on_issue_updated(self, data: Dict[str, Any]):
        \"\"\"Handle issue updated event\"\"\"
        pass
    
    async def _on_issue_completed(self, data: Dict[str, Any]):
        \"\"\"Handle issue completed event\"\"\"
        
        # Create PR if needed
        github_ext = self.orchestrator.extensions.get('github')
        if github_ext:
            await github_ext.handle_task('create_pr_for_issue', data)
    
    def _map_priority(self, priority: str) -> int:
        \"\"\"Map priority string to Linear priority number\"\"\"
        
        priority_map = {
            'urgent': 1,
            'high': 2,
            'medium': 3,
            'low': 4,
            'none': 0
        }
        
        return priority_map.get(priority.lower(), 3)
    
    async def _get_auto_assignee(self, issue_type: str, labels: List[str]) -> Optional[str]:
        \"\"\"Get automatic assignee based on issue type and labels\"\"\"
        
        if issue_type in self.auto_assignment_rules:
            assignees = self.auto_assignment_rules[issue_type]
            # Simple round-robin assignment
            import random
            return random.choice(assignees)
        
        return None
    
    async def _get_user_id_by_email(self, email: str) -> Optional[str]:
        \"\"\"Get Linear user ID by email\"\"\"
        # Mock implementation
        return f\"user_{hash(email) % 1000}\"
    
    async def _get_team_issues(self) -> List[Dict[str, Any]]:
        \"\"\"Get all issues for the team\"\"\"
        # Mock implementation
        return []
    
    async def _generate_issues_from_analysis(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        \"\"\"Generate issues based on codebase analysis\"\"\"
        
        issues = []
        
        # Example: Create issue for code quality improvements
        issues.append({
            'title': f\"Code Quality Improvements for {analysis_result['repository']}\",
            'description': f\"Based on codebase analysis, the following improvements are recommended:\
\
{analysis_result['summary']}\",
            'type': 'research',
            'priority': 'medium',
            'labels': ['code-quality', 'analysis-generated']
        })
        
        return issues
    
    async def cleanup(self):
        \"\"\"Cleanup Linear extension\"\"\"
        
        self.status = \"stopped\"
        logger.info(\"Linear extension cleaned up\")
    
    def get_status(self) -> Dict[str, Any]:
        \"\"\"Get extension status\"\"\"
        
        return {
            'status': self.status,
            'team_id': self.config.team_id,
            'auto_create_issues': self.config.auto_create_issues,
            'auto_assign_issues': self.config.auto_assign_issues,
            'sync_with_github': self.config.sync_with_github
        }

