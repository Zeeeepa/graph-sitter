import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
import { mockProjects } from './api/mockData';
import DashboardAPI from './services/dashboardAPI';

const App: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [openSettings, setOpenSettings] = useState(false);
  const [openProjectDialog, setOpenProjectDialog] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workflowEvents, setWorkflowEvents] = useState<WorkflowEvent[]>([]);
  const [settings, setSettings] = useState<Settings>({
    githubToken: process.env.REACT_APP_GITHUB_TOKEN || '',
    linearToken: process.env.REACT_APP_LINEAR_TOKEN || '',
    codegenOrgId: process.env.REACT_APP_CODEGEN_ORG_ID || '',
    codegenToken: process.env.REACT_APP_CODEGEN_TOKEN || '',
    prefectToken: process.env.REACT_APP_PREFECT_TOKEN || '',
    controlFlowToken: process.env.REACT_APP_CONTROL_FLOW_TOKEN || '',
    agentFlowToken: process.env.REACT_APP_AGENT_FLOW_TOKEN || '',
    webhookBaseUrl: process.env.REACT_APP_WEBHOOK_BASE_URL || 'https://api.dashboard.example.com',
  });

  // Initialize API
  const api = useMemo(() => new DashboardAPI(settings), [settings]);

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

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const fetchedProjects = await api.getProjects();
      setProjects(fetchedProjects);
      setError(null);
    } catch (err) {
      setError('Failed to fetch projects');
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleWebSocketEvent = (event: WebSocketEvent) => {
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
    setOpenProjectDialog(false);
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

  const handleProjectPin = async (projectId: string) => {
    try {
      await api.pinProject({ projectId });
      setProjects(prev =>
        prev.map(p =>
          p.id === projectId
            ? { ...p, pinned: true }
            : p
        )
      );
    } catch (err) {
      console.error('Error pinning project:', err);
      // Show error notification
    }
  };

  const handleProjectUnpin = async (projectId: string) => {
    try {
      await api.unpinProject({ projectId });
      setProjects(prev =>
        prev.map(p =>
          p.id === projectId
            ? { ...p, pinned: false }
            : p
        )
      );
    } catch (err) {
      console.error('Error unpinning project:', err);
      // Show error notification
    }
  };

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project);
    setOpenProjectDialog(true);
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
                onSelect={() => handleProjectSelect(project)}
                onPin={() => handleProjectPin(project.id)}
                onUnpin={() => handleProjectUnpin(project.id)}
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
