# OpenEvolve Integration Architecture

## Overview

This document outlines the comprehensive integration architecture between Graph-Sitter's task management system and OpenEvolve's evaluation framework for step-by-step effectiveness analysis.

## Integration Components

### 1. Core OpenEvolve Components

#### Evaluator (`src/core/evaluator/evaluator.py`)
- **Purpose**: Step-by-step effectiveness analysis of task implementations
- **Key Features**:
  - Async program evaluation with multiple strategies
  - LLM-based code evaluation and scoring
  - Parallel evaluation capabilities
  - Cascade evaluation for complex scenarios

#### Database (`src/core/engine/database.py`)
- **Purpose**: Program storage and evolution tracking
- **Key Features**:
  - Program versioning and genealogy tracking
  - Performance metrics storage
  - Complexity and diversity calculations
  - Evolution iteration tracking

#### Controller (`src/core/engine/controller.py`)
- **Purpose**: Main orchestration and workflow management
- **Key Features**:
  - Evolution process coordination
  - Prompt sampling and LLM ensemble management
  - Best program tracking across iterations
  - Detailed logging and metadata management

### 2. Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Graph-Sitter Task Management                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Task Engine   │  │  Analytics      │  │   Workflow      │  │
│  │                 │  │  System         │  │   Manager       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Integration Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Evaluator     │  │   Database      │  │   Controller    │  │
│  │   Adapter       │  │   Bridge        │  │   Proxy         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      OpenEvolve Core                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   evaluator.py  │  │   database.py   │  │  controller.py  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Data Flow Architecture

#### Task Evaluation Flow
1. **Task Creation** → Graph-Sitter Task Engine
2. **Implementation Generation** → Task execution with code generation
3. **Evaluation Request** → OpenEvolve Evaluator via Integration Layer
4. **Step-by-Step Analysis** → OpenEvolve evaluation pipeline
5. **Results Storage** → Both Graph-Sitter Analytics and OpenEvolve Database
6. **Feedback Loop** → Continuous improvement based on evaluation metrics

#### Metrics Collection Flow
1. **Code Analysis** → Graph-Sitter Analytics System
2. **Complexity Metrics** → OpenEvolve Database for evolution tracking
3. **Performance Data** → Shared metrics storage
4. **Quality Indicators** → Cross-system quality scoring

## API Contracts

### 1. Evaluator Integration API

```python
class EvaluatorAdapter:
    """Adapter for OpenEvolve Evaluator integration"""
    
    async def evaluate_task_implementation(
        self,
        task_id: str,
        implementation_code: str,
        evaluation_criteria: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate a task implementation using OpenEvolve's evaluation system
        
        Args:
            task_id: Unique identifier for the task
            implementation_code: Code to be evaluated
            evaluation_criteria: Specific criteria for evaluation
            context: Additional context for evaluation
            
        Returns:
            EvaluationResult with scores, metrics, and recommendations
        """
        pass
    
    async def evaluate_multiple_implementations(
        self,
        implementations: List[TaskImplementation]
    ) -> List[EvaluationResult]:
        """Batch evaluation of multiple implementations"""
        pass
```

### 2. Database Bridge API

```python
class DatabaseBridge:
    """Bridge between Graph-Sitter and OpenEvolve databases"""
    
    def store_program_evolution(
        self,
        task_id: str,
        program: Program,
        parent_id: Optional[str] = None
    ) -> str:
        """Store program evolution data in OpenEvolve format"""
        pass
    
    def get_evolution_history(
        self,
        task_id: str
    ) -> List[Program]:
        """Retrieve evolution history for a task"""
        pass
    
    def sync_metrics(
        self,
        task_id: str,
        graph_sitter_metrics: Dict[str, Any],
        openevolve_metrics: Dict[str, Any]
    ) -> None:
        """Synchronize metrics between systems"""
        pass
```

### 3. Controller Proxy API

```python
class ControllerProxy:
    """Proxy for OpenEvolve Controller integration"""
    
    async def orchestrate_task_evolution(
        self,
        task_id: str,
        initial_implementation: str,
        evolution_config: EvolutionConfig
    ) -> EvolutionResult:
        """Orchestrate task implementation evolution"""
        pass
    
    def track_best_implementation(
        self,
        task_id: str,
        implementation: str,
        metrics: Dict[str, float]
    ) -> None:
        """Track the best implementation across evolution steps"""
        pass
```

## Database Schema Extensions

### 1. OpenEvolve Integration Tables

```sql
-- OpenEvolve evaluation results
CREATE TABLE openevolve_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    program_id VARCHAR(255) NOT NULL,
    evaluation_type VARCHAR(50) NOT NULL,
    
    -- Evaluation results
    scores JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '[]',
    
    -- Evolution tracking
    generation INTEGER DEFAULT 0,
    parent_program_id VARCHAR(255),
    iteration_found INTEGER DEFAULT 0,
    
    -- Performance data
    evaluation_duration_ms INTEGER,
    complexity_score DECIMAL(10,4),
    diversity_score DECIMAL(10,4),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_openevolve_task_id (task_id),
    INDEX idx_openevolve_program_id (program_id),
    INDEX idx_openevolve_generation (generation)
);

-- Program evolution tracking
CREATE TABLE program_evolution (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    program_id VARCHAR(255) NOT NULL,
    
    -- Program data
    code TEXT NOT NULL,
    language VARCHAR(50) DEFAULT 'python',
    
    -- Evolution metadata
    parent_id VARCHAR(255),
    generation INTEGER DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    iteration_found INTEGER DEFAULT 0,
    
    -- Performance metrics
    metrics JSONB DEFAULT '{}',
    complexity DECIMAL(10,4) DEFAULT 0.0,
    diversity DECIMAL(10,4) DEFAULT 0.0,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(task_id, program_id),
    INDEX idx_program_evolution_task (task_id),
    INDEX idx_program_evolution_parent (parent_id),
    INDEX idx_program_evolution_generation (generation)
);
```

### 2. Events Module Extension

```sql
-- OpenEvolve-specific events
CREATE TABLE openevolve_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    
    -- Event data
    program_id VARCHAR(255),
    evaluation_id UUID REFERENCES openevolve_evaluations(id),
    
    -- Event details
    event_data JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    
    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_openevolve_events_task (task_id),
    INDEX idx_openevolve_events_type (event_type),
    INDEX idx_openevolve_events_time (occurred_at)
);
```

## Performance Considerations

### 1. Async Integration
- All OpenEvolve operations are async to prevent blocking
- Task pool management for parallel evaluations
- Timeout handling for long-running evaluations

### 2. Data Synchronization
- Eventual consistency between Graph-Sitter and OpenEvolve databases
- Conflict resolution strategies for concurrent updates
- Batch operations for bulk data synchronization

### 3. Caching Strategy
- Evaluation result caching to avoid redundant computations
- Program evolution caching for quick ancestry lookups
- Metrics aggregation caching for dashboard performance

## Implementation Phases

### Phase 1: Core Integration (Week 1)
- [ ] Implement EvaluatorAdapter
- [ ] Create DatabaseBridge
- [ ] Set up basic ControllerProxy
- [ ] Add OpenEvolve integration tables

### Phase 2: Advanced Features (Week 2)
- [ ] Implement batch evaluation capabilities
- [ ] Add evolution tracking and genealogy
- [ ] Create metrics synchronization
- [ ] Implement caching layer

### Phase 3: Optimization (Week 3)
- [ ] Performance tuning and optimization
- [ ] Advanced error handling and recovery
- [ ] Comprehensive monitoring and alerting
- [ ] Integration testing and validation

## Success Metrics

1. **Integration Performance**
   - Evaluation latency < 5 seconds for typical tasks
   - Batch evaluation throughput > 100 tasks/minute
   - Data synchronization lag < 1 second

2. **System Reliability**
   - 99.9% evaluation success rate
   - Zero data loss during synchronization
   - Graceful degradation under load

3. **Quality Improvements**
   - 25% improvement in task implementation quality
   - 50% reduction in implementation iterations
   - Measurable learning from evaluation feedback

## Monitoring and Observability

### Key Metrics to Track
- Evaluation request volume and latency
- Success/failure rates for evaluations
- Data synchronization performance
- Evolution convergence rates
- Quality improvement trends

### Alerting Thresholds
- Evaluation latency > 10 seconds
- Success rate < 95%
- Synchronization lag > 5 seconds
- Memory usage > 80%

This architecture provides a robust foundation for integrating OpenEvolve's powerful evaluation capabilities with Graph-Sitter's task management system, enabling continuous improvement through step-by-step effectiveness analysis.

