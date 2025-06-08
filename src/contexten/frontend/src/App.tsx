import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

// Components
import Dashboard from './components/Dashboard';
import ProjectSelectionDialog from './components/ProjectSelectionDialog';
import ConnectionStatus from './components/ConnectionStatus';

// Services
import websocketService from './services/websocketService';
import { dashboardApi } from './api/dashboardApi';

// Styles
import './index.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeApp = async () => {
      try {
        console.log('🚀 Initializing Graph-Sitter Dashboard...');
        
        // Connect to WebSocket
        websocketService.connect();
        
        // Listen for WebSocket events
        const unsubscribe = websocketService.addListener((event) => {
          console.log('📡 WebSocket event received:', event);
          // Handle real-time updates here
        });

        // Test API connection
        try {
          const projectsData = await dashboardApi.getProjects();
          console.log('✅ API connection successful, loaded', projectsData.length, 'projects');
        } catch (apiError) {
          console.warn('⚠️ API connection failed, using fallback data');
        }

        setIsLoading(false);

        // Cleanup function
        return () => {
          websocketService.disconnect();
          unsubscribe();
        };
      } catch (err) {
        console.error('❌ Failed to initialize app:', err);
        setError(err instanceof Error ? err.message : 'Failed to initialize application');
        setIsLoading(false);
      }
    };

    initializeApp();
  }, []);

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-primary)'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
          <div>Loading Graph-Sitter Dashboard...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-primary)'
      }}>
        <div style={{ textAlign: 'center', maxWidth: '400px' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>❌</div>
          <h2 style={{ color: 'var(--accent-danger)', marginBottom: '1rem' }}>
            Initialization Error
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            {error}
          </p>
          <button 
            onClick={() => window.location.reload()}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'var(--accent-secondary)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App" style={{ backgroundColor: 'var(--bg-primary)', minHeight: '100vh' }}>
          {/* Connection Status Indicator */}
          <ConnectionStatus />
          
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route 
              path="/projects" 
              element={
                <ProjectSelectionDialog 
                  open={true}
                  onClose={() => window.history.back()}
                  repositories={[]}
                />
              } 
            />
          </Routes>
        </div>
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
