import React, { createContext, useContext, useState, useEffect } from 'react';
import { Settings } from '../types/dashboard';

interface SettingsContextType extends Settings {
  updateSettings: (settings: Partial<Settings>) => void;
  validateSettings: () => Promise<boolean>;
}

const defaultSettings: Settings = {
  githubToken: '',
  linearToken: '',
  codegenOrgId: '',
  codegenToken: '',
  autoStartFlows: false,
  enableNotifications: true,
  enableAnalytics: true,
};

export const SettingsContext = createContext<SettingsContextType | null>(null);

interface SettingsProviderProps {
  children: React.ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<Settings>(defaultSettings);

  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('dashboardSettings');
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (error) {
        console.error('Error loading settings:', error);
      }
    }
  }, []);

  const updateSettings = (newSettings: Partial<Settings>) => {
    const updatedSettings = { ...settings, ...newSettings };
    setSettings(updatedSettings);
    localStorage.setItem('dashboardSettings', JSON.stringify(updatedSettings));
  };

  const validateSettings = async (): Promise<boolean> => {
    try {
      // Validate GitHub token
      const githubResponse = await fetch('https://api.github.com/user', {
        headers: {
          Authorization: `Bearer ${settings.githubToken}`,
        },
      });
      if (!githubResponse.ok) {
        throw new Error('Invalid GitHub token');
      }

      // Validate Linear token
      const linearResponse = await fetch('https://api.linear.app/graphql', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${settings.linearToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: `
            query {
              viewer {
                id
              }
            }
          `,
        }),
      });
      if (!linearResponse.ok) {
        throw new Error('Invalid Linear token');
      }

      // Validate Codegen credentials
      const codegenResponse = await fetch('https://api.codegen.sh/validate', {
        method: 'POST',
        headers: {
          'X-Organization-ID': settings.codegenOrgId,
          Authorization: `Bearer ${settings.codegenToken}`,
        },
      });
      if (!codegenResponse.ok) {
        throw new Error('Invalid Codegen credentials');
      }

      return true;
    } catch (error) {
      console.error('Settings validation error:', error);
      return false;
    }
  };

  return (
    <SettingsContext.Provider
      value={{
        ...settings,
        updateSettings,
        validateSettings,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

