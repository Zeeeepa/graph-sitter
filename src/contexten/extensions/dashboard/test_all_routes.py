#!/usr/bin/env python3
"""
Test all routes and endpoints in the dashboard system.
"""

import requests
import subprocess
import time
import sys
import json
from typing import Dict, List, Any

class RouteValidator:
    """Validates all dashboard routes and endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "total_routes": 0,
            "working_routes": 0,
            "broken_routes": 0,
            "route_details": {}
        }
    
    def test_route(self, path: str, method: str = "GET", expected_status: int = 200) -> Dict[str, Any]:
        """Test a single route."""
        route_info = {
            "path": path,
            "method": method,
            "expected_status": expected_status,
            "actual_status": None,
            "response_time": None,
            "content_type": None,
            "content_length": None,
            "working": False,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(f"{self.base_url}{path}", timeout=5)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{path}", json={}, timeout=5)
            else:
                route_info["error"] = f"Unsupported method: {method}"
                return route_info
            
            route_info["response_time"] = time.time() - start_time
            route_info["actual_status"] = response.status_code
            route_info["content_type"] = response.headers.get("content-type", "")
            route_info["content_length"] = len(response.content)
            
            if response.status_code == expected_status:
                route_info["working"] = True
                self.results["working_routes"] += 1
            else:
                route_info["error"] = f"Expected {expected_status}, got {response.status_code}"
                self.results["broken_routes"] += 1
            
        except requests.exceptions.RequestException as e:
            route_info["error"] = str(e)
            self.results["broken_routes"] += 1
        
        self.results["total_routes"] += 1
        return route_info
    
    def test_all_routes(self) -> Dict[str, Any]:
        """Test all known routes."""
        print("🧪 Testing all dashboard routes...")
        
        # Define all routes from the standalone launcher
        routes_to_test = [
            # Basic routes
            ("/", "GET", 200),
            ("/health", "GET", 200),
            ("/api/health", "GET", 200),
            ("/docs", "GET", 200),
            
            # API routes
            ("/api/projects", "GET", 200),
            ("/api/projects", "POST", 422),  # Expect validation error without data
            
            # Non-existent routes (should 404)
            ("/nonexistent", "GET", 404),
            ("/api/nonexistent", "GET", 404),
        ]
        
        for path, method, expected_status in routes_to_test:
            print(f"🔍 Testing {method} {path}")
            route_info = self.test_route(path, method, expected_status)
            self.results["route_details"][f"{method} {path}"] = route_info
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate a route validation report."""
        report = []
        report.append("=" * 60)
        report.append("ROUTE VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY:")
        report.append(f"   Total Routes Tested: {self.results['total_routes']}")
        report.append(f"   Working Routes: {self.results['working_routes']}")
        report.append(f"   Broken Routes: {self.results['broken_routes']}")
        success_rate = (self.results['working_routes'] / self.results['total_routes']) * 100 if self.results['total_routes'] > 0 else 0
        report.append(f"   Success Rate: {success_rate:.1f}%")
        report.append("")
        
        # Route details
        report.append("🔍 ROUTE DETAILS:")
        for route_name, route_info in self.results["route_details"].items():
            status_icon = "✅" if route_info["working"] else "❌"
            report.append(f"\n{status_icon} {route_name}")
            report.append(f"   Status: {route_info['actual_status']} (expected {route_info['expected_status']})")
            
            if route_info["response_time"]:
                report.append(f"   Response Time: {route_info['response_time']:.3f}s")
            
            if route_info["content_type"]:
                report.append(f"   Content Type: {route_info['content_type']}")
            
            if route_info["content_length"]:
                report.append(f"   Content Length: {route_info['content_length']} bytes")
            
            if route_info["error"]:
                report.append(f"   Error: {route_info['error']}")
        
        return "\n".join(report)

def start_dashboard_server():
    """Start the dashboard server in background."""
    print("🚀 Starting dashboard server...")
    process = subprocess.Popen(
        [sys.executable, "start_dashboard_standalone.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Dashboard server started successfully")
            return process
        else:
            print("❌ Dashboard server not responding properly")
            return None
    except requests.exceptions.RequestException:
        print("❌ Dashboard server failed to start")
        return None

def stop_dashboard_server(process):
    """Stop the dashboard server."""
    if process:
        process.terminate()
        process.wait(timeout=5)
        print("🛑 Dashboard server stopped")

def main():
    """Main validation function."""
    print("🧪 ROUTE VALIDATION STARTING")
    print("=" * 60)
    
    # Start server
    server_process = start_dashboard_server()
    if not server_process:
        print("❌ Cannot test routes - server failed to start")
        return 1
    
    try:
        # Test routes
        validator = RouteValidator()
        results = validator.test_all_routes()
        
        # Generate report
        report = validator.generate_report()
        
        # Save report
        with open("ROUTE_VALIDATION_REPORT.md", "w") as f:
            f.write(report)
        
        # Save JSON results
        with open("route_validation_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Route validation complete!")
        print(f"📄 Report saved to: ROUTE_VALIDATION_REPORT.md")
        print(f"📊 JSON results saved to: route_validation_results.json")
        
        # Print summary
        print(f"\n📊 ROUTE VALIDATION SUMMARY:")
        print(f"   Total Routes: {results['total_routes']}")
        print(f"   Working: {results['working_routes']}")
        print(f"   Broken: {results['broken_routes']}")
        success_rate = (results['working_routes'] / results['total_routes']) * 100 if results['total_routes'] > 0 else 0
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if results['broken_routes'] > 0:
            print(f"\n❌ SOME ROUTES FAILED")
            return 1
        else:
            print(f"\n✅ ALL ROUTES WORKING!")
            return 0
    
    finally:
        # Always stop server
        stop_dashboard_server(server_process)

if __name__ == "__main__":
    sys.exit(main())

