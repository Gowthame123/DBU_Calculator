# data.py

# AWS EC2 Instance Pricing (USD per hour) - Sample Data for us-east-1
INSTANCE_PRICES = {
    "General Purpose": {
        "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384,
        "m6i.large": 0.096, "m6i.xlarge": 0.192, "m6i.2xlarge": 0.384,
    },
    "Compute Optimized": {
        "c5.large": 0.085, "c5.xlarge": 0.17, "c5.2xlarge": 0.34,
        "c6i.large": 0.085, "c6i.xlarge": 0.17, "c6i.2xlarge": 0.34,
    },
    "Memory Optimized": {
        "r5.large": 0.126, "r5.xlarge": 0.252, "r5.2xlarge": 0.504,
        "r5d.large": 0.144, "r5d.xlarge": 0.288, "r5d.2xlarge": 0.576,
    },
    "Storage Optimized": {
        "i3.large": 0.156, "i3.xlarge": 0.312, "i3.2xlarge": 0.624,
    }
}
# Flatten the instance list for the selectbox, but keep the prices separate for lookup
FLAT_INSTANCE_LIST = {f"{k} ({fam})": p for fam, instances in INSTANCE_PRICES.items() for k, p in instances.items()}
INSTANCE_LIST = list(FLAT_INSTANCE_LIST.keys())

# Databricks DBU Rates (USD per DBU)
DBU_RATES = {
    "L0 / Bronze": 0.15,
    "L1 / Silver": 0.30,
    "L2 / Gold": 0.60
}
# Constants for calculation
PHOTON_PREMIUM_MULTIPLIER = 1.2 # 20% cost increase
SPOT_DISCOUNT_MULTIPLIER = 0.3 # 70% discount means you pay 30%

# AWS S3 Pricing (USD) - Sample Data for us-east-1
S3_PRICING = {
    "Standard": {"storage_gb": 0.023, "put_1k": 0.005, "get_1k": 0.0004},
    "Intelligent-Tiering": {"storage_gb": 0.023, "put_1k": 0.005, "get_1k": 0.0004},
    "Infrequent Access": {"storage_gb": 0.0125, "put_1k": 0.01, "get_1k": 0.001},
    "Glacier Instant Retrieval": {"storage_gb": 0.004, "put_1k": 0.02, "get_1k": 0.01},
}
S3_STORAGE_CLASSES = list(S3_PRICING.keys())

# --- UPDATED: SQL Warehouse data now includes DBU and cost info for the UI ---
SQL_WAREHOUSE_PRICING = {
    "2X-Small": {"dbt_per_hr": 1, "cost_per_hr": 0.22},
    "X-Small": {"dbt_per_hr": 2, "cost_per_hr": 0.44},
    "Small": {"dbt_per_hr": 4, "cost_per_hr": 0.88},
    "Medium": {"dbt_per_hr": 8, "cost_per_hr": 1.76},
    "Large": {"dbt_per_hr": 16, "cost_per_hr": 3.52},
    "X-Large": {"dbt_per_hr": 32, "cost_per_hr": 7.04}
}
# Create a user-friendly list for the selectbox
SQL_WAREHOUSE_SIZES = [f"{size} - {data['dbt_per_hr']} DBUs - ${data['cost_per_hr']}/hr" for size, data in SQL_WAREHOUSE_PRICING.items()]
# --- END OF UPDATE ---