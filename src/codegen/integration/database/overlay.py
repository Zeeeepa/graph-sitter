"""
Database Overlay System

Provides database overlay functionality for tracking evaluations, performance metrics,
and effectiveness analysis in the OpenEvolve integration system.
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import sqlite3
import aiosqlite

from .models import (
    EvaluationSession,
    ComponentEvaluation,
    EvaluationStep,
    OutcomeCorrelation,
    PerformanceAnalysis
)


class DatabaseOverlay:
    """
    Database overlay system for OpenEvolve integration.
    
    Provides persistent storage and retrieval of evaluation data, performance metrics,
    and effectiveness analysis results.
    """
    
    def __init__(self, database_url: Optional[str] = None, schema_path: Optional[str] = None):
        """
        Initialize the database overlay.
        
        Args:
            database_url: Database connection URL (defaults to SQLite)
            schema_path: Path to SQL schema file
        """
        self.database_url = database_url or "sqlite:///openevolve_evaluations.db"
        self.schema_path = schema_path
        self.logger = logging.getLogger(__name__)
        
        # Extract database type and path
        if self.database_url.startswith("sqlite:///"):
            self.db_type = "sqlite"
            self.db_path = self.database_url.replace("sqlite:///", "")
        else:
            raise ValueError(f"Unsupported database URL: {database_url}")
        
        self.connection = None
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize the database overlay and create tables."""
        if self.is_initialized:
            return
        
        try:
            # Create database connection
            if self.db_type == "sqlite":
                self.connection = await aiosqlite.connect(self.db_path)
                await self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Create tables from schema
            await self._create_tables()
            
            self.is_initialized = True
            self.logger.info("Database overlay initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize database overlay: %s", str(e))
            raise
    
    async def _create_tables(self) -> None:
        """Create database tables from schema."""
        try:
            # SQLite-compatible schema (simplified from PostgreSQL)
            schema_sql = """
            -- Evaluation sessions
            CREATE TABLE IF NOT EXISTS evaluation_sessions (
                id TEXT PRIMARY KEY,
                session_name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                metadata TEXT DEFAULT '{}'
            );
            
            -- Component evaluations
            CREATE TABLE IF NOT EXISTS component_evaluations (
                id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
                component_type TEXT NOT NULL,
                component_name TEXT NOT NULL,
                evaluation_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                effectiveness_score REAL,
                performance_metrics TEXT DEFAULT '{}',
                execution_time_ms INTEGER,
                memory_usage_mb REAL,
                success_rate REAL,
                error_count INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            );
            
            -- Evaluation steps
            CREATE TABLE IF NOT EXISTS evaluation_steps (
                id TEXT PRIMARY KEY,
                component_evaluation_id TEXT REFERENCES component_evaluations(id) ON DELETE CASCADE,
                step_number INTEGER NOT NULL,
                step_name TEXT NOT NULL,
                step_description TEXT,
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                duration_ms INTEGER,
                status TEXT DEFAULT 'pending',
                input_data TEXT DEFAULT '{}',
                output_data TEXT DEFAULT '{}',
                error_message TEXT,
                effectiveness_contribution REAL
            );
            
            -- Outcome correlations
            CREATE TABLE IF NOT EXISTS outcome_correlations (
                id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
                component_type TEXT NOT NULL,
                expected_outcome TEXT NOT NULL,
                actual_outcome TEXT NOT NULL,
                correlation_score REAL,
                effectiveness_impact REAL,
                analysis_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                analysis_method TEXT,
                confidence_level REAL,
                metadata TEXT DEFAULT '{}'
            );
            
            -- Performance analyses
            CREATE TABLE IF NOT EXISTS performance_analyses (
                id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
                component_type TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                baseline_metrics TEXT NOT NULL,
                current_metrics TEXT NOT NULL,
                improvement_percentage REAL,
                optimization_suggestions TEXT DEFAULT '[]',
                priority_level INTEGER DEFAULT 3,
                analysis_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                analyst_agent TEXT,
                metadata TEXT DEFAULT '{}'
            );
            
            -- Agent executions
            CREATE TABLE IF NOT EXISTS agent_executions (
                id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
                agent_type TEXT NOT NULL,
                agent_instance_id TEXT,
                execution_start TEXT DEFAULT CURRENT_TIMESTAMP,
                execution_end TEXT,
                execution_status TEXT DEFAULT 'running',
                input_parameters TEXT DEFAULT '{}',
                output_results TEXT DEFAULT '{}',
                resource_usage TEXT DEFAULT '{}',
                error_details TEXT,
                parent_execution_id TEXT REFERENCES agent_executions(id)
            );
            
            -- Evaluation metrics
            CREATE TABLE IF NOT EXISTS evaluation_metrics (
                id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
                metric_name TEXT NOT NULL,
                metric_category TEXT NOT NULL,
                metric_value REAL,
                metric_unit TEXT,
                aggregation_period TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                component_filter TEXT,
                metadata TEXT DEFAULT '{}'
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_component_evaluations_session_id 
                ON component_evaluations(session_id);
            CREATE INDEX IF NOT EXISTS idx_component_evaluations_component_type 
                ON component_evaluations(component_type);
            CREATE INDEX IF NOT EXISTS idx_evaluation_steps_component_evaluation_id 
                ON evaluation_steps(component_evaluation_id);
            CREATE INDEX IF NOT EXISTS idx_outcome_correlations_session_id 
                ON outcome_correlations(session_id);
            CREATE INDEX IF NOT EXISTS idx_performance_analyses_session_id 
                ON performance_analyses(session_id);
            """
            
            # Execute schema creation
            await self.connection.executescript(schema_sql)
            await self.connection.commit()
            
            self.logger.info("Database tables created successfully")
            
        except Exception as e:
            self.logger.error("Failed to create database tables: %s", str(e))
            raise
    
    async def create_session(
        self, 
        session_name: str, 
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new evaluation session."""
        session_id = str(uuid.uuid4())
        
        try:
            await self.connection.execute(
                """
                INSERT INTO evaluation_sessions 
                (id, session_name, description, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    session_name,
                    description,
                    json.dumps(metadata or {})
                )
            )
            await self.connection.commit()
            
            self.logger.info("Created evaluation session: %s", session_id)
            return session_id
            
        except Exception as e:
            self.logger.error("Failed to create evaluation session: %s", str(e))
            raise
    
    async def store_component_evaluation(
        self,
        session_id: str,
        component_type: str,
        component_name: str,
        effectiveness_score: float,
        performance_metrics: Dict[str, Any],
        execution_time_ms: int,
        success_rate: float,
        error_count: int = 0,
        memory_usage_mb: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a component evaluation result."""
        evaluation_id = str(uuid.uuid4())
        
        try:
            await self.connection.execute(
                """
                INSERT INTO component_evaluations 
                (id, session_id, component_type, component_name, effectiveness_score,
                 performance_metrics, execution_time_ms, memory_usage_mb, success_rate,
                 error_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evaluation_id,
                    session_id,
                    component_type,
                    component_name,
                    effectiveness_score,
                    json.dumps(performance_metrics),
                    execution_time_ms,
                    memory_usage_mb,
                    success_rate,
                    error_count,
                    json.dumps(metadata or {})
                )
            )
            await self.connection.commit()
            
            self.logger.debug("Stored component evaluation: %s", evaluation_id)
            return evaluation_id
            
        except Exception as e:
            self.logger.error("Failed to store component evaluation: %s", str(e))
            raise
    
    async def store_evaluation_step(
        self,
        component_evaluation_id: Optional[str],
        step_number: int,
        step_name: str,
        step_description: str = "",
        duration_ms: int = 0,
        status: str = "completed",
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        effectiveness_contribution: float = 0.0
    ) -> str:
        """Store an evaluation step result."""
        step_id = str(uuid.uuid4())
        
        try:
            # If component_evaluation_id is None, get the latest one
            if component_evaluation_id is None:
                cursor = await self.connection.execute(
                    "SELECT id FROM component_evaluations ORDER BY evaluation_timestamp DESC LIMIT 1"
                )
                row = await cursor.fetchone()
                if row:
                    component_evaluation_id = row[0]
                else:
                    raise ValueError("No component evaluation found to associate step with")
            
            await self.connection.execute(
                """
                INSERT INTO evaluation_steps 
                (id, component_evaluation_id, step_number, step_name, step_description,
                 duration_ms, status, input_data, output_data, error_message,
                 effectiveness_contribution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step_id,
                    component_evaluation_id,
                    step_number,
                    step_name,
                    step_description,
                    duration_ms,
                    status,
                    json.dumps(input_data or {}),
                    json.dumps(output_data or {}),
                    error_message,
                    effectiveness_contribution
                )
            )
            await self.connection.commit()
            
            self.logger.debug("Stored evaluation step: %s", step_id)
            return step_id
            
        except Exception as e:
            self.logger.error("Failed to store evaluation step: %s", str(e))
            raise
    
    async def store_outcome_correlation(
        self,
        session_id: str,
        component_type: str,
        expected_outcome: Dict[str, Any],
        actual_outcome: Dict[str, Any],
        correlation_score: float,
        effectiveness_impact: float,
        analysis_method: str = "statistical",
        confidence_level: float = 0.95,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store an outcome correlation analysis."""
        correlation_id = str(uuid.uuid4())
        
        try:
            await self.connection.execute(
                """
                INSERT INTO outcome_correlations 
                (id, session_id, component_type, expected_outcome, actual_outcome,
                 correlation_score, effectiveness_impact, analysis_method,
                 confidence_level, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    correlation_id,
                    session_id,
                    component_type,
                    json.dumps(expected_outcome),
                    json.dumps(actual_outcome),
                    correlation_score,
                    effectiveness_impact,
                    analysis_method,
                    confidence_level,
                    json.dumps(metadata or {})
                )
            )
            await self.connection.commit()
            
            self.logger.debug("Stored outcome correlation: %s", correlation_id)
            return correlation_id
            
        except Exception as e:
            self.logger.error("Failed to store outcome correlation: %s", str(e))
            raise
    
    async def store_performance_analysis(
        self,
        session_id: str,
        component_type: str,
        analysis_type: str,
        baseline_metrics: Dict[str, Any],
        current_metrics: Dict[str, Any],
        improvement_percentage: float,
        optimization_suggestions: List[str],
        priority_level: int = 3,
        analyst_agent: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a performance analysis result."""
        analysis_id = str(uuid.uuid4())
        
        try:
            await self.connection.execute(
                """
                INSERT INTO performance_analyses 
                (id, session_id, component_type, analysis_type, baseline_metrics,
                 current_metrics, improvement_percentage, optimization_suggestions,
                 priority_level, analyst_agent, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    session_id,
                    component_type,
                    analysis_type,
                    json.dumps(baseline_metrics),
                    json.dumps(current_metrics),
                    improvement_percentage,
                    json.dumps(optimization_suggestions),
                    priority_level,
                    analyst_agent,
                    json.dumps(metadata or {})
                )
            )
            await self.connection.commit()
            
            self.logger.debug("Stored performance analysis: %s", analysis_id)
            return analysis_id
            
        except Exception as e:
            self.logger.error("Failed to store performance analysis: %s", str(e))
            raise
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of an evaluation session."""
        try:
            # Get session info
            cursor = await self.connection.execute(
                "SELECT * FROM evaluation_sessions WHERE id = ?",
                (session_id,)
            )
            session_row = await cursor.fetchone()
            
            if not session_row:
                raise ValueError(f"Session not found: {session_id}")
            
            # Get evaluation counts and averages
            cursor = await self.connection.execute(
                """
                SELECT 
                    component_type,
                    COUNT(*) as evaluation_count,
                    AVG(effectiveness_score) as avg_effectiveness,
                    AVG(execution_time_ms) as avg_execution_time,
                    AVG(success_rate) as avg_success_rate
                FROM component_evaluations 
                WHERE session_id = ?
                GROUP BY component_type
                """,
                (session_id,)
            )
            component_stats = await cursor.fetchall()
            
            # Get correlation count
            cursor = await self.connection.execute(
                "SELECT COUNT(*) FROM outcome_correlations WHERE session_id = ?",
                (session_id,)
            )
            correlation_count = (await cursor.fetchone())[0]
            
            # Get performance analysis count
            cursor = await self.connection.execute(
                "SELECT COUNT(*) FROM performance_analyses WHERE session_id = ?",
                (session_id,)
            )
            analysis_count = (await cursor.fetchone())[0]
            
            return {
                'session_id': session_id,
                'session_name': session_row[1],
                'description': session_row[2],
                'created_at': session_row[3],
                'status': session_row[5],
                'component_statistics': [
                    {
                        'component_type': row[0],
                        'evaluation_count': row[1],
                        'avg_effectiveness': row[2],
                        'avg_execution_time_ms': row[3],
                        'avg_success_rate': row[4]
                    }
                    for row in component_stats
                ],
                'correlation_count': correlation_count,
                'analysis_count': analysis_count
            }
            
        except Exception as e:
            self.logger.error("Failed to get session summary: %s", str(e))
            raise
    
    async def get_component_evaluations(
        self, 
        session_id: str, 
        component_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get component evaluations for a session."""
        try:
            if component_type:
                cursor = await self.connection.execute(
                    """
                    SELECT * FROM component_evaluations 
                    WHERE session_id = ? AND component_type = ?
                    ORDER BY evaluation_timestamp DESC
                    """,
                    (session_id, component_type)
                )
            else:
                cursor = await self.connection.execute(
                    """
                    SELECT * FROM component_evaluations 
                    WHERE session_id = ?
                    ORDER BY evaluation_timestamp DESC
                    """,
                    (session_id,)
                )
            
            rows = await cursor.fetchall()
            
            evaluations = []
            for row in rows:
                evaluations.append({
                    'id': row[0],
                    'session_id': row[1],
                    'component_type': row[2],
                    'component_name': row[3],
                    'evaluation_timestamp': row[4],
                    'effectiveness_score': row[5],
                    'performance_metrics': json.loads(row[6]) if row[6] else {},
                    'execution_time_ms': row[7],
                    'memory_usage_mb': row[8],
                    'success_rate': row[9],
                    'error_count': row[10],
                    'metadata': json.loads(row[11]) if row[11] else {}
                })
            
            return evaluations
            
        except Exception as e:
            self.logger.error("Failed to get component evaluations: %s", str(e))
            raise
    
    async def cleanup(self) -> None:
        """Cleanup database connections."""
        try:
            if self.connection:
                await self.connection.close()
            
            self.is_initialized = False
            self.logger.info("Database overlay cleanup completed")
            
        except Exception as e:
            self.logger.error("Error during database cleanup: %s", str(e))
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

