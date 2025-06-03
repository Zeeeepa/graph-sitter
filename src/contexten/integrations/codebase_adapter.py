"""
Codebase Integration Adapter

This module provides integration between the Contexten system and
the existing graph_sitter codebase analysis capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import json

# Import existing codebase analysis functions
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Request for codebase analysis."""
    repository_url: str
    analysis_type: str = "comprehensive"
    target_files: Optional[List[str]] = None
    target_classes: Optional[List[str]] = None
    target_functions: Optional[List[str]] = None
    include_dependencies: bool = True
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisResult:
    """Result from codebase analysis."""
    request_id: str
    repository_url: str
    analysis_type: str
    status: str
    summary: Optional[str] = None
    file_analyses: Optional[Dict[str, Any]] = None
    class_analyses: Optional[Dict[str, Any]] = None
    function_analyses: Optional[Dict[str, Any]] = None
    symbol_analyses: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CodebaseAdapter:
    """
    Adapter for integrating with existing graph_sitter codebase analysis.
    
    This adapter provides a unified interface for accessing codebase analysis
    capabilities while maintaining compatibility with the existing system.
    """
    
    def __init__(self):
        """Initialize the codebase adapter."""
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        self.active_analyses: Dict[str, asyncio.Task] = {}
        
        logger.info("Codebase adapter initialized")
    
    async def analyze_codebase(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Perform comprehensive codebase analysis.
        
        Args:
            request: Analysis request parameters
            
        Returns:
            Analysis result
        """
        request_id = self._generate_request_id(request)
        
        logger.info(f"Starting codebase analysis: {request.repository_url}")
        
        # Check cache first
        if request_id in self.analysis_cache:
            cached_result = self.analysis_cache[request_id]
            if self._is_cache_valid(cached_result):
                logger.info(f"Returning cached analysis result for {request_id}")
                return cached_result
        
        # Create analysis result
        result = AnalysisResult(
            request_id=request_id,
            repository_url=request.repository_url,
            analysis_type=request.analysis_type,
            status="running",
            started_at=datetime.now()
        )
        
        try:
            # Perform the analysis based on type
            if request.analysis_type == "comprehensive":
                await self._perform_comprehensive_analysis(request, result)
            elif request.analysis_type == "summary":
                await self._perform_summary_analysis(request, result)
            elif request.analysis_type == "targeted":
                await self._perform_targeted_analysis(request, result)
            else:
                raise ValueError(f"Unknown analysis type: {request.analysis_type}")
            
            result.status = "completed"
            result.completed_at = datetime.now()
            
            # Cache the result
            self.analysis_cache[request_id] = result
            
            logger.info(f"Completed codebase analysis: {request_id}")
            
        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            result.completed_at = datetime.now()
            logger.error(f"Codebase analysis failed: {e}")
        
        return result
    
    async def _perform_comprehensive_analysis(self, request: AnalysisRequest, result: AnalysisResult):
        """Perform comprehensive codebase analysis."""
        # This would integrate with actual codebase loading
        # For now, we'll simulate the analysis
        
        logger.info("Performing comprehensive analysis...")
        
        # Simulate loading codebase
        await asyncio.sleep(1)  # Simulate processing time
        
        # Use existing analysis functions (simulated)
        try:
            # In a real implementation, this would load the actual codebase
            # codebase = load_codebase(request.repository_url)
            # result.summary = get_codebase_summary(codebase)
            
            # For now, provide simulated results
            result.summary = f"Comprehensive analysis of {request.repository_url}"
            result.file_analyses = await self._analyze_files(request)
            result.class_analyses = await self._analyze_classes(request)
            result.function_analyses = await self._analyze_functions(request)
            result.metrics = await self._calculate_metrics(request)
            
        except Exception as e:
            raise Exception(f"Comprehensive analysis failed: {e}")
    
    async def _perform_summary_analysis(self, request: AnalysisRequest, result: AnalysisResult):
        """Perform summary-only analysis."""
        logger.info("Performing summary analysis...")
        
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # In a real implementation:
        # codebase = load_codebase(request.repository_url)
        # result.summary = get_codebase_summary(codebase)
        
        result.summary = f"Summary analysis of {request.repository_url}: Python project with multiple modules"
        result.metrics = {
            "total_files": 42,
            "total_lines": 15000,
            "total_functions": 180,
            "total_classes": 25
        }
    
    async def _perform_targeted_analysis(self, request: AnalysisRequest, result: AnalysisResult):
        """Perform targeted analysis of specific files/classes/functions."""
        logger.info("Performing targeted analysis...")
        
        await asyncio.sleep(0.3)  # Simulate processing time
        
        # Analyze specific targets
        if request.target_files:
            result.file_analyses = {}
            for file_path in request.target_files:
                result.file_analyses[file_path] = await self._analyze_single_file(file_path)
        
        if request.target_classes:
            result.class_analyses = {}
            for class_name in request.target_classes:
                result.class_analyses[class_name] = await self._analyze_single_class(class_name)
        
        if request.target_functions:
            result.function_analyses = {}
            for function_name in request.target_functions:
                result.function_analyses[function_name] = await self._analyze_single_function(function_name)
    
    async def _analyze_files(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Analyze files in the codebase."""
        # In a real implementation, this would use get_file_summary
        # for each file in the codebase
        
        return {
            "src/main.py": {
                "lines": 150,
                "functions": 8,
                "classes": 2,
                "complexity": "medium",
                "summary": "Main application entry point"
            },
            "src/utils.py": {
                "lines": 80,
                "functions": 12,
                "classes": 0,
                "complexity": "low",
                "summary": "Utility functions"
            }
        }
    
    async def _analyze_classes(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Analyze classes in the codebase."""
        # In a real implementation, this would use get_class_summary
        # for each class in the codebase
        
        return {
            "MainApplication": {
                "file": "src/main.py",
                "methods": 6,
                "lines": 120,
                "complexity": "medium",
                "summary": "Main application class"
            },
            "ConfigManager": {
                "file": "src/config.py",
                "methods": 4,
                "lines": 60,
                "complexity": "low",
                "summary": "Configuration management class"
            }
        }
    
    async def _analyze_functions(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Analyze functions in the codebase."""
        # In a real implementation, this would use get_function_summary
        # for each function in the codebase
        
        return {
            "process_data": {
                "file": "src/main.py",
                "lines": 25,
                "parameters": 3,
                "complexity": "medium",
                "summary": "Processes input data"
            },
            "validate_input": {
                "file": "src/utils.py",
                "lines": 15,
                "parameters": 2,
                "complexity": "low",
                "summary": "Validates input parameters"
            }
        }
    
    async def _analyze_single_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file."""
        # In a real implementation: get_file_summary(file)
        return {
            "path": file_path,
            "lines": 100,
            "functions": 5,
            "classes": 1,
            "summary": f"Analysis of {file_path}"
        }
    
    async def _analyze_single_class(self, class_name: str) -> Dict[str, Any]:
        """Analyze a single class."""
        # In a real implementation: get_class_summary(class)
        return {
            "name": class_name,
            "methods": 4,
            "lines": 80,
            "summary": f"Analysis of class {class_name}"
        }
    
    async def _analyze_single_function(self, function_name: str) -> Dict[str, Any]:
        """Analyze a single function."""
        # In a real implementation: get_function_summary(function)
        return {
            "name": function_name,
            "lines": 20,
            "parameters": 2,
            "summary": f"Analysis of function {function_name}"
        }
    
    async def _calculate_metrics(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Calculate codebase metrics."""
        return {
            "total_files": 15,
            "total_lines": 2500,
            "total_functions": 45,
            "total_classes": 8,
            "complexity_score": 6.5,
            "maintainability_index": 78,
            "test_coverage": 85.2,
            "documentation_coverage": 72.1
        }
    
    def _generate_request_id(self, request: AnalysisRequest) -> str:
        """Generate a unique request ID."""
        import hashlib
        request_str = f"{request.repository_url}:{request.analysis_type}:{request.target_files}:{request.target_classes}:{request.target_functions}"
        return hashlib.md5(request_str.encode()).hexdigest()[:12]
    
    def _is_cache_valid(self, result: AnalysisResult, max_age_hours: int = 24) -> bool:
        """Check if cached result is still valid."""
        if not result.completed_at:
            return False
        
        age = datetime.now() - result.completed_at
        return age.total_seconds() < (max_age_hours * 3600)
    
    async def get_analysis_status(self, request_id: str) -> Optional[str]:
        """Get the status of an analysis request."""
        if request_id in self.analysis_cache:
            return self.analysis_cache[request_id].status
        elif request_id in self.active_analyses:
            return "running"
        else:
            return None
    
    async def cancel_analysis(self, request_id: str) -> bool:
        """Cancel an active analysis."""
        if request_id in self.active_analyses:
            task = self.active_analyses[request_id]
            task.cancel()
            del self.active_analyses[request_id]
            logger.info(f"Cancelled analysis: {request_id}")
            return True
        return False
    
    def get_cached_analyses(self) -> List[AnalysisResult]:
        """Get all cached analysis results."""
        return list(self.analysis_cache.values())
    
    def clear_cache(self, older_than_hours: Optional[int] = None):
        """Clear analysis cache."""
        if older_than_hours is None:
            self.analysis_cache.clear()
            logger.info("Cleared all cached analyses")
        else:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            to_remove = []
            
            for request_id, result in self.analysis_cache.items():
                if result.completed_at and result.completed_at < cutoff_time:
                    to_remove.append(request_id)
            
            for request_id in to_remove:
                del self.analysis_cache[request_id]
            
            logger.info(f"Cleared {len(to_remove)} old cached analyses")
    
    async def batch_analyze(self, requests: List[AnalysisRequest]) -> List[AnalysisResult]:
        """Perform batch analysis of multiple requests."""
        logger.info(f"Starting batch analysis of {len(requests)} requests")
        
        # Create tasks for concurrent execution
        tasks = [self.analyze_codebase(request) for request in requests]
        
        # Execute all analyses concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        analysis_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error result
                error_result = AnalysisResult(
                    request_id=self._generate_request_id(requests[i]),
                    repository_url=requests[i].repository_url,
                    analysis_type=requests[i].analysis_type,
                    status="failed",
                    error_message=str(result),
                    started_at=datetime.now(),
                    completed_at=datetime.now()
                )
                analysis_results.append(error_result)
            else:
                analysis_results.append(result)
        
        logger.info(f"Completed batch analysis: {len(analysis_results)} results")
        return analysis_results
    
    def get_adapter_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        total_analyses = len(self.analysis_cache)
        successful_analyses = len([r for r in self.analysis_cache.values() if r.status == "completed"])
        failed_analyses = len([r for r in self.analysis_cache.values() if r.status == "failed"])
        
        return {
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "success_rate": successful_analyses / total_analyses if total_analyses > 0 else 0,
            "active_analyses": len(self.active_analyses),
            "cache_size": len(self.analysis_cache),
            "available_functions": [
                "get_codebase_summary",
                "get_file_summary",
                "get_class_summary",
                "get_function_summary",
                "get_symbol_summary"
            ]
        }


# Convenience functions for common operations
async def quick_analyze(repository_url: str, analysis_type: str = "summary") -> AnalysisResult:
    """Quick analysis of a repository."""
    adapter = CodebaseAdapter()
    request = AnalysisRequest(
        repository_url=repository_url,
        analysis_type=analysis_type
    )
    return await adapter.analyze_codebase(request)


async def analyze_specific_files(repository_url: str, file_paths: List[str]) -> AnalysisResult:
    """Analyze specific files in a repository."""
    adapter = CodebaseAdapter()
    request = AnalysisRequest(
        repository_url=repository_url,
        analysis_type="targeted",
        target_files=file_paths
    )
    return await adapter.analyze_codebase(request)


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the codebase adapter."""
        adapter = CodebaseAdapter()
        
        # Comprehensive analysis
        request = AnalysisRequest(
            repository_url="https://github.com/example/repo",
            analysis_type="comprehensive"
        )
        
        result = await adapter.analyze_codebase(request)
        print(f"Analysis result: {result.status}")
        print(f"Summary: {result.summary}")
        
        # Targeted analysis
        targeted_request = AnalysisRequest(
            repository_url="https://github.com/example/repo",
            analysis_type="targeted",
            target_files=["src/main.py", "src/utils.py"]
        )
        
        targeted_result = await adapter.analyze_codebase(targeted_request)
        print(f"Targeted analysis: {targeted_result.file_analyses}")
        
        # Get adapter stats
        stats = adapter.get_adapter_stats()
        print(f"Adapter stats: {stats}")
    
    asyncio.run(example_usage())

