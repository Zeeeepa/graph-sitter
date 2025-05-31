"""
Performance Validation Testing Suite

Tests system performance benchmarking, scalability testing,
resource utilization optimization, and response time validation.
"""

import pytest
import asyncio
import time
import psutil
import threading
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import resource


class TestPerformanceValidation:
    """Test suite for performance validation."""

    @pytest.fixture
    def performance_monitor(self):
        """Performance monitoring utility."""
        class PerformanceMonitor:
            def __init__(self):
                self.metrics = {}
                self.start_time = None
                self.process = psutil.Process()
            
            def start_monitoring(self):
                self.start_time = time.time()
                self.metrics["start_memory"] = self.process.memory_info().rss / 1024 / 1024  # MB
                self.metrics["start_cpu"] = self.process.cpu_percent()
            
            def stop_monitoring(self):
                if self.start_time:
                    self.metrics["duration"] = time.time() - self.start_time
                    self.metrics["end_memory"] = self.process.memory_info().rss / 1024 / 1024  # MB
                    self.metrics["end_cpu"] = self.process.cpu_percent()
                    self.metrics["memory_delta"] = self.metrics["end_memory"] - self.metrics["start_memory"]
            
            def get_metrics(self):
                return self.metrics.copy()
        
        return PerformanceMonitor()

    @pytest.fixture
    def load_generator(self):
        """Load generation utility for stress testing."""
        class LoadGenerator:
            def __init__(self):
                self.results = []
            
            def generate_load(self, target_function, num_requests=100, concurrent_users=10):
                """Generate load against a target function."""
                def worker():
                    start_time = time.time()
                    try:
                        result = target_function()
                        status = "success"
                        error = None
                    except Exception as e:
                        result = None
                        status = "error"
                        error = str(e)
                    
                    duration = time.time() - start_time
                    return {
                        "status": status,
                        "duration": duration,
                        "error": error,
                        "result": result
                    }
                
                # Execute load test
                with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                    futures = [executor.submit(worker) for _ in range(num_requests)]
                    results = [future.result() for future in as_completed(futures)]
                
                return results
        
        return LoadGenerator()

    def test_system_performance_benchmarking(self, performance_monitor):
        """Test system performance benchmarking."""
        from graph_sitter.core import CodebaseAnalyzer
        from graph_sitter.performance import PerformanceBenchmark
        
        benchmark = PerformanceBenchmark()
        
        # Test code analysis performance
        performance_monitor.start_monitoring()
        
        analysis_results = benchmark.benchmark_code_analysis(
            test_cases=[
                {"size": "small", "files": 10, "lines": 1000},
                {"size": "medium", "files": 100, "lines": 10000},
                {"size": "large", "files": 1000, "lines": 100000}
            ]
        )
        
        performance_monitor.stop_monitoring()
        metrics = performance_monitor.get_metrics()
        
        # Verify performance benchmarks
        for size, result in analysis_results.items():
            assert result["duration"] > 0
            assert result["throughput"] > 0  # files per second
            assert result["memory_usage"] > 0
            
            # Performance thresholds
            if size == "small":
                assert result["duration"] < 5.0  # Under 5 seconds
            elif size == "medium":
                assert result["duration"] < 30.0  # Under 30 seconds
            elif size == "large":
                assert result["duration"] < 300.0  # Under 5 minutes
        
        # Overall system metrics
        assert metrics["memory_delta"] < 500  # Less than 500MB memory increase
        assert metrics["duration"] < 600  # Total benchmark under 10 minutes

    def test_scalability_testing(self, load_generator):
        """Test system scalability under increasing load."""
        from graph_sitter.core import CodebaseAnalyzer
        
        analyzer = CodebaseAnalyzer()
        
        # Test different load levels
        load_levels = [
            {"users": 1, "requests": 10},
            {"users": 5, "requests": 50},
            {"users": 10, "requests": 100},
            {"users": 20, "requests": 200}
        ]
        
        scalability_results = {}
        
        for load_level in load_levels:
            def test_function():
                # Simulate analysis operation
                return analyzer.quick_analyze("test_file.py")
            
            results = load_generator.generate_load(
                target_function=test_function,
                num_requests=load_level["requests"],
                concurrent_users=load_level["users"]
            )
            
            # Calculate metrics
            successful_requests = [r for r in results if r["status"] == "success"]
            success_rate = len(successful_requests) / len(results)
            avg_response_time = statistics.mean([r["duration"] for r in successful_requests])
            p95_response_time = statistics.quantiles([r["duration"] for r in successful_requests], n=20)[18]  # 95th percentile
            
            scalability_results[load_level["users"]] = {
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time,
                "throughput": len(successful_requests) / sum(r["duration"] for r in successful_requests)
            }
        
        # Verify scalability characteristics
        for users, metrics in scalability_results.items():
            assert metrics["success_rate"] >= 0.95  # At least 95% success rate
            assert metrics["avg_response_time"] < 10.0  # Average under 10 seconds
            assert metrics["p95_response_time"] < 30.0  # 95th percentile under 30 seconds
        
        # Verify system scales reasonably
        single_user_throughput = scalability_results[1]["throughput"]
        multi_user_throughput = scalability_results[10]["throughput"]
        
        # Should achieve at least 50% of linear scaling
        assert multi_user_throughput >= single_user_throughput * 5

    def test_resource_utilization_optimization(self, performance_monitor):
        """Test resource utilization optimization."""
        from graph_sitter.optimization import ResourceOptimizer
        
        optimizer = ResourceOptimizer()
        
        # Test memory optimization
        performance_monitor.start_monitoring()
        
        memory_test_results = optimizer.test_memory_optimization(
            test_scenarios=[
                "large_file_analysis",
                "concurrent_processing",
                "memory_intensive_operations"
            ]
        )
        
        performance_monitor.stop_monitoring()
        metrics = performance_monitor.get_metrics()
        
        # Verify memory optimization
        for scenario, result in memory_test_results.items():
            assert result["peak_memory_mb"] < 1024  # Under 1GB peak memory
            assert result["memory_efficiency"] > 0.7  # At least 70% efficient
            assert result["gc_collections"] < 100  # Reasonable garbage collection
        
        # Test CPU optimization
        cpu_test_results = optimizer.test_cpu_optimization(
            test_scenarios=[
                "parallel_processing",
                "cpu_intensive_analysis",
                "concurrent_tasks"
            ]
        )
        
        for scenario, result in cpu_test_results.items():
            assert result["cpu_utilization"] > 0.5  # At least 50% CPU utilization
            assert result["cpu_utilization"] < 0.9  # Not over 90% (leave headroom)
            assert result["thread_efficiency"] > 0.6  # Efficient threading
        
        # Test I/O optimization
        io_test_results = optimizer.test_io_optimization(
            test_scenarios=[
                "file_reading",
                "concurrent_file_access",
                "large_file_processing"
            ]
        )
        
        for scenario, result in io_test_results.items():
            assert result["io_wait_time"] < 0.3  # Less than 30% I/O wait
            assert result["throughput_mbps"] > 10  # At least 10 MB/s throughput

    def test_response_time_validation(self):
        """Test response time validation across different operations."""
        from graph_sitter.core import CodebaseAnalyzer
        from graph_sitter.api import APIEndpoints
        
        # Test API response times
        api = APIEndpoints()
        
        api_endpoints = [
            {"endpoint": "/analyze", "method": "POST", "expected_time": 5.0},
            {"endpoint": "/health", "method": "GET", "expected_time": 0.1},
            {"endpoint": "/metrics", "method": "GET", "expected_time": 1.0},
            {"endpoint": "/status", "method": "GET", "expected_time": 0.5}
        ]
        
        for endpoint_config in api_endpoints:
            start_time = time.time()
            
            if endpoint_config["method"] == "GET":
                response = api.get(endpoint_config["endpoint"])
            else:
                response = api.post(endpoint_config["endpoint"], data={})
            
            response_time = time.time() - start_time
            
            assert response_time < endpoint_config["expected_time"]
            assert response["status"] == "success"
        
        # Test core operation response times
        analyzer = CodebaseAnalyzer()
        
        core_operations = [
            {"operation": "parse_file", "max_time": 2.0},
            {"operation": "analyze_dependencies", "max_time": 5.0},
            {"operation": "calculate_metrics", "max_time": 3.0},
            {"operation": "generate_report", "max_time": 10.0}
        ]
        
        for operation_config in core_operations:
            start_time = time.time()
            
            if operation_config["operation"] == "parse_file":
                result = analyzer.parse_file("test_file.py")
            elif operation_config["operation"] == "analyze_dependencies":
                result = analyzer.analyze_dependencies("test_project")
            elif operation_config["operation"] == "calculate_metrics":
                result = analyzer.calculate_metrics("test_project")
            elif operation_config["operation"] == "generate_report":
                result = analyzer.generate_report("test_project")
            
            operation_time = time.time() - start_time
            
            assert operation_time < operation_config["max_time"]
            assert result is not None

    def test_concurrent_performance(self):
        """Test performance under concurrent load."""
        from graph_sitter.core import CodebaseAnalyzer
        
        analyzer = CodebaseAnalyzer()
        
        def concurrent_analysis_task(task_id):
            start_time = time.time()
            try:
                result = analyzer.analyze_project(f"test_project_{task_id}")
                status = "success"
                error = None
            except Exception as e:
                result = None
                status = "error"
                error = str(e)
            
            duration = time.time() - start_time
            return {
                "task_id": task_id,
                "status": status,
                "duration": duration,
                "error": error
            }
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        
        for concurrency in concurrency_levels:
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(concurrent_analysis_task, i) for i in range(concurrency)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_tasks = [r for r in results if r["status"] == "success"]
            success_rate = len(successful_tasks) / len(results)
            avg_task_duration = statistics.mean([r["duration"] for r in successful_tasks])
            
            # Performance assertions
            assert success_rate >= 0.9  # At least 90% success rate
            assert total_time < 60.0  # Complete within 60 seconds
            assert avg_task_duration < 30.0  # Average task under 30 seconds
            
            # Verify reasonable scaling
            if concurrency == 1:
                baseline_time = total_time
            else:
                # Should not be more than 2x slower than baseline per task
                assert total_time / concurrency < baseline_time * 2

    def test_memory_leak_detection(self):
        """Test for memory leaks during extended operations."""
        import gc
        
        from graph_sitter.core import CodebaseAnalyzer
        
        analyzer = CodebaseAnalyzer()
        
        # Baseline memory measurement
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Perform repeated operations
        for i in range(100):
            # Simulate various operations
            analyzer.parse_file(f"test_file_{i}.py")
            analyzer.analyze_dependencies(f"test_project_{i}")
            analyzer.calculate_metrics(f"test_project_{i}")
            
            # Force garbage collection every 10 iterations
            if i % 10 == 0:
                gc.collect()
        
        # Final memory measurement
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory leak detection
        assert memory_increase < 100  # Less than 100MB increase
        
        # Test memory cleanup
        analyzer.cleanup()
        gc.collect()
        
        cleanup_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_after_cleanup = cleanup_memory - initial_memory
        
        assert memory_after_cleanup < memory_increase * 0.5  # At least 50% cleanup

    def test_database_performance(self):
        """Test database performance under load."""
        from graph_sitter.database import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Test query performance
        query_tests = [
            {"query": "SELECT * FROM tasks LIMIT 100", "max_time": 0.1},
            {"query": "SELECT COUNT(*) FROM codebase", "max_time": 0.05},
            {"query": "SELECT * FROM analytics WHERE event_type = 'analysis'", "max_time": 0.2},
            {"query": "SELECT * FROM prompts JOIN tasks ON prompts.task_id = tasks.id", "max_time": 0.5}
        ]
        
        for query_test in query_tests:
            start_time = time.time()
            result = db_manager.execute_query(query_test["query"])
            query_time = time.time() - start_time
            
            assert query_time < query_test["max_time"]
            assert result is not None
        
        # Test concurrent database access
        def db_operation(operation_id):
            start_time = time.time()
            try:
                # Simulate database operations
                db_manager.insert_task(f"Task {operation_id}", "Test description")
                db_manager.get_tasks(limit=10)
                db_manager.update_task_status(operation_id, "completed")
                status = "success"
                error = None
            except Exception as e:
                status = "error"
                error = str(e)
            
            duration = time.time() - start_time
            return {"status": status, "duration": duration, "error": error}
        
        # Test with concurrent database operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(db_operation, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze database performance
        successful_ops = [r for r in results if r["status"] == "success"]
        success_rate = len(successful_ops) / len(results)
        avg_duration = statistics.mean([r["duration"] for r in successful_ops])
        
        assert success_rate >= 0.95  # At least 95% success rate
        assert avg_duration < 1.0  # Average operation under 1 second

    def test_caching_performance(self):
        """Test caching system performance."""
        from graph_sitter.caching import CacheManager
        
        cache_manager = CacheManager()
        
        # Test cache hit/miss performance
        cache_key = "test_analysis_result"
        test_data = {"analysis": "result", "metrics": [1, 2, 3, 4, 5]}
        
        # Test cache write performance
        start_time = time.time()
        cache_manager.set(cache_key, test_data)
        write_time = time.time() - start_time
        
        assert write_time < 0.01  # Cache write under 10ms
        
        # Test cache read performance
        start_time = time.time()
        cached_data = cache_manager.get(cache_key)
        read_time = time.time() - start_time
        
        assert read_time < 0.005  # Cache read under 5ms
        assert cached_data == test_data
        
        # Test cache performance under load
        def cache_operation(op_id):
            start_time = time.time()
            
            # Mix of read and write operations
            if op_id % 2 == 0:
                cache_manager.set(f"key_{op_id}", {"data": op_id})
            else:
                cache_manager.get(f"key_{op_id - 1}")
            
            return time.time() - start_time
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(cache_operation, i) for i in range(1000)]
            durations = [future.result() for future in as_completed(futures)]
        
        avg_cache_time = statistics.mean(durations)
        max_cache_time = max(durations)
        
        assert avg_cache_time < 0.01  # Average under 10ms
        assert max_cache_time < 0.1   # Max under 100ms

    def test_network_performance(self):
        """Test network performance for external API calls."""
        from graph_sitter.integrations import ExternalAPIClient
        
        api_client = ExternalAPIClient()
        
        # Test API call performance
        api_tests = [
            {"service": "github", "endpoint": "/user", "max_time": 2.0},
            {"service": "linear", "endpoint": "/issues", "max_time": 3.0},
            {"service": "slack", "endpoint": "/channels", "max_time": 1.5}
        ]
        
        for api_test in api_tests:
            start_time = time.time()
            
            try:
                response = api_client.call_api(
                    service=api_test["service"],
                    endpoint=api_test["endpoint"]
                )
                call_time = time.time() - start_time
                
                assert call_time < api_test["max_time"]
                assert response["status"] == "success"
                
            except Exception as e:
                # Network issues are acceptable in tests
                if "network" not in str(e).lower():
                    raise
        
        # Test concurrent API calls
        def api_call_task(task_id):
            start_time = time.time()
            try:
                response = api_client.call_api("github", "/user")
                status = "success"
                error = None
            except Exception as e:
                response = None
                status = "error"
                error = str(e)
            
            duration = time.time() - start_time
            return {"status": status, "duration": duration, "error": error}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(api_call_task, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze API performance
        successful_calls = [r for r in results if r["status"] == "success"]
        if successful_calls:  # Only test if we have successful calls
            success_rate = len(successful_calls) / len(results)
            avg_duration = statistics.mean([r["duration"] for r in successful_calls])
            
            assert success_rate >= 0.8  # At least 80% success (network can be flaky)
            assert avg_duration < 5.0   # Average under 5 seconds

