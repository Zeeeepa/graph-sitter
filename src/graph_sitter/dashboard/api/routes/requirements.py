"""Requirements management API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...models.requirements import Requirements, RequirementItem, RequirementsHistory, RequirementsTemplate
from ...services.requirements_service import RequirementsService
from ...utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class CreateRequirementsRequest(BaseModel):
    """Request model for creating requirements."""
    title: str
    description: Optional[str] = None
    template_name: Optional[str] = None
    functional_requirements: List[RequirementItem] = []
    non_functional_requirements: List[RequirementItem] = []
    technical_requirements: List[RequirementItem] = []
    business_requirements: List[RequirementItem] = []


class UpdateRequirementsRequest(BaseModel):
    """Request model for updating requirements."""
    title: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    functional_requirements: Optional[List[RequirementItem]] = None
    non_functional_requirements: Optional[List[RequirementItem]] = None
    technical_requirements: Optional[List[RequirementItem]] = None
    business_requirements: Optional[List[RequirementItem]] = None


def get_requirements_service(request: Request) -> RequirementsService:
    """Dependency to get requirements service."""
    if not hasattr(request.app.state, "requirements_service"):
        raise HTTPException(status_code=503, detail="Requirements service not available")
    return request.app.state.requirements_service


@router.get("/{project_id}", response_model=Requirements)
async def get_requirements(
    project_id: str,
    requirements_service: RequirementsService = Depends(get_requirements_service),
):
    """Get requirements for a project."""
    try:
        requirements = await requirements_service.get_requirements(project_id)
        
        if not requirements:
            raise HTTPException(status_code=404, detail="Requirements not found")
            
        return requirements
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching requirements for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch requirements")


@router.post("/{project_id}", response_model=Requirements)
async def create_requirements(
    project_id: str,
    request_data: CreateRequirementsRequest,
    requirements_service: RequirementsService = Depends(get_requirements_service),
):
    """Create requirements for a project."""
    try:
        from datetime import datetime
        
        # Create requirements object
        requirements = Requirements(
            project_id=project_id,
            title=request_data.title,
            description=request_data.description,
            functional_requirements=request_data.functional_requirements,
            non_functional_requirements=request_data.non_functional_requirements,
            technical_requirements=request_data.technical_requirements,
            business_requirements=request_data.business_requirements,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="dashboard",
            last_modified_by="dashboard",
        )
        
        # Apply template if specified
        if request_data.template_name:
            templates = await requirements_service.get_requirements_templates()
            template = next((t for t in templates if t.name == request_data.template_name), None)
            
            if template:
                # Add default items from template
                requirements.functional_requirements.extend(template.default_items)
                
        # Create requirements file
        success = await requirements_service.create_requirements(project_id, requirements)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create requirements file")
            
        logger.info(f"Created requirements for project {project_id}")
        return requirements
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating requirements for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create requirements")


@router.put("/{project_id}", response_model=Requirements)
async def update_requirements(
    project_id: str,
    request_data: UpdateRequirementsRequest,
    requirements_service: RequirementsService = Depends(get_requirements_service),
):
    """Update requirements for a project."""
    try:
        # Get existing requirements
        requirements = await requirements_service.get_requirements(project_id)
        
        if not requirements:
            raise HTTPException(status_code=404, detail="Requirements not found")
            
        # Update fields
        if request_data.title:
            requirements.title = request_data.title
            
        if request_data.description is not None:
            requirements.description = request_data.description
            
        if request_data.version:
            requirements.version = request_data.version
            
        if request_data.status:
            requirements.status = request_data.status
            
        if request_data.functional_requirements is not None:
            requirements.functional_requirements = request_data.functional_requirements
            
        if request_data.non_functional_requirements is not None:
            requirements.non_functional_requirements = request_data.non_functional_requirements
            
        if request_data.technical_requirements is not None:
            requirements.technical_requirements = request_data.technical_requirements
            
        if request_data.business_requirements is not None:
            requirements.business_requirements = request_data.business_requirements
            
        # Update requirements file
        success = await requirements_service.update_requirements(project_id, requirements)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update requirements file")
            
        logger.info(f"Updated requirements for project {project_id}")
        return requirements
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating requirements for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update requirements")


@router.get("/{project_id}/history", response_model=List[RequirementsHistory])
async def get_requirements_history(
    project_id: str,
    requirements_service: RequirementsService = Depends(get_requirements_service),
):
    """Get requirements change history for a project."""
    try:
        history = await requirements_service.get_requirements_history(project_id)
        return history
        
    except Exception as e:
        logger.error(f"Error fetching requirements history for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch requirements history")


@router.get("/templates/list", response_model=List[RequirementsTemplate])
async def get_requirements_templates(
    requirements_service: RequirementsService = Depends(get_requirements_service),
):
    """Get available requirements templates."""
    try:
        templates = await requirements_service.get_requirements_templates()
        return templates
        
    except Exception as e:
        logger.error(f"Error fetching requirements templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch requirements templates")


@router.post("/{project_id}/generate")
async def generate_requirements_from_code(
    project_id: str,
    request: Request,
    requirements_service: RequirementsService = Depends(get_requirements_service),
):
    """Generate requirements based on code analysis."""
    try:
        # Get chat service for AI-powered generation
        if not hasattr(request.app.state, "chat_service"):
            raise HTTPException(status_code=503, detail="Chat service not available for requirements generation")
            
        chat_service = request.app.state.chat_service
        
        # Generate requirements prompt
        prompt = await chat_service.generate_requirements_prompt(project_id)
        
        # Create a chat session for requirements generation
        session = await chat_service.create_session(
            project_id=project_id,
            context={"purpose": "requirements_generation"}
        )
        
        # Get AI response
        response = await chat_service.send_message(
            session.session_id,
            prompt,
            include_code_analysis=True
        )
        
        if not response:
            raise HTTPException(status_code=500, detail="Failed to generate requirements")
            
        return {
            "generated_requirements": response,
            "prompt_used": prompt,
            "session_id": session.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating requirements for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate requirements")


@router.post("/{project_id}/validate")
async def validate_requirements(
    project_id: str,
    requirements_service: RequirementsService = Depends(get_requirements_service),
):
    """Validate requirements against project code."""
    try:
        requirements = await requirements_service.get_requirements(project_id)
        
        if not requirements:
            raise HTTPException(status_code=404, detail="Requirements not found")
            
        # Validation logic would go here
        # For now, return a simple validation result
        
        validation_results = {
            "valid": True,
            "issues": [],
            "suggestions": [
                "Consider adding more specific acceptance criteria",
                "Some requirements could benefit from priority assignment",
                "Add estimated effort for implementation planning"
            ],
            "coverage": {
                "functional": len(requirements.functional_requirements),
                "non_functional": len(requirements.non_functional_requirements),
                "technical": len(requirements.technical_requirements),
                "business": len(requirements.business_requirements),
            }
        }
        
        return validation_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating requirements for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate requirements")


@router.post("/{project_id}/export")
async def export_requirements(
    project_id: str,
    format: str = "markdown",
    requirements_service: RequirementsService = Depends(get_requirements_service),
):
    """Export requirements in various formats."""
    try:
        requirements = await requirements_service.get_requirements(project_id)
        
        if not requirements:
            raise HTTPException(status_code=404, detail="Requirements not found")
            
        if format.lower() == "markdown":
            # Generate markdown content
            content = await requirements_service._generate_requirements_file(requirements)
            
            return {
                "format": "markdown",
                "content": content,
                "filename": f"{project_id.replace('/', '_')}_requirements.md"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting requirements for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export requirements")

