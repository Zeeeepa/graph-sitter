"""
Configuration Validation System
Validates environment variables and system configuration for Graph-Sitter project
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import re
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    level: ValidationLevel
    component: str
    message: str
    suggestion: Optional[str] = None


class ConfigValidator:
    """Comprehensive configuration validation system"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.required_env_vars = {
            'CODEGEN_ORG_ID': 'Codegen organization ID',
            'CODEGEN_TOKEN': 'Codegen API token',
            'DATABASE_URL': 'PostgreSQL database connection string'
        }
        
        self.optional_env_vars = {
            'CODEGEN_BASE_URL': 'Codegen API base URL',
            'GRAPH_SITTER_CACHE_DIR': 'Graph-Sitter cache directory',
            'CONTEXTEN_ANTHROPIC_API_KEY': 'Anthropic API key for chat agent',
            'GITHUB_TOKEN': 'GitHub API token',
            'LINEAR_API_KEY': 'Linear API key',
            'SLACK_BOT_TOKEN': 'Slack bot token'
        }
    
    def validate_all(self) -> Tuple[bool, List[ValidationResult]]:
        """Run all validation checks"""
        logger.info("Starting comprehensive configuration validation...")
        
        # Clear previous results
        self.results = []
        
        # Run validation checks
        self._validate_environment_variables()
        self._validate_codegen_configuration()
        self._validate_database_configuration()
        self._validate_file_structure()
        self._validate_dependencies()
        self._validate_permissions()
        
        # Determine overall success
        has_errors = any(result.level == ValidationLevel.ERROR for result in self.results)
        
        logger.info(f"Validation completed. Found {len(self.results)} issues.")
        return not has_errors, self.results
    
    def _validate_environment_variables(self):
        """Validate required and optional environment variables"""
        logger.info("Validating environment variables...")
        
        # Check required variables
        for var_name, description in self.required_env_vars.items():
            value = os.getenv(var_name)
            if not value:
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="environment",
                    message=f"Required environment variable {var_name} is not set",
                    suggestion=f"Set {var_name} in your .env file. Description: {description}"
                ))
            elif var_name == 'CODEGEN_ORG_ID' and not value.isdigit():
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="environment",
                    message=f"CODEGEN_ORG_ID must be numeric, got: {value}",
                    suggestion="Check your Codegen organization ID"
                ))
            elif var_name == 'CODEGEN_TOKEN' and not self._validate_token_format(value):
                self.results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    component="environment",
                    message="CODEGEN_TOKEN format appears invalid",
                    suggestion="Verify your token from https://codegen.sh/token"
                ))
        
        # Check optional variables
        for var_name, description in self.optional_env_vars.items():
            value = os.getenv(var_name)
            if not value:
                self.results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    component="environment",
                    message=f"Optional environment variable {var_name} is not set",
                    suggestion=f"Consider setting {var_name}. Description: {description}"
                ))
    
    def _validate_codegen_configuration(self):
        """Validate Codegen API configuration"""
        logger.info("Validating Codegen configuration...")
        
        org_id = os.getenv('CODEGEN_ORG_ID')
        token = os.getenv('CODEGEN_TOKEN')
        base_url = os.getenv('CODEGEN_BASE_URL', 'https://api.codegen.com')
        
        if org_id and token:
            try:
                # Test Codegen API connection
                import requests
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                # Simple validation request
                response = requests.get(
                    f"{base_url}/v1/auth/validate",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.results.append(ValidationResult(
                        level=ValidationLevel.INFO,
                        component="codegen",
                        message="Codegen API connection successful"
                    ))
                else:
                    self.results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        component="codegen",
                        message=f"Codegen API authentication failed: {response.status_code}",
                        suggestion="Check your CODEGEN_TOKEN and CODEGEN_ORG_ID"
                    ))
                    
            except ImportError:
                self.results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    component="codegen",
                    message="Cannot test Codegen API - requests library not available",
                    suggestion="Install requests: pip install requests"
                ))
            except Exception as e:
                self.results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    component="codegen",
                    message=f"Cannot test Codegen API connection: {str(e)}",
                    suggestion="Check your network connection and API configuration"
                ))
    
    def _validate_database_configuration(self):
        """Validate database configuration"""
        logger.info("Validating database configuration...")
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            return
        
        # Parse database URL
        if not db_url.startswith('postgresql://'):
            self.results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                component="database",
                message="DATABASE_URL must start with 'postgresql://'",
                suggestion="Use format: postgresql://user:password@host:port/database"
            ))
            return
        
        try:
            # Test database connection
            import psycopg2
            from urllib.parse import urlparse
            
            parsed = urlparse(db_url)
            
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:] if parsed.path else 'postgres'
            )
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.results.append(ValidationResult(
                level=ValidationLevel.INFO,
                component="database",
                message=f"Database connection successful: {version}"
            ))
            
        except ImportError:
            self.results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                component="database",
                message="Cannot test database connection - psycopg2 not available",
                suggestion="Install psycopg2: pip install psycopg2-binary"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                component="database",
                message=f"Database connection failed: {str(e)}",
                suggestion="Check your DATABASE_URL and ensure PostgreSQL is running"
            ))
    
    def _validate_file_structure(self):
        """Validate project file structure"""
        logger.info("Validating file structure...")
        
        required_dirs = [
            'src/graph_sitter',
            'src/codegen',
            'database/tasks',
            'database/analytics',
            'database/prompts'
        ]
        
        required_files = [
            'database/README.md',
            'database/init/00_core_tables.sql',
            'database/tasks/models.sql',
            'database/analytics/models.sql',
            'database/prompts/models.sql'
        ]
        
        # Check directories
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="file_structure",
                    message=f"Required directory missing: {dir_path}",
                    suggestion=f"Create directory: mkdir -p {dir_path}"
                ))
        
        # Check files
        for file_path in required_files:
            if not Path(file_path).exists():
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="file_structure",
                    message=f"Required file missing: {file_path}",
                    suggestion=f"Create or restore file: {file_path}"
                ))
    
    def _validate_dependencies(self):
        """Validate Python dependencies"""
        logger.info("Validating dependencies...")
        
        required_packages = [
            'psycopg2',
            'requests',
            'sqlalchemy',
            'pydantic'
        ]
        
        optional_packages = [
            'anthropic',
            'openai',
            'github',
            'slack_sdk'
        ]
        
        # Check required packages
        for package in required_packages:
            try:
                __import__(package)
                self.results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    component="dependencies",
                    message=f"Required package {package} is available"
                ))
            except ImportError:
                self.results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    component="dependencies",
                    message=f"Required package {package} is not installed",
                    suggestion=f"Install package: pip install {package}"
                ))
        
        # Check optional packages
        for package in optional_packages:
            try:
                __import__(package)
                self.results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    component="dependencies",
                    message=f"Optional package {package} is available"
                ))
            except ImportError:
                self.results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    component="dependencies",
                    message=f"Optional package {package} is not installed",
                    suggestion=f"Install for enhanced features: pip install {package}"
                ))
    
    def _validate_permissions(self):
        """Validate file and directory permissions"""
        logger.info("Validating permissions...")
        
        # Check cache directory permissions
        cache_dir = os.getenv('GRAPH_SITTER_CACHE_DIR', '/tmp/graph_sitter_cache')
        cache_path = Path(cache_dir)
        
        try:
            cache_path.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = cache_path / 'test_write.tmp'
            test_file.write_text('test')
            test_file.unlink()
            
            self.results.append(ValidationResult(
                level=ValidationLevel.INFO,
                component="permissions",
                message=f"Cache directory writable: {cache_dir}"
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                component="permissions",
                message=f"Cannot write to cache directory {cache_dir}: {str(e)}",
                suggestion=f"Check permissions or set GRAPH_SITTER_CACHE_DIR to writable location"
            ))
    
    def _validate_token_format(self, token: str) -> bool:
        """Validate token format (basic check)"""
        # Basic validation - tokens should be alphanumeric with dashes
        return bool(re.match(r'^[a-zA-Z0-9\-_]+$', token)) and len(token) > 10
    
    def print_results(self):
        """Print validation results in a formatted way"""
        if not self.results:
            print("✅ No validation issues found!")
            return
        
        # Group by level
        errors = [r for r in self.results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in self.results if r.level == ValidationLevel.WARNING]
        info = [r for r in self.results if r.level == ValidationLevel.INFO]
        
        # Print errors
        if errors:
            print("\n❌ ERRORS:")
            for result in errors:
                print(f"  [{result.component}] {result.message}")
                if result.suggestion:
                    print(f"    💡 {result.suggestion}")
        
        # Print warnings
        if warnings:
            print("\n⚠️  WARNINGS:")
            for result in warnings:
                print(f"  [{result.component}] {result.message}")
                if result.suggestion:
                    print(f"    💡 {result.suggestion}")
        
        # Print info
        if info:
            print("\n📋 INFO:")
            for result in info:
                print(f"  [{result.component}] {result.message}")
                if result.suggestion:
                    print(f"    💡 {result.suggestion}")
        
        # Summary
        print(f"\n📊 SUMMARY: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")


def main():
    """Main validation entry point"""
    print("🔍 Graph-Sitter Configuration Validator")
    print("=" * 50)
    
    validator = ConfigValidator()
    success, results = validator.validate_all()
    
    validator.print_results()
    
    if success:
        print("\n✅ All critical validations passed!")
        return 0
    else:
        print("\n❌ Validation failed - please fix the errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

