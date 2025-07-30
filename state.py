# state.py
import streamlit as st
import pandas as pd
from data import INSTANCE_LIST, SQL_WAREHOUSE_SIZES, S3_STORAGE_CLASSES, DBU_RATES

def initialize_state():
    """Initializes session state variables if they don't exist."""
    if 'initialized' in st.session_state:
        return

    st.session_state.initialized = True

    # Databricks state
    st.session_state.dbx_jobs = {
        tier: pd.DataFrame([{
            "#": 1, "Job Name": f"{tier.split(' / ')[1]} Job 1", "Runtime (hrs)": 0, "Runs/Month": 0,
            "Instance Type": INSTANCE_LIST[0], "Nodes": 1, "Photon": False, "Spot": False
        }]) for tier in DBU_RATES.keys()
    }

    # S3 state
    st.session_state.s3_calc_method = "Direct Storage"
    st.session_state.s3_direct = {
        "Landing Zone": {"class": "Standard", "amount": 0, "unit": "GB", "put": 0, "get": 0},
        "L0 / Bronze": {"class": "Standard", "amount": 0, "unit": "GB", "put": 0, "get": 0},
        "L1 / Silver": {"class": "Infrequent Access", "amount": 0, "unit": "GB", "put": 0, "get": 0},
        "L2 / Gold": {"class": "Standard", "amount": 0, "unit": "GB", "put": 0, "get": 0},
    }
    st.session_state.s3_table_based = {
        "Landing Zone": {"tables": 0, "records": 100000, "size_kb": 1.0},
        "L0 / Bronze": {"tables": 0, "records": 100000, "size_kb": 1.5},
        "L1 / Silver": {"tables": 0, "records": 100000, "size_kb": 2.0},
        "L2 / Gold": {"tables": 0, "records": 100000, "size_kb": 2.5},
    }

    # SQL Warehouse state
    st.session_state.sql_warehouses = [{
        "id": "warehouse_0", "name": "Primary BI Warehouse", "size": SQL_WAREHOUSE_SIZES[0], # Default to 2X-Small
        "hours_per_day": 8, "days_per_month": 22, "auto_suspend": True, "suspend_after": 10
    }]

    #Monthly Growth Rate for Databricks & S3
    st.session_state.monthly_growth_percent = 0.0 