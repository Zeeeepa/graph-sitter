"""
Codebase Analyzer: Core analysis engine for Graph-Sitter system

This module provides comprehensive codebase analysis capabilities including:
- Multi-language parsing
- Dependency graph construction
- Code metrics calculation
- Dead code detection
- Impact analysis
"""

import os
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json

from ..utils.config import Config
from ..utils.database import DatabaseManager
from ..utils.validation import CodeValidator
from .graph_builder import GraphBuilder
from .metrics_calculator import MetricsCalculator


@dataclass
class AnalysisResult:
    """Container for analysis results"""
    repository_id: str
    commit_sha: str
    files_analyzed: int
    symbols_found: int
    dependencies_mapped: int
    dead_code_detected: int
    complexity_score: float
    maintainability_index: float
    analysis_duration: float
    errors: List[str]
    warnings: List[str]


@dataclass
class FileAnalysis:
    """Container for individual file analysis results"""
    file_path: str
    language: str
    metrics: Dict[str, Any]
    symbols: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    dead_code: List[Dict[str, Any]]
    errors: List[str]


class CodebaseAnalyzer:
    """
    Main codebase analysis engine that orchestrates the analysis process
    """
    
    def __init__(self, config: Config):
        """
        Initialize the codebase analyzer
        
        Args:
            config: Configuration object containing analysis settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager(config.database_url)
        self.graph_builder = GraphBuilder(config)
        self.metrics_calculator = MetricsCalculator(config)
        self.validator = CodeValidator()
        
        # Supported file extensions by language
        self.language_extensions = {
            'python': ['.py', '.pyx', '.pyi'],
            'typescript': ['.ts', '.tsx'],
            'javascript': ['.js', '.jsx', '.mjs'],
            'java': ['.java'],
            'csharp': ['.cs'],
            'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'c': ['.c', '.h'],
            'rust': ['.rs'],
            'go': ['.go'],
            'ruby': ['.rb'],
            'php': ['.php'],
            'swift': ['.swift'],
            'kotlin': ['.kt', '.kts'],
            'scala': ['.scala'],
            'r': ['.r', '.R'],
            'sql': ['.sql'],
            'shell': ['.sh', '.bash', '.zsh'],
            'yaml': ['.yaml', '.yml'],
            'json': ['.json'],
            'xml': ['.xml'],
            'html': ['.html', '.htm'],
            'css': ['.css', '.scss', '.sass'],
            'markdown': ['.md', '.markdown']
        }
    
    def analyze_repository(self, repo_path: str, commit_sha: Optional[str] = None) -> AnalysisResult:
        """
        Analyze an entire repository
        
        Args:
            repo_path: Path to the repository root
            commit_sha: Optional specific commit to analyze
            
        Returns:
            AnalysisResult containing comprehensive analysis data
        """
        start_time = time.time()
        self.logger.info(f"Starting repository analysis: {repo_path}")
        
        try:
            # Validate repository
            if not self._validate_repository(repo_path):
                raise ValueError(f"Invalid repository path: {repo_path}")
            
            # Get or create repository record
            repo_id = self._get_or_create_repository(repo_path)
            
            # Get commit information
            if not commit_sha:
                commit_sha = self._get_current_commit(repo_path)
            
            commit_id = self._get_or_create_commit(repo_id, commit_sha, repo_path)
            
            # Discover files to analyze
            files_to_analyze = self._discover_files(repo_path)
            self.logger.info(f"Found {len(files_to_analyze)} files to analyze")
            
            # Analyze files in parallel
            file_results = self._analyze_files_parallel(files_to_analyze, repo_id, commit_id)
            
            # Build dependency graph
            dependency_count = self._build_dependency_graph(file_results, repo_id, commit_id)
            
            # Calculate repository-level metrics
            repo_metrics = self._calculate_repository_metrics(file_results)
            
            # Detect dead code
            dead_code_count = self._detect_dead_code(file_results, repo_id, commit_id)
            
            # Store results in database
            self._store_analysis_results(repo_id, commit_id, file_results, repo_metrics)
            
            analysis_duration = time.time() - start_time
            
            result = AnalysisResult(
                repository_id=repo_id,
                commit_sha=commit_sha,
                files_analyzed=len(file_results),
                symbols_found=sum(len(fr.symbols) for fr in file_results),
                dependencies_mapped=dependency_count,
                dead_code_detected=dead_code_count,
                complexity_score=repo_metrics.get('avg_complexity', 0),
                maintainability_index=repo_metrics.get('avg_maintainability', 0),
                analysis_duration=analysis_duration,
                errors=[],
                warnings=[]
            )
            
            self.logger.info(f"Repository analysis completed in {analysis_duration:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Repository analysis failed: {str(e)}")
            raise
    
    def analyze_file(self, file_path: str, repo_id: str, commit_id: str) -> FileAnalysis:
        """
        Analyze a single file
        
        Args:
            file_path: Path to the file to analyze
            repo_id: Repository identifier
            commit_id: Commit identifier
            
        Returns:
            FileAnalysis containing file-specific analysis data
        """
        self.logger.debug(f"Analyzing file: {file_path}")
        
        try:
            # Determine language
            language = self._detect_language(file_path)
            if not language:
                return FileAnalysis(
                    file_path=file_path,
                    language='unknown',
                    metrics={},
                    symbols=[],
                    dependencies=[],
                    dead_code=[],
                    errors=['Unknown file type']
                )
            
            # Validate file
            validation_result = self.validator.validate_file(file_path)
            if not validation_result.is_valid:
                return FileAnalysis(
                    file_path=file_path,
                    language=language,
                    metrics={},
                    symbols=[],
                    dependencies=[],
                    dead_code=[],
                    errors=validation_result.errors
                )
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Calculate file hash
            file_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Parse file and extract symbols
            symbols = self.graph_builder.extract_symbols(file_path, content, language)
            
            # Calculate metrics
            metrics = self.metrics_calculator.calculate_file_metrics(
                file_path, content, language, symbols
            )
            
            # Extract dependencies
            dependencies = self.graph_builder.extract_dependencies(
                file_path, content, language, symbols
            )
            
            # Detect dead code in file
            dead_code = self._detect_file_dead_code(file_path, content, language, symbols)
            
            return FileAnalysis(
                file_path=file_path,
                language=language,
                metrics=metrics,
                symbols=symbols,
                dependencies=dependencies,
                dead_code=dead_code,
                errors=[]
            )
            
        except Exception as e:
            self.logger.error(f"File analysis failed for {file_path}: {str(e)}")
            return FileAnalysis(
                file_path=file_path,
                language='unknown',
                metrics={},
                symbols=[],
                dependencies=[],
                dead_code=[],
                errors=[str(e)]
            )
    
    def _validate_repository(self, repo_path: str) -> bool:
        """Validate that the path is a valid repository"""
        path = Path(repo_path)
        return path.exists() and path.is_dir() and (path / '.git').exists()
    
    def _get_or_create_repository(self, repo_path: str) -> str:
        """Get or create repository record in database"""
        repo_name = Path(repo_path).name
        
        # Try to get existing repository
        repo_id = self.db_manager.get_repository_by_path(repo_path)
        if repo_id:
            return repo_id
        
        # Create new repository record
        return self.db_manager.create_repository(
            name=repo_name,
            full_name=repo_path,
            url=f"file://{repo_path}",
            language=self._detect_primary_language(repo_path)
        )
    
    def _get_current_commit(self, repo_path: str) -> str:
        """Get current commit SHA"""
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return 'unknown'
    
    def _get_or_create_commit(self, repo_id: str, commit_sha: str, repo_path: str) -> str:
        """Get or create commit record in database"""
        commit_id = self.db_manager.get_commit_by_sha(repo_id, commit_sha)
        if commit_id:
            return commit_id
        
        # Get commit details
        commit_info = self._get_commit_info(repo_path, commit_sha)
        
        return self.db_manager.create_commit(
            repository_id=repo_id,
            sha=commit_sha,
            message=commit_info.get('message', ''),
            author_name=commit_info.get('author_name', ''),
            author_email=commit_info.get('author_email', ''),
            committed_at=commit_info.get('committed_at')
        )
    
    def _discover_files(self, repo_path: str) -> List[str]:
        """Discover all analyzable files in the repository"""
        files = []
        repo_path = Path(repo_path)
        
        # Get all supported extensions
        supported_extensions = set()
        for exts in self.language_extensions.values():
            supported_extensions.update(exts)
        
        # Walk through repository
        for root, dirs, filenames in os.walk(repo_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '__pycache__', 'venv', 'env', 'build', 'dist',
                'target', 'bin', 'obj', 'out'
            }]
            
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix.lower() in supported_extensions:
                    files.append(str(file_path))
        
        return files
    
    def _analyze_files_parallel(self, files: List[str], repo_id: str, commit_id: str) -> List[FileAnalysis]:
        """Analyze files in parallel for better performance"""
        results = []
        max_workers = min(self.config.max_workers, len(files))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all file analysis tasks
            future_to_file = {
                executor.submit(self.analyze_file, file_path, repo_id, commit_id): file_path
                for file_path in files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to analyze {file_path}: {str(e)}")
                    # Create error result
                    results.append(FileAnalysis(
                        file_path=file_path,
                        language='unknown',
                        metrics={},
                        symbols=[],
                        dependencies=[],
                        dead_code=[],
                        errors=[str(e)]
                    ))
        
        return results
    
    def _build_dependency_graph(self, file_results: List[FileAnalysis], repo_id: str, commit_id: str) -> int:
        """Build dependency graph from file analysis results"""
        return self.graph_builder.build_dependency_graph(file_results, repo_id, commit_id)
    
    def _calculate_repository_metrics(self, file_results: List[FileAnalysis]) -> Dict[str, Any]:
        """Calculate repository-level metrics"""
        return self.metrics_calculator.calculate_repository_metrics(file_results)
    
    def _detect_dead_code(self, file_results: List[FileAnalysis], repo_id: str, commit_id: str) -> int:
        """Detect dead code across the repository"""
        # This would implement sophisticated dead code detection
        # For now, return sum of file-level dead code
        return sum(len(fr.dead_code) for fr in file_results)
    
    def _detect_file_dead_code(self, file_path: str, content: str, language: str, symbols: List[Dict]) -> List[Dict]:
        """Detect dead code within a single file"""
        # Placeholder implementation
        # Real implementation would use AST analysis to detect:
        # - Unused variables
        # - Unreachable code
        # - Unused imports
        # - Dead functions
        return []
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        extension = Path(file_path).suffix.lower()
        
        for language, extensions in self.language_extensions.items():
            if extension in extensions:
                return language
        
        return None
    
    def _detect_primary_language(self, repo_path: str) -> Optional[str]:
        """Detect the primary programming language of the repository"""
        language_counts = {}
        
        for file_path in self._discover_files(repo_path):
            language = self._detect_language(file_path)
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1
        
        if language_counts:
            return max(language_counts, key=language_counts.get)
        
        return None
    
    def _get_commit_info(self, repo_path: str, commit_sha: str) -> Dict[str, Any]:
        """Get detailed commit information"""
        import subprocess
        from datetime import datetime
        
        try:
            # Get commit details
            result = subprocess.run([
                'git', 'show', '--format=%H|%s|%an|%ae|%cn|%ce|%ct', '--no-patch', commit_sha
            ], cwd=repo_path, capture_output=True, text=True, check=True)
            
            parts = result.stdout.strip().split('|')
            if len(parts) >= 7:
                return {
                    'sha': parts[0],
                    'message': parts[1],
                    'author_name': parts[2],
                    'author_email': parts[3],
                    'committer_name': parts[4],
                    'committer_email': parts[5],
                    'committed_at': datetime.fromtimestamp(int(parts[6]))
                }
        except subprocess.CalledProcessError:
            pass
        
        return {
            'sha': commit_sha,
            'message': 'Unknown',
            'author_name': 'Unknown',
            'author_email': 'unknown@example.com',
            'committed_at': datetime.now()
        }
    
    def _store_analysis_results(self, repo_id: str, commit_id: str, 
                              file_results: List[FileAnalysis], repo_metrics: Dict[str, Any]):
        """Store analysis results in database"""
        self.db_manager.store_analysis_results(repo_id, commit_id, file_results, repo_metrics)


# Import time module at the top
import time

