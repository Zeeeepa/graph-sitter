import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface WorkflowMonitorProps {
  projects: Project[];
}

const WorkflowMonitor: React.FC<WorkflowMonitorProps> = ({ projects }) => {
  // Filter projects by workflow status
  const runningWorkflows = projects.filter(p => p.flowEnabled && p.flowStatus === 'running');
  const stoppedWorkflows = projects.filter(p => p.flowEnabled && p.flowStatus === 'stopped');
  const completedWorkflows = projects.filter(p => p.flowEnabled && p.flowStatus === 'completed');

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <PlayIcon color="success" />;
      case 'stopped':
        return <PauseIcon color="warning" />;
      case 'completed':
        return <CheckIcon color="primary" />;
      default:
        return <ErrorIcon color="error" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'warning';
      case 'completed':
        return 'primary';
      default:
        return 'error';
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
        Workflow Monitor
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Running Workflows
            </Typography>
            <Chip 
              label={runningWorkflows.length} 
              color="success" 
              sx={{ mb: 2 }}
            />
            <List dense>
              {runningWorkflows.slice(0, 3).map((project) => (
                <ListItem key={project.id}>
                  <ListItemIcon>
                    {getStatusIcon(project.flowStatus)}
                  </ListItemIcon>
                  <ListItemText 
                    primary={project.name}
                    secondary={`Progress: ${project.progress}%`}
                  />
                </ListItem>
              ))}
              {runningWorkflows.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  No running workflows
                </Typography>
              )}
            </List>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Stopped Workflows
            </Typography>
            <Chip 
              label={stoppedWorkflows.length} 
              color="warning" 
              sx={{ mb: 2 }}
            />
            <List dense>
              {stoppedWorkflows.slice(0, 3).map((project) => (
                <ListItem key={project.id}>
                  <ListItemIcon>
                    {getStatusIcon(project.flowStatus)}
                  </ListItemIcon>
                  <ListItemText 
                    primary={project.name}
                    secondary={`Progress: ${project.progress}%`}
                  />
                </ListItem>
              ))}
              {stoppedWorkflows.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  No stopped workflows
                </Typography>
              )}
            </List>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Completed Workflows
            </Typography>
            <Chip 
              label={completedWorkflows.length} 
              color="primary" 
              sx={{ mb: 2 }}
            />
            <List dense>
              {completedWorkflows.slice(0, 3).map((project) => (
                <ListItem key={project.id}>
                  <ListItemIcon>
                    {getStatusIcon(project.flowStatus)}
                  </ListItemIcon>
                  <ListItemText 
                    primary={project.name}
                    secondary={`Progress: ${project.progress}%`}
                  />
                </ListItem>
              ))}
              {completedWorkflows.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  No completed workflows
                </Typography>
              )}
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default WorkflowMonitor;
