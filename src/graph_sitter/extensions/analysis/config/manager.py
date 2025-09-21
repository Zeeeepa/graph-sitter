#!/usr/bin/env python3
"""
Configuration Manager

Handles loading, merging, and validation of analysis configuration from multiple sources.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from copy import deepcopy

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import tomli
    TOML_AVAILABLE = True
except ImportError:
    try:
        import tomllib  # Python 3.11+
        tomli = tomllib
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False

from .defaults import DEFAULT_CONFIG, ANALYSIS_PROFILES, ENVIRONMENT_OVERRIDES


class ConfigManager:
    """Manages analysis configuration from multiple sources."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            base_path: Base directory to look for config files (default: current directory)
        """
        self.base_path = Path(base_path or os.getcwd())
        self.config = deepcopy(DEFAULT_CONFIG)
        self.config_sources = []
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load configuration from all available sources."""
        # Load in priority order (later overrides earlier)
        self._load_default_config()
        self._load_system_config()
        self._load_user_config()
        self._load_project_config()
        self._load_environment_overrides()
        
        # Validate final configuration
        self._validate_config()
    
    def _load_default_config(self):
        """Load default configuration."""
        self.config_sources.append({"source": "defaults", "config": deepcopy(DEFAULT_CONFIG)})
        logging.debug("Loaded default configuration")
    
    def _load_system_config(self):
        """Load system-wide configuration."""
        system_paths = [
            Path("/etc/graph-sitter/analysis.yaml"),
            Path("/etc/graph-sitter/analysis.yml"), 
            Path("/etc/graph-sitter/analysis.json"),
        ]
        
        for config_path in system_paths:
            if config_path.exists():
                try:
                    config = self._load_config_file(config_path)
                    self._merge_config(config)
                    self.config_sources.append({"source": f"system:{config_path}", "config": config})
                    logging.debug(f"Loaded system config from {config_path}")
                    break
                except Exception as e:
                    logging.warning(f"Failed to load system config {config_path}: {e}")
    
    def _load_user_config(self):
        """Load user-specific configuration."""
        user_dir = Path.home()
        user_paths = [
            user_dir / ".config" / "graph-sitter" / "analysis.yaml",
            user_dir / ".config" / "graph-sitter" / "analysis.yml",
            user_dir / ".config" / "graph-sitter" / "analysis.json",
            user_dir / ".graph-sitter-analysis.yaml",
            user_dir / ".graph-sitter-analysis.yml", 
            user_dir / ".graph-sitter-analysis.json",
        ]
        
        for config_path in user_paths:
            if config_path.exists():
                try:
                    config = self._load_config_file(config_path)
                    self._merge_config(config)
                    self.config_sources.append({"source": f"user:{config_path}", "config": config})
                    logging.debug(f"Loaded user config from {config_path}")
                    break
                except Exception as e:
                    logging.warning(f"Failed to load user config {config_path}: {e}")
    
    def _load_project_config(self):
        """Load project-specific configuration."""
        # Look for config files in project directory
        project_paths = [
            self.base_path / ".graph-sitter-analysis.yaml",
            self.base_path / ".graph-sitter-analysis.yml",
            self.base_path / ".graph-sitter-analysis.json",
            self.base_path / "graph-sitter-analysis.yaml",
            self.base_path / "graph-sitter-analysis.yml", 
            self.base_path / "graph-sitter-analysis.json",
            self.base_path / "pyproject.toml",  # Check for tool.graph-sitter-analysis section
        ]
        
        for config_path in project_paths:
            if config_path.exists():
                try:
                    if config_path.name == "pyproject.toml":
                        config = self._load_pyproject_config(config_path)
                    else:
                        config = self._load_config_file(config_path)
                    
                    if config:
                        self._merge_config(config)
                        self.config_sources.append({"source": f"project:{config_path}", "config": config})
                        logging.debug(f"Loaded project config from {config_path}")
                        break
                except Exception as e:
                    logging.warning(f"Failed to load project config {config_path}: {e}")
    
    def _load_environment_overrides(self):
        """Load environment-specific overrides."""
        env = os.environ.get("GS_ANALYSIS_ENV", "").lower()
        
        if env in ENVIRONMENT_OVERRIDES:
            override_config = ENVIRONMENT_OVERRIDES[env]
            self._merge_config(override_config)
            self.config_sources.append({"source": f"environment:{env}", "config": override_config})
            logging.debug(f"Applied environment overrides for: {env}")
        
        # Also check for environment variables
        env_overrides = self._load_env_variables()
        if env_overrides:
            self._merge_config(env_overrides)
            self.config_sources.append({"source": "environment_variables", "config": env_overrides})
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from a file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.json':
                return json.load(f)
            elif config_path.suffix.lower() in ['.yaml', '.yml']:
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML not available for YAML config files")
                return yaml.safe_load(f) or {}
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
    
    def _load_pyproject_config(self, pyproject_path: Path) -> Optional[Dict[str, Any]]:
        """Load configuration from pyproject.toml file."""
        if not TOML_AVAILABLE:
            logging.warning("TOML support not available - skipping pyproject.toml")
            return None
        
        try:
            with open(pyproject_path, 'rb') as f:
                data = tomli.load(f)
            
            # Look for tool.graph-sitter-analysis section
            return data.get("tool", {}).get("graph-sitter-analysis", {})
        except Exception as e:
            logging.warning(f"Failed to parse pyproject.toml: {e}")
            return None
    
    def _load_env_variables(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Map environment variables to config paths
        env_mappings = {
            "GS_ANALYSIS_PROFILE": ["analysis", "profile"],
            "GS_ANALYSIS_PARALLEL": ["analysis", "parallel_execution"],
            "GS_ANALYSIS_MAX_PARALLEL": ["analysis", "max_parallel_tools"],
            "GS_ANALYSIS_TIMEOUT_MULTIPLIER": ["analysis", "timeout_multiplier"],
            "GS_ANALYSIS_OUTPUT_FORMAT": ["analysis", "output", "format"],
            "GS_ANALYSIS_VERBOSITY": ["analysis", "output", "verbosity"],
            "GS_ANALYSIS_MIN_SEVERITY": ["analysis", "filtering", "min_severity"],
            "GS_ANALYSIS_CACHE_ENABLED": ["analysis", "caching", "enabled"],
            "GS_ANALYSIS_DB_PATH": ["database", "path"],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if value.lower() in ["true", "false"]:
                    value = value.lower() == "true"
                elif value.isdigit():
                    value = int(value)
                elif value.replace(".", "").isdigit():
                    value = float(value)
                
                # Set nested config value
                current = env_config
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})
                current[config_path[-1]] = value
        
        return env_config
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration into existing config."""
        self.config = self._deep_merge(self.config, new_config)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_config(self):
        """Validate the final merged configuration."""
        try:
            # Validate profile exists
            profile = self.config.get("analysis", {}).get("profile", "standard")
            if profile not in ANALYSIS_PROFILES:
                logging.warning(f"Unknown profile '{profile}', using 'standard'")
                self.config["analysis"]["profile"] = "standard"
            
            # Validate tools exist
            available_tools = set(self.config.get("tools", {}).keys())
            profile_tools = set(ANALYSIS_PROFILES[profile]["enabled_tools"])
            missing_tools = profile_tools - available_tools
            
            if missing_tools:
                logging.warning(f"Profile '{profile}' requires missing tools: {missing_tools}")
            
            # Validate numeric values
            numeric_fields = [
                (["analysis", "max_parallel_tools"], 1, 8),
                (["analysis", "timeout_multiplier"], 0.1, 5.0),
                (["database", "retention_days"], 1, 365),
            ]
            
            for path, min_val, max_val in numeric_fields:
                current = self.config
                for key in path:
                    current = current.get(key, {})
                
                if isinstance(current, (int, float)):
                    if not (min_val <= current <= max_val):
                        logging.warning(f"Value {current} for {'.'.join(path)} outside valid range [{min_val}, {max_val}]")
            
            logging.debug("Configuration validation completed")
            
        except Exception as e:
            logging.error(f"Configuration validation failed: {e}")
    
    def get(self, path: str, default=None) -> Any:
        """Get configuration value by dot-separated path."""
        keys = path.split('.')
        current = self.config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def get_profile_config(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific profile."""
        profile_name = profile_name or self.get("analysis.profile", "standard")
        
        if profile_name not in ANALYSIS_PROFILES:
            logging.warning(f"Unknown profile '{profile_name}', using 'standard'")
            profile_name = "standard"
        
        profile = ANALYSIS_PROFILES[profile_name].copy()
        
        # Merge with current analysis config
        analysis_config = self.get("analysis", {})
        profile.update(analysis_config)
        
        return profile
    
    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific tool."""
        return self.get(f"tools.{tool_name}")
    
    def get_enabled_tools(self, profile_name: Optional[str] = None) -> List[str]:
        """Get list of enabled tools for current or specified profile."""
        profile_config = self.get_profile_config(profile_name)
        profile_tools = set(profile_config.get("enabled_tools", []))
        
        # Filter by actual tool availability and enabled status
        enabled_tools = []
        for tool_name in profile_tools:
            tool_config = self.get_tool_config(tool_name)
            if tool_config and tool_config.get("enabled", True):
                enabled_tools.append(tool_name)
        
        return enabled_tools
    
    def export_config(self, format: str = "yaml") -> str:
        """Export current configuration as string."""
        if format.lower() == "json":
            return json.dumps(self.config, indent=2)
        elif format.lower() in ["yaml", "yml"]:
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML not available for YAML export")
            return yaml.dump(self.config, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def save_config(self, path: Union[str, Path], format: Optional[str] = None):
        """Save current configuration to file."""
        config_path = Path(path)
        
        if format is None:
            format = config_path.suffix.lower().lstrip('.')
        
        content = self.export_config(format)
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Configuration saved to {config_path}")
    
    def get_config_sources(self) -> List[Dict[str, Any]]:
        """Get list of configuration sources that were loaded."""
        return self.config_sources.copy()
    
    def reload_config(self):
        """Reload configuration from all sources."""
        self.config = deepcopy(DEFAULT_CONFIG)
        self.config_sources = []
        self._load_all_configs()