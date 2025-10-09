"""Unified AutoGenLib Adapter for AI-powered error resolution.

Consolidates autogenlib_context.py, autogenlib_ai_resolve.py, and extensions.
Integrated features from src/graph_sitter/extensions/autogenlib/:
- Advanced exception handling
- Intelligent caching
- AI-powered code generation
"""

import logging
import os
import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import Codebase - available from top-level package per __init__.py line 7
try:
    from graph_sitter import Codebase
except ImportError:
    # Fallback: try direct import from core
    try:
        from graph_sitter.core.codebase import Codebase
    except ImportError:
        # Final fallback for development/testing
        Codebase = None
# Try relative imports first, fall back to absolute
try:
    from .analysis_utils import AnalysisError, setup_logger
except ImportError:
    from analysis_utils import AnalysisError, setup_logger

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
    - Advanced caching (from extensions/autogenlib/_cache.py)
    - Exception handling (from extensions/autogenlib/_exception_handler.py)
    """
    
    def __init__(
        self,
        codebase: Codebase,
        graph_sitter_adapter=None,
        lsp_manager=None,
        ai_config: Optional[Dict[str, Any]] = None,
        enable_caching: bool = True
    ):
        """Initialize AI resolution adapter.
        
        Args:
            codebase: Graph-sitter Codebase instance
            graph_sitter_adapter: GraphSitterAdapter for code analysis
            lsp_manager: LSPDiagnosticsManager for diagnostics
            ai_config: AI configuration (provider, model, etc.)
            enable_caching: Whether to enable response caching
        """
        self.codebase = codebase
        self.gs_adapter = graph_sitter_adapter
        self.lsp_manager = lsp_manager
        self.ai_config = ai_config or {}
        self._client = None
        self._context_cache: Dict[str, Any] = {}
        self._enable_caching = enable_caching
        self._cache_dir = None
        
        # Initialize cache directory
        if self._enable_caching:
            self._init_cache_directory()
        
        # Configure AI client
        self._setup_ai_client()
        
        logger.info("Initialized AutoGenLibAdapter (caching: %s)", enable_caching)
    
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
    
    # ==================================================================
    # INTEGRATED FEATURES FROM extensions/autogenlib/
    # ==================================================================
    
    def _init_cache_directory(self):
        """Initialize cache directory for storing AI responses."""
        cache_dir = Path.home() / ".autogenlib_cache"
        cache_dir.mkdir(exist_ok=True)
        self._cache_dir = cache_dir
        logger.info(f"Cache directory initialized: {cache_dir}")
    
    def _get_cache_key(self, error: AnalysisError) -> str:
        """Generate cache key for an error."""
        key_data = f"{error.file_path}:{error.line}:{error.error_type}:{error.message}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_fix(self, error: AnalysisError) -> Optional[Dict[str, Any]]:
        """Get cached fix for an error if available."""
        if not self._enable_caching or not self._cache_dir:
            return None
        
        cache_key = self._get_cache_key(error)
        cache_file = self._cache_dir / f"{cache_key}.json"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Cache hit for error at {error.file_path}:{error.line}")
                    return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache: {e}")
        
        return None
    
    def _cache_fix(self, error: AnalysisError, fix_result: Dict[str, Any]):
        """Cache a fix result."""
        if not self._enable_caching or not self._cache_dir:
            return
        
        cache_key = self._get_cache_key(error)
        cache_file = self._cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(fix_result, f, indent=2)
            logger.info(f"Cached fix for error at {error.file_path}:{error.line}")
        except IOError as e:
            logger.warning(f"Error writing cache: {e}")
    
    def generate_advanced_fix(
        self,
        error: AnalysisError,
        source_code: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Generate advanced fix using OpenAI with detailed analysis.
        
        This method integrates the advanced error fixing from
        extensions/autogenlib/_exception_handler.py
        
        Args:
            error: AnalysisError to fix
            source_code: Source code of the file
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with:
                - explanation: What was wrong and how it was fixed
                - changes: List of specific changes made
                - fixed_code: Complete fixed source code
                - confidence: Confidence level (0-1)
        """
        # Check cache first
        if use_cache:
            cached = self._get_cached_fix(error)
            if cached:
                return cached
        
        if not self._client or not HAS_OPENAI:
            return {
                "error": "OpenAI client not configured",
                "explanation": None,
                "changes": [],
                "fixed_code": None,
                "confidence": 0.0
            }
        
        try:
            # Create comprehensive system prompt
            system_prompt = """
You are an expert Python developer specialized in fixing static analysis errors.

You excel at:
1. Understanding static analysis tool outputs (ruff, mypy, pylint, bandit, etc.)
2. Identifying the root cause of style, type, security, and logic issues
3. Providing minimal, targeted fixes that resolve the specific issue
4. Maintaining code consistency and following Python best practices
5. Explaining the reasoning behind each fix

Your fixes should:
1. Address the specific error without introducing new issues
2. Maintain the original code's functionality and intent
3. Follow PEP 8 and modern Python conventions
4. Include type hints where appropriate
5. Add necessary imports or remove unused ones

Always provide both the fixed code and a clear explanation.
"""
            
            # Create detailed user prompt
            user_prompt = f"""
STATIC ANALYSIS ERROR FIXING TASK

ERROR DETAILS:
- File: {error.file_path}
- Line: {error.line}
- Column: {error.column}
- Error Type: {error.error_type}
- Severity: {error.severity}
- Tool: {error.tool_source}
- Message: {error.message}

CURRENT SOURCE CODE:
```python
{source_code}
```

TASK:
Fix the specific error identified above. Focus on the exact line and issue mentioned.

RESPONSE FORMAT (JSON):
{{
    "explanation": "Clear explanation of what was wrong and how you fixed it",
    "changes": [
        {{
            "line": {error.line},
            "description": "What was changed on this line",
            "original": "original code",
            "new": "fixed code"
        }}
    ],
    "fixed_code": "Complete fixed Python code for the entire file",
    "confidence": 0.9
}}
"""
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.ai_config.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.ai_config.get('temperature', 0.2),
                max_tokens=self.ai_config.get('max_tokens', 3000)
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Cache the result
            if use_cache:
                self._cache_fix(error, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating advanced fix: {e}")
            return {
                "error": str(e),
                "explanation": None,
                "changes": [],
                "fixed_code": None,
                "confidence": 0.0
            }
    
    def clear_cache(self):
        """Clear all cached fixes."""
        if not self._cache_dir:
            return
        
        try:
            import shutil
            shutil.rmtree(self._cache_dir)
            self._init_cache_directory()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache."""
        if not self._cache_dir:
            return {"enabled": False}
        
        try:
            cache_files = list(self._cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "enabled": True,
                "cache_dir": str(self._cache_dir),
                "cached_fixes": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}
    
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
