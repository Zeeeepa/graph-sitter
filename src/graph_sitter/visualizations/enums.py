from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Dict, Any, Tuple


@dataclass(frozen=True)
class VizNode:
    """Visualization node with enhanced validation and lazy loading support."""
    name: Optional[str] = None
    text: Optional[str] = None
    code: Optional[str] = None
    color: Optional[str] = None
    shape: Optional[str] = None
    start_point: Optional[Tuple[int, int]] = None
    emoji: Optional[str] = None
    end_point: Optional[Tuple[int, int]] = None
    file_path: Optional[str] = None
    symbol_name: Optional[str] = None
    # Performance optimization: lazy-loaded metadata
    _metadata: Dict[str, Any] = field(default_factory=dict, compare=False)
    
    def __post_init__(self):
        """Validate node data on creation."""
        if self.start_point and len(self.start_point) != 2:
            raise ValueError("start_point must be a tuple of (row, col)")
        if self.end_point and len(self.end_point) != 2:
            raise ValueError("end_point must be a tuple of (row, col)")
        if self.color and not self.color.startswith('#') and not self.color.isalpha():
            raise ValueError("color must be a hex color (#RRGGBB) or named color")


@dataclass(frozen=True)
class GraphJson:
    """Enhanced graph JSON structure with validation."""
    type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate graph JSON structure."""
        if self.type not in [GraphType.TREE, GraphType.GRAPH]:
            raise ValueError(f"Invalid graph type: {self.type}")
        if not isinstance(self.data, dict):
            raise ValueError("data must be a dictionary")


class GraphType(StrEnum):
    """Supported graph visualization types."""
    TREE = "tree"
    GRAPH = "graph"


class ExportFormat(StrEnum):
    """Supported export formats for visualizations."""
    JSON = "json"
    HTML = "html"
    PNG = "png"
    SVG = "svg"


class VisualizationError(Exception):
    """Base exception for visualization-related errors."""
    pass


class GraphConversionError(VisualizationError):
    """Raised when graph conversion fails."""
    pass


class FileOperationError(VisualizationError):
    """Raised when file operations fail."""
    pass

