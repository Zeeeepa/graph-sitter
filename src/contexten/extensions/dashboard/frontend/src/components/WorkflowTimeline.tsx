import React from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
  useTheme,
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/lab';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Refresh as RetryIcon,
  Code as CodeIcon,
  BugReport as BugIcon,
  Merge as MergeIcon,
  Build as BuildIcon,
  Assignment as TaskIcon,
} from '@mui/icons-material';
import { WorkflowEvent } from '../types/dashboard';

interface WorkflowTimelineProps {
  events: WorkflowEvent[];
}

export const WorkflowTimeline: React.FC<WorkflowTimelineProps> = ({ events }) => {
  const theme = useTheme();

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'flow_start':
        return <PlayIcon />;
      case 'flow_stop':
        return <StopIcon />;
      case 'flow_error':
        return <ErrorIcon />;
      case 'flow_success':
        return <SuccessIcon />;
      case 'flow_retry':
        return <RetryIcon />;
      case 'code_change':
        return <CodeIcon />;
      case 'issue_update':
        return <BugIcon />;
      case 'pr_merge':
        return <MergeIcon />;
      case 'build':
        return <BuildIcon />;
      case 'task':
        return <TaskIcon />;
      default:
        return <TaskIcon />;
    }
  };

  const getEventColor = (type: string): 'success' | 'error' | 'warning' | 'info' | 'primary' => {
    switch (type) {
      case 'flow_start':
        return 'primary';
      case 'flow_stop':
        return 'warning';
      case 'flow_error':
        return 'error';
      case 'flow_success':
        return 'success';
      case 'flow_retry':
        return 'warning';
      case 'code_change':
        return 'info';
      case 'issue_update':
        return 'warning';
      case 'pr_merge':
        return 'success';
      case 'build':
        return 'primary';
      case 'task':
        return 'info';
      default:
        return 'primary';
    }
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: 'numeric',
      day: 'numeric',
      month: 'short',
    }).format(date);
  };

  if (!events.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <Typography color="text.secondary">No workflow events available</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Timeline position="alternate">
        {events.map((event, index) => (
          <TimelineItem key={event.id}>
            <TimelineOppositeContent color="text.secondary">
              {formatDate(event.timestamp)}
            </TimelineOppositeContent>
            <TimelineSeparator>
              <TimelineDot color={getEventColor(event.type)}>
                {getEventIcon(event.type)}
              </TimelineDot>
              {index < events.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="h6" component="div">
                  {event.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {event.description}
                </Typography>
                {event.metadata && (
                  <Box sx={{ mt: 1 }}>
                    <List dense>
                      {Object.entries(event.metadata).map(([key, value]) => (
                        <ListItem key={key}>
                          <ListItemText
                            primary={key.replace(/_/g, ' ').toUpperCase()}
                            secondary={value}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
                {event.tags && (
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {event.tags.map(tag => (
                      <Chip
                        key={tag}
                        label={tag}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                )}
                {event.links && (
                  <Box sx={{ mt: 1 }}>
                    {event.links.map(link => (
                      <Typography
                        key={link.url}
                        variant="body2"
                        component="a"
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{
                          display: 'block',
                          color: theme.palette.primary.main,
                          textDecoration: 'none',
                          '&:hover': {
                            textDecoration: 'underline',
                          },
                        }}
                      >
                        {link.title}
                      </Typography>
                    ))}
                  </Box>
                )}
              </Paper>
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    </Box>
  );
};

