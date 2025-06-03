# Browser Use Suite Launcher

A PowerShell script to easily set up and launch the complete Browser Use ecosystem including:
- **browser-use**: Core AI browser automation library
- **web-ui**: Gradio-based web interface 
- **workflow-use**: Deterministic workflow automation (RPA 2.0)

## Quick Start

1. **Download the script**: Save `launch-browser-use-suite.ps1` to your desired location
2. **Run with default settings**:
   ```powershell
   .\launch-browser-use-suite.ps1
   ```
3. **Access the web interface**: Open http://127.0.0.1:7788 in your browser

## Prerequisites

### For Local Installation
- Python 3.11+
- Git
- Node.js and npm
- UV package manager (recommended, will fallback to pip)

### For Docker Installation
- Docker Desktop
- Docker Compose

## Usage Examples

### Basic Usage
```powershell
# Install and launch everything with defaults
.\launch-browser-use-suite.ps1
```

### Custom Configuration
```powershell
# Custom directory and port
.\launch-browser-use-suite.ps1 -WorkingDirectory "D:\my-browser-use" -WebUIPort 8080

# Use Docker with persistent browser
.\launch-browser-use-suite.ps1 -UseDocker -PersistentBrowser

# Skip installation and just launch
.\launch-browser-use-suite.ps1 -SkipInstall
```

### Docker Mode
```powershell
# Use Docker instead of local Python environment
.\launch-browser-use-suite.ps1 -UseDocker
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-WorkingDirectory` | Installation directory | `C:\browser-use-suite` |
| `-PythonVersion` | Python version to use | `3.11` |
| `-WebUIPort` | Web UI port | `7788` |
| `-WebUIIP` | Web UI IP address | `127.0.0.1` |
| `-SkipInstall` | Skip installation, just launch | `false` |
| `-UseDocker` | Use Docker instead of local install | `false` |
| `-PersistentBrowser` | Keep browser open between tasks | `false` |
| `-Help` | Show help message | `false` |

## What the Script Does

1. **Checks Prerequisites**: Verifies all required tools are installed
2. **Creates Working Directory**: Sets up the installation location
3. **Clones Repositories**: Downloads all three Browser Use components
4. **Sets Up Environments**: 
   - Creates Python virtual environments
   - Installs dependencies
   - Builds the workflow extension
   - Configures environment files
5. **Launches Web UI**: Starts the Gradio interface
6. **Opens Browser**: Automatically opens the web interface

## After Installation

### Web Interface
- **URL**: http://127.0.0.1:7788 (or your custom IP/port)
- **Features**: Full browser automation with AI agents
- **Models**: Supports OpenAI, Anthropic, Google, Azure, DeepSeek, Ollama, etc.

### Workflow Commands
Navigate to `{WorkingDirectory}\workflow-use\workflows` and use:

```powershell
# Create a new workflow
python cli.py create-workflow

# Run workflow as tool with AI prompt
python cli.py run-as-tool examples/example.workflow.json --prompt "fill the form with example data"

# Run workflow with predefined variables
python cli.py run-workflow examples/example.workflow.json

# See all available commands
python cli.py --help
```

### Docker Mode
When using Docker:
- **Web Interface**: http://127.0.0.1:7788
- **VNC Viewer**: http://127.0.0.1:6080/vnc.html (password: "youvncpassword")

## Configuration

### API Keys
Edit the `.env` files in each component directory:
- `web-ui\.env`: Add your LLM API keys (OpenAI, Anthropic, etc.)
- `workflow-use\workflows\.env`: Add your OpenAI API key

### Environment Variables
The script automatically creates `.env` files from examples. You'll need to add your API keys:

```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
# ... other API keys as needed
```

## Troubleshooting

### Common Issues
1. **Missing Prerequisites**: Install Python 3.11+, Git, Node.js, and npm
2. **Permission Errors**: Run PowerShell as Administrator
3. **Port Conflicts**: Use `-WebUIPort` to specify a different port
4. **API Key Errors**: Ensure your API keys are properly set in `.env` files

### Stopping the Services
- **Local Mode**: Press Ctrl+C in the PowerShell window
- **Docker Mode**: Run `docker-compose down` in the web-ui directory

## Features

### Browser Use Core
- AI-powered browser automation
- Support for multiple LLM providers
- Playwright-based browser control
- Screenshot and interaction capabilities

### Web UI
- User-friendly Gradio interface
- Real-time browser interaction viewing
- Custom browser support
- Persistent browser sessions
- High-definition screen recording

### Workflow Use
- Record-once, replay-forever workflows
- Deterministic automation (RPA 2.0)
- Self-healing capabilities
- Variable extraction from forms
- LLM fallback when steps fail

## License

This launcher script is provided as-is. The individual Browser Use components maintain their own licenses (MIT).

