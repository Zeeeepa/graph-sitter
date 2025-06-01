"""Evaluation service for orchestrating OpenEvolve evaluations."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from graph_sitter.configs.models.openevolve_config import OpenEvolveConfig
from .client import OpenEvolveClient, OpenEvolveAPIError
from .database import EvaluationRepository, OpenEvolveEvaluation, SystemImprovement
from .models import (
    EvaluationRequest, EvaluationResult, EvaluationStatus, EvaluationTrigger,
    EvaluationSummary, SystemImprovement as SystemImprovementModel
)

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for managing OpenEvolve evaluations."""
    
    def __init__(self, config: OpenEvolveConfig, session: Session):
        """Initialize the evaluation service.
        
        Args:
            config: OpenEvolve configuration
            session: Database session
        """
        self.config = config
        self.session = session
        self.repository = EvaluationRepository(session)
        self._client: Optional[OpenEvolveClient] = None
        self._last_evaluation_time: Optional[datetime] = None
        self._evaluation_queue: asyncio.Queue = asyncio.Queue(maxsize=config.evaluation_queue_size)
        self._processing_task: Optional[asyncio.Task] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = OpenEvolveClient(self.config)
        await self._client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    def start_processing(self):
        """Start the background evaluation processing task."""
        if not self._processing_task or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_evaluation_queue())
    
    def stop_processing(self):
        """Stop the background evaluation processing task."""
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
    
    async def trigger_evaluation(
        self, 
        trigger_event: EvaluationTrigger, 
        context: Dict[str, Any],
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """Trigger a new evaluation.
        
        Args:
            trigger_event: Event that triggered the evaluation
            context: Context data for the evaluation
            priority: Evaluation priority (1=highest, 10=lowest)
            metadata: Additional metadata
            
        Returns:
            Evaluation ID
            
        Raises:
            ValueError: If evaluations are disabled or rate limited
        """
        if not self.config.enable_auto_evaluation and trigger_event != EvaluationTrigger.MANUAL:
            raise ValueError("Automatic evaluations are disabled")
        
        # Check rate limiting
        if self._last_evaluation_time:
            time_since_last = datetime.utcnow() - self._last_evaluation_time
            if time_since_last.total_seconds() < self.config.min_evaluation_interval:
                raise ValueError(f"Rate limited: minimum interval is {self.config.min_evaluation_interval} seconds")
        
        # Create evaluation request
        evaluation_request = EvaluationRequest(
            trigger_event=trigger_event,
            context=context,
            priority=priority,
            metadata=metadata or {}
        )
        
        # Store in database
        evaluation_data = {
            "id": evaluation_request.id,
            "status": EvaluationStatus.PENDING.value,
            "trigger_event": trigger_event.value,
            "priority": priority,
            "context": context,
            "metadata": metadata or {},
            "timeout": evaluation_request.timeout,
        }
        
        evaluation = self.repository.create_evaluation(evaluation_data)
        
        # Add to processing queue
        try:
            await self._evaluation_queue.put(evaluation_request)
            logger.info(f"Evaluation {evaluation_request.id} queued for processing")
        except asyncio.QueueFull:
            # Update status to failed if queue is full
            self.repository.update_evaluation_status(
                evaluation_request.id,
                EvaluationStatus.FAILED,
                error_message="Evaluation queue is full"
            )
            raise ValueError("Evaluation queue is full")
        
        self._last_evaluation_time = datetime.utcnow()
        return evaluation_request.id
    
    async def get_evaluation_result(self, evaluation_id: UUID) -> Optional[EvaluationResult]:
        """Get evaluation result by ID.
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            Evaluation result or None
        """
        evaluation = self.repository.get_evaluation(evaluation_id)
        if not evaluation:
            return None
        
        return self._convert_to_result(evaluation)
    
    async def list_evaluations(
        self,
        status: Optional[EvaluationStatus] = None,
        trigger_event: Optional[EvaluationTrigger] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EvaluationResult]:
        """List evaluations with optional filtering.
        
        Args:
            status: Filter by status
            trigger_event: Filter by trigger event
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of evaluation results
        """
        evaluations = self.repository.list_evaluations(status, trigger_event, limit, offset)
        return [self._convert_to_result(eval) for eval in evaluations]
    
    async def cancel_evaluation(self, evaluation_id: UUID) -> bool:
        """Cancel an evaluation.
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            True if cancellation was successful
        """
        evaluation = self.repository.get_evaluation(evaluation_id)
        if not evaluation:
            return False
        
        if evaluation.status in [EvaluationStatus.COMPLETED.value, EvaluationStatus.FAILED.value, EvaluationStatus.CANCELLED.value]:
            return False
        
        # Cancel in OpenEvolve if it has been submitted
        if evaluation.evaluation_id and self._client:
            await self._client.cancel_evaluation(evaluation.evaluation_id)
        
        # Update status in database
        self.repository.update_evaluation_status(
            evaluation_id,
            EvaluationStatus.CANCELLED
        )
        
        logger.info(f"Evaluation {evaluation_id} cancelled")
        return True
    
    async def process_evaluation_result(self, evaluation_id: UUID) -> Optional[EvaluationResult]:
        """Process and apply evaluation results.
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            Updated evaluation result or None
        """
        evaluation = self.repository.get_evaluation(evaluation_id)
        if not evaluation or not evaluation.evaluation_id:
            return None
        
        if not self._client:
            logger.error("OpenEvolve client not available")
            return None
        
        try:
            # Get results from OpenEvolve
            result_data = await self._client.get_evaluation_result(evaluation.evaluation_id)
            
            # Update evaluation with results
            self.repository.update_evaluation_status(
                evaluation_id,
                EvaluationStatus(result_data.get("status", "completed")),
                results=result_data.get("results", {}),
                metrics=result_data.get("metrics", {}),
                completed_at=datetime.utcnow()
            )
            
            # Process system improvements
            improvements = await self._client.get_system_improvements(evaluation.evaluation_id)
            for improvement_data in improvements:
                improvement = {
                    "evaluation_id": evaluation_id,
                    "improvement_type": improvement_data.get("type", "unknown"),
                    "description": improvement_data.get("description", ""),
                    "priority": improvement_data.get("priority", 5),
                    "estimated_impact": improvement_data.get("estimated_impact"),
                    "implementation_complexity": improvement_data.get("complexity"),
                }
                self.repository.create_improvement(improvement)
            
            logger.info(f"Processed evaluation result for {evaluation_id}")
            return await self.get_evaluation_result(evaluation_id)
            
        except OpenEvolveAPIError as e:
            logger.error(f"Failed to process evaluation result for {evaluation_id}: {e}")
            self.repository.update_evaluation_status(
                evaluation_id,
                EvaluationStatus.FAILED,
                error_message=str(e)
            )
            return None
    
    async def get_evaluation_summary(self, days: int = 30) -> EvaluationSummary:
        """Get evaluation summary for the specified period.
        
        Args:
            days: Number of days to include in summary
            
        Returns:
            Evaluation summary
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all evaluations in the period
        evaluations = self.session.query(OpenEvolveEvaluation).filter(
            OpenEvolveEvaluation.created_at >= since_date
        ).all()
        
        total_evaluations = len(evaluations)
        completed_evaluations = len([e for e in evaluations if e.status == EvaluationStatus.COMPLETED.value])
        failed_evaluations = len([e for e in evaluations if e.status == EvaluationStatus.FAILED.value])
        
        # Calculate averages
        completed_evals = [e for e in evaluations if e.status == EvaluationStatus.COMPLETED.value and e.metrics]
        
        avg_execution_time = None
        avg_improvement_score = None
        
        if completed_evals:
            execution_times = [e.metrics.get("execution_time") for e in completed_evals if e.metrics and e.metrics.get("execution_time")]
            if execution_times:
                avg_execution_time = sum(execution_times) / len(execution_times)
            
            improvement_scores = [e.metrics.get("improvement_score") for e in completed_evals if e.metrics and e.metrics.get("improvement_score")]
            if improvement_scores:
                avg_improvement_score = sum(improvement_scores) / len(improvement_scores)
        
        success_rate = (completed_evaluations / total_evaluations * 100) if total_evaluations > 0 else 0
        
        last_evaluation_at = None
        if evaluations:
            last_evaluation_at = max(e.created_at for e in evaluations)
        
        return EvaluationSummary(
            total_evaluations=total_evaluations,
            completed_evaluations=completed_evaluations,
            failed_evaluations=failed_evaluations,
            average_execution_time=avg_execution_time,
            average_improvement_score=avg_improvement_score,
            success_rate=success_rate,
            last_evaluation_at=last_evaluation_at
        )
    
    async def apply_system_improvement(self, improvement_id: UUID) -> bool:
        """Apply a system improvement.
        
        Args:
            improvement_id: Improvement ID
            
        Returns:
            True if application was successful
        """
        improvement = self.session.query(SystemImprovement).filter(
            SystemImprovement.id == improvement_id
        ).first()
        
        if not improvement or improvement.applied:
            return False
        
        try:
            # Here you would implement the actual improvement application logic
            # This is a placeholder for the actual implementation
            logger.info(f"Applying system improvement {improvement_id}: {improvement.description}")
            
            # Mark as applied
            results = {"applied_at": datetime.utcnow().isoformat(), "status": "success"}
            self.repository.mark_improvement_applied(improvement_id, results)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply system improvement {improvement_id}: {e}")
            return False
    
    async def _process_evaluation_queue(self):
        """Background task to process evaluation queue."""
        logger.info("Started evaluation queue processing")
        
        while True:
            try:
                # Get evaluation from queue
                evaluation_request = await self._evaluation_queue.get()
                
                # Process the evaluation
                await self._process_single_evaluation(evaluation_request)
                
                # Mark task as done
                self._evaluation_queue.task_done()
                
                # Small delay to prevent overwhelming the API
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                logger.info("Evaluation queue processing cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing evaluation queue: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_single_evaluation(self, evaluation_request: EvaluationRequest):
        """Process a single evaluation.
        
        Args:
            evaluation_request: Evaluation request to process
        """
        if not self._client:
            logger.error("OpenEvolve client not available")
            return
        
        try:
            # Submit to OpenEvolve
            openevolve_id = await self._client.submit_evaluation(evaluation_request)
            
            # Update database with OpenEvolve ID
            self.repository.update_evaluation_status(
                evaluation_request.id,
                EvaluationStatus.SUBMITTED,
                evaluation_id=openevolve_id,
                submitted_at=datetime.utcnow()
            )
            
            # Poll for completion
            await self._poll_evaluation_completion(evaluation_request.id, openevolve_id)
            
        except OpenEvolveAPIError as e:
            logger.error(f"Failed to submit evaluation {evaluation_request.id}: {e}")
            self.repository.update_evaluation_status(
                evaluation_request.id,
                EvaluationStatus.FAILED,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error processing evaluation {evaluation_request.id}: {e}")
            self.repository.update_evaluation_status(
                evaluation_request.id,
                EvaluationStatus.FAILED,
                error_message=f"Unexpected error: {e}"
            )
    
    async def _poll_evaluation_completion(self, evaluation_id: UUID, openevolve_id: str):
        """Poll OpenEvolve for evaluation completion.
        
        Args:
            evaluation_id: Internal evaluation ID
            openevolve_id: OpenEvolve evaluation ID
        """
        if not self._client:
            return
        
        max_polls = 60  # Maximum number of polls (5 minutes with 5-second intervals)
        poll_interval = 5  # Seconds between polls
        
        for _ in range(max_polls):
            try:
                status = await self._client.get_evaluation_status(openevolve_id)
                
                if status == EvaluationStatus.RUNNING:
                    # Update status to running
                    self.repository.update_evaluation_status(
                        evaluation_id,
                        EvaluationStatus.RUNNING,
                        started_at=datetime.utcnow()
                    )
                elif status in [EvaluationStatus.COMPLETED, EvaluationStatus.FAILED]:
                    # Process final result
                    await self.process_evaluation_result(evaluation_id)
                    break
                
                await asyncio.sleep(poll_interval)
                
            except OpenEvolveAPIError as e:
                logger.error(f"Error polling evaluation {openevolve_id}: {e}")
                break
        else:
            # Timeout
            logger.warning(f"Evaluation {openevolve_id} polling timed out")
            self.repository.update_evaluation_status(
                evaluation_id,
                EvaluationStatus.FAILED,
                error_message="Evaluation polling timed out"
            )
    
    def _convert_to_result(self, evaluation: OpenEvolveEvaluation) -> EvaluationResult:
        """Convert database evaluation to result model.
        
        Args:
            evaluation: Database evaluation record
            
        Returns:
            Evaluation result model
        """
        return EvaluationResult(
            id=evaluation.id,
            evaluation_id=evaluation.evaluation_id or "",
            status=EvaluationStatus(evaluation.status),
            submitted_at=evaluation.submitted_at or evaluation.created_at,
            started_at=evaluation.started_at,
            completed_at=evaluation.completed_at,
            results=evaluation.results or {},
            metrics=evaluation.metrics,
            error_message=evaluation.error_message,
            recommendations=[]  # Would be populated from improvements
        )

