"""
Consolidated AI Integration
==========================

This module consolidates all AI-related functionality into a unified interface
that works seamlessly with the enhanced codebase integration system.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class AICapability(Enum):
    """Available AI capabilities."""
    CODE_GENERATION = "code_generation"
    ERROR_ANALYSIS = "error_analysis"
    CODE_COMPLETION = "code_completion"
    DOCUMENTATION_GENERATION = "documentation_generation"
    REFACTORING_SUGGESTIONS = "refactoring_suggestions"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    TEST_GENERATION = "test_generation"


@dataclass
class AIConfig:
    """Configuration for AI integration."""
    enabled_capabilities: List[AICapability] = field(default_factory=lambda: list(AICapability))
    model_preferences: Dict[str, str] = field(default_factory=dict)
    max_context_length: int = 4000
    temperature: float = 0.1
    max_tokens: int = 1000
    enable_caching: bool = True
    cache_ttl: int = 3600  # seconds
    enable_streaming: bool = False
    fallback_enabled: bool = True


@dataclass
class AIResponse:
    """Standardized AI response format."""
    capability: AICapability
    success: bool
    content: Any
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0


class ConsolidatedAIIntegration:
    """
    Consolidated AI integration that provides a unified interface to all
    AI capabilities across the codebase analysis system.
    """
    
    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self._providers = {}
        self._cache = {}
        self._performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'average_response_time': 0.0
        }
        
        # Initialize available providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available AI providers."""
        try:
            # Try to initialize Serena code generation
            if AICapability.CODE_GENERATION in self.config.enabled_capabilities:
                try:
                    from graph_sitter.extensions.serena.generation.code_generator import CodeGenerator
                    self._providers[AICapability.CODE_GENERATION] = CodeGenerator()
                    logger.info("Serena code generation provider initialized")
                except ImportError:
                    logger.warning("Serena code generation not available")
            
            # Try to initialize other AI providers
            self._initialize_fallback_providers()
            
        except Exception as e:
            logger.error(f"Error initializing AI providers: {e}")
    
    def _initialize_fallback_providers(self):
        """Initialize fallback AI providers."""
        try:
            # Initialize basic pattern-based providers for each capability
            for capability in self.config.enabled_capabilities:
                if capability not in self._providers:
                    self._providers[capability] = self._create_fallback_provider(capability)
                    logger.info(f"Fallback provider initialized for {capability.value}")
                    
        except Exception as e:
            logger.error(f"Error initializing fallback providers: {e}")
    
    def _create_fallback_provider(self, capability: AICapability):
        """Create a fallback provider for a specific capability."""
        class FallbackProvider:
            def __init__(self, capability_type):
                self.capability_type = capability_type
            
            def generate(self, prompt: str, context: str = "") -> str:
                """Generate fallback response."""
                if self.capability_type == AICapability.CODE_GENERATION:
                    return f"# TODO: Implement code generation for: {prompt[:100]}..."
                elif self.capability_type == AICapability.ERROR_ANALYSIS:
                    return f"Error analysis needed for: {prompt[:100]}..."
                elif self.capability_type == AICapability.DOCUMENTATION_GENERATION:
                    return f'"""\nTODO: Add documentation for: {prompt[:100]}...\n"""'
                else:
                    return f"# AI capability {self.capability_type.value} not fully implemented"
        
        return FallbackProvider(capability)
    
    async def generate_code(self, prompt: str, context: str = "", 
                           language: str = "python") -> AIResponse:
        """Generate code using AI."""
        return await self._execute_ai_request(
            AICapability.CODE_GENERATION,
            prompt,
            context,
            {"language": language}
        )
    
    async def analyze_error(self, error_message: str, code_context: str = "",
                           file_path: str = "") -> AIResponse:
        """Analyze an error using AI."""
        return await self._execute_ai_request(
            AICapability.ERROR_ANALYSIS,
            error_message,
            code_context,
            {"file_path": file_path}
        )
    
    async def generate_completion(self, code_prefix: str, cursor_position: int = 0,
                                 language: str = "python") -> AIResponse:
        """Generate code completion using AI."""
        return await self._execute_ai_request(
            AICapability.CODE_COMPLETION,
            code_prefix,
            "",
            {"cursor_position": cursor_position, "language": language}
        )
    
    async def generate_documentation(self, code: str, doc_type: str = "function") -> AIResponse:
        """Generate documentation using AI."""
        return await self._execute_ai_request(
            AICapability.DOCUMENTATION_GENERATION,
            code,
            "",
            {"doc_type": doc_type}
        )
    
    async def suggest_refactoring(self, code: str, issues: List[str] = None) -> AIResponse:
        """Suggest refactoring improvements using AI."""
        return await self._execute_ai_request(
            AICapability.REFACTORING_SUGGESTIONS,
            code,
            "",
            {"issues": issues or []}
        )
    
    async def analyze_security(self, code: str, language: str = "python") -> AIResponse:
        """Analyze code for security issues using AI."""
        return await self._execute_ai_request(
            AICapability.SECURITY_ANALYSIS,
            code,
            "",
            {"language": language}
        )
    
    async def optimize_performance(self, code: str, performance_metrics: Dict[str, Any] = None) -> AIResponse:
        """Suggest performance optimizations using AI."""
        return await self._execute_ai_request(
            AICapability.PERFORMANCE_OPTIMIZATION,
            code,
            "",
            {"performance_metrics": performance_metrics or {}}
        )
    
    async def generate_tests(self, code: str, test_framework: str = "pytest") -> AIResponse:
        """Generate tests using AI."""
        return await self._execute_ai_request(
            AICapability.TEST_GENERATION,
            code,
            "",
            {"test_framework": test_framework}
        )
    
    async def _execute_ai_request(self, capability: AICapability, prompt: str,
                                 context: str = "", metadata: Dict[str, Any] = None) -> AIResponse:
        """Execute an AI request with caching and error handling."""
        import time
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(capability, prompt, context, metadata)
            if self.config.enable_caching and cache_key in self._cache:
                self._performance_metrics['cache_hits'] += 1
                cached_response = self._cache[cache_key]
                cached_response.metadata['from_cache'] = True
                return cached_response
            
            # Get provider
            provider = self._providers.get(capability)
            if not provider:
                return AIResponse(
                    capability=capability,
                    success=False,
                    content=None,
                    error=f"No provider available for {capability.value}"
                )
            
            # Execute request
            if hasattr(provider, 'generate_code'):
                # Serena-style provider
                content = provider.generate_code(prompt, context)
            elif hasattr(provider, 'generate'):
                # Generic provider
                content = provider.generate(prompt, context)
            else:
                # Fallback
                content = f"# AI response for {capability.value}: {prompt[:50]}..."
            
            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(capability, content, metadata)
            
            # Create response
            response = AIResponse(
                capability=capability,
                success=True,
                content=content,
                confidence=confidence,
                metadata=metadata or {},
                execution_time=time.time() - start_time
            )
            
            # Cache response
            if self.config.enable_caching:
                self._cache[cache_key] = response
            
            # Update metrics
            self._performance_metrics['total_requests'] += 1
            self._performance_metrics['successful_requests'] += 1
            self._update_average_response_time(response.execution_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in AI request for {capability.value}: {e}")
            
            # Update metrics
            self._performance_metrics['total_requests'] += 1
            self._performance_metrics['failed_requests'] += 1
            
            return AIResponse(
                capability=capability,
                success=False,
                content=None,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _generate_cache_key(self, capability: AICapability, prompt: str,
                           context: str, metadata: Dict[str, Any] = None) -> str:
        """Generate a cache key for the request."""
        import hashlib
        
        key_data = f"{capability.value}:{prompt}:{context}:{str(metadata or {})}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _calculate_confidence(self, capability: AICapability, content: Any,
                             metadata: Dict[str, Any] = None) -> float:
        """Calculate confidence score for the AI response."""
        try:
            # Basic confidence calculation based on content length and type
            if not content:
                return 0.0
            
            base_confidence = 0.5
            
            # Adjust based on capability
            if capability == AICapability.CODE_GENERATION:
                if isinstance(content, str) and len(content) > 50:
                    base_confidence += 0.3
                if "def " in content or "class " in content:
                    base_confidence += 0.2
            elif capability == AICapability.ERROR_ANALYSIS:
                if isinstance(content, str) and len(content) > 100:
                    base_confidence += 0.3
                if any(word in content.lower() for word in ["error", "issue", "problem", "fix"]):
                    base_confidence += 0.2
            
            # Adjust based on provider type
            if hasattr(self._providers.get(capability), 'generate_code'):
                base_confidence += 0.1  # Serena provider bonus
            
            return min(base_confidence, 1.0)
            
        except Exception:
            return 0.5  # Default confidence
    
    def _update_average_response_time(self, response_time: float):
        """Update average response time metric."""
        current_avg = self._performance_metrics['average_response_time']
        total_requests = self._performance_metrics['total_requests']
        
        if total_requests == 1:
            self._performance_metrics['average_response_time'] = response_time
        else:
            self._performance_metrics['average_response_time'] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
    
    async def batch_process(self, requests: List[Dict[str, Any]]) -> List[AIResponse]:
        """Process multiple AI requests in batch."""
        try:
            tasks = []
            
            for request in requests:
                capability = AICapability(request['capability'])
                prompt = request['prompt']
                context = request.get('context', '')
                metadata = request.get('metadata', {})
                
                task = self._execute_ai_request(capability, prompt, context, metadata)
                tasks.append(task)
            
            # Execute all requests concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    processed_responses.append(AIResponse(
                        capability=AICapability(requests[i]['capability']),
                        success=False,
                        content=None,
                        error=str(response)
                    ))
                else:
                    processed_responses.append(response)
            
            return processed_responses
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get AI integration performance metrics."""
        return {
            **self._performance_metrics,
            'cache_size': len(self._cache),
            'available_capabilities': [cap.value for cap in self.config.enabled_capabilities],
            'active_providers': list(self._providers.keys()),
            'success_rate': (
                self._performance_metrics['successful_requests'] / 
                max(self._performance_metrics['total_requests'], 1)
            ) * 100
        }
    
    def clear_cache(self):
        """Clear the AI response cache."""
        self._cache.clear()
        logger.info("AI response cache cleared")
    
    def get_capability_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of each AI capability."""
        status = {}
        
        for capability in AICapability:
            provider = self._providers.get(capability)
            status[capability.value] = {
                'enabled': capability in self.config.enabled_capabilities,
                'provider_available': provider is not None,
                'provider_type': type(provider).__name__ if provider else None,
                'is_fallback': (
                    provider and 
                    type(provider).__name__ == 'FallbackProvider'
                ) if provider else False
            }
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the AI integration."""
        health_status = {
            'overall_health': 'healthy',
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check provider availability
            missing_providers = []
            for capability in self.config.enabled_capabilities:
                if capability not in self._providers:
                    missing_providers.append(capability.value)
            
            if missing_providers:
                health_status['issues'].append(f"Missing providers: {missing_providers}")
                health_status['recommendations'].append("Install missing AI dependencies")
                health_status['overall_health'] = 'degraded'
            
            # Check performance metrics
            success_rate = (
                self._performance_metrics['successful_requests'] / 
                max(self._performance_metrics['total_requests'], 1)
            ) * 100
            
            if success_rate < 80:
                health_status['issues'].append(f"Low success rate: {success_rate:.1f}%")
                health_status['recommendations'].append("Check AI provider configurations")
                health_status['overall_health'] = 'degraded'
            
            # Check cache size
            if len(self._cache) > self.config.max_context_length:
                health_status['issues'].append("Cache size is large")
                health_status['recommendations'].append("Consider clearing cache or reducing TTL")
            
            # Test a simple request
            try:
                test_response = await self.generate_code("# Test comment", "")
                if not test_response.success:
                    health_status['issues'].append("Test request failed")
                    health_status['overall_health'] = 'critical'
            except Exception as e:
                health_status['issues'].append(f"Test request error: {e}")
                health_status['overall_health'] = 'critical'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in AI health check: {e}")
            return {
                'overall_health': 'critical',
                'error': str(e),
                'issues': [f"Health check failed: {e}"],
                'recommendations': ['Restart AI integration']
            }


# Factory function
def create_ai_integration(config: Optional[AIConfig] = None) -> ConsolidatedAIIntegration:
    """Create a consolidated AI integration instance."""
    return ConsolidatedAIIntegration(config)


# Convenience functions for common operations
async def generate_code_fix(error_message: str, code_context: str = "") -> str:
    """Quick function to generate a code fix."""
    ai = create_ai_integration()
    response = await ai.generate_code(
        f"Fix this error: {error_message}",
        code_context
    )
    return response.content if response.success else f"# Could not generate fix: {response.error}"


async def analyze_code_quality(code: str) -> Dict[str, Any]:
    """Quick function to analyze code quality."""
    ai = create_ai_integration()
    
    # Run multiple analyses
    tasks = [
        ai.analyze_security(code),
        ai.suggest_refactoring(code),
        ai.optimize_performance(code)
    ]
    
    results = await asyncio.gather(*tasks)
    
    return {
        'security_analysis': results[0].content if results[0].success else None,
        'refactoring_suggestions': results[1].content if results[1].success else None,
        'performance_optimization': results[2].content if results[2].success else None,
        'overall_score': sum(r.confidence for r in results if r.success) / len(results)
    }
