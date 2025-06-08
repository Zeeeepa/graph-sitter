import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { Project, WorkflowEvent } from '../types/dashboard';

interface WorkflowControlProps {
  project: Project;
  events?: WorkflowEvent[];
  onStartFlow: (projectId: string) => Promise<void>;
  onStopFlow: (projectId: string) => Promise<void>;
  onRefreshStatus: (projectId: string) => Promise<void>;
}

const WorkflowControl: React.FC<WorkflowControlProps> = ({
  project,
  events = [],
  onStartFlow,
  onStopFlow,
  onRefreshStatus,
}) => {
  const [loading, setLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<WorkflowEvent | null>(null);

  const handleStartFlow = async () => {
    setLoading(true);
    try {
      await onStartFlow(project.id);
    } finally {
      setLoading(false);
    }
  };

  const handleStopFlow = async () => {
    setLoading(true);
    try {
      await onStopFlow(project.id);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshStatus = async () => {
    setLoading(true);
    try {
      await onRefreshStatus(project.id);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenEventDetails = (event: WorkflowEvent) => {
    setSelectedEvent(event);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedEvent(null);
  };

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'default' => {
    switch (status) {
      case 'running':
        return 'success';
      case 'error':
        return 'error';
      case 'stopped':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getEventTypeColor = (type: string): 'success' | 'error' | 'warning' | 'info' => {
    switch (type) {
      case 'task_completed':
        return 'success';
      case 'flow_started':
        return 'info';
      case 'flow_stopped':
        return 'warning';
      default:
        return 'info';
    }
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Workflow Control</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip
              label={project.flowStatus}
              color={getStatusColor(project.flowStatus)}
              size="small"
            />
            <IconButton
              size="small"
              onClick={handleRefreshStatus}
              disabled={loading}
            >
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Button
            variant="contained"
            color="success"
            startIcon={loading ? <CircularProgress size={20} /> : <PlayIcon />}
            onClick={handleStartFlow}
            disabled={loading || project.flowStatus === 'running'}
          >
            Start Flow
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={loading ? <CircularProgress size={20} /> : <StopIcon />}
            onClick={handleStopFlow}
            disabled={loading || project.flowStatus === 'stopped'}
          >
            Stop Flow
          </Button>
        </Box>

        <Typography variant="subtitle1" gutterBottom>
          Recent Events
        </Typography>
        <List>
          {events.map((event) => (
            <ListItem
              key={event.id}
              secondaryAction={
                <IconButton edge="end" onClick={() => handleOpenEventDetails(event)}>
                  <InfoIcon />
                </IconButton>
              }
              sx={{
                bgcolor: 'background.paper',
                mb: 1,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body1">{event.message}</Typography>
                    <Chip
                      size="small"
                      label={event.type}
                      color={getEventTypeColor(event.type)}
                    />
                  </Box>
                }
                secondary={new Date(event.timestamp).toLocaleString()}
              />
            </ListItem>
          ))}
        </List>

        <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
          <DialogTitle>Event Details</DialogTitle>
          <DialogContent>
            {selectedEvent && (
              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label="Type"
                  value={selectedEvent.type}
                  InputProps={{ readOnly: true }}
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  label="Message"
                  value={selectedEvent.message}
                  InputProps={{ readOnly: true }}
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  label="Timestamp"
                  value={new Date(selectedEvent.timestamp).toLocaleString()}
                  InputProps={{ readOnly: true }}
                  sx={{ mb: 2 }}
                />
                {selectedEvent.taskId && (
                  <TextField
                    fullWidth
                    label="Task ID"
                    value={selectedEvent.taskId}
                    InputProps={{ readOnly: true }}
                    sx={{ mb: 2 }}
                  />
                )}
                {selectedEvent.metadata && (
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Metadata"
                    value={JSON.stringify(selectedEvent.metadata, null, 2)}
                    InputProps={{ readOnly: true }}
                  />
                )}
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Close</Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </Box>
  );
};

export default WorkflowControl;

