import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json
import urllib.request

# Page configuration
st.set_page_config(
    page_title="UIDAI Biometric Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Metrics Styling */
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 5px;
        border-top: 3px solid #09447d;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: #666;
        font-size: 0.9rem;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #09447d;
        font-weight: 700;
        font-size: 1.8rem;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #09447d;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1 {
        border-bottom: 2px solid #f39c12;
        padding-bottom: 15px;
        margin-bottom: 25px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 4px 4px 0 0;
        color: #09447d;
        border: 1px solid #e0e0e0;
        border-bottom: none;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #09447d;
        color: white;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eaeaea;
    }
    
    /* Buttons */
    div.stButton > button {
        background-color: #09447d;
        color: white;
        border-radius: 4px;
        border: none;
        padding: 0.5rem 1rem;
    }
    div.stButton > button:hover {
        background-color: #062f56;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load all CSV data files"""
    data_files = []
    
    # Check for data files in the directory structure
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Look for CSV files in data directories
    for folder in ['data1.csv', 'data2.csv', 'data3.csv']:
        folder_path = os.path.join(base_path, folder)
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith('.csv'):
                    file_path = os.path.join(folder_path, file)
                    data_files.append(file_path)
    
    # Load and combine all data
    if data_files:
        dfs = []
        for file in data_files:
            try:
                df = pd.read_csv(file)
                dfs.append(df)
            except Exception as e:
                st.warning(f"Could not load {file}: {e}")
        
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            # Convert date column to datetime
            if 'date' in combined_df.columns:
                combined_df['date'] = pd.to_datetime(combined_df['date'], format='%d-%m-%Y', errors='coerce')
            return combined_df
    
    return pd.DataFrame()

@st.cache_data
def load_geojson():
    """Load India States GeoJSON"""
    url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    try:
        with urllib.request.urlopen(url) as response:
            geojson = json.load(response)
        return geojson
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return None

def main():
    # Header Section
    col1, col2 = st.columns([1, 5])
    with col1:
        # Placeholder for Emblem if needed, or just text
        st.markdown("## 🏛️")
    with col2:
        st.markdown("# Unique Identification Authority of India")
        st.markdown("### Aadhaar Biometric Authentication Dashboard")
        st.markdown("*Government of India*")
    
    # Load data
    with st.spinner("Loading secure data..."):
        df = load_data()
    
    if df.empty:
        st.error("System Notification: Data unavailable. Please verify data files.")
        return
    
    # Sidebar filters with UIDAI style
    st.sidebar.markdown("### � Search & Filter")
    st.sidebar.info("Authorized Personnel Only")

    
    # Date filter
    if 'date' in df.columns and not df['date'].isna().all():
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(df['date'].min(), df['date'].max()),
            min_value=df['date'].min(),
            max_value=df['date'].max()
        )
        
        if len(date_range) == 2:
            df = df[(df['date'] >= pd.Timestamp(date_range[0])) & 
                   (df['date'] <= pd.Timestamp(date_range[1]))]
    
    # State filter
    if 'state' in df.columns:
        states = ['All'] + sorted(df['state'].dropna().unique().tolist())
        selected_state = st.sidebar.selectbox("Select State", states)
        
        if selected_state != 'All':
            df = df[df['state'] == selected_state]
    
    # District filter
    if 'district' in df.columns and selected_state != 'All':
        districts = ['All'] + sorted(df['district'].dropna().unique().tolist())
        selected_district = st.sidebar.selectbox("Select District", districts)
        
        if selected_district != 'All':
            df = df[df['district'] == selected_district]
    
    # Calculate metrics
    total_records = len(df)
    
    # Age group columns - Ensure they exist to prevent KeyErrors
    age_5_17_col = 'bio_age_5_17'
    age_17_plus_col = 'bio_age_17_'
    
    if age_5_17_col not in df.columns:
        df[age_5_17_col] = 0
    if age_17_plus_col not in df.columns:
        df[age_17_plus_col] = 0
    
    total_age_5_17 = df[age_5_17_col].sum() if age_5_17_col else 0
    total_age_17_plus = df[age_17_plus_col].sum() if age_17_plus_col else 0
    total_authentications = total_age_5_17 + total_age_17_plus
    
    # Display key metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📍 Total Records",
            value=f"{total_records:,}",
            delta="Locations"
        )
    
    with col2:
        st.metric(
            label="✅ Total Authentications",
            value=f"{total_authentications:,}",
            delta="All Age Groups"
        )
    
    with col3:
        st.metric(
            label="👶 Age 5-17",
            value=f"{total_age_5_17:,}",
            delta=f"{(total_age_5_17/total_authentications*100):.1f}%" if total_authentications > 0 else "0%"
        )
    
    with col4:
        st.metric(
            label="👨 Age 17+",
            value=f"{total_age_17_plus:,}",
            delta=f"{(total_age_17_plus/total_authentications*100):.1f}%" if total_authentications > 0 else "0%"
        )
    
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overview", "🗺️ Geographic Analysis", "📊 Age Distribution", "📋 Data Table", "🇮🇳 India Map & Heatmaps"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Top 10 states by authentications
            if 'state' in df.columns:
                state_data = df.groupby('state').agg({
                    age_5_17_col: 'sum' if age_5_17_col else lambda x: 0,
                    age_17_plus_col: 'sum' if age_17_plus_col else lambda x: 0
                }).reset_index()
                state_data['total'] = state_data[age_5_17_col] + state_data[age_17_plus_col]
                state_data = state_data.nlargest(10, 'total')
                
                
                fig = px.bar(
                    state_data,
                    x='total',
                    y='state',
                    orientation='h',
                    title='Top 10 States by Authentications',
                    labels={'total': 'Total Authentications', 'state': 'State'},
                    color='total',
                    color_continuous_scale=['#d0e1f5', '#09447d'] # Custom Blue Scale
                )
                fig.update_layout(
                    height=400,
                    template="plotly_white",
                    title_font=dict(size=18, color='#09447d', family="Segoe UI"),
                    font=dict(color="#333"),
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Age group distribution pie chart
            age_dist_data = pd.DataFrame({
                'Age Group': ['5-17 Years', '17+ Years'],
                'Count': [total_age_5_17, total_age_17_plus]
            })
            
            fig = px.pie(
                age_dist_data,
                values='Count',
                names='Age Group',
                title='Authentication Distribution by Age Group',
                color_discrete_sequence=['#09447d', '#f39c12'] # UIDAI Blue & Orange
            )
            fig.update_layout(
                height=400,
                template="plotly_white",
                title_font=dict(size=18, color='#09447d', family="Segoe UI"),
                font=dict(color="#333"),
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Time series if date is available
        if 'date' in df.columns and not df['date'].isna().all():
            st.subheader("📅 Authentication Trends Over Time")
            
            time_data = df.groupby('date').agg({
                age_5_17_col: 'sum' if age_5_17_col else lambda x: 0,
                age_17_plus_col: 'sum' if age_17_plus_col else lambda x: 0
            }).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=time_data['date'],
                y=time_data[age_5_17_col],
                name='Age 5-17',
                mode='lines+markers',
                line=dict(color='#09447d', width=3)
            ))
            fig.add_trace(go.Scatter(
                x=time_data['date'],
                y=time_data[age_17_plus_col],
                name='Age 17+',
                mode='lines+markers',
                line=dict(color='#f39c12', width=3)
            ))
            
            fig.update_layout(
                title='Daily Authentication Trends',
                xaxis_title='Date',
                yaxis_title='Number of Authentications',
                hovermode='x unified',
                height=400,
                template="plotly_white",
                title_font=dict(size=18, color='#09447d', family="Segoe UI"),
                font=dict(color="#333"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("🗺️ Geographic Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top districts
            if 'district' in df.columns:
                district_data = df.groupby('district').agg({
                    age_5_17_col: 'sum' if age_5_17_col else lambda x: 0,
                    age_17_plus_col: 'sum' if age_17_plus_col else lambda x: 0
                }).reset_index()
                district_data['total'] = district_data[age_5_17_col] + district_data[age_17_plus_col]
                district_data = district_data.nlargest(15, 'total')
                
                fig = px.bar(
                    district_data,
                    x='total',
                    y='district',
                    orientation='h',
                    title='Top 15 Districts by Authentications',
                    labels={'total': 'Total Authentications', 'district': 'District'},
                    color='total',
                    color_continuous_scale=['#e6f2ff', '#09447d']
                )
                fig.update_layout(
                    height=500,
                    template="plotly_white",
                    title_font=dict(size=18, color='#09447d', family="Segoe UI"),
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # State-wise breakdown
            if 'state' in df.columns:
                state_summary = df.groupby('state').agg({
                    age_5_17_col: 'sum' if age_5_17_col else lambda x: 0,
                    age_17_plus_col: 'sum' if age_17_plus_col else lambda x: 0,
                    'district': 'nunique'
                }).reset_index()
                state_summary['total'] = state_summary[age_5_17_col] + state_summary[age_17_plus_col]
                state_summary = state_summary.nlargest(15, 'total')
                
                fig = px.scatter(
                    state_summary,
                    x='district',
                    y='total',
                    size='total',
                    color='state',
                    title='States: Districts vs Total Authentications',
                    labels={'district': 'Number of Districts', 'total': 'Total Authentications'},
                    hover_data=['state']
                )
                fig.update_layout(
                    height=500, 
                    showlegend=False,
                    template="plotly_white",
                    title_font=dict(size=18, color='#09447d', family="Segoe UI"),
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("📊 Age Group Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # State-wise age distribution
            if 'state' in df.columns:
                state_age = df.groupby('state').agg({
                    age_5_17_col: 'sum' if age_5_17_col else lambda x: 0,
                    age_17_plus_col: 'sum' if age_17_plus_col else lambda x: 0
                }).reset_index()
                state_age = state_age.nlargest(10, age_5_17_col)
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Age 5-17',
                    x=state_age['state'],
                    y=state_age[age_5_17_col],
                    marker_color='#09447d'
                ))
                fig.add_trace(go.Bar(
                    name='Age 17+',
                    x=state_age['state'],
                    y=state_age[age_17_plus_col],
                    marker_color='#f39c12'
                ))
                
                fig.update_layout(
                    title='Top 10 States: Age Group Comparison',
                    xaxis_title='State',
                    yaxis_title='Number of Authentications',
                    barmode='group',
                    height=400,
                    template="plotly_white",
                    title_font=dict(size=18, color='#09447d', family="Segoe UI"),
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Age ratio by state
            if 'state' in df.columns:
                state_ratio = df.groupby('state').agg({
                    age_5_17_col: 'sum' if age_5_17_col else lambda x: 0,
                    age_17_plus_col: 'sum' if age_17_plus_col else lambda x: 0
                }).reset_index()
                state_ratio['total'] = state_ratio[age_5_17_col] + state_ratio[age_17_plus_col]
                state_ratio['ratio_5_17'] = (state_ratio[age_5_17_col] / state_ratio['total'] * 100).round(2)
                state_ratio = state_ratio.nlargest(10, 'total')
                
                fig = px.bar(
                    state_ratio,
                    x='state',
                    y='ratio_5_17',
                    title='Top 10 States: % of Age 5-17 Authentications',
                    labels={'ratio_5_17': 'Percentage (%)', 'state': 'State'},
                    color='ratio_5_17',
                    color_continuous_scale=['#ffedd5', '#f39c12'] # Orange Scale
                )
                fig.update_layout(
                    height=400,
                    template="plotly_white",
                    title_font=dict(size=18, color='#09447d', family="Segoe UI"),
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("📋 Raw Data")
        
        # Add summary statistics
        st.write("**Summary Statistics:**")
        summary_df = df.groupby('state').agg({
            age_5_17_col: 'sum' if age_5_17_col else lambda x: 0,
            age_17_plus_col: 'sum' if age_17_plus_col else lambda x: 0,
            'district': 'nunique',
            'pincode': 'nunique'
        }).reset_index()
        summary_df.columns = ['State', 'Age 5-17', 'Age 17+', 'Districts', 'Pincodes']
        summary_df['Total'] = summary_df['Age 5-17'] + summary_df['Age 17+']
        summary_df = summary_df.sort_values('Total', ascending=False)
        
        st.dataframe(summary_df, use_container_width=True, height=300)
        
        st.write("**Detailed Data:**")
        st.dataframe(df, use_container_width=True, height=400)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"uidai_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with tab5:
        st.subheader("🇮🇳 India Zone Map & Heatmaps")
        
        geojson = load_geojson()
        
        if geojson and 'state' in df.columns:
            # Prepare data for map
            map_data = df.groupby('state').agg({
                age_5_17_col: 'sum' if age_5_17_col else lambda x: 0,
                age_17_plus_col: 'sum' if age_17_plus_col else lambda x: 0
            }).reset_index()
            map_data['total'] = map_data[age_5_17_col] + map_data[age_17_plus_col]
            
            # Determine Zones
            # Quantiles for 33% and 66%
            low_threshold = map_data['total'].quantile(0.33)
            high_threshold = map_data['total'].quantile(0.66)
            
            def get_zone(val):
                if val <= low_threshold:
                    return 'Yellow' # Low activity -> Yellow (Caution/Low) or maybe Red? User asked for Red, Green, Yellow. Usually High is Green. 
                    # Let's assume High Volume = Green, Medium = Yellow, Low = Red? Or usually performance: Good = Green.
                    # If "performance" means "more authentications is better", then High = Green.
                    # if "performance" means "load", might be different. 
                    # I will assume More Authentications = Better/Active -> Green.
                    # Low Authentications -> Red.
                elif val <= high_threshold:
                    return 'Yellow'
                else:
                    return 'Green'

            # Let's refine the zones logic to match exactly "Red, Green and Yellow zones"
            # Low = Red, Medium = Yellow, High = Green
            def get_zone_color_val(val):
                if val <= low_threshold:
                    return 'Low Activity (Red)'
                elif val <= high_threshold:
                    return 'Medium Activity (Yellow)'
                else:
                    return 'High Activity (Green)'
            
            map_data['Zone'] = map_data['total'].apply(get_zone_color_val)
            
            # Map Zones to Colors explicitly
            color_discrete_map = {
                'Low Activity (Red)': 'red',
                'Medium Activity (Yellow)': 'yellow',
                'High Activity (Green)': 'green'
            }
            
            st.markdown("### 🗺️ State Performance Zones")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                fig_map = px.choropleth_mapbox(
                    map_data,
                    geojson=geojson,
                    featureidkey='properties.ST_NM',
                    locations='state',
                    color='Zone',
                    color_discrete_map=color_discrete_map,
                    hover_name='state',
                    hover_data=['total'],
                    center={"lat": 20.5937, "lon": 78.9629},
                    mapbox_style="carto-positron",
                    zoom=3,
                    opacity=0.7,
                    title="India State Zones (Red/Yellow/Green)"
                )
                fig_map.update_layout(height=600, margin={"r":0,"t":30,"l":0,"b":0})
                
                # Capture selection event
                map_event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", key="india_map")
            
            with col2:
                st.info("""
                **Zone Legend:**
                - 🟢 **Green**: High Volume (Top 33%)
                - 🟡 **Yellow**: Medium Volume (Middle 33%)
                - 🔴 **Red**: Low Volume (Bottom 33%)
                """)
                st.write("**Click on a state to view details!**")
                st.dataframe(map_data[['state', 'total', 'Zone']].sort_values('total', ascending=False), hide_index=True, height=500)

        # Handle Interaction
        selected_state = None
        if map_event and map_event.get("selection") and map_event["selection"].get("points"):
            # For choropleth, the location is usually in 'location' or 'x'/'y' depending on internal mapping, 
            # but for our config locations='state', it should be in point['location']
            selected_state = map_event["selection"]["points"][0].get("location")
        
        if selected_state:
            st.divider()
            st.markdown(f"## 📊 Deep Dive: {selected_state}")
            
            state_df = df[df['state'] == selected_state]
            
            # Metrics for State
            s_total = len(state_df)
            s_auth = state_df[age_5_17_col].sum() + state_df[age_17_plus_col].sum() if age_5_17_col and age_17_plus_col else 0
            s_districts = state_df['district'].nunique() if 'district' in state_df.columns else 0
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Records", f"{s_total:,}")
            m2.metric("Authentications", f"{s_auth:,}")
            m3.metric("Districts Covered", f"{s_districts}")
            
            # Detailed Charts
            dc1, dc2 = st.columns(2)
            
            with dc1:
                if 'district' in state_df.columns:
                    dist_data = state_df.groupby('district').size().reset_index(name='count').nlargest(10, 'count')
                    fig_dist = px.bar(dist_data, x='count', y='district', orientation='h', title=f"Top Districts in {selected_state}")
                    st.plotly_chart(fig_dist, use_container_width=True)
            
            with dc2:
                if age_5_17_col and age_17_plus_col:
                    age_data = pd.DataFrame({
                        'Age Group': ['5-17', '17+'],
                        'Count': [state_df[age_5_17_col].sum(), state_df[age_17_plus_col].sum()]
                    })
                    fig_age = px.pie(age_data, values='Count', names='Age Group', title=f"Age Distribution in {selected_state}")
                    st.plotly_chart(fig_age, use_container_width=True)

        st.markdown("---")
        st.subheader("🔥 Data Density Heatmaps")
        
        h_col1, h_col2 = st.columns(2)
        
        with h_col1:
            if 'state' in df.columns and 'district' in df.columns:
                # State vs District Density (Top 5 States)
                top_states = df.groupby('state').size().nlargest(5).index.tolist()
                heatmap_df = df[df['state'].isin(top_states)].groupby(['state', 'district']).size().reset_index(name='count')
                
                # To make it readable, maybe just filtered to top states
                fig_density = px.density_heatmap(
                    heatmap_df, 
                    x='state', 
                    y='district', 
                    z='count', 
                    title="Density Heatmap: Top 5 States vs Districts",
                    color_continuous_scale='Viridis'
                )
                fig_density.update_layout(height=500)
                st.plotly_chart(fig_density, use_container_width=True)
        
        with h_col2:
            if 'date' in df.columns and 'state' in df.columns:
                 # Date vs State Heatmap
                 date_state_df = df.groupby(['date', 'state']).size().reset_index(name='count')
                 fig_time_heat = px.density_heatmap(
                     date_state_df,
                     x='date',
                     y='state',
                     z='count',
                     title="Temporal Heatmap: Activity by State over Time",
                     color_continuous_scale='Magma'
                 )
                 fig_time_heat.update_layout(height=500)
                 st.plotly_chart(fig_time_heat, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='background-color: #09447d; color: white; padding: 20px; text-align: center; border-radius: 5px; margin-top: 30px;'>
            <p style='margin:0; font-size: 0.9rem;'>Unique Identification Authority of India | Government of India</p>
            <p style='margin:5px 0 0 0; font-size: 0.8rem; opacity: 0.8;'>For Official Use Only | Confidential Biometric Data</p>
            <p style='margin:5px 0 0 0; font-size: 0.8rem;'>© 2024 UIDAI. All Rights Reserved.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
