import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { 
  AppState, 
  Project, 
  ViewState, 
  SearchState, 
  CodeAnalysis, 
  User, 
  FileNode,
  Symbol,
  SearchResult,
  EditorState
} from '@/types';

interface AppStore extends AppState {
  // Actions
  setUser: (user: User | null) => void;
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
  removeProject: (id: string) => void;
  setActiveProject: (project: Project | null) => void;
  setCodeAnalysis: (analysis: CodeAnalysis | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // View State Actions
  setActiveTab: (tab: ViewState['activeTab']) => void;
  setSelectedFile: (filePath: string | null) => void;
  setSidebarWidth: (width: number) => void;
  setEditorWidth: (width: number) => void;
  setBottomPanelHeight: (height: number) => void;
  toggleMinimap: () => void;
  toggleLineNumbers: () => void;
  toggleWordWrap: () => void;
  setTheme: (theme: ViewState['theme']) => void;
  
  // Search Actions
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: SearchResult[]) => void;
  setSearching: (searching: boolean) => void;
  setSelectedSearchResult: (result: SearchResult | null) => void;
  updateSearchFilters: (filters: Partial<SearchState['filters']>) => void;
  
  // File Tree Actions
  expandFileNode: (path: string) => void;
  collapseFileNode: (path: string) => void;
  selectFileNode: (path: string) => void;
  
  // Editor Actions
  openFile: (filePath: string, content?: string) => void;
  closeFile: (filePath: string) => void;
  updateFileContent: (filePath: string, content: string) => void;
  markFileDirty: (filePath: string, dirty: boolean) => void;
  
  // Symbol Navigation
  goToSymbol: (symbol: Symbol) => void;
  goToDefinition: (filePath: string, line: number, column: number) => void;
  findReferences: (filePath: string, line: number, column: number) => void;
}

const initialViewState: ViewState = {
  activeTab: 'explorer',
  sidebarWidth: 300,
  editorWidth: 800,
  bottomPanelHeight: 200,
  showMinimap: true,
  showLineNumbers: true,
  wordWrap: false,
  theme: 'dark'
};

const initialSearchState: SearchState = {
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
};

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      immer((set) => ({
        // Initial State
        user: null,
        projects: [],
        activeProject: null,
        viewState: initialViewState,
        searchState: initialSearchState,
        codeAnalysis: null,
        isLoading: false,
        error: null,
        
        // User Actions
        setUser: (user) => set((state) => {
          state.user = user;
        }),
        
        // Project Actions
        setProjects: (projects) => set((state) => {
          state.projects = projects;
        }),
        
        addProject: (project) => set((state) => {
          state.projects.push(project);
        }),
        
        updateProject: (id, updates) => set((state) => {
          const index = state.projects.findIndex(p => p.id === id);
          if (index !== -1) {
            Object.assign(state.projects[index], updates);
          }
          if (state.activeProject?.id === id) {
            Object.assign(state.activeProject, updates);
          }
        }),
        
        removeProject: (id) => set((state) => {
          state.projects = state.projects.filter(p => p.id !== id);
          if (state.activeProject?.id === id) {
            state.activeProject = null;
          }
        }),
        
        setActiveProject: (project) => set((state) => {
          state.activeProject = project;
          if (project) {
            state.viewState.activeProject = project.id;
          }
        }),
        
        setCodeAnalysis: (analysis) => set((state) => {
          state.codeAnalysis = analysis;
        }),
        
        setLoading: (loading) => set((state) => {
          state.isLoading = loading;
        }),
        
        setError: (error) => set((state) => {
          state.error = error;
        }),
        
        // View State Actions
        setActiveTab: (tab) => set((state) => {
          state.viewState.activeTab = tab;
        }),
        
        setSelectedFile: (filePath) => set((state) => {
          state.viewState.selectedFile = filePath || undefined;
        }),
        
        setSidebarWidth: (width) => set((state) => {
          state.viewState.sidebarWidth = width;
        }),
        
        setEditorWidth: (width) => set((state) => {
          state.viewState.editorWidth = width;
        }),
        
        setBottomPanelHeight: (height) => set((state) => {
          state.viewState.bottomPanelHeight = height;
        }),
        
        toggleMinimap: () => set((state) => {
          state.viewState.showMinimap = !state.viewState.showMinimap;
        }),
        
        toggleLineNumbers: () => set((state) => {
          state.viewState.showLineNumbers = !state.viewState.showLineNumbers;
        }),
        
        toggleWordWrap: () => set((state) => {
          state.viewState.wordWrap = !state.viewState.wordWrap;
        }),
        
        setTheme: (theme) => set((state) => {
          state.viewState.theme = theme;
        }),
        
        // Search Actions
        setSearchQuery: (query) => set((state) => {
          state.searchState.query = query;
        }),
        
        setSearchResults: (results) => set((state) => {
          state.searchState.results = results;
        }),
        
        setSearching: (searching) => set((state) => {
          state.searchState.isSearching = searching;
        }),
        
        setSelectedSearchResult: (result) => set((state) => {
          state.searchState.selectedResult = result || undefined;
        }),
        
        updateSearchFilters: (filters) => set((state) => {
          Object.assign(state.searchState.filters, filters);
        }),
        
        // File Tree Actions
        expandFileNode: (path) => set((state) => {
          const updateNode = (node: FileNode): FileNode => {
            if (node.path === path) {
              return { ...node, is_expanded: true };
            }
            if (node.children) {
              return {
                ...node,
                children: node.children.map(updateNode)
              };
            }
            return node;
          };
          
          if (state.codeAnalysis?.file_tree) {
            state.codeAnalysis.file_tree = updateNode(state.codeAnalysis.file_tree);
          }
        }),
        
        collapseFileNode: (path) => set((state) => {
          const updateNode = (node: FileNode): FileNode => {
            if (node.path === path) {
              return { ...node, is_expanded: false };
            }
            if (node.children) {
              return {
                ...node,
                children: node.children.map(updateNode)
              };
            }
            return node;
          };
          
          if (state.codeAnalysis?.file_tree) {
            state.codeAnalysis.file_tree = updateNode(state.codeAnalysis.file_tree);
          }
        }),
        
        selectFileNode: (path) => set((state) => {
          const updateNode = (node: FileNode): FileNode => {
            return {
              ...node,
              is_selected: node.path === path,
              children: node.children?.map(updateNode)
            };
          };
          
          if (state.codeAnalysis?.file_tree) {
            state.codeAnalysis.file_tree = updateNode(state.codeAnalysis.file_tree);
          }
          state.viewState.selectedFile = path;
        }),
        
        // Editor Actions
        openFile: (filePath, content) => set((state) => {
          // Implementation would depend on editor state management
          state.viewState.selectedFile = filePath;
        }),
        
        closeFile: (filePath) => set((state) => {
          if (state.viewState.selectedFile === filePath) {
            state.viewState.selectedFile = undefined;
          }
        }),
        
        updateFileContent: (filePath, content) => set((state) => {
          // Implementation would depend on editor state management
        }),
        
        markFileDirty: (filePath, dirty) => set((state) => {
          // Implementation would depend on editor state management
        }),
        
        // Symbol Navigation
        goToSymbol: (symbol) => set((state) => {
          state.viewState.selectedFile = symbol.location.file_path;
          // Additional logic to navigate to specific line/column
        }),
        
        goToDefinition: (filePath, line, column) => set((state) => {
          // Implementation would involve API call to get definition location
        }),
        
        findReferences: (filePath, line, column) => set((state) => {
          // Implementation would involve API call to find references
        })
      })),
      {
        name: 'web-eval-agent-store',
        partialize: (state) => ({
          user: state.user,
          viewState: state.viewState,
          searchState: {
            ...state.searchState,
            results: [], // Don't persist search results
            isSearching: false
          }
        })
      }
    ),
    {
      name: 'web-eval-agent-store'
    }
  )
);

// Selectors
export const useUser = () => useAppStore((state) => state.user);
export const useProjects = () => useAppStore((state) => state.projects);
export const useActiveProject = () => useAppStore((state) => state.activeProject);
export const useViewState = () => useAppStore((state) => state.viewState);
export const useSearchState = () => useAppStore((state) => state.searchState);
export const useCodeAnalysis = () => useAppStore((state) => state.codeAnalysis);
export const useIsLoading = () => useAppStore((state) => state.isLoading);
export const useError = () => useAppStore((state) => state.error);

// Computed selectors
export const useSelectedFile = () => useAppStore((state) => state.viewState.selectedFile);
export const useActiveTab = () => useAppStore((state) => state.viewState.activeTab);
export const useTheme = () => useAppStore((state) => state.viewState.theme);

export const useFileTree = () => useAppStore((state) => state.codeAnalysis?.file_tree);
export const useSymbols = () => useAppStore((state) => state.codeAnalysis?.symbols || []);
export const useDependencies = () => useAppStore((state) => state.codeAnalysis?.dependencies || []);
export const useCodeMetrics = () => useAppStore((state) => state.codeAnalysis?.metrics);

export const useSearchResults = () => useAppStore((state) => state.searchState.results);
export const useIsSearching = () => useAppStore((state) => state.searchState.isSearching);
export const useSearchQuery = () => useAppStore((state) => state.searchState.query);

// Action selectors
export const useAppActions = () => useAppStore((state) => ({
  setUser: state.setUser,
  setProjects: state.setProjects,
  addProject: state.addProject,
  updateProject: state.updateProject,
  removeProject: state.removeProject,
  setActiveProject: state.setActiveProject,
  setCodeAnalysis: state.setCodeAnalysis,
  setLoading: state.setLoading,
  setError: state.setError
}));

export const useViewActions = () => useAppStore((state) => ({
  setActiveTab: state.setActiveTab,
  setSelectedFile: state.setSelectedFile,
  setSidebarWidth: state.setSidebarWidth,
  setEditorWidth: state.setEditorWidth,
  setBottomPanelHeight: state.setBottomPanelHeight,
  toggleMinimap: state.toggleMinimap,
  toggleLineNumbers: state.toggleLineNumbers,
  toggleWordWrap: state.toggleWordWrap,
  setTheme: state.setTheme
}));

export const useSearchActions = () => useAppStore((state) => ({
  setSearchQuery: state.setSearchQuery,
  setSearchResults: state.setSearchResults,
  setSearching: state.setSearching,
  setSelectedSearchResult: state.setSelectedSearchResult,
  updateSearchFilters: state.updateSearchFilters
}));

export const useFileActions = () => useAppStore((state) => ({
  expandFileNode: state.expandFileNode,
  collapseFileNode: state.collapseFileNode,
  selectFileNode: state.selectFileNode,
  openFile: state.openFile,
  closeFile: state.closeFile,
  updateFileContent: state.updateFileContent,
  markFileDirty: state.markFileDirty
}));

export const useNavigationActions = () => useAppStore((state) => ({
  goToSymbol: state.goToSymbol,
  goToDefinition: state.goToDefinition,
  findReferences: state.findReferences
}));
