import React from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  Alert
} from '@mui/material';
import { useQuery } from 'react-query';
import ProjectCard from './ProjectCard';
import RealTimeMetrics from './RealTimeMetrics';
import WorkflowMonitor from './WorkflowMonitor';
import { useDashboardStore } from '../store/dashboardStore';
import { dashboardApi, DashboardStats } from '../api/dashboardApi';
import { Project as DashboardProject } from '../types/dashboard';
import { Project as BaseProject } from '../types/index';

// Type conversion function
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
    tags: [],
    metrics: {
      commits: 0,
      contributors: 0,
      openPRs: 0,
      closedPRs: 0,
      issues: 0,
      tests: 0,
      coverage: 0
    }
  };
}

const Dashboard: React.FC = () => {
  const { projects, setProjects } = useDashboardStore();

  const { isLoading: projectsLoading, error: projectsError } = useQuery(
    'projects',
    dashboardApi.getProjects,
    {
      onSuccess: (data: DashboardProject[]) => {
        setProjects(data);
      },
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>(
    'stats',
    dashboardApi.getStats,
    {
      refetchInterval: 30000
    }
  );

  const handlePin = async (projectId: string) => {
    try {
      // Pin project logic here
      console.log('Pinning project:', projectId);
    } catch (error) {
      console.error('Failed to pin project:', error);
    }
  };

  const handleUnpin = async (projectId: string) => {
    try {
      // Unpin project logic here
      console.log('Unpinning project:', projectId);
    } catch (error) {
      console.error('Failed to unpin project:', error);
    }
  };

  if (projectsLoading) {
    return (
      <Container maxWidth="xl">
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '60vh'
          }}
        >
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (projectsError) {
    return (
      <Container maxWidth="xl">
        <Alert severity="error">
          Error loading projects. Please try again later.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      {/* Stats Overview */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Dashboard Overview
        </Typography>
        {statsLoading ? (
          <CircularProgress size={20} />
        ) : stats ? (
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle1">Total Projects</Typography>
              <Typography variant="h4">{stats.total_projects}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle1">Active Projects</Typography>
              <Typography variant="h4">{stats.active_projects}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle1">Running Flows</Typography>
              <Typography variant="h4">{stats.running_flows}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="subtitle1">Quality Score</Typography>
              <Typography variant="h4">{stats.quality_score}%</Typography>
            </Grid>
          </Grid>
        ) : (
          <Alert severity="warning">No stats available</Alert>
        )}
      </Paper>

      {/* Projects Grid */}
      {!projects?.length ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No projects found
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
      <RealTimeMetrics projects={projects || []} />

      {/* Workflow Monitor */}
      <WorkflowMonitor projects={projects || []} />

      {/* Footer Info */}
      <Box sx={{ mt: 6, py: 3, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Last updated: {new Date().toLocaleString()}
        </Typography>
      </Box>
    </Container>
  );
};

export default Dashboard;
