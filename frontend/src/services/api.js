/**
 * API service for communicating with the backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add auth token if available
    const token = localStorage.getItem('github_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Authentication
  async authenticateGitHub(token) {
    return this.request('/github/authenticate', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  // Projects
  async getProjects() {
    return this.request('/projects');
  }

  async createProject(projectData) {
    return this.request('/projects', {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
  }

  async updateProject(projectId, projectData) {
    return this.request(`/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(projectData),
    });
  }

  async deleteProject(projectId) {
    return this.request(`/projects/${projectId}`, {
      method: 'DELETE',
    });
  }

  async pinProject(projectId) {
    return this.request(`/projects/${projectId}/pin`, {
      method: 'POST',
    });
  }

  async unpinProject(projectId) {
    return this.request(`/projects/${projectId}/unpin`, {
      method: 'POST',
    });
  }

  // Workflows
  async getWorkflows(projectId) {
    return this.request(`/workflows?project_id=${projectId}`);
  }

  async createWorkflow(workflowData) {
    return this.request('/workflows', {
      method: 'POST',
      body: JSON.stringify(workflowData),
    });
  }

  async getWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}`);
  }

  async startWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}/start`, {
      method: 'POST',
    });
  }

  async stopWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}/stop`, {
      method: 'POST',
    });
  }

  async getWorkflowStatus(workflowId) {
    return this.request(`/workflows/${workflowId}/status`);
  }

  // Agents
  async executeAgent(prompt, projectId) {
    return this.request('/agents/execute', {
      method: 'POST',
      body: JSON.stringify({ prompt, project_id: projectId }),
    });
  }

  async getActiveAgents(projectId) {
    return this.request(`/agents/active?project_id=${projectId}`);
  }

  async getAgentStatus(taskId) {
    return this.request(`/agents/${taskId}/status`);
  }

  async getAllActiveAgents() {
    return this.request('/agents/active');
  }

  // Plans
  async createPlan(projectId, requirements) {
    return this.request('/plans', {
      method: 'POST',
      body: JSON.stringify({
        project_id: projectId,
        requirements: requirements,
      }),
    });
  }

  async getPlan(planId) {
    return this.request(`/plans/${planId}`);
  }

  async updatePlan(planId, planData) {
    return this.request(`/plans/${planId}`, {
      method: 'PUT',
      body: JSON.stringify(planData),
    });
  }

  // Code Analysis
  async analyzeCode(projectId, options = {}) {
    return this.request('/analysis/code', {
      method: 'POST',
      body: JSON.stringify({
        project_id: projectId,
        ...options,
      }),
    });
  }

  async getAnalysisResults(projectId) {
    return this.request(`/analysis/results?project_id=${projectId}`);
  }

  // Deployments
  async createDeployment(deploymentData) {
    return this.request('/deployments', {
      method: 'POST',
      body: JSON.stringify(deploymentData),
    });
  }

  async getDeployments(projectId) {
    return this.request(`/deployments?project_id=${projectId}`);
  }

  async getDeploymentStatus(deploymentId) {
    return this.request(`/deployments/${deploymentId}/status`);
  }

  // GitHub Integration
  async getRepositories() {
    return this.request('/github/repositories');
  }

  async getRepository(owner, repo) {
    return this.request(`/github/repositories/${owner}/${repo}`);
  }

  async getPullRequests(owner, repo, state = 'open') {
    return this.request(`/github/repositories/${owner}/${repo}/pulls?state=${state}`);
  }

  async createPullRequest(owner, repo, prData) {
    return this.request(`/github/repositories/${owner}/${repo}/pulls`, {
      method: 'POST',
      body: JSON.stringify(prData),
    });
  }

  async getPullRequestStatus(owner, repo, prNumber) {
    return this.request(`/github/repositories/${owner}/${repo}/pulls/${prNumber}/status`);
  }

  // Health Check
  async healthCheck() {
    return this.request('/health');
  }

  // WebSocket connection info
  getWebSocketUrl(clientId = 'default') {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.REACT_APP_WS_URL || 'localhost:8000';
    return `${wsProtocol}//${wsHost}/ws/${clientId}`;
  }
}

// Create and export singleton instance
export const apiService = new ApiService();

// Export class for testing
export { ApiService };

// Helper functions
export const formatError = (error) => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export const isApiError = (error) => {
  return error.response && error.response.status;
};

export const getErrorStatus = (error) => {
  return error.response?.status;
};

// API response types for TypeScript-like documentation
/**
 * @typedef {Object} Project
 * @property {string} id - Project ID
 * @property {string} name - Project name
 * @property {string} description - Project description
 * @property {string} github_url - GitHub repository URL
 * @property {string} owner - Repository owner
 * @property {string} repo_name - Repository name
 * @property {string} default_branch - Default branch
 * @property {boolean} is_pinned - Whether project is pinned
 * @property {string} requirements - Project requirements
 * @property {string} plan - Generated plan
 * @property {string} created_at - Creation timestamp
 * @property {string} updated_at - Last update timestamp
 */

/**
 * @typedef {Object} WorkflowExecution
 * @property {string} id - Workflow ID
 * @property {string} project_id - Associated project ID
 * @property {string} name - Workflow name
 * @property {string} status - Current status
 * @property {string} plan - Execution plan
 * @property {number} current_step - Current step number
 * @property {number} total_steps - Total steps
 * @property {number} progress_percentage - Progress percentage
 * @property {string} error_message - Error message if failed
 * @property {Object} metadata - Additional metadata
 * @property {string} started_at - Start timestamp
 * @property {string} completed_at - Completion timestamp
 * @property {string} created_at - Creation timestamp
 */

/**
 * @typedef {Object} AgentTask
 * @property {string} id - Task ID
 * @property {string} project_id - Associated project ID
 * @property {string} workflow_id - Associated workflow ID
 * @property {string} codegen_task_id - Codegen SDK task ID
 * @property {string} original_prompt - Original prompt
 * @property {string} enhanced_prompt - Enhanced prompt
 * @property {Object} prompt_enhancement_techniques - Enhancement metadata
 * @property {string} status - Current status
 * @property {string} result - Task result
 * @property {string} web_url - Codegen web URL
 * @property {string} error_message - Error message if failed
 * @property {number} execution_time_seconds - Execution time
 * @property {Object} metadata - Additional metadata
 * @property {string} created_at - Creation timestamp
 * @property {string} updated_at - Last update timestamp
 */

