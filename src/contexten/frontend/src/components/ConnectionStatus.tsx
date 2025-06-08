import React, { useState, useEffect } from 'react';
import websocketService from '../services/websocketService';
import { dashboardApi } from '../api/dashboardApi';

type ConnectionState = 'connected' | 'disconnected' | 'connecting' | 'error';

interface ConnectionStatusProps {
  className?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ className = '' }) => {
  const [wsStatus, setWsStatus] = useState<ConnectionState>('disconnected');
  const [apiStatus, setApiStatus] = useState<boolean>(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Listen to WebSocket connection status
    websocketService.addConnectionStatusListener((status: string) => {
      setWsStatus(status as ConnectionState);
    });

    // Check API health periodically
    const checkApiHealth = async () => {
      try {
        const health = await dashboardApi.checkHealth();
        setApiStatus(health.healthy);
      } catch (error) {
        setApiStatus(false);
      }
    };

    // Initial health check
    checkApiHealth();

    // Check API health every 30 seconds
    const healthInterval = setInterval(checkApiHealth, 30000);

    return () => {
      clearInterval(healthInterval);
    };
  }, []);

  const getStatusColor = () => {
    if (wsStatus === 'connected' && apiStatus) return 'connected';
    if (wsStatus === 'connecting') return 'connecting';
    return 'disconnected';
  };

  const getStatusText = () => {
    if (wsStatus === 'connected' && apiStatus) return 'Connected';
    if (wsStatus === 'connecting') return 'Connecting...';
    if (wsStatus === 'error' || !apiStatus) return 'Connection Error';
    return 'Disconnected';
  };

  const getStatusIcon = () => {
    const status = getStatusColor();
    switch (status) {
      case 'connected':
        return '🟢';
      case 'connecting':
        return '🟡';
      default:
        return '🔴';
    }
  };

  const handleRetry = () => {
    websocketService.reconnect();
  };

  const toggleDetails = () => {
    setShowDetails(!showDetails);
  };

  return (
    <div className={`connection-status ${getStatusColor()} ${className}`}>
      <div 
        className="status-indicator"
        onClick={toggleDetails}
        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
      >
        <span>{getStatusIcon()}</span>
        <span>{getStatusText()}</span>
        <span style={{ fontSize: '0.8rem' }}>{showDetails ? '▼' : '▶'}</span>
      </div>
      
      {showDetails && (
        <div className="status-details" style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-primary)',
          borderRadius: '6px',
          padding: '1rem',
          minWidth: '200px',
          boxShadow: 'var(--shadow-md)',
          zIndex: 1000,
          marginTop: '0.5rem'
        }}>
          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Connection Status</strong>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
            <span>WebSocket:</span>
            <span className={`status-${wsStatus}`}>
              {wsStatus === 'connected' ? '🟢 Connected' : 
               wsStatus === 'connecting' ? '🟡 Connecting' : 
               wsStatus === 'error' ? '🔴 Error' : '🔴 Disconnected'}
            </span>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span>API:</span>
            <span className={apiStatus ? 'status-active' : 'status-danger'}>
              {apiStatus ? '🟢 Healthy' : '🔴 Unavailable'}
            </span>
          </div>
          
          {(wsStatus !== 'connected' || !apiStatus) && (
            <button 
              onClick={handleRetry}
              style={{
                width: '100%',
                padding: '0.5rem',
                backgroundColor: 'var(--accent-secondary)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem'
              }}
            >
              Retry Connection
            </button>
          )}
          
          <div style={{ 
            marginTop: '0.75rem', 
            fontSize: '0.75rem', 
            color: 'var(--text-muted)',
            borderTop: '1px solid var(--border-primary)',
            paddingTop: '0.5rem'
          }}>
            {wsStatus === 'error' && 'WebSocket connection failed. Check if the backend is running.'}
            {!apiStatus && 'API is not responding. Please check your connection.'}
            {wsStatus === 'connected' && apiStatus && 'All systems operational.'}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;
