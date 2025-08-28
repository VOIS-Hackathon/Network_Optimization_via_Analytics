#!/usr/bin/env python
# coding: utf-8
import pandas as pd
# import numpy as np
from sklearn.ensemble import IsolationForest
import dash  # type: ignore
from dash import dcc, html, Input, Output, State, callback  # type: ignore
import plotly.express as px  # type: ignore
# import plotly.io as pio  # type: ignore
# import plotly.graph_objects as   # type: ignore
import os
    
dash.register_page(__name__, path="/")

df = pd.read_csv(os.path.join(os.path.dirname(__file__), "final_data.csv"))

# Dropdown options
operators = [{"label": op, "value": op} for op in df["operator"].unique()]
network_types = [{"label": nt, "value": nt} for nt in df["network_type"].unique()]


FEATURE_COLS = [
    'latency_sec', 'bandwidth_mbps', 'dropped_calls', 'total_calls',
    'uptime_percent', 'users_connected', 'download_speed_mbps', 'upload_speed_mbps',
    'signal_strength.RSSI', 'signal_strength.RSRP', 'signal_strength.SINR',
    'tower_load_percent', 'average_call_duration_sec', 'handover_success_rate',
    'packet_loss_percent', 'jitter_ms', 'tower_temperature_c', 'battery_backup_hours',
    'tower_age_years'
]

layout = html.Div(
    className="dark",
    id="theme-container",
    children=[
        html.Div (
        className="container",
        children =[dcc.Store(id="filtered-data"),
        html.H1(
            "📡 Network Performance Optimization Dashboard",
            style={"textAlign": "center"},
        ),

        # Filters
        html.Div(
    className="filter",
    children=[
        html.Div([
            html.Label("Select Operator:"),
            dcc.Dropdown(id="operator_filter", options=operators, value=None, multi=True, placeholder="")
        ]),
        html.Div([
            html.Label("Select Network Type:"),
        dcc.Dropdown(
            id="network_filter",
            options=network_types,
            value=None,
            multi=True,
            placeholder=""  # removes "Select..."
        )
        ]),
        html.Div(className="datePick",children=[
            html.Label("Select Date Range:"),
            dcc.DatePickerRange(
                id="date_filter",
                start_date=df["timestamp"].min(),
                end_date=df["timestamp"].max(),
                display_format="YYYY-MM-DD",
            )
        ], style={"gridColumn": "span 3"}) 
    ]
),
        html.Br(),

        # KPI Cards
        html.Div(
            id="kpi_cards", style={"display": "flex", "justifyContent": "space-around"}
        ),
        html.Br(),

        # Tabs
        dcc.Tabs(
        id="tabs",
        value="trends",
        children=[
            dcc.Tab(label="Trends", value="trends"),
            dcc.Tab(label="Anomalies", value="anomalies"),
            dcc.Tab(label="Geo View", value="geo"),
        ],persistence=True
        ),
        html.Div(id="tab-content"),

        html.Button("🌙", id="theme-toggle", n_clicks=0, className="theme-btn"),
        ]),
    ],
)

# -------------------
# Callbacks
# -------------------

@callback(
    Output("filtered-data", "data"),
    [Input("operator_filter", "value"),
     Input("network_filter", "value"),
     Input("date_filter", "start_date"),
     Input("date_filter", "end_date")]
)
def filter_and_store(selected_ops, selected_nts, start_date, end_date):
    dff = df
    if selected_ops:
        dff = dff[dff["operator"].isin(selected_ops)]
    if selected_nts:
        dff = dff[dff["network_type"].isin(selected_nts)]
    dff = dff[(dff["timestamp"] >= start_date) & (dff["timestamp"] <= end_date)]
    return dff.to_dict("records")   # serialize for storage


# --- theme callback ---
@callback(
    Output("theme-container", "className"),
    Output("theme-toggle", "children"),
    Input("theme-toggle", "n_clicks"),
    State("theme-container", "className"),
    prevent_initial_call=True,
)
def toggle_theme(n_clicks, current_theme):
    if current_theme == "light":
        return "dark", "☀️"
    return "light", "🌙"

# --- Kpi callback ---
@callback(
    Output("kpi_cards", "children"),
    Input("filtered-data", "data")
)
def update_kpis(data):
    dff = pd.DataFrame(data)
    return [
        html.Div(className="kpi-card", children=[html.H3("Avg Latency"), html.H4(f"{dff['latency_sec'].mean():.2f} sec")]),
        html.Div(className="kpi-card", children=[html.H3("Total Dropped Calls"), html.H4(style={"color":"red"},children=[f"{dff['dropped_calls'].sum()}"])]),
        html.Div(className="kpi-card", children=[html.H3("Avg Bandwidth"), html.H4(f"{dff['bandwidth_numeric'].mean()/1e6:.2f} Mbps")]),
        html.Div(className="kpi-card", children=[html.H3("Avg Drop Rate"), html.H4(style={'color':'red'},children=[f"{dff['call_drop_rate'].mean():.2f}%"])]),
    ]

# --- Trends callback ---
@callback(
    [
    Output("latency_trend", "figure"),
    Output("drop_trend", "figure"),
    Output("bandwidth_trend", "figure"),
    ],
    [
    Input("filtered-data", "data"),
    Input("theme-container", "className")],
    prevent_initial_call=False
)
def update_latency(data, theme):
    template = "plotly_dark" if theme == "dark" else "plotly_white"
    dff = pd.DataFrame(data)
    # Trends
    latency_fig = px.line(
        dff,
        x="timestamp",
        y="latency_sec",
        color="operator",
        title="Latency Over Time",
        template=template,
        custom_data=dff[FEATURE_COLS]  
    )
    drop_fig = px.line(
        dff,
        x="timestamp",
        y="dropped_calls",
        color="operator",
        title="Dropped Calls Over Time",
        template=template,
        custom_data=dff[FEATURE_COLS]  
    )
    bandwidth_fig = px.line(
        dff,
        x="timestamp",
        y="bandwidth_numeric",
        color="operator",
        title="Bandwidth Usage Over Time",
        template=template,
        custom_data=dff[FEATURE_COLS]  
    )
    for fig in [latency_fig,drop_fig,bandwidth_fig]:
        fig.update_layout(uirevision="constant")

    return latency_fig,drop_fig,bandwidth_fig


# --- Anomaly callback ---
@callback(
    Output("anomaly_scatter", "figure"),
    [
    Input("filtered-data", "data"),
    Input("theme-container", "className")]
)
def update_anomaly(data,theme_class="dark"):
    template = "plotly_dark" if theme_class == "dark" else "plotly_white"
    dff = pd.DataFrame(data)

    fig = px.scatter(
        dff,
        x="latency_sec", y="call_drop_rate",
        color="anomaly", size="bandwidth_numeric",
        hover_data=["tower_id", "operator", "network_type"],
        title="Anomaly Detection: Latency vs Call Drop Rate",
        template=template,
        render_mode="webgl",
    )
    fig.update_layout(uirevision="constant")
    return fig

# --- Geo callback ---
@callback(
    Output("geo_map", "figure"),
    [
        Input("filtered-data", "data"),
        Input("theme-container", "className")
    ]
)
def update_geo(data, theme_class="dark"):
    template = "plotly_dark" if theme_class == "dark" else "plotly_white"
    dff = pd.DataFrame(data)

    fig = px.scatter_map(
        dff,
        lat="location.latitude", lon="location.longitude",
        color="latency_sec", size="users_connected",
        hover_data=["tower_id", "operator", "call_drop_rate"],
        title="Geospatial Tower Performance",
        zoom=5,
        template=template,
        map_style="carto-positron" if theme_class == "light" else "carto-darkmatter",
    )
    fig.update_layout(uirevision="constant")
    return fig


# --- tabs callback ---
@callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "trends":
        return [
            dcc.Store(id="selected-tower-data"),   
            dcc.Location(id="url", refresh = True),
            dcc.Graph(id="latency_trend"),
            dcc.Graph(id="drop_trend"),
            dcc.Graph(id="bandwidth_trend"),
        ]
    elif tab == "anomalies":
        return dcc.Graph(id="anomaly_scatter")
    elif tab == "geo":
        return dcc.Graph(id="geo_map")
    return []

@callback(
    Output("selected-tower-data","data"),
    Output("url","href"),
    Input("latency_trend","clickData"),
    prevent_initial_call = True
)
def handle_click(clickData):
    print("CLICKDATA:", clickData)
    if not clickData:
        raise dash.exceptions.PreventUpdate
    features = clickData["points"][0]["customdata"]
    print("FEATURES:", features)
    row_dict = dict(zip(FEATURE_COLS, features))
    return row_dict, "/page2"