# OpenEvolve Integration for Graph-sitter

A comprehensive integration that enhances Graph-sitter with OpenEvolve's evolutionary coding capabilities, continuous learning mechanics, and comprehensive step context tracking.

## Overview

This extension combines the power of Graph-sitter's code analysis and manipulation framework with OpenEvolve's evolutionary optimization approach, creating an intelligent system that learns from every evolution step and continuously improves its strategies.

### Key Features

- **Enhanced Code Evolution**: Leverage OpenEvolve's evolutionary algorithms with Graph-sitter's deep code understanding
- **Continuous Learning**: Learn from every evolution step to improve future outcomes
- **Comprehensive Context Tracking**: Track decision trees, performance metrics, and execution patterns
- **Performance Monitoring**: Real-time monitoring with bottleneck detection and optimization recommendations
- **Pattern Recognition**: Identify successful strategies and adapt algorithms based on historical data
- **Database Integration**: Comprehensive storage of evolution history, learning data, and analytics

## Architecture

The integration consists of several key components:

```
┌─────────────────────────────────────────────────────────────┐
│                OpenEvolve Integration                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Integration   │  │ Continuous      │  │   Context    │ │
│  │   Controller    │  │ Learning        │  │   Tracker    │ │
│  │                 │  │ System          │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Database      │  │ Performance     │  │ Configuration│ │
│  │   Manager       │  │ Monitor         │  │ Management   │ │
│  │                 │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Graph-sitter Core                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Code Analysis │  │ Symbol Tracking │  │ Dependency   │ │
│  │                 │  │                 │  │ Analysis     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Installation

The OpenEvolve integration is included as part of the Graph-sitter extensions. Ensure you have the required dependencies:

```bash
pip install graph-sitter[openevolve]
# or
pip install aiosqlite numpy scikit-learn pyyaml
```

## Quick Start

### Basic Usage

```python
import asyncio
from pathlib import Path
from graph_sitter.codebase import Codebase
from graph_sitter.extensions.openevolve import OpenEvolveIntegration, OpenEvolveConfig

async def evolve_code():
    # Initialize codebase and configuration
    codebase = Codebase(Path("./my_project"))
    config = OpenEvolveConfig()
    
    # Create integration
    integration = OpenEvolveIntegration(codebase, config)
    
    # Start evolution session
    session_id = await integration.start_evolution_session(
        target_files=["src/main.py"],
        objectives={
            "improve_performance": 0.8,
            "reduce_complexity": 0.7,
            "maintain_functionality": 1.0
        },
        max_iterations=50
    )
    
    # Evolve code
    result = await integration.evolve_code(
        file_path="src/main.py",
        evolution_prompt="Optimize for better performance while maintaining readability",
        context={"focus_areas": ["performance", "readability"]}
    )
    
    # Get insights and end session
    insights = await integration.get_evolution_insights()
    final_report = await integration.end_evolution_session()
    
    return result, insights, final_report

# Run the evolution
asyncio.run(evolve_code())
```

### Configuration

Create a configuration file for customized behavior:

```python
from graph_sitter.extensions.openevolve import OpenEvolveConfig

# Create and customize configuration
config = OpenEvolveConfig()

# Learning settings
config.learning.min_pattern_frequency = 3
config.learning.pattern_confidence_threshold = 0.7
config.learning.learning_rate = 0.1

# Performance monitoring
config.performance.enable_monitoring = True
config.performance.execution_time_threshold = 30.0

# Evolution parameters
config.evolution.max_iterations = 100
config.evolution.population_size = 50

# Database settings
config.database.database_path = "./my_evolution.db"
config.database.max_session_age_days = 30

# Save configuration
config.save_to_file("openevolve_config.yaml")
```

## Core Components

### 1. Integration Controller (`OpenEvolveIntegration`)

The main interface for the integration, orchestrating all components:

```python
integration = OpenEvolveIntegration(codebase, config, database_path)

# Session management
session_id = await integration.start_evolution_session(...)
result = await integration.evolve_code(...)
insights = await integration.get_evolution_insights()
await integration.end_evolution_session()
```

### 2. Continuous Learning System

Learns from every evolution step to improve future outcomes:

```python
# The learning system automatically:
# - Recognizes patterns in successful evolutions
# - Adapts algorithms based on historical performance
# - Provides enhanced context for new evolutions
# - Optimizes strategy weights based on results

# Access learning insights
insights = await integration.get_evolution_insights()
patterns = insights["learning_insights"]["patterns"]
confidence = insights["learning_confidence"]
```

### 3. Context Tracker

Comprehensive tracking of execution steps and decision trees:

```python
# Automatic context tracking includes:
# - Step-by-step execution logging
# - Decision tree construction
# - Performance metrics collection
# - Error pattern analysis

# Access context patterns
patterns = await integration.context_tracker.analyze_patterns(session_id)
decision_tree = integration.context_tracker.decision_trees[session_id]
```

### 4. Performance Monitor

Real-time performance monitoring with analytics:

```python
# Performance monitoring provides:
# - Real-time metric collection
# - Bottleneck identification
# - Trend analysis
# - Optimization recommendations

analytics = await integration.performance_monitor.get_session_analytics(session_id)
report = await integration.performance_monitor.generate_performance_report()
```

### 5. Database Manager

Comprehensive data storage and retrieval:

```python
# Database stores:
# - Evolution sessions and steps
# - Decision trees and context data
# - Performance metrics and analytics
# - Learning data and patterns

# Access stored data
history = await integration.database.get_file_evolution_history("src/main.py")
session_data = await integration.database.get_session_data(session_id)
```

## Advanced Features

### Continuous Learning

The system learns from every evolution step:

```python
# Enable advanced learning features
config.learning.min_training_samples = 50
config.learning.max_training_samples = 5000
config.learning.retrain_interval_hours = 1

# The system will:
# - Train predictive models on historical data
# - Recognize successful patterns
# - Adapt strategy weights based on performance
# - Provide intelligent suggestions for new evolutions
```

### Pattern Recognition

Identify and leverage successful evolution patterns:

```python
# Pattern recognition analyzes:
# - Common characteristics of successful evolutions
# - Prompt patterns that lead to good results
# - Code complexity patterns that work well
# - Context patterns that predict success

# Access recognized patterns
pattern_analysis = await integration.learning_system.pattern_recognizer.analyze_evolution_patterns(history)
successful_patterns = pattern_analysis["patterns"]
```

### Performance Optimization

Automatic performance monitoring and optimization:

```python
# Enable comprehensive monitoring
config.performance.enable_monitoring = True
config.performance.bottleneck_detection_enabled = True
config.performance.auto_optimization_enabled = True

# Get optimization recommendations
optimization = await integration.optimize_evolution_strategy()
suggested_config = optimization["suggested_config"]
```

### Custom Metrics

Define custom metrics for your specific use case:

```python
# Record custom metrics during evolution
await integration.context_tracker.record_metrics(step_id, {
    "custom_complexity_score": 0.75,
    "domain_specific_metric": 0.82,
    "business_value_score": 0.90
})

# Custom metrics are automatically included in:
# - Performance analytics
# - Learning algorithms
# - Pattern recognition
# - Optimization recommendations
```

## Configuration Reference

### Learning Configuration

```yaml
learning:
  min_pattern_frequency: 3          # Minimum frequency for pattern recognition
  pattern_confidence_threshold: 0.7  # Confidence threshold for patterns
  learning_rate: 0.1                # Learning rate for adaptive algorithms
  adaptation_window: 50             # Window size for adaptation
  min_training_samples: 10          # Minimum samples for model training
  retrain_interval_hours: 1         # How often to retrain models
  max_training_samples: 1000        # Maximum samples for training
```

### Database Configuration

```yaml
database:
  database_path: "openevolve.db"    # Database file path
  connection_pool_size: 5           # Connection pool size
  max_session_age_days: 30          # Data retention period
  cleanup_interval_hours: 24        # Cleanup frequency
  enable_backup: true               # Enable automatic backups
```

### Performance Configuration

```yaml
performance:
  enable_monitoring: true           # Enable performance monitoring
  execution_time_threshold: 30.0    # Threshold for slow operations
  error_rate_threshold: 0.1         # Threshold for high error rates
  bottleneck_detection_enabled: true # Enable bottleneck detection
  generate_reports: true            # Generate performance reports
```

### Evolution Configuration

```yaml
evolution:
  max_iterations: 100               # Maximum evolution iterations
  population_size: 50               # Population size for evolution
  elite_ratio: 0.2                  # Ratio of elite individuals
  mutation_rate: 0.1                # Mutation rate
  evaluation_timeout: 60.0          # Timeout for evaluations
```

## Examples

### Example 1: Basic Code Evolution

```python
async def basic_evolution():
    codebase = Codebase(Path("./project"))
    integration = OpenEvolveIntegration(codebase)
    
    session_id = await integration.start_evolution_session(
        target_files=["calculator.py"],
        objectives={"performance": 0.8, "readability": 0.7}
    )
    
    result = await integration.evolve_code(
        file_path="calculator.py",
        evolution_prompt="Optimize mathematical operations"
    )
    
    await integration.end_evolution_session()
    return result
```

### Example 2: Continuous Learning Across Sessions

```python
async def learning_example():
    integration = OpenEvolveIntegration(codebase, config)
    
    # Run multiple sessions to build learning data
    for i in range(5):
        session_id = await integration.start_evolution_session(
            target_files=[f"module_{i}.py"],
            objectives={"quality": 0.8}
        )
        
        await integration.evolve_code(
            file_path=f"module_{i}.py",
            evolution_prompt="Improve code quality"
        )
        
        # System learns from each session
        insights = await integration.get_evolution_insights()
        confidence = insights["learning_confidence"]
        
        await integration.end_evolution_session()
        print(f"Session {i+1} - Learning confidence: {confidence:.2f}")
```

### Example 3: Performance Monitoring

```python
async def monitoring_example():
    config = OpenEvolveConfig()
    config.performance.enable_monitoring = True
    config.performance.generate_reports = True
    
    integration = OpenEvolveIntegration(codebase, config)
    
    session_id = await integration.start_evolution_session(
        target_files=["large_module.py"],
        objectives={"performance": 1.0}
    )
    
    # Monitor performance during evolution
    for i in range(10):
        await integration.evolve_code(
            file_path="large_module.py",
            evolution_prompt=f"Optimization step {i+1}"
        )
        
        # Get real-time analytics
        analytics = await integration.performance_monitor.get_session_analytics(session_id)
        print(f"Step {i+1} - Avg time: {analytics['real_time_metrics']['avg_execution_time']:.2f}s")
    
    # Generate final performance report
    report = await integration.performance_monitor.generate_performance_report(session_id)
    await integration.end_evolution_session()
    
    return report
```

## Best Practices

### 1. Configuration Management

- Use configuration files for consistent settings across environments
- Validate configuration before starting evolution sessions
- Optimize configuration based on your specific use case

### 2. Session Management

- Always end evolution sessions to ensure proper cleanup
- Use meaningful session objectives that align with your goals
- Monitor session performance and adjust parameters as needed

### 3. Learning Optimization

- Provide sufficient training data for effective learning
- Use consistent evolution prompts to help pattern recognition
- Monitor learning confidence and adjust thresholds accordingly

### 4. Performance Monitoring

- Enable monitoring for production use
- Set appropriate thresholds for your environment
- Review performance reports regularly for optimization opportunities

### 5. Database Management

- Configure appropriate data retention policies
- Enable backups for important evolution data
- Monitor database size and performance

## Troubleshooting

### Common Issues

1. **Low Learning Confidence**
   - Increase training data by running more evolution sessions
   - Adjust pattern recognition thresholds
   - Ensure consistent evolution contexts

2. **Performance Bottlenecks**
   - Enable performance monitoring to identify issues
   - Adjust execution time thresholds
   - Consider parallel processing for large codebases

3. **Database Issues**
   - Check database permissions and disk space
   - Verify database schema initialization
   - Monitor connection pool usage

4. **Configuration Errors**
   - Validate configuration using `config.validate()`
   - Check file paths and permissions
   - Review log files for detailed error messages

### Debug Mode

Enable debug mode for detailed logging:

```python
config = OpenEvolveConfig()
config.debug_mode = True
config.log_level = "DEBUG"
```

### Logging

Configure logging for better visibility:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## API Reference

For detailed API documentation, see the individual module documentation:

- [`OpenEvolveIntegration`](./integration.py) - Main integration interface
- [`ContinuousLearningSystem`](./continuous_learning.py) - Learning and adaptation
- [`ContextTracker`](./context_tracker.py) - Context and decision tracking
- [`PerformanceMonitor`](./performance_monitor.py) - Performance monitoring
- [`OpenEvolveDatabase`](./database_manager.py) - Data storage and retrieval
- [`OpenEvolveConfig`](./config.py) - Configuration management

## Contributing

Contributions are welcome! Please see the main Graph-sitter contributing guidelines and ensure:

- All new features include comprehensive tests
- Documentation is updated for new functionality
- Performance impact is considered and measured
- Learning algorithms are validated with appropriate datasets

## License

This extension is part of Graph-sitter and follows the same license terms.

