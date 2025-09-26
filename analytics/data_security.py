"""
Data Security and Privacy Controls for LDAP Analytics
"""

import pandas as pd
import re
from typing import Dict, List, Any
import hashlib

class DataSecurityManager:
    """Manages data security, masking, and access controls"""

    def __init__(self):
        # Define sensitive data patterns
        self.sensitive_fields = {
            'email': ['email', 'mail'],
            'phone': ['phone', 'telephone', 'mobile'],
            'employee_id': ['employee_id', 'employeeNumber', 'workerId'],
            'salary': ['salary', 'compensation'],
            'ssn': ['ssn', 'social_security'],
            'personal_id': ['personal_id', 'national_id']
        }

        # Data access levels
        self.access_levels = {
            'admin': ['all'],
            'manager': ['team_data', 'reporting_structure', 'basic_info'],
            'viewer': ['aggregated_data', 'public_info'],
            'auditor': ['audit_logs', 'access_reports']
        }

    def mask_email(self, email: str) -> str:
        """Mask email addresses for privacy"""
        if not email or '@' not in email:
            return email

        username, domain = email.split('@', 1)
        if len(username) <= 2:
            masked_username = '*' * len(username)
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]

        return f"{masked_username}@{domain}"

    def mask_phone(self, phone: str) -> str:
        """Mask phone numbers"""
        if not phone:
            return phone

        # Remove non-digits
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 10:
            return f"***-***-{digits[-4:]}"
        return "***-****"

    def mask_employee_id(self, emp_id: str) -> str:
        """Mask employee IDs"""
        if not emp_id:
            return emp_id

        if len(emp_id) <= 3:
            return '*' * len(emp_id)
        return emp_id[:2] + '*' * (len(emp_id) - 3) + emp_id[-1]

    def hash_sensitive_data(self, data: str, salt: str = "dashboard_salt") -> str:
        """Create consistent hash for sensitive data"""
        if not data:
            return data

        return hashlib.sha256(f"{data}{salt}".encode()).hexdigest()[:8]

    def apply_data_masking(self, df: pd.DataFrame, user_role: str) -> pd.DataFrame:
        """Apply appropriate data masking based on user role"""
        if user_role == 'admin':
            return df  # Admins see everything

        masked_df = df.copy()

        # Apply masking based on role
        if user_role in ['viewer', 'auditor']:
            # Mask all sensitive fields for viewers
            for column in masked_df.columns:
                if any(field in column.lower() for field in self.sensitive_fields['email']):
                    masked_df[column] = masked_df[column].apply(self.mask_email)
                elif any(field in column.lower() for field in self.sensitive_fields['phone']):
                    masked_df[column] = masked_df[column].apply(self.mask_phone)
                elif any(field in column.lower() for field in self.sensitive_fields['employee_id']):
                    masked_df[column] = masked_df[column].apply(self.mask_employee_id)

        elif user_role == 'manager':
            # Managers see less masking for their team
            for column in masked_df.columns:
                if any(field in column.lower() for field in self.sensitive_fields['phone']):
                    masked_df[column] = masked_df[column].apply(self.mask_phone)

        return masked_df

    def filter_data_by_access_level(self, df: pd.DataFrame, user_role: str, user_context: Dict) -> pd.DataFrame:
        """Filter data based on user access level"""
        if user_role == 'admin':
            return df

        filtered_df = df.copy()

        # Managers only see their team
        if user_role == 'manager':
            user_email = user_context.get('email', '')
            user_uid = user_email.split('@')[0] if '@' in user_email else ''

            # Filter to show only direct reports and their reports
            if 'manager' in filtered_df.columns:
                team_filter = (
                    (filtered_df['manager'] == user_uid) |
                    (filtered_df['uid'] == user_uid)
                )

                # Also include indirect reports (2 levels down)
                direct_reports = filtered_df[filtered_df['manager'] == user_uid]['uid'].tolist()
                if direct_reports:
                    indirect_filter = filtered_df['manager'].isin(direct_reports)
                    team_filter = team_filter | indirect_filter

                filtered_df = filtered_df[team_filter]

        # Viewers get aggregated data only
        elif user_role == 'viewer':
            # For viewers, only show aggregated statistics
            if len(filtered_df) > 0:
                # Create aggregated view
                agg_data = []
                if 'department' in filtered_df.columns:
                    dept_stats = filtered_df.groupby('department').agg({
                        'uid': 'count',
                        'seniority_level': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'
                    }).reset_index()
                    dept_stats.columns = ['Department', 'Team_Size', 'Common_Seniority']
                    return dept_stats

        return filtered_df

    def sanitize_export_data(self, df: pd.DataFrame, export_format: str, user_role: str) -> pd.DataFrame:
        """Sanitize data for export with additional security measures"""
        sanitized_df = df.copy()

        # Remove internal fields that shouldn't be exported
        internal_fields = ['password', 'hash', 'session', 'token', 'secret']
        columns_to_remove = [col for col in sanitized_df.columns
                           if any(field in col.lower() for field in internal_fields)]

        if columns_to_remove:
            sanitized_df = sanitized_df.drop(columns=columns_to_remove)

        # Apply role-based sanitization
        sanitized_df = self.apply_data_masking(sanitized_df, user_role)

        # Add export metadata for auditing
        if export_format.lower() == 'csv':
            # Add header comment for CSV
            sanitized_df.attrs['export_info'] = {
                'exported_by': user_role,
                'export_time': pd.Timestamp.now().isoformat(),
                'data_classification': 'CONFIDENTIAL - Red Hat Internal'
            }

        return sanitized_df

    def check_data_access_permission(self, data_type: str, user_role: str, user_permissions: List[str]) -> bool:
        """Check if user has permission to access specific data type"""
        permission_map = {
            'people_data': ['view_all', 'view_team'],
            'org_chart': ['view_all', 'view_team', 'view_reports'],
            'analytics': ['view_all', 'view_reports'],
            'export': ['export_data'],
            'audit_logs': ['view_audit', 'admin']
        }

        required_permissions = permission_map.get(data_type, ['view_all'])
        return any(perm in user_permissions for perm in required_permissions)

    def validate_search_parameters(self, search_params: Dict) -> Dict:
        """Validate and sanitize search parameters to prevent injection"""
        sanitized_params = {}

        for key, value in search_params.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized_value = re.sub(r'[<>"\';\\]', '', value)
                # Limit length to prevent DoS
                sanitized_value = sanitized_value[:100]
                sanitized_params[key] = sanitized_value
            else:
                sanitized_params[key] = value

        return sanitized_params

# Global data security manager
data_security = DataSecurityManager()