import React, { useRef, useEffect, useState, useCallback } from 'react';
import Editor, { Monaco } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { 
  DocumentIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
  MagnifyingGlassIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import { EditorState, CodeError, Location, Symbol } from '@/types';
import { useTheme, useViewState } from '@/store';
import { getLanguageFromExtension } from '@/utils/fileUtils';

interface CodeEditorProps {
  filePath?: string;
  content?: string;
  language?: string;
  errors?: CodeError[];
  symbols?: Symbol[];
  readOnly?: boolean;
  className?: string;
  onContentChange?: (content: string) => void;
  onCursorPositionChange?: (line: number, column: number) => void;
  onSymbolClick?: (symbol: Symbol) => void;
  onGoToDefinition?: (filePath: string, line: number, column: number) => void;
  onFindReferences?: (filePath: string, line: number, column: number) => void;
}

interface EditorMarker {
  id: string;
  range: monaco.IRange;
  options: monaco.editor.IModelDecorationOptions;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  filePath,
  content = '',
  language,
  errors = [],
  symbols = [],
  readOnly = false,
  className,
  onContentChange,
  onCursorPositionChange,
  onSymbolClick,
  onGoToDefinition,
  onFindReferences
}) => {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const theme = useTheme();
  const viewState = useViewState();
  const [isLoading, setIsLoading] = useState(true);
  const [decorations, setDecorations] = useState<string[]>([]);

  // Determine language from file extension if not provided
  const detectedLanguage = language || (filePath ? getLanguageFromExtension(filePath) : 'plaintext');

  // Configure Monaco Editor
  const handleEditorDidMount = useCallback((editor: monaco.editor.IStandaloneCodeEditor, monaco: Monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    setIsLoading(false);

    // Configure editor options
    editor.updateOptions({
      minimap: { enabled: viewState.showMinimap },
      lineNumbers: viewState.showLineNumbers ? 'on' : 'off',
      wordWrap: viewState.wordWrap ? 'on' : 'off',
      readOnly,
      fontSize: 14,
      fontFamily: 'JetBrains Mono, Fira Code, Monaco, Consolas, monospace',
      lineHeight: 20,
      letterSpacing: 0.5,
      smoothScrolling: true,
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: true,
      renderWhitespace: 'selection',
      renderControlCharacters: true,
      folding: true,
      foldingStrategy: 'indentation',
      showFoldingControls: 'always',
      bracketPairColorization: { enabled: true },
      guides: {
        bracketPairs: true,
        indentation: true
      },
      suggest: {
        showKeywords: true,
        showSnippets: true,
        showFunctions: true,
        showConstructors: true,
        showFields: true,
        showVariables: true,
        showClasses: true,
        showStructs: true,
        showInterfaces: true,
        showModules: true,
        showProperties: true,
        showEvents: true,
        showOperators: true,
        showUnits: true,
        showValues: true,
        showConstants: true,
        showEnums: true,
        showEnumMembers: true,
        showColors: true,
        showFiles: true,
        showReferences: true,
        showFolders: true,
        showTypeParameters: true,
        showIssues: true,
        showUsers: true,
        showWords: true
      }
    });

    // Add cursor position change listener
    editor.onDidChangeCursorPosition((e) => {
      onCursorPositionChange?.(e.position.lineNumber, e.position.column);
    });

    // Add content change listener
    editor.onDidChangeModelContent(() => {
      const value = editor.getValue();
      onContentChange?.(value);
    });

    // Add context menu actions
    editor.addAction({
      id: 'go-to-definition',
      label: 'Go to Definition',
      keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.F12],
      contextMenuGroupId: 'navigation',
      contextMenuOrder: 1,
      run: (editor) => {
        const position = editor.getPosition();
        if (position && filePath) {
          onGoToDefinition?.(filePath, position.lineNumber, position.column);
        }
      }
    });

    editor.addAction({
      id: 'find-references',
      label: 'Find All References',
      keybindings: [monaco.KeyMod.Shift | monaco.KeyCode.F12],
      contextMenuGroupId: 'navigation',
      contextMenuOrder: 2,
      run: (editor) => {
        const position = editor.getPosition();
        if (position && filePath) {
          onFindReferences?.(filePath, position.lineNumber, position.column);
        }
      }
    });

    // Add symbol click handler
    editor.onMouseDown((e) => {
      if (e.event.ctrlKey || e.event.metaKey) {
        const position = e.target.position;
        if (position) {
          const symbol = findSymbolAtPosition(symbols, position.lineNumber, position.column);
          if (symbol) {
            onSymbolClick?.(symbol);
          }
        }
      }
    });

    // Configure hover provider for symbols
    monaco.languages.registerHoverProvider(detectedLanguage, {
      provideHover: (model, position) => {
        const symbol = findSymbolAtPosition(symbols, position.lineNumber, position.column);
        if (symbol) {
          return {
            range: new monaco.Range(
              position.lineNumber,
              position.column,
              position.lineNumber,
              position.column + symbol.name.length
            ),
            contents: [
              { value: `**${symbol.kind}** ${symbol.name}` },
              { value: symbol.signature || '' },
              { value: symbol.documentation || '' }
            ].filter(c => c.value)
          };
        }
        return null;
      }
    });

    // Configure definition provider
    monaco.languages.registerDefinitionProvider(detectedLanguage, {
      provideDefinition: (model, position) => {
        const symbol = findSymbolAtPosition(symbols, position.lineNumber, position.column);
        if (symbol?.definition) {
          return {
            uri: monaco.Uri.file(symbol.definition.file_path),
            range: new monaco.Range(
              symbol.definition.line,
              symbol.definition.column,
              symbol.definition.end_line || symbol.definition.line,
              symbol.definition.end_column || symbol.definition.column
            )
          };
        }
        return null;
      }
    });

    // Configure reference provider
    monaco.languages.registerReferenceProvider(detectedLanguage, {
      provideReferences: (model, position, context) => {
        const symbol = findSymbolAtPosition(symbols, position.lineNumber, position.column);
        if (symbol?.references) {
          return symbol.references.map(ref => ({
            uri: monaco.Uri.file(ref.file_path),
            range: new monaco.Range(
              ref.line,
              ref.column,
              ref.end_line || ref.line,
              ref.end_column || ref.column
            )
          }));
        }
        return [];
      }
    });
  }, [
    detectedLanguage,
    viewState,
    readOnly,
    symbols,
    filePath,
    onCursorPositionChange,
    onContentChange,
    onSymbolClick,
    onGoToDefinition,
    onFindReferences
  ]);

  // Update decorations when errors change
  useEffect(() => {
    if (!editorRef.current || !monacoRef.current) return;

    const editor = editorRef.current;
    const monaco = monacoRef.current;

    // Create decorations for errors
    const newDecorations: monaco.editor.IModelDeltaDecoration[] = errors
      .filter(error => error.file_path === filePath)
      .map(error => ({
        range: new monaco.Range(error.line, error.column, error.line, error.column + 1),
        options: {
          isWholeLine: false,
          className: clsx(
            'editor-error-decoration',
            error.severity === 'error' && 'border-b-2 border-red-500',
            error.severity === 'warning' && 'border-b-2 border-yellow-500',
            error.severity === 'info' && 'border-b-2 border-blue-500'
          ),
          hoverMessage: {
            value: `**${error.severity.toUpperCase()}**: ${error.message}${error.rule ? ` (${error.rule})` : ''}`
          },
          glyphMarginClassName: clsx(
            'editor-error-glyph',
            error.severity === 'error' && 'bg-red-500',
            error.severity === 'warning' && 'bg-yellow-500',
            error.severity === 'info' && 'bg-blue-500'
          ),
          minimap: {
            color: error.severity === 'error' ? '#ef4444' : 
                   error.severity === 'warning' ? '#f59e0b' : '#3b82f6',
            position: monaco.editor.MinimapPosition.Inline
          }
        }
      }));

    // Apply decorations
    const newDecorationIds = editor.deltaDecorations(decorations, newDecorations);
    setDecorations(newDecorationIds);
  }, [errors, filePath, decorations]);

  // Update editor options when view state changes
  useEffect(() => {
    if (!editorRef.current) return;

    editorRef.current.updateOptions({
      minimap: { enabled: viewState.showMinimap },
      lineNumbers: viewState.showLineNumbers ? 'on' : 'off',
      wordWrap: viewState.wordWrap ? 'on' : 'off'
    });
  }, [viewState.showMinimap, viewState.showLineNumbers, viewState.wordWrap]);

  // Navigate to specific line and column
  const goToPosition = useCallback((line: number, column: number) => {
    if (!editorRef.current) return;

    editorRef.current.setPosition({ lineNumber: line, column });
    editorRef.current.revealLineInCenter(line);
    editorRef.current.focus();
  }, []);

  // Expose editor methods
  React.useImperativeHandle(React.createRef(), () => ({
    goToPosition,
    focus: () => editorRef.current?.focus(),
    getValue: () => editorRef.current?.getValue() || '',
    setValue: (value: string) => editorRef.current?.setValue(value),
    getSelection: () => editorRef.current?.getSelection(),
    setSelection: (selection: monaco.ISelection) => editorRef.current?.setSelection(selection)
  }));

  if (!filePath) {
    return (
      <div className={clsx('flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900', className)}>
        <div className="text-center text-gray-500 dark:text-gray-400">
          <DocumentIcon className="w-16 h-16 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No file selected</h3>
          <p>Select a file from the explorer to view its contents</p>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('flex flex-col h-full', className)}>
      {/* Editor Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2">
          <DocumentIcon className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {filePath.split('/').pop()}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {detectedLanguage}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Error Summary */}
          {errors.length > 0 && (
            <div className="flex items-center space-x-1 text-xs">
              {errors.filter(e => e.severity === 'error').length > 0 && (
                <div className="flex items-center text-red-500">
                  <ExclamationCircleIcon className="w-4 h-4 mr-1" />
                  {errors.filter(e => e.severity === 'error').length}
                </div>
              )}
              {errors.filter(e => e.severity === 'warning').length > 0 && (
                <div className="flex items-center text-yellow-500">
                  <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
                  {errors.filter(e => e.severity === 'warning').length}
                </div>
              )}
              {errors.filter(e => e.severity === 'info').length > 0 && (
                <div className="flex items-center text-blue-500">
                  <InformationCircleIcon className="w-4 h-4 mr-1" />
                  {errors.filter(e => e.severity === 'info').length}
                </div>
              )}
            </div>
          )}

          {/* Editor Actions */}
          <button
            className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            title="Search in file"
            onClick={() => {
              if (editorRef.current) {
                editorRef.current.getAction('actions.find')?.run();
              }
            }}
          >
            <MagnifyingGlassIcon className="w-4 h-4" />
          </button>

          <button
            className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            title="Editor settings"
          >
            <Cog6ToothIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-900 z-10">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"
            />
          </div>
        )}

        <Editor
          height="100%"
          language={detectedLanguage}
          value={content}
          theme={theme === 'dark' ? 'vs-dark' : 'vs'}
          onMount={handleEditorDidMount}
          options={{
            automaticLayout: true,
            scrollBeyondLastLine: false,
            renderLineHighlight: 'line',
            selectOnLineNumbers: true,
            roundedSelection: false,
            cursorStyle: 'line',
            mouseWheelZoom: true,
            contextmenu: true,
            quickSuggestions: true,
            parameterHints: { enabled: true },
            formatOnPaste: true,
            formatOnType: true,
            autoIndent: 'full',
            tabCompletion: 'on',
            wordBasedSuggestions: true,
            semanticHighlighting: { enabled: true }
          }}
          loading={
            <div className="flex items-center justify-center h-full">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"
              />
            </div>
          }
        />
      </div>
    </div>
  );
};

// Helper function to find symbol at position
function findSymbolAtPosition(symbols: Symbol[], line: number, column: number): Symbol | null {
  return symbols.find(symbol => {
    const loc = symbol.location;
    return loc.line === line && 
           column >= loc.column && 
           column <= (loc.end_column || loc.column + symbol.name.length);
  }) || null;
}
