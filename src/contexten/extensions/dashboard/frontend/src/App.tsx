import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  Container,
  Grid,
  Typography,
  Alert,
  CircularProgress
} from '@mui/material';
import TopBar from './components/TopBar';
import ProjectCard from './components/ProjectCard';
import ProjectDialog from './components/ProjectDialog';
import SettingsDialog from './components/SettingsDialog';
import RealTimeMetrics from './components/RealTimeMetrics';
import WorkflowMonitor from './components/WorkflowMonitor';
import { Project } from './types/dashboard';

// Create Material-UI theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
});

const App: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data for demonstration
  useEffect(() => {
    const loadMockData = () => {
      const mockProjects: Project[] = [
        {
          id: '1',
          name: 'AI Dashboard System',
          description: 'Complete dashboard for AI-powered development workflows',
          repository: 'https://github.com/Zeeeepa/graph-sitter',
          status: 'active',
          progress: 75,
          flowEnabled: true,
          flowStatus: 'running',
          lastActivity: new Date(),
          requirements: 'Build a comprehensive dashboard system with React and Material-UI',
          plan: {
            id: 'plan-1',
            projectId: '1',
            title: 'Dashboard Implementation Plan',
            description: 'Complete implementation of the dashboard system',
            tasks: [
              {
                id: 'task-1',
                title: 'Setup React Frontend',
                description: 'Initialize React app with Material-UI',
                status: 'completed',
                assignee: 'AI Agent',
                estimatedHours: 4,
                actualHours: 3,
                dependencies: [],
                createdAt: new Date(),
                updatedAt: new Date()
              },
              {
                id: 'task-2',
                title: 'Implement Dashboard Components',
                description: 'Create all necessary UI components',
                status: 'in_progress',
                assignee: 'AI Agent',
                estimatedHours: 8,
                actualHours: 6,
                dependencies: ['task-1'],
                createdAt: new Date(),
                updatedAt: new Date()
              }
            ],
            status: 'in_progress',
            createdAt: new Date(),
            updatedAt: new Date()
          }
        },
        {
          id: '2',
          name: 'Code Analysis Engine',
          description: 'Advanced code analysis and manipulation system',
          repository: 'https://github.com/Zeeeepa/graph-sitter',
          status: 'paused',
          progress: 45,
          flowEnabled: false,
          flowStatus: 'stopped',
          lastActivity: new Date(Date.now() - 86400000), // 1 day ago
          requirements: 'Implement graph-sitter based code analysis',
        },
        {
          id: '3',
          name: 'Workflow Orchestrator',
          description: 'Orchestration system for development workflows',
          repository: 'https://github.com/Zeeeepa/contexten',
          status: 'completed',
          progress: 100,
          flowEnabled: true,
          flowStatus: 'stopped',
          lastActivity: new Date(Date.now() - 172800000), // 2 days ago
          requirements: 'Create workflow orchestration with webhook integrations',
        }
      ];

      setProjects(mockProjects);
      setLoading(false);
    };

    // Simulate API call delay
    setTimeout(loadMockData, 1000);
  }, []);

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project);
    setProjectDialogOpen(true);
  };

  const handleProjectSave = (updatedProject: Project) => {
    setProjects(prev => 
      prev.map(p => p.id === updatedProject.id ? updatedProject : p)
    );
    setProjectDialogOpen(false);
    setSelectedProject(null);
  };

  const handleProjectPin = (projectName: string) => {
    // Mock project pinning
    const newProject: Project = {
      id: Date.now().toString(),
      name: projectName,
      description: `Pinned project: ${projectName}`,
      repository: `https://github.com/user/${projectName}`,
      status: 'active',
      progress: 0,
      flowEnabled: false,
      flowStatus: 'stopped',
      lastActivity: new Date(),
    };

    setProjects(prev => [...prev, newProject]);
  };

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="100vh"
          flexDirection="column"
        >
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Loading Dashboard...
          </Typography>
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'background.default' }}>
        <TopBar
          onProjectPin={handleProjectPin}
          onSettingsOpen={() => setSettingsDialogOpen(true)}
        />
        
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Real-time Metrics */}
          <Box sx={{ mb: 4 }}>
            <RealTimeMetrics projects={projects} />
          </Box>

          {/* Workflow Monitor */}
          <Box sx={{ mb: 4 }}>
            <WorkflowMonitor projects={projects} />
          </Box>

          {/* Projects Grid */}
          <Typography variant="h4" component="h1" gutterBottom>
            Pinned Projects
          </Typography>
          
          {projects.length === 0 ? (
            <Alert severity="info">
              No projects pinned yet. Click "Select Project To Pin" to get started!
            </Alert>
          ) : (
            <Grid container spacing={3}>
              {projects.map((project) => (
                <Grid item xs={12} sm={6} md={4} key={project.id}>
                  <ProjectCard
                    project={project}
                    onClick={() => handleProjectSelect(project)}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Container>

        {/* Project Dialog */}
        <ProjectDialog
          open={projectDialogOpen}
          project={selectedProject}
          onClose={() => {
            setProjectDialogOpen(false);
            setSelectedProject(null);
          }}
          onSave={handleProjectSave}
        />

        {/* Settings Dialog */}
        <SettingsDialog
          open={settingsDialogOpen}
          onClose={() => setSettingsDialogOpen(false)}
        />
      </Box>
    </ThemeProvider>
  );
};

export default App;

