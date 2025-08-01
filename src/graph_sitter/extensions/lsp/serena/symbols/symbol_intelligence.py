"""
Symbol Intelligence

Provides advanced symbol analysis, context understanding, and impact analysis.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import re

from ..types import SymbolInfo, AnalysisContext

logger = logging.getLogger(__name__)


class SymbolIntelligence:
    """
    Provides advanced symbol intelligence and analysis.
    
    Features:
    - Symbol discovery and indexing
    - Context-aware symbol analysis
    - Dependency tracking and impact analysis
    - Symbol relationship mapping
    - Usage pattern analysis
    """
    
    def __init__(self, codebase_path: str, serena_core: Any):
        self.codebase_path = Path(codebase_path)
        self.serena_core = serena_core
        
        # Symbol index and cache
        self._symbol_index: Dict[str, SymbolInfo] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._usage_patterns: Dict[str, List[Dict[str, Any]]] = {}
        
        # Analysis state
        self._indexed_files: Set[str] = set()
        self._last_index_time: Optional[float] = None
        
        logger.debug("SymbolIntelligence initialized")
    
    async def initialize(self) -> None:
        """Initialize symbol intelligence."""
        logger.info("Initializing symbol intelligence...")
        
        # Build initial symbol index
        await self._build_symbol_index()
        
        logger.info("✅ Symbol intelligence initialized")
    
    async def shutdown(self) -> None:
        """Shutdown symbol intelligence."""
        self._symbol_index.clear()
        self._dependency_graph.clear()
        self._usage_patterns.clear()
        self._indexed_files.clear()
        
        logger.info("✅ Symbol intelligence shutdown")
    
    async def get_symbol_info(
        self,
        symbol: str,
        context: Optional[AnalysisContext] = None
    ) -> Optional[SymbolInfo]:
        """
        Get comprehensive information about a symbol.
        
        Args:
            symbol: Symbol name to analyze
            context: Analysis context for more precise results
            
        Returns:
            SymbolInfo with comprehensive symbol data
        """
        try:
            # Check cache first
            if symbol in self._symbol_index:
                symbol_info = self._symbol_index[symbol]
                
                # Enhance with context if provided
                if context:
                    symbol_info = await self._enhance_symbol_with_context(symbol_info, context)
                
                return symbol_info
            
            # Search for symbol if not in cache
            symbol_info = await self._discover_symbol(symbol, context)
            
            if symbol_info:
                # Cache the result
                self._symbol_index[symbol] = symbol_info
                
                # Update dependency graph
                await self._update_dependency_graph(symbol_info)
            
            return symbol_info
            
        except Exception as e:
            logger.error(f"Error getting symbol info for '{symbol}': {e}")
            return None
    
    async def analyze_symbol_impact(
        self,
        symbol: str,
        change_type: str = "modification"
    ) -> Dict[str, Any]:
        """
        Analyze the impact of changing a symbol.
        
        Args:
            symbol: Symbol to analyze
            change_type: Type of change (modification, deletion, rename)
            
        Returns:
            Impact analysis results
        """
        try:
            impact_analysis = {
                'symbol': symbol,
                'change_type': change_type,
                'affected_files': [],
                'affected_symbols': [],
                'impact_level': 'low',
                'recommendations': [],
                'risk_factors': []
            }
            
            # Get symbol info
            symbol_info = await self.get_symbol_info(symbol)
            if not symbol_info:
                impact_analysis['impact_level'] = 'unknown'
                impact_analysis['risk_factors'].append('Symbol not found in index')
                return impact_analysis
            
            # Analyze direct dependencies
            direct_deps = self._dependency_graph.get(symbol, set())
            impact_analysis['affected_symbols'].extend(list(direct_deps))
            
            # Analyze reverse dependencies (what depends on this symbol)
            reverse_deps = self._find_reverse_dependencies(symbol)
            impact_analysis['affected_symbols'].extend(list(reverse_deps))
            
            # Collect affected files
            affected_files = set()
            for ref in symbol_info.references:
                if 'file_path' in ref:
                    affected_files.add(ref['file_path'])
            
            for usage in symbol_info.usages:
                if 'file_path' in usage:
                    affected_files.add(usage['file_path'])
            
            impact_analysis['affected_files'] = list(affected_files)
            
            # Determine impact level
            impact_analysis['impact_level'] = self._calculate_impact_level(
                len(affected_files),
                len(impact_analysis['affected_symbols']),
                symbol_info.symbol_type
            )
            
            # Generate recommendations
            impact_analysis['recommendations'] = self._generate_impact_recommendations(
                symbol_info,
                change_type,
                impact_analysis['impact_level']
            )
            
            # Identify risk factors
            impact_analysis['risk_factors'] = self._identify_risk_factors(
                symbol_info,
                change_type,
                len(affected_files)
            )
            
            return impact_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing symbol impact for '{symbol}': {e}")
            return {
                'symbol': symbol,
                'change_type': change_type,
                'impact_level': 'unknown',
                'error': str(e)
            }
    
    async def get_symbol_relationships(self, symbol: str) -> Dict[str, Any]:
        """Get relationships for a symbol (dependencies, dependents, etc.)."""
        try:
            relationships = {
                'symbol': symbol,
                'dependencies': [],
                'dependents': [],
                'related_symbols': [],
                'inheritance_chain': [],
                'composition_relationships': []
            }
            
            # Get direct dependencies
            dependencies = self._dependency_graph.get(symbol, set())
            relationships['dependencies'] = list(dependencies)
            
            # Get dependents (reverse dependencies)
            dependents = self._find_reverse_dependencies(symbol)
            relationships['dependents'] = list(dependents)
            
            # Find related symbols (same file, similar names, etc.)
            related = await self._find_related_symbols(symbol)
            relationships['related_symbols'] = related
            
            # Analyze inheritance if it's a class
            symbol_info = await self.get_symbol_info(symbol)
            if symbol_info and symbol_info.symbol_type == 'class':
                relationships['inheritance_chain'] = await self._analyze_inheritance_chain(symbol)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error getting symbol relationships for '{symbol}': {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    async def search_symbols(
        self,
        query: str,
        symbol_type: Optional[str] = None,
        file_pattern: Optional[str] = None,
        limit: int = 50
    ) -> List[SymbolInfo]:
        """Search for symbols matching criteria."""
        try:
            results = []
            
            # Search in symbol index
            for symbol_name, symbol_info in self._symbol_index.items():
                # Check name match
                if query.lower() not in symbol_name.lower():
                    continue
                
                # Check type filter
                if symbol_type and symbol_info.symbol_type != symbol_type:
                    continue
                
                # Check file pattern
                if file_pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(symbol_info.file_path, file_pattern):
                        continue
                
                results.append(symbol_info)
                
                if len(results) >= limit:
                    break
            
            # Sort by relevance (exact matches first, then partial)
            results.sort(key=lambda s: (
                0 if s.name == query else 1,  # Exact match first
                -len(s.references),  # More references = more relevant
                s.name.lower()  # Alphabetical
            ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching symbols: {e}")
            return []
    
    async def get_usage_patterns(self, symbol: str) -> Dict[str, Any]:
        """Get usage patterns for a symbol."""
        try:
            if symbol not in self._usage_patterns:
                await self._analyze_usage_patterns(symbol)
            
            patterns = self._usage_patterns.get(symbol, [])
            
            return {
                'symbol': symbol,
                'total_usages': len(patterns),
                'usage_contexts': self._categorize_usage_contexts(patterns),
                'common_patterns': self._identify_common_patterns(patterns),
                'anti_patterns': self._identify_anti_patterns(patterns)
            }
            
        except Exception as e:
            logger.error(f"Error getting usage patterns for '{symbol}': {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    async def refresh_symbol_index(self, file_paths: Optional[List[str]] = None) -> None:
        """Refresh symbol index for specified files or entire codebase."""
        try:
            if file_paths:
                # Refresh specific files
                for file_path in file_paths:
                    await self._index_file(file_path)
                    self._indexed_files.add(file_path)
            else:
                # Refresh entire index
                await self._build_symbol_index()
            
            logger.info(f"Refreshed symbol index for {len(file_paths) if file_paths else 'all'} files")
            
        except Exception as e:
            logger.error(f"Error refreshing symbol index: {e}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the symbol index."""
        return {
            'total_symbols': len(self._symbol_index),
            'indexed_files': len(self._indexed_files),
            'dependency_relationships': sum(len(deps) for deps in self._dependency_graph.values()),
            'last_index_time': self._last_index_time,
            'symbol_types': self._get_symbol_type_distribution(),
            'top_referenced_symbols': self._get_top_referenced_symbols(10)
        }
    
    async def _build_symbol_index(self) -> None:
        """Build the complete symbol index."""
        try:
            # Clear existing index
            self._symbol_index.clear()
            self._dependency_graph.clear()
            self._indexed_files.clear()
            
            # Find all Python files
            python_files = list(self.codebase_path.rglob("*.py"))
            
            # Index each file
            for file_path in python_files:
                try:
                    await self._index_file(str(file_path))
                    self._indexed_files.add(str(file_path))
                except Exception as e:
                    logger.warning(f"Error indexing file {file_path}: {e}")
            
            # Build dependency graph
            await self._build_dependency_graph()
            
            import time
            self._last_index_time = time.time()
            
            logger.info(f"Built symbol index: {len(self._symbol_index)} symbols from {len(self._indexed_files)} files")
            
        except Exception as e:
            logger.error(f"Error building symbol index: {e}")
    
    async def _index_file(self, file_path: str) -> None:
        """Index symbols in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Find function definitions
            for i, line in enumerate(lines):
                # Function definitions
                func_match = re.match(r'\s*def\s+(\w+)\s*\(([^)]*)\):', line)
                if func_match:
                    func_name = func_match.group(1)
                    params = func_match.group(2)
                    
                    symbol_info = SymbolInfo(
                        name=func_name,
                        symbol_type='function',
                        file_path=file_path,
                        line_number=i + 1,
                        character=line.find('def'),
                        signature=f"def {func_name}({params})",
                        scope=self._determine_scope(lines, i)
                    )
                    
                    # Find references and usages
                    symbol_info.references = self._find_symbol_references_in_content(func_name, content, file_path)
                    symbol_info.usages = self._find_symbol_usages_in_content(func_name, content, file_path)
                    
                    self._symbol_index[func_name] = symbol_info
                
                # Class definitions
                class_match = re.match(r'\s*class\s+(\w+)(?:\([^)]*\))?:', line)
                if class_match:
                    class_name = class_match.group(1)
                    
                    symbol_info = SymbolInfo(
                        name=class_name,
                        symbol_type='class',
                        file_path=file_path,
                        line_number=i + 1,
                        character=line.find('class'),
                        signature=line.strip(),
                        scope='global'
                    )
                    
                    symbol_info.references = self._find_symbol_references_in_content(class_name, content, file_path)
                    symbol_info.usages = self._find_symbol_usages_in_content(class_name, content, file_path)
                    
                    self._symbol_index[class_name] = symbol_info
                
                # Variable assignments (simplified)
                var_match = re.match(r'\s*(\w+)\s*=', line)
                if var_match and not line.strip().startswith('#'):
                    var_name = var_match.group(1)
                    
                    # Skip common non-variable patterns
                    if var_name not in ['if', 'for', 'while', 'def', 'class']:
                        symbol_info = SymbolInfo(
                            name=var_name,
                            symbol_type='variable',
                            file_path=file_path,
                            line_number=i + 1,
                            character=line.find(var_name),
                            scope=self._determine_scope(lines, i)
                        )
                        
                        # Only add if not already exists (avoid duplicates)
                        if var_name not in self._symbol_index:
                            self._symbol_index[var_name] = symbol_info
            
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
    
    def _determine_scope(self, lines: List[str], line_index: int) -> str:
        """Determine the scope of a symbol based on indentation."""
        current_line = lines[line_index]
        indent_level = len(current_line) - len(current_line.lstrip())
        
        if indent_level == 0:
            return 'global'
        
        # Look backwards to find containing scope
        for i in range(line_index - 1, -1, -1):
            line = lines[i]
            if line.strip():
                line_indent = len(line) - len(line.lstrip())
                if line_indent < indent_level:
                    if 'class ' in line:
                        class_match = re.search(r'class\s+(\w+)', line)
                        if class_match:
                            return class_match.group(1)
                    elif 'def ' in line:
                        func_match = re.search(r'def\s+(\w+)', line)
                        if func_match:
                            return func_match.group(1)
        
        return 'local'
    
    def _find_symbol_references_in_content(
        self,
        symbol_name: str,
        content: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Find references to a symbol in file content."""
        references = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for symbol references (not definitions)
            if symbol_name in line and not line.strip().startswith(f'def {symbol_name}') and not line.strip().startswith(f'class {symbol_name}'):
                matches = re.finditer(rf'\b{re.escape(symbol_name)}\b', line)
                for match in matches:
                    references.append({
                        'file_path': file_path,
                        'line': i + 1,
                        'character': match.start(),
                        'context': line.strip()
                    })
        
        return references
    
    def _find_symbol_usages_in_content(
        self,
        symbol_name: str,
        content: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Find usages of a symbol in file content."""
        # For now, usages are the same as references
        # Could be enhanced to distinguish between different usage types
        return self._find_symbol_references_in_content(symbol_name, content, file_path)
    
    async def _discover_symbol(
        self,
        symbol: str,
        context: Optional[AnalysisContext] = None
    ) -> Optional[SymbolInfo]:
        """Discover a symbol not in the index."""
        # Search through files for the symbol
        if context and context.file_path:
            # Search in the context file first
            await self._index_file(context.file_path)
            if symbol in self._symbol_index:
                return self._symbol_index[symbol]
        
        # Search in all indexed files
        for file_path in self._indexed_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if f'def {symbol}(' in content or f'class {symbol}' in content:
                    await self._index_file(file_path)
                    if symbol in self._symbol_index:
                        return self._symbol_index[symbol]
            except Exception as e:
                logger.debug(f"Failed to search for symbol {symbol} in file {file_path}: {e}")
                continue
        
        return None
    
    async def _enhance_symbol_with_context(
        self,
        symbol_info: SymbolInfo,
        context: AnalysisContext
    ) -> SymbolInfo:
        """Enhance symbol info with additional context."""
        # Add context-specific information
        if context.include_dependencies:
            symbol_info.dependencies = list(self._dependency_graph.get(symbol_info.name, set()))
        
        return symbol_info
    
    async def _update_dependency_graph(self, symbol_info: SymbolInfo) -> None:
        """Update dependency graph with symbol information."""
        symbol_name = symbol_info.name
        
        if symbol_name not in self._dependency_graph:
            self._dependency_graph[symbol_name] = set()
        
        # Analyze dependencies from symbol content
        try:
            with open(symbol_info.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find import statements and function calls
            for other_symbol in self._symbol_index:
                if other_symbol != symbol_name and other_symbol in content:
                    self._dependency_graph[symbol_name].add(other_symbol)
        
        except Exception as e:
            logger.error(f"Error updating dependency graph for {symbol_name}: {e}")
    
    async def _build_dependency_graph(self) -> None:
        """Build the complete dependency graph."""
        for symbol_info in self._symbol_index.values():
            await self._update_dependency_graph(symbol_info)
    
    def _find_reverse_dependencies(self, symbol: str) -> Set[str]:
        """Find symbols that depend on the given symbol."""
        reverse_deps = set()
        
        for dependent, dependencies in self._dependency_graph.items():
            if symbol in dependencies:
                reverse_deps.add(dependent)
        
        return reverse_deps
    
    def _calculate_impact_level(
        self,
        affected_files_count: int,
        affected_symbols_count: int,
        symbol_type: str
    ) -> str:
        """Calculate the impact level of a symbol change."""
        if affected_files_count > 10 or affected_symbols_count > 20:
            return 'high'
        elif affected_files_count > 3 or affected_symbols_count > 5:
            return 'medium'
        elif symbol_type in ['class', 'function'] and (affected_files_count > 1 or affected_symbols_count > 1):
            return 'medium'
        else:
            return 'low'
    
    def _generate_impact_recommendations(
        self,
        symbol_info: SymbolInfo,
        change_type: str,
        impact_level: str
    ) -> List[str]:
        """Generate recommendations based on impact analysis."""
        recommendations = []
        
        if impact_level == 'high':
            recommendations.append("Consider breaking this change into smaller, incremental changes")
            recommendations.append("Ensure comprehensive testing of all affected components")
            recommendations.append("Consider deprecation warnings before removal")
        
        if change_type == 'deletion':
            recommendations.append("Verify all references are properly handled")
            recommendations.append("Consider providing migration path for dependent code")
        
        if symbol_info.symbol_type == 'class':
            recommendations.append("Check inheritance hierarchies for breaking changes")
            recommendations.append("Verify interface compatibility")
        
        return recommendations
    
    def _identify_risk_factors(
        self,
        symbol_info: SymbolInfo,
        change_type: str,
        affected_files_count: int
    ) -> List[str]:
        """Identify risk factors for the symbol change."""
        risk_factors = []
        
        if affected_files_count > 5:
            risk_factors.append("High number of affected files")
        
        if symbol_info.symbol_type == 'class':
            risk_factors.append("Class changes can affect inheritance hierarchies")
        
        if change_type == 'deletion':
            risk_factors.append("Deletion may break dependent code")
        
        if len(symbol_info.references) > 10:
            risk_factors.append("Symbol has many references")
        
        return risk_factors
    
    async def _find_related_symbols(self, symbol: str) -> List[str]:
        """Find symbols related to the given symbol."""
        related = []
        
        symbol_info = self._symbol_index.get(symbol)
        if not symbol_info:
            return related
        
        # Find symbols in the same file
        for other_symbol, other_info in self._symbol_index.items():
            if other_symbol != symbol and other_info.file_path == symbol_info.file_path:
                related.append(other_symbol)
        
        # Find symbols with similar names
        for other_symbol in self._symbol_index:
            if other_symbol != symbol:
                # Simple similarity check
                if (symbol.lower() in other_symbol.lower() or 
                    other_symbol.lower() in symbol.lower()):
                    related.append(other_symbol)
        
        return related[:10]  # Limit results
    
    async def _analyze_inheritance_chain(self, class_symbol: str) -> List[str]:
        """Analyze inheritance chain for a class symbol."""
        # Simplified inheritance analysis
        # In a real implementation, this would parse class definitions more thoroughly
        return []
    
    async def _analyze_usage_patterns(self, symbol: str) -> None:
        """Analyze usage patterns for a symbol."""
        patterns = []
        
        symbol_info = self._symbol_index.get(symbol)
        if not symbol_info:
            return
        
        # Analyze each usage
        for usage in symbol_info.usages:
            pattern = {
                'file_path': usage.get('file_path'),
                'context': usage.get('context'),
                'line': usage.get('line'),
                'usage_type': self._classify_usage_type(usage.get('context', ''))
            }
            patterns.append(pattern)
        
        self._usage_patterns[symbol] = patterns
    
    def _classify_usage_type(self, context: str) -> str:
        """Classify the type of symbol usage."""
        context = context.strip().lower()
        
        if context.startswith('import ') or context.startswith('from '):
            return 'import'
        elif '=' in context and context.index('=') < context.find(context.split()[-1]):
            return 'assignment'
        elif '(' in context:
            return 'function_call'
        else:
            return 'reference'
    
    def _categorize_usage_contexts(self, patterns: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize usage contexts."""
        contexts = {}
        for pattern in patterns:
            usage_type = pattern.get('usage_type', 'unknown')
            contexts[usage_type] = contexts.get(usage_type, 0) + 1
        return contexts
    
    def _identify_common_patterns(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Identify common usage patterns."""
        # Simplified pattern identification
        return ["Standard function call pattern", "Import usage pattern"]
    
    def _identify_anti_patterns(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Identify anti-patterns in usage."""
        # Simplified anti-pattern detection
        return []
    
    def _get_symbol_type_distribution(self) -> Dict[str, int]:
        """Get distribution of symbol types."""
        distribution = {}
        for symbol_info in self._symbol_index.values():
            symbol_type = symbol_info.symbol_type
            distribution[symbol_type] = distribution.get(symbol_type, 0) + 1
        return distribution
    
    def _get_top_referenced_symbols(self, limit: int) -> List[Dict[str, Any]]:
        """Get top referenced symbols."""
        symbols_with_refs = [
            {
                'symbol': symbol_info.name,
                'references': len(symbol_info.references),
                'type': symbol_info.symbol_type
            }
            for symbol_info in self._symbol_index.values()
        ]
        
        symbols_with_refs.sort(key=lambda x: x['references'], reverse=True)
        return symbols_with_refs[:limit]
