# Implementation Guide: Enhanced Database Schema for Continuous Learning

This guide provides step-by-step instructions for implementing the enhanced database schema research findings from ZAM-1048.

## Executive Summary

The enhanced database schema provides a comprehensive foundation for continuous learning, OpenEvolve integration, and advanced analytics while maintaining compatibility with the existing 7-module structure. This implementation will enable:

- **Intelligent Learning**: ML model management and automated pattern recognition
- **Evolutionary Optimization**: OpenEvolve integration for continuous code improvement
- **Advanced Analytics**: Real-time performance monitoring and predictive insights
- **Scalable Architecture**: Support for millions of learning events and high-throughput analytics

## Pre-Implementation Checklist

### ✅ Prerequisites Verification

- [ ] PostgreSQL 13+ installed with required extensions
- [ ] Existing 7-module schema documented and backed up
- [ ] Development environment set up for testing
- [ ] Stakeholder approval for schema changes
- [ ] Performance baseline measurements taken

### ✅ Required PostgreSQL Extensions

```sql
-- Verify and install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
```

### ✅ Resource Requirements

| Environment | CPU | Memory | Storage | Network |
|-------------|-----|--------|---------|---------|
| Development | 4 cores | 8GB RAM | 100GB SSD | 1Gbps |
| Staging | 8 cores | 16GB RAM | 500GB SSD | 1Gbps |
| Production | 16 cores | 32GB RAM | 2TB SSD | 10Gbps |

## Implementation Phases

### Phase 1: Core Infrastructure (Weeks 1-2)

#### Week 1: Foundation Setup

**Day 1-2: Environment Preparation**

1. **Backup Current System**
   ```bash
   # Create full database backup
   pg_dump -h localhost -U postgres -d graph_sitter > backup_$(date +%Y%m%d).sql
   
   # Backup critical configuration
   cp postgresql.conf postgresql.conf.backup
   cp pg_hba.conf pg_hba.conf.backup
   ```

2. **Install Enhanced Schema**
   ```bash
   # Apply schema files in order
   psql -d graph_sitter -f database/enhanced_schema/01_learning_models.sql
   psql -d graph_sitter -f database/enhanced_schema/02_openevolve_integration.sql
   psql -d graph_sitter -f database/enhanced_schema/03_pattern_recognition.sql
   psql -d graph_sitter -f database/enhanced_schema/04_analytics_performance.sql
   psql -d graph_sitter -f database/enhanced_schema/05_integration_migration.sql
   ```

3. **Validate Installation**
   ```sql
   -- Check schema integrity
   SELECT * FROM validate_schema_integrity();
   
   -- Verify all tables created
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name LIKE '%ml_%' OR table_name LIKE '%evolution_%';
   ```

**Day 3-4: Basic Configuration**

1. **Configure Partitioning**
   ```sql
   -- Create initial partitions for next 6 months
   SELECT create_monthly_partition('learning_events', '2025-01-01'::DATE);
   SELECT create_monthly_partition('learning_events', '2025-02-01'::DATE);
   SELECT create_monthly_partition('learning_events', '2025-03-01'::DATE);
   SELECT create_monthly_partition('learning_events', '2025-04-01'::DATE);
   SELECT create_monthly_partition('learning_events', '2025-05-01'::DATE);
   SELECT create_monthly_partition('learning_events', '2025-06-01'::DATE);
   ```

2. **Set Up Data Retention Policies**
   ```sql
   INSERT INTO data_retention_policies (table_name, retention_period, archive_strategy) VALUES
   ('learning_events', '2 years', 'archive_to_s3'),
   ('system_performance_metrics', '90 days', 'delete'),
   ('query_performance_logs', '30 days', 'summarize'),
   ('evolution_individuals', '1 year', 'compress');
   ```

**Day 5: Testing and Validation**

1. **Insert Test Data**
   ```sql
   -- Test ML model creation
   INSERT INTO ml_models (name, version, model_type, framework) 
   VALUES ('test_model', 'v1.0', 'pattern_recognition', 'scikit-learn');
   
   -- Test learning event insertion
   INSERT INTO learning_events (event_type, source_system, event_data)
   VALUES ('model_prediction', 'test_system', '{"test": true}');
   
   -- Verify data insertion
   SELECT COUNT(*) FROM ml_models;
   SELECT COUNT(*) FROM learning_events;
   ```

#### Week 2: Integration Setup

**Day 1-2: Git Integration**

1. **Create Git Operation Tracking**
   ```python
   # Example Python integration code
   def track_git_operation(operation_id, operation_type, repo_id, learning_event_id):
       query = """
       INSERT INTO git_operation_learning_events 
       (git_operation_id, operation_type, repository_id, learning_event_id)
       VALUES (%s, %s, %s, %s)
       """
       cursor.execute(query, (operation_id, operation_type, repo_id, learning_event_id))
   ```

2. **Test Git Integration**
   ```sql
   -- Simulate git operations
   INSERT INTO git_operation_learning_events 
   (git_operation_id, operation_type, repository_id, learning_event_id)
   SELECT 'test_commit_' || generate_series(1,100), 'commit', 'test_repo', id
   FROM learning_events LIMIT 100;
   ```

**Day 3-4: User Session Integration**

1. **Implement Session Tracking**
   ```python
   def track_user_session(session_id, user_id, platform, learning_event_id):
       query = """
       INSERT INTO user_session_learning_events 
       (session_id, user_id, platform, learning_event_id)
       VALUES (%s, %s, %s, %s)
       """
       cursor.execute(query, (session_id, user_id, platform, learning_event_id))
   ```

**Day 5: Performance Testing**

1. **Load Testing**
   ```bash
   # Use pgbench for load testing
   pgbench -i -s 10 graph_sitter
   pgbench -c 10 -j 2 -t 1000 graph_sitter
   ```

2. **Query Performance Validation**
   ```sql
   -- Test common query patterns
   EXPLAIN ANALYZE SELECT * FROM daily_learning_metrics 
   WHERE date > CURRENT_DATE - INTERVAL '7 days';
   
   -- Check index usage
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
   FROM pg_stat_user_indexes ORDER BY idx_scan DESC;
   ```

### Phase 2: OpenEvolve Integration (Weeks 3-4)

#### Week 3: Evolution Infrastructure

**Day 1-2: Experiment Setup**

1. **Create Evolution Experiment Templates**
   ```sql
   INSERT INTO evolution_experiment_templates 
   (name, description, problem_category, template_config) VALUES
   ('code_optimization', 'General code optimization template', 'optimization',
    '{"population_size": 50, "max_generations": 100, "mutation_rate": 0.1}'),
   ('algorithm_design', 'Algorithm design and improvement', 'algorithm_design',
    '{"population_size": 30, "max_generations": 200, "mutation_rate": 0.15}');
   ```

2. **Test Experiment Creation**
   ```sql
   INSERT INTO evolution_experiments 
   (name, description, problem_definition, objective_function)
   VALUES ('test_optimization', 'Test optimization experiment',
           '{"problem": "optimize function performance"}',
           '{"metrics": ["execution_time", "memory_usage"]}');
   ```

**Day 3-4: LLM Integration**

1. **Set Up LLM Interaction Logging**
   ```python
   def log_llm_interaction(experiment_id, interaction_type, prompt, response, cost):
       query = """
       INSERT INTO llm_interactions 
       (experiment_id, interaction_type, llm_model, prompt_text, response_text, cost_usd)
       VALUES (%s, %s, %s, %s, %s, %s)
       """
       cursor.execute(query, (experiment_id, interaction_type, 'gpt-4', prompt, response, cost))
   ```

**Day 5: Evolution Testing**

1. **Simulate Evolution Process**
   ```sql
   -- Create test generation
   INSERT INTO evolution_generations (experiment_id, generation_number)
   VALUES ('experiment-uuid', 1);
   
   -- Create test individuals
   INSERT INTO evolution_individuals 
   (generation_id, experiment_id, individual_index, genotype, fitness_score)
   VALUES ('generation-uuid', 'experiment-uuid', 1, '{"code": "test"}', 0.85);
   ```

#### Week 4: Code Evaluation System

**Day 1-3: Evaluation Framework**

1. **Implement Code Evaluation**
   ```python
   def evaluate_code(individual_id, code, test_suite):
       # Run code evaluation
       results = run_evaluation(code, test_suite)
       
       # Store results
       query = """
       INSERT INTO code_evaluations 
       (individual_id, evaluation_type, test_cases_passed, test_cases_total, 
        execution_time_ms, correctness_score)
       VALUES (%s, %s, %s, %s, %s, %s)
       """
       cursor.execute(query, (individual_id, 'functional', 
                             results['passed'], results['total'],
                             results['time'], results['score']))
   ```

**Day 4-5: Integration Testing**

1. **End-to-End Evolution Test**
   ```python
   # Complete evolution workflow test
   experiment_id = create_experiment("test_evolution")
   for generation in range(5):
       gen_id = create_generation(experiment_id, generation)
       for individual in range(10):
           ind_id = create_individual(gen_id, generate_code())
           evaluate_individual(ind_id)
   ```

### Phase 3: Pattern Recognition (Weeks 5-6)

#### Week 5: Pattern Detection System

**Day 1-2: Pattern Definition**

1. **Create Pattern Templates**
   ```sql
   INSERT INTO identified_patterns 
   (pattern_type, pattern_name, pattern_description, detection_algorithm, confidence_score)
   VALUES 
   ('code_smell', 'long_method', 'Methods with excessive lines of code', 'line_count_analyzer', 0.90),
   ('performance_bottleneck', 'n_plus_one_query', 'Database N+1 query pattern', 'query_analyzer', 0.95),
   ('security_vulnerability', 'sql_injection', 'Potential SQL injection vulnerability', 'security_scanner', 0.85);
   ```

**Day 3-4: Pattern Detection Implementation**

1. **Implement Pattern Detection**
   ```python
   def detect_patterns(source_type, source_id, content):
       patterns = []
       
       # Example: Long method detection
       if source_type == 'code_file':
           lines = content.split('\n')
           if len(lines) > 50:  # Threshold for long method
               patterns.append({
                   'pattern_id': 'long_method_pattern_id',
                   'confidence': 0.90,
                   'location': {'line_count': len(lines)}
               })
       
       # Store detected patterns
       for pattern in patterns:
           store_pattern_occurrence(pattern, source_type, source_id)
   ```

**Day 5: Pattern Analytics**

1. **Create Pattern Analytics Dashboard**
   ```sql
   -- Pattern frequency analysis
   SELECT p.pattern_type, p.severity_level, COUNT(po.id) as occurrences
   FROM identified_patterns p
   JOIN pattern_occurrences po ON p.id = po.pattern_id
   WHERE po.detection_timestamp > NOW() - INTERVAL '30 days'
   GROUP BY p.pattern_type, p.severity_level
   ORDER BY occurrences DESC;
   ```

#### Week 6: Prediction and Recommendation System

**Day 1-3: Prediction Engine**

1. **Implement Prediction System**
   ```python
   def make_prediction(model_id, target_type, target_id, features):
       # Generate prediction
       prediction = model.predict(features)
       
       # Store prediction
       query = """
       INSERT INTO predictions 
       (model_id, prediction_type, target_entity_type, target_entity_id, 
        predicted_value, confidence_interval, input_features)
       VALUES (%s, %s, %s, %s, %s, %s, %s)
       """
       cursor.execute(query, (model_id, 'bug_likelihood', target_type, target_id,
                             json.dumps(prediction), json.dumps(confidence),
                             json.dumps(features)))
   ```

**Day 4-5: Recommendation Engine**

1. **Create Recommendation System**
   ```python
   def generate_recommendations(pattern_id, prediction_id):
       # Generate recommendations based on patterns and predictions
       recommendations = analyze_and_recommend(pattern_id, prediction_id)
       
       for rec in recommendations:
           query = """
           INSERT INTO recommendations 
           (recommendation_type, title, description, confidence_score, 
            source_pattern_id, source_prediction_id)
           VALUES (%s, %s, %s, %s, %s, %s)
           """
           cursor.execute(query, (rec['type'], rec['title'], rec['description'],
                                 rec['confidence'], pattern_id, prediction_id))
   ```

### Phase 4: Analytics and Optimization (Weeks 7-8)

#### Week 7: Analytics Infrastructure

**Day 1-2: Materialized Views Setup**

1. **Create Analytics Views**
   ```sql
   -- Refresh materialized views
   REFRESH MATERIALIZED VIEW daily_learning_metrics;
   REFRESH MATERIALIZED VIEW hourly_performance_summary;
   REFRESH MATERIALIZED VIEW query_performance_summary;
   
   -- Set up automatic refresh
   SELECT cron.schedule('refresh-analytics', '*/15 * * * *', 
          'REFRESH MATERIALIZED VIEW CONCURRENTLY daily_learning_metrics;');
   ```

**Day 3-4: Dashboard Implementation**

1. **Create Analytics Dashboard Queries**
   ```sql
   -- System health dashboard
   CREATE VIEW system_health_dashboard AS
   SELECT 
       'Learning Events' as component,
       COUNT(*) as events_last_hour,
       AVG(processing_time_ms) as avg_processing_time
   FROM learning_events 
   WHERE timestamp > NOW() - INTERVAL '1 hour'
   UNION ALL
   SELECT 
       'Pattern Detection' as component,
       COUNT(*) as events_last_hour,
       AVG(confidence_score * 100) as avg_confidence
   FROM pattern_occurrences 
   WHERE detection_timestamp > NOW() - INTERVAL '1 hour';
   ```

**Day 5: Performance Optimization**

1. **Query Optimization**
   ```sql
   -- Analyze slow queries
   SELECT query, mean_time, calls, total_time
   FROM pg_stat_statements
   WHERE mean_time > 1000  -- Queries taking more than 1 second
   ORDER BY mean_time DESC;
   
   -- Add missing indexes
   CREATE INDEX CONCURRENTLY idx_learning_events_user_timestamp 
   ON learning_events(user_id, timestamp) 
   WHERE user_id IS NOT NULL;
   ```

#### Week 8: Production Readiness

**Day 1-2: Monitoring Setup**

1. **Configure Monitoring**
   ```sql
   -- Set up health checks
   INSERT INTO system_health_checks 
   (check_name, check_category, check_frequency) VALUES
   ('database_connections', 'database', '1 minute'),
   ('learning_events_lag', 'analytics', '5 minutes'),
   ('model_prediction_accuracy', 'ml_pipeline', '1 hour');
   ```

**Day 3-4: Load Testing**

1. **Production Load Testing**
   ```bash
   # Simulate high-volume learning events
   python scripts/load_test_learning_events.py --events-per-second 1000 --duration 3600
   
   # Test evolution experiments under load
   python scripts/load_test_evolution.py --concurrent-experiments 10
   ```

**Day 5: Go-Live Preparation**

1. **Final Validation**
   ```sql
   -- Comprehensive system check
   SELECT * FROM validate_schema_integrity();
   SELECT * FROM detect_performance_anomalies();
   
   -- Data quality validation
   SELECT table_name, avg_quality_score 
   FROM (
       SELECT table_name, AVG(quality_score) as avg_quality_score
       FROM data_quality_checks 
       WHERE check_timestamp > NOW() - INTERVAL '24 hours'
       GROUP BY table_name
   ) q WHERE avg_quality_score < 95.0;
   ```

## Post-Implementation Tasks

### Immediate (Week 9)

1. **Production Deployment**
   - Deploy to production environment
   - Configure monitoring and alerting
   - Set up backup and recovery procedures

2. **User Training**
   - Train development team on new schema
   - Provide documentation and examples
   - Set up support channels

3. **Performance Monitoring**
   - Monitor system performance for first week
   - Adjust configurations based on real usage
   - Optimize queries as needed

### Short-term (Weeks 10-12)

1. **Feature Integration**
   - Integrate with existing applications
   - Develop analytics dashboards
   - Implement automated reporting

2. **Optimization**
   - Fine-tune performance based on usage patterns
   - Optimize data retention policies
   - Adjust partitioning strategies

### Long-term (Months 4-6)

1. **Advanced Features**
   - Implement advanced ML models
   - Add real-time analytics
   - Develop predictive maintenance

2. **Scaling**
   - Plan for horizontal scaling
   - Implement read replicas
   - Optimize for global distribution

## Success Metrics

### Technical Metrics

- [ ] Learning event processing: <10ms p95
- [ ] Pattern detection queries: <100ms p95
- [ ] Analytics aggregations: <5s p95
- [ ] System uptime: >99.9%
- [ ] Data quality score: >95%

### Business Metrics

- [ ] 50% reduction in manual error resolution
- [ ] 30% improvement in task completion times
- [ ] 80% accuracy in predictions and recommendations
- [ ] 95% automated error detection rate

### User Adoption Metrics

- [ ] 90% of development team using new features
- [ ] 100+ evolution experiments completed
- [ ] 1000+ patterns detected and resolved
- [ ] 10,000+ learning events processed daily

## Troubleshooting Guide

### Common Issues

1. **Partition Creation Failures**
   ```sql
   -- Manual partition creation
   SELECT create_monthly_partition('learning_events', CURRENT_DATE);
   ```

2. **Performance Degradation**
   ```sql
   -- Check for missing statistics
   ANALYZE learning_events;
   ANALYZE system_performance_metrics;
   
   -- Rebuild indexes if needed
   REINDEX INDEX CONCURRENTLY idx_learning_events_type_timestamp;
   ```

3. **Data Quality Issues**
   ```sql
   -- Check data quality
   SELECT * FROM data_quality_checks WHERE status = 'failed';
   
   -- Fix data quality issues
   UPDATE identified_patterns SET confidence_score = 0.5 
   WHERE confidence_score > 1.0;
   ```

### Emergency Procedures

1. **Schema Rollback**
   ```sql
   SELECT rollback_schema_version('2024.12.001');
   ```

2. **Performance Emergency**
   ```sql
   -- Disable non-critical scheduled jobs
   SELECT cron.unschedule('refresh-analytics-views');
   
   -- Drop expensive indexes temporarily
   DROP INDEX CONCURRENTLY idx_learning_events_data;
   ```

## Support and Maintenance

### Daily Tasks
- Monitor system health dashboard
- Check data quality reports
- Review performance metrics

### Weekly Tasks
- Analyze query performance trends
- Review capacity planning metrics
- Update materialized views manually if needed

### Monthly Tasks
- Create new partitions for next month
- Review and update data retention policies
- Analyze cost and resource utilization

## Conclusion

This implementation guide provides a comprehensive roadmap for deploying the enhanced database schema. Following this phased approach ensures minimal risk while delivering maximum value from the continuous learning and analytics capabilities.

The enhanced schema will transform the graph-sitter system from a traditional development tool into an intelligent, self-improving platform that continuously learns and optimizes based on usage patterns and historical data.

