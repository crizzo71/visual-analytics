"""
LDAP Data Collector for Analytics
Interfaces with the RedHat LDAP MCP server to collect organizational data
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import requests

# Add the src directory to the path to import MCP modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from redhat_ldap_mcp.core.ldap_connector import LDAPConnector
from redhat_ldap_mcp.config.models import Config

class LDAPDataCollector:
    """Collects and processes LDAP data for analytics"""

    def __init__(self, config_path: str = "config/my-ldap.json"):
        """Initialize the data collector"""
        self.config = Config.from_file(config_path)
        self.ldap_client = LDAPConnector(self.config.ldap)
        self.data_cache = {}
        self.last_refresh = None

    def collect_all_people(self) -> pd.DataFrame:
        """Collect comprehensive data about all people in the organization"""
        try:
            # Search for all people
            search_results = self.ldap_client.search_people("*", limit=5000)

            people_data = []
            for person in search_results:
                person_details = self.ldap_client.get_person_details(person.get('uid', ''))
                if person_details:
                    people_data.append(self._normalize_person_data(person_details))

            df = pd.DataFrame(people_data)
            self.data_cache['people'] = df
            self.last_refresh = datetime.now()
            return df

        except Exception as e:
            print(f"Error collecting people data: {e}")
            return pd.DataFrame()

    def collect_org_structure(self, manager_uid: str = None) -> Dict:
        """Collect organizational structure data"""
        try:
            if manager_uid:
                org_data = self.ldap_client.get_organization_chart(manager_uid)
            else:
                # Start from top-level managers
                org_data = self._build_complete_org_chart()

            self.data_cache['org_structure'] = org_data
            return org_data

        except Exception as e:
            print(f"Error collecting org structure: {e}")
            return {}

    def collect_location_data(self) -> pd.DataFrame:
        """Collect location and geographic distribution data"""
        try:
            locations = self.ldap_client.find_locations()
            location_data = []

            for location in locations:
                people_at_location = self.ldap_client.get_people_at_location(location)
                location_data.append({
                    'location': location,
                    'people_count': len(people_at_location),
                    'people': people_at_location
                })

            df = pd.DataFrame(location_data)
            self.data_cache['locations'] = df
            return df

        except Exception as e:
            print(f"Error collecting location data: {e}")
            return pd.DataFrame()

    def collect_groups_data(self) -> pd.DataFrame:
        """Collect group and team membership data"""
        try:
            groups = self.ldap_client.search_groups("*", limit=1000)
            group_data = []

            for group in groups:
                group_details = self.ldap_client.get_group_members(group.get('cn', ''))
                if group_details:
                    group_data.append({
                        'group_name': group.get('cn', ''),
                        'description': group.get('description', ''),
                        'member_count': len(group_details.get('members', [])),
                        'members': group_details.get('members', [])
                    })

            df = pd.DataFrame(group_data)
            self.data_cache['groups'] = df
            return df

        except Exception as e:
            print(f"Error collecting groups data: {e}")
            return pd.DataFrame()

    def _normalize_person_data(self, person: Dict) -> Dict:
        """Normalize person data for analytics"""
        return {
            'uid': person.get('uid', ''),
            'name': person.get('displayName', person.get('cn', '')),
            'email': person.get('mail', ''),
            'title': person.get('title', ''),
            'department': person.get('rhatCostCenterDesc', person.get('department', '')),
            'location': person.get('rhatLocation', ''),
            'geo': person.get('rhatGeo', ''),
            'manager': person.get('manager', ''),
            'hire_date': person.get('rhatHireDate', person.get('rhatOriginalHireDate', '')),
            'employee_type': person.get('employeeType', ''),
            'job_role': person.get('rhatJobRole', ''),
            'organization': person.get('rhatOrganization', ''),
            'cost_center': person.get('rhatCostCenter', ''),
            'phone': person.get('telephoneNumber', ''),
            'seniority_level': self._determine_seniority(person.get('title', '')),
            'is_manager': self._is_manager(person),
            'building_code': person.get('rhatBuildingCode', ''),
            'office_location': person.get('rhatOfficeLocation', '')
        }

    def _determine_seniority(self, title: str) -> str:
        """Determine seniority level from job title"""
        title_lower = title.lower()

        if any(level in title_lower for level in ['director', 'vp', 'vice president', 'chief']):
            return 'Executive'
        elif any(level in title_lower for level in ['senior manager', 'principal manager']):
            return 'Senior Management'
        elif 'manager' in title_lower:
            return 'Management'
        elif 'principal' in title_lower:
            return 'Principal'
        elif 'senior' in title_lower:
            return 'Senior'
        elif any(level in title_lower for level in ['associate', 'junior']):
            return 'Junior'
        else:
            return 'Mid-Level'

    def _is_manager(self, person: Dict) -> bool:
        """Determine if person is a manager"""
        title = person.get('title', '').lower()
        return 'manager' in title or 'director' in title or 'lead' in title

    def _build_complete_org_chart(self) -> Dict:
        """Build complete organizational chart"""
        # This would require recursive traversal
        # For now, return a simplified structure
        return {
            'message': 'Complete org chart collection requires recursive implementation',
            'timestamp': datetime.now().isoformat()
        }

    def get_analytics_summary(self) -> Dict:
        """Generate analytics summary"""
        if 'people' not in self.data_cache:
            self.collect_all_people()

        people_df = self.data_cache.get('people', pd.DataFrame())

        if people_df.empty:
            return {'error': 'No people data available'}

        summary = {
            'total_people': len(people_df),
            'seniority_distribution': people_df['seniority_level'].value_counts().to_dict(),
            'location_distribution': people_df['location'].value_counts().head(10).to_dict(),
            'department_distribution': people_df['department'].value_counts().head(10).to_dict(),
            'manager_count': len(people_df[people_df['is_manager'] == True]),
            'last_updated': self.last_refresh.isoformat() if self.last_refresh else None
        }

        return summary

# Example usage and testing
if __name__ == "__main__":
    collector = LDAPDataCollector()

    print("Testing LDAP Data Collector...")
    print("=" * 50)

    # Test connection
    try:
        summary = collector.get_analytics_summary()
        print("✅ Analytics Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ Error: {e}")