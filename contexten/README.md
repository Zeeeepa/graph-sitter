# Contexten - Enhanced Orchestrator

A fully featured orchestrator with SDK-Python and Strands-Agents integration for enhanced memory management, system-level event evaluation, and autonomous CI/CD capabilities.

## 🎯 Overview

Contexten is an advanced orchestration system that combines the power of:

- **SDK-Python**: Model-driven agent building with multiple provider support
- **Strands-Agents**: Advanced tool capabilities and extended memory features
- **Enhanced Memory Management**: Persistent context storage with intelligent retrieval
- **System-Level Event Evaluation**: Real-time monitoring and automated response generation
- **Autonomous CI/CD**: Self-healing pipeline management with intelligent error detection

## 🚀 Features

### Core Orchestration
- **End-to-End Automation**: Complete development lifecycle without human intervention
- **Intelligent Task Management**: AI-powered requirement analysis and task decomposition
- **Self-Healing Architecture**: Automatic error detection, analysis, and resolution
- **Continuous Learning**: System improvement based on historical patterns
- **Scalable Processing**: Parallel development across multiple projects

### SDK-Python Integration
- **Multiple Model Providers**: Amazon Bedrock, Anthropic, OpenAI, Ollama, LlamaAPI
- **Model-Driven Agents**: Create agents with specific configurations and capabilities
- **Tool Integration**: Calculator, file operations, web search, code execution, and more
- **Memory-Enabled Agents**: Persistent context across agent interactions
- **Streaming Support**: Real-time response streaming for better user experience

### Strands-Agents Tools
- **File Operations**: Read, write, and edit files with syntax highlighting
- **Shell Integration**: Secure command execution with safety controls
- **Memory Operations**: Integration with Mem0 and Amazon Bedrock Knowledge Bases
- **HTTP Client**: API requests with comprehensive authentication support
- **Python Execution**: Code execution with state persistence and safety features
- **Mathematical Tools**: Advanced calculations with symbolic math capabilities
- **AWS Integration**: Seamless access to AWS services
- **Swarm Intelligence**: Multi-agent coordination for parallel problem solving

### Memory Management
- **Persistent Storage**: SQLite-based storage with cross-session retention
- **Intelligent Retrieval**: Semantic similarity search with relevance scoring
- **Optimization Algorithms**: Automatic cleanup and performance optimization
- **Context Caching**: In-memory cache for fast access to frequently used data
- **Embedding Support**: Vector-based similarity search for semantic retrieval

### Event Evaluation
- **Real-Time Monitoring**: Continuous system event monitoring
- **Intelligent Classification**: Pattern-based event categorization
- **Automated Response**: Configurable auto-response generation
- **Impact Assessment**: Priority scoring and impact analysis
- **Pattern Learning**: Adaptive pattern recognition and response improvement

### Autonomous CI/CD
- **Pipeline Management**: Automated build, test, and deployment pipelines
- **Error Detection**: Intelligent error pattern recognition
- **Self-Healing**: Automatic error resolution and retry mechanisms
- **Continuous Optimization**: Performance monitoring and improvement
- **Multi-Stage Support**: Setup, build, test, security scan, deploy, monitor

## 📦 Installation

```bash
# Install the enhanced orchestrator
pip install -e .

# Install optional dependencies for specific features
pip install strands-agents strands-agents-tools  # For Strands-Agents integration
pip install boto3  # For AWS integration
pip install mem0  # For advanced memory features
```

## 🔧 Configuration

Create a configuration file `contexten_config.yaml`:

```yaml
# Basic settings
environment: development
debug: false
max_parallel_tasks: 10
task_timeout_seconds: 300

# Memory configuration
memory:
  backend: persistent
  retention_days: 30
  optimization_enabled: true
  cache_size_limit: 1000

# Event evaluation
events:
  monitoring_enabled: true
  classification_threshold: 0.8
  real_time_processing: true

# CI/CD configuration
cicd:
  enabled: true
  auto_healing: true
  continuous_optimization: true

# SDK-Python integration
sdk_python:
  enabled: true
  default_provider: bedrock
  default_model: us.amazon.nova-pro-v1:0
  default_temperature: 0.3

# Strands-Agents integration
strands_agents:
  enabled: true
  memory_backend: mem0
  python_timeout: 120
  shell_confirmation_required: true

# Security settings
security:
  api_key_required: true
  rate_limiting_enabled: true
  max_requests_per_minute: 100
```

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from contexten import EnhancedOrchestrator

async def main():
    # Create orchestrator
    orchestrator = EnhancedOrchestrator()
    
    try:
        # Start the orchestrator
        await orchestrator.start()
        
        # Create an agent
        agent_config = {
            "name": "my_agent",
            "model_provider": "bedrock",
            "temperature": 0.3,
            "memory_enabled": True
        }
        
        agent_id = await orchestrator.create_agent(
            agent_config=agent_config,
            tools=["calculator", "file_operations", "memory_operations"]
        )
        
        # Execute a task
        task_config = {
            "description": "Calculate the square root of 1764",
            "expression": "sqrt(1764)"
        }
        
        result = await orchestrator.execute_task(
            task_id="example_task",
            task_config=task_config,
            agent_id=agent_id
        )
        
        print(f"Task result: {result}")
        
    finally:
        await orchestrator.stop()

# Run the example
asyncio.run(main())
```

### Memory Management

```python
from contexten import MemoryManager

async def memory_example():
    memory = MemoryManager()
    await memory.start()
    
    # Store context
    await memory.store_context(
        context_id="user_prefs",
        data={"theme": "dark", "language": "python"},
        metadata={"type": "user_settings"}
    )
    
    # Retrieve context
    context = await memory.retrieve_context(context_id="user_prefs")
    print(f"Retrieved: {context}")
    
    # Semantic search
    results = await memory.retrieve_context(
        query="user preferences",
        relevance_threshold=0.7
    )
    print(f"Search results: {results}")
    
    await memory.stop()
```

### Event Evaluation

```python
from contexten import EventEvaluator

async def event_example():
    evaluator = EventEvaluator()
    await evaluator.start()
    
    # Evaluate an event
    event_data = {
        "type": "task_execution",
        "status": "failed",
        "error_message": "ImportError: No module named 'missing_lib'"
    }
    
    event_id = await evaluator.evaluate_event(event_data)
    print(f"Event evaluated: {event_id}")
    
    # Get recent events
    events = await evaluator.get_events(limit=10)
    print(f"Recent events: {len(events)}")
    
    await evaluator.stop()
```

### CI/CD Pipeline

```python
from contexten import AutonomousCICD

async def cicd_example():
    cicd = AutonomousCICD()
    await cicd.start()
    
    # Execute a pipeline
    execution_id = await cicd.execute_pipeline(
        pipeline_name="build",
        parameters={"branch": "main"}
    )
    
    # Monitor execution
    status = await cicd.get_execution_status(execution_id)
    print(f"Pipeline status: {status}")
    
    await cicd.stop()
```

## 🛠️ Advanced Usage

### Custom Agent Configuration

```python
# Create an agent with specific model and tools
agent_config = {
    "name": "advanced_agent",
    "model_provider": "anthropic",
    "model_id": "claude-3-sonnet-20240229",
    "temperature": 0.2,
    "max_tokens": 4096,
    "system_prompt": "You are an expert software engineer.",
    "custom_instructions": "Always provide detailed explanations.",
    "memory_enabled": True
}

tools = [
    "calculator",
    "file_operations",
    "python_execution",
    "http_client",
    "memory_operations",
    "swarm_intelligence"
]

agent_id = await orchestrator.create_agent(
    agent_config=agent_config,
    tools=tools,
    memory_context="advanced_session"
)
```

### Complex Task Execution

```python
# Execute a multi-step task
complex_task = {
    "description": "Analyze data, generate report, and send notification",
    "type": "multi_step",
    "steps": [
        {
            "action": "python_execution",
            "code": "import pandas as pd; df = pd.read_csv('data.csv'); summary = df.describe()"
        },
        {
            "action": "file_write",
            "path": "report.txt",
            "content": "Data analysis report"
        },
        {
            "action": "http_request",
            "method": "POST",
            "url": "https://api.example.com/notify",
            "body": '{"message": "Report generated"}'
        }
    ]
}

result = await orchestrator.execute_task(
    task_id="complex_analysis",
    task_config=complex_task,
    use_memory=True
)
```

### Custom Event Patterns

```python
from contexten.events import EventPattern, EventType, EventPriority

# Add custom event pattern
custom_pattern = EventPattern(
    name="custom_error",
    type=EventType.ERROR,
    priority=EventPriority.HIGH,
    conditions={
        "type": "custom_event",
        "severity": "critical"
    },
    response_template="Critical custom error: {error_message}",
    auto_response=True
)

await event_evaluator.add_pattern(custom_pattern)
```

## 📊 Monitoring and Analytics

### Health Monitoring

```python
# Get system health status
health = orchestrator.get_health_status()
print(f"System health: {health}")

# Get component statistics
memory_stats = await orchestrator.get_memory_stats()
event_stats = await orchestrator.get_event_stats()
cicd_status = await orchestrator.get_cicd_status()
```

### Performance Optimization

```python
# Trigger system optimization
optimization_results = await orchestrator.optimize_system()
print(f"Optimization results: {optimization_results}")

# Individual component optimization
memory_optimization = await memory_manager.optimize()
cicd_optimization = await cicd_system.optimize()
```

## 🔒 Security Features

- **API Key Authentication**: Configurable API key requirements
- **Rate Limiting**: Configurable request rate limits
- **Input Validation**: Comprehensive input validation and sanitization
- **Safe Execution**: Sandboxed code execution with timeout controls
- **Audit Logging**: Comprehensive logging of all system activities

## 🧪 Testing

Run the included examples to test functionality:

```bash
python contexten/examples.py
```

## 📚 API Reference

### EnhancedOrchestrator

Main orchestrator class that coordinates all components.

#### Methods

- `start()`: Start the orchestrator and all components
- `stop()`: Stop the orchestrator and cleanup resources
- `create_agent(agent_config, tools, memory_context)`: Create a new agent
- `execute_task(task_id, task_config, agent_id, use_memory)`: Execute a task
- `get_health_status()`: Get system health status
- `optimize_system()`: Trigger system optimization

### MemoryManager

Advanced memory management with persistent storage.

#### Methods

- `store_context(context_id, data, metadata, relevance_score)`: Store context data
- `retrieve_context(context_id, query, relevance_threshold, limit)`: Retrieve context
- `optimize()`: Optimize memory storage
- `get_stats()`: Get memory statistics

### EventEvaluator

System-level event evaluation and monitoring.

#### Methods

- `evaluate_event(event_data)`: Evaluate and process an event
- `get_events(event_type, priority, since, limit)`: Get events matching criteria
- `add_pattern(pattern)`: Add custom event pattern
- `register_handler(event_type, handler)`: Register event handler

### AutonomousCICD

Self-healing CI/CD pipeline management.

#### Methods

- `execute_pipeline(pipeline_name, execution_id, parameters)`: Execute pipeline
- `get_execution_status(execution_id)`: Get execution status
- `list_pipelines()`: List available pipelines
- `optimize()`: Optimize CI/CD system

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the examples for common usage patterns
- Review the configuration documentation

## 🗺️ Roadmap

- [ ] Enhanced swarm intelligence capabilities
- [ ] Additional model provider integrations
- [ ] Advanced analytics and reporting
- [ ] Web-based management interface
- [ ] Kubernetes deployment support
- [ ] Enhanced security features
- [ ] Performance monitoring dashboard

