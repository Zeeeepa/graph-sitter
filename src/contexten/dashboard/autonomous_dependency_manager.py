"""
Autonomous Dependency Manager for Dashboard Integration

This module provides intelligent dependency management capabilities
integrated with the dashboard monitoring system.
"""

import asyncio
import json
import os
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import requests
from codegen import Agent

logger = logging.getLogger(__name__)


@dataclass
class DependencyUpdate:
    """Represents a potential dependency update"""
    name: str
    current_version: str
    latest_version: str
    update_type: str  # major, minor, patch
    security_impact: str  # critical, high, medium, low, none
    compatibility_risk: str  # high, medium, low
    changelog_summary: str
    breaking_changes: List[str]
    recommended_action: str
    confidence_score: float
    auto_fixable: bool
    created_at: datetime


@dataclass
class SecurityVulnerability:
    """Represents a security vulnerability in dependencies"""
    id: str
    package_name: str
    affected_versions: List[str]
    severity: str
    description: str
    cve_id: Optional[str]
    fixed_version: Optional[str]
    published_date: datetime
    discovered_date: datetime


@dataclass
class DependencyAnalysisResult:
    """Result of dependency analysis"""
    total_dependencies: int
    outdated_dependencies: int
    security_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    updates_available: List[DependencyUpdate]
    vulnerabilities: List[SecurityVulnerability]
    analysis_timestamp: datetime
    next_scan_scheduled: datetime


class AutonomousDependencyManager:
    """AI-powered dependency management system integrated with dashboard"""
    
    def __init__(self, codegen_org_id: str, codegen_token: str, project_path: str = "."):
        self.codegen_agent = Agent(
            org_id=codegen_org_id,
            token=codegen_token
        )
        self.project_path = Path(project_path)
        
        # Configuration from environment
        self.scan_enabled = os.getenv("DEPENDENCY_SCAN_ENABLED", "true").lower() == "true"
        self.scan_interval = int(os.getenv("DEPENDENCY_SCAN_INTERVAL", "86400"))  # 24 hours
        self.security_scan_enabled = os.getenv("DEPENDENCY_SECURITY_SCAN_ENABLED", "true").lower() == "true"
        self.auto_update_enabled = os.getenv("DEPENDENCY_AUTO_UPDATE_ENABLED", "false").lower() == "true"
        self.update_strategy = os.getenv("DEPENDENCY_UPDATE_STRATEGY", "smart")
        self.security_priority = os.getenv("SECURITY_UPDATE_PRIORITY", "high")
        self.auto_fix_confidence_threshold = float(os.getenv("AUTO_FIX_CONFIDENCE_THRESHOLD", "0.7"))
        
        # Security settings
        self.security_critical_auto_fix = os.getenv("SECURITY_CRITICAL_AUTO_FIX", "false").lower() == "true"
        self.security_high_auto_fix = os.getenv("SECURITY_HIGH_AUTO_FIX", "false").lower() == "true"
        
        # Compatibility settings
        self.compatibility_analysis_enabled = os.getenv("COMPATIBILITY_ANALYSIS_ENABLED", "true").lower() == "true"
        self.compatibility_risk_threshold = os.getenv("COMPATIBILITY_RISK_THRESHOLD", "medium")
        self.breaking_change_detection = os.getenv("BREAKING_CHANGE_DETECTION", "true").lower() == "true"
        
        # Internal state
        self.last_scan_time: Optional[datetime] = None
        self.scan_results: Optional[DependencyAnalysisResult] = None
        self.known_patterns = self._load_known_patterns()
        
        # Callbacks for dashboard integration
        self.update_callbacks: List[callable] = []
        self.vulnerability_callbacks: List[callable] = []
    
    def _load_known_patterns(self) -> Dict[str, Any]:
        """Load known dependency patterns and compatibility rules"""
        return {
            'high_risk_packages': [
                'pillow', 'requests', 'urllib3', 'pyyaml', 'jinja2'
            ],
            'breaking_change_indicators': [
                'removed', 'deprecated', 'breaking', 'incompatible', 'major'
            ],
            'security_keywords': [
                'security', 'vulnerability', 'cve', 'exploit', 'patch'
            ]
        }
    
    async def analyze_dependencies(self, force_scan: bool = False) -> DependencyAnalysisResult:
        """Analyze all dependencies for updates and security issues"""
        
        if not self.scan_enabled and not force_scan:
            logger.info("Dependency scanning is disabled")
            return self._get_empty_result()
        
        # Check if scan is needed
        if not force_scan and self._is_recent_scan():
            logger.info("Recent scan available, skipping analysis")
            return self.scan_results
        
        logger.info("🔍 Starting dependency analysis...")
        
        try:
            # Get current dependencies
            dependencies = await self._get_current_dependencies()
            
            # Analyze each dependency
            updates = []
            vulnerabilities = []
            
            for dep_name, current_version in dependencies.items():
                # Check for updates
                update = await self._analyze_single_dependency(dep_name, current_version)
                if update:
                    updates.append(update)
                
                # Check for security vulnerabilities
                vulns = await self._check_security_vulnerabilities(dep_name, current_version)
                vulnerabilities.extend(vulns)
            
            # Use AI to prioritize and assess updates
            if updates:
                updates = await self._ai_prioritize_updates(updates)
            
            # Create analysis result
            result = DependencyAnalysisResult(
                total_dependencies=len(dependencies),
                outdated_dependencies=len(updates),
                security_vulnerabilities=len(vulnerabilities),
                critical_vulnerabilities=len([v for v in vulnerabilities if v.severity == 'critical']),
                high_vulnerabilities=len([v for v in vulnerabilities if v.severity == 'high']),
                updates_available=updates,
                vulnerabilities=vulnerabilities,
                analysis_timestamp=datetime.now(),
                next_scan_scheduled=datetime.now() + timedelta(seconds=self.scan_interval)
            )
            
            self.scan_results = result
            self.last_scan_time = datetime.now()
            
            # Notify callbacks
            await self._notify_callbacks(result)
            
            logger.info(f"✅ Dependency analysis complete: {len(updates)} updates, {len(vulnerabilities)} vulnerabilities")
            return result
            
        except Exception as e:
            logger.error(f"❌ Dependency analysis failed: {e}")
            return self._get_empty_result()
    
    async def _get_current_dependencies(self) -> Dict[str, str]:
        """Extract current dependencies from pyproject.toml and requirements files"""
        
        dependencies = {}
        
        # Try pyproject.toml first
        pyproject_path = self.project_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomli
                with open(pyproject_path, 'rb') as f:
                    data = tomli.load(f)
                
                # Extract dependencies
                deps = data.get('project', {}).get('dependencies', [])
                for dep in deps:
                    if '==' in dep:
                        name, version = dep.split('==', 1)
                        dependencies[name.strip()] = version.strip()
                    elif '>=' in dep:
                        name = dep.split('>=')[0].strip()
                        dependencies[name] = "latest"
                
            except Exception as e:
                logger.warning(f"Failed to parse pyproject.toml: {e}")
        
        # Try requirements.txt
        requirements_path = self.project_path / "requirements.txt"
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '==' in line:
                                name, version = line.split('==', 1)
                                dependencies[name.strip()] = version.strip()
                            elif '>=' in line:
                                name = line.split('>=')[0].strip()
                                dependencies[name] = "latest"
            except Exception as e:
                logger.warning(f"Failed to parse requirements.txt: {e}")
        
        return dependencies
    
    async def _analyze_single_dependency(self, name: str, current_version: str) -> Optional[DependencyUpdate]:
        """Analyze a single dependency for updates"""
        
        try:
            # Get latest version from PyPI
            response = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            latest_version = data['info']['version']
            
            if current_version == latest_version or current_version == "latest":
                return None  # No update needed
            
            # Determine update type
            update_type = self._classify_update_type(current_version, latest_version)
            
            # Check security impact
            security_impact = await self._check_security_impact(name, current_version, latest_version)
            
            # Assess compatibility risk
            compatibility_risk = await self._assess_compatibility_risk(name, current_version, latest_version, data)
            
            # Get changelog summary
            changelog_summary = await self._get_changelog_summary(name, current_version, latest_version, data)
            
            # Detect breaking changes
            breaking_changes = await self._detect_breaking_changes(name, current_version, latest_version, data)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(update_type, security_impact, compatibility_risk)
            
            # Determine if auto-fixable
            auto_fixable = self._is_auto_fixable(update_type, security_impact, compatibility_risk, confidence_score)
            
            return DependencyUpdate(
                name=name,
                current_version=current_version,
                latest_version=latest_version,
                update_type=update_type,
                security_impact=security_impact,
                compatibility_risk=compatibility_risk,
                changelog_summary=changelog_summary,
                breaking_changes=breaking_changes,
                recommended_action="analyze",
                confidence_score=confidence_score,
                auto_fixable=auto_fixable,
                created_at=datetime.now()
            )
        
        except Exception as e:
            logger.warning(f"Error analyzing {name}: {e}")
            return None
    
    def _classify_update_type(self, current: str, latest: str) -> str:
        """Classify update as major, minor, or patch"""
        
        try:
            if current == "latest":
                return "unknown"
            
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            if latest_parts[0] > current_parts[0]:
                return "major"
            elif latest_parts[1] > current_parts[1]:
                return "minor"
            elif latest_parts[2] > current_parts[2]:
                return "patch"
            else:
                return "unknown"
        
        except (ValueError, IndexError):
            return "unknown"
    
    async def _check_security_impact(self, name: str, current: str, latest: str) -> str:
        """Check if update addresses security vulnerabilities"""
        
        if not self.security_scan_enabled:
            return "none"
        
        try:
            # Check GitHub Security Advisories
            response = requests.get(
                f"https://api.github.com/advisories?ecosystem=pip&package={name}",
                timeout=10
            )
            
            if response.status_code == 200:
                advisories = response.json()
                for advisory in advisories:
                    severity = advisory.get('severity', '').lower()
                    if severity in ['critical', 'high']:
                        return severity
            
            # Use pip-audit for additional security checking
            try:
                result = subprocess.run(
                    ['pip-audit', '--format=json', '--requirement', '/dev/stdin'],
                    input=f"{name}=={current}",
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    audit_data = json.loads(result.stdout)
                    if audit_data.get('vulnerabilities'):
                        return 'high'
            except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
                pass
        
        except Exception:
            pass
        
        return "none"
    
    async def _check_security_vulnerabilities(self, name: str, version: str) -> List[SecurityVulnerability]:
        """Check for security vulnerabilities in a specific package version"""
        
        vulnerabilities = []
        
        if not self.security_scan_enabled:
            return vulnerabilities
        
        try:
            # Check GitHub Security Advisories
            response = requests.get(
                f"https://api.github.com/advisories?ecosystem=pip&package={name}",
                timeout=10
            )
            
            if response.status_code == 200:
                advisories = response.json()
                for advisory in advisories:
                    vuln = SecurityVulnerability(
                        id=advisory.get('ghsa_id', f"vuln_{name}_{datetime.now().timestamp()}"),
                        package_name=name,
                        affected_versions=[version],
                        severity=advisory.get('severity', 'unknown').lower(),
                        description=advisory.get('summary', 'Security vulnerability detected'),
                        cve_id=advisory.get('cve_id'),
                        fixed_version=None,  # Would need to parse from advisory
                        published_date=datetime.fromisoformat(advisory.get('published_at', datetime.now().isoformat()).replace('Z', '+00:00')),
                        discovered_date=datetime.now()
                    )
                    vulnerabilities.append(vuln)
        
        except Exception as e:
            logger.warning(f"Failed to check vulnerabilities for {name}: {e}")
        
        return vulnerabilities
    
    async def _assess_compatibility_risk(self, name: str, current: str, latest: str, pypi_data: Dict) -> str:
        """Assess compatibility risk of the update"""
        
        if not self.compatibility_analysis_enabled:
            return "unknown"
        
        update_type = self._classify_update_type(current, latest)
        
        # Major updates have high risk by default
        if update_type == "major":
            return "high"
        
        # Check if package is in high-risk list
        if name in self.known_patterns.get('high_risk_packages', []):
            return "medium" if update_type == "minor" else "high"
        
        # Check changelog for breaking change indicators
        description = pypi_data.get('info', {}).get('description', '').lower()
        for indicator in self.known_patterns.get('breaking_change_indicators', []):
            if indicator in description:
                return "high" if update_type == "major" else "medium"
        
        # Default risk assessment
        risk_map = {
            "major": "high",
            "minor": "medium",
            "patch": "low",
            "unknown": "medium"
        }
        
        return risk_map.get(update_type, "medium")
    
    async def _get_changelog_summary(self, name: str, current: str, latest: str, pypi_data: Dict) -> str:
        """Get a summary of changes between versions"""
        
        try:
            description = pypi_data.get('info', {}).get('description', '')
            if len(description) > 300:
                description = description[:300] + "..."
            
            # Look for release notes or changelog
            project_urls = pypi_data.get('info', {}).get('project_urls', {})
            changelog_url = None
            
            for key, url in project_urls.items():
                if any(word in key.lower() for word in ['changelog', 'changes', 'history', 'releases']):
                    changelog_url = url
                    break
            
            summary = f"Update from {current} to {latest}"
            if description:
                summary += f". {description}"
            if changelog_url:
                summary += f" See: {changelog_url}"
            
            return summary
        
        except Exception:
            return f"Update from {current} to {latest}"
    
    async def _detect_breaking_changes(self, name: str, current: str, latest: str, pypi_data: Dict) -> List[str]:
        """Detect potential breaking changes"""
        
        breaking_changes = []
        
        if not self.breaking_change_detection:
            return breaking_changes
        
        update_type = self._classify_update_type(current, latest)
        
        # Major version updates likely have breaking changes
        if update_type == "major":
            breaking_changes.append("Major version update - likely contains breaking changes")
        
        # Check description for breaking change indicators
        description = pypi_data.get('info', {}).get('description', '').lower()
        for indicator in self.known_patterns.get('breaking_change_indicators', []):
            if indicator in description:
                breaking_changes.append(f"Potential breaking change detected: {indicator}")
        
        return breaking_changes
    
    def _calculate_confidence_score(self, update_type: str, security_impact: str, compatibility_risk: str) -> float:
        """Calculate confidence score for the update recommendation"""
        
        base_score = 0.5
        
        # Security impact increases confidence
        security_boost = {
            'critical': 0.4,
            'high': 0.3,
            'medium': 0.1,
            'low': 0.05,
            'none': 0.0
        }
        base_score += security_boost.get(security_impact, 0.0)
        
        # Update type affects confidence
        update_penalty = {
            'patch': 0.0,
            'minor': -0.1,
            'major': -0.3,
            'unknown': -0.2
        }
        base_score += update_penalty.get(update_type, -0.1)
        
        # Compatibility risk reduces confidence
        risk_penalty = {
            'low': 0.0,
            'medium': -0.2,
            'high': -0.4,
            'unknown': -0.1
        }
        base_score += risk_penalty.get(compatibility_risk, -0.1)
        
        return max(0.0, min(1.0, base_score))
    
    def _is_auto_fixable(self, update_type: str, security_impact: str, compatibility_risk: str, confidence_score: float) -> bool:
        """Determine if update can be automatically applied"""
        
        if not self.auto_update_enabled:
            return False
        
        # High confidence threshold
        if confidence_score < self.auto_fix_confidence_threshold:
            return False
        
        # Security fixes with low risk
        if security_impact in ['critical', 'high'] and compatibility_risk == 'low':
            return self.security_critical_auto_fix if security_impact == 'critical' else self.security_high_auto_fix
        
        # Patch updates with low risk
        if update_type == 'patch' and compatibility_risk == 'low':
            return True
        
        return False
    
    async def _ai_prioritize_updates(self, updates: List[DependencyUpdate]) -> List[DependencyUpdate]:
        """Use AI to prioritize and assess dependency updates"""
        
        if not updates:
            return []
        
        try:
            # Build analysis prompt
            updates_data = [
                {
                    'name': update.name,
                    'current_version': update.current_version,
                    'latest_version': update.latest_version,
                    'update_type': update.update_type,
                    'security_impact': update.security_impact,
                    'compatibility_risk': update.compatibility_risk,
                    'confidence_score': update.confidence_score,
                    'auto_fixable': update.auto_fixable
                }
                for update in updates
            ]
            
            analysis_prompt = f"""
Analyze these dependency updates for a Python project (graph-sitter) and provide intelligent recommendations:

DEPENDENCY UPDATES:
{json.dumps(updates_data, indent=2)}

PROJECT CONTEXT:
- This is a critical code analysis library
- Stability is paramount
- Security updates are high priority
- Breaking changes need careful evaluation
- The project uses Cython extensions

For each dependency, provide:
1. Recommended action (update_immediately, update_with_testing, defer, skip)
2. Priority level (critical, high, medium, low)
3. Rationale for the recommendation
4. Testing strategy

Respond in JSON format:
{{
    "recommendations": [
        {{
            "name": "dependency_name",
            "action": "update_immediately|update_with_testing|defer|skip",
            "priority": "critical|high|medium|low",
            "rationale": "explanation",
            "testing_strategy": "description"
        }}
    ],
    "overall_strategy": "description"
}}
"""
            
            task = self.codegen_agent.run(prompt=analysis_prompt)
            
            # Wait for analysis with timeout
            timeout_count = 0
            while task.status not in ['completed', 'failed'] and timeout_count < 30:
                await asyncio.sleep(2)
                task.refresh()
                timeout_count += 1
            
            if task.status == 'completed':
                # Parse AI recommendations
                try:
                    import re
                    json_match = re.search(r'\{.*\}', task.result, re.DOTALL)
                    if json_match:
                        recommendations = json.loads(json_match.group())
                        
                        # Apply AI recommendations to updates
                        for update in updates:
                            for rec in recommendations.get('recommendations', []):
                                if rec['name'] == update.name:
                                    update.recommended_action = rec['action']
                                    break
                
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse AI recommendations: {e}")
            
            else:
                logger.warning(f"AI analysis failed or timed out: {task.status}")
        
        except Exception as e:
            logger.error(f"AI prioritization failed: {e}")
        
        return updates
    
    def _is_recent_scan(self) -> bool:
        """Check if a recent scan is available"""
        if not self.last_scan_time:
            return False
        
        time_since_scan = datetime.now() - self.last_scan_time
        return time_since_scan.total_seconds() < self.scan_interval
    
    def _get_empty_result(self) -> DependencyAnalysisResult:
        """Get empty analysis result"""
        return DependencyAnalysisResult(
            total_dependencies=0,
            outdated_dependencies=0,
            security_vulnerabilities=0,
            critical_vulnerabilities=0,
            high_vulnerabilities=0,
            updates_available=[],
            vulnerabilities=[],
            analysis_timestamp=datetime.now(),
            next_scan_scheduled=datetime.now() + timedelta(seconds=self.scan_interval)
        )
    
    async def _notify_callbacks(self, result: DependencyAnalysisResult):
        """Notify registered callbacks about analysis results"""
        for callback in self.update_callbacks:
            try:
                await callback(result)
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
        
        # Notify about critical vulnerabilities
        critical_vulns = [v for v in result.vulnerabilities if v.severity == 'critical']
        if critical_vulns:
            for callback in self.vulnerability_callbacks:
                try:
                    await callback(critical_vulns)
                except Exception as e:
                    logger.error(f"Error in vulnerability callback: {e}")
    
    # Public API methods
    
    def add_update_callback(self, callback: callable):
        """Add callback for dependency update notifications"""
        self.update_callbacks.append(callback)
    
    def add_vulnerability_callback(self, callback: callable):
        """Add callback for security vulnerability notifications"""
        self.vulnerability_callbacks.append(callback)
    
    def get_last_scan_result(self) -> Optional[DependencyAnalysisResult]:
        """Get the last scan result"""
        return self.scan_results
    
    def get_scan_status(self) -> Dict[str, Any]:
        """Get current scan status"""
        return {
            "scan_enabled": self.scan_enabled,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "next_scan_scheduled": (datetime.now() + timedelta(seconds=self.scan_interval)).isoformat(),
            "auto_update_enabled": self.auto_update_enabled,
            "security_scan_enabled": self.security_scan_enabled
        }
    
    async def apply_updates(self, update_names: List[str], strategy: str = "smart") -> Dict[str, Any]:
        """Apply selected dependency updates"""
        
        if not self.scan_results:
            return {"error": "No scan results available"}
        
        # Filter updates to apply
        updates_to_apply = [
            update for update in self.scan_results.updates_available
            if update.name in update_names
        ]
        
        if not updates_to_apply:
            return {"error": "No matching updates found"}
        
        # Create update prompt for Codegen AI
        update_prompt = f"""
Apply these dependency updates to the graph-sitter project:

UPDATES TO APPLY:
{json.dumps([{
    'name': u.name,
    'current': u.current_version,
    'latest': u.latest_version,
    'action': u.recommended_action,
    'security_impact': u.security_impact,
    'confidence_score': u.confidence_score
} for u in updates_to_apply], indent=2)}

Please:
1. Update pyproject.toml or requirements.txt with new versions
2. Run tests to ensure compatibility
3. Create a PR with detailed changelog
4. Include any necessary code changes for compatibility

Strategy: {strategy}

Create PR with title: "🤖 Autonomous dependency updates - {len(updates_to_apply)} packages"
"""
        
        try:
            task = self.codegen_agent.run(prompt=update_prompt)
            
            # Wait for completion with timeout
            timeout_count = 0
            while task.status not in ['completed', 'failed'] and timeout_count < 60:
                await asyncio.sleep(5)
                task.refresh()
                timeout_count += 1
            
            if task.status == 'completed':
                return {
                    "success": True,
                    "message": "Updates applied successfully",
                    "result": task.result,
                    "updates_applied": len(updates_to_apply)
                }
            else:
                return {
                    "success": False,
                    "error": f"Update failed: {task.result}",
                    "updates_attempted": len(updates_to_apply)
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Update process failed: {str(e)}",
                "updates_attempted": len(updates_to_apply)
            }
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dependency data for dashboard display"""
        
        if not self.scan_results:
            await self.analyze_dependencies()
        
        if not self.scan_results:
            return {"error": "No dependency data available"}
        
        result = self.scan_results
        
        return {
            "summary": {
                "total_dependencies": result.total_dependencies,
                "outdated_dependencies": result.outdated_dependencies,
                "security_vulnerabilities": result.security_vulnerabilities,
                "critical_vulnerabilities": result.critical_vulnerabilities,
                "high_vulnerabilities": result.high_vulnerabilities,
                "last_scan": result.analysis_timestamp.isoformat(),
                "next_scan": result.next_scan_scheduled.isoformat()
            },
            "updates": [
                {
                    "name": update.name,
                    "current_version": update.current_version,
                    "latest_version": update.latest_version,
                    "update_type": update.update_type,
                    "security_impact": update.security_impact,
                    "compatibility_risk": update.compatibility_risk,
                    "recommended_action": update.recommended_action,
                    "confidence_score": update.confidence_score,
                    "auto_fixable": update.auto_fixable,
                    "breaking_changes": update.breaking_changes
                }
                for update in result.updates_available[:20]  # Limit for dashboard
            ],
            "vulnerabilities": [
                {
                    "id": vuln.id,
                    "package_name": vuln.package_name,
                    "severity": vuln.severity,
                    "description": vuln.description,
                    "cve_id": vuln.cve_id,
                    "published_date": vuln.published_date.isoformat()
                }
                for vuln in result.vulnerabilities[:10]  # Limit for dashboard
            ],
            "status": self.get_scan_status()
        }

