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
            template = self.issue_templates[issue_type]\n            description = template['description_template'].format(\n                description=description,\n                **task_data.get('template_vars', {})\n            )\n            labels.extend(template.get('default_labels', []))\n        \n        # Auto-assign if enabled and no assignee specified\n        if self.config.auto_assign_issues and not assignee_email:\n            assignee_email = await self._get_auto_assignee(issue_type, labels)\n        \n        try:\n            # Create issue via Linear API (mock implementation)\n            issue_data = {\n                'title': title,\n                'description': description,\n                'teamId': self.config.team_id,\n                'priority': self._map_priority(priority),\n                'labels': labels\n            }\n            \n            if assignee_email:\n                # Get user ID from email\n                user_id = await self._get_user_id_by_email(assignee_email)\n                if user_id:\n                    issue_data['assigneeId'] = user_id\n            \n            # Mock issue creation\n            issue_id = f\"ISSUE-{int(asyncio.get_event_loop().time() * 1000)}\"\n            \n            # Trigger workflow automations\n            await self._trigger_workflow_automations('issue_created', {\n                'issue_id': issue_id,\n                'issue_data': issue_data\n            })\n            \n            return {\n                'issue_id': issue_id,\n                'url': f\"https://linear.app/team/issue/{issue_id}\",\n                'status': 'created',\n                'assignee': assignee_email\n            }\n            \n        except Exception as e:\n            logger.error(f\"Failed to create Linear issue: {e}\")\n            raise\n    \n    async def _analyze_repository(self, task_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Analyze repository and create issues for findings\"\"\"\n        \n        repository = task_data.get('repository')\n        analysis_type = task_data.get('analysis_type', 'comprehensive')\n        create_issues = task_data.get('create_issues', True)\n        \n        if not self.orchestrator.codebase:\n            raise ValueError(\"No codebase loaded for analysis\")\n        \n        # Perform analysis using graph_sitter\n        from graph_sitter.codebase.codebase_analysis import get_codebase_summary\n        \n        analysis_result = {\n            'repository': repository,\n            'analysis_type': analysis_type,\n            'summary': get_codebase_summary(self.orchestrator.codebase),\n            'issues_created': []\n        }\n        \n        if create_issues:\n            # Create issues based on analysis findings\n            issues_to_create = await self._generate_issues_from_analysis(analysis_result)\n            \n            for issue_data in issues_to_create:\n                try:\n                    created_issue = await self._create_issue(issue_data)\n                    analysis_result['issues_created'].append(created_issue)\n                except Exception as e:\n                    logger.error(f\"Failed to create issue from analysis: {e}\")\n        \n        return analysis_result\n    \n    async def _sync_with_github(self, task_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Sync Linear issues with GitHub PRs and issues\"\"\"\n        \n        if not self.config.sync_with_github:\n            return {'status': 'disabled', 'message': 'GitHub sync is disabled'}\n        \n        repository = task_data.get('repository')\n        sync_type = task_data.get('sync_type', 'bidirectional')  # 'linear_to_github', 'github_to_linear', 'bidirectional'\n        \n        sync_results = {\n            'repository': repository,\n            'sync_type': sync_type,\n            'synced_items': [],\n            'errors': []\n        }\n        \n        try:\n            # Get GitHub extension\n            github_ext = self.orchestrator.extensions.get('github')\n            if not github_ext:\n                raise ValueError(\"GitHub extension not available\")\n            \n            # Sync Linear issues to GitHub\n            if sync_type in ['linear_to_github', 'bidirectional']:\n                linear_issues = await self._get_team_issues()\n                \n                for issue in linear_issues:\n                    try:\n                        github_result = await github_ext.handle_task('create_issue_from_linear', {\n                            'linear_issue': issue,\n                            'repository': repository\n                        })\n                        sync_results['synced_items'].append({\n                            'type': 'linear_to_github',\n                            'linear_issue_id': issue['id'],\n                            'github_issue_id': github_result.get('issue_id')\n                        })\n                    except Exception as e:\n                        sync_results['errors'].append({\n                            'type': 'linear_to_github',\n                            'issue_id': issue['id'],\n                            'error': str(e)\n                        })\n            \n            # Sync GitHub issues to Linear\n            if sync_type in ['github_to_linear', 'bidirectional']:\n                github_issues = await github_ext.handle_task('get_repository_issues', {\n                    'repository': repository\n                })\n                \n                for issue in github_issues.get('issues', []):\n                    try:\n                        linear_result = await self._create_issue({\n                            'title': issue['title'],\n                            'description': f\"Synced from GitHub: {issue['html_url']}\\n\\n{issue['body']}\",\n                            'type': 'bug' if 'bug' in issue.get('labels', []) else 'feature',\n                            'labels': ['github-sync'] + issue.get('labels', [])\n                        })\n                        sync_results['synced_items'].append({\n                            'type': 'github_to_linear',\n                            'github_issue_id': issue['id'],\n                            'linear_issue_id': linear_result.get('issue_id')\n                        })\n                    except Exception as e:\n                        sync_results['errors'].append({\n                            'type': 'github_to_linear',\n                            'issue_id': issue['id'],\n                            'error': str(e)\n                        })\n            \n        except Exception as e:\n            logger.error(f\"GitHub sync failed: {e}\")\n            sync_results['errors'].append({'type': 'sync_error', 'error': str(e)})\n        \n        return sync_results\n    \n    async def _load_issue_templates(self):\n        \"\"\"Load issue templates for different types\"\"\"\n        \n        self.issue_templates = {\n            'bug': {\n                'description_template': '''## Bug Report\n\n**Description:**\n{description}\n\n**Steps to Reproduce:**\n1. \n2. \n3. \n\n**Expected Behavior:**\n\n\n**Actual Behavior:**\n\n\n**Environment:**\n- OS: \n- Browser: \n- Version: \n''',\n                'default_labels': ['bug', 'needs-triage']\n            },\n            'feature': {\n                'description_template': '''## Feature Request\n\n**Description:**\n{description}\n\n**Use Case:**\n\n\n**Acceptance Criteria:**\n- [ ] \n- [ ] \n- [ ] \n\n**Additional Context:**\n\n''',\n                'default_labels': ['enhancement', 'needs-review']\n            },\n            'research': {\n                'description_template': '''## Research Task\n\n**Objective:**\n{description}\n\n**Research Questions:**\n1. \n2. \n3. \n\n**Deliverables:**\n- [ ] \n- [ ] \n- [ ] \n\n**Timeline:**\n\n''',\n                'default_labels': ['research', 'investigation']\n            }\n        }\n    \n    async def _setup_auto_assignment_rules(self):\n        \"\"\"Setup automatic assignment rules\"\"\"\n        \n        self.auto_assignment_rules = {\n            'bug': ['developer1@example.com', 'developer2@example.com'],\n            'feature': ['product@example.com', 'developer1@example.com'],\n            'research': ['architect@example.com', 'researcher@example.com']\n        }\n    \n    async def _setup_workflow_automations(self):\n        \"\"\"Setup workflow automations\"\"\"\n        \n        self.workflow_automations = {\n            'issue_created': self._on_issue_created,\n            'issue_updated': self._on_issue_updated,\n            'issue_completed': self._on_issue_completed\n        }\n    \n    async def _trigger_workflow_automations(self, event: str, data: Dict[str, Any]):\n        \"\"\"Trigger workflow automations for events\"\"\"\n        \n        if event in self.workflow_automations:\n            try:\n                await self.workflow_automations[event](data)\n            except Exception as e:\n                logger.error(f\"Workflow automation error for {event}: {e}\")\n    \n    async def _on_issue_created(self, data: Dict[str, Any]):\n        \"\"\"Handle issue created event\"\"\"\n        \n        # Notify Slack if enabled\n        slack_ext = self.orchestrator.extensions.get('slack')\n        if slack_ext:\n            await slack_ext.handle_task('notify_issue_created', data)\n    \n    async def _on_issue_updated(self, data: Dict[str, Any]):\n        \"\"\"Handle issue updated event\"\"\"\n        pass\n    \n    async def _on_issue_completed(self, data: Dict[str, Any]):\n        \"\"\"Handle issue completed event\"\"\"\n        \n        # Create PR if needed\n        github_ext = self.orchestrator.extensions.get('github')\n        if github_ext:\n            await github_ext.handle_task('create_pr_for_issue', data)\n    \n    def _map_priority(self, priority: str) -> int:\n        \"\"\"Map priority string to Linear priority number\"\"\"\n        \n        priority_map = {\n            'urgent': 1,\n            'high': 2,\n            'medium': 3,\n            'low': 4,\n            'none': 0\n        }\n        \n        return priority_map.get(priority.lower(), 3)\n    \n    async def _get_auto_assignee(self, issue_type: str, labels: List[str]) -> Optional[str]:\n        \"\"\"Get automatic assignee based on issue type and labels\"\"\"\n        \n        if issue_type in self.auto_assignment_rules:\n            assignees = self.auto_assignment_rules[issue_type]\n            # Simple round-robin assignment\n            import random\n            return random.choice(assignees)\n        \n        return None\n    \n    async def _get_user_id_by_email(self, email: str) -> Optional[str]:\n        \"\"\"Get Linear user ID by email\"\"\"\n        # Mock implementation\n        return f\"user_{hash(email) % 1000}\"\n    \n    async def _get_team_issues(self) -> List[Dict[str, Any]]:\n        \"\"\"Get all issues for the team\"\"\"\n        # Mock implementation\n        return []\n    \n    async def _generate_issues_from_analysis(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:\n        \"\"\"Generate issues based on codebase analysis\"\"\"\n        \n        issues = []\n        \n        # Example: Create issue for code quality improvements\n        issues.append({\n            'title': f\"Code Quality Improvements for {analysis_result['repository']}\",\n            'description': f\"Based on codebase analysis, the following improvements are recommended:\\n\\n{analysis_result['summary']}\",\n            'type': 'research',\n            'priority': 'medium',\n            'labels': ['code-quality', 'analysis-generated']\n        })\n        \n        return issues\n    \n    async def cleanup(self):\n        \"\"\"Cleanup Linear extension\"\"\"\n        \n        self.status = \"stopped\"\n        logger.info(\"Linear extension cleaned up\")\n    \n    def get_status(self) -> Dict[str, Any]:\n        \"\"\"Get extension status\"\"\"\n        \n        return {\n            'status': self.status,\n            'team_id': self.config.team_id,\n            'auto_create_issues': self.config.auto_create_issues,\n            'auto_assign_issues': self.config.auto_assign_issues,\n            'sync_with_github': self.config.sync_with_github\n        }

