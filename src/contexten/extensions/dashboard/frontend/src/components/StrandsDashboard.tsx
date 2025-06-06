import React, { useState, useEffect } from 'react';
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
} from '@mui/icons-material';

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
  const [workflows, setWorkflows] = useState<WorkflowStatus[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [codegenTasks, setCodegenTasks] = useState<CodegenTask[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [newWorkflowOpen, setNewWorkflowOpen] = useState(false);
  const [newCodegenOpen, setNewCodegenOpen] = useState(false);
  const [workflowName, setWorkflowName] = useState('');
  const [codegenPrompt, setCodegenPrompt] = useState('');

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    // Initialize WebSocket connection
    const ws = new WebSocket(`ws://localhost:8000/ws`);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('Connected to Strands Dashboard');
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'system_health') {
        setSystemHealth(message.data);
      } else if (message.type === 'workflow_update') {
        fetchWorkflows();
      }
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      console.log('Disconnected from Strands Dashboard');
    };

    // Initial data fetch
    fetchWorkflows();
    fetchSystemHealth();
    fetchCodegenTasks();

    return () => {
      ws.close();
    };
  }, []);

  const fetchWorkflows = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/workflows`);
      const data = await response.json();
      setWorkflows(data.workflows || []);
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/health`);
      const data = await response.json();
      setSystemHealth(data);
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    }
  };

  const fetchCodegenTasks = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/codegen/tasks`);
      const data = await response.json();
      setCodegenTasks(data.tasks || []);
    } catch (error) {
      console.error('Failed to fetch codegen tasks:', error);
    }
  };

  const createWorkflow = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: workflowName }),
      });
      
      if (response.ok) {
        setNewWorkflowOpen(false);
        setWorkflowName('');
        fetchWorkflows();
      }
    } catch (error) {
      console.error('Failed to create workflow:', error);
    }
  };

  const createCodegenTask = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/codegen/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: codegenPrompt }),
      });
      
      if (response.ok) {
        setNewCodegenOpen(false);
        setCodegenPrompt('');
        fetchCodegenTasks();
      }
    } catch (error) {
      console.error('Failed to create codegen task:', error);
    }
  };

  const restartWorkflow = async (workflowId: string) => {
    try {
      await fetch(`${API_BASE}/api/workflows/${workflowId}/restart`, {
        method: 'POST',
      });
      fetchWorkflows();
    } catch (error) {
      console.error('Failed to restart workflow:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success';
      case 'completed': return 'info';
      case 'failed': return 'error';
      case 'restarting': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Strands Agent Dashboard
      </Typography>

      {/* Connection Status */}
      <Alert 
        severity={isConnected ? 'success' : 'warning'} 
        sx={{ mb: 3 }}
      >
        {isConnected ? 'Connected to Strands Backend' : 'Disconnected from Backend'}
      </Alert>

      {/* System Health */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <MonitorHeart color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">System Health</Typography>
              </Box>
              <Typography variant="h4" color={systemHealth?.status === 'healthy' ? 'success.main' : 'error.main'}>
                {systemHealth?.status || 'Unknown'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Uptime: {Math.floor((systemHealth?.uptime || 0) / 60)}m
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Workflow color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Active Workflows</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {systemHealth?.active_workflows || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Code color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Codegen Tasks</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {codegenTasks.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6">Error Count</Typography>
              <Typography variant="h4" color={systemHealth?.error_count ? 'error.main' : 'success.main'}>
                {systemHealth?.error_count || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Workflows Section */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Workflows</Typography>
                <Button
                  startIcon={<Add />}
                  variant="contained"
                  onClick={() => setNewWorkflowOpen(true)}
                >
                  New Workflow
                </Button>
              </Box>
              
              <List>
                {workflows.map((workflow) => (
                  <ListItem key={workflow.id}>
                    <ListItemText
                      primary={workflow.name}
                      secondary={`Created: ${new Date(workflow.created_at).toLocaleString()}`}
                    />
                    <Chip
                      label={workflow.status}
                      color={getStatusColor(workflow.status) as any}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => restartWorkflow(workflow.id)}
                        disabled={workflow.status === 'running'}
                      >
                        <Refresh />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
              
              {workflows.length === 0 && (
                <Typography color="text.secondary" align="center">
                  No workflows created yet
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Codegen Tasks Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Codegen Tasks</Typography>
                <Button
                  startIcon={<Code />}
                  variant="contained"
                  onClick={() => setNewCodegenOpen(true)}
                >
                  New Task
                </Button>
              </Box>
              
              <List>
                {codegenTasks.map((task) => (
                  <ListItem key={task.id}>
                    <ListItemText
                      primary={task.prompt.substring(0, 50) + '...'}
                      secondary={`Status: ${task.status} | ${new Date(task.created_at).toLocaleString()}`}
                    />
                    <Chip
                      label={task.status}
                      color={getStatusColor(task.status) as any}
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
              
              {codegenTasks.length === 0 && (
                <Typography color="text.secondary" align="center">
                  No codegen tasks yet
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* New Workflow Dialog */}
      <Dialog open={newWorkflowOpen} onClose={() => setNewWorkflowOpen(false)}>
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
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewWorkflowOpen(false)}>Cancel</Button>
          <Button onClick={createWorkflow} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>

      {/* New Codegen Task Dialog */}
      <Dialog open={newCodegenOpen} onClose={() => setNewCodegenOpen(false)}>
        <DialogTitle>Create Codegen Task</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Prompt"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={codegenPrompt}
            onChange={(e) => setCodegenPrompt(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewCodegenOpen(false)}>Cancel</Button>
          <Button onClick={createCodegenTask} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrandsDashboard;

