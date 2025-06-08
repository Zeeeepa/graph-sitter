import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  LinearProgress,
  Chip,
  Box,
  IconButton,
  Stack,
} from '@mui/material';
import {
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface ProjectCardProps {
  project: Project;
  onSelect?: (project: Project) => void;
  onPin?: (projectId: string) => void;
  onUnpin?: (projectId: string) => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onSelect,
  onPin,
  onUnpin,
}) => {
  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'default' => {
    switch (status) {
      case 'active':
        return 'success';
      case 'error':
        return 'error';
      case 'paused':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getFlowStatusColor = (status: string): 'success' | 'error' | 'warning' | 'default' => {
    switch (status) {
      case 'running':
        return 'success';
      case 'error':
        return 'error';
      case 'stopped':
        return 'warning';
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
        position: 'relative',
        cursor: onSelect ? 'pointer' : 'default',
        '&:hover': {
          boxShadow: 3,
        },
      }}
      onClick={() => onSelect?.(project)}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" component="div" gutterBottom>
            {project.name}
          </Typography>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              project.pinned ? onUnpin?.(project.id) : onPin?.(project.id);
            }}
          >
            {project.pinned ? <StarIcon color="primary" /> : <StarBorderIcon />}
          </IconButton>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {project.description}
        </Typography>

        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Chip
            size="small"
            label={project.status}
            color={getStatusColor(project.status)}
          />
          {project.flowEnabled && (
            <Chip
              size="small"
              label={project.flowStatus}
              color={getFlowStatusColor(project.flowStatus)}
              icon={project.flowStatus === 'running' ? <PlayIcon /> : <StopIcon />}
            />
          )}
        </Stack>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Progress
          </Typography>
          <LinearProgress
            variant="determinate"
            value={project.progress}
            sx={{ height: 8, borderRadius: 1 }}
          />
        </Box>

        <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 0.5 }}>
          {project.tags?.map((tag) => (
            <Chip key={tag} label={tag} size="small" />
          ))}
        </Stack>

        {project.metrics && (
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Commits: {project.metrics.commits}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              PRs: {project.metrics.prs}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Contributors: {project.metrics.contributors}
            </Typography>
          </Box>
        )}
      </CardContent>

      <CardActions sx={{ justifyContent: 'flex-end' }}>
        <IconButton size="small" onClick={(e) => {
          e.stopPropagation();
          onSelect?.(project);
        }}>
          <InfoIcon />
        </IconButton>
      </CardActions>
    </Card>
  );
};

export default ProjectCard;

