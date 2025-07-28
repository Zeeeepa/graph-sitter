import React from 'react';

interface Project {
  id: string;
  name: string;
  description?: string;
  status?: string;
}

interface AgentRunDialogProps {
  isOpen: boolean;
  onClose: () => void;
  project: Project | null;
}

export const AgentRunDialog: React.FC<AgentRunDialogProps> = ({ isOpen, onClose, project }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold mb-4">Agent Run Dialog</h2>
        {project && (
          <div className="mb-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">Project: {project.name}</p>
            {project.description && (
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">{project.description}</p>
            )}
          </div>
        )}
        <p className="text-gray-600 dark:text-gray-400 mb-4">Agent execution functionality coming soon...</p>
        <button 
          onClick={onClose}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  );
};
