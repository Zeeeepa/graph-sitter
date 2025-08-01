"""
Enhanced LSP Error Manager

This module provides the core LSP error management functionality with comprehensive
context extraction, reasoning, and impact analysis. It serves as the foundation
for the unified error interface.
"""

import asyncio
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .enhanced_error_types import (
    EnhancedErrorInfo, ErrorContext, ErrorReasoning, ImpactAnalysis,
    FixSuggestion, CodeLocation, SymbolInfo, ErrorSeverity, ErrorCategory,
    FixDifficulty, ErrorList
)
from .fix_application import FixApplicator, create_fix_suggestions_for_error

# Import existing LSP components
try:
    from graph_sitter.extensions.lsp.protocol.lsp_types import (
        Diagnostic, DiagnosticSeverity, Position, Range
    )
    from graph_sitter.extensions.lsp.language_servers.base import BaseLanguageServer
    from graph_sitter.extensions.lsp.diagnostics import DiagnosticsManager
    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class LSPServerInfo:
    """Information about an LSP server."""
    name: str
    server_instance: Any
    languages: List[str]
    capabilities: List[str]
    is_active: bool = False
    last_error: Optional[str] = None
    error_count: int = 0


class EnhancedLSPManager:
    """
    Enhanced LSP Manager that provides comprehensive error handling with rich context.
    
    This is the core component that powers the unified error interface:
    - codebase.errors()
    - codebase.full_error_context(error_id)
    - codebase.resolve_errors()
    - codebase.resolve_error(error_id)
    """
    
    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path).resolve()
        self.lsp_servers: Dict[str, LSPServerInfo] = {}
        self.error_cache: Dict[str, EnhancedErrorInfo] = {}
        self.file_modification_times: Dict[str, float] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_initialized = False
        
        # Fix application
        self.fix_applicator = FixApplicator(str(self.codebase_path))
        
        # Performance tracking
        self.stats = {
            'errors_detected': 0,
            'context_extractions': 0,
            'false_positives_filtered': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
    
    async def initialize(self) -> bool:
        """Initialize the LSP manager and discover language servers."""
        try:
            logger.info(f"Initializing Enhanced LSP Manager for {self.codebase_path}")
            
            if not LSP_AVAILABLE:
                logger.warning("LSP components not available, using fallback mode")
                return False
            
            # Discover and initialize language servers
            await self._discover_language_servers()
            
            # Start language servers
            await self._start_language_servers()
            
            self.is_initialized = True
            logger.info(f"Enhanced LSP Manager initialized with {len(self.lsp_servers)} servers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced LSP Manager: {e}")
            return False
    
    async def _discover_language_servers(self):
        """Discover available language servers."""
        import shutil
        import subprocess
        
        # Python language servers with their commands and detection methods
        python_servers = [
            ("pylsp", ["pylsp", "--help"], "python-lsp-server"),
            ("pyright", ["pyright", "--version"], "pyright-langserver"),
            ("mypy", ["mypy", "--version"], "mypy"),
        ]
        
        for server_name, test_command, description in python_servers:
            try:
                # Check if server command is available
                if shutil.which(test_command[0]):
                    # Test if server actually works
                    result = subprocess.run(
                        test_command, 
                        capture_output=True, 
                        text=True, 
                        timeout=5
                    )
                    
                    if result.returncode == 0 or "help" in test_command[1]:
                        server_info = LSPServerInfo(
                            name=server_name,
                            server_instance=None,
                            languages=["python"],
                            capabilities=["diagnostics", "hover", "completion", "code_actions"]
                        )
                        self.lsp_servers[server_name] = server_info
                        logger.debug(f"Discovered LSP server: {server_name} ({description})")
                    else:
                        logger.debug(f"LSP server {server_name} command failed: {result.stderr}")
                else:
                    logger.debug(f"LSP server {server_name} command not found: {test_command[0]}")
            except Exception as e:
                logger.debug(f"LSP server {server_name} not available: {e}")
    
    async def _start_language_servers(self):
        """Start discovered language servers."""
        for server_name, server_info in self.lsp_servers.items():
            try:
                # Initialize server (placeholder - would use actual LSP client)
                server_info.is_active = True
                logger.debug(f"Started LSP server: {server_name}")
            except Exception as e:
                logger.warning(f"Failed to start LSP server {server_name}: {e}")
                server_info.last_error = str(e)
    
    async def get_all_errors(self, force_refresh: bool = False) -> ErrorList:
        """
        Get all errors in the codebase with comprehensive context and reasoning.
        
        This is the core method that powers codebase.errors().
        """
        try:
            start_time = time.time()
            
            if not self.is_initialized:
                await self.initialize()
            
            # Get all Python files in the codebase
            python_files = self._get_python_files()
            
            # Check for file modifications
            if force_refresh or self._files_modified(python_files):
                await self._refresh_error_cache(python_files)
            
            # Get errors from cache
            all_errors = list(self.error_cache.values())
            
            # Filter false positives
            filtered_errors = await self._filter_false_positives(all_errors)
            
            # Sort by severity and location
            filtered_errors.sort(key=lambda e: (
                e.severity.value,
                e.location.file_path,
                e.location.line,
                e.location.character
            ))
            
            execution_time = time.time() - start_time
            logger.info(
                f"Retrieved {len(filtered_errors)} errors in {execution_time:.3f}s "
                f"(cache hits: {self.stats['cache_hits']}, misses: {self.stats['cache_misses']})"
            )
            
            return filtered_errors
            
        except Exception as e:
            logger.error(f"Error retrieving all errors: {e}")
            return []
    
    async def get_full_error_context(self, error_id: str) -> Optional[EnhancedErrorInfo]:
        """
        Get comprehensive context for a specific error.
        
        This powers codebase.full_error_context(error_id).
        """
        try:
            if error_id not in self.error_cache:
                # Try to find error by refreshing cache
                await self.get_all_errors(force_refresh=True)
            
            if error_id not in self.error_cache:
                logger.warning(f"Error {error_id} not found")
                return None
            
            error = self.error_cache[error_id]
            
            # Enhance context if not already done
            if not error.context.has_rich_context:
                error = await self._enhance_error_context(error)
                self.error_cache[error_id] = error
            
            # Enhance reasoning if not already done
            if not error.reasoning.has_deep_analysis:
                error = await self._enhance_error_reasoning(error)
                self.error_cache[error_id] = error
            
            self.stats['context_extractions'] += 1
            return error
            
        except Exception as e:
            logger.error(f"Error getting context for {error_id}: {e}")
            return None
    
    def _get_python_files(self) -> List[Path]:
        """Get all Python files in the codebase."""
        python_files = []
        
        for pattern in ["**/*.py"]:
            python_files.extend(self.codebase_path.glob(pattern))
        
        # Filter out common non-source directories
        excluded_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv'}
        
        filtered_files = []
        for file_path in python_files:
            if not any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                filtered_files.append(file_path)
        
        return filtered_files
    
    def _files_modified(self, files: List[Path]) -> bool:
        """Check if any files have been modified since last check."""
        for file_path in files:
            try:
                current_mtime = file_path.stat().st_mtime
                cached_mtime = self.file_modification_times.get(str(file_path), 0)
                
                if current_mtime > cached_mtime:
                    return True
            except (OSError, IOError):
                continue
        
        return False
    
    async def _refresh_error_cache(self, files: List[Path]):
        """Refresh the error cache for modified files using real LSP diagnostics."""
        logger.debug(f"Refreshing error cache for {len(files)} files")
        
        # Try to use existing LSP diagnostics system
        try:
            from graph_sitter.extensions.lsp.diagnostics import get_diagnostics
            
            for file_path in files:
                try:
                    # Get real LSP diagnostics for this file
                    relative_path = str(file_path.relative_to(self.codebase_path))
                    diagnostics = get_diagnostics(relative_path)
                    
                    # Convert LSP diagnostics to enhanced errors
                    for diag in diagnostics:
                        error_id = f"{relative_path}:{diag.get('range', {}).get('start', {}).get('line', 0)}:{diag.get('range', {}).get('start', {}).get('character', 0)}"
                        
                        # Create enhanced error from LSP diagnostic
                        location = CodeLocation(
                            file_path=relative_path,
                            line=diag.get('range', {}).get('start', {}).get('line', 0) + 1,  # Convert to 1-based
                            character=diag.get('range', {}).get('start', {}).get('character', 0),
                            end_line=diag.get('range', {}).get('end', {}).get('line', 0) + 1,
                            end_character=diag.get('range', {}).get('end', {}).get('character', 0)
                        )
                        
                        # Map LSP severity to our severity
                        severity_map = {1: ErrorSeverity.ERROR, 2: ErrorSeverity.WARNING, 3: ErrorSeverity.INFO, 4: ErrorSeverity.HINT}
                        severity = severity_map.get(diag.get('severity', 1), ErrorSeverity.ERROR)
                        
                        # Determine category from diagnostic source/code
                        category = self._determine_error_category(diag.get('message', ''), diag.get('code', ''))
                        
                        enhanced_error = EnhancedErrorInfo(
                            id=error_id,
                            location=location,
                            message=diag.get('message', 'Unknown error'),
                            severity=severity,
                            category=category,
                            error_type=str(diag.get('code', 'UNKNOWN')),
                            source=diag.get('source', 'lsp'),
                            code=diag.get('code'),
                            detected_at=time.time()
                        )
                        
                        self.error_cache[error_id] = enhanced_error
                        self.stats['errors_detected'] += 1
                    
                    # Update modification time
                    self.file_modification_times[str(file_path)] = file_path.stat().st_mtime
                    
                except Exception as e:
                    logger.warning(f"Failed to get diagnostics for {file_path}: {e}")
                    continue
                    
        except ImportError:
            logger.warning("LSP diagnostics system not available, using fallback")
            # Fallback to mock diagnostics for now
            await self._refresh_error_cache_fallback(files)
    
    async def _refresh_error_cache_fallback(self, files: List[Path]):
        """Fallback error cache refresh when LSP diagnostics not available."""
        # Update modification times
        for file_path in files:
            try:
                self.file_modification_times[str(file_path)] = file_path.stat().st_mtime
            except (OSError, IOError):
                continue
        
        # Clear cache for modified files
        modified_files = {str(f) for f in files}
        self.error_cache = {
            error_id: error for error_id, error in self.error_cache.items()
            if error.location.file_path not in modified_files
        }
        
        # Get diagnostics from LSP servers
        new_errors = await self._collect_lsp_diagnostics(files)
        
        # Enhance errors with context and reasoning
        enhanced_errors = await self._enhance_errors_batch(new_errors)
        
        # Update cache
        for error in enhanced_errors:
            self.error_cache[error.id] = error
        
        self.stats['cache_misses'] += len(new_errors)
        logger.debug(f"Added {len(enhanced_errors)} enhanced errors to cache")
    
    async def _collect_lsp_diagnostics(self, files: List[Path]) -> List[EnhancedErrorInfo]:
        """Collect diagnostics from all active LSP servers."""
        all_errors = []
        
        for file_path in files:
            try:
                # Get diagnostics from each active server
                for server_name, server_info in self.lsp_servers.items():
                    if not server_info.is_active:
                        continue
                    
                    # Simulate getting diagnostics (would use actual LSP client)
                    diagnostics = await self._get_file_diagnostics(file_path, server_name)
                    
                    # Convert to enhanced error info
                    for diagnostic in diagnostics:
                        error = self._diagnostic_to_enhanced_error(diagnostic, file_path, server_name)
                        all_errors.append(error)
                        
            except Exception as e:
                logger.warning(f"Error collecting diagnostics for {file_path}: {e}")
                continue
        
        self.stats['errors_detected'] += len(all_errors)
        return all_errors
    
    async def _get_file_diagnostics(self, file_path: Path, server_name: str) -> List[Dict[str, Any]]:
        """Get diagnostics for a specific file from a specific server."""
        # This is a placeholder - would use actual LSP client
        # For now, return mock diagnostics for testing
        
        try:
            # Read file content to analyze
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            
            diagnostics = []
            
            # Simple syntax error detection for testing
            for line_num, line in enumerate(lines, 1):
                # Check for missing colons
                if (line.strip().startswith(('if ', 'for ', 'while ', 'def ', 'class ')) and 
                    not line.rstrip().endswith(':')):
                    diagnostics.append({
                        'range': {
                            'start': {'line': line_num - 1, 'character': len(line.rstrip())},
                            'end': {'line': line_num - 1, 'character': len(line.rstrip())},
                        },
                        'message': 'Missing colon',
                        'severity': 1,  # Error
                        'code': 'E001',
                        'source': server_name,
                    })
                
                # Check for undefined variables (simple heuristic)
                if 'undefined_' in line:
                    start_pos = line.find('undefined_')
                    diagnostics.append({
                        'range': {
                            'start': {'line': line_num - 1, 'character': start_pos},
                            'end': {'line': line_num - 1, 'character': start_pos + 10},
                        },
                        'message': 'Undefined variable',
                        'severity': 1,  # Error
                        'code': 'S001',
                        'source': server_name,
                    })
            
            return diagnostics
            
        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {e}")
            return []
    
    def _diagnostic_to_enhanced_error(self, diagnostic: Dict[str, Any], file_path: Path, server_name: str) -> EnhancedErrorInfo:
        """Convert LSP diagnostic to enhanced error info."""
        range_info = diagnostic.get('range', {})
        start_pos = range_info.get('start', {})
        end_pos = range_info.get('end', {})
        
        # Create unique error ID
        error_id = self._generate_error_id(
            str(file_path),
            start_pos.get('line', 0),
            start_pos.get('character', 0),
            diagnostic.get('message', '')
        )
        
        # Map severity
        severity_map = {
            1: ErrorSeverity.ERROR,
            2: ErrorSeverity.WARNING,
            3: ErrorSeverity.INFO,
            4: ErrorSeverity.HINT,
        }
        severity = severity_map.get(diagnostic.get('severity', 1), ErrorSeverity.ERROR)
        
        # Determine category from code
        code = diagnostic.get('code', '')
        category = self._determine_error_category(code, diagnostic.get('message', ''))
        
        # Create location
        location = CodeLocation(
            file_path=str(file_path),
            line=start_pos.get('line', 0) + 1,  # Convert to 1-based
            character=start_pos.get('character', 0),
            end_line=end_pos.get('line', 0) + 1 if end_pos else None,
            end_character=end_pos.get('character', 0) if end_pos else None,
        )
        
        # Create enhanced error
        error = EnhancedErrorInfo(
            id=error_id,
            location=location,
            message=diagnostic.get('message', 'Unknown error'),
            severity=severity,
            category=category,
            error_type=str(code) if code else 'UNKNOWN',
            source=server_name,
            code=code,
        )
        
        return error
    
    def _generate_error_id(self, file_path: str, line: int, character: int, message: str) -> str:
        """Generate unique error ID."""
        content = f"{file_path}:{line}:{character}:{message}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _determine_error_category(self, code: str, message: str) -> ErrorCategory:
        """Determine error category from code and message."""
        if not code:
            return ErrorCategory.UNKNOWN
        
        code_str = str(code).upper()
        
        if code_str.startswith('E'):
            return ErrorCategory.SYNTAX
        elif code_str.startswith('S'):
            return ErrorCategory.SEMANTIC
        elif code_str.startswith('T'):
            return ErrorCategory.TYPE
        elif code_str.startswith('I'):
            return ErrorCategory.IMPORT
        elif code_str.startswith('L'):
            return ErrorCategory.LINTING
        else:
            # Analyze message for hints
            message_lower = message.lower()
            if any(word in message_lower for word in ['syntax', 'invalid', 'missing']):
                return ErrorCategory.SYNTAX
            elif any(word in message_lower for word in ['undefined', 'not defined', 'attribute']):
                return ErrorCategory.SEMANTIC
            elif any(word in message_lower for word in ['type', 'incompatible', 'annotation']):
                return ErrorCategory.TYPE
            elif any(word in message_lower for word in ['import', 'module', 'package']):
                return ErrorCategory.IMPORT
            else:
                return ErrorCategory.UNKNOWN
    
    async def _enhance_errors_batch(self, errors: List[EnhancedErrorInfo]) -> List[EnhancedErrorInfo]:
        """Enhance multiple errors with context and reasoning in batch."""
        enhanced_errors = []
        
        # Process errors in parallel
        tasks = []
        for error in errors:
            task = asyncio.create_task(self._enhance_single_error(error))
            tasks.append(task)
        
        # Wait for all enhancements to complete
        for task in asyncio.as_completed(tasks):
            try:
                enhanced_error = await task
                enhanced_errors.append(enhanced_error)
            except Exception as e:
                logger.warning(f"Error enhancing error: {e}")
                continue
        
        return enhanced_errors
    
    async def _enhance_single_error(self, error: EnhancedErrorInfo) -> EnhancedErrorInfo:
        """Enhance a single error with context and reasoning."""
        try:
            # Enhance context
            error = await self._enhance_error_context(error)
            
            # Enhance reasoning
            error = await self._enhance_error_reasoning(error)
            
            # Enhance impact analysis
            error = await self._enhance_impact_analysis(error)
            
            # Generate fix suggestions
            error = await self._generate_fix_suggestions(error)
            
            # Calculate confidence and false positive likelihood
            error = await self._calculate_error_confidence(error)
            
            return error
            
        except Exception as e:
            logger.warning(f"Error enhancing error {error.id}: {e}")
            return error
    
    async def _enhance_error_context(self, error: EnhancedErrorInfo) -> EnhancedErrorInfo:
        """Enhance error with rich context information."""
        try:
            # Get surrounding code
            surrounding_code = await self._get_surrounding_code(error.location)
            error.context.surrounding_code = surrounding_code
            
            # Get symbol definitions
            symbols = await self._get_symbol_definitions(error.location)
            error.context.symbol_definitions = symbols
            
            # Get dependency chain
            dependencies = await self._get_dependency_chain(error.location)
            error.context.dependency_chain = dependencies
            
            # Get usage patterns
            usage_patterns = await self._get_usage_patterns(error.location)
            error.context.usage_patterns = usage_patterns
            
            # Get related files
            related_files = await self._get_related_files(error.location)
            error.context.related_files = related_files
            
            return error
            
        except Exception as e:
            logger.warning(f"Error enhancing context for {error.id}: {e}")
            return error
    
    async def _enhance_error_reasoning(self, error: EnhancedErrorInfo) -> EnhancedErrorInfo:
        """Enhance error with reasoning about why it occurred."""
        try:
            # Analyze root cause
            root_cause = await self._analyze_root_cause(error)
            error.reasoning.root_cause = root_cause
            
            # Generate detailed explanation
            explanation = await self._generate_error_explanation(error)
            error.reasoning.why_occurred = explanation
            
            # Perform semantic analysis
            semantic_analysis = await self._perform_semantic_analysis(error)
            error.reasoning.semantic_analysis = semantic_analysis
            
            # Build causal chain
            causal_chain = await self._build_causal_chain(error)
            error.reasoning.causal_chain = causal_chain
            
            return error
            
        except Exception as e:
            logger.warning(f"Error enhancing reasoning for {error.id}: {e}")
            return error
    
    async def _enhance_impact_analysis(self, error: EnhancedErrorInfo) -> EnhancedErrorInfo:
        """Enhance error with impact analysis."""
        try:
            # Find affected symbols
            affected_symbols = await self._find_affected_symbols(error)
            error.impact_analysis.affected_symbols = affected_symbols
            
            # Analyze cascading effects
            cascading_effects = await self._analyze_cascading_effects(error)
            error.impact_analysis.cascading_effects = cascading_effects
            
            # Identify breaking changes
            breaking_changes = await self._identify_breaking_changes(error)
            error.impact_analysis.breaking_changes = breaking_changes
            
            # Find dependent files
            dependent_files = await self._find_dependent_files(error)
            error.impact_analysis.dependent_files = dependent_files
            
            return error
            
        except Exception as e:
            logger.warning(f"Error enhancing impact analysis for {error.id}: {e}")
            return error
    
    async def _generate_fix_suggestions(self, error: EnhancedErrorInfo) -> EnhancedErrorInfo:
        """Generate fix suggestions for the error using real fix application logic."""
        try:
            # Use the real fix suggestion generator
            fixes = create_fix_suggestions_for_error(error)
            error.suggested_fixes = fixes
            return error
            
        except Exception as e:
            logger.warning(f"Error generating fix suggestions for {error.id}: {e}")
            return error
    
    async def _calculate_error_confidence(self, error: EnhancedErrorInfo) -> EnhancedErrorInfo:
        """Calculate confidence score and false positive likelihood."""
        try:
            # Base confidence on error source and type
            base_confidence = 0.8
            
            # Adjust based on error category
            if error.category == ErrorCategory.SYNTAX:
                base_confidence = 0.95  # Syntax errors are usually reliable
            elif error.category == ErrorCategory.TYPE:
                base_confidence = 0.85  # Type errors are fairly reliable
            elif error.category == ErrorCategory.SEMANTIC:
                base_confidence = 0.75  # Semantic errors can be tricky
            
            # Adjust based on context richness
            if error.context.has_rich_context:
                base_confidence += 0.1
            
            # Calculate false positive likelihood
            false_positive_likelihood = await self._calculate_false_positive_likelihood(error)
            
            error.confidence_score = min(base_confidence, 1.0)
            error.false_positive_likelihood = false_positive_likelihood
            
            return error
            
        except Exception as e:
            logger.warning(f"Error calculating confidence for {error.id}: {e}")
            return error
    
    async def _filter_false_positives(self, errors: List[EnhancedErrorInfo]) -> List[EnhancedErrorInfo]:
        """Filter out likely false positives."""
        filtered_errors = []
        
        for error in errors:
            if error.is_likely_false_positive:
                self.stats['false_positives_filtered'] += 1
                logger.debug(f"Filtered false positive: {error.id}")
                continue
            
            filtered_errors.append(error)
        
        return filtered_errors
    
    # Placeholder methods for context extraction (would be implemented with actual analysis)
    
    async def _get_surrounding_code(self, location: CodeLocation) -> str:
        """Get surrounding code context."""
        try:
            file_path = Path(location.file_path)
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            
            start_line = max(0, location.line - 10)
            end_line = min(len(lines), location.line + 10)
            
            context_lines = lines[start_line:end_line]
            return '\n'.join(context_lines)
            
        except Exception:
            return ""
    
    async def _get_symbol_definitions(self, location: CodeLocation) -> List[SymbolInfo]:
        """Get symbol definitions related to the error location using graph-sitter."""
        try:
            # Try to use existing graph-sitter codebase if available
            if hasattr(self, '_codebase') and self._codebase:
                symbols = []
                
                # Get functions at or near the error location
                if hasattr(self._codebase, 'functions'):
                    for func in self._codebase.functions:
                        if (hasattr(func, 'file_path') and func.file_path == location.file_path and
                            hasattr(func, 'line_number') and 
                            abs(func.line_number - location.line) <= 5):
                            
                            symbol = SymbolInfo(
                                name=getattr(func, 'name', 'unknown'),
                                symbol_type='function',
                                file_path=location.file_path,
                                line=getattr(func, 'line_number', location.line),
                                column=getattr(func, 'column', 0),
                                definition=getattr(func, 'definition', None),
                                scope=getattr(func, 'scope', 'global')
                            )
                            symbols.append(symbol)
                
                # Get classes at or near the error location
                if hasattr(self._codebase, 'classes'):
                    for cls in self._codebase.classes:
                        if (hasattr(cls, 'file_path') and cls.file_path == location.file_path and
                            hasattr(cls, 'line_number') and 
                            abs(cls.line_number - location.line) <= 10):
                            
                            symbol = SymbolInfo(
                                name=getattr(cls, 'name', 'unknown'),
                                symbol_type='class',
                                file_path=location.file_path,
                                line=getattr(cls, 'line_number', location.line),
                                column=getattr(cls, 'column', 0),
                                definition=getattr(cls, 'definition', None),
                                scope=getattr(cls, 'scope', 'global')
                            )
                            symbols.append(symbol)
                
                return symbols
            
            # Fallback: Basic AST analysis using Python's ast module
            import ast
            file_path = Path(location.file_path)
            if not file_path.exists():
                return []
            
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            try:
                tree = ast.parse(content)
                symbols = []
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if hasattr(node, 'lineno') and abs(node.lineno - location.line) <= 5:
                            symbol_type = 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class'
                            symbol = SymbolInfo(
                                name=node.name,
                                symbol_type=symbol_type,
                                file_path=location.file_path,
                                line=node.lineno,
                                column=getattr(node, 'col_offset', 0),
                                definition=None,
                                scope='global'
                            )
                            symbols.append(symbol)
                
                return symbols
                
            except SyntaxError:
                # File has syntax errors, return empty list
                return []
            
        except Exception as e:
            logger.warning(f"Error getting symbol definitions: {e}")
            return []
    
    async def _get_dependency_chain(self, location: CodeLocation) -> List[str]:
        """Get dependency chain for the error location using import analysis."""
        try:
            # Try to use existing graph-sitter codebase if available
            if hasattr(self, '_codebase') and self._codebase:
                dependencies = []
                
                # Get imports from the file
                if hasattr(self._codebase, 'imports'):
                    for imp in self._codebase.imports:
                        if hasattr(imp, 'file_path') and imp.file_path == location.file_path:
                            module_name = getattr(imp, 'module_name', None) or getattr(imp, 'name', 'unknown')
                            dependencies.append(module_name)
                
                return dependencies
            
            # Fallback: Basic import analysis using Python's ast module
            import ast
            file_path = Path(location.file_path)
            if not file_path.exists():
                return []
            
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            try:
                tree = ast.parse(content)
                dependencies = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            dependencies.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            dependencies.append(node.module)
                            for alias in node.names:
                                dependencies.append(f"{node.module}.{alias.name}")
                
                return list(set(dependencies))  # Remove duplicates
                
            except SyntaxError:
                # File has syntax errors, return empty list
                return []
            
        except Exception as e:
            logger.warning(f"Error getting dependency chain: {e}")
            return []
    
    async def _get_usage_patterns(self, location: CodeLocation) -> List[Dict[str, Any]]:
        """Get usage patterns for symbols at the error location."""
        try:
            import ast
            file_path = Path(location.file_path)
            if not file_path.exists():
                return []
            
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            try:
                tree = ast.parse(content)
                patterns = []
                
                # Find variable assignments and usage patterns
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        if hasattr(node, 'lineno') and abs(node.lineno - location.line) <= 3:
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    patterns.append({
                                        'type': 'assignment',
                                        'variable': target.id,
                                        'line': node.lineno,
                                        'context': 'variable_assignment'
                                    })
                    
                    elif isinstance(node, ast.Call):
                        if hasattr(node, 'lineno') and abs(node.lineno - location.line) <= 3:
                            if isinstance(node.func, ast.Name):
                                patterns.append({
                                    'type': 'function_call',
                                    'function': node.func.id,
                                    'line': node.lineno,
                                    'context': 'function_invocation'
                                })
                            elif isinstance(node.func, ast.Attribute):
                                patterns.append({
                                    'type': 'method_call',
                                    'method': node.func.attr,
                                    'line': node.lineno,
                                    'context': 'method_invocation'
                                })
                
                return patterns
                
            except SyntaxError:
                # File has syntax errors, return basic pattern info
                return [{
                    'type': 'syntax_error',
                    'line': location.line,
                    'context': 'syntax_error_detected'
                }]
            
        except Exception as e:
            logger.warning(f"Error getting usage patterns: {e}")
            return []
    
    async def _get_related_files(self, location: CodeLocation) -> List[str]:
        """Get files related to the error location through imports and references."""
        try:
            import ast
            file_path = Path(location.file_path)
            if not file_path.exists():
                return []
            
            related_files = []
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            try:
                tree = ast.parse(content)
                
                # Find imported modules that might be local files
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and not node.module.startswith('.'):
                            # Check if this could be a local module
                            potential_file = self.codebase_path / f"{node.module.replace('.', '/')}.py"
                            if potential_file.exists():
                                related_files.append(str(potential_file.relative_to(self.codebase_path)))
                            
                            # Also check for __init__.py in package directories
                            potential_package = self.codebase_path / node.module.replace('.', '/') / "__init__.py"
                            if potential_package.exists():
                                related_files.append(str(potential_package.relative_to(self.codebase_path)))
                    
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            # Check if this could be a local module
                            potential_file = self.codebase_path / f"{alias.name.replace('.', '/')}.py"
                            if potential_file.exists():
                                related_files.append(str(potential_file.relative_to(self.codebase_path)))
                
                # Find files in the same directory (common pattern)
                current_dir = file_path.parent
                for sibling_file in current_dir.glob("*.py"):
                    if sibling_file != file_path and sibling_file.name != "__init__.py":
                        related_files.append(str(sibling_file.relative_to(self.codebase_path)))
                
                # Add __init__.py files in the same package
                init_file = current_dir / "__init__.py"
                if init_file.exists() and init_file != file_path:
                    related_files.append(str(init_file.relative_to(self.codebase_path)))
                
                return list(set(related_files))  # Remove duplicates
                
            except SyntaxError:
                # File has syntax errors, just return files in same directory
                current_dir = file_path.parent
                related_files = []
                for sibling_file in current_dir.glob("*.py"):
                    if sibling_file != file_path:
                        related_files.append(str(sibling_file.relative_to(self.codebase_path)))
                return related_files
            
        except Exception as e:
            logger.warning(f"Error getting related files: {e}")
            return []
    
    async def _analyze_root_cause(self, error: EnhancedErrorInfo) -> str:
        """Analyze the root cause of the error."""
        # Placeholder - would use semantic analysis
        if error.error_type == 'E001':
            return "Missing colon after control statement"
        elif error.error_type == 'S001':
            return "Variable referenced before definition"
        else:
            return "Unknown root cause"
    
    async def _generate_error_explanation(self, error: EnhancedErrorInfo) -> str:
        """Generate detailed explanation of why the error occurred."""
        # Placeholder - would use contextual analysis
        return f"Error occurred due to {error.message.lower()}"
    
    async def _perform_semantic_analysis(self, error: EnhancedErrorInfo) -> Optional[str]:
        """Perform semantic analysis of the error."""
        # Placeholder - would use AST and semantic analysis
        return None
    
    async def _build_causal_chain(self, error: EnhancedErrorInfo) -> List[str]:
        """Build causal chain showing how the error occurred."""
        # Placeholder - would trace execution flow
        return []
    
    async def _find_affected_symbols(self, error: EnhancedErrorInfo) -> List[str]:
        """Find symbols affected by this error."""
        # Placeholder - would analyze symbol dependencies
        return []
    
    async def _analyze_cascading_effects(self, error: EnhancedErrorInfo) -> List[str]:
        """Analyze cascading effects of this error."""
        # Placeholder - would analyze downstream impacts
        return []
    
    async def _identify_breaking_changes(self, error: EnhancedErrorInfo) -> List[str]:
        """Identify what breaks due to this error."""
        # Placeholder - would analyze breaking changes
        return []
    
    async def _find_dependent_files(self, error: EnhancedErrorInfo) -> List[str]:
        """Find files that depend on the error location."""
        # Placeholder - would analyze file dependencies
        return []
    
    async def _calculate_false_positive_likelihood(self, error: EnhancedErrorInfo) -> float:
        """Calculate likelihood that this error is a false positive."""
        # Placeholder - would use pattern matching and heuristics
        base_likelihood = 0.1
        
        # Check for common false positive patterns
        if 'dynamic' in error.message.lower():
            base_likelihood += 0.3
        
        if error.source == 'mypy' and 'Any' in error.message:
            base_likelihood += 0.2
        
        return min(base_likelihood, 1.0)
    
    async def shutdown(self):
        """Shutdown the LSP manager and clean up resources."""
        try:
            # Shutdown language servers
            for server_name, server_info in self.lsp_servers.items():
                if server_info.is_active:
                    # Shutdown server (placeholder)
                    server_info.is_active = False
                    logger.debug(f"Shutdown LSP server: {server_name}")
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            logger.info("Enhanced LSP Manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during LSP manager shutdown: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            **self.stats,
            'active_servers': len([s for s in self.lsp_servers.values() if s.is_active]),
            'cached_errors': len(self.error_cache),
            'is_initialized': self.is_initialized,
        }
