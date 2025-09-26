"""
Red Hat SSO (Keycloak) Authentication Integration
Provides OIDC authentication with Red Hat's SSO system
"""

import streamlit as st
import requests
import jwt
import base64
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import os
import json

class RedHatSSOAuth:
    """Red Hat SSO/Keycloak authentication handler"""

    def __init__(self):
        # Red Hat SSO Configuration
        self.sso_base_url = os.getenv('RH_SSO_BASE_URL', 'https://sso.redhat.com')
        self.realm = os.getenv('RH_SSO_REALM', 'redhat-external')
        self.client_id = os.getenv('RH_SSO_CLIENT_ID', 'ldap-analytics-dashboard')
        self.client_secret = os.getenv('RH_SSO_CLIENT_SECRET', '')
        self.redirect_uri = os.getenv('RH_SSO_REDIRECT_URI', 'http://localhost:8502/callback')

        # Build SSO URLs
        self.realm_url = f"{self.sso_base_url}/auth/realms/{self.realm}"
        self.auth_url = f"{self.realm_url}/protocol/openid-connect/auth"
        self.token_url = f"{self.realm_url}/protocol/openid-connect/token"
        self.userinfo_url = f"{self.realm_url}/protocol/openid-connect/userinfo"
        self.logout_url = f"{self.realm_url}/protocol/openid-connect/logout"

        # OIDC discovery
        self.discovery_url = f"{self.realm_url}/.well-known/openid_configuration"

    def generate_state_and_nonce(self) -> tuple:
        """Generate state and nonce for OIDC security"""
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        return state, nonce

    def generate_pkce_challenge(self) -> tuple:
        """Generate PKCE code challenge and verifier for enhanced security"""
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        return code_verifier, code_challenge

    def get_authorization_url(self) -> tuple:
        """Generate authorization URL for SSO login"""
        state, nonce = self.generate_state_and_nonce()
        code_verifier, code_challenge = self.generate_pkce_challenge()

        # Store in session for validation
        st.session_state['oauth_state'] = state
        st.session_state['oauth_nonce'] = nonce
        st.session_state['oauth_code_verifier'] = code_verifier

        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': 'openid profile email',
            'redirect_uri': self.redirect_uri,
            'state': state,
            'nonce': nonce,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }

        auth_url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        return auth_url, state

    def exchange_code_for_tokens(self, authorization_code: str, state: str) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        # Validate state
        if state != st.session_state.get('oauth_state'):
            st.error("Invalid OAuth state parameter")
            return None

        # Prepare token request
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': st.session_state.get('oauth_code_verifier')
        }

        try:
            response = requests.post(
                self.token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Token exchange failed: {response.status_code}")
                return None

        except Exception as e:
            st.error(f"Error exchanging code for token: {e}")
            return None

    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user information from SSO"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(self.userinfo_url, headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to get user info: {response.status_code}")
                return None

        except Exception as e:
            st.error(f"Error getting user info: {e}")
            return None

    def verify_jwt_token(self, id_token: str) -> Optional[Dict]:
        """Verify and decode ID token (simplified - in production use proper JWT verification)"""
        try:
            # NOTE: In production, you should verify the JWT signature with Keycloak's public key
            decoded = jwt.decode(id_token, options={"verify_signature": False})

            # Verify nonce
            if decoded.get('nonce') != st.session_state.get('oauth_nonce'):
                st.error("Invalid nonce in ID token")
                return None

            return decoded
        except Exception as e:
            st.error(f"Error verifying ID token: {e}")
            return None

    def map_user_roles(self, user_info: Dict, id_token_claims: Dict) -> str:
        """Map Red Hat SSO roles to dashboard roles"""
        # Check for Red Hat SSO roles/groups
        realm_access = id_token_claims.get('realm_access', {})
        roles = realm_access.get('roles', [])
        groups = user_info.get('groups', [])

        # Map based on Red Hat groups/roles
        if 'ldap-analytics-admin' in roles or 'ldap-analytics-admin' in groups:
            return 'admin'
        elif 'ldap-analytics-manager' in roles or 'ldap-analytics-manager' in groups:
            return 'manager'
        elif 'ldap-analytics-auditor' in roles or 'ldap-analytics-auditor' in groups:
            return 'auditor'
        else:
            return 'viewer'

    def create_user_session(self, user_info: Dict, id_token_claims: Dict, tokens: Dict) -> Dict:
        """Create user session from SSO information"""
        user_role = self.map_user_roles(user_info, id_token_claims)

        # Define permissions based on role
        permissions_map = {
            'admin': ['view_all', 'export_data', 'manage_users', 'view_audit'],
            'manager': ['view_team', 'export_data', 'view_reports'],
            'auditor': ['view_audit', 'view_reports'],
            'viewer': ['view_team', 'view_reports']
        }

        user_session = {
            'email': user_info.get('email', ''),
            'name': user_info.get('name', user_info.get('preferred_username', '')),
            'username': user_info.get('preferred_username', ''),
            'role': user_role,
            'permissions': permissions_map.get(user_role, []),
            'groups': user_info.get('groups', []),
            'sso_sub': id_token_claims.get('sub', ''),
            'session_start': datetime.utcnow().isoformat(),
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token'),
            'expires_at': datetime.utcnow() + timedelta(seconds=tokens.get('expires_in', 3600))
        }

        return user_session

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh access token using refresh token"""
        token_data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token
        }

        try:
            response = requests.post(
                self.token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception:
            return None

    def logout_from_sso(self, refresh_token: str = None) -> str:
        """Generate SSO logout URL"""
        params = {
            'redirect_uri': self.redirect_uri.replace('/callback', '/'),
        }

        if refresh_token:
            params['refresh_token'] = refresh_token

        return f"{self.logout_url}?{urllib.parse.urlencode(params)}"

    def handle_callback(self) -> Optional[Dict]:
        """Handle OAuth callback from SSO"""
        # Get query parameters
        query_params = st.query_params

        if 'code' in query_params and 'state' in query_params:
            code = query_params['code'][0]
            state = query_params['state'][0]

            # Exchange code for tokens
            tokens = self.exchange_code_for_tokens(code, state)
            if not tokens:
                return None

            # Get user info
            user_info = self.get_user_info(tokens['access_token'])
            if not user_info:
                return None

            # Verify ID token
            id_token_claims = self.verify_jwt_token(tokens['id_token'])
            if not id_token_claims:
                return None

            # Create user session
            user_session = self.create_user_session(user_info, id_token_claims, tokens)

            # Clear OAuth state
            for key in ['oauth_state', 'oauth_nonce', 'oauth_code_verifier']:
                if key in st.session_state:
                    del st.session_state[key]

            return user_session

        elif 'error' in query_params:
            error = query_params['error'][0]
            error_description = query_params.get('error_description', [''])[0]
            st.error(f"SSO Error: {error} - {error_description}")

        return None

    def sso_login_ui(self):
        """Display SSO login interface"""
        st.markdown("### 🔐 Red Hat SSO Login")
        st.markdown("---")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("**Red Hat Single Sign-On**")
            st.markdown("🏢 Use your Red Hat corporate account")
            st.markdown("🔑 Secure OIDC authentication")
            st.markdown("👥 Role-based access control")

        with col2:
            st.markdown("**Login with Red Hat SSO**")

            if st.button("🚀 Login with Red Hat SSO", type="primary"):
                auth_url, state = self.get_authorization_url()
                st.markdown(f"""
                <script>
                window.open('{auth_url}', '_blank');
                </script>
                """, unsafe_allow_html=True)

                st.info("🔄 Redirecting to Red Hat SSO...")
                st.markdown(f"[Click here if redirect doesn't work]({auth_url})")

        # Development fallback
        st.markdown("---")
        with st.expander("🛠️ Development Mode"):
            st.markdown("**For development/testing without SSO:**")
            if st.button("Use Demo Login", type="secondary"):
                st.session_state['dev_mode'] = True
                st.rerun()

    def is_authenticated(self) -> bool:
        """Check if user is authenticated via SSO"""
        if 'sso_user' in st.session_state:
            user = st.session_state['sso_user']
            expires_at = datetime.fromisoformat(user['expires_at'])

            if datetime.utcnow() < expires_at:
                return True
            else:
                # Try to refresh token
                if 'refresh_token' in user:
                    new_tokens = self.refresh_access_token(user['refresh_token'])
                    if new_tokens:
                        # Update session with new tokens
                        user['access_token'] = new_tokens['access_token']
                        user['expires_at'] = (datetime.utcnow() +
                                            timedelta(seconds=new_tokens.get('expires_in', 3600))).isoformat()
                        st.session_state['sso_user'] = user
                        return True

                # Token refresh failed, clear session
                self.logout()
                return False

        return False

    def require_sso_auth(self):
        """Require SSO authentication"""
        # Handle OAuth callback
        callback_user = self.handle_callback()
        if callback_user:
            st.session_state['sso_user'] = callback_user
            st.success(f"Welcome, {callback_user['name']}!")
            st.rerun()

        # Check if authenticated
        if not self.is_authenticated():
            self.sso_login_ui()
            st.stop()

    def logout(self):
        """Logout from SSO"""
        refresh_token = None
        if 'sso_user' in st.session_state:
            refresh_token = st.session_state['sso_user'].get('refresh_token')
            del st.session_state['sso_user']

        # Generate logout URL
        logout_url = self.logout_from_sso(refresh_token)

        st.markdown(f"""
        <script>
        window.location.href = '{logout_url}';
        </script>
        """, unsafe_allow_html=True)

    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user"""
        return st.session_state.get('sso_user')

# Global SSO auth instance
rh_sso_auth = RedHatSSOAuth()