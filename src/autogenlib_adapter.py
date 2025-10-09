"""Unified AutoGenLib Adapter for AI-powered error resolution.

Consolidates autogenlib_context.py and autogenlib_ai_resolve.py.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from graph_sitter import Codebase
from .analysis_utils import AnalysisError, setup_logger

logger = setup_logger(__name__)

# Try importing AI dependencies
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI not installed - AI resolution will be limited")


class AutoGenLibAdapter:
    """Unified adapter for AI-powered error resolution.
    
    Consolidates:
    - Context generation (from autogenlib_context.py)
    - AI resolution (from autogenlib_ai_resolve.py)
    """
    
    def __init__(
        self,
        codebase: Codebase,
        graph_sitter_adapter=None,
        lsp_manager=None,
        ai_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize AI resolution adapter.
        
        Args:
            codebase: Graph-sitter Codebase instance
            graph_sitter_adapter: GraphSitterAdapter for code analysis
            lsp_manager: LSPDiagnosticsManager for diagnostics
            ai_config: AI configuration (provider, model, etc.)
        """
        self.codebase = codebase
        self.gs_adapter = graph_sitter_adapter
        self.lsp_manager = lsp_manager
        self.ai_config = ai_config or {}
        self._client = None
        self._context_cache: Dict[str, Any] = {}
        
        # Configure AI client
        self._setup_ai_client()
        
        logger.info("Initialized AutoGenLibAdapter")
    
    def _setup_ai_client(self):
        """Setup AI client based on configuration."""
        provider = self.ai_config.get('provider', 'openai')
        
        if provider == 'openai' and HAS_OPENAI:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                openai.api_key = api_key
                self._client = 'openai'
                logger.info("Configured OpenAI client")
            else:
                logger.warning("OPENAI_API_KEY not found")
        else:
            logger.warning(f"Provider {provider} not configured")
    
    # Protocol Implementation
    
    def resolve_error(
        self,
        error: AnalysisError,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resolve single error using AI assistance.
        
        Args:
            error: AnalysisError to resolve
            context: Additional context
            
        Returns:
            Dictionary with fix_code, explanation, confidence
        """
        if not self._client:
            return {
                "error": "AI client not configured",
                "fix_code": None,
                "explanation": "AI resolution requires API key configuration",
                "confidence": 0.0
            }
        
        try:
            # Get comprehensive context
            full_context = self.get_error_context(error)
            if context:
                full_context.update(context)
            
            # Generate fix using AI
            prompt = self._construct_fix_prompt(error, full_context)
            fix_result = self._generate_fix_with_ai(prompt)
            
            return {
                "fix_code": fix_result.get('code'),
                "explanation": fix_result.get('explanation'),
                "confidence": fix_result.get('confidence', 0.7),
                "applied": False
            }
            
        except Exception as e:
            logger.error(f"Error resolving with AI: {e}")
            return {
                "error": str(e),
                "fix_code": None,
                "explanation": None,
                "confidence": 0.0
            }
    
    def resolve_multiple_errors(
        self,
        errors: List[AnalysisError],
        max_fixes: int = 10
    ) -> List[Dict[str, Any]]:
        """Resolve multiple errors in batch."""
        results = []
        
        # Sort by severity
        sorted_errors = sorted(
            errors,
            key=lambda e: (e.severity, e.line),
            reverse=True
        )
        
        for error in sorted_errors[:max_fixes]:
            result = self.resolve_error(error)
            results.append(result)
        
        logger.info(f"Resolved {len(results)} errors")
        return results
    
    def get_error_context(
        self,
        error: AnalysisError,
        include_related_symbols: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive context for error.
        
        Args:
            error: AnalysisError to get context for
            include_related_symbols: Whether to include related symbols
            
        Returns:
            Dictionary with error context
        """
        cache_key = f"context_{error.file_path}_{error.line}"
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]
        
        try:
            context = {
                "error": error.to_dict(),
                "file_path": error.file_path,
                "line": error.line,
                "column": error.column,
                "message": error.message,
                "severity": error.severity,
                "category": error.category,
            }
            
            # Add file context if graph-sitter adapter available
            if self.gs_adapter:
                file_details = self.gs_adapter.get_file_details(error.file_path)
                context["file_details"] = file_details
            
            # Add surrounding code
            context["code_snippet"] = self._get_code_snippet(
                error.file_path,
                error.line,
                context_lines=5
            )
            
            # Add codebase overview
            if self.gs_adapter:
                overview = self.gs_adapter.get_codebase_overview()
                context["codebase_overview"] = {
                    "files_count": overview.get('files_count'),
                    "functions_count": overview.get('functions_count'),
                }
            
            self._context_cache[cache_key] = context
            return context
            
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return {"error": str(e)}
    
    def generate_fix_strategy(
        self,
        errors: List[AnalysisError]
    ) -> Dict[str, Any]:
        """Generate comprehensive fix strategy for multiple errors.
        
        Args:
            errors: List of errors to analyze
            
        Returns:
            Dictionary with fix strategy
        """
        # Categorize errors
        by_severity = {}
        by_category = {}
        by_file = {}
        
        for error in errors:
            by_severity.setdefault(error.severity, []).append(error)
            by_category.setdefault(error.category, []).append(error)
            by_file.setdefault(error.file_path, []).append(error)
        
        strategy = {
            "total_errors": len(errors),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_category": {k: len(v) for k, v in by_category.items()},
            "by_file": {k: len(v) for k, v in by_file.items()},
            "priority_order": self._prioritize_errors(errors),
            "estimated_effort": self._estimate_fix_effort(errors),
        }
        
        return strategy
    
    # Private Helper Methods
    
    def _construct_fix_prompt(self, error: AnalysisError, context: Dict[str, Any]) -> str:
        """Construct AI prompt for fix generation."""
        prompt = f"""You are an expert code fixer. Fix the following error:

Error Type: {error.error_type}
Severity: {error.severity}
Message: {error.message}
Location: {error.file_path}:{error.line}:{error.column}

Code Context:
```python
{context.get('code_snippet', '')}
```

Please provide:
1. The fix code
2. Explanation of the fix
3. Confidence level (0-1)

Format your response as JSON:
{{"code": "...", "explanation": "...", "confidence": 0.8}}
"""
        return prompt
    
    def _generate_fix_with_ai(self, prompt: str) -> Dict[str, Any]:
        """Generate fix using AI model."""
        if self._client == 'openai':
            try:
                response = openai.ChatCompletion.create(
                    model=self.ai_config.get('model', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": "You are an expert code fixer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.ai_config.get('temperature', 0.2),
                    max_tokens=self.ai_config.get('max_tokens', 2000)
                )
                
                import json
                result = json.loads(response.choices[0].message.content)
                return result
                
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                return {
                    "code": None,
                    "explanation": f"AI generation failed: {e}",
                    "confidence": 0.0
                }
        
        return {
            "code": None,
            "explanation": "No AI client configured",
            "confidence": 0.0
        }
    
    def _get_code_snippet(
        self,
        file_path: str,
        line: int,
        context_lines: int = 5
    ) -> str:
        """Get code snippet around error line."""
        try:
            file_obj = self.codebase.get_file(file_path)
            if not hasattr(file_obj, 'source'):
                return ""
            
            lines = file_obj.source.splitlines()
            start = max(0, line - context_lines - 1)
            end = min(len(lines), line + context_lines)
            
            snippet_lines = []
            for i in range(start, end):
                prefix = ">>>" if i == line - 1 else "   "
                snippet_lines.append(f"{prefix} {i+1:4d} | {lines[i]}")
            
            return "\n".join(snippet_lines)
            
        except Exception as e:
            logger.error(f"Error getting code snippet: {e}")
            return ""
    
    def _prioritize_errors(self, errors: List[AnalysisError]) -> List[str]:
        """Prioritize errors for fixing."""
        # Sort by severity and confidence
        priority_map = {"error": 3, "warning": 2, "info": 1, "hint": 0}
        
        sorted_errors = sorted(
            errors,
            key=lambda e: (
                priority_map.get(e.severity, 0),
                e.confidence
            ),
            reverse=True
        )
        
        return [f"{e.file_path}:{e.line}" for e in sorted_errors[:10]]
    
    def _estimate_fix_effort(self, errors: List[AnalysisError]) -> str:
        """Estimate effort to fix errors."""
        count = len(errors)
        
        if count <= 5:
            return "low"
        elif count <= 20:
            return "medium"
        else:
            return "high"
    
    # Enhanced Context Generation (from autogenlib_context.py)
    
    def generate_comprehensive_context(
        self,
        errors: List[AnalysisError],
        include_patterns: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive context for AI including patterns and history.
        
        Args:
            errors: List of errors to generate context for
            include_patterns: Whether to include error patterns
            
        Returns:
            Comprehensive context dictionary
        """
        context = {
            "codebase_overview": {},
            "error_summary": {},
            "patterns": [],
            "related_files": [],
            "suggested_approach": ""
        }
        
        try:
            # Codebase overview
            if self.gs_adapter:
                context["codebase_overview"] = self.gs_adapter.get_codebase_overview()
            
            # Error summary
            context["error_summary"] = {
                "total": len(errors),
                "by_severity": self._group_by_severity(errors),
                "by_category": self._group_by_category(errors),
                "by_file": self._group_by_file(errors)
            }
            
            # Find patterns if requested
            if include_patterns:
                context["patterns"] = self._find_error_patterns(errors)
            
            # Identify related files
            context["related_files"] = self._get_relevant_files(errors)
            
            # Generate suggested approach
            context["suggested_approach"] = self._generate_fix_approach(errors)
            
        except Exception as e:
            logger.error(f"Error generating comprehensive context: {e}")
            context["error"] = str(e)
        
        return context
    
    def resolve_with_retry(
        self,
        error: AnalysisError,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ) -> Dict[str, Any]:
        """Resolve error with retry logic and exponential backoff.
        
        Args:
            error: AnalysisError to resolve
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for backoff delay
            
        Returns:
            Resolution result with attempt history
        """
        import time
        
        attempts = []
        delay = 1.0
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting resolution (attempt {attempt + 1}/{max_retries})")
                result = self.resolve_error(error)
                
                attempts.append({
                    "attempt": attempt + 1,
                    "success": result.get("fix_code") is not None,
                    "confidence": result.get("confidence", 0.0)
                })
                
                # If successful, return result
                if result.get("fix_code"):
                    return {
                        **result,
                        "attempts": attempts,
                        "final_attempt": attempt + 1
                    }
                
                # If not final attempt, wait before retrying
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= backoff_factor
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                attempts.append({
                    "attempt": attempt + 1,
                    "success": False,
                    "error": str(e)
                })
                
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= backoff_factor
        
        # All attempts failed
        return {
            "error": "All resolution attempts failed",
            "fix_code": None,
            "explanation": None,
            "confidence": 0.0,
            "attempts": attempts
        }
    
    def batch_resolve(
        self,
        errors: List[AnalysisError],
        batch_size: int = 5,
        parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """Resolve errors in batches for efficiency.
        
        Args:
            errors: List of errors to resolve
            batch_size: Number of errors per batch
            parallel: Whether to process batches in parallel
            
        Returns:
            List of resolution results
        """
        results = []
        
        # Sort errors by file and line for better batching
        sorted_errors = sorted(errors, key=lambda e: (e.file_path, e.line))
        
        # Process in batches
        for i in range(0, len(sorted_errors), batch_size):
            batch = sorted_errors[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} errors)")
            
            # Generate shared context for batch
            batch_context = self._get_batch_context(batch)
            
            # Resolve each error in batch
            for error in batch:
                result = self.resolve_error(error, context=batch_context)
                results.append(result)
        
        return results
    
    def _group_by_severity(self, errors: List[AnalysisError]) -> Dict[str, int]:
        """Group errors by severity."""
        from collections import Counter
        return dict(Counter(e.severity for e in errors))
    
    def _group_by_category(self, errors: List[AnalysisError]) -> Dict[str, int]:
        """Group errors by category."""
        from collections import Counter
        return dict(Counter(e.category for e in errors if e.category))
    
    def _group_by_file(self, errors: List[AnalysisError]) -> Dict[str, int]:
        """Group errors by file."""
        from collections import Counter
        return dict(Counter(e.file_path for e in errors))
    
    def _find_error_patterns(self, errors: List[AnalysisError]) -> List[Dict[str, Any]]:
        """Find common patterns in errors."""
        patterns = []
        
        # Find common error types
        by_type = self._group_by_category(errors)
        for error_type, count in by_type.items():
            if count >= 3:  # Pattern if appears 3+ times
                patterns.append({
                    "type": "repeated_error_type",
                    "error_type": error_type,
                    "count": count,
                    "suggestion": f"Consider addressing root cause of {error_type} errors"
                })
        
        # Find errors in same file
        by_file = self._group_by_file(errors)
        for file, count in by_file.items():
            if count >= 5:  # Multiple errors in same file
                patterns.append({
                    "type": "file_hotspot",
                    "file": file,
                    "count": count,
                    "suggestion": f"File {file} may need refactoring"
                })
        
        return patterns
    
    def _get_relevant_files(self, errors: List[AnalysisError]) -> List[str]:
        """Get list of files relevant to errors."""
        files = set(e.file_path for e in errors)
        
        # Add related files based on imports if possible
        if self.gs_adapter:
            related = set()
            for file in files:
                deps = self.gs_adapter.analyze_dependencies(file)
                related.update(imp.get("module") for imp in deps.get("imports", []))
            
            files.update(related)
        
        return sorted(list(files))
    
    def _generate_fix_approach(self, errors: List[AnalysisError]) -> str:
        """Generate suggested approach for fixing errors."""
        count = len(errors)
        severities = self._group_by_severity(errors)
        
        critical_count = severities.get("error", 0)
        warning_count = severities.get("warning", 0)
        
        if critical_count > 0:
            return f"Start with {critical_count} critical errors, then address {warning_count} warnings"
        elif warning_count > 0:
            return f"Address {warning_count} warnings systematically"
        else:
            return "Review and address remaining issues"
    
    def _get_batch_context(self, batch: List[AnalysisError]) -> Dict[str, Any]:
        """Get shared context for a batch of errors."""
        # Get common files
        files = list(set(e.file_path for e in batch))
        
        context = {
            "batch_size": len(batch),
            "common_files": files,
            "severity_distribution": self._group_by_severity(batch)
        }
        
        # Add file details for common files
        if self.gs_adapter and len(files) <= 3:
            context["file_details"] = {
                f: self.gs_adapter.get_file_details(f) for f in files
            }
        
        return context
