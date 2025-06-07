export type FlowStatus = 'stopped' | 'running' | 'paused' | 'error';

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  assignee?: string;
  estimatedHours?: number;
  dependencies?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface Plan {
  id: string;
  tasks: Task[];
  estimatedDuration?: string;
  totalTasks?: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectStats {
  openPRs: number;
  openIssues: number;
  completedTasks: number;
  totalTasks: number;
}

export interface ProjectEvent {
  id: string;
  message: string;
  timestamp: string;
  type: 'pr' | 'issue' | 'task' | 'flow' | 'error';
}

export interface Project {
  id: string;
  name: string;
  description: string;
  repository: string;
  flowStatus: FlowStatus;
  requirements?: string;
  plan?: Plan;
  stats?: ProjectStats;
  recentEvents?: ProjectEvent[];
  createdAt: string;
  updatedAt: string;
}

export interface DashboardState {
  pinnedProjects: Project[];
  availableProjects: Project[];
  selectedProject: Project | null;
  isLoading: boolean;
  error: string | null;
}

export interface WebSocketMessage {
  type: 'project_update' | 'flow_status' | 'task_update' | 'error';
  projectId?: string;
  data: any;
}

