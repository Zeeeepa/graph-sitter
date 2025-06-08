import { Project } from '../types/dashboard';

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  description: string;
  html_url: string;
  default_branch: string;
  created_at: string;
  updated_at: string;
  pushed_at: string;
  language: string;
  topics: string[];
  stargazers_count: number;
  watchers_count: number;
  forks_count: number;
  open_issues_count: number;
}

export interface GitHubBranch {
  name: string;
  commit: {
    sha: string;
    url: string;
  };
}

export interface GitHubCommit {
  sha: string;
  commit: {
    author: {
      name: string;
      email: string;
      date: string;
    };
    message: string;
  };
}

export interface GitHubPR {
  id: number;
  number: number;
  title: string;
  state: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  merged_at: string | null;
  user: {
    login: string;
  };
}

export class GitHubService {
  private token: string;
  private baseUrl = 'https://api.github.com';

  constructor(token: string) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.statusText}`);
    }

    return response.json();
  }

  async listRepositories(): Promise<GitHubRepo[]> {
    return this.request<GitHubRepo[]>('/user/repos?sort=updated&per_page=100');
  }

  async getRepository(owner: string, repo: string): Promise<GitHubRepo> {
    return this.request<GitHubRepo>(`/repos/${owner}/${repo}`);
  }

  async getBranches(owner: string, repo: string): Promise<GitHubBranch[]> {
    return this.request<GitHubBranch[]>(`/repos/${owner}/${repo}/branches`);
  }

  async getCommits(owner: string, repo: string, branch: string): Promise<GitHubCommit[]> {
    return this.request<GitHubCommit[]>(`/repos/${owner}/${repo}/commits?sha=${branch}&per_page=100`);
  }

  async getPullRequests(owner: string, repo: string, state: 'open' | 'closed' | 'all' = 'all'): Promise<GitHubPR[]> {
    return this.request<GitHubPR[]>(`/repos/${owner}/${repo}/pulls?state=${state}&per_page=100`);
  }

  async convertToProject(repo: GitHubRepo): Promise<Project> {
    // Get additional data
    const [commits, prs] = await Promise.all([
      this.getCommits(repo.owner.login, repo.name, repo.default_branch),
      this.getPullRequests(repo.owner.login, repo.name),
    ]);

    // Calculate metrics
    const metrics = {
      commits: commits.length,
      prs: prs.length,
      contributors: new Set(commits.map(c => c.commit.author.email)).size,
      issues: repo.open_issues_count,
    };

    // Convert to Project type
    return {
      id: repo.id.toString(),
      name: repo.name,
      description: repo.description || '',
      repository: repo.html_url,
      status: 'active',
      progress: 0, // Will be calculated based on milestones/issues
      flowEnabled: false,
      flowStatus: 'stopped',
      lastActivity: new Date(repo.pushed_at),
      tags: repo.topics || [],
      metrics,
    };
  }

  async searchRepositories(query: string): Promise<GitHubRepo[]> {
    const response = await this.request<{ items: GitHubRepo[] }>(
      `/search/repositories?q=${encodeURIComponent(query)}&sort=updated&order=desc&per_page=100`
    );
    return response.items;
  }

  async getContributors(owner: string, repo: string): Promise<{ login: string; contributions: number }[]> {
    return this.request<{ login: string; contributions: number }[]>(
      `/repos/${owner}/${repo}/contributors`
    );
  }

  async getLanguages(owner: string, repo: string): Promise<Record<string, number>> {
    return this.request<Record<string, number>>(
      `/repos/${owner}/${repo}/languages`
    );
  }

  async getIssues(owner: string, repo: string, state: 'open' | 'closed' | 'all' = 'all'): Promise<any[]> {
    return this.request<any[]>(
      `/repos/${owner}/${repo}/issues?state=${state}&per_page=100`
    );
  }

  async createWebhook(owner: string, repo: string, webhookUrl: string): Promise<void> {
    await this.request(
      `/repos/${owner}/${repo}/hooks`,
      {
        method: 'POST',
        body: JSON.stringify({
          name: 'web',
          active: true,
          events: ['push', 'pull_request', 'issues'],
          config: {
            url: webhookUrl,
            content_type: 'json',
            insecure_ssl: '0',
          },
        }),
      }
    );
  }
}

