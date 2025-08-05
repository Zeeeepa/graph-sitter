"""Code generation providers for AutoGenLib integration."""

import os
import ast
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
import json

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class CodeGenerationProvider(ABC):
    """Abstract base class for code generation providers."""
    
    @abstractmethod
    def generate_code(
        self,
        description: str,
        fullname: str,
        existing_code: Optional[str] = None,
        caller_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Generate code using this provider.
        
        Args:
            description: Description of what to generate
            fullname: Full module name
            existing_code: Existing code to extend
            caller_info: Information about calling code
            context: Additional context from graph-sitter
            
        Returns:
            Generated Python code or None if failed
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available and configured."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass


class CodegenSDKProvider(CodeGenerationProvider):
    """Code generation provider using Codegen SDK."""
    
    def __init__(self, org_id: str, token: str, base_url: Optional[str] = None):
        """Initialize Codegen SDK provider.
        
        Args:
            org_id: Organization ID
            token: Authentication token
            base_url: Optional base URL for API
        """
        self.org_id = org_id
        self.token = token
        self.base_url = base_url
        self._agent = None
        
        # Try to import and initialize the Codegen SDK
        try:
            from codegen import Agent
            self._agent = Agent(
                org_id=org_id,
                token=token,
                base_url=base_url
            )
            logger.info("Initialized Codegen SDK agent")
        except ImportError:
            logger.error("Codegen SDK not available. Install with: pip install codegen")
        except Exception as e:
            logger.error(f"Failed to initialize Codegen SDK: {e}")
    
    def is_available(self) -> bool:
        """Check if Codegen SDK is available."""
        return self._agent is not None
    
    @property
    def name(self) -> str:
        return "CodegenSDK"
    
    def generate_code(
        self,
        description: str,
        fullname: str,
        existing_code: Optional[str] = None,
        caller_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Generate code using Codegen SDK."""
        if not self.is_available():
            return None
        
        try:
            # Build the prompt for Codegen SDK
            prompt = self._build_prompt(
                description, fullname, existing_code, caller_info, context
            )
            
            # Run the agent
            task = self._agent.run(prompt=prompt)
            
            # Wait for completion (with timeout)
            max_attempts = 30  # 30 seconds timeout
            attempts = 0
            
            while attempts < max_attempts:
                task.refresh()
                if task.status == "completed":
                    result = task.result
                    if result:
                        # Extract code from the result
                        code = self._extract_code_from_result(result)
                        if code and self._validate_code(code):
                            return code
                    break
                elif task.status == "failed":
                    logger.error(f"Codegen SDK task failed for {fullname}")
                    break
                
                attempts += 1
                import time
                time.sleep(1)
            
            if attempts >= max_attempts:
                logger.warning(f"Codegen SDK task timed out for {fullname}")
            
        except Exception as e:
            logger.error(f"Codegen SDK generation failed for {fullname}: {e}")
        
        return None
    
    def _build_prompt(
        self,
        description: str,
        fullname: str,
        existing_code: Optional[str],
        caller_info: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build a comprehensive prompt for the Codegen SDK."""
        parts = fullname.split(".")
        module_name = parts[1] if len(parts) > 1 else "unknown"
        function_name = parts[2] if len(parts) > 2 else None
        
        prompt_parts = [
            f"Generate Python code for module '{module_name}'",
            f"Library purpose: {description}",
        ]
        
        if function_name:
            prompt_parts.append(f"Specifically implement function/class: {function_name}")
        
        if existing_code:
            prompt_parts.extend([
                "Extend the existing code:",
                f"```python\n{existing_code}\n```"
            ])
        
        if caller_info and caller_info.get("code"):
            prompt_parts.extend([
                "The code will be used in this context:",
                f"```python\n{caller_info['code']}\n```"
            ])
        
        if context:
            if context.get("dependencies"):
                prompt_parts.append("Related dependencies:")
                for dep in context["dependencies"][:5]:  # Limit to avoid token overflow
                    prompt_parts.append(f"- {dep.get('name', 'Unknown')}: {dep.get('source', '')[:200]}...")
            
            if context.get("usages"):
                prompt_parts.append("Usage examples:")
                for usage in context["usages"][:3]:
                    prompt_parts.append(f"- {usage.get('source', '')[:200]}...")
        
        prompt_parts.extend([
            "",
            "Requirements:",
            "- Return only clean Python code",
            "- Include proper docstrings and type hints",
            "- Follow PEP 8 style guidelines",
            "- Handle edge cases and errors appropriately",
            "- Make the code production-ready"
        ])
        
        return "\n".join(prompt_parts)
    
    def _extract_code_from_result(self, result: str) -> Optional[str]:
        """Extract Python code from Codegen SDK result."""
        if not result:
            return None
        
        # Try to extract code blocks
        code_block_pattern = r"```(?:python)?(.*?)```"
        matches = re.findall(code_block_pattern, result, re.DOTALL)
        
        if matches:
            # Join all code blocks
            code = "\n\n".join(match.strip() for match in matches)
            if self._validate_code(code):
                return code
        
        # If no code blocks, check if the entire result is valid Python
        if self._validate_code(result):
            return result
        
        return None
    
    def _validate_code(self, code: str) -> bool:
        """Validate that the code is syntactically correct."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False


class ClaudeProvider(CodeGenerationProvider):
    """Code generation provider using Claude API."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self._client = None
        
        # Try to import and initialize Anthropic client
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
            logger.info("Initialized Claude client")
        except ImportError:
            logger.error("Anthropic library not available. Install with: pip install anthropic")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
    
    def is_available(self) -> bool:
        """Check if Claude is available."""
        return self._client is not None
    
    @property
    def name(self) -> str:
        return "Claude"
    
    def generate_code(
        self,
        description: str,
        fullname: str,
        existing_code: Optional[str] = None,
        caller_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Generate code using Claude API."""
        if not self.is_available():
            return None
        
        try:
            # Build the prompt
            prompt = self._build_prompt(
                description, fullname, existing_code, caller_info, context
            )
            
            # Call Claude API
            response = self._client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            if response.content:
                content = response.content[0].text if response.content else ""
                code = self._extract_code_from_response(content)
                if code and self._validate_code(code):
                    return code
            
        except Exception as e:
            logger.error(f"Claude generation failed for {fullname}: {e}")
        
        return None
    
    def _build_prompt(
        self,
        description: str,
        fullname: str,
        existing_code: Optional[str],
        caller_info: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build a comprehensive prompt for Claude."""
        parts = fullname.split(".")
        module_name = parts[1] if len(parts) > 1 else "unknown"
        function_name = parts[2] if len(parts) > 2 else None
        
        prompt = f"""You are an expert Python developer. Generate high-quality Python code for the following requirements:

Module: {module_name}
Library Purpose: {description}
"""
        
        if function_name:
            prompt += f"Specific Function/Class: {function_name}\n"
        
        if existing_code:
            prompt += f"""
Existing Code to Extend:
```python
{existing_code}
```
"""
        
        if caller_info and caller_info.get("code"):
            prompt += f"""
Usage Context:
```python
{caller_info['code']}
```
"""
        
        if context:
            if context.get("dependencies"):
                prompt += "\nRelated Dependencies:\n"
                for dep in context["dependencies"][:5]:
                    prompt += f"- {dep.get('name', 'Unknown')}\n"
            
            if context.get("usages"):
                prompt += "\nUsage Examples:\n"
                for usage in context["usages"][:3]:
                    prompt += f"- {usage.get('source', '')[:200]}...\n"
        
        prompt += """
Requirements:
1. Return ONLY clean Python code without explanations
2. Include comprehensive docstrings with type hints
3. Follow PEP 8 style guidelines
4. Add proper error handling
5. Make the code production-ready
6. Use only Python standard library unless specified otherwise

Generate the complete module code:"""
        
        return prompt
    
    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Extract Python code from Claude response."""
        # Try to extract code blocks first
        code_block_pattern = r"```(?:python)?(.*?)```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            code = "\n\n".join(match.strip() for match in matches)
            if self._validate_code(code):
                return code
        
        # If no code blocks, check if the entire response is valid Python
        if self._validate_code(response):
            return response
        
        return None
    
    def _validate_code(self, code: str) -> bool:
        """Validate that the code is syntactically correct."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False


class CodeGenerator:
    """Main code generator that manages multiple providers with fallback."""
    
    def __init__(self, providers: List[CodeGenerationProvider]):
        """Initialize with a list of providers.
        
        Args:
            providers: List of code generation providers in order of preference
        """
        self.providers = providers
        logger.info(f"Initialized CodeGenerator with {len(providers)} providers")
    
    def add_provider(self, provider: CodeGenerationProvider):
        """Add a new provider to the end of the list."""
        self.providers.append(provider)
        logger.info(f"Added provider: {provider.name}")
    
    def generate_code(
        self,
        description: str,
        fullname: str,
        existing_code: Optional[str] = None,
        caller_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Generate code using the first available provider.
        
        Tries providers in order until one succeeds or all fail.
        
        Args:
            description: Description of what to generate
            fullname: Full module name
            existing_code: Existing code to extend
            caller_info: Information about calling code
            context: Additional context from graph-sitter
            
        Returns:
            Generated Python code or None if all providers failed
        """
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"Provider {provider.name} not available, skipping")
                continue
            
            logger.info(f"Attempting code generation with {provider.name} for {fullname}")
            
            try:
                code = provider.generate_code(
                    description=description,
                    fullname=fullname,
                    existing_code=existing_code,
                    caller_info=caller_info,
                    context=context
                )
                
                if code:
                    logger.info(f"Successfully generated code with {provider.name} for {fullname}")
                    return code
                else:
                    logger.warning(f"Provider {provider.name} returned no code for {fullname}")
                    
            except Exception as e:
                logger.error(f"Provider {provider.name} failed for {fullname}: {e}")
                continue
        
        logger.error(f"All providers failed to generate code for {fullname}")
        return None

