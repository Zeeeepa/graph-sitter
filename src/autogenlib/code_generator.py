"""
Code Generator for Autogenlib
On-demand code generation with intelligent context management
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path
import json
import hashlib

from .codegen_client import CodegenClient

logger = logging.getLogger(__name__)


class CodeGenerator:
    """
    Advanced code generation engine with intelligent context management
    
    Provides:
    - Template-based code generation
    - Context-aware prompt enhancement
    - Multi-language support
    - Code quality validation
    - Incremental generation
    - Pattern recognition
    """
    
    def __init__(self, codegen_client: CodegenClient):
        self.codegen_client = codegen_client
        self.templates: Dict[str, str] = {}
        self.generation_history: List[Dict[str, Any]] = []
        self.patterns: Dict[str, Any] = {}
        
        # Load built-in templates
        self._load_builtin_templates()
        
        logger.info("Code Generator initialized")
    
    def _load_builtin_templates(self):
        """Load built-in code generation templates"""
        self.templates.update({
            "python_function": """
Create a Python function with the following specifications:
- Function name: {function_name}
- Parameters: {parameters}
- Return type: {return_type}
- Description: {description}
- Include proper type hints and docstring
- Add error handling where appropriate
- Follow PEP 8 style guidelines
""",
            "python_class": """
Create a Python class with the following specifications:
- Class name: {class_name}
- Base classes: {base_classes}
- Attributes: {attributes}
- Methods: {methods}
- Description: {description}
- Include proper type hints and docstrings
- Add __init__ method with appropriate parameters
- Follow PEP 8 style guidelines
""",
            "test_suite": """
Create a comprehensive test suite for the following code:
{code_to_test}

Requirements:
- Use pytest framework
- Include unit tests for all public methods
- Add edge case testing
- Include error condition testing
- Aim for 100% code coverage
- Add proper test documentation
""",
            "api_endpoint": """
Create a REST API endpoint with the following specifications:
- Framework: {framework}
- Endpoint path: {path}
- HTTP method: {method}
- Request parameters: {parameters}
- Response format: {response_format}
- Description: {description}
- Include proper error handling
- Add input validation
- Include API documentation
""",
            "database_model": """
Create a database model with the following specifications:
- ORM: {orm}
- Model name: {model_name}
- Fields: {fields}
- Relationships: {relationships}
- Description: {description}
- Include proper constraints and validations
- Add indexes where appropriate
- Include model methods as needed
""",
            "react_component": """
Create a React component with the following specifications:
- Component name: {component_name}
- Props: {props}
- State: {state}
- Functionality: {functionality}
- Description: {description}
- Use TypeScript
- Include proper prop types
- Add error boundaries where appropriate
- Follow React best practices
""",
            "documentation": """
Create comprehensive documentation for the following code:
{code_to_document}

Include:
- Overview and purpose
- Installation instructions
- Usage examples
- API reference
- Configuration options
- Troubleshooting guide
- Contributing guidelines
Format as Markdown
"""
        })
    
    async def generate_from_template(
        self,
        template_name: str,
        template_vars: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate code using a predefined template
        
        Args:
            template_name: Name of the template to use
            template_vars: Variables to substitute in the template
            additional_context: Additional context for generation
        
        Returns:
            Generation result
        """
        if template_name not in self.templates:
            raise ValueError(f"Template not found: {template_name}")
        
        # Format template with variables
        try:
            prompt = self.templates[template_name].format(**template_vars)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
        
        # Combine context
        context = {
            "template_name": template_name,
            "template_vars": template_vars,
            **(additional_context or {})
        }
        
        # Generate code
        result = await self.codegen_client.generate_code(
            prompt=prompt,
            context=context
        )
        
        # Record generation
        self._record_generation(template_name, template_vars, result)
        
        return result
    
    async def generate_function(
        self,
        function_name: str,
        description: str,
        parameters: List[Dict[str, str]],
        return_type: str = "Any",
        language: str = "python"
    ) -> Dict[str, Any]:
        """Generate a function with specified parameters"""
        
        if language.lower() == "python":
            template_vars = {
                "function_name": function_name,
                "parameters": self._format_python_parameters(parameters),
                "return_type": return_type,
                "description": description
            }
            return await self.generate_from_template("python_function", template_vars)
        else:
            # Generic function generation
            prompt = f"""
Create a {language} function with the following specifications:
- Function name: {function_name}
- Description: {description}
- Parameters: {parameters}
- Return type: {return_type}

Include proper documentation and error handling.
"""
            return await self.codegen_client.generate_code(
                prompt=prompt,
                context={
                    "language": language,
                    "function_name": function_name,
                    "description": description
                }
            )
    
    async def generate_class(
        self,
        class_name: str,
        description: str,
        attributes: List[Dict[str, str]],
        methods: List[Dict[str, str]],
        base_classes: Optional[List[str]] = None,
        language: str = "python"
    ) -> Dict[str, Any]:
        """Generate a class with specified attributes and methods"""
        
        if language.lower() == "python":
            template_vars = {
                "class_name": class_name,
                "base_classes": base_classes or [],
                "attributes": attributes,
                "methods": methods,
                "description": description
            }
            return await self.generate_from_template("python_class", template_vars)
        else:
            # Generic class generation
            prompt = f"""
Create a {language} class with the following specifications:
- Class name: {class_name}
- Description: {description}
- Attributes: {attributes}
- Methods: {methods}
- Base classes: {base_classes or []}

Include proper documentation and best practices for {language}.
"""
            return await self.codegen_client.generate_code(
                prompt=prompt,
                context={
                    "language": language,
                    "class_name": class_name,
                    "description": description
                }
            )
    
    async def generate_tests(
        self,
        code_to_test: str,
        test_framework: str = "pytest",
        coverage_target: int = 100
    ) -> Dict[str, Any]:
        """Generate comprehensive tests for given code"""
        
        template_vars = {
            "code_to_test": code_to_test
        }
        
        context = {
            "test_framework": test_framework,
            "coverage_target": coverage_target
        }
        
        return await self.generate_from_template("test_suite", template_vars, context)
    
    async def generate_api_endpoint(
        self,
        path: str,
        method: str,
        description: str,
        parameters: Dict[str, Any],
        response_format: Dict[str, Any],
        framework: str = "fastapi"
    ) -> Dict[str, Any]:
        """Generate a REST API endpoint"""
        
        template_vars = {
            "framework": framework,
            "path": path,
            "method": method.upper(),
            "parameters": parameters,
            "response_format": response_format,
            "description": description
        }
        
        return await self.generate_from_template("api_endpoint", template_vars)
    
    async def generate_database_model(
        self,
        model_name: str,
        fields: List[Dict[str, str]],
        relationships: Optional[List[Dict[str, str]]] = None,
        orm: str = "sqlalchemy"
    ) -> Dict[str, Any]:
        """Generate a database model"""
        
        template_vars = {
            "orm": orm,
            "model_name": model_name,
            "fields": fields,
            "relationships": relationships or [],
            "description": f"Database model for {model_name}"
        }
        
        return await self.generate_from_template("database_model", template_vars)
    
    async def generate_react_component(
        self,
        component_name: str,
        props: Dict[str, str],
        functionality: str,
        state: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate a React component"""
        
        template_vars = {
            "component_name": component_name,
            "props": props,
            "state": state or {},
            "functionality": functionality,
            "description": f"React component: {component_name}"
        }
        
        return await self.generate_from_template("react_component", template_vars)
    
    async def generate_documentation(
        self,
        code_to_document: str,
        doc_type: str = "api"
    ) -> Dict[str, Any]:
        """Generate documentation for code"""
        
        template_vars = {
            "code_to_document": code_to_document
        }
        
        context = {
            "documentation_type": doc_type
        }
        
        return await self.generate_from_template("documentation", template_vars, context)
    
    async def generate_from_description(
        self,
        description: str,
        language: str = "python",
        code_type: str = "function"
    ) -> Dict[str, Any]:
        """Generate code from natural language description"""
        
        prompt = f"""
Based on the following description, create {code_type} in {language}:

{description}

Requirements:
- Follow best practices for {language}
- Include proper documentation
- Add error handling where appropriate
- Use appropriate design patterns
- Ensure code is production-ready
"""
        
        context = {
            "language": language,
            "code_type": code_type,
            "description": description
        }
        
        result = await self.codegen_client.generate_code(
            prompt=prompt,
            context=context
        )
        
        # Record generation
        self._record_generation("description_based", {
            "description": description,
            "language": language,
            "code_type": code_type
        }, result)
        
        return result
    
    async def improve_code(
        self,
        existing_code: str,
        improvement_goals: List[str],
        language: str = "python"
    ) -> Dict[str, Any]:
        """Improve existing code based on specified goals"""
        
        goals_text = "\n".join(f"- {goal}" for goal in improvement_goals)
        
        prompt = f"""
Improve the following {language} code based on these goals:
{goals_text}

Original code:
```{language}
{existing_code}
```

Provide the improved code with explanations of changes made.
"""
        
        context = {
            "language": language,
            "improvement_goals": improvement_goals,
            "original_code": existing_code
        }
        
        return await self.codegen_client.generate_code(
            prompt=prompt,
            context=context
        )
    
    async def generate_missing_code(
        self,
        codebase_context: str,
        missing_functionality: str,
        integration_points: List[str]
    ) -> Dict[str, Any]:
        """Generate missing code to complete functionality"""
        
        prompt = f"""
Based on the existing codebase context, generate the missing code for:
{missing_functionality}

Codebase context:
{codebase_context}

Integration points:
{chr(10).join(f"- {point}" for point in integration_points)}

Ensure the generated code:
- Integrates seamlessly with existing code
- Follows the same patterns and conventions
- Includes proper error handling
- Is well-documented
- Includes appropriate tests
"""
        
        context = {
            "codebase_context": codebase_context,
            "missing_functionality": missing_functionality,
            "integration_points": integration_points
        }
        
        return await self.codegen_client.generate_code(
            prompt=prompt,
            context=context
        )
    
    def add_template(self, name: str, template: str):
        """Add a custom template"""
        self.templates[name] = template
        logger.info(f"Added custom template: {name}")
    
    def get_templates(self) -> List[str]:
        """Get list of available templates"""
        return list(self.templates.keys())
    
    def get_generation_history(self) -> List[Dict[str, Any]]:
        """Get generation history"""
        return self.generation_history.copy()
    
    def _format_python_parameters(self, parameters: List[Dict[str, str]]) -> str:
        """Format parameters for Python function"""
        if not parameters:
            return ""
        
        param_strings = []
        for param in parameters:
            name = param.get("name", "")
            param_type = param.get("type", "Any")
            default = param.get("default")
            
            if default:
                param_strings.append(f"{name}: {param_type} = {default}")
            else:
                param_strings.append(f"{name}: {param_type}")
        
        return ", ".join(param_strings)
    
    def _record_generation(
        self,
        template_name: str,
        template_vars: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """Record generation for history and pattern analysis"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "template_name": template_name,
            "template_vars": template_vars,
            "success": result.get("status") == "success",
            "result_hash": self._hash_result(result)
        }
        
        self.generation_history.append(record)
        
        # Keep only last 1000 records
        if len(self.generation_history) > 1000:
            self.generation_history = self.generation_history[-1000:]
    
    def _hash_result(self, result: Dict[str, Any]) -> str:
        """Generate hash of result for deduplication"""
        result_str = json.dumps(result, sort_keys=True, default=str)
        return hashlib.sha256(result_str.encode()).hexdigest()[:16]

