"""
Codebase state management for file tree navigation and file operations.

This module handles the state for file tree display, file selection, and basic file operations.
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
import os


class CodebaseState(rx.State):
    """State management for codebase file operations."""
    
    # File tree state
    file_tree: List[Dict[str, Any]] = []
    file_tree_loading: bool = False
    file_search_query: str = ""
    
    # File filters
    show_python_files: bool = True
    show_typescript_files: bool = True
    show_other_files: bool = True
    
    # Selected file state
    selected_file_path: str = ""
    selected_file_size: int = 0
    selected_file_lines: int = 0
    
    # File content viewing
    file_content: str = ""
    file_content_visible: bool = False
    file_content_loading: bool = False
    
    # Directory expansion state
    expanded_directories: List[str] = []
    
    def __init__(self, *args, **kwargs):
        """Initialize the codebase state."""
        super().__init__(*args, **kwargs)
    
    # File tree operations
    async def refresh_file_tree(self):
        """Refresh the file tree from the current codebase."""
        self.file_tree_loading = True
        
        try:
            # Get the codebase path from parent state
            from state.dashboard_state import DashboardState
            parent_state = self.get_state(DashboardState)
            
            if not parent_state.selected_codebase_path:
                self.file_tree = []
                return
            
            # Build file tree
            root_path = Path(parent_state.selected_codebase_path)
            if root_path.exists():
                self.file_tree = await self._build_file_tree(root_path)
            else:
                self.file_tree = []
                
        except Exception as e:
            print(f"Error refreshing file tree: {e}")
            self.file_tree = []
        finally:
            self.file_tree_loading = False
    
    async def _build_file_tree(self, root_path: Path) -> List[Dict[str, Any]]:
        """Build the file tree structure."""
        try:
            tree_nodes = []
            
            # Get all items in the directory
            items = []
            for item in root_path.iterdir():
                # Skip hidden files and common ignore patterns
                if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules', '.git']:
                    continue
                items.append(item)
            
            # Sort: directories first, then files
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if item.is_dir():
                    # Directory node
                    file_count = self._count_files_in_directory(item)
                    node = {
                        "name": item.name,
                        "path": str(item),
                        "is_directory": True,
                        "expanded": str(item) in self.expanded_directories,
                        "file_count": file_count,
                        "children": []
                    }
                    
                    # If expanded, load children
                    if node["expanded"]:
                        node["children"] = await self._build_file_tree(item)
                    
                    tree_nodes.append(node)
                    
                else:
                    # File node
                    extension = item.suffix
                    node = {
                        "name": item.name,
                        "path": str(item),
                        "is_directory": False,
                        "extension": extension,
                        "size": item.stat().st_size if item.exists() else 0,
                        "error_count": 0,  # Will be populated by analysis
                        "warning_count": 0  # Will be populated by analysis
                    }
                    tree_nodes.append(node)
            
            return tree_nodes
            
        except Exception as e:
            print(f"Error building file tree: {e}")
            return []
    
    def _count_files_in_directory(self, directory: Path) -> int:
        """Count files in a directory (non-recursive)."""
        try:
            count = 0
            for item in directory.iterdir():
                if item.is_file() and not item.name.startswith('.'):
                    count += 1
            return count
        except Exception:
            return 0
    
    def toggle_directory(self, directory_path: str):
        """Toggle directory expansion state."""
        if directory_path in self.expanded_directories:
            self.expanded_directories.remove(directory_path)
        else:
            self.expanded_directories.append(directory_path)
        
        # Refresh the file tree to show/hide children
        return self.refresh_file_tree
    
    # File selection
    def select_file(self, file_path: str):
        """Select a file and load its details."""
        self.selected_file_path = file_path
        self._load_file_details()
    
    def clear_file_selection(self):
        """Clear the current file selection."""
        self.selected_file_path = ""
        self.selected_file_size = 0
        self.selected_file_lines = 0
        self.file_content = ""
        self.file_content_visible = False
    
    def _load_file_details(self):
        """Load details for the selected file."""
        if not self.selected_file_path:
            return
        
        try:
            file_path = Path(self.selected_file_path)
            if file_path.exists():
                # Get file size
                self.selected_file_size = file_path.stat().st_size
                
                # Count lines (for text files)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        self.selected_file_lines = len(f.readlines())
                except Exception:
                    self.selected_file_lines = 0
            else:
                self.selected_file_size = 0
                self.selected_file_lines = 0
                
        except Exception as e:
            print(f"Error loading file details: {e}")
            self.selected_file_size = 0
            self.selected_file_lines = 0
    
    # File content operations
    async def view_file_content(self):
        """Load and display file content."""
        if not self.selected_file_path:
            return
        
        self.file_content_loading = True
        self.file_content_visible = True
        
        try:
            file_path = Path(self.selected_file_path)
            if file_path.exists():
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Limit content size for display
                if len(content) > 50000:  # 50KB limit
                    content = content[:50000] + "\n\n... (content truncated)"
                
                self.file_content = content
            else:
                self.file_content = "File not found"
                
        except Exception as e:
            self.file_content = f"Error reading file: {str(e)}"
        finally:
            self.file_content_loading = False
    
    def hide_file_content(self):
        """Hide the file content viewer."""
        self.file_content_visible = False
    
    async def analyze_file(self):
        """Analyze the selected file (placeholder for future implementation)."""
        if not self.selected_file_path:
            return
        
        # This will be implemented when we add the analysis engine
        print(f"Analyzing file: {self.selected_file_path}")
    
    # Search and filtering
    def set_file_search_query(self, query: str):
        """Set the file search query."""
        self.file_search_query = query
    
    def toggle_python_files(self, checked: bool):
        """Toggle Python file visibility."""
        self.show_python_files = checked
    
    def toggle_typescript_files(self, checked: bool):
        """Toggle TypeScript file visibility."""
        self.show_typescript_files = checked
    
    def toggle_other_files(self, checked: bool):
        """Toggle other file visibility."""
        self.show_other_files = checked
    
    # Computed properties
    @rx.var
    def selected_file_name(self) -> str:
        """Get the name of the selected file."""
        if self.selected_file_path:
            return Path(self.selected_file_path).name
        return ""
    
    @rx.var
    def selected_file_language(self) -> str:
        """Get the language for syntax highlighting."""
        if not self.selected_file_path:
            return "text"
        
        extension = Path(self.selected_file_path).suffix.lower()
        language_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".json": "json",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".toml": "toml",
            ".cfg": "ini",
            ".ini": "ini",
        }
        
        return language_map.get(extension, "text")
    
    @rx.var
    def filtered_file_tree(self) -> List[Dict[str, Any]]:
        """Get the filtered file tree based on search and filters."""
        if not self.file_tree:
            return []
        
        # Apply search filter
        filtered_tree = self._filter_tree_by_search(self.file_tree, self.file_search_query)
        
        # Apply file type filters
        filtered_tree = self._filter_tree_by_type(filtered_tree)
        
        return filtered_tree
    
    def _filter_tree_by_search(self, tree: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Filter tree nodes by search query."""
        if not query:
            return tree
        
        filtered = []
        query_lower = query.lower()
        
        for node in tree:
            if node["is_directory"]:
                # For directories, check if name matches or if any children match
                children = self._filter_tree_by_search(node.get("children", []), query)
                if query_lower in node["name"].lower() or children:
                    filtered_node = node.copy()
                    filtered_node["children"] = children
                    filtered.append(filtered_node)
            else:
                # For files, check if name matches
                if query_lower in node["name"].lower():
                    filtered.append(node)
        
        return filtered
    
    def _filter_tree_by_type(self, tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter tree nodes by file type."""
        filtered = []
        
        for node in tree:
            if node["is_directory"]:
                # For directories, filter children
                children = self._filter_tree_by_type(node.get("children", []))
                if children:  # Only include directory if it has visible children
                    filtered_node = node.copy()
                    filtered_node["children"] = children
                    filtered.append(filtered_node)
            else:
                # For files, check extension
                extension = node.get("extension", "").lower()
                
                should_include = False
                if extension in [".py"] and self.show_python_files:
                    should_include = True
                elif extension in [".ts", ".tsx", ".js", ".jsx"] and self.show_typescript_files:
                    should_include = True
                elif extension not in [".py", ".ts", ".tsx", ".js", ".jsx"] and self.show_other_files:
                    should_include = True
                
                if should_include:
                    filtered.append(node)
        
        return filtered
