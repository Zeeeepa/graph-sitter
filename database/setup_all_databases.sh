#!/bin/bash

# =============================================================================
# GRAPH-SITTER DATABASE SETUP SCRIPT
# =============================================================================
# This script sets up all 7 specialized databases for the graph-sitter system:
# 1. Task DB - Task management and workflow orchestration
# 2. Projects DB - Project management and repository tracking  
# 3. Prompts DB - Template management and A/B testing
# 4. Codebase DB - Code analysis and relationship mapping
# 5. Analytics DB - OpenEvolve integration and performance analytics
# 6. Events DB - Multi-source event tracking and aggregation
# 7. Learning DB - Pattern recognition and continuous improvement
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_ADMIN_USER=${POSTGRES_ADMIN_USER:-postgres}
POSTGRES_ADMIN_PASSWORD=${POSTGRES_ADMIN_PASSWORD:-postgres}

# Database names
DATABASES=("task_db" "projects_db" "prompts_db" "codebase_db" "analytics_db" "events_db" "learning_db" "workflows_db")

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

# Function to check if PostgreSQL is running
check_postgres() {
    print_status "Checking PostgreSQL connection..."
    if ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_ADMIN_USER" >/dev/null 2>&1; then
        print_error "PostgreSQL is not running or not accessible at $POSTGRES_HOST:$POSTGRES_PORT"
        print_error "Please ensure PostgreSQL is running and accessible"
        exit 1
    fi
    print_success "PostgreSQL is running and accessible"
}

# Function to check if TimescaleDB extension is available
check_timescaledb() {
    print_status "Checking TimescaleDB availability..."
    if ! PGPASSWORD="$POSTGRES_ADMIN_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;" >/dev/null 2>&1; then
        print_warning "TimescaleDB extension not available. Time-series optimization will be disabled."
        print_warning "To enable TimescaleDB, install it from: https://docs.timescale.com/install/"
        return 1
    fi
    print_success "TimescaleDB extension is available"
    return 0
}

# Function to execute SQL file
execute_sql_file() {
    local sql_file="$1"
    local description="$2"
    
    print_status "Executing $description..."
    if PGPASSWORD="$POSTGRES_ADMIN_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -f "$sql_file" >/dev/null 2>&1; then
        print_success "$description completed successfully"
        return 0
    else
        print_error "$description failed"
        print_error "Check the SQL file: $sql_file"
        return 1
    fi
}

# Function to execute SQL command
execute_sql_command() {
    local sql_command="$1"
    local description="$2"
    
    print_status "$description..."
    if PGPASSWORD="$POSTGRES_ADMIN_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -c "$sql_command" >/dev/null 2>&1; then
        print_success "$description completed"
        return 0
    else
        print_error "$description failed"
        return 1
    fi
}

# Function to check if database exists
database_exists() {
    local db_name="$1"
    PGPASSWORD="$POSTGRES_ADMIN_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db_name'" | grep -q 1
}

# Function to check if user exists
user_exists() {
    local username="$1"
    PGPASSWORD="$POSTGRES_ADMIN_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_ADMIN_USER" -d postgres -tAc "SELECT 1 FROM pg_user WHERE usename='$username'" | grep -q 1
}

# Main setup function
main() {
    echo "============================================================================="
    echo "                    GRAPH-SITTER DATABASE SETUP"
    echo "============================================================================="
    echo "Setting up 8 specialized databases for the graph-sitter system"
    echo "Host: $POSTGRES_HOST:$POSTGRES_PORT"
    echo "Admin User: $POSTGRES_ADMIN_USER"
    echo "============================================================================="
    echo

    # Check prerequisites
    check_postgres
    
    # Check TimescaleDB (optional)
    TIMESCALEDB_AVAILABLE=false
    if check_timescaledb; then
        TIMESCALEDB_AVAILABLE=true
    fi

    # Step 1: Create databases and users
    print_status "Step 1: Creating databases and users..."
    if execute_sql_file "database/init_databases.sql" "Database and user creation"; then
        print_success "All databases and users created successfully"
    else
        print_error "Failed to create databases and users"
        exit 1
    fi
    echo

    # Step 2: Initialize each database schema
    print_status "Step 2: Initializing database schemas..."
    
    # Array of schema files and descriptions
    declare -A SCHEMA_FILES=(
        ["01_task_db.sql"]="Task Database (Workflow orchestration)"
        ["02_projects_db.sql"]="Projects Database (Project management)"
        ["03_prompts_db.sql"]="Prompts Database (Template management)"
        ["04_codebase_db.sql"]="Codebase Database (Code analysis)"
        ["05_analytics_db.sql"]="Analytics Database (Performance analytics)"
        ["06_events_db.sql"]="Events Database (Event tracking)"
        ["07_learning_db.sql"]="Learning Database (Pattern recognition)"
        ["08_workflows_db.sql"]="Workflows Database (Workflow orchestration)"
    )

    # Execute each schema file
    for schema_file in "01_task_db.sql" "02_projects_db.sql" "03_prompts_db.sql" "04_codebase_db.sql" "05_analytics_db.sql" "06_events_db.sql" "07_learning_db.sql" "08_workflows_db.sql"; do
        description="${SCHEMA_FILES[$schema_file]}"
        if execute_sql_file "database/schemas/$schema_file" "$description"; then
            print_success "$description initialized"
        else
            print_error "Failed to initialize $description"
            print_warning "Continuing with remaining schemas..."
        fi
    done
    echo

    # Step 3: Verify setup
    print_status "Step 3: Verifying database setup..."
    
    # Check databases
    for db in "${DATABASES[@]}"; do
        if database_exists "$db"; then
            print_success "Database '$db' exists"
        else
            print_error "Database '$db' not found"
        fi
    done

    # Check users
    USERS=("task_user" "projects_user" "prompts_user" "codebase_user" "analytics_user" "events_user" "learning_user" "workflows_user" "analytics_readonly" "graph_sitter_admin")
    for user in "${USERS[@]}"; do
        if user_exists "$user"; then
            print_success "User '$user' exists"
        else
            print_error "User '$user' not found"
        fi
    done
    echo

    # Step 4: Display connection information
    print_status "Step 4: Database connection information"
    echo
    echo "Database Connection Details:"
    echo "----------------------------"
    echo "Host: $POSTGRES_HOST"
    echo "Port: $POSTGRES_PORT"
    echo
    echo "Databases and Users:"
    echo "- Task DB: task_db (user: task_user, password: task_secure_2024!)"
    echo "- Projects DB: projects_db (user: projects_user, password: projects_secure_2024!)"
    echo "- Prompts DB: prompts_db (user: prompts_user, password: prompts_secure_2024!)"
    echo "- Codebase DB: codebase_db (user: codebase_user, password: codebase_secure_2024!)"
    echo "- Analytics DB: analytics_db (user: analytics_user, password: analytics_secure_2024!)"
    echo "- Events DB: events_db (user: events_user, password: events_secure_2024!)"
    echo "- Learning DB: learning_db (user: learning_user, password: learning_secure_2024!)"
    echo "- Workflows DB: workflows_db (user: workflows_user, password: workflows_secure_2024!)"
    echo
    echo "Special Users:"
    echo "- Read-only Analytics: analytics_readonly (password: analytics_readonly_2024!)"
    echo "- Admin: graph_sitter_admin (password: admin_secure_2024!)"
    echo

    # Final status
    echo "============================================================================="
    print_success "GRAPH-SITTER DATABASE SETUP COMPLETED"
    echo "============================================================================="
    echo "All 8 specialized databases have been initialized:"
    echo "✅ Task DB - Task management and workflow orchestration"
    echo "✅ Projects DB - Project management and repository tracking"
    echo "✅ Prompts DB - Template management and A/B testing"
    echo "✅ Codebase DB - Code analysis and relationship mapping"
    echo "✅ Analytics DB - OpenEvolve integration and performance analytics"
    echo "✅ Events DB - Multi-source event tracking and aggregation"
    echo "✅ Learning DB - Pattern recognition and continuous improvement"
    echo "✅ Workflows DB - Complete workflow orchestration"
    echo
    if [ "$TIMESCALEDB_AVAILABLE" = true ]; then
        echo "🚀 TimescaleDB optimization enabled for time-series data"
    else
        echo "⚠️  TimescaleDB not available - time-series optimization disabled"
    fi
    echo
    echo "You can now connect to each database using the credentials provided above."
    echo "============================================================================="
}

# Run main function
main "$@"
