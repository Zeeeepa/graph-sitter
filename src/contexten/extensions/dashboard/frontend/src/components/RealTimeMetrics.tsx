import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  LinearProgress
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface RealTimeMetricsProps {
  projects: Project[];
}

const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({ projects }) => {
  // Calculate metrics from projects
  const totalCommits = projects.reduce((sum, project) => sum + (project.metrics?.commits || 0), 0);
  const totalPRs = projects.reduce((sum, project) => sum + (project.metrics?.prs || 0), 0);
  const averageProgress = projects.length > 0 
    ? projects.reduce((sum, project) => sum + project.progress, 0) / projects.length 
    : 0;

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
        Real-time Metrics
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TrendingUpIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Total Commits</Typography>
            </Box>
            <Typography variant="h4" color="primary">
              {totalCommits}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Across all projects
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <SpeedIcon color="success" sx={{ mr: 1 }} />
              <Typography variant="h6">Active PRs</Typography>
            </Box>
            <Typography variant="h4" color="success.main">
              {totalPRs}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Currently open
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <AssessmentIcon color="info" sx={{ mr: 1 }} />
              <Typography variant="h6">Average Progress</Typography>
            </Box>
            <Typography variant="h4" color="info.main">
              {Math.round(averageProgress)}%
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={averageProgress} 
              sx={{ mt: 1 }}
            />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default RealTimeMetrics;

