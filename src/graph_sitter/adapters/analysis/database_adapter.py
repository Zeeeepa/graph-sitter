"""
Unified Database Adapter for Analysis Results

This module provides database integration for the new unified analysis framework
while maintaining backward compatibility with existing database schemas.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from graph_sitter.core.codebase import Codebase

# Import new unified analysis framework
from .base import AnalysisResult, AnalysisIssue, AnalysisMetric, AnalysisType, IssueSeverity

logger = logging.getLogger(__name__)


class UnifiedAnalysisDatabase:
    """
    Unified database for storing and querying codebase analysis results.
    
    This class integrates with the new standardized analysis framework
    while maintaining backward compatibility with legacy formats.
    """
    
    def __init__(self, db_path: str = "unified_analysis.db"):
        """
        Initialize the unified analysis database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema for unified analysis results."""
        try:
            with self._get_connection() as conn:
                # Codebases table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS codebases (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        root_path TEXT NOT NULL,
                        language TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT
                    )
                """)
                
                # Analysis sessions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_sessions (
                        id TEXT PRIMARY KEY,
                        codebase_id TEXT NOT NULL,
                        session_type TEXT NOT NULL,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        status TEXT DEFAULT 'running',
                        config TEXT,
                        FOREIGN KEY (codebase_id) REFERENCES codebases (id)
                    )
                """)
                
                # Analysis results table (unified format)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        analyzer_name TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        execution_time REAL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        raw_data TEXT,
                        FOREIGN KEY (session_id) REFERENCES analysis_sessions (id)
                    )
                """)
                
                # Issues table (standardized format)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_issues (
                        id TEXT PRIMARY KEY,
                        result_id TEXT NOT NULL,
                        issue_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        description TEXT NOT NULL,
                        file_path TEXT,
                        location TEXT,
                        line_number INTEGER,
                        column_number INTEGER,
                        rule_id TEXT,
                        suggestion TEXT,
                        metadata TEXT,
                        FOREIGN KEY (result_id) REFERENCES analysis_results (id)
                    )
                """)
                
                # Metrics table (standardized format)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_metrics (
                        id TEXT PRIMARY KEY,
                        result_id TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value TEXT NOT NULL,
                        metric_unit TEXT,
                        metric_description TEXT,
                        metric_category TEXT,
                        FOREIGN KEY (result_id) REFERENCES analysis_results (id)
                    )
                """)
                
                # Recommendations table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_recommendations (
                        id TEXT PRIMARY KEY,
                        result_id TEXT NOT NULL,
                        recommendation TEXT NOT NULL,
                        priority INTEGER DEFAULT 1,
                        category TEXT,
                        FOREIGN KEY (result_id) REFERENCES analysis_results (id)
                    )
                """)
                
                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_codebase_name ON codebases (name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_session_codebase ON analysis_sessions (codebase_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_result_session ON analysis_results (session_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_result_type ON analysis_results (analysis_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_issue_result ON analysis_issues (result_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_issue_severity ON analysis_issues (severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_metric_result ON analysis_metrics (result_id)")
                
                conn.commit()
                logger.info("Unified analysis database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def store_codebase(self, codebase: Codebase) -> str:
        """
        Store codebase information in the database.
        
        Args:
            codebase: Codebase to store
            
        Returns:
            Codebase ID
        """
        codebase_id = str(hash(str(codebase.root_path)))
        
        with self._get_connection() as conn:
            # Check if codebase already exists
            existing = conn.execute(
                "SELECT id FROM codebases WHERE id = ?",
                (codebase_id,)
            ).fetchone()
            
            if existing:
                # Update existing codebase
                conn.execute("""
                    UPDATE codebases 
                    SET updated_at = CURRENT_TIMESTAMP,
                        metadata = ?
                    WHERE id = ?
                """, (
                    json.dumps({
                        'file_count': len(codebase.files),
                        'function_count': sum(len(f.functions) for f in codebase.files),
                        'class_count': sum(len(f.classes) for f in codebase.files)
                    }),
                    codebase_id
                ))
            else:
                # Insert new codebase
                conn.execute("""
                    INSERT INTO codebases (id, name, root_path, language, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    codebase_id,
                    codebase.root_path.name,
                    str(codebase.root_path),
                    'python',  # Default, could be detected
                    json.dumps({
                        'file_count': len(codebase.files),
                        'function_count': sum(len(f.functions) for f in codebase.files),
                        'class_count': sum(len(f.classes) for f in codebase.files)
                    })
                ))
            
            conn.commit()
        
        return codebase_id
    
    def create_analysis_session(
        self,
        codebase_id: str,
        session_type: str = "comprehensive",
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new analysis session.
        
        Args:
            codebase_id: ID of the codebase being analyzed
            session_type: Type of analysis session
            config: Analysis configuration
            
        Returns:
            Session ID
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(codebase_id) % 10000}"
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO analysis_sessions (id, codebase_id, session_type, config)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                codebase_id,
                session_type,
                json.dumps(config) if config else None
            ))
            conn.commit()
        
        return session_id
    
    def store_analysis_result(
        self,
        session_id: str,
        analyzer_name: str,
        result: AnalysisResult
    ) -> str:
        """
        Store analysis result in the database.
        
        Args:
            session_id: Analysis session ID
            analyzer_name: Name of the analyzer
            result: Analysis result to store
            
        Returns:
            Result ID
        """
        result_id = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(analyzer_name) % 10000}"
        
        with self._get_connection() as conn:
            # Store main result
            conn.execute("""
                INSERT INTO analysis_results (
                    id, session_id, analysis_type, analyzer_name, timestamp,
                    execution_time, success, error_message, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id,
                session_id,
                result.analysis_type.value,
                analyzer_name,
                result.timestamp.isoformat(),
                result.execution_time,
                result.success,
                result.error_message,
                json.dumps(result.raw_data)
            ))
            
            # Store issues
            for issue in result.issues:
                issue_id = f"issue_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(issue.description) % 10000}"
                conn.execute("""
                    INSERT INTO analysis_issues (
                        id, result_id, issue_type, severity, description,
                        file_path, location, line_number, column_number,
                        rule_id, suggestion, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    issue_id,
                    result_id,
                    issue.type,
                    issue.severity.value,
                    issue.description,
                    issue.file,
                    str(issue.location) if issue.location else None,
                    issue.line_number,
                    issue.column_number,
                    issue.rule_id,
                    issue.suggestion,
                    json.dumps(issue.metadata) if issue.metadata else None
                ))
            
            # Store metrics
            for metric in result.metrics:
                metric_id = f"metric_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(metric.name) % 10000}"
                conn.execute("""
                    INSERT INTO analysis_metrics (
                        id, result_id, metric_name, metric_value,
                        metric_unit, metric_description, metric_category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric_id,
                    result_id,
                    metric.name,
                    str(metric.value),
                    metric.unit,
                    metric.description,
                    metric.category
                ))
            
            # Store recommendations
            for i, recommendation in enumerate(result.recommendations):
                rec_id = f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
                conn.execute("""
                    INSERT INTO analysis_recommendations (
                        id, result_id, recommendation, priority
                    ) VALUES (?, ?, ?, ?)
                """, (
                    rec_id,
                    result_id,
                    recommendation,
                    i + 1  # Priority based on order
                ))
            
            conn.commit()
        
        return result_id
    
    def complete_analysis_session(self, session_id: str, status: str = "completed") -> None:
        """
        Mark an analysis session as completed.
        
        Args:
            session_id: Session ID to complete
            status: Final status of the session
        """
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE analysis_sessions 
                SET completed_at = CURRENT_TIMESTAMP, status = ?
                WHERE id = ?
            """, (status, session_id))
            conn.commit()
    
    def get_analysis_results(
        self,
        codebase_id: Optional[str] = None,
        session_id: Optional[str] = None,
        analysis_type: Optional[AnalysisType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve analysis results from the database.
        
        Args:
            codebase_id: Filter by codebase ID
            session_id: Filter by session ID
            analysis_type: Filter by analysis type
            limit: Maximum number of results to return
            
        Returns:
            List of analysis results
        """
        query = """
            SELECT ar.*, as_.codebase_id, c.name as codebase_name
            FROM analysis_results ar
            JOIN analysis_sessions as_ ON ar.session_id = as_.id
            JOIN codebases c ON as_.codebase_id = c.id
            WHERE 1=1
        """
        params = []
        
        if codebase_id:
            query += " AND as_.codebase_id = ?"
            params.append(codebase_id)
        
        if session_id:
            query += " AND ar.session_id = ?"
            params.append(session_id)
        
        if analysis_type:
            query += " AND ar.analysis_type = ?"
            params.append(analysis_type.value)
        
        query += " ORDER BY ar.timestamp DESC LIMIT ?"
        params.append(limit)
        
        with self._get_connection() as conn:
            results = conn.execute(query, params).fetchall()
            return [dict(row) for row in results]
    
    def get_issues_summary(
        self,
        codebase_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Get a summary of issues by severity.
        
        Args:
            codebase_id: Filter by codebase ID
            session_id: Filter by session ID
            
        Returns:
            Dictionary with issue counts by severity
        """
        query = """
            SELECT ai.severity, COUNT(*) as count
            FROM analysis_issues ai
            JOIN analysis_results ar ON ai.result_id = ar.id
            JOIN analysis_sessions as_ ON ar.session_id = as_.id
            WHERE 1=1
        """
        params = []
        
        if codebase_id:
            query += " AND as_.codebase_id = ?"
            params.append(codebase_id)
        
        if session_id:
            query += " AND ar.session_id = ?"
            params.append(session_id)
        
        query += " GROUP BY ai.severity"
        
        with self._get_connection() as conn:
            results = conn.execute(query, params).fetchall()
            return {row['severity']: row['count'] for row in results}
    
    def get_metrics_summary(
        self,
        codebase_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of metrics.
        
        Args:
            codebase_id: Filter by codebase ID
            session_id: Filter by session ID
            
        Returns:
            Dictionary with metric summaries
        """
        query = """
            SELECT am.metric_name, am.metric_value, am.metric_category
            FROM analysis_metrics am
            JOIN analysis_results ar ON am.result_id = ar.id
            JOIN analysis_sessions as_ ON ar.session_id = as_.id
            WHERE 1=1
        """
        params = []
        
        if codebase_id:
            query += " AND as_.codebase_id = ?"
            params.append(codebase_id)
        
        if session_id:
            query += " AND ar.session_id = ?"
            params.append(session_id)
        
        with self._get_connection() as conn:
            results = conn.execute(query, params).fetchall()
            
            metrics_by_category = {}
            for row in results:
                category = row['metric_category'] or 'general'
                if category not in metrics_by_category:
                    metrics_by_category[category] = {}
                
                metrics_by_category[category][row['metric_name']] = row['metric_value']
            
            return metrics_by_category
    
    def export_session_data(self, session_id: str, output_path: str) -> None:
        """
        Export all data for a session to a JSON file.
        
        Args:
            session_id: Session ID to export
            output_path: Path to save the exported data
        """
        # Get session info
        with self._get_connection() as conn:
            session = conn.execute("""
                SELECT as_.*, c.name as codebase_name, c.root_path
                FROM analysis_sessions as_
                JOIN codebases c ON as_.codebase_id = c.id
                WHERE as_.id = ?
            """, (session_id,)).fetchone()
            
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Get all results for this session
            results = self.get_analysis_results(session_id=session_id, limit=1000)
            
            # Get issues and metrics for each result
            for result in results:
                result_id = result['id']
                
                # Get issues
                issues = conn.execute("""
                    SELECT * FROM analysis_issues WHERE result_id = ?
                """, (result_id,)).fetchall()
                result['issues'] = [dict(issue) for issue in issues]
                
                # Get metrics
                metrics = conn.execute("""
                    SELECT * FROM analysis_metrics WHERE result_id = ?
                """, (result_id,)).fetchall()
                result['metrics'] = [dict(metric) for metric in metrics]
                
                # Get recommendations
                recommendations = conn.execute("""
                    SELECT * FROM analysis_recommendations WHERE result_id = ?
                """, (result_id,)).fetchall()
                result['recommendations'] = [dict(rec) for rec in recommendations]
        
        # Export to JSON
        export_data = {
            'session': dict(session),
            'results': results,
            'exported_at': datetime.now().isoformat()
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Session data exported to {output_file}")


# Convenience class for backward compatibility
class AnalysisDatabase(UnifiedAnalysisDatabase):
    """Alias for backward compatibility."""
    pass


# Export for use in other modules
__all__ = [
    "UnifiedAnalysisDatabase",
    "AnalysisDatabase"  # For backward compatibility
]

