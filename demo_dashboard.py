import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, Any

# Page configuration
st.set_page_config(
    page_title="Tread Project Planning (Demo)",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
TOTAL_PROJECT_BUDGET = 500000  # Demo budget

@st.cache_data
def load_demo_data() -> pd.DataFrame:
    """
    Load demo data from CSV or create sample data.
    """
    try:
        # Try to load from sample_data.csv if it exists
        df = pd.read_csv('sample_data.csv')
    except FileNotFoundError:
        # Create sample data if file doesn't exist
        data = {
            'Project': [
                'Downtown Office Building', 'Downtown Office Building', 'Residential Complex A', 'Residential Complex A',
                'Residential Complex A', 'Residential Complex A', 'Shopping Center Renovation', 'Shopping Center Renovation',
                'Shopping Center Renovation', 'Warehouse Expansion', 'Warehouse Expansion', 'Modern Family Home',
                'Modern Family Home', 'Modern Family Home', 'City Park Pavilion'
            ],
            'Job Name': [
                'Foundation Work', 'Site Preparation', 'Framing', 'Roofing',
                'Electrical Installation', 'Plumbing', 'HVAC Installation',
                'Insulation', 'Drywall', 'Flooring', 'Interior Painting',
                'Kitchen Installation', 'Bathroom Installation', 
                'Final Inspections', 'Landscaping'
            ],
            'Start Date': [
                '2024-01-15', '2024-01-01', '2024-03-01', '2024-04-10',
                '2024-04-01', '2024-04-15', '2024-05-01', '2024-05-15',
                '2024-05-01', '2024-06-10', '2024-07-01', '2024-07-15',
                '2024-08-01', '2024-09-10', '2024-09-15'
            ],
            'End Date': [
                '2024-02-28', '2024-01-14', '2024-04-15', '2024-05-05',
                '2024-05-15', '2024-05-30', '2024-06-10', '2024-06-05',
                '2024-06-15', '2024-07-20', '2024-08-15', '2024-08-30',
                '2024-09-15', '2024-09-20', '2024-10-15'
            ],
            'Estimated Cost': [
                50000, 15000, 75000, 45000, 30000, 25000, 40000,
                18000, 35000, 28000, 22000, 55000, 35000, 5000, 20000
            ]
        }
        df = pd.DataFrame(data)
    
    # Clean and convert data types
    df['Start Date'] = pd.to_datetime(df['Start Date'])
    df['End Date'] = pd.to_datetime(df['End Date'])
    df['Estimated Cost'] = pd.to_numeric(df['Estimated Cost'])
    
    return df

def toggle_job_completion(job_key):
    """Toggle job completion status"""
    if job_key in st.session_state.completed_jobs:
        st.session_state.completed_jobs.discard(job_key)
    else:
        st.session_state.completed_jobs.add(job_key)

def create_project_budget_pie_chart(df: pd.DataFrame, selected_project: str, total_budget: float, completed_jobs=None) -> go.Figure:
    """Create a pie chart showing jobs as slices relative to project budget."""
    if completed_jobs is None:
        completed_jobs = set()
    
    # Filter jobs for the selected project
    project_jobs = df[df['Project'] == selected_project].copy()
    
    if project_jobs.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No jobs found for this project",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title=f"Project Budget Breakdown - {selected_project}")
        return fig
    
    # Calculate total job costs
    total_job_costs = project_jobs['Estimated Cost'].sum()
    remaining_budget = max(0, total_budget - total_job_costs)
    
    # Prepare data for pie chart
    labels = []
    values = []
    colors = []
    hover_texts = []
    
    # Color palette
    job_colors = px.colors.qualitative.Set3
    
    # Add each job as a slice
    for i, (_, job) in enumerate(project_jobs.iterrows()):
        job_key = f"{job['Job Name']}_{job['Start Date'].strftime('%Y%m%d')}"
        is_completed = job_key in completed_jobs
        
        # Use different colors for completed vs in-progress jobs
        if is_completed:
            color = '#90EE90'  # Light green for completed
        else:
            color = job_colors[i % len(job_colors)]
        
        labels.append(job['Job Name'])
        values.append(job['Estimated Cost'])
        colors.append(color)
        
        # Calculate percentage of budget
        percentage = (job['Estimated Cost'] / total_budget) * 100
        status = "✅ Complete" if is_completed else "🔄 In Progress"
        
        hover_text = (
            f"<b>{job['Job Name']}</b><br>"
            f"Status: {status}<br>"
            f"Cost: ${job['Estimated Cost']:,.0f}<br>"
            f"% of Budget: {percentage:.1f}%<br>"
            f"Start: {job['Start Date'].strftime('%Y-%m-%d')}<br>"
            f"End: {job['End Date'].strftime('%Y-%m-%d')}"
        )
        hover_texts.append(hover_text)
    
    # Add remaining budget as a slice (if any)
    if remaining_budget > 0:
        labels.append('Remaining Budget')
        values.append(remaining_budget)
        colors.append('#E8E8E8')  # Light gray for remaining budget
        remaining_percentage = (remaining_budget / total_budget) * 100
        hover_texts.append(
            f"<b>Remaining Budget</b><br>"
            f"Amount: ${remaining_budget:,.0f}<br>"
            f"% of Budget: {remaining_percentage:.1f}%"
        )
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_texts,
        textinfo='label+percent',
        textposition='auto'
    )])
    
    # Calculate budget utilization
    budget_used_percentage = (total_job_costs / total_budget) * 100
    
    fig.update_layout(
        title=f"Project Budget Breakdown - {selected_project}<br><sub>Budget Utilization: {budget_used_percentage:.1f}% (${total_job_costs:,.0f} of ${total_budget:,.0f})</sub>",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.01
        )
    )
    
    return fig

def create_budget_analysis(df: pd.DataFrame, selected_project: str, total_budget: float, completed_jobs=None) -> tuple:
    """Create budget analysis charts and calculate KPIs."""
    if completed_jobs is None:
        completed_jobs = set()
    
    # Get jobs for the selected project
    project_jobs = df[df['Project'] == selected_project].copy()
    
    # Calculate project spend
    project_spend = project_jobs['Estimated Cost'].sum()
    budget_used_pct = (project_spend / total_budget) * 100
    
    # Calculate job completion status
    total_jobs = len(project_jobs)
    jobs_complete = 0
    
    for _, job in project_jobs.iterrows():
        job_key = f"{job['Job Name']}_{job['Start Date'].strftime('%Y%m%d')}"
        if job_key in completed_jobs:
            jobs_complete += 1
    
    jobs_in_progress = total_jobs - jobs_complete
    
    # Create daily spend chart for the project
    if not project_jobs.empty:
        # Group by start date and sum costs
        daily_spend = project_jobs.groupby('Start Date')['Estimated Cost'].sum().reset_index()
        daily_spend['Cumulative Spend'] = daily_spend['Estimated Cost'].cumsum()
        
        # Create subplot with secondary y-axis using new syntax
        fig = make_subplots(
            rows=1, cols=1,
            specs=[[{"secondary_y": True}]],
            subplot_titles=[f"Daily Job Starts & Spend - {selected_project}"]
        )
        
        # Daily spend bars
        fig.add_trace(
            go.Bar(
                x=daily_spend['Start Date'],
                y=daily_spend['Estimated Cost'],
                name='Daily Spend',
                marker_color='lightblue',
                hovertemplate="Date: %{x}<br>Daily Spend: $%{y:,.0f}<extra></extra>"
            ),
            secondary_y=False
        )
        
        # Cumulative spend line
        fig.add_trace(
            go.Scatter(
                x=daily_spend['Start Date'],
                y=daily_spend['Cumulative Spend'],
                mode='lines+markers',
                name='Cumulative Spend',
                line=dict(color='red', width=3),
                hovertemplate="Date: %{x}<br>Cumulative: $%{y:,.0f}<extra></extra>"
            ),
            secondary_y=True
        )
        
        # Update axes
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Daily Spend ($)", secondary_y=False)
        fig.update_yaxes(title_text="Cumulative Spend ($)", secondary_y=True)
        
        fig.update_layout(height=400)
    else:
        fig = go.Figure()
        fig.add_annotation(
            text="No jobs found for this project",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title=f"Project Budget Analysis - {selected_project}")
    
    # Calculate KPIs
    kpis = {
        'total_spend_to_date': project_spend,
        'budget_used_pct': budget_used_pct,
        'remaining_budget': total_budget - project_spend,
        'jobs_in_progress': jobs_in_progress,
        'jobs_complete': jobs_complete
    }
    
    return fig, kpis

def display_kpi_cards(kpis: Dict[str, Any], total_budget: float):
    """Display KPI cards in a grid layout."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Determine color based on budget percentage
        budget_pct = kpis['budget_used_pct']
        if budget_pct >= 90:
            color = "red"
        elif budget_pct >= 70:
            color = "orange"
        else:
            color = "green"
        
        st.metric(
            label="Total Spend to Date",
            value=f"${kpis['total_spend_to_date']:,.0f}"
        )
        st.markdown(f"<p style='color: {color}; font-size: 14px; margin-top: -10px;'>{budget_pct:.1f}% of budget</p>", unsafe_allow_html=True)
    
    with col2:
        # Use inverse color logic for remaining budget
        remaining_pct = 100 - kpis['budget_used_pct']
        if remaining_pct <= 10:  # Less than 10% remaining = danger
            remaining_color = "red"
        elif remaining_pct <= 30:  # 10-30% remaining = caution
            remaining_color = "orange"
        else:  # More than 30% remaining = safe
            remaining_color = "green"
        
        st.metric(
            label="Remaining Budget",
            value=f"${kpis['remaining_budget']:,.0f}"
        )
        st.markdown(f"<p style='color: {remaining_color}; font-size: 14px; margin-top: -10px;'>{remaining_pct:.1f}% remaining</p>", unsafe_allow_html=True)
    
    with col3:
        st.metric(
            label="Jobs in Progress",
            value=kpis['jobs_in_progress']
        )
    
    with col4:
        st.metric(
            label="Jobs Complete",
            value=kpis['jobs_complete']
        )

def main():
    """Main Streamlit application."""
    # Custom CSS for black background, white text, and champagne gold title
    st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    
    .main .block-container {
        background-color: #000000;
        color: #FFFFFF;
    }
    
    /* Style all text elements */
    .stMarkdown, .stText, p, div, span, h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
    
    /* Specific styling for the main title to ensure champagne gold shows */
    .stMarkdown h1 {
        color: #D4AF37 !important;
    }
    
    /* Override any conflicting title styles */
    h1[style*="color: #D4AF37"] {
        color: #D4AF37 !important;
    }
    
    /* Style sidebar */
    .css-1d391kg, .css-1lcbmhc, .css-1oe5cao {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
    }
    
    /* Style sidebar text */
    .css-1d391kg .stMarkdown, .css-1lcbmhc .stMarkdown {
        color: #FFFFFF !important;
    }
    
    /* Style metrics and KPI cards */
    .css-1r6slb0, .css-12oz5g7, [data-testid="metric-container"] {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
    }
    
    /* Style metric values and labels */
    [data-testid="metric-container"] > div {
        color: #FFFFFF !important;
    }
    
    /* Style tables */
    .stDataFrame, table {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
    }
    
    /* Style input fields */
    .stSelectbox > div > div, .stNumberInput > div > div > input, .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }
    
    /* Style buttons */
    .stButton > button {
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border: 1px solid #555555 !important;
    }
    
    .stButton > button:hover {
        background-color: #555555 !important;
        border: 1px solid #777777 !important;
    }
    
    /* Style checkboxes */
    .stCheckbox {
        color: #FFFFFF !important;
    }
    
    /* Style expander */
    .streamlit-expanderHeader {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
    }
    
    /* Style info/warning boxes */
    .stAlert {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Custom header with logo using Streamlit columns
    col1, col2 = st.columns([1, 10])
    
    with col1:
        try:
            st.image("tread_logo.png", width=50)
        except:
            # No fallback emoji - just empty space if logo not found
            pass
    
    with col2:
        st.markdown("""
        <h1 style="margin: 0 !important; color: #D4AF37 !important; font-size: 36px !important; font-weight: bold !important; padding-top: 10px !important;">
            🏗️ Tread Project Planning (Demo)
        </h1>
        """, unsafe_allow_html=True)
    
    st.info("🚀 This is a demo version using sample data. For the full version with Google Sheets integration, use `construction_dashboard.py`")
    st.markdown("---")
    
    # Project selection
    st.sidebar.header("View Selection")
    
    # Initialize session state variables FIRST
    if 'custom_projects' not in st.session_state:
        st.session_state.custom_projects = []
    
    if 'custom_jobs' not in st.session_state:
        st.session_state.custom_jobs = []
    
    # Load demo data after initialization
    with st.spinner("Loading demo data..."):
        df = load_demo_data()
        
        # Add custom jobs to the dataframe
        if st.session_state.custom_jobs:
            custom_df = pd.DataFrame(st.session_state.custom_jobs)
            df = pd.concat([df, custom_df], ignore_index=True)
    
    # Get available projects (including custom ones)
    base_projects = df['Project'].unique().tolist()
    available_projects = sorted(base_projects + st.session_state.custom_projects)
    
    # Project selection dropdown
    selected_project = st.sidebar.selectbox(
        "Project",
        options=available_projects,
        index=0 if available_projects else None
    )
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # Initialize project budgets in session state if not exists
    if 'project_budgets' not in st.session_state:
        st.session_state.project_budgets = {}
    
    # Budget configuration
    budget_input = st.sidebar.number_input(
        "Total Project Budget ($)",
        min_value=0,
        value=TOTAL_PROJECT_BUDGET,
        step=10000,
        format="%d"
    )
    
    # Set budget button
    if st.sidebar.button("Set", key="set_budget_btn"):
        if selected_project:
            st.session_state.project_budgets[selected_project] = budget_input
            st.sidebar.success(f"Budget set for {selected_project}")
        else:
            st.sidebar.error("Please select a project first")
    
    # Get current project budget
    budget = st.session_state.project_budgets.get(selected_project, TOTAL_PROJECT_BUDGET)
    
    # Add new project functionality
    st.sidebar.subheader("Add New Project")
    with st.sidebar.form("add_project_form"):
        new_project_name = st.text_input("Project Name")
        add_project = st.form_submit_button("Add Project")
        
        if add_project and new_project_name.strip():
            new_project_name = new_project_name.strip()
            if new_project_name not in available_projects:
                st.session_state.custom_projects.append(new_project_name)
                st.success(f"Project '{new_project_name}' added!")
                st.rerun()
            else:
                st.error("Project already exists!")
    
    if not selected_project:
        st.warning("No projects available. Please add a project to get started.")
        return
    
    # Initialize session state for job completion tracking
    if 'completed_jobs' not in st.session_state:
        st.session_state.completed_jobs = set()
    
    # Main content
    st.header(f"Dashboard for {selected_project}")
    
    # Filter by selected project
    display_df = df[df['Project'] == selected_project].copy()
    
    # Job Status Overview - Process checkboxes FIRST so state is updated before KPIs
    st.subheader("📊 Job Status Overview")
    
    # Add new job functionality
    with st.expander("➕ Add New Job", expanded=False):
        with st.form("add_job_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_job_name = st.text_input("Job Name", placeholder="e.g., Foundation Work")
                new_start_date = st.date_input("Start Date")
            with col2:
                new_estimated_cost = st.number_input("Estimated Cost ($)", min_value=0, step=1000, format="%d")
                new_end_date = st.date_input("End Date")
            
            add_job = st.form_submit_button("Add Job")
            
            if add_job:
                if new_job_name.strip() and new_start_date and new_end_date and new_estimated_cost > 0:
                    if new_end_date >= new_start_date:
                        new_job = {
                            'Project': selected_project,
                            'Job Name': new_job_name.strip(),
                            'Start Date': pd.Timestamp(new_start_date),
                            'End Date': pd.Timestamp(new_end_date),
                            'Estimated Cost': new_estimated_cost
                        }
                        st.session_state.custom_jobs.append(new_job)
                        st.success(f"Job '{new_job_name.strip()}' added to {selected_project}!")
                        st.rerun()
                    else:
                        st.error("End date must be on or after start date!")
                else:
                    st.error("Please fill in all fields with valid values!")
    
    if not display_df.empty:
        # Create interactive table with checkboxes
        st.write("**Job Status Overview:**")
        
        # Add column headers
        col1, col2, col3, col4, col5 = st.columns([0.8, 2, 1.2, 1.2, 1.2])
        with col1:
            st.markdown("**Complete**")
        with col2:
            st.markdown("**Job Name**")
        with col3:
            st.markdown("**Start Date**")
        with col4:
            st.markdown("**End Date**")
        with col5:
            st.markdown("**Estimated Cost**")
        
        st.markdown("---")
        
        for idx, row in display_df.iterrows():
            job_key = f"{row['Job Name']}_{row['Start Date'].strftime('%Y%m%d')}"
            
            # Create columns for the job row
            col1, col2, col3, col4, col5 = st.columns([0.8, 2, 1.2, 1.2, 1.2])
            
            with col1:
                checkbox_key = f"complete_{job_key}"
                
                # Initialize checkbox state if not exists
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = job_key in st.session_state.completed_jobs
                
                # Checkbox for completion status
                is_complete = st.checkbox(
                    label=f"Complete {row['Job Name']}",
                    key=checkbox_key,
                    label_visibility="collapsed"
                )
                
                # Update completed jobs set based on checkbox state
                if is_complete:
                    st.session_state.completed_jobs.add(job_key)
                else:
                    st.session_state.completed_jobs.discard(job_key)
            
            # Row styling based on completion
            if is_complete:
                row_style = "background-color: #d4edda; padding: 8px; border-radius: 4px; margin: 2px 0;"
            else:
                row_style = "padding: 8px; margin: 2px 0;"
            
            with col2:
                st.markdown(f"<div style='{row_style}'><strong>{row['Job Name']}</strong></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div style='{row_style}'>{row['Start Date'].strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<div style='{row_style}'>{row['End Date'].strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
            with col5:
                st.markdown(f"<div style='{row_style}'>${row['Estimated Cost']:,.0f}</div>", unsafe_allow_html=True)
        
        # Summary statistics
        total_cost = display_df['Estimated Cost'].sum()
        total_jobs = len(display_df)
        
        st.caption(f"**Total:** {total_jobs} jobs | **Total Cost:** ${total_cost:,.0f}")
    else:
        st.info("No jobs found for the selected project.")
    
    st.markdown("---")
    
    # Now calculate and display KPI cards with updated state
    _, kpis = create_budget_analysis(df, selected_project, budget, st.session_state.completed_jobs)
    display_kpi_cards(kpis, budget)
    
    st.markdown("---")
    
    # Project Budget Pie Chart
    st.subheader("📊 Project Budget Breakdown")
    pie_fig = create_project_budget_pie_chart(df, selected_project, budget, st.session_state.completed_jobs)
    st.plotly_chart(pie_fig, use_container_width=True)
    
    # Instructions for full version
    st.markdown("---")
    with st.expander("💡 About This Demo"):
        st.markdown("""
        This demo uses sample construction data to showcase the dashboard features.
        
        **Key Features Demonstrated:**
        - Interactive Gantt chart with monthly navigation
        - Budget analysis with daily spend tracking
        - KPI cards showing project metrics
        - Data filtering and summary statistics
        
        **To use with your own Google Sheets data:**
        1. Install dependencies: `pip install -r requirements.txt`
        2. Set up Google Sheets API credentials (see README.md)
        3. Run: `streamlit run construction_dashboard.py`
        
        **Sample Data Format:**
        The demo uses data with columns: Job Name, Start Date, End Date, Estimated Cost, Estimated Duration
        """)

if __name__ == "__main__":
    main() 