"""
RedHat LDAP Analytics Dashboard
A Streamlit-based analytics dashboard for organizational insights
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

# Import our data collector
try:
    from mcp_data_collector import MCPDataCollector
except ImportError:
    st.error("Failed to import MCPDataCollector. Make sure the module is available.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="RedHat LDAP Analytics",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #ee0000;
        text-align: center;
        margin-bottom: 2rem;
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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    """Load and cache LDAP data"""
    try:
        collector = MCPDataCollector()

        # Collect data (this would be expensive, so we cache it)
        people_df = collector.collect_sample_data()
        location_df = collector.collect_location_data()
        geo_df = collector.collect_geo_data()
        geo_map_df = collector.collect_geo_map_data()
        summary = collector.get_analytics_summary()

        return people_df, location_df, geo_df, geo_map_df, summary
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

def create_seniority_charts(people_df):
    """Create seniority distribution charts"""
    seniority_counts = people_df['seniority_level'].value_counts()

    # Create subplots
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

def create_location_map(location_df):
    """Create geographic distribution visualization"""
    if location_df.empty:
        return None

    # Simple bar chart for locations (could be enhanced with actual geographic mapping)
    fig = px.bar(
        location_df,
        x='location',
        y='people_count',
        title="Geographic Distribution",
        color='people_count',
        color_continuous_scale=['#ffeeee', '#ee0000']
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        height=400
    )

    return fig

def create_department_analysis(people_df):
    """Create department analysis charts"""
    dept_counts = people_df['department'].value_counts().head(10)

    fig = px.bar(
        x=dept_counts.values,
        y=dept_counts.index,
        orientation='h',
        title="Top 10 Departments by Size",
        color=dept_counts.values,
        color_continuous_scale=['#ffeeee', '#ee0000']
    )

    fig.update_layout(height=400)
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

    # Add custom hover template
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" +
                      "Country: %{customdata[2]}<br>" +
                      "Team Size: %{marker.size}<br>" +
                      "<extra></extra>",
        customdata=geo_map_df[['latitude', 'longitude', 'country']].values
    )

    return fig

def create_regional_breakdown(people_df):
    """Create regional breakdown chart"""
    if people_df.empty:
        return None

    # Group by geographic region
    region_counts = people_df['geo'].value_counts()

    # Create a donut chart for regions
    fig = go.Figure(data=[go.Pie(
        labels=region_counts.index,
        values=region_counts.values,
        hole=0.4,
        marker_colors=['#ee0000', '#cc0000', '#aa0000', '#880000']
    )])

    fig.update_layout(
        title="Team Distribution by Region",
        height=400,
        annotations=[dict(text='Regional<br>Distribution', x=0.5, y=0.5, font_size=12, showarrow=False)]
    )

    return fig


def main():
    """Main dashboard function"""

    # Header
    st.markdown('<h1 class="main-header">🏢 RedHat LDAP Analytics Dashboard</h1>', unsafe_allow_html=True)

    # Sidebar
    st.sidebar.markdown('<div class="sidebar-info">💡 <strong>Analytics Dashboard</strong><br>Real-time insights from RedHat LDAP directory</div>', unsafe_allow_html=True)

    # Data refresh controls
    st.sidebar.subheader("Data Controls")
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # Load data
    with st.spinner("Loading LDAP data..."):
        people_df, location_df, geo_df, geo_map_df, summary = load_data()

    if people_df.empty and not summary:
        st.error("❌ Unable to load LDAP data. Please check your connection and configuration.")
        st.stop()

    # Key Metrics Row
    st.subheader("📊 Key Metrics")

    if summary:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total People", summary.get('total_people', 'N/A'))

        with col2:
            st.metric("Managers", summary.get('manager_count', 'N/A'))

        with col3:
            manager_ratio = summary.get('manager_count', 0) / summary.get('total_people', 1) * 100
            st.metric("Manager Ratio", f"{manager_ratio:.1f}%")

        with col4:
            locations_count = len(summary.get('location_distribution', {}))
            st.metric("Locations", locations_count)

    # Charts Section
    st.subheader("📈 Analytics")

    # Seniority Analysis
    if not people_df.empty:
        st.plotly_chart(create_seniority_charts(people_df), width='stretch')

        # Geographic Map Section
        st.subheader("🌍 Global Team Map")
        if not geo_map_df.empty:
            geomap_fig = create_team_geomap(geo_map_df)
            if geomap_fig:
                st.plotly_chart(geomap_fig, width='stretch')
            else:
                st.info("Geographic map not available")

            # Geographic breakdown in columns
            col1, col2 = st.columns(2)

            with col1:
                regional_fig = create_regional_breakdown(people_df)
                if regional_fig:
                    st.plotly_chart(regional_fig, width='stretch')

            with col2:
                if not location_df.empty:
                    st.plotly_chart(create_location_map(location_df), width='stretch')
                else:
                    st.info("Location data not available")

        # Additional Charts
        st.subheader("📊 Additional Analytics")
        col1, col2 = st.columns(2)

        with col1:
            st.plotly_chart(create_department_analysis(people_df), width='stretch')

        with col2:
            # Show geographic statistics
            if not people_df.empty:
                st.markdown("**Geographic Statistics**")
                geo_stats = people_df.groupby('country').size().reset_index(name='team_size')
                st.dataframe(geo_stats, width='stretch')


    # Data Tables
    st.subheader("📋 Data Explorer")

    tab1, tab2, tab3 = st.tabs(["👥 People", "📍 Locations", "🌍 Geographic"])

    with tab1:
        if not people_df.empty:
            st.dataframe(people_df, width='stretch')
        else:
            st.info("People data not available")

    with tab2:
        if not location_df.empty:
            st.dataframe(location_df, width='stretch')
        else:
            st.info("Location data not available")

    with tab3:
        if not geo_df.empty:
            st.dataframe(geo_df, width='stretch')
        else:
            st.info("Geographic data not available")

    # Footer
    st.markdown("---")
    st.markdown("🔧 **RedHat LDAP Analytics Dashboard** | Built with Streamlit & Plotly")
    if summary.get('last_updated'):
        st.markdown(f"Last updated: {summary['last_updated']}")

if __name__ == "__main__":
    main()