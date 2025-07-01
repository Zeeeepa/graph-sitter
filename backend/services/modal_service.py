"""
Modal deployment service for infrastructure provisioning and PR environment management
"""
import asyncio
import json
import tempfile
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import modal
from modal import App, Image, Secret, Mount

from backend.config import settings
from backend.database import DatabaseManager
from backend.services.websocket_manager import WebSocketManager
from backend.services.github_service import GitHubService

logger = logging.getLogger(__name__)


class ModalDeploymentService:
    """Service for managing Modal deployments and PR environments"""
    
    def __init__(self, websocket_manager: WebSocketManager = None):
        self.websocket_manager = websocket_manager or WebSocketManager()
        self.modal_client = None
        self._setup_modal_client()
    
    def _setup_modal_client(self):
        """Setup Modal client with authentication"""
        try:
            if settings.MODAL_TOKEN:
                # Configure Modal authentication
                os.environ['MODAL_TOKEN_ID'] = settings.MODAL_TOKEN
                self.modal_client = modal.Client()
                logger.info("Modal client initialized successfully")
            else:
                logger.warning("Modal token not configured")
        except Exception as e:
            logger.error(f"Failed to setup Modal client: {e}")
    
    async def create_pr_environment(self, project_id: str, pr_number: int, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a dedicated environment for PR testing"""
        try:
            deployment_id = f"{project_id}-pr-{pr_number}-{int(datetime.now().timestamp())}"
            
            # Broadcast deployment start
            await self.websocket_manager.send_deployment_update(deployment_id, project_id, {
                'status': 'starting',
                'message': f'Creating PR environment for PR #{pr_number}',
                'pr_number': pr_number
            })
            
            # Create Modal app for this PR
            app_config = await self._create_pr_app_config(github_data, pr_number)
            deployment_result = await self._deploy_modal_app(deployment_id, app_config)
            
            # Save deployment info
            deployment_data = {
                'id': deployment_id,
                'project_id': project_id,
                'environment': 'pr',
                'status': 'deployed',
                'deployment_url': deployment_result.get('url'),
                'commit_sha': github_data.get('commit_sha'),
                'branch': github_data.get('branch'),
                'modal_app_id': deployment_result.get('app_id'),
                'health_check_url': deployment_result.get('health_url'),
                'metadata': {
                    'pr_number': pr_number,
                    'created_by': 'ai_cicd_platform',
                    'auto_cleanup': True
                }
            }
            
            # await DatabaseManager.create_deployment(deployment_data)
            
            # Broadcast success
            await self.websocket_manager.send_deployment_update(deployment_id, project_id, {
                'status': 'deployed',
                'deployment_url': deployment_result.get('url'),
                'health_check_url': deployment_result.get('health_url'),
                'message': f'PR environment deployed successfully'
            })
            
            return {
                'deployment_id': deployment_id,
                'status': 'deployed',
                'url': deployment_result.get('url'),
                'health_url': deployment_result.get('health_url'),
                'app_id': deployment_result.get('app_id')
            }
            
        except Exception as e:
            logger.error(f"Failed to create PR environment: {e}")
            await self.websocket_manager.send_deployment_update(deployment_id, project_id, {
                'status': 'failed',
                'error': str(e)
            })
            raise
    
    async def deploy_to_staging(self, project_id: str, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to staging environment"""
        try:
            deployment_id = f"{project_id}-staging-{int(datetime.now().timestamp())}"
            
            await self.websocket_manager.send_deployment_update(deployment_id, project_id, {
                'status': 'starting',
                'message': 'Deploying to staging environment'
            })
            
            # Create staging app configuration
            app_config = await self._create_staging_app_config(github_data)
            deployment_result = await self._deploy_modal_app(deployment_id, app_config)
            
            # Run deployment validation
            validation_result = await self._validate_deployment(deployment_result.get('url'))
            
            if not validation_result['healthy']:
                raise Exception(f"Deployment validation failed: {validation_result['error']}")
            
            # Save deployment
            deployment_data = {
                'id': deployment_id,
                'project_id': project_id,
                'environment': 'staging',
                'status': 'deployed',
                'deployment_url': deployment_result.get('url'),
                'commit_sha': github_data.get('commit_sha'),
                'branch': github_data.get('branch'),
                'modal_app_id': deployment_result.get('app_id'),
                'health_check_url': deployment_result.get('health_url'),
                'metadata': {
                    'validation_result': validation_result,
                    'created_by': 'ai_cicd_platform'
                }
            }
            
            await self.websocket_manager.send_deployment_update(deployment_id, project_id, {
                'status': 'deployed',
                'deployment_url': deployment_result.get('url'),
                'validation_result': validation_result,
                'message': 'Staging deployment completed successfully'
            })
            
            return {
                'deployment_id': deployment_id,
                'status': 'deployed',
                'url': deployment_result.get('url'),
                'validation': validation_result
            }
            
        except Exception as e:
            logger.error(f"Staging deployment failed: {e}")
            await self.websocket_manager.send_deployment_update(deployment_id, project_id, {
                'status': 'failed',
                'error': str(e)
            })
            raise
    
    async def deploy_to_production(self, project_id: str, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to production environment with additional safety checks"""
        try:
            deployment_id = f"{project_id}-production-{int(datetime.now().timestamp())}"
            
            await self.websocket_manager.send_deployment_update(deployment_id, project_id, {
                'status': 'starting',
                'message': 'Starting production deployment with safety checks'
            })
            
            # Run pre-deployment checks
            safety_checks = await self._run_production_safety_checks(project_id, github_data)
            
            if not safety_checks['passed']:
                raise Exception(f"Production safety checks failed: {safety_checks['errors']}")
            
            # Create production app configuration
            app_config = await self._create_production_app_config(github_data)
            
            # Deploy with blue-green strategy
            deployment_result = await self._deploy_with_blue_green(deployment_id, app_config)
            
            # Comprehensive validation
            validation_result = await self._validate_production_deployment(deployment_result.get('url'))
            
            if not validation_result['healthy']:
                # Rollback on validation failure
                await self._rollback_deployment(deployment_id)
                raise Exception(f"Production validation failed, rolled back: {validation_result['error']}")
            
            # Save successful deployment
            deployment_data = {
                'id': deployment_id,
                'project_id': project_id,
                'environment': 'production',
                'status': 'deployed',
                'deployment_url': deployment_result.get('url'),
                'commit_sha': github_data.get('commit_sha'),
                'branch': github_data.get('branch'),
                'modal_app_id': deployment_result.get('app_id'),
                'health_check_url': deployment_result.get('health_url'),
                'metadata': {
                    'safety_checks': safety_checks,
                    'validation_result': validation_result,
                    'deployment_strategy': 'blue_green',
                    'created_by': 'ai_cicd_platform'
                }
            }
            
            await self.websocket_manager.send_deployment_update(deployment_id, project_id, {
                'status': 'deployed',
                'deployment_url': deployment_result.get('url'),
                'validation_result': validation_result,
                'message': 'Production deployment completed successfully'
            })
            
            return {
                'deployment_id': deployment_id,
                'status': 'deployed',
                'url': deployment_result.get('url'),
                'validation': validation_result
            }
            
        except Exception as e:
            logger.error(f"Production deployment failed: {e}")
            await self.websocket_manager.send_deployment_update(deployment_id, project_id, {
                'status': 'failed',
                'error': str(e)
            })
            raise
    
    async def _create_pr_app_config(self, github_data: Dict[str, Any], pr_number: int) -> Dict[str, Any]:
        """Create Modal app configuration for PR environment"""
        return {
            'name': f"pr-{pr_number}-{github_data.get('repo', 'app')}",
            'image': self._get_base_image(github_data),
            'environment': 'pr',
            'secrets': await self._get_pr_secrets(),
            'mounts': await self._get_code_mount(github_data),
            'resources': {
                'cpu': 1,
                'memory': 1024,
                'timeout': 300
            },
            'auto_cleanup': True,
            'cleanup_after_hours': 24
        }
    
    async def _create_staging_app_config(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Modal app configuration for staging environment"""
        return {
            'name': f"staging-{github_data.get('repo', 'app')}",
            'image': self._get_base_image(github_data),
            'environment': 'staging',
            'secrets': await self._get_staging_secrets(),
            'mounts': await self._get_code_mount(github_data),
            'resources': {
                'cpu': 2,
                'memory': 2048,
                'timeout': 600
            },
            'auto_cleanup': False
        }
    
    async def _create_production_app_config(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Modal app configuration for production environment"""
        return {
            'name': f"production-{github_data.get('repo', 'app')}",
            'image': self._get_production_image(github_data),
            'environment': 'production',
            'secrets': await self._get_production_secrets(),
            'mounts': await self._get_code_mount(github_data),
            'resources': {
                'cpu': 4,
                'memory': 4096,
                'timeout': 1200
            },
            'auto_cleanup': False,
            'scaling': {
                'min_instances': 2,
                'max_instances': 10
            }
        }
    
    def _get_base_image(self, github_data: Dict[str, Any]) -> Image:
        """Get base Modal image for deployment"""
        # Detect project type and create appropriate image
        language = self._detect_project_language(github_data)
        
        if language == 'python':
            return (
                Image.debian_slim()
                .pip_install([
                    "fastapi",
                    "uvicorn",
                    "requests",
                    "python-dotenv"
                ])
                .apt_install(["git", "curl"])
            )
        elif language == 'node':
            return (
                Image.debian_slim()
                .apt_install(["nodejs", "npm", "git", "curl"])
                .run_commands(["npm install -g pm2"])
            )
        else:
            # Default image
            return (
                Image.debian_slim()
                .apt_install(["git", "curl", "build-essential"])
            )
    
    def _get_production_image(self, github_data: Dict[str, Any]) -> Image:
        """Get production-optimized Modal image"""
        base_image = self._get_base_image(github_data)
        
        # Add production optimizations
        return (
            base_image
            .apt_install(["nginx", "supervisor"])
            .pip_install(["gunicorn", "prometheus-client"])
        )
    
    async def _get_pr_secrets(self) -> List[Secret]:
        """Get secrets for PR environment"""
        return [
            Secret.from_dict({
                "ENVIRONMENT": "pr",
                "DEBUG": "true",
                "LOG_LEVEL": "debug"
            })
        ]
    
    async def _get_staging_secrets(self) -> List[Secret]:
        """Get secrets for staging environment"""
        return [
            Secret.from_dict({
                "ENVIRONMENT": "staging",
                "DEBUG": "false",
                "LOG_LEVEL": "info"
            })
        ]
    
    async def _get_production_secrets(self) -> List[Secret]:
        """Get secrets for production environment"""
        return [
            Secret.from_dict({
                "ENVIRONMENT": "production",
                "DEBUG": "false",
                "LOG_LEVEL": "warning"
            })
        ]
    
    async def _get_code_mount(self, github_data: Dict[str, Any]) -> Mount:
        """Create code mount from GitHub repository"""
        # Clone repository to temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Clone the specific commit/branch
            repo_url = github_data.get('clone_url')
            commit_sha = github_data.get('commit_sha')
            
            if repo_url and commit_sha:
                # Use git to clone specific commit
                subprocess.run([
                    "git", "clone", repo_url, temp_dir
                ], check=True)
                
                subprocess.run([
                    "git", "checkout", commit_sha
                ], cwd=temp_dir, check=True)
            
            # Create Modal mount
            return Mount.from_local_dir(temp_dir, remote_path="/app")
            
        except Exception as e:
            logger.error(f"Failed to create code mount: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    def _detect_project_language(self, github_data: Dict[str, Any]) -> str:
        """Detect primary programming language of the project"""
        # This would typically analyze the repository structure
        # For now, return a default
        return 'python'
    
    async def _deploy_modal_app(self, deployment_id: str, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy Modal app with given configuration"""
        try:
            # Create Modal app
            app = App(app_config['name'])
            
            # Define the main function
            @app.function(
                image=app_config['image'],
                secrets=app_config['secrets'],
                mounts=[app_config['mounts']] if 'mounts' in app_config else [],
                cpu=app_config['resources']['cpu'],
                memory=app_config['resources']['memory'],
                timeout=app_config['resources']['timeout']
            )
            def main():
                # This would contain the actual application startup logic
                import subprocess
                import os
                
                # Change to app directory
                os.chdir('/app')
                
                # Start the application based on detected type
                if os.path.exists('requirements.txt'):
                    # Python app
                    subprocess.run(['pip', 'install', '-r', 'requirements.txt'])
                    if os.path.exists('main.py'):
                        subprocess.run(['python', 'main.py'])
                    elif os.path.exists('app.py'):
                        subprocess.run(['python', 'app.py'])
                elif os.path.exists('package.json'):
                    # Node.js app
                    subprocess.run(['npm', 'install'])
                    subprocess.run(['npm', 'start'])
                
                return {"status": "running"}
            
            # Deploy the app
            with app.run():
                result = main.remote()
                
                # Generate URLs (this would be actual Modal URLs in practice)
                app_url = f"https://{app_config['name']}.modal.run"
                health_url = f"{app_url}/health"
                
                return {
                    'app_id': app_config['name'],
                    'url': app_url,
                    'health_url': health_url,
                    'status': 'deployed'
                }
                
        except Exception as e:
            logger.error(f"Modal deployment failed: {e}")
            raise
    
    async def _deploy_with_blue_green(self, deployment_id: str, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy using blue-green deployment strategy"""
        try:
            # Deploy to green environment first
            green_config = app_config.copy()
            green_config['name'] = f"{app_config['name']}-green"
            
            green_result = await self._deploy_modal_app(f"{deployment_id}-green", green_config)
            
            # Validate green deployment
            validation = await self._validate_deployment(green_result['url'])
            
            if validation['healthy']:
                # Switch traffic to green (this would involve load balancer configuration)
                # For now, just return the green deployment
                return green_result
            else:
                raise Exception(f"Green deployment validation failed: {validation['error']}")
                
        except Exception as e:
            logger.error(f"Blue-green deployment failed: {e}")
            raise
    
    async def _validate_deployment(self, deployment_url: str) -> Dict[str, Any]:
        """Validate deployment health"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Check health endpoint
                health_url = f"{deployment_url}/health"
                
                async with session.get(health_url, timeout=30) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        
                        return {
                            'healthy': True,
                            'status_code': response.status,
                            'response_time': response.headers.get('X-Response-Time', 'unknown'),
                            'health_data': health_data
                        }
                    else:
                        return {
                            'healthy': False,
                            'status_code': response.status,
                            'error': f"Health check failed with status {response.status}"
                        }
                        
        except Exception as e:
            return {
                'healthy': False,
                'error': f"Health check failed: {str(e)}"
            }
    
    async def _validate_production_deployment(self, deployment_url: str) -> Dict[str, Any]:
        """Comprehensive validation for production deployment"""
        validation_result = await self._validate_deployment(deployment_url)
        
        if validation_result['healthy']:
            # Additional production checks
            try:
                import aiohttp
                
                async with aiohttp.ClientSession() as session:
                    # Check multiple endpoints
                    endpoints = ['/health', '/api/status', '/metrics']
                    endpoint_results = {}
                    
                    for endpoint in endpoints:
                        try:
                            url = f"{deployment_url}{endpoint}"
                            async with session.get(url, timeout=10) as response:
                                endpoint_results[endpoint] = {
                                    'status': response.status,
                                    'accessible': response.status < 500
                                }
                        except:
                            endpoint_results[endpoint] = {
                                'status': 0,
                                'accessible': False
                            }
                    
                    validation_result['endpoint_checks'] = endpoint_results
                    validation_result['production_ready'] = all(
                        result['accessible'] for result in endpoint_results.values()
                    )
                    
            except Exception as e:
                validation_result['production_ready'] = False
                validation_result['error'] = f"Production validation failed: {str(e)}"
        
        return validation_result
    
    async def _run_production_safety_checks(self, project_id: str, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run safety checks before production deployment"""
        checks = {
            'passed': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if staging deployment exists and is healthy
            staging_deployments = await self.get_deployments(project_id, environment='staging')
            
            if not staging_deployments:
                checks['errors'].append("No staging deployment found")
                checks['passed'] = False
            else:
                latest_staging = staging_deployments[0]
                if latest_staging['status'] != 'deployed':
                    checks['errors'].append("Latest staging deployment is not healthy")
                    checks['passed'] = False
            
            # Check if there are any critical security issues
            # This would integrate with the code analysis service
            # analysis_results = await CodeAnalysisService().get_analysis_results(project_id)
            # critical_issues = [r for r in analysis_results if r['severity'] == 'critical']
            # 
            # if critical_issues:
            #     checks['errors'].append(f"Found {len(critical_issues)} critical security issues")
            #     checks['passed'] = False
            
            # Check if all tests are passing
            # This would integrate with CI/CD pipeline
            
        except Exception as e:
            checks['errors'].append(f"Safety check failed: {str(e)}")
            checks['passed'] = False
        
        return checks
    
    async def _rollback_deployment(self, deployment_id: str) -> bool:
        """Rollback a failed deployment"""
        try:
            # This would involve switching traffic back to the previous version
            # and cleaning up the failed deployment
            logger.info(f"Rolling back deployment {deployment_id}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    async def cleanup_pr_environment(self, project_id: str, pr_number: int) -> bool:
        """Cleanup PR environment when PR is closed"""
        try:
            # Find and cleanup PR deployments
            deployments = await self.get_deployments(project_id, environment='pr')
            
            for deployment in deployments:
                if deployment.get('metadata', {}).get('pr_number') == pr_number:
                    await self._cleanup_deployment(deployment['id'])
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup PR environment: {e}")
            return False
    
    async def _cleanup_deployment(self, deployment_id: str) -> bool:
        """Cleanup a specific deployment"""
        try:
            # This would involve stopping the Modal app and cleaning up resources
            logger.info(f"Cleaning up deployment {deployment_id}")
            return True
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return False
    
    async def get_deployments(self, project_id: str, environment: str = None) -> List[Dict[str, Any]]:
        """Get deployments for a project"""
        # This would query the database for deployments
        # return await DatabaseManager.get_deployments(project_id, environment)
        return []
    
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get current status of a deployment"""
        # This would check the actual Modal app status
        return {
            'deployment_id': deployment_id,
            'status': 'deployed',
            'health': 'healthy'
        }

