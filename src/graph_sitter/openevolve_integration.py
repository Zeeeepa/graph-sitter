"""
OpenEvolve Integration Module

This module provides integration with OpenEvolve components for step-by-step
effectiveness analysis and continuous system improvement.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# Import actual OpenEvolve components
try:
    from openevolve.evaluator import Evaluator
    from openevolve.database import Database as OpenEvolveDB
    from openevolve.controller import Controller
    OPENEVOLVE_AVAILABLE = True
except ImportError:
    OPENEVOLVE_AVAILABLE = False
    logging.warning("OpenEvolve components not available. Please install OpenEvolve package.")

logger = logging.getLogger(__name__)

class OpenEvolveIntegration:
    """
    Integration layer for OpenEvolve components
    
    This class provides a unified interface for interacting with OpenEvolve
    components for step-by-step effectiveness analysis and continuous improvement.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.evaluator = None
        self.database = None
        self.controller = None
        
        if OPENEVOLVE_AVAILABLE:
            self._initialize_openevolve_components()
        else:
            raise ImportError(
                "OpenEvolve components are not available. "
                "Please install the OpenEvolve package to use this integration."
            )
    
    def _initialize_openevolve_components(self):
        """Initialize actual OpenEvolve components"""
        try:
            # Initialize OpenEvolve components with configuration
            evaluator_config = self.config.get('evaluator', {})
            database_config = self.config.get('database', {})
            controller_config = self.config.get('controller', {})
            
            self.evaluator = Evaluator(**evaluator_config)
            self.database = OpenEvolveDB(**database_config)
            self.controller = Controller(
                evaluator=self.evaluator,
                database=self.database,
                **controller_config
            )
            
            logger.info("OpenEvolve integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenEvolve components: {e}")
            raise
    
    async def evaluate_task_completion(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate task completion effectiveness using OpenEvolve"""
        if not self.controller:
            raise RuntimeError("OpenEvolve controller not initialized")
        
        try:
            # Prepare evaluation data for OpenEvolve
            evaluation_request = {
                "task_id": task_data.get("task_id"),
                "implementation": task_data.get("implementation", ""),
                "requirements": task_data.get("requirements", []),
                "context": task_data.get("context", {}),
                "metrics": task_data.get("metrics", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Run evaluation through OpenEvolve
            evaluation_result = await self.controller.evaluate_implementation(evaluation_request)
            
            # Process and return results
            return {
                "evaluation_id": evaluation_result.get("evaluation_id"),
                "effectiveness_score": evaluation_result.get("effectiveness_score", 0.0),
                "quality_metrics": evaluation_result.get("quality_metrics", {}),
                "improvement_suggestions": evaluation_result.get("improvement_suggestions", []),
                "performance_analysis": evaluation_result.get("performance_analysis", {}),
                "evolution_recommendations": evaluation_result.get("evolution_recommendations", []),
                "evaluation_timestamp": evaluation_result.get("timestamp"),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"OpenEvolve evaluation failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "evaluation_timestamp": datetime.utcnow().isoformat()
            }
    
    async def analyze_system_performance(self) -> Dict[str, Any]:
        """Analyze overall system performance using OpenEvolve analytics"""
        if not self.database:
            raise RuntimeError("OpenEvolve database not initialized")
        
        try:
            # Get system-wide metrics from OpenEvolve database
            performance_data = await self.database.get_system_analytics()
            
            return {
                "total_evaluations": performance_data.get("total_evaluations", 0),
                "average_effectiveness": performance_data.get("average_effectiveness", 0.0),
                "quality_trends": performance_data.get("quality_trends", {}),
                "performance_metrics": performance_data.get("performance_metrics", {}),
                "improvement_areas": performance_data.get("improvement_areas", []),
                "evolution_progress": performance_data.get("evolution_progress", {}),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System performance analysis failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_improvement_recommendations(self, project_id: str) -> List[str]:
        """Get improvement recommendations for a project using OpenEvolve analysis"""
        if not self.controller:
            raise RuntimeError("OpenEvolve controller not initialized")
        
        try:
            # Get project-specific recommendations from OpenEvolve
            recommendations = await self.controller.get_project_recommendations(project_id)
            return recommendations.get("recommendations", [])
            
        except Exception as e:
            logger.error(f"Failed to get improvement recommendations: {e}")
            return []
    
    async def continuous_evaluation_loop(self, evaluation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run continuous evaluation on multiple data points using OpenEvolve"""
        if not self.controller:
            raise RuntimeError("OpenEvolve controller not initialized")
        
        try:
            # Process multiple evaluations through OpenEvolve
            batch_results = await self.controller.batch_evaluate(evaluation_data)
            
            # Aggregate and analyze results
            total_evaluations = len(batch_results)
            if total_evaluations == 0:
                return {"status": "no_data", "message": "No evaluation data provided"}
            
            effectiveness_scores = [
                result.get("effectiveness_score", 0.0) 
                for result in batch_results
            ]
            
            average_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores)
            
            # Get evolution insights from OpenEvolve
            evolution_analysis = await self.controller.analyze_evolution_progress(batch_results)
            
            return {
                "status": "completed",
                "total_evaluations": total_evaluations,
                "average_effectiveness": average_effectiveness,
                "effectiveness_distribution": {
                    "min": min(effectiveness_scores),
                    "max": max(effectiveness_scores),
                    "std_dev": self._calculate_std_dev(effectiveness_scores)
                },
                "evolution_insights": evolution_analysis,
                "evaluation_results": batch_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Continuous evaluation loop failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def evolve_implementation(self, 
                                  implementation: str, 
                                  requirements: List[str],
                                  evolution_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evolve an implementation using OpenEvolve's evolution engine"""
        if not self.controller:
            raise RuntimeError("OpenEvolve controller not initialized")
        
        try:
            evolution_request = {
                "implementation": implementation,
                "requirements": requirements,
                "config": evolution_config or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Run evolution process through OpenEvolve
            evolution_result = await self.controller.evolve_implementation(evolution_request)
            
            return {
                "evolved_implementation": evolution_result.get("evolved_implementation"),
                "evolution_steps": evolution_result.get("evolution_steps", []),
                "improvement_metrics": evolution_result.get("improvement_metrics", {}),
                "generation_count": evolution_result.get("generation_count", 0),
                "convergence_info": evolution_result.get("convergence_info", {}),
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Implementation evolution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    async def close(self):
        """Clean up OpenEvolve components"""
        try:
            if self.controller:
                await self.controller.close()
            if self.database:
                await self.database.close()
            if self.evaluator:
                await self.evaluator.close()
            logger.info("OpenEvolve integration closed successfully")
        except Exception as e:
            logger.error(f"Error closing OpenEvolve integration: {e}")

# Factory function for easy initialization
def create_openevolve_integration(config: Optional[Dict[str, Any]] = None) -> OpenEvolveIntegration:
    """Create and configure an OpenEvolve integration instance"""
    return OpenEvolveIntegration(config=config)

# Example usage
async def main():
    """Example usage of OpenEvolve integration"""
    config = {
        "evaluator": {
            "timeout_ms": 30000,
            "parallel_evaluations": 4
        },
        "database": {
            "connection_string": "postgresql://localhost/openevolve",
            "pool_size": 10
        },
        "controller": {
            "max_generations": 50,
            "population_size": 20
        }
    }
    
    integration = create_openevolve_integration(config)
    
    try:
        # Evaluate a task
        task_data = {
            "task_id": "task-123",
            "implementation": "def solve_problem(): return 42",
            "requirements": ["Function should return correct answer", "Should be efficient"],
            "context": {"language": "python", "complexity": "medium"}
        }
        
        evaluation_result = await integration.evaluate_task_completion(task_data)
        print(f"Evaluation result: {evaluation_result}")
        
        # Analyze system performance
        system_metrics = await integration.analyze_system_performance()
        print(f"System metrics: {system_metrics}")
        
        # Get improvement recommendations
        recommendations = await integration.get_improvement_recommendations("project-123")
        print(f"Recommendations: {recommendations}")
        
        # Evolve implementation
        evolution_result = await integration.evolve_implementation(
            implementation="def solve_problem(): return 42",
            requirements=["Function should return correct answer", "Should be efficient", "Should handle edge cases"]
        )
        print(f"Evolution result: {evolution_result}")
        
    finally:
        await integration.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

