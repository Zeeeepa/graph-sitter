"""
Database Storage Layer for Event System
Core-7: Event System & Multi-Platform Integration
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict
import uuid

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    from psycopg2.pool import ThreadedConnectionPool
except ImportError:
    psycopg2 = None

from graph_sitter.shared.logging.get_logger import get_logger
from .engine import ProcessedEvent, EventPriority

logger = get_logger(__name__)


class EventStorageError(Exception):
    """Base exception for event storage errors."""
    pass


class DatabaseConnectionError(EventStorageError):
    """Raised when database connection fails."""
    pass


class EventNotFoundError(EventStorageError):
    """Raised when an event is not found in storage."""
    pass


class EventStorage:
    """Database storage backend for events using PostgreSQL."""
    
    def __init__(self, 
                 connection_string: str,
                 min_connections: int = 1,
                 max_connections: int = 10):
        """Initialize the event storage with database connection."""
        if not psycopg2:
            raise ImportError("psycopg2 is required for database storage")
            
        self.connection_string = connection_string
        self.pool = None
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        self._initialize_connection_pool()
        
    def _initialize_connection_pool(self):
        """Initialize the database connection pool."""
        try:
            self.pool = ThreadedConnectionPool(
                self.min_connections,
                self.max_connections,
                self.connection_string
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to initialize database pool: {e}")
            
    def _get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            raise DatabaseConnectionError("Connection pool not initialized")
        return self.pool.getconn()
        
    def _return_connection(self, conn):
        """Return a connection to the pool."""
        if self.pool:
            self.pool.putconn(conn)
            
    def store_event(self, event: ProcessedEvent) -> str:
        """Store an event in the database."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                # Insert main event record
                cursor.execute("""
                    INSERT INTO events (
                        id, event_id, platform, event_type, source_id, source_name,
                        actor_id, actor_name, payload, metadata, correlation_id,
                        parent_event_id, created_at, processed, processed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    event.id,
                    event.id,  # Using same ID for event_id for now
                    event.platform,
                    event.event_type,
                    event.source_id,
                    event.source_name,
                    event.actor_id,
                    event.actor_name,
                    Json(event.payload),
                    Json(event.metadata),
                    event.correlation_id,
                    event.parent_event_id,
                    event.created_at,
                    event.processed_at is not None,
                    event.processed_at
                ))
                
                # Store platform-specific details
                self._store_platform_details(cursor, event)
                
                # Create initial processing status
                cursor.execute("""
                    INSERT INTO event_processing_status (
                        event_id, processor_name, status, attempt_count, created_at
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    event.id,
                    'event_engine',
                    'pending',
                    event.retry_count,
                    datetime.now(timezone.utc)
                ))
                
                conn.commit()
                logger.debug(f"Stored event {event.id} in database")
                return event.id
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to store event {event.id}: {e}")
            raise EventStorageError(f"Failed to store event: {e}")
        finally:
            if conn:
                self._return_connection(conn)
                
    def _store_platform_details(self, cursor, event: ProcessedEvent):
        """Store platform-specific event details."""
        if event.platform == 'github':
            self._store_github_details(cursor, event)
        elif event.platform == 'linear':
            self._store_linear_details(cursor, event)
        elif event.platform == 'slack':
            self._store_slack_details(cursor, event)
        elif event.platform == 'deployment':
            self._store_deployment_details(cursor, event)
            
    def _store_github_details(self, cursor, event: ProcessedEvent):
        """Store GitHub-specific event details."""
        payload = event.payload
        repo = payload.get('repository', {})
        pr = payload.get('pull_request', {})
        issue = payload.get('issue', {})
        
        cursor.execute("""
            INSERT INTO github_events (
                event_id, repository_id, repository_name, organization,
                installation_id, pull_request_number, issue_number,
                commit_sha, branch_name, action, labels, assignees
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event.id,
            repo.get('id'),
            repo.get('full_name'),
            repo.get('owner', {}).get('login'),
            payload.get('installation', {}).get('id'),
            pr.get('number'),
            issue.get('number'),
            pr.get('head', {}).get('sha') or payload.get('head_commit', {}).get('id'),
            pr.get('head', {}).get('ref'),
            payload.get('action'),
            Json(pr.get('labels', []) or issue.get('labels', [])),
            Json(pr.get('assignees', []) or issue.get('assignees', []))
        ))
        
    def _store_linear_details(self, cursor, event: ProcessedEvent):
        """Store Linear-specific event details."""
        payload = event.payload
        data = payload.get('data', {})
        
        cursor.execute("""
            INSERT INTO linear_events (
                event_id, workspace_id, team_id, issue_id, project_id,
                cycle_id, issue_number, issue_title, state_name,
                priority, labels, assignee_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event.id,
            payload.get('organizationId'),
            data.get('teamId'),
            data.get('id'),
            data.get('projectId'),
            data.get('cycleId'),
            data.get('number'),
            data.get('title'),
            data.get('state', {}).get('name'),
            data.get('priority'),
            Json(data.get('labels', [])),
            data.get('assigneeId')
        ))
        
    def _store_slack_details(self, cursor, event: ProcessedEvent):
        """Store Slack-specific event details."""
        payload = event.payload
        event_data = payload.get('event', payload)
        
        cursor.execute("""
            INSERT INTO slack_events (
                event_id, workspace_id, channel_id, channel_name,
                user_id, thread_ts, message_ts, message_text,
                message_type, bot_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event.id,
            payload.get('team_id'),
            event_data.get('channel'),
            event_data.get('channel_name'),
            event_data.get('user'),
            event_data.get('thread_ts'),
            event_data.get('ts'),
            event_data.get('text'),
            event_data.get('type'),
            event_data.get('bot_id')
        ))
        
    def _store_deployment_details(self, cursor, event: ProcessedEvent):
        """Store deployment-specific event details."""
        payload = event.payload
        
        cursor.execute("""
            INSERT INTO deployment_events (
                event_id, deployment_id, environment, status,
                repository_name, commit_sha, branch_name,
                deployment_url, log_url, started_at, completed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event.id,
            payload.get('deployment_id'),
            payload.get('environment'),
            payload.get('status'),
            payload.get('repository_name'),
            payload.get('commit_sha'),
            payload.get('branch_name'),
            payload.get('deployment_url'),
            payload.get('log_url'),
            payload.get('started_at'),
            payload.get('completed_at')
        ))
        
    def get_event(self, event_id: str) -> Optional[ProcessedEvent]:
        """Retrieve an event by ID."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM events WHERE id = %s
                """, (event_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                return self._row_to_event(row)
                
        except Exception as e:
            logger.error(f"Failed to get event {event_id}: {e}")
            raise EventStorageError(f"Failed to get event: {e}")
        finally:
            if conn:
                self._return_connection(conn)
                
    def _row_to_event(self, row: Dict[str, Any]) -> ProcessedEvent:
        """Convert database row to ProcessedEvent."""
        return ProcessedEvent(
            id=row['id'],
            platform=row['platform'],
            event_type=row['event_type'],
            source_id=row['source_id'],
            source_name=row['source_name'],
            actor_id=row['actor_id'],
            actor_name=row['actor_name'],
            payload=row['payload'],
            metadata=row['metadata'],
            correlation_id=row['correlation_id'],
            parent_event_id=row['parent_event_id'],
            created_at=row['created_at'],
            processed_at=row['processed_at'],
            processing_duration=None,  # Not stored in main table
            error_message=None,  # Retrieved separately if needed
            retry_count=0  # Retrieved from processing status if needed
        )
        
    def mark_event_processed(self, event_id: str, processor_name: str = 'event_engine'):
        """Mark an event as processed."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                # Update main event record
                cursor.execute("""
                    UPDATE events SET 
                        processed = TRUE,
                        processed_at = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                    event_id
                ))
                
                # Update processing status
                cursor.execute("""
                    UPDATE event_processing_status SET
                        status = 'completed',
                        completed_at = %s,
                        updated_at = %s
                    WHERE event_id = %s AND processor_name = %s
                """, (
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                    event_id,
                    processor_name
                ))
                
                conn.commit()
                logger.debug(f"Marked event {event_id} as processed")
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to mark event {event_id} as processed: {e}")
            raise EventStorageError(f"Failed to mark event as processed: {e}")
        finally:
            if conn:
                self._return_connection(conn)
                
    def create_correlation(self, 
                          primary_event_id: str,
                          related_event_id: str,
                          correlation_type: str,
                          confidence_score: float = 1.0,
                          correlation_data: Optional[Dict[str, Any]] = None) -> str:
        """Create a correlation between two events."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                # Call the stored procedure
                cursor.execute("""
                    SELECT create_event_correlation(%s, %s, %s, %s, %s)
                """, (
                    primary_event_id,
                    related_event_id,
                    correlation_type,
                    confidence_score,
                    Json(correlation_data or {})
                ))
                
                correlation_id = cursor.fetchone()[0]
                conn.commit()
                
                logger.debug(f"Created correlation {correlation_id} between events "
                           f"{primary_event_id} and {related_event_id}")
                return correlation_id
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to create correlation: {e}")
            raise EventStorageError(f"Failed to create correlation: {e}")
        finally:
            if conn:
                self._return_connection(conn)
                
    def get_correlated_events(self, correlation_id: str) -> List[ProcessedEvent]:
        """Get all events with the given correlation ID."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM events WHERE correlation_id = %s
                    ORDER BY created_at
                """, (correlation_id,))
                
                rows = cursor.fetchall()
                return [self._row_to_event(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get correlated events: {e}")
            raise EventStorageError(f"Failed to get correlated events: {e}")
        finally:
            if conn:
                self._return_connection(conn)
                
    def get_events_by_platform(self, 
                              platform: str,
                              limit: int = 100,
                              offset: int = 0) -> List[ProcessedEvent]:
        """Get events by platform with pagination."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE platform = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (platform, limit, offset))
                
                rows = cursor.fetchall()
                return [self._row_to_event(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get events by platform: {e}")
            raise EventStorageError(f"Failed to get events by platform: {e}")
        finally:
            if conn:
                self._return_connection(conn)
                
    def get_recent_events(self, limit: int = 100) -> List[ProcessedEvent]:
        """Get recent events across all platforms."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM events 
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
                
                rows = cursor.fetchall()
                return [self._row_to_event(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            raise EventStorageError(f"Failed to get recent events: {e}")
        finally:
            if conn:
                self._return_connection(conn)
                
    def get_event_metrics(self, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get event processing metrics."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                where_clause = ""
                params = []
                
                if start_date or end_date:
                    conditions = []
                    if start_date:
                        conditions.append("created_at >= %s")
                        params.append(start_date)
                    if end_date:
                        conditions.append("created_at <= %s")
                        params.append(end_date)
                    where_clause = "WHERE " + " AND ".join(conditions)
                
                # Get basic metrics
                cursor.execute(f"""
                    SELECT 
                        platform,
                        event_type,
                        COUNT(*) as total_events,
                        COUNT(CASE WHEN processed THEN 1 END) as processed_events,
                        COUNT(CASE WHEN NOT processed THEN 1 END) as pending_events
                    FROM events 
                    {where_clause}
                    GROUP BY platform, event_type
                    ORDER BY total_events DESC
                """, params)
                
                metrics = {
                    'by_platform_and_type': cursor.fetchall(),
                    'summary': {}
                }
                
                # Get summary metrics
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_events,
                        COUNT(CASE WHEN processed THEN 1 END) as processed_events,
                        COUNT(DISTINCT platform) as platforms_count,
                        COUNT(DISTINCT event_type) as event_types_count,
                        COUNT(DISTINCT correlation_id) as correlations_count
                    FROM events 
                    {where_clause}
                """, params)
                
                metrics['summary'] = cursor.fetchone()
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to get event metrics: {e}")
            raise EventStorageError(f"Failed to get event metrics: {e}")
        finally:
            if conn:
                self._return_connection(conn)
                
    def cleanup_old_events(self, days_to_keep: int = 30) -> int:
        """Clean up old events to manage database size."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cutoff_date = datetime.now(timezone.utc).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timezone.timedelta(days=days_to_keep)
                
                cursor.execute("""
                    DELETE FROM events 
                    WHERE created_at < %s AND processed = TRUE
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old events")
                return deleted_count
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to cleanup old events: {e}")
            raise EventStorageError(f"Failed to cleanup old events: {e}")
        finally:
            if conn:
                self._return_connection(conn)
                
    def close(self):
        """Close the database connection pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


# Factory function for creating storage with configuration
def create_event_storage(config: Dict[str, Any]) -> EventStorage:
    """Create an event storage instance from configuration."""
    connection_string = config.get('connection_string')
    if not connection_string:
        # Build connection string from components
        host = config.get('host', 'localhost')
        port = config.get('port', 5432)
        database = config.get('database', 'events')
        user = config.get('user', 'postgres')
        password = config.get('password', '')
        
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
    return EventStorage(
        connection_string=connection_string,
        min_connections=config.get('min_connections', 1),
        max_connections=config.get('max_connections', 10)
    )

