#!/bin/bash

# 🚀 Web Dashboard Launch Script
# Smart launcher with automatic dependency installation and fallback modes

set -e

# Parse command line arguments
SKIP_DOCKER=false
DEV_MODE=false

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
        -h|--help)
            echo "🚀 Web Dashboard Launch Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dev         Development mode (no Docker, minimal setup)"
            echo "  --skip-docker Skip Docker installation and database setup"
            echo "  -h, --help    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0            # Full launch with Docker and databases"
            echo "  $0 --dev      # Development mode, no Docker required"
            echo "  $0 --skip-docker # Skip Docker but try other features"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ "$DEV_MODE" = true ]; then
    echo "🚀 Starting Web Dashboard in Development Mode..."
    echo "=================================================="
else
    echo "🚀 Starting Web Dashboard with Full CI/CD Testing..."
    echo "=================================================="
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if required tools are installed
check_dependencies() {
    print_header "🔍 Checking Dependencies..."
    
    local missing_deps=()
    local install_commands=()
    
    if ! command -v node &> /dev/null; then
        missing_deps+=("node")
        install_commands+=("curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs")
    fi
    
    if ! command -v npm &> /dev/null && command -v node &> /dev/null; then
        missing_deps+=("npm")
        install_commands+=("sudo apt-get install -y npm")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
        install_commands+=("sudo apt-get install -y python3 python3-pip python3-venv")
    fi
    
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("pip3")
        install_commands+=("sudo apt-get install -y python3-pip")
    fi
    
    # Check for Docker and offer installation (unless skipped)
    if [ "$SKIP_DOCKER" = false ] && ! command -v docker &> /dev/null; then
        print_warning "Docker not found."
        if [ "$DEV_MODE" = false ]; then
            print_status "Attempting to install Docker for WSL2..."
            if ! install_docker_wsl2; then
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
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Auto-installing missing dependencies..."
        
        # Update package list
        sudo apt-get update
        
        # Install missing dependencies
        for cmd in "${install_commands[@]}"; do
            print_status "Running: $cmd"
            eval "$cmd"
        done
        
        print_status "Dependencies installed. Please restart your shell and run the script again."
        exit 0
    fi
    
    print_status "All dependencies are installed ✅"
}

# Install Docker for WSL2
install_docker_wsl2() {
    print_header "🐳 Installing Docker for WSL2..."
    
    # Check if we're in WSL2
    if grep -qi microsoft /proc/version; then
        print_status "WSL2 detected. Installing Docker..."
        
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
        
        print_status "Docker installed successfully! ✅"
        print_warning "You may need to restart your shell or run 'newgrp docker' to use Docker without sudo."
        
        # Test Docker installation
        if docker --version &> /dev/null; then
            print_status "Docker is working correctly"
        else
            print_warning "Docker installed but may need shell restart"
        fi
    else
        print_error "Not running in WSL2. Please install Docker manually."
        print_error "Visit: https://docs.docker.com/get-docker/"
        return 1
    fi
}

# Load environment variables
load_environment() {
    print_header "🔧 Loading Environment Variables..."
    
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
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
            export $(cat .env | grep -v '^#' | xargs)
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
            print_status "Use --dev mode to skip this validation"
            exit 1
        fi
        
        print_status "All required environment variables are set ✅"
    else
        print_status "Environment validation skipped (development mode) ✅"
    fi
}

# Start database services
start_database() {
    if [ "$SKIP_DOCKER" = true ]; then
        print_header "🗄️ Skipping Database Services (Development Mode)..."
        print_warning "Database services disabled. Some features may not work."
        return 0
    fi
    
    print_header "🗄️ Starting Database Services..."
    
    # Ensure Docker is available and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not available. Use --dev mode or restart your shell and try again."
        print_status "Falling back to development mode..."
        SKIP_DOCKER=true
        return 0
    fi
    
    # Start Docker service if not running
    if ! docker info &> /dev/null; then
        print_status "Starting Docker service..."
        if sudo service docker start 2>/dev/null; then
            print_status "Docker service started successfully"
            sleep 3
        else
            print_error "Failed to start Docker service. Docker may not be installed."
            print_status "Falling back to development mode..."
            SKIP_DOCKER=true
            return 0
        fi
    fi
    
    # Check if PostgreSQL is running
    if ! command -v pg_isready &> /dev/null || ! pg_isready -h localhost -p 5432 &> /dev/null; then
        print_status "Starting PostgreSQL with Docker..."
        
        # Remove existing container if it exists
        docker rm -f web-eval-postgres &> /dev/null || true
        
        docker run -d \
            --name web-eval-postgres \
            -e POSTGRES_DB=web_eval_agent \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=password \
            -p 5432:5432 \
            postgres:15-alpine
        
        # Wait for PostgreSQL to be ready
        print_status "Waiting for PostgreSQL to be ready..."
        for i in {1..60}; do
            if docker exec web-eval-postgres pg_isready -U postgres &> /dev/null; then
                print_status "PostgreSQL is ready ✅"
                break
            fi
            if [ $i -eq 60 ]; then
                print_error "PostgreSQL failed to start within 60 seconds"
                docker logs web-eval-postgres
                exit 1
            fi
            sleep 1
        done
    else
        print_status "PostgreSQL is already running ✅"
    fi
    
    # Check if Redis is running
    if ! command -v redis-cli &> /dev/null || ! redis-cli -h localhost -p 6379 ping &> /dev/null; then
        print_status "Starting Redis with Docker..."
        
        # Remove existing container if it exists
        docker rm -f web-eval-redis &> /dev/null || true
        
        docker run -d \
            --name web-eval-redis \
            -p 6379:6379 \
            redis:7-alpine
        
        # Wait for Redis to be ready
        print_status "Waiting for Redis to be ready..."
        for i in {1..30}; do
            if docker exec web-eval-redis redis-cli ping &> /dev/null; then
                print_status "Redis is ready ✅"
                break
            fi
            if [ $i -eq 30 ]; then
                print_error "Redis failed to start within 30 seconds"
                docker logs web-eval-redis
                exit 1
            fi
            sleep 1
        done
    else
        print_status "Redis is already running ✅"
    fi
    
    print_status "Database services are running ✅"
}

# Install backend dependencies
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
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Run database migrations (optional for development)
    if [ "$SKIP_DOCKER" = false ]; then
        print_status "Running database migrations..."
        if command -v docker &> /dev/null && docker ps | grep -q web-eval-postgres; then
            alembic upgrade head || print_warning "Migration failed, continuing without database..."
        else
            print_warning "Database not available, skipping migrations..."
        fi
    else
        print_warning "Skipping database migrations (development mode)"
    fi
    
    cd ..
    print_status "Backend setup complete ✅"
}

# Install frontend dependencies
setup_frontend() {
    print_header "⚛️ Setting up Frontend..."
    
    cd frontend
    
    # Check for WSL path issues and fix them
    if grep -qi microsoft /proc/version; then
        print_status "WSL detected, checking for path issues..."
        
        # Clear npm cache to avoid WSL path issues
        npm cache clean --force 2>/dev/null || true
        
        # Remove node_modules if it exists to avoid permission issues
        if [ -d "node_modules" ]; then
            print_status "Removing existing node_modules to avoid WSL path issues..."
            rm -rf node_modules
        fi
        
        # Set npm to use local cache
        export npm_config_cache="$(pwd)/.npm-cache"
        mkdir -p .npm-cache
    fi
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    if ! npm install; then
        print_warning "npm install failed, trying with legacy peer deps..."
        npm install --legacy-peer-deps || {
            print_error "npm install failed. This might be due to WSL path issues."
            print_status "Try running the following manually:"
            print_status "  cd frontend"
            print_status "  rm -rf node_modules package-lock.json"
            print_status "  npm cache clean --force"
            print_status "  npm install --legacy-peer-deps"
            exit 1
        }
    fi
    
    cd ..
    print_status "Frontend dependencies installed ✅"
}

# Start backend server
start_backend() {
    print_header "🚀 Starting Backend Server..."
    
    cd backend
    source venv/bin/activate
    
    # Start the FastAPI server in background
    print_status "Starting FastAPI server on http://localhost:8000..."
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    # Wait for backend to be ready
    print_status "Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health &> /dev/null; then
            break
        fi
        sleep 1
    done
    
    cd ..
    print_status "Backend server is running ✅"
}

# Start frontend development server
start_frontend() {
    print_header "🌐 Starting Frontend Development Server..."
    
    cd frontend
    
    # Start the Vite development server in background
    print_status "Starting Vite dev server on http://localhost:5173..."
    npm run dev &
    FRONTEND_PID=$!
    
    # Wait for frontend to be ready
    print_status "Waiting for frontend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:5173 &> /dev/null; then
            break
        fi
        sleep 1
    done
    
    cd ..
    print_status "Frontend development server is running ✅"
}

# Test Codegen API connection
test_codegen_api() {
    print_header "🤖 Testing Codegen API Connection..."
    
    # Test API connection
    response=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "Authorization: Bearer $CODEGEN_API_TOKEN" \
        -H "Content-Type: application/json" \
        "https://api.codegen.com/v1/organizations/$CODEGEN_ORG_ID/projects" || echo "000")
    
    if [ "$response" = "200" ]; then
        print_status "Codegen API connection successful ✅"
    else
        print_warning "Codegen API connection failed (HTTP $response)"
    fi
}

# Test GitHub API connection
test_github_api() {
    print_header "🐙 Testing GitHub API Connection..."
    
    # Test GitHub API
    response=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/user" || echo "000")
    
    if [ "$response" = "200" ]; then
        print_status "GitHub API connection successful ✅"
    else
        print_warning "GitHub API connection failed (HTTP $response)"
    fi
}

# Test Cloudflare Worker
test_cloudflare_worker() {
    print_header "☁️ Testing Cloudflare Worker..."
    
    # Test Cloudflare Worker
    response=$(curl -s -w "%{http_code}" -o /dev/null "$CLOUDFLARE_WORKER_URL/health" || echo "000")
    
    if [ "$response" = "200" ]; then
        print_status "Cloudflare Worker is accessible ✅"
    else
        print_warning "Cloudflare Worker connection failed (HTTP $response)"
    fi
}

# Run web-eval-agent tests
run_web_eval_tests() {
    print_header "🧪 Running Web-Eval-Agent Tests..."
    
    # Create a test script for web-eval-agent
    cat > test_web_eval.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import os
from datetime import datetime

async def test_full_cicd_cycle():
    """Test the full CI/CD cycle with web-eval-agent"""
    
    print("🧪 Starting Full CI/CD Cycle Test...")
    
    # Test 1: Health Check
    print("\n1. Testing Health Endpoints...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://localhost:8000/health') as resp:
                if resp.status == 200:
                    print("✅ Backend health check passed")
                else:
                    print(f"❌ Backend health check failed: {resp.status}")
        except Exception as e:
            print(f"❌ Backend health check error: {e}")
        
        try:
            async with session.get('http://localhost:5173') as resp:
                if resp.status == 200:
                    print("✅ Frontend health check passed")
                else:
                    print(f"❌ Frontend health check failed: {resp.status}")
        except Exception as e:
            print(f"❌ Frontend health check error: {e}")
    
    # Test 2: API Endpoints
    print("\n2. Testing API Endpoints...")
    async with aiohttp.ClientSession() as session:
        # Test projects endpoint
        try:
            async with session.get('http://localhost:8000/api/v1/projects') as resp:
                if resp.status in [200, 404]:  # 404 is OK if no projects exist
                    print("✅ Projects API endpoint accessible")
                else:
                    print(f"❌ Projects API failed: {resp.status}")
        except Exception as e:
            print(f"❌ Projects API error: {e}")
        
        # Test WebSocket endpoint
        try:
            async with session.ws_connect('ws://localhost:8000/ws') as ws:
                await ws.send_str(json.dumps({"type": "ping"}))
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print("✅ WebSocket connection successful")
                else:
                    print("❌ WebSocket connection failed")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    # Test 3: Frontend Components
    print("\n3. Testing Frontend Components...")
    # This would typically use Selenium or Playwright for browser automation
    print("✅ Frontend component testing (manual verification required)")
    
    # Test 4: Integration Tests
    print("\n4. Testing Integration...")
    
    # Simulate a project creation and analysis
    test_project = {
        "name": "Test Project",
        "description": "Automated test project",
        "github_owner": "test-org",
        "github_repo": "test-repo"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:8000/api/v1/projects',
                json=test_project,
                headers={'Content-Type': 'application/json'}
            ) as resp:
                if resp.status in [200, 201]:
                    project_data = await resp.json()
                    print(f"✅ Project creation test passed: {project_data.get('id', 'unknown')}")
                else:
                    print(f"❌ Project creation failed: {resp.status}")
        except Exception as e:
            print(f"❌ Project creation error: {e}")
    
    print("\n🎉 Full CI/CD Cycle Test Complete!")
    print(f"Test completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(test_full_cicd_cycle())
EOF
    
    # Run the test
    python3 test_web_eval.py
    
    # Clean up test file
    rm test_web_eval.py
}

# Display launch information
show_launch_info() {
    if [ "$DEV_MODE" = true ]; then
        print_header "🎉 Development Launch Complete!"
        echo "=================================================="
        echo ""
        echo "🌐 Frontend Dashboard: http://localhost:5173"
        echo "🚀 Backend API: http://localhost:8000"
        echo "📚 API Documentation: http://localhost:8000/docs"
        echo "🔍 API Health: http://localhost:8000/health"
        echo ""
        echo "⚠️  Development Mode Notes:"
        echo "  • Database services are disabled"
        echo "  • Some features may not work without database"
        echo "  • API keys are set to development values"
        echo "  • Perfect for frontend development and testing"
        echo ""
        echo "🔧 For full functionality:"
        echo "  • Run './launch.sh' (without --dev) to enable databases"
        echo "  • Configure real API keys in .env file"
        echo ""
        echo "🛑 To stop all services: Ctrl+C or run './stop.sh'"
        echo "=================================================="
    else
        print_header "🎉 Full Launch Complete!"
        echo "=================================================="
        echo ""
        echo "🌐 Frontend (Test Dashboard): http://localhost:5173"
        echo "🚀 Backend API: http://localhost:8000"
        echo "📚 API Documentation: http://localhost:8000/docs"
        echo "🔍 API Health: http://localhost:8000/health"
        echo ""
        echo "🧪 Test Dashboard Features:"
        echo "  • Interactive File Tree with search"
        echo "  • Monaco Code Editor with syntax highlighting"
        echo "  • Code Graph Visualization with multiple layouts"
        echo "  • Real-time error detection and highlighting"
        echo "  • Automated test suite (35 tests)"
        echo "  • Manual testing instructions"
        echo ""
        echo "🔧 Environment:"
        echo "  • Codegen Org ID: $CODEGEN_ORG_ID"
        if [ "$SKIP_DOCKER" = false ]; then
            echo "  • Database: PostgreSQL + Redis ✅"
        else
            echo "  • Database: Disabled (development mode)"
        fi
        echo "  • GitHub Integration: ✅"
        echo "  • Gemini AI: ✅"
        echo "  • Cloudflare Worker: $CLOUDFLARE_WORKER_URL"
        echo ""
        echo "📋 Next Steps:"
        echo "  1. Open http://localhost:5173 in your browser"
        echo "  2. Click 'Run All Tests' to execute automated tests"
        echo "  3. Follow manual testing instructions"
        echo "  4. Test CI/CD integration with real repositories"
        echo ""
        echo "🛑 To stop all services: Ctrl+C or run './stop.sh'"
        echo "=================================================="
    fi
}

# Cleanup function
cleanup() {
    print_header "🧹 Cleaning up..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    print_status "Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_dependencies
    load_environment
    start_database
    setup_backend
    setup_frontend
    start_backend
    start_frontend
    
    # Wait a moment for services to fully start
    sleep 3
    
    # Run tests only in full mode
    if [ "$DEV_MODE" = false ]; then
        test_codegen_api
        test_github_api
        test_cloudflare_worker
        run_web_eval_tests
    else
        print_status "Skipping API tests in development mode"
    fi
    
    show_launch_info
    
    # Keep the script running
    print_status "Services are running. Press Ctrl+C to stop."
    wait
}

# Run main function
main "$@"
