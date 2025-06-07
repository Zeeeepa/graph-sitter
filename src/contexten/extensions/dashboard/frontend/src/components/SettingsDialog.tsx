import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Box,
  Typography
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
}

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
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SettingsDialog: React.FC<SettingsDialogProps> = ({ open, onClose }) => {
  const [tabValue, setTabValue] = useState(0);
  const [showTokens, setShowTokens] = useState(false);
  const [settings, setSettings] = useState({
    githubToken: '',
    linearToken: '',
    codegenOrgId: '',
    codegenToken: '',
    postgresqlUrl: '',
    slackToken: '',
    autoStartFlows: true,
    enableNotifications: true,
    enableAnalytics: true
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSettingChange = (key: string, value: string | boolean) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = () => {
    // Mock save functionality
    console.log('Saving settings:', settings);
    onClose();
  };

  const validateSettings = () => {
    const required = ['githubToken', 'linearToken', 'codegenOrgId', 'codegenToken'];
    return required.every(key => settings[key as keyof typeof settings]);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h5">Settings</Typography>
        <Typography variant="body2" color="text.secondary">
          Configure API keys and system preferences
        </Typography>
      </DialogTitle>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
          <Tab label="API Configuration" />
          <Tab label="Preferences" />
          <Tab label="Advanced" />
        </Tabs>
      </Box>
      
      <DialogContent sx={{ minHeight: 400 }}>
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            API Keys & Tokens
          </Typography>
          
          <Alert severity="info" sx={{ mb: 3 }}>
            These credentials are required for the dashboard to function properly. 
            All tokens are stored securely and never shared.
          </Alert>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="GitHub Token"
              type={showTokens ? 'text' : 'password'}
              value={settings.githubToken}
              onChange={(e) => handleSettingChange('githubToken', e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
              helperText="Personal access token for GitHub API access"
            />
            
            <TextField
              fullWidth
              label="Linear Token"
              type={showTokens ? 'text' : 'password'}
              value={settings.linearToken}
              onChange={(e) => handleSettingChange('linearToken', e.target.value)}
              placeholder="lin_api_xxxxxxxxxxxxxxxxxxxx"
              helperText="API key for Linear integration"
            />
            
            <TextField
              fullWidth
              label="Codegen Organization ID"
              value={settings.codegenOrgId}
              onChange={(e) => handleSettingChange('codegenOrgId', e.target.value)}
              placeholder="org_xxxxxxxxxxxxxxxxxxxx"
              helperText="Your Codegen organization identifier"
            />
            
            <TextField
              fullWidth
              label="Codegen Token"
              type={showTokens ? 'text' : 'password'}
              value={settings.codegenToken}
              onChange={(e) => handleSettingChange('codegenToken', e.target.value)}
              placeholder="cg_xxxxxxxxxxxxxxxxxxxx"
              helperText="API token for Codegen SDK"
            />
            
            <TextField
              fullWidth
              label="PostgreSQL URL (Optional)"
              value={settings.postgresqlUrl}
              onChange={(e) => handleSettingChange('postgresqlUrl', e.target.value)}
              placeholder="postgresql://user:password@localhost:5432/dashboard"
              helperText="Database connection string for persistence"
            />
            
            <TextField
              fullWidth
              label="Slack Token (Optional)"
              type={showTokens ? 'text' : 'password'}
              value={settings.slackToken}
              onChange={(e) => handleSettingChange('slackToken', e.target.value)}
              placeholder="xoxb-xxxxxxxxxxxxxxxxxxxx"
              helperText="Bot token for Slack notifications"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={showTokens}
                  onChange={(e) => setShowTokens(e.target.checked)}
                />
              }
              label="Show tokens"
            />
          </Box>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            System Preferences
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.autoStartFlows}
                  onChange={(e) => handleSettingChange('autoStartFlows', e.target.checked)}
                />
              }
              label="Auto-start workflows when plans are generated"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableNotifications}
                  onChange={(e) => handleSettingChange('enableNotifications', e.target.checked)}
                />
              }
              label="Enable desktop notifications"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableAnalytics}
                  onChange={(e) => handleSettingChange('enableAnalytics', e.target.checked)}
                />
              }
              label="Enable analytics and usage tracking"
            />
          </Box>
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Advanced Configuration
          </Typography>
          
          <Alert severity="warning" sx={{ mb: 2 }}>
            Advanced settings should only be modified by experienced users.
          </Alert>
          
          <Typography variant="body2" color="text.secondary">
            Advanced configuration options will be available in future releases.
            This includes custom webhook endpoints, advanced workflow settings,
            and integration with external monitoring systems.
          </Typography>
        </TabPanel>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          onClick={handleSave} 
          variant="contained"
          startIcon={<SaveIcon />}
          disabled={!validateSettings()}
        >
          Save Settings
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SettingsDialog;
