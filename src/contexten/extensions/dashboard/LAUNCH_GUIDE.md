# 🚀 Contexten Dashboard Launch Guide

Quick guide to get the Contexten Dashboard up and running.

## 🎯 Quick Start

### Option 1: Automated Startup (Recommended)
```bash
cd src/contexten/extensions/dashboard
python start_dashboard.py
```

This will automatically:
- ✅ Check dependencies
- ✅ Install frontend packages
- ✅ Start backend on port 8000
- ✅ Start frontend on port 3001
- ✅ Display access URLs

### Option 2: Manual Startup

#### Backend (FastAPI)
```bash
cd src/contexten/extensions/dashboard
pip install -r requirements.txt
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend (React)
```bash
cd src/contexten/extensions/dashboard/frontend
npm install
PORT=3001 npm start
```

## 🌐 Access URLs

- **🎯 Dashboard UI**: http://localhost:3001
- **🔧 Backend API**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **🔍 API Redoc**: http://localhost:8000/redoc

## 🛠️ Prerequisites

### Required Software
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Git** (for development)

### Python Dependencies
Install with: `pip install -r requirements.txt`
- FastAPI
- Uvicorn
- WebSockets
- SQLAlchemy
- And more (see requirements.txt)

### Frontend Dependencies
Install with: `npm install` (in frontend directory)
- React 18
- TypeScript
- Material-UI
- Socket.io
- And more (see package.json)

## 🎨 Features

### Dashboard UI
- **Project Management**: Create, view, and manage projects
- **Real-time Updates**: WebSocket-powered live updates
- **Analysis Integration**: Connect with graph-sitter analysis tools
- **Workflow Orchestration**: Multi-layered task management
- **GitHub Integration**: Repository and PR management

### Backend API
- **RESTful API**: Full CRUD operations
- **WebSocket Support**: Real-time communication
- **Database Integration**: SQLAlchemy with async support
- **Authentication**: JWT-based auth system
- **File Upload**: Support for project files

## 🐛 Troubleshooting

### Frontend Issues
```bash
# Clear React cache
cd frontend
rm -rf node_modules/.cache
npm start

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Backend Issues
```bash
# Check if port 8000 is available
lsof -i :8000

# Install missing dependencies
pip install -r requirements.txt

# Run with debug mode
python -m uvicorn api:app --reload --log-level debug
```

### Port Conflicts
- Frontend default: 3001 (change with `PORT=3002 npm start`)
- Backend default: 8000 (change in uvicorn command)

## 📊 Development

### Project Structure
```
dashboard/
├── api.py              # FastAPI main application
├── database.py         # Database models and setup
├── websocket.py        # WebSocket handlers
├── start_dashboard.py  # Automated startup script
├── requirements.txt    # Python dependencies
└── frontend/           # React TypeScript app
    ├── src/
    ├── public/
    └── package.json
```

### Adding Features
1. **Backend**: Add endpoints in `api.py`
2. **Frontend**: Add components in `src/components/`
3. **Database**: Update models in `database.py`
4. **WebSocket**: Add handlers in `websocket.py`

## 🎉 Success!

Once running, you should see:
- ✅ Backend API responding at http://localhost:8000
- ✅ Frontend UI loading at http://localhost:3001
- ✅ WebSocket connections established
- ✅ Database initialized and ready

Happy coding! 🚀

