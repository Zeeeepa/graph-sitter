-- Enhanced Database Schema: OpenEvolve Integration
-- Part 2: Evolutionary Algorithm and Optimization Infrastructure

-- Evolution Experiments Table
CREATE TABLE evolution_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    problem_definition JSONB NOT NULL, -- Problem statement and constraints
    objective_function JSONB NOT NULL, -- Optimization objectives
    population_size INTEGER DEFAULT 50,
    max_generations INTEGER DEFAULT 100,
    current_generation INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'initialized', -- 'initialized', 'running', 'completed', 'failed', 'paused'
    best_score DECIMAL(10,4),
    convergence_threshold DECIMAL(10,6),
    mutation_rate DECIMAL(3,2) DEFAULT 0.1,
    crossover_rate DECIMAL(3,2) DEFAULT 0.8,
    selection_strategy VARCHAR(100) DEFAULT 'tournament',
    llm_config JSONB, -- LLM settings for code generation
    evaluation_config JSONB, -- How to evaluate generated code
    experiment_metadata JSONB, -- Additional experiment parameters
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    
    CHECK (status IN ('initialized', 'running', 'completed', 'failed', 'paused', 'cancelled')),
    CHECK (population_size > 0),
    CHECK (max_generations > 0),
    CHECK (current_generation >= 0 AND current_generation <= max_generations),
    CHECK (mutation_rate >= 0.0 AND mutation_rate <= 1.0),
    CHECK (crossover_rate >= 0.0 AND crossover_rate <= 1.0),
    CHECK (convergence_threshold > 0),
    CHECK (selection_strategy IN ('tournament', 'roulette', 'rank', 'elitist'))
);

-- Indexes for evolution_experiments
CREATE INDEX idx_evolution_experiments_status ON evolution_experiments(status);
CREATE INDEX idx_evolution_experiments_created_at ON evolution_experiments(created_at);
CREATE INDEX idx_evolution_experiments_name ON evolution_experiments(name);
CREATE INDEX idx_evolution_experiments_creator ON evolution_experiments(created_by);

-- Evolution Generations Table
CREATE TABLE evolution_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES evolution_experiments(id) ON DELETE CASCADE,
    generation_number INTEGER NOT NULL,
    population_data JSONB NOT NULL, -- Array of individuals in this generation
    generation_stats JSONB, -- Min, max, avg, std dev of scores
    best_individual_id UUID,
    worst_individual_id UUID,
    diversity_metrics JSONB, -- Genetic diversity measurements
    selection_pressure DECIMAL(3,2),
    convergence_metrics JSONB,
    generation_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generation_end TIMESTAMP WITH TIME ZONE,
    evaluation_time_total_ms INTEGER,
    mutation_count INTEGER DEFAULT 0,
    crossover_count INTEGER DEFAULT 0,
    
    UNIQUE(experiment_id, generation_number),
    CHECK (generation_number >= 0),
    CHECK (selection_pressure >= 0.0 AND selection_pressure <= 1.0),
    CHECK (evaluation_time_total_ms >= 0),
    CHECK (mutation_count >= 0),
    CHECK (crossover_count >= 0)
);

-- Indexes for evolution_generations
CREATE INDEX idx_evolution_generations_experiment ON evolution_generations(experiment_id);
CREATE INDEX idx_evolution_generations_number ON evolution_generations(generation_number);
CREATE INDEX idx_evolution_generations_start ON evolution_generations(generation_start);

-- Evolution Individuals Table
CREATE TABLE evolution_individuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generation_id UUID NOT NULL REFERENCES evolution_generations(id) ON DELETE CASCADE,
    experiment_id UUID NOT NULL REFERENCES evolution_experiments(id) ON DELETE CASCADE,
    individual_index INTEGER NOT NULL, -- Position in generation
    genotype JSONB NOT NULL, -- Code representation/parameters
    phenotype TEXT, -- Actual executable code
    fitness_score DECIMAL(10,4),
    evaluation_metrics JSONB, -- Detailed performance metrics
    parent_ids UUID[], -- Array of parent individual IDs
    mutation_applied JSONB, -- What mutations were applied
    crossover_applied JSONB, -- Crossover operations applied
    evaluation_time_ms INTEGER,
    evaluation_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'evaluating', 'completed', 'failed'
    error_log TEXT,
    code_complexity_metrics JSONB, -- Lines of code, cyclomatic complexity, etc.
    performance_benchmarks JSONB, -- Runtime, memory usage, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evaluated_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(generation_id, individual_index),
    CHECK (individual_index >= 0),
    CHECK (evaluation_time_ms >= 0),
    CHECK (evaluation_status IN ('pending', 'evaluating', 'completed', 'failed', 'timeout'))
);

-- Indexes for evolution_individuals
CREATE INDEX idx_evolution_individuals_generation ON evolution_individuals(generation_id);
CREATE INDEX idx_evolution_individuals_experiment ON evolution_individuals(experiment_id);
CREATE INDEX idx_evolution_individuals_fitness ON evolution_individuals(fitness_score DESC NULLS LAST);
CREATE INDEX idx_evolution_individuals_status ON evolution_individuals(evaluation_status);
CREATE INDEX idx_evolution_individuals_parents ON evolution_individuals USING GIN(parent_ids);

-- Evolution Operations Log Table
CREATE TABLE evolution_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES evolution_experiments(id) ON DELETE CASCADE,
    generation_id UUID REFERENCES evolution_generations(id) ON DELETE CASCADE,
    operation_type VARCHAR(100) NOT NULL, -- 'mutation', 'crossover', 'selection', 'evaluation'
    operation_subtype VARCHAR(100), -- Specific type of operation
    source_individual_ids UUID[], -- Individuals involved in operation
    target_individual_id UUID, -- Result individual (if applicable)
    operation_parameters JSONB, -- Parameters used for the operation
    operation_result JSONB, -- Result of the operation
    success BOOLEAN DEFAULT true,
    execution_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    llm_prompt TEXT, -- LLM prompt used (for LLM-based operations)
    llm_response TEXT, -- LLM response
    llm_model VARCHAR(100), -- Which LLM model was used
    
    CHECK (operation_type IN ('mutation', 'crossover', 'selection', 'evaluation', 'initialization')),
    CHECK (execution_time_ms >= 0)
);

-- Indexes for evolution_operations
CREATE INDEX idx_evolution_operations_experiment ON evolution_operations(experiment_id);
CREATE INDEX idx_evolution_operations_generation ON evolution_operations(generation_id);
CREATE INDEX idx_evolution_operations_type ON evolution_operations(operation_type);
CREATE INDEX idx_evolution_operations_timestamp ON evolution_operations(timestamp);
CREATE INDEX idx_evolution_operations_target ON evolution_operations(target_individual_id);

-- Code Evaluation Results Table
CREATE TABLE code_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    individual_id UUID NOT NULL REFERENCES evolution_individuals(id) ON DELETE CASCADE,
    evaluation_type VARCHAR(100) NOT NULL, -- 'functional', 'performance', 'quality', 'security'
    test_suite_id VARCHAR(255), -- Reference to test suite used
    test_cases_passed INTEGER DEFAULT 0,
    test_cases_failed INTEGER DEFAULT 0,
    test_cases_total INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    memory_usage_mb DECIMAL(10,2),
    cpu_usage_percent DECIMAL(5,2),
    correctness_score DECIMAL(3,2), -- 0.00 to 1.00
    efficiency_score DECIMAL(3,2), -- 0.00 to 1.00
    maintainability_score DECIMAL(3,2), -- 0.00 to 1.00
    security_score DECIMAL(3,2), -- 0.00 to 1.00
    detailed_results JSONB, -- Detailed test results and metrics
    evaluation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evaluator_version VARCHAR(50),
    
    CHECK (evaluation_type IN ('functional', 'performance', 'quality', 'security', 'integration')),
    CHECK (test_cases_passed >= 0),
    CHECK (test_cases_failed >= 0),
    CHECK (test_cases_total >= 0),
    CHECK (test_cases_passed + test_cases_failed <= test_cases_total),
    CHECK (execution_time_ms >= 0),
    CHECK (memory_usage_mb >= 0),
    CHECK (cpu_usage_percent >= 0 AND cpu_usage_percent <= 100),
    CHECK (correctness_score >= 0.00 AND correctness_score <= 1.00),
    CHECK (efficiency_score >= 0.00 AND efficiency_score <= 1.00),
    CHECK (maintainability_score >= 0.00 AND maintainability_score <= 1.00),
    CHECK (security_score >= 0.00 AND security_score <= 1.00)
);

-- Indexes for code_evaluations
CREATE INDEX idx_code_evaluations_individual ON code_evaluations(individual_id);
CREATE INDEX idx_code_evaluations_type ON code_evaluations(evaluation_type);
CREATE INDEX idx_code_evaluations_timestamp ON code_evaluations(evaluation_timestamp);
CREATE INDEX idx_code_evaluations_correctness ON code_evaluations(correctness_score DESC);

-- Evolution Experiment Templates Table
CREATE TABLE evolution_experiment_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    problem_category VARCHAR(100), -- 'optimization', 'algorithm_design', 'code_improvement'
    template_config JSONB NOT NULL, -- Default configuration for experiments
    evaluation_framework JSONB, -- Standard evaluation setup
    success_criteria JSONB, -- What constitutes success
    estimated_runtime_hours INTEGER,
    difficulty_level VARCHAR(50), -- 'beginner', 'intermediate', 'advanced', 'expert'
    tags VARCHAR(255)[], -- Array of tags for categorization
    usage_count INTEGER DEFAULT 0,
    average_success_rate DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    
    CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    CHECK (estimated_runtime_hours > 0),
    CHECK (average_success_rate >= 0.00 AND average_success_rate <= 1.00)
);

-- Indexes for evolution_experiment_templates
CREATE INDEX idx_experiment_templates_category ON evolution_experiment_templates(problem_category);
CREATE INDEX idx_experiment_templates_difficulty ON evolution_experiment_templates(difficulty_level);
CREATE INDEX idx_experiment_templates_tags ON evolution_experiment_templates USING GIN(tags);
CREATE INDEX idx_experiment_templates_usage ON evolution_experiment_templates(usage_count DESC);

-- LLM Interaction Log Table
CREATE TABLE llm_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES evolution_experiments(id) ON DELETE CASCADE,
    individual_id UUID REFERENCES evolution_individuals(id) ON DELETE CASCADE,
    interaction_type VARCHAR(100) NOT NULL, -- 'code_generation', 'mutation', 'crossover', 'evaluation'
    llm_model VARCHAR(100) NOT NULL,
    prompt_template VARCHAR(255),
    prompt_text TEXT NOT NULL,
    response_text TEXT,
    token_count_input INTEGER,
    token_count_output INTEGER,
    response_time_ms INTEGER,
    cost_usd DECIMAL(8,4), -- Cost in USD
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB, -- Additional context and parameters
    
    CHECK (interaction_type IN ('code_generation', 'mutation', 'crossover', 'evaluation', 'analysis')),
    CHECK (token_count_input >= 0),
    CHECK (token_count_output >= 0),
    CHECK (response_time_ms >= 0),
    CHECK (cost_usd >= 0)
);

-- Indexes for llm_interactions
CREATE INDEX idx_llm_interactions_experiment ON llm_interactions(experiment_id);
CREATE INDEX idx_llm_interactions_individual ON llm_interactions(individual_id);
CREATE INDEX idx_llm_interactions_type ON llm_interactions(interaction_type);
CREATE INDEX idx_llm_interactions_model ON llm_interactions(llm_model);
CREATE INDEX idx_llm_interactions_timestamp ON llm_interactions(timestamp);
CREATE INDEX idx_llm_interactions_cost ON llm_interactions(cost_usd);

-- Evolution Metrics Aggregation View
CREATE MATERIALIZED VIEW evolution_experiment_summary AS
SELECT 
    e.id,
    e.name,
    e.status,
    e.current_generation,
    e.max_generations,
    e.best_score,
    COUNT(g.id) as generations_completed,
    COUNT(i.id) as total_individuals,
    AVG(i.fitness_score) as avg_fitness,
    MAX(i.fitness_score) as max_fitness,
    MIN(i.fitness_score) as min_fitness,
    SUM(ce.execution_time_ms) as total_evaluation_time_ms,
    SUM(li.cost_usd) as total_llm_cost_usd,
    e.created_at,
    e.started_at,
    e.completed_at
FROM evolution_experiments e
LEFT JOIN evolution_generations g ON e.id = g.experiment_id
LEFT JOIN evolution_individuals i ON g.id = i.generation_id
LEFT JOIN code_evaluations ce ON i.id = ce.individual_id
LEFT JOIN llm_interactions li ON e.id = li.experiment_id
GROUP BY e.id, e.name, e.status, e.current_generation, e.max_generations, 
         e.best_score, e.created_at, e.started_at, e.completed_at;

CREATE UNIQUE INDEX idx_evolution_experiment_summary ON evolution_experiment_summary(id);

-- Trigger to update updated_at timestamps
CREATE TRIGGER update_evolution_experiments_updated_at BEFORE UPDATE ON evolution_experiments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiment_templates_updated_at BEFORE UPDATE ON evolution_experiment_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate fitness statistics for a generation
CREATE OR REPLACE FUNCTION calculate_generation_stats(gen_id UUID)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'min_fitness', MIN(fitness_score),
        'max_fitness', MAX(fitness_score),
        'avg_fitness', AVG(fitness_score),
        'std_fitness', STDDEV(fitness_score),
        'median_fitness', PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fitness_score),
        'individual_count', COUNT(*),
        'successful_evaluations', COUNT(*) FILTER (WHERE evaluation_status = 'completed'),
        'failed_evaluations', COUNT(*) FILTER (WHERE evaluation_status = 'failed')
    )
    INTO stats
    FROM evolution_individuals
    WHERE generation_id = gen_id;
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- Function to update generation statistics
CREATE OR REPLACE FUNCTION update_generation_statistics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE evolution_generations 
    SET generation_stats = calculate_generation_stats(NEW.generation_id)
    WHERE id = NEW.generation_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update generation stats when individuals are updated
CREATE TRIGGER update_generation_stats_trigger
    AFTER INSERT OR UPDATE OF fitness_score, evaluation_status ON evolution_individuals
    FOR EACH ROW
    EXECUTE FUNCTION update_generation_statistics();

-- Comments for documentation
COMMENT ON TABLE evolution_experiments IS 'OpenEvolve experiments with evolutionary algorithm parameters';
COMMENT ON TABLE evolution_generations IS 'Generations within evolution experiments with population data';
COMMENT ON TABLE evolution_individuals IS 'Individual solutions in evolutionary populations';
COMMENT ON TABLE evolution_operations IS 'Log of evolutionary operations (mutation, crossover, selection)';
COMMENT ON TABLE code_evaluations IS 'Detailed evaluation results for generated code';
COMMENT ON TABLE evolution_experiment_templates IS 'Reusable templates for common evolution problems';
COMMENT ON TABLE llm_interactions IS 'Log of all LLM interactions during evolution process';

