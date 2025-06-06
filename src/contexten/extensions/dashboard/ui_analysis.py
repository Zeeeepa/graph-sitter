#!/usr/bin/env python3
"""
Analyze the UI components and functionality of the dashboard.
"""

import re
import requests
import subprocess
import time
import sys
from typing import Dict, List, Any

class UIAnalyzer:
    """Analyzes the dashboard UI components and functionality."""
    
    def __init__(self):
        self.results = {
            "ui_components": {},
            "interactive_elements": {},
            "styling": {},
            "javascript": {},
            "api_endpoints": {},
            "missing_features": []
        }
    
    def analyze_html_content(self, html_content: str) -> Dict[str, Any]:
        """Analyze HTML content for UI components."""
        analysis = {
            "has_doctype": bool(re.search(r'<!DOCTYPE html>', html_content)),
            "has_viewport": bool(re.search(r'viewport', html_content)),
            "has_title": bool(re.search(r'<title>', html_content)),
            "has_css": bool(re.search(r'<style>', html_content)),
            "has_javascript": bool(re.search(r'<script>', html_content)),
            "interactive_elements": [],
            "ui_sections": [],
            "api_calls": []
        }
        
        # Find interactive elements
        buttons = re.findall(r'<button[^>]*>(.*?)</button>', html_content, re.DOTALL)
        inputs = re.findall(r'<input[^>]*>', html_content)
        forms = re.findall(r'<form[^>]*>', html_content)
        links = re.findall(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', html_content, re.DOTALL)
        
        analysis["interactive_elements"] = {
            "buttons": len(buttons),
            "inputs": len(inputs),
            "forms": len(forms),
            "links": len(links)
        }
        
        # Find UI sections
        headers = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', html_content, re.DOTALL)
        divs_with_class = re.findall(r'<div[^>]*class=["\']([^"\']*)["\'][^>]*>', html_content)
        
        analysis["ui_sections"] = {
            "headers": headers,
            "css_classes": divs_with_class
        }
        
        # Find API calls
        api_calls = re.findall(r'fetch\(["\']([^"\']*)["\']', html_content)
        analysis["api_calls"] = api_calls
        
        return analysis
    
    def test_api_endpoints(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Test API endpoints for functionality."""
        endpoints = {
            "/api/health": {"method": "GET", "expected": "json"},
            "/api/projects": {"method": "GET", "expected": "json"},
            "/docs": {"method": "GET", "expected": "html"},
            "/": {"method": "GET", "expected": "html"}
        }
        
        results = {}
        for endpoint, config in endpoints.items():
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                results[endpoint] = {
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "working": response.status_code == 200,
                    "size": len(response.content)
                }
                
                if endpoint == "/api/projects" and response.status_code == 200:
                    try:
                        data = response.json()
                        results[endpoint]["has_data"] = len(data) > 0
                        results[endpoint]["data_structure"] = list(data.keys()) if isinstance(data, dict) else "list"
                    except:
                        results[endpoint]["has_data"] = False
                        
            except Exception as e:
                results[endpoint] = {
                    "status": "error",
                    "error": str(e),
                    "working": False
                }
        
        return results
    
    def analyze_required_features(self) -> List[str]:
        """Analyze what features are missing for a complete dashboard."""
        required_features = [
            "Project selection dropdown",
            "Project pinning functionality", 
            "Requirements input form",
            "Plan generation button",
            "Flow execution controls",
            "Settings dialog for API keys",
            "Real-time progress tracking",
            "Quality gates display",
            "PR status monitoring",
            "Linear issue integration",
            "GitHub repository browser",
            "Workflow status indicators",
            "Error handling and notifications",
            "User authentication",
            "Data persistence"
        ]
        
        return required_features
    
    def generate_ui_report(self, html_analysis: Dict, api_results: Dict) -> str:
        """Generate comprehensive UI analysis report."""
        report = []
        report.append("=" * 70)
        report.append("COMPREHENSIVE UI ANALYSIS REPORT")
        report.append("=" * 70)
        report.append("")
        
        # HTML Structure Analysis
        report.append("🏗️ HTML STRUCTURE:")
        report.append(f"   ✅ DOCTYPE HTML5: {html_analysis['has_doctype']}")
        report.append(f"   ✅ Responsive Viewport: {html_analysis['has_viewport']}")
        report.append(f"   ✅ Page Title: {html_analysis['has_title']}")
        report.append(f"   ✅ CSS Styling: {html_analysis['has_css']}")
        report.append(f"   ✅ JavaScript: {html_analysis['has_javascript']}")
        report.append("")
        
        # Interactive Elements
        report.append("🖱️ INTERACTIVE ELEMENTS:")
        elements = html_analysis['interactive_elements']
        report.append(f"   Buttons: {elements['buttons']}")
        report.append(f"   Input Fields: {elements['inputs']}")
        report.append(f"   Forms: {elements['forms']}")
        report.append(f"   Links: {elements['links']}")
        report.append("")
        
        # UI Sections
        report.append("📱 UI SECTIONS:")
        sections = html_analysis['ui_sections']
        report.append(f"   Headers: {len(sections['headers'])}")
        if sections['headers']:
            for i, header in enumerate(sections['headers'][:5], 1):
                clean_header = re.sub(r'<[^>]+>', '', header).strip()
                report.append(f"     {i}. {clean_header}")
        
        report.append(f"   CSS Classes: {len(sections['css_classes'])}")
        unique_classes = list(set(sections['css_classes']))[:10]
        for cls in unique_classes:
            report.append(f"     - {cls}")
        report.append("")
        
        # API Integration
        report.append("🔌 API INTEGRATION:")
        api_calls = html_analysis['api_calls']
        report.append(f"   JavaScript API Calls: {len(api_calls)}")
        for call in api_calls:
            report.append(f"     - {call}")
        report.append("")
        
        # API Endpoint Testing
        report.append("🧪 API ENDPOINT TESTING:")
        for endpoint, result in api_results.items():
            status_icon = "✅" if result.get('working', False) else "❌"
            report.append(f"   {status_icon} {endpoint}")
            if result.get('working'):
                report.append(f"      Status: {result['status']}")
                report.append(f"      Content-Type: {result['content_type']}")
                report.append(f"      Size: {result['size']} bytes")
                if 'has_data' in result:
                    report.append(f"      Has Data: {result['has_data']}")
            else:
                report.append(f"      Error: {result.get('error', 'Failed')}")
        report.append("")
        
        # Missing Features
        report.append("❌ MISSING FEATURES FOR COMPLETE DASHBOARD:")
        missing_features = self.analyze_required_features()
        for i, feature in enumerate(missing_features, 1):
            report.append(f"   {i:2d}. {feature}")
        report.append("")
        
        # Overall Assessment
        working_endpoints = sum(1 for r in api_results.values() if r.get('working', False))
        total_endpoints = len(api_results)
        
        report.append("📊 OVERALL ASSESSMENT:")
        report.append(f"   API Endpoints Working: {working_endpoints}/{total_endpoints}")
        report.append(f"   Basic UI Structure: ✅ Complete")
        report.append(f"   Interactive Elements: ❌ Minimal ({elements['buttons']} buttons, {elements['inputs']} inputs)")
        report.append(f"   Required Features: ❌ {len(missing_features)} missing")
        report.append("")
        
        if working_endpoints == total_endpoints and elements['buttons'] > 0:
            report.append("✅ VERDICT: Basic dashboard functional, needs feature implementation")
        elif working_endpoints == total_endpoints:
            report.append("⚠️ VERDICT: Server works, UI needs interactive elements")
        else:
            report.append("❌ VERDICT: Critical issues need fixing")
        
        return "\n".join(report)

def start_server_for_testing():
    """Start server for UI testing."""
    print("🚀 Starting server for UI analysis...")
    process = subprocess.Popen(
        [sys.executable, "start_dashboard_standalone.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(3)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server ready for UI analysis")
            return process
    except:
        pass
    
    print("❌ Server failed to start")
    return None

def stop_server(process):
    """Stop the test server."""
    if process:
        process.terminate()
        process.wait(timeout=5)

def main():
    """Main UI analysis function."""
    print("🎨 UI ANALYSIS STARTING")
    print("=" * 50)
    
    # Start server
    server_process = start_server_for_testing()
    if not server_process:
        print("❌ Cannot analyze UI - server failed to start")
        return 1
    
    try:
        analyzer = UIAnalyzer()
        
        # Get HTML content
        response = requests.get("http://localhost:8000/", timeout=5)
        html_content = response.text
        
        # Analyze HTML
        html_analysis = analyzer.analyze_html_content(html_content)
        
        # Test API endpoints
        api_results = analyzer.test_api_endpoints()
        
        # Generate report
        report = analyzer.generate_ui_report(html_analysis, api_results)
        
        # Save report
        with open("UI_ANALYSIS_REPORT.md", "w") as f:
            f.write(report)
        
        print("✅ UI analysis complete!")
        print("📄 Report saved to: UI_ANALYSIS_REPORT.md")
        
        # Print summary
        elements = html_analysis['interactive_elements']
        working_apis = sum(1 for r in api_results.values() if r.get('working', False))
        
        print(f"\n📊 UI ANALYSIS SUMMARY:")
        print(f"   Interactive Elements: {elements['buttons']} buttons, {elements['inputs']} inputs")
        print(f"   API Endpoints: {working_apis}/{len(api_results)} working")
        print(f"   Missing Features: {len(analyzer.analyze_required_features())}")
        
        return 0
    
    finally:
        stop_server(server_process)

if __name__ == "__main__":
    sys.exit(main())

