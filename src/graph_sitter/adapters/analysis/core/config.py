"""
Analysis Configuration and Result Models

Defines configuration options and result structures for the analysis system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
import json


@dataclass
class AnalysisConfig:
    """Configuration for codebase analysis."""
    
    # Core analysis options
    use_graph_sitter: bool = True
    extensions: List[str] = field(default_factory=lambda: ['.py'])
    exclude_patterns: List[str] = field(default_factory=lambda: ['__pycache__', '.git', 'node_modules', '.venv'])
    
    # Analysis features
    enable_quality_metrics: bool = True
    enable_complexity_analysis: bool = True
    enable_pattern_detection: bool = True
    enable_dead_code_detection: bool = True
    enable_import_loop_detection: bool = True
    enable_ai_analysis: bool = False
    
    # Visualization options
    generate_visualizations: bool = False
    export_html: bool = False
    export_json: bool = True
    
    # Performance options
    max_file_size: int = 1024 * 1024  # 1MB
    parallel_processing: bool = True
    max_workers: int = 4
    
    # AI analysis options
    ai_api_key: Optional[str] = None
    ai_model: str = "gpt-3.5-turbo"
    max_ai_requests: int = 100
    
    # Output options
    output_dir: Optional[str] = None
    verbose: bool = False
    include_source: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'use_graph_sitter': self.use_graph_sitter,
            'extensions': self.extensions,
            'exclude_patterns': self.exclude_patterns,
            'enable_quality_metrics': self.enable_quality_metrics,
            'enable_complexity_analysis': self.enable_complexity_analysis,
            'enable_pattern_detection': self.enable_pattern_detection,
            'enable_dead_code_detection': self.enable_dead_code_detection,
            'enable_import_loop_detection': self.enable_import_loop_detection,
            'enable_ai_analysis': self.enable_ai_analysis,
            'generate_visualizations': self.generate_visualizations,
            'export_html': self.export_html,
            'export_json': self.export_json,
            'max_file_size': self.max_file_size,
            'parallel_processing': self.parallel_processing,
            'max_workers': self.max_workers,
            'ai_model': self.ai_model,
            'max_ai_requests': self.max_ai_requests,
            'output_dir': self.output_dir,
            'verbose': self.verbose,
            'include_source': self.include_source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisConfig':
        """Create configuration from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
    
    @classmethod
    def from_file(cls, filepath: str) -> 'AnalysisConfig':
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def save_to_file(self, filepath: str):
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


@dataclass
class AnalysisResult:
    """Complete analysis result containing all analysis data."""
    
    # Basic result info
    success: bool
    codebase_path: str = ""
    analysis_time: float = 0.0
    error: Optional[str] = None
    
    # Core analysis results
    file_analyses: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    # Metrics and quality analysis
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    complexity_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Advanced analysis results
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    dead_code: List[Dict[str, Any]] = field(default_factory=list)
    import_loops: List[Dict[str, Any]] = field(default_factory=list)
    
    # AI and visualization
    ai_insights: Dict[str, Any] = field(default_factory=dict)
    visualization_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    config: Optional[AnalysisConfig] = None
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        result = {
            'success': self.success,
            'codebase_path': self.codebase_path,
            'analysis_time': self.analysis_time,
            'timestamp': self.timestamp,
            'summary': self.summary,
            'quality_metrics': self.quality_metrics,
            'complexity_metrics': self.complexity_metrics,
            'patterns': self.patterns,
            'dead_code': self.dead_code,
            'import_loops': self.import_loops,
            'ai_insights': self.ai_insights,
            'visualization_data': self.visualization_data,
            'file_analyses': self.file_analyses
        }
        
        if self.error:
            result['error'] = self.error
            
        if self.config:
            result['config'] = self.config.to_dict()
            
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def save_to_file(self, filepath: str):
        """Save result to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create result from dictionary."""
        config_data = data.pop('config', None)
        config = AnalysisConfig.from_dict(config_data) if config_data else None
        
        return cls(
            config=config,
            **{k: v for k, v in data.items() if hasattr(cls, k)}
        )
    
    @classmethod
    def from_file(cls, filepath: str) -> 'AnalysisResult':
        """Load result from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get high-level summary statistics."""
        return {
            'success': self.success,
            'analysis_time': f"{self.analysis_time:.2f}s",
            'total_files': self.summary.get('total_files', 0),
            'total_functions': self.summary.get('total_functions', 0),
            'total_classes': self.summary.get('total_classes', 0),
            'average_complexity': f"{self.summary.get('average_complexity', 0):.2f}",
            'maintainability_score': f"{self.summary.get('maintainability_score', 0):.1f}%",
            'issues_found': len(self.patterns) + len(self.dead_code) + len(self.import_loops),
            'graph_sitter_enabled': self.summary.get('graph_sitter_enabled', False)
        }
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality metrics summary."""
        return {
            'maintainability_score': self.quality_metrics.get('maintainability_score', 0),
            'code_coverage': self.quality_metrics.get('code_coverage', 0),
            'documentation_coverage': self.quality_metrics.get('documentation_coverage', 0),
            'test_coverage': self.quality_metrics.get('test_coverage', 0),
            'technical_debt_ratio': self.quality_metrics.get('technical_debt_ratio', 0)
        }
    
    def get_complexity_summary(self) -> Dict[str, Any]:
        """Get complexity metrics summary."""
        return {
            'max_complexity': self.complexity_metrics.get('max_complexity', 0),
            'average_complexity': self.complexity_metrics.get('average_complexity', 0),
            'complexity_distribution': self.complexity_metrics.get('complexity_distribution', {}),
            'high_complexity_functions': len([
                f for f in self.file_analyses.values() 
                for func in f.get('functions', []) 
                if func.get('complexity', 0) > 10
            ])
        }
    
    def get_issues_summary(self) -> Dict[str, Any]:
        """Get issues and problems summary."""
        return {
            'total_issues': len(self.patterns) + len(self.dead_code) + len(self.import_loops),
            'pattern_issues': len(self.patterns),
            'dead_code_items': len(self.dead_code),
            'import_loops': len(self.import_loops),
            'critical_issues': len([
                p for p in self.patterns 
                if p.get('severity', '').lower() == 'critical'
            ]),
            'major_issues': len([
                p for p in self.patterns 
                if p.get('severity', '').lower() == 'major'
            ])
        }
    
    def print_summary(self):
        """Print a formatted summary of the analysis results."""
        print("🔍 CODEBASE ANALYSIS SUMMARY")
        print("=" * 50)
        
        stats = self.get_summary_stats()
        print(f"✅ Analysis Status: {'Success' if stats['success'] else 'Failed'}")
        print(f"⏱️  Analysis Time: {stats['analysis_time']}")
        print(f"📁 Total Files: {stats['total_files']}")
        print(f"⚡ Total Functions: {stats['total_functions']}")
        print(f"🏗️  Total Classes: {stats['total_classes']}")
        print(f"🔢 Average Complexity: {stats['average_complexity']}")
        print(f"📊 Maintainability: {stats['maintainability_score']}")
        print(f"⚠️  Issues Found: {stats['issues_found']}")
        print(f"🔧 Graph-sitter: {'Enabled' if stats['graph_sitter_enabled'] else 'Disabled'}")
        
        if self.error:
            print(f"\n❌ Error: {self.error}")
        
        # Quality summary
        quality = self.get_quality_summary()
        if any(quality.values()):
            print(f"\n📈 QUALITY METRICS")
            print("-" * 30)
            for metric, value in quality.items():
                if value > 0:
                    print(f"{metric.replace('_', ' ').title()}: {value:.1f}%")
        
        # Issues summary
        issues = self.get_issues_summary()
        if issues['total_issues'] > 0:
            print(f"\n⚠️  ISSUES DETECTED")
            print("-" * 30)
            print(f"Pattern Issues: {issues['pattern_issues']}")
            print(f"Dead Code Items: {issues['dead_code_items']}")
            print(f"Import Loops: {issues['import_loops']}")
            print(f"Critical Issues: {issues['critical_issues']}")
            print(f"Major Issues: {issues['major_issues']}")


# Predefined configuration presets
class AnalysisPresets:
    """Predefined analysis configuration presets."""
    
    @staticmethod
    def basic() -> AnalysisConfig:
        """Basic analysis configuration."""
        return AnalysisConfig(
            enable_ai_analysis=False,
            generate_visualizations=False,
            enable_pattern_detection=False
        )
    
    @staticmethod
    def comprehensive() -> AnalysisConfig:
        """Comprehensive analysis configuration."""
        return AnalysisConfig(
            enable_ai_analysis=False,  # Requires API key
            generate_visualizations=True,
            enable_pattern_detection=True,
            enable_dead_code_detection=True,
            enable_import_loop_detection=True,
            export_html=True
        )
    
    @staticmethod
    def quality_focused() -> AnalysisConfig:
        """Quality-focused analysis configuration."""
        return AnalysisConfig(
            enable_quality_metrics=True,
            enable_complexity_analysis=True,
            enable_pattern_detection=True,
            enable_dead_code_detection=True,
            enable_ai_analysis=False,
            generate_visualizations=False
        )
    
    @staticmethod
    def performance_optimized() -> AnalysisConfig:
        """Performance-optimized configuration for large codebases."""
        return AnalysisConfig(
            parallel_processing=True,
            max_workers=8,
            enable_ai_analysis=False,
            generate_visualizations=False,
            include_source=False
        )
    
    @staticmethod
    def ai_enhanced() -> AnalysisConfig:
        """AI-enhanced analysis configuration."""
        return AnalysisConfig(
            enable_ai_analysis=True,
            enable_pattern_detection=True,
            generate_visualizations=True,
            max_ai_requests=200
        )

