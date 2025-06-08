import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  TextField,
  Box,
  Typography,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Star as StarIcon,
  Search as SearchIcon,
  GitHub as GitHubIcon,
  Code as CodeIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { Project } from '../types/dashboard';
import { useProject } from '../hooks/useProject';

interface ProjectSelectorProps {
  open: boolean;
  onClose: () => void;
  onSelect: (project: Project) => void;
}

export const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  open,
  onClose,
  onSelect,
}) => {
  const { projects, loading, error, pinProject, getProjectMetrics } = useProject();
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredProjects, setFilteredProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [metrics, setMetrics] = useState<{
    codeQuality: number;
    performance: number;
    activity: number;
    issues: number;
  } | null>(null);

  useEffect(() => {
    setFilteredProjects(
      projects.filter(project =>
        project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    );
  }, [projects, searchTerm]);

  const handleProjectSelect = async (project: Project) => {
    setSelectedProject(project);
    const projectMetrics = await getProjectMetrics(project.id);
    setMetrics(projectMetrics);
  };

  const handleConfirm = () => {
    if (selectedProject) {
      onSelect(selectedProject);
      onClose();
    }
  };

  const handlePin = async (project: Project) => {
    await pinProject(project.id);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          height: '80vh',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <GitHubIcon />
          <Typography variant="h6">Select Project to Pin</Typography>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          fullWidth
          placeholder="Search projects..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
        />

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ display: 'flex', gap: 2, height: '100%' }}>
            <List sx={{ flex: 1, overflow: 'auto' }}>
              {filteredProjects.map((project) => (
                <ListItem
                  key={project.id}
                  button
                  selected={selectedProject?.id === project.id}
                  onClick={() => handleProjectSelect(project)}
                >
                  <ListItemText
                    primary={project.name}
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          {project.description}
                        </Typography>
                        <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {project.tags.map((tag) => (
                            <Chip
                              key={tag}
                              label={tag}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => handlePin(project)}
                      color={project.pinned ? 'primary' : 'default'}
                    >
                      <StarIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>

            {selectedProject && (
              <Box
                sx={{
                  width: 300,
                  p: 2,
                  borderLeft: 1,
                  borderColor: 'divider',
                  overflow: 'auto',
                }}
              >
                <Typography variant="h6" gutterBottom>
                  Project Details
                </Typography>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Repository
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <GitHubIcon fontSize="small" />
                    <Typography variant="body2">
                      {selectedProject.repository}
                    </Typography>
                  </Box>
                </Box>

                {metrics && (
                  <>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Metrics
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CodeIcon fontSize="small" />
                        <Typography variant="body2">
                          Code Quality: {metrics.codeQuality}%
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TimelineIcon fontSize="small" />
                        <Typography variant="body2">
                          Performance: {metrics.performance}%
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <StarIcon fontSize="small" />
                        <Typography variant="body2">
                          Activity: {metrics.activity}%
                        </Typography>
                      </Box>
                    </Box>
                  </>
                )}
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          disabled={!selectedProject}
        >
          Select Project
        </Button>
      </DialogActions>
    </Dialog>
  );
};

