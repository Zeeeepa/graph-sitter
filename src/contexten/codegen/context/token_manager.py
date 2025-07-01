"""
Token management for context optimization.

This module provides token counting and management utilities to ensure
context stays within API token limits while maximizing information density.
"""

import re
import logging
from typing import List, Optional, Dict, Any
import tiktoken


logger = logging.getLogger(__name__)


class TokenManager:
    """
    Token management for context optimization.
    
    Provides utilities for:
    - Accurate token counting
    - Content truncation to fit token limits
    - Token-aware content optimization
    - Multiple encoding support
    """
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Initialize token manager.
        
        Args:
            encoding_name: Tiktoken encoding name (cl100k_base for GPT-4)
        """
        self.encoding_name = encoding_name
        self._encoder = None
        self._fallback_enabled = True
        
        try:
            self._encoder = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoder {encoding_name}: {e}")
            logger.info("Falling back to simple token estimation")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        if self._encoder:
            try:
                return len(self._encoder.encode(text))
            except Exception as e:
                logger.warning(f"Token encoding failed: {e}")
        
        # Fallback to simple estimation
        return self._estimate_tokens(text)
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens
            
        Returns:
            Truncated text
        """
        if not text or max_tokens <= 0:
            return ""
        
        current_tokens = self.count_tokens(text)
        if current_tokens <= max_tokens:
            return text
        
        if self._encoder:
            try:
                # Encode and truncate
                tokens = self._encoder.encode(text)
                truncated_tokens = tokens[:max_tokens]
                return self._encoder.decode(truncated_tokens)
            except Exception as e:
                logger.warning(f"Token truncation failed: {e}")
        
        # Fallback to character-based truncation
        return self._truncate_by_chars(text, max_tokens)
    
    def optimize_content_for_tokens(self,
                                  content: str,
                                  max_tokens: int,
                                  preserve_structure: bool = True) -> str:
        """
        Optimize content to fit within token limits while preserving important information.
        
        Args:
            content: Content to optimize
            max_tokens: Maximum number of tokens
            preserve_structure: Whether to preserve code structure
            
        Returns:
            Optimized content
        """
        if not content or max_tokens <= 0:
            return ""
        
        current_tokens = self.count_tokens(content)
        if current_tokens <= max_tokens:
            return content
        
        if preserve_structure:
            return self._optimize_structured_content(content, max_tokens)
        else:
            return self.truncate_to_tokens(content, max_tokens)
    
    def split_content_by_tokens(self,
                              content: str,
                              chunk_size: int,
                              overlap: int = 0) -> List[str]:
        """
        Split content into chunks by token count.
        
        Args:
            content: Content to split
            chunk_size: Maximum tokens per chunk
            overlap: Number of overlapping tokens between chunks
            
        Returns:
            List of content chunks
        """
        if not content or chunk_size <= 0:
            return []
        
        if self._encoder:
            try:
                tokens = self._encoder.encode(content)
                chunks = []
                
                start = 0
                while start < len(tokens):
                    end = min(start + chunk_size, len(tokens))
                    chunk_tokens = tokens[start:end]
                    chunk_text = self._encoder.decode(chunk_tokens)
                    chunks.append(chunk_text)
                    
                    # Move start position with overlap
                    start = end - overlap
                    if start >= end:
                        break
                
                return chunks
            except Exception as e:
                logger.warning(f"Token-based splitting failed: {e}")
        
        # Fallback to character-based splitting
        return self._split_by_chars(content, chunk_size)
    
    def get_token_efficiency(self, text: str) -> float:
        """
        Calculate token efficiency (information density).
        
        Args:
            text: Text to analyze
            
        Returns:
            Efficiency score (higher is better)
        """
        if not text:
            return 0.0
        
        token_count = self.count_tokens(text)
        char_count = len(text)
        
        if token_count == 0:
            return 0.0
        
        # Calculate various efficiency metrics
        chars_per_token = char_count / token_count
        
        # Count meaningful content (letters, numbers, symbols)
        meaningful_chars = len(re.findall(r'[a-zA-Z0-9_\-\+\*\/\=\(\)\[\]\{\}]', text))
        meaningful_ratio = meaningful_chars / char_count if char_count > 0 else 0
        
        # Count code-like patterns
        code_patterns = len(re.findall(r'\b(def|class|function|import|return|if|for|while)\b', text))
        code_density = code_patterns / token_count
        
        # Combine metrics
        efficiency = (chars_per_token * 0.4 + meaningful_ratio * 0.4 + code_density * 0.2)
        
        return min(1.0, efficiency)
    
    def analyze_token_distribution(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze token distribution across multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Analysis results
        """
        if not texts:
            return {}
        
        token_counts = [self.count_tokens(text) for text in texts]
        efficiencies = [self.get_token_efficiency(text) for text in texts]
        
        total_tokens = sum(token_counts)
        avg_tokens = total_tokens / len(texts)
        avg_efficiency = sum(efficiencies) / len(efficiencies)
        
        return {
            "total_texts": len(texts),
            "total_tokens": total_tokens,
            "average_tokens": avg_tokens,
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts),
            "average_efficiency": avg_efficiency,
            "min_efficiency": min(efficiencies),
            "max_efficiency": max(efficiencies),
            "token_distribution": {
                "small": len([c for c in token_counts if c < 100]),
                "medium": len([c for c in token_counts if 100 <= c < 500]),
                "large": len([c for c in token_counts if c >= 500])
            }
        }
    
    def _estimate_tokens(self, text: str) -> int:
        """Fallback token estimation."""
        # Simple estimation: ~4 characters per token for English text
        # Adjust for code which tends to be more token-dense
        
        # Count different types of content
        words = len(text.split())
        chars = len(text)
        
        # Code indicators
        code_chars = len(re.findall(r'[{}()\[\];,.]', text))
        operators = len(re.findall(r'[+\-*/=<>!&|]', text))
        
        # Estimate based on content type
        if code_chars + operators > chars * 0.1:  # Looks like code
            estimated_tokens = chars // 3  # Code is more token-dense
        else:  # Regular text
            estimated_tokens = chars // 4
        
        # Ensure minimum reasonable estimate
        return max(words // 2, estimated_tokens)
    
    def _truncate_by_chars(self, text: str, max_tokens: int) -> str:
        """Fallback character-based truncation."""
        # Estimate character limit based on token limit
        estimated_chars = max_tokens * 4  # Conservative estimate
        
        if len(text) <= estimated_chars:
            return text
        
        # Try to truncate at word boundaries
        truncated = text[:estimated_chars]
        last_space = truncated.rfind(' ')
        
        if last_space > estimated_chars * 0.8:  # If we found a reasonable break point
            return truncated[:last_space]
        else:
            return truncated
    
    def _optimize_structured_content(self, content: str, max_tokens: int) -> str:
        """Optimize structured content while preserving important parts."""
        lines = content.split('\n')
        
        # Prioritize different types of lines
        priority_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            priority = 0
            
            # High priority: function/class definitions, imports
            if re.match(r'^\s*(def|class|import|from)', stripped):
                priority = 3
            # Medium priority: comments, docstrings
            elif re.match(r'^\s*(#|"""|\'\'\'))', stripped):
                priority = 2
            # Low priority: empty lines, simple assignments
            elif not stripped or re.match(r'^\s*\w+\s*=', stripped):
                priority = 1
            else:
                priority = 2  # Default priority
            
            priority_lines.append((priority, i, line))
        
        # Sort by priority (descending) and original order
        priority_lines.sort(key=lambda x: (-x[0], x[1]))
        
        # Add lines until we hit token limit
        selected_lines = []
        current_tokens = 0
        
        for priority, original_index, line in priority_lines:
            line_tokens = self.count_tokens(line + '\n')
            
            if current_tokens + line_tokens <= max_tokens:
                selected_lines.append((original_index, line))
                current_tokens += line_tokens
            else:
                break
        
        # Sort selected lines by original order
        selected_lines.sort(key=lambda x: x[0])
        
        # Reconstruct content
        result_lines = [line for _, line in selected_lines]
        return '\n'.join(result_lines)
    
    def _split_by_chars(self, content: str, chunk_size: int) -> List[str]:
        """Fallback character-based splitting."""
        estimated_chars = chunk_size * 4  # Conservative estimate
        chunks = []
        
        start = 0
        while start < len(content):
            end = min(start + estimated_chars, len(content))
            
            # Try to break at word boundary
            if end < len(content):
                last_space = content.rfind(' ', start, end)
                if last_space > start + estimated_chars * 0.8:
                    end = last_space
            
            chunks.append(content[start:end])
            start = end
        
        return chunks

