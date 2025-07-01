"""
Linear Assignment Detector

Intelligent assignment detection system that:
- Detects when the bot is assigned to issues
- Implements auto-assignment based on labels and keywords
- Tracks assignment history and rate limiting
- Provides assignment analytics and monitoring
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field

from .config import LinearIntegrationConfig
from .types import (
    LinearIssue, LinearEvent, AssignmentEvent, AssignmentAction, 
    ComponentStats
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class AssignmentRecord:
    """Record of an assignment event"""
    issue_id: str
    action: AssignmentAction
    assignee_id: Optional[str]
    timestamp: datetime
    source: str  # 'webhook', 'monitoring', 'auto'
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssignmentStats:
    """Assignment detection statistics"""
    assignments_detected: int = 0
    auto_assignments_made: int = 0
    assignments_processed: int = 0
    assignments_failed: int = 0
    rate_limit_hits: int = 0
    last_assignment: Optional[datetime] = None
    last_error: Optional[str] = None


class AssignmentDetector:
    """Intelligent assignment detection and auto-assignment system"""
    
    def __init__(self, config: LinearIntegrationConfig):
        self.config = config
        self.assignment_config = config.assignment
        self.bot_config = config.bot
        
        # Assignment tracking
        self.processed_assignments: Set[str] = set()
        self.assignment_history: List[AssignmentRecord] = []
        self.assignment_counts: Dict[str, int] = {}  # Hour -> count
        
        # Statistics
        self.stats = ComponentStats()
        self.assignment_stats = AssignmentStats()
        self.start_time = datetime.now()
        
        # Compiled regex patterns for keyword matching
        self.keyword_patterns = [
            re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            for keyword in self.assignment_config.auto_assign_keywords
        ]
        
        logger.info("Assignment detector initialized")
    
    def _is_bot_user(self, user_id: Optional[str], user_email: Optional[str] = None, user_name: Optional[str] = None) -> bool:
        """Check if a user is the bot"""
        if not user_id and not user_email and not user_name:
            return False
        
        # Check by user ID
        if user_id and self.bot_config.bot_user_id:
            if user_id == self.bot_config.bot_user_id:
                return True
        
        # Check by email
        if user_email and self.bot_config.bot_email:
            if user_email.lower() == self.bot_config.bot_email.lower():
                return True
        
        # Check by name
        if user_name:
            for bot_name in self.bot_config.bot_names:
                if bot_name.lower() in user_name.lower():
                    return True
        
        return False
    
    def _extract_assignee_info(self, event_data: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Extract assignee information from event data"""
        assignee_info: Dict[str, Optional[str]] = {
            "id": None,
            "email": None,
            "name": None
        }
        
        # Common paths where assignee data might be found
        assignee_paths = [
            ["data", "assignee"],
            ["assignee"],
            ["data", "issue", "assignee"],
            ["issue", "assignee"]
        ]
        
        for path in assignee_paths:
            current: Any = event_data
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    current = None
                    break
            
            if current:
                assignee_info["id"] = current.get("id")
                assignee_info["email"] = current.get("email")
                assignee_info["name"] = current.get("name")
                break
        
        return assignee_info
    
    def _extract_previous_assignee_info(self, event_data: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Extract previous assignee information from event data"""
        # Look for updatedFrom or previous data
        previous_paths = [
            ["data", "updatedFrom", "assignee"],
            ["updatedFrom", "assignee"],
            ["previousValues", "assignee"]
        ]
        
        for path in previous_paths:
            current: Any = event_data
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    current = None
                    break
            
            if current:
                return {
                    "id": current.get("id"),
                    "email": current.get("email"),
                    "name": current.get("name")
                }
        
        return {"id": None, "email": None, "name": None}
    
    async def detect_assignment_change(self, event: Dict[str, Any]) -> Optional[AssignmentEvent]:
        """Detect assignment changes from webhook events"""
        try:
            event_type = event.get("type", "")
            
            # Only process issue-related events
            if event_type not in ["Issue", "IssueUpdate"]:
                return None
            
            # Extract issue ID
            issue_id = None
            issue_paths = [
                ["data", "id"],
                ["data", "issue", "id"],
                ["issue", "id"],
                ["id"]
            ]
            
            for path in issue_paths:
                current: Any = event
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break
                if current:
                    issue_id = current
                    break
            
            if not issue_id:
                logger.debug("No issue ID found in event")
                return None
            
            # Extract assignee information
            current_assignee = self._extract_assignee_info(event)
            previous_assignee = self._extract_previous_assignee_info(event)
            
            # Determine assignment action
            action = None
            assignee_id = None
            previous_assignee_id = None
            
            current_is_bot = self._is_bot_user(
                current_assignee["id"], 
                current_assignee["email"], 
                current_assignee["name"]
            )
            
            previous_is_bot = self._is_bot_user(
                previous_assignee["id"], 
                previous_assignee["email"], 
                previous_assignee["name"]
            )
            
            if current_is_bot and not previous_is_bot:
                # Bot was assigned
                action = AssignmentAction.ASSIGNED
                assignee_id = current_assignee["id"]
                previous_assignee_id = previous_assignee["id"]
                
            elif not current_is_bot and previous_is_bot:
                # Bot was unassigned
                action = AssignmentAction.UNASSIGNED
                assignee_id = current_assignee["id"]
                previous_assignee_id = previous_assignee["id"]
                
            elif current_is_bot and previous_is_bot:
                # Bot reassigned (shouldn't happen but handle it)
                if current_assignee["id"] != previous_assignee["id"]:
                    action = AssignmentAction.REASSIGNED
                    assignee_id = current_assignee["id"]
                    previous_assignee_id = previous_assignee["id"]
            
            if action:
                assignment_event = AssignmentEvent(
                    issue_id=issue_id,
                    action=action,
                    assignee_id=assignee_id,
                    previous_assignee_id=previous_assignee_id,
                    timestamp=datetime.now(),
                    metadata={
                        "event_type": event_type,
                        "source": "webhook",
                        "current_assignee": current_assignee,
                        "previous_assignee": previous_assignee
                    }
                )
                
                self.assignment_stats.assignments_detected += 1
                self.assignment_stats.last_assignment = datetime.now()
                
                logger.info(f"Detected assignment change: {action.value} for issue {issue_id}")
                return assignment_event
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting assignment change: {e}")
            self.assignment_stats.last_error = str(e)
            return None
    
    async def is_bot_assigned(self, issue: LinearIssue) -> bool:
        """Check if the bot is assigned to an issue"""
        if not issue.assignee:
            return False
        
        return self._is_bot_user(
            issue.assignee.id,
            issue.assignee.email,
            issue.assignee.name
        )
    
    async def should_process_assignment(self, assignment_event: AssignmentEvent) -> bool:
        """Check if an assignment should be processed"""
        try:
            # Check if already processed
            if assignment_event.issue_id in self.processed_assignments:
                logger.debug(f"Assignment for issue {assignment_event.issue_id} already processed")
                return False
            
            # Check rate limiting
            if not self._check_rate_limit():
                logger.warning("Assignment rate limit exceeded")
                self.assignment_stats.rate_limit_hits += 1
                return False
            
            # Only process assignments (not unassignments)
            if assignment_event.action != AssignmentAction.ASSIGNED:
                logger.debug(f"Skipping non-assignment action: {assignment_event.action}")
                return False
            
            # Check cooldown period
            if self._is_in_cooldown(assignment_event.issue_id):
                logger.debug(f"Issue {assignment_event.issue_id} is in cooldown period")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if assignment should be processed: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        current_count = self.assignment_counts.get(current_hour, 0)
        
        return current_count < self.assignment_config.max_assignments_per_hour
    
    def _is_in_cooldown(self, issue_id: str) -> bool:
        """Check if an issue is in cooldown period"""
        cooldown_period = timedelta(seconds=self.assignment_config.assignment_cooldown)
        cutoff_time = datetime.now() - cooldown_period
        
        # Check recent assignment history
        for record in self.assignment_history:
            if (record.issue_id == issue_id and 
                record.timestamp > cutoff_time):
                return True
        
        return False
    
    async def mark_assignment_processed(self, issue_id: str) -> None:
        """Mark an assignment as processed"""
        self.processed_assignments.add(issue_id)
        
        # Update rate limiting counter
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        self.assignment_counts[current_hour] = self.assignment_counts.get(current_hour, 0) + 1
        
        # Add to history
        record = AssignmentRecord(
            issue_id=issue_id,
            action=AssignmentAction.ASSIGNED,
            assignee_id=self.bot_config.bot_user_id,
            timestamp=datetime.now(),
            source="processed"
        )
        self.assignment_history.append(record)
        
        # Clean up old history
        self._cleanup_old_records()
        
        self.assignment_stats.assignments_processed += 1
        logger.info(f"Marked assignment for issue {issue_id} as processed")
    
    def _cleanup_old_records(self) -> None:
        """Clean up old assignment records"""
        # Keep records for last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Clean assignment history
        self.assignment_history = [
            record for record in self.assignment_history
            if record.timestamp > cutoff_time
        ]
        
        # Clean rate limiting counters
        current_time = datetime.now()
        hours_to_keep = []
        for i in range(24):
            hour = (current_time - timedelta(hours=i)).strftime("%Y-%m-%d-%H")
            hours_to_keep.append(hour)
        
        self.assignment_counts = {
            hour: count for hour, count in self.assignment_counts.items()
            if hour in hours_to_keep
        }
    
    async def detect_auto_assignment_candidates(self, event: Dict[str, Any]) -> bool:
        """Detect if an issue should be auto-assigned to the bot"""
        try:
            event_type = event.get("type", "")
            
            # Only process new issues or issue updates
            if event_type not in ["Issue", "IssueUpdate"]:
                return False
            
            # Extract issue data
            issue_data = event.get("data", {})
            if not issue_data:
                return False
            
            # Check if already assigned
            assignee = issue_data.get("assignee")
            if assignee:
                logger.debug("Issue already has assignee, skipping auto-assignment")
                return False
            
            # Check labels
            labels = issue_data.get("labels", {}).get("nodes", [])
            label_names = [label.get("name", "").lower() for label in labels]
            
            has_auto_assign_label = any(
                label in label_names 
                for label in self.assignment_config.auto_assign_labels
            )
            
            if has_auto_assign_label:
                logger.info(f"Found auto-assign label in issue {issue_data.get('id')}")
                return True
            
            # Check keywords in title and description
            title = issue_data.get("title", "")
            description = issue_data.get("description", "")
            content = f"{title} {description}".lower()
            
            for pattern in self.keyword_patterns:
                if pattern.search(content):
                    logger.info(f"Found auto-assign keyword in issue {issue_data.get('id')}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting auto-assignment candidates: {e}")
            return False
    
    async def create_auto_assignment(self, issue_id: str, linear_client) -> bool:
        """Create an auto-assignment for an issue"""
        try:
            if not self.bot_config.bot_user_id:
                logger.error("Bot user ID not configured, cannot auto-assign")
                return False
            
            # Check rate limits
            if not self._check_rate_limit():
                logger.warning("Auto-assignment rate limit exceeded")
                self.assignment_stats.rate_limit_hits += 1
                return False
            
            # Assign the issue to the bot
            success = await linear_client.update_issue(
                issue_id,
                {"assignee_id": self.bot_config.bot_user_id}
            )
            
            if success:
                # Record the auto-assignment
                record = AssignmentRecord(
                    issue_id=issue_id,
                    action=AssignmentAction.ASSIGNED,
                    assignee_id=self.bot_config.bot_user_id,
                    timestamp=datetime.now(),
                    source="auto",
                    metadata={"auto_assigned": True}
                )
                self.assignment_history.append(record)
                
                # Update counters
                current_hour = datetime.now().strftime("%Y-%m-%d-%H")
                self.assignment_counts[current_hour] = self.assignment_counts.get(current_hour, 0) + 1
                
                self.assignment_stats.auto_assignments_made += 1
                logger.info(f"Auto-assigned issue {issue_id} to bot")
                return True
            else:
                logger.error(f"Failed to auto-assign issue {issue_id}")
                self.assignment_stats.assignments_failed += 1
                return False
            
        except Exception as e:
            logger.error(f"Error creating auto-assignment for issue {issue_id}: {e}")
            self.assignment_stats.assignments_failed += 1
            self.assignment_stats.last_error = str(e)
            return False
    
    def get_stats(self) -> ComponentStats:
        """Get assignment detection statistics"""
        self.stats.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        self.stats.requests_made = self.assignment_stats.assignments_detected
        self.stats.requests_successful = self.assignment_stats.assignments_processed
        self.stats.requests_failed = self.assignment_stats.assignments_failed
        self.stats.last_error = self.assignment_stats.last_error
        self.stats.last_request = self.assignment_stats.last_assignment
        
        return self.stats
    
    def get_assignment_stats(self) -> AssignmentStats:
        """Get detailed assignment statistics"""
        return self.assignment_stats
    
    def get_assignment_history(self, hours: int = 24) -> List[AssignmentRecord]:
        """Get assignment history for the specified number of hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            record for record in self.assignment_history
            if record.timestamp > cutoff_time
        ]
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get rate limiting information"""
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        current_count = self.assignment_counts.get(current_hour, 0)
        
        return {
            "current_hour_assignments": current_count,
            "max_assignments_per_hour": self.assignment_config.max_assignments_per_hour,
            "remaining_assignments": max(0, self.assignment_config.max_assignments_per_hour - current_count),
            "rate_limit_hits": self.assignment_stats.rate_limit_hits,
            "assignment_cooldown_seconds": self.assignment_config.assignment_cooldown
        }
    
    def clear_processed_assignments(self) -> None:
        """Clear the processed assignments cache"""
        self.processed_assignments.clear()
        logger.info("Cleared processed assignments cache")
    
    def reset_rate_limits(self) -> None:
        """Reset rate limiting counters"""
        self.assignment_counts.clear()
        self.assignment_stats.rate_limit_hits = 0
        logger.info("Reset rate limiting counters")
