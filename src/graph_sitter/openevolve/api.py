"""REST API endpoints for OpenEvolve evaluation management."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from graph_sitter.configs.models.openevolve_config import OpenEvolveConfig
from .models import EvaluationTrigger, EvaluationStatus
from .service import EvaluationService

logger = logging.getLogger(__name__)

# Request/Response models
class CreateEvaluationRequest(BaseModel):
    """Request model for creating an evaluation."""
    trigger_event: EvaluationTrigger = Field(description="Event that triggered the evaluation")
    context: Dict[str, Any] = Field(description="Context data for the evaluation")
    priority: int = Field(default=5, ge=1, le=10, description="Evaluation priority")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class EvaluationResponse(BaseModel):
    """Response model for evaluation data."""
    id: str = Field(description="Evaluation ID")
    evaluation_id: str = Field(description="OpenEvolve evaluation ID")
    status: EvaluationStatus = Field(description="Current status")
    trigger_event: str = Field(description="Trigger event")
    priority: int = Field(description="Priority level")
    submitted_at: Optional[str] = Field(description="Submission timestamp")
    started_at: Optional[str] = Field(description="Start timestamp")
    completed_at: Optional[str] = Field(description="Completion timestamp")
    context: Dict[str, Any] = Field(description="Context data")
    metadata: Dict[str, Any] = Field(description="Metadata")
    results: Optional[Dict[str, Any]] = Field(description="Evaluation results")
    metrics: Optional[Dict[str, Any]] = Field(description="Evaluation metrics")
    error_message: Optional[str] = Field(description="Error message if failed")


class EvaluationListResponse(BaseModel):
    """Response model for evaluation list."""
    evaluations: List[EvaluationResponse] = Field(description="List of evaluations")
    total: int = Field(description="Total number of evaluations")
    limit: int = Field(description="Limit used")
    offset: int = Field(description="Offset used")


class EvaluationSummaryResponse(BaseModel):
    """Response model for evaluation summary."""
    total_evaluations: int = Field(description="Total number of evaluations")
    completed_evaluations: int = Field(description="Number of completed evaluations")
    failed_evaluations: int = Field(description="Number of failed evaluations")
    success_rate: float = Field(description="Success rate percentage")
    average_execution_time: Optional[float] = Field(description="Average execution time")
    average_improvement_score: Optional[float] = Field(description="Average improvement score")
    last_evaluation_at: Optional[str] = Field(description="Last evaluation timestamp")


class SystemImprovementResponse(BaseModel):
    """Response model for system improvement."""
    id: str = Field(description="Improvement ID")
    evaluation_id: str = Field(description="Source evaluation ID")
    improvement_type: str = Field(description="Type of improvement")
    description: str = Field(description="Description")
    priority: int = Field(description="Priority level")
    estimated_impact: Optional[float] = Field(description="Estimated impact")
    implementation_complexity: Optional[str] = Field(description="Implementation complexity")
    applied: bool = Field(description="Whether applied")
    applied_at: Optional[str] = Field(description="Application timestamp")


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(description="Service status")
    openevolve_api_healthy: bool = Field(description="OpenEvolve API health")
    database_healthy: bool = Field(description="Database health")
    queue_size: int = Field(description="Current queue size")
    last_evaluation: Optional[str] = Field(description="Last evaluation timestamp")


# Dependency injection functions
def get_openevolve_config() -> OpenEvolveConfig:
    """Get OpenEvolve configuration."""
    return OpenEvolveConfig()


def get_database_session() -> Session:
    """Get database session."""
    # This would be implemented based on your database setup
    # For now, returning a placeholder
    raise NotImplementedError("Database session dependency not implemented")


async def get_evaluation_service(
    config: OpenEvolveConfig = Depends(get_openevolve_config),
    session: Session = Depends(get_database_session)
) -> EvaluationService:
    """Get evaluation service instance."""
    async with EvaluationService(config, session) as service:
        yield service


# Create router
router = APIRouter(prefix="/api/v1/openevolve", tags=["OpenEvolve"])


@router.post("/evaluations", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    request: CreateEvaluationRequest,
    service: EvaluationService = Depends(get_evaluation_service)
) -> EvaluationResponse:
    """Create a new evaluation.
    
    Args:
        request: Evaluation creation request
        service: Evaluation service
        
    Returns:
        Created evaluation data
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        evaluation_id = await service.trigger_evaluation(
            trigger_event=request.trigger_event,
            context=request.context,
            priority=request.priority,
            metadata=request.metadata
        )
        
        # Get the created evaluation
        result = await service.get_evaluation_result(evaluation_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created evaluation"
            )
        
        return EvaluationResponse(
            id=str(result.id),
            evaluation_id=result.evaluation_id,
            status=result.status,
            trigger_event=request.trigger_event.value,
            priority=request.priority,
            submitted_at=result.submitted_at.isoformat() if result.submitted_at else None,
            started_at=result.started_at.isoformat() if result.started_at else None,
            completed_at=result.completed_at.isoformat() if result.completed_at else None,
            context=request.context,
            metadata=request.metadata or {},
            results=result.results,
            metrics=result.metrics.dict() if result.metrics else None,
            error_message=result.error_message
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service)
) -> EvaluationResponse:
    """Get evaluation by ID.
    
    Args:
        evaluation_id: Evaluation ID
        service: Evaluation service
        
    Returns:
        Evaluation data
        
    Raises:
        HTTPException: If evaluation not found
    """
    result = await service.get_evaluation_result(evaluation_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    return EvaluationResponse(
        id=str(result.id),
        evaluation_id=result.evaluation_id,
        status=result.status,
        trigger_event="",  # Would need to get from database
        priority=0,  # Would need to get from database
        submitted_at=result.submitted_at.isoformat() if result.submitted_at else None,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        context={},  # Would need to get from database
        metadata={},  # Would need to get from database
        results=result.results,
        metrics=result.metrics.dict() if result.metrics else None,
        error_message=result.error_message
    )


@router.get("/evaluations", response_model=EvaluationListResponse)
async def list_evaluations(
    status: Optional[EvaluationStatus] = Query(None, description="Filter by status"),
    trigger_event: Optional[EvaluationTrigger] = Query(None, description="Filter by trigger event"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: EvaluationService = Depends(get_evaluation_service)
) -> EvaluationListResponse:
    """List evaluations with optional filtering.
    
    Args:
        status: Filter by status
        trigger_event: Filter by trigger event
        limit: Maximum number of results
        offset: Offset for pagination
        service: Evaluation service
        
    Returns:
        List of evaluations
    """
    results = await service.list_evaluations(status, trigger_event, limit, offset)
    
    evaluations = []
    for result in results:
        evaluations.append(EvaluationResponse(
            id=str(result.id),
            evaluation_id=result.evaluation_id,
            status=result.status,
            trigger_event="",  # Would need to get from database
            priority=0,  # Would need to get from database
            submitted_at=result.submitted_at.isoformat() if result.submitted_at else None,
            started_at=result.started_at.isoformat() if result.started_at else None,
            completed_at=result.completed_at.isoformat() if result.completed_at else None,
            context={},  # Would need to get from database
            metadata={},  # Would need to get from database
            results=result.results,
            metrics=result.metrics.dict() if result.metrics else None,
            error_message=result.error_message
        ))
    
    return EvaluationListResponse(
        evaluations=evaluations,
        total=len(evaluations),  # This should be the actual total from database
        limit=limit,
        offset=offset
    )


@router.delete("/evaluations/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_evaluation(
    evaluation_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service)
):
    """Cancel an evaluation.
    
    Args:
        evaluation_id: Evaluation ID
        service: Evaluation service
        
    Raises:
        HTTPException: If evaluation not found or cannot be cancelled
    """
    success = await service.cancel_evaluation(evaluation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found or cannot be cancelled"
        )


@router.post("/evaluations/{evaluation_id}/process", response_model=EvaluationResponse)
async def process_evaluation_result(
    evaluation_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service)
) -> EvaluationResponse:
    """Process evaluation result and apply improvements.
    
    Args:
        evaluation_id: Evaluation ID
        service: Evaluation service
        
    Returns:
        Updated evaluation data
        
    Raises:
        HTTPException: If evaluation not found or processing fails
    """
    result = await service.process_evaluation_result(evaluation_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found or processing failed"
        )
    
    return EvaluationResponse(
        id=str(result.id),
        evaluation_id=result.evaluation_id,
        status=result.status,
        trigger_event="",  # Would need to get from database
        priority=0,  # Would need to get from database
        submitted_at=result.submitted_at.isoformat() if result.submitted_at else None,
        started_at=result.started_at.isoformat() if result.started_at else None,
        completed_at=result.completed_at.isoformat() if result.completed_at else None,
        context={},  # Would need to get from database
        metadata={},  # Would need to get from database
        results=result.results,
        metrics=result.metrics.dict() if result.metrics else None,
        error_message=result.error_message
    )


@router.get("/summary", response_model=EvaluationSummaryResponse)
async def get_evaluation_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    service: EvaluationService = Depends(get_evaluation_service)
) -> EvaluationSummaryResponse:
    """Get evaluation summary for the specified period.
    
    Args:
        days: Number of days to include
        service: Evaluation service
        
    Returns:
        Evaluation summary
    """
    summary = await service.get_evaluation_summary(days)
    
    return EvaluationSummaryResponse(
        total_evaluations=summary.total_evaluations,
        completed_evaluations=summary.completed_evaluations,
        failed_evaluations=summary.failed_evaluations,
        success_rate=summary.success_rate,
        average_execution_time=summary.average_execution_time,
        average_improvement_score=summary.average_improvement_score,
        last_evaluation_at=summary.last_evaluation_at.isoformat() if summary.last_evaluation_at else None
    )


@router.get("/improvements/{evaluation_id}", response_model=List[SystemImprovementResponse])
async def get_evaluation_improvements(
    evaluation_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service)
) -> List[SystemImprovementResponse]:
    """Get system improvements for an evaluation.
    
    Args:
        evaluation_id: Evaluation ID
        service: Evaluation service
        
    Returns:
        List of system improvements
    """
    # This would need to be implemented in the service
    # For now, returning empty list
    return []


@router.post("/improvements/{improvement_id}/apply", status_code=status.HTTP_204_NO_CONTENT)
async def apply_system_improvement(
    improvement_id: UUID,
    service: EvaluationService = Depends(get_evaluation_service)
):
    """Apply a system improvement.
    
    Args:
        improvement_id: Improvement ID
        service: Evaluation service
        
    Raises:
        HTTPException: If improvement not found or application fails
    """
    success = await service.apply_system_improvement(improvement_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Improvement not found or application failed"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    config: OpenEvolveConfig = Depends(get_openevolve_config)
) -> HealthCheckResponse:
    """Check the health of the OpenEvolve service.
    
    Args:
        config: OpenEvolve configuration
        
    Returns:
        Health check results
    """
    openevolve_api_healthy = False
    
    if config.is_configured:
        try:
            from .client import OpenEvolveClient
            async with OpenEvolveClient(config) as client:
                openevolve_api_healthy = await client.health_check()
        except Exception as e:
            logger.error(f"OpenEvolve health check failed: {e}")
    
    return HealthCheckResponse(
        status="healthy" if openevolve_api_healthy else "degraded",
        openevolve_api_healthy=openevolve_api_healthy,
        database_healthy=True,  # Would implement actual database health check
        queue_size=0,  # Would get actual queue size
        last_evaluation=None  # Would get from database
    )

