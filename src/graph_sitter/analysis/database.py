"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import sqlite3

Database schema and storage layer for comprehensive codebase analysis.

This module implements the database layer for storing analysis results,
following the patterns identified from graph-sitter.com documentation.
"""

@dataclass
class CodebaseRecord:
    """Database record for codebase-level analysis."""
    id: Optional[int] = None
    path: str = ""
    name: str = ""
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    total_symbols: int = 0
    analysis_timestamp: str = ""
    metadata: str = "{}"  # JSON string for additional data

@dataclass
class FileRecord:
    """Database record for file-level analysis."""
    id: Optional[int] = None
    codebase_id: int = 0
    filepath: str = ""
    filename: str = ""
    file_type: str = ""
    lines_of_code: int = 0
    functions_count: int = 0
    classes_count: int = 0
    imports_count: int = 0
    complexity_score: float = 0.0
    maintainability_index: float = 0.0
    metadata: str = "{}"

@dataclass
class FunctionRecord:
    """Database record for function-level analysis."""
    id: Optional[int] = None
    file_id: int = 0
    name: str = ""
    qualified_name: str = ""
    start_line: int = 0
    end_line: int = 0
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    parameters_count: int = 0
    return_statements_count: int = 0
    call_sites_count: int = 0
    function_calls_count: int = 0
    is_recursive: bool = False
    is_async: bool = False
    is_generator: bool = False
    docstring: str = ""
    metadata: str = "{}"

@dataclass
class ClassRecord:
    """Database record for class-level analysis."""
    id: Optional[int] = None
    file_id: int = 0
    name: str = ""
    qualified_name: str = ""
    start_line: int = 0
    end_line: int = 0
    methods_count: int = 0
    attributes_count: int = 0
    inheritance_depth: int = 0
    parent_classes: str = "[]"  # JSON array
    child_classes: str = "[]"   # JSON array
    is_abstract: bool = False
    docstring: str = ""
    metadata: str = "{}"

@dataclass
class FunctionCallRecord:
    """Database record for function call analysis."""
    id: Optional[int] = None
    caller_function_id: int = 0
    called_function_id: Optional[int] = None
    call_name: str = ""
    call_line: int = 0
    call_column: int = 0
    arguments_count: int = 0
    is_method_call: bool = False
    is_external_call: bool = False
    call_chain_position: int = 0
    metadata: str = "{}"

@dataclass
class DependencyRecord:
    """Database record for dependency relationships."""
    id: Optional[int] = None
    source_symbol_id: int = 0
    target_symbol_id: int = 0
    dependency_type: str = ""  # 'import', 'call', 'inheritance', 'usage'
    strength: float = 1.0
    metadata: str = "{}"

@dataclass
class ImportRecord:
    """Database record for import analysis."""
    id: Optional[int] = None
    file_id: int = 0
    import_name: str = ""
    import_type: str = ""  # 'module', 'from', 'relative'
    imported_symbols: str = "[]"  # JSON array
    is_external: bool = False
    import_line: int = 0
    metadata: str = "{}"

class AnalysisDatabase:
    """
    Database layer for storing and retrieving codebase analysis results.
    
    Provides comprehensive storage for all analysis data following
    graph-sitter.com API patterns.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        """Initialize database connection and create schema."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()
    
    def _create_schema(self):
        """Create database schema for analysis storage."""
        schema_sql = """
        -- Codebase table
        CREATE TABLE IF NOT EXISTS codebases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            total_files INTEGER DEFAULT 0,
            total_functions INTEGER DEFAULT 0,
            total_classes INTEGER DEFAULT 0,
            total_imports INTEGER DEFAULT 0,
            total_symbols INTEGER DEFAULT 0,
            analysis_timestamp TEXT NOT NULL,
            metadata TEXT DEFAULT '{}'
        );
        
        -- Files table
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codebase_id INTEGER NOT NULL,
            filepath TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            lines_of_code INTEGER DEFAULT 0,
            functions_count INTEGER DEFAULT 0,
            classes_count INTEGER DEFAULT 0,
            imports_count INTEGER DEFAULT 0,
            complexity_score REAL DEFAULT 0.0,
            maintainability_index REAL DEFAULT 0.0,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (codebase_id) REFERENCES codebases (id),
            UNIQUE(codebase_id, filepath)
        );
        
        -- Functions table
        CREATE TABLE IF NOT EXISTS functions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            qualified_name TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            lines_of_code INTEGER DEFAULT 0,
            cyclomatic_complexity INTEGER DEFAULT 1,
            parameters_count INTEGER DEFAULT 0,
            return_statements_count INTEGER DEFAULT 0,
            call_sites_count INTEGER DEFAULT 0,
            function_calls_count INTEGER DEFAULT 0,
            is_recursive BOOLEAN DEFAULT FALSE,
            is_async BOOLEAN DEFAULT FALSE,
            is_generator BOOLEAN DEFAULT FALSE,
            docstring TEXT DEFAULT '',
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (file_id) REFERENCES files (id),
            UNIQUE(file_id, qualified_name)
        );
        
        -- Classes table
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            qualified_name TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            methods_count INTEGER DEFAULT 0,
            attributes_count INTEGER DEFAULT 0,
            inheritance_depth INTEGER DEFAULT 0,
            parent_classes TEXT DEFAULT '[]',
            child_classes TEXT DEFAULT '[]',
            is_abstract BOOLEAN DEFAULT FALSE,
            docstring TEXT DEFAULT '',
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (file_id) REFERENCES files (id),
            UNIQUE(file_id, qualified_name)
        );
        
        -- Function calls table
        CREATE TABLE IF NOT EXISTS function_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caller_function_id INTEGER NOT NULL,
            called_function_id INTEGER,
            call_name TEXT NOT NULL,
            call_line INTEGER NOT NULL,
            call_column INTEGER DEFAULT 0,
            arguments_count INTEGER DEFAULT 0,
            is_method_call BOOLEAN DEFAULT FALSE,
            is_external_call BOOLEAN DEFAULT FALSE,
            call_chain_position INTEGER DEFAULT 0,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (caller_function_id) REFERENCES functions (id),
            FOREIGN KEY (called_function_id) REFERENCES functions (id)
        );
        
        -- Dependencies table
        CREATE TABLE IF NOT EXISTS dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_symbol_id INTEGER NOT NULL,
            target_symbol_id INTEGER NOT NULL,
            dependency_type TEXT NOT NULL,
            strength REAL DEFAULT 1.0,
            metadata TEXT DEFAULT '{}'
        );
        
        -- Imports table
        CREATE TABLE IF NOT EXISTS imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            import_name TEXT NOT NULL,
            import_type TEXT NOT NULL,
            imported_symbols TEXT DEFAULT '[]',
            is_external BOOLEAN DEFAULT FALSE,
            import_line INTEGER NOT NULL,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (file_id) REFERENCES files (id)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_files_codebase ON files(codebase_id);
        CREATE INDEX IF NOT EXISTS idx_functions_file ON functions(file_id);
        CREATE INDEX IF NOT EXISTS idx_classes_file ON classes(file_id);
        CREATE INDEX IF NOT EXISTS idx_function_calls_caller ON function_calls(caller_function_id);
        CREATE INDEX IF NOT EXISTS idx_function_calls_called ON function_calls(called_function_id);
        CREATE INDEX IF NOT EXISTS idx_dependencies_source ON dependencies(source_symbol_id);
        CREATE INDEX IF NOT EXISTS idx_dependencies_target ON dependencies(target_symbol_id);
        CREATE INDEX IF NOT EXISTS idx_imports_file ON imports(file_id);
        """
        
        self.conn.executescript(schema_sql)
        self.conn.commit()
    
    def store_codebase(self, record: CodebaseRecord) -> int:
        """Store codebase analysis record."""
        sql = """
        INSERT OR REPLACE INTO codebases 
        (path, name, total_files, total_functions, total_classes, 
         total_imports, total_symbols, analysis_timestamp, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.conn.execute(sql, (
            record.path, record.name, record.total_files, record.total_functions,
            record.total_classes, record.total_imports, record.total_symbols,
            record.analysis_timestamp, record.metadata
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def store_file(self, record: FileRecord) -> int:
        """Store file analysis record."""
        sql = """
        INSERT OR REPLACE INTO files 
        (codebase_id, filepath, filename, file_type, lines_of_code,
         functions_count, classes_count, imports_count, complexity_score,
         maintainability_index, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.conn.execute(sql, (
            record.codebase_id, record.filepath, record.filename, record.file_type,
            record.lines_of_code, record.functions_count, record.classes_count,
            record.imports_count, record.complexity_score, record.maintainability_index,
            record.metadata
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def store_function(self, record: FunctionRecord) -> int:
        """Store function analysis record."""
        sql = """
        INSERT OR REPLACE INTO functions 
        (file_id, name, qualified_name, start_line, end_line, lines_of_code,
         cyclomatic_complexity, parameters_count, return_statements_count,
         call_sites_count, function_calls_count, is_recursive, is_async,
         is_generator, docstring, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.conn.execute(sql, (
            record.file_id, record.name, record.qualified_name, record.start_line,
            record.end_line, record.lines_of_code, record.cyclomatic_complexity,
            record.parameters_count, record.return_statements_count,
            record.call_sites_count, record.function_calls_count, record.is_recursive,
            record.is_async, record.is_generator, record.docstring, record.metadata
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def store_class(self, record: ClassRecord) -> int:
        """Store class analysis record."""
        sql = """
        INSERT OR REPLACE INTO classes 
        (file_id, name, qualified_name, start_line, end_line, methods_count,
         attributes_count, inheritance_depth, parent_classes, child_classes,
         is_abstract, docstring, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.conn.execute(sql, (
            record.file_id, record.name, record.qualified_name, record.start_line,
            record.end_line, record.methods_count, record.attributes_count,
            record.inheritance_depth, record.parent_classes, record.child_classes,
            record.is_abstract, record.docstring, record.metadata
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_codebase_metrics(self, codebase_id: int) -> Dict[str, Any]:
        """Get comprehensive metrics for a codebase."""
        sql = """
        SELECT 
            c.*,
            COUNT(DISTINCT f.id) as actual_files,
            COUNT(DISTINCT func.id) as actual_functions,
            COUNT(DISTINCT cls.id) as actual_classes,
            AVG(f.complexity_score) as avg_file_complexity,
            AVG(f.maintainability_index) as avg_maintainability,
            AVG(func.cyclomatic_complexity) as avg_function_complexity
        FROM codebases c
        LEFT JOIN files f ON c.id = f.codebase_id
        LEFT JOIN functions func ON f.id = func.file_id
        LEFT JOIN classes cls ON f.id = cls.file_id
        WHERE c.id = ?
        GROUP BY c.id
        """
        row = self.conn.execute(sql, (codebase_id,)).fetchone()
        return dict(row) if row else {}
    
    def get_dead_code_candidates(self, codebase_id: int) -> List[Dict[str, Any]]:
        """Find functions with no call sites (potential dead code)."""
        sql = """
        SELECT f.id, f.name, f.qualified_name, files.filepath, f.start_line
        FROM functions f
        JOIN files ON f.file_id = files.id
        WHERE files.codebase_id = ? AND f.call_sites_count = 0
        ORDER BY files.filepath, f.start_line
        """
        rows = self.conn.execute(sql, (codebase_id,)).fetchall()
        return [dict(row) for row in rows]
    
    def get_recursive_functions(self, codebase_id: int) -> List[Dict[str, Any]]:
        """Find recursive functions in the codebase."""
        sql = """
        SELECT f.id, f.name, f.qualified_name, files.filepath, f.start_line
        FROM functions f
        JOIN files ON f.file_id = files.id
        WHERE files.codebase_id = ? AND f.is_recursive = TRUE
        ORDER BY files.filepath, f.start_line
        """
        rows = self.conn.execute(sql, (codebase_id,)).fetchall()
        return [dict(row) for row in rows]
    
    def get_complex_functions(self, codebase_id: int, min_complexity: int = 10) -> List[Dict[str, Any]]:
        """Find functions with high cyclomatic complexity."""
        sql = """
        SELECT f.id, f.name, f.qualified_name, files.filepath, 
               f.start_line, f.cyclomatic_complexity
        FROM functions f
        JOIN files ON f.file_id = files.id
        WHERE files.codebase_id = ? AND f.cyclomatic_complexity >= ?
        ORDER BY f.cyclomatic_complexity DESC
        """
        rows = self.conn.execute(sql, (codebase_id, min_complexity)).fetchall()
        return [dict(row) for row in rows]
    
    def get_call_graph_data(self, codebase_id: int) -> List[Dict[str, Any]]:
        """Get call graph data for visualization."""
        sql = """
        SELECT 
            caller.qualified_name as caller,
            called.qualified_name as called,
            fc.call_name,
            fc.is_external_call,
            caller_file.filepath as caller_file,
            called_file.filepath as called_file
        FROM function_calls fc
        JOIN functions caller ON fc.caller_function_id = caller.id
        LEFT JOIN functions called ON fc.called_function_id = called.id
        JOIN files caller_file ON caller.file_id = caller_file.id
        LEFT JOIN files called_file ON called.file_id = called_file.id
        WHERE caller_file.codebase_id = ?
        """
        rows = self.conn.execute(sql, (codebase_id,)).fetchall()
        return [dict(row) for row in rows]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
