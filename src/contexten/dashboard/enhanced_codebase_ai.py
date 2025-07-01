"""
Enhanced Codebase AI Integration

This module provides advanced AI-powered codebase analysis and manipulation
capabilities, integrating with the Contexten Orchestrator and enhanced autogenlib
for context-aware code generation and analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

from graph_sitter import Codebase
from graph_sitter.codebase.codebase_ai import codebase_ai
from ..extensions.contexten_app import ContextenOrchestrator, ContextenConfig
from ..autogenlib import AutogenClient, GenerationRequest
from ...shared.logging.get_logger import get_logger

logger = get_logger(__name__)

class AITaskType(Enum):
    """Types of AI-powered tasks"""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    TESTING = "testing"
    SECURITY_REVIEW = "security_review"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ARCHITECTURE_REVIEW = "architecture_review"

@dataclass
class AIAnalysisRequest:
    """Request for AI-powered analysis"""
    task_type: AITaskType
    target: Union[str, Any]  # File path, function, class, or code snippet
    context: Dict[str, Any]
    instructions: str
    model_config: Dict[str, Any] = None

@dataclass
class AIAnalysisResult:
    """Result of AI-powered analysis"""
    task_type: AITaskType
    target: str
    analysis: str
    suggestions: List[str]
    code_changes: Optional[str] = None
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = None
    generation_time: float = 0.0

class EnhancedCodebaseAI:
    """Enhanced AI-powered codebase analysis and manipulation"""
    
    def __init__(self, orchestrator: ContextenOrchestrator, autogen_client: AutogenClient):
        self.orchestrator = orchestrator
        self.autogen_client = autogen_client
        self.codebase = orchestrator.codebase
        
        # AI configuration
        self.ai_config = {
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-latest",
            "temperature": 0.1,
            "max_tokens": 4000
        }
        
        # Analysis cache
        self.analysis_cache: Dict[str, AIAnalysisResult] = {}
        self.context_cache: Dict[str, Dict[str, Any]] = {}
    
    async def analyze_with_ai(self, request: AIAnalysisRequest) -> AIAnalysisResult:
        """Perform AI-powered analysis with enhanced context"""
        
        start_time = datetime.now()
        
        try:
            # Gather enhanced context
            context = await self._gather_enhanced_context(request.target, request.context)
            
            # Route to appropriate analysis method
            if request.task_type == AITaskType.CODE_ANALYSIS:
                result = await self._analyze_code_quality(request, context)
            elif request.task_type == AITaskType.CODE_GENERATION:
                result = await self._generate_code(request, context)
            elif request.task_type == AITaskType.DOCUMENTATION:
                result = await self._generate_documentation(request, context)
            elif request.task_type == AITaskType.REFACTORING:
                result = await self._suggest_refactoring(request, context)
            elif request.task_type == AITaskType.TESTING:
                result = await self._generate_tests(request, context)
            elif request.task_type == AITaskType.SECURITY_REVIEW:
                result = await self._security_review(request, context)
            elif request.task_type == AITaskType.PERFORMANCE_OPTIMIZATION:
                result = await self._optimize_performance(request, context)
            elif request.task_type == AITaskType.ARCHITECTURE_REVIEW:
                result = await self._review_architecture(request, context)
            else:
                raise ValueError(f"Unknown task type: {request.task_type}")
            
            # Calculate generation time
            result.generation_time = (datetime.now() - start_time).total_seconds()
            
            # Cache result
            cache_key = f"{request.task_type.value}_{hash(str(request.target))}"
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return AIAnalysisResult(
                task_type=request.task_type,
                target=str(request.target),
                analysis=f"Analysis failed: {str(e)}",
                suggestions=[],
                confidence_score=0.0,
                generation_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _gather_enhanced_context(self, target: Union[str, Any], base_context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather enhanced context using graph-sitter analysis"""
        
        context = base_context.copy()
        
        try:
            if self.codebase:
                # Add codebase summary
                context["codebase_summary"] = {
                    "total_files": len(self.codebase.files),
                    "total_functions": len(self.codebase.functions),
                    "total_classes": len(self.codebase.classes),
                    "languages": list(set(f.language for f in self.codebase.files if hasattr(f, 'language')))
                }
                
                # If target is a specific symbol, gather related context
                if isinstance(target, str) and hasattr(self.codebase, 'get_symbol'):
                    try:
                        symbol = self.codebase.get_symbol(target)
                        if symbol:
                            context["symbol_context"] = {
                                "type": type(symbol).__name__,
                                "file": symbol.file.filepath if hasattr(symbol, 'file') else None,
                                "dependencies": [dep.name for dep in getattr(symbol, 'dependencies', [])],
                                "usages": [usage.file.filepath for usage in getattr(symbol, 'usages', [])],
                                "call_sites": [cs.file.filepath for cs in getattr(symbol, 'call_sites', [])]
                            }
                    except Exception as e:
                        logger.debug(f"Could not get symbol context for {target}: {e}")
                
                # Add related files context
                if isinstance(target, str) and target.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                    try:
                        file = self.codebase.get_file(target)
                        if file:
                            context["file_context"] = {
                                "imports": [imp.module for imp in getattr(file, 'imports', [])],
                                "functions": [func.name for func in getattr(file, 'functions', [])],
                                "classes": [cls.name for cls in getattr(file, 'classes', [])],
                                "size_lines": len(file.source.split('\n')) if hasattr(file, 'source') else 0
                            }
                    except Exception as e:
                        logger.debug(f"Could not get file context for {target}: {e}")
            
            # Add orchestrator metrics for system context
            system_metrics = await self.orchestrator.get_system_metrics()
            context["system_context"] = {
                "health_status": system_metrics.get("health_status", {}),
                "active_tasks": system_metrics.get("active_tasks", 0),
                "extensions_status": system_metrics.get("extensions", {})
            }
            
        except Exception as e:
            logger.error(f"Error gathering enhanced context: {e}")
        
        return context
    
    async def _analyze_code_quality(self, request: AIAnalysisRequest, context: Dict[str, Any]) -> AIAnalysisResult:
        """Analyze code quality using AI"""
        
        prompt = f"""
        Analyze the following code for quality, maintainability, and best practices:
        
        Target: {request.target}
        Instructions: {request.instructions}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Please provide:
        1. Overall quality assessment
        2. Specific issues found
        3. Suggestions for improvement
        4. Code complexity analysis
        5. Maintainability score (1-10)
        """
        
        try:
            # Use codebase_ai for analysis
            analysis = await codebase_ai(prompt, target=request.target, context=context)
            
            return AIAnalysisResult(
                task_type=request.task_type,
                target=str(request.target),
                analysis=analysis,
                suggestions=self._extract_suggestions(analysis),
                confidence_score=0.85,
                metadata={"analysis_type": "quality", "context_size": len(str(context))}
            )
            
        except Exception as e:
            logger.error(f"Code quality analysis failed: {e}")
            raise
    
    async def _generate_code(self, request: AIAnalysisRequest, context: Dict[str, Any]) -> AIAnalysisResult:
        """Generate code using enhanced autogenlib"""
        
        try:
            # Create generation request for autogenlib
            gen_request = GenerationRequest(
                module_path=context.get("module_path", ""),
                function_name=context.get("function_name", ""),
                description=request.instructions,
                context=context,
                model_config=request.model_config or self.ai_config
            )
            
            # Generate code using autogenlib
            result = await self.autogen_client.generate_code(gen_request)
            
            return AIAnalysisResult(
                task_type=request.task_type,
                target=str(request.target),
                analysis=f"Generated code for: {request.instructions}",
                suggestions=[
                    "Review generated code for correctness",
                    "Add appropriate tests",
                    "Ensure proper error handling",
                    "Validate against requirements"
                ],
                code_changes=result.code,
                confidence_score=result.confidence_score,
                metadata={
                    "generation_metadata": result.metadata,
                    "cache_hit": result.cache_hit,
                    "model_used": result.model_used
                }
            )
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise
    
    async def _generate_documentation(self, request: AIAnalysisRequest, context: Dict[str, Any]) -> AIAnalysisResult:
        """Generate documentation using AI"""
        
        prompt = f"""
        Generate comprehensive documentation for the following code:
        
        Target: {request.target}
        Instructions: {request.instructions}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Please provide:
        1. Clear description of functionality
        2. Parameter documentation
        3. Return value documentation
        4. Usage examples
        5. Any important notes or warnings
        
        Format the documentation appropriately for the target language.
        """
        
        try:
            documentation = await codebase_ai(prompt, target=request.target, context=context)
            
            return AIAnalysisResult(
                task_type=request.task_type,
                target=str(request.target),
                analysis="Generated comprehensive documentation",
                suggestions=[
                    "Review documentation for accuracy",
                    "Add examples if needed",
                    "Ensure consistent formatting",
                    "Update as code changes"
                ],
                code_changes=documentation,
                confidence_score=0.90,
                metadata={"doc_type": "comprehensive", "target_type": type(request.target).__name__}
            )
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            raise
    
    async def _suggest_refactoring(self, request: AIAnalysisRequest, context: Dict[str, Any]) -> AIAnalysisResult:
        """Suggest refactoring improvements"""
        
        prompt = f"""
        Analyze the following code and suggest refactoring improvements:
        
        Target: {request.target}
        Instructions: {request.instructions}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Please provide:
        1. Identified code smells
        2. Specific refactoring suggestions
        3. Improved code structure
        4. Benefits of each suggestion
        5. Priority order for refactoring
        """
        
        try:
            analysis = await codebase_ai(prompt, target=request.target, context=context)
            
            return AIAnalysisResult(
                task_type=request.task_type,
                target=str(request.target),
                analysis=analysis,
                suggestions=self._extract_suggestions(analysis),
                confidence_score=0.80,
                metadata={"refactoring_type": "comprehensive", "complexity": "medium"}
            )
            
        except Exception as e:
            logger.error(f"Refactoring analysis failed: {e}")
            raise
    
    async def _generate_tests(self, request: AIAnalysisRequest, context: Dict[str, Any]) -> AIAnalysisResult:
        """Generate test cases using AI"""
        
        prompt = f"""
        Generate comprehensive test cases for the following code:
        
        Target: {request.target}
        Instructions: {request.instructions}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Please provide:
        1. Unit tests for all functions
        2. Edge case testing
        3. Error condition testing
        4. Integration test suggestions
        5. Test data setup and teardown
        
        Use appropriate testing framework for the language.
        """
        
        try:
            tests = await codebase_ai(prompt, target=request.target, context=context)
            
            return AIAnalysisResult(
                task_type=request.task_type,
                target=str(request.target),
                analysis="Generated comprehensive test suite",
                suggestions=[
                    "Review test coverage",
                    "Add performance tests if needed",
                    "Ensure test isolation",
                    "Add integration tests"
                ],
                code_changes=tests,
                confidence_score=0.85,
                metadata={"test_type": "comprehensive", "framework": "auto-detected"}
            )
            
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            raise
    
    async def _security_review(self, request: AIAnalysisRequest, context: Dict[str, Any]) -> AIAnalysisResult:
        """Perform security review using AI"""
        
        prompt = f"""
        Perform a comprehensive security review of the following code:
        
        Target: {request.target}
        Instructions: {request.instructions}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Please analyze for:
        1. Common security vulnerabilities
        2. Input validation issues
        3. Authentication/authorization problems
        4. Data exposure risks
        5. Injection attack vectors
        6. Cryptographic issues
        
        Provide specific recommendations for each issue found.
        """
        
        try:
            analysis = await codebase_ai(prompt, target=request.target, context=context)
            
            return AIAnalysisResult(
                task_type=request.task_type,
                target=str(request.target),
                analysis=analysis,
                suggestions=self._extract_suggestions(analysis),
                confidence_score=0.75,
                metadata={"security_focus": "comprehensive", "vulnerability_scan": True}
            )
            
        except Exception as e:
            logger.error(f"Security review failed: {e}")
            raise
    
    async def _optimize_performance(self, request: AIAnalysisRequest, context: Dict[str, Any]) -> AIAnalysisResult:
        """Suggest performance optimizations"""
        
        prompt = f"""
        Analyze the following code for performance optimization opportunities:
        
        Target: {request.target}
        Instructions: {request.instructions}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Please analyze for:
        1. Algorithmic complexity issues
        2. Memory usage optimization
        3. Database query optimization
        4. Caching opportunities
        5. Async/parallel processing potential
        6. Resource utilization improvements
        
        Provide specific optimization suggestions with expected impact.
        """
        
        try:
            analysis = await codebase_ai(prompt, target=request.target, context=context)
            
            return AIAnalysisResult(
                task_type=request.task_type,
                target=str(request.target),
                analysis=analysis,
                suggestions=self._extract_suggestions(analysis),
                confidence_score=0.80,
                metadata={"optimization_type": "performance", "complexity_analysis": True}
            )
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            raise
    
    async def _review_architecture(self, request: AIAnalysisRequest, context: Dict[str, Any]) -> AIAnalysisResult:
        """Review architectural patterns and design"""
        
        prompt = f"""
        Review the architectural design and patterns in the following code:
        
        Target: {request.target}
        Instructions: {request.instructions}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Please analyze:
        1. Design patterns usage
        2. Architectural principles adherence
        3. Separation of concerns
        4. Dependency management
        5. Scalability considerations
        6. Maintainability aspects
        
        Suggest architectural improvements and best practices.
        """
        
        try:
            analysis = await codebase_ai(prompt, target=request.target, context=context)
            
            return AIAnalysisResult(
                task_type=request.task_type,
                target=str(request.target),
                analysis=analysis,
                suggestions=self._extract_suggestions(analysis),
                confidence_score=0.85,
                metadata={"review_type": "architecture", "design_patterns": True}
            )
            
        except Exception as e:
            logger.error(f"Architecture review failed: {e}")
            raise
    
    def _extract_suggestions(self, analysis: str) -> List[str]:
        """Extract actionable suggestions from analysis text"""
        
        suggestions = []
        
        # Simple extraction based on common patterns
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['suggest', 'recommend', 'should', 'consider', 'improve']):
                if len(line) > 10 and len(line) < 200:  # Reasonable suggestion length
                    suggestions.append(line)
        
        # Limit to top 10 suggestions
        return suggestions[:10]
    
    async def batch_analyze(self, requests: List[AIAnalysisRequest]) -> List[AIAnalysisResult]:
        """Perform batch analysis for multiple requests"""
        
        try:
            # Execute requests concurrently
            tasks = [self.analyze_with_ai(request) for request in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch analysis request {i} failed: {result}")
                    processed_results.append(AIAnalysisResult(
                        task_type=requests[i].task_type,
                        target=str(requests[i].target),
                        analysis=f"Analysis failed: {str(result)}",
                        suggestions=[],
                        confidence_score=0.0
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            raise
    
    async def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all analyses performed"""
        
        if not self.analysis_cache:
            return {"message": "No analyses performed yet"}
        
        summary = {
            "total_analyses": len(self.analysis_cache),
            "by_type": {},
            "avg_confidence": 0.0,
            "avg_generation_time": 0.0,
            "recent_analyses": []
        }
        
        # Analyze by type
        for result in self.analysis_cache.values():
            task_type = result.task_type.value
            if task_type not in summary["by_type"]:
                summary["by_type"][task_type] = 0
            summary["by_type"][task_type] += 1
        
        # Calculate averages
        confidence_scores = [r.confidence_score for r in self.analysis_cache.values()]
        generation_times = [r.generation_time for r in self.analysis_cache.values()]
        
        summary["avg_confidence"] = sum(confidence_scores) / len(confidence_scores)
        summary["avg_generation_time"] = sum(generation_times) / len(generation_times)
        
        # Recent analyses (last 5)
        recent = list(self.analysis_cache.values())[-5:]
        summary["recent_analyses"] = [
            {
                "task_type": r.task_type.value,
                "target": r.target,
                "confidence": r.confidence_score,
                "suggestions_count": len(r.suggestions)
            } for r in recent
        ]
        
        return summary
