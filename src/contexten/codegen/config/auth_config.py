"""
Authentication configuration and credential management for Codegen SDK integration.

This module provides secure handling of org_id and token authentication,
including credential rotation, validation, and environment-specific management.
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import keyring
from cryptography.fernet import Fernet


logger = logging.getLogger(__name__)


@dataclass
class AuthCredentials:
    """Container for authentication credentials."""
    org_id: str
    token: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    token_hash: Optional[str] = None
    
    def __post_init__(self):
        """Generate token hash for validation."""
        if not self.token_hash:
            self.token_hash = hashlib.sha256(self.token.encode()).hexdigest()[:16]
    
    def is_expired(self) -> bool:
        """Check if credentials are expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Validate credentials format and expiration."""
        if not self.org_id or not self.token:
            return False
        if self.is_expired():
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding sensitive data)."""
        return {
            "org_id": self.org_id,
            "token_hash": self.token_hash,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class AuthConfig:
    """
    Secure authentication configuration manager.
    
    Handles org_id and token management with support for:
    - Environment variable configuration
    - Secure credential storage using keyring
    - Token rotation and validation
    - Environment-specific credential management
    """
    
    def __init__(self, 
                 service_name: str = "contexten-codegen",
                 use_keyring: bool = True,
                 encryption_key: Optional[str] = None):
        """
        Initialize authentication configuration.
        
        Args:
            service_name: Service name for keyring storage
            use_keyring: Whether to use system keyring for secure storage
            encryption_key: Optional encryption key for credential encryption
        """
        self.service_name = service_name
        self.use_keyring = use_keyring
        self.encryption_key = encryption_key
        self._credentials: Optional[AuthCredentials] = None
        
        # Initialize encryption if key provided
        self._cipher = None
        if encryption_key:
            self._cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def load_credentials(self, environment: str = "default") -> Optional[AuthCredentials]:
        """
        Load credentials from various sources in priority order:
        1. Environment variables
        2. Keyring storage
        3. Configuration file
        
        Args:
            environment: Environment name for credential isolation
            
        Returns:
            AuthCredentials if found and valid, None otherwise
        """
        # Try environment variables first
        credentials = self._load_from_environment()
        if credentials and credentials.is_valid():
            logger.info("Loaded credentials from environment variables")
            self._credentials = credentials
            return credentials
        
        # Try keyring storage
        if self.use_keyring:
            credentials = self._load_from_keyring(environment)
            if credentials and credentials.is_valid():
                logger.info(f"Loaded credentials from keyring for environment: {environment}")
                self._credentials = credentials
                return credentials
        
        # Try configuration file
        credentials = self._load_from_file(environment)
        if credentials and credentials.is_valid():
            logger.info(f"Loaded credentials from file for environment: {environment}")
            self._credentials = credentials
            return credentials
        
        logger.warning("No valid credentials found")
        return None
    
    def save_credentials(self, 
                        credentials: AuthCredentials, 
                        environment: str = "default",
                        save_to_keyring: bool = True,
                        save_to_file: bool = False) -> bool:
        """
        Save credentials to secure storage.
        
        Args:
            credentials: Credentials to save
            environment: Environment name for credential isolation
            save_to_keyring: Whether to save to system keyring
            save_to_file: Whether to save to encrypted file
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not credentials.is_valid():
            logger.error("Cannot save invalid credentials")
            return False
        
        success = True
        
        # Save to keyring
        if save_to_keyring and self.use_keyring:
            try:
                credential_data = {
                    "org_id": credentials.org_id,
                    "token": credentials.token,
                    "created_at": credentials.created_at.isoformat(),
                    "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None
                }
                
                # Encrypt if cipher available
                data_str = json.dumps(credential_data)
                if self._cipher:
                    data_str = self._cipher.encrypt(data_str.encode()).decode()
                
                keyring.set_password(self.service_name, f"{environment}_credentials", data_str)
                logger.info(f"Saved credentials to keyring for environment: {environment}")
            except Exception as e:
                logger.error(f"Failed to save credentials to keyring: {e}")
                success = False
        
        # Save to file
        if save_to_file:
            success &= self._save_to_file(credentials, environment)
        
        if success:
            self._credentials = credentials
        
        return success
    
    def rotate_token(self, new_token: str, environment: str = "default") -> bool:
        """
        Rotate authentication token.
        
        Args:
            new_token: New authentication token
            environment: Environment name
            
        Returns:
            True if rotation successful, False otherwise
        """
        if not self._credentials:
            logger.error("No existing credentials to rotate")
            return False
        
        # Create new credentials with rotated token
        new_credentials = AuthCredentials(
            org_id=self._credentials.org_id,
            token=new_token,
            created_at=datetime.utcnow(),
            expires_at=self._credentials.expires_at
        )
        
        # Validate new credentials
        if not new_credentials.is_valid():
            logger.error("New token is invalid")
            return False
        
        # Save new credentials
        return self.save_credentials(new_credentials, environment)
    
    def validate_credentials(self, credentials: Optional[AuthCredentials] = None) -> Tuple[bool, str]:
        """
        Validate credentials format and expiration.
        
        Args:
            credentials: Credentials to validate (uses current if None)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        creds = credentials or self._credentials
        if not creds:
            return False, "No credentials available"
        
        if not creds.org_id:
            return False, "Missing org_id"
        
        if not creds.token:
            return False, "Missing token"
        
        if creds.is_expired():
            return False, "Credentials expired"
        
        # Validate org_id format (should be numeric or UUID-like)
        try:
            int(creds.org_id)
        except ValueError:
            if len(creds.org_id) < 8:  # Minimum reasonable length
                return False, "Invalid org_id format"
        
        # Validate token format (should be reasonable length)
        if len(creds.token) < 16:
            return False, "Token too short"
        
        return True, "Valid"
    
    def get_credentials(self) -> Optional[AuthCredentials]:
        """Get current credentials."""
        return self._credentials
    
    def clear_credentials(self, environment: str = "default") -> None:
        """
        Clear stored credentials.
        
        Args:
            environment: Environment name
        """
        # Clear from keyring
        if self.use_keyring:
            try:
                keyring.delete_password(self.service_name, f"{environment}_credentials")
                logger.info(f"Cleared credentials from keyring for environment: {environment}")
            except Exception as e:
                logger.warning(f"Failed to clear keyring credentials: {e}")
        
        # Clear from file
        config_file = self._get_config_file_path(environment)
        if config_file.exists():
            try:
                config_file.unlink()
                logger.info(f"Cleared credentials file for environment: {environment}")
            except Exception as e:
                logger.warning(f"Failed to clear credentials file: {e}")
        
        # Clear in-memory credentials
        self._credentials = None
    
    def _load_from_environment(self) -> Optional[AuthCredentials]:
        """Load credentials from environment variables."""
        org_id = os.environ.get("CODEGEN_ORG_ID")
        token = os.environ.get("CODEGEN_API_TOKEN")
        
        if not org_id or not token:
            return None
        
        # Check for expiration time in environment
        expires_str = os.environ.get("CODEGEN_TOKEN_EXPIRES")
        expires_at = None
        if expires_str:
            try:
                expires_at = datetime.fromisoformat(expires_str)
            except ValueError:
                logger.warning("Invalid CODEGEN_TOKEN_EXPIRES format")
        
        return AuthCredentials(
            org_id=org_id,
            token=token,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )
    
    def _load_from_keyring(self, environment: str) -> Optional[AuthCredentials]:
        """Load credentials from system keyring."""
        try:
            data_str = keyring.get_password(self.service_name, f"{environment}_credentials")
            if not data_str:
                return None
            
            # Decrypt if cipher available
            if self._cipher:
                try:
                    data_str = self._cipher.decrypt(data_str.encode()).decode()
                except Exception as e:
                    logger.error(f"Failed to decrypt keyring credentials: {e}")
                    return None
            
            credential_data = json.loads(data_str)
            
            expires_at = None
            if credential_data.get("expires_at"):
                expires_at = datetime.fromisoformat(credential_data["expires_at"])
            
            return AuthCredentials(
                org_id=credential_data["org_id"],
                token=credential_data["token"],
                created_at=datetime.fromisoformat(credential_data["created_at"]),
                expires_at=expires_at
            )
        except Exception as e:
            logger.error(f"Failed to load credentials from keyring: {e}")
            return None
    
    def _load_from_file(self, environment: str) -> Optional[AuthCredentials]:
        """Load credentials from encrypted file."""
        config_file = self._get_config_file_path(environment)
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                data_str = f.read()
            
            # Decrypt if cipher available
            if self._cipher:
                try:
                    data_str = self._cipher.decrypt(data_str.encode()).decode()
                except Exception as e:
                    logger.error(f"Failed to decrypt file credentials: {e}")
                    return None
            
            credential_data = json.loads(data_str)
            
            expires_at = None
            if credential_data.get("expires_at"):
                expires_at = datetime.fromisoformat(credential_data["expires_at"])
            
            return AuthCredentials(
                org_id=credential_data["org_id"],
                token=credential_data["token"],
                created_at=datetime.fromisoformat(credential_data["created_at"]),
                expires_at=expires_at
            )
        except Exception as e:
            logger.error(f"Failed to load credentials from file: {e}")
            return None
    
    def _save_to_file(self, credentials: AuthCredentials, environment: str) -> bool:
        """Save credentials to encrypted file."""
        try:
            config_file = self._get_config_file_path(environment)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            credential_data = {
                "org_id": credentials.org_id,
                "token": credentials.token,
                "created_at": credentials.created_at.isoformat(),
                "expires_at": credentials.expires_at.isoformat() if credentials.expires_at else None
            }
            
            data_str = json.dumps(credential_data)
            
            # Encrypt if cipher available
            if self._cipher:
                data_str = self._cipher.encrypt(data_str.encode()).decode()
            
            with open(config_file, 'w') as f:
                f.write(data_str)
            
            # Set restrictive permissions
            config_file.chmod(0o600)
            
            logger.info(f"Saved credentials to file for environment: {environment}")
            return True
        except Exception as e:
            logger.error(f"Failed to save credentials to file: {e}")
            return False
    
    def _get_config_file_path(self, environment: str) -> Path:
        """Get configuration file path for environment."""
        config_dir = Path.home() / ".contexten" / "codegen"
        return config_dir / f"credentials_{environment}.json"
    
    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new encryption key for credential encryption."""
        return Fernet.generate_key().decode()

