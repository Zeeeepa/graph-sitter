import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Container,
  Chip
} from '@mui/material';
import { useQuery } from 'react-query';
import ProjectCard from './ProjectCard';
import RealTimeMetrics from './RealTimeMetrics';
import WorkflowMonitor from './WorkflowMonitor';
import { useDashboardStore } from '../store/dashboardStore';
import { dashboardApi, DashboardStats } from '../api/dashboardApi';
import { Project as DashboardProject } from '../types/dashboard';
import { Project as BaseProject } from '../types/index';

const Dashboard: React.FC = () => {
  const { projects, setProjects } = useDashboardStore();

  // Fetch projects
  const { data: projectsData, isLoading: projectsLoading, error: projectsError } = useQuery(
    'projects',
    dashboardApi.getProjects,
    {
      onSuccess: (data: BaseProject[]) => {
        setProjects(data.map(convertToDashboardProject));
      },
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>(
    'dashboard-stats',
    dashboardApi.getStats,
    {
      refetchInterval: 60000, // Refresh every minute
    }
  );

  const handlePin = async (projectId: string) => {
    try {
      await dashboardApi.pinProject({ projectId });
      // Refresh projects
      window.location.reload();
    } catch (error) {
      console.error('Failed to pin project:', error);
    }
  };

  const handleUnpin = async (projectId: string) => {
    try {
      await dashboardApi.unpinProject({ projectId });
      // Refresh projects
      window.location.reload();
    } catch (error) {
      console.error('Failed to unpin project:', error);
    }
  };

  function convertToDashboardProject(project: BaseProject): DashboardProject {
    return {
      id: project.id,
      name: project.name,
      description: project.description || '',
      repository: project.url,
      status: project.status === 'active' ? 'active' : 
             project.status === 'error' ? 'error' : 'paused',
      progress: 0, // Default value
      flowEnabled: false,
      flowStatus: 'stopped',
      lastActivity: new Date(project.updated_at),
    };
  }

  if (projectsLoading) {
    return (
      <Container maxWidth="xl">
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="400px"
        >
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (projectsError) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="error" gutterBottom>
            Failed to load dashboard data
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please try refreshing the page or contact support if the issue persists.
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Project Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor and manage your development projects
        </Typography>

        {/* Dashboard Stats */}
        {stats && (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
            <Chip
              label={`${stats.total_projects} Projects`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`${stats.active_workflows} Active Workflows`}
              color="success"
              variant="outlined"
            />
            <Chip
              label={`${stats.completed_tasks} Completed Tasks`}
              color="info"
              variant="outlined"
            />
            <Chip
              label={`${stats.pending_prs} Pending PRs`}
              color="warning"
              variant="outlined"
            />
            <Chip
              label={`${stats.quality_score}% Quality Score`}
              color={stats.quality_score >= 80 ? 'success' : 'warning'}
              variant="outlined"
            />
          </Box>
        )}
      </Box>

      {/* Projects Grid */}
      {!projects || projects.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            No projects found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Start by creating your first project or check your connection.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project: DashboardProject) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={project.id}>
              <ProjectCard
                project={project}
                onPin={handlePin}
                onUnpin={handleUnpin}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Real Time Metrics */}
      <RealTimeMetrics projects={projects.map(convertToDashboardProject) || []} />

      {/* Workflow Monitor */}
      <WorkflowMonitor projects={projects.map(convertToDashboardProject) || []} />

      {/* Footer Info */}
      <Box sx={{ mt: 6, py: 3, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Graph Sitter Dashboard - Real-time project monitoring and management
        </Typography>
      </Box>
    </Container>
  );
};

export default Dashboard;
