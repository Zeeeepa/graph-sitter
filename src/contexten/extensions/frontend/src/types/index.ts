// Project types
export interface Project {
  id: string;
  name: string;
  full_name: string;
  description?: string;
  url: string;
  default_branch: string;
  language?: string;
  status: 'active' | 'inactive' | 'archived' | 'error';
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export interface ProjectPin {
  id: string;
  project_id: string;
  user_id: string;
  position: number;
  flow_status: 'on' | 'off' | 'paused' | 'error';
  pinned_at: string;
  settings: Record<string, any>;
}

// Workflow types
export interface WorkflowPlan {
  id: string;
  project_id: string;
  title: string;
  description: string;
  requirements: string;
  generated_plan: Record<string, any>;
  tasks: WorkflowTask[];
  estimated_duration?: number;
  complexity_score: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  updated_at: string;
  created_by?: string;
  metadata: Record<string, any>;
}

export interface WorkflowTask {
  id: string;
  plan_id: string;
  title: string;
  description: string;
  task_type: string;
  dependencies: string[];
  assignee?: string;
  status: 'todo' | 'in_progress' | 'review' | 'completed' | 'failed' | 'blocked';
  priority: number;
  estimated_hours?: number;
  actual_hours?: number;
  github_pr_url?: string;
  linear_issue_id?: string;
  codegen_task_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  metadata: Record<string, any>;
}

export interface WorkflowExecution {
  id: string;
  plan_id: string;
  execution_layer: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  current_task_id?: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  execution_logs: LogEntry[];
  metrics: Record<string, any>;
}

// Quality Gate types
export interface QualityGate {
  id: string;
  task_id: string;
  gate_type: string;
  status: 'pending' | 'passed' | 'failed' | 'skipped';
  score?: number;
  threshold: number;
  issues_found: QualityIssue[];
  auto_fix_applied: boolean;
  manual_review_required: boolean;
  executed_at?: string;
  metadata: Record<string, any>;
}

export interface QualityIssue {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  file?: string;
  line?: number;
  suggestion?: string;
}

// PR types
export interface PRInfo {
  id: string;
  project_id: string;
  task_id?: string;
  pr_number: number;
  title: string;
  description: string;
  status: 'open' | 'merged' | 'closed' | 'draft';
  url: string;
  branch_name: string;
  base_branch: string;
  author: string;
  created_at: string;
  updated_at: string;
  merged_at?: string;
  quality_gates: QualityGate[];
  metadata: Record<string, any>;
}

// Event types
export interface EventLog {
  id: string;
  project_id: string;
  event_type: string;
  event_source: string;
  event_data: Record<string, any>;
  user_id?: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface LogEntry {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  message: string;
  layer?: string;
  task_id?: string;
  execution_id?: string;
  metadata?: Record<string, any>;
}

// Dashboard types
export interface DashboardStats {
  total_projects: number;
  active_workflows: number;
  completed_tasks: number;
  pending_prs: number;
  quality_score: number;
  last_updated: string;
}

// Settings types
export interface ProjectSettings {
  project_id: string;
  github_enabled: boolean;
  linear_enabled: boolean;
  slack_enabled: boolean;
  codegen_enabled: boolean;
  auto_pr_creation: boolean;
  auto_issue_creation: boolean;
  quality_gates_enabled: boolean;
  notification_preferences: Record<string, boolean>;
  custom_settings: Record<string, any>;
}

export interface EnvironmentVariables {
  github_token?: string;
  linear_api_key?: string;
  slack_token?: string;
  codegen_org_id?: string;
  codegen_token?: string;
  postgresql_url?: string;
}

// API Response types
export interface DashboardResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  errors?: string[];
}

// GitHub types
export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  url: string;
  clone_url: string;
  default_branch: string;
  language?: string;
  private: boolean;
  fork: boolean;
  archived: boolean;
  disabled: boolean;
  created_at: string;
  updated_at: string;
  pushed_at?: string;
  size: number;
  stargazers_count: number;
  watchers_count: number;
  forks_count: number;
  open_issues_count: number;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  timestamp: string;
  data?: any;
  [key: string]: any;
}

export interface ConnectionInfo {
  connection_id: string;
  user_id: string;
  connected_at: string;
  subscriptions: string[];
}

// Form types
export interface ProjectCreateRequest {
  name: string;
  full_name: string;
  description?: string;
  url: string;
  default_branch: string;
  language?: string;
}

export interface ProjectPinRequest {
  project_id: string;
  position: number;
}

export interface WorkflowPlanRequest {
  project_id: string;
  title: string;
  description: string;
  requirements: string;
}

export interface SettingsUpdateRequest {
  github_enabled?: boolean;
  linear_enabled?: boolean;
  slack_enabled?: boolean;
  codegen_enabled?: boolean;
  auto_pr_creation?: boolean;
  auto_issue_creation?: boolean;
  quality_gates_enabled?: boolean;
  notification_preferences?: Record<string, boolean>;
  custom_settings?: Record<string, any>;
}

