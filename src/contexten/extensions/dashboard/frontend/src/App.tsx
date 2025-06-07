import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Box,
  Fab,
  Snackbar,
  Alert,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Badge
} from '@mui/material';
import {
  Add as AddIcon,
  Dashboard as DashboardIcon,
  Timeline as TimelineIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';

import TopBar from './components/TopBar';
import ProjectCard from './components/ProjectCard';
import { ProjectDialog } from './components/ProjectDialog';
import SettingsDialog from './components/SettingsDialog';
import { WorkflowMonitor } from './components/WorkflowMonitor';
import { RealTimeMetrics } from './components/RealTimeMetrics';
import { AdvancedSettings } from './components/AdvancedSettings';
import { Project } from './types/dashboard';

// Create a modern theme for the dashboard
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
        },
      },
    },
  },
});

function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'workflows' | 'analytics'>('dashboard');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [advancedSettingsOpen, setAdvancedSettingsOpen] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });

  // Mock projects data
  useEffect(() => {
    const mockProjects: Project[] = [
      {
        id: '1',
        name: 'Graph Sitter Dashboard',
        description: 'Multi-layered workflow orchestration platform',
        repository: 'Zeeeepa/graph-sitter',
        status: 'active',
        progress: 75,
        flowEnabled: true,
        lastActivity: new Date(Date.now() - 300000),
        requirements: 'Implement Material-UI dashboard with real-time monitoring',
        plan: {
          id: 'plan-1',
          projectId: '1',
          requirements: 'Implement Material-UI dashboard with real-time monitoring',
          tasks: [
            {
              id: 'task-1',
              title: 'Setup Material-UI components',
              description: 'Convert existing components to Material-UI',
              status: 'completed',
              assignee: 'codegen-bot',
              estimatedHours: 4,
              actualHours: 3.5
            },
            {
              id: 'task-2',
              title: 'Implement real-time monitoring',
              description: 'Add WebSocket connections and live updates',
              status: 'in_progress',
              assignee: 'codegen-bot',
              estimatedHours: 6,
              actualHours: 2
            },
            {
              id: 'task-3',
              title: 'Add workflow orchestration',
              description: 'Implement advanced workflow management',
              status: 'pending',
              assignee: 'codegen-bot',
              estimatedHours: 8
            }
          ],
          createdAt: new Date(Date.now() - 86400000),
          updatedAt: new Date(Date.now() - 3600000)
        }
      },
      {
        id: '2',
        name: 'Contexten Core',
        description: 'Core orchestration framework',
        repository: 'Zeeeepa/contexten',
        status: 'completed',
        progress: 100,
        flowEnabled: false,
        lastActivity: new Date(Date.now() - 3600000),
        requirements: 'Enhance core framework with new features'
      }
    ];
    setProjects(mockProjects);
  }, []);

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project);
    setProjectDialogOpen(true);
  };

  const handleToggleFlow = (projectId: string, enabled: boolean) => {
    setProjects(prev => prev.map(p => 
      p.id === projectId ? { ...p, flowEnabled: enabled } : p
    ));
    setSnackbar({
      open: true,
      message: `Flow ${enabled ? 'enabled' : 'disabled'} for project`,
      severity: 'success'
    });
  };

  const handleOpenSettings = (project: Project) => {
    setSelectedProject(project);
    setAdvancedSettingsOpen(true);
  };

  const handleSaveSettings = (settings: any) => {
    console.log('Saving settings:', settings);
    setSnackbar({
      open: true,
      message: 'Settings saved successfully',
      severity: 'success'
    });
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, view: 'dashboard' as const },
    { text: 'Workflows', icon: <TimelineIcon />, view: 'workflows' as const },
    { text: 'Analytics', icon: <AnalyticsIcon />, view: 'analytics' as const },
  ];

  const renderCurrentView = () => {
    switch (currentView) {
      case 'workflows':
        return <WorkflowMonitor />;
      case 'analytics':
        return <RealTimeMetrics />;
      default:
        return (
          <Grid container spacing={3}>
            {projects.map((project) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <ProjectCard
                  project={project}
                  onOpenProject={handleProjectSelect}
                  onToggleFlow={handleToggleFlow}
                  onOpenSettings={handleOpenSettings}
                />
              </Grid>
            ))}
          </Grid>
        );
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      {/* App Bar */}
      <AppBar position="fixed" elevation={1}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => setDrawerOpen(true)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Contexten Dashboard
          </Typography>
          
          <IconButton color="inherit">
            <Badge badgeContent={3} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
          
          <IconButton 
            color="inherit"
            onClick={() => setSettingsDialogOpen(true)}
          >
            <SettingsIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Side Drawer */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box sx={{ width: 250, pt: 2 }}>
          <List>
            {menuItems.map((item) => (
              <ListItem
                button
                key={item.text}
                selected={currentView === item.view}
                onClick={() => {
                  setCurrentView(item.view);
                  setDrawerOpen(false);
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Container maxWidth="xl" sx={{ mt: 10, mb: 4 }}>
        <Box mb={3}>
          <Typography variant="h4" gutterBottom>
            {currentView === 'dashboard' && 'Project Dashboard'}
            {currentView === 'workflows' && 'Workflow Monitor'}
            {currentView === 'analytics' && 'Real-Time Analytics'}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {currentView === 'dashboard' && 'Manage your projects and workflows'}
            {currentView === 'workflows' && 'Monitor active workflow executions'}
            {currentView === 'analytics' && 'View real-time metrics and activity'}
          </Typography>
        </Box>

        {renderCurrentView()}
      </Container>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
        }}
        onClick={() => {
          // Handle add new project
          setSnackbar({
            open: true,
            message: 'Add new project feature coming soon!',
            severity: 'info'
          });
        }}
      >
        <AddIcon />
      </Fab>

      {/* Dialogs */}
      <ProjectDialog
        open={projectDialogOpen}
        project={selectedProject}
        onClose={() => {
          setProjectDialogOpen(false);
          setSelectedProject(null);
        }}
        onSave={(project) => {
          console.log('Saving project:', project);
          setProjectDialogOpen(false);
          setSelectedProject(null);
        }}
      />

      <SettingsDialog
        open={settingsDialogOpen}
        onClose={() => setSettingsDialogOpen(false)}
        onSave={handleSaveSettings}
      />

      <AdvancedSettings
        open={advancedSettingsOpen}
        onClose={() => setAdvancedSettingsOpen(false)}
        onSave={handleSaveSettings}
      />

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  );
}

export default App;
