import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  LinearProgress,
  Box,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  GitHub as GitHubIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface ProjectCardProps {
  project: Project;
  onClick?: () => void;
  onPin?: (projectId: string) => void;
  onUnpin?: (projectId: string) => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onClick, onPin, onUnpin }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'paused':
        return 'warning';
      case 'completed':
        return 'info';
      default:
        return 'default';
    }
  };

  const getFlowStatusColor = (flowStatus: string) => {
    switch (flowStatus) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Card 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        cursor: 'pointer',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 3
        },
        transition: 'all 0.2s ease-in-out'
      }}
      onClick={onClick}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" component="h2" gutterBottom>
            {project.name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip 
              label={project.status} 
              color={getStatusColor(project.status) as any}
              size="small"
            />
            {project.flowEnabled && (
              <Chip 
                label={project.flowStatus} 
                color={getFlowStatusColor(project.flowStatus) as any}
                size="small"
                variant="outlined"
              />
            )}
          </Box>
        </Box>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {project.description}
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Progress</Typography>
            <Typography variant="body2">{project.progress}%</Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={project.progress} 
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <GitHubIcon fontSize="small" color="action" />
          <Typography variant="body2" color="text.secondary" className="text-truncate">
            {project.repository}
          </Typography>
        </Box>
        
        <Typography variant="caption" color="text.secondary">
          Last activity: {project.lastActivity.toLocaleDateString()}
        </Typography>
      </CardContent>
      
      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={project.flowEnabled ? 'Pause Flow' : 'Start Flow'}>
            <IconButton 
              size="small" 
              color={project.flowEnabled ? 'warning' : 'success'}
              onClick={(e) => {
                e.stopPropagation();
                if (onClick) {
                  onClick();
                }
              }}
            >
              {project.flowEnabled ? <PauseIcon /> : <PlayIcon />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="View Timeline">
            <IconButton size="small" color="primary">
              <TimelineIcon />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Button
          variant="outlined"
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            if (onClick) {
              onClick();
            }
          }}
        >
          Manage
        </Button>
      </CardActions>
    </Card>
  );
};

export default ProjectCard;
