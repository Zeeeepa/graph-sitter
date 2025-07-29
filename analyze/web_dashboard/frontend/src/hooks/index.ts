import { useQuery } from '@tanstack/react-query';
import { mockFileContent } from '@/demo/mockData';

// Mock hook for file content
export const useFileContent = (projectId?: string, filePath?: string) => {
  return useQuery({
    queryKey: ['fileContent', projectId, filePath],
    queryFn: async () => {
      if (!filePath) return null;
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // Return mock content or default
      return mockFileContent[filePath] || `// File content for ${filePath}\n// This is mock content for demonstration\n\nconst example = "Hello World";\nconsole.log(example);`;
    },
    enabled: !!projectId && !!filePath
  });
};

// Mock hook for code analysis
export const useCodeAnalysisQuery = (projectId?: string) => {
  return useQuery({
    queryKey: ['codeAnalysis', projectId],
    queryFn: async () => {
      if (!projectId) return null;
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Return mock analysis data
      const { mockCodeAnalysis } = await import('@/demo/mockData');
      return mockCodeAnalysis;
    },
    enabled: !!projectId
  });
};
