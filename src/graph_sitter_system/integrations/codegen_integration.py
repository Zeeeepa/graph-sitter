"""
Codegen API Integration for Graph-Sitter System

Provides seamless integration with Codegen API for task management,
code generation, and analysis workflow automation.
"""

import logging
import time
from typing import Dict, List, Any, Optional
import requests
from dataclasses import dataclass
import json

from ..utils.config import CodegenConfig


@dataclass
class CodegenTask:
    """Represents a Codegen task"""
    id: str
    title: str
    description: str
    status: str
    priority: str
    assignee: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class AnalysisRequest:
    """Request for code analysis via Codegen"""
    repository_url: str
    branch: str = 'main'
    analysis_types: List[str] = None
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    metadata: Dict[str, Any] = None


class CodegenIntegration:
    """
    Integration with Codegen API for task management and analysis
    """
    
    def __init__(self, config: CodegenConfig):
        """
        Initialize Codegen integration
        
        Args:
            config: Codegen configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Setup authentication headers
        self.session.headers.update({
            'Authorization': f'Bearer {config.token}',
            'X-Organization-ID': config.org_id,
            'Content-Type': 'application/json',
            'User-Agent': 'Graph-Sitter-System/1.0.0'
        })
    
    def create_analysis_task(self, request: AnalysisRequest) -> Optional[CodegenTask]:
        """
        Create a new analysis task in Codegen
        
        Args:
            request: Analysis request details
            
        Returns:
            Created CodegenTask or None if failed
        """
        self.logger.info(f"Creating analysis task for {request.repository_url}")
        
        try:
            payload = {
                'title': f'Code Analysis: {request.repository_url}',
                'description': self._generate_analysis_description(request),
                'type': 'code_analysis',
                'priority': 'medium',
                'metadata': {
                    'repository_url': request.repository_url,
                    'branch': request.branch,
                    'analysis_types': request.analysis_types or ['complexity', 'dependencies', 'dead_code'],
                    'include_patterns': request.include_patterns or [],
                    'exclude_patterns': request.exclude_patterns or [],
                    'created_by': 'graph-sitter-system',
                    **(request.metadata or {})
                }
            }
            
            response = self.session.post(
                f"{self.config.api_url}/tasks",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 201:
                task_data = response.json()
                task = CodegenTask(
                    id=task_data['id'],
                    title=task_data['title'],
                    description=task_data['description'],
                    status=task_data['status'],
                    priority=task_data['priority'],
                    assignee=task_data.get('assignee'),
                    created_at=task_data.get('created_at'),
                    updated_at=task_data.get('updated_at'),
                    metadata=task_data.get('metadata', {})
                )
                
                self.logger.info(f"Created analysis task: {task.id}")
                return task
            else:
                self.logger.error(f"Failed to create task: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating analysis task: {str(e)}")
            return None
    
    def update_task_status(self, task_id: str, status: str, 
                          results: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update task status and results
        
        Args:
            task_id: Task identifier
            status: New status
            results: Optional analysis results
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating task {task_id} status to {status}")
        
        try:
            payload = {
                'status': status,
                'updated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
            
            if results:
                payload['metadata'] = {
                    'analysis_results': results,
                    'completed_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                }
            
            response = self.session.patch(
                f"{self.config.api_url}/tasks/{task_id}",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully updated task {task_id}")
                return True
            else:
                self.logger.error(f"Failed to update task: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating task status: {str(e)}")
            return False
    
    def get_task(self, task_id: str) -> Optional[CodegenTask]:
        """
        Get task details
        
        Args:
            task_id: Task identifier
            
        Returns:
            CodegenTask or None if not found
        """
        try:
            response = self.session.get(
                f"{self.config.api_url}/tasks/{task_id}",
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                task_data = response.json()
                return CodegenTask(
                    id=task_data['id'],
                    title=task_data['title'],
                    description=task_data['description'],
                    status=task_data['status'],
                    priority=task_data['priority'],
                    assignee=task_data.get('assignee'),
                    created_at=task_data.get('created_at'),
                    updated_at=task_data.get('updated_at'),
                    metadata=task_data.get('metadata', {})
                )
            else:
                self.logger.error(f"Failed to get task: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting task: {str(e)}")
            return None
    
    def list_tasks(self, status: Optional[str] = None, 
                   limit: int = 50) -> List[CodegenTask]:
        """
        List tasks with optional filtering
        
        Args:
            status: Optional status filter
            limit: Maximum number of tasks to return
            
        Returns:
            List of CodegenTask objects
        """
        try:
            params = {'limit': limit}
            if status:
                params['status'] = status
            
            response = self.session.get(
                f"{self.config.api_url}/tasks",
                params=params,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                tasks_data = response.json()
                tasks = []
                
                for task_data in tasks_data.get('tasks', []):
                    task = CodegenTask(
                        id=task_data['id'],
                        title=task_data['title'],
                        description=task_data['description'],
                        status=task_data['status'],
                        priority=task_data['priority'],
                        assignee=task_data.get('assignee'),
                        created_at=task_data.get('created_at'),
                        updated_at=task_data.get('updated_at'),
                        metadata=task_data.get('metadata', {})
                    )
                    tasks.append(task)
                
                return tasks
            else:
                self.logger.error(f"Failed to list tasks: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error listing tasks: {str(e)}")
            return []
    
    def submit_analysis_results(self, task_id: str, results: Dict[str, Any]) -> bool:
        """
        Submit analysis results for a task
        
        Args:
            task_id: Task identifier
            results: Analysis results
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Submitting analysis results for task {task_id}")
        
        try:
            # Format results for Codegen API
            formatted_results = self._format_analysis_results(results)
            
            payload = {
                'type': 'analysis_results',
                'data': formatted_results,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
            
            response = self.session.post(
                f"{self.config.api_url}/tasks/{task_id}/results",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"Successfully submitted results for task {task_id}")
                return True
            else:
                self.logger.error(f"Failed to submit results: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error submitting analysis results: {str(e)}")
            return False
    
    def create_code_generation_task(self, prompt: str, context: Dict[str, Any]) -> Optional[CodegenTask]:
        """
        Create a code generation task
        
        Args:
            prompt: Generation prompt
            context: Context information
            
        Returns:
            Created CodegenTask or None if failed
        """
        self.logger.info("Creating code generation task")
        
        try:
            payload = {
                'title': 'Code Generation Task',
                'description': prompt,
                'type': 'code_generation',
                'priority': 'medium',
                'metadata': {
                    'prompt': prompt,
                    'context': context,
                    'created_by': 'graph-sitter-system'
                }
            }
            
            response = self.session.post(
                f"{self.config.api_url}/tasks",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 201:
                task_data = response.json()
                return CodegenTask(
                    id=task_data['id'],
                    title=task_data['title'],
                    description=task_data['description'],
                    status=task_data['status'],
                    priority=task_data['priority'],
                    metadata=task_data.get('metadata', {})
                )
            else:
                self.logger.error(f"Failed to create generation task: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating generation task: {str(e)}")
            return None
    
    def get_organization_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get organization-level metrics
        
        Returns:
            Metrics dictionary or None if failed
        """
        try:
            response = self.session.get(
                f"{self.config.api_url}/organizations/{self.config.org_id}/metrics",
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get metrics: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting organization metrics: {str(e)}")
            return None
    
    def _generate_analysis_description(self, request: AnalysisRequest) -> str:
        """Generate task description for analysis request"""
        description = f"Automated code analysis for repository: {request.repository_url}\n\n"
        description += f"Branch: {request.branch}\n"
        
        if request.analysis_types:
            description += f"Analysis Types: {', '.join(request.analysis_types)}\n"
        
        if request.include_patterns:
            description += f"Include Patterns: {', '.join(request.include_patterns)}\n"
        
        if request.exclude_patterns:
            description += f"Exclude Patterns: {', '.join(request.exclude_patterns)}\n"
        
        description += "\nThis task will perform comprehensive code analysis including:\n"
        description += "- Complexity metrics calculation\n"
        description += "- Dependency graph construction\n"
        description += "- Dead code detection\n"
        description += "- Code quality assessment\n"
        description += "- Security vulnerability scanning\n"
        
        return description
    
    def _format_analysis_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format analysis results for Codegen API"""
        formatted = {
            'summary': {
                'files_analyzed': results.get('files_analyzed', 0),
                'symbols_found': results.get('symbols_found', 0),
                'dependencies_mapped': results.get('dependencies_mapped', 0),
                'dead_code_detected': results.get('dead_code_detected', 0),
                'complexity_score': results.get('complexity_score', 0),
                'maintainability_index': results.get('maintainability_index', 0),
                'analysis_duration': results.get('analysis_duration', 0)
            },
            'metrics': results.get('metrics', {}),
            'issues': results.get('issues', []),
            'recommendations': results.get('recommendations', []),
            'detailed_results': results.get('detailed_results', {})
        }
        
        return formatted
    
    def health_check(self) -> bool:
        """
        Check if Codegen API is accessible
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.config.api_url}/health",
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_rate_limit_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current rate limit status
        
        Returns:
            Rate limit information or None if failed
        """
        try:
            response = self.session.get(
                f"{self.config.api_url}/rate-limit",
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting rate limit status: {str(e)}")
            return None

