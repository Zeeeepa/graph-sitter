"""
Database Connection Management

Handles SQLAlchemy engine creation, session management, and connection pooling
for the graph-sitter database system with performance monitoring and health checks.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Generator, Dict, Any
from threading import Lock

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError

from .config import DatabaseConfig, get_database_config

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection manager with pooling and monitoring."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """Initialize database connection manager."""
        self.config = config or get_database_config()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._lock = Lock()
        self._query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "failed_queries": 0,
            "total_time_ms": 0,
        }
    
    @property
    def engine(self) -> Engine:
        """Get or create the SQLAlchemy engine."""
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get or create the session factory."""
        if self._session_factory is None:
            with self._lock:
                if self._session_factory is None:
                    self._session_factory = sessionmaker(
                        bind=self.engine,
                        expire_on_commit=False,
                        autoflush=True,
                        autocommit=False,
                    )
        return self._session_factory
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with monitoring."""
        logger.info(f"Creating database engine for: {self.config.database_name}")
        
        engine = create_engine(
            self.config.url,
            poolclass=QueuePool,
            **self.config.connection_args
        )
        
        # Set up event listeners for monitoring
        if self.config.enable_query_monitoring:
            self._setup_query_monitoring(engine)
        
        # Test connection
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to establish database connection: {e}")
            raise
        
        return engine
    
    def _setup_query_monitoring(self, engine: Engine) -> None:
        """Set up query monitoring event listeners."""
        
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query start time."""
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query completion and log slow queries."""
            if hasattr(context, '_query_start_time'):
                duration_ms = (time.time() - context._query_start_time) * 1000
                
                # Update statistics
                self._query_stats["total_queries"] += 1
                self._query_stats["total_time_ms"] += duration_ms
                
                # Log slow queries
                if (self.config.enable_slow_query_logging and 
                    duration_ms > self.config.slow_query_threshold_ms):
                    self._query_stats["slow_queries"] += 1
                    logger.warning(
                        f"Slow query detected: {duration_ms:.2f}ms - {statement[:200]}..."
                    )
        
        @event.listens_for(engine, "handle_error")
        def handle_error(exception_context):
            """Handle database errors."""
            self._query_stats["failed_queries"] += 1
            logger.error(f"Database error: {exception_context.original_exception}")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.session_factory()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            start_time = time.time()
            
            with self.session_scope() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1 as health_check")).fetchone()
                
                # Get connection pool status
                pool = self.engine.pool
                pool_status = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid(),
                }
                
                # Get database statistics
                db_stats = session.execute(text("""
                    SELECT 
                        current_database() as database_name,
                        pg_database_size(current_database()) as size_bytes,
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections
                """)).fetchone()
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time_ms, 2),
                "database_name": db_stats.database_name,
                "database_size_mb": round(db_stats.size_bytes / 1024 / 1024, 2),
                "active_connections": db_stats.active_connections,
                "pool_status": pool_status,
                "query_stats": self._query_stats.copy(),
                "timestamp": time.time(),
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time(),
            }
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get query performance statistics."""
        stats = self._query_stats.copy()
        if stats["total_queries"] > 0:
            stats["avg_query_time_ms"] = round(
                stats["total_time_ms"] / stats["total_queries"], 2
            )
            stats["slow_query_percentage"] = round(
                (stats["slow_queries"] / stats["total_queries"]) * 100, 2
            )
            stats["error_percentage"] = round(
                (stats["failed_queries"] / stats["total_queries"]) * 100, 2
            )
        return stats
    
    def reset_statistics(self) -> None:
        """Reset query statistics."""
        self._query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "failed_queries": 0,
            "total_time_ms": 0,
        }
        logger.info("Database query statistics reset")
    
    def close(self) -> None:
        """Close database connections and cleanup resources."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")


# Global connection instance
_connection: Optional[DatabaseConnection] = None
_connection_lock = Lock()


def get_database_connection(config: Optional[DatabaseConfig] = None) -> DatabaseConnection:
    """Get the global database connection instance."""
    global _connection
    if _connection is None:
        with _connection_lock:
            if _connection is None:
                _connection = DatabaseConnection(config)
    return _connection


def get_database_session() -> Session:
    """Get a new database session from the global connection."""
    return get_database_connection().get_session()


@contextmanager
def database_session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope using the global connection."""
    connection = get_database_connection()
    with connection.session_scope() as session:
        yield session


def close_database_connection() -> None:
    """Close the global database connection."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None


def database_health_check() -> Dict[str, Any]:
    """Perform database health check using global connection."""
    return get_database_connection().health_check()


def get_database_statistics() -> Dict[str, Any]:
    """Get database query statistics."""
    return get_database_connection().get_query_statistics()


# Context manager for temporary database configuration
@contextmanager
def temporary_database_config(config: DatabaseConfig) -> Generator[DatabaseConnection, None, None]:
    """Temporarily use a different database configuration."""
    temp_connection = DatabaseConnection(config)
    try:
        yield temp_connection
    finally:
        temp_connection.close()

