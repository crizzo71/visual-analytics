"""
Secure Configuration Management for LDAP Analytics Dashboard
"""

import os
import json
from typing import Dict, Any
from cryptography.fernet import Fernet

class SecureConfig:
    """Manages secure configuration and secrets"""

    def __init__(self):
        self.config_file = "analytics/secure_config.json"
        self.setup_encryption()

    def setup_encryption(self):
        """Setup encryption for sensitive configuration data"""
        # Generate or load encryption key
        key_file = "analytics/.encryption_key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.encryption_key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)

        self.cipher = Fernet(self.encryption_key)

    def encrypt_value(self, value: str) -> str:
        """Encrypt a configuration value"""
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a configuration value"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default secure configuration"""
        return {
            "security": {
                "session_timeout_minutes": 60,
                "max_login_attempts": 3,
                "lockout_duration_minutes": 15,
                "require_https": True,
                "secure_headers": True,
                "rate_limiting": True
            },
            "audit": {
                "log_all_access": True,
                "log_exports": True,
                "log_retention_days": 90,
                "alert_on_suspicious_activity": True
            },
            "data_protection": {
                "mask_sensitive_data": True,
                "encrypt_exports": True,
                "data_retention_days": 365,
                "anonymize_logs": True
            },
            "network": {
                "allowed_ips": ["127.0.0.1", "localhost"],
                "block_tor_nodes": True,
                "enable_firewall": True,
                "max_concurrent_sessions": 10
            },
            "features": {
                "enable_export": True,
                "enable_org_chart": True,
                "enable_search": True,
                "max_export_records": 1000
            }
        }

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")

        # Return default config if file doesn't exist
        default_config = self.get_default_config()
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        # Set restrictive permissions
        os.chmod(self.config_file, 0o600)

    def get_env_var(self, key: str, default: str = None, encrypted: bool = False) -> str:
        """Get environment variable with optional decryption"""
        value = os.getenv(key, default)
        if value and encrypted:
            try:
                value = self.decrypt_value(value)
            except Exception:
                # If decryption fails, assume it's not encrypted
                pass
        return value

# Global secure config instance
secure_config = SecureConfig()