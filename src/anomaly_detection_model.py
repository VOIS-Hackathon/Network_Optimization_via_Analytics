import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

df = pd.read_csv("data/cleaned_telecom_data.csv")

# Ensure timestamp is datetime
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Create call drop rate if not exists
if "call_drop_rate" not in df.columns:
    df["call_drop_rate"] = (df["dropped_calls"] / df["total_calls"]) * 100

# Convert bandwidth to numeric (strip units if needed)
df["bandwidth_numeric"] = df["bandwidth"].replace(
    {"Gbps": "e9", "Mbps": "e6"}, regex=True
)
df["bandwidth_numeric"] = (
    df["bandwidth_numeric"].str.replace("[^0-9\.]", "", regex=True).astype(float)
)

# Ensure timestamp is datetime
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Create call drop rate if not exists
if "call_drop_rate" not in df.columns:
    df["call_drop_rate"] = (df["dropped_calls"] / df["total_calls"]) * 100

# Convert bandwidth to numeric (strip units if needed)
df["bandwidth_numeric"] = df["bandwidth"].replace(
    {"Gbps": "e9", "Mbps": "e6"}, regex=True
)
df["bandwidth_numeric"] = (
    df["bandwidth_numeric"].str.replace("[^0-9\.]", "", regex=True).astype(float)
)

# -------------------
# Anomaly Detection (Latency + Drop Rate)
# -------------------
features = df[["latency_sec", "call_drop_rate", "bandwidth_numeric"]].fillna(0)
iso = IsolationForest(contamination=0.05, random_state=42)
df["anomaly"] = iso.fit_predict(features)
df["anomaly"] = df["anomaly"].map({1: "Normal", -1: "Anomaly"})


df.to_csv("final_data.csv", index=False)