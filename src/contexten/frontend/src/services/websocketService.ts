import { WebSocketEvent } from '../types/dashboard';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10; // Increased from 5
  private reconnectTimeout = 1000; // Start with 1 second
  private maxReconnectTimeout = 30000; // Max 30 seconds
  private listeners: ((event: WebSocketEvent) => void)[] = [];
  private connectionStatusListeners: ((status: 'connected' | 'disconnected' | 'connecting' | 'error') => void)[] = [];
  private isManuallyDisconnected = false;

  constructor(private url: string) {}

  connect() {
    if (this.isManuallyDisconnected) {
      return; // Don't auto-reconnect if manually disconnected
    }

    this.notifyConnectionStatus('connecting');
    
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        this.reconnectAttempts = 0;
        this.reconnectTimeout = 1000;
        this.notifyConnectionStatus('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketEvent;
          this.notifyListeners(data);
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected', event.code, event.reason);
        this.notifyConnectionStatus('disconnected');
        
        // Only attempt reconnection if not manually disconnected
        if (!this.isManuallyDisconnected) {
          this.handleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.notifyConnectionStatus('error');
      };
    } catch (error) {
      console.error('❌ Error creating WebSocket:', error);
      this.notifyConnectionStatus('error');
      this.handleReconnect();
    }
  }

  private handleReconnect() {
    if (this.isManuallyDisconnected) {
      return; // Don't reconnect if manually disconnected
    }

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = Math.min(this.reconnectTimeout, this.maxReconnectTimeout);
      console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts}) in ${delay}ms...`);
      
      setTimeout(() => {
        this.reconnectAttempts++;
        this.reconnectTimeout = Math.min(this.reconnectTimeout * 1.5, this.maxReconnectTimeout); // Exponential backoff with cap
        this.connect();
      }, delay);
    } else {
      console.error('❌ Max reconnection attempts reached. Please check your connection and refresh the page.');
      this.notifyConnectionStatus('error');
    }
  }

  disconnect() {
    this.isManuallyDisconnected = true;
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this.notifyConnectionStatus('disconnected');
    console.log('🔌 WebSocket manually disconnected');
  }

  reconnect() {
    this.isManuallyDisconnected = false;
    this.reconnectAttempts = 0;
    this.reconnectTimeout = 1000;
    this.connect();
  }

  addListener(callback: (event: WebSocketEvent) => void) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback);
    };
  }

  private notifyListeners(event: WebSocketEvent) {
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Error in WebSocket listener:', error);
      }
    });
  }

  // Send a message to the server
  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
      }
    } else {
      console.error('WebSocket is not connected');
    }
  }

  // Check if WebSocket is connected
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  addConnectionStatusListener(callback: (status: 'connected' | 'disconnected' | 'connecting' | 'error') => void) {
    this.connectionStatusListeners.push(callback);
  }

  private notifyConnectionStatus(status: 'connected' | 'disconnected' | 'connecting' | 'error') {
    this.connectionStatusListeners.forEach(listener => {
      try {
        listener(status);
      } catch (error) {
        console.error('Error in connection status listener:', error);
      }
    });
  }
}

// Create a singleton instance
const websocketService = new WebSocketService('ws://localhost:8000/ws');

export default websocketService;
