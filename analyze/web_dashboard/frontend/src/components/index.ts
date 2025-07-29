// Main components
export { Dashboard } from './Dashboard/Dashboard';
export { FileTree } from './FileTree/FileTree';
export { CodeEditor } from './CodeEditor/CodeEditor';
export { CodeGraph } from './CodeGraph/CodeGraph';
export { TestDashboard } from './TestDashboard/TestDashboard';

// UI components
export { ActivityBar } from './ActivityBar/ActivityBar';
export { VirtualizedList } from './VirtualizedList/VirtualizedList';

// Stub components (to be implemented)
export const SymbolNavigator = ({ onSymbolClick }: { onSymbolClick?: (symbol: any) => void }) => (
  <div className="p-4 text-gray-500">Symbol Navigator - Coming Soon</div>
);

export const SearchPanel = () => (
  <div className="p-4 text-gray-500">Search Panel - Coming Soon</div>
);

export const ProblemsPanel = () => (
  <div className="p-4 text-gray-500">Problems Panel - Coming Soon</div>
);

export const DependenciesPanel = () => (
  <div className="p-4 text-gray-500">Dependencies Panel - Coming Soon</div>
);

export const ProjectSelector = () => (
  <div className="p-2 text-gray-500">Project Selector - Coming Soon</div>
);

export const AgentRunDialog = ({ isOpen, onClose, project }: { 
  isOpen: boolean; 
  onClose: () => void; 
  project: any; 
}) => (
  isOpen ? (
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
  ) : null
);

export const StatusBar = ({ activeProject, selectedFile, codeAnalysis, onToggleBottomPanel }: {
  activeProject: any;
  selectedFile?: string;
  codeAnalysis: any;
  onToggleBottomPanel: () => void;
}) => (
  <div className="h-6 bg-blue-600 text-white text-xs flex items-center px-4">
    <span>Status Bar - Project: {activeProject?.name || 'None'}</span>
    {selectedFile && <span className="ml-4">File: {selectedFile}</span>}
  </div>
);
