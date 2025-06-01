"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
import hashlib
import time

from ..context.codebase_analyzer import CodebaseAnalyzer
from ..context.prompt_enhancer import PromptEnhancer
from ..monitoring.performance_monitor import PerformanceMonitor
from ..monitoring.usage_tracker import UsageTracker
from .cache_manager import CacheManager
from .config import AutogenConfig
from codegen import Agent

from graph_sitter.codebase.codebase_analysis import (
from graph_sitter.core.codebase import Codebase

Enhanced Autogenlib Client with Codegen SDK Integration

This module provides the core client implementation that integrates with
the Codegen SDK while leveraging graph_sitter's codebase analysis capabilities.
"""

try:
except ImportError:
    # Fallback for development/testing
    class Agent:
        def __init__(self, org_id: str, token: str):
            self.org_id = org_id
            self.token = token
        
        def run(self, prompt: str):
            # Mock implementation for development
            return MockTask(prompt)

    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary
)

@dataclass
class CallerContext:
    """Context information about the code that's calling for generation"""
    file_path: str
    function_name: str
    line_number: int
    local_variables: Dict[str, Any]
    usage_example: str

@dataclass
class GeneratedCode:
    """Result of code generation"""
    code: str
    metadata: Dict[str, Any]
    usage_info: Dict[str, Any]
    generation_time: float
    cache_hit: bool = False

class AutogenClient:
    """Enhanced autogenlib client with Codegen SDK integration"""
    
    def __init__(self, config: AutogenConfig):
        self.config = config
        
        # Initialize Codegen SDK agent
        self.codegen_agent = Agent(
            org_id=config.org_id,
            token=config.token
        )
        
        # Initialize components
        self.cache_manager = CacheManager(config.cache_config)
        self.usage_tracker = UsageTracker(config.org_id)
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize codebase analysis if path provided
        self.codebase_analyzer = None
        self.prompt_enhancer = None
        
        if config.codebase_path:
            self._initialize_codebase_analysis(config.codebase_path)
    
    def _initialize_codebase_analysis(self, codebase_path: str):
        """Initialize codebase analysis components"""
        try:
            # Load codebase using graph_sitter
            if Path(codebase_path).is_dir():
                self.codebase = Codebase.from_path(codebase_path)
            else:
                # Assume it's a git URL
                self.codebase = Codebase.from_repo(codebase_path)
            
            self.codebase_analyzer = CodebaseAnalyzer(self.codebase)
            self.prompt_enhancer = PromptEnhancer(self.codebase_analyzer)
            
        except Exception as e:
            print(f"Warning: Could not initialize codebase analysis: {e}")
            self.codebase_analyzer = None
            self.prompt_enhancer = None
    
    async def generate_code(self, 
                          module_path: str, 
                          function_name: str,
                          caller_context: Optional[CallerContext] = None,
                          **kwargs) -> GeneratedCode:
        """Generate code with enhanced context and caching"""
        
        start_time = time.time()
        
        try:
            # 1. Generate cache key
            cache_key = self._generate_cache_key(
                module_path, function_name, caller_context, kwargs
            )
            
            # 2. Check cache if enabled
            if self.config.enable_caching:
                cached_result = await self.cache_manager.get(cache_key)
                if cached_result:
                    cached_result.cache_hit = True
                    self.usage_tracker.record_cache_hit(module_path, function_name)
                    return cached_result
            
            # 3. Analyze codebase context if available
            codebase_context = None
            if self.codebase_analyzer and self.config.enable_context_enhancement:
                codebase_context = await self.codebase_analyzer.analyze_context(
                    module_path, function_name, caller_context
                )
            
            # 4. Enhance prompt with context
            enhanced_prompt = self._create_enhanced_prompt(
                module_path, function_name, caller_context, codebase_context, kwargs
            )
            
            # 5. Generate via Codegen SDK
            task = self.codegen_agent.run(prompt=enhanced_prompt)
            result = await self._wait_for_completion(task)
            
            # 6. Process and format result
            generated_code = GeneratedCode(
                code=result.get('code', ''),
                metadata=result.get('metadata', {}),
                usage_info=result.get('usage_info', {}),
                generation_time=time.time() - start_time,
                cache_hit=False
            )
            
            # 7. Cache result if enabled
            if self.config.enable_caching:
                await self.cache_manager.set(cache_key, generated_code)
            
            # 8. Track usage
            self.usage_tracker.record_generation(
                module_path, function_name, len(generated_code.code)
            )
            
            # 9. Record performance metrics
            self.performance_monitor.record_generation(
                module_path, function_name, generated_code.generation_time
            )
            
            return generated_code
            
        except Exception as e:
            self.usage_tracker.record_error(module_path, function_name, str(e))
            raise
    
    async def generate_batch(self, 
                           requests: List[Dict[str, Any]], 
                           max_concurrent: int = None) -> List[GeneratedCode]:
        """Generate multiple code pieces concurrently"""
        
        if max_concurrent is None:
            max_concurrent = self.config.max_concurrent_requests
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(request):
            async with semaphore:
                return await self.generate_code(**request)
        
        tasks = [generate_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(GeneratedCode(
                    code="",
                    metadata={"error": str(result)},
                    usage_info={},
                    generation_time=0.0
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _generate_cache_key(self, 
                          module_path: str, 
                          function_name: str,
                          caller_context: Optional[CallerContext],
                          kwargs: Dict[str, Any]) -> str:
        """Generate a cache key for the request"""
        
        key_components = [
            module_path,
            function_name,
            str(caller_context.__dict__ if caller_context else {}),
            str(sorted(kwargs.items()))
        ]
        
        # Include codebase hash if available for cache invalidation
        if self.codebase_analyzer:
            codebase_hash = self.codebase_analyzer.get_codebase_hash()
            key_components.append(codebase_hash)
        
        key_string = "|".join(key_components)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def _create_enhanced_prompt(self,
                              module_path: str,
                              function_name: str, 
                              caller_context: Optional[CallerContext],
                              codebase_context: Optional[Dict[str, Any]],
                              kwargs: Dict[str, Any]) -> str:
        """Create an enhanced prompt with context"""
        
        base_prompt = f"Generate the function '{function_name}' in module '{module_path}'"
        
        # Add any additional requirements from kwargs
        if 'requirements' in kwargs:
            base_prompt += f"\n\nRequirements: {kwargs['requirements']}"
        
        # Use prompt enhancer if available
        if self.prompt_enhancer and codebase_context:
            return self.prompt_enhancer.enhance_prompt(
                base_prompt, codebase_context, caller_context
            )
        
        # Fallback to basic prompt
        if caller_context:
            base_prompt += f"\n\nCaller context:\n- File: {caller_context.file_path}"
            base_prompt += f"\n- Usage: {caller_context.usage_example}"
        
        return base_prompt
    
    async def _wait_for_completion(self, task, timeout: int = None) -> Dict[str, Any]:
        """Wait for Codegen SDK task completion with timeout"""
        
        if timeout is None:
            timeout = self.config.task_timeout_seconds
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Refresh task status
                task.refresh()
                
                if task.status == "completed":
                    return {
                        'code': task.result,
                        'metadata': getattr(task, 'metadata', {}),
                        'usage_info': {
                            'tokens_used': getattr(task, 'tokens_used', 0),
                            'cost_estimate': getattr(task, 'cost_estimate', 0.0)
                        }
                    }
                elif task.status == "failed":
                    raise Exception(f"Task failed: {getattr(task, 'error', 'Unknown error')}")
                
                # Wait before checking again
                await asyncio.sleep(1)
                
            except Exception as e:
                if "completed" in str(e).lower():
                    # Task might be completed but with an error in status check
                    return {
                        'code': getattr(task, 'result', ''),
                        'metadata': {},
                        'usage_info': {}
                    }
                raise
        
        raise TimeoutError(f"Task timed out after {timeout} seconds")
    
    async def get_usage_report(self, time_range: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get usage and cost report"""
        return self.usage_tracker.get_usage_report(time_range)
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_monitor.get_metrics()
    
    async def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries"""
        await self.cache_manager.clear(pattern)
    
    def get_codebase_summary(self) -> Optional[str]:
        """Get summary of the analyzed codebase"""
        if self.codebase:
            return get_codebase_summary(self.codebase)
        return None

# Mock task for development/testing
class MockTask:
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.status = "pending"
        self.result = f"# Generated code for: {prompt}\npass"
    
    def refresh(self):
        self.status = "completed"
