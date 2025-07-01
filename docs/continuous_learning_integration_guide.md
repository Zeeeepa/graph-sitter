# Continuous Learning and Analytics System Integration Guide

## Overview

This guide explains how to integrate and use the Continuous Learning and Analytics System with the existing graph-sitter codebase analysis capabilities.

## Quick Start

### 1. Installation

```bash
# Install additional dependencies
pip install -r requirements_continuous_learning.txt

# For development
pip install -e .
```

### 2. Basic Usage

```python
import asyncio
from graph_sitter import Codebase
from src.continuous_learning import ContinuousLearningPipeline

async def analyze_codebase():
    # Initialize the learning pipeline
    pipeline = ContinuousLearningPipeline()
    await pipeline.start_pipeline()
    
    # Load your codebase
    codebase = Codebase.from_repo("your-org/your-repo")
    
    # Process through the learning pipeline
    result = await pipeline.process_codebase(codebase)
    
    # Get patterns and recommendations
    patterns = result['patterns']
    recommendations = result['recommendations']
    
    print(f"Found {len(patterns)} patterns")
    print(f"Generated {len(recommendations)} recommendations")
    
    # Stop the pipeline
    await pipeline.stop_pipeline()

# Run the analysis
asyncio.run(analyze_codebase())
```

### 3. Run the Demo

```bash
python examples/continuous_learning_demo.py
```

## Core Components

### 1. Pattern Engine

The Pattern Engine identifies code patterns using multiple recognition algorithms:

```python
from src.continuous_learning import PatternEngine

# Initialize pattern engine
pattern_engine = PatternEngine()

# Identify patterns in a codebase
patterns = pattern_engine.identify_patterns(codebase)

# Get pattern-based recommendations
recommendations = pattern_engine.get_pattern_recommendations(codebase)

# Update pattern confidence based on feedback
pattern_engine.update_pattern_confidence(pattern_id, feedback_score)
```

**Supported Pattern Types:**
- Design Patterns (Singleton, Factory, Observer, etc.)
- Performance Patterns (Caching, Lazy Loading, etc.)
- Error Patterns (Common error scenarios)
- Refactoring Patterns (Code improvement opportunities)
- Testing Patterns (Testing best practices)
- Architectural Patterns (System design patterns)

### 2. Knowledge Graph

The Knowledge Graph stores learned patterns and their relationships:

```python
from src.continuous_learning import KnowledgeGraph

# Initialize knowledge graph
knowledge_graph = KnowledgeGraph()

# Add patterns to the graph
pattern_node_id = knowledge_graph.add_pattern(pattern)

# Create relationships between patterns
knowledge_graph.create_relationship(
    source_id, target_id, 
    RelationshipType.SIMILAR_TO,
    confidence=0.8
)

# Find similar patterns
similar_patterns = knowledge_graph.find_similar_patterns(target_pattern)

# Get recommendations
recommendations = knowledge_graph.get_recommendations(codebase, patterns)
```

### 3. Analytics Processor

The Analytics Processor provides real-time analytics and enhanced codebase analysis:

```python
from src.continuous_learning import AnalyticsProcessor

# Initialize analytics processor
analytics = AnalyticsProcessor()

# Process codebase with enhanced analytics
result = await analytics.process_codebase_analysis(codebase)

# Get dashboard data
dashboard_data = analytics.get_analytics_dashboard_data()

# Register custom event handlers
analytics.register_custom_handler(EventType.CODE_ANALYSIS, my_handler)
```

### 4. Continuous Learning Pipeline

The main pipeline coordinates all components:

```python
from src.continuous_learning import ContinuousLearningPipeline

# Initialize pipeline
pipeline = ContinuousLearningPipeline()

# Start background learning
await pipeline.start_pipeline()

# Process codebase
result = await pipeline.process_codebase(codebase)

# Submit user feedback
await pipeline.submit_feedback(pattern_id, "positive", feedback_data)

# Submit performance metrics
await pipeline.submit_performance_metrics(operation, metrics)

# Get pipeline statistics
stats = pipeline.get_pipeline_statistics()
```

## Integration with Existing Graph-Sitter

### Enhanced Codebase Analysis

The system extends the existing `codebase_analysis.py` functions:

```python
from src.continuous_learning.analytics_processor import EnhancedCodebaseAnalyzer

# Create enhanced analyzer
enhanced_analyzer = EnhancedCodebaseAnalyzer()

# Get enhanced analysis (includes existing + new features)
analysis = enhanced_analyzer.enhanced_analysis(codebase)

# Access base summary (original functionality)
base_summary = analysis['base_summary']

# Access new features
quality_score = analysis['quality_score']
trends = analysis['trends']
predictions = analysis['predictions']
recommendations = analysis['recommendations']
```

### Backward Compatibility

All existing graph-sitter functions continue to work unchanged:

```python
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary
)

# These functions work exactly as before
summary = get_codebase_summary(codebase)
file_summary = get_file_summary(file)
```

## Configuration

### Environment Variables

```bash
# Knowledge Graph Configuration
KNOWLEDGE_GRAPH_BACKEND=neo4j  # or 'memory' for development
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Vector Database Configuration
VECTOR_DB_BACKEND=pinecone  # or 'weaviate'
PINECONE_API_KEY=your_api_key
PINECONE_ENVIRONMENT=us-west1-gcp

# Stream Processing Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=continuous_learning

# Caching Configuration
REDIS_URL=redis://localhost:6379/0

# Analytics Configuration
METRICS_RETENTION_DAYS=30
ANOMALY_DETECTION_THRESHOLD=2.0
LEARNING_RATE=0.1
```

### Configuration File

Create `config/continuous_learning.yaml`:

```yaml
pattern_engine:
  cache_size: 1000
  similarity_threshold: 0.7
  learning_rate: 0.1

knowledge_graph:
  backend: memory  # or neo4j
  max_nodes: 10000
  relationship_confidence_threshold: 0.5

analytics:
  buffer_size: 1000
  window_size_seconds: 60
  anomaly_threshold: 2.0

pipeline:
  queue_size: 1000
  batch_size: 100
  processing_interval_seconds: 5
```

## Advanced Usage

### Custom Pattern Recognizers

```python
from src.continuous_learning.pattern_engine import PatternRecognizer, CodePattern

class CustomPatternRecognizer(PatternRecognizer):
    def recognize_patterns(self, codebase):
        patterns = []
        # Your custom pattern recognition logic
        return patterns
    
    def get_pattern_confidence(self, pattern):
        # Your confidence calculation
        return confidence

# Register custom recognizer
pattern_engine = PatternEngine()
pattern_engine.recognizers.append(CustomPatternRecognizer())
```

### Custom Event Handlers

```python
async def custom_analysis_handler(event):
    """Custom handler for code analysis events."""
    codebase = event.data['codebase']
    # Your custom processing logic
    
# Register handler
analytics.register_custom_handler(EventType.CODE_ANALYSIS, custom_analysis_handler)
```

### Custom Metrics

```python
from src.continuous_learning.analytics_processor import Metric, MetricType

# Create custom metric
custom_metric = Metric(
    metric_name="custom_complexity",
    metric_type=MetricType.QUALITY,
    value=calculate_custom_complexity(codebase),
    timestamp=time.time(),
    tags={'project': 'my_project'}
)

# Collect metric
analytics.metrics_collector.collect_metric(custom_metric)
```

## Production Deployment

### Docker Configuration

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_continuous_learning.txt .
RUN pip install -r requirements_continuous_learning.txt

# Copy application code
COPY src/ /app/src/
COPY examples/ /app/examples/

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV KNOWLEDGE_GRAPH_BACKEND=neo4j
ENV VECTOR_DB_BACKEND=pinecone

# Run the application
CMD ["python", "examples/continuous_learning_demo.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: continuous-learning
spec:
  replicas: 3
  selector:
    matchLabels:
      app: continuous-learning
  template:
    metadata:
      labels:
        app: continuous-learning
    spec:
      containers:
      - name: continuous-learning
        image: continuous-learning:latest
        env:
        - name: KNOWLEDGE_GRAPH_BACKEND
          value: "neo4j"
        - name: NEO4J_URI
          valueFrom:
            secretKeyRef:
              name: neo4j-secret
              key: uri
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### Monitoring and Observability

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
patterns_identified = Counter('patterns_identified_total', 'Total patterns identified')
processing_duration = Histogram('processing_duration_seconds', 'Processing duration')
active_patterns = Gauge('active_patterns', 'Number of active patterns')

# Use in your code
patterns_identified.inc()
with processing_duration.time():
    result = await pipeline.process_codebase(codebase)
active_patterns.set(len(patterns))
```

## Troubleshooting

### Common Issues

1. **Memory Issues with Large Codebases**
   ```python
   # Use streaming processing for large codebases
   pipeline = ContinuousLearningPipeline()
   pipeline.analytics_processor.metrics_collector.buffer_size = 500  # Reduce buffer
   ```

2. **Slow Pattern Recognition**
   ```python
   # Enable caching
   pattern_engine = PatternEngine()
   pattern_engine.pattern_cache = {}  # Enable caching
   ```

3. **Knowledge Graph Performance**
   ```python
   # Use production database
   from src.continuous_learning.knowledge_graph import Neo4jKnowledgeGraphStorage
   storage = Neo4jKnowledgeGraphStorage(uri="bolt://localhost:7687")
   knowledge_graph = KnowledgeGraph(storage=storage)
   ```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('continuous_learning')
logger.setLevel(logging.DEBUG)

# Run with debug information
pipeline = ContinuousLearningPipeline()
# Debug information will be printed
```

### Performance Tuning

```python
# Optimize for your use case
pipeline = ContinuousLearningPipeline()

# Adjust queue size for high throughput
pipeline.learning_queue = asyncio.Queue(maxsize=5000)

# Adjust processing intervals
pipeline.processing_interval = 1.0  # Process every second

# Tune similarity threshold
pipeline.knowledge_graph.similarity_matcher.similarity_threshold = 0.8
```

## API Reference

See the individual module documentation for detailed API reference:

- [Pattern Engine API](../src/continuous_learning/pattern_engine.py)
- [Knowledge Graph API](../src/continuous_learning/knowledge_graph.py)
- [Analytics Processor API](../src/continuous_learning/analytics_processor.py)
- [Learning Pipeline API](../src/continuous_learning/learning_pipeline.py)

## Contributing

To contribute to the continuous learning system:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run tests
pytest tests/continuous_learning/

# Run with coverage
pytest --cov=src/continuous_learning tests/continuous_learning/
```

## Support

For questions and support:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [API documentation](#api-reference)
3. Open an issue on GitHub
4. Contact the development team

## License

This continuous learning system is part of the graph-sitter project and follows the same license terms.

