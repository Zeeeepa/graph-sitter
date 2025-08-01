# Consolidated LSP Error Retrieval System Guide

## Overview

The Consolidated LSP Error Retrieval System is a comprehensive, unified architecture that provides professional-grade code analysis, error detection, and intelligent code generation capabilities. This system consolidates multiple previously fragmented components into a cohesive, easy-to-use interface.

## Architecture

### Core Components

#### 1. Unified Analysis Engine (`unified_analysis.py`)
- **Purpose**: Consolidates all codebase analysis functionality
- **Capabilities**: 
  - BASIC: File counts, basic metrics
  - COMPREHENSIVE: Detailed metrics, architectural insights
  - DEEP: Security analysis, performance analysis, complexity metrics
- **Usage**: `engine.analyze(AnalysisLevel.COMPREHENSIVE)`

#### 2. Unified Diagnostic Engine (`unified_diagnostics.py`)
- **Purpose**: Consolidates error detection and LSP integration
- **Capabilities**:
  - Real-time error monitoring
  - LSP server integration
  - Transaction-aware diagnostics
  - Error context and suggestions
- **Usage**: `diagnostics = get_diagnostic_engine(codebase, enable_lsp=True)`

#### 3. Enhanced Codebase Integration (`enhanced_codebase_integration.py`)
- **Purpose**: Orchestrates all components into a unified system
- **Capabilities**:
  - Component lifecycle management
  - Real-time monitoring
  - Performance tracking
  - Health checks
- **Usage**: `integration = await create_enhanced_integration(codebase)`

#### 4. Consolidated AI Integration (`consolidated_ai_integration.py`)
- **Purpose**: Unified interface for all AI capabilities
- **Capabilities**:
  - Code generation
  - Error analysis
  - Documentation generation
  - Security analysis
- **Usage**: `ai = create_ai_integration(config)`

#### 5. LSP Code Generation Engine (`lsp_code_generation.py`)
- **Purpose**: Context-aware error resolution and code fixes
- **Capabilities**:
  - Pattern-based fix generation
  - AI-powered code fixes
  - Error analysis and suggestions
- **Usage**: `fixes = engine.generate_error_fixes(error_id)`

## Quick Start

### Basic Usage

```python
from graph_sitter.core.enhanced_codebase_integration import create_enhanced_integration
from graph_sitter.core.lsp_methods import LSPMethodsMixin

# Your codebase class should inherit from LSPMethodsMixin
class MyCodebase(LSPMethodsMixin):
    def __init__(self, repo_path):
        self.repo_path = repo_path

# Create codebase instance
codebase = MyCodebase("/path/to/your/repo")

# Get errors directly
errors = codebase.errors()
errors_by_file = codebase.errors_by_file("main.py")
errors_by_severity = codebase.errors_by_severity("ERROR")

# Get comprehensive analysis
basic_analysis = codebase.basic_analysis()
comprehensive_analysis = codebase.comprehensive_analysis()
deep_analysis = codebase.deep_analysis()

# Get error suggestions and fixes
error_suggestions = codebase.error_suggestions(error_id)
quick_fixes = codebase.get_quick_fixes(error_id)
```

### Advanced Usage with Enhanced Integration

```python
import asyncio
from graph_sitter.core.enhanced_codebase_integration import (
    create_enhanced_integration, IntegrationConfig
)

async def main():
    # Configure the integration
    config = IntegrationConfig(
        enable_lsp=True,
        enable_real_time_monitoring=True,
        enable_code_generation=True,
        enable_deep_analysis=True,
        analysis_level="COMPREHENSIVE"
    )
    
    # Create and initialize integration
    integration = await create_enhanced_integration(codebase, config)
    
    # Run comprehensive analysis
    results = await integration.run_comprehensive_analysis()
    print(f"Analysis completed: {results}")
    
    # Auto-fix errors
    fix_results = await integration.auto_fix_errors(max_fixes=5)
    print(f"Fixed {len(fix_results['fixed_errors'])} errors")
    
    # Health check
    health = await integration.health_check()
    print(f"System health: {health['overall_health']}")
    
    # Shutdown gracefully
    await integration.shutdown()

# Run the async function
asyncio.run(main())
```

## API Reference

### LSP Methods (Available on Codebase Objects)

#### Error Retrieval
- `errors()` - Get all errors
- `errors_by_file(file_path)` - Get errors for specific file
- `errors_by_severity(severity)` - Filter by severity ("ERROR", "WARNING", "INFO")
- `errors_by_type(error_type)` - Filter by type ("syntax", "semantic", "lint")
- `recent_errors(timestamp)` - Get recent errors since timestamp

#### Error Context and Analysis
- `full_error_context(error_id)` - Get complete error context
- `error_suggestions(error_id)` - Get fix suggestions
- `error_related_symbols(error_id)` - Get related symbols
- `error_impact_analysis(error_id)` - Get impact analysis

#### Error Statistics
- `error_summary()` - Get error statistics summary
- `error_trends()` - Get error trends over time
- `most_common_errors()` - Get most frequent errors
- `error_hotspots()` - Get files with most errors

#### Real-time Monitoring
- `watch_errors(callback)` - Set up real-time error monitoring
- `error_stream()` - Get stream of error updates
- `refresh_errors()` - Force refresh of error detection

#### Error Resolution
- `auto_fix_errors(error_ids)` - Auto-fix specific errors
- `get_quick_fixes(error_id)` - Get available quick fixes
- `apply_error_fix(error_id, fix)` - Apply specific fix

#### LSP Features
- `completions(file_path, position)` - Get code completions
- `hover_info(file_path, position)` - Get hover information
- `signature_help(file_path, position)` - Get signature help
- `definitions(file_path, position)` - Go to definition
- `references(file_path, position)` - Find references
- `document_symbols(file_path)` - Get document symbols
- `workspace_symbols(query)` - Search workspace symbols

#### Comprehensive Analysis
- `basic_analysis()` - Get basic codebase analysis
- `comprehensive_analysis(level)` - Get comprehensive analysis
- `deep_analysis()` - Get deep analysis with security/performance
- `architectural_insights()` - Get architectural insights
- `code_quality_metrics()` - Get code quality metrics
- `complexity_analysis()` - Get complexity analysis
- `dependency_analysis()` - Get dependency analysis
- `security_analysis()` - Get security analysis
- `performance_analysis()` - Get performance analysis

### Enhanced Integration API

#### Initialization
```python
from graph_sitter.core.enhanced_codebase_integration import (
    EnhancedCodebaseIntegration, IntegrationConfig
)

config = IntegrationConfig(
    enable_lsp=True,
    enable_real_time_monitoring=True,
    enable_code_generation=True,
    enable_deep_analysis=True,
    analysis_level="COMPREHENSIVE",
    cache_enabled=True,
    monitoring_interval=1.0
)

integration = EnhancedCodebaseIntegration(codebase, config)
await integration.initialize()
```

#### Core Methods
- `await initialize()` - Initialize the integration system
- `await run_comprehensive_analysis(level)` - Run comprehensive analysis
- `await auto_fix_errors(max_fixes)` - Auto-fix errors
- `await health_check()` - Perform health check
- `get_comprehensive_status()` - Get system status
- `register_callback(event_type, callback)` - Register event callbacks
- `await shutdown()` - Graceful shutdown

### AI Integration API

#### Initialization
```python
from graph_sitter.core.consolidated_ai_integration import (
    ConsolidatedAIIntegration, AIConfig, AICapability
)

config = AIConfig(
    enabled_capabilities=[
        AICapability.CODE_GENERATION,
        AICapability.ERROR_ANALYSIS,
        AICapability.DOCUMENTATION_GENERATION
    ],
    enable_caching=True,
    temperature=0.1
)

ai = ConsolidatedAIIntegration(config)
```

#### AI Methods
- `await generate_code(prompt, context, language)` - Generate code
- `await analyze_error(error_message, code_context)` - Analyze errors
- `await generate_completion(code_prefix, cursor_position)` - Code completion
- `await generate_documentation(code, doc_type)` - Generate docs
- `await suggest_refactoring(code, issues)` - Refactoring suggestions
- `await analyze_security(code, language)` - Security analysis
- `await optimize_performance(code, metrics)` - Performance optimization
- `await generate_tests(code, framework)` - Generate tests
- `await batch_process(requests)` - Batch processing

## Configuration

### Integration Configuration

```python
from graph_sitter.core.enhanced_codebase_integration import IntegrationConfig

config = IntegrationConfig(
    enable_lsp=True,                    # Enable LSP integration
    enable_real_time_monitoring=True,   # Enable real-time monitoring
    enable_code_generation=True,        # Enable code generation
    enable_deep_analysis=True,          # Enable deep analysis
    analysis_level="COMPREHENSIVE",     # Default analysis level
    cache_enabled=True,                 # Enable caching
    max_cache_size=1000,               # Maximum cache size
    monitoring_interval=1.0,           # Monitoring interval (seconds)
    auto_refresh_diagnostics=True,     # Auto-refresh diagnostics
    enable_performance_tracking=True   # Enable performance tracking
)
```

### AI Configuration

```python
from graph_sitter.core.consolidated_ai_integration import AIConfig, AICapability

config = AIConfig(
    enabled_capabilities=[              # Enabled AI capabilities
        AICapability.CODE_GENERATION,
        AICapability.ERROR_ANALYSIS,
        AICapability.DOCUMENTATION_GENERATION
    ],
    model_preferences={                 # Model preferences
        "code_generation": "gpt-4",
        "error_analysis": "gpt-3.5-turbo"
    },
    max_context_length=4000,           # Maximum context length
    temperature=0.1,                   # Generation temperature
    max_tokens=1000,                   # Maximum tokens
    enable_caching=True,               # Enable response caching
    cache_ttl=3600,                    # Cache TTL (seconds)
    enable_streaming=False,            # Enable streaming responses
    fallback_enabled=True              # Enable fallback providers
)
```

## Error Handling

The system provides comprehensive error handling and graceful degradation:

### Component Failures
- If LSP servers are unavailable, the system falls back to static analysis
- If AI providers are unavailable, pattern-based fixes are used
- Component failures are logged and reported in health checks

### Error Recovery
```python
# Check system health
health = await integration.health_check()
if health['overall_health'] != 'healthy':
    print(f"Issues: {health['issues']}")
    print(f"Recommendations: {health['recommendations']}")

# Handle specific component failures
status = integration.get_comprehensive_status()
failed_components = [
    name for name, loaded in status['integration_status']['components_loaded'].items()
    if not loaded
]
if failed_components:
    print(f"Failed components: {failed_components}")
```

## Performance Optimization

### Caching
- Analysis results are cached to improve performance
- AI responses are cached to reduce API calls
- Cache can be configured or disabled as needed

### Monitoring
```python
# Get performance metrics
metrics = integration.status.performance_metrics
print(f"Memory usage: {metrics.get('memory_usage', {})}")
print(f"Cache efficiency: {metrics.get('cache_efficiency', 0)}%")

# AI performance metrics
ai_metrics = ai.get_performance_metrics()
print(f"AI success rate: {ai_metrics['success_rate']}%")
print(f"Average response time: {ai_metrics['average_response_time']}s")
```

### Optimization Tips
1. **Use appropriate analysis levels**: BASIC for quick checks, DEEP for thorough analysis
2. **Enable caching**: Significantly improves repeated operations
3. **Configure monitoring intervals**: Balance between real-time updates and performance
4. **Batch AI requests**: Use `batch_process()` for multiple AI operations

## Troubleshooting

### Common Issues

#### 1. Import Errors
```python
# Check if components are available
try:
    from graph_sitter.core.unified_analysis import UnifiedAnalysisEngine
    print("Unified analysis available")
except ImportError as e:
    print(f"Unified analysis not available: {e}")
```

#### 2. LSP Server Issues
```python
# Check LSP server status
diagnostics = get_diagnostic_engine(codebase, enable_lsp=True)
if not diagnostics._lsp_servers:
    print("No LSP servers available")
else:
    print(f"Available LSP servers: {list(diagnostics._lsp_servers.keys())}")
```

#### 3. AI Provider Issues
```python
# Check AI provider status
ai = ConsolidatedAIIntegration()
status = ai.get_capability_status()
for capability, info in status.items():
    if not info['provider_available']:
        print(f"No provider for {capability}")
    elif info['is_fallback']:
        print(f"Using fallback provider for {capability}")
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for specific components
logger = logging.getLogger('graph_sitter.core.unified_diagnostics')
logger.setLevel(logging.DEBUG)
```

## Testing

### Running Integration Tests
```bash
# Run all integration tests
pytest tests/integration/test_consolidated_system.py -v

# Run specific test class
pytest tests/integration/test_consolidated_system.py::TestUnifiedAnalysisEngine -v

# Run with coverage
pytest tests/integration/test_consolidated_system.py --cov=graph_sitter.core
```

### Custom Testing
```python
import pytest
from graph_sitter.core.enhanced_codebase_integration import create_enhanced_integration

@pytest.mark.asyncio
async def test_my_integration():
    # Create test codebase
    codebase = MyCodebase("/path/to/test/repo")
    
    # Test integration
    integration = await create_enhanced_integration(codebase)
    
    # Run tests
    results = await integration.run_comprehensive_analysis()
    assert 'analysis' in results
    
    # Cleanup
    await integration.shutdown()
```

## Migration Guide

### From Legacy Components

If you're migrating from the old fragmented system:

#### 1. Replace Direct Component Usage
```python
# Old way
from graph_sitter.analysis.deep_analysis import DeepCodebaseAnalyzer
from graph_sitter.core.diagnostics import CodebaseDiagnostics

analyzer = DeepCodebaseAnalyzer(codebase)
diagnostics = CodebaseDiagnostics(codebase)

# New way
from graph_sitter.core.lsp_methods import LSPMethodsMixin

class MyCodebase(LSPMethodsMixin):
    # Your codebase implementation
    pass

codebase = MyCodebase(repo_path)
analysis = codebase.comprehensive_analysis()
errors = codebase.errors()
```

#### 2. Update Error Handling
```python
# Old way
try:
    analyzer = DeepCodebaseAnalyzer(codebase)
    results = analyzer.analyze()
except ImportError:
    # Fallback to basic analysis
    pass

# New way - automatic fallback handling
analysis = codebase.comprehensive_analysis()  # Handles fallbacks automatically
```

#### 3. Migrate to Async Patterns
```python
# Old synchronous code
results = analyzer.analyze()
fixes = code_gen.generate_fixes(error_id)

# New async code
async def analyze_and_fix():
    integration = await create_enhanced_integration(codebase)
    results = await integration.run_comprehensive_analysis()
    fixes = await integration.auto_fix_errors()
    await integration.shutdown()
    return results, fixes
```

## Best Practices

### 1. Resource Management
```python
# Always use async context managers or explicit shutdown
async def analyze_codebase():
    integration = await create_enhanced_integration(codebase)
    try:
        results = await integration.run_comprehensive_analysis()
        return results
    finally:
        await integration.shutdown()
```

### 2. Error Handling
```python
# Handle component failures gracefully
try:
    errors = codebase.errors()
except Exception as e:
    logger.warning(f"Error retrieval failed: {e}")
    errors = []  # Fallback to empty list
```

### 3. Performance Monitoring
```python
# Monitor system performance
integration = await create_enhanced_integration(codebase)

# Register performance callback
def performance_callback(errors, warnings):
    if len(errors) > 100:
        logger.warning(f"High error count: {len(errors)}")

integration.register_callback('error_change', performance_callback)
```

### 4. Configuration Management
```python
# Use environment-specific configurations
import os

config = IntegrationConfig(
    enable_lsp=os.getenv('ENABLE_LSP', 'true').lower() == 'true',
    analysis_level=os.getenv('ANALYSIS_LEVEL', 'COMPREHENSIVE'),
    monitoring_interval=float(os.getenv('MONITORING_INTERVAL', '1.0'))
)
```

## Contributing

### Adding New Analysis Capabilities
1. Extend `UnifiedAnalysisEngine` with new analysis methods
2. Add corresponding methods to `LSPMethodsMixin`
3. Update tests and documentation

### Adding New AI Capabilities
1. Add new capability to `AICapability` enum
2. Implement provider in `ConsolidatedAIIntegration`
3. Add corresponding public methods
4. Update tests and documentation

### Adding New LSP Features
1. Extend `EnhancedDiagnostic` with new fields if needed
2. Update `UnifiedDiagnosticEngine` with new methods
3. Add methods to `LSPMethodsMixin`
4. Update tests and documentation

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section above
2. Review the integration tests for examples
3. Check the health status of your integration
4. Enable debug logging for detailed information

The consolidated system is designed to be robust, performant, and easy to use while providing comprehensive LSP error retrieval capabilities.
