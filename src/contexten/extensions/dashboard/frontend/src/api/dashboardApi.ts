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
      prefectUrl: settings.prefectUrl || 'https://api.prefect.io',
      prefectToken: settings.prefectToken || '',
      controlFlowUrl: settings.controlFlowUrl || 'https://api.controlflow.dev',
      controlFlowToken: settings.controlFlowToken || '',
      agentFlowUrl: settings.agentFlowUrl || 'https://api.agentflow.dev',
      agentFlowToken: settings.agentFlowToken || '',
    });
  }

  async getProjects(): Promise<Project[]> {
    try {
      // Get GitHub repositories
      const repos = await this.githubService.listRepositories();
      
      // Convert to projects
      const projects = await Promise.all(
        repos.map(async repo => {
          const project = await this.githubService.convertToProject(repo);
          
          // Get Linear project info if available
          try {
            const linearProject = await this.linearService.getProjectByName(project.name);
            if (linearProject) {
              project.linearId = linearProject.id;
              project.progress = linearProject.progress;
            }
          } catch (error) {
            console.warn(`Error getting Linear info for ${project.name}:`, error);
          }

          // Get flow status
          try {
            const status = await this.flowService.getProjectFlowStatus(project.id);
            project.flowStatus = this.determineOverallStatus(status);
          } catch (error) {
            console.warn(`Error getting flow status for ${project.name}:`, error);
          }

          return project;
        })
      );

      return projects;
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

      // Get metrics from different services
      const [flowMetrics, linearMetrics, githubMetrics] = await Promise.all([
        this.getFlowMetrics(projects),
        this.getLinearMetrics(projects),
        this.getGithubMetrics(projects)
      ]);

      // Calculate overall stats
      const stats: DashboardStats = {
        total_projects: projects.length,
        active_workflows: flowMetrics.activeFlows,
        completed_tasks: linearMetrics.completedTasks,
        pending_prs: githubMetrics.pendingPRs,
        quality_score: await this.calculateQualityScore(projects),
        last_updated: new Date().toISOString(),
      };

      return stats;
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      throw error;
    }
  }

  private async getFlowMetrics(projects: Project[]) {
    const metrics = await Promise.all(
      projects.map(project => this.flowService.getFlowMetrics(project.id))
    );

    return {
      activeFlows: metrics.filter(m => m.status === 'running').length,
      totalRuns: metrics.reduce((sum, m) => sum + m.totalRuns, 0),
      successfulRuns: metrics.reduce((sum, m) => sum + m.successfulRuns, 0),
    };
  }

  private async getLinearMetrics(projects: Project[]) {
    const metrics = await Promise.all(
      projects.map(async project => {
        if (!project.linearId) return null;
        return this.linearService.getProjectMetrics(project.linearId);
      })
    );

    return {
      completedTasks: metrics.reduce((sum, m) => sum + (m?.completedTasks || 0), 0),
      totalTasks: metrics.reduce((sum, m) => sum + (m?.totalTasks || 0), 0),
    };
  }

  private async getGithubMetrics(projects: Project[]) {
    const metrics = await Promise.all(
      projects.map(project => {
        const [owner, repo] = project.repository.split('/').slice(-2);
        return this.githubService.getRepositoryMetrics(owner, repo);
      })
    );

    return {
      pendingPRs: metrics.reduce((sum, m) => sum + m.openPRs, 0),
      totalIssues: metrics.reduce((sum, m) => sum + m.totalIssues, 0),
      contributors: metrics.reduce((sum, m) => sum + m.contributors, 0),
    };
  }

  private async calculateQualityScore(projects: Project[]): Promise<number> {
    try {
      const scores = await Promise.all(
        projects.map(async project => {
          try {
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

      // Create or get Linear team
      const teams = await this.linearService.getTeams();
      let teamId = teams.find(t => t.name === project.name)?.id;
      if (!teamId) {
        teamId = await this.linearService.createTeam({
          name: project.name,
          description: project.description,
        });
      }

      // Set up webhooks and integrations
      await this.setupProjectWebhooks(project);

      // Initialize flows
      await this.flowService.startProjectFlow(project.id, {
        repository: project.repository,
        teamId,
        settings: this.settings,
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

      // Remove webhooks
      const project = await this.getProjectById(request.projectId);
      if (project) {
        await this.removeProjectWebhooks(project);
      }
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
        `${this.settings.webhookBaseUrl}/webhooks/github`
      );

      // Set up Linear webhook if we have a team
      if (project.linearId) {
        await this.linearService.createWebhook(
          project.linearId,
          `${this.settings.webhookBaseUrl}/webhooks/linear`
        );
      }

    } catch (error) {
      console.error('Error setting up webhooks:', error);
      throw error;
    }
  }

  private async removeProjectWebhooks(project: Project): Promise<void> {
    try {
      const [owner, repo] = project.repository.split('/').slice(-2);

      // Remove GitHub webhook
      await this.githubService.removeWebhook(
        owner,
        repo,
        `${this.settings.webhookBaseUrl}/webhooks/github`
      );

      // Remove Linear webhook if we have a team
      if (project.linearId) {
        await this.linearService.removeWebhook(
          project.linearId,
          `${this.settings.webhookBaseUrl}/webhooks/linear`
        );
      }

    } catch (error) {
      console.error('Error removing webhooks:', error);
      throw error;
    }
  }
}
