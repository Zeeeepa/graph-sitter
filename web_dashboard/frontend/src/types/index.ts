// Core Types for Web-Eval-Agent Dashboard

export interface Project {
  id: string;
  name: string;
  description?: string;
  github_owner: string;
  github_repo: string;
  webhook_url?: string;
  webhook_id?: string;
  status: 'active' | 'inactive' | 'archived';
  settings: ProjectSettings;
  user_id: string;
  created_at: string;
  updated_at: string;
  last_activity?: string;
}

export interface ProjectSettings {
  repository_rules?: string;
  setup_commands?: string;
  planning_statement?: string;
  auto_confirm_plan: boolean;
  auto_merge_validated_pr: boolean;
  branch?: string;
  secrets: Record<string, string>;
}

export interface AgentRun {
  id: string;
  project_id: string;
  target_text: string;
  auto_confirm_plan: boolean;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  session_id?: string;
  response_data?: any;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ValidationResult {
  id: string;
  project_id: string;
  pr_number: number;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  success: boolean;
  message?: string;
  logs: string[];
  deployment_logs: string[];
  test_results?: any;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
}

// File Tree Types
export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  children?: FileNode[];
  errors: CodeError[];
  has_errors: boolean;
  language?: string;
  extension?: string;
  is_expanded?: boolean;
  is_selected?: boolean;
  depth?: number;
}

export interface CodeError {
  file_path: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  rule?: string;
  source: string;
}

// Code Analysis Types
export interface Symbol {
  name: string;
  kind: 'function' | 'class' | 'variable' | 'constant' | 'interface' | 'type' | 'enum' | 'namespace';
  location: Location;
  definition?: Location;
  references: Location[];
  documentation?: string;
  signature?: string;
  parent?: string;
  children?: Symbol[];
}

export interface Location {
  file_path: string;
  line: number;
  column: number;
  end_line?: number;
  end_column?: number;
}

export interface CodeAnalysis {
  project_id: string;
  total_files: number;
  files_with_errors: number;
  total_errors: number;
  errors_by_severity: Record<string, number>;
  errors_by_type: Record<string, number>;
  file_tree: FileNode;
  symbols: Symbol[];
  dependencies: Dependency[];
  metrics: CodeMetrics;
  analysis_duration: number;
  analyzed_at: string;
}

export interface Dependency {
  name: string;
  version: string;
  type: 'production' | 'development' | 'peer' | 'optional';
  source: string;
  vulnerabilities?: Vulnerability[];
}

export interface Vulnerability {
  id: string;
  severity: 'low' | 'moderate' | 'high' | 'critical';
  title: string;
  description: string;
  patched_versions?: string[];
  recommendation?: string;
}

export interface CodeMetrics {
  lines_of_code: number;
  complexity: number;
  maintainability_index: number;
  test_coverage?: number;
  duplication_ratio?: number;
  technical_debt_ratio?: number;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string;
  timestamp: string;
  data: any;
  user_id?: string;
  project_id?: string;
}

export interface ProjectNotification extends WebSocketMessage {
  type: 'project_notification';
  data: {
    project_id: string;
    project_name: string;
    event_type: string;
    timestamp: string;
    [key: string]: any;
  };
}

export interface AgentRunStatusMessage extends WebSocketMessage {
  type: 'agent_run_status';
  data: {
    run_id: string;
    status: string;
    message?: string;
  };
}

export interface ValidationProgressMessage extends WebSocketMessage {
  type: 'validation_progress';
  data: {
    project_id: string;
    pr_number: number;
    message: string;
  };
}

// UI State Types
export interface ViewState {
  activeProject?: string;
  selectedFile?: string;
  activeTab: 'explorer' | 'search' | 'symbols' | 'problems' | 'dependencies';
  sidebarWidth: number;
  editorWidth: number;
  bottomPanelHeight: number;
  showMinimap: boolean;
  showLineNumbers: boolean;
  wordWrap: boolean;
  theme: 'light' | 'dark' | 'auto';
}

export interface SearchState {
  query: string;
  results: SearchResult[];
  isSearching: boolean;
  filters: SearchFilters;
  selectedResult?: SearchResult;
}

export interface SearchResult {
  file_path: string;
  line: number;
  column: number;
  match: string;
  context_before: string;
  context_after: string;
  preview: string;
}

export interface SearchFilters {
  file_types: string[];
  include_patterns: string[];
  exclude_patterns: string[];
  case_sensitive: boolean;
  whole_word: boolean;
  regex: boolean;
}

// Graph Visualization Types
export interface GraphNode {
  id: string;
  label: string;
  type: 'file' | 'function' | 'class' | 'variable' | 'import' | 'export';
  file_path?: string;
  location?: Location;
  size?: number;
  color?: string;
  group?: string;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  from: string;
  to: string;
  type: 'imports' | 'calls' | 'extends' | 'implements' | 'references' | 'contains';
  weight?: number;
  color?: string;
  metadata?: Record<string, any>;
}

export interface CodeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  layout?: 'hierarchical' | 'force' | 'circular' | 'grid';
  filters?: GraphFilters;
}

export interface GraphFilters {
  node_types: string[];
  edge_types: string[];
  min_connections: number;
  max_depth: number;
  focus_node?: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

// Editor Types
export interface EditorState {
  content: string;
  language: string;
  file_path: string;
  is_dirty: boolean;
  cursor_position: { line: number; column: number };
  selection?: { start: Location; end: Location };
  decorations: EditorDecoration[];
}

export interface EditorDecoration {
  id: string;
  range: { start: Location; end: Location };
  type: 'error' | 'warning' | 'info' | 'highlight' | 'selection';
  message?: string;
  className?: string;
}

// Command Palette Types
export interface Command {
  id: string;
  title: string;
  description?: string;
  category: string;
  shortcut?: string;
  icon?: string;
  action: () => void | Promise<void>;
  when?: () => boolean;
}

// Theme Types
export interface Theme {
  name: string;
  type: 'light' | 'dark';
  colors: {
    background: string;
    foreground: string;
    primary: string;
    secondary: string;
    accent: string;
    muted: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  editor: {
    background: string;
    foreground: string;
    selection: string;
    line_highlight: string;
    cursor: string;
    gutter: string;
    comment: string;
    keyword: string;
    string: string;
    number: string;
    function: string;
    variable: string;
    type: string;
  };
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type EventHandler<T = any> = (event: T) => void | Promise<void>;

export type AsyncEventHandler<T = any> = (event: T) => Promise<void>;

// Hook Types
export interface UseWebSocketOptions {
  url: string;
  protocols?: string[];
  onOpen?: EventHandler<Event>;
  onMessage?: EventHandler<MessageEvent>;
  onError?: EventHandler<Event>;
  onClose?: EventHandler<CloseEvent>;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseApiOptions {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
  retries?: number;
  retryDelay?: number;
}

// Store Types
export interface AppState {
  user: User | null;
  projects: Project[];
  activeProject: Project | null;
  viewState: ViewState;
  searchState: SearchState;
  codeAnalysis: CodeAnalysis | null;
  isLoading: boolean;
  error: string | null;
}

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  editor: {
    font_size: number;
    font_family: string;
    tab_size: number;
    word_wrap: boolean;
    minimap: boolean;
    line_numbers: boolean;
  };
  ui: {
    sidebar_width: number;
    panel_height: number;
    show_activity_bar: boolean;
    show_status_bar: boolean;
  };
}
