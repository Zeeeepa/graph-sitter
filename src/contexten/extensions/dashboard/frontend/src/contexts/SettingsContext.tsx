import React, { createContext, useContext, useState, useEffect } from 'react';
import { Settings } from '../types/dashboard';

interface SettingsContextType {
  settings: Settings;
  updateSettings: (newSettings: Partial<Settings>) => Promise<void>;
  validateToken: (key: keyof Settings, value: string) => Promise<boolean>;
  loading: boolean;
  error: string | null;
}

const SettingsContext = createContext<SettingsContextType>({
  settings: {
    githubToken: '',
    linearToken: '',
    codegenOrgId: '',
    codegenToken: '',
    prefectToken: '',
    controlFlowToken: '',
    agentFlowToken: '',
    webhookBaseUrl: 'https://api.dashboard.example.com',
  },
  updateSettings: async () => {},
  validateToken: async () => false,
  loading: false,
  error: null,
});

export const useSettings = () => useContext(SettingsContext);

interface SettingsProviderProps {
  children: React.ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<Settings>({
    githubToken: process.env.REACT_APP_GITHUB_TOKEN || '',
    linearToken: process.env.REACT_APP_LINEAR_TOKEN || '',
    codegenOrgId: process.env.REACT_APP_CODEGEN_ORG_ID || '',
    codegenToken: process.env.REACT_APP_CODEGEN_TOKEN || '',
    prefectToken: process.env.REACT_APP_PREFECT_TOKEN || '',
    controlFlowToken: process.env.REACT_APP_CONTROL_FLOW_TOKEN || '',
    agentFlowToken: process.env.REACT_APP_AGENT_FLOW_TOKEN || '',
    webhookBaseUrl: process.env.REACT_APP_WEBHOOK_BASE_URL || 'https://api.dashboard.example.com',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true);
        // Load settings from local storage
        const savedSettings = localStorage.getItem('dashboardSettings');
        if (savedSettings) {
          setSettings(prevSettings => ({
            ...prevSettings,
            ...JSON.parse(savedSettings),
          }));
        }
        setError(null);
      } catch (err) {
        console.error('Error loading settings:', err);
        setError('Failed to load settings');
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  const validateToken = async (key: keyof Settings, value: string): Promise<boolean> => {
    try {
      switch (key) {
        case 'githubToken':
          // Validate GitHub token
          const githubResponse = await fetch('https://api.github.com/user', {
            headers: {
              Authorization: `token ${value}`,
            },
          });
          return githubResponse.ok;

        case 'linearToken':
          // Validate Linear token
          const linearResponse = await fetch('https://api.linear.app/graphql', {
            method: 'POST',
            headers: {
              Authorization: value,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              query: '{ viewer { id } }',
            }),
          });
          return linearResponse.ok;

        case 'codegenToken':
          // Validate Codegen token
          if (!settings.codegenOrgId) return false;
          const codegenResponse = await fetch('https://api.codegen.sh/v1/validate', {
            headers: {
              Authorization: `Bearer ${value}`,
              'X-Organization-ID': settings.codegenOrgId,
            },
          });
          return codegenResponse.ok;

        case 'prefectToken':
          // Validate Prefect token
          const prefectResponse = await fetch('https://api.prefect.io/graphql', {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${value}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              query: '{ hello }',
            }),
          });
          return prefectResponse.ok;

        case 'controlFlowToken':
          // Validate ControlFlow token
          const controlFlowResponse = await fetch('https://api.controlflow.dev/validate', {
            headers: {
              Authorization: `Bearer ${value}`,
            },
          });
          return controlFlowResponse.ok;

        case 'agentFlowToken':
          // Validate Agent Flow token
          const agentFlowResponse = await fetch('https://api.agentflow.dev/validate', {
            headers: {
              Authorization: `Bearer ${value}`,
            },
          });
          return agentFlowResponse.ok;

        default:
          return true;
      }
    } catch (err) {
      console.error(`Error validating ${key}:`, err);
      return false;
    }
  };

  const updateSettings = async (newSettings: Partial<Settings>) => {
    try {
      const updatedSettings = {
        ...settings,
        ...newSettings,
      };

      // Validate required tokens
      const requiredTokens: (keyof Settings)[] = ['githubToken', 'linearToken', 'codegenToken'];
      for (const key of requiredTokens) {
        if (updatedSettings[key] && !(await validateToken(key, updatedSettings[key]))) {
          throw new Error(`Invalid ${key}`);
        }
      }

      setSettings(updatedSettings);
      // Save to local storage
      localStorage.setItem('dashboardSettings', JSON.stringify(updatedSettings));
      setError(null);
    } catch (err) {
      console.error('Error updating settings:', err);
      setError('Failed to update settings');
      throw err;
    }
  };

  return (
    <SettingsContext.Provider
      value={{
        settings,
        updateSettings,
        validateToken,
        loading,
        error,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
};

