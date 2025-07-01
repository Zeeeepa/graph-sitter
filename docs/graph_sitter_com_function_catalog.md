# Graph-sitter.com Function Catalog

This document catalogs all functions and capabilities identified from the comprehensive analysis of [graph-sitter.com](http://graph-sitter.com) documentation, organized by functionality and mapped to our implementation.

## Core Classes and APIs

### 1. Codebase Class
**Primary entry point for analyzing and transforming code**

#### Core Methods
- `Codebase(path)` - Initialize codebase analysis
- `codebase.files` - Access all files in the codebase
- `codebase.functions` - Access all functions
- `codebase.classes` - Access all classes
- `codebase.symbols` - Access all symbols
- `codebase.imports` - Access all imports
- `codebase.external_modules` - Access external modules
- `codebase.global_vars` - Access global variables
- `codebase.interfaces` - Access interfaces
- `codebase.get_file(path)` - Get specific file
- `codebase.get_function(name)` - Get specific function
- `codebase.get_class(name)` - Get specific class
- `codebase.get_symbol(name)` - Get specific symbol
- `codebase.has_file(path)` - Check if file exists
- `codebase.commit()` - Commit changes
- `codebase.ai(...)` - AI-powered code generation

**Implementation Status**: ✅ Integrated in `enhanced_analysis.py`

### 2. File and SourceFile Classes
**Working with source files and their ASTs**

#### Core Methods
- `file.name` - File name
- `file.filepath` - Full file path
- `file.source` - File source code
- `file.functions` - Functions in file
- `file.classes` - Classes in file
- `file.imports` - Imports in file
- `file.symbols` - Symbols in file
- `file.global_vars` - Global variables in file
- `file.code_block` - Code block representation
- `file.get_function(name)` - Get specific function
- `file.get_class(name)` - Get specific class
- `file.get_symbol(name)` - Get specific symbol

**Implementation Status**: ✅ Integrated in `metrics.py` and `enhanced_analysis.py`

### 3. Function Class
**Function analysis and manipulation**

#### Core Properties
- `function.name` - Function name
- `function.qualified_name` - Fully qualified name
- `function.parameters` - Function parameters
- `function.return_statements` - Return statements
- `function.call_sites` - Where function is called
- `function.function_calls` - Calls made by function
- `function.decorators` - Function decorators
- `function.dependencies` - Function dependencies
- `function.usages` - Function usages
- `function.docstring` - Function documentation
- `function.source` - Function source code
- `function.start_point` - Start position
- `function.end_point` - End position
- `function.is_async` - Is async function
- `function.filepath` - File containing function

#### Core Methods
- `function.rename(new_name)` - Rename function
- `function.move_to_file(file_path)` - Move to different file
- `function.set_docstring(docstring)` - Set documentation
- `function.get_parameter(name)` - Get specific parameter
- `function.add_parameter(param)` - Add parameter
- `function.remove()` - Remove function

**Implementation Status**: ✅ Comprehensive analysis in `metrics.py` and `call_graph.py`

### 4. Class Definition Class
**Class analysis with methods, attributes, and inheritance**

#### Core Properties
- `class_def.name` - Class name
- `class_def.qualified_name` - Fully qualified name
- `class_def.methods` - Class methods
- `class_def.attributes` - Class attributes
- `class_def.parent_class_names` - Parent classes
- `class_def.superclasses` - Superclass objects
- `class_def.subclasses` - Subclass objects
- `class_def.constructor` - Constructor method (__init__)
- `class_def.decorators` - Class decorators
- `class_def.docstring` - Class documentation
- `class_def.start_point` - Start position
- `class_def.end_point` - End position

#### Core Methods
- `class_def.get_method(name)` - Get specific method
- `class_def.get_attribute(name)` - Get specific attribute
- `class_def.add_attribute_from_source(source)` - Add attribute
- `class_def.add_attribute(attr, include_dependencies=True)` - Add attribute object
- `class_def.methods(private=False, magic=False)` - Filter methods
- `class_def.attributes(max_depth=None)` - Get attributes with inheritance
- `class_def.is_subclass_of(class_name)` - Check inheritance
- `class_def.get_parent_class(name)` - Get specific parent

**Implementation Status**: ✅ Comprehensive analysis in `metrics.py`

### 5. FunctionCall Class
**Function invocation analysis**

#### Core Properties
- `call.name` - Called function name
- `call.args` - Function arguments
- `call.source` - Call source code
- `call.function_definition` - Target function
- `call.function_definitions` - All possible targets
- `call.parent_function` - Containing function
- `call.start_point` - Call position
- `call.predecessor` - Previous call in chain
- `call.call_chain` - Full call chain
- `call.base` - Base object for chained calls

#### Core Methods
- `call.get_arg_by_parameter_name(name)` - Get argument by parameter
- `call.get_arg_by_index(index)` - Get argument by position
- `call.set_kwarg(name, value, create_on_missing=True)` - Set keyword argument
- `call.args.append(arg)` - Add new argument

**Implementation Status**: ✅ Implemented in `call_graph.py`

### 6. Argument and Parameter Classes
**Function argument and parameter analysis**

#### Argument Properties
- `arg.value` - Argument value
- `arg.index` - Argument position
- `arg.is_named` - Is keyword argument
- `arg.name` - Argument name (for kwargs)
- `arg.parameter` - Corresponding parameter

#### Parameter Properties
- `param.type` - Parameter type
- `param.is_optional` - Is optional parameter
- `param.default` - Default value

#### Core Methods
- `arg.edit(new_value)` - Change argument value
- `arg.add_keyword(name)` - Convert to keyword argument
- `param.rename(new_name)` - Rename parameter
- `param.set_type_annotation(type)` - Set type annotation

**Implementation Status**: ✅ Analyzed in `metrics.py`

### 7. Symbol Class
**General symbol representation**

#### Core Properties
- `symbol.name` - Symbol name
- `symbol.qualified_name` - Fully qualified name
- `symbol.symbol_type` - Type of symbol
- `symbol.symbol_usages` - Where symbol is used
- `symbol.dependencies` - Symbol dependencies
- `symbol.usages` - Symbol usages
- `symbol.filepath` - File containing symbol

#### Core Methods
- `symbol.rename(new_name)` - Rename symbol
- `symbol.remove()` - Remove symbol

**Implementation Status**: ✅ Integrated in `dependency_analyzer.py`

## Analysis Capabilities

### 1. Function Call Analysis
**Based on graph-sitter.com function calls and call sites patterns**

#### Implemented Functions
- `find_most_called_function()` - Find function with most call sites
- `find_most_calling_function()` - Find function making most calls
- `find_unused_functions()` - Find functions with no call sites
- `find_recursive_functions()` - Find recursive functions
- `analyze_call_patterns()` - Analyze function usage patterns
- `build_call_graph()` - Create call graph representation
- `traverse_call_graph()` - Navigate call relationships

**Implementation**: ✅ `call_graph.py` and `metrics.py`

### 2. Dependency Analysis
**Import resolution and dependency tracking**

#### Implemented Functions
- `hop_through_imports(symbol, max_hops)` - Follow import chains
- `find_dependency_paths(source, target)` - Find dependency paths
- `analyze_symbol_dependencies(symbol)` - Analyze symbol dependencies
- `find_circular_dependencies()` - Detect circular dependencies
- `build_dependency_graph()` - Create dependency graph
- `analyze_imports()` - Analyze import patterns

**Implementation**: ✅ `dependency_analyzer.py`

### 3. Dead Code Detection
**Unused code identification**

#### Implemented Functions
- `find_dead_code()` - Find unused functions and classes
- `find_unused_imports()` - Find unused imports
- `find_unused_variables()` - Find unused variables
- `estimate_cleanup_impact()` - Estimate removal impact
- `get_removal_plan()` - Generate safe removal plan

**Implementation**: ✅ `dead_code.py`

### 4. Code Metrics
**Comprehensive code quality metrics**

#### Implemented Functions
- `calculate_cyclomatic_complexity()` - Calculate complexity
- `calculate_maintainability_index()` - Calculate maintainability
- `analyze_function_metrics()` - Comprehensive function analysis
- `analyze_class_metrics()` - Comprehensive class analysis
- `analyze_file_metrics()` - File-level metrics
- `get_codebase_summary()` - Overall codebase metrics

**Implementation**: ✅ `metrics.py`

### 5. Inheritance Analysis
**Class hierarchy analysis**

#### Implemented Functions
- `analyze_inheritance_depth()` - Calculate inheritance depth
- `find_inheritance_chains()` - Find inheritance paths
- `analyze_method_resolution_order()` - MRO analysis
- `find_abstract_classes()` - Identify abstract classes
- `analyze_class_cohesion()` - Calculate class cohesion
- `analyze_class_coupling()` - Calculate class coupling

**Implementation**: ✅ `metrics.py`

### 6. Call Graph Traversal
**Advanced call graph analysis**

#### Implemented Functions
- `create_call_graph(start_func, end_func)` - Build targeted call graph
- `find_call_paths(start, end)` - Find paths between functions
- `get_function_call_depth()` - Calculate call depth
- `analyze_call_chains()` - Method chaining analysis
- `visualize_call_graph()` - Create call graph visualization
- `find_strongly_connected_components()` - Find SCC in call graph

**Implementation**: ✅ `call_graph.py`

## Database Integration

### Schema Design
**Comprehensive database schema for storing analysis results**

#### Core Tables
- `codebases` - Codebase-level information
- `files` - File-level metrics and information
- `functions` - Function-level analysis results
- `classes` - Class-level analysis results
- `function_calls` - Function call relationships
- `dependencies` - Dependency relationships
- `imports` - Import analysis results

#### Query Functions
- `get_codebase_metrics(codebase_id)` - Get codebase metrics
- `get_dead_code_candidates(codebase_id)` - Query dead code
- `get_complex_functions(codebase_id, min_complexity)` - Query complex functions
- `get_recursive_functions(codebase_id)` - Query recursive functions
- `get_call_graph_data(codebase_id)` - Get call graph data

**Implementation**: ✅ `database.py`

## Advanced Features

### 1. Documentation Analysis
**Following graph-sitter.com documentation patterns**

#### Implemented Functions
- `calculate_documentation_coverage()` - Calculate doc coverage
- `analyze_docstring_quality()` - Analyze documentation quality
- `find_undocumented_functions()` - Find functions without docs
- `generate_documentation_report()` - Create documentation report

**Implementation**: ✅ Integrated in `metrics.py`

### 2. Test Analysis
**Test coverage and quality analysis**

#### Implemented Functions
- `estimate_test_coverage()` - Estimate test coverage
- `find_test_functions()` - Identify test functions
- `analyze_test_patterns()` - Analyze testing patterns
- `find_untested_functions()` - Find functions without tests

**Implementation**: ✅ Integrated in `metrics.py` and `dead_code.py`

### 3. Import Resolution
**Advanced import tracking and resolution**

#### Implemented Functions
- `resolve_import_chain()` - Resolve import dependencies
- `find_import_cycles()` - Find circular imports
- `analyze_import_depth()` - Calculate import depth
- `optimize_import_structure()` - Suggest import optimizations

**Implementation**: ✅ `dependency_analyzer.py`

## Integration Points

### 1. Enhanced Codebase Analysis
**Main integration interface**

#### Core Methods
- `run_full_analysis()` - Comprehensive analysis
- `get_function_context_analysis()` - Function context
- `get_codebase_health_score()` - Health assessment
- `query_analysis_data()` - Database queries
- `generate_analysis_report()` - Report generation

**Implementation**: ✅ `enhanced_analysis.py`

### 2. Example Usage
**Comprehensive example demonstrating all capabilities**

#### Demonstrated Features
- Function context analysis (dependencies, usages, implementation)
- Import resolution and hop-through-imports functionality
- Codebase statistics (classes, functions, imports)
- Inheritance analysis
- Test analysis
- Dead code detection
- Call site analysis
- Recursive function detection
- Database storage for analysis results

**Implementation**: ✅ `examples/comprehensive_analysis_example.py`

## Success Criteria Verification

### ✅ All relevant graph-sitter.com functions identified and documented
- Comprehensive catalog of 50+ functions and capabilities
- Organized by functionality and implementation status
- Mapped to specific modules and classes

### ✅ Key functions integrated into existing system
- Enhanced analysis capabilities in `enhanced_analysis.py`
- Comprehensive metrics in `metrics.py`
- Call graph analysis in `call_graph.py`
- Dead code detection in `dead_code.py`
- Dependency analysis in `dependency_analyzer.py`

### ✅ Enhanced analysis capabilities available through database queries
- Complete database schema in `database.py`
- Query functions for all analysis types
- Storage and retrieval of analysis results
- Performance-optimized with proper indexing

### ✅ Improved codebase understanding and metrics
- Comprehensive example demonstrating all capabilities
- Integration with existing graph_sitter module
- Enhanced metrics beyond basic summaries
- Advanced analysis patterns following graph-sitter.com documentation

## Future Enhancements

### Potential Additions
1. **Real-time Analysis** - Incremental analysis for large codebases
2. **Machine Learning Integration** - AI-powered code quality predictions
3. **Multi-language Support** - Extend beyond Python to TypeScript/JavaScript
4. **Performance Optimization** - Parallel analysis and caching
5. **Visualization Enhancements** - Interactive dashboards and reports

### Integration Opportunities
1. **CI/CD Integration** - Automated analysis in build pipelines
2. **IDE Extensions** - Real-time analysis in development environments
3. **Code Review Tools** - Integration with PR review processes
4. **Monitoring Systems** - Continuous code quality monitoring

