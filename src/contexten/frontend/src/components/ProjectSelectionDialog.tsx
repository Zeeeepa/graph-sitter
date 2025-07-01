import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Typography,
  Box,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  GitHub as GitHubIcon,
  Star as StarIcon,
  Close as CloseIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

import { GitHubRepository, ProjectCreateRequest } from '../types';
import { dashboardApi } from '../services/api';

interface ProjectSelectionDialogProps {
  open: boolean;
  onClose: () => void;
  repositories: GitHubRepository[];
}

const ProjectSelectionDialog: React.FC<ProjectSelectionDialogProps> = ({
  open,
  onClose,
  repositories,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRepo, setSelectedRepo] = useState<GitHubRepository | null>(null);
  const [pinning, setPinning] = useState(false);

  const filteredRepositories = repositories.filter(repo =>
    repo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    repo.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    repo.language?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handlePinProject = async (repo: GitHubRepository) => {
    setPinning(true);
    try {
      // First create the project
      const projectData: ProjectCreateRequest = {
        name: repo.name,
        full_name: repo.full_name,
        description: repo.description || '',
        url: repo.url,
        default_branch: repo.default_branch,
        language: repo.language || undefined,
      };

      const projectId = await dashboardApi.createProject(projectData);

      // Then pin it
      await dashboardApi.pinProject({
        project_id: projectId,
        position: 0,
      });

      toast.success(`Successfully pinned ${repo.name}`);
      onClose();
      
      // Refresh the page to show the new project
      window.location.reload();
    } catch (error) {
      toast.error(`Failed to pin ${repo.name}`);
      console.error('Pin project error:', error);
    } finally {
      setPinning(false);
    }
  };

  const getLanguageColor = (language: string) => {
    const colors: Record<string, string> = {
      'TypeScript': '#3178c6',
      'JavaScript': '#f7df1e',
      'Python': '#3776ab',
      'Java': '#ed8b00',
      'Go': '#00add8',
      'Rust': '#000000',
      'C++': '#00599c',
    };
    return colors[language] || '#666666';
  };

  const handleClose = () => {
    setSearchTerm('');
    setSelectedRepo(null);
    onClose();
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h6">Select Project to Pin</Typography>
          <Typography variant="body2" color="text.secondary">
            Choose from your GitHub repositories
          </Typography>
        </Box>
        <IconButton onClick={handleClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {/* Search Bar */}
        <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <TextField
            fullWidth
            placeholder="Search repositories..."
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

        {/* Repository List */}
        <Box sx={{ height: 'calc(80vh - 200px)', overflow: 'auto' }}>
          {repositories.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <CircularProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Loading repositories...
              </Typography>
            </Box>
          ) : filteredRepositories.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                No repositories found matching "{searchTerm}"
              </Typography>
            </Box>
          ) : (
            <List>
              {filteredRepositories.map((repo, index) => (
                <React.Fragment key={repo.id}>
                  <ListItem
                    sx={{
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                    }}
                    onClick={() => setSelectedRepo(repo)}
                  >
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        <GitHubIcon />
                      </Avatar>
                    </ListItemAvatar>
                    
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1" component="span">
                            {repo.name}
                          </Typography>
                          {repo.private && (
                            <Chip size="small" label="Private" variant="outlined" />
                          )}
                          {repo.fork && (
                            <Chip size="small" label="Fork" variant="outlined" />
                          )}
                          {repo.archived && (
                            <Chip size="small" label="Archived" color="warning" variant="outlined" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                            {repo.description || 'No description available'}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                            {repo.language && (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <Box
                                  sx={{
                                    width: 12,
                                    height: 12,
                                    borderRadius: '50%',
                                    backgroundColor: getLanguageColor(repo.language),
                                  }}
                                />
                                <Typography variant="caption">
                                  {repo.language}
                                </Typography>
                              </Box>
                            )}
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <StarIcon sx={{ fontSize: 14 }} />
                              <Typography variant="caption">
                                {repo.stargazers_count}
                              </Typography>
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              Updated {format(new Date(repo.updated_at), 'MMM d, yyyy')}
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                    
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<AddIcon />}
                      disabled={pinning || repo.archived}
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePinProject(repo);
                      }}
                    >
                      {pinning ? 'Pinning...' : 'Pin'}
                    </Button>
                  </ListItem>
                  
                  {index < filteredRepositories.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
          {filteredRepositories.length} of {repositories.length} repositories
        </Typography>
        <Button onClick={handleClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectSelectionDialog;

