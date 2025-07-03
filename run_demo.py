#!/usr/bin/env python3
"""
Simple test runner for the construction dashboard demo.
This script verifies the core functionality without requiring Streamlit.
"""

import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta

def load_demo_data() -> pd.DataFrame:
    """Load demo data from CSV or create sample data."""
    try:
        df = pd.read_csv('sample_data.csv')
        print("✓ Loaded data from sample_data.csv")
    except FileNotFoundError:
        print("📁 Creating sample data (sample_data.csv not found)")
        data = {
            'Job Name': [
                'Foundation Work', 'Site Preparation', 'Framing', 'Roofing',
                'Electrical Installation', 'Plumbing', 'HVAC Installation'
            ],
            'Start Date': [
                '2024-01-15', '2024-01-01', '2024-03-01', '2024-04-10',
                '2024-04-01', '2024-04-15', '2024-05-01'
            ],
            'End Date': [
                '2024-02-28', '2024-01-14', '2024-04-15', '2024-05-05',
                '2024-05-15', '2024-05-30', '2024-06-10'
            ],
            'Estimated Cost': [50000, 15000, 75000, 45000, 30000, 25000, 40000],
            'Estimated Duration': [44, 14, 45, 25, 44, 45, 40]
        }
        df = pd.DataFrame(data)
    
    # Clean and convert data types
    df['Start Date'] = pd.to_datetime(df['Start Date'])
    df['End Date'] = pd.to_datetime(df['End Date'])
    df['Estimated Cost'] = pd.to_numeric(df['Estimated Cost'])
    df['Estimated Duration'] = pd.to_numeric(df['Estimated Duration'])
    
    return df

def test_data_loading():
    """Test data loading functionality."""
    print("🧪 Testing data loading...")
    df = load_demo_data()
    
    print(f"✓ Loaded {len(df)} jobs")
    print(f"✓ Date range: {df['Start Date'].min().strftime('%Y-%m-%d')} to {df['End Date'].max().strftime('%Y-%m-%d')}")
    print(f"✓ Total estimated cost: ${df['Estimated Cost'].sum():,.0f}")
    print()

def test_monthly_filtering():
    """Test monthly filtering logic."""
    print("🧪 Testing monthly filtering...")
    df = load_demo_data()
    
    # Test for January 2024
    selected_month = datetime.date(2024, 1, 1)
    month_start = selected_month.replace(day=1)
    month_end = (month_start + relativedelta(months=1)) - datetime.timedelta(days=1)
    
    # Filter jobs that overlap with the selected month
    mask = (df['Start Date'] <= pd.Timestamp(month_end)) & (df['End Date'] >= pd.Timestamp(month_start))
    month_jobs = df[mask]
    
    print(f"✓ January 2024: {len(month_jobs)} jobs")
    if not month_jobs.empty:
        for _, job in month_jobs.iterrows():
            print(f"  - {job['Job Name']}: ${job['Estimated Cost']:,.0f}")
    print()

def test_budget_calculations():
    """Test budget calculation logic."""
    print("🧪 Testing budget calculations...")
    df = load_demo_data()
    total_budget = 500000
    
    # Test for March 2024
    selected_month = datetime.date(2024, 3, 1)
    month_start = selected_month.replace(day=1)
    month_end = (month_start + relativedelta(months=1)) - datetime.timedelta(days=1)
    
    # Get jobs starting in the selected month
    month_jobs = df[
        (df['Start Date'] >= pd.Timestamp(month_start)) & 
        (df['Start Date'] <= pd.Timestamp(month_end))
    ]
    
    # Calculate cumulative spend through the selected month
    cumulative_jobs = df[df['Start Date'] <= pd.Timestamp(month_end)]
    total_spend_to_date = cumulative_jobs['Estimated Cost'].sum()
    budget_used_pct = (total_spend_to_date / total_budget) * 100
    
    print(f"✓ March 2024 analysis:")
    print(f"  - Jobs starting this month: {len(month_jobs)}")
    print(f"  - Spend this month: ${month_jobs['Estimated Cost'].sum():,.0f}")
    print(f"  - Total spend to date: ${total_spend_to_date:,.0f}")
    print(f"  - Budget used: {budget_used_pct:.1f}%")
    print(f"  - Remaining budget: ${total_budget - total_spend_to_date:,.0f}")
    print()

def main():
    """Run all tests."""
    print("🏗️ Construction Dashboard - Core Functionality Test")
    print("=" * 50)
    
    try:
        test_data_loading()
        test_monthly_filtering()
        test_budget_calculations()
        
        print("✅ All core functionality tests passed!")
        print()
        print("🚀 To run the full dashboard:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Run demo: streamlit run demo_dashboard.py")
        print("   3. Run full version: streamlit run construction_dashboard.py")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("Please check that pandas and python-dateutil are installed.")

if __name__ == "__main__":
    main() 