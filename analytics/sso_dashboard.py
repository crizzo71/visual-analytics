"""
Red Hat SSO Enabled Analytics Dashboard
Enterprise-grade authentication with Red Hat Single Sign-On
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import our modules
try:
    from mcp_data_collector import MCPDataCollector
    from rh_sso_auth import rh_sso_auth
    from audit_logger import audit_logger
    from data_security import data_security
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="RedHat LDAP Analytics - SSO",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Red Hat branding
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #ee0000;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sso-banner {
        background: linear-gradient(90deg, #ee0000, #cc0000);
        color: white;
        padding: 0.5rem;
        text-align: center;
        font-weight: bold;
        margin-bottom: 1rem;
        border-radius: 0.25rem;
    }
    .user-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ee0000;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ee0000;
    }
    .sidebar-info {
        background-color: #f0f0f0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def check_session_security():
    """Enhanced session security checks for SSO"""
    user = rh_sso_auth.get_current_user()
    if user:
        # Log session activity
        audit_logger.log_session_activity('page_access', {
            'page': 'sso_dashboard',
            'sso_user': user.get('username', ''),
            'role': user.get('role', ''),
            'auth_method': 'red_hat_sso'
        })

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_secure_data(user_role: str, user_context: dict):
    """Load and cache LDAP data with SSO security controls"""
    try:
        # Log data access with SSO context
        audit_logger.log_data_access('people_data', {
            'user_role': user_role,
            'sso_user': user_context.get('username', ''),
            'auth_method': 'red_hat_sso'
        })

        collector = MCPDataCollector()

        # Collect data
        people_df = collector.collect_sample_data()
        location_df = collector.collect_location_data()
        geo_df = collector.collect_geo_data()
        geo_map_df = collector.collect_geo_map_data()
        summary = collector.get_analytics_summary()

        # Apply security filters based on SSO roles
        people_df = data_security.filter_data_by_access_level(people_df, user_role, user_context)
        people_df = data_security.apply_data_masking(people_df, user_role)

        return people_df, location_df, geo_df, geo_map_df, summary
    except Exception as e:
        audit_logger.log_security_event(f"SSO Data loading error: {e}", 'ERROR')
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

def create_seniority_charts(people_df):
    """Create seniority distribution charts"""
    if people_df.empty:
        return None

    seniority_counts = people_df['seniority_level'].value_counts()

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "bar"}, {"type": "pie"}]],
        subplot_titles=("Seniority Distribution", "Seniority Percentage")
    )

    # Bar chart
    fig.add_trace(
        go.Bar(
            x=seniority_counts.index,
            y=seniority_counts.values,
            name="Count",
            marker_color=['#ee0000', '#cc0000', '#aa0000', '#880000', '#660000', '#440000', '#220000']
        ),
        row=1, col=1
    )

    # Pie chart
    fig.add_trace(
        go.Pie(
            labels=seniority_counts.index,
            values=seniority_counts.values,
            name="Percentage",
            marker_colors=['#ee0000', '#cc0000', '#aa0000', '#880000', '#660000', '#440000', '#220000']
        ),
        row=1, col=2
    )

    fig.update_layout(
        title_text="Team Seniority Analysis",
        showlegend=False,
        height=400
    )

    return fig

def create_team_geomap(geo_map_df):
    """Create interactive geographic map of team locations"""
    if geo_map_df.empty:
        return None

    # Create scatter map plot
    fig = px.scatter_map(
        geo_map_df,
        lat='latitude',
        lon='longitude',
        size='count',
        color='count',
        hover_name='location',
        hover_data={
            'latitude': False,
            'longitude': False,
            'count': ':,',
            'country': True
        },
        color_continuous_scale=['#ffeeee', '#ee0000'],
        size_max=30,
        zoom=1,
        title="🌍 Global Team Distribution",
        height=500
    )

    # Update layout for better map display
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0,"t":50,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title=dict(text="Team Size", side="right")
        )
    )

    return fig

def create_secure_export(df: pd.DataFrame, export_format: str, user_role: str, user_context: dict):
    """Create secure data export with SSO audit logging"""
    if not data_security.check_data_access_permission('export', user_role,
                                                     user_context.get('permissions', [])):
        st.error("❌ You don't have permission to export data")
        return

    # Sanitize data for export
    sanitized_df = data_security.sanitize_export_data(df, export_format, user_role)

    # Log export with SSO context
    audit_logger.log_data_export('people_data', len(sanitized_df), export_format)
    audit_logger.log_session_activity('data_export', {
        'sso_user': user_context.get('username', ''),
        'role': user_role,
        'record_count': len(sanitized_df),
        'format': export_format
    })

    # Create download
    if export_format.lower() == 'csv':
        csv_data = sanitized_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"ldap_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def display_user_info_banner(user: dict):
    """Display user information banner with SSO details"""
    st.markdown('<div class="sso-banner">🔐 RED HAT SSO AUTHENTICATED SESSION</div>',
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"""
        <div class="user-info">
        <strong>👤 {user.get('name', 'Unknown User')}</strong><br>
        📧 {user.get('email', 'No email')}<br>
        🏷️ Role: {user.get('role', 'viewer').title()}<br>
        🔑 Auth: Red Hat SSO
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("🔄 Refresh Session"):
            st.cache_data.clear()
            st.rerun()

    with col3:
        if st.button("🚪 SSO Logout"):
            audit_logger.log_session_activity('sso_logout', {
                'sso_user': user.get('username', ''),
                'role': user.get('role', '')
            })
            rh_sso_auth.logout()

def main():
    """Main SSO dashboard function"""

    # Require SSO authentication
    rh_sso_auth.require_sso_auth()

    # Additional security checks
    check_session_security()

    # Get user context
    user = rh_sso_auth.get_current_user()
    if not user:
        st.error("❌ SSO session not found")
        st.stop()

    user_role = user.get('role', 'viewer')
    user_name = user.get('name', 'Unknown')

    # Display user info banner
    display_user_info_banner(user)

    # Header
    st.markdown('<h1 class="main-header">🔐 RedHat LDAP Analytics - SSO Enterprise</h1>',
               unsafe_allow_html=True)

    # Sidebar with SSO info
    st.sidebar.markdown(f'''
    <div class="sidebar-info">
    <strong>🏢 Red Hat SSO</strong><br>
    User: {user.get('username', 'unknown')}<br>
    Role: {user_role.title()}<br>
    Groups: {', '.join(user.get('groups', [])[:3])}<br>
    🛡️ All access monitored
    </div>
    ''', unsafe_allow_html=True)

    # Permission-based feature controls
    if not data_security.check_data_access_permission('analytics', user_role, user.get('permissions', [])):
        st.error("❌ You don't have permission to view analytics data")
        st.stop()

    # Data refresh controls
    st.sidebar.subheader("Data Controls")
    if st.sidebar.button("🔄 Refresh Data"):
        audit_logger.log_session_activity('data_refresh', {'sso_user': user.get('username', '')})
        st.cache_data.clear()
        st.rerun()

    # Load data with SSO security
    with st.spinner("Loading secure data..."):
        people_df, location_df, geo_df, geo_map_df, summary = load_secure_data(user_role, user)

    if people_df.empty and not summary:
        st.error("❌ Unable to load data or insufficient permissions")
        st.stop()

    # Key Metrics Row (role-based)
    st.subheader("📊 Key Metrics")

    if summary:
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            accessible_count = len(people_df) if not people_df.empty else 0
            st.metric("Accessible Records", accessible_count)

        with col2:
            if user_role in ['admin', 'manager']:
                manager_count = summary.get('manager_count', 'N/A')
                st.metric("Managers", manager_count)
            else:
                st.metric("Your Access Level", user_role.title())

        with col3:
            if user_role == 'admin':
                manager_ratio = summary.get('manager_count', 0) / summary.get('total_people', 1) * 100
                st.metric("Manager Ratio", f"{manager_ratio:.1f}%")
            else:
                st.metric("Data Classification", "CONFIDENTIAL")

        with col4:
            # Manager to Employee Ratio (role-based access)
            if user_role in ['admin', 'manager']:
                total_people = summary.get('total_people', 1)
                manager_count = summary.get('manager_count', 0)
                if manager_count > 0:
                    employee_per_manager = (total_people - manager_count) / manager_count
                    st.metric("Manager:Employee", f"1:{employee_per_manager:.0f}")
                else:
                    st.metric("Manager:Employee", "N/A")
            else:
                st.metric("SSO Status", "AUTHENTICATED")

        with col5:
            locations_count = len(summary.get('location_distribution', {}))
            st.metric("Locations", locations_count)

    # Charts Section (role-based visibility)
    if user_role in ['admin', 'manager']:
        st.subheader("📈 Analytics")

        if not people_df.empty:
            seniority_fig = create_seniority_charts(people_df)
            if seniority_fig:
                st.plotly_chart(seniority_fig, config={'displayModeBar': False}, width='stretch')

            # Geographic Map Section (for admins and managers)
            if user_role in ['admin', 'manager']:
                st.subheader("🌍 Global Team Map")
                if not geo_map_df.empty:
                    geomap_fig = create_team_geomap(geo_map_df)
                    if geomap_fig:
                        st.plotly_chart(geomap_fig, config={'displayModeBar': False}, width='stretch')
                        audit_logger.log_session_activity('viewed_geomap', {
                            'user_role': user_role,
                            'sso_user': user.get('username', '')
                        })
                    else:
                        st.info("Geographic map not available")

            # Export functionality (admin/manager only)
            if user_role == 'admin':
                st.subheader("📤 Secure Export")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Export as CSV"):
                        create_secure_export(people_df, 'csv', user_role, user)
                with col2:
                    st.info("Exports are logged and audited")

    # Data Explorer (role-based)
    st.subheader("📋 Data Explorer")

    if user_role == 'admin':
        # Admins see all tabs
        tab1, tab2, tab3 = st.tabs(["👥 People", "📍 Locations", "🌍 Geographic"])

        with tab1:
            if not people_df.empty:
                st.dataframe(people_df, width='stretch')
            else:
                st.info("No people data available")

        with tab2:
            if not location_df.empty:
                st.dataframe(location_df, width='stretch')
            else:
                st.info("No location data available")

        with tab3:
            if not geo_df.empty:
                st.dataframe(geo_df, width='stretch')
            else:
                st.info("No geographic data available")

    elif user_role == 'manager':
        # Managers see limited data
        if not people_df.empty:
            st.dataframe(people_df, width='stretch')
        else:
            st.info("No team data available")

    else:
        # Viewers see summary only
        if summary:
            st.json(summary)
        else:
            st.info("Summary data not available")

    # Footer with SSO info
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("🔧 **RedHat LDAP Analytics Dashboard** | Secured with Red Hat SSO")
    with col2:
        if summary.get('last_updated'):
            st.markdown(f"Last updated: {summary['last_updated']}")

    # Session info for admins
    if user_role == 'admin':
        with st.expander("🔍 SSO Session Information"):
            st.json({
                'sso_username': user.get('username', ''),
                'name': user_name,
                'email': user.get('email', ''),
                'role': user_role,
                'permissions': user.get('permissions', []),
                'groups': user.get('groups', []),
                'session_start': user.get('session_start', 'Unknown'),
                'auth_method': 'red_hat_sso',
                'data_classification': 'CONFIDENTIAL'
            })

if __name__ == "__main__":
    main()