import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Typography, Button, Alert, AlertTitle } from '@mui/material';
import { Refresh as RefreshIcon, BugReport as BugReportIcon } from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="400px"
          padding={3}
          maxWidth="600px"
          margin="0 auto"
        >
          <Alert severity="error" sx={{ width: '100%', mb: 3 }}>
            <AlertTitle>
              <Box display="flex" alignItems="center" gap={1}>
                <BugReportIcon />
                Something went wrong
              </Box>
            </AlertTitle>
            <Typography variant="body2" sx={{ mt: 1 }}>
              An unexpected error occurred. Please try refreshing the page or contact support if the problem persists.
            </Typography>
          </Alert>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <Box
              sx={{
                width: '100%',
                backgroundColor: '#f5f5f5',
                padding: 2,
                borderRadius: 1,
                mb: 3,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                overflow: 'auto',
                maxHeight: '200px',
              }}
            >
              <Typography variant="subtitle2" color="error" gutterBottom>
                Error Details:
              </Typography>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                {this.state.error.toString()}
                {this.state.errorInfo?.componentStack}
              </pre>
            </Box>
          )}

          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={this.handleReload}
            >
              Reload Page
            </Button>
            <Button
              variant="outlined"
              onClick={this.handleReset}
            >
              Try Again
            </Button>
          </Box>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

