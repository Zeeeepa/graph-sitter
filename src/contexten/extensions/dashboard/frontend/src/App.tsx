import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Box,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  CircularProgress,
} from '@mui/material';
import ProjectCard from './components/ProjectCard';
import { Project } from './types/dashboard';

const App: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading data
    setTimeout(() => {
      loadMockData();
      setIsLoading(false);
    }, 1000);
  }, []);

  const loadMockData = () => {
    const mockProjects: Project[] = [
      {
        id: '1',
        name: 'AI Dashboard System',
        description: 'Complete dashboard for AI-powered development workflows',
        repository: 'https://github.com/Zeeeepa/graph-sitter',
        status: 'active',
        progress: 75,
        flowEnabled: true,
        flowStatus: 'running',
        lastActivity: new Date(),
        tags: ['dashboard', 'react', 'typescript'],
        metrics: {
          commits: 156,
          prs: 23,
          contributors: 8,
          issues: 45
        },
        requirements: 'Build a comprehensive dashboard system with React and Material-UI',
        plan: {
          id: 'plan-1',
          projectId: '1',
          title: 'Dashboard Implementation Plan',
          description: 'Complete implementation of the dashboard system',
          tasks: [
            {
              id: 'task-1',
              title: 'Setup React Frontend',
              description: 'Initialize React app with Material-UI',
              status: 'completed',
              assignee: 'AI Agent',
              estimatedHours: 4,
              actualHours: 3,
              dependencies: [],
              createdAt: new Date(),
              updatedAt: new Date()
            },
            {
              id: 'task-2',
              title: 'Implement Dashboard Components',
              description: 'Create all necessary UI components',
              status: 'in_progress',
              assignee: 'AI Agent',
              estimatedHours: 8,
              actualHours: 6,
              dependencies: ['task-1'],
              createdAt: new Date(),
              updatedAt: new Date()
            }
          ],
          status: 'in_progress',
          createdAt: new Date(),
          updatedAt: new Date()
        }
      },
      {
        id: '2',
        name: 'Code Analysis Engine',
        description: 'Advanced code analysis and manipulation system',
        repository: 'https://github.com/Zeeeepa/graph-sitter',
        status: 'paused',
        progress: 45,
        flowEnabled: false,
        flowStatus: 'stopped',
        lastActivity: new Date(Date.now() - 86400000), // 1 day ago
        tags: ['analysis', 'tree-sitter', 'typescript'],
        metrics: {
          commits: 89,
          prs: 12,
          contributors: 5,
          issues: 28
        },
        requirements: 'Implement graph-sitter based code analysis'
      },
      {
        id: '3',
        name: 'Workflow Orchestrator',
        description: 'Orchestration system for development workflows',
        repository: 'https://github.com/Zeeeepa/contexten',
        status: 'completed',
        progress: 100,
        flowEnabled: true,
        flowStatus: 'stopped',
        lastActivity: new Date(Date.now() - 172800000), // 2 days ago
        tags: ['workflow', 'automation', 'typescript'],
        metrics: {
          commits: 234,
          prs: 45,
          contributors: 12,
          issues: 67
        },
        requirements: 'Create workflow orchestration with webhook integrations'
      }
    ];

    setProjects(mockProjects);
  };

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project);
  };

  const handleDialogClose = () => {
    setSelectedProject(null);
  };

  const handleProjectPin = (projectName: string) => {
    // Mock project pinning
    const newProject: Project = {
      id: Date.now().toString(),
      name: projectName,
      description: `Pinned project: ${projectName}`,
      repository: 'https://github.com/example/repo',
      status: 'active',
      progress: 0,
      flowEnabled: false,
      flowStatus: 'stopped',
      lastActivity: new Date(),
      tags: ['pinned'],
      metrics: {
        commits: 0,
        prs: 0,
        contributors: 1
      }
    };

    setProjects([...projects, newProject]);
  };

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Project Dashboard
        </Typography>

        <Grid container spacing={3}>
          {projects.map((project) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={project.id}>
              <ProjectCard
                project={project}
                onPin={() => handleProjectPin(project.name)}
              />
            </Grid>
          ))}
        </Grid>

        <Dialog
          open={Boolean(selectedProject)}
          onClose={handleDialogClose}
          maxWidth="md"
          fullWidth
        >
          {selectedProject && (
            <>
              <DialogTitle>{selectedProject.name}</DialogTitle>
              <DialogContent>
                <Typography gutterBottom>
                  {selectedProject.description}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Repository: {selectedProject.repository}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Status: {selectedProject.status}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Progress: {selectedProject.progress}%
                </Typography>
              </DialogContent>
              <DialogActions>
                <Button onClick={handleDialogClose}>Close</Button>
              </DialogActions>
            </>
          )}
        </Dialog>
      </Box>
    </Container>
  );
};

export default App;

