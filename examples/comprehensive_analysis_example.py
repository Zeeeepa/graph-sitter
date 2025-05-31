#!/usr/bin/env python3
"""
Comprehensive Graph-Sitter Analysis Example

This example demonstrates the full capabilities of the Graph-Sitter system
including codebase analysis, database integration, and Codegen API usage.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from graph_sitter_system import CodebaseAnalyzer, GraphBuilder, MetricsCalculator
from graph_sitter_system.utils.config import load_config
from graph_sitter_system.utils.validation import CodeValidator
from graph_sitter_system.integrations.codegen_integration import CodegenIntegration, AnalysisRequest


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('analysis.log')
        ]
    )


async def main():
    """Main analysis workflow"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting comprehensive Graph-Sitter analysis")
    
    try:
        # Load configuration
        config = load_config('config.yaml')  # Optional config file
        logger.info("Configuration loaded successfully")
        
        # Validate Codegen credentials
        if not config.validate_codegen_credentials():
            logger.error("Invalid Codegen credentials")
            return 1
        
        # Initialize components
        analyzer = CodebaseAnalyzer(config)
        validator = CodeValidator(config.analysis.max_file_size_mb)
        codegen = CodegenIntegration(config.codegen)
        
        # Example repository path (change this to your repository)
        repo_path = os.getenv('REPO_PATH', '.')
        
        logger.info(f"Analyzing repository: {repo_path}")
        
        # Step 1: Validate repository structure
        logger.info("Step 1: Validating repository structure")
        validation_results = validator.validate_directory(repo_path, recursive=True)
        validation_summary = validator.get_validation_summary(validation_results)
        
        logger.info(f"Validation complete: {validation_summary['valid_files']}/{validation_summary['total_files']} files valid")
        
        # Step 2: Create analysis task in Codegen
        logger.info("Step 2: Creating analysis task in Codegen")
        analysis_request = AnalysisRequest(
            repository_url=f"file://{os.path.abspath(repo_path)}",
            branch='main',
            analysis_types=['complexity', 'dependencies', 'dead_code', 'security'],
            exclude_patterns=['*.pyc', '__pycache__', '.git', 'node_modules']
        )
        
        task = codegen.create_analysis_task(analysis_request)
        if not task:
            logger.error("Failed to create analysis task")
            return 1
        
        logger.info(f"Created analysis task: {task.id}")
        
        # Step 3: Perform comprehensive analysis
        logger.info("Step 3: Performing comprehensive codebase analysis")
        
        try:
            # Update task status to in progress
            codegen.update_task_status(task.id, 'in_progress')
            
            # Run the analysis
            analysis_result = analyzer.analyze_repository(repo_path)
            
            logger.info(f"Analysis complete:")
            logger.info(f"  Files analyzed: {analysis_result.files_analyzed}")
            logger.info(f"  Symbols found: {analysis_result.symbols_found}")
            logger.info(f"  Dependencies mapped: {analysis_result.dependencies_mapped}")
            logger.info(f"  Dead code detected: {analysis_result.dead_code_detected}")
            logger.info(f"  Complexity score: {analysis_result.complexity_score:.2f}")
            logger.info(f"  Maintainability index: {analysis_result.maintainability_index:.2f}")
            logger.info(f"  Analysis duration: {analysis_result.analysis_duration:.2f}s")
            
            # Step 4: Generate detailed reports
            logger.info("Step 4: Generating detailed reports")
            
            reports = await generate_detailed_reports(analyzer, analysis_result)
            
            # Step 5: Submit results to Codegen
            logger.info("Step 5: Submitting results to Codegen")
            
            results_data = {
                'files_analyzed': analysis_result.files_analyzed,
                'symbols_found': analysis_result.symbols_found,
                'dependencies_mapped': analysis_result.dependencies_mapped,
                'dead_code_detected': analysis_result.dead_code_detected,
                'complexity_score': analysis_result.complexity_score,
                'maintainability_index': analysis_result.maintainability_index,
                'analysis_duration': analysis_result.analysis_duration,
                'validation_summary': validation_summary,
                'reports': reports,
                'errors': analysis_result.errors,
                'warnings': analysis_result.warnings
            }
            
            success = codegen.submit_analysis_results(task.id, results_data)
            if success:
                codegen.update_task_status(task.id, 'completed', results_data)
                logger.info("Results submitted successfully")
            else:
                codegen.update_task_status(task.id, 'failed')
                logger.error("Failed to submit results")
            
            # Step 6: Generate recommendations
            logger.info("Step 6: Generating recommendations")
            recommendations = generate_recommendations(analysis_result, validation_summary)
            
            for recommendation in recommendations:
                logger.info(f"Recommendation: {recommendation}")
            
            logger.info("Comprehensive analysis completed successfully")
            return 0
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            codegen.update_task_status(task.id, 'failed')
            return 1
            
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        return 1


async def generate_detailed_reports(analyzer: CodebaseAnalyzer, result) -> dict:
    """Generate detailed analysis reports"""
    logger = logging.getLogger(__name__)
    
    reports = {}
    
    try:
        # Complexity report
        logger.info("Generating complexity report")
        reports['complexity'] = {
            'high_complexity_files': [],  # Would be populated from database queries
            'complexity_distribution': {},
            'complexity_trends': {}
        }
        
        # Dependency report
        logger.info("Generating dependency report")
        reports['dependencies'] = {
            'circular_dependencies': [],
            'dependency_depth': {},
            'external_dependencies': [],
            'dependency_graph_metrics': {}
        }
        
        # Dead code report
        logger.info("Generating dead code report")
        reports['dead_code'] = {
            'unused_functions': [],
            'unreachable_code': [],
            'unused_imports': [],
            'potential_savings': 0
        }
        
        # Security report
        logger.info("Generating security report")
        reports['security'] = {
            'vulnerabilities': [],
            'security_hotspots': [],
            'compliance_issues': []
        }
        
        # Quality report
        logger.info("Generating quality report")
        reports['quality'] = {
            'maintainability_score': result.maintainability_index,
            'test_coverage': 0,  # Would be calculated
            'documentation_coverage': 0,  # Would be calculated
            'code_duplication': 0  # Would be calculated
        }
        
    except Exception as e:
        logger.error(f"Error generating reports: {str(e)}")
    
    return reports


def generate_recommendations(analysis_result, validation_summary) -> list:
    """Generate actionable recommendations based on analysis results"""
    recommendations = []
    
    # Complexity recommendations
    if analysis_result.complexity_score > 20:
        recommendations.append(
            f"High complexity detected (score: {analysis_result.complexity_score:.1f}). "
            "Consider refactoring complex functions and breaking them into smaller units."
        )
    
    # Maintainability recommendations
    if analysis_result.maintainability_index < 50:
        recommendations.append(
            f"Low maintainability index ({analysis_result.maintainability_index:.1f}). "
            "Focus on improving code documentation, reducing complexity, and adding tests."
        )
    
    # Dead code recommendations
    if analysis_result.dead_code_detected > 0:
        recommendations.append(
            f"Found {analysis_result.dead_code_detected} instances of dead code. "
            "Remove unused functions, variables, and imports to improve codebase cleanliness."
        )
    
    # Validation recommendations
    if validation_summary['validation_rate'] < 0.9:
        recommendations.append(
            f"Only {validation_summary['validation_rate']:.1%} of files passed validation. "
            "Fix syntax errors and encoding issues in failing files."
        )
    
    # File size recommendations
    avg_file_size = validation_summary.get('avg_file_size_kb', 0)
    if avg_file_size > 100:
        recommendations.append(
            f"Average file size is {avg_file_size:.1f}KB. "
            "Consider breaking large files into smaller, more focused modules."
        )
    
    # Language diversity recommendations
    languages = validation_summary.get('languages', {})
    if len(languages) > 5:
        recommendations.append(
            f"Repository uses {len(languages)} different languages. "
            "Consider standardizing on fewer languages to reduce complexity."
        )
    
    return recommendations


def print_usage():
    """Print usage information"""
    print("""
Graph-Sitter Comprehensive Analysis Example

Usage:
    python comprehensive_analysis_example.py

Environment Variables:
    REPO_PATH                 - Path to repository to analyze (default: current directory)
    GRAPH_SITTER_CODEGEN_ORG_ID    - Codegen organization ID (required)
    GRAPH_SITTER_CODEGEN_TOKEN     - Codegen API token (required)
    GRAPH_SITTER_DATABASE_URL      - Database connection URL
    GRAPH_SITTER_MAX_WORKERS       - Maximum worker threads for analysis

Configuration File:
    You can also provide a config.yaml file with the following structure:
    
    database:
      url: postgresql://localhost:5432/graph_sitter
      max_connections: 20
    
    codegen:
      org_id: your-org-id
      token: your-token
      api_url: https://api.codegen.com
    
    analysis:
      max_workers: 4
      max_file_size_mb: 10
      complexity_threshold: 20
    
    cache:
      enabled: true
      cache_dir: /tmp/graph_sitter_cache
    
    logging:
      level: INFO
      file_path: analysis.log

Example:
    export GRAPH_SITTER_CODEGEN_ORG_ID="your-org-id"
    export GRAPH_SITTER_CODEGEN_TOKEN="your-token"
    export REPO_PATH="/path/to/your/repository"
    python comprehensive_analysis_example.py
    """)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_usage()
        sys.exit(0)
    
    # Check for required environment variables
    if not os.getenv('GRAPH_SITTER_CODEGEN_ORG_ID'):
        print("Error: GRAPH_SITTER_CODEGEN_ORG_ID environment variable is required")
        print("Run with --help for usage information")
        sys.exit(1)
    
    if not os.getenv('GRAPH_SITTER_CODEGEN_TOKEN'):
        print("Error: GRAPH_SITTER_CODEGEN_TOKEN environment variable is required")
        print("Run with --help for usage information")
        sys.exit(1)
    
    # Run the main analysis
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

