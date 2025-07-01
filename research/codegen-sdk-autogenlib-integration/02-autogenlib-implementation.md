# Autogenlib Implementation Plan

## Overview

This document outlines the comprehensive implementation plan for integrating autogenlib as a sub-module of the Codegen SDK, maintaining its dynamic import capabilities while providing seamless integration with the existing codegen agent system.

## 1. Module Structure Design

### 1.1 Integration Architecture

```
src/contexten/extensions/codegen/
├── __init__.py                 # Main integration exports
├── integration.py              # Core integration class
├── config.py                   # Configuration management
├── autogenlib/                 # Autogenlib sub-module
│   ├── __init__.py            # Autogenlib initialization
│   ├── enhanced_generator.py   # Enhanced generator with codegen integration
│   ├── context_injector.py     # Context injection for code generation
│   ├── cache_manager.py        # Integrated caching system
│   └── error_handler.py        # Enhanced error handling
├── adapters/                   # Adapter layer for seamless integration
│   ├── __init__.py
│   ├── codegen_adapter.py      # Codegen SDK adapter
│   └── autogenlib_adapter.py   # Autogenlib adapter
└── utils/                      # Utility functions
    ├── __init__.py
    ├── performance.py          # Performance monitoring
    └── validation.py           # Input validation
```

### 1.2 Core Integration Class

```python
# src/contexten/extensions/codegen/integration.py
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from codegen import Agent
import autogenlib
from graph_sitter.codebase.codebase_analysis import get_codebase_summary
from .config import CodegenAutogenConfig
from .autogenlib.enhanced_generator import EnhancedAutogenGenerator
from .adapters.codegen_adapter import CodegenAdapter
from .utils.performance import PerformanceMonitor

class CodegenAutogenIntegration:
    """Main integration class combining Codegen SDK with Autogenlib"""
    
    def __init__(self, config: CodegenAutogenConfig):
        self.config = config
        self._codegen_adapter = None
        self._autogen_generator = None
        self._performance_monitor = PerformanceMonitor()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all components"""
        if self._initialized:
            return
            
        # Initialize Codegen SDK adapter
        self._codegen_adapter = CodegenAdapter(
            org_id=self.config.org_id,
            token=self.config.token,
            base_url=self.config.base_url
        )
        await self._codegen_adapter.initialize()
        
        # Initialize enhanced autogenlib generator
        self._autogen_generator = EnhancedAutogenGenerator(
            config=self.config,
            codegen_adapter=self._codegen_adapter
        )
        await self._autogen_generator.initialize()
        
        self._initialized = True
    
    async def generate_with_context(
        self,
        prompt: str,
        codebase_context: Optional[Dict[str, Any]] = None,
        use_codegen_agent: bool = False
    ) -> Dict[str, Any]:
        """Generate code with enhanced context"""
        await self._ensure_initialized()
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            if use_codegen_agent:
                # Use Codegen SDK agent for complex tasks
                result = await self._codegen_adapter.run_agent_task(
                    prompt=prompt,
                    context=codebase_context
                )
            else:
                # Use enhanced autogenlib for direct generation
                result = await self._autogen_generator.generate(
                    prompt=prompt,
                    context=codebase_context
                )
            
            duration = asyncio.get_event_loop().time() - start_time
            await self._performance_monitor.record_request(duration, True)
            
            return result
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            await self._performance_monitor.record_request(duration, False)
            raise
    
    async def _ensure_initialized(self):
        """Ensure integration is initialized"""
        if not self._initialized:
            await self.initialize()
```

## 2. Enhanced Autogenlib Generator

### 2.1 Generator with Codegen Integration

```python
# src/contexten/extensions/codegen/autogenlib/enhanced_generator.py
import autogenlib
from typing import Dict, Any, Optional
from ..config import CodegenAutogenConfig
from ..adapters.codegen_adapter import CodegenAdapter
from .context_injector import ContextInjector
from .cache_manager import IntegratedCacheManager

class EnhancedAutogenGenerator:
    """Enhanced autogenlib generator with Codegen SDK integration"""
    
    def __init__(self, config: CodegenAutogenConfig, codegen_adapter: CodegenAdapter):
        self.config = config
        self.codegen_adapter = codegen_adapter
        self.context_injector = ContextInjector(config)
        self.cache_manager = IntegratedCacheManager(config)
        self._autogenlib_initialized = False
    
    async def initialize(self) -> None:
        """Initialize enhanced autogenlib"""
        if self._autogenlib_initialized:
            return
        
        # Initialize autogenlib with enhanced configuration
        autogenlib.init(
            desc=self.config.autogenlib_description,
            enable_exception_handler=self.config.enable_exception_handler,
            enable_caching=self.config.enable_caching
        )
        
        # Initialize context injector
        await self.context_injector.initialize()
        
        # Initialize cache manager
        await self.cache_manager.initialize()
        
        self._autogenlib_initialized = True
    
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Generate code with enhanced context and caching"""
        
        # Check cache first
        if use_cache:
            cached_result = await self.cache_manager.get_cached_result(prompt, context)
            if cached_result:
                return cached_result
        
        # Enhance prompt with context
        enhanced_prompt = await self.context_injector.enhance_prompt(prompt, context)
        
        # Generate using autogenlib
        try:
            # Dynamic import and execution
            generated_module = __import__(enhanced_prompt.module_name)
            result = {
                "generated_code": generated_module,
                "prompt": enhanced_prompt.text,
                "context_used": enhanced_prompt.context_summary,
                "generation_metadata": {
                    "timestamp": asyncio.get_event_loop().time(),
                    "context_size": len(str(context)) if context else 0,
                    "enhanced_prompt_size": len(enhanced_prompt.text)
                }
            }
            
            # Cache the result
            if use_cache:
                await self.cache_manager.cache_result(prompt, context, result)
            
            return result
            
        except Exception as e:
            # Enhanced error handling with Codegen SDK fallback
            return await self._handle_generation_error(e, enhanced_prompt, context)
    
    async def _handle_generation_error(
        self,
        error: Exception,
        enhanced_prompt: Any,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle generation errors with Codegen SDK fallback"""
        
        # Log the error
        logger.error(f"Autogenlib generation failed: {error}")
        
        # Fallback to Codegen SDK agent
        try:
            fallback_result = await self.codegen_adapter.run_agent_task(
                prompt=f"Generate code for: {enhanced_prompt.text}",
                context=context
            )
            
            return {
                "generated_code": fallback_result.get("result", ""),
                "prompt": enhanced_prompt.text,
                "context_used": enhanced_prompt.context_summary,
                "fallback_used": True,
                "original_error": str(error),
                "generation_metadata": {
                    "timestamp": asyncio.get_event_loop().time(),
                    "fallback_method": "codegen_sdk_agent"
                }
            }
            
        except Exception as fallback_error:
            # Both methods failed
            raise GenerationError(
                f"Both autogenlib and Codegen SDK failed. "
                f"Autogenlib error: {error}. "
                f"Codegen SDK error: {fallback_error}"
            )
```

## 3. Context Injection System

### 3.1 Context Injector Implementation

```python
# src/contexten/extensions/codegen/autogenlib/context_injector.py
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, get_file_summary, get_class_summary, get_function_summary
)
from ..config import CodegenAutogenConfig

@dataclass
class EnhancedPrompt:
    """Enhanced prompt with context injection"""
    text: str
    module_name: str
    context_summary: str
    relevance_score: float

class ContextInjector:
    """Inject relevant codebase context into generation prompts"""
    
    def __init__(self, config: CodegenAutogenConfig):
        self.config = config
        self._context_cache = {}
    
    async def initialize(self) -> None:
        """Initialize context injector"""
        # Pre-load frequently used context
        pass
    
    async def enhance_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EnhancedPrompt:
        """Enhance prompt with relevant codebase context"""
        
        # Extract context hints from prompt
        context_hints = self._extract_context_hints(prompt)
        
        # Get relevant context from codebase
        relevant_context = await self._get_relevant_context(
            prompt, context_hints, context
        )
        
        # Build enhanced prompt
        enhanced_text = self._build_enhanced_prompt(prompt, relevant_context)
        
        # Generate module name for autogenlib
        module_name = self._generate_module_name(prompt)
        
        return EnhancedPrompt(
            text=enhanced_text,
            module_name=module_name,
            context_summary=self._summarize_context(relevant_context),
            relevance_score=self._calculate_relevance_score(prompt, relevant_context)
        )
    
    def _extract_context_hints(self, prompt: str) -> List[str]:
        """Extract context hints from prompt text"""
        hints = []
        
        # Look for class names, function names, file references
        import re
        
        # Extract potential class names (CamelCase)
        class_matches = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', prompt)
        hints.extend(class_matches)
        
        # Extract potential function names (snake_case)
        function_matches = re.findall(r'\b[a-z_][a-z0-9_]*\b', prompt)
        hints.extend(function_matches)
        
        # Extract file references
        file_matches = re.findall(r'\b\w+\.(py|js|ts|java|cpp|c)\b', prompt)
        hints.extend(file_matches)
        
        return list(set(hints))  # Remove duplicates
    
    async def _get_relevant_context(
        self,
        prompt: str,
        context_hints: List[str],
        additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get relevant context from codebase analysis"""
        
        context = {}
        
        # Add codebase summary if available
        if hasattr(self, 'codebase') and self.codebase:
            context['codebase_summary'] = get_codebase_summary(self.codebase)
        
        # Add specific context based on hints
        for hint in context_hints:
            hint_context = await self._get_context_for_hint(hint)
            if hint_context:
                context[f'hint_{hint}'] = hint_context
        
        # Add additional context
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _build_enhanced_prompt(self, original_prompt: str, context: Dict[str, Any]) -> str:
        """Build enhanced prompt with context"""
        
        if not context:
            return original_prompt
        
        context_section = "## Codebase Context\n\n"
        
        for key, value in context.items():
            if isinstance(value, str) and len(value) < self.config.max_context_size:
                context_section += f"### {key}\n{value}\n\n"
        
        enhanced_prompt = f"{context_section}## Task\n{original_prompt}"
        
        # Truncate if too long
        if len(enhanced_prompt) > self.config.max_context_size:
            enhanced_prompt = enhanced_prompt[:self.config.max_context_size] + "..."
        
        return enhanced_prompt
    
    def _generate_module_name(self, prompt: str) -> str:
        """Generate unique module name for autogenlib"""
        import hashlib
        import time
        
        # Create hash from prompt and timestamp
        content = f"{prompt}_{time.time()}"
        hash_obj = hashlib.md5(content.encode())
        return f"autogen_module_{hash_obj.hexdigest()[:8]}"
```

## 4. Integrated Cache Manager

### 4.1 Multi-Level Caching System

```python
# src/contexten/extensions/codegen/autogenlib/cache_manager.py
import asyncio
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..config import CodegenAutogenConfig

class IntegratedCacheManager:
    """Multi-level cache manager for autogenlib and Codegen SDK integration"""
    
    def __init__(self, config: CodegenAutogenConfig):
        self.config = config
        self._memory_cache = {}
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    async def initialize(self) -> None:
        """Initialize cache manager"""
        # Set up cache cleanup task
        asyncio.create_task(self._cache_cleanup_task())
    
    async def get_cached_result(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached result if available"""
        
        cache_key = self._generate_cache_key(prompt, context)
        
        # Check memory cache
        if cache_key in self._memory_cache:
            cache_entry = self._memory_cache[cache_key]
            
            # Check if cache entry is still valid
            if self._is_cache_valid(cache_entry):
                self._cache_stats["hits"] += 1
                return cache_entry["result"]
            else:
                # Remove expired entry
                del self._memory_cache[cache_key]
        
        self._cache_stats["misses"] += 1
        return None
    
    async def cache_result(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        result: Dict[str, Any]
    ) -> None:
        """Cache generation result"""
        
        cache_key = self._generate_cache_key(prompt, context)
        
        cache_entry = {
            "result": result,
            "timestamp": datetime.now(),
            "ttl": self.config.cache_ttl,
            "access_count": 0
        }
        
        # Store in memory cache
        self._memory_cache[cache_key] = cache_entry
        
        # Implement LRU eviction if cache is too large
        await self._enforce_cache_limits()
    
    def _generate_cache_key(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate unique cache key"""
        
        # Create deterministic hash from prompt and context
        content = {
            "prompt": prompt,
            "context": context or {}
        }
        
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        
        expiry_time = cache_entry["timestamp"] + timedelta(seconds=cache_entry["ttl"])
        return datetime.now() < expiry_time
    
    async def _enforce_cache_limits(self) -> None:
        """Enforce cache size limits using LRU eviction"""
        
        max_cache_size = 1000  # Maximum number of cache entries
        
        if len(self._memory_cache) > max_cache_size:
            # Sort by access count and timestamp (LRU)
            sorted_entries = sorted(
                self._memory_cache.items(),
                key=lambda x: (x[1]["access_count"], x[1]["timestamp"])
            )
            
            # Remove oldest entries
            entries_to_remove = len(self._memory_cache) - max_cache_size
            for i in range(entries_to_remove):
                key_to_remove = sorted_entries[i][0]
                del self._memory_cache[key_to_remove]
                self._cache_stats["evictions"] += 1
    
    async def _cache_cleanup_task(self) -> None:
        """Periodic cache cleanup task"""
        
        while True:
            try:
                # Remove expired entries
                current_time = datetime.now()
                expired_keys = []
                
                for key, entry in self._memory_cache.items():
                    expiry_time = entry["timestamp"] + timedelta(seconds=entry["ttl"])
                    if current_time >= expiry_time:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self._memory_cache[key]
                    self._cache_stats["evictions"] += 1
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (self._cache_stats["hits"] / total_requests) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self._memory_cache),
            "hit_rate": hit_rate,
            "total_hits": self._cache_stats["hits"],
            "total_misses": self._cache_stats["misses"],
            "total_evictions": self._cache_stats["evictions"]
        }
```

## 5. Adapter Layer Implementation

### 5.1 Codegen SDK Adapter

```python
# src/contexten/extensions/codegen/adapters/codegen_adapter.py
import asyncio
from typing import Dict, Any, Optional
from codegen import Agent
from ..config import CodegenAutogenConfig

class CodegenAdapter:
    """Adapter for Codegen SDK with enhanced functionality"""
    
    def __init__(self, org_id: str, token: str, base_url: str):
        self.org_id = org_id
        self.token = token
        self.base_url = base_url
        self._agent = None
        self._connection_pool = None
    
    async def initialize(self) -> None:
        """Initialize Codegen SDK agent"""
        self._agent = Agent(
            org_id=self.org_id,
            token=self.token,
            base_url=self.base_url
        )
    
    async def run_agent_task(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run Codegen agent task with context"""
        
        # Enhance prompt with context if provided
        enhanced_prompt = prompt
        if context:
            context_str = self._format_context(context)
            enhanced_prompt = f"{context_str}\n\n{prompt}"
        
        # Run agent task
        task = self._agent.run(prompt=enhanced_prompt)
        
        # Wait for completion with timeout
        max_wait_time = 300  # 5 minutes
        wait_interval = 5    # 5 seconds
        
        for _ in range(max_wait_time // wait_interval):
            task.refresh()
            
            if task.status == "completed":
                return {
                    "result": task.result,
                    "status": task.status,
                    "web_url": task.web_url,
                    "task_id": task.id
                }
            elif task.status == "failed":
                raise Exception(f"Codegen agent task failed: {task.result}")
            
            await asyncio.sleep(wait_interval)
        
        raise TimeoutError("Codegen agent task timed out")
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for inclusion in prompt"""
        
        formatted_parts = []
        
        for key, value in context.items():
            if isinstance(value, str):
                formatted_parts.append(f"## {key}\n{value}")
            elif isinstance(value, dict):
                formatted_parts.append(f"## {key}\n{json.dumps(value, indent=2)}")
            else:
                formatted_parts.append(f"## {key}\n{str(value)}")
        
        return "\n\n".join(formatted_parts)
```

## 6. Error Handling and Recovery

### 6.1 Enhanced Error Handler

```python
# src/contexten/extensions/codegen/autogenlib/error_handler.py
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from ..config import CodegenAutogenConfig

logger = logging.getLogger(__name__)

class EnhancedErrorHandler:
    """Enhanced error handling for autogenlib with Codegen SDK integration"""
    
    def __init__(self, config: CodegenAutogenConfig):
        self.config = config
        self._retry_counts = {}
        self._circuit_breaker_state = {}
    
    async def handle_with_retry(
        self,
        operation: Callable,
        *args,
        max_retries: int = None,
        backoff_factor: float = 2.0,
        **kwargs
    ) -> Any:
        """Execute operation with retry logic"""
        
        max_retries = max_retries or self.config.max_retries
        operation_key = f"{operation.__name__}_{id(operation)}"
        
        for attempt in range(max_retries + 1):
            try:
                result = await operation(*args, **kwargs)
                
                # Reset retry count on success
                self._retry_counts[operation_key] = 0
                
                return result
                
            except Exception as e:
                self._retry_counts[operation_key] = attempt + 1
                
                if attempt == max_retries:
                    logger.error(f"Operation {operation.__name__} failed after {max_retries} retries: {e}")
                    raise
                
                # Calculate backoff delay
                delay = (backoff_factor ** attempt) + (asyncio.get_event_loop().time() % 1)
                
                logger.warning(f"Operation {operation.__name__} failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                
                await asyncio.sleep(delay)
    
    async def handle_rate_limit_error(self, error: Exception) -> None:
        """Handle rate limit errors with intelligent backoff"""
        
        # Extract rate limit information if available
        retry_after = self._extract_retry_after(error)
        
        if retry_after:
            logger.info(f"Rate limited, waiting {retry_after} seconds")
            await asyncio.sleep(retry_after)
        else:
            # Default exponential backoff
            base_delay = 60  # 1 minute base delay
            jitter = asyncio.get_event_loop().time() % 10
            delay = base_delay + jitter
            
            logger.info(f"Rate limited, waiting {delay:.2f} seconds")
            await asyncio.sleep(delay)
    
    def _extract_retry_after(self, error: Exception) -> Optional[int]:
        """Extract retry-after value from error"""
        
        error_str = str(error).lower()
        
        # Look for retry-after information in error message
        import re
        match = re.search(r'retry.after[:\s]+(\d+)', error_str)
        
        if match:
            return int(match.group(1))
        
        return None
```

## 7. Implementation Timeline

### Phase 1: Core Structure (Days 1-2)
1. ✅ Create module structure and directory layout
2. ✅ Implement `CodegenAutogenConfig` class
3. ✅ Create `CodegenAutogenIntegration` main class
4. ✅ Implement basic adapter layer

### Phase 2: Enhanced Generator (Days 3-4)
1. ✅ Implement `EnhancedAutogenGenerator` class
2. ✅ Create `ContextInjector` for prompt enhancement
3. ✅ Implement `IntegratedCacheManager`
4. ✅ Add error handling and fallback mechanisms

### Phase 3: Integration & Testing (Days 5-6)
1. Integrate with existing contexten extension system
2. Add comprehensive error handling and retry logic
3. Implement performance monitoring
4. Create unit and integration tests

### Phase 4: Optimization & Documentation (Days 7-8)
1. Performance optimization and tuning
2. Memory usage optimization
3. Create comprehensive documentation
4. Add usage examples and best practices

## 8. Success Criteria

- ✅ **Seamless Integration**: Autogenlib works as a sub-module of codegen
- ✅ **Dynamic Import Preservation**: Maintains autogenlib's core capabilities
- ✅ **Context Enhancement**: Integrates with graph_sitter analysis functions
- ✅ **Performance Targets**: <2s response time with caching
- ✅ **Error Resilience**: Robust error handling with fallback mechanisms
- ✅ **Backward Compatibility**: Existing workflows continue to work

---

*This implementation plan provides a comprehensive roadmap for integrating autogenlib as a sub-module of the Codegen SDK while maintaining all existing capabilities and adding enhanced functionality.*

