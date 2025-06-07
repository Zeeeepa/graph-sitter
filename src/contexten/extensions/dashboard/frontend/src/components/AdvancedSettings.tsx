import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tabs,
  Tab,
  Box,
  TextField,
  Switch,
  FormControlLabel,
  Typography,
  Divider,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider
} from '@mui/material';
import {
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Code as CodeIcon,
  Speed as SpeedIcon,
  Psychology as PsychologyIcon,
  AutoFixHigh as AutoFixHighIcon,
  Storage as StorageIcon,
  Email as EmailIcon,
  Chat as SlackIcon,
  Webhook as WebhookIcon,
  GitHub as GitHubIcon,
  LinearScale as LinearIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Tune as TuneIcon
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

interface AdvancedSettingsProps {
  open: boolean;
  onClose: () => void;
  onSave: (settings: any) => void;
}

export const AdvancedSettings: React.FC<AdvancedSettingsProps> = ({
  open,
  onClose,
  onSave
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [settings, setSettings] = useState({
    // API Keys
    githubToken: '',
    linearApiKey: '',
    slackBotToken: '',
    codegenOrgId: '',
    codegenToken: '',
    postgresqlUrl: '',
    circleciToken: '',
    
    // Workflow Settings
    autoExecuteWorkflows: true,
    parallelExecution: false,
    maxConcurrentTasks: 3,
    retryFailedTasks: true,
    maxRetries: 3,
    taskTimeout: 30,
    
    // Notification Settings
    emailNotifications: true,
    slackNotifications: true,
    webhookNotifications: false,
    notificationLevel: 'important',
    
    // Quality Gates
    enableCodeReview: true,
    enableTesting: true,
    enableSecurity: true,
    minCodeCoverage: 80,
    maxComplexity: 10,
    
    // Advanced Features
    advanced: {
      enable_ai_assistance: true,
      enable_predictive_analysis: false,
      enable_auto_optimization: true,
      data_retention_days: 90
    },
    
    // Custom Webhooks
    webhooks: [
      { name: 'Deployment Hook', url: 'https://api.example.com/deploy', events: ['deployment'] },
      { name: 'PR Hook', url: 'https://api.example.com/pr', events: ['pr_created', 'pr_merged'] }
    ]
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const togglePasswordVisibility = (field: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleSettingChange = (path: string, value: any) => {
    setSettings(prev => {
      const keys = path.split('.');
      const newSettings = { ...prev };
      let current: any = newSettings;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      
      return newSettings;
    });
  };

  const addWebhook = () => {
    setSettings(prev => ({
      ...prev,
      webhooks: [
        ...prev.webhooks,
        { name: '', url: '', events: [] }
      ]
    }));
  };

  const removeWebhook = (index: number) => {
    setSettings(prev => ({
      ...prev,
      webhooks: prev.webhooks.filter((_, i) => i !== index)
    }));
  };

  const handleSave = () => {
    onSave(settings);
    onClose();
  };

  const testConnection = async (service: string) => {
    // Mock connection test
    console.log(`Testing connection to ${service}...`);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <SettingsIcon />
          <Typography variant="h6">Advanced Settings</Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab icon={<SecurityIcon />} label="API Keys" />
            <Tab icon={<TuneIcon />} label="Workflow" />
            <Tab icon={<NotificationsIcon />} label="Notifications" />
            <Tab icon={<SettingsIcon />} label="Advanced" />
          </Tabs>
        </Box>

        {/* API Keys Tab */}
        <TabPanel value={tabValue} index={0}>
          <Alert severity="info" sx={{ mb: 3 }}>
            API keys are encrypted and stored securely. Test connections to verify your credentials.
          </Alert>
          
          <Grid container spacing={3}>
            {[
              { key: 'githubToken', label: 'GitHub Token', service: 'GitHub' },
              { key: 'linearApiKey', label: 'Linear API Key', service: 'Linear' },
              { key: 'slackBotToken', label: 'Slack Bot Token', service: 'Slack' },
              { key: 'codegenOrgId', label: 'Codegen Org ID', service: 'Codegen' },
              { key: 'codegenToken', label: 'Codegen Token', service: 'Codegen' },
              { key: 'postgresqlUrl', label: 'PostgreSQL URL', service: 'Database' },
              { key: 'circleciToken', label: 'CircleCI Token', service: 'CircleCI' }
            ].map(({ key, label, service }) => (
              <Grid item xs={12} key={key}>
                <Paper elevation={1} sx={{ p: 2 }}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <TextField
                      fullWidth
                      label={label}
                      type={showPasswords[key] ? 'text' : 'password'}
                      value={settings[key as keyof typeof settings] as string}
                      onChange={(e) => handleSettingChange(key, e.target.value)}
                      InputProps={{
                        endAdornment: (
                          <IconButton
                            onClick={() => togglePasswordVisibility(key)}
                            edge="end"
                          >
                            {showPasswords[key] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                        )
                      }}
                    />
                    <Button
                      variant="outlined"
                      onClick={() => testConnection(service)}
                      startIcon={<RefreshIcon />}
                    >
                      Test
                    </Button>
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Workflow Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Execution Settings</Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoExecuteWorkflows}
                    onChange={(e) => handleSettingChange('autoExecuteWorkflows', e.target.checked)}
                  />
                }
                label="Auto-execute workflows when plans are generated"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.parallelExecution}
                    onChange={(e) => handleSettingChange('parallelExecution', e.target.checked)}
                  />
                }
                label="Enable parallel task execution"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.retryFailedTasks}
                    onChange={(e) => handleSettingChange('retryFailedTasks', e.target.checked)}
                  />
                }
                label="Automatically retry failed tasks"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Typography gutterBottom>Max Concurrent Tasks</Typography>
              <Slider
                value={settings.maxConcurrentTasks}
                onChange={(_, value) => handleSettingChange('maxConcurrentTasks', value)}
                min={1}
                max={10}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Typography gutterBottom>Task Timeout (minutes)</Typography>
              <Slider
                value={settings.taskTimeout}
                onChange={(_, value) => handleSettingChange('taskTimeout', value)}
                min={5}
                max={120}
                marks={[
                  { value: 5, label: '5m' },
                  { value: 30, label: '30m' },
                  { value: 60, label: '1h' },
                  { value: 120, label: '2h' }
                ]}
                valueLabelDisplay="auto"
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>Quality Gates</Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableCodeReview}
                    onChange={(e) => handleSettingChange('enableCodeReview', e.target.checked)}
                  />
                }
                label="Require code review before merging"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableTesting}
                    onChange={(e) => handleSettingChange('enableTesting', e.target.checked)}
                  />
                }
                label="Require all tests to pass"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.enableSecurity}
                    onChange={(e) => handleSettingChange('enableSecurity', e.target.checked)}
                  />
                }
                label="Run security scans"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notifications Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Notification Channels</Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.emailNotifications}
                    onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                  />
                }
                label="Email notifications"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.slackNotifications}
                    onChange={(e) => handleSettingChange('slackNotifications', e.target.checked)}
                  />
                }
                label="Slack notifications"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.webhookNotifications}
                    onChange={(e) => handleSettingChange('webhookNotifications', e.target.checked)}
                  />
                }
                label="Webhook notifications"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Notification Level</InputLabel>
                <Select
                  value={settings.notificationLevel}
                  onChange={(e) => handleSettingChange('notificationLevel', e.target.value)}
                  label="Notification Level"
                >
                  <MenuItem value="all">All events</MenuItem>
                  <MenuItem value="important">Important only</MenuItem>
                  <MenuItem value="critical">Critical only</MenuItem>
                  <MenuItem value="none">None</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Code Tab */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Advanced Settings</Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.advanced.enable_ai_assistance}
                    onChange={(e) => handleSettingChange('advanced.enable_ai_assistance', e.target.checked)}
                  />
                }
                label="Enable AI Assistance"
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Custom Webhooks</Typography>
                <Button
                  startIcon={<AddIcon />}
                  onClick={addWebhook}
                  variant="outlined"
                  size="small"
                >
                  Add Webhook
                </Button>
              </Box>
              
              <List>
                {settings.webhooks.map((webhook, index) => (
                  <ListItem key={index} divider>
                    <ListItemText
                      primary={
                        <Box display="flex" gap={2} alignItems="center">
                          <TextField
                            size="small"
                            label="Name"
                            value={webhook.name}
                            onChange={(e) => {
                              const newWebhooks = [...settings.webhooks];
                              newWebhooks[index].name = e.target.value;
                              handleSettingChange('webhooks', newWebhooks);
                            }}
                          />
                          <TextField
                            size="small"
                            label="URL"
                            value={webhook.url}
                            onChange={(e) => {
                              const newWebhooks = [...settings.webhooks];
                              newWebhooks[index].url = e.target.value;
                              handleSettingChange('webhooks', newWebhooks);
                            }}
                            sx={{ flexGrow: 1 }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box mt={1}>
                          {webhook.events.map((event) => (
                            <Chip key={event} label={event} size="small" sx={{ mr: 0.5 }} />
                          ))}
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => removeWebhook(index)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Grid>
          </Grid>
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          startIcon={<SaveIcon />}
        >
          Save Settings
        </Button>
      </DialogActions>
    </Dialog>
  );
};
