#!/usr/bin/env python3
"""
Graph-Sitter System Validation Script
Comprehensive validation of the entire Graph-Sitter system including configuration, code, and database schemas
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from validation.config_validator import ConfigValidator
from validation.code_validator import CodeValidator


def main():
    """Main validation entry point"""
    print("🚀 Graph-Sitter Comprehensive System Validation")
    print("=" * 60)
    print()
    
    overall_success = True
    
    # 1. Configuration Validation
    print("🔧 CONFIGURATION VALIDATION")
    print("-" * 30)
    config_validator = ConfigValidator()
    config_success, config_results = config_validator.validate_all()
    config_validator.print_results()
    
    if not config_success:
        overall_success = False
    
    print("\n" + "=" * 60 + "\n")
    
    # 2. Code Validation
    print("💻 CODE VALIDATION")
    print("-" * 30)
    code_validator = CodeValidator()
    code_success, code_results = code_validator.validate_all()
    code_validator.print_results()
    
    if not code_success:
        overall_success = False
    
    print("\n" + "=" * 60 + "\n")
    
    # 3. Database Schema Validation
    print("🗄️  DATABASE SCHEMA VALIDATION")
    print("-" * 30)
    db_success = validate_database_schemas()
    
    if not db_success:
        overall_success = False
    
    print("\n" + "=" * 60 + "\n")
    
    # 4. Integration Validation
    print("🔗 INTEGRATION VALIDATION")
    print("-" * 30)
    integration_success = validate_integrations()
    
    if not integration_success:
        overall_success = False
    
    print("\n" + "=" * 60 + "\n")
    
    # Final Summary
    print("📊 FINAL VALIDATION SUMMARY")
    print("-" * 30)
    
    components = [
        ("Configuration", config_success),
        ("Code Quality", code_success),
        ("Database Schemas", db_success),
        ("Integrations", integration_success)
    ]
    
    for component, success in components:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {component:<20} {status}")
    
    print()
    
    if overall_success:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("Your Graph-Sitter system is ready for deployment.")
        return 0
    else:
        print("⚠️  VALIDATION FAILURES DETECTED")
        print("Please fix the issues above before proceeding.")
        return 1


def validate_database_schemas():
    """Validate database schema files"""
    success = True
    
    required_schema_files = [
        "database/init/00_core_tables.sql",
        "database/tasks/models.sql",
        "database/analytics/models.sql",
        "database/prompts/models.sql"
    ]
    
    for schema_file in required_schema_files:
        if not Path(schema_file).exists():
            print(f"❌ Missing schema file: {schema_file}")
            success = False
        else:
            # Basic SQL syntax check
            try:
                with open(schema_file, 'r') as f:
                    content = f.read()
                
                # Check for basic SQL structure
                if not any(keyword in content.upper() for keyword in ['CREATE TABLE', 'CREATE TYPE', 'CREATE FUNCTION']):
                    print(f"⚠️  Schema file may be empty or invalid: {schema_file}")
                    success = False
                else:
                    print(f"✅ Schema file valid: {schema_file}")
                    
            except Exception as e:
                print(f"❌ Error reading schema file {schema_file}: {e}")
                success = False
    
    # Check for required SQL functions
    required_functions = [
        "add_task",
        "add_subtask",
        "analyze_codebase",
        "add_prompt",
        "expand_prompt_full"
    ]
    
    print("\n📋 Checking required SQL functions...")
    for func_name in required_functions:
        found = False
        for schema_file in required_schema_files:
            if Path(schema_file).exists():
                try:
                    with open(schema_file, 'r') as f:
                        content = f.read()
                    if f"FUNCTION {func_name}" in content:
                        found = True
                        break
                except:
                    continue
        
        if found:
            print(f"✅ Function found: {func_name}")
        else:
            print(f"❌ Missing function: {func_name}")
            success = False
    
    return success


def validate_integrations():
    """Validate integration configurations"""
    success = True
    
    print("🔍 Checking integration requirements...")
    
    # Check for required environment variables for integrations
    integrations = {
        "Codegen API": ["CODEGEN_ORG_ID", "CODEGEN_TOKEN"],
        "Database": ["DATABASE_URL"],
        "GitHub": ["GITHUB_TOKEN"],
        "Linear": ["LINEAR_API_KEY"],
        "Anthropic": ["CONTEXTEN_ANTHROPIC_API_KEY"]
    }
    
    for integration_name, env_vars in integrations.items():
        integration_configured = True
        for env_var in env_vars:
            if not os.getenv(env_var):
                integration_configured = False
                break
        
        if integration_configured:
            print(f"✅ {integration_name} configured")
        else:
            print(f"⚠️  {integration_name} not configured (optional)")
    
    # Check for required directories
    required_dirs = [
        "src/graph_sitter",
        "src/codegen", 
        "database/tasks",
        "database/analytics",
        "database/prompts"
    ]
    
    print("\n📁 Checking directory structure...")
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            success = False
    
    # Check for modular separation
    print("\n🧩 Checking modular separation...")
    
    # Check that graph_sitter and codegen are properly separated
    graph_sitter_files = list(Path("src/graph_sitter").rglob("*.py")) if Path("src/graph_sitter").exists() else []
    codegen_files = list(Path("src/codegen").rglob("*.py")) if Path("src/codegen").exists() else []
    
    if graph_sitter_files:
        print(f"✅ Graph-Sitter module has {len(graph_sitter_files)} Python files")
    else:
        print("⚠️  Graph-Sitter module appears empty")
    
    if codegen_files:
        print(f"✅ Codegen module has {len(codegen_files)} Python files")
    else:
        print("⚠️  Codegen module appears empty")
    
    return success


if __name__ == "__main__":
    sys.exit(main())

