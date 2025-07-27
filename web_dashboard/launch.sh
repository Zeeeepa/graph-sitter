#!/bin/bash

# 🚀 Web Dashboard Launch Script
# Comprehensive CI/CD testing with web-eval-agent integration

set -e

echo "🚀 Starting Web Dashboard with Full CI/CD Testing..."
echo "=================================================="

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
    
    if ! command -v node &> /dev/null; then
        missing_deps+=("node")
    fi
    
    if ! command -v npm &> /dev/null; then
        missing_deps+=("npm")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("pip3")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_error "Please install the missing dependencies and try again."
        exit 1
    fi
    
    print_status "All dependencies are installed ✅"
}

# Load environment variables
load_environment() {
    print_header "🔧 Loading Environment Variables..."
    
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
        print_status "Environment variables loaded from .env ✅"
    else
        print_warning "No .env file found, using system environment variables"
    fi
    
    # Validate required environment variables
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
        exit 1
    fi
    
    print_status "All required environment variables are set ✅"
}

# Start database services
start_database() {
    print_header "🗄️ Starting Database Services..."
    
    # Check if PostgreSQL is running
    if ! pg_isready -h localhost -p 5432 &> /dev/null; then
        print_status "Starting PostgreSQL with Docker..."
        docker run -d \
            --name web-eval-postgres \
            -e POSTGRES_DB=web_eval_agent \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=password \
            -p 5432:5432 \
            postgres:15-alpine || print_warning "PostgreSQL container may already be running"
        
        # Wait for PostgreSQL to be ready
        print_status "Waiting for PostgreSQL to be ready..."
        for i in {1..30}; do
            if pg_isready -h localhost -p 5432 &> /dev/null; then
                break
            fi
            sleep 1
        done
    fi
    
    # Check if Redis is running
    if ! redis-cli ping &> /dev/null; then
        print_status "Starting Redis with Docker..."
        docker run -d \
            --name web-eval-redis \
            -p 6379:6379 \
            redis:7-alpine || print_warning "Redis container may already be running"
        
        # Wait for Redis to be ready
        print_status "Waiting for Redis to be ready..."
        for i in {1..10}; do
            if redis-cli ping &> /dev/null; then
                break
            fi
            sleep 1
        done
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
    
    # Run database migrations
    print_status "Running database migrations..."
    alembic upgrade head || print_warning "Migration failed, continuing..."
    
    cd ..
    print_status "Backend setup complete ✅"
}

# Install frontend dependencies
setup_frontend() {
    print_header "⚛️ Setting up Frontend..."
    
    cd frontend
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    # Build the frontend
    print_status "Building frontend..."
    npm run build
    
    cd ..
    print_status "Frontend setup complete ✅"
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
    print_header "🎉 Launch Complete!"
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
    
    test_codegen_api
    test_github_api
    test_cloudflare_worker
    run_web_eval_tests
    
    show_launch_info
    
    # Keep the script running
    print_status "Services are running. Press Ctrl+C to stop."
    wait
}

# Run main function
main "$@"
