#!/bin/bash

# Installation script for Graph Sitter package

set -e

echo "📦 Installing Graph Sitter package..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the graph_sitter_package directory."
    exit 1
fi

pip install -e .

echo "✅ Graph Sitter package installed successfully!"
echo ""
echo "🎯 You can now use:"
echo "  - gs --help          (Graph Sitter CLI)"
echo ""
echo "📚 Import in Python:"
echo "  - from graph_sitter import Codebase"

