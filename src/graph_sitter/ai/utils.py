import threading
from typing import Dict, Optional, Any

# Optional import for tiktoken
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = None

# Thread-safe encoder cache with lazy loading
_encoder_cache: Dict[str, Any] = {}
_cache_lock = threading.Lock()

# Default models and their encodings
DEFAULT_MODELS = {
    "gpt-4o": "o200k_base",
    "gpt-4": "cl100k_base", 
    "gpt-3.5-turbo": "cl100k_base",
    "text-embedding-3-small": "cl100k_base",
    "text-embedding-3-large": "cl100k_base"
}


def get_encoder(model_name: str) -> Any:
    """Get or create a cached encoder for the given model.
    
    Args:
        model_name: Name of the model to get encoder for
        
    Returns:
        tiktoken.Encoding instance for the model (if tiktoken available)
        
    Raises:
        ValueError: If model is not supported or tiktoken not available
    """
    if not TIKTOKEN_AVAILABLE:
        raise ValueError("tiktoken package not available. Install with: pip install tiktoken")
    
    with _cache_lock:
        if model_name not in _encoder_cache:
            try:
                # Try to get encoding directly for the model
                _encoder_cache[model_name] = tiktoken.encoding_for_model(model_name)
            except KeyError:
                # Fallback to default encoding if model not found
                encoding_name = DEFAULT_MODELS.get(model_name, "cl100k_base")
                try:
                    _encoder_cache[model_name] = tiktoken.get_encoding(encoding_name)
                except Exception as e:
                    raise ValueError(f"Unsupported model '{model_name}': {e}") from e
        
        return _encoder_cache[model_name]


def count_tokens(s: str, model_name: str = "gpt-4o") -> int:
    """Count tokens in a string using tiktoken with caching.
    
    Args:
        s: String to count tokens for
        model_name: Model name to use for tokenization
        
    Returns:
        Number of tokens in the string
    """
    if s is None:
        return 0
    
    if not isinstance(s, str):
        s = str(s)
    
    if not s.strip():  # Empty or whitespace-only string
        return 0
    
    if not TIKTOKEN_AVAILABLE:
        # Fallback to estimation if tiktoken not available
        return estimate_tokens_fast(s)
    
    try:
        encoder = get_encoder(model_name)
        tokens = encoder.encode(s)
        return len(tokens)
    except Exception as e:
        # Fallback to rough estimation if encoding fails
        return estimate_tokens_fast(s)


def estimate_tokens_fast(s: str) -> int:
    """Fast token estimation without tiktoken (useful for quick checks).
    
    Args:
        s: String to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    if not s:
        return 0
    
    # More sophisticated estimation based on text characteristics
    # Average English word is ~4.7 characters, ~1.3 tokens per word
    words = len(s.split())
    chars = len(s)
    
    # Use word-based estimation for text with reasonable word density
    if chars > 0 and words / chars > 0.1:  # At least 10% word density
        return max(1, int(words * 1.3))
    else:
        # Use character-based estimation for dense text/code
        return max(1, chars // 4)


def clear_encoder_cache() -> None:
    """Clear the encoder cache (useful for testing or memory management)."""
    with _cache_lock:
        _encoder_cache.clear()


def get_cache_info() -> Dict[str, int]:
    """Get information about the current encoder cache.
    
    Returns:
        Dictionary with cache statistics
    """
    with _cache_lock:
        return {
            "cached_models": len(_encoder_cache),
            "model_names": list(_encoder_cache.keys())
        }


def validate_token_limit(text: str, max_tokens: int, model_name: str = "gpt-4o") -> bool:
    """Check if text is within token limit for a model.
    
    Args:
        text: Text to validate
        max_tokens: Maximum allowed tokens
        model_name: Model name for tokenization
        
    Returns:
        True if text is within limit, False otherwise
    """
    if not text:
        return True
    
    token_count = count_tokens(text, model_name)
    return token_count <= max_tokens


def truncate_to_token_limit(
    text: str, 
    max_tokens: int, 
    model_name: str = "gpt-4o",
    truncation_strategy: str = "end"
) -> str:
    """Truncate text to fit within token limit.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum allowed tokens
        model_name: Model name for tokenization
        truncation_strategy: "start", "end", or "middle"
        
    Returns:
        Truncated text that fits within token limit
    """
    if not text or max_tokens <= 0:
        return ""
    
    current_tokens = count_tokens(text, model_name)
    if current_tokens <= max_tokens:
        return text
    
    if not TIKTOKEN_AVAILABLE:
        # Fallback to character-based truncation
        chars_per_token = 4
        max_chars = max_tokens * chars_per_token
        
        if truncation_strategy == "start":
            return f"...{text[-max_chars:]}"
        elif truncation_strategy == "middle":
            start_chars = max_chars // 2
            end_chars = max_chars - start_chars - 3  # -3 for ellipsis
            return f"{text[:start_chars]}...{text[-end_chars:]}"
        else:  # "end" strategy (default)
            return f"{text[:max_chars]}..."
    
    # Binary search for optimal truncation point
    encoder = get_encoder(model_name)
    tokens = encoder.encode(text)
    
    if len(tokens) <= max_tokens:
        return text
    
    if truncation_strategy == "start":
        # Keep the end of the text
        truncated_tokens = tokens[-max_tokens:]
        truncated_text = encoder.decode(truncated_tokens)
        return f"...{truncated_text}"
    elif truncation_strategy == "middle":
        # Keep start and end, remove middle
        start_tokens = max_tokens // 2
        end_tokens = max_tokens - start_tokens - 1  # -1 for ellipsis
        
        start_text = encoder.decode(tokens[:start_tokens])
        end_text = encoder.decode(tokens[-end_tokens:])
        return f"{start_text}...{end_text}"
    else:  # "end" strategy (default)
        # Keep the beginning of the text
        truncated_tokens = tokens[:max_tokens]
        truncated_text = encoder.decode(truncated_tokens)
        return f"{truncated_text}..."
