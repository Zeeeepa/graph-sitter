#!/usr/bin/env python3
"""
Intelligent PR Validator with Codegen Integration
This script combines graph-sitter structural validation with Codegen AI analysis
to provide comprehensive PR validation that checks both technical correctness
and code quality/architecture alignment.

Specifically adapted for the graph-sitter repository.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Import the base validator
from pr_validator import PRValidator, ValidationResult, ValidationSeverity

# Codegen imports
try:
    from codegen.agents.agent import Agent
    CODEGEN_AVAILABLE = True
except ImportError:
    print("⚠️ Codegen not available. Install with: pip install codegen")
    CODEGEN_AVAILABLE = False

# Graph-sitter imports
try:
    # Add the src directory to the path to import graph_sitter modules
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    
    from graph_sitter import Codebase
    from graph_sitter.core.class_definition import Class
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.function import Function
    from graph_sitter.core.symbol import Symbol

    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False


@dataclass
class IntelligentValidationResult:
    structural_validation: ValidationResult
    ai_validation: Optional[Dict] = None
    combined_score: float = 0.0
    recommendations: Optional[List[str]] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class IntelligentPRValidator:
    """Enhanced PR validator with AI-powered analysis"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.base_validator = PRValidator(repo_path)
        self.codebase: Optional[Codebase] = None

        # Codegen configuration
        self.org_id = os.getenv("CODEGEN_ORG_ID")
        self.api_token = os.getenv("CODEGEN_API_TOKEN")
        self.codegen_agent = None

        if CODEGEN_AVAILABLE and self.org_id and self.api_token:
            try:
                self.codegen_agent = Agent(org_id=self.org_id, token=self.api_token)
                print("✅ Codegen agent initialized")
            except Exception as e:
                print(f"⚠️ Could not initialize Codegen agent: {e}")

    def validate_pr_intelligent(
        self, pr_files: Optional[List[str]] = None
    ) -> IntelligentValidationResult:
        """Perform intelligent PR validation combining structural and AI analysis"""
        print("🧠 Starting intelligent PR validation...")

        # Step 1: Structural validation using graph-sitter
        print("🔍 Phase 1: Structural validation...")
        structural_result = self.base_validator.validate_pr(pr_files)

        # Step 2: AI-powered validation using Codegen
        ai_result = None
        if self.codegen_agent and GRAPH_SITTER_AVAILABLE:
            print("🤖 Phase 2: AI-powered validation...")
            ai_result = self._perform_ai_validation(pr_files, structural_result)
        else:
            print("⚠️ Skipping AI validation (Codegen not available)")

        # Step 3: Combine results and generate recommendations
        print("🎯 Phase 3: Generating recommendations...")
        combined_result = self._combine_results(structural_result, ai_result)

        return combined_result

    def _perform_ai_validation(
        self, pr_files: Optional[List[str]], structural_result: ValidationResult
    ) -> Dict:
        """Perform AI-powered validation using Codegen"""
        try:
            # Initialize codebase for analysis
            if not self.codebase:
                self.codebase = Codebase(str(self.repo_path))

            # Generate context for AI analysis
            context = self._generate_ai_context(pr_files, structural_result)

            # Create AI validation prompt
            prompt = self._create_ai_validation_prompt(context, structural_result)

            # Run Codegen analysis
            print("📤 Sending validation request to Codegen...")
            if self.codegen_agent is None:
                return {"status": "error", "error": "Codegen agent not initialized"}
            task = self.codegen_agent.run(prompt=prompt)

            # Wait for completion
            max_attempts = 30  # 5 minutes
            attempt = 0

            while attempt < max_attempts:
                task.refresh()

                if task.status == "completed":
                    print("✅ AI validation completed")
                    return {
                        "status": "completed",
                        "result": task.result,
                        "analysis": self._parse_ai_result(task.result),
                    }
                elif task.status == "failed":
                    print("❌ AI validation failed")
                    return {
                        "status": "failed",
                        "error": getattr(task, "error", "Unknown error"),
                    }

                attempt += 1
                time.sleep(10)

            print("⏰ AI validation timed out")
            return {"status": "timeout"}

        except Exception as e:
            print(f"❌ Error in AI validation: {e}")
            return {"status": "error", "error": str(e)}

    def _generate_ai_context(
        self, pr_files: Optional[List[str]], structural_result: ValidationResult
    ) -> Dict:
        """Generate context for AI analysis"""
        context = {
            "changed_files": pr_files or [],
            "structural_issues": len(structural_result.issues),
            "error_count": structural_result.summary.get("errors", 0),
            "warning_count": structural_result.summary.get("warnings", 0),
            "file_analysis": {},
            "symbol_analysis": {},
            "repository_type": "graph-sitter",
        }

        if not self.codebase:
            return context

        # Analyze changed files
        for file_path in context["changed_files"]:
            source_file = self._find_source_file(file_path)
            if source_file:
                context["file_analysis"][file_path] = {
                    "functions": len(source_file.functions)
                    if hasattr(source_file, "functions")
                    else 0,
                    "classes": len(source_file.classes)
                    if hasattr(source_file, "classes")
                    else 0,
                    "imports": len(source_file.imports)
                    if hasattr(source_file, "imports")
                    else 0,
                }

                # Analyze key symbols
                if hasattr(source_file, "functions"):
                    for func in source_file.functions[:3]:  # Top 3 functions
                        context["symbol_analysis"][f"{file_path}::{func.name}"] = {
                            "type": "function",
                            "call_sites": len(func.call_sites)
                            if hasattr(func, "call_sites")
                            else 0,
                            "parameters": len(func.parameters)
                            if hasattr(func, "parameters")
                            else 0,
                        }

                if hasattr(source_file, "classes"):
                    for cls in source_file.classes[:2]:  # Top 2 classes
                        context["symbol_analysis"][f"{file_path}::{cls.name}"] = {
                            "type": "class",
                            "methods": len(cls.methods)
                            if hasattr(cls, "methods")
                            else 0,
                            "usages": len(cls.symbol_usages)
                            if hasattr(cls, "symbol_usages")
                            else 0,
                        }

        return context

    def _create_ai_validation_prompt(
        self, context: Dict, structural_result: ValidationResult
    ) -> str:
        """Create prompt for AI validation"""

        # Format structural issues
        issues_summary = ""
        if structural_result.issues:
            issues_by_category: Dict[str, List[ValidationIssue]] = {}
            for issue in structural_result.issues[:10]:  # Top 10 issues
                category = issue.category
                if category not in issues_by_category:
                    issues_by_category[category] = []
                issues_by_category[category].append(issue)

            for category, issues in issues_by_category.items():
                issues_summary += f"\n### {category.replace('_', ' ').title()}\n"
                for issue in issues:
                    issues_summary += f"- {issue.severity.value.upper()}: {issue.message} ({issue.file_path})\n"

        prompt = f"""
🔍 Intelligent PR Validation Request for Graph-Sitter Repository

Please perform a comprehensive analysis of this PR's code changes and provide validation insights specifically for the graph-sitter codebase.

📊 **Repository Context:**
- Repository: graph-sitter (Python code analysis and manipulation library)
- Focus: Code graph analysis, AST manipulation, codebase understanding
- Key Technologies: Python, Tree-sitter, Rust bindings, Graph analysis

📊 **Structural Analysis Results Summary:**
- Changed files: {len(context["changed_files"])}
- Structural issues found: {context["structural_issues"]}
- Errors: {context["error_count"]}
- Warnings: {context["warning_count"]}

**Changed Files:**
{chr(10).join(f"- {file}" for file in context["changed_files"])}

**File Analysis:**
{json.dumps(context["file_analysis"], indent=2)}

**Key Symbols Analysis:**
{json.dumps(context["symbol_analysis"], indent=2)}

⚠️ **Structural Issues Detected:**
{issues_summary}

🎯 **Validation Tasks**

Please analyze the PR changes and provide:

1. **Code Quality Assessment**
   - Evaluate the overall code quality of the changes
   - Identify potential maintainability issues
   - Assess adherence to Python and graph-sitter best practices

2. **Graph-Sitter Specific Analysis**
   - Analyze impact on graph construction and manipulation
   - Check for proper codebase context usage
   - Validate graph traversal and analysis patterns
   - Assess performance implications for large codebases

3. **Architecture & Integration Review**
   - Analyze how changes affect the overall graph-sitter architecture
   - Identify potential design pattern violations
   - Assess impact on existing graph analysis components
   - Check for proper separation of concerns

4. **Performance & Scalability**
   - Identify potential performance bottlenecks in graph operations
   - Assess memory usage implications
   - Check for efficient graph traversal patterns
   - Validate caching and optimization strategies

5. **API & Compatibility**
   - Verify changes maintain API compatibility
   - Check for breaking changes in public interfaces
   - Assess impact on existing graph-sitter users
   - Validate backward compatibility

6. **Testing & Documentation**
   - Evaluate test coverage for graph analysis changes
   - Check if documentation needs updates
   - Identify missing test scenarios for graph operations

📝 **Required Output Format**

Please provide your analysis in this JSON format:

{{
  "overall_score": 85,
  "validation_status": "PASSED_WITH_RECOMMENDATIONS",
  "categories": {{
    "code_quality": {{"score": 90, "issues": ["issue1", "issue2"]}},
    "graph_sitter_specific": {{"score": 85, "issues": []}},
    "architecture": {{"score": 85, "issues": []}},
    "performance": {{"score": 80, "issues": ["potential issue"]}},
    "api_compatibility": {{"score": 90, "issues": []}},
    "testing": {{"score": 70, "issues": ["missing tests"]}}
  }},
  "recommendations": [
    "Add unit tests for new graph analysis functions",
    "Consider extracting complex graph traversal logic into separate methods",
    "Update documentation for API changes",
    "Optimize graph construction for large codebases"
  ],
  "critical_issues": [],
  "approval_recommendation": "APPROVE_WITH_SUGGESTIONS"
}}

🎯 **Focus Areas for Graph-Sitter Repository**

Based on the structural analysis, please pay special attention to:

- **Graph Construction**: Functions that build or modify the code graph
- **Symbol Resolution**: Import and dependency resolution mechanisms  
- **Performance**: Graph traversal and analysis efficiency
- **Memory Management**: Proper cleanup of graph resources
- **API Consistency**: Maintaining consistent interfaces for graph operations
- **Error Handling**: Robust error handling for graph operations
- **Codebase Context**: Proper usage of codebase context and transaction management

Provide specific, actionable feedback that helps improve the PR quality while maintaining the high standards expected for a code analysis library.
"""

        return prompt

    def _parse_ai_result(self, ai_result: str) -> Dict:
        """Parse AI validation result"""
        try:
            # Try to extract JSON from the result
            import re

            json_match = re.search(r"```json\s*(\{.*?\})\s*```", ai_result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Fallback: try to parse the entire result as JSON
            return json.loads(ai_result)
        except Exception as e:
            print(f"⚠️ Could not parse AI result as JSON: {e}")
            return {
                "overall_score": 50,
                "validation_status": "ANALYSIS_ERROR",
                "raw_result": ai_result,
                "recommendations": ["Could not parse AI analysis result"],
            }

    def _combine_results(
        self, structural_result: ValidationResult, ai_result: Optional[Dict]
    ) -> IntelligentValidationResult:
        """Combine structural and AI validation results"""
        combined = IntelligentValidationResult(
            structural_validation=structural_result, ai_validation=ai_result
        )

        # Calculate combined score
        structural_score = self._calculate_structural_score(structural_result)
        ai_score = 50  # Default if AI not available

        if ai_result and ai_result.get("status") == "completed":
            analysis = ai_result.get("analysis", {})
            ai_score = analysis.get("overall_score", 50)

            # Extract recommendations
            if "recommendations" in analysis:
                combined.recommendations.extend(analysis["recommendations"])

        # Weight: 60% structural, 40% AI (if available)
        if ai_result and ai_result.get("status") == "completed":
            combined.combined_score = (structural_score * 0.6) + (ai_score * 0.4)
        else:
            combined.combined_score = structural_score

        # Add structural recommendations
        if structural_result.summary.get("errors", 0) > 0:
            combined.recommendations.append("Fix all structural errors before merging")

        if structural_result.summary.get("warnings", 0) > 5:
            combined.recommendations.append("Consider addressing structural warnings")

        # Add graph-sitter specific recommendations
        if any("graph" in issue.category.lower() for issue in structural_result.issues):
            combined.recommendations.append("Review graph-sitter specific patterns and optimizations")

        return combined

    def _calculate_structural_score(self, result: ValidationResult) -> float:
        """Calculate score based on structural validation"""
        if not result.issues:
            return 100.0

        error_count = result.summary.get("errors", 0)
        warning_count = result.summary.get("warnings", 0)
        info_count = result.summary.get("infos", 0)

        # Scoring: Start at 100, deduct points for issues
        score = 100.0
        score -= error_count * 20  # 20 points per error
        score -= warning_count * 5  # 5 points per warning
        score -= info_count * 1  # 1 point per info

        return max(0.0, score)

    def _find_source_file(self, file_path: str) -> Optional[SourceFile]:
        """Find source file in codebase"""
        if not self.codebase:
            return None

        for file in self.codebase.files:
            if hasattr(file, "path") and str(file.path).endswith(file_path):
                return file
        return None


def generate_intelligent_report(result: IntelligentValidationResult) -> str:
    """Generate comprehensive intelligent validation report"""

    # Determine overall status
    if result.combined_score >= 90:
        status_icon = "✅"
        status_text = "EXCELLENT"
    elif result.combined_score >= 75:
        status_icon = "🟢"
        status_text = "GOOD"
    elif result.combined_score >= 60:
        status_icon = "🟡"
        status_text = "NEEDS IMPROVEMENT"
    else:
        status_icon = "🔴"
        status_text = "REQUIRES FIXES"

    report = f"""# 🧠 Intelligent PR Validation Report

{status_icon} **Overall Assessment: {status_text}**
**Combined Score: {result.combined_score:.1f}/100**

## 📊 Validation Summary

### 🔍 Structural Analysis
- Status: {"✅ PASSED" if result.structural_validation.is_valid else "❌ FAILED"}
- Issues Found: {len(result.structural_validation.issues)}
- Errors: {result.structural_validation.summary.get("errors", 0)}
- Warnings: {result.structural_validation.summary.get("warnings", 0)}

### 🤖 AI Analysis
"""

    if result.ai_validation:
        if result.ai_validation.get("status") == "completed":
            analysis = result.ai_validation.get("analysis", {})
            report += f"""- Status: ✅ COMPLETED
- AI Score: {analysis.get("overall_score", "N/A")}/100
- Validation Status: {analysis.get("validation_status", "Unknown")}
- Approval Recommendation: {analysis.get("approval_recommendation", "Unknown")}
"""

            # Add category scores if available
            if "categories" in analysis:
                report += "\n#### Category Scores\n"
                for category, data in analysis["categories"].items():
                    score = data.get("score", 0)
                    issues_count = len(data.get("issues", []))
                    report += f"- **{category.replace('_', ' ').title()}**: {score}/100"
                    if issues_count > 0:
                        report += f" ({issues_count} issues)"
                    report += "\n"
        else:
            status = result.ai_validation.get("status", "unknown")
            report += f"- Status: ⚠️ {status.upper()}\n"
            if "error" in result.ai_validation:
                report += f"- Error: {result.ai_validation['error']}\n"
    else:
        report += "- Status: ⚠️ NOT AVAILABLE\n"

    # Add recommendations
    if result.recommendations:
        report += "\n## 💡 Recommendations\n"
        for i, rec in enumerate(result.recommendations, 1):
            report += f"{i}. {rec}\n"

    # Add detailed structural issues
    if result.structural_validation.issues:
        report += "\n## 🔍 Detailed Issues\n"

        # Group by category
        categories: Dict[str, List[ValidationIssue]] = {}
        for issue in result.structural_validation.issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)

        for category, issues in categories.items():
            report += f"\n### {category.replace('_', ' ').title()}\n"
            for issue in issues:
                severity_icon = {
                    ValidationSeverity.ERROR: "❌",
                    ValidationSeverity.WARNING: "⚠️",
                    ValidationSeverity.INFO: "ℹ️",
                }[issue.severity]

                report += f"- {severity_icon} **{issue.file_path}**"
                if issue.line_number:
                    report += f":{issue.line_number}"
                if issue.symbol_name:
                    report += f" ({issue.symbol_name})"
                report += f": {issue.message}\n"

                if issue.suggestion:
                    report += f"  💡 *{issue.suggestion}*\n"

    # Add AI detailed analysis if available
    if (
        result.ai_validation
        and result.ai_validation.get("status") == "completed"
        and "raw_result" in result.ai_validation.get("analysis", {})
    ):
        report += "\n## 🤖 AI Analysis Details\n"
        report += result.ai_validation["analysis"]["raw_result"]

    report += f"\n---\n**Report generated at:** {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"

    return report


def main():
    """Main function for intelligent PR validation"""
    print("🧠 Intelligent PR Validator with AI Integration")
    print("=" * 60)

    # Get environment variables
    repo_path = os.getenv("GITHUB_WORKSPACE", ".")
    pr_number = os.getenv("GITHUB_PR_NUMBER")

    # Check for Codegen credentials
    if not os.getenv("CODEGEN_ORG_ID") or not os.getenv("CODEGEN_API_TOKEN"):
        print("⚠️ Codegen credentials not found. Running structural validation only.")

    # Initialize intelligent validator
    validator = IntelligentPRValidator(repo_path)

    # Run intelligent validation
    result = validator.validate_pr_intelligent()

    # Generate report
    report = generate_intelligent_report(result)
    print(report)

    # Save reports
    with open("intelligent_validation_report.md", "w") as f:
        f.write(report)

    with open("intelligent_validation_result.json", "w") as f:
        json.dump(
            {
                "combined_score": result.combined_score,
                "is_valid": result.structural_validation.is_valid,
                "structural_summary": result.structural_validation.summary,
                "ai_status": result.ai_validation.get("status") if result.ai_validation else None,
                "recommendations": result.recommendations,
                "issues": [
                    asdict(issue) for issue in result.structural_validation.issues
                ],
            },
            f,
            indent=2,
            default=str,
        )

    # Determine exit code based on combined score
    if result.combined_score >= 75:
        print(
            f"\n✅ Intelligent validation passed! Score: {result.combined_score:.1f}/100"
        )
        sys.exit(0)
    else:
        print(
            f"\n❌ Intelligent validation failed. Score: {result.combined_score:.1f}/100"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
