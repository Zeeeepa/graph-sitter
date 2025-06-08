import { useState, useEffect } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import { DashboardAPI } from '../api/dashboardApi';

interface ProjectMetrics {
  codeQuality: number;
  workflowSuccessRate: number;
  activeContributors: number;
  openIssues: number;
  activityTimeline: Array<{
    date: string;
    commits: number;
    prs: number;
  }>;
  workflowPerformance: Array<{
    name: string;
    successful: number;
    failed: number;
  }>;
  codeAnalysis: {
    linesOfCode: number;
    testCoverage: number;
    technicalDebt: number;
    duplication: number;
  };
  teamPerformance: {
    avgPRReviewTime: number;
    avgIssueResolutionTime: number;
    sprintVelocity: number;
    teamSatisfaction: number;
  };
}

export const useProjectMetrics = (projectId: string) => {
  const [metrics, setMetrics] = useState<ProjectMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { settings } = useSettings();
  const api = new DashboardAPI(settings);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch metrics from different services
        const [
          githubMetrics,
          linearMetrics,
          codegenMetrics,
          flowMetrics
        ] = await Promise.all([
          api.githubService.getRepositoryMetrics(projectId),
          api.linearService.getProjectMetrics(projectId),
          api.codegenService.analyzeCode(projectId, 'main'),
          api.flowService.getFlowMetrics(projectId)
        ]);

        // Calculate activity timeline
        const activityTimeline = await api.githubService.getActivityTimeline(projectId);

        // Calculate workflow performance
        const workflowPerformance = [
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
        ];

        // Combine all metrics
        const combinedMetrics: ProjectMetrics = {
          codeQuality: codegenMetrics.qualityScore,
          workflowSuccessRate: Math.round(
            (flowMetrics.successful / (flowMetrics.successful + flowMetrics.failed)) * 100
          ),
          activeContributors: githubMetrics.activeContributors,
          openIssues: linearMetrics.openIssues,
          activityTimeline,
          workflowPerformance,
          codeAnalysis: {
            linesOfCode: codegenMetrics.linesOfCode,
            testCoverage: codegenMetrics.testCoverage,
            technicalDebt: codegenMetrics.technicalDebt,
            duplication: codegenMetrics.duplication,
          },
          teamPerformance: {
            avgPRReviewTime: githubMetrics.avgPRReviewTime,
            avgIssueResolutionTime: linearMetrics.avgIssueResolutionTime,
            sprintVelocity: linearMetrics.sprintVelocity,
            teamSatisfaction: linearMetrics.teamSatisfaction,
          },
        };

        setMetrics(combinedMetrics);
      } catch (err) {
        console.error('Error fetching project metrics:', err);
        setError('Failed to fetch project metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, [projectId, api]);

  return { metrics, loading, error };
};

