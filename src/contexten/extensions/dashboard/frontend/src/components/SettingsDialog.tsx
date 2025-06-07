import React, { useState, useEffect } from 'react';

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (settings: EnvironmentSettings) => void;
}

export interface EnvironmentSettings {
  github_token: string;
  linear_api_key: string;
  slack_bot_token: string;
  codegen_org_id: string;
  codegen_token: string;
  postgresql_url: string;
  circleci_token: string;
}

export const SettingsDialog: React.FC<SettingsDialogProps> = ({
  isOpen,
  onClose,
  onSave
}) => {
  const [settings, setSettings] = useState<EnvironmentSettings>({
    github_token: '',
    linear_api_key: '',
    slack_bot_token: '',
    codegen_org_id: '',
    codegen_token: '',
    postgresql_url: '',
    circleci_token: ''
  });

  const [isValidating, setIsValidating] = useState(false);
  const [validationResults, setValidationResults] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (isOpen) {
      // Load current settings
      loadCurrentSettings();
    }
  }, [isOpen]);

  const loadCurrentSettings = async () => {
    try {
      const response = await fetch('/api/settings');
      if (response.ok) {
        const currentSettings = await response.json();
        setSettings(currentSettings);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const validateSettings = async () => {
    setIsValidating(true);
    const results: Record<string, boolean> = {};

    try {
      const response = await fetch('/api/settings/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      if (response.ok) {
        const validation = await response.json();
        Object.assign(results, validation);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }

    setValidationResults(results);
    setIsValidating(false);
  };

  const handleSave = async () => {
    await validateSettings();
    
    // Check if all validations passed
    const allValid = Object.values(validationResults).every(valid => valid);
    
    if (allValid) {
      onSave(settings);
      onClose();
    }
  };

  const settingsFields = [
    {
      key: 'github_token' as keyof EnvironmentSettings,
      label: 'GitHub Token',
      description: 'Personal access token for GitHub API access',
      placeholder: 'ghp_...',
      type: 'password'
    },
    {
      key: 'linear_api_key' as keyof EnvironmentSettings,
      label: 'Linear API Key',
      description: 'API key for Linear integration',
      placeholder: 'lin_api_...',
      type: 'password'
    },
    {
      key: 'slack_bot_token' as keyof EnvironmentSettings,
      label: 'Slack Bot Token',
      description: 'Bot token for Slack integration',
      placeholder: 'xoxb-...',
      type: 'password'
    },
    {
      key: 'codegen_org_id' as keyof EnvironmentSettings,
      label: 'Codegen Organization ID',
      description: 'Your Codegen organization identifier',
      placeholder: 'org_...',
      type: 'text'
    },
    {
      key: 'codegen_token' as keyof EnvironmentSettings,
      label: 'Codegen API Token',
      description: 'API token for Codegen SDK access',
      placeholder: 'cg_...',
      type: 'password'
    },
    {
      key: 'postgresql_url' as keyof EnvironmentSettings,
      label: 'PostgreSQL URL',
      description: 'Database connection string',
      placeholder: 'postgresql://user:pass@host:port/db',
      type: 'password'
    },
    {
      key: 'circleci_token' as keyof EnvironmentSettings,
      label: 'CircleCI Token',
      description: 'API token for CircleCI integration',
      placeholder: 'circle_...',
      type: 'password'
    }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Environment Settings</h2>
            <p className="text-sm text-gray-600">Configure API keys and environment variables</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[70vh]">
          <div className="space-y-6">
            {settingsFields.map((field) => (
              <div key={field.key}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {field.label}
                </label>
                <p className="text-xs text-gray-500 mb-2">{field.description}</p>
                <div className="relative">
                  <input
                    type={field.type}
                    value={settings[field.key]}
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      [field.key]: e.target.value
                    }))}
                    placeholder={field.placeholder}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      validationResults[field.key] === false 
                        ? 'border-red-300 bg-red-50' 
                        : validationResults[field.key] === true
                        ? 'border-green-300 bg-green-50'
                        : 'border-gray-300'
                    }`}
                  />
                  {validationResults[field.key] === true && (
                    <div className="absolute right-3 top-2 text-green-500">✓</div>
                  )}
                  {validationResults[field.key] === false && (
                    <div className="absolute right-3 top-2 text-red-500">✗</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center p-6 border-t border-gray-200">
          <button
            onClick={validateSettings}
            disabled={isValidating}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 disabled:bg-gray-400"
          >
            {isValidating ? 'Validating...' : 'Validate Settings'}
          </button>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

