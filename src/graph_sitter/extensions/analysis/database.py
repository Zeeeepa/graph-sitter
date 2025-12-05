#!/usr/bin/env python3
"""
Analysis Database and Error Management

SQLite-based storage for analysis results, error tracking, and session management.
"""

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AnalysisError:
    """Structured representation of a code analysis error."""

    file_path: str
    line: int
    column: int
    error_type: str
    severity: str
    message: str
    tool_source: str
    category: str = "general"
    fix_suggestion: Optional[str] = None
    confidence: float = 1.0
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "error_type": self.error_type,
            "severity": self.severity,
            "message": self.message,
            "tool_source": self.tool_source,
            "category": self.category,
            "fix_suggestion": self.fix_suggestion,
            "confidence": self.confidence,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisError":
        """Create AnalysisError from dictionary."""
        return cls(**data)


class ErrorDatabase:
    """SQLite database for storing and querying analysis errors."""

    def __init__(self, db_path: str = "analysis_errors.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_path TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tools_used TEXT NOT NULL,
                    total_errors INTEGER DEFAULT 0,
                    config_hash TEXT,
                    completed BOOLEAN DEFAULT FALSE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    file_path TEXT NOT NULL,
                    line INTEGER,
                    column INTEGER,
                    error_type TEXT,
                    severity TEXT,
                    message TEXT,
                    tool_source TEXT,
                    category TEXT,
                    fix_suggestion TEXT,
                    confidence REAL,
                    context TEXT,
                    FOREIGN KEY (session_id) REFERENCES analysis_sessions (id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_session 
                ON errors (session_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_category 
                ON errors (category)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_severity 
                ON errors (severity)
            """)

    def create_session(
        self, target_path: str, tools_used: List[str], config: Dict[str, Any]
    ) -> int:
        """Create a new analysis session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO analysis_sessions 
                (target_path, timestamp, tools_used, config_hash)
                VALUES (?, ?, ?, ?)
            """,
                (
                    target_path,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    json.dumps(tools_used),
                    str(hash(json.dumps(config, sort_keys=True))),
                ),
            )
            return cursor.lastrowid

    def store_errors(self, errors: List[AnalysisError], session_id: int):
        """Store errors in the database."""
        with sqlite3.connect(self.db_path) as conn:
            for error in errors:
                conn.execute(
                    """
                    INSERT INTO errors 
                    (session_id, file_path, line, column, error_type, severity, 
                     message, tool_source, category, fix_suggestion, confidence, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_id,
                        error.file_path,
                        error.line,
                        error.column,
                        error.error_type,
                        error.severity,
                        error.message,
                        error.tool_source,
                        error.category,
                        error.fix_suggestion,
                        error.confidence,
                        error.context,
                    ),
                )

    def update_session(self, session_id: int, total_errors: int):
        """Update session with final error count."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE analysis_sessions 
                SET total_errors = ?, completed = TRUE 
                WHERE id = ?
            """,
                (total_errors, session_id),
            )

    def query_errors(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query errors with filters."""
        query = "SELECT * FROM errors WHERE 1=1"
        params = []

        for key, value in filters.items():
            if key in ["severity", "category", "tool_source", "error_type"]:
                query += f" AND {key} = ?"
                params.append(value)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis sessions."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM analysis_sessions 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_session_errors(self, session_id: int) -> List[AnalysisError]:
        """Get all errors for a specific session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT file_path, line, column, error_type, severity, message,
                       tool_source, category, fix_suggestion, confidence, context
                FROM errors 
                WHERE session_id = ?
            """, (session_id,))
            
            errors = []
            for row in cursor.fetchall():
                errors.append(AnalysisError(
                    file_path=row["file_path"],
                    line=row["line"],
                    column=row["column"],
                    error_type=row["error_type"],
                    severity=row["severity"],
                    message=row["message"],
                    tool_source=row["tool_source"],
                    category=row["category"],
                    fix_suggestion=row["fix_suggestion"],
                    confidence=row["confidence"] or 1.0,
                    context=row["context"],
                ))
            return errors