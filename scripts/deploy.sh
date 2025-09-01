#!/usr/bin/env bash
# deploy.sh - Deployment script for graph-sitter
# 
# This script automates the deployment process for the graph-sitter project.
# It includes environment setup, testing, building, and deployment steps
# with proper error handling and logging.
#
# Usage: ./scripts/deploy.sh [environment]
#   environment: (optional) Deployment environment (dev, staging, prod)
#                Defaults to 'dev' if not specified

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="deploy_${TIMESTAMP}.log"
DEPLOY_ENV=${1:-dev}  # Default to 'dev' if not specified
PACKAGE_NAME="graph-sitter"
BACKUP_DIR="./backups/${TIMESTAMP}"

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function to print to console and log file
log() {
    local level=$1
    local message=$2
    local color=$NC
    
    case $level in
        "INFO") color=$BLUE ;;
        "SUCCESS") color=$GREEN ;;
        "WARNING") color=$YELLOW ;;
        "ERROR") color=$RED ;;
    esac
    
    echo -e "${color}[$(date +'%Y-%m-%d %H:%M:%S')] [${level}] ${message}${NC}" | tee -a $LOG_FILE
}

# Error handler
handle_error() {
    log "ERROR" "Deployment failed at line $1"
    log "INFO" "Check the log file for details: $LOG_FILE"
    exit 1
}

# Set up error trap
trap 'handle_error $LINENO' ERR

# Create backup directory
mkdir -p $BACKUP_DIR

# Display deployment information
log "INFO" "Starting deployment of $PACKAGE_NAME to $DEPLOY_ENV environment"
log "INFO" "Deployment timestamp: $TIMESTAMP"

# Ensure we're in the project root directory
if [ ! -f "pyproject.toml" ]; then
    log "ERROR" "Must run from project root directory containing pyproject.toml"
    exit 1
fi

# Create and activate virtual environment
log "INFO" "Setting up virtual environment"
if [ ! -d ".venv" ]; then
    log "INFO" "Creating virtual environment"
    uv venv
fi

# Source the virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    log "SUCCESS" "Virtual environment activated"
else
    log "ERROR" "Virtual environment activation failed"
    exit 1
fi

# Update dependencies
log "INFO" "Updating dependencies"
uv sync
log "SUCCESS" "Dependencies updated"

# Run linting and type checking
log "INFO" "Running code quality checks"
uv run ruff check . || log "WARNING" "Linting issues found, review the output"
uv run mypy . || log "WARNING" "Type checking issues found, review the output"

# Run tests
log "INFO" "Running tests"
uv run pytest -xvs || { log "ERROR" "Tests failed"; exit 1; }
log "SUCCESS" "All tests passed"

# Create backup of current version (if applicable)
if [ -d "dist" ]; then
    log "INFO" "Backing up current distribution"
    cp -r dist/* $BACKUP_DIR/ 2>/dev/null || log "WARNING" "No previous distribution to backup"
fi

# Build package
log "INFO" "Building package"
uv run python -m build
log "SUCCESS" "Package built successfully"

# Deploy based on environment
case $DEPLOY_ENV in
    "dev")
        log "INFO" "Deploying to development environment"
        # Development deployment steps here
        # Example: copy to development server, restart services, etc.
        log "SUCCESS" "Deployed to development environment"
        ;;
    "staging")
        log "INFO" "Deploying to staging environment"
        # Staging deployment steps here
        # Example: upload to staging server, run migrations, restart services
        log "SUCCESS" "Deployed to staging environment"
        ;;
    "prod")
        log "INFO" "Deploying to production environment"
        # Production deployment steps
        # Example: upload to production server, run with zero downtime, etc.
        
        # Confirmation for production deployment
        read -p "Are you sure you want to deploy to production? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "INFO" "Production deployment cancelled"
            exit 0
        fi
        
        log "SUCCESS" "Deployed to production environment"
        ;;
    *)
        log "ERROR" "Unknown environment: $DEPLOY_ENV"
        log "INFO" "Valid environments are: dev, staging, prod"
        exit 1
        ;;
esac

# Post-deployment tasks
log "INFO" "Running post-deployment tasks"
# Add any post-deployment tasks here (e.g., cache clearing, notifications)

# Deployment summary
log "SUCCESS" "Deployment completed successfully"
log "INFO" "Deployment log saved to: $LOG_FILE"

# Optional: Display deployment information
echo -e "\n${GREEN}=== Deployment Summary ===${NC}"
echo -e "Package: $PACKAGE_NAME"
echo -e "Environment: $DEPLOY_ENV"
echo -e "Timestamp: $TIMESTAMP"
echo -e "Log file: $LOG_FILE"
echo -e "${GREEN}=========================${NC}"

exit 0

