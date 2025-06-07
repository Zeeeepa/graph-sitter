import React, { useState } from 'react';
import { Project, Plan, Task } from '../types/dashboard';

interface ProjectDialogProps {
  project: Project | null;
  isOpen: boolean;
  onClose: () => void;
  onCreatePlan: (projectId: string, requirements: string) => void;
  onStartFlow: (projectId: string) => void;
}

export const ProjectDialog: React.FC<ProjectDialogProps> = ({
  project,
  isOpen,
  onClose,
  onCreatePlan,
  onStartFlow
}) => {
  const [activeTab, setActiveTab] = useState<'requirements' | 'plan'>('requirements');
  const [requirements, setRequirements] = useState('');
  const [isCreatingPlan, setIsCreatingPlan] = useState(false);

  if (!isOpen || !project) return null;

  const handleCreatePlan = async () => {
    if (!requirements.trim()) return;
    
    setIsCreatingPlan(true);
    try {
      await onCreatePlan(project.id, requirements);
      setActiveTab('plan');
    } finally {
      setIsCreatingPlan(false);
    }
  };

  const getTaskStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'in_progress': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{project.name}</h2>
            <p className="text-sm text-gray-600">{project.repository}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('requirements')}
            className={`px-6 py-3 text-sm font-medium ${
              activeTab === 'requirements'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Requirements
          </button>
          <button
            onClick={() => setActiveTab('plan')}
            className={`px-6 py-3 text-sm font-medium ${
              activeTab === 'plan'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            disabled={!project.plan}
          >
            Plan {project.plan && `(${project.plan.tasks.length} tasks)`}
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === 'requirements' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Requirements & Instructions
                </label>
                <textarea
                  value={requirements}
                  onChange={(e) => setRequirements(e.target.value)}
                  placeholder="Describe what you want to achieve with this project. Be specific about features, improvements, or fixes needed..."
                  className="w-full h-40 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <button
                onClick={handleCreatePlan}
                disabled={!requirements.trim() || isCreatingPlan}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {isCreatingPlan ? 'Creating Plan...' : 'Generate Plan'}
              </button>

              {project.requirements && (
                <div className="mt-6 p-4 bg-gray-50 rounded-md">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Current Requirements:</h4>
                  <p className="text-sm text-gray-600">{project.requirements}</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'plan' && project.plan && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">Execution Plan</h3>
                <button
                  onClick={() => onStartFlow(project.id)}
                  disabled={project.flowStatus === 'running'}
                  className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {project.flowStatus === 'running' ? 'Flow Running...' : 'Start Flow'}
                </button>
              </div>

              <div className="space-y-3">
                {project.plan.tasks.map((task, index) => (
                  <div key={task.id} className="border border-gray-200 rounded-md p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">
                          {index + 1}. {task.title}
                        </h4>
                        <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${getTaskStatusColor(task.status)}`}>
                        {task.status.replace('_', ' ')}
                      </span>
                    </div>

                    {task.assignee && (
                      <div className="text-xs text-gray-500">
                        Assigned to: {task.assignee}
                      </div>
                    )}

                    {task.estimatedHours && (
                      <div className="text-xs text-gray-500">
                        Estimated: {task.estimatedHours}h
                      </div>
                    )}

                    {task.dependencies && task.dependencies.length > 0 && (
                      <div className="text-xs text-gray-500 mt-1">
                        Dependencies: {task.dependencies.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {project.plan.estimatedDuration && (
                <div className="mt-4 p-3 bg-blue-50 rounded-md">
                  <div className="text-sm text-blue-800">
                    <strong>Estimated Duration:</strong> {project.plan.estimatedDuration}
                  </div>
                  {project.plan.totalTasks && (
                    <div className="text-sm text-blue-700">
                      <strong>Total Tasks:</strong> {project.plan.totalTasks}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'plan' && !project.plan && (
            <div className="text-center py-8">
              <div className="text-gray-400 text-lg mb-2">📋</div>
              <p className="text-gray-600">No plan created yet.</p>
              <p className="text-sm text-gray-500">Switch to Requirements tab to create a plan.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

