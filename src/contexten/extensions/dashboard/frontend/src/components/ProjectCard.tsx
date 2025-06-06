import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  IconButton,
  Switch,
  FormControlLabel,
  LinearProgress,
  Menu,
  MenuItem,
  Divider,
  Avatar,
  Tooltip,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  GitHub as GitHubIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  BugReport as BugReportIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';

import { Project } from '../types';
import { useDashboardStore } from '../store/dashboardStore';

interface ProjectCardProps {
  project: Project;
  onFlowToggle: (projectId: string, enabled: boolean) => void;
  onRemovePin: (projectId: string) => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onFlowToggle,
  onRemovePin,
}) => {
  const navigate = useNavigate();
  const { setSelectedProject } = useDashboardStore();
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleCardClick = () => {
    setSelectedProject(project);
    navigate(`/project/${project.id}`);
  };

  const handleFlowToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    event.stopPropagation();
    onFlowToggle(project.id, event.target.checked);
  };

  const handleRemovePin = () => {
    handleMenuClose();
    onRemovePin(project.id);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getLanguageColor = (language: string) => {
    const colors: Record<string, string> = {
      'TypeScript': '#3178c6',
      'JavaScript': '#f7df1e',
      'Python': '#3776ab',
      'Java': '#ed8b00',
      'Go': '#00add8',
      'Rust': '#000000',
      'C++': '#00599c',
    };
    return colors[language] || '#666666';
  };

  // Mock data for demonstration
  const mockStats = {
    activePRs: Math.floor(Math.random() * 5) + 1,
    openIssues: Math.floor(Math.random() * 10) + 2,
    workflowProgress: Math.floor(Math.random() * 100),
    lastActivity: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
    flowEnabled: Math.random() > 0.5,
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
        },
        border: '1px solid',
        borderColor: 'divider',
      }}
      onClick={handleCardClick}
    >
      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography variant="h6" component="h2" noWrap sx={{ fontWeight: 600 }}>
              {project.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap>
              {project.full_name}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              size="small"
              label={project.status}
              color={getStatusColor(project.status) as any}
              variant="outlined"
            />
            <IconButton size="small" onClick={handleMenuOpen}>
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Description */}
        {project.description && (
          <Typography 
            variant="body2" 
            color="text.secondary" 
            sx={{ 
              mb: 2,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {project.description}
          </Typography>
        )}

        {/* Language and Stats */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          {project.language && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: getLanguageColor(project.language),
                }}
              />
              <Typography variant="caption" color="text.secondary">
                {project.language}
              </Typography>
            </Box>
          )}
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Active PRs">
              <Chip
                size="small"
                icon={<GitHubIcon />}
                label={mockStats.activePRs}
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            </Tooltip>
            
            <Tooltip title="Open Issues">
              <Chip
                size="small"
                icon={<BugReportIcon />}
                label={mockStats.openIssues}
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            </Tooltip>
          </Box>
        </Box>

        {/* Workflow Progress */}
        {mockStats.workflowProgress > 0 && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                Workflow Progress
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {mockStats.workflowProgress}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={mockStats.workflowProgress} 
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>
        )}

        {/* Event List Preview */}
        <Box sx={{ mb: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
            Recent Activity
          </Typography>
          <Box sx={{ mt: 0.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <CheckCircleIcon sx={{ fontSize: 14, color: 'success.main' }} />
              <Typography variant="caption" color="text.secondary">
                PR #42 merged successfully
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <ScheduleIcon sx={{ fontSize: 14, color: 'warning.main' }} />
              <Typography variant="caption" color="text.secondary">
                Quality gate pending review
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TimelineIcon sx={{ fontSize: 14, color: 'info.main' }} />
              <Typography variant="caption" color="text.secondary">
                Workflow started 2h ago
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Last Activity */}
        <Typography variant="caption" color="text.secondary">
          Last activity: {format(mockStats.lastActivity, 'MMM d, HH:mm')}
        </Typography>
      </CardContent>

      <Divider />

      {/* Actions */}
      <CardActions sx={{ justifyContent: 'space-between', px: 2, py: 1.5 }}>
        <FormControlLabel
          control={
            <Switch
              size="small"
              checked={mockStats.flowEnabled}
              onChange={handleFlowToggle}
              onClick={(e) => e.stopPropagation()}
            />
          }
          label={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {mockStats.flowEnabled ? <PlayIcon sx={{ fontSize: 16 }} /> : <PauseIcon sx={{ fontSize: 16 }} />}
              <Typography variant="caption">
                Flow {mockStats.flowEnabled ? 'On' : 'Off'}
              </Typography>
            </Box>
          }
          sx={{ margin: 0 }}
        />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            Health: 
          </Typography>
          <Chip
            size="small"
            label="85%"
            color="success"
            variant="outlined"
            sx={{ fontSize: '0.7rem', height: 18 }}
          />
        </Box>
      </CardActions>

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        onClick={(e) => e.stopPropagation()}
      >
        <MenuItem onClick={handleMenuClose}>
          <SettingsIcon sx={{ mr: 1, fontSize: 18 }} />
          Project Settings
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <TimelineIcon sx={{ mr: 1, fontSize: 18 }} />
          View Workflows
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <GitHubIcon sx={{ mr: 1, fontSize: 18 }} />
          Open in GitHub
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleRemovePin} sx={{ color: 'error.main' }}>
          Remove Pin
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default ProjectCard;

