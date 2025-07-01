"""
Graph-Sitter Integration Layer
Provides seamless integration between Graph-Sitter codebase analysis and the analysis framework
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import asyncpg
from graph_sitter import Codebase
from graph_sitter.core.codebase import Codebase as GraphSitterCodebase

from .database_manager import DatabaseManager
from .analysis_executor import AnalysisExecutor
from .codegen_integration import CodegenIntegration

logger = logging.getLogger(__name__)


class GraphSitterIntegration:
    """
    Main integration class that orchestrates Graph-Sitter analysis with the framework
    """
    
    def __init__(
        self,
        database_url: str,
        codegen_api_key: Optional[str] = None,
        codegen_org_id: Optional[str] = None
    ):
        self.db_manager = DatabaseManager(database_url)
        self.analysis_executor = AnalysisExecutor(self.db_manager)
        self.codegen_integration = CodegenIntegration(
            api_key=codegen_api_key,
            org_id=codegen_org_id
        ) if codegen_api_key else None
        
    async def initialize(self):
        """Initialize the integration layer"""
        await self.db_manager.initialize()
        logger.info("Graph-Sitter integration layer initialized")
    
    async def analyze_repository(
        self,
        repo_path_or_url: str,
        analysis_types: Optional[List[str]] = None,
        language: Optional[str] = None,
        branch: str = "main",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a repository
        
        Args:
            repo_path_or_url: Local path or GitHub URL
            analysis_types: List of analysis types to run (default: all)
            language: Programming language override
            branch: Git branch to analyze
            config: Additional configuration options
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        start_time = time.time()
        
        try:
            # Create or get repository record
            repo_id = await self._setup_repository(repo_path_or_url, branch, config)
            
            # Initialize Graph-Sitter codebase
            codebase = await self._create_codebase(repo_path_or_url, language, branch)
            
            # Extract and store codebase structure
            await self._extract_codebase_structure(codebase, repo_id, branch)
            
            # Run analyses
            analysis_results = await self._run_analyses(
                codebase, repo_id, analysis_types or self._get_default_analyses()
            )
            
            # Update repository status
            await self._update_repository_status(repo_id, "completed")
            
            execution_time = time.time() - start_time
            
            return {
                "repository_id": str(repo_id),
                "status": "completed",
                "execution_time_seconds": execution_time,
                "analysis_results": analysis_results,
                "codebase_summary": await self._get_codebase_summary(repo_id),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analysis failed for {repo_path_or_url}: {str(e)}")
            if 'repo_id' in locals():
                await self._update_repository_status(repo_id, "failed", str(e))
            raise
    
    async def _setup_repository(
        self, 
        repo_path_or_url: str, 
        branch: str, 
        config: Optional[Dict[str, Any]]
    ) -> UUID:
        """Create or update repository record in database"""
        
        # Determine if this is a local path or URL
        if repo_path_or_url.startswith(('http://', 'https://', 'git@')):
            # Extract repo name from URL
            repo_name = repo_path_or_url.split('/')[-1].replace('.git', '')
            full_name = '/'.join(repo_path_or_url.split('/')[-2:]).replace('.git', '')
            url = repo_path_or_url
        else:
            # Local path
            path = Path(repo_path_or_url)
            repo_name = path.name
            full_name = f"local/{repo_name}"
            url = f"file://{path.absolute()}"
        
        # Check if repository already exists
        async with self.db_manager.get_connection() as conn:
            existing_repo = await conn.fetchrow(
                "SELECT id FROM repositories WHERE full_name = $1",
                full_name
            )
            
            if existing_repo:
                repo_id = existing_repo['id']
                # Update last analyzed timestamp and status
                await conn.execute(
                    """
                    UPDATE repositories 
                    SET last_analyzed_at = NOW(), analysis_status = 'analyzing',
                        configuration = $2
                    WHERE id = $1
                    """,
                    repo_id, json.dumps(config or {})
                )
            else:
                # Create new repository record
                repo_id = await conn.fetchval(
                    """
                    INSERT INTO repositories (
                        name, full_name, url, default_branch, analysis_status, configuration
                    ) VALUES ($1, $2, $3, $4, 'analyzing', $5)
                    RETURNING id
                    """,
                    repo_name, full_name, url, branch, json.dumps(config or {})
                )
        
        return repo_id
    
    async def _create_codebase(
        self, 
        repo_path_or_url: str, 
        language: Optional[str], 
        branch: str
    ) -> GraphSitterCodebase:
        """Create Graph-Sitter codebase instance"""
        
        if repo_path_or_url.startswith(('http://', 'https://', 'git@')):
            # Remote repository
            codebase = Codebase.from_repo(
                repo_path_or_url,
                language=language,
                commit=branch if branch != "main" else None
            )
        else:
            # Local repository
            codebase = Codebase(
                repo_path_or_url,
                language=language
            )
        
        return codebase
    
    async def _extract_codebase_structure(
        self, 
        codebase: GraphSitterCodebase, 
        repo_id: UUID, 
        branch: str
    ):
        """Extract and store codebase structure in database"""
        
        async with self.db_manager.get_connection() as conn:
            # Store files
            for file in codebase.files:
                file_id = await conn.fetchval(
                    """
                    INSERT INTO files (
                        repository_id, branch_name, file_path, file_name, 
                        file_extension, language, size_bytes, line_count,
                        content_hash, is_binary, is_test, is_documentation
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (repository_id, branch_name, file_path) 
                    DO UPDATE SET 
                        size_bytes = EXCLUDED.size_bytes,
                        line_count = EXCLUDED.line_count,
                        content_hash = EXCLUDED.content_hash,
                        updated_at = NOW()
                    RETURNING id
                    """,
                    repo_id, branch, file.filepath, file.filename,
                    file.extension, file.language, len(file.source.encode('utf-8')),
                    len(file.source.splitlines()), 
                    self._calculate_content_hash(file.source),
                    False,  # is_binary - Graph-Sitter typically handles text files
                    'test' in file.filepath.lower(),
                    any(doc in file.filepath.lower() for doc in ['readme', 'doc', 'docs'])
                )
                
                # Store symbols
                await self._store_symbols(conn, file, file_id)
                
                # Store imports
                await self._store_imports(conn, file, file_id)
    
    async def _store_symbols(self, conn, file, file_id: UUID):
        """Store symbols (functions, classes, etc.) from a file"""
        
        # Store functions
        for func in file.functions:
            symbol_id = await conn.fetchval(
                """
                INSERT INTO symbols (
                    file_id, symbol_type, name, qualified_name, signature,
                    start_line, end_line, visibility, is_static, is_async,
                    return_type, parameters, docstring, complexity_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (file_id, symbol_type, name, start_line) 
                DO UPDATE SET 
                    signature = EXCLUDED.signature,
                    complexity_score = EXCLUDED.complexity_score,
                    updated_at = NOW()
                RETURNING id
                """,
                file_id, 'function', func.name, func.qualified_name,
                getattr(func, 'signature', ''), func.start_line, func.end_line,
                getattr(func, 'visibility', 'public'), 
                getattr(func, 'is_static', False),
                getattr(func, 'is_async', False),
                getattr(func, 'return_type', None),
                json.dumps(getattr(func, 'parameters', [])),
                getattr(func, 'docstring', None),
                getattr(func, 'complexity_score', None)
            )
        
        # Store classes
        for cls in file.classes:
            class_id = await conn.fetchval(
                """
                INSERT INTO symbols (
                    file_id, symbol_type, name, qualified_name, signature,
                    start_line, end_line, visibility, is_abstract,
                    docstring
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (file_id, symbol_type, name, start_line) 
                DO UPDATE SET 
                    signature = EXCLUDED.signature,
                    updated_at = NOW()
                RETURNING id
                """,
                file_id, 'class', cls.name, cls.qualified_name,
                getattr(cls, 'signature', ''), cls.start_line, cls.end_line,
                getattr(cls, 'visibility', 'public'),
                getattr(cls, 'is_abstract', False),
                getattr(cls, 'docstring', None)
            )
            
            # Store class methods
            for method in getattr(cls, 'methods', []):
                await conn.execute(
                    """
                    INSERT INTO symbols (
                        file_id, symbol_type, name, qualified_name, signature,
                        start_line, end_line, parent_symbol_id, visibility,
                        is_static, is_async, return_type, parameters, docstring,
                        complexity_score
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (file_id, symbol_type, name, start_line) 
                    DO UPDATE SET 
                        complexity_score = EXCLUDED.complexity_score,
                        updated_at = NOW()
                    """,
                    file_id, 'method', method.name, method.qualified_name,
                    getattr(method, 'signature', ''), method.start_line, method.end_line,
                    class_id, getattr(method, 'visibility', 'public'),
                    getattr(method, 'is_static', False),
                    getattr(method, 'is_async', False),
                    getattr(method, 'return_type', None),
                    json.dumps(getattr(method, 'parameters', [])),
                    getattr(method, 'docstring', None),
                    getattr(method, 'complexity_score', None)
                )
    
    async def _store_imports(self, conn, file, file_id: UUID):
        """Store import statements from a file"""
        
        for imp in getattr(file, 'imports', []):
            await conn.execute(
                """
                INSERT INTO imports (
                    file_id, import_type, import_path, import_name,
                    alias_name, is_relative, is_wildcard, line_number,
                    is_external, package_name
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (file_id, import_path, import_name) 
                DO NOTHING
                """,
                file_id, getattr(imp, 'import_type', 'module'),
                imp.module_path, getattr(imp, 'name', None),
                getattr(imp, 'alias', None), getattr(imp, 'is_relative', False),
                getattr(imp, 'is_wildcard', False), getattr(imp, 'line_number', None),
                getattr(imp, 'is_external', True),
                getattr(imp, 'package_name', None)
            )
    
    async def _run_analyses(
        self, 
        codebase: GraphSitterCodebase, 
        repo_id: UUID, 
        analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Run specified analyses on the codebase"""
        
        results = {}
        
        for analysis_type in analysis_types:
            try:
                logger.info(f"Running {analysis_type} analysis for repository {repo_id}")
                
                # Execute analysis template
                result = await self.analysis_executor.execute_analysis(
                    analysis_type, repo_id
                )
                
                results[analysis_type] = result
                
                # Store result in database
                await self._store_analysis_result(result)
                
            except Exception as e:
                logger.error(f"Failed to run {analysis_type} analysis: {str(e)}")
                results[analysis_type] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        return results
    
    async def _store_analysis_result(self, result: Dict[str, Any]):
        """Store analysis result in the database"""
        
        async with self.db_manager.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO analysis_results (
                    analysis_type, analysis_subtype, repository_id,
                    analyzer_name, analyzer_version, analysis_date,
                    results, metrics, score, grade, confidence_level,
                    recommendations, warnings, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """,
                result['analysis_type'], result['analysis_subtype'],
                UUID(result['repository_id']), result['analyzer_name'],
                result['analyzer_version'], result['analysis_date'],
                json.dumps(result['results']), json.dumps(result['metrics']),
                result['score'], result['grade'], result['confidence_level'],
                result['recommendations'], result['warnings'],
                json.dumps(result['metadata'])
            )
    
    async def _update_repository_status(
        self, 
        repo_id: UUID, 
        status: str, 
        error_message: Optional[str] = None
    ):
        """Update repository analysis status"""
        
        async with self.db_manager.get_connection() as conn:
            if error_message:
                await conn.execute(
                    """
                    UPDATE repositories 
                    SET analysis_status = $2, last_analyzed_at = NOW(),
                        metadata = jsonb_set(
                            COALESCE(metadata, '{}'), 
                            '{last_error}', 
                            to_jsonb($3::text)
                        )
                    WHERE id = $1
                    """,
                    repo_id, status, error_message
                )
            else:
                await conn.execute(
                    """
                    UPDATE repositories 
                    SET analysis_status = $2, last_analyzed_at = NOW()
                    WHERE id = $1
                    """,
                    repo_id, status
                )
    
    async def _get_codebase_summary(self, repo_id: UUID) -> Dict[str, Any]:
        """Get summary statistics for the analyzed codebase"""
        
        async with self.db_manager.get_connection() as conn:
            summary = await conn.fetchrow(
                """
                SELECT 
                    COUNT(DISTINCT f.id) as file_count,
                    COUNT(DISTINCT s.id) as symbol_count,
                    COUNT(DISTINCT CASE WHEN s.symbol_type = 'function' THEN s.id END) as function_count,
                    COUNT(DISTINCT CASE WHEN s.symbol_type = 'class' THEN s.id END) as class_count,
                    COUNT(DISTINCT i.id) as import_count,
                    SUM(f.line_count) as total_lines,
                    COUNT(DISTINCT f.language) as language_count,
                    array_agg(DISTINCT f.language) as languages
                FROM files f
                LEFT JOIN symbols s ON f.id = s.file_id
                LEFT JOIN imports i ON f.id = i.file_id
                WHERE f.repository_id = $1
                """,
                repo_id
            )
            
            return dict(summary) if summary else {}
    
    def _get_default_analyses(self) -> List[str]:
        """Get list of default analysis types to run"""
        return [
            'CyclomaticComplexity',
            'MaintainabilityIndex', 
            'DependencyGraph',
            'CodeQuality',
            'DeadCodeDetection',
            'SecurityAnalysis'
        ]
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of file content"""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def get_analysis_results(
        self, 
        repo_id: UUID, 
        analysis_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve analysis results for a repository"""
        
        async with self.db_manager.get_connection() as conn:
            if analysis_type:
                results = await conn.fetch(
                    """
                    SELECT * FROM analysis_results 
                    WHERE repository_id = $1 AND analysis_type = $2
                    ORDER BY analysis_date DESC
                    """,
                    repo_id, analysis_type
                )
            else:
                results = await conn.fetch(
                    """
                    SELECT * FROM analysis_results 
                    WHERE repository_id = $1
                    ORDER BY analysis_date DESC
                    """,
                    repo_id
                )
            
            return [dict(result) for result in results]
    
    async def create_analysis_task(
        self,
        repo_path_or_url: str,
        analysis_types: Optional[List[str]] = None,
        priority: int = 5,
        configuration: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """Create an analysis task for asynchronous execution"""
        
        task_config = {
            "repo_path_or_url": repo_path_or_url,
            "analysis_types": analysis_types or self._get_default_analyses(),
            "configuration": configuration or {}
        }
        
        async with self.db_manager.get_connection() as conn:
            task_id = await conn.fetchval(
                """
                INSERT INTO tasks (
                    name, description, task_type, priority, configuration
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                f"Analyze repository: {repo_path_or_url}",
                f"Comprehensive analysis of {repo_path_or_url}",
                "analysis",
                priority,
                json.dumps(task_config)
            )
        
        return task_id
    
    async def close(self):
        """Close database connections and cleanup"""
        await self.db_manager.close()
        logger.info("Graph-Sitter integration layer closed")


# Example usage and testing
async def main():
    """Example usage of the Graph-Sitter integration"""
    
    # Initialize integration
    integration = GraphSitterIntegration(
        database_url="postgresql://user:password@localhost/analysis_db"
    )
    
    await integration.initialize()
    
    try:
        # Analyze a repository
        result = await integration.analyze_repository(
            repo_path_or_url="https://github.com/example/repo.git",
            analysis_types=["CyclomaticComplexity", "MaintainabilityIndex"],
            language="python"
        )
        
        print(f"Analysis completed: {result['status']}")
        print(f"Repository ID: {result['repository_id']}")
        print(f"Execution time: {result['execution_time_seconds']:.2f} seconds")
        
        # Get analysis results
        repo_id = UUID(result['repository_id'])
        results = await integration.get_analysis_results(repo_id)
        
        for analysis_result in results:
            print(f"Analysis: {analysis_result['analysis_type']}")
            print(f"Score: {analysis_result['score']}")
            print(f"Grade: {analysis_result['grade']}")
            
    finally:
        await integration.close()


if __name__ == "__main__":
    asyncio.run(main())

