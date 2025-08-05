"""Requirements management service."""

import os
from datetime import datetime
from typing import Dict, List, Optional

from github import Github
from github.Repository import Repository

from ..models.requirements import Requirements, RequirementItem, RequirementsHistory, RequirementsTemplate
from ..utils.cache import CacheManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RequirementsService:
    """Service for managing project requirements."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize requirements service.
        
        Args:
            github_token: GitHub access token for repository access
        """
        self.github_token = github_token or os.getenv("GITHUB_ACCESS_TOKEN")
        if self.github_token:
            self.github = Github(self.github_token)
        else:
            self.github = None
            logger.warning("No GitHub token provided, repository operations will be limited")
            
        self.cache = CacheManager()
        
    async def get_requirements(self, project_id: str) -> Optional[Requirements]:
        """Get requirements for a project.
        
        Args:
            project_id: Project ID (repository full name)
            
        Returns:
            Requirements object or None if not found
        """
        cache_key = f"requirements_{project_id}"
        cached_requirements = await self.cache.get(cache_key)
        
        if cached_requirements:
            return cached_requirements
            
        if not self.github:
            return None
            
        try:
            repo = self.github.get_repo(project_id)
            
            # Try to find requirements file
            requirements_file = None
            for filename in ["REQUIREMENTS.md", "requirements.md", "Requirements.md"]:
                try:
                    requirements_file = repo.get_contents(filename)
                    break
                except Exception:
                    continue
                    
            if not requirements_file:
                return None
                
            # Parse requirements file content
            content = requirements_file.decoded_content.decode("utf-8")
            requirements = await self._parse_requirements_file(content, project_id)
            
            if requirements:
                requirements.file_path = requirements_file.path
                requirements.git_hash = requirements_file.sha
                
                # Cache for 5 minutes
                await self.cache.set(cache_key, requirements, ttl=300)
                
            return requirements
            
        except Exception as e:
            logger.error(f"Error fetching requirements for {project_id}: {e}")
            return None
    
    async def create_requirements(self, 
                                project_id: str,
                                requirements: Requirements,
                                commit_message: Optional[str] = None) -> bool:
        """Create requirements file for a project.
        
        Args:
            project_id: Project ID (repository full name)
            requirements: Requirements object to create
            commit_message: Git commit message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.github:
            logger.error("GitHub token required for creating requirements")
            return False
            
        try:
            repo = self.github.get_repo(project_id)
            
            # Generate requirements file content
            content = await self._generate_requirements_file(requirements)
            
            # Create or update file
            message = commit_message or f"Add requirements v{requirements.version}"
            
            try:
                # Try to get existing file
                existing_file = repo.get_contents(requirements.file_path)
                repo.update_file(
                    requirements.file_path,
                    message,
                    content,
                    existing_file.sha
                )
            except Exception:
                # File doesn't exist, create new
                repo.create_file(
                    requirements.file_path,
                    message,
                    content
                )
                
            # Update requirements metadata
            requirements.updated_at = datetime.utcnow()
            requirements.last_modified_by = "dashboard"
            
            # Clear cache
            cache_key = f"requirements_{project_id}"
            await self.cache.delete(cache_key)
            
            logger.info(f"Created requirements for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating requirements for {project_id}: {e}")
            return False
    
    async def update_requirements(self, 
                                project_id: str,
                                requirements: Requirements,
                                commit_message: Optional[str] = None) -> bool:
        """Update requirements file for a project.
        
        Args:
            project_id: Project ID (repository full name)
            requirements: Updated requirements object
            commit_message: Git commit message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.github:
            logger.error("GitHub token required for updating requirements")
            return False
            
        try:
            repo = self.github.get_repo(project_id)
            
            # Get existing file
            existing_file = repo.get_contents(requirements.file_path)
            
            # Generate updated content
            content = await self._generate_requirements_file(requirements)
            
            # Update file
            message = commit_message or f"Update requirements v{requirements.version}"
            repo.update_file(
                requirements.file_path,
                message,
                content,
                existing_file.sha
            )
            
            # Update requirements metadata
            requirements.updated_at = datetime.utcnow()
            requirements.last_modified_by = "dashboard"
            requirements.git_hash = existing_file.sha
            
            # Clear cache
            cache_key = f"requirements_{project_id}"
            await self.cache.delete(cache_key)
            
            logger.info(f"Updated requirements for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating requirements for {project_id}: {e}")
            return False
    
    async def get_requirements_history(self, project_id: str) -> List[RequirementsHistory]:
        """Get requirements change history for a project.
        
        Args:
            project_id: Project ID (repository full name)
            
        Returns:
            List of requirements history entries
        """
        cache_key = f"requirements_history_{project_id}"
        cached_history = await self.cache.get(cache_key)
        
        if cached_history:
            return cached_history
            
        if not self.github:
            return []
            
        try:
            repo = self.github.get_repo(project_id)
            history = []
            
            # Get commits that modified requirements files
            for filename in ["REQUIREMENTS.md", "requirements.md", "Requirements.md"]:
                try:
                    commits = repo.get_commits(path=filename)
                    for commit in commits:
                        history_entry = RequirementsHistory(
                            id=commit.sha,
                            project_id=project_id,
                            version="unknown",  # Would need to parse from commit
                            change_type="updated",
                            changes={},
                            changed_by=commit.author.login if commit.author else "unknown",
                            changed_at=commit.commit.author.date,
                            commit_hash=commit.sha,
                        )
                        history.append(history_entry)
                    break  # Found the file, stop looking
                except Exception:
                    continue
                    
            # Sort by date (newest first)
            history.sort(key=lambda x: x.changed_at, reverse=True)
            
            # Cache for 10 minutes
            await self.cache.set(cache_key, history, ttl=600)
            return history
            
        except Exception as e:
            logger.error(f"Error fetching requirements history for {project_id}: {e}")
            return []
    
    async def get_requirements_templates(self) -> List[RequirementsTemplate]:
        """Get available requirements templates.
        
        Returns:
            List of requirements templates
        """
        templates = [
            RequirementsTemplate(
                name="Basic Software Project",
                description="Standard template for software development projects",
                sections=[
                    "Functional Requirements",
                    "Non-Functional Requirements", 
                    "Technical Requirements",
                    "Business Requirements"
                ],
                default_items=[
                    RequirementItem(
                        id="func_001",
                        title="User Authentication",
                        description="System must provide secure user authentication",
                        priority="high",
                        status="pending",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    ),
                    RequirementItem(
                        id="nonfunc_001",
                        title="Performance",
                        description="System must respond within 2 seconds",
                        priority="medium",
                        status="pending",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    ),
                ]
            ),
            RequirementsTemplate(
                name="Web Application",
                description="Template for web application projects",
                sections=[
                    "User Interface Requirements",
                    "API Requirements",
                    "Database Requirements",
                    "Security Requirements",
                    "Performance Requirements"
                ],
                default_items=[
                    RequirementItem(
                        id="ui_001",
                        title="Responsive Design",
                        description="Application must work on mobile and desktop",
                        priority="high",
                        status="pending",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    ),
                ]
            ),
            RequirementsTemplate(
                name="API Service",
                description="Template for API and microservice projects",
                sections=[
                    "API Endpoints",
                    "Data Models",
                    "Authentication & Authorization",
                    "Rate Limiting",
                    "Documentation"
                ],
                default_items=[
                    RequirementItem(
                        id="api_001",
                        title="RESTful API Design",
                        description="API must follow REST principles",
                        priority="high",
                        status="pending",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    ),
                ]
            ),
        ]
        
        return templates
    
    async def _parse_requirements_file(self, content: str, project_id: str) -> Optional[Requirements]:
        """Parse requirements file content into Requirements object.
        
        Args:
            content: File content
            project_id: Project ID
            
        Returns:
            Requirements object or None if parsing fails
        """
        try:
            # This is a simplified parser - in reality, you'd want a more robust
            # markdown parser that can handle the specific format
            
            lines = content.split('\n')
            
            requirements = Requirements(
                project_id=project_id,
                title="Project Requirements",
                description="",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by="unknown",
                last_modified_by="unknown",
            )
            
            current_section = None
            current_item = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("# "):
                    requirements.title = line[2:]
                elif line.startswith("## "):
                    current_section = line[3:].lower()
                elif line.startswith("### "):
                    # New requirement item
                    if current_item and current_section:
                        self._add_item_to_section(requirements, current_section, current_item)
                    
                    current_item = RequirementItem(
                        id=f"req_{len(requirements.functional_requirements) + len(requirements.non_functional_requirements) + 1}",
                        title=line[4:],
                        description="",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                elif line and current_item:
                    # Add to description
                    if current_item.description:
                        current_item.description += "\n" + line
                    else:
                        current_item.description = line
                        
            # Add last item
            if current_item and current_section:
                self._add_item_to_section(requirements, current_section, current_item)
                
            return requirements
            
        except Exception as e:
            logger.error(f"Error parsing requirements file: {e}")
            return None
    
    def _add_item_to_section(self, requirements: Requirements, section: str, item: RequirementItem):
        """Add requirement item to appropriate section.
        
        Args:
            requirements: Requirements object
            section: Section name
            item: Requirement item
        """
        if "functional" in section:
            requirements.functional_requirements.append(item)
        elif "non-functional" in section or "performance" in section:
            requirements.non_functional_requirements.append(item)
        elif "technical" in section:
            requirements.technical_requirements.append(item)
        elif "business" in section:
            requirements.business_requirements.append(item)
        else:
            # Default to functional
            requirements.functional_requirements.append(item)
    
    async def _generate_requirements_file(self, requirements: Requirements) -> str:
        """Generate requirements file content from Requirements object.
        
        Args:
            requirements: Requirements object
            
        Returns:
            Markdown content
        """
        content = []
        
        # Title and description
        content.append(f"# {requirements.title}")
        content.append("")
        
        if requirements.description:
            content.append(requirements.description)
            content.append("")
            
        # Metadata
        content.append(f"**Version:** {requirements.version}")
        content.append(f"**Status:** {requirements.status}")
        content.append(f"**Last Updated:** {requirements.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # Functional Requirements
        if requirements.functional_requirements:
            content.append("## Functional Requirements")
            content.append("")
            for item in requirements.functional_requirements:
                content.append(f"### {item.title}")
                content.append("")
                content.append(item.description)
                content.append("")
                content.append(f"- **Priority:** {item.priority}")
                content.append(f"- **Status:** {item.status}")
                if item.assignee:
                    content.append(f"- **Assignee:** {item.assignee}")
                if item.due_date:
                    content.append(f"- **Due Date:** {item.due_date.strftime('%Y-%m-%d')}")
                content.append("")
                
        # Non-Functional Requirements
        if requirements.non_functional_requirements:
            content.append("## Non-Functional Requirements")
            content.append("")
            for item in requirements.non_functional_requirements:
                content.append(f"### {item.title}")
                content.append("")
                content.append(item.description)
                content.append("")
                content.append(f"- **Priority:** {item.priority}")
                content.append(f"- **Status:** {item.status}")
                if item.assignee:
                    content.append(f"- **Assignee:** {item.assignee}")
                content.append("")
                
        # Technical Requirements
        if requirements.technical_requirements:
            content.append("## Technical Requirements")
            content.append("")
            for item in requirements.technical_requirements:
                content.append(f"### {item.title}")
                content.append("")
                content.append(item.description)
                content.append("")
                content.append(f"- **Priority:** {item.priority}")
                content.append(f"- **Status:** {item.status}")
                if item.assignee:
                    content.append(f"- **Assignee:** {item.assignee}")
                content.append("")
                
        # Business Requirements
        if requirements.business_requirements:
            content.append("## Business Requirements")
            content.append("")
            for item in requirements.business_requirements:
                content.append(f"### {item.title}")
                content.append("")
                content.append(item.description)
                content.append("")
                content.append(f"- **Priority:** {item.priority}")
                content.append(f"- **Status:** {item.status}")
                if item.assignee:
                    content.append(f"- **Assignee:** {item.assignee}")
                content.append("")
                
        return "\n".join(content)

