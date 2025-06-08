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
  active_projects: number;
  completed_projects: number;
  running_flows: number;
  average_progress: number;
  total_tasks: number;
  completed_tasks: number;
  quality_score: number;
}

// Helper function to convert ISO string to Date
function toDate(isoString: string): Date {
  return new Date(isoString);
}

const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Graph Sitter',
    description: 'Tree-sitter based code analysis',
    repository: 'https://github.com/example/graph-sitter',
    status: 'active',
    progress: 85,
    flowEnabled: true,
    flowStatus: 'running',
    lastActivity: new Date(), // Direct Date object instead of conversion
    tags: ['core', 'typescript'],
    metrics: {
      commits: 156,
      contributors: 8,
      openPRs: 12,
      closedPRs: 45,
      issues: 23,
      tests: 342,
      coverage: 89
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
    lastActivity: new Date(), // Direct Date object instead of conversion
    tags: ['frontend', 'react'],
    metrics: {
      commits: 89,
      contributors: 5,
      openPRs: 8,
      closedPRs: 32,
      issues: 15,
      tests: 156,
      coverage: 76
    }
  }
];

export const dashboardApi = {
  // Get all projects
  getProjects: async (): Promise<Project[]> => {
    // Mock data for now
    return [
      {
        id: '1',
        name: 'Graph Sitter',
        description: 'Tree-sitter based code analysis',
        repository: 'https://github.com/example/graph-sitter',
        status: 'active',
        progress: 85,
        flowEnabled: true,
        flowStatus: 'running',
        lastActivity: new Date(), // Direct Date object instead of conversion
        tags: ['core', 'typescript'],
        metrics: {
          commits: 156,
          contributors: 8,
          openPRs: 12,
          closedPRs: 45,
          issues: 23,
          tests: 342,
          coverage: 89
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
        lastActivity: new Date(), // Direct Date object instead of conversion
        tags: ['frontend', 'react'],
        metrics: {
          commits: 89,
          contributors: 5,
          openPRs: 8,
          closedPRs: 32,
          issues: 15,
          tests: 156,
          coverage: 76
        }
      }
    ];
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
        active_projects: 8,
        completed_projects: 156,
        running_flows: 5,
        average_progress: 75,
        total_tasks: 100,
        completed_tasks: 156,
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
