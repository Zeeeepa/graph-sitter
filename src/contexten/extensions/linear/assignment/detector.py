"""
Linear Assignment Detection

Intelligent assignment detection and routing for Linear issues.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..types import LinearIssue, LinearUser, LinearTeam, LinearIssuePriority
from ..enhanced_client import EnhancedLinearClient

logger = logging.getLogger(__name__)


class AssignmentStrategy(Enum):
    """Assignment strategy types"""
    ROUND_ROBIN = "round_robin"
    WORKLOAD_BASED = "workload_based"
    SKILL_BASED = "skill_based"
    PRIORITY_BASED = "priority_based"
    RANDOM = "random"
    MANUAL = "manual"


class SkillLevel(Enum):
    """Skill level enumeration"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class UserSkill:
    """User skill representation"""
    skill_name: str
    level: SkillLevel
    confidence: float = 1.0  # 0.0 to 1.0
    last_used: Optional[datetime] = None
    
    @property
    def score(self) -> float:
        """Calculate skill score"""
        base_score = self.level.value * self.confidence
        
        # Decay score based on last usage
        if self.last_used:
            days_since_used = (datetime.now() - self.last_used).days
            decay_factor = max(0.5, 1.0 - (days_since_used / 365))  # Decay over a year
            base_score *= decay_factor
        
        return base_score


@dataclass
class UserProfile:
    """Extended user profile for assignment"""
    user: LinearUser
    skills: List[UserSkill] = field(default_factory=list)
    current_workload: int = 0
    max_workload: int = 10
    availability: float = 1.0  # 0.0 to 1.0
    timezone: Optional[str] = None
    preferred_issue_types: Set[str] = field(default_factory=set)
    last_assignment: Optional[datetime] = None
    
    @property
    def workload_ratio(self) -> float:
        """Get current workload ratio"""
        return self.current_workload / self.max_workload if self.max_workload > 0 else 0.0
    
    @property
    def is_available(self) -> bool:
        """Check if user is available for assignment"""
        return self.availability > 0.0 and self.workload_ratio < 1.0
    
    def get_skill_score(self, skill_name: str) -> float:
        """Get skill score for a specific skill"""
        for skill in self.skills:
            if skill.skill_name.lower() == skill_name.lower():
                return skill.score
        return 0.0
    
    def has_skill(self, skill_name: str, min_level: SkillLevel = SkillLevel.BEGINNER) -> bool:
        """Check if user has a specific skill at minimum level"""
        for skill in self.skills:
            if skill.skill_name.lower() == skill_name.lower():
                return skill.level.value >= min_level.value
        return False


@dataclass
class AssignmentRule:
    """Assignment rule configuration"""
    id: str
    name: str
    description: str
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    strategy: AssignmentStrategy = AssignmentStrategy.WORKLOAD_BASED
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    min_skill_level: SkillLevel = SkillLevel.BEGINNER
    team_id: Optional[str] = None
    priority_weight: float = 1.0
    enabled: bool = True
    
    def matches_issue(self, issue: LinearIssue) -> bool:
        """Check if rule matches an issue"""
        if not self.enabled:
            return False
        
        for condition in self.conditions:
            if not self._evaluate_condition(condition, issue):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any], issue: LinearIssue) -> bool:
        """Evaluate a single condition against an issue"""
        field = condition.get("field", "")
        operator = condition.get("operator", "equals")
        value = condition.get("value")
        
        # Get issue field value
        issue_value = getattr(issue, field, None)
        
        # Handle nested fields
        if "." in field:
            parts = field.split(".")
            issue_value = issue
            for part in parts:
                issue_value = getattr(issue_value, part, None) if issue_value else None
        
        # Evaluate condition
        if operator == "equals":
            return issue_value == value
        elif operator == "not_equals":
            return issue_value != value
        elif operator == "contains":
            return value in str(issue_value) if issue_value else False
        elif operator == "in":
            return issue_value in value if isinstance(value, list) else False
        elif operator == "greater_than":
            return float(issue_value) > float(value) if issue_value else False
        elif operator == "less_than":
            return float(issue_value) < float(value) if issue_value else False
        
        return False


@dataclass
class AssignmentResult:
    """Assignment result"""
    issue_id: str
    assigned_user: Optional[LinearUser] = None
    strategy_used: Optional[AssignmentStrategy] = None
    confidence_score: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    alternative_candidates: List[LinearUser] = field(default_factory=list)
    assignment_time: datetime = field(default_factory=datetime.now)
    success: bool = False
    error_message: Optional[str] = None


class AssignmentDetector:
    """Intelligent assignment detection and routing"""
    
    def __init__(self, linear_client: EnhancedLinearClient):
        self.linear_client = linear_client
        self.user_profiles: Dict[str, UserProfile] = {}
        self.assignment_rules: Dict[str, AssignmentRule] = {}
        self.assignment_history: List[AssignmentResult] = []
        self._round_robin_index = 0
        
        logger.info("Assignment detector initialized")
    
    async def initialize(self):
        """Initialize the assignment detector with team data"""
        try:
            # Load teams and users
            teams_response = await self.linear_client.get_teams()
            if teams_response.success:
                for team in teams_response.data:
                    await self._load_team_members(team.id)
            
            # Setup default assignment rules
            self._setup_default_rules()
            
            logger.info(f"Assignment detector initialized with {len(self.user_profiles)} users")
            
        except Exception as e:
            logger.error(f"Failed to initialize assignment detector: {e}")
    
    async def _load_team_members(self, team_id: str):
        """Load team members and create user profiles"""
        # This would require a team members API call
        # For now, create placeholder profiles
        pass
    
    def _setup_default_rules(self):
        """Setup default assignment rules"""
        # High priority issues
        high_priority_rule = AssignmentRule(
            id="high_priority",
            name="High Priority Issues",
            description="Assign high priority issues to experienced developers",
            conditions=[
                {"field": "priority", "operator": "in", "value": [LinearIssuePriority.URGENT.value, LinearIssuePriority.HIGH.value]}
            ],
            strategy=AssignmentStrategy.SKILL_BASED,
            min_skill_level=SkillLevel.ADVANCED,
            priority_weight=2.0
        )
        
        # Bug issues
        bug_rule = AssignmentRule(
            id="bug_issues",
            name="Bug Issues",
            description="Assign bug issues to developers with debugging skills",
            conditions=[
                {"field": "title", "operator": "contains", "value": "bug"},
                {"field": "description", "operator": "contains", "value": "error"}
            ],
            strategy=AssignmentStrategy.SKILL_BASED,
            required_skills=["debugging", "troubleshooting"],
            min_skill_level=SkillLevel.INTERMEDIATE
        )
        
        # Feature development
        feature_rule = AssignmentRule(
            id="feature_development",
            name="Feature Development",
            description="Assign feature development based on workload",
            conditions=[
                {"field": "title", "operator": "contains", "value": "feature"}
            ],
            strategy=AssignmentStrategy.WORKLOAD_BASED,
            preferred_skills=["frontend", "backend", "fullstack"]
        )
        
        # Default rule
        default_rule = AssignmentRule(
            id="default",
            name="Default Assignment",
            description="Default assignment strategy for all other issues",
            strategy=AssignmentStrategy.ROUND_ROBIN
        )
        
        self.assignment_rules = {
            "high_priority": high_priority_rule,
            "bug_issues": bug_rule,
            "feature_development": feature_rule,
            "default": default_rule
        }
    
    def add_user_profile(self, profile: UserProfile):
        """Add or update a user profile"""
        self.user_profiles[profile.user.id] = profile
        logger.info(f"Added user profile: {profile.user.name}")
    
    def update_user_workload(self, user_id: str, workload_change: int):
        """Update user workload"""
        if user_id in self.user_profiles:
            self.user_profiles[user_id].current_workload += workload_change
            self.user_profiles[user_id].current_workload = max(0, self.user_profiles[user_id].current_workload)
    
    def add_assignment_rule(self, rule: AssignmentRule):
        """Add an assignment rule"""
        self.assignment_rules[rule.id] = rule
        logger.info(f"Added assignment rule: {rule.name}")
    
    async def suggest_assignment(self, issue: LinearIssue) -> AssignmentResult:
        """Suggest assignment for an issue"""
        result = AssignmentResult(
            issue_id=issue.id,
            assignment_time=datetime.now()
        )
        
        try:
            # Find matching rule
            matching_rule = self._find_matching_rule(issue)
            if not matching_rule:
                matching_rule = self.assignment_rules.get("default")
            
            if not matching_rule:
                result.error_message = "No assignment rules configured"
                return result
            
            result.strategy_used = matching_rule.strategy
            result.reasoning.append(f"Using rule: {matching_rule.name}")
            
            # Get candidate users
            candidates = self._get_candidate_users(issue, matching_rule)
            if not candidates:
                result.error_message = "No available candidates found"
                return result
            
            # Select best candidate based on strategy
            selected_user = self._select_user(candidates, matching_rule, issue)
            if not selected_user:
                result.error_message = "Failed to select user"
                return result
            
            result.assigned_user = selected_user.user
            result.confidence_score = self._calculate_confidence(selected_user, matching_rule, issue)
            result.alternative_candidates = [p.user for p in candidates[:3] if p.user.id != selected_user.user.id]
            result.success = True
            
            # Update assignment history
            self.assignment_history.append(result)
            
            # Update user's last assignment time
            selected_user.last_assignment = datetime.now()
            
            logger.info(f"Suggested assignment: {issue.identifier} -> {selected_user.user.name}")
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Assignment suggestion failed: {e}")
        
        return result
    
    def _find_matching_rule(self, issue: LinearIssue) -> Optional[AssignmentRule]:
        """Find the first matching rule for an issue"""
        # Sort rules by priority weight (descending)
        sorted_rules = sorted(
            self.assignment_rules.values(),
            key=lambda r: r.priority_weight,
            reverse=True
        )
        
        for rule in sorted_rules:
            if rule.matches_issue(issue):
                return rule
        
        return None
    
    def _get_candidate_users(self, issue: LinearIssue, rule: AssignmentRule) -> List[UserProfile]:
        """Get candidate users for assignment"""
        candidates = []
        
        for profile in self.user_profiles.values():
            # Check availability
            if not profile.is_available:
                continue
            
            # Check team membership if specified
            if rule.team_id and issue.team and issue.team.id != rule.team_id:
                continue
            
            # Check required skills
            if rule.required_skills:
                has_all_required = all(
                    profile.has_skill(skill, rule.min_skill_level)
                    for skill in rule.required_skills
                )
                if not has_all_required:
                    continue
            
            candidates.append(profile)
        
        return candidates
    
    def _select_user(self, candidates: List[UserProfile], rule: AssignmentRule, issue: LinearIssue) -> Optional[UserProfile]:
        """Select the best user from candidates"""
        if not candidates:
            return None
        
        if rule.strategy == AssignmentStrategy.ROUND_ROBIN:
            return self._select_round_robin(candidates)
        elif rule.strategy == AssignmentStrategy.WORKLOAD_BASED:
            return self._select_by_workload(candidates)
        elif rule.strategy == AssignmentStrategy.SKILL_BASED:
            return self._select_by_skills(candidates, rule, issue)
        elif rule.strategy == AssignmentStrategy.PRIORITY_BASED:
            return self._select_by_priority(candidates, issue)
        elif rule.strategy == AssignmentStrategy.RANDOM:
            import random
            return random.choice(candidates)
        else:
            return candidates[0]  # Default to first candidate
    
    def _select_round_robin(self, candidates: List[UserProfile]) -> UserProfile:
        """Select user using round-robin strategy"""
        if self._round_robin_index >= len(candidates):
            self._round_robin_index = 0
        
        selected = candidates[self._round_robin_index]
        self._round_robin_index += 1
        
        return selected
    
    def _select_by_workload(self, candidates: List[UserProfile]) -> UserProfile:
        """Select user with lowest workload"""
        return min(candidates, key=lambda p: p.workload_ratio)
    
    def _select_by_skills(self, candidates: List[UserProfile], rule: AssignmentRule, issue: LinearIssue) -> UserProfile:
        """Select user based on skill matching"""
        def skill_score(profile: UserProfile) -> float:
            score = 0.0
            
            # Score for required skills
            for skill in rule.required_skills:
                score += profile.get_skill_score(skill) * 2.0
            
            # Score for preferred skills
            for skill in rule.preferred_skills:
                score += profile.get_skill_score(skill) * 1.0
            
            # Penalty for high workload
            score *= (1.0 - profile.workload_ratio * 0.5)
            
            return score
        
        return max(candidates, key=skill_score)
    
    def _select_by_priority(self, candidates: List[UserProfile], issue: LinearIssue) -> UserProfile:
        """Select user based on issue priority and user experience"""
        def priority_score(profile: UserProfile) -> float:
            # Higher priority issues should go to more experienced users
            if issue.priority in [LinearIssuePriority.URGENT, LinearIssuePriority.HIGH]:
                # Prefer users with higher skill levels
                avg_skill_level = sum(skill.level.value for skill in profile.skills) / len(profile.skills) if profile.skills else 1
                return avg_skill_level * (1.0 - profile.workload_ratio)
            else:
                # For lower priority, prefer users with lower workload
                return 1.0 - profile.workload_ratio
        
        return max(candidates, key=priority_score)
    
    def _calculate_confidence(self, profile: UserProfile, rule: AssignmentRule, issue: LinearIssue) -> float:
        """Calculate confidence score for assignment"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on skill match
        if rule.required_skills:
            skill_matches = sum(1 for skill in rule.required_skills if profile.has_skill(skill, rule.min_skill_level))
            confidence += (skill_matches / len(rule.required_skills)) * 0.3
        
        # Increase confidence based on availability
        confidence += (1.0 - profile.workload_ratio) * 0.2
        
        # Decrease confidence if user was recently assigned
        if profile.last_assignment:
            days_since_assignment = (datetime.now() - profile.last_assignment).days
            if days_since_assignment < 1:
                confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    async def auto_assign_issue(self, issue: LinearIssue) -> AssignmentResult:
        """Automatically assign an issue"""
        suggestion = await self.suggest_assignment(issue)
        
        if not suggestion.success or not suggestion.assigned_user:
            return suggestion
        
        try:
            # Update issue assignment via Linear API
            response = await self.linear_client.update_issue(
                issue.id,
                assignee_id=suggestion.assigned_user.id
            )
            
            if response.success:
                # Update user workload
                self.update_user_workload(suggestion.assigned_user.id, 1)
                suggestion.reasoning.append("Issue automatically assigned")
                logger.info(f"Auto-assigned issue {issue.identifier} to {suggestion.assigned_user.name}")
            else:
                suggestion.success = False
                suggestion.error_message = f"Failed to assign issue: {', '.join(response.errors)}"
        
        except Exception as e:
            suggestion.success = False
            suggestion.error_message = f"Assignment failed: {e}"
            logger.error(f"Auto-assignment failed: {e}")
        
        return suggestion
    
    def get_assignment_stats(self) -> Dict[str, Any]:
        """Get assignment statistics"""
        total_assignments = len(self.assignment_history)
        successful_assignments = len([a for a in self.assignment_history if a.success])
        
        # Strategy usage
        strategy_usage = {}
        for assignment in self.assignment_history:
            if assignment.strategy_used:
                strategy = assignment.strategy_used.value
                strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
        
        # User assignment counts
        user_assignments = {}
        for assignment in self.assignment_history:
            if assignment.assigned_user:
                user_id = assignment.assigned_user.id
                user_assignments[user_id] = user_assignments.get(user_id, 0) + 1
        
        return {
            "total_assignments": total_assignments,
            "successful_assignments": successful_assignments,
            "success_rate": successful_assignments / total_assignments if total_assignments > 0 else 0,
            "strategy_usage": strategy_usage,
            "user_assignments": user_assignments,
            "active_users": len([p for p in self.user_profiles.values() if p.is_available]),
            "total_users": len(self.user_profiles),
            "assignment_rules": len(self.assignment_rules)
        }

