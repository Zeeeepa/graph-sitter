"""
Graph-sitter code analysis service for comprehensive code quality checks
"""
import os
import asyncio
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import tree_sitter
from tree_sitter import Language, Parser, Node
import subprocess
import logging

from backend.config import settings
from backend.database import DatabaseManager, AnalysisResult
from backend.services.github_service import GitHubService
from backend.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class GraphSitterAnalyzer:
    """Graph-sitter based code analyzer for multiple languages"""
    
    def __init__(self):
        self.languages = {}
        self.parsers = {}
        self._setup_languages()
    
    def _setup_languages(self):
        """Setup tree-sitter languages"""
        try:
            # Build language libraries if not exists
            self._build_language_libraries()
            
            # Load languages
            for lang in settings.GRAPH_SITTER_LANGUAGES:
                try:
                    lib_path = f"./tree-sitter-{lang}.so"
                    if os.path.exists(lib_path):
                        language = Language(lib_path, lang)
                        parser = Parser()
                        parser.set_language(language)
                        
                        self.languages[lang] = language
                        self.parsers[lang] = parser
                        logger.info(f"Loaded tree-sitter language: {lang}")
                except Exception as e:
                    logger.warning(f"Failed to load language {lang}: {e}")
        except Exception as e:
            logger.error(f"Failed to setup tree-sitter languages: {e}")
    
    def _build_language_libraries(self):
        """Build tree-sitter language libraries"""
        for lang in settings.GRAPH_SITTER_LANGUAGES:
            lib_path = f"./tree-sitter-{lang}.so"
            if not os.path.exists(lib_path):
                try:
                    # Clone and build language grammar
                    repo_url = f"https://github.com/tree-sitter/tree-sitter-{lang}"
                    temp_dir = tempfile.mkdtemp()
                    
                    subprocess.run([
                        "git", "clone", "--depth", "1", repo_url, 
                        os.path.join(temp_dir, f"tree-sitter-{lang}")
                    ], check=True, capture_output=True)
                    
                    # Build shared library
                    lang_dir = os.path.join(temp_dir, f"tree-sitter-{lang}")
                    subprocess.run([
                        "gcc", "-shared", "-fPIC", "-O2",
                        "-I", "src",
                        "src/parser.c",
                        "-o", lib_path
                    ], cwd=lang_dir, check=True, capture_output=True)
                    
                    # Cleanup
                    shutil.rmtree(temp_dir)
                    logger.info(f"Built tree-sitter library for {lang}")
                    
                except Exception as e:
                    logger.warning(f"Failed to build {lang} library: {e}")
    
    def get_language_from_file(self, file_path: str) -> Optional[str]:
        """Determine language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext)
    
    def parse_file(self, file_path: str, content: str) -> Optional[Node]:
        """Parse file content using appropriate tree-sitter parser"""
        language = self.get_language_from_file(file_path)
        if not language or language not in self.parsers:
            return None
        
        parser = self.parsers[language]
        tree = parser.parse(content.encode('utf-8'))
        return tree.root_node
    
    def find_dead_code(self, root_node: Node, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Find potentially dead code (unused functions, variables)"""
        issues = []
        
        # Find all function definitions
        functions = self._find_nodes_by_type(root_node, ['function_definition', 'function_declaration', 'method_definition'])
        function_names = set()
        
        for func in functions:
            name_node = self._get_function_name(func)
            if name_node:
                function_names.add(name_node.text.decode('utf-8'))
        
        # Find all function calls
        calls = self._find_nodes_by_type(root_node, ['call_expression', 'function_call'])
        called_functions = set()
        
        for call in calls:
            name_node = self._get_call_name(call)
            if name_node:
                called_functions.add(name_node.text.decode('utf-8'))
        
        # Find unused functions
        unused_functions = function_names - called_functions
        
        for func in functions:
            name_node = self._get_function_name(func)
            if name_node and name_node.text.decode('utf-8') in unused_functions:
                # Skip main functions and special methods
                func_name = name_node.text.decode('utf-8')
                if not self._is_special_function(func_name):
                    issues.append({
                        'type': 'dead_code',
                        'severity': 'medium',
                        'message': f'Potentially unused function: {func_name}',
                        'line': func.start_point[0] + 1,
                        'column': func.start_point[1],
                        'suggestion': f'Consider removing unused function {func_name} or verify it is actually used'
                    })
        
        return issues
    
    def find_unused_parameters(self, root_node: Node, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Find unused function parameters"""
        issues = []
        
        functions = self._find_nodes_by_type(root_node, ['function_definition', 'function_declaration', 'method_definition'])
        
        for func in functions:
            params = self._get_function_parameters(func)
            func_body = self._get_function_body(func)
            
            if not func_body:
                continue
            
            for param in params:
                param_name = param.text.decode('utf-8')
                
                # Skip special parameters
                if param_name.startswith('_') or param_name in ['self', 'cls', 'args', 'kwargs']:
                    continue
                
                # Check if parameter is used in function body
                if not self._is_identifier_used_in_node(func_body, param_name):
                    issues.append({
                        'type': 'unused_parameter',
                        'severity': 'low',
                        'message': f'Unused parameter: {param_name}',
                        'line': param.start_point[0] + 1,
                        'column': param.start_point[1],
                        'suggestion': f'Remove unused parameter {param_name} or prefix with underscore if intentionally unused'
                    })
        
        return issues
    
    def find_security_issues(self, root_node: Node, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Find potential security vulnerabilities"""
        issues = []
        
        # Check for dangerous function calls
        dangerous_patterns = {
            'eval': 'Use of eval() can lead to code injection vulnerabilities',
            'exec': 'Use of exec() can lead to code injection vulnerabilities',
            'subprocess.call': 'Direct subprocess calls may be vulnerable to injection',
            'os.system': 'Use of os.system() can lead to command injection',
            'pickle.loads': 'Unpickling untrusted data can lead to code execution',
            'yaml.load': 'Use yaml.safe_load() instead of yaml.load() to prevent code execution'
        }
        
        calls = self._find_nodes_by_type(root_node, ['call_expression', 'function_call'])
        
        for call in calls:
            call_text = call.text.decode('utf-8')
            
            for pattern, message in dangerous_patterns.items():
                if pattern in call_text:
                    issues.append({
                        'type': 'security_vulnerability',
                        'severity': 'high',
                        'message': f'Potential security issue: {message}',
                        'line': call.start_point[0] + 1,
                        'column': call.start_point[1],
                        'suggestion': f'Review usage of {pattern} and consider safer alternatives'
                    })
        
        # Check for hardcoded secrets
        string_literals = self._find_nodes_by_type(root_node, ['string_literal', 'string'])
        
        secret_patterns = ['password', 'secret', 'key', 'token', 'api_key']
        
        for string_node in string_literals:
            string_content = string_node.text.decode('utf-8').lower()
            
            for pattern in secret_patterns:
                if pattern in string_content and len(string_content) > 10:
                    issues.append({
                        'type': 'hardcoded_secret',
                        'severity': 'critical',
                        'message': f'Potential hardcoded secret detected',
                        'line': string_node.start_point[0] + 1,
                        'column': string_node.start_point[1],
                        'suggestion': 'Move secrets to environment variables or secure configuration'
                    })
        
        return issues
    
    def find_code_quality_issues(self, root_node: Node, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Find code quality and maintainability issues"""
        issues = []
        
        # Check function complexity (number of nested blocks)
        functions = self._find_nodes_by_type(root_node, ['function_definition', 'function_declaration', 'method_definition'])
        
        for func in functions:
            complexity = self._calculate_cyclomatic_complexity(func)
            
            if complexity > 10:
                func_name = self._get_function_name(func)
                name = func_name.text.decode('utf-8') if func_name else 'unknown'
                
                issues.append({
                    'type': 'high_complexity',
                    'severity': 'medium',
                    'message': f'Function {name} has high cyclomatic complexity ({complexity})',
                    'line': func.start_point[0] + 1,
                    'column': func.start_point[1],
                    'suggestion': f'Consider breaking down function {name} into smaller, more focused functions'
                })
        
        # Check for long functions
        for func in functions:
            func_lines = func.end_point[0] - func.start_point[0]
            
            if func_lines > 50:
                func_name = self._get_function_name(func)
                name = func_name.text.decode('utf-8') if func_name else 'unknown'
                
                issues.append({
                    'type': 'long_function',
                    'severity': 'low',
                    'message': f'Function {name} is very long ({func_lines} lines)',
                    'line': func.start_point[0] + 1,
                    'column': func.start_point[1],
                    'suggestion': f'Consider breaking down function {name} into smaller functions'
                })
        
        return issues
    
    def _find_nodes_by_type(self, node: Node, types: List[str]) -> List[Node]:
        """Find all nodes of specified types"""
        results = []
        
        def traverse(n):
            if n.type in types:
                results.append(n)
            for child in n.children:
                traverse(child)
        
        traverse(node)
        return results
    
    def _get_function_name(self, func_node: Node) -> Optional[Node]:
        """Extract function name from function definition node"""
        for child in func_node.children:
            if child.type == 'identifier':
                return child
        return None
    
    def _get_call_name(self, call_node: Node) -> Optional[Node]:
        """Extract function name from call expression node"""
        for child in call_node.children:
            if child.type == 'identifier':
                return child
            elif child.type == 'attribute':
                # Handle method calls like obj.method()
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        return subchild
        return None
    
    def _get_function_parameters(self, func_node: Node) -> List[Node]:
        """Extract parameter nodes from function definition"""
        params = []
        
        for child in func_node.children:
            if child.type == 'parameters':
                for param_child in child.children:
                    if param_child.type == 'identifier':
                        params.append(param_child)
        
        return params
    
    def _get_function_body(self, func_node: Node) -> Optional[Node]:
        """Extract function body node"""
        for child in func_node.children:
            if child.type in ['block', 'suite']:
                return child
        return None
    
    def _is_identifier_used_in_node(self, node: Node, identifier: str) -> bool:
        """Check if identifier is used within a node"""
        def traverse(n):
            if n.type == 'identifier' and n.text.decode('utf-8') == identifier:
                return True
            for child in n.children:
                if traverse(child):
                    return True
            return False
        
        return traverse(node)
    
    def _is_special_function(self, func_name: str) -> bool:
        """Check if function is a special function that shouldn't be flagged as unused"""
        special_functions = {
            'main', '__init__', '__str__', '__repr__', '__len__', '__getitem__',
            '__setitem__', '__delitem__', '__iter__', '__next__', '__enter__',
            '__exit__', '__call__', '__eq__', '__ne__', '__lt__', '__le__',
            '__gt__', '__ge__', '__hash__', '__bool__', '__contains__'
        }
        
        return func_name in special_functions or func_name.startswith('test_')
    
    def _calculate_cyclomatic_complexity(self, func_node: Node) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_types = ['if_statement', 'while_statement', 'for_statement', 'try_statement', 'except_clause']
        
        def traverse(n):
            nonlocal complexity
            if n.type in decision_types:
                complexity += 1
            for child in n.children:
                traverse(child)
        
        traverse(func_node)
        return complexity


class CodeAnalysisService:
    """Main service for code analysis using Graph-sitter"""
    
    def __init__(self, websocket_manager: WebSocketManager = None):
        self.analyzer = GraphSitterAnalyzer()
        self.websocket_manager = websocket_manager or WebSocketManager()
    
    async def analyze_repository(self, project_id: str, github_token: str, owner: str, repo: str, branch: str = None) -> Dict[str, Any]:
        """Analyze entire repository for code quality issues"""
        try:
            # Clone repository to temporary directory
            temp_dir = await self._clone_repository(github_token, owner, repo, branch)
            
            # Broadcast analysis start
            await self.websocket_manager.send_code_analysis_update(project_id, {
                'status': 'started',
                'message': f'Starting code analysis for {owner}/{repo}'
            })
            
            # Analyze all files
            analysis_results = []
            total_files = 0
            processed_files = 0
            
            # Count total files first
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if self.analyzer.get_language_from_file(file):
                        total_files += 1
            
            # Process files
            for root, dirs, files in os.walk(temp_dir):
                # Skip common directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, temp_dir)
                    
                    if self.analyzer.get_language_from_file(file):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            file_results = await self._analyze_file(relative_path, content, project_id)
                            analysis_results.extend(file_results)
                            
                            processed_files += 1
                            
                            # Broadcast progress
                            progress = int((processed_files / total_files) * 100)
                            await self.websocket_manager.send_code_analysis_update(project_id, {
                                'status': 'processing',
                                'progress': progress,
                                'current_file': relative_path,
                                'processed_files': processed_files,
                                'total_files': total_files
                            })
                            
                        except Exception as e:
                            logger.error(f"Error analyzing file {relative_path}: {e}")
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            # Save results to database
            await self._save_analysis_results(project_id, analysis_results, owner, repo, branch)
            
            # Broadcast completion
            await self.websocket_manager.send_code_analysis_update(project_id, {
                'status': 'completed',
                'total_issues': len(analysis_results),
                'issues_by_severity': self._group_by_severity(analysis_results),
                'issues_by_type': self._group_by_type(analysis_results)
            })
            
            return {
                'status': 'completed',
                'total_files_analyzed': processed_files,
                'total_issues': len(analysis_results),
                'issues': analysis_results,
                'summary': {
                    'by_severity': self._group_by_severity(analysis_results),
                    'by_type': self._group_by_type(analysis_results)
                }
            }
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            await self.websocket_manager.send_code_analysis_update(project_id, {
                'status': 'failed',
                'error': str(e)
            })
            raise
    
    async def _clone_repository(self, github_token: str, owner: str, repo: str, branch: str = None) -> str:
        """Clone repository to temporary directory"""
        temp_dir = tempfile.mkdtemp()
        
        # Use GitHub token for authentication
        repo_url = f"https://{github_token}@github.com/{owner}/{repo}.git"
        
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd.extend(["-b", branch])
        cmd.extend([repo_url, temp_dir])
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            shutil.rmtree(temp_dir)
            raise Exception(f"Failed to clone repository: {stderr.decode()}")
        
        return temp_dir
    
    async def _analyze_file(self, file_path: str, content: str, project_id: str) -> List[Dict[str, Any]]:
        """Analyze single file for issues"""
        root_node = self.analyzer.parse_file(file_path, content)
        if not root_node:
            return []
        
        issues = []
        
        # Run all analysis types
        issues.extend(self.analyzer.find_dead_code(root_node, content, file_path))
        issues.extend(self.analyzer.find_unused_parameters(root_node, content, file_path))
        issues.extend(self.analyzer.find_security_issues(root_node, content, file_path))
        issues.extend(self.analyzer.find_code_quality_issues(root_node, content, file_path))
        
        # Add file path to all issues
        for issue in issues:
            issue['file_path'] = file_path
            issue['project_id'] = project_id
        
        return issues
    
    async def _save_analysis_results(self, project_id: str, results: List[Dict[str, Any]], owner: str, repo: str, branch: str):
        """Save analysis results to database"""
        for result in results:
            analysis_data = {
                'id': f"{project_id}_{result['file_path']}_{result['line']}_{result['type']}",
                'project_id': project_id,
                'branch': branch or 'main',
                'analysis_type': result['type'],
                'file_path': result['file_path'],
                'line_number': result['line'],
                'issue_type': result['type'],
                'severity': result['severity'],
                'message': result['message'],
                'suggestion': result.get('suggestion', ''),
                'metadata': {
                    'column': result.get('column', 0),
                    'owner': owner,
                    'repo': repo
                }
            }
            
            # Save to database (implement actual database save)
            # await DatabaseManager.create_analysis_result(analysis_data)
    
    def _group_by_severity(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group results by severity"""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for result in results:
            severity = result.get('severity', 'low')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    def _group_by_type(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group results by issue type"""
        type_counts = {}
        
        for result in results:
            issue_type = result.get('type', 'unknown')
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        return type_counts
    
    async def get_analysis_results(self, project_id: str) -> List[Dict[str, Any]]:
        """Get stored analysis results for a project"""
        # Implement database query
        # return await DatabaseManager.get_analysis_results(project_id)
        return []
    
    async def resolve_issue(self, project_id: str, issue_id: str) -> bool:
        """Mark an analysis issue as resolved"""
        # Implement database update
        # return await DatabaseManager.resolve_analysis_issue(issue_id)
        return True

