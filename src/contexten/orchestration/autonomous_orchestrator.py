"""
Autonomous Orchestrator - Main orchestration engine for autonomous CI/CD operations.

This module provides the core orchestration logic that integrates:
- Prefect for workflow management
- Codegen SDK for AI-powered operations
- Linear for task management
- GitHub for code management
- graph-sitter for code analysis
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import asyncio
import logging
import os

from codegen import Agent as CodegenAgent
from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret

from ..agents.chat_agent import ChatAgent
from ..agents.code_agent import CodeAgent
from .config import OrchestrationConfig
from .monitoring import SystemMonitor
from .workflow_types import AutonomousWorkflowType


class OperationStatus(Enum):
    """Status of autonomous operations"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationResult:
    """Result of an autonomous operation"""
    operation_id: str
    operation_type: AutonomousWorkflowType
    status: OperationStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class AutonomousOrchestrator:
    """
    Main orchestrator for autonomous CI/CD operations.
    
    This class coordinates all autonomous operations across the system,
    integrating Prefect workflows with Codegen SDK, Linear, GitHub, and graph-sitter.
    """
    
    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.monitor = SystemMonitor(config)
        self.codegen_agent: Optional[CodegenAgent] = None
        self.active_operations: Dict[str, OperationResult] = {}
        
    async def initialize(self) -> None:
        """Initialize the orchestrator and all its components"""
        self.logger.info("Initializing Autonomous Orchestrator...")
        
        # Initialize Codegen SDK agent
        await self._initialize_codegen_agent()
        
        # Initialize monitoring
        await self.monitor.initialize()
        
        # Validate configuration
        await self._validate_configuration()
        
        self.logger.info("Autonomous Orchestrator initialized successfully")
    
    async def _initialize_codegen_agent(self) -> None:
        """Initialize the Codegen SDK agent"""
        try:
            org_id = self.config.codegen_org_id or os.getenv("CODEGEN_ORG_ID")
            token = self.config.codegen_token or os.getenv("CODEGEN_TOKEN")
            
            if not org_id or not token:
                raise ValueError("Codegen SDK credentials not found")
            
            self.codegen_agent = CodegenAgent(org_id=org_id, token=token)
            self.logger.info("Codegen SDK agent initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Codegen SDK agent: {e}")
            raise
    
    async def _validate_configuration(self) -> None:
        """Validate the orchestrator configuration"""
        required_configs = [
            ("codegen_org_id", self.config.codegen_org_id),
            ("codegen_token", self.config.codegen_token),
        ]
        
        missing_configs = [name for name, value in required_configs if not value]
        
        if missing_configs:
            raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")
    
    async def trigger_autonomous_operation(
        self,
        operation_type: AutonomousWorkflowType,
        context: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ) -> str:
        """
        Trigger an autonomous operation.
        
        Args:
            operation_type: Type of operation to trigger
            context: Additional context for the operation
            priority: Operation priority (1-10, higher is more urgent)
            
        Returns:
            Operation ID for tracking
        """
        operation_id = f"{operation_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        operation_result = OperationResult(
            operation_id=operation_id,
            operation_type=operation_type,
            status=OperationStatus.PENDING,
            started_at=datetime.now(),
            metadata={"priority": priority, "context": context or {}}
        )
        
        self.active_operations[operation_id] = operation_result
        
        # Execute operation asynchronously
        asyncio.create_task(self._execute_operation(operation_result))
        
        self.logger.info(f"Triggered autonomous operation: {operation_id}")
        return operation_id
    
    async def _execute_operation(self, operation: OperationResult) -> None:
        """Execute an autonomous operation"""
        try:
            operation.status = OperationStatus.RUNNING
            self.logger.info(f"Executing operation: {operation.operation_id}")
            
            # Generate operation prompt based on type
            prompt = self._generate_operation_prompt(operation)
            
            # Execute via Codegen SDK
            task = self.codegen_agent.run(prompt=prompt)
            
            # Wait for completion with timeout
            result = await self._wait_for_codegen_task(task, timeout_minutes=30)
            
            operation.result = result
            operation.status = OperationStatus.COMPLETED
            operation.completed_at = datetime.now()
            
            self.logger.info(f"Operation completed: {operation.operation_id}")
            
        except Exception as e:
            operation.status = OperationStatus.FAILED
            operation.error = str(e)
            operation.completed_at = datetime.now()
            
            self.logger.error(f"Operation failed: {operation.operation_id} - {e}")
            
            # Trigger recovery if enabled
            if self.config.auto_recovery_enabled:
                await self._trigger_recovery(operation)
    
    def _generate_operation_prompt(self, operation: OperationResult) -> str:
        """Generate a prompt for the Codegen SDK based on operation type"""
        context = operation.metadata.get("context", {})
        
        prompts = {
            AutonomousWorkflowType.COMPONENT_ANALYSIS: self._generate_component_analysis_prompt(context),
            AutonomousWorkflowType.FAILURE_ANALYSIS: self._generate_failure_analysis_prompt(context),
            AutonomousWorkflowType.PERFORMANCE_MONITORING: self._generate_performance_monitoring_prompt(context),
            AutonomousWorkflowType.DEPENDENCY_MANAGEMENT: self._generate_dependency_management_prompt(context),
            AutonomousWorkflowType.SECURITY_AUDIT: self._generate_security_audit_prompt(context),
            AutonomousWorkflowType.TEST_OPTIMIZATION: self._generate_test_optimization_prompt(context),
            AutonomousWorkflowType.CODE_QUALITY_CHECK: self._generate_code_quality_prompt(context),
            AutonomousWorkflowType.LINEAR_SYNC: self._generate_linear_sync_prompt(context),
            AutonomousWorkflowType.GITHUB_AUTOMATION: self._generate_github_automation_prompt(context),
            AutonomousWorkflowType.HEALTH_CHECK: self._generate_health_check_prompt(context),
        }
        
        return prompts.get(operation.operation_type, f"Execute {operation.operation_type.value} operation")
    
    def _generate_component_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for component analysis"""
        component = context.get("component", "unknown")
        linear_issue_id = context.get("linear_issue_id", "")
        
        return f"""
        Perform comprehensive component analysis for: {component}
        
        Tasks:
        1. Analyze code quality and identify unused code
        2. Check for parameter issues and type safety
        3. Evaluate performance and optimization opportunities
        4. Review integration points and dependencies
        5. Generate improvement recommendations
        
        {f"Update Linear issue {linear_issue_id} with findings." if linear_issue_id else ""}
        
        Use graph-sitter for deep code analysis and provide actionable insights.
        """
    
    def _generate_failure_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for failure analysis"""
        workflow_run_id = context.get("workflow_run_id", "")
        failure_type = context.get("failure_type", "unknown")
        
        return f"""
        Analyze and fix CI/CD failure:
        
        Workflow Run ID: {workflow_run_id}
        Failure Type: {failure_type}
        
        Tasks:
        1. Analyze failure logs and identify root cause
        2. Determine if this is a known issue pattern
        3. Generate and implement fix if possible
        4. Create PR with fix and comprehensive testing
        5. Update monitoring to prevent similar failures
        
        Use autonomous error healing and self-recovery mechanisms.
        """
    
    def _generate_performance_monitoring_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for performance monitoring"""
        return """
        Perform comprehensive performance monitoring and optimization:
        
        Tasks:
        1. Analyze current system performance metrics
        2. Identify performance bottlenecks and regressions
        3. Review resource usage patterns
        4. Generate optimization recommendations
        5. Implement performance improvements where safe
        6. Update monitoring thresholds and alerts
        
        Focus on CI/CD pipeline performance and system responsiveness.
        """
    
    def _generate_dependency_management_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for dependency management"""
        return """
        Perform autonomous dependency management:
        
        Tasks:
        1. Scan for outdated dependencies and security vulnerabilities
        2. Analyze compatibility and breaking changes
        3. Create dependency update plan with risk assessment
        4. Implement safe dependency updates with comprehensive testing
        5. Update documentation and migration guides
        6. Monitor for post-update issues
        
        Prioritize security updates while maintaining system stability.
        """
    
    def _generate_security_audit_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for security audit"""
        return """
        Perform comprehensive security audit:
        
        Tasks:
        1. Scan codebase for security vulnerabilities
        2. Review authentication and authorization patterns
        3. Analyze data handling and privacy compliance
        4. Check for exposed secrets and credentials
        5. Validate security configurations
        6. Generate security improvement recommendations
        7. Implement critical security fixes
        
        Focus on autonomous security monitoring and remediation.
        """
    
    def _generate_test_optimization_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for test optimization"""
        return """
        Optimize testing suite and coverage:
        
        Tasks:
        1. Analyze test coverage and identify gaps
        2. Detect flaky and unreliable tests
        3. Optimize test execution time and parallelization
        4. Review test quality and maintainability
        5. Generate new tests for uncovered code paths
        6. Implement test infrastructure improvements
        
        Focus on autonomous test generation and optimization.
        """
    
    def _generate_code_quality_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for code quality check"""
        return """
        Perform comprehensive code quality analysis:
        
        Tasks:
        1. Analyze code complexity and maintainability
        2. Identify code smells and anti-patterns
        3. Review coding standards compliance
        4. Detect duplicate and dead code
        5. Analyze documentation quality
        6. Generate refactoring recommendations
        7. Implement safe code quality improvements
        
        Use graph-sitter for deep structural analysis.
        """
    
    def _generate_linear_sync_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for Linear synchronization"""
        return """
        Synchronize with Linear for task management:
        
        Tasks:
        1. Monitor Linear issues for component analysis requests
        2. Create sub-issues for granular component analysis
        3. Update issue status based on operation progress
        4. Generate progress reports and summaries
        5. Handle issue assignments and notifications
        6. Maintain Linear-GitHub synchronization
        
        Ensure autonomous task distribution and tracking.
        """
    
    def _generate_github_automation_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for GitHub automation"""
        return """
        Perform GitHub automation tasks:
        
        Tasks:
        1. Monitor PR events and status changes
        2. Automate PR reviews and feedback
        3. Manage branch creation and cleanup
        4. Handle deployment validation
        5. Automate merging of approved PRs
        6. Generate release notes and changelogs
        
        Focus on autonomous PR lifecycle management.
        """
    
    def _generate_health_check_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for health check"""
        return """
        Perform comprehensive system health check:
        
        Tasks:
        1. Check all system components and integrations
        2. Validate API connectivity and performance
        3. Monitor resource usage and capacity
        4. Verify backup and recovery systems
        5. Test alert and notification systems
        6. Generate health status report
        
        Ensure system reliability and autonomous operation capability.
        """
    
    async def _wait_for_codegen_task(self, task, timeout_minutes: int = 30) -> Dict[str, Any]:
        """Wait for Codegen SDK task completion with timeout"""
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.now() - start_time < timeout:
            task.refresh()
            
            if task.status == "completed":
                return {"status": "success", "result": task.result}
            elif task.status == "failed":
                return {"status": "failed", "error": task.error}
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        return {"status": "timeout", "error": "Task timed out"}
    
    async def _trigger_recovery(self, failed_operation: OperationResult) -> None:
        """Trigger recovery operation for failed operation"""
        recovery_context = {
            "failed_operation_id": failed_operation.operation_id,
            "failure_reason": failed_operation.error,
            "operation_type": failed_operation.operation_type.value
        }
        
        await self.trigger_autonomous_operation(
            AutonomousWorkflowType.FAILURE_ANALYSIS,
            context=recovery_context,
            priority=8  # High priority for recovery
        )
    
    async def get_operation_status(self, operation_id: str) -> Optional[OperationResult]:
        """Get the status of an operation"""
        return self.active_operations.get(operation_id)
    
    async def list_active_operations(self) -> List[OperationResult]:
        """List all active operations"""
        return [op for op in self.active_operations.values() 
                if op.status in [OperationStatus.PENDING, OperationStatus.RUNNING]]
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an operation"""
        operation = self.active_operations.get(operation_id)
        if operation and operation.status in [OperationStatus.PENDING, OperationStatus.RUNNING]:
            operation.status = OperationStatus.CANCELLED
            operation.completed_at = datetime.now()
            return True
        return False
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        return await self.monitor.get_comprehensive_metrics()
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator gracefully"""
        self.logger.info("Shutting down Autonomous Orchestrator...")
        
        # Cancel all pending operations
        for operation in self.active_operations.values():
            if operation.status in [OperationStatus.PENDING, OperationStatus.RUNNING]:
                operation.status = OperationStatus.CANCELLED
                operation.completed_at = datetime.now()
        
        # Shutdown monitoring
        await self.monitor.shutdown()
        
        self.logger.info("Autonomous Orchestrator shutdown complete")

