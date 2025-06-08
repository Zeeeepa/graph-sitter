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
  pinned?: boolean;
  linearId?: string;
  metrics: {
    commits: number;
    prs: number;
    contributors: number;
    issues: number;
  };
  requirements?: string;
  plan?: ProjectPlan;
}

export interface ProjectPlan {
  id: string;
  projectId: string;
  title: string;
  description: string;
  tasks: ProjectTask[];
  status: 'not_started' | 'in_progress' | 'completed' | 'error';
  createdAt: Date;
  updatedAt: Date;
}

export interface ProjectTask {
  id: string;
  title: string;
  description: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'error';
  assignee: string;
  estimatedHours: number;
  actualHours: number;
  dependencies: string[];
  createdAt: Date;
  updatedAt: Date;
  subTasks?: ProjectTask[];
}

export interface WorkflowEvent {
  id: string;
  projectId: string;
  type: 'flow_start' | 'flow_stop' | 'flow_error' | 'flow_success' | 'flow_retry' | 'code_change' | 'issue_update' | 'pr_merge' | 'build' | 'task';
  title: string;
  description: string;
  timestamp: Date;
  metadata?: Record<string, any>;
  tags?: string[];
  links?: {
    title: string;
    url: string;
  }[];
}

export interface Settings {
  githubToken: string;
  linearToken: string;
  codegenOrgId: string;
  codegenToken: string;
  prefectToken: string;
  controlFlowToken: string;
  agentFlowToken: string;
  webhookBaseUrl: string;
  prefectUrl?: string;
  controlFlowUrl?: string;
  agentFlowUrl?: string;
}

export interface ProjectPinRequest {
  projectId: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface DashboardStats {
  total_projects: number;
  active_workflows: number;
  completed_tasks: number;
  pending_prs: number;
  quality_score: number;
  last_updated: string;
}

export interface FlowMetrics {
  status: 'running' | 'stopped' | 'error';
  totalRuns: number;
  successfulRuns: number;
  codeAnalysis: {
    successful: number;
    failed: number;
  };
  tests: {
    successful: number;
    failed: number;
  };
  deployments: {
    successful: number;
    failed: number;
  };
}

export interface ProjectMetrics {
  codeQuality: number;
  workflowSuccessRate: number;
  activeContributors: number;
  openIssues: number;
  activityTimeline: Array<{
    date: string;
    commits: number;
    prs: number;
  }>;
  workflowPerformance: Array<{
    name: string;
    successful: number;
    failed: number;
  }>;
  codeAnalysis: {
    linesOfCode: number;
    testCoverage: number;
    technicalDebt: number;
    duplication: number;
  };
  teamPerformance: {
    avgPRReviewTime: number;
    avgIssueResolutionTime: number;
    sprintVelocity: number;
    teamSatisfaction: number;
  };
}

export interface WebSocketEvent {
  type: string;
  data: any;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: string;
  assignee: string;
  dueDate?: Date;
  priority: number;
  projectId: string;
  parentTaskId?: string;
}

