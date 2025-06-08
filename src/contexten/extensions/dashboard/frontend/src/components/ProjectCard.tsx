import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  Chip,
  LinearProgress,
  CardActions,
  Button,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  GitHub as GitHubIcon,
  Timeline as TimelineIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface ProjectCardProps {
  project: Project;
  onPin?: (projectId: string) => void;
  onUnpin?: (projectId: string) => void;
}

const getFlowStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
  switch (status) {
    case 'running':
      return 'success';
    case 'stopped':
      return 'warning';
    case 'error':
      return 'error';
    default:
      return 'default';
  }
};

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onPin, onUnpin }) => {
  const handlePin = () => {
    if (onPin) {
      onPin(project.id);
    }
  };

  const handleUnpin = () => {
    if (onUnpin) {
      onUnpin(project.id);
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" component="div">
            {project.name}
          </Typography>
          <IconButton onClick={project.flowEnabled ? handleUnpin : handlePin} size="small">
            {project.flowEnabled ? <StarIcon /> : <StarBorderIcon />}
          </IconButton>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {project.description}
        </Typography>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Progress
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={project.progress} 
            sx={{ mb: 1 }}
          />
          <Typography variant="body2" color="text.secondary">
            {`${Math.round(project.progress)}%`}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip
            icon={project.flowStatus === 'running' ? <PlayIcon /> : <PauseIcon />}
            label={project.flowStatus}
            size="small"
            color={getFlowStatusColor(project.flowStatus) as any}
          />
          {project.tags.map((tag: string) => (
            <Chip key={tag} size="small" label={tag} />
          ))}
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton size="small" href={project.repository} target="_blank">
            <GitHubIcon />
          </IconButton>
          <IconButton size="small">
            <TimelineIcon />
          </IconButton>
          <IconButton size="small">
            <SettingsIcon />
          </IconButton>
        </Box>
      </CardContent>

      <CardActions>
        <Button size="small" startIcon={<GitHubIcon />} href={project.repository} target="_blank">
          View Repository
        </Button>
        <Button size="small" startIcon={<TimelineIcon />}>
          View Timeline
        </Button>
      </CardActions>
    </Card>
  );
};

export default ProjectCard;

