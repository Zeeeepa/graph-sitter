#!/usr/bin/env bash
set -e

# Full Build Script for graph-sitter
# This script installs all dependencies and sets up the development environment

# Display colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Graph-Sitter Full Build Script ===${NC}"

# Step 1: Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
SUDO=""
if command -v sudo &> /dev/null; then
    SUDO="sudo"
fi

if command -v apt &> /dev/null; then
    # Install all required system dependencies
    $SUDO apt update
    $SUDO apt install -y gcc build-essential python3-dev libpixman-1-dev libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev jq
    $SUDO apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
        libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
        xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git
elif command -v brew &> /dev/null; then
    # macOS dependencies
    brew install jq
    brew install openssl readline sqlite3 xz zlib tcl-tk
else
    echo -e "${YELLOW}Unsupported package manager. Installing minimal dependencies...${NC}"
    if command -v dnf &> /dev/null; then
        $SUDO dnf install -y jq gcc python3-devel
    elif command -v yum &> /dev/null; then
        $SUDO yum install -y jq gcc python3-devel
    elif command -v pacman &> /dev/null; then
        $SUDO pacman -Sy jq gcc python
    else
        echo -e "${RED}Could not install system dependencies automatically.${NC}"
        echo -e "${YELLOW}Please install the following packages manually:${NC}"
        echo "- gcc/build-essential"
        echo "- python3-dev"
        echo "- jq"
        echo "- libpixman, libcairo, libpango, libjpeg, libgif, librsvg"
    fi
fi

# Step 2: Install UV package manager
echo -e "${YELLOW}Installing UV package manager...${NC}"
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add UV to PATH for this session
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Step 3: Create and activate virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Removing existing virtual environment...${NC}"
    rm -rf .venv
fi

uv venv
source .venv/bin/activate

# Step 4: Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
uv sync --dev

# Step 5: Install development tools
echo -e "${YELLOW}Installing development tools...${NC}"
uv tool install deptry
uv tool update-shell

# Step 6: Install pre-commit hooks
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
uv tool install pre-commit --with pre-commit-uv
pre-commit install
pre-commit install-hooks

# Step 7: Run additional setup scripts
echo -e "${YELLOW}Running additional setup scripts...${NC}"
if [ -f "./scripts/install-deps.sh" ]; then
    bash ./scripts/install-deps.sh
fi

if [ -f "./scripts/setup.sh" ]; then
    bash ./scripts/setup.sh
fi

# Step 8: Install Cython if not already installed
echo -e "${YELLOW}Checking for Cython...${NC}"
if ! python -c "import Cython" &> /dev/null; then
    echo -e "${YELLOW}Installing Cython...${NC}"
    uv pip install cython
fi

# Step 9: Compile Cython modules
echo -e "${YELLOW}Building Cython modules...${NC}"
python -m pip install -e .

# Check if compilation was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Cython modules compiled successfully!${NC}"
else
    echo -e "${RED}Failed to compile Cython modules. Please check the error messages above.${NC}"
    exit 1
fi

# Step 10: Create necessary directories for tests
echo -e "${YELLOW}Creating necessary directories for tests...${NC}"
mkdir -p tests/integration/verified_codemods/codemod_data

# Step 11: Ask if user wants to run tests
if [ "$1" == "--test" ] || [ "$1" == "-t" ]; then
    RUN_TESTS=true
else
    echo -e "${CYAN}Do you want to run tests? (y/n) [default: n]:${NC}"
    read -r run_tests_input
    if [[ "$run_tests_input" =~ ^[Yy]$ ]]; then
        RUN_TESTS=true
    else
        RUN_TESTS=false
    fi
fi

if [ "$RUN_TESTS" = true ]; then
    echo -e "${YELLOW}Running tests...${NC}"
    if [ -f "./scripts/full_test.sh" ]; then
        bash ./scripts/full_test.sh
    else
        python -m pytest tests/unit -v -p no:xdist -p no:cov
    fi
fi

echo -e "${YELLOW}To activate the virtual environment in the future, run:${NC}"
echo -e "  source .venv/bin/activate"
echo -e "${YELLOW}To run tests:${NC}"
echo -e "  ./scripts/full_test.sh           # Interactive test runner"
echo -e "  ./scripts/full_test.sh --unit    # Run unit tests"
echo -e "  ./scripts/full_test.sh --all     # Run all tests"
echo -e "  ./scripts/full_test.sh --coverage # Run with coverage"

echo -e "${GREEN}Full build completed successfully!${NC}"
echo -e "${BLUE}=== Environment Information ===${NC}"
echo -e "${YELLOW}Python version:${NC} $(python --version)"
echo -e "${YELLOW}UV version:${NC} $(uv --version)"

echo -e "${BLUE}=== Next Steps ===${NC}"
echo -e "${YELLOW}To activate the virtual environment in the future, run:${NC}"
echo -e "  source .venv/bin/activate"
echo -e "${YELLOW}To run tests:${NC}"
echo -e "  ./scripts/full_test.sh           # Interactive test runner"
echo -e "  ./scripts/full_test.sh --unit    # Run unit tests"
echo -e "  ./scripts/full_test.sh --all     # Run all tests"
echo -e "  ./scripts/full_test.sh --coverage # Run with coverage"
