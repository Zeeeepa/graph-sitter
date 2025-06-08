import React, { useEffect, useState } from 'react';
import { Box, Button, Container, Grid, Paper, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import SettingsIcon from '@mui/icons-material/Settings';

import ProjectCard from './ProjectCard';
import ProjectDialog from './ProjectDialog';
import ProjectSelectionDialog from './ProjectSelectionDialog';
import SettingsDialog from './SettingsDialog';
import RealTimeMetrics from './RealTimeMetrics';
import WorkflowMonitor from './WorkflowMonitor';
import TopBar from './TopBar';

import { useWebSocket } from '../hooks/useWebSocket';
import { useDashboardStore } from '../store/dashboardStore';
import { dashboardApi } from '../services/api';
import { Project, Settings, WorkflowEvent } from '../types';

const ConsolidatedDashboard: React.FC = () => {
  const theme = useTheme();
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [projectSelectionOpen, setProjectSelectionOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  const {
    projects,
    setProjects,
    updateProject,
    dashboardStats,
    setDashboardStats,
    connected,
  } = useDashboardStore();

  // WebSocket integration
  const { subscribeToProject, unsubscribeFromProject } = useWebSocket({
    onProjectUpdate: (projectId, updateType, data) => {
      if (updateType === 'status') {
        updateProject(projectId, { status: data.status });
      } else if (updateType === 'progress') {
        updateProject(projectId, { progress: data.progress });
      } else if (updateType === 'flow') {
        updateProject(projectId, {
          flowEnabled: data.enabled,
          flowStatus: data.status
        });
      }
    },
    onWorkflowEvent: (projectId, eventType, data) => {
      // Handle workflow events
      if (eventType === 'task_completed') {
        updateProject(projectId, {
          progress: data.progress
        });
      }
    },
    onMetricsUpdate: (projectId, metrics) => {
      updateProject(projectId, { metrics });
      // Update dashboard stats if available
      if (metrics.dashboard) {
        setDashboardStats(metrics.dashboard);
      }
    }
  });

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load projects
        const projectsData = await dashboardApi.getProjects();
        setProjects(projectsData);

        // Load stats
        const stats = await dashboardApi.getDashboardStats();
        setDashboardStats(stats);

        // Subscribe to project updates
        projectsData.forEach(project => {
          subscribeToProject(project.id);
        });
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      }
    };

    loadData();

    return () => {
      // Unsubscribe from project updates
      projects.forEach(project => {
        unsubscribeFromProject(project.id);
      });
    };
  }, []);

  const handleProjectPin = async (projectName: string) => {
    try {
      await dashboardApi.pinProject({ projectName });
      const projectsData = await dashboardApi.getProjects();
      setProjects(projectsData);
    } catch (error) {
      console.error('Failed to pin project:', error);
    }
  };

  const handleProjectClick = (project: Project) => {
    setSelectedProject(project);
    setProjectDialogOpen(true);
  };

  const handleProjectSave = async (project: Project) => {
    try {
      if (project.id) {
        await dashboardApi.updateProjectSettings(project.id, {
          requirements: project.requirements,
          flowEnabled: project.flowEnabled
        });
        updateProject(project.id, project);
      }
      setProjectDialogOpen(false);
    } catch (error) {
      console.error('Failed to save project:', error);
    }
  };

  const handleSettingsSave = async (settings: Settings) => {
    try {
      await dashboardApi.updateEnvironmentVariables(settings);
      setSettingsOpen(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleFlowToggle = async (projectId: string, enabled: boolean) => {
    try {
      if (enabled) {
        await dashboardApi.startWorkflow(projectId);
      } else {
        await dashboardApi.stopWorkflow(projectId);
      }
      updateProject(projectId, { flowEnabled: enabled });
    } catch (error) {
      console.error('Failed to toggle flow:', error);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <TopBar
        onProjectPin={handleProjectPin}
        onSettingsOpen={() => setSettingsOpen(true)}
      />

      <Container maxWidth="xl" sx={{ flexGrow: 1, py: 3 }}>
        <Grid container spacing={3}>
          {/* Real-time metrics */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <RealTimeMetrics
                projects={projects}
                metrics={dashboardStats}
              />
            </Paper>
          </Grid>

          {/* Pinned projects */}
          <Grid item xs={12}>
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">Pinned Projects</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setProjectSelectionOpen(true)}
              >
                Pin Project
              </Button>
            </Box>

            <Grid container spacing={2}>
              {projects.map(project => (
                <Grid item xs={12} sm={6} md={4} key={project.id}>
                  <ProjectCard
                    project={project}
                    onClick={() => handleProjectClick(project)}
                    onFlowToggle={handleFlowToggle}
                  />
                </Grid>
              ))}
            </Grid>
          </Grid>

          {/* Workflow monitor */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <WorkflowMonitor
                projects={projects}
              />
            </Paper>
          </Grid>
        </Grid>
      </Container>

      {/* Dialogs */}
      <ProjectDialog
        open={projectDialogOpen}
        project={selectedProject}
        onClose={() => setProjectDialogOpen(false)}
        onSave={handleProjectSave}
      />

      <ProjectSelectionDialog
        open={projectSelectionOpen}
        onClose={() => setProjectSelectionOpen(false)}
        onProjectSelect={handleProjectPin}
      />

      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSave={handleSettingsSave}
      />
    </Box>
  );
};

export default ConsolidatedDashboard;

