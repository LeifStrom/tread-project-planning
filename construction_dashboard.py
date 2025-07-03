import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
import datetime
from dateutil.relativedelta import relativedelta
import json
import os
from typing import Optional, Dict, Any, List
import time

# Page configuration
st.set_page_config(
    page_title="Construction Jobs Dashboard",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
TOTAL_PROJECT_BUDGET = 1000000  # Default budget - can be overridden from sheet
SHEET_NAME = "ConstructionJobs"
REQUIRED_COLUMNS = ['Job Name', 'Start Date', 'End Date', 'Estimated Cost', 'Estimated Duration', 'Status']

# Updated scope to include write permissions
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def load_google_credentials() -> Optional[Credentials]:
    """
    Load Google credentials from various sources.
    Priority: 1) GOOGLE_APPLICATION_CREDENTIALS env var, 2) Streamlit secrets, 3) credentials.json file
    """
    try:
        # Try GOOGLE_APPLICATION_CREDENTIALS environment variable first
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            credentials_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
            if os.path.exists(credentials_path):
                return Credentials.from_service_account_file(credentials_path, scopes=SCOPE)
        
        # Try Streamlit secrets (for cloud deployment)
        if "google_credentials" in st.secrets:
            credentials_dict = dict(st.secrets["google_credentials"])
            return Credentials.from_service_account_info(credentials_dict, scopes=SCOPE)
        
        # Try credentials.json file in current directory
        if os.path.exists("credentials.json"):
            return Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
        
        # Try GOOGLE_CREDENTIALS environment variable (JSON string)
        if "GOOGLE_CREDENTIALS" in os.environ:
            credentials_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
            return Credentials.from_service_account_info(credentials_dict, scopes=SCOPE)
        
        return None
    except Exception as e:
        st.error(f"Error loading Google credentials: {str(e)}")
        return None

def get_sheet_connection(sheet_url: str):
    """Get authenticated connection to Google Sheet."""
    credentials = load_google_credentials()
    if not credentials:
        raise Exception("Google credentials not found")
    
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(sheet_url)
    
    # Try to get the ConstructionJobs worksheet, create if it doesn't exist
    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
    except gspread.WorksheetNotFound:
        # Create the worksheet with headers
        worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=10)
        worksheet.append_row(REQUIRED_COLUMNS)
        st.success(f"Created new worksheet '{SHEET_NAME}' with proper headers!")
    
    return spreadsheet, worksheet

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_sheet(sheet_url: str, force_refresh: bool = False) -> Optional[pd.DataFrame]:
    """
    Load job data from Google Sheets with caching.
    Expected columns: Job Name, Start Date, End Date, Estimated Cost, Estimated Duration, Status
    """
    if force_refresh:
        st.cache_data.clear()
    
    try:
        _, worksheet = get_sheet_connection(sheet_url)
        
        # Get all data
        data = worksheet.get_all_records()
        
        if not data:
            st.warning("No data found in the sheet.")
            return pd.DataFrame(columns=REQUIRED_COLUMNS)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Validate required columns
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")
            st.info(f"Expected columns: {', '.join(REQUIRED_COLUMNS)}")
            return None
        
        # Clean and convert data types
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')
        df['Estimated Cost'] = pd.to_numeric(df['Estimated Cost'], errors='coerce')
        df['Estimated Duration'] = pd.to_numeric(df['Estimated Duration'], errors='coerce')
        
        # Fill empty Status fields with 'Planned'
        df['Status'] = df['Status'].fillna('Planned')
        df['Status'] = df['Status'].replace('', 'Planned')
        
        # Remove rows with invalid dates or costs
        df = df.dropna(subset=['Start Date', 'End Date', 'Estimated Cost'])
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data from sheet: {str(e)}")
        return None

def add_job_to_sheet(sheet_url: str, job_data: Dict[str, Any]) -> bool:
    """Add a new job to the Google Sheet."""
    try:
        _, worksheet = get_sheet_connection(sheet_url)
        
        # Prepare row data in the correct order
        row_data = [
            job_data['Job Name'],
            job_data['Start Date'].strftime('%Y-%m-%d'),
            job_data['End Date'].strftime('%Y-%m-%d'),
            job_data['Estimated Cost'],
            job_data['Estimated Duration'],
            job_data['Status']
        ]
        
        # Append the row
        worksheet.append_row(row_data)
        return True
        
    except Exception as e:
        st.error(f"Error adding job to sheet: {str(e)}")
        return False

def update_job_in_sheet(sheet_url: str, row_index: int, job_data: Dict[str, Any]) -> bool:
    """Update an existing job in the Google Sheet."""
    try:
        _, worksheet = get_sheet_connection(sheet_url)
        
        # Prepare row data in the correct order (row_index is 1-based, add 1 for header)
        actual_row = row_index + 2
        
        worksheet.update_cell(actual_row, 1, job_data['Job Name'])
        worksheet.update_cell(actual_row, 2, job_data['Start Date'].strftime('%Y-%m-%d'))
        worksheet.update_cell(actual_row, 3, job_data['End Date'].strftime('%Y-%m-%d'))
        worksheet.update_cell(actual_row, 4, job_data['Estimated Cost'])
        worksheet.update_cell(actual_row, 5, job_data['Estimated Duration'])
        worksheet.update_cell(actual_row, 6, job_data['Status'])
        
        return True
        
    except Exception as e:
        st.error(f"Error updating job in sheet: {str(e)}")
        return False

def delete_job_from_sheet(sheet_url: str, row_index: int) -> bool:
    """Delete a job from the Google Sheet."""
    try:
        _, worksheet = get_sheet_connection(sheet_url)
        
        # Delete row (row_index is 0-based, add 2 for header and 1-based indexing)
        actual_row = row_index + 2
        worksheet.delete_rows(actual_row)
        
        return True
        
    except Exception as e:
        st.error(f"Error deleting job from sheet: {str(e)}")
        return False

def create_gantt_chart(df: pd.DataFrame, selected_month: datetime.date) -> go.Figure:
    """
    Create a Gantt chart for jobs in the selected month.
    """
    # Filter jobs that overlap with the selected month
    month_start = selected_month.replace(day=1)
    month_end = (month_start + relativedelta(months=1)) - datetime.timedelta(days=1)
    
    # Filter jobs that overlap with the selected month
    mask = (df['Start Date'] <= pd.Timestamp(month_end)) & (df['End Date'] >= pd.Timestamp(month_start))
    month_jobs = df[mask].copy()
    
    if month_jobs.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No jobs scheduled for this month",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title="Job Schedule - Gantt Chart")
        return fig
    
    # Create Gantt chart
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    status_colors = {
        'Planned': '#FFA500',      # Orange
        'In Progress': '#1E90FF',  # Blue
        'Completed': '#32CD32',    # Green
        'On Hold': '#FF6347',      # Red
        'Cancelled': '#808080'     # Gray
    }
    
    for i, (_, job) in enumerate(month_jobs.iterrows()):
        # Use status-based color if available, otherwise use default color scheme
        color = status_colors.get(job['Status'], colors[i % len(colors)])
        
        # Clip dates to month boundaries for display
        display_start = max(job['Start Date'], pd.Timestamp(month_start))
        display_end = min(job['End Date'], pd.Timestamp(month_end))
        
        fig.add_trace(go.Bar(
            x=[display_end - display_start],
            y=[job['Job Name']],
            base=display_start,
            orientation='h',
            marker_color=color,
            hovertemplate=(
                f"<b>{job['Job Name']}</b><br>"
                f"Status: {job['Status']}<br>"
                f"Start: {job['Start Date'].strftime('%Y-%m-%d')}<br>"
                f"End: {job['End Date'].strftime('%Y-%m-%d')}<br>"
                f"Cost: ${job['Estimated Cost']:,.0f}<br>"
                f"Duration: {job['Estimated Duration']} days<br>"
                "<extra></extra>"
            ),
            name=job['Job Name']
        ))
    
    fig.update_layout(
        title=f"Job Schedule - {selected_month.strftime('%B %Y')}",
        xaxis_title="Timeline",
        yaxis_title="Jobs",
        showlegend=False,
        height=max(400, len(month_jobs) * 40 + 100),
        xaxis=dict(
            range=[pd.Timestamp(month_start), pd.Timestamp(month_end)],
            type='date'
        )
    )
    
    return fig

def create_budget_analysis(df: pd.DataFrame, selected_month: datetime.date, total_budget: float) -> tuple:
    """
    Create budget analysis charts and calculate KPIs.
    Returns: (daily_spend_fig, kpi_dict)
    """
    month_start = selected_month.replace(day=1)
    month_end = (month_start + relativedelta(months=1)) - datetime.timedelta(days=1)
    
    # Get jobs starting in the selected month
    month_jobs = df[
        (df['Start Date'] >= pd.Timestamp(month_start)) & 
        (df['Start Date'] <= pd.Timestamp(month_end))
    ].copy()
    
    # Calculate cumulative spend through the selected month
    cumulative_jobs = df[df['Start Date'] <= pd.Timestamp(month_end)].copy()
    total_spend_to_date = cumulative_jobs['Estimated Cost'].sum()
    budget_used_pct = (total_spend_to_date / total_budget) * 100
    
    # Create daily spend chart for the month
    if not month_jobs.empty:
        # Group by start date and sum costs
        daily_spend = month_jobs.groupby('Start Date')['Estimated Cost'].sum().reset_index()
        daily_spend['Cumulative Spend'] = daily_spend['Estimated Cost'].cumsum()
        
        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=1, cols=1,
            specs=[[{"secondary_y": True}]],
            subplot_titles=[f"Daily Job Starts & Spend - {selected_month.strftime('%B %Y')}"]
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
            text="No jobs starting this month",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title=f"Daily Job Starts & Spend - {selected_month.strftime('%B %Y')}")
    
    # Calculate KPIs
    kpis = {
        'total_spend_to_date': total_spend_to_date,
        'budget_used_pct': budget_used_pct,
        'remaining_budget': total_budget - total_spend_to_date,
        'jobs_this_month': len(month_jobs),
        'spend_this_month': month_jobs['Estimated Cost'].sum()
    }
    
    return fig, kpis

def display_kpi_cards(kpis: Dict[str, Any], total_budget: float):
    """
    Display KPI cards in a grid layout.
    """
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
            label="Jobs This Month",
            value=kpis['jobs_this_month']
        )
    
    with col4:
        st.metric(
            label="Spend This Month",
            value=f"${kpis['spend_this_month']:,.0f}"
        )

def validate_job_data(job_name: str, start_date: datetime.date, end_date: datetime.date, cost: float, duration: int) -> List[str]:
    """Validate job data and return list of errors."""
    errors = []
    
    if not job_name.strip():
        errors.append("Job name is required")
    
    if start_date >= end_date:
        errors.append("End date must be after start date")
    
    if cost < 0:
        errors.append("Estimated cost must be non-negative")
    
    if duration <= 0:
        errors.append("Estimated duration must be positive")
    
    return errors

def display_add_job_form(sheet_url: str):
    """Display the add job form."""
    st.subheader("➕ Add New Job")
    
    with st.form("add_job_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            job_name = st.text_input("Job Name*", placeholder="e.g., Foundation Work")
            start_date = st.date_input("Start Date*", value=datetime.date.today())
            estimated_cost = st.number_input("Estimated Cost ($)*", min_value=0.0, step=1000.0, format="%.2f")
        
        with col2:
            status_options = ['Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled']
            status = st.selectbox("Status*", options=status_options, index=0)
            end_date = st.date_input("End Date*", value=datetime.date.today() + datetime.timedelta(days=30))
            estimated_duration = st.number_input("Estimated Duration (days)*", min_value=1, step=1, value=30)
        
        submitted = st.form_submit_button("Add Job", type="primary")
        
        if submitted:
            # Validate data
            errors = validate_job_data(job_name, start_date, end_date, estimated_cost, estimated_duration)
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Prepare job data
                job_data = {
                    'Job Name': job_name.strip(),
                    'Start Date': start_date,
                    'End Date': end_date,
                    'Estimated Cost': estimated_cost,
                    'Estimated Duration': estimated_duration,
                    'Status': status
                }
                
                # Add to sheet
                with st.spinner("Adding job to sheet..."):
                    success = add_job_to_sheet(sheet_url, job_data)
                
                if success:
                    st.success(f"✅ Job '{job_name}' added successfully!")
                    st.cache_data.clear()  # Clear cache to show updated data
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Failed to add job. Please try again.")

def display_job_management(df: pd.DataFrame, sheet_url: str):
    """Display job management interface with edit/delete options."""
    st.subheader("📋 Job Management")
    
    if df.empty:
        st.info("No jobs found. Add some jobs to get started!")
        return
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search jobs", placeholder="Search by job name...")
    with col2:
        status_filter = st.selectbox("Filter by Status", 
                                   options=['All'] + ['Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled'],
                                   index=0)
    
    # Apply filters
    filtered_df = df.copy()
    if search_term:
        filtered_df = filtered_df[filtered_df['Job Name'].str.contains(search_term, case=False, na=False)]
    if status_filter != 'All':
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]
    
    if filtered_df.empty:
        st.info("No jobs match the current filters.")
        return
    
    # Display jobs with edit/delete options
    for idx, job in filtered_df.iterrows():
        with st.expander(f"📝 {job['Job Name']} - {job['Status']}", expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write("**Job Details:**")
                st.write(f"• Start: {job['Start Date'].strftime('%Y-%m-%d')}")
                st.write(f"• End: {job['End Date'].strftime('%Y-%m-%d')}")
                st.write(f"• Cost: ${job['Estimated Cost']:,.2f}")
                st.write(f"• Duration: {job['Estimated Duration']} days")
                st.write(f"• Status: {job['Status']}")
            
            with col2:
                if st.button("✏️ Edit", key=f"edit_{idx}"):
                    st.session_state[f"editing_{idx}"] = True
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{idx}", type="secondary"):
                    st.session_state[f"confirm_delete_{idx}"] = True
            
            # Edit form
            if st.session_state.get(f"editing_{idx}", False):
                st.markdown("---")
                st.write("**Edit Job:**")
                
                with st.form(f"edit_form_{idx}"):
                    edit_col1, edit_col2 = st.columns(2)
                    
                    with edit_col1:
                        new_job_name = st.text_input("Job Name", value=job['Job Name'], key=f"edit_name_{idx}")
                        new_start_date = st.date_input("Start Date", value=job['Start Date'].date(), key=f"edit_start_{idx}")
                        new_cost = st.number_input("Estimated Cost ($)", value=float(job['Estimated Cost']), 
                                                 min_value=0.0, step=1000.0, key=f"edit_cost_{idx}")
                    
                    with edit_col2:
                        new_status = st.selectbox("Status", 
                                                options=['Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled'],
                                                index=['Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled'].index(job['Status']),
                                                key=f"edit_status_{idx}")
                        new_end_date = st.date_input("End Date", value=job['End Date'].date(), key=f"edit_end_{idx}")
                        new_duration = st.number_input("Duration (days)", value=int(job['Estimated Duration']), 
                                                     min_value=1, step=1, key=f"edit_duration_{idx}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_submitted = st.form_submit_button("💾 Update Job", type="primary")
                    with col2:
                        cancel_edit = st.form_submit_button("❌ Cancel")
                    
                    if update_submitted:
                        # Validate data
                        errors = validate_job_data(new_job_name, new_start_date, new_end_date, new_cost, new_duration)
                        
                        if errors:
                            for error in errors:
                                st.error(error)
                        else:
                            # Prepare updated job data
                            updated_job_data = {
                                'Job Name': new_job_name.strip(),
                                'Start Date': new_start_date,
                                'End Date': new_end_date,
                                'Estimated Cost': new_cost,
                                'Estimated Duration': new_duration,
                                'Status': new_status
                            }
                            
                            # Find the original row index in the full dataframe
                            original_idx = df.index[df['Job Name'] == job['Job Name']].tolist()[0]
                            
                            # Update in sheet
                            with st.spinner("Updating job..."):
                                success = update_job_in_sheet(sheet_url, original_idx, updated_job_data)
                            
                            if success:
                                st.success("✅ Job updated successfully!")
                                st.session_state[f"editing_{idx}"] = False
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Failed to update job. Please try again.")
                    
                    if cancel_edit:
                        st.session_state[f"editing_{idx}"] = False
                        st.rerun()
            
            # Delete confirmation
            if st.session_state.get(f"confirm_delete_{idx}", False):
                st.markdown("---")
                st.warning(f"⚠️ Are you sure you want to delete '{job['Job Name']}'? This action cannot be undone.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Yes, Delete", key=f"confirm_yes_{idx}", type="primary"):
                        # Find the original row index in the full dataframe
                        original_idx = df.index[df['Job Name'] == job['Job Name']].tolist()[0]
                        
                        # Delete from sheet
                        with st.spinner("Deleting job..."):
                            success = delete_job_from_sheet(sheet_url, original_idx)
                        
                        if success:
                            st.success("✅ Job deleted successfully!")
                            st.session_state[f"confirm_delete_{idx}"] = False
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete job. Please try again.")
                
                with col2:
                    if st.button("❌ Cancel", key=f"confirm_no_{idx}"):
                        st.session_state[f"confirm_delete_{idx}"] = False
                        st.rerun()

def main():
    """
    Main Streamlit application.
    """
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
            🏗️ Tread Project Planning
        </h1>
        """, unsafe_allow_html=True)
    
    st.info("📊 Real-time Google Sheets Integration for Construction Job Management")
    st.markdown("---")
    
    # Sidebar configuration
    st.sidebar.header("📊 Configuration")
    
    # Google Sheet URL input
    sheet_url = st.sidebar.text_input(
        "Google Sheet URL*",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        help="Paste the full URL of your Google Sheet containing job data"
    )
    
    # Budget configuration
    budget = st.sidebar.number_input(
        "Total Project Budget ($)",
        min_value=0,
        value=TOTAL_PROJECT_BUDGET,
        step=10000,
        format="%d"
    )
    
    # Data refresh button
    st.sidebar.markdown("---")
    st.sidebar.header("🔄 Data Management")
    
    if st.sidebar.button("🔄 Refresh from Sheets", type="primary"):
        if sheet_url:
            with st.spinner("Refreshing data..."):
                st.cache_data.clear()
                df = load_data_from_sheet(sheet_url, force_refresh=True)
            st.sidebar.success("✅ Data refreshed!")
        else:
            st.sidebar.error("Please enter a Google Sheet URL first")
    
    # Date selection
    st.sidebar.header("📅 View Selection")
    
    # Year and month selection
    current_date = datetime.date.today()
    selected_year = st.sidebar.selectbox(
        "Year",
        options=list(range(current_date.year - 2, current_date.year + 3)),
        index=2  # Current year
    )
    
    selected_month = st.sidebar.selectbox(
        "Month",
        options=list(range(1, 13)),
        index=current_date.month - 1,
        format_func=lambda x: datetime.date(2000, x, 1).strftime('%B')
    )
    
    selected_date = datetime.date(selected_year, selected_month, 1)
    
    # Check if Google Sheet URL is provided
    if not sheet_url:
        st.info("👈 Please enter your Google Sheet URL in the sidebar to get started.")
        
        # Show setup instructions
        with st.expander("📋 Setup Instructions", expanded=True):
            st.markdown("""
            ### 🔧 Google Sheets Setup
            
            1. **Create a Google Sheet** with the following columns (exact names required):
               - `Job Name` (text)
               - `Start Date` (date, format: YYYY-MM-DD)
               - `End Date` (date, format: YYYY-MM-DD)
               - `Estimated Cost` (number)
               - `Estimated Duration` (number, in days)
               - `Status` (text: Planned, In Progress, Completed, On Hold, or Cancelled)
            
            2. **Set up Google Cloud Project:**
               ```bash
               # Create a new project or select existing one at:
               # https://console.cloud.google.com/
               
               # Enable required APIs:
               # - Google Sheets API
               # - Google Drive API
               ```
            
            3. **Create Service Account:**
               ```bash
               # Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
               # 1. Click "Create Service Account"
               # 2. Give it a name (e.g., "sheets-dashboard")
               # 3. Click "Create and Continue"
               # 4. Skip role assignment (click "Continue")
               # 5. Click "Done"
               
               # Create and download key:
               # 1. Click on the created service account
               # 2. Go to "Keys" tab
               # 3. Click "Add Key" → "Create new key" → "JSON"
               # 4. Download the JSON file
               ```
            
            4. **Setup Credentials (choose one method):**
               
               **Method 1 - Environment Variable (Recommended):**
               ```bash
               export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
               ```
               
               **Method 2 - Local File:**
               ```bash
               # Place the downloaded JSON file as "credentials.json" in the same folder as this app
               ```
               
               **Method 3 - Environment JSON String:**
               ```bash
               export GOOGLE_CREDENTIALS='{"type": "service_account", "project_id": "..."}'
               ```
            
            5. **Share Google Sheet:**
               ```bash
               # 1. Open your Google Sheet
               # 2. Click "Share" button
               # 3. Add the service account email (found in credentials.json)
               # 4. Give it "Editor" permissions
               # 5. Click "Send"
               ```
            
            6. **Run the Dashboard:**
               ```bash
               streamlit run construction_dashboard.py
               ```
            
            ### 📊 Sample Data Format
            | Job Name | Start Date | End Date | Estimated Cost | Estimated Duration | Status |
            |----------|------------|----------|----------------|-------------------|---------|
            | Foundation Work | 2024-01-15 | 2024-02-28 | 50000 | 44 | In Progress |
            | Framing | 2024-03-01 | 2024-04-15 | 75000 | 45 | Planned |
            | Electrical Installation | 2024-04-01 | 2024-05-15 | 30000 | 44 | Planned |
            
            ### 🚀 Features Available:
            - ✅ **Real-time data sync** with Google Sheets
            - ✅ **Add new jobs** directly from the dashboard
            - ✅ **Edit existing jobs** with in-place editing
            - ✅ **Delete jobs** with confirmation
            - ✅ **Interactive Gantt charts** with status-based colors
            - ✅ **Budget analysis** and KPI tracking
            - ✅ **Search and filter** jobs by name and status
            - ✅ **Monthly/yearly** views for project planning
            """)
        return
    
    # Load data
    with st.spinner("Loading data from Google Sheets..."):
        df = load_data_from_sheet(sheet_url)
    
    if df is None:
        st.error("❌ Failed to load data. Please check your sheet URL and credentials.")
        st.stop()
    
    # Main content
    st.header(f"📊 Dashboard for {selected_date.strftime('%B %Y')}")
    
    # Display KPI cards
    if not df.empty:
        _, kpis = create_budget_analysis(df, selected_date, budget)
        display_kpi_cards(kpis, budget)
    else:
        st.info("No data available for KPI calculation.")
    
    st.markdown("---")
    
    # Add Job Section
    with st.expander("➕ Add New Job", expanded=False):
        display_add_job_form(sheet_url)
    
    st.markdown("---")
    
    # Create two columns for the main charts
    if not df.empty:
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("📅 Job Schedule - Gantt Chart")
            gantt_fig = create_gantt_chart(df, selected_date)
            st.plotly_chart(gantt_fig, use_container_width=True)
        
        with col2:
            st.subheader("💰 Budget Analysis")
            budget_fig, _ = create_budget_analysis(df, selected_date, budget)
            st.plotly_chart(budget_fig, use_container_width=True)
        
        st.markdown("---")
        
        # Job Management
        display_job_management(df, sheet_url)
        
        st.markdown("---")
        
        # Data table
        st.subheader("📊 Job Data Summary")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            show_all = st.checkbox("Show all jobs", value=False)
        with col2:
            if not show_all:
                st.info(f"Showing jobs for {selected_date.strftime('%B %Y')}")
        
        # Display filtered data
        if show_all:
            display_df = df.copy()
        else:
            month_start = selected_date.replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - datetime.timedelta(days=1)
            mask = (df['Start Date'] <= pd.Timestamp(month_end)) & (df['End Date'] >= pd.Timestamp(month_start))
            display_df = df[mask].copy()
        
        if not display_df.empty:
            # Format for display
            display_df_formatted = display_df.copy()
            display_df_formatted['Start Date'] = display_df_formatted['Start Date'].dt.strftime('%Y-%m-%d')
            display_df_formatted['End Date'] = display_df_formatted['End Date'].dt.strftime('%Y-%m-%d')
            display_df_formatted['Estimated Cost'] = display_df_formatted['Estimated Cost'].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(
                display_df_formatted,
                use_container_width=True,
                hide_index=True
            )
            
            # Summary statistics
            if show_all:
                total_cost = df['Estimated Cost'].sum()
                total_jobs = len(df)
            else:
                total_cost = display_df['Estimated Cost'].sum()
                total_jobs = len(display_df)
            
            st.caption(f"**Total:** {total_jobs} jobs | **Total Cost:** ${total_cost:,.0f}")
        else:
            st.info("No jobs found for the selected period.")
    else:
        st.info("🏗️ No jobs found in your sheet. Use the 'Add New Job' section above to get started!")

if __name__ == "__main__":
    main() 