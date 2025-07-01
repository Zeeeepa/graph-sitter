#!/usr/bin/env python3
"""
Basic Integration Example - Codegen SDK + Autogenlib

This example demonstrates the basic usage of the integrated Codegen SDK + Autogenlib system
for code generation with context enhancement.
"""

import asyncio
import os
from typing import Dict, Any

# Import the integrated system (this would be the actual import path)
# from contexten.extensions.codegen import CodegenAutogenIntegration, CodegenAutogenConfig

# Mock implementation for demonstration
class CodegenAutogenIntegration:
    """Mock implementation for demonstration purposes"""
    
    def __init__(self, config):
        self.config = config
        self._initialized = False
    
    async def initialize(self):
        """Initialize the integration"""
        print("🚀 Initializing Codegen SDK + Autogenlib integration...")
        print(f"   - Org ID: {self.config.org_id}")
        print(f"   - Base URL: {self.config.base_url}")
        print(f"   - Caching: {'Enabled' if self.config.enable_caching else 'Disabled'}")
        self._initialized = True
        print("✅ Integration initialized successfully!")
    
    async def generate_with_context(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate code with context enhancement"""
        if not self._initialized:
            await self.initialize()
        
        print(f"\n🔄 Generating code for: '{prompt}'")
        
        # Simulate context enhancement
        if kwargs.get('codebase_context'):
            print("📊 Enhancing with codebase context...")
        
        # Simulate generation
        await asyncio.sleep(0.5)  # Simulate processing time
        
        return {
            "generated_code": f"# Generated code for: {prompt}\ndef example_function():\n    pass",
            "context_used": bool(kwargs.get('codebase_context')),
            "generation_time": 0.5,
            "method": "autogenlib" if not kwargs.get('use_codegen_agent') else "codegen_sdk"
        }

class CodegenAutogenConfig:
    """Configuration class for the integration"""
    
    def __init__(self, org_id: str, token: str, **kwargs):
        self.org_id = org_id
        self.token = token
        self.base_url = kwargs.get('base_url', 'https://api.codegen.com')
        self.enable_caching = kwargs.get('enable_caching', True)
        self.cache_ttl = kwargs.get('cache_ttl', 3600)
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables"""
        return cls(
            org_id=os.getenv('CODEGEN_ORG_ID', 'demo_org_id'),
            token=os.getenv('CODEGEN_API_TOKEN', 'demo_token'),
            enable_caching=True,
            cache_ttl=3600
        )


async def basic_usage_example():
    """Demonstrate basic usage of the integration"""
    
    print("=" * 60)
    print("🔧 Basic Integration Usage Example")
    print("=" * 60)
    
    # 1. Initialize from environment variables (recommended)
    config = CodegenAutogenConfig.from_env()
    integration = CodegenAutogenIntegration(config)
    
    # 2. Initialize the integration
    await integration.initialize()
    
    # 3. Simple code generation
    print("\n📝 Example 1: Simple Code Generation")
    result = await integration.generate_with_context(
        prompt="Create a function to validate email addresses"
    )
    print(f"✅ Generated: {result['generated_code'][:50]}...")
    print(f"⏱️  Time: {result['generation_time']}s")
    print(f"🔧 Method: {result['method']}")
    
    # 4. Code generation with context
    print("\n📝 Example 2: Context-Enhanced Generation")
    result = await integration.generate_with_context(
        prompt="Add error handling to the login function",
        codebase_context={
            "target_file": "src/auth/login.py",
            "related_functions": ["validate_user", "create_session"],
            "error_patterns": ["try/except", "logging"]
        }
    )
    print(f"✅ Generated: {result['generated_code'][:50]}...")
    print(f"📊 Context used: {result['context_used']}")
    print(f"⏱️  Time: {result['generation_time']}s")
    
    # 5. Using Codegen SDK agent for complex tasks
    print("\n📝 Example 3: Complex Task with Codegen SDK Agent")
    result = await integration.generate_with_context(
        prompt="Refactor the entire authentication module to use async/await",
        use_codegen_agent=True,  # Use Codegen SDK for complex tasks
        codebase_context={
            "module": "auth",
            "files": ["login.py", "register.py", "session.py"],
            "requirements": ["async/await", "error handling", "logging"]
        }
    )
    print(f"✅ Generated: {result['generated_code'][:50]}...")
    print(f"🤖 Method: {result['method']}")
    print(f"⏱️  Time: {result['generation_time']}s")


async def configuration_examples():
    """Demonstrate different configuration options"""
    
    print("\n" + "=" * 60)
    print("⚙️  Configuration Examples")
    print("=" * 60)
    
    # 1. Environment-based configuration (recommended)
    print("\n🌍 Environment-based Configuration:")
    config_env = CodegenAutogenConfig.from_env()
    print(f"   - Org ID: {config_env.org_id}")
    print(f"   - Caching: {config_env.enable_caching}")
    print(f"   - Cache TTL: {config_env.cache_ttl}s")
    
    # 2. Direct configuration
    print("\n🔧 Direct Configuration:")
    config_direct = CodegenAutogenConfig(
        org_id="your_org_id",
        token="your_api_token",
        base_url="https://api.codegen.com",
        enable_caching=True,
        cache_ttl=7200  # 2 hours
    )
    print(f"   - Org ID: {config_direct.org_id}")
    print(f"   - Base URL: {config_direct.base_url}")
    print(f"   - Cache TTL: {config_direct.cache_ttl}s")
    
    # 3. Performance-optimized configuration
    print("\n🚀 Performance-Optimized Configuration:")
    config_perf = CodegenAutogenConfig(
        org_id="your_org_id",
        token="your_api_token",
        enable_caching=True,
        cache_ttl=3600,
        # Additional performance settings would go here
    )
    print(f"   - Caching: {config_perf.enable_caching}")
    print(f"   - Optimized for: <2s response time")


async def error_handling_example():
    """Demonstrate error handling capabilities"""
    
    print("\n" + "=" * 60)
    print("🛡️  Error Handling Examples")
    print("=" * 60)
    
    config = CodegenAutogenConfig.from_env()
    integration = CodegenAutogenIntegration(config)
    
    # Simulate various error scenarios
    print("\n🔄 Testing error handling scenarios...")
    
    try:
        # This would normally handle rate limits, network errors, etc.
        result = await integration.generate_with_context(
            prompt="Generate a complex microservice architecture"
        )
        print("✅ Request completed successfully")
        
    except Exception as e:
        print(f"❌ Error handled gracefully: {e}")
        print("🔄 Fallback mechanisms would be triggered")
    
    print("\n🛡️  Error handling features:")
    print("   - Exponential backoff for rate limits")
    print("   - Circuit breaker for API failures")
    print("   - Automatic fallback: autogenlib → Codegen SDK")
    print("   - Graceful degradation for context enhancement")


async def performance_monitoring_example():
    """Demonstrate performance monitoring capabilities"""
    
    print("\n" + "=" * 60)
    print("📊 Performance Monitoring Examples")
    print("=" * 60)
    
    config = CodegenAutogenConfig.from_env()
    integration = CodegenAutogenIntegration(config)
    await integration.initialize()
    
    # Simulate multiple requests to show performance metrics
    print("\n🔄 Running performance test...")
    
    start_time = asyncio.get_event_loop().time()
    
    for i in range(3):
        result = await integration.generate_with_context(
            prompt=f"Create function #{i+1}",
            codebase_context={"test": True}
        )
        print(f"   Request {i+1}: {result['generation_time']}s")
    
    total_time = asyncio.get_event_loop().time() - start_time
    
    print(f"\n📊 Performance Summary:")
    print(f"   - Total time: {total_time:.2f}s")
    print(f"   - Average per request: {total_time/3:.2f}s")
    print(f"   - Target: <2s per request ✅")
    
    # Mock cache statistics
    print(f"\n💾 Cache Statistics:")
    print(f"   - Hit rate: 85% ✅")
    print(f"   - Memory usage: 245MB")
    print(f"   - Cache entries: 1,247")


async def main():
    """Main example runner"""
    
    print("🎯 Codegen SDK + Autogenlib Integration Examples")
    print("=" * 60)
    
    # Set up demo environment variables
    os.environ.setdefault('CODEGEN_ORG_ID', 'demo_org_123')
    os.environ.setdefault('CODEGEN_API_TOKEN', 'demo_token_456')
    
    try:
        # Run all examples
        await basic_usage_example()
        await configuration_examples()
        await error_handling_example()
        await performance_monitoring_example()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("🚀 Ready to implement the integration!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("🔧 Check configuration and try again")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())

