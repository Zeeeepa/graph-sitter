"""
Main OpenEvolve Integration class for Graph-sitter

This module provides the primary interface for integrating OpenEvolve's evolutionary
capabilities with Graph-sitter's code analysis and manipulation framework.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from graph_sitter.core.interfaces import CodebaseInterface
from graph_sitter.shared.logging import get_logger

from .context_tracker import ContextTracker
from .continuous_learning import ContinuousLearningSystem
from .database_manager import OpenEvolveDatabase
from .performance_monitor import PerformanceMonitor
from .config import OpenEvolveConfig

logger = get_logger(__name__)


class OpenEvolveIntegration:
    """
    Main integration class that orchestrates OpenEvolve capabilities within Graph-sitter.
    
    This class provides:
    - Enhanced code evolution with continuous learning
    - Comprehensive step context tracking
    - Performance monitoring and analytics
    - Integration with existing graph_sitter functionality
    """
    
    def __init__(
        self,
        codebase: CodebaseInterface,
        config: Optional[OpenEvolveConfig] = None,
        database_path: Optional[str] = None
    ):
        """
        Initialize the OpenEvolve integration.
        
        Args:
            codebase: Graph-sitter codebase interface
            config: OpenEvolve configuration
            database_path: Path to the database for storing evolution data
        """
        self.codebase = codebase
        self.config = config or OpenEvolveConfig()
        
        # Initialize core components
        self.database = OpenEvolveDatabase(database_path or self.config.database_path)
        self.context_tracker = ContextTracker(self.database)
        self.learning_system = ContinuousLearningSystem(self.database, self.config)
        self.performance_monitor = PerformanceMonitor(self.database)
        
        # Evolution state
        self.current_session_id = None
        self.evolution_history = []
        
        logger.info("OpenEvolve integration initialized successfully")
    
    async def start_evolution_session(
        self,
        target_files: List[str],
        objectives: Dict[str, Any],
        max_iterations: int = 100
    ) -> str:
        """
        Start a new evolution session for the specified files.
        
        Args:
            target_files: List of file paths to evolve
            objectives: Evolution objectives and metrics
            max_iterations: Maximum number of evolution iterations
            
        Returns:
            Session ID for tracking the evolution
        """
        session_id = f"session_{int(time.time())}"
        self.current_session_id = session_id
        
        # Initialize session in database
        await self.database.create_session(
            session_id=session_id,
            target_files=target_files,
            objectives=objectives,
            max_iterations=max_iterations
        )
        
        # Start context tracking
        self.context_tracker.start_session(session_id)
        
        # Initialize performance monitoring
        self.performance_monitor.start_monitoring(session_id)
        
        logger.info(f"Started evolution session {session_id} for {len(target_files)} files")
        return session_id
    
    async def evolve_code(
        self,
        file_path: str,
        evolution_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evolve code in a specific file using OpenEvolve capabilities.
        
        Args:
            file_path: Path to the file to evolve
            evolution_prompt: Prompt describing the desired evolution
            context: Additional context for the evolution
            
        Returns:
            Evolution result with metrics and generated code
        """
        if not self.current_session_id:
            raise ValueError("No active evolution session. Call start_evolution_session first.")
        
        start_time = time.time()
        
        # Track the evolution step
        step_id = await self.context_tracker.start_step(
            session_id=self.current_session_id,
            step_type="code_evolution",
            file_path=file_path,
            prompt=evolution_prompt,
            context=context
        )
        
        try:
            # Get current code analysis from graph-sitter
            current_analysis = await self._analyze_current_code(file_path)
            
            # Apply continuous learning insights
            enhanced_context = await self.learning_system.enhance_context(
                file_path=file_path,
                current_analysis=current_analysis,
                evolution_prompt=evolution_prompt,
                historical_context=context
            )
            
            # Perform the evolution
            evolution_result = await self._perform_evolution(
                file_path=file_path,
                current_analysis=current_analysis,
                enhanced_context=enhanced_context,
                evolution_prompt=evolution_prompt
            )
            
            # Track performance metrics
            execution_time = time.time() - start_time
            await self.performance_monitor.record_evolution_metrics(
                session_id=self.current_session_id,
                step_id=step_id,
                execution_time=execution_time,
                result=evolution_result
            )
            
            # Complete the step tracking
            await self.context_tracker.complete_step(
                step_id=step_id,
                result=evolution_result,
                execution_time=execution_time
            )
            
            # Update learning system with results
            await self.learning_system.learn_from_result(
                step_id=step_id,
                evolution_result=evolution_result,
                context=enhanced_context
            )
            
            logger.info(f"Code evolution completed for {file_path} in {execution_time:.2f}s")
            return evolution_result
            
        except Exception as e:
            # Track the error
            await self.context_tracker.record_error(
                step_id=step_id,
                error=str(e),
                execution_time=time.time() - start_time
            )
            logger.error(f"Evolution failed for {file_path}: {str(e)}")
            raise
    
    async def get_evolution_insights(
        self,
        session_id: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get insights and analytics from evolution history.
        
        Args:
            session_id: Specific session to analyze (current session if None)
            file_path: Specific file to analyze (all files if None)
            
        Returns:
            Evolution insights and analytics
        """
        target_session = session_id or self.current_session_id
        if not target_session:
            raise ValueError("No session specified and no active session")
        
        # Get performance analytics
        performance_data = await self.performance_monitor.get_session_analytics(target_session)
        
        # Get learning insights
        learning_insights = await self.learning_system.get_insights(
            session_id=target_session,
            file_path=file_path
        )
        
        # Get context patterns
        context_patterns = await self.context_tracker.analyze_patterns(
            session_id=target_session,
            file_path=file_path
        )
        
        return {
            "session_id": target_session,
            "performance": performance_data,
            "learning_insights": learning_insights,
            "context_patterns": context_patterns,
            "timestamp": time.time()
        }
    
    async def optimize_evolution_strategy(self) -> Dict[str, Any]:
        """
        Use continuous learning to optimize the evolution strategy.
        
        Returns:
            Optimization results and updated strategy parameters
        """
        if not self.current_session_id:
            raise ValueError("No active evolution session")
        
        # Analyze historical performance
        optimization_result = await self.learning_system.optimize_strategy(
            session_id=self.current_session_id
        )
        
        # Update configuration based on learning
        if optimization_result.get("suggested_config"):
            self.config.update(optimization_result["suggested_config"])
        
        logger.info("Evolution strategy optimized based on continuous learning")
        return optimization_result
    
    async def end_evolution_session(self) -> Dict[str, Any]:
        """
        End the current evolution session and generate final report.
        
        Returns:
            Final session report with complete analytics
        """
        if not self.current_session_id:
            raise ValueError("No active evolution session")
        
        session_id = self.current_session_id
        
        # Generate final analytics
        final_report = await self.get_evolution_insights(session_id)
        
        # Stop monitoring and tracking
        self.performance_monitor.stop_monitoring(session_id)
        self.context_tracker.end_session(session_id)
        
        # Finalize session in database
        await self.database.finalize_session(session_id, final_report)
        
        # Clear current session
        self.current_session_id = None
        
        logger.info(f"Evolution session {session_id} completed successfully")
        return final_report
    
    async def _analyze_current_code(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze the current code using graph-sitter capabilities.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Code analysis results
        """
        # Use graph-sitter's analysis capabilities
        file_node = self.codebase.get_file(file_path)
        if not file_node:
            raise ValueError(f"File not found: {file_path}")
        
        # Perform comprehensive analysis
        analysis = {
            "file_path": file_path,
            "symbols": [symbol.to_dict() for symbol in file_node.symbols],
            "dependencies": [dep.to_dict() for dep in file_node.dependencies],
            "complexity_metrics": file_node.get_complexity_metrics(),
            "code_structure": file_node.get_structure_analysis(),
            "timestamp": time.time()
        }
        
        return analysis
    
    async def _perform_evolution(
        self,
        file_path: str,
        current_analysis: Dict[str, Any],
        enhanced_context: Dict[str, Any],
        evolution_prompt: str
    ) -> Dict[str, Any]:
        """
        Perform the actual code evolution using OpenEvolve capabilities.
        
        Args:
            file_path: Path to the file being evolved
            current_analysis: Current code analysis
            enhanced_context: Enhanced context from learning system
            evolution_prompt: Evolution prompt
            
        Returns:
            Evolution result
        """
        # This would integrate with the actual OpenEvolve evolution engine
        # For now, we'll create a placeholder that demonstrates the structure
        
        evolution_result = {
            "file_path": file_path,
            "original_code": current_analysis.get("code", ""),
            "evolved_code": "",  # Would be generated by OpenEvolve
            "evolution_metrics": {
                "complexity_improvement": 0.0,
                "performance_improvement": 0.0,
                "maintainability_score": 0.0
            },
            "applied_patterns": enhanced_context.get("suggested_patterns", []),
            "learning_insights_used": enhanced_context.get("insights", []),
            "timestamp": time.time()
        }
        
        # TODO: Integrate with actual OpenEvolve evolution engine
        logger.warning("Evolution engine integration not yet implemented - using placeholder")
        
        return evolution_result

