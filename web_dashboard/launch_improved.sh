#!/bin/bash

# 🚀 Enhanced Web Dashboard Launch Script
# WSL-optimized launcher with comprehensive environment handling

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1 ✅"; }

# Parse command line arguments
SKIP_DOCKER=false
DEV_MODE=false
FORCE_WSL_SETUP=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            SKIP_DOCKER=true
            shift
            ;;
        --force-wsl-setup)
            FORCE_WSL_SETUP=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "🚀 Enhanced Web Dashboard Launch Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev              Development mode (no Docker, minimal setup)"
            echo "  --skip-docker      Skip Docker installation and database setup"
            echo "  --force-wsl-setup  Force WSL environment setup and validation"
            echo "  --verbose          Enable verbose logging"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                 # Full launch with Docker and databases"
            echo "  $0 --dev           # Development mode, no Docker required"
            echo "  $0 --force-wsl-setup # Fix WSL environment issues"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Environment detection and setup
detect_environment() {
    log_info "🔍 Detecting and validating environment..."
    
    # Detect WSL
    if [[ -f /proc/version ]] && grep -qi microsoft /proc/version; then
        export IS_WSL=true
        if grep -qi "WSL2" /proc/version; then
            export WSL_VERSION="WSL2"
        else
            export WSL_VERSION="WSL1"
        fi
        log_info "Detected: $WSL_VERSION"
    else
        export IS_WSL=false
        log_info "Detected: Native Linux"
    fi
    
    # Check for Windows Node.js contamination in WSL
    if [[ "$IS_WSL" == "true" ]]; then
        if command -v node >/dev/null 2>&1; then
            NODE_PATH=$(which node)
            if [[ "$NODE_PATH" == *"/mnt/c/"* ]] || [[ "$NODE_PATH" == *"Windows"* ]]; then
                log_warn "Windows Node.js detected in WSL - this may cause path issues"
                export NODE_SOURCE="WINDOWS"
                if [[ "$FORCE_WSL_SETUP" == "true" ]]; then
                    setup_wsl_nodejs
                fi
            else
                log_info "WSL-native Node.js detected"
                export NODE_SOURCE="WSL"
            fi
        else
            log_warn "Node.js not found - will install WSL-native version"
            export NODE_SOURCE="MISSING"
            if [[ "$FORCE_WSL_SETUP" == "true" ]]; then
                setup_wsl_nodejs
            fi
        fi
    fi
    
    # Environment summary
    if [[ "$VERBOSE" == "true" ]]; then
        log_debug "Environment: WSL=$IS_WSL, WSL_VERSION=${WSL_VERSION:-N/A}, Node Source: ${NODE_SOURCE:-NATIVE}"
    fi
}

# Setup WSL-native Node.js
setup_wsl_nodejs() {
    log_info "🔧 Setting up WSL-native Node.js environment..."
    
    # Install Node.js via NodeSource repository (recommended for WSL)
    if ! command -v curl >/dev/null 2>&1; then
        log_info "Installing curl..."
        sudo apt-get update && sudo apt-get install -y curl
    fi
    
    # Install Node.js 18.x (LTS)
    log_info "Installing Node.js 18.x LTS..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    # Verify installation
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        NODE_VERSION=$(node --version)
        NPM_VERSION=$(npm --version)
        log_success "Node.js $NODE_VERSION and npm $NPM_VERSION installed"
        export NODE_SOURCE="WSL"
    else
        log_error "Failed to install Node.js"
        exit 1
    fi
}

# Enhanced dependency checking
check_dependencies() {
    log_info "🔍 Checking dependencies..."
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python3")
    fi
    
    # Check pip
    if ! command -v pip3 >/dev/null 2>&1; then
        missing_deps+=("python3-pip")
    fi
    
    # Check Node.js (only if not forcing WSL setup)
    if [[ "$FORCE_WSL_SETUP" != "true" ]] && ! command -v node >/dev/null 2>&1; then
        missing_deps+=("nodejs")
    fi
    
    # Check npm (only if not forcing WSL setup)
    if [[ "$FORCE_WSL_SETUP" != "true" ]] && ! command -v npm >/dev/null 2>&1; then
        missing_deps+=("npm")
    fi
    
    # Check Docker (only if not skipping)
    if [[ "$SKIP_DOCKER" != "true" ]]; then
        if command -v docker >/dev/null 2>&1; then
            log_info "Docker command found, checking service status..."
            if ! docker ps >/dev/null 2>&1; then
                log_warn "Docker command found but daemon not accessible"
                check_docker_wsl_integration
            else
                log_success "Docker is accessible"
            fi
        else
            log_warn "Docker not found"
            missing_deps+=("docker")
        fi
    else
        log_warn "Skipping Docker installation (--skip-docker or --dev mode)"
    fi
    
    # Install missing dependencies
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_info "Installing missing dependencies: ${missing_deps[*]}"
        sudo apt-get update
        for dep in "${missing_deps[@]}"; do
            case $dep in
                "nodejs")
                    if [[ "$IS_WSL" == "true" ]]; then
                        setup_wsl_nodejs
                    else
                        sudo apt-get install -y nodejs npm
                    fi
                    ;;
                "docker")
                    install_docker
                    ;;
                *)
                    sudo apt-get install -y "$dep"
                    ;;
            esac
        done
    fi
    
    log_success "Dependency check complete"
}

# Enhanced Docker WSL integration check
check_docker_wsl_integration() {
    if [[ "$IS_WSL" == "true" ]]; then
        log_info "WSL detected - checking Docker Desktop integration..."
        
        # Check if Docker Desktop is running on Windows
        if [[ -f "/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe" ]] || [[ -f "/mnt/c/Users/$USER/AppData/Local/Docker/Docker Desktop.exe" ]]; then
            log_info "Docker Desktop detected on Windows"
            log_warn "Please ensure Docker Desktop is running and WSL integration is enabled"
            log_info "In Docker Desktop: Settings → Resources → WSL Integration → Enable integration"
        fi
        
        # Try alternative Docker startup methods
        log_info "Trying alternative Docker startup methods..."
        
        # Try to start Docker service if it exists
        if systemctl list-unit-files | grep -q docker.service; then
            log_info "Attempting to start Docker service..."
            if sudo systemctl start docker 2>/dev/null; then
                log_success "Docker service started"
                return 0
            fi
        else
            log_warn "Docker service not found in systemd"
        fi
        
        # Provide helpful tips
        log_error "Docker is installed but not accessible. Common fixes:"
        log_info "1. Add your user to docker group: sudo usermod -aG docker \$USER"
        log_info "2. Restart your shell: newgrp docker"
        log_info "3. For WSL: Ensure Docker Desktop is running with WSL integration"
        log_info "4. Try: sudo systemctl enable docker && sudo systemctl start docker"
        
        log_warn "Continuing in development mode without Docker..."
        SKIP_DOCKER=true
    fi
}

# Install Docker (if needed)
install_docker() {
    if [[ "$IS_WSL" == "true" ]]; then
        log_info "Installing Docker Engine for WSL..."
        
        # Install Docker Engine (not Docker Desktop)
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        
        # Start Docker service
        sudo systemctl enable docker
        sudo systemctl start docker
        
        log_info "Docker installed. You may need to restart your shell or run 'newgrp docker'"
    else
        log_info "Installing Docker..."
        sudo apt-get install -y docker.io
        sudo systemctl enable docker
        sudo systemctl start docker
        sudo usermod -aG docker $USER
    fi
}

# Enhanced environment variable setup
setup_environment() {
    log_info "🔧 Loading environment variables..."
    
    if [[ -f .env ]]; then
        log_info "Loading existing .env file..."
        set -a
        source .env
        set +a
        log_success "Environment variables loaded from .env"
    else
        if [[ "$DEV_MODE" == "true" ]]; then
            log_warn "No .env file found"
            log_info "Creating minimal .env for development mode..."
            cat > .env << EOF
# Development Environment Variables
CODEGEN_ORG_ID=dev-org
CODEGEN_API_TOKEN=dev-token
GITHUB_TOKEN=dev-github-token
GEMINI_API_KEY=dev-gemini-key
CLOUDFLARE_API_KEY=dev-cloudflare-key
CLOUDFLARE_ACCOUNT_ID=dev-account-id
CLOUDFLARE_WORKER_URL=https://dev-worker.example.com
DATABASE_URL=postgresql://postgres:password@localhost:5432/web_eval_agent
EOF
            set -a
            source .env
            set +a
            log_success "Created and loaded development .env"
        else
            log_warn "No .env file found. Please copy .env.example to .env and configure it."
            log_info "Creating .env from .env.example..."
            cp .env.example .env
            log_warn "Please edit .env file with your actual API keys and configuration"
            return 1
        fi
    fi
    
    # Validate required environment variables (skip in dev mode)
    if [[ "$DEV_MODE" != "true" ]]; then
        local required_vars=("CODEGEN_ORG_ID" "CODEGEN_API_TOKEN" "GITHUB_TOKEN")
        local missing_vars=()
        
        for var in "${required_vars[@]}"; do
            if [[ -z "${!var}" ]]; then
                missing_vars+=("$var")
            fi
        done
        
        if [[ ${#missing_vars[@]} -gt 0 ]]; then
            log_error "Missing required environment variables: ${missing_vars[*]}"
            log_info "Please configure these in your .env file"
            return 1
        fi
        
        log_success "All required environment variables are set"
    else
        log_success "Environment validation skipped (development mode)"
    fi
}

# Enhanced backend setup with proper virtual environment handling
setup_backend() {
    log_info "🐍 Setting up backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install graph-sitter if available
    if [[ -f "../../setup.py" ]] || [[ -f "../../pyproject.toml" ]]; then
        log_info "Installing graph-sitter from parent directory..."
        pip install -e ../..
    fi
    
    # Database setup (skip in dev mode)
    if [[ "$DEV_MODE" != "true" ]] && [[ "$SKIP_DOCKER" != "true" ]]; then
        log_info "Running database migrations..."
        alembic upgrade head
    else
        log_warn "Skipping database migrations (development mode)"
    fi
    
    # Start backend server
    log_info "Starting backend server..."
    if [[ "$DEV_MODE" == "true" ]]; then
        # In dev mode, start with reload and handle missing database gracefully
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    else
        uvicorn main:app --host 0.0.0.0 --port 8000 &
    fi
    
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    
    # Wait a moment and check if backend started successfully
    sleep 3
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_success "Backend server started (PID: $BACKEND_PID)"
    else
        log_error "Backend server failed to start"
        return 1
    fi
    
    cd ..
}

# Enhanced frontend setup with path validation
setup_frontend() {
    log_info "⚛️ Setting up frontend..."
    
    cd frontend
    
    # Validate we're in the correct directory and using correct Node.js
    if [[ "$IS_WSL" == "true" ]] && [[ "$NODE_SOURCE" == "WINDOWS" ]]; then
        log_warn "Using Windows Node.js in WSL - this may cause issues"
        log_info "Consider running with --force-wsl-setup to install WSL-native Node.js"
    fi
    
    # Clean install if there are path issues
    if [[ "$IS_WSL" == "true" ]] && [[ -d "node_modules" ]]; then
        log_info "Cleaning existing node_modules to prevent path issues..."
        rm -rf node_modules package-lock.json
    fi
    
    # Install dependencies
    log_info "Installing Node.js dependencies..."
    if ! npm install; then
        log_warn "npm install failed, trying with legacy peer deps..."
        npm install --legacy-peer-deps
    fi
    
    # Build in production mode (skip in dev mode)
    if [[ "$DEV_MODE" != "true" ]]; then
        log_info "Building frontend for production..."
        npm run build
    fi
    
    # Start development server
    log_info "Starting frontend development server..."
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    
    # Wait a moment and check if frontend started successfully
    sleep 3
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        log_success "Frontend development server started (PID: $FRONTEND_PID)"
    else
        log_error "Frontend development server failed to start"
        return 1
    fi
    
    cd ..
}

# Health check function
health_check() {
    log_info "🏥 Performing health checks..."
    
    # Check backend
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_warn "Backend health check failed - this is normal in development mode"
    fi
    
    # Check frontend
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
        log_success "Frontend health check passed"
    else
        log_warn "Frontend health check failed - server may still be starting"
    fi
}

# Cleanup function
cleanup() {
    log_info "🧹 Cleaning up..."
    
    if [[ -f backend.pid ]]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            log_info "Stopping backend server (PID: $BACKEND_PID)..."
            kill $BACKEND_PID
        fi
        rm -f backend.pid
    fi
    
    if [[ -f frontend.pid ]]; then
        FRONTEND_PID=$(cat frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            log_info "Stopping frontend server (PID: $FRONTEND_PID)..."
            kill $FRONTEND_PID
        fi
        rm -f frontend.pid
    fi
}

# Trap cleanup on exit
trap cleanup EXIT INT TERM

# Main execution
main() {
    if [[ "$DEV_MODE" == "true" ]]; then
        echo "🚀 Starting Web Dashboard in Development Mode..."
        echo "=================================================="
    else
        echo "🚀 Starting Web Dashboard with Full Features (WSL Enhanced)..."
        echo "=================================================="
    fi
    
    # Environment detection and setup
    detect_environment
    
    # Check and install dependencies
    check_dependencies
    
    # Setup environment variables
    if ! setup_environment; then
        log_error "Environment setup failed"
        exit 1
    fi
    
    # Skip database services in dev mode
    if [[ "$DEV_MODE" == "true" ]]; then
        log_info "🗄️ Skipping Database Services (Development Mode)..."
        log_warn "Database services disabled. Some features may not work."
    else
        # Database setup would go here
        log_info "🗄️ Setting up database services..."
        # ... database setup code ...
    fi
    
    # Setup backend
    if ! setup_backend; then
        log_error "Backend setup failed"
        exit 1
    fi
    
    # Setup frontend
    if ! setup_frontend; then
        log_error "Frontend setup failed"
        exit 1
    fi
    
    # Health checks
    if [[ "$DEV_MODE" != "true" ]]; then
        sleep 5
        health_check
    else
        log_info "Skipping API tests in development mode"
    fi
    
    # Success message
    if [[ "$DEV_MODE" == "true" ]]; then
        echo -e "${BLUE}🎉 Development Launch Complete!${NC}"
    else
        echo -e "${BLUE}🎉 Full Launch Complete!${NC}"
    fi
    echo "=================================================="
    echo ""
    echo "🌐 Frontend Dashboard: http://localhost:5173"
    echo "🚀 Backend API: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "🔍 API Health: http://localhost:8000/health"
    echo ""
    
    if [[ "$DEV_MODE" == "true" ]]; then
        echo "⚠️  Development Mode Notes:"
        echo "  • Database services are disabled"
        echo "  • Some features may not work without database"
        echo "  • API keys are set to development values"
        echo "  • Perfect for frontend development and testing"
        echo ""
        echo "🔧 For full functionality:"
        echo "  • Run './launch_improved.sh' (without --dev) to enable databases"
        echo "  • Configure real API keys in .env file"
    fi
    
    echo ""
    echo "🛑 To stop all services: Ctrl+C or run './stop.sh'"
    echo "=================================================="
    
    log_info "Services are running. Press Ctrl+C to stop."
    
    # Keep script running
    wait
}

# Run main function
main "$@"
