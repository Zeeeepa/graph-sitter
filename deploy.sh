#!/bin/bash

# Enhanced Codebase Analytics Deployment Script
set -e

echo "🚀 Starting Enhanced Codebase Analytics Deployment"
echo "=================================================="

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Function to check service health
check_service_health() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    print_status "Checking health of $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            print_success "$service_name is healthy!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service_name failed to become healthy after $max_attempts attempts"
    return 1
}

# Parse command line arguments
ENVIRONMENT="development"
REBUILD=false
LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        --logs)
            LOGS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --env ENVIRONMENT    Set environment (development|production) [default: development]"
            echo "  --rebuild           Force rebuild of Docker images"
            echo "  --logs              Show logs after deployment"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "Deployment environment: $ENVIRONMENT"

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down --remove-orphans

# Remove old images if rebuild is requested
if [ "$REBUILD" = true ]; then
    print_status "Rebuilding Docker images..."
    docker-compose build --no-cache
else
    print_status "Building Docker images..."
    docker-compose build
fi

# Start services based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    print_status "Starting production services..."
    docker-compose up -d
    
    # Wait for services to be ready
    sleep 10
    
    # Check service health
    check_service_health "Backend API" "http://localhost:8000/health"
    check_service_health "Frontend" "http://localhost:3000"
    check_service_health "Nginx" "http://localhost:80"
    
    print_success "Production deployment completed!"
    print_status "Services are available at:"
    echo "  🌐 Frontend: http://localhost"
    echo "  🔧 API: http://localhost/api"
    echo "  📊 API Docs: http://localhost/api/docs"
    
else
    print_status "Starting development services..."
    docker-compose up -d backend
    
    # Wait for backend to be ready
    sleep 5
    
    # Check backend health
    check_service_health "Backend API" "http://localhost:8000/health"
    
    print_success "Development backend deployment completed!"
    print_status "Services are available at:"
    echo "  🔧 Backend API: http://localhost:8000"
    echo "  📊 API Docs: http://localhost:8000/docs"
    echo ""
    print_status "To start the frontend in development mode:"
    echo "  cd frontend && npm run dev"
fi

# Show logs if requested
if [ "$LOGS" = true ]; then
    print_status "Showing service logs (Ctrl+C to exit)..."
    docker-compose logs -f
fi

# Show container status
print_status "Container status:"
docker-compose ps

print_success "Deployment script completed successfully! 🎉"

