"""
Authentication and Authorization for LDAP Analytics Dashboard
"""

import streamlit as st
import hashlib
import hmac
import os
from typing import Dict, List, Optional
import jwt
from datetime import datetime, timedelta
import requests

class DashboardAuth:
    """Authentication and authorization handler for the dashboard"""

    def __init__(self):
        self.secret_key = os.getenv('DASHBOARD_SECRET_KEY', 'your-secret-key-change-this')
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))

        # Authorized users (in production, this should be in a database or LDAP)
        self.authorized_users = {
            'crizzo@redhat.com': {
                'name': 'Christine Rizzo',
                'role': 'admin',
                'permissions': ['view_all', 'export_data', 'manage_users']
            },
            'demo@redhat.com': {
                'name': 'Demo User',
                'role': 'viewer',
                'permissions': ['view_team', 'view_reports']
            }
        }

    def check_password(self, email: str, password: str) -> bool:
        """Verify user credentials (simplified - use proper auth in production)"""
        # In production, this should verify against LDAP or identity provider
        if email in self.authorized_users:
            # Simple demo passwords (NEVER do this in production!)
            demo_passwords = {
                'crizzo@redhat.com': 'admin123',
                'demo@redhat.com': 'demo123'
            }
            return demo_passwords.get(email) == password
        return False

    def authenticate_with_ldap(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate against LDAP (placeholder implementation)"""
        # This would integrate with your actual LDAP authentication
        # For now, fall back to simple auth
        email = f"{username}@redhat.com"
        if self.check_password(email, password):
            return self.authorized_users.get(email)
        return None

    def create_session_token(self, user_email: str) -> str:
        """Create a JWT session token"""
        payload = {
            'email': user_email,
            'exp': datetime.utcnow() + timedelta(minutes=self.session_timeout),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_session_token(self, token: str) -> Optional[Dict]:
        """Verify and decode session token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_email = payload.get('email')
            if user_email in self.authorized_users:
                return self.authorized_users[user_email]
        except jwt.ExpiredSignatureError:
            st.error("Session expired. Please log in again.")
        except jwt.InvalidTokenError:
            st.error("Invalid session. Please log in again.")
        return None

    def check_permission(self, user: Dict, required_permission: str) -> bool:
        """Check if user has required permission"""
        return required_permission in user.get('permissions', [])

    def login_form(self):
        """Display login form"""
        st.markdown("### 🔐 RedHat LDAP Analytics - Secure Access")

        with st.form("login_form"):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("**Demo Credentials:**")
                st.code("Admin: crizzo@redhat.com / admin123")
                st.code("Viewer: demo@redhat.com / demo123")

            with col2:
                email = st.text_input("Email", placeholder="your.email@redhat.com")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("🔑 Login")

                if submit:
                    if self.check_password(email, password):
                        token = self.create_session_token(email)
                        st.session_state['auth_token'] = token
                        st.session_state['user'] = self.authorized_users[email]
                        st.success(f"Welcome, {self.authorized_users[email]['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

        # Security notice
        st.markdown("---")
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ee0000;'>
        <strong>🛡️ Security Notice:</strong><br>
        • This dashboard contains sensitive organizational data<br>
        • All access is logged and monitored<br>
        • Do not share your credentials<br>
        • Report any suspicious activity to IT Security
        </div>
        """, unsafe_allow_html=True)

    def logout(self):
        """Clear session and logout"""
        for key in ['auth_token', 'user']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        if 'auth_token' not in st.session_state:
            return False

        token = st.session_state['auth_token']
        user = self.verify_session_token(token)

        if user:
            st.session_state['user'] = user
            return True
        else:
            # Clear invalid session
            self.logout()
            return False

    def require_auth(self):
        """Decorator-like function to require authentication"""
        if not self.is_authenticated():
            self.login_form()
            st.stop()

    def require_permission(self, permission: str):
        """Require specific permission"""
        if not self.is_authenticated():
            self.login_form()
            st.stop()

        user = st.session_state.get('user', {})
        if not self.check_permission(user, permission):
            st.error(f"❌ Access Denied: You don't have '{permission}' permission")
            st.stop()

# Global auth instance
auth = DashboardAuth()