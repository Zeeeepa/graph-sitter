"""Enhanced Codemod Framework with Safety, Performance, and Error Handling.

This module provides improved base classes for codemods with:
- Rollback capabilities and transaction-like safety
- Performance optimizations with file filtering and parallel processing
- Comprehensive error handling and recovery mechanisms
- Structured logging and monitoring integration
"""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import File

from .codemod import Codemod


class ValidationError(Exception):
    """Raised when pre-transformation validation fails."""
    pass


class TransformationError(Exception):
    """Raised when transformation execution fails."""
    pass


class CodemodBackup:
    """Manages backup state for rollback capabilities."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.file_snapshots: Dict[str, str] = {}
        self.created_files: List[str] = []
        self.deleted_files: List[Tuple[str, str]] = []  # (filepath, content)
        self.timestamp = time.time()
    
    def create_snapshot(self) -> None:
        """Create a snapshot of current codebase state."""
        for file in self.codebase.files:
            self.file_snapshots[file.filepath] = file.content
    
    def restore_snapshot(self) -> None:
        """Restore codebase to snapshot state."""
        # Restore modified files
        for filepath, content in self.file_snapshots.items():
            file = self.codebase.get_file(filepath)
            if file:
                file.content = content
        
        # Remove created files
        for filepath in self.created_files:
            file = self.codebase.get_file(filepath)
            if file:
                file.remove()
        
        # Restore deleted files
        for filepath, content in self.deleted_files:
            self.codebase.create_file(filepath, content=content)


class SafeCodemod(Codemod):
    """Enhanced Codemod with safety mechanisms and rollback capabilities."""
    
    def __init__(self, name: str = None, execute: Callable = None, *args, **kwargs):
        super().__init__(name, execute, *args, **kwargs)
        self._backup: Optional[CodemodBackup] = None
        self._validation_rules: List[Callable[[Codebase], bool]] = []
        self.logger = logging.getLogger(f"codemod.{name or self.__class__.__name__}")
        self._dry_run = False
    
    def add_validation_rule(self, rule: Callable[[Codebase], bool], description: str = "") -> None:
        """Add a pre-transformation validation rule."""
        rule.description = description
        self._validation_rules.append(rule)
    
    def create_backup(self, codebase: Codebase) -> None:
        """Create a backup snapshot for rollback."""
        self._backup = CodemodBackup(codebase)
        self._backup.create_snapshot()
        self.logger.info(f"Created backup snapshot with {len(self._backup.file_snapshots)} files")
    
    def rollback(self, codebase: Codebase) -> None:
        """Rollback to the backup state."""
        if self._backup:
            self._backup.restore_snapshot()
            self.logger.info("Successfully rolled back to backup state")
        else:
            self.logger.warning("No backup available for rollback")
    
    def validate_preconditions(self, codebase: Codebase) -> None:
        """Run all validation rules before transformation."""
        for rule in self._validation_rules:
            try:
                if not rule(codebase):
                    description = getattr(rule, 'description', 'Unknown validation rule')
                    raise ValidationError(f"Pre-transformation validation failed: {description}")
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise
                raise ValidationError(f"Validation rule execution failed: {e}")
    
    def safe_execute(self, codebase: Codebase, dry_run: bool = False) -> Dict[str, Any]:
        """Execute codemod with safety mechanisms."""
        self._dry_run = dry_run
        start_time = time.time()
        
        try:
            # Pre-validation
            self.logger.info("Running pre-transformation validation")
            self.validate_preconditions(codebase)
            
            # Create backup (skip for dry run)
            if not dry_run:
                self.create_backup(codebase)
            
            # Execute transformation
            self.logger.info(f"Starting transformation (dry_run={dry_run})")
            if self.execute:
                result = self.execute(codebase)
            else:
                result = None
            
            execution_time = time.time() - start_time
            self.logger.info(f"Transformation completed successfully in {execution_time:.2f}s")
            
            return {
                'status': 'success',
                'execution_time': execution_time,
                'dry_run': dry_run,
                'result': result
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Transformation failed after {execution_time:.2f}s: {e}")
            
            # Rollback on failure (skip for dry run)
            if not dry_run and self._backup:
                try:
                    self.rollback(codebase)
                    self.logger.info("Rollback completed successfully")
                except Exception as rollback_error:
                    self.logger.error(f"Rollback failed: {rollback_error}")
            
            return {
                'status': 'error',
                'execution_time': execution_time,
                'error': str(e),
                'error_type': type(e).__name__,
                'dry_run': dry_run
            }


class OptimizedCodemod(SafeCodemod):
    """Codemod with performance optimizations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_filters: List[Callable[[File], bool]] = []
        self._parallel_safe = False
        self._max_workers = 4
        self._batch_size = 10
    
    def add_file_filter(self, filter_func: Callable[[File], bool], description: str = "") -> None:
        """Add a file filter to reduce processing scope."""
        filter_func.description = description
        self._file_filters.append(filter_func)
    
    def set_parallel_safe(self, parallel_safe: bool = True, max_workers: int = 4) -> None:
        """Configure parallel processing settings."""
        self._parallel_safe = parallel_safe
        self._max_workers = max_workers
    
    def get_target_files(self, codebase: Codebase) -> List[File]:
        """Get filtered list of files to process."""
        files = list(codebase.files)
        initial_count = len(files)
        
        for filter_func in self._file_filters:
            files = [f for f in files if filter_func(f)]
            description = getattr(filter_func, 'description', 'Unknown filter')
            self.logger.debug(f"Filter '{description}': {len(files)} files remaining")
        
        self.logger.info(f"File filtering: {initial_count} -> {len(files)} files ({len(files)/initial_count*100:.1f}%)")
        return files
    
    def transform_file(self, file: File) -> Dict[str, Any]:
        """Transform a single file. Override this method for file-level transformations."""
        # Default implementation - subclasses should override
        return {'status': 'skipped', 'reason': 'No file-level transformation defined'}
    
    def execute_parallel(self, codebase: Codebase) -> Dict[str, Any]:
        """Execute transformation in parallel for thread-safe operations."""
        if not self._parallel_safe:
            raise RuntimeError("Codemod is not marked as parallel-safe")
        
        target_files = self.get_target_files(codebase)
        results = {'successful': [], 'failed': [], 'skipped': []}
        
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit file transformation tasks
            future_to_file = {
                executor.submit(self.transform_file, file): file 
                for file in target_files
            }
            
            # Collect results
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    if result['status'] == 'success':
                        results['successful'].append(file.filepath)
                    elif result['status'] == 'failed':
                        results['failed'].append((file.filepath, result.get('error', 'Unknown error')))
                    else:
                        results['skipped'].append(file.filepath)
                except Exception as e:
                    results['failed'].append((file.filepath, str(e)))
        
        return results


class RobustCodemod(OptimizedCodemod):
    """Codemod with comprehensive error handling and recovery."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._continue_on_error = True
        self._max_failures = None
        self._failure_threshold = 0.5  # Stop if more than 50% of files fail
    
    def set_error_handling(self, continue_on_error: bool = True, max_failures: Optional[int] = None, 
                          failure_threshold: float = 0.5) -> None:
        """Configure error handling behavior."""
        self._continue_on_error = continue_on_error
        self._max_failures = max_failures
        self._failure_threshold = failure_threshold
    
    def execute_with_recovery(self, codebase: Codebase) -> Dict[str, Any]:
        """Execute transformation with comprehensive error handling."""
        target_files = self.get_target_files(codebase)
        results = {
            'successful': [],
            'failed': [],
            'skipped': [],
            'total_files': len(target_files),
            'start_time': time.time()
        }
        
        failure_count = 0
        
        for i, file in enumerate(target_files):
            try:
                # Check failure thresholds
                if self._max_failures and failure_count >= self._max_failures:
                    self.logger.warning(f"Stopping due to max failures ({self._max_failures}) reached")
                    results['skipped'].extend([f.filepath for f in target_files[i:]])
                    break
                
                if i > 0:  # Avoid division by zero
                    current_failure_rate = failure_count / i
                    if current_failure_rate > self._failure_threshold:
                        self.logger.warning(f"Stopping due to high failure rate ({current_failure_rate:.2%})")
                        results['skipped'].extend([f.filepath for f in target_files[i:]])
                        break
                
                # Transform file
                result = self.transform_file(file)
                
                if result['status'] == 'success':
                    results['successful'].append(file.filepath)
                    self.logger.debug(f"Successfully transformed {file.filepath}")
                else:
                    results['failed'].append((file.filepath, result.get('error', 'Unknown error')))
                    failure_count += 1
                    self.logger.warning(f"Failed to transform {file.filepath}: {result.get('error')}")
                
            except Exception as e:
                failure_count += 1
                error_msg = str(e)
                results['failed'].append((file.filepath, error_msg))
                self.logger.error(f"Exception transforming {file.filepath}: {error_msg}")
                
                if not self._continue_on_error:
                    self.logger.error("Stopping due to error (continue_on_error=False)")
                    results['skipped'].extend([f.filepath for f in target_files[i+1:]])
                    break
        
        # Calculate final metrics
        results['execution_time'] = time.time() - results['start_time']
        results['success_rate'] = len(results['successful']) / results['total_files'] if results['total_files'] > 0 else 0
        results['failure_rate'] = len(results['failed']) / results['total_files'] if results['total_files'] > 0 else 0
        
        self.logger.info(f"Transformation completed: {len(results['successful'])} successful, "
                        f"{len(results['failed'])} failed, {len(results['skipped'])} skipped "
                        f"(success rate: {results['success_rate']:.2%})")
        
        return results


# Common validation rules
def validate_git_clean(codebase: Codebase) -> bool:
    """Validate that git working directory is clean."""
    # This would need integration with git status checking
    return True  # Placeholder implementation


def validate_syntax_valid(codebase: Codebase) -> bool:
    """Validate that all files have valid syntax."""
    for file in codebase.files:
        if not file.is_valid_syntax():
            return False
    return True


def validate_no_uncommitted_changes(codebase: Codebase) -> bool:
    """Validate that there are no uncommitted changes."""
    # This would need integration with git status checking
    return True  # Placeholder implementation


# Common file filters
def filter_by_extension(extensions: List[str]) -> Callable[[File], bool]:
    """Create a filter for specific file extensions."""
    def filter_func(file: File) -> bool:
        return any(file.filepath.endswith(ext) for ext in extensions)
    filter_func.description = f"Files with extensions: {', '.join(extensions)}"
    return filter_func


def filter_by_size(max_lines: int) -> Callable[[File], bool]:
    """Create a filter for files under a certain size."""
    def filter_func(file: File) -> bool:
        return len(file.content.splitlines()) <= max_lines
    filter_func.description = f"Files with <= {max_lines} lines"
    return filter_func


def filter_by_pattern(pattern: str) -> Callable[[File], bool]:
    """Create a filter for files matching a pattern."""
    import re
    regex = re.compile(pattern)
    
    def filter_func(file: File) -> bool:
        return bool(regex.search(file.filepath))
    filter_func.description = f"Files matching pattern: {pattern}"
    return filter_func

