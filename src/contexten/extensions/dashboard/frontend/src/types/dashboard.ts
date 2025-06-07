export interface Project {
  id: string;
  name: string;
  description: string;
  repository: string;
  status: 'active' | 'completed' | 'paused' | 'error';
  progress: number;
  flowEnabled: boolean;
  lastActivity: Date;
  requirements?: string;
  plan?: Plan;
}

export interface Plan {
  id: string;
  projectId: string;
  requirements: string;
  tasks: Task[];
  createdAt: Date;
  updatedAt: Date;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  assignee: string;
  estimatedHours: number;
  actualHours?: number;
  dependencies?: string[];
}

export interface WorkflowExecution {
  id: string;
  projectId: string;
  projectName: string;
  workflowType: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  startTime?: Date;
  endTime?: Date;
  progress: number;
  totalSteps: number;
  completedSteps: number;
  tasks: WorkflowTask[];
  metadata?: Record<string, any>;
}

export interface WorkflowTask {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  logs: string[];
  error?: string;
  dependencies: string[];
}

export interface DashboardMetrics {
  projects: {
    total: number;
    active: number;
    completed: number;
    change: number;
  };
  pull_requests: {
    open: number;
    merged_today: number;
    change: number;
  };
  issues: {
    open: number;
    resolved_today: number;
    change: number;
  };
  workflows: {
    active: number;
    completed_today: number;
    success_rate: number;
  };
  performance: {
    avg_response_time: string;
    code_quality_score: number;
    test_coverage: number;
  };
  last_updated: string;
}

export interface Activity {
  id: string;
  type: 'workflow' | 'pr' | 'issue' | 'deployment';
  title: string;
  description: string;
  timestamp: string;
  status: 'success' | 'error' | 'warning' | 'pending' | 'running';
  user: string;
  metadata?: Record<string, any>;
}

export interface Settings {
  workflow: {
    auto_execute_workflows: boolean;
    parallel_execution: boolean;
    max_concurrent_tasks: number;
    retry_failed_tasks: boolean;
    max_retries: number;
    task_timeout: number;
  };
  notifications: {
    email_notifications: boolean;
    slack_notifications: boolean;
    webhook_notifications: boolean;
    notification_level: string;
  };
  quality_gates: {
    enable_code_review: boolean;
    enable_testing: boolean;
    enable_security: boolean;
    min_code_coverage: number;
    max_complexity: number;
  };
  advanced: {
    enable_ai_assistance: boolean;
    enable_predictive_analysis: boolean;
    enable_auto_optimization: boolean;
    data_retention_days: number;
  };
}

export interface EnvironmentSettings {
  github_token?: string;
  linear_token?: string;
  slack_token?: string;
  codegen_org_id?: string;
  codegen_token?: string;
  postgresql_url?: string;
}

