import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import base64
import io
import os

# Initialize the Dash app
app = dash.Dash(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "../data/cleaned_network_data.csv")

# --- Data Loading and Preprocessing ---
try:
    # Read the CSV file directly from the local file system.
    df = pd.read_csv(DATA_PATH)
except Exception as e:
    print(f"Error reading CSV file. Please make sure 'cleaned_network_data.csv' is in the same directory as this script. Error: {e}")
    df = pd.DataFrame() # Create an empty DataFrame if an error occurs

if not df.empty:
    # Clean the column names to remove leading/trailing spaces
    df.columns = df.columns.str.strip()

    # Data type conversion and cleaning
    # Convert 'timestamp' to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Convert numeric columns, handling potential errors
    numeric_cols = [
        'latency_sec', 'bandwidth_mbps', 'dropped_calls', 'total_calls', 'download_speed_mbps',
        'signal_strength_dbm', 'tower_load_percent', 'average_call_duration_sec',
        'handover_success_rate', 'packet_loss_percent', 'jitter_ms', 'tower_temperature_c',
        'battery_backup_hours', 'tower_age_years', 'upload_speed_mbps', 'location.latitude',
        'location.longitude', 'signal_strength.RSRP', 'signal_strength.SINR',
        'voip_metrics.jitter_ms', 'voip_metrics.packet_loss_percent', 'tower_height_m',
        'call_drop_rate'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate 'call_drop_rate' if it's not present or if 'total_calls' is not zero
    if 'call_drop_rate' not in df.columns or df['call_drop_rate'].isnull().all():
        df['call_drop_rate'] = df.apply(
            lambda row: (row['dropped_calls'] / row['total_calls']) * 100 if row['total_calls'] > 0 else 0,
            axis=1
        )

    # Calculate average KPIs for display
    avg_latency = df['latency_sec'].mean()
    avg_call_drop_rate = df['call_drop_rate'].mean()
    avg_bandwidth_mbps = df['bandwidth_mbps'].mean()

    # Get top 10 underperforming towers by call drop rate
    top_underperforming_towers = df.groupby('tower_id').agg(
        avg_call_drop_rate=('call_drop_rate', 'mean'),
        num_dropped_calls=('dropped_calls', 'sum'),
        total_calls=('total_calls', 'sum')
    ).sort_values(by='avg_call_drop_rate', ascending=False).head(10).reset_index()
    # Format the call drop rate to two decimal places
    top_underperforming_towers['avg_call_drop_rate'] = top_underperforming_towers['avg_call_drop_rate'].round(2)

    # --- Dashboard Layout ---
    app.layout = html.Div(
        style={'font-family': 'Arial, sans-serif', 'padding': '20px', 'background-color': '#f0f2f5'},
        children=[
            html.H1("Network Performance Dashboard", style={'color': '#333', 'text-align': 'center', 'margin-bottom': '20px'}),

            # KPIs Section
            html.Div(
                style={'display': 'flex', 'justify-content': 'space-around', 'margin-bottom': '30px'},
                children=[
                    html.Div(
                        style={'background-color': '#fff', 'padding': '20px', 'border-radius': '10px', 'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)'},
                        children=[
                            html.H2("Average Latency", style={'color': '#555', 'font-size': '1.2rem'}),
                            html.P(f"{avg_latency:.2f} s", style={'color': '#007BFF', 'font-size': '2rem', 'font-weight': 'bold'})
                        ]
                    ),
                    html.Div(
                        style={'background-color': '#fff', 'padding': '20px', 'border-radius': '10px', 'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)'},
                        children=[
                            html.H2("Average Call Drop Rate", style={'color': '#555', 'font-size': '1.2rem'}),
                            html.P(f"{avg_call_drop_rate:.2f} %", style={'color': '#FF5733', 'font-size': '2rem', 'font-weight': 'bold'})
                        ]
                    ),
                    html.Div(
                        style={'background-color': '#fff', 'padding': '20px', 'border-radius': '10px', 'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)'},
                        children=[
                            html.H2("Avg. Bandwidth Utilization", style={'color': '#555', 'font-size': '1.2rem'}),
                            html.P(f"{avg_bandwidth_mbps:.2f} Mbps", style={'color': '#28A745', 'font-size': '2rem', 'font-weight': 'bold'})
                        ]
                    )
                ]
            ),

            # Dropdown Filters
            html.Div(
                style={'display': 'flex', 'justify-content': 'center', 'gap': '20px', 'margin-bottom': '20px'},
                children=[
                    dcc.Dropdown(
                        id='operator-dropdown',
                        options=[{'label': i, 'value': i} for i in df['operator'].unique()],
                        placeholder="Select an Operator",
                        multi=True,
                        style={'width': '300px'}
                    ),
                    dcc.Dropdown(
                        id='network-type-dropdown',
                        options=[{'label': i, 'value': i} for i in df['network_type'].unique()],
                        placeholder="Select a Network Type",
                        multi=True,
                        style={'width': '300px'}
                    )
                ]
            ),

            # New charts and tables
            html.Div(
                style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '20px', 'margin-bottom': '20px'},
                children=[
                    # Interactive Map to visualize underperforming regions
                    html.Div(
                        style={'flex': '2 1 600px'},
                        children=[
                            dcc.Graph(id='underperforming-regions-map')
                        ]
                    ),
                    # Time-series plot of latency
                    html.Div(
                        style={'flex': '1 1 300px'},
                        children=[
                            dcc.Graph(id='latency-time-series')
                        ]
                    )
                ]
            ),
            
            # Top Underperforming Towers Table
            html.Div(
                style={'background-color': '#fff', 'padding': '20px', 'border-radius': '10px', 'box-shadow': '0 4px 6px rgba(0, 0, 0, 0.1)', 'margin-top': '20px'},
                children=[
                    html.H2("Top 10 Underperforming Towers", style={'color': '#555', 'font-size': '1.2rem', 'text-align': 'center'}),
                    dash_table.DataTable(
                        id='top-towers-table',
                        columns=[{"name": i, "id": i} for i in top_underperforming_towers.columns],
                        data=top_underperforming_towers.to_dict('records'),
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        },
                        style_cell={'textAlign': 'left'}
                    )
                ]
            )
        ]
    )

    # --- Callbacks ---
    # Callback to update all visualizations based on dropdown filters
    @app.callback(
        [Output('underperforming-regions-map', 'figure'),
         Output('latency-time-series', 'figure')],
        [Input('operator-dropdown', 'value'),
         Input('network-type-dropdown', 'value')]
    )
    def update_graphs(selected_operators, selected_network_types):
        # Filter the DataFrame based on selections
        filtered_df = df.copy()
        if selected_operators:
            filtered_df = filtered_df[filtered_df['operator'].isin(selected_operators)]
        if selected_network_types:
            filtered_df = filtered_df[filtered_df['network_type'].isin(selected_network_types)]

        # --- Mapbox Plot ---
        # Group data by location to get average call drop rate for each tower
        map_data = filtered_df.groupby(['location.latitude', 'location.longitude', 'tower_id']).agg(
            avg_call_drop_rate=('call_drop_rate', 'mean')
        ).reset_index()

        fig_map = px.scatter_map(
            map_data,
            lat="location.latitude",
            lon="location.longitude",
            color="avg_call_drop_rate",
            size="avg_call_drop_rate",
            hover_name="tower_id",
            hover_data={"avg_call_drop_rate": ':.2f'},
            color_continuous_scale=px.colors.sequential.Inferno,
            map_style="carto-positron",
            zoom=10,
            title="Underperforming Regions by Average Call Drop Rate"
        )
        fig_map.update_layout(
            margin={"r":0,"t":50,"l":0,"b":0},
            title={'x': 0.5, 'xanchor': 'center'},
            coloraxis_colorbar={'title':'Call Drop %'}
        )

        # --- Time-Series Plot ---
        # Group by a time interval (e.g., hour) to show trends
        time_series_data = filtered_df.groupby(filtered_df['timestamp'].dt.to_period('H')).agg(
            avg_latency=('latency_sec', 'mean')
        ).reset_index()
        time_series_data['timestamp'] = time_series_data['timestamp'].astype(str)

        fig_latency = px.line(
            time_series_data,
            x='timestamp',
            y='avg_latency',
            markers=True,
            title="Average Latency Over Time"
        )
        fig_latency.update_layout(
            xaxis_title="Time",
            yaxis_title="Average Latency (s)",
            title={'x': 0.5, 'xanchor': 'center'}
        )
        
        return fig_map, fig_latency

if __name__ == '__main__':
    # The run_server() call is a placeholder and will be handled by the Canvas environment.
    # In a local environment, you would use app.run(debug=True).
    app.run(debug=True)
