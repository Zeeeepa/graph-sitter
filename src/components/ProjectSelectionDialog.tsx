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
  ListItemButton,
  Typography,
  Box,
  Chip,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Search as SearchIcon,
  GitHub as GitHubIcon,
} from '@mui/icons-material';

export interface ProjectSelectionDialogProps {
  open: boolean;
  onClose: () => void;
  repositories: Array<{
    id: string;
    name: string;
    description?: string;
    url: string;
    language?: string;
    stars?: number;
    lastUpdated?: Date;
  }>;
  onSelectRepository?: (repository: any) => void;
}

const ProjectSelectionDialog: React.FC<ProjectSelectionDialogProps> = ({
  open,
  onClose,
  repositories,
  onSelectRepository,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);

  const filteredRepositories = repositories.filter(repo =>
    repo.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (repo.description && repo.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleSelectRepository = (repository: any) => {
    setSelectedRepo(repository.id);
    if (onSelectRepository) {
      onSelectRepository(repository);
    }
  };

  const handleConfirm = () => {
    if (selectedRepo && onSelectRepository) {
      const repository = repositories.find(repo => repo.id === selectedRepo);
      if (repository) {
        onSelectRepository(repository);
      }
    }
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle>
        <Typography variant="h6" component="div">
          Select Repository
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Choose a repository to create a new project from
        </Typography>
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 2 }}>
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
            sx={{ mb: 2 }}
          />
        </Box>

        <List sx={{ maxHeight: '400px', overflow: 'auto' }}>
          {filteredRepositories.length === 0 ? (
            <ListItem>
              <ListItemText
                primary="No repositories found"
                secondary="Try adjusting your search terms"
              />
            </ListItem>
          ) : (
            filteredRepositories.map((repository) => (
              <ListItem key={repository.id} disablePadding>
                <ListItemButton
                  selected={selectedRepo === repository.id}
                  onClick={() => handleSelectRepository(repository)}
                  sx={{
                    border: selectedRepo === repository.id ? 2 : 1,
                    borderColor: selectedRepo === repository.id ? 'primary.main' : 'divider',
                    borderRadius: 1,
                    mb: 1,
                    '&:hover': {
                      borderColor: 'primary.main',
                    },
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    <GitHubIcon sx={{ mr: 2, color: 'text.secondary' }} />
                    <Box sx={{ flexGrow: 1 }}>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle1" component="span">
                              {repository.name}
                            </Typography>
                            {repository.language && (
                              <Chip
                                label={repository.language}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            {repository.description && (
                              <Typography variant="body2" color="text.secondary">
                                {repository.description}
                              </Typography>
                            )}
                            <Typography variant="caption" color="text.secondary">
                              {repository.url}
                            </Typography>
                          </Box>
                        }
                      />
                    </Box>
                    {repository.stars && (
                      <Box sx={{ textAlign: 'right', ml: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          ⭐ {repository.stars}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </ListItemButton>
              </ListItem>
            ))
          )}
        </List>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          disabled={!selectedRepo}
        >
          Select Repository
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectSelectionDialog;

