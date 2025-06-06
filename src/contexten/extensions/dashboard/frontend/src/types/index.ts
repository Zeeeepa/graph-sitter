// Strands Dashboard Types
export interface WorkflowStatus {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

export interface SystemHealth {
  status: string;
  uptime: number;
  active_workflows: number;
  error_count: number;
  last_check: string;
}

export interface CodegenTask {
  id: string;
  prompt: string;
  status: string;
  result?: string;
  created_at: string;
}

export interface WebSocketMessage {
  type: 'system_health' | 'workflow_update' | 'codegen_update';
  data: any;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface CreateWorkflowRequest {
  name: string;
}

export interface CreateCodegenTaskRequest {
  prompt: string;
}

