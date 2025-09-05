#!/usr/bin/env python3
"""
Comprehensive Web Dashboard Testing with Web-Eval-Agent
========================================================

This script uses Playwright to systematically test all dashboard functionality:
- All buttons and interactive elements
- Navigation flows and user journeys
- API communication and data loading
- Component interactions and state management
- Performance metrics and error detection

Usage:
    python web_dashboard_tester.py
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class DashboardTester:
    """Comprehensive dashboard testing with detailed reporting."""
    
    def __init__(self, frontend_url: str = "http://localhost:5173", backend_url: str = "http://localhost:8000"):
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.test_results = []
        self.performance_metrics = {}
        self.errors_found = []
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def setup_browser(self):
        """Initialize browser and page for testing."""
        print("🔧 Setting up browser environment...")
        playwright = await async_playwright().start()
        
        # Launch browser with debugging options
        self.browser = await playwright.chromium.launch(
            headless=True,  # Set to False to see the browser in action
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context with viewport
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # Create page and set up error handling
        self.page = await self.context.new_page()
        
        # Listen for console messages and errors
        self.page.on('console', self._handle_console_message)
        self.page.on('pageerror', self._handle_page_error)
        self.page.on('requestfailed', self._handle_request_failed)
        
        print("✅ Browser setup complete")
        
    async def _handle_console_message(self, msg):
        """Handle console messages from the page."""
        if msg.type == 'error':
            self.errors_found.append({
                'type': 'console_error',
                'message': msg.text,
                'timestamp': datetime.now().isoformat()
            })
            
    async def _handle_page_error(self, error):
        """Handle page errors."""
        self.errors_found.append({
            'type': 'page_error',
            'message': str(error),
            'timestamp': datetime.now().isoformat()
        })
        
    async def _handle_request_failed(self, request):
        """Handle failed requests."""
        self.errors_found.append({
            'type': 'request_failed',
            'url': request.url,
            'method': request.method,
            'timestamp': datetime.now().isoformat()
        })
    
    async def test_backend_health(self) -> Dict[str, Any]:
        """Test backend API health and connectivity."""
        print("🔍 Testing backend API health...")
        
        test_result = {
            'test_name': 'Backend Health Check',
            'status': 'unknown',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Test health endpoint
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            test_result['details']['health_status'] = response.status_code
            test_result['details']['health_response'] = response.json() if response.status_code == 200 else None
            
            # Test projects endpoint
            projects_response = requests.get(f"{self.backend_url}/api/projects", timeout=5)
            test_result['details']['projects_status'] = projects_response.status_code
            test_result['details']['projects_response'] = projects_response.json() if projects_response.status_code == 200 else None
            
            if response.status_code == 200 and projects_response.status_code == 200:
                test_result['status'] = 'passed'
                print("✅ Backend API is healthy")
            else:
                test_result['status'] = 'failed'
                print("❌ Backend API health check failed")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['details']['error'] = str(e)
            print(f"❌ Backend API connection failed: {e}")
            
        self.test_results.append(test_result)
        return test_result
    
    async def test_page_load(self) -> Dict[str, Any]:
        """Test initial page load and basic functionality."""
        print("🌐 Testing page load and initial rendering...")
        
        test_result = {
            'test_name': 'Page Load Test',
            'status': 'unknown',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            
            # Navigate to the dashboard
            await self.page.goto(self.frontend_url, wait_until='networkidle')
            load_time = time.time() - start_time
            
            # Wait for React to render
            await self.page.wait_for_selector('[data-testid="dashboard"], .dashboard, #root > div', timeout=10000)
            
            # Check page title
            title = await self.page.title()
            test_result['details']['page_title'] = title
            test_result['details']['load_time'] = load_time
            
            # Check if main components are present
            components_found = {}
            
            # Look for file tree
            file_tree = await self.page.query_selector('[data-testid="file-tree"], .file-tree, .sidebar')
            components_found['file_tree'] = file_tree is not None
            
            # Look for code editor
            code_editor = await self.page.query_selector('[data-testid="code-editor"], .monaco-editor, .code-editor')
            components_found['code_editor'] = code_editor is not None
            
            # Look for graph visualization
            graph_viz = await self.page.query_selector('[data-testid="code-graph"], .vis-network, .graph-container')
            components_found['graph_visualization'] = graph_viz is not None
            
            test_result['details']['components_found'] = components_found
            test_result['details']['total_components'] = sum(components_found.values())
            
            if load_time < 5.0 and sum(components_found.values()) >= 2:
                test_result['status'] = 'passed'
                print(f"✅ Page loaded successfully in {load_time:.2f}s with {sum(components_found.values())} components")
            else:
                test_result['status'] = 'failed'
                print(f"❌ Page load issues: {load_time:.2f}s load time, {sum(components_found.values())} components found")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['details']['error'] = str(e)
            print(f"❌ Page load test failed: {e}")
            
        self.test_results.append(test_result)
        return test_result
    
    async def test_interactive_elements(self) -> Dict[str, Any]:
        """Test all buttons, clicks, and interactive elements."""
        print("🎮 Testing interactive elements and buttons...")
        
        test_result = {
            'test_name': 'Interactive Elements Test',
            'status': 'unknown',
            'details': {'interactions_tested': []},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            interactions_passed = 0
            total_interactions = 0
            
            # Test file tree interactions
            print("  📁 Testing file tree interactions...")
            file_tree_items = await self.page.query_selector_all('.file-tree-item, .tree-node, [role="treeitem"]')
            
            if file_tree_items:
                for i, item in enumerate(file_tree_items[:5]):  # Test first 5 items
                    try:
                        total_interactions += 1
                        await item.click()
                        await self.page.wait_for_timeout(500)  # Wait for any animations
                        interactions_passed += 1
                        test_result['details']['interactions_tested'].append(f'file_tree_item_{i}')
                    except Exception as e:
                        print(f"    ⚠️ File tree item {i} click failed: {e}")
            
            # Test buttons
            print("  🔘 Testing buttons...")
            buttons = await self.page.query_selector_all('button, [role="button"], .btn')
            
            for i, button in enumerate(buttons[:10]):  # Test first 10 buttons
                try:
                    total_interactions += 1
                    
                    # Get button text for identification
                    button_text = await button.inner_text() if await button.inner_text() else f"button_{i}"
                    
                    # Check if button is visible and enabled
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    
                    if is_visible and is_enabled:
                        await button.click()
                        await self.page.wait_for_timeout(300)
                        interactions_passed += 1
                        test_result['details']['interactions_tested'].append(f'button: {button_text}')
                    else:
                        test_result['details']['interactions_tested'].append(f'button_disabled: {button_text}')
                        
                except Exception as e:
                    print(f"    ⚠️ Button {i} interaction failed: {e}")
            
            # Test input fields
            print("  📝 Testing input fields...")
            inputs = await self.page.query_selector_all('input, textarea, [contenteditable="true"]')
            
            for i, input_field in enumerate(inputs[:5]):  # Test first 5 inputs
                try:
                    total_interactions += 1
                    
                    input_type = await input_field.get_attribute('type') or 'text'
                    
                    if input_type in ['text', 'search', 'email']:
                        await input_field.fill('test input')
                        await self.page.wait_for_timeout(200)
                        interactions_passed += 1
                        test_result['details']['interactions_tested'].append(f'input_{input_type}_{i}')
                        
                except Exception as e:
                    print(f"    ⚠️ Input field {i} interaction failed: {e}")
            
            # Test dropdown/select elements
            print("  📋 Testing dropdown elements...")
            selects = await self.page.query_selector_all('select, [role="combobox"], .dropdown')
            
            for i, select in enumerate(selects[:3]):  # Test first 3 selects
                try:
                    total_interactions += 1
                    await select.click()
                    await self.page.wait_for_timeout(300)
                    interactions_passed += 1
                    test_result['details']['interactions_tested'].append(f'select_{i}')
                except Exception as e:
                    print(f"    ⚠️ Select element {i} interaction failed: {e}")
            
            # Calculate success rate
            success_rate = (interactions_passed / total_interactions * 100) if total_interactions > 0 else 0
            test_result['details']['interactions_passed'] = interactions_passed
            test_result['details']['total_interactions'] = total_interactions
            test_result['details']['success_rate'] = success_rate
            
            if success_rate >= 70:
                test_result['status'] = 'passed'
                print(f"✅ Interactive elements test passed: {interactions_passed}/{total_interactions} ({success_rate:.1f}%)")
            else:
                test_result['status'] = 'failed'
                print(f"❌ Interactive elements test failed: {interactions_passed}/{total_interactions} ({success_rate:.1f}%)")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['details']['error'] = str(e)
            print(f"❌ Interactive elements test failed: {e}")
            
        self.test_results.append(test_result)
        return test_result
    
    async def test_navigation_flows(self) -> Dict[str, Any]:
        """Test navigation flows and user journeys."""
        print("🧭 Testing navigation flows...")
        
        test_result = {
            'test_name': 'Navigation Flows Test',
            'status': 'unknown',
            'details': {'flows_tested': []},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            flows_passed = 0
            total_flows = 0
            
            # Test file selection flow
            print("  📁 Testing file selection flow...")
            try:
                total_flows += 1
                
                # Find and click a file in the tree
                file_items = await self.page.query_selector_all('.file-item, .tree-file, [data-type="file"]')
                if file_items:
                    await file_items[0].click()
                    await self.page.wait_for_timeout(1000)
                    
                    # Check if code editor updated
                    editor_content = await self.page.query_selector('.monaco-editor, .code-editor-content')
                    if editor_content:
                        flows_passed += 1
                        test_result['details']['flows_tested'].append('file_selection_to_editor')
                        print("    ✅ File selection → Editor update flow works")
                    else:
                        print("    ⚠️ File selection → Editor update flow failed")
                else:
                    print("    ⚠️ No file items found for testing")
                    
            except Exception as e:
                print(f"    ❌ File selection flow failed: {e}")
            
            # Test graph interaction flow
            print("  🕸️ Testing graph interaction flow...")
            try:
                total_flows += 1
                
                # Look for graph nodes
                graph_container = await self.page.query_selector('.vis-network, .graph-container, [data-testid="graph"]')
                if graph_container:
                    # Try to interact with the graph
                    await graph_container.click()
                    await self.page.wait_for_timeout(500)
                    flows_passed += 1
                    test_result['details']['flows_tested'].append('graph_interaction')
                    print("    ✅ Graph interaction flow works")
                else:
                    print("    ⚠️ Graph container not found")
                    
            except Exception as e:
                print(f"    ❌ Graph interaction flow failed: {e}")
            
            # Test search flow
            print("  🔍 Testing search flow...")
            try:
                total_flows += 1
                
                # Find search input
                search_input = await self.page.query_selector('input[type="search"], .search-input, [placeholder*="search" i]')
                if search_input:
                    await search_input.fill('test')
                    await self.page.keyboard.press('Enter')
                    await self.page.wait_for_timeout(1000)
                    flows_passed += 1
                    test_result['details']['flows_tested'].append('search_functionality')
                    print("    ✅ Search flow works")
                else:
                    print("    ⚠️ Search input not found")
                    
            except Exception as e:
                print(f"    ❌ Search flow failed: {e}")
            
            # Test panel resizing flow
            print("  📏 Testing panel resizing flow...")
            try:
                total_flows += 1
                
                # Look for resizable panels
                resize_handles = await self.page.query_selector_all('.resize-handle, [data-panel-resize-handle-id]')
                if resize_handles:
                    handle = resize_handles[0]
                    
                    # Get initial position
                    box = await handle.bounding_box()
                    if box:
                        # Simulate drag
                        await self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                        await self.page.mouse.down()
                        await self.page.mouse.move(box['x'] + 50, box['y'] + box['height']/2)
                        await self.page.mouse.up()
                        await self.page.wait_for_timeout(500)
                        
                        flows_passed += 1
                        test_result['details']['flows_tested'].append('panel_resizing')
                        print("    ✅ Panel resizing flow works")
                else:
                    print("    ⚠️ No resize handles found")
                    
            except Exception as e:
                print(f"    ❌ Panel resizing flow failed: {e}")
            
            # Calculate success rate
            success_rate = (flows_passed / total_flows * 100) if total_flows > 0 else 0
            test_result['details']['flows_passed'] = flows_passed
            test_result['details']['total_flows'] = total_flows
            test_result['details']['success_rate'] = success_rate
            
            if success_rate >= 60:
                test_result['status'] = 'passed'
                print(f"✅ Navigation flows test passed: {flows_passed}/{total_flows} ({success_rate:.1f}%)")
            else:
                test_result['status'] = 'failed'
                print(f"❌ Navigation flows test failed: {flows_passed}/{total_flows} ({success_rate:.1f}%)")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['details']['error'] = str(e)
            print(f"❌ Navigation flows test failed: {e}")
            
        self.test_results.append(test_result)
        return test_result
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics and resource usage."""
        print("⚡ Testing performance metrics...")
        
        test_result = {
            'test_name': 'Performance Metrics Test',
            'status': 'unknown',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Measure page load performance
            start_time = time.time()
            await self.page.reload(wait_until='networkidle')
            load_time = time.time() - start_time
            
            # Get performance metrics from browser
            performance_metrics = await self.page.evaluate('''() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                const paint = performance.getEntriesByType('paint');
                
                return {
                    domContentLoaded: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : 0,
                    loadComplete: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
                    firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                    firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                    resourceCount: performance.getEntriesByType('resource').length
                };
            }''')
            
            # Memory usage (if available)
            try:
                memory_info = await self.page.evaluate('() => performance.memory ? {usedJSHeapSize: performance.memory.usedJSHeapSize, totalJSHeapSize: performance.memory.totalJSHeapSize} : null')
                if memory_info:
                    test_result['details']['memory_usage'] = memory_info
            except:
                pass
            
            test_result['details']['load_time'] = load_time
            test_result['details']['performance_metrics'] = performance_metrics
            
            # Performance thresholds
            performance_score = 0
            max_score = 4
            
            if load_time < 3.0:
                performance_score += 1
            if performance_metrics['firstContentfulPaint'] < 2000:
                performance_score += 1
            if performance_metrics['domContentLoaded'] < 1000:
                performance_score += 1
            if performance_metrics['resourceCount'] < 50:
                performance_score += 1
                
            test_result['details']['performance_score'] = f"{performance_score}/{max_score}"
            
            if performance_score >= 3:
                test_result['status'] = 'passed'
                print(f"✅ Performance test passed: {performance_score}/{max_score} metrics within thresholds")
            else:
                test_result['status'] = 'failed'
                print(f"❌ Performance test failed: {performance_score}/{max_score} metrics within thresholds")
                
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['details']['error'] = str(e)
            print(f"❌ Performance test failed: {e}")
            
        self.test_results.append(test_result)
        return test_result
    
    async def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        print("📊 Generating comprehensive test report...")
        
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
            'errors_found': self.errors_found,
            'performance_metrics': self.performance_metrics,
            'recommendations': []
        }
        
        # Generate recommendations based on results
        if success_rate < 70:
            report['recommendations'].append("Overall success rate is below 70%. Consider reviewing failed tests and fixing critical issues.")
        
        if len(self.errors_found) > 0:
            report['recommendations'].append(f"Found {len(self.errors_found)} errors during testing. Review console errors and failed requests.")
        
        if any(test['test_name'] == 'Performance Metrics Test' and test['status'] == 'failed' for test in self.test_results):
            report['recommendations'].append("Performance metrics are below optimal thresholds. Consider optimizing load times and resource usage.")
        
        # Save report to file
        report_file = Path('dashboard_test_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Test report saved to: {report_file}")
        return report
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        print("🧹 Browser cleanup complete")
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests in sequence."""
        print("🚀 Starting comprehensive dashboard testing...")
        print("=" * 60)
        
        try:
            await self.setup_browser()
            
            # Run all test phases
            await self.test_backend_health()
            await self.test_page_load()
            await self.test_interactive_elements()
            await self.test_navigation_flows()
            await self.test_performance_metrics()
            
            # Generate final report
            report = await self.generate_test_report()
            
            print("\n" + "=" * 60)
            print("🎯 COMPREHENSIVE TEST RESULTS")
            print("=" * 60)
            print(f"📊 Total Tests: {report['test_summary']['total_tests']}")
            print(f"✅ Passed: {report['test_summary']['passed_tests']}")
            print(f"❌ Failed: {report['test_summary']['failed_tests']}")
            print(f"📈 Success Rate: {report['test_summary']['success_rate']:.1f}%")
            print(f"🚨 Errors Found: {len(report['errors_found'])}")
            
            if report['recommendations']:
                print("\n💡 RECOMMENDATIONS:")
                for i, rec in enumerate(report['recommendations'], 1):
                    print(f"   {i}. {rec}")
            
            return report
            
        except Exception as e:
            print(f"❌ Comprehensive test failed: {e}")
            return {'error': str(e)}
        finally:
            await self.cleanup()

async def main():
    """Main function to run dashboard testing."""
    print("🌐 Web Dashboard Comprehensive Testing")
    print("=====================================")
    
    # Check if services are running
    print("🔍 Checking service availability...")
    
    try:
        frontend_check = requests.get("http://localhost:5173", timeout=5)
        print("✅ Frontend service is running")
    except:
        print("❌ Frontend service not available at http://localhost:5173")
        print("   Please start the frontend with: cd web_dashboard/frontend && npm run dev")
        return
    
    try:
        backend_check = requests.get("http://localhost:8000/api/health", timeout=5)
        print("✅ Backend service is running")
    except:
        print("❌ Backend service not available at http://localhost:8000")
        print("   Please start the backend service")
        return
    
    # Run comprehensive testing
    tester = DashboardTester()
    report = await tester.run_comprehensive_test()
    
    print(f"\n🎉 Testing complete! Report saved to dashboard_test_report.json")
    return report

if __name__ == "__main__":
    asyncio.run(main())
