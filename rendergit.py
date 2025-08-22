#!/usr/bin/env python3
"""
RenderGit: Interactive Dark Mode Codebase Explorer

A tool that flattens a GitHub repo into an interactive HTML page with dark mode
and graph-sitter visualizations for exploring code relationships.
"""

from __future__ import annotations
import argparse
import html
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union, Tuple

# External deps
import networkx as nx
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename, TextLexer
import markdown

# Constants
MAX_DEFAULT_BYTES = 50 * 1024
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico", ".pdf",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".mp3", ".mp4",
    ".mov", ".avi", ".mkv", ".wav", ".ogg", ".flac", ".ttf", ".otf", ".eot",
    ".woff", ".woff2", ".so", ".dll", ".dylib", ".class", ".jar", ".exe", ".bin",
}
MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd", ".mkdn"}

# Graph visualization constants
NODE_COLORS = {
    "file": "#4b5563",
    "directory": "#6366f1",
    "function": "#10b981",
    "class": "#f59e0b",
    "import": "#ec4899",
    "variable": "#8b5cf6",
    "root": "#ef4444",
}

# Visualization types
VISUALIZATION_TYPES = {
    "dependency": "Dependency Graph",
    "call_trace": "Call Trace",
    "blast_radius": "Blast Radius",
    "method_relationships": "Method Relationships",
}

@dataclass
class RenderDecision:
    include: bool
    reason: str  # "ok" | "binary" | "too_large" | "ignored"

@dataclass
class FileInfo:
    path: pathlib.Path  # absolute path on disk
    rel: str  # path relative to repo root (slash-separated)
    size: int
    decision: RenderDecision
    
    
def run(cmd: List[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def git_clone(url: str, dst: str) -> None:
    run(["git", "clone", "--depth", "1", url, dst])


def git_head_commit(repo_dir: str) -> str:
    try:
        cp = run(["git", "rev-parse", "HEAD"], cwd=repo_dir)
        return cp.stdout.strip()
    except Exception:
        return "(unknown)"


def bytes_human(n: int) -> str:
    """Human-readable bytes: 1 decimal for KiB and above, integer for B."""
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    f = float(n)
    i = 0
    while f >= 1024.0 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    if i == 0:
        return f"{int(f)} {units[i]}"
    else:
        return f"{f:.1f} {units[i]}"


def looks_binary(path: pathlib.Path) -> bool:
    ext = path.suffix.lower()
    if ext in BINARY_EXTENSIONS:
        return True
    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
            if b"\x00" in chunk:
                return True
            # Heuristic: try UTF-8 decode; if it hard-fails, likely binary
            try:
                chunk.decode("utf-8")
            except UnicodeDecodeError:
                return True
            return False
    except Exception:
        # If unreadable, treat as binary to be safe
        return True


def decide_file(path: pathlib.Path, repo_root: pathlib.Path, max_bytes: int) -> FileInfo:
    rel = str(path.relative_to(repo_root)).replace(os.sep, "/")
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        size = 0
    # Ignore VCS and build junk
    if "/.git/" in f"/{rel}/" or rel.startswith(".git/"):
        return FileInfo(path, rel, size, RenderDecision(False, "ignored"))
    if size > max_bytes:
        return FileInfo(path, rel, size, RenderDecision(False, "too_large"))
    if looks_binary(path):
        return FileInfo(path, rel, size, RenderDecision(False, "binary"))
    return FileInfo(path, rel, size, RenderDecision(True, "ok"))


def collect_files(repo_root: pathlib.Path, max_bytes: int) -> List[FileInfo]:
    infos: List[FileInfo] = []
    for p in sorted(repo_root.rglob("**/*")):
        if p.is_symlink():
            continue
        if p.is_file():
            infos.append(decide_file(p, repo_root, max_bytes))
    return infos


def generate_tree_fallback(root: pathlib.Path) -> str:
    """Minimal tree-like output if tree command is missing."""
    lines: List[str] = []
    prefix_stack: List[str] = []

    def walk(dir_path: pathlib.Path, prefix: str = ""):
        entries = [e for e in dir_path.iterdir() if e.name != ".git"]
        entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
        for i, e in enumerate(entries):
            last = i == len(entries) - 1
            branch = "└── " if last else "├── "
            lines.append(prefix + branch + e.name)
            if e.is_dir():
                extension = "    " if last else "│   "
                walk(e, prefix + extension)

    lines.append(root.name)
    walk(root)
    return "\n".join(lines)


def try_tree_command(root: pathlib.Path) -> str:
    try:
        cp = run(["tree", "-a", "-I", ".git", "."], cwd=str(root))
        return cp.stdout
    except Exception:
        return generate_tree_fallback(root)


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def render_markdown_text(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["fenced_code", "tables", "toc"])


def highlight_code(text: str, filename: str, formatter: HtmlFormatter) -> str:
    try:
        lexer = get_lexer_for_filename(filename, stripall=False)
    except Exception:
        lexer = TextLexer(stripall=False)
    return highlight(text, lexer, formatter)


def slugify(path_str: str) -> str:
    # Simple slug: keep alnum, dash, underscore; replace others with '-'
    out = []
    for ch in path_str:
        if ch.isalnum() or ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("-")
    return "".join(out)


def generate_cxml_text(infos: List[FileInfo], repo_dir: pathlib.Path) -> str:
    """Generate CXML format text for LLM consumption."""
    lines = ["<documents>"]

    rendered = [i for i in infos if i.decision.include]
    for index, i in enumerate(rendered, 1):
        lines.append(f'<document index="{index}">')
        lines.append(f"<source>{i.rel}</source>")
        lines.append("<document_content>")

        try:
            text = read_text(i.path)
            lines.append(text)
        except Exception as e:
            lines.append(f"Failed to read: {str(e)}")

        lines.append("</document_content>")
        lines.append("</document>")

    lines.append("</documents>")
    return "\n".join(lines)


def create_dependency_graph(infos: List[FileInfo]) -> nx.DiGraph:
    """Create a dependency graph based on imports between files."""
    G = nx.DiGraph()
    
    # Add all files as nodes
    for info in infos:
        if info.decision.include:
            G.add_node(info.rel, type="file", size=info.size, color=NODE_COLORS["file"])
    
    # Add edges based on imports
    for info in infos:
        if not info.decision.include:
            continue
            
        try:
            content = read_text(info.path)
            
            # Simple import detection for Python files
            if info.path.suffix.lower() == ".py":
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("import ") or line.startswith("from "):
                        # Very basic import parsing
                        imported = line.split()[1].split(".")[0]
                        for target in infos:
                            if target.decision.include and target.path.stem == imported:
                                G.add_edge(info.rel, target.rel, type="import")
            
            # Simple import detection for JavaScript/TypeScript files
            elif info.path.suffix.lower() in [".js", ".jsx", ".ts", ".tsx"]:
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("import ") and " from " in line:
                        imported = line.split(" from ")[1].strip().strip("'").strip('"')
                        if imported.startswith("."):
                            # Relative import
                            imported_path = os.path.normpath(os.path.join(os.path.dirname(info.rel), imported))
                            for target in infos:
                                if target.decision.include and target.rel.startswith(imported_path):
                                    G.add_edge(info.rel, target.rel, type="import")
        except Exception:
            # Skip files that can't be read
            pass
    
    return G


def create_call_graph(infos: List[FileInfo]) -> nx.DiGraph:
    """Create a simplified call graph based on function name occurrences."""
    G = nx.DiGraph()
    
    # Extract function definitions (very simplified)
    functions = {}
    for info in infos:
        if not info.decision.include:
            continue
            
        try:
            content = read_text(info.path)
            
            # Simple function detection for Python files
            if info.path.suffix.lower() == ".py":
                for i, line in enumerate(content.split("\n")):
                    line = line.strip()
                    if line.startswith("def "):
                        func_name = line[4:].split("(")[0].strip()
                        functions[func_name] = (info.rel, i)
                        G.add_node(f"{info.rel}:{func_name}", 
                                  type="function", 
                                  file=info.rel, 
                                  line=i,
                                  color=NODE_COLORS["function"])
            
            # Simple function detection for JavaScript/TypeScript files
            elif info.path.suffix.lower() in [".js", ".jsx", ".ts", ".tsx"]:
                for i, line in enumerate(content.split("\n")):
                    line = line.strip()
                    if "function " in line or "=> {" in line or "=> (" in line:
                        # Very basic function detection
                        if "function " in line:
                            func_name = line.split("function ")[1].split("(")[0].strip()
                        else:
                            parts = line.split("=")
                            if len(parts) > 1:
                                func_name = parts[0].strip()
                            else:
                                continue
                        
                        functions[func_name] = (info.rel, i)
                        G.add_node(f"{info.rel}:{func_name}", 
                                  type="function", 
                                  file=info.rel, 
                                  line=i,
                                  color=NODE_COLORS["function"])
        except Exception:
            # Skip files that can't be read
            pass
    
    # Find function calls
    for info in infos:
        if not info.decision.include:
            continue
            
        try:
            content = read_text(info.path)
            
            # Look for function calls
            for func_name, (file_rel, line_num) in functions.items():
                if func_name in content:
                    # This is a very simplified approach - in a real tool we'd use AST parsing
                    for i, line in enumerate(content.split("\n")):
                        if func_name + "(" in line and info.rel != file_rel:
                            caller = None
                            # Try to determine the calling function
                            for j in range(i, -1, -1):
                                prev_line = content.split("\n")[j].strip()
                                if prev_line.startswith("def ") or "function " in prev_line or "=> {" in prev_line:
                                    if prev_line.startswith("def "):
                                        caller_name = prev_line[4:].split("(")[0].strip()
                                    elif "function " in prev_line:
                                        caller_name = prev_line.split("function ")[1].split("(")[0].strip()
                                    else:
                                        parts = prev_line.split("=")
                                        if len(parts) > 1:
                                            caller_name = parts[0].strip()
                                        else:
                                            continue
                                    
                                    caller = f"{info.rel}:{caller_name}"
                                    break
                            
                            if caller and caller in G.nodes:
                                G.add_edge(caller, f"{file_rel}:{func_name}", type="call")
        except Exception:
            # Skip files that can't be read
            pass
    
    return G


def graph_to_json(G: nx.DiGraph) -> str:
    """Convert a NetworkX graph to JSON for visualization."""
    return json.dumps(nx.node_link_data(G), indent=2)


def derive_temp_output_path(repo_url: str) -> pathlib.Path:
    """Derive a temporary output path from the repo URL."""
    # Extract repo name from URL like https://github.com/owner/repo or https://github.com/owner/repo.git
    parts = repo_url.rstrip('/').split('/')
    if len(parts) >= 2:
        repo_name = parts[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        filename = f"{repo_name}.html"
    else:
        filename = "repo.html"

    return pathlib.Path(tempfile.gettempdir()) / filename


def main() -> int:
    ap = argparse.ArgumentParser(description="Interactive dark mode codebase explorer with graph-sitter visualizations")
    ap.add_argument("repo_url", help="GitHub repo URL (https://github.com/owner/repo[.git])")
    ap.add_argument("-o", "--out", help="Output HTML file path (default: temporary file derived from repo name)")
    ap.add_argument("--max-bytes", type=int, default=MAX_DEFAULT_BYTES, help="Max file size to render (bytes); larger files are listed but skipped")
    ap.add_argument("--no-open", action="store_true", help="Don't open the HTML file in browser after generation")
    args = ap.parse_args()

    # Set default output path if not provided
    if args.out is None:
        args.out = str(derive_temp_output_path(args.repo_url))

    tmpdir = tempfile.mkdtemp(prefix="rendergit_")
    repo_dir = pathlib.Path(tmpdir, "repo")

    try:
        print(f"📁 Cloning {args.repo_url} to temporary directory: {repo_dir}", file=sys.stderr)
        git_clone(args.repo_url, str(repo_dir))
        head = git_head_commit(str(repo_dir))
        print(f"✓ Clone complete (HEAD: {head[:8]})", file=sys.stderr)

        print(f"📊 Scanning files in {repo_dir}...", file=sys.stderr)
        infos = collect_files(repo_dir, args.max_bytes)
        rendered_count = sum(1 for i in infos if i.decision.include)
        skipped_count = len(infos) - rendered_count
        print(f"✓ Found {len(infos)} files total ({rendered_count} will be rendered, {skipped_count} skipped)", file=sys.stderr)

        print(f"🔨 Generating HTML with interactive visualizations...", file=sys.stderr)
        html_out = build_html(args.repo_url, repo_dir, head, infos)

        out_path = pathlib.Path(args.out)
        print(f"💾 Writing HTML file: {out_path.resolve()}", file=sys.stderr)
        out_path.write_text(html_out, encoding="utf-8")
        file_size = out_path.stat().st_size
        print(f"✓ Wrote {bytes_human(file_size)} to {out_path}", file=sys.stderr)

        if not args.no_open:
            print(f"🌐 Opening {out_path} in browser...", file=sys.stderr)
            webbrowser.open(f"file://{out_path.resolve()}")

        print(f"🗑️  Cleaning up temporary directory: {tmpdir}", file=sys.stderr)
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())


def build_html(repo_url: str, repo_dir: pathlib.Path, head_commit: str, infos: List[FileInfo]) -> str:
    # Create formatters for both light and dark themes
    light_formatter = HtmlFormatter(style="default")
    dark_formatter = HtmlFormatter(style="monokai")
    
    # Get CSS for both themes
    light_pygments_css = light_formatter.get_style_defs('.light-theme .highlight')
    dark_pygments_css = dark_formatter.get_style_defs('.dark-theme .highlight')

    # Stats
    rendered = [i for i in infos if i.decision.include]
    skipped_binary = [i for i in infos if i.decision.reason == "binary"]
    skipped_large = [i for i in infos if i.decision.reason == "too_large"]
    skipped_ignored = [i for i in infos if i.decision.reason == "ignored"]
    total_files = len(rendered) + len(skipped_binary) + len(skipped_large) + len(skipped_ignored)

    # Directory tree
    tree_text = try_tree_command(repo_dir)

    # Generate CXML text for LLM view
    cxml_text = generate_cxml_text(infos, repo_dir)
    
    # Generate graph visualizations
    dependency_graph = create_dependency_graph(infos)
    call_graph = create_call_graph(infos)
    
    # Convert graphs to JSON
    dependency_graph_json = graph_to_json(dependency_graph)
    call_graph_json = graph_to_json(call_graph)

    # Table of contents
    toc_items: List[str] = []
    for i in rendered:
        anchor = slugify(i.rel)
        toc_items.append(
            f'<li><a href="#file-{anchor}">{html.escape(i.rel)}</a> '
            f'<span class="muted">({bytes_human(i.size)})</span></li>'
        )
    toc_html = "".join(toc_items)

    # Render file sections
    sections: List[str] = []
    for i in rendered:
        anchor = slugify(i.rel)
        p = i.path
        ext = p.suffix.lower()
        try:
            text = read_text(p)
            if ext in MARKDOWN_EXTENSIONS:
                body_html = render_markdown_text(text)
            else:
                # Use light theme formatter by default (theme switching is handled by CSS)
                code_html = highlight_code(text, i.rel, light_formatter)
                body_html = f'<div class="highlight">{code_html}</div>'
        except Exception as e:
            body_html = f'<pre class="error">Failed to render: {html.escape(str(e))}</pre>'
        sections.append(f"""
<section class="file-section" id="file-{anchor}">
    <h2>{html.escape(i.rel)} <span class="muted">({bytes_human(i.size)})</span></h2>
    <div class="file-body">{body_html}</div>
    <div class="back-top"><a href="#top">↑ Back to top</a></div>
</section>
""")

    # Skips lists
    def render_skip_list(title: str, items: List[FileInfo]) -> str:
        if not items:
            return ""
        lis = [
            f"<li><code>{html.escape(i.rel)}</code> "
            f"<span class='muted'>({bytes_human(i.size)})</span></li>"
            for i in items
        ]
        return (
            f"<details open><summary>{html.escape(title)} ({len(items)})</summary>"
            f"<ul class='skip-list'>\n" + "\n".join(lis) + "\n</ul></details>"
        )

    skipped_html = (
        render_skip_list("Skipped binaries", skipped_binary) +
        render_skip_list("Skipped large files", skipped_large)
    )

    # HTML with left sidebar TOC and dark mode support
    return f"""
<!DOCTYPE html>
<html lang="en" class="light-theme">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>RenderGit – {html.escape(repo_url)}</title>
    <style>
        /* CSS Variables for theming */
        :root.light-theme {{
            --bg-color: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #f1f3f5;
            --text-color: #212529;
            --text-muted: #6c757d;
            --border-color: #e9ecef;
            --link-color: #0366d6;
            --link-hover: #0056b3;
            --code-bg: #f6f8fa;
            --error-color: #b00020;
            --error-bg: #fff3f3;
            --highlight-color: #f8f9fa;
            --active-btn-bg: #0366d6;
            --active-btn-color: white;
            --hover-btn-bg: #f6f8fa;
            --sidebar-bg: #fafbfc;
            --sidebar-border: #eee;
            --node-file: #4b5563;
            --node-directory: #6366f1;
            --node-function: #10b981;
            --node-class: #f59e0b;
            --node-import: #ec4899;
            --node-variable: #8b5cf6;
            --node-root: #ef4444;
        }}
        
        :root.dark-theme {{
            --bg-color: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-color: #c9d1d9;
            --text-muted: #8b949e;
            --border-color: #30363d;
            --link-color: #58a6ff;
            --link-hover: #79c0ff;
            --code-bg: #161b22;
            --error-color: #f85149;
            --error-bg: #3d1a1a;
            --highlight-color: #161b22;
            --active-btn-bg: #1f6feb;
            --active-btn-color: white;
            --hover-btn-bg: #21262d;
            --sidebar-bg: #161b22;
            --sidebar-border: #30363d;
            --node-file: #8b949e;
            --node-directory: #a5b4fc;
            --node-function: #34d399;
            --node-class: #fbbf24;
            --node-import: #f472b6;
            --node-variable: #a78bfa;
            --node-root: #f87171;
        }}
        
        /* Base styles */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, 'Apple Color Emoji','Segoe UI Emoji';
            margin: 0;
            padding: 0;
            line-height: 1.45;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 1rem;
        }}
        
        .meta small {{
            color: var(--text-muted);
        }}
        
        .counts {{
            margin-top: 0.25rem;
            color: var(--text-color);
        }}
        
        .muted {{
            color: var(--text-muted);
            font-weight: normal;
            font-size: 0.9em;
        }}
        
        a {{
            color: var(--link-color);
            text-decoration: none;
        }}
        
        a:hover {{
            color: var(--link-hover);
            text-decoration: underline;
        }}
        
        /* Layout with sidebar */
        .page {{
            display: grid;
            grid-template-columns: 320px minmax(0,1fr);
            gap: 0;
        }}
        
        #sidebar {{
            position: sticky;
            top: 0;
            align-self: start;
            height: 100vh;
            overflow: auto;
            border-right: 1px solid var(--sidebar-border);
            background: var(--sidebar-bg);
            transition: background-color 0.3s ease, border-color 0.3s ease;
        }}
        
        #sidebar .sidebar-inner {{
            padding: 0.75rem;
        }}
        
        #sidebar h2 {{
            margin: 0 0 0.5rem 0;
            font-size: 1rem;
        }}
        
        .toc {{
            list-style: none;
            padding-left: 0;
            margin: 0;
            overflow-x: auto;
        }}
        
        .toc li {{
            padding: 0.15rem 0;
            white-space: nowrap;
        }}
        
        .toc a {{
            text-decoration: none;
            display: inline-block;
        }}
        
        main.container {{
            padding-top: 1rem;
        }}
        
        pre {{
            background: var(--code-bg);
            padding: 0.75rem;
            overflow: auto;
            border-radius: 6px;
            transition: background-color 0.3s ease;
        }}
        
        code {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono','Courier New', monospace;
        }}
        
        .highlight {{
            overflow-x: auto;
        }}
        
        .file-section {{
            padding: 1rem;
            border-top: 1px solid var(--border-color);
            transition: border-color 0.3s ease;
        }}
        
        .file-section h2 {{
            margin: 0 0 0.5rem 0;
            font-size: 1.1rem;
        }}
        
        .file-body {{
            margin-bottom: 0.5rem;
        }}
        
        .back-top {{
            font-size: 0.9rem;
        }}
        
        .skip-list code {{
            background: var(--code-bg);
            padding: 0.1rem 0.3rem;
            border-radius: 4px;
            transition: background-color 0.3s ease;
        }}
        
        .error {{
            color: var(--error-color);
            background: var(--error-bg);
            transition: color 0.3s ease, background-color 0.3s ease;
        }}
        
        /* Hide duplicate top TOC on wide screens */
        .toc-top {{
            display: block;
        }}
        
        @media (min-width: 1000px) {{
            .toc-top {{
                display: none;
            }}
        }}
        
        :target {{
            scroll-margin-top: 8px;
        }}
        
        /* View toggle */
        .view-toggle {{
            margin: 1rem 0;
            display: flex;
            gap: 0.5rem;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .toggle-btn {{
            padding: 0.5rem 1rem;
            border: 1px solid var(--border-color);
            background: var(--bg-color);
            cursor: pointer;
            border-radius: 6px;
            font-size: 0.9rem;
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
        }}
        
        .toggle-btn.active {{
            background: var(--active-btn-bg);
            color: var(--active-btn-color);
            border-color: var(--active-btn-bg);
        }}
        
        .toggle-btn:hover:not(.active) {{
            background: var(--hover-btn-bg);
        }}
        
        /* Theme toggle */
        .theme-toggle {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 100;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .theme-toggle-btn {{
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            background: var(--bg-color);
            cursor: pointer;
            border-radius: 6px;
            font-size: 1rem;
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
        }}
        
        .theme-toggle-btn:hover {{
            background: var(--hover-btn-bg);
        }}
        
        /* Views */
        .view {{
            display: none;
        }}
        
        .view.active {{
            display: block;
        }}
        
        /* LLM view */
        #llm-text {{
            width: 100%;
            height: 70vh;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.85em;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1rem;
            resize: vertical;
            background-color: var(--bg-secondary);
            color: var(--text-color);
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
        }}
        
        .copy-hint {{
            margin-top: 0.5rem;
            color: var(--text-muted);
            font-size: 0.9em;
        }}
        
        /* Graph visualization */
        #graph-container {{
            width: 100%;
            height: 70vh;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background-color: var(--bg-secondary);
            transition: background-color 0.3s ease, border-color 0.3s ease;
        }}
        
        .graph-controls {{
            margin-top: 1rem;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}
        
        .graph-controls select, .graph-controls input {{
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background-color: var(--bg-color);
            color: var(--text-color);
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
        }}
        
        .graph-legend {{
            margin-top: 1rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .legend-color {{
            width: 1rem;
            height: 1rem;
            border-radius: 3px;
        }}
        
        /* Pygments for light theme */
        {light_pygments_css}
        
        /* Pygments for dark theme */
        {dark_pygments_css}
    </style>
    <!-- D3.js for graph visualization -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
    <a id="top"></a>
    
    <!-- Theme toggle -->
    <div class="theme-toggle">
        <button class="theme-toggle-btn" id="theme-toggle" title="Toggle dark/light mode">
            <span id="theme-icon">🌙</span>
        </button>
    </div>
    
    <div class="page">
        <nav id="sidebar">
            <div class="sidebar-inner">
                <h2>Contents ({len(rendered)})</h2>
                <ul class="toc toc-sidebar">
                    <li><a href="#top">↑ Back to top</a></li>
                    {toc_html}
                </ul>
            </div>
        </nav>
        
        <main class="container">
            <section>
                <div class="meta">
                    <div><strong>Repository:</strong> <a href="{html.escape(repo_url)}">{html.escape(repo_url)}</a></div>
                    <small><strong>HEAD commit:</strong> {html.escape(head_commit)}</small>
                    <div class="counts">
                        <strong>Total files:</strong> {total_files} · <strong>Rendered:</strong> {len(rendered)} · <strong>Skipped:</strong> {len(skipped_binary) + len(skipped_large) + len(skipped_ignored)}
                    </div>
                </div>
            </section>

            <div class="view-toggle">
                <strong>View:</strong>
                <button class="toggle-btn active" data-view="human-view">👤 Human</button>
                <button class="toggle-btn" data-view="graph-view">📊 Graph</button>
                <button class="toggle-btn" data-view="llm-view">🤖 LLM</button>
            </div>

            <div id="human-view" class="view active">
                <section>
                    <h2>Directory tree</h2>
                    <pre>{html.escape(tree_text)}</pre>
                </section>

                <section class="toc-top">
                    <h2>Table of contents ({len(rendered)})</h2>
                    <ul class="toc">{toc_html}</ul>
                </section>

                <section>
                    <h2>Skipped items</h2>
                    {skipped_html}
                </section>

                {''.join(sections)}
            </div>

            <div id="graph-view" class="view">
                <section>
                    <h2>📊 Interactive Code Graph</h2>
                    <p>Explore code relationships and dependencies visually:</p>
                    
                    <div class="graph-controls">
                        <select id="graph-type">
                            <option value="dependency">Dependency Graph</option>
                            <option value="call">Call Graph</option>
                        </select>
                        
                        <input type="text" id="graph-search" placeholder="Search nodes...">
                        
                        <button class="toggle-btn" id="graph-zoom-in">Zoom In</button>
                        <button class="toggle-btn" id="graph-zoom-out">Zoom Out</button>
                        <button class="toggle-btn" id="graph-reset">Reset</button>
                    </div>
                    
                    <div id="graph-container"></div>
                    
                    <div class="graph-legend">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: var(--node-file);"></div>
                            <span>File</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: var(--node-directory);"></div>
                            <span>Directory</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: var(--node-function);"></div>
                            <span>Function</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: var(--node-class);"></div>
                            <span>Class</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: var(--node-import);"></div>
                            <span>Import</span>
                        </div>
                    </div>
                </section>
            </div>

            <div id="llm-view" class="view">
                <section>
                    <h2>🤖 LLM View - CXML Format</h2>
                    <p>Copy the text below and paste it to an LLM for analysis:</p>
                    <textarea id="llm-text" readonly>{html.escape(cxml_text)}</textarea>
                    <div class="copy-hint">
                        💡 <strong>Tip:</strong> Click in the text area and press Ctrl+A (Cmd+A on Mac) to select all, then Ctrl+C (Cmd+C) to copy.
                    </div>
                </section>
            </div>
        </main>
    </div>
    
    <script>
        // Store graph data
        const graphData = {{
            dependency: {dependency_graph_json},
            call: {call_graph_json}
        }};
        
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        const themeIcon = document.getElementById('theme-icon');
        const htmlRoot = document.documentElement;
        
        // Check for saved theme preference or use system preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {{
            htmlRoot.className = savedTheme;
            updateThemeIcon();
        }} else {{
            // Check system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
                htmlRoot.className = 'dark-theme';
                updateThemeIcon();
            }}
        }}
        
        // Update theme icon based on current theme
        function updateThemeIcon() {{
            if (htmlRoot.className === 'dark-theme') {{
                themeIcon.textContent = '☀️';
            }} else {{
                themeIcon.textContent = '🌙';
            }}
        }}
        
        // Toggle theme
        themeToggle.addEventListener('click', () => {{
            if (htmlRoot.className === 'dark-theme') {{
                htmlRoot.className = 'light-theme';
            }} else {{
                htmlRoot.className = 'dark-theme';
            }}
            updateThemeIcon();
            localStorage.setItem('theme', htmlRoot.className);
            
            // If graph is active, redraw it
            if (document.getElementById('graph-view').classList.contains('active')) {{
                renderGraph(currentGraphType);
            }}
        }});
        
        // View toggle
        const viewButtons = document.querySelectorAll('.toggle-btn[data-view]');
        const views = document.querySelectorAll('.view');
        
        viewButtons.forEach(button => {{
            button.addEventListener('click', () => {{
                // Update active button
                viewButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Update active view
                const viewId = button.getAttribute('data-view');
                views.forEach(view => {{
                    view.classList.remove('active');
                    if (view.id === viewId) {{
                        view.classList.add('active');
                        
                        // If switching to graph view, render the graph
                        if (viewId === 'graph-view') {{
                            renderGraph(currentGraphType);
                        }}
                        
                        // If switching to LLM view, auto-select text
                        if (viewId === 'llm-view') {{
                            setTimeout(() => {{
                                const textArea = document.getElementById('llm-text');
                                textArea.focus();
                                textArea.select();
                            }}, 100);
                        }}
                    }}
                }});
            }});
        }});
        
        // Graph visualization
        let currentGraphType = 'dependency';
        let simulation;
        let svg;
        let g;
        let zoom;
        
        // Graph type selector
        const graphTypeSelect = document.getElementById('graph-type');
        graphTypeSelect.addEventListener('change', () => {{
            currentGraphType = graphTypeSelect.value;
            renderGraph(currentGraphType);
        }});
        
        // Graph search
        const graphSearch = document.getElementById('graph-search');
        graphSearch.addEventListener('input', () => {{
            const searchTerm = graphSearch.value.toLowerCase();
            
            // Highlight matching nodes
            if (svg) {{
                svg.selectAll('.node')
                    .classed('highlight', d => {{
                        if (!searchTerm) return false;
                        return d.id.toLowerCase().includes(searchTerm);
                    }});
            }}
        }});
        
        // Zoom controls
        document.getElementById('graph-zoom-in').addEventListener('click', () => {{
            svg.transition().duration(500).call(zoom.scaleBy, 1.5);
        }});
        
        document.getElementById('graph-zoom-out').addEventListener('click', () => {{
            svg.transition().duration(500).call(zoom.scaleBy, 0.75);
        }});
        
        document.getElementById('graph-reset').addEventListener('click', () => {{
            svg.transition().duration(500).call(
                zoom.transform,
                d3.zoomIdentity.translate(0, 0).scale(1)
            );
        }});
        
        function renderGraph(type) {{
            const container = document.getElementById('graph-container');
            container.innerHTML = '';
            
            const data = graphData[type];
            if (!data || !data.nodes || data.nodes.length === 0) {{
                container.innerHTML = '<div class="error" style="padding: 2rem; text-align: center;">No graph data available for this view.</div>';
                return;
            }}
            
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            // Create SVG
            svg = d3.select('#graph-container')
                .append('svg')
                .attr('width', width)
                .attr('height', height)
                .attr('viewBox', [0, 0, width, height])
                .attr('style', 'max-width: 100%; height: auto;');
            
            // Add zoom behavior
            zoom = d3.zoom()
                .scaleExtent([0.1, 10])
                .on('zoom', (event) => {{
                    g.attr('transform', event.transform);
                }});
            
            svg.call(zoom);
            
            // Create container for graph
            g = svg.append('g');
            
            // Create links
            const links = g.selectAll('.link')
                .data(data.links)
                .enter()
                .append('line')
                .attr('class', 'link')
                .attr('stroke', 'var(--text-muted)')
                .attr('stroke-width', 1.5)
                .attr('stroke-opacity', 0.6);
            
            // Create nodes
            const nodes = g.selectAll('.node')
                .data(data.nodes)
                .enter()
                .append('circle')
                .attr('class', 'node')
                .attr('r', d => d.type === 'file' ? 5 : 7)
                .attr('fill', d => {{
                    if (d.color) return d.color;
                    return `var(--node-${{d.type || 'file'}})`;
                }})
                .attr('stroke', 'var(--bg-color)')
                .attr('stroke-width', 1.5)
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));
            
            // Add tooltips
            nodes.append('title')
                .text(d => d.id);
            
            // Add labels
            const labels = g.selectAll('.label')
                .data(data.nodes)
                .enter()
                .append('text')
                .attr('class', 'label')
                .attr('dx', 12)
                .attr('dy', '.35em')
                .text(d => {{
                    if (d.type === 'function') {{
                        // For functions, show only the function name
                        return d.id.split(':').pop();
                    }}
                    // For files, show the filename without the path
                    return d.id.split('/').pop();
                }})
                .attr('fill', 'var(--text-color)')
                .attr('font-size', '10px');
            
            // Create simulation
            simulation = d3.forceSimulation(data.nodes)
                .force('link', d3.forceLink(data.links).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(30))
                .on('tick', () => {{
                    links
                        .attr('x1', d => d.source.x)
                        .attr('y1', d => d.source.y)
                        .attr('x2', d => d.target.x)
                        .attr('y2', d => d.target.y);
                    
                    nodes
                        .attr('cx', d => d.x)
                        .attr('cy', d => d.y);
                    
                    labels
                        .attr('x', d => d.x)
                        .attr('y', d => d.y);
                }});
            
            // Drag functions
            function dragstarted(event, d) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }}
            
            function dragged(event, d) {{
                d.fx = event.x;
                d.fy = event.y;
            }}
            
            function dragended(event, d) {{
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }}
        }}
        
        // Auto-select text in LLM view when clicking in the textarea
        document.getElementById('llm-text').addEventListener('click', function() {{
            this.select();
        }});
    </script>
</body>
</html>
"""
