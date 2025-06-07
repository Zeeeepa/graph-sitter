import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Menu,
  MenuItem,
  Box,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Settings as SettingsIcon,
  PushPin as PinIcon,
  KeyboardArrowDown as ArrowDownIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface TopBarProps {
  availableProjects: Project[];
  onPinProject: (project: Project) => void;
  onOpenSettings: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  availableProjects,
  onPinProject,
  onOpenSettings
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handlePinProject = (project: Project) => {
    onPinProject(project);
    handleClose();
  };

  return (
    <AppBar 
      position="static" 
      elevation={1}
      sx={{ 
        backgroundColor: 'white', 
        color: 'text.primary',
        borderBottom: '1px solid',
        borderColor: 'divider'
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography 
            variant="h5" 
            component="h1" 
            sx={{ 
              fontWeight: 'bold',
              color: 'primary.main',
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }}
          >
            🎯 Contexten Dashboard
          </Typography>
          <Chip 
            label="Multi-layered Workflow Orchestration Platform" 
            variant="outlined" 
            size="small"
            sx={{ 
              fontSize: '0.75rem',
              color: 'text.secondary',
              borderColor: 'divider'
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Project Pin Button */}
          <Button
            variant="outlined"
            startIcon={<PinIcon />}
            endIcon={<ArrowDownIcon />}
            onClick={handleClick}
            sx={{
              textTransform: 'none',
              borderColor: 'primary.main',
              color: 'primary.main',
              '&:hover': {
                borderColor: 'primary.dark',
                backgroundColor: 'primary.50'
              }
            }}
          >
            Select Project To Pin
          </Button>

          <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={handleClose}
            PaperProps={{
              sx: {
                width: 320,
                maxHeight: 400,
                mt: 1
              }
            }}
          >
            {availableProjects.length === 0 ? (
              <MenuItem disabled>
                <Box sx={{ py: 2, textAlign: 'center', width: '100%' }}>
                  <Typography variant="body2" color="text.secondary">
                    No projects available to pin
                  </Typography>
                </Box>
              </MenuItem>
            ) : (
              availableProjects.map((project) => (
                <MenuItem 
                  key={project.id} 
                  onClick={() => handlePinProject(project)}
                  sx={{ 
                    flexDirection: 'column', 
                    alignItems: 'flex-start',
                    py: 2,
                    '&:hover': {
                      backgroundColor: 'primary.50'
                    }
                  }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 'medium' }}>
                    {project.name}
                  </Typography>
                  <Typography 
                    variant="caption" 
                    color="text.secondary"
                    sx={{ mt: 0.5, maxWidth: '100%' }}
                    noWrap
                  >
                    {project.description || project.repository}
                  </Typography>
                </MenuItem>
              ))
            )}
          </Menu>

          {/* Settings Button */}
          <Tooltip title="Open Settings">
            <IconButton
              onClick={onOpenSettings}
              sx={{
                color: 'primary.main',
                '&:hover': {
                  backgroundColor: 'primary.50'
                }
              }}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

