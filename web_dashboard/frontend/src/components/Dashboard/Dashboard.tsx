import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { 
  Bars3Icon,
  XMarkIcon,
  FolderIcon,
  MagnifyingGlassIcon,
  CodeBracketIcon,
  ExclamationTriangleIcon,
  CubeIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  PlayIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { useActiveProject, useViewState, useViewActions, useCodeAnalysis } from '@/store';
import { FileTree } from '@/components/FileTree/FileTree';
import { CodeEditor } from '@/components/CodeEditor/CodeEditor';
import { SymbolNavigator } from '@/components/SymbolNavigator/SymbolNavigator';
import { SearchPanel } from '@/components/SearchPanel/SearchPanel';
import { ProblemsPanel } from '@/components/ProblemsPanel/ProblemsPanel';
import { DependenciesPanel } from '@/components/DependenciesPanel/DependenciesPanel';
import { ProjectSelector } from '@/components/ProjectSelector/ProjectSelector';
import { AgentRunDialog } from '@/components/AgentRunDialog/AgentRunDialog';
import { CodeGraph } from '@/components/CodeGraph/CodeGraph';
import { StatusBar } from '@/components/StatusBar/StatusBar';
import { ActivityBar } from '@/components/ActivityBar/ActivityBar';
import { useFileContent } from '@/hooks/useFileContent';
import { useCodeAnalysisQuery } from '@/hooks/useCodeAnalysis';

interface DashboardProps {
  className?: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ className }) => {
  const { projectId } = useParams<{ projectId: string }>();
  const activeProject = useActiveProject();
  const viewState = useViewState();
  const codeAnalysis = useCodeAnalysis();
  const { setActiveTab, setSidebarWidth, setBottomPanelHeight } = useViewActions();
  
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isBottomPanelVisible, setIsBottomPanelVisible] = useState(true);
  const [showAgentDialog, setShowAgentDialog] = useState(false);
  const [showGraphView, setShowGraphView] = useState(false);

  // Load file content for selected file
  const { data: fileContent, isLoading: isLoadingFile } = useFileContent(
    activeProject?.id,
    viewState.selectedFile
  );

  // Load code analysis for active project
  const { data: analysisData, isLoading: isLoadingAnalysis } = useCodeAnalysisQuery(
    activeProject?.id
  );

  // Handle file selection from tree
  const handleFileSelect = useCallback((filePath: string) => {
    // File selection is handled by the store
  }, []);

  // Handle file double-click to open in editor
  const handleFileDoubleClick = useCallback((filePath: string) => {
    // Open file in editor
  }, []);

  // Handle symbol navigation
  const handleSymbolClick = useCallback((symbol: any) => {
    // Navigate to symbol definition
  }, []);

  // Handle go to definition
  const handleGoToDefinition = useCallback((filePath: string, line: number, column: number) => {
    // Navigate to definition
  }, []);

  // Handle find references
  const handleFindReferences = useCallback((filePath: string, line: number, column: number) => {
    // Find and show references
  }, []);

  // Handle agent run
  const handleStartAgentRun = useCallback((targetText: string) => {
    setShowAgentDialog(true);
  }, []);

  // Sidebar tabs configuration
  const sidebarTabs = [
    {
      id: 'explorer' as const,
      label: 'Explorer',
      icon: FolderIcon,
      component: (
        <FileTree
          onFileSelect={handleFileSelect}
          onFileDoubleClick={handleFileDoubleClick}
        />
      )
    },
    {
      id: 'search' as const,
      label: 'Search',
      icon: MagnifyingGlassIcon,
      component: <SearchPanel />
    },
    {
      id: 'symbols' as const,
      label: 'Symbols',
      icon: CodeBracketIcon,
      component: (
        <SymbolNavigator
          onSymbolClick={handleSymbolClick}
        />
      )
    },
    {
      id: 'problems' as const,
      label: 'Problems',
      icon: ExclamationTriangleIcon,
      component: <ProblemsPanel />
    },
    {
      id: 'dependencies' as const,
      label: 'Dependencies',
      icon: CubeIcon,
      component: <DependenciesPanel />
    }
  ];

  const activeSidebarTab = sidebarTabs.find(tab => tab.id === viewState.activeTab);

  if (!activeProject) {
    return (
      <div className={clsx('h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900', className)}>
        <div className="text-center">
          <FolderIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            No Project Selected
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Select a project to start exploring your codebase
          </p>
          <ProjectSelector />
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('h-screen flex flex-col bg-gray-50 dark:bg-gray-900', className)}>
      {/* Top Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-4">
          <ProjectSelector />
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAgentDialog(true)}
              className="flex items-center px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <PlayIcon className="w-4 h-4 mr-1" />
              Run Agent
            </button>
            
            <button
              onClick={() => setShowGraphView(!showGraphView)}
              className={clsx(
                'flex items-center px-3 py-1.5 text-sm rounded-md transition-colors',
                showGraphView
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              )}
            >
              <ChartBarIcon className="w-4 h-4 mr-1" />
              Graph View
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {activeProject.name}
          </span>
          
          <button className="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
            <Cog6ToothIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Activity Bar */}
        <ActivityBar
          activeTab={viewState.activeTab}
          onTabChange={setActiveTab}
          tabs={sidebarTabs.map(tab => ({
            id: tab.id,
            label: tab.label,
            icon: tab.icon
          }))}
        />

        {/* Sidebar */}
        <AnimatePresence>
          {!isSidebarCollapsed && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: viewState.sidebarWidth, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-hidden"
            >
              <div className="h-full flex flex-col">
                {/* Sidebar Header */}
                <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {activeSidebarTab?.label}
                  </h3>
                  <button
                    onClick={() => setIsSidebarCollapsed(true)}
                    className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                </div>

                {/* Sidebar Content */}
                <div className="flex-1 overflow-hidden">
                  {activeSidebarTab?.component}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Editor Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <PanelGroup direction="vertical">
            {/* Editor Panel */}
            <Panel defaultSize={70} minSize={30}>
              <div className="h-full">
                {showGraphView ? (
                  <CodeGraph
                    className="h-full"
                    onNodeClick={(node) => {
                      if (node.file_path) {
                        handleFileSelect(node.file_path);
                      }
                    }}
                  />
                ) : (
                  <CodeEditor
                    filePath={viewState.selectedFile}
                    content={fileContent}
                    errors={codeAnalysis?.file_tree ? getAllErrors(codeAnalysis.file_tree) : []}
                    symbols={codeAnalysis?.symbols || []}
                    onSymbolClick={handleSymbolClick}
                    onGoToDefinition={handleGoToDefinition}
                    onFindReferences={handleFindReferences}
                  />
                )}
              </div>
            </Panel>

            {/* Bottom Panel */}
            {isBottomPanelVisible && (
              <>
                <PanelResizeHandle className="h-1 bg-gray-200 dark:bg-gray-700 hover:bg-blue-500 transition-colors" />
                <Panel defaultSize={30} minSize={15} maxSize={50}>
                  <div className="h-full bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center space-x-4">
                        <button
                          className={clsx(
                            'text-sm font-medium',
                            'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                          )}
                        >
                          Problems
                        </button>
                        <button className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100">
                          Output
                        </button>
                        <button className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100">
                          Terminal
                        </button>
                      </div>
                      
                      <button
                        onClick={() => setIsBottomPanelVisible(false)}
                        className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    </div>
                    
                    <div className="flex-1 overflow-hidden">
                      <ProblemsPanel />
                    </div>
                  </div>
                </Panel>
              </>
            )}
          </PanelGroup>
        </div>
      </div>

      {/* Status Bar */}
      <StatusBar
        activeProject={activeProject}
        selectedFile={viewState.selectedFile}
        codeAnalysis={codeAnalysis}
        onToggleBottomPanel={() => setIsBottomPanelVisible(!isBottomPanelVisible)}
      />

      {/* Agent Run Dialog */}
      <AgentRunDialog
        isOpen={showAgentDialog}
        onClose={() => setShowAgentDialog(false)}
        project={activeProject}
      />

      {/* Sidebar Toggle Button (when collapsed) */}
      {isSidebarCollapsed && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setIsSidebarCollapsed(false)}
          className="fixed left-2 top-1/2 transform -translate-y-1/2 z-50 p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg hover:shadow-xl transition-shadow"
        >
          <Bars3Icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </motion.button>
      )}
    </div>
  );
};

// Helper function to get all errors from file tree
function getAllErrors(fileTree: any): any[] {
  const errors: any[] = [];
  
  const traverse = (node: any) => {
    if (node.errors) {
      errors.push(...node.errors);
    }
    if (node.children) {
      node.children.forEach(traverse);
    }
  };
  
  traverse(fileTree);
  return errors;
}
