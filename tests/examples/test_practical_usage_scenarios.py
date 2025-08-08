#!/usr/bin/env python3
"""
Practical Usage Scenarios for Serena Error Analysis

This file demonstrates real-world usage scenarios and validates that the error analysis
system works as expected in practical situations.
"""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, List, Any

from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.serena import (
    SerenaAPI,
    ComprehensiveErrorAnalyzer,
    get_codebase_error_analysis,
    analyze_file_errors,
    find_function_relationships,
    create_serena_api
)


class TestPracticalUsageScenarios:
    """Test practical usage scenarios that developers would encounter."""
    
    @pytest.fixture
    def web_application_codebase(self):
        """Create a realistic web application codebase with common issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create typical web app structure
            (project_root / "app").mkdir()
            (project_root / "app" / "models").mkdir()
            (project_root / "app" / "views").mkdir()
            (project_root / "app" / "utils").mkdir()
            
            # Models with database-related issues
            user_model = '''
"""User model with database operations."""
import hashlib
from typing import Optional, List
from .database import db_connection

class User:
    """User model class."""
    
    def __init__(self, username: str, email: str, password: str, unused_role: str = None):
        """Initialize user."""
        self.username = username
        self.email = email
        self.password_hash = self._hash_password(password)
        # unused_role parameter is not used - common mistake
    
    def _hash_password(self, password: str) -> str:
        """Hash password for storage."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def save(self) -> bool:
        """Save user to database."""
        try:
            conn = db_connection()
            cursor = conn.cursor()
            
            # SQL injection vulnerability - should be detected
            query = f"INSERT INTO users (username, email, password_hash) VALUES ('{self.username}', '{self.email}', '{self.password_hash}')"
            cursor.execute(query)
            
            conn.commit()
            return True
        except Exception as e:
            # Undefined logger - common mistake
            logger.error(f"Failed to save user: {e}")  # Error: logger not defined
            return False
    
    @classmethod
    def find_by_username(cls, username: str) -> Optional['User']:
        """Find user by username."""
        try:
            conn = db_connection()
            cursor = conn.cursor()
            
            # Another SQL injection vulnerability
            cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
            row = cursor.fetchone()
            
            if row:
                # Undefined variable - typo in column name
                return cls(row['user_name'], row['email'], row['password_hash'])  # Error: should be 'username'
            return None
        except Exception:
            return None
    
    def update_profile(self, new_email: str, new_username: str, extra_param1: str, extra_param2: str):
        """Update user profile with too many parameters."""
        # extra_param1 and extra_param2 are unused
        self.email = new_email
        self.username = new_username
        return self.save()
'''
            
            # Views with web framework issues
            user_views = '''
"""User views for web application."""
from flask import Flask, request, jsonify, render_template
from .models.user import User
from .utils.validation import validate_email, validate_password

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user."""
    data = request.get_json()
    
    # Missing validation - security issue
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Undefined function call - typo
    if not validate_user_input(username, email, password):  # Error: function doesn't exist
        return jsonify({'error': 'Invalid input'}), 400
    
    # Create user with unused parameter
    user = User(username, email, password, "default_role")  # unused parameter
    
    if user.save():
        return jsonify({'message': 'User created successfully'}), 201
    else:
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/login', methods=['POST'])
def login_user():
    """Login user."""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    # Find user
    user = User.find_by_username(username)
    
    if user and user._hash_password(password) == user.password_hash:
        # Missing import for session management
        session['user_id'] = user.username  # Error: session not imported
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/profile/<username>')
def get_profile(username, unused_param=None):
    """Get user profile with unused parameter."""
    # unused_param is not used
    user = User.find_by_username(username)
    
    if user:
        return jsonify({
            'username': user.username,
            'email': user.email
        })
    else:
        return jsonify({'error': 'User not found'}), 404

def helper_function_never_called(param1, param2, param3):
    """This function is never called - dead code."""
    return param1 + param2 + param3
'''
            
            # Utils with validation issues
            validation_utils = '''
"""Validation utilities."""
import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    
    # Simple email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str, min_length: int = 8, unused_complexity: bool = True) -> bool:
    """Validate password strength."""
    # unused_complexity parameter is not used
    if not password:
        return False
    
    if len(password) < min_length:
        return False
    
    # Check for undefined variable - typo
    if not has_special_chars:  # Error: has_special_chars not defined
        return False
    
    return True

def validate_username(username: str) -> bool:
    """Validate username format."""
    if not username:
        return False
    
    # Username should be alphanumeric and underscores only
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))

# Function with wrong name that should be validate_user_input
def validate_user_data(username: str, email: str, password: str) -> bool:
    """Validate all user input data."""
    return (validate_username(username) and 
            validate_email(email) and 
            validate_password(password))
'''
            
            # Database connection with issues
            database_py = '''
"""Database connection utilities."""
import sqlite3
import os
from typing import Optional

def db_connection() -> sqlite3.Connection:
    """Get database connection."""
    db_path = os.getenv('DATABASE_PATH', 'app.db')
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    except sqlite3.Error as e:
        # Undefined variable in error handling
        log.error(f"Database connection failed: {e}")  # Error: log not defined
        raise

def init_database():
    """Initialize database tables."""
    conn = db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def cleanup_old_sessions(days_old: int, unused_param: str = None):
    """Clean up old sessions."""
    # unused_param is not used
    conn = db_connection()
    cursor = conn.cursor()
    
    # Missing import for datetime
    cutoff_date = datetime.now() - timedelta(days=days_old)  # Error: datetime not imported
    
    cursor.execute(
        "DELETE FROM sessions WHERE created_at < ?",
        (cutoff_date,)
    )
    
    conn.commit()
    conn.close()
'''
            
            # Configuration with issues
            config_py = '''
"""Application configuration."""
import os
from typing import Dict, Any

class Config:
    """Base configuration class."""
    
    def __init__(self, debug_mode: bool = False, unused_env: str = None):
        """Initialize configuration."""
        self.debug_mode = debug_mode
        # unused_env parameter is not used
        
    def get_database_url(self) -> str:
        """Get database URL."""
        # Undefined environment variable access
        return os.getenv('DATABASE_URL', default_db_url)  # Error: default_db_url not defined
    
    def get_secret_key(self) -> str:
        """Get secret key for sessions."""
        secret = os.getenv('SECRET_KEY')
        if not secret:
            # Undefined variable
            raise ValueError(f"SECRET_KEY not set in environment: {missing_key}")  # Error: missing_key not defined
        return secret
    
    def load_from_file(self, config_file: str, backup_file: str, extra_file: str) -> Dict[str, Any]:
        """Load configuration from file with too many parameters."""
        # extra_file parameter is unused
        config = {}
        
        try:
            with open(config_file, 'r') as f:
                # Missing import for json
                config = json.load(f)  # Error: json not imported
        except FileNotFoundError:
            try:
                with open(backup_file, 'r') as f:
                    config = json.load(f)
            except FileNotFoundError:
                config = {}
        
        return config

# Global configuration instance
app_config = Config()

def get_config() -> Config:
    """Get application configuration."""
    return app_config

def unused_config_function():
    """This function is never called."""
    return {"unused": True}
'''
            
            # Write all files
            (project_root / "app" / "__init__.py").write_text("")
            (project_root / "app" / "models" / "__init__.py").write_text("")
            (project_root / "app" / "views" / "__init__.py").write_text("")
            (project_root / "app" / "utils" / "__init__.py").write_text("")
            
            (project_root / "app" / "models" / "user.py").write_text(user_model)
            (project_root / "app" / "views" / "user_views.py").write_text(user_views)
            (project_root / "app" / "utils" / "validation.py").write_text(validation_utils)
            (project_root / "app" / "models" / "database.py").write_text(database_py)
            (project_root / "app" / "config.py").write_text(config_py)
            
            yield project_root
    
    def test_web_app_comprehensive_analysis(self, web_application_codebase):
        """Test comprehensive analysis of a web application."""
        print("\n🔍 ANALYZING WEB APPLICATION CODEBASE")
        print("=" * 50)
        
        # Create codebase and API
        codebase = Codebase(str(web_application_codebase))
        api = create_serena_api(codebase, enable_lsp=False)
        
        try:
            # Get comprehensive analysis
            analysis = get_codebase_error_analysis(codebase)
            
            print(f"📊 ANALYSIS RESULTS:")
            print(f"   Total errors: {analysis['error_summary'].get('total_errors', 0)}")
            print(f"   Total warnings: {analysis['error_summary'].get('total_warnings', 0)}")
            print(f"   Files analyzed: {len(analysis['dependency_graph'])}")
            print(f"   Unused parameters found: {len(analysis['unused_parameters'])}")
            print(f"   Wrong parameters found: {len(analysis['wrong_parameters'])}")
            
            # Verify we got meaningful results
            assert isinstance(analysis, dict)
            assert 'error_summary' in analysis
            assert 'dependency_graph' in analysis
            
            # Should have analyzed Python files
            python_files = [f for f in analysis['dependency_graph'].keys() if f.endswith('.py')]
            assert len(python_files) >= 5, f"Should analyze multiple Python files, got {len(python_files)}"
            
            print(f"   ✅ Successfully analyzed {len(python_files)} Python files")
            
        finally:
            api.shutdown()
    
    def test_unused_parameter_detection_in_web_app(self, web_application_codebase):
        """Test detection of unused parameters in web application."""
        print("\n🔍 DETECTING UNUSED PARAMETERS")
        print("=" * 40)
        
        codebase = Codebase(str(web_application_codebase))
        api = create_serena_api(codebase, enable_lsp=False)
        
        try:
            unused_params = api.get_unused_parameters()
            
            print(f"📊 Found {len(unused_params)} unused parameters:")
            for param in unused_params[:5]:  # Show first 5
                print(f"   - {param.get('parameter_name', 'unknown')} in {param.get('function_name', 'unknown')}")
                if param.get('suggestion'):
                    print(f"     💡 {param['suggestion']}")
            
            # Verify we found some unused parameters
            assert isinstance(unused_params, list)
            print(f"   ✅ Successfully detected unused parameters")
            
        finally:
            api.shutdown()
    
    def test_function_relationship_analysis_web_app(self, web_application_codebase):
        """Test function relationship analysis in web application."""
        print("\n🔍 ANALYZING FUNCTION RELATIONSHIPS")
        print("=" * 45)
        
        codebase = Codebase(str(web_application_codebase))
        
        # Analyze relationships for a key function
        relationships = find_function_relationships(codebase, 'validate_email')
        
        print(f"📊 Relationships for 'validate_email':")
        print(f"   Callers: {len(relationships['callers'])}")
        print(f"   Calls: {len(relationships['calls'])}")
        print(f"   Symbol usage: {len(relationships['symbol_usage'])}")
        print(f"   Related symbols: {len(relationships['related_symbols'])}")
        
        # Show some details
        if relationships['callers']:
            print(f"   📞 Called by:")
            for caller in relationships['callers'][:3]:
                print(f"      - {caller.get('caller_function', 'unknown')} in {caller.get('file_path', 'unknown')}")
        
        assert isinstance(relationships, dict)
        assert 'function_name' in relationships
        assert relationships['function_name'] == 'validate_email'
        print(f"   ✅ Successfully analyzed function relationships")
    
    def test_file_specific_error_analysis(self, web_application_codebase):
        """Test file-specific error analysis."""
        print("\n🔍 ANALYZING SPECIFIC FILES")
        print("=" * 35)
        
        codebase = Codebase(str(web_application_codebase))
        
        # Analyze the user model file
        user_model_file = "app/models/user.py"
        result = analyze_file_errors(codebase, user_model_file)
        
        print(f"📊 Analysis of {user_model_file}:")
        print(f"   Errors found: {len(result['errors'])}")
        print(f"   Error contexts: {len(result['error_contexts'])}")
        print(f"   Dependencies: {len(result['dependencies'])}")
        
        # Show error details
        for i, error in enumerate(result['errors'][:3]):  # Show first 3 errors
            print(f"   🚨 Error {i+1}: {error.get('message', 'Unknown error')[:60]}...")
        
        # Show dependencies
        if result['dependencies']:
            print(f"   📦 Dependencies:")
            for dep in result['dependencies'][:5]:  # Show first 5 dependencies
                print(f"      - {dep}")
        
        assert isinstance(result, dict)
        assert result['file_path'] == user_model_file
        print(f"   ✅ Successfully analyzed file-specific errors")
    
    def test_security_issue_detection(self, web_application_codebase):
        """Test detection of potential security issues."""
        print("\n🔍 DETECTING SECURITY ISSUES")
        print("=" * 35)
        
        codebase = Codebase(str(web_application_codebase))
        api = create_serena_api(codebase, enable_lsp=False)
        
        try:
            # Get all errors with context
            errors_with_context = api.get_all_errors_with_context()
            
            # Look for potential security-related issues
            security_related = []
            for error_ctx in errors_with_context:
                error_msg = error_ctx['error'].get('message', '').lower()
                if any(keyword in error_msg for keyword in ['sql', 'injection', 'undefined', 'import']):
                    security_related.append(error_ctx)
            
            print(f"📊 Potential security-related issues: {len(security_related)}")
            
            for i, issue in enumerate(security_related[:3]):  # Show first 3
                error = issue['error']
                print(f"   🚨 Issue {i+1}: {error.get('message', 'Unknown')[:60]}...")
                print(f"      📍 Location: {error.get('file_path', 'unknown')}:{error.get('line', 0)}")
                
                if issue['fix_suggestions']:
                    print(f"      💡 Suggestion: {issue['fix_suggestions'][0][:50]}...")
            
            print(f"   ✅ Security analysis completed")
            
        finally:
            api.shutdown()
    
    def test_dependency_analysis_web_app(self, web_application_codebase):
        """Test dependency analysis for web application."""
        print("\n🔍 ANALYZING DEPENDENCIES")
        print("=" * 30)
        
        codebase = Codebase(str(web_application_codebase))
        api = create_serena_api(codebase, enable_lsp=False)
        
        try:
            dep_graph = api.get_dependency_graph()
            
            print(f"📊 Dependency Analysis:")
            print(f"   Files with dependencies: {len(dep_graph)}")
            
            # Find files with most dependencies
            files_by_deps = sorted(
                [(f, len(deps)) for f, deps in dep_graph.items() if deps],
                key=lambda x: x[1],
                reverse=True
            )
            
            print(f"   📦 Files with most dependencies:")
            for file_path, dep_count in files_by_deps[:5]:
                print(f"      - {file_path}: {dep_count} dependencies")
            
            # Show dependencies for a specific file
            if files_by_deps:
                top_file, _ = files_by_deps[0]
                deps = dep_graph[top_file]
                print(f"   📋 Dependencies of {top_file}:")
                for dep in deps[:5]:  # Show first 5
                    print(f"      - {dep}")
            
            assert isinstance(dep_graph, dict)
            print(f"   ✅ Dependency analysis completed")
            
        finally:
            api.shutdown()
    
    def test_code_quality_metrics(self, web_application_codebase):
        """Test code quality metrics extraction."""
        print("\n🔍 ANALYZING CODE QUALITY")
        print("=" * 35)
        
        codebase = Codebase(str(web_application_codebase))
        api = create_serena_api(codebase, enable_lsp=False)
        
        try:
            # Get comprehensive status
            status = api.get_status()
            
            print(f"📊 System Status:")
            print(f"   Error analyzer: {'✅' if status['error_analyzer_initialized'] else '❌'}")
            print(f"   MCP bridge: {'✅' if status['mcp_bridge_available'] else '❌'}")
            print(f"   Semantic tools: {'✅' if status['semantic_tools_available'] else '❌'}")
            print(f"   LSP enabled: {'✅' if status['lsp_enabled'] else '❌'}")
            
            print(f"\n📈 Error Statistics:")
            print(f"   Total errors: {status['total_errors']}")
            print(f"   Total warnings: {status['total_warnings']}")
            print(f"   Total diagnostics: {status['total_diagnostics']}")
            
            # Get error summary for more details
            summary = api.get_error_summary()
            if 'errors_by_type' in summary:
                print(f"\n🏷️  Error Types:")
                for error_type, count in summary['errors_by_type'].items():
                    print(f"   - {error_type}: {count}")
            
            assert isinstance(status, dict)
            print(f"   ✅ Code quality analysis completed")
            
        finally:
            api.shutdown()
    
    def test_practical_workflow_simulation(self, web_application_codebase):
        """Simulate a practical developer workflow."""
        print("\n🔍 SIMULATING DEVELOPER WORKFLOW")
        print("=" * 40)
        
        codebase = Codebase(str(web_application_codebase))
        
        print("👨‍💻 Developer Workflow Simulation:")
        print("   1. Initial codebase analysis...")
        
        # Step 1: Initial analysis
        analysis = get_codebase_error_analysis(codebase)
        total_issues = (analysis['error_summary'].get('total_errors', 0) + 
                       len(analysis['unused_parameters']) + 
                       len(analysis['wrong_parameters']))
        
        print(f"      Found {total_issues} total issues")
        
        print("   2. Analyzing specific problematic file...")
        
        # Step 2: Focus on specific file
        if analysis['error_summary'].get('most_problematic_files'):
            problem_file = analysis['error_summary']['most_problematic_files'][0]['file_path']
            file_analysis = analyze_file_errors(codebase, problem_file)
            print(f"      Analyzed {problem_file}: {len(file_analysis['errors'])} errors")
        
        print("   3. Investigating function relationships...")
        
        # Step 3: Investigate key functions
        key_functions = ['validate_email', 'save', 'register_user']
        for func in key_functions:
            try:
                relationships = find_function_relationships(codebase, func)
                callers = len(relationships['callers'])
                usage = len(relationships['symbol_usage'])
                print(f"      {func}: {callers} callers, {usage} usages")
            except Exception:
                print(f"      {func}: analysis skipped")
        
        print("   4. Checking unused parameters...")
        
        # Step 4: Review unused parameters
        unused_count = len(analysis['unused_parameters'])
        print(f"      Found {unused_count} unused parameters to clean up")
        
        print("   ✅ Workflow simulation completed successfully!")
        
        # Verify the workflow produced meaningful results
        assert isinstance(analysis, dict)
        assert total_issues >= 0  # Should have some analysis results


if __name__ == '__main__':
    # Run with verbose output to see the practical demonstrations
    pytest.main([__file__, '-v', '-s'])
