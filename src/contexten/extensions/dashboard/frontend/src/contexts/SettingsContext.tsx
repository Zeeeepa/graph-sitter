import React, { createContext, useContext, useState, useEffect } from 'react';
import { Settings } from '../types/dashboard';

interface SettingsContextType {
  settings: Settings;
  updateSettings: (newSettings: Partial<Settings>) => void;
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
    webhookBaseUrl: '',
  },
  updateSettings: () => {},
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

  const updateSettings = async (newSettings: Partial<Settings>) => {
    try {
      const updatedSettings = {
        ...settings,
        ...newSettings,
      };
      setSettings(updatedSettings);
      // Save to local storage
      localStorage.setItem('dashboardSettings', JSON.stringify(updatedSettings));
      setError(null);
    } catch (err) {
      console.error('Error updating settings:', err);
      setError('Failed to update settings');
    }
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, loading, error }}>
      {children}
    </SettingsContext.Provider>
  );
};

