import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import toast from 'react-hot-toast';

import { useDashboardStore } from '../store/dashboardStore';
import { WebSocketMessage } from '../types';

export const useWebSocket = () => {
  const socketRef = useRef<Socket | null>(null);
  const { 
    user, 
    setConnected, 
    updateProject, 
    addWorkflowPlan, 
    updateWorkflowPlan 
  } = useDashboardStore();

  useEffect(() => {
    // Initialize WebSocket connection
    const initializeWebSocket = () => {
      const wsUrl = `ws://localhost:8000/ws/${user.id}`;
      
      try {
        socketRef.current = io(wsUrl, {
          transports: ['websocket'],
          autoConnect: true,
        });

        const socket = socketRef.current;

        // Connection events
        socket.on('connect', () => {
          console.log('WebSocket connected');
          setConnected(true);
          toast.success('Connected to dashboard');
        });

        socket.on('disconnect', () => {
          console.log('WebSocket disconnected');
          setConnected(false);
          toast.error('Disconnected from dashboard');
        });

        socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          setConnected(false);
          toast.error('Failed to connect to dashboard');
        });

        // Dashboard event handlers
        socket.on('connection_established', (data: any) => {
          console.log('Dashboard connection established:', data);
          
          // Subscribe to relevant topics
          socket.emit('subscribe', { topic: 'project_updates' });
          socket.emit('subscribe', { topic: 'workflow_updates' });
          socket.emit('subscribe', { topic: 'github_events' });
          socket.emit('subscribe', { topic: 'linear_events' });
        });

        socket.on('project_update', (message: WebSocketMessage) => {
          console.log('Project update received:', message);
          
          if (message.project_id && message.data) {
            updateProject(message.project_id, message.data);
            toast.success(`Project ${message.data.name || message.project_id} updated`);
          }
        });

        socket.on('workflow_update', (message: WebSocketMessage) => {
          console.log('Workflow update received:', message);
          
          if (message.workflow_id) {
            const { status, progress } = message;
            toast.success(`Workflow ${status}: ${progress}% complete`);
          }
        });

        socket.on('github_event', (message: WebSocketMessage) => {
          console.log('GitHub event received:', message);
          
          const { event_type, data } = message;
          
          switch (event_type) {
            case 'pull_request':
              if (data.action === 'opened') {
                toast(`New PR opened: ${data.pull_request?.title}`, { icon: 'ℹ️' });
              } else if (data.action === 'merged') {
                toast(`PR merged: ${data.pull_request?.title}`, { icon: '✅' });
              }
              break;
            case 'issues':
              if (data.action === 'opened') {
                toast(`New issue: ${data.issue?.title}`, { icon: 'ℹ️' });
              }
              break;
            case 'push':
              toast(`New commits pushed to ${data.ref}`, { icon: 'ℹ️' });
              break;
          }
        });

        socket.on('linear_event', (message: WebSocketMessage) => {
          console.log('Linear event received:', message);
          
          const { event_type, data } = message;
          
          if (event_type === 'issue_updated') {
            toast(`Linear issue updated: ${data.title}`, { icon: 'ℹ️' });
          }
        });

        socket.on('quality_gate_update', (message: WebSocketMessage) => {
          console.log('Quality gate update received:', message);
          
          const { gate_data } = message;
          
          if (gate_data.status === 'passed') {
            toast.success(`Quality gate passed: ${gate_data.gate_type}`);
          } else if (gate_data.status === 'failed') {
            toast.error(`Quality gate failed: ${gate_data.gate_type}`);
          }
        });

        socket.on('pr_update', (message: WebSocketMessage) => {
          console.log('PR update received:', message);
          
          const { pr_data } = message;
          
          if (pr_data.status === 'merged') {
            toast(`PR merged: ${pr_data.title}`, { icon: '✅' });
          } else if (pr_data.status === 'closed') {
            toast(`PR closed: ${pr_data.title}`, { icon: 'ℹ️' });
          }
        });

        // Handle ping/pong for connection health
        socket.on('pong', () => {
          console.log('WebSocket pong received');
        });

        // Send periodic ping to keep connection alive
        const pingInterval = setInterval(() => {
          if (socket.connected) {
            socket.emit('ping');
          }
        }, 30000); // Ping every 30 seconds

        // Cleanup interval on disconnect
        socket.on('disconnect', () => {
          clearInterval(pingInterval);
        });

      } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        setConnected(false);
      }
    };

    // Initialize WebSocket
    initializeWebSocket();

    // Cleanup on unmount
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
      setConnected(false);
    };
  }, [user.id, setConnected, updateProject, addWorkflowPlan, updateWorkflowPlan]);

  // Utility functions for sending messages
  const sendMessage = (type: string, data: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(type, data);
    } else {
      console.warn('WebSocket not connected, cannot send message:', type, data);
    }
  };

  const subscribeToTopic = (topic: string) => {
    sendMessage('subscribe', { topic });
  };

  const unsubscribeFromTopic = (topic: string) => {
    sendMessage('unsubscribe', { topic });
  };

  const getStatus = () => {
    sendMessage('get_status', {});
  };

  return {
    connected: socketRef.current?.connected || false,
    sendMessage,
    subscribeToTopic,
    unsubscribeFromTopic,
    getStatus,
  };
};
