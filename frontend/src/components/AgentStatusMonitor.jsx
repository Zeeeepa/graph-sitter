/**
 * Real-time Agent Status Monitor Component
 * Shows live status of Codegen agents with enhanced prompt information
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  IconButton,
  Collapse,
  Grid,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  ExpandMore,
  ExpandLess,
  Refresh,
  OpenInNew,
  PlayArrow,
  Stop,
  Info,
  Timeline,
  Code,
  BugReport,
  Speed,
} from '@mui/icons-material';
import { apiService } from '../services/api';

const AgentStatusMonitor = ({ projectId, sx }) => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedAgent, setExpandedAgent] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  useEffect(() => {
    if (projectId) {
      fetchAgentStatus();
      // Set up polling for real-time updates
      const interval = setInterval(fetchAgentStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [projectId]);

  const fetchAgentStatus = async () => {
    try {
      setLoading(true);
      const response = await apiService.getActiveAgents(projectId);
      setAgents(response.agents || []);
    } catch (error) {
      console.error('Error fetching agent status:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'default',
      running: 'primary',
      processing: 'secondary',
      completed: 'success',
      failed: 'error',
    };
    return colors[status] || 'default';
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: <Timeline />,
      running: <PlayArrow />,
      processing: <Speed />,
      completed: <Info />,
      failed: <BugReport />,
    };
    return icons[status] || <Info />;
  };

  const handleExpandAgent = (agentId) => {
    setExpandedAgent(expandedAgent === agentId ? null : agentId);
  };

  const handleShowDetails = (agent) => {
    setSelectedAgent(agent);
    setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
    setSelectedAgent(null);
  };

  const formatPrompt = (prompt, maxLength = 100) => {
    if (!prompt) return 'No prompt available';
    return prompt.length > maxLength ? `${prompt.substring(0, maxLength)}...` : prompt;
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <Card sx={{ ...sx }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="div">
            🤖 Agent Status Monitor
          </Typography>
          <Box>
            <Tooltip title="Refresh Status">
              <IconButton onClick={fetchAgentStatus} disabled={loading}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {agents.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="textSecondary">
              No active agents for this project
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Create a plan and start a workflow to see agent activity
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={2}>
            {agents.map((agent) => (
              <Grid item xs={12} key={agent.id}>
                <Card
                  variant="outlined"
                  sx={{
                    border: `2px solid ${
                      agent.status === 'running' ? '#00d4aa' :
                      agent.status === 'completed' ? '#4caf50' :
                      agent.status === 'failed' ? '#f44336' : 'rgba(255, 255, 255, 0.1)'
                    }`,
                    transition: 'all 0.3s ease',
                  }}
                >
                  <CardContent>
                    {/* Agent Header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          {getStatusIcon(agent.status)}
                          <Typography variant="h6" sx={{ ml: 1, mr: 2 }}>
                            Agent {agent.id.substring(0, 8)}
                          </Typography>
                          <Chip
                            label={agent.status.toUpperCase()}
                            color={getStatusColor(agent.status)}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                        
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                          Created: {formatTimestamp(agent.created_at)}
                        </Typography>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Prompt:</strong> {formatPrompt(agent.original_prompt)}
                        </Typography>
                      </Box>

                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="View Details">
                          <IconButton size="small" onClick={() => handleShowDetails(agent)}>
                            <Info />
                          </IconButton>
                        </Tooltip>
                        
                        {agent.web_url && (
                          <Tooltip title="Open in Codegen">
                            <IconButton
                              size="small"
                              onClick={() => window.open(agent.web_url, '_blank')}
                            >
                              <OpenInNew />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        <IconButton
                          size="small"
                          onClick={() => handleExpandAgent(agent.id)}
                        >
                          {expandedAgent === agent.id ? <ExpandLess /> : <ExpandMore />}
                        </IconButton>
                      </Box>
                    </Box>

                    {/* Progress Bar */}
                    {agent.progress_info && (
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">
                            {agent.progress_info.current_action}
                          </Typography>
                          <Typography variant="body2">
                            {agent.progress_info.progress_percentage}%
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={agent.progress_info.progress_percentage}
                          sx={{
                            height: 8,
                            borderRadius: 4,
                            backgroundColor: 'rgba(255, 255, 255, 0.1)',
                          }}
                        />
                      </Box>
                    )}

                    {/* Expanded Details */}
                    <Collapse in={expandedAgent === agent.id}>
                      <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>
                              Enhanced Prompt Preview:
                            </Typography>
                            <Box
                              sx={{
                                p: 2,
                                backgroundColor: 'rgba(0, 0, 0, 0.2)',
                                borderRadius: 1,
                                maxHeight: 150,
                                overflow: 'auto',
                                fontFamily: 'monospace',
                                fontSize: '0.875rem',
                              }}
                            >
                              {agent.enhanced_prompt || 'No enhanced prompt available'}
                            </Box>
                          </Grid>
                          
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>
                              Status History:
                            </Typography>
                            <Box sx={{ maxHeight: 150, overflow: 'auto' }}>
                              {agent.status_history && agent.status_history.length > 0 ? (
                                agent.status_history.map((status, index) => (
                                  <Box key={index} sx={{ mb: 1 }}>
                                    <Typography variant="body2">
                                      <Chip
                                        label={status.status}
                                        size="small"
                                        color={getStatusColor(status.status)}
                                        sx={{ mr: 1 }}
                                      />
                                      {formatTimestamp(status.timestamp)}
                                    </Typography>
                                    {status.message && (
                                      <Typography variant="caption" color="textSecondary">
                                        {status.message}
                                      </Typography>
                                    )}
                                  </Box>
                                ))
                              ) : (
                                <Typography variant="body2" color="textSecondary">
                                  No status history available
                                </Typography>
                              )}
                            </Box>
                          </Grid>
                        </Grid>
                      </Box>
                    </Collapse>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Agent Details Dialog */}
        <Dialog
          open={detailsOpen}
          onClose={handleCloseDetails}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Agent Details: {selectedAgent?.id.substring(0, 8)}
          </DialogTitle>
          <DialogContent>
            {selectedAgent && (
              <Box>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Basic Information
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemIcon>
                          <Info />
                        </ListItemIcon>
                        <ListItemText
                          primary="Status"
                          secondary={
                            <Chip
                              label={selectedAgent.status.toUpperCase()}
                              color={getStatusColor(selectedAgent.status)}
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
                          primary="Created"
                          secondary={formatTimestamp(selectedAgent.created_at)}
                        />
                      </ListItem>
                      {selectedAgent.web_url && (
                        <ListItem>
                          <ListItemIcon>
                            <OpenInNew />
                          </ListItemIcon>
                          <ListItemText
                            primary="Codegen URL"
                            secondary={
                              <Button
                                size="small"
                                onClick={() => window.open(selectedAgent.web_url, '_blank')}
                              >
                                Open in Codegen
                              </Button>
                            }
                          />
                        </ListItem>
                      )}
                    </List>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Prompt Enhancement
                    </Typography>
                    {selectedAgent.prompt_enhancement_techniques && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Techniques Used:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {selectedAgent.prompt_enhancement_techniques.techniques_used?.map((technique, index) => (
                            <Chip
                              key={index}
                              label={technique}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Original Prompt
                    </Typography>
                    <Box
                      sx={{
                        p: 2,
                        backgroundColor: 'rgba(0, 0, 0, 0.2)',
                        borderRadius: 1,
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                        mb: 2,
                      }}
                    >
                      {selectedAgent.original_prompt}
                    </Box>
                    
                    <Typography variant="h6" gutterBottom>
                      Enhanced Prompt
                    </Typography>
                    <Box
                      sx={{
                        p: 2,
                        backgroundColor: 'rgba(0, 0, 0, 0.2)',
                        borderRadius: 1,
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                        maxHeight: 300,
                        overflow: 'auto',
                      }}
                    >
                      {selectedAgent.enhanced_prompt || 'No enhanced prompt available'}
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDetails}>Close</Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default AgentStatusMonitor;

