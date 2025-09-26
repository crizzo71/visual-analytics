"""
Audit Logging for LDAP Analytics Dashboard
"""

import logging
import json
from datetime import datetime
import streamlit as st
import os
from typing import Dict, Any

class AuditLogger:
    """Comprehensive audit logging for security and compliance"""

    def __init__(self):
        self.setup_audit_logging()

    def setup_audit_logging(self):
        """Configure audit logging"""
        # Create audit logs directory
        audit_dir = "logs"
        os.makedirs(audit_dir, exist_ok=True)

        # Configure audit logger
        self.audit_logger = logging.getLogger('ldap_analytics_audit')
        self.audit_logger.setLevel(logging.INFO)

        # Create file handler for audit logs
        audit_file = os.path.join(audit_dir, 'audit.log')
        file_handler = logging.FileHandler(audit_file)
        file_handler.setLevel(logging.INFO)

        # Create detailed formatter
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Add handler if not already added
        if not self.audit_logger.handlers:
            self.audit_logger.addHandler(file_handler)

    def get_user_context(self) -> Dict[str, Any]:
        """Extract user context for audit logging"""
        user = st.session_state.get('user', {})

        # Get client information (Streamlit provides limited info)
        context = {
            'user_email': user.get('email', 'anonymous'),
            'user_name': user.get('name', 'Unknown'),
            'user_role': user.get('role', 'none'),
            'session_id': st.session_state.get('session_id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
        }

        # Try to get additional context if available
        try:
            # This would require additional setup to get real client info
            context.update({
                'user_agent': 'Streamlit Dashboard',
                'ip_address': 'localhost',  # In production, capture real IP
            })
        except:
            pass

        return context

    def log_event(self, event_type: str, details: Dict[str, Any], level: str = 'INFO'):
        """Log an audit event"""
        context = self.get_user_context()

        audit_record = {
            'event_type': event_type,
            'user_context': context,
            'details': details,
            'severity': level
        }

        message = json.dumps(audit_record, default=str)

        if level.upper() == 'WARNING':
            self.audit_logger.warning(message)
        elif level.upper() == 'ERROR':
            self.audit_logger.error(message)
        elif level.upper() == 'CRITICAL':
            self.audit_logger.critical(message)
        else:
            self.audit_logger.info(message)

    def log_login_attempt(self, email: str, success: bool, ip_address: str = 'localhost'):
        """Log login attempts"""
        self.log_event(
            'LOGIN_ATTEMPT',
            {
                'email': email,
                'success': success,
                'ip_address': ip_address
            },
            'WARNING' if not success else 'INFO'
        )

    def log_data_access(self, data_type: str, filters: Dict = None):
        """Log data access events"""
        self.log_event(
            'DATA_ACCESS',
            {
                'data_type': data_type,
                'filters': filters or {},
                'action': 'view'
            }
        )

    def log_data_export(self, data_type: str, record_count: int, export_format: str):
        """Log data export events"""
        self.log_event(
            'DATA_EXPORT',
            {
                'data_type': data_type,
                'record_count': record_count,
                'export_format': export_format
            },
            'WARNING'  # Data exports are higher risk
        )

    def log_configuration_change(self, change_type: str, old_value: Any, new_value: Any):
        """Log configuration changes"""
        self.log_event(
            'CONFIGURATION_CHANGE',
            {
                'change_type': change_type,
                'old_value': str(old_value),
                'new_value': str(new_value)
            },
            'WARNING'
        )

    def log_security_event(self, event_description: str, severity: str = 'WARNING'):
        """Log security-related events"""
        self.log_event(
            'SECURITY_EVENT',
            {
                'description': event_description,
                'requires_investigation': severity in ['ERROR', 'CRITICAL']
            },
            severity
        )

    def log_ldap_query(self, query_type: str, search_base: str, filters: str):
        """Log LDAP queries for compliance"""
        self.log_event(
            'LDAP_QUERY',
            {
                'query_type': query_type,
                'search_base': search_base,
                'filters': filters
            }
        )

    def log_session_activity(self, activity: str, details: Dict = None):
        """Log user session activities"""
        self.log_event(
            'SESSION_ACTIVITY',
            {
                'activity': activity,
                'details': details or {}
            }
        )

# Global audit logger instance
audit_logger = AuditLogger()