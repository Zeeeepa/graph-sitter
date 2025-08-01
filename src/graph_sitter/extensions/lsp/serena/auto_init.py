"""
Auto-initialization for Serena Integration

This module automatically integrates Serena capabilities into the Codebase class
when imported. It should be imported after the Codebase class is defined.
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def initialize_serena_integration() -> bool:
    """Initialize Serena integration with the Codebase class."""
    try:
        # Import Codebase class
        from graph_sitter.core.codebase import Codebase
        
        # Add Serena methods to Codebase
        add_serena_to_codebase(Codebase)
        
        logger.info("✅ Serena LSP integration successfully added to Codebase class")
        logger.info("🚀 Available methods: get_completions, get_hover_info, rename_symbol, extract_method, semantic_search, and more!")
        
        return True
        
    except ImportError as e:
        logger.warning(f"Could not import Codebase class for Serena integration: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Serena integration: {e}")
        return False


def add_serena_to_codebase(codebase_class: type) -> None:
    """Add Serena methods to the Codebase class."""
    
    # Import Serena components
    from .core import SerenaCore, get_or_create_core
    from .types import SerenaConfig, SerenaCapability
    from .lsp_integration import SerenaLSPIntegration
    
    # Import unified error interface
    from .unified_error_interface import add_unified_error_interface
    
    async def get_serena_core(self) -> Optional[SerenaCore]:
        """Get or create Serena core instance for this codebase."""
        if not hasattr(self, '_serena_core'):
            try:
                config = SerenaConfig()
                self._serena_core = await get_or_create_core(str(self.root_path), config)
                
                # Set up LSP integration if available
                if hasattr(self, '_serena_lsp_integration'):
                    self._serena_core.set_lsp_integration(self._serena_lsp_integration)
                
            except Exception as e:
                logger.error(f"Error creating Serena core: {e}")
                return None
        
        return getattr(self, '_serena_core', None)
    
    async def get_serena_lsp_integration(self) -> Optional[SerenaLSPIntegration]:
        """Get or create Serena LSP integration for this codebase."""
        if not hasattr(self, '_serena_lsp_integration'):
            try:
                from .lsp_integration import SerenaLSPIntegration
                self._serena_lsp_integration = SerenaLSPIntegration(str(self.root_path))
                await self._serena_lsp_integration.initialize()
                
                # Connect to core if available
                serena_core = await self.get_serena_core()
                if serena_core:
                    serena_core.set_lsp_integration(self._serena_lsp_integration)
                
            except Exception as e:
                logger.error(f"Error creating Serena LSP integration: {e}")
                return None
        
        return getattr(self, '_serena_lsp_integration', None)
    
    # LSP Integration Methods
    async def get_completions(
        self,
        file_path: str,
        line: int,
        character: int,
        context: Optional[str] = None
    ) -> list:
        """Get code completions at the specified position."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                completions = await serena_core.get_completions(file_path, line, character, context)
                return [completion.to_dict() for completion in completions]
            
            # Fallback to LSP integration
            lsp_integration = await self.get_serena_lsp_integration()
            if lsp_integration:
                return await lsp_integration.get_completions(file_path, line, character)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting completions: {e}")
            return []
    
    async def get_hover_info(
        self,
        file_path: str,
        line: int,
        character: int
    ) -> Optional[dict]:
        """Get hover information at the specified position."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                hover_info = await serena_core.get_hover_info(file_path, line, character)
                return hover_info.to_dict() if hover_info else None
            
            # Fallback to LSP integration
            lsp_integration = await self.get_serena_lsp_integration()
            if lsp_integration:
                return await lsp_integration.get_hover_info(file_path, line, character)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting hover info: {e}")
            return None
    
    async def get_diagnostics(
        self,
        file_path: Optional[str] = None
    ) -> list:
        """Get diagnostics/errors for a file or entire codebase."""
        try:
            lsp_integration = await self.get_serena_lsp_integration()
            if lsp_integration:
                if file_path:
                    return await lsp_integration.get_file_diagnostics(file_path)
                else:
                    return await lsp_integration.get_all_diagnostics()
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting diagnostics: {e}")
            return []
    
    # Refactoring Methods
    async def rename_symbol(
        self,
        file_path: str,
        line: int,
        character: int,
        new_name: str
    ) -> dict:
        """Rename a symbol at the specified position."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                result = await serena_core.get_refactoring_result(
                    'rename',
                    file_path=file_path,
                    line=line,
                    character=character,
                    old_name='',  # Will be determined automatically
                    new_name=new_name
                )
                return result.to_dict()
            
            return {'success': False, 'error': 'Serena core not available'}
            
        except Exception as e:
            logger.error(f"Error renaming symbol: {e}")
            return {'success': False, 'error': str(e)}
    
    async def extract_method(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        method_name: str
    ) -> dict:
        """Extract selected code into a new method."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                result = await serena_core.get_refactoring_result(
                    'extract_method',
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    new_name=method_name,
                    extract_type='method'
                )
                return result.to_dict()
            
            return {'success': False, 'error': 'Serena core not available'}
            
        except Exception as e:
            logger.error(f"Error extracting method: {e}")
            return {'success': False, 'error': str(e)}
    
    async def extract_variable(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        variable_name: str
    ) -> dict:
        """Extract selected expression into a variable."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                result = await serena_core.get_refactoring_result(
                    'extract_variable',
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    new_name=variable_name,
                    extract_type='variable'
                )
                return result.to_dict()
            
            return {'success': False, 'error': 'Serena core not available'}
            
        except Exception as e:
            logger.error(f"Error extracting variable: {e}")
            return {'success': False, 'error': str(e)}
    
    # Symbol Intelligence Methods
    async def get_symbol_info(
        self,
        symbol: str,
        file_path: Optional[str] = None
    ) -> Optional[dict]:
        """Get comprehensive information about a symbol."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                from .types import AnalysisContext
                context = AnalysisContext(file_path=file_path) if file_path else None
                symbol_info = await serena_core.get_symbol_info(symbol, context)
                
                if symbol_info:
                    return {
                        'name': symbol_info.name,
                        'type': symbol_info.symbol_type,
                        'file_path': symbol_info.file_path,
                        'line_number': symbol_info.line_number,
                        'character': symbol_info.character,
                        'scope': symbol_info.scope,
                        'signature': symbol_info.signature,
                        'documentation': symbol_info.documentation,
                        'references': symbol_info.references,
                        'dependencies': symbol_info.dependencies,
                        'usages': symbol_info.usages
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    async def analyze_symbol_impact(
        self,
        symbol: str,
        change_type: str = "modification"
    ) -> dict:
        """Analyze the impact of changing a symbol."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                return await serena_core.get_capability('symbol_intelligence').analyze_symbol_impact(
                    symbol, change_type
                )
            
            return {'symbol': symbol, 'error': 'Symbol intelligence not available'}
            
        except Exception as e:
            logger.error(f"Error analyzing symbol impact: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    # Code Actions Methods
    async def get_code_actions(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        context: Optional[list] = None
    ) -> list:
        """Get available code actions for the specified range."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                actions = await serena_core.get_code_actions(
                    file_path, start_line, end_line, context or []
                )
                return [
                    {
                        'id': action.id,
                        'title': action.title,
                        'kind': action.kind,
                        'description': action.description,
                        'is_preferred': action.is_preferred,
                        'disabled_reason': action.disabled_reason
                    }
                    for action in actions
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting code actions: {e}")
            return []
    
    async def apply_code_action(
        self,
        action_id: str,
        file_path: str,
        **kwargs
    ) -> dict:
        """Apply a specific code action."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                return await serena_core.apply_code_action(action_id, file_path=file_path, **kwargs)
            
            return {'success': False, 'error': 'Serena core not available'}
            
        except Exception as e:
            logger.error(f"Error applying code action: {e}")
            return {'success': False, 'error': str(e)}
    
    # Search and Generation Methods
    async def semantic_search(
        self,
        query: str,
        **kwargs
    ) -> dict:
        """Perform semantic search in the codebase."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                result = await serena_core.semantic_search(query, **kwargs)
                return result.to_dict()
            
            return {
                'query': query,
                'results': [],
                'total_count': 0,
                'search_time': 0.0,
                'error': 'Semantic search not available'
            }
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return {
                'query': query,
                'results': [],
                'total_count': 0,
                'search_time': 0.0,
                'error': str(e)
            }
    
    async def generate_code(
        self,
        prompt: str,
        file_path: Optional[str] = None,
        context: Optional[dict] = None
    ) -> dict:
        """Generate code using AI assistance."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core:
                from .types import AnalysisContext
                analysis_context = None
                if file_path or context:
                    analysis_context = AnalysisContext(
                        file_path=file_path or '',
                        cursor_position=context.get('cursor_position') if context else None,
                        selection_range=context.get('selection_range') if context else None
                    )
                
                result = await serena_core.generate_code(prompt, analysis_context)
                return result.to_dict()
            
            return {
                'success': False,
                'generated_code': '',
                'error': 'Code generation not available'
            }
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return {
                'success': False,
                'generated_code': '',
                'error': str(e)
            }
    
    # Real-time Analysis Methods
    async def enable_realtime_analysis(
        self,
        watch_patterns: Optional[list] = None
    ) -> bool:
        """Enable real-time file monitoring and analysis."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core and serena_core.is_capability_enabled(SerenaCapability.REAL_TIME_ANALYSIS):
                realtime_analyzer = serena_core.get_capability(SerenaCapability.REAL_TIME_ANALYSIS)
                if realtime_analyzer:
                    return await realtime_analyzer.enable_analysis(
                        watch_patterns or ['*.py', '*.js', '*.ts']
                    )
            
            return False
            
        except Exception as e:
            logger.error(f"Error enabling real-time analysis: {e}")
            return False
    
    async def disable_realtime_analysis(self) -> bool:
        """Disable real-time file monitoring and analysis."""
        try:
            serena_core = await self.get_serena_core()
            if serena_core and serena_core.is_capability_enabled(SerenaCapability.REAL_TIME_ANALYSIS):
                realtime_analyzer = serena_core.get_capability(SerenaCapability.REAL_TIME_ANALYSIS)
                if realtime_analyzer:
                    return await realtime_analyzer.disable_analysis()
            
            return False
            
        except Exception as e:
            logger.error(f"Error disabling real-time analysis: {e}")
            return False
    
    # Status and Configuration Methods
    async def get_serena_status(self) -> dict:
        """Get comprehensive Serena integration status."""
        try:
            status = {
                'integration_active': False,
                'lsp_integration': False,
                'core_initialized': False,
                'enabled_capabilities': [],
                'active_capabilities': [],
                'performance_metrics': {}
            }
            
            # Check LSP integration
            lsp_integration = await self.get_serena_lsp_integration()
            if lsp_integration:
                status['lsp_integration'] = True
                lsp_status = lsp_integration.get_status()
                status.update(lsp_status)
            
            # Check core
            serena_core = await self.get_serena_core()
            if serena_core:
                status['core_initialized'] = True
                core_status = serena_core.get_status()
                status.update(core_status)
                status['integration_active'] = True
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting Serena status: {e}")
            return {'error': str(e)}
    
    async def configure_serena(
        self,
        config: Optional[dict] = None
    ) -> bool:
        """Configure Serena integration settings."""
        try:
            if config:
                from .types import SerenaConfig
                
                # Create new config from dict
                serena_config = SerenaConfig()
                for key, value in config.items():
                    if hasattr(serena_config, key):
                        setattr(serena_config, key, value)
                
                # Reinitialize with new config
                if hasattr(self, '_serena_core'):
                    await self._serena_core.shutdown()
                    delattr(self, '_serena_core')
                
                self._serena_core = await get_or_create_core(str(self.root_path), serena_config)
                
                logger.info("Serena configuration updated")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error configuring Serena: {e}")
            return False
    
    # Add all methods to the Codebase class
    methods_to_add = [
        # Core methods
        'get_serena_core',
        'get_serena_lsp_integration',
        
        # LSP Integration
        'get_completions',
        'get_hover_info', 
        'get_diagnostics',
        
        # Refactoring
        'rename_symbol',
        'extract_method',
        'extract_variable',
        
        # Symbol Intelligence
        'get_symbol_info',
        'analyze_symbol_impact',
        
        # Code Actions
        'get_code_actions',
        'apply_code_action',
        
        # Search and Generation
        'semantic_search',
        'generate_code',
        
        # Real-time Analysis
        'enable_realtime_analysis',
        'disable_realtime_analysis',
        
        # Status and Configuration
        'get_serena_status',
        'configure_serena'
    ]
    
    # Add methods to class
    for method_name in methods_to_add:
        method = locals()[method_name]
        setattr(codebase_class, method_name, method)
    
    # Add unified error interface methods
    add_unified_error_interface(codebase_class)
    
    logger.debug(f"Added {len(methods_to_add)} Serena methods + unified error interface to Codebase class")


# Auto-initialize when this module is imported
_initialized = initialize_serena_integration()
