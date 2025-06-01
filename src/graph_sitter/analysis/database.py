"""Database integration for storing and querying analysis results."""

import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .enhanced_analysis import AnalysisReport
from .metrics import CodebaseMetrics, FunctionMetrics, ClassMetrics, FileMetrics

logger = logging.getLogger(__name__)


class AnalysisDatabase:
    """Database for storing and querying codebase analysis results."""
    
    def __init__(self, db_path: str = "analysis.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        try:
            with self._get_connection() as conn:
                # Codebases table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS codebases (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        path TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_analyzed TIMESTAMP,
                        total_files INTEGER,
                        total_functions INTEGER,
                        total_classes INTEGER,
                        total_symbols INTEGER,
                        total_imports INTEGER,
                        total_lines INTEGER,
                        health_score REAL,
                        metadata TEXT
                    )
                """)
                
                # Analysis reports table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codebase_id TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        health_score REAL,
                        total_issues INTEGER,
                        total_recommendations INTEGER,
                        report_data TEXT,
                        FOREIGN KEY (codebase_id) REFERENCES codebases (id)
                    )
                """)
                
                # Functions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS functions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codebase_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        filepath TEXT NOT NULL,
                        line_count INTEGER,
                        parameter_count INTEGER,
                        cyclomatic_complexity INTEGER,
                        maintainability_index REAL,
                        documentation_coverage REAL,
                        test_coverage_estimate REAL,
                        is_async BOOLEAN,
                        has_decorators BOOLEAN,
                        has_docstring BOOLEAN,
                        has_type_annotations BOOLEAN,
                        impact_score REAL,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (codebase_id) REFERENCES codebases (id)
                    )
                """)
                
                # Classes table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS classes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codebase_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        filepath TEXT NOT NULL,
                        method_count INTEGER,
                        attribute_count INTEGER,
                        inheritance_depth INTEGER,
                        subclass_count INTEGER,
                        cohesion_score REAL,
                        coupling_score REAL,
                        documentation_coverage REAL,
                        test_coverage_estimate REAL,
                        has_constructor BOOLEAN,
                        has_docstring BOOLEAN,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (codebase_id) REFERENCES codebases (id)
                    )
                """)
                
                # Function calls table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS function_calls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codebase_id TEXT NOT NULL,
                        caller_function TEXT NOT NULL,
                        callee_function TEXT NOT NULL,
                        call_count INTEGER DEFAULT 1,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (codebase_id) REFERENCES codebases (id)
                    )
                """)
                
                # Dependencies table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS dependencies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codebase_id TEXT NOT NULL,
                        source_symbol TEXT NOT NULL,
                        target_symbol TEXT NOT NULL,
                        dependency_type TEXT,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (codebase_id) REFERENCES codebases (id)
                    )
                """)
                
                # Imports table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS imports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codebase_id TEXT NOT NULL,
                        source_file TEXT NOT NULL,
                        imported_module TEXT NOT NULL,
                        imported_symbol TEXT,
                        is_external BOOLEAN,
                        is_unused BOOLEAN,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (codebase_id) REFERENCES codebases (id)
                    )
                """)
                
                # Issues table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS issues (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codebase_id TEXT NOT NULL,
                        issue_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        symbol_name TEXT,
                        description TEXT,
                        suggestion TEXT,
                        filepath TEXT,
                        line_start INTEGER,
                        line_end INTEGER,
                        confidence REAL,
                        impact_score REAL,
                        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (codebase_id) REFERENCES codebases (id)
                    )
                """)
                
                # Create indexes for better query performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_functions_codebase ON functions(codebase_id)",
                    "CREATE INDEX IF NOT EXISTS idx_functions_complexity ON functions(cyclomatic_complexity)",
                    "CREATE INDEX IF NOT EXISTS idx_classes_codebase ON classes(codebase_id)",
                    "CREATE INDEX IF NOT EXISTS idx_function_calls_codebase ON function_calls(codebase_id)",
                    "CREATE INDEX IF NOT EXISTS idx_dependencies_codebase ON dependencies(codebase_id)",
                    "CREATE INDEX IF NOT EXISTS idx_imports_codebase ON imports(codebase_id)",
                    "CREATE INDEX IF NOT EXISTS idx_issues_codebase ON issues(codebase_id)",
                    "CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity)",
                ]
                
                for index_sql in indexes:
                    conn.execute(index_sql)
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def store_analysis_report(self, report: AnalysisReport) -> int:
        """Store complete analysis report."""
        try:
            with self._get_connection() as conn:
                # Store/update codebase info
                self._store_codebase_info(conn, report)
                
                # Store analysis report
                report_id = conn.execute("""
                    INSERT INTO analysis_reports 
                    (codebase_id, timestamp, health_score, total_issues, total_recommendations, report_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    report.codebase_id,
                    report.timestamp,
                    report.health_score,
                    len(report.issues),
                    len(report.recommendations),
                    json.dumps(asdict(report), default=str)
                )).lastrowid
                
                # Store function metrics
                self._store_function_metrics(conn, report.codebase_id, report.function_analysis)
                
                # Store class metrics
                self._store_class_metrics(conn, report.codebase_id, report.class_analysis)
                
                # Store call graph data
                self._store_call_graph_data(conn, report.codebase_id, report.call_graph_analysis)
                
                # Store dependency data
                self._store_dependency_data(conn, report.codebase_id, report.dependency_analysis)
                
                # Store issues
                self._store_issues(conn, report.codebase_id, report.issues)
                
                conn.commit()
                logger.info(f"Stored analysis report {report_id} for codebase {report.codebase_id}")
                return report_id
                
        except Exception as e:
            logger.error(f"Error storing analysis report: {e}")
            raise
    
    def _store_codebase_info(self, conn: sqlite3.Connection, report: AnalysisReport):
        """Store or update codebase information."""
        summary = report.summary
        
        conn.execute("""
            INSERT OR REPLACE INTO codebases 
            (id, name, path, last_analyzed, total_files, total_functions, total_classes, 
             total_symbols, total_imports, total_lines, health_score, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.codebase_id,
            report.codebase_id,  # Use ID as name for now
            "unknown",  # Path not available in report
            report.timestamp,
            summary.get('total_files', 0),
            summary.get('total_functions', 0),
            summary.get('total_classes', 0),
            summary.get('total_symbols', 0),
            summary.get('total_imports', 0),
            summary.get('total_lines', 0),
            report.health_score,
            json.dumps(summary, default=str)
        ))
    
    def _store_function_metrics(self, conn: sqlite3.Connection, codebase_id: str, 
                              function_analysis: List[Dict[str, Any]]):
        """Store function metrics."""
        # Clear existing function data for this codebase
        conn.execute("DELETE FROM functions WHERE codebase_id = ?", (codebase_id,))
        
        for func_data in function_analysis:
            conn.execute("""
                INSERT INTO functions 
                (codebase_id, name, filepath, line_count, parameter_count, cyclomatic_complexity,
                 maintainability_index, documentation_coverage, test_coverage_estimate,
                 is_async, has_decorators, has_docstring, has_type_annotations, impact_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                codebase_id,
                func_data.get('name', ''),
                func_data.get('filepath', ''),
                func_data.get('line_count', 0),
                func_data.get('parameter_count', 0),
                func_data.get('cyclomatic_complexity', 0),
                func_data.get('maintainability_index', 0.0),
                func_data.get('documentation_coverage', 0.0),
                func_data.get('test_coverage_estimate', 0.0),
                func_data.get('is_async', False),
                func_data.get('has_decorators', False),
                func_data.get('has_docstring', False),
                func_data.get('has_type_annotations', False),
                func_data.get('impact_score', 0.0)
            ))
    
    def _store_class_metrics(self, conn: sqlite3.Connection, codebase_id: str,
                           class_analysis: List[Dict[str, Any]]):
        """Store class metrics."""
        # Clear existing class data for this codebase
        conn.execute("DELETE FROM classes WHERE codebase_id = ?", (codebase_id,))
        
        for class_data in class_analysis:
            conn.execute("""
                INSERT INTO classes 
                (codebase_id, name, filepath, method_count, attribute_count, inheritance_depth,
                 subclass_count, cohesion_score, coupling_score, documentation_coverage,
                 test_coverage_estimate, has_constructor, has_docstring)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                codebase_id,
                class_data.get('name', ''),
                class_data.get('filepath', ''),
                class_data.get('method_count', 0),
                class_data.get('attribute_count', 0),
                class_data.get('inheritance_depth', 0),
                class_data.get('subclass_count', 0),
                class_data.get('cohesion_score', 0.0),
                class_data.get('coupling_score', 0.0),
                class_data.get('documentation_coverage', 0.0),
                class_data.get('test_coverage_estimate', 0.0),
                class_data.get('has_constructor', False),
                class_data.get('has_docstring', False)
            ))
    
    def _store_call_graph_data(self, conn: sqlite3.Connection, codebase_id: str,
                             call_graph_analysis: Dict[str, Any]):
        """Store call graph data."""
        # Clear existing call graph data
        conn.execute("DELETE FROM function_calls WHERE codebase_id = ?", (codebase_id,))
        
        # Store function calls if available
        patterns = call_graph_analysis.get('patterns', {})
        # This is simplified - in practice you'd extract actual call relationships
        # from the call graph analysis
    
    def _store_dependency_data(self, conn: sqlite3.Connection, codebase_id: str,
                             dependency_analysis: Dict[str, Any]):
        """Store dependency data."""
        # Clear existing dependency data
        conn.execute("DELETE FROM dependencies WHERE codebase_id = ?", (codebase_id,))
        conn.execute("DELETE FROM imports WHERE codebase_id = ?", (codebase_id,))
        
        # Store import analysis if available
        import_analysis = dependency_analysis.get('import_analysis', {})
        # This is simplified - in practice you'd extract actual import relationships
    
    def _store_issues(self, conn: sqlite3.Connection, codebase_id: str,
                     issues: List[Dict[str, Any]]):
        """Store detected issues."""
        # Clear existing issues
        conn.execute("DELETE FROM issues WHERE codebase_id = ?", (codebase_id,))
        
        for issue in issues:
            conn.execute("""
                INSERT INTO issues 
                (codebase_id, issue_type, severity, symbol_name, description, suggestion)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                codebase_id,
                issue.get('type', ''),
                issue.get('severity', ''),
                issue.get('symbol', ''),
                issue.get('description', ''),
                issue.get('suggestion', '')
            ))
    
    # Query methods
    def get_codebase_metrics(self, codebase_id: str) -> Optional[Dict[str, Any]]:
        """Get codebase metrics."""
        try:
            with self._get_connection() as conn:
                row = conn.execute("""
                    SELECT * FROM codebases WHERE id = ?
                """, (codebase_id,)).fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error getting codebase metrics: {e}")
            return None
    
    def get_dead_code_candidates(self, codebase_id: str, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """Query dead code candidates."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT f.name, f.filepath, f.impact_score, f.has_docstring
                    FROM functions f
                    WHERE f.codebase_id = ? AND f.impact_score < 0.1
                    ORDER BY f.impact_score ASC
                """, (codebase_id,)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting dead code candidates: {e}")
            return []
    
    def get_complex_functions(self, codebase_id: str, min_complexity: int = 10) -> List[Dict[str, Any]]:
        """Query complex functions."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT name, filepath, cyclomatic_complexity, maintainability_index, line_count
                    FROM functions 
                    WHERE codebase_id = ? AND cyclomatic_complexity >= ?
                    ORDER BY cyclomatic_complexity DESC
                """, (codebase_id, min_complexity)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting complex functions: {e}")
            return []
    
    def get_recursive_functions(self, codebase_id: str) -> List[Dict[str, Any]]:
        """Query recursive functions."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT DISTINCT fc.caller_function as name
                    FROM function_calls fc
                    WHERE fc.codebase_id = ? AND fc.caller_function = fc.callee_function
                """, (codebase_id,)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting recursive functions: {e}")
            return []
    
    def get_call_graph_data(self, codebase_id: str) -> Dict[str, Any]:
        """Get call graph data."""
        try:
            with self._get_connection() as conn:
                # Get function call relationships
                calls = conn.execute("""
                    SELECT caller_function, callee_function, call_count
                    FROM function_calls 
                    WHERE codebase_id = ?
                """, (codebase_id,)).fetchall()
                
                # Get function metrics for nodes
                functions = conn.execute("""
                    SELECT name, cyclomatic_complexity, impact_score
                    FROM functions 
                    WHERE codebase_id = ?
                """, (codebase_id,)).fetchall()
                
                return {
                    'calls': [dict(row) for row in calls],
                    'functions': [dict(row) for row in functions]
                }
        except Exception as e:
            logger.error(f"Error getting call graph data: {e}")
            return {}
    
    def get_analysis_history(self, codebase_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get analysis history for a codebase."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT timestamp, health_score, total_issues, total_recommendations
                    FROM analysis_reports 
                    WHERE codebase_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (codebase_id, limit)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting analysis history: {e}")
            return []
    
    def get_issues_by_severity(self, codebase_id: str, severity: str = None) -> List[Dict[str, Any]]:
        """Get issues by severity."""
        try:
            with self._get_connection() as conn:
                if severity:
                    rows = conn.execute("""
                        SELECT issue_type, severity, symbol_name, description, suggestion
                        FROM issues 
                        WHERE codebase_id = ? AND severity = ?
                        ORDER BY analyzed_at DESC
                    """, (codebase_id, severity)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT issue_type, severity, symbol_name, description, suggestion
                        FROM issues 
                        WHERE codebase_id = ?
                        ORDER BY 
                            CASE severity 
                                WHEN 'critical' THEN 1
                                WHEN 'high' THEN 2
                                WHEN 'medium' THEN 3
                                WHEN 'low' THEN 4
                                ELSE 5
                            END,
                            analyzed_at DESC
                    """, (codebase_id,)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting issues: {e}")
            return []
    
    def get_function_metrics_summary(self, codebase_id: str) -> Dict[str, Any]:
        """Get function metrics summary."""
        try:
            with self._get_connection() as conn:
                row = conn.execute("""
                    SELECT 
                        COUNT(*) as total_functions,
                        AVG(cyclomatic_complexity) as avg_complexity,
                        AVG(maintainability_index) as avg_maintainability,
                        AVG(documentation_coverage) as avg_documentation,
                        AVG(test_coverage_estimate) as avg_test_coverage,
                        SUM(CASE WHEN has_docstring THEN 1 ELSE 0 END) as documented_functions,
                        SUM(CASE WHEN is_async THEN 1 ELSE 0 END) as async_functions
                    FROM functions 
                    WHERE codebase_id = ?
                """, (codebase_id,)).fetchone()
                
                return dict(row) if row else {}
        except Exception as e:
            logger.error(f"Error getting function metrics summary: {e}")
            return {}
    
    def export_analysis_data(self, codebase_id: str, output_file: str):
        """Export analysis data to JSON file."""
        try:
            data = {
                'codebase_metrics': self.get_codebase_metrics(codebase_id),
                'function_metrics': self.get_function_metrics_summary(codebase_id),
                'complex_functions': self.get_complex_functions(codebase_id),
                'dead_code_candidates': self.get_dead_code_candidates(codebase_id),
                'issues': self.get_issues_by_severity(codebase_id),
                'analysis_history': self.get_analysis_history(codebase_id),
                'call_graph': self.get_call_graph_data(codebase_id)
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Exported analysis data to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting analysis data: {e}")
            raise


# Convenience functions
def create_analysis_database(db_path: str = "analysis.db") -> AnalysisDatabase:
    """Create and initialize analysis database."""
    return AnalysisDatabase(db_path)


def store_analysis_report(report: AnalysisReport, db_path: str = "analysis.db") -> int:
    """Store analysis report in database."""
    db = AnalysisDatabase(db_path)
    return db.store_analysis_report(report)


def query_codebase_metrics(codebase_id: str, db_path: str = "analysis.db") -> Optional[Dict[str, Any]]:
    """Query codebase metrics from database."""
    db = AnalysisDatabase(db_path)
    return db.get_codebase_metrics(codebase_id)


def query_complex_functions(codebase_id: str, min_complexity: int = 10, 
                          db_path: str = "analysis.db") -> List[Dict[str, Any]]:
    """Query complex functions from database."""
    db = AnalysisDatabase(db_path)
    return db.get_complex_functions(codebase_id, min_complexity)


def export_analysis_data(codebase_id: str, output_file: str, db_path: str = "analysis.db"):
    """Export analysis data to file."""
    db = AnalysisDatabase(db_path)
    db.export_analysis_data(codebase_id, output_file)

