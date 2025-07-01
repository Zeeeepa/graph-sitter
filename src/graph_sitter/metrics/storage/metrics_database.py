"""Database storage for metrics data."""

from psycopg2.extras import RealDictCursor
import mysql.connector
import psycopg2

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Any, Tuple
from pathlib import Path

if TYPE_CHECKING:
    from graph_sitter.metrics.models.metrics_data import (
        MetricsData,
        CodebaseMetrics,
        FileMetrics,
        ClassMetrics,
        FunctionMetrics,
        HalsteadMetrics,
    )

logger = logging.getLogger(__name__)

class MetricsDatabase:
    """Database interface for storing and retrieving metrics data.
    
    This class provides a high-level interface for storing metrics data
    in a database, supporting both SQL and NoSQL backends.
    """
    
    def __init__(self, connection_string: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize the metrics database.
        
        Args:
            connection_string: Database connection string.
            config: Configuration options for the database.
        """
        self.connection_string = connection_string
        self.config = config or {}
        self.connection = None
        
        # Database type detection
        if connection_string:
            if connection_string.startswith('postgresql://') or connection_string.startswith('postgres://'):
                self.db_type = 'postgresql'
            elif connection_string.startswith('sqlite://'):
                self.db_type = 'sqlite'
            elif connection_string.startswith('mysql://'):
                self.db_type = 'mysql'
            else:
                self.db_type = 'postgresql'  # Default
        else:
            self.db_type = self.config.get('db_type', 'postgresql')
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """Initialize database connection."""
        try:
            if self.db_type == 'postgresql':
                self._initialize_postgresql()
            elif self.db_type == 'sqlite':
                self._initialize_sqlite()
            elif self.db_type == 'mysql':
                self._initialize_mysql()
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise
    
    def _initialize_postgresql(self) -> None:
        """Initialize PostgreSQL connection."""
        try:
            
            if self.connection_string:
                self.connection = psycopg2.connect(
                    self.connection_string,
                    cursor_factory=RealDictCursor
                )
            else:
                # Use individual connection parameters
                self.connection = psycopg2.connect(
                    host=self.config.get('host', 'localhost'),
                    port=self.config.get('port', 5432),
                    database=self.config.get('database', 'metrics'),
                    user=self.config.get('user', 'postgres'),
                    password=self.config.get('password', ''),
                    cursor_factory=RealDictCursor
                )
            
            self.connection.autocommit = True
            logger.info("PostgreSQL connection established")
            
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise
    
    def _initialize_sqlite(self) -> None:
        """Initialize SQLite connection."""
        try:
            import sqlite3
            
            db_path = self.config.get('database', 'metrics.db')
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row
            
            logger.info(f"SQLite connection established: {db_path}")
            
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {str(e)}")
            raise
    
    def _initialize_mysql(self) -> None:
        """Initialize MySQL connection."""
        try:
            
            if self.connection_string:
                # Parse MySQL connection string
                # This is a simplified parser
                config = {}
                # Implementation would parse the connection string
            else:
                config = {
                    'host': self.config.get('host', 'localhost'),
                    'port': self.config.get('port', 3306),
                    'database': self.config.get('database', 'metrics'),
                    'user': self.config.get('user', 'root'),
                    'password': self.config.get('password', ''),
                }
            
            self.connection = mysql.connector.connect(**config)
            logger.info("MySQL connection established")
            
        except ImportError:
            logger.error("mysql-connector-python not installed. Install with: pip install mysql-connector-python")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            raise
    
    def initialize_schema(self) -> None:
        """Initialize the database schema."""
        try:
            schema_file = Path(__file__).parent.parent / "database" / "schema.sql"
            
            if not schema_file.exists():
                logger.error(f"Schema file not found: {schema_file}")
                return
            
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema creation
            cursor = self.connection.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute(schema_sql)
            else:
                # For SQLite and MySQL, we might need to split and execute statements separately
                statements = schema_sql.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)
            
            if hasattr(self.connection, 'commit'):
                self.connection.commit()
            
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {str(e)}")
            raise
    
    def store_metrics_data(self, metrics_data: MetricsData) -> int:
        """Store complete metrics data in the database.
        
        Args:
            metrics_data: Complete metrics data to store.
            
        Returns:
            ID of the stored codebase metrics record.
        """
        try:
            cursor = self.connection.cursor()
            
            # Store codebase metrics first
            codebase_id = self._store_codebase_metrics(cursor, metrics_data.codebase_metrics)
            
            # Store file metrics
            for file_path, file_metrics in metrics_data.file_metrics.items():
                file_id = self._store_file_metrics(cursor, codebase_id, file_metrics)
                
                # Store class metrics for this file
                if file_path in metrics_data.class_metrics:
                    for class_metrics in metrics_data.class_metrics[file_path]:
                        class_id = self._store_class_metrics(cursor, file_id, class_metrics)
                
                # Store function metrics for this file
                if file_path in metrics_data.function_metrics:
                    for function_metrics in metrics_data.function_metrics[file_path]:
                        function_id = self._store_function_metrics(cursor, file_id, function_metrics)
            
            if hasattr(self.connection, 'commit'):
                self.connection.commit()
            
            logger.info(f"Stored metrics data for project {metrics_data.codebase_metrics.project_name}")
            return codebase_id
            
        except Exception as e:
            if hasattr(self.connection, 'rollback'):
                self.connection.rollback()
            logger.error(f"Failed to store metrics data: {str(e)}")
            raise
    
    def _store_codebase_metrics(self, cursor, codebase_metrics: CodebaseMetrics) -> int:
        """Store codebase metrics."""
        sql = """
        INSERT INTO codebase_metrics (
            project_name, git_commit_hash, calculated_at,
            total_files, total_lines, total_logical_lines, total_source_lines,
            total_comment_lines, total_blank_lines,
            total_cyclomatic_complexity, average_cyclomatic_complexity,
            total_halstead_volume, average_maintainability_index,
            total_classes, total_functions, total_imports, total_global_vars, total_interfaces,
            dead_code_files, test_files, average_test_coverage,
            comment_ratio, test_file_ratio, language_distribution,
            calculation_duration, errors_count, warnings_count
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
        """
        
        # Adapt SQL for different databases
        if self.db_type == 'sqlite':
            sql = sql.replace('%s', '?').replace('RETURNING id', '')
        elif self.db_type == 'mysql':
            sql = sql.replace('RETURNING id', '')
        
        values = (
            codebase_metrics.project_name,
            codebase_metrics.git_commit_hash,
            codebase_metrics.calculated_at,
            codebase_metrics.total_files,
            codebase_metrics.total_lines,
            codebase_metrics.total_logical_lines,
            codebase_metrics.total_source_lines,
            codebase_metrics.total_comment_lines,
            codebase_metrics.total_blank_lines,
            codebase_metrics.total_cyclomatic_complexity,
            codebase_metrics.average_cyclomatic_complexity,
            codebase_metrics.total_halstead_volume,
            codebase_metrics.average_maintainability_index,
            codebase_metrics.total_classes,
            codebase_metrics.total_functions,
            codebase_metrics.total_imports,
            codebase_metrics.total_global_vars,
            codebase_metrics.total_interfaces,
            codebase_metrics.dead_code_files,
            codebase_metrics.test_files,
            codebase_metrics.average_test_coverage,
            codebase_metrics.comment_ratio,
            codebase_metrics.test_file_ratio,
            json.dumps(codebase_metrics.language_distribution),
            0.0,  # calculation_duration - would come from MetricsData
            0,    # errors_count - would come from MetricsData
            0,    # warnings_count - would come from MetricsData
        )
        
        cursor.execute(sql, values)
        
        if self.db_type == 'postgresql':
            return cursor.fetchone()['id']
        else:
            return cursor.lastrowid
    
    def _store_file_metrics(self, cursor, codebase_id: int, file_metrics: FileMetrics) -> int:
        """Store file metrics."""
        sql = """
        INSERT INTO file_metrics (
            codebase_metrics_id, file_path, language, calculated_at,
            cyclomatic_complexity, maintainability_index,
            total_lines, logical_lines, source_lines, comment_lines, blank_lines,
            class_count, function_count, import_count, global_var_count, interface_count,
            has_dead_code, test_coverage, is_test_file, comment_ratio
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
        """
        
        if self.db_type == 'sqlite':
            sql = sql.replace('%s', '?').replace('RETURNING id', '')
        elif self.db_type == 'mysql':
            sql = sql.replace('RETURNING id', '')
        
        values = (
            codebase_id,
            file_metrics.file_path,
            file_metrics.language,
            file_metrics.calculated_at,
            file_metrics.cyclomatic_complexity,
            file_metrics.maintainability_index,
            file_metrics.total_lines,
            file_metrics.logical_lines,
            file_metrics.source_lines,
            file_metrics.comment_lines,
            file_metrics.blank_lines,
            file_metrics.class_count,
            file_metrics.function_count,
            file_metrics.import_count,
            file_metrics.global_var_count,
            file_metrics.interface_count,
            file_metrics.has_dead_code,
            file_metrics.test_coverage,
            file_metrics.is_test_file,
            file_metrics.comment_ratio,
        )
        
        cursor.execute(sql, values)
        
        if self.db_type == 'postgresql':
            return cursor.fetchone()['id']
        else:
            return cursor.lastrowid
    
    def _store_halstead_metrics(self, cursor, halstead_metrics: HalsteadMetrics) -> int:
        """Store Halstead metrics."""
        sql = """
        INSERT INTO halstead_metrics (
            n1, n2, N1, N2, volume, difficulty, effort
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
        """
        
        if self.db_type == 'sqlite':
            sql = sql.replace('%s', '?').replace('RETURNING id', '')
        elif self.db_type == 'mysql':
            sql = sql.replace('RETURNING id', '')
        
        values = (
            halstead_metrics.n1,
            halstead_metrics.n2,
            halstead_metrics.N1,
            halstead_metrics.N2,
            halstead_metrics.volume,
            halstead_metrics.difficulty,
            halstead_metrics.effort,
        )
        
        cursor.execute(sql, values)
        
        if self.db_type == 'postgresql':
            return cursor.fetchone()['id']
        else:
            return cursor.lastrowid
    
    def _store_class_metrics(self, cursor, file_id: int, class_metrics: ClassMetrics) -> int:
        """Store class metrics."""
        # Store Halstead metrics first
        halstead_id = self._store_halstead_metrics(cursor, class_metrics.halstead)
        
        sql = """
        INSERT INTO class_metrics (
            file_metrics_id, halstead_metrics_id, class_name, start_line, end_line, calculated_at,
            cyclomatic_complexity, maintainability_index,
            total_lines, logical_lines, source_lines, comment_lines, blank_lines,
            method_count, attribute_count, depth_of_inheritance, number_of_children,
            has_dead_methods, comment_ratio
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
        """
        
        if self.db_type == 'sqlite':
            sql = sql.replace('%s', '?').replace('RETURNING id', '')
        elif self.db_type == 'mysql':
            sql = sql.replace('RETURNING id', '')
        
        values = (
            file_id,
            halstead_id,
            class_metrics.name,
            class_metrics.start_line,
            class_metrics.end_line,
            class_metrics.calculated_at,
            class_metrics.cyclomatic_complexity,
            class_metrics.maintainability_index,
            class_metrics.total_lines,
            class_metrics.logical_lines,
            class_metrics.source_lines,
            class_metrics.comment_lines,
            class_metrics.blank_lines,
            class_metrics.method_count,
            class_metrics.attribute_count,
            class_metrics.depth_of_inheritance,
            class_metrics.number_of_children,
            class_metrics.has_dead_methods,
            class_metrics.comment_ratio,
        )
        
        cursor.execute(sql, values)
        
        if self.db_type == 'postgresql':
            return cursor.fetchone()['id']
        else:
            return cursor.lastrowid
    
    def _store_function_metrics(self, cursor, file_id: int, function_metrics: FunctionMetrics) -> int:
        """Store function metrics."""
        # Store Halstead metrics first
        halstead_id = self._store_halstead_metrics(cursor, function_metrics.halstead)
        
        sql = """
        INSERT INTO function_metrics (
            file_metrics_id, halstead_metrics_id, function_name, start_line, end_line, calculated_at,
            cyclomatic_complexity, maintainability_index,
            total_lines, logical_lines, source_lines, comment_lines, blank_lines,
            parameter_count, return_statement_count, function_call_count, nesting_depth,
            is_recursive, is_dead_code, has_unused_parameters,
            call_site_count, dependency_count, comment_ratio, complexity_per_line
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
        """
        
        if self.db_type == 'sqlite':
            sql = sql.replace('%s', '?').replace('RETURNING id', '')
        elif self.db_type == 'mysql':
            sql = sql.replace('RETURNING id', '')
        
        values = (
            file_id,
            halstead_id,
            function_metrics.name,
            function_metrics.start_line,
            function_metrics.end_line,
            function_metrics.calculated_at,
            function_metrics.cyclomatic_complexity,
            function_metrics.maintainability_index,
            function_metrics.total_lines,
            function_metrics.logical_lines,
            function_metrics.source_lines,
            function_metrics.comment_lines,
            function_metrics.blank_lines,
            function_metrics.parameter_count,
            function_metrics.return_statement_count,
            function_metrics.function_call_count,
            function_metrics.nesting_depth,
            function_metrics.is_recursive,
            function_metrics.is_dead_code,
            function_metrics.has_unused_parameters,
            function_metrics.call_site_count,
            function_metrics.dependency_count,
            function_metrics.comment_ratio,
            function_metrics.complexity_per_line,
        )
        
        cursor.execute(sql, values)
        
        if self.db_type == 'postgresql':
            return cursor.fetchone()['id']
        else:
            return cursor.lastrowid
    
    def get_latest_metrics(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get the latest metrics for a project.
        
        Args:
            project_name: Name of the project.
            
        Returns:
            Dictionary with latest metrics or None if not found.
        """
        try:
            cursor = self.connection.cursor()
            
            sql = """
            SELECT * FROM latest_codebase_metrics 
            WHERE project_name = %s
            """
            
            if self.db_type in ['sqlite', 'mysql']:
                sql = sql.replace('%s', '?')
            
            cursor.execute(sql, (project_name,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest metrics for {project_name}: {str(e)}")
            return None
    
    def get_metrics_history(
        self, 
        project_name: str, 
        days: int = 30,
        metric_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics history for a project.
        
        Args:
            project_name: Name of the project.
            days: Number of days of history to retrieve.
            metric_names: Specific metrics to retrieve (optional).
            
        Returns:
            List of historical metrics data.
        """
        try:
            cursor = self.connection.cursor()
            
            if metric_names:
                placeholders = ', '.join(['%s'] * len(metric_names))
                sql = f"""
                SELECT * FROM metrics_trends 
                WHERE project_name = %s 
                AND calculated_at >= NOW() - INTERVAL '{days} days'
                AND metric_name IN ({placeholders})
                ORDER BY calculated_at DESC
                """
                values = [project_name] + metric_names
            else:
                sql = f"""
                SELECT * FROM codebase_metrics 
                WHERE project_name = %s 
                AND calculated_at >= NOW() - INTERVAL '{days} days'
                ORDER BY calculated_at DESC
                """
                values = [project_name]
            
            if self.db_type == 'sqlite':
                sql = sql.replace('%s', '?').replace("NOW() - INTERVAL '{days} days'", f"datetime('now', '-{days} days')")
            elif self.db_type == 'mysql':
                sql = sql.replace("NOW() - INTERVAL '{days} days'", f"NOW() - INTERVAL {days} DAY")
            
            cursor.execute(sql, values)
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get metrics history for {project_name}: {str(e)}")
            return []
    
    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
