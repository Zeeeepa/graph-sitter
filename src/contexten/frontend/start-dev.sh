#!/bin/bash

# Consolidated Strands Dashboard - Development Server Startup Script

echo "🚀 Starting Consolidated Strands Dashboard..."
echo "📍 Location: $(pwd)"
echo "🔧 Installing dependencies if needed..."

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

echo "🌐 Starting development server on port 3001..."
echo "🔗 Dashboard will be available at: http://localhost:3001"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the development server
npm start

