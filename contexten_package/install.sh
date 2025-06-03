#!/bin/bash

# Installation script for Contexten package

set -e

echo "🤖 Installing Contexten package..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the contexten_package directory."
    exit 1
fi

pip install -e .

echo "✅ Contexten package installed successfully!"
echo ""
echo "🎯 You can now use:"
echo "  - contexten --help   (Contexten CLI)"
echo "  - contexten-dashboard (Contexten Dashboard)"
echo ""
echo "📚 Import in Python:"
echo "  - from contexten import FlowManager"

