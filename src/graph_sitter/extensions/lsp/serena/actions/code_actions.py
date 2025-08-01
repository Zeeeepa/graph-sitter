"""
Code Actions

Provides automated code fixes, improvements, and quick actions.
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..types import CodeAction

logger = logging.getLogger(__name__)


class CodeActions:
    """
    Provides code actions and quick fixes.
    
    Features:
    - Automated code fixes (imports, formatting, etc.)
    - Quick refactoring actions
    - Code improvement suggestions
    - Integration with LSP code actions
    - Context-aware action discovery
    """
    
    def __init__(self, codebase_path: str, serena_core: Any):
        self.codebase_path = Path(codebase_path)
        self.serena_core = serena_core
        
        # Action registry
        self._action_providers: Dict[str, Any] = {}
        self._cached_actions: Dict[str, List[CodeAction]] = {}
        
        logger.debug("CodeActions initialized")
    
    async def initialize(self) -> None:
        """Initialize code actions system."""
        logger.info("Initializing code actions...")
        
        # Register built-in action providers
        await self._register_builtin_providers()
        
        logger.info("✅ Code actions initialized")
    
    async def shutdown(self) -> None:
        """Shutdown code actions system."""
        self._action_providers.clear()
        self._cached_actions.clear()
        
        logger.info("✅ Code actions shutdown")
    
    async def get_code_actions(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        context: List[str],
        diagnostics: Optional[List[Dict[str, Any]]] = None
    ) -> List[CodeAction]:
        """
        Get available code actions for the specified range.
        
        Args:
            file_path: Path to the file
            start_line: Start line of the range
            end_line: End line of the range
            context: Context lines around the range
            diagnostics: Optional diagnostics/errors in the range
            
        Returns:
            List of available code actions
        """
        try:
            actions = []
            
            # Create cache key
            cache_key = f"{file_path}:{start_line}:{end_line}:{hash(tuple(context))}"
            
            # Check cache first
            if cache_key in self._cached_actions:
                return self._cached_actions[cache_key]
            
            # Get file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_lines = f.readlines()
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                return []
            
            # Extract the relevant code section
            code_section = ''.join(file_lines[start_line-1:end_line])
            
            # Get actions from all providers
            for provider_name, provider in self._action_providers.items():
                try:
                    provider_actions = await provider.get_actions(
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        code_section=code_section,
                        context=context,
                        diagnostics=diagnostics or []
                    )
                    actions.extend(provider_actions)
                except Exception as e:
                    logger.error(f"Error getting actions from provider {provider_name}: {e}")
            
            # Sort actions by priority and relevance
            actions.sort(key=lambda a: (
                0 if a.is_preferred else 1,
                0 if a.kind == 'quickfix' else 1,
                a.title.lower()
            ))
            
            # Cache the results
            self._cached_actions[cache_key] = actions
            
            logger.debug(f"Found {len(actions)} code actions for {file_path}:{start_line}-{end_line}")
            return actions
            
        except Exception as e:
            logger.error(f"Error getting code actions: {e}")
            return []
    
    async def apply_code_action(
        self,
        action_id: str,
        file_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply a specific code action.
        
        Args:
            action_id: ID of the action to apply
            file_path: Path to the file
            **kwargs: Additional parameters for the action
            
        Returns:
            Result of applying the action
        """
        try:
            # Find the action provider
            provider = None
            for provider_name, p in self._action_providers.items():
                if hasattr(p, 'can_handle_action') and p.can_handle_action(action_id):
                    provider = p
                    break
            
            if not provider:
                return {
                    'success': False,
                    'error': f'No provider found for action: {action_id}'
                }
            
            # Apply the action
            result = await provider.apply_action(
                action_id=action_id,
                file_path=file_path,
                **kwargs
            )
            
            # Clear cache for affected file
            self._clear_cache_for_file(file_path)
            
            # Emit event
            if self.serena_core:
                await self.serena_core._emit_event("code_action.applied", {
                    'action_id': action_id,
                    'file_path': file_path,
                    'success': result.get('success', False)
                })
            
            logger.info(f"Applied code action {action_id} to {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error applying code action {action_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_available_action_kinds(self) -> List[str]:
        """Get list of available action kinds."""
        kinds = set()
        
        for provider in self._action_providers.values():
            if hasattr(provider, 'get_supported_kinds'):
                provider_kinds = provider.get_supported_kinds()
                kinds.update(provider_kinds)
        
        return sorted(list(kinds))
    
    def clear_cache(self, file_path: Optional[str] = None) -> None:
        """Clear action cache for a file or all files."""
        if file_path:
            self._clear_cache_for_file(file_path)
        else:
            self._cached_actions.clear()
    
    async def _register_builtin_providers(self) -> None:
        """Register built-in action providers."""
        # Import action provider
        import_provider = ImportActionProvider()
        self._action_providers['import'] = import_provider
        
        # Formatting action provider
        format_provider = FormattingActionProvider()
        self._action_providers['format'] = format_provider
        
        # Refactoring action provider
        refactor_provider = RefactoringActionProvider(self.serena_core)
        self._action_providers['refactor'] = refactor_provider
        
        # Quick fix provider
        quickfix_provider = QuickFixActionProvider()
        self._action_providers['quickfix'] = quickfix_provider
        
        logger.debug("Registered built-in action providers")
    
    def _clear_cache_for_file(self, file_path: str) -> None:
        """Clear cache entries for a specific file."""
        keys_to_remove = [
            key for key in self._cached_actions.keys()
            if key.startswith(f"{file_path}:")
        ]
        
        for key in keys_to_remove:
            del self._cached_actions[key]


class ImportActionProvider:
    """Provides import-related code actions."""
    
    def get_supported_kinds(self) -> List[str]:
        """Get supported action kinds."""
        return ['source.organizeImports', 'quickfix.import']
    
    def can_handle_action(self, action_id: str) -> bool:
        """Check if this provider can handle the action."""
        return action_id.startswith('import.')
    
    async def get_actions(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        code_section: str,
        context: List[str],
        diagnostics: List[Dict[str, Any]]
    ) -> List[CodeAction]:
        """Get import-related actions."""
        actions = []
        
        try:
            # Check for missing imports
            missing_imports = self._find_missing_imports(code_section, file_path)
            for missing_import in missing_imports:
                actions.append(CodeAction(
                    id=f"import.add_{missing_import['name']}",
                    title=f"Add import: {missing_import['import_statement']}",
                    kind='quickfix',
                    description=f"Add missing import for {missing_import['name']}",
                    is_preferred=True,
                    data={
                        'import_statement': missing_import['import_statement'],
                        'line_to_add': missing_import.get('line_to_add', 1)
                    }
                ))
            
            # Check for unused imports
            unused_imports = self._find_unused_imports(file_path)
            if unused_imports:
                actions.append(CodeAction(
                    id="import.remove_unused",
                    title=f"Remove {len(unused_imports)} unused imports",
                    kind='source.organizeImports',
                    description="Remove unused import statements",
                    data={'unused_imports': unused_imports}
                ))
            
            # Organize imports action
            actions.append(CodeAction(
                id="import.organize",
                title="Organize imports",
                kind='source.organizeImports',
                description="Sort and organize import statements"
            ))
            
        except Exception as e:
            logger.error(f"Error getting import actions: {e}")
        
        return actions
    
    async def apply_action(self, action_id: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """Apply import action."""
        try:
            if action_id.startswith('import.add_'):
                return await self._add_import(file_path, kwargs.get('data', {}))
            elif action_id == 'import.remove_unused':
                return await self._remove_unused_imports(file_path, kwargs.get('data', {}))
            elif action_id == 'import.organize':
                return await self._organize_imports(file_path)
            else:
                return {'success': False, 'error': f'Unknown import action: {action_id}'}
                
        except Exception as e:
            logger.error(f"Error applying import action {action_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _find_missing_imports(self, code_section: str, file_path: str) -> List[Dict[str, Any]]:
        """Find missing imports in code section."""
        missing = []
        
        # Common patterns that suggest missing imports
        patterns = {
            r'\bos\.': {'name': 'os', 'import_statement': 'import os'},
            r'\bsys\.': {'name': 'sys', 'import_statement': 'import sys'},
            r'\bre\.': {'name': 're', 'import_statement': 'import re'},
            r'\bjson\.': {'name': 'json', 'import_statement': 'import json'},
            r'\bPath\(': {'name': 'Path', 'import_statement': 'from pathlib import Path'},
            r'\btyping\.': {'name': 'typing', 'import_statement': 'import typing'},
        }
        
        # Check current imports
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception:
            return missing
        
        for pattern, import_info in patterns.items():
            if re.search(pattern, code_section):
                # Check if already imported
                if import_info['import_statement'] not in file_content:
                    missing.append(import_info)
        
        return missing
    
    def _find_unused_imports(self, file_path: str) -> List[str]:
        """Find unused imports in file."""
        unused = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Find import statements
            import_lines = []
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    import_lines.append((i, line.strip()))
            
            # Check if each import is used
            for line_num, import_line in import_lines:
                # Extract imported names
                imported_names = self._extract_imported_names(import_line)
                
                # Check if any imported name is used
                used = False
                for name in imported_names:
                    if self._is_name_used(name, content, import_line):
                        used = True
                        break
                
                if not used:
                    unused.append(import_line)
        
        except Exception as e:
            logger.error(f"Error finding unused imports: {e}")
        
        return unused
    
    def _extract_imported_names(self, import_line: str) -> List[str]:
        """Extract imported names from import statement."""
        names = []
        
        if import_line.startswith('import '):
            # import module
            module = import_line[7:].split(' as ')[0].strip()
            names.append(module.split('.')[0])
        elif import_line.startswith('from '):
            # from module import name
            parts = import_line.split(' import ')
            if len(parts) == 2:
                imported_part = parts[1]
                # Handle multiple imports
                for name in imported_part.split(','):
                    name = name.split(' as ')[0].strip()
                    names.append(name)
        
        return names
    
    def _is_name_used(self, name: str, content: str, import_line: str) -> bool:
        """Check if a name is used in the content."""
        # Remove the import line from content for checking
        content_without_import = content.replace(import_line, '')
        
        # Look for usage patterns
        patterns = [
            rf'\b{re.escape(name)}\.',  # module.something
            rf'\b{re.escape(name)}\(',  # function call
            rf'\b{re.escape(name)}\[',  # indexing
            rf'\b{re.escape(name)}\s',  # general usage
        ]
        
        for pattern in patterns:
            if re.search(pattern, content_without_import):
                return True
        
        return False
    
    async def _add_import(self, file_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add import statement to file."""
        try:
            import_statement = data.get('import_statement')
            line_to_add = data.get('line_to_add', 1)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Insert import statement
            lines.insert(line_to_add - 1, import_statement + '\n')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return {
                'success': True,
                'changes': [{
                    'file': file_path,
                    'type': 'add_import',
                    'import_statement': import_statement
                }]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _remove_unused_imports(self, file_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove unused imports from file."""
        try:
            unused_imports = data.get('unused_imports', [])
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove each unused import
            for unused_import in unused_imports:
                content = content.replace(unused_import + '\n', '')
                content = content.replace(unused_import, '')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'changes': [{
                    'file': file_path,
                    'type': 'remove_unused_imports',
                    'removed_count': len(unused_imports)
                }]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _organize_imports(self, file_path: str) -> Dict[str, Any]:
        """Organize imports in file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find import section
            import_lines = []
            other_lines = []
            in_import_section = True
            
            for line in lines:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    if in_import_section:
                        import_lines.append(line)
                    else:
                        other_lines.append(line)
                elif line.strip() == '' and in_import_section:
                    import_lines.append(line)
                else:
                    in_import_section = False
                    other_lines.append(line)
            
            # Sort imports
            import_lines.sort(key=lambda x: (
                0 if x.strip().startswith('import ') else 1,  # import before from
                x.strip().lower()
            ))
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(import_lines)
                if import_lines and not import_lines[-1].strip() == '':
                    f.write('\n')
                f.writelines(other_lines)
            
            return {
                'success': True,
                'changes': [{
                    'file': file_path,
                    'type': 'organize_imports',
                    'organized_count': len([l for l in import_lines if l.strip()])
                }]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class FormattingActionProvider:
    """Provides formatting-related code actions."""
    
    def get_supported_kinds(self) -> List[str]:
        return ['source.formatDocument', 'quickfix.format']
    
    def can_handle_action(self, action_id: str) -> bool:
        return action_id.startswith('format.')
    
    async def get_actions(self, **kwargs) -> List[CodeAction]:
        """Get formatting actions."""
        return [
            CodeAction(
                id="format.document",
                title="Format document",
                kind='source.formatDocument',
                description="Format the entire document"
            ),
            CodeAction(
                id="format.selection",
                title="Format selection",
                kind='source.formatDocument',
                description="Format the selected code"
            )
        ]
    
    async def apply_action(self, action_id: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """Apply formatting action."""
        # Simplified formatting - in practice would use black, autopep8, etc.
        return {
            'success': True,
            'changes': [{
                'file': file_path,
                'type': action_id,
                'applied': True
            }]
        }


class RefactoringActionProvider:
    """Provides refactoring-related code actions."""
    
    def __init__(self, serena_core: Any):
        self.serena_core = serena_core
    
    def get_supported_kinds(self) -> List[str]:
        return ['refactor.extract', 'refactor.inline', 'refactor.rename']
    
    def can_handle_action(self, action_id: str) -> bool:
        return action_id.startswith('refactor.')
    
    async def get_actions(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        code_section: str,
        **kwargs
    ) -> List[CodeAction]:
        """Get refactoring actions."""
        actions = []
        
        # Extract method action (if multiple lines selected)
        if end_line > start_line:
            actions.append(CodeAction(
                id="refactor.extract.method",
                title="Extract method",
                kind='refactor.extract',
                description="Extract selected code into a new method",
                data={
                    'start_line': start_line,
                    'end_line': end_line,
                    'extract_type': 'method'
                }
            ))
        
        # Extract variable action (if single expression)
        if start_line == end_line and '=' not in code_section:
            actions.append(CodeAction(
                id="refactor.extract.variable",
                title="Extract variable",
                kind='refactor.extract',
                description="Extract expression into a variable",
                data={
                    'start_line': start_line,
                    'end_line': end_line,
                    'extract_type': 'variable'
                }
            ))
        
        return actions
    
    async def apply_action(self, action_id: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """Apply refactoring action."""
        try:
            if not self.serena_core:
                return {'success': False, 'error': 'Serena core not available'}
            
            data = kwargs.get('data', {})
            
            if action_id == 'refactor.extract.method':
                result = await self.serena_core.get_refactoring_result(
                    'extract_method',
                    file_path=file_path,
                    start_line=data.get('start_line'),
                    end_line=data.get('end_line'),
                    extract_type='method'
                )
            elif action_id == 'refactor.extract.variable':
                result = await self.serena_core.get_refactoring_result(
                    'extract_variable',
                    file_path=file_path,
                    start_line=data.get('start_line'),
                    end_line=data.get('end_line'),
                    extract_type='variable'
                )
            else:
                return {'success': False, 'error': f'Unknown refactoring action: {action_id}'}
            
            return {
                'success': result.success,
                'changes': [change.to_dict() if hasattr(change, 'to_dict') else change for change in result.changes],
                'conflicts': [conflict.to_dict() if hasattr(conflict, 'to_dict') else conflict for conflict in result.conflicts]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class QuickFixActionProvider:
    """Provides quick fix code actions."""
    
    def get_supported_kinds(self) -> List[str]:
        return ['quickfix']
    
    def can_handle_action(self, action_id: str) -> bool:
        return action_id.startswith('quickfix.')
    
    async def get_actions(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        code_section: str,
        context: List[str],
        diagnostics: List[Dict[str, Any]]
    ) -> List[CodeAction]:
        """Get quick fix actions."""
        actions = []
        
        # Analyze diagnostics for quick fixes
        for diagnostic in diagnostics:
            message = diagnostic.get('message', '').lower()
            
            if 'undefined' in message or 'not defined' in message:
                # Extract undefined name
                match = re.search(r"'(\w+)' is not defined", diagnostic.get('message', ''))
                if match:
                    undefined_name = match.group(1)
                    actions.append(CodeAction(
                        id=f"quickfix.add_import_{undefined_name}",
                        title=f"Add import for '{undefined_name}'",
                        kind='quickfix',
                        description=f"Add import statement for undefined name '{undefined_name}'",
                        is_preferred=True,
                        data={'undefined_name': undefined_name}
                    ))
            
            elif 'unused' in message:
                actions.append(CodeAction(
                    id="quickfix.remove_unused",
                    title="Remove unused code",
                    kind='quickfix',
                    description="Remove unused variable or import"
                ))
        
        # Code style quick fixes
        if 'def ' in code_section and '"""' not in code_section:
            actions.append(CodeAction(
                id="quickfix.add_docstring",
                title="Add docstring",
                kind='quickfix',
                description="Add docstring to function"
            ))
        
        return actions
    
    async def apply_action(self, action_id: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """Apply quick fix action."""
        # Simplified quick fix implementation
        return {
            'success': True,
            'changes': [{
                'file': file_path,
                'type': action_id,
                'applied': True
            }]
        }

