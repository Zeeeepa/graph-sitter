#!/bin/bash

# Unified Webhooks Deployment Script
# This script helps deploy the unified webhook system to Modal

set -e

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check environment variables
check_env_vars() {
    local required_vars=("GITHUB_TOKEN" "GITHUB_ORG" "GITHUB_REPO")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set these variables in your .env file or environment."
        return 1
    fi
    
    return 0
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Check if .env file exists
    if [[ -f ".env" ]]; then
        print_status "Loading environment variables from .env file..."
        export $(grep -v '^#' .env | xargs)
    else
        print_warning ".env file not found. Make sure environment variables are set."
    fi
    
    # Check required environment variables
    if ! check_env_vars; then
        exit 1
    fi
    
    print_success "Environment setup complete"
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check if Modal CLI is installed
    if ! command_exists modal; then
        print_error "Modal CLI not found. Installing..."
        pip install modal
    fi
    
    # Check if Python dependencies are available
    python -c "import modal, fastapi, codegen" 2>/dev/null || {
        print_warning "Some Python dependencies missing. Installing..."
        pip install modal fastapi "codegen>=0.22.2" uvicorn pydantic "openai>=1.1.0" slack_sdk
    }
    
    print_success "Dependencies check complete"
}

# Function to authenticate with Modal
authenticate_modal() {
    print_status "Checking Modal authentication..."
    
    if ! modal token current >/dev/null 2>&1; then
        print_warning "Modal authentication required"
        print_status "Please authenticate with Modal..."
        modal token new
    else
        print_success "Modal authentication verified"
    fi
}

# Function to deploy to Modal
deploy_to_modal() {
    local app_name="${1:-unified-webhooks}"
    local deploy_mode="${2:-deploy}"
    
    print_status "Deploying to Modal..."
    print_status "App name: $app_name"
    print_status "Deploy mode: $deploy_mode"
    
    # Change to the script directory
    cd "$(dirname "$0")"
    
    if [[ "$deploy_mode" == "serve" ]]; then
        print_status "Starting development server..."
        modal serve webhooks.py --name "$app_name"
    else
        print_status "Deploying to production..."
        modal deploy webhooks.py --name "$app_name"
        
        if [[ $? -eq 0 ]]; then
            print_success "Deployment successful!"
            print_status "Your webhook endpoints are now available at:"
            echo "  - Unified webhook: https://$app_name.modal.run/unified-webhook"
            echo "  - GitHub only: https://$app_name.modal.run/github-only-webhook"
            echo "  - Linear only: https://$app_name.modal.run/linear-only-webhook"
            echo "  - Health check: https://$app_name.modal.run/health-check"
        else
            print_error "Deployment failed!"
            exit 1
        fi
    fi
}

# Function to show webhook configuration help
show_webhook_config() {
    local app_name="${1:-unified-webhooks}"
    
    echo ""
    print_status "Webhook Configuration Instructions:"
    echo ""
    echo "GitHub Webhook Setup:"
    echo "  1. Go to your repository settings → Webhooks"
    echo "  2. Add webhook with URL: https://$app_name.modal.run/unified-webhook"
    echo "  3. Select events: Pull requests, Issues, Pushes"
    echo "  4. Content type: application/json"
    echo ""
    echo "Linear Webhook Setup:"
    echo "  1. Go to Linear Settings → API → Webhooks"
    echo "  2. Add webhook with URL: https://$app_name.modal.run/unified-webhook"
    echo "  3. Select events: Issues, Comments, Projects"
    echo "  4. Save webhook configuration"
    echo ""
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n, --name NAME       Set app name (default: unified-webhooks)"
    echo "  -d, --dev             Deploy in development mode (serve)"
    echo "  -c, --config-only     Show webhook configuration instructions only"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy with default settings"
    echo "  $0 -n my-webhooks    # Deploy with custom app name"
    echo "  $0 -d                # Deploy in development mode"
    echo "  $0 -c                # Show webhook configuration only"
    echo ""
}

# Main function
main() {
    local app_name="unified-webhooks"
    local deploy_mode="deploy"
    local config_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                app_name="$2"
                shift 2
                ;;
            -d|--dev)
                deploy_mode="serve"
                shift
                ;;
            -c|--config-only)
                config_only=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Show configuration only if requested
    if [[ "$config_only" == true ]]; then
        show_webhook_config "$app_name"
        exit 0
    fi
    
    print_status "Starting unified webhooks deployment..."
    print_status "App name: $app_name"
    
    # Run deployment steps
    setup_environment
    check_dependencies
    authenticate_modal
    deploy_to_modal "$app_name" "$deploy_mode"
    
    # Show configuration instructions
    if [[ "$deploy_mode" == "deploy" ]]; then
        show_webhook_config "$app_name"
    fi
    
    print_success "Deployment process complete!"
}

# Run main function with all arguments
main "$@"

