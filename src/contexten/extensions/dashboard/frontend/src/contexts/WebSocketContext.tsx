import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useSettings } from './SettingsContext';
import { WebSocketEvent } from '../types/dashboard';

interface WebSocketContextType {
  connected: boolean;
  lastEvent: WebSocketEvent | null;
  sendMessage: (message: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType>({
  connected: false,
  lastEvent: null,
  sendMessage: () => {},
});

export const useWebSocket = () => useContext(WebSocketContext);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const { settings } = useSettings();
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${settings.webhookBaseUrl.replace('http', 'ws')}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      // Send authentication message
      ws.send(JSON.stringify({
        type: 'auth',
        data: {
          githubToken: settings.githubToken,
          linearToken: settings.linearToken,
          codegenToken: settings.codegenToken,
        },
      }));
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      wsRef.current = null;

      // Attempt to reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      try {
        const wsEvent: WebSocketEvent = JSON.parse(event.data);
        setLastEvent(wsEvent);

        // Handle different event types
        switch (wsEvent.type) {
          case 'project_updated':
            // Emit event for project updates
            window.dispatchEvent(new CustomEvent('project_updated', {
              detail: wsEvent.data,
            }));
            break;

          case 'flow_status':
            // Emit event for flow status changes
            window.dispatchEvent(new CustomEvent('flow_status', {
              detail: wsEvent.data,
            }));
            break;

          case 'task_updated':
            // Emit event for task updates
            window.dispatchEvent(new CustomEvent('task_updated', {
              detail: wsEvent.data,
            }));
            break;

          case 'error':
            console.error('WebSocket error event:', wsEvent.data);
            break;

          default:
            console.log('Unhandled WebSocket event:', wsEvent);
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };

    wsRef.current = ws;
  };

  useEffect(() => {
    if (settings.webhookBaseUrl) {
      connect();
    }

    return () => {
      // Clean up WebSocket connection
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [settings.webhookBaseUrl]);

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  return (
    <WebSocketContext.Provider
      value={{
        connected,
        lastEvent,
        sendMessage,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

