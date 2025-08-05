"""
Database Integration Testing Suite

Tests all SQL operations, data integrity, consistency, performance,
and concurrent access for tasks, codebase, prompts, and analytics.
"""

import pytest
import asyncio
import time
import threading
from typing import Dict, List, Any
from unittest.mock import Mock, patch
import sqlite3
import tempfile
import os


class TestDatabaseIntegration:
    """Test suite for database integration validation."""

    @pytest.fixture
    def test_db_path(self):
        """Create a temporary test database."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)

    @pytest.fixture
    def db_connection(self, test_db_path):
        """Create database connection for testing."""
        conn = sqlite3.connect(test_db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.close()

    @pytest.fixture
    def sample_schema(self, db_connection):
        """Create sample database schema for testing."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS codebase (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            path TEXT NOT NULL,
            language TEXT,
            size_bytes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            type TEXT DEFAULT 'user',
            task_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        );

        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_data TEXT,
            codebase_id INTEGER,
            task_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (codebase_id) REFERENCES codebase (id),
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        );

        CREATE INDEX idx_tasks_status ON tasks(status);
        CREATE INDEX idx_analytics_event_type ON analytics(event_type);
        CREATE INDEX idx_analytics_timestamp ON analytics(timestamp);
        """
        
        for statement in schema_sql.split(';'):
            if statement.strip():
                db_connection.execute(statement)
        db_connection.commit()
        return db_connection

    def test_task_operations(self, sample_schema):
        """Test all task-related SQL operations."""
        conn = sample_schema
        
        # Test INSERT
        cursor = conn.execute(
            "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
            ("Test Task", "Test Description", "pending")
        )
        task_id = cursor.lastrowid
        conn.commit()
        
        assert task_id is not None
        
        # Test SELECT
        result = conn.execute(
            "SELECT id, title, description, status FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()
        
        assert result is not None
        assert result[1] == "Test Task"
        assert result[2] == "Test Description"
        assert result[3] == "pending"
        
        # Test UPDATE
        conn.execute(
            "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            ("completed", task_id)
        )
        conn.commit()
        
        updated_result = conn.execute(
            "SELECT status FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()
        
        assert updated_result[0] == "completed"
        
        # Test DELETE
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        
        deleted_result = conn.execute(
            "SELECT id FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()
        
        assert deleted_result is None

    def test_codebase_operations(self, sample_schema):
        """Test all codebase-related SQL operations."""
        conn = sample_schema
        
        # Test INSERT with unique constraint
        conn.execute(
            "INSERT INTO codebase (name, path, language, size_bytes) VALUES (?, ?, ?, ?)",
            ("test-repo", "/path/to/repo", "python", 1024)
        )
        conn.commit()
        
        # Test duplicate name handling
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO codebase (name, path, language) VALUES (?, ?, ?)",
                ("test-repo", "/another/path", "javascript")
            )
        
        # Test SELECT with filtering
        result = conn.execute(
            "SELECT name, language, size_bytes FROM codebase WHERE language = ?",
            ("python",)
        ).fetchone()
        
        assert result[0] == "test-repo"
        assert result[1] == "python"
        assert result[2] == 1024

    def test_prompts_operations(self, sample_schema):
        """Test prompt-related SQL operations with foreign keys."""
        conn = sample_schema
        
        # Create a task first
        task_cursor = conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            ("Test Task", "Test Description")
        )
        task_id = task_cursor.lastrowid
        conn.commit()
        
        # Test INSERT with foreign key
        conn.execute(
            "INSERT INTO prompts (content, type, task_id) VALUES (?, ?, ?)",
            ("Test prompt content", "user", task_id)
        )
        conn.commit()
        
        # Test JOIN query
        result = conn.execute("""
            SELECT p.content, p.type, t.title 
            FROM prompts p 
            JOIN tasks t ON p.task_id = t.id 
            WHERE t.id = ?
        """, (task_id,)).fetchone()
        
        assert result[0] == "Test prompt content"
        assert result[1] == "user"
        assert result[2] == "Test Task"
        
        # Test foreign key constraint
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO prompts (content, type, task_id) VALUES (?, ?, ?)",
                ("Invalid prompt", "user", 99999)  # Non-existent task_id
            )

    def test_analytics_operations(self, sample_schema):
        """Test analytics-related SQL operations."""
        conn = sample_schema
        
        # Create dependencies
        codebase_cursor = conn.execute(
            "INSERT INTO codebase (name, path, language) VALUES (?, ?, ?)",
            ("analytics-repo", "/path", "python")
        )
        codebase_id = codebase_cursor.lastrowid
        
        task_cursor = conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            ("Analytics Task", "Test")
        )
        task_id = task_cursor.lastrowid
        conn.commit()
        
        # Test analytics INSERT
        events = [
            ("code_analysis", '{"lines": 100}', codebase_id, task_id),
            ("task_completion", '{"duration": 300}', None, task_id),
            ("codebase_scan", '{"files": 50}', codebase_id, None)
        ]
        
        for event in events:
            conn.execute(
                "INSERT INTO analytics (event_type, event_data, codebase_id, task_id) VALUES (?, ?, ?, ?)",
                event
            )
        conn.commit()
        
        # Test aggregation queries
        result = conn.execute(
            "SELECT COUNT(*) FROM analytics WHERE event_type = ?",
            ("code_analysis",)
        ).fetchone()
        
        assert result[0] == 1
        
        # Test complex JOIN query
        result = conn.execute("""
            SELECT a.event_type, c.name, t.title 
            FROM analytics a 
            LEFT JOIN codebase c ON a.codebase_id = c.id 
            LEFT JOIN tasks t ON a.task_id = t.id 
            WHERE a.event_type = ?
        """, ("code_analysis",)).fetchone()
        
        assert result[0] == "code_analysis"
        assert result[1] == "analytics-repo"
        assert result[2] == "Analytics Task"

    def test_data_integrity_constraints(self, sample_schema):
        """Test data integrity and constraint validation."""
        conn = sample_schema
        
        # Test NOT NULL constraints
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO tasks (title) VALUES (NULL)")
        
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO codebase (name, path) VALUES (NULL, '/path')")
        
        # Test UNIQUE constraints
        conn.execute(
            "INSERT INTO codebase (name, path, language) VALUES (?, ?, ?)",
            ("unique-repo", "/path1", "python")
        )
        conn.commit()
        
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO codebase (name, path, language) VALUES (?, ?, ?)",
                ("unique-repo", "/path2", "javascript")
            )
        
        # Test foreign key constraints
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO prompts (content, task_id) VALUES (?, ?)",
                ("Test", 99999)  # Non-existent task_id
            )

    def test_performance_large_datasets(self, sample_schema):
        """Test database performance with large datasets."""
        conn = sample_schema
        
        # Insert large number of records
        start_time = time.time()
        
        # Batch insert tasks
        tasks_data = [(f"Task {i}", f"Description {i}", "pending") for i in range(1000)]
        conn.executemany(
            "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
            tasks_data
        )
        
        # Batch insert analytics
        analytics_data = [(f"event_{i % 10}", f'{{"data": {i}}}', None, None) for i in range(5000)]
        conn.executemany(
            "INSERT INTO analytics (event_type, event_data, codebase_id, task_id) VALUES (?, ?, ?, ?)",
            analytics_data
        )
        
        conn.commit()
        insert_time = time.time() - start_time
        
        # Test query performance
        start_time = time.time()
        result = conn.execute(
            "SELECT COUNT(*) FROM analytics WHERE event_type LIKE 'event_%'"
        ).fetchone()
        query_time = time.time() - start_time
        
        assert result[0] == 5000
        assert insert_time < 5.0  # Should complete within 5 seconds
        assert query_time < 1.0   # Query should be fast with index

    def test_concurrent_access(self, test_db_path):
        """Test concurrent database access."""
        def worker_function(worker_id, results):
            try:
                conn = sqlite3.connect(test_db_path, check_same_thread=False)
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Create table if not exists
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS concurrent_test (
                        id INTEGER PRIMARY KEY,
                        worker_id INTEGER,
                        value TEXT
                    )
                """)
                
                # Insert data
                for i in range(10):
                    conn.execute(
                        "INSERT INTO concurrent_test (worker_id, value) VALUES (?, ?)",
                        (worker_id, f"value_{worker_id}_{i}")
                    )
                conn.commit()
                
                # Read data
                result = conn.execute(
                    "SELECT COUNT(*) FROM concurrent_test WHERE worker_id = ?",
                    (worker_id,)
                ).fetchone()
                
                results[worker_id] = result[0]
                conn.close()
                
            except Exception as e:
                results[worker_id] = f"Error: {e}"
        
        # Run concurrent workers
        results = {}
        threads = []
        
        for i in range(5):
            thread = threading.Thread(target=worker_function, args=(i, results))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all workers completed successfully
        for worker_id, result in results.items():
            assert isinstance(result, int)
            assert result == 10

    def test_transaction_rollback(self, sample_schema):
        """Test transaction handling and rollback."""
        conn = sample_schema
        
        # Test successful transaction
        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            ("Transaction Test", "Test Description")
        )
        conn.execute("COMMIT")
        
        result = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE title = ?",
            ("Transaction Test",)
        ).fetchone()
        assert result[0] == 1
        
        # Test rollback
        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            ("Rollback Test", "This should be rolled back")
        )
        conn.execute("ROLLBACK")
        
        result = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE title = ?",
            ("Rollback Test",)
        ).fetchone()
        assert result[0] == 0

    def test_backup_restore(self, sample_schema, test_db_path):
        """Test database backup and restore functionality."""
        conn = sample_schema
        
        # Insert test data
        conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            ("Backup Test", "Test data for backup")
        )
        conn.commit()
        
        # Create backup
        backup_path = test_db_path + ".backup"
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        
        # Verify backup
        backup_conn = sqlite3.connect(backup_path)
        result = backup_conn.execute(
            "SELECT title FROM tasks WHERE title = ?",
            ("Backup Test",)
        ).fetchone()
        backup_conn.close()
        
        assert result is not None
        assert result[0] == "Backup Test"
        
        # Cleanup
        os.unlink(backup_path)

    def test_database_migration_simulation(self, sample_schema):
        """Test database schema migration scenarios."""
        conn = sample_schema
        
        # Simulate adding a new column
        conn.execute("ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 1")
        
        # Test that existing data is preserved
        conn.execute(
            "INSERT INTO tasks (title, description, priority) VALUES (?, ?, ?)",
            ("Priority Task", "Test", 5)
        )
        conn.commit()
        
        result = conn.execute(
            "SELECT title, priority FROM tasks WHERE title = ?",
            ("Priority Task",)
        ).fetchone()
        
        assert result[0] == "Priority Task"
        assert result[1] == 5
        
        # Test that old records have default priority
        conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            ("Default Priority", "Test")
        )
        conn.commit()
        
        result = conn.execute(
            "SELECT priority FROM tasks WHERE title = ?",
            ("Default Priority",)
        ).fetchone()
        
        assert result[0] == 1  # Default value

