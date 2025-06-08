// Dashboard Type Definitions

export interface Project {
  id: string;
  name: string;
  description: string;
  repository: string;
  status: 'active' | 'paused' | 'completed' | 'error';
  progress: number;
  flowEnabled: boolean;
  flowStatus: 'running' | 'stopped' | 'error';
  lastActivity: Date;
  tags: string[];
  metrics: ProjectMetrics;
  requirements?: string;
  plan?: Plan;
}

export interface ProjectMetrics {
  commits: number;
  contributors: number;
  openPRs: number;
  closedPRs: number;
  issues: number;
  tests: number;
  coverage: number;
}

export interface Plan {
  id: string;
  projectId: string;
  title: string;
  description: string;
  tasks: Task[];
  status: 'draft' | 'in_progress' | 'completed';
  createdAt: Date;
  updatedAt: Date;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  assignee?: string;
  estimatedHours: number;
  actualHours?: number;
  dependencies: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface WorkflowEvent {
  id: string;
  projectId: string;
  taskId?: string;
  type: 'task_created' | 'task_updated' | 'task_completed' | 'flow_started' | 'flow_stopped';
  message: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface Settings {
  githubToken: string;
  linearToken: string;
  codegenOrgId: string;
  codegenToken: string;
  postgresqlUrl?: string;
  slackToken?: string;
  autoStartFlows: boolean;
  enableNotifications: boolean;
  enableAnalytics: boolean;
}

export interface Metrics {
  totalProjects: number;
  activeProjects: number;
  completedProjects: number;
  runningFlows: number;
  averageProgress: number;
  totalTasks: number;
  completedTasks: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// API Endpoints
export interface ApiEndpoints {
  projects: {
    list: () => Promise<ApiResponse<Project[]>>;
    get: (id: string) => Promise<ApiResponse<Project>>;
    create: (project: Partial<Project>) => Promise<ApiResponse<Project>>;
    update: (id: string, project: Partial<Project>) => Promise<ApiResponse<Project>>;
    delete: (id: string) => Promise<ApiResponse<void>>;
  };
  plans: {
    generate: (projectId: string, requirements: string) => Promise<ApiResponse<Plan>>;
    get: (id: string) => Promise<ApiResponse<Plan>>;
    update: (id: string, plan: Partial<Plan>) => Promise<ApiResponse<Plan>>;
  };
  workflows: {
    start: (projectId: string) => Promise<ApiResponse<void>>;
    stop: (projectId: string) => Promise<ApiResponse<void>>;
    status: (projectId: string) => Promise<ApiResponse<{ status: string }>>;
  };
  metrics: {
    get: () => Promise<ApiResponse<Metrics>>;
  };
}

// WebSocket Events
export interface WebSocketEvent {
  type: 'project_updated' | 'task_updated' | 'workflow_event' | 'metrics_updated';
  payload: any;
  timestamp: Date;
}

// Component Props
export interface DashboardProps {
  initialProjects?: Project[];
  settings?: Partial<Settings>;
}

export interface ProjectCardProps {
  project: Project;
  onClick: () => void;
  onFlowToggle?: (projectId: string, enabled: boolean) => void;
}

export interface ProjectDialogProps {
  open: boolean;
  project: Project | null;
  onClose: () => void;
  onSave: (project: Project) => void;
}

export interface SettingsDialogProps {
  open: boolean;
  settings: Settings;
  onClose: () => void;
  onSave: (settings: Settings) => void;
}

export interface TopBarProps {
  onProjectPin: (projectName: string) => void;
  onSettingsOpen: () => void;
  projects?: Project[];
}

export interface RealTimeMetricsProps {
  projects: Project[];
  metrics?: Metrics;
}

export interface WorkflowMonitorProps {
  projects: Project[];
  events?: WorkflowEvent[];
}
