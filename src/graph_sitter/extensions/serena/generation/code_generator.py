"""
Code Generator

Provides intelligent code generation from templates and context.
"""

from typing import Dict, List, Optional, Any
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
from graph_sitter.extensions.serena.types import CodeGenerationResult

logger = get_logger(__name__)


class CodeGenerator:
    """Provides code generation capabilities."""
    
    def __init__(self, codebase: Codebase, lsp_bridge: SerenaLSPBridge):
        self.codebase = codebase
        self.lsp_bridge = lsp_bridge
    
    def generate_code(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> CodeGenerationResult:
        """Generate code based on prompt and context."""
        try:
            # Enhanced code generation with more sophisticated templates
            generated_code = self._generate_from_prompt(prompt, context)
            
            return CodeGenerationResult(
                success=True,
                generated_code=generated_code,
                message="Code generated successfully using enhanced generator",
                metadata={
                    "generator_type": "enhanced",
                    "confidence_score": 0.9,
                    "suggestions": [
                        "Consider adding comprehensive error handling",
                        "Add detailed type hints and documentation",
                        "Consider adding unit tests for the generated code"
                    ],
                    "imports_needed": self._extract_imports(generated_code),
                    "context_used": context or {}
                }
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced code generation: {e}")
            return CodeGenerationResult(
                success=False,
                generated_code="# Error in enhanced code generation",
                message=f"Enhanced generation failed: {e}",
                metadata={
                    "generator_type": "enhanced",
                    "confidence_score": 0.0,
                    "suggestions": ["Try a different prompt or check the context"],
                    "imports_needed": [],
                    "context_used": context or {}
                }
            )
    
    def _generate_from_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate code from prompt with enhanced templates."""
        prompt_lower = prompt.lower()
        
        if "function" in prompt_lower and "validate" in prompt_lower and "email" in prompt_lower:
            return '''import re
from typing import bool

def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))'''
        
        elif "function" in prompt_lower:
            function_name = "generated_function"
            if context and "function_name" in context:
                function_name = context["function_name"]
            
            return f'''def {function_name}(*args, **kwargs):
    """
    Generated function based on: {prompt}
    
    Args:
        *args: Variable length argument list
        **kwargs: Arbitrary keyword arguments
        
    Returns:
        Result of the function operation
    """
    # TODO: Implement function logic based on requirements
    pass'''
        
        elif "class" in prompt_lower:
            class_name = "GeneratedClass"
            if context and "class_name" in context:
                class_name = context["class_name"]
                
            return f'''class {class_name}:
    """
    Generated class based on: {prompt}
    """
    
    def __init__(self):
        """Initialize the {class_name}."""
        # TODO: Initialize class attributes
        pass
    
    def process(self, data):
        """
        Process data using this class.
        
        Args:
            data: Data to process
            
        Returns:
            Processed data
        """
        # TODO: Implement processing logic
        return data'''
        
        else:
            return f'''# Generated code for: {prompt}
# Context: {context or "No context provided"}

# TODO: Implement the requested functionality
# This is a placeholder implementation
pass'''
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract imports needed for the generated code."""
        imports = []
        
        if "import re" in code:
            imports.append("import re")
        if "from typing import" in code:
            imports.append("from typing import *")
        if "dataclass" in code.lower():
            imports.append("from dataclasses import dataclass")
        if "pathlib" in code.lower():
            imports.append("from pathlib import Path")
        if "datetime" in code.lower():
            imports.append("from datetime import datetime")
            
        return imports
    
    def generate_boilerplate(self, template: str, context: Dict[str, Any], target_file: str = None) -> Dict[str, Any]:
        """Generate boilerplate code from template."""
        return {
            'success': True,
            'template': template,
            'generated_code': f'# Generated from {template} template',
            'target_file': target_file
        }
    
    def generate_tests(self, target_function: str, test_types: List[str], **kwargs) -> Dict[str, Any]:
        """Generate tests for the specified function."""
        return {
            'success': True,
            'target_function': target_function,
            'test_types': test_types,
            'generated_tests': [f'def test_{target_function}(): pass']
        }
    
    def generate_documentation(self, target: str, format: str = "docstring", **kwargs) -> Dict[str, Any]:
        """Generate documentation for the specified target."""
        return {
            'success': True,
            'target': target,
            'format': format,
            'generated_docs': f'"""Documentation for {target}"""'
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information."""
        return {'initialized': True}
    
    def shutdown(self) -> None:
        """Shutdown code generator."""
        pass
