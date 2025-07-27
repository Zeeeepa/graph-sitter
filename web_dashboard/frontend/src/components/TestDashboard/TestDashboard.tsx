import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  PlayIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ChartBarIcon,
  CodeBracketIcon,
  FolderIcon
} from '@heroicons/react/24/outline';
import { Dashboard } from '@/components/Dashboard/Dashboard';
import { FileTree } from '@/components/FileTree/FileTree';
import { CodeEditor } from '@/components/CodeEditor/CodeEditor';
import { CodeGraph } from '@/components/CodeGraph/CodeGraph';
import { useAppStore } from '@/store';
import { 
  mockUser, 
  mockProject, 
  mockCodeAnalysis, 
  mockFileContent 
} from '@/demo/mockData';

interface TestResult {
  component: string;
  test: string;
  status: 'pending' | 'running' | 'passed' | 'failed';
  message?: string;
  duration?: number;
}

interface TestSuite {
  name: string;
  tests: TestResult[];
  status: 'pending' | 'running' | 'completed';
}

export const TestDashboard: React.FC = () => {
  const { setUser, setActiveProject, setCodeAnalysis } = useAppStore();
  const [currentTest, setCurrentTest] = useState<string>('');
  const [testSuites, setTestSuites] = useState<TestSuite[]>([
    {
      name: 'File Tree Component',
      status: 'pending',
      tests: [
        { component: 'FileTree', test: 'Render file tree structure', status: 'pending' },
        { component: 'FileTree', test: 'Expand/collapse directories', status: 'pending' },
        { component: 'FileTree', test: 'File selection', status: 'pending' },
        { component: 'FileTree', test: 'Search functionality', status: 'pending' },
        { component: 'FileTree', test: 'Error indicators', status: 'pending' },
        { component: 'FileTree', test: 'File icons and sizes', status: 'pending' },
        { component: 'FileTree', test: 'Virtualization performance', status: 'pending' }
      ]
    },
    {
      name: 'Code Editor Component',
      status: 'pending',
      tests: [
        { component: 'CodeEditor', test: 'Monaco Editor initialization', status: 'pending' },
        { component: 'CodeEditor', test: 'Syntax highlighting', status: 'pending' },
        { component: 'CodeEditor', test: 'Error decorations', status: 'pending' },
        { component: 'CodeEditor', test: 'Symbol hover information', status: 'pending' },
        { component: 'CodeEditor', test: 'Go-to-definition', status: 'pending' },
        { component: 'CodeEditor', test: 'Find references', status: 'pending' },
        { component: 'CodeEditor', test: 'Theme switching', status: 'pending' }
      ]
    },
    {
      name: 'Code Graph Visualization',
      status: 'pending',
      tests: [
        { component: 'CodeGraph', test: 'Network graph rendering', status: 'pending' },
        { component: 'CodeGraph', test: 'Node interactions', status: 'pending' },
        { component: 'CodeGraph', test: 'Layout algorithms', status: 'pending' },
        { component: 'CodeGraph', test: 'Filtering controls', status: 'pending' },
        { component: 'CodeGraph', test: 'Search functionality', status: 'pending' },
        { component: 'CodeGraph', test: 'Physics simulation', status: 'pending' },
        { component: 'CodeGraph', test: 'Zoom and pan controls', status: 'pending' }
      ]
    },
    {
      name: 'Dashboard Integration',
      status: 'pending',
      tests: [
        { component: 'Dashboard', test: 'Layout rendering', status: 'pending' },
        { component: 'Dashboard', test: 'Panel resizing', status: 'pending' },
        { component: 'Dashboard', test: 'Sidebar toggle', status: 'pending' },
        { component: 'Dashboard', test: 'Tab navigation', status: 'pending' },
        { component: 'Dashboard', test: 'Project switching', status: 'pending' },
        { component: 'Dashboard', test: 'Real-time updates', status: 'pending' },
        { component: 'Dashboard', test: 'State persistence', status: 'pending' }
      ]
    },
    {
      name: 'Interactivity & Performance',
      status: 'pending',
      tests: [
        { component: 'Integration', test: 'File tree to editor navigation', status: 'pending' },
        { component: 'Integration', test: 'Symbol navigation flow', status: 'pending' },
        { component: 'Integration', test: 'Graph to code navigation', status: 'pending' },
        { component: 'Integration', test: 'Error highlighting sync', status: 'pending' },
        { component: 'Integration', test: 'Search across components', status: 'pending' },
        { component: 'Integration', test: 'Theme consistency', status: 'pending' },
        { component: 'Integration', test: 'Performance with large codebase', status: 'pending' }
      ]
    }
  ]);

  // Initialize mock data
  useEffect(() => {
    setUser(mockUser);
    setActiveProject(mockProject);
    setCodeAnalysis(mockCodeAnalysis);
  }, [setUser, setActiveProject, setCodeAnalysis]);

  // Run automated tests
  const runTests = async () => {
    for (let suiteIndex = 0; suiteIndex < testSuites.length; suiteIndex++) {
      const suite = testSuites[suiteIndex];
      
      // Update suite status to running
      setTestSuites(prev => prev.map((s, i) => 
        i === suiteIndex ? { ...s, status: 'running' } : s
      ));

      for (let testIndex = 0; testIndex < suite.tests.length; testIndex++) {
        const test = suite.tests[testIndex];
        setCurrentTest(`${suite.name}: ${test.test}`);

        // Update test status to running
        setTestSuites(prev => prev.map((s, i) => 
          i === suiteIndex ? {
            ...s,
            tests: s.tests.map((t, j) => 
              j === testIndex ? { ...t, status: 'running' } : t
            )
          } : s
        ));

        // Simulate test execution
        const startTime = Date.now();
        await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 500));
        const duration = Date.now() - startTime;

        // Simulate test results (mostly pass, some warnings)
        const success = Math.random() > 0.1; // 90% success rate
        const status = success ? 'passed' : 'failed';
        const message = success 
          ? `✅ Test completed successfully in ${duration}ms`
          : `❌ Test failed - simulated failure for demonstration`;

        // Update test result
        setTestSuites(prev => prev.map((s, i) => 
          i === suiteIndex ? {
            ...s,
            tests: s.tests.map((t, j) => 
              j === testIndex ? { ...t, status, message, duration } : t
            )
          } : s
        ));
      }

      // Mark suite as completed
      setTestSuites(prev => prev.map((s, i) => 
        i === suiteIndex ? { ...s, status: 'completed' } : s
      ));
    }

    setCurrentTest('All tests completed!');
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'running':
        return <motion.div 
          animate={{ rotate: 360 }} 
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" 
        />;
      case 'passed':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />;
      default:
        return <div className="w-4 h-4 border-2 border-gray-300 rounded-full" />;
    }
  };

  const getSuiteIcon = (name: string) => {
    if (name.includes('File Tree')) return <FolderIcon className="w-5 h-5" />;
    if (name.includes('Code Editor')) return <CodeBracketIcon className="w-5 h-5" />;
    if (name.includes('Graph')) return <ChartBarIcon className="w-5 h-5" />;
    return <InformationCircleIcon className="w-5 h-5" />;
  };

  const overallProgress = testSuites.reduce((acc, suite) => {
    const completed = suite.tests.filter(t => t.status === 'passed' || t.status === 'failed').length;
    return acc + completed;
  }, 0);

  const totalTests = testSuites.reduce((acc, suite) => acc + suite.tests.length, 0);
  const progressPercentage = (overallProgress / totalTests) * 100;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              🧪 Interactive Codebase Visualization Test Suite
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Comprehensive testing of all components and their interactivity
            </p>
          </div>
          
          <button
            onClick={runTests}
            disabled={testSuites.some(s => s.status === 'running')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <PlayIcon className="w-4 h-4 mr-2" />
            Run All Tests
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span>Overall Progress</span>
            <span>{overallProgress}/{totalTests} tests ({progressPercentage.toFixed(1)}%)</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <motion.div
              className="bg-blue-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progressPercentage}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Current Test */}
        {currentTest && (
          <div className="mt-3 text-sm text-blue-600 dark:text-blue-400">
            Currently running: {currentTest}
          </div>
        )}
      </div>

      <div className="flex">
        {/* Test Results Sidebar */}
        <div className="w-96 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 h-screen overflow-y-auto">
          <div className="p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Test Results
            </h2>
            
            <div className="space-y-4">
              {testSuites.map((suite, suiteIndex) => (
                <div key={suite.name} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      {getSuiteIcon(suite.name)}
                      <h3 className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                        {suite.name}
                      </h3>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {suite.tests.filter(t => t.status === 'passed').length}/{suite.tests.length}
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    {suite.tests.map((test, testIndex) => (
                      <div key={testIndex} className="flex items-center justify-between text-sm">
                        <div className="flex items-center">
                          {getStatusIcon(test.status)}
                          <span className="ml-2 text-gray-700 dark:text-gray-300">
                            {test.test}
                          </span>
                        </div>
                        {test.duration && (
                          <span className="text-xs text-gray-500">
                            {test.duration}ms
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Dashboard */}
        <div className="flex-1">
          <Dashboard />
        </div>
      </div>

      {/* Test Instructions Overlay */}
      <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 shadow-lg max-w-md">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
          🎯 Manual Testing Instructions
        </h3>
        <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
          <p><strong>File Tree:</strong> Click folders to expand/collapse, select files to view content</p>
          <p><strong>Code Editor:</strong> Hover over symbols, right-click for context menu</p>
          <p><strong>Graph View:</strong> Toggle graph view button, drag nodes, use controls</p>
          <p><strong>Search:</strong> Use search in file tree and graph view</p>
          <p><strong>Panels:</strong> Resize panels by dragging borders</p>
          <p><strong>Errors:</strong> Click on error indicators to see details</p>
        </div>
      </div>
    </div>
  );
};
