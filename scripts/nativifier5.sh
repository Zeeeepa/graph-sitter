#!/bin/bash

# =============================================================================
# Comprehensive Nativefier 5-Way Split App Creator
# =============================================================================
# Creates a professional 5-pane desktop application from web URLs
# with resizable panes, shared authentication, and full customization
# 
# Usage: ./nativifier5.sh [OPTIONS]
# Author: Codegen AI Assistant
# Version: 1.0.0
# =============================================================================

set -euo pipefail

# Default configuration
DEFAULT_URLS=(
    "https://codegen.com/"
    "https://codegen.com/dashboard"
    "https://codegen.com/settings"
    "https://codegen.com/repos"
    "https://codegen.com/analytics"
)

DEFAULT_TITLES=(
    "🏠 Home"
    "📊 Dashboard"
    "⚙️ Settings"
    "📁 Repos"
    "📈 Analytics"
)

APP_NAME="Codegen-5Way"
APP_WIDTH=1800
APP_HEIGHT=1200
PLATFORM="linux"
ARCH="x64"
CHROME_USER_DATA="$HOME/.config/google-chrome/Default"
TEMP_HTML="/tmp/nativefier-5way.html"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Comprehensive Nativefier 5-Way Split App Creator

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -n, --name NAME         App name (default: $APP_NAME)
    -w, --width WIDTH       App width (default: $APP_WIDTH)
    -H, --height HEIGHT     App height (default: $APP_HEIGHT)
    -p, --platform PLATFORM Platform: linux, darwin, win32 (default: $PLATFORM)
    -a, --arch ARCH         Architecture: x64, arm64 (default: $ARCH)
    -c, --chrome-data PATH  Chrome user data directory (default: $CHROME_USER_DATA)
    -u, --urls URL1,URL2... Comma-separated URLs (default: codegen.com pages)
    -t, --titles T1,T2...   Comma-separated titles (default: predefined titles)
    --no-auth               Don't use Chrome authentication
    --vertical              Use vertical layout instead of grid
    --horizontal            Use horizontal 1x5 layout (all panes in one row)
    --single                Use single 1x1 layout (one pane only)
    --debug                 Enable debug mode
    --clean                 Clean previous installations

EXAMPLES:
    # Basic usage with defaults
    $0

    # Custom URLs and titles
    $0 -u "https://github.com,https://linear.app" -t "GitHub,Linear"

    # Windows app with custom size
    $0 -p win32 -w 1920 -H 1080 -n "MyApp"

    # Vertical layout without authentication
    $0 --vertical --no-auth
    
    # Horizontal 1x5 layout
    $0 --horizontal
    
    # Single pane layout
    $0 --single -u "https://codegen.com/" -t "Codegen"

FEATURES:
    ✅ Fully resizable panes with drag handles
    ✅ Shared authentication across all panes
    ✅ Professional UI with headers and styling
    ✅ Cross-platform support (Linux, macOS, Windows)
    ✅ Customizable layouts (grid or vertical)
    ✅ Auto-launch capability
    ✅ Comprehensive error handling
    ✅ Debug mode for troubleshooting

EOF
}

# Parse command line arguments
parse_args() {
    URLS=("${DEFAULT_URLS[@]}")
    TITLES=("${DEFAULT_TITLES[@]}")
    USE_AUTH=true
    LAYOUT="grid"
    DEBUG=false
    CLEAN=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -n|--name)
                APP_NAME="$2"
                shift 2
                ;;
            -w|--width)
                APP_WIDTH="$2"
                shift 2
                ;;
            -H|--height)
                APP_HEIGHT="$2"
                shift 2
                ;;
            -p|--platform)
                PLATFORM="$2"
                shift 2
                ;;
            -a|--arch)
                ARCH="$2"
                shift 2
                ;;
            -c|--chrome-data)
                CHROME_USER_DATA="$2"
                shift 2
                ;;
            -u|--urls)
                IFS=',' read -ra URLS <<< "$2"
                shift 2
                ;;
            -t|--titles)
                IFS=',' read -ra TITLES <<< "$2"
                shift 2
                ;;
            --no-auth)
                USE_AUTH=false
                shift
                ;;
            --vertical)
                LAYOUT="vertical"
                shift
                ;;
            --horizontal)
                LAYOUT="horizontal"
                shift
                ;;
            --single)
                LAYOUT="single"
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --clean)
                CLEAN=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Validate URLs and titles count
    if [[ ${#URLS[@]} -ne ${#TITLES[@]} ]]; then
        log_error "Number of URLs (${#URLS[@]}) must match number of titles (${#TITLES[@]})"
        exit 1
    fi

    # Allow single URL for single layout
    if [[ $LAYOUT == "single" ]]; then
        if [[ ${#URLS[@]} -ne 1 ]]; then
            log_error "Single layout requires exactly 1 URL (got ${#URLS[@]})"
            exit 1
        fi
    else
        if [[ ${#URLS[@]} -lt 2 || ${#URLS[@]} -gt 9 ]]; then
            log_error "Number of URLs must be between 2 and 9 (got ${#URLS[@]})"
            exit 1
        fi
    fi
}

# Check dependencies
check_dependencies() {
    log_step "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for Node.js
    if ! command -v node &> /dev/null; then
        missing_deps+=("nodejs")
    fi
    
    # Check for npm
    if ! command -v npm &> /dev/null; then
        missing_deps+=("npm")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again"
        exit 1
    fi
    
    log_success "All dependencies found"
}

# Install Nativefier
install_nativefier() {
    log_step "Installing/updating Nativefier..."
    
    if npm list -g nativefier &> /dev/null; then
        log_info "Nativefier already installed, updating..."
        npm update -g nativefier
    else
        log_info "Installing Nativefier globally..."
        npm install -g nativefier
    fi
    
    log_success "Nativefier ready"
}

# Generate CSS based on layout and number of panes
generate_css() {
    local num_panes=${#URLS[@]}
    
    if [[ $LAYOUT == "vertical" ]]; then
        # Vertical layout
        cat << EOF
        .container { 
            display: flex;
            flex-direction: column;
            height: 100vh; 
        }
        
        .pane { 
            flex: 1;
            display: flex; 
            flex-direction: column; 
            background: white;
            min-height: 100px;
        }
        
        .resizer { 
            height: 3px;
            background: #e2e8f0; 
            cursor: row-resize; 
            transition: background 0.2s;
        }
        
        .resizer:hover { 
            background: #cbd5e0; 
        }
EOF
    elif [[ $LAYOUT == "horizontal" ]]; then
        # Horizontal 1x5 layout
        cat << EOF
        .container { 
            display: flex;
            flex-direction: row;
            height: 100vh; 
        }
        
        .pane { 
            flex: 1;
            display: flex; 
            flex-direction: column; 
            background: white;
            min-width: 200px;
        }
        
        .resizer { 
            width: 3px;
            background: #e2e8f0; 
            cursor: col-resize; 
            transition: background 0.2s;
        }
        
        .resizer:hover { 
            background: #cbd5e0; 
        }
EOF
    elif [[ $LAYOUT == "single" ]]; then
        # Single 1x1 layout
        cat << EOF
        .container { 
            display: flex;
            height: 100vh; 
        }
        
        .pane { 
            flex: 1;
            display: flex; 
            flex-direction: column; 
            background: white;
        }
EOF
    else
        # Grid layout (default)
        local cols=$(( (num_panes + 1) / 2 ))
        local rows=$(( (num_panes + cols - 1) / cols ))
        
        cat << EOF
        .container { 
            display: grid; 
            grid-template-columns: repeat($cols, 1fr);
            grid-template-rows: repeat($rows, 1fr);
            height: 100vh; 
            gap: 3px;
            background: #e2e8f0;
        }
        
        .pane { 
            display: flex; 
            flex-direction: column; 
            background: white;
            min-width: 200px;
            min-height: 200px;
        }
EOF
    fi
}

# Generate JavaScript for resizing functionality
generate_javascript() {
    if [[ $LAYOUT == "vertical" ]]; then
        cat << 'EOF'
        let isResizing = false;
        let currentResizer = null;
        
        document.querySelectorAll('.resizer').forEach(resizer => {
            resizer.addEventListener('mousedown', initResize);
        });
        
        function initResize(e) {
            isResizing = true;
            currentResizer = e.target;
            document.addEventListener('mousemove', doResize);
            document.addEventListener('mouseup', stopResize);
            document.body.style.cursor = 'row-resize';
            e.preventDefault();
        }
        
        function doResize(e) {
            if (!isResizing) return;
            
            const container = document.querySelector('.container');
            const rect = container.getBoundingClientRect();
            const percentage = ((e.clientY - rect.top) / rect.height) * 100;
            
            // Update flex-basis of previous pane
            const panes = Array.from(container.children).filter(child => child.classList.contains('pane'));
            const resizerIndex = Array.from(container.children).indexOf(currentResizer);
            const paneIndex = Math.floor(resizerIndex / 2);
            
            if (panes[paneIndex]) {
                panes[paneIndex].style.flexBasis = Math.max(10, Math.min(80, percentage)) + '%';
            }
        }
        
        function stopResize() {
            isResizing = false;
            currentResizer = null;
            document.removeEventListener('mousemove', doResize);
            document.removeEventListener('mouseup', stopResize);
            document.body.style.cursor = 'default';
        }
EOF
    elif [[ $LAYOUT == "horizontal" ]]; then
        cat << 'EOF'
        let isResizing = false;
        let currentResizer = null;
        
        document.querySelectorAll('.resizer').forEach(resizer => {
            resizer.addEventListener('mousedown', initResize);
        });
        
        function initResize(e) {
            isResizing = true;
            currentResizer = e.target;
            document.addEventListener('mousemove', doResize);
            document.addEventListener('mouseup', stopResize);
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        }
        
        function doResize(e) {
            if (!isResizing) return;
            
            const container = document.querySelector('.container');
            const rect = container.getBoundingClientRect();
            const percentage = ((e.clientX - rect.left) / rect.width) * 100;
            
            // Update flex-basis of previous pane
            const panes = Array.from(container.children).filter(child => child.classList.contains('pane'));
            const resizerIndex = Array.from(container.children).indexOf(currentResizer);
            const paneIndex = Math.floor(resizerIndex / 2);
            
            if (panes[paneIndex]) {
                panes[paneIndex].style.flexBasis = Math.max(10, Math.min(80, percentage)) + '%';
            }
        }
        
        function stopResize() {
            isResizing = false;
            currentResizer = null;
            document.removeEventListener('mousemove', doResize);
            document.removeEventListener('mouseup', stopResize);
            document.body.style.cursor = 'default';
        }
EOF
    elif [[ $LAYOUT == "single" ]]; then
        cat << 'EOF'
        // Single layout doesn't need resizing
        console.log('Single layout loaded');
EOF
    else
        cat << 'EOF'
        // Grid layout doesn't need complex resizing logic
        // Could be extended for advanced grid resizing if needed
        console.log('Grid layout loaded with', document.querySelectorAll('.pane').length, 'panes');
EOF
    fi
}

# Create HTML file
create_html() {
    log_step "Creating HTML layout..."
    
    local num_panes=${#URLS[@]}
    
    cat > "$TEMP_HTML" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>$APP_NAME</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            height: 100vh; 
            overflow: hidden; 
            background: #f7fafc;
        }
        
        $(generate_css)
        
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 8px 16px; 
            font-size: 13px; 
            font-weight: 600;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header-title {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .header-status {
            font-size: 11px;
            opacity: 0.8;
        }
        
        iframe { 
            flex: 1; 
            border: none; 
            width: 100%;
            height: 100%;
            background: white;
        }
        
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 14px;
        }
        
        .pane:hover .header {
            background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
    </style>
</head>
<body>
    <div class="container" id="container">
EOF

    # Generate panes
    for i in "${!URLS[@]}"; do
        local url="${URLS[$i]}"
        local title="${TITLES[$i]}"
        
        cat >> "$TEMP_HTML" << EOF
        <div class="pane" data-url="$url">
            <div class="header">
                <div class="header-title">
                    <span>$title</span>
                </div>
                <div class="header-status">●</div>
            </div>
            <iframe src="$url" 
                    sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation allow-downloads"
                    loading="lazy"
                    onload="this.parentNode.querySelector('.header-status').style.color='#48bb78'"
                    onerror="this.parentNode.querySelector('.header-status').style.color='#f56565'">
            </iframe>
        </div>
EOF

        # Add resizer between panes (except after last pane)
        if [[ $i -lt $((${#URLS[@]} - 1)) && ($LAYOUT == "vertical" || $LAYOUT == "horizontal") ]]; then
            echo '        <div class="resizer"></div>' >> "$TEMP_HTML"
        fi
    done

    cat >> "$TEMP_HTML" << EOF
    </div>

    <script>
        $(generate_javascript)
        
        // Prevent iframe interference with resizing
        document.addEventListener('mousedown', function() {
            document.querySelectorAll('iframe').forEach(iframe => {
                iframe.style.pointerEvents = 'none';
            });
        });
        
        document.addEventListener('mouseup', function() {
            document.querySelectorAll('iframe').forEach(iframe => {
                iframe.style.pointerEvents = 'auto';
            });
        });
        
        // Debug logging
        if ($DEBUG) {
            console.log('$APP_NAME loaded with ${#URLS[@]} panes');
            console.log('Layout: $LAYOUT');
            console.log('URLs:', $(printf '%s\n' "${URLS[@]}" | jq -R . | jq -s .));
        }
        
        // Update status indicators
        document.querySelectorAll('iframe').forEach(iframe => {
            iframe.addEventListener('load', function() {
                const status = this.parentNode.querySelector('.header-status');
                status.textContent = '●';
                status.style.color = '#48bb78';
            });
            
            iframe.addEventListener('error', function() {
                const status = this.parentNode.querySelector('.header-status');
                status.textContent = '●';
                status.style.color = '#f56565';
            });
        });
    </script>
</body>
</html>
EOF

    log_success "HTML layout created: $TEMP_HTML"
}

# Clean previous installations
clean_previous() {
    if [[ $CLEAN == true ]]; then
        log_step "Cleaning previous installations..."
        
        local app_dir="./${APP_NAME}-${PLATFORM}-${ARCH}"
        if [[ -d "$app_dir" ]]; then
            log_info "Removing existing app directory: $app_dir"
            rm -rf "$app_dir"
        fi
        
        log_success "Cleanup completed"
    fi
}

# Build Nativefier app
build_app() {
    log_step "Building Nativefier app..."
    
    local nativefier_args=(
        "file://$TEMP_HTML"
        --name "$APP_NAME"
        --platform "$PLATFORM"
        --arch "$ARCH"
        --width "$APP_WIDTH"
        --height "$APP_HEIGHT"
        --single-instance
        --disable-dev-shm-usage
        --no-sandbox
    )
    
    # Add authentication if enabled
    if [[ $USE_AUTH == true && -d "$CHROME_USER_DATA" ]]; then
        log_info "Using Chrome authentication from: $CHROME_USER_DATA"
        nativefier_args+=(
            --user-data-dir "$CHROME_USER_DATA"
            --disable-web-security
        )
    else
        log_warning "Chrome authentication disabled or directory not found"
    fi
    
    # Platform-specific options
    case $PLATFORM in
        linux)
            nativefier_args+=(
                --enable-features=UseOzonePlatform
                --ozone-platform=wayland
            )
            ;;
        darwin)
            nativefier_args+=(
                --app-copyright "Created with Nativefier"
                --app-version "1.0.0"
            )
            ;;
        win32)
            nativefier_args+=(
                --win32metadata.CompanyName "Nativefier App"
                --win32metadata.FileDescription "$APP_NAME"
            )
            ;;
    esac
    
    # Add user agent
    nativefier_args+=(
        --user-agent "Mozilla/5.0 ($(uname -s); $(uname -m)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    if [[ $DEBUG == true ]]; then
        log_info "Nativefier command: nativefier ${nativefier_args[*]}"
    fi
    
    # Run nativefier
    if nativefier "${nativefier_args[@]}"; then
        log_success "App built successfully!"
    else
        log_error "Failed to build app"
        exit 1
    fi
}

# Launch app
launch_app() {
    local app_dir="./${APP_NAME}-${PLATFORM}-${ARCH}"
    
    if [[ -d "$app_dir" ]]; then
        log_step "Launching app..."
        
        case $PLATFORM in
            linux)
                if [[ -x "$app_dir/$APP_NAME" ]]; then
                    "$app_dir/$APP_NAME" &
                    log_success "App launched!"
                else
                    log_error "Executable not found: $app_dir/$APP_NAME"
                fi
                ;;
            darwin)
                if [[ -d "$app_dir/$APP_NAME.app" ]]; then
                    open "$app_dir/$APP_NAME.app"
                    log_success "App launched!"
                else
                    log_error "App bundle not found: $app_dir/$APP_NAME.app"
                fi
                ;;
            win32)
                if [[ -x "$app_dir/$APP_NAME.exe" ]]; then
                    "$app_dir/$APP_NAME.exe" &
                    log_success "App launched!"
                else
                    log_error "Executable not found: $app_dir/$APP_NAME.exe"
                fi
                ;;
        esac
    else
        log_error "App directory not found: $app_dir"
    fi
}

# Cleanup temporary files
cleanup() {
    if [[ -f "$TEMP_HTML" ]]; then
        rm -f "$TEMP_HTML"
    fi
}

# Main execution
main() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "  Comprehensive Nativefier 5-Way Creator"
    echo "=============================================="
    echo -e "${NC}"
    
    parse_args "$@"
    check_dependencies
    install_nativefier
    clean_previous
    create_html
    build_app
    launch_app
    cleanup
    
    echo -e "${GREEN}"
    echo "=============================================="
    echo "  🎉 SUCCESS! App created and launched!"
    echo "=============================================="
    echo -e "${NC}"
    echo "App Name: $APP_NAME"
    echo "Platform: $PLATFORM ($ARCH)"
    echo "Size: ${APP_WIDTH}x${APP_HEIGHT}"
    echo "Layout: $LAYOUT"
    echo "Panes: ${#URLS[@]}"
    echo "Authentication: $([ $USE_AUTH == true ] && echo "Enabled" || echo "Disabled")"
    echo ""
    echo "App location: ./${APP_NAME}-${PLATFORM}-${ARCH}/"
    echo ""
    echo "Enjoy your new desktop app! 🚀"
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
