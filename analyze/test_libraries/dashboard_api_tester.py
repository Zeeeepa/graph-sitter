#!/usr/bin/env python3
"""
Dashboard API and Frontend Testing
==================================

Alternative testing approach using requests and HTML parsing
to test dashboard functionality without browser dependencies.
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import re

class DashboardAPITester:
    """Test dashboard functionality via API calls and HTML parsing."""
    
    def __init__(self, frontend_url: str = "http://localhost:5173", backend_url: str = "http://localhost:8000"):
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.test_results = []
        self.session = requests.Session()
        
    def test_backend_api(self) -> Dict[str, Any]:
        """Test all backend API endpoints."""
        print("🔍 Testing backend API endpoints...")
        
        test_result = {
            'test_name': 'Backend API Test',
            'status': 'unknown',
            'details': {'endpoints_tested': []},
            'timestamp': datetime.now().isoformat()
        }
        
        endpoints_passed = 0
        total_endpoints = 0
        
        # Test health endpoint
        try:
            total_endpoints += 1
            response = self.session.get(f"{self.backend_url}/api/health", timeout=5)
            if response.status_code == 200:
                endpoints_passed += 1
                test_result['details']['endpoints_tested'].append({
                    'endpoint': '/api/health',
                    'status': 'passed',
                    'response': response.json()
                })
                print("  ✅ /api/health - OK")
            else:
                test_result['details']['endpoints_tested'].append({
                    'endpoint': '/api/health',
                    'status': 'failed',
                    'status_code': response.status_code
                })
                print(f"  ❌ /api/health - Failed ({response.status_code})")
        except Exception as e:
            test_result['details']['endpoints_tested'].append({
                'endpoint': '/api/health',
                'status': 'error',
                'error': str(e)
            })
            print(f"  ❌ /api/health - Error: {e}")
        
        # Test projects endpoint
        try:
            total_endpoints += 1
            response = self.session.get(f"{self.backend_url}/api/projects", timeout=5)
            if response.status_code == 200:
                endpoints_passed += 1
                test_result['details']['endpoints_tested'].append({
                    'endpoint': '/api/projects',
                    'status': 'passed',
                    'response': response.json()
                })
                print("  ✅ /api/projects - OK")
            else:
                test_result['details']['endpoints_tested'].append({
                    'endpoint': '/api/projects',
                    'status': 'failed',
                    'status_code': response.status_code
                })
                print(f"  ❌ /api/projects - Failed ({response.status_code})")
        except Exception as e:
            test_result['details']['endpoints_tested'].append({
                'endpoint': '/api/projects',
                'status': 'error',
                'error': str(e)
            })
            print(f"  ❌ /api/projects - Error: {e}")
        
        # Calculate success rate
        success_rate = (endpoints_passed / total_endpoints * 100) if total_endpoints > 0 else 0
        test_result['details']['endpoints_passed'] = endpoints_passed
        test_result['details']['total_endpoints'] = total_endpoints
        test_result['details']['success_rate'] = success_rate
        
        if success_rate >= 80:
            test_result['status'] = 'passed'
        else:
            test_result['status'] = 'failed'
            
        self.test_results.append(test_result)
        return test_result
    
    def test_frontend_structure(self) -> Dict[str, Any]:
        """Test frontend HTML structure and components."""
        print("🌐 Testing frontend structure...")
        
        test_result = {
            'test_name': 'Frontend Structure Test',
            'status': 'unknown',
            'details': {'components_found': {}},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            response = self.session.get(self.frontend_url, timeout=10)
            load_time = time.time() - start_time
            
            test_result['details']['load_time'] = load_time
            test_result['details']['status_code'] = response.status_code
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check page title
                title = soup.find('title')
                test_result['details']['page_title'] = title.text if title else 'No title found'
                
                # Check for React root
                root_div = soup.find('div', {'id': 'root'})
                test_result['details']['components_found']['react_root'] = root_div is not None
                
                # Check for Vite development indicators
                vite_scripts = soup.find_all('script', src=re.compile(r'/@vite/'))
                test_result['details']['components_found']['vite_dev_mode'] = len(vite_scripts) > 0
                
                # Check for CSS imports
                css_links = soup.find_all('link', {'rel': 'stylesheet'})
                test_result['details']['components_found']['css_loaded'] = len(css_links) > 0
                
                # Check for JavaScript modules
                js_modules = soup.find_all('script', {'type': 'module'})
                test_result['details']['components_found']['js_modules'] = len(js_modules) > 0
                
                # Count total components found
                components_found = sum(test_result['details']['components_found'].values())
                test_result['details']['total_components'] = components_found
                
                if load_time < 5.0 and components_found >= 3:
                    test_result['status'] = 'passed'
                    print(f"  ✅ Frontend loaded in {load_time:.2f}s with {components_found} components")
                else:
                    test_result['status'] = 'failed'
                    print(f"  ❌ Frontend issues: {load_time:.2f}s load time, {components_found} components")
            else:
                test_result['status'] = 'failed'
                print(f"  ❌ Frontend returned status code: {response.status_code}")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['details']['error'] = str(e)
            print(f"  ❌ Frontend test failed: {e}")
            
        self.test_results.append(test_result)
        return test_result
    
    def test_static_assets(self) -> Dict[str, Any]:
        """Test static assets and resources."""
        print("📦 Testing static assets...")
        
        test_result = {
            'test_name': 'Static Assets Test',
            'status': 'unknown',
            'details': {'assets_tested': []},
            'timestamp': datetime.now().isoformat()
        }
        
        assets_passed = 0
        total_assets = 0
        
        # Common static assets to test
        assets_to_test = [
            '/vite.svg',
            '/@vite/client',
            '/src/main.tsx',
            '/src/App.tsx'
        ]
        
        for asset in assets_to_test:
            try:
                total_assets += 1
                url = f"{self.frontend_url}{asset}"
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    assets_passed += 1
                    test_result['details']['assets_tested'].append({
                        'asset': asset,
                        'status': 'passed',
                        'size': len(response.content)
                    })
                    print(f"  ✅ {asset} - OK ({len(response.content)} bytes)")
                else:
                    test_result['details']['assets_tested'].append({
                        'asset': asset,
                        'status': 'failed',
                        'status_code': response.status_code
                    })
                    print(f"  ⚠️ {asset} - Status {response.status_code}")
                    
            except Exception as e:
                test_result['details']['assets_tested'].append({
                    'asset': asset,
                    'status': 'error',
                    'error': str(e)
                })
                print(f"  ❌ {asset} - Error: {e}")
        
        # Calculate success rate
        success_rate = (assets_passed / total_assets * 100) if total_assets > 0 else 0
        test_result['details']['assets_passed'] = assets_passed
        test_result['details']['total_assets'] = total_assets
        test_result['details']['success_rate'] = success_rate
        
        if success_rate >= 50:  # Lower threshold since some assets might not be accessible
            test_result['status'] = 'passed'
        else:
            test_result['status'] = 'failed'
            
        self.test_results.append(test_result)
        return test_result
    
    def test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS configuration between frontend and backend."""
        print("🔗 Testing CORS configuration...")
        
        test_result = {
            'test_name': 'CORS Configuration Test',
            'status': 'unknown',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Test preflight request
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{self.backend_url}/api/health", headers=headers, timeout=5)
            
            test_result['details']['preflight_status'] = response.status_code
            test_result['details']['cors_headers'] = dict(response.headers)
            
            # Check for required CORS headers
            cors_headers_present = {
                'access-control-allow-origin': 'Access-Control-Allow-Origin' in response.headers,
                'access-control-allow-methods': 'Access-Control-Allow-Methods' in response.headers,
                'access-control-allow-headers': 'Access-Control-Allow-Headers' in response.headers
            }
            
            test_result['details']['cors_headers_present'] = cors_headers_present
            
            # Test actual request with Origin header
            actual_response = self.session.get(
                f"{self.backend_url}/api/health",
                headers={'Origin': self.frontend_url},
                timeout=5
            )
            
            test_result['details']['actual_request_status'] = actual_response.status_code
            
            cors_score = sum(cors_headers_present.values())
            if cors_score >= 2 and actual_response.status_code == 200:
                test_result['status'] = 'passed'
                print(f"  ✅ CORS configured correctly ({cors_score}/3 headers present)")
            else:
                test_result['status'] = 'failed'
                print(f"  ❌ CORS issues detected ({cors_score}/3 headers present)")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['details']['error'] = str(e)
            print(f"  ❌ CORS test failed: {e}")
            
        self.test_results.append(test_result)
        return test_result
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        print("📊 Generating test report...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test['status'] == 'passed')
        failed_tests = sum(1 for test in self.test_results if test['status'] == 'failed')
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results,
            'recommendations': []
        }
        
        # Generate recommendations
        if success_rate < 70:
            report['recommendations'].append("Overall success rate is below 70%. Review failed tests and address critical issues.")
        
        backend_test = next((test for test in self.test_results if test['test_name'] == 'Backend API Test'), None)
        if backend_test and backend_test['status'] == 'failed':
            report['recommendations'].append("Backend API tests failed. Ensure all endpoints are working correctly.")
        
        frontend_test = next((test for test in self.test_results if test['test_name'] == 'Frontend Structure Test'), None)
        if frontend_test and frontend_test['status'] == 'failed':
            report['recommendations'].append("Frontend structure issues detected. Check React app initialization and component loading.")
        
        cors_test = next((test for test in self.test_results if test['test_name'] == 'CORS Configuration Test'), None)
        if cors_test and cors_test['status'] == 'failed':
            report['recommendations'].append("CORS configuration issues detected. Ensure proper cross-origin headers are set.")
        
        # Save report
        report_file = Path('dashboard_api_test_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Test report saved to: {report_file}")
        return report
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all API and frontend tests."""
        print("🚀 Starting comprehensive API and frontend testing...")
        print("=" * 60)
        
        try:
            # Run all test phases
            self.test_backend_api()
            self.test_frontend_structure()
            self.test_static_assets()
            self.test_cors_configuration()
            
            # Generate final report
            report = self.generate_test_report()
            
            print("\n" + "=" * 60)
            print("🎯 COMPREHENSIVE TEST RESULTS")
            print("=" * 60)
            print(f"📊 Total Tests: {report['test_summary']['total_tests']}")
            print(f"✅ Passed: {report['test_summary']['passed_tests']}")
            print(f"❌ Failed: {report['test_summary']['failed_tests']}")
            print(f"📈 Success Rate: {report['test_summary']['success_rate']:.1f}%")
            
            if report['recommendations']:
                print("\n💡 RECOMMENDATIONS:")
                for i, rec in enumerate(report['recommendations'], 1):
                    print(f"   {i}. {rec}")
            
            return report
            
        except Exception as e:
            print(f"❌ Comprehensive test failed: {e}")
            return {'error': str(e)}

def main():
    """Main function to run API testing."""
    print("🌐 Dashboard API & Frontend Testing")
    print("==================================")
    
    # Check if services are running
    print("🔍 Checking service availability...")
    
    try:
        frontend_check = requests.get("http://localhost:5173", timeout=5)
        print("✅ Frontend service is running")
    except:
        print("❌ Frontend service not available at http://localhost:5173")
        return
    
    try:
        backend_check = requests.get("http://localhost:8000/api/health", timeout=5)
        print("✅ Backend service is running")
    except:
        print("❌ Backend service not available at http://localhost:8000")
        return
    
    # Run comprehensive testing
    tester = DashboardAPITester()
    report = tester.run_comprehensive_test()
    
    print(f"\n🎉 Testing complete! Report saved to dashboard_api_test_report.json")
    return report

if __name__ == "__main__":
    main()

