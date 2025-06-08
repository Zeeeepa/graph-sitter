/**
 * Main App component for AI-Powered CI/CD Automation Platform
 */
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, AppBar, Toolbar, Typography, Button, Alert, Snackbar } from '@mui/material';
import { GitHub, Dashboard, Settings, Logout } from '@mui/icons-material';

// Components
import ProjectDashboard from './components/ProjectDashboard';
import AgentStatusMonitor from './components/AgentStatusMonitor';
import WorkflowMonitor from './components/WorkflowMonitor';
import PlanCreator from './components/PlanCreator';
import GitHubAuth from './components/GitHubAuth';
import LoadingSpinner from './components/LoadingSpinner';

// Services
import { apiService } from './services/api';
import { useWebSocket } from './hooks/useWebSocket';

// Theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00d4aa',
    },
    secondary: {
      main: '#ff6b6b',
    },
    background: {
      default: '#0a0e27',
      paper: '#1a1f3a',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
  },
});

function App() {
  // State management
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  // WebSocket connection for real-time updates
  const { 
    isConnected, 
    lastMessage, 
    sendMessage,
    connectionStats 
  } = useWebSocket('ws://localhost:8000/ws/dashboard-client');

  // Initialize app
  useEffect(() => {
    initializeApp();
  }, []);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      handleWebSocketMessage(lastMessage);
    }
  }, [lastMessage]);

  const initializeApp = async () => {
    try {
      setLoading(true);
      
      // Check if user is already authenticated
      const token = localStorage.getItem('github_token');
      if (token) {
        await authenticateWithToken(token);
      }
    } catch (error) {
      console.error('App initialization error:', error);
      setError('Failed to initialize application');
    } finally {
      setLoading(false);
    }
  };

  const authenticateWithToken = async (token) => {
    try {
      // Validate token and get repositories
      const response = await apiService.authenticateGitHub(token);
      
      setIsAuthenticated(true);
      setProjects(response.repositories);
      setUser({ token });
      
      // Subscribe to project updates via WebSocket
      if (sendMessage) {
        sendMessage({
          type: 'subscribe_project',
          project_id: 'all'
        });
      }
      
      showNotification('Successfully authenticated with GitHub!', 'success');
    } catch (error) {
      console.error('Authentication error:', error);
      localStorage.removeItem('github_token');
      setError('GitHub authentication failed');
    }
  };

  const handleGitHubAuth = async (token) => {
    localStorage.setItem('github_token', token);
    await authenticateWithToken(token);
  };

  const handleLogout = () => {
    localStorage.removeItem('github_token');
    setIsAuthenticated(false);
    setUser(null);
    setProjects([]);
    setSelectedProject(null);
    showNotification('Logged out successfully', 'info');
  };

  const handleWebSocketMessage = (message) => {
    try {
      const data = JSON.parse(message.data);
      
      switch (data.type) {
        case 'agent_status_update':
          // Handle agent status updates
          showNotification(
            `Agent ${data.task_id}: ${data.status}`,
            data.status === 'completed' ? 'success' : 'info'
          );
          break;
          
        case 'workflow_update':
          // Handle workflow updates
          showNotification(
            `Workflow ${data.workflow_id}: ${data.status}`,
            data.status === 'completed' ? 'success' : 'info'
          );
          break;
          
        case 'code_analysis_update':
          // Handle code analysis updates
          showNotification(
            `Code analysis completed for ${data.project_id}`,
            'info'
          );
          break;
          
        case 'deployment_update':
          // Handle deployment updates
          showNotification(
            `Deployment ${data.deployment_id}: ${data.status}`,
            data.status === 'deployed' ? 'success' : 'info'
          );
          break;
          
        case 'system_notification':
          // Handle system notifications
          showNotification(data.message, data.severity);
          break;
          
        default:
          console.log('Unhandled WebSocket message:', data);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({ message, severity });
  };

  const handleCloseNotification = () => {
    setNotification(null);
  };

  const handleProjectSelect = (project) => {
    setSelectedProject(project);
    
    // Subscribe to specific project updates
    if (sendMessage) {
      sendMessage({
        type: 'subscribe_project',
        project_id: project.id
      });
    }
  };

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <LoadingSpinner message="Initializing AI-Powered CI/CD Platform..." />
      </ThemeProvider>
    );
  }

  if (!isAuthenticated) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <GitHubAuth onAuth={handleGitHubAuth} />
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          {/* App Bar */}
          <AppBar position="static" sx={{ background: 'rgba(26, 31, 58, 0.95)', backdropFilter: 'blur(10px)' }}>
            <Toolbar>
              <Dashboard sx={{ mr: 2 }} />
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                AI-Powered CI/CD Platform
              </Typography>
              
              {/* Connection Status */}
              <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: isConnected ? '#4caf50' : '#f44336',
                    mr: 1,
                  }}
                />
                <Typography variant="body2" color="textSecondary">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </Typography>
              </Box>
              
              <Button
                color="inherit"
                startIcon={<Logout />}
                onClick={handleLogout}
              >
                Logout
              </Button>
            </Toolbar>
          </AppBar>

          {/* Main Content */}
          <Box sx={{ p: 3 }}>
            <Routes>
              <Route
                path="/"
                element={
                  <ProjectDashboard
                    projects={projects}
                    selectedProject={selectedProject}
                    onProjectSelect={handleProjectSelect}
                    onProjectUpdate={setProjects}
                  />
                }
              />
              <Route
                path="/project/:projectId"
                element={
                  selectedProject ? (
                    <Box>
                      {/* Project Header */}
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="h4" gutterBottom>
                          {selectedProject.name}
                        </Typography>
                        <Typography variant="body1" color="textSecondary">
                          {selectedProject.description}
                        </Typography>
                      </Box>

                      {/* Agent Status Monitor */}
                      <AgentStatusMonitor
                        projectId={selectedProject.id}
                        sx={{ mb: 3 }}
                      />

                      {/* Plan Creator */}
                      <PlanCreator
                        project={selectedProject}
                        sx={{ mb: 3 }}
                      />

                      {/* Workflow Monitor */}
                      <WorkflowMonitor
                        projectId={selectedProject.id}
                      />
                    </Box>
                  ) : (
                    <Navigate to="/" replace />
                  )
                }
              />
            </Routes>
          </Box>

          {/* Error Display */}
          {error && (
            <Alert
              severity="error"
              onClose={() => setError(null)}
              sx={{
                position: 'fixed',
                bottom: 16,
                left: 16,
                right: 16,
                zIndex: 1000,
              }}
            >
              {error}
            </Alert>
          )}

          {/* Notifications */}
          <Snackbar
            open={!!notification}
            autoHideDuration={6000}
            onClose={handleCloseNotification}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          >
            {notification && (
              <Alert
                onClose={handleCloseNotification}
                severity={notification.severity}
                sx={{ width: '100%' }}
              >
                {notification.message}
              </Alert>
            )}
          </Snackbar>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;

