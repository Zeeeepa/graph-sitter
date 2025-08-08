"""
Serena Core Integration

Main orchestrator for all Serena LSP capabilities in graph-sitter.
Coordinates between LSP integration, refactoring, symbol intelligence, and other advanced features.
"""

import asyncio
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum

from .types import (
    SerenaCapability, 
    SerenaConfig, 
    RefactoringResult,
    SymbolInfo,
    CodeAction,
    CodeGenerationResult,
    SemanticSearchResult,
    HoverInfo,
    CompletionItem,
    AnalysisContext,
    PerformanceMetrics,
    EventSubscription,
    EventHandler,
    AsyncEventHandler
)

logger = logging.getLogger(__name__)


class SerenaCore:
    """
    Core Serena integration for graph-sitter.
    
    Orchestrates all Serena LSP capabilities and provides unified interface
    for real-time code intelligence, refactoring, and advanced analysis.
    
    Features:
    - Capability management and coordination
    - Event-driven architecture
    - Performance monitoring
    - Background processing
    - LSP integration coordination
    """
    
    def __init__(self, codebase_path: str, config: Optional[SerenaConfig] = None):
        self.codebase_path = Path(codebase_path)
        self.config = config or SerenaConfig()
        
        # Core state
        self._capabilities: Dict[SerenaCapability, Any] = {}
        self._initialized = False
        self._shutdown_requested = False
        
        # Event system
        self._event_subscriptions: Dict[str, List[EventSubscription]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Background processing
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._background_thread: Optional[threading.Thread] = None
        self._background_tasks: List[asyncio.Task] = []
        
        # Performance tracking
        self._performance_metrics: List[PerformanceMetrics] = []
        self._operation_counts: Dict[str, int] = {}
        
        # LSP integration reference (will be set by LSP integration)
        self._lsp_integration: Optional[Any] = None
        
        logger.info(f"SerenaCore initialized for codebase: {self.codebase_path}")
    
    async def initialize(self) -> bool:
        """
        Initialize all enabled capabilities.
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True
        
        try:
            logger.info("Initializing Serena core capabilities...")
            
            # Start background processing if needed
            if self.config.realtime_analysis:
                await self._start_background_processing()
            
            # Initialize enabled capabilities
            await self._initialize_capabilities()
            
            # Emit initialization event
            await self._emit_event("core.initialized", {
                'capabilities': [cap.value for cap in self.config.enabled_capabilities],
                'config': self.config.__dict__
            })
            
            self._initialized = True
            logger.info("✅ Serena core initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Serena core: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown all capabilities and background processing."""
        if not self._initialized:
            return
        
        logger.info("Shutting down Serena core...")
        self._shutdown_requested = True
        
        try:
            # Emit shutdown event
            await self._emit_event("core.shutting_down", {})
            
            # Shutdown capabilities
            for capability, instance in self._capabilities.items():
                if hasattr(instance, 'shutdown'):
                    try:
                        if asyncio.iscoroutinefunction(instance.shutdown):
                            await instance.shutdown()
                        else:
                            instance.shutdown()
                    except Exception as e:
                        logger.error(f"Error shutting down {capability.value}: {e}")
            
            # Cancel background tasks
            for task in self._background_tasks:
                task.cancel()
            
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            # Stop background thread
            if self._background_thread and self._background_thread.is_alive():
                self._background_thread.join(timeout=5.0)
            
            self._capabilities.clear()
            self._background_tasks.clear()
            self._event_subscriptions.clear()
            
            self._initialized = False
            logger.info("✅ Serena core shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during Serena core shutdown: {e}")
    
    def set_lsp_integration(self, lsp_integration: Any) -> None:
        """Set reference to LSP integration for coordination."""
        self._lsp_integration = lsp_integration
        logger.debug("LSP integration reference set")
    
    def get_capability(self, capability: SerenaCapability) -> Optional[Any]:
        """Get instance of a specific capability."""
        return self._capabilities.get(capability)
    
    def is_capability_enabled(self, capability: SerenaCapability) -> bool:
        """Check if a capability is enabled and available."""
        return (
            capability in self.config.enabled_capabilities and
            capability in self._capabilities
        )
    
    async def get_refactoring_result(self, refactoring_type: str, **kwargs) -> RefactoringResult:
        """Get refactoring result through the refactoring engine."""
        if not self.is_capability_enabled(SerenaCapability.REFACTORING):
            return RefactoringResult(
                success=False,
                refactoring_type=None,
                changes=[],
                conflicts=[],
                error_message="Refactoring capability not enabled"
            )
        
        refactoring_engine = self._capabilities[SerenaCapability.REFACTORING]
        return await refactoring_engine.perform_refactoring(refactoring_type, **kwargs)
    
    async def get_symbol_info(self, symbol: str, context: Optional[AnalysisContext] = None) -> Optional[SymbolInfo]:
        """Get symbol information through symbol intelligence."""
        if not self.is_capability_enabled(SerenaCapability.SYMBOL_INTELLIGENCE):
            return None
        
        symbol_intelligence = self._capabilities[SerenaCapability.SYMBOL_INTELLIGENCE]
        return await symbol_intelligence.get_symbol_info(symbol, context)
    
    async def get_code_actions(self, file_path: str, start_line: int, end_line: int, context: List[str]) -> List[CodeAction]:
        """Get available code actions."""
        if not self.is_capability_enabled(SerenaCapability.CODE_ACTIONS):
            return []
        
        code_actions = self._capabilities[SerenaCapability.CODE_ACTIONS]
        return await code_actions.get_code_actions(file_path, start_line, end_line, context)
    
    async def apply_code_action(self, action_id: str, **kwargs) -> Dict[str, Any]:
        """Apply a specific code action."""
        if not self.is_capability_enabled(SerenaCapability.CODE_ACTIONS):
            return {'success': False, 'error': 'Code actions capability not enabled'}
        
        code_actions = self._capabilities[SerenaCapability.CODE_ACTIONS]
        return await code_actions.apply_code_action(action_id, **kwargs)
    
    async def generate_code(self, prompt: str, context: Optional[AnalysisContext] = None) -> CodeGenerationResult:
        """Generate code using AI assistance."""
        if not self.is_capability_enabled(SerenaCapability.CODE_GENERATION):
            return CodeGenerationResult(
                success=False,
                generated_code="",
                error_message="Code generation capability not enabled"
            )
        
        code_generator = self._capabilities[SerenaCapability.CODE_GENERATION]
        return await code_generator.generate_code(prompt, context)
    
    async def semantic_search(self, query: str, **kwargs) -> SemanticSearchResult:
        """Perform semantic search in the codebase."""
        if not self.is_capability_enabled(SerenaCapability.SEMANTIC_SEARCH):
            return SemanticSearchResult(
                query=query,
                results=[],
                total_count=0,
                search_time=0.0,
                metadata={'error': 'Semantic search capability not enabled'}
            )
        
        semantic_search = self._capabilities[SerenaCapability.SEMANTIC_SEARCH]
        return await semantic_search.search(query, **kwargs)
    
    async def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[HoverInfo]:
        """Get hover information for a position."""
        if not self.is_capability_enabled(SerenaCapability.HOVER_INFO):
            return None
        
        hover_provider = self._capabilities[SerenaCapability.HOVER_INFO]
        return await hover_provider.get_hover_info(file_path, line, character)
    
    async def get_completions(self, file_path: str, line: int, character: int, context: Optional[str] = None) -> List[CompletionItem]:
        """Get code completions for a position."""
        if not self.is_capability_enabled(SerenaCapability.COMPLETIONS):
            return []
        
        completion_provider = self._capabilities[SerenaCapability.COMPLETIONS]
        return await completion_provider.get_completions(file_path, line, character, context)
    
    def subscribe_to_event(self, event_type: str, handler: Union[EventHandler, AsyncEventHandler], priority: int = 0) -> None:
        """Subscribe to an event type."""
        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            is_async=asyncio.iscoroutinefunction(handler),
            priority=priority
        )
        
        if event_type not in self._event_subscriptions:
            self._event_subscriptions[event_type] = []
        
        self._event_subscriptions[event_type].append(subscription)
        
        # Sort by priority (higher priority first)
        self._event_subscriptions[event_type].sort(key=lambda s: s.priority, reverse=True)
        
        logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe_from_event(self, event_type: str, handler: Union[EventHandler, AsyncEventHandler]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._event_subscriptions:
            self._event_subscriptions[event_type] = [
                sub for sub in self._event_subscriptions[event_type]
                if sub.handler != handler
            ]
            logger.debug(f"Unsubscribed from event: {event_type}")
    
    async def _emit_event(self, event_type: str, data: Any) -> None:
        """Emit an event to all subscribers."""
        if event_type not in self._event_subscriptions:
            return
        
        subscriptions = self._event_subscriptions[event_type]
        
        for subscription in subscriptions:
            try:
                if subscription.is_async:
                    await subscription.handler(event_type, data)
                else:
                    subscription.handler(event_type, data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    def get_performance_metrics(self) -> List[Dict[str, Any]]:
        """Get performance metrics for all operations."""
        return [metric.to_dict() for metric in self._performance_metrics]
    
    def get_operation_counts(self) -> Dict[str, int]:
        """Get operation counts."""
        return self._operation_counts.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        return {
            'initialized': self._initialized,
            'codebase_path': str(self.codebase_path),
            'enabled_capabilities': [cap.value for cap in self.config.enabled_capabilities],
            'active_capabilities': [cap.value for cap in self._capabilities.keys()],
            'background_processing': self._background_thread is not None and self._background_thread.is_alive(),
            'event_subscriptions': {
                event_type: len(subscriptions)
                for event_type, subscriptions in self._event_subscriptions.items()
            },
            'operation_counts': self._operation_counts,
            'performance_metrics_count': len(self._performance_metrics)
        }
    
    async def _initialize_capabilities(self) -> None:
        """Initialize all enabled capabilities."""
        for capability in self.config.enabled_capabilities:
            try:
                await self._initialize_capability(capability)
            except Exception as e:
                logger.error(f"Failed to initialize capability {capability.value}: {e}")
    
    async def _initialize_capability(self, capability: SerenaCapability) -> None:
        """Initialize a specific capability."""
        logger.debug(f"Initializing capability: {capability.value}")
        
        if capability == SerenaCapability.REFACTORING:
            from .refactoring.refactoring_engine import RefactoringEngine
            instance = RefactoringEngine(self.codebase_path, self)
            await instance.initialize()
            self._capabilities[capability] = instance
            
        elif capability == SerenaCapability.SYMBOL_INTELLIGENCE:
            from .symbols.symbol_intelligence import SymbolIntelligence
            instance = SymbolIntelligence(self.codebase_path, self)
            await instance.initialize()
            self._capabilities[capability] = instance
            
        elif capability == SerenaCapability.CODE_ACTIONS:
            from .actions.code_actions import CodeActions
            instance = CodeActions(self.codebase_path, self)
            await instance.initialize()
            self._capabilities[capability] = instance
            
        elif capability == SerenaCapability.REAL_TIME_ANALYSIS:
            from .realtime.realtime_analyzer import RealtimeAnalyzer
            instance = RealtimeAnalyzer(self.codebase_path, self)
            await instance.initialize()
            self._capabilities[capability] = instance
            
        elif capability == SerenaCapability.SEMANTIC_SEARCH:
            from .search.semantic_search import SemanticSearch
            instance = SemanticSearch(self.codebase_path, self)
            await instance.initialize()
            self._capabilities[capability] = instance
            
        elif capability == SerenaCapability.CODE_GENERATION:
            from .generation.code_generator import CodeGenerator
            instance = CodeGenerator(self.codebase_path, self)
            await instance.initialize()
            self._capabilities[capability] = instance
            
        elif capability == SerenaCapability.HOVER_INFO:
            from .intelligence.hover import HoverProvider
            instance = HoverProvider(self.codebase_path, self)
            await instance.initialize()
            self._capabilities[capability] = instance
            
        elif capability == SerenaCapability.COMPLETIONS:
            from .intelligence.completions import CompletionProvider
            instance = CompletionProvider(self.codebase_path, self)
            await instance.initialize()
            self._capabilities[capability] = instance
        
        logger.info(f"✅ Initialized capability: {capability.value}")
    
    async def _start_background_processing(self) -> None:
        """Start background processing for real-time features."""
        if self._background_thread and self._background_thread.is_alive():
            return
        
        logger.info("Starting background processing...")
        
        # Create event loop for background thread
        def run_background_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._event_loop = loop
            
            try:
                # Start background tasks
                self._background_tasks = [
                    loop.create_task(self._event_processor()),
                    loop.create_task(self._performance_monitor()),
                ]
                
                # Run until shutdown
                loop.run_until_complete(self._background_runner())
                
            except Exception as e:
                logger.error(f"Error in background processing: {e}")
            finally:
                loop.close()
        
        self._background_thread = threading.Thread(target=run_background_loop, daemon=True)
        self._background_thread.start()
        
        logger.info("✅ Background processing started")
    
    async def _background_runner(self) -> None:
        """Main background processing loop."""
        while not self._shutdown_requested:
            try:
                await asyncio.sleep(1.0)
                
                # Emit heartbeat event
                await self._emit_event("core.heartbeat", {
                    'timestamp': asyncio.get_event_loop().time(),
                    'active_tasks': len(self._background_tasks)
                })
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background runner: {e}")
                await asyncio.sleep(5.0)  # Wait before retrying
    
    async def _event_processor(self) -> None:
        """Process events from the event queue."""
        while not self._shutdown_requested:
            try:
                # Process events with timeout
                try:
                    event_type, data = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=1.0
                    )
                    await self._emit_event(event_type, data)
                except asyncio.TimeoutError:
                    continue
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing events: {e}")
    
    async def _performance_monitor(self) -> None:
        """Monitor performance metrics."""
        while not self._shutdown_requested:
            try:
                await asyncio.sleep(30.0)  # Monitor every 30 seconds
                
                # Clean up old metrics (keep last 1000)
                if len(self._performance_metrics) > 1000:
                    self._performance_metrics = self._performance_metrics[-1000:]
                
                # Emit performance event
                await self._emit_event("core.performance_update", {
                    'metrics_count': len(self._performance_metrics),
                    'operation_counts': self._operation_counts.copy()
                })
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitor: {e}")
    
    def _record_operation(self, operation_name: str, duration: float) -> None:
        """Record an operation for performance tracking."""
        # Update operation count
        self._operation_counts[operation_name] = self._operation_counts.get(operation_name, 0) + 1
        
        # Record performance metric
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=0.0,  # Not tracking start time for recorded operations
            end_time=0.0,
            duration=duration
        )
        
        self._performance_metrics.append(metric)
        
        # Emit operation event
        if self._event_loop:
            asyncio.run_coroutine_threadsafe(
                self._emit_event("core.operation_completed", {
                    'operation': operation_name,
                    'duration': duration,
                    'count': self._operation_counts[operation_name]
                }),
                self._event_loop
            )


# Convenience functions for creating and managing SerenaCore instances
_global_core_instance: Optional[SerenaCore] = None


async def get_or_create_core(codebase_path: str, config: Optional[SerenaConfig] = None) -> SerenaCore:
    """Get or create a global SerenaCore instance."""
    global _global_core_instance
    
    if _global_core_instance is None:
        _global_core_instance = SerenaCore(codebase_path, config)
        await _global_core_instance.initialize()
    
    return _global_core_instance


async def shutdown_global_core() -> None:
    """Shutdown the global SerenaCore instance."""
    global _global_core_instance
    
    if _global_core_instance:
        await _global_core_instance.shutdown()
        _global_core_instance = None


def create_core(codebase_path: str, config: Optional[SerenaConfig] = None) -> SerenaCore:
    """Create a new SerenaCore instance (not global)."""
    return SerenaCore(codebase_path, config)

