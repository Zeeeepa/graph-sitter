# Graph-Sitter Dashboard

A modern, dark-themed dashboard for the Graph-Sitter code analysis framework with real-time WebSocket updates and comprehensive extension support.

## 🚀 Features

- **Dark-Only Theme**: Beautiful, modern dark interface optimized for developer workflows
- **Real-time Updates**: WebSocket-powered live project status and flow monitoring
- **Extension Integration**: Seamless integration with Graph-Sitter analysis, visualization, and resolution extensions
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Connection Management**: Intelligent connection handling with automatic retry and fallback mechanisms
- **Project Management**: Pin/unpin projects, track progress, and monitor flow status

## 🏗️ Architecture

### Backend (FastAPI)
- **WebSocket Support**: Real-time communication for live updates
- **REST API**: Comprehensive endpoints for project management and statistics
- **Extension API**: Dynamic extension loading and capability discovery
- **Health Monitoring**: Built-in health checks and connection monitoring

### Frontend (React + TypeScript)
- **Modern React**: Hooks-based architecture with TypeScript
- **React Query**: Intelligent data fetching with caching and error handling
- **WebSocket Service**: Robust connection management with exponential backoff
- **Component Library**: Reusable, themed components following design system

### Extensions
- **Graph-Sitter Analysis**: Code complexity and dependency analysis
- **Graph-Sitter Visualize**: Interactive code visualization and graph generation
- **Graph-Sitter Resolve**: Symbol resolution and cross-reference analysis

## 🛠️ Development Setup

### Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **npm or yarn** (package manager)

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install fastapi uvicorn websockets
   ```

2. **Start the backend server**:
   ```bash
   python simple_backend.py
   ```
   
   The backend will start on `http://localhost:8000` with:
   - REST API endpoints at `/api/*`
   - WebSocket endpoint at `/ws`
   - Health check at `/health`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd src/contexten/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start the development server**:
   ```bash
   npm start
   # or
   yarn start
   ```
   
   The frontend will start on `http://localhost:3000`

### Full Development Workflow

1. **Start Backend** (Terminal 1):
   ```bash
   python simple_backend.py
   ```

2. **Start Frontend** (Terminal 2):
   ```bash
   cd src/contexten/frontend
   npm start
   ```

3. **Open Browser**:
   Navigate to `http://localhost:3000`

## 📡 API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/projects` | Get all projects |
| `GET` | `/api/projects/{id}` | Get specific project |
| `POST` | `/api/projects/{id}/pin` | Pin project to dashboard |
| `POST` | `/api/projects/{id}/unpin` | Unpin project from dashboard |
| `GET` | `/api/stats` | Get dashboard statistics |
| `GET` | `/api/extensions` | Get available extensions |
| `GET` | `/health` | Health check |

### WebSocket Events

| Event Type | Description |
|------------|-------------|
| `connection_established` | Initial connection confirmation |
| `project_status_update` | Periodic project status updates |
| `project_pinned` | Project pinned notification |
| `project_unpinned` | Project unpinned notification |

## 🎨 Theme System

The dashboard uses a comprehensive dark-only theme with CSS custom properties:

```css
:root {
  --bg-primary: #0d1117;      /* Main background */
  --bg-secondary: #161b22;    /* Card backgrounds */
  --bg-tertiary: #21262d;     /* Input backgrounds */
  --text-primary: #f0f6fc;    /* Primary text */
  --text-secondary: #8b949e;  /* Secondary text */
  --accent-primary: #238636;  /* Success/active states */
  --accent-secondary: #1f6feb; /* Links and buttons */
}
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

### Backend Configuration

The backend can be configured by modifying `simple_backend.py`:

```python
# CORS origins
allow_origins=["http://localhost:3001", "http://localhost:3000"]

# Server settings
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🧪 Testing

### Frontend Testing
```bash
cd src/contexten/frontend
npm test
```

### Backend Testing
```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest
```

## 🚀 Production Deployment

### Backend
```bash
# Install production dependencies
pip install gunicorn

# Run with gunicorn
gunicorn simple_backend:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
cd src/contexten/frontend
npm run build
```

## 🔍 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure backend is running on port 8000
   - Check firewall settings
   - Verify CORS configuration

2. **API Requests Failing**
   - Check backend logs for errors
   - Verify API endpoints are accessible
   - Check network connectivity

3. **Frontend Build Issues**
   - Clear node_modules and reinstall
   - Check Node.js version compatibility
   - Verify all dependencies are installed

### Debug Mode

Enable debug logging by setting:
```javascript
localStorage.setItem('debug', 'true');
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://reactjs.org/)
- Inspired by modern developer tools and GitHub's design system
- WebSocket implementation based on FastAPI WebSocket documentation

