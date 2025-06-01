# Enhanced Database Schema for Continuous Learning and Analytics

This directory contains the enhanced database schema designed to support continuous learning, pattern analysis, and OpenEvolve integration for the graph-sitter system.

## Overview

The enhanced schema extends the existing 7-module structure with sophisticated machine learning and analytics capabilities while maintaining backward compatibility. It supports:

- **Machine Learning Model Management**: Model versioning, training tracking, and performance monitoring
- **OpenEvolve Integration**: Evolutionary algorithm experiments and optimization tracking
- **Pattern Recognition**: Automated pattern detection and recommendation systems
- **Analytics & Performance**: Time-series analytics and system optimization
- **Integration**: Seamless integration with existing git, user, and API systems

## Schema Structure

### Core Components

1. **[01_learning_models.sql](01_learning_models.sql)** - Machine Learning Infrastructure
   - `ml_models` - Model storage and versioning
   - `training_datasets` - Dataset management and quality tracking
   - `model_training_sessions` - Training process monitoring
   - `model_evaluations` - Performance evaluation results
   - `feature_store` - Feature engineering and management

2. **[02_openevolve_integration.sql](02_openevolve_integration.sql)** - OpenEvolve Integration
   - `evolution_experiments` - Evolutionary algorithm experiments
   - `evolution_generations` - Population tracking across generations
   - `evolution_individuals` - Individual solutions and fitness scores
   - `code_evaluations` - Code quality and performance evaluation
   - `llm_interactions` - LLM usage tracking and cost analysis

3. **[03_pattern_recognition.sql](03_pattern_recognition.sql)** - Pattern Recognition & Analytics
   - `identified_patterns` - Detected patterns and their characteristics
   - `pattern_occurrences` - Specific pattern instances
   - `predictions` - ML model predictions and accuracy tracking
   - `recommendations` - Actionable recommendations
   - `ab_testing_experiments` - A/B testing infrastructure

4. **[04_analytics_performance.sql](04_analytics_performance.sql)** - Analytics & Performance
   - `learning_events` - Time-series event tracking (partitioned)
   - `system_performance_metrics` - High-frequency performance monitoring
   - `query_performance_logs` - Database query optimization
   - `resource_utilization` - System resource monitoring
   - `capacity_planning_metrics` - Growth projection and planning

5. **[05_integration_migration.sql](05_integration_migration.sql)** - Integration & Migration
   - `schema_migrations` - Version control and rollback support
   - `git_operation_learning_events` - Git integration
   - `user_session_learning_events` - User behavior integration
   - `data_quality_checks` - Automated quality monitoring

## Key Features

### 🚀 Performance Optimizations

- **Partitioned Tables**: Time-series tables use range partitioning for optimal performance
- **Strategic Indexing**: Composite indexes for common query patterns
- **Materialized Views**: Pre-computed analytics for fast dashboard queries
- **Query Optimization**: Built-in query performance tracking and optimization

### 🔄 Scalability Design

- **Horizontal Scaling**: Supports sharding and read replicas
- **Data Retention**: Automated archival and cleanup policies
- **Compression**: Built-in data compression strategies
- **Growth Planning**: Capacity planning and resource projection

### 🛡️ Data Quality & Reliability

- **ACID Compliance**: Full transactional integrity
- **Foreign Key Constraints**: Referential integrity across all tables
- **Data Validation**: Check constraints and business rule enforcement
- **Quality Monitoring**: Automated data quality checks and alerting

### 🔗 Integration Points

- **Backward Compatibility**: Seamless integration with existing 7-module schema
- **Event Sourcing**: All changes tracked through learning events
- **API Integration**: RESTful API support through structured data models
- **Real-time Analytics**: Support for streaming analytics and real-time dashboards

## Installation

### Prerequisites

- PostgreSQL 13+ with extensions:
  - `uuid-ossp` for UUID generation
  - `pg_cron` for scheduled jobs
  - `pg_stat_statements` for query performance tracking

### Deployment Steps

1. **Backup Existing Data**
   ```sql
   SELECT backup_critical_data();
   ```

2. **Apply Schema in Order**
   ```bash
   psql -f 01_learning_models.sql
   psql -f 02_openevolve_integration.sql
   psql -f 03_pattern_recognition.sql
   psql -f 04_analytics_performance.sql
   psql -f 05_integration_migration.sql
   ```

3. **Validate Installation**
   ```sql
   SELECT * FROM validate_schema_integrity();
   ```

4. **Migrate Existing Data**
   ```sql
   SELECT * FROM migrate_existing_data();
   ```

## Usage Examples

### Machine Learning Workflow

```sql
-- Create a new model
INSERT INTO ml_models (name, version, model_type, framework, hyperparameters)
VALUES ('pattern_classifier', 'v1.0', 'pattern_recognition', 'scikit-learn', 
        '{"n_estimators": 100, "max_depth": 10}');

-- Track training session
INSERT INTO model_training_sessions (model_id, dataset_id, total_epochs)
VALUES ('model-uuid', 'dataset-uuid', 50);

-- Record predictions
INSERT INTO predictions (model_id, prediction_type, target_entity_type, 
                        predicted_value, confidence_interval)
VALUES ('model-uuid', 'bug_likelihood', 'code_file', 
        '{"probability": 0.85}', '{"lower": 0.80, "upper": 0.90}');
```

### OpenEvolve Experiment

```sql
-- Start evolution experiment
INSERT INTO evolution_experiments (name, problem_definition, objective_function)
VALUES ('optimize_sorting', 
        '{"problem": "optimize sorting algorithm"}',
        '{"metrics": ["execution_time", "memory_usage"]}');

-- Track individual solutions
INSERT INTO evolution_individuals (generation_id, genotype, phenotype, fitness_score)
VALUES ('gen-uuid', '{"params": {"algorithm": "quicksort"}}', 
        'def quicksort(arr): ...', 0.92);
```

### Pattern Detection

```sql
-- Record detected pattern
INSERT INTO identified_patterns (pattern_type, pattern_name, confidence_score)
VALUES ('code_smell', 'long_method', 0.95);

-- Track pattern occurrence
INSERT INTO pattern_occurrences (pattern_id, source_type, source_id, location_data)
VALUES ('pattern-uuid', 'code_file', 'file123', 
        '{"file": "utils.py", "line_start": 45, "line_end": 120}');
```

## Query Examples

See [examples/common_queries.sql](examples/common_queries.sql) for comprehensive query examples including:

- Model performance analysis
- Evolution experiment tracking
- Pattern trend analysis
- System performance monitoring
- A/B testing results
- Data quality reports

## Monitoring & Maintenance

### Automated Jobs

The schema includes several automated maintenance jobs:

- **Data Cleanup**: Removes old learning events (weekly)
- **View Refresh**: Updates materialized views (every 15 minutes)
- **Partition Creation**: Creates new partitions (monthly)
- **Quality Checks**: Validates data quality (daily)
- **Health Monitoring**: System health checks (every 5 minutes)

### Performance Monitoring

Key metrics to monitor:

- Learning event processing lag
- Model prediction accuracy trends
- Query performance degradation
- Resource utilization thresholds
- Data quality scores

### Alerting Thresholds

- Learning event lag > 5 minutes
- Model accuracy drops > 20% from baseline
- Query response time > 2x baseline
- Data quality score < 90%
- Resource utilization > 85%

## Migration Strategy

### Phase 1: Core Infrastructure (Weeks 1-2)
- Deploy ML model and training infrastructure
- Set up basic learning events tracking
- Implement partitioning for time-series tables

### Phase 2: OpenEvolve Integration (Weeks 3-4)
- Deploy evolution experiment tracking
- Integrate with existing git operations
- Add LLM interaction logging

### Phase 3: Pattern Recognition (Weeks 5-6)
- Implement pattern detection systems
- Deploy recommendation engine
- Add A/B testing infrastructure

### Phase 4: Analytics & Optimization (Weeks 7-8)
- Create analytics dashboards
- Implement data retention policies
- Optimize query performance

## Rollback Procedures

If rollback is needed:

```sql
-- Rollback to specific version
SELECT rollback_schema_version('2024.12.001');

-- Restore from backup
-- (Restore backup tables created during migration)
```

## Security Considerations

- **Row-Level Security**: Implemented for multi-tenant access
- **Data Encryption**: Sensitive model data encrypted at field level
- **Audit Logging**: All data access logged for compliance
- **Access Control**: Role-based permissions for different user types

## Performance Benchmarks

Target performance metrics:

| Operation | Target Performance |
|-----------|-------------------|
| Learning event insertion | <10ms p95 |
| Pattern detection queries | <100ms p95 |
| Analytics aggregations | <5s p95 |
| Model training data retrieval | <1s p95 |
| Evolution experiment queries | <500ms p95 |

## Storage Projections

| Component | Daily Volume | Annual Storage |
|-----------|--------------|----------------|
| Learning Events | 1M events | 12GB |
| Performance Metrics | 10M metrics | 120GB |
| Pattern Occurrences | 100K patterns | 1.2GB |
| Evolution Data | 1K experiments | 500MB |
| **Total** | | **~134GB/year** |

## Support & Troubleshooting

### Common Issues

1. **Partition Creation Failures**
   - Ensure pg_cron extension is installed
   - Check partition creation function permissions

2. **Performance Degradation**
   - Monitor index usage with `pg_stat_user_indexes`
   - Check for missing statistics with `ANALYZE`

3. **Data Quality Issues**
   - Review data quality check results
   - Validate foreign key constraints

### Getting Help

- Check the [common queries](examples/common_queries.sql) for usage patterns
- Review function documentation in the SQL files
- Monitor system health with built-in health checks

## Contributing

When extending the schema:

1. Follow the established naming conventions
2. Add appropriate indexes for new query patterns
3. Include data validation constraints
4. Update materialized views if needed
5. Add corresponding rollback scripts
6. Document new tables and functions

## License

This schema is part of the graph-sitter project and follows the same licensing terms.

