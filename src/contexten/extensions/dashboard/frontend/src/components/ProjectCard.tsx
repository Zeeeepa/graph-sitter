import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  LinearProgress,
  IconButton,
  Tooltip,
  Avatar,
  Stack
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Settings as SettingsIcon,
  GitHub as GitHubIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface ProjectCardProps {
  project: Project;
  onOpenProject: (project: Project) => void;
  onToggleFlow: (projectId: string, enabled: boolean) => void;
  onOpenSettings: (project: Project) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onOpenProject,
  onToggleFlow,
  onOpenSettings
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'paused': return 'warning';
      case 'error': return 'error';
      case 'completed': return 'info';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckIcon fontSize="small" />;
      case 'paused': return <ScheduleIcon fontSize="small" />;
      case 'error': return <ErrorIcon fontSize="small" />;
      case 'completed': return <CheckIcon fontSize="small" />;
      default: return <ScheduleIcon fontSize="small" />;
    }
  };

  const progress = project.progress || 0;
  const flowEnabled = project.flowEnabled || false;

  return (
    <Card 
      elevation={2}
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          elevation: 4,
          transform: 'translateY(-2px)'
        }
      }}
    >
      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography 
              variant="h6" 
              component="h3" 
              sx={{ 
                fontWeight: 'bold',
                mb: 0.5,
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <Avatar sx={{ width: 24, height: 24, bgcolor: 'primary.main' }}>
                <GitHubIcon fontSize="small" />
              </Avatar>
              {project.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {project.description || 'No description available'}
            </Typography>
          </Box>
          
          <Tooltip title="Project Settings">
            <IconButton 
              size="small" 
              onClick={() => onOpenSettings(project)}
              sx={{ ml: 1 }}
            >
              <SettingsIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Status and Flow */}
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Chip
            icon={getStatusIcon(project.status)}
            label={project.status.charAt(0).toUpperCase() + project.status.slice(1)}
            color={getStatusColor(project.status) as any}
            size="small"
            variant="outlined"
          />
          <Chip
            label={flowEnabled ? 'Flow: ON' : 'Flow: OFF'}
            color={flowEnabled ? 'success' : 'default'}
            size="small"
            variant={flowEnabled ? 'filled' : 'outlined'}
          />
        </Stack>

        {/* Progress */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Progress
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {progress}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ 
              height: 8, 
              borderRadius: 4,
              backgroundColor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                borderRadius: 4
              }
            }}
          />
        </Box>

        {/* Repository Info */}
        {project.repository && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <GitHubIcon fontSize="small" color="action" />
            <Typography variant="caption" color="text.secondary">
              {project.repository}
            </Typography>
          </Box>
        )}

        {/* Last Activity */}
        {project.lastActivity && (
          <Typography variant="caption" color="text.secondary">
            Last activity: {new Date(project.lastActivity).toLocaleDateString()}
          </Typography>
        )}
      </CardContent>

      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Button
          variant="contained"
          startIcon={<TimelineIcon />}
          onClick={() => onOpenProject(project)}
          sx={{ textTransform: 'none' }}
        >
          View Details
        </Button>
        
        <Button
          variant={flowEnabled ? "outlined" : "contained"}
          color={flowEnabled ? "error" : "success"}
          startIcon={flowEnabled ? <PauseIcon /> : <PlayIcon />}
          onClick={() => onToggleFlow(project.id, !flowEnabled)}
          sx={{ textTransform: 'none' }}
        >
          {flowEnabled ? 'Stop Flow' : 'Start Flow'}
        </Button>
      </CardActions>
    </Card>
  );
};

