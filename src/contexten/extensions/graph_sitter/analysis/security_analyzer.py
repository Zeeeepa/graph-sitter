#!/usr/bin/env python3
"""
Security Analyzer

Detects security vulnerabilities and unsafe patterns using graph_sitter API.
Focuses on real security issues that can be detected through static analysis.
"""

import re
import graph_sitter
from graph_sitter import Codebase


@graph_sitter.function("analyze-security")
def analyze_security(codebase: Codebase):
    """Analyze security vulnerabilities in the codebase."""
    results = {
        'sql_injection_risks': [],
        'hardcoded_secrets': [],
        'unsafe_eval_usage': [],
        'insecure_random': [],
        'path_traversal_risks': [],
        'command_injection_risks': [],
        'summary': {
            'total_issues': 0,
            'critical_issues': 0,
            'high_issues': 0
        }
    }
    
    # Analyze each function for security issues
    for function in codebase.functions:
        # Skip test files
        if "test" in function.file.filepath:
            continue
        
        # Check for SQL injection risks
        sql_risks = detect_sql_injection(function)
        results['sql_injection_risks'].extend(sql_risks)
        
        # Check for unsafe eval usage
        eval_risks = detect_unsafe_eval(function)
        results['unsafe_eval_usage'].extend(eval_risks)
        
        # Check for insecure random usage
        random_risks = detect_insecure_random(function)
        results['insecure_random'].extend(random_risks)
        
        # Check for command injection
        cmd_risks = detect_command_injection(function)
        results['command_injection_risks'].extend(cmd_risks)
        
        # Check for path traversal
        path_risks = detect_path_traversal(function)
        results['path_traversal_risks'].extend(path_risks)
    
    # Analyze files for hardcoded secrets
    for file in codebase.files:
        if "test" in file.filepath:
            continue
        
        secrets = detect_hardcoded_secrets(file)
        results['hardcoded_secrets'].extend(secrets)
    
    # Calculate summary
    all_issues = (
        results['sql_injection_risks'] +
        results['hardcoded_secrets'] +
        results['unsafe_eval_usage'] +
        results['insecure_random'] +
        results['path_traversal_risks'] +
        results['command_injection_risks']
    )
    
    results['summary']['total_issues'] = len(all_issues)
    results['summary']['critical_issues'] = len([i for i in all_issues if i.get('severity') == 'critical'])
    results['summary']['high_issues'] = len([i for i in all_issues if i.get('severity') == 'high'])
    
    return results


def detect_sql_injection(function):
    """Detect potential SQL injection vulnerabilities."""
    risks = []
    source = function.source
    
    # Patterns that indicate SQL injection risk
    sql_patterns = [
        r'execute\s*\(\s*["\'].*%.*["\']',  # String formatting in execute
        r'cursor\.execute\s*\(\s*f["\']',    # f-string in execute
        r'\.format\s*\(.*\)\s*\)',          # .format() in SQL
        r'query\s*=.*\+.*',                 # String concatenation
        r'SELECT.*\+.*FROM',                # Direct concatenation in SELECT
        r'INSERT.*\+.*VALUES',              # Direct concatenation in INSERT
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, source, re.IGNORECASE):
            risks.append({
                'type': 'sql_injection',
                'severity': 'critical',
                'function': function.name,
                'file': function.file.filepath,
                'line': function.start_point[0] if function.start_point else 0,
                'description': 'Potential SQL injection vulnerability detected',
                'pattern': pattern,
                'recommendation': 'Use parameterized queries instead of string concatenation'
            })
            break  # Only report once per function
    
    return risks


def detect_hardcoded_secrets(file):
    """Detect hardcoded passwords, API keys, and secrets."""
    secrets = []
    source = file.source
    
    # Patterns for different types of secrets
    secret_patterns = [
        (r'password\s*=\s*["\'][^"\']{8,}["\']', 'hardcoded_password', 'critical'),
        (r'api_key\s*=\s*["\'][^"\']{20,}["\']', 'hardcoded_api_key', 'high'),
        (r'secret\s*=\s*["\'][^"\']{16,}["\']', 'hardcoded_secret', 'high'),
        (r'token\s*=\s*["\'][^"\']{20,}["\']', 'hardcoded_token', 'high'),
        (r'private_key\s*=\s*["\'][^"\']{32,}["\']', 'hardcoded_private_key', 'critical'),
        (r'["\'][A-Za-z0-9]{32,}["\']', 'potential_secret', 'medium'),  # Generic long strings
    ]
    
    for pattern, secret_type, severity in secret_patterns:
        matches = re.finditer(pattern, source, re.IGNORECASE)
        for match in matches:
            line_num = source[:match.start()].count('\n') + 1
            
            # Skip if it looks like a placeholder or example
            matched_text = match.group(0).lower()
            if any(placeholder in matched_text for placeholder in ['example', 'placeholder', 'your_', 'xxx', '123']):
                continue
            
            secrets.append({
                'type': secret_type,
                'severity': severity,
                'file': file.filepath,
                'line': line_num,
                'description': f'{secret_type.replace("_", " ").title()} detected',
                'recommendation': 'Move secret to environment variable or secure configuration'
            })
    
    return secrets


def detect_unsafe_eval(function):
    """Detect unsafe use of eval() and exec()."""
    risks = []
    source = function.source
    
    # Check for direct eval/exec usage
    unsafe_functions = ['eval', 'exec', 'compile']
    
    for func_call in function.function_calls:
        if hasattr(func_call, 'name') and func_call.name in unsafe_functions:
            risks.append({
                'type': 'unsafe_eval',
                'severity': 'high',
                'function': function.name,
                'file': function.file.filepath,
                'line': function.start_point[0] if function.start_point else 0,
                'description': f'Unsafe use of {func_call.name}() detected',
                'recommendation': 'Use safer alternatives like ast.literal_eval() or avoid dynamic code execution'
            })
    
    # Also check source for patterns
    eval_patterns = [
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bcompile\s*\('
    ]
    
    for pattern in eval_patterns:
        if re.search(pattern, source):
            # Only add if not already detected through function calls
            if not any(risk['type'] == 'unsafe_eval' for risk in risks):
                risks.append({
                    'type': 'unsafe_eval',
                    'severity': 'high',
                    'function': function.name,
                    'file': function.file.filepath,
                    'line': function.start_point[0] if function.start_point else 0,
                    'description': 'Unsafe eval/exec usage detected',
                    'recommendation': 'Use safer alternatives like ast.literal_eval() or avoid dynamic code execution'
                })
                break
    
    return risks


def detect_insecure_random(function):
    """Detect use of insecure random number generation for security purposes."""
    risks = []
    source = function.source
    
    # Check if function uses random module for security-sensitive operations
    if ('import random' in source or 'from random import' in source):
        security_keywords = ['password', 'token', 'key', 'secret', 'salt', 'nonce', 'session']
        
        if any(keyword in source.lower() for keyword in security_keywords):
            risks.append({
                'type': 'insecure_random',
                'severity': 'medium',
                'function': function.name,
                'file': function.file.filepath,
                'line': function.start_point[0] if function.start_point else 0,
                'description': 'Insecure random number generation for security purposes',
                'recommendation': 'Use secrets module instead of random for cryptographic purposes'
            })
    
    return risks


def detect_command_injection(function):
    """Detect potential command injection vulnerabilities."""
    risks = []
    source = function.source
    
    # Patterns that indicate command injection risk
    cmd_patterns = [
        r'os\.system\s*\([^)]*\+',          # os.system with concatenation
        r'subprocess\.[^(]*\([^)]*\+',      # subprocess with concatenation
        r'shell=True.*\+',                  # shell=True with concatenation
        r'exec\([^)]*\+',                   # exec with concatenation
    ]
    
    for pattern in cmd_patterns:
        if re.search(pattern, source, re.IGNORECASE):
            risks.append({
                'type': 'command_injection',
                'severity': 'high',
                'function': function.name,
                'file': function.file.filepath,
                'line': function.start_point[0] if function.start_point else 0,
                'description': 'Potential command injection vulnerability',
                'recommendation': 'Use parameterized commands and avoid shell=True when possible'
            })
            break
    
    return risks


def detect_path_traversal(function):
    """Detect potential path traversal vulnerabilities."""
    risks = []
    source = function.source
    
    # Patterns that indicate path traversal risk
    path_patterns = [
        r'open\s*\([^)]*\+',               # open() with concatenation
        r'file\s*=.*\+',                   # file assignment with concatenation
        r'path.*\+.*\.\.',                 # path with .. and concatenation
        r'os\.path\.join\([^)]*input',     # os.path.join with user input
    ]
    
    for pattern in path_patterns:
        if re.search(pattern, source, re.IGNORECASE):
            risks.append({
                'type': 'path_traversal',
                'severity': 'medium',
                'function': function.name,
                'file': function.file.filepath,
                'line': function.start_point[0] if function.start_point else 0,
                'description': 'Potential path traversal vulnerability',
                'recommendation': 'Validate and sanitize file paths, use os.path.abspath() and check against allowed directories'
            })
            break
    
    return risks


def check_import_security(codebase: Codebase):
    """Check for imports of potentially dangerous modules."""
    dangerous_imports = []
    
    # Modules that should be used carefully
    dangerous_modules = {
        'pickle': 'Can execute arbitrary code during deserialization',
        'marshal': 'Can execute arbitrary code during deserialization',
        'subprocess': 'Can execute system commands',
        'os': 'Provides system access',
        'eval': 'Can execute arbitrary code',
        'exec': 'Can execute arbitrary code'
    }
    
    for file in codebase.files:
        for imp in file.imports:
            module_name = imp.module if hasattr(imp, 'module') else str(imp)
            
            if module_name in dangerous_modules:
                dangerous_imports.append({
                    'module': module_name,
                    'file': file.filepath,
                    'warning': dangerous_modules[module_name],
                    'recommendation': 'Ensure proper input validation and security measures'
                })
    
    return dangerous_imports


if __name__ == "__main__":
    # Example usage
    codebase = Codebase("./")
    
    print("🔒 Analyzing security vulnerabilities...")
    results = analyze_security(codebase)
    
    print(f"\n🚨 Security Analysis Results:")
    print(f"Total security issues: {results['summary']['total_issues']}")
    print(f"Critical issues: {results['summary']['critical_issues']}")
    print(f"High severity issues: {results['summary']['high_issues']}")
    
    # Show critical issues
    if results['sql_injection_risks']:
        print(f"\n💉 SQL Injection Risks ({len(results['sql_injection_risks'])}):")
        for risk in results['sql_injection_risks'][:3]:
            print(f"  • {risk['function']} in {risk['file']}")
    
    if results['hardcoded_secrets']:
        print(f"\n🔑 Hardcoded Secrets ({len(results['hardcoded_secrets'])}):")
        for secret in results['hardcoded_secrets'][:3]:
            print(f"  • {secret['type']} in {secret['file']} (line {secret['line']})")
    
    if results['unsafe_eval_usage']:
        print(f"\n⚠️ Unsafe eval/exec Usage ({len(results['unsafe_eval_usage'])}):")
        for risk in results['unsafe_eval_usage']:
            print(f"  • {risk['function']} in {risk['file']}")
    
    # Check dangerous imports
    dangerous = check_import_security(codebase)
    if dangerous:
        print(f"\n⚡ Potentially Dangerous Imports ({len(dangerous)}):")
        for imp in dangerous[:3]:
            print(f"  • {imp['module']} in {imp['file']}: {imp['warning']}")

