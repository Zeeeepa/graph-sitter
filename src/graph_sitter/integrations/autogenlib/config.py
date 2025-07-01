"""Configuration for autogenlib integration."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AutogenLibConfig(BaseSettings):
    """Configuration for autogenlib integration."""
    
    # Core autogenlib settings
    enabled: bool = Field(default=False, description="Enable autogenlib integration")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key for code generation")
    openai_api_base_url: Optional[str] = Field(default=None, description="OpenAI API base URL")
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    
    # Caching settings
    enable_caching: bool = Field(default=True, description="Enable caching of generated code")
    cache_directory: Optional[str] = Field(default=None, description="Directory for autogenlib cache")
    
    # Exception handling
    enable_exception_handler: bool = Field(default=True, description="Enable autogenlib exception handler")
    
    # Graph-sitter integration settings
    use_graph_sitter_context: bool = Field(default=True, description="Use graph-sitter for enhanced context")
    max_context_size: int = Field(default=10000, description="Maximum context size in characters")
    include_ast_analysis: bool = Field(default=True, description="Include AST analysis in context")
    include_symbol_table: bool = Field(default=True, description="Include symbol table in context")
    
    # Generation settings
    temperature: float = Field(default=0.1, description="Temperature for code generation")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens for generation")
    
    # Database settings
    store_generation_history: bool = Field(default=True, description="Store generation history in database")
    store_patterns: bool = Field(default=True, description="Store successful patterns for reuse")
    
    # Security settings
    allowed_namespaces: list[str] = Field(
        default_factory=lambda: ["autogenlib.generated"],
        description="Allowed namespaces for dynamic generation"
    )
    
    class Config:
        env_prefix = "GRAPH_SITTER_AUTOGENLIB_"
        case_sensitive = False


class GenerationRequest(BaseModel):
    """Request for code generation."""
    
    module_name: str = Field(description="Name of the module to generate")
    function_name: Optional[str] = Field(default=None, description="Specific function to generate")
    description: str = Field(description="Description of what to generate")
    existing_code: Optional[str] = Field(default=None, description="Existing code to extend")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    caller_info: Optional[Dict[str, Any]] = Field(default=None, description="Information about the caller")


class GenerationResult(BaseModel):
    """Result of code generation."""
    
    success: bool = Field(description="Whether generation was successful")
    code: Optional[str] = Field(default=None, description="Generated code")
    error: Optional[str] = Field(default=None, description="Error message if generation failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    context_used: Optional[Dict[str, Any]] = Field(default=None, description="Context that was used")
    generation_time: Optional[float] = Field(default=None, description="Time taken for generation")

