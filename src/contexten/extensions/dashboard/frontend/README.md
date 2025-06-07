# Consolidated Strands Dashboard

A React-based dashboard for managing AI-powered development workflows with real-time monitoring and project management capabilities.

## 🚀 Quick Start

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn

### Installation & Running

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env if you need to change default settings
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```
   
   Or use the convenience script:
   ```bash
   ./start-dev.sh
   ```

4. **Open your browser:**
   - The dashboard will be available at: `http://localhost:3001`
   - The app will automatically reload when you make changes

## 📁 Project Structure

```
src/
├── components/          # React components
│   ├── TopBar.tsx      # Navigation bar
│   ├── ProjectCard.tsx # Project display cards
│   ├── ProjectDialog.tsx # Project details modal
│   ├── RealTimeMetrics.tsx # Live metrics display
│   └── WorkflowMonitor.tsx # Workflow status monitor
├── types/              # TypeScript type definitions
├── services/           # API services
├── store/              # State management (Zustand)
├── hooks/              # Custom React hooks
├── App.tsx             # Main application component
└── index.tsx           # Application entry point
```

## 🛠 Available Scripts

- `npm start` - Start development server (port 3001)
- `npm build` - Build for production
- `npm test` - Run tests
- `npm run type-check` - TypeScript type checking
- `npm run lint` - ESLint code linting
- `npm run format` - Prettier code formatting

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
PORT=3001
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

### Backend Integration
The dashboard expects a backend API running on `http://localhost:8000` with the following endpoints:
- `/api/projects` - Project management
- `/api/workflows` - Workflow monitoring
- `/ws` - WebSocket for real-time updates

## 🎨 Features

- **Project Management**: Pin, monitor, and manage development projects
- **Real-time Metrics**: Live updates on project status and performance
- **Workflow Monitoring**: Track automated development workflows
- **Material-UI Design**: Modern, responsive interface
- **TypeScript**: Full type safety and IntelliSense support

## 🐛 Troubleshooting

### Port Already in Use
If port 3001 is busy, you can specify a different port:
```bash
PORT=3002 npm start
```

### Missing Dependencies
If you encounter module not found errors:
```bash
npm install
```

### TypeScript Errors
Run type checking to identify issues:
```bash
npm run type-check
```

## 📝 Development Notes

- The app uses Material-UI for consistent styling
- State management is handled by Zustand
- Real-time features use WebSocket connections
- The app is configured to proxy API requests to `localhost:8000`
