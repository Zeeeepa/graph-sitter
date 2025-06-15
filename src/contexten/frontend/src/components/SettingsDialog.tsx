import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Grid,
  Typography,
  Alert,
  Box,
  Divider,
} from '@mui/material';
import { Settings } from '../types/dashboard';
import GitHubLoginButton from './GitHubLoginButton';
import { isGitHubAuthenticated, getGitHubUser } from '../services/githubService';
import { GitHubUser } from '../types/github';

interface SettingsDialogProps {
  open: boolean;
  settings: Settings;
  onClose: () => void;
  onSave: (settings: Settings) => void;
}

const SettingsDialog: React.FC<SettingsDialogProps> = ({
  open,
  settings,
  onClose,
  onSave,
}) => {
  const [formData, setFormData] = useState<Settings>(settings);
  const [testStatus, setTestStatus] = useState<{
    github?: boolean;
    linear?: boolean;
    slack?: boolean;
    postgresql?: boolean;
  }>({});
  const [githubUser, setGithubUser] = useState<GitHubUser | null>(null);

  useEffect(() => {
    // Check GitHub authentication status when dialog opens
    if (open && isGitHubAuthenticated()) {
      fetchGitHubUser();
    }
  }, [open]);

  const fetchGitHubUser = async () => {
    try {
      const user = await getGitHubUser();
      setGithubUser(user);
      setTestStatus(prev => ({ ...prev, github: true }));
    } catch (error) {
      console.error('Error fetching GitHub user:', error);
      setGithubUser(null);
      setTestStatus(prev => ({ ...prev, github: false }));
    }
  };

  const handleChange = (field: keyof Settings) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleTestConnection = async (type: 'linear' | 'slack' | 'postgresql') => {
    // Simulate testing connection
    setTestStatus((prev) => ({ ...prev, [type]: undefined }));
    try {
      // In a real app, this would make an API call to test the connection
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setTestStatus((prev) => ({ ...prev, [type]: true }));
    } catch (error) {
      setTestStatus((prev) => ({ ...prev, [type]: false }));
    }
  };

  const handleGitHubLoginSuccess = (user: GitHubUser) => {
    setGithubUser(user);
    setTestStatus(prev => ({ ...prev, github: true }));
  };

  const handleGitHubLoginError = (error: Error) => {
    console.error('GitHub login error:', error);
    setTestStatus(prev => ({ ...prev, github: false }));
  };

  const handleSave = () => {
    onSave(formData);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Settings</DialogTitle>
      <DialogContent>
        <Grid container spacing={3} sx={{ mt: 1 }}>
          {/* GitHub Section */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              GitHub Integration
            </Typography>
            <Box sx={{ mb: 2 }}>
              {githubUser ? (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <img 
                    src={githubUser.avatar_url} 
                    alt={`${githubUser.login}'s avatar`} 
                    style={{ width: 40, height: 40, borderRadius: '50%', marginRight: 16 }}
                  />
                  <Typography>
                    Logged in as <strong>{githubUser.login}</strong>
                  </Typography>
                </Box>
              ) : null}
              
              <GitHubLoginButton 
                variant="contained"
                fullWidth
                onSuccess={handleGitHubLoginSuccess}
                onError={handleGitHubLoginError}
              />
              
              {testStatus.github !== undefined && (
                <Alert severity={testStatus.github ? 'success' : 'error'} sx={{ mt: 1 }}>
                  {testStatus.github
                    ? 'Successfully connected to GitHub'
                    : 'Failed to connect to GitHub'}
                </Alert>
              )}
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Linear Section */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Linear Integration
            </Typography>
            <Box sx={{ mb: 2 }}>
              <TextField
                fullWidth
                label="Linear Token"
                type="password"
                value={formData.linearToken}
                onChange={handleChange('linearToken')}
                sx={{ mb: 2 }}
              />
              <Button
                variant="outlined"
                onClick={() => handleTestConnection('linear')}
                sx={{ mr: 2 }}
              >
                Test Connection
              </Button>
              {testStatus.linear !== undefined && (
                <Alert severity={testStatus.linear ? 'success' : 'error'} sx={{ mt: 1 }}>
                  {testStatus.linear
                    ? 'Successfully connected to Linear'
                    : 'Failed to connect to Linear'}
                </Alert>
              )}
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Slack Section */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Slack Integration
            </Typography>
            <Box sx={{ mb: 2 }}>
              <TextField
                fullWidth
                label="Slack Token"
                type="password"
                value={formData.slackToken || ''}
                onChange={handleChange('slackToken')}
                sx={{ mb: 2 }}
              />
              <Button
                variant="outlined"
                onClick={() => handleTestConnection('slack')}
                sx={{ mr: 2 }}
              >
                Test Connection
              </Button>
              {testStatus.slack !== undefined && (
                <Alert severity={testStatus.slack ? 'success' : 'error'} sx={{ mt: 1 }}>
                  {testStatus.slack
                    ? 'Successfully connected to Slack'
                    : 'Failed to connect to Slack'}
                </Alert>
              )}
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Database Section */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Database Configuration
            </Typography>
            <Box sx={{ mb: 2 }}>
              <TextField
                fullWidth
                label="PostgreSQL URL"
                value={formData.postgresqlUrl || ''}
                onChange={handleChange('postgresqlUrl')}
                sx={{ mb: 2 }}
              />
              <Button
                variant="outlined"
                onClick={() => handleTestConnection('postgresql')}
                sx={{ mr: 2 }}
              >
                Test Connection
              </Button>
              {testStatus.postgresql !== undefined && (
                <Alert severity={testStatus.postgresql ? 'success' : 'error'} sx={{ mt: 1 }}>
                  {testStatus.postgresql
                    ? 'Successfully connected to PostgreSQL'
                    : 'Failed to connect to PostgreSQL'}
                </Alert>
              )}
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* General Settings */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              General Settings
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.autoStartFlows}
                      onChange={handleChange('autoStartFlows')}
                    />
                  }
                  label="Auto-start flows for new projects"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.enableNotifications}
                      onChange={handleChange('enableNotifications')}
                    />
                  }
                  label="Enable notifications"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.enableAnalytics}
                      onChange={handleChange('enableAnalytics')}
                    />
                  }
                  label="Enable analytics"
                />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained" color="primary">
          Save Settings
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SettingsDialog;
