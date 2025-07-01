"""Test suite for enhanced codemod framework.

Tests safety mechanisms, performance optimizations, and error handling
capabilities of the enhanced codemod framework.
"""

import pytest
import tempfile
import time
from unittest.mock import Mock, MagicMock, patch

from codemods.enhanced_codemod import (
    SafeCodemod, OptimizedCodemod, RobustCodemod,
    ValidationError, TransformationError, CodemodBackup,
    validate_syntax_valid, filter_by_extension, filter_by_size
)
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import File


class TestCodemodBackup:
    """Test backup and rollback functionality."""
    
    def test_backup_creation(self):
        """Test that backup snapshots are created correctly."""
        # Mock codebase and files
        mock_codebase = Mock(spec=Codebase)
        mock_file1 = Mock(spec=File)
        mock_file1.filepath = "test1.py"
        mock_file1.content = "print('hello')"
        mock_file2 = Mock(spec=File)
        mock_file2.filepath = "test2.py"
        mock_file2.content = "print('world')"
        mock_codebase.files = [mock_file1, mock_file2]
        
        # Create backup
        backup = CodemodBackup(mock_codebase)
        backup.create_snapshot()
        
        # Verify snapshot was created
        assert len(backup.file_snapshots) == 2
        assert backup.file_snapshots["test1.py"] == "print('hello')"
        assert backup.file_snapshots["test2.py"] == "print('world')"
    
    def test_backup_restore(self):
        """Test that backup restoration works correctly."""
        # Mock codebase and files
        mock_codebase = Mock(spec=Codebase)
        mock_file = Mock(spec=File)
        mock_file.filepath = "test.py"
        mock_file.content = "original content"
        mock_codebase.files = [mock_file]
        mock_codebase.get_file.return_value = mock_file
        
        # Create backup
        backup = CodemodBackup(mock_codebase)
        backup.create_snapshot()
        
        # Modify file content
        mock_file.content = "modified content"
        
        # Restore backup
        backup.restore_snapshot()
        
        # Verify content was restored
        assert mock_file.content == "original content"


class TestSafeCodemod:
    """Test SafeCodemod functionality."""
    
    def test_validation_rule_addition(self):
        """Test adding validation rules."""
        codemod = SafeCodemod("test_codemod")
        
        def dummy_rule(codebase):
            return True
        
        codemod.add_validation_rule(dummy_rule, "Test rule")
        assert len(codemod._validation_rules) == 1
        assert codemod._validation_rules[0] == dummy_rule
    
    def test_validation_success(self):
        """Test successful validation."""
        codemod = SafeCodemod("test_codemod")
        mock_codebase = Mock(spec=Codebase)
        
        def passing_rule(codebase):
            return True
        
        codemod.add_validation_rule(passing_rule, "Passing rule")
        
        # Should not raise exception
        codemod.validate_preconditions(mock_codebase)
    
    def test_validation_failure(self):
        """Test validation failure."""
        codemod = SafeCodemod("test_codemod")
        mock_codebase = Mock(spec=Codebase)
        
        def failing_rule(codebase):
            return False
        
        codemod.add_validation_rule(failing_rule, "Failing rule")
        
        # Should raise ValidationError
        with pytest.raises(ValidationError, match="Failing rule"):
            codemod.validate_preconditions(mock_codebase)
    
    def test_safe_execute_success(self):
        """Test successful safe execution."""
        def mock_execute(codebase):
            return "success"
        
        codemod = SafeCodemod("test_codemod", execute=mock_execute)
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.files = []
        
        result = codemod.safe_execute(mock_codebase)
        
        assert result['status'] == 'success'
        assert result['result'] == 'success'
        assert 'execution_time' in result
    
    def test_safe_execute_with_rollback(self):
        """Test safe execution with rollback on failure."""
        def failing_execute(codebase):
            raise Exception("Test failure")
        
        codemod = SafeCodemod("test_codemod", execute=failing_execute)
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.files = []
        
        with patch.object(codemod, 'rollback') as mock_rollback:
            result = codemod.safe_execute(mock_codebase)
            
            assert result['status'] == 'error'
            assert 'Test failure' in result['error']
            mock_rollback.assert_called_once()
    
    def test_dry_run_execution(self):
        """Test dry run execution."""
        def mock_execute(codebase):
            return "dry run result"
        
        codemod = SafeCodemod("test_codemod", execute=mock_execute)
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.files = []
        
        result = codemod.safe_execute(mock_codebase, dry_run=True)
        
        assert result['status'] == 'success'
        assert result['dry_run'] is True
        assert result['result'] == "dry run result"


class TestOptimizedCodemod:
    """Test OptimizedCodemod functionality."""
    
    def test_file_filter_addition(self):
        """Test adding file filters."""
        codemod = OptimizedCodemod("test_codemod")
        
        def dummy_filter(file):
            return True
        
        codemod.add_file_filter(dummy_filter, "Test filter")
        assert len(codemod._file_filters) == 1
        assert codemod._file_filters[0] == dummy_filter
    
    def test_file_filtering(self):
        """Test file filtering functionality."""
        codemod = OptimizedCodemod("test_codemod")
        
        # Mock files
        mock_file1 = Mock(spec=File)
        mock_file1.filepath = "test.py"
        mock_file2 = Mock(spec=File)
        mock_file2.filepath = "test.js"
        mock_file3 = Mock(spec=File)
        mock_file3.filepath = "test.py"
        
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.files = [mock_file1, mock_file2, mock_file3]
        
        # Add filter for Python files only
        codemod.add_file_filter(lambda f: f.filepath.endswith('.py'), "Python files")
        
        filtered_files = codemod.get_target_files(mock_codebase)
        
        assert len(filtered_files) == 2
        assert all(f.filepath.endswith('.py') for f in filtered_files)
    
    def test_parallel_processing_configuration(self):
        """Test parallel processing configuration."""
        codemod = OptimizedCodemod("test_codemod")
        
        # Initially not parallel safe
        assert codemod._parallel_safe is False
        
        # Configure for parallel processing
        codemod.set_parallel_safe(True, max_workers=8)
        
        assert codemod._parallel_safe is True
        assert codemod._max_workers == 8
    
    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_parallel_execution(self, mock_executor):
        """Test parallel execution functionality."""
        codemod = OptimizedCodemod("test_codemod")
        codemod.set_parallel_safe(True)
        
        # Mock files
        mock_files = [Mock(spec=File) for _ in range(3)]
        for i, file in enumerate(mock_files):
            file.filepath = f"test{i}.py"
        
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.files = mock_files
        
        # Mock transform_file method
        def mock_transform(file):
            return {'status': 'success', 'file': file.filepath}
        
        codemod.transform_file = mock_transform
        
        # Mock executor
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        
        # Mock futures
        mock_futures = []
        for file in mock_files:
            future = Mock()
            future.result.return_value = {'status': 'success', 'file': file.filepath}
            mock_futures.append(future)
        
        mock_executor_instance.submit.side_effect = mock_futures
        
        # Mock as_completed
        with patch('concurrent.futures.as_completed', return_value=mock_futures):
            results = codemod.execute_parallel(mock_codebase)
        
        assert len(results['successful']) == 3
        assert len(results['failed']) == 0


class TestRobustCodemod:
    """Test RobustCodemod functionality."""
    
    def test_error_handling_configuration(self):
        """Test error handling configuration."""
        codemod = RobustCodemod("test_codemod")
        
        # Configure error handling
        codemod.set_error_handling(
            continue_on_error=False,
            max_failures=5,
            failure_threshold=0.3
        )
        
        assert codemod._continue_on_error is False
        assert codemod._max_failures == 5
        assert codemod._failure_threshold == 0.3
    
    def test_execute_with_recovery_success(self):
        """Test successful execution with recovery."""
        codemod = RobustCodemod("test_codemod")
        
        # Mock files
        mock_files = [Mock(spec=File) for _ in range(3)]
        for i, file in enumerate(mock_files):
            file.filepath = f"test{i}.py"
        
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.files = mock_files
        
        # Mock successful transform_file
        def mock_transform(file):
            return {'status': 'success', 'file': file.filepath}
        
        codemod.transform_file = mock_transform
        
        results = codemod.execute_with_recovery(mock_codebase)
        
        assert results['total_files'] == 3
        assert len(results['successful']) == 3
        assert len(results['failed']) == 0
        assert results['success_rate'] == 1.0
    
    def test_execute_with_recovery_partial_failure(self):
        """Test execution with partial failures."""
        codemod = RobustCodemod("test_codemod")
        codemod.set_error_handling(continue_on_error=True, max_failures=10)
        
        # Mock files
        mock_files = [Mock(spec=File) for _ in range(5)]
        for i, file in enumerate(mock_files):
            file.filepath = f"test{i}.py"
        
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.files = mock_files
        
        # Mock transform_file with some failures
        def mock_transform(file):
            if "test1" in file.filepath or "test3" in file.filepath:
                return {'status': 'failed', 'error': 'Test error', 'file': file.filepath}
            return {'status': 'success', 'file': file.filepath}
        
        codemod.transform_file = mock_transform
        
        results = codemod.execute_with_recovery(mock_codebase)
        
        assert results['total_files'] == 5
        assert len(results['successful']) == 3
        assert len(results['failed']) == 2
        assert results['success_rate'] == 0.6
    
    def test_failure_threshold_stopping(self):
        """Test that execution stops when failure threshold is reached."""
        codemod = RobustCodemod("test_codemod")
        codemod.set_error_handling(
            continue_on_error=True,
            failure_threshold=0.3  # Stop if more than 30% fail
        )
        
        # Mock files
        mock_files = [Mock(spec=File) for _ in range(10)]
        for i, file in enumerate(mock_files):
            file.filepath = f"test{i}.py"
        
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.files = mock_files
        
        # Mock transform_file with high failure rate
        def mock_transform(file):
            # Fail first 4 files (40% failure rate)
            if int(file.filepath.split('test')[1].split('.')[0]) < 4:
                return {'status': 'failed', 'error': 'Test error', 'file': file.filepath}
            return {'status': 'success', 'file': file.filepath}
        
        codemod.transform_file = mock_transform
        
        results = codemod.execute_with_recovery(mock_codebase)
        
        # Should stop early due to high failure rate
        assert len(results['failed']) >= 3  # At least 3 failures before stopping
        assert len(results['skipped']) > 0  # Some files should be skipped


class TestBuiltinValidators:
    """Test built-in validation functions."""
    
    def test_validate_syntax_valid(self):
        """Test syntax validation."""
        mock_codebase = Mock(spec=Codebase)
        mock_file = Mock(spec=File)
        mock_file.is_valid_syntax.return_value = True
        mock_codebase.files = [mock_file]
        
        assert validate_syntax_valid(mock_codebase) is True
        
        # Test with invalid syntax
        mock_file.is_valid_syntax.return_value = False
        assert validate_syntax_valid(mock_codebase) is False


class TestBuiltinFilters:
    """Test built-in filter functions."""
    
    def test_filter_by_extension(self):
        """Test extension-based filtering."""
        filter_func = filter_by_extension(['.py', '.ts'])
        
        mock_file1 = Mock(spec=File)
        mock_file1.filepath = "test.py"
        mock_file2 = Mock(spec=File)
        mock_file2.filepath = "test.js"
        mock_file3 = Mock(spec=File)
        mock_file3.filepath = "test.ts"
        
        assert filter_func(mock_file1) is True
        assert filter_func(mock_file2) is False
        assert filter_func(mock_file3) is True
    
    def test_filter_by_size(self):
        """Test size-based filtering."""
        filter_func = filter_by_size(100)
        
        mock_file1 = Mock(spec=File)
        mock_file1.content = "\\n".join([f"line {i}" for i in range(50)])  # 50 lines
        mock_file2 = Mock(spec=File)
        mock_file2.content = "\\n".join([f"line {i}" for i in range(150)])  # 150 lines
        
        assert filter_func(mock_file1) is True
        assert filter_func(mock_file2) is False


class TestIntegration:
    """Integration tests for the enhanced codemod framework."""
    
    def test_full_workflow_with_all_features(self):
        """Test complete workflow with all enhanced features."""
        # Create a comprehensive codemod
        class TestCodemod(RobustCodemod):
            def __init__(self):
                super().__init__("integration_test_codemod")
                
                # Add validation
                self.add_validation_rule(lambda cb: True, "Always pass validation")
                
                # Add filters
                self.add_file_filter(filter_by_extension(['.py']), "Python files")
                
                # Configure error handling
                self.set_error_handling(continue_on_error=True, max_failures=5)
            
            def transform_file(self, file):
                return {'status': 'success', 'transformed': True}
        
        codemod = TestCodemod()
        
        # Mock codebase
        mock_files = []
        for i in range(5):
            mock_file = Mock(spec=File)
            mock_file.filepath = f"test{i}.py"
            mock_file.content = f"# Test file {i}"
            mock_files.append(mock_file)
        
        mock_codebase = Mock(spec=Codebase)
        mock_codebase.files = mock_files
        
        # Execute with safety features
        result = codemod.safe_execute(mock_codebase)
        
        assert result['status'] == 'success'
        assert 'execution_time' in result


if __name__ == "__main__":
    pytest.main([__file__])

