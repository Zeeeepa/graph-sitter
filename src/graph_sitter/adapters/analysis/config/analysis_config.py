#!/usr/bin/env python3
"""
Enhanced Analysis Configuration

Updated configuration system to support all features from the consolidated analysis system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path


@dataclass
class AnalysisConfig:
    """Enhanced configuration for comprehensive analysis."""
    
    # Core analysis settings
    use_graph_sitter: bool = True
    use_advanced_config: bool = False
    extensions: List[str] = field(default_factory=lambda: ['.py'])
    
    # Quality thresholds
    max_complexity: int = 10
    min_maintainability: int = 20
    confidence_threshold: float = 0.5
    
    # Feature flags
    include_dead_code: bool = False
    include_import_loops: bool = False
    include_training_data: bool = False
    include_enhanced_metrics: bool = False
    include_graph_analysis: bool = False
    
    # Output settings
    output_format: str = "text"  # text, json, yaml
    output_file: Optional[str] = None
    quiet: bool = False
    verbose: bool = False
    
    # Performance settings
    max_files: Optional[int] = None
    timeout_seconds: Optional[int] = None
    parallel_processing: bool = True
    
    # Graph-sitter specific settings
    graph_sitter_config: Dict[str, Any] = field(default_factory=dict)
    
    # Exclusion patterns
    exclude_patterns: List[str] = field(default_factory=lambda: [
        '__pycache__', '.git', '.venv', 'venv', 'env',
        'node_modules', '.pytest_cache', '.mypy_cache'
    ])
    
    # Analysis modes
    analysis_mode: str = "standard"  # standard, comprehensive, quick, training, refactoring
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'use_graph_sitter': self.use_graph_sitter,
            'use_advanced_config': self.use_advanced_config,
            'extensions': self.extensions,
            'max_complexity': self.max_complexity,
            'min_maintainability': self.min_maintainability,
            'confidence_threshold': self.confidence_threshold,
            'include_dead_code': self.include_dead_code,
            'include_import_loops': self.include_import_loops,
            'include_training_data': self.include_training_data,
            'include_enhanced_metrics': self.include_enhanced_metrics,
            'include_graph_analysis': self.include_graph_analysis,
            'output_format': self.output_format,
            'output_file': self.output_file,
            'quiet': self.quiet,
            'verbose': self.verbose,
            'max_files': self.max_files,
            'timeout_seconds': self.timeout_seconds,
            'parallel_processing': self.parallel_processing,
            'graph_sitter_config': self.graph_sitter_config,
            'exclude_patterns': self.exclude_patterns,
            'analysis_mode': self.analysis_mode
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AnalysisConfig':
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'AnalysisConfig':
        """Load configuration from file."""
        import json
        try:
            import yaml
            YAML_AVAILABLE = True
        except ImportError:
            YAML_AVAILABLE = False
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml'] and YAML_AVAILABLE:
                config_dict = yaml.safe_load(f)
            else:
                config_dict = json.load(f)
        
        return cls.from_dict(config_dict)
    
    def save_to_file(self, config_path: str):
        """Save configuration to file."""
        import json
        try:
            import yaml
            YAML_AVAILABLE = True
        except ImportError:
            YAML_AVAILABLE = False
        
        config_path = Path(config_path)
        config_dict = self.to_dict()
        
        with open(config_path, 'w') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml'] and YAML_AVAILABLE:
                yaml.dump(config_dict, f, default_flow_style=False)
            else:
                json.dump(config_dict, f, indent=2)


@dataclass
class PresetConfigs:
    """Predefined configuration presets for common use cases."""
    
    @staticmethod
    def quick_analysis() -> AnalysisConfig:
        """Configuration for quick analysis."""
        return AnalysisConfig(
            analysis_mode="quick",
            include_dead_code=False,
            include_import_loops=False,
            include_training_data=False,
            include_enhanced_metrics=False,
            include_graph_analysis=False
        )
    
    @staticmethod
    def comprehensive_analysis() -> AnalysisConfig:
        """Configuration for comprehensive analysis."""
        return AnalysisConfig(
            analysis_mode="comprehensive",
            include_dead_code=True,
            include_import_loops=True,
            include_training_data=True,
            include_enhanced_metrics=True,
            include_graph_analysis=True,
            use_advanced_config=True
        )
    
    @staticmethod
    def ml_training() -> AnalysisConfig:
        """Configuration for ML training data generation."""
        return AnalysisConfig(
            analysis_mode="training",
            include_training_data=True,
            include_enhanced_metrics=True,
            use_advanced_config=True,
            output_format="json"
        )
    
    @staticmethod
    def refactoring_analysis() -> AnalysisConfig:
        """Configuration for refactoring analysis."""
        return AnalysisConfig(
            analysis_mode="refactoring",
            include_dead_code=True,
            include_import_loops=True,
            include_graph_analysis=True,
            max_complexity=8,  # Stricter complexity threshold
            min_maintainability=30  # Higher maintainability threshold
        )
    
    @staticmethod
    def ci_cd_analysis() -> AnalysisConfig:
        """Configuration for CI/CD pipeline analysis."""
        return AnalysisConfig(
            analysis_mode="standard",
            quiet=True,
            output_format="json",
            max_complexity=15,  # Reasonable for CI/CD
            min_maintainability=20,
            timeout_seconds=300  # 5 minute timeout
        )


def create_default_config() -> AnalysisConfig:
    """Create default analysis configuration."""
    return AnalysisConfig()


def create_config_from_args(args) -> AnalysisConfig:
    """Create configuration from command line arguments."""
    config = AnalysisConfig()
    
    # Update from args
    if hasattr(args, 'no_graph_sitter'):
        config.use_graph_sitter = not args.no_graph_sitter
    if hasattr(args, 'advanced_config'):
        config.use_advanced_config = args.advanced_config
    if hasattr(args, 'extensions'):
        config.extensions = args.extensions
    if hasattr(args, 'max_complexity'):
        config.max_complexity = args.max_complexity
    if hasattr(args, 'min_maintainability'):
        config.min_maintainability = args.min_maintainability
    
    # Feature flags
    if hasattr(args, 'comprehensive') and args.comprehensive:
        config = PresetConfigs.comprehensive_analysis()
    elif hasattr(args, 'quick_analyze') and args.quick_analyze:
        config = PresetConfigs.quick_analysis()
    elif hasattr(args, 'training_data') and args.training_data:
        config = PresetConfigs.ml_training()
    else:
        if hasattr(args, 'dead_code'):
            config.include_dead_code = args.dead_code
        if hasattr(args, 'import_loops'):
            config.include_import_loops = args.import_loops
        if hasattr(args, 'enhanced_metrics'):
            config.include_enhanced_metrics = args.enhanced_metrics
        if hasattr(args, 'graph_analysis'):
            config.include_graph_analysis = args.graph_analysis
    
    # Output settings
    if hasattr(args, 'format'):
        config.output_format = args.format
    if hasattr(args, 'output'):
        config.output_file = args.output
    if hasattr(args, 'quiet'):
        config.quiet = args.quiet
    if hasattr(args, 'verbose'):
        config.verbose = args.verbose
    
    return config

