#!/bin/bash

# Strands Dashboard Startup Script
echo "🚀 Starting Strands Agent Dashboard..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements_dashboard.txt

# Set up environment variables (if not already set)
if [ -z "$CODEGEN_ORG_ID" ]; then
    echo "⚠️  CODEGEN_ORG_ID not set. Please set it with:"
    echo "   export CODEGEN_ORG_ID='your_org_id'"
fi

if [ -z "$CODEGEN_TOKEN" ]; then
    echo "⚠️  CODEGEN_TOKEN not set. Please set it with:"
    echo "   export CODEGEN_TOKEN='your_token'"
fi

# Start backend in background
echo "🔧 Starting backend server..."
python3 strands_dashboard_backend.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend started successfully on http://localhost:8000"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🎨 Starting React frontend..."
cd src/contexten/extensions/dashboard/frontend

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

# Use the simple App.tsx if it exists
if [ -f "src/App_Simple.tsx" ]; then
    echo "🔄 Using simplified App component..."
    cp src/App.tsx src/App_Original.tsx 2>/dev/null
    cp src/App_Simple.tsx src/App.tsx
fi

# Start React app
echo "🌐 Starting React app on http://localhost:3000..."
npm start &
FRONTEND_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down Strands Dashboard..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "✅ Strands Dashboard is starting up!"
echo "📊 Backend: http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait

