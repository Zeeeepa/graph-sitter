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

# Updated import to use the standardized format
from graph_sitter import codebase

logger = logging.getLogger(__name__)

@dataclass
class LinearConfig:
    """Configuration for Linear integration"""
    api_key: str
    team_id: str
    auto_create_issues: bool = True
    auto_assign_issues: bool = False
    sync_with_github: bool = True
    webhook_secret: Optional[str] = None


class LinearExtension:
    """Enhanced Linear extension with advanced issue management capabilities"""
    
    def __init__(self, config: LinearConfig, orchestrator=None):
        self.config = config
        self.orchestrator = orchestrator
        self.client = LinearClient(config.api_key)
        self.status = "initializing"
        
        # Advanced features
        self.issue_templates = {}
        self.auto_assignment_rules = {}
        self.workflow_automations = {}
        
    async def initialize(self):
        """Initialize the Linear extension"""
        
        logger.info("Initializing Linear extension...")
        
        # Load issue templates
        await self._load_issue_templates()
        
        # Setup auto-assignment rules
        await self._setup_auto_assignment_rules()
        
        # Setup workflow automations
        await self._setup_workflow_automations()
        
        self.status = "ready"
        logger.info("Linear extension initialized successfully")
    
    async def handle_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle various Linear tasks"""
        
        if self.status != "ready":
            await self.initialize()
        
        task_handlers = {
            'create_issue': self._create_issue,
            'update_issue': self._update_issue,
            'get_issue': self._get_issue,
            'list_issues': self._list_issues,
            'analyze_repository': self._analyze_repository,
            'sync_with_github': self._sync_with_github,
            'create_project': self._create_project,
            'manage_team': self._manage_team
        }
        
        if task_type not in task_handlers:
            raise ValueError(f"Unknown task type: {task_type}")
        
        try:
            result = await task_handlers[task_type](task_data)
            logger.info(f"Successfully completed task: {task_type}")
            return result
        except Exception as e:
            logger.error(f"Failed to complete task {task_type}: {e}")
            raise
    
    async def _create_issue(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Linear issue with advanced features"""
        
        title = task_data.get('title', 'Untitled Issue')
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
            issue_id = f"ISSUE-{int(asyncio.get_event_loop().time() * 1000)}"
            
            # Trigger workflow automations
            await self._trigger_workflow_automations('issue_created', {
                'issue_id': issue_id,
                'issue_data': issue_data
            })
            
            return {
                'issue_id': issue_id,
                'url': f"https://linear.app/team/issue/{issue_id}",
                'status': 'created',
                'assignee': assignee_email
            }
            
        except Exception as e:
            logger.error(f"Failed to create Linear issue: {e}")
            raise
    
    async def _analyze_repository(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repository and create issues for findings"""
        
        repository = task_data.get('repository')
        analysis_type = task_data.get('analysis_type', 'comprehensive')
        create_issues = task_data.get('create_issues', True)
        
        if not self.orchestrator.codebase:
            raise ValueError("No codebase loaded for analysis")
        
        # Perform analysis using graph_sitter with updated import
        analysis_result = {
            'repository': repository,
            'analysis_type': analysis_type,
            'summary': codebase.get_codebase_summary(self.orchestrator.codebase),
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
                    logger.error(f"Failed to create issue from analysis: {e}")
        
        return analysis_result
    
    async def _update_issue(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Linear issue"""
        # Implementation for updating issues
        pass
    
    async def _get_issue(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific Linear issue"""
        # Implementation for getting issues
        pass
    
    async def _list_issues(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """List Linear issues with filters"""
        # Implementation for listing issues
        pass
    
    async def _create_project(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Linear project"""
        # Implementation for creating projects
        pass
    
    async def _manage_team(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage team settings and members"""
        # Implementation for team management
        pass
    
    async def _sync_with_github(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync Linear issues with GitHub PRs and issues"""
        
        if not self.config.sync_with_github:
            return {'status': 'disabled', 'message': 'GitHub sync is disabled'}
        
        repository = task_data.get('repository')
        sync_type = task_data.get('sync_type', 'bidirectional')
        
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
                raise ValueError("GitHub extension not available")
            
            # Implementation for syncing with GitHub
            # This would include bidirectional sync logic
            
        except Exception as e:
            logger.error(f"GitHub sync failed: {e}")
            sync_results['errors'].append({'type': 'sync_error', 'error': str(e)})
        
        return sync_results
    
    async def _load_issue_templates(self):
        """Load issue templates for different types"""
        
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
        """Setup automatic assignment rules"""
        
        self.auto_assignment_rules = {
            'bug': ['developer1@example.com', 'developer2@example.com'],
            'feature': ['product@example.com', 'developer1@example.com'],
            'research': ['architect@example.com', 'researcher@example.com']
        }
    
    async def _setup_workflow_automations(self):
        """Setup workflow automations"""
        
        self.workflow_automations = {
            'issue_created': self._on_issue_created,
            'issue_updated': self._on_issue_updated,
            'issue_completed': self._on_issue_completed
        }
    
    async def _trigger_workflow_automations(self, event: str, data: Dict[str, Any]):
        """Trigger workflow automations for events"""
        
        if event in self.workflow_automations:
            try:
                await self.workflow_automations[event](data)
            except Exception as e:
                logger.error(f"Workflow automation error for {event}: {e}")
    
    async def _on_issue_created(self, data: Dict[str, Any]):
        """Handle issue created event"""
        
        # Notify Slack if enabled
        slack_ext = self.orchestrator.extensions.get('slack')
        if slack_ext:
            await slack_ext.handle_task('notify_issue_created', data)
    
    async def _on_issue_updated(self, data: Dict[str, Any]):
        """Handle issue updated event"""
        pass
    
    async def _on_issue_completed(self, data: Dict[str, Any]):
        """Handle issue completed event"""
        
        # Create PR if needed
        github_ext = self.orchestrator.extensions.get('github')
        if github_ext:
            await github_ext.handle_task('create_pr_for_issue', data)
    
    def _map_priority(self, priority: str) -> int:
        """Map priority string to Linear priority number"""
        
        priority_map = {
            'urgent': 1,
            'high': 2,
            'medium': 3,
            'low': 4,
            'none': 0
        }
        
        return priority_map.get(priority.lower(), 3)
    
    async def _get_auto_assignee(self, issue_type: str, labels: List[str]) -> Optional[str]:
        """Get automatic assignee based on issue type and labels"""
        
        if issue_type in self.auto_assignment_rules:
            assignees = self.auto_assignment_rules[issue_type]
            # Simple round-robin assignment
            import random
            return random.choice(assignees)
        
        return None
    
    async def _get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get Linear user ID by email"""
        # Mock implementation
        return f"user_{hash(email) % 1000}"
    
    async def _get_team_issues(self) -> List[Dict[str, Any]]:
        """Get all issues for the team"""
        # Mock implementation
        return []
    
    async def _generate_issues_from_analysis(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate issues based on codebase analysis"""
        
        issues = []
        
        # Example: Create issue for code quality improvements
        issues.append({
            'title': f"Code Quality Improvements for {analysis_result['repository']}",
            'description': f"Based on codebase analysis, the following improvements are recommended:\n\n{analysis_result['summary']}",
            'type': 'research',
            'priority': 'medium',
            'labels': ['code-quality', 'analysis-generated']
        })
        
        return issues
    
    async def cleanup(self):
        """Cleanup Linear extension"""
        
        self.status = "stopped"
        logger.info("Linear extension cleaned up")
    
    def get_status(self) -> Dict[str, Any]:
        """Get extension status"""
        
        return {
            'status': self.status,
            'team_id': self.config.team_id,
            'auto_create_issues': self.config.auto_create_issues,
            'auto_assign_issues': self.config.auto_assign_issues,
            'sync_with_github': self.config.sync_with_github
        }

