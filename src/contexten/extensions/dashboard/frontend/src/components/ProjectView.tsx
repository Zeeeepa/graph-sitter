import React from 'react';
import {
  Box,
  Typography,
  Container,
  Paper,
  Button,
  Chip,
  Grid,
  Card,
  CardContent,
  LinearProgress,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  PlayArrow as PlayIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';

import { useDashboardStore } from '../store/dashboardStore';

const ProjectView: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { selectedProject } = useDashboardStore();

  // Mock data for demonstration
  const mockWorkflows = [
    {
      id: '1',
      title: 'Feature Implementation',
      status: 'running',
      progress: 65,
      tasks: 8,
      completedTasks: 5,
    },
    {
      id: '2', 
      title: 'Bug Fix Workflow',
      status: 'completed',
      progress: 100,
      tasks: 3,
      completedTasks: 3,
    },
  ];

  const handleBack = () => {
    navigate('/dashboard');
  };

  if (!selectedProject) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ py: 4, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Project not found
          </Typography>
          <Button onClick={handleBack} startIcon={<ArrowBackIcon />}>
            Back to Dashboard
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Button 
          onClick={handleBack} 
          startIcon={<ArrowBackIcon />}
          sx={{ mb: 2 }}
        >
          Back to Dashboard
        </Button>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              {selectedProject.name}
            </Typography>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {selectedProject.full_name}
            </Typography>
            {selectedProject.description && (
              <Typography variant="body2" color="text.secondary">
                {selectedProject.description}
              </Typography>
            )}
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip 
              label={selectedProject.status} 
              color={selectedProject.status === 'active' ? 'success' : 'default'}
            />
            {selectedProject.language && (
              <Chip label={selectedProject.language} variant="outlined" />
            )}
          </Box>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Workflows Section */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Active Workflows
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                size="small"
              >
                Create Workflow
              </Button>
            </Box>
            
            {mockWorkflows.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary" gutterBottom>
                  No workflows found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Create your first workflow to get started
                </Typography>
              </Box>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {mockWorkflows.map((workflow) => (
                  <Card key={workflow.id} variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box>
                          <Typography variant="h6" gutterBottom>
                            {workflow.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {workflow.completedTasks} of {workflow.tasks} tasks completed
                          </Typography>
                        </Box>
                        <Chip 
                          label={workflow.status}
                          color={workflow.status === 'completed' ? 'success' : 'primary'}
                          size="small"
                        />
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Progress
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {workflow.progress}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={workflow.progress}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                      
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button size="small" startIcon={<PlayIcon />}>
                          View Details
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Project Info Sidebar */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Project Information
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Default Branch
                </Typography>
                <Typography variant="body1">
                  {selectedProject.default_branch}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Repository URL
                </Typography>
                <Typography 
                  variant="body1" 
                  component="a" 
                  href={selectedProject.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ color: 'primary.main', textDecoration: 'none' }}
                >
                  View on GitHub
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Created
                </Typography>
                <Typography variant="body1">
                  {new Date(selectedProject.created_at).toLocaleDateString()}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Last Updated
                </Typography>
                <Typography variant="body1">
                  {new Date(selectedProject.updated_at).toLocaleDateString()}
                </Typography>
              </Box>
            </Box>
          </Paper>

          {/* Quick Actions */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Button variant="outlined" fullWidth>
                Create New Workflow
              </Button>
              <Button variant="outlined" fullWidth>
                View GitHub Issues
              </Button>
              <Button variant="outlined" fullWidth>
                Open in Linear
              </Button>
              <Button variant="outlined" fullWidth>
                Project Settings
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ProjectView;

