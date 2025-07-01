import React, { useState } from 'react';
import { Button, CircularProgress } from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import { initiateGitHubLogin, isGitHubAuthenticated, logoutFromGitHub } from '../services/githubService';
import { GitHubLoginButtonProps } from '../types/github';

const GitHubLoginButton: React.FC<GitHubLoginButtonProps> = ({
  className,
  variant = 'contained',
  size = 'medium',
  fullWidth = false,
  disabled = false,
  onSuccess,
  onError,
}) => {
  const [loading, setLoading] = useState(false);
  const authenticated = isGitHubAuthenticated();

  const handleLogin = async () => {
    if (authenticated) {
      // If already authenticated, log out
      try {
        logoutFromGitHub();
        window.location.reload(); // Reload to update UI
      } catch (error) {
        console.error('Error logging out from GitHub:', error);
        onError?.(error instanceof Error ? error : new Error(String(error)));
      }
      return;
    }

    setLoading(true);
    try {
      initiateGitHubLogin();
      // Note: The actual success callback will happen after the redirect
    } catch (error) {
      console.error('Error initiating GitHub login:', error);
      setLoading(false);
      onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      disabled={disabled || loading}
      onClick={handleLogin}
      className={className}
      startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <GitHubIcon />}
      sx={{
        backgroundColor: authenticated ? '#2da44e' : '#24292e',
        '&:hover': {
          backgroundColor: authenticated ? '#2c974b' : '#2b3137',
        },
      }}
    >
      {authenticated ? 'Logout from GitHub' : 'Login with GitHub'}
    </Button>
  );
};

export default GitHubLoginButton;

