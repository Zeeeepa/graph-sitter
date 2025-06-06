"""
🎛️ ENHANCED CONFIGURATION MODULE 🎛️

Advanced configuration system with CodebaseConfig integration, custom pipelines,
and feature toggles based on graph-sitter.com advanced settings.

Features:
- Advanced CodebaseConfig usage with all flags
- Custom analysis pipelines
- Feature toggles and conditional analysis
- Environment-specific configurations
- Configuration validation and optimization
- Dynamic configuration updates
- Configuration templates and presets
"""

from .advanced_config import (
    AdvancedCodebaseConfig,
    create_optimized_config,
    create_debug_config,
    create_production_config
)

from .pipeline_config import (
    AnalysisPipeline,
    PipelineStage,
    create_custom_pipeline,
    create_quality_pipeline,
    create_security_pipeline
)

from .feature_toggles import (
    FeatureToggle,
    FeatureManager,
    create_feature_manager
)

from .config_templates import (
    ConfigTemplate,
    load_config_template,
    save_config_template,
    get_builtin_templates
)

__all__ = [
    # Advanced config
    'AdvancedCodebaseConfig',
    'create_optimized_config',
    'create_debug_config',
    'create_production_config',
    
    # Pipeline config
    'AnalysisPipeline',
    'PipelineStage',
    'create_custom_pipeline',
    'create_quality_pipeline',
    'create_security_pipeline',
    
    # Feature toggles
    'FeatureToggle',
    'FeatureManager',
    'create_feature_manager',
    
    # Config templates
    'ConfigTemplate',
    'load_config_template',
    'save_config_template',
    'get_builtin_templates'
]

