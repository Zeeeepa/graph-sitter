import React from 'react';

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  // Mock WebSocket provider - just pass through children
  return <>{children}</>;
};
