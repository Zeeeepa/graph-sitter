#!/bin/bash

# 🛑 Web Dashboard Stop Script
# Gracefully stop all services

echo "🛑 Stopping Web Dashboard Services..."
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Stop Node.js processes (Vite dev server)
print_header "🌐 Stopping Frontend Services..."
pkill -f "vite" || print_warning "No Vite processes found"
pkill -f "npm run dev" || print_warning "No npm dev processes found"
print_status "Frontend services stopped"

# Stop Python processes (FastAPI server)
print_header "🐍 Stopping Backend Services..."
pkill -f "uvicorn" || print_warning "No uvicorn processes found"
pkill -f "fastapi" || print_warning "No FastAPI processes found"
print_status "Backend services stopped"

# Stop Docker containers
print_header "🐳 Stopping Docker Services..."
docker stop web-eval-postgres 2>/dev/null || print_warning "PostgreSQL container not running"
docker stop web-eval-redis 2>/dev/null || print_warning "Redis container not running"

# Remove Docker containers
docker rm web-eval-postgres 2>/dev/null || print_warning "PostgreSQL container not found"
docker rm web-eval-redis 2>/dev/null || print_warning "Redis container not found"
print_status "Docker services stopped"

# Clean up any remaining processes
print_header "🧹 Final Cleanup..."
pkill -f "web_dashboard" 2>/dev/null || true
pkill -f "test_web_eval" 2>/dev/null || true

print_status "All services have been stopped ✅"
echo "====================================="
