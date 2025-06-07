import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tabs,
  Tab,
  Box,
  TextField,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
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

const ProjectDialog: React.FC<ProjectDialogProps> = ({ open, project, onClose, onSave }) => {
  const [tabValue, setTabValue] = useState(0);
  const [requirements, setRequirements] = useState(project?.requirements || '');

  if (!project) return null;

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSave = () => {
    const updatedProject = {
      ...project,
      requirements
    };
    onSave(updatedProject);
  };

  const handleGeneratePlan = () => {
    // Mock plan generation
    console.log('Generating plan for:', requirements);
  };

  const handleStartFlow = () => {
    // Mock flow start
    console.log('Starting flow for project:', project.name);
  };

  const getTaskStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'in_progress':
        return <PlayIcon color="primary" />;
      case 'pending':
        return <ScheduleIcon color="action" />;
      default:
        return <ErrorIcon color="error" />;
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h5">{project.name}</Typography>
        <Typography variant="body2" color="text.secondary">
          {project.repository}
        </Typography>
      </DialogTitle>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="project tabs">
          <Tab label="Requirements" />
          <Tab label="Plan" />
          <Tab label="Progress" />
        </Tabs>
      </Box>
      
      <DialogContent sx={{ minHeight: 400 }}>
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Project Requirements
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={8}
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            placeholder="Enter detailed project requirements and instructions..."
            variant="outlined"
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            onClick={handleGeneratePlan}
            disabled={!requirements.trim()}
          >
            Generate Plan
          </Button>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Execution Plan
          </Typography>
          {project.plan ? (
            <>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {project.plan.description}
              </Typography>
              <List>
                {project.plan.tasks.map((task) => (
                  <ListItem key={task.id}>
                    <ListItemIcon>
                      {getTaskStatusIcon(task.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={task.title}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {task.description}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                            <Chip label={task.status} size="small" />
                            <Chip label={`${task.estimatedHours}h estimated`} size="small" variant="outlined" />
                            {task.assignee && (
                              <Chip label={task.assignee} size="small" variant="outlined" />
                            )}
                          </Box>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
              <Divider sx={{ my: 2 }} />
              <Button
                variant="contained"
                color="success"
                onClick={handleStartFlow}
                startIcon={<PlayIcon />}
              >
                Start Flow
              </Button>
            </>
          ) : (
            <Typography color="text.secondary">
              No plan generated yet. Go to Requirements tab to create one.
            </Typography>
          )}
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Project Progress
          </Typography>
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Overall Progress</Typography>
              <Typography variant="body2">{project.progress}%</Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={project.progress} 
              sx={{ height: 10, borderRadius: 5 }}
            />
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Chip 
              label={`Status: ${project.status}`} 
              color={project.status === 'active' ? 'success' : 'default'}
            />
            <Chip 
              label={`Flow: ${project.flowStatus}`} 
              color={project.flowStatus === 'running' ? 'success' : 'error'}
              variant="outlined"
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary">
            Last activity: {project.lastActivity.toLocaleString()}
          </Typography>
        </TabPanel>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained">
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectDialog;
