#!/usr/bin/env python3
"""
Entry point for running the analysis module as a script.

Usage:
    python -m graph_sitter.adapters.analysis <path>
    python -m graph_sitter.adapters.analysis.cli <path>
"""

from .cli import main

if __name__ == "__main__":
    main()

