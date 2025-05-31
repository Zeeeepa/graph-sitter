"""
Memory Manager - Extended memory management with persistent storage and intelligent retrieval
"""

import asyncio
import json
import sqlite3
import pickle
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import hashlib
import numpy as np
from pathlib import Path


@dataclass
class MemoryEntry:
    """Represents a memory entry with metadata"""
    context_id: str
    data: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    relevance_score: float = 1.0
    embedding: Optional[List[float]] = None


class MemoryManager:
    """
    Extended Memory Management System
    
    Features:
    - Persistent context storage
    - Cross-session memory retention
    - Intelligent context retrieval
    - Memory optimization algorithms
    - Semantic similarity search
    """
    
    def __init__(
        self,
        backend: str = "persistent",
        retention_days: int = 30,
        optimization_enabled: bool = True,
        db_path: str = "contexten_memory.db"
    ):
        """Initialize the Memory Manager"""
        self.backend = backend
        self.retention_days = retention_days
        self.optimization_enabled = optimization_enabled
        self.db_path = Path(db_path)
        
        self.logger = logging.getLogger(__name__)
        
        # In-memory cache for fast access
        self._memory_cache: Dict[str, MemoryEntry] = {}
        self._cache_size_limit = 1000
        
        # Statistics
        self._stats = {
            "total_entries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "optimizations_run": 0,
            "last_optimization": None
        }
        
        # Database connection
        self._db_conn: Optional[sqlite3.Connection] = None
        
    async def start(self):
        """Initialize the memory manager"""
        self.logger.info("Starting Memory Manager...")
        
        # Initialize database
        await self._init_database()
        
        # Load recent entries into cache
        await self._load_cache()
        
        # Start optimization task if enabled
        if self.optimization_enabled:
            asyncio.create_task(self._optimization_loop())
        
        self.logger.info("Memory Manager started successfully")
    
    async def stop(self):
        """Stop the memory manager and cleanup"""
        self.logger.info("Stopping Memory Manager...")
        
        # Save cache to database
        await self._save_cache()
        
        # Close database connection
        if self._db_conn:
            self._db_conn.close()
        
        self.logger.info("Memory Manager stopped successfully")
    
    async def _init_database(self):
        """Initialize the SQLite database"""
        self._db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Create tables
        self._db_conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                context_id TEXT PRIMARY KEY,
                data BLOB,
                metadata TEXT,
                timestamp TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                relevance_score REAL DEFAULT 1.0,
                embedding BLOB
            )
        """)
        
        self._db_conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_entries(timestamp)
        """)
        
        self._db_conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_relevance ON memory_entries(relevance_score)
        """)
        
        self._db_conn.commit()
    
    async def _load_cache(self):
        """Load recent entries into memory cache"""
        if not self._db_conn:
            return
        
        # Load most recent and frequently accessed entries
        cursor = self._db_conn.execute("""
            SELECT context_id, data, metadata, timestamp, access_count, 
                   last_accessed, relevance_score, embedding
            FROM memory_entries
            ORDER BY relevance_score DESC, access_count DESC, timestamp DESC
            LIMIT ?
        """, (self._cache_size_limit,))
        
        for row in cursor.fetchall():
            context_id, data_blob, metadata_json, timestamp_str, access_count, last_accessed_str, relevance_score, embedding_blob = row
            
            # Deserialize data
            data = pickle.loads(data_blob)
            metadata = json.loads(metadata_json)
            timestamp = datetime.fromisoformat(timestamp_str)
            last_accessed = datetime.fromisoformat(last_accessed_str) if last_accessed_str else None
            embedding = pickle.loads(embedding_blob) if embedding_blob else None
            
            entry = MemoryEntry(
                context_id=context_id,
                data=data,
                metadata=metadata,
                timestamp=timestamp,
                access_count=access_count,
                last_accessed=last_accessed,
                relevance_score=relevance_score,
                embedding=embedding
            )
            
            self._memory_cache[context_id] = entry
        
        self._stats["total_entries"] = len(self._memory_cache)
        self.logger.info(f"Loaded {len(self._memory_cache)} entries into cache")
    
    async def _save_cache(self):
        """Save cache entries to database"""
        if not self._db_conn:
            return
        
        for entry in self._memory_cache.values():
            await self._save_entry_to_db(entry)
        
        self._db_conn.commit()
    
    async def _save_entry_to_db(self, entry: MemoryEntry):
        """Save a single entry to database"""
        if not self._db_conn:
            return
        
        data_blob = pickle.dumps(entry.data)
        metadata_json = json.dumps(entry.metadata)
        embedding_blob = pickle.dumps(entry.embedding) if entry.embedding else None
        
        self._db_conn.execute("""
            INSERT OR REPLACE INTO memory_entries 
            (context_id, data, metadata, timestamp, access_count, last_accessed, relevance_score, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.context_id,
            data_blob,
            metadata_json,
            entry.timestamp.isoformat(),
            entry.access_count,
            entry.last_accessed.isoformat() if entry.last_accessed else None,
            entry.relevance_score,
            embedding_blob
        ))
    
    async def store_context(
        self,
        context_id: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        relevance_score: float = 1.0
    ) -> bool:
        """
        Store context data with metadata
        
        Args:
            context_id: Unique identifier for the context
            data: Data to store
            metadata: Additional metadata
            relevance_score: Initial relevance score
            
        Returns:
            Success status
        """
        try:
            metadata = metadata or {}
            
            # Generate embedding for semantic search
            embedding = await self._generate_embedding(data)
            
            entry = MemoryEntry(
                context_id=context_id,
                data=data,
                metadata=metadata,
                timestamp=datetime.now(),
                relevance_score=relevance_score,
                embedding=embedding
            )
            
            # Store in cache
            self._memory_cache[context_id] = entry
            
            # Manage cache size
            if len(self._memory_cache) > self._cache_size_limit:
                await self._evict_cache_entries()
            
            # Save to database
            await self._save_entry_to_db(entry)
            if self._db_conn:
                self._db_conn.commit()
            
            self._stats["total_entries"] += 1
            self.logger.debug(f"Stored context {context_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store context {context_id}: {e}")
            return False
    
    async def retrieve_context(
        self,
        context_id: Optional[str] = None,
        query: Optional[str] = None,
        relevance_threshold: float = 0.5,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve context data
        
        Args:
            context_id: Specific context ID to retrieve
            query: Query for semantic search
            relevance_threshold: Minimum relevance score
            limit: Maximum number of results
            
        Returns:
            Retrieved context data
        """
        try:
            if context_id:
                # Direct retrieval
                entry = await self._get_entry(context_id)
                if entry and entry.relevance_score >= relevance_threshold:
                    await self._update_access_stats(entry)
                    return {
                        "context_id": entry.context_id,
                        "data": entry.data,
                        "metadata": entry.metadata,
                        "relevance_score": entry.relevance_score
                    }
                return {}
            
            elif query:
                # Semantic search
                results = await self._semantic_search(query, relevance_threshold, limit)
                return {
                    "query": query,
                    "results": results,
                    "count": len(results)
                }
            
            else:
                # Return recent entries
                recent_entries = await self._get_recent_entries(limit)
                return {
                    "recent_entries": recent_entries,
                    "count": len(recent_entries)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve context: {e}")
            return {}
    
    async def _get_entry(self, context_id: str) -> Optional[MemoryEntry]:
        """Get a specific entry by ID"""
        # Check cache first
        if context_id in self._memory_cache:
            self._stats["cache_hits"] += 1
            return self._memory_cache[context_id]
        
        # Check database
        self._stats["cache_misses"] += 1
        
        if not self._db_conn:
            return None
        
        cursor = self._db_conn.execute("""
            SELECT data, metadata, timestamp, access_count, last_accessed, relevance_score, embedding
            FROM memory_entries WHERE context_id = ?
        """, (context_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        data_blob, metadata_json, timestamp_str, access_count, last_accessed_str, relevance_score, embedding_blob = row
        
        # Deserialize
        data = pickle.loads(data_blob)
        metadata = json.loads(metadata_json)
        timestamp = datetime.fromisoformat(timestamp_str)
        last_accessed = datetime.fromisoformat(last_accessed_str) if last_accessed_str else None
        embedding = pickle.loads(embedding_blob) if embedding_blob else None
        
        entry = MemoryEntry(
            context_id=context_id,
            data=data,
            metadata=metadata,
            timestamp=timestamp,
            access_count=access_count,
            last_accessed=last_accessed,
            relevance_score=relevance_score,
            embedding=embedding
        )
        
        # Add to cache
        self._memory_cache[context_id] = entry
        
        return entry
    
    async def _update_access_stats(self, entry: MemoryEntry):
        """Update access statistics for an entry"""
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        
        # Update relevance score based on access pattern
        time_factor = 1.0 - (datetime.now() - entry.timestamp).days / 365.0
        access_factor = min(entry.access_count / 10.0, 1.0)
        entry.relevance_score = max(0.1, time_factor * 0.5 + access_factor * 0.5)
    
    async def _semantic_search(
        self,
        query: str,
        threshold: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        query_embedding = await self._generate_embedding(query)
        if not query_embedding:
            return []
        
        results = []
        
        # Search in cache
        for entry in self._memory_cache.values():
            if entry.embedding:
                similarity = self._calculate_similarity(query_embedding, entry.embedding)
                if similarity >= threshold:
                    results.append({
                        "context_id": entry.context_id,
                        "data": entry.data,
                        "metadata": entry.metadata,
                        "similarity": similarity,
                        "relevance_score": entry.relevance_score
                    })
        
        # Sort by similarity and relevance
        results.sort(key=lambda x: (x["similarity"], x["relevance_score"]), reverse=True)
        
        return results[:limit]
    
    async def _generate_embedding(self, data: Any) -> Optional[List[float]]:
        """Generate embedding for data (simplified implementation)"""
        try:
            # Convert data to string representation
            if isinstance(data, str):
                text = data
            else:
                text = json.dumps(data, default=str)
            
            # Simple hash-based embedding (in production, use proper embedding models)
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to normalized vector
            embedding = [float(b) / 255.0 for b in hash_bytes[:32]]
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception:
            return 0.0
    
    async def _get_recent_entries(self, limit: int) -> List[Dict[str, Any]]:
        """Get recent entries"""
        entries = sorted(
            self._memory_cache.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        return [
            {
                "context_id": entry.context_id,
                "data": entry.data,
                "metadata": entry.metadata,
                "timestamp": entry.timestamp.isoformat(),
                "relevance_score": entry.relevance_score
            }
            for entry in entries[:limit]
        ]
    
    async def _evict_cache_entries(self):
        """Evict least relevant entries from cache"""
        if len(self._memory_cache) <= self._cache_size_limit:
            return
        
        # Sort by relevance score and last access time
        entries = sorted(
            self._memory_cache.items(),
            key=lambda x: (x[1].relevance_score, x[1].last_accessed or datetime.min)
        )
        
        # Remove least relevant entries
        entries_to_remove = len(self._memory_cache) - self._cache_size_limit + 100  # Remove extra for buffer
        
        for i in range(entries_to_remove):
            context_id, entry = entries[i]
            
            # Save to database before removing from cache
            await self._save_entry_to_db(entry)
            del self._memory_cache[context_id]
    
    async def _optimization_loop(self):
        """Background optimization loop"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self.optimize()
            except Exception as e:
                self.logger.error(f"Optimization loop error: {e}")
    
    async def optimize(self) -> Dict[str, Any]:
        """Run memory optimization"""
        self.logger.info("Starting memory optimization...")
        
        optimization_results = {
            "entries_before": len(self._memory_cache),
            "entries_removed": 0,
            "entries_updated": 0,
            "database_cleaned": False
        }
        
        # Remove expired entries
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        expired_entries = []
        
        for context_id, entry in self._memory_cache.items():
            if entry.timestamp < cutoff_date and entry.relevance_score < 0.3:
                expired_entries.append(context_id)
        
        for context_id in expired_entries:
            del self._memory_cache[context_id]
            optimization_results["entries_removed"] += 1
        
        # Update relevance scores
        for entry in self._memory_cache.values():
            old_score = entry.relevance_score
            
            # Decay relevance over time
            age_days = (datetime.now() - entry.timestamp).days
            time_decay = max(0.1, 1.0 - (age_days / 365.0))
            
            # Boost based on access frequency
            access_boost = min(entry.access_count / 100.0, 0.5)
            
            entry.relevance_score = max(0.1, time_decay * 0.7 + access_boost * 0.3)
            
            if abs(entry.relevance_score - old_score) > 0.1:
                optimization_results["entries_updated"] += 1
        
        # Clean database
        if self._db_conn:
            self._db_conn.execute("""
                DELETE FROM memory_entries 
                WHERE timestamp < ? AND relevance_score < 0.2
            """, (cutoff_date.isoformat(),))
            self._db_conn.commit()
            optimization_results["database_cleaned"] = True
        
        optimization_results["entries_after"] = len(self._memory_cache)
        
        self._stats["optimizations_run"] += 1
        self._stats["last_optimization"] = datetime.now().isoformat()
        
        self.logger.info(f"Memory optimization completed: {optimization_results}")
        return optimization_results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory management statistics"""
        return {
            **self._stats,
            "cache_size": len(self._memory_cache),
            "cache_limit": self._cache_size_limit,
            "retention_days": self.retention_days,
            "optimization_enabled": self.optimization_enabled,
            "backend": self.backend
        }
    
    def is_healthy(self) -> bool:
        """Check if memory manager is healthy"""
        return (
            self._db_conn is not None and
            len(self._memory_cache) <= self._cache_size_limit * 1.1  # Allow 10% overflow
        )

