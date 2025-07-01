/**
 * Workflow Monitor Component - Real-time workflow execution monitoring
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Chip,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Paper,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Pause,
  Refresh,
  ExpandMore,
  ExpandLess,
  CheckCircle,
  Error,
  Schedule,
  Replay,
  Visibility,
  Timeline,
  Code,
  CloudUpload,
  Security,
  Notifications,
} from '@mui/icons-material';

import { apiService } from '../services/api';

const WorkflowMonitor = ({ projectId, sx }) => {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [expandedWorkflow, setExpandedWorkflow] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (projectId) {
      fetchWorkflows();
      // Set up polling for real-time updates
      const interval = setInterval(fetchWorkflows, 3000);
      return () => clearInterval(interval);
    }
  }, [projectId]);

  const fetchWorkflows = async () => {
    try {
      const response = await apiService.getWorkflows(projectId);
      setWorkflows(response.workflows || []);
    } catch (error) {
      console.error('Error fetching workflows:', error);
    }
  };

  const handleStartWorkflow = async (workflowId) => {
    try {
      setLoading(true);
      await apiService.startWorkflow(workflowId);
      await fetchWorkflows();
    } catch (error) {
      console.error('Error starting workflow:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStopWorkflow = async (workflowId) => {
    try {
      setLoading(true);
      await apiService.stopWorkflow(workflowId);
      await fetchWorkflows();
    } catch (error) {
      console.error('Error stopping workflow:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'default',
      running: 'primary',
      completed: 'success',
      failed: 'error',
      cancelled: 'warning',
      paused: 'info',
    };
    return colors[status] || 'default';
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: <Schedule />,
      running: <PlayArrow />,
      completed: <CheckCircle />,
      failed: <Error />,
      cancelled: <Stop />,
      paused: <Pause />,
    };
    return icons[status] || <Schedule />;
  };

  const getStepIcon = (stepType) => {
    const icons = {
      code_analysis: <Code />,
      agent_execution: <PlayArrow />,
      pr_creation: <Timeline />,
      deployment: <CloudUpload />,
      validation: <Security />,
      notification: <Notifications />,
    };
    return icons[stepType] || <Timeline />;
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'Not started';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end - start) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  const WorkflowCard = ({ workflow }) => {
    const isExpanded = expandedWorkflow === workflow.workflow_id;
    
    return (
      <Card
        sx={{
          mb: 2,
          border: workflow.status === 'running' ? '2px solid #00d4aa' : '1px solid rgba(255, 255, 255, 0.1)',
          transition: 'all 0.3s ease',
        }}
      >
        <CardContent>
          {/* Workflow Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {getStatusIcon(workflow.status)}
                <Typography variant="h6" sx={{ ml: 1, mr: 2 }}>
                  {workflow.name}
                </Typography>
                <Chip
                  label={workflow.status.toUpperCase()}
                  color={getStatusColor(workflow.status)}
                  size="small"
                  variant="outlined"
                />
              </Box>
              
              <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                Created: {new Date(workflow.created_at).toLocaleString()}
              </Typography>
              
              {workflow.started_at && (
                <Typography variant="body2" color="textSecondary">
                  Duration: {formatDuration(workflow.started_at, workflow.completed_at)}
                </Typography>
              )}
            </Box>

            <Box sx={{ display: 'flex', gap: 1 }}>
              {workflow.status === 'pending' && (
                <Tooltip title="Start Workflow">
                  <IconButton
                    color="primary"
                    onClick={() => handleStartWorkflow(workflow.workflow_id)}
                    disabled={loading}
                  >
                    <PlayArrow />
                  </IconButton>
                </Tooltip>
              )}
              
              {workflow.status === 'running' && (
                <Tooltip title="Stop Workflow">
                  <IconButton
                    color="error"
                    onClick={() => handleStopWorkflow(workflow.workflow_id)}
                    disabled={loading}
                  >
                    <Stop />
                  </IconButton>
                </Tooltip>
              )}
              
              <Tooltip title="View Details">
                <IconButton
                  onClick={() => {
                    setSelectedWorkflow(workflow);
                    setDetailsOpen(true);
                  }}
                >
                  <Visibility />
                </IconButton>
              </Tooltip>
              
              <IconButton
                onClick={() => setExpandedWorkflow(isExpanded ? null : workflow.workflow_id)}
              >
                {isExpanded ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>
          </Box>

          {/* Progress Bar */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">
                Progress: {workflow.progress_percentage}%
              </Typography>
              <Typography variant="body2">
                {workflow.steps?.filter(s => s.status === 'completed').length || 0} / {workflow.steps?.length || 0} steps
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={workflow.progress_percentage}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
              }}
            />
          </Box>

          {/* Error Message */}
          {workflow.error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {workflow.error}
            </Alert>
          )}

          {/* Expanded Steps */}
          <Collapse in={isExpanded}>
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <Typography variant="subtitle1" gutterBottom>
                Workflow Steps:
              </Typography>
              
              <Stepper orientation="vertical" activeStep={-1}>
                {workflow.steps?.map((step, index) => (
                  <Step key={step.step_id} completed={step.status === 'completed'}>
                    <StepLabel
                      error={step.status === 'failed'}
                      icon={getStepIcon(step.step_type)}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1">
                          {step.name}
                        </Typography>
                        <Chip
                          label={step.status}
                          size="small"
                          color={getStatusColor(step.status)}
                          variant="outlined"
                        />
                      </Box>
                    </StepLabel>
                    <StepContent>
                      <Box sx={{ pl: 2 }}>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          Type: {step.step_type}
                        </Typography>
                        
                        {step.started_at && (
                          <Typography variant="body2" color="textSecondary">
                            Duration: {formatDuration(step.started_at, step.completed_at)}
                          </Typography>
                        )}
                        
                        {step.error && (
                          <Alert severity="error" sx={{ mt: 1, mb: 1 }}>
                            {step.error}
                          </Alert>
                        )}
                        
                        {step.result && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" color="textSecondary">
                              Result:
                            </Typography>
                            <Paper
                              sx={{
                                p: 1,
                                mt: 0.5,
                                backgroundColor: 'rgba(0, 0, 0, 0.2)',
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                                maxHeight: 100,
                                overflow: 'auto',
                              }}
                            >
                              {JSON.stringify(step.result, null, 2)}
                            </Paper>
                          </Box>
                        )}
                      </Box>
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    );
  };

  return (
    <Card sx={{ ...sx }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="div">
            🔄 Workflow Monitor
          </Typography>
          <Box>
            <Tooltip title="Refresh Workflows">
              <IconButton onClick={fetchWorkflows} disabled={loading}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {workflows.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Timeline sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="body1" color="textSecondary">
              No workflows found for this project
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Create a plan and start a workflow to see execution progress
            </Typography>
          </Box>
        ) : (
          <Box>
            {workflows.map((workflow) => (
              <WorkflowCard key={workflow.workflow_id} workflow={workflow} />
            ))}
          </Box>
        )}

        {/* Workflow Details Dialog */}
        <Dialog
          open={detailsOpen}
          onClose={() => setDetailsOpen(false)}
          maxWidth="lg"
          fullWidth
        >
          <DialogTitle>
            Workflow Details: {selectedWorkflow?.name}
          </DialogTitle>
          <DialogContent>
            {selectedWorkflow && (
              <Box>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Basic Information
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemIcon>
                          {getStatusIcon(selectedWorkflow.status)}
                        </ListItemIcon>
                        <ListItemText
                          primary="Status"
                          secondary={
                            <Chip
                              label={selectedWorkflow.status.toUpperCase()}
                              color={getStatusColor(selectedWorkflow.status)}
                              size="small"
                            />
                          }
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <Timeline />
                        </ListItemIcon>
                        <ListItemText
                          primary="Progress"
                          secondary={`${selectedWorkflow.progress_percentage}% (${selectedWorkflow.steps?.filter(s => s.status === 'completed').length || 0}/${selectedWorkflow.steps?.length || 0} steps)`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <Schedule />
                        </ListItemIcon>
                        <ListItemText
                          primary="Duration"
                          secondary={formatDuration(selectedWorkflow.started_at, selectedWorkflow.completed_at)}
                        />
                      </ListItem>
                    </List>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Step Summary
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {['pending', 'running', 'completed', 'failed', 'skipped'].map(status => {
                        const count = selectedWorkflow.steps?.filter(s => s.status === status).length || 0;
                        if (count === 0) return null;
                        
                        return (
                          <Box key={status} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Chip
                              label={status}
                              color={getStatusColor(status)}
                              size="small"
                              variant="outlined"
                            />
                            <Typography variant="body2">
                              {count} step{count !== 1 ? 's' : ''}
                            </Typography>
                          </Box>
                        );
                      })}
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Metadata
                    </Typography>
                    <Paper
                      sx={{
                        p: 2,
                        backgroundColor: 'rgba(0, 0, 0, 0.2)',
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                        maxHeight: 200,
                        overflow: 'auto',
                      }}
                    >
                      {JSON.stringify(selectedWorkflow.metadata || {}, null, 2)}
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default WorkflowMonitor;

