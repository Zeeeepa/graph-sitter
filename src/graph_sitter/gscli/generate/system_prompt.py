import json
from pathlib import Path
from typing import Optional, List

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def find_docs_directory() -> Optional[Path]:
    """Find the docs directory, checking multiple possible locations."""
    current_dir = Path.cwd()
    
    # Check common locations for docs directory
    possible_locations = [
        current_dir / "docs",
        current_dir.parent / "docs", 
        current_dir / "../docs",
        Path("./docs"),
    ]
    
    for location in possible_locations:
        try:
            resolved_path = location.resolve()
            if resolved_path.exists() and resolved_path.is_dir():
                mint_file = resolved_path / "mint.json"
                if mint_file.exists():
                    return resolved_path
        except (OSError, RuntimeError):
            continue
    
    return None


def render_page(docs_dir: Path, page_str: str) -> str:
    """Render a single page, handling missing files gracefully."""
    try:
        page_file = docs_dir / (page_str + ".mdx")
        if page_file.exists():
            return page_file.read_text(encoding="utf-8")
        else:
            logger.warning(f"Page file not found: {page_file}")
            return f"<!-- Page not found: {page_str} -->"
    except Exception as e:
        logger.error(f"Error reading page {page_str}: {e}")
        return f"<!-- Error reading page: {page_str} -->"


def render_group(docs_dir: Path, page_strs: List[str]) -> str:
    """Render a group of pages."""
    return "\\n\\n".join([render_page(docs_dir, x) for x in page_strs])


def get_group(mint_data: dict, name: str) -> Optional[List[str]]:
    """Get a group from mint.json navigation."""
    try:
        group = next((x for x in mint_data["navigation"] if x.get("group") == name), None)
        if group:
            return group["pages"]
        return None
    except (KeyError, TypeError) as e:
        logger.error(f"Error getting group {name}: {e}")
        return None


def render_groups(docs_dir: Path, mint_data: dict, group_names: List[str]) -> str:
    """Render multiple groups."""
    rendered_groups = []
    
    for group_name in group_names:
        group_pages = get_group(mint_data, group_name)
        if group_pages:
            rendered_group = render_group(docs_dir, group_pages)
            rendered_groups.append(rendered_group)
        else:
            logger.warning(f"Group not found: {group_name}")
    
    return "\\n\\n".join(rendered_groups)


def get_system_prompt() -> str:
    """Generates a string system prompt based on the docs"""
    try:
        docs_dir = find_docs_directory()
        
        if not docs_dir:
            logger.error("Could not find docs directory")
            return "# System Prompt\\n\\nError: Documentation directory not found."
        
        mint_file = docs_dir / "mint.json"
        
        if not mint_file.exists():
            logger.error(f"mint.json not found at {mint_file}")
            return "# System Prompt\\n\\nError: mint.json not found."
        
        try:
            with open(mint_file, encoding="utf-8") as f:
                mint_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in mint.json: {e}")
            return "# System Prompt\\n\\nError: Invalid mint.json format."
        
        return render_groups(docs_dir, mint_data, ["Introduction", "Building with Codegen", "Tutorials"])
        
    except Exception as e:
        logger.error(f"Error generating system prompt: {e}")
        return f"# System Prompt\\n\\nError generating system prompt: {e}"
