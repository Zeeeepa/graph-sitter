"""Main integration class for autogenlib with graph-sitter."""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from graph_sitter.core.interfaces.codebase import Codebase
from .config import AutogenLibConfig, GenerationRequest, GenerationResult
from .generator import EnhancedCodeGenerator
from .context_provider import GraphSitterContextProvider

logger = logging.getLogger(__name__)


class AutogenLibIntegration:
    """Main integration class that provides autogenlib functionality to graph-sitter."""
    
    def __init__(self, config: Optional[AutogenLibConfig] = None, codebase: Optional[Codebase] = None):
        self.config = config or AutogenLibConfig()
        self.codebase = codebase
        self.generator = None
        self.context_provider = None
        
        if self.config.enabled:
            self._initialize()
            
    def _initialize(self):
        """Initialize the integration components."""
        try:
            self.context_provider = GraphSitterContextProvider(self.config, self.codebase)
            self.generator = EnhancedCodeGenerator(self.config, self.codebase)
            logger.info("AutogenLib integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AutogenLib integration: {e}")
            raise
            
    def is_enabled(self) -> bool:
        """Check if the integration is enabled and properly initialized."""
        return self.config.enabled and self.generator is not None
        
    def generate_missing_implementation(
        self,
        module_name: str,
        function_name: Optional[str] = None,
        description: Optional[str] = None,
        existing_code: Optional[str] = None,
        caller_info: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """Generate missing implementation using enhanced context."""
        if not self.is_enabled():
            return GenerationResult(
                success=False,
                error="AutogenLib integration is not enabled or not properly initialized"
            )
            
        # Use default description if none provided
        if not description:
            if function_name:
                description = f"Implement the {function_name} function in the {module_name} module"
            else:
                description = f"Implement functionality for the {module_name} module"
                
        request = GenerationRequest(
            module_name=module_name,
            function_name=function_name,
            description=description,
            existing_code=existing_code,
            caller_info=caller_info
        )
        
        return self.generator.generate_code(request)
        
    def suggest_code_completion(
        self,
        context: str,
        cursor_position: int,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """Suggest code completions based on context."""
        if not self.is_enabled():
            return []
            
        suggestions = []
        
        try:
            # Analyze the context around the cursor
            lines = context.split('\n')
            current_line_idx = 0
            char_count = 0
            
            for i, line in enumerate(lines):
                if char_count + len(line) >= cursor_position:
                    current_line_idx = i
                    break
                char_count += len(line) + 1  # +1 for newline
                
            current_line = lines[current_line_idx] if current_line_idx < len(lines) else ""
            
            # Extract partial function/variable name
            line_up_to_cursor = current_line[:cursor_position - char_count]
            
            # Simple completion logic - this could be enhanced
            if "def " in line_up_to_cursor:
                # Function definition completion
                suggestions.append({
                    "type": "function",
                    "text": "def function_name(self, *args, **kwargs):\n    \"\"\"Function docstring.\"\"\"\n    pass",
                    "description": "Complete function definition",
                    "confidence": 0.8
                })
            elif "import " in line_up_to_cursor:
                # Import completion
                suggestions.append({
                    "type": "import",
                    "text": "from typing import Optional, Dict, Any",
                    "description": "Common typing imports",
                    "confidence": 0.7
                })
                
        except Exception as e:
            logger.error(f"Error generating code completions: {e}")
            
        return suggestions[:max_suggestions]
        
    def generate_refactoring_suggestions(
        self,
        code: str,
        target_pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate context-aware refactoring suggestions."""
        if not self.is_enabled():
            return []
            
        suggestions = []
        
        try:
            # Analyze the code for refactoring opportunities
            analysis = self.context_provider._analyze_existing_code(code)
            
            # Generate suggestions based on analysis
            if analysis.get("complexity", 0) > 10:
                suggestions.append({
                    "type": "complexity_reduction",
                    "description": "Consider breaking down complex functions",
                    "confidence": 0.8,
                    "details": f"Code complexity: {analysis['complexity']}"
                })
                
            if len(analysis.get("functions", [])) > 20:
                suggestions.append({
                    "type": "module_split",
                    "description": "Consider splitting this module into smaller modules",
                    "confidence": 0.7,
                    "details": f"Function count: {len(analysis['functions'])}"
                })
                
            # Check for missing docstrings
            functions_without_docs = [
                f for f in analysis.get("functions", []) 
                if not f.get("docstring")
            ]
            if functions_without_docs:
                suggestions.append({
                    "type": "documentation",
                    "description": "Add docstrings to functions",
                    "confidence": 0.9,
                    "details": f"Functions missing docstrings: {len(functions_without_docs)}"
                })
                
        except Exception as e:
            logger.error(f"Error generating refactoring suggestions: {e}")
            
        return suggestions
        
    def generate_template_code(
        self,
        template_type: str,
        parameters: Dict[str, Any]
    ) -> GenerationResult:
        """Generate code from templates with context awareness."""
        if not self.is_enabled():
            return GenerationResult(
                success=False,
                error="AutogenLib integration is not enabled"
            )
            
        template_descriptions = {
            "class": "Create a Python class with the specified attributes and methods",
            "function": "Create a Python function with the specified signature and behavior",
            "module": "Create a Python module with the specified functionality",
            "test": "Create unit tests for the specified code",
            "api_client": "Create an API client class with the specified endpoints",
            "data_model": "Create a data model class with the specified fields",
            "cli_command": "Create a CLI command with the specified options"
        }
        
        description = template_descriptions.get(template_type, f"Generate {template_type} code")
        
        # Enhance description with parameters
        if parameters:
            param_desc = ", ".join([f"{k}: {v}" for k, v in parameters.items()])
            description += f" with parameters: {param_desc}"
            
        module_name = parameters.get("module_name", f"autogenlib.generated.{template_type}")
        
        request = GenerationRequest(
            module_name=module_name,
            function_name=parameters.get("function_name"),
            description=description,
            context=parameters
        )
        
        return self.generator.generate_code(request)
        
    def get_generation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the history of code generations."""
        if not self.is_enabled():
            return []
            
        # This would integrate with the database to get real history
        # For now, return empty list
        return []
        
    def get_cached_modules(self) -> List[str]:
        """Get list of cached modules."""
        if not self.is_enabled():
            return []
            
        # This would integrate with autogenlib's cache
        return []
        
    def clear_cache(self, module_name: Optional[str] = None):
        """Clear the generation cache."""
        if self.is_enabled() and self.generator:
            self.generator.clear_cache(module_name)
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        if not self.is_enabled():
            return {"enabled": False}
            
        stats = {
            "enabled": True,
            "config": {
                "use_graph_sitter_context": self.config.use_graph_sitter_context,
                "enable_caching": self.config.enable_caching,
                "max_context_size": self.config.max_context_size
            }
        }
        
        if self.generator:
            stats.update(self.generator.get_generation_stats())
            
        return stats
        
    def update_config(self, new_config: AutogenLibConfig):
        """Update the configuration and reinitialize if necessary."""
        old_enabled = self.config.enabled
        self.config = new_config
        
        if new_config.enabled and not old_enabled:
            # Enable integration
            self._initialize()
        elif not new_config.enabled and old_enabled:
            # Disable integration
            self.generator = None
            self.context_provider = None
            logger.info("AutogenLib integration disabled")
        elif new_config.enabled and old_enabled:
            # Reinitialize with new config
            self._initialize()
            
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the current configuration."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if self.config.enabled:
            if not self.config.openai_api_key:
                validation["errors"].append("OpenAI API key is required when integration is enabled")
                validation["valid"] = False
                
            if self.config.max_context_size < 1000:
                validation["warnings"].append("Max context size is very small, may affect generation quality")
                
            if not self.config.allowed_namespaces:
                validation["warnings"].append("No allowed namespaces specified, generation allowed everywhere")
                
        return validation

