import { useState, useEffect, useCallback, useContext } from 'react';
import { Project } from '../types/dashboard';
import { ProjectManager, ProjectManagerConfig } from '../services/ProjectManager';
import { SettingsContext } from '../contexts/SettingsContext';

export function useProject() {
  const settings = useContext(SettingsContext);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projectManager, setProjectManager] = useState<ProjectManager | null>(null);

  useEffect(() => {
    if (settings) {
      const config: ProjectManagerConfig = {
        githubToken: settings.githubToken,
        linearToken: settings.linearToken,
        codegenConfig: {
          orgId: settings.codegenOrgId,
          token: settings.codegenToken,
        },
        flowConfig: {
          prefectToken: settings.prefectToken || '',
          controlFlowToken: settings.controlFlowToken || '',
          agentFlowToken: settings.agentFlowToken || '',
        },
      };
      setProjectManager(new ProjectManager(config));
    }
  }, [settings]);

  const loadProjects = useCallback(async () => {
    if (!projectManager) return;

    try {
      setLoading(true);
      setError(null);
      const discoveredProjects = await projectManager.discoverProjects();
      setProjects(discoveredProjects);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  }, [projectManager]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const pinProject = useCallback(async (projectId: string) => {
    if (!projectManager) return;

    try {
      await projectManager.pinProject(projectId);
      await loadProjects(); // Reload projects to get updated list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to pin project');
    }
  }, [projectManager, loadProjects]);

  const unpinProject = useCallback(async (projectId: string) => {
    if (!projectManager) return;

    try {
      await projectManager.unpinProject(projectId);
      await loadProjects(); // Reload projects to get updated list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unpin project');
    }
  }, [projectManager, loadProjects]);

  const getProjectMetrics = useCallback(async (projectId: string) => {
    if (!projectManager) return null;

    try {
      return await projectManager.getProjectMetrics(projectId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get project metrics');
      return null;
    }
  }, [projectManager]);

  return {
    projects,
    loading,
    error,
    pinProject,
    unpinProject,
    getProjectMetrics,
    refresh: loadProjects,
  };
}

