import { Project } from '../types/dashboard';

export const mockProjects: Project[] = [
  {
    id: 'graph-sitter',
    name: 'Graph Sitter',
    description: 'Code analysis and manipulation engine using tree-sitter with graph-based queries',
    repository: 'https://github.com/Zeeeepa/graph-sitter',
    status: 'active',
    progress: 75,
    flowEnabled: true,
    flowStatus: 'running',
    lastActivity: new Date(),
    tags: ['analysis', 'tree-sitter', 'typescript', 'graph-queries'],
    metrics: {
      commits: 156,
      prs: 23,
      contributors: 8,
      issues: 45
    },
    requirements: 'Build a robust code analysis engine with tree-sitter integration',
    plan: {
      id: 'plan-1',
      projectId: 'graph-sitter',
      title: 'Graph Sitter Implementation',
      description: 'Complete implementation of the graph-based code analysis system',
      tasks: [
        {
          id: 'task-1',
          title: 'Tree-sitter Integration',
          description: 'Set up tree-sitter parsers and basic query functionality',
          status: 'completed',
          assignee: 'AI Agent',
          estimatedHours: 8,
          actualHours: 7,
          dependencies: [],
          createdAt: new Date(),
          updatedAt: new Date()
        },
        {
          id: 'task-2',
          title: 'Graph Query Engine',
          description: 'Implement graph-based code query system',
          status: 'in_progress',
          assignee: 'AI Agent',
          estimatedHours: 12,
          actualHours: 8,
          dependencies: ['task-1'],
          createdAt: new Date(),
          updatedAt: new Date()
        }
      ],
      status: 'in_progress',
      createdAt: new Date(),
      updatedAt: new Date()
    }
  },
  {
    id: 'contexten',
    name: 'Contexten',
    description: 'Agentic orchestrator with chat-agent, langchain, github, and linear integrations',
    repository: 'https://github.com/Zeeeepa/contexten',
    status: 'active',
    progress: 60,
    flowEnabled: true,
    flowStatus: 'running',
    lastActivity: new Date(),
    tags: ['agent', 'langchain', 'integrations', 'typescript'],
    metrics: {
      commits: 89,
      prs: 12,
      contributors: 5,
      issues: 28
    },
    requirements: 'Create a powerful agent orchestration system with multiple integrations'
  },
  {
    id: 'voltagent',
    name: 'Voltagent',
    description: 'Open Source TypeScript AI Agent Framework',
    repository: 'https://github.com/Zeeeepa/voltagent',
    status: 'active',
    progress: 85,
    flowEnabled: true,
    flowStatus: 'running',
    lastActivity: new Date(Date.now() - 86400000), // 1 day ago
    tags: ['agent', 'framework', 'typescript', 'open-source'],
    metrics: {
      commits: 234,
      prs: 45,
      contributors: 12,
      issues: 67
    },
    requirements: 'Build an extensible TypeScript framework for AI agents'
  },
  {
    id: 'deep-research',
    name: 'Deep Research',
    description: 'Codebase exploration with AI research agents',
    repository: 'https://github.com/Zeeeepa/deep-research',
    status: 'active',
    progress: 40,
    flowEnabled: true,
    flowStatus: 'running',
    lastActivity: new Date(),
    tags: ['research', 'ai', 'codebase-analysis'],
    metrics: {
      commits: 45,
      prs: 8,
      contributors: 3,
      issues: 15
    },
    requirements: 'Develop AI-powered codebase research and exploration capabilities'
  }
];

