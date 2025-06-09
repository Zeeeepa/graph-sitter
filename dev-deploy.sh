#!/bin/bash

# Development Deployment Script (No Docker Required)
set -e

echo "🚀 Starting Enhanced Codebase Analytics Development Deployment"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        print_status "Killing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 2
    fi
}

# Parse command line arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false
INSTALL_DEPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --backend-only      Start only the backend service"
            echo "  --frontend-only     Start only the frontend service"
            echo "  --install-deps      Install dependencies before starting"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Install dependencies if requested
if [ "$INSTALL_DEPS" = true ]; then
    print_status "Installing backend dependencies..."
    cd backend
    pip3 install -r requirements.txt
    cd ..
    
    print_status "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start backend
if [ "$FRONTEND_ONLY" = false ]; then
    print_status "Starting backend service..."
    
    # Kill any existing process on port 8000
    kill_port 8000
    
    cd backend
    print_status "Backend starting on http://localhost:8000"
    python3 api.py &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to start
    sleep 3
    
    # Check if backend is running
    if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
        print_success "Backend is running successfully!"
        echo "  🔧 API: http://localhost:8000"
        echo "  📊 API Docs: http://localhost:8000/docs"
    else
        print_error "Backend failed to start"
        exit 1
    fi
fi

# Start frontend
if [ "$BACKEND_ONLY" = false ]; then
    print_status "Starting frontend service..."
    
    # Kill any existing process on ports 3000-3010
    for port in {3000..3010}; do
        kill_port $port
    done
    
    cd frontend
    print_status "Frontend starting..."
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend to start
    sleep 5
    
    print_success "Frontend is starting!"
    print_status "Frontend will be available at one of these URLs:"
    echo "  🌐 http://localhost:3000"
    echo "  🌐 http://localhost:3001"
    echo "  🌐 http://localhost:3002"
fi

# Create a cleanup function
cleanup() {
    print_status "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill processes on known ports
    kill_port 8000
    for port in {3000..3010}; do
        kill_port $port
    done
    
    print_success "Services stopped."
}

# Set up signal handlers
trap cleanup EXIT INT TERM

print_success "Development deployment completed! 🎉"
print_status "Services are running. Press Ctrl+C to stop all services."

# Keep script running
if [ "$BACKEND_ONLY" = false ] && [ "$FRONTEND_ONLY" = false ]; then
    print_status "Both services are running. Monitoring..."
    while true; do
        sleep 10
        # Check if services are still running
        if ! curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
            print_warning "Backend appears to be down"
        fi
    done
elif [ "$BACKEND_ONLY" = true ]; then
    print_status "Backend service is running. Monitoring..."
    while true; do
        sleep 10
        if ! curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
            print_error "Backend has stopped"
            break
        fi
    done
else
    print_status "Frontend service is running in background."
    wait $FRONTEND_PID
fi

