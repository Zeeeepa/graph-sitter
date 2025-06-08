import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  IconButton,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { Project, Settings, Task, WorkflowEvent } from './types/dashboard';
import ProjectCard from './components/ProjectCard';
import ProjectDialog from './components/ProjectDialog';
import SettingsDialog from './components/SettingsDialog';
import TaskManagement from './components/TaskManagement';
import WorkflowControl from './components/WorkflowControl';
import RealTimeMetrics from './components/RealTimeMetrics';
import websocketService from './services/websocketService';

// Mock data for development
const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Core Engine',
    description: 'Main processing engine',
    status: 'active',
    repository: 'https://github.com/example/core',
    progress: 75,
    flowEnabled: true,
    flowStatus: 'running',
    lastActivity: new Date(),
    tags: ['core', 'typescript'],
    metrics: {
      commits: 156,
      prs: 23,
      contributors: 8,
      issues: 45
    }
  },
  {
    id: '2',
    name: 'Dashboard UI',
    description: 'React dashboard interface',
    status: 'active',
    repository: 'https://github.com/example/dashboard',
    progress: 60,
    flowEnabled: false,
    flowStatus: 'stopped',
    lastActivity: new Date(),
    tags: ['frontend', 'react'],
    metrics: {
      commits: 89,
      prs: 12,
      contributors: 5,
      issues: 28
    }
  }
];

const App: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [openProjectDialog, setOpenProjectDialog] = useState(false);
  const [openSettings, setOpenSettings] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workflowEvents, setWorkflowEvents] = useState<WorkflowEvent[]>([]);

  const [settings, setSettings] = useState<Settings>({
    githubToken: '',
    linearToken: '',
    codegenOrgId: '',
    codegenToken: '',
    autoStartFlows: false,
    enableNotifications: true,
    enableAnalytics: true,
  });

  useEffect(() => {
    // Load initial data
    loadMockData();

    // Setup WebSocket connection
    websocketService.connect();
    const unsubscribe = websocketService.addListener((event) => {
      handleWebSocketEvent(event);
    });

    return () => {
      unsubscribe();
      websocketService.disconnect();
    };
  }, []);

  const loadMockData = () => {
    setLoading(true);
    try {
      setProjects(mockProjects);
      setLoading(false);
    } catch (err) {
      setError('Failed to load projects');
      setLoading(false);
    }
  };

  const handleWebSocketEvent = (event: any) => {
    switch (event.type) {
      case 'project_updated':
        setProjects(prev => 
          prev.map(p => p.id === event.payload.id ? { ...p, ...event.payload } : p)
        );
        break;
      case 'workflow_event':
        setWorkflowEvents(prev => [event.payload, ...prev].slice(0, 50));
        break;
      case 'metrics_updated':
        // Handle metrics update
        break;
    }
  };

  const handleCreateProject = () => {
    setSelectedProject(null);
    setOpenProjectDialog(true);
  };

  const handleSaveProject = (project: Project) => {
    if (project.id && projects.some(p => p.id === project.id)) {
      setProjects(prev =>
        prev.map(p => p.id === project.id ? project : p)
      );
    } else {
      setProjects(prev => [...prev, project]);
    }
  };

  const handleTaskUpdate = (projectId: string, task: Task) => {
    setProjects(prev =>
      prev.map(p => {
        if (p.id === projectId && p.plan) {
          return {
            ...p,
            plan: {
              ...p.plan,
              tasks: p.plan.tasks.map(t => t.id === task.id ? task : t),
            },
          };
        }
        return p;
      })
    );
  };

  const handleTaskCreate = (projectId: string, task: Partial<Task>) => {
    setProjects(prev =>
      prev.map(p => {
        if (p.id === projectId && p.plan) {
          return {
            ...p,
            plan: {
              ...p.plan,
              tasks: [...p.plan.tasks, task as Task],
            },
          };
        }
        return p;
      })
    );
  };

  const handleTaskDelete = (projectId: string, taskId: string) => {
    setProjects(prev =>
      prev.map(p => {
        if (p.id === projectId && p.plan) {
          return {
            ...p,
            plan: {
              ...p.plan,
              tasks: p.plan.tasks.filter(t => t.id !== taskId),
            },
          };
        }
        return p;
      })
    );
  };

  const handleStartFlow = async (projectId: string) => {
    setProjects(prev =>
      prev.map(p =>
        p.id === projectId
          ? { ...p, flowStatus: 'running', flowEnabled: true }
          : p
      )
    );
  };

  const handleStopFlow = async (projectId: string) => {
    setProjects(prev =>
      prev.map(p =>
        p.id === projectId
          ? { ...p, flowStatus: 'stopped', flowEnabled: false }
          : p
      )
    );
  };

  const handleRefreshStatus = async (projectId: string) => {
    // In a real app, this would fetch the latest status from the server
    console.log('Refreshing status for project:', projectId);
  };

  const handleDialogClose = () => {
    setSelectedProject(null);
    setOpenProjectDialog(false);
  };

  const handleSettingsSave = (newSettings: Settings) => {
    setSettings(newSettings);
    setOpenSettings(false);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1">
            Project Dashboard
          </Typography>
          <Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateProject}
              sx={{ mr: 2 }}
            >
              New Project
            </Button>
            <IconButton onClick={() => setOpenSettings(true)}>
              <SettingsIcon />
            </IconButton>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Real Time Metrics */}
        <RealTimeMetrics projects={projects} />

        {/* Project Grid */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {projects.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <ProjectCard
                project={project}
                onPin={(projectId) => console.log('Pin project:', projectId)}
                onUnpin={(projectId) => console.log('Unpin project:', projectId)}
              />
            </Grid>
          ))}
        </Grid>

        {/* Selected Project Details */}
        {selectedProject && (
          <>
            <Typography variant="h5" gutterBottom>
              {selectedProject.name} Details
            </Typography>

            {/* Task Management */}
            <TaskManagement
              project={selectedProject}
              onTaskUpdate={handleTaskUpdate}
              onTaskCreate={handleTaskCreate}
              onTaskDelete={handleTaskDelete}
            />

            {/* Workflow Control */}
            <WorkflowControl
              project={selectedProject}
              events={workflowEvents.filter(e => e.projectId === selectedProject.id)}
              onStartFlow={handleStartFlow}
              onStopFlow={handleStopFlow}
              onRefreshStatus={handleRefreshStatus}
            />
          </>
        )}

        {/* Dialogs */}
        <ProjectDialog
          open={openProjectDialog}
          project={selectedProject}
          onClose={handleDialogClose}
          onSave={handleSaveProject}
        />

        <SettingsDialog
          open={openSettings}
          settings={settings}
          onClose={() => setOpenSettings(false)}
          onSave={handleSettingsSave}
        />
      </Box>
    </Container>
  );
};

export default App;
