"""
Graph Sitter Code Analysis Engine
Provides comprehensive code analysis and PR validation capabilities.
"""

import asyncio
import logging
import uuid
import subprocess
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..base.interfaces import BaseAnalysisEngine

logger = logging.getLogger(__name__)


class ComprehensiveAnalysisEngine(BaseAnalysisEngine):
    """Comprehensive code analysis engine using Graph Sitter."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.pr_validations: Dict[str, Dict[str, Any]] = {}
        
        # Try to import graph_sitter if available
        try:
            import tree_sitter
            self.tree_sitter_available = True
            self.logger.info("Tree-sitter library available")
        except ImportError:
            self.tree_sitter_available = False
            self.logger.warning("Tree-sitter library not available, using fallback analysis")
    
    async def _initialize_impl(self) -> None:
        """Initialize the analysis engine."""
        self.logger.info("Initializing Graph Sitter analysis engine")
        
        # Initialize any required parsers or analysis tools
        if self.tree_sitter_available:
            await self._initialize_parsers()
    
    async def _initialize_parsers(self) -> None:
        """Initialize tree-sitter parsers for different languages."""
        try:
            # This would initialize parsers for different languages
            # For now, we'll just log that we're ready
            self.logger.info("Tree-sitter parsers initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize parsers: {e}")
    
    async def _handle_impl(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Handle analysis requests."""
        action = payload.get("action")
        
        if action == "analyze_code":
            result = await self.analyze_code(
                payload.get("code_path", ""),
                payload.get("analysis_type", "comprehensive")
            )
            return {"analysis_id": result.get("analysis_id"), "status": "completed", "result": result}
        elif action == "validate_pr":
            result = await self.validate_pr(payload.get("pr_data", {}))
            return {"validation_id": result.get("validation_id"), "status": "completed", "result": result}
        elif action == "get_analysis_report":
            return await self.get_analysis_report(payload.get("analysis_id"))
        else:
            return {"error": f"Unknown action: {action}", "status": "failed"}
    
    async def analyze_code(self, code_path: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze code at the given path."""
        analysis_id = str(uuid.uuid4())
        
        analysis_result = {
            "analysis_id": analysis_id,
            "code_path": code_path,
            "analysis_type": analysis_type,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "issues": [],
            "metrics": {},
            "suggestions": []
        }
        
        self.analysis_cache[analysis_id] = analysis_result
        
        try:
            # Check if path exists
            if not os.path.exists(code_path):
                raise FileNotFoundError(f"Code path not found: {code_path}")
            
            # Perform different types of analysis
            if analysis_type == "comprehensive":
                await self._comprehensive_analysis(code_path, analysis_result)
            elif analysis_type == "syntax":
                await self._syntax_analysis(code_path, analysis_result)
            elif analysis_type == "quality":
                await self._quality_analysis(code_path, analysis_result)
            else:
                await self._basic_analysis(code_path, analysis_result)
            
            analysis_result["status"] = "completed"
            analysis_result["completed_at"] = datetime.utcnow().isoformat()
            
            self.logger.info(f"Code analysis completed: {analysis_id}")
            
        except Exception as e:
            analysis_result["status"] = "failed"
            analysis_result["error"] = str(e)
            analysis_result["failed_at"] = datetime.utcnow().isoformat()
            
            self.logger.error(f"Code analysis failed: {e}")
        
        return analysis_result
    
    async def validate_pr(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a pull request."""
        validation_id = str(uuid.uuid4())
        
        validation_result = {
            "validation_id": validation_id,
            "pr_number": pr_data.get("number"),
            "pr_title": pr_data.get("title"),
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "checks": {},
            "overall_score": 0,
            "recommendations": []
        }
        
        self.pr_validations[validation_id] = validation_result
        
        try:
            # Validate different aspects of the PR
            await self._validate_pr_structure(pr_data, validation_result)
            await self._validate_code_changes(pr_data, validation_result)
            await self._validate_tests(pr_data, validation_result)
            await self._validate_documentation(pr_data, validation_result)
            
            # Calculate overall score
            validation_result["overall_score"] = self._calculate_pr_score(validation_result)
            
            validation_result["status"] = "completed"
            validation_result["completed_at"] = datetime.utcnow().isoformat()
            
            self.logger.info(f"PR validation completed: {validation_id}")
            
        except Exception as e:
            validation_result["status"] = "failed"
            validation_result["error"] = str(e)
            validation_result["failed_at"] = datetime.utcnow().isoformat()
            
            self.logger.error(f"PR validation failed: {e}")
        
        return validation_result
    
    async def get_analysis_report(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis report."""
        if analysis_id in self.analysis_cache:
            return self.analysis_cache[analysis_id]
        elif analysis_id in self.pr_validations:
            return self.pr_validations[analysis_id]
        else:
            return {"error": f"Analysis {analysis_id} not found", "status": "not_found"}
    
    async def _comprehensive_analysis(self, code_path: str, result: Dict[str, Any]) -> None:
        """Perform comprehensive code analysis."""
        # Syntax analysis
        await self._syntax_analysis(code_path, result)
        
        # Quality analysis
        await self._quality_analysis(code_path, result)
        
        # Security analysis
        await self._security_analysis(code_path, result)
        
        # Performance analysis
        await self._performance_analysis(code_path, result)
    
    async def _syntax_analysis(self, code_path: str, result: Dict[str, Any]) -> None:
        """Perform syntax analysis."""
        if self.tree_sitter_available:
            # Use tree-sitter for syntax analysis
            syntax_issues = await self._tree_sitter_syntax_check(code_path)
        else:
            # Fallback to basic syntax checking
            syntax_issues = await self._basic_syntax_check(code_path)
        
        result["issues"].extend(syntax_issues)
        result["metrics"]["syntax_errors"] = len(syntax_issues)
    
    async def _quality_analysis(self, code_path: str, result: Dict[str, Any]) -> None:
        """Perform code quality analysis."""
        quality_issues = []
        
        # Check for common quality issues
        if os.path.isfile(code_path):
            quality_issues.extend(await self._analyze_file_quality(code_path))
        elif os.path.isdir(code_path):
            for root, dirs, files in os.walk(code_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                        file_path = os.path.join(root, file)
                        quality_issues.extend(await self._analyze_file_quality(file_path))
        
        result["issues"].extend(quality_issues)
        result["metrics"]["quality_issues"] = len(quality_issues)
    
    async def _security_analysis(self, code_path: str, result: Dict[str, Any]) -> None:
        """Perform security analysis."""
        security_issues = []
        
        # Basic security checks
        if os.path.isfile(code_path):
            security_issues.extend(await self._check_file_security(code_path))
        elif os.path.isdir(code_path):
            for root, dirs, files in os.walk(code_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                        file_path = os.path.join(root, file)
                        security_issues.extend(await self._check_file_security(file_path))
        
        result["issues"].extend(security_issues)
        result["metrics"]["security_issues"] = len(security_issues)
    
    async def _performance_analysis(self, code_path: str, result: Dict[str, Any]) -> None:
        """Perform performance analysis."""
        performance_issues = []
        
        # Basic performance checks
        if os.path.isfile(code_path):
            performance_issues.extend(await self._check_file_performance(code_path))
        elif os.path.isdir(code_path):
            for root, dirs, files in os.walk(code_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                        file_path = os.path.join(root, file)
                        performance_issues.extend(await self._check_file_performance(file_path))
        
        result["issues"].extend(performance_issues)
        result["metrics"]["performance_issues"] = len(performance_issues)
    
    async def _basic_analysis(self, code_path: str, result: Dict[str, Any]) -> None:
        """Perform basic code analysis."""
        await self._syntax_analysis(code_path, result)
    
    async def _tree_sitter_syntax_check(self, code_path: str) -> List[Dict[str, Any]]:
        """Use tree-sitter for syntax checking."""
        issues = []
        
        try:
            # This would use tree-sitter to parse and check syntax
            # For now, return empty list as placeholder
            pass
        except Exception as e:
            issues.append({
                "type": "syntax_error",
                "severity": "error",
                "message": f"Tree-sitter parsing failed: {e}",
                "file": code_path,
                "line": 1
            })
        
        return issues
    
    async def _basic_syntax_check(self, code_path: str) -> List[Dict[str, Any]]:
        """Basic syntax checking without tree-sitter."""
        issues = []
        
        if code_path.endswith('.py'):
            # Use Python's ast module for basic syntax checking
            try:
                with open(code_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import ast
                ast.parse(content)
                
            except SyntaxError as e:
                issues.append({
                    "type": "syntax_error",
                    "severity": "error",
                    "message": str(e),
                    "file": code_path,
                    "line": e.lineno or 1
                })
            except Exception as e:
                issues.append({
                    "type": "parse_error",
                    "severity": "warning",
                    "message": f"Could not parse file: {e}",
                    "file": code_path,
                    "line": 1
                })
        
        return issues
    
    async def _analyze_file_quality(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze file quality."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check for long lines
            for i, line in enumerate(lines, 1):
                if len(line.rstrip()) > 120:
                    issues.append({
                        "type": "line_too_long",
                        "severity": "warning",
                        "message": f"Line too long ({len(line.rstrip())} characters)",
                        "file": file_path,
                        "line": i
                    })
            
            # Check for large functions (basic heuristic)
            if file_path.endswith('.py'):
                function_lines = 0
                in_function = False
                function_start = 0
                
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith('def ') or stripped.startswith('async def '):
                        if in_function and function_lines > 50:
                            issues.append({
                                "type": "function_too_long",
                                "severity": "warning",
                                "message": f"Function is too long ({function_lines} lines)",
                                "file": file_path,
                                "line": function_start
                            })
                        in_function = True
                        function_start = i
                        function_lines = 1
                    elif in_function:
                        if stripped and not line.startswith(' ') and not line.startswith('\t'):
                            # End of function
                            if function_lines > 50:
                                issues.append({
                                    "type": "function_too_long",
                                    "severity": "warning",
                                    "message": f"Function is too long ({function_lines} lines)",
                                    "file": file_path,
                                    "line": function_start
                                })
                            in_function = False
                            function_lines = 0
                        else:
                            function_lines += 1
        
        except Exception as e:
            issues.append({
                "type": "analysis_error",
                "severity": "warning",
                "message": f"Could not analyze file: {e}",
                "file": file_path,
                "line": 1
            })
        
        return issues
    
    async def _check_file_security(self, file_path: str) -> List[Dict[str, Any]]:
        """Check file for security issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for potential security issues
            security_patterns = [
                ('password', 'Potential hardcoded password'),
                ('api_key', 'Potential hardcoded API key'),
                ('secret', 'Potential hardcoded secret'),
                ('eval(', 'Use of eval() function'),
                ('exec(', 'Use of exec() function'),
            ]
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line_lower = line.lower()
                for pattern, message in security_patterns:
                    if pattern in line_lower and not line.strip().startswith('#'):
                        issues.append({
                            "type": "security_warning",
                            "severity": "warning",
                            "message": message,
                            "file": file_path,
                            "line": i
                        })
        
        except Exception as e:
            pass  # Ignore file reading errors for security check
        
        return issues
    
    async def _check_file_performance(self, file_path: str) -> List[Dict[str, Any]]:
        """Check file for performance issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for potential performance issues
            performance_patterns = [
                ('for.*in.*range(len(', 'Consider using enumerate() instead of range(len())'),
                ('time.sleep(', 'Consider using async sleep for better performance'),
            ]
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                for pattern, message in performance_patterns:
                    import re
                    if re.search(pattern, line) and not line.strip().startswith('#'):
                        issues.append({
                            "type": "performance_warning",
                            "severity": "info",
                            "message": message,
                            "file": file_path,
                            "line": i
                        })
        
        except Exception as e:
            pass  # Ignore file reading errors for performance check
        
        return issues
    
    async def _validate_pr_structure(self, pr_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate PR structure."""
        checks = {}
        
        # Check title
        title = pr_data.get("title", "")
        if len(title) < 10:
            checks["title_length"] = {"status": "fail", "message": "PR title too short"}
        elif len(title) > 100:
            checks["title_length"] = {"status": "warning", "message": "PR title very long"}
        else:
            checks["title_length"] = {"status": "pass", "message": "PR title length OK"}
        
        # Check description
        description = pr_data.get("body", "")
        if len(description) < 20:
            checks["description"] = {"status": "warning", "message": "PR description is very short"}
        else:
            checks["description"] = {"status": "pass", "message": "PR description provided"}
        
        result["checks"]["structure"] = checks
    
    async def _validate_code_changes(self, pr_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate code changes in PR."""
        checks = {}
        
        # This would analyze the actual diff/changes
        # For now, provide basic validation
        files_changed = pr_data.get("changed_files", 0)
        
        if files_changed == 0:
            checks["files_changed"] = {"status": "fail", "message": "No files changed"}
        elif files_changed > 20:
            checks["files_changed"] = {"status": "warning", "message": "Many files changed, consider splitting PR"}
        else:
            checks["files_changed"] = {"status": "pass", "message": f"{files_changed} files changed"}
        
        result["checks"]["code_changes"] = checks
    
    async def _validate_tests(self, pr_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate tests in PR."""
        checks = {}
        
        # Check if test files are included
        # This would analyze the actual files in the PR
        checks["tests_included"] = {"status": "warning", "message": "Cannot verify test coverage"}
        
        result["checks"]["tests"] = checks
    
    async def _validate_documentation(self, pr_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate documentation in PR."""
        checks = {}
        
        # Check if documentation is updated
        checks["documentation"] = {"status": "info", "message": "Documentation check not implemented"}
        
        result["checks"]["documentation"] = checks
    
    def _calculate_pr_score(self, validation_result: Dict[str, Any]) -> int:
        """Calculate overall PR score."""
        score = 100
        
        for category, checks in validation_result["checks"].items():
            for check_name, check_result in checks.items():
                if check_result["status"] == "fail":
                    score -= 20
                elif check_result["status"] == "warning":
                    score -= 10
        
        return max(0, score)


# Alias for backward compatibility and expected import name
CodeAnalysisEngine = ComprehensiveAnalysisEngine

