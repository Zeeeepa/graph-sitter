/**
 * Project Dashboard Component - Main dashboard for managing projects and workflows
 */
import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Tooltip,
  Fab,
  Badge,
} from '@mui/material';
import {
  PushPin,
  PushPinOutlined,
  GitHub,
  Add,
  Refresh,
  PlayArrow,
  Stop,
  Settings,
  Code,
  BugReport,
  Security,
  Speed,
  Visibility,
  Launch,
  Timeline,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import { apiService } from '../services/api';

const ProjectDashboard = ({ projects, selectedProject, onProjectSelect, onProjectUpdate }) => {
  const navigate = useNavigate();
  const [pinnedProjects, setPinnedProjects] = useState([]);
  const [unpinnedProjects, setUnpinnedProjects] = useState([]);
  const [addProjectOpen, setAddProjectOpen] = useState(false);
  const [newProjectData, setNewProjectData] = useState({
    repository: '',
    requirements: '',
    plan: ''
  });
  const [loading, setLoading] = useState(false);
  const [projectStats, setProjectStats] = useState({});

  useEffect(() => {
    if (projects) {
      const pinned = projects.filter(p => p.is_pinned);
      const unpinned = projects.filter(p => !p.is_pinned);
      setPinnedProjects(pinned);
      setUnpinnedProjects(unpinned);
      
      // Fetch stats for each project
      pinned.forEach(project => {
        fetchProjectStats(project.id);
      });
    }
  }, [projects]);

  const fetchProjectStats = async (projectId) => {
    try {
      const [workflows, agents, analysis] = await Promise.all([
        apiService.getWorkflows(projectId),
        apiService.getActiveAgents(projectId),
        apiService.getAnalysisResults(projectId)
      ]);

      setProjectStats(prev => ({
        ...prev,
        [projectId]: {
          activeWorkflows: workflows.filter(w => w.status === 'running').length,
          totalWorkflows: workflows.length,
          activeAgents: agents.length,
          analysisIssues: analysis.reduce((acc, issue) => {
            acc[issue.severity] = (acc[issue.severity] || 0) + 1;
            return acc;
          }, {})
        }
      }));
    } catch (error) {
      console.error(`Error fetching stats for project ${projectId}:`, error);
    }
  };

  const handlePinToggle = async (project) => {
    try {
      setLoading(true);
      
      if (project.is_pinned) {
        await apiService.unpinProject(project.id);
      } else {
        await apiService.pinProject(project.id);
      }
      
      // Update local state
      const updatedProjects = projects.map(p => 
        p.id === project.id ? { ...p, is_pinned: !p.is_pinned } : p
      );
      onProjectUpdate(updatedProjects);
      
    } catch (error) {
      console.error('Error toggling pin:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProject = async () => {
    try {
      setLoading(true);
      
      const projectData = {
        ...newProjectData,
        is_pinned: true
      };
      
      const newProject = await apiService.createProject(projectData);
      
      // Update projects list
      const updatedProjects = [...projects, newProject];
      onProjectUpdate(updatedProjects);
      
      // Reset form
      setNewProjectData({ repository: '', requirements: '', plan: '' });
      setAddProjectOpen(false);
      
    } catch (error) {
      console.error('Error adding project:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProjectClick = (project) => {
    onProjectSelect(project);
    navigate(`/project/${project.id}`);
  };

  const getStatusColor = (status) => {
    const colors = {
      running: 'primary',
      completed: 'success',
      failed: 'error',
      pending: 'default'
    };
    return colors[status] || 'default';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#f44336',
      high: '#ff9800',
      medium: '#2196f3',
      low: '#4caf50'
    };
    return colors[severity] || '#9e9e9e';
  };

  const ProjectCard = ({ project, isPinned = false }) => {
    const stats = projectStats[project.id] || {};
    
    return (
      <Card
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          border: isPinned ? '2px solid #00d4aa' : '1px solid rgba(255, 255, 255, 0.1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 8px 25px rgba(0, 212, 170, 0.3)',
          },
        }}
        onClick={() => handleProjectClick(project)}
      >
        <CardContent sx={{ flexGrow: 1 }}>
          {/* Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" component="div" gutterBottom>
                {project.name}
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                {project.description || 'No description available'}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <GitHub fontSize="small" />
                <Typography variant="caption" color="textSecondary">
                  {project.owner}/{project.repo_name}
                </Typography>
              </Box>
            </Box>
            
            <Tooltip title={isPinned ? 'Unpin project' : 'Pin project'}>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handlePinToggle(project);
                }}
                disabled={loading}
              >
                {isPinned ? <PushPin color="primary" /> : <PushPinOutlined />}
              </IconButton>
            </Tooltip>
          </Box>

          {/* Stats */}
          <Box sx={{ mb: 2 }}>
            <Grid container spacing={1}>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center', p: 1, backgroundColor: 'rgba(0, 212, 170, 0.1)', borderRadius: 1 }}>
                  <Typography variant="h6" color="primary">
                    {stats.activeWorkflows || 0}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Active Workflows
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center', p: 1, backgroundColor: 'rgba(255, 107, 107, 0.1)', borderRadius: 1 }}>
                  <Typography variant="h6" color="secondary">
                    {stats.activeAgents || 0}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Active Agents
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>

          {/* Analysis Issues */}
          {stats.analysisIssues && Object.keys(stats.analysisIssues).length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Code Analysis Issues:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {Object.entries(stats.analysisIssues).map(([severity, count]) => (
                  <Chip
                    key={severity}
                    label={`${severity}: ${count}`}
                    size="small"
                    sx={{
                      backgroundColor: getSeverityColor(severity),
                      color: 'white',
                      fontSize: '0.75rem'
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Requirements Preview */}
          {project.requirements && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Requirements:
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ 
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical'
              }}>
                {project.requirements}
              </Typography>
            </Box>
          )}

          {/* Plan Status */}
          {project.plan && (
            <Box sx={{ mb: 1 }}>
              <Chip
                label="Plan Created"
                color="success"
                size="small"
                icon={<Timeline />}
              />
            </Box>
          )}
        </CardContent>

        <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="View Project">
              <IconButton size="small" color="primary">
                <Visibility />
              </IconButton>
            </Tooltip>
            <Tooltip title="Open GitHub">
              <IconButton 
                size="small" 
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(project.github_url, '_blank');
                }}
              >
                <Launch />
              </IconButton>
            </Tooltip>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            {project.plan ? (
              <Button
                size="small"
                variant="contained"
                color="primary"
                startIcon={<PlayArrow />}
                onClick={(e) => {
                  e.stopPropagation();
                  // Start workflow
                }}
              >
                Start Flow
              </Button>
            ) : (
              <Button
                size="small"
                variant="outlined"
                onClick={(e) => {
                  e.stopPropagation();
                  handleProjectClick(project);
                }}
              >
                Create Plan
              </Button>
            )}
          </Box>
        </CardActions>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            🚀 AI-Powered CI/CD Dashboard
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Manage your projects with intelligent automation and real-time monitoring
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => window.location.reload()}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setAddProjectOpen(true)}
          >
            Add Project
          </Button>
        </Box>
      </Box>

      {/* Pinned Projects */}
      {pinnedProjects.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PushPin color="primary" />
            Pinned Projects ({pinnedProjects.length})
          </Typography>
          <Grid container spacing={3}>
            {pinnedProjects.map((project) => (
              <Grid item xs={12} md={6} lg={4} key={project.id}>
                <ProjectCard project={project} isPinned={true} />
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* All Projects */}
      <Box>
        <Typography variant="h5" gutterBottom>
          All Projects ({projects.length})
        </Typography>
        
        {projects.length === 0 ? (
          <Card sx={{ p: 4, textAlign: 'center' }}>
            <GitHub sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No projects yet
            </Typography>
            <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
              Add your first GitHub repository to get started with AI-powered CI/CD automation
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setAddProjectOpen(true)}
            >
              Add Your First Project
            </Button>
          </Card>
        ) : (
          <Grid container spacing={3}>
            {projects.map((project) => (
              <Grid item xs={12} md={6} lg={4} key={project.id}>
                <ProjectCard project={project} isPinned={project.is_pinned} />
              </Grid>
            ))}
          </Grid>
        )}
      </Box>

      {/* Add Project Dialog */}
      <Dialog
        open={addProjectOpen}
        onClose={() => setAddProjectOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Add New Project</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Select Repository</InputLabel>
              <Select
                value={newProjectData.repository}
                onChange={(e) => setNewProjectData(prev => ({ ...prev, repository: e.target.value }))}
                label="Select Repository"
              >
                {unpinnedProjects.map((repo) => (
                  <MenuItem key={repo.id} value={repo.full_name}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <GitHub fontSize="small" />
                      {repo.full_name}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              multiline
              rows={4}
              label="Project Requirements"
              placeholder="Describe what you want to achieve with this project..."
              value={newProjectData.requirements}
              onChange={(e) => setNewProjectData(prev => ({ ...prev, requirements: e.target.value }))}
              sx={{ mb: 3 }}
            />

            <TextField
              fullWidth
              multiline
              rows={6}
              label="Execution Plan (Optional)"
              placeholder="AI will generate a plan if left empty..."
              value={newProjectData.plan}
              onChange={(e) => setNewProjectData(prev => ({ ...prev, plan: e.target.value }))}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddProjectOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleAddProject}
            variant="contained"
            disabled={!newProjectData.repository || loading}
          >
            Add Project
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button for Quick Add */}
      <Fab
        color="primary"
        aria-label="add project"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
        }}
        onClick={() => setAddProjectOpen(true)}
      >
        <Add />
      </Fab>
    </Box>
  );
};

export default ProjectDashboard;

