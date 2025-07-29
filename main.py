# main.py
import streamlit as st
from streamlit_toggle import theme as st_toggle_theme
from state import initialize_state
from calculations import calculate_databricks_costs_for_tier, calculate_s3_cost_per_zone, calculate_sql_warehouse_cost
from ui_components import render_summary_column, render_databricks_tab, render_s3_tab, render_sql_warehouse_tab, render_configuration_guide
from data import DBU_RATES

# --- Page Configuration ---
st.set_page_config(
    page_title="Cloud Cost Calculator",
    page_icon="🧮",
    layout="wide"
)

# --- 1. Initialize Session State ---
# This is the most important part. It MUST be called before any calculations.
initialize_state()

# --- 2. Perform All Calculations ---
# This block can now safely access session_state because it has been initialized.
calculated_dbx_data = {}
for tier in DBU_RATES.keys():
    df_with_costs, dbu_cost, ec2_cost = calculate_databricks_costs_for_tier(st.session_state.dbx_jobs[tier], tier)
    calculated_dbx_data[tier] = {
        "df": df_with_costs,
        "dbu_cost": dbu_cost,
        "ec2_cost": ec2_cost
    }

s3_costs_per_zone, s3_cost = calculate_s3_cost_per_zone()
sql_cost = calculate_sql_warehouse_cost()

databricks_total_cost = sum(data['dbu_cost'] + data['ec2_cost'] for data in calculated_dbx_data.values())
total_cost = databricks_total_cost + s3_cost + sql_cost

# --- 3. Render Main Layout ---
title_col, toggle_col = st.columns([4, 1])

with title_col:
    st.title("☁️ Cloud Cost Calculator")
    st.caption("Databricks & AWS Cost Estimation")

with toggle_col:
    st_toggle_theme(widget='checkbox', label="🌙 Dark Mode")

main_col, summary_col = st.columns([3, 1])

with main_col:
    tab1, tab2, tab3 = st.tabs(["Databricks & Compute", "S3 Storage", "SQL Warehouse"])

    with tab1:
        render_databricks_tab(calculated_dbx_data)
        render_configuration_guide()
    with tab2:
        render_s3_tab(s3_costs_per_zone, s3_cost)
    with tab3:
        render_sql_warehouse_tab(sql_cost)

with summary_col:
    render_summary_column(total_cost, databricks_total_cost, s3_cost, sql_cost)