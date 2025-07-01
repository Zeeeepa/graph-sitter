import React, { useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Container,
  Box,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import { useQuery } from 'react-query';
import ProjectCard from './ProjectCard';
import RealTimeMetrics from './RealTimeMetrics';
import WorkflowMonitor from './WorkflowMonitor';
import { dashboardApi } from '../api/dashboardApi';
import { Project, DashboardStats } from '../types/dashboard';

const Dashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);

  // Fetch projects
  const { isLoading: projectsLoading, error: projectsError } = useQuery<Project[]>(
    'projects',
    dashboardApi.getProjects,
    {
      onSuccess: (data: Project[]) => {
        setProjects(data);
      },
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  // Fetch stats
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>(
    'stats',
    dashboardApi.getStats,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
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

  if (projectsLoading || statsLoading) {
    return (
      <Container maxWidth="xl">
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '60vh',
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
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Alert severity="error">
            Failed to load projects. Please try again later.
          </Alert>
        </Box>
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
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            label={`${stats?.total_projects || 0} Total Projects`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`${stats?.active_workflows || 0} Active Workflows`}
            color="success"
            variant="outlined"
          />
          <Chip
            label={`${stats?.completed_tasks || 0} Completed Tasks`}
            color="info"
            variant="outlined"
          />
          <Chip
            label={`${stats?.pending_prs || 0} Pending PRs`}
            color="warning"
            variant="outlined"
          />
          <Chip
            label={`Quality Score: ${stats?.quality_score || 0}%`}
            color="secondary"
            variant="outlined"
          />
        </Box>
      </Paper>

      {/* Projects Grid */}
      {projects.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No projects found
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project) => (
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
      <RealTimeMetrics projects={projects} />

      {/* Workflow Monitor */}
      <WorkflowMonitor projects={projects} />

      {/* Footer Info */}
      <Box sx={{ mt: 6, py: 3, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Last updated: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : 'Never'}
        </Typography>
      </Box>
    </Container>
  );
};

export default Dashboard;

