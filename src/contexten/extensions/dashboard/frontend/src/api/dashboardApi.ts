import axios from 'axios';
import { Project } from '../types/dashboard';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export interface ProjectPinRequest {
  projectId: string;
}

export interface DashboardStats {
  total_projects: number;
  active_workflows: number;
  completed_tasks: number;
  pending_prs: number;
  quality_score: number;
}

// Add type conversion helper
function toDate(isoString: string): Date {
  return new Date(isoString);
}

export const dashboardApi = {
  // Get all projects
  getProjects: async (): Promise<Project[]> => {
    try {
      const response = await api.get('/projects');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      // Return mock data for development
      return [
        {
          id: '1',
          name: 'Graph Sitter Core',
          description: 'Core graph-sitter functionality',
          status: 'active',
          repository: 'https://github.com/example/graph-sitter',
          progress: 85,
          flowEnabled: true,
          flowStatus: 'running',
          lastActivity: toDate(new Date().toISOString()),
          tags: ['core', 'typescript'],
          metrics: {
            commits: 156,
            prs: 23,
            issues: 8,
            contributors: 5
          }
        },
        {
          id: '2',
          name: 'Dashboard UI',
          description: 'React dashboard interface',
          status: 'active',
          repository: 'https://github.com/example/dashboard',
          progress: 60,
          flowEnabled: false,
          flowStatus: 'stopped',
          lastActivity: toDate(new Date().toISOString()),
          tags: ['frontend', 'react'],
          metrics: {
            commits: 89,
            prs: 12,
            issues: 15,
            contributors: 3
          }
        }
      ];
    }
  },

  // Get dashboard statistics
  getStats: async (): Promise<DashboardStats> => {
    try {
      const response = await api.get('/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      // Return mock data for development
      return {
        total_projects: 12,
        active_workflows: 8,
        completed_tasks: 156,
        pending_prs: 23,
        quality_score: 87
      };
    }
  },

  // Pin a project
  pinProject: async (request: ProjectPinRequest): Promise<void> => {
    try {
      await api.post('/projects/pin', request);
    } catch (error) {
      console.error('Failed to pin project:', error);
      throw error;
    }
  },

  // Unpin a project
  unpinProject: async (request: ProjectPinRequest): Promise<void> => {
    try {
      await api.post('/projects/unpin', request);
    } catch (error) {
      console.error('Failed to unpin project:', error);
      throw error;
    }
  },

  // Get project details
  getProject: async (projectId: string): Promise<Project> => {
    try {
      const response = await api.get(`/projects/${projectId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch project:', error);
      throw error;
    }
  }
};
