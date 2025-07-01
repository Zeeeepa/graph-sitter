"""Context enhancement using existing codebase analysis functions."""

import logging
import os
from typing import Dict, List, Optional

from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary,
)

from .config import AutogenConfig
from .exceptions import ContextError
from .models import ContextData, TaskRequest

logger = logging.getLogger(__name__)


class ContextEnhancer:
    """Enhances prompts with codebase context using graph-sitter analysis."""
    
    def __init__(self, config: AutogenConfig):
        """Initialize the context enhancer.
        
        Args:
            config: Configuration object.
        """
        self.config = config
        self._codebase_cache: Dict[str, Codebase] = {}
    
    def enhance_prompt(self, request: TaskRequest) -> str:
        """Enhance a prompt with relevant codebase context.
        
        Args:
            request: Task request containing the original prompt.
            
        Returns:
            Enhanced prompt with codebase context.
            
        Raises:
            ContextError: If context enhancement fails.
        """
        if not self.config.enable_context_enhancement or not request.enhance_context:
            return request.prompt
        
        try:
            # Get codebase context
            context_data = self._get_context_data(request)
            
            # Build enhanced prompt
            enhanced_prompt = self._build_enhanced_prompt(request.prompt, context_data)
            
            # Ensure we don't exceed max context length
            if len(enhanced_prompt) > self.config.max_context_length:
                enhanced_prompt = self._truncate_context(enhanced_prompt, request.prompt)
            
            logger.info(f"Enhanced prompt from {len(request.prompt)} to {len(enhanced_prompt)} characters")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Failed to enhance prompt: {e}")
            if self.config.log_level == "DEBUG":
                raise ContextError(f"Context enhancement failed: {e}")
            else:
                # Fallback to original prompt if enhancement fails
                logger.warning("Falling back to original prompt due to context enhancement failure")
                return request.prompt
    
    def _get_context_data(self, request: TaskRequest) -> ContextData:
        """Get context data for the request.
        
        Args:
            request: Task request.
            
        Returns:
            ContextData object with relevant context information.
        """
        context_data = ContextData()
        
        if not request.codebase_path:
            return context_data
        
        try:
            # Get or load codebase
            codebase = self._get_codebase(request.codebase_path)
            
            # Get codebase summary
            if self.config.include_file_summaries:
                context_data.codebase_summary = get_codebase_summary(codebase)
            
            # Get relevant file summaries
            if self.config.include_file_summaries:
                context_data.file_summaries = self._get_relevant_file_summaries(codebase, request.prompt)
            
            # Get relevant class summaries
            if self.config.include_class_summaries:
                context_data.class_summaries = self._get_relevant_class_summaries(codebase, request.prompt)
            
            # Get relevant function summaries
            if self.config.include_function_summaries:
                context_data.function_summaries = self._get_relevant_function_summaries(codebase, request.prompt)
            
            return context_data
            
        except Exception as e:
            logger.error(f"Failed to get context data: {e}")
            raise ContextError(f"Failed to analyze codebase: {e}")
    
    def _get_codebase(self, codebase_path: str) -> Codebase:
        """Get or load a codebase.
        
        Args:
            codebase_path: Path to the codebase.
            
        Returns:
            Codebase object.
        """
        if codebase_path in self._codebase_cache:
            return self._codebase_cache[codebase_path]
        
        if not os.path.exists(codebase_path):
            raise ContextError(f"Codebase path does not exist: {codebase_path}")
        
        try:
            codebase = Codebase(codebase_path)
            self._codebase_cache[codebase_path] = codebase
            logger.info(f"Loaded codebase from {codebase_path}")
            return codebase
        except Exception as e:
            raise ContextError(f"Failed to load codebase from {codebase_path}: {e}")
    
    def _get_relevant_file_summaries(self, codebase: Codebase, prompt: str) -> List[str]:
        """Get relevant file summaries based on the prompt.
        
        Args:
            codebase: Codebase object.
            prompt: Original prompt.
            
        Returns:
            List of relevant file summaries.
        """
        summaries = []
        
        # Get all files and their summaries
        for file in list(codebase.files)[:10]:  # Limit to first 10 files for performance
            try:
                summary = get_file_summary(file)
                summaries.append(summary)
            except Exception as e:
                logger.warning(f"Failed to get summary for file {file.name}: {e}")
        
        return summaries
    
    def _get_relevant_class_summaries(self, codebase: Codebase, prompt: str) -> List[str]:
        """Get relevant class summaries based on the prompt.
        
        Args:
            codebase: Codebase object.
            prompt: Original prompt.
            
        Returns:
            List of relevant class summaries.
        """
        summaries = []
        
        # Get all classes and their summaries
        for cls in list(codebase.classes)[:5]:  # Limit to first 5 classes for performance
            try:
                summary = get_class_summary(cls)
                summaries.append(summary)
            except Exception as e:
                logger.warning(f"Failed to get summary for class {cls.name}: {e}")
        
        return summaries
    
    def _get_relevant_function_summaries(self, codebase: Codebase, prompt: str) -> List[str]:
        """Get relevant function summaries based on the prompt.
        
        Args:
            codebase: Codebase object.
            prompt: Original prompt.
            
        Returns:
            List of relevant function summaries.
        """
        summaries = []
        
        # Get all functions and their summaries
        for func in list(codebase.functions)[:5]:  # Limit to first 5 functions for performance
            try:
                summary = get_function_summary(func)
                summaries.append(summary)
            except Exception as e:
                logger.warning(f"Failed to get summary for function {func.name}: {e}")
        
        return summaries
    
    def _build_enhanced_prompt(self, original_prompt: str, context_data: ContextData) -> str:
        """Build an enhanced prompt with context data.
        
        Args:
            original_prompt: Original prompt.
            context_data: Context data to include.
            
        Returns:
            Enhanced prompt string.
        """
        parts = [
            "# Codebase Context",
            "",
            "You are working with a codebase. Here's the relevant context:",
            "",
        ]
        
        # Add codebase summary
        if context_data.codebase_summary:
            parts.extend([
                "## Codebase Overview",
                context_data.codebase_summary,
                "",
            ])
        
        # Add file summaries
        if context_data.file_summaries:
            parts.extend([
                "## Relevant Files",
                "",
            ])
            for summary in context_data.file_summaries[:3]:  # Limit to 3 files
                parts.extend([summary, ""])
        
        # Add class summaries
        if context_data.class_summaries:
            parts.extend([
                "## Relevant Classes",
                "",
            ])
            for summary in context_data.class_summaries[:2]:  # Limit to 2 classes
                parts.extend([summary, ""])
        
        # Add function summaries
        if context_data.function_summaries:
            parts.extend([
                "## Relevant Functions",
                "",
            ])
            for summary in context_data.function_summaries[:2]:  # Limit to 2 functions
                parts.extend([summary, ""])
        
        # Add original prompt
        parts.extend([
            "# Task",
            "",
            original_prompt,
        ])
        
        return "\n".join(parts)
    
    def _truncate_context(self, enhanced_prompt: str, original_prompt: str) -> str:
        """Truncate context to fit within max length while preserving the original prompt.
        
        Args:
            enhanced_prompt: Enhanced prompt that's too long.
            original_prompt: Original prompt to preserve.
            
        Returns:
            Truncated prompt.
        """
        max_length = self.config.max_context_length
        
        # If even the original prompt is too long, truncate it
        if len(original_prompt) >= max_length:
            return original_prompt[:max_length - 100] + "...\n\n[Context truncated due to length]"
        
        # Calculate available space for context
        available_space = max_length - len(original_prompt) - 200  # Buffer for formatting
        
        if available_space <= 0:
            return original_prompt
        
        # Find the context section
        context_start = enhanced_prompt.find("# Codebase Context")
        task_start = enhanced_prompt.find("# Task")
        
        if context_start == -1 or task_start == -1:
            return original_prompt
        
        # Truncate context section
        context_section = enhanced_prompt[context_start:task_start]
        if len(context_section) > available_space:
            context_section = context_section[:available_space] + "\n\n[Context truncated due to length]\n\n"
        
        # Rebuild prompt
        return context_section + enhanced_prompt[task_start:]
    
    def clear_cache(self) -> None:
        """Clear the codebase cache."""
        self._codebase_cache.clear()
        logger.info("Codebase cache cleared")

