import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Menu,
  MenuItem,
  Chip,
  IconButton,
  Badge,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  PushPin as PinIcon,
  Notifications as NotificationsIcon,
  GitHub as GitHubIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';

import { useDashboardStore } from '../store/dashboardStore';
import { dashboardApi } from '../services/api';
import ProjectSelectionDialog from './ProjectSelectionDialog';

const TopBar: React.FC = () => {
  const { setSettingsOpen, user } = useDashboardStore();
  const [projectMenuAnchor, setProjectMenuAnchor] = useState<null | HTMLElement>(null);
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [notificationMenuAnchor, setNotificationMenuAnchor] = useState<null | HTMLElement>(null);

  // Fetch GitHub repositories
  const { data: repositories = [] } = useQuery(
    'github-repositories',
    dashboardApi.getGitHubRepositories,
    {
      enabled: true,
      staleTime: 10 * 60 * 1000, // 10 minutes
    }
  );

  // Fetch pinned projects
  const { data: pinnedProjects = [] } = useQuery(
    'pinned-projects',
    dashboardApi.getProjects,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const handleProjectMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setProjectMenuAnchor(event.currentTarget);
  };

  const handleProjectMenuClose = () => {
    setProjectMenuAnchor(null);
  };

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationMenuAnchor(event.currentTarget);
  };

  const handleNotificationMenuClose = () => {
    setNotificationMenuAnchor(null);
  };

  const handleSelectProjectToPin = () => {
    handleProjectMenuClose();
    setProjectDialogOpen(true);
  };

  return (
    <>
      <AppBar 
        position="sticky" 
        elevation={0}
        sx={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <Toolbar>
          {/* Logo and Title */}
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            <Typography 
              variant="h6" 
              component="div" 
              sx={{ 
                fontWeight: 'bold',
                background: 'linear-gradient(45deg, #fff, #f0f0f0)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              Contexten Dashboard
            </Typography>
            
            {/* Status Indicators */}
            <Box sx={{ ml: 3, display: 'flex', gap: 1 }}>
              <Chip
                size="small"
                label={`${pinnedProjects.length} Projects`}
                sx={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  fontSize: '0.75rem',
                }}
              />
              <Chip
                size="small"
                label="Multi-Layer Orchestration"
                sx={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  fontSize: '0.75rem',
                }}
              />
            </Box>
          </Box>

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Notifications */}
            <IconButton
              color="inherit"
              onClick={handleNotificationMenuOpen}
              sx={{ color: 'white' }}
            >
              <Badge badgeContent={3} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>

            {/* Select Project To Pin */}
            <Button
              variant="outlined"
              startIcon={<PinIcon />}
              onClick={handleProjectMenuOpen}
              sx={{
                color: 'white',
                borderColor: 'rgba(255, 255, 255, 0.5)',
                '&:hover': {
                  borderColor: 'white',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              Select Project To Pin
            </Button>

            {/* Settings */}
            <Button
              variant="outlined"
              startIcon={<SettingsIcon />}
              onClick={() => setSettingsOpen(true)}
              sx={{
                color: 'white',
                borderColor: 'rgba(255, 255, 255, 0.5)',
                '&:hover': {
                  borderColor: 'white',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              Settings
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Project Selection Menu */}
      <Menu
        anchorEl={projectMenuAnchor}
        open={Boolean(projectMenuAnchor)}
        onClose={handleProjectMenuClose}
        PaperProps={{
          sx: { minWidth: 250 }
        }}
      >
        <MenuItem onClick={handleSelectProjectToPin}>
          <GitHubIcon sx={{ mr: 1 }} />
          Browse GitHub Repositories
        </MenuItem>
        <MenuItem onClick={handleProjectMenuClose} disabled>
          <PinIcon sx={{ mr: 1 }} />
          Quick Pin Recent Projects
        </MenuItem>
      </Menu>

      {/* Notification Menu */}
      <Menu
        anchorEl={notificationMenuAnchor}
        open={Boolean(notificationMenuAnchor)}
        onClose={handleNotificationMenuClose}
        PaperProps={{
          sx: { minWidth: 300, maxHeight: 400 }
        }}
      >
        <MenuItem onClick={handleNotificationMenuClose}>
          <Box>
            <Typography variant="subtitle2">Workflow Completed</Typography>
            <Typography variant="body2" color="text.secondary">
              Project "FastAPI Enhancement" finished successfully
            </Typography>
          </Box>
        </MenuItem>
        <MenuItem onClick={handleNotificationMenuClose}>
          <Box>
            <Typography variant="subtitle2">Quality Gate Failed</Typography>
            <Typography variant="body2" color="text.secondary">
              Code coverage below threshold in "React Dashboard"
            </Typography>
          </Box>
        </MenuItem>
        <MenuItem onClick={handleNotificationMenuClose}>
          <Box>
            <Typography variant="subtitle2">PR Created</Typography>
            <Typography variant="body2" color="text.secondary">
              New pull request opened for "Database Migration"
            </Typography>
          </Box>
        </MenuItem>
      </Menu>

      {/* Project Selection Dialog */}
      <ProjectSelectionDialog
        open={projectDialogOpen}
        onClose={() => setProjectDialogOpen(false)}
        repositories={repositories}
      />
    </>
  );
};

export default TopBar;

