"""
MCP Data Collector for Analytics
Interfaces with the RedHat LDAP MCP server via HTTP to collect organizational data
"""

import json
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, List, Optional
import subprocess
import os

class MCPDataCollector:
    """Collects and processes LDAP data via MCP tools for analytics"""

    def __init__(self, mcp_server_url: str = "http://127.0.0.1:8814/redhat-ldap-mcp"):
        """Initialize the MCP data collector"""
        self.mcp_server_url = mcp_server_url
        self.data_cache = {}
        self.last_refresh = None

    def _call_mcp_tool(self, tool_name: str, arguments: Dict = None) -> Dict:
        """Call an MCP tool via Claude CLI"""
        if arguments is None:
            arguments = {}

        # Format the arguments as a query string
        arg_str = ", ".join([f"{k}='{v}'" for k, v in arguments.items()]) if arguments else ""

        # Create the command
        prompt = f"Use the {tool_name} tool"
        if arg_str:
            prompt += f" with arguments: {arg_str}"

        try:
            # Call via Claude CLI
            result = subprocess.run([
                "claude", "-p",
                "--allowedTools", f"mcp__redhat-ldap__{tool_name}",
                prompt
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                # Parse the response - this is simplified
                return {"success": True, "data": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_location_coordinates(self) -> Dict[str, Dict]:
        """Get latitude/longitude coordinates for team locations"""
        return {
            'Raleigh, NC, USA': {'lat': 35.7796, 'lon': -78.6382, 'country': 'United States'},
            'Raleigh, NC': {'lat': 35.7796, 'lon': -78.6382, 'country': 'United States'},
            'Beijing, China': {'lat': 39.9042, 'lon': 116.4074, 'country': 'China'},
            'Ra\'anana, Israel': {'lat': 32.1833, 'lon': 34.8667, 'country': 'Israel'},
            'Waterford, Ireland': {'lat': 52.2583, 'lon': -7.1119, 'country': 'Ireland'},
            'Boston, MA': {'lat': 42.3601, 'lon': -71.0589, 'country': 'United States'},
            'Brno, Czech Republic': {'lat': 49.1951, 'lon': 16.6068, 'country': 'Czech Republic'},
            'São Paulo, Brazil': {'lat': -23.5505, 'lon': -46.6333, 'country': 'Brazil'},
            'Madrid, Spain': {'lat': 40.4168, 'lon': -3.7038, 'country': 'Spain'}
        }

    def collect_sample_data(self) -> pd.DataFrame:
        """Collect sample organizational data for analytics"""

        # Get location coordinates
        location_coords = self.get_location_coordinates()

        # For now, we'll use the known data from your team
        sample_data = [
            {
                'uid': 'crizzo',
                'name': 'Christine Rizzo',
                'email': 'crizzo@redhat.com',
                'title': 'Senior Manager, Engineering',
                'department': 'R&D OpenShift Management',
                'location': 'Raleigh, NC, USA',
                'geo': 'Americas',
                'hire_date': '2019-05-31',
                'employee_type': 'Regular',
                'seniority_level': 'Senior Management',
                'is_manager': True,
                'manager': 'jlaska'
            },
            {
                'uid': 'twilliam',
                'name': 'Tim Williams',
                'email': 'twilliam@redhat.com',
                'title': 'Principal Software Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Raleigh, NC',
                'geo': 'Americas',
                'seniority_level': 'Principal',
                'is_manager': False,
                'manager': 'crizzo'
            },
            {
                'uid': 'ychang',
                'name': 'Yufen Chang',
                'email': 'ychang@redhat.com',
                'title': 'Manager, Engineering',
                'department': 'R&D OpenShift Management',
                'location': 'Beijing, China',
                'geo': 'APAC',
                'seniority_level': 'Management',
                'is_manager': True,
                'manager': 'crizzo'
            },
            {
                'uid': 'etabak',
                'name': 'Elad Tabak',
                'email': 'etabak@redhat.com',
                'title': 'Principal Software Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Ra\'anana, Israel',
                'geo': 'EMEA',
                'seniority_level': 'Principal',
                'is_manager': False,
                'manager': 'crizzo'
            },
            {
                'uid': 'croche',
                'name': 'Ciaran Roche',
                'email': 'croche@redhat.com',
                'title': 'Principal Software Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Waterford, Ireland',
                'geo': 'EMEA',
                'hire_date': '2018-01-08',
                'seniority_level': 'Principal',
                'is_manager': False,
                'manager': 'crizzo'
            },
            {
                'uid': 'rcampos',
                'name': 'Ren Campos',
                'email': 'rcampos@redhat.com',
                'title': 'Senior Software Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Boston, MA',
                'geo': 'Americas',
                'seniority_level': 'Senior',
                'is_manager': False,
                'manager': 'crizzo'
            },
            {
                'uid': 'mparilova',
                'name': 'Michaela Parilova',
                'email': 'mparilova@redhat.com',
                'title': 'Associate Software Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Brno, Czech Republic',
                'geo': 'EMEA',
                'seniority_level': 'Junior',
                'is_manager': False,
                'manager': 'crizzo'
            },
            {
                'uid': 'rbenevides',
                'name': 'Rafael Benevides',
                'email': 'rbenevides@redhat.com',
                'title': 'Principal Software Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'São Paulo, Brazil',
                'geo': 'Americas',
                'seniority_level': 'Principal',
                'is_manager': False,
                'manager': 'crizzo'
            },
            {
                'uid': 'jsell',
                'name': 'John Sell',
                'email': 'jsell@redhat.com',
                'title': 'Software Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Raleigh, NC',
                'geo': 'Americas',
                'seniority_level': 'Mid-Level',
                'is_manager': False,
                'manager': 'crizzo'
            },
            # Beijing team under Yufen
            {
                'uid': 'yisun',
                'name': 'Yi Sun',
                'email': 'yisun@redhat.com',
                'title': 'Senior Software Quality Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Beijing, China',
                'geo': 'APAC',
                'seniority_level': 'Senior',
                'is_manager': False,
                'manager': 'ychang'
            },
            {
                'uid': 'yanmingsun',
                'name': 'Yanming Sun',
                'email': 'yanmingsun@redhat.com',
                'title': 'Principal Software Quality Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Beijing, China',
                'geo': 'APAC',
                'seniority_level': 'Principal',
                'is_manager': False,
                'manager': 'ychang'
            },
            {
                'uid': 'xli',
                'name': 'Xue Li',
                'email': 'xli@redhat.com',
                'title': 'Principal Software Quality Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Beijing, China',
                'geo': 'APAC',
                'seniority_level': 'Principal',
                'is_manager': False,
                'manager': 'ychang'
            },
            {
                'uid': 'yzhang',
                'name': 'Ying Zhang',
                'email': 'yzhang@redhat.com',
                'title': 'Software Quality Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Beijing, China',
                'geo': 'APAC',
                'seniority_level': 'Mid-Level',
                'is_manager': False,
                'manager': 'ychang'
            },
            {
                'uid': 'zwang',
                'name': 'Zhe Wang',
                'email': 'zwang@redhat.com',
                'title': 'Senior Software Quality Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Beijing, China',
                'geo': 'APAC',
                'seniority_level': 'Senior',
                'is_manager': False,
                'manager': 'ychang'
            },
            {
                'uid': 'dwang',
                'name': 'dandan wang',
                'email': 'dwang@redhat.com',
                'title': 'Senior Software Quality Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Beijing, China',
                'geo': 'APAC',
                'seniority_level': 'Senior',
                'is_manager': False,
                'manager': 'ychang'
            },
            {
                'uid': 'amarin',
                'name': 'Angel Marin',
                'email': 'amarin@redhat.com',
                'title': 'Principal Software Engineer',
                'department': 'R&D OpenShift Management',
                'location': 'Madrid, Spain',
                'geo': 'EMEA',
                'seniority_level': 'Principal',
                'is_manager': False,
                'manager': 'ychang'
            }
        ]

        # Add geographic coordinates to the data
        for person in sample_data:
            location = person['location']
            coords = location_coords.get(location, {})
            person['latitude'] = coords.get('lat', 0)
            person['longitude'] = coords.get('lon', 0)
            person['country'] = coords.get('country', 'Unknown')

        df = pd.DataFrame(sample_data)
        self.data_cache['people'] = df
        self.last_refresh = datetime.now()
        return df

    def collect_geo_map_data(self) -> pd.DataFrame:
        """Collect data specifically formatted for geographic mapping"""
        people_df = self.data_cache.get('people', self.collect_sample_data())

        # Group by location for map visualization
        geo_data = people_df.groupby(['location', 'latitude', 'longitude', 'country']).agg({
            'name': lambda x: list(x),
            'title': lambda x: list(x),
            'seniority_level': lambda x: list(x),
            'uid': 'count'
        }).reset_index()

        geo_data.columns = ['location', 'latitude', 'longitude', 'country', 'team_members', 'titles', 'seniority_levels', 'count']

        # Create hover text with team member details
        geo_data['hover_text'] = geo_data.apply(lambda row:
            f"<b>{row['location']}</b><br>" +
            f"Team Size: {row['count']}<br>" +
            f"Members: {', '.join(row['team_members'][:3])}" +
            (f"<br>... and {row['count']-3} more" if row['count'] > 3 else ""),
            axis=1
        )

        return geo_data

    def collect_location_data(self) -> pd.DataFrame:
        """Collect location distribution data"""
        people_df = self.data_cache.get('people', self.collect_sample_data())

        location_counts = people_df.groupby('location').size().reset_index(name='people_count')
        location_counts['people'] = location_counts['location'].apply(
            lambda loc: people_df[people_df['location'] == loc]['name'].tolist()
        )

        self.data_cache['locations'] = location_counts
        return location_counts

    def collect_geo_data(self) -> pd.DataFrame:
        """Collect geographic distribution data"""
        people_df = self.data_cache.get('people', self.collect_sample_data())

        geo_counts = people_df.groupby('geo').size().reset_index(name='people_count')
        geo_counts['locations'] = geo_counts['geo'].apply(
            lambda geo: people_df[people_df['geo'] == geo]['location'].unique().tolist()
        )

        return geo_counts

    def get_analytics_summary(self) -> Dict:
        """Generate analytics summary"""
        people_df = self.data_cache.get('people', self.collect_sample_data())

        summary = {
            'total_people': len(people_df),
            'seniority_distribution': people_df['seniority_level'].value_counts().to_dict(),
            'location_distribution': people_df['location'].value_counts().to_dict(),
            'geo_distribution': people_df['geo'].value_counts().to_dict(),
            'department_distribution': people_df['department'].value_counts().to_dict(),
            'manager_count': len(people_df[people_df['is_manager'] == True]),
            'manager_ratio': len(people_df[people_df['is_manager'] == True]) / len(people_df) * 100,
            'last_updated': self.last_refresh.isoformat() if self.last_refresh else None
        }

        return summary

    def test_mcp_connection(self) -> bool:
        """Test MCP server connection"""
        try:
            result = self._call_mcp_tool("test_connection")
            return result.get('success', False)
        except Exception as e:
            print(f"Error testing MCP connection: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    collector = MCPDataCollector()

    print("Testing MCP Data Collector...")
    print("=" * 50)

    # Test data collection
    try:
        people_df = collector.collect_sample_data()
        print(f"✅ Collected data for {len(people_df)} people")

        summary = collector.get_analytics_summary()
        print("✅ Analytics Summary:")
        for key, value in summary.items():
            if isinstance(value, dict) and len(value) > 3:
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {value}")

        locations_df = collector.collect_location_data()
        print(f"✅ Collected location data for {len(locations_df)} locations")

    except Exception as e:
        print(f"❌ Error: {e}")