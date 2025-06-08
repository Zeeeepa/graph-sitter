import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  Divider,
  useTheme,
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Project } from '../types/dashboard';
import { useProjectMetrics } from '../hooks/useProjectMetrics';

interface ProjectMetricsProps {
  project: Project;
}

export const ProjectMetrics: React.FC<ProjectMetricsProps> = ({ project }) => {
  const theme = useTheme();
  const { metrics, loading, error } = useProjectMetrics(project.id);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!metrics) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <Typography>No metrics available</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Code Quality Score
            </Typography>
            <Typography variant="h4">
              {metrics.codeQuality}%
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Workflow Success Rate
            </Typography>
            <Typography variant="h4">
              {metrics.workflowSuccessRate}%
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Active Contributors
            </Typography>
            <Typography variant="h4">
              {metrics.activeContributors}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Open Issues
            </Typography>
            <Typography variant="h4">
              {metrics.openIssues}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Divider sx={{ my: 4 }} />

      {/* Activity Timeline */}
      <Typography variant="h6" gutterBottom>
        Activity Timeline
      </Typography>
      <Box sx={{ height: 300, mb: 4 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={metrics.activityTimeline}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="commits"
              stroke={theme.palette.primary.main}
              name="Commits"
            />
            <Line
              type="monotone"
              dataKey="prs"
              stroke={theme.palette.secondary.main}
              name="Pull Requests"
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>

      <Divider sx={{ my: 4 }} />

      {/* Workflow Performance */}
      <Typography variant="h6" gutterBottom>
        Workflow Performance
      </Typography>
      <Box sx={{ height: 300, mb: 4 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={metrics.workflowPerformance}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar
              dataKey="successful"
              name="Successful"
              fill={theme.palette.success.main}
            />
            <Bar
              dataKey="failed"
              name="Failed"
              fill={theme.palette.error.main}
            />
          </BarChart>
        </ResponsiveContainer>
      </Box>

      {/* Additional Metrics */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Code Analysis
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Lines of Code
                </Typography>
                <Typography variant="h6">
                  {metrics.codeAnalysis.linesOfCode.toLocaleString()}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Test Coverage
                </Typography>
                <Typography variant="h6">
                  {metrics.codeAnalysis.testCoverage}%
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Technical Debt
                </Typography>
                <Typography variant="h6">
                  {metrics.codeAnalysis.technicalDebt} hours
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Code Duplication
                </Typography>
                <Typography variant="h6">
                  {metrics.codeAnalysis.duplication}%
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Team Performance
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Avg. PR Review Time
                </Typography>
                <Typography variant="h6">
                  {metrics.teamPerformance.avgPRReviewTime} hours
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Avg. Issue Resolution
                </Typography>
                <Typography variant="h6">
                  {metrics.teamPerformance.avgIssueResolutionTime} days
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Sprint Velocity
                </Typography>
                <Typography variant="h6">
                  {metrics.teamPerformance.sprintVelocity} points
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Team Satisfaction
                </Typography>
                <Typography variant="h6">
                  {metrics.teamPerformance.teamSatisfaction}/10
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

