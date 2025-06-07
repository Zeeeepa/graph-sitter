import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Chip
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';

interface TopBarProps {
  onProjectPin: (projectName: string) => void;
  onSettingsOpen: () => void;
}

const TopBar: React.FC<TopBarProps> = ({ onProjectPin, onSettingsOpen }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleProjectSelect = (projectName: string) => {
    onProjectPin(projectName);
    handleClose();
  };

  // Mock GitHub projects
  const mockProjects = [
    'graph-sitter',
    'contexten',
    'dashboard-system',
    'ai-workflow-manager',
    'code-analysis-engine'
  ];

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Contexten Dashboard
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip 
            label="AI-Powered" 
            color="secondary" 
            size="small" 
            variant="outlined"
          />
          
          <Button
            color="inherit"
            startIcon={<AddIcon />}
            endIcon={<ExpandMoreIcon />}
            onClick={handleClick}
            sx={{ textTransform: 'none' }}
          >
            Select Project To Pin
          </Button>
          
          <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={handleClose}
            MenuListProps={{
              'aria-labelledby': 'project-select-button',
            }}
          >
            {mockProjects.map((project) => (
              <MenuItem 
                key={project} 
                onClick={() => handleProjectSelect(project)}
              >
                {project}
              </MenuItem>
            ))}
          </Menu>
          
          <IconButton
            color="inherit"
            onClick={onSettingsOpen}
            aria-label="settings"
          >
            <SettingsIcon />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default TopBar;

