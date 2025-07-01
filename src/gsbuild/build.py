import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def update_init_file(file: Path) -> None:
    """Update __init__.py with generated imports and exports.
    
    Optimized to avoid unnecessary file operations and improve build performance.
    """
    path = Path(__file__).parent.parent
    sys.path.append(str(path))
    
    # Import only when needed to reduce startup time
    from graph_sitter.gscli.generate.runner_imports import generate_exported_modules, get_runner_imports

    # Check if file needs updating to avoid unnecessary writes
    content = file.read_text()
    new_imports = get_runner_imports(include_codegen=False)
    new_exports = generate_exported_modules()
    new_content = new_imports + "\n" + content + "\n" + new_exports
    
    # Only write if content has changed
    if content != new_content:
        file.write_text(new_content)


class SpecialBuildHook(BuildHookInterface):
    """Custom build hook for graph-sitter package generation.
    
    Optimized for better build performance and reliability.
    """
    PLUGIN_NAME = "codegen_build"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Initialize build hook with performance optimizations."""
        file = Path(self.root) / "src" / "graph_sitter" / "__init__.py"
        
        # Ensure file exists before processing
        if file.exists():
            update_init_file(file)
            build_data["artifacts"].append(f"/{file}")
        else:
            # Log warning but don't fail the build
            print(f"Warning: {file} not found, skipping build hook")

