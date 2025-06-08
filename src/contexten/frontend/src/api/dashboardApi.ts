import { Project, DashboardStats, ProjectPinRequest, ApiResponse } from '../types/dashboard';

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 10000; // 10 seconds

// Enhanced fetch with timeout and error handling
async function fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please check your connection');
      }
      throw error;
    }
    
    throw new Error('Unknown error occurred');
  }
}

// Mock data for development (fallback when API is unavailable)
const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Graph-Sitter Core',
    description: 'Code analysis framework with advanced parsing capabilities',
    status: 'active',
    repository: 'https://github.com/Zeeeepa/graph-sitter',
    progress: 85,
    flowEnabled: true,
    flowStatus: 'running',
    lastActivity: new Date(),
    tags: ['core', 'typescript', 'analysis'],
    metrics: {
      commits: 156,
      prs: 23,
      contributors: 8,
      issues: 45
    }
  },
  {
    id: '2', 
    name: 'Contexten Extensions',
    description: 'AI agent framework with graph-sitter integration',
    status: 'active',
    repository: 'https://github.com/Zeeeepa/contexten',
    progress: 70,
    flowEnabled: true,
    flowStatus: 'idle',
    lastActivity: new Date(),
    tags: ['ai', 'agents', 'python'],
    metrics: {
      commits: 89,
      prs: 12,
      contributors: 5,
      issues: 23
    }
  },
  {
    id: '3',
    name: 'Dashboard UI',
    description: 'React dashboard interface with real-time updates',
    status: 'development',
    repository: 'https://github.com/Zeeeepa/dashboard',
    progress: 60,
    flowEnabled: false,
    flowStatus: 'disabled',
    lastActivity: new Date(),
    tags: ['frontend', 'react', 'dashboard'],
    metrics: {
      commits: 67,
      prs: 8,
      contributors: 3,
      issues: 15
    }
  }
];

const mockStats: DashboardStats = {
  totalProjects: 3,
  activeProjects: 2,
  flowEnabled: 2,
  totalCommits: 312,
  totalPRs: 43,
  totalContributors: 16,
  totalIssues: 83
};

export const dashboardApi = {
  /**
   * Get all projects
   * @returns Promise<Project[]>
   */
  getProjects: async (): Promise<Project[]> => {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/api/projects`);
      const data = await response.json();
      return data.projects || [];
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      console.log('🔄 Using mock data as fallback');
      return mockProjects;
    }
  },

  /**
   * Get dashboard statistics
   * @returns Promise<DashboardStats>
   */
  getStats: async (): Promise<DashboardStats> => {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/api/stats`);
      const data = await response.json();
      return data.stats || mockStats;
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      console.log('🔄 Using mock stats as fallback');
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
      const response = await fetchWithTimeout(`${API_BASE_URL}/api/projects/${request.projectId}/pin`, {
        method: 'POST',
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to pin project');
      }
      console.log('✅ Project pinned successfully');
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
      const response = await fetchWithTimeout(`${API_BASE_URL}/api/projects/${request.projectId}/unpin`, {
        method: 'POST',
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to unpin project');
      }
      console.log('✅ Project unpinned successfully');
    } catch (error) {
      console.error('Failed to unpin project:', error);
      throw error;
    }
  },

  /**
   * Get available extensions
   */
  getExtensions: async () => {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/api/extensions`);
      const data = await response.json();
      return data.extensions || [];
    } catch (error) {
      console.error('Failed to fetch extensions:', error);
      console.log('🔄 Using mock extensions as fallback');
      // Return mock extensions as fallback
      return [
        {
          id: 'graph_sitter_analysis',
          name: 'Graph-Sitter Analysis',
          description: 'Code analysis and complexity metrics',
          status: 'active',
          version: '1.0.0',
          capabilities: ['complexity_analysis', 'dependency_analysis', 'security_analysis']
        },
        {
          id: 'graph_sitter_visualize', 
          name: 'Graph-Sitter Visualize',
          description: 'Code visualization and graph generation',
          status: 'active',
          version: '1.0.0',
          capabilities: ['dependency_graphs', 'call_graphs', 'complexity_heatmaps']
        },
        {
          id: 'graph_sitter_resolve',
          name: 'Graph-Sitter Resolve', 
          description: 'Symbol resolution and import analysis',
          status: 'active',
          version: '1.0.0',
          capabilities: ['symbol_resolution', 'import_analysis', 'cross_references']
        }
      ];
    }
  },

  /**
   * Check API health
   */
  checkHealth: async () => {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/health`);
      const data = await response.json();
      return { healthy: true, ...data };
    } catch (error) {
      console.error('Health check failed:', error);
      return { 
        healthy: false, 
        error: error instanceof Error ? error.message : 'Health check failed' 
      };
    }
  }
};

