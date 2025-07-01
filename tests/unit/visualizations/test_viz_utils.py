"""Tests for visualization utilities."""

import json
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
import pytest
import networkx as nx

from graph_sitter.visualizations.viz_utils import (
    get_graph_json,
    get_node_options,
    get_node_id,
    validate_graph_input,
    graph_to_json,
    get_conversion_stats,
    clear_conversion_cache
)
from graph_sitter.visualizations.enums import (
    VizNode,
    GraphType,
    VisualizationError,
    GraphConversionError,
    FileOperationError
)


class MockEditable:
    """Mock Editable object for testing."""
    
    def __init__(self, span="test_span", viz=None):
        self.span = span
        self.viz = viz or VizNode(name="test_node")


class MockImportable:
    """Mock Importable object for testing."""
    
    def __init__(self, node_id="test_id"):
        self.node_id = node_id


class TestGetGraphJson:
    """Test get_graph_json function."""

    def test_get_graph_json_file_exists(self):
        """Test reading existing graph JSON file."""
        test_data = {"type": "graph", "data": {"nodes": [], "edges": []}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            mock_op = Mock()
            mock_op.viz_file_path = temp_path
            
            result = get_graph_json(mock_op)
            assert result == test_data
        finally:
            os.unlink(temp_path)

    def test_get_graph_json_file_not_exists(self):
        """Test reading non-existent graph JSON file."""
        mock_op = Mock()
        mock_op.viz_file_path = "/nonexistent/path.json"
        
        result = get_graph_json(mock_op)
        assert result is None

    def test_get_graph_json_invalid_json(self):
        """Test reading invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name
        
        try:
            mock_op = Mock()
            mock_op.viz_file_path = temp_path
            
            with pytest.raises(FileOperationError, match="Invalid JSON"):
                get_graph_json(mock_op)
        finally:
            os.unlink(temp_path)

    def test_get_graph_json_not_dict(self):
        """Test reading JSON that's not a dictionary."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(["not", "a", "dict"], f)
            temp_path = f.name
        
        try:
            mock_op = Mock()
            mock_op.viz_file_path = temp_path
            
            with pytest.raises(FileOperationError, match="Invalid graph JSON"):
                get_graph_json(mock_op)
        finally:
            os.unlink(temp_path)

    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_get_graph_json_io_error(self, mock_file):
        """Test handling IO errors."""
        mock_op = Mock()
        mock_op.viz_file_path = "/test/path.json"
        
        with patch('os.path.exists', return_value=True):
            with pytest.raises(FileOperationError, match="Failed to read"):
                get_graph_json(mock_op)


class TestGetNodeOptions:
    """Test get_node_options function."""

    def test_get_node_options_editable_with_viz(self):
        """Test extracting options from Editable with viz property."""
        viz_node = VizNode(name="test", color="red")
        editable = MockEditable(viz=viz_node)
        
        options = get_node_options(editable)
        assert options["name"] == "test"
        assert options["color"] == "red"

    def test_get_node_options_editable_without_viz(self):
        """Test extracting options from Editable without viz property."""
        editable = Mock(spec=[])  # No viz attribute
        
        options = get_node_options(editable)
        assert options == {}

    def test_get_node_options_non_editable(self):
        """Test extracting options from non-Editable object."""
        options = get_node_options("string_node")
        assert options == {}
        
        options = get_node_options(123)
        assert options == {}

    def test_get_node_options_error_handling(self):
        """Test error handling in get_node_options."""
        # Mock an Editable that raises an exception when accessing viz
        editable = Mock()
        editable.viz = Mock(side_effect=Exception("Test error"))
        
        with pytest.raises(GraphConversionError, match="Failed to extract node options"):
            get_node_options(editable)


class TestGetNodeId:
    """Test get_node_id function."""

    def test_get_node_id_importable(self):
        """Test extracting ID from Importable object."""
        importable = MockImportable("test_node_id")
        
        node_id = get_node_id(importable)
        assert node_id == "test_node_id"

    def test_get_node_id_editable(self):
        """Test extracting ID from Editable object."""
        editable = MockEditable(span="test_span")
        
        node_id = get_node_id(editable)
        assert node_id == "test_span"

    def test_get_node_id_string(self):
        """Test extracting ID from string."""
        node_id = get_node_id("string_id")
        assert node_id == "string_id"

    def test_get_node_id_int(self):
        """Test extracting ID from integer."""
        node_id = get_node_id(42)
        assert node_id == 42

    def test_get_node_id_unsupported_type(self):
        """Test error handling for unsupported node types."""
        with pytest.raises(GraphConversionError, match="Unsupported node type"):
            get_node_id([1, 2, 3])

    def test_get_node_id_error_handling(self):
        """Test error handling in get_node_id."""
        # Mock an object that raises an exception
        mock_obj = Mock()
        mock_obj.node_id = Mock(side_effect=Exception("Test error"))
        
        with pytest.raises(GraphConversionError, match="Failed to extract node ID"):
            get_node_id(mock_obj)


class TestValidateGraphInput:
    """Test validate_graph_input function."""

    def test_validate_graph_input_valid(self):
        """Test validation of valid graph."""
        G = nx.Graph()
        G.add_node(1, data={"test": "value"})
        G.add_edge(1, 2, weight=1.0)
        
        # Should not raise any exception
        validate_graph_input(G)

    def test_validate_graph_input_empty(self):
        """Test validation of empty graph."""
        G = nx.Graph()
        
        # Should not raise exception, but may log warning
        validate_graph_input(G)

    def test_validate_graph_input_not_graph(self):
        """Test validation of non-graph object."""
        with pytest.raises(GraphConversionError, match="Expected NetworkX Graph"):
            validate_graph_input("not_a_graph")

    def test_validate_graph_input_large_graph(self):
        """Test validation of large graph."""
        G = nx.Graph()
        # Add many nodes to trigger warning
        for i in range(15000):
            G.add_node(i)
        
        # Should not raise exception, but may log warning
        validate_graph_input(G)

    def test_validate_graph_input_invalid_node_data(self):
        """Test validation with invalid node data."""
        G = nx.Graph()
        G.add_node(1, data="not_a_dict")
        
        with pytest.raises(GraphConversionError, match="Invalid node data"):
            validate_graph_input(G)

    def test_validate_graph_input_invalid_edge_data(self):
        """Test validation with invalid edge data."""
        G = nx.Graph()
        G.add_edge(1, 2, data="not_a_dict")
        
        with pytest.raises(GraphConversionError, match="Invalid edge data"):
            validate_graph_input(G)


class TestGraphToJson:
    """Test graph_to_json function."""

    def test_graph_to_json_simple_graph(self):
        """Test converting simple graph to JSON."""
        G = nx.Graph()
        G.add_node(1, name="node1")
        G.add_node(2, name="node2")
        G.add_edge(1, 2, weight=1.0)
        
        result = graph_to_json(G)
        
        # Parse the result to verify structure
        parsed = json.loads(result)
        assert parsed["type"] == GraphType.GRAPH
        assert "data" in parsed
        assert "nodes" in parsed["data"]
        assert "links" in parsed["data"]

    def test_graph_to_json_with_root(self):
        """Test converting graph to JSON with root node."""
        G = nx.DiGraph()
        G.add_node(1, name="root")
        G.add_node(2, name="child")
        G.add_edge(1, 2)
        
        result = graph_to_json(G, root=1)
        
        # Parse the result to verify structure
        parsed = json.loads(result)
        assert parsed["type"] == GraphType.TREE

    def test_graph_to_json_with_editable_nodes(self):
        """Test converting graph with Editable nodes."""
        G = nx.Graph()
        node1 = MockEditable(span="span1", viz=VizNode(name="test1"))
        node2 = MockEditable(span="span2", viz=VizNode(name="test2"))
        
        G.add_node(node1)
        G.add_node(node2)
        G.add_edge(node1, node2)
        
        result = graph_to_json(G)
        
        # Should not raise exception
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["type"] == GraphType.GRAPH

    def test_graph_to_json_with_symbol_edge(self):
        """Test converting graph with symbol in edge data."""
        G = nx.Graph()
        G.add_node(1)
        G.add_node(2)
        
        symbol = MockEditable(viz=VizNode(name="symbol"))
        G.add_edge(1, 2, symbol=symbol, weight=1.0)
        
        result = graph_to_json(G)
        
        # Should not raise exception
        assert isinstance(result, str)

    def test_graph_to_json_error_handling(self):
        """Test error handling in graph conversion."""
        # Test with invalid root
        G = nx.Graph()
        G.add_node(1)
        
        with pytest.raises(GraphConversionError, match="Root node .* not found"):
            graph_to_json(G, root=999)

    def test_graph_to_json_skip_validation(self):
        """Test graph conversion with validation skipped."""
        G = nx.Graph()
        G.add_node(1)
        
        result = graph_to_json(G, validate_input=False)
        assert isinstance(result, str)

    def test_graph_to_json_node_processing_error(self):
        """Test handling of node processing errors."""
        G = nx.Graph()
        
        # Add a node that will cause processing errors
        bad_node = Mock()
        bad_node.span = Mock(side_effect=Exception("Test error"))
        G.add_node(bad_node)
        
        # Should still produce valid JSON with error information
        result = graph_to_json(G)
        assert isinstance(result, str)
        
        parsed = json.loads(result)
        assert parsed["type"] == GraphType.GRAPH


class TestPerformanceMonitoring:
    """Test performance monitoring functions."""

    def test_get_conversion_stats(self):
        """Test getting conversion statistics."""
        stats = get_conversion_stats()
        
        assert isinstance(stats, dict)
        assert "node_cache_hits" in stats
        assert "node_cache_misses" in stats
        assert "node_cache_size" in stats
        assert "node_cache_max_size" in stats

    def test_clear_conversion_cache(self):
        """Test clearing conversion cache."""
        # This should not raise any exception
        clear_conversion_cache()
        
        # Verify cache is cleared
        stats = get_conversion_stats()
        assert stats["node_cache_size"] == 0

