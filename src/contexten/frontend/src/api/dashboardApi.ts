import { Project, DashboardStats, ProjectPinRequest, ApiResponse } from '../types/dashboard';

// Mock data for development
const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Core Engine',
    description: 'Main processing engine',
    status: 'active',
    repository: 'https://github.com/example/core',
    progress: 75,
    flowEnabled: true,
    flowStatus: 'running',
    lastActivity: new Date(),
    tags: ['core', 'typescript'],
    metrics: {
      commits: 156,
      prs: 23,
      contributors: 8,
      issues: 45
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
    lastActivity: new Date(),
    tags: ['frontend', 'react'],
    metrics: {
      commits: 89,
      prs: 12,
      contributors: 5,
      issues: 28
    }
  }
];

const mockStats: DashboardStats = {
  total_projects: 10,
  active_workflows: 3,
  completed_tasks: 25,
  pending_prs: 5,
  quality_score: 85,
  last_updated: new Date().toISOString()
};

/**
 * Dashboard API client
 * Handles all interactions with the dashboard backend
 */
export const dashboardApi = {
  /**
   * Get all projects
   * @returns Promise<Project[]>
   */
  getProjects: async (): Promise<Project[]> => {
    try {
      const response = await fetch('/api/projects');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: ApiResponse<Project[]> = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to fetch projects');
      }
      return data.data || mockProjects;
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      return mockProjects;
    }
  },

  /**
   * Get dashboard statistics
   * @returns Promise<DashboardStats>
   */
  getStats: async (): Promise<DashboardStats> => {
    try {
      const response = await fetch('/api/stats');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: ApiResponse<DashboardStats> = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to fetch stats');
      }
      return data.data || mockStats;
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      return mockStats;
    }
  },

  /**
   * Pin a project
   * @param request ProjectPinRequest
   * @returns Promise<void>
   */
  pinProject: async (request: ProjectPinRequest): Promise<void> => {
    try {
      const response = await fetch('/api/projects/pin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: ApiResponse<void> = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to pin project');
      }
    } catch (error) {
      console.error('Failed to pin project:', error);
      throw error;
    }
  },

  /**
   * Unpin a project
   * @param request ProjectPinRequest
   * @returns Promise<void>
   */
  unpinProject: async (request: ProjectPinRequest): Promise<void> => {
    try {
      const response = await fetch('/api/projects/unpin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: ApiResponse<void> = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to unpin project');
      }
    } catch (error) {
      console.error('Failed to unpin project:', error);
      throw error;
    }
  }
};

