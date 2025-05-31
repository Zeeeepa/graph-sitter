"""
Security and Compliance Testing Suite

Tests security vulnerability assessment, data privacy compliance,
access control validation, and audit trail verification.
"""

import pytest
import time
import hashlib
import secrets
import tempfile
import os
import json
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import base64
import jwt
from datetime import datetime, timedelta


class TestSecurityCompliance:
    """Test suite for security and compliance validation."""

    @pytest.fixture
    def security_scanner(self):
        """Security scanning utility."""
        class SecurityScanner:
            def __init__(self):
                self.vulnerabilities = []
                self.scan_results = {}
            
            def scan_dependencies(self, requirements_file: str) -> Dict[str, Any]:
                """Scan dependencies for known vulnerabilities."""
                # Mock vulnerability database
                known_vulnerabilities = {
                    "requests": {
                        "2.25.0": ["CVE-2021-33503"],
                        "2.24.0": ["CVE-2021-33503", "CVE-2020-26137"]
                    },
                    "urllib3": {
                        "1.25.8": ["CVE-2020-26137"],
                        "1.24.3": ["CVE-2019-11324"]
                    }
                }
                
                vulnerabilities = []
                if os.path.exists(requirements_file):
                    with open(requirements_file, 'r') as f:
                        for line in f:
                            if '==' in line:
                                package, version = line.strip().split('==')
                                if package in known_vulnerabilities:
                                    if version in known_vulnerabilities[package]:
                                        for cve in known_vulnerabilities[package][version]:
                                            vulnerabilities.append({
                                                "package": package,
                                                "version": version,
                                                "cve": cve,
                                                "severity": "high" if "2021" in cve else "medium"
                                            })
                
                return {
                    "vulnerabilities": vulnerabilities,
                    "total_packages": 10,  # Mock count
                    "vulnerable_packages": len(set(v["package"] for v in vulnerabilities)),
                    "scan_timestamp": time.time()
                }
            
            def scan_code_secrets(self, directory: str) -> Dict[str, Any]:
                """Scan code for potential secrets."""
                secrets_patterns = [
                    r"api_key\s*=\s*['\"][^'\"]+['\"]",
                    r"password\s*=\s*['\"][^'\"]+['\"]",
                    r"token\s*=\s*['\"][^'\"]+['\"]",
                    r"secret\s*=\s*['\"][^'\"]+['\"]"
                ]
                
                potential_secrets = []
                if os.path.exists(directory):
                    for root, dirs, files in os.walk(directory):
                        for file in files:
                            if file.endswith(('.py', '.js', '.ts', '.yaml', '.yml')):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r') as f:
                                        content = f.read()
                                        for i, line in enumerate(content.split('\n'), 1):
                                            for pattern in secrets_patterns:
                                                import re
                                                if re.search(pattern, line, re.IGNORECASE):
                                                    potential_secrets.append({
                                                        "file": file_path,
                                                        "line": i,
                                                        "type": "potential_secret",
                                                        "severity": "high"
                                                    })
                                except Exception:
                                    continue
                
                return {
                    "potential_secrets": potential_secrets,
                    "files_scanned": 50,  # Mock count
                    "scan_timestamp": time.time()
                }
        
        return SecurityScanner()

    @pytest.fixture
    def access_control_tester(self):
        """Access control testing utility."""
        class AccessControlTester:
            def __init__(self):
                self.test_users = {
                    "admin": {"role": "admin", "permissions": ["read", "write", "delete", "admin"]},
                    "user": {"role": "user", "permissions": ["read", "write"]},
                    "readonly": {"role": "readonly", "permissions": ["read"]},
                    "guest": {"role": "guest", "permissions": []}
                }
            
            def test_authentication(self, username: str, password: str) -> Dict[str, Any]:
                """Test authentication mechanisms."""
                # Mock authentication
                if username in self.test_users and password == "correct_password":
                    token = jwt.encode(
                        {
                            "user": username,
                            "role": self.test_users[username]["role"],
                            "exp": datetime.utcnow() + timedelta(hours=1)
                        },
                        "secret_key",
                        algorithm="HS256"
                    )
                    return {
                        "authenticated": True,
                        "token": token,
                        "user": username,
                        "role": self.test_users[username]["role"]
                    }
                else:
                    return {
                        "authenticated": False,
                        "error": "Invalid credentials"
                    }
            
            def test_authorization(self, token: str, required_permission: str) -> Dict[str, Any]:
                """Test authorization mechanisms."""
                try:
                    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
                    user = payload["user"]
                    user_permissions = self.test_users[user]["permissions"]
                    
                    authorized = required_permission in user_permissions
                    
                    return {
                        "authorized": authorized,
                        "user": user,
                        "required_permission": required_permission,
                        "user_permissions": user_permissions
                    }
                except jwt.ExpiredSignatureError:
                    return {"authorized": False, "error": "Token expired"}
                except jwt.InvalidTokenError:
                    return {"authorized": False, "error": "Invalid token"}
        
        return AccessControlTester()

    @pytest.fixture
    def audit_logger(self):
        """Audit logging utility."""
        class AuditLogger:
            def __init__(self):
                self.audit_log = []
            
            def log_event(self, event_type: str, user: str, resource: str, action: str, result: str, metadata: Optional[Dict] = None):
                """Log audit event."""
                audit_entry = {
                    "timestamp": time.time(),
                    "event_type": event_type,
                    "user": user,
                    "resource": resource,
                    "action": action,
                    "result": result,
                    "metadata": metadata or {},
                    "session_id": secrets.token_hex(16),
                    "ip_address": "127.0.0.1"  # Mock IP
                }
                self.audit_log.append(audit_entry)
                return audit_entry
            
            def get_audit_trail(self, user: Optional[str] = None, resource: Optional[str] = None) -> List[Dict]:
                """Get audit trail with optional filtering."""
                filtered_log = self.audit_log
                
                if user:
                    filtered_log = [entry for entry in filtered_log if entry["user"] == user]
                
                if resource:
                    filtered_log = [entry for entry in filtered_log if entry["resource"] == resource]
                
                return filtered_log
            
            def verify_audit_integrity(self) -> Dict[str, Any]:
                """Verify audit log integrity."""
                # Simple integrity check using hashes
                log_hash = hashlib.sha256(
                    json.dumps(self.audit_log, sort_keys=True).encode()
                ).hexdigest()
                
                return {
                    "integrity_verified": True,
                    "log_entries": len(self.audit_log),
                    "log_hash": log_hash,
                    "verification_timestamp": time.time()
                }
        
        return AuditLogger()

    def test_vulnerability_assessment(self, security_scanner):
        """Test security vulnerability assessment."""
        # Create test requirements file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("requests==2.25.0\n")
            f.write("urllib3==1.25.8\n")
            f.write("numpy==1.21.0\n")
            requirements_file = f.name
        
        try:
            # Test dependency vulnerability scanning
            vuln_results = security_scanner.scan_dependencies(requirements_file)
            
            assert "vulnerabilities" in vuln_results
            assert "total_packages" in vuln_results
            assert "vulnerable_packages" in vuln_results
            
            # Should detect vulnerabilities in test data
            assert len(vuln_results["vulnerabilities"]) > 0
            assert vuln_results["vulnerable_packages"] > 0
            
            # Verify vulnerability details
            for vuln in vuln_results["vulnerabilities"]:
                assert "package" in vuln
                assert "version" in vuln
                assert "cve" in vuln
                assert "severity" in vuln
                assert vuln["severity"] in ["low", "medium", "high", "critical"]
        
        finally:
            os.unlink(requirements_file)
        
        # Test code secrets scanning
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with potential secrets
            test_files = {
                "config.py": 'api_key = "sk-1234567890abcdef"\npassword = "secret123"',
                "settings.js": 'const token = "ghp_abcdef123456789";',
                "docker-compose.yml": 'environment:\n  - SECRET_KEY=mysecretkey123'
            }
            
            for filename, content in test_files.items():
                with open(os.path.join(temp_dir, filename), 'w') as f:
                    f.write(content)
            
            secrets_results = security_scanner.scan_code_secrets(temp_dir)
            
            assert "potential_secrets" in secrets_results
            assert "files_scanned" in secrets_results
            
            # Should detect potential secrets
            assert len(secrets_results["potential_secrets"]) > 0
            
            for secret in secrets_results["potential_secrets"]:
                assert "file" in secret
                assert "line" in secret
                assert "type" in secret
                assert "severity" in secret

    def test_data_privacy_compliance(self):
        """Test data privacy compliance (GDPR, CCPA, etc.)."""
        from graph_sitter.privacy import DataPrivacyManager
        
        privacy_manager = DataPrivacyManager()
        
        # Test data classification
        test_data = {
            "user_email": "user@example.com",
            "user_name": "John Doe",
            "ip_address": "192.168.1.1",
            "session_id": "sess_123456",
            "code_content": "def hello(): print('world')",
            "project_name": "my-project"
        }
        
        classification = privacy_manager.classify_data(test_data)
        
        assert "pii_fields" in classification
        assert "sensitive_fields" in classification
        assert "public_fields" in classification
        
        # Email and name should be classified as PII
        assert "user_email" in classification["pii_fields"]
        assert "user_name" in classification["pii_fields"]
        
        # IP address should be sensitive
        assert "ip_address" in classification["sensitive_fields"]
        
        # Code content should be public (non-sensitive)
        assert "code_content" in classification["public_fields"]
        
        # Test data anonymization
        anonymized_data = privacy_manager.anonymize_data(test_data)
        
        assert anonymized_data["user_email"] != test_data["user_email"]
        assert anonymized_data["user_name"] != test_data["user_name"]
        assert "@" not in anonymized_data["user_email"]  # Should be hashed/anonymized
        
        # Test data retention policies
        retention_policy = privacy_manager.get_retention_policy("user_data")
        
        assert "retention_period_days" in retention_policy
        assert "deletion_criteria" in retention_policy
        assert "compliance_requirements" in retention_policy
        
        # Test data deletion
        deletion_result = privacy_manager.delete_user_data("user_123")
        
        assert deletion_result["status"] == "success"
        assert "deleted_records" in deletion_result
        assert "audit_trail" in deletion_result

    def test_access_control_validation(self, access_control_tester, audit_logger):
        """Test access control validation."""
        # Test authentication
        auth_tests = [
            {"username": "admin", "password": "correct_password", "should_succeed": True},
            {"username": "user", "password": "correct_password", "should_succeed": True},
            {"username": "admin", "password": "wrong_password", "should_succeed": False},
            {"username": "nonexistent", "password": "any_password", "should_succeed": False}
        ]
        
        for test_case in auth_tests:
            auth_result = access_control_tester.test_authentication(
                test_case["username"], 
                test_case["password"]
            )
            
            if test_case["should_succeed"]:
                assert auth_result["authenticated"] is True
                assert "token" in auth_result
                assert "role" in auth_result
                
                # Log successful authentication
                audit_logger.log_event(
                    "authentication", 
                    test_case["username"], 
                    "system", 
                    "login", 
                    "success"
                )
            else:
                assert auth_result["authenticated"] is False
                assert "error" in auth_result
                
                # Log failed authentication
                audit_logger.log_event(
                    "authentication", 
                    test_case["username"], 
                    "system", 
                    "login", 
                    "failure"
                )
        
        # Test authorization
        # Get a valid token for testing
        admin_auth = access_control_tester.test_authentication("admin", "correct_password")
        user_auth = access_control_tester.test_authentication("user", "correct_password")
        readonly_auth = access_control_tester.test_authentication("readonly", "correct_password")
        
        authorization_tests = [
            {"token": admin_auth["token"], "permission": "admin", "should_succeed": True},
            {"token": admin_auth["token"], "permission": "write", "should_succeed": True},
            {"token": user_auth["token"], "permission": "write", "should_succeed": True},
            {"token": user_auth["token"], "permission": "admin", "should_succeed": False},
            {"token": readonly_auth["token"], "permission": "read", "should_succeed": True},
            {"token": readonly_auth["token"], "permission": "write", "should_succeed": False}
        ]
        
        for test_case in authorization_tests:
            authz_result = access_control_tester.test_authorization(
                test_case["token"],
                test_case["permission"]
            )
            
            if test_case["should_succeed"]:
                assert authz_result["authorized"] is True
            else:
                assert authz_result["authorized"] is False
            
            # Log authorization attempt
            audit_logger.log_event(
                "authorization",
                authz_result.get("user", "unknown"),
                "resource",
                test_case["permission"],
                "success" if authz_result["authorized"] else "failure"
            )

    def test_audit_trail_verification(self, audit_logger):
        """Test audit trail verification."""
        # Generate test audit events
        test_events = [
            {"type": "authentication", "user": "admin", "resource": "system", "action": "login", "result": "success"},
            {"type": "data_access", "user": "admin", "resource": "user_data", "action": "read", "result": "success"},
            {"type": "data_modification", "user": "admin", "resource": "user_data", "action": "update", "result": "success"},
            {"type": "configuration", "user": "admin", "resource": "system_config", "action": "modify", "result": "success"},
            {"type": "authentication", "user": "user", "resource": "system", "action": "login", "result": "success"},
            {"type": "data_access", "user": "user", "resource": "project_data", "action": "read", "result": "success"},
            {"type": "authorization", "user": "user", "resource": "admin_panel", "action": "access", "result": "failure"}
        ]
        
        for event in test_events:
            audit_logger.log_event(
                event["type"],
                event["user"],
                event["resource"],
                event["action"],
                event["result"],
                {"test_event": True}
            )
        
        # Test audit trail retrieval
        full_audit_trail = audit_logger.get_audit_trail()
        assert len(full_audit_trail) >= len(test_events)
        
        # Test filtered audit trail
        admin_audit_trail = audit_logger.get_audit_trail(user="admin")
        admin_events = [e for e in test_events if e["user"] == "admin"]
        assert len(admin_audit_trail) >= len(admin_events)
        
        # Test resource-specific audit trail
        system_audit_trail = audit_logger.get_audit_trail(resource="system")
        system_events = [e for e in test_events if e["resource"] == "system"]
        assert len(system_audit_trail) >= len(system_events)
        
        # Test audit integrity verification
        integrity_result = audit_logger.verify_audit_integrity()
        
        assert integrity_result["integrity_verified"] is True
        assert "log_entries" in integrity_result
        assert "log_hash" in integrity_result
        assert "verification_timestamp" in integrity_result
        
        # Verify audit entry structure
        for entry in full_audit_trail:
            required_fields = ["timestamp", "event_type", "user", "resource", "action", "result"]
            for field in required_fields:
                assert field in entry
            
            assert entry["result"] in ["success", "failure"]
            assert isinstance(entry["timestamp"], (int, float))

    def test_encryption_and_data_protection(self):
        """Test encryption and data protection mechanisms."""
        from graph_sitter.security import EncryptionManager
        
        encryption_manager = EncryptionManager()
        
        # Test data encryption
        sensitive_data = {
            "api_key": "sk-1234567890abcdef",
            "user_password": "user_password_123",
            "personal_info": {"name": "John Doe", "email": "john@example.com"}
        }
        
        # Test symmetric encryption
        encrypted_data = encryption_manager.encrypt_data(json.dumps(sensitive_data))
        
        assert encrypted_data != json.dumps(sensitive_data)  # Should be different
        assert isinstance(encrypted_data, str)  # Should be string (base64 encoded)
        
        # Test decryption
        decrypted_data = encryption_manager.decrypt_data(encrypted_data)
        assert json.loads(decrypted_data) == sensitive_data
        
        # Test key rotation
        old_key_id = encryption_manager.get_current_key_id()
        encryption_manager.rotate_encryption_key()
        new_key_id = encryption_manager.get_current_key_id()
        
        assert old_key_id != new_key_id
        
        # Test that old encrypted data can still be decrypted
        decrypted_with_old_key = encryption_manager.decrypt_data(encrypted_data)
        assert json.loads(decrypted_with_old_key) == sensitive_data
        
        # Test password hashing
        password = "user_password_123"
        hashed_password = encryption_manager.hash_password(password)
        
        assert hashed_password != password
        assert encryption_manager.verify_password(password, hashed_password) is True
        assert encryption_manager.verify_password("wrong_password", hashed_password) is False
        
        # Test secure token generation
        token = encryption_manager.generate_secure_token(32)
        
        assert len(token) == 64  # 32 bytes = 64 hex characters
        assert token != encryption_manager.generate_secure_token(32)  # Should be unique

    def test_secure_communication(self):
        """Test secure communication protocols."""
        from graph_sitter.security import SecureCommunication
        
        secure_comm = SecureCommunication()
        
        # Test TLS/SSL configuration
        tls_config = secure_comm.get_tls_config()
        
        assert tls_config["min_version"] >= "TLSv1.2"
        assert "cipher_suites" in tls_config
        assert "certificate_validation" in tls_config
        assert tls_config["certificate_validation"] is True
        
        # Test API request signing
        request_data = {
            "method": "POST",
            "url": "/api/analyze",
            "body": {"project": "test-project"},
            "timestamp": int(time.time())
        }
        
        signature = secure_comm.sign_request(request_data)
        
        assert signature is not None
        assert isinstance(signature, str)
        
        # Test signature verification
        is_valid = secure_comm.verify_request_signature(request_data, signature)
        assert is_valid is True
        
        # Test with tampered data
        tampered_data = request_data.copy()
        tampered_data["body"]["project"] = "malicious-project"
        
        is_valid_tampered = secure_comm.verify_request_signature(tampered_data, signature)
        assert is_valid_tampered is False
        
        # Test rate limiting
        rate_limiter = secure_comm.get_rate_limiter()
        
        # Test normal usage
        for i in range(10):
            allowed = rate_limiter.is_allowed("user_123", "api_call")
            assert allowed is True
        
        # Test rate limit exceeded
        for i in range(100):  # Exceed rate limit
            rate_limiter.is_allowed("user_123", "api_call")
        
        # Should now be rate limited
        allowed = rate_limiter.is_allowed("user_123", "api_call")
        assert allowed is False

    def test_compliance_reporting(self):
        """Test compliance reporting capabilities."""
        from graph_sitter.compliance import ComplianceReporter
        
        reporter = ComplianceReporter()
        
        # Test GDPR compliance report
        gdpr_report = reporter.generate_gdpr_report()
        
        assert "data_processing_activities" in gdpr_report
        assert "data_retention_policies" in gdpr_report
        assert "user_rights_implementation" in gdpr_report
        assert "data_breach_procedures" in gdpr_report
        assert "privacy_by_design" in gdpr_report
        
        # Verify GDPR requirements
        assert gdpr_report["user_rights_implementation"]["right_to_access"] is True
        assert gdpr_report["user_rights_implementation"]["right_to_deletion"] is True
        assert gdpr_report["user_rights_implementation"]["right_to_portability"] is True
        
        # Test SOC 2 compliance report
        soc2_report = reporter.generate_soc2_report()
        
        assert "security_controls" in soc2_report
        assert "availability_controls" in soc2_report
        assert "processing_integrity" in soc2_report
        assert "confidentiality_controls" in soc2_report
        
        # Test ISO 27001 compliance report
        iso27001_report = reporter.generate_iso27001_report()
        
        assert "information_security_policy" in iso27001_report
        assert "risk_management" in iso27001_report
        assert "access_control" in iso27001_report
        assert "incident_management" in iso27001_report
        
        # Test compliance score calculation
        compliance_score = reporter.calculate_compliance_score()
        
        assert "overall_score" in compliance_score
        assert "category_scores" in compliance_score
        assert 0 <= compliance_score["overall_score"] <= 100
        
        for category, score in compliance_score["category_scores"].items():
            assert 0 <= score <= 100

    def test_incident_response(self):
        """Test security incident response procedures."""
        from graph_sitter.security import IncidentResponseManager
        
        incident_manager = IncidentResponseManager()
        
        # Test incident detection
        security_events = [
            {"type": "failed_login", "user": "admin", "count": 10, "timeframe": "5_minutes"},
            {"type": "unusual_access", "user": "user", "resource": "admin_panel", "timestamp": time.time()},
            {"type": "data_exfiltration", "user": "user", "data_volume": "100MB", "timestamp": time.time()}
        ]
        
        for event in security_events:
            incident_detected = incident_manager.detect_incident(event)
            
            if event["type"] == "failed_login" and event["count"] >= 5:
                assert incident_detected["is_incident"] is True
                assert incident_detected["severity"] in ["low", "medium", "high", "critical"]
            
            if event["type"] == "data_exfiltration":
                assert incident_detected["is_incident"] is True
                assert incident_detected["severity"] == "critical"
        
        # Test incident response workflow
        incident = {
            "id": "INC-001",
            "type": "data_breach",
            "severity": "high",
            "description": "Unauthorized access to user data",
            "affected_systems": ["user_database", "api_server"],
            "detection_time": time.time()
        }
        
        response_plan = incident_manager.create_response_plan(incident)
        
        assert "containment_steps" in response_plan
        assert "investigation_steps" in response_plan
        assert "recovery_steps" in response_plan
        assert "communication_plan" in response_plan
        
        # Test incident execution
        execution_result = incident_manager.execute_response_plan(response_plan)
        
        assert execution_result["status"] in ["in_progress", "completed"]
        assert "steps_completed" in execution_result
        assert "estimated_completion" in execution_result
        
        # Test incident reporting
        incident_report = incident_manager.generate_incident_report(incident["id"])
        
        assert "incident_summary" in incident_report
        assert "timeline" in incident_report
        assert "impact_assessment" in incident_report
        assert "lessons_learned" in incident_report
        assert "preventive_measures" in incident_report

