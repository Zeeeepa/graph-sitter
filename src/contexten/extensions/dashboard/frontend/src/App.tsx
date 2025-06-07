import React, { useState, useEffect } from 'react';
import { ProjectCard } from './components/ProjectCard';
import { ProjectDialog } from './components/ProjectDialog';
import { TopBar } from './components/TopBar';
import { SettingsDialog, EnvironmentSettings } from './components/SettingsDialog';
import { Project } from './types/dashboard';

const App: React.FC = () => {
  const [pinnedProjects, setPinnedProjects] = useState<Project[]>([]);
  const [availableProjects, setAvailableProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [showProjectDialog, setShowProjectDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);

  useEffect(() => {
    loadPinnedProjects();
    loadAvailableProjects();
  }, []);

  const loadPinnedProjects = async () => {
    try {
      const response = await fetch('/api/projects/pinned');
      if (response.ok) {
        const projects = await response.json();
        setPinnedProjects(projects);
      }
    } catch (error) {
      console.error('Failed to load pinned projects:', error);
    }
  };

  const loadAvailableProjects = async () => {
    try {
      const response = await fetch('/api/projects/available');
      if (response.ok) {
        const projects = await response.json();
        setAvailableProjects(projects);
      }
    } catch (error) {
      console.error('Failed to load available projects:', error);
    }
  };

  const handlePinProject = async (project: Project) => {
    try {
      const response = await fetch('/api/projects/pin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectId: project.id })
      });

      if (response.ok) {
        setPinnedProjects(prev => [...prev, project]);
        setAvailableProjects(prev => prev.filter(p => p.id !== project.id));
      }
    } catch (error) {
      console.error('Failed to pin project:', error);
    }
  };

  const handleSelectProject = (project: Project) => {
    setSelectedProject(project);
    setShowProjectDialog(true);
  };

  const handleToggleFlow = async (projectId: string) => {
    try {
      const project = pinnedProjects.find(p => p.id === projectId);
      if (!project) return;

      const action = project.flowStatus === 'running' ? 'stop' : 'start';
      const response = await fetch(`/api/projects/${projectId}/flow/${action}`, {
        method: 'POST'
      });

      if (response.ok) {
        setPinnedProjects(prev => prev.map(p => 
          p.id === projectId 
            ? { ...p, flowStatus: action === 'start' ? 'running' : 'stopped' }
            : p
        ));
      }
    } catch (error) {
      console.error('Failed to toggle flow:', error);
    }
  };

  const handleCreatePlan = async (projectId: string, requirements: string) => {
    try {
      const response = await fetch(`/api/projects/${projectId}/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements })
      });

      if (response.ok) {
        const plan = await response.json();
        setPinnedProjects(prev => prev.map(p => 
          p.id === projectId 
            ? { ...p, plan, requirements }
            : p
        ));
        setSelectedProject(prev => prev ? { ...prev, plan, requirements } : null);
      }
    } catch (error) {
      console.error('Failed to create plan:', error);
    }
  };

  const handleStartFlow = async (projectId: string) => {
    try {
      const response = await fetch(`/api/projects/${projectId}/flow/start`, {
        method: 'POST'
      });

      if (response.ok) {
        setPinnedProjects(prev => prev.map(p => 
          p.id === projectId 
            ? { ...p, flowStatus: 'running' }
            : p
        ));
        setSelectedProject(prev => prev ? { ...prev, flowStatus: 'running' } : null);
      }
    } catch (error) {
      console.error('Failed to start flow:', error);
    }
  };

  const handleSaveSettings = async (settings: EnvironmentSettings) => {
    try {
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      if (response.ok) {
        // Reload projects after settings update
        loadAvailableProjects();
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <TopBar
        availableProjects={availableProjects}
        onPinProject={handlePinProject}
        onOpenSettings={() => setShowSettingsDialog(true)}
      />

      <main className="container mx-auto px-6 py-8">
        {pinnedProjects.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">📌</div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">No Projects Pinned</h2>
            <p className="text-gray-600 mb-6">
              Start by pinning a project from the "Select Project To Pin" dropdown above.
            </p>
            <p className="text-sm text-gray-500">
              Once pinned, you can add requirements, generate plans, and start automated workflows.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {pinnedProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onSelect={handleSelectProject}
                onToggleFlow={handleToggleFlow}
              />
            ))}
          </div>
        )}
      </main>

      <ProjectDialog
        project={selectedProject}
        isOpen={showProjectDialog}
        onClose={() => {
          setShowProjectDialog(false);
          setSelectedProject(null);
        }}
        onCreatePlan={handleCreatePlan}
        onStartFlow={handleStartFlow}
      />

      <SettingsDialog
        isOpen={showSettingsDialog}
        onClose={() => setShowSettingsDialog(false)}
        onSave={handleSaveSettings}
      />
    </div>
  );
};

export default App;

