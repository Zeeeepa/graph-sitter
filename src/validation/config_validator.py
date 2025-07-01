"""
Configuration Validator
Validates Graph-Sitter configuration files and settings
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

try:
    import toml
except ImportError:
    try:
        import tomllib as toml
    except ImportError:
        # Fallback for older Python versions
        toml = None

class ConfigValidator:
    """Validates system configuration"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        
    def validate_all(self) -> Tuple[bool, Dict]:
        """Validate all configuration aspects"""
        results = {
            "pyproject_toml": self._validate_pyproject_toml(),
            "environment_vars": self._validate_environment_variables(),
            "test_config": self._validate_test_configuration(),
            "ci_config": self._validate_ci_configuration()
        }
        
        success = all(results.values())
        return success, results
    
    def _validate_pyproject_toml(self) -> bool:
        """Validate pyproject.toml configuration"""
        pyproject_path = Path("pyproject.toml")
        
        if not pyproject_path.exists():
            self.issues.append("pyproject.toml not found")
            return False
        
        if toml is None:
            self.warnings.append("TOML parser not available - skipping pyproject.toml validation")
            return True
        
        try:
            if hasattr(toml, 'load'):
                config = toml.load(pyproject_path)
            else:
                # tomllib (Python 3.11+) uses loads with binary mode
                with open(pyproject_path, 'rb') as f:
                    config = toml.load(f)
            
            # Check required sections
            required_sections = ["project", "tool.pytest.ini_options"]
            for section in required_sections:
                if not self._get_nested_key(config, section.split(".")):
                    self.issues.append(f"Missing required section: {section}")
                    return False
            
            # Validate pytest configuration
            pytest_config = config.get("tool", {}).get("pytest", {}).get("ini_options", {})
            
            if "addopts" not in pytest_config:
                self.warnings.append("No pytest addopts configured")
            
            if "pythonpath" not in pytest_config:
                self.warnings.append("No pythonpath configured for pytest")
            
            return True
            
        except Exception as e:
            self.issues.append(f"Failed to parse pyproject.toml: {e}")
            return False
    
    def _validate_environment_variables(self) -> bool:
        """Validate required environment variables"""
        optional_vars = [
            "CODEGEN_ORG_ID",
            "CODEGEN_TOKEN", 
            "GITHUB_TOKEN",
            "LINEAR_API_KEY",
            "CONTEXTEN_ANTHROPIC_API_KEY"
        ]
        
        missing_vars = []
        for var in optional_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.warnings.append(f"Optional environment variables not set: {', '.join(missing_vars)}")
        
        return True  # All env vars are optional
    
    def _validate_test_configuration(self) -> bool:
        """Validate test configuration"""
        test_dir = Path("tests")
        
        if not test_dir.exists():
            self.issues.append("Tests directory not found")
            return False
        
        # Check for conftest.py
        main_conftest = test_dir / "conftest.py"
        if not main_conftest.exists():
            self.warnings.append("Main conftest.py not found")
        
        # Check test structure
        required_dirs = ["unit", "integration", "shared"]
        for dir_name in required_dirs:
            test_subdir = test_dir / dir_name
            if not test_subdir.exists():
                self.warnings.append(f"Test subdirectory not found: {dir_name}")
        
        return True
    
    def _validate_ci_configuration(self) -> bool:
        """Validate CI/CD configuration"""
        github_dir = Path(".github")
        
        if not github_dir.exists():
            self.warnings.append("No .github directory found")
            return True
        
        workflows_dir = github_dir / "workflows"
        if not workflows_dir.exists():
            self.warnings.append("No GitHub workflows directory found")
            return True
        
        # Check for test workflows
        workflow_files = list(workflows_dir.glob("*.yml"))
        test_workflows = []
        
        for workflow_file in workflow_files:
            try:
                content = workflow_file.read_text()
                if any(keyword in content for keyword in ["pytest", "test", "coverage"]):
                    test_workflows.append(workflow_file.name)
            except Exception:
                continue
        
        if not test_workflows:
            self.warnings.append("No test workflows found in CI/CD configuration")
        
        return True
    
    def _get_nested_key(self, data: Dict, keys: List[str]) -> Any:
        """Get nested dictionary key"""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def print_results(self):
        """Print validation results"""
        if self.issues:
            print("❌ Configuration Issues:")
            for issue in self.issues:
                print(f"  - {issue}")
        
        if self.warnings:
            print("⚠️  Configuration Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.issues and not self.warnings:
            print("✅ Configuration validation passed")
        elif not self.issues:
            print("✅ Configuration validation passed with warnings")
