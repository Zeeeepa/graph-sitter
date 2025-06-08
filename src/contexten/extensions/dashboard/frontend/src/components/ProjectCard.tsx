import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  IconButton,
  Box,
  Chip,
  LinearProgress,
  Tooltip
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  GitHub as GitHubIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface ProjectCardProps {
  project: Project;
  onPin?: (projectId: string) => void;
  onUnpin?: (projectId: string) => void;
  onClick?: () => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onClick, onPin, onUnpin }) => {
  const handlePin = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onPin) {
      onPin(project.id);
    }
  };

  const handleUnpin = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onUnpin) {
      onUnpin(project.id);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'paused':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getFlowStatusColor = (status: string) => {
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

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        cursor: 'pointer',
        '&:hover': {
          boxShadow: 6
        }
      }}
      onClick={() => {
        if (onClick) {
          onClick();
        }
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" component="div" noWrap>
            {project.name}
          </Typography>
          <IconButton
            size="small"
            onClick={project.flowEnabled ? handleUnpin : handlePin}
          >
            {project.flowEnabled ? <StarIcon color="warning" /> : <StarBorderIcon />}
          </IconButton>
        </Box>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}
        >
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
            sx={{ height: 8, borderRadius: 2 }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          <Chip
            size="small"
            label={project.status}
            color={getStatusColor(project.status) as any}
          />
          <Chip
            size="small"
            label={project.flowStatus}
            color={getFlowStatusColor(project.flowStatus) as any}
          />
          {project.tags.map((tag) => (
            <Chip key={tag} size="small" label={tag} />
          ))}
        </Box>

        <Typography variant="caption" color="text.secondary">
          Last activity: {project.lastActivity.toLocaleString()}
        </Typography>
      </CardContent>

      <CardActions sx={{ justifyContent: 'space-between', px: 2, py: 1 }}>
        <Box>
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
          <Tooltip title="View on GitHub">
            <IconButton
              size="small"
              href={project.repository}
              target="_blank"
              onClick={(e) => e.stopPropagation()}
            >
              <GitHubIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Tooltip title="Project Settings">
          <IconButton size="small" onClick={(e) => e.stopPropagation()}>
            <SettingsIcon />
          </IconButton>
        </Tooltip>
      </CardActions>
    </Card>
  );
};

export default ProjectCard;
