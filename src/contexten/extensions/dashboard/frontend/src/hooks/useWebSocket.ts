import { useEffect, useRef, useState } from 'react';
import { WebSocketEvent } from '../types';
import { useDashboardStore } from '../store/dashboardStore';

interface UseWebSocketOptions {
  onProjectUpdate?: (projectId: string, updateType: string, data: any) => void;
  onWorkflowEvent?: (projectId: string, eventType: string, data: any) => void;
  onMetricsUpdate?: (projectId: string, metrics: any) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const setStoreConnected = useDashboardStore(state => state.setConnected);

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      setStoreConnected(true);
      if (options.onConnectionChange) {
        options.onConnectionChange(true);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      setStoreConnected(false);
      if (options.onConnectionChange) {
        options.onConnectionChange(false);
      }
      wsRef.current = null;

      // Attempt to reconnect
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketEvent = JSON.parse(event.data);
        handleMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    wsRef.current = ws;
  };

  const handleMessage = (message: WebSocketEvent) => {
    switch (message.type) {
      case 'project_update':
        if (options.onProjectUpdate) {
          const { project_id, type, data } = message.payload;
          options.onProjectUpdate(project_id, type, data);
        }
        break;

      case 'workflow_event':
        if (options.onWorkflowEvent) {
          const { project_id, type, data } = message.payload;
          options.onWorkflowEvent(project_id, type, data);
        }
        break;

      case 'metrics_update':
        if (options.onMetricsUpdate) {
          const { project_id, metrics } = message.payload;
          options.onMetricsUpdate(project_id, metrics);
        }
        break;

      default:
        console.warn('Unknown message type:', message.type);
    }
  };

  const subscribeToProject = (projectId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        project_id: projectId
      }));
    }
  };

  const unsubscribeFromProject = (projectId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        project_id: projectId
      }));
    }
  };

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    connected,
    subscribeToProject,
    unsubscribeFromProject
  };
};

export default useWebSocket;

