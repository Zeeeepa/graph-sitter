import { WorkflowEvent } from '../types/dashboard';

export interface FlowConfig {
  prefectUrl: string;
  prefectToken: string;
  controlFlowUrl: string;
  controlFlowToken: string;
  agentFlowUrl: string;
  agentFlowToken: string;
}

export interface FlowStatus {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  startTime: string;
  endTime?: string;
  progress: number;
  logs: string[];
  error?: string;
}

export interface FlowRun {
  id: string;
  flowId: string;
  status: FlowStatus['status'];
  startTime: string;
  endTime?: string;
  parameters: Record<string, any>;
  result?: any;
}

export interface FlowMetrics {
  totalRuns: number;
  successfulRuns: number;
  failedRuns: number;
  averageDuration: number;
  lastRunStatus: FlowStatus['status'];
}

export class FlowService {
  private config: FlowConfig;

  constructor(config: FlowConfig) {
    this.config = config;
  }

  private async prefectRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.config.prefectUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.config.prefectToken}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`Prefect API error: ${response.statusText}`);
    }

    return response.json();
  }

  private async controlFlowRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.config.controlFlowUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.config.controlFlowToken}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`ControlFlow API error: ${response.statusText}`);
    }

    return response.json();
  }

  private async agentFlowRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.config.agentFlowUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.config.agentFlowToken}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`AgentFlow API error: ${response.statusText}`);
    }

    return response.json();
  }

  // Prefect Flow Management
  async startPrefectFlow(flowId: string, parameters: Record<string, any>): Promise<FlowRun> {
    return this.prefectRequest<FlowRun>('/flows/start', {
      method: 'POST',
      body: JSON.stringify({
        flowId,
        parameters,
      }),
    });
  }

  async stopPrefectFlow(runId: string): Promise<void> {
    await this.prefectRequest(`/flows/${runId}/stop`, {
      method: 'POST',
    });
  }

  async getPrefectFlowStatus(runId: string): Promise<FlowStatus> {
    return this.prefectRequest<FlowStatus>(`/flows/${runId}/status`);
  }

  // ControlFlow Management
  async startControlFlow(flowId: string, parameters: Record<string, any>): Promise<FlowRun> {
    return this.controlFlowRequest<FlowRun>('/flows/start', {
      method: 'POST',
      body: JSON.stringify({
        flowId,
        parameters,
      }),
    });
  }

  async stopControlFlow(runId: string): Promise<void> {
    await this.controlFlowRequest(`/flows/${runId}/stop`, {
      method: 'POST',
    });
  }

  async getControlFlowStatus(runId: string): Promise<FlowStatus> {
    return this.controlFlowRequest<FlowStatus>(`/flows/${runId}/status`);
  }

  // Agent Flow Management
  async startAgentFlow(flowId: string, parameters: Record<string, any>): Promise<FlowRun> {
    return this.agentFlowRequest<FlowRun>('/flows/start', {
      method: 'POST',
      body: JSON.stringify({
        flowId,
        parameters,
      }),
    });
  }

  async stopAgentFlow(runId: string): Promise<void> {
    await this.agentFlowRequest(`/flows/${runId}/stop`, {
      method: 'POST',
    });
  }

  async getAgentFlowStatus(runId: string): Promise<FlowStatus> {
    return this.agentFlowRequest<FlowStatus>(`/flows/${runId}/status`);
  }

  // Combined Flow Management
  async startProjectFlow(projectId: string, parameters: Record<string, any>): Promise<{
    prefectRun?: FlowRun;
    controlRun?: FlowRun;
    agentRun?: FlowRun;
  }> {
    try {
      const [prefectRun, controlRun, agentRun] = await Promise.all([
        this.startPrefectFlow(`${projectId}-prefect`, parameters),
        this.startControlFlow(`${projectId}-control`, parameters),
        this.startAgentFlow(`${projectId}-agent`, parameters),
      ]);

      return {
        prefectRun,
        controlRun,
        agentRun,
      };
    } catch (error) {
      console.error('Error starting project flows:', error);
      throw error;
    }
  }

  async stopProjectFlow(projectId: string): Promise<void> {
    try {
      await Promise.all([
        this.stopPrefectFlow(`${projectId}-prefect`),
        this.stopControlFlow(`${projectId}-control`),
        this.stopAgentFlow(`${projectId}-agent`),
      ]);
    } catch (error) {
      console.error('Error stopping project flows:', error);
      throw error;
    }
  }

  async getProjectFlowStatus(projectId: string): Promise<{
    prefectStatus?: FlowStatus;
    controlStatus?: FlowStatus;
    agentStatus?: FlowStatus;
  }> {
    try {
      const [prefectStatus, controlStatus, agentStatus] = await Promise.all([
        this.getPrefectFlowStatus(`${projectId}-prefect`),
        this.getControlFlowStatus(`${projectId}-control`),
        this.getAgentFlowStatus(`${projectId}-agent`),
      ]);

      return {
        prefectStatus,
        controlStatus,
        agentStatus,
      };
    } catch (error) {
      console.error('Error getting project flow status:', error);
      throw error;
    }
  }

  async getFlowMetrics(projectId: string): Promise<{
    prefectMetrics?: FlowMetrics;
    controlMetrics?: FlowMetrics;
    agentMetrics?: FlowMetrics;
  }> {
    try {
      const [prefectMetrics, controlMetrics, agentMetrics] = await Promise.all([
        this.prefectRequest<FlowMetrics>(`/flows/${projectId}-prefect/metrics`),
        this.controlFlowRequest<FlowMetrics>(`/flows/${projectId}-control/metrics`),
        this.agentFlowRequest<FlowMetrics>(`/flows/${projectId}-agent/metrics`),
      ]);

      return {
        prefectMetrics,
        controlMetrics,
        agentMetrics,
      };
    } catch (error) {
      console.error('Error getting flow metrics:', error);
      throw error;
    }
  }

  async getFlowEvents(projectId: string): Promise<WorkflowEvent[]> {
    try {
      const [prefectEvents, controlEvents, agentEvents] = await Promise.all([
        this.prefectRequest<any[]>(`/flows/${projectId}-prefect/events`),
        this.controlFlowRequest<any[]>(`/flows/${projectId}-control/events`),
        this.agentFlowRequest<any[]>(`/flows/${projectId}-agent/events`),
      ]);

      // Convert and combine events
      const events: WorkflowEvent[] = [
        ...prefectEvents.map(e => this.convertToWorkflowEvent(e, projectId, 'prefect')),
        ...controlEvents.map(e => this.convertToWorkflowEvent(e, projectId, 'control')),
        ...agentEvents.map(e => this.convertToWorkflowEvent(e, projectId, 'agent')),
      ];

      // Sort by timestamp
      return events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    } catch (error) {
      console.error('Error getting flow events:', error);
      throw error;
    }
  }

  private convertToWorkflowEvent(event: any, projectId: string, source: string): WorkflowEvent {
    return {
      id: event.id,
      projectId,
      taskId: event.taskId,
      type: event.type,
      message: event.message,
      timestamp: new Date(event.timestamp),
      metadata: {
        ...event.metadata,
        source,
      },
    };
  }
}

