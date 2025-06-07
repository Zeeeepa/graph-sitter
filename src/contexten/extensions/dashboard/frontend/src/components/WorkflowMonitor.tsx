import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Paper
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
  BugReport as BugIcon,
  Build as BuildIcon
} from '@mui/icons-material';

interface WorkflowStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  logs?: string[];
  error?: string;
}

interface WorkflowExecution {
  id: string;
  projectId: string;
  projectName: string;
  status: 'running' | 'completed' | 'failed' | 'paused';
  startTime: Date;
  endTime?: Date;
  steps: WorkflowStep[];
  progress: number;
  totalSteps: number;
  completedSteps: number;
}

interface WorkflowMonitorProps {
  projectId?: string;
  onRefresh?: () => void;
}

export const WorkflowMonitor: React.FC<WorkflowMonitorProps> = ({
  projectId,
  onRefresh
}) => {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedExecution, setExpandedExecution] = useState<string | null>(null);

  // Mock data for demonstration
  useEffect(() => {
    const mockExecutions: WorkflowExecution[] = [
      {
        id: 'exec-1',
        projectId: 'proj-1',
        projectName: 'Graph Sitter Dashboard',
        status: 'running',
        startTime: new Date(Date.now() - 300000), // 5 minutes ago
        steps: [
          {
            id: 'step-1',
            name: 'Code Analysis',
            status: 'completed',
            startTime: new Date(Date.now() - 300000),
            endTime: new Date(Date.now() - 240000),
            duration: 60000
          },
          {
            id: 'step-2',
            name: 'Generate Plan',
            status: 'completed',
            startTime: new Date(Date.now() - 240000),
            endTime: new Date(Date.now() - 180000),
            duration: 60000
          },
          {
            id: 'step-3',
            name: 'Create Linear Issues',
            status: 'running',
            startTime: new Date(Date.now() - 180000)
          },
          {
            id: 'step-4',
            name: 'Execute Tasks',
            status: 'pending'
          },
          {
            id: 'step-5',
            name: 'Quality Gates',
            status: 'pending'
          }
        ],
        progress: 40,
        totalSteps: 5,
        completedSteps: 2
      },
      {
        id: 'exec-2',
        projectId: 'proj-2',
        projectName: 'Contexten Core',
        status: 'completed',
        startTime: new Date(Date.now() - 3600000), // 1 hour ago
        endTime: new Date(Date.now() - 1800000), // 30 minutes ago
        steps: [
          {
            id: 'step-1',
            name: 'Code Analysis',
            status: 'completed',
            duration: 45000
          },
          {
            id: 'step-2',
            name: 'Generate Plan',
            status: 'completed',
            duration: 30000
          },
          {
            id: 'step-3',
            name: 'Execute Tasks',
            status: 'completed',
            duration: 900000
          }
        ],
        progress: 100,
        totalSteps: 3,
        completedSteps: 3
      }
    ];

    setExecutions(mockExecutions);
  }, [projectId]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'paused': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <PlayIcon />;
      case 'completed': return <CheckIcon />;
      case 'failed': return <ErrorIcon />;
      case 'paused': return <PauseIcon />;
      default: return <ScheduleIcon />;
    }
  };

  const getStepIcon = (stepName: string) => {
    if (stepName.toLowerCase().includes('analysis')) return <CodeIcon />;
    if (stepName.toLowerCase().includes('test') || stepName.toLowerCase().includes('quality')) return <BugIcon />;
    if (stepName.toLowerCase().includes('build') || stepName.toLowerCase().includes('execute')) return <BuildIcon />;
    return <TimelineIcon />;
  };

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const handleRefresh = () => {
    setLoading(true);
    if (onRefresh) {
      onRefresh();
    }
    setTimeout(() => setLoading(false), 1000);
  };

  return (
    <Card elevation={2}>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <TimelineIcon />
            <Typography variant="h6">Workflow Monitor</Typography>
          </Box>
        }
        action={
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        }
      />
      <CardContent>
        {executions.length === 0 ? (
          <Alert severity="info">
            No active workflows. Start a project flow to see execution details.
          </Alert>
        ) : (
          <Box>
            {executions.map((execution) => (
              <Accordion
                key={execution.id}
                expanded={expandedExecution === execution.id}
                onChange={(_, isExpanded) => 
                  setExpandedExecution(isExpanded ? execution.id : null)
                }
                sx={{ mb: 2 }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Grid container alignItems="center" spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getStatusIcon(execution.status)}
                        <Typography variant="subtitle1" fontWeight="medium">
                          {execution.projectName}
                        </Typography>
                        <Chip
                          label={execution.status}
                          color={getStatusColor(execution.status)}
                          size="small"
                        />
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Progress: {execution.completedSteps}/{execution.totalSteps} steps
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={execution.progress}
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionSummary>
                <AccordionDetails>
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Execution Steps:
                    </Typography>
                    <List dense>
                      {execution.steps.map((step, index) => (
                        <ListItem key={step.id}>
                          <ListItemIcon>
                            <Box display="flex" alignItems="center" gap={1}>
                              <Typography variant="body2" color="text.secondary">
                                {index + 1}.
                              </Typography>
                              {getStepIcon(step.name)}
                            </Box>
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box display="flex" alignItems="center" gap={1}>
                                <Typography variant="body2">
                                  {step.name}
                                </Typography>
                                <Chip
                                  label={step.status}
                                  color={getStatusColor(step.status)}
                                  size="small"
                                />
                              </Box>
                            }
                            secondary={
                              step.duration ? (
                                <Typography variant="caption" color="text.secondary">
                                  Duration: {formatDuration(step.duration)}
                                </Typography>
                              ) : step.status === 'running' ? (
                                <Typography variant="caption" color="primary">
                                  Running...
                                </Typography>
                              ) : null
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                    
                    {execution.status === 'failed' && (
                      <Alert severity="error" sx={{ mt: 2 }}>
                        <Typography variant="body2">
                          Workflow failed. Check individual step logs for details.
                        </Typography>
                      </Alert>
                    )}
                    
                    <Paper variant="outlined" sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
                      <Typography variant="caption" color="text.secondary">
                        Started: {execution.startTime.toLocaleString()}
                        {execution.endTime && (
                          <> • Completed: {execution.endTime.toLocaleString()}</>
                        )}
                      </Typography>
                    </Paper>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

