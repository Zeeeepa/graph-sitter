import axios from 'axios';
import {
  Project,
  WorkflowPlan,
  DashboardStats,
  GitHubRepository,
  DashboardResponse,
  ProjectCreateRequest,
  ProjectPinRequest,
  WorkflowPlanRequest,
  SettingsUpdateRequest,
  EnvironmentVariables,
} from '../types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/dashboard',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    // Add authentication token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

export const dashboardApi = {
  // Health check
  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await api.get('/health');
    return response.data;
  },

  // Project management
  getProjects: async (): Promise<Project[]> => {
    const response = await api.get<DashboardResponse<{ projects: Project[] }>>('/projects');
    return response.data.data?.projects || [];
  },

  createProject: async (projectData: ProjectCreateRequest): Promise<string> => {
    const response = await api.post<DashboardResponse<{ project_id: string }>>('/projects', projectData);
    return response.data.data?.project_id || '';
  },

  pinProject: async (pinData: ProjectPinRequest): Promise<void> => {
    await api.post('/projects/pin', pinData);
  },

  unpinProject: async (projectId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}/pin`);
  },

  getProjectStatus: async (projectId: string): Promise<any> => {
    const response = await api.get<DashboardResponse>(`/projects/${projectId}/status`);
    return response.data.data;
  },

  // GitHub integration
  getGitHubRepositories: async (): Promise<GitHubRepository[]> => {
    const response = await api.get<DashboardResponse<{ repositories: GitHubRepository[] }>>('/projects/github');
    return response.data.data?.repositories || [];
  },

  // Workflow management
  getWorkflowPlans: async (projectId: string): Promise<WorkflowPlan[]> => {
    const response = await api.get<DashboardResponse<{ plans: WorkflowPlan[] }>>(`/projects/${projectId}/plans`);
    return response.data.data?.plans || [];
  },

  createWorkflowPlan: async (planData: WorkflowPlanRequest): Promise<{ plan_id: string; generated_plan: any }> => {
    const response = await api.post<DashboardResponse<{ plan_id: string; generated_plan: any }>>(
      `/projects/${planData.project_id}/plans`,
      planData
    );
    return response.data.data || { plan_id: '', generated_plan: {} };
  },

  startWorkflow: async (projectId: string, planId: string): Promise<void> => {
    await api.post(`/projects/${projectId}/plans/${planId}/start`);
  },

  // Settings management
  updateProjectSettings: async (projectId: string, settings: SettingsUpdateRequest): Promise<void> => {
    await api.put(`/projects/${projectId}/settings`, settings);
  },

  updateEnvironmentVariables: async (variables: EnvironmentVariables): Promise<void> => {
    await api.put('/settings/environment', variables);
  },

  // Dashboard stats
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardResponse<DashboardStats>>('/stats');
    return response.data.data || {
      total_projects: 0,
      active_workflows: 0,
      completed_tasks: 0,
      pending_prs: 0,
      quality_score: 0,
      last_updated: new Date().toISOString(),
    };
  },
};

export default api;

