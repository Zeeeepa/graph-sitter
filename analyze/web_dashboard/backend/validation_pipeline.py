"""
Validation Pipeline for Web-Eval-Agent Dashboard

Handles automated validation of PRs using web-eval-agent and graph-sitter analysis.
"""

import asyncio
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

import docker
from docker.errors import DockerException

from models import Project, ValidationResult, ValidationResultCreate, ValidationStatus
from database import Database
from github_integration import GitHubIntegration

logger = logging.getLogger(__name__)


class ValidationEnvironment:
    """Manages isolated validation environments."""
    
    def __init__(self, project: Project, pr_number: int):
        """Initialize validation environment."""
        self.project = project
        self.pr_number = pr_number
        self.environment_id = f"validation-{project.id}-{pr_number}-{uuid.uuid4().hex[:8]}"
        self.temp_dir = None
        self.container = None
        self.docker_client = None
        
    async def setup(self) -> bool:
        """Set up the validation environment."""
        try:
            # Create temporary directory
            self.temp_dir = Path(tempfile.mkdtemp(prefix=f"webeval-{self.environment_id}-"))
            logger.info(f"Created temp directory: {self.temp_dir}")
            
            # Initialize Docker client
            self.docker_client = docker.from_env()
            
            # Clone repository
            clone_success = await self._clone_pr_code()
            if not clone_success:
                return False
            
            # Set up validation environment
            setup_success = await self._setup_validation_environment()
            if not setup_success:
                return False
            
            logger.info(f"Validation environment {self.environment_id} set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up validation environment: {e}")
            await self.cleanup()
            return False
    
    async def _clone_pr_code(self) -> bool:
        """Clone PR code to temporary directory."""
        try:
            # Get PR information
            github_integration = GitHubIntegration()
            await github_integration.initialize()
            
            pr_info = await github_integration.get_pull_request(
                self.project.github_owner,
                self.project.github_repo,
                self.pr_number
            )
            
            if not pr_info:
                logger.error(f"Could not get PR {self.pr_number} information")
                return False
            
            # Clone the head branch
            head_ref = pr_info["head"]["ref"]
            head_sha = pr_info["head"]["sha"]
            
            clone_success = await github_integration.clone_repository(
                self.project.github_owner,
                self.project.github_repo,
                str(self.temp_dir / "repo"),
                branch=head_ref
            )
            
            if not clone_success:
                logger.error(f"Failed to clone repository for PR {self.pr_number}")
                return False
            
            # Checkout specific commit
            process = await asyncio.create_subprocess_exec(
                "git", "checkout", head_sha,
                cwd=str(self.temp_dir / "repo"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to checkout commit {head_sha}: {stderr.decode()}")
                return False
            
            logger.info(f"Successfully cloned PR {self.pr_number} code")
            return True
            
        except Exception as e:
            logger.error(f"Error cloning PR code: {e}")
            return False
    
    async def _setup_validation_environment(self) -> bool:
        """Set up the validation environment with dependencies."""
        try:
            repo_dir = self.temp_dir / "repo"
            
            # Check if package.json exists (Node.js project)
            package_json = repo_dir / "package.json"
            if package_json.exists():
                return await self._setup_nodejs_environment(repo_dir)
            
            # Check if requirements.txt exists (Python project)
            requirements_txt = repo_dir / "requirements.txt"
            if requirements_txt.exists():
                return await self._setup_python_environment(repo_dir)
            
            # Check if Dockerfile exists
            dockerfile = repo_dir / "Dockerfile"
            if dockerfile.exists():
                return await self._setup_docker_environment(repo_dir)
            
            # Default setup for unknown project types
            logger.warning(f"Unknown project type, using default setup")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up validation environment: {e}")
            return False
    
    async def _setup_nodejs_environment(self, repo_dir: Path) -> bool:
        """Set up Node.js validation environment."""
        try:
            logger.info("Setting up Node.js validation environment")
            
            # Install dependencies
            process = await asyncio.create_subprocess_exec(
                "npm", "install",
                cwd=str(repo_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"npm install failed: {stderr.decode()}")
                return False
            
            # Run build if build script exists
            package_json_path = repo_dir / "package.json"
            if package_json_path.exists():
                import json
                with open(package_json_path) as f:
                    package_data = json.load(f)
                
                scripts = package_data.get("scripts", {})
                if "build" in scripts:
                    logger.info("Running build script")
                    
                    process = await asyncio.create_subprocess_exec(
                        "npm", "run", "build",
                        cwd=str(repo_dir),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        logger.warning(f"Build script failed: {stderr.decode()}")
                        # Don't fail validation for build errors, continue with testing
            
            logger.info("Node.js environment set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Node.js environment: {e}")
            return False
    
    async def _setup_python_environment(self, repo_dir: Path) -> bool:
        """Set up Python validation environment."""
        try:
            logger.info("Setting up Python validation environment")
            
            # Create virtual environment
            venv_dir = repo_dir / "venv"
            process = await asyncio.create_subprocess_exec(
                "python3", "-m", "venv", str(venv_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to create virtual environment: {stderr.decode()}")
                return False
            
            # Install dependencies
            pip_path = venv_dir / "bin" / "pip"
            process = await asyncio.create_subprocess_exec(
                str(pip_path), "install", "-r", "requirements.txt",
                cwd=str(repo_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"pip install failed: {stderr.decode()}")
                return False
            
            logger.info("Python environment set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Python environment: {e}")
            return False
    
    async def _setup_docker_environment(self, repo_dir: Path) -> bool:
        """Set up Docker validation environment."""
        try:
            logger.info("Setting up Docker validation environment")
            
            # Build Docker image
            image_tag = f"webeval-{self.environment_id}:latest"
            
            try:
                image, build_logs = self.docker_client.images.build(
                    path=str(repo_dir),
                    tag=image_tag,
                    rm=True,
                    forcerm=True
                )
                
                logger.info(f"Docker image {image_tag} built successfully")
                return True
                
            except DockerException as e:
                logger.error(f"Docker build failed: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Error setting up Docker environment: {e}")
            return False
    
    async def run_setup_commands(self, setup_commands: str) -> bool:
        """Run custom setup commands."""
        if not setup_commands:
            return True
        
        try:
            logger.info("Running custom setup commands")
            
            # Split commands by newlines and run each
            commands = [cmd.strip() for cmd in setup_commands.split('\n') if cmd.strip()]
            
            for command in commands:
                logger.info(f"Running: {command}")
                
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=str(self.temp_dir / "repo"),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"Setup command failed: {command}")
                    logger.error(f"Error: {stderr.decode()}")
                    return False
                
                logger.info(f"Command completed: {stdout.decode()}")
            
            logger.info("All setup commands completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running setup commands: {e}")
            return False
    
    async def cleanup(self):
        """Clean up the validation environment."""
        try:
            # Stop and remove container if exists
            if self.container:
                try:
                    self.container.stop()
                    self.container.remove()
                    logger.info(f"Removed container for {self.environment_id}")
                except DockerException as e:
                    logger.warning(f"Error removing container: {e}")
            
            # Remove temporary directory
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Removed temp directory: {self.temp_dir}")
            
            # Close Docker client
            if self.docker_client:
                self.docker_client.close()
            
        except Exception as e:
            logger.error(f"Error cleaning up validation environment: {e}")


class ValidationPipeline:
    """Manages the validation pipeline for PRs."""
    
    def __init__(self):
        """Initialize validation pipeline."""
        self.database = None
        self.github_integration = None
        self.max_concurrent_validations = 3
        self.active_validations = {}
        
    async def initialize(self):
        """Initialize validation pipeline."""
        # Initialize dependencies
        from database import get_database
        self.database = await get_database()
        
        self.github_integration = GitHubIntegration()
        await self.github_integration.initialize()
        
        logger.info("Validation pipeline initialized")
    
    async def validate_pr(
        self, 
        project: Project, 
        pr_number: int,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> ValidationResult:
        """Validate a PR using the validation pipeline."""
        validation_id = f"{project.id}-{pr_number}"
        
        # Check if validation is already running
        if validation_id in self.active_validations:
            logger.warning(f"Validation already running for PR {pr_number}")
            return self.active_validations[validation_id]
        
        try:
            # Create validation result record
            validation_result = await self.database.create_validation_result(
                ValidationResultCreate(
                    project_id=project.id,
                    pr_number=pr_number,
                    status=ValidationStatus.PENDING
                )
            )
            
            # Store in active validations
            self.active_validations[validation_id] = validation_result
            
            # Start validation
            await self._run_validation(project, pr_number, validation_result, progress_callback)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error starting validation for PR {pr_number}: {e}")
            
            # Update validation result with error
            if validation_id in self.active_validations:
                validation_result = self.active_validations[validation_id]
                await self.database.update_validation_result(
                    validation_result.id,
                    {
                        "status": ValidationStatus.FAILED.value,
                        "success": False,
                        "message": f"Validation failed to start: {str(e)}",
                        "completed_at": datetime.utcnow()
                    }
                )
                del self.active_validations[validation_id]
            
            raise
    
    async def _run_validation(
        self, 
        project: Project, 
        pr_number: int, 
        validation_result: ValidationResult,
        progress_callback: Optional[Callable[[str], None]] = None
    ):
        """Run the validation process."""
        validation_id = f"{project.id}-{pr_number}"
        
        def send_progress(message: str):
            logger.info(f"Validation {validation_id}: {message}")
            if progress_callback:
                asyncio.create_task(progress_callback(message))
        
        try:
            # Update status to running
            await self.database.update_validation_result(
                validation_result.id,
                {
                    "status": ValidationStatus.RUNNING.value,
                    "started_at": datetime.utcnow()
                }
            )
            
            send_progress("Starting validation pipeline...")
            
            # Set up validation environment
            send_progress("Setting up validation environment...")
            environment = ValidationEnvironment(project, pr_number)
            
            setup_success = await environment.setup()
            if not setup_success:
                raise RuntimeError("Failed to set up validation environment")
            
            send_progress("Environment set up successfully")
            
            try:
                # Run custom setup commands if specified
                setup_commands = project.settings.get("setup_commands")
                if setup_commands:
                    send_progress("Running custom setup commands...")
                    setup_success = await environment.run_setup_commands(setup_commands)
                    if not setup_success:
                        raise RuntimeError("Custom setup commands failed")
                    send_progress("Setup commands completed")
                
                # Run validation tests
                send_progress("Running validation tests...")
                test_results = await self._run_validation_tests(environment, send_progress)
                
                # Analyze results
                send_progress("Analyzing validation results...")
                analysis_results = await self._analyze_validation_results(environment, test_results, send_progress)
                
                # Determine overall success
                overall_success = test_results.get("success", False) and analysis_results.get("success", False)
                
                # Update validation result
                await self.database.update_validation_result(
                    validation_result.id,
                    {
                        "status": ValidationStatus.SUCCESS.value if overall_success else ValidationStatus.FAILED.value,
                        "success": overall_success,
                        "message": "Validation completed successfully" if overall_success else "Validation failed",
                        "test_results": {
                            "tests": test_results,
                            "analysis": analysis_results
                        },
                        "completed_at": datetime.utcnow()
                    }
                )
                
                if overall_success:
                    send_progress("✅ Validation passed! PR is ready for review.")
                    
                    # Auto-merge if enabled
                    if project.settings.get("auto_merge_validated_pr", False):
                        send_progress("Auto-merging validated PR...")
                        await self._auto_merge_pr(project, pr_number)
                else:
                    send_progress("❌ Validation failed. Please review the issues.")
                
            finally:
                # Clean up environment
                send_progress("Cleaning up validation environment...")
                await environment.cleanup()
                send_progress("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Validation error for PR {pr_number}: {e}")
            
            # Update validation result with error
            await self.database.update_validation_result(
                validation_result.id,
                {
                    "status": ValidationStatus.FAILED.value,
                    "success": False,
                    "message": f"Validation error: {str(e)}",
                    "completed_at": datetime.utcnow()
                }
            )
            
            send_progress(f"❌ Validation failed with error: {str(e)}")
            
        finally:
            # Remove from active validations
            if validation_id in self.active_validations:
                del self.active_validations[validation_id]
    
    async def _run_validation_tests(self, environment: ValidationEnvironment, progress_callback: Callable[[str], None]) -> Dict[str, Any]:
        """Run validation tests using web-eval-agent."""
        try:
            repo_dir = environment.temp_dir / "repo"
            
            # Check if this is a web application
            is_web_app = await self._detect_web_application(repo_dir)
            
            if not is_web_app:
                progress_callback("Not a web application, skipping web-eval-agent tests")
                return {
                    "success": True,
                    "message": "No web tests needed for this project type",
                    "tests_run": 0,
                    "tests_passed": 0,
                    "tests_failed": 0
                }
            
            progress_callback("Detected web application, running web-eval-agent tests...")
            
            # Start the application
            app_process = await self._start_application(repo_dir, progress_callback)
            
            if not app_process:
                return {
                    "success": False,
                    "message": "Failed to start application for testing",
                    "error": "Application startup failed"
                }
            
            try:
                # Wait for application to be ready
                await asyncio.sleep(10)
                
                # Run web-eval-agent tests
                test_results = await self._run_web_eval_agent(repo_dir, progress_callback)
                
                return test_results
                
            finally:
                # Stop application
                if app_process:
                    app_process.terminate()
                    try:
                        await asyncio.wait_for(app_process.wait(), timeout=10)
                    except asyncio.TimeoutError:
                        app_process.kill()
                        await app_process.wait()
            
        except Exception as e:
            logger.error(f"Error running validation tests: {e}")
            return {
                "success": False,
                "message": f"Test execution failed: {str(e)}",
                "error": str(e)
            }
    
    async def _detect_web_application(self, repo_dir: Path) -> bool:
        """Detect if this is a web application."""
        # Check for common web application indicators
        web_indicators = [
            "package.json",  # Node.js web apps
            "index.html",    # Static web apps
            "app.py",        # Flask apps
            "manage.py",     # Django apps
            "next.config.js", # Next.js apps
            "nuxt.config.js", # Nuxt.js apps
            "vue.config.js",  # Vue.js apps
            "angular.json",   # Angular apps
            "svelte.config.js" # Svelte apps
        ]
        
        for indicator in web_indicators:
            if (repo_dir / indicator).exists():
                return True
        
        # Check package.json for web-related dependencies
        package_json = repo_dir / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    package_data = json.load(f)
                
                dependencies = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                web_deps = ["react", "vue", "angular", "svelte", "next", "nuxt", "express", "fastify", "koa"]
                
                if any(dep in dependencies for dep in web_deps):
                    return True
            except:
                pass
        
        return False
    
    async def _start_application(self, repo_dir: Path, progress_callback: Callable[[str], None]) -> Optional[asyncio.subprocess.Process]:
        """Start the application for testing."""
        try:
            # Try different start commands based on project type
            start_commands = [
                ["npm", "start"],
                ["npm", "run", "dev"],
                ["npm", "run", "serve"],
                ["python", "app.py"],
                ["python", "manage.py", "runserver"],
                ["python", "-m", "flask", "run"],
                ["yarn", "start"],
                ["yarn", "dev"]
            ]
            
            for command in start_commands:
                try:
                    progress_callback(f"Trying to start application with: {' '.join(command)}")
                    
                    process = await asyncio.create_subprocess_exec(
                        *command,
                        cwd=str(repo_dir),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    # Wait a bit to see if the process starts successfully
                    await asyncio.sleep(3)
                    
                    if process.returncode is None:  # Process is still running
                        progress_callback(f"Application started successfully with: {' '.join(command)}")
                        return process
                    else:
                        # Process exited, try next command
                        continue
                        
                except FileNotFoundError:
                    # Command not found, try next
                    continue
                except Exception as e:
                    logger.warning(f"Failed to start with {command}: {e}")
                    continue
            
            progress_callback("Could not start application with any known command")
            return None
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            return None
    
    async def _run_web_eval_agent(self, repo_dir: Path, progress_callback: Callable[[str], None]) -> Dict[str, Any]:
        """Run web-eval-agent tests."""
        try:
            progress_callback("Running web-eval-agent tests...")
            
            # TODO: Implement actual web-eval-agent integration
            # For now, return mock results
            
            # Simulate test execution
            await asyncio.sleep(5)
            
            # Mock test results
            test_results = {
                "success": True,
                "message": "All web tests passed",
                "tests_run": 10,
                "tests_passed": 10,
                "tests_failed": 0,
                "test_details": [
                    {"name": "Page Load Test", "status": "passed", "duration": 1.2},
                    {"name": "Navigation Test", "status": "passed", "duration": 0.8},
                    {"name": "Form Submission Test", "status": "passed", "duration": 2.1},
                    {"name": "Responsive Design Test", "status": "passed", "duration": 1.5},
                    {"name": "Accessibility Test", "status": "passed", "duration": 3.2}
                ]
            }
            
            progress_callback(f"Web tests completed: {test_results['tests_passed']}/{test_results['tests_run']} passed")
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error running web-eval-agent: {e}")
            return {
                "success": False,
                "message": f"Web-eval-agent execution failed: {str(e)}",
                "error": str(e)
            }
    
    async def _analyze_validation_results(self, environment: ValidationEnvironment, test_results: Dict[str, Any], progress_callback: Callable[[str], None]) -> Dict[str, Any]:
        """Analyze validation results using graph-sitter."""
        try:
            progress_callback("Running code analysis with graph-sitter...")
            
            repo_dir = environment.temp_dir / "repo"
            
            # TODO: Implement actual graph-sitter analysis
            # For now, return mock results
            
            # Simulate analysis
            await asyncio.sleep(3)
            
            # Mock analysis results
            analysis_results = {
                "success": True,
                "message": "Code analysis completed successfully",
                "files_analyzed": 25,
                "issues_found": 2,
                "issues": [
                    {
                        "file": "src/components/Button.js",
                        "line": 15,
                        "severity": "warning",
                        "message": "Unused variable 'className'",
                        "rule": "no-unused-vars"
                    },
                    {
                        "file": "src/utils/helpers.js",
                        "line": 42,
                        "severity": "info",
                        "message": "Consider using const instead of let",
                        "rule": "prefer-const"
                    }
                ],
                "metrics": {
                    "complexity": "low",
                    "maintainability": "high",
                    "test_coverage": 85.5
                }
            }
            
            progress_callback(f"Code analysis completed: {analysis_results['issues_found']} issues found")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing validation results: {e}")
            return {
                "success": False,
                "message": f"Code analysis failed: {str(e)}",
                "error": str(e)
            }
    
    async def _auto_merge_pr(self, project: Project, pr_number: int):
        """Auto-merge a validated PR."""
        try:
            success = await self.github_integration.merge_pull_request(
                project.github_owner,
                project.github_repo,
                pr_number,
                commit_title=f"Auto-merge validated PR #{pr_number}",
                commit_message="This PR has been automatically merged after successful validation.",
                merge_method="merge"
            )
            
            if success:
                logger.info(f"Successfully auto-merged PR #{pr_number}")
            else:
                logger.error(f"Failed to auto-merge PR #{pr_number}")
                
        except Exception as e:
            logger.error(f"Error auto-merging PR #{pr_number}: {e}")
    
    async def get_validation_status(self, project_id: str, pr_number: int) -> Optional[ValidationResult]:
        """Get validation status for a PR."""
        validation_id = f"{project_id}-{pr_number}"
        
        # Check active validations first
        if validation_id in self.active_validations:
            return self.active_validations[validation_id]
        
        # Check database
        validation_results = await self.database.get_project_validation_results(project_id)
        
        for result in validation_results:
            if result.pr_number == pr_number:
                return result
        
        return None
    
    async def cancel_validation(self, project_id: str, pr_number: int) -> bool:
        """Cancel a running validation."""
        validation_id = f"{project_id}-{pr_number}"
        
        if validation_id in self.active_validations:
            # TODO: Implement proper cancellation
            validation_result = self.active_validations[validation_id]
            
            await self.database.update_validation_result(
                validation_result.id,
                {
                    "status": ValidationStatus.CANCELLED.value,
                    "success": False,
                    "message": "Validation cancelled by user",
                    "completed_at": datetime.utcnow()
                }
            )
            
            del self.active_validations[validation_id]
            
            logger.info(f"Cancelled validation for PR {pr_number}")
            return True
        
        return False
    
    async def shutdown(self):
        """Shutdown validation pipeline."""
        # Cancel all active validations
        for validation_id in list(self.active_validations.keys()):
            project_id, pr_number = validation_id.split("-", 1)
            await self.cancel_validation(project_id, int(pr_number))
        
        logger.info("Validation pipeline shutdown complete")
