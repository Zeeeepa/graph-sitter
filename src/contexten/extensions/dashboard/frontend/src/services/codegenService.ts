import { Plan, Task } from '../types/dashboard';

export interface CodegenConfig {
  orgId: string;
  token: string;
}

export interface CodegenPlanRequest {
  projectId: string;
  requirements: string;
  context?: {
    repository?: string;
    branch?: string;
    files?: string[];
  };
}

export interface CodegenTask {
  id: string;
  title: string;
  description: string;
  estimatedHours: number;
  dependencies: string[];
  priority: number;
  skills: string[];
  complexity: 'low' | 'medium' | 'high';
}

export interface CodegenPlan {
  id: string;
  title: string;
  description: string;
  tasks: CodegenTask[];
  estimatedDuration: number;
  confidence: number;
  recommendations: string[];
}

export class CodegenService {
  private config: CodegenConfig;
  private baseUrl = 'https://api.codegen.sh';

  constructor(config: CodegenConfig) {
    this.config = config;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.config.token}`,
        'X-Organization-ID': this.config.orgId,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`Codegen API error: ${response.statusText}`);
    }

    return response.json();
  }

  async generatePlan(request: CodegenPlanRequest): Promise<CodegenPlan> {
    return this.request<CodegenPlan>('/v1/plan/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async convertToPlan(codegenPlan: CodegenPlan, projectId: string): Promise<Plan> {
    const tasks: Task[] = codegenPlan.tasks.map(task => ({
      id: task.id,
      title: task.title,
      description: task.description,
      status: 'pending',
      estimatedHours: task.estimatedHours,
      dependencies: task.dependencies,
      createdAt: new Date(),
      updatedAt: new Date(),
    }));

    return {
      id: codegenPlan.id,
      projectId,
      title: codegenPlan.title,
      description: codegenPlan.description,
      tasks,
      status: 'draft',
      createdAt: new Date(),
      updatedAt: new Date(),
    };
  }

  async analyzeCode(repository: string, branch: string): Promise<{
    issues: string[];
    recommendations: string[];
    complexity: number;
    coverage: number;
  }> {
    return this.request('/v1/analyze/code', {
      method: 'POST',
      body: JSON.stringify({
        repository,
        branch,
      }),
    });
  }

  async validatePR(prUrl: string): Promise<{
    valid: boolean;
    issues: string[];
    suggestions: string[];
    score: number;
  }> {
    return this.request('/v1/validate/pr', {
      method: 'POST',
      body: JSON.stringify({
        prUrl,
      }),
    });
  }

  async suggestReviewers(prUrl: string): Promise<{
    reviewers: Array<{
      username: string;
      confidence: number;
      expertise: string[];
    }>;
  }> {
    return this.request('/v1/suggest/reviewers', {
      method: 'POST',
      body: JSON.stringify({
        prUrl,
      }),
    });
  }

  async estimateComplexity(tasks: Task[]): Promise<{
    complexity: 'low' | 'medium' | 'high';
    estimatedHours: number;
    confidence: number;
  }> {
    return this.request('/v1/estimate/complexity', {
      method: 'POST',
      body: JSON.stringify({
        tasks: tasks.map(t => ({
          title: t.title,
          description: t.description,
          dependencies: t.dependencies,
        })),
      }),
    });
  }

  async suggestImprovements(repository: string): Promise<{
    suggestions: Array<{
      title: string;
      description: string;
      priority: 'low' | 'medium' | 'high';
      effort: 'low' | 'medium' | 'high';
      impact: 'low' | 'medium' | 'high';
    }>;
  }> {
    return this.request('/v1/suggest/improvements', {
      method: 'POST',
      body: JSON.stringify({
        repository,
      }),
    });
  }
}

