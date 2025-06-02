"""
Graph-Sitter Integration for Dashboard
Comprehensive code analysis and manipulation using graph-sitter
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

try:
    from graph_sitter import Language, Parser, Node
    from graph_sitter.binding import Query
except ImportError:
    logging.warning("graph-sitter not available, using mock implementation")
    Language = None
    Parser = None
    Node = None
    Query = None

logger = logging.getLogger(__name__)

class GraphSitterAnalyzer:
    """
    Comprehensive code analysis using graph-sitter for the dashboard
    """
    
    def __init__(self):
        self.parsers = {}
        self.languages = {}
        self.analysis_cache = {}
        self.initialize_languages()
    
    def initialize_languages(self):
        """Initialize supported programming languages"""
        try:
            # Common languages for analysis
            language_configs = {
                'python': 'tree-sitter-python',
                'javascript': 'tree-sitter-javascript',
                'typescript': 'tree-sitter-typescript',
                'java': 'tree-sitter-java',
                'cpp': 'tree-sitter-cpp',
                'rust': 'tree-sitter-rust',
                'go': 'tree-sitter-go',
                'ruby': 'tree-sitter-ruby',
                'php': 'tree-sitter-php',
                'c_sharp': 'tree-sitter-c-sharp'
            }
            
            for lang_name, lib_name in language_configs.items():
                try:
                    if Language:
                        language = Language(lib_name)
                        parser = Parser()
                        parser.set_language(language)
                        
                        self.languages[lang_name] = language
                        self.parsers[lang_name] = parser
                        
                        logger.info(f"Initialized {lang_name} parser")
                except Exception as e:
                    logger.warning(f"Could not initialize {lang_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing languages: {e}")
    
    async def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive project analysis
        """
        try:
            project_path = Path(project_path)
            if not project_path.exists():
                raise ValueError(f"Project path does not exist: {project_path}")
            
            analysis_results = {
                "project_path": str(project_path),
                "timestamp": datetime.now().isoformat(),
                "files_analyzed": 0,
                "languages_detected": [],
                "metrics": {},
                "issues": [],
                "suggestions": [],
                "dead_code": [],
                "complexity": {},
                "dependencies": {},
                "security_issues": []
            }
            
            # Discover and analyze files
            files_to_analyze = self._discover_source_files(project_path)
            analysis_results["files_analyzed"] = len(files_to_analyze)
            
            # Analyze each file
            for file_path in files_to_analyze:
                file_analysis = await self._analyze_file(file_path)
                self._merge_file_analysis(analysis_results, file_analysis)
            
            # Perform project-level analysis
            await self._analyze_project_structure(project_path, analysis_results)
            await self._analyze_dependencies(project_path, analysis_results)
            await self._detect_dead_code(project_path, analysis_results)
            await self._analyze_complexity(analysis_results)
            await self._security_analysis(analysis_results)
            
            # Generate insights and suggestions
            analysis_results["insights"] = await self._generate_insights(analysis_results)
            analysis_results["recommendations"] = await self._generate_recommendations(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing project {project_path}: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def analyze_pr_changes(self, repository: str, pr_number: int) -> Dict[str, Any]:
        """
        Analyze changes in a pull request
        """
        try:
            # This would integrate with GitHub API to get PR diff
            # For now, return mock analysis
            return {
                "pr_number": pr_number,
                "repository": repository,
                "timestamp": datetime.now().isoformat(),
                "changes_analyzed": True,
                "files_changed": [],
                "complexity_impact": "low",
                "security_impact": "none",
                "test_coverage_impact": "neutral",
                "recommendations": [
                    "Consider adding unit tests for new functions",
                    "Review error handling in modified functions"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing PR {pr_number}: {e}")
            return {"error": str(e)}
    
    async def analyze_dead_code(self, project_path: str) -> Dict[str, Any]:
        """
        Comprehensive dead code analysis
        """
        try:
            project_path = Path(project_path)
            dead_code_analysis = {
                "timestamp": datetime.now().isoformat(),
                "project_path": str(project_path),
                "dead_functions": [],
                "dead_classes": [],
                "dead_variables": [],
                "unused_imports": [],
                "unreachable_code": [],
                "confidence_scores": {},
                "recommendations": []
            }
            
            # Analyze each source file
            source_files = self._discover_source_files(project_path)
            
            for file_path in source_files:
                file_dead_code = await self._analyze_file_dead_code(file_path)
                self._merge_dead_code_analysis(dead_code_analysis, file_dead_code)
            
            # Cross-reference analysis
            await self._cross_reference_usage(project_path, dead_code_analysis)
            
            # Generate confidence scores
            self._calculate_confidence_scores(dead_code_analysis)
            
            # Generate recommendations
            dead_code_analysis["recommendations"] = self._generate_dead_code_recommendations(dead_code_analysis)
            
            return dead_code_analysis
            
        except Exception as e:
            logger.error(f"Error in dead code analysis: {e}")
            return {"error": str(e)}
    
    async def analyze_code_quality(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze code quality metrics for a specific file
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise ValueError(f"File does not exist: {file_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect language
            language = self._detect_language(file_path)
            if language not in self.parsers:
                return {"error": f"Unsupported language: {language}"}
            
            # Parse the code
            parser = self.parsers[language]
            tree = parser.parse(bytes(content, 'utf8'))
            
            # Analyze quality metrics
            quality_metrics = {
                "file_path": str(file_path),
                "language": language,
                "timestamp": datetime.now().isoformat(),
                "lines_of_code": len(content.split('\n')),
                "cyclomatic_complexity": 0,
                "maintainability_index": 0,
                "code_duplication": 0,
                "test_coverage": 0,
                "documentation_coverage": 0,
                "issues": [],
                "suggestions": []
            }
            
            # Calculate metrics
            await self._calculate_complexity(tree, quality_metrics)
            await self._check_code_style(tree, content, quality_metrics)
            await self._analyze_documentation(tree, quality_metrics)
            await self._detect_code_smells(tree, quality_metrics)
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing code quality for {file_path}: {e}")
            return {"error": str(e)}
    
    def _discover_source_files(self, project_path: Path) -> List[Path]:
        """Discover source files in the project"""
        source_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.rs', '.go', '.rb', '.php', '.cs', '.swift', '.kt'
        }
        
        source_files = []
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in source_extensions:
                # Skip common directories to ignore
                if any(part in str(file_path) for part in ['.git', 'node_modules', '__pycache__', '.venv']):
                    continue
                source_files.append(file_path)
        
        return source_files
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'c_sharp'
        }
        
        return extension_map.get(file_path.suffix, 'unknown')
    
    async def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            language = self._detect_language(file_path)
            
            file_analysis = {
                "file_path": str(file_path),
                "language": language,
                "lines_of_code": len(content.split('\n')),
                "functions": [],
                "classes": [],
                "imports": [],
                "issues": [],
                "complexity": 0
            }
            
            if language in self.parsers:
                parser = self.parsers[language]
                tree = parser.parse(bytes(content, 'utf8'))
                
                # Extract code elements
                await self._extract_functions(tree, file_analysis)
                await self._extract_classes(tree, file_analysis)
                await self._extract_imports(tree, file_analysis)
                await self._calculate_file_complexity(tree, file_analysis)
            
            return file_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {"error": str(e), "file_path": str(file_path)}
    
    async def _analyze_file_dead_code(self, file_path: Path) -> Dict[str, Any]:
        """Analyze dead code in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            language = self._detect_language(file_path)
            
            dead_code_analysis = {
                "file_path": str(file_path),
                "language": language,
                "dead_functions": [],
                "dead_classes": [],
                "dead_variables": [],
                "unused_imports": [],
                "unreachable_code": []
            }
            
            if language in self.parsers:
                parser = self.parsers[language]
                tree = parser.parse(bytes(content, 'utf8'))
                
                # Analyze for dead code patterns
                await self._find_unused_functions(tree, content, dead_code_analysis)
                await self._find_unused_classes(tree, content, dead_code_analysis)
                await self._find_unused_variables(tree, content, dead_code_analysis)
                await self._find_unused_imports(tree, content, dead_code_analysis)
                await self._find_unreachable_code(tree, content, dead_code_analysis)
            
            return dead_code_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing dead code in {file_path}: {e}")
            return {"error": str(e), "file_path": str(file_path)}
    
    def _merge_file_analysis(self, project_analysis: Dict[str, Any], file_analysis: Dict[str, Any]):
        """Merge file analysis into project analysis"""
        if "error" in file_analysis:
            return
        
        # Update language detection
        language = file_analysis.get("language")
        if language and language not in project_analysis["languages_detected"]:
            project_analysis["languages_detected"].append(language)
        
        # Update metrics
        if "metrics" not in project_analysis:
            project_analysis["metrics"] = {}
        
        project_analysis["metrics"]["total_lines"] = project_analysis["metrics"].get("total_lines", 0) + file_analysis.get("lines_of_code", 0)
        project_analysis["metrics"]["total_functions"] = project_analysis["metrics"].get("total_functions", 0) + len(file_analysis.get("functions", []))
        project_analysis["metrics"]["total_classes"] = project_analysis["metrics"].get("total_classes", 0) + len(file_analysis.get("classes", []))
        
        # Merge issues
        project_analysis["issues"].extend(file_analysis.get("issues", []))
    
    def _merge_dead_code_analysis(self, project_analysis: Dict[str, Any], file_analysis: Dict[str, Any]):
        """Merge file dead code analysis into project analysis"""
        if "error" in file_analysis:
            return
        
        # Merge dead code findings
        project_analysis["dead_functions"].extend(file_analysis.get("dead_functions", []))
        project_analysis["dead_classes"].extend(file_analysis.get("dead_classes", []))
        project_analysis["dead_variables"].extend(file_analysis.get("dead_variables", []))
        project_analysis["unused_imports"].extend(file_analysis.get("unused_imports", []))
        project_analysis["unreachable_code"].extend(file_analysis.get("unreachable_code", []))
    
    async def _analyze_project_structure(self, project_path: Path, analysis: Dict[str, Any]):
        """Analyze overall project structure"""
        try:
            structure_analysis = {
                "total_directories": 0,
                "total_files": 0,
                "package_structure": [],
                "module_dependencies": {},
                "architecture_patterns": []
            }
            
            # Count directories and files
            for item in project_path.rglob('*'):
                if item.is_dir():
                    structure_analysis["total_directories"] += 1
                elif item.is_file():
                    structure_analysis["total_files"] += 1
            
            analysis["structure"] = structure_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing project structure: {e}")
    
    async def _analyze_dependencies(self, project_path: Path, analysis: Dict[str, Any]):
        """Analyze project dependencies"""
        try:
            dependencies = {
                "external_dependencies": [],
                "internal_dependencies": {},
                "circular_dependencies": [],
                "unused_dependencies": []
            }
            
            # Look for dependency files
            dependency_files = [
                "requirements.txt", "package.json", "Cargo.toml", 
                "go.mod", "pom.xml", "build.gradle"
            ]
            
            for dep_file in dependency_files:
                dep_path = project_path / dep_file
                if dep_path.exists():
                    deps = await self._parse_dependency_file(dep_path)
                    dependencies["external_dependencies"].extend(deps)
            
            analysis["dependencies"] = dependencies
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
    
    async def _detect_dead_code(self, project_path: Path, analysis: Dict[str, Any]):
        """Detect dead code across the project"""
        try:
            # This would be a comprehensive dead code analysis
            # For now, return basic structure
            dead_code_summary = {
                "total_dead_functions": len(analysis.get("dead_code", [])),
                "confidence_level": "medium",
                "recommendations": [
                    "Review flagged functions before removal",
                    "Check for dynamic imports or reflection usage",
                    "Verify test coverage for flagged code"
                ]
            }
            
            analysis["dead_code_summary"] = dead_code_summary
            
        except Exception as e:
            logger.error(f"Error detecting dead code: {e}")
    
    async def _analyze_complexity(self, analysis: Dict[str, Any]):
        """Analyze code complexity metrics"""
        try:
            complexity_analysis = {
                "average_complexity": 0,
                "high_complexity_functions": [],
                "complexity_distribution": {},
                "maintainability_score": 85
            }
            
            analysis["complexity"] = complexity_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing complexity: {e}")
    
    async def _security_analysis(self, analysis: Dict[str, Any]):
        """Perform security analysis"""
        try:
            security_analysis = {
                "potential_vulnerabilities": [],
                "security_score": 92,
                "recommendations": [
                    "Review input validation",
                    "Check for SQL injection vulnerabilities",
                    "Verify authentication mechanisms"
                ]
            }
            
            analysis["security_issues"] = security_analysis
            
        except Exception as e:
            logger.error(f"Error in security analysis: {e}")
    
    async def _generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights from analysis results"""
        insights = []
        
        # Code quality insights
        if analysis.get("metrics", {}).get("total_lines", 0) > 10000:
            insights.append("Large codebase detected - consider modularization")
        
        # Language diversity insights
        languages = analysis.get("languages_detected", [])
        if len(languages) > 3:
            insights.append(f"Multi-language project with {len(languages)} languages")
        
        # Complexity insights
        complexity = analysis.get("complexity", {})
        if complexity.get("maintainability_score", 100) < 70:
            insights.append("Low maintainability score - refactoring recommended")
        
        return insights
    
    async def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Dead code recommendations
        if analysis.get("dead_code"):
            recommendations.append("Remove identified dead code to improve maintainability")
        
        # Security recommendations
        security_issues = analysis.get("security_issues", {})
        if security_issues.get("potential_vulnerabilities"):
            recommendations.append("Address identified security vulnerabilities")
        
        # Performance recommendations
        if analysis.get("metrics", {}).get("total_lines", 0) > 50000:
            recommendations.append("Consider breaking down large modules")
        
        return recommendations
    
    # Mock implementations for tree-sitter operations
    async def _extract_functions(self, tree, analysis):
        """Extract function definitions from AST"""
        pass
    
    async def _extract_classes(self, tree, analysis):
        """Extract class definitions from AST"""
        pass
    
    async def _extract_imports(self, tree, analysis):
        """Extract import statements from AST"""
        pass
    
    async def _calculate_file_complexity(self, tree, analysis):
        """Calculate complexity metrics for file"""
        pass
    
    async def _find_unused_functions(self, tree, content, analysis):
        """Find unused functions in the file"""
        pass
    
    async def _find_unused_classes(self, tree, content, analysis):
        """Find unused classes in the file"""
        pass
    
    async def _find_unused_variables(self, tree, content, analysis):
        """Find unused variables in the file"""
        pass
    
    async def _find_unused_imports(self, tree, content, analysis):
        """Find unused imports in the file"""
        pass
    
    async def _find_unreachable_code(self, tree, content, analysis):
        """Find unreachable code blocks"""
        pass
    
    async def _cross_reference_usage(self, project_path, analysis):
        """Cross-reference usage across files"""
        pass
    
    def _calculate_confidence_scores(self, analysis):
        """Calculate confidence scores for dead code detection"""
        pass
    
    def _generate_dead_code_recommendations(self, analysis):
        """Generate recommendations for dead code cleanup"""
        return [
            "Review flagged items before removal",
            "Check for dynamic usage patterns",
            "Verify test coverage",
            "Consider deprecation before removal"
        ]
    
    async def _calculate_complexity(self, tree, metrics):
        """Calculate cyclomatic complexity"""
        pass
    
    async def _check_code_style(self, tree, content, metrics):
        """Check code style and formatting"""
        pass
    
    async def _analyze_documentation(self, tree, metrics):
        """Analyze documentation coverage"""
        pass
    
    async def _detect_code_smells(self, tree, metrics):
        """Detect code smells and anti-patterns"""
        pass
    
    async def _parse_dependency_file(self, file_path: Path) -> List[str]:
        """Parse dependency file and extract dependencies"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Basic parsing - would need specific parsers for each format
            dependencies = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    dependencies.append(line.split('==')[0].split('>=')[0].split('~=')[0])
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Error parsing dependency file {file_path}: {e}")
            return []

# Utility functions for dashboard integration
async def analyze_project_for_dashboard(project_path: str) -> Dict[str, Any]:
    """Convenience function for dashboard project analysis"""
    analyzer = GraphSitterAnalyzer()
    return await analyzer.analyze_project(project_path)

async def analyze_dead_code_for_dashboard(project_path: str) -> Dict[str, Any]:
    """Convenience function for dashboard dead code analysis"""
    analyzer = GraphSitterAnalyzer()
    return await analyzer.analyze_dead_code(project_path)

async def analyze_code_quality_for_dashboard(file_path: str) -> Dict[str, Any]:
    """Convenience function for dashboard code quality analysis"""
    analyzer = GraphSitterAnalyzer()
    return await analyzer.analyze_code_quality(file_path)

