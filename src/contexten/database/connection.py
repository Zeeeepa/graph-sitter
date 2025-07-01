"""
Database connection management for the comprehensive CI/CD system.

Provides async database connectivity with support for both SQLite (development) 
and PostgreSQL (production) databases.
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from ..config.database import DatabaseConfig

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class DatabaseManager:
    """Manages database connections and sessions for the CI/CD system."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the database connection and create tables."""
        if self._initialized:
            return
            
        logger.info(f"Initializing database connection to {self.config.database_url}")
        
        # Create async engine with appropriate configuration
        engine_kwargs = {
            "echo": self.config.echo_sql,
            "pool_pre_ping": True,
        }
        
        # SQLite-specific configuration
        if self.config.database_url.startswith("sqlite"):
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                },
            })
        
        self._engine = create_async_engine(
            self.config.database_url,
            **engine_kwargs
        )
        
        # Create session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create all tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        self._initialized = True
        logger.info("Database initialization completed")
    
    async def close(self) -> None:
        """Close the database connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("Database connection closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        if not self._initialized:
            await self.initialize()
        
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        if not self._engine:
            raise RuntimeError("Database not initialized")
        return self._engine


# Global database manager instance
_database_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _database_manager
    if _database_manager is None:
        from ..config.database import get_database_config
        config = get_database_config()
        _database_manager = DatabaseManager(config)
    return _database_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function to get a database session."""
    db_manager = get_database_manager()
    async with db_manager.get_session() as session:
        yield session

