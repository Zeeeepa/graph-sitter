#!/usr/bin/env python3
"""
Diagnostic Streaming Enhancement for Existing Serena Integration
==============================================================

This module enhances the existing Serena error integration with real-time
diagnostic streaming capabilities. It builds on the existing 24 error types
and analysis infrastructure.
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import logging
from datetime import datetime
from dataclasses import asdict

# Add paths for imports
current_dir = Path(__file__).parent
graph_sitter_root = current_dir.parent.parent
src_path = graph_sitter_root / "src"
sys.path.insert(0, str(src_path))

# Import existing Serena error integration
from serena_error_integration import (
    SerenaErrorAnalyzer,
    CodeError,
    ErrorSeverity,
    ErrorCategory
)

# Import graph-sitter context
from graph_sitter.codebase.codebase_context import CodebaseContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiagnosticStreamer:
    """Real-time diagnostic streaming using existing Serena error analysis."""
    
    def __init__(self):
        self.error_analyzer = SerenaErrorAnalyzer()  # Use existing analyzer
        self.active_streams: Dict[str, Set] = {}  # repo_url -> set of websockets
        self.diagnostic_cache: Dict[str, List[CodeError]] = {}
        self.last_analysis: Dict[str, datetime] = {}
        
    async def start_diagnostic_stream(self, repo_url: str, codebase, websocket):
        """Start real-time diagnostic streaming for a repository."""
        try:
            # Initialize stream for this repo
            if repo_url not in self.active_streams:
                self.active_streams[repo_url] = set()
            self.active_streams[repo_url].add(websocket)
            
            logger.info(f"Started diagnostic stream for {repo_url}")
            
            # Run initial comprehensive error analysis using existing analyzer
            await self.run_comprehensive_error_analysis(repo_url, codebase, websocket)
            
            # Start periodic updates (every 30 seconds)
            asyncio.create_task(self.periodic_diagnostic_updates(repo_url, codebase))
            
        except Exception as e:
            logger.error(f"Error starting diagnostic stream: {e}")
            await self.send_diagnostic_error(websocket, str(e))
    
    async def run_comprehensive_error_analysis(self, repo_url: str, codebase, websocket):
        """Run comprehensive error analysis using existing Serena analyzer."""
        try:
            await self.send_diagnostic_update(websocket, "Starting error analysis...", "info")
            
            # Use existing error analyzer methods
            errors = []
            files_analyzed = 0
            total_files = len(list(codebase.files))
            
            for file in codebase.files:
                try:
                    # Analyze file using existing error detection patterns
                    file_errors = await self.analyze_file_errors(file)
                    errors.extend(file_errors)
                    files_analyzed += 1
                    
                    # Send progress update
                    if files_analyzed % 10 == 0:
                        progress = (files_analyzed / total_files) * 100
                        await self.send_diagnostic_update(
                            websocket, 
                            f"Analyzed {files_analyzed}/{total_files} files", 
                            "progress",
                            {"progress": progress, "errors_found": len(errors)}
                        )
                        
                except Exception as e:
                    logger.error(f"Error analyzing file {file.name}: {e}")
                    continue
            
            # Cache results
            self.diagnostic_cache[repo_url] = errors
            self.last_analysis[repo_url] = datetime.now()
            
            # Categorize errors using existing error categories
            error_summary = self.categorize_errors(errors)
            
            # Send comprehensive results
            await self.send_diagnostic_results(websocket, {
                "repo_url": repo_url,
                "total_errors": len(errors),
                "files_analyzed": files_analyzed,
                "error_summary": error_summary,
                "errors": [self.serialize_error(error) for error in errors[:100]],  # Limit for performance
                "analysis_timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in comprehensive error analysis: {e}")
            await self.send_diagnostic_error(websocket, str(e))
    
    async def analyze_file_errors(self, file) -> List[CodeError]:
        """Analyze file for errors using existing Serena patterns."""
        errors = []
        
        try:
            # Use existing error analyzer patterns
            file_content = getattr(file, 'source', '')
            if not file_content:
                return errors
            
            # Check syntax errors
            syntax_errors = self.error_analyzer._check_syntax_errors(file_content, file.filepath)
            errors.extend(syntax_errors)
            
            # Check import errors
            import_errors = self.error_analyzer._check_import_errors(file_content, file.filepath)
            errors.extend(import_errors)
            
            # Check security vulnerabilities
            security_errors = self.error_analyzer._check_security_vulnerabilities(file_content, file.filepath)
            errors.extend(security_errors)
            
            # Check code smells
            code_smell_errors = self.error_analyzer._check_code_smells(file_content, file.filepath)
            errors.extend(code_smell_errors)
            
            # Check performance issues
            performance_errors = self.error_analyzer._check_performance_issues(file_content, file.filepath)
            errors.extend(performance_errors)
            
        except Exception as e:
            logger.error(f"Error analyzing file {file.name}: {e}")
            # Create error for analysis failure
            errors.append(CodeError(
                id=f"analysis_error_{hash(file.filepath)}",
                category=ErrorCategory.LOGIC,
                severity=ErrorSeverity.LOW,
                message=f"Analysis error: {str(e)}",
                filepath=file.filepath,
                line_start=1,
                line_end=1
            ))
        
        return errors
    
    def categorize_errors(self, errors: List[CodeError]) -> Dict[str, Any]:
        """Categorize errors using existing error categories."""
        summary = {
            "by_severity": {severity.value: 0 for severity in ErrorSeverity},
            "by_category": {category.value: 0 for category in ErrorCategory},
            "critical_files": [],
            "most_common_errors": []
        }
        
        file_error_counts = {}
        error_type_counts = {}
        
        for error in errors:
            # Count by severity
            summary["by_severity"][error.severity.value] += 1
            
            # Count by category
            summary["by_category"][error.category.value] += 1
            
            # Track files with most errors
            if error.filepath not in file_error_counts:
                file_error_counts[error.filepath] = 0
            file_error_counts[error.filepath] += 1
            
            # Track most common error types
            error_key = f"{error.category.value}_{error.severity.value}"
            if error_key not in error_type_counts:
                error_type_counts[error_key] = 0
            error_type_counts[error_key] += 1
        
        # Get top problematic files
        summary["critical_files"] = sorted(
            file_error_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Get most common error types
        summary["most_common_errors"] = sorted(
            error_type_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return summary
    
    def serialize_error(self, error: CodeError) -> Dict[str, Any]:
        """Serialize CodeError for JSON transmission."""
        return {
            "id": error.id,
            "category": error.category.value,
            "severity": error.severity.value,
            "message": error.message,
            "filepath": error.filepath,
            "line_start": error.line_start,
            "line_end": error.line_end,
            "column_start": error.column_start,
            "column_end": error.column_end,
            "context_lines": error.context_lines or [],
            "suggested_fix": error.suggested_fix,
            "related_errors": error.related_errors or [],
            "affected_functions": error.affected_functions or [],
            "blast_radius": error.blast_radius
        }
    
    async def periodic_diagnostic_updates(self, repo_url: str, codebase):
        """Run periodic diagnostic updates."""
        while repo_url in self.active_streams and self.active_streams[repo_url]:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Check if we still have active connections
                if not self.active_streams.get(repo_url):
                    break
                
                # Run incremental analysis
                await self.run_incremental_analysis(repo_url, codebase)
                
            except Exception as e:
                logger.error(f"Error in periodic updates for {repo_url}: {e}")
                break
    
    async def run_incremental_analysis(self, repo_url: str, codebase):
        """Run incremental diagnostic analysis."""
        try:
            # For now, run a lightweight check
            # In a full implementation, this would check for file changes
            current_time = datetime.now()
            last_check = self.last_analysis.get(repo_url, current_time)
            
            # Send heartbeat to active connections
            if repo_url in self.active_streams:
                for websocket in list(self.active_streams[repo_url]):
                    try:
                        await self.send_diagnostic_update(
                            websocket,
                            f"Diagnostic monitoring active - last check: {last_check.strftime('%H:%M:%S')}",
                            "heartbeat",
                            {"last_check": last_check.isoformat()}
                        )
                    except Exception as e:
                        # Remove disconnected websocket
                        self.active_streams[repo_url].discard(websocket)
                        logger.info(f"Removed disconnected websocket from {repo_url}")
                        
        except Exception as e:
            logger.error(f"Error in incremental analysis: {e}")
    
    async def send_diagnostic_update(self, websocket, message: str, update_type: str, data: Dict = None):
        """Send diagnostic update to websocket."""
        try:
            update = {
                "type": "diagnostic_update",
                "update_type": update_type,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "data": data or {}
            }
            await websocket.send_text(json.dumps(update))
        except Exception as e:
            logger.error(f"Error sending diagnostic update: {e}")
    
    async def send_diagnostic_results(self, websocket, results: Dict):
        """Send comprehensive diagnostic results."""
        try:
            message = {
                "type": "diagnostic_results",
                "data": results,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending diagnostic results: {e}")
    
    async def send_diagnostic_error(self, websocket, error_message: str):
        """Send diagnostic error message."""
        try:
            message = {
                "type": "diagnostic_error",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending diagnostic error: {e}")
    
    def stop_diagnostic_stream(self, repo_url: str, websocket):
        """Stop diagnostic streaming for a websocket."""
        if repo_url in self.active_streams:
            self.active_streams[repo_url].discard(websocket)
            if not self.active_streams[repo_url]:
                del self.active_streams[repo_url]
                logger.info(f"Stopped diagnostic stream for {repo_url}")

# Add methods to existing SerenaErrorAnalyzer class
class EnhancedSerenaErrorAnalyzer(SerenaErrorAnalyzer):
    """Enhanced version of existing SerenaErrorAnalyzer with streaming capabilities."""
    
    def _check_syntax_errors(self, content: str, filepath: str) -> List[CodeError]:
        """Check for syntax errors using existing patterns."""
        errors = []
        try:
            # Use existing syntax error patterns
            for pattern_name, pattern_info in self.error_patterns.items():
                if 'syntax' in pattern_name.lower():
                    for pattern in pattern_info['patterns']:
                        import re
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            errors.append(CodeError(
                                id=f"syntax_{hash(f'{filepath}_{line_num}_{pattern}')}",
                                category=pattern_info['category'],
                                severity=pattern_info['severity'],
                                message=f"Syntax error detected: {match.group()}",
                                filepath=filepath,
                                line_start=line_num,
                                line_end=line_num,
                                context_lines=[content.split('\n')[max(0, line_num-2):line_num+1]]
                            ))
        except Exception as e:
            logger.error(f"Error checking syntax errors: {e}")
        return errors
    
    def _check_import_errors(self, content: str, filepath: str) -> List[CodeError]:
        """Check for import errors using existing patterns."""
        errors = []
        try:
            # Use existing import error patterns
            for pattern_name, pattern_info in self.error_patterns.items():
                if 'import' in pattern_name.lower():
                    for pattern in pattern_info['patterns']:
                        import re
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            errors.append(CodeError(
                                id=f"import_{hash(f'{filepath}_{line_num}_{pattern}')}",
                                category=pattern_info['category'],
                                severity=pattern_info['severity'],
                                message=f"Import error detected: {match.group()}",
                                filepath=filepath,
                                line_start=line_num,
                                line_end=line_num,
                                suggested_fix="Check import path and ensure module is available"
                            ))
        except Exception as e:
            logger.error(f"Error checking import errors: {e}")
        return errors
    
    def _check_security_vulnerabilities(self, content: str, filepath: str) -> List[CodeError]:
        """Check for security vulnerabilities using existing patterns."""
        errors = []
        try:
            # Use existing security patterns
            for pattern_name, pattern_info in self.error_patterns.items():
                if 'security' in pattern_name.lower():
                    for pattern in pattern_info['patterns']:
                        import re
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            errors.append(CodeError(
                                id=f"security_{hash(f'{filepath}_{line_num}_{pattern}')}",
                                category=ErrorCategory.SECURITY,
                                severity=ErrorSeverity.HIGH,
                                message=f"Security vulnerability detected: {match.group()}",
                                filepath=filepath,
                                line_start=line_num,
                                line_end=line_num,
                                suggested_fix="Review security implications and use safer alternatives"
                            ))
        except Exception as e:
            logger.error(f"Error checking security vulnerabilities: {e}")
        return errors
    
    def _check_code_smells(self, content: str, filepath: str) -> List[CodeError]:
        """Check for code smells using existing patterns."""
        errors = []
        try:
            # Check for long lines
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if len(line) > 120:
                    errors.append(CodeError(
                        id=f"long_line_{hash(f'{filepath}_{i}')}",
                        category=ErrorCategory.STYLE,
                        severity=ErrorSeverity.LOW,
                        message=f"Line too long ({len(line)} characters)",
                        filepath=filepath,
                        line_start=i + 1,
                        line_end=i + 1,
                        suggested_fix="Break long line into multiple lines"
                    ))
        except Exception as e:
            logger.error(f"Error checking code smells: {e}")
        return errors
    
    def _check_performance_issues(self, content: str, filepath: str) -> List[CodeError]:
        """Check for performance issues using existing patterns."""
        errors = []
        try:
            # Check for potential performance issues
            import re
            performance_patterns = [
                (r'for.*in.*range\(len\(', "Use enumerate() instead of range(len())"),
                (r'\.append\(.*\)\s*$', "Consider list comprehension for better performance"),
            ]
            
            for pattern, suggestion in performance_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    errors.append(CodeError(
                        id=f"performance_{hash(f'{filepath}_{line_num}_{pattern}')}",
                        category=ErrorCategory.PERFORMANCE,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"Performance issue: {match.group()}",
                        filepath=filepath,
                        line_start=line_num,
                        line_end=line_num,
                        suggested_fix=suggestion
                    ))
        except Exception as e:
            logger.error(f"Error checking performance issues: {e}")
        return errors

# Global diagnostic streamer instance
diagnostic_streamer = DiagnosticStreamer()

# Export for use in main application
__all__ = [
    'DiagnosticStreamer',
    'EnhancedSerenaErrorAnalyzer', 
    'diagnostic_streamer'
]
