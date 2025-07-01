import React from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  Chip,
  Avatar,
  Divider
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface WorkflowMonitorProps {
  projects: Project[];
}

const WorkflowMonitor: React.FC<WorkflowMonitorProps> = ({ projects }) => {
  // Generate mock workflow events
  const generateWorkflowEvents = () => {
    const events: any[] = []; // Explicitly type the events array

    projects.forEach(project => {
      if (project.plan?.tasks) {
        project.plan.tasks.forEach(task => {
          events.push({
            id: `${project.id}-${task.id}`,
            projectName: project.name,
            taskTitle: task.title,
            status: task.status,
            assignee: task.assignee || 'AI Agent',
            timestamp: task.updatedAt,
            type: 'task'
          });
        });
      }
      
      // Add project-level events
      events.push({
        id: `${project.id}-status`,
        projectName: project.name,
        taskTitle: `Project ${project.status}`,
        status: project.status,
        assignee: 'System',
        timestamp: project.lastActivity,
        type: 'project'
      });
    });
    
    return events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()).slice(0, 10);
  };

  const events = generateWorkflowEvents();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'active':
        return <CheckIcon color="success" />;
      case 'in_progress':
        return <PlayIcon color="primary" />;
      case 'pending':
        return <ScheduleIcon color="action" />;
      default:
        return <ErrorIcon color="error" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'active':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'pending':
        return 'default';
      default:
        return 'error';
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h5" gutterBottom>
        Workflow Monitor
      </Typography>
      
      <Paper sx={{ maxHeight: 400, overflow: 'auto' }}>
        {events.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="text.secondary">
              No workflow events yet. Start by pinning a project and creating a plan!
            </Typography>
          </Box>
        ) : (
          <List>
            {events.map((event, index) => (
              <React.Fragment key={event.id}>
                <ListItem>
                  <ListItemIcon>
                    {getStatusIcon(event.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1">
                          {event.taskTitle}
                        </Typography>
                        <Chip 
                          label={event.status} 
                          size="small" 
                          color={getStatusColor(event.status) as any}
                        />
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          {event.projectName}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Avatar sx={{ width: 16, height: 16 }}>
                            <PersonIcon sx={{ fontSize: 12 }} />
                          </Avatar>
                          <Typography variant="caption" color="text.secondary">
                            {event.assignee}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            • {formatTimeAgo(event.timestamp)}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
                {index < events.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>
      
      {events.length > 0 && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
          <Chip 
            label="Live Updates Active" 
            color="success" 
            variant="outlined"
            sx={{ animation: 'pulse 2s infinite' }}
          />
        </Box>
      )}
    </Box>
  );
};

export default WorkflowMonitor;
