import React from 'react';
import { Project, FlowStatus } from '../types/dashboard';

interface ProjectCardProps {
  project: Project;
  onSelect: (project: Project) => void;
  onToggleFlow: (projectId: string) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ 
  project, 
  onSelect, 
  onToggleFlow 
}) => {
  const getStatusColor = (status: FlowStatus) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'paused': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getProgressPercentage = () => {
    if (!project.plan || project.plan.tasks.length === 0) return 0;
    const completedTasks = project.plan.tasks.filter(task => task.status === 'completed').length;
    return (completedTasks / project.plan.tasks.length) * 100;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
      <div className="flex justify-between items-start mb-4">
        <div onClick={() => onSelect(project)} className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
          <p className="text-sm text-gray-600">{project.description}</p>
          <div className="flex items-center mt-2">
            <span className="text-xs text-gray-500">Repository:</span>
            <span className="text-xs text-blue-600 ml-1">{project.repository}</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${getStatusColor(project.flowStatus)}`}></div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleFlow(project.id);
            }}
            className={`px-3 py-1 text-xs rounded-full ${
              project.flowStatus === 'running' 
                ? 'bg-red-100 text-red-800 hover:bg-red-200' 
                : 'bg-green-100 text-green-800 hover:bg-green-200'
            }`}
          >
            {project.flowStatus === 'running' ? 'Stop' : 'Start'} Flow
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>{Math.round(getProgressPercentage())}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${getProgressPercentage()}%` }}
          ></div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-lg font-semibold text-gray-900">
            {project.stats?.openPRs || 0}
          </div>
          <div className="text-xs text-gray-500">Open PRs</div>
        </div>
        <div>
          <div className="text-lg font-semibold text-gray-900">
            {project.stats?.openIssues || 0}
          </div>
          <div className="text-xs text-gray-500">Issues</div>
        </div>
        <div>
          <div className="text-lg font-semibold text-gray-900">
            {project.plan?.tasks.length || 0}
          </div>
          <div className="text-xs text-gray-500">Tasks</div>
        </div>
      </div>

      {/* Recent Events */}
      {project.recentEvents && project.recentEvents.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Activity</h4>
          <div className="space-y-1">
            {project.recentEvents.slice(0, 3).map((event, index) => (
              <div key={index} className="text-xs text-gray-600 flex justify-between">
                <span className="truncate">{event.message}</span>
                <span className="text-gray-400 ml-2">{event.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

