"""Tests for VisualizationManager."""

import os
import tempfile
import asyncio
from unittest.mock import Mock, patch, MagicMock
import pytest
import networkx as nx
import plotly.graph_objects as go

from graph_sitter.visualizations.visualization_manager import VisualizationManager
from graph_sitter.visualizations.enums import (
    ExportFormat,
    VisualizationError,
    FileOperationError,
    GraphConversionError
)


class TestVisualizationManager:
    """Test VisualizationManager functionality."""

    @pytest.fixture
    def mock_repo_operator(self):
        """Create a mock RepoOperator for testing."""
        mock_op = Mock()
        mock_op.base_dir = "/test/base"
        mock_op.folder_exists = Mock(return_value=False)
        mock_op.mkdir = Mock()
        mock_op.emptydir = Mock()
        return mock_op

    @pytest.fixture
    def viz_manager(self, mock_repo_operator):
        """Create a VisualizationManager instance for testing."""
        return VisualizationManager(mock_repo_operator)

    def test_init(self, mock_repo_operator):
        """Test VisualizationManager initialization."""
        manager = VisualizationManager(mock_repo_operator)
        
        assert manager.op == mock_repo_operator
        assert manager._executor is not None
        assert manager._write_lock is not None
        assert isinstance(manager._stats, dict)

    def test_viz_path_property(self, viz_manager):
        """Test viz_path property."""
        expected_path = os.path.join("/test/base", "codegen-graphviz")
        assert viz_manager.viz_path == expected_path

    def test_viz_file_path_property(self, viz_manager):
        """Test viz_file_path property."""
        expected_path = os.path.join("/test/base", "codegen-graphviz", "graph.json")
        assert viz_manager.viz_file_path == expected_path

    def test_ensure_viz_directory_create_new(self, viz_manager):
        """Test ensuring visualization directory when it doesn't exist."""
        viz_manager.op.folder_exists.return_value = False
        
        viz_manager._ensure_viz_directory()
        
        viz_manager.op.mkdir.assert_called_once_with(viz_manager.viz_path)

    def test_ensure_viz_directory_exists_writable(self, viz_manager):
        """Test ensuring visualization directory when it exists and is writable."""
        viz_manager.op.folder_exists.return_value = True
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('os.remove') as mock_remove:
                viz_manager._ensure_viz_directory()
                
                mock_open.assert_called_once()
                mock_remove.assert_called_once()

    def test_ensure_viz_directory_exists_not_writable(self, viz_manager):
        """Test ensuring visualization directory when it exists but is not writable."""
        viz_manager.op.folder_exists.return_value = True
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(FileOperationError, match="Cannot write to visualization directory"):
                viz_manager._ensure_viz_directory()

    def test_ensure_viz_directory_mkdir_fails(self, viz_manager):
        """Test handling mkdir failure."""
        viz_manager.op.folder_exists.return_value = False
        viz_manager.op.mkdir.side_effect = Exception("Mkdir failed")
        
        with pytest.raises(FileOperationError, match="Failed to create visualization directory"):
            viz_manager._ensure_viz_directory()

    def test_clear_graphviz_data_success(self, viz_manager):
        """Test successful clearing of visualization data."""
        viz_manager.op.folder_exists.return_value = True
        
        viz_manager.clear_graphviz_data()
        
        viz_manager.op.emptydir.assert_called_once_with(viz_manager.viz_path)
        assert viz_manager._stats["cache_clears"] == 1

    def test_clear_graphviz_data_no_directory(self, viz_manager):
        """Test clearing when directory doesn't exist."""
        viz_manager.op.folder_exists.return_value = False
        
        viz_manager.clear_graphviz_data()
        
        viz_manager.op.emptydir.assert_not_called()

    def test_clear_graphviz_data_error(self, viz_manager):
        """Test error handling in clear_graphviz_data."""
        viz_manager.op.folder_exists.return_value = True
        viz_manager.op.emptydir.side_effect = Exception("Clear failed")
        
        with pytest.raises(FileOperationError, match="Failed to clear visualization data"):
            viz_manager.clear_graphviz_data()
        
        assert viz_manager._stats["writes_failed"] == 1

    def test_write_file_sync_success(self, viz_manager):
        """Test successful synchronous file writing."""
        content = "test content"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            viz_manager._write_file_sync(temp_path, content)
            
            # Verify file was written
            with open(temp_path, 'r') as f:
                assert f.read() == content
            
            # Verify stats were updated
            assert viz_manager._stats["bytes_written"] > 0
        finally:
            os.unlink(temp_path)

    def test_write_file_sync_io_error(self, viz_manager):
        """Test handling IO error in synchronous file writing."""
        with pytest.raises(FileOperationError, match="Failed to write visualization file"):
            viz_manager._write_file_sync("/invalid/path/file.json", "content")

    def test_write_graphviz_data_networkx_graph(self, viz_manager):
        """Test writing NetworkX graph data."""
        G = nx.Graph()
        G.add_node(1, name="test")
        G.add_edge(1, 2)
        
        with patch.object(viz_manager, '_ensure_viz_directory'):
            with patch.object(viz_manager, '_write_file_sync') as mock_write:
                viz_manager.write_graphviz_data(G)
                
                mock_write.assert_called_once()
                args, kwargs = mock_write.call_args
                assert args[0] == viz_manager.viz_file_path
                assert isinstance(args[1], str)  # JSON content

    def test_write_graphviz_data_plotly_figure(self, viz_manager):
        """Test writing Plotly figure data."""
        fig = go.Figure(data=go.Bar(x=[1, 2, 3], y=[4, 5, 6]))
        
        with patch.object(viz_manager, '_ensure_viz_directory'):
            with patch.object(viz_manager, '_write_file_sync') as mock_write:
                viz_manager.write_graphviz_data(fig)
                
                mock_write.assert_called_once()
                args, kwargs = mock_write.call_args
                assert args[0] == viz_manager.viz_file_path
                assert isinstance(args[1], str)  # JSON content

    def test_write_graphviz_data_unsupported_type(self, viz_manager):
        """Test error handling for unsupported graph type."""
        with pytest.raises(VisualizationError, match="Unsupported graph type"):
            viz_manager.write_graphviz_data("not_a_graph")

    def test_write_graphviz_data_conversion_error(self, viz_manager):
        """Test handling graph conversion errors."""
        G = nx.Graph()
        
        with patch.object(viz_manager, '_ensure_viz_directory'):
            with patch('graph_sitter.visualizations.viz_utils.graph_to_json', 
                      side_effect=Exception("Conversion failed")):
                with pytest.raises(GraphConversionError, match="Graph conversion failed"):
                    viz_manager.write_graphviz_data(G)

    @pytest.mark.asyncio
    async def test_write_graphviz_data_async_success(self, viz_manager):
        """Test successful asynchronous writing."""
        G = nx.Graph()
        G.add_node(1, name="test")
        
        with patch.object(viz_manager, '_ensure_viz_directory'):
            with patch.object(viz_manager, '_write_file_sync') as mock_write:
                await viz_manager.write_graphviz_data_async(G)
                
                mock_write.assert_called_once()
                assert viz_manager._stats["writes_completed"] == 1

    @pytest.mark.asyncio
    async def test_write_graphviz_data_async_error(self, viz_manager):
        """Test error handling in asynchronous writing."""
        G = nx.Graph()
        
        with patch.object(viz_manager, '_ensure_viz_directory', 
                         side_effect=FileOperationError("Directory error")):
            with pytest.raises(FileOperationError):
                await viz_manager.write_graphviz_data_async(G)
            
            assert viz_manager._stats["writes_failed"] == 1

    def test_export_visualization_json(self, viz_manager):
        """Test exporting visualization in JSON format."""
        G = nx.Graph()
        G.add_node(1, name="test")
        
        with patch.object(viz_manager, '_ensure_viz_directory'):
            with patch.object(viz_manager, '_write_file_sync') as mock_write:
                result_path = viz_manager.export_visualization(G, ExportFormat.JSON)
                
                expected_path = os.path.join(viz_manager.viz_path, "graph.json")
                assert result_path == expected_path
                mock_write.assert_called_once()

    def test_export_visualization_custom_path(self, viz_manager):
        """Test exporting visualization with custom output path."""
        G = nx.Graph()
        G.add_node(1, name="test")
        custom_path = "/custom/path/output.json"
        
        with patch.object(viz_manager, '_write_file_sync') as mock_write:
            result_path = viz_manager.export_visualization(
                G, ExportFormat.JSON, output_path=custom_path
            )
            
            assert result_path == custom_path
            mock_write.assert_called_once()

    def test_export_visualization_unsupported_format(self, viz_manager):
        """Test error handling for unsupported export format."""
        G = nx.Graph()
        
        with pytest.raises(VisualizationError, match="Export format .* not yet implemented"):
            viz_manager.export_visualization(G, ExportFormat.PNG)

    def test_export_visualization_invalid_format(self, viz_manager):
        """Test error handling for invalid export format."""
        G = nx.Graph()
        
        with pytest.raises(VisualizationError, match="Unsupported export format"):
            viz_manager.export_visualization(G, "invalid_format")

    def test_get_performance_stats(self, viz_manager):
        """Test getting performance statistics."""
        # Simulate some operations
        viz_manager._stats["writes_completed"] = 5
        viz_manager._stats["writes_failed"] = 1
        viz_manager._stats["bytes_written"] = 1000
        
        with patch('graph_sitter.visualizations.viz_utils.get_conversion_stats',
                  return_value={"node_cache_hits": 10, "node_cache_misses": 2}):
            stats = viz_manager.get_performance_stats()
            
            assert stats["writes_completed"] == 5
            assert stats["writes_failed"] == 1
            assert stats["bytes_written"] == 1000
            assert stats["node_cache_hits"] == 10
            assert stats["node_cache_misses"] == 2
            assert "success_rate" in stats
            assert stats["success_rate"] == (5 / 6) * 100  # 5 success out of 6 total

    def test_cleanup(self, viz_manager):
        """Test cleanup method."""
        mock_executor = Mock()
        viz_manager._executor = mock_executor
        
        viz_manager.cleanup()
        
        mock_executor.shutdown.assert_called_once_with(wait=True)

    def test_cleanup_error_handling(self, viz_manager):
        """Test error handling in cleanup."""
        mock_executor = Mock()
        mock_executor.shutdown.side_effect = Exception("Shutdown failed")
        viz_manager._executor = mock_executor
        
        # Should not raise exception
        viz_manager.cleanup()

    def test_del_method(self, viz_manager):
        """Test __del__ method calls cleanup."""
        with patch.object(viz_manager, 'cleanup') as mock_cleanup:
            viz_manager.__del__()
            mock_cleanup.assert_called_once()

    def test_del_method_error_handling(self, viz_manager):
        """Test __del__ method handles cleanup errors."""
        with patch.object(viz_manager, 'cleanup', side_effect=Exception("Cleanup failed")):
            # Should not raise exception
            viz_manager.__del__()


class TestVisualizationManagerIntegration:
    """Integration tests for VisualizationManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def real_repo_operator(self, temp_dir):
        """Create a real-like RepoOperator for integration testing."""
        mock_op = Mock()
        mock_op.base_dir = temp_dir
        
        def folder_exists(path):
            return os.path.exists(path)
        
        def mkdir(path):
            os.makedirs(path, exist_ok=True)
        
        def emptydir(path):
            if os.path.exists(path):
                for file in os.listdir(path):
                    file_path = os.path.join(path, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
        
        mock_op.folder_exists = folder_exists
        mock_op.mkdir = mkdir
        mock_op.emptydir = emptydir
        
        return mock_op

    def test_full_workflow_networkx(self, real_repo_operator):
        """Test complete workflow with NetworkX graph."""
        manager = VisualizationManager(real_repo_operator)
        
        # Create a test graph
        G = nx.Graph()
        G.add_node(1, name="node1", color="red")
        G.add_node(2, name="node2", color="blue")
        G.add_edge(1, 2, weight=1.5)
        
        try:
            # Write the graph
            manager.write_graphviz_data(G)
            
            # Verify file was created
            assert os.path.exists(manager.viz_file_path)
            
            # Verify file content
            with open(manager.viz_file_path, 'r') as f:
                content = f.read()
                assert len(content) > 0
                
            # Verify stats
            stats = manager.get_performance_stats()
            assert stats["writes_completed"] == 1
            assert stats["writes_failed"] == 0
            assert stats["bytes_written"] > 0
            
        finally:
            manager.cleanup()

    @pytest.mark.asyncio
    async def test_full_workflow_async(self, real_repo_operator):
        """Test complete async workflow."""
        manager = VisualizationManager(real_repo_operator)
        
        # Create a test graph
        G = nx.DiGraph()
        G.add_node("root", name="Root Node")
        G.add_node("child1", name="Child 1")
        G.add_node("child2", name="Child 2")
        G.add_edge("root", "child1")
        G.add_edge("root", "child2")
        
        try:
            # Write the graph asynchronously
            await manager.write_graphviz_data_async(G, root="root")
            
            # Verify file was created
            assert os.path.exists(manager.viz_file_path)
            
            # Verify stats
            stats = manager.get_performance_stats()
            assert stats["writes_completed"] == 1
            
        finally:
            manager.cleanup()

