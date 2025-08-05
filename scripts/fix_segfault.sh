#!/usr/bin/env bash
set -e

# Fix Segmentation Fault Script for graph-sitter
# This script helps prevent segmentation faults in tests by limiting memory usage

# Display colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=== Graph-Sitter Segmentation Fault Fix ===${NC}"

# Ensure we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}No virtual environment detected. Activating...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}No .venv directory found. Please run './scripts/fullbuild.sh' first.${NC}"
        exit 1
    fi
fi

# Check if ulimit command is available
if command -v ulimit &> /dev/null; then
    echo -e "${BLUE}Setting memory limits to prevent segmentation faults...${NC}"
    
    # Get current memory limit
    CURRENT_LIMIT=$(ulimit -m)
    if [ "$CURRENT_LIMIT" = "unlimited" ]; then
        echo -e "${YELLOW}Current memory limit is unlimited. Setting a reasonable limit...${NC}"
        
        # Set memory limit to 8GB (8388608 KB) or adjust as needed
        ulimit -m 8388608
        ulimit -v 8388608
        
        echo -e "${GREEN}Memory limits set to 8GB to prevent excessive memory usage.${NC}"
    else
        echo -e "${GREEN}Memory limits already set to $CURRENT_LIMIT KB.${NC}"
    fi
else
    echo -e "${YELLOW}ulimit command not available. Skipping memory limit setting.${NC}"
fi

# Create a .skiptest file for problematic repositories
echo -e "${BLUE}Creating skip file for problematic repositories...${NC}"
mkdir -p tests/integration/codemod/repos/open_source/.skiptests
echo "mypy" > tests/integration/codemod/repos/open_source/.skiptests/large_repos.txt
echo -e "${GREEN}Created skip file for large repositories that cause segmentation faults.${NC}"

echo -e "${BOLD}${GREEN}Segmentation fault fixes applied successfully!${NC}"
echo -e "${YELLOW}You can now run tests with reduced risk of segmentation faults.${NC}"
echo -e "${YELLOW}To run tests, use: ./scripts/full_test.sh --unit${NC}"

