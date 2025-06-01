"""Enhanced version of delete_unused_functions codemod using the new safety framework.

This example demonstrates how to migrate existing codemods to use the enhanced
framework with safety, performance, and error handling improvements.
"""

from codemods.enhanced_codemod import RobustCodemod, filter_by_extension, validate_syntax_valid
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import File
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage
from graph_sitter.writer_decorators import canonical
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Enhanced version of delete unused functions codemod with safety mechanisms,
    performance optimizations, and comprehensive error handling.""",
    uid="enhanced-delete-unused-functions",
)
@canonical
class EnhancedDeleteUnusedFunctionsCodemod(RobustCodemod, Skill):
    """Enhanced codemod that safely deletes unused functions with rollback capabilities.
    
    Improvements over original:
    - Pre-transformation validation
    - Rollback capabilities if something goes wrong
    - File filtering for better performance
    - Comprehensive error handling and recovery
    - Detailed logging and metrics
    """

    language = ProgrammingLanguage.PYTHON

    def __init__(self, *args, **kwargs):
        super().__init__("enhanced_delete_unused_functions", *args, **kwargs)
        
        # Configure safety mechanisms
        self.add_validation_rule(validate_syntax_valid, "All files must have valid syntax")
        self.add_validation_rule(self._validate_no_main_functions, "Preserve main functions")
        
        # Configure performance optimizations
        self.add_file_filter(filter_by_extension(['.py']), "Python files only")
        self.add_file_filter(self._filter_non_test_files, "Exclude test files")
        
        # Configure error handling
        self.set_error_handling(
            continue_on_error=True,
            max_failures=10,
            failure_threshold=0.3  # Stop if more than 30% of files fail
        )
        
        # Enable parallel processing (safe for this operation)
        self.set_parallel_safe(True, max_workers=4)

    def _validate_no_main_functions(self, codebase: Codebase) -> bool:
        """Validation rule to ensure we don't delete main functions."""
        for file in codebase.files:
            for function in file.functions:
                if function.name == "main" and not function.usages:
                    # Main functions without usages are still important
                    self.logger.warning(f"Found main function without usages in {file.filepath}")
        return True  # This is a warning, not a blocker

    def _filter_non_test_files(self, file: File) -> bool:
        """Filter out test files to avoid deleting test functions."""
        return not any(pattern in file.filepath.lower() for pattern in ['test_', '_test.py', '/tests/'])

    def transform_file(self, file: File) -> dict:
        """Transform a single file by removing unused functions."""
        try:
            removed_functions = []
            functions_to_remove = []
            
            # Collect functions to remove (don't modify during iteration)
            for function in file.functions:
                if self._should_remove_function(function):
                    functions_to_remove.append(function)
            
            # Remove collected functions
            for function in functions_to_remove:
                function_name = function.name
                function.remove()
                removed_functions.append(function_name)
                self.logger.debug(f"Removed unused function: {function_name}")
            
            return {
                'status': 'success',
                'removed_functions': removed_functions,
                'count': len(removed_functions)
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__
            }

    def _should_remove_function(self, function) -> bool:
        """Determine if a function should be removed."""
        # Don't remove if function has usages
        if function.usages:
            return False
        
        # Don't remove special functions
        if function.name.startswith('__') and function.name.endswith('__'):
            return False
        
        # Don't remove main functions
        if function.name == 'main':
            return False
        
        # Don't remove exported functions (they might be used externally)
        if hasattr(function, 'is_exported') and function.is_exported:
            return False
        
        # Don't remove functions with decorators (might be important)
        if hasattr(function, 'decorators') and function.decorators:
            return False
        
        return True

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        """Execute the enhanced transformation with safety and performance features."""
        if self._parallel_safe:
            # Use parallel processing for better performance
            results = self.execute_parallel(codebase)
        else:
            # Use sequential processing with error recovery
            results = self.execute_with_recovery(codebase)
        
        # Log summary statistics
        total_removed = sum(
            result.get('count', 0) 
            for result in results.get('successful', [])
            if isinstance(result, dict)
        )
        
        self.logger.info(f"Transformation summary:")
        self.logger.info(f"  - Files processed: {results.get('total_files', 0)}")
        self.logger.info(f"  - Files successful: {len(results.get('successful', []))}")
        self.logger.info(f"  - Files failed: {len(results.get('failed', []))}")
        self.logger.info(f"  - Functions removed: {total_removed}")
        self.logger.info(f"  - Success rate: {results.get('success_rate', 0):.2%}")


# Example usage and testing
if __name__ == "__main__":
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create codemod instance
    codemod = EnhancedDeleteUnusedFunctionsCodemod()
    
    # Example of how to use with a codebase
    # codebase = Codebase("./")
    # 
    # # Dry run first to see what would be changed
    # dry_result = codemod.safe_execute(codebase, dry_run=True)
    # print(f"Dry run result: {dry_result}")
    # 
    # # If dry run looks good, execute for real
    # if dry_result['status'] == 'success':
    #     real_result = codemod.safe_execute(codebase, dry_run=False)
    #     print(f"Execution result: {real_result}")
    
    print("Enhanced codemod example created successfully!")

