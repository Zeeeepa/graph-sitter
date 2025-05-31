"""Database schema creation for autogenlib integration."""

from typing import Any, Dict


def create_autogenlib_tables() -> Dict[str, str]:
    """Return SQL statements to create autogenlib tables."""
    
    tables = {}
    
    # Generation history table
    tables["generation_history"] = """
    CREATE TABLE IF NOT EXISTS generation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_name TEXT NOT NULL,
        function_name TEXT,
        description TEXT NOT NULL,
        generated_code TEXT NOT NULL,
        context_used TEXT, -- JSON string
        success BOOLEAN NOT NULL,
        error_message TEXT,
        generation_time REAL NOT NULL,
        model_used TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Generation patterns table
    tables["generation_patterns"] = """
    CREATE TABLE IF NOT EXISTS generation_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_name TEXT NOT NULL UNIQUE,
        pattern_type TEXT NOT NULL,
        description_keywords TEXT NOT NULL, -- JSON array
        code_template TEXT NOT NULL,
        context_requirements TEXT, -- JSON object
        success_count INTEGER DEFAULT 1,
        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Generation cache table
    tables["generation_cache"] = """
    CREATE TABLE IF NOT EXISTS generation_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cache_key TEXT NOT NULL UNIQUE,
        module_name TEXT NOT NULL,
        function_name TEXT,
        description_hash TEXT NOT NULL,
        context_hash TEXT NOT NULL,
        generated_code TEXT NOT NULL,
        hit_count INTEGER DEFAULT 0,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    );
    """
    
    # Generation metrics table
    tables["generation_metrics"] = """
    CREATE TABLE IF NOT EXISTS generation_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL UNIQUE,
        total_generations INTEGER DEFAULT 0,
        successful_generations INTEGER DEFAULT 0,
        failed_generations INTEGER DEFAULT 0,
        average_generation_time REAL DEFAULT 0.0,
        cache_hits INTEGER DEFAULT 0,
        cache_misses INTEGER DEFAULT 0,
        most_common_patterns TEXT, -- JSON array
        error_types TEXT -- JSON object
    );
    """
    
    return tables


def create_autogenlib_indexes() -> Dict[str, str]:
    """Return SQL statements to create indexes for autogenlib tables."""
    
    indexes = {}
    
    # Indexes for generation_history
    indexes["idx_generation_history_module"] = """
    CREATE INDEX IF NOT EXISTS idx_generation_history_module 
    ON generation_history(module_name);
    """
    
    indexes["idx_generation_history_created_at"] = """
    CREATE INDEX IF NOT EXISTS idx_generation_history_created_at 
    ON generation_history(created_at);
    """
    
    indexes["idx_generation_history_success"] = """
    CREATE INDEX IF NOT EXISTS idx_generation_history_success 
    ON generation_history(success);
    """
    
    # Indexes for generation_patterns
    indexes["idx_generation_patterns_type"] = """
    CREATE INDEX IF NOT EXISTS idx_generation_patterns_type 
    ON generation_patterns(pattern_type);
    """
    
    indexes["idx_generation_patterns_last_used"] = """
    CREATE INDEX IF NOT EXISTS idx_generation_patterns_last_used 
    ON generation_patterns(last_used);
    """
    
    # Indexes for generation_cache
    indexes["idx_generation_cache_module"] = """
    CREATE INDEX IF NOT EXISTS idx_generation_cache_module 
    ON generation_cache(module_name);
    """
    
    indexes["idx_generation_cache_last_accessed"] = """
    CREATE INDEX IF NOT EXISTS idx_generation_cache_last_accessed 
    ON generation_cache(last_accessed);
    """
    
    indexes["idx_generation_cache_expires_at"] = """
    CREATE INDEX IF NOT EXISTS idx_generation_cache_expires_at 
    ON generation_cache(expires_at);
    """
    
    return indexes


def create_autogenlib_views() -> Dict[str, str]:
    """Return SQL statements to create views for autogenlib analytics."""
    
    views = {}
    
    # View for generation statistics
    views["generation_stats"] = """
    CREATE VIEW IF NOT EXISTS generation_stats AS
    SELECT 
        DATE(created_at) as date,
        COUNT(*) as total_generations,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_generations,
        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_generations,
        AVG(generation_time) as avg_generation_time,
        COUNT(DISTINCT module_name) as unique_modules
    FROM generation_history
    GROUP BY DATE(created_at)
    ORDER BY date DESC;
    """
    
    # View for popular patterns
    views["popular_patterns"] = """
    CREATE VIEW IF NOT EXISTS popular_patterns AS
    SELECT 
        pattern_name,
        pattern_type,
        success_count,
        last_used,
        ROUND(julianday('now') - julianday(last_used)) as days_since_last_use
    FROM generation_patterns
    ORDER BY success_count DESC, last_used DESC;
    """
    
    # View for cache performance
    views["cache_performance"] = """
    CREATE VIEW IF NOT EXISTS cache_performance AS
    SELECT 
        module_name,
        COUNT(*) as cache_entries,
        SUM(hit_count) as total_hits,
        AVG(hit_count) as avg_hits_per_entry,
        MAX(last_accessed) as last_cache_hit
    FROM generation_cache
    GROUP BY module_name
    ORDER BY total_hits DESC;
    """
    
    return views


def drop_autogenlib_tables() -> Dict[str, str]:
    """Return SQL statements to drop autogenlib tables."""
    
    drop_statements = {}
    
    # Drop views first (they depend on tables)
    drop_statements["drop_views"] = """
    DROP VIEW IF EXISTS generation_stats;
    DROP VIEW IF EXISTS popular_patterns;
    DROP VIEW IF EXISTS cache_performance;
    """
    
    # Drop tables
    drop_statements["drop_tables"] = """
    DROP TABLE IF EXISTS generation_metrics;
    DROP TABLE IF EXISTS generation_cache;
    DROP TABLE IF EXISTS generation_patterns;
    DROP TABLE IF EXISTS generation_history;
    """
    
    return drop_statements


def get_migration_scripts() -> Dict[str, str]:
    """Return migration scripts for database schema updates."""
    
    migrations = {}
    
    # Migration to add new columns (example)
    migrations["add_model_version"] = """
    ALTER TABLE generation_history 
    ADD COLUMN model_version TEXT DEFAULT 'unknown';
    """
    
    migrations["add_context_size"] = """
    ALTER TABLE generation_history 
    ADD COLUMN context_size INTEGER DEFAULT 0;
    """
    
    return migrations

