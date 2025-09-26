"""
Secure RedHat LDAP Analytics Dashboard
Enhanced with authentication, authorization, and audit logging
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

# Security imports
from auth import auth
from audit_logger import audit_logger
from data_security import data_security
from secure_config import secure_config

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import our data collector
try:
    from mcp_data_collector import MCPDataCollector
except ImportError:
    st.error("Failed to import MCPDataCollector. Make sure the module is available.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="RedHat LDAP Analytics - Secure",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load secure configuration
config = secure_config.load_config()

# Custom CSS for security styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #ee0000;
        text-align: center;
        margin-bottom: 2rem;
    }
    .security-banner {
        background: linear-gradient(90deg, #ee0000, #cc0000);
        color: white;
        padding: 0.5rem;
        text-align: center;
        font-weight: bold;
        margin-bottom: 1rem;
        border-radius: 0.25rem;
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
    """Enhanced session security checks"""
    # Check for session hijacking
    if 'session_fingerprint' not in st.session_state:
        st.session_state['session_fingerprint'] = hash(str(datetime.now()))

    # Log session activity
    audit_logger.log_session_activity('page_access', {'page': 'dashboard'})

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_secure_data(user_role: str, user_context: dict):
    """Load and cache LDAP data with security controls"""
    try:
        # Log data access
        audit_logger.log_data_access('people_data', {'user_role': user_role})

        collector = MCPDataCollector()

        # Collect data
        people_df = collector.collect_sample_data()
        location_df = collector.collect_location_data()
        geo_df = collector.collect_geo_data()
        geo_map_df = collector.collect_geo_map_data()
        summary = collector.get_analytics_summary()

        # Apply security filters
        people_df = data_security.filter_data_by_access_level(people_df, user_role, user_context)
        people_df = data_security.apply_data_masking(people_df, user_role)

        return people_df, location_df, geo_df, geo_map_df, summary
    except Exception as e:
        audit_logger.log_security_event(f"Data loading error: {e}", 'ERROR')
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

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

def create_secure_export(df: pd.DataFrame, export_format: str, user_role: str):
    """Create secure data export with audit logging"""
    if not data_security.check_data_access_permission('export', user_role,
                                                     st.session_state.get('user', {}).get('permissions', [])):
        st.error("❌ You don't have permission to export data")
        return

    # Sanitize data for export
    sanitized_df = data_security.sanitize_export_data(df, export_format, user_role)

    # Log export
    audit_logger.log_data_export('people_data', len(sanitized_df), export_format)

    # Create download
    if export_format.lower() == 'csv':
        csv_data = sanitized_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"ldap_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def create_team_geomap(geo_map_df):
    """Create interactive geographic map of team locations"""
    if geo_map_df.empty:
        return None

    # Create scatter mapbox plot
    fig = px.scatter_mapbox(
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
            title="Team Size",
            titleside="right"
        )
    )

    return fig

def main():
    """Main secure dashboard function"""

    # Security banner
    st.markdown('<div class="security-banner">🔐 SECURE ACCESS - CONFIDENTIAL DATA - RED HAT INTERNAL</div>',
                unsafe_allow_html=True)

    # Authentication check
    auth.require_auth()

    # Additional security checks
    check_session_security()

    # Get user context
    user = st.session_state.get('user', {})
    user_role = user.get('role', 'viewer')
    user_name = user.get('name', 'Unknown')

    # Header with user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<h1 class="main-header">🔐 RedHat LDAP Analytics Dashboard</h1>',
                   unsafe_allow_html=True)
    with col2:
        st.markdown(f"**Welcome, {user_name}**")
        st.markdown(f"Role: `{user_role.title()}`")
        if st.button("🚪 Logout"):
            audit_logger.log_session_activity('logout')
            auth.logout()

    # Sidebar with security info
    st.sidebar.markdown('<div class="sidebar-info">🛡️ <strong>Security Status</strong><br>All access is monitored and logged</div>',
                       unsafe_allow_html=True)

    # Permission-based feature controls
    if not data_security.check_data_access_permission('analytics', user_role, user.get('permissions', [])):
        st.error("❌ You don't have permission to view analytics data")
        st.stop()

    # Data refresh controls
    st.sidebar.subheader("Data Controls")
    if st.sidebar.button("🔄 Refresh Data"):
        audit_logger.log_session_activity('data_refresh')
        st.cache_data.clear()
        st.rerun()

    # Load data with security
    with st.spinner("Loading secure data..."):
        people_df, location_df, geo_df, geo_map_df, summary = load_secure_data(user_role, user)

    if people_df.empty and not summary:
        st.error("❌ Unable to load data or insufficient permissions")
        st.stop()

    # Key Metrics Row (role-based)
    st.subheader("📊 Key Metrics")

    if summary:
        col1, col2, col3, col4 = st.columns(4)

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
            locations_count = len(summary.get('location_distribution', {}))
            st.metric("Locations", locations_count)

    # Charts Section (role-based visibility)
    if user_role in ['admin', 'manager']:
        st.subheader("📈 Analytics")

        if not people_df.empty:
            seniority_fig = create_seniority_charts(people_df)
            if seniority_fig:
                st.plotly_chart(seniority_fig, use_container_width=True)

            # Geographic Map Section (for admins and managers)
            if user_role in ['admin', 'manager']:
                st.subheader("🌍 Global Team Map")
                if not geo_map_df.empty:
                    geomap_fig = create_team_geomap(geo_map_df)
                    if geomap_fig:
                        st.plotly_chart(geomap_fig, use_container_width=True)
                        audit_logger.log_session_activity('viewed_geomap', {'user_role': user_role})
                    else:
                        st.info("Geographic map not available")

            # Export functionality (admin/manager only)
            if user_role == 'admin':
                st.subheader("📤 Secure Export")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Export as CSV"):
                        create_secure_export(people_df, 'csv', user_role)
                with col2:
                    st.info("Exports are logged and audited")

    # Data Explorer (role-based)
    st.subheader("📋 Data Explorer")

    if user_role == 'admin':
        # Admins see all tabs
        tab1, tab2, tab3 = st.tabs(["👥 People", "📍 Locations", "🌍 Geographic"])

        with tab1:
            if not people_df.empty:
                st.dataframe(people_df, use_container_width=True)
            else:
                st.info("No people data available")

        with tab2:
            if not location_df.empty:
                st.dataframe(location_df, use_container_width=True)
            else:
                st.info("No location data available")

        with tab3:
            if not geo_df.empty:
                st.dataframe(geo_df, use_container_width=True)
            else:
                st.info("No geographic data available")

    elif user_role == 'manager':
        # Managers see limited data
        if not people_df.empty:
            st.dataframe(people_df, use_container_width=True)
        else:
            st.info("No team data available")

    else:
        # Viewers see summary only
        if summary:
            st.json(summary)
        else:
            st.info("Summary data not available")

    # Footer with security info
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("🔧 **RedHat LDAP Analytics Dashboard** | Secured with Authentication & Audit Logging")
    with col2:
        if summary.get('last_updated'):
            st.markdown(f"Last updated: {summary['last_updated']}")

    # Session info for admins
    if user_role == 'admin':
        with st.expander("🔍 Session Information"):
            st.json({
                'user': user_name,
                'role': user_role,
                'permissions': user.get('permissions', []),
                'session_start': st.session_state.get('session_start', 'Unknown'),
                'data_classification': 'CONFIDENTIAL'
            })

if __name__ == "__main__":
    main()