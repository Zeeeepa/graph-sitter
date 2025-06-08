"""State manager for Contexten.

This module provides the StateManager class which handles application
state management and persistence.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Type

from ..events.bus import Event

logger = logging.getLogger(__name__)

class StateError(Exception):
    """Base class for state-related errors."""
    pass

class StateTransactionError(StateError):
    """Error raised when state transaction fails."""
    pass

class StateManager:
    """Manager for application state.
    
    This class provides state management capabilities including:
    - State storage and retrieval
    - State persistence
    - State change notifications
    - Transaction support
    """

    def __init__(self, app: 'ContextenApp'):
        """Initialize the state manager.
        
        Args:
            app: The ContextenApp instance this manager belongs to
        """
        self.app = app
        self._state: Dict[str, Any] = {}
        self._observers: Dict[str, List[callable]] = {}
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._persistence_enabled = False
        self._persistence_path: Optional[str] = None

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value.
        
        Args:
            key: State key
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        return self._state.get(key, default)

    async def set_state(
        self,
        key: str,
        value: Any,
        transaction_id: Optional[str] = None
    ) -> None:
        """Set state value.
        
        Args:
            key: State key
            value: State value
            transaction_id: Optional transaction ID
            
        Raises:
            StateTransactionError: If transaction is invalid
        """
        if transaction_id:
            if transaction_id not in self._transactions:
                raise StateTransactionError(
                    f"Invalid transaction ID: {transaction_id}"
                )
            self._transactions[transaction_id][key] = value
        else:
            async with self._get_lock(key):
                old_value = self._state.get(key)
                self._state[key] = value
                await self._notify_observers(key, old_value, value)
                await self._persist_state()

    def delete_state(self, key: str) -> None:
        """Delete state value.
        
        Args:
            key: State key to delete
        """
        self._state.pop(key, None)

    def observe_state(
        self,
        key: str,
        observer: callable
    ) -> None:
        """Add state observer.
        
        Args:
            key: State key to observe
            observer: Async callable(key, old_value, new_value)
        """
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(observer)

    def remove_observer(
        self,
        key: str,
        observer: callable
    ) -> None:
        """Remove state observer.
        
        Args:
            key: State key
            observer: Observer to remove
        """
        if key in self._observers:
            if observer in self._observers[key]:
                self._observers[key].remove(observer)

    async def begin_transaction(self) -> str:
        """Begin a new state transaction.
        
        Returns:
            Transaction ID
        """
        transaction_id = f"tx_{datetime.utcnow().timestamp()}"
        self._transactions[transaction_id] = {}
        return transaction_id

    async def commit_transaction(self, transaction_id: str) -> None:
        """Commit a state transaction.
        
        Args:
            transaction_id: Transaction ID to commit
            
        Raises:
            StateTransactionError: If transaction is invalid
        """
        if transaction_id not in self._transactions:
            raise StateTransactionError(
                f"Invalid transaction ID: {transaction_id}"
            )

        try:
            # Get all required locks
            keys = list(self._transactions[transaction_id].keys())
            async with self._get_locks(keys):
                # Apply changes
                for key, value in self._transactions[transaction_id].items():
                    old_value = self._state.get(key)
                    self._state[key] = value
                    await self._notify_observers(key, old_value, value)

                # Persist state
                await self._persist_state()

        finally:
            # Clean up transaction
            del self._transactions[transaction_id]

    async def rollback_transaction(self, transaction_id: str) -> None:
        """Rollback a state transaction.
        
        Args:
            transaction_id: Transaction ID to rollback
            
        Raises:
            StateTransactionError: If transaction is invalid
        """
        if transaction_id not in self._transactions:
            raise StateTransactionError(
                f"Invalid transaction ID: {transaction_id}"
            )
        del self._transactions[transaction_id]

    def enable_persistence(self, path: str) -> None:
        """Enable state persistence.
        
        Args:
            path: Path to state file
        """
        self._persistence_enabled = True
        self._persistence_path = path

    def disable_persistence(self) -> None:
        """Disable state persistence."""
        self._persistence_enabled = False
        self._persistence_path = None

    async def load_state(self) -> None:
        """Load persisted state.
        
        Raises:
            StateError: If state cannot be loaded
        """
        if not self._persistence_enabled or not self._persistence_path:
            return

        try:
            with open(self._persistence_path, 'r') as f:
                self._state = json.load(f)
        except FileNotFoundError:
            # No persisted state yet
            pass
        except Exception as e:
            raise StateError(f"Failed to load state: {e}")

    async def _persist_state(self) -> None:
        """Persist current state.
        
        Raises:
            StateError: If state cannot be persisted
        """
        if not self._persistence_enabled or not self._persistence_path:
            return

        try:
            with open(self._persistence_path, 'w') as f:
                json.dump(self._state, f)
        except Exception as e:
            raise StateError(f"Failed to persist state: {e}")

    async def _notify_observers(
        self,
        key: str,
        old_value: Any,
        new_value: Any
    ) -> None:
        """Notify state observers of change.
        
        Args:
            key: Changed state key
            old_value: Previous value
            new_value: New value
        """
        if key in self._observers:
            for observer in self._observers[key]:
                try:
                    await observer(key, old_value, new_value)
                except Exception as e:
                    logger.error(
                        f"Error in state observer for {key}: {e}",
                        exc_info=True
                    )

        # Publish state change event
        await self.app.event_bus.publish(Event(
            type="state_changed",
            source="state_manager",
            data={
                "key": key,
                "old_value": old_value,
                "new_value": new_value,
            }
        ))

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get lock for state key.
        
        Args:
            key: State key
            
        Returns:
            Lock for the key
        """
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def _get_locks(self, keys: List[str]) -> List[asyncio.Lock]:
        """Get locks for multiple state keys.
        
        Args:
            keys: State keys
            
        Returns:
            List of locks
        """
        # Sort keys to prevent deadlocks
        sorted_keys = sorted(keys)
        return [self._get_lock(key) for key in sorted_keys]

    async def health_check(self) -> Dict[str, Any]:
        """Check state manager health.
        
        Returns:
            Dict containing health status
        """
        return {
            "status": "healthy",
            "state_keys": len(self._state),
            "active_transactions": len(self._transactions),
            "observers": sum(len(obs) for obs in self._observers.values()),
            "persistence_enabled": self._persistence_enabled,
            "timestamp": self.app.current_time.isoformat(),
        }

