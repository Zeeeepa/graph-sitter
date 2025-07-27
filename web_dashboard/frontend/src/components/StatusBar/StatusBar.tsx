import React from 'react';

interface StatusBarProps {
  activeProject: any;
  selectedFile?: string;
  codeAnalysis: any;
  onToggleBottomPanel: () => void;
}

export const StatusBar: React.FC<StatusBarProps> = ({ 
  activeProject, 
  selectedFile, 
  codeAnalysis, 
  onToggleBottomPanel 
}) => {
  return (
    <div className="h-6 bg-blue-600 text-white text-xs flex items-center px-4">
      <span>Status Bar - Project: {activeProject?.name || 'None'}</span>
      {selectedFile && <span className="ml-4">File: {selectedFile}</span>}
    </div>
  );
};

