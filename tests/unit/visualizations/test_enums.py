"""Tests for visualization enums and data structures."""

import pytest
from dataclasses import FrozenInstanceError

from graph_sitter.visualizations.enums import (
    VizNode,
    GraphJson,
    GraphType,
    ExportFormat,
    VisualizationError,
    GraphConversionError,
    FileOperationError
)


class TestVizNode:
    """Test VizNode dataclass functionality."""

    def test_viznode_creation_valid(self):
        """Test creating a valid VizNode."""
        node = VizNode(
            name="test_node",
            text="Test Node",
            color="#FF0000",
            start_point=(10, 20),
            end_point=(30, 40),
            file_path="/test/path.py",
            symbol_name="TestSymbol"
        )
        
        assert node.name == "test_node"
        assert node.text == "Test Node"
        assert node.color == "#FF0000"
        assert node.start_point == (10, 20)
        assert node.end_point == (30, 40)
        assert node.file_path == "/test/path.py"
        assert node.symbol_name == "TestSymbol"

    def test_viznode_creation_minimal(self):
        """Test creating a VizNode with minimal data."""
        node = VizNode()
        
        assert node.name is None
        assert node.text is None
        assert node.color is None
        assert node.start_point is None
        assert node.end_point is None

    def test_viznode_validation_invalid_start_point(self):
        """Test VizNode validation with invalid start_point."""
        with pytest.raises(ValueError, match="start_point must be a tuple of \\(row, col\\)"):
            VizNode(start_point=(10,))

    def test_viznode_validation_invalid_end_point(self):
        """Test VizNode validation with invalid end_point."""
        with pytest.raises(ValueError, match="end_point must be a tuple of \\(row, col\\)"):
            VizNode(end_point=(10, 20, 30))

    def test_viznode_validation_invalid_color(self):
        """Test VizNode validation with invalid color."""
        with pytest.raises(ValueError, match="color must be a hex color"):
            VizNode(color="invalid_color_123")

    def test_viznode_validation_valid_colors(self):
        """Test VizNode validation with valid colors."""
        # Hex color
        node1 = VizNode(color="#FF0000")
        assert node1.color == "#FF0000"
        
        # Named color
        node2 = VizNode(color="red")
        assert node2.color == "red"

    def test_viznode_immutable(self):
        """Test that VizNode is immutable."""
        node = VizNode(name="test")
        
        with pytest.raises(FrozenInstanceError):
            node.name = "changed"

    def test_viznode_metadata(self):
        """Test VizNode metadata functionality."""
        node = VizNode(name="test")
        
        # Metadata should be empty by default
        assert node._metadata == {}
        
        # Metadata should not affect equality comparison
        node2 = VizNode(name="test")
        assert node == node2


class TestGraphJson:
    """Test GraphJson dataclass functionality."""

    def test_graphjson_creation_valid(self):
        """Test creating a valid GraphJson."""
        data = {"nodes": [], "edges": []}
        metadata = {"created_at": "2023-01-01"}
        
        graph_json = GraphJson(
            type=GraphType.GRAPH,
            data=data,
            metadata=metadata
        )
        
        assert graph_json.type == GraphType.GRAPH
        assert graph_json.data == data
        assert graph_json.metadata == metadata

    def test_graphjson_creation_minimal(self):
        """Test creating GraphJson with minimal data."""
        data = {"test": "data"}
        
        graph_json = GraphJson(
            type=GraphType.TREE,
            data=data
        )
        
        assert graph_json.type == GraphType.TREE
        assert graph_json.data == data
        assert graph_json.metadata == {}

    def test_graphjson_validation_invalid_type(self):
        """Test GraphJson validation with invalid type."""
        with pytest.raises(ValueError, match="Invalid graph type: invalid"):
            GraphJson(type="invalid", data={})

    def test_graphjson_validation_invalid_data(self):
        """Test GraphJson validation with invalid data."""
        with pytest.raises(ValueError, match="data must be a dictionary"):
            GraphJson(type=GraphType.GRAPH, data="not_a_dict")

    def test_graphjson_immutable(self):
        """Test that GraphJson is immutable."""
        graph_json = GraphJson(type=GraphType.GRAPH, data={})
        
        with pytest.raises(FrozenInstanceError):
            graph_json.type = GraphType.TREE


class TestEnums:
    """Test enum functionality."""

    def test_graph_type_values(self):
        """Test GraphType enum values."""
        assert GraphType.TREE == "tree"
        assert GraphType.GRAPH == "graph"
        
        # Test all values are present
        assert len(GraphType) == 2

    def test_export_format_values(self):
        """Test ExportFormat enum values."""
        assert ExportFormat.JSON == "json"
        assert ExportFormat.HTML == "html"
        assert ExportFormat.PNG == "png"
        assert ExportFormat.SVG == "svg"
        
        # Test all values are present
        assert len(ExportFormat) == 4


class TestExceptions:
    """Test custom exception classes."""

    def test_visualization_error(self):
        """Test VisualizationError exception."""
        error = VisualizationError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_graph_conversion_error(self):
        """Test GraphConversionError exception."""
        error = GraphConversionError("Conversion failed")
        assert str(error) == "Conversion failed"
        assert isinstance(error, VisualizationError)
        assert isinstance(error, Exception)

    def test_file_operation_error(self):
        """Test FileOperationError exception."""
        error = FileOperationError("File operation failed")
        assert str(error) == "File operation failed"
        assert isinstance(error, VisualizationError)
        assert isinstance(error, Exception)

    def test_exception_inheritance(self):
        """Test exception inheritance hierarchy."""
        # All custom exceptions should inherit from VisualizationError
        assert issubclass(GraphConversionError, VisualizationError)
        assert issubclass(FileOperationError, VisualizationError)
        
        # VisualizationError should inherit from Exception
        assert issubclass(VisualizationError, Exception)

