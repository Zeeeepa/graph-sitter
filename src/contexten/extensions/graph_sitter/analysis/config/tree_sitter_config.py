"""
Tree-sitter Configuration

Configuration settings for tree-sitter integration and language support.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LanguageConfig:
    """Configuration for a specific programming language."""
    
    name: str
    module_name: str
    file_extensions: List[str]
    enabled: bool = True
    query_timeout_ms: int = 5000
    max_file_size_mb: int = 10


@dataclass
class TreeSitterConfig:
    """Configuration for tree-sitter integration."""
    
    # Language configurations
    languages: Dict[str, LanguageConfig] = field(default_factory=dict)
    
    # Performance settings
    parse_timeout_ms: int = 10000
    query_timeout_ms: int = 5000
    max_file_size_mb: int = 10
    enable_caching: bool = True
    cache_size: int = 1000
    
    # Analysis settings
    enable_error_recovery: bool = True
    skip_binary_files: bool = True
    skip_large_files: bool = True
    
    # Query settings
    enable_query_optimization: bool = True
    max_query_matches: int = 10000
    
    # Debug settings
    debug_mode: bool = False
    log_parse_errors: bool = True
    log_query_performance: bool = False
    
    def __post_init__(self):
        """Initialize default language configurations."""
        if not self.languages:
            self._setup_default_languages()
    
    def _setup_default_languages(self):
        """Setup default language configurations."""
        default_languages = [
            LanguageConfig(
                name='python',
                module_name='tree_sitter_python',
                file_extensions=['.py', '.pyi', '.pyx']
            ),
            LanguageConfig(
                name='javascript',
                module_name='tree_sitter_javascript',
                file_extensions=['.js', '.jsx', '.mjs']
            ),
            LanguageConfig(
                name='typescript',
                module_name='tree_sitter_typescript',
                file_extensions=['.ts', '.tsx', '.d.ts']
            ),
            LanguageConfig(
                name='java',
                module_name='tree_sitter_java',
                file_extensions=['.java']
            ),
            LanguageConfig(
                name='cpp',
                module_name='tree_sitter_cpp',
                file_extensions=['.cpp', '.cc', '.cxx', '.hpp', '.h++']
            ),
            LanguageConfig(
                name='c',
                module_name='tree_sitter_c',
                file_extensions=['.c', '.h']
            ),
            LanguageConfig(
                name='rust',
                module_name='tree_sitter_rust',
                file_extensions=['.rs']
            ),
            LanguageConfig(
                name='go',
                module_name='tree_sitter_go',
                file_extensions=['.go']
            ),
        ]
        
        for lang_config in default_languages:
            self.languages[lang_config.name] = lang_config
    
    def get_language_for_file(self, file_path: Path) -> Optional[str]:
        """
        Get the language name for a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name if found, None otherwise
        """
        extension = file_path.suffix.lower()
        
        for lang_name, lang_config in self.languages.items():
            if lang_config.enabled and extension in lang_config.file_extensions:
                return lang_name
        
        return None
    
    def is_language_enabled(self, language: str) -> bool:
        """Check if a language is enabled."""
        lang_config = self.languages.get(language)
        return lang_config is not None and lang_config.enabled
    
    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions."""
        extensions = []
        for lang_config in self.languages.values():
            if lang_config.enabled:
                extensions.extend(lang_config.file_extensions)
        return list(set(extensions))
    
    def enable_language(self, language: str) -> bool:
        """
        Enable a language.
        
        Args:
            language: Language name to enable
            
        Returns:
            True if successful, False if language not found
        """
        if language in self.languages:
            self.languages[language].enabled = True
            return True
        return False
    
    def disable_language(self, language: str) -> bool:
        """
        Disable a language.
        
        Args:
            language: Language name to disable
            
        Returns:
            True if successful, False if language not found
        """
        if language in self.languages:
            self.languages[language].enabled = False
            return True
        return False
    
    def get_language_config(self, language: str) -> Optional[LanguageConfig]:
        """Get configuration for a specific language."""
        return self.languages.get(language)
    
    def should_skip_file(self, file_path: Path) -> bool:
        """
        Check if a file should be skipped based on configuration.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be skipped
        """
        # Check if file is too large
        if self.skip_large_files and file_path.exists():
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                return True
        
        # Check if file is binary (basic check)
        if self.skip_binary_files and file_path.exists():
            try:
                with open(file_path, 'rb') as f:
                    chunk = f.read(1024)
                    if b'\x00' in chunk:  # Null bytes indicate binary file
                        return True
            except (IOError, OSError):
                return True
        
        return False
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            'languages': {
                name: {
                    'name': config.name,
                    'module_name': config.module_name,
                    'file_extensions': config.file_extensions,
                    'enabled': config.enabled,
                    'query_timeout_ms': config.query_timeout_ms,
                    'max_file_size_mb': config.max_file_size_mb
                }
                for name, config in self.languages.items()
            },
            'parse_timeout_ms': self.parse_timeout_ms,
            'query_timeout_ms': self.query_timeout_ms,
            'max_file_size_mb': self.max_file_size_mb,
            'enable_caching': self.enable_caching,
            'cache_size': self.cache_size,
            'enable_error_recovery': self.enable_error_recovery,
            'skip_binary_files': self.skip_binary_files,
            'skip_large_files': self.skip_large_files,
            'enable_query_optimization': self.enable_query_optimization,
            'max_query_matches': self.max_query_matches,
            'debug_mode': self.debug_mode,
            'log_parse_errors': self.log_parse_errors,
            'log_query_performance': self.log_query_performance
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TreeSitterConfig':
        """Create configuration from dictionary."""
        config = cls()
        
        # Update basic settings
        for key in ['parse_timeout_ms', 'query_timeout_ms', 'max_file_size_mb', 
                   'enable_caching', 'cache_size', 'enable_error_recovery',
                   'skip_binary_files', 'skip_large_files', 'enable_query_optimization',
                   'max_query_matches', 'debug_mode', 'log_parse_errors', 
                   'log_query_performance']:
            if key in data:
                setattr(config, key, data[key])
        
        # Update language configurations
        if 'languages' in data:
            config.languages = {}
            for name, lang_data in data['languages'].items():
                config.languages[name] = LanguageConfig(
                    name=lang_data['name'],
                    module_name=lang_data['module_name'],
                    file_extensions=lang_data['file_extensions'],
                    enabled=lang_data.get('enabled', True),
                    query_timeout_ms=lang_data.get('query_timeout_ms', 5000),
                    max_file_size_mb=lang_data.get('max_file_size_mb', 10)
                )
        
        return config


def create_default_tree_sitter_config() -> TreeSitterConfig:
    """Create a default tree-sitter configuration."""
    return TreeSitterConfig()


def create_performance_optimized_config() -> TreeSitterConfig:
    """Create a performance-optimized tree-sitter configuration."""
    config = TreeSitterConfig()
    config.parse_timeout_ms = 5000
    config.query_timeout_ms = 2000
    config.max_file_size_mb = 5
    config.enable_caching = True
    config.cache_size = 2000
    config.skip_large_files = True
    config.enable_query_optimization = True
    config.max_query_matches = 5000
    return config


def create_debug_config() -> TreeSitterConfig:
    """Create a debug-enabled tree-sitter configuration."""
    config = TreeSitterConfig()
    config.debug_mode = True
    config.log_parse_errors = True
    config.log_query_performance = True
    config.enable_error_recovery = True
    return config

