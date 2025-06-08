import { create } from 'zustand';
import { Project, WorkflowPlan, DashboardStats } from '../types';

interface DashboardState {
  // UI State
  settingsOpen: boolean;
  selectedProject: Project | null;
  
  // Data
  projects: Project[];
  workflowPlans: WorkflowPlan[];
  dashboardStats: DashboardStats | null;
  
  // User
  user: {
    id: string;
    name: string;
  };
  
  // WebSocket
  connected: boolean;
  
  // Actions
  setSettingsOpen: (open: boolean) => void;
  setSelectedProject: (project: Project | null) => void;
  setProjects: (projects: Project[]) => void;
  setWorkflowPlans: (plans: WorkflowPlan[]) => void;
  setDashboardStats: (stats: DashboardStats) => void;
  setConnected: (connected: boolean) => void;
  
  // Project actions
  addProject: (project: Project) => void;
  updateProject: (projectId: string, updates: Partial<Project>) => void;
  removeProject: (projectId: string) => void;
  
  // Workflow actions
  addWorkflowPlan: (plan: WorkflowPlan) => void;
  updateWorkflowPlan: (planId: string, updates: Partial<WorkflowPlan>) => void;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  // Initial state
  settingsOpen: false,
  selectedProject: null,
  projects: [],
  workflowPlans: [],
  dashboardStats: null,
  user: {
    id: 'default_user',
    name: 'Dashboard User',
  },
  connected: false,
  
  // UI Actions
  setSettingsOpen: (open) => set({ settingsOpen: open }),
  setSelectedProject: (project) => set({ selectedProject: project }),
  
  // Data Actions
  setProjects: (projects) => set({ projects }),
  setWorkflowPlans: (plans) => set({ workflowPlans: plans }),
  setDashboardStats: (stats) => set({ dashboardStats: stats }),
  setConnected: (connected) => set({ connected }),
  
  // Project Actions
  addProject: (project) => set((state) => ({
    projects: [...state.projects, project]
  })),
  
  updateProject: (projectId, updates) => set((state) => ({
    projects: state.projects.map(p => 
      p.id === projectId ? { ...p, ...updates } : p
    )
  })),
  
  removeProject: (projectId) => set((state) => ({
    projects: state.projects.filter(p => p.id !== projectId)
  })),
  
  // Workflow Actions
  addWorkflowPlan: (plan) => set((state) => ({
    workflowPlans: [...state.workflowPlans, plan]
  })),
  
  updateWorkflowPlan: (planId, updates) => set((state) => ({
    workflowPlans: state.workflowPlans.map(p =>
      p.id === planId ? { ...p, ...updates } : p
    )
  })),
}));

