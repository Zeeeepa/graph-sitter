"""
Database Integration Adapter

This module provides integration between the Contexten system and
the comprehensive database schema for data persistence and analytics.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Database connection error."""
    pass


class DatabaseOperationError(Exception):
    """Database operation error."""
    pass


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "contexten_cicd"
    username: str = "contexten"
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20


class DatabaseAdapter:
    """
    Database adapter for the comprehensive CI/CD database schema.
    
    This adapter provides high-level operations for interacting with
    the 7-module database schema while abstracting the complexity
    of direct SQL operations.
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize the database adapter.
        
        Args:
            config: Database configuration
        """
        self.config = config
        self.connection_pool = None
        self.connected = False
        
        logger.info("Database adapter initialized")
    
    async def connect(self):
        """Connect to the database."""
        try:
            # In a real implementation, this would create an actual connection pool
            # import asyncpg
            # self.connection_pool = await asyncpg.create_pool(
            #     host=self.config.host,
            #     port=self.config.port,
            #     database=self.config.database,
            #     user=self.config.username,
            #     password=self.config.password,
            #     min_size=1,
            #     max_size=self.config.pool_size
            # )
            
            # For now, simulate connection
            await asyncio.sleep(0.1)
            self.connected = True
            
            logger.info("Connected to database")
            
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
    
    async def disconnect(self):
        """Disconnect from the database."""
        if self.connection_pool:
            # await self.connection_pool.close()
            pass
        
        self.connected = False
        logger.info("Disconnected from database")
    
    async def _execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute a database query."""
        if not self.connected:
            raise DatabaseConnectionError("Not connected to database")
        
        try:
            # In a real implementation:
            # async with self.connection_pool.acquire() as connection:
            #     rows = await connection.fetch(query, *params if params else ())
            #     return [dict(row) for row in rows]
            
            # For now, simulate query execution
            await asyncio.sleep(0.01)
            logger.debug(f"Executed query: {query[:100]}...")
            return []
            
        except Exception as e:
            raise DatabaseOperationError(f"Query execution failed: {e}")
    
    async def _execute_command(self, command: str, params: Optional[Tuple] = None) -> int:
        """Execute a database command (INSERT, UPDATE, DELETE)."""
        if not self.connected:
            raise DatabaseConnectionError("Not connected to database")
        
        try:
            # In a real implementation:
            # async with self.connection_pool.acquire() as connection:
            #     result = await connection.execute(command, *params if params else ())
            #     return int(result.split()[-1])  # Extract affected row count
            
            # For now, simulate command execution
            await asyncio.sleep(0.01)
            logger.debug(f"Executed command: {command[:100]}...")
            return 1  # Simulate 1 affected row
            
        except Exception as e:
            raise DatabaseOperationError(f"Command execution failed: {e}")
    
    # Organization operations
    
    async def create_organization(self, name: str, slug: str, description: Optional[str] = None) -> str:
        """Create a new organization."""
        org_id = str(uuid.uuid4())
        
        command = """
            INSERT INTO organizations (id, name, slug, description, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        now = datetime.now()
        await self._execute_command(command, (org_id, name, slug, description, now, now))
        
        logger.info(f"Created organization: {name} ({org_id})")
        return org_id
    
    async def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization by ID."""
        query = "SELECT * FROM organizations WHERE id = $1"
        results = await self._execute_query(query, (org_id,))
        return results[0] if results else None
    
    async def list_organizations(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all organizations."""
        query = "SELECT * FROM organizations"
        if active_only:
            query += " WHERE is_active = true"
        query += " ORDER BY name"
        
        return await self._execute_query(query)
    
    # Project operations
    
    async def create_project(self, 
                           org_id: str,
                           name: str,
                           slug: str,
                           description: Optional[str] = None,
                           repository_url: Optional[str] = None) -> str:
        """Create a new project."""
        project_id = str(uuid.uuid4())
        
        command = """
            INSERT INTO projects (id, organization_id, name, slug, description, repository_url, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        now = datetime.now()
        await self._execute_command(command, (project_id, org_id, name, slug, description, repository_url, now, now))
        
        logger.info(f"Created project: {name} ({project_id})")
        return project_id
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        query = "SELECT * FROM projects WHERE id = $1"
        results = await self._execute_query(query, (project_id,))
        return results[0] if results else None
    
    async def list_projects(self, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List projects, optionally filtered by organization."""
        query = "SELECT * FROM projects"
        params = None
        
        if org_id:
            query += " WHERE organization_id = $1"
            params = (org_id,)
        
        query += " ORDER BY name"
        
        return await self._execute_query(query, params)
    
    # Task operations
    
    async def create_task(self,
                         project_id: str,
                         name: str,
                         description: Optional[str] = None,
                         workflow_id: Optional[str] = None,
                         task_definition_id: Optional[str] = None,
                         priority: int = 5,
                         config: Optional[Dict[str, Any]] = None,
                         context: Optional[Dict[str, Any]] = None) -> str:
        """Create a new task."""
        task_id = str(uuid.uuid4())
        
        command = """
            INSERT INTO tasks (id, project_id, workflow_id, task_definition_id, name, description, 
                             priority, config, context, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        
        now = datetime.now()
        await self._execute_command(command, (
            task_id, project_id, workflow_id, task_definition_id, name, description,
            priority, json.dumps(config or {}), json.dumps(context or {}), now, now
        ))
        
        logger.info(f"Created task: {name} ({task_id})")
        return task_id
    
    async def update_task_status(self, 
                               task_id: str,
                               status: str,
                               result: Optional[Dict[str, Any]] = None,
                               error_message: Optional[str] = None) -> bool:
        """Update task status."""
        now = datetime.now()
        
        if status == "running":
            command = """
                UPDATE tasks SET status = $1, started_at = $2, updated_at = $3
                WHERE id = $4
            """
            params = (status, now, now, task_id)
        elif status in ["completed", "failed", "cancelled"]:
            command = """
                UPDATE tasks SET status = $1, completed_at = $2, result = $3, 
                               error_message = $4, updated_at = $5
                WHERE id = $6
            """
            params = (status, now, json.dumps(result or {}), error_message, now, task_id)
        else:
            command = """
                UPDATE tasks SET status = $1, updated_at = $2
                WHERE id = $3
            """
            params = (status, now, task_id)
        
        affected_rows = await self._execute_command(command, params)
        return affected_rows > 0
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        query = "SELECT * FROM tasks WHERE id = $1"
        results = await self._execute_query(query, (task_id,))
        return results[0] if results else None
    
    async def list_tasks(self, 
                        project_id: Optional[str] = None,
                        status: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """List tasks with optional filters."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        param_count = 0
        
        if project_id:
            param_count += 1
            query += f" AND project_id = ${param_count}"
            params.append(project_id)
        
        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)
        
        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1}"
        params.append(limit)
        
        return await self._execute_query(query, tuple(params))
    
    # Pipeline operations
    
    async def create_pipeline(self,
                            project_id: str,
                            name: str,
                            description: Optional[str] = None,
                            pipeline_type: str = "ci_cd",
                            config: Optional[Dict[str, Any]] = None) -> str:
        """Create a new pipeline."""
        pipeline_id = str(uuid.uuid4())
        
        command = """
            INSERT INTO pipelines (id, project_id, name, description, pipeline_type, config, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        now = datetime.now()
        await self._execute_command(command, (
            pipeline_id, project_id, name, description, pipeline_type,
            json.dumps(config or {}), now, now
        ))
        
        logger.info(f"Created pipeline: {name} ({pipeline_id})")
        return pipeline_id
    
    async def create_pipeline_run(self,
                                pipeline_id: str,
                                trigger_event: Optional[Dict[str, Any]] = None) -> str:
        """Create a new pipeline run."""
        run_id = str(uuid.uuid4())
        
        command = """
            INSERT INTO pipeline_runs (id, pipeline_id, trigger_event, started_at)
            VALUES ($1, $2, $3, $4)
        """
        
        now = datetime.now()
        await self._execute_command(command, (
            run_id, pipeline_id, json.dumps(trigger_event or {}), now
        ))
        
        logger.info(f"Created pipeline run: {run_id}")
        return run_id
    
    async def update_pipeline_run(self,
                                run_id: str,
                                status: str,
                                result: Optional[Dict[str, Any]] = None,
                                error_message: Optional[str] = None) -> bool:
        """Update pipeline run status."""
        now = datetime.now()
        
        if status in ["success", "failure", "cancelled"]:
            # Calculate duration if completing
            query = "SELECT started_at FROM pipeline_runs WHERE id = $1"
            results = await self._execute_query(query, (run_id,))
            
            if results:
                started_at = results[0]["started_at"]
                duration = int((now - started_at).total_seconds())
            else:
                duration = 0
            
            command = """
                UPDATE pipeline_runs SET status = $1, completed_at = $2, duration_seconds = $3,
                                        result = $4, error_message = $5
                WHERE id = $6
            """
            params = (status, now, duration, json.dumps(result or {}), error_message, run_id)
        else:
            command = """
                UPDATE pipeline_runs SET status = $1
                WHERE id = $2
            """
            params = (status, run_id)
        
        affected_rows = await self._execute_command(command, params)
        return affected_rows > 0
    
    # Analytics operations
    
    async def record_analysis_run(self,
                                project_id: str,
                                run_type: str,
                                repository_id: Optional[str] = None,
                                commit_sha: Optional[str] = None,
                                branch: Optional[str] = None,
                                config: Optional[Dict[str, Any]] = None) -> str:
        """Record a new analysis run."""
        run_id = str(uuid.uuid4())
        
        command = """
            INSERT INTO analysis_runs (id, project_id, repository_id, run_type, commit_sha, 
                                     branch, config, started_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        now = datetime.now()
        await self._execute_command(command, (
            run_id, project_id, repository_id, run_type, commit_sha,
            branch, json.dumps(config or {}), now
        ))
        
        logger.info(f"Recorded analysis run: {run_id}")
        return run_id
    
    async def record_metric(self,
                          analysis_run_id: str,
                          metric_type: str,
                          metric_name: str,
                          metric_value: Optional[float] = None,
                          metric_data: Optional[Dict[str, Any]] = None,
                          file_path: Optional[str] = None,
                          function_name: Optional[str] = None,
                          class_name: Optional[str] = None) -> str:
        """Record a metric."""
        metric_id = str(uuid.uuid4())
        
        command = """
            INSERT INTO metrics (id, analysis_run_id, metric_type, metric_name, metric_value,
                               metric_data, file_path, function_name, class_name, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        
        now = datetime.now()
        await self._execute_command(command, (
            metric_id, analysis_run_id, metric_type, metric_name, metric_value,
            json.dumps(metric_data or {}), file_path, function_name, class_name, now
        ))
        
        return metric_id
    
    # Learning operations
    
    async def record_pattern(self,
                           org_id: str,
                           pattern_type: str,
                           pattern_data: Dict[str, Any],
                           confidence_score: float) -> str:
        """Record a recognized pattern."""
        pattern_id = str(uuid.uuid4())
        
        command = """
            INSERT INTO pattern_recognition (id, organization_id, pattern_type, pattern_data,
                                           confidence_score, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        now = datetime.now()
        await self._execute_command(command, (
            pattern_id, org_id, pattern_type, json.dumps(pattern_data),
            confidence_score, now, now
        ))
        
        logger.info(f"Recorded pattern: {pattern_type} ({pattern_id})")
        return pattern_id
    
    async def record_adaptation(self,
                              model_id: str,
                              adaptation_type: str,
                              adaptation_data: Dict[str, Any],
                              trigger_pattern_id: Optional[str] = None,
                              effectiveness_score: Optional[float] = None) -> str:
        """Record an adaptation."""
        adaptation_id = str(uuid.uuid4())
        
        command = """
            INSERT INTO adaptations (id, model_id, adaptation_type, trigger_pattern_id,
                                   adaptation_data, effectiveness_score, applied_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        now = datetime.now()
        await self._execute_command(command, (
            adaptation_id, model_id, adaptation_type, trigger_pattern_id,
            json.dumps(adaptation_data), effectiveness_score, now, now
        ))
        
        logger.info(f"Recorded adaptation: {adaptation_type} ({adaptation_id})")
        return adaptation_id
    
    # Query operations
    
    async def get_project_metrics(self, project_id: str, days: int = 30) -> Dict[str, Any]:
        """Get aggregated metrics for a project."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Task metrics
        task_query = """
            SELECT status, COUNT(*) as count, AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration
            FROM tasks 
            WHERE project_id = $1 AND created_at >= $2
            GROUP BY status
        """
        task_results = await self._execute_query(task_query, (project_id, cutoff_date))
        
        # Pipeline metrics
        pipeline_query = """
            SELECT pr.status, COUNT(*) as count, AVG(pr.duration_seconds) as avg_duration
            FROM pipeline_runs pr
            JOIN pipelines p ON pr.pipeline_id = p.id
            WHERE p.project_id = $1 AND pr.started_at >= $2
            GROUP BY pr.status
        """
        pipeline_results = await self._execute_query(pipeline_query, (project_id, cutoff_date))
        
        return {
            "project_id": project_id,
            "period_days": days,
            "task_metrics": task_results,
            "pipeline_metrics": pipeline_results,
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_organization_summary(self, org_id: str) -> Dict[str, Any]:
        """Get summary statistics for an organization."""
        # Project count
        project_query = "SELECT COUNT(*) as count FROM projects WHERE organization_id = $1 AND is_active = true"
        project_results = await self._execute_query(project_query, (org_id,))
        project_count = project_results[0]["count"] if project_results else 0
        
        # Active task count
        task_query = """
            SELECT COUNT(*) as count FROM tasks t
            JOIN projects p ON t.project_id = p.id
            WHERE p.organization_id = $1 AND t.status IN ('pending', 'running')
        """
        task_results = await self._execute_query(task_query, (org_id,))
        active_task_count = task_results[0]["count"] if task_results else 0
        
        return {
            "organization_id": org_id,
            "project_count": project_count,
            "active_task_count": active_task_count,
            "generated_at": datetime.now().isoformat()
        }
    
    async def search_patterns(self, 
                            org_id: str,
                            pattern_type: Optional[str] = None,
                            min_confidence: float = 0.7,
                            limit: int = 50) -> List[Dict[str, Any]]:
        """Search for patterns."""
        query = "SELECT * FROM pattern_recognition WHERE organization_id = $1 AND confidence_score >= $2"
        params = [org_id, min_confidence]
        param_count = 2
        
        if pattern_type:
            param_count += 1
            query += f" AND pattern_type = ${param_count}"
            params.append(pattern_type)
        
        query += f" ORDER BY confidence_score DESC, last_seen_at DESC LIMIT ${param_count + 1}"
        params.append(limit)
        
        return await self._execute_query(query, tuple(params))
    
    # Health and maintenance operations
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            # Simple query to test connection
            result = await self._execute_query("SELECT 1 as health_check")
            
            return {
                "status": "healthy",
                "connected": self.connected,
                "timestamp": datetime.now().isoformat(),
                "query_test": len(result) > 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": self.connected,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        # In a real implementation, this would query actual table statistics
        return {
            "organizations": 5,
            "projects": 25,
            "tasks": 1250,
            "pipelines": 45,
            "pipeline_runs": 890,
            "analysis_runs": 340,
            "metrics": 15600,
            "patterns": 78,
            "adaptations": 23,
            "last_updated": datetime.now().isoformat()
        }


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the database adapter."""
        config = DatabaseConfig(
            host="localhost",
            database="contexten_test",
            username="test_user"
        )
        
        adapter = DatabaseAdapter(config)
        
        try:
            # Connect to database
            await adapter.connect()
            
            # Create organization
            org_id = await adapter.create_organization(
                name="Example Org",
                slug="example-org",
                description="Example organization"
            )
            
            # Create project
            project_id = await adapter.create_project(
                org_id=org_id,
                name="Example Project",
                slug="example-project",
                repository_url="https://github.com/example/repo"
            )
            
            # Create task
            task_id = await adapter.create_task(
                project_id=project_id,
                name="Example Task",
                description="Example task description"
            )
            
            # Update task status
            await adapter.update_task_status(task_id, "running")
            await adapter.update_task_status(task_id, "completed", {"result": "success"})
            
            # Get metrics
            metrics = await adapter.get_project_metrics(project_id)
            print(f"Project metrics: {metrics}")
            
            # Health check
            health = await adapter.health_check()
            print(f"Database health: {health}")
            
        finally:
            await adapter.disconnect()
    
    asyncio.run(example_usage())

