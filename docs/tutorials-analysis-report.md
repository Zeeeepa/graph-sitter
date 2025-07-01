# Graph-sitter Tutorials Section Analysis Report

## Executive Summary

This comprehensive analysis of Graph-sitter's tutorials section reveals a mature codebase analysis and transformation framework with 28 detailed tutorials covering practical applications from basic visualization to complex API migrations. The tutorials demonstrate sophisticated capabilities for dead code detection, error pattern identification, and automated refactoring workflows.

## Tutorial Categories Overview

### Featured Tutorials (Core Capabilities)

#### 1. **Codebase Visualization** 
- **Primary Functions**: `Codebase()`, `create_downstream_call_trace()`, `create_dependencies_visualization()`, `create_blast_radius_visualization()`
- **Key Analysis Capabilities**:
  - Call trace visualization with recursive traversal
  - Function dependency graph generation
  - Blast radius analysis for impact assessment
  - NetworkX integration for graph operations
- **Error Detection Patterns**:
  - Circular dependency identification
  - Tight coupling detection
  - Critical path analysis
- **Code Examples**:
  ```python
  # Call trace visualization
  def create_downstream_call_trace(src_func: Function, depth: int = 0):
      for call in src_func.function_calls:
          func = call.function_definition
          if func and isinstance(func, Function):
              G.add_node(func, name=func_name, color=COLOR_PALETTE.get(func.__class__.__name__))
              G.add_edge(src_func, func, **generate_edge_meta(call))
              create_downstream_call_trace(func, depth + 1)
  ```

#### 2. **Delete Dead Code**
- **Primary Functions**: `function.usages`, `function.remove()`, `function.call_sites`, `codebase.commit()`
- **Key Analysis Capabilities**:
  - Unused function detection via `function.usages` analysis
  - Unused variable identification through `local_var_assignments.local_usages`
  - Safe removal with automatic import updates
  - Special case filtering (tests, decorators, endpoints)
- **Error Detection Patterns**:
  - Zero-usage symbol identification
  - Orphaned import detection
  - Empty file cleanup
- **Code Examples**:
  ```python
  # Dead code detection with filtering
  for function in codebase.functions:
      if "test" in function.file.filepath:
          continue
      if function.decorators:
          continue
      if not function.usages and not function.call_sites:
          function.remove()
  ```

#### 3. **Mine Training Data**
- **Primary Functions**: `function.dependencies`, `function.usages`, `hop_through_imports()`, `codebase.ai()`
- **Key Analysis Capabilities**:
  - Function context extraction (implementation + dependencies + usages)
  - Import chain resolution through `hop_through_imports()`
  - Structured training data generation for LLMs
  - Node2vec-style code embeddings
- **Error Detection Patterns**:
  - Import resolution validation
  - Context completeness verification
- **Code Examples**:
  ```python
  # Training data extraction
  def get_function_context(function) -> dict:
      context = {
          "implementation": {"source": function.source, "filepath": function.filepath},
          "dependencies": [],
          "usages": [],
      }
      for dep in function.dependencies:
          if isinstance(dep, Import):
              dep = hop_through_imports(dep)
          context["dependencies"].append({"source": dep.source, "filepath": dep.filepath})
  ```

### API Migration Tutorials

#### 4. **SQLAlchemy 1.4 to 2.0 Migration**
- **Primary Functions**: `call.set_name()`, `call.args`, `chain.edit()`, `file.function_calls`
- **Key Analysis Capabilities**:
  - Query pattern transformation (query() → select())
  - Method chain analysis and conversion
  - Session execution pattern updates
- **Error Detection Patterns**:
  - Legacy API usage identification
  - Incompatible pattern detection
- **Code Examples**:
  ```python
  # Query to select conversion
  for call in file.function_calls:
      if call.name == "query":
          call.set_name("select")
          if call.parent and call.parent.is_method_chain:
              chain = call.parent
              if "filter" in chain.source:
                  chain.source = chain.source.replace(".filter(", ".where(")
  ```

#### 5. **Flask to FastAPI Migration**
- **Primary Functions**: `imp.set_name()`, `imp.set_module()`, `decorator.edit()`, `file.add_import()`
- **Key Analysis Capabilities**:
  - Import statement transformation
  - Route decorator conversion
  - Static file handling setup
  - Template rendering updates
- **Error Detection Patterns**:
  - Framework-specific pattern identification
  - Missing dependency detection
- **Code Examples**:
  ```python
  # Route decorator conversion
  for decorator in function.decorators:
      if "@app.route" in decorator.source:
          route = decorator.source.split('"')[1]
          method = "get"  # Default
          if "methods=" in decorator.source:
              methods = decorator.source.split("methods=")[1].split("]")[0]
              if "post" in methods.lower():
                  method = "post"
          decorator.edit(f'@app.{method}("{route}")')
  ```

#### 6. **Python 2 to 3 Migration**
- **Primary Functions**: Print statement conversion, import updates, string handling
- **Key Analysis Capabilities**:
  - Syntax modernization
  - Import path updates
  - String/Unicode handling fixes

### Code Organization Tutorials

#### 7. **Organize Your Codebase**
- **Primary Functions**: `function.move_to_file()`, `codebase.create_file()`, `codebase.create_directory()`
- **Key Analysis Capabilities**:
  - Large file splitting with dependency tracking
  - Module organization by naming patterns
  - Import cycle detection and resolution
- **Error Detection Patterns**:
  - Circular dependency identification
  - Naming convention violations
- **Code Examples**:
  ```python
  # Module organization
  module_map = {
      "utils": lambda f: f.name.startswith("util_") or f.name.startswith("helper_"),
      "api": lambda f: f.name.startswith("api_") or f.name.startswith("endpoint_"),
      "data": lambda f: f.name.startswith("data_") or f.name.startswith("db_"),
  }
  for function in file.functions:
      target_module = next((module for module, condition in module_map.items() if condition(function)), "core")
      function.move_to_file(new_file, include_dependencies=True)
  ```

#### 8. **Improve Modularity**
- **Primary Functions**: `nx.simple_cycles()`, `symbol.move_to_file()`, coupling analysis
- **Key Analysis Capabilities**:
  - Import relationship analysis with NetworkX
  - Circular dependency breaking
  - Module coupling measurement
  - Shared code extraction
- **Error Detection Patterns**:
  - High coupling identification
  - Circular import detection
- **Code Examples**:
  ```python
  # Circular dependency detection
  def create_dependency_graph():
      G = nx.DiGraph()
      for file in codebase.files:
          G.add_node(file.filepath)
          for imp in file.imports:
              if imp.from_file:
                  G.add_edge(file.filepath, imp.from_file.filepath)
      return G
  
  cycles = list(nx.simple_cycles(graph))
  ```

#### 9. **Managing TypeScript Exports**
- **Primary Functions**: Export analysis, module boundary management
- **Key Analysis Capabilities**:
  - Export pattern optimization
  - Module interface cleanup

#### 10. **Converting Default Exports**
- **Primary Functions**: Export/import statement transformation
- **Key Analysis Capabilities**:
  - Default vs named export conversion
  - Import statement updates

### Testing & Types Tutorials

#### 11. **unittest to pytest Migration**
- **Primary Functions**: Class inheritance removal, assertion conversion, fixture setup
- **Key Analysis Capabilities**:
  - Test class to function conversion
  - Assertion method transformation
  - Fixture pattern modernization
- **Error Detection Patterns**:
  - Legacy test pattern identification
  - Incompatible assertion usage
- **Code Examples**:
  ```python
  # Assertion conversion patterns
  # From: self.assertEqual(user.name, "test")
  # To: assert user.name == "test"
  
  # From: self.assertRaises(ValueError, parse_user_id, "invalid")
  # To: with pytest.raises(ValueError): parse_user_id("invalid")
  ```

#### 12. **Increase Type Coverage**
- **Primary Functions**: `parameter.is_typed`, `function.set_return_type()`, `function.return_type`
- **Key Analysis Capabilities**:
  - Type coverage analysis across parameters, returns, and attributes
  - Simple type annotation addition
  - Type inference integration (planned)
- **Error Detection Patterns**:
  - Missing type annotations
  - Inconsistent typing patterns
- **Code Examples**:
  ```python
  # Type coverage analysis
  total_parameters = 0
  typed_parameters = 0
  for function in codebase.functions:
      total_parameters += len(function.parameters)
      typed_parameters += sum(1 for param in function.parameters if param.is_typed)
  
  # Adding return types
  for function in file.functions:
      if len(function.return_statements) == 0:
          function.set_return_type("None")
  ```

### Documentation & AI Tutorials

#### 13. **Creating Documentation**
- **Primary Functions**: `codebase.ai()`, `function.set_docstring()`, `function.docstring`
- **Key Analysis Capabilities**:
  - Documentation coverage analysis
  - AI-powered docstring generation
  - Directory-level documentation assessment
- **Error Detection Patterns**:
  - Missing documentation identification
  - Inconsistent documentation patterns
- **Code Examples**:
  ```python
  # Documentation coverage analysis
  total_functions = 0
  functions_with_docs = 0
  for function in codebase.functions:
      total_functions += 1
      if function.docstring:
          functions_with_docs += 1
  
  func_coverage = (functions_with_docs / total_functions * 100)
  ```

#### 14. **Preparing for AI**
- **Primary Functions**: `codebase.ai()`, hierarchical README generation
- **Key Analysis Capabilities**:
  - Automated directory documentation
  - Codebase structure explanation
  - AI-powered content generation
- **Error Detection Patterns**:
  - Missing structural documentation
  - Unclear module purposes

## Core Graph-sitter Functions Catalog

### Primary Analysis Functions

1. **Symbol Navigation**
   - `symbol.usages` - Find all usage locations
   - `symbol.dependencies` - Get symbol dependencies
   - `function.function_calls` - Get function call sites
   - `function.call_sites` - Get where function is called

2. **Code Transformation**
   - `symbol.remove()` - Safe symbol removal
   - `symbol.move_to_file()` - Move with dependency updates
   - `function.set_return_type()` - Add/update type annotations
   - `call.set_name()` - Rename function calls

3. **Import Management**
   - `file.imports` - Access import statements
   - `imp.set_name()` - Update import names
   - `imp.set_module()` - Change import modules
   - `hop_through_imports()` - Resolve import chains

4. **File Operations**
   - `codebase.create_file()` - Create new files
   - `codebase.create_directory()` - Create directories
   - `file.add_import()` - Add import statements
   - `codebase.commit()` - Persist changes

5. **AI Integration**
   - `codebase.ai()` - AI-powered analysis and generation
   - Context-aware code understanding
   - Automated documentation generation

### Error Detection Capabilities

1. **Dead Code Detection**
   - Zero-usage functions: `not function.usages`
   - Unused variables: `not var_assignment.local_usages`
   - Orphaned imports: Import without usage
   - Empty files: `not file.content.strip()`

2. **Dependency Issues**
   - Circular imports: `nx.simple_cycles(dependency_graph)`
   - High coupling: Usage count analysis
   - Missing dependencies: Import resolution failures

3. **Type Safety Issues**
   - Missing type annotations: `not parameter.is_typed`
   - Inconsistent typing: Type coverage analysis
   - Return type mismatches: Static analysis integration

4. **Code Quality Problems**
   - Naming convention violations: Pattern matching
   - Large file detection: Line count analysis
   - Complex function identification: Cyclomatic complexity

### Practical Applications for Codebase Health Analysis

1. **Maintenance Tasks**
   - Automated dead code removal
   - Import optimization
   - Documentation generation
   - Type annotation addition

2. **Refactoring Support**
   - Safe symbol moving
   - Module reorganization
   - API migration automation
   - Test modernization

3. **Quality Assurance**
   - Dependency cycle detection
   - Coupling analysis
   - Type coverage monitoring
   - Documentation coverage tracking

4. **Migration Assistance**
   - Framework upgrades (Flask→FastAPI)
   - Library updates (SQLAlchemy 1.4→2.0)
   - Language modernization (Python 2→3)
   - Testing framework migration (unittest→pytest)

## Advanced Features and Patterns

### Graph Analysis Integration
- NetworkX integration for dependency analysis
- Visualization capabilities with interactive graphs
- Blast radius analysis for change impact assessment

### AI-Powered Capabilities
- Context-aware code generation
- Automated documentation creation
- Intelligent refactoring suggestions
- Training data generation for LLMs

### Multi-Language Support
- Python and TypeScript/JavaScript support
- Language-agnostic patterns where possible
- Framework-specific transformations

## Conclusion

Graph-sitter's tutorial collection demonstrates a comprehensive codebase analysis and transformation framework with sophisticated capabilities for:

1. **Dead Code Detection**: Precise identification of unused code with intelligent filtering
2. **Error Pattern Recognition**: Systematic detection of common code quality issues
3. **Automated Refactoring**: Safe code transformations with dependency tracking
4. **Migration Automation**: Framework and library upgrade assistance
5. **Quality Analysis**: Type coverage, documentation coverage, and modularity assessment

The framework's strength lies in its combination of static analysis, graph-based dependency tracking, and AI integration, making it suitable for both automated maintenance tasks and complex codebase transformations.

