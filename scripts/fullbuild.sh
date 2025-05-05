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

echo -e "${BLUE}=== Graph-Sitter Full Build Script ===${NC}"
echo -e "${BLUE}This script will set up a complete development environment${NC}"
echo

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  OS="macOS"
else
  OS="Unknown"
  echo -e "${YELLOW}Warning: Unsupported OS detected. This script is optimized for Linux and macOS.${NC}"
  echo -e "${YELLOW}Some steps may not work correctly.${NC}"
fi

echo -e "${BLUE}Detected OS: ${OS}${NC}"
echo

# Install system dependencies
echo -e "${BLUE}Installing system dependencies...${NC}"
if [[ "$OS" == "Linux" ]]; then
  echo -e "${YELLOW}Running: sudo apt update && sudo apt install -y gcc build-essential python3-dev libpixman-1-dev libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev jq${NC}"
  sudo apt update && sudo apt install -y gcc build-essential python3-dev libpixman-1-dev libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev jq
  
  echo -e "${YELLOW}Running: sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git${NC}"
  sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git
  
  echo -e "${YELLOW}Running: sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev${NC}"
  sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev
elif [[ "$OS" == "macOS" ]]; then
  echo -e "${YELLOW}Running: brew install jq${NC}"
  brew install jq
fi

# Install UV package manager
echo -e "${BLUE}Installing UV package manager...${NC}"
if command -v uv &> /dev/null; then
  echo -e "${GREEN}UV is already installed.${NC}"
else
  echo -e "${YELLOW}Installing UV...${NC}"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  
  # Add UV to PATH for this session
  export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create and activate virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
if [ -d ".venv" ]; then
  echo -e "${YELLOW}Existing virtual environment found. Removing...${NC}"
  rm -rf .venv
fi

uv venv
if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to create virtual environment.${NC}"
  exit 1
fi

echo -e "${GREEN}Virtual environment created.${NC}"
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate
if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
  exit 1
fi
echo -e "${GREEN}Virtual environment activated.${NC}"

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
uv sync --dev
if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to install dependencies.${NC}"
  exit 1
fi
echo -e "${GREEN}Dependencies installed successfully.${NC}"

# Install development tools
echo -e "${BLUE}Installing development tools...${NC}"
uv tool install deptry
uv tool update-shell
echo -e "${GREEN}Development tools installed.${NC}"

# Install pre-commit hooks
echo -e "${BLUE}Installing pre-commit hooks...${NC}"
uv tool install pre-commit --with pre-commit-uv
pre-commit install
pre-commit install-hooks
echo -e "${GREEN}Pre-commit hooks installed.${NC}"

# Run setup scripts if they exist
if [ -f "install-deps.sh" ]; then
  echo -e "${BLUE}Running install-deps.sh...${NC}"
  bash install-deps.sh
  echo -e "${GREEN}install-deps.sh completed.${NC}"
fi

if [ -f "setup.sh" ]; then
  echo -e "${BLUE}Running setup.sh...${NC}"
  bash setup.sh
  echo -e "${GREEN}setup.sh completed.${NC}"
fi

# Build Cython modules
echo -e "${BLUE}Building Cython modules...${NC}"
python setup.py build_ext --inplace
if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to build Cython modules.${NC}"
  exit 1
fi
echo -e "${GREEN}Successfully built Cython modules.${NC}"

# Install the package in development mode
echo -e "${BLUE}Installing package in development mode...${NC}"
uv pip install -e .
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
fi

echo
echo -e "${GREEN}Full build process completed!${NC}"
echo -e "${BLUE}Your development environment is now set up and ready to use.${NC}"
echo -e "${BLUE}You can activate the virtual environment in future sessions with:${NC}"
echo -e "${YELLOW}  source .venv/bin/activate${NC}"

