"""
Tests for comprehensive codebase analysis functions.
"""

import pytest
from unittest.mock import Mock, MagicMock
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.file import SourceFile
from graph_sitter.enums import SymbolType, EdgeType
from graph_sitter.codebase.codebase_analysis import (
    identify_entry_points,
    detect_dead_code,
    detect_unused_parameters,
    analyze_imports,
    analyze_call_sites,
    comprehensive_analysis
)


@pytest.fixture
def mock_codebase():
    """Create a mock codebase for testing."""
    codebase = Mock(spec=Codebase)
    
    # Mock functions
    main_func = Mock(spec=Function)
    main_func.name = 'main'
    main_func.decorators = []
    
    helper_func = Mock(spec=Function)
    helper_func.name = 'helper_function'
    helper_func.decorators = []
    
    codebase.functions = [main_func, helper_func]
    
    # Mock classes
    main_class = Mock(spec=Class)
    main_class.name = 'MainClass'
    main_class.parent_class_names = []
    
    child_class = Mock(spec=Class)
    child_class.name = 'ChildClass'
    child_class.parent_class_names = ['MainClass']
    
    codebase.classes = [main_class, child_class]
    
    # Mock symbols
    codebase.symbols = [main_func, helper_func, main_class, child_class]
    
    # Mock files
    main_file = Mock(spec=SourceFile)
    main_file.name = 'main.py'
    main_file.imports = []
    main_file.symbols = [main_func, main_class]
    
    codebase.files = [main_file]
    codebase.imports = []
    codebase.external_modules = []
    
    # Mock context
    codebase.ctx = Mock()
    codebase.ctx.out_edges = Mock(return_value=[])
    
    return codebase


def test_identify_entry_points(mock_codebase):
    """Test entry point identification."""
    entry_points = identify_entry_points(mock_codebase)
    
    assert 'main_functions' in entry_points
    assert 'cli_commands' in entry_points
    assert 'exported_symbols' in entry_points
    assert 'top_level_classes' in entry_points
    assert 'web_routes' in entry_points
    assert 'decorated_functions' in entry_points
    
    # Should find the main function
    assert len(entry_points['main_functions']) == 1
    assert entry_points['main_functions'][0].name == 'main'
    
    # Should find top-level classes (not inherited by others)
    assert len(entry_points['top_level_classes']) == 1
    assert entry_points['top_level_classes'][0].name == 'ChildClass'


def test_detect_dead_code(mock_codebase):
    """Test dead code detection."""
    # Mock dependencies method
    for symbol in mock_codebase.symbols:
        symbol.dependencies = Mock(return_value=[])
    
    dead_code = detect_dead_code(mock_codebase)
    
    assert 'dead_functions' in dead_code
    assert 'dead_classes' in dead_code
    assert 'dead_variables' in dead_code
    assert 'potentially_dead' in dead_code
    
    # Results should be lists
    assert isinstance(dead_code['dead_functions'], list)
    assert isinstance(dead_code['dead_classes'], list)


def test_detect_unused_parameters(mock_codebase):
    """Test unused parameter detection."""
    # Mock function with parameters
    func_with_params = Mock(spec=Function)
    func_with_params.name = 'test_function'
    
    # Mock parameter
    param = Mock()
    param.name = 'unused_param'
    func_with_params.parameters = [param]
    func_with_params.source = 'def test_function(unused_param): pass'
    
    mock_codebase.functions = [func_with_params]
    
    unused_params = detect_unused_parameters(mock_codebase)
    
    # Should be a dictionary mapping functions to unused parameters
    assert isinstance(unused_params, dict)


def test_analyze_imports(mock_codebase):
    """Test import analysis."""
    import_analysis = analyze_imports(mock_codebase)
    
    assert 'unused_imports' in import_analysis
    assert 'circular_imports' in import_analysis
    assert 'unresolved_imports' in import_analysis
    assert 'import_statistics' in import_analysis
    
    # Should have statistics
    stats = import_analysis['import_statistics']
    assert 'total_imports' in stats
    assert 'total_files' in stats
    assert 'unused_count' in stats
    assert 'circular_count' in stats
    assert 'unresolved_count' in stats


def test_analyze_call_sites(mock_codebase):
    """Test call site analysis."""
    call_analysis = analyze_call_sites(mock_codebase)
    
    assert 'argument_mismatches' in call_analysis
    assert 'undefined_calls' in call_analysis
    assert 'call_statistics' in call_analysis
    
    # Should have statistics
    stats = call_analysis['call_statistics']
    assert 'total_calls' in stats
    assert 'resolved_calls' in stats
    assert 'unresolved_calls' in stats
    assert 'resolution_rate' in stats


def test_comprehensive_analysis(mock_codebase, capsys):
    """Test comprehensive analysis function."""
    # Mock all the individual analysis functions to avoid complex setup
    results = comprehensive_analysis(mock_codebase)
    
    # Check that all expected sections are present
    expected_sections = [
        'codebase_summary',
        'entry_points',
        'dead_code',
        'unused_parameters',
        'import_analysis',
        'call_site_analysis',
        'symbol_statistics',
        'recommendations'
    ]
    
    for section in expected_sections:
        assert section in results
    
    # Check codebase summary structure
    summary = results['codebase_summary']
    assert 'total_files' in summary
    assert 'total_functions' in summary
    assert 'total_classes' in summary
    assert 'total_symbols' in summary
    assert 'total_imports' in summary
    assert 'total_external_modules' in summary
    
    # Check that recommendations is a list
    assert isinstance(results['recommendations'], list)
    
    # Check that progress messages were printed
    captured = capsys.readouterr()
    assert "🔍 Starting comprehensive codebase analysis..." in captured.out
    assert "✅ Comprehensive analysis complete!" in captured.out


def test_entry_point_detection_with_decorators():
    """Test entry point detection with decorated functions."""
    codebase = Mock(spec=Codebase)
    
    # Mock function with CLI decorator
    cli_func = Mock(spec=Function)
    cli_func.name = 'cli_command'
    
    # Mock decorator
    decorator = Mock()
    decorator.name = 'click.command'
    cli_func.decorators = [decorator]
    
    # Mock function with web decorator
    web_func = Mock(spec=Function)
    web_func.name = 'api_endpoint'
    
    web_decorator = Mock()
    web_decorator.name = 'app.route'
    web_func.decorators = [web_decorator]
    
    codebase.functions = [cli_func, web_func]
    codebase.classes = []
    codebase.symbols = [cli_func, web_func]
    codebase.ctx = Mock()
    codebase.ctx.out_edges = Mock(return_value=[])
    
    entry_points = identify_entry_points(codebase)
    
    # Should detect CLI command
    assert len(entry_points['cli_commands']) == 1
    assert entry_points['cli_commands'][0].name == 'cli_command'
    
    # Should detect web route
    assert len(entry_points['web_routes']) == 1
    assert entry_points['web_routes'][0].name == 'api_endpoint'
    
    # Should detect decorated functions
    assert len(entry_points['decorated_functions']) == 2


def test_dead_code_with_symbol_usages():
    """Test dead code detection considering symbol usages."""
    codebase = Mock(spec=Codebase)
    
    # Mock function with no usages
    unused_func = Mock(spec=Function)
    unused_func.name = 'unused_function'
    unused_func.symbol_usages = []
    unused_func.call_sites = []
    unused_func.dependencies = Mock(return_value=[])
    
    # Mock function with usages
    used_func = Mock(spec=Function)
    used_func.name = 'used_function'
    used_func.symbol_usages = [Mock()]  # Has usages
    used_func.call_sites = []
    used_func.dependencies = Mock(return_value=[])
    
    codebase.functions = [unused_func, used_func]
    codebase.classes = []
    codebase.symbols = [unused_func, used_func]
    codebase.ctx = Mock()
    codebase.ctx.out_edges = Mock(return_value=[])
    
    dead_code = detect_dead_code(codebase)
    
    # The unused function should be in potentially_dead
    potentially_dead_names = [s.name for s in dead_code['potentially_dead']]
    assert 'unused_function' in potentially_dead_names


if __name__ == '__main__':
    pytest.main([__file__])
