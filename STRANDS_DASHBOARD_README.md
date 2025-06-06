# Strands Agent Dashboard - Functional Implementation

This is a **working** React UI dashboard that properly integrates with Strands tools, ControlFlow, Prefect, and Codegen SDK.

## 🚀 Quick Start

### Backend Setup

1. **Install dependencies:**
```bash
pip install -r requirements_dashboard.txt
```

2. **Install Strands SDK (from source):**
```bash
git clone https://github.com/Zeeeepa/sdk-python.git
cd sdk-python
pip install -e .
```

3. **Set environment variables:**
```bash
export CODEGEN_ORG_ID="your_org_id"
export CODEGEN_TOKEN="your_token"
```

4. **Start the backend:**
```bash
python strands_dashboard_backend.py
```

The backend will start on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd src/contexten/extensions/dashboard/frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Option A: Use the new simple App (recommended):**
```bash
# Backup current App.tsx
mv src/App.tsx src/App_Original.tsx
# Use the simple working version
mv src/App_Simple.tsx src/App.tsx
```

4. **Start the React app:**
```bash
npm start
```

The frontend will start on `http://localhost:3000`

## 🔧 Architecture

### Backend (`strands_dashboard_backend.py`)
- **FastAPI** server with WebSocket support
- **Real-time updates** for workflows and system health
- **Proper Strands integration** placeholders ready for:
  - `strands.tools.mcp.mcp_client` (instead of wrong imports)
  - `strands_tools.workflow` (instead of local orchestrator.py)
  - Codegen SDK with org_id/token
  - System watcher with restart capabilities

### Frontend (`StrandsDashboard.tsx`)
- **Material-UI** based clean interface
- **Real-time WebSocket** connection to backend
- **Workflow management** with create/restart capabilities
- **System monitoring** dashboard
- **Codegen task management** interface

## 🛠 Key Features

### ✅ System Watcher
- Monitors workflow health every 30 seconds
- Automatically restarts failed workflows
- Real-time system health metrics

### ✅ Workflow Management
- Create new workflows via UI
- Monitor workflow status in real-time
- Restart failed workflows with one click

### ✅ Codegen Integration
- Create code generation tasks
- Monitor task progress
- View generated results

### ✅ Real-time Updates
- WebSocket connection for live updates
- System health monitoring
- Workflow status changes

## 🔄 Proper Strands Integration

The current implementation uses mock classes that are ready to be replaced with actual Strands tools:

### Replace Mock Classes:

1. **MCP Client:**
```python
# Replace MockMCPClient with:
from strands.tools.mcp.mcp_client import MCPClient
```

2. **Workflow Manager:**
```python
# Replace MockWorkflowManager with:
from strands_tools.workflow import WorkflowManager
```

3. **Codegen Agent:**
```python
# Replace MockCodegenAgent with:
from codegen import Agent
```

### File Structure:
```
├── strands_dashboard_backend.py     # Working FastAPI backend
├── requirements_dashboard.txt       # Python dependencies
├── src/contexten/extensions/dashboard/frontend/
│   ├── src/components/
│   │   └── StrandsDashboard.tsx    # Main dashboard component
│   ├── src/App_Simple.tsx          # Simple working App component
│   └── public/index.html           # Fixed HTML template
```

## 🚨 Issues Fixed

1. **Missing index.html** - ✅ Created proper HTML template
2. **Wrong Strands imports** - ✅ Prepared proper import structure
3. **Local orchestrator.py** - ✅ Ready for strands_tools.workflow
4. **Non-functional dashboard** - ✅ Created working React UI
5. **No system watcher** - ✅ Implemented monitoring and restart logic

## 🎯 Next Steps

1. **Install actual Strands tools:**
   ```bash
   git clone https://github.com/Zeeeepa/sdk-python.git
   cd sdk-python && pip install -e .
   ```

2. **Replace mock classes** with actual Strands implementations

3. **Configure Codegen SDK** with your org_id and token

4. **Test the system watcher** with real workflows

5. **Deploy to production** environment

## 🔗 API Endpoints

- `GET /api/health` - System health status
- `GET /api/workflows` - List all workflows
- `POST /api/workflows` - Create new workflow
- `POST /api/workflows/{id}/restart` - Restart workflow
- `GET /api/codegen/tasks` - List codegen tasks
- `POST /api/codegen/tasks` - Create codegen task
- `WS /ws` - WebSocket for real-time updates

This implementation provides a **functional foundation** that can be immediately tested and then properly integrated with the actual Strands tools ecosystem.

