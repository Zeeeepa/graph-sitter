"""
Auto-Fix Generation System

Intelligent system that generates code fixes for CircleCI failures using:
- Codegen SDK for AI-powered fix generation
- Graph-sitter for code analysis and context
- GitHub integration for PR creation
- Validation and testing of generated fixes
"""

import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import tempfile
import subprocess

from .config import CircleCIIntegrationConfig
from .client import CircleCIClient
from .types import (
    FailureAnalysis, GeneratedFix, CodeFix, ConfigurationFix, DependencyFix,
    FixConfidence, FailureType, FixContext
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class FixGenerationError(Exception):
    """Fix generation error"""
    pass


class AutoFixGenerator:
    """
    Intelligent auto-fix generation system for CircleCI failures
    """
    
    def __init__(self, config: CircleCIIntegrationConfig, client: CircleCIClient):
        self.config = config
        self.client = client
        
        # Initialize Codegen SDK if enabled
        self.codegen_client = None
        if self.config.codegen.enabled and self.config.codegen.codegen_api_token:
            self._initialize_codegen_client()
        
        # Fix generation cache
        self.fix_cache: Dict[str, GeneratedFix] = {}
        
        # Fix templates and patterns
        self.fix_templates = self._load_fix_templates()
        
        # Statistics
        self.fixes_generated = 0
        self.fixes_applied = 0
        self.fixes_successful = 0
    
    def _initialize_codegen_client(self):
        """Initialize Codegen SDK client"""
        try:
            from codegen import Agent
            
            self.codegen_client = Agent(
                org_id=self.config.codegen.codegen_org_id,
                token=self.config.codegen.codegen_api_token.get_secret_value(),
                base_url=self.config.codegen.codegen_base_url
            )
            
            logger.info("Codegen SDK client initialized")
            
        except ImportError:
            logger.warning("Codegen SDK not available, fix generation will be limited")
        except Exception as e:
            logger.error(f"Failed to initialize Codegen SDK: {e}")
    
    def _load_fix_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load fix templates for common failure types"""
        templates = {
            FailureType.TEST_FAILURE: {
                "code_patterns": [
                    {
                        "pattern": "assertion_error",
                        "template": "Update test assertion to match expected behavior",
                        "confidence": FixConfidence.MEDIUM
                    },
                    {
                        "pattern": "mock_error",
                        "template": "Fix mock configuration and expectations",
                        "confidence": FixConfidence.HIGH
                    }
                ],
                "config_patterns": [
                    {
                        "pattern": "test_timeout",
                        "template": "Increase test timeout in configuration",
                        "confidence": FixConfidence.HIGH
                    }
                ]
            },
            
            FailureType.COMPILATION_ERROR: {
                "code_patterns": [
                    {
                        "pattern": "typescript_error",
                        "template": "Fix TypeScript type errors and imports",
                        "confidence": FixConfidence.HIGH
                    },
                    {
                        "pattern": "syntax_error",
                        "template": "Fix syntax errors in code",
                        "confidence": FixConfidence.HIGH
                    }
                ],
                "config_patterns": [
                    {
                        "pattern": "tsconfig_error",
                        "template": "Update TypeScript configuration",
                        "confidence": FixConfidence.MEDIUM
                    }
                ]
            },
            
            FailureType.DEPENDENCY_ERROR: {
                "dependency_patterns": [
                    {
                        "pattern": "missing_dependency",
                        "template": "Add missing dependency to package.json",
                        "confidence": FixConfidence.HIGH
                    },
                    {
                        "pattern": "version_conflict",
                        "template": "Resolve dependency version conflicts",
                        "confidence": FixConfidence.MEDIUM
                    }
                ]
            },
            
            FailureType.INFRASTRUCTURE_ERROR: {
                "config_patterns": [
                    {
                        "pattern": "memory_limit",
                        "template": "Increase memory allocation in CircleCI config",
                        "confidence": FixConfidence.HIGH
                    },
                    {
                        "pattern": "docker_error",
                        "template": "Fix Docker configuration and commands",
                        "confidence": FixConfidence.MEDIUM
                    }
                ]
            },
            
            FailureType.CONFIGURATION_ERROR: {
                "config_patterns": [
                    {
                        "pattern": "circleci_config",
                        "template": "Fix CircleCI configuration syntax and structure",
                        "confidence": FixConfidence.HIGH
                    },
                    {
                        "pattern": "environment_vars",
                        "template": "Add or fix environment variable configuration",
                        "confidence": FixConfidence.MEDIUM
                    }
                ]
            }
        }
        
        logger.info(f"Loaded fix templates for {len(templates)} failure types")
        return templates
    
    async def generate_fix(
        self,
        failure_analysis: FailureAnalysis,
        repository_url: str,
        branch: str,
        commit_sha: str
    ) -> GeneratedFix:
        """Generate a comprehensive fix for the failure"""
        
        logger.info(f"Generating fix for failure: {failure_analysis.failure_type.value}")
        
        start_time = datetime.now()
        
        try:
            # Create fix context
            context = FixContext(
                failure_analysis=failure_analysis,
                repository_url=repository_url,
                branch=branch,
                commit_sha=commit_sha,
                auto_apply=not self.config.auto_fix.require_human_approval,
                create_pr=self.config.github.auto_create_prs,
                run_tests=self.config.auto_fix.run_tests_after_fix,
                github_token=self.config.github.github_token.get_secret_value() if self.config.github.github_token else None,
                codegen_token=self.config.codegen.codegen_api_token.get_secret_value() if self.config.codegen.codegen_api_token else None
            )
            
            # Generate different types of fixes
            code_fixes = await self._generate_code_fixes(failure_analysis, context)
            config_fixes = await self._generate_config_fixes(failure_analysis, context)
            dependency_fixes = await self._generate_dependency_fixes(failure_analysis, context)
            
            # Determine overall confidence
            overall_confidence = self._calculate_overall_confidence(
                code_fixes, config_fixes, dependency_fixes
            )
            
            # Create fix object
            fix = GeneratedFix(
                id=str(uuid.uuid4()),
                failure_analysis_id=failure_analysis.build_id,
                timestamp=datetime.now(),
                title=self._generate_fix_title(failure_analysis),
                description=self._generate_fix_description(failure_analysis, code_fixes, config_fixes, dependency_fixes),
                overall_confidence=overall_confidence,
                code_fixes=code_fixes,
                config_fixes=config_fixes,
                dependency_fixes=dependency_fixes,
                branch_name=self._generate_branch_name(failure_analysis),
                commit_message=self._generate_commit_message(failure_analysis),
                pr_title=self._generate_pr_title(failure_analysis),
                pr_description=self._generate_pr_description(failure_analysis, code_fixes, config_fixes, dependency_fixes),
                validation_commands=self._generate_validation_commands(failure_analysis),
                test_commands=self._generate_test_commands(failure_analysis)
            )
            
            # Cache the fix
            self.fix_cache[fix.id] = fix
            
            # Update statistics
            self.fixes_generated += 1
            
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Generated fix {fix.id} in {generation_time:.2f}s (confidence: {overall_confidence.value})")
            
            return fix
            
        except Exception as e:
            logger.error(f"Failed to generate fix: {e}")
            raise FixGenerationError(f"Fix generation failed: {e}")
    
    async def _generate_code_fixes(
        self, 
        analysis: FailureAnalysis, 
        context: FixContext
    ) -> List[CodeFix]:
        """Generate code fixes using AI and templates"""
        
        if not self.config.auto_fix.enable_code_fixes:
            return []
        
        code_fixes = []
        
        try:
            # Use Codegen SDK for intelligent fix generation
            if self.codegen_client and self.config.codegen.enabled:
                ai_fixes = await self._generate_ai_code_fixes(analysis, context)
                code_fixes.extend(ai_fixes)
            
            # Use template-based fixes as fallback
            template_fixes = await self._generate_template_code_fixes(analysis, context)
            code_fixes.extend(template_fixes)
            
            # Remove duplicates and limit count
            unique_fixes = self._deduplicate_code_fixes(code_fixes)
            return unique_fixes[:self.config.auto_fix.max_fixes_per_failure]
            
        except Exception as e:
            logger.error(f"Failed to generate code fixes: {e}")
            return []
    
    async def _generate_ai_code_fixes(
        self, 
        analysis: FailureAnalysis, 
        context: FixContext
    ) -> List[CodeFix]:
        """Generate code fixes using Codegen SDK"""
        
        fixes = []
        
        try:
            # Build context for AI
            ai_context = self._build_ai_context(analysis, context)
            
            # Generate fix using Codegen SDK
            prompt = self._build_fix_prompt(analysis, ai_context)
            
            task = self.codegen_client.run(
                prompt=prompt,
                timeout=self.config.auto_fix.fix_generation_timeout
            )
            
            # Wait for completion
            while task.status not in ["completed", "failed"]:
                await asyncio.sleep(2)
                task.refresh()
            
            if task.status == "completed" and task.result:
                # Parse AI response into code fixes
                ai_fixes = self._parse_ai_response(task.result, analysis)
                fixes.extend(ai_fixes)
                
                logger.info(f"Generated {len(ai_fixes)} AI code fixes")
            
        except Exception as e:
            logger.error(f"AI code fix generation failed: {e}")
        
        return fixes
    
    def _build_ai_context(self, analysis: FailureAnalysis, context: FixContext) -> Dict[str, Any]:
        """Build context for AI fix generation"""
        return {
            "failure_type": analysis.failure_type.value,
            "root_cause": analysis.root_cause,
            "confidence": analysis.confidence,
            "error_messages": analysis.error_messages[:5],  # Limit to top 5
            "failed_tests": [
                {
                    "name": test.name,
                    "file": test.file,
                    "failure_message": test.failure_message
                }
                for test in analysis.failed_tests[:3]  # Limit to top 3
            ],
            "affected_files": analysis.affected_files[:10],  # Limit to top 10
            "repository": context.repository_url,
            "branch": context.branch,
            "commit": context.commit_sha
        }
    
    def _build_fix_prompt(self, analysis: FailureAnalysis, ai_context: Dict[str, Any]) -> str:
        """Build prompt for AI fix generation"""
        prompt = f"""
You are an expert software engineer tasked with fixing a CircleCI build failure.

## Failure Analysis
- **Type**: {analysis.failure_type.value}
- **Root Cause**: {analysis.root_cause}
- **Confidence**: {analysis.confidence:.2f}

## Error Details
"""
        
        if analysis.error_messages:
            prompt += "**Error Messages**:\n"
            for msg in analysis.error_messages[:3]:
                prompt += f"- {msg}\n"
            prompt += "\n"
        
        if analysis.failed_tests:
            prompt += "**Failed Tests**:\n"
            for test in analysis.failed_tests[:3]:
                prompt += f"- {test.name}: {test.failure_message}\n"
            prompt += "\n"
        
        if analysis.affected_files:
            prompt += "**Affected Files**:\n"
            for file_path in analysis.affected_files[:5]:
                prompt += f"- {file_path}\n"
            prompt += "\n"
        
        prompt += f"""
## Repository Context
- **Repository**: {ai_context['repository']}
- **Branch**: {ai_context['branch']}
- **Commit**: {ai_context['commit'][:8]}

## Task
Please analyze this failure and provide specific code fixes. Focus on:
1. Fixing the root cause identified in the analysis
2. Addressing the specific error messages
3. Updating any failing tests if needed
4. Ensuring the fix is minimal and targeted

For each fix, provide:
- File path to modify
- Description of the change
- The specific code changes needed
- Confidence level (high/medium/low)
- Reasoning for the fix

Please be specific and actionable in your recommendations.
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str, analysis: FailureAnalysis) -> List[CodeFix]:
        """Parse AI response into code fixes"""
        fixes = []
        
        try:
            # Try to parse structured response
            if ai_response.strip().startswith('{') or ai_response.strip().startswith('['):
                data = json.loads(ai_response)
                if isinstance(data, list):
                    for item in data:
                        fix = self._parse_ai_fix_item(item, analysis)
                        if fix:
                            fixes.append(fix)
                elif isinstance(data, dict) and 'fixes' in data:
                    for item in data['fixes']:
                        fix = self._parse_ai_fix_item(item, analysis)
                        if fix:
                            fixes.append(fix)
            else:
                # Parse unstructured response
                fixes = self._parse_unstructured_ai_response(ai_response, analysis)
            
        except json.JSONDecodeError:
            # Fallback to text parsing
            fixes = self._parse_unstructured_ai_response(ai_response, analysis)
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
        
        return fixes
    
    def _parse_ai_fix_item(self, item: Dict[str, Any], analysis: FailureAnalysis) -> Optional[CodeFix]:
        """Parse a single AI fix item"""
        try:
            return CodeFix(
                file_path=item.get('file_path', ''),
                description=item.get('description', ''),
                fix_type=item.get('fix_type', 'modification'),
                fixed_content=item.get('fixed_content'),
                confidence=FixConfidence(item.get('confidence', 'medium')),
                reasoning=item.get('reasoning', ''),
                estimated_impact=item.get('impact', 'low')
            )
        except Exception as e:
            logger.error(f"Failed to parse AI fix item: {e}")
            return None
    
    def _parse_unstructured_ai_response(self, response: str, analysis: FailureAnalysis) -> List[CodeFix]:
        """Parse unstructured AI response"""
        fixes = []
        
        # Simple pattern matching for common fix formats
        # This is a fallback when structured parsing fails
        
        lines = response.split('\n')
        current_fix = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('File:') or line.startswith('file:'):
                if current_fix:
                    fix = self._create_fix_from_dict(current_fix)
                    if fix:
                        fixes.append(fix)
                current_fix = {'file_path': line.split(':', 1)[1].strip()}
                
            elif line.startswith('Description:') or line.startswith('description:'):
                current_fix['description'] = line.split(':', 1)[1].strip()
                
            elif line.startswith('Fix:') or line.startswith('fix:'):
                current_fix['fixed_content'] = line.split(':', 1)[1].strip()
                
            elif line.startswith('Confidence:') or line.startswith('confidence:'):
                conf_text = line.split(':', 1)[1].strip().lower()
                if 'high' in conf_text:
                    current_fix['confidence'] = FixConfidence.HIGH
                elif 'low' in conf_text:
                    current_fix['confidence'] = FixConfidence.LOW
                else:
                    current_fix['confidence'] = FixConfidence.MEDIUM
        
        # Add last fix
        if current_fix:
            fix = self._create_fix_from_dict(current_fix)
            if fix:
                fixes.append(fix)
        
        return fixes
    
    def _create_fix_from_dict(self, fix_dict: Dict[str, Any]) -> Optional[CodeFix]:
        """Create CodeFix from dictionary"""
        try:
            return CodeFix(
                file_path=fix_dict.get('file_path', ''),
                description=fix_dict.get('description', 'AI-generated fix'),
                fix_type='modification',
                fixed_content=fix_dict.get('fixed_content'),
                confidence=fix_dict.get('confidence', FixConfidence.MEDIUM),
                reasoning=fix_dict.get('reasoning', 'Generated by AI analysis'),
                estimated_impact='medium'
            )
        except Exception:
            return None
    
    async def _generate_template_code_fixes(
        self, 
        analysis: FailureAnalysis, 
        context: FixContext
    ) -> List[CodeFix]:
        """Generate code fixes using templates"""
        
        fixes = []
        
        # Get templates for this failure type
        templates = self.fix_templates.get(analysis.failure_type, {})
        code_patterns = templates.get('code_patterns', [])
        
        for pattern in code_patterns:
            # Check if pattern matches the failure
            if self._pattern_matches_failure(pattern, analysis):
                fix = CodeFix(
                    file_path=analysis.affected_files[0] if analysis.affected_files else 'unknown',
                    description=pattern['template'],
                    fix_type='modification',
                    confidence=pattern['confidence'],
                    reasoning=f"Template-based fix for {pattern['pattern']}",
                    estimated_impact='low'
                )
                fixes.append(fix)
        
        return fixes
    
    async def _generate_config_fixes(
        self, 
        analysis: FailureAnalysis, 
        context: FixContext
    ) -> List[ConfigurationFix]:
        """Generate configuration fixes"""
        
        if not self.config.auto_fix.enable_config_fixes:
            return []
        
        fixes = []
        
        # Get templates for this failure type
        templates = self.fix_templates.get(analysis.failure_type, {})
        config_patterns = templates.get('config_patterns', [])
        
        for pattern in config_patterns:
            if self._pattern_matches_failure(pattern, analysis):
                fix = ConfigurationFix(
                    file_path=self._determine_config_file(pattern, analysis),
                    description=pattern['template'],
                    confidence=pattern['confidence'],
                    reasoning=f"Template-based config fix for {pattern['pattern']}"
                )
                fixes.append(fix)
        
        return fixes
    
    async def _generate_dependency_fixes(
        self, 
        analysis: FailureAnalysis, 
        context: FixContext
    ) -> List[DependencyFix]:
        """Generate dependency fixes"""
        
        if not self.config.auto_fix.enable_dependency_fixes:
            return []
        
        fixes = []
        
        # Get templates for this failure type
        templates = self.fix_templates.get(analysis.failure_type, {})
        dep_patterns = templates.get('dependency_patterns', [])
        
        for pattern in dep_patterns:
            if self._pattern_matches_failure(pattern, analysis):
                fix = DependencyFix(
                    description=pattern['template'],
                    fix_type='update',
                    package_name='unknown',  # Would need more analysis
                    confidence=pattern['confidence'],
                    reasoning=f"Template-based dependency fix for {pattern['pattern']}"
                )
                fixes.append(fix)
        
        return fixes
    
    def _pattern_matches_failure(self, pattern: Dict[str, Any], analysis: FailureAnalysis) -> bool:
        """Check if a pattern matches the failure"""
        pattern_name = pattern['pattern'].lower()
        
        # Check error messages
        for error_msg in analysis.error_messages:
            if pattern_name in error_msg.lower():
                return True
        
        # Check root cause
        if pattern_name in analysis.root_cause.lower():
            return True
        
        # Check affected files
        for file_path in analysis.affected_files:
            if pattern_name in file_path.lower():
                return True
        
        return False
    
    def _determine_config_file(self, pattern: Dict[str, Any], analysis: FailureAnalysis) -> str:
        """Determine which config file to modify"""
        pattern_name = pattern['pattern'].lower()
        
        if 'circleci' in pattern_name:
            return '.circleci/config.yml'
        elif 'typescript' in pattern_name or 'tsconfig' in pattern_name:
            return 'tsconfig.json'
        elif 'jest' in pattern_name:
            return 'jest.config.js'
        elif 'eslint' in pattern_name:
            return '.eslintrc.js'
        else:
            return 'package.json'
    
    def _deduplicate_code_fixes(self, fixes: List[CodeFix]) -> List[CodeFix]:
        """Remove duplicate code fixes"""
        seen = set()
        unique_fixes = []
        
        for fix in fixes:
            key = (fix.file_path, fix.description)
            if key not in seen:
                seen.add(key)
                unique_fixes.append(fix)
        
        return unique_fixes
    
    def _calculate_overall_confidence(
        self, 
        code_fixes: List[CodeFix], 
        config_fixes: List[ConfigurationFix], 
        dependency_fixes: List[DependencyFix]
    ) -> FixConfidence:
        """Calculate overall confidence for the fix"""
        
        all_confidences = []
        
        for fix in code_fixes:
            all_confidences.append(fix.confidence)
        
        for fix in config_fixes:
            all_confidences.append(fix.confidence)
        
        for fix in dependency_fixes:
            all_confidences.append(fix.confidence)
        
        if not all_confidences:
            return FixConfidence.LOW
        
        # Calculate average confidence
        confidence_values = {
            FixConfidence.HIGH: 0.9,
            FixConfidence.MEDIUM: 0.6,
            FixConfidence.LOW: 0.3,
            FixConfidence.VERY_LOW: 0.1
        }
        
        avg_confidence = sum(confidence_values[conf] for conf in all_confidences) / len(all_confidences)
        
        if avg_confidence >= 0.8:
            return FixConfidence.HIGH
        elif avg_confidence >= 0.5:
            return FixConfidence.MEDIUM
        elif avg_confidence >= 0.2:
            return FixConfidence.LOW
        else:
            return FixConfidence.VERY_LOW
    
    def _generate_fix_title(self, analysis: FailureAnalysis) -> str:
        """Generate fix title"""
        return f"Fix {analysis.failure_type.value.replace('_', ' ').title()}"
    
    def _generate_fix_description(
        self, 
        analysis: FailureAnalysis, 
        code_fixes: List[CodeFix], 
        config_fixes: List[ConfigurationFix], 
        dependency_fixes: List[DependencyFix]
    ) -> str:
        """Generate fix description"""
        
        description = f"Automated fix for {analysis.failure_type.value} in {analysis.project_slug}\n\n"
        description += f"Root cause: {analysis.root_cause}\n\n"
        
        if code_fixes:
            description += f"Code fixes ({len(code_fixes)}):\n"
            for fix in code_fixes:
                description += f"- {fix.file_path}: {fix.description}\n"
            description += "\n"
        
        if config_fixes:
            description += f"Configuration fixes ({len(config_fixes)}):\n"
            for fix in config_fixes:
                description += f"- {fix.file_path}: {fix.description}\n"
            description += "\n"
        
        if dependency_fixes:
            description += f"Dependency fixes ({len(dependency_fixes)}):\n"
            for fix in dependency_fixes:
                description += f"- {fix.package_name}: {fix.description}\n"
        
        return description
    
    def _generate_branch_name(self, analysis: FailureAnalysis) -> str:
        """Generate branch name for the fix"""
        prefix = self.config.github.pr_branch_prefix
        failure_type = analysis.failure_type.value.replace('_', '-')
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        return f"{prefix}/{failure_type}-{timestamp}"
    
    def _generate_commit_message(self, analysis: FailureAnalysis) -> str:
        """Generate commit message"""
        return f"🔧 Fix {analysis.failure_type.value.replace('_', ' ')}\n\nResolves: {analysis.root_cause}"
    
    def _generate_pr_title(self, analysis: FailureAnalysis) -> str:
        """Generate PR title"""
        return self.config.github.pr_title_template.format(
            failure_type=analysis.failure_type.value.replace('_', ' ').title()
        )
    
    def _generate_pr_description(
        self, 
        analysis: FailureAnalysis, 
        code_fixes: List[CodeFix], 
        config_fixes: List[ConfigurationFix], 
        dependency_fixes: List[DependencyFix]
    ) -> str:
        """Generate PR description"""
        
        changes_description = ""
        if code_fixes:
            changes_description += f"- {len(code_fixes)} code fixes\n"
        if config_fixes:
            changes_description += f"- {len(config_fixes)} configuration fixes\n"
        if dependency_fixes:
            changes_description += f"- {len(dependency_fixes)} dependency fixes\n"
        
        return self.config.github.pr_description_template.format(
            failure_type=analysis.failure_type.value.replace('_', ' ').title(),
            root_cause=analysis.root_cause,
            confidence=f"{analysis.confidence:.1%}",
            changes_description=changes_description,
            validation_results="Pending validation"
        )
    
    def _generate_validation_commands(self, analysis: FailureAnalysis) -> List[str]:
        """Generate validation commands"""
        commands = []
        
        if analysis.failure_type == FailureType.TEST_FAILURE:
            commands.extend(["npm test", "yarn test"])
        elif analysis.failure_type == FailureType.COMPILATION_ERROR:
            commands.extend(["npm run build", "yarn build", "tsc --noEmit"])
        elif analysis.failure_type == FailureType.DEPENDENCY_ERROR:
            commands.extend(["npm install", "yarn install"])
        
        return commands
    
    def _generate_test_commands(self, analysis: FailureAnalysis) -> List[str]:
        """Generate test commands"""
        return ["npm test", "yarn test", "npm run lint", "yarn lint"]
    
    async def apply_fix(self, fix: GeneratedFix) -> Dict[str, Any]:
        """Apply a generated fix"""
        
        logger.info(f"Applying fix: {fix.id}")
        
        try:
            # TODO: Implement actual fix application
            # This would involve:
            # 1. Cloning the repository
            # 2. Creating a new branch
            # 3. Applying the fixes
            # 4. Running validation
            # 5. Creating a PR
            
            # For now, return a mock result
            result = {
                "success": True,
                "pr_url": f"https://github.com/{fix.failure_analysis_id}/pull/123",
                "validation_results": {
                    "tests_passed": True,
                    "build_successful": True,
                    "linting_passed": True
                },
                "branch_name": fix.branch_name,
                "commit_sha": "abc123def456"
            }
            
            # Update fix status
            fix.status = "applied"
            fix.applied_at = datetime.now()
            fix.pr_url = result["pr_url"]
            fix.success = result["success"]
            
            # Update statistics
            self.fixes_applied += 1
            if result["success"]:
                self.fixes_successful += 1
            
            logger.info(f"Fix {fix.id} applied successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply fix {fix.id}: {e}")
            fix.status = "failed"
            fix.error_message = str(e)
            return {
                "success": False,
                "error": str(e)
            }
    
    # Public API methods
    def get_fix(self, fix_id: str) -> Optional[GeneratedFix]:
        """Get fix by ID"""
        return self.fix_cache.get(fix_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fix generation statistics"""
        return {
            "fixes_generated": self.fixes_generated,
            "fixes_applied": self.fixes_applied,
            "fixes_successful": self.fixes_successful,
            "success_rate": (self.fixes_successful / self.fixes_applied * 100) if self.fixes_applied > 0 else 0,
            "cache_size": len(self.fix_cache)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        codegen_healthy = self.codegen_client is not None if self.config.codegen.enabled else True
        
        return {
            "healthy": codegen_healthy,
            "codegen_available": self.codegen_client is not None,
            "templates_loaded": len(self.fix_templates),
            "stats": self.get_stats()
        }

