# Codebase Analyzer

A collection of utility functions for analyzing and manipulating codebases, focusing on call graphs, modularity, and type coverage.

## Utility Functions

### Call Graph Analysis

1. **find_all_paths_between_functions**
   * Find all possible paths between two functions in the call graph
   * Useful for understanding how functions are connected and tracing execution paths

2. **get_max_call_chain**
   * Find the longest call chain in the codebase starting from a given function
   * Helps identify complex execution flows and potential refactoring opportunities

### Code Modularity

3. **organize_imports**
   * Organize imports in a file by type (standard library, third-party, local) and name
   * Improves code readability and maintainability

4. **extract_shared_code**
   * Extract shared code into common modules
   * Reduces duplication and improves code organization

5. **determine_appropriate_shared_module**
   * Determine the appropriate module for shared code based on symbol characteristics
   * Ensures consistent organization of shared code

6. **break_circular_dependencies**
   * Break circular dependencies by extracting shared code into separate modules
   * Improves code architecture and prevents import-related issues

7. **analyze_module_coupling**
   * Analyze coupling between modules to identify highly connected components
   * Helps identify areas for refactoring to improve modularity

### Type Coverage

8. **calculate_type_coverage_percentages**
   * Calculate type coverage percentages across the codebase
   * Provides insights into type annotation completeness for parameters, return types, and attributes

## Usage Examples

```python
# Find all paths between two functions
start_func = codebase.get_function("create_skill")
end_func = codebase.get_function("auto_define_skill_description")
paths = find_all_paths_between_functions(start_func, end_func)
for path in paths:
    print(" -> ".join([func.name for func in path]))

# Get the longest call chain
main_func = codebase.get_function("main")
longest_chain = get_max_call_chain(main_func)
print("Longest call chain:")
print(" -> ".join([func.name for func in longest_chain]))

# Organize imports in a file
file = codebase.get_file("app/main.py")
organize_imports(file)

# Extract shared code
extracted = extract_shared_code(codebase, min_usages=4)
for module, symbols in extracted.items():
    print(f"Extracted {len(symbols)} symbols to {module}")

# Break circular dependencies
broken_cycles = break_circular_dependencies(codebase)
print(f"Broke {len(broken_cycles)} circular dependencies")

# Analyze module coupling
coupling = analyze_module_coupling(codebase)
for file_path, metrics in sorted(coupling.items(), key=lambda x: x[1]['score'], reverse=True)[:5]:
    print(f"{file_path}: {metrics['score']} connections")

# Calculate type coverage
coverage = calculate_type_coverage_percentages(codebase)
print(f"Parameter type coverage: {coverage['parameters']['percentage']:.1f}%")
print(f"Return type coverage: {coverage['returns']['percentage']:.1f}%")
print(f"Attribute type coverage: {coverage['attributes']['percentage']:.1f}%")
```

## Requirements

- NetworkX for graph operations
- A codebase object with appropriate attributes and methods

## Notes

These utility functions are designed to work with a codebase analysis framework that provides access to code structure through objects representing files, functions, classes, and symbols. The functions include error handling and fallbacks for cases where expected attributes or methods might not be available.

