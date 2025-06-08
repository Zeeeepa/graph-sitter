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
  Alert,
  CircularProgress,
  Grid,
  Divider,
  IconButton,
  InputAdornment,
  Tooltip,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  GitHub as GitHubIcon,
  LinearScale as LinearIcon,
  Code as CodegenIcon,
  DataObject as FlowIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useSettings } from '../contexts/SettingsContext';
import { Settings } from '../types/dashboard';

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
}

interface TokenField {
  key: keyof Settings;
  label: string;
  icon: React.ReactNode;
  required: boolean;
  tooltip: string;
}

const SettingsDialog: React.FC<SettingsDialogProps> = ({ open, onClose }) => {
  const { settings, updateSettings, validateToken } = useSettings();
  const [newSettings, setNewSettings] = useState<Settings>({ ...settings });
  const [showTokens, setShowTokens] = useState<Record<string, boolean>>({});
  const [validating, setValidating] = useState<Record<string, boolean>>({});
  const [validationStatus, setValidationStatus] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const tokenFields: TokenField[] = [
    {
      key: 'githubToken',
      label: 'GitHub Token',
      icon: <GitHubIcon />,
      required: true,
      tooltip: 'Required for repository access and project management',
    },
    {
      key: 'linearToken',
      label: 'Linear Token',
      icon: <LinearIcon />,
      required: true,
      tooltip: 'Required for task and issue management',
    },
    {
      key: 'codegenToken',
      label: 'Codegen Token',
      icon: <CodegenIcon />,
      required: true,
      tooltip: 'Required for code analysis and automation',
    },
    {
      key: 'codegenOrgId',
      label: 'Codegen Organization ID',
      icon: <CodegenIcon />,
      required: true,
      tooltip: 'Your Codegen organization identifier',
    },
    {
      key: 'prefectToken',
      label: 'Prefect Token',
      icon: <FlowIcon />,
      required: false,
      tooltip: 'Optional: For Prefect workflow integration',
    },
    {
      key: 'controlFlowToken',
      label: 'ControlFlow Token',
      icon: <FlowIcon />,
      required: false,
      tooltip: 'Optional: For ControlFlow integration',
    },
    {
      key: 'agentFlowToken',
      label: 'Agent Flow Token',
      icon: <FlowIcon />,
      required: false,
      tooltip: 'Optional: For Agent Flow integration',
    },
  ];

  const handleChange = (key: keyof Settings) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setNewSettings(prev => ({
      ...prev,
      [key]: event.target.value,
    }));
    setValidationStatus(prev => ({
      ...prev,
      [key]: false,
    }));
  };

  const toggleShowToken = (key: string) => {
    setShowTokens(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const validateTokenField = async (key: keyof Settings) => {
    if (!newSettings[key]) return;
    
    setValidating(prev => ({ ...prev, [key]: true }));
    try {
      const isValid = await validateToken(key, newSettings[key]);
      setValidationStatus(prev => ({ ...prev, [key]: isValid }));
    } catch (err) {
      setValidationStatus(prev => ({ ...prev, [key]: false }));
    } finally {
      setValidating(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleSave = async () => {
    try {
      // Validate required fields
      const missingRequired = tokenFields
        .filter(field => field.required && !newSettings[field.key])
        .map(field => field.label);

      if (missingRequired.length > 0) {
        setError(`Missing required fields: ${missingRequired.join(', ')}`);
        return;
      }

      await updateSettings(newSettings);
      onClose();
    } catch (err) {
      setError('Failed to save settings');
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
        },
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <SettingsIcon />
          <Typography variant="h6">Settings</Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {tokenFields.map(field => (
            <Grid item xs={12} key={field.key}>
              <Box display="flex" alignItems="center" gap={2}>
                {field.icon}
                <Tooltip title={field.tooltip}>
                  <TextField
                    fullWidth
                    label={field.label}
                    value={newSettings[field.key]}
                    onChange={handleChange(field.key)}
                    type={showTokens[field.key] ? 'text' : 'password'}
                    required={field.required}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => toggleShowToken(field.key)}
                            edge="end"
                          >
                            {showTokens[field.key] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                          {validating[field.key] ? (
                            <CircularProgress size={20} />
                          ) : validationStatus[field.key] ? (
                            <CheckIcon color="success" />
                          ) : validationStatus[field.key] === false ? (
                            <ErrorIcon color="error" />
                          ) : null}
                        </InputAdornment>
                      ),
                    }}
                  />
                </Tooltip>
              </Box>
            </Grid>
          ))}

          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Advanced Settings
            </Typography>
            <TextField
              fullWidth
              label="Webhook Base URL"
              value={newSettings.webhookBaseUrl}
              onChange={handleChange('webhookBaseUrl')}
              helperText="Base URL for webhook endpoints"
              sx={{ mt: 1 }}
            />
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={Object.values(validating).some(v => v)}
        >
          Save Settings
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SettingsDialog;

