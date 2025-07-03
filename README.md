# 🏗️ Construction Jobs Dashboard

A comprehensive Streamlit dashboard for tracking construction jobs, schedules, and budget analysis. The dashboard connects to Google Sheets to display interactive Gantt charts, budget timelines, and KPI metrics.

## Features

- **Interactive Gantt Chart**: Month-by-month view of job schedules with hover tooltips
- **Budget Analysis**: Daily spend tracking and cumulative budget analysis
- **KPI Dashboard**: Real-time metrics including total spend, remaining budget, and job counts
- **Google Sheets Integration**: Automatic data sync with caching for performance
- **Responsive Design**: Mobile-friendly interface with customizable views

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Google Sheets API

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the **Google Sheets API** and **Google Drive API**

2. **Create Service Account**:
   - Go to IAM & Admin > Service Accounts
   - Create a new service account
   - Download the JSON credentials file
   - Rename it to `credentials.json` and place it in the project root

3. **Prepare Your Google Sheet**:
   - Create a new Google Sheet with the required columns (see format below)
   - Share the sheet with the service account email (found in `credentials.json`)
   - Copy the sheet URL for the dashboard

### 3. Run the Dashboard

```bash
streamlit run construction_dashboard.py
```

## Google Sheet Format

Your Google Sheet should have these exact column headers:

| Job Name | Start Date | End Date | Estimated Cost | Estimated Duration | Status
|----------|------------|----------|----------------|-------------------|
| Foundation Work | 2024-01-15 | 2024-02-28 | 50000 | 44 |
| Framing | 2024-03-01 | 2024-04-15 | 75000 | 45 |
| Electrical Installation | 2024-04-01 | 2024-05-15 | 30000 | 44 |
| Plumbing | 2024-04-15 | 2024-05-30 | 25000 | 45 |
| Drywall | 2024-05-01 | 2024-06-15 | 35000 | 45 |

### Column Specifications:
- **Job Name**: Text description of the construction job
- **Start Date**: Format as YYYY-MM-DD (e.g., 2024-01-15)
- **End Date**: Format as YYYY-MM-DD (e.g., 2024-02-28)
- **Estimated Cost**: Numeric value (no currency symbols)
- **Estimated Duration**: Number of days (numeric)
- **Status**: Text description of the job status

## Deployment Options

### Local Development
```bash
streamlit run construction_dashboard.py
```

### Streamlit Cloud Deployment

1. **Push to GitHub**: Upload your code to a GitHub repository
2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Add your Google credentials to Streamlit secrets:
     ```toml
     [google_credentials]
     type = "service_account"
     project_id = "your-project-id"
     private_key_id = "your-private-key-id"
     private_key = "your-private-key"
     client_email = "your-service-account-email"
     client_id = "your-client-id"
     auth_uri = "https://accounts.google.com/o/oauth2/auth"
     token_uri = "https://oauth2.googleapis.com/token"
     ```

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "construction_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t construction-dashboard .
docker run -p 8501:8501 construction-dashboard
```

## Environment Variables

Alternative to `credentials.json` file:

```bash
export GOOGLE_CREDENTIALS='{"type": "service_account", "project_id": "...", ...}'
```

## Usage Guide

1. **Launch the App**: Open the dashboard in your browser
2. **Enter Sheet URL**: Paste your Google Sheet URL in the sidebar
3. **Configure Budget**: Set your total project budget
4. **Navigate**: Use year/month selectors to view different time periods
5. **Analyze**: Review Gantt charts, budget analysis, and KPI metrics

## Dashboard Components

### 📅 Gantt Chart
- Interactive timeline showing job schedules
- Color-coded job bars with hover details
- Month-by-month navigation
- Automatically clips jobs to month boundaries

### 💰 Budget Analysis
- Daily spend tracking for new job starts
- Cumulative spend visualization
- Budget vs. actual comparison
- Progress indicators

### 📊 KPI Cards
- **Total Spend to Date**: Cumulative project spending
- **Remaining Budget**: Available budget remaining
- **Jobs This Month**: Count of jobs in selected month
- **Spend This Month**: New spending for the month

### 📋 Data Table
- Detailed job information
- Sortable and filterable
- Option to view all jobs or month-specific
- Summary statistics

## Troubleshooting

### Common Issues

1. **"Google credentials not found"**
   - Ensure `credentials.json` exists in the project root
   - Verify the service account has access to your sheet
   - Check that APIs are enabled in Google Cloud

2. **"Missing required columns"**
   - Verify your sheet has exact column names
   - Check for extra spaces or typos in headers
   - Ensure data types match requirements

3. **"No data found"**
   - Confirm the sheet has data rows below headers
   - Check that dates are in YYYY-MM-DD format
   - Verify numeric fields don't contain text

### Performance Tips

- **Data Caching**: The app caches sheet data for 5 minutes
- **Large Datasets**: Consider filtering or paginating for 500+ jobs
- **Refresh Data**: Use Streamlit's refresh button to reload data

## Customization

### Modify Budget Calculation
Edit the `create_budget_analysis()` function to change how cumulative spend is calculated.

### Add New Charts
Extend the dashboard by adding new Plotly visualizations in the main layout.

### Custom Styling
Use Streamlit's theming or custom CSS to modify appearance.

## Dependencies

- **streamlit**: Web app framework
- **pandas**: Data manipulation
- **plotly**: Interactive charts
- **gspread**: Google Sheets integration
- **google-auth**: Authentication
- **python-dateutil**: Date utilities

## License

MIT License - Feel free to modify and use for your projects.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Google Sheets API documentation
3. Verify your data format matches requirements 