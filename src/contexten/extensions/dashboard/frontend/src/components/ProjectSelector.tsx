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
  InputAdornment,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Star as StarIcon,
  Search as SearchIcon,
  GitHub as GitHubIcon,
  Code as CodeIcon,
  Timeline as TimelineIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { Project } from '../types/dashboard';
import { useProject } from '../hooks/useProject';
import { useSettings } from '../contexts/SettingsContext';

interface ProjectSelectorProps {
  open: boolean;
  onClose: () => void;
}

export const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  open,
  onClose,
}) => {
  const { settings } = useSettings();
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
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  useEffect(() => {
    if (!open) {
      setSearchTerm('');
      setSelectedProject(null);
      setMetrics(null);
    }
  }, [open]);

  useEffect(() => {
    setFilteredProjects(
      projects.filter(project =>
        project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [searchTerm, projects]);

  const handleProjectSelect = async (project: Project) => {
    setSelectedProject(project);
    setLoadingMetrics(true);
    try {
      const projectMetrics = await getProjectMetrics(project.id);
      setMetrics({
        codeQuality: projectMetrics.codeQuality,
        performance: projectMetrics.workflowSuccessRate,
        activity: projectMetrics.activeContributors,
        issues: projectMetrics.openIssues,
      });
    } catch (err) {
      console.error('Error fetching project metrics:', err);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const handlePin = async () => {
    if (!selectedProject) return;
    try {
      await pinProject(selectedProject.id);
      onClose();
    } catch (err) {
      console.error('Error pinning project:', err);
    }
  };

  if (!settings.githubToken) {
    return (
      <Dialog open={open} onClose={onClose}>
        <DialogContent>
          <Alert severity="warning">
            Please configure your GitHub token in settings first.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          height: '80vh',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <GitHubIcon />
          <Typography variant="h6">Select Project to Pin</Typography>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ display: 'flex', p: 0 }}>
        <Box
          sx={{
            width: '40%',
            borderRight: theme => `1px solid ${theme.palette.divider}`,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box sx={{ p: 2 }}>
            <TextField
              fullWidth
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Box>

          {loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : error ? (
            <Alert severity="error" sx={{ m: 2 }}>
              {error}
            </Alert>
          ) : (
            <List sx={{ overflow: 'auto', flex: 1 }}>
              {filteredProjects.map((project) => (
                <ListItem
                  key={project.id}
                  button
                  selected={selectedProject?.id === project.id}
                  onClick={() => handleProjectSelect(project)}
                >
                  <ListItemText
                    primary={project.name}
                    secondary={project.description}
                  />
                  {project.pinned && (
                    <ListItemSecondaryAction>
                      <Tooltip title="Already pinned">
                        <StarIcon color="primary" />
                      </Tooltip>
                    </ListItemSecondaryAction>
                  )}
                </ListItem>
              ))}
            </List>
          )}
        </Box>

        <Box
          sx={{
            width: '60%',
            p: 3,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {selectedProject ? (
            <>
              <Typography variant="h6" gutterBottom>
                {selectedProject.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {selectedProject.description}
              </Typography>

              <Box display="flex" gap={1} mb={2}>
                {selectedProject.tags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" />
                ))}
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Repository Information
              </Typography>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <GitHubIcon fontSize="small" />
                <Typography variant="body2">
                  {selectedProject.repository}
                </Typography>
              </Box>

              {loadingMetrics ? (
                <Box display="flex" justifyContent="center" p={4}>
                  <CircularProgress />
                </Box>
              ) : metrics ? (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    Project Metrics
                  </Typography>
                  <Box display="flex" gap={2} mb={2}>
                    <Chip
                      icon={<CodeIcon />}
                      label={`Code Quality: ${metrics.codeQuality}%`}
                    />
                    <Chip
                      icon={<TimelineIcon />}
                      label={`Performance: ${metrics.performance}%`}
                    />
                    <Chip
                      icon={<InfoIcon />}
                      label={`Open Issues: ${metrics.issues}`}
                    />
                  </Box>
                </>
              ) : null}
            </>
          ) : (
            <Box
              display="flex"
              alignItems="center"
              justifyContent="center"
              height="100%"
              color="text.secondary"
            >
              <Typography>Select a project to view details</Typography>
            </Box>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handlePin}
          disabled={!selectedProject || selectedProject.pinned}
          startIcon={<StarIcon />}
        >
          Pin Project
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectSelector;

