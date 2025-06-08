/**
 * WebSocket hook for real-time communication with the backend
 */
import { useState, useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (url, options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionStats, setConnectionStats] = useState({
    attempts: 0,
    lastConnected: null,
    lastDisconnected: null,
  });
  
  const ws = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);
  const reconnectAttempts = useRef(0);
  
  const {
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    heartbeatInterval = 30000,
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options;

  const connect = useCallback(() => {
    try {
      // Close existing connection
      if (ws.current) {
        ws.current.close();
      }

      console.log(`Attempting to connect to WebSocket: ${url}`);
      ws.current = new WebSocket(url);

      ws.current.onopen = (event) => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        
        setConnectionStats(prev => ({
          ...prev,
          lastConnected: new Date().toISOString(),
          attempts: prev.attempts + 1,
        }));

        // Start heartbeat
        if (heartbeatInterval > 0) {
          heartbeatIntervalRef.current = setInterval(() => {
            if (ws.current?.readyState === WebSocket.OPEN) {
              ws.current.send(JSON.stringify({ type: 'ping' }));
            }
          }, heartbeatInterval);
        }

        if (onOpen) onOpen(event);
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        setIsConnected(false);
        
        setConnectionStats(prev => ({
          ...prev,
          lastDisconnected: new Date().toISOString(),
        }));

        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }

        if (onClose) onClose(event);
      };

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        if (onError) onError(event);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle internal messages
          if (data.type === 'pong') {
            // Heartbeat response
            return;
          }
          
          if (data.type === 'connection_established') {
            console.log('Connection established:', data);
            return;
          }

          setLastMessage(event);
          if (onMessage) onMessage(event);
          
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          setLastMessage(event);
          if (onMessage) onMessage(event);
        }
      };

    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setIsConnected(false);
    }
  }, [url, onOpen, onClose, onError, onMessage, maxReconnectAttempts, heartbeatInterval]);

  const disconnect = useCallback(() => {
    console.log('Manually disconnecting WebSocket');
    
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    // Clear heartbeat
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    
    // Close connection
    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
      ws.current = null;
    }
    
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
        ws.current.send(messageStr);
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        return false;
      }
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', message);
      return false;
    }
  }, []);

  const subscribeToProject = useCallback((projectId) => {
    return sendMessage({
      type: 'subscribe_project',
      project_id: projectId,
    });
  }, [sendMessage]);

  const unsubscribeFromProject = useCallback((projectId) => {
    return sendMessage({
      type: 'unsubscribe_project',
      project_id: projectId,
    });
  }, [sendMessage]);

  const getConnectionStats = useCallback(() => {
    return sendMessage({
      type: 'get_connection_stats',
    });
  }, [sendMessage]);

  // Connect on mount
  useEffect(() => {
    connect();
    
    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, reduce heartbeat frequency or pause
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = setInterval(() => {
            if (ws.current?.readyState === WebSocket.OPEN) {
              ws.current.send(JSON.stringify({ type: 'ping' }));
            }
          }, heartbeatInterval * 2); // Double the interval when hidden
        }
      } else {
        // Page is visible, restore normal heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = setInterval(() => {
            if (ws.current?.readyState === WebSocket.OPEN) {
              ws.current.send(JSON.stringify({ type: 'ping' }));
            }
          }, heartbeatInterval);
        }
        
        // Reconnect if disconnected while hidden
        if (!isConnected && reconnectAttempts.current < maxReconnectAttempts) {
          connect();
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isConnected, connect, heartbeatInterval, maxReconnectAttempts]);

  // Handle online/offline events
  useEffect(() => {
    const handleOnline = () => {
      console.log('Network is online, attempting to reconnect WebSocket');
      if (!isConnected && reconnectAttempts.current < maxReconnectAttempts) {
        connect();
      }
    };

    const handleOffline = () => {
      console.log('Network is offline');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isConnected, connect, maxReconnectAttempts]);

  return {
    isConnected,
    lastMessage,
    connectionStats,
    sendMessage,
    subscribeToProject,
    unsubscribeFromProject,
    getConnectionStats,
    connect,
    disconnect,
    readyState: ws.current?.readyState,
  };
};

// WebSocket ready states for reference
export const WebSocketReadyState = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
};

// Helper hook for handling specific message types
export const useWebSocketMessages = (messageHandlers = {}) => {
  const [messages, setMessages] = useState([]);
  const [lastMessageByType, setLastMessageByType] = useState({});

  const handleMessage = useCallback((event) => {
    try {
      const data = JSON.parse(event.data);
      const messageType = data.type;
      
      // Store all messages
      setMessages(prev => [...prev.slice(-99), data]); // Keep last 100 messages
      
      // Store last message by type
      setLastMessageByType(prev => ({
        ...prev,
        [messageType]: data,
      }));
      
      // Call specific handler if available
      if (messageHandlers[messageType]) {
        messageHandlers[messageType](data);
      }
      
      // Call general handler if available
      if (messageHandlers.onMessage) {
        messageHandlers.onMessage(data);
      }
      
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }, [messageHandlers]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastMessageByType({});
  }, []);

  const getMessagesByType = useCallback((type) => {
    return messages.filter(msg => msg.type === type);
  }, [messages]);

  return {
    messages,
    lastMessageByType,
    handleMessage,
    clearMessages,
    getMessagesByType,
  };
};

export default useWebSocket;

