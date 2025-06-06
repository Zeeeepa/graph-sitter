# Strands Agent Dashboard Backend

A clean, maintainable backend implementation that properly integrates with the Strands tools ecosystem.

## 🎯 Overview

This backend replaces the previous improper implementation with a properly architected system that uses:

- ✅ **Proper Strands Tools**: `strands_tools.workflow` and `strands.tools.mcp.mcp_client`
- ✅ **ControlFlow Integration**: Agent management and task execution
- ✅ **Prefect Integration**: Flow orchestration and monitoring
- ✅ **Codegen SDK**: With org_id + token for code generation and plan creation
- ✅ **System Watcher**: Comprehensive monitoring of all components
- ✅ **Clean API**: RESTful endpoints with WebSocket support

## 🏗️ Architecture

### Core Components

1. **Strands Workflow Manager** (`strands_workflow.py`)
   - Proper integration with `strands_tools.workflow`
   - Workflow creation, execution, and monitoring
   - Mock implementation fallback for development

2. **Strands MCP Manager** (`strands_mcp.py`)
   - Proper integration with `strands.tools.mcp.mcp_client`
   - Agent session management and task execution
   - Mock implementation fallback for development

3. **ControlFlow Manager** (`strands_controlflow.py`)
   - ControlFlow agent management
   - Task and flow execution
   - Mock implementation fallback for development

4. **Prefect Manager** (`strands_prefect.py`)
   - Prefect flow registration and execution
   - System monitoring flows
   - Mock implementation fallback for development

5. **Codegen Manager** (`strands_codegen.py`)
   - Codegen SDK integration with org_id + token
   - Code generation and plan creation tasks
   - Mock implementation fallback for development

6. **System Watcher** (`system_watcher.py`)
   - Monitors system resources (CPU, memory, disk)
   - Tracks health of all Strands components
   - Alert management and notifications

7. **Orchestrator** (`strands_orchestrator.py`)
   - Coordinates all layers (Workflow, MCP, ControlFlow, Prefect)
   - Multi-layer orchestration management
   - Health monitoring across all components

8. **API Layer** (`strands_api.py`)
   - Clean RESTful API endpoints
   - WebSocket support for real-time updates
   - Background task execution

9. **Backend Entry Point** (`strands_backend.py`)
   - Unified server startup and configuration
   - Environment variable management
   - Logging and error handling

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required for Codegen SDK
export CODEGEN_ORG_ID="your-org-id"
export CODEGEN_TOKEN="your-token"

# Optional configuration
export STRANDS_HOST="0.0.0.0"
export STRANDS_PORT="8000"
export STRANDS_DEBUG="false"
export LOG_LEVEL="INFO"
```

### 3. Start the Backend

```bash
python strands_backend.py
```

Or using uvicorn directly:

```bash
uvicorn strands_api:create_strands_api --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Endpoints

### Health & Monitoring
- `GET /api/health` - Health check with system summary
- `GET /api/system/health` - Detailed system health
- `GET /api/system/layers` - Orchestration layer health

### Workflows
- `POST /api/workflows` - Create multi-layer orchestration
- `GET /api/workflows` - List all orchestrations
- `GET /api/workflows/{id}` - Get orchestration status
- `DELETE /api/workflows/{id}` - Cancel orchestration

### Codegen Tasks
- `POST /api/codegen/tasks` - Create code generation task
- `POST /api/codegen/plans` - Create plan creation task
- `GET /api/codegen/tasks` - List tasks
- `GET /api/codegen/tasks/{id}` - Get task status
- `DELETE /api/codegen/tasks/{id}` - Cancel task

### WebSocket
- `WS /ws` - Real-time updates for workflows and tasks

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CODEGEN_ORG_ID` | - | **Required**: Codegen organization ID |
| `CODEGEN_TOKEN` | - | **Required**: Codegen API token |
| `STRANDS_HOST` | `0.0.0.0` | Server host |
| `STRANDS_PORT` | `8000` | Server port |
| `STRANDS_DEBUG` | `false` | Debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `STRANDS_WORKFLOW_ENABLED` | `true` | Enable workflow layer |
| `STRANDS_MCP_ENABLED` | `true` | Enable MCP layer |
| `CONTROLFLOW_ENABLED` | `true` | Enable ControlFlow layer |
| `PREFECT_ENABLED` | `true` | Enable Prefect layer |
| `SYSTEM_WATCHER_ENABLED` | `true` | Enable system monitoring |

## 🧪 Development Mode

The backend includes mock implementations for all Strands tools, allowing development without requiring the actual Strands tools to be installed. This enables:

- ✅ Full API testing
- ✅ Frontend development
- ✅ Integration testing
- ✅ CI/CD pipeline testing

## 📊 Monitoring

The system watcher monitors:

- **System Resources**: CPU, memory, disk usage
- **Strands Services**: Health of all layers
- **Workflows**: Active and failed workflows
- **MCP Sessions**: Active agent sessions
- **ControlFlow**: Agents and tasks
- **Prefect**: Flows and runs

Alerts are generated when thresholds are exceeded and broadcast via WebSocket.

## 🔄 Real-time Updates

WebSocket connections provide real-time updates for:

- Workflow creation, execution, and completion
- Codegen task progress and results
- System health changes
- Alert notifications

## 🛠️ Integration with React UI

This backend is designed to support a React UI with:

- **Clean API**: RESTful endpoints for all operations
- **Real-time Updates**: WebSocket for live data
- **Error Handling**: Proper error responses and logging
- **CORS Support**: Configured for frontend integration

## 📁 File Structure

```
src/contexten/extensions/dashboard/
├── strands_backend.py      # Main entry point
├── strands_api.py          # API endpoints
├── strands_orchestrator.py # Multi-layer orchestration
├── strands_workflow.py     # Workflow management
├── strands_mcp.py          # MCP client integration
├── strands_controlflow.py  # ControlFlow integration
├── strands_prefect.py      # Prefect integration
├── strands_codegen.py      # Codegen SDK integration
├── system_watcher.py       # System monitoring
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## 🎯 Next Steps

1. **Install Proper Dependencies**: Replace mock implementations with actual Strands tools
2. **Configure Production**: Set up proper environment variables
3. **Deploy**: Use with your preferred deployment method
4. **Connect Frontend**: Integrate with React UI
5. **Monitor**: Use the system watcher for health monitoring

This backend provides a solid foundation for building a comprehensive Strands agent dashboard with proper tool integration and monitoring capabilities.

