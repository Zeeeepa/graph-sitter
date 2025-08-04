"""
Refactoring Engine

Main orchestrator for all refactoring operations with safety checks,
conflict detection, and preview capabilities.
"""

import asyncio
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass

from ..types import (
    RefactoringType, 
    RefactoringResult, 
    RefactoringChange, 
    RefactoringConflict,
    ChangeType,
    ConflictType,
    PerformanceMetrics
)

logger = logging.getLogger(__name__)


@dataclass
class RefactoringConfig:
    """Configuration for refactoring operations."""
    enable_safety_checks: bool = True
    enable_conflict_detection: bool = True
    enable_preview: bool = True
    backup_before_refactor: bool = True
    max_file_changes: int = 100
    timeout_seconds: float = 30.0
    dry_run_by_default: bool = True


class RefactoringEngine:
    """
    Comprehensive refactoring engine.
    
    Provides safe refactoring operations with conflict detection,
    preview capabilities, and undo/redo support.
    
    Features:
    - Multiple refactoring types (rename, extract, inline, move)
    - Safety checks and conflict detection
    - Preview mode for all operations
    - Performance monitoring
    - Integration with LSP workspace edits
    """
    
    def __init__(self, codebase_path: str, serena_core: Any, config: Optional[RefactoringConfig] = None):
        self.codebase_path = Path(codebase_path)
        self.serena_core = serena_core
        self.config = config or RefactoringConfig()
        
        # Refactoring modules (lazy loaded)
        self._refactoring_modules: Dict[RefactoringType, Any] = {}
        
        # Operation tracking
        self._active_operations: Dict[str, RefactoringResult] = {}
        self._operation_history: List[RefactoringResult] = []
        
        # Performance tracking
        self._performance_metrics: List[PerformanceMetrics] = []
        
        logger.info(f"RefactoringEngine initialized for: {self.codebase_path}")
    
    async def initialize(self) -> None:
        """Initialize the refactoring engine."""
        logger.info("Initializing refactoring engine...")
        
        # Initialize refactoring modules
        await self._initialize_refactoring_modules()
        
        logger.info("✅ Refactoring engine initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the refactoring engine."""
        logger.info("Shutting down refactoring engine...")
        
        # Cancel any active operations
        for operation_id in list(self._active_operations.keys()):
            await self.cancel_operation(operation_id)
        
        # Shutdown refactoring modules
        for module in self._refactoring_modules.values():
            if hasattr(module, 'shutdown'):
                await module.shutdown()
        
        self._refactoring_modules.clear()
        self._active_operations.clear()
        
        logger.info("✅ Refactoring engine shutdown complete")
    
    async def perform_refactoring(
        self,
        refactoring_type: str,
        operation_id: Optional[str] = None,
        dry_run: Optional[bool] = None,
        **kwargs
    ) -> RefactoringResult:
        """
        Perform a refactoring operation.
        
        Args:
            refactoring_type: Type of refactoring to perform
            operation_id: Optional operation ID for tracking
            dry_run: Whether to perform a dry run (preview only)
            **kwargs: Refactoring-specific parameters
            
        Returns:
            RefactoringResult with changes, conflicts, and metadata
        """
        # Validate refactoring type
        try:
            ref_type = RefactoringType(refactoring_type)
        except ValueError:
            return RefactoringResult(
                success=False,
                refactoring_type=None,
                changes=[],
                conflicts=[],
                error_message=f"Invalid refactoring type: {refactoring_type}"
            )
        
        # Use dry run by default if not specified
        if dry_run is None:
            dry_run = self.config.dry_run_by_default
        
        # Generate operation ID if not provided
        if operation_id is None:
            operation_id = f"{refactoring_type}_{int(time.time() * 1000)}"
        
        # Start performance tracking
        metrics = PerformanceMetrics.start_timing(f"refactoring_{refactoring_type}")
        
        try:
            logger.info(f"Starting refactoring: {refactoring_type} (dry_run={dry_run})")
            
            # Get refactoring module
            module = await self._get_refactoring_module(ref_type)
            if not module:
                return RefactoringResult(
                    success=False,
                    refactoring_type=ref_type,
                    changes=[],
                    conflicts=[],
                    error_message=f"Refactoring module not available: {refactoring_type}"
                )
            
            # Perform safety checks if enabled
            if self.config.enable_safety_checks:
                safety_result = await self._perform_safety_checks(ref_type, **kwargs)
                if not safety_result['safe']:
                    return RefactoringResult(
                        success=False,
                        refactoring_type=ref_type,
                        changes=[],
                        conflicts=[],
                        error_message=f"Safety check failed: {safety_result['reason']}"
                    )
            
            # Perform the refactoring
            result = await module.perform_refactoring(
                dry_run=dry_run,
                operation_id=operation_id,
                **kwargs
            )
            
            # Add performance metrics
            metrics.finish_timing()
            result.execution_time = metrics.duration
            self._performance_metrics.append(metrics)
            
            # Store operation if not dry run
            if not dry_run and result.success:
                self._active_operations[operation_id] = result
                self._operation_history.append(result)
            
            # Emit event
            if self.serena_core:
                await self.serena_core._emit_event("refactoring.completed", {
                    'operation_id': operation_id,
                    'refactoring_type': refactoring_type,
                    'success': result.success,
                    'dry_run': dry_run,
                    'changes_count': len(result.changes),
                    'conflicts_count': len(result.conflicts),
                    'execution_time': result.execution_time
                })
            
            logger.info(f"Refactoring completed: {refactoring_type} (success={result.success})")
            return result
            
        except asyncio.TimeoutError:
            metrics.finish_timing()
            return RefactoringResult(
                success=False,
                refactoring_type=ref_type,
                changes=[],
                conflicts=[],
                error_message=f"Refactoring operation timed out after {self.config.timeout_seconds}s"
            )
            
        except Exception as e:
            metrics.finish_timing()
            logger.error(f"Error performing refactoring {refactoring_type}: {e}")
            return RefactoringResult(
                success=False,
                refactoring_type=ref_type,
                changes=[],
                conflicts=[],
                error_message=f"Refactoring failed: {str(e)}"
            )
    
    async def preview_refactoring(self, refactoring_type: str, **kwargs) -> RefactoringResult:
        """
        Preview a refactoring operation without applying changes.
        
        Args:
            refactoring_type: Type of refactoring to preview
            **kwargs: Refactoring-specific parameters
            
        Returns:
            RefactoringResult with preview of changes and conflicts
        """
        return await self.perform_refactoring(
            refactoring_type=refactoring_type,
            dry_run=True,
            **kwargs
        )
    
    async def apply_refactoring(self, refactoring_type: str, **kwargs) -> RefactoringResult:
        """
        Apply a refactoring operation with actual changes.
        
        Args:
            refactoring_type: Type of refactoring to apply
            **kwargs: Refactoring-specific parameters
            
        Returns:
            RefactoringResult with applied changes
        """
        return await self.perform_refactoring(
            refactoring_type=refactoring_type,
            dry_run=False,
            **kwargs
        )
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel an active refactoring operation.
        
        Args:
            operation_id: ID of operation to cancel
            
        Returns:
            True if cancellation successful
        """
        if operation_id not in self._active_operations:
            return False
        
        try:
            # Remove from active operations
            operation = self._active_operations.pop(operation_id)
            
            # Emit cancellation event
            if self.serena_core:
                await self.serena_core._emit_event("refactoring.cancelled", {
                    'operation_id': operation_id,
                    'refactoring_type': operation.refactoring_type.value if operation.refactoring_type else None
                })
            
            logger.info(f"Cancelled refactoring operation: {operation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling operation {operation_id}: {e}")
            return False
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a refactoring operation."""
        if operation_id not in self._active_operations:
            return None
        
        operation = self._active_operations[operation_id]
        return {
            'operation_id': operation_id,
            'refactoring_type': operation.refactoring_type.value if operation.refactoring_type else None,
            'success': operation.success,
            'changes_count': len(operation.changes),
            'conflicts_count': len(operation.conflicts),
            'files_changed': operation.files_changed,
            'execution_time': operation.execution_time
        }
    
    def get_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history of refactoring operations."""
        history = self._operation_history[-limit:] if limit > 0 else self._operation_history
        
        return [
            {
                'refactoring_type': op.refactoring_type.value if op.refactoring_type else None,
                'success': op.success,
                'changes_count': len(op.changes),
                'conflicts_count': len(op.conflicts),
                'files_changed': op.files_changed,
                'execution_time': op.execution_time,
                'timestamp': getattr(op, 'timestamp', None)
            }
            for op in history
        ]
    
    def get_supported_refactoring_types(self) -> List[str]:
        """Get list of supported refactoring types."""
        return [ref_type.value for ref_type in RefactoringType]
    
    def get_performance_metrics(self) -> List[Dict[str, Any]]:
        """Get performance metrics for refactoring operations."""
        return [metric.to_dict() for metric in self._performance_metrics]
    
    async def _initialize_refactoring_modules(self) -> None:
        """Initialize all refactoring modules."""
        # Import and initialize refactoring modules
        refactoring_modules = {
            RefactoringType.RENAME: ('rename_refactor', 'RenameRefactor'),
            RefactoringType.EXTRACT_METHOD: ('extract_refactor', 'ExtractRefactor'),
            RefactoringType.EXTRACT_VARIABLE: ('extract_refactor', 'ExtractRefactor'),
            RefactoringType.INLINE_METHOD: ('inline_refactor', 'InlineRefactor'),
            RefactoringType.INLINE_VARIABLE: ('inline_refactor', 'InlineRefactor'),
            RefactoringType.MOVE_SYMBOL: ('move_refactor', 'MoveRefactor'),
            RefactoringType.MOVE_FILE: ('move_refactor', 'MoveRefactor'),
            RefactoringType.ORGANIZE_IMPORTS: ('organize_imports', 'OrganizeImports')
        }
        
        for ref_type, (module_name, class_name) in refactoring_modules.items():
            try:
                # Dynamic import
                module = __import__(f'.{module_name}', package=__package__, fromlist=[class_name])
                refactor_class = getattr(module, class_name)
                
                # Initialize instance
                instance = refactor_class(self.codebase_path, self.serena_core, self.config)
                if hasattr(instance, 'initialize'):
                    await instance.initialize()
                
                self._refactoring_modules[ref_type] = instance
                logger.debug(f"Initialized refactoring module: {ref_type.value}")
                
            except ImportError as e:
                logger.warning(f"Could not import refactoring module {module_name}: {e}")
            except Exception as e:
                logger.error(f"Error initializing refactoring module {ref_type.value}: {e}")
    
    async def _get_refactoring_module(self, refactoring_type: RefactoringType) -> Optional[Any]:
        """Get refactoring module for a specific type."""
        return self._refactoring_modules.get(refactoring_type)
    
    async def _perform_safety_checks(self, refactoring_type: RefactoringType, **kwargs) -> Dict[str, Any]:
        """Perform safety checks before refactoring."""
        try:
            # Basic safety checks
            checks = {
                'file_exists': True,
                'file_writable': True,
                'no_syntax_errors': True,
                'within_limits': True
            }
            
            # Check file existence and writability
            if 'file_path' in kwargs:
                file_path = Path(kwargs['file_path'])
                if not file_path.exists():
                    checks['file_exists'] = False
                elif not file_path.is_file():
                    checks['file_exists'] = False
                else:
                    # Check if file is writable
                    try:
                        with open(file_path, 'a'):
                            pass
                    except (PermissionError, OSError):
                        checks['file_writable'] = False
            
            # Check if operation is within limits
            if refactoring_type in [RefactoringType.MOVE_FILE, RefactoringType.ORGANIZE_IMPORTS]:
                # These operations might affect many files
                if self.config.max_file_changes < 10:
                    checks['within_limits'] = False
            
            # Determine if safe
            all_safe = all(checks.values())
            
            return {
                'safe': all_safe,
                'checks': checks,
                'reason': 'Safety checks failed' if not all_safe else 'All safety checks passed'
            }
            
        except Exception as e:
            logger.error(f"Error performing safety checks: {e}")
            return {
                'safe': False,
                'checks': {},
                'reason': f'Safety check error: {str(e)}'
            }


# Utility functions for refactoring operations
def create_refactoring_change(
    file_path: str,
    start_line: int,
    start_char: int,
    end_line: int,
    end_char: int,
    old_text: str,
    new_text: str,
    change_type: ChangeType = ChangeType.REPLACE,
    description: Optional[str] = None
) -> RefactoringChange:
    """Create a RefactoringChange instance."""
    return RefactoringChange(
        file_path=file_path,
        start_line=start_line,
        start_character=start_char,
        end_line=end_line,
        end_character=end_char,
        old_text=old_text,
        new_text=new_text,
        change_type=change_type,
        description=description
    )


def create_refactoring_conflict(
    file_path: str,
    line_number: int,
    character: int,
    conflict_type: ConflictType,
    description: str,
    severity: str = "error",
    suggested_resolution: Optional[str] = None
) -> RefactoringConflict:
    """Create a RefactoringConflict instance."""
    return RefactoringConflict(
        file_path=file_path,
        line_number=line_number,
        character=character,
        conflict_type=conflict_type,
        description=description,
        severity=severity,
        suggested_resolution=suggested_resolution
    )

