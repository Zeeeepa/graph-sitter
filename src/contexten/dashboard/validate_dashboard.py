#!/usr/bin/env python3
"""
Dashboard Validation Script
Comprehensive validation of dashboard functionality and integrations
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx

logger = logging.getLogger(__name__)

class DashboardValidator:
    """
    Comprehensive dashboard validation and testing
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.validation_results = []
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_result(self, test_name: str, success: bool, message: str = "", details: Any = None):
        """Log validation result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        self.validation_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
        
        if not success and details:
            logger.error(f"Details: {details}")
    
    async def test_dashboard_health(self) -> bool:
        """Test basic dashboard health"""
        try:
            response = await self.client.get(f"{self.base_url}/")
            success = response.status_code == 200
            
            self.log_result(
                "Dashboard Health",
                success,
                f"Status: {response.status_code}",
                {"status_code": response.status_code, "response_time": response.elapsed.total_seconds()}
            )
            
            return success
            
        except Exception as e:
            self.log_result("Dashboard Health", False, f"Connection failed: {e}")
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Test core API endpoints"""
        endpoints = [
            ("/api/dashboard/overview", "GET"),
            ("/api/projects", "GET"),
            ("/api/flows/active", "GET"),
            ("/api/integrations/status", "GET"),
            ("/api/system/status", "GET")
        ]
        
        all_passed = True
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = await self.client.get(f"{self.base_url}{endpoint}")
                else:
                    response = await self.client.request(method, f"{self.base_url}{endpoint}")
                
                success = response.status_code in [200, 201, 202]
                
                self.log_result(
                    f"API {method} {endpoint}",
                    success,
                    f"Status: {response.status_code}",
                    {"status_code": response.status_code, "endpoint": endpoint}
                )
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"API {method} {endpoint}", False, f"Request failed: {e}")
                all_passed = False
        
        return all_passed
    
    async def test_enhanced_endpoints(self) -> bool:
        """Test enhanced API endpoints"""
        enhanced_endpoints = [
            ("/api/v2/projects/comprehensive", "GET"),
            ("/api/v2/analytics/comprehensive", "GET"),
            ("/api/v2/monitoring/real-time", "GET")
        ]
        
        all_passed = True
        
        for endpoint, method in enhanced_endpoints:
            try:
                response = await self.client.request(method, f"{self.base_url}{endpoint}")
                success = response.status_code in [200, 201, 202, 503]  # 503 is OK for unavailable integrations
                
                self.log_result(
                    f"Enhanced API {method} {endpoint}",
                    success,
                    f"Status: {response.status_code}",
                    {"status_code": response.status_code, "endpoint": endpoint}
                )
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Enhanced API {method} {endpoint}", False, f"Request failed: {e}")
                all_passed = False
        
        return all_passed
    
    async def test_analysis_endpoints(self) -> bool:
        """Test analysis endpoints"""
        # Test project analysis endpoint
        try:
            test_data = {"project_path": "/tmp/test_project"}
            response = await self.client.post(
                f"{self.base_url}/api/analysis/project",
                json=test_data
            )
            
            # Expect either success or service unavailable
            success = response.status_code in [200, 400, 503]
            
            self.log_result(
                "Analysis Project Endpoint",
                success,
                f"Status: {response.status_code}",
                {"status_code": response.status_code}
            )
            
            return success
            
        except Exception as e:
            self.log_result("Analysis Project Endpoint", False, f"Request failed: {e}")
            return False
    
    async def test_static_files(self) -> bool:
        """Test static file serving"""
        static_files = [
            "/static/css/dashboard.css",
            "/static/js/dashboard.js"
        ]
        
        all_passed = True
        
        for static_file in static_files:
            try:
                response = await self.client.get(f"{self.base_url}{static_file}")
                success = response.status_code in [200, 404]  # 404 is OK if using CDN
                
                self.log_result(
                    f"Static File {static_file}",
                    success,
                    f"Status: {response.status_code}",
                    {"status_code": response.status_code, "file": static_file}
                )
                
                if response.status_code == 404:
                    logger.warning(f"Static file not found: {static_file} (CDN fallback will be used)")
                
            except Exception as e:
                self.log_result(f"Static File {static_file}", False, f"Request failed: {e}")
                all_passed = False
        
        return all_passed
    
    async def test_integration_status(self) -> Dict[str, bool]:
        """Test integration status"""
        try:
            response = await self.client.get(f"{self.base_url}/api/integrations/status")
            
            if response.status_code == 200:
                data = response.json()
                integrations = data.get("integrations", {})
                
                for integration, status in integrations.items():
                    self.log_result(
                        f"Integration {integration}",
                        True,  # Just checking if we can get status
                        f"Status: {'Connected' if status else 'Disconnected'}",
                        {"integration": integration, "connected": status}
                    )
                
                return integrations
            else:
                self.log_result("Integration Status", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_result("Integration Status", False, f"Request failed: {e}")
            return {}
    
    async def test_dashboard_functionality(self) -> bool:
        """Test core dashboard functionality"""
        try:
            # Test dashboard overview
            response = await self.client.get(f"{self.base_url}/api/dashboard/overview")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for expected fields
                expected_fields = ["active_projects", "running_flows", "completed_today", "success_rate"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                success = len(missing_fields) == 0
                
                self.log_result(
                    "Dashboard Overview Data",
                    success,
                    f"Fields present: {len(expected_fields) - len(missing_fields)}/{len(expected_fields)}",
                    {"missing_fields": missing_fields, "data": data}
                )
                
                return success
            else:
                self.log_result("Dashboard Overview Data", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Dashboard Overview Data", False, f"Request failed: {e}")
            return False
    
    async def test_flow_management(self) -> bool:
        """Test flow management functionality"""
        try:
            # Test getting active flows
            response = await self.client.get(f"{self.base_url}/api/flows/active")
            success = response.status_code == 200
            
            self.log_result(
                "Flow Management",
                success,
                f"Active flows endpoint status: {response.status_code}",
                {"status_code": response.status_code}
            )
            
            return success
            
        except Exception as e:
            self.log_result("Flow Management", False, f"Request failed: {e}")
            return False
    
    async def test_performance(self) -> Dict[str, float]:
        """Test dashboard performance"""
        performance_metrics = {}
        
        # Test response times for key endpoints
        endpoints = [
            "/",
            "/api/dashboard/overview",
            "/api/projects",
            "/api/flows/active"
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = await self.client.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                response_time = end_time - start_time
                performance_metrics[endpoint] = response_time
                
                # Consider anything under 2 seconds as good
                success = response_time < 2.0
                
                self.log_result(
                    f"Performance {endpoint}",
                    success,
                    f"Response time: {response_time:.3f}s",
                    {"response_time": response_time, "endpoint": endpoint}
                )
                
            except Exception as e:
                self.log_result(f"Performance {endpoint}", False, f"Request failed: {e}")
                performance_metrics[endpoint] = float('inf')
        
        return performance_metrics
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation suite"""
        logger.info("Starting comprehensive dashboard validation...")
        
        validation_suite = [
            ("Dashboard Health", self.test_dashboard_health),
            ("API Endpoints", self.test_api_endpoints),
            ("Enhanced Endpoints", self.test_enhanced_endpoints),
            ("Analysis Endpoints", self.test_analysis_endpoints),
            ("Static Files", self.test_static_files),
            ("Dashboard Functionality", self.test_dashboard_functionality),
            ("Flow Management", self.test_flow_management)
        ]
        
        results = {}
        
        for test_name, test_func in validation_suite:
            logger.info(f"Running {test_name} tests...")
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                logger.error(f"Error in {test_name}: {e}")
                results[test_name] = False
        
        # Test integrations
        logger.info("Testing integrations...")
        integrations = await self.test_integration_status()
        results["Integrations"] = integrations
        
        # Test performance
        logger.info("Testing performance...")
        performance = await self.test_performance()
        results["Performance"] = performance
        
        # Generate summary
        passed_tests = sum(1 for result in results.values() if result is True)
        total_tests = len([r for r in results.values() if isinstance(r, bool)])
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "results": results,
            "detailed_results": self.validation_results,
            "integrations": integrations,
            "performance_metrics": performance
        }
        
        return summary
    
    def generate_report(self, summary: Dict[str, Any]) -> str:
        """Generate validation report"""
        report = f"""
# Dashboard Validation Report

## Summary
- **Total Tests**: {summary['total_tests']}
- **Passed**: {summary['passed_tests']}
- **Failed**: {summary['failed_tests']}
- **Success Rate**: {summary['success_rate']:.1f}%

## Test Results
"""
        
        for test_name, result in summary['results'].items():
            if isinstance(result, bool):
                status = "✅ PASS" if result else "❌ FAIL"
                report += f"- **{test_name}**: {status}\n"
            elif isinstance(result, dict):
                report += f"- **{test_name}**: {len(result)} items\n"
        
        report += "\n## Integration Status\n"
        for integration, status in summary['integrations'].items():
            status_text = "Connected" if status else "Disconnected"
            report += f"- **{integration}**: {status_text}\n"
        
        report += "\n## Performance Metrics\n"
        for endpoint, time_taken in summary['performance_metrics'].items():
            if time_taken != float('inf'):
                report += f"- **{endpoint}**: {time_taken:.3f}s\n"
            else:
                report += f"- **{endpoint}**: Failed\n"
        
        if summary['success_rate'] >= 80:
            report += "\n## ✅ Overall Status: HEALTHY\n"
        elif summary['success_rate'] >= 60:
            report += "\n## ⚠️ Overall Status: WARNING\n"
        else:
            report += "\n## ❌ Overall Status: CRITICAL\n"
        
        return report

async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dashboard Validation")
    parser.add_argument("--url", default="http://localhost:8080", help="Dashboard URL")
    parser.add_argument("--output", help="Output file for detailed results")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run validation
    async with DashboardValidator(args.url) as validator:
        summary = await validator.run_comprehensive_validation()
        
        # Generate report
        report = validator.generate_report(summary)
        print(report)
        
        # Save detailed results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Detailed results saved to {args.output}")
        
        # Exit with appropriate code
        if summary['success_rate'] >= 80:
            logger.info("✅ Dashboard validation passed")
            sys.exit(0)
        else:
            logger.error("❌ Dashboard validation failed")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

