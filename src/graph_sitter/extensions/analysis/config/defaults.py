#!/usr/bin/env python3
"""
Default Analysis Configuration

Provides default configurations for all analysis tools and system settings.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field

# Default tool configurations
DEFAULT_TOOL_CONFIGS = {
    "ruff": {
        "enabled": True,
        "command": "ruff",
        "args": [
            "check",
            "--output-format=json",
            "--select=E,W,F,I,N",  # Basic rules by default
        ],
        "timeout": 180,
        "priority": 1,
        "requires_network": False,
        "description": "Fast Python linter and code formatter",
        "categories": ["syntax", "style", "imports", "logic"]
    },
    
    "mypy": {
        "enabled": True,
        "command": "mypy",
        "args": [
            "--show-error-codes",
            "--show-column-numbers",
            "--no-error-summary",
            "--ignore-missing-imports",
        ],
        "timeout": 300,
        "priority": 1,
        "requires_network": False,
        "description": "Static type checker for Python",
        "categories": ["type_checking"]
    },
    
    "pyflakes": {
        "enabled": False,  # Disabled by default since ruff covers most of this
        "command": "pyflakes",
        "args": [],
        "timeout": 60,
        "priority": 2,
        "requires_network": False,
        "description": "Checks Python source files for errors",
        "categories": ["logic_error"]
    },
    
    "pycodestyle": {
        "enabled": False,  # Disabled by default since ruff covers this
        "command": "pycodestyle",
        "args": ["--statistics", "--count"],
        "timeout": 120,
        "priority": 3,
        "requires_network": False,
        "description": "Python style guide checker (PEP 8)",
        "categories": ["style_formatting"]
    },
    
    "bandit": {
        "enabled": False,  # Optional security tool
        "command": "bandit",
        "args": ["-f", "json"],
        "timeout": 300,
        "priority": 2,
        "requires_network": False,
        "description": "Security linter for Python",
        "categories": ["security"]
    },
    
    "safety": {
        "enabled": False,  # Optional vulnerability checker
        "command": "safety",
        "args": ["check", "--json"],
        "timeout": 60,
        "priority": 2,
        "requires_network": True,
        "description": "Checks Python dependencies for known vulnerabilities",
        "categories": ["security", "dependencies"]
    },
    
    "lsp": {
        "enabled": False,  # Optional LSP integration
        "command": "pylsp",
        "args": ["--stdio"],
        "timeout": 120,
        "priority": 2,
        "requires_network": False,
        "description": "Language Server Protocol diagnostics",
        "categories": ["type_checking", "general"]
    }
}

# Analysis profiles for different use cases
ANALYSIS_PROFILES = {
    "basic": {
        "name": "Basic Analysis",
        "description": "Fast analysis with essential tools",
        "enabled_tools": ["ruff"],
        "max_parallel": 2,
        "timeout_multiplier": 1.0
    },
    
    "standard": {
        "name": "Standard Analysis", 
        "description": "Balanced analysis with core tools",
        "enabled_tools": ["ruff", "mypy"],
        "max_parallel": 3,
        "timeout_multiplier": 1.2
    },
    
    "comprehensive": {
        "name": "Comprehensive Analysis",
        "description": "Complete analysis with all available tools",
        "enabled_tools": ["ruff", "mypy", "pyflakes", "pycodestyle", "bandit", "lsp"],
        "max_parallel": 4,
        "timeout_multiplier": 1.5
    },
    
    "security": {
        "name": "Security Focus",
        "description": "Security-focused analysis",
        "enabled_tools": ["ruff", "bandit", "safety"],
        "max_parallel": 2,
        "timeout_multiplier": 1.3
    },
    
    "type_checking": {
        "name": "Type Checking Focus",
        "description": "Focus on type safety and correctness",
        "enabled_tools": ["mypy", "ruff", "lsp"],
        "max_parallel": 3,
        "timeout_multiplier": 1.4
    }
}

# Default system configuration
DEFAULT_CONFIG = {
    "analysis": {
        "profile": "standard",
        "parallel_execution": True,
        "max_parallel_tools": 3,
        "timeout_multiplier": 1.0,
        "store_results": True,
        "auto_fix_enabled": False,  # AI fixing disabled by default
        
        "output": {
            "format": "console",  # console, json, html
            "verbosity": "normal",  # quiet, normal, verbose
            "show_progress": True,
            "color": True
        },
        
        "filtering": {
            "min_severity": "INFO",  # ERROR, WARNING, INFO, HINT
            "exclude_files": [
                "*.pyc",
                "__pycache__/*",
                ".git/*",
                "*.egg-info/*",
                "build/*",
                "dist/*"
            ],
            "exclude_dirs": [
                "__pycache__",
                ".git",
                ".venv",
                "venv",
                "node_modules",
                ".pytest_cache",
                ".mypy_cache"
            ],
            "max_errors_per_file": 50
        },
        
        "caching": {
            "enabled": True,
            "cache_dir": ".gs_analysis_cache",
            "cache_duration_hours": 24
        }
    },
    
    "tools": DEFAULT_TOOL_CONFIGS,
    "profiles": ANALYSIS_PROFILES,
    
    "database": {
        "enabled": True,
        "path": ".gs_analysis.db",
        "retention_days": 30,
        "auto_cleanup": True
    },
    
    "integrations": {
        "graph_sitter": {
            "enabled": True,
            "config": {
                "method_usages": True,
                "generics": True,
                "sync_enabled": True,
                "full_range_index": True
            }
        },
        "lsp": {
            "enabled": False,
            "servers": {
                "python": {
                    "command": "pylsp",
                    "args": ["--stdio"],
                    "timeout": 120
                }
            }
        },
        "ai_fixing": {
            "enabled": False,
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "max_fixes_per_session": 10
        }
    }
}

# Environment-specific overrides
ENVIRONMENT_OVERRIDES = {
    "ci": {
        "analysis": {
            "output": {
                "format": "json",
                "show_progress": False
            },
            "timeout_multiplier": 0.8,
            "max_parallel_tools": 2
        },
        "tools": {
            "safety": {"enabled": True},  # Enable security checks in CI
            "bandit": {"enabled": True}
        }
    },
    
    "development": {
        "analysis": {
            "profile": "basic",
            "auto_fix_enabled": True,
            "output": {"verbosity": "verbose"}
        }
    },
    
    "production": {
        "analysis": {
            "profile": "security",
            "timeout_multiplier": 2.0,
            "max_parallel_tools": 1
        },
        "tools": {
            "safety": {"enabled": True, "requires_network": True},
            "bandit": {"enabled": True}
        }
    }
}