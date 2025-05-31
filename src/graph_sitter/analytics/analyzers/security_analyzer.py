"""
Security Analyzer for Graph-Sitter Analytics

Detects security vulnerabilities and validates security best practices:
- Common vulnerability patterns (SQL injection, XSS, etc.)
- Insecure coding practices
- Dependency security issues
- Authentication and authorization flaws
- Data exposure risks
"""

import re
import hashlib
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.shared.logging.logger import get_logger

from ..core.base_analyzer import BaseAnalyzer
from ..core.analysis_result import AnalysisResult, Finding, Severity, FindingType

logger = get_logger(__name__)


class SecurityAnalyzer(BaseAnalyzer):
    """
    Analyzes code for security vulnerabilities and best practices violations.
    
    Detects common security issues across multiple languages including
    injection vulnerabilities, insecure practices, and data exposure risks.
    """
    
    def __init__(self):
        super().__init__("security")
        self.supported_languages = {"python", "typescript", "javascript", "java", "cpp", "rust", "go"}
        
        # Security vulnerability patterns by language
        self.vulnerability_patterns = {
            "sql_injection": {
                "python": [
                    r'cursor\.execute\s*\(\s*["\'].*%.*["\']',
                    r'\.execute\s*\(\s*f["\'].*{.*}.*["\']',
                    r'query\s*=\s*["\'].*\+.*["\']',
                ],
                "javascript": [
                    r'query\s*=\s*["`\'].*\$\{.*\}.*["`\']',
                    r'\.query\s*\(\s*["`\'].*\+.*["`\']',
                ],
                "java": [
                    r'Statement\.execute\s*\(\s*["\'].*\+.*["\']',
                    r'prepareStatement\s*\(\s*["\'].*\+.*["\']',
                ],
                "severity": Severity.CRITICAL,
                "description": "Potential SQL injection vulnerability"
            },
            "xss": {
                "javascript": [
                    r'innerHTML\s*=\s*.*\+',
                    r'document\.write\s*\(',
                    r'eval\s*\(',
                ],
                "python": [
                    r'render_template_string\s*\(',
                    r'Markup\s*\(',
                ],
                "severity": Severity.HIGH,
                "description": "Potential Cross-Site Scripting (XSS) vulnerability"
            },
            "command_injection": {
                "python": [
                    r'os\.system\s*\(',
                    r'subprocess\.call\s*\(\s*shell\s*=\s*True',
                    r'eval\s*\(',
                    r'exec\s*\(',
                ],
                "javascript": [
                    r'child_process\.exec\s*\(',
                    r'eval\s*\(',
                ],
                "java": [
                    r'Runtime\.getRuntime\(\)\.exec\s*\(',
                ],
                "severity": Severity.CRITICAL,
                "description": "Potential command injection vulnerability"
            },
            "path_traversal": {
                "python": [
                    r'open\s*\(\s*.*\+.*\)',
                    r'file\s*=\s*.*\+.*',
                ],
                "javascript": [
                    r'fs\.readFile\s*\(\s*.*\+.*\)',
                    r'require\s*\(\s*.*\+.*\)',
                ],
                "java": [
                    r'new\s+File\s*\(\s*.*\+.*\)',
                    r'Files\.read\s*\(\s*.*\+.*\)',
                ],
                "severity": Severity.HIGH,
                "description": "Potential path traversal vulnerability"
            },
            "hardcoded_secrets": {
                "all": [
                    r'password\s*=\s*["\'][^"\']{8,}["\']',
                    r'api_key\s*=\s*["\'][^"\']{16,}["\']',
                    r'secret\s*=\s*["\'][^"\']{16,}["\']',
                    r'token\s*=\s*["\'][^"\']{20,}["\']',
                ],
                "severity": Severity.HIGH,
                "description": "Hardcoded secrets or credentials detected"
            },
            "weak_crypto": {
                "python": [
                    r'hashlib\.md5\s*\(',
                    r'hashlib\.sha1\s*\(',
                    r'random\.random\s*\(',
                ],
                "javascript": [
                    r'Math\.random\s*\(',
                    r'crypto\.createHash\s*\(\s*["\']md5["\']',
                ],
                "java": [
                    r'MessageDigest\.getInstance\s*\(\s*["\']MD5["\']',
                    r'MessageDigest\.getInstance\s*\(\s*["\']SHA1["\']',
                ],
                "severity": Severity.MEDIUM,
                "description": "Weak cryptographic algorithm detected"
            }
        }
        
        # Insecure coding practices
        self.insecure_practices = {
            "python": [
                {
                    "pattern": r'pickle\.loads?\s*\(',
                    "severity": Severity.HIGH,
                    "description": "Unsafe deserialization with pickle",
                    "recommendation": "Use safer serialization formats like JSON"
                },
                {
                    "pattern": r'yaml\.load\s*\(',
                    "severity": Severity.MEDIUM,
                    "description": "Unsafe YAML loading",
                    "recommendation": "Use yaml.safe_load() instead"
                },
                {
                    "pattern": r'ssl\._create_unverified_context',
                    "severity": Severity.HIGH,
                    "description": "SSL certificate verification disabled",
                    "recommendation": "Enable SSL certificate verification"
                }
            ],
            "javascript": [
                {
                    "pattern": r'dangerouslySetInnerHTML',
                    "severity": Severity.MEDIUM,
                    "description": "Potentially unsafe HTML injection",
                    "recommendation": "Sanitize HTML content before injection"
                },
                {
                    "pattern": r'process\.env\.\w+',
                    "severity": Severity.LOW,
                    "description": "Environment variable access",
                    "recommendation": "Ensure sensitive environment variables are properly protected"
                }
            ],
            "java": [
                {
                    "pattern": r'TrustManager\[\]\s*=\s*new\s+TrustManager',
                    "severity": Severity.HIGH,
                    "description": "Custom trust manager may bypass certificate validation",
                    "recommendation": "Use default trust managers for certificate validation"
                },
                {
                    "pattern": r'setHostnameVerifier\s*\(\s*new\s+HostnameVerifier',
                    "severity": Severity.MEDIUM,
                    "description": "Custom hostname verifier may be insecure",
                    "recommendation": "Use default hostname verification"
                }
            ]
        }
        
        # Security best practices checks
        self.best_practices = {
            "authentication": [
                r'password.*==.*["\']',  # Plain text password comparison
                r'session\[\s*["\']user["\']',  # Session management
            ],
            "authorization": [
                r'if.*user\.is_admin',  # Simple admin checks
                r'role\s*==\s*["\']admin["\']',
            ],
            "input_validation": [
                r'request\.(GET|POST|args|form)\[',  # Direct parameter access
                r'input\s*\(',  # Direct input usage
            ]
        }
    
    @BaseAnalyzer.measure_execution_time
    def analyze(self, codebase: Codebase, files: List) -> AnalysisResult:
        """Perform comprehensive security analysis."""
        if not self.validate_codebase(codebase):
            result = self.create_result("failed")
            result.error_message = "Invalid codebase provided"
            return result
        
        result = self.create_result()
        
        try:
            vulnerabilities_found = []
            security_issues = []
            files_analyzed = 0
            
            for file in files:
                if not self.is_supported_file(str(file.filepath)):
                    continue
                
                file_content = self.get_file_content(file)
                if not file_content:
                    continue
                
                file_language = self._detect_language(str(file.filepath))
                files_analyzed += 1
                
                # Check for vulnerability patterns
                file_vulnerabilities = self._check_vulnerability_patterns(file, file_content, file_language)
                vulnerabilities_found.extend(file_vulnerabilities)
                
                # Check for insecure practices
                file_practices = self._check_insecure_practices(file, file_content, file_language)
                security_issues.extend(file_practices)
                
                # Check security best practices
                best_practice_issues = self._check_security_best_practices(file, file_content, file_language)
                security_issues.extend(best_practice_issues)
                
                # Check for hardcoded secrets
                secret_issues = self._check_hardcoded_secrets(file, file_content)
                security_issues.extend(secret_issues)
                
                # Analyze functions for security issues
                for func in file.functions:
                    func_issues = self._analyze_function_security(func, file_content, file_language)
                    security_issues.extend(func_issues)
                
                self.log_progress(files_analyzed, len([f for f in files if self.is_supported_file(str(f.filepath))]), "files")
            
            # Create findings from vulnerabilities and issues
            all_issues = vulnerabilities_found + security_issues
            for issue in all_issues:
                finding = Finding(
                    type=FindingType.SECURITY,
                    severity=issue["severity"],
                    title=issue["title"],
                    description=issue["description"],
                    file_path=issue["file_path"],
                    line_number=issue.get("line_number"),
                    code_snippet=issue.get("code_snippet"),
                    recommendation=issue["recommendation"],
                    rule_id=issue["rule_id"],
                    metadata=issue.get("metadata", {})
                )
                result.add_finding(finding)
            
            # Calculate security metrics
            result.metrics.files_analyzed = files_analyzed
            result.metrics.quality_score = self._calculate_security_score(all_issues, files_analyzed)
            
            # Store detailed security metrics
            result.metrics.security_metrics = {
                "files_analyzed": files_analyzed,
                "vulnerabilities_found": len(vulnerabilities_found),
                "security_issues_found": len(security_issues),
                "vulnerability_types": self._get_vulnerability_distribution(vulnerabilities_found),
                "issue_distribution": self._get_issue_distribution(all_issues),
                "critical_vulnerabilities": [v for v in vulnerabilities_found if v["severity"] == Severity.CRITICAL],
                "high_risk_files": self._identify_high_risk_files(all_issues)
            }
            
            # Generate recommendations
            result.recommendations = self._generate_security_recommendations(vulnerabilities_found, security_issues)
            
            logger.info(f"Security analysis completed: {len(vulnerabilities_found)} vulnerabilities, {len(security_issues)} security issues found")
            
        except Exception as e:
            logger.error(f"Security analysis failed: {str(e)}")
            result.status = "failed"
            result.error_message = str(e)
        
        return result
    
    def _check_vulnerability_patterns(self, file, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Check for known vulnerability patterns."""
        vulnerabilities = []
        
        for vuln_type, vuln_data in self.vulnerability_patterns.items():
            patterns = vuln_data.get(language, []) + vuln_data.get("all", [])
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, file_content, re.IGNORECASE | re.MULTILINE))
                
                for match in matches:
                    line_number = file_content[:match.start()].count('\n') + 1
                    code_snippet = self.extract_code_snippet(file_content, line_number)
                    
                    vulnerabilities.append({
                        "severity": vuln_data["severity"],
                        "title": f"{vuln_type.replace('_', ' ').title()} Vulnerability",
                        "description": vuln_data["description"],
                        "file_path": str(file.filepath),
                        "line_number": line_number,
                        "code_snippet": code_snippet,
                        "recommendation": self._get_vulnerability_recommendation(vuln_type, language),
                        "rule_id": f"SEC_{vuln_type.upper()}",
                        "metadata": {
                            "vulnerability_type": vuln_type,
                            "pattern_matched": pattern,
                            "language": language
                        }
                    })
        
        return vulnerabilities
    
    def _check_insecure_practices(self, file, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Check for insecure coding practices."""
        issues = []
        
        practices = self.insecure_practices.get(language, [])
        
        for practice in practices:
            matches = list(re.finditer(practice["pattern"], file_content, re.IGNORECASE | re.MULTILINE))
            
            for match in matches:
                line_number = file_content[:match.start()].count('\n') + 1
                code_snippet = self.extract_code_snippet(file_content, line_number)
                
                issues.append({
                    "severity": practice["severity"],
                    "title": f"Insecure Practice: {practice['description']}",
                    "description": practice["description"],
                    "file_path": str(file.filepath),
                    "line_number": line_number,
                    "code_snippet": code_snippet,
                    "recommendation": practice["recommendation"],
                    "rule_id": "SEC_PRACTICE",
                    "metadata": {
                        "practice_type": "insecure_coding",
                        "pattern_matched": practice["pattern"],
                        "language": language
                    }
                })
        
        return issues
    
    def _check_security_best_practices(self, file, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Check adherence to security best practices."""
        issues = []
        
        for practice_type, patterns in self.best_practices.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, file_content, re.IGNORECASE | re.MULTILINE))
                
                for match in matches:
                    line_number = file_content[:match.start()].count('\n') + 1
                    code_snippet = self.extract_code_snippet(file_content, line_number)
                    
                    issues.append({
                        "severity": Severity.MEDIUM,
                        "title": f"Security Best Practice Violation: {practice_type.replace('_', ' ').title()}",
                        "description": f"Code may not follow {practice_type.replace('_', ' ')} best practices",
                        "file_path": str(file.filepath),
                        "line_number": line_number,
                        "code_snippet": code_snippet,
                        "recommendation": self._get_best_practice_recommendation(practice_type),
                        "rule_id": f"SEC_BP_{practice_type.upper()}",
                        "metadata": {
                            "practice_type": practice_type,
                            "pattern_matched": pattern
                        }
                    })
        
        return issues
    
    def _check_hardcoded_secrets(self, file, file_content: str) -> List[Dict[str, Any]]:
        """Check for hardcoded secrets and credentials."""
        issues = []
        
        # Common secret patterns
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "password"),
            (r'api_key\s*=\s*["\'][A-Za-z0-9]{16,}["\']', "api_key"),
            (r'secret\s*=\s*["\'][A-Za-z0-9]{16,}["\']', "secret"),
            (r'token\s*=\s*["\'][A-Za-z0-9]{20,}["\']', "token"),
            (r'private_key\s*=\s*["\'].*["\']', "private_key"),
            (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', "private_key_content"),
        ]
        
        for pattern, secret_type in secret_patterns:
            matches = list(re.finditer(pattern, file_content, re.IGNORECASE | re.MULTILINE))
            
            for match in matches:
                line_number = file_content[:match.start()].count('\n') + 1
                
                # Don't include the actual secret in the snippet for security
                safe_snippet = re.sub(r'["\'][^"\']*["\']', '"[REDACTED]"', match.group())
                
                issues.append({
                    "severity": Severity.HIGH,
                    "title": f"Hardcoded {secret_type.replace('_', ' ').title()}",
                    "description": f"Hardcoded {secret_type.replace('_', ' ')} detected in source code",
                    "file_path": str(file.filepath),
                    "line_number": line_number,
                    "code_snippet": safe_snippet,
                    "recommendation": f"Move {secret_type.replace('_', ' ')} to environment variables or secure configuration",
                    "rule_id": "SEC_HARDCODED_SECRET",
                    "metadata": {
                        "secret_type": secret_type,
                        "pattern_matched": pattern
                    }
                })
        
        return issues
    
    def _analyze_function_security(self, func: Function, file_content: str, language: str) -> List[Dict[str, Any]]:
        """Analyze security aspects of individual functions."""
        issues = []
        
        func_content = self._extract_function_content(func, file_content)
        if not func_content:
            return issues
        
        # Check for functions that handle sensitive data
        sensitive_indicators = [
            "password", "token", "secret", "key", "auth", "login", "credential"
        ]
        
        func_name_lower = func.name.lower() if hasattr(func, 'name') else ""
        
        if any(indicator in func_name_lower for indicator in sensitive_indicators):
            # Extra scrutiny for sensitive functions
            
            # Check for proper input validation
            if not self._has_input_validation(func_content, language):
                issues.append({
                    "severity": Severity.MEDIUM,
                    "title": f"Missing Input Validation: {func.name}",
                    "description": f"Function '{func.name}' handles sensitive data but may lack proper input validation",
                    "file_path": str(func.filepath),
                    "line_number": getattr(func, 'line_number', None),
                    "recommendation": "Add input validation and sanitization for all user inputs",
                    "rule_id": "SEC_INPUT_VALIDATION",
                    "metadata": {"function_type": "sensitive"}
                })
            
            # Check for proper error handling
            if not self._has_proper_error_handling(func_content, language):
                issues.append({
                    "severity": Severity.LOW,
                    "title": f"Insufficient Error Handling: {func.name}",
                    "description": f"Function '{func.name}' may not handle errors securely",
                    "file_path": str(func.filepath),
                    "line_number": getattr(func, 'line_number', None),
                    "recommendation": "Implement proper error handling that doesn't leak sensitive information",
                    "rule_id": "SEC_ERROR_HANDLING",
                    "metadata": {"function_type": "sensitive"}
                })
        
        return issues
    
    def _has_input_validation(self, func_content: str, language: str) -> bool:
        """Check if function has input validation."""
        validation_patterns = {
            "python": [r'if\s+.*isinstance\(', r'if\s+.*len\(', r'if\s+.*not\s+'],
            "javascript": [r'if\s*\(\s*.*\.length', r'if\s*\(\s*typeof', r'if\s*\(\s*!'],
            "java": [r'if\s*\(\s*.*\.isEmpty\(\)', r'if\s*\(\s*.*==\s*null', r'if\s*\(\s*.*instanceof']
        }
        
        patterns = validation_patterns.get(language, [])
        return any(re.search(pattern, func_content, re.IGNORECASE) for pattern in patterns)
    
    def _has_proper_error_handling(self, func_content: str, language: str) -> bool:
        """Check if function has proper error handling."""
        error_patterns = {
            "python": [r'try:', r'except', r'raise'],
            "javascript": [r'try\s*{', r'catch\s*\(', r'throw'],
            "java": [r'try\s*{', r'catch\s*\(', r'throws?']
        }
        
        patterns = error_patterns.get(language, [])
        return any(re.search(pattern, func_content, re.IGNORECASE) for pattern in patterns)
    
    def _extract_function_content(self, func: Function, file_content: str) -> str:
        """Extract function content from file."""
        lines = file_content.splitlines()
        
        if hasattr(func, 'line_number') and func.line_number:
            start_line = func.line_number - 1
            
            # Find function end (simplified heuristic)
            end_line = start_line + 1
            indent_level = None
            
            for i in range(start_line + 1, len(lines)):
                line = lines[i]
                if line.strip():
                    if indent_level is None:
                        indent_level = len(line) - len(line.lstrip())
                    elif len(line) - len(line.lstrip()) <= indent_level and line.strip():
                        break
                end_line = i
            
            return "\n".join(lines[start_line:end_line + 1])
        
        return ""
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        from pathlib import Path
        
        ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".rs": "rust",
            ".go": "go"
        }
        
        return lang_map.get(ext, "unknown")
    
    def _get_vulnerability_recommendation(self, vuln_type: str, language: str) -> str:
        """Get specific recommendation for vulnerability type."""
        recommendations = {
            "sql_injection": {
                "python": "Use parameterized queries with cursor.execute(query, params) or ORM methods",
                "javascript": "Use parameterized queries or prepared statements",
                "java": "Use PreparedStatement with parameter placeholders (?)"
            },
            "xss": {
                "javascript": "Sanitize user input and use textContent instead of innerHTML",
                "python": "Use template engines with auto-escaping enabled"
            },
            "command_injection": {
                "python": "Use subprocess with shell=False and validate all inputs",
                "javascript": "Use child_process.spawn() instead of exec() and validate inputs",
                "java": "Validate and sanitize all inputs before executing commands"
            },
            "path_traversal": {
                "python": "Validate file paths and use os.path.join() for path construction",
                "javascript": "Use path.resolve() and validate file paths",
                "java": "Use Path.resolve() and validate file paths"
            }
        }
        
        return recommendations.get(vuln_type, {}).get(language, "Validate and sanitize all user inputs")
    
    def _get_best_practice_recommendation(self, practice_type: str) -> str:
        """Get recommendation for security best practice."""
        recommendations = {
            "authentication": "Implement proper authentication mechanisms with secure password handling",
            "authorization": "Use role-based access control with proper permission checks",
            "input_validation": "Validate and sanitize all user inputs before processing"
        }
        
        return recommendations.get(practice_type, "Follow security best practices")
    
    def _get_vulnerability_distribution(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of vulnerabilities by type."""
        distribution = defaultdict(int)
        for vuln in vulnerabilities:
            vuln_type = vuln.get("metadata", {}).get("vulnerability_type", "unknown")
            distribution[vuln_type] += 1
        return dict(distribution)
    
    def _get_issue_distribution(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of issues by severity."""
        distribution = defaultdict(int)
        for issue in issues:
            distribution[issue["severity"].value] += 1
        return dict(distribution)
    
    def _identify_high_risk_files(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify files with the highest security risk."""
        file_risk_scores = defaultdict(int)
        file_issue_counts = defaultdict(int)
        
        severity_weights = {
            Severity.CRITICAL: 10,
            Severity.HIGH: 5,
            Severity.MEDIUM: 2,
            Severity.LOW: 1
        }
        
        for issue in issues:
            file_path = issue["file_path"]
            weight = severity_weights.get(issue["severity"], 1)
            file_risk_scores[file_path] += weight
            file_issue_counts[file_path] += 1
        
        # Sort files by risk score
        high_risk_files = []
        for file_path, risk_score in sorted(file_risk_scores.items(), key=lambda x: x[1], reverse=True)[:10]:
            high_risk_files.append({
                "file_path": file_path,
                "risk_score": risk_score,
                "issue_count": file_issue_counts[file_path]
            })
        
        return high_risk_files
    
    def _calculate_security_score(self, issues: List[Dict[str, Any]], files_analyzed: int) -> float:
        """Calculate overall security score."""
        if files_analyzed == 0:
            return 100.0
        
        # Calculate penalty based on issues
        penalty = 0
        severity_weights = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3
        }
        
        for issue in issues:
            penalty += severity_weights.get(issue["severity"], 1)
        
        # Normalize penalty
        max_penalty = files_analyzed * 50  # Max 50 points penalty per file
        normalized_penalty = min(penalty, max_penalty)
        
        score = 100 - (normalized_penalty / max_penalty * 100) if max_penalty > 0 else 100
        return max(0, score)
    
    def _generate_security_recommendations(self, vulnerabilities: List[Dict[str, Any]], security_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable security recommendations."""
        recommendations = []
        
        # Count vulnerability types
        vuln_types = defaultdict(int)
        for vuln in vulnerabilities:
            vuln_type = vuln.get("metadata", {}).get("vulnerability_type", "unknown")
            vuln_types[vuln_type] += 1
        
        # Generate recommendations based on most common vulnerabilities
        if vuln_types.get("sql_injection", 0) > 0:
            recommendations.append(f"Fix {vuln_types['sql_injection']} SQL injection vulnerabilities using parameterized queries")
        
        if vuln_types.get("xss", 0) > 0:
            recommendations.append(f"Address {vuln_types['xss']} XSS vulnerabilities by sanitizing user input")
        
        if vuln_types.get("command_injection", 0) > 0:
            recommendations.append(f"Secure {vuln_types['command_injection']} command injection vulnerabilities")
        
        if vuln_types.get("hardcoded_secrets", 0) > 0:
            recommendations.append(f"Move {vuln_types['hardcoded_secrets']} hardcoded secrets to environment variables")
        
        # Count critical issues
        critical_count = sum(1 for issue in vulnerabilities + security_issues if issue["severity"] == Severity.CRITICAL)
        if critical_count > 0:
            recommendations.append(f"Immediately address {critical_count} critical security vulnerabilities")
        
        # General recommendations
        if len(security_issues) > 0:
            recommendations.append("Implement security code review process to prevent future issues")
        
        return recommendations[:5]  # Return top 5 recommendations

