"""
Database Manager for OpenEvolve Integration

This module provides comprehensive database schema and management for storing
step contexts, decision trees, performance metrics, and learning data.
"""

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

from graph_sitter.shared.logging import get_logger

logger = get_logger(__name__)


class OpenEvolveDatabase:
    """
    Database manager for OpenEvolve integration with comprehensive schema
    for step contexts, decision trees, and performance metrics.
    """
    
    def __init__(self, database_path: str = None):
        """
        Initialize the database manager.
        
        Args:
            database_path: Path to the SQLite database file
        """
        self.database_path = database_path or "openevolve_integration.db"
        self.connection_pool = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the database schema."""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.database_path) as db:
            await self._create_schema(db)
            await db.commit()
        
        self._initialized = True
        logger.info(f"Database initialized at {self.database_path}")
    
    async def _create_schema(self, db: aiosqlite.Connection) -> None:
        """Create the database schema."""
        
        # Evolution sessions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS evolution_sessions (
                session_id TEXT PRIMARY KEY,
                target_files TEXT,  -- JSON array of file paths
                objectives TEXT,    -- JSON object of objectives
                max_iterations INTEGER,
                start_time REAL,
                end_time REAL,
                status TEXT DEFAULT 'active',
                final_report TEXT,  -- JSON object
                created_at REAL DEFAULT (julianday('now'))
            )
        """)
        
        # Evolution steps table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS evolution_steps (
                step_id TEXT PRIMARY KEY,
                session_id TEXT,
                step_type TEXT,
                file_path TEXT,
                prompt TEXT,
                context TEXT,       -- JSON object
                start_time REAL,
                end_time REAL,
                execution_time REAL,
                status TEXT DEFAULT 'running',
                result TEXT,        -- JSON object
                metrics TEXT,       -- JSON object
                errors TEXT,        -- JSON array
                created_at REAL DEFAULT (julianday('now')),
                FOREIGN KEY (session_id) REFERENCES evolution_sessions (session_id)
            )
        """)
        
        # Decision nodes table for decision tree tracking
        await db.execute("""
            CREATE TABLE IF NOT EXISTS decision_nodes (
                node_id TEXT PRIMARY KEY,
                session_id TEXT,
                step_id TEXT,
                parent_node_id TEXT,
                decision_type TEXT,
                context TEXT,       -- JSON object
                outcome TEXT,       -- JSON object
                metrics TEXT,       -- JSON object
                timestamp REAL,
                created_at REAL DEFAULT (julianday('now')),
                FOREIGN KEY (session_id) REFERENCES evolution_sessions (session_id),
                FOREIGN KEY (step_id) REFERENCES evolution_steps (step_id),
                FOREIGN KEY (parent_node_id) REFERENCES decision_nodes (node_id)
            )
        """)
        
        # Performance metrics table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                step_id TEXT,
                metric_type TEXT,
                metric_name TEXT,
                metric_value REAL,
                metadata TEXT,      -- JSON object
                timestamp REAL,
                created_at REAL DEFAULT (julianday('now')),
                FOREIGN KEY (session_id) REFERENCES evolution_sessions (session_id),
                FOREIGN KEY (step_id) REFERENCES evolution_steps (step_id)
            )
        """)
        
        # Learning data table for continuous learning
        await db.execute("""
            CREATE TABLE IF NOT EXISTS learning_data (
                learning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_id TEXT,
                context TEXT,       -- JSON object
                result TEXT,        -- JSON object
                patterns TEXT,      -- JSON array
                insights TEXT,      -- JSON array
                success_score REAL,
                timestamp REAL,
                created_at REAL DEFAULT (julianday('now')),
                FOREIGN KEY (step_id) REFERENCES evolution_steps (step_id)
            )
        """)
        
        # Pattern analysis table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pattern_analysis (
                analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                file_path TEXT,
                pattern_type TEXT,
                pattern_data TEXT,  -- JSON object
                confidence REAL,
                frequency INTEGER,
                success_rate REAL,
                timestamp REAL,
                created_at REAL DEFAULT (julianday('now')),
                FOREIGN KEY (session_id) REFERENCES evolution_sessions (session_id)
            )
        """)
        
        # Error tracking table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS error_tracking (
                error_id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_id TEXT,
                error_type TEXT,
                error_message TEXT,
                stack_trace TEXT,
                context TEXT,       -- JSON object
                resolution TEXT,
                timestamp REAL,
                created_at REAL DEFAULT (julianday('now')),
                FOREIGN KEY (step_id) REFERENCES evolution_steps (step_id)
            )
        """)
        
        # Code evolution history table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS code_evolution_history (
                evolution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_id TEXT,
                file_path TEXT,
                original_code TEXT,
                evolved_code TEXT,
                diff_summary TEXT,
                complexity_before TEXT,  -- JSON object
                complexity_after TEXT,   -- JSON object
                improvement_metrics TEXT, -- JSON object
                timestamp REAL,
                created_at REAL DEFAULT (julianday('now')),
                FOREIGN KEY (step_id) REFERENCES evolution_steps (step_id)
            )
        """)
        
        # Create indexes for better query performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_steps_session ON evolution_steps (session_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_steps_file ON evolution_steps (file_path)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_decisions_session ON decision_nodes (session_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_decisions_step ON decision_nodes (step_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_metrics_session ON performance_metrics (session_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_metrics_step ON performance_metrics (step_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_learning_step ON learning_data (step_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_patterns_session ON pattern_analysis (session_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_errors_step ON error_tracking (step_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_evolution_file ON code_evolution_history (file_path)")
    
    async def create_session(
        self,
        session_id: str,
        target_files: List[str],
        objectives: Dict[str, Any],
        max_iterations: int
    ) -> None:
        """Create a new evolution session."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO evolution_sessions 
                (session_id, target_files, objectives, max_iterations, start_time)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                json.dumps(target_files),
                json.dumps(objectives),
                max_iterations,
                time.time()
            ))
            await db.commit()
        
        logger.debug(f"Created session {session_id}")
    
    async def store_step_context(self, step_context: Dict[str, Any]) -> None:
        """Store step context in the database."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO evolution_steps 
                (step_id, session_id, step_type, file_path, prompt, context, start_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                step_context["step_id"],
                step_context["session_id"],
                step_context["step_type"],
                step_context.get("file_path"),
                step_context.get("prompt"),
                json.dumps(step_context.get("context", {})),
                step_context["start_time"],
                step_context["status"]
            ))
            await db.commit()
        
        logger.debug(f"Stored step context {step_context['step_id']}")
    
    async def store_decision(self, decision: Dict[str, Any]) -> None:
        """Store a decision node in the database."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO decision_nodes 
                (node_id, session_id, step_id, decision_type, context, outcome, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                decision["decision_id"],
                decision.get("session_id"),
                decision["step_id"],
                decision["decision_type"],
                json.dumps(decision["context"]),
                json.dumps(decision.get("outcome")),
                decision["timestamp"]
            ))
            await db.commit()
        
        logger.debug(f"Stored decision {decision['decision_id']}")
    
    async def update_step_metrics(self, step_id: str, metrics: Dict[str, Any]) -> None:
        """Update metrics for a step."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            # Update the step record
            await db.execute("""
                UPDATE evolution_steps 
                SET metrics = ? 
                WHERE step_id = ?
            """, (json.dumps(metrics), step_id))
            
            # Store individual metrics
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, (int, float)):
                    await db.execute("""
                        INSERT INTO performance_metrics 
                        (step_id, metric_type, metric_name, metric_value, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (step_id, "step_metric", metric_name, metric_value, time.time()))
            
            await db.commit()
        
        logger.debug(f"Updated metrics for step {step_id}")
    
    async def record_step_error(self, step_id: str, error_record: Dict[str, Any]) -> None:
        """Record an error for a step."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO error_tracking 
                (step_id, error_type, error_message, context, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                step_id,
                "step_error",
                error_record["error"],
                json.dumps(error_record),
                error_record["timestamp"]
            ))
            await db.commit()
        
        logger.debug(f"Recorded error for step {step_id}")
    
    async def complete_step_context(self, step_id: str, step_context: Dict[str, Any]) -> None:
        """Complete and finalize step context."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                UPDATE evolution_steps 
                SET end_time = ?, execution_time = ?, status = ?, result = ?, errors = ?
                WHERE step_id = ?
            """, (
                step_context.get("end_time"),
                step_context.get("execution_time"),
                step_context["status"],
                json.dumps(step_context.get("result", {})),
                json.dumps(step_context.get("errors", [])),
                step_id
            ))
            await db.commit()
        
        logger.debug(f"Completed step context {step_id}")
    
    async def store_learning_data(self, learning_data: Dict[str, Any]) -> None:
        """Store learning data for continuous learning."""
        await self.initialize()
        
        # Extract success score from result
        result = learning_data.get("result", {})
        success_score = 0.0
        
        if isinstance(result, dict):
            metrics = result.get("evolution_metrics", {})
            if metrics:
                # Calculate average of improvement metrics
                improvements = [
                    metrics.get("performance_improvement", 0),
                    metrics.get("maintainability_score", 0),
                    metrics.get("complexity_improvement", 0)
                ]
                success_score = sum(improvements) / len(improvements)
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO learning_data 
                (step_id, context, result, success_score, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                learning_data["step_id"],
                json.dumps(learning_data["context"]),
                json.dumps(learning_data["result"]),
                success_score,
                learning_data["timestamp"]
            ))
            await db.commit()
        
        logger.debug(f"Stored learning data for step {learning_data['step_id']}")
    
    async def get_file_evolution_history(self, file_path: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get evolution history for a specific file."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            async with db.execute("""
                SELECT es.*, ld.success_score, ld.patterns, ld.insights
                FROM evolution_steps es
                LEFT JOIN learning_data ld ON es.step_id = ld.step_id
                WHERE es.file_path = ?
                ORDER BY es.created_at DESC
                LIMIT ?
            """, (file_path, limit)) as cursor:
                rows = await cursor.fetchall()
        
        history = []
        for row in rows:
            step_data = {
                "step_id": row[0],
                "session_id": row[1],
                "step_type": row[2],
                "file_path": row[3],
                "prompt": row[4],
                "context": json.loads(row[5]) if row[5] else {},
                "start_time": row[6],
                "end_time": row[7],
                "execution_time": row[8],
                "status": row[9],
                "result": json.loads(row[10]) if row[10] else {},
                "metrics": json.loads(row[11]) if row[11] else {},
                "errors": json.loads(row[12]) if row[12] else [],
                "success_score": row[14] if row[14] is not None else 0.0,
                "patterns": json.loads(row[15]) if row[15] else [],
                "insights": json.loads(row[16]) if row[16] else []
            }
            
            # Add success indicator
            step_data["success"] = (
                step_data["status"] == "completed" and 
                not step_data["errors"] and 
                step_data["success_score"] > 0
            )
            
            history.append(step_data)
        
        return history
    
    async def get_session_data(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all data for a session."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            async with db.execute("""
                SELECT es.*, ld.success_score, ld.patterns, ld.insights
                FROM evolution_steps es
                LEFT JOIN learning_data ld ON es.step_id = ld.step_id
                WHERE es.session_id = ?
                ORDER BY es.created_at ASC
            """, (session_id,)) as cursor:
                rows = await cursor.fetchall()
        
        session_data = []
        for row in rows:
            step_data = {
                "step_id": row[0],
                "session_id": row[1],
                "step_type": row[2],
                "file_path": row[3],
                "prompt": row[4],
                "context": json.loads(row[5]) if row[5] else {},
                "start_time": row[6],
                "end_time": row[7],
                "execution_time": row[8],
                "status": row[9],
                "result": json.loads(row[10]) if row[10] else {},
                "metrics": json.loads(row[11]) if row[11] else {},
                "errors": json.loads(row[12]) if row[12] else [],
                "success_score": row[14] if row[14] is not None else 0.0,
                "patterns": json.loads(row[15]) if row[15] else [],
                "insights": json.loads(row[16]) if row[16] else []
            }
            
            # Add success indicator
            step_data["success"] = (
                step_data["status"] == "completed" and 
                not step_data["errors"] and 
                step_data["success_score"] > 0
            )
            
            session_data.append(step_data)
        
        return session_data
    
    async def get_recent_evolution_history(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent evolution history across all sessions."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            async with db.execute("""
                SELECT es.*, ld.success_score, ld.patterns, ld.insights
                FROM evolution_steps es
                LEFT JOIN learning_data ld ON es.step_id = ld.step_id
                WHERE es.status = 'completed'
                ORDER BY es.created_at DESC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
        
        history = []
        for row in rows:
            step_data = {
                "step_id": row[0],
                "session_id": row[1],
                "step_type": row[2],
                "file_path": row[3],
                "prompt": row[4],
                "context": json.loads(row[5]) if row[5] else {},
                "start_time": row[6],
                "end_time": row[7],
                "execution_time": row[8],
                "status": row[9],
                "result": json.loads(row[10]) if row[10] else {},
                "metrics": json.loads(row[11]) if row[11] else {},
                "errors": json.loads(row[12]) if row[12] else [],
                "success_score": row[14] if row[14] is not None else 0.0,
                "patterns": json.loads(row[15]) if row[15] else [],
                "insights": json.loads(row[16]) if row[16] else []
            }
            
            # Add success indicator and complexity metrics
            step_data["success"] = (
                step_data["status"] == "completed" and 
                not step_data["errors"] and 
                step_data["success_score"] > 0
            )
            
            # Extract complexity metrics from context or result
            complexity_metrics = {}
            if "complexity_metrics" in step_data["context"]:
                complexity_metrics = step_data["context"]["complexity_metrics"]
            elif "complexity_metrics" in step_data["result"]:
                complexity_metrics = step_data["result"]["complexity_metrics"]
            
            step_data["complexity_metrics"] = complexity_metrics
            
            # Extract evolution metrics
            evolution_metrics = step_data["result"].get("evolution_metrics", {})
            step_data["evolution_metrics"] = evolution_metrics
            
            # Extract applied patterns
            applied_patterns = step_data["result"].get("applied_patterns", [])
            step_data["applied_patterns"] = applied_patterns
            
            history.append(step_data)
        
        return history
    
    async def store_pattern_analysis(
        self,
        session_id: str,
        file_path: Optional[str],
        pattern_type: str,
        pattern_data: Dict[str, Any],
        confidence: float,
        frequency: int = 1,
        success_rate: float = 0.0
    ) -> None:
        """Store pattern analysis results."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO pattern_analysis 
                (session_id, file_path, pattern_type, pattern_data, confidence, frequency, success_rate, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                file_path,
                pattern_type,
                json.dumps(pattern_data),
                confidence,
                frequency,
                success_rate,
                time.time()
            ))
            await db.commit()
        
        logger.debug(f"Stored pattern analysis for session {session_id}")
    
    async def get_performance_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get performance analytics for a session."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            # Get basic session stats
            async with db.execute("""
                SELECT COUNT(*), AVG(execution_time), MIN(execution_time), MAX(execution_time)
                FROM evolution_steps 
                WHERE session_id = ? AND status = 'completed'
            """, (session_id,)) as cursor:
                stats_row = await cursor.fetchone()
            
            # Get success rate
            async with db.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' AND errors = '[]' THEN 1 ELSE 0 END) as successful
                FROM evolution_steps 
                WHERE session_id = ?
            """, (session_id,)) as cursor:
                success_row = await cursor.fetchone()
            
            # Get performance metrics
            async with db.execute("""
                SELECT metric_name, AVG(metric_value), MIN(metric_value), MAX(metric_value)
                FROM performance_metrics 
                WHERE session_id = ?
                GROUP BY metric_name
            """, (session_id,)) as cursor:
                metrics_rows = await cursor.fetchall()
        
        analytics = {
            "session_id": session_id,
            "total_steps": stats_row[0] if stats_row[0] else 0,
            "avg_execution_time": stats_row[1] if stats_row[1] else 0,
            "min_execution_time": stats_row[2] if stats_row[2] else 0,
            "max_execution_time": stats_row[3] if stats_row[3] else 0,
            "success_rate": (success_row[1] / success_row[0]) if success_row[0] > 0 else 0,
            "performance_metrics": {}
        }
        
        for metric_row in metrics_rows:
            analytics["performance_metrics"][metric_row[0]] = {
                "avg": metric_row[1],
                "min": metric_row[2],
                "max": metric_row[3]
            }
        
        return analytics
    
    async def finalize_session(self, session_id: str, final_report: Dict[str, Any]) -> None:
        """Finalize a session with final report."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                UPDATE evolution_sessions 
                SET end_time = ?, status = 'completed', final_report = ?
                WHERE session_id = ?
            """, (time.time(), json.dumps(final_report), session_id))
            await db.commit()
        
        logger.debug(f"Finalized session {session_id}")
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Clean up old data to manage database size."""
        await self.initialize()
        
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        
        async with aiosqlite.connect(self.database_path) as db:
            # Clean up old sessions and related data
            await db.execute("""
                DELETE FROM evolution_sessions 
                WHERE start_time < ? AND status = 'completed'
            """, (cutoff_time,))
            
            # The foreign key constraints will handle cascading deletes
            await db.commit()
        
        logger.info(f"Cleaned up data older than {days_to_keep} days")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        await self.initialize()
        
        async with aiosqlite.connect(self.database_path) as db:
            stats = {}
            
            # Count records in each table
            tables = [
                "evolution_sessions", "evolution_steps", "decision_nodes",
                "performance_metrics", "learning_data", "pattern_analysis",
                "error_tracking", "code_evolution_history"
            ]
            
            for table in tables:
                async with db.execute(f"SELECT COUNT(*) FROM {table}") as cursor:
                    count = await cursor.fetchone()
                    stats[f"{table}_count"] = count[0] if count else 0
            
            # Get database file size
            db_path = Path(self.database_path)
            if db_path.exists():
                stats["database_size_mb"] = db_path.stat().st_size / (1024 * 1024)
            else:
                stats["database_size_mb"] = 0
        
        return stats

