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
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import {
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Info as InfoIcon,
  MoreVert as MoreVertIcon,
  GitHub as GitHubIcon,
  Timeline as TimelineIcon,
  Code as CodeIcon,
  BugReport as BugIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { Project, WorkflowEvent } from '../types/dashboard';
import { ProjectMetrics } from './ProjectMetrics';
import { WorkflowTimeline } from './WorkflowTimeline';

interface ProjectCardProps {
  project: Project;
  onSelect?: (project: Project) => void;
  onPin?: (projectId: string) => void;
  onUnpin?: (projectId: string) => void;
  onStartFlow?: (projectId: string) => void;
  onStopFlow?: (projectId: string) => void;
  workflowEvents?: WorkflowEvent[];
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onSelect,
  onPin,
  onUnpin,
  onStartFlow,
  onStopFlow,
  workflowEvents = [],
}) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [timelineOpen, setTimelineOpen] = React.useState(false);
  const [metricsOpen, setMetricsOpen] = React.useState(false);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setAnchorEl(null);
  };

  const handleTimelineClick = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setTimelineOpen(true);
    handleMenuClose(event);
  };

  const handleMetricsClick = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setMetricsOpen(true);
    handleMenuClose(event);
  };

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
    <>
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
            <Box>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  project.pinned ? onUnpin?.(project.id) : onPin?.(project.id);
                }}
              >
                {project.pinned ? <StarIcon color="primary" /> : <StarBorderIcon />}
              </IconButton>
              <IconButton
                size="small"
                onClick={handleMenuClick}
              >
                <MoreVertIcon />
              </IconButton>
            </Box>
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
                onClick={(e) => {
                  e.stopPropagation();
                  project.flowStatus === 'running' 
                    ? onStopFlow?.(project.id)
                    : onStartFlow?.(project.id);
                }}
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
              {project.metrics.issues && (
                <Typography variant="caption" color="text.secondary">
                  Issues: {project.metrics.issues}
                </Typography>
              )}
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

      {/* Project Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        onClick={(e) => e.stopPropagation()}
      >
        <MenuItem onClick={(e) => {
          e.stopPropagation();
          window.open(project.repository, '_blank');
          handleMenuClose(e);
        }}>
          <ListItemIcon>
            <GitHubIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Repository</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleTimelineClick}>
          <ListItemIcon>
            <TimelineIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Timeline</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMetricsClick}>
          <ListItemIcon>
            <AssessmentIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Metrics</ListItemText>
        </MenuItem>
        {project.flowEnabled && (
          <MenuItem onClick={(e) => {
            e.stopPropagation();
            project.flowStatus === 'running'
              ? onStopFlow?.(project.id)
              : onStartFlow?.(project.id);
            handleMenuClose(e);
          }}>
            <ListItemIcon>
              {project.flowStatus === 'running' ? <StopIcon fontSize="small" /> : <PlayIcon fontSize="small" />}
            </ListItemIcon>
            <ListItemText>{project.flowStatus === 'running' ? 'Stop Flow' : 'Start Flow'}</ListItemText>
          </MenuItem>
        )}
      </Menu>

      {/* Timeline Dialog */}
      <Dialog
        open={timelineOpen}
        onClose={() => setTimelineOpen(false)}
        maxWidth="md"
        fullWidth
        onClick={(e) => e.stopPropagation()}
      >
        <DialogTitle>Project Timeline - {project.name}</DialogTitle>
        <DialogContent>
          <WorkflowTimeline events={workflowEvents.filter(e => e.projectId === project.id)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTimelineOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Metrics Dialog */}
      <Dialog
        open={metricsOpen}
        onClose={() => setMetricsOpen(false)}
        maxWidth="md"
        fullWidth
        onClick={(e) => e.stopPropagation()}
      >
        <DialogTitle>Project Metrics - {project.name}</DialogTitle>
        <DialogContent>
          <ProjectMetrics project={project} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMetricsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ProjectCard;

