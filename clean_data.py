#!/usr/bin/env python
# coding: utf-8

# Data Loading and Normalization

# In[14]:


import pandas as pd
import json


# In[15]:


with open('Use Case 3 - Network optimisation.json',"r") as f:
    data=json.load(f)


# In[16]:


df=pd.json_normalize(data)


# In[17]:


df.head()


# Data Cleaning

# In[18]:


# Convert timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])


# In[19]:


df.head()


# In[20]:


# Calculate call drop rate (%)
df["call_drop_rate"] = (df["dropped_calls"] / df["total_calls"]) * 100


# In[21]:


df.head()


# In[22]:


import re

def convert_bandwidth(value):
    if pd.isna(value):
        return None
    num=float(re.findall(r"[\d.]+", value)[0])

    if "Mbps" in value:
        return num
    elif "Gbps" in value:
        return num*1000
    else:
        return num


# In[23]:


df["bandwidth_mbps"]=df["bandwidth"].apply(convert_bandwidth)


# In[24]:


df.head()


# In[25]:


print("\n🔹 First 10 rows of data:")
print(df.head(10))


# In[30]:


# Save cleaned dataset
df.to_csv("cleaned_telecom_data.csv", index=False)

# If you are in Google Colab

# If in Jupyter Notebook (local)
# Just check the folder where notebook is stored, the file will be saved there


# In[27]:





# In[31]:


print("🔹 Column Headings:")
print(list(df.columns))


# In[33]:


pip install "numpy<1.27" --force-reinstall


# In[34]:


pip install --upgrade --pre scikit-learn scipy


# In[3]:


import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# -------------------
# Load & preprocess
# -------------------
df = pd.read_csv("cleaned_telecom_data.csv")   # replace with your dataset path

# Ensure timestamp is datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Create call drop rate if not exists
if 'call_drop_rate' not in df.columns:
    df['call_drop_rate'] = (df['dropped_calls'] / df['total_calls']) * 100

# Convert bandwidth to numeric (strip units if needed)
df['bandwidth_numeric'] = df['bandwidth'].replace({'Gbps':'e9','Mbps':'e6'}, regex=True)
df['bandwidth_numeric'] = df['bandwidth_numeric'].str.replace('[^0-9\.]', '', regex=True).astype(float)

# -------------------
# Anomaly Detection (Latency + Drop Rate)
# -------------------
features = df[['latency_sec', 'call_drop_rate', 'bandwidth_numeric']].fillna(0)
iso = IsolationForest(contamination=0.05, random_state=42)
df['anomaly'] = iso.fit_predict(features)
df['anomaly'] = df['anomaly'].map({1: "Normal", -1: "Anomaly"})

# -------------------
# Dash App
# -------------------
app = dash.Dash(__name__)

# Dropdown options
operators = [{'label': op, 'value': op} for op in df['operator'].unique()]
network_types = [{'label': nt, 'value': nt} for nt in df['network_type'].unique()]

app.layout = html.Div([
    html.H1("📡 Network Performance Optimization Dashboard", style={'textAlign': 'center'}),

    # Filters
    html.Div([
        html.Label("Select Operator:"),
        dcc.Dropdown(id="operator_filter", options=operators, value=None, multi=True),
        html.Label("Select Network Type:"),
        dcc.Dropdown(id="network_filter", options=network_types, value=None, multi=True),
        dcc.DatePickerRange(
            id="date_filter",
            start_date=df['timestamp'].min(),
            end_date=df['timestamp'].max(),
            display_format='YYYY-MM-DD'
        )
    ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr 1fr', 'gap': '20px'}),

    html.Br(),

    # KPI Cards
    html.Div(id="kpi_cards", style={'display': 'flex', 'justifyContent': 'space-around'}),

    html.Br(),

    # Tabs
    dcc.Tabs([
        dcc.Tab(label="Trends", children=[
            dcc.Graph(id="latency_trend"),
            dcc.Graph(id="drop_trend"),
            dcc.Graph(id="bandwidth_trend"),
        ]),
        dcc.Tab(label=" Anomalies", children=[
            dcc.Graph(id="anomaly_scatter"),
        ]),
        dcc.Tab(label=" Geo View", children=[
            dcc.Graph(id="geo_map"),
        ]),
    ])
])


# -------------------
# Callbacks
# -------------------
@app.callback(
    [Output("kpi_cards", "children"),
     Output("latency_trend", "figure"),
     Output("drop_trend", "figure"),
     Output("bandwidth_trend", "figure"),
     Output("anomaly_scatter", "figure"),
     Output("geo_map", "figure")],
    [Input("operator_filter", "value"),
     Input("network_filter", "value"),
     Input("date_filter", "start_date"),
     Input("date_filter", "end_date")]
)
def update_dashboard(selected_ops, selected_nts, start_date, end_date):
    dff = df.copy()

    # Apply filters
    if selected_ops:
        dff = dff[dff['operator'].isin(selected_ops)]
    if selected_nts:
        dff = dff[dff['network_type'].isin(selected_nts)]
    dff = dff[(dff['timestamp'] >= start_date) & (dff['timestamp'] <= end_date)]

    # KPI cards
    kpi_cards = [
        html.Div([
            html.H3("Avg Latency"),
            html.H4(f"{dff['latency_sec'].mean():.2f} sec")
        ], style={'border': '1px solid black', 'padding': '10px', 'borderRadius': '10px'}),

        html.Div([
            html.H3("Total Dropped Calls"),
            html.H4(f"{dff['dropped_calls'].sum()}")
        ], style={'border': '1px solid black', 'padding': '10px', 'borderRadius': '10px'}),

        html.Div([
            html.H3("Avg Bandwidth"),
            html.H4(f"{dff['bandwidth_numeric'].mean()/1e6:.2f} Mbps")
        ], style={'border': '1px solid black', 'padding': '10px', 'borderRadius': '10px'}),

        html.Div([
            html.H3("Avg Drop Rate"),
            html.H4(f"{dff['call_drop_rate'].mean():.2f}%")
        ], style={'border': '1px solid black', 'padding': '10px', 'borderRadius': '10px'}),
    ]

    # Trends
    latency_fig = px.line(dff, x="timestamp", y="latency_sec", color="operator", title="Latency Over Time")
    drop_fig = px.line(dff, x="timestamp", y="dropped_calls", color="operator", title="Dropped Calls Over Time")
    bandwidth_fig = px.line(dff, x="timestamp", y="bandwidth_numeric", color="operator", title="Bandwidth Usage Over Time")

    # Anomaly scatter
    anomaly_fig = px.scatter(dff, x="latency_sec", y="call_drop_rate",
                             color="anomaly", size="bandwidth_numeric",
                             hover_data=['tower_id', 'operator', 'network_type'],
                             title="Anomaly Detection: Latency vs Call Drop Rate")

    # Geo Map
    geo_fig = px.scatter_mapbox(
        dff, lat="location.latitude", lon="location.longitude",
        color="latency_sec", size="users_connected",
        hover_data=["tower_id", "operator", "call_drop_rate"],
        title="Geospatial Tower Performance",
        zoom=5, mapbox_style="carto-positron"
    )

    return kpi_cards, latency_fig, drop_fig, bandwidth_fig, anomaly_fig, geo_fig


# -------------------
# Run App
# -------------------
if __name__ == "__main__":
    app.run(debug=True, port=8050)


# In[ ]:




