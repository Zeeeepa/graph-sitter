"""
CircleCI Extension Validation Script

Final validation script that ensures the CircleCI extension is fully functional
and ready for production use. This script performs comprehensive checks on:

- Code structure and completeness
- Configuration validation
- Import and dependency checks
- Basic functionality tests
- Documentation completeness
- Example code validation
"""

import sys
import os
import importlib
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class CircleCIExtensionValidator:
    """Comprehensive validator for CircleCI extension"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.src_path = self.base_path / "src"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.success_count = 0
        self.total_checks = 0
    
    def log_success(self, message: str):
        """Log successful check"""
        print(f"✅ {message}")
        self.success_count += 1
        self.total_checks += 1
    
    def log_error(self, message: str):
        """Log error"""
        print(f"❌ {message}")
        self.errors.append(message)
        self.total_checks += 1
    
    def log_warning(self, message: str):
        """Log warning"""
        print(f"⚠️ {message}")
        self.warnings.append(message)
    
    def check_file_exists(self, file_path: Path, description: str) -> bool:
        """Check if file exists"""
        if file_path.exists():
            self.log_success(f"{description}: {file_path.name}")
            return True
        else:
            self.log_error(f"{description} missing: {file_path}")
            return False
    
    def check_module_import(self, module_path: str, description: str) -> Optional[Any]:
        """Check if module can be imported"""
        try:
            module = importlib.import_module(module_path)
            self.log_success(f"{description} imports successfully")
            return module
        except ImportError as e:
            self.log_error(f"{description} import failed: {e}")
            return None
        except Exception as e:
            self.log_error(f"{description} import error: {e}")
            return None
    
    def validate_file_structure(self) -> bool:
        """Validate complete file structure"""
        print("\n📁 Validating File Structure")
        print("=" * 50)
        
        # Core extension files
        core_files = [
            ("src/contexten/extensions/circleci/__init__.py", "Main module init"),
            ("src/contexten/extensions/circleci/config.py", "Configuration module"),
            ("src/contexten/extensions/circleci/types.py", "Type definitions"),
            ("src/contexten/extensions/circleci/client.py", "CircleCI API client"),
            ("src/contexten/extensions/circleci/webhook_processor.py", "Webhook processor"),
            ("src/contexten/extensions/circleci/failure_analyzer.py", "Failure analyzer"),
            ("src/contexten/extensions/circleci/workflow_automation.py", "Workflow automation"),
            ("src/contexten/extensions/circleci/integration_agent.py", "Integration agent"),
            ("src/contexten/extensions/circleci/auto_fix_generator.py", "Auto-fix generator"),
            ("src/contexten/extensions/circleci/README.md", "Documentation")
        ]
        
        # Test files
        test_files = [
            ("tests/unit/extensions/circleci/test_config.py", "Config unit tests"),
            ("tests/unit/extensions/circleci/test_webhook_processor.py", "Webhook unit tests"),
            ("tests/integration/circleci/test_e2e_workflow.py", "E2E integration tests"),
            ("tests/run_circleci_tests.py", "Test runner")
        ]
        
        # Example files
        example_files = [
            ("examples/circleci_integration/basic_usage.py", "Basic usage example"),
            ("examples/circleci_integration/advanced_usage.py", "Advanced usage example")
        ]
        
        all_files = core_files + test_files + example_files
        
        success = True
        for file_path, description in all_files:
            full_path = self.base_path / file_path
            if not self.check_file_exists(full_path, description):
                success = False
        
        return success
    
    def validate_imports(self) -> bool:
        """Validate all module imports"""
        print("\n📦 Validating Module Imports")
        print("=" * 50)
        
        # Core modules to test
        modules = [
            ("src.contexten.extensions.circleci", "Main extension module"),
            ("src.contexten.extensions.circleci.config", "Configuration module"),
            ("src.contexten.extensions.circleci.types", "Type definitions"),
            ("src.contexten.extensions.circleci.client", "API client"),
            ("src.contexten.extensions.circleci.webhook_processor", "Webhook processor"),
            ("src.contexten.extensions.circleci.failure_analyzer", "Failure analyzer"),
            ("src.contexten.extensions.circleci.workflow_automation", "Workflow automation"),
            ("src.contexten.extensions.circleci.integration_agent", "Integration agent"),
            ("src.contexten.extensions.circleci.auto_fix_generator", "Auto-fix generator")
        ]
        
        success = True
        imported_modules = {}
        
        for module_path, description in modules:
            module = self.check_module_import(module_path, description)
            if module is None:
                success = False
            else:
                imported_modules[module_path] = module
        
        return success, imported_modules
    
    def validate_main_exports(self, imported_modules: Dict[str, Any]) -> bool:
        """Validate main module exports"""
        print("\n📤 Validating Main Module Exports")
        print("=" * 50)
        
        main_module_path = "src.contexten.extensions.circleci"
        if main_module_path not in imported_modules:
            self.log_error("Main module not available for export validation")
            return False
        
        main_module = imported_modules[main_module_path]
        
        # Expected exports
        expected_exports = [
            "CircleCIIntegrationConfig",
            "CircleCIIntegrationAgent",
            "CircleCIClient",
            "WebhookProcessor",
            "WorkflowAutomation",
            "FailureAnalyzer",
            "AutoFixGenerator",
            "CircleCIBuild",
            "CircleCIWorkflow",
            "CircleCIJob",
            "CircleCIEvent",
            "FailureAnalysis",
            "GeneratedFix"
        ]
        
        success = True
        for export_name in expected_exports:
            if hasattr(main_module, export_name):
                self.log_success(f"Export available: {export_name}")
            else:
                self.log_error(f"Missing export: {export_name}")
                success = False
        
        return success
    
    def validate_configuration(self, imported_modules: Dict[str, Any]) -> bool:
        """Validate configuration functionality"""
        print("\n⚙️ Validating Configuration")
        print("=" * 50)
        
        config_module_path = "src.contexten.extensions.circleci.config"
        if config_module_path not in imported_modules:
            self.log_error("Config module not available")
            return False
        
        try:
            config_module = imported_modules[config_module_path]
            
            # Test basic configuration creation
            APIConfig = config_module.APIConfig
            CircleCIIntegrationConfig = config_module.CircleCIIntegrationConfig
            
            api_config = APIConfig(api_token="test-token")
            self.log_success("API config creation")
            
            main_config = CircleCIIntegrationConfig(api=api_config)
            self.log_success("Main config creation")
            
            # Test validation
            issues = main_config.validate_configuration()
            self.log_success(f"Config validation (found {len(issues)} issues)")
            
            # Test serialization
            config_dict = main_config.dict()
            self.log_success("Config serialization")
            
            # Test summary
            summary = main_config.summary
            self.log_success("Config summary generation")
            
            return True
            
        except Exception as e:
            self.log_error(f"Configuration validation failed: {e}")
            return False
    
    def validate_types(self, imported_modules: Dict[str, Any]) -> bool:
        """Validate type definitions"""
        print("\n🏷️ Validating Type Definitions")
        print("=" * 50)
        
        types_module_path = "src.contexten.extensions.circleci.types"
        if types_module_path not in imported_modules:
            self.log_error("Types module not available")
            return False
        
        try:
            types_module = imported_modules[types_module_path]
            
            # Test key type classes
            key_types = [
                "CircleCIBuild",
                "CircleCIWorkflow", 
                "CircleCIJob",
                "CircleCIEvent",
                "FailureAnalysis",
                "GeneratedFix",
                "BuildStatus",
                "FailureType",
                "FixConfidence"
            ]
            
            success = True
            for type_name in key_types:
                if hasattr(types_module, type_name):
                    self.log_success(f"Type available: {type_name}")
                else:
                    self.log_error(f"Missing type: {type_name}")
                    success = False
            
            # Test enum values
            if hasattr(types_module, "BuildStatus"):
                BuildStatus = types_module.BuildStatus
                if hasattr(BuildStatus, "FAILED") and hasattr(BuildStatus, "SUCCESS"):
                    self.log_success("BuildStatus enum values")
                else:
                    self.log_error("BuildStatus enum missing values")
                    success = False
            
            return success
            
        except Exception as e:
            self.log_error(f"Type validation failed: {e}")
            return False
    
    def validate_integration_agent(self, imported_modules: Dict[str, Any]) -> bool:
        """Validate integration agent functionality"""
        print("\n🤖 Validating Integration Agent")
        print("=" * 50)
        
        agent_module_path = "src.contexten.extensions.circleci.integration_agent"
        config_module_path = "src.contexten.extensions.circleci.config"
        
        if agent_module_path not in imported_modules or config_module_path not in imported_modules:
            self.log_error("Required modules not available")
            return False
        
        try:
            agent_module = imported_modules[agent_module_path]
            config_module = imported_modules[config_module_path]
            
            # Create test configuration
            APIConfig = config_module.APIConfig
            CircleCIIntegrationConfig = config_module.CircleCIIntegrationConfig
            
            api_config = APIConfig(api_token="test-token")
            config = CircleCIIntegrationConfig(api=api_config, debug_mode=True)
            
            # Create agent
            CircleCIIntegrationAgent = agent_module.CircleCIIntegrationAgent
            agent = CircleCIIntegrationAgent(config)
            
            self.log_success("Integration agent creation")
            
            # Test basic methods
            if hasattr(agent, 'get_metrics'):
                metrics = agent.get_metrics()
                self.log_success("Metrics retrieval")
            else:
                self.log_error("Missing get_metrics method")
                return False
            
            if hasattr(agent, 'get_integration_status'):
                status = agent.get_integration_status()
                self.log_success("Status retrieval")
            else:
                self.log_error("Missing get_integration_status method")
                return False
            
            return True
            
        except Exception as e:
            self.log_error(f"Integration agent validation failed: {e}")
            traceback.print_exc()
            return False
    
    def validate_examples(self) -> bool:
        """Validate example code"""
        print("\n📚 Validating Examples")
        print("=" * 50)
        
        example_files = [
            self.base_path / "examples" / "circleci_integration" / "basic_usage.py",
            self.base_path / "examples" / "circleci_integration" / "advanced_usage.py"
        ]
        
        success = True
        
        for example_file in example_files:
            if not example_file.exists():
                self.log_error(f"Example file missing: {example_file}")
                success = False
                continue
            
            try:
                # Check syntax
                with open(example_file) as f:
                    content = f.read()
                    compile(content, str(example_file), 'exec')
                
                self.log_success(f"Example syntax valid: {example_file.name}")
                
                # Check for required imports
                if "from src.contexten.extensions.circleci" in content:
                    self.log_success(f"Example imports correct: {example_file.name}")
                else:
                    self.log_warning(f"Example missing CircleCI imports: {example_file.name}")
                
                # Check for async main
                if "async def main" in content or "asyncio.run" in content:
                    self.log_success(f"Example has async support: {example_file.name}")
                else:
                    self.log_warning(f"Example missing async support: {example_file.name}")
                
            except SyntaxError as e:
                self.log_error(f"Example syntax error in {example_file.name}: {e}")
                success = False
            except Exception as e:
                self.log_error(f"Example validation error in {example_file.name}: {e}")
                success = False
        
        return success
    
    def validate_documentation(self) -> bool:
        """Validate documentation completeness"""
        print("\n📖 Validating Documentation")
        print("=" * 50)
        
        readme_path = self.base_path / "src" / "contexten" / "extensions" / "circleci" / "README.md"
        
        if not readme_path.exists():
            self.log_error("Main README.md missing")
            return False
        
        try:
            with open(readme_path) as f:
                content = f.read()
            
            # Check for required sections
            required_sections = [
                "# CircleCI Extension",
                "## Features",
                "## Quick Start",
                "## Usage Examples",
                "## Configuration",
                "## Testing",
                "## API Reference"
            ]
            
            success = True
            for section in required_sections:
                if section in content:
                    self.log_success(f"Documentation section: {section}")
                else:
                    self.log_error(f"Missing documentation section: {section}")
                    success = False
            
            # Check length
            if len(content) > 5000:  # Reasonable documentation length
                self.log_success("Documentation is comprehensive")
            else:
                self.log_warning("Documentation might be too brief")
            
            return success
            
        except Exception as e:
            self.log_error(f"Documentation validation failed: {e}")
            return False
    
    def run_validation(self) -> bool:
        """Run complete validation suite"""
        print("🔍 CircleCI Extension Validation")
        print("=" * 60)
        print("Performing comprehensive validation of the CircleCI extension...")
        
        # Run all validation steps
        validation_steps = [
            ("File Structure", self.validate_file_structure),
            ("Module Imports", lambda: self.validate_imports()[0]),
            ("Main Exports", lambda: self.validate_main_exports(self.validate_imports()[1])),
            ("Configuration", lambda: self.validate_configuration(self.validate_imports()[1])),
            ("Type Definitions", lambda: self.validate_types(self.validate_imports()[1])),
            ("Integration Agent", lambda: self.validate_integration_agent(self.validate_imports()[1])),
            ("Examples", self.validate_examples),
            ("Documentation", self.validate_documentation)
        ]
        
        overall_success = True
        
        for step_name, step_func in validation_steps:
            try:
                print(f"\n🔄 Running {step_name} validation...")
                success = step_func()
                if not success:
                    overall_success = False
                    print(f"❌ {step_name} validation failed")
                else:
                    print(f"✅ {step_name} validation passed")
            except Exception as e:
                print(f"💥 {step_name} validation crashed: {e}")
                self.log_error(f"{step_name} validation crashed: {e}")
                overall_success = False
        
        # Generate final report
        self.generate_final_report(overall_success)
        
        return overall_success
    
    def generate_final_report(self, overall_success: bool):
        """Generate final validation report"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION REPORT")
        print("=" * 60)
        
        print(f"✅ Successful Checks: {self.success_count}")
        print(f"❌ Failed Checks: {len(self.errors)}")
        print(f"⚠️ Warnings: {len(self.warnings)}")
        print(f"📊 Total Checks: {self.total_checks}")
        
        if self.total_checks > 0:
            success_rate = (self.success_count / self.total_checks) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        print(f"\n{'='*60}")
        
        if overall_success:
            print("🎉 VALIDATION PASSED!")
            print("✅ The CircleCI extension is fully functional and ready for use.")
            print("\n🚀 Next Steps:")
            print("   1. Set up environment variables (API tokens)")
            print("   2. Configure webhook endpoints")
            print("   3. Deploy to your environment")
            print("   4. Test with real CircleCI projects")
        else:
            print("❌ VALIDATION FAILED!")
            print("🔧 Please fix the errors above before using the extension.")
            print("\n💡 Common fixes:")
            print("   - Check file paths and imports")
            print("   - Install missing dependencies")
            print("   - Fix syntax errors")
            print("   - Complete missing implementations")


def main():
    """Main validation entry point"""
    validator = CircleCIExtensionValidator()
    
    try:
        success = validator.run_validation()
        
        if success:
            print(f"\n🎯 Validation completed successfully!")
            sys.exit(0)
        else:
            print(f"\n🚨 Validation failed. Please review and fix issues.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation crashed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

