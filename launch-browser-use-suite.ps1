# Browser Use Suite Launcher
# This script sets up and launches browser-use with web UI and workflow capabilities
# Author: Codegen
# Version: 1.0

param(
    [string]$WorkingDirectory = "C:\browser-use-suite",
    [string]$PythonVersion = "3.11",
    [int]$WebUIPort = 7788,
    [string]$WebUIIP = "127.0.0.1",
    [switch]$SkipInstall,
    [switch]$UseDocker,
    [switch]$PersistentBrowser,
    [switch]$Help
)

# Color functions for better output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Info { Write-ColorOutput Cyan $args }

# Help function
function Show-Help {
    Write-Host @"
Browser Use Suite Launcher

DESCRIPTION:
    Sets up and launches browser-use with web UI and workflow capabilities.

PARAMETERS:
    -WorkingDirectory   Directory to install components (default: C:\browser-use-suite)
    -PythonVersion      Python version to use (default: 3.11)
    -WebUIPort          Port for web UI (default: 7788)
    -WebUIIP            IP address for web UI (default: 127.0.0.1)
    -SkipInstall        Skip installation and just launch
    -UseDocker          Use Docker instead of local installation
    -PersistentBrowser  Keep browser open between tasks
    -Help               Show this help message

EXAMPLES:
    .\launch-browser-use-suite.ps1
    .\launch-browser-use-suite.ps1 -WorkingDirectory "D:\my-browser-use" -WebUIPort 8080
    .\launch-browser-use-suite.ps1 -UseDocker -PersistentBrowser
    .\launch-browser-use-suite.ps1 -SkipInstall

REQUIREMENTS:
    - Python 3.11+ (if not using Docker)
    - Git
    - Node.js and npm (for workflow extension)
    - Docker and Docker Compose (if using -UseDocker)
"@
}

# Check if help was requested
if ($Help) {
    Show-Help
    exit 0
}

# Function to check if a command exists
function Test-Command($command) {
    try {
        Get-Command $command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    $missing = @()
    
    if (-not (Test-Command "git")) {
        $missing += "Git"
    }
    
    if ($UseDocker) {
        if (-not (Test-Command "docker")) {
            $missing += "Docker"
        }
        if (-not (Test-Command "docker-compose")) {
            $missing += "Docker Compose"
        }
    } else {
        if (-not (Test-Command "python")) {
            $missing += "Python"
        }
        if (-not (Test-Command "node")) {
            $missing += "Node.js"
        }
        if (-not (Test-Command "npm")) {
            $missing += "npm"
        }
        if (-not (Test-Command "uv")) {
            Write-Warning "UV package manager not found. Will use pip instead."
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Error "Missing prerequisites: $($missing -join ', ')"
        Write-Error "Please install the missing components and try again."
        exit 1
    }
    
    Write-Success "All prerequisites found!"
}

# Function to create working directory
function New-WorkingDirectory {
    if (-not (Test-Path $WorkingDirectory)) {
        Write-Info "Creating working directory: $WorkingDirectory"
        New-Item -ItemType Directory -Path $WorkingDirectory -Force | Out-Null
    }
    Set-Location $WorkingDirectory
    Write-Success "Working directory: $WorkingDirectory"
}

# Function to clone repositories
function Get-Repositories {
    Write-Info "Cloning repositories..."
    
    $repos = @(
        @{Name="browser-use"; URL="https://github.com/browser-use/browser-use.git"},
        @{Name="web-ui"; URL="https://github.com/browser-use/web-ui.git"},
        @{Name="workflow-use"; URL="https://github.com/browser-use/workflow-use.git"}
    )
    
    foreach ($repo in $repos) {
        if (-not (Test-Path $repo.Name)) {
            Write-Info "Cloning $($repo.Name)..."
            git clone $repo.URL $repo.Name
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to clone $($repo.Name)"
                exit 1
            }
        } else {
            Write-Info "$($repo.Name) already exists, pulling latest changes..."
            Set-Location $repo.Name
            git pull
            Set-Location ..
        }
    }
    
    Write-Success "All repositories cloned/updated!"
}

# Function to setup Python environment for web-ui
function Set-WebUIEnvironment {
    Write-Info "Setting up Web UI environment..."
    Set-Location "$WorkingDirectory\web-ui"
    
    # Create virtual environment
    if (Test-Command "uv") {
        Write-Info "Using UV to create virtual environment..."
        uv venv --python $PythonVersion
    } else {
        Write-Info "Using Python to create virtual environment..."
        python -m venv .venv
    }
    
    # Activate virtual environment
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        Write-Info "Activating virtual environment..."
        & ".venv\Scripts\Activate.ps1"
    } else {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
    
    # Install dependencies
    Write-Info "Installing Python dependencies..."
    if (Test-Command "uv") {
        uv pip install -r requirements.txt
    } else {
        pip install -r requirements.txt
    }
    
    # Install Playwright
    Write-Info "Installing Playwright..."
    playwright install
    
    # Setup environment file
    if (-not (Test-Path ".env")) {
        Write-Info "Creating .env file..."
        Copy-Item ".env.example" ".env"
        Write-Warning "Please edit .env file and add your API keys!"
    }
    
    Set-Location $WorkingDirectory
    Write-Success "Web UI environment setup complete!"
}

# Function to setup workflow environment
function Set-WorkflowEnvironment {
    Write-Info "Setting up Workflow environment..."
    Set-Location "$WorkingDirectory\workflow-use"
    
    # Build extension
    Write-Info "Building workflow extension..."
    Set-Location "extension"
    npm install
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build workflow extension"
        exit 1
    }
    
    # Setup workflow Python environment
    Set-Location "..\workflows"
    
    if (Test-Command "uv") {
        Write-Info "Using UV to sync workflow environment..."
        uv sync
    } else {
        Write-Info "Creating workflow virtual environment..."
        python -m venv .venv
        if (Test-Path ".venv\Scripts\Activate.ps1") {
            & ".venv\Scripts\Activate.ps1"
            pip install -r requirements.txt
        }
    }
    
    # Install Playwright for workflows
    Write-Info "Installing Playwright for workflows..."
    playwright install chromium
    
    # Setup environment file
    if (-not (Test-Path ".env")) {
        Write-Info "Creating workflow .env file..."
        Copy-Item ".env.example" ".env"
        Write-Warning "Please edit workflows/.env file and add your OPENAI_API_KEY!"
    }
    
    Set-Location $WorkingDirectory
    Write-Success "Workflow environment setup complete!"
}

# Function to setup Docker environment
function Set-DockerEnvironment {
    Write-Info "Setting up Docker environment..."
    Set-Location "$WorkingDirectory\web-ui"
    
    # Setup environment file
    if (-not (Test-Path ".env")) {
        Write-Info "Creating .env file for Docker..."
        Copy-Item ".env.example" ".env"
        Write-Warning "Please edit .env file and add your API keys!"
    }
    
    Set-Location $WorkingDirectory
    Write-Success "Docker environment setup complete!"
}

# Function to launch web UI
function Start-WebUI {
    Write-Info "Starting Web UI..."
    Set-Location "$WorkingDirectory\web-ui"
    
    if ($UseDocker) {
        Write-Info "Starting Web UI with Docker..."
        if ($PersistentBrowser) {
            $env:CHROME_PERSISTENT_SESSION = "true"
        }
        docker-compose up --build -d
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Web UI started with Docker!"
            Write-Info "Web Interface: http://$WebUIIP`:7788"
            Write-Info "VNC Viewer: http://$WebUIIP`:6080/vnc.html"
        } else {
            Write-Error "Failed to start Web UI with Docker"
        }
    } else {
        Write-Info "Starting Web UI locally..."
        # Activate virtual environment
        if (Test-Path ".venv\Scripts\Activate.ps1") {
            & ".venv\Scripts\Activate.ps1"
        }
        
        $webUIArgs = @("webui.py", "--ip", $WebUIIP, "--port", $WebUIPort)
        if ($PersistentBrowser) {
            # Note: This might need to be configured in the web UI settings
            Write-Info "Persistent browser mode requested (configure in web UI settings)"
        }
        
        Write-Success "Starting Web UI on http://$WebUIIP`:$WebUIPort"
        python @webUIArgs
    }
    
    Set-Location $WorkingDirectory
}

# Function to show workflow commands
function Show-WorkflowCommands {
    Write-Info @"

WORKFLOW COMMANDS:
To use workflows, navigate to: $WorkingDirectory\workflow-use\workflows

Available commands:
1. Create a new workflow:
   python cli.py create-workflow

2. Run workflow as tool:
   python cli.py run-as-tool examples/example.workflow.json --prompt "your prompt here"

3. Run workflow with predefined variables:
   python cli.py run-workflow examples/example.workflow.json

4. See all commands:
   python cli.py --help

"@
}

# Function to open browser
function Open-Browser {
    Start-Sleep -Seconds 3
    Write-Info "Opening browser..."
    if ($UseDocker) {
        Start-Process "http://$WebUIIP`:7788"
    } else {
        Start-Process "http://$WebUIIP`:$WebUIPort"
    }
}

# Main execution
function Main {
    Write-Success "Browser Use Suite Launcher"
    Write-Success "=========================="
    
    # Check prerequisites
    Test-Prerequisites
    
    # Create working directory
    New-WorkingDirectory
    
    if (-not $SkipInstall) {
        # Clone repositories
        Get-Repositories
        
        if ($UseDocker) {
            # Setup Docker environment
            Set-DockerEnvironment
        } else {
            # Setup environments
            Set-WebUIEnvironment
            Set-WorkflowEnvironment
        }
        
        Write-Success "Installation complete!"
    }
    
    # Show workflow commands
    Show-WorkflowCommands
    
    # Launch Web UI
    Write-Info "Launching Browser Use Suite..."
    
    # Start web UI in background job for local installation
    if (-not $UseDocker) {
        $job = Start-Job -ScriptBlock {
            param($WorkingDir, $WebUIIP, $WebUIPort)
            Set-Location "$WorkingDir\web-ui"
            if (Test-Path ".venv\Scripts\Activate.ps1") {
                & ".venv\Scripts\Activate.ps1"
            }
            python webui.py --ip $WebUIIP --port $WebUIPort
        } -ArgumentList $WorkingDirectory, $WebUIIP, $WebUIPort
        
        Write-Success "Web UI started in background (Job ID: $($job.Id))"
        Write-Info "Web Interface: http://$WebUIIP`:$WebUIPort"
        
        # Open browser
        Open-Browser
        
        Write-Info @"

BROWSER USE SUITE IS RUNNING!

Web Interface: http://$WebUIIP`:$WebUIPort

To stop the Web UI, run: Stop-Job $($job.Id); Remove-Job $($job.Id)

Press Ctrl+C to exit this script (Web UI will continue running in background)
"@
        
        # Keep script running
        try {
            while ($true) {
                Start-Sleep -Seconds 5
                if ((Get-Job -Id $job.Id).State -eq "Failed") {
                    Write-Error "Web UI job failed!"
                    Receive-Job -Id $job.Id
                    break
                }
            }
        } catch {
            Write-Info "Stopping..."
        } finally {
            Stop-Job $job.Id -ErrorAction SilentlyContinue
            Remove-Job $job.Id -ErrorAction SilentlyContinue
        }
    } else {
        # Docker mode
        Start-WebUI
        Open-Browser
        
        Write-Info @"

BROWSER USE SUITE IS RUNNING WITH DOCKER!

Web Interface: http://$WebUIIP`:7788
VNC Viewer: http://$WebUIIP`:6080/vnc.html

To stop: docker-compose down (in the web-ui directory)
"@
    }
}

# Error handling
try {
    Main
} catch {
    Write-Error "An error occurred: $_"
    Write-Error $_.ScriptStackTrace
    exit 1
}

