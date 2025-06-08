"""Extension capabilities system for the unified extension framework.

This module defines the capability system that allows extensions to advertise
their functionality and enables capability-based discovery and routing.
"""

import enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class CapabilityType(str, enum.Enum):
    """Types of capabilities that extensions can provide."""
    
    # Code Analysis & Manipulation
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_TRANSFORMATION = "code_transformation"
    AST_MANIPULATION = "ast_manipulation"
    SYNTAX_HIGHLIGHTING = "syntax_highlighting"
    
    # Version Control
    GIT_OPERATIONS = "git_operations"
    REPOSITORY_MANAGEMENT = "repository_management"
    BRANCH_MANAGEMENT = "branch_management"
    PULL_REQUEST_MANAGEMENT = "pull_request_management"
    
    # Issue & Project Management
    ISSUE_TRACKING = "issue_tracking"
    PROJECT_MANAGEMENT = "project_management"
    TASK_MANAGEMENT = "task_management"
    WORKFLOW_AUTOMATION = "workflow_automation"
    
    # CI/CD & DevOps
    CONTINUOUS_INTEGRATION = "continuous_integration"
    CONTINUOUS_DEPLOYMENT = "continuous_deployment"
    BUILD_AUTOMATION = "build_automation"
    TEST_AUTOMATION = "test_automation"
    DEPLOYMENT_MANAGEMENT = "deployment_management"
    
    # Communication & Notifications
    MESSAGING = "messaging"
    NOTIFICATIONS = "notifications"
    EMAIL_SENDING = "email_sending"
    CHAT_INTEGRATION = "chat_integration"
    
    # Data & Storage
    DATA_STORAGE = "data_storage"
    DATA_RETRIEVAL = "data_retrieval"
    DATA_TRANSFORMATION = "data_transformation"
    CACHING = "caching"
    
    # Compute & Processing
    SERVERLESS_COMPUTE = "serverless_compute"
    BATCH_PROCESSING = "batch_processing"
    STREAM_PROCESSING = "stream_processing"
    PARALLEL_PROCESSING = "parallel_processing"
    
    # AI & Machine Learning
    AI_AGENT_INTEGRATION = "ai_agent_integration"
    NATURAL_LANGUAGE_PROCESSING = "natural_language_processing"
    CODE_COMPLETION = "code_completion"
    INTELLIGENT_SUGGESTIONS = "intelligent_suggestions"
    
    # Monitoring & Observability
    HEALTH_MONITORING = "health_monitoring"
    PERFORMANCE_MONITORING = "performance_monitoring"
    LOGGING = "logging"
    METRICS_COLLECTION = "metrics_collection"
    ALERTING = "alerting"
    
    # Security
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SECURITY_SCANNING = "security_scanning"
    VULNERABILITY_DETECTION = "vulnerability_detection"
    
    # Integration & Connectivity
    API_INTEGRATION = "api_integration"
    WEBHOOK_HANDLING = "webhook_handling"
    EVENT_PROCESSING = "event_processing"
    MESSAGE_QUEUING = "message_queuing"
    
    # Context & Knowledge Management
    CONTEXT_MANAGEMENT = "context_management"
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    DOCUMENTATION_GENERATION = "documentation_generation"
    
    # Custom capabilities
    CUSTOM = "custom"


class CapabilityParameter(BaseModel):
    """Parameter definition for a capability."""
    name: str
    type: str  # "string", "integer", "boolean", "object", "array"
    description: str = ""
    required: bool = True
    default: Optional[Any] = None
    enum_values: Optional[List[Any]] = None
    validation_pattern: Optional[str] = None


class CapabilityMethod(BaseModel):
    """Method definition for a capability."""
    name: str
    description: str = ""
    parameters: List[CapabilityParameter] = Field(default_factory=list)
    return_type: str = "object"
    return_description: str = ""
    async_method: bool = True
    examples: List[Dict[str, Any]] = Field(default_factory=list)


class ExtensionCapability(BaseModel):
    """Extension capability definition."""
    name: str
    type: CapabilityType
    version: str = "1.0.0"
    description: str = ""
    methods: List[CapabilityMethod] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Quality attributes
    reliability_level: str = "standard"  # "basic", "standard", "high", "critical"
    performance_tier: str = "standard"   # "basic", "standard", "high", "premium"
    security_level: str = "standard"     # "basic", "standard", "high", "enterprise"


class CapabilityRegistry:
    """Registry for managing extension capabilities."""
    
    def __init__(self):
        """Initialize capability registry."""
        self._capabilities: Dict[str, Dict[str, ExtensionCapability]] = {}  # type -> {name -> capability}
        self._extension_capabilities: Dict[str, List[ExtensionCapability]] = {}  # extension -> capabilities
        self._capability_providers: Dict[str, List[str]] = {}  # capability_name -> [extension_names]
    
    def register_capability(
        self, 
        extension_name: str, 
        capability: ExtensionCapability
    ) -> bool:
        """Register a capability for an extension.
        
        Args:
            extension_name: Name of the extension providing the capability
            capability: Capability definition
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Add to type-based index
            if capability.type.value not in self._capabilities:
                self._capabilities[capability.type.value] = {}
            self._capabilities[capability.type.value][capability.name] = capability
            
            # Add to extension-based index
            if extension_name not in self._extension_capabilities:
                self._extension_capabilities[extension_name] = []
            self._extension_capabilities[extension_name].append(capability)
            
            # Add to provider index
            if capability.name not in self._capability_providers:
                self._capability_providers[capability.name] = []
            if extension_name not in self._capability_providers[capability.name]:
                self._capability_providers[capability.name].append(extension_name)
            
            return True
            
        except Exception:
            return False
    
    def unregister_extension_capabilities(self, extension_name: str) -> bool:
        """Unregister all capabilities for an extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if extension_name not in self._extension_capabilities:
                return True
                
            capabilities = self._extension_capabilities[extension_name]
            
            # Remove from type-based index
            for capability in capabilities:
                if capability.type.value in self._capabilities:
                    self._capabilities[capability.type.value].pop(capability.name, None)
                    if not self._capabilities[capability.type.value]:
                        del self._capabilities[capability.type.value]
                
                # Remove from provider index
                if capability.name in self._capability_providers:
                    if extension_name in self._capability_providers[capability.name]:
                        self._capability_providers[capability.name].remove(extension_name)
                    if not self._capability_providers[capability.name]:
                        del self._capability_providers[capability.name]
            
            # Remove from extension-based index
            del self._extension_capabilities[extension_name]
            
            return True
            
        except Exception:
            return False
    
    def find_capabilities_by_type(self, capability_type: CapabilityType) -> List[ExtensionCapability]:
        """Find capabilities by type.
        
        Args:
            capability_type: Type of capability to find
            
        Returns:
            List of capabilities of the specified type
        """
        return list(self._capabilities.get(capability_type.value, {}).values())
    
    def find_capability_by_name(self, name: str) -> Optional[ExtensionCapability]:
        """Find capability by name.
        
        Args:
            name: Capability name
            
        Returns:
            Capability if found, None otherwise
        """
        for type_capabilities in self._capabilities.values():
            if name in type_capabilities:
                return type_capabilities[name]
        return None
    
    def find_providers_for_capability(self, capability_name: str) -> List[str]:
        """Find extensions that provide a specific capability.
        
        Args:
            capability_name: Name of the capability
            
        Returns:
            List of extension names that provide the capability
        """
        return self._capability_providers.get(capability_name, [])
    
    def get_extension_capabilities(self, extension_name: str) -> List[ExtensionCapability]:
        """Get all capabilities provided by an extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            List of capabilities provided by the extension
        """
        return self._extension_capabilities.get(extension_name, [])
    
    def search_capabilities(
        self,
        query: str,
        capability_type: Optional[CapabilityType] = None,
        tags: Optional[List[str]] = None,
        reliability_level: Optional[str] = None
    ) -> List[ExtensionCapability]:
        """Search capabilities based on criteria.
        
        Args:
            query: Search query (matches name and description)
            capability_type: Optional capability type filter
            tags: Optional tags filter
            reliability_level: Optional reliability level filter
            
        Returns:
            List of matching capabilities
        """
        results = []
        
        # Get capabilities to search
        if capability_type:
            search_capabilities = self.find_capabilities_by_type(capability_type)
        else:
            search_capabilities = []
            for type_capabilities in self._capabilities.values():
                search_capabilities.extend(type_capabilities.values())
        
        # Apply filters
        for capability in search_capabilities:
            # Text search
            if query.lower() not in capability.name.lower() and query.lower() not in capability.description.lower():
                continue
            
            # Tags filter
            if tags and not any(tag in capability.tags for tag in tags):
                continue
            
            # Reliability level filter
            if reliability_level and capability.reliability_level != reliability_level:
                continue
            
            results.append(capability)
        
        return results
    
    def get_capability_stats(self) -> Dict[str, Any]:
        """Get capability registry statistics.
        
        Returns:
            Dictionary of statistics
        """
        total_capabilities = sum(len(caps) for caps in self._capabilities.values())
        
        type_counts = {
            cap_type: len(caps) 
            for cap_type, caps in self._capabilities.items()
        }
        
        return {
            "total_capabilities": total_capabilities,
            "total_types": len(self._capabilities),
            "total_extensions": len(self._extension_capabilities),
            "type_distribution": type_counts,
            "average_capabilities_per_extension": (
                total_capabilities / len(self._extension_capabilities) 
                if self._extension_capabilities else 0
            )
        }


# Predefined common capabilities
COMMON_CAPABILITIES = {
    # Code Analysis
    "code_analysis": ExtensionCapability(
        name="code_analysis",
        type=CapabilityType.CODE_ANALYSIS,
        description="Analyze source code for structure, complexity, and issues",
        methods=[
            CapabilityMethod(
                name="analyze_file",
                description="Analyze a single source file",
                parameters=[
                    CapabilityParameter(name="file_path", type="string", description="Path to the file to analyze"),
                    CapabilityParameter(name="language", type="string", description="Programming language", required=False),
                ],
                return_description="Analysis results including metrics and issues"
            ),
            CapabilityMethod(
                name="analyze_directory",
                description="Analyze all files in a directory",
                parameters=[
                    CapabilityParameter(name="directory_path", type="string", description="Path to the directory"),
                    CapabilityParameter(name="recursive", type="boolean", description="Analyze subdirectories", default=True),
                ],
                return_description="Aggregated analysis results"
            )
        ]
    ),
    
    # Issue Management
    "issue_management": ExtensionCapability(
        name="issue_management",
        type=CapabilityType.ISSUE_TRACKING,
        description="Create, update, and manage issues",
        methods=[
            CapabilityMethod(
                name="create_issue",
                description="Create a new issue",
                parameters=[
                    CapabilityParameter(name="title", type="string", description="Issue title"),
                    CapabilityParameter(name="description", type="string", description="Issue description"),
                    CapabilityParameter(name="priority", type="string", description="Issue priority", required=False),
                ],
                return_description="Created issue object"
            ),
            CapabilityMethod(
                name="update_issue",
                description="Update an existing issue",
                parameters=[
                    CapabilityParameter(name="issue_id", type="string", description="Issue identifier"),
                    CapabilityParameter(name="updates", type="object", description="Fields to update"),
                ],
                return_description="Updated issue object"
            )
        ]
    ),
    
    # Messaging
    "messaging": ExtensionCapability(
        name="messaging",
        type=CapabilityType.MESSAGING,
        description="Send messages and notifications",
        methods=[
            CapabilityMethod(
                name="send_message",
                description="Send a message",
                parameters=[
                    CapabilityParameter(name="recipient", type="string", description="Message recipient"),
                    CapabilityParameter(name="content", type="string", description="Message content"),
                    CapabilityParameter(name="channel", type="string", description="Communication channel", required=False),
                ],
                return_description="Message delivery status"
            )
        ]
    ),
    
    # CI/CD
    "build_automation": ExtensionCapability(
        name="build_automation",
        type=CapabilityType.BUILD_AUTOMATION,
        description="Trigger and manage build processes",
        methods=[
            CapabilityMethod(
                name="trigger_build",
                description="Trigger a build",
                parameters=[
                    CapabilityParameter(name="project", type="string", description="Project identifier"),
                    CapabilityParameter(name="branch", type="string", description="Git branch", required=False),
                    CapabilityParameter(name="parameters", type="object", description="Build parameters", required=False),
                ],
                return_description="Build information and status"
            ),
            CapabilityMethod(
                name="get_build_status",
                description="Get build status",
                parameters=[
                    CapabilityParameter(name="build_id", type="string", description="Build identifier"),
                ],
                return_description="Current build status and details"
            )
        ]
    )
}

