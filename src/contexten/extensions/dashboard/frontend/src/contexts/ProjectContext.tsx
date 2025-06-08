import React, { createContext, useContext, useState, useEffect } from 'react';
import { Project, ProjectMetrics } from '../types/dashboard';
import { useSettings } from './SettingsContext';
import { DashboardAPI } from '../api/dashboardApi';

interface ProjectContextType {
  projects: Project[];
  loading: boolean;
  error: string | null;
  pinProject: (projectId: string) => Promise<void>;
  unpinProject: (projectId: string) => Promise<void>;
  getProjectMetrics: (projectId: string) => Promise<ProjectMetrics>;
  refreshProjects: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType>({
  projects: [],
  loading: false,
  error: null,
  pinProject: async () => {},
  unpinProject: async () => {},
  getProjectMetrics: async () => ({
    codeQuality: 0,
    workflowSuccessRate: 0,
    activeContributors: 0,
    openIssues: 0,
    activityTimeline: [],
    workflowPerformance: [],
    codeAnalysis: {
      linesOfCode: 0,
      testCoverage: 0,
      technicalDebt: 0,
      duplication: 0,
    },
    teamPerformance: {
      avgPRReviewTime: 0,
      avgIssueResolutionTime: 0,
      sprintVelocity: 0,
      teamSatisfaction: 0,
    },
  }),
  refreshProjects: async () => {},
});

export const useProject = () => useContext(ProjectContext);

interface ProjectProviderProps {
  children: React.ReactNode;
}

export const ProjectProvider: React.FC<ProjectProviderProps> = ({ children }) => {
  const { settings } = useSettings();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [api, setApi] = useState<DashboardAPI | null>(null);

  useEffect(() => {
    setApi(new DashboardAPI(settings));
  }, [settings]);

  const fetchProjects = async () => {
    if (!api) return;
    try {
      setLoading(true);
      const fetchedProjects = await api.getProjects();
      setProjects(fetchedProjects);
      setError(null);
    } catch (err) {
      console.error('Error fetching projects:', err);
      setError('Failed to fetch projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (api) {
      fetchProjects();
    }
  }, [api]);

  const pinProject = async (projectId: string) => {
    if (!api) return;
    try {
      await api.pinProject({ projectId });
      setProjects(prev =>
        prev.map(p =>
          p.id === projectId
            ? { ...p, pinned: true }
            : p
        )
      );
    } catch (err) {
      console.error('Error pinning project:', err);
      throw err;
    }
  };

  const unpinProject = async (projectId: string) => {
    if (!api) return;
    try {
      await api.unpinProject({ projectId });
      setProjects(prev =>
        prev.map(p =>
          p.id === projectId
            ? { ...p, pinned: false }
            : p
        )
      );
    } catch (err) {
      console.error('Error unpinning project:', err);
      throw err;
    }
  };

  const getProjectMetrics = async (projectId: string): Promise<ProjectMetrics> => {
    if (!api) {
      throw new Error('API not initialized');
    }

    try {
      const project = projects.find(p => p.id === projectId);
      if (!project) {
        throw new Error('Project not found');
      }

      // Get metrics from different services
      const [flowMetrics, linearMetrics, githubMetrics] = await Promise.all([
        api.flowService.getFlowMetrics(projectId),
        api.linearService.getProjectMetrics(project.linearId || ''),
        api.githubService.getRepositoryMetrics(
          project.repository.split('/').slice(-2)[0],
          project.repository.split('/').slice(-2)[1]
        ),
      ]);

      // Get activity timeline
      const activityTimeline = await api.githubService.getActivityTimeline(
        project.repository.split('/').slice(-2)[0],
        project.repository.split('/').slice(-2)[1]
      );

      // Get code analysis
      const codeAnalysis = await api.codegenService.analyzeCode(
        project.repository,
        'main'
      );

      return {
        codeQuality: codeAnalysis.qualityScore,
        workflowSuccessRate: Math.round(
          (flowMetrics.successful / (flowMetrics.successful + flowMetrics.failed)) * 100
        ),
        activeContributors: githubMetrics.activeContributors,
        openIssues: linearMetrics.openIssues,
        activityTimeline,
        workflowPerformance: [
          {
            name: 'Code Analysis',
            successful: flowMetrics.codeAnalysis.successful,
            failed: flowMetrics.codeAnalysis.failed,
          },
          {
            name: 'Tests',
            successful: flowMetrics.tests.successful,
            failed: flowMetrics.tests.failed,
          },
          {
            name: 'Deployments',
            successful: flowMetrics.deployments.successful,
            failed: flowMetrics.deployments.failed,
          },
        ],
        codeAnalysis: {
          linesOfCode: codeAnalysis.linesOfCode,
          testCoverage: codeAnalysis.testCoverage,
          technicalDebt: codeAnalysis.technicalDebt,
          duplication: codeAnalysis.duplication,
        },
        teamPerformance: {
          avgPRReviewTime: githubMetrics.avgPRReviewTime,
          avgIssueResolutionTime: linearMetrics.avgIssueResolutionTime,
          sprintVelocity: linearMetrics.sprintVelocity,
          teamSatisfaction: linearMetrics.teamSatisfaction,
        },
      };
    } catch (err) {
      console.error('Error getting project metrics:', err);
      throw err;
    }
  };

  return (
    <ProjectContext.Provider
      value={{
        projects,
        loading,
        error,
        pinProject,
        unpinProject,
        getProjectMetrics,
        refreshProjects: fetchProjects,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

