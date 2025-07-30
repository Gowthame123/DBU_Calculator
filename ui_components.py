# ui_components.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import DBU_RATES, INSTANCE_LIST, S3_STORAGE_CLASSES, SQL_WAREHOUSE_SIZES, SQL_WAREHOUSE_PRICING

def render_summary_column(total_cost, databricks_cost, s3_cost, sql_cost):
    """Renders the right-hand summary column with the donut chart."""
    st.header("📈 Monthly Total")
    st.metric("Total Cloud Cost", f"${total_cost:,.2f}")
    st.divider()

        # New: Monthly Growth Input
    st.subheader("Growth Projection")
    st.session_state.monthly_growth_percent = st.number_input(
        "Monthly Databricks + S3 Growth %",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.monthly_growth_percent,
        step=0.1,
        format="%.1f",
        help="Anticipated monthly percentage increase in Databricks and S3 costs."
    )

    # Calculate 12-month projected cost
    projected_cost_12_months = 0
    current_dbx_s3_cost = databricks_cost + s3_cost
    sql_warehouse_cost_fixed = sql_cost # SQL warehouse cost is assumed not to grow with this percentage

    if st.session_state.monthly_growth_percent > 0:
        growth_factor = 1 + (st.session_state.monthly_growth_percent / 100)
        # Calculate sum of a geometric series for 12 months for growing costs
        # Sum = a * (r^n - 1) / (r - 1)
        # a = current_dbx_s3_cost (cost for month 1)
        # r = growth_factor
        # n = 12 months
        if growth_factor != 1: # Avoid division by zero if growth is 0%
            projected_cost_12_months = current_dbx_s3_cost * (growth_factor**12 - 1) / (growth_factor - 1)
        else: # If growth is 0%, it's just 12 * current_dbx_s3_cost
            projected_cost_12_months = current_dbx_s3_cost * 12
    else:
        projected_cost_12_months = current_dbx_s3_cost * 12 # No growth, just 12x current cost

    # Add the fixed SQL warehouse cost for 12 months
    projected_cost_12_months += sql_warehouse_cost_fixed * 12

    st.metric("12-Month Projected Total", f"${projected_cost_12_months:,.2f}")
    st.divider()

    st.header("Cost Distribution")
    cost_data = {
        "Databricks & Compute": databricks_cost,
        "S3 Storage": s3_cost,
        "SQL Warehouse": sql_cost,
    }
    non_zero_costs = {k: v for k, v in cost_data.items() if v > 0}

    if non_zero_costs:
        fig = go.Figure(data=[go.Pie(
            labels=list(non_zero_costs.keys()), values=list(non_zero_costs.values()), hole=.6,
            marker_colors=['#FF8C00', '#3CB371', '#1E90FF'], hoverinfo="label+percent",
            textinfo="percent", textfont_size=14
        )])
        fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",
            y=-0.2,  # Adjust this value to move the legend further down
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=0, b=0, l=0, r=0),
        height=250
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No costs configured yet.")

    st.divider()
    st.header("Cost Insights")
    st.info("""
    - Consider **spot instances** for non-critical workloads to save ~70% on EC2.
    - Enable **auto-suspend** for SQL warehouses to avoid paying for idle compute.
    - Use appropriate **S3 storage classes** for data to optimize storage costs.
    """)

def render_databricks_tab(calculated_dbx_data):
    """Renders the detailed Databricks & Compute tab UI."""
    st.header("Databricks & Compute Costs")
    st.markdown("Configure jobs across different tiers. Specify the number of jobs and configure them in the table below.")
    # container for the main content
    total_dbu_cost = sum(data['dbu_cost'] for data in calculated_dbx_data.values())
    total_ec2_cost = sum(data['ec2_cost'] for data in calculated_dbx_data.values())
    total_jobs = sum(len(st.session_state.dbx_jobs[tier]) for tier in DBU_RATES.keys())

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Jobs", f"{total_jobs}")
        c2.metric("DBU Costs", f"${total_dbu_cost:,.2f}")
        c3.metric("EC2 Costs", f"${total_ec2_cost:,.2f}")
        c4.metric("Monthly Total", f"${total_dbu_cost + total_ec2_cost:,.2f}")

    for tier, data in calculated_dbx_data.items():
        with st.container(border=True):
            df_state = st.session_state.dbx_jobs[tier]
            tier_total_cost = data['dbu_cost'] + data['ec2_cost']
            
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"### {tier} <span style='background-color:#E8E8E8; border-radius:5px; padding: 2px 8px; font-size:90%; font-weight:bold; color:black;'>${tier_total_cost:,.2f}</span>", unsafe_allow_html=True)
            
            c2.write(f"{tier}")
            num_jobs = c2.number_input("Number of Jobs", min_value=0, max_value=20, value=len(df_state), key=f"num_jobs_{tier}", label_visibility="collapsed")

            # --- THIS IS THE FIX ---
            # This logic robustly handles adding or removing rows and prevents errors.
            current_len = len(df_state)
            if num_jobs != current_len:
                if num_jobs > current_len:
                    # Add new rows
                    new_rows_count = num_jobs - current_len
                    new_rows = pd.DataFrame([{
                        "Job Name": "New Job", "Runtime (hrs)": 0, "Runs/Month": 0,
                        "Instance Type": INSTANCE_LIST[0], "Nodes": 1, "Photon": False, "Spot": False
                    }] * new_rows_count)
                    updated_df = pd.concat([df_state, new_rows], ignore_index=True)
                else: # num_jobs < current_len
                    # Remove rows from the end
                    updated_df = df_state.head(num_jobs)
                
                # Always re-index the '#' column after any change
                updated_df['#'] = updated_df.index + 1
                st.session_state.dbx_jobs[tier] = updated_df
                st.rerun()


            if not df_state.empty:
                display_df = data['df']
                editable_cols = ["Job Name", "Runtime (hrs)", "Runs/Month", "Instance Type", "Nodes", "Photon", "Spot"]
                
                edited_df = st.data_editor(
                    display_df,
                    column_order=["Job Name", "#", "Runtime (hrs)", "Runs/Month", "Instance Type", "Nodes", "Photon", "Spot", "DBU Units", "EC2 Cost", "DBU Cost" ],
                    column_config={
                        "#": st.column_config.NumberColumn("Job.no", disabled=True, width="small"),
                        "Instance Type": st.column_config.SelectboxColumn("Instance Type", options=INSTANCE_LIST, required=True),
                       # "DBU Rate": st.column_config.NumberColumn("DBU Rate", format="$%.4f", disabled=True),
                        #"Cost": st.column_config.TextColumn("Cost", disabled=True),
                        "DBU Units": st.column_config.NumberColumn("DBU", format="%.2f", disabled=True),
                        "DBU Cost": st.column_config.NumberColumn("DBX", format="$%.2f", disabled=True),
                        "EC2 Cost": st.column_config.NumberColumn("EC2", format="$%.2f", disabled=True),
                    },
                    hide_index=True, key=f"editor_{tier}", use_container_width=True
                )
                
                # if not edited_df[editable_cols].reset_index(drop=True).equals(df_state[editable_cols].reset_index(drop=True)):
                #     st.session_state.dbx_jobs[tier] = edited_df[["#"] + editable_cols]
                #     st.rerun()

                if not edited_df[editable_cols].reset_index(drop=True).equals(df_state[editable_cols].reset_index(drop=True)):
                    st.session_state.dbx_jobs[tier] = edited_df[["#"] + editable_cols ] 
                    st.rerun()

def render_s3_tab(s3_costs_per_zone, total_s3_cost):
    """Renders the S3 Storage tab UI with a vertical layout and summary."""
    st.header("AWS S3 Storage Costs")
    st.radio("Calculation Method", ["Direct Storage", "Table-Based"], key="s3_calc_method", horizontal=True)
    
    st.divider()

    if st.session_state.s3_calc_method == "Direct Storage":
        for zone, config in st.session_state.s3_direct.items():
            with st.container(border=True):
                st.subheader(zone)
                c1, c2, c3 = st.columns(3)
                config["class"] = c1.selectbox("Storage Class", S3_STORAGE_CLASSES, key=f"s3_class_{zone}", index=S3_STORAGE_CLASSES.index(config["class"]))
                config["amount"] = c2.number_input("Storage Amount", min_value=0, key=f"s3_amount_{zone}", value=config["amount"])
                config["unit"] = c3.selectbox("Unit", ["GB", "TB"], key=f"s3_unit_{zone}", index=["GB", "TB"].index(config["unit"]))
                
                # c4, c5, _ = st.columns(3)
                # config["put"] = c4.number_input("PUTs (x1000)", min_value=0, key=f"s3_put_{zone}", value=config["put"])
                # config["get"] = c5.number_input("GETs (x1000)", min_value=0, key=f"s3_get_{zone}", value=config["get"])
    else: # Table-Based
        for zone, config in st.session_state.s3_table_based.items():
            with st.container(border=True):
                st.subheader(zone)
                c1, c2, c3 = st.columns(3)
                config["tables"] = c1.number_input("Tables", min_value=0, key=f"s3_tbl_tables_{zone}", value=config["tables"])
                config["records"] = c2.number_input("Avg Records", min_value=0, key=f"s3_tbl_records_{zone}", value=config["records"])
                # Changed format to integer and step to 1
                config["size_kb"] = c3.number_input("Avg Rec Size (KB)", min_value=0, key=f"s3_tbl_size_{zone}", value=int(config["size_kb"]), step=1)

    st.divider()

    with st.container(border=True):
        st.subheader("Total S3 Storage Cost")
        st.markdown(f"<h2 style='text-align: center;'>${total_s3_cost:,.2f}/month</h2>", unsafe_allow_html=True)
        st.caption(f"Calculated using {st.session_state.s3_calc_method} method")
        
        st.divider()
        
        cols = st.columns(4)
        for i, (zone, cost) in enumerate(s3_costs_per_zone.items()):
            with cols[i]:
                st.metric(label=zone, value=f"${cost:,.2f}")

def render_sql_warehouse_tab(total_sql_cost):
    """Renders the SQL Warehouse tab UI with a total cost summary."""
    st.header("Databricks SQL Warehouse Costs")
    
    for i, warehouse in enumerate(st.session_state.sql_warehouses):
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.subheader(warehouse["name"])
                size_key = warehouse["size"].split(" - ")[0]
                dbt_per_hr = SQL_WAREHOUSE_PRICING.get(size_key, {}).get("dbt_per_hr", 0)
                st.caption(f"{dbt_per_hr} DBUs • {warehouse['hours_per_day']}h/day • {warehouse['days_per_month']} days/month")
            # with c3:
            #     if warehouse["auto_suspend"]:
            #         hourly_rate = SQL_WAREHOUSE_PRICING.get(size_key, {}).get("cost_per_hr", 0)
            #         warehouse_cost = hourly_rate * warehouse["hours_per_day"] * warehouse["days_per_month"]
            #         st.markdown(f"<h4 style='text-align: right;'>${warehouse_cost:,.2f}/month</h4>", unsafe_allow_html=True)
            #     else:
            #         st.markdown(f"<h4 style='text-align: right;'>$0.00/month</h4>", unsafe_allow_html=True)
            
            st.markdown("---")

            st.markdown("**Basic Configuration**")
            c1, c2 = st.columns(2)
            warehouse["name"] = c1.text_input("Warehouse Name", value=warehouse["name"], key=f"sql_name_{i}", label_visibility="collapsed")
            warehouse["size"] = c2.selectbox("Warehouse Size", SQL_WAREHOUSE_SIZES, index=SQL_WAREHOUSE_SIZES.index(warehouse["size"]), key=f"sql_size_{i}", label_visibility="collapsed")

            st.markdown("**Usage Configuration**")
            c3, c4 = st.columns(2)
            warehouse["hours_per_day"] = c3.number_input("Hours per Day", min_value=0, max_value=24, value=warehouse["hours_per_day"], key=f"sql_hours_{i}")
            warehouse["days_per_month"] = c4.number_input("Days per Month", min_value=0, max_value=31, value=warehouse["days_per_month"], key=f"sql_days_{i}")

            # st.markdown("**Auto-Suspend Configuration**")
            # warehouse["auto_suspend"] = st.checkbox("Enable Auto-Suspend", value=warehouse["auto_suspend"], key=f"sql_suspend_{i}")
            # if warehouse["auto_suspend"]:
            #     warehouse["suspend_after"] = st.number_input("Suspend After (minutes)", min_value=0, value=warehouse["suspend_after"], key=f"sql_suspend_after_{i}")

    if st.button("＋ Add SQL Warehouse"):
        new_id = f"warehouse_{len(st.session_state.sql_warehouses)}"
        st.session_state.sql_warehouses.append({"id": new_id, "name": "New Warehouse", "size": SQL_WAREHOUSE_SIZES[0], "hours_per_day": 8, "days_per_month": 22, "auto_suspend": True, "suspend_after": 10})
        st.rerun()

    st.divider()

    with st.container(border=True):
        st.subheader("Total SQL Warehouse Cost")
        warehouse_count = len(st.session_state.sql_warehouses)
        st.markdown(f"<h2 style='text-align: center;'>${total_sql_cost:,.2f}/month</h2>", unsafe_allow_html=True)
        st.caption(f"{warehouse_count} warehouse(s) configured")

def render_configuration_guide():
    """Renders the configuration guide expander at the bottom of a tab."""
    with st.expander("ℹ️ Configuration Guide", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            **Photon Engine** Adds 20% to DBU cost but provides significant performance improvements for analytical workloads.
            """)
            st.markdown("""
            **DBU Rates (Auto-calculated)** Bronze: $0.15, Silver: $0.30, Gold: $0.60 per DBU hour (before Photon premium).
            """)
        with c2:
            st.markdown("""
            **Spot Instances** Provides ~70% cost savings on EC2 compute but instances may be interrupted.
            """)
            st.markdown("""
            **Instance Families** Choose instance types based on workload: General Purpose (`m5`), Compute Optimized (`c5`), Memory Optimized (`r5`/`r5d`).
            """)