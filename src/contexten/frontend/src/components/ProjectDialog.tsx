import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  Typography,
  IconButton,
  InputAdornment,
  SelectChangeEvent,
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { Project } from '../types/dashboard';

interface ProjectDialogProps {
  open: boolean;
  project: Project | null;
  onClose: () => void;
  onSave: (project: Project) => void;
}

const ProjectDialog: React.FC<ProjectDialogProps> = ({
  open,
  project,
  onClose,
  onSave,
}) => {
  const [formData, setFormData] = useState<Partial<Project>>({
    name: '',
    description: '',
    repository: '',
    status: 'active',
    progress: 0,
    flowEnabled: false,
    flowStatus: 'stopped',
    tags: [],
    metrics: {
      commits: 0,
      prs: 0,
      contributors: 0,
      issues: 0,
    },
  });

  const [newTag, setNewTag] = useState('');

  useEffect(() => {
    if (project) {
      setFormData(project);
    } else {
      setFormData({
        name: '',
        description: '',
        repository: '',
        status: 'active',
        progress: 0,
        flowEnabled: false,
        flowStatus: 'stopped',
        tags: [],
        metrics: {
          commits: 0,
          prs: 0,
          contributors: 0,
          issues: 0,
        },
      });
    }
  }, [project]);

  const handleChange = (field: keyof Project) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | SelectChangeEvent
  ) => {
    setFormData((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleSelectChange = (field: keyof Project) => (
    event: any
  ) => {
    setFormData((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleAddTag = () => {
    if (newTag && !formData.tags?.includes(newTag)) {
      setFormData((prev) => ({
        ...prev,
        tags: [...(prev.tags || []), newTag],
      }));
      setNewTag('');
    }
  };

  const handleDeleteTag = (tagToDelete: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags?.filter((tag) => tag !== tagToDelete),
    }));
  };

  const handleSubmit = () => {
    if (formData.name && formData.repository) {
      onSave({
        id: project?.id || Date.now().toString(),
        lastActivity: project?.lastActivity || new Date(),
        ...formData,
      } as Project);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {project ? 'Edit Project' : 'Create New Project'}
      </DialogTitle>
      <DialogContent>
        <Grid container spacing={3} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              label="Project Name"
              value={formData.name}
              onChange={handleChange('name')}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Description"
              value={formData.description}
              onChange={handleChange('description')}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              required
              label="Repository URL"
              value={formData.repository}
              onChange={handleChange('repository')}
            />
          </Grid>

          <Grid item xs={6}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                label="Status"
                onChange={handleChange('status')}
              >
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="paused">Paused</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="error">Error</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={6}>
            <TextField
              fullWidth
              type="number"
              label="Progress"
              value={formData.progress}
              onChange={handleChange('progress')}
              InputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>,
              }}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              Tags
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
              <TextField
                label="Add Tag"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
              />
              <Button
                variant="contained"
                onClick={handleAddTag}
                startIcon={<AddIcon />}
              >
                Add
              </Button>
            </Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {formData.tags?.map((tag) => (
                <Chip
                  key={tag}
                  label={tag}
                  onDelete={() => handleDeleteTag(tag)}
                  deleteIcon={<CloseIcon />}
                />
              ))}
            </Box>
          </Grid>

          {project && (
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Metrics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={3}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Commits"
                    value={formData.metrics?.commits || 0}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        metrics: { 
                          commits: Number(e.target.value),
                          prs: prev.metrics?.prs || 0,
                          contributors: prev.metrics?.contributors || 0,
                          issues: prev.metrics?.issues || 0
                        },
                      }))
                    }
                  />
                </Grid>
                <Grid item xs={3}>
                  <TextField
                    fullWidth
                    type="number"
                    label="PRs"
                    value={formData.metrics?.prs || 0}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        metrics: { 
                          commits: prev.metrics?.commits || 0,
                          prs: Number(e.target.value),
                          contributors: prev.metrics?.contributors || 0,
                          issues: prev.metrics?.issues || 0
                        },
                      }))
                    }
                  />
                </Grid>
                <Grid item xs={3}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Contributors"
                    value={formData.metrics?.contributors || 0}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        metrics: { 
                          commits: prev.metrics?.commits || 0,
                          prs: prev.metrics?.prs || 0,
                          contributors: Number(e.target.value),
                          issues: prev.metrics?.issues || 0
                        },
                      }))
                    }
                  />
                </Grid>
                <Grid item xs={3}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Issues"
                    value={formData.metrics?.issues || 0}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        metrics: { 
                          commits: prev.metrics?.commits || 0,
                          prs: prev.metrics?.prs || 0,
                          contributors: prev.metrics?.contributors || 0,
                          issues: Number(e.target.value)
                        },
                      }))
                    }
                  />
                </Grid>
              </Grid>
            </Grid>
          )}
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          disabled={!formData.name || !formData.repository}
        >
          {project ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectDialog;
