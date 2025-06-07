import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  // LinearProgress removed as it's unused
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  // ErrorIcon removed as it's unused
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface RealTimeMetricsProps {
  projects: Project[];
}

const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({ projects }) => {
  const activeProjects = projects.filter(p => p.status === 'active').length;
  const completedProjects = projects.filter(p => p.status === 'completed').length;
  const runningFlows = projects.filter(p => p.flowEnabled && p.flowStatus === 'running').length;
  const averageProgress = projects.length > 0 
    ? Math.round(projects.reduce((sum, p) => sum + p.progress, 0) / projects.length)
    : 0;

  const metrics = [
    {
      title: 'Active Projects',
      value: activeProjects,
      icon: <TrendingUpIcon />,
      color: 'primary',
      description: 'Currently in development'
    },
    {
      title: 'Running Flows',
      value: runningFlows,
      icon: <SpeedIcon />,
      color: 'success',
      description: 'Automated workflows active'
    },
    {
      title: 'Completed',
      value: completedProjects,
      icon: <CheckCircleIcon />,
      color: 'info',
      description: 'Successfully finished'
    },
    {
      title: 'Avg Progress',
      value: `${averageProgress}%`,
      icon: <TrendingUpIcon />,
      color: 'warning',
      description: 'Overall completion rate'
    }
  ];

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h5" gutterBottom>
        Real-time Metrics
      </Typography>
      
      <Grid container spacing={3}>
        {metrics.map((metric, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card 
              sx={{ 
                p: 2, 
                display: 'flex', 
                flexDirection: 'column',
                height: 120,
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box 
                    sx={{ 
                      color: `${metric.color}.main`,
                      mr: 1,
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    {metric.icon}
                  </Box>
                  <Typography variant="h6" component="div">
                    {metric.value}
                  </Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {metric.title}
                </Typography>
                
                <Typography variant="caption" color="text.secondary">
                  {metric.description}
                </Typography>
                
                {/* Animated background effect */}
                <Box
                  sx={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: 4,
                    background: `linear-gradient(90deg, transparent, ${metric.color === 'primary' ? '#1976d2' : 
                      metric.color === 'success' ? '#2e7d32' :
                      metric.color === 'info' ? '#0288d1' : '#ed6c02'}20)`,
                    animation: 'pulse 2s infinite'
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      {projects.length > 0 && (
        <Card sx={{ p: 2, mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Health
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip 
                label="All Systems Operational" 
                color="success" 
                icon={<CheckCircleIcon />}
              />
              <Chip 
                label={`${projects.length} Projects Monitored`} 
                variant="outlined"
              />
              <Chip 
                label="Real-time Updates Active" 
                color="info" 
                variant="outlined"
              />
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default RealTimeMetrics;
