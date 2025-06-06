#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE VISUALIZATION MODULE TESTS 🧪

Test script to validate all visualization modules are working correctly.
This tests the fixes for the broken imports and validates functionality.
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test that all imports work correctly."""
    print("🔍 Testing imports...")
    
    try:
        # Test main module imports
        import src.graph_sitter.adapters.analysis.visualization as viz_module
        print("✅ Main visualization module imports successful")
        
        # Test specific module imports
        from src.graph_sitter.adapters.analysis.visualization.dashboards import (
            MetricsDashboard, QualityDashboard, PerformanceDashboard, 
            create_comprehensive_dashboard, MetricData, DashboardConfig
        )
        print("✅ Dashboard module imports successful")
        
        from src.graph_sitter.adapters.analysis.visualization.dependency_graphs import (
            DependencyGraphGenerator, create_dependency_graph, 
            visualize_call_graph, visualize_import_graph,
            GraphNode, GraphEdge, GraphConfig
        )
        print("✅ Dependency graphs module imports successful")
        
        from src.graph_sitter.adapters.analysis.visualization.exporters import (
            ReportExporter, export_to_html, export_to_pdf, 
            export_to_json, export_to_svg, ExportConfig, ExportResult
        )
        print("✅ Exporters module imports successful")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False

def test_dashboard_functionality():
    """Test dashboard creation and HTML generation."""
    print("\n📊 Testing dashboard functionality...")
    
    try:
        from src.graph_sitter.adapters.analysis.visualization.dashboards import (
            MetricsDashboard, QualityDashboard, PerformanceDashboard, 
            MetricData, create_comprehensive_dashboard
        )
        
        # Test MetricsDashboard
        dashboard = MetricsDashboard()
        dashboard.add_metric(MetricData(
            name="Lines of Code",
            value=15000,
            unit="lines",
            trend=5.2,
            status="normal",
            description="Total lines of code in the project"
        ))
        
        dashboard.add_metric(MetricData(
            name="Test Coverage",
            value=85.5,
            unit="%",
            trend=-2.1,
            status="warning",
            description="Percentage of code covered by tests"
        ))
        
        html = dashboard.generate_html()
        assert len(html) > 1000, "Dashboard HTML should be substantial"
        assert "Lines of Code" in html, "Metric should appear in HTML"
        print("✅ MetricsDashboard working correctly")
        
        # Test QualityDashboard
        quality_dashboard = QualityDashboard()
        quality_dashboard.add_quality_score("maintainability", 85.0)
        quality_dashboard.add_quality_score("complexity", 72.5)
        quality_dashboard.add_quality_issue({
            'file': 'test.py',
            'line': 42,
            'severity': 'warning',
            'message': 'Unused variable',
            'rule': 'unused-variable'
        })
        
        quality_html = quality_dashboard.generate_html()
        assert len(quality_html) > 500, "Quality dashboard HTML should be substantial"
        print("✅ QualityDashboard working correctly")
        
        # Test comprehensive dashboard
        metrics_data = {
            'total_lines': 15000,
            'complexity': {'average': 7.2},
            'test_coverage': 85.5,
            'technical_debt': {'hours': 45}
        }
        
        quality_data = {
            'scores': {'maintainability': 85.0, 'complexity': 72.5},
            'issues': [
                {'file': 'test.py', 'line': 42, 'severity': 'warning', 'message': 'Unused variable', 'rule': 'unused-variable'}
            ]
        }
        
        comprehensive_html = create_comprehensive_dashboard(
            metrics_data=metrics_data,
            quality_data=quality_data
        )
        assert len(comprehensive_html) > 2000, "Comprehensive dashboard should be substantial"
        assert "<!DOCTYPE html>" in comprehensive_html, "Should be valid HTML"
        print("✅ Comprehensive dashboard working correctly")
        
        return True
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        traceback.print_exc()
        return False

def test_dependency_graph_functionality():
    """Test dependency graph creation and analysis."""
    print("\n🕸️ Testing dependency graph functionality...")
    
    try:
        from src.graph_sitter.adapters.analysis.visualization.dependency_graphs import (
            DependencyGraphGenerator, create_dependency_graph, 
            visualize_call_graph, visualize_import_graph
        )
        
        # Test basic dependency graph
        dependencies = {
            'module_a.py': ['module_b.py', 'module_c.py'],
            'module_b.py': ['module_c.py', 'module_d.py'],
            'module_c.py': ['module_d.py'],
            'module_d.py': ['module_a.py']  # Creates circular dependency
        }
        
        graph = create_dependency_graph(dependencies)
        metrics = graph.calculate_metrics()
        
        assert metrics['node_count'] == 4, f"Expected 4 nodes, got {metrics['node_count']}"
        assert metrics['edge_count'] == 6, f"Expected 6 edges, got {metrics['edge_count']}"
        assert metrics['circular_dependencies'] >= 1, "Should detect circular dependencies"
        
        # Test circular dependency detection
        circular_deps = graph.detect_circular_dependencies()
        assert len(circular_deps) >= 1, "Should detect at least one circular dependency"
        print("✅ Circular dependency detection working")
        
        # Test JSON export
        graph_data = graph.export_to_json()
        assert 'nodes' in graph_data, "Export should contain nodes"
        assert 'edges' in graph_data, "Export should contain edges"
        assert 'metrics' in graph_data, "Export should contain metrics"
        print("✅ Graph JSON export working")
        
        # Test call graph visualization
        call_data = {
            'main.process_data': {'utils.validate': 5, 'utils.transform': 3},
            'utils.validate': {'utils.check_type': 2},
            'utils.transform': {'utils.normalize': 4}
        }
        
        call_html = visualize_call_graph(call_data)
        assert len(call_html) > 1000, "Call graph HTML should be substantial"
        assert "d3.v7.min.js" in call_html, "Should use D3.js for visualization"
        print("✅ Call graph visualization working")
        
        # Test import graph visualization
        import_html = visualize_import_graph(dependencies)
        assert len(import_html) > 1000, "Import graph HTML should be substantial"
        assert "Circular Dependencies" in import_html, "Should show circular dependencies"
        print("✅ Import graph visualization working")
        
        return True
    except Exception as e:
        print(f"❌ Dependency graph test failed: {e}")
        traceback.print_exc()
        return False

def test_exporter_functionality():
    """Test export functionality for different formats."""
    print("\n📤 Testing exporter functionality...")
    
    try:
        from src.graph_sitter.adapters.analysis.visualization.exporters import (
            ReportExporter, export_to_html, export_to_json, 
            export_multiple_formats, ExportConfig
        )
        import tempfile
        
        # Test data
        test_data = {
            'title': 'Test Analysis Report',
            'metrics': {
                'total_files': 150,
                'total_lines': 15000,
                'test_coverage': 85.5,
                'complexity_score': 7.2
            },
            'issues': [
                {'file': 'test.py', 'line': 42, 'severity': 'warning', 'message': 'Unused variable'},
                {'file': 'main.py', 'line': 15, 'severity': 'error', 'message': 'Syntax error'}
            ],
            'dependencies': ['module_a', 'module_b', 'module_c']
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test HTML export
            html_path = temp_path / 'test_report.html'
            html_result = export_to_html(test_data, html_path)
            
            assert html_result.success, f"HTML export failed: {html_result.error_message}"
            assert html_result.file_size > 1000, "HTML file should be substantial"
            assert html_path.exists(), "HTML file should exist"
            print("✅ HTML export working")
            
            # Test JSON export
            json_path = temp_path / 'test_report.json'
            json_result = export_to_json(test_data, json_path)
            
            assert json_result.success, f"JSON export failed: {json_result.error_message}"
            assert json_result.file_size > 100, "JSON file should contain data"
            assert json_path.exists(), "JSON file should exist"
            print("✅ JSON export working")
            
            # Test multiple format export
            formats = ['html', 'json', 'csv', 'markdown']
            results = export_multiple_formats(test_data, temp_path, formats, 'multi_test')
            
            for format_name, result in results.items():
                assert result.success, f"{format_name} export failed: {result.error_message}"
                expected_file = temp_path / f'multi_test.{format_name}'
                assert expected_file.exists(), f"{format_name} file should exist"
            
            print("✅ Multiple format export working")
            
            # Test ReportExporter with custom config
            config = ExportConfig(
                format="html",
                include_metadata=True,
                include_timestamp=True,
                custom_css="body { background: #f0f0f0; }"
            )
            
            exporter = ReportExporter(config)
            custom_path = temp_path / 'custom_report.html'
            custom_result = exporter.export(test_data, custom_path)
            
            assert custom_result.success, "Custom export should succeed"
            assert custom_path.exists(), "Custom file should exist"
            
            # Check that metadata was included
            with open(custom_path, 'r') as f:
                content = f.read()
                assert "_export_metadata" in str(test_data) or "Generated on:" in content, "Should include metadata"
            
            print("✅ Custom export configuration working")
        
        return True
    except Exception as e:
        print(f"❌ Exporter test failed: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """Test integration between all modules."""
    print("\n🔗 Testing module integration...")
    
    try:
        from src.graph_sitter.adapters.analysis.visualization import (
            MetricsDashboard, DependencyGraphGenerator, ReportExporter,
            create_comprehensive_dashboard, create_dependency_graph, export_to_html
        )
        import tempfile
        
        # Create integrated analysis data
        analysis_data = {
            'title': 'Integrated Analysis Report',
            'timestamp': '2024-06-06T08:00:00',
            'project': 'graph-sitter-analysis'
        }
        
        # Create metrics dashboard
        dashboard = MetricsDashboard()
        dashboard.add_code_quality_metrics({
            'total_lines': 25000,
            'complexity': {'average': 8.5},
            'test_coverage': 78.2,
            'technical_debt': {'hours': 67}
        })
        
        # Create dependency graph
        dependencies = {
            'core/engine.py': ['utils/helpers.py', 'config/settings.py'],
            'utils/helpers.py': ['config/settings.py'],
            'visualization/dashboards.py': ['core/engine.py'],
            'config/settings.py': []
        }
        
        dep_graph = create_dependency_graph(dependencies)
        
        # Combine data
        integrated_data = {
            **analysis_data,
            'dashboard_html': dashboard.generate_html(),
            'dependency_metrics': dep_graph.calculate_metrics(),
            'dependency_graph': dep_graph.export_to_json()
        }
        
        # Export integrated report
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / 'integrated_report.html'
            result = export_to_html(integrated_data, report_path)
            
            assert result.success, "Integrated export should succeed"
            assert result.file_size > 2000, "Integrated report should be substantial"
            
            # Verify content
            with open(report_path, 'r') as f:
                content = f.read()
                assert 'Integrated Analysis Report' in content, "Should contain title"
                assert 'dashboard' in content.lower(), "Should contain dashboard content"
                assert 'dependency' in content.lower(), "Should contain dependency content"
        
        print("✅ Module integration working correctly")
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 STARTING COMPREHENSIVE VISUALIZATION MODULE TESTS\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Dashboard Functionality", test_dashboard_functionality),
        ("Dependency Graph Functionality", test_dependency_graph_functionality),
        ("Exporter Functionality", test_exporter_functionality),
        ("Integration Tests", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING: {test_name}")
        print('='*60)
        
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Visualization modules are working correctly!")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
