#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RUN_TESTS=false

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --test)
      RUN_TESTS=true
      shift
      ;;
    *)
      # Unknown option
      ;;
  esac
done

echo -e "${BLUE}=== Graph-Sitter Build and Test Script ===${NC}"
echo -e "${BLUE}This script will compile Cython modules and optionally run tests${NC}"
echo

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
  echo -e "${YELLOW}Warning: No active virtual environment detected.${NC}"
  echo -e "${YELLOW}It's recommended to run this script within a virtual environment.${NC}"
  echo -e "${YELLOW}You can create one with: uv venv && source .venv/bin/activate${NC}"
  echo
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted.${NC}"
    exit 1
  fi
fi

# Ensure we're in the project root directory
if [ ! -f "pyproject.toml" ]; then
  echo -e "${RED}Error: pyproject.toml not found. Please run this script from the project root directory.${NC}"
  exit 1
fi

# Install Cython if not already installed
echo -e "${BLUE}Checking for Cython...${NC}"
python -c "import Cython" 2>/dev/null
if [ $? -ne 0 ]; then
  echo -e "${YELLOW}Cython not found. Installing...${NC}"
  if command -v uv &> /dev/null; then
    uv pip install Cython
  else
    pip install Cython
  fi
else
  echo -e "${GREEN}Cython is already installed.${NC}"
fi

# Build Cython modules
echo -e "${BLUE}Building Cython modules...${NC}"
python setup.py build_ext --inplace
if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to build Cython modules.${NC}"
  exit 1
fi
echo -e "${GREEN}Successfully built Cython modules.${NC}"

# Install the package in development mode if not already installed
echo -e "${BLUE}Installing package in development mode...${NC}"
if command -v uv &> /dev/null; then
  uv pip install -e .
else
  pip install -e .
fi

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to install package in development mode.${NC}"
  exit 1
fi
echo -e "${GREEN}Successfully installed package in development mode.${NC}"

# Run tests if requested
if [ "$RUN_TESTS" = true ]; then
  echo -e "${BLUE}Running tests...${NC}"
  echo -e "${YELLOW}Note: Using -p no:xdist -p no:cov to disable distributed testing and coverage plugins which might cause issues.${NC}"
  python -m pytest tests/unit -v -p no:xdist -p no:cov
  TEST_RESULT=$?
  if [ $TEST_RESULT -ne 0 ]; then
    echo -e "${RED}Some tests failed.${NC}"
  else
    echo -e "${GREEN}All tests passed!${NC}"
  fi
else
  echo -e "${BLUE}Tests not run. Use --test flag to run tests.${NC}"
  echo -e "${YELLOW}You can run tests manually with:${NC}"
  echo -e "${YELLOW}  python -m pytest tests/unit -v -p no:xdist -p no:cov${NC}"
  echo -e "${YELLOW}  # Or run specific test files:${NC}"
  echo -e "${YELLOW}  python -m pytest tests/unit/specific/path/to/test_file.py -v -p no:xdist -p no:cov${NC}"
fi

echo
echo -e "${GREEN}Build process completed!${NC}"
echo -e "${BLUE}You should now be able to import and use the graph_sitter modules.${NC}"

