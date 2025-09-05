import React from 'react';

interface Project {
  id: string;
  name: string;
  status?: string;
}

interface CodeAnalysis {
  errors?: number;
  warnings?: number;
  linesOfCode?: number;
  status?: 'analyzing' | 'complete' | 'error';
}

interface StatusBarProps {
  activeProject: Project | null;
  selectedFile?: string;
  codeAnalysis: CodeAnalysis | null;
  onToggleBottomPanel: () => void;
}

export const StatusBar: React.FC<StatusBarProps> = ({ 
  activeProject, 
  selectedFile, 
  codeAnalysis, 
  onToggleBottomPanel 
}) => {
  const handleToggleClick = () => {
    onToggleBottomPanel();
  };

  return (
    <div className="h-6 bg-blue-600 text-white text-xs flex items-center px-4 justify-between">
      <div className="flex items-center space-x-4">
        <span>Project: {activeProject?.name || 'None'}</span>
        {selectedFile && <span>File: {selectedFile}</span>}
        {codeAnalysis && (
          <span>
            {codeAnalysis.status === 'analyzing' && 'Analyzing...'}
            {codeAnalysis.status === 'complete' && (
              <>
                {codeAnalysis.errors ? `${codeAnalysis.errors} errors` : ''}
                {codeAnalysis.warnings ? ` ${codeAnalysis.warnings} warnings` : ''}
              </>
            )}
          </span>
        )}
      </div>
      <button 
        onClick={handleToggleClick}
        className="hover:bg-blue-700 px-2 py-1 rounded text-xs transition-colors"
        title="Toggle bottom panel"
      >
        ⬆️
      </button>
    </div>
  );
};
