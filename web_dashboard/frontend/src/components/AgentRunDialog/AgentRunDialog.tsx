import React from 'react';

interface AgentRunDialogProps {
  isOpen: boolean;
  onClose: () => void;
  project: any;
}

export const AgentRunDialog: React.FC<AgentRunDialogProps> = ({ isOpen, onClose, project }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">Agent Run Dialog</h2>
        <p className="text-gray-600 dark:text-gray-400 mb-4">Coming Soon</p>
        <button 
          onClick={onClose}
          className="px-4 py-2 bg-blue-600 text-white rounded-md"
        >
          Close
        </button>
      </div>
    </div>
  );
};

