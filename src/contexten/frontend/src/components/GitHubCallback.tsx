import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';
import { handleGitHubCallback } from '../services/githubService';

const GitHubCallback: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const processCallback = async () => {
      try {
        // Get the code from the URL query parameters
        const searchParams = new URLSearchParams(location.search);
        const code = searchParams.get('code');
        
        if (!code) {
          throw new Error('No authorization code found in the URL');
        }
        
        // Exchange the code for a token
        await handleGitHubCallback(code);
        
        // Redirect back to the settings page or dashboard
        setTimeout(() => {
          navigate('/dashboard');
        }, 1500);
      } catch (err) {
        console.error('Error during GitHub callback:', err);
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    processCallback();
  }, [location, navigate]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: 3,
      }}
    >
      {loading ? (
        <>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 3 }}>
            Completing GitHub authentication...
          </Typography>
        </>
      ) : error ? (
        <>
          <Alert severity="error" sx={{ width: '100%', maxWidth: 500 }}>
            {error}
          </Alert>
          <Typography variant="body1" sx={{ mt: 2 }}>
            You will be redirected back to the dashboard in a few seconds.
          </Typography>
        </>
      ) : (
        <>
          <Alert severity="success" sx={{ width: '100%', maxWidth: 500 }}>
            Successfully authenticated with GitHub!
          </Alert>
          <Typography variant="body1" sx={{ mt: 2 }}>
            You will be redirected back to the dashboard in a few seconds.
          </Typography>
        </>
      )}
    </Box>
  );
};

export default GitHubCallback;

