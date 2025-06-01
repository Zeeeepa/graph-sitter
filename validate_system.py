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
    
    # 3. Test Suite Validation
    print("🧪 TEST SUITE VALIDATION")
    print("-" * 30)
    test_success = validate_test_suite()
    
    if not test_success:
        overall_success = False
    
    print("\n" + "=" * 60 + "\n")
    
    # 4. Database Schema Validation
    print("🗄️  DATABASE SCHEMA VALIDATION")
    print("-" * 30)
    db_success = validate_database_schemas()
    
    if not db_success:
        overall_success = False
    
    print("\n" + "=" * 60 + "\n")
    
    # 5. Integration Validation
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
        ("Test Suite", test_success),
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


def validate_test_suite():
    """Validate test suite health and quality"""
    success = True
    
    print("🔍 Analyzing test suite structure...")
    
    # Check test directory structure
    test_dir = Path("tests")
    if not test_dir.exists():
        print("❌ Tests directory not found")
        return False
    
    # Count test files
    test_files = list(test_dir.rglob("test_*.py"))
    total_test_files = len(test_files)
    
    if total_test_files == 0:
        print("❌ No test files found")
        return False
    
    print(f"✅ Found {total_test_files} test files")
    
    # Check for conftest.py
    conftest_files = list(test_dir.rglob("conftest.py"))
    if conftest_files:
        print(f"✅ Found {len(conftest_files)} conftest.py files")
    else:
        print("⚠️  No conftest.py files found")
    
    # Analyze skipped tests
    skipped_count = 0
    xfail_count = 0
    
    for test_file in test_files:
        try:
            content = test_file.read_text(encoding='utf-8', errors='ignore')
            skipped_count += content.count("@pytest.mark.skip")
            xfail_count += content.count("@pytest.mark.xfail")
        except Exception as e:
            print(f"⚠️  Could not read {test_file}: {e}")
    
    print(f"📊 Test health metrics:")
    print(f"  - Total test files: {total_test_files}")
    print(f"  - Skipped tests: {skipped_count}")
    print(f"  - XFail tests: {xfail_count}")
    
    # Quality thresholds
    skip_ratio = skipped_count / max(total_test_files, 1)
    if skip_ratio > 0.3:  # More than 30% skipped
        print(f"⚠️  High skip ratio: {skip_ratio:.1%} of tests are skipped")
        success = False
    else:
        print(f"✅ Acceptable skip ratio: {skip_ratio:.1%}")
    
    # Check for test configuration
    pyproject_toml = Path("pyproject.toml")
    if pyproject_toml.exists():
        try:
            content = pyproject_toml.read_text()
            if "[tool.pytest.ini_options]" in content:
                print("✅ Pytest configuration found in pyproject.toml")
            else:
                print("⚠️  No pytest configuration found")
        except Exception as e:
            print(f"⚠️  Could not read pyproject.toml: {e}")
    
    # Check for CI/CD test integration
    github_workflows = Path(".github/workflows")
    if github_workflows.exists():
        workflow_files = list(github_workflows.glob("*.yml"))
        test_workflows = [
            f for f in workflow_files 
            if any(keyword in f.read_text() for keyword in ["pytest", "test", "coverage"])
        ]
        
        if test_workflows:
            print(f"✅ Found {len(test_workflows)} CI/CD workflows with testing")
        else:
            print("⚠️  No CI/CD test workflows found")
    
    # Check for coverage configuration
    if "[tool.coverage" in pyproject_toml.read_text() if pyproject_toml.exists() else False:
        print("✅ Coverage configuration found")
    else:
        print("⚠️  No coverage configuration found")
    
    return success


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
