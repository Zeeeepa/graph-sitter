/**
 * Consolidated Dashboard Component
 * Combines the best elements from all three PRs into a unified React UI
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  AppBar,
  Toolbar,
  Container,
  Fab,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  GitHub as GitHubIcon,
  Code as CodeIcon,
  Assessment as AssessmentIcon,
  Notifications as NotificationsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  BugReport as BugReportIcon
} from '@mui/icons-material';

// Types
interface Project {
  id: string;
  name: string;
  repo_url: string;
  owner: string;
  repo_name: string;
  full_name: string;
  description: string;
  is_pinned: boolean;
  requirements: string;
  flow_status: string;
  project_status: string;
  progress_percentage: number;
  quality_score: number;
  test_coverage: number;
  complexity_score: number;
  security_score: number;
  created_at: string;
  updated_at: string;
}

interface Flow {
  id: string;
  project_id: string;
  name: string;
  status: string;
  progress_percentage: number;
  tasks: Task[];
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

interface Task {
  id: string;
  flow_id: string;
  project_id: string;
  title: string;
  description: string;
  task_type: string;
  status: string;
  progress_percentage: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

interface SystemHealth {
  status: string;
  timestamp: string;
  services: {
    github: string;
    linear: string;
    slack: string;
    codegen: string;
    database: string;
    strands_workflow: string;
    strands_mcp: string;
    controlflow: string;
    prefect: string;
  };
  system_metrics: {
    cpu: { usage_percent: number };
    memory: { usage_percent: number };
    disk: { usage_percent: number };
  };
  active_workflows: number;
  active_tasks: number;
  error_count: number;
}

interface QualityGate {
  id: string;
  name: string;
  metric: string;
  threshold: number;
  operator: string;
  severity: string;
  status: string;
  current_value?: number;
  message: string;
}

const ConsolidatedDashboard: React.FC = () => {
  // State management
  const [projects, setProjects] = useState<Project[]>([]);
  const [flows, setFlows] = useState<Flow[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [qualityGates, setQualityGates] = useState<{ [projectId: string]: QualityGate[] }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<any[]>([]);
  
  // Dialog states
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [requirementsDialogOpen, setRequirementsDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  
  // Form states
  const [newProjectUrl, setNewProjectUrl] = useState('');
  const [newProjectRequirements, setNewProjectRequirements] = useState('');
  const [projectRequirements, setProjectRequirements] = useState('');
  
  // WebSocket connection
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  // API base URL
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `${API_BASE.replace('http', 'ws')}/ws`;
      const websocket = new WebSocket(wsUrl);
      
      websocket.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        setWs(websocket);
        
        // Subscribe to all events
        websocket.send(JSON.stringify({
          type: 'subscribe',
          topics: ['all']
        }));
      };
      
      websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        setWs(null);
        
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('disconnected');
      };
    };
    
    setConnectionStatus('connecting');
    connectWebSocket();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'project_update':
        if (message.data.action === 'created') {
          setProjects(prev => [...prev, message.data.project]);
        } else if (message.data.action === 'updated') {
          setProjects(prev => prev.map(p => 
            p.id === message.data.project.id ? message.data.project : p
          ));
        } else if (message.data.action === 'deleted') {
          setProjects(prev => prev.filter(p => p.id !== message.data.project_id));
        }
        break;
        
      case 'flow_update':
        if (message.data.action === 'started') {
          setFlows(prev => [...prev, message.data.flow]);
        } else if (message.data.action === 'updated') {
          setFlows(prev => prev.map(f => 
            f.id === message.data.flow.id ? message.data.flow : f
          ));
        }
        break;
        
      case 'system_health_update':
        setSystemHealth(message.data);
        break;
        
      case 'quality_gate_update':
        setQualityGates(prev => ({
          ...prev,
          [message.data.project_id]: message.data.results
        }));
        break;
        
      default:
        console.log('Unhandled WebSocket message:', message);
    }
    
    // Add notification
    if (message.type !== 'system_health_update') {
      addNotification({
        type: 'info',
        message: `${message.type}: ${message.data.action || 'update'}`,
        timestamp: new Date().toISOString()
      });
    }
  }, []);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      // Load projects
      const projectsResponse = await fetch(`${API_BASE}/api/projects`);
      if (projectsResponse.ok) {
        const projectsData = await projectsResponse.json();
        setProjects(projectsData);
      }
      
      // Load system health
      const healthResponse = await fetch(`${API_BASE}/api/health`);
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setSystemHealth(healthData);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Failed to load initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Utility functions
  const addNotification = (notification: any) => {
    const id = Date.now().toString();
    setNotifications(prev => [...prev, { ...notification, id }]);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'connected':
      case 'completed':
      case 'passed':
        return 'success';
      case 'warning':
      case 'paused':
        return 'warning';
      case 'error':
      case 'failed':
      case 'disconnected':
        return 'error';
      case 'running':
      case 'in_progress':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'connected':
      case 'completed':
      case 'passed':
        return <CheckCircleIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'error':
      case 'failed':
      case 'disconnected':
        return <ErrorIcon />;
      case 'running':
      case 'in_progress':
        return <PlayIcon />;
      default:
        return <InfoIcon />;
    }
  };

  // API functions
  const createProject = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: newProjectUrl,
          requirements: newProjectRequirements,
          auto_pin: true
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        addNotification({
          type: 'success',
          message: 'Project created successfully'
        });
        setProjectDialogOpen(false);
        setNewProjectUrl('');
        setNewProjectRequirements('');
      } else {
        throw new Error('Failed to create project');
      }
    } catch (err) {
      addNotification({
        type: 'error',
        message: 'Failed to create project'
      });
    }
  };

  const startWorkflow = async (projectId: string, requirements: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/workflows/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          requirements: requirements,
          auto_execute: true
        })
      });
      
      if (response.ok) {
        addNotification({
          type: 'success',
          message: 'Workflow started successfully'
        });
        setRequirementsDialogOpen(false);
        setSelectedProject(null);
        setProjectRequirements('');
      } else {
        throw new Error('Failed to start workflow');
      }
    } catch (err) {
      addNotification({
        type: 'error',
        message: 'Failed to start workflow'
      });
    }
  };

  const generatePlan = async (projectId: string, requirements: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/codegen/plans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          requirements: requirements,
          include_quality_gates: true
        })
      });
      
      if (response.ok) {
        addNotification({
          type: 'success',
          message: 'Plan generated successfully'
        });
      } else {
        throw new Error('Failed to generate plan');
      }
    } catch (err) {
      addNotification({
        type: 'error',
        message: 'Failed to generate plan'
      });
    }
  };

  const validateQualityGates = async (projectId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/quality-gates/${projectId}/validate`, {
        method: 'POST'
      });
      
      if (response.ok) {
        addNotification({
          type: 'info',
          message: 'Quality gate validation started'
        });
      } else {
        throw new Error('Failed to start validation');
      }
    } catch (err) {
      addNotification({
        type: 'error',
        message: 'Failed to validate quality gates'
      });
    }
  };

  // Render functions
  const renderTopBar = () => (
    <AppBar position="static" sx={{ mb: 3 }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Strands Agent Dashboard
        </Typography>
        
        <Tooltip title="System Health">
          <Chip
            icon={getStatusIcon(systemHealth?.status || 'unknown')}
            label={systemHealth?.status || 'Unknown'}
            color={getStatusColor(systemHealth?.status || 'unknown') as any}
            variant="outlined"
            sx={{ mr: 2, color: 'white', borderColor: 'white' }}
          />
        </Tooltip>
        
        <Tooltip title="WebSocket Connection">
          <Chip
            icon={getStatusIcon(connectionStatus)}
            label={connectionStatus}
            color={getStatusColor(connectionStatus) as any}
            variant="outlined"
            sx={{ mr: 2, color: 'white', borderColor: 'white' }}
          />
        </Tooltip>
        
        <Tooltip title="Notifications">
          <IconButton color="inherit">
            <Badge badgeContent={notifications.length} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Settings">
          <IconButton color="inherit" onClick={() => setSettingsDialogOpen(true)}>
            <SettingsIcon />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Refresh">
          <IconButton color="inherit" onClick={loadInitialData}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );

  const renderSystemHealth = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          System Health
        </Typography>
        
        {systemHealth && (
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                System Resources
              </Typography>
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2">
                  CPU: {systemHealth.system_metrics.cpu?.usage_percent?.toFixed(1) || 0}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={systemHealth.system_metrics.cpu?.usage_percent || 0}
                  color={systemHealth.system_metrics.cpu?.usage_percent > 80 ? 'error' : 'primary'}
                />
              </Box>
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2">
                  Memory: {systemHealth.system_metrics.memory?.usage_percent?.toFixed(1) || 0}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={systemHealth.system_metrics.memory?.usage_percent || 0}
                  color={systemHealth.system_metrics.memory?.usage_percent > 85 ? 'error' : 'primary'}
                />
              </Box>
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2">
                  Disk: {systemHealth.system_metrics.disk?.usage_percent?.toFixed(1) || 0}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={systemHealth.system_metrics.disk?.usage_percent || 0}
                  color={systemHealth.system_metrics.disk?.usage_percent > 90 ? 'error' : 'primary'}
                />
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                Services
              </Typography>
              <Grid container spacing={1}>
                {Object.entries(systemHealth.services).map(([service, status]) => (
                  <Grid item xs={6} key={service}>
                    <Chip
                      icon={getStatusIcon(status)}
                      label={service}
                      color={getStatusColor(status) as any}
                      size="small"
                      variant="outlined"
                    />
                  </Grid>
                ))}
              </Grid>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Active Workflows: {systemHealth.active_workflows}
                </Typography>
                <Typography variant="body2">
                  Active Tasks: {systemHealth.active_tasks}
                </Typography>
                <Typography variant="body2">
                  Errors: {systemHealth.error_count}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        )}
      </CardContent>
    </Card>
  );

  const renderProjectCard = (project: Project) => (
    <Grid item xs={12} md={6} lg={4} key={project.id}>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Typography variant="h6" component="div" noWrap>
              {project.name}
            </Typography>
            {project.is_pinned && (
              <Chip label="Pinned" size="small" color="primary" />
            )}
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {project.description || 'No description'}
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" gutterBottom>
              Progress: {project.progress_percentage.toFixed(1)}%
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={project.progress_percentage}
              sx={{ mb: 1 }}
            />
            
            <Chip
              icon={getStatusIcon(project.flow_status)}
              label={project.flow_status}
              color={getStatusColor(project.flow_status) as any}
              size="small"
            />
          </Box>
          
          <Grid container spacing={1} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SpeedIcon fontSize="small" sx={{ mr: 0.5 }} />
                <Typography variant="caption">
                  Quality: {project.quality_score.toFixed(1)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <AssessmentIcon fontSize="small" sx={{ mr: 0.5 }} />
                <Typography variant="caption">
                  Coverage: {project.test_coverage.toFixed(1)}%
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <BugReportIcon fontSize="small" sx={{ mr: 0.5 }} />
                <Typography variant="caption">
                  Complexity: {project.complexity_score.toFixed(1)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SecurityIcon fontSize="small" sx={{ mr: 0.5 }} />
                <Typography variant="caption">
                  Security: {project.security_score.toFixed(1)}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
        
        <CardActions>
          <Button
            size="small"
            startIcon={<CodeIcon />}
            onClick={() => {
              setSelectedProject(project);
              setProjectRequirements(project.requirements);
              setRequirementsDialogOpen(true);
            }}
          >
            Plan
          </Button>
          <Button
            size="small"
            startIcon={<PlayIcon />}
            onClick={() => {
              setSelectedProject(project);
              setProjectRequirements(project.requirements);
              setRequirementsDialogOpen(true);
            }}
          >
            Start Flow
          </Button>
          <Button
            size="small"
            startIcon={<AssessmentIcon />}
            onClick={() => validateQualityGates(project.id)}
          >
            Validate
          </Button>
        </CardActions>
      </Card>
    </Grid>
  );

  const renderProjectDialog = () => (
    <Dialog open={projectDialogOpen} onClose={() => setProjectDialogOpen(false)} maxWidth="md" fullWidth>
      <DialogTitle>Add New Project</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          label="GitHub Repository URL"
          fullWidth
          variant="outlined"
          value={newProjectUrl}
          onChange={(e) => setNewProjectUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          sx={{ mb: 2 }}
        />
        <TextField
          margin="dense"
          label="Requirements (Optional)"
          fullWidth
          multiline
          rows={4}
          variant="outlined"
          value={newProjectRequirements}
          onChange={(e) => setNewProjectRequirements(e.target.value)}
          placeholder="Describe what you want to build or improve..."
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setProjectDialogOpen(false)}>Cancel</Button>
        <Button onClick={createProject} variant="contained" disabled={!newProjectUrl}>
          Create Project
        </Button>
      </DialogActions>
    </Dialog>
  );

  const renderRequirementsDialog = () => (
    <Dialog open={requirementsDialogOpen} onClose={() => setRequirementsDialogOpen(false)} maxWidth="md" fullWidth>
      <DialogTitle>
        {selectedProject ? `Plan for ${selectedProject.name}` : 'Project Plan'}
      </DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          label="Requirements"
          fullWidth
          multiline
          rows={6}
          variant="outlined"
          value={projectRequirements}
          onChange={(e) => setProjectRequirements(e.target.value)}
          placeholder="Describe what you want to build, fix, or improve..."
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setRequirementsDialogOpen(false)}>Cancel</Button>
        <Button 
          onClick={() => selectedProject && generatePlan(selectedProject.id, projectRequirements)}
          variant="outlined"
          disabled={!projectRequirements}
        >
          Generate Plan
        </Button>
        <Button 
          onClick={() => selectedProject && startWorkflow(selectedProject.id, projectRequirements)}
          variant="contained"
          disabled={!projectRequirements}
        >
          Start Flow
        </Button>
      </DialogActions>
    </Dialog>
  );

  const renderNotifications = () => (
    <>
      {notifications.map((notification) => (
        <Snackbar
          key={notification.id}
          open={true}
          autoHideDuration={5000}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert severity={notification.type} onClose={() => 
            setNotifications(prev => prev.filter(n => n.id !== notification.id))
          }>
            {notification.message}
          </Alert>
        </Snackbar>
      ))}
    </>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography>Loading dashboard...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {renderTopBar()}
      
      <Container maxWidth="xl">
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {renderSystemHealth()}
        
        <Typography variant="h5" gutterBottom>
          Projects
        </Typography>
        
        <Grid container spacing={3}>
          {projects.map(renderProjectCard)}
        </Grid>
        
        {projects.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No projects yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Add your first GitHub repository to get started
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setProjectDialogOpen(true)}
            >
              Add Project
            </Button>
          </Box>
        )}
      </Container>
      
      <Fab
        color="primary"
        aria-label="add"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => setProjectDialogOpen(true)}
      >
        <AddIcon />
      </Fab>
      
      {renderProjectDialog()}
      {renderRequirementsDialog()}
      {renderNotifications()}
    </Box>
  );
};

export default ConsolidatedDashboard;

