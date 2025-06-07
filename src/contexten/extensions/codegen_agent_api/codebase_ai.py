"""
CodebaseAI interface for the Codegen Agent API extension.

Provides a direct function call interface similar to codebase.ai while using the Agent pattern internally.
Migrated from src/codegen/codebase_ai.py with contexten extension integration.
"""

from typing import Any, Dict, Optional, Union, List
import json
import logging
from .agent import Agent
from .task import Task
from .types import TaskPriority, CodebaseAITarget, CodebaseAIContext, CodebaseAIRequest
from .exceptions import ValidationError, TimeoutError as CodegenTimeoutError

logger = logging.getLogger(__name__)


class CodebaseAI:
    """
    CodebaseAI interface for direct function calls with contexten extension integration.
    
    Usage:
        codebase_ai = CodebaseAI(org_id="323", token="sk-...")
        
        # Function improvement
        result = codebase_ai(
            "Improve this function's implementation",
            target=function,
            context=context
        )
        
        # Method summary
        summary = codebase_ai(
            "Generate a summary of this method's purpose",
            target=method,
            context={
                "class": method.parent,
                "usages": list(method.usages),
                "dependencies": method.dependencies,
                "style": "concise"
            }
        )
    """
    
    def __init__(
        self,
        org_id: str,
        token: str,
        base_url: Optional[str] = None,
        timeout: int = 300,
        **kwargs
    ):
        """
        Initialize CodebaseAI interface.
        
        Args:
            org_id: Codegen organization ID
            token: Codegen API token
            base_url: Optional base URL override
            timeout: Default timeout for operations
            **kwargs: Additional Agent configuration
        """
        self.agent = Agent(
            org_id=org_id,
            token=token,
            base_url=base_url,
            timeout=timeout,
            validate_on_init=False,
            **kwargs
        )
        self.default_timeout = timeout
        
        logger.info(f"CodebaseAI initialized for org {org_id} (contexten extension)")
    
    def __call__(
        self,
        prompt: str,
        target: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        priority: Union[str, TaskPriority] = TaskPriority.NORMAL,
        wait_for_completion: bool = True,
        **kwargs
    ) -> Union[str, Dict[str, Any], Task]:
        """
        Direct function call interface like codebase.ai.
        
        Args:
            prompt: The instruction or query
            target: Target object (function, method, class, etc.)
            context: Additional context information
            timeout: Operation timeout
            priority: Task priority
            wait_for_completion: Whether to wait for task completion
            **kwargs: Additional parameters
            
        Returns:
            Result string, dict, or Task object depending on configuration
        """
        # Validate inputs
        if not prompt or not isinstance(prompt, str):
            raise ValidationError("prompt must be a non-empty string", field="prompt")
        
        # Convert string priority to enum if needed
        if isinstance(priority, str):
            try:
                priority = TaskPriority(priority.lower())
            except ValueError:
                raise ValidationError(
                    f"priority must be one of {[p.value for p in TaskPriority]}", 
                    field="priority"
                )
        
        # Enhance prompt with target and context information
        enhanced_prompt = self._enhance_prompt(prompt, target, context)
        
        # Create and execute task
        task = self.agent.run(
            prompt=enhanced_prompt,
            priority=priority,
            timeout=timeout or self.default_timeout,
            **kwargs
        )
        
        if wait_for_completion:
            # Wait for completion and return result
            return self._wait_and_extract_result(task, timeout or self.default_timeout)
        else:
            # Return task for manual monitoring
            return task
    
    def _enhance_prompt(
        self,
        prompt: str,
        target: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Enhance prompt with target and context information."""
        enhanced = prompt
        
        # Add target information
        if target is not None:
            enhanced += "\\n\\n## Target Information\\n"
            enhanced += self._format_target(target)
        
        # Add context information
        if context:
            enhanced += "\\n\\n## Context Information\\n"
            enhanced += self._format_context(context)
        
        # Add codebase.ai style guidelines
        enhanced += "\\n\\n## Guidelines\\n"
        enhanced += "- Provide precise, actionable results\\n"
        enhanced += "- Consider the target's structure and dependencies\\n"
        enhanced += "- Use the provided context to inform your response\\n"
        enhanced += "- Focus on practical, implementable solutions\\n"
        enhanced += "- This request is processed by the contexten codegen extension\\n"
        
        return enhanced
    
    def _format_target(self, target: Any) -> str:
        """Format target information for the prompt."""
        if isinstance(target, dict):
            # Handle dictionary-based targets (like function metadata)
            formatted = ""
            for key, value in target.items():
                if key == "source" and isinstance(value, str):
                    formatted += f"**{key.title()}:**\\n```\\n{value}\\n```\\n\\n"
                else:
                    formatted += f"**{key.title()}:** {value}\\n"
            return formatted
        
        elif hasattr(target, '__dict__'):
            # Handle object-based targets
            formatted = f"**Type:** {type(target).__name__}\\n"
            for attr, value in target.__dict__.items():
                if not attr.startswith('_'):
                    formatted += f"**{attr.title()}:** {value}\\n"
            return formatted
        
        elif isinstance(target, str):
            # Handle string targets (like code snippets)
            return f"**Code:**\\n```\\n{target}\\n```\\n"
        
        else:
            # Handle other types
            return f"**Target:** {str(target)}\\n"
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for the prompt."""
        formatted = ""
        
        for key, value in context.items():
            if isinstance(value, (list, tuple)):
                formatted += f"**{key.title()}:**\\n"
                for item in value:
                    formatted += f"- {item}\\n"
                formatted += "\\n"
            elif isinstance(value, dict):
                formatted += f"**{key.title()}:**\\n"
                for sub_key, sub_value in value.items():
                    formatted += f"- {sub_key}: {sub_value}\\n"
                formatted += "\\n"
            else:
                formatted += f"**{key.title()}:** {value}\\n"
        
        return formatted
    
    def _wait_and_extract_result(self, task: Task, timeout: int) -> Union[str, Dict[str, Any]]:
        """Wait for task completion and extract result."""
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            task.refresh()
            
            if task.status == "completed":
                result = task.result
                
                # Try to extract the most relevant part of the result
                if isinstance(result, dict):
                    # Look for common result keys
                    for key in ['result', 'output', 'response', 'content']:
                        if key in result:
                            return result[key]
                    return result
                else:
                    return result
            
            elif task.status == "failed":
                error_msg = getattr(task, 'error', 'Task failed')
                raise RuntimeError(f"Task failed: {error_msg}")
            
            elif task.status == "cancelled":
                raise RuntimeError("Task was cancelled")
            
            elif task.status == "timeout":
                raise CodegenTimeoutError("Task timed out on server")
            
            # Wait before next check
            time.sleep(1.0)
        
        raise CodegenTimeoutError(f"Task timed out after {timeout} seconds")
    
    # Convenience methods for common operations
    def improve_function(
        self,
        function: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Improve a function's implementation."""
        return self(
            "Improve this function's implementation",
            target=function,
            context=context,
            **kwargs
        )
    
    def summarize_method(
        self,
        method: Any,
        style: str = "concise",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Generate a summary of a method's purpose."""
        context = context or {}
        context["style"] = style
        
        return self(
            "Generate a summary of this method's purpose",
            target=method,
            context=context,
            **kwargs
        )
    
    def analyze_codebase(
        self,
        codebase_info: Dict[str, Any],
        analysis_type: str = "comprehensive",
        **kwargs
    ) -> str:
        """Analyze a codebase."""
        return self(
            f"Perform {analysis_type} analysis of this codebase",
            target=codebase_info,
            context={"analysis_type": analysis_type},
            **kwargs
        )
    
    def generate_docs(
        self,
        target: Any,
        doc_type: str = "comprehensive",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Generate documentation for code."""
        context = context or {}
        context["doc_type"] = doc_type
        
        return self(
            f"Generate {doc_type} documentation",
            target=target,
            context=context,
            **kwargs
        )
    
    def refactor_code(
        self,
        code: Any,
        refactor_type: str = "improve",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Refactor code."""
        context = context or {}
        context["refactor_type"] = refactor_type
        
        return self(
            f"Refactor this code to {refactor_type}",
            target=code,
            context=context,
            **kwargs
        )
    
    def explain_code(
        self,
        code: Any,
        explanation_level: str = "detailed",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Explain code functionality."""
        context = context or {}
        context["explanation_level"] = explanation_level
        
        return self(
            f"Provide a {explanation_level} explanation of this code",
            target=code,
            context=context,
            **kwargs
        )
    
    def find_bugs(
        self,
        code: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Find potential bugs in code."""
        return self(
            "Analyze this code for potential bugs and issues",
            target=code,
            context=context,
            **kwargs
        )
    
    def optimize_performance(
        self,
        code: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Optimize code for performance."""
        return self(
            "Optimize this code for better performance",
            target=code,
            context=context,
            **kwargs
        )
    
    def add_tests(
        self,
        code: Any,
        test_type: str = "unit",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Generate tests for code."""
        context = context or {}
        context["test_type"] = test_type
        
        return self(
            f"Generate {test_type} tests for this code",
            target=code,
            context=context,
            **kwargs
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get CodebaseAI statistics."""
        agent_stats = self.agent.get_stats()
        return {
            "codebase_ai": {
                "default_timeout": self.default_timeout,
                "agent_stats": agent_stats
            }
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"CodebaseAI(org_id={self.agent.org_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"CodebaseAI(org_id={self.agent.org_id}, agent_requests={self.agent._request_count})"


# Global instance for convenience (similar to how codebase.ai might work)
_global_instance: Optional[CodebaseAI] = None


def initialize_codebase_ai(org_id: str, token: str, **kwargs) -> CodebaseAI:
    """Initialize global codebase.ai instance."""
    global _global_instance
    _global_instance = CodebaseAI(org_id=org_id, token=token, **kwargs)
    logger.info(f"Global CodebaseAI instance initialized for org {org_id}")
    return _global_instance


def codebase_ai(
    prompt: str,
    target: Optional[Any] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Union[str, Dict[str, Any]]:
    """
    Global codebase.ai function (requires initialization).
    
    Usage:
        # Initialize once
        initialize_codebase_ai(org_id="323", token="sk-...")
        
        # Use anywhere
        result = codebase_ai("Improve this function", target=function, context=context)
    """
    if _global_instance is None:
        raise RuntimeError(
            "codebase_ai not initialized. Call initialize_codebase_ai() first."
        )
    
    return _global_instance(prompt, target=target, context=context, **kwargs)


def get_global_instance() -> Optional[CodebaseAI]:
    """Get the global CodebaseAI instance."""
    return _global_instance


def reset_global_instance() -> None:
    """Reset the global CodebaseAI instance."""
    global _global_instance
    _global_instance = None
    logger.info("Global CodebaseAI instance reset")


# Convenience functions for common patterns
def improve_function(function: Any, context: Optional[Dict[str, Any]] = None, **kwargs):
    """Improve a function's implementation."""
    return codebase_ai(
        "Improve this function's implementation",
        target=function,
        context=context,
        **kwargs
    )


def summarize_method(method: Any, style: str = "concise", **kwargs):
    """Generate a summary of a method's purpose."""
    return codebase_ai(
        "Generate a summary of this method's purpose",
        target=method,
        context={"style": style},
        **kwargs
    )


def analyze_codebase(codebase_info: Dict[str, Any], analysis_type: str = "comprehensive", **kwargs):
    """Analyze a codebase."""
    return codebase_ai(
        f"Perform {analysis_type} analysis of this codebase",
        target=codebase_info,
        context={"analysis_type": analysis_type},
        **kwargs
    )


def generate_docs(target: Any, doc_type: str = "comprehensive", **kwargs):
    """Generate documentation for code."""
    return codebase_ai(
        f"Generate {doc_type} documentation",
        target=target,
        context={"doc_type": doc_type},
        **kwargs
    )


def refactor_code(code: Any, refactor_type: str = "improve", **kwargs):
    """Refactor code."""
    return codebase_ai(
        f"Refactor this code to {refactor_type}",
        target=code,
        context={"refactor_type": refactor_type},
        **kwargs
    )


def explain_code(code: Any, explanation_level: str = "detailed", **kwargs):
    """Explain code functionality."""
    return codebase_ai(
        f"Provide a {explanation_level} explanation of this code",
        target=code,
        context={"explanation_level": explanation_level},
        **kwargs
    )


def find_bugs(code: Any, **kwargs):
    """Find potential bugs in code."""
    return codebase_ai(
        "Analyze this code for potential bugs and issues",
        target=code,
        **kwargs
    )


def optimize_performance(code: Any, **kwargs):
    """Optimize code for performance."""
    return codebase_ai(
        "Optimize this code for better performance",
        target=code,
        **kwargs
    )


def add_tests(code: Any, test_type: str = "unit", **kwargs):
    """Generate tests for code."""
    return codebase_ai(
        f"Generate {test_type} tests for this code",
        target=code,
        context={"test_type": test_type},
        **kwargs
    )


# Export all classes and functions
__all__ = [
    # Main class
    "CodebaseAI",
    
    # Global instance management
    "initialize_codebase_ai",
    "codebase_ai",
    "get_global_instance",
    "reset_global_instance",
    
    # Convenience functions
    "improve_function",
    "summarize_method",
    "analyze_codebase",
    "generate_docs",
    "refactor_code",
    "explain_code",
    "find_bugs",
    "optimize_performance",
    "add_tests",
]

