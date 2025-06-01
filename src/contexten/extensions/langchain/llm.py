"""LLM implementation supporting OpenAI, Anthropic, XAI, and Codegen SDK models."""

import os
from collections.abc import Sequence
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_xai import ChatXAI
from pydantic import Field

# Import our custom Codegen chat model
from .codegen_chat import ChatCodegen
from .llm_config import get_llm_config


class LLM(BaseChatModel):
    """A unified chat model that supports OpenAI, Anthropic, XAI, and Codegen SDK."""

    model_provider: str = Field(default="anthropic", description="The model provider to use.")

    model_name: str = Field(default="claude-3-5-sonnet-latest", description="Name of the model to use.")

    temperature: float = Field(default=0, description="Temperature parameter for the model.", ge=0, le=1)

    top_p: Optional[float] = Field(default=None, description="Top-p sampling parameter.", ge=0, le=1)

    top_k: Optional[int] = Field(default=None, description="Top-k sampling parameter.", ge=1)

    max_tokens: Optional[int] = Field(default=None, description="Maximum number of tokens to generate.", ge=1)
    
    # Codegen SDK specific fields
    codegen_org_id: Optional[str] = Field(default=None, description="Codegen organization ID")
    codegen_token: Optional[str] = Field(default=None, description="Codegen API token")

    def __init__(self, model_provider: str = "anthropic", model_name: str = "claude-3-5-sonnet-latest", **kwargs: Any) -> None:
        """Initialize the LLM.

        Args:
            model_provider: "anthropic", "openai", "xai", or "codegen"
            model_name: Name of the model to use
            **kwargs: Additional configuration options. Supported options:
                - temperature: Temperature parameter (0-1)
                - top_p: Top-p sampling parameter (0-1)
                - top_k: Top-k sampling parameter (>= 1)
                - max_tokens: Maximum number of tokens to generate
                - codegen_org_id: Codegen organization ID (for codegen provider)
                - codegen_token: Codegen API token (for codegen provider)
        """
        # Set model provider and name before calling super().__init__
        kwargs["model_provider"] = model_provider
        kwargs["model_name"] = model_name

        # Filter out unsupported kwargs
        supported_kwargs = {
            "model_provider", "model_name", "temperature", "top_p", "top_k", 
            "max_tokens", "callbacks", "tags", "metadata", "codegen_org_id", "codegen_token"
        }
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_kwargs}

        super().__init__(**filtered_kwargs)
        self._model = self._get_model()

    @classmethod
    def from_config(cls, **kwargs) -> "LLM":
        """Create LLM instance using global configuration.
        
        This method uses the global LLM configuration to determine the default
        provider and settings, while allowing overrides via kwargs.
        
        Args:
            **kwargs: Override any configuration settings
            
        Returns:
            LLM instance configured with global settings
        """
        config = get_llm_config()
        
        # Start with global configuration
        provider = kwargs.pop("model_provider", None) or config.auto_select_provider()
        model = kwargs.pop("model_name", None) or config.default_model
        
        # Get provider-specific configuration
        provider_config = config.get_provider_config(provider)
        
        # Merge configurations (kwargs take precedence)
        final_kwargs = {**provider_config, **kwargs}
        
        return cls(model_provider=provider, model_name=model, **final_kwargs)

    @classmethod
    def with_codegen(cls, org_id: str, token: str, model: str = "codegen-agent", **kwargs) -> "LLM":
        """Create LLM instance specifically configured for Codegen SDK.
        
        Args:
            org_id: Codegen organization ID
            token: Codegen API token
            model: Model name to use
            **kwargs: Additional configuration options
            
        Returns:
            LLM instance configured for Codegen SDK
        """
        return cls(
            model_provider="codegen",
            model_name=model,
            codegen_org_id=org_id,
            codegen_token=token,
            **kwargs
        )

    @property
    def _llm_type(self) -> str:
        """Return identifier for this LLM class."""
        return "unified_chat_model"

    def _get_model_kwargs(self) -> dict[str, Any]:
        """Get kwargs for the specific model provider."""
        base_kwargs = {
            "temperature": self.temperature,
        }

        if self.top_p is not None:
            base_kwargs["top_p"] = self.top_p

        if self.top_k is not None:
            base_kwargs["top_k"] = self.top_k

        if self.max_tokens is not None:
            base_kwargs["max_tokens"] = self.max_tokens

        if self.model_provider == "anthropic":
            return {**base_kwargs, "model": self.model_name}
        elif self.model_provider == "xai":
            xai_api_base = os.getenv("XAI_API_BASE", "https://api.x.ai/v1/")
            return {**base_kwargs, "model": self.model_name, "xai_api_base": xai_api_base}
        elif self.model_provider == "codegen":
            return {**base_kwargs, "model": self.model_name, "org_id": self.codegen_org_id, "token": self.codegen_token}
        else:  # openai
            return {**base_kwargs, "model": self.model_name}

    def _get_model(self) -> BaseChatModel:
        """Get the appropriate model instance based on configuration."""
        if self.model_provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                msg = "ANTHROPIC_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            max_tokens = 8192
            return ChatAnthropic(**self._get_model_kwargs(), max_tokens=max_tokens, max_retries=10, timeout=1000)

        elif self.model_provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                msg = "OPENAI_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatOpenAI(**self._get_model_kwargs(), max_tokens=4096, max_retries=10, timeout=1000)

        elif self.model_provider == "xai":
            if not os.getenv("XAI_API_KEY"):
                msg = "XAI_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatXAI(**self._get_model_kwargs(), max_tokens=12000)

        elif self.model_provider == "codegen":
            # Use credentials from instance or environment
            org_id = self.codegen_org_id or os.getenv("CODEGEN_ORG_ID")
            token = self.codegen_token or os.getenv("CODEGEN_TOKEN")
            
            if not org_id:
                msg = "CODEGEN_ORG_ID not found. Please provide codegen_org_id parameter or set CODEGEN_ORG_ID environment variable."
                raise ValueError(msg)
            if not token:
                msg = "CODEGEN_TOKEN not found. Please provide codegen_token parameter or set CODEGEN_TOKEN environment variable."
                raise ValueError(msg)
                
            model_kwargs = self._get_model_kwargs()
            return ChatCodegen(
                org_id=org_id,
                token=token,
                model_name=model_kwargs.get("model", self.model_name),
                temperature=model_kwargs.get("temperature", self.temperature),
                max_tokens=model_kwargs.get("max_tokens", 4000)
            )

        msg = f"Unknown model provider: {self.model_provider}. Must be one of: anthropic, openai, xai, codegen"
        raise ValueError(msg)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completion using the underlying model.

        Args:
            messages: The messages to generate from
            stop: Optional list of stop sequences
            run_manager: Optional callback manager for tracking the run
            **kwargs: Additional arguments to pass to the model

        Returns:
            ChatResult containing the generated completion
        """
        return self._model._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def bind_tools(
        self,
        tools: Sequence[BaseTool],
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind tools to the underlying model.

        Args:
            tools: List of tools to bind
            **kwargs: Additional arguments to pass to the model

        Returns:
            Runnable that can be used to invoke the model with tools
        """
        return self._model.bind_tools(tools, **kwargs)
