import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Box,
  Menu,
  MenuItem,
  Tooltip,
  Badge,
  useTheme,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Add as AddIcon,
  GitHub as GitHubIcon,
  LinearScale as LinearIcon,
  Code as CodegenIcon,
  DataObject as FlowIcon,
} from '@mui/icons-material';
import { useSettings } from '../contexts/SettingsContext';
import { useProject } from '../contexts/ProjectContext';
import ProjectSelector from './ProjectSelector';
import SettingsDialog from './SettingsDialog';

const TopBar: React.FC = () => {
  const theme = useTheme();
  const { settings } = useSettings();
  const { projects } = useProject();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [projectSelectorOpen, setProjectSelectorOpen] = useState(false);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleSettingsClick = () => {
    setSettingsOpen(true);
    handleMenuClose();
  };

  const handleProjectSelectorClick = () => {
    setProjectSelectorOpen(true);
    handleMenuClose();
  };

  const getServiceStatus = (token: string) => {
    return token ? 'Connected' : 'Not Connected';
  };

  return (
    <>
      <AppBar 
        position="static" 
        color="default" 
        elevation={1}
        sx={{
          bgcolor: theme.palette.background.paper,
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{
              flexGrow: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <FlowIcon sx={{ fontSize: 28 }} />
            Dashboard
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Tooltip title="Service Status">
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Tooltip title={`GitHub: ${getServiceStatus(settings.githubToken)}`}>
                  <IconButton size="small" color={settings.githubToken ? 'primary' : 'default'}>
                    <GitHubIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title={`Linear: ${getServiceStatus(settings.linearToken)}`}>
                  <IconButton size="small" color={settings.linearToken ? 'primary' : 'default'}>
                    <LinearIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title={`Codegen: ${getServiceStatus(settings.codegenToken)}`}>
                  <IconButton size="small" color={settings.codegenToken ? 'primary' : 'default'}>
                    <CodegenIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Tooltip>

            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleProjectSelectorClick}
              sx={{ borderRadius: 2 }}
            >
              Select Project to Pin
            </Button>

            <Tooltip title="Notifications">
              <IconButton>
                <Badge badgeContent={projects.filter(p => p.flowStatus === 'error').length} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>

            <Tooltip title="Settings">
              <IconButton onClick={handleSettingsClick}>
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>

      <ProjectSelector
        open={projectSelectorOpen}
        onClose={() => setProjectSelectorOpen(false)}
      />

      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </>
  );
};

export default TopBar;

