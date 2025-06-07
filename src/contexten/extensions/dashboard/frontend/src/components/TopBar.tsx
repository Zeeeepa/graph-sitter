import React, { useState } from 'react';
import { Project } from '../types/dashboard';

interface TopBarProps {
  availableProjects: Project[];
  onPinProject: (project: Project) => void;
  onOpenSettings: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  availableProjects,
  onPinProject,
  onOpenSettings
}) => {
  const [showProjectDropdown, setShowProjectDropdown] = useState(false);

  return (
    <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">Contexten Dashboard</h1>
          <div className="text-sm text-gray-500">
            Project Management & Workflow Orchestration
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Select Project to Pin */}
          <div className="relative">
            <button
              onClick={() => setShowProjectDropdown(!showProjectDropdown)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center space-x-2"
            >
              <span>📌</span>
              <span>Select Project To Pin</span>
              <span className="text-blue-200">▼</span>
            </button>

            {showProjectDropdown && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                <div className="p-3 border-b border-gray-200">
                  <h3 className="text-sm font-medium text-gray-900">Available Projects</h3>
                  <p className="text-xs text-gray-500">Select a project to add to your dashboard</p>
                </div>
                <div className="max-h-60 overflow-y-auto">
                  {availableProjects.length > 0 ? (
                    availableProjects.map((project) => (
                      <button
                        key={project.id}
                        onClick={() => {
                          onPinProject(project);
                          setShowProjectDropdown(false);
                        }}
                        className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                      >
                        <div className="font-medium text-gray-900">{project.name}</div>
                        <div className="text-sm text-gray-600">{project.repository}</div>
                        <div className="text-xs text-gray-500 mt-1">{project.description}</div>
                      </button>
                    ))
                  ) : (
                    <div className="px-4 py-6 text-center text-gray-500">
                      <div className="text-2xl mb-2">🔍</div>
                      <p className="text-sm">No projects available</p>
                      <p className="text-xs">Check your GitHub integration settings</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Settings Button */}
          <button
            onClick={onOpenSettings}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 flex items-center space-x-2"
          >
            <span>⚙️</span>
            <span>Settings</span>
          </button>
        </div>
      </div>

      {/* Click outside to close dropdown */}
      {showProjectDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowProjectDropdown(false)}
        />
      )}
    </div>
  );
};

