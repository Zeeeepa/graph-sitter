"""
Code Intelligence Module

Provides real-time code intelligence features including completions,
hover information, and signature help.
"""

from .code_intelligence import CodeIntelligence
from .completions import CompletionProvider
from .hover import HoverProvider
from .signatures import SignatureProvider

__all__ = [
    'CodeIntelligence',
    'CompletionProvider', 
    'HoverProvider',
    'SignatureProvider'
]

