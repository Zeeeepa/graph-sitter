import React from 'react';
import {
  Box,
  Grid,
  Typography,
  Container,
  Paper,
  Chip,
  CircularProgress,
} from '@mui/material';
import { useQuery } from 'react-query';

import ProjectCard from './ProjectCard';
import { dashboardApi } from '../services/api';
import { useDashboardStore } from '../store/dashboardStore';

const Dashboard: React.FC = () => {
  const { projects, setProjects } = useDashboardStore();

  // Fetch projects
  const { data: projectsData, isLoading, error } = useQuery(
    'projects',
    dashboardApi.getProjects,
    {
      onSuccess: (data: Project[]) => {
        setProjects(data);
      },
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  // Fetch dashboard stats
  const { data: stats } = useQuery(
    'dashboard-stats',
    dashboardApi.getDashboardStats,
    {
      refetchInterval: 60000, // Refresh every minute
    }
  );

  const handleFlowToggle = async (projectId: string, enabled: boolean) => {
    try {
      // TODO: Implement flow toggle API call
      console.log(`Toggle flow for project ${projectId}: ${enabled}`);
    } catch (error) {
      console.error('Failed to toggle flow:', error);
    }
  };

  const handlePin = async (projectId: string) => {
    try {
      await dashboardApi.pinProject(projectId);
      // Refresh projects
      window.location.reload();
    } catch (error) {
      console.error('Failed to pin project:', error);
    }
  };

  const handleUnpin = async (projectId: string) => {
    try {
      await dashboardApi.unpinProject(projectId);
      // Refresh projects
      window.location.reload();
    } catch (error) {
      console.error('Failed to unpin project:', error);
    }
  };

  if (isLoading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '60vh' 
        }}
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl">
      {/* Dashboard Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Project Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          Multi-layered workflow orchestration for your development projects
        </Typography>
        
        {/* Stats Overview */}
        {stats && (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
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
      {projects.length === 0 ? (
        <Paper 
          sx={{ 
            p: 6, 
            textAlign: 'center',
            background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
          }}
        >
          <Typography variant="h5" gutterBottom>
            No Projects Pinned
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Get started by pinning your first project from GitHub
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Click "Select Project To Pin" in the top bar to browse your repositories
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project: Project) => (
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

      {/* Footer Info */}
      <Box sx={{ mt: 6, py: 3, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Powered by Contexten • Multi-layered Workflow Orchestration
        </Typography>
      </Box>
    </Container>
  );
};

export default Dashboard;
