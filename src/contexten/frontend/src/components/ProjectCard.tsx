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
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  GitHub as GitHubIcon,
  Timeline as TimelineIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Settings as SettingsIcon,
  BugReport as BugIcon,
  People as PeopleIcon,
  Commit as CommitIcon,
  MergeType as PRIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface ProjectCardProps {
  project: Project;
  onPin?: (projectId: string) => void;
  onUnpin?: (projectId: string) => void;
  onSelect?: (project: Project) => void;
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

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onPin, onUnpin, onSelect }) => {
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

  const handleCardClick = () => {
    if (onSelect) {
      onSelect(project);
    }
  };

  return (
    <Card 
      sx={{ cursor: onSelect ? 'pointer' : 'default' }}
      onClick={handleCardClick}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" component="div">
            {project.name}
          </Typography>
          <IconButton 
            onClick={project.flowEnabled ? handleUnpin : handlePin} 
            size="small"
            color={project.flowEnabled ? 'primary' : 'default'}
          >
            {project.flowEnabled ? <StarIcon /> : <StarBorderIcon />}
          </IconButton>
        </Box>

        {/* Description */}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {project.description}
        </Typography>

        {/* Progress */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Progress
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={project.progress} 
            sx={{ mb: 1 }}
            color={project.progress >= 80 ? 'success' : project.progress >= 40 ? 'primary' : 'warning'}
          />
          <Typography variant="body2" color="text.secondary">
            {`${Math.round(project.progress)}%`}
          </Typography>
        </Box>

        {/* Status and Tags */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Chip
            icon={project.flowStatus === 'running' ? <PlayIcon /> : <PauseIcon />}
            label={project.flowStatus}
            size="small"
            color={getFlowStatusColor(project.flowStatus)}
          />
          {project.tags.map((tag: string) => (
            <Chip 
              key={tag} 
              size="small" 
              label={tag}
              variant="outlined"
            />
          ))}
        </Box>

        {/* Metrics */}
        {project.metrics && (
          <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
            <Tooltip title="Commits">
              <Chip
                icon={<CommitIcon />}
                label={project.metrics.commits}
                size="small"
                variant="outlined"
              />
            </Tooltip>
            <Tooltip title="Pull Requests">
              <Chip
                icon={<PRIcon />}
                label={project.metrics.prs}
                size="small"
                variant="outlined"
              />
            </Tooltip>
            <Tooltip title="Contributors">
              <Chip
                icon={<PeopleIcon />}
                label={project.metrics.contributors}
                size="small"
                variant="outlined"
              />
            </Tooltip>
            {project.metrics.issues && (
              <Tooltip title="Issues">
                <Chip
                  icon={<BugIcon />}
                  label={project.metrics.issues}
                  size="small"
                  variant="outlined"
                />
              </Tooltip>
            )}
          </Box>
        )}

        {/* Action Icons */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="View Repository">
            <IconButton size="small" href={project.repository} target="_blank">
              <GitHubIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="View Timeline">
            <IconButton size="small">
              <TimelineIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton size="small">
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </CardContent>

      {/* Card Actions */}
      <CardActions>
        <Button 
          size="small" 
          startIcon={<GitHubIcon />} 
          href={project.repository} 
          target="_blank"
        >
          Repository
        </Button>
        <Button 
          size="small" 
          startIcon={<TimelineIcon />}
        >
          Timeline
        </Button>
      </CardActions>
    </Card>
  );
};

export default ProjectCard;
