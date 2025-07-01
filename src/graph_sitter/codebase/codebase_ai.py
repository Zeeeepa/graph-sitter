"""Enhanced Codebase AI with Context-Aware Analysis and Codegen SDK Integration."""

import asyncio
import codecs
import json
import logging
import time
from typing import Any, Dict, List, Union

from graph_sitter.ai.client_factory import AIClientFactory
from graph_sitter.ai.context_gatherer import ContextGatherer
from graph_sitter.core.file import File
from graph_sitter.core.interfaces.editable import Editable

logger = logging.getLogger(__name__)


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
        metadata: Dict[str, Any] = None
    ):
        self.content = content
        self.provider = provider
        self.model = model
        self.tokens_used = tokens_used
        self.response_time = response_time
        self.context_size = context_size
        self.metadata = metadata or {}
    
    def __str__(self) -> str:
        return self.content
    
    def __repr__(self) -> str:
        return f"AIResponse(provider={self.provider}, model={self.model}, tokens={self.tokens_used})"


async def codebase_ai(
    codebase,
    prompt: str,
    target: Editable | None = None,
    context: Union[str, Editable, List[Editable], Dict[str, Union[str, Editable, List[Editable]]], None] = None,
    model: str = "gpt-4o",
    include_context: bool = True,
    max_context_tokens: int = 8000
) -> AIResponse:
    """Primary async method with full context awareness.
    
    Args:
        codebase: The codebase instance
        prompt: The text prompt to send to the AI
        target: Optional editable object that provides the main focus
        context: Additional context to help inform the AI's response
        model: The AI model to use for generating the response
        include_context: Whether to automatically gather rich context
        max_context_tokens: Maximum tokens to use for context
        
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
    
    # Generate enhanced system prompt with context
    system_prompt = await _generate_enhanced_system_prompt(
        codebase, target, context, include_context, max_context_tokens
    )
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    # Make AI request
    try:
        if provider == "codegen":
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                tools=generate_tools(),
                temperature=0
            )
        else:  # OpenAI
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=generate_tools(),
                temperature=0,
                tool_choice="required" if model.startswith("gpt") else None
            )
        
        # Extract response content
        content = _extract_response_content(response)
        
        # Calculate metrics
        response_time = time.time() - start_time
        context_size = len(system_prompt)
        
        return AIResponse(
            content=content,
            provider=provider,
            model=model,
            tokens_used=0,  # TODO: Extract from response if available
            response_time=response_time,
            context_size=context_size,
            metadata={"target_type": target.__class__.__name__ if target else None}
        )
        
    except Exception as e:
        logger.error(f"AI request failed: {e}")
        raise


def codebase_ai_sync(
    codebase,
    prompt: str,
    target: Editable | None = None,
    context: Union[str, Editable, List[Editable], Dict[str, Union[str, Editable, List[Editable]]], None] = None,
    model: str = "gpt-4o",
    include_context: bool = True,
    max_context_tokens: int = 8000
) -> AIResponse:
    """Sync convenience method for non-async contexts."""
    return asyncio.run(codebase_ai(
        codebase, prompt, target, context, model, include_context, max_context_tokens
    ))


async def _generate_enhanced_system_prompt(
    codebase,
    target: Editable | None = None,
    context: Union[str, Editable, List[Editable], Dict[str, Union[str, Editable, List[Editable]]], None] = None,
    include_context: bool = True,
    max_context_tokens: int = 8000
) -> str:
    """Generate enhanced system prompt with rich context awareness."""
    
    # Base prompt
    prompt = """Hey CodegenBot!
You are an incredibly precise and thoughtful AI who helps developers accomplish complex transformations on their codebase.
You always provide clear, concise, and accurate responses.
When dealing with code, you maintain the original structure and style unless explicitly asked to change it.

You have access to comprehensive codebase analysis and context information to help you provide more accurate and relevant responses.
"""

    # Add target-specific information
    if target:
        prompt += f"""
The user has requested a response on the following code element:

[[[TARGET CODE BEGIN]]]
{target.extended_source if hasattr(target, 'extended_source') else getattr(target, 'source', 'Source not available')}
[[[TARGET CODE END]]]

Your job is to follow the instructions of the user, given the context provided.
"""
    else:
        prompt += """
Your job is to follow the instructions of the user.
"""

    # Add rich context if enabled
    if include_context and target:
        try:
            context_gatherer = ContextGatherer(codebase)
            rich_context = context_gatherer.gather_target_context(target)
            formatted_context = context_gatherer.format_context_for_prompt(rich_context)
            optimized_context = context_gatherer.optimize_context_size(formatted_context, max_context_tokens)
            
            prompt += f"""

[[[RICH CONTEXT BEGIN]]]
{optimized_context}
[[[RICH CONTEXT END]]]
"""
        except Exception as e:
            logger.warning(f"Failed to gather rich context: {e}")

    # Add user-provided context
    if context:
        prompt += """
The user has provided some additional context that you can use to assist with your response.
You may use this context to inform your answer, but you're not required to directly include it in your response.

Here is the additional context:
"""
        prompt += generate_context(context)

    # Add the rest of the original system prompt guidelines
    prompt += """
Please ensure your response is accurate and relevant to the user's request. You may think out loud in the response.

Generally, when responding with an answer, try to follow these general "ground rules":
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
- Avoid editing existing code that does not need editing, unless the user explicitly asks for something else.
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
- Do not include formatting like triple quotes in your response, unless the user explicitly asks for something else.
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
- Do not include formatting like triple quotes in your response, unless the user explicitly asks for something else.
- Do not include any markdown formatting, unless the user explicitly asks for something else.
- Do not include any code or other context that the user has provided to you, unless the user explicitly asks for something else.

REMEMBER: When giving the final answer, you must use the set_answer tool to provide the final answer that will be used in subsequent operations such as writing to a file, renaming, or editing.
"""

    return prompt


def _extract_response_content(response) -> str:
    """Extract content from AI response."""
    if hasattr(response, 'choices') and response.choices:
        choice = response.choices[0]
        if choice.finish_reason in ["tool_calls", "function_call", "stop"]:
            if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                tool_call = choice.message.tool_calls[0]
                response_answer = json.loads(tool_call.function.arguments)
                if "answer" in response_answer:
                    response_answer = response_answer["answer"]
                else:
                    raise ValueError("No answer found in tool call")
            else:
                raise ValueError("No tool call found in AI response")
        elif choice.finish_reason == "length":
            raise ValueError("AI response too long / ran out of tokens")
        elif choice.finish_reason == "content_filter":
            raise ValueError("AI response was blocked by content filter")
        else:
            raise ValueError(f"Unknown finish reason from AI: {choice.finish_reason}")
    else:
        raise ValueError("No response from AI Provider")

    # Handle escape sequences
    response_answer = codecs.decode(response_answer, "unicode_escape")
    return response_answer


# Legacy functions for backward compatibility
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
