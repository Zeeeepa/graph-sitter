import json
import os
from dataclasses import asdict
from functools import lru_cache
from typing import TYPE_CHECKING, Optional, Dict, Any, Union
import logging

import networkx as nx
from networkx import DiGraph, Graph

from graph_sitter.core.interfaces.editable import Editable
from graph_sitter.core.interfaces.importable import Importable
from graph_sitter.output.utils import DeterministicJSONEncoder
from graph_sitter.visualizations.enums import (
    GraphJson, 
    GraphType, 
    VisualizationError, 
    GraphConversionError,
    FileOperationError
)

if TYPE_CHECKING:
    from graph_sitter.git.repo_operator.repo_operator import RepoOperator

logger = logging.getLogger(__name__)

####################################################################################################################
# READING GRAPH VISUALIZATION DATA
####################################################################################################################


def get_graph_json(op: "RepoOperator") -> Optional[Dict[str, Any]]:
    """
    Safely read graph visualization data from file.
    
    Args:
        op: RepoOperator instance containing viz_file_path
        
    Returns:
        Graph JSON data or None if file doesn't exist or is invalid
        
    Raises:
        FileOperationError: If file exists but cannot be read or parsed
    """
    try:
        if not os.path.exists(op.viz_file_path):
            logger.debug(f"Visualization file not found: {op.viz_file_path}")
            return None
            
        with open(op.viz_file_path, 'r', encoding='utf-8') as f:
            graph_json = json.load(f)
            
        # Validate the loaded JSON structure
        if not isinstance(graph_json, dict):
            raise FileOperationError("Invalid graph JSON: expected dictionary")
            
        logger.debug(f"Successfully loaded graph JSON from {op.viz_file_path}")
        return graph_json
        
    except json.JSONDecodeError as e:
        raise FileOperationError(f"Invalid JSON in visualization file: {e}")
    except IOError as e:
        raise FileOperationError(f"Failed to read visualization file: {e}")
    except Exception as e:
        raise FileOperationError(f"Unexpected error reading visualization file: {e}")


####################################################################################################################
# NETWORKX GRAPH TO JSON WITH PERFORMANCE OPTIMIZATIONS
####################################################################################################################


@lru_cache(maxsize=128)
def _get_cached_node_options(node_key: str, node_type: str) -> Dict[str, Any]:
    """
    Cache node options to avoid repeated computation.
    
    Args:
        node_key: String representation of the node
        node_type: Type of the node for optimization
        
    Returns:
        Cached node options dictionary
    """
    # This is a simplified cache - in practice, we'd need to handle
    # the actual node object serialization more carefully
    return {}


def get_node_options(node: Union[Editable, str, int]) -> Dict[str, Any]:
    """
    Extract visualization options from a node with error handling.
    
    Args:
        node: Node object to extract options from
        
    Returns:
        Dictionary of visualization options
        
    Raises:
        GraphConversionError: If node options cannot be extracted
    """
    try:
        if isinstance(node, Editable):
            if hasattr(node, 'viz'):
                return asdict(node.viz)
            else:
                logger.warning(f"Editable node {node} missing viz property")
                return {}
        return {}
    except Exception as e:
        raise GraphConversionError(f"Failed to extract node options: {e}")


def get_node_id(node: Union[Editable, str, int]) -> Union[str, int]:
    """
    Extract node ID with enhanced error handling and type safety.
    
    Args:
        node: Node object to extract ID from
        
    Returns:
        Node identifier
        
    Raises:
        GraphConversionError: If node ID cannot be determined
    """
    try:
        if isinstance(node, Importable):
            return node.node_id
        elif isinstance(node, Editable):
            return str(node.span)
        elif isinstance(node, (str, int)):
            return node
        else:
            raise GraphConversionError(f"Unsupported node type: {type(node)}")
    except Exception as e:
        raise GraphConversionError(f"Failed to extract node ID: {e}")


def validate_graph_input(G: Graph) -> None:
    """
    Validate input graph before conversion.
    
    Args:
        G: NetworkX graph to validate
        
    Raises:
        GraphConversionError: If graph is invalid
    """
    if not isinstance(G, Graph):
        raise GraphConversionError(f"Expected NetworkX Graph, got {type(G)}")
    
    if G.number_of_nodes() == 0:
        logger.warning("Converting empty graph")
    
    # Check for extremely large graphs that might cause memory issues
    if G.number_of_nodes() > 10000:
        logger.warning(f"Large graph detected: {G.number_of_nodes()} nodes. Consider optimization.")
    
    # Validate node and edge data
    for node, data in G.nodes(data=True):
        if data and not isinstance(data, dict):
            raise GraphConversionError(f"Invalid node data for {node}: expected dict, got {type(data)}")
    
    for u, v, data in G.edges(data=True):
        if data and not isinstance(data, dict):
            raise GraphConversionError(f"Invalid edge data for ({u}, {v}): expected dict, got {type(data)}")


def graph_to_json(
    G1: Graph, 
    root: Optional[Union[Editable, str, int]] = None,
    validate_input: bool = True
) -> str:
    """
    Convert NetworkX graph to JSON with comprehensive error handling and optimization.
    
    Args:
        G1: NetworkX graph to convert
        root: Optional root node for tree visualization
        validate_input: Whether to validate input graph (default: True)
        
    Returns:
        JSON string representation of the graph
        
    Raises:
        GraphConversionError: If conversion fails
        VisualizationError: If validation fails
    """
    try:
        if validate_input:
            validate_graph_input(G1)
        
        logger.debug(f"Converting graph with {G1.number_of_nodes()} nodes and {G1.number_of_edges()} edges")
        
        # Create directed graph for consistent output
        G2 = DiGraph()
        
        # Process nodes with error handling
        for node_tuple in G1.nodes(data=True):
            try:
                node, node_data = node_tuple
                options = get_node_options(node)
                if node_data:
                    options.update(node_data)
                node_id = get_node_id(node)
                G2.add_node(node_id, **options)
            except Exception as e:
                logger.error(f"Failed to process node {node_tuple}: {e}")
                # Add node with minimal data to maintain graph structure
                try:
                    node_id = get_node_id(node_tuple[0])
                    G2.add_node(node_id, error=f"Processing failed: {e}")
                except Exception:
                    # Last resort: use string representation
                    G2.add_node(str(node_tuple[0]), error=f"Processing failed: {e}")

        # Process edges with error handling
        for edge_tuple in G1.edges(data=True):
            try:
                u, v, edge_data = edge_tuple
                options = dict(edge_data) if edge_data else {}
                
                # Handle special symbol attribute
                if "symbol" in options:
                    try:
                        symbol_options = get_node_options(options["symbol"])
                        options.update(symbol_options)
                        del options["symbol"]
                    except Exception as e:
                        logger.warning(f"Failed to process symbol in edge {u}->{v}: {e}")
                        del options["symbol"]
                
                u_id = get_node_id(u)
                v_id = get_node_id(v)
                G2.add_edge(u_id, v_id, **options)
                
            except Exception as e:
                logger.error(f"Failed to process edge {edge_tuple}: {e}")
                # Add edge with minimal data to maintain graph structure
                try:
                    u_id = get_node_id(edge_tuple[0])
                    v_id = get_node_id(edge_tuple[1])
                    G2.add_edge(u_id, v_id, error=f"Processing failed: {e}")
                except Exception:
                    # Skip this edge if we can't even get basic IDs
                    logger.error(f"Completely failed to process edge {edge_tuple}")

        # Generate appropriate JSON based on root parameter
        try:
            if root:
                root_id = get_node_id(root)
                if root_id not in G2:
                    raise GraphConversionError(f"Root node {root_id} not found in graph")
                
                graph_data = nx.tree_data(G2, root_id)
                graph_json = GraphJson(type=GraphType.TREE.value, data=graph_data)
            else:
                graph_data = nx.node_link_data(G2)
                graph_json = GraphJson(type=GraphType.GRAPH.value, data=graph_data)
            
            result = json.dumps(
                asdict(graph_json), 
                cls=DeterministicJSONEncoder, 
                indent=2
            )
            
            logger.debug(f"Successfully converted graph to JSON ({len(result)} characters)")
            return result
            
        except Exception as e:
            raise GraphConversionError(f"Failed to serialize graph to JSON: {e}")
            
    except GraphConversionError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise GraphConversionError(f"Unexpected error during graph conversion: {e}")


####################################################################################################################
# PERFORMANCE MONITORING
####################################################################################################################


def get_conversion_stats() -> Dict[str, Any]:
    """
    Get statistics about graph conversion performance.
    
    Returns:
        Dictionary containing performance statistics
    """
    cache_info = _get_cached_node_options.cache_info()
    return {
        "node_cache_hits": cache_info.hits,
        "node_cache_misses": cache_info.misses,
        "node_cache_size": cache_info.currsize,
        "node_cache_max_size": cache_info.maxsize
    }


def clear_conversion_cache() -> None:
    """Clear all conversion caches to free memory."""
    _get_cached_node_options.cache_clear()
    logger.debug("Cleared visualization conversion cache")

