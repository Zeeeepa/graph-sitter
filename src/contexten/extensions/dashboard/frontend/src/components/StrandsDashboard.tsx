import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Skeleton,
  Fade,
  Tooltip,
  LinearProgress,
  Snackbar,
  AppBar,
  Toolbar,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Add,
  Settings,
  MonitorHeart,
  Code,
  Workflow,
  Error as ErrorIcon,
  CheckCircle,
  Warning,
  Info,
  Delete,
  Visibility,
} from '@mui/icons-material';
import toast from 'react-hot-toast';

interface WorkflowStatus {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

interface SystemHealth {
  status: string;
  uptime: number;
  active_workflows: number;
  error_count: number;
  last_check: string;
}

interface CodegenTask {
  id: string;
  prompt: string;
  status: string;
  result?: string;
  created_at: string;
}

const StrandsDashboard: React.FC = () => {
  // State management
  const [workflows, setWorkflows] = useState<WorkflowStatus[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [codegenTasks, setCodegenTasks] = useState<CodegenTask[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [newWorkflowOpen, setNewWorkflowOpen] = useState(false);
  const [newCodegenOpen, setNewCodegenOpen] = useState(false);
  const [taskDetailOpen, setTaskDetailOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<CodegenTask | null>(null);
  
  // Form states
  const [workflowName, setWorkflowName] = useState('');
  const [codegenPrompt, setCodegenPrompt] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // WebSocket connection with reconnection logic
  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws`);
    
    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      toast.success('Connected to Strands Backend');
      console.log('Connected to Strands Dashboard');
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'system_health') {
          setSystemHealth(message.data);
        } else if (message.type === 'workflow_update') {
          fetchWorkflows();
          toast.info('Workflow updated');
        } else if (message.type === 'codegen_update') {
          fetchCodegenTasks();
          toast.info('Codegen task updated');
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      console.log('Disconnected from Strands Dashboard');
      
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (!isConnected) {
          connectWebSocket();
        }
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection failed');
    };

    return ws;
  }, [isConnected]);

  useEffect(() => {
    const ws = connectWebSocket();
    
    // Initial data fetch
    const initializeData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchWorkflows(),
          fetchSystemHealth(),
          fetchCodegenTasks()
        ]);
      } catch (err) {
        setError('Failed to load initial data');
      } finally {
        setLoading(false);
      }
    };

    initializeData();

    return () => {
      ws.close();
    };
  }, [connectWebSocket]);

  // API functions with error handling
  const fetchWorkflows = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/workflows`);
      if (!response.ok) throw new Error('Failed to fetch workflows');
      const data = await response.json();
      setWorkflows(data.workflows || []);
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
      toast.error('Failed to load workflows');
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/health`);
      if (!response.ok) throw new Error('Failed to fetch system health');
      const data = await response.json();
      setSystemHealth(data);
    } catch (error) {
      console.error('Failed to fetch system health:', error);
      toast.error('Failed to load system health');
    }
  };

  const fetchCodegenTasks = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/codegen/tasks`);
      if (!response.ok) throw new Error('Failed to fetch codegen tasks');
      const data = await response.json();
      setCodegenTasks(data.tasks || []);
    } catch (error) {
      console.error('Failed to fetch codegen tasks:', error);
      toast.error('Failed to load codegen tasks');
    }
  };

  const createWorkflow = async () => {
    if (!workflowName.trim()) {
      toast.error('Please enter a workflow name');
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/api/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: workflowName.trim() }),
      });
      
      if (!response.ok) throw new Error('Failed to create workflow');
      
      setNewWorkflowOpen(false);
      setWorkflowName('');
      await fetchWorkflows();
      toast.success('Workflow created successfully');
    } catch (error) {
      console.error('Failed to create workflow:', error);
      toast.error('Failed to create workflow');
    } finally {
      setSubmitting(false);
    }
  };

  const createCodegenTask = async () => {
    if (!codegenPrompt.trim()) {
      toast.error('Please enter a prompt');
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/api/codegen/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: codegenPrompt.trim() }),
      });
      
      if (!response.ok) throw new Error('Failed to create codegen task');
      
      setNewCodegenOpen(false);
      setCodegenPrompt('');
      await fetchCodegenTasks();
      toast.success('Codegen task created successfully');
    } catch (error) {
      console.error('Failed to create codegen task:', error);
      toast.error('Failed to create codegen task');
    } finally {
      setSubmitting(false);
    }
  };

  const restartWorkflow = async (workflowId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/workflows/${workflowId}/restart`, {
        method: 'POST',
      });
      
      if (!response.ok) throw new Error('Failed to restart workflow');
      
      await fetchWorkflows();
      toast.success('Workflow restarted successfully');
    } catch (error) {
      console.error('Failed to restart workflow:', error);
      toast.error('Failed to restart workflow');
    }
  };

  // Utility functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success';
      case 'completed': return 'info';
      case 'failed': return 'error';
      case 'restarting': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <PlayArrow />;
      case 'completed': return <CheckCircle />;
      case 'failed': return <ErrorIcon />;
      case 'restarting': return <Refresh />;
      default: return <Info />;
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  // Loading skeleton component
  const LoadingSkeleton = () => (
    <Grid container spacing={3}>
      {[1, 2, 3, 4].map((i) => (
        <Grid item xs={12} md={3} key={i}>
          <Card>
            <CardContent>
              <Skeleton variant="text" width="60%" height={32} />
              <Skeleton variant="text" width="40%" height={48} />
              <Skeleton variant="text" width="80%" height={24} />
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <AppBar position="static" elevation={0} sx={{ mb: 3, bgcolor: 'transparent' }}>
          <Toolbar sx={{ px: 0 }}>
            <Typography variant="h4" component="h1" sx={{ color: 'text.primary' }}>
              Strands Agent Dashboard
            </Typography>
          </Toolbar>
        </AppBar>
        <LoadingSkeleton />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <AppBar position="static" elevation={0} sx={{ mb: 3, bgcolor: 'transparent' }}>
        <Toolbar sx={{ px: 0 }}>
          <Typography variant="h4" component="h1" sx={{ color: 'text.primary', flexGrow: 1 }}>
            Strands Agent Dashboard
          </Typography>
          <Tooltip title="Refresh Data">
            <IconButton 
              onClick={() => {
                fetchWorkflows();
                fetchSystemHealth();
                fetchCodegenTasks();
              }}
              sx={{ ml: 2 }}
            >
              <Refresh />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Connection Status */}
      <Fade in={true}>
        <Alert 
          severity={isConnected ? 'success' : 'warning'} 
          sx={{ mb: 3 }}
          icon={isConnected ? <CheckCircle /> : <Warning />}
        >
          {isConnected ? 'Connected to Strands Backend' : 'Disconnected from Backend - Attempting to reconnect...'}
        </Alert>
      </Fade>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* System Health Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <MonitorHeart color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">System Health</Typography>
              </Box>
              <Typography 
                variant="h4" 
                color={systemHealth?.status === 'healthy' ? 'success.main' : 'error.main'}
                sx={{ mb: 1 }}
              >
                {systemHealth?.status || 'Unknown'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Uptime: {formatUptime(systemHealth?.uptime || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Last check: {systemHealth?.last_check ? new Date(systemHealth.last_check).toLocaleTimeString() : 'Never'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Workflow color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Active Workflows</Typography>
              </Box>
              <Typography variant="h4" color="primary" sx={{ mb: 1 }}>
                {systemHealth?.active_workflows || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total workflows: {workflows.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Code color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Codegen Tasks</Typography>
              </Box>
              <Typography variant="h4" color="primary" sx={{ mb: 1 }}>
                {codegenTasks.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active: {codegenTasks.filter(t => t.status === 'running').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <ErrorIcon color={systemHealth?.error_count ? 'error' : 'disabled'} sx={{ mr: 1 }} />
                <Typography variant="h6">Error Count</Typography>
              </Box>
              <Typography 
                variant="h4" 
                color={systemHealth?.error_count ? 'error.main' : 'success.main'}
                sx={{ mb: 1 }}
              >
                {systemHealth?.error_count || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Last 24 hours
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Workflows Section */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Workflows</Typography>
                <Button
                  startIcon={<Add />}
                  variant="contained"
                  onClick={() => setNewWorkflowOpen(true)}
                  disabled={!isConnected}
                >
                  New Workflow
                </Button>
              </Box>
              
              {workflows.length > 0 ? (
                <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {workflows.map((workflow) => (
                    <ListItem 
                      key={workflow.id}
                      sx={{ 
                        border: 1, 
                        borderColor: 'divider', 
                        borderRadius: 1, 
                        mb: 1,
                        '&:last-child': { mb: 0 }
                      }}
                    >
                      <Box sx={{ mr: 2 }}>
                        {getStatusIcon(workflow.status)}
                      </Box>
                      <ListItemText
                        primary={
                          <Typography variant="subtitle1" fontWeight="medium">
                            {workflow.name}
                          </Typography>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Created: {new Date(workflow.created_at).toLocaleString()}
                            </Typography>
                            {workflow.error_message && (
                              <Typography variant="body2" color="error.main" sx={{ mt: 0.5 }}>
                                Error: {workflow.error_message}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={workflow.status}
                          color={getStatusColor(workflow.status) as any}
                          size="small"
                        />
                        <Tooltip title="Restart Workflow">
                          <IconButton
                            size="small"
                            onClick={() => restartWorkflow(workflow.id)}
                            disabled={workflow.status === 'running' || !isConnected}
                          >
                            <Refresh />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    py: 4,
                    color: 'text.secondary'
                  }}
                >
                  <Workflow sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                  <Typography variant="h6" gutterBottom>
                    No workflows created yet
                  </Typography>
                  <Typography variant="body2" align="center">
                    Create your first workflow to start monitoring your Strands agents
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Codegen Tasks Section */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Codegen Tasks</Typography>
                <Button
                  startIcon={<Code />}
                  variant="contained"
                  onClick={() => setNewCodegenOpen(true)}
                  disabled={!isConnected}
                >
                  New Task
                </Button>
              </Box>
              
              {codegenTasks.length > 0 ? (
                <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {codegenTasks.map((task) => (
                    <ListItem 
                      key={task.id}
                      sx={{ 
                        border: 1, 
                        borderColor: 'divider', 
                        borderRadius: 1, 
                        mb: 1,
                        '&:last-child': { mb: 0 }
                      }}
                    >
                      <Box sx={{ mr: 2 }}>
                        {getStatusIcon(task.status)}
                      </Box>
                      <ListItemText
                        primary={
                          <Typography variant="subtitle1" fontWeight="medium">
                            {task.prompt.length > 50 ? `${task.prompt.substring(0, 50)}...` : task.prompt}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="body2" color="text.secondary">
                            {new Date(task.created_at).toLocaleString()}
                          </Typography>
                        }
                      />
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={task.status}
                          color={getStatusColor(task.status) as any}
                          size="small"
                        />
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedTask(task);
                              setTaskDetailOpen(true);
                            }}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    py: 4,
                    color: 'text.secondary'
                  }}
                >
                  <Code sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                  <Typography variant="h6" gutterBottom>
                    No codegen tasks yet
                  </Typography>
                  <Typography variant="body2" align="center">
                    Create your first task to start generating code with AI
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* New Workflow Dialog */}
      <Dialog 
        open={newWorkflowOpen} 
        onClose={() => setNewWorkflowOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Workflow</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Workflow Name"
            fullWidth
            variant="outlined"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            placeholder="Enter a descriptive name for your workflow"
            helperText="Choose a name that describes what this workflow will do"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewWorkflowOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button 
            onClick={createWorkflow} 
            variant="contained" 
            disabled={submitting || !workflowName.trim()}
          >
            {submitting ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
        {submitting && <LinearProgress />}
      </Dialog>

      {/* New Codegen Task Dialog */}
      <Dialog 
        open={newCodegenOpen} 
        onClose={() => setNewCodegenOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create Codegen Task</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Prompt"
            fullWidth
            multiline
            rows={6}
            variant="outlined"
            value={codegenPrompt}
            onChange={(e) => setCodegenPrompt(e.target.value)}
            placeholder="Describe what code you want to generate..."
            helperText="Be specific about the functionality, language, and requirements"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewCodegenOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button 
            onClick={createCodegenTask} 
            variant="contained" 
            disabled={submitting || !codegenPrompt.trim()}
          >
            {submitting ? 'Creating...' : 'Create Task'}
          </Button>
        </DialogActions>
        {submitting && <LinearProgress />}
      </Dialog>

      {/* Task Detail Dialog */}
      <Dialog 
        open={taskDetailOpen} 
        onClose={() => setTaskDetailOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Task Details</DialogTitle>
        <DialogContent>
          {selectedTask && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Prompt
              </Typography>
              <Typography variant="body1" paragraph sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                {selectedTask.prompt}
              </Typography>
              
              <Typography variant="h6" gutterBottom>
                Status
              </Typography>
              <Chip
                label={selectedTask.status}
                color={getStatusColor(selectedTask.status) as any}
                sx={{ mb: 2 }}
              />
              
              {selectedTask.result && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Result
                  </Typography>
                  <Typography 
                    variant="body2" 
                    component="pre" 
                    sx={{ 
                      bgcolor: 'grey.50', 
                      p: 2, 
                      borderRadius: 1, 
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap'
                    }}
                  >
                    {selectedTask.result}
                  </Typography>
                </>
              )}
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Created: {new Date(selectedTask.created_at).toLocaleString()}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTaskDetailOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrandsDashboard;

