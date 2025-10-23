"""
NPM Package Analyzer Pro - Ultimate Edition
A comprehensive tool for discovering, analyzing, and downloading NPM packages
with advanced features, proper markdown rendering, and high-performance concurrency.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import sqlite3
import os
import subprocess
import threading
import concurrent.futures
import datetime
import time
import random
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional, Tuple, Union, Sequence, Callable, Any, cast
from dataclasses import dataclass, asdict, field
import platform
import sys
import re
from urllib.parse import urlparse, urljoin
import webbrowser
import configparser
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.extra import ExtraExtension
import html
import base64
from bs4 import BeautifulSoup, Tag, Tag
from bs4.element import NavigableString
import queue
import hashlib
import zlib
from functools import lru_cache, partial
import tkinter.font as tkfont
import mimetypes
import tempfile
import shutil
from pathlib import Path
import humanize
import dateutil.parser
from dateutil.relativedelta import relativedelta
import tarfile
import zipfile
import io


# Rate limiting
from collections import deque
from threading import Lock

class RateLimiter:
    def __init__(self, max_calls=2, time_window=1.0):
        self.max_calls, self.time_window, self.calls, self.lock = max_calls, time_window, deque(), Lock()
    def wait_if_needed(self):
        import time
        with self.lock:
            now = time.time()
            self.calls = deque([c for c in self.calls if c > now - self.time_window])
            if len(self.calls) >= self.max_calls and self.calls:
                time.sleep(max(0, self.time_window - (now - self.calls[0]) + 0.1))
            self.calls.append(time.time())

npm_rate_limiter = RateLimiter()

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('npm_analyzer.log', maxBytes=5*1024*1024, backupCount=2),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
CACHE_DB = "npm_cache.db"
SEARCH_HISTORY_DB = "search_history.db"
SETTINGS_FILE = "npm_analyzer_settings.ini"
CACHE_TTL_DAYS = 7
DEFAULT_MAX_CONCURRENT_REQUESTS = 40
REQUEST_TIMEOUT = 30
DEFAULT_MAX_RESULTS = 50000
MAX_SEARCH_HISTORY = 20
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "npm_packages")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Modern Dark Theme with color gradients
class Theme:
    BG = "#0D1117"
    BG_SECONDARY = "#161B22"
    BG_TERTIARY = "#21262D"
    BG_HOVER = "#30363D"
    BG_INPUT = "#010409"
    TEXT = "#E6EDF3"
    TEXT_SECONDARY = "#8B949E"
    TEXT_MUTED = "#6E7681"
    ACCENT = "#58A6FF"
    ACCENT_DARK = "#1F6FEB"
    SUCCESS = "#3FB950"
    SUCCESS_DARK = "#2EA043"
    WARNING = "#D29922"
    WARNING_DARK = "#B3881E"
    ERROR = "#F85149"
    ERROR_DARK = "#DA3633"
    BORDER = "#30363D"
    CODE_BG = "#2D3748"
    CODE_FG = "#E2E8F0"
    CODE_COMMENT = "#8B949E"
    CODE_KEYWORD = "#F97583"
    CODE_STRING = "#A5D6FF"
    CODE_NUMBER = "#B392F0"
    CODE_FUNCTION = "#FFE066"
    SCROLLBAR = "#484F58"
    BUTTON_HOVER = "#373E47"

    # Color gradients for sizes
    SIZE_KB_LIGHT = "#79C0FF"    # Light blue for small KB
    SIZE_KB_DARK = "#58A6FF"     # Darker blue for larger KB
    SIZE_MB_LIGHT = "#A371F7"    # Light purple for small MB
    SIZE_MB_DARK = "#7C3AED"     # Darker purple for larger MB
    SIZE_GB_LIGHT = "#FF7B72"    # Light red for small GB
    SIZE_GB_DARK = "#F85149"     # Darker red for larger GB

    # Color gradients for time
    TIME_VERY_RECENT = "#7EE787"  # Bright green for very recent (hours)
    TIME_RECENT = "#FFA657"       # Orange for recent (days)
    TIME_MEDIUM = "#D29922"       # Yellow for medium (weeks)
    TIME_OLD = "#8B949E"          # Gray for old (months+)

    @classmethod
    def get_code_theme(cls):
        return {
            'background': cls.CODE_BG,
            'highlight': '#3E4C5E',
            'comment': cls.CODE_COMMENT,
            'keyword': cls.CODE_KEYWORD,
            'name.builtin': cls.CODE_KEYWORD,
            'name.function': cls.CODE_FUNCTION,
            'name.class': cls.CODE_FUNCTION,
            'string': cls.CODE_STRING,
            'number': cls.CODE_NUMBER,
            'operator': cls.CODE_KEYWORD,
        }

class MarkdownRenderer:
    """Enhanced Markdown renderer with syntax highlighting and proper styling"""

    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        self._setup_tags()

    def _setup_tags(self):
        """Setup text widget tags for markdown styling"""
        # Headers
        self.text_widget.tag_config("h1", foreground=Theme.ACCENT, font=("Segoe UI", 18, "bold"), spacing3=10)
        self.text_widget.tag_config("h2", foreground=Theme.ACCENT, font=("Segoe UI", 16, "bold"), spacing3=8)
        self.text_widget.tag_config("h3", foreground=Theme.ACCENT, font=("Segoe UI", 14, "bold"), spacing3=6)
        self.text_widget.tag_config("h4", foreground=Theme.ACCENT, font=("Segoe UI", 12, "bold"), spacing3=4)
        self.text_widget.tag_config("h5", foreground=Theme.ACCENT, font=("Segoe UI", 11, "bold"))
        self.text_widget.tag_config("h6", foreground=Theme.ACCENT, font=("Segoe UI", 10, "bold"))

        # Text styles
        self.text_widget.tag_config("bold", font=("Segoe UI", 10, "bold"))
        self.text_widget.tag_config("italic", font=("Segoe UI", 10, "italic"))
        self.text_widget.tag_config("bold_italic", font=("Segoe UI", 10, "bold italic"))
        self.text_widget.tag_config("strikethrough", overstrike=True)
        self.text_widget.tag_config("link", foreground=Theme.ACCENT, underline=True)

        # Code styles
        self.text_widget.tag_config("code", background=Theme.CODE_BG, foreground=Theme.CODE_FG,
                                  font=("Consolas", 10), spacing3=2)
        self.text_widget.tag_config("codeblock", background=Theme.CODE_BG, foreground=Theme.CODE_FG,
                                  font=("Consolas", 10), lmargin1=20, lmargin2=20, spacing3=5)

        # Block styles
        self.text_widget.tag_config("blockquote", lmargin1=20, lmargin2=20, spacing3=5,
                                  foreground=Theme.TEXT_SECONDARY)
        self.text_widget.tag_config("pre", background=Theme.BG_TERTIARY, font=("Consolas", 10))

        # List styles
        self.text_widget.tag_config("list_item", lmargin1=20, lmargin2=20)
        self.text_widget.tag_config("ordered_list", lmargin1=20, lmargin2=20)
        self.text_widget.tag_config("unordered_list", lmargin1=20, lmargin2=20)

        # Table styles
        self.text_widget.tag_config("table", spacing3=5)
        self.text_widget.tag_config("table_header", font=("Segoe UI", 10, "bold"),
                                  background=Theme.BG_TERTIARY)
        self.text_widget.tag_config("table_cell", spacing3=2)

        # Syntax highlighting tags
        for token_type, color in Theme.get_code_theme().items():
            self.text_widget.tag_config(f"token.{token_type}", foreground=color)

    def render(self, markdown_text: str):
        """Render markdown text in the widget with full styling"""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)

        if not markdown_text or not markdown_text.strip():
            self.text_widget.insert(tk.END, "(No README available)")
            self.text_widget.config(state=tk.DISABLED)
            return

        try:
            # Convert markdown to HTML with extensions
            html_content = markdown.markdown(
                markdown_text,
                extensions=[
                    'tables',
                    FencedCodeExtension(),
                    CodeHiliteExtension(guess_lang=False, linenums=False),
                    ExtraExtension(),
                    TableExtension(),
                    TocExtension()
                ],
                output_format='html'
            )

            # Parse HTML and apply tags
            soup = BeautifulSoup(html_content, 'html.parser')
            self._parse_html(soup, self.text_widget)

        except Exception as e:
            logger.error(f"Error rendering markdown: {e}")
            # Fallback to plain text with basic formatting
            self._render_as_plain_text(markdown_text)

        self.text_widget.config(state=tk.DISABLED)

    def _render_as_plain_text(self, text: str):
        """Render as plain text with basic formatting"""
        lines = text.split('\n')
        in_code_block = False
        code_block_content = []

        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    self.text_widget.insert(tk.END, '\n'.join(code_block_content), "codeblock")
                    self.text_widget.insert(tk.END, '\n')
                    code_block_content = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                continue

            if in_code_block:
                code_block_content.append(line)
                continue

            # Handle headers
            if line.startswith('# '):
                self.text_widget.insert(tk.END, '\n', ())
                self.text_widget.insert(tk.END, line[2:] + '\n', "h1")
            elif line.startswith('## '):
                self.text_widget.insert(tk.END, '\n', ())
                self.text_widget.insert(tk.END, line[3:] + '\n', "h2")
            elif line.startswith('### '):
                self.text_widget.insert(tk.END, '\n', ())
                self.text_widget.insert(tk.END, line[4:] + '\n', "h3")
            elif line.startswith('#### '):
                self.text_widget.insert(tk.END, '\n', ())
                self.text_widget.insert(tk.END, line[5:] + '\n', "h4")
            elif line.startswith('##### '):
                self.text_widget.insert(tk.END, '\n', ())
                self.text_widget.insert(tk.END, line[6:] + '\n', "h5")
            elif line.startswith('###### '):
                self.text_widget.insert(tk.END, '\n', ())
                self.text_widget.insert(tk.END, line[7:] + '\n', "h6")
            elif line.strip().startswith('>'):
                # Blockquote
                self.text_widget.insert(tk.END, '\n', ())
                self.text_widget.insert(tk.END, line.strip()[1:] + '\n', "blockquote")
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                # List item
                self.text_widget.insert(tk.END, '• ' + line.strip()[2:] + '\n', "list_item")
            elif line.strip().startswith('1. '):
                # Ordered list
                self.text_widget.insert(tk.END, line + '\n', "ordered_list")
            elif line.strip() == '':
                self.text_widget.insert(tk.END, '\n', ())
            else:
                # Regular text with inline formatting
                formatted_line = self._format_inline_text(line)
                self.text_widget.insert(tk.END, formatted_line + '\n', ())

    def _format_inline_text(self, text: str) -> str:
        """Format inline text with bold, italic, code, and links"""
        # Simple regex-based formatting
        # Bold text **text**
        text = re.sub(r'\*\*(.*?)\*\*', lambda m: f'**{m.group(1)}**', text)
        # Italic text *text*
        text = re.sub(r'\*(.*?)\*', lambda m: f'*{m.group(1)}*', text)
        # Inline code `code`
        text = re.sub(r'`(.*?)`', lambda m: f'`{m.group(1)}`', text)
        # Links [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'[{m.group(1)}]({m.group(2)})', text)
        return text

    def _parse_html(self, element, widget, tag_stack=None, in_code_block=False):
        """Recursively parse HTML elements and apply tags"""
        if tag_stack is None:
            tag_stack = []

        for child in element.children:
            if child.name:
                current_tags = tag_stack.copy()
                new_tags = []

                # Handle opening tag
                if child.name == 'h1':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                    new_tags.append("h1")
                elif child.name == 'h2':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                    new_tags.append("h2")
                elif child.name == 'h3':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                    new_tags.append("h3")
                elif child.name == 'h4':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                    new_tags.append("h4")
                elif child.name == 'h5':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                    new_tags.append("h5")
                elif child.name == 'h6':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                    new_tags.append("h6")
                elif child.name == 'strong' or child.name == 'b':
                    new_tags.append("bold")
                elif child.name == 'em' or child.name == 'i':
                    new_tags.append("italic")
                elif child.name == 'u':
                    new_tags.append("underline")
                elif child.name == 'del' or child.name == 's':
                    new_tags.append("strikethrough")
                elif child.name == 'code':
                    if in_code_block:
                        new_tags.append("codeblock")
                    else:
                        new_tags.append("code")
                elif child.name == 'pre':
                    new_tags.append("pre")
                    in_code_block = True
                elif child.name == 'blockquote':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                    new_tags.append("blockquote")
                elif child.name == 'a':
                    new_tags.append("link")
                elif child.name == 'p':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                elif child.name == 'br':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                    continue
                elif child.name == 'hr':
                    widget.insert(tk.END, '\n' + '─' * 50 + '\n', tuple(current_tags))
                    continue
                elif child.name == 'ul':
                    new_tags.append("unordered_list")
                elif child.name == 'ol':
                    new_tags.append("ordered_list")
                elif child.name == 'li':
                    new_tags.append("list_item")
                    widget.insert(tk.END, "• ", tuple(current_tags + ["list_item"]))
                elif child.name == 'table':
                    new_tags.append("table")
                    widget.insert(tk.END, '\n', tuple(current_tags))
                elif child.name == 'thead':
                    new_tags.append("table_header")
                elif child.name == 'th' or child.name == 'td':
                    widget.insert(tk.END, ' ', tuple(current_tags))
                    if child.name == 'th':
                        new_tags.append("table_header")
                    else:
                        new_tags.append("table_cell")
                elif child.name == 'tr':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                elif child.name == 'div' and 'highlight' in child.get('class', []):
                    new_tags.append("codeblock")
                    code = child.get_text()
                    widget.insert(tk.END, code, tuple(current_tags + ["codeblock"]))
                    widget.insert(tk.END, '\n', tuple(current_tags + ["codeblock"]))
                    continue

                # Recursively process children with updated tag stack
                self._parse_html(child, widget, current_tags + new_tags, in_code_block)

                # Handle closing tag
                if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'blockquote', 'table']:
                    widget.insert(tk.END, '\n', tuple(current_tags))
                elif child.name == 'li':
                    widget.insert(tk.END, '\n', tuple(current_tags))
                elif child.name == 'tr':
                    widget.insert(tk.END, '\n', tuple(current_tags))
            else:
                # Handle text nodes
                text = str(child.string)
                if text.strip():
                    # Replace multiple spaces with single space
                    text = ' '.join(text.split())
                    widget.insert(tk.END, text, tuple(tag_stack))

@dataclass
class PackageInfo:
    """Enhanced NPM package information structure with caching and validation"""
    name: str
    version: str = ""
    description: str = ""
    author: str = ""
    license: str = ""
    homepage: str = ""
    repository: str = ""
    downloads_last_week: int = 0
    downloads_last_month: int = 0
    downloads_trend: str = "stable"
    size_unpacked: str = "Unknown"
    file_count: str = "Unknown"
    dependencies_count: int = 0
    dev_dependencies_count: int = 0
    peer_dependencies_count: int = 0
    total_versions: int = 0
    published_date: str = ""
    modified_date: str = ""
    last_publish: str = ""
    keywords: List[str] = field(default_factory=list)
    has_typescript: bool = False
    has_tests: bool = False
    has_readme: bool = False
    maintainers_count: int = 0
    maintainers: List[str] = field(default_factory=list)
    github_stars: str = "N/A"
    github_forks: str = "N/A"
    github_issues: str = "N/A"
    score_quality: float = 0.0
    score_popularity: float = 0.0
    score_maintenance: float = 0.0
    score_final: float = 0.0
    dependents: List[str] = field(default_factory=list)
    dependents_count: int = 0
    dependencies: List[str] = field(default_factory=list)
    readme: str = ""
    dependency_details: Dict[str, Dict] = field(default_factory=dict)
    dependent_details: Dict[str, Dict] = field(default_factory=dict)
    last_fetched: float = 0.0
    cache_key: str = ""
    file_tree: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize and validate fields"""
        self.last_fetched = time.time()
        self.cache_key = self._generate_cache_key()

    def _generate_cache_key(self) -> str:
        """Generate a cache key based on package name and version"""
        key_data = f"{self.name}:{self.version}".encode('utf-8')
        return hashlib.md5(key_data).hexdigest()

    def to_dict(self) -> Dict:
        """Convert to dictionary for caching"""
        d = asdict(self)
        d['keywords'] = json.dumps(self.keywords)
        d['maintainers'] = json.dumps(self.maintainers)
        d['dependencies'] = json.dumps(self.dependencies)
        d['dependents'] = json.dumps(self.dependents)
        d['dependency_details'] = json.dumps(self.dependency_details)
        d['dependent_details'] = json.dumps(self.dependent_details)
        d['file_tree'] = json.dumps(self.file_tree)
        return d

    @classmethod
    def from_dict(cls, data: Dict) -> 'PackageInfo':
        """Create from dictionary (from cache)"""
        if 'keywords' in data and isinstance(data['keywords'], str):
            try:
                data['keywords'] = json.loads(data['keywords'])
            except:
                data['keywords'] = []
        if 'maintainers' in data and isinstance(data['maintainers'], str):
            try:
                data['maintainers'] = json.loads(data['maintainers'])
            except:
                data['maintainers'] = []
        if 'dependencies' in data and isinstance(data['dependencies'], str):
            try:
                data['dependencies'] = json.loads(data['dependencies'])
            except:
                data['dependencies'] = []
        if 'dependents' in data and isinstance(data['dependents'], str):
            try:
                data['dependents'] = json.loads(data['dependents'])
            except:
                data['dependents'] = []
        if 'dependency_details' in data and isinstance(data['dependency_details'], str):
            try:
                data['dependency_details'] = json.loads(data['dependency_details'])
            except:
                data['dependency_details'] = {}
        if 'dependent_details' in data and isinstance(data['dependent_details'], str):
            try:
                data['dependent_details'] = json.loads(data['dependent_details'])
            except:
                data['dependent_details'] = {}
        if 'file_tree' in data and isinstance(data['file_tree'], str):
            try:
                data['file_tree'] = json.loads(data['file_tree'])
            except:
                data['file_tree'] = {}

        instance = cls(**data)
        instance.last_fetched = time.time()
        return instance

    def is_stale(self, ttl: int = 3600) -> bool:
        """Check if package data is stale"""
        return (time.time() - self.last_fetched) > ttl

    def humanize_size(self) -> str:
        """Return human-readable size"""
        if self.size_unpacked == "Unknown":
            return "Unknown"
        try:
            # Extract numeric value
            size_str = re.sub(r'[^\d.]', '', self.size_unpacked)
            if not size_str:
                return self.size_unpacked
            size = float(size_str)
            unit = re.search(r'[A-Za-z]+', self.size_unpacked)
            if unit:
                unit = unit.group(0).upper()
                if unit == 'KB':
                    size *= 1024
                elif unit == 'MB':
                    size *= 1024 * 1024
                elif unit == 'GB':
                    size *= 1024 * 1024 * 1024
            return humanize.naturalsize(size, binary=True)
        except:
            return self.size_unpacked

    def humanize_date(self, date_str: str) -> str:
        """Convert date string to human-readable format"""
        if not date_str or date_str == "Unknown":
            return "Unknown"
        try:
            date = dateutil.parser.parse(date_str)
            now = datetime.datetime.now()
            delta = relativedelta(now, date)
            if delta.years > 0:
                return f"{delta.years} year{'s' if delta.years > 1 else ''} ago"
            elif delta.months > 0:
                return f"{delta.months} month{'s' if delta.months > 1 else ''} ago"
            elif delta.days > 0:
                return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
            elif delta.hours > 0:
                return f"{delta.hours} hour{'s' if delta.hours > 1 else ''} ago"
            elif delta.minutes > 0:
                return f"{delta.minutes} minute{'s' if delta.minutes > 1 else ''} ago"
            else:
                return "Just now"
        except:
            return date_str

    def get_size_color(self) -> str:
        """Get color based on package size with gradient"""
        if self.size_unpacked == "Unknown":
            return Theme.TEXT_MUTED

        try:
            # Extract numeric value
            size_str = re.sub(r'[^\d.]', '', self.size_unpacked)
            if not size_str:
                return Theme.TEXT_MUTED

            size = float(size_str)
            unit = re.search(r'[A-Za-z]+', self.size_unpacked)
            if unit:
                unit = unit.group(0).upper()
                if unit == 'KB':
                    # Gradient from light to darker blue based on size
                    ratio = min(size / 100, 1.0)  # Normalize to 0-1, max at 100KB
                    return self._interpolate_color(Theme.SIZE_KB_LIGHT, Theme.SIZE_KB_DARK, ratio)
                elif unit == 'MB':
                    # Gradient from light to darker purple based on size
                    ratio = min(size / 10, 1.0)  # Normalize to 0-1, max at 10MB
                    return self._interpolate_color(Theme.SIZE_MB_LIGHT, Theme.SIZE_MB_DARK, ratio)
                elif unit == 'GB':
                    # Gradient from light to darker red based on size
                    ratio = min(size / 1, 1.0)  # Normalize to 0-1, max at 1GB
                    return self._interpolate_color(Theme.SIZE_GB_LIGHT, Theme.SIZE_GB_DARK, ratio)

            return Theme.TEXT_MUTED
        except:
            return Theme.TEXT_MUTED

    def _interpolate_color(self, color1: str, color2: str, ratio: float) -> str:
        """Interpolate between two colors"""
        try:
            # Convert hex to RGB
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

            # Interpolate
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)

            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color1

    def get_time_color(self) -> str:
        """Get color based on last publish time with gradient"""
        if self.last_publish == "Unknown":
            return Theme.TEXT_MUTED

        try:
            # Parse the human-readable time string
            if "hour" in self.last_publish:
                # Very recent - bright green
                hours_match = re.search(r'(\d+)', self.last_publish)
                if hours_match:
                    hours = int(hours_match.group(1))
                    # Gradient from bright to slightly dimmer green based on hours
                    ratio = min(hours / 24, 1.0)  # Normalize to 0-1 over 24 hours
                    return self._interpolate_color(Theme.TIME_VERY_RECENT, Theme.TIME_RECENT, ratio)
                return Theme.TIME_VERY_RECENT
            elif "day" in self.last_publish:
                # Days ago - orange
                days_match = re.search(r'(\d+)', self.last_publish)
                if days_match:
                    days = int(days_match.group(1))
                    if days <= 3:
                        # Recent days - brighter orange
                        ratio = min(days / 3, 1.0)
                        return self._interpolate_color(Theme.TIME_RECENT, Theme.TIME_MEDIUM, ratio)
                    else:
                        # Older days - yellow
                        ratio = min((days - 3) / 4, 1.0)  # Normalize over 4 days
                        return self._interpolate_color(Theme.TIME_MEDIUM, Theme.TIME_OLD, ratio)
                return Theme.TIME_RECENT
            elif "week" in self.last_publish:
                # Weeks ago - yellow to gray
                weeks_match = re.search(r'(\d+)', self.last_publish)
                if weeks_match:
                    weeks = int(weeks_match.group(1))
                    ratio = min(weeks / 4, 1.0)  # Normalize over 4 weeks
                    return self._interpolate_color(Theme.TIME_MEDIUM, Theme.TIME_OLD, ratio)
                return Theme.TIME_MEDIUM
            elif "month" in self.last_publish or "year" in self.last_publish:
                # Months or years ago - gray
                return Theme.TIME_OLD
            else:
                return Theme.TEXT_MUTED
        except:
            return Theme.TEXT_MUTED

class SettingsManager:
    """Enhanced settings manager with validation and defaults"""

    DEFAULT_SETTINGS = {
        'General': {
            'download_directory': DEFAULT_DOWNLOAD_DIR,
            'npm_path': '',
            'auto_open_folder': 'True',
            'max_concurrent_downloads': '5',
            'max_concurrent_requests': str(DEFAULT_MAX_CONCURRENT_REQUESTS),
            'render_markdown': 'True',
            'cache_ttl_days': str(CACHE_TTL_DAYS),
            'show_dependencies': 'True',
            'show_dependents': 'True',
            'dark_mode': 'True',
            'font_size': '10',
            'show_tooltips': 'True'
        }
    }

    def __init__(self, settings_file: str = SETTINGS_FILE):
        self.settings_file = settings_file
        self.config = configparser.ConfigParser()
        self._load_settings()

    def _load_settings(self):
        """Load settings from file with validation"""
        try:
            if os.path.exists(self.settings_file):
                self.config.read(self.settings_file)
                # Validate all settings exist
                for section, options in self.DEFAULT_SETTINGS.items():
                    if section not in self.config:
                        self.config[section] = {}
                    for key, default in options.items():
                        if key not in self.config[section]:
                            self.config[section][key] = default
            else:
                # Create default settings file
                self.config.read_dict(self.DEFAULT_SETTINGS)
                self._save_settings()
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.config.read_dict(self.DEFAULT_SETTINGS)
            self._save_settings()

    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                self.config.write(f)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def get(self, section: str, key: str, fallback: str = '') -> str:
        """Get setting value with fallback"""
        try:
            return self.config.get(section, key, fallback=fallback)
        except:
            return fallback

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer setting with validation"""
        try:
            value = self.config.get(section, key, fallback=str(fallback))
            return int(value)
        except (ValueError, configparser.NoOptionError):
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean setting with validation"""
        try:
            value = self.config.get(section, key, fallback=str(fallback)).lower()
            return value in ('true', 'yes', '1', 'on')
        except (ValueError, configparser.NoOptionError):
            return fallback

    def set(self, section: str, key: str, value: str):
        """Set setting value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self._save_settings()

    def get_download_dir(self) -> str:
        """Get download directory with validation"""
        path = self.get('General', 'download_directory', DEFAULT_DOWNLOAD_DIR)
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except:
                path = DEFAULT_DOWNLOAD_DIR
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
        return path

    def set_download_dir(self, path: str):
        """Set download directory"""
        self.set('General', 'download_directory', path)

class CacheManager:
    """Enhanced SQLite-based cache manager with compression and validation"""

    def __init__(self, db_path: str, ttl_days: int = CACHE_TTL_DAYS):
        self.db_path = db_path
        self.ttl_days = ttl_days
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize database with proper schema and indexes"""
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30,
                isolation_level=None  # Auto-commit mode
            )
            self.conn.row_factory = sqlite3.Row

            # Enable WAL mode for better concurrency
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA temp_store=MEMORY")
            self.conn.execute("PRAGMA cache_size=-2000")  # 2MB cache

            # Create tables if they don't exist
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS packages (
                    cache_key TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT,
                    description TEXT,
                    author TEXT,
                    license TEXT,
                    homepage TEXT,
                    repository TEXT,
                    downloads_last_week INTEGER,
                    downloads_last_month INTEGER,
                    downloads_trend TEXT,
                    size_unpacked TEXT,
                    file_count TEXT,
                    dependencies_count INTEGER,
                    dev_dependencies_count INTEGER,
                    peer_dependencies_count INTEGER,
                    total_versions INTEGER,
                    published_date TEXT,
                    modified_date TEXT,
                    last_publish TEXT,
                    keywords TEXT,
                    has_typescript INTEGER,
                    has_tests INTEGER,
                    has_readme INTEGER,
                    maintainers_count INTEGER,
                    maintainers TEXT,
                    github_stars TEXT,
                    github_forks TEXT,
                    github_issues TEXT,
                    score_quality REAL,
                    score_popularity REAL,
                    score_maintenance REAL,
                    score_final REAL,
                    dependents_count INTEGER,
                    dependencies TEXT,
                    dependents TEXT,
                    readme BLOB,
                    dependency_details TEXT,
                    dependent_details TEXT,
                    file_tree TEXT,
                    last_fetched REAL,
                    compressed INTEGER DEFAULT 0,
                    UNIQUE(name, version)
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS package_dependencies (
                    package_key TEXT NOT NULL,
                    dependency_name TEXT NOT NULL,
                    version TEXT,
                    size TEXT,
                    files TEXT,
                    last_publish TEXT,
                    PRIMARY KEY (package_key, dependency_name),
                    FOREIGN KEY (package_key) REFERENCES packages(cache_key) ON DELETE CASCADE
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS package_dependents (
                    package_key TEXT NOT NULL,
                    dependent_name TEXT NOT NULL,
                    size TEXT,
                    files TEXT,
                    last_publish TEXT,
                    PRIMARY KEY (package_key, dependent_name),
                    FOREIGN KEY (package_key) REFERENCES packages(cache_key) ON DELETE CASCADE
                )
            """)

            # Create indexes for performance
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_package_name ON packages(name)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_last_fetched ON packages(last_fetched)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_dependency_name ON package_dependencies(dependency_name)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_dependent_name ON package_dependents(dependent_name)")

            self.conn.commit()
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            self.conn = None

    def _compress_data(self, data: str) -> bytes:
        """Compress data for storage"""
        return zlib.compress(data.encode('utf-8'), level=6)

    def _decompress_data(self, data: bytes) -> str:
        """Decompress data from storage"""
        return zlib.decompress(data).decode('utf-8')

    def get_package(self, name: str, version: str = "latest") -> Optional[PackageInfo]:
        """Get package from cache with TTL check"""
        if not self.conn:
            return None

        try:
            # Generate cache key
            key_data = f"{name}:{version}".encode('utf-8')
            cache_key = hashlib.md5(key_data).hexdigest()

            cursor = self.conn.execute("""
                SELECT * FROM packages
                WHERE name = ? AND (version = ? OR ? = 'latest')
                AND last_fetched > strftime('%s', 'now', ? || ' days') * 1000
                ORDER BY last_fetched DESC
                LIMIT 1
            """, (name, version, version, f"-{self.ttl_days}"))

            row = cursor.fetchone()
            if not row:
                return None

            data = dict(row)

            # Decompress readme if needed
            if data.get('compressed') and data.get('readme'):
                data['readme'] = self._decompress_data(data['readme'])

            # Get dependencies and dependents
            data['dependency_details'] = self._get_dependency_details(cache_key)
            data['dependent_details'] = self._get_dependent_details(cache_key)

            return PackageInfo.from_dict(data)
        except Exception as e:
            logger.error(f"Error getting package from cache: {e}")
            return None

    def _get_dependency_details(self, package_key: str) -> Dict[str, Dict]:
        """Get dependency details from cache"""
        if not self.conn:
            return {}

        try:
            cursor = self.conn.execute("""
                SELECT dependency_name, version, size, files, last_publish
                FROM package_dependencies
                WHERE package_key = ?
            """, (package_key,))

            details = {}
            for row in cursor:
                details[row['dependency_name']] = {
                    'version': row['version'],
                    'size': row['size'],
                    'files': row['files'],
                    'last_publish': row['last_publish']
                }
            return details
        except Exception as e:
            logger.error(f"Error getting dependency details: {e}")
            return {}

    def _get_dependent_details(self, package_key: str) -> Dict[str, Dict]:
        """Get dependent details from cache"""
        if not self.conn:
            return {}

        try:
            cursor = self.conn.execute("""
                SELECT dependent_name, size, files, last_publish
                FROM package_dependents
                WHERE package_key = ?
            """, (package_key,))

            details = {}
            for row in cursor:
                details[row['dependent_name']] = {
                    'size': row['size'],
                    'files': row['files'],
                    'last_publish': row['last_publish']
                }
            return details
        except Exception as e:
            logger.error(f"Error getting dependent details: {e}")
            return {}

    def save_package(self, package: PackageInfo):
        """Save package to cache with compression"""
        if not self.conn or not package:
            return

        try:
            data = package.to_dict()

            # Compress readme if it's large
            if package.readme and len(package.readme) > 1024:
                data['readme'] = self._compress_data(package.readme)
                data['compressed'] = 1
            else:
                data['compressed'] = 0

            # Generate cache key if not present
            if not data.get('cache_key'):
                data['cache_key'] = package._generate_cache_key()

            data['last_fetched'] = time.time() * 1000  # Store as milliseconds

            # Prepare columns and values
            columns = []
            values = []
            placeholders = []

            for key, value in data.items():
                if key in ['dependency_details', 'dependent_details', 'keywords', 'maintainers', 'dependencies', 'dependents', 'file_tree']:
                    # These are handled separately
                    continue
                if key == 'readme' and data.get('compressed'):
                    # Already compressed
                    pass
                elif isinstance(value, (dict, list)):
                    # Skip complex types that should be handled separately
                    continue
                columns.append(key)
                values.append(value)
                placeholders.append('?')

            # Insert or replace the package
            self.conn.execute(f"""
                INSERT OR REPLACE INTO packages ({', '.join(columns)}, last_fetched)
                VALUES ({', '.join(placeholders)}, ?)
            """, tuple(values) + (data['last_fetched'],))

            # Save dependency details
            self._save_dependency_details(data['cache_key'], data.get('dependency_details', {}))

            # Save dependent details
            self._save_dependent_details(data['cache_key'], data.get('dependent_details', {}))

            self.conn.commit()
        except Exception as e:
            logger.error(f"Cache save error for {package.name}: {e}")
            self.conn.rollback()

    def _save_dependency_details(self, package_key: str, details: Dict[str, Dict]):
        """Save dependency details to cache"""
        if not self.conn or not details or not isinstance(details, dict):
            return

        try:
            # Clear existing details
            self.conn.execute("""
                DELETE FROM package_dependencies
                WHERE package_key = ?
            """, (package_key,))

            # Insert new details
            for dep_name, dep_data in details.items():
                self.conn.execute("""
                    INSERT INTO package_dependencies
                    (package_key, dependency_name, version, size, files, last_publish)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (package_key, dep_name, dep_data.get('version'),
                       dep_data.get('size'), dep_data.get('files'), dep_data.get('last_publish')))
        except Exception as e:
            logger.error(f"Error saving dependency details: {e}")
            self.conn.rollback()

    def _save_dependent_details(self, package_key: str, details: Dict[str, Dict]):
        """Save dependent details to cache"""
        if not self.conn or not details or not isinstance(details, dict):
            return

        try:
            # Clear existing details
            self.conn.execute("""
                DELETE FROM package_dependents
                WHERE package_key = ?
            """, (package_key,))

            # Insert new details
            for dep_name, dep_data in details.items():
                self.conn.execute("""
                    INSERT INTO package_dependents
                    (package_key, dependent_name, size, files, last_publish)
                    VALUES (?, ?, ?, ?, ?)
                """, (package_key, dep_name, dep_data.get('size'),
                       dep_data.get('files'), dep_data.get('last_publish')))
        except Exception as e:
            logger.error(f"Error saving dependent details: {e}")
            self.conn.rollback()

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.conn:
            return {'total': 0, 'fresh': 0, 'expired': 0, 'size': 0}

        try:
            # Get basic stats
            cursor = self.conn.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN last_fetched > strftime('%s', 'now', '-1 day') * 1000 THEN 1 END) as fresh,
                    COUNT(CASE WHEN last_fetched <= strftime('%s', 'now', '-' || ? || ' days') * 1000 THEN 1 END) as expired,
                    SUM(LENGTH(readme)) as size
                FROM packages
            """, (self.ttl_days,))

            row = cursor.fetchone()
            return {
                'total': row['total'],
                'fresh': row['fresh'],
                'expired': row['expired'],
                'size': humanize.naturalsize(row['size'] or 0, binary=True)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'total': 0, 'fresh': 0, 'expired': 0, 'size': 0}

    def clear_expired(self):
        """Clear expired cache entries"""
        if not self.conn:
            return

        try:
            # Delete expired packages
            self.conn.execute("""
                DELETE FROM packages
                WHERE last_fetched <= strftime('%s', 'now', '-' || ? || ' days') * 1000
            """, (self.ttl_days,))

            # Vacuum to reclaim space
            self.conn.execute("VACUUM")
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            self.conn.rollback()

    def clear_all(self):
        """Clear all cache entries"""
        if not self.conn:
            return

        try:
            self.conn.execute("DELETE FROM packages")
            self.conn.execute("DELETE FROM package_dependencies")
            self.conn.execute("DELETE FROM package_dependents")
            self.conn.execute("VACUUM")
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            self.conn.rollback()

    def close(self):
        """Close the database connection"""
        if self.conn:
            try:
                self.conn.execute("PRAGMA optimize")
                self.conn.close()
            except:
                pass
            self.conn = None

class SearchHistoryManager:
    """Enhanced search history manager with tagging and statistics"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize database with proper schema"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    timestamp REAL DEFAULT (strftime('%s', 'now') * 1000),
                    result_count INTEGER DEFAULT 0,
                    duration_ms INTEGER DEFAULT 0,
                    tags TEXT
                )
            """)

            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON search_history(timestamp)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_query ON search_history(query)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_mode ON search_history(mode)")

            self.conn.commit()
        except Exception as e:
            logger.error(f"Search history database initialization error: {e}")
            self.conn = None

    def add_search(self, query: str, mode: str, result_count: int = 0,
                  duration_ms: int = 0, tags: Optional[List[str]] = None):
        """Add a search to history with metadata"""
        if not self.conn:
            return

        try:
            # Delete duplicate entries
            self.conn.execute("""
                DELETE FROM search_history
                WHERE query = ? AND mode = ?
            """, (query, mode))

            # Insert new entry
            self.conn.execute("""
                INSERT INTO search_history (query, mode, result_count, duration_ms, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (query, mode, result_count, duration_ms, json.dumps(tags or [])))

            # Keep only the most recent searches
            self.conn.execute(f"""
                DELETE FROM search_history
                WHERE id NOT IN (
                    SELECT id FROM search_history
                    ORDER BY timestamp DESC
                    LIMIT {MAX_SEARCH_HISTORY}
                )
            """)

            self.conn.commit()
        except Exception as e:
            logger.error(f"Error adding search to history: {e}")

    def get_recent_searches(self, limit: int = MAX_SEARCH_HISTORY) -> List[Tuple[str, str]]:
        """Get recent searches with optional limit"""
        if not self.conn:
            return []

        try:
            cursor = self.conn.execute("""
                SELECT query, mode
                FROM search_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            return [(row['query'], row['mode']) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting search history: {e}")
            return []

    def get_search_stats(self) -> Dict:
        """Get statistics about search history"""
        if not self.conn:
            return {}

        try:
            cursor = self.conn.execute("""
                SELECT
                    COUNT(*) as total_searches,
                    COUNT(DISTINCT query) as unique_queries,
                    AVG(result_count) as avg_results,
                    AVG(duration_ms) as avg_duration,
                    mode as mode,
                    COUNT(*) as mode_count
                FROM search_history
                GROUP BY mode
            """)

            stats = {
                'total_searches': 0,
                'unique_queries': 0,
                'avg_results': 0,
                'avg_duration': 0,
                'by_mode': {}
            }

            for row in cursor:
                if 'mode' in row:
                    stats['by_mode'][row['mode']] = row['mode_count']
                else:
                    stats['total_searches'] = row['total_searches']
                    stats['unique_queries'] = row['unique_queries']
                    stats['avg_results'] = row['avg_results'] or 0
                    stats['avg_duration'] = row['avg_duration'] or 0

            return stats
        except Exception as e:
            logger.error(f"Error getting search stats: {e}")
            return {}

    def clear_history(self):
        """Clear all search history"""
        if not self.conn:
            return

        try:
            self.conn.execute("DELETE FROM search_history")
            self.conn.execute("VACUUM")
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error clearing search history: {e}")

    def get_popular_queries(self, limit: int = 5) -> List[Tuple[str, int]]:
        """Get most popular search queries"""
        if not self.conn:
            return []

        try:
            cursor = self.conn.execute("""
                SELECT query, COUNT(*) as count
                FROM search_history
                GROUP BY query
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))

            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting popular queries: {e}")
            return []

    def close(self):
        """Close the database connection"""
        if self.conn:
            try:
                self.conn.execute("PRAGMA optimize")
                self.conn.close()
            except:
                pass
            self.conn = None

class NPMClient:
    """Enhanced NPM Registry API client with high-performance concurrency"""

    def __init__(self, cache: CacheManager, settings: SettingsManager):
        self.cache = cache
        self.settings = settings
        self.registry_url = "https://registry.npmjs.org"
        self.search_url = f"{self.registry_url}/-/v1/search"
        self.npm_web_url = "https://www.npmjs.com/package"
        self.github_api_url = "https://api.github.com"
        self.concurrency = settings.get_int('General', 'max_concurrent_requests', DEFAULT_MAX_CONCURRENT_REQUESTS)
        self.max_retries = 3
        self.npm_path = find_npm_executable()
        self.download_dir = settings.get_download_dir()
        self.session = self._create_session()
        self._request_count = 0
        self._cache_hits = 0
        self._rate_limit_semaphore = threading.Semaphore(self.concurrency)
        self._dependency_cache: Dict[str, Dict[str, str]] = {}
        self._dependent_cache: Dict[str, Dict[str, str]] = {}

    def _create_session(self):
        """Create a requests session with proper configuration"""
        session = requests.Session()

        # Configure retry strategy
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=self.concurrency * 2,
            pool_maxsize=self.concurrency * 3
        )

        session.mount('http://', adapter)
        session.mount('https://', adapter)

        session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })

        return session

    def _make_request(self, url: str, params: Optional[Dict] = None,
                    headers: Optional[Dict] = None) -> Optional[requests.Response]:
        """Make a synchronous HTTP request with rate limiting"""
        try:
            response = self.session.get(url, params=params, headers=headers,
                                     timeout=REQUEST_TIMEOUT)

            if response.status_code == 429:
                wait_time = random.uniform(1, 3)
                logger.warning(f"Rate limited on {url}, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                return self._make_request(url, params, headers)

            response.raise_for_status()
            self._request_count += 1
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def _get_file_info_from_npm_view(self, package_name: str,
                                   version: str = 'latest') -> Tuple[Optional[int], Optional[int]]:
        """Get file count and size using npm view command"""
        if not self.npm_path:
            return None, None

        try:
            cmd = [self.npm_path, 'view', f"{package_name}@{version}",
                    'dist.unpackedSize', 'dist.fileCount']

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    try:
                        size = int(lines[0].strip())
                        file_count = int(lines[1].strip())
                        return file_count, size
                    except ValueError:
                        pass
        except Exception as e:
            logger.error(f"Error getting file info from npm view: {e}")

        return None, None

    def _scrape_npm_web_page(self, package_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Enhanced scraper for npmjs.com with multiple extraction strategies"""
        url = f"{self.npm_web_url}/{package_name}"
        response = self._make_request(url)

        if not response:
            return None, None, None

        try:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract from JSON data embedded in the page
            script_tags = soup.find_all('script')
            for script in script_tags:
                if 'window.__context__' in str(script):
                    try:
                        json_str = str(script).split('window.__context__ = ', 1)[1].split(';</script>', 1)[0].strip()
                        json_data = json.loads(json_str)
                        package_data = json_data.get('context', {}).get('package', {})

                        if package_data:
                            unpacked_size = package_data.get('unpackedSize')
                            file_count = package_data.get('fileCount')
                            publish_time = package_data.get('publishTime')

                            if unpacked_size:
                                unpacked_size = self._format_size(unpacked_size)
                            if file_count is not None:
                                file_count = str(file_count)
                            if publish_time and publish_time.get('publishTime'):
                                last_publish = self._format_publish_date(publish_time['publishTime'])
                            else:
                                last_publish = None

                            if unpacked_size and file_count:
                                return unpacked_size, file_count, last_publish
                    except Exception as e:
                        logger.error(f"Error parsing JSON from script: {e}")
                        continue

            # Extract from the page directly
            unpacked_size = None
            total_files = None
            last_publish = None

            # Unpacked size
            size_element = soup.find('p', string=re.compile(r'Unpacked Size'))
            if size_element:
                size_value = size_element.find_next('div')
                if size_value:
                    unpacked_size = size_value.get_text(strip=True)

            # Total files
            files_element = soup.find('p', string=re.compile(r'Total Files'))
            if files_element:
                files_value = files_element.find_next('div')
                if files_value:
                    total_files = files_value.get_text(strip=True)

            # Last publish date
            publish_element = soup.find('p', string=re.compile(r'Published'))
            if publish_element:
                publish_value = publish_element.find_next('div')
                if publish_value:
                    last_publish = publish_value.get_text(strip=True)

            return unpacked_size, total_files, last_publish
        except Exception as e:
            logger.error(f"Error scraping npm web page for {package_name}: {e}")
            return None, None, None

    def _format_publish_date(self, timestamp: Union[int, float]) -> str:
        """Format publish timestamp to human-readable string"""
        try:
            date_obj = datetime.datetime.fromtimestamp(timestamp / 1000)
            now = datetime.datetime.now()
            delta = now - date_obj

            if delta.days > 365:
                years = delta.days // 365
                return f"{years} year{'s' if years > 1 else ''} ago"
            elif delta.days > 30:
                months = delta.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            elif delta.days > 0:
                return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
        except:
            return "Unknown"

    def _get_dependents_count(self, package_name: str) -> int:
        """Get the number of dependents for a package from npmjs.com"""
        try:
            url = f"{self.npm_web_url}/{package_name}?activeTab=dependents"
            response = self._make_request(url)

            if not response:
                return 0

            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the dependents tab with count
            dependents_tab = soup.find('a', {'id': 'tab-dependents'})
            if dependents_tab:
                count_text = dependents_tab.get_text(strip=True)
                match = re.search(r'\[(\d+)\]', count_text)
                if match:
                    return int(match.group(1))

            # Alternative approach - find the dependents heading
            dependents_heading = soup.find('h2', string=re.compile(r'Dependents\W*(\d+)?'))
            if dependents_heading:
                match = re.search(r'(\d+)', dependents_heading.get_text())
                if match:
                    return int(match.group(1))

            # If we can't find the count, try to count the dependents in the list
            dependents_list = soup.find('div', {'id': 'tabpanel-dependents'})
            if dependents_list:
                packages = dependents_list.find_all('a', href=re.compile(r'/package/'))
                return len(packages)
        except Exception as e:
            logger.error(f"Error getting dependents count for {package_name}: {e}")

        return 0

    def _get_dependency_details(self, package_name: str,
                           dependencies: List[str]) -> Dict[str, Dict]:
        """Get detailed information for dependencies with concurrent requests"""
        details = {}
        limit = min(20, len(dependencies))

        def fetch_dep_details(dep_name: str) -> Tuple[str, Dict[str, str]]:
            """Fetch details for a single dependency"""
            try:
                # First try cache
                if dep_name in self._dependency_cache:
                    return dep_name, self._dependency_cache[dep_name]

                # Then try registry API
                url = f"https://registry.npmjs.org/{dep_name}"
                response = self._make_request(url)

                if response and response.status_code == 200:
                    data = response.json()
                    latest_version = data.get('dist-tags', {}).get('latest', '')

                    if latest_version and latest_version in data.get('versions', {}):
                        version_info = data['versions'][latest_version]
                        dist_data = version_info.get('dist', {})

                        result = {
                            'version': latest_version,
                            'size': self._format_size(dist_data.get('unpackedSize')),
                            'files': str(dist_data.get('fileCount', 'Unknown')),
                            'last_publish': self._format_publish_date(
                                data.get('time', {}).get(latest_version, 0)
                            ) if latest_version in data.get('time', {}) else 'Unknown'
                        }

                        # Cache the result
                        self._dependency_cache[dep_name] = result
                        return dep_name, result

                # Fallback to minimal info
                return dep_name, {
                    'size': 'Unknown',
                    'files': 'Unknown',
                    'last_publish': 'Unknown',
                    'version': 'Unknown'
                }
            except Exception as e:
                logger.error(f"Error fetching details for {dep_name}: {e}")
                return dep_name, {
                    'size': 'Unknown',
                    'files': 'Unknown',
                    'last_publish': 'Unknown',
                    'version': 'Unknown'
                }

        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(10, limit))) as executor:
            futures = [executor.submit(fetch_dep_details, dep_name)
                      for dep_name in dependencies[:limit]]

            for future in concurrent.futures.as_completed(futures):
                dep_name, result = future.result()
                details[dep_name] = result

        return details

    def _extract_file_tree(self, package_name: str,
                         version: str = 'latest') -> Dict[str, Any]:
        """Extract file tree from downloaded package"""
        try:
            # Create a temporary directory for extraction
            temp_dir = tempfile.mkdtemp()

            # Download the package
            download_result = self.download_package(package_name, version)

            if not download_result['success']:
                return {}

            package_file = download_result['file']
            package_path = os.path.join(self.download_dir, package_file)

            if not os.path.exists(package_path):
                return {}

            # Extract the package
            file_tree: dict[str, dict] = {}

            if package_file.endswith('.tgz'):
                # Handle tar.gz files
                with tarfile.open(package_path, 'r:gz') as tar:
                    for member in tar.getmembers():
                        if member.isfile():
                            path_parts = member.name.split('/')
                            self._add_to_file_tree(file_tree, path_parts, member.size)

            elif package_file.endswith('.zip'):
                # Handle zip files
                with zipfile.ZipFile(package_path, 'r') as zip_ref:
                    for file_info in zip_ref.infolist():
                        if not file_info.is_dir():
                            path_parts = file_info.filename.split('/')
                            self._add_to_file_tree(file_tree, path_parts, file_info.file_size)

            # Clean up
            shutil.rmtree(temp_dir, ignore_errors=True)

            return file_tree
        except Exception as e:
            logger.error(f"Error extracting file tree for {package_name}: {e}")
            return {}

    def _add_to_file_tree(self, file_tree: Dict[str, Any],
                          path_parts: List[str], size: int):
        """Add a file to the file tree structure"""
        current = file_tree

        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1:
                # This is a file
                current[part] = {
                    'type': 'file',
                    'size': size,
                    'size_str': humanize.naturalsize(size, binary=True)
                }
            else:
                # This is a directory
                if part not in current:
                    current[part] = {
                        'type': 'directory',
                        'children': {}
                    }
                current = current[part]['children']

    def get_comprehensive_data(self, package_name: str) -> Optional[PackageInfo]:
        """Fetch comprehensive package data with concurrent requests"""
        # Check cache first
        cached = self.cache.get_package(package_name)
        if cached and not cached.is_stale():
            self._cache_hits += 1
            return cached

        try:
            # Fetch from registry API
            registry_data = self._fetch_registry_data(package_name)
            if not registry_data:
                return None

            # Extract basic info
            latest_version = registry_data.get('dist-tags', {}).get('latest', '')
            if not latest_version or latest_version not in registry_data.get('versions', {}):
                return None

            version_info = registry_data['versions'][latest_version]
            time_data = registry_data.get('time', {})

            # Get file info
            dist_data = version_info.get('dist', {})
            file_count = dist_data.get('fileCount', 'Unknown')
            size_bytes = dist_data.get('unpackedSize', 'Unknown')

            if size_bytes != 'Unknown' and size_bytes is not None:
                size_str = self._format_size(size_bytes)
            else:
                size_str = 'Unknown'

            if file_count is not None:
                file_count_str = str(file_count)
            else:
                file_count_str = 'Unknown'

            # Calculate last publish date
            last_publish = 'Unknown'
            if latest_version in time_data:
                try:
                    date_str = time_data[latest_version]
                    last_publish = self._format_publish_date(
                        dateutil.parser.parse(date_str).timestamp() * 1000
                    )
                except:
                    last_publish = 'Unknown'

            # Get dependencies and dependents
            dependencies = list(version_info.get('dependencies', {}).keys())
            dev_deps = version_info.get('devDependencies', {})
            peer_deps = version_info.get('peerDependencies', {})

            # Get dependents count
            dependents_count = self._get_dependents_count(package_name)

            # Get README content
            readme_content = self._fetch_readme(package_name, registry_data)

            # Get dependency details concurrently
            dependency_details = self._get_dependency_details(package_name, dependencies)

            # Get file tree
            file_tree = self._extract_file_tree(package_name, latest_version)

            # Get author info
            author_data = version_info.get('author', {})
            author = author_data.get('name', '') if isinstance(author_data, dict) else str(author_data) if author_data else ''

            # Get repository info
            repo = version_info.get('repository', {})
            repo_url = self._extract_repo_url(repo)

            # Create package info object
            package_info = PackageInfo(
                name=package_name,
                version=latest_version,
                description=version_info.get('description', ''),
                author=author,
                license=version_info.get('license', 'Unknown'),
                homepage=version_info.get('homepage', ''),
                repository=repo_url,
                downloads_last_week=self._fetch_download_stats(package_name).get('downloads', 0),
                downloads_trend='stable',
                size_unpacked=size_str,
                file_count=file_count_str,
                dependencies_count=len(dependencies),
                dev_dependencies_count=len(dev_deps) if isinstance(dev_deps, dict) else 0,
                peer_dependencies_count=len(peer_deps) if isinstance(peer_deps, dict) else 0,
                total_versions=len(registry_data.get('versions', {})),
                published_date=time_data.get(latest_version, 'Unknown'),
                modified_date=time_data.get('modified', 'Unknown'),
                last_publish=last_publish,
                keywords=version_info.get('keywords', []),
                has_typescript='typescript' in dev_deps or any('@types' in key for key in dependencies),
                has_tests=any(key in dev_deps for key in ['jest', 'mocha', 'jasmine', 'ava', 'tape']),
                has_readme=bool(readme_content),
                maintainers_count=len(registry_data.get('maintainers', [])),
                maintainers=[m.get('name', '') for m in registry_data.get('maintainers', []) if isinstance(m, dict)],
                dependents_count=dependents_count,
                dependencies=dependencies,
                readme=readme_content,
                dependency_details=dependency_details,
                file_tree=file_tree
            )

            # Save to cache
            self.cache.save_package(package_info)

            return package_info
        except Exception as e:
            logger.error(f"Error fetching comprehensive data for {package_name}: {e}")
            return None

    def _fetch_registry_data(self, package_name: str) -> Optional[Dict]:
        """Fetch package data from npm registry"""
        url = f"{self.registry_url}/{package_name}"
        response = self._make_request(url)
        return response.json() if response else None

    def _fetch_readme(self, package_name: str, registry_data: Dict) -> str:
        """Fetch README content from multiple sources"""
        readme_content = ""

        # Try registry first
        if 'readme' in registry_data and isinstance(registry_data['readme'], str):
            readme_content = registry_data['readme'].strip()
            if readme_content:
                return readme_content

        # Try GitHub if repository URL is available
        repo_url = self._extract_repo_url(registry_data.get('versions', {}).get(
            registry_data.get('dist-tags', {}).get('latest', ''), {}
        ).get('repository', {}))

        if repo_url and 'github.com' in repo_url:
            github_readme = self._fetch_github_readme(repo_url)
            if github_readme:
                return github_readme

        # Fallback to npmjs.com
        return self._fetch_npmjs_readme(package_name)

    def _fetch_github_readme(self, repo_url: str) -> str:
        """Fetch README from GitHub repository"""
        try:
            # Extract owner and repo name
            parts = urlparse(repo_url).path.strip('/').split('/')
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1].replace('.git', '')

                # Try different README filenames
                readme_names = ['README.md', 'README.rst', 'README', 'readme.md', 'readme.rst', 'readme']

                for readme_name in readme_names:
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_name}"
                    headers = {'Accept': 'application/vnd.github.v3+json'}

                    response = self._make_request(api_url, headers=headers)
                    if response and response.status_code == 200:
                        data = response.json()
                        if data.get('content'):
                            try:
                                content = base64.b64decode(data['content']).decode('utf-8')
                                return content.strip()
                            except:
                                continue
        except Exception as e:
            logger.error(f"Error fetching GitHub README: {e}")

        return ""

    def _fetch_npmjs_readme(self, package_name: str) -> str:
        """Fetch README from npmjs.com page"""
        try:
            url = f"https://www.npmjs.com/package/{package_name}"
            response = self._make_request(url)

            if not response:
                return ""

            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            readme_div = soup.find('div', {'id': 'readme'})
            if readme_div:
                readme_content = ''

                # Cast to Tag to access find_all method
                readme_tag = cast(Tag, readme_div)

                for element in readme_tag.find_all(['p', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'code', 'table', 'tr', 'td', 'th']):
                    if element.name == 'pre':
                        readme_content += f"\n\n```\n{element.get_text()}\n```\n"
                    elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        readme_content += f"\n{element.get_text()}\n"
                    elif element.name == 'code':
                        readme_content += f"`{element.get_text()}`"
                    else:
                        readme_content += f"\n{element.get_text()}\n"

                return readme_content.strip()
        except Exception as e:
            logger.error(f"Error fetching npmjs README: {e}")

        return ""

    def _fetch_download_stats(self, package_name: str) -> Dict:
        """Fetch download statistics for a package"""
        try:
            url = f"https://api.npmjs.org/downloads/point/last-week/{package_name}"
            response = self._make_request(url)

            if response:
                data = response.json()
                return {
                    'downloads': data.get('downloads', 0),
                    'trend': 'stable'
                }
        except Exception as e:
            logger.error(f"Error fetching downloads for {package_name}: {e}")

        return {'downloads': 0, 'trend': 'unknown'}

    def _extract_repo_url(self, repository: Union[str, Dict]) -> str:
        """Extract and normalize repository URL"""
        if isinstance(repository, dict):
            url = repository.get('url', '')
        else:
            url = str(repository)

        url = url.replace('git+', '').replace('git://', 'https://')
        url = url.replace('git@github.com:', 'https://github.com/')
        url = url.rstrip('.git')

        return url

    def _format_size(self, bytes_size: Union[int, float, None]) -> str:
        """Format size in human-readable format"""
        if not bytes_size or bytes_size == "Unknown":
            return "Unknown"

        try:
            size = int(bytes_size)
            return humanize.naturalsize(size, binary=True)
        except:
            return str(bytes_size)

    def search_packages(self, query: str, date_filter: Optional[datetime.datetime] = None,
                      size_min: Optional[float] = None, size_max: Optional[float] = None,
                      max_results: int = DEFAULT_MAX_RESULTS,
                      progress_callback: Optional[Callable] = None,
                      result_callback: Optional[Callable] = None,
                      fetch_details: bool = False) -> List[PackageInfo]:
        """Search packages with enhanced filtering and concurrent requests"""

        if not query:
            return []

        # Convert size filters to bytes
        min_bytes = int(size_min * 1024) if size_min else None
        max_bytes = int(size_max * 1024 * 1024) if size_max else None

        all_packages: dict[str, dict] = {}
        page_size = 250
        from_value = 0
        total_retrieved = 0

        def fetch_page():
            nonlocal from_value, total_retrieved

            while len(all_packages) < max_results:
                params = {
                    "text": query,
                    "size": page_size,
                    "from": from_value
                }

                try:
                    response = self._make_request(self.search_url, params=params)
                    if not response:
                        break

                    data = response.json()
                    results = data.get('objects', [])

                    if not results:
                        break

                    # Process results in parallel
                    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, self.concurrency)) as executor:
                        futures = []

                        for result in results:
                            pkg_data = result.get('package', {})
                            package_name = pkg_data.get('name', '')

                            if not package_name or package_name in all_packages:
                                continue

                            if fetch_details:
                                futures.append(executor.submit(self.get_comprehensive_data, package_name))
                            else:
                                # Create minimal package info for search results
                                version = pkg_data.get('version', 'latest')
                                description = pkg_data.get('description', '')

                                # Get basic stats
                                downloads = 0
                                try:
                                    stats_url = f"https://api.npmjs.org/downloads/point/last-week/{package_name}"
                                    stats_response = self._make_request(stats_url)
                                    if stats_response:
                                        downloads = stats_response.json().get('downloads', 0)
                                except:
                                    pass

                                # Get dependents count
                                dependents_count = 0
                                try:
                                    dependents_count = self._get_dependents_count(package_name)
                                except:
                                    pass

                                # Get dependencies count
                                dependencies_count = 0
                                try:
                                    registry_url = f"https://registry.npmjs.org/{package_name}"
                                    registry_response = self._make_request(registry_url)
                                    if registry_response:
                                        registry_data = registry_response.json()
                                        latest_version = registry_data.get('dist-tags', {}).get('latest', '')
                                        if latest_version and latest_version in registry_data.get('versions', {}):
                                            version_info = registry_data['versions'][latest_version]
                                            dependencies = version_info.get('dependencies', {})
                                            dependencies_count = len(dependencies) if isinstance(dependencies, dict) else 0
                                except:
                                    pass

                                # Get last publish date
                                last_publish = 'Unknown'
                                try:
                                    registry_url = f"https://registry.npmjs.org/{package_name}"
                                    registry_response = self._make_request(registry_url)
                                    if registry_response:
                                        registry_data = registry_response.json()
                                        latest_version = registry_data.get('dist-tags', {}).get('latest', '')
                                        if latest_version and latest_version in registry_data.get('time', {}):
                                            date_str = registry_data['time'][latest_version]
                                            last_publish = self._format_publish_date(
                                                dateutil.parser.parse(date_str).timestamp() * 1000
                                            )
                                except:
                                    pass

                                # Get size info
                                size_unpacked = 'Unknown'
                                file_count = 'Unknown'
                                try:
                                    size, files = self._get_file_info_from_npm_view(package_name, version)
                                    if size is not None:
                                        size_unpacked = self._format_size(size)
                                    if files is not None:
                                        file_count = str(files)
                                except:
                                    pass

                                pkg = PackageInfo(
                                    name=package_name,
                                    version=version,
                                    description=description,
                                    downloads_last_week=downloads,
                                    dependents_count=dependents_count,
                                    dependencies_count=dependencies_count,
                                    last_publish=last_publish,
                                    size_unpacked=size_unpacked,
                                    file_count=file_count
                                )
                                all_packages[package_name] = pkg
                                total_retrieved += 1

                                # Update progress
                                if progress_callback:
                                    progress_callback(
                                        len(all_packages),
                                        min(max_results, total_retrieved),
                                        max_results
                                    )

                                # Update UI with the new package
                                if result_callback:
                                    result_callback([pkg])

                    if fetch_details:
                        for future in concurrent.futures.as_completed(futures):
                            if len(all_packages) >= max_results:
                                break

                            pkg = future.result()
                            if not pkg:
                                continue

                            # Apply filters
                            skip_package = False
                            if size_min:
                                size_bytes = self._parse_size_to_bytes(pkg.size_unpacked)
                                if size_bytes is not None and size_bytes < min_bytes:
                                    skip_package = True

                            if not skip_package and date_filter:
                                try:
                                    if pkg.modified_date != 'N/A' and pkg.modified_date != 'Unknown':
                                        pkg_date = dateutil.parser.parse(pkg.modified_date)
                                        if pkg_date < date_filter:
                                            skip_package = True
                                except:
                                    skip_package = True

                            if skip_package:
                                continue

                            all_packages[package_name] = pkg
                            total_retrieved += 1

                            # Update progress
                            if progress_callback:
                                progress_callback(
                                    len(all_packages),
                                    min(max_results, total_retrieved),
                                    max_results
                                )

                            # Update UI with the new package
                            if result_callback:
                                result_callback([pkg])

                    from_value += page_size
                except Exception as e:
                    logger.error(f"Error fetching page: {e}")
                    break

        # Run fetch in a separate thread
        fetch_thread = threading.Thread(target=fetch_page, daemon=True)
        fetch_thread.start()
        fetch_thread.join()

        return list(all_packages.values())[:max_results]

    def _parse_size_to_bytes(self, size_str: Optional[str]) -> Optional[int]:
        """Convert size string like '20.5 KB' to bytes"""
        if not size_str or size_str == "Unknown":
            return None

        try:
            # Extract numeric value and unit
            match = re.match(r'([\d.]+)\s*([KMGT]?B)?', size_str, re.IGNORECASE)
            if not match:
                return None

            value = float(match.group(1))
            unit = match.group(2) or 'B'

            units = {
                'B': 1,
                'KB': 1024,
                'MB': 1024 * 1024,
                'GB': 1024 * 1024 * 1024,
                'TB': 1024 * 1024 * 1024 * 1024
            }

            multiplier = units.get(unit.upper(), 1)
            return int(value * multiplier)
        except:
            return None

    def download_package(self, package_name: str, version: str = 'latest',
                      progress_callback: Optional[Callable] = None) -> Dict:
        """Download a package using npm with proper error handling"""
        if not self.npm_path:
            return {
                'success': False,
                'package': package_name,
                'file': None,
                'error': 'npm not found. Please install Node.js and npm.'
            }

        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)

        original_dir = os.getcwd()
        os.chdir(self.download_dir)

        try:
            cmd = [self.npm_path, 'pack', f"{package_name}@{version}"]
            logger.info(f"Running command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
            )

            if result.returncode == 0:
                downloaded_file = result.stdout.strip()
                success = True
                error_message = None
                logger.info(f"Successfully downloaded {package_name}")
            else:
                downloaded_file = None
                success = False
                error_message = result.stderr
                logger.error(f"Failed to download {package_name}: {error_message}")
        except subprocess.TimeoutExpired:
            downloaded_file = None
            success = False
            error_message = "Download timed out"
            logger.error(f"Download timeout for {package_name}")
        except Exception as e:
            downloaded_file = None
            success = False
            error_message = str(e)
            logger.error(f"Download error for {package_name}: {e}")
        finally:
            os.chdir(original_dir)

        return {
            'success': success,
            'package': package_name,
            'file': downloaded_file,
            'error': error_message
        }

    def download_packages_concurrent(self, package_list: Sequence[Union[str, Dict]],
                                 progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Download multiple packages concurrently with proper rate limiting"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)

        results = []
        max_workers = min(5, self.settings.get_int('General', 'max_concurrent_downloads', 5))
        download_semaphore = threading.Semaphore(max_workers)
        result_lock = threading.Lock()

        def download_single_package(package_info: Union[str, Dict], index: int, total: int):
            nonlocal results

            with download_semaphore:
                package_name = package_info if isinstance(package_info, str) else package_info.get('name', '')
                version = package_info.get('version', 'latest') if isinstance(package_info, dict) else 'latest'

                try:
                    result = self.download_package(package_name, version)

                    with result_lock:
                        results.append(result)
                        if progress_callback:
                            progress_callback(index + 1, total, result)
                except Exception as e:
                    logger.error(f"Error downloading {package_name}: {e}")
                    with result_lock:
                        results.append({
                            'success': False,
                            'package': package_name,
                            'file': None,
                            'error': str(e)
                        })
                        if progress_callback:
                            progress_callback(index + 1, total, {
                                'success': False,
                                'package': package_name,
                                'file': None,
                                'error': str(e)
                            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, max_workers or 1)) as executor:
            futures = [
                executor.submit(download_single_package, package, i, len(package_list))
                for i, package in enumerate(package_list)
            ]
            concurrent.futures.wait(futures)

        return results

    def set_download_dir(self, directory: str):
        """Set the download directory"""
        self.download_dir = directory
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def get_stats(self) -> Dict:
        """Get client statistics"""
        return {
            'requests': self._request_count,
            'cache_hits': self._cache_hits,
            'cache_hit_rate': f"{(self._cache_hits / max(1, self._request_count + self._cache_hits) * 100):.1f}%"
        }

def find_npm_executable() -> Optional[str]:
    """Find npm executable on the current platform with enhanced search"""
    npm_path = None

    # First try the simple approach
    try:
        if IS_WINDOWS:
            result = subprocess.run(
                ['where', 'npm'],
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            result = subprocess.run(
                ['which', 'npm'],
                capture_output=True,
                text=True,
                check=True
            )

        if result.returncode == 0:
            npm_path = result.stdout.strip().split('\n')[0]
            if npm_path and npm_path.endswith('.py'):
                npm_path = None
            if IS_WINDOWS and npm_path and not npm_path.endswith('.cmd') and os.path.exists(npm_path + '.cmd'):
                npm_path = npm_path + '.cmd'
            if npm_path and os.path.exists(npm_path):
                return npm_path
    except:
        pass

    # Then try common paths
    common_paths = []

    if IS_WINDOWS:
        program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
        program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
        localappdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        appdata = os.environ.get('APPDATA', os.path.expanduser('~\AppData\Roaming'))

        common_paths = [
            os.path.join(program_files, 'nodejs', 'npm.cmd'),
            os.path.join(program_files_x86, 'nodejs', 'npm.cmd'),
            os.path.join(localappdata, 'Programs', 'nodejs', 'npm.cmd'),
            os.path.join(appdata, 'npm', 'npm.cmd'),
            os.path.join(localappdata, 'npm', 'npm.cmd'),
            os.path.join(program_files, 'nodejs', 'npm'),
            os.path.join(program_files_x86, 'nodejs', 'npm'),
            os.path.join(localappdata, 'Programs', 'nodejs', 'npm'),
            os.path.join(appdata, 'npm', 'npm'),
            os.path.join(localappdata, 'npm', 'npm'),
        ]
    elif IS_MAC:
        common_paths = [
            '/usr/local/bin/npm',
            '/opt/homebrew/bin/npm',
            os.path.expanduser('~/.npm/bin/npm'),
            os.path.expanduser('~/node_modules/.bin/npm'),
            os.path.expanduser('~/.nvm/versions/node/*/bin/npm'),
            '/usr/local/opt/node/bin/npm',
        ]
    elif IS_LINUX:
        common_paths = [
            '/usr/bin/npm',
            '/usr/local/bin/npm',
            os.path.expanduser('~/.npm/bin/npm'),
            os.path.expanduser('~/node_modules/.bin/npm'),
            os.path.expanduser('~/.nvm/versions/node/*/bin/npm'),
            '/snap/bin/npm',
        ]

    # Expand glob patterns for nvm
    if IS_MAC or IS_LINUX:
        import glob
        nvm_path = os.path.expanduser('~/.nvm/versions/node/*/bin/npm')
        if glob.glob(nvm_path):
            common_paths.extend(glob.glob(nvm_path))

    # Check all common paths
    for path in common_paths:
        if os.path.exists(path):
            return path

    return None

class FileTreeViewer:
    """File tree viewer for exploring package contents"""

    def __init__(self, parent, on_file_select: Callable):
        self.parent = parent
        self.on_file_select = on_file_select
        self.current_package: Optional[str] = None
        self.current_file_tree: Dict[str, Any] = {}
        self._create_ui()

    def _create_ui(self):
        """Create the file tree UI"""
        # Main container
        self.container = ttk.Frame(self.parent)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Frame(self.container)
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header, text="File Tree", font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)

        # Refresh button
        self.refresh_btn = ttk.Button(
            header,
            text="Refresh",
            style="Secondary.TButton",
            command=self.refresh_tree
        )
        self.refresh_btn.pack(side=tk.RIGHT)

        # Paned window for tree and content
        self.paned = ttk.PanedWindow(self.container, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Tree view
        tree_frame = ttk.Frame(self.paned)
        self.paned.add(tree_frame, weight=1)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("size",),
            show="tree headings"
        )
        self.tree.heading("#0", text="File")
        self.tree.heading("size", text="Size")
        self.tree.column("#0", width=200)
        self.tree.column("size", width=80, anchor='e')

        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # File content viewer
        content_frame = ttk.Frame(self.paned)
        self.paned.add(content_frame, weight=2)

        self.content_text = tk.Text(
            content_frame,
            wrap=tk.NONE,
            bg=Theme.BG_SECONDARY,
            fg=Theme.TEXT,
            relief='flat',
            padx=10,
            pady=10,
            font=("Consolas", 9)
        )

        content_scrollbar_y = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.content_text.yview)
        content_scrollbar_x = ttk.Scrollbar(content_frame, orient=tk.HORIZONTAL, command=self.content_text.xview)

        self.content_text.configure(yscrollcommand=content_scrollbar_y.set, xscrollcommand=content_scrollbar_x.set)

        self.content_text.grid(row=0, column=0, sticky="nsew")
        content_scrollbar_y.grid(row=0, column=1, sticky="ns")
        content_scrollbar_x.grid(row=1, column=0, sticky="ew")

        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # Bind events
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Configure syntax highlighting tags
        self._setup_syntax_tags()

    def _setup_syntax_tags(self):
        """Setup syntax highlighting tags for code viewer"""
        # Common file extensions and their syntax highlighting
        self.syntax_configs = {
            '.js': {
                'keywords': ['abstract', 'arguments', 'await', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 'const', 'continue', 'debugger', 'default', 'delete', 'do', 'double', 'else', 'enum', 'eval', 'export', 'extends', 'false', 'final', 'finally', 'float', 'for', 'function', 'goto', 'if', 'implements', 'import', 'in', 'instanceof', 'int', 'interface', 'let', 'long', 'native', 'new', 'null', 'package', 'private', 'protected', 'public', 'return', 'short', 'static', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'true', 'try', 'typeof', 'var', 'void', 'volatile', 'while', 'with', 'yield'],
                'strings': Theme.CODE_STRING,
                'comments': Theme.CODE_COMMENT,
                'keywords': Theme.CODE_KEYWORD,
                'numbers': Theme.CODE_NUMBER,
                'functions': Theme.CODE_FUNCTION
            },
            '.ts': {
                'keywords': ['abstract', 'as', 'asserts', 'async', 'await', 'boolean', 'break', 'case', 'catch', 'class', 'const', 'constructor', 'continue', 'debugger', 'declare', 'default', 'delete', 'do', 'double', 'else', 'enum', 'export', 'extends', 'false', 'finally', 'for', 'from', 'function', 'get', 'if', 'implements', 'import', 'in', 'infer', 'instanceof', 'interface', 'is', 'keyof', 'let', 'module', 'namespace', 'never', 'new', 'null', 'number', 'object', 'of', 'package', 'private', 'protected', 'public', 'readonly', 'require', 'return', 'set', 'static', 'string', 'super', 'symbol', 'this', 'throw', 'true', 'try', 'type', 'typeof', 'undefined', 'unique', 'unknown', 'var', 'void', 'while', 'with', 'yield'],
                'strings': Theme.CODE_STRING,
                'comments': Theme.CODE_COMMENT,
                'keywords': Theme.CODE_KEYWORD,
                'numbers': Theme.CODE_NUMBER,
                'functions': Theme.CODE_FUNCTION
            },
            '.json': {
                'keywords': ['true', 'false', 'null'],
                'strings': Theme.CODE_STRING,
                'comments': Theme.CODE_COMMENT,
                'keywords': Theme.CODE_KEYWORD,
                'numbers': Theme.CODE_NUMBER,
                'functions': Theme.CODE_FUNCTION
            },
            '.md': {
                'keywords': [],
                'strings': Theme.CODE_STRING,
                'comments': Theme.CODE_COMMENT,
                'keywords': Theme.CODE_KEYWORD,
                'numbers': Theme.CODE_NUMBER,
                'functions': Theme.CODE_FUNCTION
            },
            '.py': {
                'keywords': ['and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'exec', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'not', 'or', 'pass', 'print', 'raise', 'return', 'try', 'while', 'with', 'yield'],
                'strings': Theme.CODE_STRING,
                'comments': Theme.CODE_COMMENT,
                'keywords': Theme.CODE_KEYWORD,
                'numbers': Theme.CODE_NUMBER,
                'functions': Theme.CODE_FUNCTION
            }
        }

        # Configure tags
        for ext, config in self.syntax_configs.items():
            self.content_text.tag_config(f"{ext}_keyword", foreground=config['keywords'])
            self.content_text.tag_config(f"{ext}_string", foreground=config['strings'])
            self.content_text.tag_config(f"{ext}_comment", foreground=config['comments'])
            self.content_text.tag_config(f"{ext}_number", foreground=config['numbers'])
            self.content_text.tag_config(f"{ext}_function", foreground=config['functions'])

    def load_package(self, package_name: str, file_tree: Dict[str, Any]):
        """Load file tree for a package"""
        self.current_package = package_name
        self.current_file_tree = file_tree

        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Populate tree
        self._populate_tree(file_tree, "")

        # Expand first level
        for item in self.tree.get_children():
            self.tree.item(item, open=True)

    def _populate_tree(self, tree_data: Dict[str, Any], parent: str):
        """Recursively populate the tree view"""
        for name, data in tree_data.items():
            if data['type'] == 'directory':
                # Add directory node
                node = self.tree.insert(
                    parent,
                    "end",
                    text=name,
                    values=("",),
                    open=False
                )
                # Add children
                self._populate_tree(data['children'], node)
            else:
                # Add file node
                self.tree.insert(
                    parent,
                    "end",
                    text=name,
                    values=(data['size_str'],),
                    tags=(name,)
                )

    def _on_tree_select(self, event):
        """Handle tree selection"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        item_text = self.tree.item(item, "text")

        # Check if it's a file
        if not self.tree.get_children(item):  # No children means it's a file
            self._load_file_content(item_text)

    def _on_tree_double_click(self, event):
        """Handle double-click on tree item"""
        self._on_tree_select(event)

    def _load_file_content(self, filename: str):
        """Load content of a selected file"""
        if not self.current_package:
            return

        # Clear content
        self.content_text.delete(1.0, tk.END)

        # Get file path
        file_path = self._get_file_path(filename)
        if not file_path:
            self.content_text.insert(tk.END, f"Could not locate file: {filename}")
            return

        try:
            # Try to extract and read the file
            temp_dir = tempfile.mkdtemp()

            # Download the package
            client = NPMClient(CacheManager(CACHE_DB), SettingsManager())
            download_result = client.download_package(self.current_package)

            if not download_result['success']:
                self.content_text.insert(tk.END, f"Error downloading package: {download_result['error']}")
                return

            package_file = download_result['file']
            package_path = os.path.join(client.download_dir, package_file)

            if not os.path.exists(package_path):
                self.content_text.insert(tk.END, f"Package file not found: {package_path}")
                return

            # Extract the file
            content = None

            if package_file.endswith('.tgz'):
                # Handle tar.gz files
                with tarfile.open(package_path, 'r:gz') as tar:
                    for member in tar.getmembers():
                        if member.isfile() and member.name == file_path:
                            extracted_file = tar.extractfile(member)
                            if extracted_file:
                                content = extracted_file.read().decode('utf-8', errors='replace')
                                break
            elif package_file.endswith('.zip'):
                # Handle zip files
                with zipfile.ZipFile(package_path, 'r') as zip_ref:
                    for file_info in zip_ref.infolist():
                        if not file_info.is_dir() and file_info.filename == file_path:
                            with zip_ref.open(file_info) as file:
                                content = file.read().decode('utf-8', errors='replace')
                            break

            # Clean up
            shutil.rmtree(temp_dir, ignore_errors=True)

            if content:
                # Apply syntax highlighting
                self._apply_syntax_highlighting(content, filename)
            else:
                self.content_text.insert(tk.END, f"Could not extract file: {file_path}")
        except Exception as e:
            self.content_text.insert(tk.END, f"Error loading file: {str(e)}")

    def _get_file_path(self, filename: str) -> Optional[str]:
        """Get the full path of a file in the package"""
        def find_path(tree_data: Dict[str, Any], path: str = "") -> Optional[str]:
            for name, data in tree_data.items():
                if data['type'] == 'directory':
                    result = find_path(data['children'], f"{path}{name}/")
                    if result:
                        return result
                elif name == filename:
                    return f"{path}{name}"
            return None

        return find_path(self.current_file_tree)

    def _apply_syntax_highlighting(self, content: str, filename: str):
        """Apply syntax highlighting to content"""
        # Get file extension
        _, ext = os.path.splitext(filename.lower())

        # Get syntax config
        config = self.syntax_configs.get(ext, self.syntax_configs.get('.md'))
        if not config:
            # No syntax highlighting, just insert plain text
            self.content_text.insert(tk.END, content)
            return

        # Apply syntax highlighting
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Track position in line
            pos = 0

            # Skip if line is empty
            if not line:
                self.content_text.insert(tk.END, '\n')
                continue

            # Process line character by character
            in_string = False
            in_comment = False
            string_char = None

            while pos < len(line):
                # Check for comments (only at beginning of line for most languages)
                if pos == 0 and not in_string and not in_comment:
                    if ext in ['.py', '.js', '.ts'] and line.startswith('#'):
                        # Python comment
                        self.content_text.insert(tk.END, line[pos:], f"{ext}_comment")
                        pos = len(line)
                        continue
                    elif ext in ['.js', '.ts'] and line.startswith('//'):
                        # JavaScript/TypeScript comment
                        self.content_text.insert(tk.END, line[pos:], f"{ext}_comment")
                        pos = len(line)
                        continue

                # Check for string start
                if not in_string and not in_comment and line[pos] in ['"', "'", '`']:
                    in_string = True
                    string_char = line[pos]
                    self.content_text.insert(tk.END, line[pos], f"{ext}_string")
                    pos += 1
                    continue

                # Check for string end
                if in_string and line[pos] == string_char and (pos == 0 or line[pos-1] != '\\'):
                    in_string = False
                    self.content_text.insert(tk.END, line[pos], f"{ext}_string")
                    pos += 1
                    continue

                # Process content based on context
                if in_string:
                    # Inside string
                    self.content_text.insert(tk.END, line[pos], f"{ext}_string")
                elif in_comment:
                    # Inside comment
                    self.content_text.insert(tk.END, line[pos], f"{ext}_comment")
                else:
                    # Check for keywords
                    # Extract word at current position
                    word_match = re.match(r'\b(\w+)\b', line[pos:])
                    if word_match:
                        word = word_match.group(1)
                        if word in config['keywords']:
                            self.content_text.insert(tk.END, word, f"{ext}_keyword")
                            pos += len(word)
                            continue

                    # Check for numbers
                    num_match = re.match(r'\b(\d+)\b', line[pos:])
                    if num_match:
                        num = num_match.group(1)
                        self.content_text.insert(tk.END, num, f"{ext}_number")
                        pos += len(num)
                        continue

                    # Default text
                    self.content_text.insert(tk.END, line[pos])

                pos += 1

            # Add newline
            self.content_text.insert(tk.END, '\n')

    def refresh_tree(self):
        """Refresh the file tree"""
        if self.current_package:
            # This would typically reload the file tree
            # For now, we'll just call the callback
            if self.on_file_select:
                self.on_file_select(self.current_package)

class NPMAnalyzerApp:
    """Main application window with all enhanced features"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NPM Package Analyzer Pro - Ultimate Edition")
        self.root.geometry("1800x1000")
        self.root.minsize(1200, 800)

        # Initialize components
        self.settings = SettingsManager()
        self.cache = CacheManager(CACHE_DB, self.settings.get_int('General', 'cache_ttl_days', CACHE_TTL_DAYS))
        self.search_history = SearchHistoryManager(SEARCH_HISTORY_DB)
        self.client = NPMClient(self.cache, self.settings)

        # Set download directory from settings
        self.client.download_dir = self.settings.get_download_dir()

        # State variables
        self.current_package: Optional[str] = None
        self.selected_date: Optional[datetime.date] = None
        self.all_results: List[PackageInfo] = []
        self.result_counter = 0
        self.package_items: Dict[str, str] = {}
        self.search_stop_flag = threading.Event()
        self.is_searching = False
        self.markdown_renderer: Optional[MarkdownRenderer] = None
        self.search_task: Optional[threading.Thread] = None
        self.font = tkfont.Font(family="Segoe UI", size=self.settings.get_int('General', 'font_size', 10))

        # Setup UI
        self._setup_theme()
        self._create_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_theme(self):
        """Setup application theme and styles"""
        self.root.configure(bg=Theme.BG)
        style = ttk.Style()
        style.theme_use("clam")

        # Configure base styles
        style.configure("TFrame", background=Theme.BG)
        style.configure("TLabel", background=Theme.BG, foreground=Theme.TEXT)
        style.configure("Treeview", background=Theme.BG_SECONDARY, foreground=Theme.TEXT,
                       fieldbackground=Theme.BG_SECONDARY, borderwidth=0, rowheight=24)
        style.configure("Treeview.Heading", background=Theme.BG_TERTIARY, foreground=Theme.TEXT,
                       borderwidth=0, relief="flat", font=self.font)
        style.map("Treeview", background=[('selected', Theme.ACCENT)], foreground=[('selected', Theme.BG)])
        style.configure("TProgressbar", background=Theme.ACCENT, troughcolor=Theme.BG_TERTIARY,
                       borderwidth=0, thickness=10)
        style.configure("TNotebook", background=Theme.BG)
        style.configure("TNotebook.Tab", background=Theme.BG_TERTIARY, foreground=Theme.TEXT,
                       padding=[10, 5], font=self.font)
        style.map("TNotebook.Tab", background=[("selected", Theme.BG_SECONDARY)],
                   expand=[("selected", [1, 1, 1, 0])])

        # Configure custom styles
        style.configure("Primary.TButton", background=Theme.ACCENT, foreground=Theme.BG,
                       borderwidth=0, font=self.font)
        style.configure("Secondary.TButton", background=Theme.BG_SECONDARY, foreground=Theme.TEXT,
                       borderwidth=0, font=self.font)
        style.configure("Success.TButton", background=Theme.SUCCESS, foreground=Theme.BG,
                       borderwidth=0, font=self.font)
        style.configure("Danger.TButton", background=Theme.ERROR, foreground=Theme.BG,
                       borderwidth=0, font=self.font)
        style.configure("Warning.TButton", background=Theme.WARNING, foreground=Theme.BG,
                       borderwidth=0, font=self.font)

        # Configure entry styles
        style.configure("Primary.TEntry", fieldbackground=Theme.BG_INPUT, foreground=Theme.TEXT,
                       insertcolor=Theme.TEXT, borderwidth=1, font=self.font)
        style.configure("Secondary.TEntry", fieldbackground=Theme.BG_SECONDARY, foreground=Theme.TEXT,
                       insertcolor=Theme.TEXT, borderwidth=1, font=self.font)

        # Configure combobox styles
        style.configure("TCombobox", fieldbackground=Theme.BG_INPUT, foreground=Theme.TEXT,
                       insertcolor=Theme.TEXT, borderwidth=1, font=self.font)

        # Configure scrollbar styles
        style.configure("TScrollbar", background=Theme.SCROLLBAR, troughcolor=Theme.BG,
                       bordercolor=Theme.BG, arrowcolor=Theme.TEXT)

        # Configure checkbutton styles
        style.configure("TCheckbutton", background=Theme.BG, foreground=Theme.TEXT, font=self.font,
                       indicatorcolor=Theme.BG, selectcolor=Theme.BG_TERTIARY)

        # Configure radiobutton styles
        style.configure("TRadiobutton", background=Theme.BG, foreground=Theme.TEXT, font=self.font,
                       indicatorcolor=Theme.BG, selectcolor=Theme.BG_TERTIARY)

    def _create_ui(self):
        """Create the main user interface"""
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Header with search history and controls
        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, 10))

        # Search history dropdown
        ttk.Label(header, text="Recent Searches:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_history_var = tk.StringVar()
        self.search_history_combo = ttk.Combobox(
            header,
            textvariable=self.search_history_var,
            values=[],
            state="readonly",
            width=40
        )
        self.search_history_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.search_history_combo.bind("<<ComboboxSelected>>", self._on_history_selected)

        # Clear history button
        ttk.Button(
            header,
            text="Clear History",
            style="Secondary.TButton",
            command=self._clear_search_history
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Settings button
        ttk.Button(
            header,
            text="⚙ Settings",
            style="Primary.TButton",
            command=self._open_settings
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Worker status
        self.worker_display = ttk.Label(
            header,
            text=f"{self.client.concurrency} Workers | npm {'Found' if self.client.npm_path else 'Not Found'}",
            foreground=Theme.SUCCESS if self.client.npm_path else Theme.ERROR
        )
        self.worker_display.pack(side=tk.RIGHT)

        # Search bar
        search_container = ttk.Frame(main)
        search_container.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_container, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_container,
            textvariable=self.search_var,
            width=50
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        search_entry.bind("<Return>", lambda e: self._search_packages())

        # Stop button (initially hidden)
        self.stop_btn = ttk.Button(
            search_container,
            text="Stop",
            style="Danger.TButton",
            command=self._stop_search
        )

        ttk.Button(
            search_container,
            text="Search",
            style="Primary.TButton",
            command=self._search_packages
        ).pack(side=tk.RIGHT)

        # Enhanced Filters
        filters = ttk.Frame(main)
        filters.pack(fill=tk.X, pady=(0, 10))

        # Search mode
        mode_frame = ttk.Frame(filters)
        mode_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(mode_frame, text="Search Mode:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_mode = tk.StringVar(value="general")
        self.mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.search_mode,
            values=["general", "exact package", "keywords", "author", "maintainer", "scope"],
            state="readonly",
            width=15
        )
        self.mode_combo.pack(side=tk.LEFT)
        self.mode_combo.bind("<<ComboboxSelected>>", self._show_mode_explanation)

        # Size filter
        size_frame = ttk.Frame(filters)
        size_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(size_frame, text="Min Size (KB):").pack(side=tk.LEFT, padx=(0, 5))
        self.min_size_var = tk.StringVar()
        self.min_size_entry = ttk.Entry(
            size_frame,
            textvariable=self.min_size_var,
            width=8
        )
        self.min_size_entry.pack(side=tk.LEFT)

        # Worker configuration
        worker_frame = ttk.Frame(filters)
        worker_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(worker_frame, text="Workers:").pack(side=tk.LEFT, padx=(0, 5))
        self.worker_var = tk.StringVar(value=str(self.client.concurrency))
        worker_entry = ttk.Entry(
            worker_frame,
            textvariable=self.worker_var,
            width=5
        )
        worker_entry.pack(side=tk.LEFT)
        worker_entry.bind("<Return>", lambda e: self._update_worker_count())

        # Date filter
        date_frame = ttk.Frame(filters)
        date_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(date_frame, text="Updated Since:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_filter = tk.StringVar(value="all time")
        date_combo = ttk.Combobox(
            date_frame,
            textvariable=self.date_filter,
            values=["all time", "last week", "last month", "last year", "custom date"],
            state="readonly",
            width=12
        )
        date_combo.pack(side=tk.LEFT)
        date_combo.bind("<<ComboboxSelected>>", self._on_date_change)

        # Custom date button
        self.date_btn_frame = ttk.Frame(filters)
        self.date_btn = ttk.Button(
            self.date_btn_frame,
            text="Select Date",
            style="Secondary.TButton",
            command=self._show_calendar
        )
        self.date_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.date_label = ttk.Label(self.date_btn_frame, text="", foreground=Theme.ACCENT)
        self.date_label.pack(side=tk.LEFT)

        # Max results input
        max_frame = ttk.Frame(filters)
        max_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(max_frame, text="Max Results:").pack(side=tk.LEFT, padx=(0, 5))
        self.max_results_var = tk.StringVar(value=str(DEFAULT_MAX_RESULTS))
        max_entry = ttk.Entry(
            max_frame,
            textvariable=self.max_results_var,
            width=10
        )
        max_entry.pack(side=tk.LEFT)
        max_entry.bind("<Return>", lambda e: self._validate_max_results())

        # Cache buttons
        ttk.Button(
            filters,
            text="Cache Stats",
            style="Secondary.TButton",
            command=self._show_cache_stats
        ).pack(side=tk.RIGHT, padx=(0, 5))

        ttk.Button(
            filters,
            text="Clear Cache",
            style="Secondary.TButton",
            command=self._clear_cache
        ).pack(side=tk.RIGHT)

        # Split panel for results and details
        paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Results
        left_panel = ttk.Frame(paned, padding=5)
        paned.add(left_panel, weight=2)

        # Results header
        results_header = ttk.Frame(left_panel)
        results_header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(results_header, text="Search Results", font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        self.results_count = ttk.Label(results_header, text="0 packages", foreground=Theme.TEXT_SECONDARY)
        self.results_count.pack(side=tk.LEFT, padx=10)

        # Selection controls
        sel_frame = ttk.Frame(results_header)
        sel_frame.pack(side=tk.RIGHT)

        ttk.Button(
            sel_frame,
            text="Select All",
            style="Secondary.TButton",
            command=self._select_all
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            sel_frame,
            text="Deselect All",
            style="Secondary.TButton",
            command=self._deselect_all
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            sel_frame,
            text="Download All",
            style="Warning.TButton",
            command=self._download_all
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            sel_frame,
            text="Download Selected",
            style="Success.TButton",
            command=self._download_selected
        ).pack(side=tk.LEFT, padx=5)

        self.fetch_details = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            sel_frame,
            text="Auto-enrich",
            variable=self.fetch_details
        ).pack(side=tk.LEFT, padx=5)

        # Results tree with enhanced columns
        tree_container = ttk.Frame(left_panel)
        tree_container.pack(fill=tk.BOTH, expand=True)

        self.results_tree = ttk.Treeview(
            tree_container,
            columns=("#", "name", "version", "files", "size", "dependencies", "dependents", "downloads", "last_publish"),
            show="tree headings",
            height=20
        )

        # Configure columns
        self.results_tree.heading("#0", text="")
        self.results_tree.heading("#", text="#", anchor='center')
        self.results_tree.heading("name", text="Package")
        self.results_tree.heading("version", text="Version", anchor='center')
        self.results_tree.heading("files", text="Files", anchor='center')
        self.results_tree.heading("size", text="Size", anchor='center')
        self.results_tree.heading("dependencies", text="Deps", anchor='center')
        self.results_tree.heading("dependents", text="Dependents", anchor='center')
        self.results_tree.heading("downloads", text="Downloads/wk", anchor='e')
        self.results_tree.heading("last_publish", text="Last Publish", anchor='center')

        # Set column widths
        self.results_tree.column("#0", width=30, stretch=False)
        self.results_tree.column("#", width=50, stretch=False, anchor='center')
        self.results_tree.column("name", width=200)
        self.results_tree.column("version", width=80, anchor='center')
        self.results_tree.column("files", width=80, anchor='center')
        self.results_tree.column("size", width=100, anchor='center')
        self.results_tree.column("dependencies", width=80, anchor='center')
        self.results_tree.column("dependents", width=100, anchor='center')
        self.results_tree.column("downloads", width=100, anchor='e')
        self.results_tree.column("last_publish", width=120, anchor='center')

        # Configure scrollbars
        scrollbar_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Pack widgets
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Bind events
        self.results_tree.bind("<ButtonRelease-1>", self._on_result_click)
        self.results_tree.bind("<space>", self._toggle_selection)
        self.results_tree.bind("<Double-1>", self._on_double_click)

        # Right panel - Details
        right_panel = ttk.Frame(paned, padding=5)
        paned.add(right_panel, weight=3)

        # Notebook for tabs
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Overview tab (with README)
        self._create_overview_tab()

        # File Tree tab
        self._create_file_tree_tab()

        # Dependencies tab
        self._create_dependencies_tab()

        # JSON tab
        self._create_json_tab()

        # Action buttons
        action_frame = ttk.Frame(right_panel)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            action_frame,
            text="Download",
            style="Primary.TButton",
            command=self._download_current
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text="NPM Page",
            style="Secondary.TButton",
            command=self.open_npm_page
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text="Repository",
            style="Secondary.TButton",
            command=self.open_repo
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text="Homepage",
            style="Secondary.TButton",
            command=self.open_homepage
        ).pack(side=tk.LEFT, padx=5)

        # Status bar
        status_container = ttk.Frame(main)
        status_container.pack(fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            status_container,
            textvariable=self.status_var,
            anchor=tk.W
        ).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        self.stats_label = ttk.Label(status_container, text="")
        self.stats_label.pack(side=tk.RIGHT, padx=10)

        # Progress bar
        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(5, 0))

        # Initial message
        self._clear_details()

    def _create_overview_tab(self):
        """Create the overview tab with package details and README"""
        overview_tab = ttk.Frame(self.notebook)
        self.notebook.add(overview_tab, text="Overview")

        # Create scrollable frame
        overview_scroll = ttk.Frame(overview_tab)
        overview_scroll.pack(fill=tk.BOTH, expand=True)

        overview_canvas = tk.Canvas(overview_scroll, bg=Theme.BG, highlightthickness=0)
        overview_scrollbar = ttk.Scrollbar(overview_scroll, orient=tk.VERTICAL, command=overview_canvas.yview)

        self.overview_content = ttk.Frame(overview_canvas)

        def on_overview_configure(event):
            overview_canvas.configure(scrollregion=overview_canvas.bbox("all"))

        self.overview_content.bind("<Configure>", on_overview_configure)

        overview_canvas.create_window((0, 0), window=self.overview_content, anchor="nw")
        overview_canvas.configure(yscrollcommand=overview_scrollbar.set)

        overview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        overview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_file_tree_tab(self):
        """Create the file tree tab for exploring package contents"""
        file_tree_tab = ttk.Frame(self.notebook)
        self.notebook.add(file_tree_tab, text="Files")

        # Create file tree viewer
        self.file_tree_viewer = FileTreeViewer(file_tree_tab, self._on_file_tree_select)

    def _create_dependencies_tab(self):
        """Create the dependencies tab with dependency and dependent information"""
        deps_tab = ttk.Frame(self.notebook)
        self.notebook.add(deps_tab, text="Dependencies")

        # Create a paned window for dependencies and dependents
        deps_paned = ttk.PanedWindow(deps_tab, orient=tk.VERTICAL)
        deps_paned.pack(fill=tk.BOTH, expand=True)

        # Dependencies section
        deps_frame = ttk.Frame(deps_paned)
        deps_paned.add(deps_frame, weight=1)

        deps_label = ttk.Label(deps_frame, text="Dependencies", font=('Segoe UI', 10, 'bold'))
        deps_label.pack(anchor=tk.W, padx=5, pady=(5, 0))

        deps_scroll = ttk.Frame(deps_frame)
        deps_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.deps_tree = ttk.Treeview(
            deps_scroll,
            columns=("name", "version", "size", "files", "last_publish"),
            show="tree headings"
        )

        self.deps_tree.heading("#0", text="")
        self.deps_tree.heading("name", text="Dependency")
        self.deps_tree.heading("version", text="Version")
        self.deps_tree.heading("size", text="Size")
        self.deps_tree.heading("files", text="Files")
        self.deps_tree.heading("last_publish", text="Last Publish")

        self.deps_tree.column("#0", width=30, stretch=False)
        self.deps_tree.column("name", width=200)
        self.deps_tree.column("version", width=100)
        self.deps_tree.column("size", width=80, anchor='center')
        self.deps_tree.column("files", width=80, anchor='center')
        self.deps_tree.column("last_publish", width=120, anchor='center')

        deps_scrollbar_y = ttk.Scrollbar(deps_scroll, orient=tk.VERTICAL, command=self.deps_tree.yview)
        self.deps_tree.configure(yscrollcommand=deps_scrollbar_y.set)

        self.deps_tree.grid(row=0, column=0, sticky="nsew")
        deps_scrollbar_y.grid(row=0, column=1, sticky="ns")

        deps_scroll.grid_rowconfigure(0, weight=1)
        deps_scroll.grid_columnconfigure(0, weight=1)

        # Dependents section
        dependents_frame = ttk.Frame(deps_paned)
        deps_paned.add(dependents_frame, weight=1)

        dependents_label = ttk.Label(dependents_frame, text="Dependents", font=('Segoe UI', 10, 'bold'))
        dependents_label.pack(anchor=tk.W, padx=5, pady=(5, 0))

        dependents_scroll = ttk.Frame(dependents_frame)
        dependents_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.dependents_tree = ttk.Treeview(
            dependents_scroll,
            columns=("name", "size", "files", "last_publish"),
            show="tree headings"
        )

        self.dependents_tree.heading("#0", text="")
        self.dependents_tree.heading("name", text="Dependent Package")
        self.dependents_tree.heading("size", text="Size")
        self.dependents_tree.heading("files", text="Files")
        self.dependents_tree.heading("last_publish", text="Last Publish")

        self.dependents_tree.column("#0", width=30, stretch=False)
        self.dependents_tree.column("name", width=200)
        self.dependents_tree.column("size", width=80, anchor='center')
        self.dependents_tree.column("files", width=80, anchor='center')
        self.dependents_tree.column("last_publish", width=120, anchor='center')

        dependents_scrollbar_y = ttk.Scrollbar(dependents_scroll, orient=tk.VERTICAL, command=self.dependents_tree.yview)
        self.dependents_tree.configure(yscrollcommand=dependents_scrollbar_y.set)

        self.dependents_tree.grid(row=0, column=0, sticky="nsew")
        dependents_scrollbar_y.grid(row=0, column=1, sticky="ns")

        dependents_scroll.grid_rowconfigure(0, weight=1)
        dependents_scroll.grid_columnconfigure(0, weight=1)

    def _create_json_tab(self):
        """Create the JSON tab with package data"""
        json_tab = ttk.Frame(self.notebook)
        self.notebook.add(json_tab, text="JSON")

        # Create scrollable frame
        json_scroll = ttk.Frame(json_tab)
        json_scroll.pack(fill=tk.BOTH, expand=True)

        json_canvas = tk.Canvas(json_scroll, bg=Theme.BG, highlightthickness=0)
        json_scrollbar = ttk.Scrollbar(json_scroll, orient=tk.VERTICAL, command=json_canvas.yview)

        self.json_content = ttk.Frame(json_canvas)

        def on_json_configure(event):
            json_canvas.configure(scrollregion=json_canvas.bbox("all"))

        self.json_content.bind("<Configure>", on_json_configure)

        json_canvas.create_window((0, 0), window=self.json_content, anchor="nw")
        json_canvas.configure(yscrollcommand=json_scrollbar.set)

        json_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        json_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create the JSON text widget
        self.json_text = tk.Text(
            self.json_content,
            wrap='word',
            bg=Theme.BG_SECONDARY,
            fg=Theme.TEXT,
            relief='flat',
            padx=10,
            pady=10,
            font=("Consolas", 9)
        )
        self.json_text.pack(fill=tk.BOTH, expand=True)

    def _update_search_history(self):
        """Update the search history dropdown"""
        recent_searches = self.search_history.get_recent_searches()
        search_list = [f"{query} ({mode})" for query, mode in recent_searches]
        self.search_history_combo['values'] = search_list

    def _on_history_selected(self, event=None):
        """Handle selection from search history"""
        selection = self.search_history_var.get()
        if selection:
            try:
                query_part = selection.rsplit(' (', 1)[0]
                mode_part = selection.rsplit(' (', 1)[1].rstrip(')')
                self.search_var.set(query_part)
                self.search_mode.set(mode_part)
            except:
                pass

    def _clear_search_history(self):
        """Clear the search history"""
        if messagebox.askyesno("Clear History", "Clear all search history?"):
            self.search_history.clear_history()
            self._update_search_history()
            self.status_var.set("Search history cleared")

    def _show_mode_explanation(self, event=None):
        """Show explanation for current search mode"""
        mode = self.search_mode.get()
        explanations = {
            "general": "Search across package names, descriptions, and keywords. Best for broad discovery.",
            "exact package": "Search for exact package name matches only. Use when you know the exact name.",
            "keywords": "Search only in package keywords. Find packages with specific functionality tags.",
            "author": "Search by package author name. Find all packages by a specific developer.",
            "maintainer": "Search by package maintainer name. Find packages maintained by specific people.",
            "scope": "Search within specific npm scopes (e.g., @angular, @react). Find packages from organizations."
        }
        explanation_text = explanations.get(mode, "No description available")
        self.status_var.set(f"Search mode: {explanation_text}")

    def _validate_max_results(self, event=None):
        """Validate max results input"""
        try:
            value = int(self.max_results_var.get())
            if value < 1:
                self.max_results_var.set(str(DEFAULT_MAX_RESULTS))
            elif value > 1000000:
                self.max_results_var.set("1000000")
        except ValueError:
            self.max_results_var.set(str(DEFAULT_MAX_RESULTS))

    def _on_date_change(self, event=None):
        if self.date_filter.get() == "custom date":
            self.date_btn_frame.pack(side=tk.LEFT, padx=(10, 0))
        else:
            self.date_btn_frame.pack_forget()
            self.selected_date = None
            self.date_label.config(text="")

    def _show_calendar(self):
        # This would typically open a calendar dialog
        # For simplicity, we'll just set today's date
        today = datetime.date.today()
        self.selected_date = today
        self.date_label.config(text=today.strftime("%Y-%m-%d"))

    def _show_cache_stats(self):
        stats = self.cache.get_stats()
        msg = f"""Cache Statistics:
Total Entries: {stats['total']}
Fresh Entries: {stats['fresh']}
Expired Entries: {stats['expired']}
Size: {stats['size']}
TTL: {self.cache.ttl_days} days"""
        messagebox.showinfo("Cache Statistics", msg)

    def _clear_cache(self):
        if messagebox.askyesno("Clear Cache", "Clear expired cache entries?"):
            self.cache.clear_expired()
            stats = self.cache.get_stats()
            messagebox.showinfo("Cache Cleared", f"Cache cleared. {stats['total']} entries remaining.")

    def _toggle_selection(self, event):
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            icon = self.results_tree.item(item, "text")
            self.results_tree.item(item, text="[X]" if icon == "[ ]" else "[ ]")

    def _select_all(self):
        for item in self.results_tree.get_children():
            self.results_tree.item(item, text="[X]")

    def _deselect_all(self):
        for item in self.results_tree.get_children():
            self.results_tree.item(item, text="[ ]")

    def _update_worker_count(self, event=None):
        """Update worker count and display"""
        try:
            workers = int(self.worker_var.get())
            if workers < 1:
                workers = 1
            elif workers > 50:
                workers = 50

            self.client.concurrency = workers
            npm_status = "npm Found" if self.client.npm_path else "npm Not Found"
            npm_color = Theme.SUCCESS if self.client.npm_path else Theme.ERROR
            self.worker_display.config(text=f"{workers} Workers | {npm_status}", foreground=npm_color)
            self.status_var.set(f"Worker count updated to {workers}")
        except ValueError:
            self.worker_var.set(str(self.client.concurrency))
            self.status_var.set("Invalid worker count")

    def _stop_search(self):
        """Stop current search"""
        self.search_stop_flag.set()
        self.stop_btn.pack_forget()
        self.status_var.set("Stopping search...")

    def _search_packages(self, event=None):
        """Search for NPM packages with various filters and options"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Input Required", "Please enter a search query")
            return

        # Add to search history
        self.search_history.add_search(query, self.search_mode.get())
        self._update_search_history()

        # Validate inputs
        self._validate_max_results()
        max_results = int(self.max_results_var.get())

        # Validate worker count and update display
        try:
            workers = int(self.worker_var.get())
            if workers < 1:
                workers = 1
            elif workers > 50:
                workers = 50
            self.client.concurrency = workers
        except:
            workers = self.client.concurrency

        # Update worker display in header
        npm_status = "npm Found" if self.client.npm_path else "npm Not Found"
        npm_color = Theme.SUCCESS if self.client.npm_path else Theme.ERROR
        self.worker_display.config(text=f"{workers} Workers | {npm_status}", foreground=npm_color)

        # Parse size filters
        size_min = None
        try:
            min_size_str = self.min_size_var.get().strip()
            if min_size_str:
                size_min = float(min_size_str)
                if size_min < 0:
                    size_min = None
        except:
            size_min = None

        # Parse date filter
        date_filter = None
        date_option = self.date_filter.get()
        if date_option == "last week":
            date_filter = datetime.datetime.now() - datetime.timedelta(days=7)
        elif date_option == "last month":
            date_filter = datetime.datetime.now() - datetime.timedelta(days=30)
        elif date_option == "last year":
            date_filter = datetime.datetime.now() - datetime.timedelta(days=365)
        elif date_option == "custom date" and self.selected_date:
            date_filter = datetime.datetime.combine(self.selected_date, datetime.time.min)

        # Parse search mode
        mode = self.search_mode.get()
        search_query = query

        if mode == "keywords":
            search_query = f"keywords:{query}"
        elif mode == "author":
            search_query = f"author:{query}"
        elif mode == "maintainer":
            search_query = f"maintainer:{query}"
        elif mode == "scope":
            search_query = f"scope:{query}"
        elif mode == "exact package":
            search_query = f"package:{query}"

        # Clear results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        self.all_results = []
        self.result_counter = 0
        self.package_items = {}
        self._clear_details()

        # Set searching state and show stop button
        self.is_searching = True
        self.search_stop_flag.clear()
        self.stop_btn.pack(side=tk.RIGHT, padx=10, pady=8)
        self.root.config(cursor="watch")
        self.status_var.set(f"Searching with {workers} workers...")
        self.progress["value"] = 0

        def perform_search():
            try:
                start_time = time.time()

                def progress_callback(current: int, total: int, max_results: int):
                    percent = (current / max_results) * 100
                    self.root.after(0, lambda p=percent: self.progress.configure(value=p))
                    self.root.after(0, lambda: self.status_var.set(f"Fetching: {current}/{max_results}"))

                def result_callback(packages: List[PackageInfo]):
                    for pkg in packages:
                        self.root.after(0, lambda p=pkg: self.add_package_to_results(p))

                packages = self.client.search_packages(
                    search_query,
                    date_filter=date_filter,
                    size_min=size_min,
                    max_results=max_results,
                    progress_callback=progress_callback,
                    result_callback=result_callback,
                    fetch_details=self.fetch_details.get()
                )

                self.all_results = packages
                elapsed = time.time() - start_time

                self.root.after(0, lambda: self.status_var.set(f"Found {len(packages)} packages in {elapsed:.1f}s"))
                self.root.after(0, lambda: self.results_count.config(text=f"{len(packages)} packages"))

                stats = self.client.get_stats()
                self.root.after(0, lambda: self.stats_label.config(
                    text=f"Requests: {stats['requests']} | Cache: {stats['cache_hit_rate']}"
                ))
            except Exception as e:
                logger.error(f"Search error: {e}")
                self.root.after(0, lambda: messagebox.showerror("Search Error", str(e)))
            finally:
                self.root.after(0, lambda: self.progress.configure(value=100))
                self.root.after(0, lambda: self.root.config(cursor=""))
                self.root.after(0, lambda: self.stop_btn.pack_forget())
                self.is_searching = False

        threading.Thread(target=perform_search, daemon=True).start()

    def add_package_to_results(self, pkg: PackageInfo):
        """Add a package to the results tree"""
        downloads = pkg.downloads_last_week if pkg.downloads_last_week > 0 else ''
        dependencies = pkg.dependencies_count if pkg.dependencies_count > 0 else ''
        dependents = pkg.dependents_count if pkg.dependents_count > 0 else ''

        # Create tags for color coding
        size_tag = f"size{self.result_counter}"
        time_tag = f"time{self.result_counter}"

        item = self.results_tree.insert(
            "",
            "end",
            text="[ ]",
            values=(
                self.result_counter,
                pkg.name,
                pkg.version,
                pkg.file_count,
                pkg.size_unpacked,
                dependencies,
                dependents,
                downloads,
                pkg.last_publish
            ),
            tags=(size_tag, time_tag)
        )

        # Configure color tags
        self.results_tree.tag_configure(size_tag, foreground=pkg.get_size_color())
        self.results_tree.tag_configure(time_tag, foreground=pkg.get_time_color())

        self.package_items[pkg.name] = item
        self.result_counter += 1

    def _on_result_click(self, event):
        region = self.results_tree.identify_region(event.x, event.y)
        if region == "tree":
            item = self.results_tree.identify_row(event.y)
            if item:
                icon = self.results_tree.item(item, "text")
                self.results_tree.item(item, text="[X]" if icon == "[ ]" else "[ ]")
            return

        selection = self.results_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.results_tree.item(item, "values")
        if values:
            package_name = values[1]
            if package_name:
                self.current_package = package_name
                self.root.config(cursor="watch")
                self.status_var.set(f"Loading: {package_name}")

                def fetch():
                    try:
                        pkg = self.client.get_comprehensive_data(package_name)
                        if pkg:
                            self.root.after(0, lambda: self._display_package(pkg))
                    except Exception as e:
                        logger.error(f"Error loading package: {e}")
                        self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                    finally:
                        self.root.after(0, lambda: self.root.config(cursor=""))
                        self.root.after(0, lambda: self.status_var.set("Ready"))

                threading.Thread(target=fetch, daemon=True).start()

    def _on_double_click(self, event):
        """Handle double-click on a package to open npm page"""
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            values = self.results_tree.item(item, "values")
            if values:
                package_name = values[1]
                if package_name:
                    webbrowser.open(f"https://www.npmjs.com/package/{package_name}")

    def _display_package(self, pkg: PackageInfo):
        """Display package details with proper markdown rendering"""
        # Clear overview content
        for widget in self.overview_content.winfo_children():
            widget.destroy()

        # Clear dependencies and dependents trees
        for item in self.deps_tree.get_children():
            self.deps_tree.delete(item)
        for item in self.dependents_tree.get_children():
            self.dependents_tree.delete(item)

        # Header with install command
        header = ttk.Frame(self.overview_content)
        header.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(header, text=pkg.name, font=('Segoe UI', 14, 'bold')).pack(anchor=tk.W, padx=15, pady=(10, 2))
        ttk.Label(header, text=f"v{pkg.version}", foreground=Theme.TEXT_SECONDARY).pack(anchor=tk.W, padx=15, pady=(0, 5))

        # Install command
        install_frame = ttk.Frame(header)
        install_frame.pack(anchor=tk.W, padx=15, pady=(0, 10))

        ttk.Label(install_frame, text="Install:").pack(side=tk.LEFT)
        install_cmd = f"npm install {pkg.name}"
        cmd_label = ttk.Label(install_frame, text=install_cmd, foreground=Theme.ACCENT, font=("Consolas", 9))
        cmd_label.pack(side=tk.LEFT, padx=5)

        # Copy install command
        def copy_install_cmd():
            self.root.clipboard_clear()
            self.root.clipboard_append(install_cmd)
            self.status_var.set("Install command copied to clipboard")

        ttk.Button(install_frame, text="Copy", style="Secondary.TButton", command=copy_install_cmd).pack(side=tk.LEFT)

        # Description
        if pkg.description:
            desc_frame = ttk.Frame(self.overview_content)
            desc_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
            ttk.Label(desc_frame, text=pkg.description, wraplength=600, justify=tk.LEFT).pack(anchor=tk.W)

        # README section
        if pkg.readme and pkg.readme.strip():
            readme_frame = ttk.Frame(self.overview_content)
            readme_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15), padx=5)

            ttk.Label(readme_frame, text="README", font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))

            # Create a frame for README content
            readme_container = ttk.Frame(readme_frame)
            readme_container.pack(fill=tk.BOTH, expand=True)

            # Create a frame for the markdown text widget
            readme_text_frame = ttk.Frame(readme_container)
            readme_text_frame.pack(fill=tk.BOTH, expand=True)

            # Create the markdown text widget
            self.readme_text = tk.Text(
                readme_text_frame,
                wrap='word',
                bg=Theme.BG_SECONDARY,
                fg=Theme.TEXT,
                relief='flat',
                padx=10,
                pady=10,
                font=("Segoe UI", 10)
            )

            # Initialize markdown renderer
            self.markdown_renderer = MarkdownRenderer(self.readme_text)

            # Render the README
            self.markdown_renderer.render(pkg.readme)

            # Add scrollbar
            readme_scrollbar = ttk.Scrollbar(readme_container, orient=tk.VERTICAL, command=self.readme_text.yview)
            self.readme_text.configure(yscrollcommand=readme_scrollbar.set)

            self.readme_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            readme_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Enhanced info fields
        info_data = [
            ("Unpacked Size", pkg.size_unpacked),
            ("Total Files", pkg.file_count),
            ("Weekly Downloads", str(pkg.downloads_last_week) if pkg.downloads_last_week else 'N/A'),
            ("Download Trend", pkg.downloads_trend),
            ("Last Publish", pkg.last_publish),
            ("Published Date", pkg.published_date),
            ("Last Modified", pkg.modified_date),
            ("License", pkg.license),
            ("Author", pkg.author),
            ("Dependencies", f"{pkg.dependencies_count} ({len(pkg.dependencies) if pkg.dependencies else 0} direct)"),
            ("Dev Dependencies", str(pkg.dev_dependencies_count)),
            ("Peer Dependencies", str(pkg.peer_dependencies_count)),
            ("Dependents", str(pkg.dependents_count)),
            ("Total Versions", str(pkg.total_versions)),
            ("Maintainers", str(pkg.maintainers_count)),
            ("Has TypeScript", "Yes" if pkg.has_typescript else "No"),
            ("Has Tests", "Yes" if pkg.has_tests else "No"),
            ("Has Readme", "Yes" if pkg.has_readme else "No"),
            ("Quality Score", f"{pkg.score_quality:.2f}"),
            ("Popularity Score", f"{pkg.score_popularity:.2f}"),
            ("Maintenance Score", f"{pkg.score_maintenance:.2f}"),
            ("Final Score", f"{pkg.score_final:.2f}"),
        ]

        for label, value in info_data:
            if value and value != 'Unknown' and value != 'N/A' and value != '0':
                row = ttk.Frame(self.overview_content)
                row.pack(fill=tk.X, pady=3, padx=5)
                ttk.Label(row, text=label, width=20, anchor=tk.W).pack(side=tk.LEFT)
                ttk.Label(row, text=value, font=('Segoe UI', 9, 'bold'), anchor=tk.W).pack(
                    side=tk.LEFT, fill=tk.X, expand=True
                )

        # URLs section
        if pkg.homepage or pkg.repository:
            ttk.Separator(self.overview_content, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

            urls_frame = ttk.Frame(self.overview_content)
            urls_frame.pack(fill=tk.X, padx=5)

            if pkg.homepage:
                homepage_frame = ttk.Frame(urls_frame)
                homepage_frame.pack(fill=tk.X, pady=2)
                ttk.Label(homepage_frame, text="Homepage:", width=10, anchor=tk.W).pack(side=tk.LEFT)
                homepage_btn = ttk.Button(
                    homepage_frame,
                    text=pkg.homepage,
                    style="Secondary.TButton",
                    command=lambda: self.open_url(pkg.homepage)
                )
                homepage_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

            if pkg.repository:
                repo_frame = ttk.Frame(urls_frame)
                repo_frame.pack(fill=tk.X, pady=2)
                ttk.Label(repo_frame, text="Repository:", width=10, anchor=tk.W).pack(side=tk.LEFT)
                repo_btn = ttk.Button(
                    repo_frame,
                    text=pkg.repository,
                    style="Secondary.TButton",
                    command=lambda: self.open_url(pkg.repository)
                )
                repo_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Keywords section
        if pkg.keywords:
            ttk.Separator(self.overview_content, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

            ttk.Label(self.overview_content, text="Keywords", font=('Segoe UI', 10, 'bold')).pack(
                anchor=tk.W, pady=(0, 10), padx=5
            )

            keywords_text = ', '.join(pkg.keywords[:20])
            if len(pkg.keywords) > 20:
                keywords_text += f" ... and {len(pkg.keywords) - 20} more"

            ttk.Label(self.overview_content, text=keywords_text, wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, padx=5)

        # Update dependencies and dependents tabs with detailed information
        if pkg.dependency_details:
            for dep_name, details in pkg.dependency_details.items():
                self.deps_tree.insert(
                    "",
                    "end",
                    text="",
                    values=(
                        dep_name,
                        details.get('version', 'N/A'),
                        details.get('size', 'N/A'),
                        details.get('files', 'N/A'),
                        details.get('last_publish', 'N/A')
                    )
                )
        else:
            self.deps_tree.insert("", "end", text="", values=("No dependencies found", "", "", "", ""))

        if pkg.dependents:
            for dep_name in pkg.dependents[:20]:  # Limit to 20 dependents
                self.dependents_tree.insert("", "end", text="", values=(dep_name, "N/A", "N/A", "N/A"))
        elif pkg.dependents_count > 0:
            self.dependents_tree.insert("", "end", text="", values=(f"{pkg.dependents_count} dependents (not loaded)", "", "", ""))
        else:
            self.dependents_tree.insert("", "end", text="", values=("No dependents found", "", "", ""))

        # Update JSON tab
        self.json_text.delete('1.0', 'end')
        json_data = json.dumps(pkg.to_dict(), indent=2)
        self.json_text.insert('1.0', json_data)

        # Update file tree tab
        if pkg.file_tree:
            self.file_tree_viewer.load_package(pkg.name, pkg.file_tree)

        self.status_var.set(f"Loaded: {pkg.name}")

    def _clear_details(self):
        """Clear details panels"""
        # Clear overview content
        for widget in self.overview_content.winfo_children():
            widget.destroy()

        self.json_text.delete('1.0', 'end')

        ttk.Label(
            self.overview_content,
            text="Select a package to view details",
            foreground=Theme.TEXT_MUTED,
            font=("Segoe UI", 10, "italic")
        ).pack(expand=True)

    def _download_selected(self):
        selected_packages = []
        for item in self.results_tree.get_children():
            if self.results_tree.item(item, "text") == "[X]":
                values = self.results_tree.item(item, "values")
                if values:
                    selected_packages.append(values[1])

        if not selected_packages:
            messagebox.showwarning("No Selection", "Please select at least one package")
            return

        self._confirm_and_download(selected_packages, "selected packages")

    def _download_all(self):
        if not self.all_results:
            messagebox.showwarning("No Results", "No packages to download")
            return

        package_names = [pkg.name for pkg in self.all_results]
        self._confirm_and_download(package_names, "all packages")

    def _download_current(self):
        if not self.current_package:
            messagebox.showwarning("No Selection", "Please select a package")
            return

        self._confirm_and_download([self.current_package], "current package")

    def _confirm_and_download(self, packages: List[str], description: str):
        """Confirm and download selected packages"""
        if not packages:
            return

        if not self.client.npm_path:
            messagebox.showerror(
                "npm Not Found",
                "npm is not installed or not in PATH.\n\n"
                "Please install Node.js and npm:\n"
                "https://nodejs.org/"
            )
            return

        # Use configured download directory
        download_dir = self.settings.get_download_dir()

        # Create a subdirectory for this batch
        batch_dir = os.path.join(download_dir, f"npm_downloads_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        os.makedirs(batch_dir, exist_ok=True)

        self.client.set_download_dir(batch_dir)

        response = messagebox.askyesno(
            "Confirm Download",
            f"Download {len(packages)} {description} to:\n{batch_dir}?"
        )

        if not response:
            return

        self.root.config(cursor="watch")
        self.status_var.set(f"Downloading {len(packages)} packages...")
        self.progress["value"] = 0

        def do_download():
            try:
                def progress_callback(current: int, total: int, result: Dict):
                    percent = (current / total) * 100
                    self.root.after(0, lambda p=percent: self.progress.configure(value=p))
                    self.root.after(0, lambda: self.status_var.set(
                        f"Downloading: {current}/{total} - {result['package']}"
                    ))

                results = self.client.download_packages_concurrent(
                    packages,
                    progress_callback=progress_callback
                )

                success = sum(1 for r in results if r['success'])
                failed = [r for r in results if not r['success']]

                # Show detailed results
                if failed:
                    failed_msg = "\nFailed downloads:\n" + "\n".join([
                        f"- {pkg['package']}: {pkg['error']}"
                        for pkg in failed[:5]
                    ])
                    if len(failed) > 5:
                        failed_msg += f"\n... and {len(failed) - 5} more"

                    messagebox.showwarning(
                        "Download Complete with Errors",
                        f"Downloaded {success}/{len(packages)} packages successfully to:\n{batch_dir}\n{failed_msg}"
                    )
                else:
                    messagebox.showinfo(
                        "Download Complete",
                        f"Downloaded {success}/{len(packages)} packages successfully to:\n{batch_dir}"
                    )

                self.root.after(0, lambda: self.status_var.set(
                    f"Downloaded {success}/{len(packages)} packages"
                ))

                # Auto-open folder if enabled
                if self.settings.get_bool('General', 'auto_open_folder', True):
                    try:
                        if IS_WINDOWS:
                            os.startfile(batch_dir)
                        elif IS_MAC:
                            subprocess.run(['open', batch_dir])
                        else:
                            subprocess.run(['xdg-open', batch_dir])
                    except:
                        pass
            except Exception as e:
                logger.error(f"Download error: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Download Error", str(e)))
            finally:
                self.root.after(0, lambda: self.progress.configure(value=100))
                self.root.after(0, lambda: self.root.config(cursor=""))

        threading.Thread(target=do_download, daemon=True).start()

    def open_npm_page(self):
        if self.current_package:
            self.open_url(f"https://www.npmjs.com/package/{self.current_package}")

    def open_repo(self):
        if self.current_package:
            def fetch_repo():
                try:
                    pkg = self.client.get_comprehensive_data(self.current_package)
                    if pkg and pkg.repository:
                        self.root.after(0, lambda: self.open_url(pkg.repository))
                    else:
                        self.root.after(0, lambda: messagebox.showinfo(
                            "No Repository",
                            "No repository URL found"
                        ))
                except Exception as e:
                    logger.error(f"Error opening repository: {e}")

            threading.Thread(target=fetch_repo, daemon=True).start()

    def open_homepage(self):
        if self.current_package:
            def fetch_homepage():
                try:
                    pkg = self.client.get_comprehensive_data(self.current_package)
                    if pkg and pkg.homepage:
                        self.root.after(0, lambda: self.open_url(pkg.homepage))
                    else:
                        self.root.after(0, lambda: messagebox.showinfo(
                            "No Homepage",
                            "No homepage URL found"
                        ))
                except Exception as e:
                    logger.error(f"Error opening homepage: {e}")

            threading.Thread(target=fetch_homepage, daemon=True).start()

    def open_url(self, url: str):
        """Open a URL in the default browser"""
        try:
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Error opening URL: {e}")
            messagebox.showerror("Error", f"Could not open URL: {url}")

    def _open_settings(self):
        """Open settings dialog"""
        # This would typically open a settings dialog
        # For simplicity, we'll just show a message
        messagebox.showinfo("Settings", "Settings dialog would open here")

    def _on_file_tree_select(self, package_name: str):
        """Handle file tree selection"""
        # This is called when a package is selected in the file tree viewer
        # We don't need to do anything here as the file tree viewer handles its own updates
        pass

    def on_close(self):
        """Handle application close"""
        # Clean up resources
        if self.cache:
            self.cache.close()
        if self.search_history:
            self.search_history.close()
        self.root.destroy()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = NPMAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()