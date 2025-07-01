"""Enhanced code generator that combines autogenlib with graph-sitter analysis."""

import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import autogenlib
from autogenlib._generator import generate_code as autogenlib_generate_code
from autogenlib._cache import get_cached_code, cache_module

from .config import AutogenLibConfig, GenerationRequest, GenerationResult
from .context_provider import GraphSitterContextProvider
from graph_sitter.core.interfaces.codebase import Codebase

logger = logging.getLogger(__name__)


class EnhancedCodeGenerator:
    """Enhanced code generator that leverages both autogenlib and graph-sitter."""
    
    def __init__(self, config: AutogenLibConfig, codebase: Optional[Codebase] = None):
        self.config = config
        self.codebase = codebase
        self.context_provider = GraphSitterContextProvider(config, codebase)
        
        # Initialize autogenlib with our configuration
        self._initialize_autogenlib()
        
    def _initialize_autogenlib(self):
        """Initialize autogenlib with graph-sitter integration settings."""
        # Set up autogenlib configuration
        autogenlib.init(
            desc="Graph-sitter enhanced code generation system",
            enable_caching=self.config.enable_caching,
            enable_exception_handler=self.config.enable_exception_handler
        )
        
        # Set environment variables for autogenlib
        import os
        if self.config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.config.openai_api_key
        if self.config.openai_api_base_url:
            os.environ["OPENAI_API_BASE_URL"] = self.config.openai_api_base_url
        if self.config.openai_model:
            os.environ["OPENAI_MODEL"] = self.config.openai_model
            
    def generate_code(self, request: GenerationRequest) -> GenerationResult:
        """Generate code using enhanced context from graph-sitter."""
        start_time = time.time()
        
        try:
            # Check if generation is allowed for this namespace
            if not self._is_namespace_allowed(request.module_name):
                return GenerationResult(
                    success=False,
                    error=f"Generation not allowed for namespace: {request.module_name}",
                    generation_time=time.time() - start_time
                )
                
            # Get enhanced context
            enhanced_context = self.context_provider.get_enhanced_context(
                module_name=request.module_name,
                function_name=request.function_name,
                caller_info=request.caller_info,
                existing_code=request.existing_code
            )
            
            # Format context for autogenlib
            formatted_context = self.context_provider.format_context_for_autogenlib(enhanced_context)
            
            # Enhance the description with graph-sitter context
            enhanced_description = self._enhance_description(request.description, formatted_context)
            
            # Generate code using autogenlib with enhanced context
            generated_code = autogenlib_generate_code(
                description=enhanced_description,
                fullname=request.module_name,
                existing_code=request.existing_code,
                caller_info=request.caller_info
            )
            
            if generated_code:
                # Store generation history if enabled
                if self.config.store_generation_history:
                    self._store_generation_history(request, generated_code, enhanced_context)
                    
                # Extract and store patterns if enabled
                if self.config.store_patterns:
                    self._extract_and_store_patterns(request, generated_code, enhanced_context)
                    
                return GenerationResult(
                    success=True,
                    code=generated_code,
                    metadata={
                        "enhanced_context_used": True,
                        "context_size": len(formatted_context),
                        "patterns_detected": len(enhanced_context.get("patterns", {}).get("common_patterns", []))
                    },
                    context_used=enhanced_context,
                    generation_time=time.time() - start_time
                )
            else:
                return GenerationResult(
                    success=False,
                    error="Code generation failed - no code returned from autogenlib",
                    context_used=enhanced_context,
                    generation_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"Error generating code: {e}", exc_info=True)
            return GenerationResult(
                success=False,
                error=str(e),
                generation_time=time.time() - start_time
            )
            
    def _is_namespace_allowed(self, module_name: str) -> bool:
        """Check if code generation is allowed for the given namespace."""
        if not self.config.allowed_namespaces:
            return True
            
        for allowed_ns in self.config.allowed_namespaces:
            if module_name.startswith(allowed_ns):
                return True
                
        return False
        
    def _enhance_description(self, description: str, context: str) -> str:
        """Enhance the description with graph-sitter context."""
        if not context:
            return description
            
        enhanced = f"""
{description}

## Additional Context from Graph-Sitter Analysis:
{context}

Please use this context to generate code that:
1. Follows the patterns and conventions identified in the codebase
2. Is compatible with the existing architecture and dependencies
3. Matches the usage patterns shown in the caller analysis
4. Implements best practices based on similar functions in the codebase
"""
        
        # Truncate if too long
        if len(enhanced) > self.config.max_context_size:
            truncated_context = context[:self.config.max_context_size - len(description) - 200]
            enhanced = f"""
{description}

## Additional Context from Graph-Sitter Analysis (truncated):
{truncated_context}
...

Please use this context to generate appropriate code.
"""
        
        return enhanced
        
    def _store_generation_history(
        self, 
        request: GenerationRequest, 
        generated_code: str, 
        context: Dict[str, Any]
    ):
        """Store generation history in the database."""
        # This would integrate with graph-sitter's database system
        # For now, just log the generation
        logger.info(f"Generated code for {request.module_name}:{request.function_name}")
        logger.debug(f"Generated code length: {len(generated_code)} characters")
        
    def _extract_and_store_patterns(
        self, 
        request: GenerationRequest, 
        generated_code: str, 
        context: Dict[str, Any]
    ):
        """Extract and store successful patterns for future use."""
        # Analyze the generated code for patterns
        patterns = {
            "module_name": request.module_name,
            "function_name": request.function_name,
            "description_keywords": request.description.lower().split(),
            "code_patterns": self._extract_code_patterns(generated_code),
            "context_patterns": context.get("patterns", {})
        }
        
        # Store patterns (would integrate with database)
        logger.debug(f"Extracted patterns: {patterns}")
        
    def _extract_code_patterns(self, code: str) -> Dict[str, Any]:
        """Extract patterns from generated code."""
        import ast
        
        patterns = {
            "imports": [],
            "function_signatures": [],
            "error_handling": False,
            "docstrings": False,
            "type_hints": False
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    patterns["imports"].append(ast.unparse(node))
                elif isinstance(node, ast.FunctionDef):
                    patterns["function_signatures"].append({
                        "name": node.name,
                        "args": len(node.args.args),
                        "has_docstring": ast.get_docstring(node) is not None,
                        "has_type_hints": any(arg.annotation for arg in node.args.args) or node.returns is not None
                    })
                    if ast.get_docstring(node):
                        patterns["docstrings"] = True
                    if any(arg.annotation for arg in node.args.args) or node.returns:
                        patterns["type_hints"] = True
                elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                    patterns["error_handling"] = True
                    
        except SyntaxError:
            pass
            
        return patterns
        
    def get_cached_code(self, module_name: str) -> Optional[str]:
        """Get cached code for a module."""
        return get_cached_code(module_name)
        
    def clear_cache(self, module_name: Optional[str] = None):
        """Clear the generation cache."""
        if module_name:
            # Clear specific module cache
            autogenlib.set_caching(False)
            autogenlib.set_caching(True)
        else:
            # Clear all cache
            autogenlib.set_caching(False)
            autogenlib.set_caching(True)
            
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about code generation."""
        # This would integrate with the database to get real stats
        return {
            "total_generations": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_generation_time": 0.0,
            "most_common_patterns": [],
            "cache_hit_rate": 0.0
        }

