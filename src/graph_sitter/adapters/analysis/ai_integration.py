"""
🤖 AI Integration and Automated Analysis

AI-powered code analysis, improvement suggestions, and automated issue detection:
- Automated code analysis with contextual understanding
- Intelligent improvement suggestions and refactoring recommendations
- Documentation generation and code explanation
- Issue detection with automatic context retrieval
- Integration with existing codebase_ai.py functionality
- Batch processing for large codebases

Leverages AI to provide intelligent insights and automated code improvements.
"""

import json
import traceback
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set, Union, Callable
from pathlib import Path

try:
    from graph_sitter.core.class_definition import Class
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.function import Function
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.enums import EdgeType, SymbolType
except ImportError:
    print("Warning: Graph-sitter modules not available. Some functionality may be limited.")
    Class = object
    Codebase = object
    Function = object


@dataclass
class AIAnalysisResult:
    """Result of AI-powered analysis"""
    analysis_type: str
    target: str
    suggestions: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    documentation: str = ""
    confidence: float = 0.0
    context_used: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IssueDetectionResult:
    """Result of automated issue detection"""
    issue_type: str
    severity: str  # critical, high, medium, low
    message: str
    location: str
    function_name: str = ""
    class_name: str = ""
    suggested_fix: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    auto_fixable: bool = False


@dataclass
class ImprovementSuggestion:
    """Code improvement suggestion"""
    suggestion_type: str
    title: str
    description: str
    code_before: str = ""
    code_after: str = ""
    impact: str = "medium"  # low, medium, high
    effort: str = "medium"  # low, medium, high
    benefits: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)


class AIAnalyzer:
    """
    AI-powered code analyzer with contextual understanding
    """
    
    def __init__(self, ai_provider: Optional[Any] = None, config: Optional[Dict] = None):
        self.ai_provider = ai_provider
        self.config = config or {}
        self.analysis_cache = {}
        self.context_extractors = self._initialize_context_extractors()
    
    def _initialize_context_extractors(self) -> Dict[str, Callable]:
        """Initialize context extraction functions"""
        return {
            'function_context': self._extract_function_context,
            'class_context': self._extract_class_context,
            'file_context': self._extract_file_context,
            'dependency_context': self._extract_dependency_context,
            'usage_context': self._extract_usage_context
        }
    
    def analyze_function(self, function: Function, analysis_type: str = "comprehensive") -> AIAnalysisResult:
        """Analyze a function with AI assistance"""
        try:
            # Extract comprehensive context
            context = self._extract_function_context(function)
            
            # Prepare analysis prompt
            prompt = self._prepare_function_analysis_prompt(function, context, analysis_type)
            
            # Get AI analysis (mock implementation)
            ai_response = self._get_ai_analysis(prompt, context)
            
            # Parse and structure the response
            result = self._parse_ai_response(ai_response, "function", function.name)
            result.context_used = context
            
            return result
            
        except Exception as e:
            print(f"Error analyzing function {function.name}: {e}")
            return AIAnalysisResult(
                analysis_type=analysis_type,
                target=function.name,
                issues=[{"type": "analysis_error", "message": str(e)}]
            )
    
    def analyze_class(self, cls: Class, analysis_type: str = "comprehensive") -> AIAnalysisResult:
        """Analyze a class with AI assistance"""
        try:
            context = self._extract_class_context(cls)
            prompt = self._prepare_class_analysis_prompt(cls, context, analysis_type)
            ai_response = self._get_ai_analysis(prompt, context)
            
            result = self._parse_ai_response(ai_response, "class", cls.name)
            result.context_used = context
            
            return result
            
        except Exception as e:
            print(f"Error analyzing class {cls.name}: {e}")
            return AIAnalysisResult(
                analysis_type=analysis_type,
                target=cls.name,
                issues=[{"type": "analysis_error", "message": str(e)}]
            )
    
    def analyze_file(self, file: SourceFile, analysis_type: str = "comprehensive") -> AIAnalysisResult:
        """Analyze a file with AI assistance"""
        try:
            context = self._extract_file_context(file)
            prompt = self._prepare_file_analysis_prompt(file, context, analysis_type)
            ai_response = self._get_ai_analysis(prompt, context)
            
            result = self._parse_ai_response(ai_response, "file", file.name)
            result.context_used = context
            
            return result
            
        except Exception as e:
            print(f"Error analyzing file {file.name}: {e}")
            return AIAnalysisResult(
                analysis_type=analysis_type,
                target=file.name,
                issues=[{"type": "analysis_error", "message": str(e)}]
            )
    
    def batch_analyze_codebase(self, codebase: Codebase, 
                             analysis_types: List[str] = None) -> Dict[str, List[AIAnalysisResult]]:
        """Perform batch AI analysis on entire codebase"""
        if analysis_types is None:
            analysis_types = ["quality", "security", "performance", "maintainability"]
        
        results = {
            "functions": [],
            "classes": [],
            "files": [],
            "summary": {}
        }
        
        try:
            # Analyze functions
            for function in codebase.functions:
                for analysis_type in analysis_types:
                    result = self.analyze_function(function, analysis_type)
                    results["functions"].append(result)
            
            # Analyze classes
            for cls in codebase.classes:
                for analysis_type in analysis_types:
                    result = self.analyze_class(cls, analysis_type)
                    results["classes"].append(result)
            
            # Analyze files
            for file in codebase.files:
                result = self.analyze_file(file, "overview")
                results["files"].append(result)
            
            # Generate summary
            results["summary"] = self._generate_analysis_summary(results)
            
        except Exception as e:
            print(f"Error in batch analysis: {e}")
            results["error"] = str(e)
        
        return results
    
    def _extract_function_context(self, function: Function) -> Dict[str, Any]:
        """Extract comprehensive context for a function"""
        context = {
            "implementation": {
                "source": getattr(function, 'source', ''),
                "filepath": getattr(function, 'filepath', ''),
                "name": function.name,
                "line_count": len(getattr(function, 'source', '').splitlines())
            },
            "dependencies": [],
            "usages": [],
            "parameters": [],
            "return_statements": [],
            "complexity_indicators": {},
            "parent_context": {}
        }
        
        try:
            # Add dependencies
            if hasattr(function, 'dependencies'):
                for dep in function.dependencies:
                    context["dependencies"].append({
                        "name": getattr(dep, 'name', ''),
                        "source": getattr(dep, 'source', ''),
                        "filepath": getattr(dep, 'filepath', '')
                    })
            
            # Add usages
            if hasattr(function, 'usages'):
                for usage in function.usages:
                    context["usages"].append({
                        "location": getattr(usage, 'filepath', ''),
                        "context": getattr(usage, 'source', '')
                    })
            
            # Add parameters
            if hasattr(function, 'parameters'):
                context["parameters"] = [
                    {"name": param.name, "type": getattr(param, 'type', 'unknown')}
                    for param in function.parameters
                ]
            
            # Add parent context (class or module)
            if hasattr(function, 'parent'):
                parent = function.parent
                context["parent_context"] = {
                    "type": type(parent).__name__,
                    "name": getattr(parent, 'name', ''),
                    "source": getattr(parent, 'source', '')[:500]  # First 500 chars
                }
            
            # Add complexity indicators
            source = getattr(function, 'source', '')
            context["complexity_indicators"] = {
                "line_count": len(source.splitlines()),
                "has_loops": any(keyword in source for keyword in ['for ', 'while ']),
                "has_conditionals": any(keyword in source for keyword in ['if ', 'elif ', 'else:']),
                "has_try_catch": 'try:' in source,
                "has_async": 'async ' in source,
                "nested_functions": source.count('def ') > 1
            }
            
        except Exception as e:
            print(f"Error extracting function context: {e}")
        
        return context
    
    def _extract_class_context(self, cls: Class) -> Dict[str, Any]:
        """Extract comprehensive context for a class"""
        context = {
            "definition": {
                "name": cls.name,
                "source": getattr(cls, 'source', ''),
                "filepath": getattr(cls, 'filepath', '')
            },
            "methods": [],
            "attributes": [],
            "inheritance": {},
            "usage_patterns": [],
            "complexity_metrics": {}
        }
        
        try:
            # Add methods
            if hasattr(cls, 'methods'):
                for method in cls.methods:
                    context["methods"].append({
                        "name": method.name,
                        "source": getattr(method, 'source', ''),
                        "is_private": method.name.startswith('_'),
                        "is_property": hasattr(method, 'decorators') and 
                                     any('property' in str(d) for d in method.decorators)
                    })
            
            # Add attributes
            if hasattr(cls, 'attributes'):
                context["attributes"] = [
                    {"name": attr.name, "type": getattr(attr, 'type', 'unknown')}
                    for attr in cls.attributes
                ]
            
            # Add inheritance information
            if hasattr(cls, 'parent_class_names'):
                context["inheritance"] = {
                    "parent_classes": cls.parent_class_names,
                    "is_base_class": len(cls.parent_class_names) == 0
                }
            
            # Add complexity metrics
            source = getattr(cls, 'source', '')
            context["complexity_metrics"] = {
                "method_count": len(context["methods"]),
                "line_count": len(source.splitlines()),
                "public_methods": len([m for m in context["methods"] if not m["is_private"]]),
                "private_methods": len([m for m in context["methods"] if m["is_private"]])
            }
            
        except Exception as e:
            print(f"Error extracting class context: {e}")
        
        return context
    
    def _extract_file_context(self, file: SourceFile) -> Dict[str, Any]:
        """Extract comprehensive context for a file"""
        context = {
            "file_info": {
                "name": file.name,
                "path": getattr(file, 'filepath', ''),
                "size": len(getattr(file, 'source', ''))
            },
            "imports": [],
            "exports": [],
            "top_level_elements": {},
            "structure_metrics": {}
        }
        
        try:
            # Add imports
            if hasattr(file, 'imports'):
                for imp in file.imports:
                    context["imports"].append({
                        "module": getattr(imp, 'module', ''),
                        "symbols": getattr(imp, 'symbols', [])
                    })
            
            # Add top-level elements
            context["top_level_elements"] = {
                "functions": len(getattr(file, 'functions', [])),
                "classes": len(getattr(file, 'classes', [])),
                "global_vars": len(getattr(file, 'global_vars', []))
            }
            
            # Add structure metrics
            source = getattr(file, 'source', '')
            lines = source.splitlines()
            context["structure_metrics"] = {
                "total_lines": len(lines),
                "blank_lines": len([line for line in lines if not line.strip()]),
                "comment_lines": len([line for line in lines if line.strip().startswith('#')]),
                "import_count": len(context["imports"])
            }
            
        except Exception as e:
            print(f"Error extracting file context: {e}")
        
        return context
    
    def _extract_dependency_context(self, symbol: Any) -> Dict[str, Any]:
        """Extract dependency context for a symbol"""
        return {"dependencies": [], "dependents": []}
    
    def _extract_usage_context(self, symbol: Any) -> Dict[str, Any]:
        """Extract usage context for a symbol"""
        return {"usages": [], "usage_patterns": []}
    
    def _prepare_function_analysis_prompt(self, function: Function, 
                                        context: Dict[str, Any], 
                                        analysis_type: str) -> str:
        """Prepare AI prompt for function analysis"""
        base_prompt = f"""
        Analyze the following Python function for {analysis_type} issues and improvements:
        
        Function: {function.name}
        Source Code:
        ```python
        {context['implementation']['source']}
        ```
        
        Context:
        - File: {context['implementation']['filepath']}
        - Dependencies: {len(context['dependencies'])} items
        - Usages: {len(context['usages'])} locations
        - Parameters: {len(context['parameters'])} items
        - Line count: {context['implementation']['line_count']}
        """
        
        if analysis_type == "quality":
            return base_prompt + """
            
            Please analyze for:
            1. Code quality issues (naming, structure, readability)
            2. Potential bugs or logic errors
            3. Best practice violations
            4. Suggestions for improvement
            
            Provide specific, actionable recommendations.
            """
        
        elif analysis_type == "security":
            return base_prompt + """
            
            Please analyze for:
            1. Security vulnerabilities
            2. Input validation issues
            3. Potential injection attacks
            4. Unsafe operations
            
            Focus on security-specific concerns and mitigation strategies.
            """
        
        elif analysis_type == "performance":
            return base_prompt + """
            
            Please analyze for:
            1. Performance bottlenecks
            2. Inefficient algorithms or data structures
            3. Memory usage concerns
            4. Optimization opportunities
            
            Suggest specific performance improvements.
            """
        
        else:  # comprehensive
            return base_prompt + """
            
            Please provide a comprehensive analysis covering:
            1. Code quality and maintainability
            2. Security considerations
            3. Performance implications
            4. Documentation and testing needs
            5. Refactoring opportunities
            
            Provide detailed, prioritized recommendations.
            """
    
    def _prepare_class_analysis_prompt(self, cls: Class, 
                                     context: Dict[str, Any], 
                                     analysis_type: str) -> str:
        """Prepare AI prompt for class analysis"""
        return f"""
        Analyze the following Python class for {analysis_type} issues:
        
        Class: {cls.name}
        Methods: {len(context['methods'])}
        Attributes: {len(context['attributes'])}
        Inheritance: {context.get('inheritance', {})}
        
        Please provide analysis and recommendations for improvement.
        """
    
    def _prepare_file_analysis_prompt(self, file: SourceFile, 
                                    context: Dict[str, Any], 
                                    analysis_type: str) -> str:
        """Prepare AI prompt for file analysis"""
        return f"""
        Analyze the following Python file for {analysis_type} overview:
        
        File: {file.name}
        Structure: {context['top_level_elements']}
        Metrics: {context['structure_metrics']}
        
        Please provide a high-level analysis and recommendations.
        """
    
    def _get_ai_analysis(self, prompt: str, context: Dict[str, Any]) -> str:
        """Get AI analysis (mock implementation)"""
        # This would integrate with actual AI provider (OpenAI, Claude, etc.)
        # For now, return a mock response
        return f"""
        Analysis completed for the provided code.
        
        Issues found:
        - Consider adding type hints for better code clarity
        - Function complexity could be reduced by breaking into smaller functions
        - Missing docstring documentation
        
        Suggestions:
        - Add comprehensive error handling
        - Implement unit tests
        - Consider using more descriptive variable names
        
        Overall assessment: The code is functional but could benefit from 
        improved documentation and structure for better maintainability.
        """
    
    def _parse_ai_response(self, response: str, target_type: str, target_name: str) -> AIAnalysisResult:
        """Parse AI response into structured result"""
        # Simple parsing logic - in practice, this would be more sophisticated
        result = AIAnalysisResult(
            analysis_type="ai_analysis",
            target=target_name
        )
        
        # Extract suggestions (lines starting with "- ")
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Issues found:'):
                current_section = 'issues'
            elif line.startswith('Suggestions:'):
                current_section = 'suggestions'
            elif line.startswith('- ') and current_section == 'issues':
                result.issues.append({
                    "type": "ai_detected",
                    "message": line[2:],
                    "severity": "medium"
                })
            elif line.startswith('- ') and current_section == 'suggestions':
                result.suggestions.append(line[2:])
        
        # Set confidence based on response quality
        result.confidence = 0.8 if len(result.suggestions) > 0 else 0.5
        
        return result
    
    def _generate_analysis_summary(self, results: Dict[str, List[AIAnalysisResult]]) -> Dict[str, Any]:
        """Generate summary of batch analysis results"""
        summary = {
            "total_items_analyzed": 0,
            "total_issues_found": 0,
            "total_suggestions": 0,
            "issue_categories": Counter(),
            "suggestion_categories": Counter(),
            "confidence_distribution": []
        }
        
        for category, result_list in results.items():
            if category == "summary":
                continue
                
            summary["total_items_analyzed"] += len(result_list)
            
            for result in result_list:
                summary["total_issues_found"] += len(result.issues)
                summary["total_suggestions"] += len(result.suggestions)
                summary["confidence_distribution"].append(result.confidence)
                
                # Categorize issues
                for issue in result.issues:
                    summary["issue_categories"][issue.get("type", "unknown")] += 1
        
        # Calculate average confidence
        if summary["confidence_distribution"]:
            summary["average_confidence"] = sum(summary["confidence_distribution"]) / len(summary["confidence_distribution"])
        else:
            summary["average_confidence"] = 0.0
        
        return summary


class AutomatedIssueDetector:
    """
    Automated issue detection with AI assistance
    """
    
    def __init__(self, ai_analyzer: Optional[AIAnalyzer] = None):
        self.ai_analyzer = ai_analyzer or AIAnalyzer()
        self.issue_patterns = self._load_issue_patterns()
    
    def _load_issue_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined issue detection patterns"""
        return {
            "missing_docstring": {
                "pattern": lambda func: not getattr(func, 'docstring', None),
                "severity": "medium",
                "message": "Function missing docstring",
                "auto_fixable": True
            },
            "long_function": {
                "pattern": lambda func: len(getattr(func, 'source', '').splitlines()) > 50,
                "severity": "medium",
                "message": "Function is too long (>50 lines)",
                "auto_fixable": False
            },
            "too_many_parameters": {
                "pattern": lambda func: len(getattr(func, 'parameters', [])) > 5,
                "severity": "medium",
                "message": "Function has too many parameters",
                "auto_fixable": False
            },
            "missing_error_handling": {
                "pattern": lambda func: (
                    hasattr(func, 'is_async') and func.is_async and 
                    'try:' not in getattr(func, 'source', '')
                ),
                "severity": "high",
                "message": "Async function missing error handling",
                "auto_fixable": False
            }
        }
    
    def detect_issues(self, codebase: Codebase) -> List[IssueDetectionResult]:
        """Detect issues across the codebase"""
        issues = []
        
        # Pattern-based detection
        for function in codebase.functions:
            function_issues = self._detect_function_issues(function)
            issues.extend(function_issues)
        
        # AI-powered detection
        if self.ai_analyzer:
            ai_issues = self._detect_ai_issues(codebase)
            issues.extend(ai_issues)
        
        return issues
    
    def _detect_function_issues(self, function: Function) -> List[IssueDetectionResult]:
        """Detect issues in a specific function"""
        issues = []
        
        for issue_type, pattern_config in self.issue_patterns.items():
            try:
                if pattern_config["pattern"](function):
                    issue = IssueDetectionResult(
                        issue_type=issue_type,
                        severity=pattern_config["severity"],
                        message=pattern_config["message"],
                        location=getattr(function, 'filepath', 'unknown'),
                        function_name=function.name,
                        auto_fixable=pattern_config["auto_fixable"],
                        context=self.ai_analyzer._extract_function_context(function)
                    )
                    issues.append(issue)
            except Exception as e:
                print(f"Error detecting {issue_type} in {function.name}: {e}")
        
        return issues
    
    def _detect_ai_issues(self, codebase: Codebase) -> List[IssueDetectionResult]:
        """Use AI to detect complex issues"""
        issues = []
        
        # Sample a subset of functions for AI analysis to avoid overwhelming the system
        sample_functions = list(codebase.functions)[:10]  # Analyze first 10 functions
        
        for function in sample_functions:
            try:
                ai_result = self.ai_analyzer.analyze_function(function, "quality")
                
                for ai_issue in ai_result.issues:
                    issue = IssueDetectionResult(
                        issue_type="ai_detected",
                        severity=ai_issue.get("severity", "medium"),
                        message=ai_issue.get("message", "AI detected issue"),
                        location=getattr(function, 'filepath', 'unknown'),
                        function_name=function.name,
                        context=ai_result.context_used
                    )
                    issues.append(issue)
                    
            except Exception as e:
                print(f"Error in AI issue detection for {function.name}: {e}")
        
        return issues


class CodeImprovementSuggester:
    """
    Generate intelligent code improvement suggestions
    """
    
    def __init__(self, ai_analyzer: Optional[AIAnalyzer] = None):
        self.ai_analyzer = ai_analyzer or AIAnalyzer()
    
    def suggest_improvements(self, codebase: Codebase) -> List[ImprovementSuggestion]:
        """Generate improvement suggestions for the codebase"""
        suggestions = []
        
        # Analyze functions for improvements
        for function in list(codebase.functions)[:5]:  # Limit to first 5 functions
            try:
                function_suggestions = self._suggest_function_improvements(function)
                suggestions.extend(function_suggestions)
            except Exception as e:
                print(f"Error suggesting improvements for {function.name}: {e}")
        
        return suggestions
    
    def _suggest_function_improvements(self, function: Function) -> List[ImprovementSuggestion]:
        """Suggest improvements for a specific function"""
        suggestions = []
        
        # Get AI analysis
        ai_result = self.ai_analyzer.analyze_function(function, "comprehensive")
        
        # Convert AI suggestions to structured improvements
        for suggestion_text in ai_result.suggestions:
            suggestion = ImprovementSuggestion(
                suggestion_type="ai_suggestion",
                title=f"Improve {function.name}",
                description=suggestion_text,
                code_before=getattr(function, 'source', ''),
                impact="medium",
                effort="medium",
                benefits=[suggestion_text],
                implementation_steps=[
                    "Review the current implementation",
                    "Apply the suggested changes",
                    "Test the modified function",
                    "Update documentation if needed"
                ]
            )
            suggestions.append(suggestion)
        
        return suggestions


class DocumentationGenerator:
    """
    AI-powered documentation generator
    """
    
    def __init__(self, ai_analyzer: Optional[AIAnalyzer] = None):
        self.ai_analyzer = ai_analyzer or AIAnalyzer()
    
    def generate_function_documentation(self, function: Function) -> str:
        """Generate documentation for a function"""
        try:
            context = self.ai_analyzer._extract_function_context(function)
            
            # Create documentation prompt
            prompt = f"""
            Generate comprehensive documentation for this Python function:
            
            ```python
            {context['implementation']['source']}
            ```
            
            Include:
            1. Brief description of what the function does
            2. Parameters and their types
            3. Return value description
            4. Usage examples
            5. Any important notes or warnings
            
            Format as a proper Python docstring.
            """
            
            # Get AI response (mock)
            documentation = self._generate_mock_documentation(function)
            
            return documentation
            
        except Exception as e:
            print(f"Error generating documentation for {function.name}: {e}")
            return f'"""\nDocumentation for {function.name}\n\nTODO: Add proper documentation\n"""'
    
    def _generate_mock_documentation(self, function: Function) -> str:
        """Generate mock documentation (placeholder for AI integration)"""
        return f'''"""
        {function.name.replace('_', ' ').title()}
        
        This function performs operations related to {function.name}.
        
        Args:
            TODO: Add parameter descriptions
        
        Returns:
            TODO: Add return value description
        
        Example:
            >>> result = {function.name}()
            >>> print(result)
        
        Note:
            This documentation was auto-generated and should be reviewed.
        """'''


# Convenience functions for direct use

def analyze_with_ai(codebase: Codebase, analysis_types: List[str] = None) -> Dict[str, Any]:
    """Perform AI analysis on codebase"""
    analyzer = AIAnalyzer()
    return analyzer.batch_analyze_codebase(codebase, analysis_types)


def detect_issues_automatically(codebase: Codebase) -> List[IssueDetectionResult]:
    """Automatically detect issues in codebase"""
    detector = AutomatedIssueDetector()
    return detector.detect_issues(codebase)


def suggest_improvements(codebase: Codebase) -> List[ImprovementSuggestion]:
    """Generate improvement suggestions for codebase"""
    suggester = CodeImprovementSuggester()
    return suggester.suggest_improvements(codebase)

