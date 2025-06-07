import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface ProjectDialogProps {
  open: boolean;
  project: Project | null;
  onClose: () => void;
  onSave: (project: Project) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export const ProjectDialog: React.FC<ProjectDialogProps> = ({
  open,
  project,
  onClose,
  onSave
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [requirements, setRequirements] = useState('');
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);

  useEffect(() => {
    if (project) {
      setRequirements(project.requirements || '');
    }
  }, [project]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleGeneratePlan = async () => {
    if (!project || !requirements.trim()) return;

    setIsGeneratingPlan(true);
    try {
      // Simulate plan generation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockPlan = {
        id: `plan-${Date.now()}`,
        projectId: project.id,
        requirements,
        tasks: [
          {
            id: 'task-1',
            title: 'Analyze Requirements',
            description: 'Break down requirements into actionable tasks',
            status: 'pending' as const,
            assignee: 'codegen-bot',
            estimatedHours: 2
          },
          {
            id: 'task-2',
            title: 'Design Implementation',
            description: 'Create technical design and architecture',
            status: 'pending' as const,
            assignee: 'codegen-bot',
            estimatedHours: 4
          },
          {
            id: 'task-3',
            title: 'Implement Features',
            description: 'Code the required functionality',
            status: 'pending' as const,
            assignee: 'codegen-bot',
            estimatedHours: 8
          },
          {
            id: 'task-4',
            title: 'Testing & QA',
            description: 'Write tests and ensure quality',
            status: 'pending' as const,
            assignee: 'codegen-bot',
            estimatedHours: 3
          }
        ],
        createdAt: new Date(),
        updatedAt: new Date()
      };

      const updatedProject = {
        ...project,
        requirements,
        plan: mockPlan
      };

      onSave(updatedProject);
    } catch (error) {
      console.error('Failed to generate plan:', error);
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const handleStartFlow = async () => {
    if (!project) return;

    try {
      const updatedProject = {
        ...project,
        flowEnabled: true,
        status: 'active' as const
      };

      onSave(updatedProject);
    } catch (error) {
      console.error('Failed to start flow:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'in_progress':
        return <ScheduleIcon color="primary" />;
      case 'pending':
        return <AssignmentIcon color="action" />;
      default:
        return <ErrorIcon color="error" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'pending':
        return 'default';
      default:
        return 'error';
    }
  };

  if (!project) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2 }
      }}
    >
      <DialogTitle>
        <Typography variant="h5" component="div">
          {project.name}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {project.repository}
        </Typography>
      </DialogTitle>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Requirements" />
          <Tab label="Plan" disabled={!project.plan} />
          <Tab label="Progress" />
        </Tabs>
      </Box>

      <DialogContent sx={{ p: 0 }}>
        <TabPanel value={activeTab} index={0}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Project Requirements
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Describe what you want to achieve with this project. Be specific about features, 
              improvements, or fixes needed.
            </Typography>
            
            <TextField
              fullWidth
              multiline
              rows={6}
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="Enter your project requirements here..."
              variant="outlined"
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleGeneratePlan}
                disabled={!requirements.trim() || isGeneratingPlan}
                startIcon={isGeneratingPlan ? <ScheduleIcon /> : <AssignmentIcon />}
              >
                {isGeneratingPlan ? 'Generating Plan...' : 'Generate Plan'}
              </Button>
              
              {project.plan && (
                <Button
                  variant="outlined"
                  onClick={handleStartFlow}
                  startIcon={<PlayArrowIcon />}
                  disabled={project.flowEnabled}
                >
                  {project.flowEnabled ? 'Flow Active' : 'Start Flow'}
                </Button>
              )}
            </Box>

            {isGeneratingPlan && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Analyzing requirements and generating execution plan...
                </Typography>
              </Box>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {project.plan ? (
            <Box>
              <Typography variant="h6" gutterBottom>
                Execution Plan
              </Typography>
              
              <Alert severity="info" sx={{ mb: 2 }}>
                Plan generated on {project.plan.createdAt.toLocaleDateString()}
              </Alert>

              <Card variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Requirements
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {project.plan.requirements}
                  </Typography>
                </CardContent>
              </Card>

              <Typography variant="subtitle1" gutterBottom>
                Tasks ({project.plan.tasks.length})
              </Typography>
              
              <List>
                {project.plan.tasks.map((task, index) => (
                  <React.Fragment key={task.id}>
                    <ListItem>
                      <ListItemIcon>
                        {getStatusIcon(task.status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle2">
                              {task.title}
                            </Typography>
                            <Chip
                              label={task.status.replace('_', ' ')}
                              size="small"
                              color={getStatusColor(task.status) as any}
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {task.description}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Assignee: {task.assignee} • Estimated: {task.estimatedHours}h
                              {task.actualHours && ` • Actual: ${task.actualHours}h`}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < project.plan.tasks.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <AssignmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No Plan Generated
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Go to the Requirements tab and generate a plan first.
              </Typography>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Project Progress
            </Typography>
            
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Overall Progress</Typography>
                  <Typography variant="body2">{project.progress}%</Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={project.progress} 
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </CardContent>
            </Card>

            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h4" color="primary">
                    {project.status === 'active' ? 'Active' : 'Inactive'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Current Status
                  </Typography>
                </CardContent>
              </Card>

              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h4" color="success.main">
                    {project.flowEnabled ? 'On' : 'Off'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Flow Status
                  </Typography>
                </CardContent>
              </Card>

              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h4">
                    {project.lastActivity ? 
                      Math.floor((Date.now() - project.lastActivity.getTime()) / (1000 * 60)) + 'm' 
                      : 'N/A'
                    }
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Last Activity
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          </Box>
        </TabPanel>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

