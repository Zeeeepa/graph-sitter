import React from 'react';
import {
  Box,
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
  useMediaQuery,
} from '@mui/material';
import TopBar from '../components/TopBar';
import { SettingsProvider } from '../contexts/SettingsContext';
import { ProjectProvider } from '../contexts/ProjectContext';
import { WebSocketProvider } from '../contexts/WebSocketContext';

const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  const theme = React.useMemo(
    () =>
      createTheme({
        palette: {
          mode: prefersDarkMode ? 'dark' : 'light',
          primary: {
            main: '#2196f3',
          },
          secondary: {
            main: '#f50057',
          },
          background: {
            default: prefersDarkMode ? '#121212' : '#f5f5f5',
            paper: prefersDarkMode ? '#1e1e1e' : '#ffffff',
          },
        },
        components: {
          MuiCard: {
            styleOverrides: {
              root: {
                borderRadius: 12,
                boxShadow: prefersDarkMode
                  ? '0 4px 6px rgba(0, 0, 0, 0.2)'
                  : '0 4px 6px rgba(0, 0, 0, 0.1)',
              },
            },
          },
          MuiChip: {
            styleOverrides: {
              root: {
                borderRadius: 8,
              },
            },
          },
          MuiButton: {
            styleOverrides: {
              root: {
                borderRadius: 8,
                textTransform: 'none',
              },
            },
          },
        },
      }),
    [prefersDarkMode]
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SettingsProvider>
        <WebSocketProvider>
          <ProjectProvider>
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                minHeight: '100vh',
                bgcolor: 'background.default',
              }}
            >
              <TopBar />
              <Container
                maxWidth="xl"
                sx={{
                  mt: 4,
                  mb: 4,
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                {children}
              </Container>
            </Box>
          </ProjectProvider>
        </WebSocketProvider>
      </SettingsProvider>
    </ThemeProvider>
  );
};

export default DashboardLayout;

