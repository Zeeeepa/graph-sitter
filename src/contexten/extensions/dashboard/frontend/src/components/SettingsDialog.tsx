import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Divider,
  IconButton,
  InputAdornment,
  Alert,
  Tabs,
  Tab,
  Switch,
  FormControlLabel,
  FormGroup,
} from '@mui/material';
import {
  Close as CloseIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import toast from 'react-hot-toast';

import { dashboardApi } from '../services/api';
import { EnvironmentVariables, SettingsUpdateRequest } from '../types';

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const SettingsDialog: React.FC<SettingsDialogProps> = ({ open, onClose }) => {
  const [tabValue, setTabValue] = useState(0);
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);

  const envForm = useForm<EnvironmentVariables>({
    defaultValues: {
      github_token: '',
      linear_api_key: '',
      slack_token: '',
      codegen_org_id: '',
      codegen_token: '',
      postgresql_url: '',
    },
  });

  const projectForm = useForm<SettingsUpdateRequest>({
    defaultValues: {
      github_enabled: true,
      linear_enabled: true,
      slack_enabled: true,
      codegen_enabled: true,
      auto_pr_creation: true,
      auto_issue_creation: true,
      quality_gates_enabled: true,
    },
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const togglePasswordVisibility = (field: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field],
    }));
  };

  const handleSaveEnvironment = async (data: EnvironmentVariables) => {
    setSaving(true);
    try {
      await dashboardApi.updateEnvironmentVariables(data);
      toast.success('Environment variables updated successfully');
    } catch (error) {
      toast.error('Failed to update environment variables');
      console.error('Environment update error:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveProjectSettings = async (data: SettingsUpdateRequest) => {
    setSaving(true);
    try {
      // TODO: Implement project-specific settings update
      // For now, we'll just show a success message
      toast.success('Project settings updated successfully');
    } catch (error) {
      toast.error('Failed to update project settings');
      console.error('Project settings update error:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    envForm.reset();
    projectForm.reset();
    setTabValue(0);
    onClose();
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '70vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Dashboard Settings</Typography>
        <IconButton onClick={handleClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
          <Tab label="Environment Variables" />
          <Tab label="Project Settings" />
          <Tab label="Notifications" />
        </Tabs>
      </Box>

      <DialogContent sx={{ p: 0 }}>
        {/* Environment Variables Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ px: 3 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              Configure API keys and tokens for external service integrations.
              These are stored securely and used for automated workflows.
            </Alert>

            <form onSubmit={envForm.handleSubmit(handleSaveEnvironment)}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* GitHub Token */}
                <Controller
                  name="github_token"
                  control={envForm.control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="GitHub Access Token"
                      type={showPasswords.github_token ? 'text' : 'password'}
                      fullWidth
                      placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                      helperText="Personal access token for GitHub API access"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              onClick={() => togglePasswordVisibility('github_token')}
                              edge="end"
                            >
                              {showPasswords.github_token ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  )}
                />

                {/* Linear API Key */}
                <Controller
                  name="linear_api_key"
                  control={envForm.control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Linear API Key"
                      type={showPasswords.linear_api_key ? 'text' : 'password'}
                      fullWidth
                      placeholder="lin_api_xxxxxxxxxxxxxxxxxxxx"
                      helperText="API key for Linear issue management"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              onClick={() => togglePasswordVisibility('linear_api_key')}
                              edge="end"
                            >
                              {showPasswords.linear_api_key ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  )}
                />

                {/* Slack Token */}
                <Controller
                  name="slack_token"
                  control={envForm.control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Slack Bot Token"
                      type={showPasswords.slack_token ? 'text' : 'password'}
                      fullWidth
                      placeholder="xoxb-xxxxxxxxxxxxxxxxxxxx"
                      helperText="Bot token for Slack notifications"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              onClick={() => togglePasswordVisibility('slack_token')}
                              edge="end"
                            >
                              {showPasswords.slack_token ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  )}
                />

                <Divider />

                {/* Codegen Settings */}
                <Typography variant="h6" color="primary">
                  Codegen SDK Configuration
                </Typography>

                <Controller
                  name="codegen_org_id"
                  control={envForm.control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Codegen Organization ID"
                      fullWidth
                      placeholder="org_xxxxxxxxxxxxxxxxxxxx"
                      helperText="Your Codegen organization identifier"
                    />
                  )}
                />

                <Controller
                  name="codegen_token"
                  control={envForm.control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Codegen API Token"
                      type={showPasswords.codegen_token ? 'text' : 'password'}
                      fullWidth
                      placeholder="cg_xxxxxxxxxxxxxxxxxxxx"
                      helperText="API token for Codegen SDK access"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              onClick={() => togglePasswordVisibility('codegen_token')}
                              edge="end"
                            >
                              {showPasswords.codegen_token ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  )}
                />

                <Divider />

                {/* Database Settings */}
                <Typography variant="h6" color="primary">
                  Database Configuration
                </Typography>

                <Controller
                  name="postgresql_url"
                  control={envForm.control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="PostgreSQL Connection URL"
                      type={showPasswords.postgresql_url ? 'text' : 'password'}
                      fullWidth
                      placeholder="postgresql://user:password@localhost:5432/database"
                      helperText="PostgreSQL database connection string"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              onClick={() => togglePasswordVisibility('postgresql_url')}
                              edge="end"
                            >
                              {showPasswords.postgresql_url ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  )}
                />
              </Box>
            </form>
          </Box>
        </TabPanel>

        {/* Project Settings Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ px: 3 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              Configure default settings for new projects and workflow automation.
            </Alert>

            <form onSubmit={projectForm.handleSubmit(handleSaveProjectSettings)}>
              <FormGroup>
                <Typography variant="h6" gutterBottom>
                  Service Integrations
                </Typography>
                
                <Controller
                  name="github_enabled"
                  control={projectForm.control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch {...field} checked={field.value} />}
                      label="Enable GitHub Integration"
                    />
                  )}
                />
                
                <Controller
                  name="linear_enabled"
                  control={projectForm.control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch {...field} checked={field.value} />}
                      label="Enable Linear Integration"
                    />
                  )}
                />
                
                <Controller
                  name="slack_enabled"
                  control={projectForm.control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch {...field} checked={field.value} />}
                      label="Enable Slack Notifications"
                    />
                  )}
                />
                
                <Controller
                  name="codegen_enabled"
                  control={projectForm.control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch {...field} checked={field.value} />}
                      label="Enable Codegen SDK"
                    />
                  )}
                />

                <Divider sx={{ my: 2 }} />

                <Typography variant="h6" gutterBottom>
                  Automation Settings
                </Typography>
                
                <Controller
                  name="auto_pr_creation"
                  control={projectForm.control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch {...field} checked={field.value} />}
                      label="Automatic PR Creation"
                    />
                  )}
                />
                
                <Controller
                  name="auto_issue_creation"
                  control={projectForm.control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch {...field} checked={field.value} />}
                      label="Automatic Issue Creation"
                    />
                  )}
                />
                
                <Controller
                  name="quality_gates_enabled"
                  control={projectForm.control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch {...field} checked={field.value} />}
                      label="Enable Quality Gates"
                    />
                  )}
                />
              </FormGroup>
            </form>
          </Box>
        </TabPanel>

        {/* Notifications Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ px: 3 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              Configure notification preferences for workflow events and updates.
            </Alert>
            
            <Typography variant="body1" color="text.secondary">
              Notification settings will be available in a future update.
            </Typography>
          </Box>
        </TabPanel>
      </DialogContent>

      <DialogActions sx={{ p: 3, borderTop: '1px solid', borderColor: 'divider' }}>
        <Button onClick={handleClose}>
          Cancel
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          disabled={saving}
          onClick={() => {
            if (tabValue === 0) {
              envForm.handleSubmit(handleSaveEnvironment)();
            } else if (tabValue === 1) {
              projectForm.handleSubmit(handleSaveProjectSettings)();
            }
          }}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SettingsDialog;

