#!/bin/bash

# 🚀 Web Dashboard Launch Script - WSL Enhanced Version
# Smart launcher with WSL detection, robust error handling, and fallback modes
# Version 2.0 - Enhanced for WSL environments

set -e

# Global variables for environment detection
ENVIRONMENT=""
WSL_VERSION=""
NODE_SOURCE=""
FRONTEND_FAILED=false
BACKEND_FAILED=false

# Parse command line arguments
SKIP_DOCKER=false
DEV_MODE=false
BACKEND_ONLY=false
FORCE_NODE_INSTALL=false

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
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --force-node-install)
            FORCE_NODE_INSTALL=true
            shift
            ;;
        -h|--help)
            echo "🚀 Web Dashboard Launch Script - WSL Enhanced"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev                 Development mode (no Docker, minimal setup)"
            echo "  --skip-docker         Skip Docker installation and database setup"
            echo "  --backend-only        Launch only the backend service"
            echo "  --force-node-install  Force reinstallation of Node.js for WSL"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Full launch with auto-detection"
            echo "  $0 --dev             # Development mode, no Docker required"
            echo "  $0 --backend-only    # Backend only (useful when frontend fails)"
            echo "  $0 --force-node-install # Fix Node.js issues in WSL"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Enhanced printing functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_debug() {
    echo -e "${PURPLE}[DEBUG]${NC} $1"
}

print_tip() {
    echo -e "${CYAN}[TIP]${NC} $1"
}

# Environment detection functions
detect_environment() {
    print_header "🔍 Detecting Environment..."
    
    # Check for WSL
    if grep -qi microsoft /proc/version 2>/dev/null; then
        ENVIRONMENT="WSL"
        
        # Detect WSL version
        if grep -qi "microsoft-standard" /proc/version 2>/dev/null; then
            WSL_VERSION="WSL2"
        else
            WSL_VERSION="WSL1"
        fi
        
        print_status "Detected: $WSL_VERSION"
        
        # Check for Windows Node.js vs WSL Node.js
        detect_node_source
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        ENVIRONMENT="LINUX"
        print_status "Detected: Native Linux"
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        ENVIRONMENT="MACOS"
        print_status "Detected: macOS"
        
    else
        ENVIRONMENT="UNKNOWN"
        print_warning "Unknown environment: $OSTYPE"
    fi
    
    print_debug "Environment: $ENVIRONMENT, WSL: $WSL_VERSION, Node Source: $NODE_SOURCE"
}

detect_node_source() {
    if command -v node &> /dev/null; then
        local node_path=$(which node)
        
        if [[ "$node_path" == *"/mnt/c/"* ]] || [[ "$node_path" == *"Program Files"* ]]; then
            NODE_SOURCE="WINDOWS"
            print_warning "Windows Node.js detected in WSL - this may cause path issues"
        else
            NODE_SOURCE="WSL"
            print_status "WSL-native Node.js detected"
        fi
    else
        NODE_SOURCE="NONE"
        print_status "Node.js not found"
    fi
}

# WSL-specific Node.js installation
install_wsl_nodejs() {
    print_header "📦 Installing WSL-Native Node.js..."
    
    # Remove any existing Windows Node.js from PATH in this session
    export PATH=$(echo $PATH | tr ':' '\n' | grep -v "/mnt/c/" | tr '\n' ':')
    
    # Install Node.js using NodeSource repository (recommended for WSL)
    print_status "Adding NodeSource repository..."
    
    if ! curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -; then
        print_error "Failed to add NodeSource repository"
        
        # Fallback: try using snap
        print_status "Trying snap installation as fallback..."
        if command -v snap &> /dev/null; then
            sudo snap install node --classic
        else
            print_error "Snap not available. Please install Node.js manually."
            return 1
        fi
    fi
    
    # Install Node.js
    print_status "Installing Node.js..."
    if ! sudo apt-get install -y nodejs; then
        print_error "Failed to install Node.js via apt"
        return 1
    fi
    
    # Verify installation
    if command -v node &> /dev/null && command -v npm &> /dev/null; then
        local node_version=$(node --version)
        local npm_version=$(npm --version)
        print_success "Node.js $node_version and npm $npm_version installed successfully"
        
        # Update NODE_SOURCE
        NODE_SOURCE="WSL"
        return 0
    else
        print_error "Node.js installation verification failed"
        return 1
    fi
}

# Enhanced dependency checking with WSL awareness
check_dependencies() {
    print_header "🔍 Checking Dependencies..."
    
    local missing_deps=()
    local install_commands=()
    local need_node_fix=false
    
    # Check Node.js with WSL awareness
    if ! command -v node &> /dev/null; then
        missing_deps+=("node")
        if [[ "$ENVIRONMENT" == "WSL" ]]; then
            install_commands+=("install_wsl_nodejs")
        else
            install_commands+=("curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs")
        fi
    elif [[ "$ENVIRONMENT" == "WSL" ]] && [[ "$NODE_SOURCE" == "WINDOWS" ]] && [[ "$FORCE_NODE_INSTALL" == "true" ]]; then
        print_warning "Windows Node.js detected in WSL with --force-node-install"
        need_node_fix=true
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null && command -v node &> /dev/null; then
        missing_deps+=("npm")
        install_commands+=("sudo apt-get install -y npm")
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
        install_commands+=("sudo apt-get install -y python3 python3-pip python3-venv")
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("pip3")
        install_commands+=("sudo apt-get install -y python3-pip")
    fi
    
    # Handle Node.js fix for WSL
    if [[ "$need_node_fix" == "true" ]]; then
        print_status "Fixing Node.js installation for WSL..."
        if install_wsl_nodejs; then
            print_success "Node.js fixed for WSL environment"
        else
            print_error "Failed to fix Node.js for WSL"
        fi
    fi
    
    # Install missing dependencies
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Auto-installing missing dependencies..."
        
        # Update package list
        sudo apt-get update
        
        # Install missing dependencies
        for cmd in "${install_commands[@]}"; do
            print_status "Running: $cmd"
            if [[ "$cmd" == "install_wsl_nodejs" ]]; then
                install_wsl_nodejs
            else
                eval "$cmd"
            fi
        done
        
        print_success "Dependencies installed successfully"
    fi
    
    # Docker check (unless skipped)
    if [ "$SKIP_DOCKER" = false ] && ! command -v docker &> /dev/null; then
        print_warning "Docker not found."
        if [ "$DEV_MODE" = false ]; then
            print_status "Attempting to install Docker for $ENVIRONMENT..."
            if ! install_docker_for_environment; then
                print_warning "Docker installation failed. Continuing in development mode..."
                SKIP_DOCKER=true
            fi
        else
            print_status "Development mode enabled - Docker installation skipped"
        fi
    elif [ "$SKIP_DOCKER" = true ]; then
        print_warning "Skipping Docker installation (--skip-docker or --dev mode)"
    elif command -v docker &> /dev/null; then
        print_status "Docker found ✅"
    fi
    
    print_success "Dependency check complete ✅"
}

# Environment-aware Docker installation
install_docker_for_environment() {
    case "$ENVIRONMENT" in
        "WSL")
            install_docker_wsl
            ;;
        "LINUX")
            install_docker_linux
            ;;
        *)
            print_error "Docker installation not supported for $ENVIRONMENT"
            return 1
            ;;
    esac
}

# Install Docker for WSL
install_docker_wsl() {
    print_header "🐳 Installing Docker for WSL..."
    
    # Update package index
    if ! sudo apt-get update; then
        print_error "Failed to update package index"
        return 1
    fi
    
    # Install prerequisites
    if ! sudo apt-get install -y ca-certificates curl gnupg lsb-release; then
        print_error "Failed to install prerequisites"
        return 1
    fi
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    if ! curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg; then
        print_error "Failed to add Docker GPG key"
        return 1
    fi
    
    # Set up the repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update package index again
    if ! sudo apt-get update; then
        print_error "Failed to update package index after adding Docker repository"
        return 1
    fi
    
    # Install Docker Engine
    if ! sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin; then
        print_error "Failed to install Docker Engine"
        return 1
    fi
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Start Docker service
    if ! sudo service docker start; then
        print_warning "Failed to start Docker service automatically"
    fi
    
    print_success "Docker installed successfully! ✅"
    print_warning "You may need to restart your shell or run 'newgrp docker' to use Docker without sudo."
    
    return 0
}

# Install Docker for native Linux
install_docker_linux() {
    print_header "🐳 Installing Docker for Linux..."
    
    # This is similar to WSL but may have different requirements
    install_docker_wsl  # For now, use the same method
}

# Load environment variables with better error handling
load_environment() {
    print_header "🔧 Loading Environment Variables..."
    
    if [ -f .env ]; then
        # Source the .env file safely
        set -a  # automatically export all variables
        source .env
        set +a  # stop automatically exporting
        print_status "Environment variables loaded from .env ✅"
    else
        print_warning "No .env file found"
        if [ "$DEV_MODE" = true ]; then
            print_status "Creating minimal .env for development mode..."
            cat > .env << 'EOF'
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
            print_status "Created and loaded development .env ✅"
        else
            print_warning "Using system environment variables"
        fi
    fi
    
    # Validate required environment variables (skip in dev mode)
    if [ "$DEV_MODE" = false ]; then
        local required_vars=(
            "CODEGEN_ORG_ID"
            "CODEGEN_API_TOKEN"
            "GITHUB_TOKEN"
            "GEMINI_API_KEY"
            "CLOUDFLARE_API_KEY"
            "CLOUDFLARE_ACCOUNT_ID"
            "CLOUDFLARE_WORKER_URL"
        )
        
        local missing_vars=()
        for var in "${required_vars[@]}"; do
            if [ -z "${!var}" ]; then
                missing_vars+=("$var")
            fi
        done
        
        if [ ${#missing_vars[@]} -ne 0 ]; then
            print_error "Missing required environment variables: ${missing_vars[*]}"
            print_tip "Use --dev mode to skip this validation"
            print_tip "Or create a .env file with the required variables"
            exit 1
        fi
        
        print_status "All required environment variables are set ✅"
    else
        print_status "Development mode - skipping environment validation ✅"
    fi
}

# Enhanced backend setup with better error handling
setup_backend() {
    print_header "🐍 Setting up Backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    if ! pip install -r requirements.txt; then
        print_error "Failed to install Python dependencies"
        BACKEND_FAILED=true
        cd ..
        return 1
    fi
    
    # Skip database migrations in dev mode or if database unavailable
    if [ "$DEV_MODE" = true ] || [ "$SKIP_DOCKER" = true ]; then
        print_warning "Skipping database migrations (development mode)"
    else
        print_status "Running database migrations..."
        if ! python -m alembic upgrade head; then
            print_warning "Database migrations failed - continuing without database"
        fi
    fi
    
    cd ..
    print_success "Backend setup complete ✅"
}

# Enhanced frontend setup with WSL path handling
setup_frontend() {
    if [ "$BACKEND_ONLY" = true ]; then
        print_status "Skipping frontend setup (--backend-only mode)"
        return 0
    fi
    
    print_header "⚛️ Setting up Frontend..."
    
    cd frontend
    
    # WSL-specific handling
    if [[ "$ENVIRONMENT" == "WSL" ]]; then
        print_status "WSL detected, checking for path issues..."
        
        # Remove existing node_modules if it exists and might have path issues
        if [ -d "node_modules" ]; then
            print_status "Removing existing node_modules to avoid WSL path issues..."
            rm -rf node_modules
        fi
        
        # Configure npm for WSL
        print_status "Configuring npm for WSL environment..."
        npm config set cache ~/.npm-cache
        npm config set tmp ~/.npm-tmp
        
        # Ensure we're using WSL Node.js
        if [[ "$NODE_SOURCE" == "WINDOWS" ]]; then
            print_warning "Windows Node.js detected. This may cause issues."
            print_tip "Consider running with --force-node-install to fix Node.js"
        fi
    fi
    
    # Install Node.js dependencies with error handling
    print_status "Installing Node.js dependencies..."
    
    # Try normal installation first
    if ! npm install; then
        print_warning "npm install failed, trying with legacy peer deps..."
        
        if ! npm install --legacy-peer-deps; then
            print_warning "npm install with legacy peer deps failed, trying with force..."
            
            if ! npm install --force; then
                print_error "All npm install attempts failed"
                FRONTEND_FAILED=true
                cd ..
                return 1
            fi
        fi
    fi
    
    cd ..
    print_success "Frontend setup complete ✅"
}

# Start database services with fallback
start_database() {
    if [ "$SKIP_DOCKER" = true ]; then
        print_status "Skipping database services (Docker disabled)"
        return 0
    fi
    
    print_header "🗄️ Starting Database Services..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_status "Starting Docker service..."
        if ! sudo service docker start; then
            print_error "Failed to start Docker service. Docker may not be installed."
            print_status "Falling back to development mode..."
            SKIP_DOCKER=true
            return 0
        fi
    fi
    
    # Start database containers
    if [ -f "docker-compose.yml" ]; then
        print_status "Starting database containers..."
        if ! docker-compose up -d postgres redis; then
            print_warning "Failed to start database containers"
            print_status "Continuing without database..."
            SKIP_DOCKER=true
        else
            print_success "Database services started ✅"
        fi
    else
        print_warning "No docker-compose.yml found, skipping database setup"
    fi
}

# Start backend service with error handling
start_backend() {
    print_header "🚀 Starting Backend Service..."
    
    cd backend
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        print_error "Virtual environment not found. Run setup first."
        BACKEND_FAILED=true
        cd ..
        return 1
    fi
    
    # Start the backend server
    print_status "Starting FastAPI backend on port 8000..."
    
    # Start backend in background
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
    BACKEND_PID=$!
    
    cd ..
    
    # Wait a moment and check if backend started successfully
    sleep 5
    
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend started successfully ✅"
        print_status "Backend API: http://localhost:8000"
        print_status "API Documentation: http://localhost:8000/docs"
        return 0
    else
        print_error "Backend failed to start properly"
        print_tip "Check backend.log for error details"
        BACKEND_FAILED=true
        return 1
    fi
}

# Start frontend service with error handling
start_frontend() {
    if [ "$BACKEND_ONLY" = true ]; then
        print_status "Skipping frontend startup (--backend-only mode)"
        return 0
    fi
    
    if [ "$FRONTEND_FAILED" = true ]; then
        print_warning "Skipping frontend startup (setup failed)"
        return 1
    fi
    
    print_header "⚛️ Starting Frontend Service..."
    
    cd frontend
    
    # Start the frontend development server
    print_status "Starting Vite development server..."
    
    # Start frontend in background
    nohup npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    cd ..
    
    # Wait a moment and check if frontend started
    sleep 5
    
    # Try different ports as Vite may use 5173 or 5174
    local frontend_url=""
    for port in 5173 5174 5175; do
        if curl -s http://localhost:$port > /dev/null; then
            frontend_url="http://localhost:$port"
            break
        fi
    done
    
    if [ -n "$frontend_url" ]; then
        print_success "Frontend started successfully ✅"
        print_status "Frontend Dashboard: $frontend_url"
        return 0
    else
        print_error "Frontend failed to start properly"
        print_tip "Check frontend.log for error details"
        FRONTEND_FAILED=true
        return 1
    fi
}

# Display comprehensive launch information
show_launch_info() {
    print_header "🎉 Launch Summary"
    echo "=================================================="
    
    # Environment information
    echo ""
    print_status "Environment: $ENVIRONMENT $WSL_VERSION"
    print_status "Node.js Source: $NODE_SOURCE"
    
    # Service status
    echo ""
    print_header "📊 Service Status:"
    
    if [ "$BACKEND_FAILED" = false ]; then
        echo "✅ Backend API: http://localhost:8000"
        echo "📚 API Documentation: http://localhost:8000/docs"
        echo "🔍 Health Check: http://localhost:8000/health"
    else
        echo "❌ Backend: Failed to start"
        print_tip "Check backend.log for error details"
    fi
    
    if [ "$BACKEND_ONLY" = true ]; then
        echo "⏭️  Frontend: Skipped (--backend-only mode)"
    elif [ "$FRONTEND_FAILED" = false ]; then
        # Try to detect the actual frontend port
        for port in 5173 5174 5175; do
            if curl -s http://localhost:$port > /dev/null; then
                echo "✅ Frontend Dashboard: http://localhost:$port"
                break
            fi
        done
    else
        echo "❌ Frontend: Failed to start"
        print_tip "Check frontend.log for error details"
        print_tip "Try running with --backend-only for API access"
    fi
    
    if [ "$SKIP_DOCKER" = true ]; then
        echo "⏭️  Database: Disabled (development mode)"
    else
        echo "✅ Database: PostgreSQL + Redis (Docker)"
    fi
    
    # Usage instructions
    echo ""
    print_header "🔧 Usage Instructions:"
    
    if [ "$BACKEND_FAILED" = false ]; then
        echo "• Access the API at http://localhost:8000"
        echo "• View API documentation at http://localhost:8000/docs"
        echo "• Test API health at http://localhost:8000/health"
    fi
    
    if [ "$FRONTEND_FAILED" = false ] && [ "$BACKEND_ONLY" = false ]; then
        echo "• Access the dashboard in your browser"
        echo "• Use the interactive file explorer and code editor"
        echo "• Visualize code graphs and dependencies"
    fi
    
    # Troubleshooting tips
    echo ""
    print_header "🛠️ Troubleshooting:"
    
    if [ "$FRONTEND_FAILED" = true ]; then
        echo "Frontend Issues:"
        print_tip "Run './launch_upgraded.sh --backend-only' for API access"
        print_tip "Check 'frontend.log' for detailed error messages"
        
        if [[ "$ENVIRONMENT" == "WSL" ]] && [[ "$NODE_SOURCE" == "WINDOWS" ]]; then
            print_tip "Try './launch_upgraded.sh --force-node-install' to fix Node.js"
        fi
        
        print_tip "Manual frontend setup:"
        echo "  cd frontend"
        echo "  rm -rf node_modules package-lock.json"
        echo "  npm cache clean --force"
        echo "  npm install --legacy-peer-deps"
        echo "  npm run dev"
    fi
    
    if [ "$BACKEND_FAILED" = true ]; then
        echo "Backend Issues:"
        print_tip "Check 'backend.log' for detailed error messages"
        print_tip "Ensure Python dependencies are installed correctly"
        print_tip "Try running in development mode with --dev"
    fi
    
    # WSL-specific tips
    if [[ "$ENVIRONMENT" == "WSL" ]]; then
        echo ""
        print_header "🐧 WSL-Specific Tips:"
        print_tip "If you encounter path issues, ensure you're using WSL-native Node.js"
        print_tip "Windows Node.js in WSL can cause UNC path errors"
        print_tip "Use --force-node-install to install WSL-native Node.js"
        
        if [[ "$NODE_SOURCE" == "WINDOWS" ]]; then
            print_warning "You're using Windows Node.js in WSL - this may cause issues"
            print_tip "Run: ./launch_upgraded.sh --force-node-install"
        fi
    fi
    
    echo ""
    print_header "🛑 To stop all services:"
    echo "• Press Ctrl+C in this terminal"
    echo "• Or run: ./stop.sh"
    echo "• Or kill processes manually if needed"
    
    echo "=================================================="
}

# Enhanced cleanup function
cleanup() {
    print_header "🧹 Cleaning up services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes on our ports
    print_status "Cleaning up any remaining processes..."
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    print_success "Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution function
main() {
    # Print startup banner
    if [ "$DEV_MODE" = true ]; then
        echo "🚀 Starting Web Dashboard in Development Mode (WSL Enhanced)..."
    elif [ "$BACKEND_ONLY" = true ]; then
        echo "🚀 Starting Web Dashboard Backend Only (WSL Enhanced)..."
    else
        echo "🚀 Starting Web Dashboard with Full Features (WSL Enhanced)..."
    fi
    echo "=================================================="
    
    # Core setup steps
    detect_environment
    check_dependencies
    load_environment
    
    # Service setup
    start_database
    setup_backend
    
    if [ "$BACKEND_ONLY" = false ]; then
        setup_frontend
    fi
    
    # Start services
    start_backend
    
    if [ "$BACKEND_ONLY" = false ]; then
        start_frontend
    fi
    
    # Wait for services to stabilize
    sleep 2
    
    # Show launch information
    show_launch_info
    
    # Keep the script running
    if [ "$BACKEND_FAILED" = false ] || [ "$FRONTEND_FAILED" = false ]; then
        print_status "Services are running. Press Ctrl+C to stop."
        
        # Monitor services and restart if needed
        while true; do
            sleep 30
            
            # Check backend health
            if [ "$BACKEND_FAILED" = false ] && ! curl -s http://localhost:8000/health > /dev/null; then
                print_warning "Backend health check failed - service may have crashed"
                print_tip "Check backend.log for details"
            fi
            
            # Check frontend health (if running)
            if [ "$FRONTEND_FAILED" = false ] && [ "$BACKEND_ONLY" = false ]; then
                local frontend_alive=false
                for port in 5173 5174 5175; do
                    if curl -s http://localhost:$port > /dev/null; then
                        frontend_alive=true
                        break
                    fi
                done
                
                if [ "$frontend_alive" = false ]; then
                    print_warning "Frontend health check failed - service may have crashed"
                    print_tip "Check frontend.log for details"
                fi
            fi
        done
    else
        print_error "All services failed to start"
        print_tip "Check the logs and troubleshooting tips above"
        exit 1
    fi
}

# Run main function
main "$@"
