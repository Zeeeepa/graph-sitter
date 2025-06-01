import os
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Union, Dict, Any
import logging

import plotly.graph_objects as go
from networkx import Graph

from graph_sitter.core.interfaces.editable import Editable
from graph_sitter.git.repo_operator.repo_operator import RepoOperator
from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.visualizations.viz_utils import graph_to_json, get_conversion_stats
from graph_sitter.visualizations.enums import (
    ExportFormat, 
    VisualizationError, 
    FileOperationError,
    GraphConversionError
)

logger = get_logger(__name__)


class VisualizationManager:
    """
    Enhanced visualization manager with async I/O, caching, and comprehensive error handling.
    """
    
    def __init__(self, op: RepoOperator) -> None:
        """
        Initialize the visualization manager.
        
        Args:
            op: RepoOperator instance for file operations
        """
        self.op = op
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="viz-io")
        self._write_lock = threading.Lock()
        self._stats = {
            "writes_completed": 0,
            "writes_failed": 0,
            "bytes_written": 0,
            "cache_clears": 0
        }

    @property
    def viz_path(self) -> str:
        """Get the visualization directory path."""
        return os.path.join(self.op.base_dir, "codegen-graphviz")

    @property
    def viz_file_path(self) -> str:
        """Get the main visualization file path."""
        return os.path.join(self.viz_path, "graph.json")

    def _ensure_viz_directory(self) -> None:
        """
        Ensure visualization directory exists and is properly set up.
        
        Raises:
            FileOperationError: If directory cannot be created or accessed
        """
        try:
            if self.op.folder_exists(self.viz_path):
                # Verify we can write to the directory
                test_file = os.path.join(self.viz_path, ".write_test")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                except Exception as e:
                    raise FileOperationError(f"Cannot write to visualization directory: {e}")
            else:
                # Create the directory
                try:
                    self.op.mkdir(self.viz_path)
                    logger.debug(f"Created visualization directory: {self.viz_path}")
                except Exception as e:
                    raise FileOperationError(f"Failed to create visualization directory: {e}")
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError(f"Unexpected error setting up visualization directory: {e}")

    def clear_graphviz_data(self) -> None:
        """
        Clear visualization data with enhanced error handling.
        
        Raises:
            FileOperationError: If clearing fails
        """
        try:
            with self._write_lock:
                if self.op.folder_exists(self.viz_path):
                    self.op.emptydir(self.viz_path)
                    logger.debug(f"Cleared visualization data from {self.viz_path}")
                    self._stats["cache_clears"] += 1
                else:
                    logger.debug("Visualization directory does not exist, nothing to clear")
        except Exception as e:
            self._stats["writes_failed"] += 1
            raise FileOperationError(f"Failed to clear visualization data: {e}")

    def _write_file_sync(self, file_path: str, content: str) -> None:
        """
        Synchronously write content to file with proper error handling.
        
        Args:
            file_path: Path to write to
            content: Content to write
            
        Raises:
            FileOperationError: If write operation fails
        """
        try:
            with open(file_path, "w", encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
            
            # Update statistics
            self._stats["bytes_written"] += len(content.encode('utf-8'))
            logger.debug(f"Successfully wrote {len(content)} characters to {file_path}")
            
        except IOError as e:
            raise FileOperationError(f"Failed to write visualization file: {e}")
        except Exception as e:
            raise FileOperationError(f"Unexpected error writing visualization file: {e}")

    async def write_graphviz_data_async(
        self, 
        G: Union[Graph, go.Figure], 
        root: Optional[Union[Editable, str, int]] = None,
        export_format: ExportFormat = ExportFormat.JSON
    ) -> None:
        """
        Asynchronously write graph data to file.
        
        Args:
            G: NetworkX Graph or Plotly Figure to visualize
            root: Optional root node for tree visualization
            export_format: Export format (default: JSON)
            
        Raises:
            VisualizationError: If visualization fails
            FileOperationError: If file operations fail
        """
        try:
            # Prepare the visualization directory
            self._ensure_viz_directory()
            
            # Convert graph to appropriate format
            if isinstance(G, Graph):
                try:
                    graph_content = graph_to_json(G, root)
                except Exception as e:
                    raise GraphConversionError(f"Graph conversion failed: {e}")
            elif isinstance(G, go.Figure):
                try:
                    graph_content = G.to_json()
                except Exception as e:
                    raise GraphConversionError(f"Plotly figure conversion failed: {e}")
            else:
                raise VisualizationError(f"Unsupported graph type: {type(G)}")

            # Determine file path based on export format
            if export_format == ExportFormat.JSON:
                file_path = self.viz_file_path
            else:
                file_name = f"graph.{export_format.value}"
                file_path = os.path.join(self.viz_path, file_name)

            # Write file asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor, 
                self._write_file_sync, 
                file_path, 
                graph_content
            )
            
            self._stats["writes_completed"] += 1
            logger.info(f"Successfully wrote visualization data to {file_path}")
            
        except (VisualizationError, FileOperationError):
            self._stats["writes_failed"] += 1
            raise
        except Exception as e:
            self._stats["writes_failed"] += 1
            raise VisualizationError(f"Unexpected error during async visualization write: {e}")

    def write_graphviz_data(
        self, 
        G: Union[Graph, go.Figure], 
        root: Optional[Union[Editable, str, int]] = None
    ) -> None:
        """
        Write graph data to file with enhanced error handling and performance monitoring.
        
        This method maintains backward compatibility while adding comprehensive error handling.
        
        Args:
            G: NetworkX Graph or Plotly Figure to visualize
            root: Optional root node for tree visualization
            
        Raises:
            VisualizationError: If visualization fails
        """
        try:
            # Prepare the visualization directory
            self._ensure_viz_directory()
            
            # Convert graph to JSON format
            if isinstance(G, Graph):
                try:
                    graph_json = graph_to_json(G, root)
                except Exception as e:
                    raise GraphConversionError(f"Graph conversion failed: {e}")
            elif isinstance(G, go.Figure):
                try:
                    graph_json = G.to_json()
                except Exception as e:
                    raise GraphConversionError(f"Plotly figure conversion failed: {e}")
            else:
                raise VisualizationError(f"Unsupported graph type: {type(G)}")

            # Clear existing data if directory exists
            with self._write_lock:
                if self.op.folder_exists(self.viz_path):
                    self.op.emptydir(self.viz_path)
                else:
                    self.op.mkdir(self.viz_path)

                # Write the graph data to file
                self._write_file_sync(self.viz_file_path, graph_json)
            
            self._stats["writes_completed"] += 1
            logger.info(f"Successfully wrote visualization data to {self.viz_file_path}")
            
        except (VisualizationError, FileOperationError):
            self._stats["writes_failed"] += 1
            raise
        except Exception as e:
            self._stats["writes_failed"] += 1
            raise VisualizationError(f"Unexpected error during visualization write: {e}")

    def export_visualization(
        self, 
        G: Union[Graph, go.Figure], 
        export_format: ExportFormat,
        output_path: Optional[str] = None,
        root: Optional[Union[Editable, str, int]] = None
    ) -> str:
        """
        Export visualization in specified format.
        
        Args:
            G: Graph or figure to export
            export_format: Desired export format
            output_path: Optional custom output path
            root: Optional root node for tree visualization
            
        Returns:
            Path to exported file
            
        Raises:
            VisualizationError: If export fails
        """
        try:
            if export_format not in ExportFormat:
                raise VisualizationError(f"Unsupported export format: {export_format}")
            
            # Determine output path
            if output_path:
                file_path = output_path
            else:
                self._ensure_viz_directory()
                file_name = f"graph.{export_format.value}"
                file_path = os.path.join(self.viz_path, file_name)
            
            # Export based on format
            if export_format == ExportFormat.JSON:
                if isinstance(G, Graph):
                    content = graph_to_json(G, root)
                else:
                    content = G.to_json()
                self._write_file_sync(file_path, content)
            else:
                # For other formats, we'd need additional conversion logic
                # This is a placeholder for future enhancement
                raise VisualizationError(f"Export format {export_format} not yet implemented")
            
            logger.info(f"Successfully exported visualization to {file_path}")
            return file_path
            
        except Exception as e:
            if isinstance(e, VisualizationError):
                raise
            raise VisualizationError(f"Export failed: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the visualization manager.
        
        Returns:
            Dictionary containing performance metrics
        """
        conversion_stats = get_conversion_stats()
        return {
            **self._stats,
            **conversion_stats,
            "success_rate": (
                self._stats["writes_completed"] / 
                max(self._stats["writes_completed"] + self._stats["writes_failed"], 1)
            ) * 100
        }

    def cleanup(self) -> None:
        """Clean up resources used by the visualization manager."""
        try:
            self._executor.shutdown(wait=True)
            logger.debug("Visualization manager cleanup completed")
        except Exception as e:
            logger.warning(f"Error during visualization manager cleanup: {e}")

    def __del__(self):
        """Ensure cleanup on object destruction."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during destruction

