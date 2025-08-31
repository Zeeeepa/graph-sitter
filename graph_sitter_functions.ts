/**
 * graph_sitter_functions.ts
 * 
 * A comprehensive TypeScript library that organizes all graph-sitter functions
 * into three main categories: Analysis, Manipulation, and Visualization.
 * 
 * This file provides TypeScript interfaces and implementations for interacting
 * with the graph-sitter API, making it easier to perform code analysis,
 * manipulation, and visualization tasks.
 */

// Type definitions for common graph-sitter objects
export interface CodebaseConfig {
  method_usages?: boolean;
  generics?: boolean;
  sync_enabled?: boolean;
  full_range_index?: boolean;
  py_resolve_syspath?: boolean;
  exp_lazy_graph?: boolean;
}

export interface Position {
  line: number;
  column: number;
}

export interface Range {
  start: Position;
  end: Position;
}

export interface Symbol {
  name: string;
  filepath: string;
  range?: Range;
  type: string;
}

export interface File {
  path: string;
  name: string;
  content: string;
}

export interface Function {
  name: string;
  filepath: string;
  parameters: Parameter[];
  return_type?: string;
  is_async: boolean;
  decorators: string[];
  usages: Usage[];
  call_sites: CallSite[];
  dependencies: Symbol[];
  function_calls: FunctionCall[];
}

export interface Class {
  name: string;
  filepath: string;
  methods: Function[];
  attributes: Attribute[];
  superclasses: Class[];
  subclasses: Class[];
  usages: Usage[];
  dependencies: Symbol[];
  is_abstract: boolean;
}

export interface Parameter {
  name: string;
  type?: string;
  default_value?: string;
}

export interface Usage {
  filepath: string;
  range: Range;
  context: string;
}

export interface CallSite {
  filepath: string;
  range: Range;
  caller: Function;
}

export interface FunctionCall {
  name: string;
  filepath: string;
  range: Range;
  arguments: any[];
}

export interface Attribute {
  name: string;
  type?: string;
  value?: string;
}

export interface Import {
  name: string;
  filepath: string;
  is_external: boolean;
  resolved_symbol?: Symbol;
}

export interface ExternalModule {
  name: string;
  symbols: Symbol[];
}

// Main Codebase interface
export interface Codebase {
  functions: Function[];
  classes: Class[];
  imports: Import[];
  files: File[];
  symbols: Symbol[];
  external_modules: ExternalModule[];
  
  // Core methods
  get_function(name: string): Function | null;
  get_class(name: string): Class | null;
  get_file(path: string): File | null;
  get_symbol(name: string): Symbol | null;
  get_directory(path: string): Directory | null;
  
  // Git operations
  checkout(branch: string): boolean;
  commit(message: string): boolean;
  create_pr(options: PROptions): boolean;
}

export interface Directory {
  path: string;
  name: string;
  files: File[];
  subdirectories: Directory[];
}

export interface PROptions {
  title: string;
  body: string;
  base_branch?: string;
  head_branch: string;
  draft?: boolean;
}

/**
 * ===================================================
 * ANALYSIS FUNCTIONS
 * ===================================================
 * 
 * Functions for analyzing codebases, including:
 * - Code structure analysis
 * - Relationship analysis
 * - Error detection
 * - Dependency analysis
 */

export class Analysis {
  private codebase: Codebase;
  
  constructor(codebase: Codebase) {
    this.codebase = codebase;
  }
  
  /**
   * Get detailed analysis for a specific function
   */
  getFunctionAnalysis(functionName: string): Record<string, any> {
    const func = this.codebase.get_function(functionName);
    if (!func) return {};
    
    return {
      name: func.name,
      parameters: func.parameters.map(p => p.name),
      return_type: func.return_type,
      decorators: func.decorators,
      is_async: func.is_async,
      is_generator: false, // Default value, would be determined by analysis
      complexity: this.calculateComplexity(func),
      line_count: 0, // Would be calculated from code_block
      usages: func.usages.length
    };
  }
  
  /**
   * Get detailed analysis for a specific class
   */
  getClassAnalysis(className: string): Record<string, any> {
    const cls = this.codebase.get_class(className);
    if (!cls) return {};
    
    return {
      name: cls.name,
      methods: cls.methods.length,
      attributes: cls.attributes.length,
      superclasses: cls.superclasses.map(sc => sc.name),
      subclasses: cls.subclasses.map(sc => sc.name),
      decorators: [], // Would be populated from class decorators
      is_abstract: cls.is_abstract
    };
  }
  
  /**
   * Get import analysis for a file or entire codebase
   */
  getImportAnalysis(filePath?: string): Record<string, any> {
    if (filePath) {
      const file = this.codebase.get_file(filePath);
      if (!file) return { error: `File not found: ${filePath}` };
      
      // This would be populated from file.imports
      const imports = [];
      const externalImports = [];
      
      return {
        file: filePath,
        imports: imports.length,
        external_imports: externalImports.length
      };
    } else {
      // Analyze all files
      const totalFiles = this.codebase.files.length;
      const totalImports = this.codebase.imports.length;
      
      return {
        total_files: totalFiles,
        total_imports: totalImports,
        average_imports_per_file: totalFiles > 0 ? totalImports / totalFiles : 0
      };
    }
  }
  
  /**
   * Find unused code (functions, classes, imports)
   */
  findUnusedCode(): Record<string, any[]> {
    const unusedFunctions = this.codebase.functions.filter(f => f.usages.length === 0);
    const unusedClasses = this.codebase.classes.filter(c => c.usages.length === 0);
    const unusedImports = this.codebase.imports.filter(i => !i.resolved_symbol || i.resolved_symbol.usages?.length === 0);
    
    return {
      functions: unusedFunctions.map(f => ({
        name: f.name,
        filepath: f.filepath
      })),
      classes: unusedClasses.map(c => ({
        name: c.name,
        filepath: c.filepath
      })),
      imports: unusedImports.map(i => ({
        name: i.name,
        filepath: i.filepath
      }))
    };
  }
  
  /**
   * Find circular dependencies in the codebase
   */
  findCircularDependencies(): string[][] {
    // This would use a graph algorithm to find cycles
    // Simplified implementation for demonstration
    return [];
  }
  
  /**
   * Find recursive functions in the codebase
   */
  findRecursiveFunctions(): Function[] {
    return this.codebase.functions.filter(func => 
      func.function_calls.some(call => call.name === func.name)
    );
  }
  
  /**
   * Calculate complexity of a function
   */
  private calculateComplexity(func: Function): number {
    // This would analyze the function's code to determine cyclomatic complexity
    // Simplified implementation for demonstration
    return 1;
  }
  
  /**
   * Generate a summary of the codebase
   */
  getCodebaseSummary(): Record<string, any> {
    return {
      files: this.codebase.files.length,
      directories: 0, // Would be calculated
      functions: this.codebase.functions.length,
      classes: this.codebase.classes.length,
      imports: this.codebase.imports.length,
      errors: 0 // Would be calculated
    };
  }
  
  /**
   * Generate a summary of a file
   */
  getFileSummary(filePath: string): Record<string, any> {
    const file = this.codebase.get_file(filePath);
    if (!file) return { error: `File not found: ${filePath}` };
    
    // Find functions and classes in this file
    const functions = this.codebase.functions.filter(f => f.filepath === filePath);
    const classes = this.codebase.classes.filter(c => c.filepath === filePath);
    const imports = this.codebase.imports.filter(i => i.filepath === filePath);
    
    return {
      name: file.name,
      path: file.path,
      functions: functions.length,
      classes: classes.length,
      imports: imports.length,
      lines: file.content.split("\n").length
    };
  }
  
  /**
   * Generate a summary of a function
   */
  getFunctionSummary(functionName: string): Record<string, any> {
    const func = this.codebase.get_function(functionName);
    if (!func) return { error: `Function not found: ${functionName}` };
    
    return {
      name: func.name,
      filepath: func.filepath,
      parameters: func.parameters.map(p => p.name),
      return_type: func.return_type,
      docstring: null, // Would be extracted from function
      calls: func.function_calls.map(call => call.name),
      called_by: func.call_sites.map(site => site.caller.name)
    };
  }
  
  /**
   * Find the deepest inheritance chains
   */
  findDeepestInheritanceChains(): Array<[Class, number]> {
    const inheritanceDepth = this.codebase.classes.map(c => [c, c.superclasses.length] as [Class, number]);
    return inheritanceDepth.sort((a, b) => b[1] - a[1]).slice(0, 5);
  }
  
  /**
   * Find the most complex files by function count
   */
  findMostComplexFiles(): Array<[File, number]> {
    const fileComplexity = new Map<string, number>();
    
    for (const func of this.codebase.functions) {
      const count = fileComplexity.get(func.filepath) || 0;
      fileComplexity.set(func.filepath, count + 1);
    }
    
    const result: Array<[File, number]> = [];
    fileComplexity.forEach((count, path) => {
      const file = this.codebase.get_file(path);
      if (file) {
        result.push([file, count]);
      }
    });
    
    return result.sort((a, b) => b[1] - a[1]).slice(0, 5);
  }
  
  /**
   * Find the most used functions
   */
  findMostUsedFunctions(): Array<[Function, number]> {
    const functionUsage = this.codebase.functions.map(f => [f, f.usages.length] as [Function, number]);
    return functionUsage.sort((a, b) => b[1] - a[1]).slice(0, 5);
  }
}

/**
 * ===================================================
 * MANIPULATION FUNCTIONS
 * ===================================================
 * 
 * Functions for manipulating codebases, including:
 * - Symbol manipulation (rename, move, delete)
 * - Import management
 * - Code transformation
 * - File operations
 */

export class Manipulation {
  private codebase: Codebase;
  
  constructor(codebase: Codebase) {
    this.codebase = codebase;
  }
  
  /**
   * Rename a symbol (function, class, variable) throughout the codebase
   */
  renameSymbol(symbolName: string, newName: string): boolean {
    const symbol = this.codebase.get_symbol(symbolName);
    if (!symbol) return false;
    
    // In a real implementation, this would:
    // 1. Update the symbol definition
    // 2. Update all references/usages
    // 3. Update imports if necessary
    
    return true;
  }
  
  /**
   * Move a symbol to a different file
   */
  moveSymbolToFile(symbolName: string, targetFilePath: string): boolean {
    const symbol = this.codebase.get_symbol(symbolName);
    if (!symbol) return false;
    
    const targetFile = this.codebase.get_file(targetFilePath);
    if (!targetFile) return false;
    
    // In a real implementation, this would:
    // 1. Remove the symbol from its current file
    // 2. Add it to the target file
    // 3. Update imports in both files
    // 4. Update all references to use the new import path
    
    return true;
  }
  
  /**
   * Delete a symbol from the codebase
   */
  deleteSymbol(symbolName: string): boolean {
    const symbol = this.codebase.get_symbol(symbolName);
    if (!symbol) return false;
    
    // In a real implementation, this would:
    // 1. Remove the symbol definition
    // 2. Remove or update all references/usages
    // 3. Remove or update imports
    
    return true;
  }
  
  /**
   * Add an import to a file
   */
  addImport(filePath: string, importString: string): boolean {
    const file = this.codebase.get_file(filePath);
    if (!file) return false;
    
    // In a real implementation, this would:
    // 1. Parse the import string
    // 2. Add the import to the file
    // 3. Handle duplicate imports
    
    return true;
  }
  
  /**
   * Remove an import from a file
   */
  removeImport(filePath: string, importName: string): boolean {
    const file = this.codebase.get_file(filePath);
    if (!file) return false;
    
    // In a real implementation, this would:
    // 1. Find the import statement
    // 2. Remove it from the file
    // 3. Handle partial imports (e.g., from module import {a, b, c})
    
    return true;
  }
  
  /**
   * Create a new file
   */
  createFile(filePath: string, content: string): File | null {
    // In a real implementation, this would:
    // 1. Create the file
    // 2. Add it to the codebase
    // 3. Parse it for symbols
    
    return null;
  }
  
  /**
   * Delete a file
   */
  deleteFile(filePath: string): boolean {
    const file = this.codebase.get_file(filePath);
    if (!file) return false;
    
    // In a real implementation, this would:
    // 1. Remove the file
    // 2. Update all imports that reference it
    
    return true;
  }
  
  /**
   * Create a new function
   */
  createFunction(filePath: string, functionCode: string): Function | null {
    const file = this.codebase.get_file(filePath);
    if (!file) return null;
    
    // In a real implementation, this would:
    // 1. Parse the function code
    // 2. Add it to the file
    // 3. Add it to the codebase's function list
    
    return null;
  }
  
  /**
   * Create a new class
   */
  createClass(filePath: string, classCode: string): Class | null {
    const file = this.codebase.get_file(filePath);
    if (!file) return null;
    
    // In a real implementation, this would:
    // 1. Parse the class code
    // 2. Add it to the file
    // 3. Add it to the codebase's class list
    
    return null;
  }
  
  /**
   * Add a parameter to a function
   */
  addFunctionParameter(functionName: string, paramName: string, paramType?: string, defaultValue?: string): boolean {
    const func = this.codebase.get_function(functionName);
    if (!func) return false;
    
    // In a real implementation, this would:
    // 1. Update the function signature
    // 2. Update all call sites to include the new parameter (with default value if provided)
    
    return true;
  }
  
  /**
   * Remove a parameter from a function
   */
  removeFunctionParameter(functionName: string, paramName: string): boolean {
    const func = this.codebase.get_function(functionName);
    if (!func) return false;
    
    // In a real implementation, this would:
    // 1. Update the function signature
    // 2. Update all call sites to remove the parameter
    
    return true;
  }
  
  /**
   * Add a method to a class
   */
  addClassMethod(className: string, methodCode: string): boolean {
    const cls = this.codebase.get_class(className);
    if (!cls) return false;
    
    // In a real implementation, this would:
    // 1. Parse the method code
    // 2. Add it to the class
    // 3. Add it to the codebase's function list
    
    return true;
  }
  
  /**
   * Add an attribute to a class
   */
  addClassAttribute(className: string, attrName: string, attrType?: string, value?: string): boolean {
    const cls = this.codebase.get_class(className);
    if (!cls) return false;
    
    // In a real implementation, this would:
    // 1. Create the attribute
    // 2. Add it to the class
    
    return true;
  }
  
  /**
   * Set a function's return type
   */
  setFunctionReturnType(functionName: string, returnType: string): boolean {
    const func = this.codebase.get_function(functionName);
    if (!func) return false;
    
    // In a real implementation, this would:
    // 1. Update the function signature with the return type
    
    return true;
  }
  
  /**
   * Convert a function to async
   */
  convertFunctionToAsync(functionName: string): boolean {
    const func = this.codebase.get_function(functionName);
    if (!func) return false;
    
    // In a real implementation, this would:
    // 1. Add the async keyword to the function
    // 2. Update return statements to use Promise if necessary
    // 3. Update call sites to handle the async nature (await, etc.)
    
    return true;
  }
  
  /**
   * Extract a code block into a new function
   */
  extractFunction(filePath: string, startLine: number, endLine: number, newFunctionName: string): Function | null {
    const file = this.codebase.get_file(filePath);
    if (!file) return null;
    
    // In a real implementation, this would:
    // 1. Extract the code block
    // 2. Analyze variables to determine parameters and return values
    // 3. Create a new function
    // 4. Replace the original code block with a call to the new function
    
    return null;
  }
  
  /**
   * Inline a function (replace calls with the function body)
   */
  inlineFunction(functionName: string): boolean {
    const func = this.codebase.get_function(functionName);
    if (!func) return false;
    
    // In a real implementation, this would:
    // 1. Find all call sites
    // 2. Replace each call with the function body
    // 3. Handle parameters and return values
    // 4. Optionally remove the original function
    
    return true;
  }
  
  /**
   * Add a decorator to a function or class
   */
  addDecorator(symbolName: string, decoratorCode: string): boolean {
    const symbol = this.codebase.get_symbol(symbolName);
    if (!symbol) return false;
    
    // In a real implementation, this would:
    // 1. Parse the decorator code
    // 2. Add it to the symbol
    
    return true;
  }
  
  /**
   * Commit changes to the codebase
   */
  commitChanges(message: string): boolean {
    return this.codebase.commit(message);
  }
  
  /**
   * Create a pull request with the changes
   */
  createPullRequest(options: PROptions): boolean {
    return this.codebase.create_pr(options);
  }
}

/**
 * ===================================================
 * VISUALIZATION FUNCTIONS
 * ===================================================
 * 
 * Functions for visualizing codebases, including:
 * - Call graphs
 * - Dependency graphs
 * - Inheritance hierarchies
 * - Code structure visualization
 */

export interface VisualizationNode {
  id: string;
  label: string;
  type: string;
  data?: any;
  color?: string;
  size?: number;
  shape?: string;
}

export interface VisualizationEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type?: string;
  data?: any;
  color?: string;
  width?: number;
  style?: string;
}

export interface VisualizationGraph {
  nodes: VisualizationNode[];
  edges: VisualizationEdge[];
}

export interface VisualizationOptions {
  layout?: string;
  directed?: boolean;
  nodeColor?: string;
  edgeColor?: string;
  nodeSize?: number;
  edgeWidth?: number;
  labels?: boolean;
  arrows?: boolean;
  legend?: boolean;
  title?: string;
  width?: number;
  height?: number;
}

export class Visualization {
  private codebase: Codebase;
  
  constructor(codebase: Codebase) {
    this.codebase = codebase;
  }
  
  /**
   * Create a call graph visualization
   */
  createCallGraph(entryPoint?: string, options?: VisualizationOptions): VisualizationGraph {
    const nodes: VisualizationNode[] = [];
    const edges: VisualizationEdge[] = [];
    
    // Start with the entry point or all functions
    const startFunctions = entryPoint 
      ? [this.codebase.get_function(entryPoint)].filter(Boolean) 
      : this.codebase.functions;
    
    // Add nodes for all functions
    for (const func of this.codebase.functions) {
      const complexity = this.calculateComplexity(func);
      
      // Determine color based on complexity
      let color = '#10b981'; // green
      if (complexity > 10) {
        color = '#ef4444'; // red
      } else if (complexity > 5) {
        color = '#f59e0b'; // yellow
      }
      
      nodes.push({
        id: `${func.filepath}:${func.name}`,
        label: func.name,
        type: 'function',
        data: {
          filepath: func.filepath,
          parameters: func.parameters,
          return_type: func.return_type,
          is_async: func.is_async,
          complexity: complexity
        },
        color: color,
        size: Math.min(complexity * 2 + 5, 20),
        shape: 'circle'
      });
    }
    
    // Add edges for function calls
    let edgeId = 0;
    for (const func of this.codebase.functions) {
      for (const call of func.function_calls) {
        // Find the target function
        const targetFunc = this.codebase.functions.find(f => f.name === call.name);
        if (targetFunc) {
          edges.push({
            id: `edge_${edgeId++}`,
            source: `${func.filepath}:${func.name}`,
            target: `${targetFunc.filepath}:${targetFunc.name}`,
            type: 'call',
            style: 'solid',
            color: '#6b7280' // gray
          });
        }
      }
    }
    
    return { nodes, edges };
  }
  
  /**
   * Create a dependency graph visualization
   */
  createDependencyGraph(options?: VisualizationOptions): VisualizationGraph {
    const nodes: VisualizationNode[] = [];
    const edges: VisualizationEdge[] = [];
    
    // Add nodes for all files
    for (const file of this.codebase.files) {
      // Count functions and classes for size
      const functions = this.codebase.functions.filter(f => f.filepath === file.path);
      const classes = this.codebase.classes.filter(c => c.filepath === file.path);
      const size = Math.min((functions.length + classes.length) * 2 + 5, 25);
      
      nodes.push({
        id: file.path,
        label: file.name,
        type: 'file',
        data: {
          path: file.path,
          functions: functions.length,
          classes: classes.length
        },
        size: size,
        color: '#3b82f6', // blue
        shape: 'square'
      });
    }
    
    // Add edges for imports
    let edgeId = 0;
    for (const file of this.codebase.files) {
      const imports = this.codebase.imports.filter(i => i.filepath === file.path);
      
      for (const imp of imports) {
        if (imp.resolved_symbol) {
          const targetFile = this.codebase.files.find(f => f.path === imp.resolved_symbol?.filepath);
          if (targetFile) {
            edges.push({
              id: `edge_${edgeId++}`,
              source: file.path,
              target: targetFile.path,
              type: 'import',
              style: 'solid',
              color: '#6b7280' // gray
            });
          }
        }
      }
    }
    
    return { nodes, edges };
  }
  
  /**
   * Create an inheritance graph visualization
   */
  createInheritanceGraph(options?: VisualizationOptions): VisualizationGraph {
    const nodes: VisualizationNode[] = [];
    const edges: VisualizationEdge[] = [];
    
    // Add nodes for all classes
    for (const cls of this.codebase.classes) {
      const methods = cls.methods.length;
      const inheritanceDepth = cls.superclasses.length;
      
      // Color based on inheritance depth
      let color = '#8b5cf6'; // purple
      if (inheritanceDepth > 3) {
        color = '#ef4444'; // red
      } else if (inheritanceDepth > 1) {
        color = '#f59e0b'; // yellow
      }
      
      nodes.push({
        id: `${cls.filepath}:${cls.name}`,
        label: cls.name,
        type: 'class',
        data: {
          filepath: cls.filepath,
          methods: methods,
          attributes: cls.attributes.length,
          inheritance_depth: inheritanceDepth
        },
        size: Math.min(methods + 5, 20),
        color: color,
        shape: 'diamond'
      });
    }
    
    // Add edges for inheritance relationships
    let edgeId = 0;
    for (const cls of this.codebase.classes) {
      for (const superclass of cls.superclasses) {
        edges.push({
          id: `edge_${edgeId++}`,
          source: `${superclass.filepath}:${superclass.name}`,
          target: `${cls.filepath}:${cls.name}`,
          type: 'inheritance',
          style: 'solid',
          color: '#8b5cf6' // purple
        });
      }
    }
    
    return { nodes, edges };
  }
  
  /**
   * Create a modularity graph visualization
   */
  createModularityGraph(options?: VisualizationOptions): VisualizationGraph {
    const nodes: VisualizationNode[] = [];
    const edges: VisualizationEdge[] = [];
    
    // Add nodes for all functions
    for (const func of this.codebase.functions) {
      nodes.push({
        id: `${func.filepath}:${func.name}`,
        label: func.name,
        type: 'function',
        data: {
          filepath: func.filepath
        },
        color: '#10b981', // green
        shape: 'circle'
      });
    }
    
    // Add edges for shared dependencies
    let edgeId = 0;
    for (const func of this.codebase.functions) {
      for (const dep of func.dependencies) {
        // Find other functions that depend on the same symbol
        for (const otherFunc of this.codebase.functions) {
          if (otherFunc.name !== func.name) {
            const hasSameDep = otherFunc.dependencies.some(
              otherDep => otherDep.name === dep.name
            );
            
            if (hasSameDep) {
              edges.push({
                id: `edge_${edgeId++}`,
                source: `${func.filepath}:${func.name}`,
                target: `${otherFunc.filepath}:${otherFunc.name}`,
                type: 'shared_dependency',
                data: {
                  dependency: dep.name
                },
                style: 'dashed',
                color: '#6b7280' // gray
              });
            }
          }
        }
      }
    }
    
    return { nodes, edges };
  }
  
  /**
   * Create a code structure visualization
   */
  createCodeStructureVisualization(options?: VisualizationOptions): VisualizationGraph {
    const nodes: VisualizationNode[] = [];
    const edges: VisualizationEdge[] = [];
    
    // Add a root node for the codebase
    nodes.push({
      id: 'codebase',
      label: 'Codebase',
      type: 'codebase',
      color: '#3b82f6', // blue
      size: 30,
      shape: 'hexagon'
    });
    
    // Add nodes for directories
    const directories = new Set<string>();
    for (const file of this.codebase.files) {
      const dirPath = file.path.substring(0, file.path.lastIndexOf('/'));
      if (dirPath && !directories.has(dirPath)) {
        directories.add(dirPath);
        nodes.push({
          id: dirPath,
          label: dirPath.substring(dirPath.lastIndexOf('/') + 1),
          type: 'directory',
          color: '#8b5cf6', // purple
          size: 20,
          shape: 'square'
        });
        
        // Connect to parent directory or codebase
        const parentPath = dirPath.substring(0, dirPath.lastIndexOf('/'));
        edges.push({
          id: `dir_edge_${directories.size}`,
          source: parentPath || 'codebase',
          target: dirPath,
          type: 'contains',
          style: 'solid',
          color: '#6b7280' // gray
        });
      }
    }
    
    // Add nodes for files
    for (const file of this.codebase.files) {
      nodes.push({
        id: file.path,
        label: file.name,
        type: 'file',
        color: '#10b981', // green
        size: 15,
        shape: 'square'
      });
      
      // Connect to directory
      const dirPath = file.path.substring(0, file.path.lastIndexOf('/'));
      edges.push({
        id: `file_edge_${nodes.length}`,
        source: dirPath || 'codebase',
        target: file.path,
        type: 'contains',
        style: 'solid',
        color: '#6b7280' // gray
      });
    }
    
    return { nodes, edges };
  }
  
  /**
   * Create a custom visualization
   */
  createCustomVisualization(
    nodeSelector: (item: any) => boolean,
    edgeSelector: (source: any, target: any) => boolean,
    options?: VisualizationOptions
  ): VisualizationGraph {
    const nodes: VisualizationNode[] = [];
    const edges: VisualizationEdge[] = [];
    
    // Add nodes for all matching items
    const allItems = [
      ...this.codebase.functions,
      ...this.codebase.classes,
      ...this.codebase.files
    ];
    
    const selectedItems = allItems.filter(nodeSelector);
    
    for (const item of selectedItems) {
      let type = 'unknown';
      if ('parameters' in item) type = 'function';
      else if ('methods' in item) type = 'class';
      else if ('content' in item) type = 'file';
      
      nodes.push({
        id: 'filepath' in item ? `${item.filepath}:${item.name}` : item.path,
        label: item.name,
        type: type,
        data: item,
        color: '#3b82f6', // blue
        size: 15,
        shape: 'circle'
      });
    }
    
    // Add edges between matching items
    let edgeId = 0;
    for (const source of selectedItems) {
      for (const target of selectedItems) {
        if (source !== target && edgeSelector(source, target)) {
          const sourceId = 'filepath' in source ? `${source.filepath}:${source.name}` : source.path;
          const targetId = 'filepath' in target ? `${target.filepath}:${target.name}` : target.path;
          
          edges.push({
            id: `edge_${edgeId++}`,
            source: sourceId,
            target: targetId,
            type: 'custom',
            style: 'solid',
            color: '#6b7280' // gray
          });
        }
      }
    }
    
    return { nodes, edges };
  }
  
  /**
   * Calculate complexity of a function (helper method)
   */
  private calculateComplexity(func: Function): number {
    // This would analyze the function's code to determine cyclomatic complexity
    // Simplified implementation for demonstration
    return 1;
  }
}

/**
 * Factory function to create all three main components
 */
export function createGraphSitterClient(codebase: Codebase) {
  return {
    analysis: new Analysis(codebase),
    manipulation: new Manipulation(codebase),
    visualization: new Visualization(codebase)
  };
}
