// Dashboard Type Definitions

export interface BaseProject {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'completed' | 'error';
}

export interface Project extends BaseProject {
  repository: string;
  progress: number;
  flowEnabled: boolean;
  flowStatus: 'running' | 'stopped' | 'error';
  lastActivity: Date;
  tags: string[];
  metrics?: {
    commits: number;
    prs: number;
    contributors: number;
  };
}

export interface DashboardStats {
  total_projects: number;
  active_workflows: number;
  completed_tasks: number;
  pending_prs: number;
  quality_score: number;
  last_updated: string;
}

export interface ProjectPinRequest {
  projectId: string;
}

export interface ProjectCardProps {
  project: Project;
  onPin?: (projectId: string) => void;
  onUnpin?: (projectId: string) => void;
}

export interface ProjectDialogProps {
  open: boolean;
  project: Project | null;
  onClose: () => void;
  onSave: (project: Project) => void;
}

export interface TopBarProps {
  onProjectPin: (projectName: string) => void;
  onSettingsOpen: () => void;
  projects?: Project[];
}

export interface RealTimeMetricsProps {
  projects: Project[];
}

export interface WorkflowMonitorProps {
  projects: Project[];
}

