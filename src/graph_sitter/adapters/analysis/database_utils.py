"""
Database utilities for graph-sitter analysis integration.

This module provides database-specific utilities for result set conversion
and query execution that can be used across different analysis modules.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


def convert_rset_to_dicts(cursor, results) -> List[Dict[str, Any]]:
    """
    Convert database result set to list of dictionaries.
    
    This function handles different database drivers that return result sets
    in various formats (tuples, Row objects, etc.) and converts them to
    a standardized dictionary format.
    
    Args:
        cursor: Database cursor object with column description
        results: Result set from cursor.fetchall()
        
    Returns:
        List of dictionaries with column names as keys
    """
    if not results:
        return []
    
    # Try to convert directly if rows support dict conversion (e.g., sqlite3.Row)
    try:
        first_row = results[0]
        if hasattr(first_row, 'keys'):
            # Row object with dict-like interface (e.g., sqlite3.Row)
            return [dict(row) for row in results]
        elif hasattr(first_row, '_asdict'):
            # Named tuple with _asdict method
            return [row._asdict() for row in results]
    except (TypeError, AttributeError):
        pass
    
    # Fallback: use cursor.description to map column names to values
    try:
        if hasattr(cursor, 'description') and cursor.description:
            column_names = [desc[0] for desc in cursor.description]
            return [dict(zip(column_names, row)) for row in results]
    except (TypeError, AttributeError):
        pass
    
    # Last resort: return as-is if conversion fails
    # This maintains backward compatibility but may not be ideal
    return results


def execute_query_with_rset_conversion(cursor, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Execute a query and return results as a list of dictionaries.
    
    This is a convenience function that combines query execution with
    result set conversion for better database compatibility.
    
    Args:
        cursor: Database cursor object
        query: SQL query string
        params: Query parameters tuple
        
    Returns:
        List of dictionaries with query results
    """
    cursor.execute(query, params)
    results = cursor.fetchall()
    return convert_rset_to_dicts(cursor, results)


@dataclass
class AnalysisResult:
    """Enhanced analysis result with database integration"""
    id: str
    codebase_id: str
    summary: str
    metrics: Dict[str, Any]
    quality_score: float
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    created_at: datetime


@dataclass
class DatabaseMetrics:
    """Database-specific metrics for codebase analysis"""
    total_files: int
    total_functions: int
    total_classes: int
    total_lines: int
    complexity_score: float
    maintainability_index: float
    technical_debt_ratio: float
    test_coverage: float
    languages: Dict[str, int]


class DatabaseQueryBuilder:
    """Helper class for building common analysis queries"""
    
    @staticmethod
    def get_historical_analysis_query() -> str:
        """Get query for historical analysis results"""
        return """
        SELECT 
            ar.id,
            ar.created_at,
            ar.quality_score,
            ar.metrics,
            ar.total_issues,
            ar.critical_issues,
            ar.analysis_duration_ms
        FROM analysis_runs ar
        WHERE ar.codebase_id = %s
        AND ar.created_at >= NOW() - INTERVAL '%s days'
        ORDER BY ar.created_at DESC
        """
    
    @staticmethod
    def get_quality_trends_query() -> str:
        """Get query for quality trends"""
        return """
        SELECT 
            DATE(ar.created_at) as analysis_date,
            AVG(ar.quality_score) as avg_quality_score,
            COUNT(*) as analysis_count,
            AVG(ar.total_issues) as avg_issues
        FROM analysis_runs ar
        WHERE ar.organization_id = %s
        AND ar.created_at >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(ar.created_at)
        ORDER BY analysis_date DESC
        """
    
    @staticmethod
    def get_codebase_metrics_query() -> str:
        """Get query for codebase metrics"""
        return """
        SELECT 
            c.id,
            c.name,
            c.repository_url,
            COUNT(DISTINCT f.id) as file_count,
            COUNT(DISTINCT fn.id) as function_count,
            COUNT(DISTINCT cl.id) as class_count,
            SUM(f.line_count) as total_lines
        FROM codebases c
        LEFT JOIN files f ON c.id = f.codebase_id
        LEFT JOIN functions fn ON f.id = fn.file_id
        LEFT JOIN classes cl ON f.id = cl.file_id
        WHERE c.organization_id = %s
        GROUP BY c.id, c.name, c.repository_url
        """


class DatabaseConnection:
    """Database connection wrapper with analysis-specific utilities"""
    
    def __init__(self, connection):
        """
        Initialize with a database connection.
        
        Args:
            connection: Database connection object
        """
        self.connection = connection
    
    def execute_analysis_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute an analysis query and return standardized results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries with query results
        """
        with self.connection.cursor() as cursor:
            return execute_query_with_rset_conversion(cursor, query, params)
    
    def get_historical_analysis(self, codebase_id: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical analysis results for a codebase.
        
        Args:
            codebase_id: Codebase identifier
            days_back: Number of days to look back
            
        Returns:
            List of historical analysis results
        """
        query = DatabaseQueryBuilder.get_historical_analysis_query()
        return self.execute_analysis_query(query, (codebase_id, days_back))
    
    def get_quality_trends(self, organization_id: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get quality trends for an organization.
        
        Args:
            organization_id: Organization identifier
            days_back: Number of days to look back
            
        Returns:
            List of quality trend data
        """
        query = DatabaseQueryBuilder.get_quality_trends_query()
        return self.execute_analysis_query(query, (organization_id, days_back))
    
    def store_analysis_result(self, result: AnalysisResult) -> bool:
        """
        Store an analysis result in the database.
        
        Args:
            result: AnalysisResult to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.connection.cursor() as cursor:
                query = """
                INSERT INTO analysis_runs (
                    id, codebase_id, summary, metrics, quality_score,
                    total_issues, critical_issues, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    result.id,
                    result.codebase_id,
                    result.summary,
                    result.metrics,
                    result.quality_score,
                    len(result.issues),
                    len([i for i in result.issues if i.get('severity') == 'critical']),
                    result.created_at
                ))
                self.connection.commit()
                return True
        except Exception as e:
            print(f"Error storing analysis result: {e}")
            return False

