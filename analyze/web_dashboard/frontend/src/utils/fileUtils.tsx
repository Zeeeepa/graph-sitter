import React from 'react';
import {
  DocumentIcon,
  CodeBracketIcon,
  PhotoIcon,
  FilmIcon,
  MusicalNoteIcon,
  ArchiveBoxIcon,
  DocumentTextIcon,
  CogIcon,
  CubeIcon,
  CommandLineIcon
} from '@heroicons/react/24/outline';

// Language detection from file extensions
export function getLanguageFromExtension(filePath: string): string {
  const extension = filePath.split('.').pop()?.toLowerCase();
  
  const languageMap: Record<string, string> = {
    // JavaScript/TypeScript
    'js': 'javascript',
    'jsx': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'mjs': 'javascript',
    'cjs': 'javascript',
    
    // Python
    'py': 'python',
    'pyw': 'python',
    'pyi': 'python',
    
    // Web
    'html': 'html',
    'htm': 'html',
    'css': 'css',
    'scss': 'scss',
    'sass': 'sass',
    'less': 'less',
    'vue': 'vue',
    'svelte': 'svelte',
    
    // Data formats
    'json': 'json',
    'xml': 'xml',
    'yaml': 'yaml',
    'yml': 'yaml',
    'toml': 'toml',
    'ini': 'ini',
    'csv': 'csv',
    
    // Markup
    'md': 'markdown',
    'markdown': 'markdown',
    'mdx': 'markdown',
    'rst': 'restructuredtext',
    'tex': 'latex',
    
    // Programming languages
    'java': 'java',
    'kt': 'kotlin',
    'scala': 'scala',
    'go': 'go',
    'rs': 'rust',
    'cpp': 'cpp',
    'cc': 'cpp',
    'cxx': 'cpp',
    'c': 'c',
    'h': 'c',
    'hpp': 'cpp',
    'cs': 'csharp',
    'php': 'php',
    'rb': 'ruby',
    'swift': 'swift',
    'dart': 'dart',
    'lua': 'lua',
    'r': 'r',
    'jl': 'julia',
    'elm': 'elm',
    'clj': 'clojure',
    'cljs': 'clojure',
    'hs': 'haskell',
    'ml': 'ocaml',
    'fs': 'fsharp',
    'vb': 'vb',
    'pas': 'pascal',
    'pl': 'perl',
    'pm': 'perl',
    
    // Shell/Scripts
    'sh': 'shell',
    'bash': 'shell',
    'zsh': 'shell',
    'fish': 'shell',
    'ps1': 'powershell',
    'bat': 'batch',
    'cmd': 'batch',
    
    // Database
    'sql': 'sql',
    'mysql': 'sql',
    'pgsql': 'sql',
    'sqlite': 'sql',
    
    // Config files
    'dockerfile': 'dockerfile',
    'dockerignore': 'ignore',
    'gitignore': 'ignore',
    'gitattributes': 'gitattributes',
    'editorconfig': 'editorconfig',
    'prettierrc': 'json',
    'eslintrc': 'json',
    'babelrc': 'json',
    'tsconfig': 'json',
    'jsconfig': 'json',
    'package': 'json',
    'composer': 'json',
    'cargo': 'toml',
    'gemfile': 'ruby',
    'podfile': 'ruby',
    'makefile': 'makefile',
    'cmake': 'cmake',
    'gradle': 'gradle',
    'maven': 'xml',
    'pom': 'xml',
    
    // Other
    'log': 'log',
    'txt': 'plaintext',
    'rtf': 'rtf',
    'pdf': 'pdf'
  };
  
  return languageMap[extension || ''] || 'plaintext';
}

// Get file icon based on file name and extension
export function getFileIcon(fileName: string, extension?: string): React.ReactElement {
  const ext = extension || fileName.split('.').pop()?.toLowerCase() || '';
  const name = fileName.toLowerCase();
  
  // Special files
  if (name === 'package.json' || name === 'composer.json') {
    return <CubeIcon className="w-4 h-4 text-green-500" />;
  }
  
  if (name === 'dockerfile' || name.includes('docker')) {
    return <CubeIcon className="w-4 h-4 text-blue-500" />;
  }
  
  if (name.includes('readme')) {
    return <DocumentTextIcon className="w-4 h-4 text-blue-500" />;
  }
  
  if (name.includes('license') || name.includes('licence')) {
    return <DocumentTextIcon className="w-4 h-4 text-yellow-500" />;
  }
  
  if (name.includes('makefile') || name.includes('cmake')) {
    return <CogIcon className="w-4 h-4 text-orange-500" />;
  }
  
  if (name.includes('gitignore') || name.includes('gitattributes')) {
    return <DocumentIcon className="w-4 h-4 text-gray-500" />;
  }
  
  // By extension
  switch (ext) {
    // Code files
    case 'js':
    case 'jsx':
    case 'ts':
    case 'tsx':
    case 'mjs':
    case 'cjs':
      return <CodeBracketIcon className="w-4 h-4 text-yellow-500" />;
      
    case 'py':
    case 'pyw':
    case 'pyi':
      return <CodeBracketIcon className="w-4 h-4 text-blue-500" />;
      
    case 'java':
    case 'kt':
    case 'scala':
      return <CodeBracketIcon className="w-4 h-4 text-red-500" />;
      
    case 'go':
      return <CodeBracketIcon className="w-4 h-4 text-cyan-500" />;
      
    case 'rs':
      return <CodeBracketIcon className="w-4 h-4 text-orange-600" />;
      
    case 'cpp':
    case 'cc':
    case 'cxx':
    case 'c':
    case 'h':
    case 'hpp':
      return <CodeBracketIcon className="w-4 h-4 text-blue-600" />;
      
    case 'cs':
      return <CodeBracketIcon className="w-4 h-4 text-purple-500" />;
      
    case 'php':
      return <CodeBracketIcon className="w-4 h-4 text-indigo-500" />;
      
    case 'rb':
      return <CodeBracketIcon className="w-4 h-4 text-red-600" />;
      
    case 'swift':
      return <CodeBracketIcon className="w-4 h-4 text-orange-500" />;
      
    case 'dart':
      return <CodeBracketIcon className="w-4 h-4 text-blue-400" />;
      
    // Web files
    case 'html':
    case 'htm':
      return <CodeBracketIcon className="w-4 h-4 text-orange-500" />;
      
    case 'css':
    case 'scss':
    case 'sass':
    case 'less':
      return <CodeBracketIcon className="w-4 h-4 text-blue-500" />;
      
    case 'vue':
      return <CodeBracketIcon className="w-4 h-4 text-green-500" />;
      
    case 'svelte':
      return <CodeBracketIcon className="w-4 h-4 text-orange-600" />;
      
    // Data files
    case 'json':
    case 'xml':
    case 'yaml':
    case 'yml':
    case 'toml':
    case 'ini':
      return <DocumentIcon className="w-4 h-4 text-yellow-600" />;
      
    case 'csv':
      return <DocumentIcon className="w-4 h-4 text-green-600" />;
      
    // Documentation
    case 'md':
    case 'markdown':
    case 'mdx':
    case 'rst':
      return <DocumentTextIcon className="w-4 h-4 text-blue-500" />;
      
    case 'tex':
      return <DocumentTextIcon className="w-4 h-4 text-green-600" />;
      
    case 'pdf':
      return <DocumentTextIcon className="w-4 h-4 text-red-500" />;
      
    // Images
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'bmp':
    case 'svg':
    case 'webp':
    case 'ico':
      return <PhotoIcon className="w-4 h-4 text-purple-500" />;
      
    // Videos
    case 'mp4':
    case 'avi':
    case 'mov':
    case 'wmv':
    case 'flv':
    case 'webm':
    case 'mkv':
      return <FilmIcon className="w-4 h-4 text-red-500" />;
      
    // Audio
    case 'mp3':
    case 'wav':
    case 'flac':
    case 'aac':
    case 'ogg':
    case 'wma':
      return <MusicalNoteIcon className="w-4 h-4 text-green-500" />;
      
    // Archives
    case 'zip':
    case 'rar':
    case 'tar':
    case 'gz':
    case 'bz2':
    case '7z':
    case 'xz':
      return <ArchiveBoxIcon className="w-4 h-4 text-yellow-500" />;
      
    // Shell/Scripts
    case 'sh':
    case 'bash':
    case 'zsh':
    case 'fish':
    case 'ps1':
    case 'bat':
    case 'cmd':
      return <CommandLineIcon className="w-4 h-4 text-green-600" />;
      
    // Database
    case 'sql':
    case 'mysql':
    case 'pgsql':
    case 'sqlite':
      return <DocumentIcon className="w-4 h-4 text-blue-600" />;
      
    // Logs
    case 'log':
      return <DocumentIcon className="w-4 h-4 text-gray-500" />;
      
    // Default
    default:
      return <DocumentIcon className="w-4 h-4 text-gray-500" />;
  }
}

// Get file type category
export function getFileCategory(fileName: string): string {
  const extension = fileName.split('.').pop()?.toLowerCase() || '';
  
  const categories: Record<string, string[]> = {
    'code': [
      'js', 'jsx', 'ts', 'tsx', 'py', 'java', 'kt', 'go', 'rs', 'cpp', 'c', 'cs', 'php', 'rb', 'swift', 'dart'
    ],
    'web': ['html', 'css', 'scss', 'sass', 'less', 'vue', 'svelte'],
    'data': ['json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'csv'],
    'docs': ['md', 'rst', 'tex', 'pdf', 'txt'],
    'images': ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'ico'],
    'media': ['mp4', 'avi', 'mov', 'mp3', 'wav', 'flac'],
    'config': ['dockerfile', 'gitignore', 'editorconfig', 'prettierrc', 'eslintrc'],
    'archive': ['zip', 'tar', 'gz', 'rar', '7z']
  };
  
  for (const [category, extensions] of Object.entries(categories)) {
    if (extensions.includes(extension)) {
      return category;
    }
  }
  
  return 'other';
}

// Format file size
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Check if file is binary
export function isBinaryFile(fileName: string): boolean {
  const extension = fileName.split('.').pop()?.toLowerCase() || '';
  
  const binaryExtensions = [
    // Images
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'ico', 'webp',
    // Videos
    'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv',
    // Audio
    'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma',
    // Archives
    'zip', 'rar', 'tar', 'gz', 'bz2', '7z', 'xz',
    // Executables
    'exe', 'dll', 'so', 'dylib', 'app', 'deb', 'rpm',
    // Documents
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    // Fonts
    'ttf', 'otf', 'woff', 'woff2', 'eot',
    // Other binary
    'bin', 'dat', 'db', 'sqlite', 'sqlite3'
  ];
  
  return binaryExtensions.includes(extension);
}

// Get syntax highlighting theme for Monaco Editor
export function getMonacoTheme(isDark: boolean): string {
  return isDark ? 'vs-dark' : 'vs';
}

// Get file encoding
export function getFileEncoding(fileName: string): string {
  const extension = fileName.split('.').pop()?.toLowerCase() || '';
  
  // Most text files use UTF-8
  const textExtensions = [
    'js', 'jsx', 'ts', 'tsx', 'py', 'java', 'go', 'rs', 'cpp', 'c', 'cs', 'php', 'rb',
    'html', 'css', 'scss', 'sass', 'less', 'vue', 'svelte',
    'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'csv',
    'md', 'rst', 'tex', 'txt', 'log'
  ];
  
  if (textExtensions.includes(extension)) {
    return 'utf-8';
  }
  
  return 'binary';
}

// Check if file should be excluded from analysis
export function shouldExcludeFile(fileName: string, filePath: string): boolean {
  const excludePatterns = [
    // Dependencies
    'node_modules',
    'vendor',
    '.git',
    '.svn',
    '.hg',
    
    // Build outputs
    'dist',
    'build',
    'out',
    'target',
    'bin',
    'obj',
    
    // Cache
    '.cache',
    '.tmp',
    'tmp',
    'temp',
    
    // IDE
    '.vscode',
    '.idea',
    '.vs',
    
    // OS
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
    
    // Logs
    '*.log',
    'logs'
  ];
  
  const lowerPath = filePath.toLowerCase();
  const lowerName = fileName.toLowerCase();
  
  return excludePatterns.some(pattern => {
    if (pattern.includes('*')) {
      const regex = new RegExp(pattern.replace(/\*/g, '.*'));
      return regex.test(lowerName);
    }
    return lowerPath.includes(pattern) || lowerName === pattern;
  });
}
