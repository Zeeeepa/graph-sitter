"""Enhanced Codebase AI with Context-Aware Analysis and Codegen SDK Integration."""

import asyncio
import codecs
import json
import logging
import time
from typing import Any, Dict, List, Union, Optional
from dataclasses import dataclass, field
from datetime import datetime

from graph_sitter.ai.client_factory import AIClientFactory
from graph_sitter.ai.context_gatherer import ContextGatherer
from graph_sitter.core.file import File
from graph_sitter.core.interfaces.editable import Editable

logger = logging.getLogger(__name__)


@dataclass
class AnalysisMetrics:
    """Metrics for code analysis performance and quality."""
    complexity_score: float = 0.0
    maintainability_score: float = 0.0
    documentation_coverage: float = 0.0
    test_coverage_estimate: float = 0.0
    dead_code_count: int = 0
    circular_dependencies: int = 0
    code_smells: List[str] = field(default_factory=list)
    technical_debt_indicators: List[str] = field(default_factory=list)


@dataclass
class ReactiveAnalysisContext:
    """Context for reactive code analysis with change tracking."""
    file_changes: List[str] = field(default_factory=list)
    quality_deltas: Dict[str, float] = field(default_factory=dict)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    dependency_changes: List[str] = field(default_factory=list)
    test_impact: List[str] = field(default_factory=list)
    performance_impact: Dict[str, Any] = field(default_factory=dict)


class AIResponse:
    """Structured response from AI with metadata and performance metrics."""
    
    def __init__(
        self,
        content: str,
        provider: str,
        model: str,
        tokens_used: int = 0,
        response_time: float = 0.0,
        context_size: int = 0,
        metadata: Dict[str, Any] = None,
        analysis_metrics: Optional[AnalysisMetrics] = None,
        reactive_context: Optional[ReactiveAnalysisContext] = None
    ):
        self.content = content
        self.provider = provider
        self.model = model
        self.tokens_used = tokens_used
        self.response_time = response_time
        self.context_size = context_size
        self.metadata = metadata or {}
        self.analysis_metrics = analysis_metrics
        self.reactive_context = reactive_context
        self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        return self.content
    
    def __repr__(self) -> str:
        return f"AIResponse(provider={self.provider}, model={self.model}, tokens={self.tokens_used})"
    
    def get_quality_insights(self) -> Dict[str, Any]:
        """Get quality insights from the analysis."""
        if not self.analysis_metrics:
            return {}
        
        return {
            "complexity": self.analysis_metrics.complexity_score,
            "maintainability": self.analysis_metrics.maintainability_score,
            "documentation": self.analysis_metrics.documentation_coverage,
            "technical_debt": len(self.analysis_metrics.technical_debt_indicators),
            "code_smells": len(self.analysis_metrics.code_smells),
            "overall_health": self._calculate_health_score()
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate overall code health score."""
        if not self.analysis_metrics:
            return 0.0
        
        # Weighted average of different quality metrics
        weights = {
            "complexity": 0.25,
            "maintainability": 0.30,
            "documentation": 0.20,
            "technical_debt": 0.25
        }
        
        complexity_score = max(0, 1.0 - self.analysis_metrics.complexity_score)
        maintainability_score = self.analysis_metrics.maintainability_score
        documentation_score = self.analysis_metrics.documentation_coverage
        debt_score = max(0, 1.0 - len(self.analysis_metrics.technical_debt_indicators) / 10)
        
        health_score = (
            complexity_score * weights["complexity"] +
            maintainability_score * weights["maintainability"] +
            documentation_score * weights["documentation"] +
            debt_score * weights["technical_debt"]
        )
        
        return min(1.0, max(0.0, health_score))


async def codebase_ai(
    codebase,
    prompt: str,
    target: Editable | None = None,
    context: Union[str, Editable, List[Editable], Dict[str, Union[str, Editable, List[Editable]]], None] = None,
    model: str = "gpt-4o",
    include_context: bool = True,
    max_context_tokens: int = 8000,
    enable_reactive_analysis: bool = True,
    include_quality_metrics: bool = True
) -> AIResponse:
    """Primary async method with full context awareness and reactive analysis.
    
    Args:
        codebase: The codebase instance
        prompt: The text prompt to send to the AI
        target: Optional editable object that provides the main focus
        context: Additional context to help inform the AI's response
        model: The AI model to use for generating the response
        include_context: Whether to automatically gather rich context
        max_context_tokens: Maximum tokens to use for context
        enable_reactive_analysis: Whether to include reactive analysis context
        include_quality_metrics: Whether to calculate quality metrics
        
    Returns:
        AIResponse object with structured response and metadata
    """
    start_time = time.time()
    
    # Get AI client and provider
    client, provider = AIClientFactory.create_client(
        openai_api_key=codebase.ctx.secrets.openai_api_key,
        codegen_org_id=codebase.ctx.secrets.codegen_org_id,
        codegen_token=codebase.ctx.secrets.codegen_token,
        prefer_codegen=True
    )
    
    # Gather comprehensive analysis context
    analysis_metrics = None
    reactive_context = None
    
    if include_quality_metrics:
        analysis_metrics = await _calculate_analysis_metrics(codebase, target)
    
    if enable_reactive_analysis:
        reactive_context = await _gather_reactive_context(codebase, target)
    
    # Generate enhanced system prompt with comprehensive context
    system_prompt = await _generate_enhanced_system_prompt(
        codebase, target, context, include_context, max_context_tokens,
        analysis_metrics, reactive_context
    )
    
    # Prepare messages with enhanced context
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    # Add context-aware tools if using Codegen
    tools = None
    if provider == "codegen":
        tools = generate_enhanced_tools(codebase, target, analysis_metrics)
    
    # Make AI request
    try:
        if provider == "codegen":
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                tools=tools,
                temperature=0
            )
        else:  # OpenAI
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=0
            )
        
        # Extract response content
        content = response.choices[0].message.content
        tokens_used = getattr(response, 'usage', {}).get('total_tokens', 0)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Create enhanced AI response
        ai_response = AIResponse(
            content=content,
            provider=provider,
            model=model,
            tokens_used=tokens_used,
            response_time=response_time,
            context_size=len(system_prompt),
            metadata={
                "target_type": target.__class__.__name__ if target else None,
                "context_included": include_context,
                "reactive_analysis": enable_reactive_analysis,
                "quality_metrics": include_quality_metrics
            },
            analysis_metrics=analysis_metrics,
            reactive_context=reactive_context
        )
        
        logger.info(f"AI request completed in {response_time:.2f}s using {provider}")
        return ai_response
        
    except Exception as e:
        logger.error(f"AI request failed: {e}")
        # Return error response
        return AIResponse(
            content=f"AI request failed: {str(e)}",
            provider=provider,
            model=model,
            response_time=time.time() - start_time,
            metadata={"error": str(e)}
        )


def codebase_ai_sync(
    codebase,
    prompt: str,
    target: Editable | None = None,
    context: Union[str, Editable, List[Editable], Dict[str, Union[str, Editable, List[Editable]]], None] = None,
    model: str = "gpt-4o",
    include_context: bool = True,
    max_context_tokens: int = 8000,
    enable_reactive_analysis: bool = True,
    include_quality_metrics: bool = True
) -> AIResponse:
    """Sync convenience method for non-async contexts with enhanced analysis.
    
    Args:
        codebase: The codebase instance
        prompt: The text prompt to send to the AI
        target: Optional editable object that provides the main focus
        context: Additional context to help inform the AI's response
        model: The AI model to use for generating the response
        include_context: Whether to automatically gather rich context
        max_context_tokens: Maximum tokens to use for context
        enable_reactive_analysis: Whether to include reactive analysis context
        include_quality_metrics: Whether to calculate quality metrics
        
    Returns:
        AIResponse object with structured response and metadata
    """
    return asyncio.run(codebase_ai(
        codebase, prompt, target, context, model, include_context, 
        max_context_tokens, enable_reactive_analysis, include_quality_metrics
    ))


async def _calculate_analysis_metrics(codebase, target: Editable | None = None) -> AnalysisMetrics:
    """Calculate comprehensive code analysis metrics."""
    metrics = AnalysisMetrics()
    
    try:
        # Calculate complexity metrics
        if target:
            # Target-specific metrics
            metrics.complexity_score = _calculate_complexity_score(target)
            metrics.maintainability_score = _calculate_maintainability_score(target)
            metrics.documentation_coverage = _calculate_documentation_coverage(target)
        else:
            # Codebase-wide metrics
            metrics.complexity_score = _calculate_codebase_complexity(codebase)
            metrics.maintainability_score = _calculate_codebase_maintainability(codebase)
            metrics.documentation_coverage = _calculate_codebase_documentation(codebase)
        
        # Calculate additional metrics
        metrics.dead_code_count = _count_dead_code(codebase, target)
        metrics.circular_dependencies = _count_circular_dependencies(codebase)
        metrics.code_smells = _detect_code_smells(codebase, target)
        metrics.technical_debt_indicators = _detect_technical_debt(codebase, target)
        metrics.test_coverage_estimate = _estimate_test_coverage(codebase, target)
        
    except Exception as e:
        logger.warning(f"Error calculating analysis metrics: {e}")
    
    return metrics


async def _gather_reactive_context(codebase, target: Editable | None = None) -> ReactiveAnalysisContext:
    """Gather reactive analysis context with change tracking."""
    context = ReactiveAnalysisContext()
    
    try:
        # Detect recent file changes
        context.file_changes = _get_recent_file_changes(codebase)
        
        # Calculate quality deltas
        context.quality_deltas = _calculate_quality_deltas(codebase, target)
        
        # Perform impact analysis
        context.impact_analysis = _perform_impact_analysis(codebase, target)
        
        # Analyze dependency changes
        context.dependency_changes = _analyze_dependency_changes(codebase, target)
        
        # Estimate test impact
        context.test_impact = _estimate_test_impact(codebase, target)
        
        # Analyze performance impact
        context.performance_impact = _analyze_performance_impact(codebase, target)
        
    except Exception as e:
        logger.warning(f"Error gathering reactive context: {e}")
    
    return context


async def _generate_enhanced_system_prompt(
    codebase,
    target: Editable | None = None,
    context: Union[str, Editable, List[Editable], Dict[str, Union[str, Editable, List[Editable]]], None] = None,
    include_context: bool = True,
    max_context_tokens: int = 8000,
    analysis_metrics: Optional[AnalysisMetrics] = None,
    reactive_context: Optional[ReactiveAnalysisContext] = None
) -> str:
    """Generate enhanced system prompt with comprehensive context."""
    
    # Base system prompt
    system_prompt = """You are an expert software engineer with deep knowledge of code analysis, refactoring, and development best practices.

You have access to comprehensive codebase analysis including:
- Static analysis results with complexity metrics
- Real-time change tracking and impact analysis  
- Quality metrics and technical debt indicators
- Dependency analysis and test coverage estimates
- Performance impact assessments

Use this rich context to provide accurate, actionable, and context-aware responses."""
    
    # Add codebase summary
    if include_context:
        codebase_summary = _generate_codebase_summary(codebase)
        system_prompt += f"\n\n## Codebase Overview\n{codebase_summary}"
    
    # Add target-specific context
    if target and include_context:
        target_context = _generate_target_context(target)
        system_prompt += f"\n\n## Target Analysis\n{target_context}"
    
    # Add quality metrics context
    if analysis_metrics:
        metrics_context = _generate_metrics_context(analysis_metrics)
        system_prompt += f"\n\n## Quality Metrics\n{metrics_context}"
    
    # Add reactive analysis context
    if reactive_context:
        reactive_context_str = _generate_reactive_context(reactive_context)
        system_prompt += f"\n\n## Change Impact Analysis\n{reactive_context_str}"
    
    # Add user-provided context
    if context:
        user_context = _process_user_context(context)
        system_prompt += f"\n\n## Additional Context\n{user_context}"
    
    # Truncate if necessary
    if len(system_prompt) > max_context_tokens * 4:  # Rough token estimation
        system_prompt = system_prompt[:max_context_tokens * 4] + "\n\n[Context truncated due to length]"
    
    return system_prompt


def generate_system_prompt(target: Editable | None = None, context: None | str | Editable | list[Editable] | dict[str, str | Editable | list[Editable]] = None) -> str:
    """Legacy system prompt generation for backward compatibility."""
    prompt = """Hey CodegenBot!
You are an incredibly precise and thoughtful AI who helps developers accomplish complex transformations on their codebase.
You always provide clear, concise, and accurate responses.
When dealing with code, you maintain the original structure and style unless explicitly asked to change it.
"""
    if target:
        prompt += f"""
The user has just requested a response on the following code snippet:

[[[CODE SNIPPET BEGIN]]]
{target.extended_source}
[[[CODE SNIPPET END]]]

Your job is to follow the instructions of the user, given the context provided.
"""
    else:
        prompt += """
Your job is to follow the instructions of the user.
"""

    if context:
        prompt += """
The user has provided some additional context that you can use to assist with your response.
You may use this context to inform your answer, but you're not required to directly include it in your response.

Here is the additional context:
"""
        prompt += generate_context(context)

    prompt += """
Please ensure your response is accurate and relevant to the user's request. You may think out loud in the response.


Generally, when responding with an an answer, try to follow these general "ground rules":
Remember, these are just rules you should follow by default. If the user explicitly asks for something else, you should follow their instructions instead.

> When generating new code or new classes, such as "create me a new function that does XYZ" or "generate a helper function that does XYZ", try to:

- Do not include extra indentation that is not necessary, unless the user explicitly asks for something else.
- Include as much information as possible. Do not write things like "# the rest of the class" or "# the rest of the method", unless the user explicitly asks for something else.
- Do try to include comments and well-documented code, unless the user explicitly asks for something else.
- Only return the NEW code without re-iterating any existing code that the user has provided to you, unless the user explicitly asks for something else.
- Do not include any code that the user has explicitly asked you to remove, unless the user explicitly asks for something else.


> When changing existing code, such as "change this method to do XYZ" or "update this function to do XYZ" or "remove all instances of XYZ from this class", try to:

- Do not include extra indentation that is not necessary, unless the user explicitly asks for something else.
- Include the entire context of the code that the user has provided to you, unless the user explicitly asks for something else.
- Include as much information as possible. Do not write things like "# the rest of the class" or "# the rest of the method", unless the user explicitly asks for something else.
- Do try to include comments and well-documented code, unless the user explicitly asks for something else.
- Avoid edit existing code that does not need editing, unless the user explicitly asks for something else.
- When asked to modify a very small or trivial part of the code, try to only modify the part that the user has asked you to modify, unless the user explicitly asks for something else.
- If asked to make improvements, try not to change existing function signatures, decorators, or returns, unless the user explicitly asks for something else.


> When dealing with anything related to docstrings, for example "Generate a google style docstring for this method." or "Convert these existing docs to google style docstrings.", try to:

- Do not include extra indentation that is not necessary, unless the user explicitly asks for something else.
- Use the google style docstring format first, unless the user explicitly asks for something else.
- If doing google style docstrings, do not include the "self" or "cls" argument in the list of arguments, unless the user explicitly asks for something else.
- Try to have at least one line of the docstring to be a summary line, unless the user explicitly asks for something else.
- Try to keep each line of the docstring to be less than 80 characters, unless the user explicitly asks for something else.
- Try to keep any existing before and after examples in the docstring, unless the user explicitly asks for something else.
- Only respond with the content of the docstring, without any additional context like the function signature, return type, or parameter types, unless the user explicitly asks for something else.
- Do not include formatting like tripple quotes in your response, unless the user explicitly asks for something else.
- Do not include any markdown formatting, unless the user explicitly asks for something else.

If you need a refresher on what google-style docstrings are:
- The first line is a summary line.
- The second line is a description of the method.
- The third line is a list of arguments.
- The fourth line is a list of returns.
Google docstrings may also include other information like exceptions and examples.
When generating NEW code or NEW classes, also try to generate docstrings alongside the code with the google style docstring format,
unless the user explicitly asks for something else.


> When dealing with anything related to comments, such as "write me a comment for this method" or "change this existing comment to be more descriptive", try to:

- Do not include extra indentation that is not necessary, unless the user explicitly asks for something else.
- Do not include any comment delimiters like "#" or "//" unless the user explicitly asks for something else.
- Do not include any markdown formatting, unless the user explicitly asks for something else.
- Try to keep each line of the comment to be less than 80 characters, unless the user explicitly asks for something else.
- If you are only requested to edit or create a comment, do not include any code or other context that the user has provided to you, unless the user explicitly asks for something else.


> When dealing with single-word or single-phrase answers, like "what is a better name for this function" or "what is a better name for this class", try to:

- Only respond with the content of the new name, without any additional context like the function signature, return type, or parameter types, unless the user explicitly asks for something else.
- Do not include formatting like tripple quotes in your response, unless the user explicitly asks for something else.
- Do not include any markdown formatting, unless the user explicitly asks for something else.
- Do not include any code or other context that the user has provided to you, unless the user explicitly asks for something else.

REMEMBER: When giving the final answer, you must use the set_answer tool to provide the final answer that will be used in subsequent operations such as writing to a file, renaming, or editing.
    """

    return prompt


def generate_flag_system_prompt(target: Editable, context: None | str | Editable | list[Editable] | dict[str, str | Editable | list[Editable]] = None) -> str:
    prompt = f"""Hey CodegenBot!
You are an incredibly precise and thoughtful AI who helps developers accomplish complex transformations on their codebase.

You are now tasked with determining whether to flag the symbol, file, attribute, or message using AI.
Flagging a symbol means to mark it as a chunk of code that should be modified in a later step.
You will be given the user prompt, and the code snippet that the user is requesting a response on.
Use the should_flag tool to return either a true or false answer to the question of whether to flag the symbol, file, attribute, or message.

Here is the code snippet that the user is requesting a response on:

[[[CODE SNIPPET BEGIN]]]
{target.extended_source}
[[[CODE SNIPPET END]]]
"""

    if context:
        prompt += """
The user has provided some additional context that you can use to assist with your response.
You may use this context to inform your answer, but you're not required to directly include it in your response.

Here is the additional context:
"""
        prompt += generate_context(context)

    prompt += """
Please intelligently determine whether the user's request on the given code snippet should be flagged.
Remember, use the should_flag tool to return either a true or false answer to the question of whether to flag the symbol, file, attribute, or message
as a chunk of code that should be modified, edited, or changed in a later step.
    """

    return prompt


def generate_context(context: None | str | Editable | list[Editable | File] | dict[str, str | Editable | list[Editable] | File] | File = None) -> str:
    output = ""
    if not context:
        return output
    else:
        if isinstance(context, str):
            output += f"====== Context ======\n{context}\n====================\n\n"
        elif isinstance(context, Editable):
            # Get class name
            output += f"====== {context.__class__.__name__} ======\n"
            output += f"{context.extended_source}\n"
            output += "====================\n\n"
        elif isinstance(context, File):
            output += f"====== {context.__class__.__name__}======\n"
            output += f"{context.source}\n"
            output += "====================\n\n"
        elif isinstance(context, list):
            for item in context:
                output += generate_context(item)
        elif isinstance(context, dict):
            for key, value in context.items():
                output += f"[[[ {key} ]]]\n"
                output += generate_context(value)
                output += "\n\n"
        return output


def generate_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "set_answer",
                "description": "Use this function to set the final answer to the given prompt. This answer will be used in subsequent operations such as writing to a file, renaming, or editing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "description": "The final answer to the given prompt. Do not include any uneccesary context or commentary in your response.",
                        },
                    },
                    "required": ["answer"],
                },
            },
        }
    ]


def generate_flag_tools() -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "should_flag",
                "description": "Use this function to determine whether to flag the symbol, file, attribute, or message using AI.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "flag": {
                            "type": "boolean",
                            "description": "Whether to flag the symbol, file, attribute, or message.",
                        },
                    },
                    "required": ["flag"],
                },
            },
        }
    ]


def generate_enhanced_tools(codebase, target, analysis_metrics) -> list:
    tools = generate_tools()
    
    if analysis_metrics:
        tools.append({
            "type": "function",
            "function": {
                "name": "get_quality_insights",
                "description": "Use this function to get quality insights from the analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "analysis_metrics": {
                            "type": "object",
                            "description": "The analysis metrics to use for quality insights.",
                        },
                    },
                    "required": ["analysis_metrics"],
                },
            },
        })
    
    return tools


def _calculate_complexity_score(target) -> float:
    """Calculate complexity score for a target."""
    # Placeholder implementation
    return 0.0


def _calculate_maintainability_score(target) -> float:
    """Calculate maintainability score for a target."""
    # Placeholder implementation
    return 0.0


def _calculate_documentation_coverage(target) -> float:
    """Calculate documentation coverage for a target."""
    # Placeholder implementation
    return 0.0


def _calculate_codebase_complexity(codebase) -> float:
    """Calculate codebase complexity."""
    # Placeholder implementation
    return 0.0


def _calculate_codebase_maintainability(codebase) -> float:
    """Calculate codebase maintainability."""
    # Placeholder implementation
    return 0.0


def _calculate_codebase_documentation(codebase) -> float:
    """Calculate codebase documentation coverage."""
    # Placeholder implementation
    return 0.0


def _count_dead_code(codebase, target) -> int:
    """Count dead code in the codebase."""
    # Placeholder implementation
    return 0


def _count_circular_dependencies(codebase) -> int:
    """Count circular dependencies in the codebase."""
    # Placeholder implementation
    return 0


def _detect_code_smells(codebase, target) -> List[str]:
    """Detect code smells in the codebase."""
    # Placeholder implementation
    return []


def _detect_technical_debt(codebase, target) -> List[str]:
    """Detect technical debt in the codebase."""
    # Placeholder implementation
    return []


def _estimate_test_coverage(codebase, target) -> float:
    """Estimate test coverage for the codebase."""
    # Placeholder implementation
    return 0.0


def _get_recent_file_changes(codebase) -> List[str]:
    """Get recent file changes in the codebase."""
    # Placeholder implementation
    return []


def _calculate_quality_deltas(codebase, target) -> Dict[str, float]:
    """Calculate quality deltas for the codebase."""
    # Placeholder implementation
    return {}


def _perform_impact_analysis(codebase, target) -> Dict[str, Any]:
    """Perform impact analysis for the codebase."""
    # Placeholder implementation
    return {}


def _analyze_dependency_changes(codebase, target) -> List[str]:
    """Analyze dependency changes in the codebase."""
    # Placeholder implementation
    return []


def _estimate_test_impact(codebase, target) -> List[str]:
    """Estimate test impact for the codebase."""
    # Placeholder implementation
    return []


def _analyze_performance_impact(codebase, target) -> Dict[str, Any]:
    """Analyze performance impact for the codebase."""
    # Placeholder implementation
    return {}


def _generate_codebase_summary(codebase) -> str:
    """Generate a summary of the codebase."""
    # Placeholder implementation
    return ""


def _generate_target_context(target) -> str:
    """Generate context for a target."""
    # Placeholder implementation
    return ""


def _generate_metrics_context(metrics) -> str:
    """Generate context for analysis metrics."""
    # Placeholder implementation
    return ""


def _generate_reactive_context(context) -> str:
    """Generate context for reactive analysis context."""
    # Placeholder implementation
    return ""


def _process_user_context(context) -> str:
    """Process user-provided context."""
    # Placeholder implementation
    return ""
