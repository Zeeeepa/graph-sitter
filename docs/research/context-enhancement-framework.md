# Context Enhancement Framework

## Overview

The Context Enhancement Framework is a core component of the enhanced autogenlib module that leverages graph_sitter's powerful codebase analysis capabilities to provide intelligent, context-aware code generation. This framework transforms raw codebase information into structured context that significantly improves the quality and relevance of generated code.

## Architecture Overview

```
Context Enhancement Framework
├── Codebase Analyzer
│   ├── Symbol Extraction
│   ├── Dependency Analysis
│   └── Pattern Recognition
├── Context Aggregator
│   ├── Relevance Scoring
│   ├── Context Filtering
│   └── Context Ranking
├── Prompt Enhancer
│   ├── Template Engine
│   ├── Context Injection
│   └── Prompt Optimization
└── Context Cache
    ├── Analysis Cache
    ├── Pattern Cache
    └── Template Cache
```

## Core Components

### 1. Codebase Analyzer

The Codebase Analyzer is responsible for extracting meaningful information from the codebase using graph_sitter's analysis capabilities.

#### Symbol Extraction
```python
class SymbolExtractor:
    """Extract and categorize symbols from codebase"""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        
    def extract_symbols(self, file_path: str) -> SymbolContext:
        """Extract symbols with their relationships and metadata"""
        
        file = self.codebase.get_file(file_path)
        if not file:
            return SymbolContext.empty()
            
        return SymbolContext(
            classes=self._extract_classes(file),
            functions=self._extract_functions(file),
            variables=self._extract_variables(file),
            imports=self._extract_imports(file),
            exports=self._extract_exports(file)
        )
        
    def _extract_classes(self, file: SourceFile) -> List[ClassInfo]:
        """Extract class definitions with methods and attributes"""
        classes = []
        for cls in file.classes:
            classes.append(ClassInfo(
                name=cls.name,
                methods=[m.name for m in cls.methods],
                attributes=[a.name for a in cls.attributes],
                parent_classes=cls.parent_class_names,
                decorators=[d.name for d in cls.decorators],
                docstring=cls.docstring,
                line_range=(cls.start_line, cls.end_line)
            ))
        return classes
        
    def _extract_functions(self, file: SourceFile) -> List[FunctionInfo]:
        """Extract function definitions with signatures and metadata"""
        functions = []
        for func in file.functions:
            functions.append(FunctionInfo(
                name=func.name,
                parameters=[p.name for p in func.parameters],
                return_type=func.return_type,
                decorators=[d.name for d in func.decorators],
                docstring=func.docstring,
                complexity=self._calculate_complexity(func),
                line_range=(func.start_line, func.end_line)
            ))
        return functions
```

#### Dependency Analysis
```python
class DependencyAnalyzer:
    """Analyze dependencies and relationships between code elements"""
    
    def analyze_dependencies(self, target_file: str, codebase: Codebase) -> DependencyContext:
        """Analyze dependencies for a target file"""
        
        file = codebase.get_file(target_file)
        
        return DependencyContext(
            direct_imports=self._get_direct_imports(file),
            transitive_dependencies=self._get_transitive_dependencies(file, codebase),
            dependents=self._get_dependents(file, codebase),
            circular_dependencies=self._detect_circular_dependencies(file, codebase)
        )
        
    def _get_direct_imports(self, file: SourceFile) -> List[ImportInfo]:
        """Get direct imports with their usage patterns"""
        imports = []
        for imp in file.imports:
            imports.append(ImportInfo(
                module=imp.module_name,
                symbols=imp.imported_symbols,
                alias=imp.alias,
                usage_count=self._count_symbol_usage(imp, file),
                import_type=imp.import_type
            ))
        return imports
        
    def _get_transitive_dependencies(self, file: SourceFile, codebase: Codebase) -> List[str]:
        """Get all transitive dependencies"""
        visited = set()
        dependencies = []
        
        def traverse_dependencies(current_file):
            if current_file.path in visited:
                return
            visited.add(current_file.path)
            
            for imp in current_file.imports:
                if imp.is_local_import:
                    dep_file = codebase.get_file(imp.resolved_path)
                    if dep_file:
                        dependencies.append(dep_file.path)
                        traverse_dependencies(dep_file)
                        
        traverse_dependencies(file)
        return dependencies
```

#### Pattern Recognition
```python
class PatternRecognizer:
    """Recognize architectural and coding patterns in the codebase"""
    
    def recognize_patterns(self, codebase: Codebase) -> PatternContext:
        """Identify common patterns and conventions"""
        
        return PatternContext(
            architectural_patterns=self._identify_architectural_patterns(codebase),
            naming_conventions=self._analyze_naming_conventions(codebase),
            coding_standards=self._extract_coding_standards(codebase),
            design_patterns=self._identify_design_patterns(codebase)
        )
        
    def _identify_architectural_patterns(self, codebase: Codebase) -> List[ArchitecturalPattern]:
        """Identify architectural patterns like MVC, Repository, etc."""
        patterns = []
        
        # Detect MVC pattern
        if self._has_mvc_structure(codebase):
            patterns.append(ArchitecturalPattern(
                name="MVC",
                confidence=0.9,
                evidence=self._get_mvc_evidence(codebase)
            ))
            
        # Detect Repository pattern
        if self._has_repository_pattern(codebase):
            patterns.append(ArchitecturalPattern(
                name="Repository",
                confidence=0.8,
                evidence=self._get_repository_evidence(codebase)
            ))
            
        return patterns
        
    def _analyze_naming_conventions(self, codebase: Codebase) -> NamingConventions:
        """Analyze naming conventions used in the codebase"""
        
        function_names = [f.name for file in codebase.files for f in file.functions]
        class_names = [c.name for file in codebase.files for c in file.classes]
        variable_names = [v.name for file in codebase.files for v in file.global_vars]
        
        return NamingConventions(
            function_style=self._detect_naming_style(function_names),
            class_style=self._detect_naming_style(class_names),
            variable_style=self._detect_naming_style(variable_names),
            constant_style=self._detect_constant_style(variable_names)
        )
```

### 2. Context Aggregator

The Context Aggregator combines information from multiple sources and applies relevance scoring to create focused context.

```python
class ContextAggregator:
    """Aggregate and filter context information for optimal prompt enhancement"""
    
    def __init__(self, max_context_size: int = 4000):
        self.max_context_size = max_context_size
        self.relevance_scorer = RelevanceScorer()
        
    def aggregate_context(self, 
                         target_module: str,
                         target_function: str,
                         caller_context: CallerContext,
                         codebase: Codebase) -> AggregatedContext:
        """Aggregate all relevant context for code generation"""
        
        # Extract base context
        symbol_context = self.symbol_extractor.extract_symbols(target_module)
        dependency_context = self.dependency_analyzer.analyze_dependencies(target_module, codebase)
        pattern_context = self.pattern_recognizer.recognize_patterns(codebase)
        
        # Find related code
        related_functions = self._find_related_functions(target_function, codebase)
        similar_implementations = self._find_similar_implementations(target_function, codebase)
        
        # Score relevance
        context_items = self._create_context_items(
            symbol_context, dependency_context, pattern_context,
            related_functions, similar_implementations, caller_context
        )
        
        scored_items = self.relevance_scorer.score_items(context_items, target_function)
        
        # Filter and rank
        filtered_items = self._filter_by_relevance(scored_items, threshold=0.3)
        ranked_items = self._rank_by_importance(filtered_items)
        
        # Ensure context size limits
        final_context = self._trim_to_size_limit(ranked_items)
        
        return AggregatedContext(
            target_module=target_module,
            target_function=target_function,
            context_items=final_context,
            total_relevance_score=sum(item.relevance_score for item in final_context)
        )
        
    def _find_related_functions(self, target_function: str, codebase: Codebase) -> List[FunctionInfo]:
        """Find functions that might be related to the target function"""
        
        related = []
        target_words = self._extract_words(target_function)
        
        for file in codebase.files:
            for func in file.functions:
                similarity = self._calculate_name_similarity(target_function, func.name)
                if similarity > 0.5:
                    related.append(FunctionInfo(
                        name=func.name,
                        file_path=file.path,
                        similarity_score=similarity,
                        implementation=func.body[:500]  # First 500 chars
                    ))
                    
        return sorted(related, key=lambda x: x.similarity_score, reverse=True)[:5]
```

### 3. Relevance Scorer

The Relevance Scorer determines how relevant each piece of context is for the specific generation task.

```python
class RelevanceScorer:
    """Score context items based on relevance to the generation task"""
    
    def score_items(self, context_items: List[ContextItem], target_function: str) -> List[ScoredContextItem]:
        """Score context items for relevance"""
        
        scored_items = []
        target_words = self._extract_words(target_function)
        
        for item in context_items:
            score = self._calculate_relevance_score(item, target_words)
            scored_items.append(ScoredContextItem(
                item=item,
                relevance_score=score,
                score_breakdown=self._get_score_breakdown(item, target_words)
            ))
            
        return scored_items
        
    def _calculate_relevance_score(self, item: ContextItem, target_words: List[str]) -> float:
        """Calculate relevance score using multiple factors"""
        
        scores = {
            'name_similarity': self._score_name_similarity(item, target_words),
            'usage_frequency': self._score_usage_frequency(item),
            'recency': self._score_recency(item),
            'complexity_match': self._score_complexity_match(item),
            'pattern_alignment': self._score_pattern_alignment(item)
        }
        
        # Weighted combination
        weights = {
            'name_similarity': 0.3,
            'usage_frequency': 0.2,
            'recency': 0.1,
            'complexity_match': 0.2,
            'pattern_alignment': 0.2
        }
        
        total_score = sum(scores[factor] * weights[factor] for factor in scores)
        return min(1.0, max(0.0, total_score))
```

### 4. Prompt Enhancer

The Prompt Enhancer takes the aggregated context and creates enhanced prompts for the Codegen SDK.

```python
class PromptEnhancer:
    """Enhance prompts with structured context information"""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self.context_formatter = ContextFormatter()
        
    def enhance_prompt(self, 
                      base_prompt: str,
                      aggregated_context: AggregatedContext,
                      generation_type: GenerationType) -> EnhancedPrompt:
        """Create an enhanced prompt with structured context"""
        
        template = self.template_engine.get_template(generation_type)
        formatted_context = self.context_formatter.format_context(aggregated_context)
        
        enhanced_prompt = template.render(
            base_request=base_prompt,
            target_module=aggregated_context.target_module,
            target_function=aggregated_context.target_function,
            existing_symbols=formatted_context.symbols,
            dependencies=formatted_context.dependencies,
            patterns=formatted_context.patterns,
            similar_implementations=formatted_context.similar_implementations,
            coding_standards=formatted_context.coding_standards,
            architectural_context=formatted_context.architectural_context
        )
        
        return EnhancedPrompt(
            prompt=enhanced_prompt,
            context_summary=self._create_context_summary(aggregated_context),
            estimated_tokens=self._estimate_token_count(enhanced_prompt),
            context_quality_score=aggregated_context.total_relevance_score
        )
```

### 5. Template Engine

The Template Engine manages different prompt templates for various generation scenarios.

```python
class TemplateEngine:
    """Manage prompt templates for different generation scenarios"""
    
    def __init__(self):
        self.templates = self._load_templates()
        
    def get_template(self, generation_type: GenerationType) -> Template:
        """Get appropriate template for generation type"""
        return self.templates.get(generation_type, self.templates['default'])
        
    def _load_templates(self) -> Dict[GenerationType, Template]:
        """Load all prompt templates"""
        
        templates = {}
        
        # Function generation template
        templates[GenerationType.FUNCTION] = Template("""
# Code Generation Request

## Target
Generate function `{{ target_function }}` in module `{{ target_module }}`

## Base Request
{{ base_request }}

## Codebase Context

### Existing Symbols in Module
{% for symbol in existing_symbols %}
- {{ symbol.type }}: {{ symbol.name }}
  {% if symbol.signature %}Signature: {{ symbol.signature }}{% endif %}
  {% if symbol.docstring %}Purpose: {{ symbol.docstring[:100] }}...{% endif %}
{% endfor %}

### Dependencies
{% for dep in dependencies %}
- {{ dep.module }}: {{ dep.symbols|join(', ') }}
{% endfor %}

### Similar Implementations
{% for impl in similar_implementations %}
#### {{ impl.name }} (similarity: {{ impl.similarity_score }})
```python
{{ impl.implementation }}
```
{% endfor %}

### Architectural Patterns
{% for pattern in patterns %}
- {{ pattern.name }} (confidence: {{ pattern.confidence }})
{% endfor %}

### Coding Standards
- Function naming: {{ coding_standards.function_style }}
- Documentation: {{ coding_standards.docstring_style }}
- Type hints: {{ coding_standards.type_hint_usage }}

## Requirements
1. Follow the established coding patterns and naming conventions
2. Use appropriate type hints based on codebase standards
3. Include proper documentation following the project's style
4. Consider the existing architectural patterns
5. Ensure compatibility with existing dependencies
""")
        
        # Class generation template
        templates[GenerationType.CLASS] = Template("""
# Class Generation Request

## Target
Generate class `{{ target_function }}` in module `{{ target_module }}`

## Base Request
{{ base_request }}

## Codebase Context

### Existing Classes in Module
{% for cls in existing_symbols.classes %}
- {{ cls.name }}
  Methods: {{ cls.methods|join(', ') }}
  Attributes: {{ cls.attributes|join(', ') }}
  {% if cls.parent_classes %}Inherits from: {{ cls.parent_classes|join(', ') }}{% endif %}
{% endfor %}

### Class Hierarchies
{% for hierarchy in architectural_context.class_hierarchies %}
{{ hierarchy.description }}
{% endfor %}

### Design Patterns
{% for pattern in patterns %}
- {{ pattern.name }}: {{ pattern.description }}
{% endfor %}

## Requirements
1. Follow established inheritance patterns
2. Use consistent method naming and structure
3. Include appropriate class documentation
4. Consider existing design patterns
5. Maintain architectural consistency
""")
        
        return templates
```

## Context Quality Metrics

### Relevance Scoring
- **Name Similarity**: 0.0-1.0 based on semantic similarity
- **Usage Frequency**: 0.0-1.0 based on how often similar patterns are used
- **Recency**: 0.0-1.0 based on how recently the code was modified
- **Complexity Match**: 0.0-1.0 based on complexity similarity
- **Pattern Alignment**: 0.0-1.0 based on architectural pattern consistency

### Context Quality Indicators
- **Coverage**: Percentage of relevant context included
- **Precision**: Percentage of included context that is relevant
- **Completeness**: Whether all necessary context types are included
- **Coherence**: How well the context pieces work together

## Performance Optimization

### Caching Strategy
```python
class ContextCache:
    """Multi-level caching for context analysis results"""
    
    def __init__(self):
        self.analysis_cache = LRUCache(maxsize=1000)  # File analysis results
        self.pattern_cache = LRUCache(maxsize=100)    # Pattern recognition results
        self.template_cache = LRUCache(maxsize=50)    # Rendered templates
        
    async def get_analysis(self, file_path: str, file_hash: str) -> Optional[AnalysisResult]:
        """Get cached analysis result if file hasn't changed"""
        cache_key = f"{file_path}:{file_hash}"
        return self.analysis_cache.get(cache_key)
        
    async def cache_analysis(self, file_path: str, file_hash: str, result: AnalysisResult):
        """Cache analysis result with file hash for invalidation"""
        cache_key = f"{file_path}:{file_hash}"
        self.analysis_cache[cache_key] = result
```

### Incremental Analysis
```python
class IncrementalAnalyzer:
    """Perform incremental analysis for better performance"""
    
    def analyze_changes(self, changed_files: List[str], codebase: Codebase) -> ContextUpdate:
        """Analyze only changed files and their dependencies"""
        
        affected_files = self._find_affected_files(changed_files, codebase)
        
        updates = ContextUpdate()
        for file_path in affected_files:
            if self._needs_reanalysis(file_path):
                new_analysis = self._analyze_file(file_path, codebase)
                updates.add_file_update(file_path, new_analysis)
                
        return updates
```

## Integration with Autogenlib

### Context Provider Interface
```python
class ContextProvider:
    """Main interface for providing context to autogenlib"""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.analyzer = CodebaseAnalyzer(codebase)
        self.aggregator = ContextAggregator()
        self.enhancer = PromptEnhancer()
        
    async def get_enhanced_prompt(self,
                                 module_path: str,
                                 function_name: str,
                                 base_prompt: str,
                                 caller_context: CallerContext) -> EnhancedPrompt:
        """Get enhanced prompt with full context analysis"""
        
        # Aggregate context
        context = await self.aggregator.aggregate_context(
            module_path, function_name, caller_context, self.codebase
        )
        
        # Enhance prompt
        enhanced_prompt = self.enhancer.enhance_prompt(
            base_prompt, context, GenerationType.FUNCTION
        )
        
        return enhanced_prompt
```

## Conclusion

The Context Enhancement Framework provides a sophisticated system for transforming raw codebase information into actionable context for code generation. By leveraging graph_sitter's analysis capabilities and applying intelligent filtering and ranking, the framework ensures that generated code is contextually appropriate, follows established patterns, and integrates seamlessly with existing codebases.

The framework's modular design allows for easy extension and customization, while its caching and incremental analysis capabilities ensure optimal performance even with large codebases. This foundation enables autogenlib to generate higher-quality code that truly understands and respects the existing codebase structure and conventions.

