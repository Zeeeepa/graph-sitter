"""
Database Manager for Analysis Framework
Handles database connections, schema management, and data operations
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
from asyncpg import Connection, Pool

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and operations for the analysis framework
    """
    
    def __init__(self, database_url: str, pool_size: int = 10):
        self.database_url = database_url
        self.pool_size = pool_size
        self.pool: Optional[Pool] = None
        
    async def initialize(self):
        """Initialize database connection pool and schema"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=self.pool_size,
                command_timeout=60
            )
            
            # Initialize database schema
            await self._initialize_schema()
            
            logger.info(f"Database pool initialized with {self.pool_size} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    async def _initialize_schema(self):
        """Initialize database schema from SQL files"""
        schema_dir = Path(__file__).parent.parent / "database_schemas"
        
        # Order matters for schema initialization
        schema_order = [
            "tasks/init_tasks_schema.sql",
            "codebase/init_codebase_schema.sql", 
            "prompts/init_prompts_schema.sql",
            "analytics/init_analytics_schema.sql"
        ]
        
        async with self.get_connection() as conn:
            for schema_file in schema_order:
                schema_path = schema_dir / schema_file
                if schema_path.exists():
                    logger.info(f"Executing schema: {schema_file}")
                    schema_sql = schema_path.read_text()
                    await conn.execute(schema_sql)
                else:
                    logger.warning(f"Schema file not found: {schema_path}")
    
    @asynccontextmanager
    async def get_connection(self) -> Connection:
        """Get a database connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_query(
        self, 
        query: str, 
        *args, 
        fetch: str = "none"
    ) -> Any:
        """
        Execute a database query
        
        Args:
            query: SQL query string
            *args: Query parameters
            fetch: "none", "one", "all", or "val"
            
        Returns:
            Query result based on fetch type
        """
        async with self.get_connection() as conn:
            if fetch == "none":
                return await conn.execute(query, *args)
            elif fetch == "one":
                return await conn.fetchrow(query, *args)
            elif fetch == "all":
                return await conn.fetch(query, *args)
            elif fetch == "val":
                return await conn.fetchval(query, *args)
            else:
                raise ValueError(f"Invalid fetch type: {fetch}")
    
    async def execute_transaction(self, operations: List[Dict[str, Any]]) -> List[Any]:
        """
        Execute multiple operations in a transaction
        
        Args:
            operations: List of operation dictionaries with 'query', 'args', and 'fetch'
            
        Returns:
            List of results for each operation
        """
        async with self.get_connection() as conn:
            async with conn.transaction():
                results = []
                for op in operations:
                    query = op['query']
                    args = op.get('args', [])
                    fetch = op.get('fetch', 'none')
                    
                    if fetch == "none":
                        result = await conn.execute(query, *args)
                    elif fetch == "one":
                        result = await conn.fetchrow(query, *args)
                    elif fetch == "all":
                        result = await conn.fetch(query, *args)
                    elif fetch == "val":
                        result = await conn.fetchval(query, *args)
                    else:
                        raise ValueError(f"Invalid fetch type: {fetch}")
                    
                    results.append(result)
                
                return results
    
    async def bulk_insert(
        self, 
        table: str, 
        columns: List[str], 
        data: List[List[Any]]
    ) -> int:
        """
        Perform bulk insert operation
        
        Args:
            table: Table name
            columns: List of column names
            data: List of rows (each row is a list of values)
            
        Returns:
            Number of rows inserted
        """
        if not data:
            return 0
        
        placeholders = ', '.join(f'${i+1}' for i in range(len(columns)))
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        
        async with self.get_connection() as conn:
            async with conn.transaction():
                await conn.executemany(query, data)
        
        return len(data)
    
    async def upsert(
        self,
        table: str,
        data: Dict[str, Any],
        conflict_columns: List[str],
        update_columns: Optional[List[str]] = None
    ) -> Any:
        """
        Perform upsert (INSERT ... ON CONFLICT ... DO UPDATE)
        
        Args:
            table: Table name
            data: Dictionary of column -> value
            conflict_columns: Columns that define the conflict
            update_columns: Columns to update on conflict (default: all except conflict columns)
            
        Returns:
            Result of the upsert operation
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(f'${i+1}' for i in range(len(columns)))
        
        if update_columns is None:
            update_columns = [col for col in columns if col not in conflict_columns]
        
        update_clause = ', '.join(f"{col} = EXCLUDED.{col}" for col in update_columns)
        conflict_clause = ', '.join(conflict_columns)
        
        query = f"""
        INSERT INTO {table} ({', '.join(columns)}) 
        VALUES ({placeholders})
        ON CONFLICT ({conflict_clause}) 
        DO UPDATE SET {update_clause}
        RETURNING *
        """
        
        return await self.execute_query(query, *values, fetch="one")
    
    async def get_repository_by_id(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get repository information by ID"""
        result = await self.execute_query(
            "SELECT * FROM repositories WHERE id = $1",
            repo_id,
            fetch="one"
        )
        return dict(result) if result else None
    
    async def get_repository_by_name(self, full_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information by full name"""
        result = await self.execute_query(
            "SELECT * FROM repositories WHERE full_name = $1",
            full_name,
            fetch="one"
        )
        return dict(result) if result else None
    
    async def get_analysis_results(
        self, 
        repo_id: str, 
        analysis_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get analysis results for a repository"""
        if analysis_type:
            results = await self.execute_query(
                """
                SELECT * FROM analysis_results 
                WHERE repository_id = $1 AND analysis_type = $2
                ORDER BY analysis_date DESC
                LIMIT $3
                """,
                repo_id, analysis_type, limit,
                fetch="all"
            )
        else:
            results = await self.execute_query(
                """
                SELECT * FROM analysis_results 
                WHERE repository_id = $1
                ORDER BY analysis_date DESC
                LIMIT $2
                """,
                repo_id, limit,
                fetch="all"
            )
        
        return [dict(result) for result in results]
    
    async def get_code_metrics(
        self,
        repo_id: str,
        metric_type: Optional[str] = None,
        file_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get code metrics for a repository"""
        conditions = ["repository_id = $1"]
        params = [repo_id]
        
        if metric_type:
            conditions.append("metric_type = $2")
            params.append(metric_type)
        
        if file_id:
            conditions.append("file_id = $3")
            params.append(file_id)
        
        query = f"""
        SELECT * FROM code_metrics 
        WHERE {' AND '.join(conditions)}
        ORDER BY measurement_date DESC
        """
        
        results = await self.execute_query(query, *params, fetch="all")
        return [dict(result) for result in results]
    
    async def get_repository_health_summary(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get repository health summary"""
        result = await self.execute_query(
            "SELECT * FROM repository_health_summary WHERE repository_id = $1",
            repo_id,
            fetch="one"
        )
        return dict(result) if result else None
    
    async def get_security_issues(
        self, 
        repo_id: str, 
        severity_level: Optional[str] = None,
        status: str = "open"
    ) -> List[Dict[str, Any]]:
        """Get security issues for a repository"""
        conditions = ["repository_id = $1", "status = $2"]
        params = [repo_id, status]
        
        if severity_level:
            conditions.append("severity_level = $3")
            params.append(severity_level)
        
        query = f"""
        SELECT * FROM security_analysis 
        WHERE {' AND '.join(conditions)}
        ORDER BY 
            CASE severity_level 
                WHEN 'critical' THEN 1 
                WHEN 'high' THEN 2 
                WHEN 'medium' THEN 3 
                WHEN 'low' THEN 4 
                ELSE 5 
            END,
            analysis_date DESC
        """
        
        results = await self.execute_query(query, *params, fetch="all")
        return [dict(result) for result in results]
    
    async def get_trend_data(
        self,
        repo_id: str,
        metric_type: str,
        metric_name: str,
        time_period: str = "daily"
    ) -> Optional[Dict[str, Any]]:
        """Get trend analysis data"""
        result = await self.execute_query(
            """
            SELECT * FROM trend_analysis 
            WHERE repository_id = $1 AND metric_type = $2 
            AND metric_name = $3 AND time_period = $4
            ORDER BY end_date DESC
            LIMIT 1
            """,
            repo_id, metric_type, metric_name, time_period,
            fetch="one"
        )
        return dict(result) if result else None
    
    async def create_task(
        self,
        name: str,
        task_type: str,
        configuration: Dict[str, Any],
        priority: int = 5,
        description: Optional[str] = None
    ) -> str:
        """Create a new task"""
        task_id = await self.execute_query(
            """
            INSERT INTO tasks (name, description, task_type, priority, configuration)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            name, description, task_type, priority, configuration,
            fetch="val"
        )
        return str(task_id)
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update task status"""
        if error_message:
            await self.execute_query(
                """
                UPDATE tasks 
                SET status = $2, error_message = $3, updated_at = NOW()
                WHERE id = $1
                """,
                task_id, status, error_message
            )
        else:
            await self.execute_query(
                """
                UPDATE tasks 
                SET status = $2, updated_at = NOW()
                WHERE id = $1
                """,
                task_id, status
            )
    
    async def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending tasks for execution"""
        results = await self.execute_query(
            """
            SELECT * FROM tasks 
            WHERE status = 'pending'
            ORDER BY priority ASC, created_at ASC
            LIMIT $1
            """,
            limit,
            fetch="all"
        )
        return [dict(result) for result in results]
    
    async def cleanup_old_data(self, days: int = 90):
        """Clean up old analysis data"""
        operations = [
            {
                'query': """
                DELETE FROM analysis_results 
                WHERE analysis_date < NOW() - INTERVAL '%s days'
                """ % days,
                'fetch': 'none'
            },
            {
                'query': """
                DELETE FROM code_metrics 
                WHERE measurement_date < NOW() - INTERVAL '%s days'
                """ % days,
                'fetch': 'none'
            },
            {
                'query': """
                DELETE FROM task_executions 
                WHERE started_at < NOW() - INTERVAL '%s days'
                """ % days,
                'fetch': 'none'
            }
        ]
        
        await self.execute_transaction(operations)
        logger.info(f"Cleaned up data older than {days} days")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        # Table row counts
        tables = [
            'repositories', 'files', 'symbols', 'analysis_results',
            'code_metrics', 'tasks', 'security_analysis'
        ]
        
        for table in tables:
            count = await self.execute_query(
                f"SELECT COUNT(*) FROM {table}",
                fetch="val"
            )
            stats[f"{table}_count"] = count
        
        # Database size
        db_size = await self.execute_query(
            "SELECT pg_size_pretty(pg_database_size(current_database()))",
            fetch="val"
        )
        stats['database_size'] = db_size
        
        return stats
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")


# Example usage
async def main():
    """Example usage of DatabaseManager"""
    db_manager = DatabaseManager("postgresql://user:password@localhost/analysis_db")
    
    try:
        await db_manager.initialize()
        
        # Get database stats
        stats = await db_manager.get_database_stats()
        print(f"Database stats: {stats}")
        
        # Example queries
        repos = await db_manager.execute_query(
            "SELECT name, analysis_status FROM repositories LIMIT 5",
            fetch="all"
        )
        print(f"Repositories: {[dict(r) for r in repos]}")
        
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())

