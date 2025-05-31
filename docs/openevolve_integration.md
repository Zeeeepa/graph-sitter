# OpenEvolve Integration & Evaluation System

## Overview

The OpenEvolve Integration & Evaluation System is a comprehensive framework that integrates the OpenEvolve framework with the graph-sitter codebase to provide effectiveness analysis and performance evaluation for three key components:

- **evaluator.py** - Component effectiveness tracking
- **database.py** - Database overlay implementation  
- **controller.py** - Step-by-step evaluation and analysis

## Architecture

### Core Components

1. **OpenEvolve Integration Layer** (`src/codegen/integration/openevolve/`)
   - `integration_layer.py` - Main integration orchestrator
   - `agent_adapters.py` - Adapters for OpenEvolve agents
   - `config.py` - Configuration management

2. **Database Overlay System** (`src/codegen/integration/database/`)
   - `overlay.py` - Database abstraction layer
   - `models.py` - Data models for evaluation tracking
   - `evaluations_schema.sql` - Database schema

3. **Effectiveness Evaluation Engine** (`src/codegen/integration/evaluation/`)
   - `engine.py` - Core evaluation engine
   - `metrics.py` - Effectiveness and performance metrics
   - `correlations.py` - Outcome correlation analysis

4. **Performance Analysis Tools** (`src/codegen/integration/analysis/`)
   - `performance.py` - Performance analyzer
   - `optimization.py` - Optimization recommender
   - `reporting.py` - Comprehensive reporting

## Key Features

### 🎯 Component Effectiveness Evaluation
- Real-time effectiveness scoring (0.0 to 1.0)
- Multi-dimensional analysis (functionality, reliability, performance, usability, maintainability)
- Step-by-step evaluation tracking
- Historical trend analysis

### 📊 Performance Analysis
- Execution time monitoring
- Memory usage tracking
- Success rate analysis
- Bottleneck identification
- Comparative analysis across components

### 🔗 Outcome Correlation Analysis
- Statistical correlation between effectiveness and outcomes
- Confidence level calculation
- Impact assessment
- Trend detection

### 💡 Optimization Recommendations
- Automated bottleneck detection
- Priority-based recommendations
- Implementation guidance
- Success metrics definition

### 📈 Comprehensive Reporting
- JSON, Markdown, and HTML report formats
- Executive summaries
- Detailed findings
- Action plans with timelines

## Quick Start

### Installation

```bash
# Install dependencies
pip install aiosqlite

# The integration system is included in the graph-sitter package
```

### Basic Usage

```python
import asyncio
from codegen.integration import OpenEvolveIntegrator
from codegen.integration.openevolve.config import OpenEvolveConfig

async def evaluate_component():
    # Configure the integration
    config = OpenEvolveConfig(
        effectiveness_threshold=0.75,
        real_time_monitoring=True
    )
    
    # Initialize integrator
    async with OpenEvolveIntegrator(config) as integrator:
        # Evaluate a component
        result = await integrator.evaluate_component(
            component_type="evaluator",
            component_name="MyEvaluator",
            component_instance=my_evaluator_instance,
            evaluation_context={"test_data": [0.8, 0.9, 0.7]}
        )
        
        print(f"Effectiveness: {result.effectiveness_score:.3f}")
        print(f"Success: {result.success}")

# Run the evaluation
asyncio.run(evaluate_component())
```

### Batch Evaluation

```python
async def batch_evaluation():
    config = OpenEvolveConfig(max_concurrent_evaluations=5)
    
    async with OpenEvolveIntegrator(config) as integrator:
        components = {
            "evaluator": {"eval1": evaluator1, "eval2": evaluator2},
            "database": {"db1": database1},
            "controller": {"ctrl1": controller1}
        }
        
        results = await integrator.evaluate_all_components(components)
        
        for name, result in results.items():
            print(f"{name}: {result.effectiveness_score:.3f}")
```

## Configuration

### Environment Variables

```bash
# OpenEvolve Integration Settings
export OPENEVOLVE_EFFECTIVENESS_THRESHOLD=0.75
export OPENEVOLVE_SAMPLE_SIZE=100
export OPENEVOLVE_REAL_TIME=true
export OPENEVOLVE_DATABASE_URL=sqlite:///evaluations.db
export OPENEVOLVE_LOG_LEVEL=INFO

# Optional: OpenEvolve Repository Path
export OPENEVOLVE_REPO_PATH=/path/to/OpenAlpha_Evolve
export AUTOGENLIB_REPO_PATH=/path/to/autogenlib
```

### Configuration Object

```python
from codegen.integration.openevolve.config import OpenEvolveConfig

config = OpenEvolveConfig(
    # Evaluation settings
    effectiveness_threshold=0.75,
    performance_sample_size=100,
    correlation_analysis_window=1000,
    
    # Database settings
    database_url="sqlite:///openevolve_evaluations.db",
    
    # Analysis settings
    analysis_batch_size=50,
    real_time_monitoring=True,
    metric_aggregation_interval=300,  # seconds
    
    # Performance optimization
    enable_caching=True,
    cache_ttl_seconds=3600,
    max_concurrent_evaluations=10
)
```

## Performance Analysis

### Running Analysis

```python
from codegen.integration.database import DatabaseOverlay
from codegen.integration.analysis import PerformanceAnalyzer

async def analyze_performance(session_id):
    async with DatabaseOverlay() as db_overlay:
        analyzer = PerformanceAnalyzer(db_overlay, config)
        
        results = await analyzer.analyze_component_performance(
            session_id=session_id,
            component_type="evaluator",  # Optional filter
            time_window_hours=24  # Last 24 hours
        )
        
        print(f"Performance Score: {results['performance_score']:.3f}")
        print(f"Bottlenecks: {len(results['bottleneck_analysis'])}")
```

### Bottleneck Detection

The system automatically detects bottlenecks in:
- **Execution Time** - Components taking too long to execute
- **Memory Usage** - Components using excessive memory
- **Effectiveness** - Components with low effectiveness scores
- **Reliability** - Components with high error rates

### Optimization Recommendations

```python
from codegen.integration.analysis import OptimizationRecommender

async def get_recommendations(analysis_results):
    recommender = OptimizationRecommender()
    
    recommendations = await recommender.generate_recommendations(
        bottlenecks=analysis_results['bottleneck_analysis'],
        performance_data=analysis_results,
        optimization_opportunities=analysis_results['optimization_opportunities']
    )
    
    for rec in recommendations:
        print(f"Priority: {rec.priority}")
        print(f"Title: {rec.title}")
        print(f"Impact: {rec.expected_impact}")
        print(f"Effort: {rec.effort_level}")
```

## Reporting

### Generate Reports

```python
from codegen.integration.analysis import AnalysisReporter

async def generate_reports(session_id, analysis_results, recommendations):
    reporter = AnalysisReporter()
    
    # JSON Report
    json_report = await reporter.generate_comprehensive_report(
        session_id=session_id,
        analysis_results=analysis_results,
        recommendations=recommendations,
        format_type='json'
    )
    
    # Markdown Report
    markdown_report = await reporter.generate_comprehensive_report(
        session_id=session_id,
        analysis_results=analysis_results,
        recommendations=recommendations,
        format_type='markdown'
    )
    
    # HTML Report
    html_report = await reporter.generate_comprehensive_report(
        session_id=session_id,
        analysis_results=analysis_results,
        recommendations=recommendations,
        format_type='html'
    )
```

### Report Contents

Each report includes:
- **Executive Summary** - High-level performance overview
- **Component Analysis** - Detailed component effectiveness
- **Performance Trends** - Historical performance analysis
- **Bottleneck Analysis** - Identified performance issues
- **Optimization Recommendations** - Prioritized improvement suggestions
- **Action Plan** - Implementation timeline and resource requirements

## Database Schema

The system uses a comprehensive database schema to track:

### Core Tables
- `evaluation_sessions` - Evaluation session metadata
- `component_evaluations` - Component evaluation results
- `evaluation_steps` - Step-by-step evaluation tracking
- `outcome_correlations` - Outcome vs effectiveness correlation
- `performance_analyses` - Performance analysis results
- `agent_executions` - OpenEvolve agent execution tracking
- `evaluation_metrics` - Aggregated metrics

### Key Metrics Tracked
- Effectiveness scores (0.0 to 1.0)
- Execution time (milliseconds)
- Memory usage (MB)
- Success rates
- Error counts
- Correlation scores
- Trend analysis

## Integration with OpenEvolve

### Agent Adapters

The system includes adapters for OpenEvolve agents:

1. **EvaluatorAgentAdapter** - Integrates with OpenEvolve's EvaluatorAgent
2. **DatabaseAgentAdapter** - Integrates with OpenEvolve's InMemoryDatabaseAgent
3. **ControllerAgentAdapter** - Integrates with OpenEvolve's SelectionControllerAgent

### Mock Agents

When OpenEvolve is not available, the system uses mock agents for testing and development.

## Best Practices

### Component Evaluation
1. **Regular Evaluation** - Run evaluations regularly to track trends
2. **Meaningful Context** - Provide relevant evaluation context
3. **Baseline Metrics** - Establish baseline performance metrics
4. **Threshold Monitoring** - Set appropriate effectiveness thresholds

### Performance Optimization
1. **Monitor Trends** - Watch for declining performance trends
2. **Address Bottlenecks** - Prioritize critical and high-severity bottlenecks
3. **Implement Recommendations** - Follow optimization recommendations systematically
4. **Measure Impact** - Track improvement after implementing optimizations

### Data Management
1. **Regular Cleanup** - Clean up old evaluation data periodically
2. **Backup Data** - Backup evaluation databases regularly
3. **Monitor Storage** - Monitor database storage usage
4. **Archive Sessions** - Archive completed evaluation sessions

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```python
   # Ensure database URL is correct
   config = OpenEvolveConfig(
       database_url="sqlite:///path/to/database.db"
   )
   ```

2. **OpenEvolve Import Errors**
   ```python
   # Set OpenEvolve repository path
   config = OpenEvolveConfig(
       openevolve_repo_path="/path/to/OpenAlpha_Evolve"
   )
   ```

3. **Low Effectiveness Scores**
   - Check component implementation
   - Validate evaluation criteria
   - Review input data quality
   - Adjust effectiveness thresholds

4. **Performance Issues**
   - Enable caching
   - Reduce concurrent evaluations
   - Optimize database queries
   - Use appropriate batch sizes

### Logging

Enable detailed logging for debugging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

config = OpenEvolveConfig(
    log_level="DEBUG",
    enable_detailed_logging=True
)
```

## Examples

See `examples/openevolve_integration_demo.py` for a comprehensive demonstration of all system capabilities.

## API Reference

### OpenEvolveIntegrator

Main integration class for coordinating evaluations.

#### Methods
- `initialize()` - Initialize the integration system
- `evaluate_component()` - Evaluate a single component
- `evaluate_all_components()` - Evaluate multiple components
- `get_session_summary()` - Get evaluation session summary
- `cleanup()` - Cleanup resources

### PerformanceAnalyzer

Comprehensive performance analysis tool.

#### Methods
- `analyze_component_performance()` - Analyze component performance
- `_analyze_bottlenecks()` - Identify performance bottlenecks
- `_analyze_performance_trends()` - Analyze performance trends
- `_identify_optimization_opportunities()` - Find optimization opportunities

### EffectivenessEvaluator

Core effectiveness evaluation engine.

#### Methods
- `evaluate_effectiveness()` - Evaluate component effectiveness
- `_analyze_performance_metrics()` - Analyze performance metrics
- `_perform_correlation_analysis()` - Perform correlation analysis
- `_generate_optimization_recommendations()` - Generate recommendations

## Contributing

To contribute to the OpenEvolve Integration & Evaluation System:

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for any API changes
4. Ensure compatibility with the OpenEvolve framework
5. Follow the established logging and error handling patterns

## License

This integration system is part of the graph-sitter project and follows the same licensing terms.

