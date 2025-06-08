import { Project } from '../types/dashboard';
import { GitHubService } from './githubService';
import { LinearService } from './linearService';
import { CodegenService } from './codegenService';
import { FlowService } from './flowService';

export interface ProjectManagerConfig {
  githubToken: string;
  linearToken: string;
  codegenConfig: {
    orgId: string;
    token: string;
  };
  flowConfig: {
    prefectToken: string;
    controlFlowToken: string;
    agentFlowToken: string;
  };
}

export class ProjectManager {
  private githubService: GitHubService;
  private linearService: LinearService;
  private codegenService: CodegenService;
  private flowService: FlowService;
  private pinnedProjects: Set<string>;

  constructor(config: ProjectManagerConfig) {
    this.githubService = new GitHubService(config.githubToken);
    this.linearService = new LinearService(config.linearToken);
    this.codegenService = new CodegenService(config.codegenConfig);
    this.flowService = new FlowService({
      prefectUrl: 'https://api.prefect.io',
      prefectToken: config.flowConfig.prefectToken,
      controlFlowUrl: 'https://api.controlflow.dev',
      controlFlowToken: config.flowConfig.controlFlowToken,
      agentFlowUrl: 'https://api.agentflow.dev',
      agentFlowToken: config.flowConfig.agentFlowToken,
    });
    this.pinnedProjects = new Set();
  }

  async discoverProjects(): Promise<Project[]> {
    try {
      // Get GitHub repositories
      const repos = await this.githubService.listRepositories();
      
      // Convert to projects with additional data
      const projects = await Promise.all(
        repos.map(async repo => {
          try {
            const project = await this.githubService.convertToProject(repo);
            
            // Get Linear team if exists
            const teams = await this.linearService.getTeams();
            const team = teams.find(t => t.name === project.name);
            
            if (team) {
              // Get Linear issues
              const issues = await this.linearService.getTeamIssues(team.id);
              const plan = await this.linearService.createPlanFromIssues(
                team.id,
                project.id,
                `${project.name} Plan`
              );
              project.plan = plan;
            }

            // Get flow status
            const flowStatus = await this.flowService.getProjectFlowStatus(project.id);
            project.flowStatus = this.determineOverallStatus(flowStatus);
            project.flowEnabled = project.flowStatus !== 'stopped';

            // Get code analysis
            const analysis = await this.codegenService.analyzeCode(
              project.repository,
              'main'
            );
            project.metrics = {
              ...project.metrics,
              quality: analysis.score,
              issues: analysis.issues.length,
            };

            return project;
          } catch (error) {
            console.error(`Error processing project ${repo.name}:`, error);
            return null;
          }
        })
      );

      // Filter out failed projects and sort by pinned status
      return projects
        .filter((p): p is Project => p !== null)
        .sort((a, b) => {
          if (this.pinnedProjects.has(a.id) && !this.pinnedProjects.has(b.id)) return -1;
          if (!this.pinnedProjects.has(a.id) && this.pinnedProjects.has(b.id)) return 1;
          return 0;
        });
    } catch (error) {
      console.error('Error discovering projects:', error);
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

  async pinProject(projectId: string): Promise<void> {
    try {
      // Get project details
      const project = await this.getProjectById(projectId);
      if (!project) {
        throw new Error('Project not found');
      }

      // Create Linear team if needed
      const teams = await this.linearService.getTeams();
      let teamId = teams.find(t => t.name === project.name)?.id;
      if (!teamId) {
        throw new Error('Please create a Linear team manually first');
      }

      // Set up webhooks
      await this.setupProjectWebhooks(project);

      // Initialize flows
      await this.flowService.startProjectFlow(project.id, {
        repository: project.repository,
        teamId,
      });

      // Add to pinned projects
      this.pinnedProjects.add(projectId);

    } catch (error) {
      console.error('Failed to pin project:', error);
      throw error;
    }
  }

  async unpinProject(projectId: string): Promise<void> {
    try {
      // Stop all flows
      await this.flowService.stopProjectFlow(projectId);

      // Remove from pinned projects
      this.pinnedProjects.delete(projectId);
    } catch (error) {
      console.error('Failed to unpin project:', error);
      throw error;
    }
  }

  private async getProjectById(projectId: string): Promise<Project | null> {
    const projects = await this.discoverProjects();
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

  async getProjectMetrics(projectId: string): Promise<{
    codeQuality: number;
    performance: number;
    activity: number;
    issues: number;
  }> {
    try {
      const project = await this.getProjectById(projectId);
      if (!project) {
        throw new Error('Project not found');
      }

      const [owner, repo] = project.repository.split('/').slice(-2);

      // Get code analysis
      const analysis = await this.codegenService.analyzeCode(
        project.repository,
        'main'
      );

      // Get flow metrics
      const flowMetrics = await this.flowService.getFlowMetrics(projectId);

      // Get GitHub metrics
      const [commits, prs] = await Promise.all([
        this.githubService.getCommits(owner, repo, 'main'),
        this.githubService.getPullRequests(owner, repo, 'open'),
      ]);

      // Calculate metrics
      return {
        codeQuality: analysis.score,
        performance: this.calculatePerformanceScore(flowMetrics),
        activity: this.calculateActivityScore(commits.length, prs.length),
        issues: analysis.issues.length,
      };
    } catch (error) {
      console.error('Error getting project metrics:', error);
      throw error;
    }
  }

  private calculatePerformanceScore(metrics: any): number {
    const successRate = metrics.prefectMetrics?.successfulRuns || 0 +
      metrics.controlMetrics?.successfulRuns || 0 +
      metrics.agentMetrics?.successfulRuns || 0;
    
    const totalRuns = metrics.prefectMetrics?.totalRuns || 0 +
      metrics.controlMetrics?.totalRuns || 0 +
      metrics.agentMetrics?.totalRuns || 0;

    return totalRuns > 0 ? (successRate / totalRuns) * 100 : 0;
  }

  private calculateActivityScore(commits: number, prs: number): number {
    // Simple activity score based on commits and PRs
    // Could be enhanced with more sophisticated metrics
    return Math.min(100, ((commits * 2 + prs * 5) / 100) * 100);
  }
}

