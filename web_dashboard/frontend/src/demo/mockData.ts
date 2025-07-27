import { 
  Project, 
  CodeAnalysis, 
  FileNode, 
  Symbol, 
  CodeError, 
  Dependency,
  CodeMetrics,
  User
} from '@/types';

// Mock user data
export const mockUser: User = {
  id: 'user-1',
  email: 'developer@example.com',
  name: 'John Developer',
  avatar: 'https://avatars.githubusercontent.com/u/1?v=4',
  preferences: {
    theme: 'dark',
    editor: {
      font_size: 14,
      font_family: 'JetBrains Mono',
      tab_size: 2,
      word_wrap: true,
      minimap: true,
      line_numbers: true
    },
    ui: {
      sidebar_width: 300,
      panel_height: 200,
      show_activity_bar: true,
      show_status_bar: true
    }
  }
};

// Mock project data
export const mockProject: Project = {
  id: 'project-1',
  name: 'Web Dashboard',
  description: 'Interactive codebase visualization dashboard',
  github_owner: 'example-org',
  github_repo: 'web-dashboard',
  webhook_url: 'https://api.example.com/webhooks/github',
  webhook_id: 'webhook-123',
  status: 'active',
  settings: {
    repository_rules: 'Follow TypeScript best practices',
    setup_commands: 'npm install\nnpm run build',
    planning_statement: 'Build a comprehensive codebase visualization tool',
    auto_confirm_plan: false,
    auto_merge_validated_pr: false,
    branch: 'main',
    secrets: {}
  },
  user_id: 'user-1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T12:00:00Z',
  last_activity: '2024-01-15T12:00:00Z'
};

// Mock code errors
export const mockErrors: CodeError[] = [
  {
    file_path: 'src/components/Dashboard/Dashboard.tsx',
    line: 45,
    column: 12,
    severity: 'error',
    message: 'Property "invalidProp" does not exist on type "DashboardProps"',
    rule: 'typescript-error',
    source: 'typescript'
  },
  {
    file_path: 'src/components/FileTree/FileTree.tsx',
    line: 123,
    column: 8,
    severity: 'warning',
    message: 'React Hook useEffect has a missing dependency: "searchQuery"',
    rule: 'react-hooks/exhaustive-deps',
    source: 'eslint'
  },
  {
    file_path: 'src/utils/fileUtils.ts',
    line: 67,
    column: 15,
    severity: 'info',
    message: 'Consider using const assertion for this array',
    rule: 'prefer-const-assertion',
    source: 'eslint'
  },
  {
    file_path: 'src/store/index.ts',
    line: 234,
    column: 20,
    severity: 'warning',
    message: 'Unused variable "oldState"',
    rule: 'no-unused-vars',
    source: 'eslint'
  }
];

// Mock symbols
export const mockSymbols: Symbol[] = [
  {
    name: 'Dashboard',
    kind: 'function',
    location: {
      file_path: 'src/components/Dashboard/Dashboard.tsx',
      line: 35,
      column: 17,
      end_line: 35,
      end_column: 26
    },
    definition: {
      file_path: 'src/components/Dashboard/Dashboard.tsx',
      line: 35,
      column: 17,
      end_line: 35,
      end_column: 26
    },
    references: [
      {
        file_path: 'src/App.tsx',
        line: 12,
        column: 25,
        end_line: 12,
        end_column: 34
      },
      {
        file_path: 'src/components/index.ts',
        line: 3,
        column: 9,
        end_line: 3,
        end_column: 18
      }
    ],
    documentation: 'Main dashboard component that provides the IDE-like interface',
    signature: 'const Dashboard: React.FC<DashboardProps>',
    parent: undefined,
    children: []
  },
  {
    name: 'FileTree',
    kind: 'function',
    location: {
      file_path: 'src/components/FileTree/FileTree.tsx',
      line: 25,
      column: 17,
      end_line: 25,
      end_column: 25
    },
    definition: {
      file_path: 'src/components/FileTree/FileTree.tsx',
      line: 25,
      column: 17,
      end_line: 25,
      end_column: 25
    },
    references: [
      {
        file_path: 'src/components/Dashboard/Dashboard.tsx',
        line: 98,
        column: 12,
        end_line: 98,
        end_column: 20
      }
    ],
    documentation: 'Interactive file tree component with search and virtualization',
    signature: 'const FileTree: React.FC<FileTreeProps>',
    parent: undefined,
    children: []
  },
  {
    name: 'CodeEditor',
    kind: 'function',
    location: {
      file_path: 'src/components/CodeEditor/CodeEditor.tsx',
      line: 39,
      column: 17,
      end_line: 39,
      end_column: 27
    },
    definition: {
      file_path: 'src/components/CodeEditor/CodeEditor.tsx',
      line: 39,
      column: 17,
      end_line: 39,
      end_column: 27
    },
    references: [
      {
        file_path: 'src/components/Dashboard/Dashboard.tsx',
        line: 245,
        column: 20,
        end_line: 245,
        end_column: 30
      }
    ],
    documentation: 'Monaco-based code editor with symbol intelligence',
    signature: 'const CodeEditor: React.FC<CodeEditorProps>',
    parent: undefined,
    children: []
  },
  {
    name: 'useAppStore',
    kind: 'function',
    location: {
      file_path: 'src/store/index.ts',
      line: 89,
      column: 21,
      end_line: 89,
      end_column: 32
    },
    definition: {
      file_path: 'src/store/index.ts',
      line: 89,
      column: 21,
      end_line: 89,
      end_column: 32
    },
    references: [
      {
        file_path: 'src/store/index.ts',
        line: 315,
        column: 32,
        end_line: 315,
        end_column: 43
      },
      {
        file_path: 'src/components/Dashboard/Dashboard.tsx',
        line: 18,
        column: 8,
        end_line: 18,
        end_column: 19
      }
    ],
    documentation: 'Main Zustand store for application state management',
    signature: 'const useAppStore: UseBoundStore<StoreApi<AppStore>>',
    parent: undefined,
    children: []
  }
];

// Mock file tree
export const mockFileTree: FileNode = {
  name: 'web-dashboard',
  path: '/',
  type: 'directory',
  children: [
    {
      name: 'src',
      path: '/src',
      type: 'directory',
      errors: [],
      has_errors: true,
      is_expanded: true,
      children: [
        {
          name: 'components',
          path: '/src/components',
          type: 'directory',
          errors: [],
          has_errors: true,
          is_expanded: true,
          children: [
            {
              name: 'Dashboard',
              path: '/src/components/Dashboard',
              type: 'directory',
              errors: [],
              has_errors: true,
              is_expanded: true,
              children: [
                {
                  name: 'Dashboard.tsx',
                  path: '/src/components/Dashboard/Dashboard.tsx',
                  type: 'file',
                  size: 15420,
                  errors: mockErrors.filter(e => e.file_path === 'src/components/Dashboard/Dashboard.tsx'),
                  has_errors: true,
                  language: 'typescript',
                  extension: 'tsx',
                  is_selected: false
                },
                {
                  name: 'index.ts',
                  path: '/src/components/Dashboard/index.ts',
                  type: 'file',
                  size: 156,
                  errors: [],
                  has_errors: false,
                  language: 'typescript',
                  extension: 'ts',
                  is_selected: false
                }
              ]
            },
            {
              name: 'FileTree',
              path: '/src/components/FileTree',
              type: 'directory',
              errors: [],
              has_errors: true,
              is_expanded: true,
              children: [
                {
                  name: 'FileTree.tsx',
                  path: '/src/components/FileTree/FileTree.tsx',
                  type: 'file',
                  size: 12890,
                  errors: mockErrors.filter(e => e.file_path === 'src/components/FileTree/FileTree.tsx'),
                  has_errors: true,
                  language: 'typescript',
                  extension: 'tsx',
                  is_selected: false
                }
              ]
            },
            {
              name: 'CodeEditor',
              path: '/src/components/CodeEditor',
              type: 'directory',
              errors: [],
              has_errors: false,
              is_expanded: true,
              children: [
                {
                  name: 'CodeEditor.tsx',
                  path: '/src/components/CodeEditor/CodeEditor.tsx',
                  type: 'file',
                  size: 18750,
                  errors: [],
                  has_errors: false,
                  language: 'typescript',
                  extension: 'tsx',
                  is_selected: false
                }
              ]
            },
            {
              name: 'CodeGraph',
              path: '/src/components/CodeGraph',
              type: 'directory',
              errors: [],
              has_errors: false,
              is_expanded: false,
              children: [
                {
                  name: 'CodeGraph.tsx',
                  path: '/src/components/CodeGraph/CodeGraph.tsx',
                  type: 'file',
                  size: 22340,
                  errors: [],
                  has_errors: false,
                  language: 'typescript',
                  extension: 'tsx',
                  is_selected: false
                }
              ]
            }
          ]
        },
        {
          name: 'store',
          path: '/src/store',
          type: 'directory',
          errors: [],
          has_errors: true,
          is_expanded: true,
          children: [
            {
              name: 'index.ts',
              path: '/src/store/index.ts',
              type: 'file',
              size: 9876,
              errors: mockErrors.filter(e => e.file_path === 'src/store/index.ts'),
              has_errors: true,
              language: 'typescript',
              extension: 'ts',
              is_selected: false
            }
          ]
        },
        {
          name: 'utils',
          path: '/src/utils',
          type: 'directory',
          errors: [],
          has_errors: true,
          is_expanded: true,
          children: [
            {
              name: 'fileUtils.ts',
              path: '/src/utils/fileUtils.ts',
              type: 'file',
              size: 8234,
              errors: mockErrors.filter(e => e.file_path === 'src/utils/fileUtils.ts'),
              has_errors: true,
              language: 'typescript',
              extension: 'ts',
              is_selected: false
            }
          ]
        },
        {
          name: 'types',
          path: '/src/types',
          type: 'directory',
          errors: [],
          has_errors: false,
          is_expanded: false,
          children: [
            {
              name: 'index.ts',
              path: '/src/types/index.ts',
              type: 'file',
              size: 15670,
              errors: [],
              has_errors: false,
              language: 'typescript',
              extension: 'ts',
              is_selected: false
            }
          ]
        },
        {
          name: 'App.tsx',
          path: '/src/App.tsx',
          type: 'file',
          size: 3456,
          errors: [],
          has_errors: false,
          language: 'typescript',
          extension: 'tsx',
          is_selected: false
        },
        {
          name: 'main.tsx',
          path: '/src/main.tsx',
          type: 'file',
          size: 567,
          errors: [],
          has_errors: false,
          language: 'typescript',
          extension: 'tsx',
          is_selected: false
        }
      ],
      errors: [],
      has_errors: true,
      is_expanded: true
    },
    {
      name: 'public',
      path: '/public',
      type: 'directory',
      errors: [],
      has_errors: false,
      is_expanded: false,
      children: [
        {
          name: 'index.html',
          path: '/public/index.html',
          type: 'file',
          size: 1234,
          errors: [],
          has_errors: false,
          language: 'html',
          extension: 'html',
          is_selected: false
        },
        {
          name: 'favicon.ico',
          path: '/public/favicon.ico',
          type: 'file',
          size: 15086,
          errors: [],
          has_errors: false,
          language: 'binary',
          extension: 'ico',
          is_selected: false
        }
      ]
    },
    {
      name: 'package.json',
      path: '/package.json',
      type: 'file',
      size: 2345,
      errors: [],
      has_errors: false,
      language: 'json',
      extension: 'json',
      is_selected: false
    },
    {
      name: 'tsconfig.json',
      path: '/tsconfig.json',
      type: 'file',
      size: 890,
      errors: [],
      has_errors: false,
      language: 'json',
      extension: 'json',
      is_selected: false
    },
    {
      name: 'vite.config.ts',
      path: '/vite.config.ts',
      type: 'file',
      size: 1567,
      errors: [],
      has_errors: false,
      language: 'typescript',
      extension: 'ts',
      is_selected: false
    },
    {
      name: 'README.md',
      path: '/README.md',
      type: 'file',
      size: 4567,
      errors: [],
      has_errors: false,
      language: 'markdown',
      extension: 'md',
      is_selected: false
    }
  ],
  errors: [],
  has_errors: true,
  is_expanded: true
};

// Mock dependencies
export const mockDependencies: Dependency[] = [
  {
    name: 'react',
    version: '18.2.0',
    type: 'production',
    source: 'npm',
    vulnerabilities: []
  },
  {
    name: 'react-dom',
    version: '18.2.0',
    type: 'production',
    source: 'npm',
    vulnerabilities: []
  },
  {
    name: '@monaco-editor/react',
    version: '4.4.6',
    type: 'production',
    source: 'npm',
    vulnerabilities: []
  },
  {
    name: 'vis-network',
    version: '9.1.6',
    type: 'production',
    source: 'npm',
    vulnerabilities: []
  },
  {
    name: 'zustand',
    version: '4.3.2',
    type: 'production',
    source: 'npm',
    vulnerabilities: []
  },
  {
    name: 'framer-motion',
    version: '9.0.0',
    type: 'production',
    source: 'npm',
    vulnerabilities: []
  },
  {
    name: 'tailwindcss',
    version: '3.2.4',
    type: 'development',
    source: 'npm',
    vulnerabilities: []
  },
  {
    name: 'typescript',
    version: '4.9.4',
    type: 'development',
    source: 'npm',
    vulnerabilities: []
  },
  {
    name: 'vite',
    version: '4.1.0',
    type: 'development',
    source: 'npm',
    vulnerabilities: []
  },
  {
    name: 'lodash',
    version: '4.17.20',
    type: 'production',
    source: 'npm',
    vulnerabilities: [
      {
        id: 'CVE-2021-23337',
        severity: 'high',
        title: 'Command Injection in lodash',
        description: 'lodash versions prior to 4.17.21 are vulnerable to Command Injection via the template function.',
        patched_versions: ['>=4.17.21'],
        recommendation: 'Upgrade to version 4.17.21 or later'
      }
    ]
  }
];

// Mock code metrics
export const mockCodeMetrics: CodeMetrics = {
  lines_of_code: 15420,
  complexity: 3.2,
  maintainability_index: 78.5,
  test_coverage: 85.2,
  duplication_ratio: 2.1,
  technical_debt_ratio: 5.8
};

// Mock code analysis
export const mockCodeAnalysis: CodeAnalysis = {
  project_id: 'project-1',
  total_files: 25,
  files_with_errors: 4,
  total_errors: 4,
  errors_by_severity: {
    error: 1,
    warning: 2,
    info: 1
  },
  errors_by_type: {
    typescript: 1,
    eslint: 3
  },
  file_tree: mockFileTree,
  symbols: mockSymbols,
  dependencies: mockDependencies,
  metrics: mockCodeMetrics,
  analysis_duration: 2.34,
  analyzed_at: '2024-01-15T12:00:00Z'
};

// Mock file content
export const mockFileContent: Record<string, string> = {
  '/src/components/Dashboard/Dashboard.tsx': `import React, { useState, useEffect, useCallback } from 'react';
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

  // This line has an error - invalidProp doesn't exist
  const invalidUsage = className.invalidProp;

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Dashboard content */}
    </div>
  );
};`,

  '/src/components/FileTree/FileTree.tsx': `import React, { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronRightIcon, 
  ChevronDownIcon,
  DocumentIcon,
  FolderIcon,
  FolderOpenIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { FileNode, CodeError } from '@/types';
import { useFileTree, useFileActions, useSelectedFile } from '@/store';

interface FileTreeProps {
  className?: string;
  onFileSelect?: (filePath: string) => void;
  onFileDoubleClick?: (filePath: string) => void;
  showSearch?: boolean;
}

export const FileTree: React.FC<FileTreeProps> = ({
  className,
  onFileSelect,
  onFileDoubleClick,
  showSearch = true
}) => {
  const fileTree = useFileTree();
  const selectedFile = useSelectedFile();
  const { expandFileNode, collapseFileNode, selectFileNode } = useFileActions();
  const [searchQuery, setSearchQuery] = useState('');

  // This useEffect is missing searchQuery in dependencies
  useEffect(() => {
    // Some effect logic here
  }, [fileTree]);

  return (
    <div className="flex flex-col h-full">
      {/* File tree content */}
    </div>
  );
};`,

  '/src/utils/fileUtils.ts': `import React from 'react';
import { DocumentIcon, CodeBracketIcon } from '@heroicons/react/24/outline';

export function getLanguageFromExtension(filePath: string): string {
  const extension = filePath.split('.').pop()?.toLowerCase();
  
  const languageMap: Record<string, string> = {
    'js': 'javascript',
    'jsx': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'py': 'python',
    'html': 'html',
    'css': 'css'
  };
  
  // This could use const assertion
  const supportedLanguages = ['javascript', 'typescript', 'python'];
  
  return languageMap[extension || ''] || 'plaintext';
}

export function getFileIcon(fileName: string): React.ReactElement {
  const extension = fileName.split('.').pop()?.toLowerCase() || '';
  
  switch (extension) {
    case 'js':
    case 'jsx':
    case 'ts':
    case 'tsx':
      return <CodeBracketIcon className="w-4 h-4 text-yellow-500" />;
    default:
      return <DocumentIcon className="w-4 h-4 text-gray-500" />;
  }
}`,

  '/src/store/index.ts': `import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { 
  AppState, 
  Project, 
  ViewState, 
  SearchState, 
  CodeAnalysis, 
  User
} from '@/types';

interface AppStore extends AppState {
  setUser: (user: User | null) => void;
  setProjects: (projects: Project[]) => void;
  setActiveProject: (project: Project | null) => void;
  setCodeAnalysis: (analysis: CodeAnalysis | null) => void;
}

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      immer((set, get) => ({
        user: null,
        projects: [],
        activeProject: null,
        viewState: {
          activeTab: 'explorer',
          sidebarWidth: 300,
          editorWidth: 800,
          bottomPanelHeight: 200,
          showMinimap: true,
          showLineNumbers: true,
          wordWrap: false,
          theme: 'dark'
        },
        searchState: {
          query: '',
          results: [],
          isSearching: false,
          filters: {
            file_types: [],
            include_patterns: [],
            exclude_patterns: [],
            case_sensitive: false,
            whole_word: false,
            regex: false
          }
        },
        codeAnalysis: null,
        isLoading: false,
        error: null,
        
        setUser: (user) => set((state) => {
          state.user = user;
        }),
        
        setProjects: (projects) => set((state) => {
          const oldState = state.projects; // This variable is unused
          state.projects = projects;
        }),
        
        setActiveProject: (project) => set((state) => {
          state.activeProject = project;
        }),
        
        setCodeAnalysis: (analysis) => set((state) => {
          state.codeAnalysis = analysis;
        })
      })),
      { name: 'web-eval-agent-store' }
    ),
    { name: 'web-eval-agent-store' }
  )
);`
};

// Export all mock data
export {
  mockUser,
  mockProject,
  mockErrors,
  mockSymbols,
  mockFileTree,
  mockDependencies,
  mockCodeMetrics,
  mockCodeAnalysis,
  mockFileContent
};
