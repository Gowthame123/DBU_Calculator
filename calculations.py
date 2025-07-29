# calculations.py
import streamlit as st
import pandas as pd
from data import DBU_RATES, FLAT_INSTANCE_LIST, S3_PRICING, SQL_WAREHOUSE_PRICING, PHOTON_PREMIUM_MULTIPLIER, SPOT_DISCOUNT_MULTIPLIER

def calculate_databricks_costs_for_tier(jobs_df, tier):
    """
    Calculates costs for a specific tier's DataFrame.
    Returns a new DataFrame with calculated columns and total costs for the tier.
    """
    if jobs_df.empty:
        return pd.DataFrame(columns=["#", "Job Name", "Runtime (hrs)", "Runs/Month", "Instance Type", "Nodes", "Photon", "Spot", "DBU Cost", "EC2 Cost", "Total Cost"]), 0, 0

    df = jobs_df.copy()
    base_dbu_rate = DBU_RATES[tier]

    # Calculate DBU Rate per job
    DBU_cost = df.apply(
        lambda row: base_dbu_rate * PHOTON_PREMIUM_MULTIPLIER if row['Photon'] else base_dbu_rate,
        axis=1
    )

    # Calculate EC2 Cost per job
    def get_ec2_cost(row):
        ec2_rate = FLAT_INSTANCE_LIST.get(row["Instance Type"], 0) * (SPOT_DISCOUNT_MULTIPLIER if row["Spot"] else 1.0)
        return row["Runtime (hrs)"] * row["Runs/Month"] * row["Nodes"] * ec2_rate
    df['EC2 Cost'] = df.apply(get_ec2_cost, axis=1)

    # Calculate DBU Cost per job
    def get_dbu_cost(row):
        return row["Runtime (hrs)"] * row["Runs/Month"] * row["Nodes"] 
    df['DBU Cost'] = df.apply(get_dbu_cost, axis=1)

    # Create the formatted Cost string
    def format_cost_string(row):
        total_job_cost = row['DBU Cost'] + row['EC2 Cost']
        return f"${total_job_cost:,.2f}\nDBU: ${row['DBU Cost']:,.2f}\nEC2: ${row['EC2 Cost']:,.2f}"
    df['Cost'] = df.apply(format_cost_string, axis=1)
    
    # Calculate total costs for the tier
    total_dbu_cost = df['DBU Cost'].sum()
    total_ec2_cost = df['EC2 Cost'].sum()

    return df, total_dbu_cost, total_ec2_cost

def calculate_s3_cost_per_zone():
    """
    Calculates S3 cost for each individual zone and the total cost.
    """
    costs_per_zone = {}
    total_s3_cost = 0

    if "s3_calc_method" not in st.session_state:
        st.session_state["s3_calc_method"] = "Direct Storage"
        for zone, config in st.session_state.s3_direct.items():
            pricing = S3_PRICING.get(config["class"], {"storage_gb": 0, "put_1k": 0, "get_1k": 0})
            storage_gb = config["amount"] * 1024 if config["unit"] == "TB" else config["amount"]
            
            storage_cost = storage_gb * pricing["storage_gb"]
            put_cost = config["put"] * pricing["put_1k"]
            get_cost = config["get"] * pricing["get_1k"]
            
            zone_cost = storage_cost + put_cost + get_cost
            costs_per_zone[zone] = zone_cost
            total_s3_cost += zone_cost
            
    else: # Table-Based
        standard_pricing = S3_PRICING["Standard"]
        for zone, config in st.session_state.s3_table_based.items():
            total_records = config["tables"] * config["records"]
            estimated_gb = (total_records * config["size_kb"]) / (1024 * 1024)
            
            zone_cost = estimated_gb * standard_pricing["storage_gb"]
            costs_per_zone[zone] = zone_cost
            total_s3_cost += zone_cost
            
    return costs_per_zone, total_s3_cost

def calculate_sql_warehouse_cost():
    """Calculates total SQL Warehouse cost from session state."""
    total_sql_cost = 0
    for warehouse in st.session_state.sql_warehouses:
        if warehouse["auto_suspend"] and warehouse["hours_per_day"] > 0 and warehouse["days_per_month"] > 0:
            size_key = warehouse["size"].split(" - ")[0]
            hourly_rate = SQL_WAREHOUSE_PRICING.get(size_key, {}).get("cost_per_hr", 0)
            cost = hourly_rate * warehouse["hours_per_day"] * warehouse["days_per_month"]
            total_sql_cost += cost
            
    return total_sql_cost