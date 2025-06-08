import { Project, DashboardStats, ProjectPinRequest } from '../types/dashboard';

export interface DashboardStats {
  total_projects: number;
  active_workflows: number;
  completed_tasks: number;
  pending_prs: number;
  quality_score: number;
  last_updated: string;
}

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
      contributors: 8
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
      contributors: 5
    }
  }
];

export const dashboardApi = {
  // Get all projects
  getProjects: async (): Promise<Project[]> => {
    try {
      const response = await fetch('/api/projects');
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      // Return mock data for development
      return mockProjects;
    }
  },

  // Get dashboard stats
  getStats: async (): Promise<DashboardStats> => {
    try {
      const response = await fetch('/api/stats');
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      // Return mock data for development
      return {
        total_projects: 10,
        active_workflows: 3,
        completed_tasks: 25,
        pending_prs: 5,
        quality_score: 85,
        last_updated: new Date().toISOString()
      };
    }
  },

  // Pin a project
  pinProject: async (request: ProjectPinRequest): Promise<void> => {
    try {
      await fetch('/api/projects/pin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
    } catch (error) {
      console.error('Failed to pin project:', error);
      // For development, just log the action
      console.log('Pinned project:', request.projectId);
    }
  },

  // Unpin a project
  unpinProject: async (request: ProjectPinRequest): Promise<void> => {
    try {
      await fetch('/api/projects/unpin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
    } catch (error) {
      console.error('Failed to unpin project:', error);
      // For development, just log the action
      console.log('Unpinned project:', request.projectId);
    }
  }
};

