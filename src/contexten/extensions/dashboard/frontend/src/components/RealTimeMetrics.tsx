import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Grid,
  Paper,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Divider
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Speed as SpeedIcon,
  Assignment as AssignmentIcon,
  BugReport as BugReportIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  GitHub as GitHubIcon,
  LinearScale as LinearIcon,
  Code as CodeIcon
} from '@mui/icons-material';

interface MetricCard {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'increase' | 'decrease';
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

interface ActivityItem {
  id: string;
  type: 'pr' | 'issue' | 'commit' | 'deployment';
  title: string;
  description: string;
  timestamp: Date;
  status: 'success' | 'pending' | 'failed';
  user?: string;
}

interface RealTimeMetricsProps {
  projectId?: string;
  refreshInterval?: number;
}

export const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({
  projectId,
  refreshInterval = 30000 // 30 seconds
}) => {
  const [metrics, setMetrics] = useState<MetricCard[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [loading, setLoading] = useState(false);

  // Mock data generation
  const generateMockMetrics = (): MetricCard[] => [
    {
      title: 'Active Projects',
      value: 12,
      change: 2,
      changeType: 'increase',
      icon: <AssignmentIcon />,
      color: 'primary'
    },
    {
      title: 'Open PRs',
      value: 8,
      change: -1,
      changeType: 'decrease',
      icon: <GitHubIcon />,
      color: 'secondary'
    },
    {
      title: 'Issues Resolved',
      value: 24,
      change: 5,
      changeType: 'increase',
      icon: <CheckCircleIcon />,
      color: 'success'
    },
    {
      title: 'Code Quality Score',
      value: '94%',
      change: 2,
      changeType: 'increase',
      icon: <CodeIcon />,
      color: 'success'
    },
    {
      title: 'Avg Response Time',
      value: '2.3h',
      change: -0.5,
      changeType: 'decrease',
      icon: <SpeedIcon />,
      color: 'warning'
    },
    {
      title: 'Active Bugs',
      value: 3,
      change: -2,
      changeType: 'decrease',
      icon: <BugReportIcon />,
      color: 'error'
    }
  ];

  const generateMockActivities = (): ActivityItem[] => [
    {
      id: 'act-1',
      type: 'pr',
      title: 'PR #234 merged',
      description: 'Material-UI Dashboard Upgrade',
      timestamp: new Date(Date.now() - 300000),
      status: 'success',
      user: 'codegen-bot'
    },
    {
      id: 'act-2',
      type: 'issue',
      title: 'Issue created',
      description: 'Implement real-time monitoring',
      timestamp: new Date(Date.now() - 600000),
      status: 'pending',
      user: 'developer'
    },
    {
      id: 'act-3',
      type: 'commit',
      title: 'New commit',
      description: 'Add workflow monitoring component',
      timestamp: new Date(Date.now() - 900000),
      status: 'success',
      user: 'codegen-bot'
    },
    {
      id: 'act-4',
      type: 'deployment',
      title: 'Deployment started',
      description: 'Dashboard v2.0 to staging',
      timestamp: new Date(Date.now() - 1200000),
      status: 'pending',
      user: 'ci-cd'
    }
  ];

  useEffect(() => {
    const fetchMetrics = () => {
      setLoading(true);
      // Simulate API call
      setTimeout(() => {
        setMetrics(generateMockMetrics());
        setActivities(generateMockActivities());
        setLastUpdated(new Date());
        setLoading(false);
      }, 1000);
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, refreshInterval);

    return () => clearInterval(interval);
  }, [projectId, refreshInterval]);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'pr': return <GitHubIcon />;
      case 'issue': return <BugReportIcon />;
      case 'commit': return <CodeIcon />;
      case 'deployment': return <SpeedIcon />;
      default: return <AssignmentIcon />;
    }
  };

  const getActivityColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => {
      setMetrics(generateMockMetrics());
      setActivities(generateMockActivities());
      setLastUpdated(new Date());
      setLoading(false);
    }, 1000);
  };

  return (
    <Box>
      {/* Metrics Grid */}
      <Card elevation={2} sx={{ mb: 3 }}>
        <CardHeader
          title={
            <Box display="flex" alignItems="center" gap={1}>
              <DashboardIcon />
              <Typography variant="h6">Real-Time Metrics</Typography>
            </Box>
          }
          action={
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="caption" color="text.secondary">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </Typography>
              <Tooltip title="Refresh">
                <IconButton onClick={handleRefresh} disabled={loading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
          }
        />
        <CardContent>
          <Grid container spacing={3}>
            {metrics.map((metric, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      elevation: 3,
                      transform: 'translateY(-2px)'
                    }
                  }}
                >
                  <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                    <Avatar
                      sx={{
                        bgcolor: `${metric.color}.main`,
                        width: 40,
                        height: 40
                      }}
                    >
                      {metric.icon}
                    </Avatar>
                    {metric.change && (
                      <Box display="flex" alignItems="center" gap={0.5}>
                        {metric.changeType === 'increase' ? (
                          <TrendingUpIcon color="success" fontSize="small" />
                        ) : (
                          <TrendingDownIcon color="error" fontSize="small" />
                        )}
                        <Typography
                          variant="caption"
                          color={metric.changeType === 'increase' ? 'success.main' : 'error.main'}
                        >
                          {Math.abs(metric.change)}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                  <Typography variant="h4" fontWeight="bold" color={`${metric.color}.main`}>
                    {metric.value}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {metric.title}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Activity Feed */}
      <Card elevation={2}>
        <CardHeader
          title={
            <Box display="flex" alignItems="center" gap={1}>
              <ScheduleIcon />
              <Typography variant="h6">Recent Activity</Typography>
            </Box>
          }
        />
        <CardContent sx={{ pt: 0 }}>
          {loading ? (
            <Box>
              <LinearProgress sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary" textAlign="center">
                Loading activities...
              </Typography>
            </Box>
          ) : (
            <List>
              {activities.map((activity, index) => (
                <React.Fragment key={activity.id}>
                  <ListItem alignItems="flex-start" sx={{ px: 0 }}>
                    <ListItemIcon>
                      <Avatar
                        sx={{
                          bgcolor: `${getActivityColor(activity.status)}.main`,
                          width: 32,
                          height: 32
                        }}
                      >
                        {getActivityIcon(activity.type)}
                      </Avatar>
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" fontWeight="medium">
                            {activity.title}
                          </Typography>
                          <Chip
                            label={activity.status}
                            color={getActivityColor(activity.status)}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {activity.description}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatTimeAgo(activity.timestamp)}
                            {activity.user && ` • by ${activity.user}`}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < activities.length - 1 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

