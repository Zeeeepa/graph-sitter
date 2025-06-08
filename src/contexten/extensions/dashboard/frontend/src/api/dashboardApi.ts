import { Project, DashboardStats, ProjectPinRequest, ApiResponse, Settings } from '../types/dashboard';
import { GitHubService } from '../services/githubService';
import { LinearService } from '../services/linearService';
import { CodegenService } from '../services/codegenService';
import { FlowService } from '../services/flowService';

export class DashboardAPI {
  private githubService: GitHubService;
  private linearService: LinearService;
  private codegenService: CodegenService;
  private flowService: FlowService;
  private settings: Settings;

  constructor(settings: Settings) {
    this.settings = settings;
    this.githubService = new GitHubService(settings.githubToken);
    this.linearService = new LinearService(settings.linearToken);
    this.codegenService = new CodegenService({
      orgId: settings.codegenOrgId,
      token: settings.codegenToken,
    });
    this.flowService = new FlowService({
      prefectUrl: 'https://api.prefect.io',
      prefectToken: settings.prefectToken || '',
      controlFlowUrl: 'https://api.controlflow.dev',
      controlFlowToken: settings.controlFlowToken || '',
      agentFlowUrl: 'https://api.agentflow.dev',
      agentFlowToken: settings.agentFlowToken || '',
    });
  }

  async getProjects(): Promise<Project[]> {
    try {
      // Get GitHub repositories
      const repos = await this.githubService.listRepositories();
      
      // Convert to projects
      const projects = await Promise.all(
        repos.map(repo => this.githubService.convertToProject(repo))
      );

      // Get flow status for each project
      const projectsWithStatus = await Promise.all(
        projects.map(async project => {
          try {
            const status = await this.flowService.getProjectFlowStatus(project.id);
            return {
              ...project,
              flowStatus: this.determineOverallStatus(status),
            };
          } catch (error) {
            console.error(`Error getting flow status for project ${project.id}:`, error);
            return project;
          }
        })
      );

      return projectsWithStatus;
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      throw error;
    }
  }

  private determineOverallStatus(status: {
    prefectStatus?: any;
    controlStatus?: any;
    agentStatus?: any;
  }): 'running' | 'stopped' | 'error' {
    const statuses = [
      status.prefectStatus?.status,
      status.controlStatus?.status,
      status.agentStatus?.status,
    ].filter(Boolean);

    if (statuses.includes('failed')) return 'error';
    if (statuses.includes('running')) return 'running';
    return 'stopped';
  }

  async getStats(): Promise<DashboardStats> {
    try {
      // Get projects
      const projects = await this.getProjects();

      // Get flow metrics for all projects
      const flowMetrics = await Promise.all(
        projects.map(project => this.flowService.getFlowMetrics(project.id))
      );

      // Calculate overall stats
      const stats: DashboardStats = {
        total_projects: projects.length,
        active_workflows: projects.filter(p => p.flowStatus === 'running').length,
        completed_tasks: flowMetrics.reduce((sum, metrics) => {
          const completed = (metrics.prefectMetrics?.successfulRuns || 0) +
            (metrics.controlMetrics?.successfulRuns || 0) +
            (metrics.agentMetrics?.successfulRuns || 0);
          return sum + completed;
        }, 0),
        pending_prs: await this.countPendingPRs(projects),
        quality_score: await this.calculateQualityScore(projects),
        last_updated: new Date().toISOString(),
      };

      return stats;
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      throw error;
    }
  }

  private async countPendingPRs(projects: Project[]): Promise<number> {
    try {
      const prCounts = await Promise.all(
        projects.map(async project => {
          const [owner, repo] = project.repository.split('/').slice(-2);
          const prs = await this.githubService.getPullRequests(owner, repo, 'open');
          return prs.length;
        })
      );

      return prCounts.reduce((sum, count) => sum + count, 0);
    } catch (error) {
      console.error('Error counting pending PRs:', error);
      return 0;
    }
  }

  private async calculateQualityScore(projects: Project[]): Promise<number> {
    try {
      const scores = await Promise.all(
        projects.map(async project => {
          try {
            const [owner, repo] = project.repository.split('/').slice(-2);
            const analysis = await this.codegenService.analyzeCode(
              project.repository,
              'main'
            );
            return analysis.score;
          } catch (error) {
            console.error(`Error analyzing project ${project.id}:`, error);
            return 0;
          }
        })
      );

      const averageScore = scores.reduce((sum, score) => sum + score, 0) / scores.length;
      return Math.round(averageScore);
    } catch (error) {
      console.error('Error calculating quality score:', error);
      return 0;
    }
  }

  async pinProject(request: ProjectPinRequest): Promise<void> {
    try {
      // Get project details
      const project = await this.getProjectById(request.projectId);
      if (!project) {
        throw new Error('Project not found');
      }

      // Create Linear team if needed
      const teams = await this.linearService.getTeams();
      let teamId = teams.find(t => t.name === project.name)?.id;
      if (!teamId) {
        // Create team in Linear
        // Note: Linear API doesn't support team creation via API
        throw new Error('Please create a Linear team manually first');
      }

      // Set up webhooks
      await this.setupProjectWebhooks(project);

      // Initialize flows
      await this.flowService.startProjectFlow(project.id, {
        repository: project.repository,
        teamId,
      });

    } catch (error) {
      console.error('Failed to pin project:', error);
      throw error;
    }
  }

  async unpinProject(request: ProjectPinRequest): Promise<void> {
    try {
      // Stop all flows
      await this.flowService.stopProjectFlow(request.projectId);
    } catch (error) {
      console.error('Failed to unpin project:', error);
      throw error;
    }
  }

  private async getProjectById(projectId: string): Promise<Project | null> {
    const projects = await this.getProjects();
    return projects.find(p => p.id === projectId) || null;
  }

  private async setupProjectWebhooks(project: Project): Promise<void> {
    try {
      const [owner, repo] = project.repository.split('/').slice(-2);

      // Set up GitHub webhook
      await this.githubService.createWebhook(
        owner,
        repo,
        'https://api.dashboard.example.com/webhooks/github'
      );

      // Note: Linear webhooks would need to be set up via their UI
      // as their API doesn't support webhook creation

    } catch (error) {
      console.error('Error setting up webhooks:', error);
      throw error;
    }
  }
}

