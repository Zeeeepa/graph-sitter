import React, { useState, useCallback, useMemo } from 'react';
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
import { getFileIcon, getLanguageFromExtension } from '@/utils/fileUtils';
import { VirtualizedList } from '@/components/VirtualizedList';

interface FileTreeProps {
  className?: string;
  onFileSelect?: (filePath: string) => void;
  onFileDoubleClick?: (filePath: string) => void;
  showSearch?: boolean;
}

interface FileTreeItemProps {
  node: FileNode;
  depth: number;
  onToggle: (path: string) => void;
  onSelect: (path: string) => void;
  onDoubleClick: (path: string) => void;
  selectedFile?: string;
  searchQuery?: string;
}

const FileTreeItem: React.FC<FileTreeItemProps> = ({
  node,
  depth,
  onToggle,
  onSelect,
  onDoubleClick,
  selectedFile,
  searchQuery
}) => {
  const isSelected = selectedFile === node.path;
  const isDirectory = node.type === 'directory';
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = node.is_expanded;
  const hasErrors = node.has_errors;
  const errorCount = node.errors.length;

  // Highlight search matches
  const highlightedName = useMemo(() => {
    if (!searchQuery || !searchQuery.trim()) {
      return node.name;
    }

    const query = searchQuery.toLowerCase();
    const name = node.name.toLowerCase();
    const index = name.indexOf(query);

    if (index === -1) {
      return node.name;
    }

    return (
      <>
        {node.name.substring(0, index)}
        <span className="bg-yellow-200 dark:bg-yellow-800 text-yellow-900 dark:text-yellow-100">
          {node.name.substring(index, index + query.length)}
        </span>
        {node.name.substring(index + query.length)}
      </>
    );
  }, [node.name, searchQuery]);

  const handleClick = useCallback(() => {
    onSelect(node.path);
    if (isDirectory && hasChildren) {
      onToggle(node.path);
    }
  }, [node.path, isDirectory, hasChildren, onSelect, onToggle]);

  const handleDoubleClick = useCallback(() => {
    if (!isDirectory) {
      onDoubleClick(node.path);
    }
  }, [node.path, isDirectory, onDoubleClick]);

  const handleToggleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle(node.path);
  }, [node.path, onToggle]);

  const paddingLeft = depth * 16 + 8;

  return (
    <div>
      <motion.div
        className={clsx(
          'flex items-center py-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors',
          isSelected && 'bg-blue-100 dark:bg-blue-900/50 text-blue-900 dark:text-blue-100',
          hasErrors && 'border-l-2 border-red-500'
        )}
        style={{ paddingLeft }}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        whileHover={{ backgroundColor: 'rgba(0, 0, 0, 0.05)' }}
        whileTap={{ scale: 0.98 }}
      >
        {/* Expand/Collapse Icon */}
        {isDirectory && hasChildren && (
          <button
            onClick={handleToggleClick}
            className="flex-shrink-0 w-4 h-4 mr-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            {isExpanded ? (
              <ChevronDownIcon className="w-4 h-4" />
            ) : (
              <ChevronRightIcon className="w-4 h-4" />
            )}
          </button>
        )}

        {/* File/Folder Icon */}
        <div className="flex-shrink-0 w-4 h-4 mr-2">
          {isDirectory ? (
            isExpanded ? (
              <FolderOpenIcon className="w-4 h-4 text-blue-500" />
            ) : (
              <FolderIcon className="w-4 h-4 text-blue-500" />
            )
          ) : (
            <div className="w-4 h-4">
              {getFileIcon(node.name, node.extension)}
            </div>
          )}
        </div>

        {/* File/Folder Name */}
        <span className={clsx(
          'flex-1 text-sm truncate',
          isDirectory && 'font-medium'
        )}>
          {highlightedName}
        </span>

        {/* Error Indicator */}
        {hasErrors && (
          <div className="flex items-center ml-2">
            <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
            <span className="ml-1 text-xs text-red-500">{errorCount}</span>
          </div>
        )}

        {/* File Size */}
        {!isDirectory && node.size && (
          <span className="ml-2 text-xs text-gray-500">
            {formatFileSize(node.size)}
          </span>
        )}
      </motion.div>

      {/* Children */}
      <AnimatePresence>
        {isDirectory && isExpanded && hasChildren && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {node.children!.map((child) => (
              <FileTreeItem
                key={child.path}
                node={child}
                depth={depth + 1}
                onToggle={onToggle}
                onSelect={onSelect}
                onDoubleClick={onDoubleClick}
                selectedFile={selectedFile}
                searchQuery={searchQuery}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

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

  // Flatten tree for search and virtualization
  const flattenedNodes = useMemo(() => {
    if (!fileTree) return [];

    const flatten = (node: FileNode, depth: number = 0): Array<{ node: FileNode; depth: number }> => {
      const result = [{ node, depth }];
      
      if (node.type === 'directory' && node.is_expanded && node.children) {
        for (const child of node.children) {
          result.push(...flatten(child, depth + 1));
        }
      }
      
      return result;
    };

    return flatten(fileTree);
  }, [fileTree]);

  // Filter nodes based on search query
  const filteredNodes = useMemo(() => {
    if (!searchQuery.trim()) {
      return flattenedNodes;
    }

    const query = searchQuery.toLowerCase();
    return flattenedNodes.filter(({ node }) =>
      node.name.toLowerCase().includes(query) ||
      node.path.toLowerCase().includes(query)
    );
  }, [flattenedNodes, searchQuery]);

  const handleToggle = useCallback((path: string) => {
    const node = findNodeByPath(fileTree, path);
    if (node?.is_expanded) {
      collapseFileNode(path);
    } else {
      expandFileNode(path);
    }
  }, [fileTree, expandFileNode, collapseFileNode]);

  const handleSelect = useCallback((path: string) => {
    selectFileNode(path);
    onFileSelect?.(path);
  }, [selectFileNode, onFileSelect]);

  const handleDoubleClick = useCallback((path: string) => {
    onFileDoubleClick?.(path);
  }, [onFileDoubleClick]);

  if (!fileTree) {
    return (
      <div className={clsx('flex items-center justify-center h-full', className)}>
        <div className="text-center text-gray-500 dark:text-gray-400">
          <FolderIcon className="w-12 h-12 mx-auto mb-2" />
          <p>No project selected</p>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('flex flex-col h-full', className)}>
      {/* Search Bar */}
      {showSearch && (
        <div className="p-2 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      )}

      {/* File Tree */}
      <div className="flex-1 overflow-hidden">
        {filteredNodes.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
            {searchQuery ? 'No files match your search' : 'No files found'}
          </div>
        ) : (
          <VirtualizedList
            items={filteredNodes}
            itemHeight={28}
            renderItem={({ item, index }) => (
              <FileTreeItem
                key={item.node.path}
                node={item.node}
                depth={item.depth}
                onToggle={handleToggle}
                onSelect={handleSelect}
                onDoubleClick={handleDoubleClick}
                selectedFile={selectedFile}
                searchQuery={searchQuery}
              />
            )}
          />
        )}
      </div>

      {/* File Tree Stats */}
      <div className="p-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
        {filteredNodes.length} items
        {searchQuery && ` (filtered from ${flattenedNodes.length})`}
      </div>
    </div>
  );
};

// Helper functions
function findNodeByPath(tree: FileNode | null, path: string): FileNode | null {
  if (!tree) return null;
  
  if (tree.path === path) {
    return tree;
  }
  
  if (tree.children) {
    for (const child of tree.children) {
      const found = findNodeByPath(child, path);
      if (found) return found;
    }
  }
  
  return null;
}

function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(1)}${units[unitIndex]}`;
}
