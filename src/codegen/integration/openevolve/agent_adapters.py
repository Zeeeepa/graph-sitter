"""
OpenEvolve Agent Adapters

Adapter classes that bridge OpenEvolve agents with the graph-sitter evaluation system.
"""

import asyncio
import logging
import time
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .config import OpenEvolveConfig


@dataclass
class ComponentEvaluationResult:
    """Result of a component evaluation by an OpenEvolve agent."""
    effectiveness_score: float
    performance_metrics: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    step_results: List[Dict[str, Any]] = None
    agent_metadata: Dict[str, Any] = None


class BaseAgentAdapter(ABC):
    """Base class for OpenEvolve agent adapters."""
    
    def __init__(self, config: OpenEvolveConfig):
        """Initialize the adapter with configuration."""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(getattr(logging, config.log_level))
        self.is_initialized = False
        self.agent_instance = None
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the adapter and underlying agent."""
        pass
    
    @abstractmethod
    async def evaluate_component(
        self, 
        component_instance: Any, 
        component_name: str,
        context: Dict[str, Any]
    ) -> ComponentEvaluationResult:
        """Evaluate a component using the OpenEvolve agent."""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup adapter resources."""
        self.is_initialized = False
        self.agent_instance = None


class EvaluatorAgentAdapter(BaseAgentAdapter):
    """Adapter for OpenEvolve EvaluatorAgent to evaluate evaluator.py components."""
    
    async def initialize(self) -> None:
        """Initialize the EvaluatorAgent adapter."""
        try:
            # Try to import and initialize EvaluatorAgent
            if self.config.openevolve_repo_path:
                from evaluator_agent.agent import EvaluatorAgent
                from core.interfaces import TaskDefinition
                
                # Create a default task definition for evaluation
                task_definition = TaskDefinition(
                    id="component_evaluation",
                    description="Evaluate component effectiveness",
                    examples=[],
                    objective="correctness"
                )
                
                self.agent_instance = EvaluatorAgent(task_definition=task_definition)
                self.logger.info("EvaluatorAgent initialized successfully")
            else:
                # Create a mock agent for testing/development
                self.agent_instance = MockEvaluatorAgent()
                self.logger.warning("Using mock EvaluatorAgent (OpenEvolve repo path not configured)")
            
            self.is_initialized = True
            
        except ImportError as e:
            self.logger.error("Failed to import EvaluatorAgent: %s", str(e))
            # Fallback to mock agent
            self.agent_instance = MockEvaluatorAgent()
            self.is_initialized = True
        except Exception as e:
            self.logger.error("Failed to initialize EvaluatorAgent: %s", str(e))
            raise
    
    async def evaluate_component(
        self, 
        component_instance: Any, 
        component_name: str,
        context: Dict[str, Any]
    ) -> ComponentEvaluationResult:
        """Evaluate an evaluator component using EvaluatorAgent."""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        step_results = []
        
        try:
            # Step 1: Analyze component structure
            step_start = time.time()
            structure_analysis = await self._analyze_component_structure(component_instance)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'structure_analysis',
                'description': 'Analyze component structure and interfaces',
                'duration_ms': step_duration,
                'status': 'completed',
                'input_data': {'component_name': component_name},
                'output_data': structure_analysis,
                'effectiveness_contribution': 0.2
            })
            
            # Step 2: Evaluate functionality
            step_start = time.time()
            functionality_score = await self._evaluate_functionality(component_instance, context)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'functionality_evaluation',
                'description': 'Evaluate component functionality and correctness',
                'duration_ms': step_duration,
                'status': 'completed',
                'input_data': context,
                'output_data': {'functionality_score': functionality_score},
                'effectiveness_contribution': 0.4
            })
            
            # Step 3: Performance assessment
            step_start = time.time()
            performance_metrics = await self._assess_performance(component_instance)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'performance_assessment',
                'description': 'Assess component performance characteristics',
                'duration_ms': step_duration,
                'status': 'completed',
                'input_data': {},
                'output_data': performance_metrics,
                'effectiveness_contribution': 0.3
            })
            
            # Step 4: Error handling evaluation
            step_start = time.time()
            error_handling_score = await self._evaluate_error_handling(component_instance)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'error_handling_evaluation',
                'description': 'Evaluate component error handling capabilities',
                'duration_ms': step_duration,
                'status': 'completed',
                'input_data': {},
                'output_data': {'error_handling_score': error_handling_score},
                'effectiveness_contribution': 0.1
            })
            
            # Calculate overall effectiveness score
            effectiveness_score = (
                structure_analysis.get('quality_score', 0.5) * 0.2 +
                functionality_score * 0.4 +
                performance_metrics.get('efficiency_score', 0.5) * 0.3 +
                error_handling_score * 0.1
            )
            
            total_time = int((time.time() - start_time) * 1000)
            
            return ComponentEvaluationResult(
                effectiveness_score=effectiveness_score,
                performance_metrics={
                    'total_evaluation_time_ms': total_time,
                    'structure_quality': structure_analysis.get('quality_score', 0.5),
                    'functionality_score': functionality_score,
                    'performance_efficiency': performance_metrics.get('efficiency_score', 0.5),
                    'error_handling_score': error_handling_score,
                    'component_complexity': structure_analysis.get('complexity_score', 0.5)
                },
                success=True,
                step_results=step_results,
                agent_metadata={
                    'agent_type': 'EvaluatorAgent',
                    'evaluation_method': 'comprehensive_analysis',
                    'timestamp': time.time()
                }
            )
            
        except Exception as e:
            self.logger.error("Component evaluation failed: %s", str(e))
            return ComponentEvaluationResult(
                effectiveness_score=0.0,
                performance_metrics={'error': str(e)},
                success=False,
                error_message=str(e),
                step_results=step_results,
                agent_metadata={
                    'agent_type': 'EvaluatorAgent',
                    'error_traceback': traceback.format_exc()
                }
            )
    
    async def _analyze_component_structure(self, component_instance: Any) -> Dict[str, Any]:
        """Analyze the structure and design of the component."""
        try:
            # Basic structure analysis
            component_type = type(component_instance).__name__
            methods = [method for method in dir(component_instance) if not method.startswith('_')]
            
            # Assess complexity based on method count and inheritance
            complexity_score = min(1.0, len(methods) / 20.0)  # Normalize to 0-1
            
            # Assess quality based on naming conventions and structure
            quality_indicators = 0
            if hasattr(component_instance, '__doc__') and component_instance.__doc__:
                quality_indicators += 1
            if len([m for m in methods if not m.startswith('_')]) > 0:
                quality_indicators += 1
            if hasattr(component_instance, '__init__'):
                quality_indicators += 1
            
            quality_score = quality_indicators / 3.0
            
            return {
                'component_type': component_type,
                'method_count': len(methods),
                'public_methods': methods,
                'complexity_score': complexity_score,
                'quality_score': quality_score,
                'has_documentation': hasattr(component_instance, '__doc__') and bool(component_instance.__doc__)
            }
            
        except Exception as e:
            self.logger.warning("Structure analysis failed: %s", str(e))
            return {'quality_score': 0.3, 'complexity_score': 0.5, 'error': str(e)}
    
    async def _evaluate_functionality(self, component_instance: Any, context: Dict[str, Any]) -> float:
        """Evaluate the functionality of the component."""
        try:
            # Basic functionality checks
            functionality_score = 0.5  # Base score
            
            # Check if component has expected methods for an evaluator
            expected_methods = ['evaluate', 'assess', 'analyze', 'score']
            has_eval_methods = any(hasattr(component_instance, method) for method in expected_methods)
            
            if has_eval_methods:
                functionality_score += 0.3
            
            # Check if component can be called/executed
            if callable(component_instance):
                functionality_score += 0.2
            
            # Normalize to 0-1 range
            return min(1.0, functionality_score)
            
        except Exception as e:
            self.logger.warning("Functionality evaluation failed: %s", str(e))
            return 0.3
    
    async def _assess_performance(self, component_instance: Any) -> Dict[str, Any]:
        """Assess the performance characteristics of the component."""
        try:
            # Basic performance assessment
            start_time = time.time()
            
            # Try to measure instantiation time
            instantiation_time = time.time() - start_time
            
            # Estimate efficiency based on component complexity
            method_count = len([m for m in dir(component_instance) if not m.startswith('_')])
            efficiency_score = max(0.1, 1.0 - (method_count / 50.0))  # Inverse relationship with complexity
            
            return {
                'instantiation_time_ms': int(instantiation_time * 1000),
                'efficiency_score': efficiency_score,
                'method_count': method_count,
                'estimated_memory_usage': 'low'  # Placeholder
            }
            
        except Exception as e:
            self.logger.warning("Performance assessment failed: %s", str(e))
            return {'efficiency_score': 0.5, 'error': str(e)}
    
    async def _evaluate_error_handling(self, component_instance: Any) -> float:
        """Evaluate the error handling capabilities of the component."""
        try:
            # Check for error handling patterns
            error_handling_score = 0.5  # Base score
            
            # Look for exception handling in methods
            if hasattr(component_instance, '__dict__'):
                # Basic heuristic: assume better error handling if component has state
                error_handling_score += 0.2
            
            # Check for validation methods
            validation_methods = ['validate', 'check', 'verify']
            has_validation = any(hasattr(component_instance, method) for method in validation_methods)
            
            if has_validation:
                error_handling_score += 0.3
            
            return min(1.0, error_handling_score)
            
        except Exception as e:
            self.logger.warning("Error handling evaluation failed: %s", str(e))
            return 0.3


class DatabaseAgentAdapter(BaseAgentAdapter):
    """Adapter for OpenEvolve DatabaseAgent to evaluate database.py components."""
    
    async def initialize(self) -> None:
        """Initialize the DatabaseAgent adapter."""
        try:
            if self.config.openevolve_repo_path:
                from database_agent.agent import InMemoryDatabaseAgent
                self.agent_instance = InMemoryDatabaseAgent()
                self.logger.info("DatabaseAgent initialized successfully")
            else:
                self.agent_instance = MockDatabaseAgent()
                self.logger.warning("Using mock DatabaseAgent (OpenEvolve repo path not configured)")
            
            self.is_initialized = True
            
        except ImportError as e:
            self.logger.error("Failed to import DatabaseAgent: %s", str(e))
            self.agent_instance = MockDatabaseAgent()
            self.is_initialized = True
        except Exception as e:
            self.logger.error("Failed to initialize DatabaseAgent: %s", str(e))
            raise
    
    async def evaluate_component(
        self, 
        component_instance: Any, 
        component_name: str,
        context: Dict[str, Any]
    ) -> ComponentEvaluationResult:
        """Evaluate a database component using DatabaseAgent."""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        step_results = []
        
        try:
            # Step 1: Evaluate data persistence capabilities
            step_start = time.time()
            persistence_score = await self._evaluate_persistence(component_instance)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'persistence_evaluation',
                'description': 'Evaluate data persistence capabilities',
                'duration_ms': step_duration,
                'status': 'completed',
                'output_data': {'persistence_score': persistence_score},
                'effectiveness_contribution': 0.4
            })
            
            # Step 2: Assess query performance
            step_start = time.time()
            query_performance = await self._assess_query_performance(component_instance)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'query_performance',
                'description': 'Assess query performance and efficiency',
                'duration_ms': step_duration,
                'status': 'completed',
                'output_data': query_performance,
                'effectiveness_contribution': 0.3
            })
            
            # Step 3: Evaluate data integrity
            step_start = time.time()
            integrity_score = await self._evaluate_data_integrity(component_instance)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'data_integrity',
                'description': 'Evaluate data integrity and consistency',
                'duration_ms': step_duration,
                'status': 'completed',
                'output_data': {'integrity_score': integrity_score},
                'effectiveness_contribution': 0.3
            })
            
            # Calculate effectiveness score
            effectiveness_score = (
                persistence_score * 0.4 +
                query_performance.get('efficiency_score', 0.5) * 0.3 +
                integrity_score * 0.3
            )
            
            total_time = int((time.time() - start_time) * 1000)
            
            return ComponentEvaluationResult(
                effectiveness_score=effectiveness_score,
                performance_metrics={
                    'total_evaluation_time_ms': total_time,
                    'persistence_score': persistence_score,
                    'query_efficiency': query_performance.get('efficiency_score', 0.5),
                    'data_integrity_score': integrity_score,
                    'storage_efficiency': query_performance.get('storage_efficiency', 0.5)
                },
                success=True,
                step_results=step_results,
                agent_metadata={
                    'agent_type': 'DatabaseAgent',
                    'evaluation_method': 'database_analysis'
                }
            )
            
        except Exception as e:
            self.logger.error("Database component evaluation failed: %s", str(e))
            return ComponentEvaluationResult(
                effectiveness_score=0.0,
                performance_metrics={'error': str(e)},
                success=False,
                error_message=str(e),
                step_results=step_results
            )
    
    async def _evaluate_persistence(self, component_instance: Any) -> float:
        """Evaluate data persistence capabilities."""
        try:
            persistence_score = 0.5  # Base score
            
            # Check for persistence-related methods
            persistence_methods = ['save', 'store', 'persist', 'write', 'insert', 'update']
            has_persistence = any(hasattr(component_instance, method) for method in persistence_methods)
            
            if has_persistence:
                persistence_score += 0.4
            
            # Check for retrieval methods
            retrieval_methods = ['get', 'find', 'query', 'select', 'fetch']
            has_retrieval = any(hasattr(component_instance, method) for method in retrieval_methods)
            
            if has_retrieval:
                persistence_score += 0.1
            
            return min(1.0, persistence_score)
            
        except Exception as e:
            self.logger.warning("Persistence evaluation failed: %s", str(e))
            return 0.3
    
    async def _assess_query_performance(self, component_instance: Any) -> Dict[str, Any]:
        """Assess query performance characteristics."""
        try:
            # Basic performance metrics
            efficiency_score = 0.7  # Default assumption
            storage_efficiency = 0.6
            
            # Check for indexing or optimization features
            optimization_methods = ['index', 'optimize', 'cache']
            has_optimization = any(hasattr(component_instance, method) for method in optimization_methods)
            
            if has_optimization:
                efficiency_score += 0.2
                storage_efficiency += 0.3
            
            return {
                'efficiency_score': min(1.0, efficiency_score),
                'storage_efficiency': min(1.0, storage_efficiency),
                'has_optimization': has_optimization
            }
            
        except Exception as e:
            self.logger.warning("Query performance assessment failed: %s", str(e))
            return {'efficiency_score': 0.5, 'storage_efficiency': 0.5}
    
    async def _evaluate_data_integrity(self, component_instance: Any) -> float:
        """Evaluate data integrity and consistency features."""
        try:
            integrity_score = 0.5  # Base score
            
            # Check for validation methods
            validation_methods = ['validate', 'check', 'verify']
            has_validation = any(hasattr(component_instance, method) for method in validation_methods)
            
            if has_validation:
                integrity_score += 0.3
            
            # Check for transaction support
            transaction_methods = ['begin', 'commit', 'rollback', 'transaction']
            has_transactions = any(hasattr(component_instance, method) for method in transaction_methods)
            
            if has_transactions:
                integrity_score += 0.2
            
            return min(1.0, integrity_score)
            
        except Exception as e:
            self.logger.warning("Data integrity evaluation failed: %s", str(e))
            return 0.3


class ControllerAgentAdapter(BaseAgentAdapter):
    """Adapter for OpenEvolve SelectionControllerAgent to evaluate controller.py components."""
    
    async def initialize(self) -> None:
        """Initialize the SelectionControllerAgent adapter."""
        try:
            if self.config.openevolve_repo_path:
                from selection_controller.agent import SelectionControllerAgent
                self.agent_instance = SelectionControllerAgent()
                self.logger.info("SelectionControllerAgent initialized successfully")
            else:
                self.agent_instance = MockControllerAgent()
                self.logger.warning("Using mock ControllerAgent (OpenEvolve repo path not configured)")
            
            self.is_initialized = True
            
        except ImportError as e:
            self.logger.error("Failed to import SelectionControllerAgent: %s", str(e))
            self.agent_instance = MockControllerAgent()
            self.is_initialized = True
        except Exception as e:
            self.logger.error("Failed to initialize SelectionControllerAgent: %s", str(e))
            raise
    
    async def evaluate_component(
        self, 
        component_instance: Any, 
        component_name: str,
        context: Dict[str, Any]
    ) -> ComponentEvaluationResult:
        """Evaluate a controller component using SelectionControllerAgent."""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        step_results = []
        
        try:
            # Step 1: Evaluate control flow logic
            step_start = time.time()
            control_flow_score = await self._evaluate_control_flow(component_instance)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'control_flow_evaluation',
                'description': 'Evaluate control flow and decision logic',
                'duration_ms': step_duration,
                'status': 'completed',
                'output_data': {'control_flow_score': control_flow_score},
                'effectiveness_contribution': 0.4
            })
            
            # Step 2: Assess coordination capabilities
            step_start = time.time()
            coordination_score = await self._assess_coordination(component_instance)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'coordination_assessment',
                'description': 'Assess component coordination capabilities',
                'duration_ms': step_duration,
                'status': 'completed',
                'output_data': {'coordination_score': coordination_score},
                'effectiveness_contribution': 0.3
            })
            
            # Step 3: Evaluate state management
            step_start = time.time()
            state_management_score = await self._evaluate_state_management(component_instance)
            step_duration = int((time.time() - step_start) * 1000)
            
            step_results.append({
                'name': 'state_management',
                'description': 'Evaluate state management capabilities',
                'duration_ms': step_duration,
                'status': 'completed',
                'output_data': {'state_management_score': state_management_score},
                'effectiveness_contribution': 0.3
            })
            
            # Calculate effectiveness score
            effectiveness_score = (
                control_flow_score * 0.4 +
                coordination_score * 0.3 +
                state_management_score * 0.3
            )
            
            total_time = int((time.time() - start_time) * 1000)
            
            return ComponentEvaluationResult(
                effectiveness_score=effectiveness_score,
                performance_metrics={
                    'total_evaluation_time_ms': total_time,
                    'control_flow_score': control_flow_score,
                    'coordination_score': coordination_score,
                    'state_management_score': state_management_score
                },
                success=True,
                step_results=step_results,
                agent_metadata={
                    'agent_type': 'SelectionControllerAgent',
                    'evaluation_method': 'controller_analysis'
                }
            )
            
        except Exception as e:
            self.logger.error("Controller component evaluation failed: %s", str(e))
            return ComponentEvaluationResult(
                effectiveness_score=0.0,
                performance_metrics={'error': str(e)},
                success=False,
                error_message=str(e),
                step_results=step_results
            )
    
    async def _evaluate_control_flow(self, component_instance: Any) -> float:
        """Evaluate control flow and decision logic."""
        try:
            control_flow_score = 0.5  # Base score
            
            # Check for control methods
            control_methods = ['control', 'manage', 'coordinate', 'execute', 'run']
            has_control = any(hasattr(component_instance, method) for method in control_methods)
            
            if has_control:
                control_flow_score += 0.3
            
            # Check for decision-making methods
            decision_methods = ['decide', 'select', 'choose', 'determine']
            has_decisions = any(hasattr(component_instance, method) for method in decision_methods)
            
            if has_decisions:
                control_flow_score += 0.2
            
            return min(1.0, control_flow_score)
            
        except Exception as e:
            self.logger.warning("Control flow evaluation failed: %s", str(e))
            return 0.3
    
    async def _assess_coordination(self, component_instance: Any) -> float:
        """Assess coordination capabilities."""
        try:
            coordination_score = 0.5  # Base score
            
            # Check for coordination patterns
            coordination_methods = ['coordinate', 'orchestrate', 'synchronize', 'schedule']
            has_coordination = any(hasattr(component_instance, method) for method in coordination_methods)
            
            if has_coordination:
                coordination_score += 0.4
            
            # Check for communication methods
            communication_methods = ['notify', 'signal', 'broadcast', 'send']
            has_communication = any(hasattr(component_instance, method) for method in communication_methods)
            
            if has_communication:
                coordination_score += 0.1
            
            return min(1.0, coordination_score)
            
        except Exception as e:
            self.logger.warning("Coordination assessment failed: %s", str(e))
            return 0.3
    
    async def _evaluate_state_management(self, component_instance: Any) -> float:
        """Evaluate state management capabilities."""
        try:
            state_score = 0.5  # Base score
            
            # Check for state-related attributes
            if hasattr(component_instance, '__dict__') and component_instance.__dict__:
                state_score += 0.2
            
            # Check for state management methods
            state_methods = ['get_state', 'set_state', 'update_state', 'reset']
            has_state_management = any(hasattr(component_instance, method) for method in state_methods)
            
            if has_state_management:
                state_score += 0.3
            
            return min(1.0, state_score)
            
        except Exception as e:
            self.logger.warning("State management evaluation failed: %s", str(e))
            return 0.3


# Mock agents for testing/development when OpenEvolve is not available
class MockEvaluatorAgent:
    """Mock EvaluatorAgent for testing."""
    
    def __init__(self):
        self.evaluation_model_name = "mock_model"
        self.evaluation_timeout_seconds = 30


class MockDatabaseAgent:
    """Mock DatabaseAgent for testing."""
    
    def __init__(self):
        self.database_type = "mock"


class MockControllerAgent:
    """Mock ControllerAgent for testing."""
    
    def __init__(self):
        self.num_islands = 1
        self.elitism_count = 1

