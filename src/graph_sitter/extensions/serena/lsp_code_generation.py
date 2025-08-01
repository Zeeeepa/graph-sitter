"""
Serena LSP Code Generation Integration
=====================================

This module integrates Serena's code generation capabilities with the LSP
diagnostic system to provide context-aware error resolution and code fixes.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING

from graph_sitter.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from graph_sitter.core.unified_diagnostics import ErrorInfo, UnifiedDiagnosticEngine

logger = get_logger(__name__)

# Import Serena components (optional)
try:
    from graph_sitter.extensions.serena.generation.code_generator import CodeGenerator
    SERENA_AVAILABLE = True
except ImportError:
    logger.info("Serena code generation not available. Install Serena dependencies for enhanced error resolution.")
    SERENA_AVAILABLE = False
    
    # Fallback CodeGenerator
    class CodeGenerator:
        def __init__(self, *args, **kwargs):
            pass
        
        def generate_code(self, prompt: str, context: str = "") -> str:
            return "# Serena code generation not available"


class LSPCodeGenerationEngine:
    """
    Engine that integrates Serena code generation with LSP diagnostics
    to provide intelligent, context-aware error resolution.
    """
    
    def __init__(self, diagnostic_engine: "UnifiedDiagnosticEngine"):
        self.diagnostic_engine = diagnostic_engine
        self.code_generator = CodeGenerator() if SERENA_AVAILABLE else None
        self.repo_path = diagnostic_engine.repo_path
        
        # Error pattern templates for code generation
        self.error_templates = {
            "undefined_variable": {
                "patterns": [
                    r"name '(\w+)' is not defined",
                    r"undefined name '(\w+)'",
                    r"'(\w+)' is not defined"
                ],
                "template": "fix_undefined_variable",
                "priority": "high"
            },
            "import_error": {
                "patterns": [
                    r"No module named '([\w\.]+)'",
                    r"cannot import name '(\w+)' from '([\w\.]+)'",
                    r"ImportError: (.+)"
                ],
                "template": "fix_import_error",
                "priority": "high"
            },
            "syntax_error": {
                "patterns": [
                    r"invalid syntax",
                    r"unexpected EOF while parsing",
                    r"expected ':'"
                ],
                "template": "fix_syntax_error",
                "priority": "critical"
            },
            "type_error": {
                "patterns": [
                    r"'(\w+)' object has no attribute '(\w+)'",
                    r"unsupported operand type\(s\) for (.+): '(\w+)' and '(\w+)'",
                    r"argument of type '(\w+)' is not iterable"
                ],
                "template": "fix_type_error",
                "priority": "medium"
            },
            "indentation_error": {
                "patterns": [
                    r"expected an indented block",
                    r"unindent does not match any outer indentation level",
                    r"IndentationError: (.+)"
                ],
                "template": "fix_indentation_error",
                "priority": "high"
            },
            "missing_function": {
                "patterns": [
                    r"'(\w+)' object has no attribute '(\w+)'",
                    r"module '(\w+)' has no attribute '(\w+)'"
                ],
                "template": "create_missing_function",
                "priority": "medium"
            }
        }
    
    def generate_error_fixes(self, error_id: str) -> List[Dict[str, Any]]:
        """Generate code fixes for a specific error."""
        if not self.code_generator:
            return []
        
        try:
            # Get error context
            context = self.diagnostic_engine.get_full_error_context(error_id)
            if not context:
                return []
            
            error = context["error"]
            
            # Analyze error and generate fixes
            fixes = []
            
            # Pattern-based fix generation
            pattern_fixes = self._generate_pattern_based_fixes(error, context)
            fixes.extend(pattern_fixes)
            
            # Context-aware fix generation
            context_fixes = self._generate_context_aware_fixes(error, context)
            fixes.extend(context_fixes)
            
            # AI-powered fix generation
            ai_fixes = self._generate_ai_powered_fixes(error, context)
            fixes.extend(ai_fixes)
            
            return fixes
            
        except Exception as e:
            logger.error(f"Error generating fixes for {error_id}: {e}")
            return []
    
    def _generate_pattern_based_fixes(self, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fixes based on error message patterns."""
        fixes = []
        
        try:
            message = error.message.lower()
            
            # Check each error pattern
            for error_type, config in self.error_templates.items():
                for pattern in config["patterns"]:
                    match = re.search(pattern.lower(), message)
                    if match:
                        fix = self._create_pattern_fix(error_type, match, error, context, config)
                        if fix:
                            fixes.append(fix)
                        break  # Only use first matching pattern
            
            return fixes
            
        except Exception as e:
            logger.error(f"Error in pattern-based fix generation: {e}")
            return []
    
    def _create_pattern_fix(self, error_type: str, match: re.Match, error: "ErrorInfo", 
                           context: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a fix based on a matched pattern."""
        try:
            if error_type == "undefined_variable":
                variable_name = match.group(1)
                return {
                    "type": "code_fix",
                    "title": f"Define variable '{variable_name}'",
                    "description": f"Add definition for undefined variable '{variable_name}'",
                    "priority": config["priority"],
                    "code_changes": self._generate_variable_definition(variable_name, error, context),
                    "confidence": 0.8
                }
            
            elif error_type == "import_error":
                if "No module named" in error.message:
                    module_name = match.group(1)
                    return {
                        "type": "code_fix",
                        "title": f"Install missing module '{module_name}'",
                        "description": f"Add import statement or install missing module '{module_name}'",
                        "priority": config["priority"],
                        "code_changes": self._generate_import_fix(module_name, error, context),
                        "confidence": 0.9
                    }
                elif "cannot import name" in error.message:
                    symbol_name = match.group(1)
                    module_name = match.group(2)
                    return {
                        "type": "code_fix",
                        "title": f"Fix import of '{symbol_name}' from '{module_name}'",
                        "description": f"Correct the import statement for '{symbol_name}'",
                        "priority": config["priority"],
                        "code_changes": self._generate_import_symbol_fix(symbol_name, module_name, error, context),
                        "confidence": 0.7
                    }
            
            elif error_type == "syntax_error":
                return {
                    "type": "code_fix",
                    "title": "Fix syntax error",
                    "description": "Correct the syntax error in the code",
                    "priority": config["priority"],
                    "code_changes": self._generate_syntax_fix(error, context),
                    "confidence": 0.6
                }
            
            elif error_type == "type_error":
                return {
                    "type": "code_fix",
                    "title": "Fix type error",
                    "description": "Resolve the type-related error",
                    "priority": config["priority"],
                    "code_changes": self._generate_type_fix(match, error, context),
                    "confidence": 0.5
                }
            
            elif error_type == "indentation_error":
                return {
                    "type": "code_fix",
                    "title": "Fix indentation",
                    "description": "Correct the indentation error",
                    "priority": config["priority"],
                    "code_changes": self._generate_indentation_fix(error, context),
                    "confidence": 0.9
                }
            
            elif error_type == "missing_function":
                if len(match.groups()) >= 2:
                    object_name = match.group(1)
                    function_name = match.group(2)
                    return {
                        "type": "code_fix",
                        "title": f"Create missing method '{function_name}'",
                        "description": f"Add missing method '{function_name}' to '{object_name}'",
                        "priority": config["priority"],
                        "code_changes": self._generate_missing_function(object_name, function_name, error, context),
                        "confidence": 0.6
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating pattern fix: {e}")
            return None
    
    def _generate_context_aware_fixes(self, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fixes based on code context analysis."""
        fixes = []
        
        try:
            # Analyze surrounding code context
            context_lines = context.get("context_lines", {})
            before_lines = context_lines.get("before", [])
            after_lines = context_lines.get("after", [])
            error_line = context_lines.get("error_line", "")
            
            # Look for common patterns in context
            if self._has_similar_imports(before_lines):
                fix = self._suggest_similar_import(error, before_lines)
                if fix:
                    fixes.append(fix)
            
            if self._has_similar_variable_definitions(before_lines):
                fix = self._suggest_similar_variable(error, before_lines)
                if fix:
                    fixes.append(fix)
            
            if self._has_function_definitions(before_lines + after_lines):
                fix = self._suggest_function_context_fix(error, before_lines + after_lines)
                if fix:
                    fixes.append(fix)
            
            return fixes
            
        except Exception as e:
            logger.error(f"Error in context-aware fix generation: {e}")
            return []
    
    def _generate_ai_powered_fixes(self, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fixes using AI-powered code generation."""
        if not self.code_generator:
            return []
        
        fixes = []
        
        try:
            # Prepare context for AI generation
            file_context = self._prepare_file_context(error, context)
            error_context = self._prepare_error_context(error, context)
            
            # Generate AI-powered fix
            prompt = self._create_fix_prompt(error, error_context, file_context)
            
            if prompt:
                generated_code = self.code_generator.generate_code(prompt, file_context)
                
                if generated_code and generated_code.strip():
                    fix = {
                        "type": "ai_code_fix",
                        "title": "AI-generated fix",
                        "description": f"AI-suggested solution for: {error.message}",
                        "priority": "medium",
                        "code_changes": [{
                            "file_path": error.file_path,
                            "line": error.line,
                            "action": "replace_or_insert",
                            "new_code": generated_code.strip(),
                            "explanation": "AI-generated code to resolve the error"
                        }],
                        "confidence": 0.4  # Lower confidence for AI-generated fixes
                    }
                    fixes.append(fix)
            
            return fixes
            
        except Exception as e:
            logger.error(f"Error in AI-powered fix generation: {e}")
            return []
    
    def _generate_variable_definition(self, variable_name: str, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate code to define an undefined variable."""
        # Analyze context to suggest appropriate variable type and value
        context_lines = context.get("context_lines", {})
        error_line = context_lines.get("error_line", "")
        
        # Simple heuristics for variable type
        if "=" in error_line and variable_name in error_line:
            # Variable is being assigned, suggest initialization
            suggested_value = "None  # TODO: Initialize with appropriate value"
        elif any(op in error_line for op in ["+", "-", "*", "/", "%"]):
            # Used in arithmetic, suggest numeric type
            suggested_value = "0  # TODO: Initialize with appropriate numeric value"
        elif "len(" in error_line or "for " in error_line:
            # Used with len() or in for loop, suggest list/string
            suggested_value = "[]  # TODO: Initialize with appropriate collection"
        else:
            # Default suggestion
            suggested_value = "None  # TODO: Initialize with appropriate value"
        
        return [{
            "file_path": error.file_path,
            "line": max(0, error.line - 1),  # Insert before the error line
            "action": "insert",
            "new_code": f"{variable_name} = {suggested_value}",
            "explanation": f"Define the undefined variable '{variable_name}'"
        }]
    
    def _generate_import_fix(self, module_name: str, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate code to fix import errors."""
        # Find appropriate location for import (top of file, after existing imports)
        context_lines = context.get("context_lines", {})
        before_lines = context_lines.get("before", [])
        
        # Find last import line
        import_line = 0
        for i, line in enumerate(before_lines):
            if line.strip().startswith(("import ", "from ")):
                import_line = i + 1
        
        # Suggest common import patterns
        common_imports = {
            "os": "import os",
            "sys": "import sys",
            "json": "import json",
            "re": "import re",
            "datetime": "from datetime import datetime",
            "pathlib": "from pathlib import Path",
            "typing": "from typing import List, Dict, Any, Optional"
        }
        
        import_statement = common_imports.get(module_name, f"import {module_name}")
        
        return [{
            "file_path": error.file_path,
            "line": import_line,
            "action": "insert",
            "new_code": import_statement,
            "explanation": f"Add missing import for '{module_name}'"
        }]
    
    def _generate_import_symbol_fix(self, symbol_name: str, module_name: str, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate code to fix import symbol errors."""
        # Suggest alternative import patterns
        alternatives = [
            f"from {module_name} import {symbol_name}",
            f"import {module_name}",
            f"from {module_name} import *  # Consider importing specific symbols instead"
        ]
        
        return [{
            "file_path": error.file_path,
            "line": error.line,
            "action": "replace",
            "new_code": alternatives[0],  # Use the most specific import
            "explanation": f"Fix import of '{symbol_name}' from '{module_name}'",
            "alternatives": alternatives[1:]
        }]
    
    def _generate_syntax_fix(self, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate code to fix syntax errors."""
        context_lines = context.get("context_lines", {})
        error_line = context_lines.get("error_line", "").strip()
        
        fixes = []
        
        # Common syntax error fixes
        if error_line.endswith("if ") or error_line.endswith("elif ") or error_line.endswith("else"):
            fixes.append({
                "file_path": error.file_path,
                "line": error.line,
                "action": "replace",
                "new_code": error_line + ":",
                "explanation": "Add missing colon after control statement"
            })
        elif "(" in error_line and error_line.count("(") > error_line.count(")"):
            fixes.append({
                "file_path": error.file_path,
                "line": error.line,
                "action": "replace",
                "new_code": error_line + ")",
                "explanation": "Add missing closing parenthesis"
            })
        elif "[" in error_line and error_line.count("[") > error_line.count("]"):
            fixes.append({
                "file_path": error.file_path,
                "line": error.line,
                "action": "replace",
                "new_code": error_line + "]",
                "explanation": "Add missing closing bracket"
            })
        elif "{" in error_line and error_line.count("{") > error_line.count("}"):
            fixes.append({
                "file_path": error.file_path,
                "line": error.line,
                "action": "replace",
                "new_code": error_line + "}",
                "explanation": "Add missing closing brace"
            })
        
        return fixes
    
    def _generate_type_fix(self, match: re.Match, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate code to fix type errors."""
        # This is a complex area that would benefit from more sophisticated analysis
        return [{
            "file_path": error.file_path,
            "line": error.line,
            "action": "comment",
            "new_code": f"# TODO: Fix type error - {error.message}",
            "explanation": "Add TODO comment for manual type error resolution"
        }]
    
    def _generate_indentation_fix(self, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate code to fix indentation errors."""
        context_lines = context.get("context_lines", {})
        error_line = context_lines.get("error_line", "")
        before_lines = context_lines.get("before", [])
        
        # Analyze indentation pattern from previous lines
        if before_lines:
            # Find the expected indentation level
            last_line = before_lines[-1] if before_lines else ""
            if last_line.strip().endswith(":"):
                # Previous line ends with colon, need to indent
                indent = "    "  # Standard 4-space indentation
            else:
                # Match indentation of previous non-empty line
                for line in reversed(before_lines):
                    if line.strip():
                        indent = line[:len(line) - len(line.lstrip())]
                        break
                else:
                    indent = ""
        else:
            indent = ""
        
        return [{
            "file_path": error.file_path,
            "line": error.line,
            "action": "replace",
            "new_code": indent + error_line.lstrip(),
            "explanation": "Fix indentation to match expected level"
        }]
    
    def _generate_missing_function(self, object_name: str, function_name: str, error: "ErrorInfo", context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate code to create a missing function or method."""
        # This would require more sophisticated analysis to determine where to add the function
        return [{
            "file_path": error.file_path,
            "line": error.line + 1,
            "action": "insert",
            "new_code": f"""
def {function_name}(self):
    \"\"\"TODO: Implement {function_name} method.\"\"\"
    pass
""".strip(),
            "explanation": f"Create missing method '{function_name}'"
        }]
    
    # Helper methods for context analysis
    
    def _has_similar_imports(self, lines: List[str]) -> bool:
        """Check if there are similar import statements in the context."""
        return any(line.strip().startswith(("import ", "from ")) for line in lines)
    
    def _has_similar_variable_definitions(self, lines: List[str]) -> bool:
        """Check if there are similar variable definitions in the context."""
        return any("=" in line and not line.strip().startswith("#") for line in lines)
    
    def _has_function_definitions(self, lines: List[str]) -> bool:
        """Check if there are function definitions in the context."""
        return any(line.strip().startswith("def ") for line in lines)
    
    def _suggest_similar_import(self, error: "ErrorInfo", lines: List[str]) -> Optional[Dict[str, Any]]:
        """Suggest import based on similar imports in context."""
        # Implementation would analyze existing imports and suggest similar patterns
        return None
    
    def _suggest_similar_variable(self, error: "ErrorInfo", lines: List[str]) -> Optional[Dict[str, Any]]:
        """Suggest variable definition based on similar variables in context."""
        # Implementation would analyze existing variable patterns
        return None
    
    def _suggest_function_context_fix(self, error: "ErrorInfo", lines: List[str]) -> Optional[Dict[str, Any]]:
        """Suggest fix based on function context."""
        # Implementation would analyze function context and suggest appropriate fixes
        return None
    
    def _prepare_file_context(self, error: "ErrorInfo", context: Dict[str, Any]) -> str:
        """Prepare file context for AI generation."""
        try:
            file_path = Path(error.file_path)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content[:2000]  # Limit context size
        except Exception:
            pass
        
        return ""
    
    def _prepare_error_context(self, error: "ErrorInfo", context: Dict[str, Any]) -> str:
        """Prepare error context for AI generation."""
        context_lines = context.get("context_lines", {})
        before = "\n".join(context_lines.get("before", [])[-3:])  # Last 3 lines before
        error_line = context_lines.get("error_line", "")
        after = "\n".join(context_lines.get("after", [])[:3])  # First 3 lines after
        
        return f"""
Error Context:
Before:
{before}

Error Line:
{error_line}

After:
{after}

Error Message: {error.message}
""".strip()
    
    def _create_fix_prompt(self, error: "ErrorInfo", error_context: str, file_context: str) -> str:
        """Create a prompt for AI-powered fix generation."""
        return f"""
You are a Python code expert. Please analyze the following error and provide a fix.

{error_context}

File Context (first 2000 characters):
{file_context[:2000]}

Please provide a concise code fix that resolves the error. Focus on:
1. Fixing the immediate error
2. Following Python best practices
3. Maintaining code readability
4. Adding appropriate comments if needed

Provide only the corrected code without explanations.
""".strip()
    
    def get_error_resolution_suggestions(self, error_id: str) -> List[str]:
        """Get human-readable resolution suggestions for an error."""
        try:
            context = self.diagnostic_engine.get_full_error_context(error_id)
            if not context:
                return []
            
            error = context["error"]
            suggestions = []
            
            # Add pattern-based suggestions
            message = error.message.lower()
            
            if "not defined" in message:
                suggestions.append("Check if the variable is properly imported or defined before use")
                suggestions.append("Verify the spelling of the variable name")
                suggestions.append("Ensure the variable is in the correct scope")
            
            elif "no module named" in message:
                suggestions.append("Install the missing module using pip")
                suggestions.append("Check if the module name is spelled correctly")
                suggestions.append("Verify the module is in your Python path")
            
            elif "syntax error" in message:
                suggestions.append("Check for missing colons, parentheses, or quotes")
                suggestions.append("Verify proper indentation")
                suggestions.append("Look for unclosed brackets or braces")
            
            elif "indentation" in message:
                suggestions.append("Use consistent indentation (4 spaces recommended)")
                suggestions.append("Check for mixing tabs and spaces")
                suggestions.append("Ensure proper nesting of code blocks")
            
            # Add context-specific suggestions
            context_suggestions = self._get_context_specific_suggestions(error, context)
            suggestions.extend(context_suggestions)
            
            return suggestions[:5]  # Limit to top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting resolution suggestions: {e}")
            return []
    
    def _get_context_specific_suggestions(self, error: "ErrorInfo", context: Dict[str, Any]) -> List[str]:
        """Get suggestions based on the specific code context."""
        suggestions = []
        
        try:
            context_lines = context.get("context_lines", {})
            error_line = context_lines.get("error_line", "")
            before_lines = context_lines.get("before", [])
            
            # Analyze the error line for specific patterns
            if "import" in error_line:
                suggestions.append("Check if the import statement syntax is correct")
                suggestions.append("Verify the module exists and is installed")
            
            if "def " in error_line:
                suggestions.append("Ensure function definition syntax is correct")
                suggestions.append("Check for proper indentation of function body")
            
            if "class " in error_line:
                suggestions.append("Verify class definition syntax")
                suggestions.append("Check for proper inheritance syntax if applicable")
            
            # Analyze context for patterns
            if any("try:" in line for line in before_lines):
                suggestions.append("Check if except/finally blocks are properly structured")
            
            if any("if " in line for line in before_lines):
                suggestions.append("Verify if/elif/else block structure and indentation")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting context-specific suggestions: {e}")
            return []
