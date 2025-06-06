// Simplified API service for Strands Dashboard
import { WorkflowStatus, SystemHealth, CodegenTask, ApiResponse } from '../types';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class StrandsAPI {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  // System Health
  async getSystemHealth(): Promise<ApiResponse<SystemHealth>> {
    return this.request<SystemHealth>('/api/health');
  }

  // Workflows
  async getWorkflows(): Promise<ApiResponse<{ workflows: WorkflowStatus[] }>> {
    return this.request<{ workflows: WorkflowStatus[] }>('/api/workflows');
  }

  async createWorkflow(name: string): Promise<ApiResponse<WorkflowStatus>> {
    return this.request<WorkflowStatus>('/api/workflows', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async restartWorkflow(workflowId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/workflows/${workflowId}/restart`, {
      method: 'POST',
    });
  }

  // Codegen Tasks
  async getCodegenTasks(): Promise<ApiResponse<{ tasks: CodegenTask[] }>> {
    return this.request<{ tasks: CodegenTask[] }>('/api/codegen/tasks');
  }

  async createCodegenTask(prompt: string): Promise<ApiResponse<CodegenTask>> {
    return this.request<CodegenTask>('/api/codegen/tasks', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  }

  // WebSocket connection helper
  createWebSocketConnection(onMessage: (data: any) => void, onConnectionChange: (connected: boolean) => void): WebSocket {
    const ws = new WebSocket(`ws://localhost:8000/ws`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      onConnectionChange(true);
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        onMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      onConnectionChange(false);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onConnectionChange(false);
    };

    return ws;
  }
}

export const strandsAPI = new StrandsAPI();
export default strandsAPI;

