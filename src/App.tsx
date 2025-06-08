import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  IconButton,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { Project, Settings, Task, WorkflowEvent } from './types/dashboard';
import ProjectCard from './components/ProjectCard';
import ProjectDialog from './components/ProjectDialog';
import SettingsDialog from './components/SettingsDialog';
import ProjectSelectionDialog from './components/ProjectSelectionDialog';
import TaskManagement from './components/TaskManagement';
import WorkflowControl from './components/WorkflowControl';
import RealTimeMetrics from './components/RealTimeMetrics';
import Dashboard from './components/Dashboard';
import websocketService from './services/websocketService';

// Mock repositories data
const mockRepositories = [
  {
    id: '1',
    name: 'graph-sitter',
    description: 'Code analysis SDK with advanced manipulation capabilities',
    url: 'https://github.com/Zeeeepa/graph-sitter',
    language: 'Python',
    stars: 42,
    lastUpdated: new Date(),
  },
  {
    id: '2',
    name: 'contexten',
    description: 'Agentic orchestrator with chat-agent integrations',
    url: 'https://github.com/Zeeeepa/contexten',
    language: 'TypeScript',
    stars: 28,
    lastUpdated: new Date(),
  },
  {
    id: '3',
    name: 'voltagent',
    description: 'Open Source TypeScript AI Agent Framework',
    url: 'https://github.com/Zeeeepa/voltagent',
    language: 'TypeScript',
    stars: 15,
    lastUpdated: new Date(),
  },
];

const App: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [openSettings, setOpenSettings] = useState(false);
  const [openProjectDialog, setOpenProjectDialog] = useState(false);
  const [openProjectSelection, setOpenProjectSelection] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [workflowEvents, setWorkflowEvents] = useState<WorkflowEvent[]>([]);

  const [settings, setSettings] = useState<Settings>({
    githubToken: '',
    linearToken: '',
    codegenOrgId: '',
    codegenToken: '',
    autoStartFlows: false,
    enableNotifications: true,
    enableAnalytics: true,
  });

  useEffect(() => {
    // Load initial data
    loadMockData();

    // Setup WebSocket connection
    websocketService.connect();
    const unsubscribe = websocketService.addListener((event) => {
      handleWebSocketEvent(event);
    });

    return () => {
      unsubscribe();
      websocketService.disconnect();
    };
  }, []);

  const loadMockData = () => {
    setLoading(true);
    try {
      // Mock projects data
      const mockProjects: Project[] = [
        {
          id: '1',
          name: 'AI Agent Framework',
          description: 'Core AI agent processing engine',
          status: 'active',
          repository: 'https://github.com/Zeeeepa/ai-agents',
          progress: 70,
          flowEnabled: true,
          flowStatus: 'running',
          lastActivity: new Date(),
          tags: ['ai', 'agents', 'python'],
          metrics: {
            commits: 156,
            prs: 23,
            contributors: 8,
            issues: 45
          }
        },
        {
          id: '2',
          name: 'Dashboard UI',
          description: 'React dashboard interface',
          status: 'active',
          repository: 'https://github.com/Zeeeepa/dashboard',
          progress: 60,
          flowEnabled: false,
          flowStatus: 'stopped',
          lastActivity: new Date(),
          tags: ['frontend', 'react'],
          metrics: {
            commits: 89,
            prs: 12,
            contributors: 5,
            issues: 28
          }
        }
      ];
      
      setProjects(mockProjects);
      setLoading(false);
    } catch (err) {
      setError('Failed to load projects');
      setLoading(false);
    }
  };

  const handleWebSocketEvent = (event: WebSocketEvent) => {
    switch (event.type) {
      case 'project_updated':
        setProjects(prev => 
          prev.map(p => p.id === event.payload.id ? { ...p, ...event.payload } : p)
        );
        break;
      case 'workflow_event':
        setWorkflowEvents(prev => [event.payload, ...prev].slice(0, 50));
        break;
      case 'metrics_updated':
        // Handle metrics update
        break;
    }
  };

  const handleCreateProject = () => {
    setOpenProjectSelection(true);
  };

  const handleRepositorySelect = (repository: any) => {
    // Create a new project from the selected repository
    const newProject: Project = {
      id: Date.now().toString(),
      name: repository.name,
      description: repository.description || 'Project created from repository',
      status: 'active',
      repository: repository.url,
      progress: 0,
      flowEnabled: false,
      flowStatus: 'stopped',
      lastActivity: new Date(),
      tags: repository.language ? [repository.language.toLowerCase()] : [],
      metrics: {
        commits: 0,
        prs: 0,
        contributors: 1,
        issues: 0
      }
    };
    
    setProjects(prev => [...prev, newProject]);
    setOpenProjectSelection(false);
  };

  const handleSaveProject = (project: Project) => {
    if (project.id && projects.some(p => p.id === project.id)) {
      setProjects(prev =>
        prev.map(p => p.id === project.id ? project : p)
      );
    } else {
      setProjects(prev => [...prev, project]);
    }
    setOpenProjectDialog(false);
  };

  const handleTaskUpdate = (projectId: string, task: Task) => {
    setProjects(prev =>
      prev.map(p => {
        if (p.id === projectId && p.plan) {
          return {
            ...p,
            plan: {
              ...p.plan,
              tasks: p.plan.tasks.map(t => t.id === task.id ? task : t),
            },
          };
        }
        return p;
      })
    );
  };

  const handleTaskCreate = (projectId: string, task: Partial<Task>) => {
    setProjects(prev =>
      prev.map(p => {
        if (p.id === projectId && p.plan) {
          return {
            ...p,
            plan: {
              ...p.plan,
              tasks: [...p.plan.tasks, task as Task],
            },
          };
        }
        return p;
      })
    );
  };

  const handleTaskDelete = (projectId: string, taskId: string) => {
    setProjects(prev =>
      prev.map(p => {
        if (p.id === projectId && p.plan) {
          return {
            ...p,
            plan: {
              ...p.plan,
              tasks: p.plan.tasks.filter(t => t.id !== taskId),
            },
          };
        }
        return p;
      })
    );
  };

  const handleStartFlow = async (projectId: string) => {
    setProjects(prev =>
      prev.map(p =>
        p.id === projectId
          ? { ...p, flowStatus: 'running', flowEnabled: true }
          : p
      )
    );
  };

  const handleStopFlow = async (projectId: string) => {
    setProjects(prev =>
      prev.map(p =>
        p.id === projectId
          ? { ...p, flowStatus: 'stopped', flowEnabled: false }
          : p
      )
    );
  };

  const handleRefreshStatus = async (projectId: string) => {
    // In a real app, this would fetch the latest status from the server
    console.log('Refreshing status for project:', projectId);
  };

  const handleDialogClose = () => {
    setSelectedProject(null);
    setOpenProjectDialog(false);
  };

  const handleSettingsSave = (newSettings: Settings) => {
    setSettings(newSettings);
    setOpenSettings(false);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Router>
      <div>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          {/* Fixed: ProjectSelectionDialog now has all required props */}
          <Route 
            path="/projects" 
            element={
              <ProjectSelectionDialog 
                open={true}
                onClose={() => window.history.back()}
                repositories={mockRepositories}
                onSelectRepository={handleRepositorySelect}
              />
            } 
          />
        </Routes>

        {/* Dialogs */}
        <ProjectSelectionDialog
          open={openProjectSelection}
          onClose={() => setOpenProjectSelection(false)}
          repositories={mockRepositories}
          onSelectRepository={handleRepositorySelect}
        />

        <ProjectDialog
          open={openProjectDialog}
          project={selectedProject}
          onClose={handleDialogClose}
          onSave={handleSaveProject}
        />

        <SettingsDialog
          open={openSettings}
          settings={settings}
          onClose={() => setOpenSettings(false)}
          onSave={handleSettingsSave}
        />
      </div>
    </Router>
  );
};

export default App;

