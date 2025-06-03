#!/bin/bash

# Installation script for both graph_sitter and contexten packages

set -e

echo "🚀 Installing Graph Sitter and Contexten packages..."

# Check if we're in the right directory
if [ ! -d "graph_sitter_package" ] || [ ! -d "contexten_package" ]; then
    echo "❌ Error: Package directories not found. Please run this script from the project root."
    exit 1
fi

echo "📦 Installing Graph Sitter package..."
cd graph_sitter_package
pip install -e .
cd ..

echo "🤖 Installing Contexten package..."
cd contexten_package
pip install -e .
cd ..

echo "✅ Both packages installed successfully!"
echo ""
echo "🎯 You can now use:"
echo "  - gs --help          (Graph Sitter CLI)"
echo "  - contexten --help   (Contexten CLI)"
echo "  - contexten-dashboard (Contexten Dashboard)"
echo ""
echo "📚 Import in Python:"
echo "  - from graph_sitter import Codebase"
echo "  - from contexten import FlowManager"

