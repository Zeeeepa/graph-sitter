import { Project } from '../types/dashboard';

export const mockProjects: Project[] = [
  {
    id: '1',
    name: 'AI Dashboard System',
    description: 'Complete dashboard for AI-powered development workflows',
    repository: 'https://github.com/Zeeeepa/graph-sitter',
    status: 'active',
    progress: 75,
    flowEnabled: true,
    flowStatus: 'running',
    lastActivity: new Date(),
    tags: ['dashboard', 'react', 'typescript'],
    metrics: {
      commits: 156,
      prs: 23,
      contributors: 8,
      issues: 45
    },
    requirements: 'Build a comprehensive dashboard system with React and Material-UI',
    plan: {
      id: 'plan-1',
      projectId: '1',
      title: 'Dashboard Implementation Plan',
      description: 'Complete implementation of the dashboard system',
      tasks: [
        {
          id: 'task-1',
          title: 'Setup React Frontend',
          description: 'Initialize React app with Material-UI',
          status: 'completed',
          assignee: 'AI Agent',
          estimatedHours: 4,
          actualHours: 3,
          dependencies: [],
          createdAt: new Date(),
          updatedAt: new Date()
        },
        {
          id: 'task-2',
          title: 'Implement Dashboard Components',
          description: 'Create all necessary UI components',
          status: 'in_progress',
          assignee: 'AI Agent',
          estimatedHours: 8,
          actualHours: 6,
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
    id: '2',
    name: 'Code Analysis Engine',
    description: 'Advanced code analysis and manipulation system',
    repository: 'https://github.com/Zeeeepa/graph-sitter',
    status: 'paused',
    progress: 45,
    flowEnabled: false,
    flowStatus: 'stopped',
    lastActivity: new Date(Date.now() - 86400000), // 1 day ago
    tags: ['analysis', 'tree-sitter', 'typescript'],
    metrics: {
      commits: 89,
      prs: 12,
      contributors: 5,
      issues: 28
    },
    requirements: 'Implement graph-sitter based code analysis'
  },
  {
    id: '3',
    name: 'Workflow Orchestrator',
    description: 'Orchestration system for development workflows',
    repository: 'https://github.com/Zeeeepa/contexten',
    status: 'completed',
    progress: 100,
    flowEnabled: true,
    flowStatus: 'stopped',
    lastActivity: new Date(Date.now() - 172800000), // 2 days ago
    tags: ['workflow', 'automation', 'typescript'],
    metrics: {
      commits: 234,
      prs: 45,
      contributors: 12,
      issues: 67
    },
    requirements: 'Create workflow orchestration with webhook integrations'
  },
  {
    id: '4',
    name: 'Code Analysis Engine',
    description: 'Pinned project: Code Analysis Engine',
    repository: 'https://github.com/Zeeeepa/graph-sitter',
    status: 'active',
    progress: 0,
    flowEnabled: false,
    flowStatus: 'stopped',
    lastActivity: new Date(),
    tags: ['pinned'],
    metrics: {
      commits: 0,
      prs: 0,
      contributors: 1,
      issues: 0
    }
  }
];

