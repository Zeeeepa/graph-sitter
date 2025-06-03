"""
Relevance scoring for context items.

This module provides intelligent relevance scoring to determine which
context items are most relevant for a given code generation prompt.
"""

import re
import logging
from typing import Dict, List, Set, Optional
import asyncio
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Weights for different scoring factors."""
    keyword_match: float = 0.3
    semantic_similarity: float = 0.25
    type_relevance: float = 0.2
    structural_importance: float = 0.15
    recency: float = 0.1


class RelevanceScorer:
    """
    Intelligent relevance scorer for context items.
    
    Uses multiple scoring factors to determine relevance:
    - Keyword matching
    - Semantic similarity (simplified)
    - Type-based relevance
    - Structural importance
    - Recency factors
    """
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        """
        Initialize relevance scorer.
        
        Args:
            weights: Custom scoring weights
        """
        self.weights = weights or ScoringWeights()
        
        # Common programming keywords and patterns
        self.programming_keywords = {
            'function', 'class', 'method', 'variable', 'import', 'export',
            'async', 'await', 'return', 'if', 'else', 'for', 'while',
            'try', 'catch', 'throw', 'error', 'exception', 'test', 'mock',
            'api', 'endpoint', 'route', 'handler', 'middleware', 'service',
            'model', 'view', 'controller', 'component', 'module', 'package',
            'database', 'query', 'schema', 'migration', 'config', 'settings'
        }
        
        # Type importance hierarchy
        self.type_importance = {
            'codebase': 0.9,
            'class': 0.8,
            'function': 0.7,
            'file': 0.6,
            'symbol': 0.5,
            'additional': 0.4
        }
    
    async def initialize(self) -> None:
        """Initialize the relevance scorer."""
        logger.info("Relevance scorer initialized")
    
    async def score_relevance(self,
                            prompt: str,
                            content: str,
                            content_type: str) -> float:
        """
        Score the relevance of content to a prompt.
        
        Args:
            prompt: The code generation prompt
            content: Content to score
            content_type: Type of content (class, function, etc.)
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        try:
            # Calculate individual scores
            keyword_score = self._calculate_keyword_score(prompt, content)
            semantic_score = self._calculate_semantic_score(prompt, content)
            type_score = self._calculate_type_score(content_type, prompt)
            structural_score = self._calculate_structural_score(content, content_type)
            
            # Weighted combination
            total_score = (
                keyword_score * self.weights.keyword_match +
                semantic_score * self.weights.semantic_similarity +
                type_score * self.weights.type_relevance +
                structural_score * self.weights.structural_importance
            )
            
            # Ensure score is between 0 and 1
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            logger.warning(f"Error scoring relevance: {e}")
            return 0.0
    
    def _calculate_keyword_score(self, prompt: str, content: str) -> float:
        """Calculate keyword matching score."""
        prompt_words = self._extract_keywords(prompt.lower())
        content_words = self._extract_keywords(content.lower())
        
        if not prompt_words:
            return 0.0
        
        # Calculate intersection
        common_words = prompt_words.intersection(content_words)
        
        # Base score from common words
        base_score = len(common_words) / len(prompt_words)
        
        # Boost for exact phrase matches
        phrase_boost = self._calculate_phrase_matches(prompt.lower(), content.lower())
        
        # Boost for programming-specific keywords
        programming_boost = len(common_words.intersection(self.programming_keywords)) * 0.1
        
        return min(1.0, base_score + phrase_boost + programming_boost)
    
    def _calculate_semantic_score(self, prompt: str, content: str) -> float:
        """Calculate semantic similarity score (simplified)."""
        # Simplified semantic scoring based on context patterns
        
        # Check for similar code patterns
        pattern_score = 0.0
        
        # Function/method patterns
        if any(word in prompt.lower() for word in ['function', 'method', 'def']):
            if any(word in content.lower() for word in ['def ', 'function ', 'method']):
                pattern_score += 0.3
        
        # Class patterns
        if any(word in prompt.lower() for word in ['class', 'object', 'instance']):
            if any(word in content.lower() for word in ['class ', 'extends', 'implements']):
                pattern_score += 0.3
        
        # API/endpoint patterns
        if any(word in prompt.lower() for word in ['api', 'endpoint', 'route', 'handler']):
            if any(word in content.lower() for word in ['@app.', '@router.', 'endpoint', 'route']):
                pattern_score += 0.3
        
        # Test patterns
        if any(word in prompt.lower() for word in ['test', 'spec', 'mock']):
            if any(word in content.lower() for word in ['test_', 'spec_', 'mock', 'assert']):
                pattern_score += 0.3
        
        # Database patterns
        if any(word in prompt.lower() for word in ['database', 'db', 'query', 'sql']):
            if any(word in content.lower() for word in ['query', 'select', 'insert', 'update', 'delete']):
                pattern_score += 0.3
        
        return min(1.0, pattern_score)
    
    def _calculate_type_score(self, content_type: str, prompt: str) -> float:
        """Calculate type-based relevance score."""
        base_importance = self.type_importance.get(content_type, 0.5)
        
        # Adjust based on prompt content
        type_boost = 0.0
        
        prompt_lower = prompt.lower()
        
        # Boost class content for class-related prompts
        if content_type == 'class' and any(word in prompt_lower for word in ['class', 'object', 'inheritance']):
            type_boost += 0.2
        
        # Boost function content for function-related prompts
        if content_type == 'function' and any(word in prompt_lower for word in ['function', 'method', 'def']):
            type_boost += 0.2
        
        # Boost file content for file-related prompts
        if content_type == 'file' and any(word in prompt_lower for word in ['file', 'module', 'import']):
            type_boost += 0.2
        
        # Boost codebase content for architectural prompts
        if content_type == 'codebase' and any(word in prompt_lower for word in ['architecture', 'structure', 'overview']):
            type_boost += 0.2
        
        return min(1.0, base_importance + type_boost)
    
    def _calculate_structural_score(self, content: str, content_type: str) -> float:
        """Calculate structural importance score."""
        # Base score from content length and complexity
        content_length = len(content)
        
        # Normalize length score (longer content is generally more important, up to a point)
        length_score = min(0.5, content_length / 2000)
        
        # Count structural indicators
        structural_indicators = 0
        
        # Function/method definitions
        structural_indicators += len(re.findall(r'\bdef\s+\w+', content))
        structural_indicators += len(re.findall(r'\bfunction\s+\w+', content))
        structural_indicators += len(re.findall(r'\w+\s*\([^)]*\)\s*{', content))
        
        # Class definitions
        structural_indicators += len(re.findall(r'\bclass\s+\w+', content))
        
        # Import statements
        structural_indicators += len(re.findall(r'\bimport\s+', content))
        structural_indicators += len(re.findall(r'\bfrom\s+\w+\s+import', content))
        
        # Comments and documentation
        structural_indicators += len(re.findall(r'#.*|//.*|/\*.*?\*/', content))
        structural_indicators += len(re.findall(r'""".*?"""|\'\'\'.*?\'\'\'', content, re.DOTALL))
        
        # Normalize structural score
        structural_score = min(0.5, structural_indicators / 20)
        
        return length_score + structural_score
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their'
        }
        
        # Extract words (alphanumeric + underscore)
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
        
        # Filter out stop words and short words
        keywords = {
            word.lower() for word in words
            if len(word) > 2 and word.lower() not in stop_words
        }
        
        return keywords
    
    def _calculate_phrase_matches(self, prompt: str, content: str) -> float:
        """Calculate boost for exact phrase matches."""
        # Extract phrases (2-4 words)
        prompt_phrases = self._extract_phrases(prompt)
        content_phrases = self._extract_phrases(content)
        
        if not prompt_phrases:
            return 0.0
        
        common_phrases = prompt_phrases.intersection(content_phrases)
        phrase_score = len(common_phrases) / len(prompt_phrases)
        
        return min(0.3, phrase_score)  # Cap at 0.3 boost
    
    def _extract_phrases(self, text: str) -> Set[str]:
        """Extract meaningful phrases from text."""
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
        phrases = set()
        
        # Extract 2-4 word phrases
        for i in range(len(words) - 1):
            for length in [2, 3, 4]:
                if i + length <= len(words):
                    phrase = ' '.join(words[i:i+length]).lower()
                    if len(phrase) > 6:  # Minimum phrase length
                        phrases.add(phrase)
        
        return phrases
    
    def get_scoring_explanation(self,
                              prompt: str,
                              content: str,
                              content_type: str) -> Dict[str, float]:
        """Get detailed scoring breakdown for debugging."""
        keyword_score = self._calculate_keyword_score(prompt, content)
        semantic_score = self._calculate_semantic_score(prompt, content)
        type_score = self._calculate_type_score(content_type, prompt)
        structural_score = self._calculate_structural_score(content, content_type)
        
        total_score = (
            keyword_score * self.weights.keyword_match +
            semantic_score * self.weights.semantic_similarity +
            type_score * self.weights.type_relevance +
            structural_score * self.weights.structural_importance
        )
        
        return {
            'keyword_score': keyword_score,
            'semantic_score': semantic_score,
            'type_score': type_score,
            'structural_score': structural_score,
            'total_score': max(0.0, min(1.0, total_score)),
            'weights': {
                'keyword_match': self.weights.keyword_match,
                'semantic_similarity': self.weights.semantic_similarity,
                'type_relevance': self.weights.type_relevance,
                'structural_importance': self.weights.structural_importance
            }
        }

